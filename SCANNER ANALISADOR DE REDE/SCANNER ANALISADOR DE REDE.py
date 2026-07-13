import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import re
from datetime import datetime
import platform
import json
import os

class ZenmapClone:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SCANNER ANALISADOR DE REDE")

        # Maximiza a janela
        try:
            if platform.system() == "Windows":
                self.root.state("zoomed")
            else:
                self.root.attributes("-zoomed", True)
        except Exception:
            self.root.geometry("1000x780")

        # ==================== TEMA DARK ====================
        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.accent = "#00bfff"
        self.green = "#00ff9d"
        self.red = "#ff4d4d"
        self.gray = "#2d2d2d"
        self.orange = "#ff8c00"

        self.root.configure(bg=self.bg_color)

        # Estilo Treeview
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", background="#2d2d2d", foreground="#d4d4d4",
                           fieldbackground="#2d2d2d", rowheight=25)
        self.style.configure("Treeview.Heading", background="#383838", foreground="#ffffff")
        self.style.map("Treeview", background=[('selected', '#00bfff')], foreground=[('selected', 'black')])

        # ==================== PERFIS ====================
        self.profiles = {
            "Scan rápido": "nmap -D RND:20 -sS -F",
            "Top 100 portas": "nmap -D RND:20 --open -sS --top-ports 100",
            "Top 1000 portas": "nmap -D RND:20 --open -sS --top-ports 1000",
            "Detecção de serviços": "nmap -D RND:20 -sV",
            "Detecção de sistema operacional": "nmap -D RND:20 -O",
            "Scripts NSE padrão": "nmap -D RND:20 -sC",
            "Scan de vulnerabilidades": "nmap -D RND:20 --script vuln",
            "Scan de vulnerabilidades e serviços": "nmap -sV -D RND:20 --script vuln",
            "Scan de vulnerabilidades e serviços + SO": "nmap -sV -O -D RND:20 --script vuln",
            "Scan agressivo": "nmap -D RND:20 -A",
            "Scan completo TCP": "nmap -D RND:20 -p- -sS",
            "Scan UDP": "nmap -D RND:20 -sU",
            "Detecção de firewall": "nmap -D RND:20 -sA",
            "Scan stealth FIN": "nmap -D RND:20 -sF",
            "Scan Xmas": "nmap -D RND:20 -sX",
            "Scan NULL": "nmap -D RND:20 -sN",
            "Enumeração SMB": "nmap --script smb-enum-shares,smb-enum-users",
            "Brute FTP": "nmap --script ftp-brute",
            "Brute SSH": "nmap --script ssh-brute",
            "Detectar HTTP": "nmap -sV --script http-title,http-headers",
            "SSL/TLS": "nmap --script ssl-enum-ciphers -p 443",
            "Whois": "nmap --script whois-domain.nse",
            "dns-brute": "nmap --script dns-brute",
            "Traceroute": "nmap --traceroute",
            "Intense scan": "nmap -T4 -A",
            "Intense scan + UDP": "nmap -sS -sU -T4 -A",
            "Quick scan": "nmap -T4 -F",
            "Regular scan": "nmap",
            "Ping scan": "nmap -sn",
            "Slow comprehensive scan": "nmap -sS -sV -sC -T2 -A",
            "vulnerabilidades e serviços": "nmap -Pn -sV -D RND:20 --script vuln",
            "ports 100 vulnerabilidades e serviços": "nmap -Pn -sV --script vuln --top-ports 100",
            "100 portas": "nmap -Pn -D RND:20 --open -sS --top-ports 100",
            "defeat-rst-ratelimit 100 portas": "nmap -Pn -D RND:20 --defeat-rst-ratelimit --open -sS --top-ports 100"

        }

        self.load_profiles()

        self.current_ip = ""
        self.ports_list = []
        self.last_output = ""
        self.os_info = ""
        self.ip_list = []          # Lista de IP carregados do arquivo
        self.current_target_index = 0  # Índice do IP atual sendo escaneado
        self.scan_thread = None
        self.stop_flag = False

        self.create_widgets()

    def load_profiles(self):
        self.json_file = "profiles.json"
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    saved_profiles = json.load(f)
                    self.profiles.update(saved_profiles)
            except Exception as e:
                print(f"Erro ao carregar profiles.json: {e}")

    def save_profiles(self):
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar os perfis:\n{str(e)}")

    def create_widgets(self):
        # ==================== TOP FRAME (Informações) ====================
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill="x", padx=8, pady=6)

        # Target
        tk.Label(top_frame, text="Target:", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(side="left", padx=(5, 2))
        
        self.target_entry = tk.Entry(top_frame, width=35, font=("Arial", 11), bg=self.gray, fg=self.fg_color, insertbackground=self.accent)
        self.target_entry.pack(side="left", padx=5)

        # Botão ip.txt
        self.btn_load_ip = tk.Button(top_frame, text="📂 ip.txt", width=9, bg="#9E1DB4", fg="black", font=("Arial", 9, "bold"), command=self.load_ip_file)
        self.btn_load_ip.pack(side="left", padx=5)

        # Contador de IP
        self.ip_count_label = tk.Label(top_frame, text="", bg=self.bg_color, fg=self.green, font=("Arial", 9))
        self.ip_count_label.pack(side="left", padx=2)

        # Profile
        tk.Label(top_frame, text="Profile:", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(side="left", padx=(20, 2))
        
        self.profile_combo = ttk.Combobox(top_frame, values=list(self.profiles.keys()), width=35, state="readonly")
        self.profile_combo.set("Detecção de serviços")
        self.profile_combo.pack(side="left", padx=5)

        # Verbosity
        tk.Label(top_frame, text="Verbosity:", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(side="left", padx=(20, 5))
        
        self.verbosity_combo = ttk.Combobox(top_frame, values=["Normal (sem -v)", "-v", "-vv", "-vvv"], width=16, state="readonly")
        self.verbosity_combo.set("Normal (sem -v)")
        self.verbosity_combo.pack(side="left", padx=5)

        # ==================== FRAME DOS BOTÕES DE AÇÃO ====================
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=8, pady=4)

        # Botões principais
        self.btn_scan = tk.Button(btn_frame, text="▶ Scan", width=10, bg=self.green, fg="black", font=("Arial", 10, "bold"), command=self.start_scan)
        self.btn_scan.pack(side="left", padx=5)

        self.btn_cancel = tk.Button(btn_frame, text="⏹ Stop", width=10, bg=self.red, fg="black", font=("Arial", 10, "bold"), command=self.cancel_scan)
        self.btn_cancel.pack(side="left", padx=5)

        tk.Button(btn_frame, text="✅ Custom", width=10, bg="#31B3F0", fg="black", font=("Arial", 10, "bold"), command=self.add_new_profile).pack(side="left", padx=5)

        tk.Button(btn_frame, text="💾 Salvar Resultados", width=20, bg="#FF9800", fg="black", font=("Arial", 10, "bold"), command=self.save_results).pack(side="left", padx=5)

        # ==================== COMMAND FRAME ====================
        cmd_frame = tk.Frame(self.root, bg=self.bg_color)
        cmd_frame.pack(fill="x", padx=8, pady=4)

        tk.Label(cmd_frame, text="Command:", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.cmd_label = tk.Label(cmd_frame, text="", bg=self.bg_color, fg=self.accent, font=("Consolas", 11), anchor="w")
        self.cmd_label.pack(side="left", padx=5, fill="x")

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=5)

        self.output_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.output_tab, text="Nmap Output")
        self.output_text = scrolledtext.ScrolledText(self.output_tab, wrap=tk.WORD, font=("Consolas", 11), bg="#0d0d0d", fg="#d4d4d4")
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.hosts_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.hosts_tab, text="Hosts / Ports")
        self.hosts_tree = ttk.Treeview(self.hosts_tab, columns=("Host", "IP", "Port", "State", "Service", "Version"), show="headings")
        widths = [190, 150, 70, 70, 140, 340]
        for col, w in zip(self.hosts_tree["columns"], widths):
            self.hosts_tree.heading(col, text=col)
            self.hosts_tree.column(col, width=w)
        self.hosts_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.details_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.details_tab, text="Host Details")
        self.details_text = scrolledtext.ScrolledText(self.details_tab, wrap=tk.WORD, font=("Consolas", 10), bg="#0d0d0d", fg=self.fg_color)
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.topo_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.topo_tab, text="serviço/versão")
        self.topo_text = scrolledtext.ScrolledText(self.topo_tab, wrap=tk.WORD, font=("Consolas", 11), bg="#0d0d0d", fg="#00ff9d")
        self.topo_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.scans_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.scans_tab, text="Scans")
        self.scans_text = scrolledtext.ScrolledText(self.scans_tab, wrap=tk.WORD, font=("Consolas", 10), bg="#0d0d0d", fg=self.fg_color)
        self.scans_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.os_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.os_tab, text="Sistema Operacional")
        self.os_text = scrolledtext.ScrolledText(self.os_tab, wrap=tk.WORD, font=("Consolas", 11), bg="#0d0d0d", fg=self.orange)
        self.os_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.status = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor="w", bg=self.gray, fg=self.fg_color)
        self.status.pack(side="bottom", fill="x")

        self.target_entry.bind("<KeyRelease>", lambda e: self.update_command())
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.update_command())
        self.verbosity_combo.bind("<<ComboboxSelected>>", lambda e: self.update_command())

    # ==================== CARREGAR IP.TXT ====================
    def load_ip_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo ip.txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{str(e)}")
            return

        # Extrair IP válidos
        self.ip_list = []
        ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Pega o primeiro IP encontrado em cada linha
            match = ip_pattern.search(line)
            if match:
                ip = match.group(1)
                if ip not in self.ip_list:
                    self.ip_list.append(ip)

        if not self.ip_list:
            messagebox.showwarning("Aviso", "Nenhum IP válido encontrado no arquivo!")
            self.ip_count_label.config(text="")
            return

        # Atualiza a label com a contagem
        self.ip_count_label.config(text=f"{len(self.ip_list)}   IP")

        # Coloca o primeiro IP no campo target
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, self.ip_list[0])

        self.update_command()
        messagebox.showinfo("IP Carregados", f"{len(self.ip_list)} IP carregados com sucesso!\n\nClique em 'Scan' para escanear todos ou altere o target manualmente.")

    # ==================== NOVO PERFIL ====================
    def add_new_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Novo Perfil Customizado")
        dialog.geometry("720x460")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Nome do Perfil", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(15,5))
        name_entry = tk.Entry(dialog, font=("Arial", 11), bg=self.gray, fg=self.fg_color, insertbackground=self.accent)
        name_entry.pack(fill="x", padx=15, pady=5)

        tk.Label(dialog, text="Opções do Nmap | sem o nmap  | ou asim   nmap -sV -D RND:20 --script vuln", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(10,5))
        cmd_text = tk.Text(dialog, height=14, font=("Consolas", 11), bg="#0d0d0d", fg="#d4d4d4", insertbackground=self.accent)
        cmd_text.pack(fill="both", expand=True, padx=15, pady=5)
        cmd_text.insert("1.0", "")

        def save_profile():
            name = name_entry.get().strip()
            cmd = cmd_text.get("1.0", tk.END).strip()

            if not name:
                messagebox.showerror("Erro", "Nome do perfil é obrigatório!", parent=dialog)
                return
            if not cmd:
                messagebox.showerror("Erro", "Digite as opções do nmap!", parent=dialog)
                return

            if cmd.lower().startswith("nmap "):
                cmd = cmd[5:].strip()

            self.profiles[name] = f"nmap {cmd}"
            self.save_profiles()
            self.refresh_profiles()
            messagebox.showinfo("Sucesso", f"Perfil: {name}    salvo", parent=dialog)
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=self.bg_color)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Salvar Perfil", bg=self.green, fg="black", font=("Arial", 10, "bold"), command=save_profile).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancelar", bg=self.red, fg="black", font=("Arial", 10, "bold"), command=dialog.destroy).pack(side="left", padx=8)

        name_entry.focus_set()

    def refresh_profiles(self):
        current = self.profile_combo.get()
        self.profile_combo['values'] = list(self.profiles.keys())
        if current in self.profiles:
            self.profile_combo.set(current)
        else:
            self.profile_combo.set("Detecção de serviços")

    def update_command(self):
        target = self.target_entry.get().strip()
        base = self.profiles.get(self.profile_combo.get(), "nmap")
        verbosity = self.verbosity_combo.get()
        verb_flag = "" if verbosity == "Normal (sem -v)" else verbosity

        full_cmd = f"{base} {verb_flag} {target}".strip()
        self.cmd_label.config(text=full_cmd if target else base)

    # ==================== SALVAR RESULTADOS ====================
    def save_results(self):
        if not self.last_output:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Escolher Formato")
        dialog.geometry("300x150")
        dialog.configure(bg=self.bg_color)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Escolha o Formato do Relatório",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(pady=15)

        def save_txt():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text file", "*.txt")],
                initialfile="Resultados.txt"
            )

            if not file_path:
                return

            now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            target = self.target_entry.get().strip() or "Desconhecido"

            self._save_as_txt(file_path, target, now)

            dialog.destroy()
            messagebox.showinfo("Sucesso", f"Salvo Em\n\n{file_path}")

        def save_html():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML file", "*.html")],
                initialfile="Resultados.html"
            )

            if not file_path:
                return

            now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            target = self.target_entry.get().strip() or "Desconhecido"

            self._save_as_html(file_path, target, now)

            dialog.destroy()
            messagebox.showinfo("Sucesso", f"Salvo Em\n\n{file_path}")

        btn_frame = tk.Frame(dialog, bg=self.bg_color)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="TXT",
            width=10,
            bg="#00ff9d",
            fg="black",
            command=save_txt
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="HTML",
            width=10,
            bg="#00bfff",
            fg="black",
            command=save_html
        ).pack(side="left", padx=10)


    def _save_as_txt(self, file_path, target, now):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("="*90 + "\n")
            f.write(" RELATÓRIO COMPLETO DE SCAN NMAP - TODAS AS ABAS\n")
            f.write("="*90 + "\n\n")
            
            f.write(f"Data/Hora : {now}\n\n")
            f.write(f"Alvo      : {target}\n\n")
            f.write(f"IP        : {self.current_ip}\n\n")
            f.write(f"Perfil    : {self.profile_combo.get()}\n\n")
            f.write(f"Verbosity : {self.verbosity_combo.get()}\n\n")

            f.write("="*60 + "\n")
            f.write("1. NMAP OUTPUT (SAÍDA COMPLETA)\n")
            f.write("="*60 + "\n\n")
            for line in self.last_output.strip().splitlines():
                f.write(line + "\n\n")

            f.write("="*60 + "\n")
            f.write("2. HOSTS / PORTS\n")
            f.write("="*60 + "\n\n")
            f.write("HOST\tIP\tPORTA\tSTATE\tSERVICE\t\tVERSION\n")
            f.write("-"*100 + "\n")
            for port, state, service, version in self.ports_list:
                f.write(f"{target}\t{self.current_ip}\t{port}\t{state}\t{service}\t\t{version}\n")
            f.write(f"\nTotal de portas abertas: {len(self.ports_list)}\n\n\n")

            f.write("="*60 + "\n")
            f.write("3. SERVIÇO / VERSÃO\n")
            f.write("="*60 + "\n\n")
            f.write(self.topo_text.get("1.0", tk.END).strip() + "\n\n\n")

            f.write("="*60 + "\n")
            f.write("4. SCANS\n")
            f.write("="*60 + "\n\n")
            f.write(self.scans_text.get("1.0", tk.END).strip() + "\n\n\n")

            f.write("="*60 + "\n")
            f.write("5. SISTEMA OPERACIONAL\n")
            f.write("="*60 + "\n\n")
            f.write(self.os_text.get("1.0", tk.END).strip() + "\n\n\n")

            f.write("="*60 + "\n")
            f.write("6. HOST DETAILS\n")
            f.write("="*60 + "\n\n")
            f.write(self.details_text.get("1.0", tk.END).strip() + "\n\n")

            f.write("="*90 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("="*90 + "\n")

    def _save_as_html(self, file_path, target, now):
        def color_line(line):
            line = line.replace("<", "&lt;").replace(">", "&gt;")
            
            if line.startswith("Not shown:"):
                return f'{line}<br>'
            
            if line.strip().startswith("PORT") and "STATE" in line and "SERVICE" in line:
                return f'<span style="color:#00bfff; font-weight:bold;">{line}</span>'
            
            elif "open" in line and ("/tcp" in line or "/udp" in line):
                return f'<span style="color:#00ff9d;">{line}</span>'
            
            elif "filtered" in line:
                return f'<span style="color:#ff8c00;">{line}</span>'
            
            elif any(x in line for x in ["Host is up", "Service Info:", "OS details", "CPE:", 
                                       "MAC Address", "Nmap scan report", "Discovered open port"]):
                return f'<span style="color:#ff8c00;">{line}</span>'
            
            else:
                return line

        colored_lines = [color_line(line) for line in self.last_output.strip().splitlines()]
        nmap_formatted = "<br>".join(colored_lines)
        

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório Nmap - {target}</title>
    <style>
        body {{ font-family: Consolas, monospace; background: #1e1e1e; color: #d4d4d4; padding: 30px; line-height: 1.8; }}
        h1, h2 {{ color: #00bfff; }}
        .nmap-output {{ background: #0d0d0d; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 14px; line-height: 1.9; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #383838; color: #00bfff; font-weight: bold; }}
        td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
        .section {{ margin: 50px 0; }}
    </style>
</head>
<body>
    <h1>Relatório Completo de Scan Nmap</h1>
    <p><strong>Data:</strong> {now} | <strong>Alvo:</strong> {target} | <strong>IP:</strong> {self.current_ip}</p>
    <p><strong>Perfil:</strong> {self.profile_combo.get()} | <strong>Verbosity:</strong> {self.verbosity_combo.get()}</p>

    <div class="section">
        <h2>1. Nmap Output (Saída Completa)</h2>
        <div class="nmap-output">{nmap_formatted}</div>
    </div>

    <div class="section">
        <h2>2. Hosts / Ports</h2>
        <table>
            <tr><th>Host</th><th>IP</th><th>Porta</th><th>Estado</th><th>Serviço</th><th>Versão</th></tr>
"""
        for port, state, service, version in self.ports_list:
            html += f"""            <tr><td>{target}</td><td>{self.current_ip}</td><td>{port}</td><td>{state}</td><td>{service}</td><td>{version}</td></tr>
"""
        html += f"""        </table>
        <p><strong>Total de portas abertas:</strong> {len(self.ports_list)}</p>
    </div>

    <div class="section">
        <h2>3. Serviço / Versão</h2>
        <pre>{self.topo_text.get("1.0", tk.END).strip()}</pre>
    </div>

    <div class="section">
        <pre>--------------------------------------------------------------------------------</pre>
        <h2>4. Scans</h2>
        <pre>{self.scans_text.get("1.0", tk.END).strip()}</pre>
    </div>

    <div class="section">
        <pre>--------------------------------------------------------------------------------</pre>
        <h2>5. Sistema Operacional</h2>
        <pre>{self.os_text.get("1.0", tk.END).strip()}</pre>
    </div>

    <div class="section">
         <pre>--------------------------------------------------------------------------------</pre>
        <h2>6. Host Details</h2>
        <pre>{self.details_text.get("1.0", tk.END).strip()}</pre>
    </div>

</body>
</html>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html) 

    # ==================== RESTO ====================
    def colored_output(self, line):
        if "open" in line and ("/tcp" in line or "/udp" in line):
            self.output_text.insert(tk.END, line, "open")
        elif "filtered" in line:
            self.output_text.insert(tk.END, line, "filtered")
        elif any(x in line for x in ["Service Info:", "OSs:", "CPE:", "MAC Address", "Host is up", "OS details"]):
            self.output_text.insert(tk.END, line, "info")
        else:
            self.output_text.insert(tk.END, line)

    def parse_and_fill_tabs(self, output, target):
        self.last_output = output
        self.current_ip = target
        self.os_info = ""

        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output)
        if ip_match:
            self.current_ip = ip_match.group(1)

        self.ports_list = []
        for item in self.hosts_tree.get_children():
            self.hosts_tree.delete(item)

        self.details_text.delete(1.0, tk.END)
        self.topo_text.delete(1.0, tk.END)
        self.scans_text.delete(1.0, tk.END)
        self.os_text.delete(1.0, tk.END)

        for line in output.splitlines():
            port_match = re.search(r'(\d+)/(\w+)\s+(open)\s+([\w-]+)\s*(.*)', line)
            if port_match:
                port = port_match.group(1) + "/" + port_match.group(2)
                state = port_match.group(3)
                service = port_match.group(4)
                version = port_match.group(5).strip()
                self.ports_list.append((port, state, service, version))
                self.hosts_tree.insert("", "end", values=(target, self.current_ip, port.split('/')[0], state, service, version))

            if any(k in line for k in ["OS details", "OS:", "CPE:", "Aggressive OS guesses", "Running:", "Service Info:", "MAC Address"]):
                self.os_info += line + "\n\n"
            if any(k in line for k in ["Host is up", "Service Info", "OSs:", "MAC Address"]):
                self.details_text.insert(tk.END, line + "\n\n")

        if self.os_info.strip():
            self.os_text.insert(tk.END, "=== DETECÇÃO DE SISTEMA OPERACIONAL ===\n\n" + self.os_info)
        else:
            self.os_text.insert(tk.END, "Nenhuma informação de SO detectada.\n\nUse perfis com -O ou -A.\n")

        self.topo_text.insert(tk.END, "PORT\t\tSTATE\tSERVICE\t\tVERSION\n" + "-"*80 + "\n")
        for port, state, service, version in self.ports_list:
            self.topo_text.insert(tk.END, f"{port:<12}\t{state:<8}\t{service:<12}\t{version}\n")

        self.scans_text.insert(tk.END, f"Scan finalizado: {datetime.now().strftime('%H:%M:%S')}\n\nTotal de portas abertas: {len(self.ports_list)}\n")

    def run_nmap(self, target):
        base_cmd = self.profiles.get(self.profile_combo.get(), "nmap")
        try:
            cmd_parts = base_cmd.split()
            for v in ["-v", "-vv", "-vvv"]:
                if v in cmd_parts:
                    cmd_parts.remove(v)

            verbosity = self.verbosity_combo.get()
            if verbosity != "Normal (sem -v)":
                cmd_parts.append(verbosity)

            command = cmd_parts + [target]

            if platform.system() == "Windows":
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                si = None
                creationflags = 0

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='ignore',
                                       startupinfo=si, creationflags=creationflags)

            output = ""
            for line in process.stdout:
                if any(phrase in line for phrase in ["Read data files from", "Nmap done:", "scanned in"]):
                    continue
                output += line
                self.colored_output(line + "\n")
                self.output_text.see(tk.END)
                self.root.update_idletasks()

            process.wait()
            self.parse_and_fill_tabs(output, target)
            self.status.config(text=f"Scan concluído: {target}")

        except Exception as e:
            self.output_text.insert(tk.END, f"\nErro: {str(e)}\n")
            self.status.config(text="Erro")

    def run_scan_thread(self):
        """Executa scans em todos os IPs da lista ou apenas no target manual"""
        target = self.target_entry.get().strip()

        # Se tem ip_list carregada, varre todos os IPs
        if self.ip_list:
            self.stop_flag = False
            for i, ip in enumerate(self.ip_list):
                if self.stop_flag:
                    break

                self.current_target_index = i
                self.target_entry.delete(0, tk.END)
                self.target_entry.insert(0, ip)
                self.update_command()

                # Mostra progresso no output
                self.output_text.insert(tk.END, f"\n{'='*60}\n")
                self.output_text.insert(tk.END, f" Scan {i+1}/{len(self.ip_list)} - Alvo: {ip}\n")
                self.output_text.insert(tk.END, f"{'='*60}\n\n")
                self.output_text.see(tk.END)
                self.status.config(text=f"Scanning {i+1}/{len(self.ip_list)}: {ip}")

                self.run_nmap(ip)

                # Se não for o último, adiciona separador
                if i < len(self.ip_list) - 1 and not self.stop_flag:
                    self.output_text.insert(tk.END, f"\n{'='*60}\n")
                    self.output_text.insert(tk.END, f" Scan do IP {ip} finalizado. Próximo...\n")
                    self.output_text.insert(tk.END, f"{'='*60}\n\n")
                    self.output_text.see(tk.END)

            if not self.stop_flag:
                self.output_text.insert(tk.END, f"\n{'='*60}\n")
                self.output_text.insert(tk.END, f" TODOS OS {len(self.ip_list)} IPs FORAM ESCANEADOS!\n")
                self.output_text.insert(tk.END, f"{'='*60}\n")
                self.status.config(text=f"Scan completo - {len(self.ip_list)} IPs")
            else:
                self.output_text.insert(tk.END, f"\nScan cancelado pelo usuário.\n")
                self.status.config(text="Cancelado")

        else:
            # Modo manual: escaneia apenas o target digitado
            if not target:
                self.output_text.insert(tk.END, "\nErro: Digite um alvo ou carregue um ip.txt!\n")
                self.status.config(text="Erro: sem alvo")
                return
            self.run_nmap(target)
            self.status.config(text=f"Scan concluído: {target}")

    def start_scan(self):
        target = self.target_entry.get().strip()

        if not target and not self.ip_list:
            messagebox.showerror("Erro", "Digite um alvo ou carregue um arquivo ip.txt!")
            return

        self.update_command()
        self.output_text.delete(1.0, tk.END)
        self.output_text.tag_config("open", foreground="#00ff9d")
        self.output_text.tag_config("filtered", foreground="#ff8c00")
        self.output_text.tag_config("info", foreground="#ff8c00")
        self.output_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando scan...\n\n")
        self.status.config(text="Scanning...")

        self.scan_thread = threading.Thread(target=self.run_scan_thread)
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def cancel_scan(self):
        self.stop_flag = True
        self.output_text.insert(tk.END, "\n[!] Cancelando scan... (aguarde o término do scan atual)\n")
        self.status.config(text="Cancelando...")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ZenmapClone()
    app.run()
