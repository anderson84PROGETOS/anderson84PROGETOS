import psutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
import scapy.all as scapy
from ipaddress import ip_network
import threading
from mac_vendor_lookup import AsyncMacLookup, MacLookup
import webbrowser
import asyncio
import subprocess
import re
from colorama import init, Fore, Style
# Inicializando o colorama
init(autoreset=True)

class NetworkMonitorApp:
    def __init__(self, parent):
        self.main_frame = ttk.Frame(parent, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Estilo
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("TLabel", font=('Helvetica', 11))
        self.style.configure("Treeview",
                            background="#000000",
                            foreground="#00FF00",
                            fieldbackground="#000000",
                            font=('Courier', 11))
        self.style.configure("Treeview.Heading",
                            font=('Helvetica', 11, 'bold'),
                            background="#1a1a1a",
                            foreground="#00FF00")

        # Título
        self.title_label = ttk.Label(
            self.main_frame,
            text="Network Connections Monitor",
            font=("Arial", 11, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=5, pady=10)

        # Botões
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

        # Não chama list_connections na inicialização, Treeview inicia vazio

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
        self.main_frame.winfo_toplevel().clipboard_clear()
        self.main_frame.winfo_toplevel().clipboard_append(exe_path)
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

    def destroy(self):
        self.main_frame.destroy()

class NetworkScannerApp:
    def __init__(self, parent):
        self.main_frame = tk.Frame(parent)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Interface gráfica
        self.entry_label = tk.Label(self.main_frame, text="Endereço de Rede", font=("TkDefaultFont", 11, "bold"))
        self.entry_label.pack(pady=5)
        self.entry = tk.Entry(self.main_frame, width=30, font=("TkDefaultFont", 11, "bold"))
        self.entry.insert(0, "192.168.0.1/24")
        self.entry.pack(pady=5)

        self.scan_button = tk.Button(self.main_frame, text="Iniciar Escaneamento", command=self.start_scan, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
        self.scan_button.pack(pady=10)

        self.save_button = tk.Button(self.main_frame, text="Salvar Resultados", command=self.save_results, bg="#07edf5", font=("TkDefaultFont", 11, "bold"))
        self.save_button.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.main_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=5)

        self.progress_label = tk.Label(self.main_frame, text="", font=("TkDefaultFont", 11, "bold"))
        self.progress_label.pack(pady=5)

        style = ttk.Style()
        style.configure("Treeview", font=("TkDefaultFont", 11))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 11, "bold"))

        # Treeview
        self.hosts_tree = ttk.Treeview(self.main_frame, columns=("Status", "IP", "MAC", "Fabricante"), show="headings")
        self.hosts_tree.heading("Status", text="Status", anchor=tk.W)
        self.hosts_tree.heading("IP", text="Endereço IP", anchor=tk.W)
        self.hosts_tree.heading("MAC", text="Endereço MAC", anchor=tk.W)
        self.hosts_tree.heading("Fabricante", text="Fabricante", anchor=tk.W)
        self.hosts_tree.pack(pady=10)

        self.hosts_tree.column("Status", width=100, anchor=tk.W)
        self.hosts_tree.column("IP", width=200, anchor=tk.W)
        self.hosts_tree.column("MAC", width=200, anchor=tk.W)
        self.hosts_tree.column("Fabricante", width=380, anchor=tk.W)
        self.hosts_tree.configure(height=25)

        self.result_label = tk.Label(self.main_frame, text="", font=("TkDefaultFont", 11, "bold"))
        self.result_label.pack(pady=5)

        self.hosts_tree.bind("<Double-1>", self.open_link)

    async def async_lookup_mac(self, mac_address, mac_lookup):
        try:
            return await mac_lookup.lookup(mac_address)
        except KeyError:
            return "Desconhecido"

    def scan_ip(self, ip, results, mac_lookup):
        arp_request = scapy.ARP(pdst=str(ip))
        ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp_request
        answered = scapy.srp(packet, timeout=0.5, verbose=0)[0]

        for sent, received in answered:
            vendor = asyncio.run(self.async_lookup_mac(received.hwsrc, mac_lookup))
            results.append((received.psrc, received.hwsrc, vendor, "Ativo 👨‍💻"))

    def scan_network(self, network):
        results = []
        mac_lookup = AsyncMacLookup()
        asyncio.run(mac_lookup.update_vendors())

        total_ips = network.num_addresses
        progress_step = 100 / total_ips

        threads = []
        for i, ip in enumerate(network, start=1):
            thread = threading.Thread(target=self.scan_ip, args=(ip, results, mac_lookup))
            threads.append(thread)
            thread.start()

            self.progress_bar['value'] += progress_step
            self.progress_label.config(text=f"Escaneando: {ip}")
            self.main_frame.winfo_toplevel().update_idletasks()

        for thread in threads:
            thread.join()

        return results

    def start_scan(self):
        network_address = self.entry.get()
        try:
            network = ip_network(network_address, strict=False)
        except ValueError:
            self.result_label.config(text="Endereço de rede inválido!")
            return

        self.progress_bar['value'] = 0
        self.progress_label.config(text="Iniciando escaneamento...")
        scan_results = self.scan_network(network)
        self.result_label.config(text="Escaneamento concluído!")

        for row in self.hosts_tree.get_children():
            self.hosts_tree.delete(row)

        for ip, mac, vendor, status in scan_results:
            self.hosts_tree.insert("", tk.END, values=(status, ip, mac, vendor))

    def save_results(self):
        if not self.hosts_tree.get_children():
            self.result_label.config(text="Nenhum resultado para salvar")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar Resultados",
            initialfile=f'network_scan_{datetime.now().strftime("%d-%m-%Y_Horário_%H-%M")}'
        )

        if not file_path:
            self.result_label.config(text="Salvamento cancelado")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("Status\t\tEndereço IP\t\tEndereço MAC\t\t\tFabricante\n\n")
                for row in self.hosts_tree.get_children():
                    values = self.hosts_tree.item(row, "values")
                    file.write("\t\t".join(values) + "\n")
            self.result_label.config(text=f"Resultados salvos em {file_path}")
        except Exception as e:
            self.result_label.config(text=f"Erro ao salvar: {str(e)}")

    def open_link(self, event):
        selected_item = self.hosts_tree.selection()
        if not selected_item:
            return
        ip_address = self.hosts_tree.item(selected_item[0], "values")[1]
        webbrowser.open(f"http://{ip_address}")

    def destroy(self):
        self.main_frame.destroy()

