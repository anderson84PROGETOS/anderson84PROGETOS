import requests
from bs4 import BeautifulSoup
import re
import socket
from urllib.parse import urlparse

print("""

███████╗██╗███╗   ██╗██████╗ ██╗███╗   ██╗ ██████╗     ██╗██████╗ 
██╔════╝██║████╗  ██║██╔══██╗██║████╗  ██║██╔════╝     ██║██╔══██╗
█████╗  ██║██╔██╗ ██║██║  ██║██║██╔██╗ ██║██║  ███╗    ██║██████╔╝
██╔══╝  ██║██║╚██╗██║██║  ██║██║██║╚██╗██║██║   ██║    ██║██╔═══╝ 
██║     ██║██║ ╚████║██████╔╝██║██║ ╚████║╚██████╔╝    ██║██║     
╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═╝╚═╝     
                                                                                                                                                            
""")

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address

def extrair_dados(url):
    headers_global = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers_global, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"\nErro ao acessar a página: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    links = soup.find_all('a')
    urls_unicas = set()
    for link in links:
        href = link.get('href')
        if href and href.startswith('http'):
            urls_unicas.add(href)

    content_urls = re.findall(r'content=["\'](https?://\S+?)(?=["\'])', str(soup))
    for url in content_urls:
        urls_unicas.add(url)

    print(f"\n\n\nForam Encontradas {len(urls_unicas)} URL\n")
    main_site_ip = get_main_site_ip(url)
    for url in urls_unicas:
        try:
            ip = socket.gethostbyname(urlparse(url).netloc)
            print(f"\nIP: {ip}   \tURL:   {url}")
        except socket.gaierror:
            print(f"\nIP: Não encontrado  \tURL:   {url}")
    print(f"\n\nIP principal do site: {main_site_ip}")

    subdomains_info = search_subdomains(url, headers=headers_global)
    print(f"\n\nForam encontrados {len(subdomains_info)} subdomínios\n")
    for subdomain, ip in subdomains_info:
        print(f"\nIP: {ip}            \tSubdomínio:  {subdomain}")

def search_subdomains(url, headers):
    if not url.startswith('http'):
        url = f'http://{url}'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"\nErro ao acessar subdomínios: {e}")
        return []

    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    main_site_ip = get_main_site_ip(url)

    subdomains_info = []
    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(urlparse(subdomain).netloc)
        except socket.gaierror:
            ip_address = main_site_ip
        subdomains_info.append((subdomain, ip_address))

    return subdomains_info

if __name__ == '__main__':
    url = input("\nDigite a URL do website: ")
    extrair_dados(url)
    
    input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
