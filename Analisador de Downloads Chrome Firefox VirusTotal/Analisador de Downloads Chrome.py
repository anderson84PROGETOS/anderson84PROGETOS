import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ==================== CONFIGURAÇÕES ====================
PASTA_PADRAO = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Google",
    "Chrome",
    "User Data",
    "Default",
    "Download Service",
    "Files"
)

pasta_atual = PASTA_PADRAO

# Cores
COR_BG = "#2b2b2b"
COR_FG = "#ffffff"
COR_BOTOES = "#007acc"
COR_DELETAR = "#c42b1c"
COR_VERDE = "#00cc66"

def formatar_tamanho(bytes_):
    gb = bytes_ / (1024**3)
    mb = bytes_ / (1024**2)
    kb = bytes_ / 1024

    if gb >= 1:
        return f"{gb:.2f} GB"
    elif mb >= 1:
        return f"{mb:.2f} MB"
    elif kb >= 1:
        return f"{kb:.2f} KB"
    else:
        return f"{bytes_} Bytes"


# ==================== FUNÇÕES ====================
def selecionar_pasta():
    global pasta_atual
    pasta = filedialog.askdirectory()
    if pasta:
        pasta_atual = pasta
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, pasta)
        atualizar_label_pasta()


def atualizar_label_pasta():
    nome_pasta = os.path.basename(pasta_atual) if pasta_atual else "Nenhuma pasta selecionada"
    lbl_pasta.config(text=f"Pasta atual: {nome_pasta}\nCaminho: {pasta_atual}")


def abrir_pasta():
    if os.path.exists(pasta_atual):
        os.startfile(pasta_atual)


def limpar_tabela():
    for item in tree.get_children():
        tree.delete(item)


def configurar_progresso_verde():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("green.Horizontal.TProgressbar",
                    foreground=COR_VERDE,
                    background=COR_VERDE,
                    troughcolor='#555555',
                    thickness=20)


def analisar_pasta():
    limpar_tabela()
    
    # Resetar barra (branca)
    progress_bar['value'] = 0
    style = ttk.Style()
    style.configure("Horizontal.TProgressbar", background='#555555')
    janela.update()

    if not os.path.exists(pasta_atual):
        lbl_status.config(text="❌ Pasta não encontrada!")
        return

    # Ativar cor verde
    configurar_progresso_verde()
    progress_bar.configure(style="green.Horizontal.TProgressbar")

    arquivos = []
    lista_arquivos = [f for f in os.listdir(pasta_atual) if os.path.isfile(os.path.join(pasta_atual, f))]
    total = len(lista_arquivos)

    for i, arquivo in enumerate(lista_arquivos):
        caminho = os.path.join(pasta_atual, arquivo)
        tamanho = os.path.getsize(caminho)
        data = os.path.getmtime(caminho)

        arquivos.append((arquivo, caminho, tamanho, data))

        # Atualiza progresso
        progress = int((i + 1) / total * 100) if total > 0 else 100
        progress_bar['value'] = progress
        janela.update_idletasks()

    # Ordenar por tamanho (maior primeiro)
    arquivos.sort(key=lambda x: x[2], reverse=True)

    for nome, caminho, tamanho, data in arquivos:
        extensao = os.path.splitext(nome)[1]
        tree.insert(
            "", "end",
            values=(
                nome,
                "Arquivo",
                extensao or "-",
                formatar_tamanho(tamanho),
                datetime.fromtimestamp(data).strftime("%d/%m/%Y %H:%M:%S"),
                caminho
            )
        )

    total_bytes = sum(x[2] for x in arquivos)
    lbl_status.config(
        text=f"✅ {len(arquivos)} arquivo(s) encontrados | "
             f"Tamanho Total: {formatar_tamanho(total_bytes)}"
    )
    progress_bar['value'] = 100


def buscar():
    texto = entrada_busca.get().lower().strip()
    if not texto:
        return
    for item in tree.get_children():
        nome = str(tree.item(item)["values"][0]).lower()
        if texto in nome:
            tree.selection_set(item)
            tree.focus(item)
            tree.see(item)
            return


def limpar_busca():
    entrada_busca.delete(0, tk.END)


def excluir_arquivo():
    item = tree.focus()
    if not item:
        messagebox.showwarning("Atenção", "Selecione um arquivo primeiro!")
        return

    dados = tree.item(item)["values"]
    caminho = dados[5]

    if messagebox.askyesno("Confirmação", f"Excluir o arquivo?\n\n{dados[0]}"):
        try:
            os.remove(caminho)
            analisar_pasta()
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))


def excluir_todos():
    if not messagebox.askyesno("⚠️ Confirmação", "Tem certeza que deseja excluir TODOS os arquivos?"):
        return

    count = 0
    for arquivo in os.listdir(pasta_atual):
        caminho = os.path.join(pasta_atual, arquivo)
        if os.path.isfile(caminho):
            try:
                os.remove(caminho)
                count += 1
            except:
                pass

    messagebox.showinfo("Concluído", f"{count} arquivo(s) excluído(s).")
    analisar_pasta()


