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
    print(f"nEndereço IP de {domain}: {ip}")        
        
except socket.gaierror:
    print(f"\nNão foi possível obter o endereço IP de {domain}")

# Consulta o site urlscan.io para obter as URLs do domínio
urlscan_url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
response = requests.get(urlscan_url)
if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    urls = set()  # Conjunto vazio para armazenar as URLs únicas
    for result in results:
        url = result['task']['url']
        if url not in urls:
            urls.add(url)

    # Pede ao usuário para inserir o nome do arquivo para salvar as URLs
    filename = input("\nDigite o nome do arquivo para salvar: ")
    with open(filename, 'w') as f:
        f.write(f"Endereço IP de {domain}: {ip}\n\n")
        for url in urls:
            f.write(url + '\n')
    print(f"\nUrls encontradas: {len(urls)}")
else:
    print(f"\nErro ao consultar o site urlscan.io para o domínio {domain}")
    
input("\n🔎 consulta terminada ip-urlscan 🔍\n")    
