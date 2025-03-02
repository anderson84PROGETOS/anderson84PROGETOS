import os
import sys
import requests
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗   ██╗██████╗ ██╗          ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
██║   ██║██╔══██╗██║         ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
██║   ██║██████╔╝██║         ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║   
██║   ██║██╔══██╗██║         ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║   
╚██████╔╝██║  ██║███████╗    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║   
 ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝   
                                                                                                                                                                                                                                                         
""")

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("\nPor favor, insira um número válido.")

# Função para carregar e exibir a wordlist
def carregar_e_exibir_wordlist():
    wordlist_file = listar_txt_na_pasta()
    with open(wordlist_file, 'r', encoding='utf-8') as f:
        subdominios = f.read().splitlines()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Wordlist carregada: {os.path.basename(wordlist_file)}")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Contém {len(subdominios)} palavras\n")   
    return subdominios

# Função para escolher os códigos de status
def escolher_codigos_status():
    codigos_disponiveis = {
        200: "Caminho encontrado",
        301: "Redirecionamento permanente",
        302: "Redirecionamento temporário",
        403: "Acesso negado",
        404: "Não encontrado"
    }
    codigos_escolhidos = []

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha os códigos de status que deseja verificar (digite os números separados por espaço)")
    for codigo, descricao in codigos_disponiveis.items():
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{codigo} - {descricao}")

    while True:
        try:
            escolhas = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite os códigos (ex.: 200 301 302 403 404): ").strip().split()
            for escolha in escolhas:
                codigo = int(escolha)
                if codigo in codigos_disponiveis:
                    codigos_escolhidos.append(codigo)
                else:
                    print(Fore.RED + f"Código {codigo} inválido. Tente novamente.")
                    codigos_escolhidos = []
                    break
            if codigos_escolhidos:
                break
            else:
                print(Fore.RED + "Nenhum código válido selecionado. Tente novamente.")
        except ValueError:
            print(Fore.RED + "Entrada inválida. Digite apenas números separados por espaço.")

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nCódigos selecionados:", ", ".join(map(str, codigos_escolhidos)))
    return codigos_escolhidos

# Função para verificar caminhos em uma URL
def verificar_caminho(url_base, wordlist, codigos_escolhidos):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Verificando caminhos na URL: {url_base}")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] Usando wordlist com {len(wordlist)} palavras\n")

    found_paths = []
    redirects_301 = []
    redirects_302 = []

    for caminho in wordlist:
        caminho = caminho.strip()
        if not caminho.startswith('/'):
            caminho = '/' + caminho
        
        url_completa = url_base + caminho
        
        try:
            response = requests.get(url_completa, headers=headers, timeout=5, allow_redirects=False)
            status_code = response.status_code

            if status_code in codigos_escolhidos:
                if status_code == 200:
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[+] Caminho Encontrado: {url_completa}")
                    found_paths.append(url_completa)
                elif status_code == 301:
                    redirect_url = response.headers.get('Location', 'Desconhecido')
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"[>] Redirecionamento (301) Encontrado: {url_completa}")
                    redirects_301.append((url_completa, redirect_url))
                elif status_code == 302:
                    redirect_url = response.headers.get('Location', 'Desconhecido')
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"[>] Redirecionamento (302) Encontrado: {url_completa}")
                    redirects_302.append((url_completa, redirect_url))
                elif status_code == 403:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[-] Acesso negado (403): {url_completa}")
                elif status_code == 404:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[x] Não encontrado (404): {url_completa}")
        except requests.RequestException as e:
            pass

    # Exibe caminhos encontrados (200)
    if 200 in codigos_escolhidos and found_paths:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\nCaminhos Encontrados (Code: 200)\n")
        for path in found_paths:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f" - {path}")
    elif 200 in codigos_escolhidos:
        print(Fore.RED + "\nNenhum caminho válido encontrado (Code: 200).")

    # Exibe redirecionamentos 301
    if 301 in codigos_escolhidos and redirects_301:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nRedirecionamentos Encontrados (Code: 301)\n")
        for original, destino in redirects_301:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f" - {original}")
    elif 301 in codigos_escolhidos:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nNenhum redirecionamento 301 encontrado.")

    # Exibe redirecionamentos 302
    if 302 in codigos_escolhidos and redirects_302:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nRedirecionamentos Encontrados (Code: 302)\n")
        for original, destino in redirects_302:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f" - {original}")
    elif 302 in codigos_escolhidos:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nNenhum redirecionamento 302 encontrado.")

# Primeiro carrega e exibe a wordlist
subdominios = carregar_e_exibir_wordlist()

# Solicita os códigos de status a verificar
codigos_escolhidos = escolher_codigos_status()

# Solicita a URL base do usuário
url_base = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL base (ex.: https://www.exemplo.com): ").strip()
if not url_base.startswith("http://") and not url_base.startswith("https://"):
    url_base = "http://" + url_base  # Adiciona protocolo padrão se não fornecido
if url_base.endswith('/'):
    url_base = url_base[:-1]

# Executa a verificação com a URL fornecida
verificar_caminho(url_base, subdominios, codigos_escolhidos)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
