import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import time
import threading

# threading

def start_search():
    thread = threading.Thread(target=search_wayback_machine)
    thread.start()

# ---------------- FUNÇÕES ---------------- #

def format_time(seconds):
    """Formata segundos para hh:mm:ss"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def process_entries(data, total, start_time, i=1):
    """Mostra as URL uma por uma em tempo real"""
    if i >= len(data):
        # Finalizou
        end_time = time.time()
        elapsed = end_time - start_time
        count_label.config(
            text=f"Foram Capturadas: {total} URL do ano {selected_year}", 
            font=("Arial", 12)
        )
        time_label.config(
            text=f"⏱ Tempo total: {int(elapsed)} segundos ({format_time(elapsed)})", 
            font=("Arial", 12)
        )
        tempo_em_andamento_label.config(text="✅ Varredura finalizada!")
        search_button["state"] = "normal"
        return

    entry = data[i]
    timestamp = entry[0]
    formatted_time = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
    captured_url = entry[1]

    # Adiciona linha na interface
    urls_text.insert(tk.END, f"{formatted_time}    {captured_url}\n\n")
    urls_text.see(tk.END)  

    # Atualiza progresso
    progress_bar["value"] = i

    # Atualiza tempo estimado
    now = time.time()
    elapsed = now - start_time
    avg_time_per_item = elapsed / i if i != 0 else 0
    remaining = avg_time_per_item * (total - i)
    tempo_em_andamento_label.config(
        text=f"⏱ Tempo: {int(elapsed)}s ({format_time(elapsed)}) | Restante: {int(remaining)}s ({format_time(remaining)}) | URL: {i}/{total}"
    )

    # Continua chamando até acabar
    window.after(1, process_entries, data, total, start_time, i+1)

def search_wayback_machine():
    """Busca as URL no Wayback Machine"""
    global selected_year
    search_button["state"] = "disabled"
    tempo_em_andamento_label.config(text="Iniciando varredura...")    

    url = url_entry.get().strip().replace("https://", "").replace("http://", "").replace("www.", "")
    selected_year = year_entry.get().strip()

    if not url or not selected_year.isdigit() or len(selected_year) != 4:
        messagebox.showwarning("Aviso", "Digite uma URL e um ano válido.")
        search_button["state"] = "normal"
        return

    try:
        response = requests.get(
            f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&from={selected_year}&to={selected_year}&output=json&fl=timestamp,original&collapse=urlkey"
        )
        response.raise_for_status()
    except requests.RequestException as e:
        messagebox.showerror("Erro de conexão", f"Erro ao conectar com o Wayback Machine:\n{e}")
        search_button["state"] = "normal"
        return

    data = json.loads(response.text)
    if len(data) <= 1:
        messagebox.showinfo("Nenhuma URL Encontrada", f"Nenhuma URL foi capturada no ano {selected_year}.")
        search_button["state"] = "normal"
        return

    total = len(data) - 1
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    urls_text.delete("1.0", tk.END)

    start_time = time.time()

    # Processa linha por linha em tempo real
    window.after(1, process_entries, data, total, start_time, 1)

def save_to_file():
    """Salva as URLs capturadas em um arquivo de texto"""
    urls = urls_text.get("1.0", tk.END).strip()
    if not urls:
        messagebox.showwarning("Aviso", "Nenhuma URL para salvar.")
        return

    try:
        with open(f"urls_{selected_year}.txt", "w", encoding="utf-8") as f:
            f.write(f"[+] {len(urls.splitlines())} URL Encontrados no ano {selected_year}\n\n")
            f.write(urls)
        messagebox.showinfo("Sucesso", f"As URLs foram salvas em urls_{selected_year}.txt")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Erro ao salvar as URLs:\n{e}")

# ---------------- INTERFACE ---------------- #
window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.geometry("1260x900")

# Entrada URL
url_frame = tk.Frame(window)
url_frame.pack(pady=5)
url_label = tk.Label(url_frame, text="Digite a URL que deseja procurar no Wayback Machine", font=("Arial", 12))
url_label.pack()
url_entry = tk.Entry(url_frame, width=60, font=("Arial", 12))
url_entry.pack()

# Entrada manual do ano
year_frame = tk.Frame(window)
year_frame.pack(pady=5)
year_label = tk.Label(year_frame, text="Digite o Ano (ex: 1996)", font=("Arial", 12))
year_label.pack(side="left")
year_entry = tk.Entry(year_frame, width=10, font=("Arial", 12))
year_entry.pack(side="left", padx=5)

# Botões
button_frame = tk.Frame(window)
button_frame.pack(pady=10)
search_button = tk.Button(button_frame, text="Procurar", command=start_search, bg="lime", font=("Arial", 12))

search_button.grid(row=0, column=0, padx=10)
save_button = tk.Button(button_frame, text="Salvar", command=save_to_file, bg="deepskyblue", font=("Arial", 12))
save_button.grid(row=0, column=1, padx=10)

# Barra de progresso
progress_bar = ttk.Progressbar(window, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=5)

# Labels de status
tempo_em_andamento_label = tk.Label(window, text="", font=("Arial", 10), fg="blue")
tempo_em_andamento_label.pack()
count_label = tk.Label(window, text="", font=("Arial", 12))
count_label.pack()
time_label = tk.Label(window, text="", font=("Arial", 12))
time_label.pack()

# Caixa de texto com Scrollbar
text_frame = tk.Frame(window)
text_frame.pack(pady=10)

urls_text = tk.Text(text_frame, width=130, height=33, font=("Arial", 12))
urls_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(text_frame, command=urls_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
urls_text.config(yscrollcommand=scrollbar.set)

window.mainloop()
