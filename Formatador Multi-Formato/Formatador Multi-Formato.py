import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import threading
from bs4 import BeautifulSoup
import json
import jsbeautifier
import os
import sys
import subprocess
import shutil
import re

# ---------- Configurações gerais ----------
TIPOS_FORMATACAO = ["HTML", "JavaScript", "CSS", "JSON"]
ultimo_arquivo_salvo = None
ultimo_arquivo_lock = threading.Lock()
conteudo_atual = ""  # Conteúdo bruto
tipo_selecionado = "HTML"
ultima_url = None  # Guardar a última URL pesquisada

# ---------- Cabeçalhos ----------
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# ---------- Funções de formatação ----------
def formatar_html(raw):
    soup = BeautifulSoup(raw, "html.parser")
    if soup.html:
        if not soup.head:
            soup.html.insert(0, soup.new_tag("head"))
        head = soup.head
        if not head.find("meta", attrs={"charset": True}):
            meta = soup.new_tag("meta", charset="utf-8")
            head.insert(0, meta)
        if not head.find("meta", attrs={"name": "viewport"}):
            meta_vw = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1.0"})
            head.append(meta_vw)
        if not head.title:
            titulo = "Document"
            t = soup.find("title")
            if t and t.string:
                titulo = t.string.strip()
            else:
                h1 = soup.find("h1")
                if h1 and h1.string:
                    titulo = h1.string.strip()
            new_title = soup.new_tag("title")
            new_title.string = titulo
            head.append(new_title)
        return BeautifulSoup(str(soup), "html.parser").prettify()
    else:
        template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Document</title>
