import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
from datetime import datetime
import threading
import pyperclip

# Variável global de controle
stop_flag = False

def calcular_hashes(senha):
    return {
        'MD5': hashlib.md5(senha.encode('utf-8')).hexdigest(),
        'SHA1': hashlib.sha1(senha.encode('utf-8')).hexdigest(),
        'SHA256': hashlib.sha256(senha.encode('utf-8')).hexdigest(),
        'SHA512': hashlib.sha512(senha.encode('utf-8')).hexdigest()
    }

def carregar_senhas(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return [linha.strip() for linha in f if linha.strip()]
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler arquivo:\n{str(e)}")
        return []

# ======================= COPIAR COM DUAS CLICS =======================
def copiar_item(event):
    try:
        item = tree.selection()[0]
        valores = tree.item(item, "values")
        coluna = tree.identify_column(event.x)
        col_index = int(coluna.replace("#", "")) - 1
        
        texto = valores[col_index]
        pyperclip.copy(texto)
        
        root.after(0, lambda: lbl_status.config(text=f"✅ COPIADO: {texto[:30]}...", fg="#00ff41"))
        root.after(1500, lambda: lbl_status.config(text=f"✅ {len(resultados)} resultados carregados", fg="#00ff41"))
    except:
        pass

def processar_thread():
    global stop_flag
    stop_flag = False
    
    if not senhas:
        return

    resultados.clear()
    tree.delete(*tree.get_children())
    total = len(senhas)

    for i, senha in enumerate(senhas):
        if stop_flag:
            root.after(0, lambda: lbl_progress.config(text="⛔ PROCESSO INTERROMPIDO PELO USUÁRIO"))
            root.after(0, lambda: messagebox.showinfo("Parado", "Processamento interrompido."))
            root.after(0, lambda: btn_processar.config(state="normal"))
            root.after(0, lambda: btn_stop.config(state="disabled"))
            return

        hashes = calcular_hashes(senha)
        resultados.append((senha, hashes))
        
        root.after(0, lambda s=senha, h=hashes: 
            tree.insert("", "end", values=(s, h['MD5'], h['SHA1'], h['SHA256'], h['SHA512'])))
        
        progresso = int(((i + 1) / total) * 100)
        root.after(0, lambda p=progresso: progress_bar.configure(value=p))
        root.after(0, lambda p=progresso, idx=i+1: 
            lbl_progress.config(text=f"Processando... {p}% ({idx}/{total})"))

    # Finalizado normalmente
    root.after(0, lambda: lbl_progress.config(text=f"✅ CONCLUÍDO! {total} SENHAS PROCESSADAS."))
    root.after(0, lambda: messagebox.showinfo("Sucesso", f"Processamento finalizado!"))
    root.after(0, lambda: btn_processar.config(state="normal"))
    root.after(0, lambda: btn_stop.config(state="disabled"))

def processar():
    global stop_flag
    stop_flag = False
    btn_processar.config(state="disabled")
    btn_stop.config(state="normal")
    progress_bar.configure(value=0)
    lbl_progress.config(text="INICIANDO PROCESSAMENTO...")
    
    threading.Thread(target=processar_thread, daemon=True).start()

def stop_processamento():
    global stop_flag
    stop_flag = True
    lbl_progress.config(text="⛔ PARANDO... AGUARDE")
    btn_stop.config(state="disabled")

def salvar_arquivo():
    if not resultados:
        messagebox.showwarning("Aviso", "Nada para salvar!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
    if path:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Hashes gerados em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
                for senha, h in resultados:
                    f.write(f"Senha: {senha}\n\n")
                    f.write(f"MD5     : {h['MD5']}\n")
                    f.write(f"SHA1    : {h['SHA1']}\n")
                    f.write(f"SHA256  : {h['SHA256']}\n")
                    f.write(f"SHA512  : {h['SHA512']}\n")
                    f.write("-" * 100 + "\n")
            messagebox.showinfo("Sucesso", "Arquivo salvo!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

def selecionar_arquivo():
    global senhas
    arq = filedialog.askopenfilename(title="Abrir arquivo de senhas", filetypes=[("TXT", "*.txt")])
    if arq:
        senhas = carregar_senhas(arq)
        lbl_status.config(text=f"✅ {len(senhas)} SENHAS CARREGADAS")
        btn_processar.config(state="normal")

def pesquisar():
    termo = entry_pesquisa.get().strip().lower()
    tree.delete(*tree.get_children())
    for senha, hashes in resultados:
        if (termo in senha.lower() or 
            termo in hashes['MD5'].lower() or 
            termo in hashes['SHA1'].lower() or 
            termo in hashes['SHA256'].lower() or 
            termo in hashes['SHA512'].lower()):
            tree.insert("", "end", values=(senha, hashes['MD5'], hashes['SHA1'], hashes['SHA256'], hashes['SHA512']))

def limpar_pesquisa():
    entry_pesquisa.delete(0, tk.END)
    tree.delete(*tree.get_children())
    for senha, hashes in resultados:
        tree.insert("", "end", values=(senha, hashes['MD5'], hashes['SHA1'], hashes['SHA256'], hashes['SHA512']))

# ======================= GUI =======================
root = tk.Tk()
root.title("HASH CONVERTER")
root.geometry("1480x880")
root.state("zoomed")
root.configure(bg="#0a0a0a")
root.resizable(True, True)

senhas = []
resultados = []

font_title = ("Courier New", 18, "bold")
font_text = ("Courier New", 10)

# Título
tk.Label(root, text="╔═╗ HACKER HASH CONVERTER ═╗\nMD5 | SHA1 | SHA256 | SHA512", 
         font=font_title, fg="#00ff41", bg="#0a0a0a").pack(pady=12)

# ======================= BOTÕES =======================
frame_top = tk.Frame(root, bg="#0a0a0a")
frame_top.pack(fill="x", padx=20, pady=8)

btn_select = tk.Button(frame_top, text="📂 SELECIONAR .TXT", command=selecionar_arquivo,
                       width=20, height=2, bg="#003300", fg="#00ff41", activebackground="#00aa00",
                       font=font_text, relief="ridge", bd=3)
btn_select.pack(side="left", padx=5)

btn_processar = tk.Button(frame_top, text="🔄 PROCESSAR", command=processar,
                          width=18, height=2, bg="#004400", fg="#00c3ff", activebackground="#00cc00",
                          font=font_text, relief="ridge", bd=3, state="disabled")
btn_processar.pack(side="left", padx=5)

btn_save = tk.Button(frame_top, text="💾 SALVAR", command=salvar_arquivo,
                     width=18, height=2, bg="#002200", fg="#e76b06", activebackground="#00bb00",
                     font=font_text, relief="ridge", bd=3)
btn_save.pack(side="left", padx=5)

# BOTÃO STOP (melhorado)
btn_stop = tk.Button(frame_top, text="⛔ STOP", command=stop_processamento,
                     width=14, height=2, bg="#880000", fg="#ffffff", activebackground="#ff0000",
                     font=("Courier New", 10, "bold"), relief="ridge", bd=3, state="disabled")
btn_stop.pack(side="left", padx=5)

# Pesquisa (mantido igual)
frame_search = tk.Frame(root, bg="#0a0a0a")
frame_search.pack(fill="x", padx=20, pady=8)

tk.Label(frame_search, text="🔍 PESQUISAR:", fg="#00ff41", bg="#0a0a0a", font=("Courier New", 11, "bold")).pack(side="left", padx=(0,8))

entry_pesquisa = tk.Entry(frame_search, width=50, font=font_text, bg="#001100", fg="#00ff41", insertbackground="#00ff41")
entry_pesquisa.pack(side="left", padx=5, fill="x", expand=True)

btn_search = tk.Button(frame_search, text="BUSCAR", command=pesquisar,
                       bg="#005500", fg="#00ff41", activebackground="#00aa00", font=font_text, relief="ridge", bd=3, width=12)
btn_search.pack(side="left", padx=5)

btn_clear = tk.Button(frame_search, text="LIMPAR", command=limpar_pesquisa,
                      bg="#330000", fg="#ff4444", activebackground="#aa0000", font=font_text, relief="ridge", bd=3, width=10)
btn_clear.pack(side="left", padx=5)

lbl_status = tk.Label(frame_search, text="NENHUM ARQUIVO CARREGADO", fg="#00ff41", bg="#0a0a0a", font=font_text)
lbl_status.pack(side="right", padx=10)

# Progresso
frame_prog = tk.Frame(root, bg="#0a0a0a")
frame_prog.pack(fill="x", padx=20, pady=8)

lbl_progress = tk.Label(frame_prog, text="PRONTO PARA HACKEAR", fg="#00ff41", bg="#0a0a0a", font=("Courier New", 11, "bold"))
lbl_progress.pack()

progress_bar = ttk.Progressbar(frame_prog, length=1300, mode="determinate")
progress_bar.pack(pady=8)

# Estilo
style = ttk.Style()
style.theme_use('default')
style.configure("TProgressbar", background="#00ff41", troughcolor="#001100", thickness=22)
style.configure("Treeview", background="#0a0a0a", foreground="#00ff41", fieldbackground="#0a0a0a", font=("Courier New", 10))
style.configure("Treeview.Heading", background="#003300", foreground="#00ff88", font=("Courier New", 11, "bold"))
style.map("Treeview", background=[('selected', '#003300')])

# Tabela
frame_tabela = tk.Frame(root, bg="#0a0a0a")
frame_tabela.pack(fill="both", expand=True, padx=20, pady=10)

columns = ("Senha", "MD5", "SHA1", "SHA256", "SHA512")

vsb = ttk.Scrollbar(frame_tabela, orient="vertical")
hsb = ttk.Scrollbar(frame_tabela, orient="horizontal")

tree = ttk.Treeview(frame_tabela, columns=columns, show="headings",
                    yscrollcommand=vsb.set, xscrollcommand=hsb.set, style="Treeview")

vsb.config(command=tree.yview)
hsb.config(command=tree.xview)

tree.heading("Senha", text="SENHA")
tree.heading("MD5", text="MD5")
tree.heading("SHA1", text="SHA1")
tree.heading("SHA256", text="SHA256")
tree.heading("SHA512", text="SHA512")

tree.column("Senha", width=310, minwidth=310, anchor="w")
tree.column("MD5", width=315, minwidth=315, anchor="w")
tree.column("SHA1", width=375, minwidth=375, anchor="w")
tree.column("SHA256", width=565, minwidth=565, anchor="w")
tree.column("SHA512", width=1065, minwidth=1065, anchor="w")

tree.bind("<Double-1>", copiar_item)

tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

frame_tabela.grid_rowconfigure(0, weight=1)
frame_tabela.grid_columnconfigure(0, weight=1)

# ======================= RODAPÉ PEQUENO =======================
footer_text = (
    "📋 Duplo-clique = Copiar | 🔍 Pesquise Por Senha ou Hash | ⛔ Use STOP Para interromper"
)

footer = tk.Label(root, 
    text=footer_text,
    bg="#0a0a0a", 
    fg="#00ff9d", 
    font=("Consolas", 9, "bold"),
    justify="center",
    anchor="center",
    pady=6,
    relief="sunken",
    bd=1
)
footer.pack(side="bottom", fill="x")

root.mainloop()
