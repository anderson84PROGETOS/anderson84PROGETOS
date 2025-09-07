import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

# Fluxo ADS fixo
DEFAULT_ADS = "secret"

def criar_arquivo():
    # Pergunta o nome e o caminho do arquivo
    nome_arquivo = filedialog.asksaveasfilename(title="Salvar novo arquivo", defaultextension=".txt",
                                                filetypes=[("Text Files", "*.txt")])
    if not nome_arquivo:
        return
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            pass  # cria vazio
        messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' criado com sucesso!")
        texto.delete("1.0", tk.END)
        global FIXED_FILE
        FIXED_FILE = nome_arquivo
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def abrir_ads():
    global FIXED_FILE
    arquivo = filedialog.askopenfilename(title="Escolha o arquivo TXT com ADS", 
                                         filetypes=[("Text Files", "*.txt")])
    if not arquivo:
        return
    try:
        with open(f"{arquivo}:{DEFAULT_ADS}", "r", encoding="utf-8") as f:
            conteudo = f.read()
        texto.delete("1.0", tk.END)
        texto.insert(tk.END, conteudo)
        FIXED_FILE = arquivo  # salva o arquivo selecionado para salvar depois
    except FileNotFoundError:
        messagebox.showwarning("Aviso", f"O fluxo alternativo '{DEFAULT_ADS}' não existe nesse arquivo.")
        texto.delete("1.0", tk.END)

def salvar_ads():
    global FIXED_FILE
    if not FIXED_FILE:
        messagebox.showwarning("Aviso", "Crie ou abra um arquivo primeiro!")
        return
    try:
        with open(f"{FIXED_FILE}:{DEFAULT_ADS}", "w", encoding="utf-8") as f:
            f.write(texto.get("1.0", tk.END))
        messagebox.showinfo("Sucesso", f"Conteúdo salvo no fluxo alternativo '{DEFAULT_ADS}' do arquivo '{FIXED_FILE}'!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def copiar_comando():
    global FIXED_FILE
    if not FIXED_FILE:
        messagebox.showwarning("Aviso", "Crie ou abra um arquivo primeiro!")
        return
    comando = f'notepad "{FIXED_FILE}:{DEFAULT_ADS}"'
    root.clipboard_clear()
    root.clipboard_append(comando)
    root.update()
    messagebox.showinfo("Comando Copiado", f"Comando copiado para o clipboard:\n\n{comando}")

# Interface Tkinter
root = tk.Tk()
root.title("Visualizador ADS  >> USAR >> notepad arquivo.txt:secret")
root.geometry("980x640")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

# Botões
novo_btn = tk.Button(btn_frame, text="Criar arquivo TXT", bg="#4df7f5", fg="black", command=criar_arquivo)
novo_btn.pack(side=tk.LEFT, padx=5)

abrir_btn = tk.Button(btn_frame, text="Abrir ADS (secret)", bg="#03fc24", fg="black", command=abrir_ads)
abrir_btn.pack(side=tk.LEFT, padx=5)

salvar_btn = tk.Button(btn_frame, text="Salvar ADS (secret)", bg="#f5ad05", fg="black", command=salvar_ads)
salvar_btn.pack(side=tk.LEFT, padx=5)

copiar_cmd_btn = tk.Button(btn_frame, text="Copiar comando CMD", bg="#ff4d4d", fg="black", command=copiar_comando)
copiar_cmd_btn.pack(side=tk.LEFT, padx=5)

# ScrolledText
texto = scrolledtext.ScrolledText(root, width=100, height=30, font=('Arial', 12))
texto.pack()

# Variável global para armazenar o arquivo atual
FIXED_FILE = None

root.mainloop()
