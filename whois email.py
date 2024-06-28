import re
import requests
from bs4 import BeautifulSoup
from socket import *

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ███████╗███╗   ███╗ █████╗ ██╗██╗     
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔════╝████╗ ████║██╔══██╗██║██║     
██║ █╗ ██║███████║██║   ██║██║███████╗    █████╗  ██╔████╔██║███████║██║██║     
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║     
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
                                                                                
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

def encontrar_emails(text):
    email_regex = r'[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}'
    emails = re.findall(email_regex, text)
    return emails

def obter_whois(endereco):
    tld = '.' + endereco.split('.')[-1]
    servidor_whois = servidores_whois_tdl.get(tld, None)

    if servidor_whois:
        response = requisicao_whois(servidor_whois, endereco, servidor_whois in ['whois.verisign-grs.com', 'whois.educause.edu'])
        if response:
            emails = encontrar_emails(response)
            if emails:
                print("\n========== E-mails Encontrados ==========\n")
                for email in set(emails):  # Use set para evitar e-mails duplicados
                    print(email)
            else:
                print("\n========== E-mails Encontrados ==========\n")
        else:
            print("Não foi possível obter a resposta do servidor WHOIS.")
    else:
        print("TLD não suportado ou servidor WHOIS não encontrado.")

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        response = requisicao_whois(servidor_whois_gov, endereco, False)
        if response:
            emails = encontrar_emails(response)
            if emails:
                print("\n========== E-mails Encontrados ==========\n")
                for email in set(emails):
                    print(email)
            
            else:
                print("\n========== E-mails Encontrados ==========\n")

        else:
            print("Não foi possível obter a resposta do servidor WHOIS.")
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    response = requisicao_whois(servidor_whois, endereco, False)
    if response:
        emails = encontrar_emails(response)
        if emails:
            print("\n========== E-mails Encontrados ==========\n")
            for email in set(emails):
                print(email)
        
    else:
        print("Não foi possível obter a resposta do servidor WHOIS.")

def obter_whois_ip(ip):
    servidor_whois = servidores_whois_tdl.get('.ip', None)
    response = requisicao_whois(servidor_whois, ip, False)
    if response:
        emails = encontrar_emails(response)
        if emails:
            print("\n========== E-mails Encontrados (WHOIS) ==========\n")
            for email in set(emails):
                print(email)
        else:
            print("\nNenhum e-mail Encontrado no WHOIS.")
    else:
        print("Não foi possível obter a resposta do servidor WHOIS.")

def buscar_whois(endereco):
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', endereco):  # Verifica se é um IP
        obter_whois_ip(endereco)
    elif re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)
    elif re.search(r'\.br$', endereco):
        obter_whois_br(endereco)
    else:
        obter_whois(endereco)

def obter_emails_site(endereco):
    url = f"http://{endereco}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            emails = encontrar_emails(response.text)
            if emails:
                
                for email in set(emails):  # Use set para evitar e-mails duplicados
                    print(email)
            
        else:
            print(f"\nNão foi possível acessar o site ({url}). Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"\nErro ao acessar o site: {e}")

if __name__ == "__main__":
    endereco = input("\nDigite o nome do website: ")
    buscar_whois(endereco)
    obter_emails_site(endereco)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
