import requests
from concurrent.futures import ThreadPoolExecutor
import sys

# Solicita ao usuário para digitar o nome do website
website = input("\nDigite a url do website: ").strip()

# Verifica se o website foi digitado
if not website:
    print("Você não digitou o nome do website. Saindo...")
    sys.exit(1)

# Função para verificar diretórios
def check_directory(palavra):
    url = f"{website}/{palavra}/"
    try:
        resposta = requests.head(url, allow_redirects=True)
        if resposta.status_code == 200:
            print(f"Diretório encontrado: {palavra}")
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")

# Função para verificar arquivos
def check_file(palavra):
    url = f"{website}/{palavra}"
    try:
        resposta = requests.head(url, allow_redirects=True)
        if resposta.status_code == 200:
            print(f"Arquivo encontrado: {palavra}")
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")

# Lê o arquivo lista.txt
with open('lista.txt') as f:
    palavras = f.read().splitlines()

# Primeiro, verifica os diretórios
print("")
print("Procurando diretórios...\n")
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(check_directory, palavras)

print("\n\nProcurando arquivos...\n")
# Depois, verifica os arquivos
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(check_file, palavras)
    
input("\n\n🎯 Pressione Enter para sair 🎯\n")   
