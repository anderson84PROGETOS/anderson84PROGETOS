#!/usr/bin/env python3

import asyncio
import os
import queue
import threading
import time as _time
import urllib.parse
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import aiohttp

# ─────────────────────────────────────────────
# PALETA DE CORES
# ─────────────────────────────────────────────
COLORS = {
    "bg_main":       "#0f1115",
    "bg_frame":      "#14171c",
    "bg_input":      "#0a0c0f",
    "fg_text":       "#d1d5db",
    "fg_muted":      "#6b7280",
    "accent_blue":   "#3b82f6",
    "accent_green":  "#10b981",
    "accent_red":    "#ef4444",
    "accent_yellow": "#fbbf24",
    "border":        "#374151",
    "tree_bg":       "#0a0c0f",
    "tree_alt":      "#111418",
    "progress_bg":   "#1e2028",
    "progress_bar":  "#3b82f6",
}

def status_color_html(code: int) -> str:
    if 200 <= code < 300: return "status-2xx"
    if 300 <= code < 400: return "status-3xx"
    if 400 <= code < 500: return "status-4xx"
    if code >= 500:       return "status-5xx"
    return ""


class WebFuzzerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"⚡ WebFuzzer")
        self.root.geometry("1200x780")
        self.root.minsize(950, 620)
        self.root.configure(bg=COLORS["bg_main"])

        self.events: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.scan_thread: threading.Thread | None = None
        self.results: list[dict] = []
        self.records: dict[str, dict] = {}
        self.next_iid = 0
        self.sort_reverse: dict[str, bool] = {}
        self.total_words = 0

        self._configure_styles()
        self._build_ui()
        self.root.after(100, self._poll_events)

    # ─────────────────────────────────────────
    # ESTILIZAÇÃO
    # ─────────────────────────────────────────
    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        font_default = ("Segoe UI", 9)
        font_bold = ("Segoe UI", 9, "bold")
        font_mono = ("Consolas", 9)

        style.configure("TFrame", background=COLORS["bg_main"])

        style.configure(
            "TLabelframe", background=COLORS["bg_frame"],
            bordercolor=COLORS["border"], lightcolor=COLORS["border"],
            darkcolor=COLORS["border"], relief="solid", borderwidth=1,
        )
        style.configure(
            "TLabelframe.Label", background=COLORS["bg_main"],
            foreground=COLORS["accent_blue"], font=("Segoe UI", 10, "bold"),
        )

        style.configure("TLabel", background=COLORS["bg_frame"],
                         foreground=COLORS["fg_text"], font=font_default)
        style.configure("Status.TLabel", background=COLORS["bg_main"],
                         foreground=COLORS["accent_green"], font=font_bold)
        style.configure("Title.TLabel", background=COLORS["bg_main"],
                         foreground=COLORS["accent_blue"], font=("Segoe UI", 12, "bold"))
        style.configure("TitleGreen.TLabel", background=COLORS["bg_main"],
                         foreground=COLORS["accent_green"], font=("Segoe UI", 10))
        style.configure("Progress.TLabel", background=COLORS["bg_main"],
                         foreground=COLORS["accent_blue"], font=font_bold)
        style.configure("Dark.TLabel", background=COLORS["bg_main"],
                         foreground=COLORS["fg_text"], font=font_default)

        style.configure(
            "TEntry", fieldbackground=COLORS["bg_input"], foreground="white",
            insertcolor="white", bordercolor=COLORS["border"],
            lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            borderwidth=1, padding=4,
        )
        style.map("TEntry",
            bordercolor=[("focus", COLORS["accent_blue"])],
            lightcolor=[("focus", COLORS["accent_blue"])],
            darkcolor=[("focus", COLORS["accent_blue"])],
        )

        style.configure(
            "TCombobox", fieldbackground=COLORS["bg_input"],
            background=COLORS["bg_frame"], foreground="white",
            bordercolor=COLORS["border"], arrowcolor="white",
            lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            borderwidth=1, padding=4,
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["bg_input"])],
            foreground=[("readonly", "white")],
            bordercolor=[("focus", COLORS["accent_blue"])],
        )

        style.configure(
            "TCheckbutton", background=COLORS["bg_frame"],
            foreground=COLORS["fg_text"], font=font_default,
            indicatorcolor=COLORS["bg_input"], indicatorrelief="solid",
        )
        style.map("TCheckbutton",
            indicatorcolor=[("selected", "white")],
            background=[("active", COLORS["bg_frame"])],
        )

        style.configure(
            "TButton", background=COLORS["bg_input"], foreground=COLORS["fg_text"],
            bordercolor=COLORS["border"], lightcolor=COLORS["border"],
            darkcolor=COLORS["border"], borderwidth=1, focuscolor="none", padding=(8, 4),
        )
        style.map("TButton", background=[("active", COLORS["border"])])

        style.configure(
            "Start.TButton", background="#16a34a", foreground="white",
            bordercolor="#15803d", lightcolor="#15803d", darkcolor="#15803d", font=font_default,
        )
        style.map("Start.TButton",
            background=[("active", "#15803d"), ("disabled", COLORS["bg_frame"])],
            foreground=[("disabled", COLORS["fg_muted"])],
        )

        style.configure(
            "Stop.TButton", background=COLORS["bg_input"], foreground=COLORS["accent_red"],
            bordercolor=COLORS["accent_red"], lightcolor=COLORS["accent_red"],
            darkcolor=COLORS["accent_red"], font=font_default,
        )
        style.map("Stop.TButton",
            background=[("active", "#450a0a"), ("disabled", COLORS["bg_frame"])],
            bordercolor=[("disabled", COLORS["border"])],
            foreground=[("disabled", COLORS["fg_muted"])],
            lightcolor=[("disabled", COLORS["border"])],
            darkcolor=[("disabled", COLORS["border"])],
        )

        style.configure(
            "Export.TButton", background="#2563eb", foreground="white",
            bordercolor="#1d4ed8", lightcolor="#1d4ed8", darkcolor="#1d4ed8", font=font_default,
        )
        style.map("Export.TButton", background=[("active", "#1d4ed8")])

        style.configure(
            "Treeview", background=COLORS["tree_bg"], fieldbackground=COLORS["tree_bg"],
            foreground=COLORS["fg_text"], bordercolor=COLORS["border"],
            borderwidth=1, rowheight=24, font=font_mono,
        )
        style.configure(
            "Treeview.Heading", background=COLORS["bg_main"],
            foreground=COLORS["accent_blue"], bordercolor=COLORS["border"],
            relief="flat", font=font_bold,
        )
        style.map("Treeview",
            background=[("selected", COLORS["border"])],
            foreground=[("selected", "white")],
        )
        style.map("Treeview.Heading", background=[("active", COLORS["bg_frame"])])

        style.configure(
            "Vertical.TScrollbar", background=COLORS["border"],
            troughcolor=COLORS["bg_main"], bordercolor=COLORS["bg_main"],
            arrowcolor="white", width=12,
        )

        # Notebook (Abas)
        style.configure("TNotebook", background=COLORS["bg_main"],
                         bordercolor=COLORS["border"])
        style.configure(
            "TNotebook.Tab", background=COLORS["bg_frame"],
            foreground=COLORS["fg_muted"], padding=(12, 6),
            font=font_bold, bordercolor=COLORS["border"],
        )
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["bg_main"])],
            foreground=[("selected", COLORS["accent_blue"])],
        )

        # Barra de progresso
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=COLORS["progress_bg"],
            background=COLORS["progress_bar"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["progress_bar"],
            darkcolor="#2563eb",
            thickness=22,
        )

    # ─────────────────────────────────────────
    # CONSTRUÇÃO DA INTERFACE
    # ─────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=COLORS["bg_main"])
        header.pack(fill="x", padx=10, pady=(8, 0))
        ttk.Label(header, text="⚡ WebFuzzer", style="Title.TLabel").pack(side="left")       

        # ── Configuração ──
        config = ttk.LabelFrame(self.root, text=" ⚙ Configuração ")
        config.pack(fill="x", padx=10, pady=10)
        config.columnconfigure(1, weight=1)

        # URL
        ttk.Label(config, text="URL (use FUZZ):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.url_entry = ttk.Entry(config)
        self.url_entry.grid(row=0, column=1, columnspan=5, sticky="ew", padx=5, pady=5)
        self.url_entry.insert(0, "http://exemplo.com.br/FUZZ")

        # Wordlist
        ttk.Label(config, text="Wordlist:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.wordlist_entry = ttk.Entry(config)
        self.wordlist_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Button(config, text="📁 Procurar", command=self._browse_wordlist).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(config, text="Método:").grid(row=1, column=4, sticky="e", padx=5, pady=5)
        self.method_var = tk.StringVar(value="GET")
        ttk.Combobox(config, textvariable=self.method_var,
                     values=("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"),
                     state="readonly", width=8).grid(row=1, column=5, sticky="w", padx=5, pady=5)

        # Threads + Timeout
        ttk.Label(config, text="Threads:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.threads_entry = ttk.Entry(config)
        self.threads_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.threads_entry.insert(0, "5")

        ttk.Label(config, text="Timeout (s):").grid(row=2, column=4, sticky="e", padx=5, pady=5)
        self.timeout_entry = ttk.Entry(config)
        self.timeout_entry.grid(row=2, column=5, sticky="w", padx=5, pady=5)
        self.timeout_entry.insert(0, "10")

        # Keyword + Filtrar
        ttk.Label(config, text="Keyword:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.keyword_entry = ttk.Entry(config)
        self.keyword_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.keyword_entry.insert(0, "FUZZ")

        ttk.Label(config, text="Filtrar status:").grid(row=3, column=4, sticky="e", padx=5, pady=5)
        self.filter_entry = ttk.Entry(config)
        self.filter_entry.grid(row=3, column=5, sticky="w", padx=5, pady=5)
        self.filter_entry.insert(0, "200,301")

        # Dados + Template
        ttk.Label(config, text="Dados (opcional):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.data_entry = ttk.Entry(config)
        self.data_entry.grid(row=4, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        self.data_entry.insert(0, "username=admin&password=FUZZ")

        ttk.Label(config, text="Template:").grid(row=4, column=4, sticky="e", padx=5, pady=5)
        self.data_template_var = tk.StringVar(value="Login Form")
        template_combo = ttk.Combobox(
            config, textvariable=self.data_template_var,
            values=("Login Form", "Login Email", "JSON Login", "JSON Search",
                    "SQL Injection", "XSS Payload", "Register User",
                    "API Key", "Upload File", "Limpar"),
            state="readonly", width=15,
        )
        template_combo.grid(row=4, column=5, sticky="w", padx=5, pady=5)
        template_combo.bind("<<ComboboxSelected>>", self._apply_data_template)

        # SSL
        self.verify_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config, text="Verificar SSL", variable=self.verify_ssl_var)\
            .grid(row=5, column=1, sticky="w", padx=8, pady=(0, 8))

        # ── Barra de Progresso ──
        progress_frame = tk.Frame(self.root, bg=COLORS["bg_main"])
        progress_frame.pack(fill="x", padx=10, pady=(0, 5))

        progress_header = tk.Frame(progress_frame, bg=COLORS["bg_main"])
        progress_header.pack(fill="x")
        ttk.Label(progress_header, text="📊 Progresso:", style="Dark.TLabel").pack(side="left")
        self.progress_pct_label = ttk.Label(progress_header, text="0%", style="Progress.TLabel")
        self.progress_pct_label.pack(side="left", padx=(8, 0))
        self.progress_detail_label = ttk.Label(progress_header, text="0 / 0 palavras",
                                                style="Dark.TLabel")
        self.progress_detail_label.pack(side="right")

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var,
            maximum=100, mode="determinate",
            style="Custom.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(4, 0))

        # ── Controles ──
        controls = tk.Frame(self.root, bg=COLORS["bg_main"])
        controls.pack(fill="x", padx=10, pady=(5, 8))

        self.start_button = ttk.Button(controls, text="▶ Iniciar", style="Start.TButton",
                                       command=self._start_scan, width=12)
        self.start_button.pack(side="left", padx=(0, 10))

        self.stop_button = ttk.Button(controls, text="■ Parar", style="Stop.TButton",
                                      command=self._stop_scan, state="disabled", width=12)
        self.stop_button.pack(side="left", padx=(0, 10))

        ttk.Button(controls, text="💾 Exportar HTML", style="Export.TButton",
                   command=self._export_html, width=16).pack(side="left", padx=(0, 10))

        ttk.Button(controls, text="🗑 Limpar Tudo", command=self._clear_all,
                   width=14).pack(side="left")

        self.status_label = ttk.Label(controls, text="● Pronto", style="Status.TLabel")
        self.status_label.pack(side="right")

        # ── Notebook (Abas) ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ─── Aba 1: Resultados ───
        tab_results = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.notebook.add(tab_results, text="  📋 Resultados  ")

        tree_frame = tk.Frame(tab_results, bg=COLORS["border"], bd=1)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)

        columns = ("input", "status", "size", "words", "time", "url")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        headings = {
            "input": "➤ Entrada", "status": "Status", "size": "Bytes",
            "words": "Words", "time": "Tempo", "url": "URL Completa",
        }
        widths = {"input": 140, "status": 70, "size": 90, "words": 70, "time": 90, "url": 500}

        for col in columns:
            self.tree.heading(col, text=headings[col],
                              command=lambda c=col: self._sort_tree(c))
            self.tree.column(col, width=widths[col], anchor="w")

        self.tree.tag_configure("s2xx", foreground=COLORS["accent_green"])
        self.tree.tag_configure("s3xx", foreground=COLORS["accent_blue"])
        self.tree.tag_configure("s4xx", foreground=COLORS["accent_yellow"])
        self.tree.tag_configure("s5xx", foreground=COLORS["accent_red"])
        self.tree.tag_configure("row_even", background=COLORS["tree_bg"])
        self.tree.tag_configure("row_odd", background=COLORS["tree_alt"])

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Evento de seleção na tabela
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # ─── Aba 2: Detalhes HTTP (Cabeçalhos + Body) ───
        tab_details = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.notebook.add(tab_details, text="  🔍 Detalhes HTTP  ")

        # Painel dividido: Request | Response
        details_paned = tk.PanedWindow(tab_details, orient="horizontal",
                                        bg=COLORS["border"], sashwidth=4,
                                        sashrelief="flat")
        details_paned.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Request ──
        req_frame = tk.Frame(details_paned, bg=COLORS["bg_main"])
        details_paned.add(req_frame, minsize=300)

        req_title = tk.Frame(req_frame, bg=COLORS["bg_frame"])
        req_title.pack(fill="x")
        tk.Label(req_title, text="  📤 REQUEST", bg=COLORS["bg_frame"],
                 fg=COLORS["accent_blue"], font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=6)

        # Request Headers
        tk.Label(req_frame, text="Headers da Requisição:", bg=COLORS["bg_main"],
                 fg=COLORS["fg_text"], font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(8, 2))

        self.req_headers_text = tk.Text(
            req_frame, bg=COLORS["bg_input"], fg="#22d3ee",
            font=("Consolas", 9), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word", height=8,
        )
        self.req_headers_text.pack(fill="x", padx=8, pady=(0, 4))

        # Request Body / Dados POST
        tk.Label(req_frame, text="Body / Dados Enviados:", bg=COLORS["bg_main"],
                 fg=COLORS["fg_text"], font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(4, 2))

        self.req_body_text = tk.Text(
            req_frame, bg=COLORS["bg_input"], fg=COLORS["accent_yellow"],
            font=("Consolas", 9), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word", height=6,
        )
        self.req_body_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Response ──
        resp_frame = tk.Frame(details_paned, bg=COLORS["bg_main"])
        details_paned.add(resp_frame, minsize=300)

        resp_title = tk.Frame(resp_frame, bg=COLORS["bg_frame"])
        resp_title.pack(fill="x")
        tk.Label(resp_title, text="  📥 RESPONSE", bg=COLORS["bg_frame"],
                 fg=COLORS["accent_green"], font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=6)

        # Response Status
        self.resp_status_label = tk.Label(
            resp_frame, text="Status: —", bg=COLORS["bg_main"],
            fg=COLORS["accent_green"], font=("Segoe UI", 11, "bold"), anchor="w",
        )
        self.resp_status_label.pack(fill="x", padx=8, pady=(8, 4))

        # Response Headers
        tk.Label(resp_frame, text="Headers da Resposta:", bg=COLORS["bg_main"],
                 fg=COLORS["fg_text"], font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(4, 2))

        self.resp_headers_text = tk.Text(
            resp_frame, bg=COLORS["bg_input"], fg="#a78bfa",
            font=("Consolas", 9), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word", height=8,
        )
        self.resp_headers_text.pack(fill="x", padx=8, pady=(0, 4))

        # Response Body Preview
        tk.Label(resp_frame, text="Body (preview):", bg=COLORS["bg_main"],
                 fg=COLORS["fg_text"], font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(4, 2))

        self.resp_body_text = tk.Text(
            resp_frame, bg=COLORS["bg_input"], fg=COLORS["fg_text"],
            font=("Consolas", 9), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word", height=6,
        )
        self.resp_body_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ─── Aba 3: Formulário POST ───
        tab_form = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.notebook.add(tab_form, text="  📝 Formulário POST  ")

        form_top = tk.Frame(tab_form, bg=COLORS["bg_frame"])
        form_top.pack(fill="x", padx=4, pady=4)
        tk.Label(form_top, text="  📝 Dados do Formulário / POST Body",
                 bg=COLORS["bg_frame"], fg=COLORS["accent_blue"],
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=8, pady=6)

        # Tabela de parâmetros do formulário
        form_tree_frame = tk.Frame(tab_form, bg=COLORS["border"], bd=1)
        form_tree_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.form_tree = ttk.Treeview(
            form_tree_frame, columns=("param", "value"), show="headings",
        )
        self.form_tree.heading("param", text="Parâmetro")
        self.form_tree.heading("value", text="Valor")
        self.form_tree.column("param", width=250, anchor="w")
        self.form_tree.column("value", width=500, anchor="w")

        form_scroll = ttk.Scrollbar(form_tree_frame, orient="vertical",
                                     command=self.form_tree.yview)
        self.form_tree.configure(yscrollcommand=form_scroll.set)
        self.form_tree.pack(side="left", fill="both", expand=True)
        form_scroll.pack(side="right", fill="y")

        # Dados brutos
        tk.Label(tab_form, text="  Dados Brutos (Raw):", bg=COLORS["bg_main"],
                 fg=COLORS["fg_text"], font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(4, 2))

        self.form_raw_text = tk.Text(
            tab_form, bg=COLORS["bg_input"], fg=COLORS["accent_yellow"],
            font=("Consolas", 10), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word", height=5,
        )
        self.form_raw_text.pack(fill="x", padx=8, pady=(0, 8))

        # ─── Aba 4: Estatísticas ───
        tab_stats = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.notebook.add(tab_stats, text="  📊 Estatísticas  ")

        self.stats_text = tk.Text(
            tab_stats, bg=COLORS["bg_input"], fg=COLORS["fg_text"],
            font=("Consolas", 11), insertbackground="white",
            relief="solid", bd=1, highlightbackground=COLORS["border"],
            highlightthickness=1, wrap="word",
        )
        self.stats_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.stats_text.insert("1.0", "  Inicie um scan para ver as estatísticas...")
        self.stats_text.config(state="disabled")

    # ─────────────────────────────────────────
    # AÇÕES
    # ─────────────────────────────────────────
    def _browse_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecionar wordlist",
            filetypes=(("Texto", "*.txt"), ("Todos", "*.*")),
        )
        if path:
            self.wordlist_entry.delete(0, "end")
            self.wordlist_entry.insert(0, path)

    def _apply_data_template(self, event=None):
        templates = {
            "Login Form":    "username=admin&password=FUZZ",
            "Login Email":   "email=admin@test.com&password=FUZZ",
            "JSON Login":    '{"username":"admin","password":"FUZZ"}',
            "JSON Search":   '{"query":"FUZZ","limit":10}',
            "SQL Injection": "id=FUZZ' OR '1'='1",
            "XSS Payload":   "search=<script>FUZZ</script>",
            "Register User": "username=FUZZ&email=FUZZ@test.com&password=123456",
            "API Key":       "api_key=FUZZ&action=verify",
            "Upload File":   "filename=FUZZ.txt&content=test",
            "Limpar":        "",
        }
        template = self.data_template_var.get()
        if template in templates:
            self.data_entry.delete(0, "end")
            self.data_entry.insert(0, templates[template])
            if template in ("Login Form", "Login Email", "JSON Login", "JSON Search",
                            "Register User", "API Key", "Upload File"):
                self.method_var.set("POST")
            elif template in ("SQL Injection", "XSS Payload"):
                self.method_var.set("GET")

    def _clear_all(self):
        self.results.clear()
        self.records.clear()
        self.next_iid = 0
        self.total_words = 0
        self.tree.delete(*self.tree.get_children())
        self.progress_var.set(0)
        self.progress_pct_label.config(text="0%")
        self.progress_detail_label.config(text="0 / 0 palavras")
        self._clear_detail_panels()
        self._update_stats_tab({})
        self.status_label.config(text="● Pronto", foreground=COLORS["accent_green"])

    def _clear_detail_panels(self):
        for widget in (self.req_headers_text, self.req_body_text,
                       self.resp_headers_text, self.resp_body_text, self.form_raw_text):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")
        self.resp_status_label.config(text="Status: —", fg=COLORS["fg_muted"])
        self.form_tree.delete(*self.form_tree.get_children())

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        record = self.records.get(iid)
        if not record:
            return
        self._populate_details(record)
        self._populate_form_tab(record)

    def _populate_details(self, record: dict):
        # Request Headers
        req_headers = record.get("req_headers_str", "")
        self.req_headers_text.config(state="normal")
        self.req_headers_text.delete("1.0", "end")
        self.req_headers_text.insert("1.0", req_headers if req_headers else "(sem cabeçalhos)")
        self.req_headers_text.config(state="disabled")

        # Request Body
        req_body = record.get("req_body", "")
        self.req_body_text.config(state="normal")
        self.req_body_text.delete("1.0", "end")
        self.req_body_text.insert("1.0", req_body if req_body else "(sem body / GET request)")
        self.req_body_text.config(state="disabled")

        # Response Status
        status = record.get("status", 0)
        color = COLORS["fg_text"]
        if 200 <= status < 300:   color = COLORS["accent_green"]
        elif 300 <= status < 400: color = COLORS["accent_blue"]
        elif 400 <= status < 500: color = COLORS["accent_yellow"]
        elif status >= 500:       color = COLORS["accent_red"]
        self.resp_status_label.config(text=f"Status: {status}", fg=color)

        # Response Headers
        resp_headers = record.get("resp_headers_str", "")
        self.resp_headers_text.config(state="normal")
        self.resp_headers_text.delete("1.0", "end")
        self.resp_headers_text.insert("1.0", resp_headers if resp_headers else "(sem cabeçalhos)")
        self.resp_headers_text.config(state="disabled")

        # Response Body
        resp_body = record.get("resp_body_preview", "")
        self.resp_body_text.config(state="normal")
        self.resp_body_text.delete("1.0", "end")
        self.resp_body_text.insert("1.0", resp_body if resp_body else "(sem body)")
        self.resp_body_text.config(state="disabled")

        # Muda para a aba de detalhes
        self.notebook.select(1)

    def _populate_form_tab(self, record: dict):
        self.form_tree.delete(*self.form_tree.get_children())
        self.form_raw_text.config(state="normal")
        self.form_raw_text.delete("1.0", "end")

        req_body = record.get("req_body", "")
        if not req_body:
            self.form_raw_text.insert("1.0", "(Sem dados POST enviados)")
            self.form_raw_text.config(state="disabled")
            return

        self.form_raw_text.insert("1.0", req_body)
        self.form_raw_text.config(state="disabled")

        # Tenta parsear como form-urlencoded
        if req_body.strip().startswith("{"):
            # JSON
            try:
                import json
                data = json.loads(req_body)
                if isinstance(data, dict):
                    for k, v in data.items():
                        self.form_tree.insert("", "end", values=(k, str(v)))
                return
            except Exception:
                pass

        # form-urlencoded
        try:
            params = urllib.parse.parse_qs(req_body, keep_blank_values=True)
            for k, vals in params.items():
                for v in vals:
                    self.form_tree.insert("", "end", values=(k, v))
        except Exception:
            self.form_tree.insert("", "end", values=("(raw)", req_body))

    def _update_stats_tab(self, stats: dict):
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")

        if not stats and not self.results:
            self.stats_text.insert("1.0", "  Inicie um scan para ver as estatísticas...")
            self.stats_text.config(state="disabled")
            return

        total = len(self.results)
        c2 = sum(1 for r in self.results if 200 <= r["status"] < 300)
        c3 = sum(1 for r in self.results if 300 <= r["status"] < 400)
        c4 = sum(1 for r in self.results if 400 <= r["status"] < 500)
        c5 = sum(1 for r in self.results if r["status"] >= 500)
        avg_time = (sum(r["time"] for r in self.results) / total * 1000) if total else 0
        avg_size = (sum(r["size"] for r in self.results) / total) if total else 0
        total_bytes = sum(r["size"] for r in self.results)

        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║         ⚡ WebFuzzer  — Estatísticas             ║",
            "╠══════════════════════════════════════════════════╣",
            f"║  📋 Total de resultados:      {total:>8}            ║",
            f"║  📦 Palavras processadas:     {stats.get('completed', total):>8}            ║",
            f"║  ❌ Erros de conexão:         {stats.get('failed', 0):>8}            ║",
            f"║  🔇 Filtrados (ocultos):      {stats.get('filtered', 0):>8}            ║",
            "╠══════════════════════════════════════════════════╣",
            "║  Status HTTP:                                    ║",
            f"║    ✅ 2xx (Sucesso):          {c2:>8}            ║",
            f"║    🔀 3xx (Redirect):         {c3:>8}            ║",
            f"║    ⚠️  4xx (Erro Cliente):     {c4:>8}            ║",
            f"║    🔥 5xx (Erro Servidor):    {c5:>8}            ║",
            "╠══════════════════════════════════════════════════╣",
            "║  Performance:                                    ║",
            f"║    ⏱  Tempo médio:         {avg_time:>8.0f} ms          ║",
            f"║    📊 Tamanho médio:       {avg_size:>8.0f} bytes       ║",
            f"║    💾 Total transferido:   {total_bytes:>8,} bytes       ║",
            "╚══════════════════════════════════════════════════╝",
        ]

        self.stats_text.insert("1.0", "\n".join(lines))
        self.stats_text.config(state="disabled")

    # ─────────────────────────────────────────
    # SCAN
    # ─────────────────────────────────────────
    def _start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return

        url = self.url_entry.get().strip()
        wordlist = self.wordlist_entry.get().strip()
        keyword = self.keyword_entry.get().strip() or "FUZZ"
        data = self.data_entry.get().strip()

        try:
            threads = int(self.threads_entry.get())
            timeout = float(self.timeout_entry.get())
            if not 1 <= threads <= 200:
                raise ValueError("Threads: 1‑200")
            if timeout <= 0:
                raise ValueError("Timeout > 0")
        except ValueError as exc:
            messagebox.showerror("Config inválida", str(exc))
            return

        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showerror("URL inválida", "URL HTTP/HTTPS válida é necessária.")
            return

        if not os.path.isfile(wordlist):
            messagebox.showerror("Erro", "Arquivo de Wordlist não encontrado.")
            return

        try:
            ft = self.filter_entry.get().strip()
            filter_status = {int(v.strip()) for v in ft.split(",") if v.strip()} if ft else set()
        except ValueError:
            messagebox.showerror("Filtro", "Códigos de status devem ser separados por vírgula.")
            return

        self.results.clear()
        self.records.clear()
        self.next_iid = 0
        self.tree.delete(*self.tree.get_children())
        self.stop_event.clear()
        self.progress_var.set(0)
        self.progress_pct_label.config(text="0%")
        self.progress_detail_label.config(text="0 / 0 palavras")
        self._clear_detail_panels()

        cfg = {
            "url": url, "wordlist": wordlist, "keyword": keyword,
            "data": data, "method": self.method_var.get(),
            "threads": threads, "timeout": timeout,
            "filter_status": filter_status, "verify_ssl": self.verify_ssl_var.get(),
        }

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="● Iniciando…", foreground=COLORS["accent_blue"])
        self.notebook.select(0)

        self.scan_thread = threading.Thread(target=self._run_thread, args=(cfg,), daemon=True)
        self.scan_thread.start()

    def _stop_scan(self):
        self.stop_event.set()
        self.status_label.config(text="● Parando…", foreground=COLORS["accent_red"])

    def _run_thread(self, cfg):
        try:
            asyncio.run(self._scan(cfg))
        except Exception as exc:
            self.events.put(("fatal_error", str(exc)))
        finally:
            self.events.put(("finished",))

    async def _scan(self, cfg):
        words = []
        try:
            with open(cfg["wordlist"], "r", encoding="utf-8", errors="ignore") as fh:
                words = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
        except OSError as exc:
            self.events.put(("fatal_error", f"Leitura da wordlist: {exc}"))
            return

        total = len(words)
        self.events.put(("started", total))
        if not words:
            return

        wq = asyncio.Queue()
        for w in words:
            wq.put_nowait(w)

        timeout = aiohttp.ClientTimeout(total=cfg["timeout"])
        connector = aiohttp.TCPConnector(limit=cfg["threads"])
        stats = {"completed": 0, "found": 0, "failed": 0, "filtered": 0}

        # ── Headers customizados da sessão ──
        session_headers = {}
        is_json = cfg["data"].strip().startswith("{") and cfg["data"].strip().endswith("}")
        if is_json:
            session_headers["Content-Type"] = "application/json"

        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=session_headers,
        ) as session:

            async def worker():
                while not self.stop_event.is_set():
                    try:
                        word = wq.get_nowait()
                    except asyncio.QueueEmpty:
                        return

                    url = cfg["url"].replace(
                        cfg["keyword"], urllib.parse.quote(word, safe="")
                    )
                    req_data = (
                        cfg["data"].replace(cfg["keyword"], word)
                        if cfg["data"]
                        else None
                    )

                    # ── Monta string legível dos headers da REQUEST ──
                    parsed_url = urllib.parse.urlsplit(url)
                    host = parsed_url.netloc
                    req_h_lines = [
                        f"{cfg['method']} {parsed_url.path or '/'}"
                        + (f"?{parsed_url.query}" if parsed_url.query else "")
                        + f" HTTP/1.1",
                        f"Host: {host}",
                    ]
                    for k, v in session_headers.items():
                        req_h_lines.append(f"{k}: {v}")
                    if req_data:
                        req_h_lines.append(
                            f"Content-Length: {len(req_data.encode('utf-8'))}"
                        )
                    req_headers_str = "\n".join(req_h_lines)

                    t0 = _time.perf_counter()
                    try:
                        kwargs = {
                            "allow_redirects": False,
                            "ssl": cfg["verify_ssl"],
                        }
                        # Sempre enviar como bytes UTF-8 (evita erro de encoding)
                        if req_data:
                            kwargs["data"] = req_data.encode("utf-8")

                        async with session.request(
                            cfg["method"], url, **kwargs
                        ) as resp:
                            body = await resp.read()
                            elapsed = _time.perf_counter() - t0
                            body_text = body.decode("utf-8", errors="replace")

                            # ── Cabeçalhos da RESPONSE (seguro contra None) ──
                            ver_major = getattr(resp.version, "major", 1)
                            ver_minor = getattr(resp.version, "minor", 1)
                            reason = resp.reason or ""
                            resp_h_lines = [
                                f"HTTP/{ver_major}.{ver_minor}"
                                f" {resp.status} {reason}".rstrip()
                            ]
                            for k, v in resp.headers.items():
                                resp_h_lines.append(f"{k}: {v}")
                            resp_headers_str = "\n".join(resp_h_lines)

                            result = {
                                "input": word,
                                "url": url,
                                "status": resp.status,
                                "size": len(body),
                                "time": elapsed,
                                "content_type": resp.headers.get(
                                    "Content-Type", ""
                                ),
                                "redirect": resp.headers.get("Location", ""),
                                "words": len(body_text.split()),
                                "req_headers_str": req_headers_str,
                                "req_body": req_data or "",
                                "resp_headers_str": resp_headers_str,
                                "resp_body_preview": body_text[:2000],
                            }

                            if (
                                not cfg["filter_status"]
                                or resp.status in cfg["filter_status"]
                            ):
                                stats["found"] += 1
                                self.events.put(("result", result))
                            else:
                                stats["filtered"] += 1

                    except asyncio.TimeoutError:
                        stats["failed"] += 1
                    except aiohttp.ClientError:
                        stats["failed"] += 1
                    except Exception:
                        stats["failed"] += 1
                    finally:
                        stats["completed"] += 1
                        if (
                            stats["completed"] % 5 == 0
                            or stats["completed"] == total
                        ):
                            self.events.put(
                                ("progress", stats["completed"], total)
                            )

            await asyncio.gather(
                *[
                    asyncio.create_task(worker())
                    for _ in range(min(cfg["threads"], total))
                ]
            )

        self.events.put(("stats", dict(stats)))

    # ─────────────────────────────────────────
    # EVENT LOOP
    # ─────────────────────────────────────────
    def _poll_events(self):
        try:
            while True:
                ev = self.events.get_nowait()
                self._handle(ev)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _handle(self, ev):
        kind = ev[0]
        if kind == "started":
            self.total_words = ev[1]
            self.status_label.config(text=f"● Processando {ev[1]} palavras…",
                                     foreground=COLORS["accent_blue"])
        elif kind == "progress":
            completed, total = ev[1], ev[2]
            pct = (completed / total * 100) if total else 0
            self.progress_var.set(pct)
            self.progress_pct_label.config(text=f"{pct:.1f}%")
            self.progress_detail_label.config(text=f"{completed:,} / {total:,} palavras")
            self.status_label.config(text=f"● {completed:,}/{total:,}",
                                     foreground=COLORS["accent_blue"])
        elif kind == "result":
            self._add_result(ev[1])
        elif kind == "fatal_error":
            messagebox.showerror("Erro", ev[1])
        elif kind == "finished":
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            if self.stop_event.is_set():
                self.status_label.config(text="● Interrompido", foreground=COLORS["accent_red"])
        elif kind == "stats":
            s = ev[1]
            self.progress_var.set(100)
            self.progress_pct_label.config(text="100%")
            self.status_label.config(
                text=f"● Concluído — {s['found']} encontrados | {s['failed']} erros | {s['filtered']} filtrados",
                foreground=COLORS["accent_green"],
            )
            self._update_stats_tab(s)

    def _add_result(self, result: dict):
        self.results.append(result)
        iid = str(self.next_iid)
        self.next_iid += 1
        self.records[iid] = result

        tag = "s5xx"
        if 200 <= result["status"] < 300:   tag = "s2xx"
        elif 300 <= result["status"] < 400: tag = "s3xx"
        elif 400 <= result["status"] < 500: tag = "s4xx"

        parity = "row_even" if self.next_iid % 2 == 0 else "row_odd"

        self.tree.insert("", "end", iid=iid, values=(
            result["input"], result["status"], f'{result["size"]:,}',
            f'{result.get("words", 0):,}', f'{result["time"] * 1000:.0f} ms',
            result["url"],
        ), tags=(tag, parity))

    def _sort_tree(self, column: str):
        rev = self.sort_reverse.get(column, False)
        items = list(self.tree.get_children(""))

        def key(iid):
            r = self.records[iid]
            if column in ("status", "size", "time", "words"):
                return r.get(column, 0)
            return r.get(column, "").casefold()

        items.sort(key=key, reverse=rev)
        for i, iid in enumerate(items):
            self.tree.move(iid, "", i)
        self.sort_reverse[column] = not rev

    # ─────────────────────────────────────────
    # EXPORTAÇÃO HTML
    # ─────────────────────────────────────────
    def _export_html(self):
        if not self.results:
            messagebox.showinfo("Aviso", "Sem resultados para exportar.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile=f"webfuzzer_{datetime.now():%Y%m%d_%H%M%S}.html",
            filetypes=(("HTML", "*.html"),),
        )
        if not path:
            return

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        total = len(self.results)
        c2 = sum(1 for r in self.results if 200 <= r["status"] < 300)
        c3 = sum(1 for r in self.results if 300 <= r["status"] < 400)
        c4 = sum(1 for r in self.results if 400 <= r["status"] < 500)
        c5 = sum(1 for r in self.results if r["status"] >= 500)
        avg_time = (sum(r["time"] for r in self.results) / total * 1000) if total else 0

        rows_html = ""
        for r in self.results:
            resp_h = self._esc(r.get("resp_headers_str", "")).replace("\n", "<br>")
            req_body = self._esc(r.get("req_body", ""))
            rows_html += f"""
            <tr class="result-row" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'table-row':'none'">
                <td>{self._esc(r['input'])}</td>
                <td class="{status_color_html(r['status'])}">{r['status']}</td>
                <td>{r['size']:,}</td>
                <td>{r.get('words',0):,}</td>
                <td>{r['time']*1000:.0f} ms</td>
                <td>{self._esc(r.get('content_type',''))}</td>
                <td class="url-cell"><a href="{self._esc(r['url'])}" target="_blank">{self._esc(r['url'])}</a></td>
            </tr>
            <tr class="detail-row" style="display:none">
                <td colspan="7">
                    <div class="detail-grid">
                        <div class="detail-box">
                            <h4>📤 Request Body</h4>
                            <pre>{req_body if req_body else '(sem body)'}</pre>
                        </div>
                        <div class="detail-box">
                            <h4>📥 Response Headers</h4>
                            <pre>{resp_h}</pre>
                        </div>
                    </div>
                </td>
            </tr>"""

        html = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<title>Relatório WebFuzzer</title>