class WiFiScannerApp:
    BANNER = """
    ███████╗ ██████╗ █████╗ ███╗   ██╗    ██╗    ██╗██╗███████╗██╗    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
    ██╔════╝██╔════╝██╔══██╗████╗  ██║    ██║    ██║██║██╔════╝██║    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
    ███████╗██║     ███████║██╔██╗ ██║    ██║ █╗ ██║██║█████╗  ██║    ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝
    ╚════██║██║     ██╔══██║██║╚██╗██║    ██║███╗██║██║██╔══╝  ██║    ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗
    ███████║╚██████╗██║  ██║██║ ╚████║    ╚███╔███╔╝██║██║     ██║    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝     ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
    """

    def __init__(self, parent):
        self.main_frame = tk.Frame(parent, bg="#1e1e1e")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Banner
        banner_label = tk.Label(self.main_frame, text=self.BANNER, font=("Courier", 10), fg="cyan", bg="#1e1e1e", justify="center")
        banner_label.pack(pady=10)

        # Botões
        button_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        button_frame.pack(pady=10)
        scan_button = tk.Button(button_frame, text="Escanear Redes", command=self.mostrar_resultados, bg="#4CAF50", fg="white", font=("Arial", 12))
        scan_button.pack(side="left", padx=5)
        save_button = tk.Button(button_frame, text="Salvar Resultados", command=self.salvar_resultados, bg="#2196F3", fg="white", font=("Arial", 12))
        save_button.pack(side="left", padx=5)
        exit_button = tk.Button(button_frame, text="Sair", command=self.main_frame.winfo_toplevel().quit, bg="#f44336", fg="white", font=("Arial", 12))
        exit_button.pack(side="left", padx=5)

        # Frame principal com scrollbar
        self.scroll_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.scroll_frame, bg="#1e1e1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1e1e1e")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Status Label
        self.status_label = tk.Label(self.main_frame, text="Pronto", font=("Arial", 11, "bold"), fg="white", bg="#1e1e1e")
        self.status_label.pack(pady=5)

        # Armazenar resultados para salvar
        self.redes_netsh = {}

    def scan_wifi_windows(self):
        padrao_ssid = re.compile(r"SSID \d+ : (.+)")
        padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)")
        padrao_sinal = re.compile(r"Sinal\s+: (\d+)%")
        padrao_canal = re.compile(r"Canal\s+: (\d+)")
        padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)")
        redes_encontradas = {}

        try:
            result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
            redes = result.split("\n\n")

            for rede in redes:
                ssid = padrao_ssid.search(rede)
                bssid = padrao_bssid.search(rede)
                sinal = padrao_sinal.search(rede)
                canal = padrao_canal.search(rede)
                autenticacao = padrao_autenticacao.search(rede)

                if ssid and bssid:
                    mac_address = bssid.group(1)
                    if mac_address not in redes_encontradas:
                        try:
                            fabricante = MacLookup().lookup(mac_address)
                        except:
                            fabricante = "Desconhecido"

                        sinal_status = "Fraco" if int(sinal.group(1)) < 40 else "Médio" if int(sinal.group(1)) < 70 else "Forte"
                        seguranca = autenticacao.group(1) if autenticacao else "Desconhecido"
                        redes_encontradas[mac_address] = (ssid.group(1), canal.group(1), fabricante, sinal.group(1), sinal_status, seguranca)
        except subprocess.CalledProcessError as e:
            return {"error": f"Erro ao executar netsh: {e}"}
        return redes_encontradas

    def copy_field(self, event):
        widget = event.widget
        if isinstance(widget, tk.Label) and widget["text"] not in ["SSID", "BSSID", "Canal", "Fabricante", "Sinal", "Segurança", "="*136]:
            text = widget["text"]
            self.main_frame.winfo_toplevel().clipboard_clear()
            self.main_frame.winfo_toplevel().clipboard_append(text)
            self.status_label.config(text=f"Copiado: {text}")

    def clear_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def mostrar_resultados(self):
        self.clear_results()

        headers = ["SSID", "BSSID", "Canal", "Fabricante", "Sinal", "Segurança"]
        for col, header in enumerate(headers):
            label = tk.Label(self.scrollable_frame, text=header, font=("Arial", 12, "bold"), fg="magenta", bg="#1e1e1e")
            label.grid(row=0, column=col, padx=5, pady=5, sticky="w")

        separator = tk.Label(self.scrollable_frame, text="="*136, font=("Arial", 10), fg="magenta", bg="#1e1e1e")
        separator.grid(row=1, column=0, columnspan=6, pady=5)

        self.redes_netsh = self.scan_wifi_windows()
        if "error" in self.redes_netsh:
            error_label = tk.Label(self.scrollable_frame, text=self.redes_netsh["error"], font=("Arial", 12), fg="red", bg="#1e1e1e")
            error_label.grid(row=2, column=0, columnspan=6, pady=5)
            self.status_label.config(text="Erro ao escanear redes")
            return

        for row, (bssid, (ssid, canal, fabricante, sinal, sinal_status, seguranca)) in enumerate(self.redes_netsh.items(), start=2):
            values = [ssid, bssid, canal, fabricante, f"{sinal}% ({sinal_status})", seguranca]
            for col, value in enumerate(values):
                label = tk.Label(self.scrollable_frame, text=value, font=("Arial", 10), fg="lightgreen", bg="#1e1e1e")
                label.grid(row=row, column=col, padx=5, pady=2, sticky="w")
                label.bind("<Double-1>", self.copy_field)

        self.status_label.config(text="Escaneamento concluído")

    def salvar_resultados(self):
        if not self.redes_netsh or "error" in self.redes_netsh:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar. Execute um escaneamento primeiro.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar Resultados",
            initialfile=f'wifi_scan_{datetime.now().strftime("%d-%m-%Y_Horário_%H-%M")}'
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("Wi-Fi Scan Results\n")
                    f.write("=" * 134 + "\n")
                    f.write(f"{'SSID':<30} {'BSSID':<20} {'Canal':<10} {'Fabricante':<40} {'Sinal':<15} {'Segurança':<20}\n")
                    f.write("=" * 134 + "\n")
                    for bssid, (ssid, canal, fabricante, sinal, sinal_status, seguranca) in self.redes_netsh.items():
                        f.write(f"{ssid:<30} {bssid:<20} {canal:<10} {fabricante:<40} {sinal + '% (' + sinal_status + ')':<15} {seguranca:<20}\n")
                    f.write("=" * 134 + "\n")
                messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
                self.status_label.config(text="Resultados salvos")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar o arquivo: {e}")
                self.status_label.config(text="Erro ao salvar resultados")

    def destroy(self):
        self.main_frame.destroy()

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Tools")
        self.root.geometry("1200x900")
        self.root.configure(bg="#1e1e1e")
        self.root.wm_state('zoomed')  # Maximize window

        self.current_app = None

        # Configure root grid to center content
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=10)  # More weight for app container
        self.root.grid_columnconfigure(0, weight=1)

        # Menu Frame
        self.menu_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.menu_frame.grid(row=0, column=0, sticky="ew", pady=10)

        # Configure menu_frame grid for centering buttons
        self.menu_frame.grid_columnconfigure(0, weight=1)
        self.menu_frame.grid_columnconfigure(1, weight=0)  # Button column
        self.menu_frame.grid_columnconfigure(2, weight=0)  # Button column
        self.menu_frame.grid_columnconfigure(3, weight=0)  # Button column
        self.menu_frame.grid_columnconfigure(4, weight=1)

        # Buttons centered in the menu_frame
        tk.Button(self.menu_frame, text="Network Monitor", command=self.load_network_monitor,
                 bg="#4CAF50", fg="white", font=("Arial", 12)).grid(row=0, column=1, padx=5)
        tk.Button(self.menu_frame, text="Network Scanner", command=self.load_network_scanner,
                 bg="#2196F3", fg="white", font=("Arial", 12)).grid(row=0, column=2, padx=5)
        tk.Button(self.menu_frame, text="Wi-Fi Scanner", command=self.load_wifi_scanner,
                 bg="#fa9405", fg="white", font=("Arial", 12)).grid(row=0, column=3, padx=5)

        # Container for apps
        self.app_container = tk.Frame(self.root, bg="#1e1e1e")
        self.app_container.grid(row=1, column=0, sticky="nsew")

        # Configure app_container to expand
        self.app_container.grid_rowconfigure(0, weight=1)
        self.app_container.grid_columnconfigure(0, weight=1)

        # Load default app
        self.load_network_monitor()

    def clear_container(self):
        if self.current_app:
            self.current_app.destroy()
        for widget in self.app_container.winfo_children():
            widget.destroy()

    def load_network_monitor(self):
        self.clear_container()
        self.current_app = NetworkMonitorApp(self.app_container)
        self.root.title("Network Tools - Network Monitor")

    def load_network_scanner(self):
        self.clear_container()
        self.current_app = NetworkScannerApp(self.app_container)
        self.root.title("Network Tools - Network Scanner")

    def load_wifi_scanner(self):
        self.clear_container()
        self.current_app = WiFiScannerApp(self.app_container)
        self.root.title("Network Tools - Wi-Fi Scanner")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
