import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

# ========================================================= 
# VARIÁVEIS GLOBAIS
# =========================================================

todos_logs = []

# =========================================================
# CONFIGURAÇÕES
# =========================================================

EXTENSOES = (".log", ".etl", ".evtx", ".txt", ".dmp", ".cab")

PASTAS_LOGS = [
    r"C:\Windows\System32\winevt\Logs",
    r"C:\Windows\Logs",
    r"C:\Windows\Panther",
    r"C:\Windows\INF",
    r"C:\Windows\debug",
    r"C:\Windows\System32\LogFiles",
]

IGNORAR = ["WinSxS", "Temp", "$Recycle.Bin", "System Volume Information"]

# =========================================================
# JANELA PRINCIPAL - ESTILO HACKER
# =========================================================

root = tk.Tk()
root.title("█ MONITØR DE LØGS WINDOWS █")
root.state("zoomed")
root.configure(bg="#0a0a0a")

# Estilo Hacker Verde
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#0a0a0a", foreground="#00ff41", fieldbackground="#0a0a0a", font=("Consolas", 10))
style.configure("Treeview.Heading", background="#00aa00", foreground="#000000", font=("Consolas", 10, "bold"))
style.map("Treeview", background=[('selected', '#003300')], foreground=[('selected', '#00ff41')])

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_tamanho(bytes_size):
    try:
        if bytes_size >= 1024 ** 3:
            return f"{bytes_size / (1024 ** 3):.2f} GB"
        elif bytes_size >= 1024 ** 2:
            return f"{bytes_size / (1024 ** 2):.2f} MB"
        elif bytes_size >= 1024:
            return f"{bytes_size / 1024:.2f} KB"
        return f"{bytes_size} Bytes"
    except:
        return "0 Bytes"

def data_arquivo(caminho):
    try:
        dt = datetime.fromtimestamp(os.path.getmtime(caminho))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return "Desconhecida"

def formatar_data_hora_iso(iso_str):
    try:
        iso_str = iso_str.rstrip("Z").split('.')[0]
        dt = datetime.fromisoformat(iso_str)
        return f"Data: {dt.strftime('%d/%m/%Y')}    Hora: {dt.strftime('%H:%M')}"
    except:
        return iso_str

def processar_eventos(saida):
    linhas = saida.splitlines()
    novas_linhas = []
    for linha in linhas:
        if linha.strip().startswith("Date:"):
            iso_ts = linha.split("Date:")[1].strip()
            linha = formatar_data_hora_iso(iso_ts)
        novas_linhas.append(linha)
    return "\n".join(novas_linhas)

# =========================================================
# PESQUISA
# =========================================================

def pesquisar_logs():
    termo = entrada_pesquisa.get().lower().strip()
    tree.delete(*tree.get_children())

    if not termo:
        limpar_pesquisa()
        return

    encontrados = 0
    for item in todos_logs:
        texto_completo = " ".join(map(str, item)).lower()
        if termo in texto_completo:
            tree.insert("", tk.END, values=item)
            encontrados += 1

    status_var.set(f"► PESQUISA: {encontrados} resultados encontrados")

def limpar_pesquisa():
    entrada_pesquisa.delete(0, tk.END)
    tree.delete(*tree.get_children())
    for item in todos_logs:
        tree.insert("", tk.END, values=item)
    status_var.set(f"► {len(todos_logs)} logs carregados | Ordenado por tamanho")

# =========================================================
# CARREGAR LOGS (Thread) - Ordenado por tamanho
# =========================================================

def thread_logs():
    global todos_logs
    todos_logs.clear()
    tree.delete(*tree.get_children())

    contador = 0
    total_bytes = 0
    logs_temp = []

    for pasta_base in PASTAS_LOGS:
        if not os.path.exists(pasta_base):
            continue

        for raiz, dirs, arquivos in os.walk(pasta_base):
            dirs[:] = [d for d in dirs if d not in IGNORAR]

            for arquivo in arquivos:
                if not arquivo.lower().endswith(EXTENSOES):
                    continue

                try:
                    caminho = os.path.join(raiz, arquivo)
                    tamanho_bytes = os.path.getsize(caminho)
                    total_bytes += tamanho_bytes

                    tamanho_formatado = formatar_tamanho(tamanho_bytes)
                    data_txt = data_arquivo(caminho)

                    dados = (arquivo, caminho, tamanho_formatado, data_txt, tamanho_bytes)
                    logs_temp.append(dados)

                    contador += 1

                    if contador % 80 == 0:
                        status_var.set(f"► ESCANEANDO... {contador} logs | {formatar_tamanho(total_bytes)}")
                        root.update_idletasks()

                except:
                    pass

    # Ordenar por tamanho (maior primeiro)
    logs_temp.sort(key=lambda x: x[4], reverse=True)

    for item in logs_temp:
        dados_display = item[:4]
        todos_logs.append(dados_display)
        tree.insert("", tk.END, values=dados_display)

    total_mb = round(total_bytes / (1024 * 1024), 2)
    status_var.set(f"► FINALIZADO | {contador} logs | Total: {total_mb} MB | Ordenado por tamanho (↓)")


