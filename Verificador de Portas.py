import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import re
from tkinter.ttk import Progressbar

def get_host_from_url(url):
    match = re.match(r'https?://([a-zA-Z0-9.-]+)', url)
    if match:
        return match.group(1)
    else:
        return url

def check_port(url, port):
    host = get_host_from_url(url)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        ip_address = socket.gethostbyname(host)
        sock.connect((ip_address, port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()

def check_ports(url, progress_var):
    open_ports = []
    total_ports = len(ports)

    for i, (port, description) in enumerate(ports.items()):
        if check_port(url, port):
            open_ports.append((f'A porta {port} ({description}) está aberta em {url}', 'red'))
        else:
            open_ports.append((f'A porta {port} ({description}) está fechada em {url}', 'black'))

        progress_percent = min(1, int((i + 1) / total_ports * 100))
        progress_var.set(progress_percent)
        window.update_idletasks()

    return open_ports

def on_check_ports():
    url = site_entry.get()
    if not url:
        messagebox.showinfo("Erro", "Por favor, insira um URL.")
        return

    progress_var.set(0)
    total_ports = len(ports)
    progress_bar['maximum'] = total_ports

    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)

    for line, color in check_ports(url, progress_var):
        result_text.insert(tk.END, line + '\n\n\n', color)

    # Set the progress to 100 after the loop completes
    progress_var.set(100)
    window.update_idletasks()

    result_text.config(state=tk.DISABLED)

# Configuração da janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Verificador de Portas")

# Elementos da interface
site_label = tk.Label(window, text="Digite a URL do Website ou nome do site", font=("Arial", 12))
site_label.pack(pady=5)

site_entry = tk.Entry(window, width=30, font=("Arial", 12))
site_entry.pack(pady=10)

check_button = tk.Button(window, text="Verificar Portas", command=on_check_ports, background="#11e7f2")
check_button.pack(pady=10)

# Adding a progress bar
progress_var = tk.IntVar()
progress_bar = Progressbar(window, orient=tk.HORIZONTAL, length=200, mode='determinate', variable=progress_var)
progress_bar.pack(pady=10)

result_text = scrolledtext.ScrolledText(window, width=130, height=43, font=("Arial", 12))
result_text.pack(pady=10)

# Dicionário de portas
ports = {
    21: 'FTP - Servidor de arquivos',
    22: 'SSH - Terminal remoto criptografado',
    23: 'Telnet - Terminal remoto',
    25: 'SMTP - Serviço de e-mails',
    53: 'DNS - Servidor DNS',
    80: 'HTTP - Servidor Web',
    110: 'POP3 - Serviço de acesso a e-mails',
    135: 'Microsoft/NetBIOS - Serviços de descoberta de rede Microsoft',
    139: 'Microsoft/NetBIOS - Serviços de descoberta de rede Microsoft',
    143: 'IMAP - Serviço de sincronização de e-mails',
    443: 'HTTPS - Servidor Web com criptografia - SSL',
    3306: 'MySQL - Servidor de Banco de Dados MySQL',
    3389: 'RDP - Área de trabalho remota Windows',
    # Adicione outras portas conforme necessário
}

# Adicionando as tags para colorir o texto
result_text.tag_config('red', foreground='red')
result_text.tag_config('black', foreground='black')

# Inicia o loop principal da interface gráfica
window.mainloop()
