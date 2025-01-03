import requests
import urllib.parse
from collections import deque
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # Agora você pode usar 'urljoin' diretamente
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗   ██╗██████╗ ██╗         ███████╗███╗   ███╗ █████╗ ██╗██╗          ██████╗ ██████╗  █████╗ ██████╗     
██║   ██║██╔══██╗██║         ██╔════╝████╗ ████║██╔══██╗██║██║         ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗    
██║   ██║██████╔╝██║         █████╗  ██╔████╔██║███████║██║██║         ██║  ███╗██████╔╝███████║██████╔╝    
██║   ██║██╔══██╗██║         ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║         ██║   ██║██╔══██╗██╔══██║██╔══██╗    
╚██████╔╝██║  ██║███████╗    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗    ╚██████╔╝██║  ██║██║  ██║██████╔╝    
 ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     
                                                                                                                                                                                                                                                                      
""")

def process_url():
    user_url = input(Fore.LIGHTMAGENTA_EX + "Digite a URL do Website: ").strip()
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url
    urls = deque([user_url])
    scrapped_urls = set()  # Usando um set para garantir URLs únicas
    emails = set()
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

        scrapped_urls.add(url)
        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        print(Fore.LIGHTYELLOW_EX + f"\n{url}")

        # Extraindo emails
        new_emails = set(re.findall(r'[a-zA-Z0-9\.\-+_]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}', response.text, re.I))
        emails.update(new_emails)        

        # Encontrando URLs em tags <a>
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  # Resolver URLs relativas
            # Verifica se a URL gerada é de HTTP ou HTTPS e se já não foi visitada
            if full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                scrapped_urls.add(full_url)
                urls.append(full_url)

        # Encontrando URLs em tags <meta http-equiv="onion-location">
        for meta_tag in soup.find_all("meta", attrs={"http-equiv": "onion-location"}):
            if meta_tag.get("content"):
                meta_url = meta_tag.get("content")
                if meta_url.startswith(("http://", "https://")) and meta_url not in scrapped_urls:
                    print(Fore.LIGHTGREEN_EX + f"\n{meta_url}")
                    scrapped_urls.add(meta_url)
                    urls.append(meta_url)        

    # Exibindo URLs e e-mails encontrados
    print(Fore.LIGHTYELLOW_EX + '\n\n################## URL ######################')
    print(Fore.LIGHTYELLOW_EX + f'\nForam Encontradas URL: {len(scrapped_urls)}')
    print(Fore.LIGHTRED_EX + '\n\n################## Email ######################')
    print(Fore.LIGHTRED_EX + f'\nForam Encontrados Emails: {len(emails)}\n')
    print(Fore.LIGHTRED_EX + '\n'.join(emails))        

    # Perguntar se deseja salvar os resultados
    save = input(Fore.LIGHTMAGENTA_EX + "\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
    if save == 's':
        file_name = input(Fore.LIGHTMAGENTA_EX + "\nDigite o nome do arquivo para salvar (exemplo: arquivo.txt): ").strip()
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write("################## URL ######################\n")
                f.write(f"\nForam Encontradas URL: {len(scrapped_urls)}\n\n")
                f.write('\n\n'.join(sorted(scrapped_urls)))
                f.write("\n\n\n################## Email ######################\n")
                f.write(f"\nForam Encontrados Emails: {len(emails)}\n\n")
                f.write('\n'.join(emails))
            print(Fore.LIGHTGREEN_EX + f"\nInformações salvas com sucesso no arquivo: {file_name}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    process_url()

input(Fore.LIGHTMAGENTA_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
