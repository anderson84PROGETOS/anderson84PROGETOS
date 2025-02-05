import requests
import concurrent.futures
from urllib.parse import urljoin
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import threading
from tkinter import ttk

# Cabeçalhos para evitar o erro 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',  # Pode ajudar a evitar bloqueios
}

def fuzz_url(base_url, word, results_text, found_urls, update_progress, selected_statuses):
    url = urljoin(base_url, word.strip())
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        status = response.status_code
        size = len(response.content)

        if status in selected_statuses:
            page_type = (
                "Página Mínima" if size < 1024 else
                "Página Pequena" if size < 10240 else
                "Página Média" if size < 1048576 else
                "Página Normal" if size < 10485760 else
                "Página Grande"
            )
            result = f"{url:<94} Status: {status}, Tamanho: {size / (1024 * 1024):.2f} MB, Tipo: {page_type}"

            # Defina as tags para as cores
            results_text.tag_configure("green", foreground="green")  # Para status 200
            results_text.tag_configure("red", foreground="red")      # Para status 403

            # Condicional para aplicar cor verde para status 200
            if status == 200:
                results_text.insert(tk.END, result + "\n", "green")
            # Condicional para aplicar cor vermelha para status 403
            elif status == 403:
                results_text.insert(tk.END, result + "\n", "red")
            else:
                results_text.insert(tk.END, result + "\n")

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
                with open(filename, 'w') as file:
                    file.write(results_text.get(1.0, tk.END))
                messagebox.showinfo("Resultado", f"Total de URL Encontradas: {len(found_urls)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")

def main():
    found_urls = []
    wordlist_path = None
    fuzz_thread = None
    selected_statuses = set()  # Set to hold selected HTTP statuses
    
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
    
    def toggle_status(status):
        """Toggle the HTTP status in the selected list."""
        if status in selected_statuses:
            selected_statuses.remove(status)
        else:
            selected_statuses.add(status)
        status_label.config(text=f"Status Selecionados: {', '.join(map(str, selected_statuses))}")
    
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
        
        if not selected_statuses:
            messagebox.showerror("Erro", "Selecione pelo menos um status HTTP.")
            return
        
        results_text.delete(1.0, tk.END)
        progress['value'] = 0

        def update_progress():
            progress['value'] += (100 / len(words))
            progress.update()
        
        def fuzz_in_thread():
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(fuzz_url, base_url, word, results_text, found_urls, update_progress, selected_statuses) for word in words]
                    concurrent.futures.wait(futures)
                # Atualize a label de URLs encontradas após o fuzzing
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
    window.title("Dirb Tool")
    window.geometry("1260x950")
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
    
    tk.Label(window, text="Selecione os status HTTP Desejados").pack(pady=5)
    
    # Create buttons for each HTTP status    
    status_frame = tk.Frame(window)
    status_frame.pack(pady=5)

    for status in [200, 301, 302, 403, 404, 429, 500]:
        status_button = tk.Button(status_frame, text=str(status), command=lambda s=status: toggle_status(s), font=("Arial", 10), background='#f5b20a', width=6)
        status_button.pack(side=tk.LEFT, padx=2)
    
    status_label = tk.Label(window, text="Status Selecionados: Nenhum", font=("Arial", 10))
    status_label.pack(pady=5)
    
    start_button = tk.Button(window, text="Iniciar Fuzzing", command=start_fuzzing, font=("Arial", 11, "bold"), background='#00FF00')
    start_button.pack(pady=5)
    
    save_button = tk.Button(window, text="Salvar Resultados", command=lambda: save_results(results_text, found_urls), font=("Arial", 11, "bold"), background='#f5b20a')
    save_button.pack(pady=5)
    
    progress = ttk.Progressbar(window, orient="horizontal", length=400, mode="determinate", style='green.Horizontal.TProgressbar')
    progress.pack(pady=5)
    
    results_text = ScrolledText(window, width=148, height=30)
    results_text.pack(pady=5)

    # Adicionando a label para mostrar o total de URLs encontradas
    total_urls_found_label = tk.Label(window, text="Total de URL Encontradas: 0", font=("Arial", 12, "bold"))
    total_urls_found_label.pack(pady=5)
    
    window.mainloop()

if __name__ == "__main__":
    main()
