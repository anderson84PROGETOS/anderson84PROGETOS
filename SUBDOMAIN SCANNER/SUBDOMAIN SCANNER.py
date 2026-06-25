import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import requests
import threading
import time
import urllib3

# Desativa aviso de HTTPS inseguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== CONFIG ==================
root = tk.Tk()
root.title("SUBDOMAIN SCANNER")
root.state("zoomed")
root.configure(bg="black")

GREEN = "#00ff00"
DARK_GREEN = "#00cc00"
BG = "black"

# Variáveis
current_wordlist = []
results = []
scanning = False
target_domain = ""
progress_value = tk.DoubleVar(value=0)

# ================== FUNÇÕES ==================
def scan_subdomain(sub, domain):
    full = f"{sub}.{domain}"
    ip = None
    status = "?"
    protocol = "HTTP"   # padrão

    try:
        ip = socket.gethostbyname(full)
        
        # Tenta HTTPS primeiro
        try:
            r = requests.get(f"https://{full}", timeout=4, verify=False)
            status = r.status_code
            protocol = "HTTPS"
        except:
            # Se HTTPS falhar, tenta HTTP
            try:
                r = requests.get(f"http://{full}", timeout=4, verify=False)
                status = r.status_code
                protocol = "HTTP"
            except:
                status = "?"
                protocol = "HTTP"
        
        result = f"[+] https://{full:<50} → {ip:<20} ({protocol} {status})" if protocol == "HTTPS" else \
                 f"[+] http://{full:<50}  → {ip:<20} ({protocol} {status})"
        
        results.append(result)
        root.after(0, update_results)        
    except:
        pass

def start_scan():
    global scanning, results, target_domain
    domain = entry_domain.get().strip()
    
    if not domain:
        messagebox.showwarning("Atenção", "Digite um domínio!")
        return
    if not current_wordlist:
        messagebox.showwarning("Atenção", "Carregue uma wordlist .txt primeiro!")
        return
    if scanning:
        return
    
    target_domain = domain
    scanning = True
    results.clear()
    text_results.delete(1.0, tk.END)
    progress_value.set(0)
    
    btn_start.config(state="disabled", text="SCANNING...")
    
    def worker():
        global scanning
        total = len(current_wordlist)
        for i, sub in enumerate(current_wordlist):
            if not scanning:
                break
            scan_subdomain(sub, domain)
            progress = ((i + 1) / total) * 100
            root.after(0, lambda p=progress: progress_value.set(p))
            time.sleep(0.22)
        
        scanning = False
        root.after(0, finish_scan)
    
    threading.Thread(target=worker, daemon=True).start()

def finish_scan():
    btn_start.config(state="normal", text="INICIAR SCAN")
    progress_value.set(100)
    status_label.config(text=f"Scan finalizado | Encontrados: {len(results)}")

def update_results():
    text_results.delete(1.0, tk.END)
    for res in results[-25:]:
        text_results.insert(tk.END, res + "\n")
    text_results.see(tk.END)
    
    status_label.config(
        text=f"Wordlist: {len(current_wordlist)} | Encontrados: {len(results)} | Escaneando: {'SIM' if scanning else 'NÃO'}"
    )

def load_wordlist():
    global current_wordlist
    file_path = filedialog.askopenfilename(
        title="Selecione a Wordlist (.txt)",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_wordlist = [line.strip() for line in f if line.strip()]
            
            if current_wordlist:
                status_label.config(text=f"Wordlist carregada: {len(current_wordlist)} subdomínios")
                progress_value.set(0)
                btn_start.config(state="normal")
            else:
                messagebox.showwarning("Erro", "Wordlist vazia!")
        except:
            messagebox.showerror("Erro", "Não foi possível ler a wordlist.")

def save_results():
    if not results:
        messagebox.showwarning("Atenção", "Não há resultados para salvar!")
        return
    file_path = filedialog.asksaveasfilename(
        title="Salvar Resultados",
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")]
    )
    if file_path:
        try:
            # Data no formato brasileiro DD/MM/YYYY
            data_atual = time.strftime("%d/%m/%Y %H:%M:%S")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Subdomain Scan - Alvo: {target_domain}\n\n")
                f.write(f"Data: {data_atual}\n")
                f.write("="*100 + "\n\n")
                for res in results:
                    f.write(res + "\n")
            status_label.config(text=f"Resultados salvos\n\n{file_path}")
        except:
            messagebox.showerror("Erro", "Erro ao salvar arquivo.")

# ================== INTERFACE ==================
title = tk.Label(root, text="SUBDOMAIN ENUMERATOR", 
                 font=("Consolas", 26, "bold"), fg=GREEN, bg=BG)
title.pack(pady=25)

frame_input = tk.Frame(root, bg=BG)
frame_input.pack(pady=10)

tk.Label(frame_input, text="Domínio Alvo:", font=("Consolas", 14), fg=GREEN, bg=BG).pack(side=tk.LEFT, padx=10)
entry_domain = tk.Entry(frame_input, width=45, font=("Consolas", 14), bg="#111111", fg=GREEN, insertbackground=GREEN)
entry_domain.pack(side=tk.LEFT, padx=10)
entry_domain.insert(0, "exemplo.com")

# Progresso
progress_frame = tk.Frame(root, bg=BG)
progress_frame.pack(pady=12, padx=50, fill=tk.X)
tk.Label(progress_frame, text="Progresso:", font=("Consolas", 12), fg=GREEN, bg=BG).pack(side=tk.LEFT, padx=10)

progress_bar = ttk.Progressbar(progress_frame, variable=progress_value, maximum=100, 
                               style="green.Horizontal.TProgressbar")
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

style = ttk.Style()
style.configure("green.Horizontal.TProgressbar", foreground=GREEN, background=GREEN, troughcolor="#001a00", thickness=18)

# Botões
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=15)

btn_start = tk.Button(btn_frame, text="INICIAR SCAN", font=("Consolas", 12, "bold"),
                      bg="#003300", fg=GREEN, activebackground="#00aa00", activeforeground="black",
                      width=22, height=2, command=start_scan, state="disabled")
btn_start.pack(side=tk.LEFT, padx=12)

btn_wordlist = tk.Button(btn_frame, text="CARREGAR WORDLIST", font=("Consolas", 12, "bold"),
                         bg="#003300", fg=GREEN, activebackground="#00aa00", activeforeground="black",
                         width=22, height=2, command=load_wordlist)
btn_wordlist.pack(side=tk.LEFT, padx=12)

btn_save = tk.Button(btn_frame, text="SALVAR RESULTADOS", font=("Consolas", 12, "bold"),
                     bg="#003300", fg=GREEN, activebackground="#00aa00", activeforeground="black",
                     width=22, height=2, command=save_results)
btn_save.pack(side=tk.LEFT, padx=12)

tk.Label(root, text="RESULTADOS", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=(15,5))

text_results = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 11),
                                         bg="#0a0a0a", fg=GREEN, insertbackground=GREEN)
text_results.pack(padx=50, pady=10, fill=tk.BOTH, expand=True)

status_label = tk.Label(root, text="Carregue uma wordlist .txt para começar", 
                        font=("Consolas", 12), fg=DARK_GREEN, bg=BG)
status_label.pack(pady=8)

root.mainloop()
