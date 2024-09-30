import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

print("""

██╗    ██╗███████╗██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██║    ██║██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══╝  ██╔══██╗    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝███████╗██████╔╝    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                     
""")

# Função para extrair URLs de uma página HTML, incluindo URLs dentro do código-fonte
def extract_urls(base_url, html):
    soup = BeautifulSoup(html, 'html.parser')
    urls = set()  # Usando set para garantir que não haja URLs duplicadas

    # Extraindo URLs a partir dos links (tag <a>)
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        # Filtros básicos para remover âncoras e outros links irrelevantes
        if parsed_url.scheme in ['http', 'https'] and not parsed_url.path.endswith('.jpg') and not parsed_url.path.endswith('.png'):
            urls.add(full_url)

    # Extraindo URLs presentes no código-fonte da página (em texto ou scripts)
    url_pattern = r'https?://[a-zA-Z0-9./?=_-]+'
    found_urls_in_code = re.findall(url_pattern, html)
    
    for url in found_urls_in_code:
        parsed_url = urlparse(url)
        # Filtros para URLs válidas (não duplicadas e removendo imagens)
        if parsed_url.scheme in ['http', 'https'] and not parsed_url.path.endswith('.jpg') and not parsed_url.path.endswith('.png'):
            urls.add(url)
    
    return urls

# Função principal para fazer o scraping
def scrape_website(url):
    try:
        # Cabeçalhos HTTP para evitar erro 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        # Fazer a requisição HTTP
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            html_content = response.text

            # Extração de URLs
            urls = extract_urls(url, html_content)

            # Exibindo resultados
            print(f"\n\nTotal de URL encontradas: {len(urls)}\n")
            for found_url in urls:
                print(found_url)

            # Pergunta ao usuário se deseja salvar os resultados em um arquivo
            save_option = input("\n\nDeseja salvar os resultados (s/n): ").lower()

            if save_option == 's':
                # Pergunta o nome do arquivo ao usuário
                file_name = input("\nDigite o nome do arquivo (ex: resultados.txt): ")
                
                if not file_name.endswith('.txt'):
                    file_name += '.txt'

                # Salvando em um arquivo
                with open(file_name, "w") as file:
                    file.write(f"Total de URL encontradas: {len(urls)}\n\n")
                    for found_url in urls:
                        file.write(found_url + "\n\n")

                print(f"\nResultados salvos Em: {file_name}")
            else:
                print("\nOs resultados não foram salvos")
        else:
            print(f"\nErro ao acessar {url}: Código de status {response.status_code}")
    except Exception as e:
        print(f"\nErro ao acessar {url}: {str(e)}")

# Solicita o URL ao usuário
if __name__ == "__main__":  
    site_url = input("\nDigite o URL do site para fazer scraping: ")
    scrape_website(site_url)
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
