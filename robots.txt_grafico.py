import urllib.request
import io
import tkinter as tk
import pyperclip

# Função para obter o arquivo robots.txt
def get_robots_txt(url):
    if url.endswith('/'):
        path = url
    else:
        path = url + '/'
    req = urllib.request.urlopen(path + "robots.txt", data=None)
    data = io.TextIOWrapper(req, encoding='utf-8')
    return data.read()

# Função para lidar com o botão pressionado
def handle_click():
    url = url_entry.get()
    robots_txt = get_robots_txt(url)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, robots_txt)  

# Configuração da janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Obter arquivo robots.txt")

# Criação do campo de entrada de URL
url_label = tk.Label(root, text="Digite a url do website", font=("bold", 14))
url_entry = tk.Entry(root, width=50, font=("bold", 14))

url_label.grid(row=0, column=0, padx=5, pady=5)
url_entry.grid(row=0, column=1, padx=10, pady=0)

# Criação do botão para obter o arquivo robots.txt
get_robots_txt_button = tk.Button(root, text="Obter arquivo robots.txt", command=handle_click, font=("bold", 14))
get_robots_txt_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

# Criação do campo de texto para exibir o resultado
result_text = tk.Text(root, height=40, width=140, font=("bold", 13))
result_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

# Função para lidar com o botão "Copiar informações" pressionado
def copy_info():
    pyperclip.copy(result_text.get("1.0", "end-1c")) # Copia o conteúdo da caixa de texto para a área de transferência

# Criação do botão para copiar informações
copy_info_button = tk.Button(root, text="Copiar informações", command=copy_info, font=("bold", 13))
copy_info_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Função para lidar com o botão "Limpar campos" pressionado
def clear_fields():
    url_entry.delete(0, tk.END)
    result_text.delete(1.0, tk.END)  

# Criação do botão para limpar os campos
clear_fields_button = tk.Button(root, text="Limpar", command=clear_fields, font=("bold", 13))
clear_fields_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Inicialização da janela principal
root.mainloop()
