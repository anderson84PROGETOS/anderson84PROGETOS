import urllib.request
import io
import tkinter as tk
from tkinter import Scrollbar, filedialog
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

# Função para copiar o conteúdo da caixa de texto para a área de transferência
def copy_info():
    pyperclip.copy(result_text.get("1.0", "end-1c"))  

# Função para limpar o campo de texto result_text
def clear_result_text():
    result_text.delete(1.0, tk.END)

# Função para salvar o conteúdo do campo de texto em um arquivo
def save_file():
    content = result_text.get("1.0", "end-1c")
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

# Função para limpar os campos
def clear_fields():
    url_entry.delete(0, tk.END)
    clear_result_text()

# Configuração da janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Obter arquivo robots.txt")

# Criação do campo de entrada de URL
url_label = tk.Label(root, text="Digite a URL do website", font=("bold", 12))
url_entry = tk.Entry(root, width=50, font=("bold", 12))

url_label.grid(row=0, column=0, padx=5, pady=15, columnspan=2)
url_entry.grid(row=1, column=0, padx=10, pady=10, columnspan=2)

# Criação do botão para obter o arquivo robots.txt
get_robots_txt_button = tk.Button(root, text="Obter arquivo robots.txt", command=handle_click, font=("bold", 12), bg="#1bf0f7")
get_robots_txt_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

# Criação da barra de rolagem
scrollbar = Scrollbar(root)
scrollbar.grid(row=3, column=2, rowspan=2, sticky='ns')

# Criação do campo de texto para exibir o resultado
result_text = tk.Text(root, height=37, width=128, font=("bold", 13), yscrollcommand=scrollbar.set)
result_text.grid(row=3, column=0, columnspan=2, padx=50, pady=5)

scrollbar.config(command=result_text.yview)

# Criação do botão para salvar o conteúdo em um arquivo
save_file_button = tk.Button(root, text="Salvar arquivo", command=save_file, font=("bold", 12), bg="#00FF00")
save_file_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

# Criação do botão para limpar apenas o campo de texto result_text
clear_result_text_button = tk.Button(root, text="Limpar Resultado", command=clear_result_text, font=("bold", 12), bg="#D2691E")
clear_result_text_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

# Inicialização da janela principal
root.mainloop()
