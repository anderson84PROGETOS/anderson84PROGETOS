import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests

def buscar_subdominios():
    dominio_alvo = entry_dominio_alvo.get()
    api_url = f"https://crt.sh/?q=%.{dominio_alvo}&output=json"
    resultado = requests.get(api_url)
    
    if resultado.status_code == 200:
        subdominios = [item['name_value'] for item in resultado.json()]
        
        nome_arquivo = entry_nome_arquivo.get()
        if nome_arquivo:
            with open(nome_arquivo, "w") as arquivo:
                total_subdominios = len(subdominios)
                progress_var.set(0)
                for i, subdominio in enumerate(subdominios, start=1):
                    arquivo.write(subdominio + "\n")
                    progress_var.set((i / total_subdominios) * 100)
                    root.update_idletasks()
            
            with open(nome_arquivo, "r") as arquivo:
                linhas_unicas = set(arquivo.readlines())
            
            with open(nome_arquivo, "w") as arquivo:
                arquivo.writelines(linhas_unicas)
            
            text_conteudo.delete(1.0, tk.END)
            with open(nome_arquivo, "r") as arquivo:
                conteudo = arquivo.read()
                text_conteudo.insert(tk.END, conteudo)
            num_linhas = len(conteudo.split('\n')) - 1
            label_num_linhas.config(text="Número de subdomínios encontrados: " + str(num_linhas))
    else:
        messagebox.showerror("Erro", "Falha ao buscar subdomínios. Verifique o domínio alvo e sua conexão com a internet.")

root = tk.Tk()
root.wm_state('zoomed')
root.title("Busca de Subdomínios")

label_dominio_alvo = tk.Label(root, text="Digite o domínio alvo: Exemplo: google.com")
entry_dominio_alvo = tk.Entry(root, width=50)
label_nome_arquivo = tk.Label(root, text="Nome do arquivo: Exemplo: arquivo.txt")
entry_nome_arquivo = tk.Entry(root, width=50)
button_buscar = tk.Button(root, text="Buscar Subdomínios", command=buscar_subdominios)

text_conteudo = tk.Text(root, height=40, width=150)
label_num_linhas = tk.Label(root, text="Número de subdomínios encontrados: ")
progress_var = tk.DoubleVar()

progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=668, mode='determinate', variable=progress_var)
progress_bar.place(x=300, y=800)

label_dominio_alvo.pack()
entry_dominio_alvo.pack()
label_nome_arquivo.pack()
entry_nome_arquivo.pack()
button_buscar.pack()
text_conteudo.pack()
label_num_linhas.pack()

root.mainloop()
