#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import quote

# ---------------------------------------------------------------------------
# MOTORES DE BUSCA
# ---------------------------------------------------------------------------
MOTORES = {
    "Google":     "https://www.google.com/search?q={q}",
    "Bing":       "https://www.bing.com/search?q={q}",
    "DuckDuckGo": "https://duckduckgo.com/?q={q}",
    "Yandex":     "https://yandex.com/search/?text={q}",
    "Brave":      "https://search.brave.com/search?q={q}",
}

# ---------------------------------------------------------------------------
# BASE DE DORKS — lista de tuplas (RÓTULO, TEMPLATE)
# ---------------------------------------------------------------------------
DORKS = [
    # ── PDF ──
    ("PDF", 'site:{site} filetype:pdf'),
    ("PDF - index of", 'site:{site} filetype:pdf intitle:"index of"'),
    ("PDF - confidencial", 'site:{site} filetype:pdf intext:confidencial'),
    ("PDF - senha/password", 'site:{site} filetype:pdf intext:senha OR intext:password'),
    ("PDF - download", 'site:{site} filetype:pdf inurl:download'),
    ("PDF - backup", 'site:{site} filetype:pdf inurl:backup'),
    ("PDF - cpf/rg", 'site:{site} filetype:pdf (intext:cpf OR intext:rg)'),

    # ── DOC / DOCX ──
    ("DOC", 'site:{site} filetype:doc'),
    ("DOCX", 'site:{site} filetype:docx'),
    ("DOC ou DOCX", 'site:{site} (filetype:doc OR filetype:docx)'),
    ("DOC - senha", 'site:{site} filetype:doc intext:senha'),
    ("DOCX - contrato", 'site:{site} filetype:docx intext:contrato'),
    ("DOC - backup", 'site:{site} filetype:doc inurl:backup'),
    ("DOCX - folha de pagamento", 'site:{site} filetype:docx intext:folha de pagamento'),
    ("DOC/DOCX - confidencial", 'site:{site} (filetype:doc OR filetype:docx) intitle:"confidencial"'),

    # ── TXT ──
    ("TXT", 'site:{site} filetype:txt'),
    ("TXT - senha", 'site:{site} filetype:txt intext:senha'),
    ("TXT - password", 'site:{site} filetype:txt intext:password'),
    ("TXT - usuario", 'site:{site} filetype:txt intext:usuario'),
    ("TXT - backup", 'site:{site} filetype:txt inurl:backup'),
    ("TXT - log", 'site:{site} filetype:txt inurl:log'),
    ("TXT - index of", 'site:{site} filetype:txt intitle:"index of"'),
    ("TXT - chave/token", 'site:{site} filetype:txt intext:chave OR intext:token'),

    # ── CSV ──
    ("CSV", 'site:{site} filetype:csv'),
    ("CSV - cpf", 'site:{site} filetype:csv intext:cpf'),
    ("CSV - cnpj", 'site:{site} filetype:csv intext:cnpj'),
    ("CSV - email", 'site:{site} filetype:csv intext:email'),
    ("CSV - password", 'site:{site} filetype:csv intext:password'),
    ("CSV - export", 'site:{site} filetype:csv inurl:export'),
    ("CSV - backup", 'site:{site} filetype:csv inurl:backup'),
    ("CSV - index of", 'site:{site} filetype:csv intitle:"index of"'),
    ("CSV - download", 'site:{site} filetype:csv inurl:download'),

    # ── JPG / JPEG ──
    ("JPG", 'site:{site} filetype:jpg'),
    ("JPG ou JPEG", 'site:{site} (filetype:jpg OR filetype:jpeg)'),
    ("JPG - upload", 'site:{site} filetype:jpg inurl:upload'),
    ("JPG - galeria", 'site:{site} filetype:jpg inurl:galeria'),
    ("JPG - docs/documentos", 'site:{site} filetype:jpg inurl:docs OR inurl:documentos'),

    # ── PNG ──
    ("PNG", 'site:{site} filetype:png'),
    ("PNG - logo", 'site:{site} filetype:png inurl:logo'),
    ("PNG - upload", 'site:{site} filetype:png inurl:upload'),
    ("PNG - index of /imagens", 'site:{site} filetype:png intitle:"index of" /imagens'),

    # ── GIF ──
    ("GIF", 'site:{site} filetype:gif'),
    ("GIF - banner", 'site:{site} filetype:gif inurl:banner'),

    # ── WEBP ──
    ("WEBP", 'site:{site} filetype:webp'),
    ("WEBP - img", 'site:{site} filetype:webp inurl:img'),

    # ── EXTRAS ──
    ("JPG - upload (extra)", 'site:{site} inurl:upload filetype:jpg'),
    ("PNG - imagesize", 'site:{site} filetype:png imagesize:1000x1000'),

    # ── MP4 ──
    ("MP4", 'site:{site} filetype:mp4'),
    ("MP4 - video", 'site:{site} filetype:mp4 inurl:video'),
    ("MP4 - uploads", 'site:{site} filetype:mp4 inurl:uploads'),
    ("MP4 - media", 'site:{site} filetype:mp4 inurl:media'),
    ("MP4 - index of", 'site:{site} filetype:mp4 intitle:"index of"'),

    # ── MP3 ──
    ("MP3", 'site:{site} filetype:mp3'),
    ("MP3 - audio", 'site:{site} filetype:mp3 inurl:audio'),
    ("MP3 - podcast", 'site:{site} filetype:mp3 inurl:podcast'),
    ("MP3 - index of", 'site:{site} filetype:mp3 intitle:"index of"'),

    # ── WAV ──
    ("WAV", 'site:{site} filetype:wav'),
    ("WAV - audio", 'site:{site} filetype:wav inurl:audio'),
    ("WAV - index of /audio", 'site:{site} filetype:wav intitle:"index of" /audio'),

    # ── MOV ──
    ("MOV", 'site:{site} filetype:mov'),
    ("MOV - video", 'site:{site} filetype:mov inurl:video'),
    ("MOV - storage", 'site:{site} filetype:mov inurl:storage'),

    # ── CURINGAS ──
    ("Midia - index of", 'site:{site} intitle:"index of" (mp4 OR mp3 OR wav OR mov)'),
    ("Todos os documentos", 'site:{site} (filetype:pdf OR filetype:doc OR filetype:docx OR filetype:txt OR filetype:csv)'),
    ("Arquivos + dados sensiveis", 'site:{site} (filetype:csv OR filetype:xls OR filetype:pdf) (intext:cpf OR intext:cnpj OR intext:email)'),
    ("Diretorios abertos", 'site:{site} intitle:"index of" (pdf OR csv OR xls OR zip)'),
    ("Backups antigos", 'site:{site} (filetype:bak OR filetype:old OR filetype:tmp)'),

    # ═══════════════════════════════════════════════════════════════════════
    # PACOTE NOVO — dorks com rótulos
    # ═══════════════════════════════════════════════════════════════════════
    ("Documentos expostos publicamente", 'site:{site} ext:doc | ext:docx | ext:odt | ext:rtf | ext:sxw | ext:psw | ext:ppt | ext:pptx | ext:pps | ext:csv'),
    ("Vulnerabilidades de listagem de diretórios", 'site:{site} intitle:index.of'),
    ("Arquivos de configuração expostos", 'site:{site} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini | ext:env'),
    ("Arquivos de banco de dados expostos", 'site:{site} ext:sql | ext:dbf | ext:mdb'),
    ("Arquivos de log expostos", 'site:{site} ext:log'),
    ("Arquivos de backup e antigos", 'site:{site} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup'),
    ("Páginas de login", 'site:{site} inurl:login | inurl:signin | intitle:Login | intitle:"sign in" | inurl:auth'),
    ("Erros SQL", 'site:{site} intext:"sql syntax near" | intext:"syntax error has occurred" | intext:"incorrect syntax near" | intext:"unexpected end of SQL command" | intext:"Warning: mysql_connect()" | intext:"Warning: mysql_query()" | intext:"Warning: pg_connect()"'),
    ("Erros/advertências PHP", 'site:{site} "PHP Parse error" | "PHP Warning" | "PHP Error"'),
    ("phpinfo()", 'site:{site} ext:php intitle:phpinfo "published by the PHP Group"'),
    ("Pesquisar em pastebin.com / sites de postagem", 'site:pastebin.com | site:paste2.org | site:pastehtml.com | site:slexy.org | site:snipplr.com | site:snipt.net | site:textsnip.com | site:bitpaste.app | site:justpaste.it | site:heypasteit.com | site:hastebin.com | site:dpaste.org | site:dpaste.com | site:codepad.org | site:jsitor.com | site:codepen.io | site:jsfiddle.net | site:dotnetfiddle.net | site:phpfiddle.org | site:ide.geeksforgeeks.org | site:repl.it | site:ideone.com | site:paste.debian.net | site:paste.org | site:paste.org.ru | site:codebeautify.org | site:codeshare.io | site:trello.com {site}'),
    ("Pesquisar em github.com e gitlab.com", 'site:github.com | site:gitlab.com {site}'),
    ("Pesquisar no stackoverflow.com", 'site:stackoverflow.com {site}'),
    ("Páginas de cadastro", 'site:{site} inurl:signup | inurl:register | intitle:Signup'),
    ("Encontrar Subdomínios", 'site:*.{site}'),
    ("Encontrar Sub-Subdomínios", 'site:*.*.{site}'),
    ("Pesquisar no Wayback Machine", 'https://web.archive.org/web/*/{site}/*'),
    ("Mostrar apenas IPs (abre várias abas)", '({site}) (site:*.*.29.* | site:*.*.28.* | site:*.*.27.* | site:*.*.26.* | site:*.*.25.* | site:*.*.24.* | site:*.*.23.* | site:*.*.22.* | site:*.*.21.* | site:*.*.20.* | site:*.*.19.* | site:*.*.18.* | site:*.*.17.* | site:*.*.16.* | site:*.*.15.* | site:*.*.14.* | site:*.*.13.* | site:*.*.12.* | site:*.*.11.* | site:*.*.10.* | site:*.*.9.* | site:*.*.8.* | site:*.*.7.* | site:*.*.6.* | site:*.*.5.* | site:*.*.4.* | site:*.*.3.* | site:*.*.2.* | site:*.*.1.* | site:*.*.0.*)'),
    ("Google Docs - documentos vazados", 'site:docs.{site}/document/d'),
    ("Google Docs - apresentações vazadas", 'site:docs.{site}/presentation/d'),
    ("Google Docs - desenhos vazados", 'site:docs.{site}/drawings/d'),
    ("Google Docs - qualquer arquivo (img/vídeo/zip/pdf)", 'site:docs.{site}/file/d'),
    ("Google Drive - pastas expostas", 'site:docs.{site}/folder/d'),
    ("Google Docs - itens secretos", 'site:docs.{site}/open intext:secreto'),
    ("Achar inurl e index.php", '"{site}" + inurl=index.php?id=1'),
    ("Arquivo PDF", 'site:{site} ext:pdf'),
    ("Arquivo XML", 'site:{site} ext:xml'),
    ("Arquivo DOCX", 'site:{site} ext:docx'),
    ("Achar intext", 'intext:{site}'),
    ("TXT senha url", 'filetype:txt intext:senha url site:{site}'),
    ("Servidores Scribd", 'servidores site:scribd.com AND:{site}'),
    ("SQL", '{site} filetype:sql'),
    ("ENV", 'filetype:env {site}'),
    ("Achar inurl", 'inurl:{site}'),
    ("PDF/XLSX/DOCX/TXT", '\'{site}\' filetype:pdf OR filetype:xlsx OR filetype:docx OR filetype:txt'),
    ("TXT (2)", 'site:{site} filetype:txt'),
    ("WEBCAM 7", '{site} intitle:"WEBCAM 7" -inurl:/admin.html'),
    ("robots.txt", '{site} robots.txt'),
    ("index of - senha", 'intitle:"index of" intext:{site}'),
    ("Nome de pessoa", 'intext:"{site}"'),
    ("Nome do IP", 'IP:{site}'),
    ("PDF confidencial", 'filetype:pdf intitle:confidencial site:{site}'),
    ("Confidencial", 'intitle:confidencial filetype:pdf intext:"{site}"'),
    ("Credit card (pastebin)", 'site:pastebin.com {site} credit card'),
    ("Google Drive", 'site:drive.google.com {site}'),
    ("Login -Painel", 'site:{site} intitle:Login -Painel'),
    ("Achar link", 'link:{site}'),
    ("Extrair dados", '"{site}"'),
    (".git - index of", '{site} intitle:index of .git'),
    ("site .git", 'site:{site} intitle:index of .git'),
    ("git config", 'site:{site} intitle:"index of" "/.git/config"'),
    ("XML (2)", 'site:{site} filetype:xml'),
    ("LOG (2)", 'site:{site} filetype:log'),
    ("index of /logs", 'site:{site} index of /logs'),
    ("contact-form-7 (1)", 'site:{site}/wp-content/plugins/contact-form-7'),
    ("contact-form-7 (2)", 'site:{site} /wp-content/plugins/contact-form-7'),
    ("Financial report PDF", 'financial report site:{site} filetype:pdf'),
    ("intitle nome", 'intitle:"{site}"'),
    ("PDF com nome", 'filetype:pdf "{site}"'),
    ("inurl email", 'inurl: {site}'),
    ("Achar email", '"{site}"'),
    ("Jusbrasil", 'site:jusbrasil.com.br "{site}"'),
    ("Instagram (intext)", 'site:instagram.com intext:"{site}"'),
    ("Instagram", 'site:instagram.com intext:{site}'),
    ("intext nome", 'intext:"{site}"'),
    ("Google Drive (2)", 'site:drive.google.com "{site}"'),
    ("PDF com nome (2)", 'filetype:pdf "{site}"'),
]

# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------
dorks_geradas = []  # lista de (rótulo, dork) geradas para o site atual

def encontrar_chrome():
    candidatos = []
    if sys.platform.startswith("win"):
        candidatos = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        candidatos = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        candidatos = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho
    return None

def url_para_dork(dork):
    """Se for uma URL direta (http/https), abre ela. Senão, monta busca no motor."""
    dork = dork.strip()
    if dork.lower().startswith(("http://", "https://")):
        return dork
    q = quote(dork)
    template = MOTORES.get(combo_motor.get(), MOTORES["Google"])
    return template.format(q=q)

def abrir_no_chrome(dork):
    url = url_para_dork(dork)
    chrome = encontrar_chrome()
    if chrome:
        subprocess.Popen([chrome, url])
    else:
        import webbrowser
        webbrowser.open(url)

# ---------------------------------------------------------------------------
# LÓGICA DA INTERFACE
# ---------------------------------------------------------------------------
def normalizar_site(texto):
    site = texto.strip()
    for prefixo in ("https://", "http://", "www."):
        if site.lower().startswith(prefixo):
            site = site[len(prefixo):]
    return site.rstrip("/").strip()

def gerar(event=None):
    site = normalizar_site(entry_site.get())
    if not site:
        messagebox.showwarning("Atenção", "Digite o nome do site primeiro.\nEx.: exemplo.com.br")
        return
    dorks_geradas.clear()
    lista.delete(0, tk.END)
    for rotulo, template in DORKS:
        dork = template.format(site=site)
        dorks_geradas.append((rotulo, dork))
        lista.insert(tk.END, f"{rotulo}: {dork}")
    lista.selection_set(0)
    lista.activate(0)
    sincronizar_campo()
    status_var.set(f"✔ {len(dorks_geradas)} dorks geradas para {site} · motor: {combo_motor.get()}")