<style>
    :root {{ --bg:#0d1117; --card:#161b22; --fg:#e6edf3; --border:#30363d;
             --blue:#58a6ff; --green:#3fb950; --orange:#d29922; --red:#f85149; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--fg); padding: 24px; }}
    .container {{ max-width: 1400px; margin: auto; }}
    .header {{ background: var(--card); padding: 24px; border: 1px solid var(--border);
               border-radius: 10px; margin-bottom: 24px; border-left: 5px solid var(--blue); }}
    .header h2 {{ margin-bottom: 8px; }}
    .header p {{ color: #8b949e; }}
    .stats {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 24px; }}
    .stat {{ background: var(--card); padding: 18px 12px; text-align: center;
             border: 1px solid var(--border); border-radius: 10px; }}
    .stat .num {{ font-size: 28px; font-weight: bold; }}
    .stat .lbl {{ display: block; font-size: 11px; color: #8b949e; text-transform: uppercase; margin-top: 4px; }}
    .progress-bar {{ background: #21262d; border-radius: 8px; overflow: hidden; height: 28px;
                     margin-bottom: 24px; border: 1px solid var(--border); position: relative; }}
    .progress-fill {{ background: linear-gradient(90deg, #2563eb, #3b82f6, #60a5fa);
                      height: 100%; border-radius: 8px; transition: width 0.3s; }}
    .progress-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                      font-weight: bold; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--card);
             border-radius: 10px; overflow: hidden; }}
    th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }}
    th {{ background: #21262d; color: var(--blue); position: sticky; top: 0; font-size: 12px; }}
    .result-row {{ cursor: pointer; transition: background 0.15s; }}
    .result-row:hover {{ background: #21262d; }}
    .detail-row td {{ background: #0d1117; padding: 16px; }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .detail-box {{ background: var(--card); border: 1px solid var(--border);
                   border-radius: 8px; padding: 14px; }}
    .detail-box h4 {{ color: var(--blue); margin-bottom: 8px; font-size: 13px; }}
    .detail-box pre {{ font-family: Consolas, monospace; font-size: 12px; color: #8b949e;
                       white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow: auto; }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .status-2xx {{ color: var(--green); font-weight: bold; }}
    .status-3xx {{ color: var(--blue); font-weight: bold; }}
    .status-4xx {{ color: var(--orange); font-weight: bold; }}
    .status-5xx {{ color: var(--red); font-weight: bold; }}
    .footer {{ text-align: center; color: #484f58; margin-top: 32px; font-size: 12px; }}
</style></head><body>
<div class="container">
    <div class="header">
        <h2>⚡ WebFuzzer — Relatório</h2>
        <p>📅 Gerado em {now} &nbsp;|&nbsp; 🎯 URL: {self._esc(self.url_entry.get())}</p>
    </div>
    <div class="stats">
        <div class="stat"><div class="num">{total}</div><span class="lbl">Total</span></div>
        <div class="stat"><div class="num status-2xx">{c2}</div><span class="lbl">2xx Sucesso</span></div>
        <div class="stat"><div class="num status-3xx">{c3}</div><span class="lbl">3xx Redirect</span></div>
        <div class="stat"><div class="num status-4xx">{c4}</div><span class="lbl">4xx Erro</span></div>
        <div class="stat"><div class="num status-5xx">{c5}</div><span class="lbl">5xx Server</span></div>
        <div class="stat"><div class="num" style="color:var(--blue)">{avg_time:.0f}ms</div><span class="lbl">Tempo Médio</span></div>
    </div>
    <div class="progress-bar">
        <div class="progress-fill" style="width:100%"></div>
        <div class="progress-text">100% Concluído</div>
    </div>
    <table>
        <thead>
            <tr><th>Entrada</th><th>Status</th><th>Bytes</th><th>Words</th><th>Tempo</th><th>Content-Type</th><th>URL</th></tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    <p class="footer">WebFuzzer — Relatório gerado automaticamente &nbsp;|&nbsp; 🔒 Uso autorizado apenas</p>
</div></body></html>"""

        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(html)
            messagebox.showinfo("Sucesso", f"HTML salvo em:\n{path}")
        except OSError as exc:
            messagebox.showerror("Erro", str(exc))

    @staticmethod
    def _esc(t: str) -> str:
        return (t.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def main():
    root = tk.Tk()
    WebFuzzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
