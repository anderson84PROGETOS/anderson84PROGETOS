import requests
import json
import tkinter as tk
from tkinter import scrolledtext, Label, filedialog

def coletar_informacoes(alvo):
    req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))
    dados = json.loads(req.text)
    subdominios = set()
    for value in dados:
        subdominios.add(value['name_value'])
    return list(subdominios)

def exibir_resultados():
    alvo = entry.get().rstrip()
    resultados = coletar_informacoes(alvo)
    result_text.delete('1.0', tk.END)
    for resultado in resultados:
        result_text.insert(tk.END, resultado + '\n')
    mostrar_mensagem(len(resultados))

def mostrar_mensagem(numero_subdominios):
    mensagem = f"Foram encontrados {numero_subdominios} subdomínios únicos."
    mensagem_label.config(text=mensagem)

def salvar_arquivo():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(result_text.get("1.0", tk.END))

window = tk.Tk()
window.wm_state('zoomed')
window.title("Coletar Subdomínios")

instrucoes_label = Label(window, text="Digite o nome do WebSite", font=("Arial", 12))
instrucoes_label.grid(row=0, column=0, padx=5, pady=5, columnspan=2)

entry = tk.Entry(window, width=40, font=("TkDefaultFont", 12, "bold"))
entry.grid(row=1, column=0, padx=5, pady=5, columnspan=2)

button = tk.Button(window, text="Coletar Informações", command=exibir_resultados, bg="#0cf2e3", font=("TkDefaultFont", 11, "bold"))
button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

save_button = tk.Button(window, text="Salvar", command=salvar_arquivo, bg="#1be305", font=("TkDefaultFont", 11, "bold"))
save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

mensagem_label = Label(window, text="", font=("Arial", 12, "bold"))
mensagem_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

result_frame = tk.Frame(window)
result_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=2)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=100, height=40, font=("Arial", 12))
result_text.pack(padx=205, pady=5)

window.mainloop()
