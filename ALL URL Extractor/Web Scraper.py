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

# Custom headers
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

img_original = None  # Global variable for original image
html_atual = ""      # Store current HTML for extracting info and scripts

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
    url = entrada_url.get()
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
            print(f"Error downloading {src_url}: {e}")

    messagebox.showinfo("Download completed",
                        f"Images downloaded: {baixadas}\nErrors: {erros}")

def buscar_dados():
    """Fetch website data and update tabs."""
    def run_fetch():
        global img_original, html_atual
        url = entrada_url.get()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url  # Add default scheme

        try:
            update_progress(10)  # Start process
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            if not hostname:
                raise ValueError("Invalid URL: hostname not found.")

            ip = socket.gethostbyname(hostname)
            porta = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)

            update_progress(20)  # After resolving hostname
            resposta = requests.get(url, headers=headers_customizados, timeout=15)
            resposta.raise_for_status()

            # General Tab
            geral_texto = (
                f"Request URL: {resposta.url}\n"
                f"\nRemote Address: {ip}:{porta}\n"
                f"\nRequest Method: {resposta.request.method}\n"
                f"\nStatus Code: {resposta.status_code} {resposta.reason}\n"
                f"\nReferrer Policy: origin"
            )
            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, geral_texto)
            update_progress(30)  # After filling General tab

            # Headers Tab
            resposta_sem_ua = requests.get(url, headers=headers_customizados, timeout=15)
            cabecalhos_texto = "\n".join(f"{k}: {v}" for k, v in resposta_sem_ua.headers.items())
            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos_texto)
            update_progress(40)  # After filling Headers tab

            # Response Tab
            html_atual = resposta.text
            aba_resposta_texto.delete(1.0, tk.END)
            aba_resposta_texto.insert(tk.END, html_atual[:10000])
            update_progress(50)  # After filling Response tab

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
            update_progress(50)

            # Initiator Tab (Resources)
            soup_iniciador = BeautifulSoup(html_atual, 'html.parser')
            recursos = []

            # Scripts
            for script in soup_iniciador.find_all('script', src=True):
                recursos.append({
                    'tipo': 'Script',
                    'url': urljoin(url, script.get('src')),
                    'status': 'N/A',
                    'tamanho': 'N/A'
                })

            # CSS (via <link>)
            for link in soup_iniciador.find_all('link', href=True):
                if link.get('rel') and 'stylesheet' in link.get('rel'):
                    recursos.append({
                        'tipo': 'CSS',
                        'url': urljoin(url, link.get('href')),
                        'status': 'N/A',
                        'tamanho': 'N/A'
                    })

            # Images
            for img in soup_iniciador.find_all('img', src=True):
                if not img.get('src').startswith('data:'):
                    recursos.append({
                        'tipo': 'Image',
                        'url': urljoin(url, img.get('src')),
                        'status': 'N/A',
                        'tamanho': 'N/A'
                    })

            # Get status and size of resources
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

            # Format output
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
            update_progress(70)  # After filling Initiator tab

            # URLs Tab (All URLs from the site, including relative and meta content)
            soup_urls = BeautifulSoup(html_atual, 'html.parser')
            urls_encontradas = set()  # Use set to avoid duplicates

            # Tags and attributes that may contain URLs
            tags_atributos = [
                ('a', 'href'),         # Links
                ('img', 'src'),        # Images
                ('script', 'src'),     # Scripts
                ('link', 'href'),      # CSS, favicon, etc.
                ('iframe', 'src'),     # Iframes
                ('source', 'src'),     # Video/audio
                ('video', 'src'),      # Video
                ('audio', 'src'),      # Audio
                ('form', 'action'),    # Forms
                ('object', 'data'),    # Objects
                ('embed', 'src'),      # Embeds
                ('area', 'href'),      # Image maps
                ('track', 'src'),      # Video captions
                ('base', 'href'),      # Base URL
                ('input', 'src'),      # Image inputs
                ('param', 'value'),    # Object parameters
                ('meta', 'content'),   # Meta tags with URLs
            ]

            # Extract URLs from HTML tags
            for tag, attr in tags_atributos:
                for elemento in soup_urls.find_all(tag, {attr: True}):
                    url_encontrada = elemento.get(attr)
                    if url_encontrada and not url_encontrada.startswith('data:'):
                        url_absoluta = urljoin(url, url_encontrada)
                        urls_encontradas.add(url_absoluta)

            # Extract URLs from meta content attributes
            for meta in soup_urls.find_all('meta', content=True):
                content = meta.get('content')
                if content and not content.startswith('data:'):
                    if content.startswith(('http://', 'https://', '/', './', '../')):
                        url_absoluta = urljoin(url, content)
                        urls_encontradas.add(url_absoluta)

            # Format output
            urls_text = ""
            for idx, url_encontrada in enumerate(sorted(urls_encontradas), 1):
                urls_text += f"URL: {idx} {url_encontrada}\n\n"
            aba_urls_texto.delete(1.0, tk.END)
            aba_urls_texto.insert(tk.END, urls_text if urls_text.strip() else "No URLs found on the site or in meta tags.")
            update_progress(80)  # After filling URLs tab

            # Preview Tab (Screenshot)
            screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
            try:
                screen_response = requests.get(screenshot_url, timeout=60)
                screen_response.raise_for_status()
                img_data = BytesIO(screen_response.content)
                img_original = Image.open(img_data)

                # Resize proportionally
                max_width = 1220
                ratio = max_width / img_original.width
                new_height = int(img_original.height * ratio)
                img_exibicao = img_original.resize((max_width, new_height), Image.LANCZOS)

                tk_img = ImageTk.PhotoImage(img_exibicao)

                # Update canvas with scroll
                aba_visualizacao_canvas.delete("all")
                aba_visualizacao_canvas.image = tk_img  # Keep reference
                aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
                aba_visualizacao_canvas.config(scrollregion=(0, 0, max_width, new_height))
                aba_visualizacao_texto.config(text="")
            except Exception as e:
                img_original = None
                aba_visualizacao_canvas.delete("all")
                aba_visualizacao_texto.config(text=f"Screenshot unavailable: {e}")

            update_progress(100)  # Process completed

        except Exception as e:
            update_progress(0)
            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, f"Error: {e}")
            for text_widget in [aba_cabecalhos_texto, aba_resposta_texto, aba_payload_texto, aba_iniciador_texto, aba_urls_texto]:
                text_widget.delete(1.0, tk.END)
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_texto.config(text="Screenshot unavailable.")
            messagebox.showerror("Error", f"Failed to fetch data: {e}")

    # Run in a separate thread to avoid freezing the UI
    threading.Thread(target=run_fetch, daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("Web Scraper")
root.geometry("1200x900")
root.wm_state('zoomed')

frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

label_url = ttk.Label(frame_url, text="Enter the website URL:")
label_url.pack(side='left', padx=(0, 5))

entrada_url = ttk.Entry(frame_url)
entrada_url.pack(side='left', fill='x', expand=True)

botao_buscar = ttk.Button(frame_url, text="Fetch", command=buscar_dados)
botao_buscar.pack(side='left', padx=5)

barra_progresso = ttk.Progressbar(root, length=400, mode='determinate')
barra_progresso.pack(pady=(0, 10))

abas = ttk.Notebook(root)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# General Tab
frame_geral = ttk.Frame(abas)
aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD, width=154, height=52)
aba_geral_texto.pack()
abas.add(frame_geral, text="General")

