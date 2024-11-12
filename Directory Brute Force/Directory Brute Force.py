import requests
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from threading import Thread

# Cabeçalhos HTTP personalizados para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def directory_brute_force(url, wordlist):
    found_directories = []

    # Adiciona '/' ao final da URL caso não tenha
    if not url.endswith('/'):
        url += '/'

    output_text.insert(tk.END, f"Iniciando busca de Diretórios Em: {url}\n\n")

    try:
        with open(wordlist, 'r') as file:
            directories = file.readlines()
            total_directories = len(directories)
            progress_bar['maximum'] = total_directories  # Define o valor máximo da barra de progresso

            for count, line in enumerate(directories, start=1):
                directory = line.strip()
                target_url = url + directory

                try:
                    # Adiciona os headers à requisição
                    response = requests.get(target_url, headers=headers)
                    
                    # Se o código de status é 200, o diretório existe
                    if response.status_code == 200:
                        found_directories.append(target_url)
                        output_text.insert(tk.END, f"Diretório Encontrado: {target_url}\n")

                except requests.RequestException as e:
                    output_text.insert(tk.END, f"Erro ao acessar {target_url}: {e}\n")

                # Atualiza a barra de progresso
                progress_bar['value'] = count
                count_label.config(text=f"{count}/{total_directories} diretórios verificados")
                root.update_idletasks()  # Atualiza a interface gráfica

        output_text.insert(tk.END, "Busca concluída.\n")
        messagebox.showinfo("Busca Concluída", "A busca de diretórios foi concluída!")
    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo wordlist não encontrado.")

    return found_directories

def select_wordlist():
    global wordlist_path
    wordlist_path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Selecione o arquivo wordlist",
                                               filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if wordlist_path:
        wordlist_label.config(text=f"Wordlist selecionada: {os.path.basename(wordlist_path)}")

def start_brute_force_thread():
    url = url_entry.get()
    if url and wordlist_path:
        output_text.delete(1.0, tk.END)  # Limpa a saída
        progress_bar['value'] = 0  # Reinicia a barra de progresso
        # Cria e inicia um thread para a função directory_brute_force
        brute_force_thread = Thread(target=directory_brute_force, args=(url, wordlist_path))
        brute_force_thread.start()
    else:
        messagebox.showwarning("Entrada Inválida", "Por favor, insira uma URL e selecione uma wordlist.")

# Configuração da interface gráfica (Tkinter)
root = tk.Tk()
root.title("Directory Brute Force")
root.geometry("950x910")
root.wm_state('zoomed')

# Entrada para URL
tk.Label(root, text="Digite a URL do Website", font=("TkDefaultFont", 12)).pack(pady=5)
url_entry = tk.Entry(root, width=35, font=("TkDefaultFont", 12))
url_entry.pack(pady=5)

# Botão para seleção de arquivo wordlist
wordlist_label = tk.Label(root, text="Nenhuma wordlist selecionada", font=("TkDefaultFont", 10))
wordlist_label.pack(pady=5)
wordlist_button = tk.Button(root, text="Selecionar Wordlist", command=select_wordlist, font=("TkDefaultFont", 11, "bold"))
wordlist_button.pack(pady=5)

# Botão para iniciar brute force
start_button = tk.Button(root, text="Iniciar Busca", command=start_brute_force_thread, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
start_button.pack(pady=10)

# Barra de progresso
progress_bar = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
progress_bar.pack(pady=5)
count_label = tk.Label(root, text="0/0 diretórios verificados", font=("TkDefaultFont", 10))
count_label.pack()

# Área de texto para saída
output_text = scrolledtext.ScrolledText(root, width=100, height=35, font=("TkDefaultFont", 11))
output_text.pack(padx=10, pady=10)

# Caminho inicial do arquivo wordlist
wordlist_path = ""

# Inicia o loop da interface gráfica
root.mainloop()
