import requests
import urllib.parse
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗ ██████╗ ███████╗    ███████╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗
██╔══██╗██╔══██╗██╔════╝    ██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝
██████╔╝██║  ██║█████╗      █████╗   ╚███╔╝    ██║   ██████╔╝███████║██║        ██║   
██╔═══╝ ██║  ██║██╔══╝      ██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║   
██║     ██████╔╝██║         ███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║   
╚═╝     ╚═════╝ ╚═╝         ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝   
                                                                                                                                                                               
""")

def process_url():
    user_url = input(Fore.LIGHTMAGENTA_EX + "\nDigite a URL do Website: ").strip()
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url
    urls = deque([user_url])
    scrapped_urls = set()  # Usando um set para garantir URLs únicas
    count = 0
    print(Fore.LIGHTRED_EX + "\nEscaneando Aguarde....\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }    

    while urls and count < 100:
        url = urls.popleft()
        count += 1

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            continue
        except KeyboardInterrupt:
            print("[-] Encerrando!")
            break

        # Filtrando apenas URLs que terminam com .pdf ou .PDF
        if url.lower().endswith(".pdf"):
            scrapped_urls.add(url)
            print(Fore.LIGHTGREEN_EX + f"\n{url}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Encontrando URLs em tags <a>
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  # Resolver URLs relativas
            # Verifica se a URL gerada é de HTTP ou HTTPS e se já não foi visitada
            if full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                # Filtrando URLs que terminam com .pdf ou .PDF
                if full_url.lower().endswith(".pdf"):
                    scrapped_urls.add(full_url)
                    print(Fore.LIGHTGREEN_EX + f"\n{full_url}")
                urls.append(full_url)

        # Encontrando URLs em tags <meta http-equiv="onion-location">
        for meta_tag in soup.find_all("meta", attrs={"http-equiv": "onion-location"}):
            if meta_tag.get("content"):
                meta_url = meta_tag.get("content")
                if meta_url.startswith(("http://", "https://")) and meta_url not in scrapped_urls:
                    # Filtrando URLs que terminam com .pdf ou .PDF
                    if meta_url.lower().endswith(".pdf"):
                        scrapped_urls.add(meta_url)
                        print(Fore.LIGHTGREEN_EX + f"\n{meta_url}")
                    urls.append(meta_url)

    # Exibindo somente as URLs com .pdf ou .PDF
    print(Fore.LIGHTYELLOW_EX + '\n\n################## URL PDF ######################')
    print(Fore.LIGHTYELLOW_EX + f'\nForam Encontradas URL: {len(scrapped_urls)}')

    # Perguntar se deseja salvar os resultados
    save = input(Fore.LIGHTMAGENTA_EX + "\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
    if save == 's':
        file_name = input(Fore.LIGHTMAGENTA_EX + "\nDigite o nome do arquivo para salvar (exemplo: arquivo.txt): ").strip()
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write("################## URL PDF ######################\n")
                f.write(f"\nForam Encontradas URL: {len(scrapped_urls)}\n\n")
                f.write('\n\n'.join(sorted(scrapped_urls)))
            print(Fore.LIGHTGREEN_EX + f"\nInformações salvas com sucesso no arquivo: {file_name}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"Erro ao salvar o arquivo: {e}")

def process_query():
    print(Fore.LIGHTMAGENTA_EX + "Escolha o motor de busca\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "1 - Google")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "2 - Bing")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "3 - DuckDuckGo")
    
    choice = input(Fore.LIGHTMAGENTA_EX + "\nDigite o número do motor de busca desejado (1/2/3): ").strip()
    if choice == '1':
        search_google()
    elif choice == '2':
        search_bing()
    elif choice == '3':
        search_duckduckgo()
    else:
        print(Fore.LIGHTRED_EX + "Escolha inválida. Tente novamente.")

def search_google():    
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nBuscando no Google")
    # Adicione código para buscar os resultados do Google (pode exigir parsing de resultados ou API)

def search_bing():    
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nBuscando no Bing")
    # Adicione código para buscar os resultados do Bing (pode exigir parsing de resultados ou API)

def search_duckduckgo():    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nBuscando no DuckDuckGo")
    # Adicione código para buscar os resultados do DuckDuckGo (pode exigir parsing de resultados ou API)

if __name__ == "__main__":
    process_query()    
    process_url()

input(Fore.LIGHTMAGENTA_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
