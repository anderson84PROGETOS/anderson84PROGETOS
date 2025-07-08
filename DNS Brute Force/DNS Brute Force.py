import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re

def carregar_lista_arquivo(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            linhas = [linha.strip() for linha in f.readlines()]
            # Remove linhas vazias e ignora caracteres inválidos para subdomínios
            return [l for l in linhas if l and re.match(r"^[\w\.-]+$", l)]
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {e}")
        return []

def resolver_dominios(base_domain, wordlist, output, progress_bar, btn_start, label_total):
    resultados = []
    total = len(wordlist)

    for i, prefixo in enumerate(wordlist, 1):
        subdominio = prefixo + base_domain
        try:
            ip = socket.gethostbyname(subdominio)
            resultados.append((subdominio, ip))
            output.insert(tk.END, f"HOST ENCONTRADO: {subdominio:<40} IP: {ip}\n")
        except (socket.gaierror, UnicodeError):
            pass
        progress_bar["value"] = (i / total) * 100
        output.update()

    if not resultados:
        output.insert(tk.END, "[WARN] - Nenhum host encontrado\n")

    label_total.config(text=f"Total de hosts Encontrados: {len(resultados)}")
    btn_start.config(bg="#0bfc03", state=tk.NORMAL, text="Iniciar Busca")

def iniciar_resolucao(entry_domain, entry_arquivo, output, progress_bar, btn_start, label_total):
    domain = entry_domain.get().strip()
    caminho = entry_arquivo.get().strip()

    if not domain or not caminho:
        messagebox.showwarning("Aviso", "Informe o domínio base e selecione a wordlist.")
        return

    output.delete(1.0, tk.END)
    progress_bar["value"] = 0
    label_total.config(text="Total de hosts Encontrados: 0")

    wordlist = carregar_lista_arquivo(caminho)
    if not wordlist:
        output.insert(tk.END, "[ERRO] - Wordlist vazia ou inválida.\n")
        return

    btn_start.config(bg="#05ffff", text="Buscando", state=tk.DISABLED)

    threading.Thread(
        target=lambda: resolver_dominios(domain, wordlist, output, progress_bar, btn_start, label_total),
        daemon=True
    ).start()

def selecionar_arquivo(entry):
    caminho = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if caminho:
        entry.delete(0, tk.END)
        entry.insert(0, caminho)

def salvar_resultados(output):
    conteudo = output.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showinfo("Info", "Nenhum resultado para salvar.")
        return

    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de Texto", "*.txt")])
    if caminho:
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Resultados salvos em: {caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

# GUI
root = tk.Tk()
root.title("DNS Brute Force")
root.geometry("1080x950")

tk.Label(root, text="Domínio Base (ex: .exemplo.com)", font=("Arial", 11)).pack()
entry_domain = tk.Entry(root, width=40, font=("Arial", 11))
entry_domain.pack()

tk.Label(root, text="Wordlist (arquivo .txt)", font=("Arial", 11)).pack()
frame_file = tk.Frame(root)
frame_file.pack()

entry_arquivo = tk.Entry(frame_file, width=50, font=("Arial", 11))
entry_arquivo.pack(side=tk.LEFT, padx=10)

btn_browse = tk.Button(frame_file, text="Selecionar", font=("Arial", 11), bg="#05c5ff", command=lambda: selecionar_arquivo(entry_arquivo))
btn_browse.pack(side=tk.LEFT)

label_total = tk.Label(root, text="Total de hosts Encontrados: 0", font=("Arial", 11, "bold"))
label_total.pack(pady=5)

btn_start = tk.Button(root, text="Iniciar Busca", font=("Arial", 11), bg="#0bfc03", command=lambda: iniciar_resolucao(entry_domain, entry_arquivo, output_text, progress_bar, btn_start, label_total))
btn_start.pack(pady=10)

btn_save = tk.Button(root, text="Salvar Resultados (.txt)", font=("Arial", 11), bg="#ff8f05", command=lambda: salvar_resultados(output_text))
btn_save.pack(pady=5)

progress_bar = ttk.Progressbar(root, length=500)
progress_bar.pack(pady=5)

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=40)
output_text.pack(pady=10)

root.mainloop()
