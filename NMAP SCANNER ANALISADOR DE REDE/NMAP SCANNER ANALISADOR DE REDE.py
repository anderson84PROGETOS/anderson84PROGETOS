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
        self.root.title("NMAP SCANNER ANALISADOR DE REDE")

        # ==================== JANELA ====================

        try:
            if platform.system() == "Windows":
                self.root.state("zoomed")
            else:
                self.root.attributes("-zoomed", True)
        except Exception:
            self.root.geometry("1200x780")

        # ==================== TEMA DARK ====================

        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.accent = "#00bfff"
        self.green = "#00ff9d"
        self.red = "#ff4d4d"
        self.gray = "#2d2d2d"
        self.orange = "#ff8c00"
        self.abobora = "#FF7518"

        self.root.configure(bg=self.bg_color)

        # ==================== ESTILO ====================

        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(
            "Treeview",
            background="#2d2d2d",
            foreground="#d4d4d4",
            fieldbackground="#2d2d2d",
            rowheight=25
        )

        self.style.configure(
            "Treeview.Heading",
            background="#383838",
            foreground="#ffffff"
        )

        self.style.map(
            "Treeview",
            background=[("selected", "#00bfff")],
            foreground=[("selected", "black")]
        )

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
            
            "defeat-rst-ratelimit 100 portas": "nmap -Pn -D RND:20 --defeat-rst-ratelimit --open -sS --top-ports 100",

            "-p21,22,53,111": "nmap -D RND:20 --open -sV -p21,22,53,111",

            "Porta 80,43": "nmap -D RND:20 -sV -p80,43",

            "Porta 43": "nmap -D RND:20 -sV -p43",

            "FTP": "nmap -D RND:20 --script ftp-anon,ftp-syst -p 21",

            "SSH": "nmap -D RND:20 -sV --script ssh2-enum-algos -p 22",

            "FTP Brute": "nmap -D RND:20 --script ftp-brute -p 21",

            "FTP CVE-2010-4221": "nmap -D RND:20 --script ftp-vuln-cve2010-4221 -p 21",

            "SSH Algoritmos": "nmap -D RND:20 --script ssh2-enum-algos -p 22",

            "ssh-brute": "nmap -d -p 22 --script ssh-brute --script-args \"userdb=users.lst,passdb=pass.lst,ssh-brute.timeout=4s\"",   

            "SMB Protocol Enumeration": "nmap --script smb-os-discovery,smb-protocols -p 445",

            "Ping Scan / Host Discovery": "nmap -sn -R",

            "Aggressive Scan": "nmap -sV -A -R",

            "top-ports 100":"nmap -sV -A -R --top-ports 100",

            "Telnet Encryption": "nmap -p 23 --script telnet-encryption",

        }

        self.load_profiles()

        # ==================== VARIÁVEIS ====================

        self.current_ip = ""
        self.ports_list = []
        self.last_output = ""
        self.os_info = ""

        self.ip_list = []
        self.current_target_index = 0

        self.scan_thread = None
        self.stop_flag = False
        self.nmap_process = None
        self.scan_running = False

        self.create_widgets()

    # ==========================================================
    # PERFIS
    # ==========================================================

    def load_profiles(self):
        self.json_file = "profiles.json"

        if os.path.exists(self.json_file):
            try:
                with open(
                    self.json_file,
                    "r",
                    encoding="utf-8"
                ) as f:
                    saved_profiles = json.load(f)

                if isinstance(saved_profiles, dict):
                    self.profiles.update(saved_profiles)

            except Exception as e:
                print(f"Erro ao carregar profiles.json: {e}")

    def save_profiles(self):
        try:
            with open(
                self.json_file,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    self.profiles,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar os perfis:\n{str(e)}")

    # ==========================================================
    # INTERFACE
    # ==========================================================

    def create_widgets(self):

        # ==================== TOP FRAME ====================

        top_frame = tk.Frame(
            self.root,
            bg=self.bg_color
        )

        top_frame.pack(
            fill="x",
            padx=8,
            pady=6
        )

        # Target

        tk.Label(
            top_frame,
            text="Target:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(5, 2)
        )

        self.target_entry = tk.Entry(
            top_frame,
            width=35,
            font=("Arial", 11),
            bg=self.gray,
            fg=self.fg_color,
            insertbackground=self.accent
        )

        self.target_entry.pack(
            side="left",
            padx=5
        )

        # IP.TXT

        self.btn_load_ip = tk.Button(
            top_frame,
            text="📂 ip.txt",
            width=9,
            bg="#9E1DB4",
            fg="black",
            font=("Arial", 9, "bold"),
            command=self.load_ip_file
        )

        self.btn_load_ip.pack(
            side="left",
            padx=5
        )

        # Contador

        self.ip_count_label = tk.Label(
            top_frame,
            text="",
            bg=self.bg_color,
            fg=self.green,
            font=("Arial", 9)
        )

        self.ip_count_label.pack(
            side="left",
            padx=2
        )

        # Profile

        tk.Label(
            top_frame,
            text="Profile:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(20, 2)
        )

        self.profile_combo = ttk.Combobox(
            top_frame,
            values=list(self.profiles.keys()),
            width=60,
            state="readonly"
        )

        self.profile_combo.set("Detecção de serviços")

        self.profile_combo.pack(
            side="left",
            padx=5
        )

        # Verbosity

        tk.Label(
            top_frame,
            text="Verbosity:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(20, 5)
        )

        self.verbosity_combo = ttk.Combobox(
            top_frame,
            values=[
                "Normal (sem -v)",
                "-v",
                "-vv",
                "-vvv"
            ],
            width=16,
            state="readonly"
        )

        self.verbosity_combo.set("Normal (sem -v)")

        self.verbosity_combo.pack(
            side="left",
            padx=5
        )

        # ==================== BOTÕES ====================

        btn_frame = tk.Frame(
            self.root,
            bg=self.bg_color
        )

        btn_frame.pack(
            fill="x",
            padx=8,
            pady=4
        )

        self.btn_scan = tk.Button(
            btn_frame,
            text="▶ Scan",
            width=10,
            bg=self.green,
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.start_scan
        )

        self.btn_scan.pack(
            side="left",
            padx=5
        )

        self.btn_cancel = tk.Button(
            btn_frame,
            text="⏹ CANCELAR SCAN",
            width=18,
            bg=self.red,
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.cancel_scan
        )

        self.btn_cancel.pack(
            side="left",
            padx=5
        )

        tk.Button(
            btn_frame,
            text="✅ Custom",
            width=10,
            bg="#31B3F0",
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.add_new_profile
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            btn_frame,
            text="💾 Salvar Resultados",
            width=20,
            bg="#FF9800",
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.save_results
        ).pack(
            side="left",
            padx=5
        )

        # ==================== COMMAND ====================

        cmd_frame = tk.Frame(
            self.root,
            bg=self.bg_color
        )

        cmd_frame.pack(
            fill="x",
            padx=8,
            pady=4
        )

        tk.Label(
            cmd_frame,
            text="Command:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=5
        )

        self.cmd_label = tk.Label(
            cmd_frame,
            text="",
            bg=self.bg_color,
            fg=self.accent,
            font=("Consolas", 11),
            anchor="w"
        )

        self.cmd_label.pack(
            side="left",
            padx=5,
            fill="x",
            expand=True
        )

        # ==================== NOTEBOOK ====================

        self.notebook = ttk.Notebook(self.root)

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=5
        )

        # ==================== NMAP OUTPUT ====================

        self.output_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.output_tab,
            text="Nmap Output"
        )

        self.output_text = scrolledtext.ScrolledText(
            self.output_tab,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#0d0d0d",
            fg="#d4d4d4",
            insertbackground="white"
        )

        self.output_text.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== HOSTS / PORTS ====================

        self.hosts_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.hosts_tab,
            text="Hosts / Ports"
        )

        self.hosts_tree = ttk.Treeview(
            self.hosts_tab,
            columns=(
                "Host",
                "IP",
                "Port",
                "State",
                "Service",
                "Version"
            ),
            show="headings"
        )

        widths = [
            190,
            150,
            70,
            70,
            140,
            340
        ]

        for col, width in zip(
            self.hosts_tree["columns"],
            widths
        ):
            self.hosts_tree.heading(
                col,
                text=col
            )

            self.hosts_tree.column(
                col,
                width=width
            )

        self.hosts_tree.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== DETAILS ====================

        self.details_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.details_tab,
            text="Host Details"
        )

        self.details_text = scrolledtext.ScrolledText(
            self.details_tab,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0d0d0d",
            fg=self.fg_color
        )

        self.details_text.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== SERVIÇO / VERSÃO ====================

        self.topo_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.topo_tab,
            text="Serviço/Versão"
        )

        self.topo_text = scrolledtext.ScrolledText(
            self.topo_tab,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#0d0d0d",
            fg=self.green
        )

        self.topo_text.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== SCANS ====================

        self.scans_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.scans_tab,
            text="Scans"
        )

        self.scans_text = scrolledtext.ScrolledText(
            self.scans_tab,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0d0d0d",
            fg=self.fg_color
        )

        self.scans_text.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== SISTEMA OPERACIONAL ====================

        self.os_tab = tk.Frame(
            self.notebook,
            bg=self.bg_color
        )

        self.notebook.add(
            self.os_tab,
            text="Sistema Operacional"
        )

        self.os_text = scrolledtext.ScrolledText(
            self.os_tab,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#0d0d0d",
            fg=self.orange
        )

        self.os_text.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ==================== STATUS ====================

        self.status = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor="w",
            bg=self.gray,
            fg=self.fg_color
        )

        self.status.pack(
            side="bottom",
            fill="x"
        )

        # ==================== TAGS ====================

        self.output_text.tag_configure(
            "open",
            foreground=self.green
        )

        self.output_text.tag_configure(
            "filtered",
            foreground=self.orange
        )

        self.output_text.tag_configure(
            "info",
            foreground=self.orange
        )

        self.output_text.tag_configure(
            "abobora",
            foreground=self.abobora
        )

        # ==================== EVENTOS ====================

        self.target_entry.bind(
            "<KeyRelease>",
            lambda event: self.update_command()
        )

        self.profile_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_command()
        )

        self.verbosity_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_command()
        )

        self.update_command()

    # ==========================================================
    # CARREGAR IP.TXT
    # ==========================================================

    def load_ip_file(self):

        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo ip.txt",
            filetypes=[
                ("Arquivo de texto", "*.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                lines = f.readlines()

        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Não foi possível ler o arquivo:\n{str(e)}"
            )
            return

        self.ip_list = []

        # Regex IPv4
        ip_pattern = re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        )

        for line in lines:

            line = line.strip()

            if not line:
                continue

            match = ip_pattern.search(line)

            if match:

                ip = match.group(0)

                # Validar octetos
                try:
                    octets = [
                        int(x)
                        for x in ip.split(".")
                    ]

                    if all(
                        0 <= x <= 255
                        for x in octets
                    ):
                        if ip not in self.ip_list:
                            self.ip_list.append(ip)

                except ValueError:
                    pass

        if not self.ip_list:

            messagebox.showwarning(
                "Aviso",
                "Nenhum IP válido encontrado no arquivo!"
            )

            self.ip_count_label.config(
                text=""
            )

            return

        self.ip_count_label.config(
            text=f"{len(self.ip_list)} IP"
        )

        self.target_entry.delete(
            0,
            tk.END
        )

        self.target_entry.insert(
            0,
            self.ip_list[0]
        )

        self.update_command()

        messagebox.showinfo(
            "IP Carregados",
            f"{len(self.ip_list)} IP carregados com sucesso!\n\n"
            "Clique em 'Scan' para escanear todos "
            "ou altere o target manualmente."
        )

    # ==========================================================
    # NOVO PERFIL
    # ==========================================================

    def add_new_profile(self):

        dialog = tk.Toplevel(self.root)

        dialog.title("Novo Perfil Customizado")

        dialog.geometry("820x600")

        dialog.configure(bg=self.bg_color)

        dialog.transient(self.root)

        dialog.grab_set()

        tk.Label(dialog, text="Nome do Perfil", bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        name_entry = tk.Entry(dialog, font=("Arial", 11), bg=self.gray, fg=self.fg_color, insertbackground=self.accent)

        name_entry.pack(fill="x", padx=15,  pady=5)

        tk.Label(dialog,
            text=("Opções do Nmap\n\n"""
                "Exemplo com nmap:  nmap -sV --top-ports 100\n\n"
                "Exemplo sem nmap:             -sV --top-ports 100"
            ),

            bg=self.bg_color, fg=self.fg_color, font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 5))

        cmd_text = tk.Text(dialog, height=14, font=("Consolas", 11), bg="#0d0d0d", fg="#d4d4d4", insertbackground=self.accent)

        cmd_text.pack(fill="both", expand=True, padx=15, pady=5)

        def save_profile():

            name = name_entry.get().strip()

            cmd = cmd_text.get("1.0", tk.END).strip()

            if not name:

                messagebox.showerror("Erro", "Nome do perfil é obrigatório!", parent=dialog)

                return

            if not cmd:

                messagebox.showerror("Erro", "Digite as opções do Nmap", parent=dialog)

                return

            if cmd.lower().startswith("nmap "):
                cmd = cmd[5:].strip()

            self.profiles[name] = f"nmap {cmd}"

            self.save_profiles()

            self.refresh_profiles()

            messagebox.showinfo(
                "Sucesso",
                f"Perfil: {name} salvo",
                parent=dialog
            )

            dialog.destroy()

        btn_frame = tk.Frame(
            dialog,
            bg=self.bg_color
        )

        btn_frame.pack(
            pady=12
        )

        tk.Button(
            btn_frame,
            text="Salvar Perfil",
            bg=self.green,
            fg="black",
            font=("Arial", 10, "bold"),
            command=save_profile
        ).pack(
            side="left",
            padx=8
        )

        tk.Button(
            btn_frame,
            text="Cancelar",
            bg=self.red,
            fg="black",
            font=("Arial", 10, "bold"),
            command=dialog.destroy
        ).pack(
            side="left",
            padx=8
        )

        name_entry.focus_set()

    def refresh_profiles(self):

        current = self.profile_combo.get()

        self.profile_combo["values"] = list(
            self.profiles.keys()
        )

        if current in self.profiles:

            self.profile_combo.set(
                current
            )

        else:

            self.profile_combo.set(
                "Detecção de serviços"
            )

        self.update_command()

    # ==========================================================
    # ATUALIZAR COMMAND
    # ==========================================================

    def update_command(self):

        target = self.target_entry.get().strip()

        base = self.profiles.get(
            self.profile_combo.get(),
            "nmap"
        )

        verbosity = self.verbosity_combo.get()

        verb_flag = ""

        if verbosity != "Normal (sem -v)":
            verb_flag = verbosity

        full_cmd = (
            f"{base} {verb_flag} {target}"
        ).strip()

        self.cmd_label.config(
            text=full_cmd
        )

    # ==========================================================
    # SALVAR RESULTADOS
    # ==========================================================

    def save_results(self):

        if not self.last_output:

            messagebox.showwarning(
                "Aviso",
                "Nenhum resultado para salvar!"
            )

            return

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Escolher Formato"
        )

        dialog.geometry(
            "300x150"
        )

        dialog.configure(
            bg=self.bg_color
        )

        dialog.grab_set()

        dialog.resizable(
            False,
            False
        )

        tk.Label(
            dialog,
            text="Escolha o Formato do Relatório",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold")
        ).pack(
            pady=15
        )

        def save_txt():

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[
                    ("Text file", "*.txt")
                ],
                initialfile="Resultados.txt"
            )

            if not file_path:
                return

            now = datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )

            target = (
                self.target_entry.get().strip()
                or "Desconhecido"
            )

            try:

                self._save_as_txt(
                    file_path,
                    target,
                    now
                )

                dialog.destroy()

                messagebox.showinfo(
                    "Sucesso",
                    f"Salvo em:\n\n{file_path}"
                )

            except Exception as e:

                messagebox.showerror(
                    "Erro",
                    f"Erro ao salvar:\n{str(e)}"
                )

        def save_html():

            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[
                    ("HTML file", "*.html")
                ],
                initialfile="Resultados.html"
            )

            if not file_path:
                return

            now = datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )

            target = (
                self.target_entry.get().strip()
                or "Desconhecido"
            )

            try:

                self._save_as_html(
                    file_path,
                    target,
                    now
                )

                dialog.destroy()

                messagebox.showinfo(
                    "Sucesso",
                    f"Salvo em:\n\n{file_path}"
                )

            except Exception as e:

                messagebox.showerror(
                    "Erro",
                    f"Erro ao salvar:\n{str(e)}"
                )

        btn_frame = tk.Frame(
            dialog,
            bg=self.bg_color
        )

        btn_frame.pack(
            pady=10
        )

        tk.Button(
            btn_frame,
            text="TXT",
            width=10,
            bg=self.green,
            fg="black",
            command=save_txt
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            btn_frame,
            text="HTML",
            width=10,
            bg=self.accent,
            fg="black",
            command=save_html
        ).pack(
            side="left",
            padx=10
        )

    # ==========================================================
    # SALVAR TXT
    # ==========================================================

    def _save_as_txt(
        self,
        file_path,
        target,
        now
    ):

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write("=" * 90 + "\n")
            f.write(
                " RELATÓRIO COMPLETO DE SCAN NMAP - TODAS AS ABAS\n"
            )
            f.write("=" * 90 + "\n\n")

            f.write(
                f"Data/Hora : {now}\n\n"
            )

            f.write(
                f"Alvo      : {target}\n\n"
            )

            f.write(
                f"IP        : {self.current_ip}\n\n"
            )

            f.write(
                f"Perfil    : {self.profile_combo.get()}\n\n"
            )

            f.write(
                f"Verbosity : {self.verbosity_combo.get()}\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("1. NMAP OUTPUT\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                self.last_output.strip()
                + "\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("2. HOSTS / PORTS\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                "HOST\tIP\tPORTA\tSTATE\tSERVICE\tVERSION\n"
            )

            f.write("-" * 100 + "\n")

            for (
                port,
                state,
                service,
                version
            ) in self.ports_list:

                f.write(
                    f"{target}\t"
                    f"{self.current_ip}\t"
                    f"{port}\t"
                    f"{state}\t"
                    f"{service}\t"
                    f"{version}\n"
                )

            f.write(
                f"\nTotal de portas abertas: "
                f"{len(self.ports_list)}\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("3. SERVIÇO / VERSÃO\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                self.topo_text.get(
                    "1.0",
                    tk.END
                ).strip()
                + "\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("4. SCANS\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                self.scans_text.get(
                    "1.0",
                    tk.END
                ).strip()
                + "\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("5. SISTEMA OPERACIONAL\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                self.os_text.get(
                    "1.0",
                    tk.END
                ).strip()
                + "\n\n"
            )

            f.write("=" * 60 + "\n")
            f.write("6. HOST DETAILS\n")
            f.write("=" * 60 + "\n\n")

            f.write(
                self.details_text.get(
                    "1.0",
                    tk.END
                ).strip()
                + "\n\n"
            )

            f.write("=" * 90 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("=" * 90 + "\n")

    # ==========================================================
    # ESCAPE HTML
    # ==========================================================

    def html_escape(self, text):

        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    # ==========================================================
    # SALVAR HTML
    # ==========================================================

    def _save_as_html(
        self,
        file_path,
        target,
        now
    ):

        def color_line(line):

            line = self.html_escape(line)

            if line.startswith("Not shown:"):

                return (
                    f'<span style="color:#d4d4d4;">'
                    f'{line}</span>'
                )

            if (
                line.strip().startswith("PORT")
                and "STATE" in line
                and "SERVICE" in line
            ):

                return (
                    f'<span style="color:#00bfff; '
                    f'font-weight:bold;">'
                    f'{line}</span>'
                )

            if (
                "open" in line
                and (
                    "/tcp" in line
                    or "/udp" in line
                )
            ):

                return (
                    f'<span style="color:#00ff9d;">'
                    f'{line}</span>'
                )

            if "filtered" in line:

                return (
                    f'<span style="color:#ff8c00;">'
                    f'{line}</span>'
                )

            if any(
                x in line
                for x in [
                    "Host is up",
                    "Service Info:",
                    "OS details",
                    "CPE:",
                    "MAC Address",
                    "Nmap scan report",
                    "Discovered open port"
                ]
            ):

                return (
                    f'<span style="color:#ff8c00;">'
                    f'{line}</span>'
                )

            return line

        colored_lines = [
            color_line(line)
            for line in
            self.last_output.strip().splitlines()
        ]

        nmap_formatted = "<br>".join(
            colored_lines
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<title>
Relatório Nmap - {self.html_escape(target)}
</title>

<style>

body {{
    font-family: Consolas, monospace;
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 30px;
    line-height: 1.8;
}}

h1,
h2 {{
    color: #00bfff;
}}

.nmap-output {{
    background: #0d0d0d;
    padding: 20px;
    border-radius: 8px;
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.9;
}}

table {{
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
}}

th {{
    background: #383838;
    color: #00bfff;
    font-weight: bold;
}}

td {{
    border: 1px solid #444;
    padding: 10px;
    text-align: left;
}}

.section {{
    margin: 50px 0;
}}

pre {{
    background: #0d0d0d;
    padding: 15px;
    white-space: pre-wrap;
    color: #d4d4d4;
}}

</style>

</head>

<body>

<h1>
Relatório Completo de Scan Nmap
</h1>

<p>
<strong>Data:</strong>
{self.html_escape(now)}
|
<strong>Alvo:</strong>
{self.html_escape(target)}
|
<strong>IP:</strong>
{self.html_escape(self.current_ip)}
</p>

<p>
<strong>Perfil:</strong>
{self.html_escape(self.profile_combo.get())}
|
<strong>Verbosity:</strong>
{self.html_escape(self.verbosity_combo.get())}
</p>

<div class="section">

<h2>
1. Nmap Output
</h2>

<div class="nmap-output">
{nmap_formatted}
</div>

</div>

<div class="section">

<h2>
2. Hosts / Ports
</h2>

<table>

<tr>
<th>Host</th>
<th>IP</th>
<th>Porta</th>
<th>Estado</th>
<th>Serviço</th>
<th>Versão</th>
</tr>
"""

        for (
            port,
            state,
            service,
            version
        ) in self.ports_list:

            html += f"""
<tr>

<td>{self.html_escape(target)}</td>

<td>{self.html_escape(self.current_ip)}</td>

<td>{self.html_escape(port)}</td>

<td>{self.html_escape(state)}</td>

<td>{self.html_escape(service)}</td>

<td>{self.html_escape(version)}</td>

</tr>
"""

        html += f"""

</table>

<p>
<strong>Total de portas abertas:</strong>
{len(self.ports_list)}
</p>

</div>

<div class="section">

<h2>
3. Serviço / Versão
</h2>

<pre>
{self.html_escape(
    self.topo_text.get("1.0", tk.END).strip()
)}
</pre>

</div>

<div class="section">

<h2>
4. Scans
</h2>

<pre>
{self.html_escape(
    self.scans_text.get("1.0", tk.END).strip()
)}
</pre>

</div>

<div class="section">

<h2>
5. Sistema Operacional
</h2>

<pre>
{self.html_escape(
    self.os_text.get("1.0", tk.END).strip()
)}
</pre>

</div>

<div class="section">

<h2>
6. Host Details
</h2>

<pre>
{self.html_escape(
    self.details_text.get("1.0", tk.END).strip()
)}
</pre>

</div>

</body>
</html>
"""

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

    # ==========================================================
    # OUTPUT COLORIDO
    # ==========================================================

    def colored_output(self, line):

        if (
            "open" in line
            and (
                "/tcp" in line
                or "/udp" in line
            )
        ):

            self.output_text.insert(
                tk.END,
                line,
                "open"
            )

        elif "filtered" in line:

            self.output_text.insert(
                tk.END,
                line,
                "filtered"
            )

        elif any(
            x in line
            for x in [
                "Service Info:",
                "OSs:",
                "CPE:",
                "MAC Address",
                "Host is up",
                "OS details"
            ]
        ):

            self.output_text.insert(
                tk.END,
                line,
                "info"
            )

        else:

            self.output_text.insert(
                tk.END,
                line
            )

    # ==========================================================
    # PARSER
    # ==========================================================

    def parse_and_fill_tabs(
        self,
        output,
        target
    ):

        self.last_output = output

        self.current_ip = target

        self.os_info = ""

        # Procurar IP
        ip_match = re.search(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            output
        )

        if ip_match:

            self.current_ip = ip_match.group(0)

        self.ports_list = []

        # Limpar Treeview

        for item in self.hosts_tree.get_children():

            self.hosts_tree.delete(item)

        # Limpar abas

        self.details_text.delete(
            "1.0",
            tk.END
        )

        self.topo_text.delete(
            "1.0",
            tk.END
        )

        self.scans_text.delete(
            "1.0",
            tk.END
        )

        self.os_text.delete(
            "1.0",
            tk.END
        )

        # ==================== PORTAS ====================

        port_pattern = re.compile(
            r"^\s*(\d+)\/(\w+)\s+"
            r"(open|closed|filtered|open\|filtered)"
            r"\s+(\S+)"
            r"(?:\s+(.*))?$"
        )

        for line in output.splitlines():

            port_match = port_pattern.match(line)

            if port_match:

                port_number = port_match.group(1)

                protocol = port_match.group(2)

                state = port_match.group(3)

                service = port_match.group(4)

                version = (
                    port_match.group(5)
                    or ""
                ).strip()

                port = (
                    f"{port_number}/{protocol}"
                )

                # Guardar portas abertas
                if state == "open":

                    self.ports_list.append(
                        (
                            port,
                            state,
                            service,
                            version
                        )
                    )

                self.hosts_tree.insert(
                    "",
                    "end",
                    values=(
                        target,
                        self.current_ip,
                        port_number,
                        state,
                        service,
                        version
                    )
                )

            # ==================== SO ====================

            if any(
                k in line
                for k in [
                    "OS details",
                    "OS:",
                    "CPE:",
                    "Aggressive OS guesses",
                    "Running:",
                    "Service Info:",
                    "MAC Address"
                ]
            ):

                self.os_info += (
                    line + "\n\n"
                )

            # ==================== DETAILS ====================

            if any(
                k in line
                for k in [
                    "Host is up",
                    "Service Info",
                    "OSs:",
                    "MAC Address",
                    "Nmap scan report"
                ]
            ):

                self.details_text.insert(
                    tk.END,
                    line + "\n\n"
                )

        # ==================== SO ====================

        if self.os_info.strip():

            self.os_text.insert(
                tk.END,
                "=== DETECÇÃO DE SISTEMA OPERACIONAL ===\n\n"
                + self.os_info
            )

        else:

            self.os_text.insert(
                tk.END,
                "Nenhuma informação de SO detectada.\n\n"
                "Use perfis com -O ou -A.\n"
            )

        # ==================== SERVIÇO ====================

        self.topo_text.insert(
            tk.END,
            "PORT\t\tSTATE\tSERVICE\t\tVERSION\n"
        )

        self.topo_text.insert(
            tk.END,
            "-" * 80 + "\n"
        )

        for (
            port,
            state,
            service,
            version
        ) in self.ports_list:

            self.topo_text.insert(
                tk.END,
                f"{port:<12}\t"
                f"{state:<8}\t"
                f"{service:<12}\t"
                f"{version}\n"
            )

        # ==================== SCANS ====================

        self.scans_text.insert(
            tk.END,
            f"Scan finalizado: "
            f"{datetime.now().strftime('%H:%M:%S')}\n\n"
        )

        self.scans_text.insert(
            tk.END,
            f"Total de portas abertas: "
            f"{len(self.ports_list)}\n"
        )

    # ==========================================================
    # EXECUTAR NMAP
    # ==========================================================

    def run_nmap(self, target):

        base_cmd = self.profiles.get(
            self.profile_combo.get(),
            "nmap"
        )

        process = None

        try:

            # Separar comando
            cmd_parts = base_cmd.split()

            # Remover verbosity antiga
            for v in [
                "-v",
                "-vv",
                "-vvv"
            ]:

                while v in cmd_parts:
                    cmd_parts.remove(v)

            # Adicionar verbosity selecionada

            verbosity = self.verbosity_combo.get()

            if verbosity != "Normal (sem -v)":

                cmd_parts.append(
                    verbosity
                )

            # Adicionar target

            command = (
                cmd_parts
                + [target]
            )

            # ==================== WINDOWS ====================

            if platform.system() == "Windows":

                startupinfo = (
                    subprocess.STARTUPINFO()
                )

                startupinfo.dwFlags |= (
                    subprocess.STARTF_USESHOWWINDOW
                )

                startupinfo.wShowWindow = (
                    subprocess.SW_HIDE
                )

                creationflags = (
                    subprocess.CREATE_NO_WINDOW
                )

            else:

                startupinfo = None
                creationflags = 0

            # ==================== INICIAR ====================

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                startupinfo=startupinfo,
                creationflags=creationflags,
                bufsize=1
            )

            self.nmap_process = process

            output = ""

            # ==================== LER OUTPUT ====================

            while True:

                if self.stop_flag:

                    break

                line = process.stdout.readline()

                if not line:

                    if process.poll() is not None:
                        break

                    continue

                # Ignorar algumas linhas

                if any(
                    phrase in line
                    for phrase in [
                        "Read data files from",
                        "Nmap done:",
                        "scanned in"
                    ]
                ):

                    continue

                output += line

                # Atualização segura da GUI
                self.root.after(
                    0,
                    self._append_output,
                    line
                )

            # ==================== CANCELAMENTO ====================

            if self.stop_flag:

                try:

                    if process.poll() is None:

                        process.terminate()

                        try:

                            process.wait(
                                timeout=1
                            )

                        except subprocess.TimeoutExpired:

                            process.kill()

                            process.wait(
                                timeout=1
                            )

                except Exception:
                    pass

                self.nmap_process = None

                self.root.after(
                    0,
                    self._scan_cancelled_message
                )

                return False

            # ==================== ESPERAR ====================

            process.wait()

            self.nmap_process = None

            # ==================== RESULTADO ====================

            self.root.after(
                0,
                self.parse_and_fill_tabs,
                output,
                target
            )

            self.root.after(
                0,
                self._scan_completed_message,
                target
            )

            return True

        except FileNotFoundError:

            self.nmap_process = None

            if not self.stop_flag:

                self.root.after(
                    0,
                    self._show_error,
                    "Nmap não encontrado.\n\n"
                    "Verifique se o Nmap está instalado "
                    "e disponível no PATH."
                )

            return False

        except Exception as e:

            self.nmap_process = None

            if not self.stop_flag:

                self.root.after(
                    0,
                    self._show_error,
                    str(e)
                )

            return False

        finally:

            if process is not None:

                try:

                    if process.stdout:
                        process.stdout.close()

                except Exception:
                    pass

    # ==========================================================
    # ADICIONAR OUTPUT NA GUI
    # ==========================================================

    def _append_output(self, line):

        if self.stop_flag:
            return
        
        self.colored_output(line + "\n")

        self.output_text.see(tk.END)

    # ==========================================================
    # MENSAGEM CANCELADO
    # ==========================================================

    def _scan_cancelled_message(self):

        self.output_text.tag_configure("abobora", foreground=self.abobora)

        self.output_text.insert(tk.END, "\n[!] ⏹ SCAN CANCELADO\n", "abobora")

        self.output_text.see(tk.END)

        self.status.config(text="⏹ Scan cancelado")

        self.scan_running = False

        self.nmap_process = None

        self.btn_scan.config(state=tk.NORMAL)

        self.btn_cancel.config(state=tk.NORMAL)

    # ==========================================================
    # MENSAGEM CONCLUÍDO
    # ==========================================================

    def _scan_completed_message(self, target):

        if self.stop_flag:
            return

        self.output_text.tag_configure("abobora", foreground=self.abobora)

        self.output_text.insert(tk.END, "\n[✓] SCAN CONCLUÍDO Nmap\n", "abobora")

        self.output_text.see(tk.END)

        self.status.config(text=f"Scan concluído: {target}")

    # ==========================================================
    # ERRO
    # ==========================================================

    def _show_error(self, error):

        self.output_text.insert(tk.END, f"\n[ERRO] {error}\n")

        self.output_text.see(tk.END)

        self.status.config(text="Erro")

    # ==========================================================
    # THREAD DOS SCANS
    # ==========================================================

    def run_scan_thread(self):

        try:

            target = (
                self.target_entry.get().strip()
            )

            # ==================== IP.TXT ====================

            if self.ip_list:

                total = len(
                    self.ip_list
                )

                for i, ip in enumerate(
                    self.ip_list
                ):

                    if self.stop_flag:
                        break

                    self.current_target_index = i

                    # Atualizar target
                    self.root.after(
                        0,
                        self._set_target,
                        ip
                    )

                    # Separador

                    self.root.after(
                        0,
                        self._append_progress,
                        i + 1,
                        total,
                        ip
                    )

                    self.root.after(
                        0,
                        self._set_status,
                        f"Scanning {i + 1}/{total}: {ip}"
                    )

                    # Scan

                    result = self.run_nmap(
                        ip
                    )

                    if self.stop_flag:
                        break

                    if not result:
                        continue

                    # Próximo IP

                    if (
                        i < total - 1
                        and not self.stop_flag
                    ):

                        self.root.after(0, self._append_separator, ip)

                # ==================== FINAL ====================

                if not self.stop_flag:

                    self.root.after(0, self._all_scans_completed, total)

            # ==================== TARGET MANUAL ====================

            else:

                if not target:

                    self.root.after(0, self._show_error, "Digite um alvo ou carregue um ip.txt!")

                    return

                self.run_nmap(target)

        finally:

            self.scan_running = False

            self.nmap_process = None

            self.root.after(0, self._scan_thread_finished)

    # ==========================================================
    # ATUALIZAR TARGET
    # ==========================================================

    def _set_target(self, ip):

        self.target_entry.delete(0, tk.END)

        self.target_entry.insert(0, ip)

        self.update_command()

    # ==========================================================
    # PROGRESSO
    # ==========================================================

    def _append_progress(self, number, total, ip):

        self.output_text.insert(tk.END, "\n" + "=" * 60 + "\n")

        self.output_text.insert(tk.END, f" Scan {number}/{total} - Alvo: {ip}\n")

        self.output_text.insert(tk.END, "=" * 60 + "\n\n")

        self.output_text.see(tk.END)

    # ==========================================================
    # SEPARADOR
    # ==========================================================

    def _append_separator(self, ip):

        self.output_text.insert(tk.END, "\n" + "=" * 60 + "\n")

        self.output_text.insert(tk.END, f" Scan do IP {ip} finalizado. Próximo...\n")

        self.output_text.insert(tk.END, "=" * 60 + "\n\n")

        self.output_text.see(tk.END)

    # ==========================================================
    # TODOS CONCLUÍDOS
    # ==========================================================

    def _all_scans_completed(self, total):

        self.output_text.insert(tk.END, "\n" + "=" * 60 + "\n")

        self.output_text.insert(tk.END, f" TODOS OS {total} IP FORAM ESCANEADOS!\n")

        self.output_text.insert(tk.END, "=" * 60 + "\n")

        self.output_text.see(tk.END)

        self.status.config(text=f"Scan completo - {total} IP")

    # ==========================================================
    # THREAD TERMINOU
    # ==========================================================

    def _scan_thread_finished(self):

        self.scan_running = False

        self.nmap_process = None

        self.btn_scan.config(state=tk.NORMAL)

        self.btn_cancel.config(state=tk.NORMAL)

    # ==========================================================
    # STATUS
    # ==========================================================

    def _set_status(self, text):

        self.status.config(text=text)

    # ==========================================================
    # INICIAR SCAN
    # ==========================================================

    def start_scan(self):

        if self.scan_running:

            messagebox.showwarning("Scan em execução", "Já existe um scan em execução.")

            return

        target = (self.target_entry.get().strip())

        if not target and not self.ip_list:

            messagebox.showerror("Erro", "Digite um alvo ou carregue um arquivo ip.txt!")

            return

        self.update_command()

        # Limpar output

        self.output_text.delete("1.0", tk.END)

        # Limpar abas

        for item in self.hosts_tree.get_children():
            self.hosts_tree.delete(item)

        self.details_text.delete("1.0", tk.END)

        self.topo_text.delete("1.0", tk.END)

        self.scans_text.delete("1.0", tk.END)

        self.os_text.delete("1.0", tk.END)

        self.last_output = ""

        self.ports_list = []

        # Mensagem inicial

        self.output_text.insert(
            tk.END,
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            "Iniciando scan...\n\n"
        )

        self.status.config(text="Scanning...")

        self.stop_flag = False

        self.scan_running = True

        self.btn_scan.config(state=tk.DISABLED)

        # Thread

        self.scan_thread = threading.Thread(target=self.run_scan_thread, daemon=True)

        self.scan_thread.start()

    # ==========================================================
    # CANCELAR SCAN
    # ==========================================================

    def cancel_scan(self):

        if (
            not self.scan_running
            and not self.nmap_process
        ):

            self.status.config(text="Nenhum scan em execução")

            return

        # ==================== FLAG ====================

        self.stop_flag = True

        self.scan_running = False

        # ==================== MENSAGEM ====================

        self.output_text.tag_configure("abobora", foreground=self.abobora)

        self.output_text.insert(tk.END, "\n[!] ⏹ CANCELAR SCAN\n", "abobora")

        self.output_text.insert(tk.END,"\n[x] ⏹ SCAN CONCLUÍDO Nmap\n", "abobora")

        self.output_text.see(tk.END)

        self.status.config(text="⏹ Cancelando...")

        # ==================== PROCESSO ====================

        process = self.nmap_process

        if process:

            try:

                if process.poll() is None:

                    process.terminate()

                    try:

                        process.wait(timeout=1)

                    except subprocess.TimeoutExpired:

                        process.kill()

                        process.wait(timeout=1)

            except Exception as e:
                pass
            finally:
                self.nmap_process = None        

    # ==========================================================
    # MAINLOOP
    # ==========================================================

    def run(self):

        self.root.mainloop()

# ==============================================================
# INICIAR PROGRAMA
# ==============================================================

if __name__ == "__main__":

    app = ZenmapClone()

    app.run()

