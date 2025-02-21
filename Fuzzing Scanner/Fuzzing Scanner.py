import os
import requests
import threading
from urllib.parse import urljoin
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

def procurar_arquivo_txt():
    """Abre um seletor de arquivos para escolher uma wordlist .txt e exibe o número de palavras."""
    arquivo = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if arquivo:
        entry_wordlist.delete(0, tk.END)
        entry_wordlist.insert(0, arquivo)

        # Contar as palavras no arquivo
        wordlist = load_wordlist(arquivo)
        if wordlist:
            num_palavras = len(wordlist)
            label_wordlist_count.config(text=f"Wordlist: {num_palavras} Palavras")
        else:
            label_wordlist_count.config(text="Wordlist vazia ou não encontrada.")

def escolher_codigos_status():
    """Obtém os códigos de status selecionados."""
    selecionados = set()
    if var_200.get():
        selecionados.add(200)
    if var_301.get():
        selecionados.add(301)
    if var_403.get():
        selecionados.add(403)
    return selecionados if selecionados else {200}

def load_wordlist(filename):
    """Carrega a wordlist e retorna uma lista de palavras-chave."""
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []

def find_pages():
    """Inicia a busca em uma thread separada para evitar travamento da interface."""
    threading.Thread(target=executar_scan, daemon=True).start()

def executar_scan():
    """Executa a busca de páginas sem travar a interface."""
    base_url = entry_url.get().strip()
    arquivo_wordlist = entry_wordlist.get().strip()

    if not base_url or not arquivo_wordlist:
        text_output.insert(tk.END, "\n[ERRO] Preencha todos os campos!\n")
        return

    wordlist = load_wordlist(arquivo_wordlist)
    if not wordlist:
        text_output.insert(tk.END, "\n[ERRO] Wordlist vazia ou arquivo não encontrado!\n")
        return

    codigos_status = escolher_codigos_status()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Verificando o protocolo (http ou https)
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url  # Adiciona http:// se o protocolo não for especificado

    text_output.insert(tk.END, f"[INFO] Iniciando verificação em: {base_url}\n\n")

    # Configurando a barra de progresso
    progress_bar["maximum"] = len(wordlist)
    progress_bar["value"] = 0

    for i, word in enumerate(wordlist):
        test_url = urljoin(base_url, word)
        try:
            response = requests.get(test_url, headers=headers, timeout=5, allow_redirects=False)
            if response.status_code in codigos_status:
                msg = f"({response.status_code}) {test_url}\n"
                text_output.insert(tk.END, msg)
                text_output.yview(tk.END)  # Auto-scroll

        except requests.RequestException:
            continue  # Ignora erros e segue para a próxima URL

        progress_bar["value"] = i + 1  # Atualiza a barra de progresso
        root.update_idletasks()  # Atualiza a interface sem travar

    text_output.insert(tk.END, "\n\n[INFO] Verificação concluída.\n")

# Criando interface gráfica
root = tk.Tk()
root.title("Fuzzing Scanner")
root.geometry("1260x950")

frame = tk.Frame(root)
frame.pack(pady=10)

# Entrada para URL
label = tk.Label(frame, text="Digite a URL do website", font=("Arial", 11, "bold"))
label.grid(pady=5)

entry_url = tk.Entry(frame, width=40, font=("Arial", 11, "bold"))
entry_url.grid(pady=5)

# Botão de iniciar busca
tk.Button(frame, text="Iniciar", command=find_pages, font=("Arial", 11, "bold"), bg="#00FF00").grid(pady=5)

# Label para mostrar o número de palavras na wordlist
label_wordlist_count = tk.Label(frame, text="Wordlist:  0  Palavras", font=("Arial", 11, "bold"))
label_wordlist_count.grid(pady=5)

tk.Button(frame, text="Selecionar", command=procurar_arquivo_txt, font=("Arial", 11, "bold"), bg="#07f7e3").grid(pady=10)
entry_wordlist = tk.Entry(frame, width=80, font=("Arial", 11, "bold"))
entry_wordlist.grid(pady=5)

# Checkbuttons para códigos de status (lado a lado)
var_200, var_301, var_403 = tk.IntVar(), tk.IntVar(), tk.IntVar()
frame_codigos = tk.Frame(frame)
frame_codigos.grid(row=6, column=0, columnspan=3, pady=5)

# Checkbuttons para códigos de status (lado a lado)
tk.Checkbutton(frame_codigos, text="200", variable=var_200, font=("Arial", 11, "bold"), 
               bg="#00FF00", selectcolor="#00FF00").grid(row=0, column=0, padx=10, pady=5, sticky="w")

tk.Checkbutton(frame_codigos, text="301", variable=var_301, font=("Arial", 11, "bold"), 
               bg="#fcb103", selectcolor="#fcb103").grid(row=0, column=1, padx=10, pady=5, sticky="w")

tk.Checkbutton(frame_codigos, text="403", variable=var_403, font=("Arial", 11, "bold"), 
               bg="#fc0320", selectcolor="#fc0320").grid(row=0, column=2, padx=10, pady=5, sticky="w")

# Barra de progresso
progress_bar = ttk.Progressbar(root, length=500, mode="determinate")
progress_bar.pack(pady=5)

# Área de saída
text_output = scrolledtext.ScrolledText(root, width=120, height=30, font=("Arial", 11, "bold"))
text_output.pack()

root.mainloop()
