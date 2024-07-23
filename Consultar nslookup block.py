import subprocess
import re
import requests
import ipaddress
from bs4 import BeautifulSoup
from socket import *
from tkinter import *
from tkinter import scrolledtext
import tkinter as tk

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout

def get_mx_records(domain):
    nslookup_command = f'nslookup -query=mx {domain} | findstr "mail exchanger"'
    return run_command(nslookup_command)

def ping_host(host):
    ping_command = f'ping -4 -n 1 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\[(\d+\.\d+\.\d+\.\d+)\]')
    match = ip_regex.search(ping_output)
    if match:
        return match.group(1)
    return None

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
                display_result(result_text)

        elif re.search(r'\.com$', endereco):
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                display_result(whois_text)

                emails = encontrar_emails(soup_whois)
                if emails:
                    display_result("\nE-mails encontrados:")
                    for email in emails:
                        display_result(email)

                name = extrair_campo(whois_section, "Registrant Name:")
                registration_date = extrair_campo(whois_section, "Creation Date:")
                expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

                if name:
                    display_result(f"Nome do Titular: {name}")
                if registration_date:
                    display_result(f"Data de Registro: {registration_date}")
                if expiration_date:
                    display_result(f"Data de Expiração: {expiration_date}")
        else:
            display_result("Tipo de domínio desconhecido")
    else:
        display_result("Erro ao obter informações WHOIS.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    display_result(resultado)

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        display_result(resultado)
    else:
        display_result("Servidor WHOIS para domínios .gov não encontrado.")

def consulta_whois(endereco):
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        display_result("Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    display_result("\n\nEndereços IP disponíveis na sub-rede\n")
    ips = []

    for ip in network.hosts():
        ips.append(str(ip))
        display_result(str(ip))

def display_result(result):
    result_text.insert(END, result + '\n')
    result_text.yview(END)

def main():
    domain = entry_website.get().strip()
    if not domain:
        display_result("Por favor, insira um nome de website válido.")
        return
    
    display_result(f"Registros MX para website: {domain}\n")
    mx_records = get_mx_records(domain)
    display_result(mx_records)
    
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()
            display_result(f"\nPinging no website: {mx_host}")
            ping_result = ping_host(mx_host)
            display_result(ping_result)
            
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                display_result(f"\nConsultando WHOIS para IP: {ip_address}")
                consulta_whois(ip_address)
            else:
                display_result("IP não encontrado na resposta do ping.")
    
    subnet = entry_subnet.get().strip()
    if subnet:
        list_subnet_ips(subnet)
    else:
        display_result("Por favor, insira um bloco de IP válido.")

root = Tk()
root.wm_state('zoomed')
root.title("Consultar nslookup block")

frame = Frame(root)
frame.pack(padx=10, pady=5)

# Criar e posicionar os widgets
label_instruction = tk.Label(root, text="Digite o nome do website", font=("TkDefaultFont", 11, "bold"))
label_instruction.pack()

entry_website = tk.Entry(root, width=23, font=("TkDefaultFont", 11, "bold"))
entry_website.pack()

label_subnet = tk.Label(root, text="Digite o bloco de IP Exemplo: inetnum: 200.196.144.0/20", font=("TkDefaultFont", 11, "bold"))
label_subnet.pack(pady=15)

entry_subnet = tk.Entry(root, width=50, font=("TkDefaultFont", 11, "bold"))
entry_subnet.pack()

button_extract = tk.Button(root, text="Consultar", command=main, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
button_extract.pack(pady=10)

result_text = scrolledtext.ScrolledText(root, width=120, height=38, font=("TkDefaultFont", 12, "bold"))
result_text.pack(padx=10, pady=10)

root.mainloop()
