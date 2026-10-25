#!/usr/bin/env python3
"""
Network Sniffer GUI - Analisador de Tráfego de Rede Avançado
Captura e filtra pacotes HTTP, HTTPS, DNS, Cookies, Forms, Login, etc.
Requer privilégios de root/administrador.
Inicia automaticamente a captura na interface eth0.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import subprocess
import signal
import os
import re
import json
import datetime
import sys
import html as html_module
from collections import defaultdict


class NetworkSnifferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Sniffer Network - Analisador de Tráfego de Rede")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a2e")
        self.root.minsize(1000, 600)

        # Variáveis de controle
        self.is_capturing = False
        self.tcpdump_process = None
        self.capture_thread = None
        self.packet_count = 0
        self.filtered_count = 0
        self.all_packets = []
        self.stats = defaultdict(int)

        # Armazenar dados estruturados para HTML
        self.captured_credentials = []
        self.captured_cookies = []
        self.captured_dns = []
        self.captured_http_requests = []
        self.captured_auth_tokens = []
        self.capture_start_time = None
        self.capture_end_time = None

        # Janela de configurações (criada sob demanda)
        self.config_window = None

        # Estilo
        self.setup_styles()

        # Inicializar variáveis de filtros ANTES de criar widgets
        self.init_filter_vars()

        # Interface
        self.create_widgets()
        # Verificar root
        self.check_privileges()

    def init_filter_vars(self):
        """Inicializa todas as variáveis de filtros."""
        # Interface
        self.interface_var = tk.StringVar(value="eth0")

        # Filtros de protocolo
        self.filter_vars = {}
        filters_list = [
            ("http", True), ("https", False), ("dns", False),
            ("ftp", False), ("smtp", False), ("pop3", False),
            ("imap", False), ("ssh", False), ("telnet", False),
            ("mysql", False), ("pgsql", False),
        ]
        for key, default in filters_list:
            self.filter_vars[key] = tk.BooleanVar(value=default)

        # Filtros HTTP
        self.http_filter_vars = {}
        http_filters = [
            ("post", True), ("get", False), ("login", True),
            ("cookie", True), ("form", True), ("json_data", True),
            ("auth", True), ("setcookie", True), ("content_type", False),
            ("user_agent", False), ("referer", False),
        ]
        for key, default in http_filters:
            self.http_filter_vars[key] = tk.BooleanVar(value=default)

        # Filtros TLS
        self.tls_filter_vars = {}
        tls_filters = [
            ("sni", False), ("client_hello", False), ("certs", False),
        ]
        for key, default in tls_filters:
            self.tls_filter_vars[key] = tk.BooleanVar(value=default)

        # Entradas (StringVars)
        self.domain_filter_var = tk.StringVar(value="")
        self.ip_filter_var = tk.StringVar(value="")
        self.port_filter_var = tk.StringVar(value="")
        self.search_filter_var = tk.StringVar(value="")
        self.keywords_var = (
            "password,passwd,pass,pwd,senha,login,user,username,"
            "usuario,email,token,session,cookie,auth,credit,card,"
            "cpf,cnpj,secret,api_key"
        )

        # Opções
        self.verbose_var = tk.BooleanVar(value=True)
        self.resolve_var = tk.BooleanVar(value=False)
        self.packet_limit_var = tk.StringVar(value="0")

    def setup_styles(self):
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'accent2': '#00d2ff',
            'text': '#ffffff',
            'text_dim': '#a0a0b0',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'error': '#ff4444',
            'http_post': '#ff6b6b',
            'http_get': '#51cf66',
            'https': '#ffd43b',
            'dns': '#748ffc',
            'cookie': '#f783ac',
            'form': '#da77f2',
            'login': '#ff8787',
            'credential': '#ff0000',
        }

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background=self.colors['bg_dark'])
        style.configure('Medium.TFrame', background=self.colors['bg_medium'])
        style.configure('Dark.TLabel', background=self.colors['bg_dark'],
                        foreground=self.colors['text'], font=('Consolas', 10))
        style.configure('Title.TLabel', background=self.colors['bg_dark'],
                        foreground=self.colors['accent'],
                        font=('Consolas', 16, 'bold'))
        style.configure('Dark.TNotebook',
                        background=self.colors['bg_dark'])
        style.configure('Dark.TNotebook.Tab',
                        background=self.colors['bg_medium'],
                        foreground=self.colors['text'],
                        font=('Consolas', 10, 'bold'), padding=[15, 8])

    def create_widgets(self):
        # ===================== HEADER =====================
        header_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], pady=8)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame, text="🔍 NETWORK SNIFFER",
                 font=('Consolas', 20, 'bold'), fg=self.colors['accent'],
                 bg=self.colors['bg_dark']).pack(side=tk.LEFT, padx=15)

        tk.Label(header_frame,
                 text="Analisador de Tráfego de Rede Avançado",
                 font=('Consolas', 10), fg=self.colors['text_dim'],
                 bg=self.colors['bg_dark']).pack(side=tk.LEFT, padx=5)

        self.status_indicator = tk.Label(
            header_frame, text="⬤ PARADO",
            font=('Consolas', 12, 'bold'),
            fg=self.colors['error'],
            bg=self.colors['bg_dark'])
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ===================== BARRA DE CONTROLES (TOPO) =====================
        toolbar = tk.Frame(self.root, bg=self.colors['bg_medium'], pady=8)
        toolbar.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Interface selector (compacto no toolbar)
        tk.Label(toolbar, text="📡 Interface:",
                 bg=self.colors['bg_medium'],
                 fg=self.colors['accent2'],
                 font=('Consolas', 9, 'bold')).pack(side=tk.LEFT, padx=(10, 5))

        interfaces = self.get_interfaces()
        if "eth0" not in interfaces:
            interfaces.insert(0, "eth0")
        self.iface_combo = ttk.Combobox(
            toolbar, textvariable=self.interface_var,
            values=interfaces, width=15, state='readonly')
        self.iface_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="🔄",
                  command=self.refresh_interfaces,
                  bg=self.colors['bg_light'], fg=self.colors['text'],
                  font=('Consolas', 9), relief=tk.FLAT,
                  width=3, cursor='hand2').pack(side=tk.LEFT, padx=2)

        # Separador
        tk.Frame(toolbar, bg=self.colors['bg_light'],
                 width=2, height=30).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Botão Configurações
        tk.Button(toolbar, text="CONFIGURAÇÕES / FILTROS",
                  command=self.open_config_window,
                  bg=self.colors['accent2'], fg='black',
                  font=('Consolas', 9, 'bold'),
                  relief=tk.FLAT, cursor='hand2',
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        # Separador
        tk.Frame(toolbar, bg=self.colors['bg_light'],
                 width=2, height=30).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Botões de controle
        self.start_btn = tk.Button(
            toolbar, text="▶  INICIAR CAPTURA",
            command=self.start_capture,
            bg=self.colors['success'], fg='black',
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT, cursor='hand2',
            padx=15, pady=5)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            toolbar, text="⏹  PARAR",
            command=self.stop_capture,
            bg=self.colors['error'], fg='white',
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT, cursor='hand2',
            state=tk.DISABLED, padx=15, pady=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Separador
        tk.Frame(toolbar, bg=self.colors['bg_light'],
                 width=2, height=30).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        tk.Button(toolbar, text="🗑️  Limpar",
                  command=self.clear_output,
                  bg=self.colors['bg_light'], fg=self.colors['text'],
                  font=('Consolas', 9), relief=tk.FLAT,
                  cursor='hand2', padx=10, pady=5).pack(side=tk.LEFT, padx=3)

        tk.Button(toolbar, text="💾  Salvar HTML",
                  command=self.save_capture_html,
                  bg='#e94560', fg='white',
                  font=('Consolas', 9, 'bold'), relief=tk.FLAT,
                  cursor='hand2', padx=10, pady=5).pack(side=tk.LEFT, padx=3)

        tk.Button(toolbar, text="📊  Stats",
                  command=self.show_stats,
                  bg=self.colors['bg_light'], fg=self.colors['text'],
                  font=('Consolas', 9), relief=tk.FLAT,
                  cursor='hand2', padx=10, pady=5).pack(side=tk.LEFT, padx=3)

        # ===================== ÁREA PRINCIPAL (NOTEBOOK OCUPANDO TUDO) =====================
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(main_frame, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab: Tráfego ao Vivo ---
        live_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(live_frame, text="📡 Tráfego ao Vivo")

        self.live_output = scrolledtext.ScrolledText(
            live_frame, bg='#0d1117', fg=self.colors['text'],
            font=('Consolas', 10), relief=tk.FLAT, wrap=tk.WORD,
            insertbackground=self.colors['text'])
        self.live_output.pack(fill=tk.BOTH, expand=True)

        # Tags de cores
        tags_config = {
            'http_post': {'foreground': self.colors['http_post'],
                          'font': ('Consolas', 10, 'bold')},
            'http_get': {'foreground': self.colors['http_get']},
            'https': {'foreground': self.colors['https']},
            'dns': {'foreground': self.colors['dns']},
            'cookie': {'foreground': self.colors['cookie']},
            'form': {'foreground': self.colors['form']},
            'login': {'foreground': self.colors['login'],
                      'font': ('Consolas', 11, 'bold')},
            'credential': {'foreground': self.colors['credential'],
                           'font': ('Consolas', 11, 'bold'),
                           'background': '#3d0000'},
            'separator': {'foreground': self.colors['text_dim']},
            'header': {'foreground': self.colors['accent2']},
            'timestamp': {'foreground': self.colors['text_dim']},
            'warning': {'foreground': self.colors['warning'],
                        'font': ('Consolas', 10, 'bold')},
            'info': {'foreground': self.colors['accent2']},
            'sni': {'foreground': '#ffd43b',
                    'font': ('Consolas', 10, 'bold')},
            'raw': {'foreground': '#6c757d'},
        }
        for tag, config in tags_config.items():
            self.live_output.tag_configure(tag, **config)

        # --- Tab: Credenciais ---
        cred_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(cred_frame, text="🔑 Credenciais")

        self.cred_output = scrolledtext.ScrolledText(
            cred_frame, bg='#1a0000', fg=self.colors['credential'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cred_output.pack(fill=tk.BOTH, expand=True)
        self.cred_output.tag_configure(
            'alert', foreground='#ff0000',
            font=('Consolas', 13, 'bold'))
        self.cred_output.tag_configure(
            'data', foreground='#ff8888')

        # --- Tab: Cookies ---
        cookie_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(cookie_frame, text="🍪 Cookies")

        self.cookie_output = scrolledtext.ScrolledText(
            cookie_frame, bg='#1a0a15', fg=self.colors['cookie'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cookie_output.pack(fill=tk.BOTH, expand=True)

        # --- Tab: DNS/SNI ---
        dns_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(dns_frame, text="🌍 DNS/SNI")

        self.dns_output = scrolledtext.ScrolledText(
            dns_frame, bg='#0a0a1a', fg=self.colors['dns'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.dns_output.pack(fill=tk.BOTH, expand=True)

        # --- Tab: Raw Data ---
        raw_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(raw_frame, text="📝 Raw Data")

        self.raw_output = scrolledtext.ScrolledText(
            raw_frame, bg='#0d1117', fg='#8b949e',
            font=('Consolas', 10), relief=tk.FLAT, wrap=tk.WORD)
        self.raw_output.pack(fill=tk.BOTH, expand=True)

        # --- Tab: Comando ---
        cmd_frame = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(cmd_frame, text="⌨️ Comando")

        self.cmd_output = scrolledtext.ScrolledText(
            cmd_frame, bg='#0d1117', fg=self.colors['success'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cmd_output.pack(fill=tk.BOTH, expand=True)

        # ===================== BARRA DE STATUS =====================
        status_frame = tk.Frame(self.root, bg=self.colors['bg_medium'],
                                height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame, text="Pronto. Configure os filtros e inicie a captura.",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Consolas', 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.packet_count_label = tk.Label(
            status_frame, text="Pacotes: 0",
            bg=self.colors['bg_medium'],
            fg=self.colors['accent2'],
            font=('Consolas', 10, 'bold'))
        self.packet_count_label.pack(side=tk.RIGHT, padx=10)

        self.filtered_count_label = tk.Label(
            status_frame, text="Filtrados: 0",
            bg=self.colors['bg_medium'],
            fg=self.colors['warning'],
            font=('Consolas', 10, 'bold'))
        self.filtered_count_label.pack(side=tk.RIGHT, padx=10)

        self.cred_count_label = tk.Label(
            status_frame, text="🔑 Credenciais: 0",
            bg=self.colors['bg_medium'],
            fg=self.colors['error'],
            font=('Consolas', 10, 'bold'))
        self.cred_count_label.pack(side=tk.RIGHT, padx=10)

    # ========================================================================
    # JANELA DE CONFIGURAÇÕES (MODAL)
    # ========================================================================
    def open_config_window(self):
        """Abre a janela de configurações/filtros."""
        if self.config_window is not None and self.config_window.winfo_exists():
            self.config_window.lift()
            self.config_window.focus_force()
            return

        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("⚙️ Configurações e Filtros")
        self.config_window.geometry("520x750")
        self.config_window.configure(bg=self.colors['bg_dark'])
        self.config_window.minsize(480, 600)

        # Header
        header = tk.Frame(self.config_window, bg=self.colors['bg_medium'], pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="⚙️ CONFIGURAÇÕES E FILTROS",
                 font=('Consolas', 14, 'bold'),
                 fg=self.colors['accent'],
                 bg=self.colors['bg_medium']).pack(side=tk.LEFT, padx=15)
        tk.Button(header, text="✖ Fechar",
                  command=self.config_window.destroy,
                  bg=self.colors['error'], fg='white',
                  font=('Consolas', 9, 'bold'), relief=tk.FLAT,
                  cursor='hand2', padx=10).pack(side=tk.RIGHT, padx=15)

        # Container com scroll
        container = tk.Frame(self.config_window, bg=self.colors['bg_dark'])
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=self.colors['bg_dark'],
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL,
                                   command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['bg_dark'])

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw",
                              width=490)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll com mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.config_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._close_config(canvas))

        # --- Filtros de Protocolo ---
        self.create_section_label(scrollable, "🔧 FILTROS DE PROTOCOLO")
        proto_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        proto_frame.pack(fill=tk.X, padx=15, pady=2)

        filters_list = [
            ("HTTP (porta 80)", "http"),
            ("HTTPS/TLS (porta 443)", "https"),
            ("DNS (porta 53)", "dns"),
            ("FTP (porta 21)", "ftp"),
            ("SMTP (porta 25/587)", "smtp"),
            ("POP3 (porta 110)", "pop3"),
            ("IMAP (porta 143)", "imap"),
            ("SSH (porta 22)", "ssh"),
            ("Telnet (porta 23)", "telnet"),
            ("MySQL (porta 3306)", "mysql"),
            ("PostgreSQL (porta 5432)", "pgsql"),
        ]

        for text, key in filters_list:
            cb = tk.Checkbutton(
                proto_frame, text=text, variable=self.filter_vars[key],
                bg=self.colors['bg_dark'], fg=self.colors['text'],
                selectcolor=self.colors['bg_medium'],
                activebackground=self.colors['bg_dark'],
                activeforeground=self.colors['accent2'],
                font=('Consolas', 10))
            cb.pack(anchor=tk.W, pady=1)

        # --- Filtros HTTP Avançados ---
        self.create_section_label(scrollable, "🌐 FILTROS HTTP AVANÇADOS")
        http_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        http_frame.pack(fill=tk.X, padx=15, pady=2)

        http_filters = [
            ("POST Requests (Formulários)", "post"),
            ("GET Requests", "get"),
            ("Login/Senha (Credenciais)", "login"),
            ("Cookies", "cookie"),
            ("Form Data (urlencoded)", "form"),
            ("JSON Data", "json_data"),
            ("Authorization Headers", "auth"),
            ("Set-Cookie (Respostas)", "setcookie"),
            ("Content-Type", "content_type"),
            ("User-Agent", "user_agent"),
            ("Referer", "referer"),
        ]

        for text, key in http_filters:
            cb = tk.Checkbutton(
                http_frame, text=text, variable=self.http_filter_vars[key],
                bg=self.colors['bg_dark'], fg=self.colors['accent2'],
                selectcolor=self.colors['bg_medium'],
                activebackground=self.colors['bg_dark'],
                activeforeground=self.colors['accent'],
                font=('Consolas', 10))
            cb.pack(anchor=tk.W, pady=1)

        # --- Filtros TLS/SNI ---
        self.create_section_label(scrollable, "🔒 FILTROS TLS/HTTPS")
        tls_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        tls_frame.pack(fill=tk.X, padx=15, pady=2)

        tls_filters = [
            ("TLS Handshake (SNI)", "sni"),
            ("TLS Client Hello", "client_hello"),
            ("Certificados", "certs"),
        ]

        for text, key in tls_filters:
            cb = tk.Checkbutton(
                tls_frame, text=text, variable=self.tls_filter_vars[key],
                bg=self.colors['bg_dark'], fg=self.colors['https'],
                selectcolor=self.colors['bg_medium'],
                activebackground=self.colors['bg_dark'],
                font=('Consolas', 10))
            cb.pack(anchor=tk.W, pady=1)

        # --- Filtro por Domínio/Host ---
        self.create_section_label(scrollable, "🎯 FILTRO POR DOMÍNIO/HOST")
        domain_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        domain_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(domain_frame, text="Domínio (ex: exemplo.com.br):",
                 bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
                 font=('Consolas', 9)).pack(anchor=tk.W)
        tk.Entry(domain_frame, textvariable=self.domain_filter_var,
                 bg=self.colors['bg_medium'], fg=self.colors['text'],
                 insertbackground=self.colors['text'],
                 font=('Consolas', 10), relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # --- Filtro por IP ---
        self.create_section_label(scrollable, "🖥️ FILTRO POR IP")
        ip_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        ip_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(ip_frame, text="IP de origem/destino:",
                 bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
                 font=('Consolas', 9)).pack(anchor=tk.W)
        tk.Entry(ip_frame, textvariable=self.ip_filter_var,
                 bg=self.colors['bg_medium'], fg=self.colors['text'],
                 insertbackground=self.colors['text'],
                 font=('Consolas', 10), relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # --- Porta Customizada ---
        self.create_section_label(scrollable, "🔌 PORTA CUSTOMIZADA")
        port_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        port_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(port_frame, text="Portas (ex: 8080,8443,3000):",
                 bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
                 font=('Consolas', 9)).pack(anchor=tk.W)
        tk.Entry(port_frame, textvariable=self.port_filter_var,
                 bg=self.colors['bg_medium'], fg=self.colors['text'],
                 insertbackground=self.colors['text'],
                 font=('Consolas', 10), relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # --- Busca no Conteúdo ---
        self.create_section_label(scrollable, "🔎 BUSCA NO CONTEÚDO")
        search_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        search_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(search_frame, text="Termo de busca:",
                 bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
                 font=('Consolas', 9)).pack(anchor=tk.W)
        tk.Entry(search_frame, textvariable=self.search_filter_var,
                 bg=self.colors['bg_medium'], fg=self.colors['text'],
                 insertbackground=self.colors['text'],
                 font=('Consolas', 10), relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # --- Palavras-chave sensíveis ---
        self.create_section_label(scrollable, "⚠️ PALAVRAS-CHAVE SENSÍVEIS")
        keywords_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        keywords_frame.pack(fill=tk.X, padx=15, pady=2)

        self.keywords_text = tk.Text(
            keywords_frame, height=4,
            bg=self.colors['bg_medium'],
            fg=self.colors['warning'],
            insertbackground=self.colors['text'],
            font=('Consolas', 9), relief=tk.FLAT, wrap=tk.WORD)
        self.keywords_text.pack(fill=tk.X, pady=2)
        self.keywords_text.insert("1.0", self.keywords_var)

        # --- Opções de Captura ---
        self.create_section_label(scrollable, "⚙️ OPÇÕES DE CAPTURA")
        opts_frame = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        opts_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Checkbutton(
            opts_frame, text="Modo Verboso (payload completo)",
            variable=self.verbose_var,
            bg=self.colors['bg_dark'], fg=self.colors['text'],
            selectcolor=self.colors['bg_medium'],
            font=('Consolas', 10)).pack(anchor=tk.W)

        tk.Checkbutton(
            opts_frame, text="Resolver DNS (mais lento)",
            variable=self.resolve_var,
            bg=self.colors['bg_dark'], fg=self.colors['text'],
            selectcolor=self.colors['bg_medium'],
            font=('Consolas', 10)).pack(anchor=tk.W)

        tk.Label(opts_frame,
                 text="Limite de pacotes (0 = ilimitado):",
                 bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
                 font=('Consolas', 9)).pack(anchor=tk.W, pady=(5, 0))
        tk.Entry(opts_frame, textvariable=self.packet_limit_var,
                 bg=self.colors['bg_medium'], fg=self.colors['text'],
                 insertbackground=self.colors['text'],
                 font=('Consolas', 10), relief=tk.FLAT,
                 width=15).pack(anchor=tk.W, pady=2)

        # Botão aplicar/fechar
        btn_apply = tk.Frame(scrollable, bg=self.colors['bg_dark'])
        btn_apply.pack(fill=tk.X, padx=15, pady=20)

        tk.Button(btn_apply, text="✅ APLICAR E FECHAR",
                  command=lambda: self._apply_and_close(canvas),
                  bg=self.colors['success'], fg='black',
                  font=('Consolas', 11, 'bold'),
                  relief=tk.FLAT, cursor='hand2',
                  pady=10).pack(fill=tk.X)

    def _close_config(self, canvas):
        """Fecha a janela de configurações."""
        try:
            self.keywords_var = self.keywords_text.get("1.0", tk.END).strip()
        except Exception:
            pass
        canvas.unbind_all("<MouseWheel>")
        self.config_window.destroy()
        self.config_window = None

    def _apply_and_close(self, canvas):
        """Aplica configurações e fecha."""
        self._close_config(canvas)
        self.status_label.config(text="✅ Configurações aplicadas com sucesso.")

    def create_section_label(self, parent, text):
        frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.X, padx=10, pady=(12, 2))
        tk.Label(frame, text=text, bg=self.colors['bg_dark'],
                 fg=self.colors['accent'],
                 font=('Consolas', 10, 'bold')).pack(anchor=tk.W)
        tk.Frame(frame, bg=self.colors['accent'],
                 height=1).pack(fill=tk.X, pady=2)

    def check_privileges(self):
        if os.geteuid() != 0:
            self.log_live(
                "⚠️  AVISO: Este programa precisa ser executado "
                "como ROOT!\n", 'warning')
            self.log_live(
                "   Execute: sudo python3 sniffer.py\n\n", 'info')

    def get_interfaces(self):
        interfaces = []
        try:
            result = subprocess.run(
                ['ip', 'link', 'show'],
                capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                match = re.match(r'^\d+:\s+(\S+):', line)
                if match:
                    iface = match.group(1)
                    if iface != 'lo':
                        interfaces.append(iface)
        except Exception:
            try:
                for iface in os.listdir('/sys/class/net/'):
                    if iface != 'lo':
                        interfaces.append(iface)
            except Exception:
                pass
        if not interfaces:
            interfaces = ["eth0"]
        return interfaces

    def refresh_interfaces(self):
        interfaces = self.get_interfaces()
        self.iface_combo['values'] = interfaces
        self.log_live(
            f"🔄 Interfaces atualizadas: {', '.join(interfaces)}\n",
            'info')

    def build_tcpdump_command(self):
        cmd = ['tcpdump']
        iface = self.interface_var.get()
        if iface:
            cmd.extend(['-i', iface])

        if self.verbose_var.get():
            cmd.append('-A')
        if not self.resolve_var.get():
            cmd.append('-n')

        cmd.extend(['-l', '-s', '0', '-tttt'])

        try:
            limit = int(self.packet_limit_var.get())
            if limit > 0:
                cmd.extend(['-c', str(limit)])
        except ValueError:
            pass

        bpf_parts = []
        port_filters = []
        port_map = {
            'http': '80', 'https': '443', 'dns': '53',
            'ftp': '21', 'smtp': '25 or port 587',
            'pop3': '110', 'imap': '143', 'ssh': '22',
            'telnet': '23', 'mysql': '3306', 'pgsql': '5432',
        }

        for key, var in self.filter_vars.items():
            if var.get() and key in port_map:
                port_val = port_map[key]
                if 'or' in port_val:
                    port_filters.append(f'(port {port_val})')
                else:
                    port_filters.append(f'port {port_val}')

        custom_ports = self.port_filter_var.get().strip()
        if custom_ports:
            for port in custom_ports.split(','):
                port = port.strip()
                if port.isdigit():
                    port_filters.append(f'port {port}')

        if port_filters:
            bpf_parts.append('(' + ' or '.join(port_filters) + ')')

        ip_filter = self.ip_filter_var.get().strip()
        if ip_filter:
            bpf_parts.append(f'(host {ip_filter})')

        if bpf_parts:
            cmd.append(' and '.join(bpf_parts))

        return cmd

    def start_capture(self):
        if self.is_capturing:
            return

        self.capture_start_time = datetime.datetime.now()
        cmd = self.build_tcpdump_command()
        cmd_str = ' '.join(cmd)

        self.cmd_output.delete("1.0", tk.END)
        self.cmd_output.insert(tk.END,
                               f"Comando executado:\n\n{cmd_str}\n\n")
        self.cmd_output.insert(tk.END, "=" * 60 + "\n\n")
        self.cmd_output.insert(tk.END,
                               "Filtros ativos (análise de conteúdo):\n\n")

        for key, var in self.http_filter_vars.items():
            status = "✅" if var.get() else "❌"
            self.cmd_output.insert(tk.END, f"  {status} HTTP/{key}\n")
        for key, var in self.tls_filter_vars.items():
            status = "✅" if var.get() else "❌"
            self.cmd_output.insert(tk.END, f"  {status} TLS/{key}\n")

        domain = self.domain_filter_var.get().strip()
        if domain:
            self.cmd_output.insert(
                tk.END, f"\n  🎯 Domínio filtrado: {domain}\n")

        search = self.search_filter_var.get().strip()
        if search:
            self.cmd_output.insert(tk.END, f"  🔎 Busca: {search}\n")

        self.is_capturing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_indicator.config(text="⬤ CAPTURANDO",
                                      fg=self.colors['success'])
        self.status_label.config(text="Capturando pacotes...")

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_live("\n" + "=" * 70 + "\n", 'separator')
        self.log_live(f"🚀 CAPTURA INICIADA - {now}\n", 'warning')
        self.log_live(
            f"   Interface: {self.interface_var.get()}\n", 'info')
        self.log_live("=" * 70 + "\n\n", 'separator')

        self.capture_thread = threading.Thread(
            target=self.capture_packets, args=(cmd,), daemon=True)
        self.capture_thread.start()

    def capture_packets(self, cmd):
        try:
            self.tcpdump_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, preexec_fn=os.setsid)

            current_packet = []

            for line in iter(self.tcpdump_process.stdout.readline, ''):
                if not self.is_capturing:
                    break

                if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
                            line):
                    if current_packet:
                        self.process_packet('\n'.join(current_packet))
                    current_packet = [line.rstrip()]
                else:
                    current_packet.append(line.rstrip())

            if current_packet:
                self.process_packet('\n'.join(current_packet))

        except Exception as e:
            self.root.after(0, lambda: self.log_live(
                f"\n❌ ERRO: {str(e)}\n", 'credential'))
        finally:
            self.root.after(0, self.capture_stopped)

    def process_packet(self, packet_data):
        self.packet_count += 1
        self.root.after(0, lambda: self.packet_count_label.config(
            text=f"Pacotes: {self.packet_count}"))

        self.all_packets.append(packet_data)
        self.root.after(0, lambda pd=packet_data:
                        self.raw_output.insert(
                            tk.END, pd + "\n" + "-" * 50 + "\n"))

        data_lower = packet_data.lower()

        domain = self.domain_filter_var.get().strip().lower()
        if domain and domain not in data_lower:
            return

        search = self.search_filter_var.get().strip().lower()
        if search and search not in data_lower:
            return

        is_http = False

        # POST
        if self.http_filter_vars.get('post', tk.BooleanVar()).get():
            if 'POST ' in packet_data:
                is_http = True
                self.stats['POST'] += 1
                host = self._extract_field(packet_data, r'Host:\s*(\S+)')
                uri = self._extract_field(packet_data, r'POST\s+(\S+)')
                ct = self._extract_field(
                    packet_data, r'Content-Type:\s*(.+)')
                self.captured_http_requests.append({
                    'time': datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'method': 'POST',
                    'host': host or 'N/A',
                    'uri': uri or 'N/A',
                    'content_type': ct or 'N/A',
                    'raw': packet_data[:2000]
                })
                self.root.after(0, lambda pd=packet_data:
                                self.log_post(pd))

        # GET
        if self.http_filter_vars.get('get', tk.BooleanVar()).get():
            if 'GET ' in packet_data and 'POST ' not in packet_data:
                is_http = True
                self.stats['GET'] += 1
                host = self._extract_field(packet_data, r'Host:\s*(\S+)')
                uri = self._extract_field(packet_data, r'GET\s+(\S+)')
                self.captured_http_requests.append({
                    'time': datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'method': 'GET',
                    'host': host or 'N/A',
                    'uri': uri or 'N/A',
                    'content_type': 'N/A',
                    'raw': packet_data[:2000]
                })
                self.root.after(0, lambda pd=packet_data:
                                self.log_get(pd))

        # Cookies
        if self.http_filter_vars.get('cookie', tk.BooleanVar()).get():
            cookie_match = re.search(
                r'Cookie:\s*(.+)', packet_data, re.IGNORECASE)
            if cookie_match:
                is_http = True
                self.stats['Cookies'] += 1
                host = self._extract_field(
                    packet_data, r'Host:\s*(\S+)')
                self.captured_cookies.append({
                    'time': datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'type': 'Cookie',
                    'host': host or 'N/A',
                    'value': cookie_match.group(1).strip()[:500]
                })
                self.root.after(
                    0,
                    lambda cm=cookie_match, pd=packet_data:
                        self.log_cookie(cm.group(1), pd))

        # Set-Cookie
        if self.http_filter_vars.get('setcookie', tk.BooleanVar()).get():
            setcookie_match = re.search(
                r'Set-Cookie:\s*(.+)', packet_data, re.IGNORECASE)
            if setcookie_match:
                is_http = True
                self.stats['Set-Cookies'] += 1
                self.captured_cookies.append({
                    'time': datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'type': 'Set-Cookie',
                    'host': 'N/A',
                    'value': setcookie_match.group(1).strip()[:500]
                })
                self.root.after(
                    0,
                    lambda sc=setcookie_match.group(1):
                        self.log_setcookie(sc))

        # Form Data
        if self.http_filter_vars.get('form', tk.BooleanVar()).get():
            if 'application/x-www-form-urlencoded' in data_lower:
                is_http = True
                self.stats['Form Data'] += 1
                self.root.after(0, lambda pd=packet_data:
                                self.log_form(pd))

        # JSON
        if self.http_filter_vars.get('json_data', tk.BooleanVar()).get():
            if ('application/json' in data_lower
                    or 'content-type: application/json' in data_lower):
                is_http = True
                self.stats['JSON'] += 1
                self.root.after(0, lambda pd=packet_data:
                                self.log_json(pd))

        # Authorization
        if self.http_filter_vars.get('auth', tk.BooleanVar()).get():
            auth_match = re.search(
                r'Authorization:\s*(.+)', packet_data, re.IGNORECASE)
            if auth_match:
                is_http = True
                self.stats['Auth Headers'] += 1
                self.captured_auth_tokens.append({
                    'time': datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'value': auth_match.group(1).strip()[:500],
                    'host': self._extract_field(
                        packet_data, r'Host:\s*(\S+)') or 'N/A'
                })
                self.root.after(
                    0,
                    lambda am=auth_match.group(1):
                        self.log_auth(am))

        # User-Agent
        if self.http_filter_vars.get('user_agent', tk.BooleanVar()).get():
            ua_match = re.search(
                r'User-Agent:\s*(.+)', packet_data, re.IGNORECASE)
            if ua_match:
                is_http = True

        # Referer
        if self.http_filter_vars.get('referer', tk.BooleanVar()).get():
            ref_match = re.search(
                r'Referer:\s*(.+)', packet_data, re.IGNORECASE)
            if ref_match:
                is_http = True

        # Credenciais
        if self.http_filter_vars.get('login', tk.BooleanVar()).get():
            # Pegar keywords (da janela de config ou da variável salva)
            try:
                if (self.config_window is not None
                        and self.config_window.winfo_exists()):
                    keywords_raw = self.keywords_text.get("1.0", tk.END).strip()
                else:
                    keywords_raw = self.keywords_var
            except Exception:
                keywords_raw = self.keywords_var

            keywords = [k.strip().lower() for k in keywords_raw.split(',')
                        if k.strip()]

            for keyword in keywords:
                if keyword in data_lower:
                    patterns = [
                        rf'{keyword}[=:]\s*([^\s&"\'<>]+)',
                        rf'"{keyword}"\s*:\s*"([^"]+)"',
                        rf'{keyword}\s*=\s*([^\s&]+)',
                    ]
                    for pattern in patterns:
                        match = re.search(
                            pattern, packet_data, re.IGNORECASE)
                        if match:
                            is_http = True
                            self.stats['Credentials'] += 1
                            host = self._extract_field(
                                packet_data, r'Host:\s*(\S+)')
                            uri = self._extract_field(
                                packet_data,
                                r'(?:POST|GET)\s+(\S+)')
                            self.captured_credentials.append({
                                'time': datetime.datetime.now().strftime(
                                    '%Y-%m-%d %H:%M:%S'),
                                'field': keyword,
                                'value': match.group(1)[:200],
                                'host': host or 'N/A',
                                'uri': uri or 'N/A',
                                'raw': packet_data[:1000]
                            })
                            self.root.after(
                                0,
                                lambda k=keyword,
                                       v=match.group(1),
                                       pd=packet_data:
                                    self.log_credential(k, v, pd))
                            break

        # TLS/SNI
        if self.tls_filter_vars.get('sni', tk.BooleanVar()).get():
            if '.443' in packet_data or 'https' in data_lower:
                domain_matches = re.findall(
                    r'([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?'
                    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]*'
                    r'[a-zA-Z0-9])?)*\.[a-zA-Z]{2,})',
                    packet_data)
                for d in domain_matches:
                    if len(d) > 5 and '.' in d:
                        self.stats['SNI/DNS'] += 1
                        self.captured_dns.append({
                            'time': datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'),
                            'type': 'TLS SNI',
                            'query': d
                        })
                        self.root.after(
                            0,
                            lambda dn=d, pd=packet_data:
                                self.log_sni(dn, pd))
                        break

        # DNS
        if self.filter_vars.get('dns', tk.BooleanVar()).get():
            if ('.53' in packet_data
                    or ' A?' in packet_data
                    or ' AAAA?' in packet_data):
                dns_match = re.search(
                    r'(?:A\?|AAAA\?|PTR\?)\s+(\S+)', packet_data)
                if dns_match:
                    self.stats['DNS'] += 1
                    self.captured_dns.append({
                        'time': datetime.datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S'),
                        'type': 'DNS Query',
                        'query': dns_match.group(1)
                    })
                    self.root.after(
                        0,
                        lambda dm=dns_match.group(1),
                               pd=packet_data:
                            self.log_dns(dm, pd))

        if is_http:
            self.filtered_count += 1
            self.root.after(0, lambda: self.filtered_count_label.config(
                text=f"Filtrados: {self.filtered_count}"))

    def _extract_field(self, data, pattern):
        match = re.search(pattern, data, re.IGNORECASE)
        return match.group(1).strip() if match else None

    # ==================== FUNÇÕES DE LOG ====================

    def log_live(self, text, tag=None):
        self.live_output.insert(tk.END, text, tag)
        self.live_output.see(tk.END)

    def log_post(self, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n{'─' * 60}\n", 'separator')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live("🔴 HTTP POST REQUEST\n", 'http_post')

        uri_match = re.search(r'POST\s+(\S+)', data)
        if uri_match:
            self.log_live(
                f"   URI: {uri_match.group(1)}\n", 'http_post')

        host_match = re.search(
            r'Host:\s*(\S+)', data, re.IGNORECASE)
        if host_match:
            self.log_live(
                f"   Host: {host_match.group(1)}\n", 'header')

        ct_match = re.search(
            r'Content-Type:\s*(.+)', data, re.IGNORECASE)
        if ct_match:
            self.log_live(
                f"   Content-Type: {ct_match.group(1).strip()}\n",
                'info')

        if self.verbose_var.get():
            lines = data.split('\n')
            payload_started = False
            for line in lines:
                if not line.strip() and not payload_started:
                    payload_started = True
                    continue
                if payload_started and line.strip():
                    self.log_live(
                        f"   📦 Payload: {line.strip()}\n", 'form')

    def log_get(self, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live("🟢 HTTP GET ", 'http_get')

        uri_match = re.search(r'GET\s+(\S+)', data)
        if uri_match:
            uri = uri_match.group(1)
            self.log_live(f"{uri}\n", 'http_get')
            if '?' in uri:
                params = uri.split('?', 1)[1]
                self.log_live(f"   Params: {params}\n", 'info')

        host_match = re.search(
            r'Host:\s*(\S+)', data, re.IGNORECASE)
        if host_match:
            self.log_live(
                f"   Host: {host_match.group(1)}\n", 'header')

    def log_cookie(self, cookie_data, packet_data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n[{timestamp}] ", 'timestamp')
        self.log_live(
            f"🍪 COOKIE: {cookie_data.strip()}\n", 'cookie')

        host_match = re.search(
            r'Host:\s*(\S+)', packet_data, re.IGNORECASE)
        if host_match:
            self.log_live(
                f"   Host: {host_match.group(1)}\n", 'header')

        self.cookie_output.insert(
            tk.END,
            f"[{timestamp}] {'─' * 40}\n"
            f"  Host: "
            f"{host_match.group(1) if host_match else 'N/A'}\n"
            f"  Cookie: {cookie_data.strip()}\n\n")
        self.cookie_output.see(tk.END)

    def log_setcookie(self, cookie_data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live(
            f"🍪 SET-COOKIE: {cookie_data.strip()}\n", 'cookie')

        self.cookie_output.insert(
            tk.END,
            f"[{timestamp}] SET-COOKIE:\n"
            f"  {cookie_data.strip()}\n\n")
        self.cookie_output.see(tk.END)

    def log_form(self, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live("📝 FORM DATA DETECTED\n", 'form')

        lines = data.split('\n')
        for line in lines:
            if '=' in line and '&' in line and 'HTTP' not in line:
                pairs = line.strip().split('&')
                for pair in pairs:
                    if '=' in pair:
                        key, _, value = pair.partition('=')
                        self.log_live(
                            f"   📋 {key} = {value}\n", 'form')

    def log_json(self, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live("📦 JSON DATA\n", 'info')

        json_match = re.search(r'(\{[^}]+\})', data)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                self.log_live(
                    f"   {json.dumps(parsed, indent=2)}\n", 'info')
            except json.JSONDecodeError:
                self.log_live(
                    f"   {json_match.group(1)}\n", 'info')

    def log_auth(self, auth_data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n{'─' * 60}\n", 'separator')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live(
            f"🔐 AUTHORIZATION: {auth_data.strip()}\n", 'credential')

        if 'Basic' in auth_data:
            try:
                import base64
                encoded = auth_data.split('Basic')[1].strip()
                decoded = base64.b64decode(encoded).decode(
                    'utf-8', errors='ignore')
                self.log_live(
                    f"   ⚠️  Decoded: {decoded}\n", 'credential')
                self.cred_output.insert(
                    tk.END,
                    f"\n{'🔓' * 20}\n"
                    f"[{timestamp}] BASIC AUTH DECODED:\n"
                    f"  Raw: {auth_data.strip()}\n"
                    f"  Decoded: {decoded}\n"
                    f"{'🔓' * 20}\n\n")
                self.cred_output.see(tk.END)
            except Exception:
                pass

        if 'Bearer' in auth_data:
            self.log_live(
                f"   🎫 Token Bearer detectado\n", 'warning')
            self.cred_output.insert(
                tk.END,
                f"\n[{timestamp}] BEARER TOKEN:\n"
                f"  {auth_data.strip()}\n\n")
            self.cred_output.see(tk.END)

    def log_credential(self, keyword, value, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n{'⚠️ ' * 20}\n", 'warning')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live("🔑 CREDENCIAL DETECTADA!\n", 'credential')
        self.log_live(f"   Campo: {keyword}\n", 'credential')
        self.log_live(f"   Valor: {value}\n", 'credential')

        host_match = re.search(
            r'Host:\s*(\S+)', data, re.IGNORECASE)
        if host_match:
            self.log_live(
                f"   Host: {host_match.group(1)}\n", 'header')

        uri_match = re.search(
            r'(?:POST|GET)\s+(\S+)', data)
        if uri_match:
            self.log_live(
                f"   URI: {uri_match.group(1)}\n", 'header')

        self.log_live(f"{'⚠️ ' * 20}\n\n", 'warning')

        self.cred_output.insert(
            tk.END, f"\n{'🚨' * 25}\n", 'alert')
        self.cred_output.insert(
            tk.END,
            f"[{timestamp}] CREDENCIAL CAPTURADA!\n"
            f"  Campo: {keyword}\n"
            f"  Valor: {value}\n"
            f"  Host: "
            f"{host_match.group(1) if host_match else 'N/A'}\n"
            f"  URI: "
            f"{uri_match.group(1) if uri_match else 'N/A'}\n")
        self.cred_output.insert(
            tk.END, f"{'🚨' * 25}\n\n", 'alert')
        self.cred_output.see(tk.END)

        self.root.after(
            0, lambda: self.cred_count_label.config(
                text=f"🔑 Credenciais: {self.stats['Credentials']}"))

    def log_sni(self, domain, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live(f"🔒 TLS/SNI: {domain}\n", 'sni')

        self.dns_output.insert(
            tk.END, f"[{timestamp}] 🔒 TLS SNI: {domain}\n")
        self.dns_output.see(tk.END)

    def log_dns(self, query, data):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{timestamp}] ", 'timestamp')
        self.log_live(f"🌍 DNS Query: {query}\n", 'dns')

        self.dns_output.insert(
            tk.END, f"[{timestamp}] 🌍 DNS: {query}\n")
        self.dns_output.see(tk.END)

    def stop_capture(self):
        self.is_capturing = False
        self.capture_end_time = datetime.datetime.now()

        if self.tcpdump_process:
            try:
                os.killpg(
                    os.getpgid(self.tcpdump_process.pid),
                    signal.SIGTERM)
            except Exception:
                try:
                    self.tcpdump_process.terminate()
                    self.tcpdump_process.kill()
                except Exception:
                    pass

        self.capture_stopped()

    def capture_stopped(self):
        self.is_capturing = False
        if not self.capture_end_time:
            self.capture_end_time = datetime.datetime.now()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(
            text="⬤ PARADO", fg=self.colors['error'])
        self.status_label.config(text="Captura finalizada")

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_live(f"\n{'=' * 70}\n", 'separator')
        self.log_live(f"⏹ CAPTURA FINALIZADA - {now}\n", 'warning')
        self.log_live(
            f"   Total de pacotes: {self.packet_count}\n", 'info')
        self.log_live(
            f"   Pacotes filtrados: {self.filtered_count}\n", 'info')
        self.log_live(
            f"   Credenciais encontradas: "
            f"{self.stats.get('Credentials', 0)}\n", 'credential')
        self.log_live(f"{'=' * 70}\n", 'separator')

    def clear_output(self):
        self.live_output.delete("1.0", tk.END)
        self.cred_output.delete("1.0", tk.END)
        self.cookie_output.delete("1.0", tk.END)
        self.dns_output.delete("1.0", tk.END)
        self.raw_output.delete("1.0", tk.END)
        self.cmd_output.delete("1.0", tk.END)
        self.packet_count = 0
        self.filtered_count = 0
        self.stats.clear()
        self.all_packets.clear()
        self.captured_credentials.clear()
        self.captured_cookies.clear()
        self.captured_dns.clear()
        self.captured_http_requests.clear()
        self.captured_auth_tokens.clear()
        self.capture_start_time = None
        self.capture_end_time = None
        self.packet_count_label.config(text="Pacotes: 0")
        self.filtered_count_label.config(text="Filtrados: 0")
        self.cred_count_label.config(text="🔑 Credenciais: 0")

    # ==================== SALVAR HTML ====================

    def save_capture_html(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html")],
            title="Salvar Relatório HTML",
            initialfile=f"network_capture_"
                        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        f".html"
        )
        if not filename:
            return

        try:
            html_content = self._generate_html_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            messagebox.showinfo(
                "✅ Sucesso",
                f"Relatório HTML salvo com sucesso!\n\n{filename}")
        except Exception as e:
            messagebox.showerror(
                "❌ Erro", f"Erro ao salvar relatório:\n{str(e)}")

    def _generate_html_report(self):
        now = datetime.datetime.now()
        start = (self.capture_start_time.strftime('%Y-%m-%d %H:%M:%S')
                 if self.capture_start_time else 'N/A')
        end = (self.capture_end_time.strftime('%Y-%m-%d %H:%M:%S')
               if self.capture_end_time else now.strftime('%Y-%m-%d %H:%M:%S'))

        if self.capture_start_time and self.capture_end_time:
            duration = self.capture_end_time - self.capture_start_time
            duration_str = str(duration).split('.')[0]
        else:
            duration_str = 'N/A'

        iface = self.interface_var.get()
        cred_count = self.stats.get('Credentials', 0)

        stats_rows = ""
        icons_map = {
            'POST': ('🔴', '#ff6b6b'),
            'GET': ('🟢', '#51cf66'),
            'Cookies': ('🍪', '#f783ac'),
            'Set-Cookies': ('🍪', '#f783ac'),
            'Form Data': ('📝', '#da77f2'),
            'JSON': ('📦', '#748ffc'),
            'Auth Headers': ('🔐', '#ffd43b'),
            'Credentials': ('🔑', '#ff4444'),
            'SNI/DNS': ('🔒', '#ffd43b'),
            'DNS': ('🌍', '#748ffc'),
        }

        for key, count in sorted(
                self.stats.items(), key=lambda x: x[1], reverse=True):
            icon, color = icons_map.get(key, ('📊', '#a0a0b0'))
            pct = ((count / self.filtered_count * 100)
                   if self.filtered_count > 0 else 0)
            stats_rows += f"""
                <tr>
                    <td>{icon} {html_module.escape(str(key))}</td>
                    <td class="count" style="color: {color};">{count}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill"
                                 style="width: {min(pct, 100):.1f}%;
                                        background: {color};"></div>
                        </div>
                    </td>
                    <td class="pct">{pct:.1f}%</td>
                </tr>"""

        if not stats_rows:
            stats_rows = """
                <tr>
                    <td colspan="4" style="text-align:center; color:#666;">
                        Nenhum dado capturado
                    </td>
                </tr>"""

        cred_rows = ""
        for cred in self.captured_credentials:
            cred_rows += f"""
                <tr class="cred-row">
                    <td>{html_module.escape(cred['time'])}</td>
                    <td class="cred-field">{html_module.escape(cred['field'])}</td>
                    <td class="cred-value">{html_module.escape(cred['value'])}</td>
                    <td>{html_module.escape(cred['host'])}</td>
                    <td>{html_module.escape(cred['uri'])}</td>
                </tr>"""

        if not cred_rows:
            cred_rows = """
                <tr>
                    <td colspan="5" style="text-align:center; color:#666;">
                        Nenhuma credencial capturada
                    </td>
                </tr>"""

        cookie_rows = ""
        for cookie in self.captured_cookies:
            cookie_rows += f"""
                <tr>
                    <td>{html_module.escape(cookie['time'])}</td>
                    <td>
                        <span class="badge badge-cookie">
                            {html_module.escape(cookie['type'])}
                        </span>
                    </td>
                    <td>{html_module.escape(cookie['host'])}</td>
                    <td class="cookie-val">{html_module.escape(cookie['value'])}</td>
                </tr>"""

        if not cookie_rows:
            cookie_rows = """
                <tr>
                    <td colspan="4" style="text-align:center; color:#666;">
                        Nenhum cookie capturado
                    </td>
                </tr>"""

        dns_rows = ""
        for dns in self.captured_dns:
            badge_class = ('badge-sni' if dns['type'] == 'TLS SNI'
                           else 'badge-dns')
            dns_rows += f"""
                <tr>
                    <td>{html_module.escape(dns['time'])}</td>
                    <td>
                        <span class="badge {badge_class}">
                            {html_module.escape(dns['type'])}
                        </span>
                    </td>
                    <td class="dns-query">{html_module.escape(dns['query'])}</td>
                </tr>"""

        if not dns_rows:
            dns_rows = """
                <tr>
                    <td colspan="3" style="text-align:center; color:#666;">
                        Nenhuma consulta DNS/SNI capturada
                    </td>
                </tr>"""

        http_rows = ""
        for req in self.captured_http_requests[-200:]:
            method_class = ('method-post' if req['method'] == 'POST'
                            else 'method-get')
            http_rows += f"""
                <tr>
                    <td>{html_module.escape(req['time'])}</td>
                    <td>
                        <span class="badge {method_class}">
                            {html_module.escape(req['method'])}
                        </span>
                    </td>
                    <td>{html_module.escape(req['host'])}</td>
                    <td class="uri-cell">{html_module.escape(req['uri'])}</td>
                    <td><small>{html_module.escape(req['content_type'])}</small></td>
                </tr>"""

        if not http_rows:
            http_rows = """
                <tr>
                    <td colspan="5" style="text-align:center; color:#666;">
                        Nenhuma requisição HTTP capturada
                    </td>
                </tr>"""

        auth_rows = ""
        for auth in self.captured_auth_tokens:
            auth_rows += f"""
                <tr>
                    <td>{html_module.escape(auth['time'])}</td>
                    <td>{html_module.escape(auth['host'])}</td>
                    <td class="auth-val">{html_module.escape(auth['value'])}</td>
                </tr>"""

        if not auth_rows:
            auth_rows = """
                <tr>
                    <td colspan="3" style="text-align:center; color:#666;">
                        Nenhum token de autenticação capturado
                    </td>
                </tr>"""

        live_text = html_module.escape(
            self.live_output.get("1.0", tk.END).strip())
        raw_text = html_module.escape(
            self.raw_output.get("1.0", tk.END).strip()[:50000])

        active_filters = []
        for key, var in self.filter_vars.items():
            if var.get():
                active_filters.append(key.upper())
        for key, var in self.http_filter_vars.items():
            if var.get():
                active_filters.append(f"HTTP_{key.upper()}")
        for key, var in self.tls_filter_vars.items():
            if var.get():
                active_filters.append(f"TLS_{key.upper()}")

        filters_badges = ""
        for f in active_filters:
            filters_badges += (
                f'<span class="badge badge-filter">{f}</span> ')

        cred_alert = ""
        if cred_count > 0:
            cred_alert = f"""
            <div class="alert-banner">
                <div class="alert-icon">🚨</div>
                <div class="alert-text">
                    <strong>ALERTA DE SEGURANÇA:</strong>
                    {cred_count} credencial(is) capturada(s) em texto claro!
                    <br>
                    <small>
                        Dados sensíveis foram transmitidos sem criptografia adequada.
                    </small>
                </div>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Sniffer Report - {now.strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Inter', sans-serif;
            background: #0a0a1a; color: #e0e0e0;
            line-height: 1.6; min-height: 100vh;
        }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        @keyframes glowPulse {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(233, 69, 96, 0.3); }}
            50% {{ box-shadow: 0 0 40px rgba(233, 69, 96, 0.6); }}
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
            padding: 40px 0; text-align: center;
            border-bottom: 3px solid #e94560;
        }}
        .header h1 {{
            font-size: 2.5em; color: #e94560;
            text-shadow: 0 0 30px rgba(233, 69, 96, 0.5);
            margin-bottom: 8px;
        }}
        .header .subtitle {{ color: #00d2ff; font-size: 1.1em; }}
        .header .report-time {{ color: #a0a0b0; font-size: 0.9em; margin-top: 10px; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 20px; }}
        .alert-banner {{
            background: linear-gradient(135deg, #3d0000, #5c0000);
            border: 2px solid #ff4444; border-radius: 12px;
            padding: 20px 30px; margin-bottom: 30px;
            display: flex; align-items: center; gap: 20px;
            animation: glowPulse 2s ease-in-out infinite;
        }}
        .alert-icon {{ font-size: 3em; animation: pulse 1.5s ease-in-out infinite; }}
        .alert-text {{ color: #ff8888; font-size: 1.1em; }}
        .alert-text strong {{ color: #ff4444; font-size: 1.2em; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px; margin-bottom: 40px;
        }}
        .summary-card {{
            background: linear-gradient(145deg, #1a1a2e, #16213e);
            border: 1px solid #2a2a4a; border-radius: 16px;
            padding: 25px; text-align: center;
            transition: all 0.3s ease;
            animation: fadeInUp 0.6s ease forwards;
        }}
        .summary-card:hover {{
            transform: translateY(-5px); border-color: #e94560;
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.2);
        }}
        .summary-card .card-icon {{ font-size: 2.5em; margin-bottom: 10px; }}
        .summary-card .card-value {{ font-size: 2.2em; font-weight: 800; margin-bottom: 5px; }}
        .summary-card .card-label {{
            color: #a0a0b0; font-size: 0.85em;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        .card-packets .card-value {{ color: #00d2ff; }}
        .card-filtered .card-value {{ color: #00ff88; }}
        .card-duration .card-value {{ color: #ffaa00; font-size: 1.4em; }}
        .card-creds .card-value {{ color: #ff4444; }}
        .card-cookies .card-value {{ color: #f783ac; }}
        .card-dns .card-value {{ color: #748ffc; }}
        .info-bar {{
            background: #16213e; border: 1px solid #2a2a4a;
            border-radius: 12px; padding: 20px 30px;
            margin-bottom: 30px; display: flex;
            flex-wrap: wrap; gap: 30px; align-items: center;
        }}
        .info-item {{ display: flex; align-items: center; gap: 8px; }}
        .info-item .label {{ color: #a0a0b0; font-size: 0.85em; text-transform: uppercase; }}
        .info-item .value {{ color: #00d2ff; font-weight: 600; }}
        .badge {{
            display: inline-block; padding: 4px 12px;
            border-radius: 20px; font-size: 0.75em;
            font-weight: 600; text-transform: uppercase; margin: 3px;
        }}
        .badge-filter {{ background: rgba(0, 210, 255, 0.15); color: #00d2ff; }}
        .badge-cookie {{ background: rgba(247, 131, 172, 0.15); color: #f783ac; }}
        .badge-sni {{ background: rgba(255, 212, 59, 0.15); color: #ffd43b; }}
        .badge-dns {{ background: rgba(116, 143, 252, 0.15); color: #748ffc; }}
        .method-post {{ background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }}
        .method-get {{ background: rgba(81, 207, 102, 0.2); color: #51cf66; }}
        .section {{
            background: #12122a; border: 1px solid #2a2a4a;
            border-radius: 16px; margin-bottom: 30px; overflow: hidden;
        }}
        .section-header {{
            padding: 20px 30px; display: flex;
            align-items: center; gap: 12px;
            cursor: pointer; transition: background 0.3s; user-select: none;
        }}
        .section-header:hover {{ background: rgba(233, 69, 96, 0.05); }}
        .section-header .section-icon {{ font-size: 1.5em; }}
        .section-header h2 {{ font-size: 1.3em; font-weight: 700; flex: 1; }}
        .section-header .section-count {{
            background: rgba(233, 69, 96, 0.2); color: #e94560;
            padding: 4px 14px; border-radius: 20px;
            font-size: 0.85em; font-weight: 700;
        }}
        .section-header .toggle-icon {{
            font-size: 1.2em; color: #a0a0b0; transition: transform 0.3s;
        }}
        .section-content {{ padding: 0 30px 25px; }}
        .section-stats h2 {{ color: #00d2ff; }}
        .section-creds h2 {{ color: #ff4444; }}
        .section-http h2 {{ color: #51cf66; }}
        .section-cookies h2 {{ color: #f783ac; }}
        .section-dns h2 {{ color: #748ffc; }}
        .section-auth h2 {{ color: #ffd43b; }}
        .section-live h2 {{ color: #a0a0b0; }}
        .section-raw h2 {{ color: #6c757d; }}
        .data-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.9em; }}
        .data-table thead th {{
            background: #1a1a3a; color: #a0a0b0;
            padding: 12px 16px; text-align: left;
            font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.5px; font-size: 0.8em;
            border-bottom: 2px solid #2a2a4a;
            position: sticky; top: 0; z-index: 1;
        }}
        .data-table tbody tr {{ transition: background 0.2s; }}
        .data-table tbody tr:hover {{ background: rgba(233, 69, 96, 0.05); }}
        .data-table tbody tr:nth-child(even) {{ background: rgba(255, 255, 255, 0.02); }}
        .data-table tbody td {{
            padding: 10px 16px;
            border-bottom: 1px solid #1a1a3a;
            vertical-align: top;
        }}
        .cred-row {{ background: rgba(255, 0, 0, 0.03) !important; }}
        .cred-row:hover {{ background: rgba(255, 0, 0, 0.08) !important; }}
        .cred-field {{ color: #ffaa00; font-weight: 700; }}
        .cred-value {{
            color: #ff4444; font-weight: 700;
            font-family: 'Consolas', monospace; word-break: break-all;
        }}
        .cookie-val {{
            font-family: 'Consolas', monospace; font-size: 0.85em;
            color: #f783ac; word-break: break-all; max-width: 500px;
        }}
        .dns-query {{
            font-family: 'Consolas', monospace;
            color: #748ffc; font-weight: 600;
        }}
        .uri-cell {{
            font-family: 'Consolas', monospace; font-size: 0.85em;
            color: #51cf66; word-break: break-all; max-width: 400px;
        }}
        .auth-val {{
            font-family: 'Consolas', monospace; font-size: 0.85em;
            color: #ffd43b; word-break: break-all;
        }}
        .count {{ font-weight: 800; font-size: 1.2em; }}
        .pct {{ color: #a0a0b0; font-size: 0.9em; }}
        .progress-bar {{
            width: 100%; height: 8px; background: #1a1a3a;
            border-radius: 4px; overflow: hidden;
        }}
        .progress-fill {{
            height: 100%; border-radius: 4px;
            transition: width 0.5s ease; min-width: 2px;
        }}
        .log-container {{
            max-height: 600px; overflow-y: auto;
            background: #0d1117; border: 1px solid #21262d;
            border-radius: 8px;
        }}
        .log-output {{
            font-family: 'Consolas', monospace;
            font-size: 0.82em; line-height: 1.5;
            padding: 20px; white-space: pre-wrap;
            word-wrap: break-word; color: #c9d1d9;
        }}
        .table-scroll {{ max-height: 500px; overflow-y: auto; border-radius: 8px; }}
        .footer {{
            text-align: center; padding: 30px;
            color: #555; font-size: 0.85em;
            border-top: 1px solid #1a1a3a; margin-top: 40px;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>🔍 NETWORK SNIFFER REPORT</h1>
    <div class="subtitle">Relatório de Análise de Tráfego de Rede</div>
    <div class="report-time">Gerado em {now.strftime('%d/%m/%Y às %H:%M:%S')}</div>
</div>

<div class="container">
    {cred_alert}

    <div class="summary-grid">
        <div class="summary-card card-packets">
            <div class="card-icon">📡</div>
            <div class="card-value">{self.packet_count:,}</div>
            <div class="card-label">Total de Pacotes</div>
        </div>
        <div class="summary-card card-filtered">
            <div class="card-icon">🔍</div>
            <div class="card-value">{self.filtered_count:,}</div>
            <div class="card-label">Pacotes Filtrados</div>
        </div>
        <div class="summary-card card-duration">
            <div class="card-icon">⏱️</div>
            <div class="card-value">{duration_str}</div>
            <div class="card-label">Duração</div>
        </div>
        <div class="summary-card card-creds">
            <div class="card-icon">🔑</div>
            <div class="card-value">{cred_count}</div>
            <div class="card-label">Credenciais</div>
        </div>
        <div class="summary-card card-cookies">
            <div class="card-icon">🍪</div>
            <div class="card-value">{len(self.captured_cookies)}</div>
            <div class="card-label">Cookies</div>
        </div>
        <div class="summary-card card-dns">
            <div class="card-icon">🌍</div>
            <div class="card-value">{len(self.captured_dns)}</div>
            <div class="card-label">DNS/SNI</div>
        </div>
    </div>

    <div class="info-bar">
        <div class="info-item"><span class="label">Interface:</span><span class="value">{html_module.escape(iface)}</span></div>
        <div class="info-item"><span class="label">Início:</span><span class="value">{start}</span></div>
        <div class="info-item"><span class="label">Fim:</span><span class="value">{end}</span></div>
        <div class="info-item"><span class="label">HTTP:</span><span class="value">{len(self.captured_http_requests)}</span></div>
        <div class="info-item"><span class="label">Auth:</span><span class="value">{len(self.captured_auth_tokens)}</span></div>
    </div>

    <div class="section">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">⚙️</span>
            <h2 style="color: #a0a0b0;">Filtros Ativos</h2>
            <span class="section-count">{len(active_filters)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div style="padding: 10px 0;">
                {filters_badges if filters_badges else '<span style="color:#666;">Nenhum filtro ativo</span>'}
            </div>
        </div>
    </div>

    <div class="section section-stats">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">📊</span>
            <h2>Estatísticas por Tipo</h2>
            <span class="section-count">{len(self.stats)} tipos</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Tipo</th><th>Qtde</th><th style="min-width:200px;">Distribuição</th><th>%</th></tr>
                    </thead>
                    <tbody>{stats_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-creds">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">🔑</span>
            <h2>Credenciais Capturadas</h2>
            <span class="section-count">{len(self.captured_credentials)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Horário</th><th>Campo</th><th>Valor</th><th>Host</th><th>URI</th></tr>
                    </thead>
                    <tbody>{cred_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-http">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">🌐</span>
            <h2>Requisições HTTP</h2>
            <span class="section-count">{len(self.captured_http_requests)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Horário</th><th>Método</th><th>Host</th><th>URI</th><th>Content-Type</th></tr>
                    </thead>
                    <tbody>{http_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-cookies">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">🍪</span>
            <h2>Cookies Capturados</h2>
            <span class="section-count">{len(self.captured_cookies)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Horário</th><th>Tipo</th><th>Host</th><th>Valor</th></tr>
                    </thead>
                    <tbody>{cookie_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-dns">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">🌍</span>
            <h2>Consultas DNS / TLS SNI</h2>
            <span class="section-count">{len(self.captured_dns)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Horário</th><th>Tipo</th><th>Domínio / Query</th></tr>
                    </thead>
                    <tbody>{dns_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-auth">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">🔐</span>
            <h2>Tokens de Autenticação</h2>
            <span class="section-count">{len(self.captured_auth_tokens)}</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr><th>Horário</th><th>Host</th><th>Authorization Header</th></tr>
                    </thead>
                    <tbody>{auth_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="section section-live">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">📡</span>
            <h2>Log de Tráfego ao Vivo</h2>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content">
            <div class="log-container">
                <div class="log-output">{live_text}</div>
            </div>
        </div>
    </div>

    <div class="section section-raw">
        <div class="section-header" onclick="toggleSection(this)">
            <span class="section-icon">📝</span>
            <h2>Raw Data (primeiros 50KB)</h2>
            <span class="section-count">{len(self.all_packets)} pacotes</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="section-content" style="display:none;">
            <div class="log-container">
                <div class="log-output" style="font-size:0.75em; color:#6c757d;">{raw_text}</div>
            </div>
        </div>
    </div>
</div>

<div class="footer">
    <p>🔍 <strong>Network Sniffer Report</strong> — Gerado em {now.strftime('%d/%m/%Y às %H:%M:%S')}</p>
    <p style="margin-top:5px;">Interface: {html_module.escape(iface)} | Pacotes: {self.packet_count:,} | Filtrados: {self.filtered_count:,} | Credenciais: {cred_count}</p>
    <p style="margin-top:10px; color:#444;">⚠️ Este relatório pode conter informações sensíveis. Manuseie com cuidado.</p>
</div>

<script>
    function toggleSection(header) {{
        const content = header.nextElementSibling;
        const icon = header.querySelector('.toggle-icon');
        if (content.style.display === 'none') {{
            content.style.display = 'block';
            icon.style.transform = 'rotate(0deg)';
        }} else {{
            content.style.display = 'none';
            icon.style.transform = 'rotate(-90deg)';
        }}
    }}
    document.addEventListener('DOMContentLoaded', function() {{
        const rawSection = document.querySelector('.section-raw .section-content');
        if (rawSection) {{
            rawSection.style.display = 'none';
            const icon = document.querySelector('.section-raw .toggle-icon');
            if (icon) icon.style.transform = 'rotate(-90deg)';
        }}
    }});
</script>
</body>
</html>"""
        return html

    def show_stats(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Estatísticas de Captura")
        stats_window.geometry("600x650")
        stats_window.configure(bg=self.colors['bg_dark'])

        tk.Label(stats_window, text="📊 ESTATÍSTICAS",
                 font=('Consolas', 16, 'bold'),
                 fg=self.colors['accent'],
                 bg=self.colors['bg_dark']).pack(pady=15)

        stats_text = scrolledtext.ScrolledText(
            stats_window, bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        stats_text.insert(tk.END, f"{'═' * 50}\n")
        stats_text.insert(tk.END, f"  RESUMO DA CAPTURA\n")
        stats_text.insert(tk.END, f"{'═' * 50}\n\n")
        stats_text.insert(
            tk.END, f"  📡 Total de Pacotes:     {self.packet_count}\n")
        stats_text.insert(
            tk.END, f"  🔍 Pacotes Filtrados:    {self.filtered_count}\n\n")
        stats_text.insert(tk.END, f"{'─' * 50}\n")
        stats_text.insert(tk.END, f"  DETALHAMENTO POR TIPO\n")
        stats_text.insert(tk.END, f"{'─' * 50}\n\n")

        icons = {
            'POST': '🔴', 'GET': '🟢', 'Cookies': '🍪',
            'Set-Cookies': '🍪', 'Form Data': '📝',
            'JSON': '📦', 'Auth Headers': '🔐',
            'Credentials': '🔑', 'SNI/DNS': '🔒', 'DNS': '🌍',
        }

        for key, count in sorted(
                self.stats.items(), key=lambda x: x[1], reverse=True):
            icon = icons.get(key, '📊')
            bar = '█' * min(count, 30) + '░' * max(0, 30 - count)
            stats_text.insert(
                tk.END, f"  {icon} {key:20s} {count:5d}  {bar}\n")

        if not self.stats:
            stats_text.insert(tk.END, "  Nenhuma estatística disponível.\n")
            stats_text.insert(tk.END, "  Inicie uma captura primeiro.\n")

        stats_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.is_capturing:
            if messagebox.askyesno(
                    "Confirmar",
                    "Captura em andamento. Deseja parar e sair?"):
                self.stop_capture()
                self.root.after(500, self.root.destroy)
            return
        self.root.destroy()


def main():
    if os.geteuid() != 0:
        print("\n" + "=" * 60)
        print("⚠️  AVISO: Este programa precisa ser executado como ROOT!")
        print("   Execute: sudo python3 sniffer.py")
        print("=" * 60 + "\n")

    try:
        subprocess.run(['which', 'tcpdump'],
                        capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ tcpdump não encontrado! Instale com:")
        print("   sudo apt install tcpdump")
        print("   ou: sudo yum install tcpdump")
        sys.exit(1)

    root = tk.Tk()
    app = NetworkSnifferGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
