import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

print("""

██╗     ██╗███╗   ██╗██╗  ██╗     ██████╗  ██████╗ ██████╗ ██╗  ██╗███████╗██████╗ 
██║     ██║████╗  ██║██║ ██╔╝    ██╔════╝ ██╔═══██╗██╔══██╗██║  ██║██╔════╝██╔══██╗
██║     ██║██╔██╗ ██║█████╔╝     ██║  ███╗██║   ██║██████╔╝███████║█████╗  ██████╔╝
██║     ██║██║╚██╗██║██╔═██╗     ██║   ██║██║   ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
███████╗██║██║ ╚████║██║  ██╗    ╚██████╔╝╚██████╔╝██║     ██║  ██║███████╗██║  ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝     ╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                   
""")

def capturar_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = set()
    # Encontrar URLs nos atributos 'href' das tags <a>
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href.startswith('http') or href.startswith('https'):
            urls.add(href)
    # Encontrar URLs dentro do atributo 'content' com o valor 'onion-location'
    onion_urls = re.findall(r'onion-location"\s+content="(https?://\S+)"', str(soup))
    urls.update(onion_urls)
    # Encontrar URLs onion dentro do conteúdo da página
    onion_urls_content = re.findall(r'(https?://\w+\.onion\S*)', str(soup))
    urls.update(onion_urls_content)
    return list(urls)

def get_links(url):
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
        headers = {'User-Agent': user_agent}
        response = requests.get(url, headers=headers)
        links = capturar_urls(response.text)
        return links
    except Exception as e:
        print("Erro ao obter links:", e)
        return []

def get_domains(links):
    domains = set()
    for link in links:
        domain = urlparse(link).netloc
        domains.add(domain)
    return domains

def save_to_file(file_name, content):
    try:
        with open(file_name, 'w') as file:
            file.write(content)
        print(f"\nConteúdo salvo com sucesso no arquivo: {file_name}")
    except Exception as e:
        print("Erro ao salvar o conteúdo no arquivo:", e)

def main():
    url = input("\nDigite a URL do website: ")
    links = get_links(url)
    domains = get_domains(links)

    print("\n\nLinks encontrados:", len(links))
    print()
    for link in links:
        print(link)

    print("\n\nDomínios encontrados:", len(domains))
    print()
    for domain in domains:
        print(domain)

    save_file = input("\nDeseja salvar os links e domínios em um arquivo de texto? (s/n): ").lower()
    if save_file == 's':
        file_name = input("\nDigite o nome do arquivo: ")
        content = f"Links encontrados ({len(links)}):\n\n" + '\n\n'.join(links) + \
                  f"\n\n\n\nDominios encontrados ({len(domains)}):\n\n" + '\n'.join(domains)
        save_to_file(file_name, content)

if __name__ == "__main__":
    main()

input("\n\n\n\n🎯 Pressione Enter para sair 🎯\n\n")
