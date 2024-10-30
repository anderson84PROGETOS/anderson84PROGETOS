from scapy.all import sniff, IP, TCP, UDP, Raw, wrpcap
from scapy.layers.http import HTTPRequest
from tkinter import *
from tkinter import scrolledtext, filedialog
import threading
import os
import re

capturing = False
packets = []
stop_event = threading.Event()
target_url = ""

def capture_packets():
    global capturing
    capturing = True
    try:
        sniff(filter="tcp port 80 or tcp port 443 or udp port 443", prn=process_packet, store=0, stop_filter=stop_capture_event)
    except Exception as e:
        append_text(f"Erro ao capturar pacotes: {str(e)}\n")

def stop_capture_event(packet):
    return stop_event.is_set()

def process_packet(packet):
    global packets
    packets.append(packet)

    if IP in packet:
        if packet.haslayer(HTTPRequest):
            handle_http_request(packet)
        elif packet.haslayer(TCP) and (packet[TCP].dport == 443 or packet[TCP].sport == 443):
            append_https_packet_info(packet)
        elif packet.haslayer(UDP) and packet[UDP].dport == 443:
            append_text("Pacote UDP na porta 443 capturado. (QUIC)\n")

def handle_http_request(packet):
    http_layer = packet[HTTPRequest]
    header = f"\n\nSite: {http_layer.Host.decode()}\n"
    header += "Cabeçalho da Página (HTTP)\n"
    header += f"[Method] {http_layer.Method.decode()}\n"
    header += f"[Path] {http_layer.Path.decode()}\n"

    payload = http_layer.payload.load.decode() if http_layer.payload else ""
    extract_credentials(header, payload)
    append_additional_info(packet, header)

def extract_credentials(header, payload):
    username_match = re.search(r'(?i)(username|login)=([^&]+)', payload)
    password_match = re.search(r'(?i)(password|pass)=([^&]+)', payload)

    if username_match:
        header += f"[Username] {username_match.group(2)}\n"
    if password_match:
        header += f"[Password] {password_match.group(2)}\n"

    packet_text.insert(END, header + "\n\n")
    packet_text.see(END)

def append_https_packet_info(packet):
    packet_info = f"\nHTTPS: {packet[IP].src:<20} {packet[IP].dst:<20}  {packet.summary():<20}\n\n"
    packet_text.insert(END, packet_info)
    packet_text.see(END)

def append_additional_info(packet, header):
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    header += f"[Source IP] {src_ip} -> [Destination IP] {dst_ip}\n"

def append_text(text):
    packet_text.insert(END, text)
    packet_text.see(END)

def start_capture():
    global target_url
    target_url = url_entry.get()
    if not capturing and target_url:
        stop_event.clear()
        append_text(f"Capturando pacotes para o host: {target_url}\n")
        thread = threading.Thread(target=capture_packets)
        thread.daemon = True
        thread.start()
        start_button.config(state=DISABLED)
        stop_button.config(state=NORMAL)

def stop_capture():
    global capturing
    capturing = False
    stop_event.set()
    start_button.config(state=NORMAL)
    stop_button.config(state=DISABLED)

def save_capture():
    file_path = filedialog.asksaveasfilename(defaultextension=".pcapng", filetypes=[("PCAPNG files", "*.pcapng")])
    if file_path:
        if packets:
            wrpcap(file_path, packets)
            append_text(f"\nCaptura salva em: {os.path.basename(file_path)}\n")
        else:
            append_text("Nenhum pacote capturado para salvar.\n")

# Interface Gráfica
root = Tk()
root.title("Capture http https Packets")
root.geometry("1250x950")
root.wm_state('zoomed')

Label(root, text="Insira a URL completa (ex: http://exemplo.com)", font=("Arial", 12)).pack()

url_entry = Entry(root, width=40, font=("Arial", 12))
url_entry.pack(pady=10)

Label(root, text="Pacotes HTTP/HTTPS capturados", font=("Arial", 12)).pack()

start_button = Button(root, text="Iniciar Captura", command=start_capture, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
start_button.pack(pady=10)

stop_button = Button(root, text="Parar Captura", command=stop_capture, state=DISABLED, font=("TkDefaultFont", 11, "bold"), bg='#29eb0c')
stop_button.pack(pady=10)

save_button = Button(root, text="Salvar Captura", command=save_capture, font=("TkDefaultFont", 11, "bold"), bg='#eb0c38')
save_button.pack(pady=10)

packet_text = scrolledtext.ScrolledText(root, width=145, height=35, font=("TkDefaultFont", 11, "bold"))
packet_text.pack(pady=10)

root.mainloop()
