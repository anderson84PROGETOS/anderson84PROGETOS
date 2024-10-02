import requests
from bs4 import BeautifulSoup

print("""
███████╗██╗████████╗███████╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██╔════╝██║╚══██╔══╝██╔════╝    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
███████╗██║   ██║   █████╗      ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
╚════██║██║   ██║   ██╔══╝      ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
███████║██║   ██║   ███████╗    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚══════╝╚═╝   ╚═╝   ╚══════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
""")

def get_site_info(url):
    # Definindo os cabeçalhos personalizados
    headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    results = []  # Lista para armazenar resultados

    try:
        # Fazendo uma requisição GET ao site com os cabeçalhos
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta um erro se a requisição falhar

        # Analisando o conteúdo HTML com BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraindo o título da página
        title = soup.title.string if soup.title else 'Sem título'
        results.append(f'Título da página: {title}\n')

        # Extraindo todos os cabeçalhos (h1, h2, h3, etc.)
        headers = {f'h{i}': [header.get_text(strip=True) for header in soup.find_all(f'h{i}')] for i in range(1, 7)}
        for h, texts in headers.items():
            if texts:
                results.append(f'{h}: {texts}\n')

        # Extraindo todos os links da página e filtrando por http/https
        links = {a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith(('http://', 'https://'))}

        # Extraindo URLs de outras tags que podem conter links (src, data-src, etc.)
        sources = {tag['src'] for tag in soup.find_all(src=True) if tag['src'].startswith(('http://', 'https://'))}

        # Extraindo URLs do atributo content de tags meta
        meta_links = {meta['content'] for meta in soup.find_all('meta', content=True) if meta['content'].startswith(('http://', 'https://'))}

        # Unindo todas as URLs encontradas
        all_links = links.union(sources).union(meta_links)

        # Exibir links encontrados
        results.append('\nLinks Encontrados\n=================\n')
        for link in all_links:
            results.append(f'{link}\n')  # Adicionando cada link em uma nova linha com espaço antes
        
        # Exibir o número total de URLs encontradas
        total_links = len(all_links)
        results.append(f'\nTotal de URL Encontradas: {total_links}\n')
    
    except requests.exceptions.RequestException as e:
        results.append(f'\nErro ao acessar o site: {e}\n')

    return results  # Retorna os resultados coletados

# Solicitar a URL do usuário
url = input("\nDigite a URL do website (ex: https://example.com): ")

# Chamar a função para obter informações do site
results = get_site_info(url)
print("\n")
# Exibir os resultados no console
for line in results:
    print(line)

# Perguntar se o usuário deseja salvar os resultados
save_option = input("\nDeseja salvar os resultados? (s/n): ").strip().lower()

if save_option == 's':
    filename = input("\nDigite o nome do arquivo para salvar (ex: arquivo.txt): ")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(f"{line}\n" for line in results)  # Salva os resultados no arquivo com quebras de linha
        print(f'\nResultados salvos Em: {filename}')
    except Exception as e:
        print(f'\nErro ao salvar o arquivo: {e}')

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
