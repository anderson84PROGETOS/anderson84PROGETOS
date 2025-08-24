import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import time
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import webbrowser
import subprocess
import sys
import os
import threading

# --- Funções ---

# Buscar URLs no Wikileaks
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
        if progresso:
            progresso['value'] = page
            root.update_idletasks()
    return todas_urls

# Abrir link no navegador anônimo
def abrir_no_navegador(link):
    chrome_path = ""
    firefox_path = ""
    if sys.platform.startswith('win'):
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        firefox_path = "C:/Program Files/Mozilla Firefox/firefox.exe"
    elif sys.platform.startswith('darwin'):
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        firefox_path = "/Applications/Firefox.app/Contents/MacOS/firefox"
    else:
        chrome_path = "/usr/bin/google-chrome"
        firefox_path = "/usr/bin/firefox"

    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, "--incognito", link])
    elif os.path.exists(firefox_path):
        subprocess.Popen([firefox_path, "-private-window", link])
    else:
        webbrowser.open_new(link)

# Thread para buscar sem travar GUI
def buscar_thread():
    btn_buscar.config(bg="#028a0f")  # verde escuro
    thread = threading.Thread(target=lambda: buscar_e_restaurar())
    thread.start()

def buscar_e_restaurar():
    term = entry_termo.get().strip()
    try:
        paginas = int(entry_paginas.get().strip())
        if paginas < 1:
            paginas = 1
    except ValueError:
        paginas = 1
    progresso['maximum'] = paginas
    progresso['value'] = 0
    global urls
    urls = buscar_wikileaks_paginas(term, total_paginas=paginas, progresso=progresso)
    mostrar_resultados(urls)
    btn_buscar.config(bg="#03fc24")  # verde original
    progresso['value'] = 0

# Mostrar resultados com botão próprio
def mostrar_resultados(urls):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()  # limpa resultados anteriores
    if not urls:
        tk.Label(scrollable_frame, text="Nenhum resultado encontrado.", font=("Arial", 12)).pack(pady=10)
        return
    for i, url in enumerate(urls, start=1):
        frame_link = tk.Frame(scrollable_frame, bd=1, relief="solid", padx=10, pady=5)
        frame_link.pack(fill="x", expand=True, pady=5)

        tk.Label(frame_link, text=f"Resultado: {i}", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Label do link com wraplength
        tk.Label(frame_link, text=url, fg="#0a39f5", cursor="hand2", font=("Arial", 12, "bold"),
                 wraplength=1100, justify="left").pack(anchor="w")
        
        tk.Button(frame_link, text="Abrir Link", bg="#fcf403", font=("Arial", 10, "bold"),
                  command=lambda u=url: abrir_no_navegador(u)).pack(anchor="w", pady=2)

# Salvar resultados em txt
def salvar_txt():
    if not urls:
        messagebox.showwarning("Vazio", "Nenhum conteúdo para salvar!")
        return
    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de texto", "*.txt")],
        title="Salvar arquivo como"
    )
    if caminho_arquivo:
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            for i, u in enumerate(urls, start=1):
                f.write(f"Resultado: {i}\n{u}\n{'='*120}\n\n")
        messagebox.showinfo("Salvo", f"Resultados salvos em: {caminho_arquivo}")

# --- GUI ---

root = tk.Tk()
root.title("Buscar Wikileaks")
root.wm_state('zoomed')
root.geometry("1024x720")

# Frame de busca
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Digite Para Buscar", font=("Arial", 12)).grid(pady=5)
entry_termo = tk.Entry(frame, width=25, font=("Arial", 12))
entry_termo.grid(pady=5)

tk.Label(frame, text="Número de Páginas De 1 A 50", font=("Arial", 12)).grid(pady=5)
entry_paginas = tk.Entry(frame, width=10, font=("Arial", 12))
entry_paginas.grid(padx=5)

btn_buscar = tk.Button(frame, text="Buscar", bg="#03fc24", fg="black", font=("Arial", 12, "bold"),
                       command=buscar_thread)
btn_buscar.grid(pady=5)

btn_salvar = tk.Button(frame, text="Salvar", bg="#03e8fc", fg="black", font=("Arial", 12, "bold"),
                       command=salvar_txt)
btn_salvar.grid(pady=5)

progresso = ttk.Progressbar(frame, orient="horizontal", length=600, mode="determinate")
progresso.grid(pady=5)

# Frame rolável para resultados com Canvas dentro de um quadro preto
frame_resultados_outer = tk.Frame(root, bg="black", bd=2, relief="solid")  # quadro preto
frame_resultados_outer.pack(fill="both", expand=True, padx=10, pady=10)  # espaço externo

# Frame interno para organizar canvas e scrollbar
frame_resultados = tk.Frame(frame_resultados_outer)
frame_resultados.pack(fill="both", expand=True, padx=2, pady=2)  # espaço entre a borda e o conteúdo

canvas = tk.Canvas(frame_resultados, bg="white")  # fundo branco do canvas
scrollbar = tk.Scrollbar(frame_resultados, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollable_frame = tk.Frame(canvas, bg="white")  # fundo branco para resultados

# Permitir que o scrollable_frame se expanda corretamente
def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig(canvas_frame, width=canvas.winfo_width())

scrollable_frame.bind("<Configure>", on_configure)

canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Lista global de URL
urls = []

root.mainloop()
