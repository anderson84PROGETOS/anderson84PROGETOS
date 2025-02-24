import requests
import urllib.parse
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗   ██╗██████╗ ██╗         ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
██║   ██║██╔══██╗██║         ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
██║   ██║██████╔╝██║         ███████╗█████╗  ███████║██████╔╝██║     ███████║
██║   ██║██╔══██╗██║         ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
╚██████╔╝██║  ██║███████╗    ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
                                                                            
""")

def process_url():
    user_url = input(Fore.LIGHTMAGENTA_EX + "Digite a URL do Website: ").strip()
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url

    # Perguntar quantas URLs o usuário deseja encontrar
    max_urls = input(Fore.LIGHTMAGENTA_EX + "\nQuantas URL deseja Encontrar (Exemplo: 100): ").strip()
    try:
        max_urls = int(max_urls)
    except ValueError:
        print(Fore.RED + "Por favor, insira um número válido.")
        return

    urls = deque([user_url])
    scrapped_urls = set()
    print(Fore.LIGHTRED_EX + "\nEscaneando, aguarde...\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    while urls and len(scrapped_urls) < max_urls:  # Adicionando limite de URLs
        url = urls.popleft()

        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            continue
        except KeyboardInterrupt:
            print(Fore.RED + "[-] Encerrando!")
            break

        if url not in scrapped_urls:
            scrapped_urls.add(url)
            print(Fore.LIGHTYELLOW_EX + f"\n{len(scrapped_urls)} = {url}")

        # Verificar o tipo de conteúdo antes de tentar analisar
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Encontrando URLs em tags <a>
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup.find_all("a", href=True):
                full_url = urljoin(url, tag["href"])
                if full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                    urls.append(full_url)
            
            # Encontrando URLs em <meta http-equiv="onion-location">
            for meta_tag in soup.find_all("meta", attrs={"http-equiv": "onion-location"}):
                meta_url = meta_tag.get("content")
                if meta_url and meta_url.startswith(("http://", "https://")) and meta_url not in scrapped_urls:
                    scrapped_urls.add(meta_url)
                    print(Fore.LIGHTGREEN_EX + f"\n{len(scrapped_urls)} = {meta_url}")
                    urls.append(meta_url)
        else:
            print(Fore.LIGHTRED_EX + f"\n[!] Ignorando URL (não HTML): {url}")
    
    print(Fore.LIGHTCYAN_EX + '\n################## RESULTADOS ######################')
    print(Fore.LIGHTCYAN_EX + f'\nTotal de URL encontradas: {len(scrapped_urls)}')

    save = input(Fore.LIGHTMAGENTA_EX + "\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
    if save == 's':
        file_name = input(Fore.LIGHTMAGENTA_EX + "\nDigite o nome do arquivo para salvar (exemplo: urls.txt): ").strip()
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write("################## RESULTADOS ######################\n")
                f.write(f"\nTotal de URL encontradas: {len(scrapped_urls)}\n\n")
                for i, url in enumerate(sorted(scrapped_urls), 1):
                    f.write(f"{i} = {url}\n")
            print(Fore.LIGHTGREEN_EX + f"\nInformações salvas com sucesso no arquivo: {file_name}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    process_url()

input(Fore.LIGHTMAGENTA_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================")
