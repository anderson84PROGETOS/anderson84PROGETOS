import tkinter as tk
from tkinter import scrolledtext, Entry, StringVar, OptionMenu, Label
import webbrowser
import requests
from bs4 import BeautifulSoup
import re

# Função para construir a consulta de busca (dork)
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
        "achar inurl e index.php": f'"{site_nome}" + inurl=index.php?id=1',
        "achar arquivo pdf": f"site:{site_nome} ext:pdf",
        "achar arquivo xml": f"site:{site_nome} ext:xml",
        "achar arquivo docx": f"site:{site_nome} ext:docx",
        "achar arquivo intext":f"intext:{site_nome}",
        "achar arquivo txt senha url": f"filetype:txt intext:senha url site:{site_nome}",       
        "achar Arquivo nos Servidores do Scribd": f"servidores site:scribd.com AND:{site_nome}",
        "achar arquivo sql aperte a tecla espaço ou nome do site": f"{site_nome} filetype:sql",
        "achar arquivo env": f"filetype:env {site_nome}",
        "Achar arquivo inurl": f"inurl:{site_nome}",
        "Achar arquivo pdf xlsx docx txt": f"'{site_nome}' filetype:pdf OR filetype:xlsx OR filetype:docx OR filetype:txt",
        "Achar arquivo txt": f"site:{site_nome} filetype:txt",
        "Achar arquivo WEBCAM 7 Aperte Espasso": f"{site_nome} intitle:\"WEBCAM 7\" -inurl:/admin.html",
        "Achar arquivo robots.txt": f"{site_nome} robots.txt",
        "Achar arquivo senha": f"intitle:\"index of\" intext:{site_nome}",
        "Achar nome de pessoa": f'intext:"{site_nome}"',
        "Nome do IP": f'IP:{site_nome}',
        "Achar arquivo pdf confidencial": f'filetype:pdf intitle:confidencial site:{site_nome}',
        "Confidencial": f'intitle:confidencial filetype:pdf intext:"{site_nome}"',
        "Achar credit card": f'site:pastebin.com {site_nome} credit card',
        "Achar coisas em google drive": f'site:drive.google.com {site_nome}',
        "Achar email": f'"{site_nome}"',    

    }

    return consultas.get(dork_selecionada, "")

def extrair_informacoes_pagina(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text()))

        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http', 'www')):
                links.add(href)
            elif href.startswith('/'):
                links.add(url + href)

        links_especificos = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'scribd.com' in href or 'telemetr.io' in href or 'telegram' in href:
                links_especificos.append(href)

        spans = [span.get_text() for span in soup.find_all('span')]

        return emails, links, links_especificos, spans

    except requests.exceptions.RequestException as e:
        return str(e), set(), [], []

def exibir_resultados_no_texto(emails, links, links_especificos, spans, consulta, dork_selecionada):
    resultado_completo = (
        f"Pesquisa: Google - Dork: {dork_selecionada}\n\n"
        f"Consulta: {consulta}\n"
        f"==============================\n\n"
        f"Resultado Encontrados para: {consulta}\n\n"
        f"----------------------------------\n"
        f"Emails Encontrados:\n\n"
    )

    if emails:
        for email in emails:
            resultado_completo += f"- {email}\n"
    else:
        resultado_completo += "Nenhum email encontrado.\n"

    resultado_completo += f"\n----------------------------------\n"
    resultado_completo += f"Links Encontrados:\n\n"

    if links:
        for i, link in enumerate(links, 1):
            resultado_completo += f"{i}. {link}\n\n"
    else:
        resultado_completo += "Nenhum link encontrado.\n"

    resultado_completo += f"\n=============================\n"
    resultado_completo += f"Links Específicos Encontrados\n\n"

    if links_especificos:
        for i, link in enumerate(links_especificos, 1):
            resultado_completo += f"{i}. {link}\n\n"
    else:
        resultado_completo += "Nenhum link específico encontrado.\n"

    resultado_completo += f"\n===================================\n"
    resultado_completo += f"Conteúdo dentro de <span>\n\n"

    if spans:
        for span in spans:
            resultado_completo += f"- {span}\n"
    else:
        resultado_completo += "Nenhum conteúdo <span> encontrado.\n"

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, resultado_completo)

