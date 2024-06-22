import subprocess
import tkinter as tk
from tkinter import scrolledtext
from urllib.parse import urlparse
import requests
import re

def obter_informacoes_website(endereco):
    user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers=user_agent)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                result = "==================================================== DNS Zone Transfer ====================================================\n\n"
                result += f"Name Servers: {dados['isp']}\n"
                result += f"\nOrganização: {dados['org']}\n"
                result += f"\nPaís: {dados['country']}\n"
                result += f"\nRegião: {dados['regionName']}\n"
                result += f"\nCidade: {dados['city']}\n\n"                
                result += exibir_ipv4(endereco)
                result += f"\n\n" 
                return result
            else:
                return "Falha ao obter informações de geolocalização.\n"
        else:
            return f"Erro ao acessar o serviço de geolocalização: {resposta.status_code}\n"
    except Exception as e:
        return f"Erro ao obter informações de geolocalização: {str(e)}\n"

def dns_transfer(site_url):
    parsed_url = urlparse(site_url)
    site = parsed_url.netloc or parsed_url.path  # Extrai o domínio da URL

    # Primeiro, obtenha as informações de geolocalização e endereços IPv4
    result = obter_informacoes_website(site)

    # Em seguida, realize a transferência de zona DNS
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    if not servers:
        result += "Nenhum servidor de nomes encontrado para o site.\n"
        display_result(result)
        return

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    for output in output_list_dns:
        output_lines = output.splitlines()
        filtered_lines = [line for line in output_lines if not line.startswith("Servidor:") and not line.startswith("Address:") and not line.strip() == ""]
        result += "\n\n".join(filtered_lines) + "\n"

    display_result(result)

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
        result = "\n↓ Endereços IP ↓\n\n"
        for ipv4_address in ipv4_addresses:
            result += ipv4_address + "\n\n"
            
        return result
    else:
        return "Nenhum Endereço IPv4 encontrado."

def display_result(result):
    info_text.config(state=tk.NORMAL)
    info_text.delete(1.0, tk.END)
    info_text.insert(tk.END, result)
    info_text.config(state=tk.DISABLED)

def run_dns_transfer():
    site_url = url_entry.get().strip()
    if site_url:
        dns_transfer(site_url)
    else:
        display_result("Por favor, insira uma URL válida.")

root = tk.Tk()
root.wm_state('zoomed')
root.title("DNS Zone Transfer")

url_label = tk.Label(root, text="Digite a URL do WebSite", font=("Arial", 11))
url_label.pack(pady=3)

url_entry = tk.Entry(root, width=35, font=("Arial", 11))
url_entry.pack(pady=3)

dns_transfer_button = tk.Button(root, text="DNS Zone Transfer", command=run_dns_transfer, font=("Arial", 11), bg="#0bfc03")
dns_transfer_button.pack(pady=5)

info_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=45, font=("Arial", 12))
info_text.pack(pady=5)

root.mainloop()
