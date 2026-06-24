import socket
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
import re

# ==================== PORTAS ====================
PORTAS = {
    "HTTP":     {"port": 80,   "proto": "TCP"},
    "HTTPS":    {"port": 443,  "proto": "TCP"},
    "FTP":      {"port": 21,   "proto": "TCP"},
    "FTPS":     {"port": 990,  "proto": "TCP"},
    "SSH":      {"port": 22,   "proto": "TCP"},
    "Telnet":   {"port": 23,   "proto": "TCP"},
    "SMTP":     {"port": 25,   "proto": "TCP"},
    "POP3":     {"port": 110,  "proto": "TCP"},
    "IMAP":     {"port": 143,  "proto": "TCP"},
    "MSRPC":    {"port": 135,  "proto": "TCP"},
    "NetBIOS":  {"port": 139,  "proto": "TCP"},
    "SMB":      {"port": 445,  "proto": "TCP"},
    "MS-SQL":   {"port": 1434, "proto": "TCP"},
    "Nping":    {"port": 9929, "proto": "TCP"},
    "Elite":    {"port": 31337,"proto": "TCP"},
    "DNS":      {"port": 53,   "proto": "UDP"},
    "DHCP":     {"port": 67,   "proto": "UDP"},
    "SNMP":     {"port": 161,  "proto": "UDP"},
}

