import requests
from bs4 import BeautifulSoup

# Pede a URL do website e o nome do arquivo para salvar as URLs
url = input("\nDigite a URL do website: ")
filename = input("\nDigite o nome do arquivo para salvar as URLs: ")

print("\n↓↓ as url do href foram encontradas ↓↓\n")

# Realiza a requisição HTTP para obter o conteúdo da página
response = requests.get(url)

# Cria o objeto BeautifulSoup para analisar o conteúdo HTML
soup = BeautifulSoup(response.content, "html.parser")

# Cria um conjunto para armazenar as URLs únicas
unique_urls = set()

# Percorre todas as tags <a> da página e extrai o valor do atributo href
for link in soup.find_all("a"):
    href = link.get("href")
    
    # Verifica se a URL começa com "http" ou "https" e se ainda não foi capturada
    if href and href.startswith(("http", "https")) and href not in unique_urls:
        unique_urls.add(href)

# Salva as URLs únicas em um arquivo e mostra na tela
with open(filename, "w") as file:
    for url in unique_urls:
        file.write(url + "\n")
        print(url)

# Imprime a mensagem de conclusão
print(f"\nAs URLs foram salvas em: {filename}")

input("\n==> fim do href website aperte Enter pra sair <==\n")
