import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

print("""

██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗      ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝      ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                                                  
""")

# Cabeçalhos padrão para Firefox
headers_firefox = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36'
}

def get_website_info(url):
    # Cabeçalhos para evitar erro 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Fazendo a requisição HTTP com headers
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Verifica se a requisição foi bem-sucedida

    # Parsing do conteúdo HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extraindo o título da página
    title = soup.title.string if soup.title else 'N/A'

    # Extraindo a meta descrição
    description = soup.find('meta', attrs={'name': 'description'})
    description_content = description['content'] if description else 'N/A'

    # Extraindo o domínio base da URL fornecida
    base_url = urlparse(url).netloc

    # Extraindo e classificando os links
    internal_links = set()
    external_links = set()
    onion_links = set()

    def classify_link(href):
        parsed_href = urlparse(href)
        
        # URLs relativas se tornam URLs absolutas
        if not parsed_href.netloc:
            href = urljoin(url, href)
            parsed_href = urlparse(href)

        if parsed_href.netloc == base_url:
            internal_links.add(href)
        elif parsed_href.scheme in ['http', 'https']:
            external_links.add(href)
        
        if '.onion' in href:
            onion_links.add(href)

    # Buscando links em tags 'a'
    for a in soup.find_all('a', href=True):
        classify_link(a['href'])

    # Buscando links em outras tags que podem conter URLs
    for tag in soup.find_all(src=True):
        classify_link(tag['src'])
    for tag in soup.find_all(data=True):
        classify_link(tag['data'])
    for tag in soup.find_all(content=True):
        classify_link(tag['content'])

    # Encontrando o rodapé
    footer = soup.find('footer')
    footer_text = footer.get_text() if footer else 'N/A'

    return {
        'title': title,
        'description': description_content,
        'internal_links': internal_links,
        'external_links': external_links,
        'onion_links': onion_links,
        'footer_text': footer_text
    }

def obter_name_servers(endereco_ip):
    user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco_ip}", headers=user_agent)
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados['isp']
        else:
            return 'N/A'
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter informações do IP: {e}")
        return 'N/A'

def exibir_robots_txt(site, headers):
    robots_url = urljoin(site, '/robots.txt')
    response = requests.get(robots_url, headers=headers)
    print(f"\n\n🎯============= Conteúdo do robots.txt =============🎯\n\n")
    if response.status_code == 200:
        print(response.text)
    else:
        print(f"Não foi possível acessar o robots.txt (Status: {response.status_code})")

if __name__ == "__main__":
    url = input("\nDigite a URL do site: ")
    
    ip = urlparse(url).netloc
    name_servers = obter_name_servers(ip)
    print(f"\n\nName Server: {name_servers}\n")

    info = get_website_info(url)
    print(f"\n\nTítulo: {info['title']}\n")
    print(f"\nDescrição: {info['description']}\n")    
    
    print(f"\n\n========== Texto do Rodapé ==========\n\n{info['footer_text']}\n")
    
    print("\n\n========== Links Internos ==========\n")
    print(f"Total de Links Internos: {len(info['internal_links'])}\n")
    for link in info['internal_links']:
        print(link)
    
    print("\n\n========== Links Externos ==========\n")
    print(f"Total de Links Externos: {len(info['external_links'])}\n")
    for link in info['external_links']:
        print(link)
    
    print("\n\n========== Links .onion ==========\n")
    print(f"Total de Links .onion: {len(info['onion_links'])}\n")
    for link in info['onion_links']:
        print(link)    

    # Exibir o conteúdo do robots.txt usando a URL fornecida
    exibir_robots_txt(url, headers_firefox)

input("\n\n=================== PRESSIONE ENTER PARA SAIR ===================\n\n")
