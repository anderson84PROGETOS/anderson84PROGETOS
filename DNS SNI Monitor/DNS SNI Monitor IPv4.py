# ============================================================
#  DNS + SNI MONITOR // HACKER MODE (IPv4 only | 1 IP por host)
#  Testado em Windows 10/11 | Python 3.8+ | Scapy 2.6.x
# ============================================================
#  INSTALACAO (Windows 10):
#   1) Python 3.8+  ->  https://www.python.org/downloads/
#      Na instalacao, MARQUE: "Add Python to PATH"
#   2) Npcap        ->  https://npcap.com/#download
#      Marque: "Install Npcap in WinPcap API-compatible Mode"
#   3) CMD:  pip install --upgrade scapy
#   4) Execute:  python monitor.py
#      (ou salve como monitor.pyw para abrir sem console)
# ============================================================

import sys
import os
import traceback
import logging
import warnings
import socket
import time
import queue
import threading
from datetime import datetime
import platform

ERROR_LOG = "erro_ao_iniciar.txt"


def _write_error_log(text):
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def fatal_error(exc):
    """Mostra o erro numa janela e grava em erro_ao_iniciar.txt."""
    tb = traceback.format_exc()
    _write_error_log(tb)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "ERRO AO INICIAR",
            str(exc) + "\n\nDetalhes completos em: " + ERROR_LOG
        )
        root.destroy()
    except Exception:
        pass
    sys.exit(1)


# ====================== IMPORTS ======================
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox

    warnings.filterwarnings("ignore")
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
    logging.getLogger("scapy.loading").setLevel(logging.ERROR)
    logging.getLogger("scapy").setLevel(logging.ERROR)

    # IMPORTS CORRIGIDOS: direto dos submodulos,
    # evitando o circular import do scapy.all
    from scapy.sendrecv import sniff
    from scapy.layers.inet import TCP
    from scapy.packet import Raw
    from scapy.config import conf
    from scapy.layers.dns import DNS, DNSQR, DNSRR

    conf.verb = 0
except Exception as e:
    fatal_error(e)