def salvar_txt():
    destino = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo Texto", "*.txt")]
    )
    if not destino:
        return

    with open(destino, "w", encoding="utf-8") as arq:
        arq.write(f"Pasta analisada: {pasta_atual}\n")
        arq.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        arq.write("="*100 + "\n\n")
        
        for item in tree.get_children():
            linha = tree.item(item)["values"]
            arq.write(" | ".join(map(str, linha)) + "\n")

    messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{destino}")


def abrir_arquivo(event):
    item = tree.focus()
    if not item:
        return
    caminho = tree.item(item)["values"][5]
    if os.path.exists(caminho):
        os.startfile(caminho)


# ==================== INTERFACE ====================
janela = tk.Tk()
janela.title("Analisador de Downloads - Chrome")
janela.geometry("1400x760")
janela.state("zoomed")
janela.configure(bg=COR_BG)

# Label da Pasta Atual (destacado)
lbl_pasta = tk.Label(janela, text="", bg="#1e1e1e", fg="#00ffcc", 
                     font=("Arial", 11, "bold"), anchor="w", justify="left")
lbl_pasta.pack(fill="x", padx=10, pady=8)

# Barra de Progresso
progress_bar = ttk.Progressbar(janela, length=400, mode='determinate')
progress_bar.pack(fill="x", padx=10, pady=5)

# Frame do caminho + botões
frame1 = tk.Frame(janela, bg=COR_BG)
frame1.pack(fill="x", padx=10, pady=5)

entrada_pasta = tk.Entry(frame1, font=("Arial", 10))
entrada_pasta.pack(side="left", fill="x", expand=True, padx=(0, 5))
entrada_pasta.insert(0, pasta_atual)

tk.Button(frame1, text="Selecionar Pasta", command=selecionar_pasta, bg="#444444", fg="white", relief="flat", width=15).pack(side="left", padx=4)
tk.Button(frame1, text="Analisar", command=analisar_pasta, bg=COR_BOTOES, fg="white", relief="flat", font=("Arial", 9, "bold"), width=12).pack(side="left", padx=4)
tk.Button(frame1, text="Abrir Pasta", command=abrir_pasta, bg="#444444", fg="white", relief="flat", width=12).pack(side="left", padx=4)
tk.Button(frame1, text="Salvar TXT", command=salvar_txt, bg="#28a745", fg="white", relief="flat", width=12).pack(side="left", padx=4)

# Busca
frame2 = tk.Frame(janela, bg=COR_BG)
frame2.pack(fill="x", padx=10, pady=5)

tk.Label(frame2, text="Pesquisar:", bg=COR_BG, fg=COR_FG, font=("Arial", 10)).pack(side="left", padx=(0, 5))
entrada_busca = tk.Entry(frame2, font=("Arial", 10))
entrada_busca.pack(side="left", fill="x", expand=True, padx=(0, 5))

tk.Button(frame2, text="Buscar", command=buscar, bg=COR_BOTOES, fg="white", relief="flat").pack(side="left", padx=4)
tk.Button(frame2, text="Limpar", command=limpar_busca, bg="#666666", fg="white", relief="flat").pack(side="left")

# Status
lbl_status = tk.Label(janela, text="", bg=COR_BG, fg="#00ff88", anchor="w", font=("Arial", 10, "bold"))
lbl_status.pack(fill="x", padx=10, pady=5)

# Tabela
colunas = ("Nome", "Tipo", "Extensão", "Tamanho", "Data", "Caminho")
tree = ttk.Treeview(janela, columns=colunas, show="headings")
for col in colunas:
    tree.heading(col, text=col)

tree.column("Nome", width=250)
tree.column("Tipo", width=80)
tree.column("Extensão", width=100)
tree.column("Tamanho", width=90)
tree.column("Data", width=140)
tree.column("Caminho", width=540)

scroll_y = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scroll_y.set)

scroll_y.pack(side="right", fill="y")
tree.pack(fill="both", expand=True, padx=10, pady=5)

tree.bind("<Double-1>", abrir_arquivo)

# Botões inferiores
frame3 = tk.Frame(janela, bg=COR_BG)
frame3.pack(fill="x", padx=10, pady=10)

tk.Button(frame3, text="Excluir Selecionado", command=excluir_arquivo,
          bg=COR_DELETAR, fg="white", relief="flat", font=("Arial", 9, "bold")).pack(side="left", padx=5)
tk.Button(frame3, text="Excluir TODOS os Arquivos", command=excluir_todos,
          bg=COR_DELETAR, fg="white", relief="flat", font=("Arial", 9, "bold")).pack(side="left", padx=5)

# Inicialização
atualizar_label_pasta()
analisar_pasta()

janela.mainloop()
