import requests
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText  # Importa o ScrolledText

import threading  # Importa a biblioteca de threads

# Cabeçalhos HTTP para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def find_subdomains(domain, wordlist):
    """
    Encontra subdomínios ativos de um domínio fornecido usando uma wordlist.
    """
    active_subdomains = []
    output_text.delete(1.0, tk.END)  # Limpar a área de saída
    output_text.insert(tk.END, f"[+] Buscando subdomínios para: {domain}\n")
    
    # Configura a barra de progresso
    progress_bar['maximum'] = len(wordlist)
    progress_bar['value'] = 0  # Começar do zero
    root.update_idletasks()  # Atualiza a interface gráfica

    for index, sub in enumerate(wordlist):
        subdomain = f"http://{sub.strip()}.{domain}"
        try:
            response = requests.get(subdomain, headers=headers, timeout=5)
            if response.status_code == 200:
                output_text.insert(tk.END, f"\n\n[✓] Ativo: {subdomain}")
                active_subdomains.append(subdomain)
        except requests.exceptions.RequestException:
            pass  # Ignorar erros de conexão ou tempo esgotado
        
        # Atualiza a barra de progresso
        progress_bar['value'] = index + 1
        root.update_idletasks()  # Atualiza a interface gráfica

    output_text.insert(tk.END, "\n\n\n[+] Busca finalizada.\n")
    return active_subdomains

def open_file():
    """
    Abre uma caixa de diálogo para selecionar o arquivo de wordlist.
    """
    file_path = filedialog.askopenfilename(title="Escolha uma wordlist", filetypes=[("Text files", "*.txt")])
    if file_path:
        wordlist_label.config(text=f"Wordlist escolhida: {file_path}")

def start_search():
    """
    Inicia a busca por subdomínios com base no domínio e na wordlist escolhida.
    """
    domain = domain_entry.get().strip()
    if not domain:
        output_text.insert(tk.END, "Por favor, insira um domínio.\n")
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
    threading.Thread(target=find_subdomains, args=(domain, wordlist), daemon=True).start()

# Criar a interface gráfica
root = tk.Tk()
root.title("Subdomain Finder")
root.wm_state('zoomed')

# Layout
frame = tk.Frame(root)
frame.pack(pady=10)

domain_label = tk.Label(frame, text="Digite o domínio", font=("TkDefaultFont", 11, "bold"))
domain_label.grid(pady=5)

domain_entry = tk.Entry(frame, width=30, font=("TkDefaultFont", 11, "bold"))
domain_entry.grid(pady=5)

search_button = tk.Button(frame, text="Buscar Subdomínios", command=start_search, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
search_button.grid(pady=10)

wordlist_button = tk.Button(frame, text="Escolher Wordlist", command=open_file, font=("TkDefaultFont", 11, "bold"), bg='#07edf5')
wordlist_button.grid(pady=10)

wordlist_label = tk.Label(frame, text="Nenhuma wordlist escolhida", font=("TkDefaultFont", 11, "bold"))
wordlist_label.grid(pady=5)

# Barra de progresso
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

# Caixa de texto rolável para exibição dos resultados
output_text = ScrolledText(root, width=100, height=35, font=("TkDefaultFont", 11, "bold"))
output_text.pack(padx=10, pady=10)

root.mainloop()
