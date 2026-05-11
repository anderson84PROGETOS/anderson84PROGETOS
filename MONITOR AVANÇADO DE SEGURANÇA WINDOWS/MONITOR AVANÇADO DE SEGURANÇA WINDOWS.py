import os
import re
import time
import socket
import hashlib
import threading
import subprocess
import tkinter as tk
import webbrowser
import urllib.parse
import ipaddress

from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

# =========================================================
# VIRUSTOTAL
# =========================================================

def abrir_virustotal(valor):
    if not valor:
        return
    url = "https://www.virustotal.com/gui/search/" + urllib.parse.quote(str(valor), safe="")
    webbrowser.open(url)

# =========================================================
# DETECÇÃO INTELIGENTE
# =========================================================

def detectar_valor(linha):
    if not linha:
        return None

    hash_patterns = [
        r"\b[a-fA-F0-9]{64}\b",
        r"\b[a-fA-F0-9]{40}\b",
        r"\b[a-fA-F0-9]{32}\b",
    ]

    for p in hash_patterns:
        m = re.search(p, linha)
        if m:
            return m.group(0)

    ipv4 = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", linha)
    if ipv4:
        return ipv4.group(0)

    for token in linha.split():
        try:
            ipaddress.ip_address(token)
            return token
        except:
            pass

    dominio = re.search(r"DOMÍNIO:\s*([a-zA-Z0-9\.\-\_]+)", linha)
    if dominio:
        return dominio.group(1)

    dominio2 = re.search(r"\b([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})\b", linha)
    if dominio2:
        return dominio2.group(1)

    return None

# =========================================================
# PSUTIL
# =========================================================

try:
    import psutil
except ImportError:
    messagebox.showerror("Erro", "Instale: pip install psutil")
    raise

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFICAR_CADA = 5

PALAVRAS_SUSPEITAS = [
    "powershell", "cmd.exe", "wscript", "cscript", "keylogger",
    "backdoor", "ransom", "mimikatz", "meterpreter", "reverse",
    "shell", "netcat", "nc.exe", "malware", "trojan", "cobalt",
    "beacon", "empire"
]

PORTAS_SUSPEITAS = [4444, 5555, 6666, 1337, 9001, 31337, 8080, 443]

PASTAS_PERSISTENCIA = [
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
    os.path.expandvars(r"%TEMP%"),
    os.path.expandvars(r"%APPDATA%"),
    os.path.expandvars(r"%LOCALAPPDATA%"),
]

# =========================================================
# CONTROLE
# =========================================================

stop_event = threading.Event()
monitorando = False

# =========================================================
# INTERFACE
# =========================================================

janela = tk.Tk()
janela.title("MONITOR AVANÇADO DE SEGURANÇA WINDOWS")
janela.geometry("1300x800")
janela.state("zoomed")
janela.configure(bg="#101010")

area_logs = None
progress_bar = None

# =========================================================
# LOG
# =========================================================

def log(msg, tag="status"):
    if not area_logs:
        return
    agora = datetime.now().strftime("%H:%M:%S")
    area_logs.insert(tk.END, f"[{agora}] {msg}\n", tag)
    area_logs.see(tk.END)

# =========================================================
# HASH
# =========================================================

def calcular_hash(arquivo):
    try:
        h = hashlib.sha256()
        with open(arquivo, "rb") as f:
            for b in iter(lambda: f.read(4096), b""):
                h.update(b)
        return h.hexdigest()
    except:
        return None

# =========================================================
# SCAN DE PASTA (NOVO)
# =========================================================

def scan_pasta(pasta):
    if not pasta or not os.path.exists(pasta):
        return

    log(f"🔍 INICIANDO SCAN NA PASTA: {pasta}", "alerta")
    progress_bar['value'] = 0
    janela.update()

    arquivos = []
    for root, dirs, files in os.walk(pasta):
        for file in files:
            arquivos.append(os.path.join(root, file))

    total = len(arquivos)
    if total == 0:
        log("Nenhum arquivo encontrado na pasta.", "status")
        progress_bar['value'] = 100
        return

    for i, caminho in enumerate(arquivos):
        try:
            nome = os.path.basename(caminho).lower()
            extensao = os.path.splitext(nome)[1].lower()

            # Atualiza barra de progresso
            progress_bar['value'] = (i + 1) / total * 100
            janela.update_idletasks()

            suspeito = False
            motivo = ""

            if extensao in [".exe", ".bat", ".ps1", ".vbs", ".cmd", ".scr", ".pif"]:
                suspeito = True
                motivo = "Extensão executável"

            if any(palavra in nome for palavra in PALAVRAS_SUSPEITAS):
                suspeito = True
                motivo = "Nome suspeito"

            if suspeito:
                log(f"🚩 ARQUIVO SUSPEITO ENCONTRADO", "alerta")
                log(f"Caminho: {caminho}", "alerta")
                log(f"Motivo: {motivo}", "alerta")

                h = calcular_hash(caminho)
                if h:
                    log(f"HASH: {h}", "alerta")
                log("-" * 60, "alerta")

        except:
            continue

    progress_bar['value'] = 100
    log("✅ SCAN DA PASTA CONCLUÍDO!", "status")

def escolher_e_scanear_pasta():
    pasta = filedialog.askdirectory(title="Selecione a pasta para escanear")
    if pasta:
        threading.Thread(target=scan_pasta, args=(pasta,), daemon=True).start()

# =========================================================
# CLIQUE NO LOG
# =========================================================

def ao_duplo_clique(event):
    try:
        index = area_logs.index(f"@{event.x},{event.y}")
        linha = area_logs.get(index + " linestart", index + " lineend")
        valor = detectar_valor(linha)
        if valor:
            abrir_virustotal(valor)
    except:
        pass

