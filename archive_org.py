import requests
import json

# Obter a URL do usuário
url = input("\nDigite a URL que deseja procurar no Wayback Machine: ")

# Fazer uma solicitação HTTP para o Arquivo de Internet do Wayback Machine
response = requests.get("http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url))

# Verificar se a solicitação foi bem-sucedida
if response.status_code == 200:
    # Converter a resposta JSON em um objeto Python
    data = json.loads(response.text)
    
    # Perguntar ao usuário o nome do arquivo de saída
    output_file_name = input("\nDigite o nome do arquivo de saída [ Exemplo: exemplo.txt ]: ")
    
    # Salvar as URLs capturadas no arquivo de saída
    with open(output_file_name, "w", encoding="utf-8") as f:
        for url in data:
            f.write(url[0] + "\n")


     # Mostrar as URLs capturadas na tela
    print("\n↓↓ Foram capturadas as seguintes URL ↓↓\n")
    for url in data:
        print(url[0])        
    
    # Mostrar o número de URLs capturadas na tela
    print("\nForam capturadas {} URL".format(len(data)))
    
else:
    print("Não foi possível capturar as URLs. O servidor retornou o código de status {}.".format(response.status_code))
    
    
input("\nScan Completo Aperte ENTER SAIR\n")
