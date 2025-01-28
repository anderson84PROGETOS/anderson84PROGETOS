import requests
import os
import time  # Adicionado para controlar a velocidade
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
    txt_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt Encontrado na pasta.")
        exit()

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            print("\n")
            if 1 <= choice <= len(txt_files):
                return os.path.join(os.path.dirname(__file__), txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, insira um número válido.")

# Leitura do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()

# Abrindo o arquivo de wordlist
with open(wordlist_file, 'r') as f:
    lista = f.read().splitlines()

# Digitar a URL base
url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website: ")

# Certifique-se de que a URL termina sem barra
if not url.endswith('/'):
    url += '/'

print("\n")

# Inicializando contador de diretórios válidos
count = 1  

# Percorrendo a lista de caminhos da wordlist
for i in lista:
    url_to_check = url + i
    try:
        # Fazendo a requisição HTTP
        response = requests.get(url_to_check, timeout=5)

        # Mostrando progresso como no Dirb
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"TESTANDO: {url_to_check}", end="\r", flush=True)

        # Se o diretório ou arquivo for encontrado (status 200)
        if response.status_code == 200:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"DIRETÓRIO ENCONTRADO ({count}): {url_to_check}")
            count += 1

        # Pequeno atraso para evitar sobreposição visual e reduzir uso de recursos
        time.sleep(0.3)

    # Tratando erros de conexão (silenciado para simular Dirb)
    except requests.exceptions.RequestException:
        time.sleep(0.3)  # Mesmo atraso para manter consistência

# Finalizar o programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== SCAN FINALIZADO. PRESSIONE ENTER PARA SAIR ==========\n\n")
