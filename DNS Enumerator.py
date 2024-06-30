import dns.resolver
import dns.query
import dns.zone
import tkinter as tk
from tkinter import scrolledtext

def get_dns_records(domain, info_text):
    info_text.insert(tk.END, f"[+] Performing Enumeration for WebSite: {domain}\n\n")

    # Get SOA record
    try:
        soa_record = dns.resolver.resolve(domain, 'SOA')
        for soa in soa_record:
            info_text.insert(tk.END, f"[soa]    SOA {soa.mname} {soa.serial}\n")
    except Exception as e:
        info_text.insert(tk.END, f"[-] SOA record not found for {domain}: {e}\n")

    # Get NS records
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        for ns in ns_records:
            ns_ip = dns.resolver.resolve(ns.target, 'A')[0]
            info_text.insert(tk.END, f"[ns]       NS {ns.target} {ns_ip}\n")
    except Exception as e:
        info_text.insert(tk.END, f"[-] NS records not found for {domain}: {e}\n")

    # Get MX records
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        for mx in mx_records:
            mx_ip = dns.resolver.resolve(mx.exchange, 'A')[0]
            info_text.insert(tk.END, f"[mx]      MX {mx.exchange} {mx_ip}\n")
    except Exception as e:
        info_text.insert(tk.END, f"[-] MX records not found for {domain}: {e}\n")

    # Get A records
    try:
        a_records = dns.resolver.resolve(domain, 'A')
        for a in a_records:
            info_text.insert(tk.END, f"[a]        A {domain} {a.address}\n")
    except Exception as e:
        info_text.insert(tk.END, f"[-] A records not found for {domain}: {e}\n")

    # Get TXT records
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for txt in txt_records:
            info_text.insert(tk.END, f"[txt]      TXT {domain} {txt.strings}\n")
    except Exception as e:
        info_text.insert(tk.END, f"[-] TXT records not found for {domain}: {e}\n")

    # Get SRV records for common services
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0]
                info_text.insert(tk.END, f"[srv]     SRV {srv_domain} {srv.target} {srv_ip} {srv.port}\n")
        except Exception as e:
            info_text.insert(tk.END, "")

def execute_dns_operations():
    domain = url_entry.get()
    info_text.config(state=tk.NORMAL)
    info_text.delete(1.0, tk.END)
    get_dns_records(domain, info_text)
    info_text.config(state=tk.DISABLED)

# Configuração da janela principal
root = tk.Tk()
root.title("DNS Enumerator")
root.wm_state('zoomed')

# Entrada de URL
url_label = tk.Label(root, text="Digite o nome do website", font=("Arial", 12))
url_label.pack(pady=5)
url_entry = tk.Entry(root, width=30, font=("Arial", 12))
url_entry.pack(pady=5)

# Botão para executar as operações DNS
execute_button = tk.Button(root, text="Executar", font=("Arial", 12), command=execute_dns_operations, bg="#0bfc03")
execute_button.pack(pady=5)

# Área de texto para exibir as informações
info_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=45, font=("Arial", 12))
info_text.pack(pady=5)
info_text.config(state=tk.DISABLED)

# Iniciar o loop da interface gráfica
root.mainloop()
