import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from tqdm import tqdm
import time

print("""

██╗     ██╗███╗   ██╗██╗  ██╗     ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ███████╗██████╗ 
██║     ██║████╗  ██║██║ ██╔╝    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║     ██║██╔██╗ ██║█████╔╝     ██║  ███╗██████╔╝███████║██████╔╝██████╔╝█████╗  ██████╔╝
██║     ██║██║╚██╗██║██╔═██╗     ██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══╝  ██╔══██╗
███████╗██║██║ ╚████║██║  ██╗    ╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                          
""")

def get_all_urls(base_url, method):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.request(method, base_url, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx ou 5xx)
    except requests.RequestException as e:
        print(f"\nError with {method} request: {e}")
        return set()

    soup = BeautifulSoup(response.content, 'html.parser')
    
    urls = set()
    
    # Busca por tags que podem conter URLs
    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        url = tag.get('href') or tag.get('src')
        if url:
            full_url = urljoin(base_url, url)
            urls.add(full_url)
    
    # Busca por atributos específicos 'href' e 'content' que começam com 'http' ou 'https'
    for tag in soup.find_all(True, {'href': lambda x: x and x.startswith(('http://', 'https://')), 'content': lambda x: x and (x.startswith('http://') or x.startswith('https://'))}):
        url = tag.get('href') or tag.get('content')
        if url:
            urls.add(url)
    
    # Extração de URLs do atributo 'content'
    content_urls = re.findall(r'(?<=content=["\'])https?://[^"\']+|(?<=content=["\'])[^"\']+', response.text)
    for content_url in content_urls:
        normalized_url = normalize_url(content_url, base_url)
        if normalized_url:
            urls.add(normalized_url)
    
    return urls

def normalize_url(url, base_url):
    return urljoin(base_url, url)

def main():
    base_url = input("\nDigite a URL do website: ")
    if not base_url:
        print("\nURL inválida. Saindo...")
        return
    
    # Obtendo as URLs
    print("\nExtraindo URL\n")
    urls = get_all_urls(base_url, 'GET')
    
    # Exibir barra de progresso
    with tqdm(total=len(urls), desc="Progresso", unit="URL", ncols=90) as pbar:
        for url in urls:
            pbar.update(1)  # Atualiza a barra de progresso

    # Atraso de 3 segundos antes de mostrar os resultados
    time.sleep(3)

    # Exibir resultados
    print(f"\nURL Encontradas para: {base_url} ({len(urls)} URL Encontradas)\n")
    for url in urls:
        print("\n", url)

    # Pergunta se o usuário deseja salvar os resultados
    save_option = input("\n\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if save_option == 's':
        file_name = input("\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
        try:
            with open(file_name, 'w') as file:
                # Escreve a mensagem no arquivo
                file.write(f"URL Encontradas para: {base_url} ({len(urls)} URL Encontradas)\n\n")
                for url in urls:
                    file.write(url + '\n\n')  # Cada URL em uma nova linha
            print(f"\nResultados salvos em: {file_name}")
        except Exception as e:
            print(f"\nErro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
