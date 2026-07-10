import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinter import Canvas
import requests
from PIL import Image, ImageTk
import socket
from urllib.parse import urlparse, urljoin
from io import BytesIO
import os
from bs4 import BeautifulSoup
import threading
import re
import subprocess
import sys
import shutil
import random
import time

# =========================================================
# USER AGENTS
# =========================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]

def carregar_user_agents_txt():
    global USER_AGENTS
    caminho = filedialog.askopenfilename(title="Selecionar user-agent.txt", filetypes=[("Arquivo TXT", "*.txt")])
    if not caminho:
        return
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            novos_agents = [linha.strip() for linha in f if linha.strip()]
        if novos_agents:
            USER_AGENTS = novos_agents
            messagebox.showinfo("Sucesso", f"{len(USER_AGENTS)} User-Agents carregados.")
        else:
            messagebox.showwarning("Aviso", "Nenhum User-Agent encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao carregar TXT:\n{e}")

def gerar_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }

# =========================================================
# VARIÁVEIS GLOBAIS
# =========================================================

img_original = None
html_atual = ""
urls_extraidas = []
dominio_detectado = None

# =========================================================
# FUNÇÕES CHROME ANÔNIMO
# =========================================================

def abrir_no_chrome_anonimo(url):
    try:
        caminhos = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome = next((c for c in caminhos if os.path.isfile(c)), None)
        if not chrome and sys.platform != "win32":
            chrome = shutil.which("google-chrome") or shutil.which("chrome")

        if chrome:
            subprocess.Popen([chrome, "--incognito", "--start-maximized", url])
        else:
            messagebox.showerror("Erro", "Google Chrome não encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir Chrome:\n{e}")

def abrir_url_no_chrome_anonima(event):
    try:
        widget = event.widget
        index = widget.index(f"@{event.x},{event.y}")
        linha = widget.get(index + " linestart", index + " lineend").strip()
        match = re.search(r'(https?://[^\s"\'<>]+)', linha)
        if match:
            abrir_no_chrome_anonimo(match.group(1))
    except:
        pass

def abrir_todas_urls_anonimas():
    if not urls_extraidas:
        messagebox.showwarning("Aviso", "Nenhuma URL encontrada.")
        return
    if messagebox.askyesno("Confirmar", f"Abrir TODAS as {len(urls_extraidas)} URLs em modo anônimo?"):
        for url in urls_extraidas:
            if url.startswith(("http://", "https://")):
                abrir_no_chrome_anonimo(url)
                time.sleep(0.7)

# =========================================================
# ASN BGP - CORRIGIDO
# =========================================================

def abrir_asn_bgp():
    texto = aba_geral_texto.get(1.0, tk.END)
    match = re.search(r'Organização:\s*(AS\d+)', texto)
    
    if not match:
        messagebox.showwarning("Aviso", "ASN não encontrado.")
        return

    numero_as = match.group(1)
    url = f"https://bgp.he.net/{numero_as}"

    try:
        abrir_no_chrome_anonimo(url)   # ← Agora usa a função unificada
        # Alternativa direta:
        # subprocess.Popen([chrome_path, "--incognito", "--start-maximized", url])
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir ASN:\n{e}")


# =========================================================
# OUTRAS FUNÇÕES (mantidas do seu código)
# =========================================================

def obter_as_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("org", "Unknown Organization")
        return "Unknown Organization"
    except:
        return "Error: Não foi possível obter"

def update_progress(value):
    barra_progresso['value'] = value
    root.update_idletasks()

def salvar_imagem():
    global img_original
    if img_original:
        caminho = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if caminho:
            img_original.save(caminho, format="PNG")
            messagebox.showinfo("OK", "Imagem salva com sucesso.")
    else:
        messagebox.showwarning("Aviso", "Nenhuma imagem carregada.")

