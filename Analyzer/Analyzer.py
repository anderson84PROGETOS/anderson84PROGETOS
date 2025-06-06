import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import Counter
import re
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗
███████║██╔██╗ ██║███████║██║      ╚████╔╝   ███╔╝ █████╗  ██████╔╝
██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗
██║  ██║██║ ╚████║██║  ██║███████╗   ██║   ███████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝
                                                                                                 
""")

def fetch_site_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[Erro] Falha ao acessar {url}: {e}")
        return None

def extract_text(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=' ')
    return re.sub(r'\s+', ' ', text).strip()

def extract_footer(soup):
    footer = soup.find("footer")
    if footer:
        return re.sub(r'\s+', ' ', footer.get_text(separator=' ', strip=True))
    return "Rodapé não encontrado na página."

def count_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    common_words = set(["a", "e", "de", "do", "da", "em", "um", "para", "com", "o", "os", "as", "na", "no", "que", "é", "por"])
    filtered = [w for w in words if w not in common_words and len(w) > 2]
    return Counter(filtered).most_common(20)

def extract_links(soup, base_url):
    internal = set()
    external = set()
    parsed_base = urlparse(base_url)
    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag['href'])
        if urlparse(full_url).netloc == parsed_base.netloc:
            internal.add(full_url)
        else:
            external.add(full_url)
    return internal, external

def extract_urls_from_meta(soup):
    return {tag['content'] for tag in soup.find_all("meta", content=True)
            if tag['content'].startswith(('http://', 'https://'))}

def extract_seo_data(soup):
    seo = {
        "title": soup.title.string.strip() if soup.title else "N/A",
        "meta_description": "N/A",
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "h2": [h.get_text(strip=True) for h in soup.find_all("h2")]
    }
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        seo["meta_description"] = meta["content"].strip()
    return seo

def extract_resources(soup, base_url):
    imgs = [urljoin(base_url, img['src']) for img in soup.find_all("img", src=True)]
    scripts = [urljoin(base_url, s['src']) for s in soup.find_all("script", src=True)]
    css = [urljoin(base_url, l['href']) for l in soup.find_all("link", rel="stylesheet", href=True)]
    return imgs, scripts, css

def display_report(url, seo, internal, external, imgs, scripts, css, meta_urls, footer_text):
    print(f"\n🔍 Análise do site: {url}\n")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n=== SEO ===")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nTítulo: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + Style.BRIGHT + f"{seo['title']}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nMeta description: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + Style.BRIGHT + f"{seo['meta_description']}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nH1 tags: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + Style.BRIGHT + f"{seo['h1']}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nH2 tags: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + Style.BRIGHT + f"{seo['h2']}\n")
    
    print(Fore.LIGHTYELLOW_EX + "\n\n=== Rodapé ===")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + footer_text)

    print(Fore.LIGHTYELLOW_EX + "\n=== Links Internos ===\n")
    for link in internal:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + link)

    print(Fore.LIGHTYELLOW_EX + "\n=== Links Externos ===\n")
    for link in external:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + link)

    print(Fore.LIGHTYELLOW_EX + "\n=== Imagens ===\n")
    for i in imgs:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + i)

    print(Fore.LIGHTYELLOW_EX + "\n=== Scripts JS ===\n")
    for s in scripts:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + s)

    print(Fore.LIGHTYELLOW_EX + "\n=== CSS ===\n")
    for c in css:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + c)

    print(Fore.LIGHTYELLOW_EX + "\n=== URL em content= ===\n")
    for u in meta_urls:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + u)

def save_report(url, seo, internal, external, imgs, scripts, css, meta_urls, footer_text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write("=== SEO ===\n")
        f.write(f"\nTítulo: {seo['title']}\n")
        f.write(f"\nDescrição: {seo['meta_description']}\n")
        f.write(f"\nH1: {seo['h1']}\n")
        f.write(f"\nH2: {seo['h2']}\n\n")

        f.write("\n=== Rodapé ===\n\n")
        f.write(f"{footer_text}\n\n")

        f.write("\n=== Links Internos ===\n\n")
        for link in internal:
            f.write(link + "\n")
        f.write("\n")

        f.write("\n=== Links Externos ===\n\n")
        for link in external:
            f.write(link + "\n")
        f.write("\n")

        f.write("\n=== Imagens ===\n\n")
        for i in imgs:
            f.write(i + "\n")
        f.write("\n")

        f.write("\n=== Scripts JS ===\n\n")
        for s in scripts:
            f.write(s + "\n")
        f.write("\n")

        f.write("\n=== CSS ===\n\n")
        for c in css:
            f.write(c + "\n")
        f.write("\n")

        f.write("\n=== URL em content= ===\n\n")
        for u in meta_urls:
            f.write(u + "\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n✅ Relatório salvo como: {filename}")

def main():
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do site (ex: https://exemplo.com): ").strip()
    html = fetch_site_html(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")
    text = extract_text(soup)
    keywords = count_keywords(text)  # opcional
    internal, external = extract_links(soup, url)
    seo = extract_seo_data(soup)
    imgs, scripts, css = extract_resources(soup, url)
    meta_urls = extract_urls_from_meta(soup)
    footer_text = extract_footer(soup)

    display_report(url, seo, internal, external, imgs, scripts, css, meta_urls, footer_text)

    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar o relatório em arquivo? (s/n): ").strip().lower()
    if salvar == "s":
        nome_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (sem .txt): ").strip()
        if not nome_arquivo:
            nome_arquivo = "relatorio"
        nome_arquivo += ".txt"
        save_report(url, seo, internal, external, imgs, scripts, css, meta_urls, footer_text, nome_arquivo)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n\n  ========== PRESSIONE ENTER PARA SAIR ==========\n")
