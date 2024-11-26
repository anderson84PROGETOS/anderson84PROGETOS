import requests
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText  # Importa o ScrolledText
import threading  # Importa a biblioteca de threads
import time  # Importa a biblioteca de tempo

# Cabeçalhos HTTP para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def find_paths(url, wordlist):
    """
    Encontra diretórios ativos em uma URL fornecida usando uma wordlist de caminhos.
    """
    active_paths = []
    output_text.delete(1.0, tk.END)  # Limpar a área de saída
    output_text.insert(tk.END, f"[+] Buscando Subdomain para: {url}\n")
    
    # Configura a barra de progresso
    progress_bar['maximum'] = len(wordlist)
    progress_bar['value'] = 0  # Começar do zero
    root.update_idletasks()  # Atualiza a interface gráfica

    start_time = time.time()  # Marca o tempo de início
    total_time = 0  # Variável para somar o tempo total gasto
    
    for index, path in enumerate(wordlist):
        full_url = f"{url.rstrip('/')}/{path.strip()}"
        try:
            request_start = time.time()  # Marca o tempo de início da requisição
            response = requests.get(full_url, headers=headers, timeout=5)
            request_end = time.time()  # Marca o tempo de término da requisição
            
            if response.status_code == 200:
                output_text.insert(tk.END, f"\n\n[✓] Encontrado: {full_url}")
                active_paths.append(full_url)
            
            # Soma o tempo gasto na requisição atual
            total_time += (request_end - request_start)
        
        except requests.exceptions.RequestException:
            pass  # Ignorar erros de conexão ou tempo esgotado
        
        # Atualiza a barra de progresso
        progress_bar['value'] = index + 1
        root.update_idletasks()  # Atualiza a interface gráfica
        
        # Atualiza o tempo decorrido
        elapsed_time = time.time() - start_time
        elapsed_time_label.config(text=f"Tempo Decorrido: {format_time(elapsed_time)}")
        
        # Estimativa de tempo restante
        if index + 1 > 0:
            avg_time_per_request = total_time / (index + 1)  # Tempo médio por requisição
            remaining_requests = len(wordlist) - (index + 1)
            estimated_remaining_time = avg_time_per_request * remaining_requests
            estimated_remaining_time_label.config(text=f"Tempo Restante: {format_time(estimated_remaining_time)}")
    
    output_text.insert(tk.END, "\n\n\n[+] Busca finalizada.\n")
    return active_paths

def format_time(seconds):
    """Formata o tempo decorrido em minutos e segundos"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

def open_file():
    """
    Abre uma caixa de diálogo para selecionar o arquivo de wordlist.
    """
    file_path = filedialog.askopenfilename(title="Escolha uma wordlist", filetypes=[("Text files", "*.txt")])
    if file_path:
        wordlist_label.config(text=f"Wordlist escolhida: {file_path}")

def start_search():
    """
    Inicia a busca por diretórios com base na URL e na wordlist escolhida.
    """
    url = url_entry.get().strip()
    if not url:
        output_text.insert(tk.END, "Por favor, insira uma URL.\n")
        return
    
    # Certifique-se de que uma wordlist foi escolhida
    if wordlist_label.cget("text") == "Nenhuma wordlist escolhida":
        output_text.insert(tk.END, "Por favor, escolha uma wordlist.\n")
        return
    
    # Lê a wordlist escolhida
    file_path = wordlist_label.cget("text").replace("Wordlist escolhida: ", "")
    with open(file_path, 'r') as file:
        wordlist = file.readlines()

    # Inicia a busca em uma thread separada para não bloquear a GUI
    threading.Thread(target=find_paths, args=(url, wordlist), daemon=True).start()

# Criar a interface gráfica
root = tk.Tk()
root.title("Buscar Subdomain")
root.wm_state('zoomed')

# Layout
frame = tk.Frame(root)
frame.pack(pady=10)

url_label = tk.Label(frame, text="Digite a URL do site (com http:// ou https://)", font=("TkDefaultFont", 11, "bold"))
url_label.grid(pady=5)

url_entry = tk.Entry(frame, width=30, font=("TkDefaultFont", 11, "bold"))
url_entry.grid(pady=5)

search_button = tk.Button(frame, text="Buscar Subdomain", command=start_search, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
search_button.grid(pady=10)

wordlist_button = tk.Button(frame, text="Escolher Wordlist", command=open_file, font=("TkDefaultFont", 11, "bold"), bg='#07edf5')
wordlist_button.grid(pady=10)

wordlist_label = tk.Label(frame, text="Nenhuma wordlist escolhida", font=("TkDefaultFont", 11, "bold"))
wordlist_label.grid(pady=5)

# Barra de progresso
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

# Rótulo para exibir o tempo decorrido
elapsed_time_label = tk.Label(root, text="Tempo Decorrido: 0m 0s", font=("TkDefaultFont", 11, "bold"))
elapsed_time_label.pack(pady=5)

# Rótulo para exibir o tempo restante estimado
estimated_remaining_time_label = tk.Label(root, text="Tempo Restante: 0m 0s", font=("TkDefaultFont", 11, "bold"))
estimated_remaining_time_label.pack(pady=5)

# Caixa de texto rolável para exibição dos resultados
output_text = ScrolledText(root, width=100, height=32, font=("TkDefaultFont", 11, "bold"))
output_text.pack(padx=10, pady=10)

root.mainloop()
