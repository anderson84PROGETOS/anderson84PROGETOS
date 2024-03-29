import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
from PIL import Image, ImageTk
from io import BytesIO
from ttkthemes import ThemedStyle

def format_headers(headers):
    formatted_headers = ""
    for key, value in headers.items():
        formatted_headers += f"[{key}] {value}\n"
    return formatted_headers.strip()

def make_request(method, url, data=None, headers=None):
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
            description = "O método GET solicita a representação de um recurso específico. Requisições utilizando o método GET devem retornar apenas dados."
        elif method == "HEAD":
            response = requests.head(url, headers=headers)
            description = "O método HEAD solicita uma resposta de forma idêntica ao método GET, porém sem conter o corpo da resposta."
        elif method == "POST":
            response = requests.post(url, data=data, headers=headers)
            description = "O método POST é utilizado para submeter uma entidade a um recurso específico, frequentemente causando uma mudança no estado do recurso ou efeitos colaterais no servidor."
        elif method == "PUT":
            response = requests.put(url, data=data, headers=headers)
            description = "O método PUT substitui todas as atuais representações do recurso de destino pela carga de dados da requisição."
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
            description = "O método DELETE remove um recurso específico."
        elif method == "CONNECT":
            response = requests.request("CONNECT", url, headers=headers)
            description = "O método CONNECT estabelece um túnel para o servidor identificado pelo recurso de destino."
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers)
            description = "O método OPTIONS é usado para descrever as opções de comunicação com o recurso de destino."
        elif method == "TRACE":
            response = requests.trace(url, headers=headers)
            description = "O método TRACE executa um teste de chamada loop-back junto com o caminho para o recurso de destino."
        elif method == "PATCH":
            response = requests.patch(url, data=data, headers=headers)
            description = "O método PATCH é utilizado para aplicar modificações parciais em um recurso."
        else:
            return "Método inválido"

        response.raise_for_status()
        headers_info = format_headers(response.headers)        
        return f"\n{headers_info}\n\nDescrição:\n{description}"        
    except requests.exceptions.HTTPError as errh:
        return f"Erro HTTP: {errh}"
    except requests.exceptions.RequestException as err:
        return f"Erro de Requisição: {errh}"

def on_submit():
    url = url_entry.get()
    method = method_var.get()

    headers = {"User-Agent": linux_user_agent}
    result = make_request(method, url, headers=headers)

    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"Cabeçalho da Página ({method})\n{result}\n")
    result_text.config(state=tk.DISABLED)

# Configurar a janela principal
app = tk.Tk()
app.wm_state('zoomed')
app.title("Visualizador de Requisições HTTP")

# URL do ícone
icon_url = "https://s.lorientlejour.com/storage/attachments/1340/288429_164190.png/r/800/288429_164190.png"  # Substitua pela URL do seu ícone

# Função para baixar o ícone da web
def download_icon(url):
    response = requests.get(url)
    icon_data = BytesIO(response.content)
    return Image.open(icon_data)

# Baixar o ícone da web
icon_image = download_icon(icon_url)

# Converter a imagem para o formato Tkinter
tk_icon = ImageTk.PhotoImage(icon_image)

# Definir o ícone da janela
app.iconphoto(True, tk_icon)

# URL Entry
url_label = tk.Label(app, text="Digite a URL do website", font=("Arial", 12))
url_label.pack(pady=2)

url_entry = tk.Entry(app, width=40, font=("Arial", 12))
url_entry.pack(pady=5)

# Method Selector
method_var = tk.StringVar()
method_var.set("GET")

method_label = tk.Label(app, text="Selecione o método", font=("Arial", 13))
method_label.pack()

# Use ttk.OptionMenu em vez de tk.OptionMenu
method_menu_style = ThemedStyle(app)
method_menu_style.set_theme("ubuntu")
method_menu = ttk.OptionMenu(app, method_var, "GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH")
method_menu.pack(pady=10)

# Configurar a fonte para o estilo TButton
method_menu["menu"].configure(font=("Arial", 12))

# Submit Button
submit_button = ttk.Button(app, text="Enviar", command=on_submit, style="TButton")
submit_button.pack(pady=10)

# Configurar a cor para o estilo TButton
submit_button_style = ThemedStyle(app)
submit_button_style.set_theme("ubuntu")
submit_button_style.configure("TButton", font=("Arial", 13), foreground="#042047", background="#11e7f2")

# Result Text
result_text = scrolledtext.ScrolledText(app, width=152, height=43, state=tk.DISABLED, font=("Arial", 11))
result_text.pack(pady=10)

# User Agent
linux_user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

app.mainloop()
