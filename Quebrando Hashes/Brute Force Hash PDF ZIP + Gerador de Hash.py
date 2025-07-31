import hashlib
import tkinter as tk
import threading
from tkinter import filedialog, messagebox, scrolledtext, ttk
import pikepdf
import os
import pyzipper
import time

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

def update_label_testando(pwd):
    label_testando.config(text=f"Wordlist atual: Testando:   {pwd}")
    root.update_idletasks()
    time.sleep(0.2)

def try_crack_hash(target_hash, hash_func_name, passwords):
    for pwd in passwords:
        update_label_testando(pwd)
        h = getattr(hashlib, hash_func_name)(pwd.encode()).hexdigest()
        if h == target_hash.lower():
            label_testando.config(text=f"Senha Encontrada: {pwd}")
            return pwd
    return None

def try_crack_pdf(pdf_path, passwords):
    for pwd in passwords:
        update_label_testando(pwd)
        try:
            with pikepdf.open(pdf_path, password=pwd):
                label_testando.config(text=f"Senha Encontrada: {pwd}")
                return pwd
        except pikepdf._qpdf.PasswordError:
            continue
        except Exception:
            break
    return None

def try_crack_zip(zip_path, passwords):
    try:
        with pyzipper.AESZipFile(zip_path) as zf:
            for pwd in passwords:
                update_label_testando(pwd)
                try:
                    zf.pwd = pwd.encode('utf-8')
                    zf.namelist()
                    with zf.open(zf.namelist()[0]) as f:
                        f.read(1)
                    label_testando.config(text=f"Senha Encontrada: {pwd}")
                    return pwd
                except Exception:
                    continue
    except Exception as e:
        print(f"Erro ao abrir ZIP: {e}")
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
    total_entradas = len(entradas)

    progress_bar["value"] = 0
    progress_bar["maximum"] = total_entradas

    # Escreve informações iniciais no resultado em tempo real
    resultado_text.insert(tk.END, f"[INFO] Total de entradas: {total_entradas}\n\n")
    resultado_text.insert(tk.END, "[INFO] Análise das Entradas\n\n")

    for idx, entrada in enumerate(entradas, start=1):
        entrada = entrada.strip()
        pwd = None
        info = f"[{idx}] Entrada: {entrada}\n"

        if os.path.isfile(entrada):
            lower = entrada.lower()
            if lower.endswith(".pdf"):
                info += "    [*] Arquivo PDF Detectado\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_pdf(entrada, passwords)
            elif lower.endswith(".zip"):
                info += "    [*] Arquivo ZIP Detectado\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_zip(entrada, passwords)
            else:
                info += "    [*] Arquivo desconhecido\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
        else:
            tipo = detectar_tipo_hash(entrada)
            if tipo:
                info += f"    [*] Hash Detectado: {tipo.upper()}\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_hash(entrada, tipo, passwords)
            else:
                info += "    [*] Tipo de entrada não reconhecido\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()

        if pwd:
            resultado_text.insert(tk.END, f"    [+] Senha Encontrada: {pwd}\n\n")
        else:
            resultado_text.insert(tk.END, f"    [-] Senha Não Encontrada\n\n")

        resultado_text.see(tk.END)
        root.update_idletasks()

        progress_bar["value"] = idx

    label_testando.config(text="Wordlist atual: Finalizado.")

def iniciar_thread():
    btn_iniciar.config(bg="#03fc30", state=tk.DISABLED)
    threading.Thread(target=run_bruteforce_thread, daemon=True).start()

def run_bruteforce_thread():
    try:
        iniciar()
    finally:
        btn_iniciar.config(state=tk.NORMAL, bg="#059e07")

def selecionar_wordlist():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if file_path:
        entry_wordlist.delete(0, tk.END)
        entry_wordlist.insert(0, file_path)
        passwords = load_wordlist(file_path)
        label_palavras.config(text=f"Total de palavras na wordlist: {len(passwords)}")

def selecionar_arquivo_hashes():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
                input_text.delete("1.0", tk.END)
                input_text.insert(tk.END, conteudo)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler o arquivo de hashes:\n{e}")

