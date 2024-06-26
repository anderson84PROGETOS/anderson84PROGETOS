import re
import requests
from bs4 import BeautifulSoup
from socket import AF_INET, SOCK_STREAM, socket
import subprocess
import ipaddress

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ███╗   ███╗██╗  ██╗
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ████╗ ████║╚██╗██╔╝
██║ █╗ ██║███████║██║   ██║██║███████╗    ██╔████╔██║ ╚███╔╝ 
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║╚██╔╝██║ ██╔██╗ 
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██║ ╚═╝ ██║██╔╝ ██╗
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝
                                                             
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
    endereco = input("\n\n\nDigite o ip do ping para consultar whois: ").strip()
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

def list_subnet_ips(subnet):
    try:
        # Cria um objeto de sub-rede com base na string fornecida
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        print("Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    print("\n========== Endereços IP disponíveis na sub-rede ==========\n")
    ips = []  # Lista para armazenar os IPs

    # Percorre todos os endereços IP na sub-rede e os imprime
    for ip in network.hosts():
        ips.append(str(ip))
        print(ip)

    # Pergunta ao usuário se deseja salvar os IPs em um arquivo
    save = input("\nDeseja salvar os IPs em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nOs IPs foram salvos com sucesso no arquivo '{filename}'.")
        except Exception as e:
            print(f"Erro ao salvar os IPs no arquivo: {e}")

def main():
    website = input("\nDigite o nome do website: ").strip()

    # Consulta registros MX
    print("\nConsultando registros MX para: ", website)
    subprocess.run(["nslookup", "-query=mx", website])

    # Solicita ao usuário o nome do Post
    post = input("\nDigite o Post (exemplo: post02.Exemplo.com): ")

    if post:
        # Consulta registros MX com o nome do Post
        print("\nConsultando registros MX para: ", post)
        subprocess.run(["nslookup", "-query=mx", post])
        print("\nPing para:", post)
        subprocess.run(["ping", "-4", "-n", "1", post])

    # Realiza o ping para o website original
    print("\nPing para: ", website)
    subprocess.run(["ping", "-4", "-n", "1", website])

    # Executa a consulta WHOIS
    consulta_whois()

    # Solicita ao usuário que insira o bloco de IP
    subnet = input("\n\nDigite o bloco de IP (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

    input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")

if __name__ == "__main__":
    main()
