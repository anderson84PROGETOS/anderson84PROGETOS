#!/usr/bin/env python3
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import queue
import time
import itertools
import string
import re
from datetime import datetime, timedelta
import platform

# Importações seguras para arquivos comprimidos/PDF
try:
    import pikepdf
except ImportError:
    pikepdf = None

try:
    import pyzipper
except ImportError:
    pyzipper = None

class PyCrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Advanced Cracker Analyzer Pro 🔐")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        # ── Variáveis de Controle ──
        self.is_running = False
        self.is_paused = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.threads = []
        self.found_passwords = {}
        self.total_attempts = 0
        self.start_time = 0
        self.lock = threading.Lock()

        self.log_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.max_threads = 5

        # ── Streaming de Wordlist ──
        self.word_queue = queue.Queue(maxsize=100000)
        self.producer_done = False
        self.wl_total = 0
        self.wl_counting = False

        # ── Alvos de Ataque (Hashes e Arquivos) ──
        self.targets = []

        # ── Paleta de Cores ──
        self.colors = {
            "bg_dark": "#0a0a0a",
            "bg_medium": "#121212",
            "bg_light": "#1a1a1a",
            "accent": "#FF7518",
            "accent2": "#00bfff",
            "text": "#ffffff",
            "text_dim": "#888888",
            "success": "#FF7518",
            "warning": "#fcca03",
            "error": "#ec3609",
            "border": "#222222"
        }

        self.setup_styles()
        self.create_widgets()
        self.process_queues()

    # ══════════════════════════════════════════════════════════
    #  CONFIGURAÇÃO DE ESTILOS (Tkinter ttk)
    # ══════════════════════════════════════════════════════════
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", background=self.colors["bg_dark"], foreground=self.colors["accent2"], font=("Consolas", 14, "bold"))
        style.configure("Header.TLabel", background=self.colors["bg_dark"], foreground=self.colors["accent2"], font=("Consolas", 11, "bold"))
        style.configure("Info.TLabel", background=self.colors["bg_dark"], foreground=self.colors["text"], font=("Consolas", 10))
        style.configure("Status.TLabel", background=self.colors["bg_medium"], foreground=self.colors["accent2"], font=("Consolas", 10, "bold"))
        style.configure("Dark.TFrame", background=self.colors["bg_dark"])
        style.configure("Card.TFrame", background=self.colors["bg_medium"], relief="ridge")
        style.configure("Green.Horizontal.TProgressbar", troughcolor=self.colors["bg_medium"], background=self.colors["accent2"])
        style.configure("Dark.TNotebook", background=self.colors["bg_dark"])
        style.configure("Dark.TNotebook.Tab", background=self.colors["bg_medium"], foreground=self.colors["text_dim"], font=("Consolas", 10, "bold"), padding=(15, 5))
        style.map("Dark.TNotebook.Tab", background=[("selected", self.colors["accent2"])], foreground=[("selected", "#000000")])

    # ══════════════════════════════════════════════════════════
    #  CONSTRUÇÃO DOS COMPONENTES (WIDGETS)
    # ══════════════════════════════════════════════════════════
    def create_widgets(self):
        # Banner Ascii
        banner_frame = ttk.Frame(self.root, style="Dark.TFrame")
        banner_frame.pack(fill="x", padx=10, pady=(10, 5))

        banner_text = """
       ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗ 
      ║                                                                                                                                                                                                                                      ║
      ║   █████╗ ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗██████╗      ██████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗      █████╗ ███╗   ██╗ █████╗ ██╗  ██╗   ██╗███████╗███████╗██████╗     ██████╗ ██████╗  ██████╗     ║
      ║  ██╔══██╗██╔══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝██╔════╝██╔══██╗    ██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔══██╗██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗    ██╔══██╗██╔══██╗██╔═══██╗    ║
      ║  ███████║██║  ██║██║   ██║███████║██╔██╗ ██║██║     █████╗  ██║  ██║    ██║     ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝    ███████║██╔██╗ ██║███████║██║   ╚████╔╝   ███╔╝ █████╗  ██████╔╝    ██████╔╝██████╔╝██║   ██║    ║
      ║  ██╔══██║██║  ██║╚██╗ ██╔╝██╔══██║██║╚██╗██║██║     ██╔══╝  ██║  ██║    ██║     ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗    ██╔══██║██║╚██╗██║██╔══██║██║    ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗    ██╔═══╝ ██╔══██╗██║   ██║    ║
      ║  ██║  ██║██████╔╝ ╚████╔╝ ██║  ██║██║ ╚████║╚██████╗███████╗██████╔╝    ╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║    ██║  ██║██║ ╚████║██║  ██║███████╗██║   ███████╗███████╗██║  ██║    ██║     ██║  ██║╚██████╔╝    ║
      ║  ╚═╝  ╚═╝╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝     ║
      ║                                                                                                                                                                                                                                      ║
      ║                                                                              [MULTI-TARGET]  [STREAMING ENGINE]  [ANALYZER]                                                                                                          ║
                                 ╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝                           
      """

        banner_label = tk.Label(banner_frame, text=banner_text, bg=self.colors["bg_dark"], fg=self.colors["accent2"], font=("Consolas", 7), justify="center")
        banner_label.pack()

        # Notebook (Painel de Abas Separadas)
        self.notebook = ttk.Notebook(self.root, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_config = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_config, text="⚙ Configuração")

        self.tab_console = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_console, text="📋 Console")

        self.tab_results = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_results, text="🔓 Resultados")

        self.tab_analyzer = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_analyzer, text="🔎 Identificador de Hash")

        self.tab_hashgen = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_hashgen, text="⚡ Gerador de Hash")

        self.tab_wordlist = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_wordlist, text="📝 Gerador de Wordlist")

        self.create_config_tab()
        self.create_console_tab()
        self.create_results_tab()
        self.create_analyzer_tab()
        self.create_hashgen_tab()
        self.create_wordlist_tab()
        self.create_status_bar()

    # ─────────────────────────────────────────────────────────
    # BARRA DE STATUS
    # ─────────────────────────────────────────────────────────
    def create_status_bar(self):
        status_bar = tk.Frame(self.root, bg=self.colors["bg_medium"], bd=1, relief="sunken")
        status_bar.pack(side="bottom", fill="x")

        self.lbl_status = tk.Label(status_bar, text="● Pronto", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 9, "bold"), anchor="w")
        self.lbl_status.pack(side="left", padx=10, pady=3)

        self.lbl_threads_info = tk.Label(status_bar, text=f"Threads: {self.max_threads} | pikepdf: {'✔' if pikepdf else '✘'} | pyzipper: {'✔' if pyzipper else '✘'}", bg=self.colors["bg_medium"], fg=self.colors["text_dim"], font=("Consolas", 9), anchor="e")
        self.lbl_threads_info.pack(side="right", padx=10, pady=3)

    # ─────────────────────────────────────────────────────────
    # ABA 1: CONFIGURAÇÃO
    # ─────────────────────────────────────────────────────────
    def create_config_tab(self):
        main_frame = ttk.Frame(self.tab_config, style="Dark.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # --- Entrada de Alvos ---
        targets_frame = tk.LabelFrame(left_frame, text=" 🎯 Alvos (Hashes ou Caminhos de Arquivos PDF/ZIP) ",
                                      bg=self.colors["bg_medium"], fg=self.colors["accent2"],
                                      font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=10)
        targets_frame.pack(fill="x", pady=(0, 10))

        type_frame = ttk.Frame(targets_frame, style="Dark.TFrame")
        type_frame.pack(fill="x", pady=(0, 8))

        tk.Label(type_frame, text="Tipo de Hash padrão:", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 10)).pack(side="left", padx=(0, 10))

        self.hash_type = tk.StringVar(value="auto")
        hash_types = ["auto", "md5", "sha1", "sha256", "sha512", "sha224", "sha384"]
        self.hash_combo = ttk.Combobox(type_frame, textvariable=self.hash_type, values=hash_types, state="readonly", width=12, font=("Consolas", 10))
        self.hash_combo.pack(side="left")

        tk.Label(targets_frame, text="Insira os dados (uma entrada por linha. Suporta caminhos de arquivos PDF/ZIP):", bg=self.colors["bg_medium"], fg=self.colors["text_dim"], font=("Consolas", 9)).pack(anchor="w", pady=(5, 2))

        self.targets_input = tk.Text(targets_frame, height=8, bg=self.colors["bg_dark"], fg=self.colors["text"], insertbackground=self.colors["accent2"], font=("Consolas", 10), relief="sunken", bd=2)
        self.targets_input.pack(fill="x", pady=5)
        self.targets_input.insert("1.0", "# Cole hashes ou caminhos de arquivos aqui\n# Exemplo de Hash: e10adc3949ba59abbe56e057f20f883e\n# Exemplo de Arquivo: C:\\Users\\Nome\\Documento.pdf")

        btn_load_frame = ttk.Frame(targets_frame, style="Dark.TFrame")
        btn_load_frame.pack(fill="x")

        tk.Button(btn_load_frame, text="📂 Importar Hashes (.txt)", command=self.load_targets_file, bg=self.colors["bg_light"], fg=self.colors["text"], font=("Consolas", 9, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="left", padx=(0, 5))
        tk.Button(btn_load_frame, text="📁 Adicionar PDF/ZIP", command=self.add_file_target, bg="#e92a73", fg="black", font=("Consolas", 9, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="left", padx=(0, 5))
        tk.Button(btn_load_frame, text="🗑 Limpar", command=lambda: self.targets_input.delete("1.0", "end"), bg=self.colors["error"], fg=self.colors["text"], font=("Consolas", 9, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="left")

        # --- Opções de Ataque ---
        mode_frame = tk.LabelFrame(left_frame, text=" ⚔ Modo de Ataque ", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=10)
        mode_frame.pack(fill="x", pady=(0, 10))

        self.attack_mode = tk.StringVar(value="wordlist")
        modes = [
            ("📖 Wordlist (Dicionário) — Recomendado", "wordlist"),
            ("🔤 Brute Force (Força Bruta Local)", "bruteforce"),
            ("📖+🔤 Dicionário + Regras de Mutação", "rules")
        ]

        for text, mode in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.attack_mode, value=mode, command=self.toggle_mode_options, bg=self.colors["bg_medium"], fg=self.colors["text"], selectcolor=self.colors["bg_dark"], activebackground=self.colors["bg_medium"], activeforeground=self.colors["accent2"], font=("Consolas", 10), cursor="hand2")
            rb.pack(anchor="w", pady=2)

        # ── Painel de Configuração à Direita ──
        right_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # --- Aba Opções Wordlist ---
        self.wordlist_frame = tk.LabelFrame(right_frame, text=" 📖 Opções de Wordlist ", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=10)
        self.wordlist_frame.pack(fill="x", pady=(0, 10))

        tk.Label(self.wordlist_frame, text="Arquivo Wordlist (.txt):", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 10)).pack(anchor="w")
        wl_entry_frame = ttk.Frame(self.wordlist_frame, style="Dark.TFrame")
        wl_entry_frame.pack(fill="x", pady=5)

        self.wordlist_path = tk.StringVar()
        tk.Entry(wl_entry_frame, textvariable=self.wordlist_path, bg=self.colors["bg_dark"], fg=self.colors["accent2"], insertbackground=self.colors["accent2"], font=("Consolas", 10), relief="sunken", bd=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(wl_entry_frame, text="📁 Buscar", command=self.browse_wordlist, bg=self.colors["bg_light"], fg=self.colors["text"], font=("Consolas", 9, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="right")

        self.lbl_wordlist_info = tk.Label(self.wordlist_frame, text="Total de Linhas: 0", bg=self.colors["bg_medium"], fg=self.colors["text_dim"], font=("Consolas", 9))
        self.lbl_wordlist_info.pack(anchor="w", pady=2)

        # --- Aba Opções Brute Force ---
        self.bruteforce_frame = tk.LabelFrame(right_frame, text=" 🔤 Opções Brute Force ", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=10)
        self.bruteforce_frame.pack(fill="x", pady=(0, 10))

        self.use_lower = tk.BooleanVar(value=True)
        self.use_upper = tk.BooleanVar(value=False)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_special = tk.BooleanVar(value=False)

        checks = [
            ("Minúsculas (a-z)", self.use_lower),
            ("Maiúsculas (A-Z)", self.use_upper),
            ("Dígitos (0-9)", self.use_digits),
            ("Especiais (!@#$)", self.use_special)
        ]

        for text, var in checks:
            tk.Checkbutton(self.bruteforce_frame, text=text, variable=var, bg=self.colors["bg_medium"], fg=self.colors["text"], selectcolor=self.colors["bg_dark"], activebackground=self.colors["bg_medium"], font=("Consolas", 9), cursor="hand2").pack(anchor="w")

        len_frame = ttk.Frame(self.bruteforce_frame, style="Dark.TFrame")
        len_frame.pack(fill="x", pady=5)
        tk.Label(len_frame, text="Tam. Min:", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 10)).pack(side="left")
        self.min_length = tk.IntVar(value=1)
        tk.Spinbox(len_frame, from_=1, to=12, textvariable=self.min_length, width=4, bg=self.colors["bg_dark"], fg=self.colors["accent2"]).pack(side="left", padx=5)

        tk.Label(len_frame, text="Max:", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 10)).pack(side="left", padx=(10, 0))
        self.max_length = tk.IntVar(value=6)
        tk.Spinbox(len_frame, from_=1, to=12, textvariable=self.max_length, width=4, bg=self.colors["bg_dark"], fg=self.colors["accent2"]).pack(side="left", padx=5)

        # --- Opções de Regras ---
        self.rules_frame = tk.LabelFrame(right_frame, text=" 📖+🔤 Regras de Mutação ", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=10)
        self.rules_frame.pack(fill="x", pady=(0, 10))

        self.rule_capitalize = tk.BooleanVar(value=True)
        self.rule_upper = tk.BooleanVar(value=False)
        self.rule_leet = tk.BooleanVar(value=True)
        self.rule_append_num = tk.BooleanVar(value=True)

        rules = [
            ("Capitalize (senha -> Senha)", self.rule_capitalize),
            ("UPPER (senha -> SENHA)", self.rule_upper),
            ("L33t Speak (senha -> 53nh4)", self.rule_leet),
            ("Adicionar Números (senha -> senha123)", self.rule_append_num)
        ]

        for text, var in rules:
            tk.Checkbutton(self.rules_frame, text=text, variable=var, bg=self.colors["bg_medium"], fg=self.colors["text"], selectcolor=self.colors["bg_dark"], activebackground=self.colors["bg_medium"], font=("Consolas", 9), cursor="hand2").pack(anchor="w")

        # --- Controle de Threads e Inicialização ---
        action_frame = tk.Frame(left_frame, bg=self.colors["bg_dark"])
        action_frame.pack(fill="x", pady=(10, 0))

        self.btn_start = tk.Button(action_frame, text="▶  INICIAR RECONHECIMENTO", command=self.start_attack, bg="#059e07", fg="black", font=("Consolas", 12, "bold"), relief="raised", bd=3, cursor="hand2", height=2)
        self.btn_start.pack(fill="x", pady=(0, 5))

        btn_row = tk.Frame(action_frame, bg=self.colors["bg_dark"])
        btn_row.pack(fill="x")

        self.btn_pause = tk.Button(btn_row, text="⏸ PAUSAR", command=self.pause_attack, bg=self.colors["warning"], fg="black", font=("Consolas", 10, "bold"), relief="raised", bd=2, cursor="hand2", state="disabled")
        self.btn_pause.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_stop = tk.Button(btn_row, text="⏹ PARAR", command=self.stop_attack, bg=self.colors["error"], fg="white", font=("Consolas", 10, "bold"), relief="raised", bd=2, cursor="hand2", state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(3, 0))

        self.toggle_mode_options()

    # ─────────────────────────────────────────────────────────
    # ABA 2: CONSOLE & ESTATÍSTICAS
    # ─────────────────────────────────────────────────────────
    def create_console_tab(self):
        console_frame = ttk.Frame(self.tab_console, style="Dark.TFrame")
        console_frame.pack(fill="both", expand=True, padx=10, pady=10)

        stats_frame = tk.LabelFrame(console_frame, text=" 📊 Estatísticas Operacionais ", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"), bd=2, relief="ridge", padx=10, pady=8)
        stats_frame.pack(fill="x", pady=(0, 10))

        stats_grid = tk.Frame(stats_frame, bg=self.colors["bg_medium"])
        stats_grid.pack(fill="x")

        self.lbl_speed = tk.Label(stats_grid, text="⚡ Velocidade: 0 p/s", bg=self.colors["bg_medium"], fg=self.colors["accent2"], font=("Consolas", 11, "bold"))
        self.lbl_speed.grid(row=0, column=0, sticky="w", padx=(0, 30))

        self.lbl_attempts = tk.Label(stats_grid, text="🔢 Testadas: 0", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 11))
        self.lbl_attempts.grid(row=0, column=1, sticky="w", padx=(0, 30))

        self.lbl_found = tk.Label(stats_grid, text="🔓 Encontradas: 0", bg=self.colors["bg_medium"], fg=self.colors["accent"], font=("Consolas", 11, "bold"))
        self.lbl_found.grid(row=0, column=2, sticky="w")

        self.lbl_elapsed = tk.Label(stats_grid, text="⏱ Tempo Decorrido: 00:00:00", bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 11))
        self.lbl_elapsed.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.lbl_current = tk.Label(stats_grid, text="🔍 Testando: ---", bg=self.colors["bg_medium"], fg=self.colors["warning"], font=("Consolas", 11))
        self.lbl_current.grid(row=1, column=1, columnspan=2, sticky="w", pady=(5, 0))

        # Progresso
        progress_frame = tk.Frame(console_frame, bg=self.colors["bg_dark"])
        progress_frame.pack(fill="x", pady=(5, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, style="Green.Horizontal.TProgressbar", length=400)
        self.progress_bar.pack(fill="x")

        self.lbl_progress = tk.Label(progress_frame, text="0%", bg=self.colors["bg_dark"], fg=self.colors["accent2"], font=("Consolas", 10, "bold"))
        self.lbl_progress.pack()

        # Saída do Terminal
        tk.Label(console_frame, text="📋 Histórico de Execução (Terminal):", bg=self.colors["bg_dark"], fg=self.colors["accent2"], font=("Consolas", 11, "bold")).pack(anchor="w")
        self.console_output = scrolledtext.ScrolledText(console_frame, bg="#000000", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 10), relief="sunken", bd=2, state="disabled")
        self.console_output.pack(fill="both", expand=True, pady=(3, 0))

        self.console_output.tag_configure("info", foreground="#00d2ff")
        self.console_output.tag_configure("detected", foreground="#00bfff", font=("Consolas", 10, "bold"))
        self.console_output.tag_configure("success", foreground=self.colors["accent"])
        self.console_output.tag_configure("warning", foreground=self.colors["warning"])
        self.console_output.tag_configure("error", foreground=self.colors["error"])

    # ─────────────────────────────────────────────────────────
    # ABA 3: RESULTADOS
    # ─────────────────────────────────────────────────────────
    def create_results_tab(self):
        results_frame = ttk.Frame(self.tab_results, style="Dark.TFrame")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(results_frame, text="🔓 Senhas Recuperadas com Sucesso:", bg=self.colors["bg_dark"], fg=self.colors["accent2"], font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0, 5))

        tree_frame = tk.Frame(results_frame, bg=self.colors["bg_dark"])
        tree_frame.pack(fill="both", expand=True)

        columns = ("id", "target", "password", "type", "time")
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        self.results_tree.heading("id", text="ID")
        self.results_tree.heading("target", text="Hash Completa Quebrada / Caminho do Arquivo")
        self.results_tree.heading("password", text="🔑 Senha Recuperada")
        self.results_tree.heading("type", text="Tipo")
        self.results_tree.heading("time", text="Tempo decorrido")

        self.results_tree.column("id", width=30)
        self.results_tree.column("target", width=800, stretch=True)
        self.results_tree.column("password", width=210)
        self.results_tree.column("type", width=80)
        self.results_tree.column("time", width=100)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        btn_frame = tk.Frame(results_frame, bg=self.colors["bg_dark"])
        btn_frame.pack(fill="x", pady=(10, 0))

        tk.Button(btn_frame, text="💾 Exportar Resultados (.txt)", command=self.export_results, bg=self.colors["bg_light"], fg=self.colors["text"], font=("Consolas", 10, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="left", padx=(0, 5))
        tk.Button(btn_frame, text="🗑 Limpar Tabela", command=self.clear_results, bg=self.colors["error"], fg=self.colors["text"], font=("Consolas", 10, "bold"), relief="raised", bd=2, cursor="hand2").pack(side="left")

    # ─────────────────────────────────────────────────────────
    # ABA 4: IDENTIFICADOR DE HASH (COM CORES)
    # ─────────────────────────────────────────────────────────
    def create_analyzer_tab(self):
        container = ttk.Frame(self.tab_analyzer, style="Dark.TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        left_side = tk.Frame(container, bg=self.colors["bg_dark"], highlightbackground="#222", highlightthickness=1)
        left_side.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(left_side, text="🔎 IDENTIFICADOR DE TIPO DE HASH", font=("Consolas", 14, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent2"]).pack(pady=8)

        btn_ident_frame = tk.Frame(left_side, bg=self.colors["bg_dark"])
        btn_ident_frame.pack(pady=4)

        tk.Button(btn_ident_frame, text="📂 Abrir .txt", command=self.abrir_arquivo_ident_hash, bg="#FF9800", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_ident_frame, text="🔍 Identificar", command=self.identificar_hashes, bg="#06c91a", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_ident_frame, text="💾 Salvar Análise", command=self.salvar_ident_hash, bg="#2196F3", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_ident_frame, text="🗑️ Limpar", command=self.limpar_ident_hash, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        tk.Label(left_side, text="Insira as hashes para analisar (uma por linha):", font=("Consolas", 11, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent2"]).pack(anchor="w", padx=15, pady=(10, 2))
        self.entrada_identificar_hash = scrolledtext.ScrolledText(left_side, height=8, bg=self.colors["bg_medium"], fg=self.colors["text"], insertbackground=self.colors["accent2"], font=("Consolas", 11))
        self.entrada_identificar_hash.pack(fill="both", expand=True, padx=15, pady=5)

        tk.Label(left_side, text="Resultado da Análise de Estrutura:", font=("Consolas", 11, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent2"]).pack(anchor="w", padx=15, pady=(10, 2))
        self.resultado_ident_hash = scrolledtext.ScrolledText(left_side, height=10, bg=self.colors["bg_medium"], fg=self.colors["text"], font=("Consolas", 11))
        self.resultado_ident_hash.pack(fill="both", expand=True, padx=15, pady=5)

        self.resultado_ident_hash.tag_configure("sucesso", foreground="#00ff41", font=("Consolas", 11, "bold"))
        self.resultado_ident_hash.tag_configure("aviso", foreground="#FF9800", font=("Consolas", 11, "bold"))
        self.resultado_ident_hash.tag_configure("erro", foreground="#f44336", font=("Consolas", 11, "bold"))
        self.resultado_ident_hash.tag_configure("info", foreground="#00bfff", font=("Consolas", 11))
        self.resultado_ident_hash.tag_configure("separador", foreground="#555555")

    # ─────────────────────────────────────────────────────────
    # ABA 5: GERADOR DE HASH
    # ─────────────────────────────────────────────────────────
    def create_hashgen_tab(self):
        container = ttk.Frame(self.tab_hashgen, style="Dark.TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        right_side = tk.Frame(container, bg=self.colors["bg_dark"], highlightbackground="#222", highlightthickness=1)
        right_side.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(right_side, text="⚡ GERADOR DE HASHES", font=("Consolas", 14, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent"]).pack(pady=8)

        tk.Label(right_side, text="Senha ou Texto Limpo:", font=("Consolas", 11, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent"]).pack(anchor="w", padx=15, pady=(10, 2))
        self.entrada_gerador_texto = scrolledtext.ScrolledText(right_side, height=5, bg=self.colors["bg_medium"], fg=self.colors["text"], insertbackground=self.colors["accent"], font=("Consolas", 11))
        self.entrada_gerador_texto.pack(fill="x", padx=15, pady=5)

        frame_botoes_gen = tk.Frame(right_side, bg=self.colors["bg_dark"])
        frame_botoes_gen.pack(pady=10)

        tk.Button(frame_botoes_gen, text="Gerar MD5", command=lambda: self.gerar_hash_individual("md5"), bg="#d0c4fc", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=4)
        tk.Button(frame_botoes_gen, text="Gerar SHA1", command=lambda: self.gerar_hash_individual("sha1"), bg="#c4fce8", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=4)
        tk.Button(frame_botoes_gen, text="Gerar SHA256", command=lambda: self.gerar_hash_individual("sha256"), bg="#fcd7c4", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=4)
        tk.Button(frame_botoes_gen, text="Gerar SHA512", command=lambda: self.gerar_hash_individual("sha512"), bg="#fbc4f7", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=4)
        tk.Button(frame_botoes_gen, text="⚡ Todos Algoritmos", command=self.gerar_todos_hashes, bg="#00ff41", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=8)
        tk.Button(frame_botoes_gen, text="💾 Salvar como .txt", command=self.salvar_hashes_gerados, bg="#2196F3", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=4)
        tk.Button(frame_botoes_gen, text="🗑️ Limpar", command=self.limpar_gerador, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=4)

        tk.Label(right_side, text="Hashes Resultantes Geradas:", font=("Consolas", 11, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent"]).pack(anchor="w", padx=15, pady=(10, 2))
        self.saida_gerador = scrolledtext.ScrolledText(right_side, height=12, bg=self.colors["bg_medium"], fg=self.colors["accent"], font=("Consolas", 11))
        self.saida_gerador.pack(fill="both", expand=True, padx=15, pady=5)

    # ─────────────────────────────────────────────────────────
    # ABA 6: GERADOR DE WORDLIST (SEM LIMITE — MODO EXPLOSIVO)
    # ─────────────────────────────────────────────────────────
    def create_wordlist_tab(self):
        container = ttk.Frame(self.tab_wordlist, style="Dark.TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        frame = tk.Frame(container, bg=self.colors["bg_dark"], highlightbackground="#222", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(frame, text="📝 GERADOR DE WORDLIST (SEM LIMITE)", font=("Consolas", 14, "bold"),
                 bg=self.colors["bg_dark"], fg=self.colors["accent"]).pack(pady=8)

        # Palavras-base
        tk.Label(frame, text="Palavras-base (uma por linha):", font=("Consolas", 11, "bold"),
                 bg=self.colors["bg_dark"], fg=self.colors["accent"]).pack(anchor="w", padx=15, pady=(10, 2))
        self.wl_base_text = scrolledtext.ScrolledText(frame, height=6, bg=self.colors["bg_medium"],
                                                      fg=self.colors["text"], insertbackground=self.colors["accent"],
                                                      font=("Consolas", 11))
        self.wl_base_text.pack(fill="x", padx=15, pady=5)
        self.wl_base_text.insert("1.0", "# Exemplo:\nadmin\nsenha\ncasa\ndeo")

        # Opções de mutação
        opts = tk.LabelFrame(frame, text=" ⚙ Opções de Mutação ", bg=self.colors["bg_medium"],
                             fg=self.colors["accent2"], font=("Consolas", 10, "bold"), bd=2,
                             relief="ridge", padx=10, pady=8)
        opts.pack(fill="x", padx=15, pady=8)

        self.wl_capitalize = tk.BooleanVar(value=True)
        self.wl_upper = tk.BooleanVar(value=True)
        self.wl_lower = tk.BooleanVar(value=True)
        self.wl_leet = tk.BooleanVar(value=False)
        self.wl_reverse = tk.BooleanVar(value=False)
        self.wl_append_nums = tk.BooleanVar(value=True)
        self.wl_dedupe = tk.BooleanVar(value=False)

        wl_checks = [
            ("Capitalize (casa -> Casa)", self.wl_capitalize),
            ("MAIÚSCULAS (casa -> CASA)", self.wl_upper),
            ("minúsculas (CASA -> casa)", self.wl_lower),
            ("L33t Speak (casa -> c4s4)", self.wl_leet),
            ("Inverter (casa -> asac)", self.wl_reverse),
            ("Adicionar Números (casa -> casa123)", self.wl_append_nums),
            ("Remover Duplicatas", self.wl_dedupe),
        ]
        for text, var in wl_checks:
            tk.Checkbutton(opts, text=text, variable=var, bg=self.colors["bg_medium"],
                           fg=self.colors["text"], selectcolor=self.colors["bg_dark"],
                           activebackground=self.colors["bg_medium"], font=("Consolas", 9),
                           cursor="hand2").pack(side="left", padx=(0, 15))

        # ── MODO EXPLOSIVO (geração combinatória SEM LIMITE) ──
        boom = tk.LabelFrame(frame, text=" 💥 Modo Explosivo (Geração Combinatória Ilimitada) ", bg=self.colors["bg_medium"],
                             fg=self.colors["error"], font=("Consolas", 10, "bold"), bd=2,
                             relief="ridge", padx=10, pady=8)
        boom.pack(fill="x", padx=15, pady=8)

        self.wl_explosive = tk.BooleanVar(value=False)
        tk.Checkbutton(boom, text="💥 ATIVAR MODO EXPLOSIVO (sufixos combinatórios)", variable=self.wl_explosive,
                       bg=self.colors["bg_medium"], fg=self.colors["warning"], selectcolor=self.colors["bg_dark"],
                       activebackground=self.colors["bg_medium"], font=("Consolas", 10, "bold"),
                       cursor="hand2").pack(anchor="w")

        boom_row = tk.Frame(boom, bg=self.colors["bg_medium"])
        boom_row.pack(fill="x", pady=3)

        tk.Label(boom_row, text="Sufixos (charset):", bg=self.colors["bg_medium"], fg=self.colors["text"],
                 font=("Consolas", 9)).pack(side="left")
        self.wl_suf_charset = tk.StringVar(value="0123456789")
        tk.Entry(boom_row, textvariable=self.wl_suf_charset, width=25, bg=self.colors["bg_dark"],
                 fg=self.colors["accent2"], font=("Consolas", 9)).pack(side="left", padx=5)

        tk.Label(boom_row, text="Tam. Max sufixo:", bg=self.colors["bg_medium"], fg=self.colors["text"],
                 font=("Consolas", 9)).pack(side="left", padx=(10, 0))
        self.wl_suf_maxlen = tk.IntVar(value=3)
        tk.Spinbox(boom_row, from_=1, to=6, textvariable=self.wl_suf_maxlen, width=4,
                   bg=self.colors["bg_dark"], fg=self.colors["accent2"], font=("Consolas", 9)).pack(side="left", padx=5)

        self.wl_suf_pre = tk.BooleanVar(value=False)
        tk.Checkbutton(boom_row, text="Também como prefixo", variable=self.wl_suf_pre,
                       bg=self.colors["bg_medium"], fg=self.colors["text"], selectcolor=self.colors["bg_dark"],
                       activebackground=self.colors["bg_medium"], font=("Consolas", 9)).pack(side="left", padx=10)

        self.wl_combine_words = tk.BooleanVar(value=True)
        tk.Checkbutton(boom, text="🔗 Combinar palavras-base entre si (admin+senha, casa+123...)", variable=self.wl_combine_words,
                       bg=self.colors["bg_medium"], fg=self.colors["text"], selectcolor=self.colors["bg_dark"],
                       activebackground=self.colors["bg_medium"], font=("Consolas", 9)).pack(anchor="w")

        self.lbl_wl_warning = tk.Label(boom, text="⚠ Charset 10 + tam 3 = 1.110 sufixos por palavra. "
                                       "Charset 62 + tam 4 = 15.054.496 sufixos por palavra!",
                                       bg=self.colors["bg_medium"], fg=self.colors["warning"], font=("Consolas", 8))
        self.lbl_wl_warning.pack(anchor="w")

        # Botões
        btn_frame = tk.Frame(frame, bg=self.colors["bg_dark"])
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="⚡ Gerar Preview", command=self.wl_gerar_preview, bg="#00ff41",
                  fg="black", font=("Consolas", 10, "bold")).pack(side="left", padx=4)
        tk.Button(btn_frame, text="💾 Salvar como .txt", command=self.wl_salvar, bg="#2196F3",
                  fg="black", font=("Consolas", 10, "bold")).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✅ Usar como Wordlist", command=self.wl_usar, bg="#FF7518",
                  fg="black", font=("Consolas", 10, "bold")).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🗑️ Limpar", command=self.wl_limpar, bg="#f44336",
                  fg="white", font=("Consolas", 10, "bold")).pack(side="left", padx=4)

        self.lbl_wl_count = tk.Label(frame, text="Total de linhas geradas: 0", bg=self.colors["bg_dark"],
                                     fg=self.colors["warning"], font=("Consolas", 10, "bold"))
        self.lbl_wl_count.pack(anchor="w", padx=15)

        # Preview
        self.wl_preview = scrolledtext.ScrolledText(frame, height=10, bg="#000000", fg="#00ff41",
                                                    insertbackground="#00ff41", font=("Consolas", 10))
        self.wl_preview.pack(fill="both", expand=True, padx=15, pady=5)

    def _wl_leet(self, s):
        mapping = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        return "".join(mapping.get(c, c) for c in s)

    def wl_mutacoes(self, word):
        """Gera todas as mutações de uma palavra-base conforme as opções."""
        resultados = []
        vistos = set()

        def add(x):
            if x and x not in vistos:
                vistos.add(x)
                resultados.append(x)

        base_forms = [word]
        if self.wl_lower.get(): base_forms.append(word.lower())
        if self.wl_upper.get(): base_forms.append(word.upper())
        if self.wl_capitalize.get(): base_forms.append(word.capitalize())

        for form in base_forms:
            add(form)
            if self.wl_leet.get():
                add(self._wl_leet(form))
            if self.wl_reverse.get():
                add(form[::-1])
                if self.wl_leet.get():
                    add(self._wl_leet(form)[::-1])

            # Números fixos
            if self.wl_append_nums.get():
                for num in ["1", "12", "123", "1234", "12345", "123456", "!", "@", "#", "2024", "2025", "2026"]:
                    add(form + num)
                    if self.wl_leet.get():
                        add(self._wl_leet(form) + num)
                    if self.wl_reverse.get():
                        add(form[::-1] + num)

            # 💥 MODO EXPLOSIVO: sufixos/prefixos combinatórios SEM LIMITE
            if self.wl_explosive.get():
                charset = self.wl_suf_charset.get() or "0123456789"
                maxlen = self.wl_suf_maxlen.get()
                for n in range(1, maxlen + 1):
                    for suf_tuple in itertools.product(charset, repeat=n):
                        suf = "".join(suf_tuple)
                        add(form + suf)          # sufixo
                        if self.wl_suf_pre.get():
                            add(suf + form)      # prefixo
                        if self.wl_leet.get():
                            add(self._wl_leet(form) + suf)
        return resultados

    def wl_gerar_lista(self):
        """Retorna a lista completa de senhas geradas — SEM LIMITE de linhas."""
        raw = self.wl_base_text.get("1.0", tk.END).strip().splitlines()
        palavras = [l.strip() for l in raw if l.strip() and not l.strip().startswith("#")]
        if not palavras:
            return []

        if self.wl_dedupe.get():
            lista = set()
            for p in palavras:
                lista.update(self.wl_mutacoes(p))
            return sorted(lista)
        else:
            lista = []
            for p in palavras:
                lista.extend(self.wl_mutacoes(p))

        # 🔗 Combinar palavras-base entre si (admin+senha, casa+123+admin, etc.)
        if self.wl_explosive.get() and self.wl_combine_words.get() and len(palavras) > 1:
            for a, b in itertools.permutations(palavras, 2):
                lista.append(a + b)
                lista.append(b + a)
                if self.wl_append_nums.get():
                    for num in ["1", "123", "2024", "2025", "2026"]:
                        lista.append(a + b + num)
        return lista

    def wl_gerar_preview(self):
        lista = self.wl_gerar_lista()
        self.wl_preview.delete("1.0", tk.END)
        self.lbl_wl_count.config(text=f"Total de linhas geradas: {len(lista):,}")
        preview = lista[:2000]
        self.wl_preview.insert(tk.END, "\n".join(preview))
        if len(lista) > len(preview):
            self.wl_preview.insert(tk.END, f"\n\n[...] +{len(lista)-len(preview):,} linhas (todas salvas no arquivo)")

    def wl_salvar(self):
        lista = self.wl_gerar_lista()
        if not lista:
            messagebox.showerror("Erro", "Nenhuma palavra-base informada!")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo Texto", "*.txt")],
                                               initialfile="wordlist.txt")
        if caminho:
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("\n".join(lista))
                messagebox.showinfo("Sucesso", f"Wordlist salva com {len(lista):,} linhas!\n\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def wl_usar(self):
        """Escolhe onde salvar (SEM LIMITE de linhas) e configura como wordlist ativa do ataque."""
        lista = self.wl_gerar_lista()
        if not lista:
            messagebox.showerror("Erro", "Nenhuma palavra-base informada!")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Wordlist e Usar no Ataque",
            defaultextension=".txt",
            filetypes=[("Arquivo Texto", "*.txt")],
            initialfile="wordlist.txt"
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(lista))
            self.wordlist_path.set(caminho)
            self.wl_total = len(lista)
            self.count_wordlist_lines(caminho)
            self.lbl_wl_count.config(text=f"Total de linhas geradas: {len(lista):,}")
            self.log_message(f"[+] Wordlist gerada e configurada: {caminho} ({len(lista):,} linhas)", "info")
            messagebox.showinfo("Sucesso", f"Wordlist configurada para ataque!\n\n{caminho}\n({len(lista):,} linhas)")
            self.notebook.select(0)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao configurar wordlist: {e}")

    def wl_limpar(self):
        self.wl_base_text.delete("1.0", tk.END)
        self.wl_preview.delete("1.0", tk.END)
        self.lbl_wl_count.config(text="Total de linhas geradas: 0")

    # ══════════════════════════════════════════════════════════
    #  PROCESSAMENTO DE QUEUES (ASSÍNCRONO E THREAD-SAFE)
    # ══════════════════════════════════════════════════════════
    def process_queues(self):
        # 1. Logs de Execução
        while not self.log_queue.empty():
            try:
                msg, tag = self.log_queue.get_nowait()
                self.console_output.configure(state="normal")
                self.console_output.insert("end", msg, tag)
                self.console_output.see("end")
                self.console_output.configure(state="disabled")
            except queue.Empty:
                break

        # 2. Senhas Encontradas
        while not self.result_queue.empty():
            try:
                res = self.result_queue.get_nowait()
                self.results_tree.insert("", "end", values=res)
            except queue.Empty:
                break

        # 3. Atualizações de Interface
        while not self.ui_queue.empty():
            try:
                item = self.ui_queue.get_nowait()
                kind = item[0]
                if kind == "wordlist_total":
                    count, name = item[1], item[2]
                    self.lbl_wordlist_info.config(text=f"Total de Linhas: {count:,} em {name}")
                elif kind == "progress":
                    pct, label_text = item[1], item[2]
                    self.progress_var.set(pct)
                    self.lbl_progress.config(text=f"{pct:.1f}%")
                    self.lbl_current.config(text=label_text)
            except queue.Empty:
                break

        if self.is_running:
            self.update_live_stats()

        self.root.after(80, self.process_queues)

    def update_live_stats(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        with self.lock:
            attempts = self.total_attempts
            found = len(self.found_passwords)

        speed = attempts / elapsed if elapsed > 0 else 0
        self.lbl_speed.config(text=f"⚡ Velocidade: {speed:,.0f} p/s")
        self.lbl_attempts.config(text=f"🔢 Testadas: {attempts:,}")
        self.lbl_found.config(text=f"🔓 Encontradas: {found}")

        elapsed_str = str(timedelta(seconds=int(elapsed)))
        self.lbl_elapsed.config(text=f"⏱ Tempo Decorrido: {elapsed_str}")

    # ══════════════════════════════════════════════════════════
    #  AÇÕES DE CONFIGURAÇÃO & DIALOGS
    # ══════════════════════════════════════════════════════════
    def toggle_mode_options(self):
        mode = self.attack_mode.get()
        if mode == "wordlist":
            self.wordlist_frame.configure(fg=self.colors["accent2"])
            self.bruteforce_frame.configure(fg=self.colors["text_dim"])
            self.rules_frame.configure(fg=self.colors["text_dim"])
        elif mode == "bruteforce":
            self.wordlist_frame.configure(fg=self.colors["text_dim"])
            self.bruteforce_frame.configure(fg=self.colors["accent2"])
            self.rules_frame.configure(fg=self.colors["text_dim"])
        elif mode == "rules":
            self.wordlist_frame.configure(fg=self.colors["accent2"])
            self.bruteforce_frame.configure(fg=self.colors["text_dim"])
            self.rules_frame.configure(fg=self.colors["accent2"])

    def browse_wordlist(self):
        path = filedialog.askopenfilename(title="Selecionar Wordlist", filetypes=[("Arquivos TXT", "*.txt"), ("Todos os Arquivos", "*.*")])
        if path:
            self.wordlist_path.set(path)
            self.count_wordlist_lines(path)

    def count_wordlist_lines(self, path):
        if not os.path.isfile(path):
            return
        self.wl_counting = True
        self.lbl_wordlist_info.config(text="Contando linhas...")

        def _counter():
            try:
                count = 0
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024 * 8), b""):
                        count += chunk.count(b"\n")
                self.wl_total = count
                self.wl_counting = False
                self.ui_queue.put(("wordlist_total", count, os.path.basename(path)))
            except Exception as e:
                self.wl_counting = False
                self.log_queue.put((f"[!] Erro ao analisar wordlist: {e}\n", "error"))

        threading.Thread(target=_counter, daemon=True).start()

    def load_targets_file(self):
        path = filedialog.askopenfilename(title="Selecionar Arquivo de Hashes", filetypes=[("Arquivos TXT", "*.txt"), ("Todos os Arquivos", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self.targets_input.delete("1.0", tk.END)
                self.targets_input.insert("1.0", content)
                self.log_message(f"[+] Arquivo de hashes importado: {os.path.basename(path)}", "info")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler arquivo:\n{e}")

    def add_file_target(self):
        path = filedialog.askopenfilename(title="Adicionar Arquivo (PDF ou ZIP)", filetypes=[("Arquivos Comprimidos/PDF", "*.pdf *.zip")])
        if path:
            self.targets_input.insert(tk.END, f"\n{path}")
            self.log_message(f"[+] Arquivo anexado: {os.path.basename(path)}", "info")

    def log_message(self, msg, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((f"[{timestamp}] {msg}\n", tag))

    # ══════════════════════════════════════════════════════════
    #  PARSING & VALIDAÇÃO DE ALVOS
    # ══════════════════════════════════════════════════════════
    def parse_targets(self):
        raw = self.targets_input.get("1.0", tk.END).strip().splitlines()
        self.targets = []

        for idx, line in enumerate(raw, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 1. Verificar se é arquivo PDF ou ZIP
            if os.path.isfile(line):
                ext = os.path.splitext(line)[1].lower()
                if ext == ".pdf":
                    if not pikepdf:
                        self.log_message(f"[!] Biblioteca 'pikepdf' ausente. Ignorando PDF: {line}", "error")
                        continue
                    self.targets.append({"type": "pdf", "value": line, "user": os.path.basename(line), "id": idx})
                elif ext == ".zip":
                    if not pyzipper:
                        self.log_message(f"[!] Biblioteca 'pyzipper' ausente. Ignorando ZIP: {line}", "error")
                        continue
                    self.targets.append({"type": "zip", "value": line, "user": os.path.basename(line), "id": idx})
                else:
                    self.log_message(f"[!] Extensão de arquivo não suportada: {line}", "error")
            else:
                # 2. Tratar como Hash
                candidate_hash = line
                user = f"Hash_{idx}"
                if ":" in line:
                    parts = line.split(":", 1)
                    user = parts[0].strip()
                    candidate_hash = parts[1].strip()

                htype = self.hash_type.get()
                if htype == "auto":
                    htype = self.detect_hash_type(candidate_hash)

                if htype:
                    self.targets.append({"type": "hash", "value": candidate_hash.lower(), "hash_type": htype, "user": user, "id": idx})
                    self.log_message(f"[🔍] Hash Detectado ({htype.upper()}): {candidate_hash}", "detected")
                else:
                    self.log_message(f"[!] Entrada não reconhecida: {line}", "error")

        return len(self.targets) > 0

    def detect_hash_type(self, hash_str):
        h = hash_str.strip()
        tamanho = len(h)
        if not re.match(r'^[0-9a-fA-F]+$', h):
            return None
        lengths = {32: "md5", 40: "sha1", 56: "sha224", 64: "sha256", 96: "sha384", 128: "sha512"}
        return lengths.get(tamanho)

    def compute_hash(self, text, algorithm):
        encoded = text.encode('utf-8')
        return getattr(hashlib, algorithm)(encoded).hexdigest()

    def get_charset(self):
        charset = ""
        if self.use_lower.get(): charset += string.ascii_lowercase
        if self.use_upper.get(): charset += string.ascii_uppercase
        if self.use_digits.get(): charset += string.digits
        if self.use_special.get(): charset += "!@#$%^&*()_+-="
        return charset if charset else string.ascii_lowercase + string.digits

    def apply_rules(self, word):
        mutations = [word]
        if self.rule_capitalize.get():
            mutations.append(word.capitalize())
        if self.rule_upper.get():
            mutations.append(word.upper())
        if self.rule_leet.get():
            mapping = {'a':'4', 'e':'3', 'i':'1', 'o':'0', 's':'5', 't':'7'}
            leet = "".join(mapping.get(c, c) for c in word.lower())
            mutations.append(leet)
        if self.rule_append_num.get():
            for num in ["1", "123", "2024", "2025"]:
                mutations.append(word + num)
        return list(set(mutations))

    # ══════════════════════════════════════════════════════════
    #  MÓDULO DE VALIDAÇÃO DE SENHAS
    # ══════════════════════════════════════════════════════════
    def test_password(self, password):
        for target in self.targets:
            target_type = target["type"]
            target_val = target["value"]

            if target_val in self.found_passwords:
                continue

            if target_type == "hash":
                htype = target["hash_type"]
                computed = self.compute_hash(password, htype)
                if computed == target_val:
                    self.register_found(target, password)

            elif target_type == "pdf":
                try:
                    with pikepdf.open(target_val, password=password):
                        self.register_found(target, password)
                except pikepdf.PasswordError:
                    continue
                except Exception:
                    pass

            elif target_type == "zip":
                try:
                    with pyzipper.AESZipFile(target_val) as zf:
                        zf.pwd = password.encode('utf-8')
                        zf.namelist()
                        with zf.open(zf.namelist()[0]) as f:
                            f.read(1)
                        self.register_found(target, password)
                except Exception:
                    continue

    def register_found(self, target, password):
        target_val = target["value"]
        user = target["user"]
        target_type = target["type"].upper() if target["type"] != "hash" else target["hash_type"].upper()

        with self.lock:
            if target_val not in self.found_passwords:
                self.found_passwords[target_val] = password
                elapsed = time.time() - self.start_time
                elapsed_str = str(timedelta(seconds=int(elapsed)))

                self.log_message(f"🔓 ENCONTRADA! {user} : [{password}] (Tipo: {target_type})", "success")
                self.result_queue.put((target["id"], target_val, password, target_type, elapsed_str))

                if len(self.found_passwords) >= len(self.targets):
                    self.stop_event.set()

    # ══════════════════════════════════════════════════════════
    #  ESTRUTURA DE WORKERS & CONTROLE MULTI-THREADING
    # ══════════════════════════════════════════════════════════
    def start_attack(self):
        if self.is_running:
            return
        if not self.parse_targets():
            messagebox.showerror("Erro", "Nenhuma entrada válida configurada!")
            return

        mode = self.attack_mode.get()
        if mode in ("wordlist", "rules"):
            wl = self.wordlist_path.get().strip()
            if not wl or not os.path.isfile(wl):
                messagebox.showerror("Erro", "Defina uma Wordlist válida para continuar.")
                return

        self.stop_event.clear()
        self.pause_event.set()
        self.is_running = True
        self.is_paused = False
        self.total_attempts = 0
        self.found_passwords = {}
        self.start_time = time.time()
        self.threads = []
        self.producer_done = False

        while not self.word_queue.empty():
            try: self.word_queue.get_nowait()
            except queue.Empty: break

        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.notebook.select(1)

        self.console_output.configure(state="normal")
        self.console_output.delete("1.0", tk.END)
        self.console_output.configure(state="disabled")

        self.log_message("============================================================", "info")
        self.log_message(f"🚀 Iniciando mecanismo PyCracker - Modo: {mode.upper()}", "info")
        self.log_message(f"🎯 Alvos identificados para recuperação: {len(self.targets)}", "info")
        self.log_message("============================================================", "info")

        if mode == "wordlist":
            self.init_wordlist_attack()
        elif mode == "bruteforce":
            self.init_bruteforce_attack()
        elif mode == "rules":
            self.init_rules_attack()

    def _wordlist_producer(self, wl_path):
        batch = []
        batch_size = 50000
        try:
            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if self.stop_event.is_set():
                        break
                    word = line.rstrip("\n\r")
                    if word:
                        batch.append(word)
                        if len(batch) >= batch_size:
                            self.word_queue.put(batch)
                            batch = []
                if batch and not self.stop_event.is_set():
                    self.word_queue.put(batch)
        except Exception as e:
            self.log_message(f"[!] Falha na leitura do buffer: {e}", "error")
        finally:
            self.producer_done = True

    def init_wordlist_attack(self):
        wl_path = self.wordlist_path.get().strip()

        producer = threading.Thread(target=self._wordlist_producer, args=(wl_path,), daemon=True)
        self.threads.append(producer)
        producer.start()

        for i in range(self.max_threads):
            t = threading.Thread(target=self.wordlist_worker, args=(i+1,), daemon=True)
            self.threads.append(t)
            t.start()

        threading.Thread(target=self.monitor_thread_state, daemon=True).start()

    def wordlist_worker(self, thread_id):
        processed = 0
        while not self.stop_event.is_set():
            self.pause_event.wait()
            try:
                batch = self.word_queue.get(timeout=0.5)
            except queue.Empty:
                if self.producer_done: return
                continue

            for word in batch:
                if self.stop_event.is_set(): return
                self.test_password(word)
                processed += 1
                with self.lock:
                    self.total_attempts += 1
                    current = self.total_attempts

                if processed % 10000 == 0:
                    pct = (current / self.wl_total) * 100 if self.wl_total > 0 else 0
                    self.ui_queue.put(("progress", pct, f"🔍 T{thread_id}: {word[:30]}"))

    def init_bruteforce_attack(self):
        charset = self.get_charset()
        min_len = self.min_length.get()
        max_len = self.max_length.get()
        total_est = sum(len(charset) ** l for l in range(min_len, max_len + 1))

        self.log_message(f"[*] Charset de Busca: {len(charset)} caracteres", "info")
        self.log_message(f"[*] Limites de Tamanho: {min_len} a {max_len}", "info")
        self.log_message(f"[*] Total Estimado: {total_est:,} combinações", "warning")

        for i in range(self.max_threads):
            t = threading.Thread(target=self.bruteforce_worker, args=(charset, min_len, max_len, i, total_est), daemon=True)
            self.threads.append(t)
            t.start()

        threading.Thread(target=self.monitor_thread_state, daemon=True).start()

    def bruteforce_worker(self, charset, min_len, max_len, thread_id, total):
        split_size = max(1, len(charset) // self.max_threads)
        start_i = thread_id * split_size
        my_chars = charset[start_i:] if thread_id == self.max_threads - 1 else charset[start_i:start_i+split_size]

        if not my_chars: return
        count = 0

        for r_len in range(min_len, max_len + 1):
            if self.stop_event.is_set(): return

            if r_len == 1:
                for c in my_chars:
                    self.pause_event.wait()
                    if self.stop_event.is_set(): return
                    self.test_password(c)
                    count += 1
                    with self.lock: self.total_attempts += 1
            else:
                for first in my_chars:
                    for combo in itertools.product(charset, repeat=r_len - 1):
                        self.pause_event.wait()
                        if self.stop_event.is_set(): return
                        candidate = first + "".join(combo)
                        self.test_password(candidate)
                        count += 1
                        with self.lock:
                            self.total_attempts += 1
                            current = self.total_attempts

                        if count % 10000 == 0:
                            pct = (current / total) * 100 if total > 0 else 0
                            self.ui_queue.put(("progress", pct, f"🔍 T{thread_id+1}: {candidate}"))

    def init_rules_attack(self):
        wl_path = self.wordlist_path.get().strip()
        producer = threading.Thread(target=self._wordlist_producer, args=(wl_path,), daemon=True)
        self.threads.append(producer)
        producer.start()

        for i in range(self.max_threads):
            t = threading.Thread(target=self.rules_worker, args=(i+1,), daemon=True)
            self.threads.append(t)
            t.start()

        threading.Thread(target=self.monitor_thread_state, daemon=True).start()

    def rules_worker(self, thread_id):
        processed = 0
        while not self.stop_event.is_set():
            self.pause_event.wait()
            try:
                batch = self.word_queue.get(timeout=0.5)
            except queue.Empty:
                if self.producer_done: return
                continue

            for word in batch:
                if self.stop_event.is_set(): return
                mutations = self.apply_rules(word)
                for mut in mutations:
                    if self.stop_event.is_set(): return
                    self.test_password(mut)
                    processed += 1
                    with self.lock:
                        self.total_attempts += 1
                        current = self.total_attempts

                    if processed % 15000 == 0:
                        pct = (current / (self.wl_total * 4)) * 100 if self.wl_total > 0 else 0
                        self.ui_queue.put(("progress", pct, f"🔍 T{thread_id}: {mut[:30]}"))

    def monitor_thread_state(self):
        for t in self.threads:
            t.join()

        self.is_running = False
        self.root.after(0, self.finish_execution)

    def pause_attack(self):
        if not self.is_running: return
        if self.is_paused:
            self.pause_event.set()
            self.is_paused = False
            self.btn_pause.config(text="⏸ PAUSAR", bg=self.colors["warning"])
            self.log_message("[*] Processamento retomado.", "info")
        else:
            self.pause_event.clear()
            self.is_paused = True
            self.btn_pause.config(text="▶ RETOMAR", bg="#059e07")
            self.log_message("[*] Processamento suspenso temporariamente.", "warning")

    def stop_attack(self):
        if self.is_running:
            self.stop_event.set()
            self.pause_event.set()
            self.log_message("[-] Sinalização de parada enviada às threads.", "error")

    def finish_execution(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.progress_var.set(100)
        self.lbl_progress.config(text="Finalizado")

        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸ PAUSAR", bg=self.colors["warning"])
        self.btn_stop.config(state="disabled")

        self.log_message("============================================================", "info")
        self.log_message(f"🏁 Concluído em: {str(timedelta(seconds=int(elapsed)))}", "info")
        self.log_message(f"🔢 Total de Chaves Testadas: {self.total_attempts:,}", "info")
        self.log_message(f"🔓 Alvos Resolvidos: {len(self.found_passwords)} / {len(self.targets)}", "success")
        self.log_message("============================================================", "info")

        if self.found_passwords:
            self.notebook.select(2)

    # ══════════════════════════════════════════════════════════
    #  EXPORTAÇÃO & MANUTENÇÃO DOS RESULTADOS
    # ══════════════════════════════════════════════════════════
    def export_results(self):
        if not self.found_passwords:
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo Texto", "*.txt")])
        if caminho:
            try:
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write("=== PYCRACKER RECUPERAÇÃO DE DADOS ===\n\n")
                    for k, v in self.found_passwords.items():
                        f.write(f"Alvo/Arquivo Completo: {k} | Senha Encontrada: {v}\n")
                messagebox.showinfo("Sucesso", "Exportação realizada!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    def clear_results(self):
        for c in self.results_tree.get_children():
            self.results_tree.delete(c)
        self.found_passwords.clear()

    # ══════════════════════════════════════════════════════════
    #  MÓDULOS DE ANÁLISE (IDENTIFICADOR DE HASH)
    # ══════════════════════════════════════════════════════════
    def abrir_arquivo_ident_hash(self):
        caminho = filedialog.askopenfilename(title="Abrir Hashes", filetypes=[("Arquivos Texto", "*.txt"), ("Todos", "*.*")])
        if caminho:
            try:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    self.entrada_identificar_hash.delete("1.0", tk.END)
                    self.entrada_identificar_hash.insert("1.0", f.read())
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def identificar_hashes(self):
        raw = self.entrada_identificar_hash.get("1.0", tk.END).strip().splitlines()
        self.resultado_ident_hash.delete("1.0", tk.END)
        for line in raw:
            line = line.strip()
            if not line: continue
            res, tag = detectar_hash_avancado(line)
            self.resultado_ident_hash.insert(tk.END, f"🔑 Hash: {line}\n", "info")
            self.resultado_ident_hash.insert(tk.END, f"{res}\n", tag)
            self.resultado_ident_hash.insert(tk.END, f"{'─'*50}\n", "separador")

    def salvar_ident_hash(self):
        content = self.resultado_ident_hash.get("1.0", tk.END).strip()
        if content:
            caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
            if caminho:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(content)

    def limpar_ident_hash(self):
        self.entrada_identificar_hash.delete("1.0", tk.END)
        self.resultado_ident_hash.delete("1.0", tk.END)

    # ══════════════════════════════════════════════════════════
    #  MÓDULOS DE ANÁLISE (GERADOR DE HASH)
    # ══════════════════════════════════════════════════════════
    def gerar_hash_individual(self, algo):
        text = self.entrada_gerador_texto.get("1.0", tk.END).strip()
        if not text: return
        h = self.compute_hash(text, algo)
        self.saida_gerador.delete("1.0", tk.END)
        self.saida_gerador.insert(tk.END, f"[{algo.upper()}]\n{h}\n")

    def gerar_todos_hashes(self):
        text = self.entrada_gerador_texto.get("1.0", tk.END).strip()
        if not text: return
        self.saida_gerador.delete("1.0", tk.END)
        for algo in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']:
            self.saida_gerador.insert(tk.END, f"🔹 {algo.upper()}:\n{self.compute_hash(text, algo)}\n\n")

    def salvar_hashes_gerados(self):
        content = self.saida_gerador.get("1.0", tk.END).strip()
        if content:
            caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
            if caminho:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(content)

    def limpar_gerador(self):
        self.entrada_gerador_texto.delete("1.0", tk.END)
        self.saida_gerador.delete("1.0", tk.END)

# ══════════════════════════════════════════════════════════
#  IDENTIFICAÇÃO AVANÇADA DE HASH (COM TAG DE COR)
# ══════════════════════════════════════════════════════════
def detectar_hash_avancado(hash_str):
    hash_str = hash_str.strip()
    tamanho = len(hash_str)

    if not re.match(r'^[0-9a-fA-F]+$', hash_str):
        return "❌ Formato hexadecimal de assinatura inválido.", "erro"

    if tamanho == 32:
        return "✅ MD5 (32 chars) | NTLM | MD4 | LM", "sucesso"
    elif tamanho == 40:
        return "✅ SHA-1 (40 chars) | RIPEMD-160", "sucesso"
    elif tamanho == 56:
        return "✅ SHA-224 (56 chars)", "sucesso"
    elif tamanho == 64:
        return "✅ SHA-256 (64 chars) | SHA3-256", "sucesso"
    elif tamanho == 96:
        return "✅ SHA-384 (96 chars)", "sucesso"
    elif tamanho == 128:
        return "✅ SHA-512 (128 chars) | SHA3-512", "sucesso"
    else:
        return f"❓ Assinatura desconhecida ({tamanho} caracteres hexadecimais)", "aviso"

def main():
    root = tk.Tk()
    app = PyCrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
