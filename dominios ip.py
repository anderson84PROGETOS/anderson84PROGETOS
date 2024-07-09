import requests
import re
import socket
from urllib.parse import urlparse
from io import BytesIO

print("""

██████╗  ██████╗ ███╗   ███╗██╗███╗   ██╗██╗ ██████╗ ███████╗    ██╗██████╗ 
██╔══██╗██╔═══██╗████╗ ████║██║████╗  ██║██║██╔═══██╗██╔════╝    ██║██╔══██╗
██║  ██║██║   ██║██╔████╔██║██║██╔██╗ ██║██║██║   ██║███████╗    ██║██████╔╝
██║  ██║██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║██║   ██║╚════██║    ██║██╔═══╝ 
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╔╝███████║    ██║██║     
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚══════╝    ╚═╝╚═╝     
                                                                           
""")

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address, main_site_domain

def search_subdomains(url):
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
        print(f"Erro ao fazer requisição para {url}: {e}")
        return [], ""

    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    main_site_ip, main_site_domain = get_main_site_ip(url)

    subdomains_info = []

    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])
        except socket.gaierror:
            ip_address = main_site_ip
        subdomains_info.append((subdomain, ip_address))

    return subdomains_info, main_site_domain

def save_to_file(subdomains_info, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for subdomain, ip_address in subdomains_info:
            file.write(f'{subdomain}  →  {ip_address}\n\n')           

def main():
    url = input("\nDigite o Nome do website ou a URL do website: ")
    subdomains_info, main_site_domain = search_subdomains(url)

    print(f"\nForam Encontradas: {len(subdomains_info)} URL no website: {main_site_domain}\n")

    for subdomain, ip_address in subdomains_info:
        print(f"{subdomain}  →  {ip_address}")

    while True:
        salvar = input("\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
        if salvar == "s":
            nome_arquivo = input("\nDigite o nome do arquivo para salvar as informações (ex: subdomains.txt): ")
            if nome_arquivo.strip():  # Verifica se foi digitado algum nome de arquivo
                save_to_file(subdomains_info, nome_arquivo)
                print(f"\n\nAs informações foram salvas no arquivo: {nome_arquivo}")
            else:
                print("\nNenhum nome de arquivo foi fornecido. As informações não foram salvas.")
            break
        elif salvar == "n":
            print("\nAs informações não foram salvas.")
            break
        else:
            print("\nResposta inválida. Por favor, responda com 's' para sim ou 'n' para não.")

if __name__ == "__main__":
    main()
    
input("\nFIM [ENTER SAIR]\n")
