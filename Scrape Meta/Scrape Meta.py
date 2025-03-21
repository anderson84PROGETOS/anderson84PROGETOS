import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

# Exibe o banner inicial
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗    ███╗   ███╗███████╗████████╗ █████╗ 
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝    ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗
███████╗██║     ██████╔╝███████║██████╔╝█████╗      ██╔████╔██║█████╗     ██║   ███████║
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝      ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║
███████║╚██████╗██║  ██║██║  ██║██║     ███████╗    ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝    ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝

""")

# Função para obter links externos e informações de meta tags
def get_website_info(url):
    # Extrai o domínio base
    base_domain = urlparse(url).netloc or url  # Caso url seja apenas o domínio
    
    # Cabeçalhos para simular um navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    # Tenta HTTPS primeiro (porta 443)
    if not url.startswith('http://') and not url.startswith('https://'):
        url_https = 'https://' + url
    else:
        url_https = url
    
    try:
        response = requests.get(url_https, headers=headers, timeout=10)
        response.raise_for_status()
        url_base = url_https  # Usa a URL que funcionou
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ssl_err:
        # Se HTTPS falhar, tenta HTTP (porta 80)
        url_http = 'http://' + base_domain if not url.startswith('http://') else url
        try:
            response = requests.get(url_http, headers=headers, timeout=10)
            response.raise_for_status()
            url_base = url_http  # Usa a URL que funcionou
        except requests.RequestException as http_err:
            return [Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar o site: HTTPS falhou ({str(ssl_err)}), HTTP falhou ({str(http_err)})"]
    except requests.RequestException as e:
        return [Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar o site: {str(e)}"]
    
    # Parseia o HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Determina o protocolo usado com base na URL que funcionou
    protocol = 'http://' if url_base.startswith('http://') else 'https://'
    
    # Extrai links externos das tags <a>
    external_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Converte links relativos em absolutos
        if href.startswith('/'):
            href = protocol + base_domain + href
        elif not href.startswith('http'):
            continue  # Ignora links inválidos ou não-HTTP
        
        # Extrai o domínio do link
        link_domain = urlparse(href).netloc
        
        # Verifica se o domínio do link é diferente do domínio base (link externo)
        if link_domain and link_domain != base_domain:
            external_links.add(href)
    
    # Extrai URLs das tags <meta>
    meta_urls = set()
    for meta in soup.find_all('meta'):
        meta_content = meta.get('content', '')
        if meta_content and ('http://' in meta_content or 'https://' in meta_content):
            meta_url = meta_content if urlparse(meta_content).scheme else None
            if meta_url:
                meta_urls.add(meta_url)
    
    # Combina links externos e URLs de meta tags
    all_urls = external_links.union(meta_urls)
    
    return sorted(list(all_urls)) if all_urls else [Fore.LIGHTRED_EX + Style.BRIGHT + "Nenhum link externo ou URL em meta tags Encontrado"]

# Solicita input do usuário
website = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website (ex.: google.com): ")

# Executa a análise
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nURL Encontrada no site: {website}\n")
result = get_website_info(website)

# Mostra os resultados com números
for i, url in enumerate(result, 1):
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{i:<3} = " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f" {url}")

# Pergunta se deseja salvar os resultados
save_option = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n\nDeseja salvar os resultados? (s/n): ").strip().lower()

if save_option == "s":
    file_name = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (ex.: urls_web.txt): ").strip()
    
    try:
        with open(file_name, "w", encoding="utf-8") as file:

            # Escreve o cabeçalho no arquivo
            file.write(f"URL Encontrada no site: {website}\n\n")

            # Escreve os resultados
            for i, url in enumerate(result, 1):
                file.write(f"{i:<3} {url}\n\n")

        # Perguntar se desaja salvar os resultados
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos com sucesso em: {file_name}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar o arquivo: {str(e)}")
else:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nO arquivo não foi salvo !")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
