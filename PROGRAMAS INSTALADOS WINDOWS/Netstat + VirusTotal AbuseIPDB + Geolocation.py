import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from datetime import datetime
import socket
import requests
import threading
import queue

# ==================== CACHE ====================
ip_cache = {}

def get_ip_info(ip):
    if ip in ip_cache:
        return ip_cache[ip]

    try:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = ip

        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,regionName", 
                                  timeout=5)
            data = response.json()
            country = data.get("country", "N/A")
            region = data.get("regionName", "N/A")
        except:
            country = "N/A"
            region = "N/A"

        info = (hostname, country, region)
        ip_cache[ip] = info
        return info
    except:
        return (ip, "N/A", "N/A")


def get_selected_ip():
    selected = tree.selection()
    if not selected:
        return None
    item = tree.item(selected[0])
    valores = item["values"]
    foreign_address = str(valores[3])

    if foreign_address.startswith("["):
        ip = foreign_address.split("]")[0].replace("[", "")
    elif ":" in foreign_address:
        ip = foreign_address.rsplit(":", 1)[0]
    else:
        ip = foreign_address
    return ip


def atualizar_status_selecionado(event=None):
    ip = get_selected_ip()
    if ip:
        hostname, country, region = get_ip_info(ip)
        lbl_selected_ip.config(text=f"IP: {ip}")
        lbl_selected_host.config(text=f"Host: {hostname}")
        lbl_selected_country.config(text=f"País: {country}")
        lbl_selected_state.config(text=f"Estado: {region}")
    else:
        lbl_selected_ip.config(text="IP: Nenhum selecionado")
        lbl_selected_host.config(text="Host: -")
        lbl_selected_country.config(text="País: -")
        lbl_selected_state.config(text="Estado: -")


def abrir_virustotal():
    ip = get_selected_ip()
    if ip:
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")
        mensagem = f"VirusTotal aberto para: {ip}"
        lbl_contador.config(text=mensagem, fg="#0b63e6")       

def abrir_abuseipdb():
    ip = get_selected_ip()
    if ip:
        webbrowser.open(f"https://www.abuseipdb.com/check/{ip}")
        mensagem = f"AbuseIPDB aberto para: {ip}"
        lbl_contador.config(text=mensagem, fg="#D35A0A")


def salvar_resultados():
    if not tree.get_children():
        messagebox.showwarning("Aviso", "Não há dados para salvar. Atualize primeiro.")
        return

    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        initialfile=f"conexoes_netstat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    if not arquivo:
        return

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("=== RELATÓRIO DE CONEXÕES ESTABELECIDAS ===\n\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 260 + "\n\n")
            
            # Formato solicitado
            f.write(
                f"{'#':<5}"
                f"{'Proto':<10}"
                f"{'Local':<60}"
                f"{'Foreign':<50}"
                f"{'Hostname':<50}"
                f"{'Country':<30}"
                f"{'State':<35}"
                f"{'Conn State':<15}"
                f"{'PID':<10}\n"
            )
            f.write("-" * 260 + "\n")
            
            for item in tree.get_children():
                valores = tree.item(item)["values"]
                linha = (
                    f"{str(valores[0]):<5}"
                    f"{str(valores[1]):<10}"
                    f"{str(valores[2]):<60}"
                    f"{str(valores[3]):<50}"
                    f"{str(valores[4]):<50}"
                    f"{str(valores[5]):<30}"
                    f"{str(valores[6]):<35}"
                    f"{str(valores[7]):<15}"
                    f"{str(valores[8]):<10}\n"
                )
                f.write(linha)
           
            f.write("\n" + "=" * 260 + "\n")
            f.write(f"Total de conexões: {len(tree.get_children())}\n")

        lbl_bottom_status.config(text=f"💾 Arquivo salvo com sucesso!", fg="#28a745")
        messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{arquivo}")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")


def atualizar():
    for item in tree.get_children():
        tree.delete(item)

    lbl_bottom_status.config(text="🔄 Atualizando...", fg="#0078D7")
    lbl_contador.config(text="Carregando...")

    try:
        resultado = subprocess.check_output(
            "netstat -ano | findstr ESTABLISHED",
            shell=True,
            text=True,
            encoding="cp850",
            errors="ignore"
        ).strip()

        linhas = [l for l in resultado.splitlines() if l.strip()]

        result_queue = queue.Queue()

        def process_line(linha, idx):
            partes = linha.split()
            if len(partes) >= 5:
                proto = partes[0]
                local = partes[1]
                foreign = partes[2]
                state = partes[3]
                pid = partes[4] if len(partes) > 4 else ""

                if foreign.startswith("["):
                    ip = foreign.split("]")[0].replace("[", "")
                elif ":" in foreign:
                    ip = foreign.rsplit(":", 1)[0]
                else:
                    ip = foreign

                hostname, country, region = get_ip_info(ip)
                result_queue.put((idx+1, proto, local, foreign, hostname, country, region, state, pid))

        threads = [threading.Thread(target=process_line, args=(linha, idx)) for idx, linha in enumerate(linhas)]
        for t in threads: t.start()
        for t in threads: t.join()

        contador = 0
        while not result_queue.empty():
            tree.insert("", "end", values=result_queue.get())
            contador += 1

        lbl_contador.config(text=f"{contador} Conexões Encontradas", fg="#195C05")
        lbl_bottom_status.config(text=f"✅ Atualização concluída - {contador} conexões", fg="#28a745")

    except Exception as e:
        lbl_bottom_status.config(text="❌ Erro na atualização", fg="red")
        messagebox.showerror("Erro", str(e))


