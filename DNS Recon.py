import json
import tkinter as tk
from tkinter import messagebox
import dns.resolver
from urllib.parse import urlparse

def dns_research(domain):
    try:
        # Consulta de subdomínios
        subdomains = []
        answers = dns.resolver.resolve(domain, rdtype='NS')
        for answer in answers:
            subdomains.append(str(answer).rstrip('.'))
        
        # Consulta de registros TXT
        txt_records = []
        answers = dns.resolver.resolve(domain, rdtype='TXT')
        for answer in answers:
            txt_records.extend(answer.strings)
        
        result = {
            'Subdomains': subdomains,
            'TXT Records': [record.decode() for record in txt_records]
        }
        
        return json.dumps(result, indent=4)
        
    except dns.resolver.NXDOMAIN:
        messagebox.showinfo('Results', 'Invalid domain or URL.')
    except dns.exception.DNSException as e:
        messagebox.showerror('Error', str(e))

    return None

def perform_lookup():
    domain = entry.get().strip()
    if domain:
        parsed_url = urlparse(domain)
        if parsed_url.netloc:
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
        result_json = dns_research(domain)
        if result_json:
            result.delete(1.0, tk.END)  # Limpa o conteúdo anterior da caixa de texto
            result.insert(tk.END, result_json)
    else:
        messagebox.showinfo('Error', 'Please enter a domain or URL.')

# Configuração da janela principal
window = tk.Tk()
window.title('DNS Recon')
window.wm_state('zoomed')

# Rótulo e campo de entrada
label = tk.Label(window, text='URL or Domain')
label.pack()
entry = tk.Entry(window)
entry.pack()

# Botão de pesquisa
button = tk.Button(window, text='Lookup', command=perform_lookup)
button.pack()

# Caixa de texto para exibir os resultados
result = tk.Text(window, height=50, width=160)  # Definindo a altura e largura da caixa de texto
result.pack()

# Executar a janela principal
window.mainloop()
