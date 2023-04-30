import requests
import json
import tkinter as tk
from tkinter import filedialog, messagebox

def search_wayback_machine():
    # Obter a URL do usuário
    url = url_entry.get()

    # Fazer uma solicitação HTTP para o Arquivo de Internet do Wayback Machine
    response = requests.get("http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url))

    # Verificar se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Converter a resposta JSON em um objeto Python
        data = json.loads(response.text)

        # Perguntar ao usuário o nome do arquivo de saída
        output_file_name = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="arquivo.txt")

        # Salvar as URLs capturadas no arquivo de saída
        with open(output_file_name, "w", encoding="utf-8") as f:
            for url in data:
                f.write(url[0] + "\n")

        # Mostrar as URLs capturadas na tela
        urls_label.config(text="Foram capturadas as seguintes URL")
        urls_text.delete("1.0", tk.END)
        for url in data:
            urls_text.insert(tk.END, url[0] + "\n")

        # Contar o número de URLs capturadas e mostrar na tela
        count_label.config(text="Foram capturadas {} URL".format(len(data)))
    else:
        messagebox.showerror("Erro", "Não foi possível capturar as URL O servidor retornou o código de status {}.".format(response.status_code))

# Criar a janela principal
window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.geometry("1300x1000")
window.wm_state('zoomed')

# Criar os widgets da interface gráfica
url_label = tk.Label(window, text="Digite a URL que deseja procurar no Wayback Machine")
url_entry = tk.Entry(window, width=50)
search_button = tk.Button(window, text="Procurar", command=search_wayback_machine)
urls_label = tk.Label(window, text="")
urls_text = tk.Text(window, height=50, width=120)
count_label = tk.Label(window, text="")

# Posicionar os widgets na janela
url_label.grid(row=0, column=0, padx=5, pady=5)
url_entry.grid(row=0, column=1, padx=5, pady=5)
search_button.grid(row=0, column=2, padx=5, pady=5)
urls_label.grid(row=1, column=0, padx=5, pady=5)
urls_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
count_label.grid(row=3, column=0, padx=5, pady=5)

# Iniciar a execução da janela
window.mainloop()
