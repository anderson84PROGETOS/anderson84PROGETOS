import re
import requests
from bs4 import BeautifulSoup
from socket import AF_INET, SOCK_STREAM, socket
import subprocess
import ipaddress

print("""

██████╗ ██╗      ██████╗  ██████╗██╗  ██╗    ██╗██████╗     ████████╗ ██████╗  ██████╗ ██╗     
██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝    ██║██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
██████╔╝██║     ██║   ██║██║     █████╔╝     ██║██████╔╝       ██║   ██║   ██║██║   ██║██║     
██╔══██╗██║     ██║   ██║██║     ██╔═██╗     ██║██╔═══╝        ██║   ██║   ██║██║   ██║██║     
██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗    ██║██║            ██║   ╚██████╔╝╚██████╔╝███████╗
╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝    ╚═╝╚═╝            ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
                                                                                               
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

def encontrar_emails(texto):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = re.findall(email_regex, texto)
    return emails

def extrair_campo(texto, label):
    padrao = re.compile(rf"{label}:\s*(.*)")
    resultado = padrao.search(texto)
    return resultado.group(1).strip() if resultado else None

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
            print(whois_text)

            # Extraindo e-mails
            emails = encontrar_emails(whois_text)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)

            # Extraindo mais campos, se necessário
            name = extrair_campo(whois_text, "Registrant Name")
            registration_date = extrair_campo(whois_text, "Creation Date")
            expiration_date = extrair_campo(whois_text, "Registrar Registration Expiration Date")

            if name:
                print(f"Nome do Titular: {name}")
            if registration_date:
                print(f"Data de Registro: {registration_date}")
            if expiration_date:
                print(f"Data de Expiração: {expiration_date}")

    if response_registro_br.status_code == 200 and re.search(r'\.br$', endereco):
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            print(result_text)
    else:
        print("")

def consulta_whois():
    endereco = input("\nDigite o IP do servidor MX do Ping Para Consultar WHOIS: ").strip()
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        servidor_whois_gov = servidores_whois_tdl.get('.gov')
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        print(resultado)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        print("Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    print("Endereços IP disponíveis na sub-rede:")
    ips = [str(ip) for ip in network.hosts()]
    for ip in ips:
        print(ip)

    save = input("\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nOs IP foram salvos com sucesso no arquivo: {filename}")
        except Exception as e:
            print(f"Erro ao salvar os IPs no arquivo: {e}")

def main():
    website = input("\nDigite o nome do website (ex, example.com): ").strip()

    # Consulta registros MX
    print("\nConsultando registros MX para:", website)
    mx_lookup = subprocess.run(["nslookup", "-query=mx", website], capture_output=True, text=True)
    print(mx_lookup.stdout)

    post = input("\nDigite o servidor MX (exemplo: post02.example.com): ").strip()

    if post:
        print("\nPing para:", post)
        ping_post = subprocess.run(["ping", "-4", "-n", "1", post], capture_output=True, text=True)
        print(ping_post.stdout)

        ip_line = [line for line in ping_post.stdout.split('\n') if 'Disparando' in line or 'Pinging' in line]
        if ip_line:
            ip_address = ip_line[0].split(' ')[2].strip('[]')
            print(f"\nIP do servidor MX {post}: {ip_address}")

    print("\nPing para:", website)
    ping_website = subprocess.run(["ping", "-4", "-n", "1", website], capture_output=True, text=True)
    print(ping_website.stdout)

    ip_line = [line for line in ping_website.stdout.split('\n') if 'Disparando' in line or 'Pinging' in line]
    if ip_line:
        ip_address = ip_line[0].split(' ')[2].strip('[]')
        print(f"\nIP do website {website}: {ip_address}")

    consulta_whois()

    subnet = input("\n\nDigite o bloco de IP (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

    input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")

if __name__ == "__main__":
    main()
