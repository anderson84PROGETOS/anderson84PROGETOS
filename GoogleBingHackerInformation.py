import tkinter as tk
from tkinter import scrolledtext, Entry, StringVar, OptionMenu, Label, ttk
import webbrowser
import requests
from bs4 import BeautifulSoup
from ttkthemes import ThemedStyle
from PIL import Image, ImageTk
from io import BytesIO

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
        "Show only IP addresses (opens multiple tabs)": f"({site_nome}) (site:*.*.29.* | site:*.*.28.* | site:*.*.27.* | site:*.*.26.* | site:*.*.25.* | site:*.*.24.* | site:*.*.23.* | site:*.*.22.* | site:*.*.21.* | site:*.*.20.* | site:*.*.19.* | site:*.*.18.* | site:*.*.17.* | site:*.*.16.* | site:*.*.15.* | site:*.*.14.* | site:*.*.13.* | site:*.*.12.* | site:*.*.11.* | site:*.*.10.* | site:*.*.9.* | site:*.*.8.* | site:*.*.7.* | site:*.*.6.* | site:*.*.5.* | site:*.*.4.* | site:*.*.3.* | site:*.*.2.* | site:*.*.1.* | site:*.*.0.*)",
        "Para encontrar documentos Apresentaçoes e desenhos vazados": f"site:docs.{site_nome}/document/d",
        "Para encontrar presentation": f"site:docs.{site_nome}/presentation/d",
        "Para encontrar drawings": f"site:docs.{site_nome}/drawings/d",
        "Já para encontrar qualquer tipo de arquivo como imagens vídeos zip e PDF": f"site:docs.{site_nome}/file/d",
        "Agora se você quer encontrar uma pasta completa do Google Drive exposta": f"site:docs.{site_nome}/folder/d",
        "Esses para achar itens secreto": f"site:docs.{site_nome}/open intext:secreto",
        "Achar inurl e index.php": f'"{site_nome}" + inurl=index.php?id=1',
        "Achar Arquivo pdf": f"site:{site_nome} ext:pdf",
        "Achar Arquivo xml": f"site:{site_nome} ext:xml",
        "Achar Arquivo docx": f"site:{site_nome} ext:docx",
    }

    return consultas.get(dork_selecionada, "")

def obter_dados_hacking(motor_pesquisa):
    site_nome = site_entry.get()
    if not site_nome:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, insira o nome do site.")
        return

    dork_selecionada = dork_var.get()
    if not dork_selecionada:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, selecione uma Dork.")
        return

    # Construir a consulta
    consulta = construir_consulta_dork(site_nome, dork_selecionada)

    if not consulta:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Consulta não disponível para a Dork selecionada.")
        return

    if motor_pesquisa == "Google":
        url = f"https://www.google.com/search?q={consulta.replace(' ', '+')}"
    elif motor_pesquisa == "Bing":
        url = f"https://www.bing.com/search?q={consulta.replace(' ', '+')}"
    else:
        return

    # Adicionar um cabeçalho User-Agent à solicitação
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'}

    # Abrir a consulta no navegador padrão
    webbrowser.open_new_tab(url)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verificar se houve erro na solicitação HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        resultado = soup.get_text()

        # Adicionar uma nova linha antes de exibir o resultado
        resultado_completo = f"\n{motor_pesquisa} - site:{site_nome} {dork_selecionada}\n\n\n{consulta}\n\n\n\n\n\n\n{resultado}"
        result_text.delete(1.0, tk.END)  # Limpar o conteúdo atual no widget ScrolledText
        result_text.insert(tk.END, resultado_completo)  # Inserir o novo conteúdo
    except requests.exceptions.RequestException as e:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Erro ao acessar a URL: {e}")

# Criar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Google Bing Hacker Information")

# Configurando o estilo temático
style = ThemedStyle(window)
style.set_theme("itft1")  # Escolha o tema desejado

# URL do ícone
icon_url = "https://images.frandroid.com/wp-content/uploads/2021/10/google-bing.jpg"  # Substitua pela URL do seu ícone

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
    "Show only IP addresses (opens multiple tabs)",
    "Para encontrar documentos Apresentaçoes e desenhos vazados",
    "Para encontrar presentation",
    "Para encontrar drawings",
    "Já para encontrar qualquer tipo de arquivo como imagens vídeos zip e PDF",
    "Agora se você quer encontrar uma pasta completa do Google Drive exposta",
    "Esses para achar itens secreto",
    "Achar inurl e index.php",
    "Achar Arquivo pdf",
    "Achar Arquivo xml",
    "Achar Arquivo docx",
]

# Variável para armazenar a Dork selecionada
dork_var = StringVar(window)
dork_var.set(dorks[0])  # Inicialmente, selecione a primeira Dork

# Rótulo para instruções
instrucoes_label = Label(dorks_frame, text="Por favor, selecione uma Dork", font=("Arial", 12))
instrucoes_label.grid(padx=530, pady=0)

# Dropdown para selecionar a Dork do Google
dork_menu = OptionMenu(dorks_frame, dork_var, *dorks)
dork_menu.grid(column=0, row=1)

# Criar o frame para a entrada do nome do site
site_frame = tk.Frame(window)
site_frame.grid(column=0, row=1, padx=5)

# Rótulo para instruções
site_label = Label(site_frame, text="Por favor, insira o nome do site ou URL do site", font=("Arial", 12))
site_label.grid(column=0, row=0)

# Entrada do nome do site
site_entry = Entry(site_frame, width=34, font=("Arial", 12))
site_entry.grid(column=0, row=1, padx=5, pady=2)

# Criar os botões para obter dados usando ttkButton
obter_dados_google_button = ttk.Button(window, text="Search Google", command=lambda: obter_dados_hacking("Google"))
obter_dados_google_button.grid(column=0, row=1, pady=(100, 5))

obter_dados_bing_button = ttk.Button(window, text="Search Bing", command=lambda: obter_dados_hacking("Bing"))
obter_dados_bing_button.grid(column=0, row=2, pady=8)

# Criar o frame para os resultados
result_frame = tk.Frame(window)
result_frame.grid(column=0, row=3, columnspan=2, padx=5, pady=2)

# Criar os widgets ScrolledText para os resultados do Google e Bing
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=135, height=37, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

# Iniciar o loop da janela
window.mainloop()
