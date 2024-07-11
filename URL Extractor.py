import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import re

def get_all_urls(base_url, method):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.request(method, base_url, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx or 5xx)
    except requests.RequestException as e:
        messagebox.showerror("HTTP Error", f"Error with {method} request: {e}")
        return set()

    soup = BeautifulSoup(response.content, 'html.parser')
    
    urls = set()
    
    # Busca por tags que podem conter URLs
    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        url = tag.get('href') or tag.get('src')
        if url:
            full_url = urljoin(base_url, url)
            urls.add(full_url)
    
    # Busca por atributos específicos 'href' e 'content' que começam com 'http' ou 'https'
    for tag in soup.find_all(True, {'href': lambda x: x and x.startswith(('http://', 'https://')), 'content': lambda x: x and (x.startswith('http://') or x.startswith('https://'))}):
        url = tag.get('href') or tag.get('content')
        if url:
            urls.add(url)
    
    # Extração de URLs do atributo 'content'
    content_urls = re.findall(r'(?<=content=["\'])https?://[^"\']+|(?<=content=["\'])[^"\']+', response.text)
    for content_url in content_urls:
        normalized_url = normalize_url(content_url, base_url)
        if normalized_url:
            urls.add(normalized_url)
    
    return urls

def fetch_urls(method):
    base_url = url_entry.get()
    if not base_url:
        messagebox.showwarning("Input Error", "Please enter a website URL.")
        return

    urls = get_all_urls(base_url, method)
    if urls:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "\n".join(urls))
    else:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "No URLs found.")

def save_to_file():
    urls = result_text.get(1.0, tk.END)
    if not urls.strip():
        messagebox.showwarning("Save Error", "No data to save.")
        return
    
    # Abrir caixa de diálogo para salvar arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(urls)
        messagebox.showinfo("Save Success", f"Results saved to {file_path}")

def create_gui():
    global url_entry, result_text
    
    root = tk.Tk()
    root.title("URLExtractor")
    root.wm_state('zoomed')  # Definindo uma geometria inicial para a janela

    label_instruction = tk.Label(root, text="Digite a URL do website", font=("TkDefaultFont", 12, "bold"))
    label_instruction.pack(pady=5)

    url_entry = tk.Entry(root, width=35, font=("TkDefaultFont", 11, "bold"))
    url_entry.pack(pady=5)

    methods_frame = tk.Frame(root)
    methods_frame.pack(pady=10)    

    method_buttons = ["Executar"]
    for method in method_buttons:
        button = tk.Button(methods_frame, text=method, command=lambda m="GET": fetch_urls(m), bg="#0af28d", font=("TkDefaultFont", 11, "bold"))
        button.pack(side=tk.LEFT, padx=5)

    button_save = tk.Button(root, text="Salvar Resultados", command=save_to_file, bg="#07f5ed", font=("TkDefaultFont", 11, "bold"))
    button_save.pack(pady=10)

    result_text = scrolledtext.ScrolledText(root, width=130, height=38, font=("TkDefaultFont", 12, "bold"))
    result_text.pack(pady=10)

    root.mainloop()

def normalize_url(url, base_url):
    # Implemente a normalização da URL conforme necessário
    return urljoin(base_url, url)

if __name__ == "__main__":
    create_gui()
