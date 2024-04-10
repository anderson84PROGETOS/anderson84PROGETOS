import socket
import re
import requests
from bs4 import BeautifulSoup

print("""

██████╗  ██████╗ ███╗   ███╗██╗███╗   ██╗██╗ ██████╗     ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗
██╔══██╗██╔═══██╗████╗ ████║██║████╗  ██║██║██╔═══██╗    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝
██║  ██║██║   ██║██╔████╔██║██║██╔██╗ ██║██║██║   ██║    ██║ █╗ ██║███████║██║   ██║██║███████╗
██║  ██║██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║██║   ██║    ██║███╗██║██╔══██║██║   ██║██║╚════██║
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╔╝    ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝      ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝                                                                                              
                                                         
""")

def obter_informacoes_whois_br(endereco):
    # Define o servidor WHOIS para domínios .br
    servidor_whois = 'whois.registro.br'
    
    # Define a porta WHOIS padrão
    porta = 43

    # Abre uma conexão de socket com o servidor WHOIS
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((servidor_whois, porta))

    # Envia a consulta WHOIS para o domínio especificado
    sock.sendall((endereco + "\r\n").encode())

    # Inicializa uma variável para armazenar a resposta WHOIS
    resposta_whois = b''

    # Recebe a resposta WHOIS em blocos e a concatena
    while True:
        dados = sock.recv(1024)
        if not dados:
            break
        resposta_whois += dados

    # Fecha a conexão de socket
    sock.close()

    # Tentativa de decodificação usando diferentes codecs
    codecs = ['utf-8', 'iso-8859-1', 'latin-1']
    for codec in codecs:
        try:
            decoded_response = resposta_whois.decode(codec)
            break
        except UnicodeDecodeError:
            pass
    else:
        print("Não foi possível decodificar a resposta WHOIS.")
        return

    # Imprime a resposta WHOIS
    print(decoded_response)

def obter_informacoes_whois_com(endereco):
    url = f"https://www.whois.com/whois/{endereco}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        whois_section = soup.find("pre", class_="df-raw")
        
        if whois_section:
            print("\nWHOIS para {}\n".format(endereco))
            print(whois_section.get_text())
        else:
            print("Não foi possível encontrar informações WHOIS para este domínio.")
    else:
        print("Erro ao obter informações WHOIS.")

# Main menu
print("\nSelecione uma opção\n")
print("\n1. Obter informações WHOIS para um website .BR")
print("\n2. Obter informações WHOIS para um website .COM")
opcao = input("\nOpção: ")
print("\n")

if opcao == "1":
    endereco = input("Digite o nome do website (.BR): ")
    obter_informacoes_whois_br(endereco)
elif opcao == "2":
    endereco = input("Digite o nome do website (.COM): ")
    obter_informacoes_whois_com(endereco)
else:
    print("Opção inválida.")

input("\n\n🎯 Pressione Enter para sair 🎯\n")
