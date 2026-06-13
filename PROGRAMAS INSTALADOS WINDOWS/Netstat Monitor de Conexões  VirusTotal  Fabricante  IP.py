# =========================================================
# MONITOR DE PROCESSOS COMPLETO + VIRUSTOTAL + FABRICANTE + IP
# =========================================================
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import subprocess
import psutil
from datetime import datetime
from tkinter import filedialog
import hashlib

# pywin32 para Fabricante
try:
    import win32api
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    

# =========================================================
# JANELA
# =========================================================
root = tk.Tk()
root.title("Netstat Monitor de Conexões  VirusTotal  Fabricante  IP")
root.geometry("1900x850")
root.state("zoomed")
root.configure(bg="#1e1e1e")

# =========================================================
# ESTILO
# =========================================================
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#252526", foreground="white",
                fieldbackground="#252526", rowheight=28, font=("Consolas", 10))
style.configure("Treeview.Heading", background="#00ff88", foreground="black",
                font=("Segoe UI", 10, "bold"))
style.map("Treeview", background=[("selected", "#094771")])

# =========================================================
# FRAME PRINCIPAL
# =========================================================
frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# =========================================================
# COLUNAS (Adicionada IP)
# =========================================================
columns = (
    "nome", "pid", "cpu", "memoria", "threads", "criado",
    "fabricante", "ip", "caminho"
)

arvore = ttk.Treeview(frame, columns=columns, show="headings")

for col in columns:
    arvore.heading(col, text=col.upper())

arvore.column("nome", width=260)
arvore.column("pid", width=80)
arvore.column("ip", width=350)
arvore.column("cpu", width=100)
arvore.column("memoria", width=110)
arvore.column("threads", width=80)
arvore.column("criado", width=160)
arvore.column("fabricante", width=250)
arvore.column("caminho", width=550)

# Scrollbars
style.configure("Vertical.TScrollbar", background="#00ff88", troughcolor="#1e1e1e",
                arrowcolor="black", darkcolor="#00cc66", lightcolor="#00ff88")

scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=arvore.yview, style="Vertical.TScrollbar")
scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=arvore.xview, style="Horizontal.TScrollbar")

arvore.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
arvore.pack(fill=tk.BOTH, expand=True)

# =========================================================
# VARIÁVEIS
# =========================================================
dados_processos = []
auto_refresh = tk.BooleanVar(value=True)
refresh_interval = 3000  # 3 segundos

# =========================================================
# FUNÇÕES
# =========================================================
def bytes_para_mb(valor):
    return f"{valor / 1024 / 1024:.2f} MB"

def get_fabricante(exe_path):
    if not PYWIN32_AVAILABLE or not exe_path or exe_path == "N/A":
        return "N/A"
    try:
        info = win32api.GetFileVersionInfo(exe_path, "\\")
        lang, codepage = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')[0]
        company = win32api.GetFileVersionInfo(exe_path, u'\\StringFileInfo\\%04x%04x\\CompanyName' % (lang, codepage))
        return str(company).strip() if company else "N/A"
    except:
        return "N/A"

def get_ips_do_processo(pid):
    """Retorna IPs/Portas que o processo está usando"""
    if not pid:
        return "N/A"
    try:
        conexoes = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.pid == pid:
                try:
                    ip = conn.laddr.ip
                    porta = conn.laddr.port
                    conexoes.append(f"{ip}:{porta}")
                except:
                    pass
        return ", ".join(conexoes[:3]) if conexoes else "N/A"  # Mostra até 3 conexões
    except:
        return "N/A"

def abrir_pasta(caminho):
    if caminho == "N/A":
        messagebox.showwarning("Caminho inválido", "Não foi possível localizar a pasta.")
        return
    try:
        pasta = os.path.dirname(caminho)
        subprocess.Popen(f'explorer "{pasta}"')
    except Exception as erro:
        messagebox.showerror("Erro", f"Erro ao abrir pasta:\n{erro}")

def abrir_virustotal(nome, caminho):
    if caminho == "N/A" or not os.path.exists(caminho):
        url = f"https://www.virustotal.com/gui/search/{nome}"
    else:
        try:
            with open(caminho, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            url = f"https://www.virustotal.com/gui/file/{file_hash}"
        except:
            url = f"https://www.virustotal.com/gui/search/{nome}"
    webbrowser.open(url)

# =========================================================
# CARREGAR PROCESSOS
# =========================================================
def carregar_processos():
    global dados_processos
    for item in arvore.get_children():
        arvore.delete(item)
    dados_processos = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info',
                                     'num_threads', 'create_time', 'exe']):
        try:
            info = proc.info
            pid = info['pid']
            nome = info['name'] or "Sem Nome"
            
            cpu = f"{info['cpu_percent']:.1f}%" if info['cpu_percent'] is not None else "N/A"
            memoria = bytes_para_mb(info['memory_info'].rss) if info['memory_info'] else "N/A"
            threads = info['num_threads'] or "N/A"
            
            criado = datetime.fromtimestamp(info['create_time']).strftime('%d/%m/%Y %H:%M:%S') if info['create_time'] else "N/A"
            
            caminho = info.get('exe') or "N/A"
            fabricante = get_fabricante(caminho)
            ip_info = get_ips_do_processo(pid)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        dados = (nome, pid, cpu, memoria, threads, criado, fabricante, ip_info, caminho)
        dados_processos.append(dados)
        arvore.insert("", tk.END, values=dados)

