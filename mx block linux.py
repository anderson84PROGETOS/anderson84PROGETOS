import subprocess
import re
import requests
import ipaddress
from bs4 import BeautifulSoup
from socket import *

print("""

███╗   ███╗██╗  ██╗    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗    ██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗
████╗ ████║╚██╗██╔╝    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝    ██║     ██║████╗  ██║██║   ██║╚██╗██╔╝
██╔████╔██║ ╚███╔╝     ██████╔╝██║     ██║   ██║██║     █████╔╝     ██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝ 
██║╚██╔╝██║ ██╔██╗     ██╔══██╗██║     ██║   ██║██║     ██╔═██╗     ██║     ██║██║╚██╗██║██║   ██║ ██╔██╗ 
██║ ╚═╝ ██║██╔╝ ██╗    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗    ███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗
╚═╝     ╚═╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
                                                                              
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
    nslookup_command = f'nslookup -query=mx {domain} | grep "mail exchanger"'
    return run_command(nslookup_command)

# Windows ping -4 -n 1     Linux ping -c 1
def ping_host(host):
    ping_command = f'ping -c 1 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    match = ip_regex.search(ping_output)
    if match:
        return match.group(0)
    return None

def obter_whois(endereco):
    whois_command = f'whois {endereco}'
    print(run_command(whois_command))

def consulta_whois(endereco):
    obter_whois(endereco)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        print("Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    print("Endereços IP disponíveis na sub-rede:")
    ips = []

    for ip in network.hosts():
        ips.append(str(ip))
        print(ip)

    save = input("\n\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: (exemplo: bloco_ip.txt): ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nOs IP foram salvos com sucesso no arquivo: {filename}")
        except Exception as e:
            print(f"Erro ao salvar os IP no arquivo: {e}")

def main():
    domain = input("Digite o nome do Website: ")
    print("\n")
    
    mx_records = get_mx_records(domain)   
    print(f"\nRegistros MX para website: {domain}\n\n{mx_records}\n")    
    
    # Extract mail exchanger hosts and ping them
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()            
            mx_host = re.sub(r'^1\.|1$', '', mx_host).rstrip('.')  # Remove número 1 no início ou final, e ponto final
            print(f"\nPinging no website: {mx_host}")
            print()
            ping_result = ping_host(mx_host)
            print(ping_result)
            
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                print(f"\nConsultando WHOIS para IP: {ip_address}")
                print()
                consulta_whois(ip_address)
            else:
                print("IP não encontrado na resposta do ping.")

    subnet = input("\n\nDigite o bloco de IP do inetnum: (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
