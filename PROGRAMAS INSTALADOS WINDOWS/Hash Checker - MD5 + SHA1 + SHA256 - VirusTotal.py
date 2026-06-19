import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
import webbrowser
import os
from datetime import datetime
import threading
import time
import subprocess  # ← Adicionado para abrir pastas

# ===================== FUNÇÕES =====================

def calcular_hashes(caminho, indice, total_arquivos):
    try:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()

        tamanho_total = os.path.getsize(caminho)
        lido = 0

        with open(caminho, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break

                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)

                lido += len(chunk)
                progresso_arquivo = lido / tamanho_total
                progresso_total = ((indice + progresso_arquivo) / total_arquivos) * 100

                progress['value'] = progresso_total
                root.update_idletasks()

        return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()

    except Exception as e:
        print(f"Erro ao ler {caminho}: {e}")
        return None, None, None


def abrir_pasta(caminho):
    """Abre a pasta que contém o arquivo"""
    if not caminho:
        messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
        return
    try:
        pasta = os.path.dirname(caminho)
        if os.name == 'nt':  # Windows
            os.startfile(pasta)
        else:  # Linux / macOS
            subprocess.Popen(['xdg-open', pasta])
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir pasta:\n{str(e)}")


def processar_pasta(caminho_pasta):
    btn_selecionar.config(state="disabled")
    progress['value'] = 0

    arquivos = []
    for raiz, dirs, files in os.walk(caminho_pasta):
        for nome_arquivo in files:
            caminho_completo = os.path.join(raiz, nome_arquivo)
            arquivos.append(caminho_completo)

    total = len(arquivos)
    if total == 0:
        messagebox.showinfo("Aviso", "Nenhum arquivo encontrado na pasta!")
        btn_selecionar.config(state="normal")
        return

    for i, caminho in enumerate(arquivos):
        nome = os.path.basename(caminho)
        try:
            tamanho = f"{os.path.getsize(caminho) / (1024*1024):.2f} MB"
        except:
            tamanho = "N/A"

        md5_hash, sha1_hash, sha256_hash = calcular_hashes(caminho, i, total)
        
        if md5_hash and sha1_hash and sha256_hash:
            tree.insert("", "end", values=(nome, md5_hash, sha1_hash, sha256_hash, tamanho, caminho))
        
        progress['value'] = ((i + 1) / total) * 100
        root.update_idletasks()

        if total > 10:
            time.sleep(0.01)

    progress['value'] = 100
    btn_selecionar.config(state="normal")
    messagebox.showinfo("Concluído", f"{total} arquivo(s) processado(s) com sucesso!")


def selecionar_pasta():
    pasta = filedialog.askdirectory(title="Selecione uma pasta")
    if not pasta:
        return

    for item in tree.get_children():
        tree.delete(item)

    threading.Thread(target=processar_pasta, args=(pasta,), daemon=True).start()


def salvar_resultados():
    if not tree.get_children():
        messagebox.showwarning("Aviso", "Não há resultados para salvar!")
        return

    arquivo_salvar = filedialog.asksaveasfilename(
        title="Salvar resultados como...",
        defaultextension=".txt",
        filetypes=[("Arquivo TXT", "*.txt"), ("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")]
    )
    
    if not arquivo_salvar:
        return

    try:
        with open(arquivo_salvar, "w", encoding="utf-8") as f:
            f.write("=== HASH CHECKER - RESULTADOS ===\n\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("="*120 + "\n\n")
            
            for item in tree.get_children():
                valores = tree.item(item)['values']
                f.write(f"Nome do Arquivo : {valores[0]}\n")
                f.write(f"MD5            : {valores[1]}\n")
                f.write(f"SHA-1          : {valores[2]}\n")
                f.write(f"SHA-256        : {valores[3]}\n")
                f.write(f"Tamanho        : {valores[4]}\n")
                f.write(f"Caminho        : {valores[5]}\n")
                f.write("-" * 120 + "\n\n")
        
        messagebox.showinfo("Sucesso", f"Resultados salvos em:\n{arquivo_salvar}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")


def abrir_virus_total(hash_value):
    if not hash_value:
        messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
        return
    url = f"https://www.virustotal.com/gui/file/{hash_value}"
    webbrowser.open(url)


def on_double_click(event):
    """Duplo clique abre a pasta do arquivo"""
    item = tree.selection()
    if item:
        valores = tree.item(item[0])['values']
        abrir_pasta(valores[5])  # Caminho completo está na coluna 5


# ===================== INTERFACE =====================

root = tk.Tk()
root.title("Hash Checker - MD5 + SHA1 + SHA256 - VirusTotal")
root.geometry("1480x750")
root.state("zoomed")

style = ttk.Style()
style.theme_use('default')

# Scrollbar Vertical Grossa
style.configure("Vertical.TScrollbar", width=14, arrowsize=14)
style.map("Vertical.TScrollbar",
          background=[('active', "#3B3B3B"), ('!active', "#3D3D3D")],
          troughcolor=[('!active', "#A09F9F")])

style.configure("green.Horizontal.TProgressbar", background='#00FF00', troughcolor='#D3D3D3')

# Layout Superior
top_frame = tk.Frame(root)
top_frame.pack(pady=10, padx=10, fill="x")

tk.Label(top_frame, text="Hash Checker (MD5 + SHA-1 + SHA256) + VirusTotal", 
         font=("Arial", 16, "bold")).pack(side="left")

btn_selecionar = tk.Button(top_frame, text="📁 Selecionar Pasta", 
                           command=selecionar_pasta, bg="#13F71B", 
                           font=("Arial", 10, "bold"), fg="black", padx=15)
btn_selecionar.pack(side="right", padx=5)

# Progresso
progress_frame = tk.Frame(root)
progress_frame.pack(pady=5, padx=10, fill="x")
tk.Label(progress_frame, text="Progresso:", font=("Arial", 10)).pack(side="left", padx=5)
progress = ttk.Progressbar(progress_frame, style="green.Horizontal.TProgressbar", 
                           orient="horizontal", length=900, mode="determinate")
progress.pack(side="left", padx=5, fill="x", expand=True)

# ==================== TABELA COM SCROLLBAR ====================
table_frame = tk.Frame(root)
table_frame.pack(pady=10, padx=10, fill="both", expand=True)

columns = ("Nome", "MD5", "SHA1", "SHA256", "Tamanho", "Caminho")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=22)