# Headers Tab
frame_cabecalhos = ttk.Frame(abas)
aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_cabecalhos, wrap=tk.WORD, width=154, height=52)
aba_cabecalhos_texto.pack()
abas.add(frame_cabecalhos, text="Headers")

# Response Tab
frame_resposta = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_resposta, wrap=tk.WORD, width=154, height=52)
aba_resposta_texto.pack()
abas.add(frame_resposta, text="Response")

# Initiator Tab
frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD, width=154, height=52)
aba_iniciador_texto.pack()
abas.add(frame_iniciador, text="Initiator")

# URLs Tab
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, width=155, height=52)
aba_urls_texto.pack()
abas.add(frame_urls, text="URL")

# Payload Tab
frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD, width=154, height=52)
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
aba_salvar_texto = scrolledtext.ScrolledText(frame_salvar, wrap=tk.WORD, width=154, height=40)
aba_salvar_texto.insert(tk.END, "Click the button below to save the full page screenshot in .PNG format.\n\n"
                                "Or click 'Save all images' to download all images present on the website.")
aba_salvar_texto.config(state='disabled')
aba_salvar_texto.pack(pady=10)

botao_salvar = ttk.Button(frame_salvar, text="Save Screenshot", command=salvar_imagem)
botao_salvar.pack(pady=5)

botao_salvar_todas = ttk.Button(frame_salvar, text="Save all website images", command=salvar_todas_imagens)
botao_salvar_todas.pack(pady=5)
abas.add(frame_salvar, text="Save Images")

root.mainloop()
