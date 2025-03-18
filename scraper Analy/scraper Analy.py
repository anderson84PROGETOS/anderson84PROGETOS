import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from colorama import Fore, Style, init
import re

# Inicializando o colorama
init(autoreset=True)
# Exibe o banner inicial
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗      █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝
███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝    ███████║██╔██╗ ██║███████║██║      ╚████╔╝ 
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗    ██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝  
███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║    ██║  ██║██║ ╚████║██║  ██║███████╗   ██║   
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   
                                                                                                       
""")

def get_sitemap(url):
    """Busca e extrai URLs de um sitemap.xml."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    sitemap_url = urljoin(url, '/sitemap.xml')
    sitemap_urls = []  # Usando lista para preservar duplicatas
    
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
        urls = re.findall(r'<loc>(.*?)</loc>', response.text)
        if urls:
            for idx, u in enumerate(urls):
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n{u}")                
                sitemap_urls.append(u)  # Adiciona cada URL à lista, incluindo duplicatas
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhuma URL encontrada no sitemap.")
        return sitemap_urls
    except requests.RequestException as e:
        pass
        return []

def scrape_website(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Capturando o código-fonte bruto
        source_code = response.text
        soup = BeautifulSoup(source_code, 'html.parser')

        # 1. Extraindo o título da página
        title = soup.title.string if soup.title else "Sem título"
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTítulo da página: {title}\n")

        # 2. Extraindo todos os links
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nLinks Encontrados")
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                links.add(full_url)
        for tag in soup.find_all(True):
            content = tag.get('content')
            if content and isinstance(content, str) and content.startswith('http'):
                full_url = urljoin(url, content)
                links.add(full_url)
        js_pattern = r'https?://[^\s\'"]+\.js'
        js_from_source = set(re.findall(js_pattern, source_code))
        links.update(js_from_source)

        js_links = {link for link in links if link.endswith('.js')}
        other_links = links - js_links

        for link in sorted(other_links):
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n{link}")
        if js_links:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\nArquivos JavaScript encontrados")
            for link in sorted(js_links):
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n{link}")

        # 3. Extraindo links do sitemap
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nLinks do Sitemap\n")
        sitemap_links = get_sitemap(url)
        if not sitemap_links:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "Nenhum sitemap encontrado ou acessível.")

        # 4. Extraindo texto visível
        print(Fore.LIGHTWHITE_EX + "\n\nTexto principal\n")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        clean_text = " ".join(text.split())
        print(Fore.LIGHTWHITE_EX + clean_text[:500] + "..." if len(clean_text) > 500 else clean_text)

        # 5. Extraindo imagens
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nImagens Encontradas")
        images = set()
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url:
                full_img_url = urljoin(url, img_url)
                images.add(full_img_url)
        for img_url in sorted(images):
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{img_url}")

        # 6. Informações adicionais
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nInformações adicionais")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nTotal de links Encontrados: {len(links)}")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nTotal de links JavaScript Encontrados: {len(js_links)}")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nTotal de links do sitemap Encontrados: {len(sitemap_links)}")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTotal de imagens Encontradas: {len(images)}")

        return {
            'title': title,
            'links': list(other_links),
            'js': list(js_links),
            'sitemap': sitemap_links,  # Mantendo como lista para preservar duplicatas
            'text': clean_text,
            'images': list(images)
        }

    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar o website: {e}")
        return None

if __name__ == "__main__":
    target_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (exemplo: https://example.com): ").strip()
    if not target_url.startswith("http"):
        target_url = "https://" + target_url
    print(f"\nAnalisando: {target_url}\n")
    result = scrape_website(target_url)

    if result:
        save_choice = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDeseja salvar os resultados? (s/n): ").lower()
        if save_choice == 's':
            file_name = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (ex: arquivo.txt): ").strip()
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(f"Analisando Website: {target_url}\n")
                f.write(f"\nTítulo: {result['title']}\n\n")
                f.write("Links\n\n" + "\n\n".join(result['links']) + "\n\n\n")
                f.write("Texto\n\n" + result['text'] + "\n\n\n")
                f.write("Imagens\n\n" + "\n\n".join(result['images']) + "\n\n\n")
                f.write("JavaScript\n\n" + "\n\n".join(result['js']) + "\n\n\n")
                f.write("Sitemap\n\n" + "\n\n".join(result['sitemap']) + "\n\n\n")
                f.write(f"Total de links Encontrados: {len(result['links']) + len(result['js'])}\n")
                f.write(f"Total de links JavaScript Encontrados: {len(result['js'])}\n")
                f.write(f"Total de links do Sitemap Encontrados: {len(result['sitemap'])}\n")
                f.write(f"Total de imagens Encontradas: {len(result['images'])}")
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nResultados salvos em: {file_name}")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nResultados não foram salvos")

    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
