import tkinter as tk
from tkinter import scrolledtext, filedialog
from scapy.all import sniff
from scapy.layers.inet import IP, TCP
import socket
from urllib.parse import urlparse
import threading

# Variável global para controle de captura
capturing = False

# Função de callback para processar os pacotes capturados
def packet_callback(packet, text_area):
    if packet.haslayer(IP) and packet.haslayer(TCP):
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        sport = packet[TCP].sport
        dport = packet[TCP].dport

        # Exibir informações básicas dos pacotes capturados
        text_area.insert(tk.END, f"\n[+] {ip_src}:{sport}     ==>   {ip_dst}:{dport}\n")
        text_area.insert(tk.END, "=" * 35 + "\n\n")
        
        # Exibir os dados do pacote de forma legível (somente o payload em string)
        if packet[TCP].payload:
            payload = bytes(packet[TCP].payload).decode(errors='ignore').strip()  # Decodifica para string
            text_area.insert(tk.END, f"==== Payload ====\n\n{payload}\n\n")  # Exibe o payload como string

            # Adiciona uma nova linha se o payload parecer ser um cabeçalho HTTP
            if payload.startswith('GET') or payload.startswith('POST'):
                text_area.insert(tk.END, f"\n==== Cabeçalho HTTP =====\n\n{payload}\n\n")
        
        text_area.insert(tk.END, "=" * 35 + "\n")
        text_area.see(tk.END)

# Função para iniciar a captura de pacotes
def start_sniffing(website_entry, text_area, stop_event):
    global capturing
    capturing = True
    website_url = website_entry.get()

    # Extrair o nome do host da URL
    try:
        parsed_url = urlparse(website_url)
        host = parsed_url.netloc or parsed_url.path  # Pega o host da URL
        if not host:
            raise ValueError("URL inválida")
    except Exception as e:
        text_area.insert(tk.END, f"URL inválida: {e}\n")
        return

    # Resolve o IP do website
    try:
        ip_address = socket.gethostbyname(host)
        text_area.insert(tk.END, f"Website: {host}   IP: {ip_address}\n")
    except socket.gaierror:
        text_area.insert(tk.END, f"Erro: não foi possível resolver a URL '{host}'\n")
        return

    filter_str = f"host {ip_address}"
    text_area.insert(tk.END, f"\n\nCapturando Pacotes Para o IP: {ip_address}\n\n")

    # Função para verificar o estado de captura e parar quando solicitado
    def sniff_packets():
        while not stop_event.is_set():
            sniff(filter=filter_str, prn=lambda packet: packet_callback(packet, text_area), store=0, count=1)

    # Iniciar a captura de pacotes em uma thread separada
    sniff_thread = threading.Thread(target=sniff_packets)
    sniff_thread.daemon = True  # Permitir que o thread feche junto com o programa
    sniff_thread.start()

# Função para parar a captura de pacotes
def stop_sniffing(stop_event, text_area):
    global capturing
    if capturing:
        stop_event.set()
        text_area.insert(tk.END, "\nCaptura de pacotes interrompida.\n")
        capturing = False

# Função para salvar a captura em um arquivo .txt
def save_capture(text_area):
    content = text_area.get("1.0", tk.END)  # Pega todo o conteúdo da área de texto
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(content)

# Função principal para criar a interface
def create_gui():
    # Configurações da janela principal
    root = tk.Tk()
    root.title("Packet Sniffer")
    root.geometry("1200x1000")

    # Variável para parar a captura de pacotes
    stop_event = threading.Event()

    # Campo de entrada para a URL do website
    website_label = tk.Label(root, text="Digite a URL do website", font=("TkDefaultFont", 10, "bold"))
    website_label.pack(pady=5)

    website_entry = tk.Entry(root, width=40, font=("TkDefaultFont", 10, "bold"))
    website_entry.pack(pady=5)

    # Botão para iniciar a captura de pacotes
    sniff_button = tk.Button(root, text="Iniciar Captura", command=lambda: start_sniffing(website_entry, text_area, stop_event), 
                             font=("TkDefaultFont", 10, "bold"), bg='#07f5c1')
    sniff_button.pack(pady=5)

    # Botão para parar a captura de pacotes
    stop_button = tk.Button(root, text="Parar Captura", command=lambda: stop_sniffing(stop_event, text_area), 
                            font=("TkDefaultFont", 10, "bold"), bg='#a503fc')
    stop_button.pack(pady=5)

    # Botão para salvar a captura
    save_button = tk.Button(root, text="Salvar Captura", command=lambda: save_capture(text_area), 
                            font=("TkDefaultFont", 10, "bold"), bg='#add8e6')
    save_button.pack(pady=5)

    # Área de texto para exibir as informações dos pacotes capturados
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=140, height=40, font=("TkDefaultFont", 11, "bold"))
    text_area.pack(pady=10)    

    # Rodar a interface
    root.mainloop()

if __name__ == "__main__":
    create_gui()
