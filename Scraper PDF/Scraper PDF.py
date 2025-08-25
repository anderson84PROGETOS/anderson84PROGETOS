import requests
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import re

# ====== Headers globais reutilizados em scraping e download ======
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
    return name or 'arquivo.pdf'

def filename_from_response(response, url: str) -> str:
    cd = response.headers.get('Content-Disposition', '')
    match = re.search(r"filename\*=(?:UTF-8'')?([^;\n]+)", cd)
    if match:
        fname = match.group(1)
    else:
        match = re.search(r'filename="?([^";]+)"?', cd)
        fname = match.group(1) if match else ''

    if not fname:
        fname = os.path.basename(url.split('?')[0])

    if not fname.lower().endswith('.pdf'):
        fname += '.pdf'

    return sanitize_filename(fname)

def process_url(user_url, max_pdfs, progress_callback):
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url

    urls = deque([user_url])
    scrapped_urls = []

    while urls and len(scrapped_urls) < max_pdfs:
        url = urls.popleft()
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            continue

        if url.lower().endswith('.pdf'):
            if url not in scrapped_urls:
                scrapped_urls.append(url)
                progress_callback(len(scrapped_urls), max_pdfs)
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(url, tag['href'])
            if full_url.startswith(('http://', 'https://')) and full_url not in scrapped_urls:
                if full_url.lower().endswith('.pdf'):
                    scrapped_urls.append(full_url)
                    progress_callback(len(scrapped_urls), max_pdfs)
                    if len(scrapped_urls) >= max_pdfs:
                        break
                urls.append(full_url)

    return scrapped_urls

def start_scraping_thread():
    threading.Thread(target=start_scraping, daemon=True).start()

def start_scraping():
    global found_pdfs
    user_url = url_entry.get().strip()
    try:
        max_pdfs = int(pdf_count_entry.get())
    except ValueError:
        messagebox.showerror('Erro', 'Digite um número válido para a quantidade de PDF')
        return

    if not user_url:
        messagebox.showerror('Erro', 'Digite uma URL válida!')
        return

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, 'Escaneando... Aguarde.\n')
    root.update()

    progress_bar['value'] = 0
    progress_bar['maximum'] = max_pdfs

    def update_progress(current, total):
        progress_bar['value'] = current
        root.update_idletasks()

    found_pdfs = process_url(user_url, max_pdfs, update_progress)

    result_text.delete(1.0, tk.END)
    if found_pdfs:
        for i, pdf in enumerate(found_pdfs, start=1):
            result_text.insert(tk.END, f"{i} = {pdf}\n\n")
        messagebox.showinfo('Concluído', f'Foram Encontrados: {len(found_pdfs)} PDF')
    else:
        result_text.insert(tk.END, 'Nenhum PDF Encontrado.')

def save_results():
    content = result_text.get(1.0, tk.END).strip()
    if not content:
        messagebox.showwarning('Aviso', 'Nenhum resultado para salvar!')
        return

    file_path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Arquivos de Texto', '*.txt')])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        messagebox.showinfo('Salvo', f'Resultados salvos em: {file_path}')

def download_pdfs_thread():
    threading.Thread(target=download_pdfs, daemon=True).start()

def download_pdfs():
    if not found_pdfs:
        messagebox.showwarning('Aviso', 'Nenhum PDF para baixar!')
        return

    folder = filedialog.askdirectory(title='Escolha a pasta para salvar os PDF')
    if not folder:
        return

    session = requests.Session()
    session.headers.update(HEADERS)

    ok, fail = 0, 0
    progress_bar['value'] = 0
    progress_bar['maximum'] = len(found_pdfs)

    for idx, url in enumerate(found_pdfs, start=1):
        try:
            parsed = urlparse(url)
            base_referer = f"{parsed.scheme}://{parsed.netloc}/"
            alt_referer = f"{parsed.scheme}://{parsed.netloc}{os.path.dirname(parsed.path)}/"

            resp = session.get(url, headers={"Referer": base_referer}, stream=True, timeout=30)
            if resp.status_code == 403:
                resp = session.get(url, headers={"Referer": alt_referer}, stream=True, timeout=30)
            resp.raise_for_status()

            filename = filename_from_response(resp, url)
            filepath = os.path.join(folder, filename)

            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024*64):
                    if chunk:
                        f.write(chunk)

            ok += 1
            result_text.insert(tk.END, f"\n✔ Baixado: {filename}\n")
        except Exception as e:
            fail += 1
            result_text.insert(tk.END, f"\n\n✖ Erro ao baixar {url}: {e}\n")

        progress_bar['value'] = idx
        result_text.see(tk.END)
        root.update_idletasks()

    messagebox.showinfo('Download Concluído', f"Sucesso: {ok} | Falhas: {fail}\nPasta: {folder}")

# ==== GUI Tkinter ====
root = tk.Tk()
root.title('PDF Scraper')
root.geometry("1250x900")
# Maximizar janela
root.state('zoomed')

frame = tk.Frame(root)
frame.pack(pady=5)

# Usando grid para todos os widgets dentro do frame
tk.Label(frame, text='Digite a URL do website', font=('Arial', 11, 'bold')).grid(pady=5)
url_entry = tk.Entry(frame, width=40, font=('Arial', 11, 'bold'))
url_entry.grid(pady=5)

tk.Label(frame, text='Número máximo de PDF', font=('Arial', 11, 'bold')).grid(pady=5)
pdf_count_entry = tk.Entry(frame, width=10, font=('Arial', 11, 'bold'))
pdf_count_entry.grid( pady=5)

start_button = tk.Button(frame, text='Iniciar Busca', bg="#03fc24", fg="black", command=start_scraping_thread)
start_button.grid(pady=5)

save_button = tk.Button(frame, text='Salvar Resultados', bg="#f5b342", fg="black", command=save_results)
save_button.grid(pady=5)

download_button = tk.Button(frame, text='Baixar PDF', bg="#08fbff", fg="black", command=download_pdfs_thread)
download_button.grid(pady=5)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress_bar.pack(pady=5)

result_text = scrolledtext.ScrolledText(root, width=128, height=30, font=('Arial', 12, 'bold'))
result_text.pack(pady=5)

found_pdfs = []

root.mainloop()