def salvar_todas_imagens():
    global html_atual
    url = entrada_url.get().strip()
    if not html_atual:
        messagebox.showwarning("Aviso", "Nenhum HTML carregado.")
        return
    pasta = filedialog.askdirectory()
    if not pasta: return

    soup = BeautifulSoup(html_atual, "html.parser")
    baixadas = 0
    for idx, tag in enumerate(soup.find_all("img"), 1):
        src = tag.get("src")
        if not src or src.startswith("data:"): continue
        src_url = urljoin(url, src)
        try:
            resp = requests.get(src_url, headers=gerar_headers(), timeout=15)
            resp.raise_for_status()
            ext = os.path.splitext(urlparse(src_url).path)[1] or ".png"
            caminho = os.path.join(pasta, f"image_{idx}{ext}")
            with open(caminho, "wb") as f:
                f.write(resp.content)
            baixadas += 1
        except:
            pass
    messagebox.showinfo("Finalizado", f"Imagens baixadas: {baixadas}")

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

def extrair_todas_urls(html_content, base_url=None):
    global dominio_detectado
    dominio_detectado = detectar_dominio_base(html_content) if not base_url else base_url
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = set()
    tags = [('a','href'),('img','src'),('script','src'),('link','href'),('iframe','src'),('video','src'),('audio','src'),('form','action')]
    for tag in soup.find_all(True):
        for name, attr in tags:
            if tag.name == name and tag.has_attr(attr):
                valor = tag[attr]
                if isinstance(valor, str):
                    if valor.startswith("http"):
                        urls.add(valor)
                    elif valor.startswith("/") and dominio_detectado:
                        urls.add(urljoin(dominio_detectado, valor))
    urls.update(re.compile(r'http[s]?://[^\s"\'<>]+').findall(html_content))
    return sorted(urls)

def mostrar_urls():
    aba_urls_texto.delete(1.0, tk.END)
    if urls_extraidas:
        aba_urls_texto.insert(tk.END, f"TOTAL URL: {len(urls_extraidas)}\n\n")
        if dominio_detectado:
            aba_urls_texto.insert(tk.END, f"DOMINIO: {dominio_detectado}\n\n")
        for idx, url in enumerate(urls_extraidas, 1):
            aba_urls_texto.insert(tk.END, f"URL #{idx}: {url}\n\n")

def pesquisar_urls():
    termo = entrada_pesquisa.get().strip().lower()
    aba_urls_texto.delete(1.0, tk.END)
    filtradas = [url for url in urls_extraidas if termo in url.lower()]
    for i, url in enumerate(filtradas, 1):
        aba_urls_texto.insert(tk.END, f"URL: {i}\n\n{url}\n\n\n\n")

def salvar_urls():
    if not urls_extraidas:
        messagebox.showwarning("Aviso", "Nenhuma URL encontrada.")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"TOTAL URL: {len(urls_extraidas)}\n\n")
            if dominio_detectado:
                f.write(f"DOMINIO DETECTADO: {dominio_detectado}\n\n")
            for idx, url in enumerate(urls_extraidas, 1):
                f.write(f"URL #{idx}: {url}\n\n")
        messagebox.showinfo("OK", f"{len(urls_extraidas)} URLs salvas.")

def abrir_arquivo():
    global urls_extraidas, html_atual
    caminho = filedialog.askopenfilename(filetypes=[("HTML", "*.html *.htm")])
    if caminho:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                html_atual = f.read()
            urls_extraidas = extrair_todas_urls(html_atual)
            mostrar_urls()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

# =========================================================
# BUSCAR DADOS
# =========================================================

