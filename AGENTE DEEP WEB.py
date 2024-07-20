import requests
import re
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup

print("""

 █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗    ██████╗ ███████╗███████╗██████╗     ██╗    ██╗███████╗██████╗ 
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔══██╗    ██║    ██║██╔════╝██╔══██╗
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   █████╗      ██║  ██║█████╗  █████╗  ██████╔╝    ██║ █╗ ██║█████╗  ██████╔╝
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══╝      ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝     ██║███╗██║██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████╗    ██████╔╝███████╗███████╗██║         ╚███╔███╔╝███████╗██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝    ╚═════╝ ╚══════╝╚══════╝╚═╝          ╚══╝╚══╝ ╚══════╝╚═════╝ 

""")

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address

def search_subdomains(url, headers):
    if not url.startswith('http'):
        url = f'http://{url}'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição para {url}: {e}")
        return [], get_main_site_ip(url)
    
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    main_site_ip = get_main_site_ip(url)

    subdomains_info = []
    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(urlparse(subdomain).netloc)
        except socket.gaierror:
            ip_address = main_site_ip
        subdomains_info.append((subdomain, ip_address))

    return subdomains_info, main_site_ip

def extract_data(url):
    headers_global = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers_global)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição para {url}: {e}")
        return

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        urls_unicas = set()

        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                urls_unicas.add(href)

        content_urls = re.findall(r'content=["\'](https?://\S+?)(?=["\'])', str(soup))
        urls_unicas.update(content_urls)

        print(f"\n\nForam Encontradas {len(urls_unicas)} URL\n")
        main_site_ip = get_main_site_ip(url)

        for url in urls_unicas:
            try:
                ip = socket.gethostbyname(urlparse(url).netloc)
                print(f"IP: {ip}   \tURL: {url}\n\n")
            except socket.gaierror:
                print(f"IP: Não encontrado  \tURL: {url}\n\n")

        print(f"\nIP principal do site: {main_site_ip}")

        subdomains_info, main_site_ip = search_subdomains(url, headers_global)
        print(f"\nForam Encontrados {len(subdomains_info)} subdomínios\n")
        for subdomain, ip in subdomains_info:
            print(f"IP: {ip}   \tSubdomínio: {subdomain}")

def main():
    url = input("\nDigite a URL do website: ")
    extract_data(url)

    subdomains_info, main_site_domain = search_subdomains(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    })

    print(f"\n\n\nForam Encontradas: {len(subdomains_info)} URLs no website: {main_site_domain}\n")
    for subdomain, ip_address in subdomains_info:
        print(f"{subdomain:<70}  IP: {ip_address}")

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
