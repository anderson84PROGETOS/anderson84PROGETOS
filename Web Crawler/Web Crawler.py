#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
import time
import os
import threading
import re
import socket
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# ---------------- Cabeçalhos padrão ----------------
HEADERS_PADRAO = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

EXTENSOES_IGNORAR = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".mp4", ".mp3", ".avi", ".mov", ".pdf", ".zip", ".rar",
    ".exe", ".dll", ".iso", ".woff", ".woff2",
)

# ---------------- Variáveis globais ----------------
links_encontrados = set()
dominios = set()
subdominios = set()
emails_encontrados = set()
telefones_encontrados = set()

# ---------------- Funções do crawler ----------------
def link_valido(href):
    if not href:
        return False
    href = href.strip()
    if href.startswith("#") or href.lower().startswith(("javascript:",)):
        return False
    for ext in EXTENSOES_IGNORAR:
        if href.lower().split("?")[0].endswith(ext):
            return False
    return True

def limpar_href(href):
    if not href:
        return None
    h = href.strip().split()[0]
    if h.startswith("https:/") and not h.startswith("https://"):
        h = h.replace("https:/", "https://", 1)
    if h.startswith("http:/") and not h.startswith("http://"):
        h = h.replace("http:/", "http://", 1)
    return h

def normalizar_url(base, href):
    try:
        href_limpo = limpar_href(href)
        if not href_limpo:
            return None
        full = urljoin(base, href_limpo).replace(" ", "")
        return full
    except Exception:
        return None

def extrair_dominio_subdominio(url):
    ext = tldextract.extract(url)
    if not ext.domain:
        return None, None
    dominio = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
    subdominio = ext.subdomain if ext.subdomain else None
    return dominio, subdominio

def buscar(url, headers, timeout=10):
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 200 and "text/html" in ct:
            return r.text
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# ---------------- Funções para extrair emails e telefones ----------------
def extrair_emails(texto, soup=None):
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', texto))
    if soup:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                email = href[7:].split("?")[0].strip()
                if email:
                    emails.add(email)
    return emails

def extrair_telefones(texto):
    padrao_telefone = r'(\+?\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{3,5}[\s-]?\d{4})'
    return set(re.findall(padrao_telefone, texto))

# ---------------- Função WHOIS Brasil ----------------
def requisicao_whois(dominio):
    servidor = 'whois.registro.br'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    resultado = ''
    try:
        s.connect((servidor, 43))
        s.send((dominio + "\r\n").encode())
        while True:
            dados = s.recv(65535)
            if not dados:
                break
            resultado += dados.decode(errors='ignore')
    except Exception as e:
        resultado = f"⚠️ Erro: {e}"
    finally:
        s.close()
    # Remove linhas de comentário que começam com %
    resultado = "\n".join(l for l in resultado.splitlines() if not l.strip().startswith("%"))
    # Extrai emails do WHOIS
    emails_whois = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resultado))
    return emails_whois

# ---------------- Função principal do rastreamento ----------------
def rastrear_gui(start_url, headers, max_profundidade, mesmo_dominio, atraso, max_paginas, text_widget, progress):
    from collections import deque
    global links_encontrados, dominios, subdominios, emails_encontrados, telefones_encontrados

    links_encontrados.clear()
    dominios.clear()
    subdominios.clear()
    emails_encontrados.clear()
    telefones_encontrados.clear()

    parsed_start = urlparse(start_url)
    netloc_base = parsed_start.netloc.lower()
    fila = deque()
    fila.append((start_url, 0))
    visitados = set()
    paginas_rastreadas = 0
    contador_descobertos = 0

    while fila:
        url, profundidade = fila.popleft()
        if url in visitados or paginas_rastreadas >= max_paginas:
            continue
        visitados.add(url)
        paginas_rastreadas += 1

        text_widget.insert(tk.END, f"\n[fetch {paginas_rastreadas}] profundidade={profundidade} -> {url}\n\n")
        text_widget.see(tk.END)

        html = buscar(url, headers)
        if not html:
            time.sleep(atraso)
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Extrai emails e telefones do site
        emails_encontrados.update(extrair_emails(html, soup))
        telefones_encontrados.update(extrair_telefones(html))

        # Extrai emails do WHOIS (apenas .br)
        dominio, sub = extrair_dominio_subdominio(url)
        if dominio and dominio.endswith(".br"):
            try:
                emails_encontrados.update(requisicao_whois(dominio))
            except:
                pass

        if dominio:
            dominios.add(dominio)
        if sub:
            subdominios.add(f"{sub}.{dominio}" if dominio else sub)

        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if not link_valido(href):
                continue
            full = normalizar_url(url, href)
            if not full:
                continue
            full = full.split("#")[0].rstrip("/")
            if full in links_encontrados:
                continue
            d, s = extrair_dominio_subdominio(full)
            if d:
                dominios.add(d)
            if s:
                subdominios.add(f"{s}.{d}" if d else s)
            links_encontrados.add(full)
            contador_descobertos += 1
            text_widget.insert(tk.END, f"[{contador_descobertos}] profundidade={profundidade+1} -> {full}\n")
            text_widget.see(tk.END)

            if profundidade + 1 <= max_profundidade:
                if mesmo_dominio:
                    netloc = urlparse(full).netloc.lower()
                    if netloc == netloc_base and full not in visitados:
                        fila.append((full, profundidade+1))
                else:
                    if full not in visitados:
                        fila.append((full, profundidade+1))

        progress['value'] = min((paginas_rastreadas / max_paginas) * 100, 100)
        progress.update()
        text_widget.update()
        time.sleep(atraso)

    progress['value'] = 100
    progress.update()
    messagebox.showinfo("Concluído", f"Rastreamento finalizado!\nLinks: {len(links_encontrados)}\nDomínios: {len(dominios)}\nSubdomínios: {len(subdominios)}\nEmails: {len(emails_encontrados)}\nTelefones: {len(telefones_encontrados)}")
    progress['value'] = 0

