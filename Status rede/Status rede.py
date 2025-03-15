import psutil
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

# Mensagem com comando equivalente no PowerShell
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nOu Digite isso no PowerShell: Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' }     PID:   tasklist | findstr 4296 ")

# Exibe o banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"""

███████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗    ██████╗ ███████╗██████╗ ███████╗
██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝    ██╔══██╗██╔════╝██╔══██╗██╔════╝
███████╗   ██║   ███████║   ██║   ██║   ██║███████╗    ██████╔╝█████╗  ██║  ██║█████╗  
╚════██║   ██║   ██╔══██║   ██║   ██║   ██║╚════██║    ██╔══██╗██╔══╝  ██║  ██║██╔══╝  
███████║   ██║   ██║  ██║   ██║   ╚██████╔╝███████║    ██║  ██║███████╗██████╔╝███████╗
╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝
                                                                                       
""")

def obter_nome_processo(pid):
    """ Obtém o nome do processo pelo PID. """
    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "Desconhecido"

def listar_conexoes_estabelecidas():
    conexoes = psutil.net_connections(kind='tcp')  # Obtém conexões TCP

    # Separando conexões IPv4 e IPv6
    conexoes_ipv4 = []
    conexoes_ipv6 = []

    for conn in conexoes:
        if conn.status == 'ESTABLISHED':
            local_addr = conn.laddr.ip if conn.laddr else "N/A"
            local_port = conn.laddr.port if conn.laddr else "N/A"
            remote_addr = conn.raddr.ip if conn.raddr else "N/A"
            remote_port = conn.raddr.port if conn.raddr else "N/A"
            state = conn.status
            applied_setting = "Internet"
            owning_process = conn.pid if conn.pid else "N/A"
            process_name = obter_nome_processo(owning_process)  # Obtém nome do processo

            # Verifica se é IPv4 ou IPv6
            if ":" in local_addr:  # IPv6 contém ":"
                conexoes_ipv6.append((local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name))
            else:
                conexoes_ipv4.append((local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name))

    # Cabeçalho da tabela
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{'LocalAddress':<40} {'LocalPort':<10} {'RemoteAddress':<40} {'RemotePort':<10} {'State':<12} {'AppliedSetting':<15} {'PID':<7} {'Processo'}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "-" * 150)

    # Exibe IPv4 primeiro
    for local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name in conexoes_ipv4:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{local_addr:<40} {local_port:<10} {remote_addr:<40} {remote_port:<10} {state:<12} {applied_setting:<15} {owning_process:<7} {process_name}")

    # Exibe IPv6 depois
    for local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name in conexoes_ipv6:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{local_addr:<40} {local_port:<10} {remote_addr:<40} {remote_port:<10} {state:<12} {applied_setting:<15} {owning_process:<7} {process_name}")

if __name__ == "__main__":
    listar_conexoes_estabelecidas()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
