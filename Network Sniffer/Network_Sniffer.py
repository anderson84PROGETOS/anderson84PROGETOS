#!/usr/bin/env python3
"""
Network Sniffer GUI - Analisador de Tráfego de Rede Avançado
- Filtros no TOPO (colapsáveis pelo botão 👁️)
- 👁️ e ▶ INICIAR ao lado da aba "Comando"
- Porta 80 (HTTP) marcada por padrão; 443 e SNI desmarcados
- Captura só inicia pelo botão (sem auto-start)
Execute: sudo python3 Network_Sniffer.py
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
        self.root.title("🔍 Network Sniffer - Analisador de Tráfego de Rede")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a2e")
        self.root.minsize(1100, 650)

        self.is_capturing = False
        self.tcpdump_process = None
        self.packet_count = 0
        self.filtered_count = 0
        self.all_packets = []
        self.stats = defaultdict(int)

        self.captured_credentials = []
        self.captured_cookies = []
        self.captured_dns = []
        self.captured_http_requests = []
        self.captured_auth_tokens = []
        self.capture_start_time = None
        self.capture_end_time = None

        self.filters_visible = True
        self.saved_height = 420

        self.setup_styles()
        self.create_widgets()
        self.check_privileges()

    # ==================== ESTILO ====================
    def setup_styles(self):
        self.colors = {
            'bg_dark': '#1a1a2e', 'bg_medium': '#16213e',
            'bg_light': '#0f3460', 'accent': '#e94560',
            'accent2': '#00d2ff', 'text': '#ffffff',
            'text_dim': '#a0a0b0', 'success': '#00ff88',
            'warning': '#ffaa00', 'error': '#ff4444',
            'http_post': '#ff6b6b', 'http_get': '#51cf66',
            'https': '#ffd43b', 'dns': '#748ffc',
            'cookie': '#f783ac', 'form': '#da77f2',
            'login': '#ff8787', 'credential': '#ff0000',
        }
        style = ttk.Style()
        style.theme_use('clam')
        c = self.colors
        style.configure('Dark.TLabelframe', background=c['bg_dark'],
                        foreground=c['accent2'])
        style.configure('Dark.TLabelframe.Label', background=c['bg_dark'],
                        foreground=c['accent2'],
                        font=('Consolas', 10, 'bold'))
        style.configure('Dark.TNotebook', background=c['bg_dark'])
        style.configure('Dark.TNotebook.Tab', background=c['bg_medium'],
                        foreground=c['text'],
                        font=('Consolas', 10, 'bold'), padding=[14, 7])

    def check_privileges(self):
        if os.geteuid() != 0:
            self.log_live(
                "⚠️  AVISO: Este programa precisa ser executado "
                "como ROOT!\n", 'warning')
            self.log_live(
                "   Execute: sudo python3 Network_Sniffer.py\n\n", 'info')

    # ==================== INTERFACE ====================
    def create_widgets(self):
        c = self.colors

        # ---- Header ----
        header = tk.Frame(self.root, bg=c['bg_dark'], pady=5)
        header.pack(fill=tk.X)

        tk.Label(header, text="🔍 NETWORK SNIFFER",
                 font=('Consolas', 18, 'bold'), fg=c['accent'],
                 bg=c['bg_dark']).pack(side=tk.LEFT, padx=15)
        tk.Label(header, text="Analisador de Tráfego de Rede Avançado",
                 font=('Consolas', 10), fg=c['text_dim'],
                 bg=c['bg_dark']).pack(side=tk.LEFT, padx=5)
        self.status_indicator = tk.Label(
            header, text="⬤ PARADO", font=('Consolas', 12, 'bold'),
            fg=c['error'], bg=c['bg_dark'])
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ==========================================================
        # PAINEL DE FILTROS (topo) — frame normal, colapsável
        # ==========================================================
        self.top_frame = tk.Frame(self.root, bg=c['bg_dark'],
                                  height=self.saved_height)
        # Inicia visível (logo abaixo do header)
        self.top_frame.pack(fill=tk.X, padx=5, before=self.root.pack_slaves()[-1]
                            if self.root.pack_slaves() else None)
        self.top_frame.pack_propagate(False)

        top_canvas = tk.Canvas(self.top_frame, bg=c['bg_dark'],
                               highlightthickness=0)
        top_hscroll = ttk.Scrollbar(self.top_frame, orient=tk.HORIZONTAL,
                                    command=top_canvas.xview)
        top_vscroll = ttk.Scrollbar(self.top_frame, orient=tk.VERTICAL,
                                    command=top_canvas.yview)
        top_scrollable = tk.Frame(top_canvas, bg=c['bg_dark'])

        top_scrollable.bind(
            "<Configure>",
            lambda e: top_canvas.configure(
                scrollregion=top_canvas.bbox("all")))
        top_canvas.create_window((0, 0), window=top_scrollable, anchor="nw")
        top_canvas.configure(yscrollcommand=top_vscroll.set,
                             xscrollcommand=top_hscroll.set)

        top_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        top_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        top_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_filter_columns(top_scrollable)

        # ==========================================================
        # ÁREA DE RESULTADOS (embaixo, largura total)
        # ==========================================================
        self.results_frame = tk.Frame(self.root, bg=c['bg_dark'])
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(self.results_frame,
                                     style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Barra flutuante ao lado da aba "⌨️ Comando" (canto sup. direito)
        quick_bar = tk.Frame(self.results_frame, bg=c['bg_medium'],
                             bd=1, relief=tk.RAISED)
        quick_bar.place(relx=1.0, y=3, anchor=tk.NE, x=-6)

        self.eye_btn = tk.Button(
            quick_bar, text="👁️", width=4,
            command=self.toggle_filters,
            bg=c['bg_light'], fg=c['accent2'],
            font=('Consolas', 12, 'bold'), relief=tk.FLAT, cursor='hand2')
        self.eye_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.quick_capture_btn = tk.Button(
            quick_bar, text="▶ INICIAR", width=12,
            command=self.toggle_capture,
            bg=c['success'], fg='black',
            font=('Consolas', 10, 'bold'), relief=tk.FLAT, cursor='hand2')
        self.quick_capture_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.notebook.bind("<ButtonPress>", lambda e: quick_bar.lift())

        # ---- Abas ----
        live_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(live_frame, text="📡 Tráfego ao Vivo")
        self.live_output = scrolledtext.ScrolledText(
            live_frame, bg='#0d1117', fg=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, wrap=tk.WORD, insertbackground=c['text'])
        self.live_output.pack(fill=tk.BOTH, expand=True)

        tags_config = {
            'http_post': {'foreground': c['http_post'],
                          'font': ('Consolas', 10, 'bold')},
            'http_get': {'foreground': c['http_get']},
            'https': {'foreground': c['https']},
            'dns': {'foreground': c['dns']},
            'cookie': {'foreground': c['cookie']},
            'form': {'foreground': c['form']},
            'login': {'foreground': c['login'],
                      'font': ('Consolas', 11, 'bold')},
            'credential': {'foreground': c['credential'],
                           'font': ('Consolas', 11, 'bold'),
                           'background': '#3d0000'},
            'separator': {'foreground': c['text_dim']},
            'header': {'foreground': c['accent2']},
            'timestamp': {'foreground': c['text_dim']},
            'warning': {'foreground': c['warning'],
                        'font': ('Consolas', 11, 'bold')},
            'info': {'foreground': c['accent2']},
            'sni': {'foreground': '#ffd43b',
                    'font': ('Consolas', 10, 'bold')},
        }
        for tag, config in tags_config.items():
            self.live_output.tag_configure(tag, **config)

        cred_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(cred_frame, text="🔑 Credenciais")
        self.cred_output = scrolledtext.ScrolledText(
            cred_frame, bg='#1a0000', fg=c['credential'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cred_output.pack(fill=tk.BOTH, expand=True)
        self.cred_output.tag_configure('alert', foreground='#ff0000',
                                       font=('Consolas', 12, 'bold'))

        cookie_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(cookie_frame, text="🍪 Cookies")
        self.cookie_output = scrolledtext.ScrolledText(
            cookie_frame, bg='#1a0a15', fg=c['cookie'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cookie_output.pack(fill=tk.BOTH, expand=True)

        dns_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(dns_frame, text="🌍 DNS/SNI")
        self.dns_output = scrolledtext.ScrolledText(
            dns_frame, bg='#0a0a1a', fg=c['dns'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.dns_output.pack(fill=tk.BOTH, expand=True)

        raw_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(raw_frame, text="📝 Raw Data")
        self.raw_output = scrolledtext.ScrolledText(
            raw_frame, bg='#0d1117', fg='#8b949e', font=('Consolas', 10),
            relief=tk.FLAT, wrap=tk.WORD)
        self.raw_output.pack(fill=tk.BOTH, expand=True)

        cmd_frame = tk.Frame(self.notebook, bg=c['bg_dark'])
        self.notebook.add(cmd_frame, text="⌨️ Comando")
        self.cmd_output = scrolledtext.ScrolledText(
            cmd_frame, bg='#0d1117', fg=c['success'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        self.cmd_output.pack(fill=tk.BOTH, expand=True)

        # ---- Barra de status ----
        status_frame = tk.Frame(self.root, bg=c['bg_medium'], height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame, text="Pronto. Clique em INICIAR CAPTURA.",
            bg=c['bg_medium'], fg=c['text_dim'], font=('Consolas', 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.packet_count_label = tk.Label(
            status_frame, text="Pacotes: 0", bg=c['bg_medium'],
            fg=c['accent2'], font=('Consolas', 9, 'bold'))
        self.packet_count_label.pack(side=tk.RIGHT, padx=10)

        self.filtered_count_label = tk.Label(
            status_frame, text="Filtrados: 0", bg=c['bg_medium'],
            fg=c['warning'], font=('Consolas', 9, 'bold'))
        self.filtered_count_label.pack(side=tk.RIGHT, padx=10)

        self.cred_count_label = tk.Label(
            status_frame, text="🔑 Credenciais: 0", bg=c['bg_medium'],
            fg=c['error'], font=('Consolas', 9, 'bold'))
        self.cred_count_label.pack(side=tk.RIGHT, padx=10)

    # ---- Colunas do painel de filtros ----
    def build_filter_columns(self, parent):
        c = self.colors

        # ---- Coluna 1: Interface + Controles ----
        col1 = tk.Frame(parent, bg=c['bg_dark'])
        col1.pack(side=tk.LEFT, anchor=tk.N, padx=8, pady=5)

        self.create_section_label(col1, "📡 INTERFACE DE REDE")
        iface_frame = tk.Frame(col1, bg=c['bg_dark'])
        iface_frame.pack(fill=tk.X, padx=5, pady=2)

        self.interface_var = tk.StringVar(value="eth0")
        interfaces = self.get_interfaces()
        if "eth0" not in interfaces:
            interfaces.insert(0, "eth0")
        self.iface_combo = ttk.Combobox(
            iface_frame, textvariable=self.interface_var,
            values=interfaces, width=20, state='readonly')
        self.iface_combo.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(iface_frame, text="🔄", command=self.refresh_interfaces,
                  bg=c['bg_light'], fg=c['text'], font=('Consolas', 10),
                  relief=tk.FLAT, width=3).pack(side=tk.RIGHT, padx=2)

        self.create_section_label(col1, "🎮 CONTROLES")
        btn_frame = tk.Frame(col1, bg=c['bg_dark'])
        btn_frame.pack(fill=tk.X, padx=5, pady=3)

        self.start_btn = tk.Button(
            btn_frame, text="▶ INICIAR CAPTURA",
            command=self.start_capture,
            bg=c['success'], fg='black', font=('Consolas', 10, 'bold'),
            relief=tk.FLAT, cursor='hand2', height=1)
        self.start_btn.pack(fill=tk.X, pady=2)

        self.stop_btn = tk.Button(
            btn_frame, text="⏹ PARAR CAPTURA", command=self.stop_capture,
            bg=c['error'], fg='white', font=('Consolas', 10, 'bold'),
            relief=tk.FLAT, cursor='hand2', state=tk.DISABLED, height=1)
        self.stop_btn.pack(fill=tk.X, pady=2)

        btn_frame2 = tk.Frame(col1, bg=c['bg_dark'])
        btn_frame2.pack(fill=tk.X, padx=5, pady=2)

        tk.Button(btn_frame2, text="🗑️ Limpar", command=self.clear_output,
                  bg=c['bg_light'], fg=c['text'], font=('Consolas', 9),
                  relief=tk.FLAT, cursor='hand2').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(btn_frame2, text="💾 HTML",
                  command=self.save_capture_html,
                  bg=c['accent'], fg='white',
                  font=('Consolas', 9, 'bold'), relief=tk.FLAT,
                  cursor='hand2').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(btn_frame2, text="📊 Stats", command=self.show_stats,
                  bg=c['bg_light'], fg=c['text'], font=('Consolas', 9),
                  relief=tk.FLAT, cursor='hand2').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        # Botão 👁️ também aqui (mesma função do olho da barra)
        self.eye_btn2 = tk.Button(
            btn_frame2, text="👁️ Filtros", command=self.toggle_filters,
            bg=c['bg_light'], fg=c['accent2'],
            font=('Consolas', 9, 'bold'), relief=tk.FLAT, cursor='hand2')
        self.eye_btn2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        self.create_section_label(col1, "⚙️ OPÇÕES DE CAPTURA")
        opts_frame = tk.Frame(col1, bg=c['bg_dark'])
        opts_frame.pack(fill=tk.X, padx=5, pady=2)

        self.verbose_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_frame, text="Modo Verboso (payload completo)",
                       variable=self.verbose_var, bg=c['bg_dark'],
                       fg=c['text'], selectcolor=c['bg_medium'],
                       font=('Consolas', 9)).pack(anchor=tk.W)
        self.resolve_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Resolver DNS (mais lento)",
                       variable=self.resolve_var, bg=c['bg_dark'],
                       fg=c['text'], selectcolor=c['bg_medium'],
                       font=('Consolas', 9)).pack(anchor=tk.W)

        tk.Label(opts_frame, text="Limite de pacotes (0 = ilimitado):",
                 bg=c['bg_dark'], fg=c['text_dim'],
                 font=('Consolas', 8)).pack(anchor=tk.W, pady=(4, 0))
        self.packet_limit = tk.Entry(
            opts_frame, bg=c['bg_medium'], fg=c['text'],
            insertbackground=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, width=10)
        self.packet_limit.pack(anchor=tk.W, pady=2)
        self.packet_limit.insert(0, "0")

        # ---- Coluna 2: Protocolos ----
        col2 = tk.Frame(parent, bg=c['bg_dark'])
        col2.pack(side=tk.LEFT, anchor=tk.N, padx=8, pady=5)

        self.create_section_label(col2, "🔧 FILTROS DE PROTOCOLO")
        proto_frame = tk.Frame(col2, bg=c['bg_dark'])
        proto_frame.pack(fill=tk.X, padx=5, pady=2)

        self.filter_vars = {}
        filters_list = [
            ("HTTP (porta 80)", "http", True),      # <-- já marcado
            ("HTTPS/TLS (porta 443)", "https", False),
            ("DNS (porta 53)", "dns", False),
            ("FTP (porta 21)", "ftp", False),
            ("SMTP (porta 25/587)", "smtp", False),
            ("POP3 (porta 110)", "pop3", False),
            ("IMAP (porta 143)", "imap", False),
            ("SSH (porta 22)", "ssh", False),
            ("Telnet (porta 23)", "telnet", False),
            ("MySQL (porta 3306)", "mysql", False),
            ("PostgreSQL (porta 5432)", "pgsql", False),
        ]
        proto_left = tk.Frame(proto_frame, bg=c['bg_dark'])
        proto_left.pack(side=tk.LEFT, anchor=tk.N)
        proto_right = tk.Frame(proto_frame, bg=c['bg_dark'])
        proto_right.pack(side=tk.LEFT, anchor=tk.N, padx=10)

        for idx, (text, key, default) in enumerate(filters_list):
            var = tk.BooleanVar(value=default)
            self.filter_vars[key] = var
            parent_cb = proto_left if idx < 6 else proto_right
            tk.Checkbutton(parent_cb, text=text, variable=var,
                           bg=c['bg_dark'], fg=c['text'],
                           selectcolor=c['bg_medium'],
                           activebackground=c['bg_dark'],
                           font=('Consolas', 9)).pack(anchor=tk.W, pady=1)

        # ---- Coluna 3: HTTP Avançados ----
        col3 = tk.Frame(parent, bg=c['bg_dark'])
        col3.pack(side=tk.LEFT, anchor=tk.N, padx=8, pady=5)

        self.create_section_label(col3, "🌐 FILTROS HTTP AVANÇADOS")
        http_frame = tk.Frame(col3, bg=c['bg_dark'])
        http_frame.pack(fill=tk.X, padx=5, pady=2)

        self.http_filter_vars = {}
        http_filters = [
            ("POST Requests (Formulários)", "post", True),
            ("GET Requests", "get", False),
            ("Login/Senha (Credenciais)", "login", True),
            ("Cookies", "cookie", True),
            ("Form Data (urlencoded)", "form", True),
            ("JSON Data", "json_data", True),
            ("Authorization Headers", "auth", True),
            ("Set-Cookie (Respostas)", "setcookie", True),
        ]
        for text, key, default in http_filters:
            var = tk.BooleanVar(value=default)
            self.http_filter_vars[key] = var
            tk.Checkbutton(http_frame, text=text, variable=var,
                           bg=c['bg_dark'], fg=c['accent2'],
                           selectcolor=c['bg_medium'],
                           activebackground=c['bg_dark'],
                           font=('Consolas', 9)).pack(anchor=tk.W, pady=1)

        # ---- Coluna 4: TLS + Destino ----
        col4 = tk.Frame(parent, bg=c['bg_dark'])
        col4.pack(side=tk.LEFT, anchor=tk.N, padx=8, pady=5)

        self.create_section_label(col4, "🔒 FILTROS TLS/HTTPS")
        tls_frame = tk.Frame(col4, bg=c['bg_dark'])
        tls_frame.pack(fill=tk.X, padx=5, pady=2)

        self.tls_filter_vars = {}
        for text, key, default in [
                ("TLS Handshake (SNI)", "sni", False),
                ("TLS Client Hello", "client_hello", False),
                ("Certificados", "certs", False)]:
            var = tk.BooleanVar(value=default)
            self.tls_filter_vars[key] = var
            tk.Checkbutton(tls_frame, text=text, variable=var,
                           bg=c['bg_dark'], fg=c['https'],
                           selectcolor=c['bg_medium'],
                           activebackground=c['bg_dark'],
                           font=('Consolas', 9)).pack(anchor=tk.W, pady=1)

        self.create_section_label(col4, "🎯 DOMÍNIO / IP")
        dest_frame = tk.Frame(col4, bg=c['bg_dark'])
        dest_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(dest_frame, text="Domínio (ex: exemplo.com.br):",
                 bg=c['bg_dark'], fg=c['text_dim'],
                 font=('Consolas', 8)).pack(anchor=tk.W)
        self.domain_filter = tk.Entry(
            dest_frame, bg=c['bg_medium'], fg=c['text'],
            insertbackground=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, width=28)
        self.domain_filter.pack(fill=tk.X, pady=1)

        tk.Label(dest_frame, text="IP de origem/destino:",
                 bg=c['bg_dark'], fg=c['text_dim'],
                 font=('Consolas', 8)).pack(anchor=tk.W)
        self.ip_filter = tk.Entry(
            dest_frame, bg=c['bg_medium'], fg=c['text'],
            insertbackground=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, width=28)
        self.ip_filter.pack(fill=tk.X, pady=1)

        tk.Label(dest_frame, text="Porta customizada:",
                 bg=c['bg_dark'], fg=c['text_dim'],
                 font=('Consolas', 8)).pack(anchor=tk.W)
        self.port_filter = tk.Entry(
            dest_frame, bg=c['bg_medium'], fg=c['text'],
            insertbackground=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, width=28)
        self.port_filter.pack(fill=tk.X, pady=1)
        self.port_filter.insert(0, "Ex: 8080,8443,3000")

        # ---- Coluna 5: Busca + Palavras-chave ----
        col5 = tk.Frame(parent, bg=c['bg_dark'])
        col5.pack(side=tk.LEFT, anchor=tk.N, padx=8, pady=5)

        self.create_section_label(col5, "🔎 BUSCA NO CONTEÚDO")
        search_frame = tk.Frame(col5, bg=c['bg_dark'])
        search_frame.pack(fill=tk.X, padx=5, pady=2)

        self.search_filter = tk.Entry(
            search_frame, bg=c['bg_medium'], fg=c['text'],
            insertbackground=c['text'], font=('Consolas', 10),
            relief=tk.FLAT, width=28)
        self.search_filter.pack(fill=tk.X, pady=2)
        self.search_filter.insert(0, "Ex: password, token, sessão")

        self.create_section_label(col5, "⚠️ PALAVRAS-CHAVE SENSÍVEIS")
        keywords_frame = tk.Frame(col5, bg=c['bg_dark'])
        keywords_frame.pack(fill=tk.X, padx=5, pady=2)

        self.keywords_text = tk.Text(
            keywords_frame, height=6, width=32, bg=c['bg_medium'],
            fg=c['warning'], insertbackground=c['text'],
            font=('Consolas', 9), relief=tk.FLAT)
        self.keywords_text.pack(fill=tk.X, pady=2)
        self.keywords_text.insert(
            "1.0",
            "password,passwd,pass,pwd,senha,login,user,username,"
            "usuario,email,token,session,cookie,auth,credit,card,"
            "cpf,cnpj,secret,api_key")

    # ==================== TOGGLE DE FILTROS (SEM ERRO) ====================
    def toggle_filters(self):
        """Oculta/mostra o painel de filtros.
        Usa pack_forget()/pack() — compatível com qualquer Tk."""
        if self.filters_visible:
            try:
                h = self.top_frame.winfo_height()
                if h > 50:
                    self.saved_height = h
            except Exception:
                self.saved_height = 420
            self.top_frame.pack_forget()
            self.filters_visible = False
            self.eye_btn.config(fg=self.colors['text_dim'])
            self.eye_btn2.config(fg=self.colors['text_dim'])
            self.status_label.config(
                text="Filtros ocultos — clique no 👁️ para mostrar")
        else:
            self.top_frame.configure(height=self.saved_height)
            self.top_frame.pack(fill=tk.X, padx=5,
                                before=self.results_frame)
            self.top_frame.pack_propagate(False)
            self.filters_visible = True
            self.eye_btn.config(fg=self.colors['accent2'])
            self.eye_btn2.config(fg=self.colors['accent2'])
            self.status_label.config(text="Filtros visíveis")

    def create_section_label(self, parent, text):
        frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.X, padx=5, pady=(6, 2))
        tk.Label(frame, text=text, bg=self.colors['bg_dark'],
                 fg=self.colors['accent'],
                 font=('Consolas', 10, 'bold')).pack(anchor=tk.W)
        tk.Frame(frame, bg=self.colors['accent'],
                 height=1).pack(fill=tk.X, pady=2)

    # ==================== UTILITÁRIOS ====================
    def get_interfaces(self):
        interfaces = []
        try:
            result = subprocess.run(['ip', 'link', 'show'],
                                    capture_output=True, text=True,
                                    timeout=5)
            for line in result.stdout.split('\n'):
                match = re.match(r'^\d+:\s+(\S+):', line)
                if match and match.group(1) != 'lo':
                    interfaces.append(match.group(1))
        except Exception:
            try:
                interfaces = [i for i in os.listdir('/sys/class/net/')
                              if i != 'lo']
            except Exception:
                pass
        return interfaces or ["eth0"]

    def refresh_interfaces(self):
        interfaces = self.get_interfaces()
        self.iface_combo['values'] = interfaces
        self.log_live(
            f"🔄 Interfaces atualizadas: {', '.join(interfaces)}\n", 'info')

    # ==================== CAPTURA ====================
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
            limit = int(self.packet_limit.get())
            if limit > 0:
                cmd.extend(['-c', str(limit)])
        except ValueError:
            pass

        port_map = {
            'http': '80', 'https': '443', 'dns': '53', 'ftp': '21',
            'smtp': '25 or port 587', 'pop3': '110', 'imap': '143',
            'ssh': '22', 'telnet': '23', 'mysql': '3306', 'pgsql': '5432',
        }
        port_filters = []
        for key, var in self.filter_vars.items():
            if var.get() and key in port_map:
                port_val = port_map[key]
                if 'or' in port_val:
                    port_filters.append(f'(port {port_val})')
                else:
                    port_filters.append(f'port {port_val}')

        custom_ports = self.port_filter.get().strip()
        if custom_ports and not custom_ports.startswith("Ex:"):
            for port in custom_ports.split(','):
                port = port.strip()
                if port.isdigit():
                    port_filters.append(f'port {port}')

        bpf_parts = []
        if port_filters:
            bpf_parts.append('(' + ' or '.join(port_filters) + ')')
        ip_filter = self.ip_filter.get().strip()
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

        self.cmd_output.delete("1.0", tk.END)
        self.cmd_output.insert(tk.END, "Comando executado:\n\n"
                               + ' '.join(cmd) + "\n\n" + "=" * 60 + "\n\n")

        self.is_capturing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_indicator.config(text="⬤ CAPTURANDO",
                                     fg=self.colors['success'])
        self.status_label.config(text="Capturando pacotes...")
        self.update_quick_button()

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_live("\n" + "=" * 70 + "\n", 'separator')
        self.log_live(f"🚀 CAPTURA INICIADA - {now}\n", 'warning')
        self.log_live(f"   Interface: {self.interface_var.get()}\n", 'info')
        self.log_live("=" * 70 + "\n\n", 'separator')

        threading.Thread(target=self.capture_packets, args=(cmd,),
                         daemon=True).start()

    def capture_packets(self, cmd):
        try:
            self.tcpdump_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, preexec_fn=os.setsid)

            current_packet = []
            for line in iter(self.tcpdump_process.stdout.readline, ''):
                if not self.is_capturing:
                    break
                if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', line):
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
        self.root.after(0, lambda pd=packet_data: self.raw_output.insert(
            tk.END, pd + "\n" + "-" * 50 + "\n"))

        data_lower = packet_data.lower()

        domain = self.domain_filter.get().strip().lower()
        if domain and domain not in data_lower:
            return
        search = self.search_filter.get().strip().lower()
        if (search and not search.startswith("ex:")
                and search not in data_lower):
            return

        is_http = False

        # POST
        if self.http_filter_vars['post'].get() and 'POST ' in packet_data:
            is_http = True
            self.stats['POST'] += 1
            host = self._extract_field(packet_data, r'Host:\s*(\S+)')
            uri = self._extract_field(packet_data, r'POST\s+(\S+)')
            ct = self._extract_field(packet_data, r'Content-Type:\s*(.+)')
            self.captured_http_requests.append({
                'time': datetime.datetime.now().strftime('%H:%M:%S'),
                'method': 'POST', 'host': host or 'N/A',
                'uri': uri or 'N/A', 'content_type': ct or 'N/A'})
            self.root.after(0, lambda pd=packet_data: self.log_post(pd))

        # GET
        if (self.http_filter_vars['get'].get()
                and 'GET ' in packet_data and 'POST ' not in packet_data):
            is_http = True
            self.stats['GET'] += 1
            host = self._extract_field(packet_data, r'Host:\s*(\S+)')
            uri = self._extract_field(packet_data, r'GET\s+(\S+)')
            self.captured_http_requests.append({
                'time': datetime.datetime.now().strftime('%H:%M:%S'),
                'method': 'GET', 'host': host or 'N/A',
                'uri': uri or 'N/A', 'content_type': 'N/A'})
            self.root.after(0, lambda pd=packet_data: self.log_get(pd))

        # Cookies
        if self.http_filter_vars['cookie'].get():
            m = re.search(r'Cookie:\s*(.+)', packet_data, re.I)
            if m:
                is_http = True
                self.stats['Cookies'] += 1
                host = self._extract_field(packet_data, r'Host:\s*(\S+)')
                self.captured_cookies.append({
                    'time': datetime.datetime.now().strftime('%H:%M:%S'),
                    'type': 'Cookie', 'host': host or 'N/A',
                    'value': m.group(1).strip()[:500]})
                self.root.after(0, lambda cm=m.group(1), pd=packet_data:
                                self.log_cookie(cm, pd))

        # Set-Cookie
        if self.http_filter_vars['setcookie'].get():
            m = re.search(r'Set-Cookie:\s*(.+)', packet_data, re.I)
            if m:
                is_http = True
                self.stats['Set-Cookies'] += 1
                self.captured_cookies.append({
                    'time': datetime.datetime.now().strftime('%H:%M:%S'),
                    'type': 'Set-Cookie', 'host': 'N/A',
                    'value': m.group(1).strip()[:500]})
                self.root.after(0, lambda sc=m.group(1):
                                self.log_setcookie(sc))

        # Form / JSON / Auth
        if (self.http_filter_vars['form'].get()
                and 'application/x-www-form-urlencoded' in data_lower):
            is_http = True
            self.stats['Form Data'] += 1
            self.root.after(0, lambda pd=packet_data: self.log_form(pd))

        if (self.http_filter_vars['json_data'].get()
                and 'application/json' in data_lower):
            is_http = True
            self.stats['JSON'] += 1
            self.root.after(0, lambda pd=packet_data: self.log_json(pd))

        if self.http_filter_vars['auth'].get():
            m = re.search(r'Authorization:\s*(.+)', packet_data, re.I)
            if m:
                is_http = True
                self.stats['Auth Headers'] += 1
                self.captured_auth_tokens.append({
                    'time': datetime.datetime.now().strftime('%H:%M:%S'),
                    'value': m.group(1).strip()[:500],
                    'host': self._extract_field(
                        packet_data, r'Host:\s*(\S+)') or 'N/A'})
                self.root.after(0, lambda am=m.group(1): self.log_auth(am))

        # Credenciais
        if self.http_filter_vars['login'].get():
            keywords = [k.strip().lower() for k in (
                self.keywords_text.get("1.0", tk.END).strip().split(','))
                if k.strip()]
            for keyword in keywords:
                if keyword in data_lower:
                    for pattern in [
                            rf'{keyword}[=:]\s*([^\s&"\'<>]+)',
                            rf'"{keyword}"\s*:\s*"([^"]+)"']:
                        m = re.search(pattern, packet_data, re.I)
                        if m:
                            is_http = True
                            self.stats['Credentials'] += 1
                            host = self._extract_field(
                                packet_data, r'Host:\s*(\S+)')
                            uri = self._extract_field(
                                packet_data, r'(?:POST|GET)\s+(\S+)')
                            self.captured_credentials.append({
                                'time': datetime.datetime.now().strftime(
                                    '%H:%M:%S'),
                                'field': keyword,
                                'value': m.group(1)[:200],
                                'host': host or 'N/A',
                                'uri': uri or 'N/A'})
                            self.root.after(0, lambda k=keyword,
                                            v=m.group(1), pd=packet_data:
                                            self.log_credential(k, v, pd))
                            break

        # TLS/SNI
        if self.tls_filter_vars['sni'].get():
            if '.443' in packet_data or 'https' in data_lower:
                for d in re.findall(
                        r'([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?'
                        r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?)*'
                        r'\.[a-zA-Z]{2,})', packet_data):
                    if len(d) > 5:
                        self.stats['SNI/DNS'] += 1
                        self.captured_dns.append({
                            'time': datetime.datetime.now().strftime(
                                '%H:%M:%S'),
                            'type': 'TLS SNI', 'query': d})
                        self.root.after(0, lambda dn=d, pd=packet_data:
                                        self.log_sni(dn, pd))
                        break

        # DNS
        if self.filter_vars['dns'].get():
            m = re.search(r'(?:A\?|AAAA\?|PTR\?)\s+(\S+)', packet_data)
            if m or ('.53' in packet_data and ' A?' in packet_data):
                if m:
                    self.stats['DNS'] += 1
                    self.captured_dns.append({
                        'time': datetime.datetime.now().strftime('%H:%M:%S'),
                        'type': 'DNS Query', 'query': m.group(1)})
                    self.root.after(0, lambda dm=m.group(1), pd=packet_data:
                                    self.log_dns(dm, pd))

        if is_http:
            self.filtered_count += 1
            self.root.after(0, lambda: self.filtered_count_label.config(
                text=f"Filtrados: {self.filtered_count}"))

    def _extract_field(self, data, pattern):
        m = re.search(pattern, data, re.I)
        return m.group(1).strip() if m else None

    # ==================== LOGS ====================
    def log_live(self, text, tag=None):
        self.live_output.insert(tk.END, text, tag)
        self.live_output.see(tk.END)

    def log_post(self, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n{'─' * 60}\n[{ts}] ", 'timestamp')
        self.log_live("🔴 HTTP POST REQUEST\n", 'http_post')
        uri = re.search(r'POST\s+(\S+)', data)
        if uri:
            self.log_live(f"   URI: {uri.group(1)}\n", 'http_post')
        host = re.search(r'Host:\s*(\S+)', data, re.I)
        if host:
            self.log_live(f"   Host: {host.group(1)}\n", 'header')
        ct = re.search(r'Content-Type:\s*(.+)', data, re.I)
        if ct:
            self.log_live(f"   Content-Type: {ct.group(1).strip()}\n", 'info')
        if self.verbose_var.get():
            started = False
            for line in data.split('\n'):
                if not line.strip() and not started:
                    started = True
                    continue
                if started and line.strip():
                    self.log_live(f"   📦 Payload: {line.strip()}\n", 'form')

    def log_get(self, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live("🟢 HTTP GET ", 'http_get')
        uri = re.search(r'GET\s+(\S+)', data)
        if uri:
            self.log_live(f"{uri.group(1)}\n", 'http_get')
        host = re.search(r'Host:\s*(\S+)', data, re.I)
        if host:
            self.log_live(f"   Host: {host.group(1)}\n", 'header')

    def log_cookie(self, cookie_data, packet_data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n[{ts}] ", 'timestamp')
        self.log_live(f"🍪 COOKIE: {cookie_data.strip()}\n", 'cookie')
        host = re.search(r'Host:\s*(\S+)', packet_data, re.I)
        self.cookie_output.insert(
            tk.END, f"[{ts}] {'─' * 40}\n  Host: "
            f"{host.group(1) if host else 'N/A'}\n"
            f"  Cookie: {cookie_data.strip()}\n\n")
        self.cookie_output.see(tk.END)

    def log_setcookie(self, cookie_data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live(f"🍪 SET-COOKIE: {cookie_data.strip()}\n", 'cookie')
        self.cookie_output.insert(
            tk.END, f"[{ts}] SET-COOKIE:\n  {cookie_data.strip()}\n\n")
        self.cookie_output.see(tk.END)

    def log_form(self, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live("📝 FORM DATA DETECTED\n", 'form')
        for line in data.split('\n'):
            if '=' in line and '&' in line and 'HTTP' not in line:
                for pair in line.strip().split('&'):
                    if '=' in pair:
                        key, _, value = pair.partition('=')
                        self.log_live(f"   📋 {key} = {value}\n", 'form')

    def log_json(self, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live("📦 JSON DATA\n", 'info')
        m = re.search(r'(\{[^}]+\})', data)
        if m:
            try:
                self.log_live(
                    f"   {json.dumps(json.loads(m.group(1)), indent=2)}\n",
                    'info')
            except json.JSONDecodeError:
                self.log_live(f"   {m.group(1)}\n", 'info')

    def log_auth(self, auth_data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n[{ts}] ", 'timestamp')
        self.log_live(f"🔐 AUTHORIZATION: {auth_data.strip()}\n",
                      'credential')
        if 'Basic' in auth_data:
            try:
                import base64
                encoded = auth_data.split('Basic')[1].strip()
                decoded = base64.b64decode(encoded).decode(
                    'utf-8', errors='ignore')
                self.log_live(f"   ⚠️  Decoded: {decoded}\n", 'credential')
                self.cred_output.insert(
                    tk.END, f"\n[{ts}] BASIC AUTH DECODED:\n"
                    f"  Raw: {auth_data.strip()}\n"
                    f"  Decoded: {decoded}\n\n", 'alert')
                self.cred_output.see(tk.END)
            except Exception:
                pass
        if 'Bearer' in auth_data:
            self.log_live("   🎫 Token Bearer detectado\n", 'warning')
            self.cred_output.insert(
                tk.END, f"\n[{ts}] BEARER TOKEN:\n  {auth_data.strip()}\n\n")
            self.cred_output.see(tk.END)

    def log_credential(self, keyword, value, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"\n{'⚠️ ' * 20}\n[{ts}] ", 'timestamp')
        self.log_live("🔑 CREDENCIAL DETECTADA!\n", 'credential')
        self.log_live(f"   Campo: {keyword}\n   Valor: {value}\n",
                      'credential')
        host = re.search(r'Host:\s*(\S+)', data, re.I)
        uri = re.search(r'(?:POST|GET)\s+(\S+)', data)
        if host:
            self.log_live(f"   Host: {host.group(1)}\n", 'header')
        if uri:
            self.log_live(f"   URI: {uri.group(1)}\n", 'header')
        self.log_live(f"{'⚠️ ' * 20}\n\n", 'warning')

        self.cred_output.insert(tk.END, f"\n{'🚨' * 25}\n", 'alert')
        self.cred_output.insert(
            tk.END, f"[{ts}] CREDENCIAL CAPTURADA!\n  Campo: {keyword}\n"
            f"  Valor: {value}\n  Host: "
            f"{host.group(1) if host else 'N/A'}\n  URI: "
            f"{uri.group(1) if uri else 'N/A'}\n")
        self.cred_output.insert(tk.END, f"{'🚨' * 25}\n\n", 'alert')
        self.cred_output.see(tk.END)
        self.root.after(0, lambda: self.cred_count_label.config(
            text=f"🔑 Credenciais: {self.stats['Credentials']}"))

    def log_sni(self, domain, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live(f"🔒 TLS/SNI: {domain}\n", 'sni')
        self.dns_output.insert(tk.END, f"[{ts}] 🔒 TLS SNI: {domain}\n")
        self.dns_output.see(tk.END)

    def log_dns(self, query, data):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_live(f"[{ts}] ", 'timestamp')
        self.log_live(f"🌍 DNS Query: {query}\n", 'dns')
        self.dns_output.insert(tk.END, f"[{ts}] 🌍 DNS: {query}\n")
        self.dns_output.see(tk.END)

    # ==================== INICIAR/PARAR ====================
    def toggle_capture(self):
        if self.is_capturing:
            self.stop_capture()
        else:
            self.start_capture()

    def update_quick_button(self):
        if self.is_capturing:
            self.quick_capture_btn.config(text="⏹ PARAR",
                                          bg=self.colors['error'],
                                          fg='white')
        else:
            self.quick_capture_btn.config(text="▶ INICIAR",
                                          bg=self.colors['success'],
                                          fg='black')

    def stop_capture(self):
        self.is_capturing = False
        self.capture_end_time = datetime.datetime.now()
        if self.tcpdump_process:
            try:
                os.killpg(os.getpgid(self.tcpdump_process.pid),
                          signal.SIGTERM)
            except Exception:
                try:
                    self.tcpdump_process.terminate()
                    self.tcpdump_process.kill()
                except Exception:
                    pass

    def capture_stopped(self):
        self.is_capturing = False
        if not self.capture_end_time:
            self.capture_end_time = datetime.datetime.now()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(text="⬤ PARADO",
                                     fg=self.colors['error'])
        self.status_label.config(text="Captura finalizada")
        self.update_quick_button()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_live(f"\n{'=' * 70}\n", 'separator')
        self.log_live(f"⏹ CAPTURA FINALIZADA - {now}\n", 'warning')
        self.log_live(f"   Total de pacotes: {self.packet_count}\n", 'info')
        self.log_live(
            f"   Credenciais: {self.stats.get('Credentials', 0)}\n",
            'credential')
        self.log_live(f"{'=' * 70}\n", 'separator')

    def clear_output(self):
        for w in (self.live_output, self.cred_output, self.cookie_output,
                  self.dns_output, self.raw_output, self.cmd_output):
            w.delete("1.0", tk.END)
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

    # ==================== RELATÓRIO HTML ====================
    def save_capture_html(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html")],
            title="Salvar Relatório HTML",
            initialfile=f"network_capture_"
                        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        f".html")
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self._generate_html_report())
            messagebox.showinfo("✅ Sucesso",
                                f"Relatório salvo!\n\n{filename}")
        except Exception as e:
            messagebox.showerror("❌ Erro",
                                 f"Erro ao salvar relatório:\n{str(e)}")

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

    # ==================== STATS ====================
    def show_stats(self):
        win = tk.Toplevel(self.root)
        win.title("📊 Estatísticas de Captura")
        win.geometry("500x600")
        win.configure(bg=self.colors['bg_dark'])
        tk.Label(win, text="📊 ESTATÍSTICAS", font=('Consolas', 16, 'bold'),
                 fg=self.colors['accent'],
                 bg=self.colors['bg_dark']).pack(pady=15)
        txt = scrolledtext.ScrolledText(
            win, bg=self.colors['bg_medium'], fg=self.colors['text'],
            font=('Consolas', 11), relief=tk.FLAT, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        txt.insert(tk.END, f"{'═' * 45}\n  RESUMO DA CAPTURA\n"
                   f"{'═' * 45}\n\n")
        txt.insert(tk.END,
                   f"  📡 Total de Pacotes:  {self.packet_count}\n"
                   f"  🔍 Filtrados:         {self.filtered_count}\n\n"
                   f"{'─' * 45}\n  DETALHAMENTO\n{'─' * 45}\n\n")
        icons = {'POST': '🔴', 'GET': '🟢', 'Cookies': '🍪',
                 'Set-Cookies': '🍪', 'Form Data': '📝', 'JSON': '📦',
                 'Auth Headers': '🔐', 'Credentials': '🔑',
                 'SNI/DNS': '🔒', 'DNS': '🌍'}
        for key, count in sorted(self.stats.items(),
                                 key=lambda x: x[1], reverse=True):
            icon = icons.get(key, '📊')
            bar = '█' * min(count, 30) + '░' * max(0, 30 - count)
            txt.insert(tk.END,
                       f"  {icon} {key:20s} {count:5d}  {bar}\n")
        if not self.stats:
            txt.insert(tk.END, "  Inicie uma captura primeiro.\n")
        txt.config(state=tk.DISABLED)

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
        print("   Execute: sudo python3 Network_Sniffer.py")
        print("=" * 60 + "\n")
    try:
        subprocess.run(['which', 'tcpdump'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ tcpdump não encontrado! Instale com:")
        print("   sudo apt install tcpdump")
        sys.exit(1)

    root = tk.Tk()
    app = NetworkSnifferGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
