import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import requests
import threading
import time
import urllib3
import socket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== CONFIG ==================
root = tk.Tk()
root.title("DIRECTORY BRUTEFORCE")
root.state("zoomed")
root.configure(bg="black")

GREEN = "#00ff00"
DARK_GREEN = "#00cc00"
BG = "black"

current_wordlist = []
results = []
scanning = False
target_url = ""
progress_value = tk.DoubleVar(value=0)
current_scanning = tk.StringVar(value="Aguardando...")

# ================== HEADERS ==================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53',
}

# ================== FUNÇÕES ==================
def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}" if unit != 'B' else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def check_domain_exists(domain):
    try:
        clean_domain = domain.replace("http://", "").replace("https://", "").split("/")[0]
        socket.gethostbyname(clean_domain)
        return True
    except:
        return False


def scan_directory(path, base_url):
    try:
        path = path.strip().lstrip("/")
        if not path:
            return
            
        full_url = f"{base_url}/{path}"
        
        r = requests.get(full_url, headers=HEADERS, timeout=8, verify=False, allow_redirects=True)
        
        status = r.status_code
        size = len(r.content)
        size_human = human_readable_size(size)
        
        if status in [200, 301, 302, 403, 500]:
            result = f"[+] {full_url:<70} → (HTTP {status}) [Size: {size_human}]"
            if result not in results:
                results.append(result)
                root.after(0, update_results)            
    except:
        pass


def start_scan():
    global scanning, results, target_url, current_wordlist
    base_input = entry_domain.get().strip().rstrip("/")
    
    if not base_input:
        messagebox.showwarning("Atenção", "Digite a URL base!")
        return
    if not current_wordlist:
        messagebox.showwarning("Atenção", "Carregue uma wordlist .txt primeiro!")
        return
    if scanning:
        return

    current_scanning.set("Verificando domínio...")
    root.update()

    if not check_domain_exists(base_input):
        messagebox.showerror("Erro", f"Domínio não encontrado ou inacessível:\n\n{base_input}")
        current_scanning.set("Aguardando...")
        return

    scanning = True
    results.clear()
    text_results.delete(1.0, tk.END)
    progress_value.set(0)
    current_scanning.set("Preparando scan...")

    btn_start.config(state="disabled", text="SCANNING...")

    # Bases únicas
    bases = []
    if base_input.startswith("http://") or base_input.startswith("https://"):
        bases.append(base_input)
    else:
        bases.append("http://" + base_input)
        bases.append("https://" + base_input)
    bases = list(dict.fromkeys(bases))

    # Wordlist única (sem repetição de linhas)
    unique_wordlist = list(dict.fromkeys(current_wordlist))

    def worker():
        global scanning, target_url
        total = len(unique_wordlist) * len(bases)
        count = 0

        for path in unique_wordlist:                    # ← Uma vez por palavra da wordlist
            if not scanning:
                break
                
            path_clean = path.strip().lstrip("/")
            current_scanning.set(f"Testando: {path_clean}")

            for base_url in bases:                      # Testa http + https para cada palavra
                target_url = base_url
                current_scanning.set(f"Testando: {base_url}/{path_clean}")
                
                scan_directory(path, base_url)
                
                count += 1
                progress = (count / total) * 100
                root.after(0, lambda p=progress: progress_value.set(p))
                
                time.sleep(0.18)   # Delay leve
        
        scanning = False
        root.after(0, finish_scan)
    
    threading.Thread(target=worker, daemon=True).start()


def finish_scan():
    btn_start.config(state="normal", text="INICIAR SCAN")
    progress_value.set(100)
    current_scanning.set("Scan finalizado!")
    status_label.config(text=f"Scan finalizado | Encontrados: {len(results)}")


def update_results():
    text_results.delete(1.0, tk.END)
    for res in results[-25:]:
        text_results.insert(tk.END, res + "\n")
    text_results.see(tk.END)
    
    status_label.config(
        text=f"Wordlist: {len(current_wordlist)} únicas | Encontrados: {len(results)}"
    )


