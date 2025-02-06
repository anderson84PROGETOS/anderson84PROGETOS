import socket
from colorama import init, Fore, Style
import requests  # Para capturar o cabeçalho HTTP

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
______               _     _____                      ______               _                        _ 
| ___ \             | |   /  ___|                     | ___ \             | |                      | |
| |_/ /  ___   _ __ | |_  \ `--.   ___   __ _  _ __   | |_/ / _ __   ___  | |_   ___    ___   ___  | |
|  __/  / _ \ | '__|| __|  `--. \ / __| / _` || '_ \  |  __/ | '__| / _ \ | __| / _ \  / __| / _ \ | |
| |    | (_) || |   | |_  /\__/ /| (__ | (_| || | | | | |    | |   | (_) || |_ | (_) || (__ | (_) || |
\_|     \___/ |_|    \__| \____/  \___| \__,_||_| |_| \_|    |_|    \___/  \__| \___/  \___| \___/ |_|                                                                                                                                                                                                                                                                                                                                                                       
""")

# Dicionário com alguns protocolos padrão associados às portas
PROTOCOLS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP (Servidor)",
    68: "DHCP (Cliente)",
    69: "TFTP (Trivial FTP)",
    80: "HTTP",
    111: "RPCbind",
    110: "POP3",
    123: "NTP (Network Time Protocol)",
    143: "IMAP",
    161: "SNMP",
    162: "SNMP (Trap)",
    443: "HTTPS",
    514: "Syslog",
    1106: "MySQL (Via TCP/IP)",
    1812: "RADIUS (Autenticação)",
    2049: "NFS (Network File System)",
    27017: "MongoDB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP Alternativo",
        
}

def get_banner(host, porta):
    """ Tenta obter o banner do serviço rodando na porta especificada. """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, porta))
            banner = s.recv(1024).decode().strip()
            return banner if banner else "Nenhum banner"
    except:
        return "Nenhum banner"

def get_http_header(host):
    """ Obtém o cabeçalho HTTP da porta 80 """
    try:
        response = requests.get(f"http://{host}", timeout=2)
        headers = response.headers
        formatted_headers = "\n".join([f"{key}: {value}" for key, value in headers.items()])
        return formatted_headers
    except:
        return "Não foi possível obter o cabeçalho HTTP"

def portscan(host, porta_inicial, porta_final=None):
    if porta_final is None:
        portas = [int(porta_inicial)]
    else:
        portas = range(int(porta_inicial), int(porta_final) + 1)

    for porta in portas:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            resultado = s.connect_ex((host, porta))
            protocolo = PROTOCOLS.get(porta, "Desconhecido")  # Obtém o protocolo, se existir

            if resultado == 0:
                banner = get_banner(host, porta)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{host:<25} Porta: {porta:<5} - ABERTA   " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Protocolo: {protocolo:<10} " + Fore.LIGHTGREEN_EX + f"Banner: {banner}\n")

                
                # Se a porta for 80, obter o cabeçalho HTTP e exibir
                if porta == 80:
                    http_header = get_http_header(host)
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nCabeçalho HTTP da porta 80\n\n{http_header}\n")
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + f"{host:<25} Porta: {porta:<5} - FECHADA", end="\r")
                

if __name__ == "__main__":
    host = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website: ")
    intervalo = input("\n\nDigite a porta ou intervalo de portas (ex: 21 ou 21-80): ")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nEscaneando Portas Aguarde...\n")

    try:
        if "-" in intervalo:
            porta_inicial, porta_final = intervalo.split("-")
            portscan(host, porta_inicial, porta_final)
        else:
            portscan(host, intervalo)
    except ValueError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: O formato deve ser 'porta' ou 'porta_inicial-porta_final'.")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
