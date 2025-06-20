import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

def carregar_hashes():
    caminho = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if caminho:
        with open(caminho, "r") as f:
            hashes = [linha.strip().lower() for linha in f if linha.strip()]
        txt_hashes.delete("1.0", tk.END)
        txt_hashes.insert(tk.END, "\n".join(hashes))
        atualizar_label_hash()
        atualizar_label_resultados(0)  # reset resultados ao carregar

def carregar_wordlist():
    caminho = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if caminho:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            wordlist = [linha.strip() for linha in f if linha.strip()]
        txt_wordlist.delete("1.0", tk.END)
        txt_wordlist.insert(tk.END, "\n".join(wordlist))
        atualizar_label_wordlist()

def quebrar_hashes():
    algoritmo = combo_algoritmo.get()
    if not algoritmo:
        messagebox.showwarning("Selecione um algoritmo", "Por favor, selecione um algoritmo de hash.")
        return

    hashes = txt_hashes.get("1.0", tk.END).strip().split("\n")
    wordlist = txt_wordlist.get("1.0", tk.END).strip().split("\n")
    resultados = []

    hash_set = set(hashes)

    for senha in wordlist:
        if algoritmo == "MD5":
            h = hashlib.md5(senha.encode("utf-8")).hexdigest()
        elif algoritmo == "SHA-1":
            h = hashlib.sha1(senha.encode("utf-8")).hexdigest()
        elif algoritmo == "SHA-256":
            h = hashlib.sha256(senha.encode("utf-8")).hexdigest()
        elif algoritmo == "SHA-512":
            h = hashlib.sha512(senha.encode("utf-8")).hexdigest()
        else:
            continue

        if h in hash_set:
            resultados.append(f"{h}  Senha: {senha}\n")

    if resultados:        
        txt_resultados.delete("1.0", tk.END)
        txt_resultados.insert(tk.END, "\n".join(resultados))
        atualizar_label_resultados(len(resultados))
    else:
        messagebox.showwarning("Nada encontrado", "Nenhuma correspondência encontrada.")
        txt_resultados.delete("1.0", tk.END)
        atualizar_label_resultados(0)

def atualizar_label_hash(*args):
    hashes = txt_hashes.get("1.0", tk.END).strip().split("\n")
    num_hashes = len([h for h in hashes if h.strip()])
    hash_label_text.set(f"Hashes (Algoritmo: {combo_algoritmo.get()}) - {num_hashes} carregadas")

def atualizar_label_wordlist(*args):
    wordlist = txt_wordlist.get("1.0", tk.END).strip().split("\n")
    num_words = len([w for w in wordlist if w.strip()])
    wordlist_label_text.set(f"Wordlist (uma senha por linha) - {num_words} senhas")

def atualizar_label_resultados(qtd):
    resultados_label_text.set(f"Resultados Encontrados - {qtd} registros")

def salvar_resultados():
    conteudo = txt_resultados.get("1.0", tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Nenhum dado", "Não há resultados para salvar.")
        return

    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        messagebox.showinfo("Sucesso", f"salvos em: {caminho}")

# Interface gráfica
janela = tk.Tk()
janela.title("Quebrando Hashes")
janela.geometry("1200x950")

frame1 = tk.Frame(janela)
frame1.pack(pady=10)

btn_hashes = tk.Button(frame1, text="Carregar Arquivo de Hashes", bg="#03fc30", fg="black", command=carregar_hashes)
btn_hashes.grid(row=0, column=0, padx=10)

btn_wordlist = tk.Button(frame1, text="Carregar Wordlist", bg="#03fcf4", fg="black", command=carregar_wordlist)
btn_wordlist.grid(row=0, column=1, padx=10)

tk.Label(frame1, text="Algoritmo:").grid(row=0, column=2, padx=(10, 0))
combo_algoritmo = ttk.Combobox(frame1, values=["MD5", "SHA-1", "SHA-256", "SHA-512"])
combo_algoritmo.set("MD5")
combo_algoritmo.grid(row=0, column=3, padx=5)
combo_algoritmo.bind("<<ComboboxSelected>>", atualizar_label_hash)

btn_executar = tk.Button(frame1, text="Iniciar Quebra", bg="#03fc30", fg="black", command=quebrar_hashes)
btn_executar.grid(row=0, column=4, padx=10)

btn_salvar = tk.Button(frame1, text="Salvar Resultados", bg="#fcd303", fg="black", command=salvar_resultados)
btn_salvar.grid(row=0, column=5, padx=10)

# Labels dinâmicos
hash_label_text = tk.StringVar()
hash_label_text.set("Hashes (Algoritmo: MD5)")
tk.Label(janela, textvariable=hash_label_text).pack(pady=(10, 0))

txt_hashes = scrolledtext.ScrolledText(janela, width=130, height=15)
txt_hashes.pack(padx=10, pady=(0, 10))
txt_hashes.bind("<KeyRelease>", atualizar_label_hash)

wordlist_label_text = tk.StringVar()
wordlist_label_text.set("Wordlist (uma senha por linha)")
tk.Label(janela, textvariable=wordlist_label_text).pack(pady=(10, 0))

txt_wordlist = scrolledtext.ScrolledText(janela, width=130, height=15)
txt_wordlist.pack(padx=10, pady=(0, 10))
txt_wordlist.bind("<KeyRelease>", atualizar_label_wordlist)

resultados_label_text = tk.StringVar()
resultados_label_text.set("Resultados Encontrados")
tk.Label(janela, textvariable=resultados_label_text).pack(pady=(10, 0))

txt_resultados = scrolledtext.ScrolledText(janela, width=130, height=15, bg="#e7ffe7")
txt_resultados.pack(padx=10, pady=(0, 10))

janela.mainloop()
