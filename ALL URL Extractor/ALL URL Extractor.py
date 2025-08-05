import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from bs4 import BeautifulSoup
import re
import subprocess
import sys
import os
import shutil
from urllib.parse import urljoin, urlparse
import requests

urls_extraidas = []
dominio_detectado = None

def detectar_dominio_base(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        for attr in ['href', 'src']:
            if tag.has_attr(attr):
                valor = tag[attr]
                if valor.startswith("http"):
                    parsed = urlparse(valor)
                    return f"{parsed.scheme}://{parsed.netloc}"
    return None

def extrair_todas_urls(html_content):
    global dominio_detectado
    dominio_detectado = detectar_dominio_base(html_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = set()

    atributos = ['href', 'src', 'data-src', 'srcset']
    todas_as_tags = soup.find_all(True)
    total = len(todas_as_tags)

    for i, tag in enumerate(todas_as_tags):
        for attr in atributos:
            if tag.has_attr(attr):
                valor = tag[attr]
                if isinstance(valor, str):
                    partes = [v.strip().split(" ")[0] for v in valor.split(",")]
                    for parte in partes:
                        if parte.startswith("http"):
                            urls.add(parte)
                        elif parte.startswith("/") and dominio_detectado:
                            url_completa = urljoin(dominio_detectado, parte)
                            urls.add(url_completa)

        progresso["value"] = int((i + 1) / total * 100)
        janela.update_idletasks()

    padrao_url = re.compile(r'http[s]?://[^\s"\'<>]+')
    encontrados = padrao_url.findall(html_content)
    urls.update(encontrados)

    return sorted(urls)

def abrir_arquivo():
    global urls_extraidas
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo index.html",
        filetypes=[("Arquivos HTML", "*.html;*.htm")]
    )

    if caminho_arquivo:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo_html = f.read()

            progresso["value"] = 0
            resultado_texto.delete(1.0, tk.END)

            urls_extraidas = extrair_todas_urls(conteudo_html)

            mostrar_resultados()

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao ler o arquivo:\n{e}")

def extrair_de_url():
    global urls_extraidas
    url = entrada_url.get().strip()

    if not url.startswith("http"):
        messagebox.showwarning("URL inválida", "Por favor, digite uma URL válida começando com http ou https.")
        return

    try:
        progresso["value"] = 0
        resultado_texto.delete(1.0, tk.END)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        resposta = requests.get(url, headers=headers, timeout=10)
        resposta.raise_for_status()
        html = resposta.text

        urls_extraidas = extrair_todas_urls(html)
        mostrar_resultados()

    except Exception as e:
        messagebox.showerror("Erro ao acessar URL", f"Ocorreu um erro:\n{e}")

def mostrar_resultados():
    resultado_texto.delete(1.0, tk.END)
    if urls_extraidas:
        resultado_texto.insert(tk.END, f"Total de URL Encontradas: {len(urls_extraidas)}\n\n")
        if dominio_detectado:
            resultado_texto.insert(tk.END, f"Domínio Detectado: {dominio_detectado}\n\n\n")
        for url in urls_extraidas:
            resultado_texto.insert(tk.END, f"{url}\n\n")
    else:
        resultado_texto.insert(tk.END, "Nenhuma URL encontrada.")
    progresso["value"] = 100

def salvar_resultado():
    if not urls_extraidas:
        messagebox.showwarning("Aviso", "Nenhuma URL para salvar.")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar URLs como"
    )

    if caminho_salvar:
        try:
            with open(caminho_salvar, 'w', encoding='utf-8') as f:
                f.write(f"Total de URL Encontradas: {len(urls_extraidas)}\n\n\n")
                for url in urls_extraidas:
                    f.write(url + "\n\n")

            # Mostra no campo de texto também (opcional, pode remover se quiser)
            resultado_texto.insert(tk.END, f"\n[✔] {len(urls_extraidas)} URL salvas em: {caminho_salvar}\n")

            messagebox.showinfo("Salvo", "URL salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"{e}")

def abrir_url_no_chrome_anonima(url):
    caminhos_possiveis = []

    if sys.platform == "win32":
        caminhos_possiveis = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        caminhos_possiveis = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        caminhos_possiveis = ["google-chrome", "chrome", "chromium-browser", "chromium"]

    caminho_chrome = None
    for caminho in caminhos_possiveis:
        if os.path.isfile(caminho) or shutil.which(caminho):
            caminho_chrome = caminho
            break

    if caminho_chrome is None:
        messagebox.showerror("Erro", "Google Chrome não encontrado no sistema.")
        return

    try:
        subprocess.Popen([caminho_chrome, "--incognito", url])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o Chrome:\n{e}")

def abrir_url_ao_clicar(event):
    try:
        index = resultado_texto.index(f"@{event.x},{event.y}")
        linha = resultado_texto.get(index + " linestart", index + " lineend").strip()

        if linha.startswith("http"):
            abrir_url_no_chrome_anonima(linha)
    except Exception as e:
        print(f"Erro ao abrir URL: {e}")

# GUI
janela = tk.Tk()
janela.title("Extrator de TODAS as URL do index.html ou URL do website")
janela.geometry("1280x1024")

label = tk.Label(janela, text="Digite a URL do website", font=("Arial", 12, "bold"))
label.pack(pady=5)

frame_top = tk.Frame(janela)
frame_top.pack(pady=10)

btn_abrir = tk.Button(frame_top, text="Selecionar index.html", bg="#05d3f7", command=abrir_arquivo)
btn_abrir.pack(side=tk.LEFT, padx=5)

btn_salvar = tk.Button(frame_top, text="Salvar URL", bg="#f7b705", command=salvar_resultado)
btn_salvar.pack(side=tk.LEFT, padx=5)

entrada_url = tk.Entry(frame_top, width=80)
entrada_url.pack(side=tk.LEFT, padx=5)

btn_extrair_url = tk.Button(frame_top, text="Extrair de URL", bg="#05f746", command=extrair_de_url)
btn_extrair_url.pack(side=tk.LEFT, padx=5)

progresso = ttk.Progressbar(janela, orient='horizontal', length=790, mode='determinate')
progresso.pack(pady=10)

resultado_texto = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=140, height=47)
resultado_texto.pack(padx=10, pady=10)

resultado_texto.bind("<Double-Button-1>", abrir_url_ao_clicar)

janela.mainloop() 
