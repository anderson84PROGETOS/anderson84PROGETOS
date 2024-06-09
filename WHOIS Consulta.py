import re
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext
from socket import *

# WHOIS servers dictionary
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Function to make WHOIS request
def requisicao_whois(servidor_whois, endereco_host, padrao, output_text):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':  # For .com and .net domains
                objeto_socket.send('domain {}\r\n'.format(endereco_host).encode())
            else:
                objeto_socket.send('n + {}\r\n'.format(endereco_host).encode())
        else:
            objeto_socket.send('{}\r\n'.format(endereco_host).encode())
        
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            output_text.insert(tk.END, dados.decode('latin-1') + "\n")
    else:
        output_text.insert(tk.END, "Erro ao conectar ao servidor WHOIS.\n")
    objeto_socket.close()

# Function to find emails in HTML
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

# Function to extract specific field from WHOIS section
def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

# Function to get WHOIS information for a domain
def obter_whois(endereco, output_text):
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

# Function to get WHOIS information for .gov domains
def obter_whois_gov(endereco, output_text):
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False, output_text)
    else:
        output_text.insert(tk.END, "Servidor WHOIS para domínios .gov não encontrado.\n")

# Function to get WHOIS information for .br domains
def obter_whois_br(endereco, output_text):
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False, output_text)

# Function to get WHOIS information for IP addresses using who.is
def obter_whois_ip_whois(ip, output_text):
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

# Function to get WHOIS information for IP addresses based on the selected server
def obter_whois_ip(ip, output_text, servidor_selecionado):
    if servidor_selecionado == 'registro.br':
        requisicao_whois('whois.registro.br', ip, False, output_text)
    else:  # Servidor 'who.is'
        obter_whois_ip_whois(ip, output_text)

# Function to search WHOIS information based on the input
def buscar_whois():
    endereco = entry.get().strip()
    output_text.delete(1.0, tk.END)
    servidor_selecionado = var_servidor.get()
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', endereco):  # Verifica se é um IP
        obter_whois_ip(endereco, output_text, servidor_selecionado)
    elif re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco, output_text)
    elif re.search(r'\.br$', endereco):
        obter_whois_br(endereco, output_text)
    elif re.search(r'\.com$', endereco):
        obter_whois(endereco, output_text)    
    else:
        obter_whois(endereco, output_text)

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("WHOIS Consulta")

frame = tk.Frame(root)
frame.pack(pady=5)

label = tk.Label(frame, text="Digite o nome do Website ou IP para WHOIS", font=("Arial", 12))
label.pack(padx=10, pady=3)

entry = tk.Entry(frame, width=35, font=("Arial", 12))
entry.pack(padx=10, pady=5)

# Variável para armazenar a escolha do servidor WHOIS
var_servidor = tk.StringVar(value='registro.br')

frame_radios = tk.Frame(root)
frame_radios.pack(pady=2)

button = tk.Button(frame, text="Consultar WHOIS", command=buscar_whois, font=("Arial", 12), bg="#0bfc03")
button.pack(pady=1)

radio1 = tk.Radiobutton(frame_radios, text="registro.br", variable=var_servidor, value='registro.br', font=("Arial", 12))
radio1.pack(side=tk.LEFT, padx=2)

radio2 = tk.Radiobutton(frame_radios, text="who.is", variable=var_servidor, value='who.is', font=("Arial", 12))
radio2.pack(side=tk.LEFT, padx=2)

output_text = scrolledtext.ScrolledText(root, width=120, height=44, font=("TkDefaultFont", 11, "bold"))
output_text.pack(pady=2)

root.mainloop()
