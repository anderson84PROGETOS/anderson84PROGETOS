import socket
import ssl
import requests
import urllib3

print("""

██████╗  ██████╗ ██████╗ ████████╗    ███████╗ ██████╗ ██████╗ ██╗   ██╗████████╗
██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██╔════╝██╔════╝██╔═══██╗██║   ██║╚══██╔══╝
██████╔╝██║   ██║██████╔╝   ██║       ███████╗██║     ██║   ██║██║   ██║   ██║   
██╔═══╝ ██║   ██║██╔══██╗   ██║       ╚════██║██║     ██║   ██║██║   ██║   ██║   
██║     ╚██████╔╝██║  ██║   ██║       ███████║╚██████╗╚██████╔╝╚██████╔╝   ██║   
╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   
                                                                                
""")

# Suprimir os avisos de InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cabeçalhos personalizados para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def check_pswa(server, port=443):
    try:
        # Verificar SSL para HTTPS
        sock = socket.create_connection((server, port), timeout=5)
        if port == 443:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=server) as ssock:
                cert = ssock.getpeercert()
                print(f"\nSSL Certificado válido para: {server}")
        
        # Acessar o PSWA com cabeçalhos personalizados (HTTP/HTTPS)
        protocol = "https" if port == 443 else "http"
        url = f"{protocol}://{server}:{port}/pswa/"
        verify_ssl = port == 443
        response = requests.get(url, timeout=5, verify=verify_ssl, headers=headers)
        
        if response.status_code == 200:
            print(f"\nPSWA encontrado em {url}")
        else:
            print(f"\nPSWA não encontrado. Status code: {response.status_code}")
            print("\n===============================================================")
    
    except ssl.SSLError as e:
        print(f"\nErro de SSL: {e}")
    except socket.timeout:
        print(f"\nServidor {server} não respondeu na porta {port}.")        
    except requests.exceptions.RequestException as e:
        print(f"\nErro ao tentar acessar {url}: {e}")
    except ConnectionRefusedError:
        print(f"\nConexão recusada na porta {port} para: {server:<25} Tentando outra porta")
        

def check_ssh(server, port=22):
    try:
        # Conectar e capturar o banner SSH
        sock = socket.create_connection((server, port), timeout=5)
        banner = sock.recv(1024).decode().strip()  # Ler o banner do SSH
        print(f"\nConexão SSH bem-sucedida em: {server:<25} Porta:{port}")
        print(f"\nBanner SSH: {banner}")
    except socket.timeout:
        print(f"\nServidor {server} não respondeu na porta {port} (SSH)")
    except ConnectionRefusedError:
        print(f"\nConexão SSH recusada na porta {port} para: {server}")
    except Exception as e:
        print(f"\nErro ao tentar acessar SSH: {e}")

def check_ftp(server, port=21):
    try:
        # Conectar e capturar o banner FTP
        sock = socket.create_connection((server, port), timeout=5)
        banner = sock.recv(1024).decode().strip()  # Ler o banner do FTP
        print(f"\nConexão FTP bem-sucedida em: {server:<25} Porta:{port}")
        print(f"\nBanner FTP: {banner}")
    except socket.timeout:
        print(f"\nServidor {server} não respondeu na porta {port} (FTP)")
    except ConnectionRefusedError:
        print(f"\nConexão FTP recusada na porta {port} para: {server}")
    except Exception as e:
        print(f"\nErro ao tentar acessar FTP: {e}")

def check_telnet(server, port=23):
    try:
        # Conectar e capturar o banner Telnet
        sock = socket.create_connection((server, port), timeout=5)
        banner = sock.recv(1024)  # Ler o banner do Telnet (em bytes)
        
        try:
            # Tentar decodificar usando CP850  latin-1  utf-8
            decoded_banner = banner.decode('latin-1', errors='ignore').strip()
            print(f"\nConexão Telnet bem-sucedida em: {server:<25} Porta:{port}")
            print(f"\nBanner Telnet: {decoded_banner}")
        except UnicodeDecodeError as e:
            print(f"\nErro ao decodificar o banner Telnet: {e}")
            print(f"Banner (bytes): {banner}")

    except socket.timeout:
        print(f"\nServidor {server} não respondeu na porta {port} (Telnet)")
    except ConnectionRefusedError:
        print(f"\nConexão Telnet recusada na porta {port} para: {server}")
    except Exception as e:
        print(f"\nErro ao tentar acessar Telnet: {e}")

def monitor():
    # Input do nome do website ou servidor
    server = input("\nDigite o nome do website: ")
    print("\n===============================================================")
    
    # Tentando primeiro na porta 443 (HTTPS)
    print("\nTentando conexão na porta: 443 (HTTPS)...")
    check_pswa(server, port=443)
    
    # Tentando na porta 80 (HTTP)
    print("\nTentando conexão na porta: 80 (HTTP)...")
    check_pswa(server, port=80)
    
    # Tentando na porta 22 (SSH)
    print("\n\nTentando conexão na porta: 22 (SSH)...")
    check_ssh(server, port=22)
    
    # Tentando na porta 21 (FTP)
    print("\n\nTentando conexão na porta: 21 (FTP)...")
    check_ftp(server, port=21)
    
    # Tentando na porta 23 (Telnet)
    print("\n\nTentando conexão na porta: 23 (Telnet)...")
    check_telnet(server, port=23)

if __name__ == "__main__":
    monitor()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
