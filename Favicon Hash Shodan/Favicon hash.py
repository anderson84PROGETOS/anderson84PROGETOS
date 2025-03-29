import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser

from colorama import init, Fore, Style
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

        # Coleta URLs de favicons (terminando em .ico ou .png)
        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url and (favicon_url.endswith('.ico') or favicon_url.endswith('.png')):
                favicon_urls.add(urljoin(url, favicon_url))

        # Verifica o favicon padrão em /favicon.ico
        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url, headers=headers)
        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)

        if favicon_urls:
            result_text = ""
            for favicon_url in favicon_urls:
                # Cabeçalho ajustado para mostrar o favicon específico
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nFavicons URL Encontradas Para: {favicon_url}\n") 
                result_text += f"===========================================================================================================================\n"            
                result_text += f"URL do favicon: {favicon_url}\n"

                # Verifica o hash do favicon
                response = requests.get(favicon_url, headers=headers)
                if response.status_code == 200:
                    favicon = response.content
                    favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nHash do favicon do website: {favicon_url:<50} HASH é: {favicon_hash}")
                    result_text += f"\nHash do favicon do website: {favicon_url:<50} HASH é: {favicon_hash}\n\n"                    

                    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nLink para pesquisa no Shodan: {shodan_url}\n")
                    result_text += f"Link para pesquisa no Shodan: {shodan_url}\n\n"
                    result_text += f"http.favicon.hash:{favicon_hash}\n\n"
                    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"http.favicon.hash:{favicon_hash}\n\n")
                    
                    # Pergunta ao usuário se deseja abrir o link do Shodan
                    open_shodan = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Deseja abrir o link do Shodan? (s/n): ")
                    print(Fore.YELLOW + "========================================\n")
                    if open_shodan.lower() == 's':
                        webbrowser.open(shodan_url)

                else:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNão foi possível obter o conteúdo de {favicon_url}")
                    result_text += f"\nErro ao obter o favicon: {favicon_url}\n"

            # Pergunta se o usuário deseja salvar os resultados em um arquivo
            save_results = input(Fore.LIGHTGREEN_EX + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ")
            if save_results.lower() == 's':
                filename = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo (exemplo: resultados.txt): ")
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(result_text)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos Em: {filename}")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum favicon .ico ou .png encontrado.")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao buscar os favicons: {e}")

def main():    
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website (exemplo: http://businesscorp.com.br): ")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    
    find_favicons_and_hashes(url)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
