import socket

print("""

██████╗  █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗      ██████╗ ██████╗  █████╗ ██████╗ 
██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗
██████╔╝███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ██║  ███╗██████╔╝███████║██████╔╝
██╔══██╗██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██╗██╔══██║██╔══██╗
██████╔╝██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
                                                                                         
""")

def banner_grab(ip, port):
    try:
        # Cria um socket
        s = socket.socket()
        s.settimeout(5)  # Define um tempo limite de 5 segundos

        # Conecta ao IP e porta fornecidos
        s.connect((ip, port))
        
        if port == 80:
            # Envia uma solicitação HTTP padrão para a porta 80
            s.sendall(b"HEAD / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % ip.encode())

        # Recebe a resposta (banner)
        banner = s.recv(1024)
        
        # Decodifica usando ISO-8859-1 (Latin-1)
        return banner.decode('ISO-8859-1').strip()
    except socket.error:
        # Ignora portas que estão fechadas ou recusam a conexão
        return None
    except Exception as e:
        return str(e)
    finally:
        s.close()

def parse_ports(port_range):
    """ Analisa a string de entrada de portas e retorna uma lista de portas. """
    ports = set()
    for part in port_range.split(','):
        if '-' in part:
            start_port, end_port = part.split('-')
            try:
                start_port = int(start_port)
                end_port = int(end_port)
                if start_port <= end_port:
                    ports.update(range(start_port, end_port + 1))
            except ValueError:
                print(f"Intervalo de porta inválido: {part}")
        else:
            try:
                ports.add(int(part))
            except ValueError:
                print(f"Porta inválida: {part}")
    return sorted(ports)

def main():
    ip = input("\nDigite o endereço IP ou domínio: ")
    port_range = input("\n\nDigite o intervalo de portas (ex: 21-8180 ou 80): ")
    ports = parse_ports(port_range)

    if not ports:
        print("Nenhuma porta válida fornecida.")
        return

    print(f"\n\nBanners Encontrados para o website: {ip}\n")
    print("""
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
| E | S | C | A | N | E | A | N | D | O |   | B | A | N | N | E | R |   | G | R | A | B |
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
""")
    for port in ports:
        banner = banner_grab(ip, port)
        if banner:  # Exibe apenas portas com banners encontrados
            print(f"\nPorta {port}: {banner}")

if __name__ == "__main__":
    main()
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")    
