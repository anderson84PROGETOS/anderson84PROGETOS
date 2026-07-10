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

def get_edge_profiles():
    localappdata = os.environ.get("LOCALAPPDATA", "")
    base_path = os.path.join(localappdata, "Microsoft", "Edge", "User Data")
    profiles = []
    
    if not os.path.exists(base_path):
        return []
    
    for folder in os.listdir(base_path):
        if folder in ["Default", "System Profile"] or folder.startswith("Profile "):
            download_service = os.path.join(base_path, folder, "Download Service", "Files")
            if os.path.exists(download_service):
                profiles.append((folder, download_service))
    
    return profiles

def get_firefox_default():
    localappdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    profile_name = "x5oy8no8.default-release"
    
    path1 = os.path.join(localappdata, "Mozilla", "Firefox", "Profiles", profile_name, "cache2", "entries")
    if os.path.exists(path1):
        return path1
    
    path2 = os.path.join(appdata, "Mozilla", "Firefox", "Profiles", profile_name, "cache2", "entries")
    if os.path.exists(path2):
        return path2
    
    mozilla_path = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(mozilla_path):
        for folder in os.listdir(mozilla_path):
            if folder.endswith('.default-release') or 'default' in folder:
                full_path = os.path.join(mozilla_path, folder, "cache2", "entries")
                if os.path.exists(full_path):
                    return full_path
    return path1

PASTA_PADRAO_CHROME = get_chrome_default()
PASTA_PADRAO_FIREFOX = get_firefox_default()
EDGE_PROFILES = get_edge_profiles()

pasta_atual = PASTA_PADRAO_CHROME

# Cores
COR_BG = "#2b2b2b"
COR_FG = "#ffffff"
COR_BOTOES = "#007acc"
COR_DELETAR = "#bd8307"
COR_VERDE = "#00cc66"
COR_LARANJA = "#00eeff"

def formatar_tamanho(bytes_):
    gb = bytes_ / (1024**3)
    mb = bytes_ / (1024**2)
    kb = bytes_ / 1024
    if gb >= 1: return f"{gb:.2f} GB"
    elif mb >= 1: return f"{mb:.2f} MB"
    elif kb >= 1: return f"{kb:.2f} KB"
    else: return f"{bytes_} Bytes"

# ==================== VARIÁVEIS GLOBAIS ====================
todos_arquivos = []

# ==================== FUNÇÕES ====================
def selecionar_pasta():
    global pasta_atual
    pasta = filedialog.askdirectory(title="Selecione uma pasta")
    if pasta:
        pasta_atual = pasta
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, pasta)
        atualizar_label_pasta()
        analisar_pasta()

def atualizar_label_pasta():
    nome = os.path.basename(pasta_atual) if pasta_atual else "Nenhuma"
    lbl_pasta.config(text=f"Pasta atual: {nome}\nCaminho: {pasta_atual}")

def analisar_pasta():
    global todos_arquivos
    limpar_tabela()
    progress_bar['value'] = 0
    janela.update()

    if not os.path.exists(pasta_atual):
        lbl_status.config(text="❌ Pasta não Encontrada!")
        return

    configurar_progresso_verde()

    todos_arquivos = []
    lista_arquivos = [f for f in os.listdir(pasta_atual) if os.path.isfile(os.path.join(pasta_atual, f))]
    
    for i, arquivo in enumerate(lista_arquivos):
        caminho = os.path.join(pasta_atual, arquivo)
        try:
            tamanho = os.path.getsize(caminho)
            data = os.path.getmtime(caminho)
            todos_arquivos.append((arquivo, caminho, tamanho, data))
        except:
            continue

        progress = int((i + 1) / len(lista_arquivos) * 100)
        progress_bar['value'] = progress
        janela.update_idletasks()

    todos_arquivos.sort(key=lambda x: x[2], reverse=True)
    preencher_tabela(todos_arquivos)

    total_bytes = sum(x[2] for x in todos_arquivos)
    lbl_status.config(text=f"✅ {len(todos_arquivos)} Arquivos | Total: {formatar_tamanho(total_bytes)}")
    progress_bar['value'] = 100

def preencher_tabela(arquivos):
    limpar_tabela()
    for nome, caminho, tamanho, data in arquivos:
        extensao = os.path.splitext(nome)[1]
        tree.insert("", "end", values=(nome, "Arquivo", extensao or "-", 
                                       formatar_tamanho(tamanho),
                                       datetime.fromtimestamp(data).strftime("%d/%m/%Y %H:%M:%S"), 
                                       caminho))

def limpar_tabela():
    for item in tree.get_children():
        tree.delete(item)

def configurar_progresso_verde():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("green.Horizontal.TProgressbar", foreground=COR_VERDE, background=COR_VERDE, 
                    troughcolor='#555555', thickness=20)

def calcular_hash_arquivo(caminho):
    try:
        sha256 = hashlib.sha256()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None

