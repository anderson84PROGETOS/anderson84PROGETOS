import requests
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import pyperclip

# Função para ler a chave da API a partir de um arquivo .txt
def read_api_key_from_file(file_path='api_key.txt'):
    try:
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
        return api_key
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado.")
        return None

# Função para salvar a chave da API em um arquivo .txt
def save_api_key_to_file(api_key, file_path='api_key.txt'):
    with open(file_path, 'w') as file:
        file.write(api_key)

# Função para realizar a pesquisa de domínio
def search_domain():
    domain = domain_entry.get().split('/')[2]
    url_api = f'https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}'
    response = requests.get(url_api)
    if response.status_code == 200:
        results = response.json()['data']['emails']
        email_list.delete(0, tk.END)
        for result in results:
            email_list.insert(tk.END, result['value'])
    else:
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, f'Erro - código de status HTTP: {response.status_code}')

# Função para limpar os resultados
def clear_results():
    email_list.delete(0, tk.END)

# Função para exibir a chave da API
def show_api_key():
    if api_key:
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, f"A chave da API atual é:  {api_key}")
    else:
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, "Nenhuma chave da API inserida.")

# Função para salvar os resultados em um arquivo
def save_results():
    results = email_list.get(0, tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write('\n'.join(results))
        messagebox.showinfo("Salvo com sucesso", "Resultados salvos com sucesso!")

# Função para inserir uma nova chave da API
def set_api_key():
    global api_key
    api_key = simpledialog.askstring("Chave da API", "Informe a nova chave da API: ")
    if api_key:
        save_api_key_to_file(api_key)
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, f'Chave API inserida com sucesso:  {api_key}')

# Ler a chave da API do arquivo ou solicitar ao usuário se não existir
api_key = read_api_key_from_file()
if api_key is None:
    set_api_key()

# Criar a janela principal
window = tk.Tk()
window.title('Hunter.io Search')
window.state('zoomed')

# Elementos da interface gráfica
domain_label = tk.Label(window, text='Digite a URL do site', font=('Arial', 14))
domain_label.pack()

domain_entry = tk.Entry(window, width=50, font=('Arial', 14))
domain_entry.pack()

button_frame = tk.Frame(window)
button_frame.pack(pady=10)

search_button = tk.Button(button_frame, text='Hunter.io Search Busca Email', font=('Arial', 14), command=search_domain, bg='#0ae5f5')
search_button.pack(side=tk.LEFT)

clear_button = tk.Button(button_frame, text='Limpar resultados', font=('Arial', 14), command=clear_results, bg='#fc0324')
clear_button.pack(side=tk.RIGHT, pady=10)

save_button = tk.Button(button_frame, text='Salvar Resultados', font=('Arial', 14), command=save_results, bg='#00ff00')
save_button.pack(side=tk.RIGHT, padx=10)

email_list = tk.Listbox(window, width=100, height=35, font=('Arial', 13))
email_list.pack()

set_api_key_button = tk.Button(window, text='Inserir Nova Chave da API', font=('Arial', 12), command=set_api_key, bg='#9c178a')
set_api_key_button.pack(pady=10)

# Botão para mostrar a chave atual
show_api_key_button = tk.Button(window, text='Mostrar Chave Atual', font=('Arial', 12), command=show_api_key, bg='#f0fc03')
show_api_key_button.pack()

window.mainloop()
