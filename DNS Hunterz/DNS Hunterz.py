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

# Cabeçalhos simulando navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Lista para armazenar resultados encontrados
resultados_encontrados = []

# Função para listar arquivos .txt na pasta
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

# Carregar conteúdo da wordlist
def carregar_wordlist(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

# Verifica DNS
def check_dns(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror:
        return None

# Verifica se a URL responde
def check_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

# Função principal por subdomínio
def test_domain(subdomain):
    full_domain = f"{subdomain}.{domain}" if subdomain else domain
    ip = check_dns(full_domain)
    if ip:
        resultado = f"[✓] DNS resolvido: {full_domain:<33} -> {ip}"
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + resultado)
        resultados_encontrados.append(resultado)

        for scheme in ["https://", "http://"]:
            url = scheme + full_domain
            status = check_url(url)
            if status:
                info = f"    └── [{scheme.upper().replace('://','')}] {url:<40} [status {status}]"
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + info)
                resultados_encontrados.append(info)
                break

# Escolha do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()
subdomains = carregar_wordlist(wordlist_file)

print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nTotal de subdomínios na wordlist: {len(subdomains)}\n")

# Entrada do domínio
domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "🔍 Digite o domínio do site (ex: exemplo.com.br): ").strip()

print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n🔎 Iniciando varredura para: {domain}\n")

# Execução com threads
if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(test_domain, subdomains)

    # Pergunta se deseja salvar
    salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if salvar in ['s', 'sim']:
        nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (Digite somente o nome do arquivo sem .txt): ").strip()
        if not nome_arquivo:
            nome_arquivo = "resultado"  # nome padrão caso não digite nada
        if not nome_arquivo.endswith('.txt'):
            nome_arquivo += '.txt'
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            for linha in resultados_encontrados:
                f.write(linha + '\n')
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n✅ Resultados salvos em: {nome_arquivo}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n⚠️ Resultados não foram salvos.")

    input(Fore.LIGHTRED_EX + "\n\n  ========== PRESSIONE ENTER PARA SAIR ==========\n")
