import requests
import re
import socket
import tkinter as tk
from tkinter import ttk, font, filedialog, scrolledtext
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from ttkthemes import ThemedStyle
from PIL import Image, ImageTk
from io import BytesIO

def extrair_dados(resultado_texto):
    url = url_entry.get()

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

def save_to_file():
    if result_text.get(1.0, tk.END).strip():
        arquivo_saida = filedialog.asksaveasfilename(defaultextension=".txt")
        with open(arquivo_saida, 'w', encoding='utf-8') as file:
            file.write(result_text.get(1.0, tk.END))
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"Os Resultados Foram Salvos Em: {arquivo_saida}\n")

window = tk.Tk()
window.wm_state('zoomed')
window.title("Web Scraping Tool")

style = ThemedStyle(window)
style.set_theme("itft1")

# URL do ícone
icon_url = "https://cdn-icons-png.freepik.com/512/10150/10150772.png"  # Substitua pela URL do seu ícone

# Função para baixar o ícone da web
def download_icon(url):
    response = requests.get(url)
    icon_data = BytesIO(response.content)
    return Image.open(icon_data)

# Baixar o ícone da web
icon_image = download_icon(icon_url)

# Converter a imagem para o formato TKinter
tk_icon = ImageTk.PhotoImage(icon_image)

# Definir o ícone da janela
window.iconphoto(True, tk_icon)

title_label = ttk.Label(window, text='Web Scraping Tool', font=('TkDefaultFont', 15, 'bold'))
title_label.pack(side=tk.TOP, anchor=tk.W, padx=440, pady=20)
bold_font = font.Font(weight='bold')

url_label = tk.Label(window, text='Digite o Nome do site ou a URL do website >>>>>>>>>>>> ex: https://google.com', padx=12, font=bold_font, background='#03fcf8')
url_label.pack(side=tk.TOP, anchor=tk.W, padx=223, pady=5)

clear_all_button = ttk.Button(window, text='Clean All', command=lambda: result_text.delete('1.0', tk.END), style='TButton')
clear_all_button.pack(side=tk.RIGHT, pady=(0, 800), padx=5)

save_button = ttk.Button(window, text='Save to File', command=save_to_file, style='TButton')
save_button.pack(side=tk.RIGHT, padx=5, pady=(0, 800))

url_entry = ttk.Entry(window, font=bold_font)
url_entry.pack(side=tk.TOP, padx=5, pady=5, ipadx=222, ipady=5)

search_button = ttk.Button(window, text='Search', command=lambda: extrair_dados(result_text), style='TButton')
search_button.pack(side=tk.TOP, pady=2)

result_frame = ttk.Frame(window, padding=10)
result_frame.pack(pady=10)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=110, height=40, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W, pady=15)

window.mainloop()
