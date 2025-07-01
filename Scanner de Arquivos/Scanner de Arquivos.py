import os
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
import threading

resultados = []

def contar_arquivos(pasta):
    total = 0
    for _, _, files in os.walk(pasta):
        total += len(files)
    return total

def buscar_arquivos_thread(ano_filtro, pasta):
    tree.delete(*tree.get_children())
    resultados.clear()

    total_arquivos = contar_arquivos(pasta)
    if total_arquivos == 0:
        messagebox.showinfo("Aviso", "Nenhum arquivo encontrado.")
        return

    progresso["maximum"] = total_arquivos
    progresso["value"] = 0
    janela.update_idletasks()

    contador = 0
    for root, dirs, files in os.walk(pasta):
        for nome_arquivo in files:
            try:
                caminho = os.path.join(root, nome_arquivo)
                p = Path(caminho)
                data_mod = datetime.fromtimestamp(p.stat().st_mtime)
                data_criacao = datetime.fromtimestamp(p.stat().st_ctime)

                if data_criacao.year >= ano_filtro:
                    valores = (
                        nome_arquivo,
                        data_criacao.strftime("%Y-%m-%d"),
                        data_mod.strftime("%Y-%m-%d"),
                        caminho
                    )
                    tree.insert('', 'end', values=valores)
                    resultados.append(valores)
            except Exception as e:
                print(f"Erro com arquivo: {caminho} - {e}")

            contador += 1
            progresso["value"] = contador
            janela.update_idletasks()

    messagebox.showinfo("Concluído", f"{len(resultados)} arquivos listados.")

def buscar_arquivos():
    entrada = simpledialog.askstring("Ano", "Filtrar arquivos criados a partir de qual ano? (ex: 2000)")
    if not entrada:
        return

    try:
        ano_filtro = int(entrada)
        if ano_filtro < 1900 or ano_filtro > 3000:
            raise ValueError
    except ValueError:
        messagebox.showerror("Erro", "Ano inválido. Digite algo como 2000, 2024, etc.")
        return

    pasta = filedialog.askdirectory(title="Selecione a pasta para escanear")
    if not pasta:
        return

    thread = threading.Thread(target=buscar_arquivos_thread, args=(ano_filtro, pasta), daemon=True)
    thread.start()

def salvar_txt():
    if not resultados:
        messagebox.showwarning("Aviso", "Nenhum dado para salvar.")
        return

    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de texto", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            for item in resultados:
                linha = f"Nome: {item[0]} | Criado: {item[1]} | Modificado: {item[2]} | Caminho: {item[3]}\n"
                f.write(linha)
        messagebox.showinfo("Sucesso", f"Arquivo salvo em {caminho}")

# GUI
janela = tk.Tk()
janela.title("Scanner de Arquivos")

# Botões superiores
frame_top = tk.Frame(janela)
frame_top.pack(pady=10)

tk.Button(frame_top, text="Selecionar Pasta e Filtrar", command=buscar_arquivos, bg="#05fc4f").pack(side="left", padx=10)
tk.Button(frame_top, text="Salvar como TXT", command=salvar_txt, bg="#fc8c03").pack(side="left", padx=10)

# Barra de progresso
progresso = ttk.Progressbar(janela, length=800, mode='determinate')
progresso.pack(pady=5)

# Frame da tabela com scrollbar
frame_tabela = tk.Frame(janela)
frame_tabela.pack(fill='both', expand=True, padx=10, pady=5)

colunas = ("Nome", "Criado em", "Modificado em", "Caminho completo")
tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings')

for col in colunas:
    tree.heading(col, text=col)
    tree.column(col, width=150 if col != "Caminho completo" else 400)

scrollbar_vertical = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar_vertical.set)

scrollbar_vertical.pack(side="right", fill="y")
tree.pack(side="left", fill="both", expand=True)

janela.geometry("1000x650")
janela.state("zoomed")
janela.mainloop()
