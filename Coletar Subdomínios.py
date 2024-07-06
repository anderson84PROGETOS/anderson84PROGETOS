import requests
import json
import tkinter as tk
from tkinter import scrolledtext, Label, filedialog, messagebox
from tkinter.ttk import Progressbar  # Importe Progressbar do ttk
import threading

def coletar_informacoes(alvo, progress_bar, info_text):
    req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))
    dados = json.loads(req.text)
    subdominios = set()
    total_subdominios = len(dados)
    
    for idx, value in enumerate(dados, 1):
        subdominios.add(value['name_value'])
        # Atualiza a barra de progresso
        atualizar_barra_progresso(idx, total_subdominios, progress_bar)
        
    # Insere a mensagem de conclusão
    info_text.config(state=tk.NORMAL)
    info_text.insert(tk.END, "\n\n\nProcesso de Enumeração concluído 💯\n")
    info_text.config(state=tk.DISABLED)

    return list(subdominios)

def atualizar_barra_progresso(current_idx, total_subdominios, progress_bar):
    progress = current_idx / total_subdominios * 100
    progress_bar['value'] = progress
    window.update()

def atualizar_progresso_thread(alvo, progress_bar, info_text):
    def thread_func():
        resultados = coletar_informacoes(alvo, progress_bar, info_text)
        exibir_resultados_na_gui(resultados)
    
    thread = threading.Thread(target=thread_func)
    thread.start()

def exibir_resultados_na_gui(resultados):
    result_text.delete('1.0', tk.END)
    for resultado in resultados:
        result_text.insert(tk.END, resultado + '\n')
    mostrar_mensagem(len(resultados))
    button.config(state=tk.NORMAL)  # Reativa o botão após terminar

def exibir_resultados():
    alvo = entry.get().rstrip()
    button.config(state=tk.DISABLED)  # Desativa o botão durante o processamento
    progress_bar['value'] = 0  # Reinicia a barra de progresso
    info_text.config(state=tk.DISABLED)
    info_text.delete('1.0', tk.END)  # Limpa a caixa de texto de informações
    atualizar_progresso_thread(alvo, progress_bar, info_text)

def mostrar_mensagem(numero_subdominios):
    mensagem = f"Foram encontrados {numero_subdominios} subdomínios únicos."
    mensagem_label.config(text=mensagem)

def salvar_arquivo():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(result_text.get("1.0", tk.END))

        messagebox.showinfo("Arquivo Salvo", "Resultados salvos com sucesso!")

window = tk.Tk()
window.wm_state('zoomed')
window.title("Coletar Subdomínios")

instrucoes_label = Label(window, text="Digite o nome do WebSite", font=("Arial", 12))
instrucoes_label.grid(row=0, column=0, padx=5, pady=5, columnspan=2)

entry = tk.Entry(window, width=30, font=("TkDefaultFont", 12, "bold"))
entry.grid(row=1, column=0, padx=5, pady=5, columnspan=2)

button = tk.Button(window, text="Coletar Informações", command=exibir_resultados, bg="#0cf2e3", font=("TkDefaultFont", 11, "bold"))
button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

save_button = tk.Button(window, text="Salvar", command=salvar_arquivo, bg="#1be305", font=("TkDefaultFont", 11, "bold"))
save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Barra de progresso usando Progressbar do ttk
progress_bar = Progressbar(window, orient=tk.HORIZONTAL, length=260, mode='determinate')
progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

mensagem_label = Label(window, text="", font=("Arial", 12, "bold"))
mensagem_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

result_frame = tk.Frame(window)
result_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=2)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=100, height=38, font=("Arial", 12))
result_text.pack(padx=205, pady=5)

# Caixa de texto para informações
info_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=100, height=10, font=("Arial", 12))
info_text.grid(row=7, column=0, columnspan=2, padx=5, pady=50)
info_text.config(state=tk.DISABLED)

window.mainloop()
