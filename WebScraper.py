import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

print("""

    ██╗    ██╗███████╗██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗     
    ██║    ██║██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗    
    ██║ █╗ ██║█████╗  ██████╔╝    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝    
    ██║███╗██║██╔══╝  ██╔══██╗    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗    
    ╚███╔███╔╝███████╗██████╔╝    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║    
     ╚══╝╚══╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝    
                                                                                              
                                                                                                                           
""")

url = input("\nDigite a URL do Website: ")

resposta = requests.get(url)

if resposta.status_code != 200:
    print("Erro na URL")
    exit()

dominio_base = urlparse(url).netloc

sopa = BeautifulSoup(resposta.content, features='html.parser')

# Encontrar todos os subdomínios nos URLs
subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', resposta.text))

# Imprimir subdomínios na tela e mostrar o número de subdomínios
print(f"\nForam Encontrados ====>  {len(subdomains)}  Subdomínios\n")
for subdomain in subdomains:
    print(subdomain)

# Encontrar todos os links (URLs)
links = sopa.find_all('a', href=True)
urls = {link['href'] for link in links if link['href'].startswith('http://') or link['href'].startswith('https://') or link['href'].startswith('/')}  # Usando set comprehension para criar um conjunto de URLs

# Construir URLs completas
urls_completas = {urljoin(url, link) if link.startswith('/') else link for link in urls}  # Usando set comprehension para criar um conjunto de URLs completas

# Filtrar URLs internas
urls_internas = {link for link in urls_completas if dominio_base in urlparse(link).netloc}  # Usando set comprehension para criar um conjunto de URLs internas

# Imprimir URLs internos na tela e mostrar o número de URLs internas
print(f"\nForam Encontradas ====>  {len(urls_internas)}   URL internas\n")
for url in urls_internas:
    print(url)

# Perguntar ao usuário se deseja salvar os resultados em um arquivo
salvar_arquivo = input("\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()

if salvar_arquivo == 's':
    arquivo_saida = input("\nNome do Arquivo de Saída (exemplo: arquivo.txt): ")
    
    with open(arquivo_saida, 'w', encoding='utf-8') as file:
        file.write(f"\nForam Encontrados ====>  {len(subdomains)}  Subdomínios\n\n")
        for subdomain in subdomains:
            file.write(subdomain + '\n')
        
        file.write(f"\nForam Encontradas ====>  {len(urls_internas)}  URL internas\n\n")
        for url in urls_internas:
            file.write(url + '\n')
    
    print(f"\nOs Resultados Foram Salvos Em: {arquivo_saida}\n")
elif salvar_arquivo == 'n':
    print("\nOs Resultados Não Foram salvos\n")
else:
    print("\nOpção inválida. Os Resultados Não Foram salvos\n")

input("\nPRESSIONE [ENTER SAIR]\n")
