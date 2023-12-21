import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import webbrowser

def get_robots_txt():
    url = url_entry.get().strip()

    if not url:
        messagebox.showinfo("Aviso", "Por favor, digite uma URL válida.")
        return

    # Adiciona uma barra no final da URL, se não houver
    if not url.endswith('/'):
        url += '/'

    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, 'Carregando...')

    try:
        response = fetch_robots_txt(url)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, response)
    except Exception as e:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, 'Erro: ' + str(e))

def fetch_robots_txt(url):
    try:
        response = requests.get(url + 'robots.txt')
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception('Erro na solicitação HTTP: ' + str(e))

def search_on_google():
    query = url_entry.get().strip() + '/robots.txt'

    if query:
        webbrowser.open('https://www.google.com/search?q=' + query)
    else:
        messagebox.showinfo("Aviso", "Por favor, digite algo para pesquisar.")

# Criar a janela principal
app = tk.Tk()
app.wm_state('zoomed')
app.title("Robots.txt Viewer")

# Criar widgets
label = tk.Label(app, text="Digite URL completa do site: Exemplo https://google.com", font=("Arial Bold", 12))
label.pack(pady=10)

url_entry = tk.Entry(app, width=40, fg="black", font=("Arial Bold", 12))
url_entry.pack(pady=10)

get_button = tk.Button(app, text="Obter robots.txt", command=get_robots_txt, bg="#12efff", fg="black", font=("Arial Bold", 12))
get_button.pack(pady=5)

search_button = tk.Button(app, text="Pesquisar no Google por /robots.txt", command=search_on_google, bg="#05ff48", fg="black", font=("Arial Bold", 12))
search_button.pack(pady=5)

# Adicionar uma barra de rolagem vertical ao widget Text
result_text = scrolledtext.ScrolledText(app, wrap=tk.WORD, height=40, width=130, fg="black", font=("Arial Bold", 12))
result_text.pack(pady=10)


# Iniciar o loop principal da interface gráfica
app.mainloop()
