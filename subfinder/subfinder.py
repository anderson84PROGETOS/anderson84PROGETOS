import os
import requests
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗██╗   ██╗██████╗ ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██╔════╝██║   ██║██╔══██╗██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
███████╗██║   ██║██████╔╝█████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
╚════██║██║   ██║██╔══██╗██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
███████║╚██████╔╝██████╔╝██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
""")

# Configuração de headers para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para processar a wordlist
def process_wordlist(file_path):
    try:
        with open(file_path, "r") as file:
            linhas = file.readlines()
            subdominios = set(linha.strip() for linha in linhas if linha.strip())
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nTotal de subdomínios únicos na wordlist: {len(subdominios)}\n")
            return subdominios
    except FileNotFoundError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: Arquivo '{file_path}' não encontrado.\n")
        return None

# Função para verificar subdomínios
def verificar_subdominios(subdominios, dominio_base):
    ativos = set()
    count = 1
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nVerificando subdomínios...\n")

    for subdominio in subdominios:
        url_http = f"http://{subdominio}.{dominio_base}"
        url_https = f"https://{subdominio}.{dominio_base}"

        for url in [url_http, url_https]:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    if url not in ativos:
                        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{count} - Ativo: {url}")
                        ativos.add(url)
                        count += 1
                    break  # Para de tentar outras opções após sucesso
            except requests.exceptions.RequestException:
                continue  # Ignora erros e tenta a próxima opção

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTotal de subdomínios ativos encontrados: {len(ativos)}\n")
    return list(ativos)

# Função para procurar arquivos .txt
def procurar_arquivos_txt():
    current_directory = os.getcwd()
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nProcurando arquivos .txt no diretório: {current_directory}")
    
    arquivos_txt = [f for f in os.listdir(current_directory) if f.endswith('.txt')]
    
    if arquivos_txt:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nArquivos .txt encontrados:\n")
        for idx, arquivo in enumerate(arquivos_txt, 1):
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{idx}. {arquivo}")
        
        escolha = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nEscolha o número do arquivo da wordlist (ex: 1): "))
        
        if 1 <= escolha <= len(arquivos_txt):
            return os.path.abspath(arquivos_txt[escolha - 1])
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida!")
            return None
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .txt encontrado no diretório atual.")
        return None

# Função principal
def main():
    wordlist_path = procurar_arquivos_txt()
    
    if not wordlist_path:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro: Não foi possível localizar um arquivo de wordlist válido.")
        return
    
    dominio_base = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o domínio base (ex: exemplo.com): ").strip()
    
    subdominios = process_wordlist(wordlist_path)
    
    if subdominios:
        subdominios_ativos = verificar_subdominios(subdominios, dominio_base)
        
        if subdominios_ativos:            
            escolha = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar os subdomínios ativos? (s/n): ").lower()
            if escolha == 's':
                nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar: ").strip()
                with open(nome_arquivo, "w") as file:
                    for subdominio in subdominios_ativos:
                        file.write(f"{subdominio}\n")
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nSubdomínios ativos salvos em: {nome_arquivo}\n")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum subdomínio ativo encontrado.\n")    

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
