import tkinter as tk
from tkinter import scrolledtext, Entry, StringVar, OptionMenu, Label
import webbrowser  # Importar o módulo webbrowser
import requests
from bs4 import BeautifulSoup

def obter_dados_google_hacking():
    site_nome = site_entry.get()
    if not site_nome:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, insira o nome do site.")
        return

    dork_selecionada = dork_var.get()
    if not dork_selecionada:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, selecione uma Dork do Google.")
        return

    # Construir a consulta
    consulta = f"site:{site_nome} {dork_selecionada}".replace(" ", "+")
    url = f"https://www.google.com/search?q={consulta}"

    # Abrir a consulta no navegador padrão
    webbrowser.open_new_tab(url)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar se houve erro na solicitação HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        resultado = soup.get_text()

        # Adicionar uma nova linha antes de exibir o resultado
        resultado_completo = f"site:{site_nome} {dork_selecionada}\n\n\n{resultado}"
        result_text.delete(1.0, tk.END)  # Limpar o conteúdo atual no widget ScrolledText
        result_text.insert(tk.END, resultado_completo)  # Inserir o novo conteúdo
    except requests.exceptions.RequestException as e:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Erro ao acessar a URL: {e}")        

# Criar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Google Hacking Information Gathering")

# Criar o frame para a lista de Dorks do Google
dorks_frame = tk.Frame(window)
dorks_frame.grid(column=0, row=0, padx=10, pady=10)

# Lista de Dorks do Google
dorks = [
    "Publicly exposed documents",
    "Directory listing vulns",
    "Configuration files exposed",
    "Database files exposed",
    "Log files exposed",
    "Backup and old files",
    "Login pages",
    "SQL errors",
    "PHP errors/warnings",
    "phpinfo()",
    "Search pastebin.com / pasting sites",
    "Search github.com and gitlab.com",
    "Search stackoverflow.com",
    "Signup pages",
    "Find Subdomains",
    "Find Sub-Subdomains",
    "Search in Wayback Machine",
    "Show only IP addresses (opens multiple tabs)"
]

# Variável para armazenar a Dork selecionada
dork_var = StringVar(window)
dork_var.set(dorks[0])  # Inicialmente, selecione a primeira Dork

# Rótulo para instruções
instrucoes_label = Label(dorks_frame, text="Por favor, selecione uma Dork do Google")
instrucoes_label.grid(column=0, row=0, padx=5, pady=2)

# Dropdown para selecionar a Dork do Google
dork_menu = OptionMenu(dorks_frame, dork_var, *dorks)
dork_menu.grid(column=0, row=1)

# Criar o frame para a entrada do nome do site
site_frame = tk.Frame(window)
site_frame.grid(column=0, row=1, padx=5, pady=2)

# Rótulo para instruções
site_label = Label(site_frame, text="Por favor, insira o nome do site")
site_label.grid(column=0, row=0, padx=5, pady=2)

# Entrada do nome do site
site_entry = Entry(site_frame, width=30, font=("Arial", 12))
site_entry.grid(column=0, row=1, padx=5, pady=2)

# Criar o botão para obter dados
obter_dados_button = tk.Button(window, text="Search Google", command=obter_dados_google_hacking, font=("Arial", 12) ,bg="#00FFFF")
obter_dados_button.grid(column=0, row=2, pady=10)

# Criar o frame para o resultado
result_frame = tk.Frame(window)
result_frame.grid(column=0, row=3, padx=5, pady=2)

# Criar o widget ScrolledText
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=138, height=40, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

# Iniciar o loop da janela
window.mainloop()
