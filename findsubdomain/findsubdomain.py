import os
import sys
import requests
import concurrent.futures
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗██╗███╗   ██╗██████╗ ███████╗██╗   ██╗██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗
██╔════╝██║████╗  ██║██╔══██╗██╔════╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║
█████╗  ██║██╔██╗ ██║██║  ██║███████╗██║   ██║██████╔╝██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║
██╔══╝  ██║██║╚██╗██║██║  ██║╚════██║██║   ██║██╔══██╗██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║
██║     ██║██║ ╚████║██████╔╝███████║╚██████╔╝██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝                                                                                                      
""")

def listar_txt_na_pasta():
    """Lista os arquivos .txt na pasta atual e permite ao usuário escolher um para usar como wordlist."""
    pasta_atual = os.getcwd()  
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Escolha um arquivo de wordlist disponível\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{idx} - {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número do arquivo da wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print("\nOpção inválida. Tente novamente.")
        except ValueError:
            print("\nPor favor, insira um número válido.")

def carregar_wordlist(arquivo):
    """Lê a wordlist do arquivo e retorna uma lista de subdomínios sem duplicatas e sem pontos extras."""
    with open(arquivo, 'r', encoding='utf-8') as f:
        palavras = [linha.strip().lstrip('.') for linha in f if linha.strip()]
    return palavras  # Mantendo a lista com todas as palavras

def check_subdomain(domain, subdomain):
    """Verifica se um subdomínio existe."""
    url = f"http://{subdomain}.{domain}"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code < 400:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"SUBDOMÍNIO ENCONTRADO: {url}")
            return url
    except requests.RequestException:
        pass
    return None

def find_subdomains(domain, wordlist):
    """Executa a busca por subdomínios em paralelo usando a wordlist escolhida."""
    found_subdomains = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_subdomain, domain, sub): sub for sub in wordlist}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                found_subdomains.add(result)

    return found_subdomains

if __name__ == "__main__":
    wordlist_file = listar_txt_na_pasta()
    wordlist = carregar_wordlist(wordlist_file)

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Wordlist Escolhida: {os.path.basename(wordlist_file)}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] Palavras na wordlist: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + str(len(wordlist)) + "\n")
    
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website (exemplo.com): ").strip()

    if site:
        print(f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}\n[+] Buscando subdomínios para: {Fore.LIGHTGREEN_EX}{Style.BRIGHT}{site}\n")
        subdomains = find_subdomains(site, wordlist)

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n\n[+] Subdomínios Encontrados: {len(subdomains)}")  # Exibe a contagem final

        if subdomains:
            salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
            if salvar == "s":
                nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (ex: subdomains.txt): ").strip()
                with open(nome_arquivo, "w") as f:
                    for sub in subdomains:
                        f.write(sub + "\n")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] Resultados salvos em: {nome_arquivo}")
            else:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[-] Resultados não foram salvos.")
        else:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[-] Nenhum subdomínio encontrado.")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
