import os
import re
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import init, Fore, Style
from datetime import datetime

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + r"""
██╗    ██╗███████╗██████╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██║    ██║██╔════╝██╔══██╗    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██║ █╗ ██║█████╗  ██████╔╝    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
╚███╔███╔╝███████╗██████╔╝    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
""")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def salvar_em_arquivo(nome_arquivo, dados):
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(set(dados))))

def criar_pasta(destino):
    if not os.path.exists(destino):
        os.makedirs(destino)

def extrair_emails(conteudo):
    return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', conteudo)))

def buscar_pdf_links(url, destino, pdfs_encontrados, contagem):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = urljoin(url, link['href'])
            if href.lower().endswith('.pdf'):
                pdfs_encontrados.append(href)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[PDF] {href}')
                contagem['pdfs'] += 1
    except requests.exceptions.RequestException:
        pass

def buscar_emails(url, destino, emails_encontrados, contagem):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        emails = extrair_emails(response.text)
        for email in emails:
            if email not in emails_encontrados:
                emails_encontrados.add(email)
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f'[EMAIL] {email}')
                contagem['emails'] += 1
    except requests.exceptions.RequestException:
        pass

def buscar_robots_txt(url_base, destino):
    try:
        robots_url = urljoin(url_base, '/robots.txt')
        response = requests.get(robots_url, headers=headers, timeout=10)
        if response.status_code == 200:
            caminho = os.path.join(destino, 'robots.txt')
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + '[ROBOTS] Salvo robots.txt')
    except Exception:
        pass

def buscar_archive_org(url_base, destino, arquivos_encontrados):
    try:
        parsed = urlparse(url_base)
        host = parsed.netloc
        api_url = f"https://web.archive.org/cdx/search/cdx?url={host}/*&output=json&fl=timestamp,original&collapse=urlkey&filter=statuscode:200"
        response = requests.get(api_url, headers=headers, timeout=20)
        if response.status_code == 200 and len(response.json()) > 1:
            linhas = response.json()[1:]
            resultados_formatados = []
            for item in linhas:
                timestamp, link = item
                if link not in arquivos_encontrados:
                    arquivos_encontrados.append(link)
                    try:
                        # Converter timestamp para DD/MM/YYYY Horas:HH:MM
                        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                        data_fmt = f"{dt.strftime('%d/%m/%Y')}  Horas: {dt.strftime('%H:%M:%S')}"
                        saida = f"{data_fmt}    {link}"
                        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + saida)
                        resultados_formatados.append(saida)
                    except Exception:
                        pass
            # salvar já formatado
            salvar_em_arquivo(os.path.join(destino, 'archive_links.txt'), resultados_formatados)
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + '[ARCHIVE] Nenhum resultado encontrado.')
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f'[ERRO ARCHIVE] {e}')

def buscar_links(url, destino, links_encontrados, internos, externos, js_files, endpoints, fuzzables):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        base_domain = urlparse(url).netloc
        for tag in soup.find_all('a', href=True):
            href = urljoin(url, tag['href'])
            if href.startswith('http') and href not in links_encontrados:
                links_encontrados.add(href)
                parsed_href = urlparse(href)
                if base_domain in parsed_href.netloc:
                    internos.add(href)
                else:
                    externos.add(href)
                if re.search(r'\?.+=', href):
                    fuzzables.add(href)
                if re.search(r'\/(api|login|admin|auth|endpoint)[\/]?', href):
                    endpoints.add(href)
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT +  f'[LINK] {href}')
        for script in soup.find_all('script', src=True):
            src = urljoin(url, script['src'])
            if src not in js_files:
                js_files.add(src)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'[JS] {src}')
    except Exception:
        pass

def main(url):
    dominio = urlparse(url).netloc.replace('.', '_')
    pasta_destino = f'dados_{dominio}'
    criar_pasta(pasta_destino)

    pdfs = []
    emails = set()
    arquivos_archive = []
    links = set()
    internos = set()
    externos = set()
    js_files = set()
    endpoints = set()
    fuzzables = set()
    contagem = {'pdfs': 0, 'emails': 0, 'erros': 0}

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] Buscando links...')
    buscar_links(url, pasta_destino, links, internos, externos, js_files, endpoints, fuzzables)

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] Buscando robots.txt...')
    buscar_robots_txt(url, pasta_destino)

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] Buscando arquivos no Archive.org...')
    buscar_archive_org(url, pasta_destino, arquivos_archive)

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] Buscando PDF e e-mails...')
    threads = []
    for link in links:
        t1 = threading.Thread(target=buscar_pdf_links, args=(link, pasta_destino, pdfs, contagem))
        t2 = threading.Thread(target=buscar_emails, args=(link, pasta_destino, emails, contagem))
        t1.start()
        t2.start()
        threads.extend([t1, t2])
    for t in threads:
        t.join()

    salvar_em_arquivo(os.path.join(pasta_destino, 'pdfs.txt'), pdfs)
    salvar_em_arquivo(os.path.join(pasta_destino, 'emails.txt'), emails)
    salvar_em_arquivo(os.path.join(pasta_destino, 'links.txt'), links)
    salvar_em_arquivo(os.path.join(pasta_destino, 'internal_urls.txt'), internos)
    salvar_em_arquivo(os.path.join(pasta_destino, 'external_urls.txt'), externos)
    salvar_em_arquivo(os.path.join(pasta_destino, 'js_files.txt'), js_files)
    salvar_em_arquivo(os.path.join(pasta_destino, 'endpoints.txt'), endpoints)
    salvar_em_arquivo(os.path.join(pasta_destino, 'fuzzable_urls.txt'), fuzzables)

    contagem['archive_links'] = len(arquivos_archive)
    contagem['links'] = len(links)
    contagem['internal_urls'] = len(internos)
    contagem['external_urls'] = len(externos)
    contagem['js_files'] = len(js_files)
    contagem['endpoints'] = len(endpoints)
    contagem['fuzzable_urls'] = len(fuzzables)

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f'\nFinalizado. Resultados salvos em: {pasta_destino}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'PDF Encontrados: {contagem["pdfs"]}')
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f'E-mail Encontrados: {contagem["emails"]}')
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f'Arquivos no Archive: {contagem["archive_links"]}')
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f'Links Encontrados: {contagem["links"]}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'URL Internas Encontradas: {contagem["internal_urls"]}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'URL Externas Encontradas: {contagem["external_urls"]}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'Arquivos JS Encontrados: {contagem["js_files"]}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'Endpoints Encontrados: {contagem["endpoints"]}')
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'URL Fuzzáveis Encontradas: {contagem["fuzzable_urls"]}')

if __name__ == '__main__':
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT +
                 "Digite a URL do website (ex.: https://example.com ou http://example.com): ").strip()
    if not site.startswith(('http://', 'https://')):
        site = 'http://' + site
    main(site)
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
