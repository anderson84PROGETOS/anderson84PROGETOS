import os
import warnings
import sys
import io

# ====================== SUPRESSÃO DE AVISOS ======================
os.environ["SCAPY_NO_WIRESHARK"] = "1"
warnings.filterwarnings("ignore")
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except:
    pass
sys.stderr = io.StringIO()

# ====================== IMPORTS ======================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from scapy.all import sniff, IP, TCP, Raw, IFACES
import threading
from datetime import datetime
import re
import time

# ====================== VARIÁVEIS ======================
detections = []
port_scan_tracker = {}
sniff_thread = None
stop_sniff = False

# Interface fixada (da sua foto)
FIXED_INTERFACE_DISPLAY = "Ethernet - Realtek PCIe GBE Family Controller"

def get_friendly_interfaces():
    friendly = []
    for iface in IFACES.values():
        name = getattr(iface, 'name', str(iface))
        desc = getattr(iface, 'description', '')
        display = f"{name} - {desc}" if desc else name
        friendly.append((display, name))
    return friendly

def log_message(ip, program, details):
    timestamp = datetime.now().strftime("%H:%M:%S")
    detections.append((timestamp, ip, program, details))
    
    for item in tree.get_children():
        tree.delete(item)
    for det in detections[-150:]:
        tree.insert("", "end", values=det)
    
    log_text.insert(tk.END, f"{timestamp} {ip} {details}\n")
    log_text.see(tk.END)

def detect_port_scan(src_ip, dport):
    now = time.time()
    if src_ip not in port_scan_tracker:
        port_scan_tracker[src_ip] = []
    port_scan_tracker[src_ip].append((dport, now))
    port_scan_tracker[src_ip] = [p for p in port_scan_tracker[src_ip] if now - p[1] < 8]
    
    if len(port_scan_tracker[src_ip]) >= 10:
        log_message(src_ip, "Nmap Port Scan", f"SYN -> {len(port_scan_tracker[src_ip])} portas")
        port_scan_tracker[src_ip] = []

def packet_callback(packet):
    if stop_sniff or IP not in packet:
        return
    src_ip = packet[IP].src

    if TCP in packet:
        dport = packet[TCP].dport
        flags = packet[TCP].flags
        
        if flags & 0x02:  # SYN
            detect_port_scan(src_ip, dport)
        
        if dport == 445 or packet[TCP].sport == 445:
            log_message(src_ip, "Windows SMB", "SMB Negotiate / Conexão")
        
        if dport in [5985, 5986] or packet[TCP].sport in [5985, 5986]:
            log_message(src_ip, "PowerShell WinRM", "Conexão WinRM detectada")

    if Raw in packet and TCP in packet:
        try:
            payload = bytes(packet[Raw]).decode(errors='ignore')
            if "user-agent:" in payload.lower():
                match = re.search(r'user-agent:\s*([^\r\n]+)', payload, re.I)
                if match:
                    ua = match.group(1)
                    prog = "curl" if "curl" in ua.lower() else "HTTP Request"
                    log_message(src_ip, prog, f"User-Agent: {ua[:70]}...")
        except:
            pass

def start_sniffing(iface):
    global stop_sniff
    stop_sniff = False
    try:
        log_message("SYSTEM", "INFO", f"Monitor iniciado na interface: {iface}\n")
        sniff(iface=iface, prn=packet_callback, store=False, filter="ip", stop_filter=lambda x: stop_sniff)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao capturar:\n{e}\n\nExecute como Administrador!")

def start_monitor():
    global sniff_thread
    selection = combo_interfaces.get()
    if not selection:
        messagebox.showwarning("Atenção", "Selecione uma interface!")
        return

    for disp, real_name in interface_list:
        if disp == selection:
            iface = real_name
            break
    else:
        iface = selection

    if sniff_thread and sniff_thread.is_alive():
        messagebox.showinfo("Info", "Já está monitorando!")
        return

    sniff_thread = threading.Thread(target=start_sniffing, args=(iface,), daemon=True)
    sniff_thread.start()
    status_label.config(text=f"Monitorando: {selection[:60]}...", fg="green")