def calcular_hash():
    item = tree.focus()
    if not item:
        messagebox.showwarning("Atenção", "Selecione um arquivo para calcular o hash!")
        return
    
    caminho = tree.item(item)["values"][5]
    if not os.path.exists(caminho):
        messagebox.showerror("Erro", "Arquivo não encontrado!")
        return

    lbl_status.config(text="🔄 Calculando SHA-256...")
    hash_label.config(text="Calculando...")
    janela.update()

    hash_file = calcular_hash_arquivo(caminho)
    if hash_file:
        hash_label.config(text=hash_file)
        lbl_status.config(text="✅ Hash SHA-256 calculado com sucesso")
    else:
        hash_label.config(text="Erro ao calcular hash")
        lbl_status.config(text="❌ Erro ao calcular hash")

def copiar_hash():
    hash_atual = hash_label.cget("text")
    if hash_atual and hash_atual not in ["Calculando...", "Selecione um arquivo e clique em Calcular Hash", "Erro ao calcular hash"]:
        janela.clipboard_clear()
        janela.clipboard_append(hash_atual)
        janela.update()
        lbl_status.config(text="✅ Hash copiado para a área de transferência!")
    else:
        messagebox.showwarning("Atenção", "Não há hash para copiar!")

def scan_virustotal(caminho):
    if not os.path.exists(caminho):
        messagebox.showerror("Erro", "Arquivo não Encontrado!")
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
        messagebox.showwarning("Atenção", "Selecione um Arquivo!")
        return
    caminho = tree.item(item)["values"][5]
    threading.Thread(target=scan_virustotal, args=(caminho,), daemon=True).start()

def mudar_pasta(caminho):
    global pasta_atual
    pasta_atual = caminho
    entrada_pasta.delete(0, tk.END)
    entrada_pasta.insert(0, pasta_atual)
    atualizar_label_pasta()
    analisar_pasta()

def adicionar_pasta_personalizada():
    pasta = filedialog.askdirectory(title="Selecione uma pasta personalizada")
    if pasta:
        mudar_pasta(pasta)

def abrir_arquivo(event=None):
    item = tree.focus()
    if item:
        caminho = tree.item(item)["values"][5]
        if os.path.exists(caminho):
            os.startfile(caminho)

def excluir_arquivo():
    item = tree.focus()
    if not item: 
        messagebox.showwarning("Atenção", "Selecione um Arquivo!")
        return
    dados = tree.item(item)["values"]
    if messagebox.askyesno("Confirmar", f"Excluir {dados[0]}?"):
        try:
            os.remove(dados[5])
            analisar_pasta()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

def excluir_todos():
    if messagebox.askyesno("⚠️ CUIDADO", "Excluir TODOS os Arquivos da Pasta?"):
        count = 0
        for f in os.listdir(pasta_atual):
            try:
                os.remove(os.path.join(pasta_atual, f))
                count += 1
            except:
                pass
        messagebox.showinfo("Pronto", f"{count} Arquivos Excluídos.")
        analisar_pasta()

def buscar_arquivos():
    termo = entrada_busca.get().strip().lower()
    if not termo:
        preencher_tabela(todos_arquivos)
        return
    filtrados = [arq for arq in todos_arquivos if termo in arq[0].lower()]
    preencher_tabela(filtrados)
    lbl_status.config(text=f"🔎 {len(filtrados)} Arquivos Encontrados: {termo}")

# ==================== INTERFACE ====================
janela = tk.Tk()
janela.title("Analisador de Downloads - Chrome / Firefox / Edge + Pastas Personalizadas + VirusTotal")
janela.geometry("1400x760")
janela.state("zoomed")
janela.configure(bg=COR_BG)

lbl_pasta = tk.Label(janela, text="", bg="#1e1e1e", fg="#00ffcc", font=("Arial", 11, "bold"), anchor="w")
lbl_pasta.pack(fill="x", padx=10, pady=8)

progress_bar = ttk.Progressbar(janela, mode='determinate')
progress_bar.pack(fill="x", padx=10, pady=5)

# Frame Pasta
frame1 = tk.Frame(janela, bg=COR_BG)
frame1.pack(fill="x", padx=10, pady=5)

entrada_pasta = tk.Entry(frame1, font=("Arial", 10))
entrada_pasta.pack(side="left", fill="x", expand=True, padx=(0,5))
entrada_pasta.insert(0, pasta_atual)

tk.Button(frame1, text="Selecionar Pasta", command=selecionar_pasta,
          bg="#07BDF5", fg="black", width=15, font=("Arial", 10, "bold")).pack(side="left", padx=4)

tk.Button(frame1, text="Analisar", command=analisar_pasta,
          bg="#08D47F", fg="black", width=12, font=("Arial", 10, "bold")).pack(side="left", padx=4)

tk.Button(frame1, text="Abrir Pasta", 
          command=lambda: os.startfile(pasta_atual) if os.path.exists(pasta_atual) else None,
          bg="#E6E21E", fg="black", width=12, font=("Arial", 10, "bold")).pack(side="left", padx=4)

# ==================== BOTÕES DE PERFIS ====================
frame_pastas = tk.Frame(janela, bg=COR_BG)
frame_pastas.pack(fill="x", padx=10, pady=2)

