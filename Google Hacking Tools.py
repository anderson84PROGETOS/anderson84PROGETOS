import tkinter as tk
from tkinter import scrolledtext, Entry, StringVar, OptionMenu, Label
import webbrowser  # Importar o módulo webbrowser
import requests
from bs4 import BeautifulSoup

def construir_consulta_dork(site_nome, dork_selecionada):
    consultas = {
        "Publicly exposed documents": f"site:{site_nome} ext:doc | ext:docx | ext:odt | ext:rtf | ext:sxw | ext:psw | ext:ppt | ext:pptx | ext:pps | ext:csv",
        "Directory listing vulns": f"site:{site_nome} intitle:index.of",
        "Configuration files exposed": f"site:{site_nome} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini | ext:env",
        "Database files exposed": f"site:{site_nome} ext:sql | ext:dbf | ext:mdb",
        "Log files exposed": f"site:{site_nome} ext:log",
        "Backup and old files": f"site:{site_nome} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup",
        "Login pages": f"site:{site_nome} inurl:login | inurl:signin | intitle:Login | intitle:\"sign in\" | inurl:auth",
        "SQL errors": f"site:{site_nome} intext:\"sql syntax near\" | intext:\"syntax error has occurred\" | intext:\"incorrect syntax near\" | intext:\"unexpected end of SQL command\" | intext:\"Warning: mysql_connect()\" | intext:\"Warning: mysql_query()\" | intext:\"Warning: pg_connect()\"",
        "PHP errors/warnings": f"site:{site_nome} \"PHP Parse error\" | \"PHP Warning\" | \"PHP Error\"",
        "phpinfo()": f"site:{site_nome} ext:php intitle:phpinfo \"published by the PHP Group\"",
        "Search pastebin.com / pasting sites": f"site:pastebin.com | site:paste2.org | site:pastehtml.com | site:slexy.org | site:snipplr.com | site:snipt.net | site:textsnip.com | site:bitpaste.app | site:justpaste.it | site:heypasteit.com | site:hastebin.com | site:dpaste.org | site:dpaste.com | site:codepad.org | site:jsitor.com | site:codepen.io | site:jsfiddle.net | site:dotnetfiddle.net | site:phpfiddle.org | site:ide.geeksforgeeks.org | site:repl.it | site:ideone.com | site:paste.debian.net | site:paste.org | site:paste.org.ru | site:codebeautify.org  | site:codeshare.io | site:trello.com {site_nome}",
        "Search github.com and gitlab.com": f"site:github.com | site:gitlab.com {site_nome}",
        "Search stackoverflow.com": f"site:stackoverflow.com {site_nome}",
        "Signup pages": f"site:{site_nome} inurl:signup | inurl:register | intitle:Signup",
        "Find Subdomains": f"site:*.{site_nome}",
        "Find Sub-Subdomains": f"site:*.*.{site_nome}",
        "Search in Wayback Machine": f"https://web.archive.org/web/*/{site_nome}/*",
        "Show only IP addresses (opens multiple tabs)": f"({site_nome}) (site:*.*.29.* | site:*.*.28.* | site:*.*.27.* | site:*.*.26.* | site:*.*.25.* | site:*.*.24.* | site:*.*.23.* | site:*.*.22.* | site:*.*.21.* | site:*.*.20.* | site:*.*.19.* | site:*.*.18.* | site:*.*.17.* | site:*.*.16.* | site:*.*.15.* | site:*.*.14.* | site:*.*.13.* | site:*.*.12.* | site:*.*.11.* | site:*.*.10.* | site:*.*.9.* | site:*.*.8.* | site:*.*.7.* | site:*.*.6.* | site:*.*.5.* | site:*.*.4.* | site:*.*.3.* | site:*.*.2.* | site:*.*.1.* | site:*.*.0.*)"
    }

    return consultas.get(dork_selecionada, "")

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
    consulta = construir_consulta_dork(site_nome, dork_selecionada)

    if not consulta:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Consulta não disponível para a Dork selecionada.")
        return

    url = f"https://www.google.com/search?q={consulta.replace(' ', '+')}"

    # Abrir a consulta no navegador padrão
    webbrowser.open_new_tab(url)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar se houve erro na solicitação HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        resultado = soup.get_text()

        # Adicionar uma nova linha antes de exibir o resultado       
        resultado_completo = f"site:{site_nome} {dork_selecionada}\n\n\n{consulta}\n\n\n\n\n\n\n{resultado}"
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
obter_dados_button = tk.Button(window, text="Search Google", command=obter_dados_google_hacking, font=("Arial", 12), bg="#00FFFF")
obter_dados_button.grid(column=0, row=2, pady=10)

# Criar o frame para o resultado
result_frame = tk.Frame(window)
result_frame.grid(column=0, row=3, padx=5, pady=2)

# Criar o widget ScrolledText
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=138, height=40, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

# Iniciar o loop da janela
window.mainloop()
