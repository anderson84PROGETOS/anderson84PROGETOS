import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

print("""

██████╗  ██████╗ ██████╗  ██████╗ ████████╗███████╗   ████████╗██╗  ██╗████████╗
██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝   ╚══██╔══╝╚██╗██╔╝╚══██╔══╝
██████╔╝██║   ██║██████╔╝██║   ██║   ██║   ███████╗      ██║    ╚███╔╝    ██║   
██╔══██╗██║   ██║██╔══██╗██║   ██║   ██║   ╚════██║      ██║    ██╔██╗    ██║   
██║  ██║╚██████╔╝██████╔╝╚██████╔╝   ██║   ███████║██╗   ██║   ██╔╝ ██╗   ██║   
╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   
                                                                                                                                                                            
""")

# Cabeçalhos personalizados para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_links(url):
    try:
        # Faz a requisição para o site
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verifica se houve erros na requisição

        # Parse do conteúdo HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontra todos os elementos <a> e extrai os links completos, sem duplicatas
        links = {urljoin(url, a['href']) for a in soup.find_all('a', href=True)}  # Usando set para remover duplicatas

        # Encontra todas as tags <meta> e extrai o conteúdo dos atributos "content"
        meta_contents = [meta.get('content') for meta in soup.find_all('meta') if meta.get('content')]

        return links, meta_contents

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o site: {e}")
        return set(), []

def get_robots_txt(url):
    try:
        # Constrói a URL para o arquivo robots.txt
        robots_url = urljoin(url, '/robots.txt')
        response = requests.get(robots_url, headers=headers)
        response.raise_for_status()  # Verifica se houve erros na requisição

        # Processa o conteúdo do robots.txt e extrai URLs completas, sem duplicatas
        robots_lines = response.text.splitlines()
        urls_in_robots = set()  # Usa um set para evitar duplicatas

        for line in robots_lines:
            if line.startswith('Allow:') or line.startswith('Disallow:'):
                # Extrai o caminho após 'Allow:' ou 'Disallow:'
                path = line.split(':', 1)[1].strip()
                if path:
                    # Cria a URL completa usando urljoin
                    full_url = urljoin(url, path)
                    urls_in_robots.add(full_url)  # Adiciona ao set

        return response.text, urls_in_robots

    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o robots.txt: {e}", set()

# Solicita ao usuário a URL
url = input("Digite a URL do website: ")
links, meta_contents = get_links(url)
robots_content, robots_urls = get_robots_txt(url)

# Exibe URLs completas encontradas no robots.txt, sem duplicatas
print(f"\n\nURL Encontradas no robots.txt: {len(robots_urls)}\n")
for robots_url in sorted(robots_urls):  # Ordena as URLs para melhor apresentação
    print(f" {robots_url}")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
