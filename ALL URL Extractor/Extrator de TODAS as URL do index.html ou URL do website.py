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

def obter_as_info(ip):
    """Fetch ASN and organization information for the given IP."""
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            org = data.get("org", "Unknown Organization")  # Ex: "AS20940 Akamai International B.V."
            return org
        else:
            return "Unknown Organization"
    except Exception as e:
        return f"Error fetching ASN data: {e}"

# Custom headers for HTTP requests
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Global variables
img_original = None  # Original screenshot image
html_atual = ""      # Current HTML content
urls_extraidas = []  # Extracted URL
dominio_detectado = None  # Detected base domain

def update_progress(value):
    """Update the progress bar."""
    barra_progresso['value'] = value
    root.update_idletasks()

def salvar_imagem():
    """Save the screenshot image."""
    global img_original
    if img_original:
        caminho = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if caminho:
            img_original.save(caminho, format='PNG')
            messagebox.showinfo("Success", f"Image saved at:\n{caminho}")
    else:
        messagebox.showwarning("Warning", "No screenshot loaded to save.")

def salvar_todas_imagens():
    """Save all images from the website."""
    global html_atual
    url = entrada_url.get().strip()
    if not html_atual:
        messagebox.showwarning("Warning", "No HTML content loaded to extract images.")
        return

    pasta = filedialog.askdirectory(title="Choose folder to save images")
    if not pasta:
        return

    soup = BeautifulSoup(html_atual, 'html.parser')
    tags_img = soup.find_all('img')

    if not tags_img:
        messagebox.showinfo("Result", "No images found on the website.")
        return

    baixadas = 0
    erros = 0

    for idx, tag in enumerate(tags_img, 1):
        src = tag.get('src')
        if not src:
            continue

        src_url = urljoin(url, src)

        # Skip base64 or invalid src
        if src_url.startswith('data:'):
            continue

        try:
            resp_img = requests.get(src_url, headers=headers_customizados, timeout=15)
            resp_img.raise_for_status()

            # Determine correct extension; default to .png if unidentified
            ext = os.path.splitext(urlparse(src_url).path)[1]
            if ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                ext = '.png'

            nome_arquivo = f"image_{idx}{ext}"
            caminho_arquivo = os.path.join(pasta, nome_arquivo)

            with open(caminho_arquivo, 'wb') as f:
                f.write(resp_img.content)
            baixadas += 1
        except Exception as e:
            erros += 1
            pass

    messagebox.showinfo("Download completed",
                        f"Images downloaded: {baixadas}")

def detectar_dominio_base(html_content):
    """Detect the base domain from HTML content."""
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
    """Extract all URL from HTML content."""
    global dominio_detectado
    dominio_detectado = detectar_dominio_base(html_content) if not base_url else base_url
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = set()

    # Tags and attributes that may contain URL
    tags_atributos = [
        ('a', 'href'), ('img', 'src'), ('script', 'src'), ('link', 'href'),
        ('iframe', 'src'), ('source', 'src'), ('video', 'src'), ('audio', 'src'),
        ('form', 'action'), ('object', 'data'), ('embed', 'src'), ('area', 'href'),
        ('track', 'src'), ('base', 'href'), ('input', 'src'), ('param', 'value'),
        ('meta', 'content')
    ]

    total = len(soup.find_all(True))
    for i, tag in enumerate(soup.find_all(True)):
        for tag_name, attr in tags_atributos:
            if tag.name == tag_name and tag.has_attr(attr):
                valor = tag[attr]
                if isinstance(valor, str):
                    partes = [v.strip().split(" ")[0] for v in valor.split(",")]
                    for parte in partes:
                        if parte.startswith("http"):
                            urls.add(parte)
                        elif parte.startswith("/") and dominio_detectado:
                            url_completa = urljoin(dominio_detectado, parte)
                            urls.add(url_completa)
        update_progress(int((i + 1) / total * 100))

    # Extract URL from text content using regex
    padrao_url = re.compile(r'http[s]?://[^\s"\'<>]+')
    encontrados = padrao_url.findall(html_content)
    urls.update(encontrados)

    return sorted(urls)

