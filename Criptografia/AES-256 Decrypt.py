from Crypto.Cipher import AES
import base64
import re
import string
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 █████╗ ███████╗███████╗    ██████╗ ███████╗ ██████╗     ██████╗ ███████╗ ██████╗██████╗ ██╗   ██╗██████╗ ████████╗
██╔══██╗██╔════╝██╔════╝    ╚════██╗██╔════╝██╔════╝     ██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝
███████║█████╗  ███████╗     █████╔╝███████╗███████╗     ██║  ██║█████╗  ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   
██╔══██║██╔══╝  ╚════██║    ██╔═══╝ ╚════██║██╔═══██╗    ██║  ██║██╔══╝  ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   
██║  ██║███████╗███████║    ███████╗███████║╚██████╔╝    ██████╔╝███████╗╚██████╗██║  ██║   ██║   ██║        ██║   
╚═╝  ╚═╝╚══════╝╚══════╝    ╚══════╝╚══════╝ ╚═════╝     ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   

""")

# Entradas
mensagem_base64 = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a mensagem_base64: ")
chave_base64 = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite a Chave AES-256 Base64: ")
iv = b'vetor_init_16byt'  # Deve ser o mesmo IV usado na criptografia

try:
    mensagem_criptografada = base64.b64decode(mensagem_base64)
    chave = base64.b64decode(chave_base64)
except Exception as e:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro ao decodificar Base64:", e)
    exit(1)

# Cria cifra e descriptografa
try:
    cipher = AES.new(chave, AES.MODE_CBC, iv)
    dados_decifrados = cipher.decrypt(mensagem_criptografada)
except Exception as e:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro ao descriptografar:", e)
    exit(1)

# Verifica se há dados
if not dados_decifrados:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: dados descriptografados vazios. Verifique a chave ou IV.")
    exit(1)

# Remove padding PKCS7 se existir
pad_len = dados_decifrados[-1]
if 1 <= pad_len <= 16:
    dados_decifrados = dados_decifrados[:-pad_len]

# Decodifica os bytes para string
mensagem_original = dados_decifrados.decode('utf-8', errors='ignore')

# Filtra caracteres imprimíveis (letras, números, símbolos, etc)
mensagem_limpa = ''.join(c for c in mensagem_original if c in string.printable)

# Remove prefixos estranhos antes de nomes reais
match = re.search(r'[a-zA-Z]{3,}.*', mensagem_limpa)
mensagem_limpa = match.group().strip() if match else mensagem_limpa.strip()

# Exibe o resultado final
print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nMensagem Descriptografada: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{mensagem_limpa}")

# Pausa para o usuário ver
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
