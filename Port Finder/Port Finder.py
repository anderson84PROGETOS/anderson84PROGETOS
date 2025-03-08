import nmap
import socket
import time
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗  ██████╗ ██████╗ ████████╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██████╔╝██║   ██║██████╔╝   ██║       █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██╔═══╝ ██║   ██║██╔══██╗   ██║       ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
██║     ╚██████╔╝██║  ██║   ██║       ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                
""")

def get_ip(host):
    """Converte nome do host para IP"""
    try:
        ip = socket.gethostbyname(host)
        return ip
    except socket.gaierror:
        return None

def parse_ports(port_input):
    """Converte a entrada de portas em uma lista de inteiros"""
    ports = []
    
    # Remove espaços em branco
    port_input = port_input.replace(' ', '')
    
    # Verifica se é um intervalo (ex.: 21-65536)
    if '-' in port_input:
        try:
            start, end = map(int, port_input.split('-'))
            if 1 <= start <= 65535 and 1 <= end <= 65535 and start <= end:
                ports = list(range(start, end + 1))
            else:
                raise ValueError("Intervalo de portas inválido (1-65535)")
        except ValueError as e:
            print(f"Erro: {e}")
            return None
    else:
        # Trata como lista de portas separadas por vírgula
        try:
            ports = [int(p) for p in port_input.split(',') if 1 <= int(p) <= 65535]
            if not ports:
                raise ValueError("Nenhuma porta válida fornecida")
        except ValueError as e:
            print(f"Erro: {e}")
            return None
    
    return ports

def scan_ports(target, ports):
    """Realiza scan de portas no alvo, exibindo portas abertas/filtradas, banner e serviços"""
    nm = nmap.PortScanner()
    
    # Converte para IP se for um domínio
    ip = get_ip(target) if not target.replace('.', '').isdigit() else target
    
    if not ip:
        print("Erro: Não foi possível resolver o hostname")
        return None
    
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nIniciando scan em: {target}\n\nIP: {ip}\n")
    
    # Exibe o estado do host uma vez
    nm.scan(ip, arguments='-p 80')  # Scan rápido para verificar estado
    for host in nm.all_hosts():
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Estado: {nm[host].state()}\n")
        break
    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Protocolo: tcp\n")
    
    # Inicia a contagem de tempo
    start_time = time.time()
    
    # Escaneia cada porta individualmente
    for port in ports:
        try:
            # Adiciona a opção -sV para detecção de serviço e versão
            nm.scan(ip, str(port), arguments='-sV')  # Escaneia uma porta por vez com detecção de versão
            for host in nm.all_hosts():
                if 'tcp' in nm[host] and port in nm[host]['tcp']:
                    state = nm[host]['tcp'][port]['state']
                    # Exibe apenas portas abertas ou filtradas com cores específicas
                    if state == 'open':
                        service = nm[host]['tcp'][port].get('name', 'desconhecido')
                        product = nm[host]['tcp'][port].get('product', '')
                        version = nm[host]['tcp'][port].get('version', '')
                        banner = f"{product} {version}".strip() if product or version else "Nenhum banner detectado"
                        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Porta: {port}\tEstado: {state:<10}\tServiço: {service:<10}\tBanner: {banner}")
                    elif state == 'filtered':
                        service = nm[host]['tcp'][port].get('name', 'desconhecido')
                        product = nm[host]['tcp'][port].get('product', '')
                        version = nm[host]['tcp'][port].get('version', '')
                        banner = f"{product} {version}".strip() if product or version else "Nenhum banner detectado"
                        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Porta: {port}\tEstado: {state:<10}\tServiço: {service:<10}\tBanner: {banner}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao escanear a porta {port}: {e}")
    
    # Calcula o tempo decorrido
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Tenta obter informações de serviço e OS (executa um scan adicional com -O se necessário)
    nm.scan(ip, arguments='-O -p ' + ','.join(map(str, ports)))  # Scan com detecção de OS
    service_info = ""
    for host in nm.all_hosts():
        os_info = nm[host].get('osmatch', [])
        cpe_info = nm[host].get('cpe', [])
        os_str = ""
        cpe_str = ""
        
        if os_info:
            os_names = [match.get('name', 'desconhecido') for match in os_info]
            os_str = "sistema Operacional: " + ", ".join(os_names[:2])  # Limita a 2 OSs para evitar excesso
        if cpe_info:
            cpe_str = "CPE: " + ", ".join(cpe_info[:2])  # Limita a 2 CPEs
        
        service_info = f"\nService Info: {os_str}" + (f"; {cpe_str}" if cpe_str else "\n")
        if not os_str and not cpe_str:
            service_info = "Service Info: Nenhuma informação de sistema operacional detectada\n"
        break
    
    # Exibe informações de serviço
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n{service_info}")
    
    # Formata o tempo em segundos ou minutos
    if elapsed_time < 60:
        time_str = f"{elapsed_time:,.2f}".replace('.', ',') + " segundos"
    else:
        minutes = elapsed_time / 60
        time_str = f"{minutes:,.2f}".replace('.', ',') + " minutos"
    
    # Exibe o tempo total do scan
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Escaneado Em: {time_str}")

def main():
    # Solicita input do usuário
    target = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o IP ou nome do website (exemplo: 192.168.1.1 ou google.com): ").strip()
    
    # Solicita portas ou intervalo
    port_input = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite as portas (ex: 21,22,23,25,53,55,80,111,443,8080,8081) ou intervalo (ex: 21-65536): ").strip()
    
    # Converte a entrada de portas em uma lista
    ports = parse_ports(port_input)
    
    if ports:
        # Executa o scan com as portas fornecidas
        scan_ports(target, ports)
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT +"\nNenhum scan realizado devido a entrada inválida de portas.")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n========== PRESSIONE ENTER PARA SAIR ==========\n")
