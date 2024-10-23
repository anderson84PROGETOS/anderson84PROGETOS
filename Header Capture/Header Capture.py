from scapy.all import sniff, IP, UDP, TCP, wrpcap
from scapy.layers.http import HTTPRequest
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog
import threading
import re
import os

# Variável global para controlar a captura
capturing = False
packets = []
stop_event = threading.Event()  # Evento para parar a captura

# Função para capturar pacotes
def capture_packets():
    global capturing
    capturing = True
    try:
        # Captura pacotes HTTP (TCP), HTTPS (TCP) e pacotes UDP na porta 443 (QUIC)
        sniff(filter="tcp port 80 or tcp port 443 or udp port 443", prn=process_packet, store=0, stop_filter=stop_capture_event)
    except Exception as e:
        packet_text.insert(END, f"Erro ao capturar pacotes: {str(e)}\n")
        packet_text.see(END)

# Função que define quando parar a captura
def stop_capture_event(packet):
    return stop_event.is_set()

# Função para processar pacotes
def process_packet(packet):
    global packets
    packets.append(packet)
    
    if IP in packet:
        if packet.haslayer(HTTPRequest):
            http_layer = packet[HTTPRequest]
            # Monta o cabeçalho HTTP em um formato organizado
            header = f"\n\nSite: {http_layer.Host.decode()}\n"
            header += "Cabeçalho da Página (HTTP)\n"
            header += f"[Method] {http_layer.Method.decode()}\n"
            header += f"[Path] {http_layer.Path.decode()}\n"
            
            # Extraindo o conteúdo do payload, se disponível
            payload = http_layer.payload.load.decode() if http_layer.payload else ""
            
            # Busca por campos de Username e Password
            username_match = re.search(r'(?i)(username|login)=([^&]+)', payload)
            password_match = re.search(r'(?i)(password|pass)=([^&]+)', payload)

            if username_match:
                header += f"[Username] {username_match.group(2)}\n"
            if password_match:
                header += f"[Password] {password_match.group(2)}\n"
            
            # Adiciona cabeçalhos adicionais se disponíveis
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            header += f"[Source IP] {src_ip} -> [Destination IP] {dst_ip}\n"
            
            # Adiciona o cabeçalho à caixa de texto
            packet_text.insert(END, header + "\n\n")
            packet_text.see(END)  # Rola para baixo para ver os novos resultados

        elif packet.haslayer(TCP) and (packet[TCP].dport == 443 or packet[TCP].sport == 443):
            # Captura pacotes HTTPS
            packet_info = f"\nHTTPS: {packet[IP].src:<20} {packet[IP].dst:<20}  {packet.summary():<20}\n\n"
            packet_text.insert(END, packet_info)  # Exibe na GUI

        elif packet.haslayer(UDP) and packet[UDP].dport == 443:
            # Aqui você pode adicionar lógica para lidar com pacotes QUIC
            packet_text.insert(END, "Pacote UDP na porta 443 capturado. (QUIC)\n")
            packet_text.see(END)

# Função para iniciar a captura em uma thread
def start_capture():
    if not capturing:
        stop_event.clear()  # Limpa o evento de parada
        thread = threading.Thread(target=capture_packets)
        thread.daemon = True  # Permite que o thread feche quando a janela é fechada
        thread.start()
        start_button.config(state=DISABLED)
        stop_button.config(state=NORMAL)

# Função para parar a captura de pacotes
def stop_capture():
    global capturing
    capturing = False
    stop_event.set()  # Sinaliza para parar a captura
    start_button.config(state=NORMAL)
    stop_button.config(state=DISABLED)

# Função para salvar a captura em um arquivo PCAPNG
def save_capture():
    file_path = filedialog.asksaveasfilename(defaultextension=".pcapng", filetypes=[("PCAPNG files", "*.pcapng")])
    if file_path:
        if packets:
            wrpcap(file_path, packets)
            packet_text.insert(END, f"\nCaptura salva em: {os.path.basename(file_path)}\n")
            packet_text.see(END)
        else:
            packet_text.insert(END, "Nenhum pacote capturado para salvar.\n")
            packet_text.see(END)

# Criando a interface gráfica
root = Tk()
root.title("Captura de Pacotes HTTP/HTTPS/HTTP/3")
root.geometry("1250x950")
root.wm_state('zoomed')

# Label
label = Label(root, text="Pacotes HTTP/HTTPS/HTTP/3 capturados", font=("Arial", 12))
label.pack()

# Botão para iniciar a captura com formatação
start_button = Button(root, text="Iniciar Captura", command=start_capture,
                      font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
start_button.pack(pady=10)

# Botão para parar a captura
stop_button = Button(root, text="Parar Captura", command=stop_capture, state=DISABLED,
                     font=("TkDefaultFont", 11, "bold"), bg='#29eb0c')
stop_button.pack(pady=10)

# Botão para salvar os pacotes capturados em PCAPNG
save_button = Button(root, text="Salvar Captura", command=save_capture,
                     font=("TkDefaultFont", 11, "bold"), bg='#eb0c38')
save_button.pack(pady=10)

# Campo de texto com barra de rolagem para exibir pacotes
packet_text = scrolledtext.ScrolledText(root, width=145, height=45)
packet_text.pack(pady=10)

# Inicia a interface gráfica
root.mainloop()
