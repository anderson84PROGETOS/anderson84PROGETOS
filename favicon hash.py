import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser

print("""

███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗    ██╗  ██╗ █████╗ ███████╗██╗  ██╗
██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║    ██║  ██║██╔══██╗██╔════╝██║  ██║
█████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║    ███████║███████║███████╗███████║
██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║    ██╔══██║██╔══██║╚════██║██╔══██║
██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║    ██║  ██║██║  ██║███████║██║  ██║
╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                                
""")

print("\nExemplo: http.favicon.hash:-1353760233\n======================================\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def find_favicon_urls(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicon_urls = set()

        # Procura por links de favicon no HTML
        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url:
                favicon_urls.add(urljoin(url, favicon_url))

        # Procura por ícones no caminho padrão (/favicon.ico)
        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url, headers=headers)
        print(f"\n\nResposta HEAD para website: {default_favicon_url}     [{default_favicon_response.status_code}]\n\n")

        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)

        return list(favicon_urls)
    except Exception as e:
        print(f"Erro ao buscar os ícones: {e}")
        return []

if __name__ == "__main__":
    site_url = input("\nDigite a URL do WebSite: ")
    favicon_urls = find_favicon_urls(site_url)
    hashes = []

    if favicon_urls:
        print("\nIcones Encontrados Favicon\n==========================\n")
        for favicon_url in favicon_urls:
            print(favicon_url)

        for favicon_url in favicon_urls:
            # Obtém o favicon
            response = requests.get(favicon_url, headers=headers)

            # Calcula o hash do favicon
            if response.status_code == 200:
                favicon = response.content
                favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                hashes.append((favicon_url, favicon_hash))
                print(f"\n\nO hash do favicon do website: {favicon_url} é: {favicon_hash}")
                print(f"\nhttp.favicon.hash:{favicon_hash}\n")

                print(f"\n\nLink para pesquisa no Shodan\n============================")
                shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                print(shodan_url)

                choice = input("\n\n\nDeseja abrir o link para a pesquisa no Shodan (s/n): ").lower()
                if choice == 's':
                    print(f"\n[*] Abrindo link para a pesquisa no Shodan")
                    webbrowser.open(shodan_url)
                elif choice == 'n':
                    print("\nEscolheu não abrir o link para o Shodan.")
                else:
                    print("\nEscolha inválida. Ignorando a abertura de links.")

            else:
                print(f"\nNão foi possível obter o favicon de {favicon_url}")

        save_choice = input("\n\n\nDeseja salvar as hashes e links Encontrados no Arquivo (s/n): ").lower()
        if save_choice == 's':
            file_name = input("\nDigite o nome do arquivo (ex: arquivo.txt): ")
            try:
                with open(file_name, 'w') as file:
                    for favicon_url, favicon_hash in hashes:
                        shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                        file.write(f"URL: {favicon_url}\nHash: http.favicon.hash:{favicon_hash}\n\nLink para pesquisa no Shodan\n============================\n{shodan_url}\n\n\n\n\n\n")
                print(f"\nAs informações foram salvas no arquivo: {file_name}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
        elif save_choice == 'n':
            print("\nEscolheu não salvar as informações.")
        else:
            print("\nEscolha inválida. Ignorando o salvamento das informações.")

    else:
        print("\nNenhum Icone Encontrado")

input("\n\nFavion Terminado Aperte ENTER SAIR\n==================================\n\n")
