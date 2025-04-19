import hashlib
import os
import sys
import zlib  # Para CRC32
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"""

██╗  ██╗ █████╗ ███████╗██╗  ██╗     ██████╗██████╗  █████╗  ██████╗██╗  ██╗██╗███╗   ██╗ ██████╗ 
██║  ██║██╔══██╗██╔════╝██║  ██║    ██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║████╗  ██║██╔════╝ 
███████║███████║███████╗███████║    ██║     ██████╔╝███████║██║     █████╔╝ ██║██╔██╗ ██║██║  ███╗
██╔══██║██╔══██║╚════██║██╔══██║    ██║     ██╔══██╗██╔══██║██║     ██╔═██╗ ██║██║╚██╗██║██║   ██║
██║  ██║██║  ██║███████║██║  ██║    ╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                                                                                                          
""")

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

# Função para calcular o hash de diferentes tipos
def calcular_hash(algoritmo, palavra):
    if algoritmo == 'MD5':
        return hashlib.md5(palavra.encode()).hexdigest()
    elif algoritmo == 'SHA1':
        return hashlib.sha1(palavra.encode()).hexdigest()
    elif algoritmo == 'SHA256':
        return hashlib.sha256(palavra.encode()).hexdigest()
    elif algoritmo == 'SHA512':
        return hashlib.sha512(palavra.encode()).hexdigest()
    elif algoritmo == 'CRC32':
        return format(zlib.crc32(palavra.encode()) & 0xFFFFFFFF, '08x')
    else:
        raise ValueError("Algoritmo de hash inválido.")

# Função para identificar o tipo de hash com base no comprimento
def identificar_hash(hash_input):
    hash_input = hash_input.strip()
    length = len(hash_input)
    
    # Verifica se é um valor hexadecimal válido
    is_hex = all(c in '0123456789abcdefABCDEF' for c in hash_input)
    
    if length == 32 and is_hex:
        return 'MD5'
    elif length == 40 and is_hex:
        return 'SHA1'
    elif length == 64 and is_hex:
        return 'SHA256'
    elif length == 128 and is_hex:
        return 'SHA512'
    elif length == 8 and is_hex:
        return 'CRC32'
    else:
        raise ValueError(Fore.LIGHTRED_EX + Style.BRIGHT + "\nHash inválida. A entrada deve ser um hash válido (MD5, SHA1, SHA256, SHA512 ou CRC32).")

# Leitura do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()
wordlist = carregar_wordlist(wordlist_file)
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nConteúdo da wordlist Total de palavras: {len(wordlist)}\n")

# Leitura da hash a ser quebrada
hash_to_crack = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a Hash: ").strip()

# Identificação automática do tipo de hash
try:
    tipo_hash = identificar_hash(hash_to_crack)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTipo de hash identificado: {tipo_hash}")
except ValueError as e:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: {e}")
    sys.exit()

try:
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nIniciando a busca pela senha no arquivo {wordlist_file}\n")
    for line_number, word in enumerate(wordlist, 1):
        hashed = calcular_hash(tipo_hash, word)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nVerificando a senha na linha {line_number}: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f" {word:<25} " + Fore.LIGHTCYAN_EX + f"Hash: {hashed}")  # Mostra o hash calculado
        
        # Comparação insensível a maiúsculas/minúsculas para todos os hashes
        if hashed == hash_to_crack.lower():
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nSenha Encontrada na linha: {line_number:<3}  " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f" Senha: {word}")
            break
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nSenha não encontrada na wordlist.")
except FileNotFoundError:
    print(f"O arquivo {wordlist_file} não foi encontrado. Verifique o caminho do arquivo.")
except ValueError as e:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: {e}")
    sys.exit()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
