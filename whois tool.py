import re
import requests
from bs4 import BeautifulSoup
from socket import *

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ████████╗ ██████╗  ██████╗ ██╗     
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
██║ █╗ ██║███████║██║   ██║██║███████╗       ██║   ██║   ██║██║   ██║██║     
██║███╗██║██╔══██║██║   ██║██║╚════██║       ██║   ██║   ██║██║   ██║██║     
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║       ██║   ╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
                                                                             
""")

# Mapeamento dos servidores WHOIS para diferentes TLDs
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
                objeto_socket.send('domain {}\r\n'.format(endereco_host).encode())
            else:
                objeto_socket.send('n + {}\r\n'.format(endereco_host).encode())
        else:
            objeto_socket.send('{}\r\n'.format(endereco_host).encode())

        response = ''
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            response += dados.decode('latin-1')
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
    url_whois = "https://www.whois.com/whois/{}".format(endereco)
    url_registro_br = "https://registro.br/cgi-bin/whois/?qr={}".format(endereco)

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
    url_whois = "https://who.is/whois-ip/ip-address/{}".format(ip)
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

if __name__ == "__main__":
    endereco = input("\nDigite o nome do Website ou IP para WHOIS: ").strip()
    print("\n\n")
    buscar_whois(endereco)

input("\n\n🎯============ PRESSIONE ENTER PARA SAIR ============🎯\n")    
