import tkinter as tk
from tkinter import ttk
import psutil
import socket
import threading
import time
import webbrowser
from tkinter import filedialog, messagebox
from datetime import datetime

class ConnectionMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("MONITOR DE CONEXÕES E PROCESSOS")
        self.root.geometry("1300x750")
        self.root.state("zoomed")
        self.root.configure(bg="#1e1e1e")

        # Title
        titulo = tk.Label(root, text="MONITOR DE CONEXÕES E PROCESSOS", 
                         font=("Arial", 18, "bold"), bg="#1e1e1e", fg="#00ff00")
        titulo.pack(pady=10)

        # Notebook (Abas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Aba 1: Conexões
        self.create_connections_tab()
        # Aba 2: Processos
        self.create_processes_tab()

        # Status bar
        self.status_bar = tk.Label(root, text="Dica: Botão Direito = VirusTotal | Duplo clique = VirusTotal IP Remoto", 
                                  bd=1, relief="sunken", anchor="w", bg="#2b2b2b", fg="white")
        self.status_bar.pack(side="bottom", fill="x")

        self.executando = True
        threading.Thread(target=self.monitorar_conexoes, daemon=True).start()
        threading.Thread(target=self.monitorar_processos, daemon=True).start()

    def create_connections_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Conexões de Rede")

        colunas = ("Nº", "PID", "Processo", "IP Local", "Porta Local", "IP Remoto", "Porta Remota", "Hostname", "Status")
        self.tree_conn = ttk.Treeview(tab, columns=colunas, show="headings")
        
        widths = [10, 80, 100, 230, 90, 230, 100, 320, 120]
        for col, w in zip(colunas, widths):
            self.tree_conn.heading(col, text=col)
            self.tree_conn.column(col, width=w, anchor="center" if col in ["Nº","PID","Porta Local","Porta Remota"] else "w")

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree_conn.yview)
        self.tree_conn.configure(yscrollcommand=scrollbar.set)
        self.tree_conn.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Menu contexto
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="VirusTotal - IP Remoto", command=self.consultar_ip_remoto)
        self.menu.add_command(label="VirusTotal - IP Local", command=self.consultar_ip_local)

        self.tree_conn.bind("<Button-3>", self.menu_contexto)
        self.tree_conn.bind("<Double-1>", self.abrir_virustotal)

        # Botão salvar
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="💾 Salvar Conexões", command=self.salvar_conexoes).pack(side="left", padx=5)

    def create_processes_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Processos")

        colunas = ("PID", "Nome", "CPU %", "Memória %", "Threads", "Status")
        self.tree_proc = ttk.Treeview(tab, columns=colunas, show="headings")
        
        widths = [80, 220, 90, 100, 80, 120]
        for col, w in zip(colunas, widths):
            self.tree_proc.heading(col, text=col)
            self.tree_proc.column(col, width=w, anchor="center")

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree_proc.yview)
        self.tree_proc.configure(yscrollcommand=scrollbar.set)
        self.tree_proc.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Atualizar Agora", command=self.atualizar_processos).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 Salvar Processos", command=self.salvar_processos).pack(side="left", padx=5)

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

                dados.append((pid, processo, ip_local, porta_local, ip_remoto, porta_remota, hostname, conn.status))

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
            dados = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'status']):
                info = proc.info
                dados.append((
                    info['pid'],
                    info['name'][:40],
                    f"{info['cpu_percent']:.1f}",
                    f"{info['memory_percent']:.1f}",
                    info['num_threads'],
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
                f.write("="*90 + "\n\n")
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

    def abrir_virustotal(self, event):
        item = self.tree_conn.selection()
        if item:
            valores = self.tree_conn.item(item[0], "values")
            ip = valores[5]  # IP Remoto
            if ip:
                webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

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
