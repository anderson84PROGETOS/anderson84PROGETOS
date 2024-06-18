import subprocess
import requests
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        ipv4_text = "\n".join(ipv4_addresses)
        result_text.insert(tk.END, f"========================================== Endereços IPv4 Encontrados ======================================================\n\n\n{ipv4_text}\n")
    else:
        messagebox.showinfo("Resultado", "Nenhum Endereço IPv4 encontrado.")

def obter_informacoes_website(endereco):
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers={'User-Agent': 'Mozilla/5.0'})
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                info_text = f"\n\n========================================== Informações do Website ==========================================================\n\n\n\nNAME SERVERS: {dados['isp']}\n\n\nIP: {dados['query']}\n"
                result_text.insert(tk.END, info_text)
            else:
                messagebox.showerror("Erro", f"Erro ao obter informações do site: {dados['message']}")
        else:
            messagebox.showerror("Erro", f"Erro ao consultar serviço para informações do site: Código {resposta.status_code}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao obter informações do site: {str(e)}")

def dns_transfer(site):
    result_text.insert(tk.END, "\n\n\n========================================== Transferência de Zona DNS =======================================================\n\n")
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    unique_outputs = set()
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        if output.stdout not in unique_outputs:
            unique_outputs.add(output.stdout)
    
    for output in unique_outputs:
        result_text.insert(tk.END, output + "\n")

def run_all():
    url = entry.get()
    site = url.replace('http://', '').replace('https://', '').split('/')[0]
    result_text.delete('1.0', tk.END)
    exibir_ipv4(site)
    obter_informacoes_website(site)
    dns_transfer(site)

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("Transfer DNS")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Digite a URL do website", font=("Arial", 11))
label.pack(pady=0)

entry = tk.Entry(frame, width=40, font=("Arial", 11))
entry.pack(pady=5)

button = tk.Button(frame, text="Executar", command=run_all, font=("Arial", 11), bg="#0bfc03")
button.pack(pady=5)

result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=44, font=("Arial", 12))
result_text.pack(padx=10, pady=5)

root.mainloop()
