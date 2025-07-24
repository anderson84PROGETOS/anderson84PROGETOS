import os
import sys
import warnings
import logging
import threading
import socket
import tkinter as tk
from tkinter import filedialog  # <- Adicionado para salvar arquivo

# Ignorar todos os warnings
warnings.filterwarnings("ignore")

# Configurar logging silencioso
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)

# Suprimir mensagens para evitar alertas do Wireshark e Scapy
def suppress_stderr():
    try:
        sys.stderr.flush()
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(2)
        os.dup2(devnull, 2)
        os.close(devnull)
        return old_stderr
    except Exception:
        return None

def restore_stderr(old_stderr):
    if old_stderr:
        try:
            sys.stderr.flush()
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
        except Exception:
            pass

# Suprimir mensagens no import do Scapy
old_stderr = suppress_stderr()
from scapy.all import sniff, IP, TCP, wrpcap
restore_stderr(old_stderr)

# Variáveis globais
visited_entries = set()
sniffing = False
stop_sniffing_flag = False
sniff_thread = None
root = None
listbox = None
scan_button = None
captured_packets = []  # <- Lista para armazenar pacotes capturados

def resolve_hostname_async(ip_port):
    def resolve():
        ip, port = ip_port.split(":")
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = "Domínio não Encontrado"
        update_hostname(ip_port, hostname)
    threading.Thread(target=resolve, daemon=True).start()

def update_hostname(ip_port, hostname):
    for i in range(listbox.size()):
        entry = listbox.get(i)
        if ip_port in entry and "Servidor:" not in entry:
            new_entry = f"{ip_port:<42} Servidor: {hostname}"
            root.after(0, lambda i=i, e=new_entry: listbox.delete(i) or listbox.insert(i, e))
            break

def process_packet(packet):
    if packet.haslayer(IP) and packet.haslayer(TCP):
        dst_ip = packet[IP].dst
        dst_port = packet[TCP].dport
        if dst_port in [80, 443]:
            ip_port = f"{dst_ip}:{dst_port}"
            if ip_port not in visited_entries:
                visited_entries.add(ip_port)
                display_text = f"{ip_port:<42} Resolvido: (aguarde...)"
                root.after(0, lambda: listbox.insert(tk.END, display_text))
                resolve_hostname_async(ip_port)
            captured_packets.append(packet)  # <- Adiciona pacote à lista

def sniff_packets():
    global sniffing, stop_sniffing_flag
    sniffing = True

    def stop_filter(packet):
        return stop_sniffing_flag

    sniff(filter="tcp port 80 or tcp port 443", prn=process_packet, store=False, stop_filter=stop_filter)
    sniffing = False
    scan_button.config(state=tk.NORMAL)

def on_start_scan():
    global sniffing, stop_sniffing_flag, sniff_thread
    if not sniffing:
        stop_sniffing_flag = False
        scan_button.config(state=tk.DISABLED)
        sniff_thread = threading.Thread(target=sniff_packets, daemon=True)
        sniff_thread.start()

def on_stop_scan():
    global stop_sniffing_flag
    if sniffing:
        stop_sniffing_flag = True

def on_save_file():
    if captured_packets:
        filepath = filedialog.asksaveasfilename(defaultextension=".pcapng", filetypes=[("PCAPNG files", "*.pcapng")])
        if filepath:
            wrpcap(filepath, captured_packets)
    else:
        print("Nenhum pacote capturado para salvar.")

def on_close():
    global stop_sniffing_flag
    stop_sniffing_flag = True
    if sniff_thread and sniff_thread.is_alive():
        sniff_thread.join(timeout=1)
    root.destroy()

def run_gui():
    global root, listbox, scan_button
    root = tk.Tk()
    root.title("Monitor de Conexões HTTP/HTTPS")
    root.geometry("1000x800")

    # Botões
    button_frame = tk.Frame(root)
    button_frame.pack(pady=(10, 5))

    scan_button = tk.Button(button_frame, text="Começar Scan", command=on_start_scan, bg="#16fc05", fg="black", height=2)
    scan_button.pack(side=tk.LEFT, padx=5)

    stop_button = tk.Button(button_frame, text="Parar", command=on_stop_scan, bg="#fc4305", fg="white", height=2)
    stop_button.pack(side=tk.LEFT, padx=5)

    save_button = tk.Button(button_frame, text="Salvar .pcapng", command=on_save_file, bg="#05a3fc", fg="white", height=2)
    save_button.pack(side=tk.LEFT, padx=5)

    close_button = tk.Button(button_frame, text="Fechar", command=on_close, bg="#555555", fg="white", height=2)
    close_button.pack(side=tk.LEFT, padx=5)

    # Lista
    list_frame = tk.Frame(root)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(list_frame, width=140, height=45, yscrollcommand=scrollbar.set)
    listbox.pack(padx=10, fill=tk.BOTH, expand=True)

    scrollbar.config(command=listbox.yview)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# Iniciar GUI
if __name__ == "__main__":
    run_gui()
