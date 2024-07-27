import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

print("""

████████╗ ██████╗  ██████╗ ██╗              ██╗███████╗     ██████╗███████╗███████╗    ██╗   ██╗██████╗ ██╗         
╚══██╔══╝██╔═══██╗██╔═══██╗██║              ██║██╔════╝    ██╔════╝██╔════╝██╔════╝    ██║   ██║██╔══██╗██║         
   ██║   ██║   ██║██║   ██║██║              ██║███████╗    ██║     ███████╗███████╗    ██║   ██║██████╔╝██║         
   ██║   ██║   ██║██║   ██║██║         ██   ██║╚════██║    ██║     ╚════██║╚════██║    ██║   ██║██╔══██╗██║         
   ██║   ╚██████╔╝╚██████╔╝███████╗    ╚█████╔╝███████║    ╚██████╗███████║███████║    ╚██████╔╝██║  ██║███████╗    
   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝     ╚════╝ ╚══════╝     ╚═════╝╚══════╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚══════╝    
                                                                                                                    
""")

def find_resources_urls(url):
    try:
        # Cabeçalhos personalizados para evitar erros 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        # Faz a requisição HTTP GET para a URL fornecida com cabeçalhos personalizados
        response = requests.get(url, headers=headers)

        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            js_urls = set()
            css_urls = set()
            img_urls = set()
            ico_urls = set()  # URLs que terminam com .ico
            php_urls = set()
            other_urls = set()

            # Encontra todos os elementos <script>, <link>, <a>, <img> e o favicon na página
            for script in soup.find_all('script', {'src': True}):
                js_url = script['src']
                js_full_url = urljoin(url, js_url)
                js_urls.add(js_full_url)

            for link in soup.find_all('link', {'href': True}):
                css_url = link['href']
                css_full_url = urljoin(url, css_url)
                css_urls.add(css_full_url)

            for anchor in soup.find_all('a', {'href': True}):
                href_url = anchor['href']
                if href_url.endswith('.php'):
                    php_full_url = urljoin(url, href_url)
                    php_urls.add(php_full_url)
                else:
                    other_urls.add(href_url)

            for img in soup.find_all('img', {'src': True}):
                img_url = img['src']
                img_full_url = urljoin(url, img_url)
                img_urls.add(img_full_url)

            # Encontra o favicon
            favicon_link = soup.find('link', rel='icon')
            if favicon_link:
                favicon_url = favicon_link.get('href', '')
                favicon_full_url = urljoin(url, favicon_url)
                ico_urls.add(favicon_full_url)

            return js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls

        else:
            print(f"\nErro {response.status_code} ao acessar: {url}")
            return set(), set(), set(), set(), set(), set()

    except requests.exceptions.RequestException as e:
        print(f"\nErro ao fazer requisição para {url}: {e}")
        return set(), set(), set(), set(), set(), set()

# Exemplo de uso:
if __name__ == "__main__":
    website_url = input("\nDigite a URL do website: ")
    js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls = find_resources_urls(website_url)

    if js_urls or css_urls or img_urls or ico_urls or php_urls or other_urls:
        print(f"\n\nURLs Encontradas no Website: {website_url}\n\n")

        if js_urls:
            print(f"Total de URL de Arquivos JavaScript js: {len(js_urls)}")
            print("\nURL de Arquivos JavaScript\n==========================")
            for js_url in js_urls:
                print(js_url)

        if css_urls:
            print(f"\n\nTotal de URL de Arquivos CSS: {len(css_urls)}")
            print("\nURL de Arquivos CSS\n===================")
            for css_url in css_urls:
                print(css_url)

        if img_urls:
            print(f"\n\nTotal de URL de Imagens: {len(img_urls)}")
            print("\nURL de Imagens\n==============")
            for img_url in img_urls:
                print(img_url)

        if ico_urls:
            print(f"\n\nTotal de URL de Arquivos ICO e Favicon: {len(ico_urls)}")
            print("\nURL de Arquivos ICO e Favicon\n=============================")
            for ico_url in ico_urls:
                print(ico_url)

        if php_urls:
            print(f"\n\nTotal de URL de Arquivos PHP: {len(php_urls)}")
            print("\nURL de Arquivos PHP\n===================")
            for php_url in php_urls:
                print(php_url)

        if other_urls:
            print(f"\n\nTotal de Outros URL: {len(other_urls)}")
            print("\nOutros URL\n==========")
            for other_url in other_urls:
                print(other_url)
    else:
        print("\nNenhuma URL de recurso encontrada.")

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
