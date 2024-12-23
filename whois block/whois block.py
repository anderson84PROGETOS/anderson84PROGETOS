import subprocess
import re
import requests
import ipaddress  # Importa o módulo ipaddress
from bs4 import BeautifulSoup
from socket import *

print("""

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
    nslookup_command = f'nslookup -query=mx {domain} | findstr "mail exchanger"'
    return run_command(nslookup_command)

def ping_host(host):
    ping_command = f'ping -4 -n 1 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\[(\d+\.\d+\.\d+\.\d+)\]')
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
            if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
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

    # Filtra linhas que não começam com '%'
    linhas_filtradas = [linha for linha in resultado.splitlines() if not linha.startswith('%')]
    resultado_filtrado = '\n'.join(linhas_filtradas)
    print(resultado_filtrado)

def consulta_whois(endereco):
    obter_whois_br(endereco)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError:
        print("\nErro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20\n")
        return

    print("\nEndereços IP disponíveis na sub-rede\n")
    ips = []

    for ip in network.hosts():
        ips.append(str(ip))
        print(ip)

    save = input("\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nIP salvos no arquivo: {filename}")
        except Exception as e:
            print(f"\nErro ao salvar os IP no arquivo: {e}\n")

def main():
    domain = input("Digite o nome do Website: ")
    print()    
    mx_records = get_mx_records(domain)   
    print(f"\nRegistros MX para website: {domain}\n")
    
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            # Extraindo o nome do host MX do registro
            mx_host = line.split('=')[-1].strip()
            # Exibindo o domínio seguido do registro MX
            ping_result = ping_host(mx_host)
            ip_address = obter_ip_do_ping(ping_result)
            print(f"{domain}     MX = {mx_host}    IP: {ip_address}")
    
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()
            print(f"\n\nPinging no website: {mx_host}\n")
            ping_result = ping_host(mx_host)

            # Extrai apenas o endereço IP do resultado do ping
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                print(f"Consultando WHOIS para IP: {ip_address}")
                consulta_whois(ip_address)
            else:
                print(f"\nNão foi possível obter o IP do host: {mx_host}\n")

    subnet = input("\nDigite o bloco de IP do inetnum: (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
