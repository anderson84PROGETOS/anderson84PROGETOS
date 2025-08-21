import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from collections import deque
import warnings
from bs4 import XMLParsedAsHTMLWarning

# Initialize colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗███████╗██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██║    ██║██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══╝  ██╔══██╗    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝███████╗██████╔╝    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝                                                                                    
""")

# Headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8,application/pdf',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Ignore BeautifulSoup XMLParsedAsHTMLWarning
warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)

global_count = 1  # Global counter for PDF found

def fetch_pdfs_from_urls(starting_urls, max_pdfs=float('inf'), pdf_list=None, pasta_pdfs=None):
    urls = deque(starting_urls)  # Queue of URLs to process
    scrapped_urls = set()  # Set for already processed URLs
    pdf_urls = set()  # Set to store PDF URLs
    global global_count

    while urls and len(pdf_urls) < max_pdfs:
        url = urls.popleft()

        if url in scrapped_urls:
            continue

        scrapped_urls.add(url)

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            pass
            continue

        response.encoding = response.apparent_encoding

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            pass
            continue

        # Find <a> tags with URLs ending in .pdf and containing numbers
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])
            if (full_url.endswith(".pdf") and 
                full_url not in pdf_urls and 
                re.search(r'\d', full_url)):  # Check for numbers in URL
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n{global_count:<2} = PDF: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + full_url)
                pdf_urls.add(full_url)
                # Download PDF immediately
                nome_arquivo = os.path.basename(full_url.split("?")[0])
                destino_arquivo = os.path.join(pasta_pdfs, nome_arquivo)
                try:
                                    
                    r = requests.get(full_url, headers=HEADERS, stream=True, timeout=10)
                    r.raise_for_status()
                    with open(destino_arquivo, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    if pdf_list is not None and full_url not in pdf_list:
                        pdf_list.append(full_url)  # Add to PDF list for saving
                except Exception as e:
                    pass
                global_count += 1
                if len(pdf_urls) >= max_pdfs:
                    break
            elif full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                urls.append(full_url)

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n\nForam Encontrados: {len(pdf_urls)} PDF")

def baixar_arquivos(url, destino="downloads"):
    # Create folders
    pasta_fotos = os.path.join(destino, "fotos")
    pasta_videos = os.path.join(destino, "videos")
    pasta_pdfs = os.path.join(destino, "pdfs")
    pasta_links = os.path.join(destino, "links")
    os.makedirs(pasta_fotos, exist_ok=True)
    os.makedirs(pasta_videos, exist_ok=True)
    os.makedirs(pasta_pdfs, exist_ok=True)
    os.makedirs(pasta_links, exist_ok=True)

    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[+] Acessando: {url}")
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=10)
        resposta.raise_for_status()
    except Exception as e:
        pass
        return

    html = resposta.text

    # Regex for traditional links (src and href)
    padrao_links = r'(src|href)="([^"]+)"'
    links_tradicionais = re.findall(padrao_links, html, re.IGNORECASE)
    links_tradicionais = [link for _, link in links_tradicionais]

    # Regex for meta tag content
    padrao_meta = r'<meta[^>]+content="([^"]+)"'
    links_meta = re.findall(padrao_meta, html, re.IGNORECASE)

    # Combine all links
    todos_links = links_tradicionais + links_meta

    if not todos_links:
        print(Fore.LIGHTRED_EX + "\n[-] Nenhum link encontrado.")
        return

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] {len(todos_links)} links Encontrados\n")

    # Separate links by category
    lista_fotos = []
    lista_videos = []
    lista_pdfs = []
    lista_outros = []

    for idx, link in enumerate(todos_links, start=1):
        link_absoluto = urljoin(url, link)
        nome_arquivo = os.path.basename(link_absoluto.split("?")[0])

        if re.search(r'\.(jpg|jpeg|png|ico|gif)$', nome_arquivo, re.IGNORECASE):
            lista_fotos.append(link_absoluto)
            destino_arquivo = os.path.join(pasta_fotos, nome_arquivo)
            tipo = "imagem"
        elif re.search(r'\.(mp4|webm|avi|mov|mkv|flv|wmv|m4v)$', nome_arquivo, re.IGNORECASE):
            lista_videos.append(link_absoluto)
            destino_arquivo = os.path.join(pasta_videos, nome_arquivo)
            tipo = "vídeo"
        elif re.search(r'\.pdf$', nome_arquivo, re.IGNORECASE):
            lista_pdfs.append(link_absoluto)
            destino_arquivo = os.path.join(pasta_pdfs, nome_arquivo)
            tipo = "PDF"
        else:
            lista_outros.append(link_absoluto)
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[{idx}] Link externo/meta: {link_absoluto}")
            continue

        # Download images, videos, and PDFs
        try:
            print(Fore.LIGHTGREEN_EX + f"\n\n[{idx}] Baixando {tipo}: {link_absoluto}\n")
            r = requests.get(link_absoluto, headers=HEADERS, stream=True, timeout=10)
            r.raise_for_status()
            with open(destino_arquivo, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            pass
            continue

    # Save links to text files with headers
    arq_fotos = os.path.join(pasta_links, "links_fotos.txt")
    arq_videos = os.path.join(pasta_links, "links_videos.txt")
    arq_pdfs = os.path.join(pasta_links, "links_pdfs.txt")
    arq_outros = os.path.join(pasta_links, "links_outros.txt")

    with open(arq_fotos, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_fotos)} links de IMAGENS Encontrados\n\n")
        f.write("\n\n".join(lista_fotos))

    with open(arq_videos, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_videos)} links de VÍDEOS Encontrados\n\n")
        f.write("\n\n".join(lista_videos))

    with open(arq_pdfs, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_pdfs)} links de PDF Encontrados\n\n")
        f.write("\n\n".join(lista_pdfs))

    with open(arq_outros, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_outros)} links EXTERNOS/META Encontrados\n\n")
        f.write("\n\n".join(lista_outros))

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\n[✓] Download finalizado!\n")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[✓] Links salvos\n\n{arq_fotos}\n{arq_videos}\n{arq_pdfs}\n{arq_outros}")

    # Additional PDF crawling
    max_pdfs_input = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nQuantos PDF deseja encontrar (deixe em branco para buscar todos): ").strip()
    max_pdfs = int(max_pdfs_input) if max_pdfs_input else float('inf')
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nEscaneando website para PDF: {url}\n")

    fetch_pdfs_from_urls([url], max_pdfs, lista_pdfs, pasta_pdfs)

    # Update PDF links file
    with open(arq_pdfs, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_pdfs)} links de PDF Encontrados\n\n")
        f.write("\n\n".join(lista_pdfs))

if __name__ == "__main__":
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do site: ").strip()
    if not site.startswith(('http:', 'https:')):
        site = 'https://' + site
    baixar_arquivos(site)

    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
