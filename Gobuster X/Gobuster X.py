import os
import sys
import requests  # Para fazer requisições HTTP
from colorama import Fore, Style, init  # Para cores no terminal

# Inicializando o colorama e exibindo o banner
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗  ██████╗ ██████╗ ██╗   ██╗███████╗████████╗███████╗██████╗     ██╗  ██╗
██╔════╝ ██╔═══██╗██╔══██╗██║   ██║██╔════╝╚══██╔══╝██╔════╝██╔══██╗    ╚██╗██╔╝
██║  ███╗██║   ██║██████╔╝██║   ██║███████╗   ██║   █████╗  ██████╔╝     ╚███╔╝ 
██║   ██║██║   ██║██╔══██╗██║   ██║╚════██║   ██║   ██╔══╝  ██╔══██╗     ██╔██╗ 
╚██████╔╝╚██████╔╝██████╔╝╚██████╔╝███████║   ██║   ███████╗██║  ██║    ██╔╝ ██╗
 ╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝

""")  # Removido espaço extra após o banner

# Função para listar arquivos .txt na pasta atual
def listar_txt_na_pasta():
    """Lista os arquivos .txt na pasta atual e permite ao usuário escolher um para usar como wordlist."""
    pasta_atual = os.getcwd()  
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .txt encontrado na pasta.")
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
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nPor favor, insira um número válido.")

# Função para carregar a wordlist
def carregar_wordlist(arquivo):
    """Lê a wordlist do arquivo e retorna uma lista de subdomínios sem duplicatas e sem pontos extras."""
    with open(arquivo, 'r', encoding='utf-8') as f:
        palavras = [linha.strip().lstrip('.') for linha in f if linha.strip()]
    return palavras  # Mantendo a lista com todas as palavras

# Função para testar URLs com cabeçalhos personalizados
def testar_url(base_url, palavra, resultados):
    """Testa uma URL com a palavra da wordlist e armazena resultados válidos."""
    url = f"{base_url}/{palavra}"
    # Definir cabeçalhos para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        resposta = requests.get(url, headers=headers, timeout=5)
        if resposta.status_code == 200:  # Sucesso
            print(Fore.GREEN + f"(Status: {resposta.status_code})  [+] Encontrado: {url}")
            resultados.append(url)
        elif resposta.status_code != 404:  # Outros códigos além de 404
            pass
    except requests.RequestException:
        pass

# Função principal
def main():        
    # Selecionar e carregar a wordlist primeiro
    arquivo_wordlist = listar_txt_na_pasta()
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nCarregando wordlist: {arquivo_wordlist}")
    wordlist = carregar_wordlist(arquivo_wordlist)
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nConteúdo da wordlist Total de palavras: {len(wordlist)}")
    
    # Solicitar a URL base depois de mostrar a wordlist
    base_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website (ex: http://exemplo.com): ").rstrip('/')
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url

    # Lista de resultados
    resultados = []

    # Testar URLs sequencialmente
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nIniciando Enumeração\n")
    for palavra in wordlist:
        testar_url(base_url, palavra, resultados)

    # Resumo dos resultados    
    if resultados:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nDiretórios Encontradas: {len(resultados)}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\nNenhum diretório Encontrado.")

if __name__ == "__main__":
    main()
    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
