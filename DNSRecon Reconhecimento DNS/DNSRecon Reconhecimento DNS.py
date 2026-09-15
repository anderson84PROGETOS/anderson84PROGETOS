#!/usr/bin/env python3
"""
DNSRecon GUI - Ferramenta de Reconhecimento DNS em Modo Gráfico
(Combobox Dark Fix + 5 Threads Padrão)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import socket
import threading
import os
import random
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import platform

try:
    import dns.resolver
    import dns.zone
    import dns.reversename
    import dns.query
    import dns.message
    import dns.rdatatype
    import dns.flags
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False


class DNSReconGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DNSRecon Reconhecimento DNS")
        self.root.geometry("1300x900")
        self.root.minsize(1050, 750)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        # Motor e controle
        self.is_running = False
        self.results = []
        self.stop_event = threading.Event()
        self.resolver = None

        # Progresso real thread-safe
        self.progress_lock = threading.Lock()
        self.total_tasks = 1
        self.completed_tasks = 0

        # Wordlist padrão
        self.default_subdomains = [
            'www', 'mail', 'ftp', 'smtp', 'pop', 'imap', 'webmail',
            'ns', 'ns1', 'ns2', 'ns3', 'dns', 'dns1', 'dns2',
            'mx', 'mx1', 'mx2', 'relay', 'email',
            'vpn', 'remote', 'gateway', 'gw', 'proxy',
            'admin', 'administrator', 'panel', 'cpanel', 'whm',
            'api', 'app', 'apps', 'dev', 'development', 'staging',
            'test', 'testing', 'stage', 'prod', 'production',
            'web', 'web1', 'web2', 'www1', 'www2',
            'db', 'database', 'mysql', 'postgres', 'sql', 'mongo',
            'redis', 'cache', 'memcached', 'elasticsearch',
            'cdn', 'static', 'assets', 'media', 'images', 'img',
            'blog', 'forum', 'wiki', 'docs', 'doc', 'help', 'support',
            'shop', 'store', 'portal', 'intranet', 'extranet',
            'cloud', 'server', 'host', 'hosting', 'node',
            'ssh', 'sftp', 'git', 'svn', 'jenkins', 'ci', 'cd',
            'monitor', 'monitoring', 'nagios', 'zabbix', 'grafana',
            'log', 'logs', 'syslog', 'elk', 'kibana',
            'ldap', 'ad', 'dc', 'exchange', 'owa', 'autodiscover',
            'backup', 'bak', 'old', 'new', 'legacy',
            'firewall', 'fw', 'router', 'switch',
            'sip', 'voip', 'pbx', 'asterisk',
            'm', 'mobile', 'wap',
            'secure', 'ssl', 'tls', 'https',
            'auth', 'login', 'sso', 'oauth',
            'status', 'health', 'ping',
            'demo', 'sandbox', 'lab', 'internal',
            'crm', 'erp', 'hr', 'finance',
            'analytics', 'stats', 'metrics',
            'download', 'downloads', 'upload', 'uploads',
            'file', 'files', 'share', 'nas', 'storage',
            's3', 'bucket', 'aws', 'azure', 'gcp',
            'docker', 'k8s', 'kubernetes', 'container',
            'proxy1', 'proxy2', 'lb', 'loadbalancer',
            'ws', 'websocket', 'socket', 'realtime',
            'beta', 'alpha', 'canary', 'preview',
        ]

        # Cores do tema escuro (Tokyonight)
        self.colors = {
            'bg':       '#1a1b26',
            'fg':       '#c0caf5',
            'accent':   '#7aa2f7',
            'accent2':  '#9ece6a',
            'warning':  '#e0af68',
            'error':    '#f7768e',
            'surface':  '#24283b',
            'surface2': '#414868',
            'text':     '#c0caf5',
            'subtext':  '#565f89',
            'green':    '#9ece6a',
            'red':      '#f7768e',
            'yellow':   '#e0af68',
            'blue':     '#7aa2f7',
            'purple':   '#bb9af7',
            'cyan':     '#7dcfff',
        }

        self.root.configure(bg=self.colors['bg'])
        self.setup_styles()
        self.build_gui()

        if not DNS_AVAILABLE:
            self.log("ERRO: Módulo 'dnspython' não encontrado", 'error')
            self.log("Instale com: pip install dnspython", 'error')
            self.start_btn.configure(state=tk.DISABLED)

    # ================================================================
    # ESTILOS
    # ================================================================
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab',
                        background=self.colors['surface'],
                        foreground=self.colors['fg'],
                        padding=[15, 5],
                        font=('Consolas', 10, 'bold'))
        style.map('TNotebook.Tab',
                  background=[('selected', self.colors['accent'])],
                  foreground=[('selected', '#1a1b26')])

        style.configure('Dark.TFrame',    background=self.colors['bg'])
        style.configure('Surface.TFrame', background=self.colors['surface'])

        style.configure('Dark.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['fg'],
                        font=('Consolas', 10))
        style.configure('Title.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['accent'],
                        font=('Consolas', 14, 'bold'))
        style.configure('Surface.TLabel',
                        background=self.colors['surface'],
                        foreground=self.colors['fg'],
                        font=('Consolas', 10))

        style.configure('Accent.TButton',
                        background=self.colors['accent'],
                        foreground='#1a1b26',
                        font=('Consolas', 10, 'bold'),
                        padding=[10, 5])
        style.map('Accent.TButton',
                  background=[('active', self.colors['accent2']),
                              ('disabled', self.colors['surface2'])])

        style.configure('Stop.TButton',
                        background=self.colors['error'],
                        foreground='white',
                        font=('Consolas', 10, 'bold'),
                        padding=[10, 5])
        style.map('Stop.TButton',
                  background=[('active', '#ff4060'),
                              ('disabled', self.colors['surface2'])])

        style.configure('Export.TButton',
                        background=self.colors['green'],
                        foreground='#1a1b26',
                        font=('Consolas', 9, 'bold'),
                        padding=[8, 4])
        style.map('Export.TButton',
                  background=[('active', '#b5e878')])

        style.configure('Dark.TCheckbutton',
                        background=self.colors['bg'],
                        foreground=self.colors['fg'],
                        font=('Consolas', 10))

        style.configure('Accent.Horizontal.TProgressbar',
                        background=self.colors['accent'],
                        troughcolor=self.colors['surface'])

        style.configure('Dark.TLabelframe',
                        background=self.colors['bg'],
                        foreground=self.colors['accent'])
        style.configure('Dark.TLabelframe.Label',
                        background=self.colors['bg'],
                        foreground=self.colors['accent'],
                        font=('Consolas', 10, 'bold'))

        # ---- Combobox Dark (texto legível, seta azul) ----
        style.configure(
            'Dark.TCombobox',
            fieldbackground=self.colors['surface'],
            background=self.colors['surface2'],
            foreground=self.colors['text'],
            arrowcolor=self.colors['accent'],
            font=('Consolas', 10, 'bold')
        )
        style.map(
            'Dark.TCombobox',
            fieldbackground=[
                ('readonly', self.colors['surface']),
                ('active',   self.colors['surface'])
            ],
            foreground=[
                ('readonly', self.colors['text']),
                ('active',   self.colors['text'])
            ],
            selectbackground=[
                ('readonly', self.colors['accent'])
            ],
            selectforeground=[
                ('readonly', '#1a1b26')
            ]
        )

        # ---- Spinbox Dark ----
        style.configure(
            'Dark.TSpinbox',
            fieldbackground=self.colors['surface'],
            background=self.colors['surface2'],
            foreground=self.colors['text'],
            arrowcolor=self.colors['accent'],
            font=('Consolas', 10)
        )
        style.map(
            'Dark.TSpinbox',
            fieldbackground=[
                ('active', self.colors['surface']),
                ('readonly', self.colors['surface'])
            ],
            foreground=[
                ('active', self.colors['text']),
                ('readonly', self.colors['text'])
            ]
        )

        style.configure('Dark.Treeview',
                        background=self.colors['surface'],
                        foreground=self.colors['fg'],
                        fieldbackground=self.colors['surface'],
                        font=('Consolas', 9),
                        rowheight=22)
        style.configure('Dark.Treeview.Heading',
                        background=self.colors['surface2'],
                        foreground=self.colors['accent'],
                        font=('Consolas', 10, 'bold'))
        style.map('Dark.Treeview',
                  background=[('selected', self.colors['accent'])],
                  foreground=[('selected', '#1a1b26')])

    # ================================================================
    # INTERFACE
    # ================================================================
    def build_gui(self):
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_banner(main_frame)
        self.create_input_frame(main_frame)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.create_console_tab()
        self.create_table_tab()
        self.create_options_tab()
        self.create_wordlist_tab()

        self.create_status_bar(main_frame)

    def create_banner(self, parent):
        banner_frame = ttk.Frame(parent, style='Dark.TFrame')
        banner_frame.pack(fill=tk.X, pady=(0, 5))

        banner = (
            "  ____  _   _ ____  ____                          \n"
            " |  _ \\| \\ | / ___||  _ \\ ___  ___ ___  _ __     \n"
            " | | | |  \\| \\___ \\| |_) / _ \\/ __/ _ \\| '_ \\   \n"
            " | |_| | |\\  |___) |  _ <  __/ (_| (_) | | | |   \n"
            " |____/|_| \\_|____/|_| \\_\\___|\\___\\___/|_| |_|   \n"
            "              Ferramenta de Enumeracao DNS v5.1    "
        )
        lbl = tk.Label(banner_frame, text=banner,
                       font=('Consolas', 9, 'bold'),
                       bg=self.colors['bg'],
                       fg=self.colors['cyan'],
                       justify=tk.LEFT)
        lbl.pack()

    def create_input_frame(self, parent):
        input_frame = ttk.Frame(parent, style='Dark.TFrame')
        input_frame.pack(fill=tk.X, pady=5)

        # ----- Linha 1 -----
        row1 = ttk.Frame(input_frame, style='Dark.TFrame')
        row1.pack(fill=tk.X, pady=3)

        ttk.Label(row1, text="Alvo:", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=(0, 5))

        self.target_var = tk.StringVar()
        self.target_entry = tk.Entry(
            row1, textvariable=self.target_var,
            bg=self.colors['surface'], fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 11), relief=tk.FLAT, width=35)
        self.target_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        self.target_entry.insert(0, "exemplo.com")
        self.target_entry.bind('<FocusIn>', self.on_entry_focus)
        self.target_entry.bind('<Return>', lambda e: self.start_scan())

        ttk.Label(row1, text="Tipo:", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=(10, 5))

        self.scan_type = tk.StringVar(value='all')
        scan_types = [
            'all', 'standard', 'records', 'bruteforce',
            'reverse', 'zone_transfer', 'cache_snoop'
        ]
        self.scan_combo = ttk.Combobox(
            row1, textvariable=self.scan_type, values=scan_types,
            style='Dark.TCombobox', width=14, state='readonly')
        self.scan_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Forçar cores do dropdown (lista aberta) no Windows/Linux
        self.root.option_add('*TCombobox*Listbox.background', self.colors['surface'])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors['text'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors['accent'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#1a1b26')
        self.root.option_add('*TCombobox*Listbox.font', 'Consolas 10')

        ttk.Label(row1, text="DNS:", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=(10, 5))

        self.dns_server_var = tk.StringVar(value='8.8.8.8')
        tk.Entry(
            row1, textvariable=self.dns_server_var,
            bg=self.colors['surface'], fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 11), relief=tk.FLAT, width=15
        ).pack(side=tk.LEFT, padx=(0, 10), ipady=3)

        # 5 Threads (padrão)
        ttk.Label(row1, text="Threads:", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=(10, 5))

        self.threads_var = tk.IntVar(value=5)
        threads_spin = ttk.Spinbox(
            row1, from_=1, to=100,
            textvariable=self.threads_var,
            style='Dark.TSpinbox', width=5)
        threads_spin.pack(side=tk.LEFT, padx=(0, 10))

        # ----- Linha 2 - Botões -----
        row2 = ttk.Frame(input_frame, style='Dark.TFrame')
        row2.pack(fill=tk.X, pady=3)

        self.start_btn = ttk.Button(
            row2, text="  INICIAR SCAN  ",
            style='Accent.TButton', command=self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=3)

        self.stop_btn = ttk.Button(
            row2, text="  PARAR  ",
            style='Stop.TButton', command=self.stop_scan,
            state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        self.clear_btn = ttk.Button(
            row2, text="  LIMPAR  ",
            style='Accent.TButton', command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=3)

        ttk.Label(row2, text="  |  ", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=5)
        ttk.Label(row2, text="Exportar:", style='Dark.TLabel').pack(
            side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            row2, text=" TXT ", style='Export.TButton',
            command=lambda: self.export_results('txt')
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            row2, text=" HTML ", style='Export.TButton',
            command=lambda: self.export_results('html')
        ).pack(side=tk.LEFT, padx=2)

    def create_console_tab(self):
        console_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(console_frame, text='  Console  ')

        self.console = scrolledtext.ScrolledText(
            console_frame,
            bg='#1a1b26', fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 10), wrap=tk.WORD,
            state=tk.DISABLED, relief=tk.FLAT,
            padx=10, pady=10,
            selectbackground=self.colors['accent'],
            selectforeground='#1a1b26')
        self.console.pack(fill=tk.BOTH, expand=True)

        self.console.tag_config('info',      foreground=self.colors['blue'])
        self.console.tag_config('success',   foreground=self.colors['green'])
        self.console.tag_config('warning',   foreground=self.colors['yellow'])
        self.console.tag_config('error',     foreground=self.colors['red'])
        self.console.tag_config('header',    foreground=self.colors['purple'],
                                font=('Consolas', 11, 'bold'))
        self.console.tag_config('result',    foreground=self.colors['cyan'])
        self.console.tag_config('separator', foreground=self.colors['subtext'])

    def create_table_tab(self):
        table_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(table_frame, text='  Resultados  ')

        filter_frame = ttk.Frame(table_frame, style='Dark.TFrame')
        filter_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(filter_frame, text="Filtrar tipo:",
                  style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))

        self.filter_var = tk.StringVar(value='Todos')
        filter_types = [
            'Todos', 'A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME',
            'SOA', 'SRV', 'PTR', 'CAA', 'DNSKEY', 'DMARC',
            'SPF', 'DKIM', 'AXFR', 'CACHE', 'WILDCARD'
        ]
        self.filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_var,
            values=filter_types, style='Dark.TCombobox',
            width=12, state='readonly')
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_combo.bind('<<ComboboxSelected>>', self.filter_table)

        ttk.Label(filter_frame, text="Pesquisar:",
                  style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_table)
        tk.Entry(
            filter_frame, textvariable=self.search_var,
            bg=self.colors['surface'], fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 10), relief=tk.FLAT, width=30
        ).pack(side=tk.LEFT, padx=(0, 15), ipady=2)

        self.count_label = ttk.Label(
            filter_frame, text="Total: 0", style='Dark.TLabel')
        self.count_label.pack(side=tk.RIGHT, padx=10)

        tree_frame = ttk.Frame(table_frame, style='Dark.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('tipo', 'nome', 'valor', 'ttl', 'info')
        self.tree = ttk.Treeview(
            tree_frame, columns=columns,
            show='headings', style='Dark.Treeview')

        self.tree.heading('tipo',  text='Tipo',           anchor=tk.W)
        self.tree.heading('nome',  text='Nome/Host',      anchor=tk.W)
        self.tree.heading('valor', text='Valor/IP',       anchor=tk.W)
        self.tree.heading('ttl',   text='TTL',            anchor=tk.W)
        self.tree.heading('info',  text='Info Adicional', anchor=tk.W)

        self.tree.column('tipo',  width=80,  minwidth=60)
        self.tree.column('nome',  width=250, minwidth=150)
        self.tree.column('valor', width=650, minwidth=150)
        self.tree.column('ttl',   width=80,  minwidth=50)
        self.tree.column('info',  width=350, minwidth=150)

        v_scroll = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree_menu = tk.Menu(
            self.tree, tearoff=0,
            bg=self.colors['surface'], fg=self.colors['fg'],
            activebackground=self.colors['accent'],
            activeforeground='#1a1b26')
        self.tree_menu.add_command(
            label="Copiar Valor", command=self.copy_tree_value)
        self.tree_menu.add_command(
            label="Copiar Linha", command=self.copy_tree_row)
        self.tree.bind('<Button-3>', self.show_tree_menu)

    def create_options_tab(self):
        options_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(options_frame, text='  Opcoes  ')

        canvas = tk.Canvas(
            options_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            options_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas, style='Dark.TFrame')

        scrollable.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        records_frame = ttk.LabelFrame(
            scrollable, text=" Tipos de Registro DNS ",
            style='Dark.TLabelframe')
        records_frame.pack(fill=tk.X, padx=10, pady=10)

        self.record_vars = {}
        record_types = [
            ('A', True), ('AAAA', True), ('MX', True), ('NS', True),
            ('TXT', True), ('CNAME', True), ('SOA', True), ('SRV', True),
            ('PTR', True), ('CAA', True), ('DNSKEY', False),
            ('NSEC', False), ('NSEC3', False), ('RRSIG', False),
            ('DS', False), ('TLSA', False), ('LOC', False),
            ('HINFO', False), ('NAPTR', False), ('SPF', True),
        ]

        row_frame = None
        for i, (rtype, default) in enumerate(record_types):
            if i % 5 == 0:
                row_frame = ttk.Frame(records_frame, style='Dark.TFrame')
                row_frame.pack(fill=tk.X, padx=10, pady=2)
            var = tk.BooleanVar(value=default)
            self.record_vars[rtype] = var
            ttk.Checkbutton(
                row_frame, text=rtype, variable=var,
                style='Dark.TCheckbutton').pack(side=tk.LEFT, padx=10)

        sel_frame = ttk.Frame(records_frame, style='Dark.TFrame')
        sel_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(
            sel_frame, text=" Selecionar Todos ",
            style='Accent.TButton',
            command=lambda: self.select_all_records(True)
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            sel_frame, text=" Desmarcar Todos ",
            style='Accent.TButton',
            command=lambda: self.select_all_records(False)
        ).pack(side=tk.LEFT, padx=5)

        scan_opts = ttk.LabelFrame(
            scrollable, text=" Opcoes de Scan ",
            style='Dark.TLabelframe')
        scan_opts.pack(fill=tk.X, padx=10, pady=10)

        opts_row = ttk.Frame(scan_opts, style='Dark.TFrame')
        opts_row.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(opts_row, text="Timeout:",
                  style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.timeout_var = tk.IntVar(value=5)
        ttk.Spinbox(
            opts_row, from_=1, to=30,
            textvariable=self.timeout_var,
            style='Dark.TSpinbox', width=5
        ).pack(side=tk.LEFT, padx=(0, 20))

        self.wildcard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opts_row, text="Verificar Wildcard",
            variable=self.wildcard_var,
            style='Dark.TCheckbutton').pack(side=tk.LEFT, padx=10)

        self.tcp_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row, text="Usar TCP",
            variable=self.tcp_var,
            style='Dark.TCheckbutton').pack(side=tk.LEFT, padx=10)

        brute_frame = ttk.LabelFrame(
            scrollable, text=" Opcoes de Brute Force ",
            style='Dark.TLabelframe')
        brute_frame.pack(fill=tk.X, padx=10, pady=10)

        bf_row = ttk.Frame(brute_frame, style='Dark.TFrame')
        bf_row.pack(fill=tk.X, padx=10, pady=5)

        self.bf_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            bf_row, text="Ativar Brute Force",
            variable=self.bf_enabled,
            style='Dark.TCheckbutton').pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(bf_row, text="Wordlist:",
                  style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.wordlist_path = tk.StringVar(value="(padrao interno)")
        tk.Entry(
            bf_row, textvariable=self.wordlist_path,
            bg=self.colors['surface'], fg=self.colors['fg'],
            font=('Consolas', 10), relief=tk.FLAT, width=30
        ).pack(side=tk.LEFT, padx=(0, 5), ipady=2)
        ttk.Button(
            bf_row, text="Abrir",
            command=self.browse_wordlist).pack(side=tk.LEFT)

        rev_frame = ttk.LabelFrame(
            scrollable, text=" Opcoes de Reverse Lookup ",
            style='Dark.TLabelframe')
        rev_frame.pack(fill=tk.X, padx=10, pady=10)

        rev_row = ttk.Frame(rev_frame, style='Dark.TFrame')
        rev_row.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(rev_row, text="Range IP (CIDR):",
                  style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.reverse_range = tk.StringVar()
        tk.Entry(
            rev_row, textvariable=self.reverse_range,
            bg=self.colors['surface'], fg=self.colors['fg'],
            font=('Consolas', 10), relief=tk.FLAT, width=25
        ).pack(side=tk.LEFT, padx=(0, 10), ipady=2)
        ttk.Label(rev_row, text="Ex: 192.168.1.0/24",
                  style='Dark.TLabel').pack(side=tk.LEFT)

    def create_wordlist_tab(self):
        wl_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(wl_frame, text='  Wordlist  ')

        ttk.Label(
            wl_frame,
            text="Lista de subdominios para Brute Force (um por linha):",
            style='Dark.TLabel').pack(anchor=tk.W, padx=10, pady=5)

        self.wordlist_text = scrolledtext.ScrolledText(
            wl_frame,
            bg=self.colors['surface'], fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 10), wrap=tk.WORD,
            relief=tk.FLAT, padx=10, pady=10,
            selectbackground=self.colors['accent'],
            selectforeground='#1a1b26')
        self.wordlist_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.wordlist_text.insert('1.0', '\n'.join(self.default_subdomains))

        btn_frame = ttk.Frame(wl_frame, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            btn_frame, text=" Carregar Arquivo ",
            style='Accent.TButton',
            command=self.load_wordlist).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame, text=" Salvar Wordlist ",
            style='Accent.TButton',
            command=self.save_wordlist).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame, text=" Restaurar Padrao ",
            style='Accent.TButton',
            command=self.reset_wordlist).pack(side=tk.LEFT, padx=5)

        self.wl_count_label = ttk.Label(
            btn_frame,
            text=f"Total: {len(self.default_subdomains)} palavras",
            style='Dark.TLabel')
        self.wl_count_label.pack(side=tk.RIGHT, padx=10)

    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent, style='Surface.TFrame')
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(
            status_frame, textvariable=self.status_var,
            style='Surface.TLabel').pack(side=tk.LEFT, padx=10, pady=5)

        self.progress_pct_var = tk.StringVar(value="0%")
        ttk.Label(
            status_frame, textvariable=self.progress_pct_var,
            style='Surface.TLabel').pack(side=tk.RIGHT, padx=(0, 10), pady=5)

        self.progress = ttk.Progressbar(
            status_frame, mode='determinate',
            style='Accent.Horizontal.TProgressbar', length=300)
        self.progress.pack(side=tk.RIGHT, padx=10, pady=5)

    # ================================================================
    # UTILITÁRIOS
    # ================================================================
    def on_entry_focus(self, event):
        if self.target_entry.get() == "exemplo.com":
            self.target_entry.delete(0, tk.END)

    def increment_progress(self):
        with self.progress_lock:
            self.completed_tasks += 1
            pct = min(100, int(
                (self.completed_tasks / max(self.total_tasks, 1)) * 100))
        self.root.after(0, self._update_progress_ui, pct)

    def _update_progress_ui(self, pct):
        self.progress['value'] = pct
        self.progress_pct_var.set(f"{pct}%")
        target = self.target_var.get().strip()
        self.status_var.set(f"Escaneando {target}...")

    def log(self, message, tag='info'):
        def _log():
            self.console.configure(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix_map = {
                'info': '[*]', 'success': '[+]', 'warning': '[!]',
                'error': '[-]', 'header': '[#]', 'result': '[>]',
                'separator': ''
            }
            prefix = prefix_map.get(tag, '[*]')
            if tag == 'separator':
                self.console.insert(tk.END, f"{message}\n", tag)
            else:
                self.console.insert(
                    tk.END,
                    f"[{timestamp}] {prefix} {message}\n", tag)
            self.console.see(tk.END)
            self.console.configure(state=tk.DISABLED)

        if threading.current_thread() is threading.main_thread():
            _log()
        else:
            self.root.after(0, _log)

    def add_result(self, record_type, name, value, ttl='', info=''):
        result = {
            'type':  str(record_type),
            'name':  str(name),
            'value': str(value),
            'ttl':   str(ttl),
            'info':  str(info)
        }
        self.results.append(result)
        self.root.after(0, self._insert_tree_item, result)

    def _insert_tree_item(self, result):
        self.tree.insert('', tk.END, values=(
            result['type'], result['name'],
            result['value'], result['ttl'], result['info']))
        self.count_label.config(text=f"Total: {len(self.results)}")

    def select_all_records(self, state):
        for var in self.record_vars.values():
            var.set(state)

    def browse_wordlist(self):
        fp = filedialog.askopenfilename(
            title="Selecionar Wordlist",
            filetypes=[("Text", "*.txt"), ("Todos", "*.*")])
        if fp:
            self.wordlist_path.set(fp)
            self.load_wordlist_from_file(fp)

    def load_wordlist(self):
        fp = filedialog.askopenfilename(
            title="Carregar Wordlist",
            filetypes=[("Text", "*.txt"), ("Todos", "*.*")])
        if fp:
            self.load_wordlist_from_file(fp)

    def load_wordlist_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.wordlist_text.delete('1.0', tk.END)
            self.wordlist_text.insert('1.0', content)
            words = [w.strip() for w in content.split('\n') if w.strip()]
            self.wl_count_label.config(text=f"Total: {len(words)} palavras")
            self.log(f"Wordlist carregada: {len(words)} palavras", 'success')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar: {e}")

    def save_wordlist(self):
        fp = filedialog.asksaveasfilename(
            title="Salvar Wordlist", defaultextension=".txt",
            filetypes=[("Text", "*.txt")])
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(self.wordlist_text.get('1.0', tk.END))
                self.log(f"Wordlist salva: {fp}", 'success')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def reset_wordlist(self):
        self.wordlist_text.delete('1.0', tk.END)
        self.wordlist_text.insert('1.0', '\n'.join(self.default_subdomains))
        self.wl_count_label.config(
            text=f"Total: {len(self.default_subdomains)} palavras")

    def filter_table(self, *args):
        ftype = self.filter_var.get()
        search = self.search_var.get().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for r in self.results:
            if ftype != 'Todos' and r['type'] != ftype:
                continue
            if search:
                hay = f"{r['name']} {r['value']} {r['info']}".lower()
                if search not in hay:
                    continue
            self.tree.insert('', tk.END, values=(
                r['type'], r['name'], r['value'], r['ttl'], r['info']))
            count += 1
        self.count_label.config(text=f"Total: {count}")

    def show_tree_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def copy_tree_value(self):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])['values']
            if vals:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(vals[2]))

    def copy_tree_row(self):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])['values']
            if vals:
                self.root.clipboard_clear()
                self.root.clipboard_append('\t'.join(str(v) for v in vals))

    def clear_results(self):
        self.console.configure(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.configure(state=tk.DISABLED)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results.clear()
        self.count_label.config(text="Total: 0")
        self.progress['value'] = 0
        self.progress_pct_var.set("0%")
        self.status_var.set("Pronto")

    def get_wordlist_from_text(self):
        content = self.wordlist_text.get('1.0', tk.END)
        return [w.strip() for w in content.split('\n')
                if w.strip() and not w.strip().startswith('#')]

    # ================================================================
    # EXPORTAÇÃO
    # ================================================================
    def export_results(self, fmt):
        if not self.results:
            messagebox.showwarning("Aviso", "Nenhum resultado para exportar")
            return

        exts = {'txt': '.txt', 'html': '.html'}
        fp = filedialog.asksaveasfilename(
            title=f"Exportar como {fmt.upper()}",
            defaultextension=exts[fmt],
            filetypes=[(f"{fmt.upper()} Files", f"*{exts[fmt]}")])
        if not fp:
            return

        try:
            if fmt == 'txt':
                self._export_txt(fp)
            elif fmt == 'html':
                self._export_html(fp)
            self.log(f"Exportado: {fp}", 'success')
            messagebox.showinfo("Sucesso", f"Exportado para:\n{fp}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    def _export_txt(self, fp):
        with open(fp, 'w', encoding='utf-8') as f:
            f.write("DNSRecon GUI - Relatório DNS\n")
            f.write(f"{'=' * 90}\n")
            f.write(f"Alvo: {self.target_var.get()}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total: {len(self.results)} registros\n")
            f.write(f"{'=' * 90}\n\n")
            f.write(f"{'Tipo':<10} {'Nome':<40} {'Valor':<45} "
                    f"{'TTL':<8} {'Info'}\n")
            f.write(f"{'-'*10} {'-'*40} {'-'*45} {'-'*8} {'-'*30}\n")
            for r in self.results:
                f.write(f"{r['type']:<10} {r['name']:<40} "
                        f"{r['value']:<45} {r['ttl']:<8} {r['info']}\n")

    def _export_html(self, fp):
        target = self.target_var.get()
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        badge_map = {
            'A': 'badge-a', 'AAAA': 'badge-aaaa', 'MX': 'badge-mx',
            'NS': 'badge-ns', 'TXT': 'badge-txt', 'CNAME': 'badge-cname',
            'SOA': 'badge-default', 'SRV': 'badge-default',
            'PTR': 'badge-default', 'CAA': 'badge-default',
            'AXFR': 'badge-axfr', 'WILDCARD': 'badge-wildcard',
            'DMARC': 'badge-txt', 'SPF': 'badge-txt',
            'DKIM': 'badge-txt', 'CACHE': 'badge-mx',
        }

        rows_html = ""
        for r in self.results:
            rt = r['type'].upper()
            bcls = badge_map.get(rt, 'badge-default')
            rows_html += f"""
                <tr>
                    <td><span class="badge {bcls}">{rt}</span></td>
                    <td>{r['name']}</td>
                    <td>{r['value']}</td>
                    <td>{r['ttl'] or '-'}</td>
                    <td>{r['info'] or '-'}</td>
                </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>DNSRecon - {target}</title>
