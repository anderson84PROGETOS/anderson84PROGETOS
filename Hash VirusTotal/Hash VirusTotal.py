import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import webbrowser

def calculate_all_hashes(file_path):
    """Calcula todos os hashes suportados (MD5, SHA1, SHA256, SHA512)."""
    hash_types = ["md5", "sha1", "sha256"]
    results = {}
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            for hash_type in hash_types:
                hash_func = hashlib.new(hash_type)
                hash_func.update(data)
                results[hash_type] = hash_func.hexdigest()
        return results
    except Exception as e:
        return {"Erro": f"Erro ao calcular os hashes: {e}"}

def browse_file():
    """Abre o seletor de arquivos para escolher um arquivo."""
    file_path = filedialog.askopenfilename(title="Selecione um arquivo")
    if file_path:
        file_path_var.set(file_path)

def generate_all_hashes():
    """Gera todos os hashes para o arquivo selecionado."""
    file_path = file_path_var.get()
    if not file_path:
        messagebox.showerror("Erro", "Por favor, selecione um arquivo.")
        return
    
    results = calculate_all_hashes(file_path)
    result_display.delete(1.0, tk.END)  # Limpa o campo de resultados
    for hash_type, hash_value in results.items():
        result_display.insert(tk.END, f"{hash_type.upper()}\n", "hash_type")
        result_display.insert(tk.END, f"{hash_value}\n\n")
    result_display.see(tk.END)
    
    # Armazena as hashes em uma variável global
    global all_hashes
    all_hashes = results

def open_virustotal():
    """Abre o site do VirusTotal no navegador com a hash SHA-256 calculada."""
    if not all_hashes or "sha256" not in all_hashes:
        messagebox.showerror("Erro", "Nenhuma hash SHA-256 calculada para pesquisar.")
        return

    # Recupera a hash SHA-256
    sha256_hash = all_hashes["sha256"]

    # Cria a URL para o VirusTotal com a hash SHA-256
    url = f"https://www.virustotal.com/gui/file/{sha256_hash}"
    
    # Abre a URL em uma nova aba
    webbrowser.open_new_tab(url)

# Variável global para armazenar as hashes
all_hashes = {}

# Configuração da interface gráfica
root = tk.Tk()
root.title("Hash VirusTotal")
root.geometry("1200x1000")

# Variáveis
file_path_var = tk.StringVar()

# Layout
tk.Label(root, text="Selecione um arquivo", font=("Arial", 11)).pack(pady=5)
file_entry = tk.Entry(root, textvariable=file_path_var, width=80, state="readonly", font=("Arial", 11))
file_entry.pack(pady=5)


# Botão Procurar
browse_button = tk.Button(root, text="Procurar", command=browse_file, font=("Arial", 11), bg="#03d3fc")
browse_button.pack(pady=5)

# Botão VirusTotal
virustotal_button = tk.Button(root, text="Acessar VirusTotal", command=open_virustotal, font=("Arial", 11), bg="#fc9003")
virustotal_button.pack(pady=5)

# Botão Calcular Hashes
generate_button = tk.Button(root, text="Calcular Todos os Hashes", command=generate_all_hashes, font=("Arial", 11), bg="#0af759")
generate_button.pack(pady=20)

# Adiciona o rótulo para o resultado da HASH
tk.Label(
    root,
    text="Resultado da HASH",  # Parte 1 do texto
    background="#fc2003",  # Fundo 
    font=("Arial", 11, "bold")
).pack(pady=20)

tk.Label(
    root,
    text="MD5    SHA1    SHA256",  # Parte 2 do texto
    foreground="#fc2003",  # Vermelho para o texto
    font=("Arial", 11, "bold")
).pack(pady=0)  # Sem espaçamento extra

# ScrolledText para exibir resultados
result_display = ScrolledText(root, wrap=tk.WORD, width=130, height=33, state="normal", font=("Arial", 11))
result_display.pack(pady=5)

# Configuração das tags para o ScrolledText
result_display.tag_config("hash_type", foreground="#fc2003", font=("Arial", 12, "bold"))

# Inicia o loop principal
root.mainloop()
