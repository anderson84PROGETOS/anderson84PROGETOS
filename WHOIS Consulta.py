import re
import requests
from bs4 import BeautifulSoup
from socket import *
import tkinter as tk
from tkinter import scrolledtext

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
            output_text.insert(tk.END, whois_text + "\n")

            emails = encontrar_emails(soup_whois)
            if emails:
                output_text.insert(tk.END, "\nE-mails encontrados:\n")
                for email in emails:
                    output_text.insert(tk.END, email + "\n")

            name = extrair_campo(whois_section, "Registrant Name:")
            registration_date = extrair_campo(whois_section, "Creation Date:")
            expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

            if name:
                output_text.insert(tk.END, "Nome do Titular: " + name + "\n")
            if registration_date:
                output_text.insert(tk.END, "Data de Registro: " + registration_date + "\n")
            if expiration_date:
                output_text.insert(tk.END, "Data de Expiração: " + expiration_date + "\n")
    elif response_registro_br.status_code == 200 and re.search(r'\.br$', endereco):
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            output_text.insert(tk.END, result_text + "\n")
    else:
        output_text.insert(tk.END, "Erro ao obter informações WHOIS.\n")

def obter_whois_gov(endereco):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        response = requisicao_whois(servidor_whois_gov, endereco, False)
        output_text.insert(tk.END, response + "\n")
    else:
        output_text.insert(tk.END, "Servidor WHOIS para domínios .gov não encontrado.\n")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    response = requisicao_whois(servidor_whois, endereco, False)
    output_text.insert(tk.END, response + "\n")

def obter_whois_ip_whois(ip):
    url_whois = "https://who.is/whois-ip/ip-address/{}".format(ip)
    response_whois = requests.get(url_whois)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("div", class_="col-md-12 queryResponseBodyKey")

        if whois_section:
            whois_text = whois_section.get_text()
            output_text.insert(tk.END, whois_text + "\n")

            emails = encontrar_emails(soup_whois)
            if emails:
                output_text.insert(tk.END, "\nE-mails encontrados:\n")
                for email in emails:
                    output_text.insert(tk.END, email + "\n")
    else:
        output_text.insert(tk.END, "Erro ao obter informações WHOIS.\n")

def obter_whois_ip(ip):
    obter_whois_ip_whois(ip)

def buscar_whois():
    endereco = entry.get().strip()
    output_text.delete(1.0, tk.END)
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

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("WHOIS Consulta")

frame = tk.Frame(root)
frame.pack(pady=5)

label = tk.Label(frame, text="Digite o nome do Website ou IP para WHOIS", font=("Arial", 12))
label.pack(padx=10, pady=5)

entry = tk.Entry(frame, width=35, font=("Arial", 12))
entry.pack(padx=10, pady=5)

button = tk.Button(frame, text="Consultar WHOIS", command=buscar_whois, font=("Arial", 12), bg="#0bfc03")
button.pack(pady=5)

output_text = scrolledtext.ScrolledText(root, width=120, height=42, font=("TkDefaultFont", 12, "bold"))
output_text.pack(pady=5)

root.mainloop()
