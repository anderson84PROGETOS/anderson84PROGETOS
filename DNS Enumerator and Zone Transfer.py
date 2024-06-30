import subprocess
import dns.resolver
import tkinter as tk
from tkinter import scrolledtext

def dns_enum(domain, info_text):
    try:
        answers = dns.resolver.resolve(domain, 'A')
        info_text.insert(tk.END, "Host's addresses\n==============\n")
        for answer in answers:
            info_text.insert(tk.END, f"{domain: <40} {'IN A': <10} IP: {answer.address}\n")
    except dns.resolver.NoAnswer:
        info_text.insert(tk.END, f"[!] Nenhum registro A encontrado para {domain}.\n")
    except dns.resolver.NXDOMAIN:
        info_text.insert(tk.END, f"[!] O domínio {domain} não foi encontrado.\n")
    except Exception as e:
        info_text.insert(tk.END, f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")
    
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        info_text.insert(tk.END, f"\n\nMail (MX) Servers\n===============\n")
        if answers:
            for answer in answers:
                info_text.insert(tk.END, f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {dns.resolver.resolve(answer.exchange, 'A')[0].address}\n")
        else:
            info_text.insert(tk.END, f"[!] Nenhum registro MX encontrado para {domain}.\n")
    except Exception as e:
        info_text.insert(tk.END, f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        info_text.insert(tk.END, f"\n\nName Servers\n===============\n")
        for answer in answers:
            info_text.insert(tk.END, f"{answer.target.to_text(): <40} {'IN NS': <10} IP: {dns.resolver.resolve(answer.target, 'A')[0].address}\n")
    except dns.resolver.NoAnswer:
        info_text.insert(tk.END, f"[!] Nenhum registro NS encontrado para {domain}.\n")
    except Exception as e:
        info_text.insert(tk.END, f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

def dns_transfer(site, info_text):
    info_text.insert(tk.END, f"\n\n\nTransferência de Zona DNS\n======================\n")
    
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    info_text.insert(tk.END, f"\nSaída de: nslookup -query=ns {site}\n\n")
    info_text.insert(tk.END, output_dns.stdout)
    
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]
    info_text.insert(tk.END, f"\nServidores DNS Encontrados\n=======================\n")
    for server in servers:
        info_text.insert(tk.END, f"{server}\n")
    
    unique_outputs = set()
    
    for server in servers:
        output_mx = subprocess.run(['nslookup', '-type=mx', site, server], capture_output=True, text=True)
        info_text.insert(tk.END, f"\nSaída de: nslookup -type=mx {site} {server}\n\n")
        info_text.insert(tk.END, output_mx.stdout)
        
        filtered_lines_mx = [line for line in output_mx.stdout.splitlines() if "mail exchanger" in line]
        unique_outputs.add("\n".join(filtered_lines_mx))
        
        output_ns = subprocess.run(['nslookup', site, server], capture_output=True, text=True)
        info_text.insert(tk.END, f"\nSaída de: nslookup {site} {server}\n\n")
        info_text.insert(tk.END, output_ns.stdout)
        
        filtered_lines_ns = [line for line in output_ns.stdout.splitlines() if "name =" in line]
        unique_outputs.add("\n".join(filtered_lines_ns))
        
        for ns_line in filtered_lines_ns:
            ns_name = ns_line.split("name =")[-1].strip()
            if ns_name:
                output_ip = subprocess.run(['nslookup', ns_name], capture_output=True, text=True)
                info_text.insert(tk.END, f"\nSaída de: nslookup {ns_name}\n\n")
                info_text.insert(tk.END, output_ip.stdout)
                
                filtered_lines_ip = [line for line in output_ip.stdout.splitlines() if "Address" in line]
                unique_outputs.add("\n".join(filtered_lines_ip))    

def execute_dns_operations():
    url = url_entry.get()
    site = url.replace('http://', '').replace('https://', '').split('/')[0]
    
    info_text.config(state=tk.NORMAL)
    info_text.delete(1.0, tk.END)
    
    dns_enum(site, info_text)
    dns_transfer(site, info_text)
    
    info_text.config(state=tk.DISABLED)

# Configuração da janela principal
root = tk.Tk()
root.title("DNS Enumerator and Zone Transfer")
root.wm_state('zoomed')

# Entrada de URL
url_label = tk.Label(root, text="Digite o nome do website ou a URL do website", font=("Arial", 12))
url_label.pack(pady=5)

url_entry = tk.Entry(root, width=38, font=("Arial", 12))
url_entry.pack(pady=5)

# Botão para executar as operações DNS
execute_button = tk.Button(root, text="Executar", font=("Arial", 12), command=execute_dns_operations, bg="#0bfc03")
execute_button.pack(pady=5)

# Área de texto para exibir as informações
info_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=43, font=("Arial", 12))
info_text.pack(pady=5)
info_text.config(state=tk.DISABLED)

# Iniciar o loop da interface gráfica
root.mainloop()
