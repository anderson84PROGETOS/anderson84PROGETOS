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

    finally:
        # Fecha o socket
        cliente_socket.close()

if __name__ == "__main__":
    ip = input("\nDigite o endereço IP do servidor ou nome do WebSite: ")
    print("\n")
    enviar_solicitacao_http(ip)

input("\nFIM ENTER SAIR\n")