def obter_dados(site_nome, dork_selecionada, abrir_google=False):
    consulta = construir_consulta_dork(site_nome, dork_selecionada)

    if not consulta:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Consulta não disponível para a Dork selecionada.")
        return

    url = f"https://www.google.com/search?q={consulta}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    if abrir_google:
        webbrowser.open_new_tab(url)

    emails, links, links_especificos, spans = extrair_informacoes_pagina(url, headers)
    exibir_resultados_no_texto(emails, links, links_especificos, spans, consulta, dork_selecionada)

def obter_dados_hacking():
    site_nome = site_entry.get()
    dork_selecionada = dork_var.get()

    if not site_nome or not dork_selecionada:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, insira o nome do site e selecione uma Dork.")
        return

    obter_dados(site_nome, dork_selecionada, abrir_google=True)

def obter_dados_sem_google():
    site_nome = site_entry.get()
    dork_selecionada = dork_var.get()

    if not site_nome or not dork_selecionada:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, insira o nome do site e selecione uma Dork.")
        return

    obter_dados(site_nome, dork_selecionada, abrir_google=False)

window = tk.Tk()
window.wm_state('zoomed')
window.title("Google Dork")

dorks_frame = tk.Frame(window)
dorks_frame.grid(column=0, row=0, padx=20, pady=3)

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
    "achar inurl e index.php",
    "achar arquivo pdf",
    "achar arquivo xml",
    "achar arquivo docx",
    "achar arquivo intext",
    "achar arquivo txt senha url",
    "achar Arquivo nos Servidores do Scribd",
    "achar arquivo sql aperte a tecla espaço ou nome do site",
    "achar arquivo env",
    "Achar arquivo inurl",
    "Achar arquivo pdf xlsx docx txt",
    "Achar arquivo txt",
    "Achar arquivo WEBCAM 7 Aperte Espasso",
    "Achar arquivo robots.txt",
    "Achar arquivo senha",
    "Achar nome de pessoa",
    "Nome do IP",
    "Achar arquivo pdf confidencial",
    "Confidencial",
    "Achar credit card",
    "Achar coisas em google drive",
    "Achar email",
]

dork_var = StringVar(window)
dork_var.set(dorks[0])

instrucoes_label = Label(dorks_frame, text="Por Favor Selecione uma Dork", font=("Arial", 12))
instrucoes_label.grid(padx=530, pady=0)

dorks_frame.option_add("*Font", ("Arial", 10))  # Define fonte padrão para widgets filhos do dorks_frame
dork_menu = OptionMenu(dorks_frame, dork_var, *dorks)
dork_menu.grid(column=0, row=1)

site_frame = tk.Frame(window)
site_frame.grid(column=0, row=1, padx=2)

site_label = Label(site_frame, text="Informe o Nome ou Conteúdo Para Pesquisa", font=("Arial", 12))
site_label.grid(column=0, row=0)

site_entry = Entry(site_frame, width=50, font=("Arial", 12))
site_entry.grid(column=0, row=1, padx=5, pady=2)

obter_dados_google_button = tk.Button(window, text="Search Google", command=obter_dados_hacking, bg='#00FF00',font=("Arial", 12, "bold"))
obter_dados_google_button.grid(column=0, row=2, pady=(10, 5))

obter_dados_sem_google_button = tk.Button(window, text="Obter Resultados", command=obter_dados_sem_google, bg='#07dbd4', font=("Arial", 12, "bold"))
obter_dados_sem_google_button.grid(column=0, row=3, pady=(10, 5))

result_frame = tk.Frame(window)
result_frame.grid(column=0, row=4, columnspan=2, padx=5, pady=2)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=135, height=37, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

window.mainloop()
