import requests
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import re

def clean_url(url):
    """Limpa a URL para pegar apenas o domínio"""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url


def search_wayback_machine(from_year=None, to_year=None):
    search_button["state"] = "disabled"
    period_button["state"] = "disabled"
    
    raw_url = url_entry.get().strip()
    
    if not raw_url:
        messagebox.showwarning("Aviso", "Digite uma URL ou domínio!")
        reset_buttons()
        return

    domain = clean_url(raw_url)

    # Monta a URL com filtro de data se informado
    api_url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=timestamp,original&collapse=urlkey"
    
    if from_year and to_year:
        api_url += f"&from={from_year}0101&to={to_year}1231"
        count_label.config(text=f"Buscando capturas de {domain} Entre {from_year} e {to_year}")
    else:
        count_label.config(text=f"Buscando todas as capturas de {domain}")

    try:
        response = requests.get(api_url)

        if response.status_code == 200:
            data = json.loads(response.text)
            
            urls_text.delete("1.0", tk.END)
            progress_bar["maximum"] = max(len(data) - 1, 0)
            progress_bar["value"] = 0

            total = len(data) - 1
            count_label.config(text=f"Processando {total} capturas")

            for i, entry in enumerate(data):
                if i == 0:  # Ignorar cabeçalho
                    continue

                timestamp = entry[0]
                formatted_time = (
                    f"{timestamp[6:8]}/{timestamp[4:6]}/{timestamp[:4]} "
                    f"{timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
                )
                captured_url = entry[1]

                line = f"[{formatted_time}]  {captured_url}\n\n"
                urls_text.insert(tk.END, line)
                urls_text.see(tk.END)
                
                progress_bar["value"] = i
                window.update_idletasks()

            count_label.config(
                text=f"✅ Foram capturadas {total} URL de {domain}", 
                font=("Consolas", 12, "bold")
            )
        else:
            messagebox.showerror("Erro", f"Servidor retornou código {response.status_code}")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na conexão: {str(e)}")
    finally:
        reset_buttons()


def reset_buttons():
    search_button["state"] = "normal"
    period_button["state"] = "normal"


def start_search_thread():
    threading.Thread(target=search_wayback_machine, daemon=True).start()


def start_period_search():
    try:
        from_year = int(from_year_entry.get().strip())
        to_year = int(to_year_entry.get().strip())
        
        if from_year > to_year:
            messagebox.showwarning("Aviso", "Ano inicial deve ser menor ou igual ao ano final!")
            return
        if from_year < 1990 or to_year > 2030:
            if not messagebox.askyesno("Confirmação", "Anos fora do intervalo comum (1990-2030). Deseja continuar?"):
                return
                
        threading.Thread(
            target=search_wayback_machine, 
            args=(from_year, to_year),
            daemon=True
        ).start()
    except ValueError:
        messagebox.showwarning("Aviso", "Por favor, insira anos válidos (apenas números)")


def save_urls_to_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", 
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return

    try:
        content = urls_text.get("1.0", tk.END).strip()
        lines = [line for line in content.split("\n") if line.strip()]
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Foram Capturadas: {len(lines)} URL\n\n\n")
            f.write("\n\n".join(lines))
        
        messagebox.showinfo("Sucesso", f"Arquivo salvo\n\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar: {str(e)}")


def on_close():
    if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
        window.destroy()


# ==================== INTERFACE ====================
window = tk.Tk()
window.title("WAYBACK MACHINE URL CAPTURATOR")
window.geometry("1280x950")
window.configure(bg="#0a0a0a")
window.wm_state("zoomed")

style = ttk.Style()
style.theme_use("default")
style.configure("TProgressbar", background="#00ff41", troughcolor="#1a1a1a")

title_label = tk.Label(window, text="WAYBACK MACHINE URL CAPTURATOR", 
                       font=("Consolas", 18, "bold"), fg="#00ff41", bg="#0a0a0a")
title_label.grid(row=0, column=0, columnspan=3, pady=10)

url_label = tk.Label(window, text="Digite o domínio (example.com ou http://example.com):", 
                     font=("Consolas", 12), fg="#00ff41", bg="#0a0a0a")
url_entry = tk.Entry(window, width=70, font=("Consolas", 12),
                     bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41")

# === Frame para filtro de período ===
period_frame = tk.Frame(window, bg="#0a0a0a")
period_frame.grid(row=3, column=0, columnspan=3, pady=8)

tk.Label(period_frame, text="Ano Inicial:", font=("Consolas", 11), fg="#00ff41", bg="#0a0a0a").pack(side="left", padx=5)
from_year_entry = tk.Entry(period_frame, width=8, font=("Consolas", 11), bg="#1a1a1a", fg="#00ff41", justify="center")
from_year_entry.pack(side="left", padx=5)
from_year_entry.insert(0, "1996")  # valor padrão

tk.Label(period_frame, text="Ano Final:", font=("Consolas", 11), fg="#00ff41", bg="#0a0a0a").pack(side="left", padx=5)
to_year_entry = tk.Entry(period_frame, width=8, font=("Consolas", 11), bg="#1a1a1a", fg="#00ff41", justify="center")
to_year_entry.pack(side="left", padx=5)
to_year_entry.insert(0, "2026")  # valor padrão

# Botões
button_frame = tk.Frame(window, bg="#0a0a0a")
button_frame.grid(row=4, column=0, columnspan=3, pady=10)

search_button = tk.Button(button_frame, text="▶ BUSCAR TODAS", 
                          command=start_search_thread, bg="#008000", fg="#00ff41",
                          font=("Consolas", 12, "bold"), width=22, height=2)
search_button.pack(side="left", padx=8)

period_button = tk.Button(button_frame, text="📅 BUSCAR POR PERÍODO", 
                          command=start_period_search, bg="#0066cc", fg="#00ff41",
                          font=("Consolas", 12, "bold"), width=25, height=2)
period_button.pack(side="left", padx=8)

save_button = tk.Button(button_frame, text="💾 SALVAR RESULTADOS", 
                        command=save_urls_to_file, bg="#006400", fg="#00ff41",
                        font=("Consolas", 12, "bold"), width=25, height=2)
save_button.pack(side="left", padx=8)

# Resultados
urls_text = tk.Text(window, height=35, width=150, font=("Consolas", 11),
                    bg="#0a0a0a", fg="#00ff41", insertbackground="#00ff41")
urls_scrollbar = ttk.Scrollbar(window, command=urls_text.yview)
urls_text.config(yscrollcommand=urls_scrollbar.set)

count_label = tk.Label(window, text="", font=("Consolas", 12), fg="#00ff41", bg="#0a0a0a")
progress_bar = ttk.Progressbar(window, orient="horizontal", length=800, mode="determinate")

# Layout
url_label.grid(row=1, column=0, padx=10, pady=5, columnspan=3)
url_entry.grid(row=2, column=0, padx=10, pady=5, columnspan=3)
count_label.grid(row=5, column=0, pady=5, columnspan=3)
progress_bar.grid(row=6, column=0, pady=5, padx=20, columnspan=3)
urls_text.grid(row=7, column=0, padx=20, pady=5, columnspan=2, sticky="nsew")
urls_scrollbar.grid(row=7, column=2, sticky="ns", pady=5)

window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()