def abrir_arquivo():
    """Open and process an HTML file to extract URL."""
    global urls_extraidas, html_atual
    caminho_arquivo = filedialog.askopenfilename(
        title="Select index.html file",
        filetypes=[("HTML Files", "*.html;*.htm")]
    )

    if caminho_arquivo:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                html_atual = f.read()

            update_progress(0)
            aba_urls_texto.delete(1.0, tk.END)
            urls_extraidas = extrair_todas_urls(html_atual)
            mostrar_urls()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")

def buscar_dados():
    """Fetch website data and update tabs."""
    def run_fetch():
        global img_original, html_atual, urls_extraidas
        url = entrada_url.get().strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        try:
            update_progress(10)
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            if not hostname:
                raise ValueError("Invalid URL: hostname not found.")

            ip = socket.gethostbyname(hostname)
            porta = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)

            # Obter informações ASN usando a função fornecida
            org_info = obter_as_info(ip)
            # Extrair número AS e organização, se disponíveis
            if org_info.startswith("AS") and " " in org_info:
                numero_as, organizacao = org_info.split(" ", 1)
                detalhes_as = f"https://bgp.he.net/{numero_as}"
            else:
                numero_as = "Unknown AS"
                organizacao = org_info if org_info != "Unknown Organization" else org_info
                detalhes_as = "N/A"

            update_progress(20)
            resposta = requests.get(url, headers=headers_customizados, timeout=15)
            resposta.raise_for_status()
            html_atual = resposta.text

            # General Tab
            geral_texto = (
                f"Request URL: {resposta.url}\n"
                f"\nRemote Address: {ip}:{porta}\n"
                f"\nRequest Method: {resposta.request.method}\n"
                f"\nStatus Code: {resposta.status_code} {resposta.reason}\n"                
                f"\nOrganização: {numero_as} {organizacao}\n"
                f"\nDetalhes AS: {detalhes_as}"
            )
            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, geral_texto)
            update_progress(30)

            # Headers Tab
            cabecalhos_texto = "\n".join(f"{k}: {v}" for k, v in resposta.headers.items())
            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos_texto)
            update_progress(40)

            # Response Tab
            aba_resposta_texto.delete(1.0, tk.END)
            aba_resposta_texto.insert(tk.END, html_atual[:10000])
            update_progress(50)

            # Payload Tab (Scripts)
            soup_payload = BeautifulSoup(html_atual, 'html.parser')
            script_tags = soup_payload.find_all('script')
            payload_text = ""
            for script in script_tags:
                if script.has_attr('src'):
                    script_url = urljoin(url, script['src'])
                    try:
                        resp_script = requests.get(script_url, headers=headers_customizados, timeout=15)
                        resp_script.raise_for_status()
                        payload_text += f"<!-- Script from {script_url} -->\n{resp_script.text}\n\n"
                    except Exception as ex:
                        payload_text += f"<!-- Error loading script from {script_url}: {ex} -->\n\n"
                else:
                    if script.string:
                        payload_text += script.string + "\n\n"
            aba_payload_texto.delete(1.0, tk.END)
            aba_payload_texto.insert(tk.END, payload_text if payload_text.strip() else "No scripts found in payload.")
            update_progress(60)

            # Initiator Tab (Resources)
            soup_iniciador = BeautifulSoup(html_atual, 'html.parser')
            recursos = []
            for script in soup_iniciador.find_all('script', src=True):
                recursos.append({
                    'tipo': 'Script',
                    'url': urljoin(url, script.get('src')),
                    'status': 'N/A',
                    'tamanho': 'N/A'
                })
            for link in soup_iniciador.find_all('link', href=True):
                if link.get('rel') and 'stylesheet' in link.get('rel'):
                    recursos.append({
                        'tipo': 'CSS',
                        'url': urljoin(url, link.get('href')),
                        'status': 'N/A',
                        'tamanho': 'N/A'
                    })
            for img in soup_iniciador.find_all('img', src=True):
                if not img.get('src').startswith('data:'):
                    recursos.append({
                        'tipo': 'Image',
                        'url': urljoin(url, img.get('src')),
                        'status': 'N/A',
                        'tamanho': 'N/A'
                    })
            for recurso in recursos:
                try:
                    resp = requests.head(recurso['url'], headers=headers_customizados, timeout=5)
                    recurso['status'] = f"{resp.status_code} {resp.reason}"
                    if 'Content-Length' in resp.headers:
                        tamanho = int(resp.headers['Content-Length'])
                        recurso['tamanho'] = f"{tamanho / 1024:.2f} KB"
                except Exception:
                    recurso['status'] = 'Error'
                    recurso['tamanho'] = 'N/A'
            iniciador_text = ""
            for idx, recurso in enumerate(recursos, 1):
                iniciador_text += (
                    f"Resource #{idx}\n"
                    f"Type: {recurso['tipo']}\n"
                    f"URL: {recurso['url']}\n"
                    f"Status: {recurso['status']}\n"
                    f"Size: {recurso['tamanho']}\n"
                    f"{'-'*50}\n"
                )
            aba_iniciador_texto.delete(1.0, tk.END)
            aba_iniciador_texto.insert(tk.END, iniciador_text if iniciador_text.strip() else "No initiator resources found.")
            update_progress(70)

            # URL Tab
            urls_extraidas = extrair_todas_urls(html_atual, base_url=url)
            mostrar_urls()
            update_progress(80)

            # Preview Tab (Screenshot)
            screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
            try:
                screen_response = requests.get(screenshot_url, timeout=60)
                screen_response.raise_for_status()
                img_data = BytesIO(screen_response.content)
                img_original = Image.open(img_data)
                max_width = 1220
                ratio = max_width / img_original.width
                new_height = int(img_original.height * ratio)
                img_exibicao = img_original.resize((max_width, new_height), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img_exibicao)
                aba_visualizacao_canvas.delete("all")
                aba_visualizacao_canvas.image = tk_img
                aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
                aba_visualizacao_canvas.config(scrollregion=(0, 0, max_width, new_height))
                aba_visualizacao_texto.config(text="")
            except Exception as e:
                img_original = None
                aba_visualizacao_canvas.delete("all")
                aba_visualizacao_texto.config(text=f"Screenshot unavailable: {e}")

            update_progress(100)

        except Exception as e:
            update_progress(0)
            for text_widget in [aba_geral_texto, aba_cabecalhos_texto, aba_resposta_texto, aba_payload_texto, aba_iniciador_texto, aba_urls_texto]:
                text_widget.delete(1.0, tk.END)
            aba_urls_texto.insert(tk.END, f"Error: {e}")
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_texto.config(text="Screenshot unavailable.")
            messagebox.showerror("Error", f"Failed to fetch data: {e}")

    threading.Thread(target=run_fetch, daemon=True).start()

