import subprocess
import re
import requests
import ipaddress  # Importa o módulo ipaddress
from bs4 import BeautifulSoup
from socket import *

print("""

███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗     ███╗   ███╗██╗  ██╗
████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗    ████╗ ████║╚██╗██╔╝
██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝    ██╔████╔██║ ╚███╔╝ 
██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝     ██║╚██╔╝██║ ██╔██╗ 
██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║         ██║ ╚═╝ ██║██╔╝ ██╗
╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝         ╚═╝     ╚═╝╚═╝  ╚═╝
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
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

def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = []

    email_section = soup.find("div", class_="row-fluid registry-data")
    if email_section:
        email_text = email_section.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        email_matches = re.findall(email_regex, email_text)
        emails.extend(email_matches)

    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        email_matches = re.findall(email_regex, whois_text)
        emails.extend(email_matches)

    return emails

def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200 and response_registro_br.status_code == 200:
        if re.search(r'\.br$', endereco):
            soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
            div_result = soup_registro_br.find("div", class_="result")
            if div_result:
                result_text = div_result.get_text()
                print(result_text)

        elif re.search(r'\.com$', endereco):
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                print(whois_text)

                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)

                name = extrair_campo(whois_section, "Registrant Name:")
                registration_date = extrair_campo(whois_section, "Creation Date:")
                expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

                if name:
                    print(f"Nome do Titular: {name}")
                if registration_date:
                    print(f"Data de Registro: {registration_date}")
                if expiration_date:
                    print(f"Data de Expiração: {expiration_date}")
        else:
            print("Tipo de domínio desconhecido")
    else:
        print("Erro ao obter informações WHOIS.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    print(resultado)

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        print(resultado)
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def consulta_whois(endereco):
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

def list_subnet_ips(subnet):
    try:
        # Cria um objeto de sub-rede com base na string fornecida
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        print("\nErro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    print("\nEndereços IP disponíveis na sub-rede:")
    ips = []  # Lista para armazenar os IPs

    # Percorre todos os endereços IP na sub-rede e os imprime
    for ip in network.hosts():
        ips.append(str(ip))
        print(ip)

    # Pergunta ao usuário se deseja salvar os IPs em um arquivo
    save = input("\n\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: (exemplo: bloco_ip.txt): ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nOs IPs foram salvos com sucesso no arquivo: {filename}")
        except Exception as e:
            print(f"\nErro ao salvar os IP no arquivo: {e}")

def main():
    domain = input("Digite o nome do Website: ")
    print()
    
    # Get MX records
    mx_records = get_mx_records(domain)   
    print(f"\nRegistros MX para website: {domain}\n\n{mx_records}\n")    
    
    # Extract mail exchanger hosts and ping them
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()
            print(f"\nPinging no website: {mx_host}")
            ping_result = ping_host(mx_host)
            print(ping_result)
            
            # Get the IP address from the ping result
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                print(f"\n\nConsultando WHOIS para IP: {ip_address}")
                consulta_whois(ip_address)
            else:
                print("\nIP não encontrado na resposta do ping.")

    # Solicita ao usuário que insira o bloco de IP
    subnet = input("\n\nDigite o bloco de IP do inetnum: (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
