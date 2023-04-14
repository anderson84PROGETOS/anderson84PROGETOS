import requests
import json
import argparse

def wayback_machine(url, output_file=None):
    # Construir a URL da API do Wayback Machine do Internet Archive
    api_url = "http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url)

    # Fazer uma solicitação GET à API
    response = requests.get(api_url)

    # Analisar a resposta JSON
    if response.status_code == 200:
        data = json.loads(response.text)

        # Verificar se há capturas de tela do site
        if len(data) > 1:
            print("\n🔎 Capturas de tela disponíveis para o site 🔍\n")
            urls = []
            for item in data[1:]:
                url = item[0]
                urls.append(url)
                print(url)
            # Salvar as URLs em um arquivo de texto, se necessário
            if output_file is not None:
                with open(output_file, "w", encoding="utf-8") as f:
                    for url in urls:
                        f.write(url + "\n")
                count = len(urls)
                print("\nForam salvos {} links no arquivo {}.".format(count, output_file))
        else:
            print("\nNenhuma captura de tela disponível para o site.")
    else:
        print("\nNão foi possível acessar o Wayback Machine do Internet Archive.")

# Definir os argumentos da linha de comando
print("\n")
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description="Como usar o script: python3 wayback_machine.py example.com -o captures.txt")
parser.add_argument("url", help="Digite o nome do site para verificar capturas de tela")
parser.add_argument("-o", "--output", help="Nome do arquivo para salvar as URLs das capturas de tela")

args = parser.parse_args()

# Chamar a função wayback_machine
wayback_machine(args.url, args.output)