def mostrar_urls():
    """Display extracted URL in the URL tab."""
    aba_urls_texto.delete(1.0, tk.END)
    if urls_extraidas:
        aba_urls_texto.insert(tk.END, f"Total URL Found: {len(urls_extraidas)}\n\n")
        if dominio_detectado:
            aba_urls_texto.insert(tk.END, f"Detected Domain: {dominio_detectado}\n\n")
        for idx, url in enumerate(urls_extraidas, 1):
            aba_urls_texto.insert(tk.END, f"URL #{idx}: {url}\n\n")
    else:
        aba_urls_texto.insert(tk.END, "No URL found.")

def salvar_urls():
    """Save extracted URL to a file."""
    if not urls_extraidas:
        messagebox.showwarning("Warning", "No URL to save.")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text File", "*.txt")],
        title="Save URL as"
    )

    if caminho_salvar:
        try:
            with open(caminho_salvar, 'w', encoding='utf-8') as f:
                f.write(f"Total URL Found: {len(urls_extraidas)}\n\n")
                if dominio_detectado:
                    f.write(f"Detected Domain: {dominio_detectado}\n\n")
                for url in urls_extraidas:
                    f.write(url + "\n\n")
            aba_urls_texto.insert(tk.END, f"\n[✔] {len(urls_extraidas)} URL saved to: {caminho_salvar}\n")
            messagebox.showinfo("Saved", "URL saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save URL:\n{e}")

def abrir_url_no_chrome_anonima(event):
    """Open a URL in Chrome incognito mode maximized on double-click."""
    try:
        index = aba_urls_texto.index(f"@{event.x},{event.y}")
        linha = aba_urls_texto.get(index + " linestart", index + " lineend").strip()
        if linha.startswith("URL #"):
            url = linha.split(":", 1)[1].strip()
            if url.startswith("http"):
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
                    messagebox.showerror("Error", "Google Chrome not found on the system.")
                    return

                subprocess.Popen([caminho_chrome, "--incognito", "--start-maximized", url])
    except Exception as e:
        pass

