import tkinter as tk
from tkinter import scrolledtext
import requests

def follow_redirects(url):
    try:
        response = requests.get(url, allow_redirects=True)
        result_text.delete('1.0', tk.END)  # Limpa o texto anterior
        result_text.insert(tk.END, "\n⬇️Redirecionamentos  ⬇️\n\n")
        for i, resp in enumerate(response.history, start=1):
            result_text.insert(tk.END, f"\n\n{i}. 👉 ({resp.status_code}) {resp.url}")
        
        if response.status_code == 200:
            result_text.insert(tk.END, f"\n\n\n{len(response.history) + 1}. 🆗 (200 - OK) {response.url}")
        else:
            result_text.insert(tk.END, f"\n{len(response.history) + 1}.Acesso Proibido:Forbidden ❎ ({response.status_code}) {response.url}")

    except requests.RequestException as e:
        result_text.delete('1.0', tk.END)  # Limpa o texto anterior
        result_text.insert(tk.END, "\nErro ao seguir redirecionamentos: " + str(e))

def main():
    url = url_entry.get()
    follow_redirects(url)

# Configuração da interface gráfica
window = tk.Tk()
window.wm_state('zoomed')
window.title("Verificador de Redirecionamento")

# Frame para o rótulo e a entrada de URL
url_frame = tk.Frame(window)
url_frame.grid(row=0, column=0, padx=5, pady=2, columnspan=2)

url_label = tk.Label(url_frame, text="Digite a URL para verificar o redirecionamento", font=("TkDefaultFont", 11, "bold"))
url_label.grid(row=0, column=0, padx=5, pady=2)

url_entry = tk.Entry(url_frame, width=55, font=("TkDefaultFont", 12, "bold"))
url_entry.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

# Botão "Verificar" com tamanho menor
check_button = tk.Button(window, text="Verificar", command=main, bg="#0cf2e3", font=("TkDefaultFont", 11, "bold"))
check_button.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

# Frame para a área de resultados
result_frame = tk.Frame(window)
result_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=2)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=138, height=45, font=("Arial", 12))
result_text.pack(padx=5, pady=15)

window.mainloop()