def buscar_dados():

    def run_fetch():

        global img_original
        global html_atual
        global urls_extraidas

        url = entrada_url.get().strip()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:

            update_progress(10)

            parsed = urlparse(url)

            hostname = parsed.hostname

            ip = socket.gethostbyname(hostname)

            porta = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)

            org_info = obter_as_info(ip)

            update_progress(20)

            # =====================================================
            # REQUEST COM USER AGENT AUTOMÁTICO
            # =====================================================

            headers = gerar_headers()

            sessao = requests.Session()

            resposta = sessao.get(url, headers=headers, timeout=20, allow_redirects=True)

            # TENTA NOVAMENTE CASO 403
            if resposta.status_code == 403:

                for _ in range(5):

                    headers = gerar_headers()

                    resposta = sessao.get(url, headers=headers, timeout=20)

                    if resposta.status_code != 403:
                        break

                    time.sleep(1)

            resposta.raise_for_status()

            html_atual = resposta.text

            org_info = obter_as_info(ip)
            if org_info.startswith("AS") and " " in org_info:
                numero_as, organizacao = org_info.split(" ", 1)
                detalhes_as = f"https://bgp.he.net/{numero_as}"
            else:
                numero_as = "Unknown AS"
                organizacao = org_info if org_info != "Unknown Organization" else org_info
                detalhes_as = "N/A"

            geral = (
                f"Request URL: {resposta.url}\n"
                f"\nRemote Address: {ip}:{porta}\n"
                f"\nRequest Method: {resposta.request.method}\n"
                f"\nStatus Code: {resposta.status_code} {resposta.reason}\n"
                f"\nOrganização: {numero_as} {organizacao}\n"
                f"\nDetalhes AS: {detalhes_as}\n\n"                
                f"\nUSER-AGENT\n\n{headers['User-Agent']}"


            )

            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, geral)

            update_progress(30)

            # =====================================================
            # HEADERS
            # =====================================================

            cabecalhos = "\n".join(f"{k}: {v}" for k, v in resposta.headers.items())

            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos)

            update_progress(40)

            # =====================================================
            # RESPONSE
            # =====================================================

            aba_resposta_texto.delete(1.0, tk.END)

            aba_resposta_texto.insert(tk.END, html_atual[:50000])

            update_progress(50)

            # =====================================================
            # PAYLOAD
            # =====================================================

            soup = BeautifulSoup(html_atual, "html.parser")

            payload = ""

            for script in soup.find_all("script"):

                if script.get("src"):

                    script_url = urljoin(url, script.get("src"))

                    try:

                        headers = gerar_headers()

                        r = requests.get(script_url, headers=headers, timeout=10)

                        payload += f"\n\n===== {script_url} =====\n\n"

                        payload += r.text

                    except Exception as ex:

                        payload += f"\nERRO: {ex}\n"

                else:

                    if script.string:
                        payload += script.string + "\n"

            aba_payload_texto.delete(1.0, tk.END)

            aba_payload_texto.insert(tk.END, payload if payload else "Nenhum payload.")

            update_progress(60)

            # =====================================================
            # INITIATOR
            # =====================================================

            recursos = []

            for script in soup.find_all("script", src=True):
                recursos.append({
                    "tipo": "SCRIPT",
                    "url": urljoin(url, script["src"])
                })

            for link in soup.find_all("link", href=True):
                recursos.append({
                    "tipo": "CSS",
                    "url": urljoin(url, link["href"])
                })

            for img in soup.find_all("img", src=True):
                if not img["src"].startswith("data:"):
                    recursos.append({
                        "tipo": "IMAGE",
                        "url": urljoin(url, img["src"])
                    })

            aba_iniciador_texto.delete(1.0, tk.END)

            # Configuração de cores
            aba_iniciador_texto.tag_configure("green",  foreground="#00ff00")   # Sucesso (200)
            aba_iniciador_texto.tag_configure("yellow", foreground="#ffff00")   # Redirecionamento (301/302)
            aba_iniciador_texto.tag_configure("red",    foreground="#ff4444")   # Bloqueado / Erro (403)
            aba_iniciador_texto.tag_configure("blue",   foreground="#00aaff")   # URL
            aba_iniciador_texto.tag_configure("gray",   foreground="#aaaaaa")   # Texto normal

            for idx, r in enumerate(recursos, 1):
                try:
                    headers = gerar_headers()
                    resp = requests.head(
                        r["url"],
                        headers=headers,
                        timeout=10,
                        allow_redirects=True
                    )
                    status = resp.status_code
                    tamanho = resp.headers.get("Content-Length", "?")
                except:
                    status = "ERRO"
                    tamanho = "?"

                # Escolha da cor conforme o status
                if isinstance(status, int):
                    if status == 200:
                        status_tag = "green"
                    elif status in (301, 302, 307, 308):
                        status_tag = "yellow"
                    elif status in (403, 404, 500, 502, 503):
                        status_tag = "red"
                    else:
                        status_tag = "gray"
                else:
                    status_tag = "red"

                # Inserção formatada
                aba_iniciador_texto.insert(tk.END, f"RESOURCE #{idx}\n", "green")
                aba_iniciador_texto.insert(tk.END, f"TYPE: {r['tipo']}\n", "gray")
                aba_iniciador_texto.insert(tk.END, f"URL: {r['url']}\n", "blue")
                aba_iniciador_texto.insert(tk.END, f"STATUS: {status}\n", status_tag)
                aba_iniciador_texto.insert(tk.END, f"SIZE: {tamanho}\n", "gray")
                aba_iniciador_texto.insert(tk.END, "-" * 70 + "\n", "gray")

            update_progress(70)

            # =====================================================
            # EXTRAIR URLS
            # =====================================================

            urls_extraidas = extrair_todas_urls(html_atual, base_url=url)

            mostrar_urls()

            update_progress(80)

            # =====================================================
            # SCREENSHOT
            # =====================================================

            try:

                screenshot_url = f"https://image.thum.io/get/fullpage/{url}"

                screen = requests.get(screenshot_url, timeout=60)

                img_data = BytesIO(screen.content)

                img_original = Image.open(img_data)

                largura = 1200

                ratio = largura / img_original.width

                altura = int(img_original.height * ratio)

                img_resize = img_original.resize((largura, altura), Image.LANCZOS)

                tk_img = ImageTk.PhotoImage(img_resize)

                aba_visualizacao_canvas.delete("all")

                aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)

                aba_visualizacao_canvas.image = tk_img

                aba_visualizacao_canvas.config(scrollregion=(0, 0, largura, altura))

            except Exception as e:                
                  pass              

            update_progress(100)

        except Exception as e:

            update_progress(0)

            messagebox.showerror("ERRO", str(e))

    threading.Thread(target=run_fetch, daemon=True).start()


