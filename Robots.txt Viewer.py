import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import webbrowser
from ttkthemes import ThemedStyle
from PIL import Image, ImageTk
from io import BytesIO

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
window = tk.Tk()
window.wm_state('zoomed')
window.title("Robots.txt Viewer")

# Configurando o estilo temático
style = ThemedStyle(window)
style.set_theme("itft1")  # Escolha o tema desejado (por exemplo, 'itft1'"aquativo""arc""blue""clearlooks""elegance""equilux""itft1""keramik""kroc""plastik""radiance""scidblue""smog""vista""winxpblue")

# URL do ícone
icon_url = "https://st.depositphotos.com/47577860/52372/v/450/depositphotos_523728482-stock-illustration-robots-txt-coding-icon-filled.jpg"  # Substitua pela URL do seu ícone

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

# Criar widgets
label = tk.Label(window, text="Digite URL completa do site: Exemplo https://google.com", font=("Arial Bold", 12))
label.pack(pady=10)

url_entry = tk.Entry(window, width=43, fg="black", font=("Arial Bold", 12))
url_entry.pack(pady=10)

get_button = ttk.Button(window, text="Obter robots.txt", command=get_robots_txt, style="TButton")
get_button.pack(pady=5)

search_button = ttk.Button(window, text="Pesquisar no Google por /robots.txt", command=search_on_google, style="TButton")
search_button.pack(pady=5)

# Adicionar uma barra de rolagem vertical ao widget Text
result_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, height=40, width=130, fg="black", font=("Arial Bold", 12))
result_text.pack(pady=10)

# Adicione os botões ao estilo temático
style.configure("TButton", font=("Arial Bold", 12))

# Iniciar o loop principal da interface gráfica
window.mainloop()
