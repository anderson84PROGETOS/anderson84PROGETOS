import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import re
import socket
from urllib.parse import urlparse

# Cabeçalhos para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'application/json'
}

# Função para testar um link extraído do código fonte
def test_link(base_url, path, results):
    url = urljoin(base_url, path)
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            ip_address = socket.gethostbyname(urlparse(url).netloc)
            results.append((url, ip_address))
            print(f"URL: {url:<87}  |  IP: {ip_address}")
    except requests.exceptions.RequestException:
        pass

# Função para extrair todas as URLs do código fonte da página inicial
def get_all_links(base_url):
    try:
        response = requests.get(base_url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http://') or href.startswith('https://'):
                links.add(href)
            else:
                links.add(urljoin(base_url, href))
        return links
    except requests.exceptions.RequestException:
        return set()

# Função para gerar caminhos a partir das URLs extraídas
def scan_directories(base_url):
    links = get_all_links(base_url)
    print(f"\n\nForam Encontradas: {len(links)} URL\n")
    results = []
    threads = []
    for link in links:
        thread = threading.Thread(target=test_link, args=(base_url, link, results))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return results

# Função para obter o IP principal do site
def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address, main_site_domain

# Função para buscar subdomínios
def search_subdomains(url):
    if not url.startswith('http'):
        url = f'http://{url}'
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
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

# Função para salvar informações em um arquivo
def save_to_file(subdomains_info, scanned_links, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write("Subdomínios Encontrados\n")
        file.write(f"Total: {len(subdomains_info)}\n\n")
        for subdomain, ip_address in subdomains_info:
            file.write(f'{subdomain:<100}  IP:  {ip_address}\n')
        
        file.write("\nURL Escaneadas\n")
        file.write(f"Total: {len(scanned_links)}\n\n")
        for url, ip_address in scanned_links:
            file.write(f'{url:<100}  IP:  {ip_address}\n')

def main():
    url = input("\nDigite a URL do website: ")
    subdomains_info, main_site_domain = search_subdomains(url)
    print(f"\nForam Encontradas: {len(subdomains_info)} Subdomínio no website: {main_site_domain}\n")
    for subdomain, ip_address in subdomains_info:
        print(f"Subdomínio: {subdomain:<80}  |  IP: {ip_address}")
    
    scanned_links = scan_directories(url)
    
    while True:
        salvar = input("\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
        if salvar == "s":
            nome_arquivo = input("\nDigite o nome do arquivo para salvar as informações (ex: resultados.txt): ")
            if nome_arquivo.strip():
                save_to_file(subdomains_info, scanned_links, nome_arquivo)
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

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
