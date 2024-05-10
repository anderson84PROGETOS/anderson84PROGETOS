import subprocess
import socket
import ipaddress
import tkinter as tk
from tkinter import Scrollbar, Text, Entry, Button, Label, messagebox, filedialog  # Adicionando filedialog
import requests
from bs4 import BeautifulSoup

def obter_informacoes_whois_com():
    endereco = website_entry.get()
    url = f"https://www.whois.com/whois/{endereco}"
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        whois_section = soup.find("pre", class_="df-raw")
        
        if whois_section:
            text_box.insert(tk.END, whois_section.get_text() + '\n')
        else:
            text_box.insert(tk.END, "Não foi possível encontrar informações WHOIS para este domínio\n")
    else:
        text_box.insert(tk.END, "Erro ao obter informações WHOIS\n")

def obter_informacoes_whois_br():
    endereco = website_entry.get()
    servidor_whois = 'whois.registro.br'
    porta = 43
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((servidor_whois, porta))
    sock.sendall((endereco + "\r\n").encode())
    resposta_whois = b''
    while True:
        dados = sock.recv(1024)
        if not dados:
            break
        resposta_whois += dados
    sock.close()
    codecs = ['utf-8', 'iso-8859-1', 'latin-1']
    for codec in codecs:
        try:
            decoded_response = resposta_whois.decode(codec)
            break
        except UnicodeDecodeError:
            pass
    else:
        text_box.insert(tk.END, "Não foi possível decodificar a resposta WHOIS\n")
        return
    text_box.insert(tk.END, decoded_response + '\n')

def consultar_registros_mx():
    website = website_entry.get()
    try:
        # Consultar registros MX usando o comando nslookup para o website
        output = subprocess.run(["nslookup", "-query=mx", website], capture_output=True, text=True).stdout
        
        # Verificar se há registros MX na saída
        mx_records = [line.split()[-1] for line in output.splitlines() if "mail exchanger" in line.lower()]
        
        if mx_records:
            # Se houver registros MX, exibir na caixa de texto
            text_box.insert(tk.END, "Registros MX para o website\n")
            for record in mx_records:
                text_box.insert(tk.END, record + '\n')
        else:
            text_box.insert(tk.END, "Não foi possível encontrar registros MX para o website\n")
    except Exception as e:
        text_box.insert(tk.END, f"Erro ao consultar registros MX para o website: {e}\n")

def consultar_ping():
    post = website_entry.get()
    if post:
        output = subprocess.run(["ping", "-4", "-n", "1", post], capture_output=True, text=True).stdout
        text_box.insert(tk.END, output + '\n')
    else:
        text_box.insert(tk.END, "O Post não foi fornecido\n")

def list_subnet_ips():
    subnet = website_entry.get()
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        text_box.insert(tk.END, "Insira um bloco de IP válido. Exemplo: 200.196.144.0/20\n")
        return

    ips = []
    for ip in network.hosts():
        ips.append(str(ip))

    output = "\nEndereços IP disponíveis na sub-rede\n"
    for ip in ips:
        output += ip + '\n'
    text_box.insert(tk.END, output)    

def salvar_resultados():
    filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
    if filename:
        with open(filename, 'w') as f:
            text_content = text_box.get("1.0", tk.END)
            f.write(text_content)
        messagebox.showinfo("Salvar Resultados", "Os resultados foram salvos com sucesso!")

# Configurações da janela
window = tk.Tk()
window.wm_state('zoomed')
window.title("IP Block Check WHOIS .COM e .BR")

# Rótulos e campos de entrada
Label(window, text="Digite o nome do website", font=('TkDefaultFont', 12)).pack()
website_entry = Entry(window, width=30, font=('TkDefaultFont', 12))
website_entry.pack(pady=5)

# Botões
Button(window, text="Registros MX", command=consultar_registros_mx, font=('TkDefaultFont', 11), bg='#0cf2df').pack(pady=5)
Button(window, text="Consultar Ping", command=consultar_ping, font=('TkDefaultFont', 11), bg='#069467').pack(pady=5)
Button(window, text="WHOIS .BR", command=obter_informacoes_whois_br, font=('TkDefaultFont', 11), bg='#0cf249').pack(pady=5)
Button(window, text="WHOIS .COM", command=obter_informacoes_whois_com, font=('TkDefaultFont', 11), bg='#f21818').pack(pady=5)
Button(window, text="Listar IPs da Sub-rede", command=list_subnet_ips, font=('TkDefaultFont', 11), bg='#fcf408').pack(pady=5)
Button(window, text="Salvar Resultados", command=salvar_resultados, font=('TkDefaultFont', 11), bg='#e907ed').pack(pady=2)

# Caixa de texto
scrollbar = Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_box = Text(window, height=33, width=130, font=('TkDefaultFont', 13))
text_box.pack(pady=10)

text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

window.mainloop()
