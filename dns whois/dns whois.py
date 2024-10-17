import subprocess
import os
import socket
import requests
from bs4 import BeautifulSoup
import re

# Função para limpar a tela
def limpar_tela():
    subprocess.call("cls" if os.name == "nt" else "clear", shell=True)

# Dicionário de servidores WHOIS por TLD
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Função para obter informações DNS usando o comando nslookup
def obter_info_dns(dominio, tipo_registro):
    try:
        resultado = subprocess.run(['nslookup', f'-type={tipo_registro}', dominio], capture_output=True, text=True)
        if resultado.returncode != 0:
            return f"Erro ao executar nslookup para {tipo_registro} no domínio {dominio}."
        
        saida_filtrada = [linha for linha in resultado.stdout.splitlines() if not linha.startswith("Servidor") and not linha.startswith("Address")]
        if not saida_filtrada:
            return f"Nenhuma informação de {tipo_registro} encontrada para {dominio}."
        
        return "\n".join(saida_filtrada).strip()
    except Exception as e:
        return f"Erro ao tentar obter informações DNS: {str(e)}"

# Função para obter o IP do domínio
def obter_ip(dominio):
    try:
        ip = socket.gethostbyname(dominio)
        return f"O domínio: {dominio}   IP: {ip}"
    except socket.gaierror:
        return f"Erro: Não foi possível obter o IP do domínio {dominio}."

# Função para fazer a requisição WHOIS via socket
def requisicao_whois(servidor_whois, endereco_host, padrao):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as objeto_socket:
        try:
            objeto_socket.connect((servidor_whois, 43))
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':
                    objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
                else:
                    objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'{endereco_host}\r\n'.encode())

            resultado = ''
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                resultado += dados.decode('latin-1')
            return resultado
        except Exception as e:
            return f"Erro: {str(e)}"

# Função para encontrar e-mails em um conteúdo HTML
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

# Função para extrair campos específicos do WHOIS
def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

# Função para obter informações WHOIS de um domínio
def obter_whois(endereco):
    if re.search(r'\.br$', endereco):
        obter_whois_br(endereco)
    else:
        url_whois = f"https://www.whois.com/whois/{endereco}"
        try:
            response_whois = requests.get(url_whois)
            response_whois.raise_for_status()  # Levanta um erro para códigos de resposta HTTP não 200

            # Parse WHOIS.COM
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                print(whois_text)

                # Extrair e exibir informações adicionais
                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)

                # Extrair mais campos se necessário
                name = extrair_campo(soup_whois, "Registrant Name:")
                registration_date = extrair_campo(soup_whois, "Creation Date:")
                expiration_date = extrair_campo(soup_whois, "Registrar Registration Expiration Date:")

                if name:
                    print(f"Nome do Titular: {name}")
                if registration_date:
                    print(f"Data de Registro: {registration_date}")
                if expiration_date:
                    print(f"Data de Expiração: {expiration_date}")
            else:
                print("Não foi possível encontrar as informações WHOIS.")
        except requests.HTTPError as http_err:
            print(f"Erro ao obter informações WHOIS: {http_err}")
        except Exception as e:
            print(f"Erro ao processar a requisição WHOIS: {str(e)}")

# Funções específicas para WHOIS do .br e .gov
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

# Função principal
# Função principal
def main():
    while True:
        dominio = input("\nDigite o IP ou nome do website: ").strip()
        if not dominio:
            print("Por favor, insira um domínio ou IP válido.")
            continue
        
        while True:
            limpar_tela()
            menu = (
                "\t1  = A\n"
                "\t2  = NS\n"
                "\t3  = PTR\n"
                "\t4  = TXT\n"
                "\t5  = MX\n"
                "\t6  = SOA\n"
                "\t7  = DS\n"
                "\t8  = SRV\n"
                "\t9  = NSEC3\n"
                "\t10 = HINFO\n"
                "\t11 = CNAME\n"
                "\t12 = ANY\n"
                "\t13 = IP\n"
                "\t14 = WHOIS\n"
                "\t00 = Digitar novo domínio\n"
                "\t0  = SAIR"
            )
            
            print(f"\n+ - [ RECONHECIMENTO DNS com NSLOOKUP ] - +")
            print(f"\nDomínio: {dominio}\n")
            print(menu)

            op = input("\nSelecione uma das opções: ")

            if op == '1':
                print("\nselecionado = A\n")
                print(obter_info_dns(dominio, 'A'))
            elif op == '2':
                print("\nselecionado = NS\n")
                print(obter_info_dns(dominio, 'NS'))
            elif op == '3':
                print("\nselecionado = PTR\n")
                print(obter_info_dns(dominio, 'PTR'))
            elif op == '4':
                print("\nselecionado = TXT\n")
                print(obter_info_dns(dominio, 'TXT'))
            elif op == '5':
                print("\nselecionado = MX\n")
                print(obter_info_dns(dominio, 'MX'))
            elif op == '6':
                print("\nselecionado = SOA\n")
                print(obter_info_dns(dominio, 'SOA'))
            elif op == '7':
                print("\nselecionado = DS\n")
                print(obter_info_dns(dominio, 'DS'))
            elif op == '8':
                print("\nselecionado = SRV\n")
                print(obter_info_dns(dominio, 'SRV'))
            elif op == '9':
                print("\nselecionado = NSEC3\n")
                print(obter_info_dns(dominio, 'NSEC3'))
            elif op == '10':
                print("\nselecionado = HINFO\n")
                print(obter_info_dns(dominio, 'HINFO'))
            elif op == '11':
                print("\nselecionado = CNAME\n")
                print(obter_info_dns(dominio, 'CNAME'))
            elif op == '12':
                print("\nselecionado = ANY\n")
                print(obter_info_dns(dominio, 'ANY'))
            elif op == '13':
                print("\nselecionado = IP\n")
                print(obter_ip(dominio))
            elif op == '14':
                print("\nselecionado = WHOIS\n")
                obter_whois(dominio)
            elif op == '00':
                break
            elif op == '0':
                print("Saindo...")
                return
            else:
                print("Opção inválida, tente novamente.")
            
            # Adicione uma pausa para o usuário ver o resultado
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()
