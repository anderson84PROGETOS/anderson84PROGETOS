import os
import dns.resolver
import socket
import time  # Importa a biblioteca time para medir o tempo de execução
import requests  # Para fazer o download do arquivo de subdomínios da URL
import re  # Para validar subdomínios

print("""

███████╗██╗   ██╗██████╗ ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗     ██████╗ ███╗   ██╗███████╗
██╔════╝██║   ██║██╔══██╗██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔════╝
███████╗██║   ██║██████╔╝█████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝    ██║  ██║██╔██╗ ██║███████╗
╚════██║██║   ██║██╔══██╗██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗    ██║  ██║██║╚██╗██║╚════██║
███████║╚██████╔╝██████╔╝██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║    ██████╔╝██║ ╚████║███████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                           
""")

def carregar_lista_nomes(arquivo):
    """Carrega a lista de subdomínios a partir de um arquivo de texto e remove pontos finais extras."""
    if not os.path.isfile(arquivo):
        print(f"Erro: Arquivo '{arquivo}' não encontrado.")
        return []
    with open(arquivo, 'r') as file:
        # Remove espaços em branco e pontos finais, se existirem
        return [linha.strip().rstrip(".") for linha in file if linha.strip()]

def carregar_lista_nomes_da_url(url):
    """Carrega a lista de subdomínios a partir de uma URL."""
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx/5xx
        conteudo = resposta.text
        subdominios = [linha.strip().rstrip(".") for linha in conteudo.splitlines() if linha.strip()]
        return subdominios
    except requests.RequestException as e:
        print(f"Erro ao carregar a lista de subdomínios da URL: {e}")
        return []

def validar_subdominio(subdominio):
    """Valida se o subdomínio é uma string adequada para consulta DNS."""
    if len(subdominio) > 253 or not re.match(r'^[a-zA-Z0-9-]{1,63}$', subdominio.split('.')[0]):
        return False
    return True

def verificar_protocolo(subdominio):
    """Detecta automaticamente se o protocolo é HTTP ou HTTPS."""
    try:
        # Tenta conectar na porta 443 (HTTPS)
        socket.create_connection((subdominio, 443), timeout=3)
        return "https"
    except (socket.timeout, socket.error):
        try:
            # Tenta conectar na porta 80 (HTTP)
            socket.create_connection((subdominio, 80), timeout=3)
            return "http"
        except (socket.timeout, socket.error):
            # Caso nenhuma das portas esteja acessível, retorna http por padrão
            return "http"

def calcular_tempo_estimado(subdominios_list, tempo_medio_por_subdominio):
    """Calcula o tempo estimado total para processar todos os subdomínios."""
    total_subdominios = len(subdominios_list)
    tempo_estimado = total_subdominios * tempo_medio_por_subdominio
    
    # Calcula horas, minutos e segundos
    horas = tempo_estimado // 3600
    minutos = (tempo_estimado % 3600) // 60
    segundos = tempo_estimado % 60
    
    return tempo_estimado, horas, minutos, segundos

def buscar_subdominios(domains_list, domain):
    subdominios_encontrados = []
    start_time = time.time()  # Marca o tempo de início da busca
    
    # Estima o tempo médio por subdomínio (tempo em segundos)
    tempo_medio_por_subdominio = 0.5  # Este valor pode ser ajustado com base em testes anteriores
    
    # Calcula e exibe o tempo estimado de execução antes de iniciar
    tempo_estimado, horas_estimadas, minutos_estimados, segundos_restantes = calcular_tempo_estimado(domains_list, tempo_medio_por_subdominio)
    print(f"Tempo estimado para escanear todos os subdomínios: {horas_estimadas:.0f} horas, {minutos_estimados:.0f} minutos e {segundos_restantes:.0f} segundos\n")
    
    for i, subdominio in enumerate(domains_list):
        if not validar_subdominio(subdominio):
            print(f"Subdomínio inválido: {subdominio}")
            continue
        
        try:
            subdominio_completo = f"{subdominio}.{domain}"
            
            # Usar resolvers padrão do sistema
            resolver = dns.resolver.Resolver()
            
            # Tenta resolver o subdomínio
            resolver.resolve(subdominio_completo, 'A')
            
            # Obtém o endereço IP do subdomínio
            ip = socket.gethostbyname(subdominio_completo)
            
            # Detecta o protocolo (http ou https)
            protocolo = verificar_protocolo(subdominio_completo)
            subdominio_url = f"{protocolo}://{subdominio_completo}"
            
            subdominios_encontrados.append(subdominio_url)
            print(f"Sub: {subdominio_url:<72} IP: {ip}")
           
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            pass  # Subdomínio não encontrado ou erro de resposta
        except (socket.gaierror, socket.error) as e:
            print(f"Erro ao obter IP de {subdominio_completo}: {e}")
            pass
        except dns.exception.DNSException as e:
            print(f"Erro ao consultar {subdominio_completo}: {e}")
            pass

    # Exibe o tempo total após o término da busca
    tempo_execucao_total = time.time() - start_time
    minutos_total = tempo_execucao_total // 60
    segundos_total = tempo_execucao_total % 60
    print(f"\n\nTempo total de execução: {minutos_total:.0f} minutos e {segundos_total:.2f} segundos\n")
    return subdominios_encontrados

if __name__ == "__main__":
    # Solicita ao usuário qual arquivo de subdomínios ele deseja usar
    print("\nEscolha um arquivo de subdomínios\n")
    print("1. word.txt  = Contem 575 Lista")
    print("2. names.txt = Contem 129407 Lista")
    print("3. subdomain.txt = Contem 676 Lista")
    print("4. common.txt = Contem 868 Lista")
    escolha = input("\nDigite o número da sua escolha: ").strip()

    if escolha == "1":
        url = "https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/Subdomain%20dns/word.txt"
    elif escolha == "2":
        url = "https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/Subdomain%20dns/names.txt"
    elif escolha == "3":
        url = "https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/Subdomain%20dns/subdomain.txt"                                                

    elif escolha == "4":
        url = "https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/dns%20sub/common.txt" 
   
    else:
        print("\nEscolha inválida. Saindo do programa.")
        exit()

    # Solicita o nome do domínio
    domain = input("\nDigite o nome do website (exemplo: example.com): ").strip()

    # Carregar subdomínios da URL
    subdominios = carregar_lista_nomes_da_url(url)

    # Verificação de subdomínios
    if not subdominios:
        print("\nNenhum subdomínio para verificar. Certifique-se de que a URL contém subdomínios.")
    else:
        # Exibe uma mensagem informando que a busca será iniciada
        print("\n\nIniciando a busca de subdomínios...\n")
        
        encontrados = buscar_subdominios(subdominios, domain)

    if encontrados:
        print(f"\n\nTotal de subdomínios Encontrados: {len(encontrados)}")
    else:
        print("\nNenhum subdomínio encontrado.")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
