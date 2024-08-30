import requests
from bs4 import BeautifulSoup

print(""""

██╗    ██╗███████╗██████╗      ██████╗██████╗  █████╗ ██╗    ██╗██╗     ██╗███╗   ██╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗    ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██║████╗  ██║██╔════╝ 
██║ █╗ ██║█████╗  ██████╔╝    ██║     ██████╔╝███████║██║ █╗ ██║██║     ██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══╝  ██╔══██╗    ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██║██║╚██╗██║██║   ██║
╚███╔███╔╝███████╗██████╔╝    ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                             
""")

def web_crawler(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        
        # Usar um conjunto para armazenar URLs únicas
        unique_links = set()
        
        for link in links:
            href = link.get('href')
            # Filtrar apenas URLs que começam com http ou https
            if href and (href.startswith('http://') or href.startswith('https://')) and href not in unique_links:
                unique_links.add(href)
        
        # Procurar por URLs em tags meta
        metas = soup.find_all('meta')
        for meta in metas:
            content = meta.get('content')
            if content and (content.startswith('http://') or content.startswith('https://')) and content not in unique_links:
                unique_links.add(content)

        # Mostrar todas as URLs encontradas
        for link in unique_links:
            print(link)
        
        # Mostrar o total de URLs encontradas
        total_urls = len(unique_links)
        print(f"\n\nTotal de URL Encontradas: {total_urls}")
        
        # Perguntar se o usuário deseja salvar as URLs em um arquivo
        save_option = input("\n\nDeseja salvar as URL em um arquivo? (s/n): ").strip().lower()
        if save_option == 's':
            filename = input("\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
            with open(filename, 'w') as file:
                for link in unique_links:
                    file.write(link + "\n")
                # Salvar também a contagem de URLs no arquivo
                file.write(f"\nTotal de URL Encontradas: {total_urls}\n")
            print(f"\nURL salvas Em: {filename}")
            
        else:
            print("\nURL não foram salvas")
    else:
        print(f"Erro ao acessar {url}: Status code {response.status_code}")

# Solicita ao usuário que insira a URL
url = input("\nDigite a URL do website: ")
print(f"\nURL Encontradas\n===============\n")
web_crawler(url)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