</head>
<body>
<!-- CONTENT_PLACEHOLDER -->
</body>
</html>"""
        t_soup = BeautifulSoup(template, "html.parser")
        body = t_soup.body
        inner = BeautifulSoup(raw, "html.parser")
        if inner.body:
            for item in inner.body.contents:
                body.append(item)
        elif inner.html:
            for item in inner.html.contents:
                body.append(item)
        else:
            for item in inner.contents:
                body.append(item)
        return BeautifulSoup(str(t_soup), "html.parser").prettify()

def formatar_json(raw):
    try:
        data = json.loads(raw)
        return json.dumps(data, indent=4, ensure_ascii=False)
    except Exception:
        return raw

def formatar_js_css(raw):
    opts = jsbeautifier.default_options()
    opts.indent_size = 4
    return jsbeautifier.beautify(raw, opts)

def formatar_conteudo(raw, tipo):
    if tipo == "HTML":
        return formatar_html(raw)
    elif tipo == "JSON":
        return formatar_json(raw)
    elif tipo in ["JavaScript", "CSS"]:
        return formatar_js_css(raw)
    else:
        return raw

# ---------- Atualizar ScrolledText ----------
def atualizar_scrolledtext():
    global conteudo_atual
    if not conteudo_atual:
        return
    texto_formatado = formatar_conteudo(conteudo_atual, tipo_selecionado)
    linhas = texto_formatado.splitlines()
    total = len(linhas)
    text_area.delete(1.0, tk.END)
    for i, linha in enumerate(linhas, 1):
        text_area.insert(tk.END, linha + "\n")
        progress['value'] = (i / total) * 100
        janela.update_idletasks()
    progress['value'] = 0

# ---------- ProgressBar ----------
def iniciar_progresso():
    progress['value'] = 0
    janela.update_idletasks()

def finalizar_progresso():
    progress['value'] = 0
    janela.update_idletasks()

# ---------- Baixar conteúdo ----------
def baixar_conteudo(modo="mostrar"):
    global conteudo_atual, ultima_url
    url = entrada_url.get().strip()
    if not url:
        messagebox.showerror("Erro", "Digite uma URL!")
        return
    try:
        iniciar_progresso()
        resposta = requests.get(url, headers=HEADERS, timeout=12)
        resposta.raise_for_status()
        encoding = resposta.apparent_encoding or "utf-8"
        conteudo_atual = resposta.content.decode(encoding, errors='replace')
        ultima_url = url  # guarda a última URL acessada
        atualizar_scrolledtext()
        btn_abrir_anonimo.config(state=tk.NORMAL)
        if modo == "salvar":
            salvar_html()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro", f"Não foi possível baixar a página:\n{e}")
    finally:
        finalizar_progresso()

def thread_mostrar():
    threading.Thread(target=baixar_conteudo, args=("mostrar",), daemon=True).start()

def thread_salvar():
    threading.Thread(target=baixar_conteudo, args=("salvar",), daemon=True).start()

# ---------- Salvar resultados da pesquisa ----------
def salvar_resultados_pesquisa():
    conteudo = text_area.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showerror("Erro", "Não há resultados para salvar!")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        title="Salvar resultado da pesquisa como"
    )

    if caminho:
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Resultado salvo em\n\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar arquivo:\n{e}")

# ---------- Salvar conteúdo ----------
def salvar_html():
    global conteudo_atual
    if not conteudo_atual:
        messagebox.showerror("Erro", "Não há conteúdo para salvar!")
        return
    ext = ".html" if tipo_selecionado == "HTML" else ".txt"
    caminho = filedialog.asksaveasfilename(defaultextension=ext,
                                           filetypes=[("Todos os arquivos", "*.*")],
                                           title="Salvar como")
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(formatar_conteudo(conteudo_atual, tipo_selecionado))
        messagebox.showinfo("Sucesso", f"{tipo_selecionado} salvo em\n\n{caminho}")
        global ultimo_arquivo_salvo
        with ultimo_arquivo_lock:
            ultimo_arquivo_salvo = caminho
        btn_abrir_anonimo.config(state=tk.NORMAL)

# ---------- Abrir arquivo existente ----------
def abrir_html_existente():
    global conteudo_atual
    caminho = filedialog.askopenfilename(filetypes=[("Todos os arquivos", "*.*")],
                                         title="Selecione um arquivo")
    if caminho:
        iniciar_progresso()
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo_atual = f.read()
        atualizar_scrolledtext()
        global ultimo_arquivo_salvo
        with ultimo_arquivo_lock:
            ultimo_arquivo_salvo = caminho
        btn_abrir_anonimo.config(state=tk.NORMAL)
        finalizar_progresso()

# ---------- Abrir em modo anônimo ----------
def abrir_em_anonimo(alvo):
    if not alvo:
        messagebox.showerror("Erro", "Nada para abrir em modo anônimo.")
        return
    if os.path.exists(alvo):
        file_url = os.path.abspath(alvo)
        alvo = f"file:///{file_url.replace(os.sep, '/')}"
    try:
        if sys.platform.startswith("win"):
            caminhos_possiveis = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Microsoft Edge\Application\msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
            ]
            for exe in caminhos_possiveis:
                if os.path.exists(exe):
                    nome = os.path.basename(exe).lower()
                    if "chrome" in nome:
                        subprocess.Popen([exe, "--incognito", alvo])
                    elif "msedge" in nome:
                        subprocess.Popen([exe, "--inprivate", alvo])
                    elif "firefox" in nome:
                        subprocess.Popen([exe, "-private-window", alvo])
                    return
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", alvo])
        else:
            subprocess.Popen(["xdg-open", alvo])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir em modo anônimo:\n{e}")

def botao_abrir_anonimo_click():
    def runner():
        with ultimo_arquivo_lock:
            caminho = ultimo_arquivo_salvo
        alvo = caminho or ultima_url
        abrir_em_anonimo(alvo)
    threading.Thread(target=runner, daemon=True).start()

# ---------- Pesquisar ----------
def pesquisar_texto():
    termo = entrada_pesquisa.get().strip()
    if not termo:
        return

    text_area.delete(1.0, tk.END)

    # Regex para capturar URLs (http, https, .onion, etc.)
    url_regex = re.compile(r"https?://[a-zA-Z0-9\-\._/~%]+[^\s\"'<>]*", re.IGNORECASE)

    resultados = set()
    conteudo = conteudo_atual

    if termo.lower().startswith("http") or termo.lower().endswith(".onion"):
        urls = url_regex.findall(conteudo)
        for u in urls:
            if termo.lower() in u.lower():
                resultados.add(u)

        if resultados:
            text_area.insert(tk.END, f"URL Encontradas para: {termo}\n\n")
            for url in sorted(resultados):
                text_area.insert(tk.END, url + "\n\n", "url")
            text_area.tag_config("url", foreground="red", underline=1)
            text_area.insert(tk.END, f"\nTotal de URL Encontradas: {len(resultados)}")
        else:
            text_area.insert(tk.END, f"Nenhuma URL encontrada para: {termo}")
        return

    termo_lower = termo.lower()
    for linha in conteudo.splitlines():
        if termo_lower in linha.lower():
            idx = linha.lower().find(termo_lower)
            start = max(0, idx - 40)
            end = min(len(linha), idx + len(termo) + 40)
            trecho = linha[start:end].strip()
            resultados.add(trecho)

    if resultados:
        text_area.insert(tk.END, f"Resultados da pesquisa: {termo}\n\n")
        text_area.tag_config("highlight", foreground="red")
        for r in sorted(resultados):
            insert_before = text_area.index(tk.INSERT)
            text_area.insert(tk.END, r + "\n")
            for m in re.finditer(re.escape(termo), r, re.IGNORECASE):
                line_no = insert_before.split('.')[0]
                start_idx = f"{line_no}.{m.start()}"
                end_idx = f"{line_no}.{m.end()}"
                try:
                    text_area.tag_add("highlight", start_idx, end_idx)
                except:
                    pass
        text_area.insert(tk.END, f"\nTotal de resultados Encontrados: {len(resultados)}")
    else:
        text_area.insert(tk.END, f"Nenhum resultado encontrado para: {termo}")

# ---------- Interface gráfica ----------
janela = tk.Tk()
janela.wm_state('zoomed')
janela.title("Formatador Multi-Formato")

frame = tk.Frame(janela)
frame.pack(padx=8, pady=8, anchor="w")

# URL e tipo
tk.Label(frame, text="Digite a URL do Website").grid(row=0, column=0, sticky="w", pady=4)
entrada_url = tk.Entry(frame, width=50)
entrada_url.grid(row=0, column=1, columnspan=2, pady=4, padx=6)

def atualizar_tipo(valor):
    global tipo_selecionado
    tipo_selecionado = valor
    threading.Thread(target=atualizar_scrolledtext, daemon=True).start()

tipo_var = tk.StringVar()
tipo_var.set(TIPOS_FORMATACAO[0])
tipo_menu = tk.OptionMenu(frame, tipo_var, *TIPOS_FORMATACAO, command=atualizar_tipo)
tipo_menu.grid(row=0, column=3, padx=6)

# Botões
btn_mostrar = tk.Button(frame, text="Pesquisar Website Mostrar (formatado)", bg="#03fc24", fg="black", command=thread_mostrar)
btn_mostrar.grid(row=1, column=0, pady=6, padx=4)
btn_salvar = tk.Button(frame, text="Salvar (formatado)", bg="#fcd103", fg="black", command=salvar_html)
btn_salvar.grid(row=1, column=1, pady=6, padx=4)
btn_abrir_anonimo = tk.Button(frame, text="Abrir em modo anônimo", bg="#00c8ff", fg="black", command=botao_abrir_anonimo_click, state=tk.DISABLED)
btn_abrir_anonimo.grid(row=1, column=2, pady=6, padx=4)
btn_abrir_existente = tk.Button(frame, text="Abrir arquivo existente", bg="#8a05ff", fg="black", command=abrir_html_existente)
btn_abrir_existente.grid(row=1, column=3, pady=6, padx=4)

# Pesquisa
frame_pesquisa = tk.Frame(frame)
frame_pesquisa.grid(row=2, column=0, columnspan=4, pady=4, sticky="w")
tk.Label(frame_pesquisa, text="Pesquisar Resultado").grid(row=0, column=0)
entrada_pesquisa = tk.Entry(frame_pesquisa, width=50)
entrada_pesquisa.grid(row=0, column=1, padx=4)
btn_pesquisar = tk.Button(frame_pesquisa, text="Pesquisar Resultado", bg="#03f0fc", fg="black", command=pesquisar_texto)
btn_pesquisar.grid(row=0, column=2, padx=4)

btn_salvar_pesquisa = tk.Button(frame_pesquisa, text="Salvar Resultado da pesquisa", bg="#f7ff05", fg="black", command=salvar_resultados_pesquisa)
btn_salvar_pesquisa.grid(row=0, column=3, padx=4)

# Progressbar
progress = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate")
progress.grid(row=3, column=0, columnspan=4, pady=4, sticky="we")

# ScrolledText
text_area = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=150, height=46)
text_area.pack(padx=8, pady=8)

janela.mainloop()