# Erros imprevistos ficam gravados em erro_ao_iniciar.txt
def _excepthook(exc_type, exc_value, exc_tb):
    _write_error_log("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))


sys.excepthook = _excepthook

# ====================== CONFIGURACAO ======================
DNS_LOG = "dns_log.txt"
SNI_LOG = "sni_log.txt"

stop_event = threading.Event()
seen_dns = set()
seen_sni = set()
dns_thread = None
sni_thread = None
save_to_file = True  # copia do checkbox, lida com seguranca nas threads

# Cache de resolucao: host -> (timestamp, "ip_unico")
ip_cache = {}
IP_CACHE_TTL = 600  # 10 minutos

# Fila thread-safe: threads de captura so enfileiram;
# a interface (thread principal) atualiza a tela.
msg_queue = queue.Queue()

# ====================== RESOLUCAO DE IP ======================
def resolve_host(host):
    """Resolve um hostname e retorna APENAS 1 IPv4 (com cache de 10 minutos)."""
    cached = ip_cache.get(host)
    if cached and (time.time() - cached[0]) < IP_CACHE_TTL:
        return cached[1]

    ip = ""
    try:
        # AF_INET = SOMENTE IPv4 (ignora IPv6)
        infos = socket.getaddrinfo(host, None, socket.AF_INET)
        ips = sorted({info[4][0] for info in infos if info[4][0]})
        if ips:
            ip = ips[0]  # pega SOMENTE o primeiro IP
    except Exception:
        pass

    ip_cache[host] = (time.time(), ip)
    return ip


def extract_dns_ips(packet):
    """Extrai APENAS o primeiro IPv4 (registro A) da resposta DNS contida no pacote."""
    ips = []
    try:
        dns = packet[DNS]
        ans = dns.an
        while ans is not None:
            # type == 1  -> A (IPv4)
            # type == 28 -> AAAA (IPv6) -> IGNORADO
            if isinstance(ans, DNSRR) and ans.type == 1:
                ip = ans.rdata
                if isinstance(ip, bytes):
                    ip = ip.decode(errors="ignore")
                ips.append(str(ip))
                break  # pega somente o PRIMEIRO IP e para
            ans = ans.rr
    except Exception:
        pass
    return ips


# ====================== PROCESSAMENTO ======================
def process_dns(packet):
    if stop_event.is_set():
        return
    if not packet.haslayer(DNS):
        return
    try:
        if not packet.haslayer(DNSQR):
            return
        domain = packet[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
        now_minute = datetime.now().strftime("%d/%m/%Y %H:%M")
        unique_key = f"{now_minute}:{domain}"
        if unique_key in seen_dns:
            return
        seen_dns.add(unique_key)

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # 1) Primeiro IPv4 real da resposta DNS capturada
        ips = extract_dns_ips(packet)
        if ips:
            ips_str = ips[0]
        else:
            # 2) Fallback: resolve via socket (retorna somente 1 IPv4)
            ips_str = resolve_host(domain)

        if ips_str:
            log_entry = f"[DNS] [{timestamp}] {domain:<80} IP: {ips_str}"
        else:
            log_entry = f"[DNS] [{timestamp}] {domain:<80} IP: (nao resolvido)"

        log_message(log_entry, tag="dns")

        if save_to_file:
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
        return
    if not (packet.haslayer(TCP) and packet.haslayer(Raw)):
        return
    sni = extract_sni(packet[Raw].load)
    if not sni:
        return
    try:
        now_minute = datetime.now().strftime("%d/%m/%Y %H:%M")
        unique_key = f"{now_minute}:{sni}"
        if unique_key in seen_sni:
            return
        seen_sni.add(unique_key)

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ips_str = resolve_host(sni)  # resolve_host ja retorna somente 1 IPv4

        if ips_str:
            log_entry = f"[SNI] [{timestamp}] {sni:<80} IP: {ips_str}"
        else:
            log_entry = f"[SNI] [{timestamp}] {sni:<80} IP: (nao resolvido)"

        log_message(log_entry, tag="sni")

        if save_to_file:
            with open(SNI_LOG, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
    except Exception as e:
        log_message(f"[SNI Error] {e}", tag="error")


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


# ====================== INTERFACE GRAFICA ======================
def log_message(msg, tag="info"):
    """Enfileira a mensagem (thread-safe)."""
    msg_queue.put((msg, tag))


def _drain_queue():
    """Atualiza a tela com as mensagens da fila (thread principal)."""
    try:
        while True:
            msg, tag = msg_queue.get_nowait()
            text_area.configure(state="normal")
            text_area.insert(tk.END, msg + "\n", tag)
            text_area.see(tk.END)
            text_area.configure(state="disabled")
    except queue.Empty:
        pass
    root.after(100, _drain_queue)


def clear_log():
    """Limpa completamente a area de resultados."""
    text_area.configure(state="normal")
    text_area.delete("1.0", tk.END)
    text_area.configure(state="disabled")
    seen_dns.clear()
    seen_sni.clear()


def start_monitoring():
    global dns_thread, sni_thread, save_to_file

    if not var_dns.get() and not var_sni.get():
        messagebox.showwarning("Aviso", "Selecione pelo menos uma opcao (DNS ou SNI).")
        return

    stop_event.clear()
    seen_dns.clear()
    seen_sni.clear()
    save_to_file = var_save.get()

    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    chk_dns.config(state="disabled")
    chk_sni.config(state="disabled")
    chk_save.config(state="disabled")

    log_message("=" * 50, tag="info")
    log_message(f"Monitor iniciado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", tag="info")
    log_message(f"Sistema: {platform.system()} {platform.release()}", tag="info")
    log_message(f"Scapy: {conf.version}", tag="info")
    log_message("-> Resolucao de IP: SOMENTE IPv4", tag="info")
    log_message("-> Exibicao: 1 IP por host", tag="info")
    if save_to_file:
        log_message("-> Salvando logs em arquivo: ATIVADO", tag="info")
    else:
        log_message("-> Salvando logs em arquivo: DESATIVADO", tag="info")
    log_message("=" * 50, tag="info")

    if var_dns.get():
        log_message("-> Monitor DNS ativado", tag="dns")
        dns_thread = threading.Thread(target=start_dns_sniff, daemon=True)
        dns_thread.start()

    if var_sni.get():
        log_message("-> Monitor SNI (TLS) ativado", tag="sni")
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
    log_message("\n[OK] Monitoramento parado.\n", tag="info")


def show_help():
    help_win = tk.Toplevel(root)
    help_win.title("HELP - Como Instalar")
    help_win.geometry("800x700")
    help_win.configure(bg="#000000")
    help_win.resizable(False, False)

    help_win.update_idletasks()
    x = (help_win.winfo_screenwidth() // 2) - (700 // 2)
    y = (help_win.winfo_screenheight() // 2) - (500 // 2)
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
        height=18
    )
    help_text.pack(fill="both", expand=True)

    help_content = """[!] ATENCAO
Este programa precisa ser executado como Administrador (Windows)
ou root (Linux/Kali).

=======================================================
[ WINDOWS 10 / 11 ]
=======================================================

1. Instale o Python 3.8 ou superior:
   https://www.python.org/downloads/
   (na instalacao, MARQUE "Add Python to PATH")

2. Instale o Npcap:
   https://npcap.com/#download
   (marque "Install Npcap in WinPcap API-compatible Mode")

3. Abra o CMD (Win + R, digite cmd) e rode:
   pip install --upgrade scapy

4. Execute este script como Administrador:
   botao direito no arquivo -> Executar como administrador
   OU pelo CMD: python monitor.py

Dica: salve o arquivo com o nome monitor.pyw para
abrir com 2 cliques SEM mostrar a janela preta do CMD.

=======================================================
[ KALI LINUX ]
=======================================================

1. sudo apt update && sudo apt upgrade -y
2. sudo apt install python3 python3-pip python3-tk python3-scapy -y
3. sudo python3 monitor.py

=======================================================
[ SE A JANELA NAO ABRIR ]
=======================================================

Rode pelo CMD para ver o erro exato:
   python monitor.py
O erro tambem fica gravado em: erro_ao_iniciar.txt

- "python nao e reconhecido" -> reinstale o Python
  marcando "Add Python to PATH"
- "No module named 'scapy'" -> pip install scapy
- "cannot import name 'TCP' from partially initialized
   module 'scapy.all'" -> rode: pip install --upgrade scapy
   e apague qualquer arquivo scapy.py que exista na
   mesma pasta do script
- "Cannot load WinPcap/Npcap" -> instale o Npcap
- Antivirus pode bloquear a captura -> permita o programa
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
root.title("DNS SNI Monitor IPv4")
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


def _report_callback_exception(self, exc, val, tb):
    _write_error_log("".join(traceback.format_exception(exc, val, tb)))


tk.Tk.report_callback_exception = _report_callback_exception

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

# Botoes
frame_buttons = ttk.Frame(root, padding=10)
frame_buttons.pack(fill="x")

btn_start = ttk.Button(frame_buttons, text="INICIAR", command=start_monitoring)
btn_start.pack(side="left", padx=5)

btn_stop = ttk.Button(frame_buttons, text="PARAR", command=stop_monitoring, state="disabled")
btn_stop.pack(side="left", padx=5)

btn_clear = ttk.Button(frame_buttons, text="LIMPAR", command=clear_log)
btn_clear.pack(side="left", padx=5)

btn_help = ttk.Button(frame_buttons, text="HELP", command=show_help)
btn_help.pack(side="left", padx=5)

ttk.Label(frame_buttons, text="  [!] EXECUTAR COMO ADMINISTRADOR / ROOT", foreground="#FF0000").pack(side="left", padx=10)

# Area de log
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

# Rodape
ttk.Label(root, text="[ LOGS ] dns_log.txt  |  sni_log.txt", font=("Consolas", 8)).pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

# Mensagem inicial
log_message(">>> SISTEMA PRONTO <<<", tag="info")
log_message("\nSelecione as opcoes e clique em INICIAR.", tag="info")
log_message("")
log_message("[!] ATENCAO: execute como Administrador (Windows) ou root (Linux/Kali).", tag="error")
log_message("")
log_message("Se a captura falhar, verifique se o Npcap esta instalado.", tag="error")
log_message("")
log_message("Clique no botao HELP para ver as instrucoes de instalacao.", tag="info")
log_message("")
log_message(">>> AGUARDANDO COMANDO... <<<", tag="info")
log_message("")

# Inicia o loop que atualiza a tela a partir da fila
_drain_queue()

root.mainloop()