# ---------------- Função salvar resultados ----------------
def salvar_resultados():
    global links_encontrados, dominios, subdominios, emails_encontrados, telefones_encontrados
    if not links_encontrados:
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
        return
    pasta = filedialog.askdirectory(title="Escolha a pasta para salvar os resultados")
    if not pasta:
        return
    try:
        with open(os.path.join(pasta, "links.txt"), "w", encoding="utf-8") as f:
            for item in sorted(links_encontrados):
                f.write(item + "\n")
        with open(os.path.join(pasta, "dominios.txt"), "w", encoding="utf-8") as f:
            for item in sorted(dominios):
                f.write(item + "\n")
        with open(os.path.join(pasta, "subdominios.txt"), "w", encoding="utf-8") as f:
            for item in sorted(subdominios):
                f.write(item + "\n")
        with open(os.path.join(pasta, "email.txt"), "w", encoding="utf-8") as f:
            for item in sorted(emails_encontrados):
                f.write(item + "\n")
        with open(os.path.join(pasta, "telefone.txt"), "w", encoding="utf-8") as f:
            for item in sorted(telefones_encontrados):
                f.write(item + "\n")
        messagebox.showinfo("Sucesso", f"Resultados salvos em\n\n{pasta}")
    except Exception as e:
        messagebox.showerror("Erro", f"\nFalha ao salvar arquivos: {e}")

# ---------------- GUI ----------------
def iniciar_rastreamento_thread():
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Informe a URL inicial.")
        return
    if not urlparse(url).scheme:
        url = "http://" + url
    try:
        profundidade = int(entry_profundidade.get())
        mesmo_dominio = var_mesmo_dominio.get()
        atraso = float(entry_atraso.get())
        max_paginas = int(entry_max_paginas.get())
    except Exception:
        messagebox.showerror("Erro", "Parâmetros inválidos!")
        return
    headers = HEADERS_PADRAO.copy()
    threading.Thread(
        target=rastrear_gui,
        args=(url, headers, profundidade, mesmo_dominio, atraso, max_paginas, txt_output, progress),
        daemon=True
    ).start()

# ---------------- Janela ----------------
root = tk.Tk()
root.title("Web Crawler Emails Telefone Link")
root.geometry("1280x1024")

tk.Label(root, text="Digite a url do website (ex: https://example.com)", font=("Arial", 10)).pack(pady=6)

frame_inputs = tk.Frame(root)
frame_inputs.pack(pady=10)

tk.Label(frame_inputs, text="URL inicial:").grid(row=0, column=0, sticky="e")
entry_url = tk.Entry(frame_inputs, width=60)
entry_url.grid(row=0, column=1, padx=5)

tk.Label(frame_inputs, text="Profundidade:").grid(row=1, column=0, sticky="e")
entry_profundidade = tk.Entry(frame_inputs, width=10)
entry_profundidade.insert(0, "2")
entry_profundidade.grid(row=1, column=1, sticky="w", padx=5)

var_mesmo_dominio = tk.BooleanVar(value=True)
chk_mesmo_dominio = tk.Checkbutton(frame_inputs, text="Mesmo domínio?", variable=var_mesmo_dominio)
chk_mesmo_dominio.grid(row=1, column=1, sticky="e", padx=5)

tk.Label(frame_inputs, text="Atraso (s):").grid(row=2, column=0, sticky="e")
entry_atraso = tk.Entry(frame_inputs, width=10)
entry_atraso.insert(0, "0.5")
entry_atraso.grid(row=2, column=1, sticky="w", padx=5)

tk.Label(frame_inputs, text="Máx páginas:").grid(row=3, column=0, sticky="e")
entry_max_paginas = tk.Entry(frame_inputs, width=10)
entry_max_paginas.insert(0, "1000")
entry_max_paginas.grid(row=3, column=1, sticky="w", padx=5)

btn_iniciar = tk.Button(frame_inputs, text="Iniciar Rastreamento", bg="#03fc0b", fg="black", command=iniciar_rastreamento_thread)
btn_iniciar.grid(row=4, column=0, columnspan=2, pady=5)

btn_salvar = tk.Button(root, text="💾 Salvar Resultados 💾", bg="#fc9d03", fg="black", command=salvar_resultados)
btn_salvar.pack(pady=5)

progress = ttk.Progressbar(root, orient="horizontal", length=800, mode="determinate")
progress.pack(pady=5)

txt_output = scrolledtext.ScrolledText(root, width=145, height=40)
txt_output.pack(pady=5)

root.mainloop()
