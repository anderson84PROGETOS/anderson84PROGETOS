import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading

class NetworkToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Scanner & Tools - Windows 10")
        self.root.geometry("1100x750")
        self.root.state("zoomed")
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_nmap_tab()
        self.create_curl_tab()
        self.create_windows_tab()
    
    def create_nmap_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Nmap Scan")
        
        # === Frame Superior ===
        top_frame = tk.Frame(tab)
        top_frame.pack(fill="x", padx=10, pady=8)
        
        tk.Label(top_frame, text="Alvo (IP, Range ou Hostname):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.nmap_target = tk.Entry(top_frame, width=60, font=("Consolas", 10))
        self.nmap_target.insert(0, "")
        self.nmap_target.pack(pady=5, fill="x")
        
        # Atualiza automaticamente ao digitar
        self.nmap_target.bind("<KeyRelease>", self.atualizar_comando)
        
        # === Opções ===
        options_frame = tk.LabelFrame(tab, text="Opções de Scan", padx=10, pady=8)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Verbose
        tk.Label(options_frame, text="Verbose:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_verbose = ttk.Combobox(options_frame, values=["", "-v", "-vv", "-vvv"], width=8, state="readonly")
        self.combo_verbose.set("-v")
        self.combo_verbose.grid(row=0, column=1, padx=5)
        
        # Tipo de Scan
        tk.Label(options_frame, text="Tipo de Scan:").grid(row=0, column=2, sticky="w", padx=5)
        scan_types = [
            "Scan rápido", "Top 100 portas", "Top 1000 portas", "Detecção de serviços",
            "Detecção de sistema operacional", "Scripts NSE padrão", "Scan de vulnerabilidades",
            "Scan de vulnerabilidades e serviços", "Scan agressivo", "Scan completo TCP",
            "Scan UDP", "Detecção de firewall", "Scan stealth FIN", "Scan Xmas",
            "Scan NULL", "Enumeração SMB", "Brute FTP", "Brute SSH", "Detectar HTTP",
            "SSL/TLS", "dns-brute", "Traceroute"
        ]
        self.combo_scan = ttk.Combobox(options_frame, values=scan_types, width=35, state="readonly")
        self.combo_scan.set("Scan rápido")
        self.combo_scan.grid(row=0, column=3, padx=5)
        
        # Botão Atualizar Comando
        tk.Button(options_frame, text="Atualizar Comando", bg="#2196F3", fg="black",
                 command=self.atualizar_comando).grid(row=0, column=4, padx=10)
        
        # Preview do Comando
        tk.Label(tab, text="Comando Nmap:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10,2))
        self.entry_comando = scrolledtext.ScrolledText(tab, height=3, font=("Consolas", 10))
        self.entry_comando.pack(fill="x", padx=10, pady=5)
        
        # Botão Executar
        btn_frame = tk.Frame(tab)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="🚀 EXECUTAR SCAN", bg="#4CAF50", fg="black", font=("Arial", 11, "bold"),
                 command=lambda: self.run_command_thread(self.run_nmap_custom)).pack()
        
        # Output
        tk.Label(tab, text="Saída do Scan:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(5,2))
        self.nmap_output = scrolledtext.ScrolledText(tab, height=22, font=("Consolas", 9))
        self.nmap_output.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Atualiza comando inicial
        self.atualizar_comando()
        
        # Bind para atualizar automaticamente
        self.combo_scan.bind("<<ComboboxSelected>>", self.atualizar_comando)
        self.combo_verbose.bind("<<ComboboxSelected>>", self.atualizar_comando)
    
    def atualizar_comando(self, event=None):
        alvo = self.nmap_target.get().strip()
        verbose = self.combo_verbose.get()
        scan_tipo = self.combo_scan.get()
        
        scans_preview = {
            "Scan rápido": f"nmap {verbose} -D RND:20 -sS -F {alvo}",
            "Top 100 portas": f"nmap {verbose} -D RND:20 --open -sS --top-ports 100 {alvo}",
            "Top 1000 portas": f"nmap {verbose} -D RND:20 --open -sS --top-ports 1000 {alvo}",
            "Detecção de serviços": f"nmap {verbose} -D RND:20 -sV {alvo}",
            "Detecção de sistema operacional": f"nmap {verbose} -D RND:20 -O {alvo}",
            "Scripts NSE padrão": f"nmap {verbose} -D RND:20 -sC {alvo}",
            "Scan de vulnerabilidades": f"nmap {verbose} -D RND:20 --script vuln {alvo}",
            "Scan de vulnerabilidades e serviços": f"nmap {verbose} -sV -D RND:20 --script vuln {alvo}",
            "Scan de vulnerabilidades e serviços + sistema operacional": f"nmap {verbose} -sV -O -D RND:20 --script vuln {alvo}",
            "Scan agressivo": f"nmap {verbose} -D RND:20 -A {alvo}",
            "Scan completo TCP": f"nmap {verbose} -D RND:20 -p- -sS {alvo}",
            "Scan UDP": f"nmap {verbose} -D RND:20 -sU {alvo}",
            "Detecção de firewall": f"nmap {verbose} -D RND:20 -sA {alvo}",
            "Scan stealth FIN": f"nmap {verbose} -D RND:20 -sF {alvo}",
            "Scan Xmas": f"nmap {verbose} -D RND:20 -sX {alvo}",
            "Scan NULL": f"nmap {verbose} -D RND:20 -sN {alvo}",
            "Enumeração SMB": f"nmap {verbose} --script smb-enum-shares,smb-enum-users {alvo}",
            "Brute FTP": f"nmap {verbose} --script ftp-brute {alvo}",
            "Brute SSH": f"nmap {verbose} --script ssh-brute {alvo}",
            "Detectar HTTP": f"nmap {verbose} -sV --script http-title,http-headers {alvo}",
            "SSL/TLS": f"nmap {verbose} --script ssl-enum-ciphers -p 443 {alvo}",
            "dns-brute": f"nmap {verbose} --script dns-brute {alvo}",
            "Traceroute": f"nmap {verbose} --traceroute {alvo}",
        }
        
        comando = scans_preview.get(scan_tipo, f"nmap {verbose} {alvo}")
        self.entry_comando.delete(1.0, tk.END)
        self.entry_comando.insert(tk.END, comando)
    
    def run_nmap_custom(self):
        comando_texto = self.entry_comando.get("1.0", tk.END).strip()
        if not comando_texto or not self.nmap_target.get().strip():
            messagebox.showerror("Erro", "Digite um alvo e/ou comando válido!")
            return
        
        self.nmap_output.delete(1.0, tk.END)
        self.nmap_output.insert(tk.END, f"Executando: {comando_texto}\n\n{'='*80}\n")
        self.root.update()
        
        try:
            cmd_list = comando_texto.split()
            result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=300)
            
            self.nmap_output.insert(tk.END, result.stdout)
            if result.stderr:
                self.nmap_output.insert(tk.END, "\nERROS:\n" + result.stderr)
                
        except FileNotFoundError:
            self.nmap_output.insert(tk.END, "❌ Nmap não encontrado! Instale e adicione ao PATH.")
        except subprocess.TimeoutExpired:
            self.nmap_output.insert(tk.END, "⏰ Scan excedeu o tempo limite (5 minutos).")
        except Exception as e:
            self.nmap_output.insert(tk.END, f"Erro: {e}")
    
    def create_curl_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Curl")
        
        tk.Label(tab, text="URL:").pack(anchor="w", padx=10, pady=5)
        self.curl_url = tk.Entry(tab, width=80)
        self.curl_url.insert(0, "https://httpbin.org/ip")
        self.curl_url.pack(padx=10, pady=5)
        
        options_frame = tk.Frame(tab)
        options_frame.pack(pady=8)
        
        self.curl_mode = tk.StringVar(value="headers")
        tk.Radiobutton(options_frame, text="Só Headers (-I)", variable=self.curl_mode, value="headers").pack(side="left", padx=10)
        tk.Radiobutton(options_frame, text="Requisição Completa", variable=self.curl_mode, value="full").pack(side="left", padx=10)
        
        tk.Button(tab, text="🌐 Executar Curl", bg="#2196F3", fg="black", font=("Arial", 10, "bold"),
                 command=lambda: self.run_command_thread(self.run_curl)).pack(pady=10)
        
        self.curl_output = scrolledtext.ScrolledText(tab, height=25, font=("Consolas", 9))
        self.curl_output.pack(fill="both", expand=True, padx=10, pady=5)
    
    def create_windows_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Comandos Windows")
        
        ping_frame = tk.LabelFrame(tab, text="Ping Personalizado", padx=10, pady=5)
        ping_frame.pack(fill="x", padx=10, pady=8)
        
        tk.Label(ping_frame, text="Site ou IP:").pack(anchor="w")
        self.ping_target = tk.Entry(ping_frame, width=50)
        self.ping_target.insert(0, "google.com")
        self.ping_target.pack(pady=5)
        
        tk.Button(ping_frame, text="📡 Executar Ping", bg="#4CAF50", fg="black",
                 command=lambda: self.run_command_thread(self.run_ping)).pack(pady=5)
        
        tk.Label(tab, text="Outros Comandos:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(15,5))
        
        commands = {
            "🖥️ IP Config Completo": "ipconfig /all",
            "🔌 Netstat (Conexões Ativas)": "netstat -ano",
            "📊 System Information": "systeminfo",
            "🌐 Mostrar DNS Cache": "ipconfig /displaydns",
            "🔄 Limpar Cache DNS": "ipconfig /flushdns"
        }
        
        for text, cmd in commands.items():
            btn = tk.Button(tab, text=text, width=40, 
                          command=lambda c=cmd: self.run_command_thread(lambda: self.run_windows_cmd(c)))
            btn.pack(pady=4)
        
        self.win_output = scrolledtext.ScrolledText(tab, height=22, font=("Consolas", 9))
        self.win_output.pack(fill="both", expand=True, padx=10, pady=10)
    
    def run_command_thread(self, func):
        thread = threading.Thread(target=func, daemon=True)
        thread.start()
    
    def run_curl(self):
        url = self.curl_url.get().strip()
        if not url:
            messagebox.showerror("Erro", "Digite uma URL!")
            return
        
        self.curl_output.delete(1.0, tk.END)
        self.root.update()
        
        mode = self.curl_mode.get()
        
        try:
            if mode == "headers":
                cmd_str = f"curl -I -L --silent {url}"
                self.curl_output.insert(tk.END, f"Executando: {cmd_str}\n")
                self.curl_output.insert(tk.END, "="*80 + "\n\n")
                self.root.update()
                
                result = subprocess.run(["curl", "-I", "-L", "--silent", url], 
                                      capture_output=True, text=True, timeout=30)
            else:
                cmd_str = f"curl -L --silent {url}"
                self.curl_output.insert(tk.END, f"Executando: {cmd_str}\n")
                self.curl_output.insert(tk.END, "="*80 + "\n\n")
                self.root.update()
                
                result = subprocess.run(["curl", "-L", "--silent", url], 
                                      capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                self.curl_output.insert(tk.END, result.stdout)
            if result.stderr:
                self.curl_output.insert(tk.END, "\nERROS:\n" + result.stderr)
                
        except FileNotFoundError:
            self.curl_output.insert(tk.END, "❌ Curl não encontrado! Use o curl nativo do Windows 10.")
        except subprocess.TimeoutExpired:
            self.curl_output.insert(tk.END, "⏰ Timeout: A requisição demorou muito.")
        except Exception as e:
            self.curl_output.insert(tk.END, f"Erro: {e}")
    
    def run_ping(self):
        target = self.ping_target.get().strip()
        if not target:
            messagebox.showerror("Erro", "Digite um alvo!")
            return
        self.win_output.delete(1.0, tk.END)
        self.win_output.insert(tk.END, f"Executando ping -n 5 -4 {target}\n\n")
        try:
            result = subprocess.run(f"ping {target} -n 5 -4", shell=True, capture_output=True, text=True, timeout=30)
            self.win_output.insert(tk.END, result.stdout)
        except Exception as e:
            self.win_output.insert(tk.END, f"Erro: {e}")
    
    def run_windows_cmd(self, command):
        self.win_output.delete(1.0, tk.END)
        self.win_output.insert(tk.END, f"Executando: {command}\n\n")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            self.win_output.insert(tk.END, result.stdout)
            if result.stderr:
                self.win_output.insert(tk.END, "\nERROS:\n" + result.stderr)
        except Exception as e:
            self.win_output.insert(tk.END, f"Erro: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkToolGUI(root)
    root.mainloop()
