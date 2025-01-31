import requests
import os
import time
import sys
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗ ██╗██████╗ ██████╗      ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗ 
██╔══██╗██║██╔══██╗██╔══██╗    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║  ██║██║██████╔╝██████╔╝    ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
██║  ██║██║██╔══██╗██╔══██╗    ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██████╔╝██║██║  ██║██████╔╝    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
╚═════╝ ╚═╝╚═╝  ╚═╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                                                                                                                                                                
""")

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()  # Obtém o diretório atual
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, insira um número válido.")

# Leitura do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()

# Abrindo o arquivo de wordlist
with open(wordlist_file, 'r', encoding='utf-8') as f:
    lista = f.read().splitlines()

# Digitar a URL base
url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website: ")

# Certifique-se de que a URL termina sem barra
if not url.endswith('/'):
    url += '/'

print("\n")

# Inicializando contador de diretórios válidos
count = 1  

# Armazenar resultados para salvar depois
resultados = []

# Percorrendo a lista de caminhos da wordlist
for i in lista:
    url_to_check = url + i
    try:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"TESTANDO: {url_to_check}", end="\r", flush=True)
        response = requests.get(url_to_check, timeout=5)

        if response.status_code in [404, 500]:
            continue

        if response.status_code == 200:
            color = Fore.GREEN  # Sucesso
        elif response.status_code in [301, 302]:
            color = Fore.CYAN  # Redirecionamento
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"  [Redirecionamento] - {response.url}")
        elif response.status_code == 403:
            color = Fore.RED   # Acesso negado
        elif response.status_code == 429:
            color = Fore.YELLOW # Muitas requisições
        elif response.status_code == 400:
            color = Fore.MAGENTA  # Requisição inválida  
        else:
            color = Fore.WHITE  # Outros códigos

        result = f"{count:<4}: {url_to_check:<72}  CODE: {response.status_code}"
        print(color + Style.BRIGHT + result + Style.RESET_ALL)
        resultados.append(result)
        count += 1

        time.sleep(0.3)

    except requests.exceptions.RequestException:
        time.sleep(0.3)  # Mantendo consistência visual

# Perguntar se o usuário deseja salvar os resultados
salvar = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados? (s/n): ").lower()

if salvar == 's':
    nome_arquivo = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (exemplo: resultados.txt): ")

    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        for resultado in resultados:
            f.write(resultado + "\n")

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados Salvos Em: {nome_arquivo}")

# Finalizar o programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== SCAN FINALIZADO. PRESSIONE ENTER PARA SAIR ==========\n\n")