def sincronizar_campo(event=None):
    """Clique numa dork → ela aparece no campo width=30 (só a dork, sem rótulo)."""
    selecionadas = lista.curselection()
    if selecionadas:
        _, dork = dorks_geradas[selecionadas[0]]
        entry_dork.delete(0, tk.END)
        entry_dork.insert(0, dork)

def abrir_do_campo(event=None):
    """Abre o texto do campo (editável) com confirmação Sim/Não."""
    dork = entry_dork.get().strip()
    if not dork:
        messagebox.showinfo("Info", "O campo de dork está vazio.\nSelecione uma dork na lista primeiro.")
        return

    resposta = messagebox.askyesno(
        "Abrir no Google Chrome?",
        f"Deseja abrir esta busca no Google Chrome?\n\n"
        f"🔍 {dork}\n\n"
        f"Motor: {combo_motor.get()}",
        icon=messagebox.QUESTION,
    )

    if resposta:
        abrir_no_chrome(dork)
        status_var.set(f"✔ Aberta: {dork}")
        pular_proxima()
    else:
        status_var.set(f"✖ Não aberta: {dork}")

def pular_proxima():
    """Após abrir, seleciona a próxima dork da lista."""
    selecionadas = lista.curselection()
    if selecionadas and selecionadas[0] + 1 < lista.size():
        prox = selecionadas[0] + 1
        lista.selection_clear(0, tk.END)
        lista.selection_set(prox)
        lista.activate(prox)
        lista.see(prox)
        sincronizar_campo()

