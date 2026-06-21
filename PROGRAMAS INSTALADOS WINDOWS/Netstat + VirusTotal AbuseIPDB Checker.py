import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from datetime import datetime

def get_selected_ip():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Aviso", "Selecione uma conexão na tabela.")
        return None

    item = tree.item(selected[0])
    valores = item["values"]
    foreign_address = str(valores[3])

    if foreign_address.startswith("["):           # IPv6
        ip = foreign_address.split("]")[0].replace("[", "")
    elif ":" in foreign_address:                  # IPv4
        ip = foreign_address.rsplit(":", 1)[0]
    else:
        ip = foreign_address

    return ip


def abrir_virustotal():
    ip = get_selected_ip()
    if ip:
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")
        mensagem = f"VirusTotal aberto para: {ip}"
        lbl_contador.config(text=mensagem, fg="#0b63e6")
        lbl_status.config(text=mensagem)


def abrir_abuseipdb():
    ip = get_selected_ip()
    if ip:
        webbrowser.open(f"https://www.abuseipdb.com/check/{ip}")
        mensagem = f"AbuseIPDB aberto para: {ip}"
        lbl_contador.config(text=mensagem, fg="#D35A0A")
        lbl_status.config(text=mensagem)


def salvar_resultados():
    if not tree.get_children():
        messagebox.showwarning("Aviso", "Não há dados para salvar. Atualize primeiro.")
        return

    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        initialfile=f"conexoes_netstat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
   
    if not arquivo:
        return

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=== RELATÓRIO DE CONEXÕES ESTABELECIDAS ===\n\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 150 + "\n\n")
           
            f.write(f"{'#':<4} {'Proto':<10} {'Local Address':<60} {'Foreign Address':<50} {'State':<12} {'PID':<8}\n")
            f.write("-" * 150 + "\n")
           
            for item in tree.get_children():
                valores = tree.item(item)["values"]
                linha = f"{valores[0]:<4} {valores[1]:<10} {valores[2]:<60} {valores[3]:<50} {valores[4]:<12} {valores[5]:<8}\n"
                f.write(linha)
           
            f.write("\n" + "=" * 150 + "\n")
            f.write(f"Total de conexões: {len(tree.get_children())}\n")

        mensagem = f"Resultados salvos com sucesso!"
        lbl_contador.config(text=mensagem, fg="#28a745")
        lbl_status.config(text=f"Arquivo salvo em: {arquivo}")
        messagebox.showinfo("Sucesso", f"Arquivo salvo!\n\n{arquivo}")

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar:\n{str(e)}")


def atualizar():
    for item in tree.get_children():
        tree.delete(item)

    try:
        resultado = subprocess.check_output(
            "netstat -ano | findstr ESTABLISHED",
            shell=True,
            text=True,
            encoding="cp850",
            errors="ignore"
        ).strip()

        contador = 0
        for linha in resultado.splitlines():
            partes = linha.split()
            if len(partes) >= 5:
                proto = partes[0]
                local = partes[1]
                foreign = partes[2]
                state = partes[3]
                pid = partes[4] if len(partes) > 4 else ""

                tree.insert("", "end", values=(contador + 1, proto, local, foreign, state, pid))
                contador += 1

        lbl_contador.config(text=f"{contador} Conexões Encontradas", fg="#195C05")
        lbl_status.config(text="Atualização concluída com sucesso")

    except Exception as e:
        lbl_contador.config(text="Erro ao atualizar conexões", fg="red")
        messagebox.showerror("Erro", f"Erro ao atualizar:\n{str(e)}")


# ==========================
# JANELA PRINCIPAL
# ==========================
root = tk.Tk()
root.title("Netstat + VirusTotal / AbuseIPDB Checker")
root.geometry("1250x720")
root.state("zoomed")

# ==========================
# BOTÕES SUPERIORES
# ==========================
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=8)

tk.Button(
    top_frame, text="🔄 Atualizar Conexões", command=atualizar,
    bg="#0AEC7B", fg="black", font=("Arial", 10, "bold"), width=20
).pack(side="left", padx=5)

tk.Button(
    top_frame, text="🌐 VirusTotal", command=abrir_virustotal,
    bg="#4994f7", fg="black", font=("Arial", 10, "bold"), width=18
).pack(side="left", padx=5)

tk.Button(
    top_frame, text="🌐 AbuseIPDB", command=abrir_abuseipdb,
    bg="#f34b08", fg="black", font=("Arial", 10, "bold"), width=18
).pack(side="left", padx=5)

tk.Button(
    top_frame, text="💾 Salvar Resultados (.txt)", command=salvar_resultados,
    bg="#f3a908", fg="black", font=("Arial", 10, "bold"), width=22
).pack(side="left", padx=5)

# ==========================
# LABEL ABAIXO DOS BOTÕES
# ==========================
lbl_contador = tk.Label(
    root,
    text="0 conexões encontradas",
    font=("Arial", 11, "bold"),
    fg="#0078D7",
    bg="#f0f0f0",
    pady=8
)
lbl_contador.pack(fill="x", padx=10, pady=(0, 8))

# ==========================
# FRAME PARA TABELA + SCROLLBAR
# ==========================
table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=10, pady=5)

# TABELA
columns = ("#", "Proto", "Local Address", "Foreign Address", "State", "PID")
tree = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.column("#", width=50, anchor="center")
tree.column("Proto", width=80, anchor="center")
tree.column("Local Address", width=320)
tree.column("Foreign Address", width=320)
tree.column("State", width=130, anchor="center")
tree.column("PID", width=80, anchor="center")

tree.pack(side="left", fill="both", expand=True)

# SCROLLBAR (agora bem posicionado à direita)
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")

tree.configure(yscrollcommand=scrollbar.set)

# ==========================
# BARRA DE STATUS INFERIOR
# ==========================
lbl_status = tk.Label(root, text="Pronto - Clique em Atualizar",
                     anchor="w", relief="sunken", bg="#e0e0e0")
lbl_status.pack(side="bottom", fill="x")

# ==========================
# INICIALIZAÇÃO
# ==========================
atualizar()
root.mainloop()