# =========================================================
# GUI - TEMA DARK + VERDE
# =========================================================

root = tk.Tk()
root.title("AVANÇADO EXTRATOR DE URL WEBSITE")
root.geometry("1280x1024")
root.wm_state("zoomed")
root.configure(bg="#0f0f0f")  # Fundo escuro

# Estilo Dark
style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background="#0f0f0f")
style.configure("TLabel", background="#0f0f0f", foreground="#00ff88")
style.configure("TButton", background="#1e1e1e", foreground="#00ff88", font=("Arial", 10, "bold"))
style.configure("TEntry", fieldbackground="#1e1e1e", foreground="#ffffff", insertcolor="#00ff88")
style.configure("TNotebook", background="#0f0f0f", borderwidth=0)
style.configure("TNotebook.Tab", background="#1e1e1e", foreground="#00cc77", padding=[10, 5])
style.map("TNotebook.Tab", background=[("selected", "#00ff88")], foreground=[("selected", "#000000")])

style.configure("TProgressbar", background="#00ff88", troughcolor="#1e1e1e")

# URL Frame
frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

ttk.Label(frame_url, text="Digite a URL do website", font=("Arial", 12, "bold")).pack(pady=5)
entrada_url = ttk.Entry(frame_url, width=90, font=("Arial", 11))
entrada_url.pack(pady=5)

# Botões
frame_buttons = ttk.Frame(frame_url)
frame_buttons.pack(pady=5)

tk.Button(frame_buttons, text="🔍 Extrair URL", bg="#00ff44", fg="black", font=("Arial", 10, "bold"), command=buscar_dados).pack(side='left', padx=4)
tk.Button(frame_buttons, text="📁 Abrir HTML", bg="#00ccff", fg="black", font=("Arial", 10, "bold"), command=abrir_arquivo).pack(side='left', padx=4)

# Botão ASN
botao_asn = tk.Button(frame_buttons, text="Abrir ASN BGP", bg="#ff8566", fg="black", font=("Arial", 10, "bold"), command=abrir_asn_bgp)
botao_asn.pack(side='left', padx=5)

