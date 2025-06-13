import hashlib
import os
import sys
from colorama import init, Fore, Style
import zlib  # Para CRC32

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗  ██╗ █████╗ ███████╗██╗  ██╗    ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
██║  ██║██╔══██╗██╔════╝██║  ██║    ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
███████║███████║███████╗███████║    ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
██╔══██║██╔══██║╚════██║██╔══██║    ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
██║  ██║██║  ██║███████║██║  ██║    ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝ 

""")

def simple_hash(input_string):
    """Gera um hash simples personalizado (não criptográfico)."""
    hash_value = 0
    for char in input_string:
        hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFF  # Limita a 32 bits
    return hex(hash_value)[2:].zfill(8)  # Formato hexadecimal de 8 dígitos

def generate_hash(input_string, hash_type):
    """Gera diferentes tipos de hash a partir de uma string."""
    input_bytes = input_string.encode('utf-8')
    
    if hash_type == 'simple':
        return simple_hash(input_string)
    elif hash_type == 'crc32':
        return hex(zlib.crc32(input_bytes) & 0xFFFFFFFF)[2:].zfill(8)
    elif hash_type == 'md5':
        return hashlib.md5(input_bytes).hexdigest()
    elif hash_type == 'sha1':
        return hashlib.sha1(input_bytes).hexdigest()
    elif hash_type == 'sha256':
        return hashlib.sha256(input_bytes).hexdigest()
    elif hash_type == 'sha512':
        return hashlib.sha512(input_bytes).hexdigest()
    else:
        return None

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
    with open(arquivo, 'r', encoding='latin1') as f:
        palavras = [linha.strip() for linha in f if linha.strip()]
    return palavras

# Menu interativo para o usuário
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha uma opção\n")
print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "1 - Gerar hash")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "2 - Descriptografar hash usando uma wordlist")

opcao = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número da opção: ")

if opcao == '1':
    input_string = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite um Nome para gerar o hash: ")
    
    # Lista de tipos de hash disponíveis
    hash_types = ['simple', 'crc32', 'md5', 'sha1', 'sha256', 'sha512']
    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha o tipo de hash")
    for idx, h_type in enumerate(hash_types, start=1):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{idx} - {h_type.upper()}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número do tipo de hash: "))
            if 1 <= choice <= len(hash_types):
                hash_type = hash_types[choice - 1]
                break
            else:
                print(Fore.LIGHTRED_EX + "\nOpção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + "\nPor favor, insira um número válido.")

    hash_result = generate_hash(input_string, hash_type)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nO hash {hash_type.upper()} de: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + input_string)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nA hash {hash_type.upper()} é: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + hash_result)
    
    # Solicitar nome do arquivo e salvar o hash no formato "TIPO: hash"
    nome_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar o hash (sem extensão): ")
    nome_arquivo = nome_arquivo + ".txt" if not nome_arquivo.endswith('.txt') else nome_arquivo
    formatted_hash = f"{hash_type.upper()}: {hash_result}"
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
            arquivo.write(formatted_hash)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nHash salvo com sucesso em: {nome_arquivo} " + Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "    foi salvo dentro do arquivo.txt como: " + Fore.CYAN + Style.BRIGHT + f"{formatted_hash}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"\nErro ao salvar o arquivo: {e}")

elif opcao == '2':
    wordlist_arquivo = listar_txt_na_pasta()
    wordlist = carregar_wordlist(wordlist_arquivo)
    print(Fore.LIGHTCYAN_EX + f"\nWordlist carregada com: {len(wordlist)} palavras")

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o hash para tentar descobrir a palavra original: ", end="")
    hash_to_crack = input(Fore.LIGHTGREEN_EX + Style.BRIGHT).strip().lower()

    # Lista de tipos de hash a serem testados automaticamente
    hash_types = ['simple', 'crc32', 'md5', 'sha1', 'sha256', 'sha512']
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT +  "\nTentando descriptografar o hash com todos os tipos Disponíveis...")

    found = False
    for hash_type in hash_types:
        print(Fore.LIGHTCYAN_EX + f"\nTestando tipo: {hash_type.upper()}")
        for word in wordlist:
            hashed_word = generate_hash(word, hash_type)
            if hashed_word == hash_to_crack:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[✅] Hash correspondente Encontrado!\n\nPalavra original: ", end="")
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + word)
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTipo de hash: {hash_type.upper()}")
                found = True
                break
        if found:
            break

    if not found:
        print(Fore.LIGHTRED_EX + "\n[❌] Nenhuma correspondência encontrada na wordlist para nenhum tipo de hash.")

else:
    print(Fore.LIGHTRED_EX + "\nOpção inválida. Saindo...")

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
