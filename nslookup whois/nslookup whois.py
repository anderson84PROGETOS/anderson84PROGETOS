import subprocess
import re
import dns.resolver
import requests
from bs4 import BeautifulSoup
from socket import gethostbyname, gaierror, socket, AF_INET, SOCK_STREAM

print("""

███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗     ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗
████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝
██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝    ██║ █╗ ██║███████║██║   ██║██║███████╗
██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝     ██║███╗██║██╔══██║██║   ██║██║╚════██║
██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║         ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║
╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝          ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝
                                                                                                            
""")

# Servidores WHOIS para diferentes TLDs
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def get_ipv4_addresses(site):
    try:
        # Usando a biblioteca dns.resolver diretamente para obter os servidores DNS
        result = dns.resolver.resolve(site, 'NS')
        return [str(rdata.target) for rdata in result]
    except dns.resolver.NoAnswer:
        print("Nenhum servidor de nome encontrado para o site.")
        return []

def get_mx_ips(website):
    try:
        website = re.sub(r'^https?://', '', website)
        answers = dns.resolver.resolve(website, 'MX')

        mx_records = []
        for answer in answers:
            mx_record = answer.exchange.to_text().rstrip('.')  # Remove o ponto final
            real_ip = gethostbyname(mx_record)
            mx_records.append((mx_record, real_ip))
            print(f"\n\nMX do Domínio: {website}\n==============================================\n\nServidor: {mx_record} \n\nO IP Real do Servidor é: {real_ip}\n")
            
        return mx_records
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print("\nNenhum registro MX encontrado ou domínio não existe.")
        return None
    except gaierror as e:
        print(f"Erro ao tentar obter o IP: {e}")
        return None

def requisicao_whois(servidor_whois, endereco_host, padrao):
    try:
        objeto_socket = socket(AF_INET, SOCK_STREAM)
        conexao = objeto_socket.connect_ex((servidor_whois, 43))
        if conexao == 0:
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
                    objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
                else:
                    objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'{endereco_host}\r\n'.encode())
            resultado = ""
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                resultado += dados.decode('latin-1')
            objeto_socket.close()
            return resultado
        else:
            print("Erro de conexão com o servidor WHOIS.")
            return None
    except Exception as e:
        print(f"Erro ao conectar ao servidor WHOIS: {e}")
        return None

def extrair_campo(whois_section, campo):
    """
    Função para extrair um campo específico da seção WHOIS usando regex.
    """
    regex = re.compile(rf"{campo}\s*:\s*(.*)")
    resultado = regex.search(whois_section.get_text())
    if resultado:
        return resultado.group(1).strip()
    return None

def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = []

    # Procura e retorna os e-mails na página principal do WHOIS
    email_section = soup.find("div", class_="row-fluid registry-data")
    if email_section:
        email_text = email_section.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        email_matches = re.findall(email_regex, email_text)
        emails.extend(email_matches)

    # Procura e retorna os e-mails no resultado completo do WHOIS
    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        email_matches = re.findall(email_regex, whois_text)
        emails.extend(email_matches)

    return emails

def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200 and response_registro_br.status_code == 200:
        if re.search(r'\.br$', endereco):
            # Parse REGISTRO.BR
            soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
            div_result = soup_registro_br.find("div", class_="result")
            if div_result:
                result_text = div_result.get_text()
                print(result_text)

        elif re.search(r'\.com$', endereco):
            # Parse WHOIS.COM
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                print(whois_text)

                # Extract and display additional information
                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)

                # Extract more fields if needed
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

def consulta_whois():
    endereco = input("\nDigite o IP do MX Para Consultar WHOIS: ").strip()
    print("\n")
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

def main():
    site = input("\nDigite o nome do WebSite: ")
    ipv4_addresses = get_ipv4_addresses(site)
    print(f"\nServidores DNS para o site: {site}\n")
    for ipv4 in ipv4_addresses:
        print(ipv4.rstrip('.'))  # Remover o ponto final        

    mx_records = get_mx_ips(site)       
    consulta_whois()
    
if __name__ == "__main__":
    main()

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
