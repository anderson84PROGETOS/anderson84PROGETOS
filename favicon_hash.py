import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser

print("""\n
    
    ███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗    ██╗  ██╗ █████╗ ███████╗██╗  ██╗
    ██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║    ██║  ██║██╔══██╗██╔════╝██║  ██║
    █████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║    ███████║███████║███████╗███████║
    ██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║    ██╔══██║██╔══██║╚════██║██╔══██║
    ██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║    ██║  ██║██║  ██║███████║██║  ██║
    ╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                            
""") 

def find_favicon_urls(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicon_urls = set()

        # Procura por links de favicon no HTML
        for link in soup.find_all('link', rel='icon'):
            favicon_url = link.get('href')
            if favicon_url:
                favicon_urls.add(urljoin(url, favicon_url))

        # Procura por ícones no caminho padrão (/favicon.ico)
        default_favicon_url = urljoin(url, '/favicon.ico')
        default_favicon_response = requests.head(default_favicon_url)
        print(f"\nResposta HEAD para {default_favicon_url}     [{default_favicon_response.status_code}]")

        if default_favicon_response.status_code == 200:
            favicon_urls.add(default_favicon_url)

        return list(favicon_urls)
    except Exception as e:
        print(f"Erro ao buscar os ícones: {e}")
        return []

if __name__ == "__main__":
    site_url = input("\nDigite a URL do WebSite: ")
    favicon_urls = find_favicon_urls(site_url)

    if favicon_urls:
        print("\n ⬇️  Icones Encontrados ⬇️\n")
        for favicon_url in favicon_urls:
            print(favicon_url)
            
        for favicon_url in favicon_urls:
            # Obtém o favicon
            response = requests.get(favicon_url)

            # Calcula o hash do favicon
            if response.status_code == 200:
                favicon = codecs.encode(response.content, "base64")
                favicon_hash = mmh3.hash(favicon)
                print(f"\nO hash do favicon de {favicon_url} é: {favicon_hash}")

                print(f"\n[!] http.favicon.hash:{favicon_hash}")

                choice = input("\n\n\nDeseja abrir o link para a pesquisa no Shodan (s/n)? ").lower()
                if choice == 's':
                    print(f"\n[*] Abra o link para a pesquisa no Shodan:")
                    print(f"\n> https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}")
                    webbrowser.open(f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}")
                elif choice == 'n':
                    print(f"\n[*] Escolheu não abrir o link para o Shodan.")
                else:
                    print("\nEscolha inválida. Ignorando a abertura de links.")

            else:
                print(f"\nNão foi possível obter o favicon de {favicon_url}")

    else:
        print("\nNenhum Icone Encontrado")

input("\nFavion Terminado Aperte ENTER SAIR\n")