# =========================================================
# ATUALIZAÇÃO EM TEMPO REAL
# =========================================================
def atualizar_tempo_real():
    if auto_refresh.get():
        carregar_processos()
    root.after(refresh_interval, atualizar_tempo_real)

# =========================================================
# DUPLO CLIQUE
# =========================================================
def clique_duplo(event):
    item = arvore.selection()
    if not item:
        return
    valores = arvore.item(item[0], "values")
    coluna = arvore.identify_column(event.x)

    if coluna == "#1":        # Coluna NOME → VirusTotal
        abrir_virustotal(valores[0], valores[8])
    elif coluna == "#9":      # Coluna CAMINHO → Abrir Pasta
        abrir_pasta(valores[8])

arvore.bind("<Double-1>", clique_duplo)

# =========================================================
# FRAME DE BOTÕES
# =========================================================
frame_botoes = tk.Frame(root, bg="#1e1e1e")
frame_botoes.pack(fill=tk.X, padx=10, pady=8)

btn_atualizar = tk.Button(frame_botoes, text="Atualizar Agora", command=carregar_processos,
                          bg="#00ff88", fg="black", font=("Segoe UI", 10, "bold"),
                          padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
btn_atualizar.pack(side=tk.LEFT, padx=5)

chk_auto = tk.Checkbutton(frame_botoes, text="Atualização Automática (3s)", variable=auto_refresh,
                          bg="#1e1e1e", fg="#00ff88", selectcolor="#252526", font=("Segoe UI", 10))
chk_auto.pack(side=tk.LEFT, padx=15)

entrada_pesquisa = tk.Entry(frame_botoes, font=("Segoe UI", 11), width=45,
                            bg="#252526", fg="white", insertbackground="white", relief=tk.FLAT)
entrada_pesquisa.pack(side=tk.LEFT, padx=10, ipady=6)

def pesquisar():
    termo = entrada_pesquisa.get().lower().strip()
    for item in arvore.get_children():
        arvore.delete(item)
    
    if not termo:
        for item in dados_processos:
            arvore.insert("", tk.END, values=item)
        return
    
    for item in dados_processos:
        if termo in " ".join(str(c).lower() for c in item):
            arvore.insert("", tk.END, values=item)

btn_pesquisar = tk.Button(frame_botoes, text="Pesquisar", command=pesquisar,
                          bg="#ffd166", fg="black", font=("Segoe UI", 10, "bold"),
                          padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
btn_pesquisar.pack(side=tk.LEFT, padx=5)

# =========================================================
# SALVAR TXT (com IP)
# =========================================================
def salvar_txt():
    if not dados_processos:
        messagebox.showwarning("Sem dados", "Nenhum processo para salvar.")
        return
    arquivo = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Arquivo TXT", "*.txt")])
    if not arquivo:
        return
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("="*220 + "\n")
            f.write(f"RELATÓRIO COMPLETO DE PROCESSOS + IP - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("="*220 + "\n\n")
            for item in dados_processos:
                f.write(f"NOME       : {item[0]}\n")
                f.write(f"PID        : {item[1]}\n")
                f.write(f"CPU        : {item[2]}\n")
                f.write(f"MEMÓRIA    : {item[3]}\n")
                f.write(f"THREADS    : {item[4]}\n")
                f.write(f"CRIADO     : {item[5]}\n")
                f.write(f"FABRICANTE : {item[6]}\n")
                f.write(f"IP         : {item[7]}\n")          # ← IP adicionado aqui
                f.write(f"CAMINHO    : {item[8]}\n")
                f.write("-"*220 + "\n")

        messagebox.showinfo("Sucesso", "Relatório salvo com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

btn_salvar = tk.Button(frame_botoes, text="Salvar TXT", command=salvar_txt,
                       bg="#f74012", fg="black", font=("Segoe UI", 10, "bold"),
                       padx=15, pady=8, relief=tk.FLAT, cursor="hand2")
btn_salvar.pack(side=tk.LEFT, padx=5)

# Informação
info = tk.Label(root, 
    text="Duplo clique na coluna NOME → VirusTotal | Duplo clique na coluna CAMINHO → Abrir pasta",
    bg="#1e1e1e", fg="#dcdcaa", font=("Segoe UI", 10))
info.pack(pady=8)

# =========================================================
# INICIALIZAÇÃO
# =========================================================
carregar_processos()
root.after(1000, atualizar_tempo_real)

root.mainloop()
