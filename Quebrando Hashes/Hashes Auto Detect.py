import hashlib
import tkinter as tk
import threading
from tkinter import filedialog, messagebox, scrolledtext, ttk

def load_wordlist(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        messagebox.showerror("Erro", "Erro ao abrir o wordlist.")
        return []

def detectar_tipo_hash(hash_str):
    tamanho = len(hash_str)
    if tamanho == 32:
        return 'md5'
    elif tamanho == 40:
        return 'sha1'
    elif tamanho == 64:
        return 'sha256'
    elif tamanho == 128:
        return 'sha512'
    else:
        return None

def try_crack_hash(target_hash, hash_func_name, passwords):
    for pwd in passwords:
        if hash_func_name == 'md5':
            h = hashlib.md5(pwd.encode()).hexdigest()
        elif hash_func_name == 'sha1':
            h = hashlib.sha1(pwd.encode()).hexdigest()
        elif hash_func_name == 'sha256':
            h = hashlib.sha256(pwd.encode()).hexdigest()
        elif hash_func_name == 'sha512':
            h = hashlib.sha512(pwd.encode()).hexdigest()
        else:
            continue
        if h == target_hash.lower():
            return pwd
    return None

def iniciar():
    wordlist_path = entry_wordlist.get()
    entradas = input_text.get("1.0", tk.END).strip().splitlines()

    if not wordlist_path or not entradas:
        messagebox.showwarning("Aviso", "Preencha todos os campos.")
        return

    passwords = load_wordlist(wordlist_path)
    label_palavras.config(text=f"Total de palavras na wordlist: {len(passwords)}")

    resultado_text.delete("1.0", tk.END)

    total_hashes = len(entradas)
    resultado_text.insert(tk.END, f"[INFO] Total de hashes: {total_hashes}\n\n")    
    resultado_text.insert(tk.END, "[INFO] Detecção de tipo de hash\n\n")

    hashes_info = []
    for idx, hash_line in enumerate(entradas, start=1):
        hash_line = hash_line.strip()
        if not hash_line:
            continue
        tipo_detectado = detectar_tipo_hash(hash_line)
        if tipo_detectado:
            resultado_text.insert(tk.END, f"Hash {idx}: {hash_line} → {tipo_detectado.upper()}\n")
            hashes_info.append((hash_line, tipo_detectado))
        else:
            resultado_text.insert(tk.END, f"Hash {idx}: {hash_line} → [Tipo Desconhecido]\n")
            hashes_info.append((hash_line, None))

    resultado_text.insert(tk.END, "\n\n[INFO] Iniciando quebra de Hash\n\n")

    progress_bar["maximum"] = total_hashes
    progress_bar["value"] = 0
    root.update_idletasks()

    for idx, (hash_line, tipo_detectado) in enumerate(hashes_info, start=1):
        resultado_text.insert(tk.END, f"[{idx}] Hash: {hash_line}\n")

        if not tipo_detectado:
            resultado_text.insert(tk.END, "    [!] Tipo de hash não reconhecido. Pulando...\n\n")
            continue

        resultado_text.insert(tk.END, f"    [*] Tipo Detectado: {tipo_detectado.upper()}\n")       
        pwd_found = try_crack_hash(hash_line, tipo_detectado, passwords)
        if pwd_found:
            resultado_text.insert(tk.END, f"    [+] Senha Encontrada: {pwd_found}\n\n")
        else:
            resultado_text.insert(tk.END, "    [-] Nenhuma senha funcionou.\n\n")

        progress_bar["value"] = idx
        root.update_idletasks()

def selecionar_wordlist():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if file_path:
        entry_wordlist.delete(0, tk.END)
        entry_wordlist.insert(0, file_path)
        passwords = load_wordlist(file_path)
        label_palavras.config(text=f"Total de palavras na wordlist: {len(passwords)}")

def iniciar_thread():
    t = threading.Thread(target=iniciar)
    t.daemon = True  # <- ESSENCIAL: permite fechar o programa mesmo com thread rodando
    t.start()

def on_closing():
    root.destroy()  # fecha tudo imediatamente

def salvar_resultados():
    conteudo = resultado_text.get("1.0", tk.END)
    linhas = conteudo.strip().splitlines()

    blocos_resultado = []
    bloco_atual = []

    for linha in linhas:
        if linha.startswith("[") and "] Hash:" in linha:
            # Começo de um novo bloco
            if bloco_atual:
                blocos_resultado.append(bloco_atual)
                bloco_atual = []
        bloco_atual.append(linha)

    # Adiciona o último bloco, se houver
    if bloco_atual:
        blocos_resultado.append(bloco_atual)

    # Filtra blocos que contêm uma senha encontrada
    blocos_filtrados = [bloco for bloco in blocos_resultado if any("[+] Senha Encontrada:" in l for l in bloco)]

    if not blocos_filtrados:
        messagebox.showinfo("Info", "Nenhuma senha encontrada para salvar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar Resultados"
    )

    if caminho:
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write("[INFO] Iniciando quebra de Hash\n\n")
                for bloco in blocos_filtrados:
                    f.write("\n".join(bloco) + "\n\n")
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")   

# GUI
root = tk.Tk()
root.title("Hashes (AutoDetect)")
root.geometry("1265x900")
root.wm_state('zoomed')
root.protocol("WM_DELETE_WINDOW", on_closing)  # <- Adiciona tratamento ao fechar

tk.Label(root, text="Hashes (um por linha)").pack()
input_text = scrolledtext.ScrolledText(root, height=6, width=80)
input_text.pack()

tk.Label(root, text="Wordlist (.txt)").pack()
frame_wordlist = tk.Frame(root)
frame_wordlist.pack()
entry_wordlist = tk.Entry(frame_wordlist, width=96)
entry_wordlist.pack(side=tk.LEFT)
tk.Button(frame_wordlist, text="Selecionar", command=selecionar_wordlist, bg="#03f4fc", fg="black").pack(side=tk.LEFT, padx=10)

label_palavras = tk.Label(root, text="Total de palavras na wordlist: 0")
label_palavras.pack(pady=5)

def iniciar_thread():
    btn_iniciar.config(bg="#03fc30")  # muda para azul ao clicar
    t = threading.Thread(target=iniciar)
    t.daemon = True
    t.start()

btn_iniciar = tk.Button(root, text="Iniciar Brute force", command=iniciar_thread, bg="#059e07", fg="black")
btn_iniciar.pack(pady=10)

btn_salvar = tk.Button(root, text="Salvar Senhas Encontradas", command=salvar_resultados, bg="#eda705", fg="black")
btn_salvar.pack(pady=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
progress_bar.pack(pady=5)

tk.Label(root, text="Resultado").pack()
resultado_text = scrolledtext.ScrolledText(root, width=148, height=35)
resultado_text.pack()

root.mainloop()
