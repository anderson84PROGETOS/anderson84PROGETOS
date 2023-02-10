import requests
from bs4 import BeautifulSoup

# nome do site
site = input("\nDigite o nome do site (exemplo: www.google.com): ")

# fazendo a requisição ao site
response = requests.get(f"http://{site}")

# verificando se a requisição foi bem-sucedida
if response.status_code == 200:
    # parseando o conteúdo da página com BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    # extraindo todos os links da página
    links = soup.find_all("a")

    # lista para armazenar os subdomínios
    subdomains = []

    # percorrendo todos os links da página
    for link in links:
        # extrair o endereço completo do link
        url = link.get("href")

        # verificando se o link é um subdomínio do site
        if url and site in url and url not in subdomains:
            subdomains.append(url)

    # escrevendo os subdomínios encontrados no arquivo
    with open("subdomains.txt", "w") as file:
        for subdomain in subdomains:
            file.write(subdomain + "\n")
            
    # imprimindo os subdomínios encontrados
    print("\n ↓↓ Subdomínios encontrados ↓↓\n")
    for subdomain in subdomains:
        print(subdomain)

    print(f"\n Subdomínios encontrados foram salvos no arquivo 'subdomains.txt'")
else:
    print("\n Ocorreu um erro ao acessar o site.")
    
input("\n FIM [ENTER] SAIR \n")     