def load_wordlist():
    global current_wordlist
    file_path = filedialog.askopenfilename(
        title="Selecione a Wordlist (.txt)",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            
            current_wordlist = list(dict.fromkeys(lines))   # Remove duplicatas
            
            if current_wordlist:
                status_label.config(text=f"Wordlist carregada: {len(current_wordlist)} entradas únicas")
                progress_value.set(0)
                btn_start.config(state="normal")
            else:
                messagebox.showwarning("Erro", "A wordlist está vazia!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler a wordlist.\n\n{e}")


def save_results():
    if not results:
        messagebox.showwarning("Atenção", "Não há resultados para salvar!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Directory Scan - Alvo: {target_url}\n\n")
                f.write(f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*120 + "\n\n")
                for res in results:
                    f.write(res + "\n")
            status_label.config(text=f"Resultados salvos\n\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo.\n\n{e}")


# ================== INTERFACE ==================
title = tk.Label(root, text="DIRECTORY BRUTEFORCE", font=("Consolas", 26, "bold"), fg=GREEN, bg=BG)
title.pack(pady=25)

frame_input = tk.Frame(root, bg=BG)
frame_input.pack(pady=10)

tk.Label(frame_input, text="URL Base:", font=("Consolas", 14), fg=GREEN, bg=BG).pack(side=tk.LEFT, padx=10)
entry_domain = tk.Entry(frame_input, width=50, font=("Consolas", 14), bg="#111111", fg=GREEN, insertbackground=GREEN)
entry_domain.pack(side=tk.LEFT, padx=10)
entry_domain.insert(0, "http://businesscorp.com.br")

current_frame = tk.Frame(root, bg=BG)
current_frame.pack(pady=5)
tk.Label(current_frame, text="Testando agora:", font=("Consolas", 12), fg=GREEN, bg=BG).pack(side=tk.LEFT, padx=10)
current_label = tk.Label(current_frame, textvariable=current_scanning, font=("Consolas", 12), fg="#00ff88", bg=BG)
current_label.pack(side=tk.LEFT)

progress_frame = tk.Frame(root, bg=BG)
progress_frame.pack(pady=8, padx=50, fill=tk.X)
tk.Label(progress_frame, text="Progresso:", font=("Consolas", 12), fg=GREEN, bg=BG).pack(side=tk.LEFT, padx=10)
progress_bar = ttk.Progressbar(progress_frame, variable=progress_value, maximum=100, style="green.Horizontal.TProgressbar")
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

style = ttk.Style()
style.configure("green.Horizontal.TProgressbar", foreground=GREEN, background=GREEN, troughcolor="#001a00", thickness=18)

btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=15)

btn_start = tk.Button(btn_frame, text="INICIAR SCAN", font=("Consolas", 12, "bold"),
                      bg="#003300", fg=GREEN, width=22, height=2, command=start_scan, state="disabled")
btn_start.pack(side=tk.LEFT, padx=12)

btn_wordlist = tk.Button(btn_frame, text="CARREGAR WORDLIST", font=("Consolas", 12, "bold"),
                         bg="#003300", fg=GREEN, width=22, height=2, command=load_wordlist)
btn_wordlist.pack(side=tk.LEFT, padx=12)

btn_save = tk.Button(btn_frame, text="SALVAR RESULTADOS", font=("Consolas", 12, "bold"),
                     bg="#003300", fg=GREEN, width=22, height=2, command=save_results)
btn_save.pack(side=tk.LEFT, padx=12)

tk.Label(root, text="RESULTADOS:", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=(15,5))

text_results = scrolledtext.ScrolledText(root, height=18, font=("Consolas", 11), bg="#0a0a0a", fg=GREEN)
text_results.pack(padx=50, pady=10, fill=tk.BOTH, expand=True)

status_label = tk.Label(root, text="Carregue uma wordlist .txt para começar", font=("Consolas", 12), fg=DARK_GREEN, bg=BG)
status_label.pack(pady=8)

root.mainloop()
