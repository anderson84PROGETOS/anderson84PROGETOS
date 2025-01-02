import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗    ██╗  ██╗ █████╗ ███████╗██╗  ██╗
██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║    ██║  ██║██╔══██╗██╔════╝██║  ██║
█████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║    ███████║███████║███████╗███████║
██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║    ██╔══██║██╔══██║╚════██║██╔══██║
██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║    ██║  ██║██║  ██║███████║██║  ██║
╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
""")

def find_favicons_and_hashes(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicon_urls = set()

        # Coleta URLs de favicons
        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url and (favicon_url.endswith('.ico') or favicon_url.endswith('.png')):
                favicon_urls.add(urljoin(url, favicon_url))

        # Verifica o favicon padrão em /favicon.ico
        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url, headers=headers)
        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)

        result_text = ""
        if favicon_urls:
            print("\n\nFavicons URL Encontradas\n")
            result_text += "Favicons URL Encontradas\n"
            for favicon_url in favicon_urls:
                print(Fore.LIGHTWHITE_EX + favicon_url)
                result_text += f"\n\n{favicon_url}\n"                

                # Verifica o hash do favicon
                response = requests.get(favicon_url, headers=headers)
                if response.status_code == 200:
                    favicon = response.content
                    favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                    print(Fore.LIGHTGREEN_EX + f"\nHash do favicon do website: {favicon_url} " + Fore.LIGHTYELLOW_EX + f"   http.favicon.hash:{favicon_hash}")
                    result_text += f"\nHash do favicon do website: {favicon_url}    http.favicon.hash:{favicon_hash}\n"

                    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                    print(Fore.LIGHTMAGENTA_EX + f"\nLink para pesquisa no Shodan: {shodan_url}\n")
                    result_text += f"\nLink para pesquisa no Shodan: {shodan_url}\n"
                    result_text += f"\nhttp.favicon.hash:{favicon_hash}\n==============================\n"
                    print(Fore.LIGHTRED_EX + f"http.favicon.hash:{favicon_hash}\n\n")

                    # Pergunta ao usuário se deseja abrir o link do Shodan
                    open_shodan = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDeseja abrir o link do Shodan? (s/n): ")
                    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "======================================================\n\n")
                    if open_shodan.lower() == 's':
                        webbrowser.open(shodan_url)

                else:
                    print(f"\nNão foi possível obter o conteúdo de {favicon_url}")
                    result_text += f"\nErro ao obter o favicon: {favicon_url}\n"

            # Pergunta se o usuário deseja salvar os resultados em um arquivo
            save_results = input(Fore.LIGHTRED_EX + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ")
            if save_results.lower() == 's':
                filename = input("\nDigite o nome do arquivo (exemplo: resultados.txt): ")
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(result_text)
                print(f"\nResultados salvos em: {filename}")
        else:
            print("\nNenhum favicon .ico ou .png encontrado.")
    except Exception as e:
        print(f"\nErro ao buscar os favicons: {e}")

def main():    
    url = input(Fore.LIGHTMAGENTA_EX + "\nDigite a URL do website (exemplo: http://example.com): ")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    
    find_favicons_and_hashes(url)

if __name__ == "__main__":
    main()

input(Fore.LIGHTMAGENTA_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
