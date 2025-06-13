import hashlib
import os
import sys
import zlib  # Para CRC32
from colorama import init, Fore, Style
import time

# Inicializa o colorama
init(autoreset=True)

# Exibe a descrição do script e os tipos de hash suportados
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗  ██╗ █████╗ ███████╗██╗  ██╗     ██████╗██████╗  █████╗  ██████╗██╗  ██╗██╗███╗   ██╗ ██████╗ 
██║  ██║██╔══██╗██╔════╝██║  ██║    ██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║████╗  ██║██╔════╝ 
███████║███████║███████╗███████║    ██║     ██████╔╝███████║██║     █████╔╝ ██║██╔██╗ ██║██║  ███╗
██╔══██║██╔══██║╚════██║██╔══██║    ██║     ██╔══██╗██╔══██║██║     ██╔═██╗ ██║██║╚██╗██║██║   ██║
██║  ██║██║  ██║███████║██║  ██║    ╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
""")
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Script de Quebra de Hashes")
print(Fore.LIGHTGREEN_EX + "Este script tenta quebrar hashes comparando-os com uma wordlist")
print(Fore.LIGHTGREEN_EX + "Tipos de hash suportados")
print(Fore.LIGHTCYAN_EX + "- MD5 (32 caracteres, ex: 5f4dcc3b5aa765d61d8327deb882cf99)")
print(Fore.LIGHTCYAN_EX + "- SHA1 (40 caracteres)")
print(Fore.LIGHTCYAN_EX + "- SHA256 (64 caracteres)")
print(Fore.LIGHTCYAN_EX + "- SHA512 (128 caracteres)")
print(Fore.LIGHTCYAN_EX + "- CRC32 (8 caracteres)")
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nO script testará cada palavra da wordlist e variações comuns")
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "A saída detalhada está sempre ativada para mostrar cada tentativa\n")

# Função para listar arquivos .txt no diretório atual
def listar_arquivos_txt():
    diretorio_atual = os.getcwd()
    arquivos_txt = [f for f in os.listdir(diretorio_atual) if f.lower().endswith('.txt')]
    if not arquivos_txt:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .txt encontrado no diretório atual.")
        sys.exit(1)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nSelecione um arquivo de wordlist:\n")
    for idx, arquivo in enumerate(arquivos_txt, start=1):
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{idx} = {arquivo}")
    while True:
        try:
            escolha = int(input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o número do arquivo de wordlist: "))
            if 1 <= escolha <= len(arquivos_txt):
                return os.path.join(diretorio_atual, arquivos_txt[escolha - 1])
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "Opção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "Entrada inválida. Digite um número.")

# Função para carregar a wordlist
def carregar_wordlist(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            return [linha.strip() for linha in f if linha.strip()]
    except FileNotFoundError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: Arquivo '{caminho_arquivo}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao ler a wordlist: {e}")
        sys.exit(1)

# Função para calcular hash MD5 (fornecida anteriormente)
def calcular_md5(palavra):
    return hashlib.md5(palavra.encode('utf-8')).hexdigest()

# Função para calcular hashes para diferentes algoritmos
def calcular_hash(algoritmo, palavra):
    try:
        if algoritmo == 'MD5':
            return calcular_md5(palavra)  # Usa a função específica para MD5
        elif algoritmo == 'SHA1':
            return hashlib.sha1(palavra.encode('utf-8')).hexdigest()
        elif algoritmo == 'SHA256':
            return hashlib.sha256(palavra.encode('utf-8')).hexdigest()
        elif algoritmo == 'SHA512':
            return hashlib.sha512(palavra.encode('utf-8')).hexdigest()
        elif algoritmo == 'CRC32':
            return format(zlib.crc32(palavra.encode('utf-8')) & 0xFFFFFFFF, '08x')
        else:
            raise ValueError("\nAlgoritmo de hash inválido.")
    except UnicodeEncodeError:
        return None  # Pula palavras que não podem ser codificadas

# Função para validar hash MD5 (fornecida anteriormente)
def validar_md5(hash_entrada):
    hash_entrada = hash_entrada.strip().lower()
    if len(hash_entrada) == 32 and all(c in '0123456789abcdef' for c in hash_entrada):
        return True
    return False

# Função para identificar o tipo de hash com base no tamanho
def identificar_hash(hash_entrada):
    hash_entrada = hash_entrada.strip().lower()
    tamanho = len(hash_entrada)
    eh_hex = all(c in '0123456789abcdef' for c in hash_entrada)
    
    if tamanho == 32 and eh_hex:
        return 'MD5'
    elif tamanho == 40 and eh_hex:
        return 'SHA1'
    elif tamanho == 64 and eh_hex:
        return 'SHA256'
    elif tamanho == 128 and eh_hex:
        return 'SHA512'
    elif tamanho == 8 and eh_hex:
        return 'CRC32'
    else:
        raise ValueError(Fore.LIGHTRED_EX + Style.BRIGHT + "\nHash inválido. Deve ser um hash válido MD5 (32), SHA1 (40), SHA256 (64), SHA512 (128) ou CRC32 (8) em formato hexadecimal.")

# Função para gerar variações simples de senhas
def gerar_variacoes(palavra):
    variacoes = [
        palavra,                    # Original
        palavra.upper(),            # Maiúscula
        palavra.lower(),            # Minúscula
        palavra.capitalize(),       # Primeira letra maiúscula
        palavra + "123",            # Adiciona "123"
        palavra + "!",              # Adiciona "!"
        palavra + "2023",           # Adiciona "2023"
        palavra + "@",              # Adiciona "@"
        "123" + palavra,            # Adiciona "123" no início
    ]
    return variacoes

# Lógica principal
def main():
    # Seleciona e carrega a wordlist
    arquivo_wordlist = listar_arquivos_txt()
    wordlist = carregar_wordlist(arquivo_wordlist)
    total_palavras = len(wordlist)
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nWordlist carregada: {arquivo_wordlist} ({total_palavras} palavras)\n")

    # Obtém a entrada do hash
    hash_a_quebrar = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o hash: ").strip().lower()
    try:
        tipo_hash = identificar_hash(hash_a_quebrar)
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTipo de hash identificado: {tipo_hash}")
    except ValueError as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: {e}")
        sys.exit(1)

    # Modo verbose sempre ativado
    verbose = True

    # Quebra o hash
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nIniciando quebra do hash {tipo_hash} usando {arquivo_wordlist}\n")
    tempo_inicio = time.time()
    for idx, palavra in enumerate(wordlist, 1):
        # Tenta variações da palavra
        for variacao in gerar_variacoes(palavra):
            hash_calculado = calcular_hash(tipo_hash, variacao)
            if hash_calculado is None:
                continue  # Pula palavras com problemas de codificação
            if verbose:
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Verificando linha {idx}/{total_palavras}: " +
                      Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{variacao:<30} " +
                      Fore.LIGHTCYAN_EX + f"Hash: {hash_calculado}")
            
            if hash_calculado == hash_a_quebrar:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nSenha Encontrada na linha {idx}: " +
                      Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{variacao}")
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nTempo gasto: {time.time() - tempo_inicio:.2f} segundos")
                input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
                return
        
        # Exibe progresso a cada 1000 palavras
        if idx % 1000 == 0:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Progresso: {idx}/{total_palavras} palavras verificadas ({(idx/total_palavras)*100:.1f}%)")
    
    # Se não encontrar correspondência
    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nSenha não encontrada na wordlist ou suas variações para {tipo_hash}.")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Tempo gasto: {time.time() - tempo_inicio:.2f} segundos")
    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\nProcesso interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro inesperado: {e}")
        sys.exit(1)
