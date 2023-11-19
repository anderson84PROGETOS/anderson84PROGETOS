import requests
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading

def search_wayback_machine():
    # Desativar o botão de busca enquanto a varredura está em andamento
    search_button["state"] = "disabled"

    # Obter a URL do usuário
    url = url_entry.get()

    # Fazer uma solicitação HTTP para o Arquivo de Internet do Wayback Machine
    response = requests.get("http://web.archive.org/cdx/search/cdx?url=*.{}/*&output=json&fl=original&collapse=urlkey".format(url))

    # Verificar se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Converter a resposta JSON em um objeto Python
        data = json.loads(response.text)

        # Configurar a barra de progresso
        progress_bar["maximum"] = len(data)
        progress_bar["value"] = 0

        # Mostrar as URLs capturadas na tela
        urls_label.config(text="Foram capturadas as seguintes URL")
        urls_text.delete("1.0", tk.END)

        for i, url in enumerate(data):
            urls_text.insert(tk.END, url[0] + "\n")

            # Atualizar a barra de progresso (agendando a atualização na thread principal)
            window.after(10, update_progress, i + 1)

        # Contar o número de URLs capturadas e mostrar na tela
        count_label.config(text="Foram capturadas {} URL".format(len(data)))
    else:
        messagebox.showerror("Erro", "Não foi possível capturar as URL. O servidor retornou o código de status {}.".format(response.status_code))

def update_progress(value):
    progress_bar["value"] = value

    # Reativar o botão de busca após a varredura
    if value == progress_bar["maximum"]:
        search_button["state"] = "normal"

def start_search_thread():
    # Desativar o botão de busca enquanto a varredura está em andamento
    search_button["state"] = "disabled"

    # Iniciar uma nova thread para a varredura
    search_thread = threading.Thread(target=search_wayback_machine)
    search_thread.start()

# Criar a janela principal
window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.wm_state('zoomed')

# Criar os widgets da interface gráfica
url_label = tk.Label(window, text="Digite a URL que deseja procurar no Wayback Machine", font=("Arial", 12))
url_entry = tk.Entry(window, width=50, font=("Arial", 12))
search_button = tk.Button(window, text="Procurar", command=start_search_thread, font=("Arial", 12), bg="#00FFFF")
urls_label = tk.Label(window, text="")
urls_text = tk.Text(window, height=42, width=158)
count_label = tk.Label(window, text="")
separator = ttk.Separator(window, orient="horizontal")
progress_bar = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")

# Posicionar os widgets na janela
url_label.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
url_entry.grid(row=1, column=0, padx=5, pady=5, columnspan=3)
search_button.grid(row=2, column=0, padx=5, pady=5, columnspan=3)
urls_label.grid(row=3, column=0, padx=5, pady=5)
urls_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
count_label.grid(row=5, column=0, padx=5, pady=5)
separator.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
progress_bar.grid(row=7, column=0, padx=5, pady=5, columnspan=3)

# salvar os arquivos.txt
# salvar os arquivos.txt
def save_urls_to_file():
    # Abre a caixa de diálogo para escolher o local do arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])

    # Se o usuário escolher um local válido
    if file_path:
        # Obtém o conteúdo das URLs
        urls_content = urls_text.get("1.0", tk.END)

        # Tenta escrever o conteúdo no arquivo
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(urls_content.strip())  # Remova espaços em branco extras no final
            messagebox.showinfo("Sucesso", "As URLs foram salvas com sucesso em {}".format(file_path))
        except Exception as e:
            messagebox.showerror("Erro", "Erro ao salvar o arquivo: {}".format(str(e)))

# Adiciona um botão "Salvar" à interface gráfica
save_button = tk.Button(window, text="Salvar", command=save_urls_to_file, font=("Arial", 12), bg="#18fa07")
save_button.grid(row=3, column=0, padx=5, pady=5, columnspan=3)

# Iniciar a execução da janela
window.mainloop()
