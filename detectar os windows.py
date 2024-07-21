import subprocess
import requests
import socket

print("""

██████╗ ███████╗████████╗███████╗ ██████╗████████╗ █████╗ ██████╗      ██████╗ ███████╗
██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗    ██╔═══██╗██╔════╝
██║  ██║█████╗     ██║   █████╗  ██║        ██║   ███████║██████╔╝    ██║   ██║███████╗
██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   ██╔══██║██╔══██╗    ██║   ██║╚════██║
██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   ██║  ██║██║  ██║    ╚██████╔╝███████║
╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
                                                                                      
""")

def get_ttl_info(ttl):
    """
    Interpreta o valor TTL e retorna o sistema operacional associado.
    """
    ttl_map = {
        'Linux': (0, 64),           # TTL entre 0 e 64 geralmente associado ao Linux
        'Windows': (65, 128),       # TTL entre 65 e 128 geralmente associado ao Windows
        'UNIX': (127, 255),         # TTL entre 127 e 255 geralmente associado ao UNIX
        'Desconhecido': (256, float('inf'))  # TTL maior que 255 é considerado desconhecido
    }
    
    # Identifica o sistema operacional baseado no TTL
    for os, (min_ttl, max_ttl) in ttl_map.items():
        if min_ttl <= ttl <= max_ttl:
            return os
    return 'Não foi detectado o sistema operacional'

def check_port(ip, port):
    """
    Verifica se uma porta específica está aberta em um IP.
    """
    try:
        with socket.create_connection((ip, port), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def main():
    # Solicita ao usuário que digite o nome ou endereço IP do website
    website = input("\nDigite o nome ou endereço IP do website: ")
    print("\n\nDetectando Sistema Operacional\n==============================\n")

    # Usa o comando 'ping' para verificar a disponibilidade do site e obter o endereço IP
    try:
        result = subprocess.run(['ping', '-n', '1', website], capture_output=True, text=True)
        ping_output = result.stdout
        
        ttl_value = None
        for line in ping_output.split('\n'):
            if "TTL=" in line:
                # No Windows, a linha contém "TTL="
                ttl_start = line.index("TTL=") + 4
                ttl_end = line.index(" ", ttl_start) if " " in line[ttl_start:] else len(line)
                ttl_value = int(line[ttl_start:ttl_end])
                os_info = get_ttl_info(ttl_value)
                print(f"Resposta do WebSite: {website}    bytes=32 tempo={line.split('tempo=')[1].split('ms')[0]}ms TTL={ttl_value}    ====> Sistema Operacional = {os_info}")
                break
        if ttl_value is None:
            print("\nNão foi possível obter o Sistema Operacional\n")
    except Exception as e:
        print(f"Erro ao executar o ping: {e}")

    # Verifica a disponibilidade das portas 80 e 443
    try:
        # Resolve o IP do site
        ip = socket.gethostbyname(website)
        
        # Verifica portas
        ports = [80, 443]
        for port in ports:
            if check_port(ip, port):
                print(f"\nPorta {port:<9} está aberta em: {ip}")
            else:
                print(f"Porta {port:<5} não está aberta em: {ip}")
    except Exception as e:
        print(f"Erro ao verificar portas: {e}")

    # Usa o comando 'curl' para obter os cabeçalhos HTTP do site
    try:
        # Tenta ambas HTTP e HTTPS
        url = f"http://{website}"
        try:
            response = requests.head(url)
        except requests.RequestException:
            url = f"https://{website}"
            response = requests.head(url)
        
        # Obtém o cabeçalho HTTP
        headers = response.headers
        server = headers.get('Server', 'Não disponível')
        # Exibe a informação
        print(f"\n\nServer: {server}")
    except requests.RequestException as e:
        print(f"\nErro ao obter cabeçalhos HTTP: {e}")

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
