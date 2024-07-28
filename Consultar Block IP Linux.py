import subprocess
import re
import requests
import ipaddress
from bs4 import BeautifulSoup
from socket import *
from tkinter import *
from tkinter import scrolledtext, filedialog, messagebox
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
    nslookup_command = f'nslookup -query=mx {domain} | grep "mail exchanger"'
    return run_command(nslookup_command)

def ping_host(host):
    ping_command = f'ping -c 1 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    match = ip_regex.search(ping_output)
    if match:
        return match.group(0)
    return None

def obter_whois(endereco):
    whois_command = f'whois {endereco}'
    return run_command(whois_command)

def consulta_whois(endereco):
    whois_result = obter_whois(endereco)
    return whois_result

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        return "Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20"

    ips = []
    for ip in network.hosts():
        ips.append(str(ip))

    return ips

def display_result(result):
    result_text.insert(END, result + '\n')
    result_text.yview(END)

def save_to_file():
    content = result_text.get(1.0, END).strip()
    if not content:
        messagebox.showinfo("Salvar", "Não há conteúdo para salvar.")
        return

    filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if filename:
        try:
            with open(filename, 'w') as f:
                f.write(content)
            messagebox.showinfo("Salvar", f"Conteúdo salvo com sucesso no arquivo: {filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o conteúdo no arquivo: {e}")

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
            mx_host = re.sub(r'^1\.|1$', '', mx_host).rstrip('.')  # Remove número 1 no início ou final, e ponto final
            display_result(f"\nPinging no website: {mx_host}")
            ping_result = ping_host(mx_host)
            display_result(ping_result)
            
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                display_result(f"\nConsultando WHOIS para IP: {ip_address}")
                whois_result = consulta_whois(ip_address)
                display_result(whois_result)
            else:
                display_result("IP não encontrado na resposta do ping.")

    subnet = entry_subnet.get().strip()
    if subnet:
        ips = list_subnet_ips(subnet)
        display_result("\n\nEndereços IP disponíveis na sub-rede\n")
        for ip in ips:
            display_result(ip)

        save = messagebox.askyesno("Salvar IPs", "Deseja salvar os IPs em um arquivo?")
        if save:
            filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if filename:
                try:
                    with open(filename, 'w') as f:
                        for ip in ips:
                            f.write(ip + '\n')
                    display_result(f"\nOs IPs foram salvos com sucesso no arquivo: {filename}")
                except Exception as e:
                    display_result(f"Erro ao salvar os IPs no arquivo: {e}")
    else:
        display_result("Por favor, insira um bloco de IP válido.")

root = Tk()
root.title("Consultar nslookup block")

# Maximizar a janela para Linux
root.attributes('-zoomed', True)

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

button_save = tk.Button(root, text="Salvar", command=save_to_file, bg="#f5a623", font=("TkDefaultFont", 11, "bold"))
button_save.pack(pady=5)

result_text = scrolledtext.ScrolledText(root, width=120, height=38, font=("TkDefaultFont", 12, "bold"))
result_text.pack(padx=10, pady=10)

root.mainloop()
