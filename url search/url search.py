import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTBLUE_EX + """

██╗   ██╗██████╗ ██╗         ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗    
██║   ██║██╔══██╗██║         ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║    
██║   ██║██████╔╝██║         ███████╗█████╗  ███████║██████╔╝██║     ███████║    
██║   ██║██╔══██╗██║         ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║    
╚██████╔╝██║  ██║███████╗    ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║    
 ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    
                                                                             
""")

def encontrar_urls(website_url):
    try:
        # Fazendo a solicitação HTTP
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'application/json'
        }
        resposta = requests.get(website_url, headers=headers, timeout=10)
        resposta.raise_for_status()

        # Analisando o HTML
        soup = BeautifulSoup(resposta.text, "html.parser")
        urls = set()

        # Encontrando URLs em tags <a>
        for tag in soup.find_all("a", href=True):
            url = urljoin(website_url, tag["href"])
            if url.startswith("http"):
                urls.add(url)

        # Encontrando URLs em tags <meta>
        for meta_tag in soup.find_all("meta"):
            if meta_tag.get("content"):
                meta_url = meta_tag.get("content")
                if meta_url.startswith("http"):
                    urls.add(meta_url)

        return urls
    except requests.RequestException as e:
        print(f"\nErro ao acessar o site: {e}")
        return set()

def main():
    website = input("\nDigite a URL do website (exemplo: https://example.com): ").strip()
    urls_encontradas = encontrar_urls(website)
    
    if urls_encontradas:
        print(f"\n\n{Fore.LIGHTMAGENTA_EX}URL únicas Encontradas no site: {website}{Style.RESET_ALL}\n")
        print(f"\n{Fore.LIGHTRED_EX}Total de URL únicas Encontradas: {len(urls_encontradas)}{Style.RESET_ALL}\n")
        for url in sorted(urls_encontradas):
            print("\n",url)        
    else:
        print("\nNenhuma URL encontrada ou erro na solicitação.")

if __name__ == "__main__":
    main()

input(Fore.LIGHTBLUE_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
