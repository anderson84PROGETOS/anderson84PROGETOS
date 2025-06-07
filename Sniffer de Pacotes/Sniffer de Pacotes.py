import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
from scapy.all import sniff, wrpcap
from scapy.layers.inet import IP

# Lista para armazenar pacotes
captured_packets = []
sniffing = False  # Controle de captura

def print_packet(pkt):
    if IP in pkt:
        proto = pkt[IP].proto
        proto_name = {1: "ICMP", 6: "TCP", 17: "UDP"}.get(proto, "OTHER")
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst

        if proto_name in ["TCP", "UDP"]:
            sport = pkt.sport
            dport = pkt.dport
            msg = f"[{proto_name:<7}] {src_ip:<20} {str(sport):<10} {dst_ip:<25} {str(dport):<10}"
        elif proto_name == "ICMP":
            msg = f"[{proto_name:<7}] {src_ip:<20} {'-':<10} {dst_ip:<25} {'-':<10}"
        else:
            msg = f"[{proto_name:<7}] {src_ip:<20} {'???':<10} {dst_ip:<25} {'???':<10}"

        packet_text.insert(tk.END, msg + "\n")
        packet_text.see(tk.END)
        captured_packets.append(pkt)

def start_sniffing():
    global sniffing
    sniffing = True
    packet_text.insert(tk.END, "\n>> Iniciando captura...\n\n")
    header = f"{'PROTO':<9} {'SRC IP':<20} {'PORT':<10} {'DST IP':<25} {'PORT':<10}"
    packet_text.insert(tk.END, header + "\n" + "-" * 85 + "\n")

    def sniff_packets():
        sniff(prn=print_packet, stop_filter=lambda x: not sniffing)

    threading.Thread(target=sniff_packets, daemon=True).start()

def stop_sniffing():
    global sniffing
    sniffing = False
    packet_text.insert(tk.END, "\n\n>> Captura finalizada. Escolha onde salvar os pacotes\n\n")

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pcap",
        filetypes=[("PCAP files", "*.pcap")],
        title="Salvar captura como"
    )

    if file_path:
        wrpcap(file_path, captured_packets)
        packet_text.insert(tk.END, f">> Pacotes salvos em: {file_path}\n")
    else:
        packet_text.insert(tk.END, ">> Salvamento cancelado pelo usuário.\n")

# Interface gráfica
root = tk.Tk()
root.title("Sniffer de Pacotes - TCP/UDP/ICMP")
root.geometry("1200x800")

frame = tk.Frame(root)
frame.pack(pady=10)

start_button = tk.Button(frame, text="Iniciar Captura", command=start_sniffing,
                         bg="green", fg="white", font=("Arial", 12, "bold"))
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(frame, text="Parar e Salvar", command=stop_sniffing,
                        bg="red", fg="white", font=("Arial", 12, "bold"))
stop_button.grid(row=0, column=1, padx=10)

packet_text = scrolledtext.ScrolledText(root, width=120, height=35,
                                        font=("TkDefaultFont", 11, "bold"))
packet_text.pack(pady=10)

root.mainloop()
