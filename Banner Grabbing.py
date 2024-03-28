import socket

print(""""

██████╗  █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗      ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ 
██████╔╝███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ██║  ███╗██████╔╝███████║██████╔╝██████╔╝██║██╔██╗ ██║██║  ███╗
██╔══██╗██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██║██║╚██╗██║██║   ██║
██████╔╝██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝██║██║ ╚████║╚██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                                                      
""")

def scanport(addr, port):
    '''Check if port is open on host'''
    socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1)
    result = socket_obj.connect_ex((addr, port))
    socket_obj.close()

    if result == 0:
        machine_hostname = socket.gethostbyaddr(addr)[0]
        service = socket.getservbyport(port)
        print("\nPorta aberta detectada: {} \t-- Porta: {} \t-- Serviço: {} \t-- Nome do Host: {}".format(addr, port, service, machine_hostname))
        return port
    else:
        return None

def bannergrabbing(addr, port):
    '''Connect to process and return application banner'''
    print("\n\nObtendo informações do serviço para porta: ", port)
    bannergrabber = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(2)
    try:
        bannergrabber.connect((addr, port))
        bannergrabber.send(b'WhoAreYou\r\n')
        banner = bannergrabber.recv(100)
        bannergrabber.close()
        print(banner.decode(), "\n")
    except:
        print("Não é possível conectar à porta ", port)

def get_banner(sock):
    try:
        # Envia uma solicitação para obter o banner do serviço com um cabeçalho de usuário
        sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36\r\n\r\n")
        # Recebe a resposta
        banner = sock.recv(1024)
        # Tenta decodificar usando utf-8
        try:
            banner_decoded = banner.decode("utf-8")
        # Se falhar, tenta decodificar usando latin-1 (iso-8859-1)
        except UnicodeDecodeError:
            banner_decoded = banner.decode("latin-1")
        return banner_decoded
    except Exception as e:
        return str(e)

def get_http_header(addr):
    '''Connects to port 80 and gets HTTP header'''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((addr, 80))
        sock.send(b"GET / HTTP/1.1\r\nHost: " + addr.encode() + b"\r\nUser-Agent: Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36\r\n\r\n")
        header_data = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            header_data += chunk
            if b"\r\n\r\n" in header_data:
                break
        sock.close()
        return header_data.decode()
    except Exception as e:
        return str(e)

def portscanner(addr, ports):
    open_ports = []
    # Verifica se há portas separadas por hífen ou vírgulas
    if '-' in ports:
        start_port, end_port = map(int, ports.split('-'))
        for port in range(start_port, end_port + 1):
            open_port = scanport(addr, port)
            if open_port is not None:
                open_ports.append(open_port)
    elif ',' in ports:
        ports_list = map(int, ports.split(','))
        for port in ports_list:
            open_port = scanport(addr, port)
            if open_port is not None:
                open_ports.append(open_port)
    else:
        port = int(ports)
        open_port = scanport(addr, port)
        if open_port is not None:
            open_ports.append(open_port)
    return open_ports

def get_service_banners_for_host(addr, portlist):
    for port in portlist:
        bannergrabbing(addr, port)

if __name__ == '__main__':
    addr = input("\n\nPor favor, insira o endereço IP ou o nome do WebSite: ")
    ports = input("\n\n\nDigite a porta ou o intervalo de portas (exemplo: 21,22,23 ou 21-80): ")
    print("\n\n")

    open_ports = portscanner(addr, ports)

    get_service_banners_for_host(addr, open_ports)

    http_header = get_http_header(addr)
    print("\n\nCabeçalho HTTP da porta 80\n\n", http_header)

input("\n\n\n🎯 Pressione Enter para sair 🎯 \n")    
