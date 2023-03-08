import tldextract
import requests
import socket

# Obter o nome de domínio a partir da entrada do usuário
domain = input("\nDigite o nome do site (exemplo.com): ")
# Extrair o nome do domínio e o sufixo a partir do nome completo do domínio
extracted_domain = tldextract.extract(domain)
# Formatar o nome de domínio extraído para ser usado na consulta da API
formatted_domain = extracted_domain.registered_domain

# Construir a URL da API com o nome de domínio formatado
url = f"https://urlscan.io/api/v1/search/?q=domain:{formatted_domain}"

# Fazer uma solicitação GET à API com a URL construída
response = requests.get(url)

# Verificar se a solicitação foi bem sucedida
if response.status_code == 200:
    # Analisar a resposta JSON para obter as informações desejadas
    results = response.json()["results"]
    if len(results) > 0:
        # Salvar as informações em um arquivo especificado pelo usuário
        filename = input("\nDigite o nome do arquivo para salvar as informações: ")
        urls = set()
        count = 0
        with open(filename, "w") as f:
            f.write(f"Endereço IP do site {domain}: {socket.gethostbyname(domain)}\n\n")
            for result in results:
                url = result['page']['url']
                if url not in urls:
                    urls.add(url)
                    count += 1
                    f.write(f"URL {count}: {url}\n")

                    # Mostrar os resultados na tela
        print(f"\nEndereço IP do site {domain}: {socket.gethostbyname(domain)}\n")
                    
        print(f"\n ⬇️ ⬇️  Foram salvas {count} URLs no arquivo ⬇️ ⬇️\n") 

        for i, url in enumerate(urls, 1):
            print(f"URL {i}: {url}")
        print(f"\n📃 Foram encontradas {count} URL 📃")
    else:
        print("\nNenhuma informação encontrada para este domínio.")
else:
    print("\nA solicitação à API falhou. Verifique se o nome de domínio foi digitado corretamente.")

input("\n🔎 Consulta terminada urlscan Enter Sair 🔍\n")
