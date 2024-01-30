import socket

def enviar_solicitacao_http(ip, porta=80):
    # Cria um socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conecta ao servidor
        cliente_socket.connect((ip, porta))

        # Envia a solicitação HTTP HEAD
        cliente_socket.sendall(b"HEAD / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")

        # Recebe a resposta do servidor
        resposta = cliente_socket.recv(4096)
        
        print("Resposta do servidor:")
        print(resposta.decode())

    except Exception as e:
        print("Ocorreu um erro durante a solicitação:", e)

    finally:
        # Fecha o socket
        cliente_socket.close()

if __name__ == "__main__":
    print("""\n
            
        ████████╗███████╗ ██████╗██╗  ██╗███╗   ██╗ ██████╗ ██╗      ██████╗  ██████╗ ██╗███████╗███████╗
        ╚══██╔══╝██╔════╝██╔════╝██║  ██║████╗  ██║██╔═══██╗██║     ██╔═══██╗██╔════╝ ██║██╔════╝██╔════╝
           ██║   █████╗  ██║     ███████║██╔██╗ ██║██║   ██║██║     ██║   ██║██║  ███╗██║█████╗  ███████╗
           ██║   ██╔══╝  ██║     ██╔══██║██║╚██╗██║██║   ██║██║     ██║   ██║██║   ██║██║██╔══╝  ╚════██║
           ██║   ███████╗╚██████╗██║  ██║██║ ╚████║╚██████╔╝███████╗╚██████╔╝╚██████╔╝██║███████╗███████║
           ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚══════╝                                                                                           

    """)         

    host = input("\nDigite o Nome do WebSite: ")

    try:
        # Tenta obter o nome do site usando o endereço IP
        ip = socket.gethostbyname(host)
        hostname = socket.gethostbyaddr(ip)[0]  # Obtém o nome do host associado ao endereço IP
        print("\nNome do site:", hostname)
        print("\nEndereço IP:", ip)
    except socket.herror as e:
        print(f"\nErro ao obter o nome do host: {e}")
        print("\nEndereço IP do site:", host) 

    print("\n")
    enviar_solicitacao_http(ip)

input("\nFIM [ENTER SAIR]\n")
