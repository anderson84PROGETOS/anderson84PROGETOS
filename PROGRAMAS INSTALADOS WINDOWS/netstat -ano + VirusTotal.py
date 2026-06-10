import subprocess
import re
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
import webbrowser
import psutil

VT_URL = "https://www.virustotal.com/gui/ip-address/{}"

# -----------------------------
# Obter caminho completo do processo pelo PID
# -----------------------------
def obter_processo(pid):
    try:
        proc = psutil.Process(int(pid))
        return proc.exe()  # Caminho completo
    except:
        return "Desconhecido"


# -----------------------------
# Ajustar largura das colunas
# -----------------------------
def auto_ajustar_colunas():
    fonte = font.Font()
    for coluna in colunas:
        largura = fonte.measure(coluna)
        for item in tree.get_children():
            valor = str(tree.set(item, coluna))
            largura = max(largura, fonte.measure(valor))
        tree.column(coluna, width=largura + 30)


# -----------------------------
# Carregar conexões
# -----------------------------
def carregar_conexoes():
    for item in tree.get_children():
        tree.delete(item)

    try:
        resultado = subprocess.check_output(
            "netstat -ano",
            shell=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        for linha in resultado.splitlines():
            if linha.strip().startswith(("TCP", "UDP")):
                partes = re.split(r"\s+", linha.strip())
                try:
                    protocolo = partes[0]
                    if protocolo == "TCP":
                        local = partes[1]
                        remoto = partes[2]
                        estado = partes[3]
                        pid = partes[4]
                    else:
                        local = partes[1]
                        remoto = partes[2]
                        estado = ""
                        pid = partes[3]

                    processo = obter_processo(pid)

                    tree.insert(
                        "",
                        "end",
                        values=(protocolo, local, remoto, estado, pid, processo)
                    )
                except:
                    pass

        auto_ajustar_colunas()

    except Exception as erro:
        print("Erro:", erro)


# -----------------------------
# Extrair IP do campo Remoto
# -----------------------------
def extrair_ip(remoto):
    if ":" in remoto:
        ip = remoto.rsplit(":", 1)[0]
    else:
        ip = remoto
    ip = ip.replace("[", "").replace("]", "")
    return ip


# -----------------------------
# Abrir IP no VirusTotal
# -----------------------------
def abrir_virustotal(item=None):
    if not item:
        selection = tree.selection()
        if not selection:
            return
        item = selection[0]

    valores = tree.item(item)["values"]
    remoto = str(valores[2])
    ip = extrair_ip(remoto)

    if ip not in ("0.0.0.0", "*", "::", "127.0.0.1", "::1", "0.0.0.0:0"):
        webbrowser.open(VT_URL.format(ip))


# -----------------------------
# Salvar todas as conexões em TXT
# -----------------------------
def salvar_txt():
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        title="Salvar conexões como..."
    )
   
    if not arquivo:
        return

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=== CONEXÕES DE REDE (netstat) ===\n\n")
            f.write(f"{'Protocolo':<10} {'Local':<30} {'Remoto':<40} {'Estado':<15} {'PID':<8} {'Caminho do Processo'}\n")
            f.write("-" * 150 + "\n")

            for item in tree.get_children():
                valores = tree.item(item)["values"]
                f.write(
                    f"{str(valores[0]):<10} "
                    f"{str(valores[1]):<30} "
                    f"{str(valores[2]):<40} "
                    f"{str(valores[3]):<15} "
                    f"{str(valores[4]):<8} "
                    f"{str(valores[5])}\n"
                )

        tk.messagebox.showinfo("Sucesso", f"Conexões salvas com sucesso em:\n{arquivo}")
    except Exception as e:
        tk.messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")


# -----------------------------
# Menu de contexto (clique direito)
# -----------------------------
def mostrar_menu_contexto(event):
    item = tree.identify_row(event.y)
    if item:
        tree.selection_set(item)

    menu = tk.Menu(root, tearoff=0, bg="#2d2d2d", fg="white")
    menu.add_command(label="🔗 Abrir no VirusTotal", command=lambda: abrir_virustotal())
    menu.tk_popup(event.x_root, event.y_root)


# -----------------------------
# Interface com cores
# -----------------------------
root = tk.Tk()
root.title("netstat -ano + VirusTotal")
root.geometry("1600x700")
root.wm_state("zoomed")
root.configure(bg="#1e1e1e")

style = ttk.Style()
style.theme_use("clam")

# Estilo da Treeview
style.configure("Treeview",
                background="#2d2d2d",
                foreground="#ffffff",
                fieldbackground="#2d2d2d",
                rowheight=30,
                font=("Segoe UI", 10))

style.configure("Treeview.Heading",
                background="#007acc",
                foreground="white",
                font=("Segoe UI", 10, "bold"))

# ==================== SCROLLBARS AZUIS ====================
style.configure("Vertical.TScrollbar",
                background="#007acc",           # Cor principal azul
                troughcolor="#1e1e1e",          # Cor do fundo
                arrowcolor="white",
                bordercolor="#007acc",
                lightcolor="#007acc",
                darkcolor="#007acc")

style.configure("Horizontal.TScrollbar",
                background="#007acc",
                troughcolor="#1e1e1e",
                arrowcolor="white",
                bordercolor="#007acc",
                lightcolor="#007acc",
                darkcolor="#007acc")

style.map("Vertical.TScrollbar",
          background=[('active', '#005a99')],
          arrowcolor=[('active', 'white')])

style.map("Horizontal.TScrollbar",
          background=[('active', '#005a99')],
          arrowcolor=[('active', 'white')])

# Botões
btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(pady=12, padx=10, fill="x")

btn_atualizar = tk.Button(
    btn_frame,
    text="🔄 Atualizar Conexões",
    font=("Segoe UI", 11, "bold"),
    bg="#007acc",
    fg="white",
    activebackground="#005a99",
    relief="flat",
    padx=15,
    pady=8,
    command=carregar_conexoes
)
btn_atualizar.pack(side="left", padx=(0, 10))

btn_salvar = tk.Button(
    btn_frame,
    text="💾 Salvar tudo em .txt",
    font=("Segoe UI", 10, "bold"),
    bg="#28a745",
    fg="white",
    activebackground="#218838",
    relief="flat",
    padx=15,
    pady=8,
    command=salvar_txt
)
btn_salvar.pack(side="left")

# Frame da tabela
table_frame = tk.Frame(root, bg="#1e1e1e")
table_frame.pack(fill="both", expand=True, padx=10, pady=5)

# Scrollbars (com estilo azul)
scroll_y = ttk.Scrollbar(table_frame, orient="vertical", style="Vertical.TScrollbar")
scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", style="Horizontal.TScrollbar")

colunas = ("Protocolo", "Local", "Remoto", "Estado", "PID", "Processo")

tree = ttk.Treeview(
    table_frame,
    columns=colunas,
    show="headings",
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set,
    style="Treeview"
)

scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)

larguras = {
    "Protocolo": 100,
    "Local": 250,
    "Remoto": 280,
    "Estado": 150,
    "PID": 80,
    "Processo": 650
}

for coluna in colunas:
    tree.heading(coluna, text=coluna)
    tree.column(coluna, width=larguras[coluna], minwidth=80, stretch=True)

# Layout (conforme você pediu)
tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

# Eventos
tree.bind("<Double-1>", lambda e: abrir_virustotal())
tree.bind("<Button-3>", mostrar_menu_contexto)

# Inicialização
carregar_conexoes()

root.mainloop()