def adicionar_arquivo():
    path = filedialog.askopenfilename(filetypes=[("Arquivos Suportados", "*.pdf *.zip")])
    if path:
        input_text.insert(tk.END, path + "\n")

def salvar_resultados():
    conteudo = resultado_text.get("1.0", tk.END)
    if "[+] Senha Encontrada:" not in conteudo:
        messagebox.showinfo("Info", "Nenhuma senha encontrada para salvar.")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
    if caminho:
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

def gerar_hash(algoritmo):
    entrada = entrada_gerar_hash.get()
    if not entrada.strip():
        messagebox.showwarning("Aviso", "Digite uma senha para gerar hash.")
        return
    h = getattr(hashlib, algoritmo)(entrada.encode()).hexdigest()
    saida_hash.delete("1.0", tk.END)
    saida_hash.insert(tk.END, f"{algoritmo.upper()}\n\n{h}")

# GUI
root = tk.Tk()
root.title("Brute Force Hash/PDF/ZIP + Gerador de Hash")
root.geometry("1150x950")
root.protocol("WM_DELETE_WINDOW", root.destroy)

tk.Label(root, text="Hashes ou Arquivos").pack()
frame_hashes = tk.Frame(root)
frame_hashes.pack()
tk.Button(frame_hashes, text="Selecionar Arquivo de Hashes", command=selecionar_arquivo_hashes, bg="#c7ffb6").pack(side=tk.LEFT, padx=5, pady=10)
tk.Button(frame_hashes, text="Selecionar PDF/ZIP", command=adicionar_arquivo, bg="#fa5f9a").pack(side=tk.LEFT, padx=5, pady=10)

input_text = scrolledtext.ScrolledText(root, width=130, height=10)
input_text.pack()

tk.Label(root, text="Wordlist (.txt)").pack()
frame_wordlist = tk.Frame(root)
frame_wordlist.pack()
entry_wordlist = tk.Entry(frame_wordlist, width=96)
entry_wordlist.pack(side=tk.LEFT)
tk.Button(frame_wordlist, text="Selecionar", command=selecionar_wordlist, bg="#03f4fc").pack(side=tk.LEFT, padx=10)

label_palavras = tk.Label(root, text="Total de palavras na wordlist: 0")
label_palavras.pack(pady=5)

btn_iniciar = tk.Button(root, text="Iniciar Brute Force", command=iniciar_thread, bg="#059e07", fg="black")
btn_iniciar.pack(pady=10)

btn_salvar = tk.Button(root, text="Salvar Senhas Encontradas", command=salvar_resultados, bg="#eda705", fg="black")
btn_salvar.pack(pady=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
progress_bar.pack(pady=5)

label_testando = tk.Label(root, text="Wordlist atual: Aguardando...", fg="blue", font=("Arial", 10, "bold"))
label_testando.pack(pady=3)

tk.Label(root, text="Resultado").pack()
resultado_text = scrolledtext.ScrolledText(root, width=130, height=10)
resultado_text.pack()

# Gerador de Hash
tk.Label(root, text="Gerar Hash de uma Senha", font=("Arial", 12, "bold")).pack(pady=8)

frame_hash = tk.Frame(root)
frame_hash.pack()
entrada_gerar_hash = tk.Entry(frame_hash, width=60)
entrada_gerar_hash.pack(side=tk.LEFT, padx=5)

frame_botoes_hash = tk.Frame(root)
frame_botoes_hash.pack(pady=5)
tk.Button(frame_botoes_hash, text="Gerar MD5", command=lambda: gerar_hash("md5"), bg="#d0c4fc").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA1", command=lambda: gerar_hash("sha1"), bg="#c4fce8").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA256", command=lambda: gerar_hash("sha256"), bg="#fcd7c4").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA512", command=lambda: gerar_hash("sha512"), bg="#fbc4f7").pack(side=tk.LEFT, padx=5)

saida_hash = tk.Text(root, width=130, height=10, fg="blue")
saida_hash.pack(pady=5)

root.mainloop()
