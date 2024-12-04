import os
import dns.resolver
import socket
import time  # Importa a biblioteca time para medir o tempo de execução

print(""" 

███████╗██╗   ██╗██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗    ██████╗ ███╗   ██╗███████╗
██╔════╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║    ██╔══██╗████╗  ██║██╔════╝
███████╗██║   ██║██████╔╝██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║    ██║  ██║██╔██╗ ██║███████╗
╚════██║██║   ██║██╔══██╗██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║  ██║██║╚██╗██║╚════██║
███████║╚██████╔╝██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ██████╔╝██║ ╚████║███████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                       
""")

def carregar_lista_nomes(arquivo):
    """Carrega a lista de subdomínios a partir de um arquivo de texto e remove pontos finais extras."""
    if not os.path.isfile(arquivo):
        print(f"Erro: Arquivo '{arquivo}' não encontrado.")
        return []
    with open(arquivo, 'r') as file:
        # Remove espaços em branco e pontos finais, se existirem
        return [linha.strip().rstrip(".") for linha in file if linha.strip()]

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
            print(f"Subdomínio: {subdominio_url:<75} IP: {ip}")            
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
    # Verifica se o arquivo existe na pasta onde o script está localizado
    script_path = os.path.dirname(os.path.abspath(__file__))
    nomes_arquivo = os.path.join(script_path, 'word.txt')

    # Solicita o nome do domínio
    domain = input("\nDigite o nome do website (exemplo: example.com): ").strip()

    # Carregar subdomínios do arquivo
    subdominios = carregar_lista_nomes(nomes_arquivo)

    # Verificação de subdomínios
    if not subdominios:
        print("\nNenhum subdomínio para verificar. Certifique-se de que o arquivo 'names.txt' contém subdomínios.")
    else:
        # Exibe uma mensagem informando que a busca será iniciada
        print("\n\nIniciando a busca de subdomínios...\n")
        
        encontrados = buscar_subdominios(subdominios, domain)

        if encontrados:
            print(f"\n\nTotal de subdomínios Encontrados: {len(encontrados)}")
        else:
            print("\nNenhum subdomínio encontrado.")

    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
