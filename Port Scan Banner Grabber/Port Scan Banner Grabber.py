import socket
import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # ← Adicionado filedialog
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from datetime import datetime

class NmapSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Scan Banner Grabber")
        self.root.geometry("1220x850")
        self.root.state('zoomed')
        self.root.configure(bg="#f0f0f0")

        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=100)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.create_widgets()

    def configure_styles(self):
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", foreground="#000000", font=("Consolas", 10))
        self.style.configure("TButton", background="#e0e0e0", foreground="#000000", font=("Consolas", 10))
        self.style.configure("TEntry", fieldbackground="#ffffff", foreground="#000000")
        self.style.configure("TCombobox", fieldbackground="#ffffff", foreground="#000000")
        self.style.map("TButton", background=[("active", "#c0c0c0")])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configuração
        config_frame = ttk.LabelFrame(main_frame, text=" Configuração do Scan ", padding=10)
        config_frame.pack(fill="x", pady=5)

        ttk.Label(config_frame, text="Alvo (IP ou Hostname):").grid(row=0, column=0, sticky="w", pady=5)
        self.target_entry = ttk.Entry(config_frame, width=45, font=("Consolas", 11))
        self.target_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.target_entry.insert(0, "")

        ttk.Label(config_frame, text="Portas:").grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = ttk.Entry(config_frame, width=45, font=("Consolas", 11))
        self.port_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.port_entry.insert(0, "1-1000")

        ttk.Label(config_frame, text="(Ex: 1-65535, 80,443,22)").grid(row=1, column=2, sticky="w", pady=5)

        ttk.Label(config_frame, text="Tipo de Scan:").grid(row=2, column=0, sticky="w", pady=5)
        self.scan_type = ttk.Combobox(config_frame, 
            values=["TCP Connect", "SYN Stealth (Simulado)", "UDP Scan"], width=42)
        self.scan_type.current(0)
        self.scan_type.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Botões
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=12)

        self.start_btn = ttk.Button(btn_frame, text="▶ INICIAR SCAN", command=self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⛔ PARAR", command=self.stop_scan, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="🗑 Limpar", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # === NOVO BOTÃO ===
        self.save_btn = ttk.Button(btn_frame, text="💾 Salvar Resultados", command=self.save_results)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        # ===================

        self.progress = ttk.Progressbar(config_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", pady=8)

        # Resultados
        result_frame = ttk.LabelFrame(main_frame, text=" Resultados ", padding=10)
        result_frame.pack(fill="both", expand=True, pady=8)

        columns = ("Porta", "Serviço", "Status", "Versão / Banner", "SO")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=18)
        
        for col, width in zip(columns, [80, 160, 100, 320, 180]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="w")

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text=" Log ", padding=8)
        log_frame.pack(fill="x", pady=5)

        self.log_text = tk.Text(log_frame, height=12, bg="#1a1a1a", fg="#00ff88", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)

    # ==================== FUNÇÃO DE SALVAR ====================
    def save_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Não há resultados para salvar!")
            return

        # Escolher onde salvar
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile=f"scan_{self.target_entry.get().strip()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not file_path:
            return  # Usuário cancelou

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=" * 125 + "\n")
                f.write("               RELATÓRIO DE SCAN DE PORTAS\n")
                f.write("=" * 125 + "\n\n")
                f.write(f"Alvo: {self.target_entry.get().strip()}\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Portas escaneadas: {self.port_entry.get()}\n")
                f.write(f"Tipo de Scan: {self.scan_type.get()}\n")
                f.write("=" * 125 + "\n\n")

                # Cabeçalho da tabela
                f.write(f"{'Porta':<8} {'Serviço':<20} {'Status':<10} {'Versão / Banner':<70} {'SO'}\n")
                f.write("-" * 125 + "\n")

                # Resultados da Treeview
                for item in self.tree.get_children():
                    values = self.tree.item(item, "values")
                    f.write(f"{values[0]:<8} {values[1]:<20} {values[2]:<10} {values[3]:<70} {values[4]}\n")

                f.write("\n" + "=" * 125 + "\n")
                f.write("LOG DO SCAN:\n")
                f.write("=" * 125 + "\n")
                f.write(self.log_text.get("1.0", tk.END))

                messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso!\n\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    # ==================== RESTO DO CÓDIGO (sem alterações) ====================

    def parse_ports(self, text):
        text = text.strip().replace(" ", "")
        ports = set()
        try:
            if "-" in text:
                start, end = map(int, text.split("-"))
                ports.update(range(max(1, start), min(65536, end + 1)))
            elif "," in text:
                for p in text.split(","):
                    if "-" in p:
                        s, e = map(int, p.split("-"))
                        ports.update(range(max(1, s), min(65536, e + 1)))
                    else:
                        ports.add(int(p))
            else:
                ports.add(int(text))
            return sorted(list(ports))
        except:
            return None

    def get_service_name(self, port):
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 443: "HTTPS", 445: "SMB", 3306: "MySQL",
            3389: "RDP", 8080: "HTTP-Proxy", 110: "POP3", 143: "IMAP"
        }
        return services.get(port, f"Desconhecido ({port})")

    def get_banner(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            
            probes = [b"HEAD / HTTP/1.1\r\n\r\n", b"\r\n", b"HELP\r\n", b"INFO\r\n", b"VERSION\r\n"]
            
            banner = ""
            for probe in probes:
                try:
                    sock.sendall(probe)
                    response = sock.recv(2048).decode(errors="ignore").strip()
                    if response:
                        banner = response.splitlines()[0][:150]
                        break
                except:
                    continue
            
            sock.close()
            return banner if banner else None
        except:
            return None

    def get_http_version(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            request = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
            sock.sendall(request.encode())
            response = sock.recv(2048).decode(errors="ignore")
            sock.close()

            for line in response.splitlines():
                if line.lower().startswith("server:"):
                    return line.split(":", 1)[1].strip()
            return None
        except:
            return None

    def detect_os(self, open_ports):
        if 3389 in open_ports:
            return "Windows"
        elif 445 in open_ports or 139 in open_ports:
            return "Windows"
        elif 22 in open_ports:
            return "Linux / Unix"
        elif 80 in open_ports or 443 in open_ports:
            return "Linux / Unix"
        return "Desconhecido"

    def scan_port(self, ip, port, scan_type):
        try:
            if scan_type.startswith("TCP") or scan_type.startswith("SYN"):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.5)
                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:
                    service = self.get_service_name(port)
                    version = "Porta Aberta"

                    banner = self.get_banner(ip, port)
                    if banner:
                        version = banner[:100]

                    if port in [80, 443, 8080]:
                        http_ver = self.get_http_version(ip, port)
                        if http_ver:
                            version = http_ver

                    return (port, service, "ABERTA", version)

            return None
        except:
            return None

    def start_scan(self):
        if self.running:
            return

        target = self.target_entry.get().strip()
        port_text = self.port_entry.get().strip()
        scan_type = self.scan_type.get()

        if not target:
            messagebox.showerror("Erro", "Digite um alvo!")
            return

        ports = self.parse_ports(port_text)
        if not ports:
            messagebox.showerror("Erro", "Formato de portas inválido!")
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.tree.delete(*self.tree.get_children())
        self.log_text.delete(1.0, tk.END)

        self.log(f"Iniciando scan em {target} | {len(ports)} portas (com Banner Grabbing)")

        threading.Thread(target=self.run_scan, args=(target, ports, scan_type), daemon=True).start()

    def run_scan(self, target, ports, scan_type):
        try:
            ip = socket.gethostbyname(target)
            self.log(f"\nResolvido: {target} → {ip}\n")
        except:
            self.log("Erro: Não foi possível resolver o hostname")
            self.finish_scan()
            return

        open_ports = []
        self.progress["maximum"] = len(ports)

        futures = [self.executor.submit(self.scan_port, ip, port, scan_type) for port in ports]

        for i, future in enumerate(as_completed(futures)):
            if not self.running:
                break
            result = future.result()
            if result:
                port, service, status, version = result
                open_ports.append(port)
                os_info = "—"  
                self.tree.insert("", tk.END, values=(port, service, status, version, os_info))
                self.log(f"Porta {port} ABERTA - {version[:80]}")

            self.progress["value"] = i + 1
            self.root.update_idletasks()

        if self.running and open_ports:
            os_detected = self.detect_os(open_ports)
            for item in self.tree.get_children():
                values = list(self.tree.item(item, "values"))
                values[4] = os_detected
                self.tree.item(item, values=values)

            self.log("\n" + "="*60)
            self.log(f"✅ Scan Finalizado! {len(open_ports)} Portas Abertas | SO: {os_detected}")
            self.log("="*60)

        self.finish_scan()

    def finish_scan(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_scan(self):
        self.running = False
        self.log("Scan interrompido pelo usuário.")

    def clear_all(self):
        self.tree.delete(*self.tree.get_children())
        self.log_text.delete(1.0, tk.END)
        self.progress["value"] = 0
        self.log("Interface limpa.")


if __name__ == "__main__":
    root = tk.Tk()
    app = NmapSimulator(root)
    root.mainloop()