def carregar_logs():
    status_var.set("► INICIANDO VARREDURA NO SISTEMA...")
    t = threading.Thread(target=thread_logs, daemon=True)
    t.start()

# =========================================================
# OUTRAS FUNÇÕES
# =========================================================

def abrir_arquivo(caminho):
    try:
        subprocess.run(['explorer', '/select,', caminho])
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def duplo_clique(event):
    item = tree.selection()
    if item:
        caminho = tree.item(item[0], "values")[1]
        abrir_arquivo(caminho)

def apagar_logs():
    if not messagebox.askyesno("CONFIRMAÇÃO", "Deseja realmente apagar os logs System e Application?"):
        return
    try:
        status_var.set("► APAGANDO LOGS...")
        subprocess.run(["wevtutil", "cl", "System"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["wevtutil", "cl", "Application"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status_var.set("► LOGS APAGADOS COM SUCESSO")
        messagebox.showinfo("SUCESSO", "Logs apagados.")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def definir_tamanho_logs():
    dialog = tk.Toplevel(root)
    dialog.title("LIMITAR TAMANHO DOS LOGS")
    dialog.geometry("420x300")
    dialog.configure(bg="#0a0a0a")
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog, text="DEFINIR TAMANHO MÁXIMO", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 12, "bold")).pack(pady=15)
    tk.Label(dialog, text="Ex: 5 = 5MB | 50 = 50MB | 100 = 100MB", bg="#0a0a0a", fg="#00aa00", font=("Consolas", 10)).pack(pady=5)

    entry = tk.Entry(dialog, font=("Consolas", 16), width=12, justify="center", bg="#111111", fg="#00ff41", insertbackground="#00ff41")
    entry.pack(pady=15)
    entry.focus()

    def confirmar():
        try:
            mb = int(entry.get().strip())
            if mb < 1 or mb > 1024:
                messagebox.showwarning("Atenção", "Valor entre 1 e 1024!")
                return
            bytes_size = mb * 1024 * 1024
            status_var.set(f"► LIMITANDO LOGS PARA {mb} MB...")
            subprocess.run(["wevtutil", "sl", "Application", f"/ms:{bytes_size}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["wevtutil", "sl", "System", f"/ms:{bytes_size}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status_var.set(f"► LOGS LIMITADOS PARA {mb} MB")
            messagebox.showinfo("SUCESSO", f"Application e System limitados para {mb} MB.")
            dialog.destroy()
        except:
            messagebox.showerror("Erro", "Digite apenas números!")

    btn_frame = tk.Frame(dialog, bg="#0a0a0a")
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="CONFIRMAR", bg="#00aa00", fg="black", font=("Consolas", 10, "bold"), width=12, command=confirmar).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="CANCELAR", bg="#aa0000", fg="white", font=("Consolas", 10, "bold"), width=12, command=dialog.destroy).pack(side=tk.LEFT, padx=10)

def ver_config_logs():
    try:
        text_area.delete("1.0", tk.END)
        app = subprocess.check_output(["wevtutil", "gl", "Application"], text=True)
        sys = subprocess.check_output(["wevtutil", "gl", "System"], text=True)
        texto = f"""============================================================
CONFIG APPLICATION
============================================================
{app}
============================================================
CONFIG SYSTEM
============================================================
{sys}"""
        text_area.insert(tk.END, texto)
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def carregar_eventos():
    text_area.delete("1.0", tk.END)
    try:
        arquivos_logs = [
            r"C:\Windows\System32\winevt\Logs\Application.evtx",
            r"C:\Windows\System32\winevt\Logs\System.evtx"
        ]
        info_logs = ""
        for arq in arquivos_logs:
            if os.path.exists(arq):
                info_logs += f"{arq}\nTAMANHO: {formatar_tamanho(os.path.getsize(arq))}\nDATA: {data_arquivo(arq)}\n{'='*60}\n"

        cmd = lambda log: ["wevtutil", "qe", log, "/c:20", "/f:text", "/q:*[System[(Level=2 or Level=3)]]"]
        
        saida_sys = subprocess.check_output(cmd("System"), text=True, stderr=subprocess.DEVNULL)
        saida_app = subprocess.check_output(cmd("Application"), text=True, stderr=subprocess.DEVNULL)

        texto = f"""============================================================
ÚLTIMOS EVENTOS (ERRO/AVISO)
============================================================
{info_logs}
SYSTEM:\n{processar_eventos(saida_sys)}
{'='*60}
APPLICATION:\n{processar_eventos(saida_app)}"""
        text_area.insert(tk.END, texto)
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def salvar():
    arquivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
    if not arquivo: return
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(text_area.get("1.0", tk.END))
            f.write("\n\n" + "="*60 + "\nTODOS OS LOGS (ORDENADOS POR TAMANHO)\n" + "="*60 + "\n\n")
            for item in todos_logs:
                f.write(f"ARQUIVO: {item[0]}\nCAMINHO: {item[1]}\nTAMANHO: {item[2]}\nDATA: {item[3]}\n{'-'*60}\n")
        messagebox.showinfo("SUCESSO", "Relatório salvo!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# =========================================================
# INTERFACE GRÁFICA
# =========================================================

frame_btn = tk.Frame(root, bg="#0a0a0a")
frame_btn.pack(pady=8)

buttons = [
    ("ABRIR MONITOR", "#03fc24", lambda: subprocess.Popen(["perfmon", "/rel"])),
    ("CARREGAR EVENTOS", "#03f0fc", carregar_eventos),
    ("PROCURAR TODOS LOGS", "#fc03f8", carregar_logs),
    ("SALVAR", "#fcd103", salvar),
    ("APAGAR LOGS", "#ff0000", apagar_logs),
    ("LIMITAR LOGS", "#0066ff", definir_tamanho_logs),
    ("VER CONFIG", "#5c00ff", ver_config_logs),
]

for text, color, cmd in buttons:
    tk.Button(frame_btn, text=text, bg=color, fg="black", font=("Consolas", 10, "bold"), 
              command=cmd).pack(side=tk.LEFT, padx=4)

# Pesquisa
frame_pesquisa = tk.Frame(root, bg="#0a0a0a")
frame_pesquisa.pack(fill="x", padx=10, pady=5)

tk.Label(frame_pesquisa, text="PESQUISAR:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11)).pack(side=tk.LEFT, padx=5)
entrada_pesquisa = tk.Entry(frame_pesquisa, font=("Consolas", 11), bg="#111111", fg="#00ff41", insertbackground="#00ff41")
entrada_pesquisa.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

tk.Button(frame_pesquisa, text="BUSCAR", bg="#00aa00", fg="black", font=("Consolas", 10, "bold"), command=pesquisar_logs).pack(side=tk.LEFT, padx=5)
tk.Button(frame_pesquisa, text="LIMPAR", bg="#ff8800", fg="black", font=("Consolas", 10, "bold"), command=limpar_pesquisa).pack(side=tk.LEFT, padx=5)

# Text Area
text_area = scrolledtext.ScrolledText(root, height=22, font=("Consolas", 10), bg="#000000", fg="#00ff41", insertbackground="#00ff41")
text_area.pack(fill="x", padx=10, pady=8)

# Treeview
frame_tabela = tk.Frame(root, bg="#0a0a0a")
frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)

tree = ttk.Treeview(frame_tabela, columns=("nome", "caminho", "tamanho", "data"), show="headings")
tree.heading("nome", text="ARQUIVO")
tree.heading("caminho", text="CAMINHO")
tree.heading("tamanho", text="TAMANHO")
tree.heading("data", text="DATA MODIFICAÇÃO")

tree.column("nome", width=700)
tree.column("caminho", width=900)
tree.column("tamanho", width=100)
tree.column("data", width=160)

scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
tree.pack(fill="both", expand=True)

tree.bind("<Double-1>", duplo_clique)

# Status
status_var = tk.StringVar(value="► PRØNTØ - AGUARDANDO COMANDO...")
status_label = tk.Label(root, textvariable=status_var, anchor="w", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 10, "bold"))
status_label.pack(fill="x")

# Texto inicial
text_area.insert(tk.END, """============================================================
     █ MONITØR DE LØGS WINDOWS v2.0 █
============================================================

• Pressione "PROCURAR TODOS LOGS" para iniciar
                 
• Arquivos ordenados do maior para o menor (GB → MB → KB)
                 
• Duplo clique para abrir o arquivo
                 
• Estilo Matrix ativado ✓
                 
""")

root.mainloop()
