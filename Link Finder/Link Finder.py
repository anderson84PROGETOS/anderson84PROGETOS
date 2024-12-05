import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

print("""

██╗     ██╗███╗   ██╗██╗  ██╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║     ██║████╗  ██║██║ ██╔╝    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║     ██║██╔██╗ ██║█████╔╝     █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║     ██║██║╚██╗██║██╔═██╗     ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
███████╗██║██║ ╚████║██║  ██╗    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                             
""")

# Cabeçalhos HTTP para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def is_link_externo(url_base, link):
    base_netloc = urlparse(url_base).netloc
    link_netloc = urlparse(link).netloc
    return base_netloc != link_netloc and bool(link_netloc)

def normalizar_link(link):
    # Corrigir formatação de links malformados
    if link.startswith("http:/") and not link.startswith("http://"):
        link = link.replace("http:/", "http://")
    elif link.startswith("https:/") and not link.startswith("https://"):
        link = link.replace("https:/", "https://")
    return link

def encontrar_links(url, visitados=None):
    if visitados is None:
        visitados = set()

    todos_os_links = set()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Buscar links em tags <a>
        for a_tag in soup.find_all("a", href=True):
            raw_link = a_tag["href"].strip()
            link = normalizar_link(urljoin(url, raw_link))

            if link not in visitados:
                visitados.add(link)
                todos_os_links.add(link)

        # Buscar links em tags <meta> com atributo content
        for meta_tag in soup.find_all("meta", content=True):
            content = meta_tag["content"].strip()
            if content.startswith("http://") or content.startswith("https://"):
                link = normalizar_link(content)
                if link not in visitados:
                    visitados.add(link)
                    todos_os_links.add(link)

        # Buscar links em tags <link> com atributo href
        for link_tag in soup.find_all("link", href=True):
            raw_link = link_tag["href"].strip()
            link = normalizar_link(urljoin(url, raw_link))

            if link not in visitados:
                visitados.add(link)
                todos_os_links.add(link)

        # Buscar links em tags <script> com atributo src
        for script_tag in soup.find_all("script", src=True):
            raw_link = script_tag["src"].strip()
            link = normalizar_link(urljoin(url, raw_link))

            if link not in visitados:
                visitados.add(link)
                todos_os_links.add(link)

    except Exception as e:
        print(f"Erro ao buscar {url}: {e}")

    return todos_os_links

def main():
    url_base = input("\nDigite a URL para análise (ex.: https://exemplo.com): ").strip()
    print(f"\nAnalisando: {url_base}\n")
    visitados = set()
    todos_os_links = encontrar_links(url_base, visitados)

    print("\n=== Todos os Links Encontrados ===\n")
    for link in sorted(todos_os_links):
        print("\n", link)

    # Exibir a contagem total de links encontrados
    print("\n\nNúmero total de links Encontrados: ", len(todos_os_links))

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
