import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
from datetime import datetime
import threading
import pyperclip

# ======================= VARIÁVEIS GLOBAIS =======================
senhas = []
resultados = []
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

# ======================= COPIAR =======================
def copiar_item(event):
    try:
        item = tree.selection()[0]
        valores = tree.item(item, "values")
        coluna = tree.identify_column(event.x)
        col_index = int(coluna.replace("#", "")) - 1
        texto = valores[col_index]
        pyperclip.copy(texto)
        
        lbl_status.config(text=f"✅ COPIADO: {texto[:30]}...", fg="#00ff41")
        root.after(1500, lambda: lbl_status.config(
            text=f"✅ {len(resultados)} resultados carregados", fg="#00ff41"))
    except:
        pass

def atualizar_colunas():
    """Atualiza visibilidade das colunas conforme checkboxes"""
    visible = [0]  # "Senha" sempre visível
    
    # Mapeamento correto: MD5=1, SHA1=2, SHA256=3, SHA512=4
    for i, var in enumerate(check_vars):
        if var.get():
            visible.append(i + 1)
    
    tree["displaycolumns"] = visible

# ======================= PROCESSAMENTO =======================
def processar_thread():
    global stop_flag
    stop_flag = False
    
    if not senhas:
        root.after(0, lambda: messagebox.showwarning("Aviso", "Nenhuma senha carregada!"))
        return

    resultados.clear()
    tree.delete(*tree.get_children())
    total = len(senhas)

    for i, senha in enumerate(senhas):
        if stop_flag:
            root.after(0, lambda: lbl_progress.config(text="⛔ INTERROMPIDO"))
            root.after(0, lambda: btn_processar.config(state="normal"))
            root.after(0, lambda: btn_stop.config(state="disabled"))
            return

        hashes = calcular_hashes(senha)
        resultados.append((senha, hashes))
        
        # Inserir na tabela de forma segura
        root.after(0, lambda s=senha, h=hashes: 
            tree.insert("", "end", values=(s, h['MD5'], h['SHA1'], h['SHA256'], h['SHA512'])))
        
        progresso = int(((i + 1) / total) * 100)
        root.after(0, lambda p=progresso, idx=i+1: 
            [progress_bar.configure(value=p),
             lbl_progress.config(text=f"Processando... {p}% ({idx}/{total})")])

    # Finalizado
    root.after(0, lambda: lbl_progress.config(text=f"✅ CONCLUÍDO! {total} SENHAS PROCESSADAS"))
    root.after(0, lambda: btn_processar.config(state="normal"))
    root.after(0, lambda: btn_stop.config(state="disabled"))
    root.after(0, atualizar_colunas)  # Atualiza colunas visíveis

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
    lbl_progress.config(text="⛔ PARANDO...")

# ======================= OUTRAS FUNÇÕES =======================
def salvar_arquivo():
    if not resultados:
        messagebox.showwarning("Aviso", "Nada para salvar!")
        return
    path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                      filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
    if path:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Hashes gerados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*120 + "\n\n")
                for senha, h in resultados:
                    f.write(f"Senha     : {senha}\n\n")
                    f.write(f"MD5       : {h['MD5']}\n")
                    f.write(f"SHA1      : {h['SHA1']}\n")
                    f.write(f"SHA256    : {h['SHA256']}\n")
                    f.write(f"SHA512    : {h['SHA512']}\n")
                    f.write("-" * 100 + "\n")
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

def selecionar_arquivo():
    global senhas
    arq = filedialog.askopenfilename(title="Selecionar arquivo de senhas", 
                                   filetypes=[("TXT", "*.txt"), ("Todos", "*.*")])
    if arq:
        senhas = carregar_senhas(arq)
        lbl_status.config(text=f"✅ {len(senhas)} SENHAS CARREGADAS", fg="#00ff41")
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
    atualizar_colunas()

def limpar_pesquisa():
    entry_pesquisa.delete(0, tk.END)
    tree.delete(*tree.get_children())
    for senha, hashes in resultados:
        tree.insert("", "end", values=(senha, hashes['MD5'], hashes['SHA1'], hashes['SHA256'], hashes['SHA512']))
    atualizar_colunas()

# ======================= GUI =======================
root = tk.Tk()
root.title("HASH CONVERTER - MD5 | SHA1 | SHA256 | SHA512")
root.geometry("1480x880")
root.state("zoomed")
root.configure(bg="#0a0a0a")

font_title = ("Courier New", 18, "bold")
font_text = ("Courier New", 10)

tk.Label(root, text="╔═╗ HACKER HASH CONVERTER ═╗\nMD5 | SHA1 | SHA256 | SHA512", 
         font=font_title, fg="#00ff41", bg="#0a0a0a").pack(pady=12)

