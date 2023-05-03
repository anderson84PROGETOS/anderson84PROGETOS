import requests
import tkinter as tk
import pyperclip

api_key = 'Digite as sua API'

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
        email_list.insert(tk.END, f"Erro - código de status HTTP: {response.status_code}")

def copy_results():
    results = email_list.get(0, tk.END)
    results_str = "\n".join(results)
    pyperclip.copy(results_str)

def clear_results():
    email_list.delete(0, tk.END)
    domain_entry.delete(0, tk.END)
        
# Configurar a janela principal
window = tk.Tk()
window.title("Hunter.io Search")
window.wm_state('zoomed')

# Adicionar widgets
domain_label = tk.Label(window, text="Digite a URL do site:", font=("Arial", 14))
domain_label.pack()

domain_entry = tk.Entry(window, width=50, font=("Arial", 14))
domain_entry.pack()

search_button = tk.Button(window, text="Buscar", font=("Arial", 14), command=search_domain)
search_button.pack()

email_list = tk.Listbox(window, width=100, height=35, font=("Arial", 12))
email_list.pack()

copy_button = tk.Button(window, text="Copiar resultados", font=("Arial", 14), command=copy_results)
copy_button.pack()

clear_button = tk.Button(window, text="Limpar resultados", font=("Arial", 14), command=clear_results)
clear_button.pack()

quit_button = tk.Button(window, text="Sair", font=("Arial", 14), command=window.quit)
quit_button.pack()

# Iniciar a janela principal
window.mainloop()

