import requests
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import time

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

def search_wayback_machine():
    search_button["state"] = "disabled"
    tempo_em_andamento_label.config(text="Iniciando varredura...")

    url = url_entry.get().strip().replace("https://", "").replace("http://", "").replace("www.", "")
    
    try:
        response = requests.get(
            f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&output=json&fl=timestamp,original&collapse=urlkey"
        )
        response.raise_for_status()
    except requests.RequestException as e:
        messagebox.showerror("Erro de conexão", f"Erro ao conectar com o Wayback Machine:\n{e}")
        search_button["state"] = "normal"
        tempo_em_andamento_label.config(text="")
        return

    data = json.loads(response.text)

    if len(data) <= 1:
        messagebox.showinfo("Nenhuma URL Encontrada", "Nenhuma URL foi capturada para esse domínio.")
        search_button["state"] = "normal"
        tempo_em_andamento_label.config(text="")
        return

    total = len(data) - 1
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    urls_label.config(text="")
    urls_text.delete("1.0", tk.END)

    start_time = time.time()
    buffer = ""

    for i, entry in enumerate(data):
        if i == 0:
            continue

        timestamp = entry[0]
        formatted_time = f"{timestamp[:4]}   {timestamp[4:6]}/{timestamp[6:8]}  {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
        captured_url = entry[1]

        buffer += f"{formatted_time}    {captured_url}\n\n"

        if i % 100 == 0 or i == total:
            urls_text.insert(tk.END, buffer)
            urls_text.update_idletasks()
            buffer = ""

        progress_bar["value"] = i
        progress_bar.update_idletasks()

        if i % 10 == 0 or i == total:
            now = time.time()
            elapsed = now - start_time
            avg_time_per_item = elapsed / i if i != 0 else 0
            remaining = avg_time_per_item * (total - i)

            tempo_em_andamento_label.config(
                text=f"⏱ Tempo: {int(elapsed)}s ({format_time(elapsed)}) | Restante: {int(remaining)}s ({format_time(remaining)}) | URL: {i}  = {total}"
            )
            tempo_em_andamento_label.update_idletasks()

    end_time = time.time()
    elapsed = end_time - start_time

    count_label.config(text=f"Foram Capturadas: {total} URL", font=("Arial", 12))
    time_label.config(text=f"⏱ Tempo total: {int(elapsed)} segundos ({format_time(elapsed)})", font=("Arial", 12))
    tempo_em_andamento_label.config(text="✅ Varredura finalizada!")
    search_button["state"] = "normal"

def start_search_thread():
    search_thread = threading.Thread(target=search_wayback_machine)
    search_thread.start()

def save_urls_to_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")]
    )

    if file_path:
        urls_content = urls_text.get("1.0", tk.END).strip()
        captured_urls = urls_content.split("\n\n")
        captured_urls = [url for url in captured_urls if url.strip()]
        total_urls = len(captured_urls)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(f"Foram capturadas: {total_urls} URL\n\n")
                file.write("\n\n".join(captured_urls))
            messagebox.showinfo("Sucesso", f"As URL foram salvas com sucesso em:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{str(e)}")

def on_close():
    if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
        window.destroy()

# ============ GUI ============

window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.geometry("1280x950")
window.wm_state("zoomed")
window.protocol("WM_DELETE_WINDOW", on_close)

# Entrada de URL
url_label = tk.Label(window, text="Digite a URL que deseja procurar no Wayback Machine", font=("Arial", 12))
url_entry = tk.Entry(window, width=50, font=("Arial", 12))

# Botões
search_button = tk.Button(window, text="Procurar", command=start_search_thread, bg="#03fc17", fg="black", font=("Arial", 12))
save_button = tk.Button(window, text="Salvar", command=save_urls_to_file, bg="#03dffc", fg="black", font=("Arial", 12))

# Texto e Scroll
urls_text = tk.Text(window, height=35, width=130, font=("Arial", 12))
urls_scrollbar = ttk.Scrollbar(window, command=urls_text.yview)
urls_text.config(yscrollcommand=urls_scrollbar.set)

# Barra de Progresso
progress_bar = ttk.Progressbar(window, orient="horizontal", length=500, mode="determinate")

# Labels
urls_label = tk.Label(window, text="")
count_label = tk.Label(window, text="")
time_label = tk.Label(window, text="")
tempo_em_andamento_label = tk.Label(window, text="", font=("Arial", 12), fg="blue")

# Layout
url_label.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
url_entry.grid(row=1, column=0, padx=5, pady=5, columnspan=3)
search_button.grid(row=2, column=0, padx=5, pady=5, columnspan=3)
save_button.grid(row=3, column=0, padx=5, pady=5, columnspan=3)
progress_bar.grid(row=4, column=0, padx=5, pady=3, columnspan=3)
tempo_em_andamento_label.grid(row=5, column=0, padx=5, pady=2, columnspan=3)
time_label.grid(row=6, column=0, padx=5, pady=3, columnspan=3)
count_label.grid(row=7, column=0, padx=5, pady=5)
urls_text.grid(row=8, column=0, columnspan=2, padx=40, pady=5, sticky="nsew")
urls_scrollbar.grid(row=8, column=2, sticky="ns")

window.mainloop()
