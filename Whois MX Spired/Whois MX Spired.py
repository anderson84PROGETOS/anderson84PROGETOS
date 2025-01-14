import ipaddress
import sys
from datetime import datetime
import locale
import re
import requests
from bs4 import BeautifulSoup
from socket import *
import dns.resolver
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ███╗   ███╗██╗  ██╗    ███████╗██████╗ ██╗██████╗ ███████╗██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ████╗ ████║╚██╗██╔╝    ██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║███████║██║   ██║██║███████╗    ██╔████╔██║ ╚███╔╝     ███████╗██████╔╝██║██████╔╝█████╗  ██║  ██║
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║╚██╔╝██║ ██╔██╗     ╚════██║██╔═══╝ ██║██╔══██╗██╔══╝  ██║  ██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██║ ╚═╝ ██║██╔╝ ██╗    ███████║██║     ██║██║  ██║███████╗██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
""")

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def remover_copyright(texto):
    # Remove o texto de copyright
    copyright_pattern = re.compile(r"%.*\n", re.MULTILINE)
    return re.sub(copyright_pattern, "", texto)

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

    # Filtra a mensagem indesejada "No match found" do WHOIS
    if "No match found" in resultado:
        return ''  # Retorna uma string vazia caso não encontre nenhum resultado

    return resultado

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

def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

def remover_informacoes_extra(texto):
    # Remover informações extras, como o aviso de ICANN, outros termos e o link da ICANN
    extra_pattern = re.compile(r"(URL of the ICANN WHOIS Data Problem Reporting System:.*|Last update of WHOIS database:.*|By submitting a query to the Amazon Registrar.*|Visit Amazon Registrar, Inc. at https://registrar.amazon.com.*|Contact information available here:.*|© \d{4}, Amazon\.com, Inc\..*|For more information on Whois status codes, please visit https://icann.org/epp|agree to abide by the following terms.*?https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-contact-support.html)", re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return re.sub(extra_pattern, "", texto)

def obter_whois_com(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    
    # Realiza a requisição para obter as informações WHOIS
    response_whois = requests.get(url_whois)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            # Remover copyrights e informações extras do WHOIS
            whois_text = remover_copyright(whois_text)
            whois_text = remover_informacoes_extra(whois_text)
            print(Fore.LIGHTYELLOW_EX + whois_text)

            # Extraindo e exibindo mais informações
            emails = encontrar_emails(soup_whois)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)

            # Extraindo mais campos, se necessário
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
        print("Erro ao obter informações WHOIS do site whois.com.")

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
                # Remover copyrights e informações extra do WHOIS
                whois_text = remover_copyright(whois_text)
                whois_text = remover_informacoes_extra(whois_text)
                print(Fore.LIGHTMAGENTA_EX + whois_text)

                # Extraindo mais informações
                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)

                # Extraindo mais campos se necessário
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
        print("Erro ao obter informações WHOIS.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    if resultado.strip():  # Verifica se a resposta não está vazia
        print(Fore.LIGHTGREEN_EX + remover_copyright(resultado))        
    else:
        print()

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        print(Fore.LIGHTMAGENTA_EX + remover_copyright(resultado))
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def get_whois_info(ip_address):
    url = f"https://who.is/whois-ip/ip-address/{ip_address}"
    response = requests.get(url)

    if response.status_code == 200:
        # Parsear o conteúdo da página com BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Procurar pela tag <pre> que contém as informações WHOIS
        whois_section = soup.find("pre")
        
        # Se a tag <pre> for encontrada, pegar o conteúdo
        if whois_section:
            whois_text = whois_section.get_text()

            # Exibir apenas as informações WHOIS, se encontradas
            if "No match found" not in whois_text:
                print(Fore.LIGHTCYAN_EX + whois_text)       

def obter_mx(endereco):
    try:
        respostas = dns.resolver.resolve(endereco, 'MX')
        print(Fore.LIGHTMAGENTA_EX + "\n========== REGISTROS MX ENCONTRADOS ==========\n")
        for resposta in respostas:
            mx_host = str(resposta.exchange).rstrip('.')
            try:
                ip = gethostbyname(mx_host)
                print(Fore.LIGHTMAGENTA_EX + f"\n{mx_host} IP: {ip}")
            except:
                print(f"{mx_host} IP: Não foi possível resolver")
    except:
        pass  # Nenhum erro ou registro será exibido caso não haja resultados.

def get_whois_info(ip_address):
    url = f"https://who.is/whois-ip/ip-address/{ip_address}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        whois_section = soup.find("pre")
        if whois_section:
            whois_text = whois_section.get_text()
            if "No match found" not in whois_text:
                print(Fore.LIGHTCYAN_EX + whois_text)

def is_ip(address):
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

# Função para exibir o input
def main():
    endereco = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o domínio ou IP para consulta: ")  # Solicita o input do usuário
    obter_whois_br(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)
    obter_whois(endereco)
    obter_whois_com(endereco)  # Adicionando a nova função aqui
    obter_mx(endereco) 

    whois_info = get_whois_info(endereco)
    if whois_info:  # Verifica se a variável contém algo antes de imprimir
        print(Fore.LIGHTCYAN_EX + whois_info)

    print(Fore.LIGHTMAGENTA_EX + "\n\n============== " + Fore.LIGHTGREEN_EX + "Mais Informações" + Fore.LIGHTMAGENTA_EX + " ==============\n")

    # Configuração para exibir a data em português do Brasil
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

    # Reconfigurar a codificação de saída para latin-1
    sys.stdout.reconfigure(encoding='latin-1')

    # Função para formatar a data
    def formatar_data(data):
        try:
            data_obj = datetime.strptime(data, "%Y-%m-%d")
            nome_dia = data_obj.strftime("%A")
            nome_mes = data_obj.strftime("%B")
            ano = data_obj.year
            return f"{nome_dia}, {data_obj.day} de {nome_mes} de {ano}", data_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None, None

    # Função WHOIS para domínios genéricos .com
    def consulta_whois_generico(domain):
        url = f"https://rdap.org/domain/{domain}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "dominio": domain,
                    "criado_em": formatar_data(data.get("events", [{}])[0].get("eventDate", "N/A").split("T")[0]),
                    "expira_em": formatar_data(data.get("events", [{}])[2].get("eventDate", "N/A").split("T")[0]),
                    "alterado_em": formatar_data(data.get("events", [{}])[1].get("eventDate", "N/A").split("T")[0]),
                }
            return None
        except Exception:
            return None        

    # Função WHOIS para domínios .br
    def consulta_whois_br(domain):
        url = f"https://rdap.registro.br/domain/{domain}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "dominio": domain,
                    "criado_em": formatar_data(data.get("events", [{}])[0].get("eventDate", "N/A").split("T")[0]),
                    "expira_em": formatar_data(data.get("events", [{}])[2].get("eventDate", "N/A").split("T")[0]),
                    "alterado_em": formatar_data(data.get("events", [{}])[1].get("eventDate", "N/A").split("T")[0]),
                }
            return None
        except Exception:
            return None

    # Função WHOIS para IPs
    def consulta_whois_ip(ip):
        url = f"https://rdap.apnic.net/ip/{ip}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "dominio": ip,
                    "criado_em": formatar_data(data.get("events", [{}])[0].get("eventDate", "N/A").split("T")[0]),
                    "expira_em": (None, None),
                    "alterado_em": (None, None),
                }
            return None
        except Exception:
            return None

    # WHOIS principal
    def consulta_whois(entry):
        if is_ip(entry):
            return consulta_whois_ip(entry)
        elif entry.endswith(".br"):
            return consulta_whois_br(entry)
        else:
            return consulta_whois_generico(entry)

    whois_info = consulta_whois(endereco)

    if not whois_info:
        print(Fore.LIGHTRED_EX + "\nNenhuma informasao Encontrada")
    else:
        print(Fore.GREEN + Style.BRIGHT + f"\n\nDominio: {whois_info['dominio']}")
        if whois_info['criado_em'][0]:
            print(Fore.LIGHTYELLOW_EX + f"\nRegistrado: {whois_info['criado_em'][0]:<50}Registrado: {whois_info['criado_em'][1]}")        
        if whois_info['alterado_em'][0]:
            print(Fore.LIGHTMAGENTA_EX + f"\nModificado: {whois_info['alterado_em'][0]:<50}Modificado: {whois_info['alterado_em'][1]}")
        if whois_info['expira_em'][0]:
            print(Fore.LIGHTRED_EX + f"\nExpira: {whois_info['expira_em'][0]:<54}Expira: {whois_info['expira_em'][1]}")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
