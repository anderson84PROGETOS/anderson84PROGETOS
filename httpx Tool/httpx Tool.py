import requests
import concurrent.futures
from urllib.parse import urljoin
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import threading
from tkinter import ttk
import socket
from bs4 import BeautifulSoup  # Necessário instalar: pip install beautifulsoup4

# Cabeçalhos para evitar o erro 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
}

def get_ip_from_url(url):
    """Obtém o IP do domínio da URL."""
    try:
        domain = url.split("://")[1].split("/")[0]
        ip = socket.gethostbyname(domain)
        return ip
    except:
        return "IP não resolvido"

def fuzz_url(base_url, word, results_text, found_urls, update_progress):
    url = urljoin(base_url, word.strip())
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        status = response.status_code
        size = len(response.content)

        # Filtrar apenas status 200
        if status == 200:
            # Obter informações adicionais
            ip = get_ip_from_url(url)
            server = response.headers.get("Server", "N\D")

            # Verificar se o conteúdo é HTML antes de parsear
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string.strip() if soup.title else "Sem título"
            else:
                title = "Conteúdo não HTML"

            # Calcular o tamanho em MB
            size_mb = size / (1024 * 1024)
              
            # Formatar a saída
            result = f"{url:<42}[IP:{ip}] TAM:{size_mb:.2f} MB,[Serv:{server}][Ti:{title}]\n\n"

            # Definir tag para cor verde
            results_text.tag_configure("#53fa05", foreground="#53fa05")

            # Exibir em verde
            results_text.insert(tk.END, result, "#53fa05")

            results_text.yview(tk.END)
            found_urls.append(url)
    except requests.RequestException:
        pass
    update_progress()

def save_results(results_text, found_urls):
    save_choice = messagebox.askyesno("Salvar Resultados", "Deseja salvar os resultados?")
    if save_choice:
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(results_text.get(1.0, tk.END))
                messagebox.showinfo("Resultado", f"Total de URL Encontradas: {len(found_urls)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")

def main():
    found_urls = []
    wordlist_path = None
    fuzz_thread = None

    def select_wordlist():
        nonlocal wordlist_path
        wordlist_path = filedialog.askopenfilename(title="Selecione o arquivo wordlist", filetypes=[("Text Files", "*.txt")])
        if wordlist_path:
            try:
                with open(wordlist_path, 'r') as file:
                    words = file.read().splitlines()
                word_count_label.config(text=f"Palavras na Wordlist: {len(words)}       WordList: {os.path.basename(wordlist_path)}")
            except:
                messagebox.showerror("Erro", "Ocorreu um erro ao carregar o wordlist.")
                return

    def start_fuzzing():
        if not wordlist_path:
            messagebox.showerror("Erro", "Nenhum arquivo wordlist selecionado.")
            return
        base_url = url_entry.get().strip()
        if not base_url.endswith("/FUZZ"):
            base_url = base_url.rstrip("/") + "/FUZZ"

        try:
            with open(wordlist_path, 'r') as file:
                words = file.read().splitlines()
        except:
            messagebox.showerror("Erro", "Ocorreu um erro ao carregar o wordlist.")
            return

        results_text.delete(1.0, tk.END)
        progress['value'] = 0

        def update_progress():
            progress['value'] += (100 / len(words))
            progress.update()

        def fuzz_in_thread():
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(fuzz_url, base_url, word, results_text, found_urls, update_progress) for word in words]
                    concurrent.futures.wait(futures)
                total_urls_found_label.config(text=f"Total de URL Encontradas: {len(found_urls)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            progress['value'] = 100
            start_button.config(state=tk.NORMAL)

        start_button.config(state=tk.DISABLED)
        nonlocal fuzz_thread
        fuzz_thread = threading.Thread(target=fuzz_in_thread)
        fuzz_thread.daemon = True
        fuzz_thread.start()

    def on_close():
        if fuzz_thread is not None and fuzz_thread.is_alive():
            fuzz_thread.join()
        window.destroy()

    window = tk.Tk()
    window.title("httpx Tool")
    window.geometry("1285x980")
    window.protocol("WM_DELETE_WINDOW", on_close)

    style = ttk.Style()
    style.theme_use('default')
    style.configure('green.Horizontal.TProgressbar', background='#00FF00')

    tk.Label(window, text="Digite a URL base (ex: https://example.com)").pack(pady=5)
    url_entry = tk.Entry(window, width=50, font=("Arial", 11, "bold"))
    url_entry.pack(pady=5)

    select_wordlist_button = tk.Button(window, text="Selecionar Wordlist", command=select_wordlist, font=("Arial", 11, "bold"), background='#0ae1f5')
    select_wordlist_button.pack(pady=5)

    word_count_label = tk.Label(window, text="Palavras na Wordlist: Nenhuma", font=("Arial", 11, "bold"), background='#03fcc6')
    word_count_label.pack(pady=5)

    start_button = tk.Button(window, text="Iniciar Fuzzing", command=start_fuzzing, font=("Arial", 11, "bold"), background='#00FF00')
    start_button.pack(pady=5)

    save_button = tk.Button(window, text="Salvar Resultados", command=lambda: save_results(results_text, found_urls), font=("Arial", 11, "bold"), background='#f5b20a')
    save_button.pack(pady=5)

    progress = ttk.Progressbar(window, orient="horizontal", length=400, mode="determinate", style='green.Horizontal.TProgressbar')
    progress.pack(pady=5)

    total_urls_found_label = tk.Label(window, text="Total de URL Encontradas: 0", font=("Arial", 12, "bold"))
    total_urls_found_label.pack(pady=5)

    results_text = ScrolledText(window, width=155, height=38, background='#0a0a0a')
    results_text.pack(pady=5)    

    window.mainloop()

if __name__ == "__main__":
    main()
