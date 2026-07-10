import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import requests
import webbrowser
from datetime import datetime

# ==================== DARK MODE THEME ====================
DARK_BG = "#1e1e2f"
DARK_FG = "#e0e0ff"
ACCENT = "#00ffcc"
ACCENT2 = "#88aaff"
BUTTON_BG = "#00cc88"
BUTTON_FG = "white"
TREE_BG = "#25253a"
TREE_FG = "#e0e0ff"
TREE_SELECTED = "#334455"
HEADER_BG = "#2d2d44"

# Cache de geolocalização
geo_cache = {}

def obter_nome_processo(pid):
    try:
        return psutil.Process(pid).name()
    except:
        return "Desconhecido"

def obter_geolocalizacao(ip):
    if ip == "N/A" or not ip or ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
        return "N/A", "N/A", "N/A", "N/A", "N/A", None, None

    if ip in geo_cache:
        return geo_cache[ip]

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,city,regionName,country,isp,org,lat,lon",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                result = (
                    data.get("city", "Desconhecido"),
                    data.get("regionName", "Desconhecido"),
                    data.get("country", "Desconhecido"),
                    data.get("isp", "N/A"),
                    data.get("org", "N/A"),
                    data.get("lat"),
                    data.get("lon")
                )
                geo_cache[ip] = result
                return result
    except:
        pass

    result = ("Desconhecido", "Desconhecido", "Desconhecido", "N/A", "N/A", None, None)
    geo_cache[ip] = result
    return result


