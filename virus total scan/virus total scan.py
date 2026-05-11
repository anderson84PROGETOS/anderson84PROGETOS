import os
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import webbrowser
import urllib.parse
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

parar = False
total = 0
atual = 0

# =========================================================
# VIRUSTOTAL
# =========================================================

def abrir_virustotal(valor):

    if not valor:
        return

    url = (
        "https://www.virustotal.com/gui/search/"
        + urllib.parse.quote(str(valor), safe="")
    )

    webbrowser.open(url)

# =========================================================
# HASH SHA256
# =========================================================

def get_hash(file_path):

    try:

        h = hashlib.sha256()

        with open(file_path, "rb") as f:

            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)

        return h.hexdigest()

    except:
        return "ERRO_HASH"

# =========================================================
# FORMATADORES
# =========================================================

def formatar_tamanho(bytes_size):

    kb = 1024
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024

    if bytes_size >= tb:
        return f"{round(bytes_size / tb, 2)} TB"

    elif bytes_size >= gb:
        return f"{round(bytes_size / gb, 2)} GB"

    elif bytes_size >= mb:
        return f"{round(bytes_size / mb, 2)} MB"

    elif bytes_size >= kb:
        return f"{round(bytes_size / kb, 2)} KB"

    else:
        return f"{bytes_size} B"

def formatar_data(timestamp):

    return datetime.fromtimestamp(timestamp).strftime(
        "%d/%m/%Y %H:%M:%S"
    )

# =========================================================
# CLASSIFICAÇÃO
# =========================================================

WHITELIST = [
    "google\\chrome",
    "chrome\\user data",
    "extensions",
    "safe browsing",
    "windows defender",
    "microsoft",
    "mozilla",
    "edge"
]

SUSPICIOUS = [
    "inject",
    "hook",
    "keylogger",
    "mimikatz",
    "meterpreter",
    "backdoor",
    "ransom",
    "stealer",
    "rat",
    "miner",
    "trojan",
    "payload",
    "spy",
    "grabber",
    "shell",
    "bypass",
    "loader",
    "crypt",
    "remote",
    "logger"
]

# =========================================================
# CLASSIFICAR
# =========================================================

def classificar(caminho, nome):

    caminho_lower = caminho.lower()
    nome_lower = nome.lower()

    # ==========================================
    # WHITELIST
    # ==========================================

    for item in WHITELIST:

        if item in caminho_lower:
            return "BAIXO", "Arquivo confiável"

    # ==========================================
    # SCORE
    # ==========================================

    score = 0

    for item in SUSPICIOUS:

        if item in nome_lower:
            score += 2

    if nome_lower.endswith(".exe"):
        score += 1

    if nome_lower.endswith(".dll"):
        score += 1

    if "temp" in caminho_lower:
        score += 1

    if "appdata" in caminho_lower:
        score += 1

    # ==========================================
    # RESULTADO
    # ==========================================

    if score >= 5:
        return "ALTO", "Malware provável"

    elif score >= 2:
        return "MEDIO", "Suspeita heurística"

    else:
        return "BAIXO", "Sem ameaça detectada"

# =========================================================
# LOG
# =========================================================

def log(msg, tag="normal"):

    timestamp = datetime.now().strftime("%H:%M:%S")

    texto.insert(
        tk.END,
        f"[{timestamp}] {msg}\n",
        tag
    )

    texto.see(tk.END)

# =========================================================
# CONTAR ARQUIVOS + TAMANHO
# =========================================================

def contar_arquivos_e_tamanho(pasta):

    total_arquivos = 0
    total_bytes = 0

    for root, dirs, files in os.walk(pasta):

        for file in files:

            caminho = os.path.join(root, file)

            total_arquivos += 1

            try:
                total_bytes += os.path.getsize(caminho)
            except:
                pass

    return total_arquivos, total_bytes

# =========================================================
# SCAN
# =========================================================