def copiar_campo():
    dork = entry_dork.get().strip()
    if not dork:
        messagebox.showinfo("Info", "O campo está vazio.")
        return
    root.clipboard_clear()
    root.clipboard_append(dork)
    status_var.set(f"✔ Copiada: {dork}")

def copiar_todas():
    if not dorks_geradas:
        return
    texto = "\n".join(f"{rotulo}: {dork}" for rotulo, dork in dorks_geradas)
    root.clipboard_clear()
    root.clipboard_append(texto)
    status_var.set(f"✔ {len(dorks_geradas)} dorks copiadas para o relatório.")

def limpar():
    entry_site.delete(0, tk.END)
    entry_dork.delete(0, tk.END)
    lista.delete(0, tk.END)
    dorks_geradas.clear()
    status_var.set("Pronto. Digite o domínio e clique em Gerar Dorks.")

# ---------------------------------------------------------------------------
# INTERFACE GRÁFICA
# ---------------------------------------------------------------------------
root = tk.Tk()
root.title("Dork Google Hacking")
root.state("zoomed")
root.geometry("980x680")
root.minsize(760, 500)

# --- Linha superior: site + motor ---
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill=tk.X)

ttk.Label(frame_top, text="Site:").pack(side=tk.LEFT)
entry_site = ttk.Entry(frame_top, width=30, font=("Consolas", 11))
entry_site.pack(side=tk.LEFT, padx=(6, 10))
entry_site.bind("<Return>", gerar)

