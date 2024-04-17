import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

def extrair_dados():
    url = entry_url.get()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
    }

    resposta = requests.get(url, headers=headers)

    if resposta.status_code != 200:
        messagebox.showerror("Erro", "Erro na URL")
        return

    dominio_base = urlparse(url).netloc

    sopa = BeautifulSoup(resposta.content, features='html.parser')

    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', resposta.text))
    urls = {link['href'] for link in sopa.find_all('a', href=True)}
    urls_completas = {urljoin(url, link) if link.startswith('/') else link for link in urls}
    urls_internas = {link for link in urls_completas if dominio_base in urlparse(link).netloc}

    resultados_text.delete('1.0', tk.END)
    resultados_text.insert(tk.END, f"Foram Encontrados ===> {len(subdomains)} Subdomínios\n\n")
    for subdomain in subdomains:
        resultados_text.insert(tk.END, subdomain + '\n')

    resultados_text.insert(tk.END, f"\nForam Encontradas ===> {len(urls_internas)} URL internas\n\n")
    for url in urls_internas:
        resultados_text.insert(tk.END, url + '\n')

def salvar_arquivo():
    arquivo_saida = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
    if arquivo_saida:
        with open(arquivo_saida, 'w', encoding='utf-8') as file:
            file.write(resultados_text.get('1.0', tk.END))
        messagebox.showinfo("Sucesso", f"Os Resultados Foram Salvos Em: {arquivo_saida}")

root = tk.Tk()
root.wm_state('zoomed')
root.title("Extrair Dados de Website")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label_url = tk.Label(frame, text="Extrair Dados Digite a URL do Website ", font=("TkDefaultFont", 11, "bold"))
label_url.grid(row=0, column=0, sticky="w")

entry_url = tk.Entry(frame, width=50, font=("TkDefaultFont", 11, "bold"))
entry_url.grid(row=0, column=1, padx=5, pady=5)

button_extrair = tk.Button(frame, text="Extrair Dados", command=extrair_dados, bg="#00FF00", font=("TkDefaultFont", 11, "bold"))
button_extrair.grid(row=0, column=2, padx=5, pady=5)

button_salvar = tk.Button(frame, text="Salvar Resultados", command=salvar_arquivo, bg="#fc9003", font=("TkDefaultFont", 11, "bold"))
button_salvar.grid(row=0, column=3, padx=5, pady=5)

resultados_text = scrolledtext.ScrolledText(frame, width=115, height=45, wrap=tk.WORD, font=("TkDefaultFont", 12, "bold"))
resultados_text.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

root.mainloop()
