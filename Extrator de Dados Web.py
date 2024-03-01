import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
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
        resultado_texto.delete('1.0', tk.END)
        resultado_texto.insert(tk.END, "Erro na URL")
        return

    dominio_base = urlparse(url).netloc

    sopa = BeautifulSoup(resposta.content, features='html.parser')

    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', resposta.text))

    resultado_texto.delete('1.0', tk.END)
    resultado_texto.insert(tk.END, f"Foram Encontrados:  {len(subdomains)}  Subdomínios\n\n")
    for subdomain in subdomains:
        resultado_texto.insert(tk.END, subdomain + '\n')

    links = sopa.find_all('a', href=True)
    urls = {link['href'] for link in links if link['href'].startswith('http://') or link['href'].startswith('https://') or link['href'].startswith('/')}
    urls_completas = {urljoin(url, link) if link.startswith('/') else link for link in urls}

    urls_internas = {link for link in urls_completas if dominio_base in urlparse(link).netloc}

    resultado_texto.insert(tk.END, f"\n\n\n\nForam Encontradas:  {len(urls_internas)}  URL Internas\n\n")
    for url in urls_internas:
        resultado_texto.insert(tk.END, url + '\n')

def salvar_resultados():
    if resultado_texto.get(1.0, tk.END).strip():
        arquivo_saida = filedialog.asksaveasfilename(defaultextension=".txt")
        with open(arquivo_saida, 'w', encoding='utf-8') as file:
            file.write(resultado_texto.get(1.0, tk.END))
        resultado_texto.delete('1.0', tk.END)
        resultado_texto.insert(tk.END, f"Os Resultados Foram Salvos Em: {arquivo_saida}\n")

root = tk.Tk()
root.wm_state('zoomed')
root.title("Extrair Dados de um Website")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label_url = tk.Label(frame, text="Digite a URL do Website", font=("Arial", 12))
label_url.grid(row=0, column=0, sticky="w")

entry_url = tk.Entry(frame, width=100, font=("Arial", 12))
entry_url.grid(row=0, column=1)

button_extrair = tk.Button(frame, text="Extrair Dados", command=extrair_dados, bg="#00FFFF", font=("Arial", 11))
button_extrair.grid(row=0, column=2, pady=5)

button_salvar = tk.Button(frame, text="Salvar Resultados", command=salvar_resultados, bg="#03fc17", font=("Arial", 10))
button_salvar.grid(row=1, column=2, pady=5)

resultado_texto = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=150, height=48, font=("Arial", 11))
resultado_texto.grid(row=2, column=0, columnspan=3, pady=5)

root.mainloop()
