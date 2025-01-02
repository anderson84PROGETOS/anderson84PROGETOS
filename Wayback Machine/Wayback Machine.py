import requests
import json
import threading
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
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
    response = requests.get(
        f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&output=json&fl=original&collapse=urlkey"
    )

    # Verificar se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Converter a resposta JSON em um objeto Python
        data = json.loads(response.text)

        # Verificar se existem dados
        if not data:
            print("\nNenhuma URL encontrada para o domínio fornecido.")
            return

        # Capturar URLs
        for url in data:
            filtered_url = url[0].replace("original", "")  # Filtrar a palavra "original"
            captured_urls.add(filtered_url)  # Adicionar ao conjunto para evitar duplicatas

        # Exibir as URLs
        print(Fore.LIGHTRED_EX + f"\n\nForam capturadas as seguintes URL do Wayback Machine\n" + "="*52)
        for filtered_url in captured_urls:
            print(f"{filtered_url}")  # Exibir a URL
        print(Fore.LIGHTGREEN_EX + f"\n\nForam capturadas: {len(captured_urls)} URL")
    else:
        print(f"\nErro: Não foi possível capturar as URL. Código de status do servidor: {response.status_code}.")

def save_urls_to_file(urls_content):
    # Pede ao usuário para escolher o nome do arquivo
    file_path = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar as URL (ex: arquivo.txt): ")

    # Tenta salvar o conteúdo no arquivo
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            # Escrever a quantidade de URLs encontradas
            file.write(f"Total de URL Encontradas: {len(urls_content)}\n\n")
            # Gravar as URLs em linhas separadas
            file.write("\n".join(urls_content).strip())  
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nSucesso: As URL foram salvas com sucesso em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {str(e)}")

def start_search():
    url = input(Fore.LIGHTGREEN_EX + "\nDigite a URL que deseja procurar no Wayback Machine: ")    
    search_wayback_machine(url)    

if __name__ == "__main__":
    # Iniciar a busca em uma thread separada
    search_thread = threading.Thread(target=start_search)
    search_thread.start()
    search_thread.join()

    # Após a busca, oferecer a opção de salvar as URLs
    if captured_urls:  # Verificar se as URLs foram capturadas
        while True:
            save_option = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDeseja salvar as URL em um arquivo? (s/n): ").lower()
            if save_option == 's':
                save_urls_to_file(captured_urls)  # Usa as URLs capturadas anteriormente
                break
            elif save_option == '':
                print(Fore.LIGHTRED_EX + "\nAs URL não foram salvas.")
                break
            elif save_option == 'n':
                print(Fore.LIGHTRED_EX + "\nAs URL não foram salvas.")
                break
    else:
        print("\nErro: Nenhuma URL foi capturada para salvar.")

input(Fore.LIGHTMAGENTA_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
