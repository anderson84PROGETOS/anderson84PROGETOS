import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import hashlib
import webbrowser
import threading

# ==================== CONFIGURAÇÕES ====================
def get_chrome_default():
    return os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Google",
        "Chrome",
        "User Data",
        "Default",
        "Download Service",
        "Files"
    )

def get_firefox_default():
    # Seu perfil específico
    localappdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    
    # Tenta encontrar o perfil exato que você tem
    profile_name = "x5oy8no8.default-release"
    
    # Caminho 1: LocalAppData
    path1 = os.path.join(localappdata, "Mozilla", "Firefox", "Profiles", profile_name, "cache2", "entries")
    if os.path.exists(path1):
        return path1
    
    # Caminho 2: AppData (Roaming)
    path2 = os.path.join(appdata, "Mozilla", "Firefox", "Profiles", profile_name, "cache2", "entries")
    if os.path.exists(path2):
        return path2
    
    # Busca automática em todos os profiles
    mozilla_path = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(mozilla_path):
        for folder in os.listdir(mozilla_path):
            if folder.endswith('.default-release') or 'default' in folder:
                full_path = os.path.join(mozilla_path, folder, "cache2", "entries")
                if os.path.exists(full_path):
                    return full_path
    
    return path1  # retorna o caminho mesmo se não existir

PASTA_PADRAO_CHROME = get_chrome_default()
PASTA_PADRAO_FIREFOX = get_firefox_default()

pasta_atual = PASTA_PADRAO_CHROME

# Cores
COR_BG = "#2b2b2b"
COR_FG = "#ffffff"
COR_BOTOES = "#007acc"
COR_DELETAR = "#c42b1c"
COR_VERDE = "#00cc66"
COR_AZUL = "#4285f4"
COR_LARANJA = "#ff6600"

def formatar_tamanho(bytes_):
    gb = bytes_ / (1024**3)
    mb = bytes_ / (1024**2)
    kb = bytes_ / 1024
    if gb >= 1: return f"{gb:.2f} GB"
    elif mb >= 1: return f"{mb:.2f} MB"
    elif kb >= 1: return f"{kb:.2f} KB"
    else: return f"{bytes_} Bytes"

# ==================== FUNÇÕES ====================
def selecionar_pasta():
    global pasta_atual
    pasta = filedialog.askdirectory()
    if pasta:
        pasta_atual = pasta
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, pasta)
        atualizar_label_pasta()

def atualizar_label_pasta():
    nome = os.path.basename(pasta_atual) if pasta_atual else "Nenhuma"
    lbl_pasta.config(text=f"Pasta atual: {nome}\nCaminho: {pasta_atual}")

def analisar_pasta():
    limpar_tabela()
    progress_bar['value'] = 0
    janela.update()

    if not os.path.exists(pasta_atual):
        lbl_status.config(text="❌ Pasta não Encontrada! Verifique o caminho.")
        return

    if not os.listdir(pasta_atual):  # Pasta vazia
        lbl_status.config(text="⚠️ Pasta Encontrada, mas está vazia.")
        return

    configurar_progresso_verde()
    progress_bar.configure(style="green.Horizontal.TProgressbar")

    arquivos = []
    lista_arquivos = [f for f in os.listdir(pasta_atual) if os.path.isfile(os.path.join(pasta_atual, f))]
    
    for i, arquivo in enumerate(lista_arquivos):
        caminho = os.path.join(pasta_atual, arquivo)
        try:
            tamanho = os.path.getsize(caminho)
            data = os.path.getmtime(caminho)
            arquivos.append((arquivo, caminho, tamanho, data))
        except:
            continue

        progress = int((i + 1) / len(lista_arquivos) * 100)
        progress_bar['value'] = progress
        janela.update_idletasks()

    arquivos.sort(key=lambda x: x[2], reverse=True)

    for nome, caminho, tamanho, data in arquivos:
        extensao = os.path.splitext(nome)[1]
        tree.insert("", "end", values=(nome, "Arquivo", extensao or "-", 
                                       formatar_tamanho(tamanho),
                                       datetime.fromtimestamp(data).strftime("%d/%m/%Y %H:%M:%S"), 
                                       caminho))

    total_bytes = sum(x[2] for x in arquivos)
    lbl_status.config(text=f"✅ {len(arquivos)} arquivo(s) | Total: {formatar_tamanho(total_bytes)}")
    progress_bar['value'] = 100

# Funções restantes (abrir, excluir, VirusTotal, etc.)
def limpar_tabela():
    for item in tree.get_children():
        tree.delete(item)

def configurar_progresso_verde():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("green.Horizontal.TProgressbar", foreground=COR_VERDE, background=COR_VERDE, troughcolor='#555555', thickness=20)

def calcular_hash_arquivo(caminho):
    try:
        sha256 = hashlib.sha256()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None

def scan_virustotal(caminho):
    if not os.path.exists(caminho):
        messagebox.showerror("Erro", "Arquivo não encontrado!")
        return
    lbl_status.config(text="🔍 Calculando hash...")
    janela.update()
    hash_file = calcular_hash_arquivo(caminho)
    if hash_file:
        webbrowser.open(f"https://www.virustotal.com/gui/file/{hash_file}")
        lbl_status.config(text="✅ Aberto no VirusTotal")
    else:
        lbl_status.config(text="❌ Erro ao calcular hash")

