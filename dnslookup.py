import socket
import requests
import threading
import itertools
import time
import sys

print("""

██████╗ ███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
██║  ██║██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
██║  ██║██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝ 
██████╔╝██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║     
╚═════╝ ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                                            
""")

def obter_wordlist_da_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP não 200
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"[ERRO] - Obtendo a wordlist da URL: {e}")
        return None

def nslookup(dominio, wordlist_url):
    wordlist = obter_wordlist_da_url(wordlist_url)
    
    if wordlist is None:
        return None

    for linha in wordlist:
        subdominio = linha.strip() + dominio
        try:
            host = socket.gethostbyname(subdominio)
            # Exibe o resultado à medida que é encontrado
            sys.stdout.write(f"\rHOST ENCONTRADO: {subdominio:<40} ====> IP: {host}\n")
            sys.stdout.flush()
        except socket.gaierror:
            continue

def animacao_carregamento():
    # Posição inicial da animação
    sys.stdout.write('\rEscaneando Aguarde.... ')
    sys.stdout.flush()
    while varredura_em_andamento:
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if not varredura_em_andamento:
                break
            sys.stdout.write(f'\rEscaneando Aguarde.... {c}')
            sys.stdout.flush()
            time.sleep(0.1)
    # Limpa a linha da animação após a conclusão
    sys.stdout.write('\r' + ' ' * 40 + '\r')
    sys.stdout.write('\n\nEscaneamento Concluído!\n')   

if __name__ == "__main__":
    dominio = input("\nDigite o nome do website: ")
    print("\n")
    wordlist_url = "https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/wordlist.txt"  # URL padrão

    varredura_em_andamento = True
    t = threading.Thread(target=animacao_carregamento)
    t.start()

    # Realiza a busca e exibe os resultados em tempo real
    nslookup(dominio, wordlist_url)
    varredura_em_andamento = False
    t.join()    
    
    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
