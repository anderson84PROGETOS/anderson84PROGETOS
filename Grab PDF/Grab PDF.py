import requests
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import init, Fore, Style
import warnings
from bs4 import XMLParsedAsHTMLWarning

# Ignorar o aviso específico
warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗ ██████╗  █████╗ ██████╗     ██████╗ ██████╗ ███████╗
██╔════╝ ██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔══██╗██╔════╝
██║  ███╗██████╔╝███████║██████╔╝    ██████╔╝██║  ██║█████╗  
██║   ██║██╔══██╗██╔══██║██╔══██╗    ██╔═══╝ ██║  ██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║██████╔╝    ██║     ██████╔╝██║     
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     ╚═╝     ╚═════╝ ╚═╝                                                                 
""")

global_count = 1  # Contador global de PDFs encontrados

def process_url():
    global global_count
    user_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do Website: ").strip()
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url

    max_pdfs = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nQuantos PDF Deseja Encontrar (Deixe em branco para buscar todos): ").strip()
    max_pdfs = int(max_pdfs) if max_pdfs else float('inf')  # Sem limite se não especificado

    urls = deque([user_url])
    scrapped_urls = set()
    pdf_urls = set()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscaneando Aguarde....\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    while urls and len(pdf_urls) < max_pdfs:
        url = urls.popleft()

        if url in scrapped_urls:
            continue

        scrapped_urls.add(url)
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            continue
        
        response.encoding = response.apparent_encoding  

        try:
            soup = BeautifulSoup(response.text, 'html.parser')  # Mantendo apenas 'html.parser' para evitar erro            
        except Exception as e:
            pass
            continue

        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  
            if full_url.endswith(".pdf") and full_url not in pdf_urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n{global_count}  =  PDF: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + full_url)
                pdf_urls.add(full_url)
                global_count += 1
                if len(pdf_urls) >= max_pdfs:
                    break
            elif full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                urls.append(full_url)

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nForam Encontrados {len(pdf_urls)} PDF")

    save = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar as informações em um arquivo? (s/n): ").strip().lower()
    if save == 's':
        file_name = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (exemplo: arquivos_pdfs.txt): ").strip()
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                for url in sorted(pdf_urls):
                    f.write(f"{url}\n\n")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nInformações salvas com sucesso no arquivo: {file_name}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    process_url()
    input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
