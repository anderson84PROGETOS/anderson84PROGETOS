import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import mmh3
import codecs
import webbrowser
import pyperclip
import webbrowser

print(r"""                                             

███████╗██╗  ██╗ ██████╗ ██████╗  █████╗ ███╗   ██╗    ███████╗ █████╗ ██╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗
██╔════╝██║  ██║██╔═══██╗██╔══██╗██╔══██╗████╗  ██║    ██╔════╝██╔══██╗██║   ██║██║██╔════╝██╔═══██╗████╗  ██║
███████╗███████║██║   ██║██║  ██║███████║██╔██╗ ██║    █████╗  ███████║██║   ██║██║██║     ██║   ██║██╔██╗ ██║
╚════██║██╔══██║██║   ██║██║  ██║██╔══██║██║╚██╗██║    ██╔══╝  ██╔══██║╚██╗ ██╔╝██║██║     ██║   ██║██║╚██╗██║
███████║██║  ██║╚██████╔╝██████╔╝██║  ██║██║ ╚████║    ██║     ██║  ██║ ╚████╔╝ ██║╚██████╗╚██████╔╝██║ ╚████║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝                  
""")
print("")

def get_favicon_urls(url):
    # Fazer uma requisição HTTP à página web
    response = requests.get(url)

    # Analisar o HTML da página com a biblioteca BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontrar todos os links do favicon na tag <link>
    favicon_links = soup.find_all('link', rel='icon')

    # Obter os valores do atributo "href" de cada link do favicon
    favicon_urls = [link.get('href') for link in favicon_links]

    # Exibir os links dos favicons na janela
    if len(favicon_urls) > 0:
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        for url in favicon_urls:
            full_url = urljoin(base_url, url)
            print(full_url)
            get_hash(full_url)
    else:
        print('\nNenhum link de favicon encontrado.')

def get_hash(favicon_url):
    response = requests.get(favicon_url)
    if response.status_code == 200:
        favicon = codecs.encode(response.content, "base64")
        favicon_hash = mmh3.hash(favicon)

        print(f"\nO hash do favicon de {favicon_url} é: {favicon_hash}")
        print(f"\n[🔑] http.favicon.hash:{favicon_hash}")

        shodan_link = f"Resultados no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
        print(shodan_link)

    else:
        print(f"\nNão foi possível obter o favicon de {favicon_url}")

def open_shodan(favicon_hash):
    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
    webbrowser.open(shodan_url)
    print("\nVocê foi redirecionado para a pesquisa do Shodan")

def copy_results(result, http_hash, shodan_link):
    results = f"{result}\n{http_hash}\n{shodan_link}"
    pyperclip.copy(results)

if __name__ == "__main__":
    url = input("Digite a URL da página: ")
    print("\n")
    favicon_urls = get_favicon_urls(url)

# Acessar o Site do Shodan

shodan_url = 'https://www.shodan.io/search?query=http.favicon.hash%3A'

def open_shodan(hash):
    webbrowser.open(shodan_url + hash)

hash_input = input("\nDigite a hash do favicon: ")
button = input("\nClique Para Acessar o Site do Shodan\n")
open_shodan(hash_input)        

input("\nShodan Favicon [FIM ENTER SAIR]\n")    
