import socket

print("""

██╗    ██╗███████╗██████╗     ██╗  ██╗███████╗ █████╗ ██████╗ ███████╗██████╗ 
██║    ██║██╔════╝██╔══██╗    ██║  ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝    ███████║█████╗  ███████║██║  ██║█████╗  ██████╔╝
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██║██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔══██╗
╚███╔███╔╝███████╗██████╔╝    ██║  ██║███████╗██║  ██║██████╔╝███████╗██║  ██║
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                              
""")

def send_http_request(host, port):
    # Cria um socket TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Conecta ao servidor web
    s.connect((host, port))

    # Envio de solicitação HTTP básica com User-Agent personalizado
    request = "GET / HTTP/1.1\r\nHost: {}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0\r\n\r\n".format(host)
    s.send(request.encode())

    # Recebe a resposta do servidor
    response = s.recv(4096)
    
    # Fecha a conexão
    s.close()

    return response.decode()

def main():
    host = input("\nDigite o nome do website: ")
    port = 80
    
    try:
        ip = socket.gethostbyname(host)
        print("\n\nCabeçalho HTTP de:", host)
        print("")
        
        response_text = send_http_request(host, port)
        print(response_text.split('\r\n\r\n')[0])  # Imprime apenas o cabeçalho HTTP
        
        print("\n\nConectando-se a:", host, "[{}] na porta".format(ip), port, "(http) open")
    except socket.gaierror:
        print("Erro: Não foi possível resolver o nome do host.")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n")
