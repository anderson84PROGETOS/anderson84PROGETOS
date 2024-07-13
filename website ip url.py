import requests
from bs4 import BeautifulSoup
import re
import socket
from urllib.parse import urlparse

print("""

██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗    ██╗██████╗     ██╗   ██╗██████╗ ██╗     
██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝    ██║██╔══██╗    ██║   ██║██╔══██╗██║     
██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗      ██║██████╔╝    ██║   ██║██████╔╝██║     
██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝      ██║██╔═══╝     ██║   ██║██╔══██╗██║     
╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗    ██║██║         ╚██████╔╝██║  ██║███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝    ╚═╝╚═╝          ╚═════╝ ╚═╝  ╚═╝╚══════╝
                                                                                                                                                                                         
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
    # Definindo os cabeçalhos HTTP para a solicitação
    headers_global = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Solicitação HTTP para obter o conteúdo da página
    response = requests.get(url, headers=headers_global)

    # Verificação se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Parsing do conteúdo HTML com BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraindo todos os links (tags <a>)
        links = soup.find_all('a')
        
        # Conjunto para armazenar URLs únicas e seus IPs
        urls_unicas = set()
        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                urls_unicas.add(href)

        # Buscando URLs dentro de atributos 'content=' usando expressão regular
        content_urls = re.findall(r'content=["\'](https?://\S+?)(?=["\'])', str(soup))

        # Adicionando URLs encontradas em 'content=' ao conjunto de URLs únicas
        for url in content_urls:
            urls_unicas.add(url)

        # Imprimindo URLs únicas, seus IPs (se possível) e contando quantas foram encontradas
        print(f"\n\n\nForam encontradas {len(urls_unicas)} URL\n")
        main_site_ip = get_main_site_ip(url)
        for url in urls_unicas:
            try:
                ip = socket.gethostbyname(urlparse(url).netloc)
                print(f"\nIP: {ip}   \tURL:   {url}")
            except socket.gaierror:
                print(f"\nIP: Não encontrado  \tURL:   {url}")
        print(f"\nIP principal do site: {main_site_ip}")

        # Buscando e imprimindo subdomínios
        subdomains_info = search_subdomains(url, headers=headers_global)
        print(f"\n\nForam encontrados {len(subdomains_info)} subdomínios\n")
        for subdomain, ip in subdomains_info:
            print(f"\nIP: {ip}            \tSubdomínio:  {subdomain}")

    else:
        print(f"\nFalha ao acessar a página. Status code: {response.status_code}")

def search_subdomains(url, headers):
    if not url.startswith('http'):
        url = f'http://{url}'
    response = requests.get(url, headers=headers)
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
    # Solicita ao usuário a URL do website
    url = input("\nDigite a URL do website: ")
    extrair_dados(url)
    
    input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
