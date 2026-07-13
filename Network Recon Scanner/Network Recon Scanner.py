import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import httpx
import ipaddress
import os
import re
import random
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse

class ScannerHTTPX:
    def __init__(self, root):
        self.root = root
        self.root.title("📡 Network Recon Scanner 📡")
        self.root.geometry("1150x850")
        self.root.state("zoomed")
        self.root.resizable(True, True)

        # Variáveis
        self.arquivo_selecionado = tk.StringVar()
        self.ips_carregados = []
        self.urls_manuais = []
        self.wordlist = []
        self.user_agents = []
        self.executando = False
        self.abortar_scan = False  # Flag de abortamento
        self.timeout = tk.IntVar(value=5)
        self.portas = tk.StringVar(value="443")
        self.max_threads = tk.IntVar(value=5)
        self.modo_url = tk.BooleanVar(value=False)
        
        # Arquivos
        self.wordlist_path = tk.StringVar()
        self.useragent_path = tk.StringVar()
        
        # Stats
        self.stats = {"online": 0, "offline": 0, "redirect": 0, "erro": 0}
        self.total_resultados = 0

        # Pool de execução (precisa ser acessível globalmente para abortar)
        self.executor_pool = None

        # Capturar fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)

        self.criar_widgets()

    def criar_widgets(self):
        # === FRAME TOPO ===
        frame_top = tk.Frame(self.root, padx=10, pady=10)
        frame_top.pack(fill=tk.X)

        # --- Modo ---
        frame_modo = tk.Frame(frame_top)
        frame_modo.pack(fill=tk.X, pady=(0, 5))

        tk.Label(frame_modo, text="Modo:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.radio_ips = tk.Radiobutton(
            frame_modo, text="Arquivo de IP", variable=self.modo_url,
            value=False, command=self.alternar_modo
        )
        self.radio_ips.pack(side=tk.LEFT, padx=5)
        
        self.radio_urls = tk.Radiobutton(
            frame_modo, text="URL Manuais", variable=self.modo_url,
            value=True, command=self.alternar_modo
        )
        self.radio_urls.pack(side=tk.LEFT, padx=5)

        # --- Frame Arquivo ---
        self.frame_arquivo = tk.Frame(frame_top)
        self.frame_arquivo.pack(fill=tk.X)

        tk.Label(self.frame_arquivo, text="Arquivo IP:").grid(row=0, column=0, sticky="w")
        self.lbl_arquivo = tk.Label(self.frame_arquivo, text="Nenhum", fg="gray", anchor="w")
        self.lbl_arquivo.grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(self.frame_arquivo, text="📂 Selecionar", command=self.selecionar_arquivo).grid(row=0, column=2, padx=3)
        tk.Button(self.frame_arquivo, text="Carregar", command=self.carregar_ips).grid(row=0, column=3, padx=3)
        self.frame_arquivo.columnconfigure(1, weight=1)

        # --- Frame URLs Manuais ---
        self.frame_urls = tk.Frame(frame_top)

        tk.Label(self.frame_urls, text="URL (uma por linha):").pack(anchor="w")

        self.txt_urls = tk.Text(self.frame_urls, height=3, width=80, font=("Consolas", 9))
        self.txt_urls.pack(fill=tk.X, pady=2)
        self.txt_urls.insert(tk.END, "http://businesscorp.com.br")

        tk.Button(self.frame_urls, text="✅ Carregar URL", command=self.carregar_urls).pack(pady=2)

        # === FRAME WORDLIST / USER-AGENT ===
        frame_extra = tk.Frame(self.root, padx=10, pady=5)
        frame_extra.pack(fill=tk.X)

        # Wordlist
        tk.Label(frame_extra, text="Wordlist (qualquer tipo):", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=2)
        
        self.lbl_wordlist = tk.Label(frame_extra, text="Nenhuma", fg="gray", anchor="w", width=30)
        self.lbl_wordlist.grid(row=0, column=1, sticky="ew", padx=2)
        
        tk.Button(frame_extra, text="📂 wordlist.txt", command=self.selecionar_wordlist).grid(row=0, column=2, padx=2)
        tk.Button(frame_extra, text="Carregar", command=self.carregar_wordlist).grid(row=0, column=3, padx=2)
        
        self.lbl_wl_count = tk.Label(frame_extra, text="0 paths", fg="gray", width=12)
        self.lbl_wl_count.grid(row=0, column=4, padx=2)

        # User-Agent
        tk.Label(frame_extra, text="User-Agents:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        
        self.lbl_ua = tk.Label(frame_extra, text="Nenhum", fg="gray", anchor="w", width=30)
        self.lbl_ua.grid(row=1, column=1, sticky="ew", padx=2)
        
        tk.Button(frame_extra, text="📂 useragent.txt", command=self.selecionar_useragent).grid(row=1, column=2, padx=2)
        tk.Button(frame_extra, text="Carregar", command=self.carregar_useragents).grid(row=1, column=3, padx=2)
        
        self.lbl_ua_count = tk.Label(frame_extra, text="0 UAs", fg="gray", width=12)
        self.lbl_ua_count.grid(row=1, column=4, padx=2)

        # Checkboxes
        self.var_usar_wordlist = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_extra, text="Usar wordlist", variable=self.var_usar_wordlist).grid(row=0, column=5, padx=10)
        
        self.var_usar_useragent = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_extra, text="Rotacionar UAs", variable=self.var_usar_useragent).grid(row=1, column=5, padx=10)

        frame_extra.grid_columnconfigure(1, weight=1)

        # === FRAME CONFIG ===
        frame_config = tk.Frame(self.root, padx=10, pady=5)
        frame_config.pack(fill=tk.X)

        tk.Label(frame_config, text="Timeout:").pack(side=tk.LEFT, padx=2)
        tk.Spinbox(frame_config, from_=1, to=30, textvariable=self.timeout, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(frame_config, text="Portas:").pack(side=tk.LEFT, padx=5)
        tk.Entry(frame_config, textvariable=self.portas, width=18).pack(side=tk.LEFT, padx=2)

        tk.Label(frame_config, text="Threads:").pack(side=tk.LEFT, padx=5)
        tk.Spinbox(frame_config, from_=1, to=100, textvariable=self.max_threads, width=5).pack(side=tk.LEFT, padx=2)

        # === LABEL DE STATUS EM TEMPO REAL ===
        self.lbl_scaneando = tk.Label(
            self.root, 
            text="⏳ Aguardando scan...", 
            anchor="w", padx=15, font=("Arial", 10, "bold"),
            fg="#1565C0", bg="#E3F2FD"
        )
        self.lbl_scaneando.pack(fill=tk.X, padx=10, pady=2)

        # === INFOS ===
        self.lbl_info = tk.Label(
            self.root, 
            text="Alvos: 0 | Paths: 0 | Reqs: 0 | ✅ 200: 0 | 🔀 3xx: 0 | ❌ 4xx: 0 | ⚠ 5xx/Err: 0", 
            anchor="w", padx=15, font=("Arial", 9, "bold")
        )
        self.lbl_info.pack(fill=tk.X)

        # === PROGRESSO ===
        self.progresso = ttk.Progressbar(self.root, mode="determinate")
        self.progresso.pack(fill=tk.X, padx=10, pady=3)

        # === BOTÕES INICIAR / STOP ===
        frame_botoes = tk.Frame(self.root, padx=10)
        frame_botoes.pack(fill=tk.X, pady=2)

        self.btn_verificar = tk.Button(
            frame_botoes, text="▶ INICIAR SCAN",
            command=self.iniciar_verificacao,
            bg="#2196F3", fg="white",
            font=("Arial", 11, "bold"), pady=6, cursor="hand2"
        )
        self.btn_verificar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_stop = tk.Button(
            frame_botoes, text="⏹ STOP",
            command=self.parar_scan,
            bg="#F44336", fg="black",
            font=("Arial", 11, "bold"), pady=6, cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(5, 0))

        # === CHECKBOXES ===
        frame_opcoes = tk.Frame(self.root, padx=10)
        frame_opcoes.pack(fill=tk.X)

        self.var_title = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_opcoes, text="Título", variable=self.var_title).pack(side=tk.LEFT, padx=5)

        self.var_server = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_opcoes, text="Server", variable=self.var_server).pack(side=tk.LEFT, padx=5)

        self.var_cLength = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_opcoes, text="Content-Length", variable=self.var_cLength).pack(side=tk.LEFT, padx=5)

        self.var_tech = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_opcoes, text="Tecnologias", variable=self.var_tech).pack(side=tk.LEFT, padx=5)

        # === RESULTADOS (TABELA) ===
        tk.Label(self.root, text="Resultados em tempo real:", anchor="w", padx=15, 
                 font=("Arial", 9, "bold")).pack(fill=tk.X)

        frame_resultado = tk.Frame(self.root)
        frame_resultado.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll_y = tk.Scrollbar(frame_resultado, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(frame_resultado, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(
            frame_resultado,
            columns=("alvo", "path", "status", "title", "server", "clength", "tech", "url"),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=12
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        colunas = {
            "alvo": ("Alvo", 140),
            "path": ("Path", 120),
            "status": ("Status", 70),
            "title": ("Título", 200),
            "server": ("Server", 140),
            "clength": ("Size", 80),
            "tech": ("Tecnologias", 170),
            "url": ("URL Final", 300)
        }

        for col, (texto, largura) in colunas.items():
            self.tree.column(col, width=largura, minwidth=60)
            self.tree.heading(col, text=texto)

        self.tree.tag_configure("online", foreground="green")
        self.tree.tag_configure("offline", foreground="red")
        self.tree.tag_configure("redirect", foreground="orange")
        self.tree.tag_configure("erro", foreground="gray")

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_resultado.grid_rowconfigure(0, weight=1)
        frame_resultado.grid_columnconfigure(0, weight=1)

        # ========================
        # === NOVO: CONSOLE DE LOG EM TEMPO REAL (PARTE INFERIOR) ===
        # ========================
        frame_console = tk.Frame(self.root, padx=10)
        frame_console.pack(fill=tk.BOTH, expand=False, pady=(0, 5))

        lbl_console = tk.Label(frame_console, text="📋 Log em tempo real:", anchor="w",
                               font=("Arial", 9, "bold"))
        lbl_console.pack(anchor="w")

        frame_console_inner = tk.Frame(frame_console)
        frame_console_inner.pack(fill=tk.BOTH, expand=True)

        scroll_console = tk.Scrollbar(frame_console_inner, orient=tk.VERTICAL)

        self.console_log = tk.Text(
            frame_console_inner,
            height=8,
            font=("Consolas", 9),
            fg="#E0E0E0",
            bg="#1E1E1E",
            wrap=tk.WORD,
            yscrollcommand=scroll_console.set,
            state=tk.DISABLED
        )
        scroll_console.config(command=self.console_log.yview)

        self.console_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_console.pack(side=tk.RIGHT, fill=tk.Y)

        # Botão para limpar console
        btn_limpar_console = tk.Button(frame_console, text="🗑 Limpar Log",
                                       command=self.limpar_console,
                                       font=("Arial", 8))
        btn_limpar_console.pack(anchor="e", pady=(2, 0))

        # === BOTTOM ===
        frame_bot = tk.Frame(self.root, padx=10, pady=5)
        frame_bot.pack(fill=tk.X)

        tk.Button(frame_bot, text="🗑 Limpar", command=self.limpar_resultados).pack(side=tk.LEFT, padx=3)
        
        
        self.btn_salvar_txt = tk.Button(
            frame_bot, text="📄 Salvar TXT (só 200/3xx)", command=self.salvar_txt,
            bg="#4CAF50", fg="black", font=("Arial", 9, "bold")
        )
        self.btn_salvar_txt.pack(side=tk.LEFT, padx=3)

        self.lbl_status = tk.Label(frame_bot, text="Pronto", anchor="e", fg="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=5)

    # ==================== MÉTODOS ====================

    def log_console(self, mensagem):
        """Adiciona uma linha formatada ao console de log em tempo real."""
        self.root.after(0, self._inserir_log, mensagem)

    def _inserir_log(self, mensagem):
        """Insere a mensagem no widget Text e faz scroll automático."""
        self.console_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        linha = f"[{timestamp}] {mensagem}\n"
        self.console_log.insert(tk.END, linha)
        self.console_log.see(tk.END)
        self.console_log.config(state=tk.DISABLED)

    def limpar_console(self):
        """Limpa o console de log."""
        self.console_log.config(state=tk.NORMAL)
        self.console_log.delete("1.0", tk.END)
        self.console_log.config(state=tk.DISABLED)

    def alternar_modo(self):
        if self.modo_url.get():
            self.frame_arquivo.pack_forget()
            self.frame_urls.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.frame_urls.pack_forget()
            self.frame_arquivo.pack(fill=tk.X)

    def selecionar_arquivo(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo com os IP",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            self.arquivo_selecionado.set(arquivo)
            self.lbl_arquivo.config(text=os.path.basename(arquivo), fg="black")

    def carregar_ips(self):
        arquivo = self.arquivo_selecionado.get()
        if not arquivo or not os.path.exists(arquivo):
            return

        try:
            with open(arquivo, "r") as f:
                linhas = f.readlines()

            self.ips_carregados = []
            self.urls_manuais = []
            for linha in linhas:
                alvo = linha.strip()
                if alvo:
                    try:
                        ipaddress.ip_address(alvo)
                        self.ips_carregados.append(alvo)
                    except ValueError:
                        if alvo.startswith(("http://", "https://")):
                            self.urls_manuais.append(alvo)

            total = len(self.ips_carregados) + len(self.urls_manuais)
            self.log_console(f"📂 Carregados {total} alvos do arquivo")
            self.atualizar_status(f"Carregados {total} alvos")
            self.atualizar_info()
        except Exception as e:
            self.atualizar_status(f"Erro: {str(e)}")

    def carregar_urls(self):
        conteudo = self.txt_urls.get("1.0", tk.END).strip()
        if not conteudo:
            messagebox.showwarning("Aviso", "Digite pelo menos uma URL!")
            return

        linhas = conteudo.split("\n")
        self.urls_manuais = []
        self.ips_carregados = []

        for linha in linhas:
            alvo = linha.strip()
            if not alvo:
                continue

            try:
                ipaddress.ip_address(alvo)
                self.ips_carregados.append(alvo)
                continue
            except ValueError:
                pass

            if not alvo.startswith(("http://", "https://")):
                alvo = "http://" + alvo

            parsed = urlparse(alvo)
            if parsed.netloc:
                self.urls_manuais.append(alvo)

        total = len(self.ips_carregados) + len(self.urls_manuais)
        if total == 0:
            messagebox.showerror("Erro", "Nenhum alvo válido!")
            return

        self.log_console(f"📂 Carregados {total} URL manuais")
        self.atualizar_status(f"Carregados {total} alvos")
        self.atualizar_info()

    def atualizar_info(self):
        paths = len(self.wordlist) if self.var_usar_wordlist.get() and self.wordlist else 1
        total_alvos = len(self.ips_carregados) + len(self.urls_manuais)
        self.lbl_info.config(
            text=f"Alvos: {total_alvos} | Paths: {paths} | ✅ 200: {self.stats['online']} | 🔀 3xx: {self.stats['redirect']} | ❌ 4xx: {self.stats['offline']} | ⚠ 5xx/Err: {self.stats['erro']}"
        )

    # ========== WORDLIST ==========

    def selecionar_wordlist(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            self.wordlist_path.set(arquivo)
            self.lbl_wordlist.config(text=os.path.basename(arquivo), fg="black")

    def carregar_wordlist(self):
        caminho = self.wordlist_path.get()
        if not caminho or not os.path.exists(caminho):
            messagebox.showwarning("Aviso", "Selecione a wordlist primeiro!")
            return

        try:
            with open(caminho, "r", errors="ignore") as f:
                linhas = f.readlines()

            self.wordlist = []
            for linha in linhas:
                path = linha.strip()
                if path:
                    if not path.startswith("/"):
                        path = "/" + path
                    self.wordlist.append(path)

            self.lbl_wl_count.config(text=f"{len(self.wordlist)} paths", fg="green")
            self.var_usar_wordlist.set(True)
            self.log_console(f"📄 Wordlist carregada: {len(self.wordlist)} paths")
            self.atualizar_status(f"Wordlist: {len(self.wordlist)} paths carregados")
            self.atualizar_info()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler wordlist: {str(e)}")

    # ========== USER-AGENTS ==========

    def selecionar_useragent(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo de User-Agents",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            self.useragent_path.set(arquivo)
            self.lbl_ua.config(text=os.path.basename(arquivo), fg="black")

    def carregar_useragents(self):
        caminho = self.useragent_path.get()
        if not caminho or not os.path.exists(caminho):
            messagebox.showwarning("Aviso", "Selecione o arquivo de UAs primeiro!")
            return

        try:
            with open(caminho, "r", errors="ignore") as f:
                linhas = f.readlines()

            self.user_agents = []
            for linha in linhas:
                ua = linha.strip()
                if ua:
                    self.user_agents.append(ua)

            self.lbl_ua_count.config(text=f"{len(self.user_agents)} UAs", fg="green")
            if self.user_agents:
                self.var_usar_useragent.set(True)
            self.log_console(f"👤 User-Agents carregados: {len(self.user_agents)}")
            self.atualizar_status(f"User-Agents: {len(self.user_agents)} carregados")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler UAs: {str(e)}")

    # ========== SCAN ==========

    def _get_user_agent(self):
        if self.var_usar_useragent.get() and self.user_agents:
            return random.choice(self.user_agents)
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def _get_paths(self):
        if self.var_usar_wordlist.get() and self.wordlist:
            return self.wordlist
        return ["/"]

    def scan_ip(self, ip, callback_status):
        """Escaneia IP com feedback em tempo real."""
        portas = [p.strip() for p in self.portas.get().split(",") if p.strip()]
        paths = self._get_paths()
        resultados = []

        urls_base = []
        for porta in portas:
            urls_base.append(f"http://{ip}:{porta}")
            urls_base.append(f"https://{ip}:{porta}")
        if "80" in portas:
            urls_base.append(f"http://{ip}")
        if "443" in portas:
            urls_base.append(f"https://{ip}")

        urls_vistas = set()
        urls_base_unicas = []
        for url in urls_base:
            if url not in urls_vistas:
                urls_vistas.add(url)
                urls_base_unicas.append(url)

        timeout_val = self.timeout.get()

        for base_url in urls_base_unicas:
            if self.abortar_scan:
                self.log_console(f"  └─ ⏹ Scan abortado durante IP {ip}")
                break

            for path in paths:
                if self.abortar_scan:
                    break

                url_completa = base_url.rstrip("/") + path
                try:
                    ua = self._get_user_agent()
                    with httpx.Client(
                        timeout=timeout_val,
                        follow_redirects=True,
                        max_redirects=5,
                        headers={"User-Agent": ua},
                        verify=False
                    ) as client:
                        callback_status(f"🔍 Testando: {url_completa}")
                        self.log_console(f"🔍 {url_completa}")
                        
                        resp = client.get(url_completa)
                        dados = self._extrair_info(resp, ip, url_completa, path)
                        resultados.append(dados)
                        
                        self.root.after(0, self._inserir_resultado_callback, dados)
                        self.log_console(f"  ├─ Status: {dados['status']} | Título: {dados['title'][:60]}")

                        if path == "/" and resp.status_code == 200:
                            break
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                    if path == "/":
                        self.log_console(f"  └─ ❌ Sem conexão: {url_completa}")
                        break
                    continue
                except Exception:
                    continue

            if self.abortar_scan:
                break

            if any(r["status"] == 200 for r in resultados):
                break

        if not resultados and not self.abortar_scan:
            dados = {
                "alvo": ip, "path": "/", "status": "N/A", "title": "-",
                "server": "-", "clength": "-", "tech": "-",
                "url": "Sem resposta", "tag": "offline"
            }
            resultados.append(dados)
            self.log_console(f"  └─ ⚠ Sem resposta para {ip}")
            self.root.after(0, self._inserir_resultado_callback, dados)

        return resultados

    def scan_url(self, url, callback_status):
        """Escaneia URL com feedback em tempo real."""
        paths = self._get_paths()
        resultados = []
        timeout_val = self.timeout.get()
        alvo = url

        for path in paths:
            if self.abortar_scan:
                self.log_console(f"  └─ ⏹ Scan abortado durante {url}")
                break

            url_completa = url.rstrip("/") + path
            try:
                ua = self._get_user_agent()
                
                callback_status(f"🔍 Testando: {url_completa}")
                self.log_console(f"🔍 {url_completa}")
                
                with httpx.Client(
                    timeout=timeout_val,
                    follow_redirects=True,
                    max_redirects=5,
                    headers={"User-Agent": ua},
                    verify=False
                ) as client:
                    resp = client.get(url_completa)
                    dados = self._extrair_info(resp, alvo, str(resp.url), path)
                    resultados.append(dados)
                    
                    self.root.after(0, self._inserir_resultado_callback, dados)
                    self.log_console(f"  ├─ Status: {dados['status']} | Título: {dados['title'][:60]}")

            except (httpx.ConnectError, httpx.ConnectTimeout):
                if path == "/":
                    self.log_console(f"  └─ ❌ Sem conexão: {url_completa}")
                    if self.abortar_scan:
                        break
                    callback_status(f"🔄 Tentando protocolo alternativo para {url}")
                    try:
                        url_alt = url.replace("http://", "https://") if "http://" in url else url.replace("https://", "http://")
                        url_alt_completa = url_alt.rstrip("/") + path
                        ua = self._get_user_agent()
                        with httpx.Client(
                            timeout=timeout_val,
                            follow_redirects=True,
                            max_redirects=5,
                            headers={"User-Agent": ua},
                            verify=False
                        ) as client:
                            resp = client.get(url_alt_completa)
                            dados = self._extrair_info(resp, alvo, str(resp.url), path)
                            resultados.append(dados)
                            self.root.after(0, self._inserir_resultado_callback, dados)
                            self.log_console(f"  ├─ 🔄 Alternativo OK: {dados['status']} | {dados['title'][:60]}")
                    except Exception:
                        self.log_console(f"  └─ ❌ Alternativo falhou: {url_alt}")
                continue
            except Exception:
                continue

        if not resultados and not self.abortar_scan:
            dados = {
                "alvo": alvo, "path": "/", "status": "N/A", "title": "-",
                "server": "-", "clength": "-", "tech": "-",
                "url": url + "/", "tag": "offline"
            }
            resultados.append(dados)
            self.log_console(f"  └─ ⚠ Sem resposta para {alvo}")
            self.root.after(0, self._inserir_resultado_callback, dados)

        return resultados

    def _inserir_resultado_callback(self, dados):
        """Insere resultado na tabela e atualiza stats em tempo real."""
        tag = dados["tag"]
        if tag == "online":
            self.stats["online"] += 1
        elif tag == "redirect":
            self.stats["redirect"] += 1
        elif tag == "erro":
            self.stats["erro"] += 1
        else:
            self.stats["offline"] += 1
        
        self.total_resultados += 1
        
        self.tree.insert("", tk.END, values=(
            dados["alvo"], dados["path"], dados["status"], dados["title"],
            dados["server"], dados["clength"], dados["tech"], dados["url"]
        ), tags=(tag,))
        
        self.tree.see(self.tree.get_children()[-1])
        
        self.lbl_info.config(
            text=f"Reqs: {self.total_resultados} | ✅ 200: {self.stats['online']} | 🔀 3xx: {self.stats['redirect']} | ❌ 4xx: {self.stats['offline']} | ⚠ 5xx/Err: {self.stats['erro']}"
        )

    def _extrair_info(self, resp, alvo, url, path="/"):
        status = resp.status_code

        title = "-"
        if self.var_title.get() and resp.text:
            match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()[:100]

        server = "-"
        if self.var_server.get():
            server = resp.headers.get("server", "-")

        clength = "-"
        if self.var_cLength.get():
            cl = resp.headers.get("content-length")
            if cl:
                try:
                    size = int(cl)
                    if size >= 1048576:
                        clength = f"{size/1048576:.1f} MB"
                    elif size >= 1024:
                        clength = f"{size/1024:.1f} KB"
                    else:
                        clength = f"{size} B"
                except ValueError:
                    clength = cl
            else:
                tam = len(resp.content)
                if tam >= 1048576:
                    clength = f"{tam/1048576:.1f} MB"
                elif tam >= 1024:
                    clength = f"{tam/1024:.1f} KB"
                else:
                    clength = f"{tam} B"

        tech = "-"
        if self.var_tech.get():
            techs = []
            h = resp.headers
            if "x-powered-by" in h: techs.append(h["x-powered-by"])
            if h.get("server") and h["server"] not in ["-", ""]: techs.append(h["server"])
            if "x-generator" in h: techs.append(h["x-generator"])
            
            if "set-cookie" in h:
                cookies = h.get("set-cookie", "")
                if "PHPSESSID" in cookies: techs.append("PHP")
                if "JSESSIONID" in cookies: techs.append("Java/JSP")
                if "ASP.NET" in cookies or "ASPSESSIONID" in cookies: techs.append("ASP.NET")
                if "laravel_session" in cookies: techs.append("Laravel")
            
            if resp.text:
                text_lower = resp.text.lower()
                if "wp-content" in text_lower or "wp-includes" in text_lower: techs.append("WordPress")
                if "nginx" in text_lower: techs.append("Nginx")
                if "joomla" in text_lower: techs.append("Joomla")
            
            tech = ", ".join(dict.fromkeys(techs)) if techs else "-"

        if status == 200: tag = "online"
        elif 300 <= status < 400: tag = "redirect"
        elif 400 <= status < 500: tag = "offline"
        elif status >= 500: tag = "erro"
        else: tag = "offline"

        return {
            "alvo": alvo, "path": path, "status": status,
            "title": title, "server": server, "clength": clength,
            "tech": tech, "url": url, "tag": tag
        }

    # ========== CONTROLE DE SCAN ==========

    def parar_scan(self):
        """Interrompe o scan em andamento."""
        if not self.executando:
            return
        
        self.abortar_scan = True
        self.log_console("⏹ Solicitando parada do scan...")
        self.lbl_scaneando.config(
            text="⏹ Parando scan... aguardando threads finalizarem",
            fg="#C62828", bg="#FFEBEE"
        )
        self.btn_stop.config(text="⏹ PARANDO...", state=tk.DISABLED)

    def iniciar_verificacao(self):
        if self.executando:
            return

        if self.modo_url.get():
            if not self.urls_manuais and not self.ips_carregados:
                self.carregar_urls()
                if not self.urls_manuais and not self.ips_carregados:
                    return
        else:
            if not self.ips_carregados and not self.urls_manuais:
                self.atualizar_status("Nenhum alvo!")
                return

        self.alvos = []
        for ip in self.ips_carregados:
            self.alvos.append(("ip", ip))
        for url in self.urls_manuais:
            self.alvos.append(("url", url))

        if not self.alvos:
            return

        self.executando = True
        self.abortar_scan = False  # Reseta a flag
        self.stats = {"online": 0, "offline": 0, "redirect": 0, "erro": 0}
        self.total_resultados = 0
        
        self.btn_verificar.config(text="⏳ SCANEANDO...", bg="#FF9800", state=tk.DISABLED)
        self.btn_stop.config(text="⏹ STOP", state=tk.NORMAL)
        self.btn_salvar_txt.config(state=tk.DISABLED)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        paths = self._get_paths()
        total_reqs = len(self.alvos) * len(paths)
        
        self.progresso["value"] = 0
        self.progresso["maximum"] = total_reqs

        self.lbl_scaneando.config(
            text=f"▶ Iniciando scan: {len(self.alvos)} alvo(s) x {len(paths)} paths = {total_reqs} requisições",
            fg="#1565C0", bg="#E3F2FD"
        )
        self.atualizar_status(f"Scan iniciado: {total_reqs} requisições")
        self.log_console(f"\n{'='*60}")
        self.log_console(f"🚀 SCAN INICIADO: {len(self.alvos)} alvo(s) | {len(paths)} path(s) = {total_reqs} requisições")
        self.log_console(f"{'='*60}\n")

        thread = threading.Thread(target=self.executar_scan)
        thread.daemon = True
        thread.start()

    def executar_scan(self):
        total_esperado = len(self.alvos) * len(self._get_paths())
        concluidos = 0

        def status_callback(msg):
            if not self.abortar_scan:
                self.root.after(0, self.lbl_scaneando.config, {"text": msg})

        with ThreadPoolExecutor(max_workers=self.max_threads.get()) as executor:
            self.executor_pool = executor
            futuros = {}
            for tipo, alvo in self.alvos:
                if self.abortar_scan:
                    break
                if tipo == "ip":
                    futuros[executor.submit(self.scan_ip, alvo, status_callback)] = alvo
                else:
                    futuros[executor.submit(self.scan_url, alvo, status_callback)] = alvo

            for futuro in as_completed(futuros):
                if self.abortar_scan:
                    # Cancela os futuros restantes
                    for f in futuros:
                        f.cancel()
                    break
                concluidos += 1
                try:
                    futuro.result()
                except Exception:
                    pass

                self.root.after(0, self._atualizar_barra, concluidos, total_esperado)

        self.executor_pool = None
        self.root.after(0, self._finalizar_scan)

    def _atualizar_barra(self, concluidos, total):
        self.progresso["value"] = concluidos
        self.progresso["maximum"] = max(total, concluidos)

    def _finalizar_scan(self):
        self.executando = False
        self.btn_verificar.config(text="▶ INICIAR SCAN", bg="#2196F3", state=tk.NORMAL)
        self.btn_stop.config(text="⏹ STOP", state=tk.DISABLED)
        self.btn_salvar_txt.config(state=tk.NORMAL)
        self.progresso["value"] = 0

        if self.abortar_scan:
            self.lbl_scaneando.config(
                text=f"⏹ SCAN ABORTADO pelo usuário! Parciais: {self.total_resultados} reqs",
                fg="#C62828", bg="#FFEBEE"
            )
            self.atualizar_status("⏹ Scan abortado")
            self.log_console(f"\n{'='*60}")
            self.log_console(f"⏹ SCAN ABORTADO PELO USUÁRIO")
            self.log_console(f"   Resultados parciais: {self.total_resultados}")
            self.log_console(f"{'='*60}")
            self.abortar_scan = False
        else:
            s = self.stats
            self.lbl_scaneando.config(
                text=f"✅ SCAN FINALIZADO! {self.total_resultados} respostas | 200: {s['online']} | 3xx: {s['redirect']} | 4xx: {s['offline']} | 5xx/Err: {s['erro']}",
                fg="#2E7D32", bg="#E8F5E9"
            )
            self.atualizar_status(
                f"✅ Finalizado! 200: {s['online']} | 3xx: {s['redirect']} | 4xx: {s['offline']} | 5xx/Err: {s['erro']}"
            )
            self.log_console(f"\n{'='*60}")
            self.log_console(f"✅ SCAN FINALIZADO!")
            self.log_console(f"   200: {s['online']} | 3xx: {s['redirect']} | 4xx: {s['offline']} | 5xx/Err: {s['erro']}")
            self.log_console(f"{'='*60}")

    def limpar_resultados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stats = {"online": 0, "offline": 0, "redirect": 0, "erro": 0}
        self.total_resultados = 0
        self.lbl_scaneando.config(text="⏳ Aguardando scan...", fg="#1565C0", bg="#E3F2FD")
        self.atualizar_info()
        self.atualizar_status("Limpou!")    

    def salvar_txt(self):
        """Salva apenas resultados com status 200 ou 3xx (exceto 304), pulando 4xx e 5xx."""
        padrao = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        arquivo = filedialog.asksaveasfilename(
            title="Salvar como TXT (apenas 200/3xx)",
            initialfile=padrao,
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )
        if not arquivo:
            return

        try:
            # Filtrar apenas resultados interessantes (200 e 3xx, sem 403/404/5xx)
            itens_interessantes = []
            for item_id in self.tree.get_children():
                valores = self.tree.item(item_id)["values"]
                status_raw = valores[2]
                try:
                    status_int = int(status_raw)
                except (ValueError, TypeError):
                    continue
                
                # Critério: 200 ou 3xx (mas não 304)
                if status_int == 200 or (300 <= status_int < 400 and status_int != 304):
                    itens_interessantes.append(valores)

            if not itens_interessantes:
                messagebox.showinfo("Info", "Nenhum resultado 200 ou 3xx para salvar.")
                return

            with open(arquivo, "w", encoding="utf-8") as f:
                alvo = self.urls_manuais[0] if self.urls_manuais else (self.ips_carregados[0] if self.ips_carregados else "N/A")
                
                f.write("=" * 210 + "\n")
                f.write("                                         SCAN HTTPX - RELATÓRIO (APENAS 200 E 3xx)\n")
                f.write("=" * 210 + "\n")

                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(f"Alvo: {alvo}\n\n")
                f.write(f"Wordlist: {len(self.wordlist)} paths\n\n" if self.wordlist else "Wordlist: não usada\n\n")
                f.write(f"UAs: {len(self.user_agents)}\n\n" if self.user_agents else "UA: padrão\n\n")
                f.write(f"Timeout: {self.timeout.get()}s | Threads: {self.max_threads.get()}\n\n")
                
                s = self.stats
                f.write(f"Total resultados na tela: {self.total_resultados}\n")
                f.write(f"200: {s['online']} | 3xx: {s['redirect']} | 4xx: {s['offline']} | 5xx/Err: {s['erro']}\n")
                f.write(f"Linhas salvas no relatório: {len(itens_interessantes)} (filtrado: apenas 200 e 3xx)\n")
                f.write("=" * 210 + "\n\n")
                
                cab = f"{'Alvo':<28} {'Path':<22} {'Status':<8} {'Título':<45} {'Server':<20} {'Size':<12} {'Tecnologias':<25} URL\n"
                f.write(cab)
                f.write("-" * 210 + "\n")
                
                for v in itens_interessantes:
                    linha = (
                        f"{str(v[0])[:26]:<28} "
                        f"{str(v[1])[:20]:<22} "
                        f"{str(v[2]):<8} "
                        f"{str(v[3])[:43]:<45} "
                        f"{str(v[4])[:18]:<20} "
                        f"{str(v[5]):<12} "
                        f"{str(v[6])[:23]:<25} "
                        f"{v[7]}"
                    )
                    f.write(linha + "\n")
                
                f.write("\n" + "=" * 210 + "\n")
                f.write("FIM\n")
                f.write("=" * 210 + "\n")
                
            self.atualizar_status(f"✅ Salvo: {os.path.basename(arquivo)} ({len(itens_interessantes)} linhas)")
            self.log_console(f"📄 Relatório TXT salvo: {arquivo} ({len(itens_interessantes)} resultados 200/3xx)")
            messagebox.showinfo("Sucesso", f"Relatório salvo com {len(itens_interessantes)} resultado(s):\n{arquivo}")
                
        except Exception as e:
            self.atualizar_status(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha:\n{str(e)}")

    # ========== FECHAMENTO LIMPO ==========

    def fechar_aplicacao(self):
        """Método chamado ao fechar a janela. Finaliza tudo de forma limpa."""
        self.log_console("🛑 Fechando aplicação...")
        
        # Se estiver escaneando, aborta
        if self.executando:
            self.abortar_scan = True
        
        # Aguarda um momento para threads finalizarem
        if self.executando:
            import time
            time.sleep(0.5)
        
        # Destroi a janela
        self.root.destroy()
        
        # Força saída do processo (mata qualquer thread órfã)
        # No Windows, isso garante que não fique nada no Gerenciador de Tarefas
        os._exit(0)

    def atualizar_status(self, msg):
        self.lbl_status.config(text=msg)


if __name__ == "__main__":
    import warnings
    import urllib3
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    root = tk.Tk()
    app = ScannerHTTPX(root)
    
    # Também captura Ctrl+C no terminal
    def signal_handler(sig, frame):
        app.log_console("🛑 Ctrl+C detectado. Fechando...")
        app.fechar_aplicacao()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    root.mainloop()