# ======================= CHECKBOXES =======================
frame_hash = tk.Frame(root, bg="#0a0a0a")
frame_hash.pack(fill="x", padx=20, pady=6)

tk.Label(frame_hash, text="MOSTRAR:", fg="#00ff88", bg="#0a0a0a", 
         font=("Courier New", 11, "bold")).pack(side="left", padx=10)

check_vars = []
hash_names = ["MD5", "SHA1", "SHA256", "SHA512"]
default_states = [True, True, True, True]

for i, name in enumerate(hash_names):
    var = tk.BooleanVar(value=default_states[i])
    check_vars.append(var)
    chk = tk.Checkbutton(frame_hash, text=name, variable=var, bg="#0a0a0a", fg="#00ff41",
                         selectcolor="#003300", font=font_text, command=atualizar_colunas)
    chk.pack(side="left", padx=12)

# ======================= BOTÕES =======================
frame_top = tk.Frame(root, bg="#0a0a0a")
frame_top.pack(fill="x", padx=20, pady=8)

btn_select = tk.Button(frame_top, text="📂 SELECIONAR .TXT", command=selecionar_arquivo,
                       width=22, height=2, bg="#003300", fg="#00ff41", font=font_text, relief="ridge", bd=3)
btn_select.pack(side="left", padx=5)

btn_processar = tk.Button(frame_top, text="🔄 PROCESSAR", command=processar,
                          width=18, height=2, bg="#004400", fg="#00c3ff", font=font_text, relief="ridge", bd=3, state="disabled")
btn_processar.pack(side="left", padx=5)

btn_save = tk.Button(frame_top, text="💾 SALVAR", command=salvar_arquivo,
                     width=18, height=2, bg="#002200", fg="#e76b06", font=font_text, relief="ridge", bd=3)
btn_save.pack(side="left", padx=5)

btn_stop = tk.Button(frame_top, text="⛔ STOP", command=stop_processamento,
                     width=14, height=2, bg="#880000", fg="#ffffff", font=("Courier New", 10, "bold"), relief="ridge", bd=3, state="disabled")
btn_stop.pack(side="left", padx=5)

# Pesquisa
frame_search = tk.Frame(root, bg="#0a0a0a")
frame_search.pack(fill="x", padx=20, pady=8)

tk.Label(frame_search, text="🔍 PESQUISAR:", fg="#00ff41", bg="#0a0a0a", font=("Courier New", 11, "bold")).pack(side="left", padx=(0,8))
entry_pesquisa = tk.Entry(frame_search, width=50, font=font_text, bg="#001100", fg="#00ff41", insertbackground="#00ff41")
entry_pesquisa.pack(side="left", padx=5, fill="x", expand=True)

btn_search = tk.Button(frame_search, text="BUSCAR", command=pesquisar, bg="#005500", fg="#00ff41", font=font_text, relief="ridge", bd=3, width=12)
btn_search.pack(side="left", padx=5)

btn_clear = tk.Button(frame_search, text="LIMPAR", command=limpar_pesquisa, bg="#330000", fg="#ff4444", font=font_text, relief="ridge", bd=3, width=10)
btn_clear.pack(side="left", padx=5)

lbl_status = tk.Label(frame_search, text="NENHUM ARQUIVO CARREGADO", fg="#00ff41", bg="#0a0a0a", font=font_text)
lbl_status.pack(side="right", padx=10)

# Progresso
frame_prog = tk.Frame(root, bg="#0a0a0a")
frame_prog.pack(fill="x", padx=20, pady=8)
lbl_progress = tk.Label(frame_prog, text="PRONTO PARA INICIAR", fg="#00ff41", bg="#0a0a0a", font=("Courier New", 11, "bold"))
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

for col in columns:
    tree.heading(col, text=col)

tree.column("Senha", width=310, minwidth=310, anchor="w")
tree.column("MD5", width=320, minwidth=320, anchor="w")
tree.column("SHA1", width=380, minwidth=380, anchor="w")
tree.column("SHA256", width=570, minwidth=570, anchor="w")
tree.column("SHA512", width=1070, minwidth=1070, anchor="w")

tree.bind("<Double-1>", copiar_item)

tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

frame_tabela.grid_rowconfigure(0, weight=1)
frame_tabela.grid_columnconfigure(0, weight=1)

# Rodapé
footer = tk.Label(root, text="📋 Duplo-clique em qualquer célula = Copiar | Use os checkboxes para mostrar/ocultar hashes", 
                 bg="#0a0a0a", fg="#00ff9d", font=("Consolas", 9, "bold"), pady=6, relief="sunken", bd=1)
footer.pack(side="bottom", fill="x")

root.mainloop()
