import socket
import dns.resolver
import requests
from bs4 import BeautifulSoup
import re
import subprocess  # Importar o módulo subprocess para executar comandos do sistema

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ███╗   ███╗██╗  ██╗    ██████╗ ██╗███╗   ██╗ ██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ████╗ ████║╚██╗██╔╝    ██╔══██╗██║████╗  ██║██╔════╝ 
██║ █╗ ██║███████║██║   ██║██║███████╗    ██╔████╔██║ ╚███╔╝     ██████╔╝██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║╚██╔╝██║ ██╔██╗     ██╔═══╝ ██║██║╚██╗██║██║   ██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██║ ╚═╝ ██║██╔╝ ██╗    ██║     ██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                               
""")

# Mapeamento dos servidores WHOIS para diferentes TLDs
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def get_host_addresses(domain):
    try:
        addresses = socket.gethostbyname_ex(domain)
        return addresses[2]
    except socket.gaierror as e:
        print(f"Error resolving {domain}: {e}")
        return []

def get_name_servers(domain):
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        return [ns.to_text() for ns in ns_records]
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:
        print(f"Domain {domain} does not exist.")
        return []
    except Exception as e:
        print(f"Error resolving NS for {domain}: {e}")
        return []

def get_mx_servers(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return [mx.to_text().split()[1] for mx in mx_records]
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:
        print(f"Domain {domain} does not exist.")
        return []
    except Exception as e:
        print(f"Error resolving MX for {domain}: {e}")
        return []

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
                objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
        else:
            objeto_socket.send(f'{endereco_host}\r\n'.encode())

        response = ''
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            response += dados.decode('latin-1')  # Decodifica como latin-1 para compatibilidade
        objeto_socket.close()
        return response
    else:
        return "Erro ao conectar ao servidor WHOIS."

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

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            print(whois_text + "\n")

            emails = encontrar_emails(soup_whois)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)

            name = extrair_campo(whois_section, "Registrant Name:")
            registration_date = extrair_campo(whois_section, "Creation Date:")
            expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

            if name:
                print("Nome do Titular: " + name)
            if registration_date:
                print("Data de Registro: " + registration_date)
            if expiration_date:
                print("Data de Expiração: " + expiration_date)
    elif response_registro_br.status_code == 200 and re.search(r'\.br$', endereco):
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            print(result_text)
    else:
        print("Erro ao obter informações WHOIS.")

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        response = requisicao_whois(servidor_whois_gov, endereco, False)
        print(response)
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    response = requisicao_whois(servidor_whois, endereco, False)
    print(response)

def obter_whois_ip_whois(ip):
    url_whois = f"https://who.is/whois-ip/ip-address/{ip}"
    response_whois = requests.get(url_whois)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("div", class_="col-md-12 queryResponseBodyKey")

        if whois_section:
            whois_text = whois_section.get_text()
            print(whois_text + "\n")

            emails = encontrar_emails(soup_whois)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)
    else:
        print("Erro ao obter informações WHOIS.")

def obter_whois_ip(ip):
    obter_whois_ip_whois(ip)

def buscar_whois(endereco):
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', endereco):  # Verifica se é um IP
        obter_whois_ip(endereco)
    elif re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)
    elif re.search(r'\.br$', endereco):
        obter_whois_br(endereco)
    elif re.search(r'\.com$', endereco):
        obter_whois(endereco)    
    else:
        obter_whois(endereco)

def ping_mx_servers(mx_servers):
    try:
        for mx in mx_servers:
            print(f"\nRealizando ping para servidor MX: {mx}\n")
            # Ajuste para Windows: usar -n em vez de -c para o comando ping
            processo_ping = subprocess.Popen(["ping", "-n", "4", mx], stdout=subprocess.PIPE)
            output, _ = processo_ping.communicate()

            # Extração do IP a partir do resultado do ping
            ip_regex = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
            # Decodificar como latin-1 para Windows, com tratamento para erros
            output_decoded = output.decode('latin-1', errors='ignore')
            ip_matches = re.findall(ip_regex, output_decoded)

            if ip_matches:
                ip = ip_matches[-1]  # Pega o último IP encontrado
                print(f"Resultado do ping para {mx}: {ip}")

                # Obtém informações WHOIS para o IP encontrado
                print(f"\nWHOIS para o IP: {ip}\n")
                obter_whois_ip(ip)
            else:
                print(f"Não foi possível obter o IP para {mx}")

    except Exception as e:
        print(f"Erro ao realizar ping para servidores MX: {e}")

def main():
    endereco = input("\nDigite o endereço IP ou domínio para consultar Whois: ").strip()
    print("\n")
    buscar_whois(endereco)

    # Obtém informações adicionais do domínio se não for um endereço IP
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', endereco):
        print("\n\n_________________________ Hosts addresses ________________________________\n")
        addresses = get_host_addresses(endereco)
        for addr in addresses:
            print(f"  {addr}")

        print("\n_________________________ Name Servers ___________________________________\n")
        name_servers = get_name_servers(endereco)
        for ns in name_servers:
            print(f"  {ns}")

        print("\n_________________________ Mail (MX) Servers _______________________________\n")
        mx_servers = get_mx_servers(endereco)
        for mx in mx_servers:
            print(f"  {mx}") 
            
        print("\n_________________________ Ping to MX Servers _______________________________\n")
        ping_mx_servers(mx_servers)
        
        print("\n\n_________________________ Launching Whois Queries _________________________\n")        

        # Realiza a consulta WHOIS para todos os endereços IP associados ao domínio
        for addr in addresses:
            print(f"\nWHOIS para o endereço IP: {addr}\n")
            obter_whois_ip(addr)
            print()        
        
if __name__ == "__main__":
    main()

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
