#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebBrute GUI - Gobuster-like directory bruteforcer with graphical interface
Uso exclusivo para testes de penetração autorizados. 
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import requests
import os
import sys
from urllib.parse import urlparse
from datetime import datetime
import time

# Tentar importar colorama para logs coloridos no terminal (opcional)
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # Fallback caso colorama não esteja instalado
    class Fore:
        GREEN = ''
        RED = ''
        YELLOW = ''
        CYAN = ''
        RESET = ''
    class Style:
        BRIGHT = ''
        RESET = ''

# =============================================================================
# Núcleo do brute force (executado em thread separada)
# =============================================================================
class GobusterEngine:
    def __init__(self, target_url, wordlist_path, extensions=None, threads=10,
                 timeout=10, status_codes=None, follow_redirect=False,
                 user_agent="WebBruteGUI/1.0"):
        self.target_url = target_url.rstrip('/')
        self.wordlist_path = wordlist_path
        self.extensions = extensions or []
        self.threads = threads
        self.timeout = timeout
        self.status_codes = status_codes or [200, 204, 301, 302, 307, 401,
                                              403, 405, 500]
        self.follow_redirect = follow_redirect
        self.user_agent = user_agent
        self.running = False
        self.queue = queue.Queue()
        self.results = []
        self.total_words = 0
        self.processed = 0
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def load_wordlist(self):
        """Carrega as palavras do wordlist."""
        words = []
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for linha in f:
                    palavra = linha.strip()
                    if palavra and not palavra.startswith('#'):
                        words.append(palavra)
            self.total_words = len(words)
            return words
        except Exception as e:
            raise Exception(f"Erro ao ler wordlist: {e}")

    def test_url(self, path):
        """Testa um caminho específico no alvo."""
        url = f"{self.target_url}/{path}"
        try:
            resp = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=self.follow_redirect,
                verify=False  # Ignorar SSL (como gobuster -k)
            )
            return resp.status_code, len(resp.content), resp.url
        except requests.exceptions.SSLError:
            return None, 0, None
        except requests.RequestException:
            return None, 0, None

    def worker(self, wordlist):
        """Worker que processa palavras da fila."""
        while self.running and not self.queue.empty():
            try:
                path = self.queue.get_nowait()
            except queue.Empty:
                break

            # Testar sem extensão
            code, size, final_url = self.test_url(path)
            if code is not None and code in self.status_codes:
                result = (path, code, size, final_url, None)
                with self.lock:
                    self.results.append(result)

            # Testar com extensões
            if self.extensions:
                for ext in self.extensions:
                    if not self.running:
                        break
                    full_path = f"{path}{ext}"
                    code2, size2, final_url2 = self.test_url(full_path)
                    if code2 is not None and code2 in self.status_codes:
                        result = (full_path, code2, size2, final_url2, ext)
                        with self.lock:
                            self.results.append(result)

            with self.lock:
                self.processed += 1
                self.queue.task_done()

    def start(self, progress_callback=None, result_callback=None):
        """Inicia o brute force."""
        self.running = True
        self.results = []
        self.processed = 0

        words = self.load_wordlist()
        if not words:
            raise Exception("Wordlist vazia ou inválida.")

        # Preencher fila
        for w in words:
            self.queue.put(w)

        threads = []
        num_workers = min(self.threads, len(words))

        for _ in range(num_workers):
            t = threading.Thread(target=self.worker, args=(words,), daemon=True)
            t.start()
            threads.append(t)

        # Monitoramento em loop
        while self.running and any(t.is_alive() for t in threads):
            time.sleep(0.1)
            if progress_callback:
                progress_callback(self.processed, self.total_words,
                                  len(self.results))

            # Se novos resultados, notificar
            if result_callback:
                with self.lock:
                    if self.results:
                        # Enviar lote (evitar sobrecarga de UI)
                        pass

        # Garantir que fila termine
        self.queue.join()
        self.running = False

        # Callback final
        if progress_callback:
            progress_callback(self.total_words, self.total_words,
                              len(self.results))

        return self.results

    def stop(self):
        """Para o brute force."""
        self.running = False