def scan_selecionado():
    item = tree.focus()
    if not item:
        messagebox.showwarning("Atenção", "Selecione um arquivo!")
        return
    caminho = tree.item(item)["values"][5]
    threading.Thread(target=scan_virustotal, args=(caminho,), daemon=True).start()

def mudar_pasta(tipo):
    global pasta_atual
    pasta_atual = PASTA_PADRAO_CHROME if tipo == "chrome" else PASTA_PADRAO_FIREFOX
    entrada_pasta.delete(0, tk.END)
    entrada_pasta.insert(0, pasta_atual)
    atualizar_label_pasta()
    analisar_pasta()

def abrir_arquivo(event=None):
    item = tree.focus()
    if item:
        caminho = tree.item(item)["values"][5]
        if os.path.exists(caminho):
            os.startfile(caminho)

def excluir_arquivo():
    item = tree.focus()
    if not item: 
        messagebox.showwarning("Atenção", "Selecione um arquivo!")
        return
    dados = tree.item(item)["values"]
    if messagebox.askyesno("Confirmar", f"Excluir {dados[0]}?"):
        try:
            os.remove(dados[5])
            analisar_pasta()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

def excluir_todos():
    if messagebox.askyesno("⚠️ CUIDADO", "Excluir TODOS os arquivos da pasta?"):
        count = 0
        for f in os.listdir(pasta_atual):
            try:
                os.remove(os.path.join(pasta_atual, f))
                count += 1
            except:
                pass
        messagebox.showinfo("Pronto", f"{count} arquivos excluídos.")
        analisar_pasta()

# ==================== INTERFACE ====================
janela = tk.Tk()
janela.title("Analisador de Downloads - Chrome / Firefox + VirusTotal")
janela.geometry("1400x760")
janela.state("zoomed")
janela.configure(bg=COR_BG)

lbl_pasta = tk.Label(janela, text="", bg="#1e1e1e", fg="#00ffcc", font=("Arial", 11, "bold"), anchor="w")
lbl_pasta.pack(fill="x", padx=10, pady=8)

progress_bar = ttk.Progressbar(janela, mode='determinate')
progress_bar.pack(fill="x", padx=10, pady=5)

frame1 = tk.Frame(janela, bg=COR_BG)
frame1.pack(fill="x", padx=10, pady=5)

entrada_pasta = tk.Entry(frame1, font=("Arial", 10))
entrada_pasta.pack(side="left", fill="x", expand=True, padx=(0,5))
entrada_pasta.insert(0, pasta_atual)

tk.Button(frame1, text="Selecionar Pasta", command=selecionar_pasta, bg="#444", fg="white", width=15).pack(side="left", padx=4)
tk.Button(frame1, text="Analisar", command=analisar_pasta, bg=COR_BOTOES, fg="white", width=12).pack(side="left", padx=4)
tk.Button(frame1, text="Abrir Pasta", command=lambda: os.startfile(pasta_atual) if os.path.exists(pasta_atual) else None, bg="#444", fg="white", width=12).pack(side="left", padx=4)

frame_pastas = tk.Frame(janela, bg=COR_BG)
frame_pastas.pack(fill="x", padx=10, pady=2)
tk.Button(frame_pastas, text="📁 Chrome Downloads", command=lambda: mudar_pasta("chrome"), bg=COR_AZUL, fg="white", width=20).pack(side="left", padx=4)
tk.Button(frame_pastas, text="📁 Firefox Cache", command=lambda: mudar_pasta("firefox"), bg=COR_AZUL, fg="white", width=20).pack(side="left", padx=4)

# Busca e Status (mantido igual)
frame2 = tk.Frame(janela, bg=COR_BG)
frame2.pack(fill="x", padx=10, pady=5)
tk.Label(frame2, text="Pesquisar:", bg=COR_BG, fg=COR_FG).pack(side="left", padx=(0,5))
entrada_busca = tk.Entry(frame2, font=("Arial", 10))
entrada_busca.pack(side="left", fill="x", expand=True, padx=(0,5))
tk.Button(frame2, text="Buscar", command=lambda: None, bg=COR_BOTOES, fg="white").pack(side="left", padx=4)  # simplificado

lbl_status = tk.Label(janela, text="", bg=COR_BG, fg="#00ff88", font=("Arial", 10, "bold"))
lbl_status.pack(fill="x", padx=10, pady=5)

# Tabela
tree = ttk.Treeview(janela, columns=("Nome", "Tipo", "Extensão", "Tamanho", "Data", "Caminho"), show="headings")
for col in tree["columns"]:
    tree.heading(col, text=col)
tree.column("Nome", width=280)
tree.column("Caminho", width=500)
tree.pack(fill="both", expand=True, padx=10, pady=5)

tree.bind("<Double-1>", abrir_arquivo)

frame3 = tk.Frame(janela, bg=COR_BG)
frame3.pack(fill="x", padx=10, pady=10)
tk.Button(frame3, text="Excluir Selecionado", command=excluir_arquivo, bg=COR_DELETAR, fg="white").pack(side="left", padx=5)
tk.Button(frame3, text="Excluir TODOS", command=excluir_todos, bg=COR_DELETAR, fg="white").pack(side="left", padx=5)
tk.Button(frame3, text="🔍 VirusTotal", command=scan_selecionado, bg=COR_LARANJA, fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)

atualizar_label_pasta()
analisar_pasta()   # Analisa automaticamente ao abrir

janela.mainloop()