<style>
body {{ font-family:'Segoe UI',sans-serif; background:#1a1b26;
       color:#c0caf5; margin:0; padding:30px; }}
.container {{ max-width:1200px; margin:0 auto; }}
h1 {{ color:#7aa2f7; margin:0 0 10px; }}
.meta {{ background:#24283b; padding:20px; border-radius:8px;
         border:1px solid #414868; margin-bottom:25px; }}
.meta div {{ margin:6px 0; }}
.meta strong {{ color:#7dcfff; }}
table {{ width:100%; border-collapse:collapse; background:#24283b;
         border-radius:8px; overflow:hidden; border:1px solid #414868; }}
th,td {{ padding:12px 16px; text-align:left; border-bottom:1px solid #414868; }}
th {{ background:#414868; color:#7aa2f7; font-weight:600;
     text-transform:uppercase; font-size:13px; }}
tr:hover {{ background:#2e344e; }}
.badge {{ display:inline-block; padding:3px 8px; border-radius:4px;
          font-weight:bold; font-size:11px; font-family:Consolas,monospace; }}
.badge-a {{ background:#9ece6a; color:#1a1b26; }}
.badge-aaaa {{ background:#73daca; color:#1a1b26; }}
.badge-mx {{ background:#7aa2f7; color:#1a1b26; }}
.badge-ns {{ background:#bb9af7; color:#1a1b26; }}
.badge-txt {{ background:#e0af68; color:#1a1b26; }}
.badge-cname {{ background:#0db9d7; color:#1a1b26; }}
.badge-axfr {{ background:#f7768e; color:#fff; }}
.badge-wildcard {{ background:#ff9e64; color:#1a1b26; }}
.badge-default {{ background:#565f89; color:#c0caf5; }}
</style>
</head>
<body>
<div class="container">
<h1>Relatório de Reconhecimento DNS</h1>
<div class="meta">
  <div>Alvo: <strong>{target}</strong></div>
  <div>Data: <strong>{date_str}</strong></div>
  <div>Total: <strong>{len(self.results)} registros</strong></div>
</div>
<table>
<thead><tr>
  <th>Tipo</th><th>Nome</th><th>Valor</th><th>TTL</th><th>Info</th>
</tr></thead>
<tbody>{rows_html}
</tbody></table>
</div></body></html>"""

        with open(fp, 'w', encoding='utf-8') as f:
            f.write(html)

    # ================================================================
    # CÁLCULO DE TAREFAS
    # ================================================================
    def _get_active_standard_records(self):
        standard = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA',
                     'SRV', 'CAA']
        return [r for r in standard
                if r not in self.record_vars or self.record_vars[r].get()]

    def _get_active_selected_records(self):
        return [rtype for rtype, var in self.record_vars.items()
                if var.get()]

    def _get_bruteforce_words(self):
        wl_path = self.wordlist_path.get()
        if wl_path != "(padrao interno)" and os.path.exists(wl_path):
            try:
                with open(wl_path, 'r', encoding='utf-8',
                          errors='ignore') as f:
                    return [l.strip() for l in f if l.strip()]
            except Exception:
                pass
        return self.get_wordlist_from_text()

    def _count_reverse_hosts(self, target):
        cidr = self.reverse_range.get().strip()
        if cidr:
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                return len(list(net.hosts()))
            except Exception:
                return 1
        return 14

    def calculate_total_tasks(self, target, scan_type):
        total = 0

        if scan_type in ('standard', 'all'):
            total += len(self._get_active_standard_records())
            total += 12  # DMARC + SPF + 9 DKIM + PTR

        if scan_type == 'records':
            total += len(self._get_active_selected_records())

        if scan_type == 'all':
            standard_set = set(self._get_active_standard_records())
            extras = [r for r in self._get_active_selected_records()
                      if r not in standard_set]
            total += len(extras)

        if scan_type in ('zone_transfer', 'all'):
            total += 3

        if scan_type in ('bruteforce', 'all'):
            if self.bf_enabled.get():
                total += len(self._get_bruteforce_words())

        if scan_type in ('reverse', 'all'):
            total += self._count_reverse_hosts(target)

        if scan_type in ('cache_snoop', 'all'):
            total += 22

        if self.wildcard_var.get():
            total += 1

        return max(total, 1)

    # ================================================================
    # CONTROLE DO SCAN
    # ================================================================
    def start_scan(self):
        target = self.target_var.get().strip()
        if not target or target == "exemplo.com":
            messagebox.showwarning("Aviso", "Insira um domínio alvo")
            return
        if not DNS_AVAILABLE:
            messagebox.showerror(
                "Erro",
                "dnspython não instalado\nExecute: pip install dnspython")
            return

        self.clear_results()
        self.is_running = True
        self.stop_event.clear()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        self.completed_tasks = 0
        self.progress['value'] = 0
        self.progress_pct_var.set("0%")
        self.status_var.set("Preparando scan...")

        t = threading.Thread(
            target=self.run_scan, args=(target,), daemon=True)
        t.start()

    def stop_scan(self):
        self.stop_event.set()
        self.is_running = False
        self.log("Scan interrompido pelo utilizador", 'warning')
        self.finish_scan()

    def finish_scan(self):
        self.root.after(0, self._finish_ui)

    def _finish_ui(self):
        self.is_running = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress['value'] = 100
        self.progress_pct_var.set("100%")
        self.status_var.set(
            f"Concluído — {len(self.results)} registros encontrados")

    def run_scan(self, target):
        try:
            scan_type = self.scan_type.get()
            dns_server = self.dns_server_var.get().strip()
            num_threads = self.threads_var.get()  # padrão 5

            self.resolver = dns.resolver.Resolver()
            self.resolver.nameservers = [dns_server]
            self.resolver.timeout = self.timeout_var.get()
            self.resolver.lifetime = self.timeout_var.get() * 2

            self.total_tasks = self.calculate_total_tasks(target, scan_type)

            self.log("=" * 65, 'separator')
            self.log("DNSRecon GUI v5.1 - Reconhecimento DNS", 'header')
            self.log("=" * 65, 'separator')
            self.log(f"Alvo       : {target}", 'info')
            self.log(f"DNS Server : {dns_server}", 'info')
            self.log(f"Scan Tipo  : {scan_type}", 'info')
            self.log(f"Threads    : {num_threads}", 'info')
            self.log(f"Timeout    : {self.timeout_var.get()}s", 'info')
            self.log(f"Tarefas    : {self.total_tasks}", 'info')
            self.log(f"Inicio     : "
                     f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 'info')
            self.log("-" * 65, 'separator')

            if scan_type in ('standard', 'all'):
                if not self.stop_event.is_set():
                    self.scan_standard_records(target)
                if not self.stop_event.is_set():
                    self.scan_additional_info(target)

            if scan_type == 'records':
                if not self.stop_event.is_set():
                    self.scan_selected_records(target)

            if scan_type == 'all':
                if not self.stop_event.is_set():
                    self.scan_extra_records(target)

            if scan_type in ('zone_transfer', 'all'):
                if not self.stop_event.is_set():
                    self.attempt_zone_transfer(target)

            if scan_type in ('bruteforce', 'all'):
                if not self.stop_event.is_set() and self.bf_enabled.get():
                    self.bruteforce_subdomains(target, num_threads)

            if scan_type in ('reverse', 'all'):
                if not self.stop_event.is_set():
                    self.reverse_lookup(target, num_threads)

            if scan_type in ('cache_snoop', 'all'):
                if not self.stop_event.is_set():
                    self.cache_snooping(target)

            if self.wildcard_var.get() and not self.stop_event.is_set():
                self.check_wildcard(target)

            self.log("-" * 65, 'separator')
            self.log(f"Scan concluído — {len(self.results)} registros "
                     f"encontrados", 'success')
            self.log(f"Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                     'info')
            self.log("=" * 65, 'separator')

        except Exception as e:
            self.log(f"Erro fatal durante scan: {e}", 'error')
        finally:
            self.root.after(0, self.finish_scan)

    # ================================================================
    # MÓDULOS DE SCAN
    # ================================================================
    def _query_record(self, target, rtype, context=""):
        if self.stop_event.is_set():
            return
        try:
            answers = self.resolver.resolve(target, rtype)
            for rdata in answers:
                ttl = answers.rrset.ttl
                info = context
                value = str(rdata)

                if rtype == 'MX':
                    info = f"Prioridade: {rdata.preference}"
                    value = str(rdata.exchange)
                elif rtype == 'SOA':
                    info = (f"Serial: {rdata.serial}, "
                            f"Refresh: {rdata.refresh}, "
                            f"Retry: {rdata.retry}")
                    value = f"MNAME: {rdata.mname}, RNAME: {rdata.rname}"
                elif rtype == 'SRV':
                    info = (f"Pri: {rdata.priority}, "
                            f"Peso: {rdata.weight}, "
                            f"Porta: {rdata.port}")
                    value = str(rdata.target)
                elif rtype == 'CAA':
                    info = f"Flags: {rdata.flags}, Tag: {rdata.tag}"
                    value = str(rdata.value)

                self.add_result(rtype, target, value, ttl, info)
                self.log(f"{rtype:>8} | {target} -> {value} "
                         f"(TTL:{ttl}) {info}", 'success')

        except dns.resolver.NoAnswer:
            self.log(f"{rtype:>8} | Sem resposta para {target}", 'warning')
        except dns.resolver.NXDOMAIN:
            self.log(f"{rtype:>8} | Domínio não existe: {target}", 'error')
        except dns.resolver.Timeout:
            self.log(f"{rtype:>8} | Timeout: {target}", 'warning')
        except dns.exception.DNSException as e:
            self.log(f"{rtype:>8} | Erro DNS: {e}", 'warning')
        except Exception as e:
            self.log(f"{rtype:>8} | Erro: {e}", 'error')
        finally:
            self.increment_progress()

    def scan_standard_records(self, target):
        self.log("\n[ REGISTROS DNS PADRÃO ]", 'header')
        self.log("-" * 45, 'separator')
        for rtype in self._get_active_standard_records():
            if self.stop_event.is_set():
                return
            self._query_record(target, rtype)

    def scan_selected_records(self, target):
        self.log("\n[ REGISTROS SELECIONADOS ]", 'header')
        self.log("-" * 45, 'separator')
        for rtype in self._get_active_selected_records():
            if self.stop_event.is_set():
                return
            self._query_record(target, rtype, "Selecionado")

    def scan_extra_records(self, target):
        standard_set = set(self._get_active_standard_records())
        extras = [r for r in self._get_active_selected_records()
                  if r not in standard_set]
        if not extras:
            return
        self.log("\n[ REGISTROS EXTRAS ]", 'header')
        self.log("-" * 45, 'separator')
        for rtype in extras:
            if self.stop_event.is_set():
                return
            self._query_record(target, rtype, "Extra")

    def scan_additional_info(self, target):
        if self.stop_event.is_set():
            return

        self.log("\n[ INFORMAÇÕES ADICIONAIS ]", 'header')
        self.log("-" * 45, 'separator')

        # DMARC
        try:
            dmarc_domain = f"_dmarc.{target}"
            answers = self.resolver.resolve(dmarc_domain, 'TXT')
            for rdata in answers:
                value = str(rdata).strip('"')
                if 'dmarc' in value.lower():
                    self.add_result(
                        'DMARC', dmarc_domain, value, '', 'Política DMARC')
                    self.log(f"   DMARC | {dmarc_domain} -> {value}",
                             'success')
        except Exception:
            self.log("   DMARC | Nenhum registro encontrado", 'warning')
        finally:
            self.increment_progress()

        # SPF
        try:
            answers = self.resolver.resolve(target, 'TXT')
            for rdata in answers:
                value = str(rdata).strip('"')
                if 'v=spf1' in value.lower():
                    self.add_result(
                        'SPF', target, value, '', 'Política SPF')
                    self.log(f"     SPF | {target} -> {value}", 'success')
        except Exception:
            self.log("     SPF | Nenhum registro encontrado", 'warning')
        finally:
            self.increment_progress()

        # DKIM
        selectors = ['default', 'google', 'selector1', 'selector2',
                     'mail', 'dkim', 'k1', 's1', 's2']
        for sel in selectors:
            if self.stop_event.is_set():
                return
            try:
                dkim_domain = f"{sel}._domainkey.{target}"
                answers = self.resolver.resolve(dkim_domain, 'TXT')
                for rdata in answers:
                    value = str(rdata).strip('"')
                    display = (value[:100] + '...') if len(value) > 100 \
                        else value
                    self.add_result(
                        'DKIM', dkim_domain, display, '',
                        f'Seletor: {sel}')
                    self.log(f"    DKIM | {dkim_domain} -> "
                             f"{value[:80]}...", 'success')
            except Exception:
                pass
            finally:
                self.increment_progress()

        # PTR
        try:
            answers = self.resolver.resolve(target, 'A')
            for rdata in answers:
                ip = str(rdata)
                try:
                    hostname = socket.gethostbyaddr(ip)
                    self.add_result(
                        'PTR', ip, hostname[0], '', 'Reverse DNS')
                    self.log(f"     PTR | {ip} -> {hostname[0]}", 'result')
                except socket.herror:
                    self.log(f"     PTR | {ip} -> Sem reverso", 'warning')
        except Exception:
            pass
        finally:
            self.increment_progress()

    def attempt_zone_transfer(self, target):
        self.log("\n[ ZONE TRANSFER (AXFR) ]", 'header')
        self.log("-" * 45, 'separator')

        try:
            ns_answers = self.resolver.resolve(target, 'NS')
            nameservers = [str(ns).rstrip('.') for ns in ns_answers]
        except Exception as e:
            self.log(f"Erro ao obter nameservers: {e}", 'error')
            for _ in range(3):
                self.increment_progress()
            return

        estimated = 3
        actual = len(nameservers)
        if actual != estimated:
            with self.progress_lock:
                self.total_tasks += (actual - estimated)

        for ns in nameservers:
            if self.stop_event.is_set():
                return
            self.log(f"Tentando AXFR em {ns}...", 'info')
            try:
                try:
                    ns_ip = str(self.resolver.resolve(ns, 'A')[0])
                except Exception:
                    ns_ip = ns

                zone = dns.zone.from_xfr(
                    dns.query.xfr(
                        ns_ip, target,
                        timeout=self.timeout_var.get()))

                self.log(f"AXFR BEM SUCEDIDA em {ns}", 'success')
                self.add_result(
                    'AXFR', ns, 'Zone Transfer Permitida',
                    '', 'VULNERÁVEL')

                for name, node in zone.nodes.items():
                    for rdataset in node.rdatasets:
                        for rdata in rdataset:
                            full_name = str(name)
                            if full_name == '@':
                                full_name = target
                            elif not full_name.endswith('.'):
                                full_name = f"{full_name}.{target}"
                            rtype = dns.rdatatype.to_text(rdataset.rdtype)
                            self.add_result(
                                rtype, full_name, str(rdata),
                                rdataset.ttl, f'AXFR via {ns}')
                            self.log(
                                f"   AXFR | {rtype:>6} | "
                                f"{full_name} -> {rdata}", 'result')

            except dns.exception.FormError:
                self.log(f"   AXFR | Recusada por {ns}", 'warning')
            except ConnectionRefusedError:
                self.log(f"   AXFR | Conexão recusada: {ns}", 'warning')
            except Exception as e:
                self.log(f"   AXFR | Falha em {ns}: {e}", 'warning')
            finally:
                self.increment_progress()

    def bruteforce_subdomains(self, target, num_threads):
        self.log("\n[ BRUTE FORCE DE SUBDOMÍNIOS ]", 'header')
        self.log("-" * 45, 'separator')

        subdomains = self._get_bruteforce_words()
        total = len(subdomains)
        self.log(f"Testando {total} subdomínios com {num_threads} threads",
                 'info')

        found_count = [0]

        def test_sub(subdomain):
            if self.stop_event.is_set():
                return
            fqdn = f"{subdomain}.{target}"
            try:
                answers = self.resolver.resolve(fqdn, 'A')
                for rdata in answers:
                    ip = str(rdata)
                    self.add_result(
                        'A', fqdn, ip, answers.rrset.ttl, 'Brute Force')
                    self.log(f"       A | {fqdn} -> {ip}", 'success')
                    found_count[0] += 1
            except Exception:
                pass
            try:
                answers = self.resolver.resolve(fqdn, 'CNAME')
                for rdata in answers:
                    val = str(rdata)
                    self.add_result(
                        'CNAME', fqdn, val, answers.rrset.ttl,
                        'Brute Force')
                    self.log(f"   CNAME | {fqdn} -> {val}", 'success')
                    found_count[0] += 1
            except Exception:
                pass
            finally:
                self.increment_progress()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(test_sub, s): s for s in subdomains}
            for fut in as_completed(futures):
                if self.stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    return
                try:
                    fut.result()
                except Exception:
                    pass

        self.log(f"\nBrute Force: {found_count[0]} encontrados "
                 f"de {total} testados", 'info')

    def reverse_lookup(self, target, num_threads):
        self.log("\n[ REVERSE DNS LOOKUP ]", 'header')
        self.log("-" * 45, 'separator')

        cidr = self.reverse_range.get().strip()
        if not cidr:
            try:
                answers = self.resolver.resolve(target, 'A')
                ip = str(answers[0])
                parts = ip.split('.')
                cidr = f"{parts[0]}.{parts[1]}.{parts[2]}.0/28"
                self.log(f"Range automático: {cidr}", 'info')
            except Exception as e:
                self.log(f"Não foi possível determinar range: {e}", 'error')
                return

        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            self.log(f"CIDR inválido: {e}", 'error')
            return

        hosts = list(network.hosts())
        total_ips = len(hosts)

        estimated = self._count_reverse_hosts(target)
        if total_ips != estimated:
            with self.progress_lock:
                self.total_tasks += (total_ips - estimated)

        self.log(f"Verificando {total_ips} IPs em {cidr}", 'info')
        found = [0]

        def rev_ip(ip_addr):
            if self.stop_event.is_set():
                return
            ip_str = str(ip_addr)
            try:
                rev_name = dns.reversename.from_address(ip_str)
                answers = self.resolver.resolve(rev_name, 'PTR')
                for rdata in answers:
                    hostname = str(rdata).rstrip('.')
                    self.add_result(
                        'PTR', ip_str, hostname,
                        answers.rrset.ttl, 'Reverse Lookup')
                    self.log(f"     PTR | {ip_str} -> {hostname}",
                             'success')
                    found[0] += 1
            except Exception:
                pass
            finally:
                self.increment_progress()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(rev_ip, ip): ip for ip in hosts}
            for fut in as_completed(futures):
                if self.stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    return
                try:
                    fut.result()
                except Exception:
                    pass

        self.log(f"\nReverse: {found[0]} PTR encontrados", 'info')

    def cache_snooping(self, target):
        self.log("\n[ DNS CACHE SNOOPING ]", 'header')
        self.log("-" * 45, 'separator')

        domains = [
            'google.com', 'facebook.com', 'youtube.com',
            'twitter.com', 'instagram.com', 'linkedin.com',
            'amazon.com', 'microsoft.com', 'apple.com',
            'netflix.com', 'github.com', 'stackoverflow.com',
            'reddit.com', 'wikipedia.org', 'yahoo.com',
            'cloudflare.com', 'wordpress.com', 'dropbox.com',
            'zoom.us', 'slack.com', 'discord.com',
            target
        ]

        dns_server = self.dns_server_var.get().strip()
        self.log(f"Servidor alvo: {dns_server}", 'info')

        cached = []
        for domain in domains:
            if self.stop_event.is_set():
                return
            try:
                query = dns.message.make_query(domain, dns.rdatatype.A)
                query.flags &= ~dns.flags.RD
                response = dns.query.udp(
                    query, dns_server, timeout=self.timeout_var.get())
                if response.answer:
                    for answer in response.answer:
                        for rdata in answer:
                            cached.append(domain)
                            self.add_result(
                                'CACHE', domain, str(rdata),
                                answer.ttl, 'Em cache no servidor')
                            self.log(
                                f"   CACHE | {domain} -> {rdata} "
                                f"(TTL:{answer.ttl})", 'success')
                            break
                        break
                else:
                    self.log(f"   CACHE | {domain} -> Não está em cache",
                             'warning')
            except Exception as e:
                self.log(f"   CACHE | {domain} -> Erro: {e}", 'error')
            finally:
                self.increment_progress()

        self.log(f"\n{len(cached)} domínios encontrados em cache", 'info')

    def check_wildcard(self, target):
        self.log("\n[ VERIFICAÇÃO DE WILDCARD DNS ]", 'header')
        self.log("-" * 45, 'separator')

        rand_sub = ''.join(random.choices(string.ascii_lowercase, k=16))
        test_domain = f"{rand_sub}.{target}"

        try:
            answers = self.resolver.resolve(test_domain, 'A')
            wildcard_ip = str(answers[0])
            self.log(
                f"WILDCARD DETECTADO! {test_domain} -> {wildcard_ip}",
                'warning')
            self.add_result(
                'WILDCARD', target, wildcard_ip, '',
                'Wildcard ativo — brute force pode ter falsos positivos')
        except dns.resolver.NXDOMAIN:
            self.log("Nenhum wildcard DNS detectado", 'success')
        except Exception as e:
            self.log(f"Erro ao verificar wildcard: {e}", 'warning')
        finally:
            self.increment_progress()


# ================================================================
# MAIN
# ================================================================
def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except Exception:
        pass

    app = DNSReconGUI(root)

    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f'+{x}+{y}')

    root.mainloop()


if __name__ == '__main__':
    main()
