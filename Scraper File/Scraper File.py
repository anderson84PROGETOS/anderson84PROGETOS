import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
import warnings
from bs4 import XMLParsedAsHTMLWarning
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗     ███████╗██╗██╗     ███████╗    
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║██║     ██╔════╝    
███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝    █████╗  ██║██║     █████╗      
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗    ██╔══╝  ██║██║     ██╔══╝      
███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║    ██║     ██║███████╗███████╗    
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚══════╝╚══════╝    
""")

# Ignorar o aviso específico
warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)

global_count = 1  # Contador global de PDFs encontrados

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
        
        # Imprimir o status da requisição
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nEscaniando website: {url}\n")

        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            js_urls = set()
            css_urls = set()
            img_urls = set()
            ico_urls = set()  # URLs que terminam com .ico
            php_urls = set()
            other_urls = set()
            pdf_urls = set()  # Conjunto para armazenar URLs de arquivos PDF

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
                
                # Verifica se a URL é um fragmento (exemplo: "#home") e ignora
                if href_url.startswith('#'):
                    continue

                # Se for um arquivo PHP, adiciona ao conjunto php_urls
                if href_url.endswith('.php'):
                    php_full_url = urljoin(url, href_url)
                    php_urls.add(php_full_url)
                # Se for um arquivo PDF, adiciona ao conjunto pdf_urls
                elif href_url.endswith('.pdf'):
                    pdf_full_url = urljoin(url, href_url)
                    pdf_urls.add(pdf_full_url)
                else:
                    # Caso contrário, adiciona aos outros URLs
                    other_urls.add(urljoin(url, href_url))  # Certificando-se de que é uma URL completa

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

            return js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls

        else:
            print(f"\nErro {response.status_code} ao acessar: {url}")
            return set(), set(), set(), set(), set(), set(), set()

    except requests.exceptions.RequestException as e:
        print(f"\nErro ao fazer requisição para {url}: {e}")
        return set(), set(), set(), set(), set(), set(), set()

def fetch_pdfs_from_urls(starting_urls, max_pdfs=10):
    urls = deque(starting_urls)  # Fila de URLs para processar
    scrapped_urls = set()  # Conjunto para URLs já processadas
    pdf_urls = set()  # Conjunto para armazenar URLs de arquivos PDF
    global global_count  # Contador global de PDFs encontrados

    # Cabeçalhos adicionais para buscar PDFs
    pdf_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept': 'application/pdf, application/x-pdf, application/vnd.adobe.xfdf, image/jpeg, image/png, image/tiff, image/pjpeg, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    while urls and len(pdf_urls) < max_pdfs:
        url = urls.popleft()

        if url in scrapped_urls:
            continue

        scrapped_urls.add(url)
        
        try:
            response = requests.get(url, headers=pdf_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            pass
            continue
        
        response.encoding = response.apparent_encoding

        try:
            soup = BeautifulSoup(response.text, 'html.parser')  # Mantendo apenas 'html.parser' para evitar erro            
        except Exception as e:
            continue

        # Adicionando logs de depuração
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  
            # Log para verificar as URLs encontradas            
           
            if full_url.endswith(".pdf") and full_url not in pdf_urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n{global_count:<2}  = PDF: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + full_url)
                pdf_urls.add(full_url)
                global_count += 1
                if len(pdf_urls) >= max_pdfs:
                    break
            elif full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                urls.append(full_url)    
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n\nForam Encontrados: {len(pdf_urls)} PDF")
    return pdf_urls

def save_results_to_file(js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls):
    filename = input("\nDigite o nome do arquivo para salvar os resultados: ").strip()
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"URL de Arquivos JavaScript: {len(js_urls)}\n")
        f.writelines(f"{url}\n" for url in js_urls)   
        
        f.write(f"\n\nURL de Arquivos CSS: {len(css_urls)}\n")
        f.writelines(f"{url}\n" for url in css_urls)

        f.write(f"\n\nURL de Imagens: {len(img_urls)}\n")
        f.writelines(f"{url}\n" for url in img_urls)

        f.write(f"\n\nURL de Ícones: {len(ico_urls)}\n")
        f.writelines(f"{url}\n" for url in ico_urls)

        f.write(f"\n\nURL de Arquivos PHP: {len(php_urls)}\n")
        f.writelines(f"{url}\n" for url in php_urls)

        f.write(f"\n\nOutras URL: {len(other_urls)}\n")
        f.writelines(f"{url}\n" for url in other_urls)       

        f.write(f"\n\nURL de Arquivos PDF: {len(pdf_urls)}\n")
        f.writelines(f"{url}\n" for url in pdf_urls)  

        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nResultados salvos em: {filename}")    


# Certificando-se de que os PDFs são encontrados corretamente e passados para a função
def fetch_pdfs_from_urls(starting_urls, max_pdfs=10):
    urls = deque(starting_urls)  # Fila de URLs para processar
    scrapped_urls = set()  # Conjunto para URLs já processadas
    pdf_urls = set()  # Conjunto para armazenar URLs de arquivos PDF
    global global_count  # Contador global de PDFs encontrados

    # Cabeçalhos adicionais para buscar PDFs
    pdf_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept': 'application/pdf, application/x-pdf, application/vnd.adobe.xfdf, image/jpeg, image/png, image/tiff, image/pjpeg, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    while urls and len(pdf_urls) < max_pdfs:
        url = urls.popleft()

        if url in scrapped_urls:
            continue

        scrapped_urls.add(url)

        try:
            response = requests.get(url, headers=pdf_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            pass
            continue
        
        response.encoding = response.apparent_encoding

        try:
            soup = BeautifulSoup(response.text, 'html.parser')  # Mantendo apenas 'html.parser' para evitar erro            
        except Exception as e:
            continue

        # Adicionando logs de depuração
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])  
            # Log para verificar as URLs encontradas            
           
            if full_url.endswith(".pdf") and full_url not in pdf_urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n{global_count:<2}  = PDF: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + full_url)
                pdf_urls.add(full_url)
                global_count += 1
                if len(pdf_urls) >= max_pdfs:
                    break
            elif full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                urls.append(full_url)    
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n\nForam Encontrados: {len(pdf_urls)} PDF")
    return pdf_urls

# Função principal para processar URL do usuário
def process_url():
    global global_count    
    user_url = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Digite a URL do Website (ex: https://example.com): ").strip()  # Removendo formatação
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url

    max_pdfs_input = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nQuantos PDF deseja encontrar (deixe em branco para buscar todos): ").strip()
    max_pdfs = int(max_pdfs_input) if max_pdfs_input else float('inf')  # Sem limite se não especificado    

    # Buscar PDFs do site inicial
    js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls = find_resources_urls(user_url)

    if js_urls or css_urls or img_urls or ico_urls or php_urls or other_urls or pdf_urls:        

        if js_urls:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Total de URL de Arquivos JavaScript js: {len(js_urls)}")
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nURL de Arquivos JavaScript\n==========================")
            for js_url in js_urls:
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + js_url)
        

        if css_urls:
            print(Fore.LIGHTWHITE_EX + f"\n\nTotal de URL de Arquivos CSS: {len(css_urls)}")
            print(Fore.LIGHTWHITE_EX + "\nURL de Arquivos CSS\n===================")
            for css_url in css_urls:
                print(Fore.LIGHTWHITE_EX + css_url)


        if img_urls:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n\nTotal de URL de Imagens: {len(img_urls)}")
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nURL de Imagens\n==============")
            for img_url in img_urls:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + img_url)

        if ico_urls:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nTotal de URL de Arquivos ICO e Favicon: {len(ico_urls)}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nURL de Arquivos ICO e Favicon\n=============================")
            for ico_url in ico_urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + ico_url)

        if php_urls:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nTotal de URL de Arquivos PHP: {len(php_urls)}")
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nURL de Arquivos PHP\n===================")
            for php_url in php_urls:
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + php_url)       

        if other_urls:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nTotal de Outros URL: {len(other_urls)}")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nOutros URL\n==========")
            for other_url in other_urls:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{other_url}")
   
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\nURL de Arquivos PDF\n===================")
        if pdf_urls:
            print(f"\n\nTotal de URL de Arquivos PDF: {len(pdf_urls)}")            
            for pdf_url in pdf_urls:
                print(pdf_url)        
    
    # Buscar mais PDFs se necessário       
    pdf_urls = fetch_pdfs_from_urls([user_url], max_pdfs)

    # Oferecer a opção de salvar resultados em arquivo
    save_results_input = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nGostaria de salvar os resultados? (s/n): ").strip().lower()
    if save_results_input == 's':    
        save_results_to_file(js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls)     
    
    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\nPRESSIONE ENTER PARA SAIR\n=========================")

# Rodar o script
process_url()
