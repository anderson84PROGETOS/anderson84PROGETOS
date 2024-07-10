import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

print("""

███████╗ ██████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ 
███████╗██║     ██████╔╝███████║██████╔╝██║██╔██╗ ██║██║  ███╗
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██║██║╚██╗██║██║   ██║
███████║╚██████╗██║  ██║██║  ██║██║     ██║██║ ╚████║╚██████╔╝
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                              
""")

# Função para extrair emails e URLs únicos de uma URL
def extract_emails_and_urls_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Conjuntos para armazenar emails e URLs únicos
    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text))
    urls = set()

    # Função para normalizar e validar URLs
    def normalize_url(url, base_url):
        normalized = urljoin(base_url, url)
        parsed_url = urlparse(normalized)
        if parsed_url.scheme in ('http', 'https') and parsed_url.netloc:
            return normalized
        return None

    # Extração de URLs de links e conteúdo geral
    for tag_name in ["a", "href"]:
        for tag in soup.find_all(tag_name):
            if tag_name == "a" and "href" in tag.attrs:
                href = tag["href"]
                normalized_url = normalize_url(href, url)
                if normalized_url:
                    urls.add(normalized_url)
            elif tag_name == "href":
                href_urls = re.findall(r'(?<=href=["\'])https?://[^"\']+|(?<=href=["\'])[^"\']+', str(tag))
                for href in href_urls:
                    normalized_url = normalize_url(href, url)
                    if normalized_url:
                        urls.add(normalized_url)

    # Extração de URLs do conteúdo textual da página (código fonte)
    text_urls = re.findall(r'(?<=href=["\'])https?://[^"\']+|(?<=href=["\'])[^"\']+', response.text)
    for text_url in text_urls:
        normalized_url = normalize_url(text_url, url)
        if normalized_url:
            urls.add(normalized_url)

    # Extração de URLs do atributo 'content'
    content_urls = re.findall(r'(?<=content=["\'])https?://[^"\']+|(?<=content=["\'])[^"\']+', response.text)
    for content_url in content_urls:
        normalized_url = normalize_url(content_url, url)
        if normalized_url:
            urls.add(normalized_url)

    return emails, urls

# Função principal
def main():
    website_url = input("\nDigite a URL do website: ")
    emails, urls = extract_emails_and_urls_from_url(website_url)

    if emails:
        print(f"\n\nEmails Encontrados no website: {website_url}")
        print(f"\n{len(emails)} Emails no total\n")
        
        for email in emails:
            print(email)
    else:
        print("\n\nNenhum email encontrado.")

    if urls:
        print(f"\n\nURL Encontradas no website: {website_url}")
        print(f"\n{len(urls)} URL no total\n")
        for url in urls:
            print(url)
    else:
        print("\n\nNenhuma URL encontrada.")

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")  # Pausa antes de sair
