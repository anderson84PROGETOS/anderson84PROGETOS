import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
from urllib.parse import urlparse, urljoin
import socket
import subprocess
from bs4 import BeautifulSoup
import threading
import re

# Custom headers for requests
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

html_atual = ""  # Store current HTML for extracting URLs

def update_progress(value):
    """Update the progress bar."""
    barra_progresso['value'] = value
    root.update_idletasks()

def get_server_name(url):
    """Fetch the server name using curl -I with custom User-Agent."""
    try:
        curl_command = [
            'curl', '-I',
            '-A', headers_customizados['User-Agent'],
            url
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=15)
        output = result.stdout
        server_match = re.search(r'^Server:\s*(.+)$', output, re.MULTILINE | re.IGNORECASE)
        if server_match:
            return server_match.group(1).strip()
        return 'Unknown'
    except (subprocess.SubprocessError, Exception) as e:
        print(f"Error running curl: {e}")
        return 'Unknown'

def salvar_tudo():
    """Save contents of General, Headers, and URL tabs to a .txt file."""
    try:
        caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not caminho:
            return

        geral_content = aba_geral_texto.get(1.0, tk.END).strip()
        cabecalhos_content = aba_cabecalhos_texto.get(1.0, tk.END).strip()
        urls_content = aba_urls_texto.get(1.0, tk.END).strip()

        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("=== General ===\n\n")
            f.write(geral_content + "\n\n")
            f.write("\n=== Headers ===\n\n")
            f.write(cabecalhos_content + "\n\n")
            f.write("\n=== URL ===\n\n")
            f.write(urls_content)

        messagebox.showinfo("Success", f"Dados salvos em: {caminho}")
    except Exception as e:
        messagebox.showerror("Error", f"Falha ao salvar o arquivo: {e}")

def buscar_dados():
    """Fetch website data and update tabs."""
    def run_fetch():
        global html_atual
        url = entrada_url.get()
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

            update_progress(20)

            server_name = get_server_name(url)

            resposta = requests.get(url, headers=headers_customizados, timeout=15)
            resposta.raise_for_status()

            # General Tab
            geral_texto = (
                f"Request URL: {resposta.url}\n"
                f"\nRemote Address: {ip}:{porta}\n"
                f"\nRequest Method: {resposta.request.method}\n"
                f"\nStatus Code: {resposta.status_code} {resposta.reason}\n"
                f"\nServer: {server_name}\n"
                f"\nReferrer Policy: origin"
            )
            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, geral_texto)
            update_progress(30)

            # Headers Tab
            cabecalhos_texto = "\n".join(f"{k}: {v}" for k, v in resposta.headers.items())
            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos_texto)
            update_progress(40)

            # URLs Tab
            html_atual = resposta.text
            soup_urls = BeautifulSoup(html_atual, 'html.parser')
            urls_encontradas = set()

            tags_atributos = [
                ('a', 'href'), ('img', 'src'), ('script', 'src'), ('link', 'href'),
                ('iframe', 'src'), ('source', 'src'), ('video', 'src'), ('audio', 'src'),
                ('form', 'action'), ('object', 'data'), ('embed', 'src'), ('area', 'href'),
                ('track', 'src'), ('base', 'href'), ('input', 'src'), ('param', 'value'),
                ('meta', 'content')
            ]

            for tag, attr in tags_atributos:
                for elemento in soup_urls.find_all(tag, {attr: True}):
                    url_encontrada = elemento.get(attr)
                    if url_encontrada and not url_encontrada.startswith('data:'):
                        url_absoluta = urljoin(url, url_encontrada)
                        urls_encontradas.add(url_absoluta)

            for meta in soup_urls.find_all('meta', content=True):
                content = meta.get('content')
                if content and not content.startswith('data:'):
                    if content.startswith(('http://', 'https://', '/', './', '../')):
                        url_absoluta = urljoin(url, content)
                        urls_encontradas.add(url_absoluta)

            urls_text = ""
            for idx, url_encontrada in enumerate(sorted(urls_encontradas), 1):
                urls_text += f"{idx} = {url_encontrada}\n\n"
            aba_urls_texto.delete(1.0, tk.END)
            aba_urls_texto.insert(tk.END, urls_text if urls_text.strip() else "No URLs found on the site or in meta tags.")
            update_progress(80)

            update_progress(100)

        except Exception as e:
            update_progress(0)
            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, f"Error: {e}")
            for text_widget in [aba_cabecalhos_texto, aba_urls_texto]:
                text_widget.delete(1.0, tk.END)
            messagebox.showerror("Error", f"Failed to fetch data: {e}")

    threading.Thread(target=run_fetch, daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("Scraper Website")
root.geometry("1200x900")
root.wm_state('zoomed')

frame_url = ttk.Frame(root)
frame_url.pack(pady=5)

label_url = ttk.Label(frame_url, text="Digite a url do website")
label_url.pack(pady=5)

entrada_url = ttk.Entry(frame_url, width=40, font=("Arial", 11))
entrada_url.pack(pady=5)

# Create a custom style for buttons
style = ttk.Style()
style.configure('Custom.TButton', background='#0bfc03', foreground='black')

# Buscar button
botao_buscar = ttk.Button(root, text="Buscar", style='Custom.TButton', command=buscar_dados)
botao_buscar.pack(pady=5)

# Salvar Tudo button
botao_salvar_tudo = ttk.Button(root, text="Salvar Tudo", style='Custom.TButton', command=salvar_tudo)
botao_salvar_tudo.pack(pady=5)

barra_progresso = ttk.Progressbar(root, length=400, mode='determinate')
barra_progresso.pack(pady=(0, 10))

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

# URLs Tab
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, width=154, height=45)
aba_urls_texto.pack()
abas.add(frame_urls, text="URL")

root.mainloop()