# ==================== INTERFACE ====================
root = tk.Tk()
root.title("Netstat + VirusTotal / AbuseIPDB + Geolocation")
root.geometry("1650x820")
root.state("zoomed")

# Top Frame
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=8, padx=10)

tk.Button(top_frame, text="🔄 Atualizar Conexões", command=atualizar,
          bg="#0AEC7B", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=4)

tk.Button(top_frame, text="🌐 VirusTotal", command=abrir_virustotal,
          bg="#4994f7", fg="black", font=("Arial", 10, "bold"), width=18).pack(side="left", padx=4)

tk.Button(top_frame, text="🌐 AbuseIPDB", command=abrir_abuseipdb,
          bg="#f34b08", fg="black", font=("Arial", 10, "bold"), width=18).pack(side="left", padx=4)

tk.Button(top_frame, text="💾 Salvar Resultados", command=salvar_resultados,
          bg="#f3a908", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=4)

lbl_contador = tk.Label(root, text="0 conexões encontradas", 
                        font=("Arial", 12, "bold"), fg="#0078D7", bg="#f0f0f0", pady=8)
lbl_contador.pack(fill="x", padx=10, pady=(0, 6))

# ==================== MAIN AREA ====================
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=5)

# ==================== TABELA ====================

table_frame = tk.Frame(main_frame)
table_frame.pack(side="left", fill="both", expand=True)

columns = (
    "#",
    "Proto",
    "Local Address",
    "Foreign Address",
    "Hostname",
    "Country",
    "State",
    "Conn State",
    "PID"
)

# Frame para Tree + Scrolls
tree_frame = tk.Frame(table_frame)
tree_frame.pack(fill="both", expand=True)

# Scroll Vertical
scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")

# Scroll Horizontal
scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")

tree = ttk.Treeview(
    tree_frame,
    columns=columns,
    show="headings",
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)

scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

for col in columns:
    tree.heading(col, text=col)

# Aumente os tamanhos para forçar barra horizontal
tree.column("#", width=60)
tree.column("Proto", width=100)
tree.column("Local Address", width=350)
tree.column("Foreign Address", width=350)
tree.column("Hostname", width=450)
tree.column("Country", width=200)
tree.column("State", width=280)
tree.column("Conn State", width=180)
tree.column("PID", width=120)

# Grid é melhor para scrollbars
tree.grid(row=0, column=0, sticky="nsew")
scrollbar_y.grid(row=0, column=1, sticky="ns")
scrollbar_x.grid(row=1, column=0, sticky="ew")

tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

tree.bind("<<TreeviewSelect>>", atualizar_status_selecionado)

# ==================== PAINEL LATERAL DIREITO ====================
right_panel = tk.LabelFrame(main_frame, text=" Informações da Seleção ", 
                           font=("Arial", 10, "bold"), padx=10, pady=10, width=320)
right_panel.pack(side="right", fill="y", padx=(10, 0))

lbl_selected_ip = tk.Label(right_panel, text="IP: Nenhum selecionado", anchor="w", font=("Consolas", 10))
lbl_selected_ip.pack(fill="x", pady=4)

lbl_selected_host = tk.Label(right_panel, text="Host: -", anchor="w", font=("Consolas", 10))
lbl_selected_host.pack(fill="x", pady=4)

lbl_selected_country = tk.Label(right_panel, text="País: -", anchor="w", font=("Consolas", 10))
lbl_selected_country.pack(fill="x", pady=4)

lbl_selected_state = tk.Label(right_panel, text="Estado: -", anchor="w", font=("Consolas", 10))
lbl_selected_state.pack(fill="x", pady=4)

tk.Label(right_panel, text="─" * 40, fg="gray").pack(pady=8)

lbl_right_info = tk.Label(right_panel, text="Dica:\nClique em uma linha\npara ver detalhes", 
                         justify="left", fg="gray", font=("Arial", 9))
lbl_right_info.pack(pady=10)

# ==================== BARRA DE STATUS INFERIOR ====================
bottom_frame = tk.Frame(root, bg="#2d2d2d", height=30)
bottom_frame.pack(side="bottom", fill="x")

lbl_bottom_status = tk.Label(bottom_frame, text="Pronto - Clique em Atualizar Conexões", 
                             anchor="w", bg="#2d2d2d", fg="#ffffff", font=("Consolas", 10))
lbl_bottom_status.pack(side="left", padx=12, fill="x", expand=True)

lbl_time = tk.Label(bottom_frame, text=datetime.now().strftime("%d/%m/%Y %H:%M"), 
                    bg="#2d2d2d", fg="#aaaaaa", font=("Consolas", 9))
lbl_time.pack(side="right", padx=12)

# Inicializar
atualizar()
root.mainloop()
