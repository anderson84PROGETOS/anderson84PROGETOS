import os
import sys
import socket
import requests
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ ███████╗
██╔══██╗████╗  ██║██╔════╝    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗╚══███╔╝
██║  ██║██╔██╗ ██║███████╗    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝  ███╔╝ 
██║  ██║██║╚██╗██║╚════██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗ ███╔╝  
██████╔╝██║ ╚████║███████║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝
""")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

resultados_encontrados = []

def listar_txt_na_pasta():
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]
    if not txt_files:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha um arquivo de wordlist")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{idx} = {file}")
    while True:
        try:
            choice = int(input(Fore.CYAN + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "Opção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "Por favor, insira um número válido.")

def carregar_wordlist(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

def check_dns(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def check_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def get_cor_status(status):
    if status == 200:
        return Fore.LIGHTGREEN_EX + Style.BRIGHT        
    elif status == 403:
        return Fore.LIGHTYELLOW_EX + Style.BRIGHT
    elif status == 404:
        return Fore.LIGHTRED_EX + Style.BRIGHT      
    else:
        return Fore.LIGHTWHITE_EX + Style.BRIGHT

def test_domain(subdomain):
    full_domain = f"{subdomain}.{domain}" if subdomain else domain
    ip = check_dns(full_domain)
    if ip:
        for scheme in ["https://", "http://"]:
            url = scheme + full_domain
            status = check_url(url)
            if status:
                protocolo = scheme.upper().replace("://", "").ljust(6)
                url_formatado = url.ljust(40)
                ip_formatado = f"IP: {ip}".ljust(22)
                status_str = f"[status {status}]"
                cor = get_cor_status(status)
                linha = f"[{protocolo}] {url_formatado} {ip_formatado} {status_str}"
                print(cor + linha)
                resultados_encontrados.append(linha)
                break

# Escolha do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()
subdomains = carregar_wordlist(wordlist_file)

print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nTotal de subdomínios na wordlist: {len(subdomains)}\n")
domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "🔍 Digite o domínio do site (ex: exemplo.com.br): ").strip()
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n🔎 Iniciando varredura para: {domain}\n")

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(test_domain, subdomains)

    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if salvar in ['s', 'sim']:
        nome_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (sem .txt): ").strip()
        if not nome_arquivo:
            nome_arquivo = "resultado"
        if not nome_arquivo.endswith('.txt'):
            nome_arquivo += '.txt'
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            for linha in resultados_encontrados:
                f.write(linha + '\n')
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n✅ Resultados salvos em: {nome_arquivo}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n⚠️ Resultados não foram salvos.")

    input(Fore.LIGHTRED_EX + "\n\n  ========== PRESSIONE ENTER PARA SAIR ==========\n")