# Botões padrão
tk.Button(frame_pastas, text="📁 Chrome Downloads", 
          command=lambda: mudar_pasta(PASTA_PADRAO_CHROME), 
          bg="#08BE57", fg="black", width=20, font=("Arial", 10, "bold")).pack(side="left", padx=4)

tk.Button(frame_pastas, text="📁 Firefox Cache", 
          command=lambda: mudar_pasta(PASTA_PADRAO_FIREFOX), 
          bg="#FA4B4B", fg="black", width=20, font=("Arial", 10, "bold")).pack(side="left", padx=4)

# Botões Edge
for nome_perfil, caminho in EDGE_PROFILES:
    btn_text = f"📁 Edge - {nome_perfil}"
    tk.Button(frame_pastas, text=btn_text, 
              command=lambda c=caminho: mudar_pasta(c), 
              bg="#0078D4", fg="black", width=22, font=("Arial", 10, "bold")).pack(side="left", padx=4)

# ==================== BOTÃO NOVA PASTA PERSONALIZADA ====================
tk.Button(frame_pastas, text="➕ Adicionar Pasta Personalizada", 
          command=adicionar_pasta_personalizada,
          bg="#FF8800", fg="black", width=25, font=("Arial", 10, "bold")).pack(side="left", padx=4)

# Frame Busca
frame2 = tk.Frame(janela, bg=COR_BG)
frame2.pack(fill="x", padx=10, pady=5)

tk.Label(frame2, text="Pesquisar:", bg=COR_BG, fg=COR_FG).pack(side="left", padx=(0,5))
entrada_busca = tk.Entry(frame2, font=("Arial", 10))
entrada_busca.pack(side="left", fill="x", expand=True, padx=(0,5))
entrada_busca.bind("<Return>", lambda e: buscar_arquivos())

tk.Button(frame2, text="🔎 Buscar", command=buscar_arquivos,
          bg=COR_BOTOES, fg="black", width=12, font=("Arial", 10, "bold")).pack(side="left", padx=4)

lbl_status = tk.Label(janela, text="", bg=COR_BG, fg="#00ff88", font=("Arial", 10, "bold"))
lbl_status.pack(fill="x", padx=10, pady=5)

# ==================== TREEVIEW ====================
frame_tree = tk.Frame(janela)
frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

tree = ttk.Treeview(
    frame_tree,
    columns=("Nome", "Tipo", "Extensão", "Tamanho", "Data", "Caminho"),
    show="headings"
)

tree.heading("Nome", text="Nome do Arquivo")
tree.heading("Tipo", text="Tipo")
tree.heading("Extensão", text="Extensão")
tree.heading("Tamanho", text="Tamanho")
tree.heading("Data", text="Data")
tree.heading("Caminho", text="Caminho Completo")

tree.column("Nome", width=400, minwidth=400)
tree.column("Tipo", width=80, minwidth=60)
tree.column("Extensão", width=100, minwidth=70)
tree.column("Tamanho", width=120, minwidth=90)
tree.column("Data", width=160, minwidth=140)
tree.column("Caminho", width=900, minwidth=900, stretch=True)

scroll_y = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=tree.xview)

tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

frame_tree.rowconfigure(0, weight=1)
frame_tree.columnconfigure(0, weight=1)

tree.bind("<Double-1>", abrir_arquivo)

# ==================== BOTÕES INFERIORES ====================
frame3 = tk.Frame(janela, bg=COR_BG)
frame3.pack(fill="x", padx=10, pady=10)

tk.Button(frame3, text="🗑️ Excluir TODOS", command=excluir_todos, 
          bg=COR_DELETAR, fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=2)

tk.Button(frame3, text="🔍 VirusTotal", command=scan_selecionado, 
          bg=COR_LARANJA, fg="black", font=("Arial", 9, "bold")).pack(side="right", padx=5)

# ==================== FRAME HASH ====================
frame_hash = tk.LabelFrame(janela, text="HASH (SHA-256)", bg=COR_BG, fg=COR_FG, font=("Arial", 10, "bold"))
frame_hash.pack(fill="x", padx=10, pady=8)

hash_label = tk.Label(frame_hash, text="Selecione um arquivo e clique em Calcular Hash", 
                     bg="#2d2d2d", fg="#00ff88", font=("Consolas", 9), wraplength=1200, justify="left")
hash_label.pack(fill="x", padx=10, pady=5)

btn_frame = tk.Frame(frame_hash, bg=COR_BG)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="🔐 Calcular Hash SHA-256", command=calcular_hash,
          bg="#249E06", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=5)

tk.Button(btn_frame, text="📋 Copiar Hash", command=copiar_hash,
          bg="#0066cc", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=5)

# ==================== RODAPÉ ====================
frame_rodape = tk.Frame(janela, bg="#1e1e1e")
frame_rodape.pack(fill="x", side="bottom", padx=10, pady=10)

tk.Label(frame_rodape, text="Análise de Downloads/Cache • Pastas Personalizadas • VirusTotal • SHA-256 Hash", 
         bg="#1e1e1e", fg="#57DF08", font=("Arial", 9)).pack(pady=5)

# Inicialização
atualizar_label_pasta()
analisar_pasta()

janela.mainloop()
