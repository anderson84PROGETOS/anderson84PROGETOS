# =========================================================
# MONITOR DE CONEXÕES DE REDE + VIRUSTOTAL + CAMINHO APP
# Pesquisar
# DUPLO CLIQUE:
# 1º clique duplo = abre VirusTotal
# 2º clique duplo na coluna CAMINHO = abre pasta do app
# =========================================================

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import subprocess
import psutil
from datetime import datetime
from tkinter import filedialog

# =========================================================
# JANELA
# =========================================================
root = tk.Tk()
root.title("Netstat Monitor de Conexões + VirusTotal + Caminho")
root.geometry("1700x780")
root.state("zoomed")
root.configure(bg="#1e1e1e")

# =========================================================
# ESTILO
# =========================================================
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#252526",
    foreground="white",
    fieldbackground="#252526",
    rowheight=28,
    font=("Consolas", 10)
)

style.configure(
    "Treeview.Heading",
    background="#00ff88",
    foreground="black",
    font=("Segoe UI", 10, "bold")
)

style.map(
    "Treeview",
    background=[("selected", "#094771")]
)

# =========================================================
# FRAME PRINCIPAL
# =========================================================
frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# =========================================================
# COLUNAS
# =========================================================
columns = (
    "processo",
    "pid",
    "ip",
    "porta",
    "tipo",
    "status",
    "memoria",
    "criado",
    "caminho"
)

arvore = ttk.Treeview(
    frame,
    columns=columns,
    show="headings"
)

# =========================================================
# CABEÇALHO
# =========================================================
for col in columns:
    arvore.heading(col, text=col.upper())

# =========================================================
# TAMANHO COLUNAS
# =========================================================
arvore.column("processo", width=220)
arvore.column("pid", width=80)
arvore.column("ip", width=300)
arvore.column("porta", width=80)
arvore.column("tipo", width=80)
arvore.column("status", width=120)
arvore.column("memoria", width=120)
arvore.column("criado", width=170)
arvore.column("caminho", width=600)

# =========================
# SCROLLBAR VERDE
# =========================
style.configure(
    "Vertical.TScrollbar",
    background="#00ff88",
    troughcolor="#1e1e1e",
    bordercolor="#1e1e1e",
    arrowcolor="black",
    darkcolor="#00cc66",
    lightcolor="#00ff88"
)

style.configure(
    "Horizontal.TScrollbar",
    background="#00ff88",
    troughcolor="#1e1e1e",
    bordercolor="#1e1e1e",
    arrowcolor="black",
    darkcolor="#00cc66",
    lightcolor="#00ff88"
)

# =========================================================
# SCROLLBARS
# =========================================================
scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=arvore.yview, style="Vertical.TScrollbar")
scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=arvore.xview, style="Horizontal.TScrollbar")

arvore.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)

scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

arvore.pack(fill=tk.BOTH, expand=True)

# =========================================================
# LISTA GLOBAL
# =========================================================
dados_conexoes = []

# =========================================================
# FUNÇÕES
# =========================================================
def bytes_para_mb(valor):
    return f"{valor / 1024 / 1024:.2f} MB"


def detectar_tipo_ip(ip):
    if ":" in ip:
        return "IPv6"
    return "IPv4"


# =========================================================
# ABRIR VIRUSTOTAL
# =========================================================
def abrir_virustotal(ip):

    if ip == "N/A":
        return

    url = f"https://www.virustotal.com/gui/ip-address/{ip}"
    webbrowser.open(url)


# =========================================================
# ABRIR PASTA
# =========================================================
def abrir_pasta(caminho):

    if caminho == "N/A":
        messagebox.showwarning(
            "Caminho inválido",
            "Não foi possível localizar a pasta."
        )
        return

    try:

        pasta = os.path.dirname(caminho)

        subprocess.Popen(f'explorer "{pasta}"')

    except Exception as erro:

        messagebox.showerror(
            "Erro",
            f"Erro ao abrir pasta:\n{erro}"
        )


# =========================================================
# PESQUISA
# =========================================================
def pesquisar():

    termo = entrada_pesquisa.get().lower().strip()

    # limpa tabela
    for item in arvore.get_children():
        arvore.delete(item)

    # mostra tudo
    if termo == "":
        for item in dados_conexoes:
            arvore.insert("", tk.END, values=item)
        return

    # filtra
    for item in dados_conexoes:

        texto = " ".join(str(campo).lower() for campo in item)

        if termo in texto:
            arvore.insert("", tk.END, values=item)


# =========================================================
# CARREGAR CONEXÕES
# =========================================================
def carregar_conexoes():

    global dados_conexoes

    # limpa tabela
    for item in arvore.get_children():
        arvore.delete(item)

    dados_conexoes = []

    conexoes = psutil.net_connections(kind='inet')

    for conn in conexoes:

        try:

            pid = conn.pid

            if pid:

                processo = psutil.Process(pid)

                nome = processo.name()

                memoria = bytes_para_mb(
                    processo.memory_info().rss
                )

                criado = datetime.fromtimestamp(
                    processo.create_time()
                ).strftime('%d/%m/%Y %H:%M:%S')

                try:
                    caminho = processo.exe()

                except Exception:
                    caminho = "N/A"

            else:

                nome = "Sistema"
                memoria = "N/A"
                criado = "N/A"
                caminho = "N/A"

        except Exception:

            nome = "Acesso Negado"
            memoria = "N/A"
            criado = "N/A"
            caminho = "N/A"

        # =========================
        # IP / PORTA
        # =========================
        try:

            ip = conn.laddr.ip
            porta = conn.laddr.port

        except Exception:

            ip = "N/A"
            porta = "N/A"

        tipo = detectar_tipo_ip(ip)

        status = conn.status if conn.status else "N/A"

        dados = (
            nome,
            pid,
            ip,
            porta,
            tipo,
            status,
            memoria,
            criado,
            caminho
        )

        dados_conexoes.append(dados)

        arvore.insert(
            "",
            tk.END,
            values=dados
        )


