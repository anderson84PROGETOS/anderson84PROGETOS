import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter.font import Font

def get_links():
    url = url_entry.get()

    if not url.startswith('http'):
        url = 'https://' + url

    response = requests.get(url)

    filename = filedialog.asksaveasfilename(defaultextension=".txt")
    if not filename:
        return

    textfile = open(filename, 'w')

    soup = BeautifulSoup(response.content, "html.parser")

    links = soup.find_all("a")

    unique_links = set()  # Conjunto para armazenar URLs únicas

    for link in links:
        href = link.get("href")
        if href:
            parsed_url = urlparse(href)
            if parsed_url.scheme in ["http", "https"]:
                unique_links.add(href)

    count = 0
    for href in unique_links:
        count += 1
        textfile.write(href + "\n")
        result_text.insert(tk.END, href + "\n")

    textfile.close()

    font = Font(weight="bold")
    result_text.insert(tk.END, f"\nForam salvos {count} links únicos", "bold")

def clear_results():
    result_text.delete(1.0, tk.END)

# Cria a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Web Scraper")

# Cria o rótulo e a entrada para a URL
url_label = tk.Label(root, text="Digite o nome do site ou a URL do website", font=("Arial", 12, "bold"))
url_label.pack(pady=8)
url_font = Font(weight="bold")
url_entry = tk.Entry(root, width=50, font=url_font)
url_entry.pack()

# Cria o botão para obter os links
get_links_button = tk.Button(root, text="Obter Links", command=get_links, bg="#00FFFF")
get_links_button.pack(pady=15)

# "Clear Results" button
btn_clear_results = tk.Button(root, text="Limpar tudo", command=clear_results, bg="#D2691E")
btn_clear_results.pack(pady=10)

# Cria a caixa de texto para exibir os resultados com scrollbar
result_text = scrolledtext.ScrolledText(root, height=49, width=179, font=("Arial", 10, "bold"))
result_text.pack()

# Inicia o loop principal da janela
root.mainloop()
