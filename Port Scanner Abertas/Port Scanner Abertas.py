import socket
import ssl
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import urllib3
import threading

# Suprimir os avisos de InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cabeçalhos personalizados para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para verificar banner e SSL
def check_banner(server, port, output_text):
    sock = None
    try:
        sock = socket.create_connection((server, port), timeout=5)

        if port == 443:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=server) as ssock:
                cert = ssock.getpeercert()
                output_text.insert(tk.END, f"\nPorta {port} aberta - SSL Certificado válido para: {server}\n")
                # Fazer uma requisição HTTP para obter o cabeçalho completo
                ssock.sendall(b"GET / HTTP/1.1\r\nHost: " + server.encode() + b"\r\n" + b"\r\n")
                response = ssock.recv(4096).decode('latin-1', errors='ignore')
                header, _, _ = response.partition("\r\n\r\n")  # Separar cabeçalho do corpo
                output_text.insert(tk.END, f"\nCabeçalho HTTP:\n{header}\n")  # Exibir apenas o cabeçalho
        elif port == 80:
            sock.sendall(b"GET / HTTP/1.1\r\nHost: " + server.encode() + b"\r\n" + b"\r\n")
            response = sock.recv(4096).decode('latin-1', errors='ignore')
            header, _, _ = response.partition("\r\n\r\n")  # Separar cabeçalho do corpo
            output_text.insert(tk.END, f"\nPorta {port} aberta em: {server}\n")
            output_text.insert(tk.END, f"\nCabeçalho HTTP\n\n{header}\n")  # Exibir apenas o cabeçalho
        else:
            banner = sock.recv(1024).decode('latin-1', errors='ignore').strip()
            if banner:
                output_text.insert(tk.END, f"\nPorta {port} aberta em: {server}\n\nBanner: {banner}\n")
                output_text.insert(tk.END, f"========================================================")
            else:
                output_text.insert(tk.END, f"\nPorta {port} aberta em: {server} (sem banner)\n")
    except (ConnectionRefusedError, socket.timeout):  # Ignorar erros de conexão e timeout
        pass  # Não faz nada, apenas ignora
    except Exception as e:
        output_text.insert(tk.END, f"\nErro inesperado na porta {port}: {e}\n")  # Exibir erro se necessário
    finally:
        if sock:
            sock.close()

# Função de monitoramento de portas
def monitor(server, start_port, end_port, output_text, progress_bar):
    total_ports = end_port - start_port + 1
    progress_bar['maximum'] = total_ports

    for port in range(start_port, end_port + 1):
        check_banner(server, port, output_text)
        progress_bar['value'] += 1
        window.update_idletasks()

    # Reativar o botão quando o escaneamento for finalizado
    start_button.config(state=tk.NORMAL)
    messagebox.showinfo("Scan Completo", "O escaneamento foi finalizado.")

# Função para iniciar o escaneamento
def start_scan():
    server = server_entry.get()
    port_range = port_entry.get()

    try:
        # Verificar se é um único número ou intervalo
        if '-' in port_range:
            start_port, end_port = map(int, port_range.split('-'))
        else:
            start_port = end_port = int(port_range)  # Se for um único número, ambos serão iguais
    except ValueError:
        messagebox.showerror("Erro", "Formato de porta inválido. Use o formato 'início-fim' ou um número único (ex: 80 ou 1-65535).")
        return

    output_text.delete(1.0, tk.END)  # Limpar a área de texto
    progress_bar['value'] = 0  # Resetar a barra de progresso

    # Desativar o botão para impedir novos escaneamentos enquanto um está em progresso
    start_button.config(state=tk.DISABLED)

    # Executar o escaneamento em uma thread separada para não travar a interface
    scan_thread = threading.Thread(target=monitor, args=(server, start_port, end_port, output_text, progress_bar))
    scan_thread.start()

# Interface gráfica com Tkinter
window = tk.Tk()
window.title("Port Scanner Abertas")
window.wm_state('zoomed') 

# Configura a janela para ajustar o layout centralizado
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

# Frame principal que contém todos os widgets
main_frame = tk.Frame(window)
main_frame.grid()

# Configurar o frame para ajustar os widgets
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(0, weight=1)

# Elementos da interface
server_label = tk.Label(main_frame, text="Nome do Website ou IP", font=("Arial", 12, "bold"))
server_label.grid(pady=5)

server_entry = tk.Entry(main_frame, width=30)
server_entry.grid(pady=5)

port_label = tk.Label(main_frame, text="Porta ou intervalo de portas (ex: 80 ou 1-65535)", font=("Arial", 12, "bold"))
port_label.grid(pady=5)

port_entry = tk.Entry(main_frame, width=30)
port_entry.grid(pady=5)

# Botão para iniciar o escaneamento
start_button = tk.Button(main_frame, text="Iniciar Escaneamento", command=start_scan, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
start_button.grid(pady=5)

# Barra de progresso usando ttk.Progressbar
progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=260, mode='determinate')
progress_bar.grid(pady=5)

# Mensagem de status após escaneamento
mensagem_label = tk.Label(main_frame, text="", font=("Arial", 12, "bold"))
mensagem_label.grid(pady=5)

# Área de texto para exibir os resultados
output_text = scrolledtext.ScrolledText(main_frame, width=120, height=35, font=("Arial", 12, "bold"))
output_text.grid(pady=5)

window.mainloop()
