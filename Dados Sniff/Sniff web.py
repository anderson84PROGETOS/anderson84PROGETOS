import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from scapy.all import sniff, IP, TCP
import socket
import re
from threading import Thread, Event

# Variável global do evento para parar a captura
stop_event = Event()

def get_ip_from_url(url):
    """Resolve o endereço IP de um domínio."""
    try:
        domain = re.match(r'(https?://)?([^/]+)', url).group(2)
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except Exception as e:
        return None

def extract_http_data(payload):
    """Extrai cabeçalhos HTTP e dados (ex: username=test&password=test) de um payload."""
    try:
        # Decodificar o payload em texto
        payload_text = bytes(payload).decode(errors='ignore')
        if "HTTP" in payload_text or "GET" in payload_text or "POST" in payload_text:
            headers_body_split = payload_text.split("\r\n\r\n", 1)
            headers = headers_body_split[0]
            body = headers_body_split[1] if len(headers_body_split) > 1 else None

            # Filtrar parâmetros específicos como username, password, uname, pass, etc.
            if body:
                filtered_data = filter_body_data(body)
                return headers, filtered_data
            return headers, None
        return None, None
    except Exception:
        return None, None

def filter_body_data(body):
    """Filtra e extrai dados de interesse no corpo da requisição HTTP."""
    params = ['username', 'password', 'uname', 'pass', 'uid', 'passw']
    filtered_data = {}

    for param in params:
        match = re.search(rf"(?<={param}=)([^&]+)", body)
        if match:
            filtered_data[param] = match.group(0)

    return filtered_data

def packet_callback(packet):
    """Callback para processar pacotes capturados."""
    if stop_event.is_set():
        return  # Interrompe a captura se o evento de parada estiver ativado

    if IP in packet and TCP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        tcp_dport = packet[TCP].dport
        tcp_sport = packet[TCP].sport
        payload = packet[TCP].payload

        if tcp_dport in [80, 443] or tcp_sport in [80, 443]:
            headers, body_data = extract_http_data(payload)
            if headers:
                result = f"\n[INFO] Pacote HTTP capturado\n\nDe: {ip_src} Para: {ip_dst}\n\nCabeçalho HTTP\n\n{headers}"
                
                # Exibe os dados filtrados no corpo HTTP em vermelho
                if body_data:
                    result += "\n"
                    # Aplica a tag vermelha ao texto "Dados Filtrados do Corpo HTTP"
                    output_text.insert(tk.END, "\nDados Filtrados do Corpo HTTP\n\n", 'red')  # Texto em vermelho
                    for key, value in body_data.items():
                        # Aplica a cor vermelha ao exibir os dados
                        output_text.insert(tk.END, f"{key}: {value}\n", 'red')
                
                # Exibe o cabeçalho e o corpo na área de texto
                output_text.insert(tk.END, result + "\n\n")
                output_text.yview(tk.END)               

def capture_packets(ip):
    """Captura pacotes HTTP e exibe na interface gráfica."""
    # Timeout de 60 segundos para evitar travamento
    sniff(filter=f"host {ip}", prn=packet_callback, store=False, timeout=60)

def start_capture():
    """Inicia a captura de pacotes após resolver o IP."""
    url = url_entry.get()
    ip = get_ip_from_url(url)
    
    if ip:
        output_text.insert(tk.END, f"\n[INFO] Capturando pacotes HTTP do host: {ip}\n")
        output_text.yview(tk.END)
        capture_thread = Thread(target=capture_packets, args=(ip,))
        capture_thread.daemon = True  # Garantir que o thread seja fechado ao fechar a aplicação
        capture_thread.start()
    else:
        messagebox.showerror("Erro", "Não foi possível resolver o IP. Tente novamente.")

def on_close():
    """Método para fechar o aplicativo e interromper a captura de pacotes."""
    stop_event.set()  # Ativa o evento de parada para parar a captura de pacotes
    root.quit()  # Fecha a janela do Tkinter

# Criação da janela principal
root = tk.Tk()
root.title("Sniff web")
root.geometry("1200x900")

# Intercepta o evento de fechar a janela (clicar no "X")
root.protocol("WM_DELETE_WINDOW", on_close)

# Adicionando widgets
url_label = tk.Label(root, text="Digite nome do website ou a URL", font=("Arial", 12))
url_label.pack(pady=10)

url_entry = tk.Entry(root, width=50, font=("Arial", 12))
url_entry.pack(pady=10)

capture_button = tk.Button(root, text="Capturar Pacotes", font=("Arial", 12), bg="#00FF00", command=start_capture)
capture_button.pack(pady=10)

# Substituindo o Text por um ScrolledText
output_text = ScrolledText(root, wrap=tk.WORD, width=150, height=43, font=("Arial", 10))
output_text.pack(pady=10)

# Definindo a tag "red" para aplicar a cor vermelha
output_text.tag_config('red', foreground='red')

# Iniciando a interface gráfica
root.mainloop()