def obter_conexoes():
    conexoes = psutil.net_connections(kind='tcp')
    conexoes_ipv4 = []
    conexoes_ipv6 = []

    for conn in conexoes:
        if conn.status == 'ESTABLISHED':
            local_addr = conn.laddr.ip if conn.laddr else "N/A"
            local_port = conn.laddr.port if conn.laddr else "N/A"
            remote_addr = conn.raddr.ip if conn.raddr else "N/A"
            remote_port = conn.raddr.port if conn.raddr else "N/A"
            owning_process = conn.pid if conn.pid else "N/A"
            process_name = obter_nome_processo(owning_process)

            cidade, estado, pais, isp, org, lat, lon = obter_geolocalizacao(remote_addr)

            row = (
                local_addr, local_port, remote_addr, remote_port, conn.status,
                owning_process, process_name, cidade, estado, pais, isp, org, lat, lon
            )

            if ":" in local_addr or ":" in remote_addr:
                conexoes_ipv6.append(row)
            else:
                conexoes_ipv4.append(row)

    return conexoes_ipv4, conexoes_ipv6


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Conexões TCP + Geolocalização")
        self.root.geometry("1620x860")
        self.root.state("zoomed")
        self.root.configure(bg=DARK_BG)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configurar_estilos()

        # Título
        title_frame = tk.Frame(root, bg=DARK_BG)
        title_frame.pack(pady=12, fill="x")
        tk.Label(title_frame, text="MONITOR DE CONEXÕES TCP + GEOLOCALIZAÇÃO",
                 font=("Courier New", 18, "bold"), fg=ACCENT, bg=DARK_BG).pack()
        tk.Label(title_frame, text="API Gratuita • Cache • BGP.he.net",
                 font=("Arial", 11), fg=ACCENT2, bg=DARK_BG).pack()

        # Botões + Barra de Progresso
        control_frame = tk.Frame(root, bg=DARK_BG)
        control_frame.pack(pady=8, fill="x", padx=12)

        self.scan_button = tk.Button(control_frame, text="🔍 Escanear Agora", font=("Arial", 10, "bold"),
                                     bg=BUTTON_BG, fg="black", padx=20, pady=8,
                                     command=self.iniciar_scan)
        self.scan_button.pack(side="left", padx=8)

        tk.Button(control_frame, text="💾 Salvar Tudo (TXT)", font=("Arial", 10, "bold"),
                  bg="#ffaa00", fg="black", padx=20, pady=8,
                  command=self.salvar_txt).pack(side="left", padx=8)

        self.auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="Auto Refresh (5s)", variable=self.auto_var,
                       bg=DARK_BG, fg="#aaffaa", selectcolor="#334455",
                       font=("Arial", 10), command=self.toggle_auto_refresh).pack(side="left", padx=12)
        # Cor verde
        style = ttk.Style()
        style.theme_use("clam")  # necessário para permitir alterar as cores

        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#d9d9d9",   # cor do fundo
            background="green",      # cor da barra
            bordercolor="#d9d9d9",
            lightcolor="green",
            darkcolor="green"
        )

        self.progress = ttk.Progressbar(
            control_frame,
            orient="horizontal",
            length=400,
            mode="determinate",
            style="Green.Horizontal.TProgressbar"
        )
        self.progress.pack(side="left", padx=20, fill="x", expand=True)

        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)

        self.frame_ipv4 = ttk.Frame(self.notebook)
        self.frame_ipv6 = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_ipv4, text="IPv4")
        self.notebook.add(self.frame_ipv6, text="IPv6")

        self.criar_tabela(self.frame_ipv4, "ipv4")
        self.criar_tabela(self.frame_ipv6, "ipv6")

        # Status
        self.status_label = tk.Label(root, text="Pronto - Pressione Escanear Agora", bd=1, relief="sunken",
                                     anchor="w", bg="#2d2d44", fg="#0ce931", font=("Arial", 9))
        self.status_label.pack(side="bottom", fill="x")

       # roda Pé
        footer = tk.Label(
            root,
            text="Como funciona: Clique em 'Escanear Agora' para listar as conexões TCP IPv4 IPv6. O sistema identifica o processo responsável, consulta Cidade, Estado, País, ISP e Organização do IP Remoto.\n\n"
            "Clique com o botão direito do mouse sobre uma conexão para abrir o IP no VirusTotal, consultar a rota no BGP.he.net ou visualizar a localização no Google Maps. Também é possível salvar todas as conexões em um arquivo TXT\n",
            bg=DARK_BG,
            fg="#0CD2F5",
            font=("Arial", 9),
            anchor="w",
            justify="left"
        )
        footer.pack(side="bottom", fill="x", padx=5)

    def configurar_estilos(self):
        self.style.configure("Treeview", background=TREE_BG, foreground=TREE_FG,
                            fieldbackground=TREE_BG, rowheight=26)
        self.style.configure("Treeview.Heading", background=HEADER_BG, foreground=DARK_FG,
                            font=("Arial", 10, "bold"))
        self.style.map("Treeview", background=[("selected", TREE_SELECTED)],
                      foreground=[("selected", "white")])

    def criar_tabela(self, parent, tipo):
        columns = (
            "Local IP", "LPort", "Remote IP", "RPort", "Estado", "PID",
            "Processo", "Cidade", "Estado/Região", "País", "ISP", "Org"
        )

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        tree = ttk.Treeview(container, columns=columns, show="headings", height=25)

        # Configuração das colunas
        tree.heading("Local IP", text="Local IP")
        tree.column("Local IP", width=250, anchor="w")

        tree.heading("LPort", text="LPort")
        tree.column("LPort", width=80, anchor="center")

        tree.heading("Remote IP", text="Remote IP")
        tree.column("Remote IP", width=250, anchor="w")

        tree.heading("RPort", text="RPort")
        tree.column("RPort", width=80, anchor="center")

        tree.heading("Estado", text="Estado")
        tree.column("Estado", width=90, anchor="center")

        tree.heading("PID", text="PID")
        tree.column("PID", width=70, anchor="center")

        tree.heading("Processo", text="Processo")
        tree.column("Processo", width=160, anchor="w")

        tree.heading("Cidade", text="Cidade")
        tree.column("Cidade", width=140, anchor="w")

        tree.heading("Estado/Região", text="Estado/Região")
        tree.column("Estado/Região", width=200, anchor="w")

        tree.heading("País", text="País")
        tree.column("País", width=150, anchor="w")

        tree.heading("ISP", text="ISP")
        tree.column("ISP", width=200, anchor="w")

        tree.heading("Org", text="Org")
        tree.column("Org", width=300, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Menu clique direito
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="🔍 Abrir no VirusTotal", command=lambda: self.abrir_virustotal(tree))
        menu.add_command(label="🌐 Abrir no BGP.he.net", command=lambda: self.abrir_bgp(tree))
        menu.add_command(label="🗺️ Abrir no Google Maps", command=lambda: self.abrir_google_maps(tree))
        tree.bind("<Button-3>", lambda e: self.mostrar_menu(e, tree, menu))

        if tipo == "ipv4":
            self.tree_ipv4 = tree
        else:
            self.tree_ipv6 = tree

        return tree

    def mostrar_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.post(event.x_root, event.y_root)

    def get_selected_row(self, tree):
        selected = tree.selection()
        if selected:
            return tree.item(selected[0])['values']
        return None

    def abrir_virustotal(self, tree):
        row = self.get_selected_row(tree)
        if row and row[2] != "N/A":
            webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{row[2]}")

    def abrir_bgp(self, tree):
        row = self.get_selected_row(tree)
        if row and row[2] != "N/A":
            webbrowser.open(f"https://bgp.he.net/ip/{row[2]}")

    def abrir_google_maps(self, tree):
        """Abre no Google Maps usando coordenadas quando disponível"""
        row = self.get_selected_row(tree)
        if not row or len(row) < 12:
            return

        ip = row[2]
        
        # Tenta pegar lat/lon do cache
        if ip in geo_cache:
            lat = geo_cache[ip][5]
            lon = geo_cache[ip][6]
            if lat and lon:
                webbrowser.open(f"https://www.google.com/maps?q={lat},{lon}")
                return

        # Fallback: busca pelo IP
        webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={ip}")

    def iniciar_scan(self):
        threading.Thread(target=self.scan_com_progresso, daemon=True).start()

    def scan_com_progresso(self):
        try:
            self.root.after(0, lambda: self.scan_button.config(state="disabled", text="🔄 Escaneando..."))
            self.root.after(0, lambda: self.progress.configure(value=0))
            self.root.after(0, lambda: self.status_label.config(text="Buscando conexões..."))

            for i in range(1, 31):
                self.root.after(0, lambda v=i*2: self.progress.configure(value=v))
                time.sleep(0.03)

            self.root.after(0, lambda: self.status_label.config(text="Obtendo geolocalização..."))
            for i in range(31, 81):
                self.root.after(0, lambda v=i: self.progress.configure(value=v))
                time.sleep(0.04)

            ipv4, ipv6 = obter_conexoes()
            self.root.after(0, lambda: self.atualizar_tabelas(ipv4, ipv6))

            total = len(ipv4) + len(ipv6)
            self.root.after(0, lambda: self.status_label.config(
                text=f"✓ Escaneamento concluído • {len(ipv4)} IPv4 | {len(ipv6)} IPv6 | Total: {total} • Cache: {len(geo_cache)}"
            ))

        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text="Erro no scan"))
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.root.after(0, lambda: self.scan_button.config(state="normal", text="🔍 Escanear Agora"))
            self.root.after(0, lambda: self.progress.configure(value=100))
            self.root.after(1500, lambda: self.progress.configure(value=0))

    def atualizar_tabelas(self, ipv4, ipv6):
        # Limpar tabelas
        for item in self.tree_ipv4.get_children():
            self.tree_ipv4.delete(item)
        for item in self.tree_ipv6.get_children():
            self.tree_ipv6.delete(item)

        # Inserir apenas as colunas visíveis (até Org)
        for conn in ipv4:
            self.tree_ipv4.insert("", "end", values=conn[:12])
        for conn in ipv6:
            self.tree_ipv6.insert("", "end", values=conn[:12])            

    def salvar_txt(self):
        try:
            ipv4, ipv6 = obter_conexoes()
            if not ipv4 and not ipv6:
                messagebox.showinfo("Aviso", "Nenhuma conexão encontrada.")
                return

            filename = f"conexoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile=filename
            )
            if not filepath:
                return

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("MONITOR DE CONEXÕES TCP + GEOLOCALIZAÇÃO\n")
                f.write("=" * 300 + "\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

                f.write("\n" + "=" * 50 + " IPv4 " + "=" * 244 + "\n\n")                

                # ==================== IPv4 ====================
                f.write(f"{'Local IP':<25} {'LPort':<8} {'Remote IP':<25} {'RPort':<8} {'PID':<8} "
                        f"{'Processo':<20} {'Cidade':<20} {'Estado/Região':<25} {'País':<25} "
                        f"{'ISP':<35} Org\n")
                f.write("-" * 300 + "\n")

                for conn in ipv4:
                    f.write(f"{conn[0]:<25} {str(conn[1]):<8} {conn[2]:<25} {str(conn[3]):<8} "
                            f"{str(conn[5]):<8} {conn[6]:<20} {conn[7]:<20} {conn[8]:<25} "
                            f"{conn[9]:<25} {conn[10]:<35} {conn[11]}\n")                 

                # ==================== IPv6 ====================
                if ipv6:
                    f.write("\n\n\n" + "=" * 50 + " IPv6 " + "=" * 244 + "\n\n")

                    colunas = [
                    ("Local IP", 50),      # Move a coluna LPort para a direita
                    ("LPort", 12),         # Aumenta o espaço da porta local
                    ("Remote IP", 50),     # Mantém espaço suficiente para IPv6
                    ("RPort", 10),
                    ("Estado", 15),
                    ("PID", 8),
                    ("Processo", 22),
                    ("Cidade", 20),
                    ("Estado/Região", 30),
                    ("País", 20),
                    ("ISP", 30),
                    ("Org", 35),
                ]

                    # Cabeçalho
                    for nome, largura in colunas:
                        f.write(f"{nome:<{largura}}")
                    f.write("\n")

                    # Linha separadora
                    f.write("-" * sum(largura for _, largura in colunas) + "\n")

                    # Dados
                    for conn in ipv6:
                        for valor, (_, largura) in zip(conn, colunas):
                            f.write(f"{str(valor):<{largura}}")
                        f.write("\n")


                f.write("\n" + "=" * 300 + "\n\n")
                f.write(f"Total de conexões: {len(ipv4) + len(ipv6)}\n")

            messagebox.showinfo("Sucesso", f"Arquivo salvo!\n\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

    def toggle_auto_refresh(self):
        if self.auto_var.get():
            if not hasattr(self, 'auto_thread') or not self.auto_thread.is_alive():
                self.auto_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
                self.auto_thread.start()

    def auto_refresh_loop(self):
        while self.auto_var.get():
            self.root.after(0, self.iniciar_scan)
            time.sleep(5)  


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop() 
