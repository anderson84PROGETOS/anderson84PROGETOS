import re
import requests
from bs4 import BeautifulSoup
from socket import *
import dns.resolver
import ipaddress

print("""

██████╗ ██╗      ██████╗  ██████╗██╗  ██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗    ██╗██████╗ 
██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║    ██║██╔══██╗
██████╔╝██║     ██║   ██║██║     █████╔╝     ███████╗██║     ███████║██╔██╗ ██║    ██║██████╔╝
██╔══██╗██║     ██║   ██║██║     ██╔═██╗     ╚════██║██║     ██╔══██║██║╚██╗██║    ██║██╔═══╝ 
██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗    ███████║╚██████╗██║  ██║██║ ╚████║    ██║██║     
╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═╝╚═╝     
                                                                                             
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
        comando = f'domain {endereco_host}\r\n' if servidor_whois == 'whois.verisign-grs.com' else f'{endereco_host}\r\n'
        objeto_socket.send(comando.encode())
        
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

    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        emails = re.findall(email_regex, whois_text)

    return emails

def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        return field.find_next_sibling("div").get_text(strip=True)
    return None

def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200:
        if re.search(r'\.com$', endereco):
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

        elif re.search(r'\.br$', endereco) and response_registro_br.status_code == 200:
            soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
            div_result = soup_registro_br.find("div", class_="result")
            if div_result:
                print(div_result.get_text())
        else:
            print("Tipo de domínio desconhecido ou não suportado.")
    else:
        print("Erro ao obter informações WHOIS.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    print(resultado)

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov')
    if servidor_whois_gov:
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        print(resultado)
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def get_mx_ip(website):
    try:
        website = re.sub(r'^https?://', '', website)
        answers = dns.resolver.resolve(website, 'MX')
        mx_record = answers[0].exchange.to_text()

        real_ip = gethostbyname(mx_record)
        print(f"\n\nO IP real do servidor MX do website {website} é: {real_ip}")
        
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print("\nNenhum registro MX encontrado ou domínio não existe.")
    except gaierror as e:
        print(f"Erro ao tentar obter o IP: {e}")

def consulta_whois():
    endereco = input("\n\nDigite o nome do website WHOIS: ").strip()
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

def list_subnet_ips(subnet):
    resultado = ""
    try:
        rede = ipaddress.ip_network(subnet, strict=False)
        resultado += f"Enderesos IP no bloco: {subnet}\n\n"
        
        for ip in rede.hosts():
            resultado += str(ip) + "\n"
    except ValueError as e:
        resultado += f"Erro: {e}\n"
    return resultado

def salvar_bloco_ip(conteudo):
    nome_arquivo = input("\nDigite o nome do arquivo para salvar o bloco de IP (ex: bloco_ip.txt): ")
    with open(nome_arquivo, "w") as arquivo:
        arquivo.write(conteudo)
    print(f"\nBloco de IPs salvo Em: {nome_arquivo}")

# Exemplo de uso
website = input("\nDigite o nome do website (ex: www.example.com): ")
get_mx_ip(website)

# Executa a consulta WHOIS
consulta_whois()

# Solicita ao usuário que insira o bloco de IP
subnet = input("\n\nDigite o bloco de IP do inetnum (ex: 200.196.144.0/20): ")
resultado_ips = list_subnet_ips(subnet)

# Exibe o resultado dos blocos IPs
print("\n\nResultados do bloco IP\n")
print(resultado_ips)

# Solicita ao usuário se deseja salvar o bloco de IP
salvar = input("\nDeseja salvar o bloco de IP em um arquivo? (s/n): ").strip().lower()
if salvar == 's':
    salvar_bloco_ip(resultado_ips)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
