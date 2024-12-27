import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar
import requests
from urllib.parse import urljoin
import threading
from concurrent.futures import ThreadPoolExecutor

def scan():
    url = url_entry.get()
    wordlist_file = wordlist_path.get()

    if not url or not wordlist_file:
        messagebox.showerror("Erro", "URL ou wordlist não fornecidos.")
        return

    try:
        with open(wordlist_file, "r", encoding="utf-8") as file:
            wordlist = [word.strip() for word in file.read().splitlines() if word.strip()]
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar a wordlist: {e}")
        return

    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, f"Scanning: {url}\n\n")

    total_words = len(wordlist)
    progress_bar["maximum"] = total_words

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'application/json'
    }

    found_directories = 0  # Contador de diretórios encontrados

    def check_directory(word):
        nonlocal found_directories  # Permite modificar a variável encontrada dentro da função
        path = urljoin(url.rstrip("/"), word.lstrip("/"))
        try:
            response = requests.get(path, headers=headers, timeout=3)  # Timeout reduzido para acelerar
            if response.status_code == 200:
                found_directories += 1  # Incrementa o contador quando encontra um diretório
                text_widget.insert(tk.END, f"DIRETÓRIO: {path}\n")
        except requests.RequestException:
            pass
        progress_bar["value"] = progress_bar["value"] + 1
        root.update_idletasks()

    with ThreadPoolExecutor(max_workers=20) as executor:  # Usando até 20 threads simultâneas
        for word in wordlist:
            executor.submit(check_directory, word)

    text_widget.insert(tk.END, f"\nScan completo!   Diretórios Encontrados: {found_directories}")
    progress_bar["value"] = total_words

def start_scan_thread():
    scan_thread = threading.Thread(target=scan)
    scan_thread.start()

def select_wordlist():
    filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if filepath:
        wordlist_path.set(filepath)

root = tk.Tk()
root.title("Dirb Scanner")
root.geometry("700x600")

frame = tk.Frame(root, pady=5, padx=10)
frame.pack(fill=tk.BOTH, expand=True)

url_label = tk.Label(frame, text="Digite a URL do website", font=("Arial", 11))
url_label.pack(pady=5)
url_entry = tk.Entry(frame, width=40)
url_entry.pack(pady=5)

wordlist_label = tk.Label(frame, text="Wordlist", font=("Arial", 11))
wordlist_label.pack(pady=5)
wordlist_path = tk.StringVar()
wordlist_entry = tk.Entry(frame, textvariable=wordlist_path, width=40)
wordlist_entry.pack(pady=5)

select_button = tk.Button(frame, text="Selecionar Wordlist", command=select_wordlist, width=20)
select_button.pack(pady=5)

scan_button = tk.Button(frame, text="Scan", command=start_scan_thread, bg="green", fg="white", font=("Arial", 12), width=15)
scan_button.pack(pady=5)

progress_bar = Progressbar(frame, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=50, font=("Arial", 11))
text_widget.pack(pady=60)

root.mainloop()
