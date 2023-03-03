import requests
import json

def wayback_machine(url):
    # Construir a URL da API do Wayback Machine do Internet Archive
    api_url = "http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url)

    # Fazer uma solicitação GET à API
    response = requests.get(api_url)

    # Analisar a resposta JSON
    if response.status_code == 200:
        data = json.loads(response.text)

        # Verificar se há capturas de tela do site
        if len(data) > 1:
            print("\n🔎 Capturas de url disponíveis para o site 🔍\n")
            for item in data[1:]:
                print(item[0])
        else:
            print("\n🔎 Nenhuma captura de url disponível para o site 🔍\n")
    else:
        print("\n🔎 Não foi possível acessar o Wayback Machine do Internet Archive 🔍\n")

# Pedir ao usuário para digitar o nome do site
url = input("\nDigite o nome do site para verificar capturas da url: ")

# Chamar a função wayback_machine
wayback_machine(url)

input("\n🔎 Escaneamento Terminado archive 🔍\n")
