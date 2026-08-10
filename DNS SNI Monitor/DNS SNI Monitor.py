# IMPORTANT: Use at your own risk. Requires administrator/root privileges.
# Install: pip install scapy
# Windows: also install Npcap[](https://npcap.com)

import warnings
import logging
import sys
import os

# ====================== SILENCIAR TUDO NO CMD ======================
warnings.filterwarnings("ignore")
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
logging.getLogger("scapy.loading").setLevel(logging.ERROR)
logging.getLogger("scapy").setLevel(logging.ERROR)

# Redireciona saída padrão (mata o "True" e qualquer outra mensagem)
sys.stdout = open(os.devnull, "w")
sys.stderr = open(os.devnull, "w")

# ====================== IMPORTS ======================
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
import platform

from scapy.all import sniff, TCP, Raw, conf
from scapy.layers.dns import DNSQR

conf.verb = 0

# ====================== CONFIGURAÇÃO ======================
DNS_LOG = "dns_log.txt"
SNI_LOG = "sni_log.txt"

stop_event = threading.Event()
seen = set()
dns_thread = None
sni_thread = None

# ====================== FUNÇÕES DE PROCESSAMENTO ======================
def process_dns(packet):
    if stop_event.is_set():
        return True
    if packet.haslayer(DNSQR):
        try:
            domain = packet[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
            now_minute = datetime.now().strftime("%d/%m/%Y %H:%M")
            unique_key = f"{now_minute}:{domain}"
            if unique_key in seen:
                return
            seen.add(unique_key)

            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            log_entry = f"[DNS] [{timestamp}] {domain}"
            log_message(log_entry, tag="dns")

            if var_save.get():
                with open(DNS_LOG, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
        except Exception as e:
            log_message(f"[DNS Error] {e}", tag="error")

def extract_sni(payload):
    try:
        data = bytes(payload)
        if len(data) < 5 or data[0] != 0x16:
            return None

        pos = 43
        if pos >= len(data):
            return None

        session_id_length = data[pos]
        pos += 1 + session_id_length
        if pos + 2 > len(data):
            return None

        cipher_suites_length = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2 + cipher_suites_length
        if pos >= len(data):
            return None

        compression_methods_length = data[pos]
        pos += 1 + compression_methods_length
        if pos + 2 > len(data):
            return None

        extensions_length = int.from_bytes(data[pos:pos+2], 'big')
        pos += 2
        end = min(pos + extensions_length, len(data))

        while pos + 4 <= end:
            ext_type = int.from_bytes(data[pos:pos+2], 'big')
            ext_length = int.from_bytes(data[pos+2:pos+4], 'big')
            pos += 4
            if pos + ext_length > len(data):
                break

            if ext_type == 0x0000:  # SNI
                sni_data = data[pos:pos+ext_length]
                if len(sni_data) < 5:
                    return None
                server_name_length = int.from_bytes(sni_data[3:5], 'big')
                server_name = sni_data[5:5+server_name_length]
                return server_name.decode(errors="ignore")
            pos += ext_length
    except Exception:
        return None
    return None

def process_sni(packet):
    if stop_event.is_set():
        return True
    if packet.haslayer(TCP) and packet.haslayer(Raw):
        sni = extract_sni(packet[Raw].load)
        if sni:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            log_entry = f"[SNI] [{timestamp}] {sni}"
            log_message(log_entry, tag="sni")

            if var_save.get():
                with open(SNI_LOG, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")

# ====================== THREADS ======================
def start_dns_sniff():
    try:
        sniff(filter="udp port 53", prn=process_dns, store=False,
              stop_filter=lambda x: stop_event.is_set())
    except Exception as e:
        log_message(f"[DNS] Erro ao iniciar: {e}", tag="error")

def start_sni_sniff():
    try:
        sniff(filter="tcp port 443", prn=process_sni, store=False,
              stop_filter=lambda x: stop_event.is_set())
    except Exception as e:
        log_message(f"[SNI] Erro ao iniciar: {e}", tag="error")

# ====================== INTERFACE GRÁFICA ======================
def log_message(msg, tag="info"):
    text_area.configure(state="normal")
    text_area.insert(tk.END, msg + "\n", tag)
    text_area.see(tk.END)
    text_area.configure(state="disabled")

def clear_log():
    """Limpa completamente a área de resultados"""
    text_area.configure(state="normal")
    text_area.delete("1.0", tk.END)
    text_area.configure(state="disabled")
    # Opcional: limpa também o set de domínios já vistos
    seen.clear()

def start_monitoring():
    global dns_thread, sni_thread

    if not var_dns.get() and not var_sni.get():
        messagebox.showwarning("Aviso", "Selecione pelo menos uma opção (DNS ou SNI).")
        return

    stop_event.clear()
    seen.clear()

    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    chk_dns.config(state="disabled")
    chk_sni.config(state="disabled")
    chk_save.config(state="disabled")

    log_message("=" * 50, tag="info")
    log_message(f"Monitor iniciado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", tag="info")
    log_message(f"Sistema: {platform.system()} {platform.release()}", tag="info")
    if var_save.get():
        log_message("→ Salvando logs em arquivo: ATIVADO", tag="info")
    else:
        log_message("→ Salvando logs em arquivo: DESATIVADO", tag="info")
    log_message("=" * 50, tag="info")

    if var_dns.get():
        log_message("→ Monitor DNS ativado", tag="dns")
        dns_thread = threading.Thread(target=start_dns_sniff, daemon=True)
        dns_thread.start()

    if var_sni.get():
        log_message("→ Monitor SNI (TLS) ativado", tag="sni")
        sni_thread = threading.Thread(target=start_sni_sniff, daemon=True)
        sni_thread.start()

    log_message("")

def stop_monitoring():
    stop_event.set()
    log_message("\n\n[!] Parando monitoramento... (pode demorar alguns segundos)", tag="error")
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")
    chk_dns.config(state="normal")
    chk_sni.config(state="normal")
    chk_save.config(state="normal")
    log_message("\n[✓] Monitoramento parado.\n", tag="info")

def show_help():
    help_win = tk.Toplevel(root)
    help_win.title("HELP - Como Instalar")
    help_win.geometry("800x760")
    help_win.configure(bg="#000000")
    help_win.resizable(False, False)

    # Centralizar a janela
    help_win.update_idletasks()
    x = (help_win.winfo_screenwidth() // 2) - (700 // 2)
    y = (help_win.winfo_screenheight() // 2) - (520 // 2)
    help_win.geometry(f"+{x}+{y}")

    frame = ttk.Frame(help_win, padding=15)
    frame.pack(fill="both", expand=True)

    title = ttk.Label(frame, text=">>> COMO INSTALAR <<<", style="Header.TLabel")
    title.pack(anchor="w", pady=(0, 10))

    help_text = scrolledtext.ScrolledText(
        frame,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#000000",
        fg="#00FF00",
        insertbackground="#00FF00",
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground="#00FF00",
        highlightcolor="#00FF00",
        height=20
    )
    help_text.pack(fill="both", expand=True)

    help_content = """[!] ATENÇÃO
Este programa precisa ser executado como Administrador (Windows)
ou root (Linux/Kali).

=======================================================
[ WINDOWS 10 / 11 ]
=======================================================

1. Instale o Python:
   https://www.python.org/downloads/
   (marque a opção "Add Python to PATH")

2. Instale o Npcap:
   https://npcap.com/#download
   (marque "Install Npcap in WinPcap API-compatible Mode")

3. Abra o CMD e digite:
   pip install scapy

4. Execute este script como Administrador
   (botão direito → Executar como administrador)

=======================================================
[ KALI LINUX ]
=======================================================

1. Atualize o sistema:
   sudo apt update && sudo apt upgrade -y

2. Instale as dependências:
   sudo apt install python3 python3-pip python3-scapy -y

3. Execute o script com root:
   sudo python3 seu_script.py

=======================================================
"""
    help_text.insert(tk.END, help_content)
    help_text.configure(state="disabled")

    btn_close = ttk.Button(frame, text="FECHAR", command=help_win.destroy)
    btn_close.pack(pady=10)

def on_closing():
    stop_event.set()
    root.destroy()

# ====================== JANELA PRINCIPAL ======================
root = tk.Tk()
root.title("DNS + SNI Monitor // HACKER MODE")
root.geometry("950x760")
root.configure(bg="#000000")

if platform.system() == "Windows":
    root.state("zoomed")
else:
    try:
        root.attributes("-zoomed", True)
    except tk.TclError:
        pass

root.minsize(650, 420)

# ====================== ESTILO HACKER VERDE ======================
style = ttk.Style()
style.theme_use("clam")

BG_BLACK = "#000000"
BG_DARK = "#0a0a0a"
FG_GREEN = "#00FF00"
FG_BRIGHT = "#33FF33"

style.configure(".", background=BG_BLACK, foreground=FG_GREEN, font=("Consolas", 10))
style.configure("TFrame", background=BG_BLACK)
style.configure("TLabel", background=BG_BLACK, foreground=FG_GREEN, font=("Consolas", 10))
style.configure("TCheckbutton", background=BG_BLACK, foreground=FG_GREEN, font=("Consolas", 10))
style.map("TCheckbutton",
          background=[("active", BG_DARK)],
          foreground=[("active", FG_BRIGHT)])

style.configure("TButton",
                background=BG_DARK,
                foreground=FG_GREEN,
                font=("Consolas", 11, "bold"),
                borderwidth=1,
                relief="flat")
style.map("TButton",
          background=[("active", "#003300"), ("disabled", "#111111")],
          foreground=[("active", FG_BRIGHT), ("disabled", "#005500")])

style.configure("Header.TLabel",
                background=BG_BLACK,
                foreground=FG_BRIGHT,
                font=("Consolas", 12, "bold"))

# Frame superior
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill="x")

ttk.Label(frame_top, text=">>> ESCOLHA O QUE DESEJA MONITORAR <<<", style="Header.TLabel").pack(anchor="w")

var_dns = tk.BooleanVar(value=True)
var_sni = tk.BooleanVar(value=True)
var_save = tk.BooleanVar(value=True)

chk_dns = ttk.Checkbutton(frame_top, text="[+] Monitor DNS (porta 53)", variable=var_dns)
chk_dns.pack(anchor="w", pady=2)

chk_sni = ttk.Checkbutton(frame_top, text="[+] Monitor SNI / TLS (porta 443)", variable=var_sni)
chk_sni.pack(anchor="w", pady=2)

chk_save = ttk.Checkbutton(frame_top, text="[+] Salvar logs em arquivo (dns_log.txt / sni_log.txt)", variable=var_save)
chk_save.pack(anchor="w", pady=2)

# Botões
frame_buttons = ttk.Frame(root, padding=10)
frame_buttons.pack(fill="x")

btn_start = ttk.Button(frame_buttons, text="▶ INICIAR", command=start_monitoring)
btn_start.pack(side="left", padx=5)

btn_stop = ttk.Button(frame_buttons, text="■ PARAR", command=stop_monitoring, state="disabled")
btn_stop.pack(side="left", padx=5)

btn_clear = ttk.Button(frame_buttons, text="🗑 LIMPAR", command=clear_log)
btn_clear.pack(side="left", padx=5)

btn_help = ttk.Button(frame_buttons, text="? HELP", command=show_help)
btn_help.pack(side="left", padx=5)

ttk.Label(frame_buttons, text="  [!] EXECUTAR COMO ADMINISTRADOR / ROOT", foreground="#FF0000").pack(side="left", padx=10)

# Área de log
frame_log = ttk.Frame(root, padding=10)
frame_log.pack(fill="both", expand=True)

ttk.Label(frame_log, text=">>> LOG EM TEMPO REAL <<<", style="Header.TLabel").pack(anchor="w")

text_area = scrolledtext.ScrolledText(
    frame_log,
    wrap=tk.WORD,
    state="disabled",
    font=("Consolas", 10),
    bg="#000000",
    fg="#00FF00",
    insertbackground="#00FF00",
    selectbackground="#003300",
    selectforeground="#00FF00",
    relief="flat",
    borderwidth=1,
    highlightthickness=1,
    highlightbackground="#00FF00",
    highlightcolor="#00FF00"
)
text_area.pack(fill="both", expand=True, pady=5)

# Tags de cor
text_area.tag_configure("info",  foreground="#00FF00")
text_area.tag_configure("dns",   foreground="#00FF00")
text_area.tag_configure("sni",   foreground="#00BFFF")
text_area.tag_configure("error", foreground="#FF3333")

# Rodapé
ttk.Label(root, text="[ LOGS ] dns_log.txt  |  sni_log.txt", font=("Consolas", 8)).pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

# Mensagem inicial (limpa)
log_message(">>> SISTEMA PRONTO <<<", tag="info")
log_message("\nSelecione as opções e clique em INICIAR.", tag="info")
log_message("")
log_message("[!] ATENÇÃO: Este programa precisa ser executado como Administrador (Windows) ou root (Linux/Kali).", tag="error")
log_message("")
log_message("Clique no botão  ? HELP  para ver as instruções de instalação.", tag="info")
log_message("")
log_message(">>> AGUARDANDO COMANDO... <<<", tag="info")
log_message("")

root.mainloop()
