import tkinter as tk
from tkinter import scrolledtext, filedialog
from scapy.all import sniff, IP, TCP, UDP, wrpcap
import socket
import re
from datetime import datetime
import threading

# Lista para armazenar os pacotes capturados
packets = []
capture_running = False  # Variável para controlar se a captura está rodando

def packet_callback(packet):
    if packet.haslayer(IP) and (packet.haslayer(TCP) or packet.haslayer(UDP)):
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        if packet.haslayer(TCP):
            sport = packet[TCP].sport
            dport = packet[TCP].dport
        elif packet.haslayer(UDP):
            sport = packet[UDP].sport
            dport = packet[UDP].dport

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = f"[{current_time}] {ip_src:<16} PORT:{sport:<15}  ==>    {ip_dst:<5}:{dport}\n"
        
        # Exibe o log na interface gráfica
        text_output.insert(tk.END, log)
        text_output.see(tk.END)

        # Adiciona o pacote à lista para salvar posteriormente
        packets.append(packet)

def capture_traffic():
    global capture_running
    website = entry.get()
    website = re.sub(r'^https?://', '', website)  # Remove o 'http://' ou 'https://'
    
    try:
        ip = socket.gethostbyname(website)  # Resolve o IP do website
        text_output.insert(tk.END, f"Capturando pacotes para: {website} ({ip})\n\n")
        text_output.see(tk.END)

        capture_running = True
        # Inicia a captura de pacotes
        sniff(filter="tcp port 80 or tcp port 443 or udp", prn=packet_callback, store=0, stop_filter=lambda x: not capture_running)

    except socket.gaierror as e:
        text_output.insert(tk.END, f"Erro ao resolver o nome do site: {e}\n")
        text_output.see(tk.END)

def stop_capture():
    global capture_running
    capture_running = False
    text_output.insert(tk.END, "\n\nCaptura interrompida.\n\n")
    text_output.see(tk.END)

def save_pcapng():
    # Abre o diálogo para salvar o arquivo .pcapng
    file_path = filedialog.asksaveasfilename(defaultextension=".pcapng", filetypes=[("PCAPNG files", "*.pcapng")])
    if file_path:
        if packets:
            wrpcap(file_path, packets)
            text_output.insert(tk.END, f"\nPacotes salvos em: {file_path}\n")
            text_output.see(tk.END)
        else:
            text_output.insert(tk.END, "\nNenhum pacote para salvar.\n")
            text_output.see(tk.END)

def start_capture():
    # Inicia a captura de pacotes em um thread separado para não travar a interface gráfica
    thread = threading.Thread(target=capture_traffic, daemon=True)
    thread.start()

# Criando a interface gráfica
root = tk.Tk()
root.title("Sniffer Network")
root.geometry("1230x900")

frame = tk.Frame(root)
frame.pack(pady=10)

label = tk.Label(frame, text="Digite a URL do website", font=("Arial", 11))
label.pack(pady=5)

entry = tk.Entry(frame, width=35, font=("Arial", 12))
entry.pack(padx=5, pady=5)

button_start = tk.Button(frame, text="Iniciar Captura", command=start_capture, font=("Arial", 11), bg="#0bfc03")
button_start.pack(pady=5)

button_stop = tk.Button(frame, text="STOP", command=stop_capture, font=("Arial", 11), bg="#fca503")
button_stop.pack(pady=5)

button_save = tk.Button(frame, text="Salvar como .pcapng", command=save_pcapng, font=("Arial", 11), bg="#03e3fc")
button_save.pack(pady=5)

text_output = scrolledtext.ScrolledText(root, width=120, height=38)
text_output.pack(pady=10)

root.mainloop()
