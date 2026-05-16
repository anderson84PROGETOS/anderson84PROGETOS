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
# CARREGAR USER AGENTS VIA TXT
# =========================================================

def carregar_user_agents_txt():

    global USER_AGENTS

    caminho = filedialog.askopenfilename(
        title="Selecionar user-agent.txt",
        filetypes=[("Arquivo TXT", "*.txt")]
    )

    if not caminho:
        return

    try:

        novos_agents = []

        with open(caminho, "r", encoding="utf-8") as f:

            linhas = f.readlines()

            for linha in linhas:

                linha = linha.strip()

                if linha:
                    novos_agents.append(linha)

        if not novos_agents:

            messagebox.showwarning(
                "Aviso",
                "Nenhum User-Agent encontrado."
            )

            return

        USER_AGENTS = novos_agents

        messagebox.showinfo(
            "Sucesso",
            f"{len(USER_AGENTS)} User-Agents carregados."
        )

    except Exception as e:

        messagebox.showerror(
            "Erro",
            f"Falha ao carregar TXT:\n{e}"
        )

def gerar_headers():
    """Gera headers aleatórios."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice([
            "en-US,en;q=0.9",
            "pt-BR,pt;q=0.9,en;q=0.8",
            "en-GB,en;q=0.9"
        ]),
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
# ASN / ORG
# =========================================================

def obter_as_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("org", "Unknown Organization")

        return "Unknown Organization"

    except Exception as e:
        return f"Error: {e}"

# =========================================================
# PROGRESSO
# =========================================================

def update_progress(value):
    barra_progresso['value'] = value
    root.update_idletasks()

# =========================================================
# SALVAR SCREENSHOT
# =========================================================

def salvar_imagem():

    global img_original

    if img_original:

        caminho = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )

        if caminho:
            img_original.save(caminho, format="PNG")
            messagebox.showinfo("OK", "Imagem salva com sucesso.")

    else:
        messagebox.showwarning("Aviso", "Nenhuma imagem carregada.")

# =========================================================
# SALVAR TODAS IMAGENS
# =========================================================

def salvar_todas_imagens():

    global html_atual

    url = entrada_url.get().strip()

    if not html_atual:
        messagebox.showwarning("Aviso", "Nenhum HTML carregado.")
        return

    pasta = filedialog.askdirectory()

    if not pasta:
        return

    soup = BeautifulSoup(html_atual, "html.parser")

    tags_img = soup.find_all("img")

    baixadas = 0

    for idx, tag in enumerate(tags_img, 1):

        src = tag.get("src")

        if not src:
            continue

        src_url = urljoin(url, src)

        if src_url.startswith("data:"):
            continue

        try:

            headers = gerar_headers()

            resp = requests.get(
                src_url,
                headers=headers,
                timeout=15
            )

            if resp.status_code == 403:
                time.sleep(1)
                headers = gerar_headers()

                resp = requests.get(
                    src_url,
                    headers=headers,
                    timeout=15
                )

            resp.raise_for_status()

            ext = os.path.splitext(
                urlparse(src_url).path
            )[1]

            if ext.lower() not in [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".bmp"
            ]:
                ext = ".png"

            caminho = os.path.join(
                pasta,
                f"image_{idx}{ext}"
            )

            with open(caminho, "wb") as f:
                f.write(resp.content)

            baixadas += 1

        except:
            pass

    messagebox.showinfo(
        "Finalizado",
        f"Imagens baixadas: {baixadas}"
    )

# =========================================================
# DETECTAR DOMINIO
# =========================================================

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

def abrir_asn_bgp():

    texto = aba_geral_texto.get(1.0, tk.END)

    match = re.search(r'Organização:\s*(AS\d+)', texto)

    if not match:

        messagebox.showwarning(
            "Aviso",
            "ASN não encontrado."
        )

        return

    numero_as = match.group(1)

    url = f"https://bgp.he.net/{numero_as}"

    try:

        caminhos_possiveis = []

        if sys.platform == "win32":

            caminhos_possiveis = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]

        elif sys.platform == "darwin":

            caminhos_possiveis = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]

        else:

            caminhos_possiveis = [
                "google-chrome",
                "chrome",
                "chromium-browser",
                "chromium"
            ]

        caminho_chrome = None

        for caminho in caminhos_possiveis:

            if os.path.isfile(caminho) or shutil.which(caminho):

                caminho_chrome = caminho

                break

        if caminho_chrome is None:

            messagebox.showerror(
                "Erro",
                "Google Chrome não encontrado."
            )

            return

        subprocess.Popen([
            caminho_chrome,
            "--incognito",
            "--start-maximized",
            url
        ])

    except Exception as e:

        messagebox.showerror(
            "Erro",
            f"Falha ao abrir ASN:\n{e}"
        )

# =========================================================
# EXTRAIR URLS
# =========================================================

def extrair_todas_urls(html_content, base_url=None):

    global dominio_detectado

    dominio_detectado = detectar_dominio_base(html_content) \
        if not base_url else base_url

    soup = BeautifulSoup(html_content, 'html.parser')

    urls = set()

    tags_atributos = [

        ('a', 'href'),
        ('img', 'src'),
        ('script', 'src'),
        ('link', 'href'),
        ('iframe', 'src'),
        ('video', 'src'),
        ('audio', 'src'),
        ('form', 'action')

    ]

    total = len(soup.find_all(True))

    for i, tag in enumerate(soup.find_all(True)):

        for tag_name, attr in tags_atributos:

            if tag.name == tag_name and tag.has_attr(attr):

                valor = tag[attr]

                if isinstance(valor, str):

                    if valor.startswith("http"):

                        urls.add(valor)

                    elif valor.startswith("/") and dominio_detectado:

                        urls.add(
                            urljoin(dominio_detectado, valor)
                        )

        if total > 0:
            update_progress(
                int((i + 1) / total * 100)
            )

    padrao_url = re.compile(r'http[s]?://[^\s"\'<>]+')

    encontrados = padrao_url.findall(html_content)

    urls.update(encontrados)

    return sorted(urls)

# =========================================================
# MOSTRAR URLS
# =========================================================

def mostrar_urls():

    aba_urls_texto.delete(1.0, tk.END)

    if urls_extraidas:

        aba_urls_texto.insert(
            tk.END,
            f"TOTAL URL: {len(urls_extraidas)}\n\n"
        )

        if dominio_detectado:

            aba_urls_texto.insert(
                tk.END,
                f"DOMINIO: {dominio_detectado}\n\n"
            )

        for idx, url in enumerate(urls_extraidas, 1):

            aba_urls_texto.insert(
                tk.END,
                f"URL #{idx}: {url}\n\n"
            )

    else:
        aba_urls_texto.insert(tk.END, "Nenhuma URL encontrada.")

# =========================================================
# SALVAR URLS
# =========================================================

def salvar_urls():

    if not urls_extraidas:

        messagebox.showwarning(
            "Aviso",
            "Nenhuma URL encontrada."
        )

        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("TXT", "*.txt")]
    )

    if caminho:

        with open(caminho, "w", encoding="utf-8") as f:

            f.write(
                f"TOTAL URL: {len(urls_extraidas)}\n\n"
            )

            if dominio_detectado:

                f.write(
                    f"DOMINIO DETECTADO: {dominio_detectado}\n\n"
                )

            for idx, url in enumerate(urls_extraidas, 1):

                f.write(
                    f"URL #{idx}: {url}\n\n"
                )

        messagebox.showinfo(
            "OK",
            f"{len(urls_extraidas)} URL salvas."
        )

# =========================================================
# ABRIR HTML
# =========================================================

def abrir_arquivo():

    global urls_extraidas
    global html_atual

    caminho = filedialog.askopenfilename(
        filetypes=[("HTML", "*.html *.htm")]
    )

    if caminho:

        try:

            with open(caminho, "r", encoding="utf-8") as f:
                html_atual = f.read()

            update_progress(0)

            urls_extraidas = extrair_todas_urls(html_atual)

            mostrar_urls()

        except Exception as e:

            messagebox.showerror(
                "Erro",
                str(e)
            )

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

            porta = parsed.port if parsed.port else (
                443 if parsed.scheme == "https" else 80
            )

            org_info = obter_as_info(ip)

            update_progress(20)

            # =====================================================
            # REQUEST COM USER AGENT AUTOMÁTICO
            # =====================================================

            headers = gerar_headers()

            sessao = requests.Session()

            resposta = sessao.get(
                url,
                headers=headers,
                timeout=20,
                allow_redirects=True
            )

            # TENTA NOVAMENTE CASO 403
            if resposta.status_code == 403:

                for _ in range(5):

                    headers = gerar_headers()

                    resposta = sessao.get(
                        url,
                        headers=headers,
                        timeout=20
                    )

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

            cabecalhos = "\n".join(
                f"{k}: {v}"
                for k, v in resposta.headers.items()
            )

            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos)

            update_progress(40)

            # =====================================================
            # RESPONSE
            # =====================================================

            aba_resposta_texto.delete(1.0, tk.END)

            aba_resposta_texto.insert(
                tk.END,
                html_atual[:50000]
            )

            update_progress(50)

            # =====================================================
            # PAYLOAD
            # =====================================================

            soup = BeautifulSoup(
                html_atual,
                "html.parser"
            )

            payload = ""

            for script in soup.find_all("script"):

                if script.get("src"):

                    script_url = urljoin(
                        url,
                        script.get("src")
                    )

                    try:

                        headers = gerar_headers()

                        r = requests.get(
                            script_url,
                            headers=headers,
                            timeout=10
                        )

                        payload += f"\n\n===== {script_url} =====\n\n"

                        payload += r.text

                    except Exception as ex:

                        payload += f"\nERRO: {ex}\n"

                else:

                    if script.string:
                        payload += script.string + "\n"

            aba_payload_texto.delete(1.0, tk.END)

            aba_payload_texto.insert(
                tk.END,
                payload if payload else "Nenhum payload."
            )

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

            aba_iniciador_texto.tag_configure(
                "green",
                foreground="#00ff00"
            )

            aba_iniciador_texto.tag_configure(
                "red",
                foreground="red"
            )

            aba_iniciador_texto.tag_configure(
                "blue",
                foreground="#00aaff"
            )

            for idx, r in enumerate(recursos, 1):

                try:

                    headers = gerar_headers()

                    resp = requests.head(
                        r["url"],
                        headers=headers,
                        timeout=10
                    )

                    status = f"{resp.status_code}"

                    tamanho = resp.headers.get(
                        "Content-Length",
                        "?"
                    )

                except:

                    status = "ERRO"
                    tamanho = "?"

                aba_iniciador_texto.insert(
                    tk.END,
                    f"RESOURCE #{idx}\n",
                    "green"
                )

                aba_iniciador_texto.insert(
                    tk.END,
                    f"TYPE: {r['tipo']}\n"
                )

                aba_iniciador_texto.insert(
                    tk.END,
                    f"URL: {r['url']}\n",
                    "blue"
                )

                aba_iniciador_texto.insert(
                    tk.END,
                    f"STATUS: {status}\n",
                    "red"
                )

                aba_iniciador_texto.insert(
                    tk.END,
                    f"SIZE: {tamanho}\n"
                )

                aba_iniciador_texto.insert(
                    tk.END,
                    "-" * 60 + "\n"
                )

            update_progress(70)

            # =====================================================
            # EXTRAIR URLS
            # =====================================================

            urls_extraidas = extrair_todas_urls(
                html_atual,
                base_url=url
            )

            mostrar_urls()

            update_progress(80)

            # =====================================================
            # SCREENSHOT
            # =====================================================

            try:

                screenshot_url = f"https://image.thum.io/get/fullpage/{url}"

                screen = requests.get(
                    screenshot_url,
                    timeout=60
                )

                img_data = BytesIO(screen.content)

                img_original = Image.open(img_data)

                largura = 1200

                ratio = largura / img_original.width

                altura = int(img_original.height * ratio)

                img_resize = img_original.resize(
                    (largura, altura),
                    Image.LANCZOS
                )

                tk_img = ImageTk.PhotoImage(img_resize)

                aba_visualizacao_canvas.delete("all")

                aba_visualizacao_canvas.create_image(
                    0,
                    0,
                    anchor='nw',
                    image=tk_img
                )

                aba_visualizacao_canvas.image = tk_img

                aba_visualizacao_canvas.config(
                    scrollregion=(0, 0, largura, altura)
                )

            except Exception as e:

                aba_visualizacao_texto.config(
                    text=f"Screenshot Error: {e}"
                )

            update_progress(100)

        except Exception as e:

            update_progress(0)

            messagebox.showerror(
                "ERRO",
                str(e)
            )

    threading.Thread(
        target=run_fetch,
        daemon=True
    ).start()

# =========================================================
# ABRIR URL CHROME
# =========================================================

def abrir_url_no_chrome_anonima(event):

    try:

        widget = event.widget

        index = widget.index(f"@{event.x},{event.y}")

        linha = widget.get(
            index + " linestart",
            index + " lineend"
        ).strip()

        url = None

        if "http://" in linha or "https://" in linha:

            partes = linha.split(":", 1)

            if len(partes) > 1:
                url = partes[1].strip()

        if url:

            caminhos = [

                os.path.expandvars(
                    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
                ),

                os.path.expandvars(
                    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
                ),

                os.path.expandvars(
                    r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
                )

            ]

            chrome = None

            for c in caminhos:

                if os.path.isfile(c):
                    chrome = c
                    break

            if chrome:

                subprocess.Popen([
                    chrome,
                    "--incognito",
                    "--start-maximized",
                    url
                ])

            else:

                messagebox.showerror(
                    "Erro",
                    "Chrome não encontrado."
                )

    except Exception as e:

        messagebox.showerror(
            "Erro",
            str(e)
        )

# =========================================================
# GUI
# =========================================================

root = tk.Tk()
root.title("EXTRATOR AVANÇADO DE URL WEBSITE")
root.geometry("1280x1024")
root.wm_state("zoomed")

# =========================================================
# URL
# =========================================================

frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

label_url = ttk.Label(frame_url, text="Digite a URL do website", font=("Arial", 12, "bold"))
label_url.pack(pady=5)

entrada_url = ttk.Entry(frame_url, width=80, font=("Arial", 11))
entrada_url.pack(pady=5)

# =========================================================
# BOTÕES
# =========================================================

frame_buttons = ttk.Frame(frame_url)
frame_buttons.pack()

botao_buscar = tk.Button(frame_buttons, text="Extrair URL", bg="#00ff44", fg="black", font=("Arial", 10, "bold"), command=buscar_dados)
botao_buscar.pack(side='left', padx=5)

botao_asn = tk.Button(frame_buttons, text="Abrir ASN BGP", bg="#ff8566", fg="black", font=("Arial", 10, "bold"), command=abrir_asn_bgp)
botao_asn.pack(side='left', padx=5)

botao_abrir = tk.Button(frame_buttons, text="Abrir HTML", bg="#00ccff", fg="black", font=("Arial", 10, "bold"), command=abrir_arquivo)
botao_abrir.pack(side='left', padx=5)

botao_salvar = tk.Button(frame_buttons,text="Salvar URL", bg="#ffcc00", fg="black", font=("Arial", 10, "bold"), command=salvar_urls)
botao_salvar.pack(side='left', padx=5)

botao_useragent = tk.Button(frame_buttons, text="Carregar User-Agent TXT", bg="#ff66ff", fg="black", font=("Arial", 10, "bold"), command=carregar_user_agents_txt)
botao_useragent.pack(side='left', padx=5)

# =========================================================
# BARRA
# =========================================================

barra_progresso = ttk.Progressbar(root, length=500, mode='determinate')
barra_progresso.pack(pady=10)

# =========================================================
# ABAS
# =========================================================

abas = ttk.Notebook(root)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# =========================================================
# GERAL
# =========================================================

frame_geral = ttk.Frame(abas)

aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD)
aba_geral_texto.pack(fill='both', expand=True)
abas.add(frame_geral, text="General")

# =========================================================
# HEADERS
# =========================================================

frame_headers = ttk.Frame(abas)

aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_headers, wrap=tk.WORD)
aba_cabecalhos_texto.pack(fill='both', expand=True)
abas.add(frame_headers, text="Headers")

# =========================================================
# RESPONSE
# =========================================================

frame_response = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_response, wrap=tk.WORD)
aba_resposta_texto.pack(fill='both', expand=True)
abas.add(frame_response, text="Response")

# =========================================================
# INITIATOR
# =========================================================

frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD)
aba_iniciador_texto.pack(fill='both', expand=True)

aba_iniciador_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_iniciador, text="Initiator")

# =========================================================
# URLS
# =========================================================

frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD)
aba_urls_texto.pack(fill='both', expand=True)

aba_urls_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_urls, text="URL")

# =========================================================
# PAYLOAD
# =========================================================

frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD)

aba_payload_texto.pack(fill='both', expand=True)
abas.add(frame_payload, text="Payload")

# =========================================================
# PREVIEW
# =========================================================

frame_visualizacao = ttk.Frame(abas)

canvas_frame = tk.Frame(frame_visualizacao)

canvas_frame.pack(fill='both', expand=True)

aba_visualizacao_canvas = Canvas(canvas_frame, bg='white')

scrollbar_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=aba_visualizacao_canvas.yview)

aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)

scrollbar_v.pack(side='right', fill='y')

aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)

aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")

aba_visualizacao_texto.pack()

abas.add(frame_visualizacao, text="Preview")

# =========================================================
# SAVE
# =========================================================

frame_save = ttk.Frame(abas)

texto_save = scrolledtext.ScrolledText(frame_save, height=8)

texto_save.insert(tk.END, "Salvar screenshot e imagens do website.")

texto_save.config(state='disabled')

texto_save.pack(fill='x')

btn_save_screen = ttk.Button(frame_save, text="Salvar Screenshot", command=salvar_imagem)

btn_save_screen.pack(pady=5)

btn_save_imgs = ttk.Button(frame_save, text="Salvar Todas Imagens", command=salvar_todas_imagens)

btn_save_imgs.pack(pady=5)

abas.add(frame_save, text="Save Images")

# =========================================================
# START
# =========================================================

root.mainloop()
