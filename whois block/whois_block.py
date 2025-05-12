import subprocess
import re
import requests
import ipaddress
from bs4 import BeautifulSoup
from socket import *
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + r"""
██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
██║ █╗ ██║███████║██║   ██║██║███████╗    ██████╔╝██║     ██║   ██║██║     █████╔╝ 
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ 
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
                                                                                                    
""")

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout

def get_mx_records(domain):
    dig_command = f'dig +short {domain} MX'
    return run_command(dig_command)

def ping_host(host):
    ping_command = f'ping -c 1 -4 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\((\d+\.\d+\.\d+\.\d+)\)')
    match = ip_regex.search(ping_output)
    if match:
        return match.group(1)
    return None

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    resultado = ''
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':
                objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
        else:
            objeto_socket.send(f'{endereco_host}\r\n'.encode())
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            resultado += dados.decode('latin-1')
    objeto_socket.close()
    return resultado

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)

    linhas_filtradas = [linha for linha in resultado.splitlines() if not linha.startswith('%')]
    resultado_filtrado = '\n'.join(linhas_filtradas)
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + resultado_filtrado)

def consulta_whois(endereco):
    obter_whois_br(endereco)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20\n")
        return

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nEndereços IP Disponíveis na sub-rede\n")
    ips = []

    for ip in network.hosts():
        ips.append(str(ip))
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + str(ip) + Style.RESET_ALL)

    save = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nIP salvos no arquivo: {filename}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar os IP no arquivo: {e}\n")

def main():
    domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do Website: ")
    print()    
    mx_records = get_mx_records(domain)   
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nRegistros MX para website: {domain}\n")
    
    for line in mx_records.splitlines():
        if line:
            mx_host = line.split()[-1].strip()
            ping_result = ping_host(mx_host)
            ip_address = obter_ip_do_ping(ping_result)
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{domain}     MX = {mx_host}    IP: {ip_address}")
    
    for line in mx_records.splitlines():
        if line:
            mx_host = line.split()[-1].strip()
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nPinging no website: {mx_host}\n")
            ping_result = ping_host(mx_host)

            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Consultando WHOIS para IP: {ip_address}")
                consulta_whois(ip_address)
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNão foi possível obter o IP do host: {mx_host}\n")

    subnet = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o bloco de IP do inetnum: (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

if __name__ == "__main__":
    main()

input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
