import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# specify the URL of the site you want to use
# especifique o URL do site que você deseja utilizar
url = input("\nDigite a url do website: ")

# send a GET request to the website
# enviar uma solicitação GET para o site
response = requests.get(url)

# save file
# salvar arquivo
filename = input("\nDigite o nome do arquivo para salvar: ")
textfile = open(filename, 'w')

print("\n↓↓ href Encontrado na url ↓↓\n")

# parse the HTML content using BeautifulSoup
# analisar o conteúdo HTML usando BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# find all the <a> tags on the page
# encontre todas as tags <a> na página
links = soup.find_all("a")

count = 0
# loop through all the links and print out the ones that start with "http" or "https"
# percorra todos os links e imprima aqueles que começam com "http" ou "https"
for link in links:
    href = link.get("href")
    if href:
        parsed_url = urlparse(href)
        if parsed_url.scheme in ["http", "https"]:
            count += 1
            textfile.write(href + "\n")
            print(href)

textfile.close()

print("\nForam salvos {} links.".format(count))

input("\nExtrador de url href Terminado {ENTER SAIR}\n") 