# =========================================================
# DUPLO CLIQUE
# =========================================================
def clique_duplo(event):

    item = arvore.selection()

    if not item:
        return

    item = item[0]

    valores = arvore.item(item, "values")

    coluna = arvore.identify_column(event.x)

    # coluna IP
    if coluna == "#3":

        ip = valores[2]

        if ip == "N/A":

            messagebox.showwarning(
                "IP inválido",
                "Não foi possível abrir o VirusTotal."
            )
            return

        abrir_virustotal(ip)

    # coluna CAMINHO
    elif coluna == "#9":

        caminho = valores[8]

        abrir_pasta(caminho)


arvore.bind("<Double-1>", clique_duplo)

# =========================================================
# FRAME BOTÕES
# =========================================================
frame_botoes = tk.Frame(root, bg="#1e1e1e")
frame_botoes.pack(fill=tk.X, padx=10, pady=5)

# =========================================================
# BOTÃO ATUALIZAR
# =========================================================
btn_atualizar = tk.Button(
    frame_botoes,
    text="Atualizar Conexões",
    command=carregar_conexoes,
    bg="#00ff88",
    fg="black",
    activebackground="#00cc66",
    activeforeground="black",
    font=("Segoe UI", 10, "bold"),
    padx=15,
    pady=8,
    relief=tk.FLAT,
    cursor="hand2"
)

btn_atualizar.pack(side=tk.LEFT, padx=5)

# =========================================================
# CAMPO PESQUISA
# =========================================================
entrada_pesquisa = tk.Entry(
    frame_botoes,
    font=("Segoe UI", 11),
    width=40,
    bg="#252526",
    fg="white",
    insertbackground="white",
    relief=tk.FLAT
)

entrada_pesquisa.pack(side=tk.LEFT, padx=10, ipady=6)

# =========================================================
# BOTÃO PESQUISAR
# =========================================================
btn_pesquisar = tk.Button(
    frame_botoes,
    text="Pesquisar Tudo",
    command=pesquisar,
    bg="#ffd166",
    fg="black",
    activebackground="#ffb703",
    activeforeground="black",
    font=("Segoe UI", 10, "bold"),
    padx=15,
    pady=8,
    relief=tk.FLAT,
    cursor="hand2"
)

btn_pesquisar.pack(side=tk.LEFT, padx=5)

# =========================================================
# LABEL
# =========================================================
info = tk.Label(
    root,
    text=(
        "Duplo clique na coluna IP = VirusTotal | "
        "Duplo clique na coluna CAMINHO = abrir pasta do aplicativo"
    ),
    bg="#1e1e1e",
    fg="#dcdcaa",
    font=("Segoe UI", 10)
)

info.pack(pady=5)

# =========================================================
# SALVAR EM TXT
# =========================================================
def salvar_txt():

    if not dados_conexoes:

        messagebox.showwarning(
            "Sem dados",
            "Não há conexões para salvar."
        )
        return

    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo TXT", "*.txt")],
        title="Salvar relatório"
    )

    if not arquivo:
        return

    try:

        with open(arquivo, "w", encoding="utf-8") as f:

            f.write("=" * 180 + "\n")
            f.write("RELATÓRIO DE CONEXÕES DE REDE\n")
            f.write("=" * 180 + "\n\n")

            for item in dados_conexoes:

                f.write(f"PROCESSO : {item[0]}\n")
                f.write(f"PID      : {item[1]}\n")
                f.write(f"IP       : {item[2]}\n")
                f.write(f"PORTA    : {item[3]}\n")
                f.write(f"TIPO     : {item[4]}\n")
                f.write(f"STATUS   : {item[5]}\n")
                f.write(f"MEMÓRIA  : {item[6]}\n")
                f.write(f"CRIADO   : {item[7]}\n")
                f.write(f"CAMINHO  : {item[8]}\n")

                f.write("-" * 180 + "\n")

        messagebox.showinfo(
            "Salvo",
            "Relatório salvo com sucesso!"
        )

    except Exception as erro:

        messagebox.showerror(
            "Erro",
            f"Erro ao salvar:\n{erro}"
        )

# =========================================================
# BOTÃO SALVAR TXT
# =========================================================
btn_salvar = tk.Button(
    frame_botoes,
    text="Salvar Tudo TXT",
    command=salvar_txt,
    bg="#f74012",
    fg="black",
    activebackground="#eb371f",
    activeforeground="white",
    font=("Segoe UI", 10, "bold"),
    padx=15,
    pady=8,
    relief=tk.FLAT,
    cursor="hand2"
)

btn_salvar.pack(side=tk.LEFT, padx=5)

# =========================================================
# PRIMEIRA CARGA
# =========================================================
carregar_conexoes()

# =========================================================
# LOOP
# =========================================================
root.mainloop()
