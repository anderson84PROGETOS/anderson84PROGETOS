import tldextract
import requests
import socket

# Pede ao usuário para inserir o nome do domínio
domain_name = input("\nDigite o nome do domínio: ")

# Extrai o domínio do nome inserido pelo usuário
domain = tldextract.extract(domain_name).registered_domain

# Obtém o endereço IP do domínio
try:
    ip = socket.gethostbyname(domain)
    print(f"\nEndereço IP de {domain}: {ip}")
except socket.gaierror:
    print(f"\nNão foi possível obter o endereço IP de {domain}")

# Consulta o site urlscan.io para informações adicionais sobre o domínio
urlscan_url = f"\nhttps://urlscan.io/api/v1/search/?q=domain:{domain}"
response = requests.get(urlscan_url)
if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    for result in results:
        print(f"\nURL: {result['task']['url']}")        
        
else:
    print(f"\nErro ao consultar o site urlscan.io para o domínio {domain}")

input("\n🔎 consulta terminada urlscan 🔍\n")
