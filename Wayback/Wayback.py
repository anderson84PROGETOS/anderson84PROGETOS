import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import time
import threading
from datetime import datetime

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def process_entries(data, total, start_time, i=1):
    if i >= len(data):
        end_time = time.time()
        elapsed = end_time - start_time
        count_label.config(text=f"Foram Capturadas: {total} URLs", font=("Arial", 12))
        time_label.config(text=f"⏱ Tempo total: {int(elapsed)} segundos ({format_time(elapsed)})", font=("Arial", 12))
        tempo_em_andamento_label.config(text="✅ Varredura finalizada!")
        search_button["state"] = "normal"
        return

    entry = data[i]
    timestamp = entry[0]
    formatted_time = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
    captured_url = entry[1]

    urls_text.insert(tk.END, f"{formatted_time}    {captured_url}\n\n")
    urls_text.see(tk.END)

    progress_bar["value"] = i
    now = time.time()
    elapsed = now - start_time
    avg_time = elapsed / i if i != 0 else 0
    remaining = avg_time * (total - i)
    tempo_em_andamento_label.config(
        text=f"⏱ Tempo: {int(elapsed)}s ({format_time(elapsed)}) | Restante: {int(remaining)}s ({format_time(remaining)}) | URL: {i}/{total}"
    )

    window.after(1, process_entries, data, total, start_time, i+1)

def search_wayback_machine():
    global selected_range
    search_button["state"] = "disabled"
    tempo_em_andamento_label.config(text="Iniciando varredura...")

    url = url_entry.get().strip().replace("https://", "").replace("http://", "").replace("www.", "")
    selected_year = year_entry.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Digite uma URL válida.")
        search_button["state"] = "normal"
        return

    from_year = 1996
    to_year = datetime.now().year
    if selected_year.isdigit() and len(selected_year) == 4:
        from_year = to_year = int(selected_year)
        selected_range = selected_year
    else:
        selected_range = f"{from_year}-{to_year}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(
            f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&from={from_year}&to={to_year}&output=json&fl=timestamp,original&collapse=urlkey",
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
    except requests.RequestException as e:
        messagebox.showerror("Erro de conexão", f"Erro ao conectar com o Wayback Machine:\n{e}")
        search_button["state"] = "normal"
        return

    try:
        data = response.json()
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao processar a resposta JSON:\n{e}")
        search_button["state"] = "normal"
        return

    if len(data) <= 1:
        messagebox.showinfo("Nenhuma URL Encontrada", f"Nenhuma URL foi capturada em {selected_range}.")
        search_button["state"] = "normal"
        return

    total = len(data) - 1
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    urls_text.delete("1.0", tk.END)
    start_time = time.time()

    # Inicia processamento em tempo real
    window.after(1, process_entries, data, total, start_time, 1)

def start_search():
    threading.Thread(target=search_wayback_machine).start()

def save_to_file():
    urls = urls_text.get("1.0", tk.END).strip()
    if not urls:
        messagebox.showwarning("Aviso", "Nenhuma URL para salvar.")
        return
    try:
        with open(f"urls_{selected_range}.txt", "w", encoding="utf-8") as f:
            f.write(f"[+] {len(urls.splitlines())} URLs Encontradas em {selected_range}\n\n")
            f.write(urls)
        messagebox.showinfo("Sucesso", f"As URLs foram salvas em urls_{selected_range}.txt")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Erro ao salvar as URLs:\n{e}")

# ---------------- INTERFACE ---------------- #
window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.geometry("1260x900")

url_frame = tk.Frame(window)
url_frame.pack(pady=5)
url_label = tk.Label(url_frame, text="Digite a URL que deseja procurar no Wayback Machine", font=("Arial", 12))
url_label.pack()
url_entry = tk.Entry(url_frame, width=60, font=("Arial", 12))
url_entry.pack()

year_frame = tk.Frame(window)
year_frame.pack(pady=5)
year_label = tk.Label(year_frame, text="Digite o Ano (ex: 1996) ou deixe vazio para buscar de 1996 até hoje", font=("Arial", 12))
year_label.pack(side="left")
year_entry = tk.Entry(year_frame, width=10, font=("Arial", 12))
year_entry.pack(side="left", padx=5)

button_frame = tk.Frame(window)
button_frame.pack(pady=10)
search_button = tk.Button(button_frame, text="Procurar", command=start_search, bg="lime", font=("Arial", 12))
search_button.grid(row=0, column=0, padx=10)
save_button = tk.Button(button_frame, text="Salvar", command=save_to_file, bg="deepskyblue", font=("Arial", 12))
save_button.grid(row=0, column=1, padx=10)

progress_bar = ttk.Progressbar(window, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=5)
tempo_em_andamento_label = tk.Label(window, text="", font=("Arial", 10), fg="blue")
tempo_em_andamento_label.pack()
count_label = tk.Label(window, text="", font=("Arial", 12))
count_label.pack()
time_label = tk.Label(window, text="", font=("Arial", 12))
time_label.pack()

text_frame = tk.Frame(window)
text_frame.pack(pady=10)
urls_text = tk.Text(text_frame, width=130, height=30, font=("Arial", 12))
urls_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(text_frame, command=urls_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
urls_text.config(yscrollcommand=scrollbar.set)

window.mainloop()
