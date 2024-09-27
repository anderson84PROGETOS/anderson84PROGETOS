import requests
import json
import threading

print("""\

██╗    ██╗ █████╗ ██╗   ██╗██████╗  █████╗  ██████╗██╗  ██╗    ███╗   ███╗ █████╗  ██████╗██╗  ██╗██╗███╗   ██╗███████╗
██║    ██║██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ████╗ ████║██╔══██╗██╔════╝██║  ██║██║████╗  ██║██╔════╝
██║ █╗ ██║███████║ ╚████╔╝ ██████╔╝███████║██║     █████╔╝     ██╔████╔██║███████║██║     ███████║██║██╔██╗ ██║█████╗  
██║███╗██║██╔══██║  ╚██╔╝  ██╔══██╗██╔══██║██║     ██╔═██╗     ██║╚██╔╝██║██╔══██║██║     ██╔══██║██║██║╚██╗██║██╔══╝  
╚███╔███╔╝██║  ██║   ██║   ██████╔╝██║  ██║╚██████╗██║  ██╗    ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██║ ╚████║███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝

""")

captured_urls = set()  # Usar um conjunto para eliminar URLs duplicadas

def search_wayback_machine(url):
    global captured_urls
    # Fazer uma solicitação HTTP para o Arquivo de Internet do Wayback Machine
    response = requests.get("http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url))

    # Verificar se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Converter a resposta JSON em um objeto Python
        data = json.loads(response.text)

        # Verificar se existem dados
        if not data:
            print("\nNenhuma URL encontrada para o domínio fornecido.")
            return

        print("\nForam capturadas as seguintes URL do Wayback Machine\n" + "="*52)

        # Exibir e armazenar as URLs capturadas
        for url in data:
            filtered_url = url[0].replace("original", "")  # Filtrar a palavra "original"
            print(f"\n{filtered_url}")  # Exibir a URL com uma linha em branco antes
            captured_urls.add(filtered_url)  # Adicionar ao conjunto para evitar duplicatas

        print("\n\nForam capturadas: {} URL".format(len(captured_urls)))
    else:
        print("\nErro: Não foi possível capturar as URL. Código de status do servidor: {}.".format(response.status_code))

def save_urls_to_file(urls_content):
    # Pede ao usuário para escolher o nome do arquivo
    file_path = input("\nDigite o nome do arquivo para salvar as URL (ex: arquivo.txt): ")    

    # Tenta salvar o conteúdo no arquivo
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n\n".join(urls_content).strip())  # Gravar as URLs com uma linha em branco entre elas
        print("\nSucesso: As URL foram salvas com sucesso Em: {}".format(file_path))
    except Exception as e:
        print("Erro ao salvar o arquivo: {}".format(str(e)))

def start_search():
    url = input("\nDigite a URL que deseja procurar no Wayback Machine: ")
    search_wayback_machine(url)

if __name__ == "__main__":
    # Iniciar a busca em uma thread separada
    search_thread = threading.Thread(target=start_search)
    search_thread.start()
    search_thread.join()

    # Após a busca, oferecer a opção de salvar as URLs
    if captured_urls:  # Verificar se as URLs foram capturadas
        while True:
            save_option = input("\nDeseja salvar as URL em um arquivo? (s/n): ").lower()
            if save_option == 's':
                save_urls_to_file(captured_urls)  # Usa as URLs capturadas anteriormente
                break
            elif save_option == 'n':
                break
            else:
                print("\nOpção inválida. Por favor, digite 's' para sim ou 'n' para não.")
    else:
        print("\nErro: Nenhuma URL foi capturada para salvar.")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
