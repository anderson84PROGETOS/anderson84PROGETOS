import tkinter as tk
from tkinter import ttk
import psutil
import socket
import threading
import time
import webbrowser
from tkinter import filedialog, messagebox
from datetime import datetime

class HTTP2Monitor:
    def __init__(self, root):
        self.root = root
        self.root.title("MONITORAR CONEXÕES HTTP/2")
        self.root.geometry("1100x600")
        self.root.state("zoomed")
        self.root.configure(bg="#1e1e1e")

        # Title
        titulo = tk.Label(
            root,
            text="MONITORAR CONEXÕES HTTP/2",
            font=("Arial", 18, "bold"),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        titulo.pack(pady=10)

        # Main frame
        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview setup
        colunas = (
            "Nº",
            "PID",
            "Processo",
            "IP Local",
            "Porta Local",
            "IP Remoto",
            "Porta Remota",
            "Hostname",
            "Status"
        )

        self.tree = ttk.Treeview(frame, columns=colunas, show="headings")
        
        # Configure columns
        self.tree.heading("Nº", text="Nº")
        self.tree.column("Nº", width=10, anchor="center")

        self.tree.heading("PID", text="PID")
        self.tree.column("PID", width=80, anchor="center")

        self.tree.heading("Processo", text="Processo")
        self.tree.column("Processo", width=100)

        self.tree.heading("IP Local", text="IP Local")
        self.tree.column("IP Local", width=230)

        self.tree.heading("Porta Local", text="Porta Local")
        self.tree.column("Porta Local", width=90, anchor="center")

        self.tree.heading("IP Remoto", text="IP Remoto")
        self.tree.column("IP Remoto", width=230)

        self.tree.heading("Porta Remota", text="Porta Remota")
        self.tree.column("Porta Remota", width=100, anchor="center")

        self.tree.heading("Hostname", text="Hostname")
        self.tree.column("Hostname", width=320)

        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status panel
        painel = tk.Frame(root, bg="#1e1e1e")
        painel.pack(fill="x", pady=5)

        self.lbl_total = tk.Label(
            painel,
            text="Conexões HTTP/2: 0",
            font=("Arial", 12, "bold"),
            bg="#1e1e1e",
            fg="cyan"
        )
        self.lbl_total.pack(side="left", padx=20)

        self.btn_salvar = tk.Button(
            painel,
            text="💾 Salvar TXT",
            font=("Arial", 10, "bold"),
            bg="#0078D7",
            fg="black",
            command=self.salvar_txt
        )

        self.btn_salvar.pack(side="right", padx=20)

        self.status_bar = tk.Label(
            root,
            text="Dica: Clique com o Botão Direito Sobre uma Conexão Para Consultar o   VirusTotal - IP Remoto   |  VirusTotal - IP Local ",
            bd=1,
            font=("Arial", 10, "bold"),
            relief="sunken",
            anchor="w",
            bg="#2b2b2b",
            fg="white"
        )

        self.status_bar.pack(side="bottom", fill="x")

        # Start monitoring thread
        self.executando = True
        thread = threading.Thread(target=self.monitorar, daemon=True)
        thread.start()

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="VirusTotal - IP Remoto", command=self.consultar_ip_remoto)
        self.menu.add_command(label="VirusTotal - IP Local", command=self.consultar_ip_local)

        # Bind events
        self.tree.bind("<Button-3>", self.menu_contexto)
        self.tree.bind("<Double-1>", self.abrir_virustotal)
        root.protocol("WM_DELETE_WINDOW", self.fechar)

    def monitorar(self):
        while self.executando:
            self.atualizar_tabela()
            time.sleep(5)

    def get_hostname(self, ip_address):
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
        except:
            hostname = "N/A"
        return hostname

    def atualizar_tabela(self):
        try:
            conexoes = psutil.net_connections(kind='tcp')
            dados = []

            for conn in conexoes:
                try:
                    if conn.status != "ESTABLISHED":
                        continue

                    pid = conn.pid if conn.pid else "N/A"
                    try:
                        processo = psutil.Process(conn.pid).name()
                    except:
                        processo = "Desconhecido"

                    ip_local = conn.laddr.ip if conn.laddr else ""
                    porta_local = conn.laddr.port if conn.laddr else ""
                    ip_remoto = conn.raddr.ip if conn.raddr else ""
                    porta_remota = conn.raddr.port if conn.raddr else ""

                    http2 = porta_remota in [443, 8443]
                    if http2:
                        hostname = self.get_hostname(ip_remoto)
                        dados.append((
                            "",
                            pid,
                            processo,
                            ip_local,
                            porta_local,
                            ip_remoto,
                            porta_remota,
                            hostname,
                            "HTTP/2"
                        ))
                except:
                    pass

            self.root.after(0, lambda: self.atualizar_interface(dados))
        except:
            pass

    def atualizar_interface(self, dados):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, linha in enumerate(dados):
            self.tree.insert("", "end", values=(i+1,) + linha[1:])
        self.lbl_total.config(text=f"Conexões HTTP/2 Detectadas: {len(dados)}")

    def fechar(self):
        self.executando = False
        self.root.destroy()

    def menu_contexto(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)            

    def abrir_virustotal(self, event):
        item = self.tree.selection()
        if not item:
            return
        valores = self.tree.item(item[0], "values")
        ip = valores[5]  # IP Remoto
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

    def consultar_ip_remoto(self):
        item = self.tree.selection()
        if not item:
            return
        valores = self.tree.item(item[0], "values")
        ip = valores[5]
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

    def consultar_ip_local(self):
        item = self.tree.selection()
        if not item:
            return
        valores = self.tree.item(item[0], "values")
        ip = valores[3]
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")


    def salvar_txt(self):

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo TXT", "*.txt")],
            title="Salvar Relatório"
        )

        if not arquivo:
            return

        try:

            with open(arquivo, "w", encoding="utf-8") as f:

                f.write("=" * 80 + "\n")
                f.write("RELATÓRIO MONITOR HTTP/2\n")
                f.write("=" * 80 + "\n")
                f.write(
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                )

                for item in self.tree.get_children():

                    valores = self.tree.item(item)["values"]

                    f.write(
                        f"Nº: {valores[0]}\n"
                        f"PID: {valores[1]}\n"
                        f"Processo: {valores[2]}\n"
                        f"IP Local: {valores[3]}\n"
                        f"Porta Local: {valores[4]}\n"
                        f"IP Remoto: {valores[5]}\n"
                        f"Porta Remota: {valores[6]}\n"
                        f"Hostname: {valores[7]}\n"
                        f"Status: {valores[8]}\n"
                    )

                    f.write("-" * 80 + "\n")

            messagebox.showinfo(
                "Sucesso",
                "Relatório salvo com sucesso!"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Falha ao salvar:\n{erro}"
            )        

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background="#2b2b2b",
        foreground="white",
        fieldbackground="#2b2b2b",
        rowheight=25
    )
    style.configure(
        "Treeview.Heading",
        font=("Arial", 10, "bold")
    )
    app = HTTP2Monitor(root)
    root.mainloop()
