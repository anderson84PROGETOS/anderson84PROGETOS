import requests
import re
import socket
from urllib.parse import urlparse
from colorama import Fore, init

# Inicializa o colorama para garantir que a coloração funcione no terminal
init(autoreset=True)

print(Fore.LIGHTBLUE_EX + """
██████╗  ██████╗ ███╗   ███╗██╗███╗   ██╗██╗ ██████╗ ███████╗    ██╗██████╗ 
██╔══██╗██╔═══██╗████╗ ████║██║████╗  ██║██║██╔═══██╗██╔════╝    ██║██╔══██╗
██║  ██║██║   ██║██╔████╔██║██║██╔██╗ ██║██║██║   ██║███████╗    ██║██████╔╝
██║  ██║██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║██║   ██║╚════██║    ██║██╔═══╝ 
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╔╝███████║    ██║██║     
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚══════╝    ╚═╝╚═╝     
""" + Fore.RESET)

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address, main_site_domain

def search_subdomains(url):
    # Garantir que a URL comece com http:// ou https://
    if not url.startswith('http'):
        url = f'http://{url}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"Erro ao fazer requisição para {url}: {e}")
        return [], ""  # Retorna lista vazia e string vazia

    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))  # Expressão regular para encontrar subdomínios
    main_site_ip, main_site_domain = get_main_site_ip(url)  # Obtem o IP do domínio principal

    subdomains_info = []

    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])  # Tenta obter o IP de cada subdomínio
        except socket.gaierror:
            ip_address = main_site_ip  # Se falhar, usa o IP do domínio principal
        subdomains_info.append((subdomain, ip_address))  # Armazena o subdomínio e seu IP

    return subdomains_info, main_site_domain  # Retorna tanto os subdomínios quanto o domínio principal

def save_to_file(subdomains_info, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for subdomain, ip_address in subdomains_info:
            file.write(f'{subdomain:<70}  IP:  {ip_address}\n\n')

def main():
    url = input(Fore.LIGHTYELLOW_EX + "\nDigite o Nome do website ou a URL do website: " + Fore.RESET)
    
    # Chama a função para buscar subdomínios e o domínio principal
    subdomains_info, main_site_domain = search_subdomains(url) 
    
    # Se o domínio principal for vazio, significa que houve erro na obtenção do domínio
    if not main_site_domain:
        print(Fore.RED + "Erro ao obter o domínio principal. Verifique a URL e tente novamente." + Fore.RESET)
        return

    # Exibe a quantidade de subdomínios encontrados
    print(f"\n\n{Fore.LIGHTRED_EX}Subdomínios Encontrados: {len(subdomains_info)}\n")

    for subdomain, ip_address in subdomains_info:
        print(f"{Fore.LIGHTGREEN_EX}{subdomain:<70}  {Fore.LIGHTRED_EX}IP: {ip_address}" + Fore.RESET)

    while True:
        salvar = input(Fore.LIGHTYELLOW_EX + "\nDeseja salvar as informações em um arquivo? (s/n): " + Fore.RESET).strip().lower()
        if salvar == "s":
            nome_arquivo = input(Fore.LIGHTYELLOW_EX + "\nDigite o nome do arquivo para salvar as informações (ex: subdomains.txt): " + Fore.RESET)
            if nome_arquivo.strip():  # Verifica se foi digitado algum nome de arquivo
                save_to_file(subdomains_info, nome_arquivo)
                print(Fore.LIGHTGREEN_EX + f"\nAs informações foram salvas no arquivo: {nome_arquivo}" + Fore.RESET)
            else:
                print(Fore.LIGHTRED_EX + "\nNenhum nome de arquivo foi fornecido. As informações não foram salvas." + Fore.RESET)
            break
        elif salvar == "n":
            print(Fore.LIGHTRED_EX + "\nAs informações não foram salvas" + Fore.RESET)
            break
        else:
            print(Fore.LIGHTRED_EX + "\nResposta inválida. Por favor, responda com 's' para sim ou 'n' para não." + Fore.RESET)

if __name__ == "__main__":
    main()

input(Fore.LIGHTBLUE_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