# =========================================================
# PROCESSOS (mantido original)
# =========================================================

def verificar_processos():
    while not stop_event.is_set():
        try:
            for p in list(psutil.process_iter(['pid', 'name', 'exe', 'cmdline'])):
                if stop_event.is_set():
                    return
                try:
                    nome = str(p.info['name']).lower()
                    exe = str(p.info.get('exe') or "").lower()
                    cmd = " ".join(p.info.get('cmdline') or []).lower()

                    if any(x in nome or x in exe or x in cmd for x in PALAVRAS_SUSPEITAS):
                        log("🚨 PROCESSO SUSPEITO DETECTADO", "alerta")
                        log(f"PID: {p.pid}", "alerta")
                        log(f"NOME: {nome}\n", "alerta")

                        if exe and os.path.exists(exe):
                            h = calcular_hash(exe)
                            if h:
                                log(f"HASH: {h}\n", "alerta")
                except:
                    pass
        except:
            pass
        stop_event.wait(VERIFICAR_CADA)

# =========================================================
# CONEXÕES (mantido original)
# =========================================================

def resolver_dominio(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

def verificar_conexoes():
    while not stop_event.is_set():
        try:
            conexoes = list(psutil.net_connections(kind='inet'))
            for c in conexoes:
                if stop_event.is_set():
                    return
                if not c.raddr:
                    continue

                ip = c.raddr.ip
                porta = c.raddr.port
                dominio = resolver_dominio(ip)

                if porta in PORTAS_SUSPEITAS:
                    log("🌐 CONEXÃO SUSPEITA", "conexao")
                    log(f"IP: {ip}", "conexao")
                    log(f"PORTA: {porta}\n", "conexao")
                    if dominio:
                        log(f"DOMÍNIO: {dominio}\n", "conexao")
                else:
                    if dominio:
                        log(f"🌍 ACESSO: {dominio}\n", "status")
        except:
            pass
        stop_event.wait(0.5)

# =========================================================
# PERSISTÊNCIA (mantido original)
# =========================================================

def verificar_persistencia():
    while not stop_event.is_set():
        try:
            for pasta in PASTAS_PERSISTENCIA:
                if stop_event.is_set():
                    return
                if not os.path.exists(pasta):
                    continue
                for arq in list(os.listdir(pasta)):
                    if stop_event.is_set():
                        return
                    caminho = os.path.join(pasta, arq)
                    if arq.endswith((".exe", ".bat", ".ps1", ".vbs", ".cmd")):
                        log("🔄 PERSISTÊNCIA DETECTADA", "persist")
                        log(f"{caminho}\n", "persist")
        except:
            pass
        stop_event.wait(VERIFICAR_CADA)

# =========================================================
# CONTROLE MONITORAMENTO
# =========================================================

def iniciar():
    global monitorando
    if monitorando:
        return
    monitorando = True
    stop_event.clear()
    log("✅ MONITORAMENTO INICIADO\n", "status")

    threading.Thread(target=verificar_processos, daemon=True).start()
    threading.Thread(target=verificar_conexoes, daemon=True).start()
    threading.Thread(target=verificar_persistencia, daemon=True).start()

def parar():
    global monitorando
    if not monitorando:
        return
    monitorando = False
    stop_event.set()
    log("⛔ PARANDO MONITORAMENTO...\n", "status")
    janela.after(0, lambda: log("⛔ MONITORAMENTO PARADO IMEDIATAMENTE\n", "status"))

# =========================================================
# FUNÇÕES EXTRAS
# =========================================================

def exportar():
    try:
        arquivo = filedialog.asksaveasfilename(defaultextension=".txt")
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(area_logs.get("1.0", tk.END))
            messagebox.showinfo("OK", "Logs exportados com sucesso!")
    except:
        pass

def limpar():
    area_logs.delete("1.0", tk.END)

# =========================================================
# UI
# =========================================================

frame = tk.Frame(janela, bg="#101010")
frame.pack(fill="x", padx=5, pady=5)

tk.Button(frame, text="INICIAR", command=iniciar, bg="green", fg="white", width=12).pack(side="left", padx=3)
tk.Button(frame, text="PARAR", command=parar, bg="red", fg="white", width=12).pack(side="left", padx=3)
tk.Button(frame, text="SCAN PASTA", command=escolher_e_scanear_pasta, bg="#FF8800", fg="white", width=15).pack(side="left", padx=3)

tk.Button(frame, text="EXPORTAR", command=exportar, bg="#444", fg="white", width=12).pack(side="left", padx=3)
tk.Button(frame, text="LIMPAR", command=limpar, bg="#444", fg="white", width=12).pack(side="left", padx=3)

# Barra de Progresso
progress_frame = tk.Frame(janela, bg="#101010")
progress_frame.pack(fill="x", padx=10, pady=2)
tk.Label(progress_frame, text="Progresso do Scan:", bg="#101010", fg="white").pack(side="left")
progress_bar = ttk.Progressbar(progress_frame, length=800, mode='determinate')
progress_bar.pack(side="left", padx=10, fill="x", expand=True)

area_logs = ScrolledText(janela, bg="black", fg="green")
area_logs.pack(fill="both", expand=True, padx=10, pady=5)

area_logs.tag_config("alerta", foreground="red")
area_logs.tag_config("conexao", foreground="orange")
area_logs.tag_config("persist", foreground="cyan")
area_logs.tag_config("status", foreground="green")

area_logs.bind("<Double-Button-1>", ao_duplo_clique)

log("Sistema iniciado\n", "status")
log("Clique em INICIAR ou em SCAN PASTA\n", "status")

janela.mainloop()
