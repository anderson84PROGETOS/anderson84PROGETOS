import socket
import psutil
import sys
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

███████╗██╗████████╗███████╗     ██████╗ ██████╗ ███╗   ██╗███╗   ██╗███████╗ ██████╗████████╗
██╔════╝██║╚══██╔══╝██╔════╝    ██╔════╝██╔═══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝╚══██╔══╝
███████╗██║   ██║   █████╗      ██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║        ██║   
╚════██║██║   ██║   ██╔══╝      ██║     ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║        ██║   
███████║██║   ██║   ███████╗    ╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║███████╗╚██████╗   ██║   
╚══════╝╚═╝   ╚═╝   ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   
                                                                                                                                                                                                     
""")

def print_progress(progress):
    # Função para exibir a barra de progresso
    bar_length = 50  # Comprimento da barra de progresso
    block = int(round(bar_length * progress / 100))
    progress_bar = f"[{'#' * block}{'-' * (bar_length - block)}] {progress}%"
    sys.stdout.write(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\r{progress_bar}")  # Sobrescreve a linha anterior
    sys.stdout.flush()

def get_connected_sites():
    # Obtém todas as conexões de rede
    connections = psutil.net_connections(kind='inet')
    total_connections = len(connections)
    processed_connections = 0

    sites = {}

    for conn in connections:
        processed_connections += 1
        # Calcula o progresso
        progress = int((processed_connections / total_connections) * 100)
        print_progress(progress)  # Atualiza a barra de progresso

        # Verifica se a conexão está estabelecida
        if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
            try:
                # Obtém o endereço IP remoto
                remote_ip = conn.raddr.ip

                # Ignora o IP local (127.0.0.1 ou localhost)
                if remote_ip == "127.0.0.1" or remote_ip == "localhost":
                    continue

                # Tenta obter o nome do domínio do IP
                domain_name = socket.gethostbyaddr(remote_ip)[0]
                
                # Simplifica o nome do domínio para exibir apenas o domínio principal (removendo subdomínios)
                domain_parts = domain_name.split('.')
                if len(domain_parts) > 2:
                    domain = '.'.join(domain_parts[-2:])  # Considera o domínio e o TLD
                else:
                    domain = domain_name  # Caso já seja um domínio completo (ex.: google.com)

                # Adiciona o domínio à lista
                sites[remote_ip] = domain

            except Exception as e:
                # Ignora conexões onde o nome do host não pôde ser resolvido
                pass

    # Exibe a lista de sites conectados
    update_sites_list(sites)

def update_sites_list(sites):
    # Exibe os sites conectados
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nSites Conectados\n\n")
    for ip, site in sites.items():
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "site: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{site:<30} " + Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "IP: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + ip)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT +"\n\nVarredura Completa!")

def main():
    get_connected_sites()

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
