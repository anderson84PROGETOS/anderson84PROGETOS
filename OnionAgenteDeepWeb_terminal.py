import requests
import re
import socket
from urllib.parse import urlparse
from io import BytesIO

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address

def search_subdomains(url):
    if not url.startswith('http'):
        url = f'http://{url}'
    response = requests.get(url)
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    num_subdomains = len(subdomains)
    main_site_ip = get_main_site_ip(url)

    subdomains_info = []

    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])
        except socket.gaierror:
            ip_address = main_site_ip

        subdomains_info.append((subdomain, ip_address))

    return subdomains_info

def save_to_file(subdomains_info, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for subdomain, ip_address in subdomains_info:
            file.write(f'{subdomain}  ➡️{ip_address}\n\n')

print("""\n
        
     █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗    ██████╗ ███████╗███████╗██████╗ ██╗    ██╗███████╗██████╗ 
    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔══██╗██║    ██║██╔════╝██╔══██╗
    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   █████╗      ██║  ██║█████╗  █████╗  ██████╔╝██║ █╗ ██║█████╗  ██████╔╝
    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══╝      ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ██║███╗██║██╔══╝  ██╔══██╗
    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████╗    ██████╔╝███████╗███████╗██║     ╚███╔███╔╝███████╗██████╔╝
    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝    ╚═════╝ ╚══════╝╚══════╝╚═╝      ╚══╝╚══╝ ╚══════╝╚═════╝                                                                                                                
                                                     
""")            

def main():
    url = input("\nDigite o Nome do site ou a URL do website: ")
    subdomains_info = search_subdomains(url)

    print("\n")
    for subdomain, ip_address in subdomains_info:
        print(f"{subdomain}  ➡️  {ip_address}")

    salvar = input("\nDeseja salvar as informações em um arquivo? (sim/nao): ").lower()
    if salvar == "sim":
        save_to_file(subdomains_info, "subdomains.txt")
        print("\n\nAS Informações foram salvas no arquivo subdomains.txt")
    else:
        print("\n\nAs informações não foram salvas")

if __name__ == "__main__":
    main()
input("\nFIM [ENTER SAIR]\n")
