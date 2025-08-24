import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import webbrowser
import subprocess
import sys
import os

# Função para buscar URLs com progresso
def buscar_wikileaks_paginas(term, total_paginas=1, delay=1, progresso=None):
    base = "https://search.wikileaks.org/?query="
    todas_urls = []

    for page in range(1, total_paginas + 1):
        url = f"{base}{urllib.parse.quote(term)}&page={page}"
        try:
            with urllib.request.urlopen(url) as response:
                html = response.read()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar página {page}: {e}")
            break

        soup = BeautifulSoup(html, "html.parser")
        resultados = soup.find_all("div", class_="result")

        if not resultados:
            break

        for item in resultados:
            link_tag = item.find("a", href=True)
            if link_tag:
                todas_urls.append(link_tag["href"])

        time.sleep(delay)

        # Atualiza barra de progresso
        if progresso:
            progresso['value'] = page
            root.update_idletasks()

    return todas_urls

# Função para abrir link no navegador anônimo
def abrir_no_navegador(link):
    chrome_path = ""
    firefox_path = ""
    
    # Detectar caminhos padrões
    if sys.platform.startswith('win'):
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        firefox_path = "C:/Program Files/Mozilla Firefox/firefox.exe"
    elif sys.platform.startswith('darwin'):
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        firefox_path = "/Applications/Firefox.app/Contents/MacOS/firefox"
    else:  # Linux
        chrome_path = "/usr/bin/google-chrome"
        firefox_path = "/usr/bin/firefox"

    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, "--incognito", link])
    elif os.path.exists(firefox_path):
        subprocess.Popen([firefox_path, "-private-window", link])
    else:
        webbrowser.open_new(link)

# Função do botão de busca
def buscar():
    term = entry_termo.get().strip()
    try:
        paginas = int(entry_paginas.get().strip())
        if paginas < 1:
            paginas = 1
    except ValueError:
        paginas = 1

    resultado_texto.delete(1.0, tk.END)
    progresso['maximum'] = paginas
    progresso['value'] = 0

    urls = buscar_wikileaks_paginas(term, total_paginas=paginas, progresso=progresso)
    
    if not urls:
        resultado_texto.insert(tk.END, "Nenhum resultado encontrado.")
        return 

    for i, u in enumerate(urls, start=1):
        resultado_texto.insert(tk.END, f"Resultado: {i}\n{u}\n{'='*120}\n\n")    

    progresso['value'] = 0  # reset após busca

# Função para salvar em txt com "Salvar como"
def salvar_txt():
    conteudo = resultado_texto.get(1.0, tk.END)
    if conteudo.strip():
        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivos de texto", "*.txt")],
            title="Salvar arquivo como"
        )
        if caminho_arquivo:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Salvo", f"URL salvas em: {caminho_arquivo}")
    else:
        messagebox.showwarning("Vazio", "Nenhum conteúdo para salvar!")

# Função para abrir link no duplo clique
def abrir_url_no_chrome_anonima(event):
    index = resultado_texto.index(f"@{event.x},{event.y}")
    linha = index.split(".")[0]
    link = resultado_texto.get(f"{linha}.0", f"{linha}.end").strip()
    if link.startswith("http"):
        abrir_no_navegador(link)

# --- GUI ---
root = tk.Tk()
root.title("Busca Wikileaks")
root.geometry("1250x885")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Digite Para Buscar", font=("Arial", 12)).grid(pady=5)
entry_termo = tk.Entry(frame, width=25, font=("Arial", 12))
entry_termo.grid(pady=5)

tk.Label(frame, text="Número de Páginas De 1 A 50", font=("Arial", 12)).grid(pady=5)
entry_paginas = tk.Entry(frame, width=10, font=("Arial", 12))
entry_paginas.grid(padx=5)

btn_buscar = tk.Button(frame, text="Buscar", bg="#03fc24", fg="black", font=("Arial", 12, "bold"), command=buscar)
btn_buscar.grid(pady=5)

btn_salvar = tk.Button(frame, text="Salvar", bg="#03e8fc", fg="black", font=("Arial", 12, "bold"), command=salvar_txt)
btn_salvar.grid(pady=5)

# Barra de progresso
from tkinter import ttk
progresso = ttk.Progressbar(frame, orient="horizontal", length=600, mode="determinate")
progresso.grid(pady=10)

resultado_texto = scrolledtext.ScrolledText(frame, width=130, height=32, font=("Arial", 12))
resultado_texto.grid(pady=5)
resultado_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)

root.mainloop()

