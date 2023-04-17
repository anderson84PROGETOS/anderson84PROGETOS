import requests
from bs4 import BeautifulSoup

# Solicita ao usuário que insira o nome que deseja pesquisar
nome = input("\nDigite o nome que deseja pesquisar: ")

# Usa a biblioteca requests para obter o conteúdo da página
url = "https://www.google.com/search?q=" + nome
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
html = requests.get(url, headers=headers).content

# Usa a biblioteca BeautifulSoup para analisar o conteúdo da página em busca de nomes correspondentes
soup = BeautifulSoup(html, 'html.parser')
resultados = soup.find_all('div', {'class': 'g'})

# Cria um arquivo de texto e escreve nele os links encontrados durante a busca
filename = input("\nDigite o nome do arquivo para salvar: ")
textfile = open(filename, 'w')

print("\n↓↓ links Encontrado na url ↓↓\n")

count = 0
for i, resultado in enumerate(resultados):
    try:
        link = resultado.find('a')['href']
        textfile.write(link + "\n")
        count += 1
    except:
        pass

# Exibe os resultados para o usuário
for resultado in resultados:
    try:
        link = resultado.find('a')['href']
        print(link)
    except:
        pass 

# Imprime a mensagem informando ao usuário quantos links foram salvos
print("\nForam salvos {} links no arquivo {}.".format(count, filename))

# Fecha o arquivo de texto
textfile.close()

input("\nGoogle Hacker Terminado {ENTER SAIR}\n") 
