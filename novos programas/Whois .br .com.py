import re
import socket
import requests
from bs4 import BeautifulSoup

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗       ██████╗ ██████╗         ██████╗ ██████╗ ███╗   ███╗
██║    ██║██║  ██║██╔═══██╗██║██╔════╝       ██╔══██╗██╔══██╗       ██╔════╝██╔═══██╗████╗ ████║
██║ █╗ ██║███████║██║   ██║██║███████╗       ██████╔╝██████╔╝       ██║     ██║   ██║██╔████╔██║
██║███╗██║██╔══██║██║   ██║██║╚════██║       ██╔══██╗██╔══██╗       ██║     ██║   ██║██║╚██╔╝██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██╗██████╔╝██║  ██║    ██╗╚██████╗╚██████╔╝██║ ╚═╝ ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝╚═════╝ ╚═╝  ╚═╝    ╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝
                                                                                               
""")

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br'
}

def requisicao_whois(servidor_whois, endereco_host, padrao):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as objeto_socket:
        try:
            objeto_socket.connect((servidor_whois, 43))
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':  # For .com and .net domains
                    objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
                else:
                    objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'{endereco_host}\r\n'.encode())
                
            resposta = b""
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                resposta += dados
            return resposta.decode('latin-1')
        except Exception as e:
            return f"Erro: {str(e)}"

def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = []

    # Procura e retorna os e-mails na página principal do WHOIS
    if soup.find("div", class_="row-fluid registry-data"):
        email_section = soup.find("div", class_="row-fluid registry-data")
        if email_section:
            email_text = email_section.get_text()
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

    try:
        response_whois = requests.get(url_whois)
        response_registro_br = requests.get(url_registro_br)

        if response_whois.status_code == 200:
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                print("\nInformações WHOIS (whois.com)\n")
                print(whois_text)

                # Extract and display additional information
                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)

                # Extract more fields if needed
                name = extrair_campo(soup_whois, "Registrant Name:")
                registration_date = extrair_campo(soup_whois, "Creation Date:")
                expiration_date = extrair_campo(soup_whois, "Registrar Registration Expiration Date:")

                if name:
                    print("\nNome do Titular:", name)
                if registration_date:
                    print("Data de Registro:", registration_date)
                if expiration_date:
                    print("Data de Expiração:", expiration_date)
        else:
            print("Erro ao obter informações WHOIS de whois.com.")

        if response_registro_br.status_code == 200:
            soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
            div_result = soup_registro_br.find("div", class_="result")
            if div_result:
                result_text = div_result.get_text()
                print("\nInformações WHOIS (registro.br)\n")
                print(result_text)
        else:
            print("Erro ao obter informações WHOIS de registro.br.")
    except Exception as e:
        print(f"Erro: {str(e)}")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resposta = requisicao_whois(servidor_whois, endereco, False)
    print("\nInformações WHOIS (registro.br)\n")
    print(resposta)

def main():
    dominio = input("\nDigite o IP ou nome do website: ").strip()
    if dominio:
        if dominio.endswith('.br'):
            obter_whois_br(dominio)
        else:
            obter_whois(dominio)
    else:
        print("Entrada inválida. Nenhum domínio fornecido.")
    
    print("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
    input()  # Espera o usuário pressionar Enter antes de sair

if __name__ == "__main__":
    main()
