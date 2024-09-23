import re
import requests
from bs4 import BeautifulSoup
from socket import *

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██╗███╗   ██╗███████╗ ██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██║████╗  ██║██╔════╝██╔═══██╗
██║ █╗ ██║███████║██║   ██║██║███████╗    ██║██╔██╗ ██║█████╗  ██║   ██║
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██║██║ ╚████║██║     ╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                                       
""")

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

def get_ip(domain):
    try:
        # Se o domínio for um IP, não faz a resolução DNS
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', domain):
            return domain
        ip = requests.get(f'https://dns.google/resolve?name={domain}&type=A').json()['Answer'][0]['data']
        print(f"Website IP: {ip}")
        return ip
    except Exception as e:
        print(f"Erro ao coletar IP: {e}")

def get_ip_info(ip):
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        ip_data = response.json()
        
        print("\nInformações do IP Website\n")        
        
        for key, value in ip_data.items():
            print(f"{key}: {value}")
        
        if 'loc' in ip_data:
            latitude, longitude = ip_data['loc'].split(',')
            map_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
            print(f"\nURL do Google Maps: {map_url}")
            
    except Exception as e:
        print(f"Erro ao coletar informações do IP: {e}")

def consulta_whois():
    endereco = input("\nDigite o IP ou Nome do website Para Consultar WHOIS: ").strip()
    print("\n")
    obter_whois_br(endereco)
    obter_whois(endereco)
    
    # Obter o IP do domínio
    ip = get_ip(endereco)
    if ip:
        get_ip_info(ip)

    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

# Executa a consulta WHOIS
consulta_whois()

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