def scan(pasta):

    global parar
    global total
    global atual

    atual = 0

    # ==========================================
    # TOTAL ARQUIVOS + TAMANHO
    # ==========================================

    total, total_bytes = contar_arquivos_e_tamanho(pasta)

    tamanho_total = formatar_tamanho(total_bytes)

    progress["maximum"] = total
    progress["value"] = 0

    # ==========================================
    # LOG INICIAL
    # ==========================================

    log(f"🔍 SCAN INICIADO: {pasta}", "info")

    log(
        f"📦 TOTAL DE ARQUIVOS: {total} | 💾 TAMANHO TOTAL: {tamanho_total}",
        "info"
    )

    log(
        "🔎 MOSTRANDO SOMENTE ARQUIVOS SUSPEITOS",
        "info"
    )

    # ==========================================
    # WALK
    # ==========================================

    for root, dirs, files in os.walk(pasta):

        if parar:

            log("🛑 SCAN INTERROMPIDO", "alto")
            return

        for file in files:

            caminho = os.path.join(root, file)

            atual += 1

            progress["value"] = atual

            # ==================================
            # SCROLLBAR / UPDATE
            # ==================================

            if atual % 10 == 0:
                janela.update_idletasks()

            # ==================================
            # INFO ARQUIVO
            # ==================================

            try:

                tamanho = formatar_tamanho(
                    os.path.getsize(caminho)
                )

                data_mod = formatar_data(
                    os.path.getmtime(caminho)
                )

            except:

                tamanho = "0 B"
                data_mod = "N/A"

            # ==================================
            # CLASSIFICAR
            # ==================================

            nivel, motivo = classificar(
                caminho,
                file
            )

            # ==================================
            # MOSTRAR SUSPEITOS
            # ==================================

            if nivel in ["MEDIO", "ALTO"]:

                sha256 = get_hash(caminho)

                log(
                    "=" * 90,
                    "linha"
                )

                if nivel == "ALTO":

                    log(
                        "🔴 RISCO ALTO DETECTADO",
                        "alto"
                    )

                else:

                    log(
                        "🟡 RISCO MÉDIO DETECTADO",
                        "medio"
                    )

                log(
                    f"📁 CAMINHO: {caminho}",
                    "normal"
                )

                log(
                    f"💾 TAMANHO: {tamanho}",
                    "normal"
                )

                log(
                    f"📅 DATA: {data_mod}",
                    "normal"
                )

                log(
                    f"⚠ MOTIVO: {motivo}",
                    "normal"
                )

                log(
                    f"🔐 SHA256: {sha256}",
                    "hash"
                )

                log(
                    "=" * 90,
                    "linha"
                )

    log("✅ SCAN FINALIZADO!", "info")

# =========================================================
# THREAD
# =========================================================

def iniciar_scan():

    pasta = filedialog.askdirectory()

    if not pasta:
        return

    threading.Thread(
        target=scan,
        args=(pasta,),
        daemon=True
    ).start()

def iniciar():

    global parar

    parar = False

    iniciar_scan()

def parar_scan():

    global parar

    parar = True

# =========================================================
# GUI
# =========================================================

janela = tk.Tk()

janela.title("virus total scan")
janela.geometry("1200x780")
janela.state("zoomed")
janela.configure(bg="#111111")

# =========================================================
# STYLE
# =========================================================

style = ttk.Style()
style.theme_use("default")
style.configure("TProgressbar", thickness=24)

# =========================================================
# FRAME BOTÕES
# =========================================================

frame = tk.Frame(janela, bg="#111111")
frame.pack(pady=10)

# =========================================================
# BOTÃO START
# =========================================================

btn_start = tk.Button(frame, text="▶ INICIAR SCAN", bg="#00aa00", fg="white", font=("Consolas", 11, "bold"), width=20, command=iniciar)
btn_start.grid(row=0, column=0, padx=10)

# =========================================================
# BOTÃO STOP
# =========================================================

btn_stop = tk.Button(frame, text="⛔ PARAR", bg="#aa0000", fg="white", font=("Consolas", 11, "bold"), width=15, command=parar_scan)
btn_stop.grid(row=0, column=1, padx=10)

# =========================================================
# BOTÃO VIRUSTOTAL
# =========================================================

btn_vt = tk.Button(frame, text="🌐 VIRUSTOTAL", bg="#0044aa", fg="white", font=("Consolas", 11, "bold"), width=20, command=lambda: abrir_virustotal(texto.get("sel.first", "sel.last")))
btn_vt.grid(row=0, column=2, padx=10)

# =========================================================
# BARRA PROGRESSO
# =========================================================

progress = ttk.Progressbar(janela, orient="horizontal", length=1120, mode="determinate")
progress.pack(pady=10)

# =========================================================
# FRAME TEXTO + SCROLLBAR
# =========================================================

frame_texto = tk.Frame(janela, bg="#111111")

frame_texto.pack(fill="both", expand=True, padx=10, pady=10)

# =========================================================
# SCROLLBAR
# =========================================================

scrollbar = tk.Scrollbar(frame_texto)

scrollbar.pack(side="right", fill="y")

# =========================================================
# LOG TEXT
# =========================================================

texto = tk.Text(frame_texto, bg="#000000", fg="#00ff00", insertbackground="white", font=("Consolas", 10), yscrollcommand=scrollbar.set)

texto.pack(side="left", fill="both", expand=True)

scrollbar.config(command=texto.yview)

# =========================================================
# TAGS CORES
# =========================================================

texto.tag_config("alto", foreground="#ff3333")

texto.tag_config("medio", foreground="#ffff00")

texto.tag_config("info", foreground="#00ffff")

texto.tag_config("hash", foreground="#ff66ff")

texto.tag_config("linha", foreground="#666666")

texto.tag_config("normal", foreground="#00ff00")

# =========================================================
# START
# =========================================================

log("🛡 EDR FORENSE INICIADO", "info")
log("💻 SISTEMA PRONTO PARA SCAN", "info")

janela.mainloop()
