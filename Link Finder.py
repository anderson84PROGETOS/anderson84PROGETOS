import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

print("""

██╗     ██╗███╗   ██╗██╗  ██╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║     ██║████╗  ██║██║ ██╔╝    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║     ██║██╔██╗ ██║█████╔╝     █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║     ██║██║╚██╗██║██╔═██╗     ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
███████╗██║██║ ╚████║██║  ██╗    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                             
""")

def cria_lista_links(url, content):
    soup = BeautifulSoup(content, 'html.parser')
    links = set()

    # Encontrar URLs em atributos comuns
    for tag in soup.find_all(True):  # True encontra todas as tags
        for attribute in ['href', 'src', 'action']:
            if tag.has_attr(attribute):
                link = tag[attribute]
                # Normaliza e substitui '#' por '/'
                link = link.replace('#', '/')
                full_url = urljoin(url, link)
                links.add(full_url)
    
    # Encontrar URLs em atributos menos comuns
    for meta_tag in soup.find_all('meta', content=True):
        content = meta_tag.get('content', '')
        # Adicionar URLs do conteúdo da tag meta
        urls_in_content = re.findall(r'http[s]?://[^\s\'"]+', content)
        for url_in_content in urls_in_content:
            full_url = urljoin(url, url_in_content)
            links.add(full_url)

    return links

def salvar_resultados(links):
    print("\n============================================")    
    # Solicitar ao usuário se deseja salvar os resultados
    salvar = input("\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if salvar == 's':
        nome_arquivo = input("\nDigite o nome do arquivo (exemplo: exemplo.txt): ").strip()
        try:
            with open(nome_arquivo, 'w') as f:
                total_urls = len(links)
                f.write(f"Total de URL Encontradas: {total_urls}\n\n")
                for link in links:
                    f.write(link + '\n\n')
            print(f"\nResultados salvos Em: {nome_arquivo}")
            print(f"\nTotal de URL salvas: {total_urls}")  # Exibir o número de URLs salvas
        except IOError as e:
            print(f"\nOcorreu um erro ao salvar o arquivo: {e}")

# Solicitar ao usuário a URL do website
url = input("\nDigite a URL do website: ")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

try:
    # Realizando a solicitação e processando a resposta
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r_content = r.text  # Decodifica os bytes em texto
    links = cria_lista_links(url, r_content)
    if links:
        print(f"\n\nTotal de URL Encontradas: {len(links)}\n")
        print('\n\n'.join(links))
        salvar_resultados(links)
    else:
        print("\nNenhum link encontrado.")
except requests.RequestException as e:
    print(f"\nOcorreu um erro ao acessar a URL: {e}")

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
