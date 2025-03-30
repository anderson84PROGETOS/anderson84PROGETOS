import requests
import urllib.parse
from collections import deque
import re

def process_url():
    # Solicita a URL do usuário
    user_url = input("Insira o Nome ou a URL do WebSite: ")
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url
    
    urls = deque([user_url])
    scrapped_urls = set()
    emails = set()
    count = 0

    # Cabeçalhos HTTP para evitar erro 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    print("\nIniciando o processamento...\n")
    
    while urls and count < 100:
        url = urls.popleft()
        count += 1

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Verifica erros na requisição HTTP
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                pass
                continue
            else:
                print(f"\nErro HTTP: {url}")
                continue
        except requests.exceptions.RequestException as e:
            pass
            continue
        except KeyboardInterrupt:
            print('\n[-] Fechando!')
            break

        scrapped_urls.add(url)
        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        path = url[:url.rfind('/') + 1] if '/' in parts.path else url
        
        print(f"\n{url}")
        
        # Busca emails na página
        new_emails = set(re.findall(r'[a-z0-9\. \-+_]+@[a-z0-9\. \-+_]+\.[a-z]+', response.text, re.I))
        emails.update(new_emails)
        
        # Processa links da página
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.find_all("a"):
            link = anchor.get('href', '')
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith(('http:', 'https:')):
                link = urllib.parse.urljoin(url, link)
            if link not in urls and link not in scrapped_urls:
                urls.append(link)    
        
    # Exibe resultados
    print("\n\n################## Emails Encontrados ######################\n")
    for email in emails:
        print("\n", email)
    print(f"\n\nTotal de URL Encontradas: {len(scrapped_urls)}")
    print(f"Total de Emails Encontrados: {len(emails)}")

if __name__ == "__main__":
    process_url()

input("\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
