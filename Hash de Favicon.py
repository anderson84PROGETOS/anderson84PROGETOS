import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import mmh3
import codecs
import webbrowser
import pyperclip
import tkinter as tk

def get_favicon_urls(url):
    # Fazer uma requisição HTTP à página web
    response = requests.get(url)

    # Analisar o HTML da página com a biblioteca BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontrar todos os links do favicon que contenham os valores "ico" ou "png" na extensão do arquivo
    favicon_links = soup.find_all('link', rel='icon', href=lambda href: href and ('.ico' in href or '.png' in href))

    # Obter os valores do atributo "href" de cada link do favicon e calcular o hash de cada favicon
    favicon_hashes = []
    if len(favicon_links) > 0:
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        for link in favicon_links:
            full_url = urljoin(base_url, link.get('href'))
            favicon_hash = get_hash(full_url)
            favicon_hashes.append(favicon_hash)

            # Atualizar a label com informações sobre o hash do favicon e um link para a pesquisa no Shodan
            favicon_info_label.config(text=favicon_info_label.cget("text") + f"\n\nO hash do favicon de {full_url} É:   {favicon_hash}")
            shodan_link = f"Resultados no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
            shodan_link_label.config(text=shodan_link)
    else:
        favicon_info_label.config(text='Nenhum link de favicon encontrado.')

    # Exibir os hashes dos favicons na janela
    if len(favicon_hashes) > 0:
        all_hashes = "".join([str(h) for h in favicon_hashes])

def get_hash(favicon_url):
    response = requests.get(favicon_url)
    if response.status_code == 200:
        favicon = codecs.encode(response.content, "base64")
        favicon_hash = mmh3.hash(favicon)
        return favicon_hash
    else:
        return f"\nNão foi possível obter o favicon de {favicon_url}"

def open_shodan():
    hash_input = hash_entry.get()
    shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{hash_input}"
    webbrowser.open(shodan_url)
    shodan_info_label.config(text="\nVocê foi redirecionado para a pesquisa do Shodan")

def copy_results():
    result = favicon_info_label.cget("text")
    http_hash = result.split("\n")[1]
    shodan_link = shodan_link_label.cget("text")
    results = f"{result}\n{shodan_link}"
    pyperclip.copy(results)

# botao Limpar Resultados
def clear_all():
    favicon_info_label.config(text="")
    shodan_link_label.config(text="")
    shodan_info_label.config(text="")
    hash_entry.delete(0, 'end')
    url_entry.delete(0, 'end')

window = tk.Tk()
window.wm_state('zoomed')
window.title("Favicon Hash Checker")

info_text = tk.Text(window, font=("Arial", 10), width=50, height=25)
info_text.place(x=400, y=450, width=870, height=500)

url_label = tk.Label(window, text="Digite a URL da página", width=20)
url_entry = tk.Entry(window, width=50)
get_favicons_button = tk.Button(window, text="URL Obter Favicons", command=lambda: get_favicon_urls(url_entry.get()))

hash_label = tk.Label(window, text="Digite a hash do favicon", width=20)
hash_entry = tk.Entry(window, width=50)

open_shodan_button = tk.Button(window, text="Abrir Shodan", command=open_shodan)

favicon_info_label = tk.Label(window, text="")
shodan_link_label = tk.Label(window, text="")
shodan_info_label = tk.Label(window, text="")

copy_results_button = tk.Button(window, text="Copiar Resultados", command=copy_results, bg="blue", fg="white")

url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
get_favicons_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
hash_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
hash_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
open_shodan_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

favicon_info_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
shodan_link_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
shodan_info_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")
copy_results_button.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="w")

# botao Limpar Resultados
clear_all_button = tk.Button(window, text="Limpar Resultados", command=clear_all, bg="red")
clear_all_button.grid(row=6, column=0, columnspan=3, padx=5, pady=200, sticky="w")

window.mainloop()