tree.heading("Nome", text="Nome do Arquivo")
tree.column("Nome", width=440, anchor="w", minwidth=150)
tree.heading("MD5", text="MD5")
tree.column("MD5", width=280, anchor="w", minwidth=260)
tree.heading("SHA1", text="SHA-1")
tree.column("SHA1", width=290, anchor="w", minwidth=260)
tree.heading("SHA256", text="SHA-256")
tree.column("SHA256", width=460, anchor="w", minwidth=400)
tree.heading("Tamanho", text="Tamanho")
tree.column("Tamanho", width=100, anchor="center")
tree.heading("Caminho", text="Caminho Completo")
tree.column("Caminho", width=1000, anchor="w", minwidth=200)

tree.grid(row=0, column=0, sticky="nsew")

# Scrollbar Vertical
scrollbar_v = ttk.Scrollbar(table_frame, orient="vertical", 
                           command=tree.yview, style="Vertical.TScrollbar")
tree.configure(yscrollcommand=scrollbar_v.set)
scrollbar_v.grid(row=0, column=1, sticky="ns")

table_frame.columnconfigure(0, weight=1)
table_frame.rowconfigure(0, weight=1)

# Scrollbar Horizontal - Cor Cinza Escuro
style.configure("Horizontal.TScrollbar", 
                width=14,           # altura da barra horizontal
                arrowsize=14)

style.map("Horizontal.TScrollbar",
          background=[('active', "#1B1B1B"), ('!active', "#302F2F")],
          troughcolor=[('!active', "#BDBDBD")])

# ==================== Scrollbar Horizontal ====================
scrollbar_h = ttk.Scrollbar(root, orient="horizontal", 
                           command=tree.xview, 
                           style="Horizontal.TScrollbar")
tree.configure(xscrollcommand=scrollbar_h.set)
scrollbar_h.pack(side="bottom", fill="x", padx=10)

# ==================== BOTÕES ====================
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="🌐 Abrir VirusTotal (SHA256)", bg="#0BEB0B", fg="black", 
          font=("Arial", 10, "bold"), 
          command=lambda: abrir_virus_total(tree.item(tree.selection()[0])['values'][3] if tree.selection() else None)
         ).pack(side="left", padx=8)

# Novo botão: Abrir Pasta
tk.Button(btn_frame, text="📂 Abrir Pasta", bg="#09EBF3", fg="black", 
          font=("Arial", 10, "bold"), padx=12,
          command=lambda: abrir_pasta(tree.item(tree.selection()[0])['values'][5] if tree.selection() else None)
         ).pack(side="left", padx=8)

tk.Button(btn_frame, text="💾 Salvar Todos os Resultados", bg="#E26C0B", fg="black", 
          font=("Arial", 10, "bold"), padx=12, command=salvar_resultados).pack(side="left", padx=8)

tk.Label(root, text="Duplo clique na linha → abre a pasta do arquivo   |   Selecione  Hash SHA-256 Abrir VirusTotal", 
         fg="blue", font=("Arial", 9)).pack(pady=5)

tree.bind("<Double-1>", on_double_click)

root.mainloop()
