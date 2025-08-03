import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import time

wordlist = []
dominio_base = ""
subdominios_inseridos = set()
parar_flag = False

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def buscar_certificados(dominio):
    try:
        url = f"https://crt.sh/?q={dominio}&output=json"
        resposta = requests.get(url, headers=HEADERS, timeout=10)
        certificados = resposta.json()
        return certificados
    except:
        return []

def atualizar_tabela(certificados):
    for cert in certificados:
        cn = cert.get("common_name", "")
        if cn in subdominios_inseridos:
            continue
        subdominios_inseridos.add(cn)
        not_before = cert.get("not_before", "")
        not_after = cert.get("not_after", "")
        issuer = cert.get("issuer_name", "")
        tree.insert("", "end", values=(cn, not_before, not_after, issuer))

def carregar_wordlist():
    global wordlist
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos de texto", "*.txt")])
    if not caminho:
        return
    try:
        with open(caminho, 'r', encoding='utf-8') as file:
            wordlist = [linha.strip() for linha in file if linha.strip()]
        lbl_status.config(text=f"Wordlist carregada com {len(wordlist)} entradas.")
        btn_escanear.config(state="normal")
        entrada_dominio.config(state="normal")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler wordlist: {e}")

def escanear_subdominios():
    global dominio_base, subdominios_inseridos, parar_flag
    dominio_base = entrada_dominio.get().strip()
    if not dominio_base:
        messagebox.showwarning("Atenção", "Digite o domínio base.")
        return

    parar_flag = False
    subdominios_inseridos.clear()
    tree.delete(*tree.get_children())
    btn_escanear.config(state="disabled")
    btn_stop.config(state="normal")
    barra_progresso["value"] = 0
    barra_progresso.start()
    threading.Thread(target=processar_subdominios).start()

def processar_subdominios():
    total = len(wordlist)
    for i, palavra in enumerate(wordlist):
        if parar_flag:
            lbl_status.config(text="Varredura interrompida pelo usuário.")
            break
        subdominio = f"{palavra}.{dominio_base}"
        certificados = buscar_certificados(subdominio)
        if certificados:
            atualizar_tabela(certificados)
        barra_progresso["value"] = ((i + 1) / total) * 100
        lbl_status.config(text=f"Progresso: {i+1}/{total} - {subdominio}")
        time.sleep(0.2)

    barra_progresso.stop()
    btn_escanear.config(state="normal")
    btn_stop.config(state="disabled")
    if not parar_flag:
        lbl_status.config(text="Varredura concluída!")

def parar_escanear():
    global parar_flag
    parar_flag = True
    btn_stop.config(state="disabled")

def salvar_resultados():
    if not tree.get_children():
        messagebox.showinfo("Info", "Nenhum resultado para salvar.")
        return

    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de texto", "*.txt")])
    if not caminho:
        return

    try:
        with open(caminho, "w", encoding="utf-8") as file:
            file.write(f"{'Sub Domínio'.ljust(65)}{'Válido De'.ljust(30)}{'Válido Até'.ljust(30)}Emissor\n\n")
            for item in tree.get_children():
                valores = tree.item(item)["values"]
                common_name = str(valores[0]).ljust(65)
                not_before = str(valores[1]).ljust(30)
                not_after = str(valores[2]).ljust(30)
                issuer = str(valores[3])
                linha = f"{common_name}{not_before}{not_after}{issuer}"
                file.write(linha + "\n")
        messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")

# GUI
janela = tk.Tk()
janela.title("Consulta de Subdomínios")
janela.geometry("1280x1024")

frame_busca = tk.Frame(janela)
frame_busca.pack(pady=10)

btn_wordlist = tk.Button(frame_busca, text="Selecionar wordlist.txt", command=carregar_wordlist, bg="#03fcf0", fg="black")
btn_wordlist.pack(side=tk.LEFT, padx=5)

tk.Label(frame_busca, text=" Domínio base").pack(side=tk.LEFT)
entrada_dominio = tk.Entry(frame_busca, width=40, state="disabled")
entrada_dominio.pack(side=tk.LEFT, padx=5)

btn_escanear = tk.Button(frame_busca, text="Escanear", command=escanear_subdominios, state="disabled", bg="#03fc62", fg="black")
btn_escanear.pack(side=tk.LEFT, padx=5)

btn_stop = tk.Button(frame_busca, text="Parar", command=parar_escanear, state="disabled", bg="#fc0307", fg="black")
btn_stop.pack(side=tk.LEFT, padx=5)

btn_salvar = tk.Button(frame_busca, text="Salvar resultados", command=salvar_resultados, bg="#fc9d03", fg="black")
btn_salvar.pack(side=tk.LEFT, padx=5)

barra_progresso = ttk.Progressbar(janela, mode="determinate", length=600)
barra_progresso.pack(pady=10)

lbl_status = tk.Label(janela, text="Nenhuma wordlist carregada.")
lbl_status.pack()

frame_tabela = tk.Frame(janela)
frame_tabela.pack(pady=10, fill=tk.BOTH, expand=True)

colunas = ("Sub Domínio", "Válido De", "Válido Até", "Emissor")
tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=40)

for col in colunas:
    tree.heading(col, text=col)
    tree.column(col, width=145, anchor="w")

scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

janela.mainloop()
