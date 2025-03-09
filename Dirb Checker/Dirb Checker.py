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

# Definir cabeçalhos para simular um navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()
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

# Função para carregar a wordlist
def carregar_wordlist(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

# Leitura do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()
wordlist = carregar_wordlist(wordlist_file)
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nConteúdo da wordlist Total de palavras: {len(wordlist)}")

# Digitar a URL base
url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website: ")
if not url.endswith('/'):
    url += '/'

print("\n")

# Inicializando contador de diretórios válidos
count = 1  
# Armazenar resultados para salvar depois
resultados = []

# Percorrendo a lista de caminhos da wordlist
for i in wordlist:
    url_to_check = url + i
    try:
        # Exibir "TESTANDO" enquanto faz a requisição
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"TESTANDO: {url_to_check}", end="\r", flush=True)
        
        # Fazendo a requisição HTTP
        response = requests.get(url_to_check, headers=headers, timeout=5)
        
        # Filtrar apenas códigos 200 e 301
        if response.status_code not in [200, 301]:
            continue

        # Definir cor com base no código de resposta HTTP
        color = Fore.GREEN if response.status_code == 200 else Fore.CYAN

        # Exibir qualquer código de status encontrado
        result = f"{count:<4}: {url_to_check:<72}  CODE: {response.status_code}"
        print(color + Style.BRIGHT + result + Style.RESET_ALL)
        resultados.append(result)  # Armazenar o resultado para salvar
        count += 1
        
        time.sleep(0.3)  # Pequeno atraso para evitar sobrecarga

    except requests.exceptions.RequestException:
        time.sleep(0.3)  # Mesmo atraso para manter consistência

# Limpar a linha do "TESTANDO" após a varredura
print(" " * 100, end="\r", flush=True)

# Perguntar se o usuário deseja salvar os resultados
salvar = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados? (s/n): ").lower()
if salvar == 's':
    nome_arquivo = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (exemplo: resultados.txt): ")
    with open(nome_arquivo, 'w') as f:
        for resultado in resultados:
            f.write(resultado + "\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados Salvos Em: {nome_arquivo}")

# Finalizar o programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== SCAN FINALIZADO. PRESSIONE ENTER PARA SAIR ==========\n\n")
