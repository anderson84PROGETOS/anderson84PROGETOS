import os
import requests
from urllib.parse import urljoin
from tqdm import tqdm
from colorama import init, Fore, Style

# Inicializa o colorama para cores no terminal
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

███████╗██╗   ██╗███████╗███████╗██╗███╗   ██╗ ██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██║   ██║╚══███╔╝╚══███╔╝██║████╗  ██║██╔════╝     ██╔════╝██╔════╝██╔══██╗████╗  ██║
█████╗  ██║   ██║  ███╔╝   ███╔╝ ██║██╔██╗ ██║██║  ███╗    ███████╗██║     ███████║██╔██╗ ██║
██╔══╝  ██║   ██║ ███╔╝   ███╔╝  ██║██║╚██╗██║██║   ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
██║     ╚██████╔╝███████╗███████╗██║██║ ╚████║╚██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝                                                                                          
""")

def procurar_arquivos_txt():
    """Procura arquivos .txt na pasta onde o script está localizado."""
    arquivos_txt = [f for f in os.listdir() if f.endswith(".txt")]
    if not arquivos_txt:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Nenhum arquivo .txt encontrado na pasta do script.\n")
        return None

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Arquivos .txt Encontrados\n")
    for i, arquivo in enumerate(arquivos_txt, 1):
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{i}. {arquivo}")

    escolha = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha um arquivo (digite o número): ").strip()
    if escolha.isdigit():
        escolha = int(escolha)
        if 1 <= escolha <= len(arquivos_txt):
            return arquivos_txt[escolha - 1]

    print("\nEscolha inválida. Saindo...\n")
    return None

def load_wordlist(filename):
    """Carrega a wordlist e retorna uma lista de palavras-chave."""
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"\nArquivo {filename} não encontrado!\n")
        return []

def escolher_codigos_status():
    """Permite ao usuário escolher os códigos de status a serem filtrados."""
    opcoes_validas = {"200", "301", "403"}
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha os códigos de status desejados (separados por vírgula)\n")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "Opções: 200,301,403")
    escolha = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite os códigos: ").strip()
    print("")
    codigos_escolhidos = {int(c) for c in escolha.split(",") if c.strip().isdigit() and c.strip() in opcoes_validas}
    
    if not codigos_escolhidos:
        print("\nNenhum código válido escolhido. Usando padrão: 200\n")
        return {200}
    return codigos_escolhidos

def find_pages(base_url, wordlist, codigos_status):
    """Busca por páginas dentro da wordlist no domínio informado."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    found_urls = []
    print("")
    #with tqdm(total=len(wordlist), desc="Progresso", unit="URL", ncols=90, leave=True) as pbar:
    with tqdm(total=len(wordlist), desc=Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Progresso", unit="URL", ncols=90, leave=True) as pbar:            
        
        for word in wordlist:
            test_url = urljoin(base_url, word)
            try:
                response = requests.get(test_url, headers=headers, timeout=5, allow_redirects=False)
                if response.status_code in codigos_status:
                    if response.status_code == 200:
                        cor = Fore.LIGHTGREEN_EX + Style.BRIGHT
                    elif response.status_code == 301:
                        cor = Fore.LIGHTYELLOW_EX + Style.BRIGHT
                    elif response.status_code == 403:
                        cor = Fore.LIGHTRED_EX + Style.BRIGHT
                    else:
                        cor = Fore.WHITE  # Caso de erro inesperado

                    msg = f"({response.status_code}) {test_url}\n"
                    found_urls.append(msg)
                    tqdm.write(cor + msg)  # Exibe colorido abaixo da barra de progresso
            except requests.RequestException:
                pass  # Ignora erros de conexão
            pbar.update(1)
    
    return found_urls

if __name__ == "__main__":
    arquivo_wordlist = procurar_arquivos_txt()
    if arquivo_wordlist:
        wordlist = load_wordlist(arquivo_wordlist)
        if wordlist:
            site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do site (com http/https): ").strip()
            codigos_status = escolher_codigos_status()
            urls_encontradas = find_pages(site, wordlist, codigos_status)            

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