# GUI setup
root = tk.Tk()
root.title("Extrator de TODAS as URL do index.html ou URL do website")
root.geometry("1280x1024")
root.wm_state('zoomed')

# URL input and buttons
frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

label_url = ttk.Label(frame_url, text="Digite a URL do website", font=("Arial", 12, "bold"))
label_url.pack(pady=(5, 5))

entrada_url = ttk.Entry(frame_url, width=60, font=("Arial", 11))
entrada_url.pack(pady=(0, 5))

# Frame for buttons to align them side by side
frame_buttons = ttk.Frame(frame_url)
frame_buttons.pack(pady=(0, 5))

# Buttons with tk.Button to support bg attribute
botao_buscar = tk.Button(frame_buttons, text="Extrair de URL", font=("Arial", 10), bg="#05fc32", fg="black", command=buscar_dados)
botao_buscar.pack(side='left', padx=5, pady=5)

botao_abrir = tk.Button(frame_buttons, text="Select HTML File", font=("Arial", 10), bg="#05d3f7", fg="black", command=abrir_arquivo)
botao_abrir.pack(side='left', padx=5, pady=5)

botao_salvar_urls = tk.Button(frame_buttons, text="Save URL", font=("Arial", 10), bg="#f7b705", fg="black", command=salvar_urls)
botao_salvar_urls.pack(side='left', padx=5, pady=5)

barra_progresso = ttk.Progressbar(root, length=500, mode='determinate')
barra_progresso.pack(pady=(0, 10))

# Notebook for tabs
abas = ttk.Notebook(root)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# General Tab
frame_geral = ttk.Frame(abas)
aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD, width=154, height=45)
aba_geral_texto.pack()
abas.add(frame_geral, text="General")

# Headers Tab
frame_cabecalhos = ttk.Frame(abas)
aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_cabecalhos, wrap=tk.WORD, width=154, height=45)
aba_cabecalhos_texto.pack()
abas.add(frame_cabecalhos, text="Headers")

# Response Tab
frame_resposta = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_resposta, wrap=tk.WORD, width=154, height=45)
aba_resposta_texto.pack()
abas.add(frame_resposta, text="Response")

# Initiator Tab
frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD, width=154, height=45)
aba_iniciador_texto.pack()
abas.add(frame_iniciador, text="Initiator")

# URL Tab
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, width=154, height=45)
aba_urls_texto.pack()
aba_urls_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_urls, text="URL")

# Payload Tab
frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD, width=154, height=45)
aba_payload_texto.pack()
abas.add(frame_payload, text="Payload")

# Preview Tab
frame_visualizacao = ttk.Frame(abas)
canvas_frame = tk.Frame(frame_visualizacao)
canvas_frame.pack(fill='both', expand=True)
aba_visualizacao_canvas = Canvas(canvas_frame, bg='white', width=1000, height=700)
scrollbar_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=aba_visualizacao_canvas.yview)
aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)
scrollbar_v.pack(side='right', fill='y')
aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)
aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")
aba_visualizacao_texto.pack()
abas.add(frame_visualizacao, text="Preview")

# Save Images Tab
frame_salvar = ttk.Frame(abas)
aba_salvar_texto = scrolledtext.ScrolledText(frame_salvar, wrap=tk.WORD, width=154, height=30)
aba_salvar_texto.insert(tk.END, "Click the button below to save the full page screenshot in .PNG format.\n\n"
                                "Or click 'Save all images' to download all images present on the website.")
aba_salvar_texto.config(state='disabled')
aba_salvar_texto.pack(pady=10)
botao_salvar = ttk.Button(frame_salvar, text="Save Screenshot", command=salvar_imagem)
botao_salvar.pack(pady=5)
botao_salvar_todas = ttk.Button(frame_salvar, text="Save All Website Images", command=salvar_todas_imagens)
botao_salvar_todas.pack(pady=5)
abas.add(frame_salvar, text="Save Images")

root.mainloop()
