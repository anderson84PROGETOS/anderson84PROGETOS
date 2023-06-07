import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import mmh3
import codecs
import webbrowser
import pyperclip
import tkinter as tk

def get_favicon_urls():
    url = url_entry.get()

    # Fazer uma requisição HTTP à página web
    response = requests.get(url)

    # Analisar o HTML da página com a biblioteca BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontrar todos os links do favicon na tag <link>
    favicon_links = soup.find_all('link', rel='icon')

    # Obter os valores do atributo "href" de cada link do favicon
    favicon_urls = [link.get('href') for link in favicon_links]

    # Exibir os links dos favicons na janela
    if len(favicon_urls) > 0:
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        result_text.delete(1.0, tk.END)
        for url in favicon_urls:
            full_url = urljoin(base_url, url)
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

        result_text.insert(tk.END, f"\nO hash do favicon de {favicon_url} é: {favicon_hash}\n")
        result_text.insert(tk.END, f"\n[🔑] http.favicon.hash:{favicon_hash}\n")

        shodan_link = f"Resultados no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}\n"
        result_text.insert(tk.END, shodan_link)

    else:
        result_text.insert(tk.END, f"\nNão foi possível obter o favicon de {favicon_url}\n")

def open_shodan():
    favicon_hash = hash_entry.get()
    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
    webbrowser.open(shodan_url)
    result_text.insert(tk.END, "\nVocê foi redirecionado para a pesquisa do Shodan\n")

def copy_results():
    result = result_text.get(1.0, tk.END)
    http_hash = hash_entry.get()
    shodan_link = f"https://www.shodan.io/search?query=http.favicon.hash%3A{http_hash}"
    results = f"{result}{http_hash}\n{shodan_link}"
    pyperclip.copy(results)

def clear_results():
    result_text.delete(1.0, tk.END)

# Cria a janela
window = tk.Tk()
window.wm_state('zoomed')
window.title("Obter Favicon Hash")

# Cria os widgets
url_label = tk.Label(window, text="URL WebSite", font=("Arial", 12, "bold"))
url_label.pack()
url_entry = tk.Entry(window, width=50, font=("Arial", 12, "bold"))
url_entry.pack()


get_favicon_button = tk.Button(window, text="Obter Favicon URLs", command=get_favicon_urls, bg="#00FA9A")
get_favicon_button.pack(pady=10)

hash_label = tk.Label(window, text="Hash do Favicon")
hash_label.pack()
hash_entry = tk.Entry(window, width=25, font=("Arial", 12, "bold"))
hash_entry.pack()

open_shodan_button = tk.Button(window, text="Abrir Shodan", command=open_shodan, bg="#00FFFF")
open_shodan_button.pack(pady=10)

result_text = tk.Text(window, width=135, height=30, font=("Arial", 12, "bold"))
result_text.pack()

copy_button = tk.Button(window, text="Copiar Resultados", command=copy_results)
copy_button.pack(pady=10)

clear_button = tk.Button(window, text="Limpar tudo", command=clear_results,bg="#D2691E")
clear_button.pack(pady=10)

# Executa a janela principal
window.mainloop()