ttk.Label(frame_top, text="Motor de Busca:").pack(side=tk.LEFT)
combo_motor = ttk.Combobox(frame_top, values=list(MOTORES.keys()), state="readonly", width=14)
combo_motor.current(0)
combo_motor.pack(side=tk.LEFT, padx=(6, 10))

ttk.Button(frame_top, text="⚡ Gerar Dorks", command=gerar).pack(side=tk.LEFT)

ttk.Label(frame_top, text="ex.: exemplo.com.br", foreground="gray").pack(side=tk.LEFT, padx=10)

# --- Lista de dorks (rótulo + dork) ---
frame_lista = ttk.Frame(root, padding=(10, 0, 10, 0))
frame_lista.pack(fill=tk.BOTH, expand=True)

scroll = ttk.Scrollbar(frame_lista)
scroll.pack(side=tk.RIGHT, fill=tk.Y)

lista = tk.Listbox(
    frame_lista,
    yscrollcommand=scroll.set,
    selectmode=tk.SINGLE,
    font=("Consolas", 9),
    activestyle="dotbox",
)
lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll.config(command=lista.yview)

lista.bind("<<ListboxSelect>>", sincronizar_campo)
lista.bind("<Double-Button-1>", abrir_do_campo)

# --- Campo da dork selecionada (width=30, editável) ---
frame_campo = ttk.Frame(root, padding=(10, 8, 10, 0))
frame_campo.pack(fill=tk.X)

ttk.Label(frame_campo, text="Dork selecionada:").pack(side=tk.LEFT)

entry_dork = ttk.Entry(frame_campo, width=30, font=("Consolas", 11))
entry_dork.pack(side=tk.LEFT, padx=(8, 8), fill=tk.X, expand=True)
entry_dork.bind("<Return>", abrir_do_campo)

# --- Botões ---
frame_botoes = ttk.Frame(root, padding=10)
frame_botoes.pack(fill=tk.X)

ttk.Button(frame_botoes, text="🌐 Abrir no Chrome", command=abrir_do_campo).pack(side=tk.LEFT, padx=(0, 6))
ttk.Button(frame_botoes, text="📋 Copiar", command=copiar_campo).pack(side=tk.LEFT, padx=6)
ttk.Button(frame_botoes, text="📄 Copiar Todas", command=copiar_todas).pack(side=tk.LEFT, padx=6)
ttk.Button(frame_botoes, text="Limpar", command=limpar).pack(side=tk.LEFT, padx=6)
ttk.Button(frame_botoes, text="Sair", command=root.destroy).pack(side=tk.RIGHT)

# --- Barra de status ---
status_var = tk.StringVar(value="Pronto. Digite o domínio ou outra coisa que deseja procurar e clique em Gerar Dorks.")
ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W, padding=6).pack(fill=tk.X, side=tk.BOTTOM)

root.mainloop()