def stop_monitor():
    global stop_sniff
    stop_sniff = True
    status_label.config(text="Monitor parado.", fg="red")

def save_results():
    if not detections:
        messagebox.showinfo("Info", "Não há resultados para salvar.")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        title="Salvar resultados como"
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=== DETECTOR DE REDE - RELATÓRIO ===\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*70 + "\n\n")
                f.write(f"{'Hora':<10} {'IP Origem':<20} {'Programa':<25} Detalhes\n")
                f.write("-"*90 + "\n")
                for det in detections:
                    f.write(f"{det[0]:<10} {det[1]:<20} {det[2]:<25} {det[3]}\n")
            messagebox.showinfo("Sucesso", f"Salvo em:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

# ====================== GUI ======================
root = tk.Tk()
root.title("Detector de Intrusão de Rede")
root.state("zoomed")

tk.Label(root, text="Detector de Intrusão de Rede", font=("Arial", 22, "bold")).pack(pady=10)

# Interface (fixada)
tk.Label(root, text="Interface de Rede", font=("Arial", 11)).pack(anchor="w", padx=10)

interface_list = get_friendly_interfaces()
display_names = [item[0] for item in interface_list]

combo_interfaces = ttk.Combobox(root, values=display_names, width=90, state="readonly")
combo_interfaces.pack(padx=20, pady=8, fill="x")

# Fixa a interface da foto
if FIXED_INTERFACE_DISPLAY in display_names:
    combo_interfaces.set(FIXED_INTERFACE_DISPLAY)
else:
    # Tenta encontrar algo parecido com Ethernet
    for disp in display_names:
        if "ethernet" in disp.lower() or "realtek" in disp.lower():
            combo_interfaces.set(disp)
            break
    else:
        if display_names:
            combo_interfaces.set(display_names[0])

# Tabela com Scrollbar
table_frame = tk.Frame(root)
table_frame.pack(padx=20, pady=10, fill="both", expand=True)

columns = ("Timestamp", "IP Origem", "Programa Detectado", "Detalhes")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=245, anchor="w")

tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=tree_scroll.set)
tree.pack(side=tk.LEFT, fill="both", expand=True)
tree_scroll.pack(side=tk.RIGHT, fill="y")

# Logs com Scrollbar
tk.Label(root, text="Logs em Tempo Real:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)

log_frame = tk.Frame(root)
log_frame.pack(padx=20, pady=5, fill="both", expand=True)

log_text = tk.Text(log_frame, height=14, font=("Consolas", 10))
log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_text.configure(yscrollcommand=log_scroll.set)
log_text.pack(side=tk.LEFT, fill="both", expand=True)
log_scroll.pack(side=tk.RIGHT, fill="y")

# Botões
btn_frame = tk.Frame(root)
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="▶ Iniciar Monitor", command=start_monitor, bg="#00aa00", fg="white", width=18).pack(side=tk.LEFT, padx=8)
tk.Button(btn_frame, text="⏹ Parar Monitor", command=stop_monitor, bg="#aa0000", fg="white", width=18).pack(side=tk.LEFT, padx=8)
tk.Button(btn_frame, text="💾 Salvar Resultados", command=save_results, bg="#0077cc", fg="white", width=20).pack(side=tk.LEFT, padx=8)
tk.Button(btn_frame, text="Limpar Tudo", command=lambda: (detections.clear(), log_text.delete(1.0, tk.END), [tree.delete(i) for i in tree.get_children()])).pack(side=tk.LEFT, padx=8)

status_label = tk.Label(root, text="Clique em Iniciar Monitor", fg="blue")
status_label.pack(pady=10)

tk.Label(root, text="Execute como Administrador!", fg="gray").pack()

root.mainloop()
