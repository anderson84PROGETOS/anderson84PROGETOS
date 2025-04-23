import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner ASCII
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗    ██╗  ██╗ █████╗ ███████╗██╗  ██╗
██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║    ██║  ██║██╔══██╗██╔════╝██║  ██║
█████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║    ███████║███████║███████╗███████║
██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║    ██╔══██║██╔══██║╚════██║██╔══██║
██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║    ██║  ██║██║  ██║███████║██║  ██║
╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
""")

def find_favicons(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    try:
        # Faz a requisição inicial para a URL
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicon_urls = set()
        
        # Busca por links de favicon na página
        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url:
                favicon_urls.add(urljoin(url, favicon_url))
        
        # Verifica o favicon padrão (/favicon.ico)
        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url, headers=headers)
        
        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)
        
        # Processa os favicons encontrados
        if favicon_urls:
            result_text = ""
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nFavicons Encontrados\n")
           
            result_text += "Favicons Encontrados\n"
            result_text += "===========================================================================================================\n"
            
            for favicon_url in favicon_urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Favicons URL Encontradas Para: {favicon_url}")
                result_text += f"\nFavicons URL Encontradas Para: {favicon_url}\n"
                
                response = requests.get(favicon_url, headers=headers)
                
                if response.status_code == 200:
                    favicon = response.content
                    favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nHash do favicon: {favicon_hash}\n")
                    result_text += f"\nHash do favicon: {favicon_hash}\n"
                    
                    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Link para pesquisa no Shodan: {shodan_url}")
                    result_text += f"\nLink para pesquisa no Shodan: {shodan_url}\n"
                    
                    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nhttp.favicon.hash:{favicon_hash}\n")
                    result_text += f"\nhttp.favicon.hash:{favicon_hash}\n"
                    
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "===========================================================================================================\n")
                    result_text += "===========================================================================================================\n"
                    
                    # Pergunta se deseja abrir o Shodan
                    open_shodan = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDeseja abrir o link do Shodan? (s/n): ")
                    print("\n")
                    if open_shodan.lower() == 's':
                        webbrowser.open(shodan_url)
                else:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNão foi possível obter o favicon de {favicon_url}\n")
                    result_text += f"\nNão foi possível obter o favicon de {favicon_url}\n"
            
            # Pergunta se deseja salvar os resultados
            save = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDeseja salvar os resultados em um arquivo? (s/n): ").lower()
            if save == 's':
                filename = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo (ex: resultado.txt): ")
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(result_text)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {filename}")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum favicon encontrado\n")
            
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao buscar favicons: {e}\n")

def main():
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website (exemplo: http://example.com): ")
    
    if not url.startswith('http'):
        url = 'http://' + url
    
    find_favicons(url)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
