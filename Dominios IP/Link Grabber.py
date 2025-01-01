import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import Fore, Style, init

# Inicializando o colorama (sem o autoreset)
init()

print(Fore.LIGHTBLUE_EX + """

██╗     ██╗███╗   ██╗██╗  ██╗     ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ███████╗██████╗ 
██║     ██║████╗  ██║██║ ██╔╝    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║     ██║██╔██╗ ██║█████╔╝     ██║  ███╗██████╔╝███████║██████╔╝██████╔╝█████╗  ██████╔╝
██║     ██║██║╚██╗██║██╔═██╗     ██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══╝  ██╔══██╗
███████╗██║██║ ╚████║██║  ██╗    ╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                                                                                               
""")

def extract_links(url):
    try:
        # Enviar a solicitação para o site
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verificar se houve algum erro
        
        # Fazer o parse do HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Conjunto para armazenar URLs únicas
        urls = set()

        # Encontrando URLs em tags <a>
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  # Resolver URLs relativas
            if full_url.startswith("http"):
                urls.add(full_url)

        # Encontrando URLs em tags <meta>
        for meta_tag in soup.find_all("meta"):
            if meta_tag.get("content"):
                meta_url = meta_tag.get("content")
                if meta_url.startswith("http"):
                    urls.add(meta_url)
        
        return urls
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o site: {e}")
        return set()

if __name__ == "__main__":
    website_url = input(f"\n{Fore.LIGHTCYAN_EX}Digite a URL do Website (exemplo: https://example.com): ")
    links = extract_links(website_url)
    
    # Ordenando os links em ordem alfabética
    sorted_links = sorted(links)
    
    # Exibir os links no terminal com cor
    print(f"\n\n{Fore.LIGHTRED_EX}links Encontrados: {len(sorted_links)} \n")
    for link in sorted_links:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n",link)

input(Fore.LIGHTBLUE_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
