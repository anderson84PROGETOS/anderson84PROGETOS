import tkinter as tk
from tkinter import ttk, scrolledtext
import dns.resolver

def get_dns_info():
    domain = domain_entry.get()
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)

    try:
        answers = dns.resolver.resolve(domain, 'A')
        display_dns_info("A  .Mapeia um nome de domínio para um endereço IPv4. ", answers)
    except dns.exception.DNSException:
        display_dns_info("A", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'AAAA')
        display_dns_info("AAAA  .Mapeia um nome de domínio para um endereço IPv6. ", answers)
    except dns.exception.DNSException:
        display_dns_info("AAAA", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        display_dns_info("NS  .Define os servidores de nomes autorizados para um domínio.", answers)
    except dns.exception.DNSException:
        display_dns_info("NS", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'PTR')
        display_dns_info("PTR  .É usado para fazer uma pesquisa inversa, mapeando um endereço IP para um nome de domínio.", answers)
    except dns.exception.DNSException:
        display_dns_info("PTR", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        display_dns_info("TXT  .Armazena texto associado a um nome de domínio, frequentemente usado para informações de autenticação e políticas de segurança.", answers)
    except dns.exception.DNSException:
        display_dns_info("TXT", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'MX')
        display_dns_info("MX  .Define os servidores de email que recebem mensagens de email para um domínio.", answers)
    except dns.exception.DNSException:
        display_dns_info("MX", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'SOA')
        display_dns_info("SOA  .Contém informações sobre a zona de autoridade de um domínio, como o endereço de email do administrador.", answers)
    except dns.exception.DNSException:
        display_dns_info("SOA", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'DS')
        display_dns_info("DS  .É usado em registros DNSSEC para prover informações de segurança sobre a zona.", answers)
    except dns.exception.DNSException:
        display_dns_info("DS", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'SRV')
        display_dns_info("SRV  .Define serviços disponíveis em um domínio, frequentemente usados para localizar servidores de chat, voip.", answers)
    except dns.exception.DNSException:
        display_dns_info("SRV", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'NSEC3')
        display_dns_info("NSEC3  .É um registro de negação de autenticação usado para reforçar a segurança no DNSSEC.", answers)
    except dns.exception.DNSException:
        display_dns_info("NSEC3", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'HINFO')
        display_dns_info("HINFO  .Armazena informações sobre o tipo de hardware e sistema operacional de um host.", answers)
    except dns.exception.DNSException:
        display_dns_info("HINFO", "N/A")

    try:
        answers = dns.resolver.resolve(domain, 'CNAME')
        display_dns_info("CNAME  .Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias.", answers)
    except dns.exception.DNSException:
        display_dns_info("CNAME", "N/A")

    result_text.config(state=tk.DISABLED)

def display_dns_info(record_type, answers):
    result_text.insert(tk.END, f"{record_type}\n")
    result_text.insert(tk.END, "-" * 40 + "\n")

    if answers != "N/A":
        for answer in answers:
            result_text.insert(tk.END, str(answer) + "\n")
    else:
        result_text.insert(tk.END, "N/A\n")

    result_text.insert(tk.END, "\n" + "-" * 40 + "\n\n")

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("DNS Information Lookup")

# Aba do Domínio
domain_frame = ttk.Frame(root, padding="10")
domain_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

domain_label = ttk.Label(domain_frame, text="Digite o domínio:", font=("Arial", 12))
domain_label.grid(column=0, row=0, sticky=tk.W)

domain_entry = ttk.Entry(domain_frame, width=40, font=("Arial", 12))
domain_entry.grid(column=1, row=0, sticky=tk.W)

domain_button = tk.Button(domain_frame, text="Obter Informações DNS", font=("Arial", 12), command=get_dns_info, bg="#00FFFF")                                        
domain_button.grid(column=2, row=0, sticky=tk.W, padx=(12, 10), pady=10)
# Resultado
result_frame = ttk.Frame(root, padding="10")
result_frame.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=138, height=47, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

# Inicializa a interface gráfica
root.mainloop()
