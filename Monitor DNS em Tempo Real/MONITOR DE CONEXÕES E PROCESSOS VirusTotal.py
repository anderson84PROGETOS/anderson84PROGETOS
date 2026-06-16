import tkinter as tk
from tkinter import ttk
import psutil
import socket
import threading
import time
import webbrowser
from tkinter import filedialog, messagebox
from datetime import datetime
import requests
from functools import lru_cache

class ConnectionMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("MONITOR DE CONEXÕES E PROCESSOS VirusTotal")
        self.root.geometry("1650x820")
        self.root.state("zoomed")
        self.root.configure(bg="#1e1e1e")

        titulo = tk.Label(root, text="MONITOR DE CONEXÕES E PROCESSOS",
                         font=("Arial", 18, "bold"), bg="#1e1e1e", fg="#00ff00")
        titulo.pack(pady=10)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.create_connections_tab()
        self.create_processes_tab()

        self.status_bar = tk.Label(root, text="Dica: Botão Direito = Menu VirusTotal | Duplo clique = VirusTotal",
                                  bd=1, relief="sunken", anchor="w", bg="#2b2b2b", fg="white")
        self.status_bar.pack(side="bottom", fill="x")

        self.executando = True
        threading.Thread(target=self.monitorar_conexoes, daemon=True).start()
        threading.Thread(target=self.monitorar_processos, daemon=True).start()

    # ====================== TABS ======================
    def create_connections_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Conexões de Rede")

        colunas = ("Nº", "PID", "Processo", "IP Local", "Porta Local", "IP Remoto",
                   "Porta Remota", "Hostname", "País", "Estado", "Status")
        
        self.tree_conn = ttk.Treeview(tab, columns=colunas, show="headings")
       
        widths = [10, 80, 130, 230, 100, 230, 100, 300, 150, 180, 120]
        for col, w in zip(colunas, widths):
            self.tree_conn.heading(col, text=col)
            self.tree_conn.column(col, width=w,
                                anchor="center" if col in ["Nº","PID","Porta Local","Porta Remota"] else "w")

        # Scrollbars
                # Scrollbars
        v_scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree_conn.yview)
        h_scrollbar = ttk.Scrollbar(tab, orient="horizontal", command=self.tree_conn.xview)
       
        self.tree_conn.configure(yscrollcommand=v_scrollbar.set, 
                                xscrollcommand=h_scrollbar.set)
        
        # Pack vertical scrollbar primeiro (lado direito)
        v_scrollbar.pack(side="right", fill="y")
        # Horizontal scrollbar por último (embaixo)
        h_scrollbar.pack(side="bottom", fill="x")
        # Layout
        self.tree_conn.pack(side="top", fill="both", expand=True)
     
        # Menu de contexto
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="VirusTotal - IP Remoto", command=self.consultar_ip_remoto)
        self.menu.add_command(label="VirusTotal - IP Local", command=self.consultar_ip_local)
        self.menu.add_command(label="VirusTotal - Processo", command=self.consultar_processo_virustotal)

        self.tree_conn.bind("<Button-3>", self.menu_contexto)
        self.tree_conn.bind("<Double-1>", self.abrir_virustotal)

        # Botão Salvar
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="💾 Salvar Conexões", command=self.salvar_conexoes).pack(side="left", padx=5)

    def create_processes_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Processos")

        colunas = ("PID", "Nome", "CPU %", "Memória %", "Threads", "IP Remoto", "País", "Estado", "Status")
        self.tree_proc = ttk.Treeview(tab, columns=colunas, show="headings")
       
        widths = [80, 170, 90, 100, 80, 200, 100, 100, 100]
        for col, w in zip(colunas, widths):
            self.tree_proc.heading(col, text=col)
            self.tree_proc.column(col, width=w, anchor="center" if col in ["PID","CPU %","Memória %","Threads"] else "w")

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree_proc.yview)
        self.tree_proc.configure(yscrollcommand=scrollbar.set)
        self.tree_proc.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.menu_proc = tk.Menu(self.root, tearoff=0)
        self.menu_proc.add_command(label="VirusTotal - IP Remoto", command=self.consultar_ip_processo)
        self.menu_proc.add_command(label="VirusTotal - Processo", command=self.consultar_processo_virustotal)

        self.tree_proc.bind("<Button-3>", self.menu_contexto_processos)
        self.tree_proc.bind("<Double-1>", self.abrir_virustotal_processo)

        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Atualizar Agora", command=self.atualizar_processos).pack(pady=5)
        ttk.Button(btn_frame, text="💾 Salvar Processos", command=self.salvar_processos).pack(pady=5)        

    # ====================== IP INFO CACHE ======================
    @lru_cache(maxsize=500)
    def get_ip_info(self, ip):
        if not ip or ip in ("0.0.0.0", "::", "127.0.0.1"):
            return "Local", "Local", "Local"
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,regionName,city", timeout=4)
            if response.status_code == 200:
                data = response.json()
                return (data.get("country", "N/A"),
                        data.get("regionName", "N/A"),
                        data.get("city", ""))
        except:
            pass
        return "N/A", "N/A", "N/A"

    # ====================== CONEXÕES ======================
    def monitorar_conexoes(self):
        while self.executando:
            self.atualizar_conexoes()
            time.sleep(4)

    def atualizar_conexoes(self):
        try:
            conexoes = psutil.net_connections(kind='tcp')
            dados = []
            for conn in conexoes:
                if conn.status != "ESTABLISHED":
                    continue
                pid = conn.pid if conn.pid else "N/A"
                try:
                    processo = psutil.Process(pid).name() if pid != "N/A" else "Sistema"
                except:
                    processo = "Desconhecido"

                ip_local = conn.laddr.ip if conn.laddr else ""
                porta_local = conn.laddr.port if conn.laddr else ""
                ip_remoto = conn.raddr.ip if conn.raddr else ""
                porta_remota = conn.raddr.port if conn.raddr else ""
                hostname = self.get_hostname(ip_remoto)
                pais, estado, _ = self.get_ip_info(ip_remoto)

                dados.append((pid, processo, ip_local, porta_local, ip_remoto,
                             porta_remota, hostname, pais, estado, conn.status))

            self.root.after(0, lambda: self.atualizar_interface_conexoes(dados))
        except:
            pass

    def atualizar_interface_conexoes(self, dados):
        for item in self.tree_conn.get_children():
            self.tree_conn.delete(item)
        for i, linha in enumerate(dados):
            self.tree_conn.insert("", "end", values=(i+1,) + linha)

    def get_hostname(self, ip):
        if not ip or ip in ("0.0.0.0", "::"):
            return "N/A"
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "N/A"

    # ====================== PROCESSOS ======================
    def monitorar_processos(self):
        while self.executando:
            self.atualizar_processos()
            time.sleep(3)

    def atualizar_processos(self):
        try:
            conn_map = {}
            for conn in psutil.net_connections(kind='tcp'):
                if conn.status == "ESTABLISHED" and conn.raddr and conn.pid:
                    if conn.pid not in conn_map:
                        conn_map[conn.pid] = []
                    conn_map[conn.pid].append(conn.raddr.ip)

            dados = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'status']):
                info = proc.info
                pid = info['pid']
                
                ip_remoto = conn_map.get(pid, [""])[0] if pid in conn_map else ""
                pais, estado, _ = self.get_ip_info(ip_remoto)

                dados.append((
                    pid,
                    info['name'][:45],
                    f"{info['cpu_percent']:.1f}",
                    f"{info['memory_percent']:.1f}",
                    info['num_threads'],
                    ip_remoto,
                    pais,
                    estado,
                    info['status']
                ))
            self.root.after(0, lambda: self.atualizar_interface_processos(dados))
        except:
            pass

    def atualizar_interface_processos(self, dados):
        for item in self.tree_proc.get_children():
            self.tree_proc.delete(item)
        for linha in dados:
            self.tree_proc.insert("", "end", values=linha)

    # ====================== SALVAR ======================
    def salvar_conexoes(self):
        self.salvar_arquivo(self.tree_conn, "conexoes")

    def salvar_processos(self):
        self.salvar_arquivo(self.tree_proc, "processos")

    def salvar_arquivo(self, tree, tipo):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo TXT", "*.txt")],
            initialfile=f"{tipo}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        )
        if not arquivo:
            return
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(f"RELATÓRIO DE {tipo.upper()} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*130 + "\n\n")
                for item in tree.get_children():
                    valores = tree.item(item)["values"]
                    f.write(" | ".join(str(v) for v in valores) + "\n")
            messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ====================== VIRUSTOTAL ======================
    def menu_contexto(self, event):
        item = self.tree_conn.identify_row(event.y)
        if item:
            self.tree_conn.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def menu_contexto_processos(self, event):
        item = self.tree_proc.identify_row(event.y)
        if item:
            self.tree_proc.selection_set(item)
            self.menu_proc.post(event.x_root, event.y_root)

    def abrir_virustotal(self, event):
        item = self.tree_conn.selection()
        if item:
            valores = self.tree_conn.item(item[0], "values")
            ip = valores[5]
            if ip and ip not in ("", "N/A"):
                webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")
            else:
                self.consultar_processo_virustotal()

    def abrir_virustotal_processo(self, event):
        self.consultar_ip_processo() or self.consultar_processo_virustotal()

    def consultar_ip_remoto(self):
        item = self.tree_conn.selection()
        if item:
            valores = self.tree_conn.item(item[0], "values")
            ip = valores[5]
            if ip:
                webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

    def consultar_ip_local(self):
        item = self.tree_conn.selection()
        if item:
            valores = self.tree_conn.item(item[0], "values")
            ip = valores[3]
            if ip:
                webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

    def consultar_ip_processo(self):
        item = self.tree_proc.selection()
        if item:
            valores = self.tree_proc.item(item[0], "values")
            ip = valores[5]
            if ip and ip not in ("", "N/A"):
                webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")
                return True
        return False

    def consultar_processo_virustotal(self):
        try:
            if self.notebook.select() == self.notebook.tabs()[1]:
                item = self.tree_proc.selection()
                if item:
                    valores = self.tree_proc.item(item[0], "values")
                    nome = valores[1]
            else:
                item = self.tree_conn.selection()
                if item:
                    valores = self.tree_conn.item(item[0], "values")
                    nome = valores[2]
            if nome:
                webbrowser.open(f"https://www.virustotal.com/gui/search/{nome}")
        except:
            pass

    def fechar(self):
        self.executando = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#2b2b2b", foreground="white",
                   fieldbackground="#2b2b2b", rowheight=26)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
  
    app = ConnectionMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.fechar)
    root.mainloop()
