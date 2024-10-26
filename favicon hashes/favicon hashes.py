import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

print("""

███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗    ██╗  ██╗ █████╗ ███████╗██╗  ██╗███████╗███████╗
██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║    ██║  ██║██╔══██╗██╔════╝██║  ██║██╔════╝██╔════╝
█████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║    ███████║███████║███████╗███████║█████╗  ███████╗
██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║    ██╔══██║██╔══██║╚════██║██╔══██║██╔══╝  ╚════██║
██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║    ██║  ██║██║  ██║███████║██║  ██║███████╗███████║
╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
                                                                                                        
""")

def find_favicons(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    results = []  # Lista para armazenar os resultados

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicon_urls = set()

        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url:
                favicon_urls.add(urljoin(url, favicon_url))

        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url, headers=headers)

        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)

        if favicon_urls:
            for favicon_url in favicon_urls:
                print(f"Favicon Encontrado: {favicon_url}")
                response = requests.get(favicon_url, headers=headers)

                if response.status_code == 200:
                    favicon = response.content
                    favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                    result = (f"\nO hash do favicon do website: {favicon_url}      hash é: {favicon_hash}\n"
                              f"Link para pesquisa no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}\n"
                              f"http.favicon.hash:{favicon_hash}\n"
                              + "=" * 130)
                    print(result)
                    results.append(result)  # Armazena o resultado na lista
                else:
                    print(f"Não foi possível obter o favicon de {favicon_url}")
        else:
            print("Nenhum ícone encontrado.")
    except Exception as e:
        print(f"Erro ao buscar os ícones: {e}")

    return results  # Retorna os resultados coletados

def save_results(filename, results):
    try:
        with open(filename, 'w') as file:
            for result in results:
                file.write(result + "\n")
        print(f"\nAs informações foram salvas Em: {filename}")
    except Exception as e:
        print(f"\nErro ao salvar as informações: {e}")

if __name__ == "__main__":
    url = input("\nDigite a URL do website (ex: https://example.com): ")
    print("\n")
    results = find_favicons(url)

    if results:
        save_option = input("\nDeseja salvar as informações? (s/n): ").strip().lower()
        if save_option == 's':
            filename = input("\nDigite o nome do arquivo para salvar (ex: hash.txt): ")
            save_results(filename, results)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
