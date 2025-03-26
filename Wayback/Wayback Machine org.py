import requests
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading

def search_wayback_machine():
    search_button["state"] = "disabled"
    url = url_entry.get()
    response = requests.get(
        f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&output=json&fl=timestamp,original&collapse=urlkey"
    )

    if response.status_code == 200:
        data = json.loads(response.text)
        progress_bar["maximum"] = len(data)
        progress_bar["value"] = 0

        urls_label.config(text="")
        urls_text.delete("1.0", tk.END)

        for i, entry in enumerate(data):
            if i == 0:  # Ignorar o cabeçalho do JSON
                continue

            timestamp = entry[0]  # Data e hora em formato 'yyyyMMddHHmmss'
            formatted_time = f"{timestamp[:4]}   {timestamp[4:6]}/{timestamp[6:8]}  {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
            captured_url = entry[1]

            # Inserir os resultados formatados no widget de texto
            urls_text.insert(tk.END, f"{formatted_time}    {captured_url}\n\n")

            # Atualizar a barra de progresso
            window.after(10, update_progress, i)

        count_label.config(text=f"Foram Capturadas {len(data) - 1} URL", font=("Arial", 12))
    else:
        messagebox.showerror(
            "Erro",
            f"Não foi possível capturar as URL. O servidor retornou o código de status {response.status_code}.",
        )

def update_progress(value):
    progress_bar["value"] = value
    if value == progress_bar["maximum"] - 1:
        search_button["state"] = "normal"

def start_search_thread():
    search_button["state"] = "disabled"
    search_thread = threading.Thread(target=search_wayback_machine)
    search_thread.start()

def save_urls_to_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")]
    )

    if file_path:
        urls_content = urls_text.get("1.0", tk.END).strip()
        captured_urls = urls_content.split("\n\n")  # Separar cada URL pelo espaço em branco entre elas
        captured_urls = [url for url in captured_urls if url.strip()]  # Filtrar linhas vazias
        total_urls = len(captured_urls)  # Contar apenas URLs válidas

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                # Escrever o total de URLs no início
                file.write(f"Foram capturadas: {total_urls} URL\n\n")
                # Escrever todas as URLs capturadas
                file.write("\n\n".join(captured_urls))
            messagebox.showinfo("Sucesso", f"As URLs foram salvas com sucesso em: {file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {str(e)}")

def on_close():
    """Método para fechar o aplicativo e interromper a execução de forma completa."""
    if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
        window.destroy()

window = tk.Tk()
window.title("Capturador de URL do Wayback Machine")
window.geometry("1280x950")
window.wm_state("zoomed")

# Intercepta o evento de fechar a janela (clicar no "X")
window.protocol("WM_DELETE_WINDOW", on_close)

url_label = tk.Label(window, text="Digite a URL que deseja procurar no Wayback Machine", font=("Arial", 12))
url_entry = tk.Entry(window, width=50, font=("Arial", 12))

# Definindo as cores dos botões manualmente
search_button = tk.Button(window, text="Procurar", command=start_search_thread, bg="#03fc17", fg="black", font=("Arial", 12))
urls_label = tk.Label(window, text="")

urls_text = tk.Text(window, height=38, width=130, font=("Arial", 12))
urls_scrollbar = ttk.Scrollbar(window, command=urls_text.yview)

urls_text.config(yscrollcommand=urls_scrollbar.set)
count_label = tk.Label(window, text="")

separator = ttk.Separator(window, orient="horizontal")
progress_bar = ttk.Progressbar(window, orient="horizontal", length=500, mode="determinate")

# Definindo a cor do botão "Salvar"
save_button = tk.Button(window, text="Salvar", command=save_urls_to_file, bg="#03dffc", fg="black", font=("Arial", 12))

# Layout
url_label.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
url_entry.grid(row=1, column=0, padx=5, pady=5, columnspan=3)
search_button.grid(row=2, column=0, padx=5, pady=5, columnspan=3)
urls_label.grid(row=3, column=0, padx=5, pady=5)
urls_text.grid(row=6, column=0, columnspan=2, padx=40, pady=5, sticky="nsew")
urls_scrollbar.grid(row=6, column=2, sticky="ns")
count_label.grid(row=5, column=0, padx=5, pady=5)
progress_bar.grid(row=4, column=0, padx=5, pady=3, columnspan=3)

save_button.grid(row=3, column=0, padx=5, pady=5, columnspan=3)

window.mainloop()
