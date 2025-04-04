import psutil
import tkinter as tk
from tkinter import ttk, filedialog
import os
from datetime import datetime

class NetworkMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Monitor")
        self.root.geometry("1230x900")
        root.wm_state('zoomed')

        # Estilo
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("TLabel", font=('Helvetica', 11))
        self.style.configure("Treeview",
                             background="#000000",  # fundo preto
                             foreground="#00FF00",  # verde limão
                             fieldbackground="#000000",
                             font=('Courier', 11))
        self.style.configure("Treeview.Heading",
                             font=('Helvetica', 11, 'bold'),
                             background="#1a1a1a",  # cinza escuro
                             foreground="#00FF00")  # verde limão

        # Frame principal
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título
        self.title_label = ttk.Label(
            self.main_frame,
            text="Network Connections Monitor Open Program | Programa aberto do monitor de conexões de rede",
            font=("Arial", 11, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=5, pady=10)

        # Botões com cores HTML
        self.refresh_button = tk.Button(self.main_frame, text="Atualizar Conexões", command=self.list_connections,
                                        background="#00FF00", activebackground="#32CD32",
                                        font=('Helvetica', 10, 'bold'))
        self.refresh_button.grid(row=1, column=0, pady=5, padx=5)

        self.clear_button = tk.Button(self.main_frame, text="Limpar Tela", command=self.clear_display,
                                      background="#FFA500", activebackground="#FF8C00",
                                      font=('Helvetica', 10, 'bold'))
        self.clear_button.grid(row=1, column=1, pady=5, padx=5)

        self.exe_path_button = tk.Button(self.main_frame, text="Mostrar Caminho do Executável", command=self.show_exe_path,
                                         background="#00f2ff", activebackground="#05b2fc",
                                         font=('Helvetica', 10, 'bold'))
        self.exe_path_button.grid(row=1, column=2, pady=5, padx=5)

        self.copy_path_button = tk.Button(self.main_frame, text="Copiar Caminho do Executável", command=self.copy_exe_path,
                                          background="#f8fc05", activebackground="#c1c406",
                                          font=('Helvetica', 10, 'bold'))
        self.copy_path_button.grid(row=1, column=3, pady=5, padx=5)

        self.save_button = tk.Button(self.main_frame, text="Salvar Resultados", command=self.save_results,
                                     background="#F08080", activebackground="#CD5C5C",
                                     font=('Helvetica', 10, 'bold'))
        self.save_button.grid(row=1, column=4, pady=5, padx=5)

        # Treeview
        self.tree = ttk.Treeview(self.main_frame,
                                 columns=("LocalAddress", "LocalPort", "RemoteAddress", "RemotePort", "State", "AppliedSetting", "PID", "Processo"),
                                 show="headings", height=36)
        self.tree.grid(row=2, column=0, columnspan=5, pady=10, sticky=(tk.W, tk.E))

        headings = ["LocalAddress", "LocalPort", "RemoteAddress", "RemotePort", "State", "AppliedSetting", "PID", "Processo"]
        for h in headings:
            self.tree.heading(h, text=h)

        self.tree.column("LocalAddress", width=350)
        self.tree.column("LocalPort", width=80)
        self.tree.column("RemoteAddress", width=300)
        self.tree.column("RemotePort", width=80)
        self.tree.column("State", width=100)
        self.tree.column("AppliedSetting", width=120)
        self.tree.column("PID", width=60)
        self.tree.column("Processo", width=150)

        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=5, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.tag_configure("header", background="#333333", foreground="#00FF00", font=('Helvetica', 11, 'bold'))
        self.tree.tag_configure("spacer", background="#000000")

        # Status
        self.status_label = ttk.Label(self.main_frame, text="Pronto", style="TLabel")
        self.status_label.grid(row=3, column=0, columnspan=5, pady=5)

        # Mostrar conexões na inicialização
        self.list_connections()

    def get_process_name(self, pid):
        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Desconhecido"

    def get_exe_path(self, pid):
        try:
            return psutil.Process(pid).exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Caminho não disponível"

    def list_connections(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conexoes = psutil.net_connections(kind='tcp')
        conexoes_ipv4 = []
        conexoes_ipv6 = []

        for conn in conexoes:
            if conn.status == 'ESTABLISHED':
                local_addr = conn.laddr.ip if conn.laddr else "N/A"
                local_port = conn.laddr.port if conn.laddr else "N/A"
                remote_addr = conn.raddr.ip if conn.raddr else "N/A"
                remote_port = conn.raddr.port if conn.raddr else "N/A"
                state = conn.status
                applied_setting = "Internet"
                owning_process = conn.pid if conn.pid else "N/A"
                process_name = self.get_process_name(owning_process)

                if ":" in local_addr:
                    conexoes_ipv6.append((local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name))
                else:
                    conexoes_ipv4.append((local_addr, local_port, remote_addr, remote_port, state, applied_setting, owning_process, process_name))

        self.tree.insert("", "end", values=("Conexões IPv4", "", "", "", "", "", "", ""), tags=("header",))
        self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""), tags=("spacer",))
        for conn in conexoes_ipv4:
            self.tree.insert("", "end", values=conn)
            self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""), tags=("spacer",))

        self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""), tags=("spacer",))
        self.tree.insert("", "end", values=("Conexões IPv6", "", "", "", "", "", "", ""), tags=("header",))
        self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""), tags=("spacer",))
        for conn in conexoes_ipv6:
            self.tree.insert("", "end", values=conn)
            self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""), tags=("spacer",))

        self.status_label.config(text=f"Atualizado em: {self.get_current_time()}", font=("Arial", 11, "bold"))

    def show_exe_path(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.status_label.config(text="Nenhuma conexão selecionada")
            return

        item_values = self.tree.item(selected_item[0])["values"]
        pid = item_values[6]
        if pid == "N/A":
            self.status_label.config(text="PID não disponível para esta conexão")
            return

        exe_path = self.get_exe_path(int(pid))
        self.status_label.config(text=f"Caminho do Executável: {exe_path}")

    def copy_exe_path(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.status_label.config(text="Nenhuma conexão selecionada para copiar")
            return

        item_values = self.tree.item(selected_item[0])["values"]
        pid = item_values[6]
        if pid == "N/A":
            self.status_label.config(text="PID não disponível para esta conexão")
            return

        exe_path = self.get_exe_path(int(pid))
        self.root.clipboard_clear()
        self.root.clipboard_append(exe_path)
        self.status_label.config(text=f"Caminho copiado: {exe_path}")

    def save_results(self):
        if not self.tree.get_children():
            self.status_label.config(text="Nenhum resultado para salvar")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar Resultados",
            initialfile=f'network_connections_{datetime.now().strftime("%d-%m-%Y_Horário_%H-%M")}'
        )

        if not file_path:
            self.status_label.config(text="Salvamento cancelado")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{'LocalAddress':<40} {'LocalPort':<10} {'RemoteAddress':<40} {'RemotePort':<10} {'State':<12} {'AppliedSetting':<15} {'PID':<7} {'Processo'}\n")
                f.write("-" * 150 + "\n")

                f.write("Conexões IPv4\n")
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    if values[0] in ("Conexões IPv4", "Conexões IPv6", ""):
                        continue
                    if ":" not in values[0]:
                        f.write(f"\n{values[0]:<40} {values[1]:<10} {values[2]:<40} {values[3]:<10} {values[4]:<12} {values[5]:<15} {values[6]:<7} {values[7]}\n")

                f.write("\n\nConexões IPv6\n\n")
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    if values[0] in ("Conexões IPv4", "Conexões IPv6", ""):
                        continue
                    if ":" in values[0]:
                        f.write(f"\n{values[0]:<40} {values[1]:<10} {values[2]:<40} {values[3]:<10} {values[4]:<12} {values[5]:<15} {values[6]:<7} {values[7]}\n")

            self.status_label.config(text=f"Resultados salvos em: {file_path}")
        except Exception as e:
            self.status_label.config(text=f"Erro ao salvar: {str(e)}")

    def clear_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status_label.config(text="Tela limpa")

    def get_current_time(self):
        return datetime.now().strftime("%d/%m/%Y  Horário: %H:%M")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMonitorApp(root)
    root.mainloop()