tk.Button(frame_buttons, text="💾 Salvar URL", bg="#ffcc00", fg="black", font=("Arial", 10, "bold"), command=salvar_urls).pack(side='left', padx=4)
tk.Button(frame_buttons, text="🌐 Abrir Todas Anônimo", bg="#ff4444", fg="black", font=("Arial", 10, "bold"), command=abrir_todas_urls_anonimas).pack(side='left', padx=4)
tk.Button(frame_buttons, text="📋 User-Agents", bg="#ff66ff", fg="black", font=("Arial", 10, "bold"), command=carregar_user_agents_txt).pack(side='left', padx=4)



entrada_pesquisa = ttk.Entry(frame_buttons, width=30)
entrada_pesquisa.pack(side="left", padx=5)
ttk.Button(frame_buttons, text="Pesquisar", command=pesquisar_urls).pack(side="left", padx=5)

barra_progresso = ttk.Progressbar(root, length=600, mode='determinate')
barra_progresso.pack(pady=10)

# =========================================================
# ABAS (Dark Theme)
# =========================================================

abas = ttk.Notebook(root)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# General
frame_geral = ttk.Frame(abas)
aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_geral_texto.pack(fill='both', expand=True)
abas.add(frame_geral, text="General")

# Headers
frame_headers = ttk.Frame(abas)
aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_headers, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_cabecalhos_texto.pack(fill='both', expand=True)
abas.add(frame_headers, text="Headers")

# Response
frame_response = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_response, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_resposta_texto.pack(fill='both', expand=True)
abas.add(frame_response, text="Response")

# Initiator
frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_iniciador_texto.pack(fill='both', expand=True)
aba_iniciador_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_iniciador, text="Initiator")

# URL
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_urls_texto.pack(fill='both', expand=True)
aba_urls_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_urls, text="URL")

# Payload
frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_payload_texto.pack(fill='both', expand=True)
abas.add(frame_payload, text="Payload")

# Preview
frame_visualizacao = ttk.Frame(abas)
canvas_frame = tk.Frame(frame_visualizacao, bg="#0f0f0f")
canvas_frame.pack(fill='both', expand=True)

aba_visualizacao_canvas = Canvas(canvas_frame, bg='#0a0a0a')
scrollbar_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=aba_visualizacao_canvas.yview)
aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)
scrollbar_v.pack(side='right', fill='y')
aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)

aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")
aba_visualizacao_texto.pack()
abas.add(frame_visualizacao, text="Preview")

# Save Images
frame_save = ttk.Frame(abas)
texto_save = scrolledtext.ScrolledText(frame_save, height=8, bg="#1e1e1e", fg="#00ff88")
texto_save.insert(tk.END, "Salvar screenshot e imagens do website.")
texto_save.config(state='disabled')
texto_save.pack(fill='x')
ttk.Button(frame_save, text="Salvar Screenshot", command=salvar_imagem).pack(pady=5)
ttk.Button(frame_save, text="Salvar Todas Imagens", command=salvar_todas_imagens).pack(pady=5)
abas.add(frame_save, text="Save Images")

# =========================================================
# RODAPÉ (FOOTER) - INSTRUÇÕES DE USO
# =========================================================

frame_rodape = tk.Frame(root, bg="#1e1e1e", height=40)
frame_rodape.pack(side='bottom', fill='x')

# Linha de instruções
instrucoes = (
    "Como usar: 1. Cole a URL → 2. Clique em 'Extrair URL' → "
    "3. Clique duplo em qualquer URL para abrir no Chrome Anônimo → "
    "4. Use 'Abrir Todas Anônimo' para abrir todas de uma vez"
)

label_rodape = tk.Label(
    frame_rodape,
    text=instrucoes,
    bg="#1e1e1e",
    fg="#00c3ff",
    font=("Arial", 9),
    wraplength=1200,
    justify="center"
)
label_rodape.pack(pady=8, padx=10)

# Versão / Crédito (opcional)
label_versao = tk.Label(
    frame_rodape,
    text="AVANÇADO EXTRATOR DE URL WEBSITE | Clique duplo = Chrome Anônimo",
    bg="#1e1e1e",
    fg="#919191",
    font=("Arial", 8)
)
label_versao.pack(side='bottom', pady=2)

# =========================================================
# START
# =========================================================

root.mainloop()