def get_banner(target, port, timeout=3):
    """Banner melhorado para várias portas (incluindo Nping, SSH, etc)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, port))
        
        banners = []

        # Probes específicos por porta
        if port in [80, 443]:
            request = f"HEAD / HTTP/1.1\r\nHost: {target}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
        elif port == 22:   # SSH
            sock.send(b"SSH-2.0-Scanner\r\n")
        elif port == 21:   # FTP
            sock.send(b"FEAT\r\n")
        elif port == 25:   # SMTP
            sock.send(b"EHLO scanner\r\n")
        elif port == 9929: # Nping
            sock.send(b"\x00")
        elif port == 31337: # Elite
            sock.send(b"HELP\r\n")
        else:
            sock.send(b"\r\n")
        
        # Recebe resposta
        response = sock.recv(4096).decode(errors='ignore')
        sock.close()
        
        # Procura Server:
        match = re.search(r'Server:\s*(.+?)(?:\r\n|$)', response, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:140]
        
        # Procura por versões comuns
        version_patterns = [
            r'(OpenSSH[^ \r\n]+)',
            r'(Apache[^ \r\n]+)',
            r'(nginx[^ \r\n]+)',
            r'(vsFTPd[^ \r\n]+)',
            r'(ProFTPD[^ \r\n]+)',
            r'(Nping echo[^ \r\n]*)',
            r'(SSH-[^\r\n]+)',
            r'([A-Za-z0-9._-]+/[0-9.]+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:140]
        
        # Se nada específico, pega primeira linha útil
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        for line in lines[:6]:
            if len(line) > 8 and not line.startswith("HTTP/"):
                return line[:140]
        
        return "Banner capturado"
        
    except:
        return ""

def scan_port(target, port, proto):
    try:
        if proto == "TCP":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.4)
            result = sock.connect_ex((target, port))
            sock.close()
            return result == 0
        else:
            return True
    except:
        return False


# ==================== GUI (mesmo estilo) ====================
class PortScannerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔥 PORT SCANNER 🔥")
        self.root.geometry("1220x800")
        self.root.state('zoomed')
        self.root.configure(bg="#0a0a0a")
        
        self.results = []
        self.current_ip = ""
        self.current_target = ""

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#0a0a0a", foreground="#00ff00", 
                       fieldbackground="#0a0a0a", font=("Consolas", 11))
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="#00ff41",
                       font=("Consolas", 11, "bold"))
        style.map("Treeview", background=[('selected', '#003300')])

        tk.Label(self.root, text="PORT SCANNER", font=("Consolas", 26, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(pady=10)
        tk.Label(self.root, text="🔥 PORT SCANNER 🔥", font=("Consolas", 11), 
                fg="#00ff41", bg="#0a0a0a").pack(pady=2)

        # Input Frame
        input_frame = tk.Frame(self.root, bg="#0a0a0a")
        input_frame.pack(pady=15)

        tk.Label(input_frame, text="ALVO:", font=("Consolas", 12), fg="#00ff00", bg="#0a0a0a").pack(side=tk.LEFT, padx=8)
        self.target_entry = tk.Entry(input_frame, width=45, font=("Consolas", 12), 
                                    bg="#1a1a1a", fg="#00ff00", insertbackground="#00ff00")
        self.target_entry.pack(side=tk.LEFT, padx=5)
        self.target_entry.insert(0, "scanme.nmap.org")

        self.scan_button = tk.Button(input_frame, text="▶ SCAN", font=("Consolas", 14, "bold"),
                                    bg="#00ff00", fg="#000000", width=12, height=1, command=self.start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=12)

        # IP Info
        self.ip_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.ip_frame.pack(pady=8)

        self.ip_label = tk.Label(self.ip_frame, text="", font=("Consolas", 12), fg="#00ff41", bg="#0a0a0a")
        self.ip_label.pack(side=tk.LEFT, padx=10)

        self.copy_button = tk.Button(self.ip_frame, text="📋 Copiar IP", font=("Consolas", 10), 
                                    bg="#1a1a1a", fg="#00ff00", command=self.copy_ip)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        # Treeview
        result_frame = tk.Frame(self.root, bg="#0a0a0a")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("Porta", "Proto", "State", "Service", "Version")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=22, style="Treeview")
        
        self.tree.heading("Porta", text="PORT")
        self.tree.heading("Proto", text="PROTO")
        self.tree.heading("State", text="STATE")
        self.tree.heading("Service", text="SERVICE")
        self.tree.heading("Version", text="VERSION")

        self.tree.column("Porta", width=80, anchor="center")
        self.tree.column("Proto", width=80, anchor="center")
        self.tree.column("State", width=110, anchor="center")
        self.tree.column("Service", width=140)
        self.tree.column("Version", width=580)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botão Salvar
        self.save_button = tk.Button(self.root, text="💾 Salvar Resultados em .txt", 
                                    font=("Consolas", 12, "bold"), bg="#00aa00", fg="#070707", 
                                    height=2, command=self.save_results)
        self.save_button.pack(pady=12)

        self.status_var = tk.StringVar(value="Pronto para o scan...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, font=("Consolas", 10), 
                             fg="#00ff00", bg="#1a1a1a", anchor="w")
        status_bar.pack(fill=tk.X, ipady=6, padx=20, pady=5)

        self.root.mainloop()

    def start_scan(self):
        self.current_target = self.target_entry.get().strip()
        if not self.current_target:
            messagebox.showwarning("Aviso", "Digite um IP ou domínio!")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results.clear()
        self.current_ip = ""

        self.scan_button.config(state="disabled", text="SCANNING...")
        self.status_var.set(f"🔍 Escaneando {self.current_target}...")

        threading.Thread(target=self.scan_thread, args=(self.current_target,), daemon=True).start()

    def scan_thread(self, target):
        try:
            ip = socket.gethostbyname(target)
            self.current_ip = ip
            self.root.after(0, lambda: self.show_ip(target, ip))
        except:
            self.root.after(0, lambda: self.status_var.set("❌ Não foi possível resolver o hostname!"))
            self.root.after(0, lambda: self.scan_button.config(state="normal", text="▶ SCAN"))
            return

        abertas = 0
        for servico, info in PORTAS.items():
            port = info["port"]
            proto = info["proto"]
            
            is_open = scan_port(ip, port, proto)
            state = "open" if is_open else "closed"
            
            version = ""
            if is_open and proto == "TCP":
                self.root.after(0, lambda p=port: self.status_var.set(f"🔍 Pegando banner da porta {p}"))
                version = get_banner(ip, port)
            
            if is_open:
                abertas += 1

            line = f"{port}/{proto.lower()} {state} {servico} {version}"
            self.results.append(line)

            color = "#00ff00" if is_open else "#ff4444"
            values = (port, proto, state.upper(), servico, version)
            
            self.root.after(0, self.add_result, values, color)

        self.root.after(0, lambda: self.finalizar_scan(abertas))

    def show_ip(self, target, ip):
        self.ip_label.config(text=f"🌐 Alvo: {target}  →  IP: {ip}")
        self.copy_button.config(state="normal")

    def copy_ip(self):
        if self.current_ip:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_ip)
            messagebox.showinfo("Copiado", f"IP {self.current_ip} copiado!")

    def add_result(self, values, color):
        item = self.tree.insert("", "end", values=values)
        self.tree.item(item, tags=(color,))
        self.tree.tag_configure(color, foreground=color)

    def finalizar_scan(self, abertas):
        self.status_var.set(f"✅ Scan finalizado! {abertas} portas aberta")
        self.scan_button.config(state="normal", text="▶ SCAN")

    def save_results(self):
        if not self.results:
            messagebox.showwarning("Aviso", "Faça um scan primeiro!")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            initialfile=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=== PORT SCANNER - NMAP STYLE ===\n\n")
                    f.write(f"Data: {datetime.now()}\n")
                    f.write(f"Alvo: {self.current_target}\n")
                    if self.current_ip:
                        f.write(f"IP: {self.current_ip}\n")
                    f.write("=" * 90 + "\n\n")
                    for line in self.results:
                        f.write(line + "\n\n")
                messagebox.showinfo("Salvo", f"Resultados salvos!\n\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    PortScannerGUI()
