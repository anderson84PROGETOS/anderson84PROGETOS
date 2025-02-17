import hashlib
import os
import sys
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

███████╗██╗  ██╗ █████╗       ██████╗ ███████╗ ██████╗ 
██╔════╝██║  ██║██╔══██╗      ╚════██╗██╔════╝██╔════╝ 
███████╗███████║███████║█████╗ █████╔╝███████╗███████╗ 
╚════██║██╔══██║██╔══██║╚════╝██╔═══╝ ╚════██║██╔═══██╗
███████║██║  ██║██║  ██║      ███████╗███████║╚██████╔╝
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝      ╚══════╝╚══════╝ ╚═════╝ 
                                                                                                                                             
""")

def generate_hash(input_string):
    """Gera o hash SHA-256 de uma string."""
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()
    return sha256_hash

def listar_txt_na_pasta():
    """Lista os arquivos .txt na pasta atual e permite ao usuário escolher um para usar como wordlist."""
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print(Fore.LIGHTRED_EX + "\nNenhum arquivo .txt encontrado na pasta")
        sys.exit()

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha um arquivo de wordlist disponível\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{idx} - {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número do arquivo da wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print(Fore.LIGHTRED_EX + "\nOpção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + "\nPor favor, insira um número válido.")

def carregar_wordlist(arquivo):
    """Lê a wordlist do arquivo e retorna uma lista de palavras únicas sem espaços extras."""
    with open(arquivo, 'r', encoding='latin1') as f:  # Alterado para 'latin1'
        palavras = [linha.strip() for linha in f if linha.strip()]
    return palavras


# Menu interativo para o usuário
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha uma opção\n")
print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "1 - Gerar hash SHA-256")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "2 - Descriptografar hash SHA-256 usando uma wordlist")

opcao = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número da opção: ")

if opcao == '1':
    input_string = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite a string para gerar o hash: ")
    hash_result = generate_hash(input_string)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nO hash SHA-256 de: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + input_string)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nA hash SHA-256 é: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + hash_result)

elif opcao == '2':
    wordlist_arquivo = listar_txt_na_pasta()
    wordlist = carregar_wordlist(wordlist_arquivo)
    print(Fore.LIGHTCYAN_EX + f"\nWordlist carregada com: {len(wordlist)} palavras")

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o hash SHA-256 para tentar descobrir a palavra original: ", end="")
    hash_to_crack = input(Fore.LIGHTGREEN_EX + Style.BRIGHT).strip().lower()

    found = False
    for word in wordlist:
        hashed_word = hashlib.sha256(word.encode()).hexdigest()
        if hashed_word == hash_to_crack:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[✅] Hash correspondente Encontrado!\n\nPalavra original: ", end="")
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + word)
            found = True
            break

    if not found:
        print(Fore.LIGHTRED_EX + "\n[❌] Nenhuma correspondência encontrada na wordlist.")

else:
    print(Fore.LIGHTRED_EX + "\nOpção inválida. Saindo...")

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")    