# =============================================================================
# Interface Gráfica - FUNDO PRETO
# =============================================================================
class WebBruteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Brute")
        self.root.geometry("1000x700")
        self.root.state("zoomed")
        self.root.minsize(800, 600)

        # Ícone (tentar carregar se existir)
        try:
            if os.name == 'nt':
                self.root.iconbitmap(default='')
        except:
            pass

        self.engine = None
        self.thread_engine = None
        self.running = False

        # ============================================================
        # PALETA FUNDO PRETO
        # ============================================================
        self.bg_dark   = "#000000"   # Fundo principal PRETO
        self.bg_frame  = "#0a0a0a"   # Fundo frames (preto levemente diferenciado)
        self.fg        = "#e0e0e0"   # Texto cinza claro
        self.accent    = "#00d4ff"   # Ciano para destaque
        self.success   = "#00ff88"   # Verde para sucesso
        self.warning   = "#ffaa00"   # Amarelo para aviso
        self.error_col = "#ff4444"   # Vermelho para erro
        self.border    = "#1a1a1a"   # Borda sutil

        self.root.configure(bg=self.bg_dark)
        self.setup_styles()
        self.build_ui()

        # --- AUTO-DETECT WORDLIST NA MESMA PASTA DO SCRIPT ---
        self.auto_detect_wordlist()

        # Tratamento de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def auto_detect_wordlist(self):
        """Procura automaticamente wordlists .txt no diretório do script."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        txt_files = [f for f in os.listdir(script_dir)
                    if f.endswith('.txt') and os.path.isfile(os.path.join(script_dir, f))]

        # Prioridade: nomes comuns de wordlist
        priority = ['wordlist.txt', 'diccionario.txt', 'palavras.txt',
                    'common.txt', 'directory-list.txt', '209_wordlist.txt']
        found = None

        for name in priority:
            if name in txt_files:
                found = os.path.join(script_dir, name)
                break

        if found:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, found)
            self.status_label.config(text=f"Wordlist: {os.path.basename(found)}")
        else:
            self.status_label.config(text="Nenhum wordlist Encontrado")

    def setup_styles(self):
        """Configura estilos do ttk com fundo preto."""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Dark.TFrame", background=self.bg_frame,
                        bordercolor=self.border, lightcolor=self.border,
                        darkcolor=self.border)
        style.configure("Dark.TLabel", background=self.bg_frame,
                        foreground=self.fg)
        style.configure("Dark.TButton", background=self.accent,
                        foreground=self.bg_dark, borderwidth=0, padding=6)
        style.map("Dark.TButton",
                  background=[('active', '#00b8e6')])
        style.configure("Stop.TButton", background=self.error_col,
                        foreground="white")
        style.map("Stop.TButton",
                  background=[('active', '#cc0000')])

        # LabelFrame
        style.configure("Dark.TLabelframe", background=self.bg_frame,
                        bordercolor=self.border, foreground=self.accent)
        style.configure("Dark.TLabelframe.Label", background=self.bg_frame,
                        foreground=self.accent)

        # Treeview
        style.configure("Treeview",
                        background="#0d0d0d",
                        foreground=self.fg,
                        fieldbackground="#0d0d0d",
                        bordercolor="#1a1a1a",
                        borderwidth=0)
        style.map("Treeview",
                  background=[('selected', self.accent)],
                  foreground=[('selected', '#000000')])

        # Progressbar
        style.configure("Horizontal.TProgressbar",
                        background=self.success,
                        troughcolor="#1a1a1a",
                        bordercolor="#1a1a1a",
                        lightcolor=self.success,
                        darkcolor=self.success)

        # Spinbox
        style.configure("TSpinbox",
                        background="#0d0d0d",
                        foreground=self.fg,
                        fieldbackground="#0d0d0d",
                        bordercolor="#1a1a1a",
                        arrowcolor=self.accent)

        # Entry
        style.configure("TEntry",
                        background="#0d0d0d",
                        foreground=self.fg,
                        fieldbackground="#0d0d0d",
                        bordercolor="#1a1a1a",
                        insertcolor=self.accent)

        # Checkbutton
        style.configure("Dark.TCheckbutton",
                        background=self.bg_frame,
                        foreground=self.fg,
                        indicatorbackground="#0d0d0d",
                        indicatormargin=3)

    def build_ui(self):
        """Constrói todos os elementos da interface."""
        # Container principal
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ============ TOPO: Entradas ============
        top_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # URL
        ttk.Label(top_frame, text="URL Alvo:", style="Dark.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(top_frame, width=60, font=("Consolas", 10))
        self.url_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW,
                            padx=5, pady=2)
        self.url_entry.insert(0, "http://")

        # Wordlist
        ttk.Label(top_frame, text="Wordlist:", style="Dark.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.wordlist_entry = ttk.Entry(top_frame, width=50,
                                        font=("Consolas", 10))
        self.wordlist_entry.grid(row=1, column=1, sticky=tk.EW, padx=5,
                                 pady=2)
        self.wordlist_btn = ttk.Button(top_frame, text="Procurar",
                                       command=self.select_wordlist,
                                       style="Dark.TButton", width=10)
        self.wordlist_btn.grid(row=1, column=2, padx=(0, 5), pady=2)

        # ============ CONFIGURAÇÕES ============
        config_frame = ttk.LabelFrame(main_frame, text="Configurações",
                                      style="Dark.TLabelframe")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Linha 1: Threads, Timeout, Extensões
        ttk.Label(config_frame, text="Threads", style="Dark.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.threads_spin = ttk.Spinbox(config_frame, from_=1, to=200,
                                        width=6)
        self.threads_spin.grid(row=0, column=1, padx=(0, 15), pady=2)
        self.threads_spin.delete(0, tk.END)
        self.threads_spin.insert(0, "4")

        ttk.Label(config_frame, text="Timeouts", style="Dark.TLabel").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.timeout_spin = ttk.Spinbox(config_frame, from_=1, to=60, width=6)
        self.timeout_spin.grid(row=0, column=3, padx=(0, 15), pady=2)
        self.timeout_spin.delete(0, tk.END)
        self.timeout_spin.insert(0, "10")

        ttk.Label(config_frame, text="Extensões", style="Dark.TLabel").grid(
            row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.ext_entry = ttk.Entry(config_frame, width=20,
                                   font=("Consolas", 10))
        self.ext_entry.grid(row=0, column=5, padx=5, pady=2)
        self.ext_entry.insert(0, ".php,.asp,.aspx,.jsp,.txt,.html,.bak")
        ttk.Label(config_frame, text="(separado por vírgula)",
                  style="Dark.TLabel", foreground="#666").grid(
            row=0, column=6, sticky=tk.W, pady=2)

        # Linha 2: Status Codes, Follow Redirect, Ignorar SSL
        ttk.Label(config_frame, text="Status Codes", style="Dark.TLabel").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.status_entry = ttk.Entry(config_frame, width=30,
                                      font=("Consolas", 10))
        self.status_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W,
                               padx=5, pady=2)
        self.status_entry.insert(0, "200,204,301,302,307,401,403,405,500")

        self.follow_var = tk.BooleanVar(value=False)
        self.follow_cb = ttk.Checkbutton(config_frame, text="Follow Redirect",
                                         variable=self.follow_var,
                                         style="Dark.TCheckbutton")
        self.follow_cb.grid(row=1, column=3, padx=5, pady=2)

        self.ssl_var = tk.BooleanVar(value=True)
        self.ssl_cb = ttk.Checkbutton(config_frame, text="Ignorar SSL",
                                      variable=self.ssl_var,
                                      style="Dark.TCheckbutton")
        self.ssl_cb.grid(row=1, column=4, padx=5, pady=2)

        # ============ BOTÕES DE CONTROLE ============
        control_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = tk.Button(control_frame, text="▶ INICIAR",
                                   bg=self.success, fg=self.bg_dark,
                                   font=("Arial", 11, "bold"),
                                   command=self.start_scan,
                                   padx=20, pady=8, relief=tk.FLAT,
                                   activebackground="#00cc66",
                                   cursor="hand2")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = tk.Button(control_frame, text="⬛ PARAR",
                                  bg=self.error_col, fg="white",
                                  font=("Arial", 11, "bold"),
                                  command=self.stop_scan,
                                  state=tk.DISABLED,
                                  padx=20, pady=8, relief=tk.FLAT,
                                  activebackground="#cc0000",
                                  cursor="hand2")
        self.stop_btn.pack(side=tk.LEFT)

        self.export_btn = tk.Button(control_frame, text="💾 Exportar",
                                    bg="#222", fg=self.fg,
                                    font=("Arial", 10),
                                    command=self.export_results,
                                    padx=15, pady=8, relief=tk.FLAT,
                                    activebackground="#333",
                                    cursor="hand2")
        self.export_btn.pack(side=tk.RIGHT)

        # ============ BARRA DE PROGRESSO ============
        progress_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        self.progress = ttk.Progressbar(progress_frame, length=100,
                                        mode='determinate',
                                        style="Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))

        self.status_label = ttk.Label(progress_frame, text="Pronto",
                                      style="Dark.TLabel", width=30)
        self.status_label.pack(side=tk.RIGHT)

        # ============ ÁREA DE RESULTADOS ============
        result_frame = ttk.LabelFrame(main_frame,
                                      text="Resultados encontrados",
                                      style="Dark.TLabelframe")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview para resultados
        columns = ("path", "status", "size", "redirect")
        self.tree = ttk.Treeview(result_frame, columns=columns,
                                 show="headings", height=15)
        self.tree.heading("path", text="Caminho")
        self.tree.heading("status", text="Status")
        self.tree.heading("size", text="Tamanho")
        self.tree.heading("redirect", text="Redireciona para")

        self.tree.column("path", width=350, minwidth=200)
        self.tree.column("status", width=70, minwidth=60, anchor=tk.CENTER)
        self.tree.column("size", width=100, minwidth=80, anchor=tk.E)
        self.tree.column("redirect", width=300, minwidth=150)

        # Scrollbars
        vsb = ttk.Scrollbar(result_frame, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # Tag colors para status codes (cores vibrantes no fundo preto)
        self.tree.tag_configure("green", foreground="#00ff88")
        self.tree.tag_configure("red", foreground="#ff4444")
        self.tree.tag_configure("yellow", foreground="#ffaa00")
        self.tree.tag_configure("cyan", foreground="#00d4ff")
        self.tree.tag_configure("white", foreground="#e0e0e0")

        # Label de estatísticas no rodapé
        self.stats_label = ttk.Label(main_frame,
                                     text="Encontrados: 0  |  Processados: 0  |  Total: 0",
                                     style="Dark.TLabel")
        self.stats_label.pack(fill=tk.X, pady=(5, 0))

        # Bind para abrir URL no navegador (duplo clique)
        self.tree.bind("<Double-1>", self.on_double_click)

    # =========================================================================
    # MÉTODOS DE CONTROLE
    # =========================================================================
    def select_wordlist(self):
        """Abre diálogo para selecionar wordlist na mesma pasta do script."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = filedialog.askopenfilename(
            title="Selecionar Wordlist",
            filetypes=[("Wordlists", "*.txt"), ("Todos", "*.*")],
            initialdir=script_dir  # ← agora abre na pasta do script
        )
        if path:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, path)

    def get_config(self):
        """Obtém configurações atuais da interface."""
        try:
            threads = int(self.threads_spin.get())
            timeout = int(self.timeout_spin.get())
        except ValueError:
            threads = 20
            timeout = 10

        ext_text = self.ext_entry.get().strip()
        extensions = [e.strip() for e in ext_text.split(",") if e.strip()]

        try:
            status_codes = [int(s.strip()) for s in
                           self.status_entry.get().split(",") if s.strip()]
        except ValueError:
            status_codes = [200, 301, 302, 403]

        return {
            "url": self.url_entry.get().strip(),
            "wordlist": self.wordlist_entry.get().strip(),
            "threads": threads,
            "timeout": timeout,
            "extensions": extensions,
            "status_codes": status_codes,
            "follow_redirect": self.follow_var.get(),
            "ignore_ssl": self.ssl_var.get(),
        }

    def validate_config(self, cfg):
        """Valida as configurações antes de iniciar."""
        if not cfg["url"] or cfg["url"] in ("http://", "https://"):
            messagebox.showerror("Erro", "Informe uma URL alvo válida.")
            return False

        if not cfg["wordlist"]:
            messagebox.showerror("Erro", "Selecione um wordlist.")
            return False

        if not os.path.isfile(cfg["wordlist"]):
            messagebox.showerror("Erro", "Arquivo de wordlist não encontrado.")
            return False

        return True

    def start_scan(self):
        """Inicia o scan em thread separada."""
        cfg = self.get_config()
        if not self.validate_config(cfg):
            return

        # Desabilitar inputs
        self.set_ui_state(False)

        # Limpar resultados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.running = True

        # Criar engine
        self.engine = GobusterEngine(
            target_url=cfg["url"],
            wordlist_path=cfg["wordlist"],
            extensions=cfg["extensions"],
            threads=cfg["threads"],
            timeout=cfg["timeout"],
            status_codes=cfg["status_codes"],
            follow_redirect=cfg["follow_redirect"],
        )

        if cfg["ignore_ssl"]:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Thread principal de execução
        def run():
            try:
                results = self.engine.start(
                    progress_callback=self.update_progress,
                )
                self.root.after(0, self.on_scan_complete, results)
            except Exception as e:
                self.root.after(0, self.on_scan_error, str(e))

        self.thread_engine = threading.Thread(target=run, daemon=True)
        self.thread_engine.start()

        # Thread de monitoramento de resultados em tempo real
        def monitor():
            last_count = 0
            while self.running:
                time.sleep(0.3)
                with self.engine.lock:
                    current = list(self.engine.results)
                if len(current) > last_count:
                    batch = current[last_count:]
                    last_count = len(current)
                    self.root.after(0, self.add_results_batch, batch)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def stop_scan(self):
        """Para o scan em andamento."""
        if self.engine:
            self.engine.stop()
        self.running = False
        self.status_label.config(text="Parado pelo usuário")

    def on_scan_complete(self, results):
        """Callback quando scan termina."""
        self.set_ui_state(True)
        self.running = False
        self.status_label.config(text="Concluído ✓")
        self.progress['value'] = 100

    def on_scan_error(self, error_msg):
        """Callback em caso de erro."""
        self.set_ui_state(True)
        self.running = False
        messagebox.showerror("Erro no Scan", error_msg)
        self.status_label.config(text=f"Erro: {error_msg[:40]}...")

    def update_progress(self, processed, total, found):
        """Atualiza barra de progresso e estatísticas."""
        if total > 0:
            pct = (processed / total) * 100
            self.progress['value'] = pct

        elapsed = ""
        self.status_label.config(
            text=f"Processando... {processed}/{total}")
        self.stats_label.config(
            text=f"Encontrados: {found}  |  Processados: {processed}  |  Total: {total}"
        )

    def add_results_batch(self, results):
        """Adiciona lote de resultados à treeview em tempo real."""
        for path, code, size, redirect, ext in results:
            # Determinar tag por status code
            if code == 200:
                tag = "green"
            elif code in (301, 302, 307, 308):
                tag = "yellow"
            elif code in (403, 401):
                tag = "red"
            elif code in (500, 502, 503):
                tag = "red"
            else:
                tag = "white"

            size_str = self.format_size(size)

            self.tree.insert("", tk.END,
                             values=(f"/{path}", code, size_str, redirect or ""),
                             tags=(tag,))

        # Atualizar contagem
        self.stats_label.config(
            text=f"Encontrados: {len(self.tree.get_children())}"
        )

    def set_ui_state(self, enabled):
        """Habilita/desabilita controles durante o scan."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.start_btn.config(state=state)
        self.url_entry.config(state=state)
        self.wordlist_entry.config(state=state)
        self.wordlist_btn.config(state=state)
        self.ext_entry.config(state=state)
        self.status_entry.config(state=state)

        if enabled:
            self.stop_btn.config(state=tk.DISABLED)
            self.start_btn.config(text="▶ INICIAR", bg=self.success)
        else:
            self.stop_btn.config(state=tk.NORMAL)
            self.start_btn.config(text="▶ PROCESSANDO...", bg="#333")

    def format_size(self, size_bytes):
        """Formata tamanho em bytes para formato legível."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/(1024*1024):.1f} MB"

    def export_results(self):
        """Exporta resultados para arquivo de texto."""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("Exportar", "Nenhum resultado para exportar.")
            return

        path = filedialog.asksaveasfilename(
            title="Salvar resultados",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# Web Brute - Resultados\n\n")
                f.write(f"# Alvo: {self.url_entry.get()}\n\n")
                f.write(f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(f"# {'='*101}\n")
                f.write(f"{'Caminho':<40} {'Status':<8} {'Tamanho':<12} {'Redireciona'}\n")
                f.write(f"{'-'*40} {'-'*8} {'-'*12} {'-'*40}\n")

                for item in items:
                    vals = self.tree.item(item, "values")
                    f.write(f"{vals[0]:<40} {vals[1]:<8} {vals[2]:<12} {vals[3]}\n")

            messagebox.showinfo("Exportar", f"Resultados salvos com sucesso\n\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def on_double_click(self, event):
        """Abre URL no navegador ao dar duplo clique."""
        item = self.tree.selection()
        if not item:
            return
        vals = self.tree.item(item[0], "values")
        if vals:
            path = vals[0]
            url = f"{self.url_entry.get().strip().rstrip('/')}{path}"
            try:
                import webbrowser
                webbrowser.open(url)
            except:
                pass

    def on_close(self):
        """Fecha a aplicação com segurança."""
        if self.running:
            if messagebox.askyesno("Saindo",
                                   "Scan em andamento. Deseja realmente sair?"):
                self.stop_scan()
                self.root.destroy()
        else:
            self.root.destroy()


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    # Suprimir avisos SSL por padrão
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    root = tk.Tk()
    app = WebBruteGUI(root)
    root.mainloop()
