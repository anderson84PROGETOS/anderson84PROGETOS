import requests
from bs4 import BeautifulSoup
import os
from docx import Document
from reportlab.pdfgen import canvas

# Solicita ao usuário que insira o nome que deseja pesquisar
nome = input("\nDigite o nome que deseja pesquisar: ")

# Usa a biblioteca requests para obter o conteúdo da página
url = "https://www.google.com/search?q=" + nome
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
html = requests.get(url, headers=headers).content

# Usa a biblioteca BeautifulSoup para analisar o conteúdo da página em busca de nomes correspondentes
soup = BeautifulSoup(html, 'html.parser')
resultados = soup.find_all('div', {'class': 'g'})

# Solicita ao usuário que escolha o formato de arquivo desejado
formato = input("\nDigite o formato de arquivo que deseja salvar (TXT, PDF ou DOC): ").lower()

# Cria um arquivo de texto e escreve nele os links encontrados durante a busca
filename = input("\nDigite o nome do arquivo para salvar: ")
if formato == "txt":
    file_path = filename + ".txt"
    textfile = open(file_path, 'w')
elif formato == "pdf":
    file_path = filename + ".pdf"
    canvas = canvas.Canvas(file_path)
elif formato == "doc":
    file_path = filename + ".docx"
    document = Document()
else:
    print("\nFormato inválido.")
    exit()

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
if formato == "txt":
    textfile.close()
    print("\nForam salvos {} links no arquivo {}.".format(count, file_path))
elif formato == "pdf":
    canvas.save()
    print("\nForam salvos {} links no arquivo {}.".format(count, file_path))
elif formato == "doc":
    document.save(file_path)
    print("\nForam salvos {} links no arquivo {}.".format(count, file_path))

input("\nGoogle Hacker Terminado {ENTER SAIR}\n") 
