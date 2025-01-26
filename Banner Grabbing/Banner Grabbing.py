import socket
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗  █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗      ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ 
██████╔╝███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ██║  ███╗██████╔╝███████║██████╔╝██████╔╝██║██╔██╗ ██║██║  ███╗
██╔══██╗██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██║██║╚██╗██║██║   ██║
██████╔╝██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝██║██║ ╚████║╚██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                                                     
""")

def banner_grabbing(host):
    try:
        # Configurando a conexão com o servidor (porta 80)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, 80))  # Conecta na porta 80
            # Enviando uma requisição HTTP HEAD
            http_request = f"HEAD / HTTP/1.0\r\nHost: {host}\r\n\r\n"
            s.sendall(http_request.encode())  # Envia o pedido HTTP HEAD

            # Recebendo a resposta do servidor
            response = s.recv(4096).decode()  # Recebe até 4096 bytes

            if response:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nBanner Grabbing\n")
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + response)  # Exibe a resposta (os cabeçalhos)
            else:
                print("\nNenhuma resposta recebida.")
    except Exception as e:
        print(f"\nErro ao executar o comando: {e}")

# Entrada de dados do usuário (apenas o host)
host = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website (ex: example.com): ")  # Entrada para o host

# Chamada da função com o host fornecido pelo usuário
banner_grabbing(host)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
