import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
import warnings
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext, ttk
import os
import threading

warnings.simplefilter("ignore")

global_count = 1  # Global counter for PDF found

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

PDF_HEADERS = {
    'User-Agent': HEADERS['User-Agent'],
    'Accept': 'application/pdf, application/x-pdf, application/vnd.adobe.xfdf, image/jpeg, image/png, image/tiff, image/pjpeg, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def find_resources_urls(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
    except:
        return set(), set(), set(), set(), set(), set(), set()
    soup = BeautifulSoup(response.content, 'html.parser')
    js_urls = set(urljoin(url, s['src']) for s in soup.find_all('script', src=True))
    css_urls = set(urljoin(url, l['href']) for l in soup.find_all('link', href=True))
    img_urls = set(urljoin(url, i['src']) for i in soup.find_all('img', src=True))
    ico_urls = set()
    favicon = soup.find('link', rel='icon')
    if favicon:
        ico_urls.add(urljoin(url, favicon.get('href','')))
    php_urls = set()
    other_urls = set()
    pdf_urls = set()
    for a in soup.find_all('a', href=True):
        full_url = urljoin(url, a['href'])
        if full_url.endswith('.php'):
            php_urls.add(full_url)
        elif full_url.endswith('.pdf'):
            pdf_urls.add(full_url)
        elif full_url.startswith(('http://', 'https://')):
            other_urls.add(full_url)
    return js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls

def fetch_pdfs_from_urls(starting_urls, max_pdfs=10, progress_bar=None):
    urls = deque(starting_urls)
    scrapped_urls = set()
    pdf_urls = set()
    total = 0
    while urls and (len(pdf_urls) < max_pdfs or max_pdfs == float('inf')):
        url = urls.popleft()
        if url in scrapped_urls:
            continue
        scrapped_urls.add(url)
        try:
            response = requests.get(url, headers=PDF_HEADERS, timeout=5)
            response.raise_for_status()
        except:
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup.find_all("a", href=True):
            full_url = urljoin(url, tag["href"])
            if full_url.endswith(".pdf") and full_url not in pdf_urls:
                pdf_urls.add(full_url)
            elif full_url.startswith(("http://", "https://")) and full_url not in scrapped_urls:
                urls.append(full_url)
        total += 1
        if progress_bar:
            progress_bar['value'] = total
            progress_bar.update()
    return pdf_urls

def download_file(url, folder_path):
    try:
        filename = os.path.join(folder_path, url.split("/")[-1])
        response = requests.get(url, stream=True, headers=PDF_HEADERS)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except:
        pass

def save_files_thread(urls, folder_path):
    progress['maximum'] = len(urls)
    progress['value'] = 0
    for url in urls:
        download_file(url, folder_path)
        progress['value'] += 1
        progress.update()
    messagebox.showinfo("Sucesso", f"{len(urls)} arquivos baixados em: {folder_path}")

def baixar_arquivos_selecionados():
    # Seleção de linhas do ScrolledText
    selected_text = result_text.tag_ranges("sel")
    if not selected_text:
        messagebox.showwarning("Aviso", "Selecione ao menos um link")
        return
    folder_path = filedialog.askdirectory(title="Selecione a pasta para salvar os arquivos")
    if not folder_path:
        return
    # Pegar linhas selecionadas
    urls = []
    for i in range(0, len(selected_text), 2):
        start = selected_text[i]
        end = selected_text[i+1]
        selected_lines = result_text.get(start, end).splitlines()
        for line in selected_lines:
            line = line.strip()
            if line.startswith("http"):
                urls.append(line)
    threading.Thread(target=save_files_thread, args=(urls, folder_path), daemon=True).start()

def adicionar_lista(titulo, urls):
    result_text.insert(tk.END, f"\n{titulo} = {len(urls)}\n\n")
    for u in urls:
        result_text.insert(tk.END, u + "\n")

def buscar_recursos_thread(url, max_pdfs):
    progress['value'] = 0
    js_urls, css_urls, img_urls, ico_urls, php_urls, other_urls, pdf_urls = find_resources_urls(url)
    pdf_urls = pdf_urls.union(fetch_pdfs_from_urls([url], max_pdfs, progress))
    result_text.config(state='normal')
    result_text.delete(1.0, tk.END)
    adicionar_lista("JavaScript", js_urls)
    adicionar_lista("CSS", css_urls)
    adicionar_lista("Imagens", img_urls)
    adicionar_lista("Ícones/Favicon", ico_urls)
    adicionar_lista("PHP", php_urls)
    adicionar_lista("Outros Links", other_urls)
    adicionar_lista("PDF", pdf_urls)
    result_text.config(state='disabled')
    progress['value'] = 100

def iniciar_busca():
    url = entry_url.get().strip()
    if not url.startswith(('http:', 'https:')):
        url = 'http://' + url
    max_pdfs_input = entry_max_pdfs.get().strip()
    max_pdfs = int(max_pdfs_input) if max_pdfs_input else float('inf')    
    threading.Thread(target=buscar_recursos_thread, args=(url, max_pdfs), daemon=True).start()    

# GUI
root = tk.Tk()
root.title("Web Resource Collector")
root.geometry("900x700")
root.state('zoomed')

tk.Label(root, text="Digite a URL do website", font=('Arial', 12)).pack(pady=5)
entry_url = tk.Entry(root, width=35, font=('Arial', 12))
entry_url.pack(pady=5)

tk.Button(root, text="Buscar Recursos", command=iniciar_busca, bg="lightblue").pack(pady=5)
tk.Button(root, text="Baixar Arquivos Selecionados", command=baixar_arquivos_selecionados, bg="lightgreen").pack(pady=5)

# Novo campo para quantidade de PDFs
tk.Label(root, text="Quantos PDF Deseja buscar acima de 80 Ele Traz Maximo de PDF TIPO 100 = 1575 PDF", font=('Arial', 12)).pack(pady=5)
entry_max_pdfs = tk.Entry(root, width=10, font=('Arial', 12))
entry_max_pdfs.pack(pady=5)

tk.Label(root, text="Resultados Encontrados").pack(pady=5)

progress = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
progress.pack(pady=10)

# Aqui está o ScrolledText
result_text = scrolledtext.ScrolledText(root, width=165, height=38, font=('Arial', 10))
result_text.pack(pady=5)

root.mainloop()
