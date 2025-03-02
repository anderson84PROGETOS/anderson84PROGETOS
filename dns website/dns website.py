import os
import socket
import sys
import http.client
import ssl
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝
██║  ██║██╔██╗ ██║███████╗    ██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗  
██║  ██║██║╚██╗██║╚════██║    ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝  
██████╔╝██║ ╚████║███████║    ╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝                                                                                   
""")

def listar_txt_na_pasta():
    """Lista arquivos .txt na pasta e permite ao usuário escolher um."""
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nPor favor, insira um número válido.")

def carregar_wordlist():
    """Carrega a wordlist escolhida pelo usuário e retorna uma lista de subdomínios válidos."""
    wordlist_file = listar_txt_na_pasta()
    with open(wordlist_file, 'r', encoding='utf-8') as f:
        subdominios = [sub.strip() for sub in f.read().splitlines() if sub.strip()]  # Remove linhas vazias

    # Filtra subdomínios inválidos (muito longos ou vazios)
    subdominios_validos = [sub for sub in subdominios if 1 <= len(sub) <= 63 and all(c.isalnum() or c in '-.' for c in sub)]

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] Wordlist carregada: {os.path.basename(wordlist_file)}")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"[+] Contém {len(subdominios_validos)} palavras válidas\n")   
    return subdominios_validos

def limpar_url(url):
    """Remove 'http://' e 'https://' da URL para manter apenas o domínio."""
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]
    return url.split('/')[0]  # Remove qualquer caminho extra após o domínio

def testar_protocolos(host):
    """Testa se o subdomínio suporta HTTP ou HTTPS e retorna o protocolo funcional."""
    # Testa HTTPS primeiro (prioridade comum)
    try:
        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(host, timeout=2, context=context)
        conn.request("HEAD", "/")
        response = conn.getresponse()
        conn.close()
        if 200 <= response.status <= 399:  # Verifica se é uma resposta válida
            return "https"
    except (http.client.HTTPException, socket.timeout, ConnectionRefusedError, socket.gaierror, ssl.SSLError):
        pass
    
    # Testa HTTP
    try:
        conn = http.client.HTTPConnection(host, timeout=2)
        conn.request("HEAD", "/")
        response = conn.getresponse()
        conn.close()
        if 200 <= response.status <= 399:  # Verifica se é uma resposta válida
            return "http"
    except (http.client.HTTPException, socket.timeout, ConnectionRefusedError, socket.gaierror):
        pass
    
    # Retorna None se nenhum protocolo funcionar
    return None

def consultar_dns(dominio, subdominios):
    """Realiza consultas DNS e exibe os resultados em tempo real com e sem protocolo."""
    encontrados_com_protocolo = []
    encontrados_sem_protocolo = []
    contador_com_protocolo = 1
    contador_sem_protocolo = 1

    # Primeira exibição: com protocolo (https:// ou http://)
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Resultados com protocolo http e https\n")
    for sub in subdominios:
        host = f"{sub}.{dominio}"
        if len(host) > 255 or any(len(label) > 63 for label in host.split('.')):
            continue  # Pula hostnames inválidos
        
        try:
            ip = socket.gethostbyname(host)
            protocolo = testar_protocolos(host)

            # Adiciona à lista de subdomínios sem protocolo (todos com IP resolvido)
            encontrados_sem_protocolo.append((host, ip))

            # Exibe e adiciona à lista com protocolo apenas se HTTP/HTTPS funcionar
            if protocolo:
                resultado = (
                    Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{contador_com_protocolo:<4} =  " +  
                    Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"HOST ENCONTRADO: " + 
                    Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{protocolo}://{host:<45}" +  
                    Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"IP: " +  
                    Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ip}"
                )
                print(resultado)
                encontrados_com_protocolo.append((host, ip, protocolo))
                contador_com_protocolo += 1

        except socket.gaierror:
            pass  # Não exibe erros de DNS

    # Segunda exibição: sem protocolo (todos os subdomínios com IP resolvido)
    if encontrados_sem_protocolo:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\n[+] Resultados sem protocolo\n")
        for host, ip in encontrados_sem_protocolo:
            resultado_sem_protocolo = (
                Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{contador_sem_protocolo:<4} =  " +  
                Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"HOST ENCONTRADO: " + 
                Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{host:<40}" +  
                Fore.LIGHTYELLOW_EX + Style.BRIGHT + f" IP: " +  
                Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ip}"
            )
            print(resultado_sem_protocolo)
            contador_sem_protocolo += 1

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Total de subdomínios com protocolo: {len(encontrados_com_protocolo)}")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n [+] Total de subdomínios sem protocolo: {len(encontrados_sem_protocolo)}\n")
    
    # Retorna ambas as listas para salvar
    return (
        [f"{proto}://{host:<40}  IP: {ip}" for host, ip, proto in encontrados_com_protocolo],  # Com protocolo
        [f"{host:<40}  IP: {ip}" for host, ip in encontrados_sem_protocolo]  # Sem protocolo
    )

def limpar_cores(texto):
    """Remove as sequências de cor ANSI do texto."""
    import re
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

def salvar_resultados(resultados_com_protocolo, resultados_sem_protocolo):
    """Salva os resultados com e sem protocolo em um único arquivo."""
    if resultados_com_protocolo or resultados_sem_protocolo:
        escolha = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar os resultados em um único arquivo? (s/n): ").strip().lower()
        if escolha == 's':
            nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (exemplo: dns_resultados.txt): ").strip()
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                # Salvar resultados com protocolo
                if resultados_com_protocolo:
                    f.write("[+] Resultados com protocolo http e https\n\n")
                    resultados_limpos_com = [limpar_cores(r) for r in resultados_com_protocolo]
                    f.write('\n'.join(resultados_limpos_com) + '\n\n')
                
                # Salvar resultados sem protocolo
                if resultados_sem_protocolo:
                    f.write("\n[+] Resultados sem protocolo\n\n")
                    resultados_limpos_sem = [limpar_cores(r) for r in resultados_sem_protocolo]
                    f.write('\n'.join(resultados_limpos_sem) + '\n')
            
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Ambos os resultados salvos em: {nome_arquivo}\n")

def main():
    subdominios = carregar_wordlist()
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome ou a URL do website (ex: exemplo.com ou https://exemplo.com): ").strip()
    dominio = limpar_url(url)
    
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Domínio processado: {dominio}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[+] Iniciando consulta DNS...\n")

    resultados_com_protocolo, resultados_sem_protocolo = consultar_dns(dominio, subdominios)
    
    if resultados_com_protocolo or resultados_sem_protocolo:
        salvar_resultados(resultados_com_protocolo, resultados_sem_protocolo)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
