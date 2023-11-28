import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import mmh3
import codecs
import webbrowser
import tkinter as tk
from tkinter import filedialog
import pyperclip  # Importa o módulo pyperclip

def get_favicon_url():
    url = url_entry.get()

    # Fazer uma requisição HTTP à página web
    response = requests.get(url)

    # Analisar o HTML da página com a biblioteca BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontrar o link do favicon na tag <link>
    favicon_link = soup.find('link', rel='icon')

    # Obter o valor do atributo "href" do link do favicon
    if favicon_link:
        favicon_url = favicon_link.get('href')
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        full_url = urljoin(base_url, favicon_url)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, full_url + '\n')
        get_hash(full_url)
    else:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, '\nNenhum link de favicon encontrado.')

def get_hash(favicon_url):
    response = requests.get(favicon_url)
    if response.status_code == 200:
        favicon = codecs.encode(response.content, "base64")
        favicon_hash = mmh3.hash(favicon)

        result_text.insert(tk.END, f"\nO hash do favicon de {favicon_url} é:  {favicon_hash}\n\n")
        result_text.insert(tk.END, f"\n\nhttp.favicon.hash:{favicon_hash}\n\n")

        shodan_link = f"Resultados no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}\n"
        result_text.insert(tk.END, shodan_link)

        # Adiciona botão para copiar apenas o hash
        copy_hash_button = tk.Button(window, text="Copiar Hash", command=lambda hash=favicon_hash: copy_hash(hash), bg="#60f70f")
        copy_hash_button.pack(pady=10)

    else:
        result_text.insert(tk.END, f"\nNão foi possível obter o favicon de {favicon_url}\n")

def open_shodan():
    favicon_hash = hash_entry.get()
    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
    webbrowser.open(shodan_url)
    result_text.insert(tk.END, "\nVocê foi redirecionado para a pesquisa do Shodan\n")

def copy_results():
    # Abre uma caixa de diálogo para escolher o local do arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

    if file_path:
        result = result_text.get(1.0, tk.END)
        http_hash = hash_entry.get()
        shodan_link = f"https://www.shodan.io/search?query=http.favicon.hash%3A{http_hash}"
        results = f"{result}{http_hash}\n{shodan_link}"

        # Salva os resultados no arquivo especificado
        with open(file_path, "w") as file:
            file.write(results)

def copy_hash(favicon_hash):
    pyperclip.copy(favicon_hash)

def clear_results():
    result_text.delete(1.0, tk.END)

# Cria a janela
window = tk.Tk()
window.wm_state('zoomed')
window.title("Obter Favicon Hash")

# Cria os widgets
url_label = tk.Label(window, text="Digite A URL WebSite", font=("Arial", 12, "bold"))
url_label.pack()
url_entry = tk.Entry(window, width=50, font=("Arial", 12, "bold"))
url_entry.pack()

get_favicon_button = tk.Button(window, text="Obter Favicon URL", command=get_favicon_url, bg="#00FA9A")
get_favicon_button.pack(pady=10)

hash_label = tk.Label(window, text="Hash do Favicon")
hash_label.pack()
hash_entry = tk.Entry(window, width=25, font=("Arial", 12, "bold"))
hash_entry.pack()

open_shodan_button = tk.Button(window, text="Abrir Shodan", command=open_shodan, bg="#00FFFF")
open_shodan_button.pack(pady=10)

result_text = tk.Text(window, width=135, height=30, font=("Arial", 12, "bold"))
result_text.pack()

copy_button = tk.Button(window, text="Salvar Resultados", command=copy_results)
copy_button.pack(pady=10)

clear_button = tk.Button(window, text="Limpar tudo", command=clear_results, bg="#D2691E")
clear_button.pack(pady=10)

# Executa a janela principal
window.mainloop()
