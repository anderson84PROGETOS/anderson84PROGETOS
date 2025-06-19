import os
import sys
from colorama import init, Fore, Style
from pypdf import PdfReader
import pyzipper
import rarfile
import py7zr

# Inicializa colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗  ██╗███████╗██╗   ██╗    ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
██║ ██╔╝██╔════╝╚██╗ ██╔╝    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
█████╔╝ █████╗   ╚████╔╝     ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
██╔═██╗ ██╔══╝    ╚██╔╝      ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
██║  ██╗███████╗   ██║       ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
╚═╝  ╚═╝╚══════╝   ╚═╝       ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
""")

# Pergunta o nome do arquivo ao usuário
file_path = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do arquivo protegido (ex: arquivo.pdf, .zip, .rar, .7z): ").strip()

# Verifica se o arquivo existe
if not os.path.isfile(file_path):
    print(Fore.RED + f"Arquivo '{file_path}' não encontrado. Saindo.")
    sys.exit()

# Lista arquivos de wordlist (.txt)
def listar_wordlists():
    arquivos = [f for f in os.listdir() if f.endswith(".txt")]
    if not arquivos:
        print(Fore.RED + "Nenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTYELLOW_EX + "\nEscolha uma wordlist:")
    for i, arquivo in enumerate(arquivos, 1):
        print(Fore.LIGHTMAGENTA_EX + f"{i} - {arquivo}")

    while True:
        try:
            escolha = int(input(Fore.CYAN + "\nDigite o número da wordlist: "))
            if 1 <= escolha <= len(arquivos):
                return arquivos[escolha - 1]
        except:
            pass
        print("Entrada inválida. Tente novamente.")

# Função principal que tenta desbloquear
def tentar_senhas(caminho, senhas):
    ext = os.path.splitext(caminho)[1].lower()
    total = len(senhas)

    for i, senha in enumerate(senhas, 1):
        print(Fore.LIGHTGREEN_EX + f"🔐 Testando senha {i}/{total}: {senha}")
        try:
            if ext == '.pdf':
                reader = PdfReader(caminho)
                if reader.is_encrypted:
                    if reader.decrypt(senha):
                        _ = reader.pages[0]
                        return senha
            elif ext == '.zip':
                with pyzipper.AESZipFile(caminho) as zf:
                    zf.pwd = senha.encode('utf-8')
                    zf.extractall()
                    return senha
            elif ext == '.rar':
                with rarfile.RarFile(caminho) as rf:
                    rf.extractall(pwd=senha)
                    return senha
            elif ext == '.7z':
                with py7zr.SevenZipFile(caminho, mode='r', password=senha) as archive:
                    archive.extractall()
                    return senha
        except Exception:
            continue
    return None

# Seleciona a wordlist
wordlist = listar_wordlists()

# Lê senhas
with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
    senhas = f.read().splitlines()

print(Fore.CYAN + "\nIniciando tentativa de senhas...\n")

# Tenta desbloquear
senha_correta = tentar_senhas(file_path, senhas)

if senha_correta:
    print(Fore.LIGHTYELLOW_EX + f"\n✅ Senha correta encontrada: {Fore.LIGHTGREEN_EX + senha_correta}\n")
else:
    print(Fore.LIGHTRED_EX + "\n❌ Nenhuma senha funcionou.\n")

input(Fore.LIGHTRED_EX + "\n========== PRESSIONE ENTER PARA SAIR ==========\n")
