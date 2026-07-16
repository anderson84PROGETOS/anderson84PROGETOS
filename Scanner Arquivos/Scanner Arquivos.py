import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from threading import Thread
from datetime import datetime
import socket
import json
import hashlib
import webbrowser

class ScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Scanner Arquivos 🛡️")
        self.root.geometry("900x700")
        self.root.state("zoomed")
        self.root.configure(bg="#0d1117")
        
        # Paleta de cores completa
        self.COLORS = {
            "bg_dark": "#0d1117",
            "bg_medium": "#161b22",
            "bg_light": "#21262d",
            "bg_input": "#0d1117",
            "bg_button": "#21262d",
            "bg_button_hover": "#30363d",
            "bg_scroll": "#0d1117",
            "bg_progress": "#21262d",
            "bg_notebook": "#161b22",
            "bg_tab_active": "#0d1117",
            "bg_tab_inactive": "#21262d",
            "bg_check": "#0d1117",
            
            "fg_primary": "#58a6ff",
            "fg_secondary": "#8b949e",
            "fg_accent": "#3fb950",
            "fg_danger": "#f85149",
            "fg_warning": "#d29922",
            "fg_info": "#79c0ff",
            "fg_success": "#56d364",
            "fg_muted": "#484f58",
            "fg_white": "#c9d1d9",
            "fg_orange": "#f0883e",
            "fg_purple": "#bc8cff",
            "fg_cyan": "#39d2c0",
            "fg_pink": "#f778ba",
            "fg_yellow": "#e3b341",
            
            "border": "#30363d",
            "highlight": "#1f6feb",
            "selection": "#264f78",
            
            "tab_result_bg": "#0d1117",
            "tab_result_fg": "#f85149",
            "tab_ip_bg": "#0d1117",
            "tab_ip_fg": "#f0883e",
            "tab_domain_bg": "#0d1117",
            "tab_domain_fg": "#d29922",
            "tab_raw_bg": "#0d1117",
            "tab_raw_fg": "#8b949e",
            "tab_hash_bg": "#0d1117",
            "tab_hash_fg": "#bc8cff",
            
            "scan_btn_idle_bg": "#1f6feb",
            "scan_btn_idle_fg": "#ffffff",
            "scan_btn_active_bg": "#da3633",
            "scan_btn_active_fg": "#ffffff",
            
            "title_fg": "#58a6ff",
            "status_idle_fg": "#484f58",
            "status_scan_fg": "#3fb950",
            "status_done_fg": "#56d364",
            
            "stats_fg": "#8b949e",
            "ext_label_fg": "#8b949e",
            
            "suspicious_fg": "#f85149",
            "clean_fg": "#56d364",
            "dns_ok_fg": "#39d2c0",
            "dns_fail_fg": "#f85149",
            "domain_list_fg": "#d29922",
            "ip_list_fg": "#f0883e",
        }
        
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure(
            "Horizontal.TProgressbar",
            background=self.COLORS["fg_accent"],
            troughcolor=self.COLORS["bg_medium"],
            bordercolor=self.COLORS["bg_medium"],
            lightcolor=self.COLORS["fg_accent"],
            darkcolor=self.COLORS["fg_accent"]
        )
        
        style.configure("Dark.TFrame", background=self.COLORS["bg_dark"])
        style.configure("Dark.TLabel", background=self.COLORS["bg_dark"], foreground=self.COLORS["fg_primary"])
        
        style.configure("TNotebook", background=self.COLORS["bg_medium"], tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", background=self.COLORS["bg_tab_inactive"], foreground=self.COLORS["fg_white"], padding=[12, 4], borderwidth=1)
        style.map("TNotebook.Tab", background=[("selected", self.COLORS["bg_tab_active"])], foreground=[("selected", self.COLORS["fg_primary"])], borderwidth=[("selected", 2)])
        
        main_frame = ttk.Frame(root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        title = tk.Label(main_frame, text="🔍 Scanner de IOCs em Arquivos", bg=self.COLORS["bg_dark"], fg=self.COLORS["title_fg"], font=("Consolas", 14, "bold"))
        title.pack(pady=(0, 12))
        
        separator = tk.Frame(main_frame, height=1, bg=self.COLORS["border"])
        separator.pack(fill=tk.X, pady=(0, 10))
        
        select_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        select_frame.pack(fill=tk.X, pady=5)
        
        self.path_var = tk.StringVar()
        path_entry = tk.Entry(select_frame, textvariable=self.path_var, bg=self.COLORS["bg_input"], fg=self.COLORS["fg_primary"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 10), width=70, relief=tk.FLAT, highlightthickness=1, highlightbackground=self.COLORS["border"], highlightcolor=self.COLORS["highlight"], bd=0)
        path_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        btn_file = tk.Button(select_frame, text="📄 Arquivo", bg=self.COLORS["bg_button"], fg=self.COLORS["fg_accent"], activebackground=self.COLORS["bg_button_hover"], activeforeground=self.COLORS["fg_accent"], font=("Consolas", 9), command=lambda: self.select_path("file"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2", bd=0, highlightthickness=0)
        btn_file.pack(side=tk.LEFT, padx=2)
        
        btn_folder = tk.Button(select_frame, text="📁 Pasta", bg=self.COLORS["bg_button"], fg=self.COLORS["fg_info"], activebackground=self.COLORS["bg_button_hover"], activeforeground=self.COLORS["fg_info"], font=("Consolas", 9), command=lambda: self.select_path("folder"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2", bd=0, highlightthickness=0)
        btn_folder.pack(side=tk.LEFT, padx=2)
        
        opt_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        opt_frame.pack(fill=tk.X, pady=6)
        
        self.recursive_var = tk.BooleanVar(value=True)
        rec_check = tk.Checkbutton(opt_frame, text="🔁 Busca Recursiva", variable=self.recursive_var, bg=self.COLORS["bg_check"], fg=self.COLORS["fg_success"], selectcolor=self.COLORS["bg_medium"], activebackground=self.COLORS["bg_dark"], activeforeground=self.COLORS["fg_success"], font=("Consolas", 9), relief=tk.FLAT, bd=0, highlightthickness=0)
        rec_check.pack(side=tk.LEFT, padx=5)
        
        self.resolve_var = tk.BooleanVar(value=True)
        res_check = tk.Checkbutton(opt_frame, text="🌐 Resolver Domínios", variable=self.resolve_var, bg=self.COLORS["bg_check"], fg=self.COLORS["fg_info"], selectcolor=self.COLORS["bg_medium"], activebackground=self.COLORS["bg_dark"], activeforeground=self.COLORS["fg_info"], font=("Consolas", 9), relief=tk.FLAT, bd=0, highlightthickness=0)
        res_check.pack(side=tk.LEFT, padx=5)
        
        self.hash_var = tk.BooleanVar(value=True)
        hash_check = tk.Checkbutton(opt_frame, text="🔐 Calcular SHA-256", variable=self.hash_var, bg=self.COLORS["bg_check"], fg=self.COLORS["fg_purple"], selectcolor=self.COLORS["bg_medium"], activebackground=self.COLORS["bg_dark"], activeforeground=self.COLORS["fg_purple"], font=("Consolas", 9), relief=tk.FLAT, bd=0, highlightthickness=0)
        hash_check.pack(side=tk.LEFT, padx=5)
        
        self.threat_check_var = tk.BooleanVar(value=True)
        threat_check = tk.Checkbutton(opt_frame, text="☢️ Verificar ameaças (VT)", variable=self.threat_check_var, bg=self.COLORS["bg_check"], fg=self.COLORS["fg_warning"], selectcolor=self.COLORS["bg_medium"], activebackground=self.COLORS["bg_dark"], activeforeground=self.COLORS["fg_warning"], font=("Consolas", 9), relief=tk.FLAT, bd=0, highlightthickness=0)
        threat_check.pack(side=tk.LEFT, padx=5)
        
        ext_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        ext_frame.pack(fill=tk.X, pady=6)
        
        ext_label = tk.Label(ext_frame, text="📎 Extensões:", bg=self.COLORS["bg_dark"], fg=self.COLORS["ext_label_fg"], font=("Consolas", 9))
        ext_label.pack(side=tk.LEFT, padx=(5, 8))
        
        self.ext_var = tk.StringVar(value=".txt,.log,.csv,.html,.php,.js,.py,.conf,.json,.xml,.ini,.cfg,.bat,.ps1,.sh,.exe,.dll,.bin")
        ext_entry = tk.Entry(ext_frame, textvariable=self.ext_var, bg=self.COLORS["bg_input"], fg=self.COLORS["fg_secondary"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 9), width=60, relief=tk.FLAT, highlightthickness=1, highlightbackground=self.COLORS["border"], highlightcolor=self.COLORS["highlight"], bd=0)
        ext_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        separator2 = tk.Frame(main_frame, height=1, bg=self.COLORS["border"])
        separator2.pack(fill=tk.X, pady=6)
        
        self.scan_btn = tk.Button(main_frame, text="▶ INICIAR SCAN", bg=self.COLORS["scan_btn_idle_bg"], fg=self.COLORS["scan_btn_idle_fg"], activebackground=self.COLORS["highlight"], activeforeground=self.COLORS["fg_white"], font=("Consolas", 12, "bold"), command=self.start_scan, relief=tk.FLAT, padx=24, pady=10, cursor="hand2", bd=0, highlightthickness=0)
        self.scan_btn.pack(pady=10)
        
        progress_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        progress_frame.pack(fill=tk.X, pady=3)
        
        # === BARRA DE PROGRESSO DETERMINATE (0-100%) ===
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", length=860, style="Horizontal.TProgressbar", maximum=100, value=0)
        
        # Label de percentual ao lado da barra
        self.progress_label = tk.Label(progress_frame, text="0%", bg=self.COLORS["bg_dark"], fg=self.COLORS["fg_accent"], font=("Consolas", 8, "bold"))
        self.progress_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.status_label = tk.Label(progress_frame, text="Pronto para escanear", bg=self.COLORS["bg_dark"], fg=self.COLORS["status_idle_fg"], font=("Consolas", 9), anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        result_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(result_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # --- Aba Resultados ---
        self.result_text = scrolledtext.ScrolledText(notebook, bg=self.COLORS["tab_result_bg"], fg=self.COLORS["tab_result_fg"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bd=0, padx=8, pady=8, highlightthickness=0)
        self.result_text.configure(selectbackground=self.COLORS["selection"], selectforeground=self.COLORS["fg_white"], inactiveselectbackground=self.COLORS["selection"])
        notebook.add(self.result_text, text="🔴 Resultados")
        
        # --- Aba IPs ---
        self.ips_text = scrolledtext.ScrolledText(notebook, bg=self.COLORS["tab_ip_bg"], fg=self.COLORS["tab_ip_fg"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bd=0, padx=8, pady=8, highlightthickness=0)
        self.ips_text.configure(selectbackground=self.COLORS["selection"], selectforeground=self.COLORS["fg_white"], inactiveselectbackground=self.COLORS["selection"])
        self.ips_text.bind("<Double-Button-1>", lambda e: self._open_vt_selected(self.ips_text))
        notebook.add(self.ips_text, text="🌐 IP Encontrados")
        
        # --- Aba Domínios ---
        self.domains_text = scrolledtext.ScrolledText(notebook, bg=self.COLORS["tab_domain_bg"], fg=self.COLORS["tab_domain_fg"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bd=0, padx=8, pady=8, highlightthickness=0)
        self.domains_text.configure(selectbackground=self.COLORS["selection"], selectforeground=self.COLORS["fg_white"], inactiveselectbackground=self.COLORS["selection"])
        self.domains_text.bind("<Double-Button-1>", lambda e: self._open_vt_selected(self.domains_text))
        notebook.add(self.domains_text, text="🏠 Domínios Encontrados")
        
        # --- Aba Hashes ---
        self.hash_text = scrolledtext.ScrolledText(notebook, bg=self.COLORS["tab_hash_bg"], fg=self.COLORS["tab_hash_fg"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bd=0, padx=8, pady=8, highlightthickness=0)
        self.hash_text.configure(selectbackground=self.COLORS["selection"], selectforeground=self.COLORS["fg_white"], inactiveselectbackground=self.COLORS["selection"])
        self.hash_text.bind("<Double-Button-1>", lambda e: self._open_vt_selected(self.hash_text))
        notebook.add(self.hash_text, text="🔐 SHA-256 Hashes")
        
        # --- Aba Raw ---
        self.raw_text = scrolledtext.ScrolledText(notebook, bg=self.COLORS["tab_raw_bg"], fg=self.COLORS["tab_raw_fg"], insertbackground=self.COLORS["fg_primary"], font=("Consolas", 8), wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bd=0, padx=8, pady=8, highlightthickness=0)
        self.raw_text.configure(selectbackground=self.COLORS["selection"], selectforeground=self.COLORS["fg_white"], inactiveselectbackground=self.COLORS["selection"])
        notebook.add(self.raw_text, text="📄 Raw Matches")
        
        separator3 = tk.Frame(main_frame, height=1, bg=self.COLORS["border"])
        separator3.pack(fill=tk.X, pady=5)
        
        action_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        action_frame.pack(fill=tk.X, pady=5)
        
        btn_clear = tk.Button(action_frame, text="🧹 Limpar", bg=self.COLORS["bg_button"], fg=self.COLORS["fg_danger"], activebackground=self.COLORS["bg_button_hover"], activeforeground=self.COLORS["fg_danger"], font=("Consolas", 9), command=self.clear_results, relief=tk.FLAT, padx=12, pady=3, cursor="hand2", bd=0, highlightthickness=0)
        btn_clear.pack(side=tk.LEFT, padx=2)
        
        btn_export = tk.Button(action_frame, text="💾 Exportar", bg=self.COLORS["bg_button"], fg=self.COLORS["fg_accent"], activebackground=self.COLORS["bg_button_hover"], activeforeground=self.COLORS["fg_accent"], font=("Consolas", 9), command=self.export_results, relief=tk.FLAT, padx=12, pady=3, cursor="hand2", bd=0, highlightthickness=0)
        btn_export.pack(side=tk.LEFT, padx=2)
        
        self.stats_label = tk.Label(action_frame, text="IP: 0  |  Domínios: 0  |  Hashes: 0  |  Arquivos: 0", bg=self.COLORS["bg_dark"], fg=self.COLORS["stats_fg"], font=("Consolas", 9))
        self.stats_label.pack(side=tk.RIGHT, padx=5)
        
        self.scanning = False
        self.results = {"ips": set(), "domains": set(), "hashes": {}, "raw": [], "files_scanned": 0}
        
        # === VARIÁVEIS DE PROGRESSO ===
        self.progress_value = 0
        self.total_files = 0
        self.processed_files = 0

        # Configuração inicial das tags de cor
        self.result_text.tag_configure("default", foreground=self.COLORS["fg_secondary"])
        
        # === CONFIGURAÇÃO DO MENU DE CONTEXTO (CLIQUE DIREITO) ===
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Cria o menu de contexto com lupa para abrir no VirusTotal"""
        
        # Cria o menu popup com estilo escuro
        self.context_menu = tk.Menu(self.root, tearoff=0, 
                                   bg=self.COLORS["bg_light"], 
                                   fg=self.COLORS["fg_white"],
                                   activebackground=self.COLORS["highlight"], 
                                   activeforeground=self.COLORS["fg_white"],
                                   font=("Consolas", 9),
                                   bd=1,
                                   relief=tk.FLAT)
        
        # Item da lupa 🔍 VirusTotal
        self.context_menu.add_command(label="🔍  Abrir no VirusTotal", 
                                     command=self._open_vt_context,
                                     font=("Consolas", 9, "bold"))
        
        self.context_menu.add_separator()
        
        # Item copiar
        self.context_menu.add_command(label="📋  Copiar", 
                                     command=self._copy_context,
                                     font=("Consolas", 9))
        
        # Aplica o bind de clique direito em TODAS as abas
        for widget in [self.result_text, self.ips_text, self.domains_text, self.hash_text, self.raw_text]:
            widget.bind("<Button-3>", self._show_context_menu)  # Botão direito do mouse
    
    def _show_context_menu(self, event):
        """Exibe o menu de contexto no local do clique"""
        widget = event.widget
        
        try:
            # Tenta selecionar a linha onde o usuário clicou
            index = widget.index(f"@{event.x},{event.y}")
            widget.mark_set(tk.INSERT, index)
            
            # Seleciona a linha inteira
            widget.tag_remove(tk.SEL, "1.0", tk.END)
            widget.tag_add(tk.SEL, f"{index} linestart", f"{index} lineend")
            widget.see(index)
        except:
            pass
        
        # Exibe o menu na posição do mouse
        self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def _get_selected_value(self, text_widget=None):
        """Extrai o valor selecionado (IP, domínio ou hash)"""
        if text_widget is None:
            text_widget = self.root.focus_get()
        
        if text_widget not in [self.result_text, self.ips_text, self.domains_text, self.hash_text, self.raw_text]:
            return None
        
        try:
            # Tenta pegar a seleção ativa
            selected = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except tk.TclError:
            # Se não houver seleção, pega a linha atual
            try:
                index = text_widget.index(tk.INSERT)
                selected = text_widget.get(f"{index} linestart", f"{index} lineend").strip()
            except:
                return None
        
        if not selected:
            return None
        
        # Limpa numeração de linha: "   1. 8.8.8.8" -> "8.8.8.8"
        selected = re.sub(r'^\s*\d+\s*\.\s*', '', selected)
        
        # Limpa emojis/marcadores do início: "🔴 exemplo.com" -> "exemplo.com"
        selected = re.sub(r'^[\s🔴✅❌🚨⚠️⚡📋🔗🔍🌟💡]*\s*', '', selected)
        
        # Remove setas e informações extras: "exemplo.com -> 1.2.3.4" -> "exemplo.com"
        selected = re.sub(r'\s*->.*$', '', selected)
        
        # Remove colchetes do raw: "[IP    ] 8.8.8.8 -> arquivo.txt"
        selected = re.sub(r'^\[.*?\]\s*', '', selected)
        
        # Pega apenas o primeiro token (IP, domínio ou hash)
        selected = selected.strip().split()[0] if selected.split() else selected
        
        return selected
    
    def _open_vt_context(self):
        """Abre o VirusTotal a partir do menu de contexto"""
        text_widget = self.root.focus_get()
        if text_widget not in [self.result_text, self.ips_text, self.domains_text, self.hash_text, self.raw_text]:
            return
        
        selected = self._get_selected_value(text_widget)
        if not selected:
            return
        
        # Verifica se é IP
        ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        # Verifica se é hash SHA-256 (64 caracteres hex)
        hash_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
        # Verifica se é domínio
        domain_pattern = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
        
        if ip_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/ip-address/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para IP: {selected}")
        elif hash_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/file/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para hash: {selected}")
        elif domain_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/domain/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para domínio: {selected}")
        else:
            self.log(f"\n❌ Valor não reconhecido: {selected}\n")
            return
        
        webbrowser.open(url)
    
    def _copy_context(self):
        """Copia o valor selecionado para a área de transferência"""
        text_widget = self.root.focus_get()
        if text_widget not in [self.result_text, self.ips_text, self.domains_text, self.hash_text, self.raw_text]:
            return
        
        selected = self._get_selected_value(text_widget)
        if not selected:
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(selected)
        self.log(f"📋 Copiado: {selected}")
    
    def select_path(self, type_):
        if type_ == "file":
            path = filedialog.askopenfilename(title="Selecione um arquivo para escanear", filetypes=[("Todos os arquivos", "*.*"), ("Arquivos de texto", "*.txt *.log *.csv"), ("Código", "*.py *.js *.php *.html")])
        else:
            path = filedialog.askdirectory(title="Selecione uma pasta para escanear")
        if path:
            self.path_var.set(path)
    
    def _open_vt_selected(self, text_widget):
        """Abre o VirusTotal com o item selecionado (IP, domínio ou hash) - Duplo clique"""
        selected = self._get_selected_value(text_widget)
        if not selected:
            return
        
        # Verifica se é IP
        ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        # Verifica se é hash SHA-256 (64 caracteres hex)
        hash_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
        # Verifica se é domínio
        domain_pattern = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
        
        if ip_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/ip-address/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para IP: {selected}")
        elif hash_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/file/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para hash: {selected}")
        elif domain_pattern.match(selected):
            url = f"https://www.virustotal.com/gui/domain/{selected}"
            self.log(f"🔍 Abrindo VirusTotal para domínio: {selected}")
        else:
            self.log(f"\n❌ Valor não reconhecido: {selected}\n")
            return
        
        webbrowser.open(url)
    
    def _detect_color(self, text: str) -> str:
        """Detecta a cor específica para cada tipo de linha conforme solicitado"""
        text_lower = text.lower()
        
        # Cabeçalhos e separadores
        if text.startswith("=") or "SCAN CONCLUÍDO" in text:
            return self.COLORS["fg_primary"]           # 🔵 #58a6ff
        
        # Alvo do scan
        if "Alvo:" in text:
            return self.COLORS["fg_info"]              # 🔵 info #79c0ff
        
        # Arquivos escaneados
        if "Arquivos escaneados:" in text:
            return self.COLORS["fg_secondary"]         # ⚪ #8b949e
        
        # Hash
        if "SHA-256" in text:
            return self.COLORS["fg_purple"]            # 🟣 #bc8cff
        
        # Seção de IP
        if "IP SUSPEITOS" in text or text.startswith("   ⚡"):
            return self.COLORS["fg_orange"]            # 🟠 #f0883e
        
        # Seção de Domínios
        if "DOMÍNIOS SUSPEITOS" in text or "Domínios encontrados" in text:
            return self.COLORS["fg_warning"]           # 🟡 #d29922
        
        # Domínios limpos
        if "Domínios limpos" in text:
            return self.COLORS["fg_success"]           # 🟢 #56d364
        
        # Domínios suspeitos individuais
        if "🔴" in text:
            return self.COLORS["fg_danger"]            # 🔴 #f85149
        
        # DNS resolvido
        if "✅" in text:
            return self.COLORS["dns_ok_fg"]            # 🌊 Ciano #39d2c0
        
        # DNS falhou
        if "❌" in text:
            return self.COLORS["dns_fail_fg"]          # 🔴 #f85149
        
        # Resumo de domínios resolvidos
        if "📊 Domínios resolvidos" in text:
            return self.COLORS["fg_primary"]           # 🔵 #58a6ff
        
        # Resolvendo domínios
        if text.startswith("🔍 Resolvendo"):
            return self.COLORS["fg_info"]
        
        # Abrindo VT
        if text.startswith("🔍 Abrindo"):
            return self.COLORS["fg_cyan"]              # 🌊 #39d2c0
        
        # Copiado
        if text.startswith("📋 Copiado"):
            return self.COLORS["fg_success"]           # 🟢 #56d364
        
        # Erros
        if text.startswith("❌ Erro") or text.startswith("❌ Valor"):
            return self.COLORS["fg_danger"]
        
        # Fallback
        return self.COLORS["fg_secondary"]
    
    def log(self, text):
        """Log com cor detectada automaticamente"""
        color = self._detect_color(text)
        
        self.result_text.config(state=tk.NORMAL)
        
        tag_name = f"color_{color.replace('#', '')}"
        
        if tag_name not in self.result_text.tag_names():
            self.result_text.tag_configure(tag_name, foreground=color)
        
        self.result_text.insert(tk.END, text + "\n", tag_name)
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def update_stats(self):
        self.stats_label.config(text=f"IP: {len(self.results['ips'])}  |  Domínios: {len(self.results['domains'])}  |  Hashes: {len(self.results['hashes'])}  |  Arquivos: {self.results['files_scanned']}")
    
    def clear_results(self):
        self.results = {"ips": set(), "domains": set(), "hashes": {}, "raw": [], "files_scanned": 0}
        for text_widget in [self.result_text, self.ips_text, self.domains_text, self.raw_text, self.hash_text]:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.config(state=tk.DISABLED)
        self.update_stats()
        self.progress_value = 0
        self.processed_files = 0
        self.total_files = 0
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="Pronto para escanear", fg=self.COLORS["status_idle_fg"])
    
    # ==================== ATUALIZAÇÃO DE PROGRESSO EM TEMPO REAL ====================
    def _update_progress_from_thread(self, percent, status_text=None):
        """Agenda a atualização da barra na thread principal"""
        self.root.after(0, lambda: self._do_update_progress(percent, status_text))
    
    def _do_update_progress(self, percent, status_text=None):
        """Executa a atualização na thread principal do Tkinter"""
        self.progress['value'] = percent
        self.progress_label.config(text=f"{int(percent)}%")
        if status_text:
            self.status_label.config(text=status_text, fg=self.COLORS["status_scan_fg"])
        self.root.update_idletasks()
    
    def export_results(self):
        if not self.results["ips"] and not self.results["domains"] and not self.results["hashes"]:
            messagebox.showinfo("Exportar", "Nada para exportar. Execute um scan primeiro.")
            return
        
        filename = filedialog.asksaveasfilename(title="Salvar resultados", defaultextension=".txt", filetypes=[("Arquivo de texto", "*.txt"), ("CSV", "*.csv"), ("JSON", "*.json")])
        
        if not filename:
            return
        
        try:
            ext = os.path.splitext(filename)[1].lower()
            with open(filename, "w", encoding="utf-8") as f:
                if ext == ".json":
                    json.dump({
                        "scan_time": datetime.now().isoformat(),
                        "target": self.path_var.get(),
                        "total_files": self.results["files_scanned"],
                        "ips": sorted(self.results["ips"]),
                        "domains": sorted(self.results["domains"]),
                        "hashes": {k: v for k, v in sorted(self.results["hashes"].items())},
                        "raw_matches": self.results["raw"]
                    }, f, indent=2)
                elif ext == ".csv":
                    f.write("tipo,valor,arquivo\n")
                    for ip in sorted(self.results["ips"]):
                        f.write(f"IP,{ip},\n")
                    for domain in sorted(self.results["domains"]):
                        f.write(f"DOMINIO,{domain},\n")
                    for filepath, sha256 in sorted(self.results["hashes"].items()):
                        f.write(f"SHA256,{sha256},{filepath}\n")
                else:
                    f.write(f"{'='*60}\n  Scanner de IOCs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n  Alvo: {self.path_var.get()}\n  Arquivos escaneados: {self.results['files_scanned']}\n\n")
                    
                    f.write(f"  {'='*56}\n  IP ({len(self.results['ips'])})\n  {'='*56}\n")
                    for ip in sorted(self.results["ips"]):
                        f.write(f"    {ip}\n")
                    
                    f.write(f"\n  {'='*56}\n  Domínios ({len(self.results['domains'])})\n  {'='*56}\n")
                    for domain in sorted(self.results["domains"]):
                        f.write(f"    {domain}\n")
                    
                    if self.results["hashes"]:
                        f.write(f"\n  {'='*56}\n  SHA-256 Hashes ({len(self.results['hashes'])})\n  {'='*56}\n")
                        for filepath, sha256 in sorted(self.results["hashes"].items()):
                            f.write(f"    {sha256}  ->  {filepath}\n")
                    
                    f.write(f"\n  {'='*56}\n  Raw Matches\n  {'='*56}\n")
                    for match in self.results["raw"]:
                        f.write(f"  [{match['type']}] {match['value']:<50} -> {match['file']}\n")
            
            messagebox.showinfo("Exportar", f"Resultados salvos em:\n{filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def start_scan(self):
        if self.scanning:
            return
        
        path = self.path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Aviso", "Selecione um arquivo ou pasta válido!")
            return
        
        self.scanning = True
        self.scan_btn.config(text="⏹ ESCANEANDO...", bg=self.COLORS["scan_btn_active_bg"], fg=self.COLORS["scan_btn_active_fg"], state=tk.DISABLED)
        
        # Limpa apenas os textos, NÃO os resultados (para não perder durante o scan)
        for text_widget in [self.result_text, self.ips_text, self.domains_text, self.raw_text, self.hash_text]:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.config(state=tk.DISABLED)
        
        self.results = {"ips": set(), "domains": set(), "hashes": {}, "raw": [], "files_scanned": 0}
        self.update_stats()
        
        # Mostra a barra de progresso
        self.progress.configure(mode="determinate", value=0)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=3)
        self.progress_label.config(text="0%")
        
        self.status_label.config(text="Iniciando scan...", fg=self.COLORS["status_scan_fg"])
        
        Thread(target=self._scan_thread, args=(path,), daemon=True).start()
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        domain_lower = domain.lower()
        safe_domains = ['google.com', 'googleapis.com', 'gstatic.com', 'googleusercontent.com', 'github.com', 'githubusercontent.com', 'github.io', 'microsoft.com', 'live.com', 'microsoftonline.com', 'cloudflare.com', 'cloudflare.net', 'amazon.com', 'amazonaws.com', 'facebook.com', 'fbcdn.net', 'twitter.com', 'x.com', 'linkedin.com', 'youtube.com', 'ytimg.com', 'instagram.com', 'whatsapp.com', 'telegram.org', 'discord.com', 'discord.gg', 'reddit.com', 'stackoverflow.com', 'stackexchange.com', 'wikipedia.org', 'wikimedia.org', 'oracle.com', 'ibm.com', 'apple.com', 'dropbox.com', 'drive.google.com', 'docs.google.com', 'mail.google.com', 'maps.google.com', 'bitbucket.org', 'gitlab.com', 'npmjs.com', 'pypi.org', 'python.org', 'docker.com', 'docker.io', 'nginx.com', 'nginx.org', 'apache.org', 'mysql.com', 'postgresql.org', 'mongodb.com', 'redis.io', 'elastic.co', 'hashicorp.com', 'terraform.io', 'kubernetes.io', 'massgrave.dev', 'raw.githubusercontent.com']
        
        for safe in safe_domains:
            if domain_lower == safe or domain_lower.endswith('.' + safe):
                return False
        
        suspicious_tlds = {'.xyz', '.top', '.gq', '.ml', '.tk', '.cf', '.ga', '.pw', '.cc', '.ws', '.bid', '.date', '.loan', '.men', '.click', '.download', '.review'}
        suspicious_keywords = ['hack', 'crack', 'exploit', 'malware', 'trojan', 'ransom', 'botnet', 'ddos', 'phish', 'phishing', '0day', 'shell', 'backdoor', 'keylog', 'crypt', 'miner', 'coin']
        
        tld = "." + domain_lower.split(".")[-1] if "." in domain_lower else ""
        
        if tld in suspicious_tlds:
            return True
        if any(kw in domain_lower for kw in suspicious_keywords):
            return True
        if len(domain_lower) > 75:
            return True
        if domain_lower.count("-") > 4:
            return True
        num_count = sum(1 for c in domain_lower if c.isdigit())
        if num_count > len(domain_lower) * 0.5 and len(domain_lower) > 10:
            return True
        return False
    
    def _calculate_sha256(self, filepath: str) -> str:
        """Calcula SHA-256 de um arquivo"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, PermissionError):
            return None
    
    def _scan_thread(self, path):
        try:
            self.results = {"ips": set(), "domains": set(), "hashes": {}, "raw": [], "files_scanned": 0}
            files_scanned = 0
            
            ip_regex = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
            domain_regex = re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')
            url_regex = re.compile(r'https?://[^\s"\'<>]+')
            
            extensions = [e.strip().lower() for e in self.ext_var.get().split(",") if e.strip()]
            
            files_to_scan = []
            if os.path.isfile(path):
                files_to_scan.append(path)
            else:
                if self.recursive_var.get():
                    for root_dir, _, filenames in os.walk(path):
                        for f in filenames:
                            files_to_scan.append(os.path.join(root_dir, f))
                else:
                    files_to_scan = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            
            # Filtra por extensão
            files_to_scan = [f for f in files_to_scan if not extensions or os.path.splitext(f)[1].lower() in extensions]
            total = len(files_to_scan)
            self.total_files = total
            
            if total == 0:
                self.root.after(0, lambda: self.log("⚠️ Nenhum arquivo encontrado com as extensões especificadas!"))
                self.root.after(0, self._finish_scan)
                return
            
            last_percent = -1
            
            for i, filepath in enumerate(files_to_scan):
                if not self.scanning:
                    break
                
                try:
                    # Calcula SHA-256 se habilitado
                    if self.hash_var.get():
                        sha256 = self._calculate_sha256(filepath)
                        if sha256:
                            rel_path = os.path.relpath(filepath, path) if os.path.isdir(path) else filepath
                            self.results["hashes"][rel_path] = sha256
                    
                    # Leitura para IOC scanning
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    files_scanned += 1
                    rel_path = os.path.relpath(filepath, path) if os.path.isdir(path) else filepath
                    
                    urls = url_regex.findall(content)
                    for url in urls:
                        self.results["raw"].append({"type": "URL", "value": url, "file": rel_path})
                    
                    ips = ip_regex.findall(content)
                    for ip in ips:
                        self.results["ips"].add(ip)
                        self.results["raw"].append({"type": "IP", "value": ip, "file": rel_path})
                    
                    domains = domain_regex.findall(content)
                    for domain in domains:
                        if not ip_regex.fullmatch(domain):
                            self.results["domains"].add(domain.lower())
                            self.results["raw"].append({"type": "DOMAIN", "value": domain, "file": rel_path})
                    
                    self.results["files_scanned"] = files_scanned
                    
                    # Calcula percentual (0 a 100)
                    percent = int(((i + 1) / total) * 100)
                    
                    # Atualiza a barra a cada mudança de percentual
                    if percent != last_percent:
                        last_percent = percent
                        self._update_progress_from_thread(
                            percent, 
                            f"Escaneando... {i+1}/{total} arquivos ({percent}%)"
                        )
                        self.root.after(0, self.update_stats)
                
                except (IOError, UnicodeDecodeError):
                    # Tenta ler como binário para hash se falhar como texto
                    if self.hash_var.get():
                        sha256 = self._calculate_sha256(filepath)
                        if sha256:
                            rel_path = os.path.relpath(filepath, path) if os.path.isdir(path) else filepath
                            if rel_path not in self.results["hashes"]:
                                self.results["hashes"][rel_path] = sha256
                    
                    # Mesmo falhando, incrementa o progresso
                    percent = int(((i + 1) / total) * 100)
                    if percent != last_percent:
                        last_percent = percent
                        self._update_progress_from_thread(
                            percent,
                            f"Escaneando... {i+1}/{total} arquivos ({percent}%)"
                        )
                    continue
            
            # Garante 100% ao final
            self._update_progress_from_thread(100, "Finalizando...")
            self.root.after(0, self._display_results)
        
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Erro: {str(e)}"))
            self.root.after(0, self._finish_scan)
    
    def _display_results(self):
        # LOG principal
        self.log(f"{'='*60}")
        self.log(f"📋 SCAN CONCLUÍDO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*60}")
        self.log(f"📁 Alvo: {self.path_var.get()}")
        self.log(f"📄 Arquivos Escaneados: {self.results['files_scanned']}")
        self.log(f"🔐 SHA-256 Hashes calculados: {len(self.results['hashes'])}")
        self.log(f"🌐 IP Encontrados: {len(self.results['ips'])}")
        self.log(f"🏠 Domínios Encontrados: {len(self.results['domains'])}")
        self.log(f"{'='*60}")
        
        if self.results["ips"]:
            self.log(f"\n🔴 IP SUSPEITOS: {len(self.results['ips'])}\n")
            for ip in sorted(self.results["ips"])[:20]:
                self.log(f"   ⚡ {ip}")
            if len(self.results["ips"]) > 20:
                self.log(f"   ... e mais {len(self.results['ips']) - 20} IP")
        
        if self.results["domains"]:
            suspicious = [d for d in self.results["domains"] if self._is_suspicious_domain(d)]
            clean = [d for d in self.results["domains"] if not self._is_suspicious_domain(d)]
            
            if suspicious:
                self.log(f"\n⚠️ DOMÍNIOS SUSPEITOS: {len(suspicious)}\n")
                for domain in sorted(suspicious)[:20]:
                    self.log(f"   🔴 {domain}")
                if len(suspicious) > 20:
                    self.log(f"   ... e mais {len(suspicious) - 20} domínios suspeitos")
            
            self.log(f"\n✅ Domínios limpos: {len(clean)}")
        
        # Preenche aba de IPs
        self.ips_text.config(state=tk.NORMAL)
        self.ips_text.delete(1.0, tk.END)
        for i, ip in enumerate(sorted(self.results["ips"]), 1):
            self.ips_text.insert(tk.END, f"{i:4d}. {ip}\n")
        self.ips_text.insert(tk.END, "\n💡 Duplo clique ou clique direito para abrir no VirusTotal")
        self.ips_text.config(state=tk.DISABLED)
        
        # Preenche aba de Domínios
        self.domains_text.config(state=tk.NORMAL)
        self.domains_text.delete(1.0, tk.END)
        for i, domain in enumerate(sorted(self.results["domains"]), 1):
            suspicious = self._is_suspicious_domain(domain)
            tag = "🚨" if suspicious else "   "
            self.domains_text.insert(tk.END, f"{i:4d}. {tag} {domain}\n")
        self.domains_text.insert(tk.END, "\n💡 Duplo clique ou clique direito para abrir no VirusTotal")
        self.domains_text.config(state=tk.DISABLED)
        
        # Preenche aba de Hashes SHA-256
        self.hash_text.config(state=tk.NORMAL)
        self.hash_text.delete(1.0, tk.END)
        if self.results["hashes"]:
            for i, (filepath, sha256) in enumerate(sorted(self.results["hashes"].items()), 1):
                self.hash_text.insert(tk.END, f"{i:4d}. {sha256}\n\n     Arquivo: {filepath}\n\n\n")
            self.hash_text.insert(tk.END, "\n💡 Duplo clique ou clique direito para abrir no VirusTotal")
        else:
            self.hash_text.insert(tk.END, "Nenhum hash calculado.\nAtive '🔐 Calcular SHA-256' nas opções e escaneie novamente.")
        self.hash_text.config(state=tk.DISABLED)
        
        # Preenche aba de Raw
        self.raw_text.config(state=tk.NORMAL)
        self.raw_text.delete(1.0, tk.END)
        for match in self.results["raw"][:500]:
            self.raw_text.insert(tk.END, f"[{match['type']:8s}] {match['value']:<100s} -> {match['file']}\n")
        if len(self.results["raw"]) > 500:
            self.raw_text.insert(tk.END, f"\n... e mais {len(self.results['raw']) - 500} matches\n")
        self.raw_text.config(state=tk.DISABLED)
        
        self.update_stats()
        self.status_label.config(text=f"✅ Scan concluído! {len(self.results['ips'])} IP, {len(self.results['domains'])} domínios, {len(self.results['hashes'])} hashes", fg=self.COLORS["status_done_fg"])
        
        if self.resolve_var.get() and self.results["domains"]:
            self.log("\n🔍 Resolvendo domínios\n")
            Thread(target=self._resolve_domains, daemon=True).start()
        
        self._finish_scan()
    
    def _resolve_domains(self):
        resolved = {}
        domain_list = list(self.results["domains"])[:50]
        total_domains = len(domain_list)
        
        for idx, domain in enumerate(domain_list):
            try:
                ip = socket.gethostbyname(domain)
                resolved[domain] = ip
                self.root.after(0, lambda d=domain, i=ip: self.log(f"   ✅ {d:<50} -> {i:<15}"))
            except socket.gaierror:
                self.root.after(0, lambda d=domain: self.log(f"   ❌ {d:<50} -> SEM RESOLUÇÃO"))
            
            # Atualiza progresso durante a resolução DNS
            if total_domains > 0:
                dns_percent = int(((idx + 1) / total_domains) * 100)
                self._update_progress_from_thread(
                    dns_percent,
                    f"Resolvendo DNS... {idx+1}/{total_domains}"
                )
        
        if resolved:
            self.root.after(0, lambda: self.log(f"\n📊 Domínios resolvidos: {len(resolved)}/{min(len(self.results['domains']), 50)}\n"))
    
    def _finish_scan(self):
        self.scanning = False
        self._update_progress_from_thread(100, "✅ Scan concluído!")
        self.scan_btn.config(text="▶ INICIAR SCAN", bg=self.COLORS["scan_btn_idle_bg"], fg=self.COLORS["scan_btn_idle_fg"], state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = ScannerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
