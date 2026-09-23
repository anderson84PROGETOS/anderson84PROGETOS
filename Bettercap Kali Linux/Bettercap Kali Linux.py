import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import queue
import platform
import os
import signal
import re
import sys


# =============================================================
# VERIFICAÇÃO DE SISTEMA — SOMENTE KALI LINUX
# =============================================================

def verificar_kali_linux():
    if platform.system() != "Linux":
        return (False, f"Sistema operacional detectado: {platform.system()}\n\n"
                       "Esta aplicação funciona SOMENTE em Kali Linux.")

    caminho_os_release = "/etc/os-release"
    if not os.path.exists(caminho_os_release):
        return (False, "Arquivo /etc/os-release não encontrado.\n\n"
                       "Não foi possível confirmar que este sistema é Kali Linux.")

    try:
        with open(caminho_os_release, "r") as arquivo:
            conteudo = arquivo.read().lower()

        if "kali" not in conteudo:
            nome_sistema = "Desconhecido"
            for linha in conteudo.split("\n"):
                if linha.startswith("pretty_name="):
                    nome_sistema = linha.split("=", 1)[1].strip('"')
                    break
            return (False, f"Sistema detectado: {nome_sistema}\n\n"
                           "Esta aplicação funciona SOMENTE em Kali Linux.")
    except Exception as erro:
        return (False, f"Erro ao ler /etc/os-release:\n{erro}")

    try:
        resultado = subprocess.run(["which", "bettercap"], capture_output=True, text=True, timeout=5)
        if resultado.returncode != 0 or not resultado.stdout.strip():
            return (False, "Bettercap não está instalado neste Kali Linux.\n\n"
                           "Instale com o comando:\n  sudo apt update && sudo apt install bettercap")
    except Exception as erro:
        return (False, f"Erro ao verificar Bettercap:\n{erro}")

    if os.geteuid() != 0:
        return (False, "Esta aplicação precisa ser executada como ROOT.\n\n"
                       "Execute com:\n  sudo python3 " + os.path.basename(sys.argv[0]))

    return (True, "")


# =============================================================
# CLASSE PRINCIPAL
# =============================================================

class BettercapGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Bettercap Kali Linux")
        self.root.geometry("1050x780")
        self.root.minsize(800, 600)

        self.root.after(200, lambda: self.root.attributes("-zoomed", True))

        self.process = None
        self.output_queue = queue.Queue()

        self.arp_spoof_ativo = False
        self.net_sniff_ativo = False
        self.net_show_ativo = False
        self.tcpdump_process = None

        # Cores
        self.bg = "#0d1117"
        self.panel = "#161b22"
        self.console_bg = "#010409"
        self.text = "#c9d1d9"
        self.subtext = "#8b949e"
        self.green = "#3fb950"
        self.red = "#f85149"
        self.blue = "#58a6ff"
        self.orange = "#d29922"
        self.purple = "#a371f7"
        self.yellow = "#e3b341"
        self.cyan = "#39c5cf"
        self.border = "#30363d"

        self.root.configure(bg=self.bg)

        self.modo_raw = False
        self.filtro = "todos"          # todos | header | cred | arp | host | netshow

        self.buffer_filtrado = []      # guarda linhas já classificadas para re-render
        self.MAX_BUFFER = 3000

        self.interface = self.detectar_interface()
        self.criar_interface()

        self.root.after(100, self.processar_saida)
        self.root.protocol("WM_DELETE_WINDOW", self.sair)

    # =========================================================
    # DETECTAR INTERFACE DE REDE
    # =========================================================

    def detectar_interface(self):
        try:
            resultado = subprocess.run(["ip", "-o", "link", "show"],
                                       capture_output=True, text=True, timeout=5)
            interfaces = []
            for linha in resultado.stdout.split("\n"):
                match = re.match(r'\d+:\s+([^:@]+)', linha)
                if match:
                    nome = match.group(1).strip()
                    if nome != "lo":
                        interfaces.append(nome)

            for preferida in ["eth0", "wlan0", "enp0s3", "enp0s8"]:
                if preferida in interfaces:
                    return preferida
            if interfaces:
                return interfaces[0]
        except Exception:
            pass
        return "eth0"

    # =========================================================
    # INTERFACE
    # =========================================================

    def criar_interface(self):

        tk.Label(self.root, text="Bettercap Kali Linux",
                 font=("Segoe UI", 24, "bold"),
                 fg=self.blue, bg=self.bg).pack(pady=(18, 2))

        tk.Label(self.root, text=f"Kali Linux • Interface: {self.interface} • root",
                 font=("Segoe UI", 10), fg=self.green, bg=self.bg).pack(pady=(0, 15))

        # PAINEL DOS BOTÕES PRINCIPAIS
        painel = tk.Frame(self.root, bg=self.panel,
                          highlightbackground=self.border, highlightthickness=1)
        painel.pack(fill="x", padx=15, pady=(0, 10))

        self.btn_ligar = tk.Button(painel, text="▶  LIGAR", command=self.ligar,
                                   font=("Segoe UI", 11, "bold"),
                                   bg="#238636", fg="white",
                                   activebackground="#2ea043", activeforeground="white",
                                   relief="flat", cursor="hand2", padx=25, pady=10)
        self.btn_ligar.pack(side="left", padx=10, pady=10)

        self.btn_desligar = tk.Button(painel, text="■  DESLIGAR", command=self.desligar,
                                      font=("Segoe UI", 11, "bold"),
                                      bg="#da3633", fg="white",
                                      activebackground="#f85149", activeforeground="white",
                                      relief="flat", cursor="hand2", padx=25, pady=10,
                                      state="disabled")
        self.btn_desligar.pack(side="left", padx=5, pady=10)

        self.btn_limpar = tk.Button(painel, text="⌫  LIMPAR LOG", command=self.limpar_log,
                                    font=("Segoe UI", 10, "bold"),
                                    bg="#30363d", fg="white",
                                    activebackground="#484f58", activeforeground="white",
                                    relief="flat", cursor="hand2", padx=18, pady=10)
        self.btn_limpar.pack(side="left", padx=5, pady=10)

        self.btn_pcap = tk.Button(painel, text="💾  SALVAR CAPTURA: OFF", command=self.toggle_pcap,
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#6e7681", fg="white",
                                  activebackground="#8b949e", activeforeground="white",
                                  relief="flat", cursor="hand2", padx=18, pady=10)
        self.btn_pcap.pack(side="left", padx=5, pady=10)

        self.btn_sair = tk.Button(painel, text="✕  SAIR", command=self.sair,
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#30363d", fg="white",
                                  activebackground="#484f58", activeforeground="white",
                                  relief="flat", cursor="hand2", padx=18, pady=10)
        self.btn_sair.pack(side="right", padx=10, pady=10)

        # PAINEL DE MÓDULOS
        painel_modulos = tk.Frame(self.root, bg=self.panel,
                                  highlightbackground=self.border, highlightthickness=1)
        painel_modulos.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(painel_modulos, text="MÓDULOS:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.text, bg=self.panel).pack(side="left", padx=(15, 10), pady=10)

        self.btn_arp = tk.Button(painel_modulos, text="⚡  ARP SPOOF: OFF",
                                 command=self.toggle_arp_spoof,
                                 font=("Segoe UI", 10, "bold"),
                                 bg="#6e7681", fg="white",
                                 activebackground="#8b949e", activeforeground="white",
                                 relief="flat", cursor="hand2", padx=18, pady=8,
                                 state="disabled")
        self.btn_arp.pack(side="left", padx=5, pady=10)

        self.btn_sniff = tk.Button(painel_modulos, text="👁  NET SNIFF: OFF",
                                   command=self.toggle_net_sniff,
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#6e7681", fg="white",
                                   activebackground="#8b949e", activeforeground="white",
                                   relief="flat", cursor="hand2", padx=18, pady=8,
                                   state="disabled")
        self.btn_sniff.pack(side="left", padx=5, pady=10)

        tk.Label(painel_modulos, text="Alvo:",
                 font=("Segoe UI", 9, "bold"),
                 fg=self.subtext, bg=self.panel).pack(side="left", padx=(20, 5), pady=10)

        self.entrada_alvo = tk.Entry(painel_modulos, bg=self.console_bg, fg=self.text,
                                     insertbackground="white", font=("Consolas", 10),
                                     relief="flat", width=25)
        self.entrada_alvo.pack(side="left", padx=5, pady=10, ipady=5)
        self.entrada_alvo.insert(0, "192.168.0.3")

        # =====================================================
        # PAINEL DE FILTROS (NET SHOW AO LADO DE HOSTS)
        # =====================================================
        painel_filtro = tk.Frame(self.root, bg=self.panel,
                                 highlightbackground=self.border, highlightthickness=1)
        painel_filtro.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(painel_filtro, text="FILTROS:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.text, bg=self.panel).pack(side="left", padx=(15, 10), pady=8)

        self.btns_filtro = {}
        filtros = [
            ("todos",   "☰  TODOS",        self.blue),
            ("header",  "HTTP HEADER",     self.cyan),
            ("cred",    "🔑 CREDENCIAIS",  self.yellow),
            ("arp",     "⚡ ARP",          self.orange),
            ("host",    "🖥 HOSTS",        self.purple),
            ("netshow", "🖥 NET SHOW",     self.green),
        ]

        for chave, texto, cor in filtros:
            b = tk.Button(painel_filtro, text=texto,
                          command=lambda c=chave: self.set_filtro(c),
                          font=("Segoe UI", 9, "bold"),
                          bg="#30363d", fg="white",
                          activebackground="#484f58", activeforeground="white",
                          relief="flat", cursor="hand2", padx=12, pady=6)
            b.pack(side="left", padx=4, pady=8)
            self.btns_filtro[chave] = b

        self.btn_raw = tk.Button(painel_filtro, text="</> RAW: OFF",
                                 command=self.toggle_raw,
                                 font=("Segoe UI", 9, "bold"),
                                 bg="#30363d", fg="white",
                                 activebackground="#484f58", activeforeground="white",
                                 relief="flat", cursor="hand2", padx=12, pady=6)
        self.btn_raw.pack(side="right", padx=(4, 15), pady=8)

        self.marcar_filtro_ativo()

        # STATUS
        status_frame = tk.Frame(self.root, bg=self.bg)
        status_frame.pack(fill="x", padx=15, pady=(0, 8))

        tk.Label(status_frame, text="STATUS:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.text, bg=self.bg).pack(side="left")

        self.status_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 16),
                                   fg=self.red, bg=self.bg)
        self.status_dot.pack(side="left", padx=6)

        self.status_label = tk.Label(status_frame, text="DESLIGADO",
                                     font=("Segoe UI", 10, "bold"),
                                     fg=self.red, bg=self.bg)
        self.status_label.pack(side="left")

        # CONSOLE
        tk.Label(self.root, text="CONSOLE / LOG DO BETTERCAP",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.text, bg=self.bg, anchor="w").pack(fill="x", padx=15)

        console_frame = tk.Frame(self.root, bg=self.console_bg,
                                 highlightbackground=self.border, highlightthickness=1)
        console_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        self.console = tk.Text(console_frame, bg=self.console_bg, fg=self.text,
                               insertbackground="white", selectbackground="#264f78",
                               font=("Consolas", 10), relief="flat", wrap="none",
                               state="disabled")
        self.console.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical
        scrollbar = tk.Scrollbar(console_frame, command=self.console.yview)
        scrollbar.pack(side="right", fill="y")
        self.console.configure(yscrollcommand=scrollbar.set)

       
        # TAGS DE COR
        self.console.tag_config("header",    foreground=self.cyan,    font=("Consolas", 10, "bold"))
        self.console.tag_config("result",    foreground=self.blue,    font=("Consolas", 10))
        self.console.tag_config("method",    foreground=self.blue,    font=("Consolas", 10, "bold"))
        self.console.tag_config("url",       foreground=self.cyan,    font=("Consolas", 10))
        self.console.tag_config("ip",        foreground=self.yellow,  font=("Consolas", 10, "bold"))
        self.console.tag_config("info",      foreground=self.subtext)
        self.console.tag_config("warn",      foreground=self.orange,  font=("Consolas", 10, "bold"))
        self.console.tag_config("error",     foreground=self.red,     font=("Consolas", 10, "bold"))
        self.console.tag_config("success",   foreground=self.green,   font=("Consolas", 10, "bold"))
        self.console.tag_config("separator", foreground=self.border)
        self.console.tag_config("field",     foreground=self.purple,  font=("Consolas", 10, "bold"))
        self.console.tag_config("value",     foreground=self.blue,    font=("Consolas", 10))
        self.console.tag_config("gui",       foreground=self.blue,    font=("Consolas", 10, "bold"))
        self.console.tag_config("cred",      foreground=self.yellow,  font=("Consolas", 10, "bold"))
        self.console.tag_config("netshow",   foreground=self.green,   font=("Consolas", 10))
        self.console.tag_config("table",     foreground=self.border)

        # ÁREA DE COMANDO
        comando_frame = tk.Frame(self.root, bg=self.bg)
        comando_frame.pack(fill="x", padx=15, pady=(0, 15))

        tk.Label(comando_frame, text="bettercap >",
                 font=("Consolas", 10, "bold"),
                 fg=self.green, bg=self.bg).pack(side="left", padx=(0, 8))

        self.entrada = tk.Entry(comando_frame, bg=self.console_bg, fg=self.text,
                                insertbackground="white", font=("Consolas", 10), relief="flat")
        self.entrada.pack(side="left", fill="x", expand=True, ipady=9)
        self.entrada.bind("<Return>", lambda event: self.enviar_comando())

        self.btn_enviar = tk.Button(comando_frame, text="ENVIAR", command=self.enviar_comando,
                                    font=("Segoe UI", 10, "bold"),
                                    bg=self.blue, fg="white",
                                    activebackground="#79c0ff", activeforeground="white",
                                    relief="flat", cursor="hand2", padx=20, pady=7)
        self.btn_enviar.pack(side="left", padx=(8, 0))

        # Mensagem inicial
        self.escrever("[GUI] Bettercap iniciado no Kali Linux.\n", tag="success")
        self.escrever(f"[GUI] Interface detectada: {self.interface}\n", tag="gui")
        self.escrever("[GUI] Executando como root: OK\n", tag="success")
        self.escrever("[GUI] Clique em LIGAR para iniciar o Bettercap.\n\n", tag="gui")

    # =========================================================
    # FILTROS
    # =========================================================

    def set_filtro(self, chave):
        self.filtro = chave
        self.marcar_filtro_ativo()
        self.re_renderizar()

        # NOVO: ao clicar no filtro NET SHOW, dispara o scan e exibe a tabela
        if chave == "netshow":
            if self.process is None:
                self.escrever("\n[GUI] Bettercap está desligado — ligue antes de usar o NET SHOW.\n", tag="warn")
            else:
                self.enviar_comando_interno("net.probe on")
                self.enviar_comando_interno("net.show")
        else:
            self.escrever(f"\n[GUI] Filtro ativo: {chave.upper()}\n", tag="gui")

    def marcar_filtro_ativo(self):
        for chave, b in self.btns_filtro.items():
            if chave == self.filtro:
                b.config(bg=self.green, fg="black")
            else:
                b.config(bg="#30363d", fg="white")

    def toggle_raw(self):
        self.modo_raw = not self.modo_raw
        self.btn_raw.config(text=f"</> RAW: {'ON' if self.modo_raw else 'OFF'}",
                            bg=self.green if self.modo_raw else "#30363d",
                            fg="black" if self.modo_raw else "white")
        self.re_renderizar()

    def re_renderizar(self):
        """Limpa o console e reescreve o buffer aplicando o filtro atual."""
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

        for tipo, partes in list(self.buffer_filtrado):
            if self.deve_mostrar(tipo):
                self.console.config(state="normal")
                for texto, tag in partes:
                    self.escrever(texto, tag=tag)
                self.console.config(state="disabled")
        self.console.see("end")

    def deve_mostrar(self, tipo):
        if self.filtro == "todos":
            return True
        return tipo == self.filtro

    # =========================================================
    # ESCREVER NO CONSOLE
    # =========================================================

    def escrever(self, texto, tag=None):
        self.console.config(state="normal")
        if tag:
            self.console.insert("end", texto, tag)
        else:
            self.console.insert("end", texto)
        self.console.config(state="disabled")
        self.console.see("end")

    def limpar_log(self):
        self.buffer_filtrado = []
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    # =========================================================
    # FORMATADOR DE LINHAS — retorna (tipo, partes)
    # =========================================================

    def formatar_linha(self, linha):

        ansi_re = re.compile(r'\x1b\[[0-9;]*[mGKHF]')
        linha = ansi_re.sub('', linha)
        linha = re.sub(r'\[\d{1,2}:\d{2}:\d{2}\]\s*', '', linha)
        linha = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}\s*', '', linha)
        linha = re.sub(r'\d{1,2}:\d{2}:\d{2}\s+', '', linha)

        linha_limpa = linha.rstrip("\n")
        if not linha_limpa.strip():
            return None

        low = linha_limpa.lower()
        strip = linha_limpa.strip()

        # =====================================================
        # TABELA NET SHOW (bordas de tabela do bettercap)
        # =====================================================
        chars_tabela = "│┌└├┤┬┴┼─▾▴"

        # Linha de dados: │ IP │ MAC │ Name │ ...
        if '│' in linha_limpa:
            colunas = [c.strip() for c in linha_limpa.split('│')]

            # Cabeçalho da tabela (IP / MAC / Name / Vendor...)
            if any('ip' == c.lower().rstrip('▴▾ ') or c.lower().startswith('ip ') for c in colunas):
                return ("netshow", [
                    ("\n", None),
                    ("┌─ NET SHOW — DISPOSITIVOS NA REDE ", "header"),
                    ("─" * 30 + "\n", "separator"),
                    ("│ ", "separator"),
                    (f"{'IP':38s}", "ip"),
                    (f"{'MAC':20s}", "field"),
                    (f"{'Name':20s}", "netshow"),
                    (f"{'Vendor':40s}", "value"),
                    (f"{'Sent':10s}", "result"),
                    (f"{'Recvd':10s}", "result"),
                    ("Seen\n", "result"),
                ])

            # Linha de dados da tabela
            dados = [c for c in colunas if c]
            if len(dados) >= 2:
                ip = mac = nome = vendor = sent = recvd = visto = ""
                extras = []
                # tenta casar IP (v4 ou v6) como primeira coluna
                for i, c in enumerate(dados):
                    if re.match(r'^[\d\.]{7,15}$', c) or ':' in c and re.match(r'^[\da-fA-F:]+$', c) and len(c) > 6:
                        ip = c
                        resto = dados[i + 1:]
                        if len(resto) >= 1:
                            mac = resto[0]
                        if len(resto) >= 2:
                            nome = resto[1]
                        if len(resto) >= 3:
                            vendor = resto[2]
                        if len(resto) >= 4:
                            sent = resto[3]
                        if len(resto) >= 5:
                            recvd = resto[4]
                        if len(resto) >= 6:
                            visto = " ".join(resto[5:])
                        break
                if ip:
                    partes = [("│ ", "separator"), (f"{ip:38s}", "ip"),
                              (f"{mac:20s}", "field"),
                              (f"{nome:20s}", "netshow"),
                              (f"{vendor:40s}", "value"),
                              (f"{sent:10s}", "result"),
                              (f"{recvd:10s}", "result"),
                              (f"{visto}\n", "info")]
                    return ("netshow", partes)

            # Linhas de borda ┌─┬─┐ ├─┼─┤ └─┴─┘ → mantém como tabela (tipo netshow)
            if any(ch in strip for ch in "┌└├┤┬┴┼") or re.match(r'^[─\-\+]+$', strip):
                return ("netshow", [("  ", None), (strip + "\n", "table")])

            # Linha totalmente vazia dentro da tabela
            return ("netshow", [("  \n", None)])

        # ---------- REQUISIÇÃO HTTP (uma linha só) ----------
        http_match = re.match(
            r'^(?:http\s+)?([\d\.]+)\s*(?:>|→)\s*([\w\.\-]+)?\s*'
            r'(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(\S+)',
            strip, re.IGNORECASE
        ) or re.match(
            r'^http\s+([\d\.]+)\s+(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(\S+)',
            strip, re.IGNORECASE
        )

        if http_match:
            grupos = http_match.groups()
            if len(grupos) == 4:
                src, host, method, path = grupos
            else:
                src, method, path = grupos
                host = ""

            partes = [
                ("\n", None),
                ("┌─ HTTP REQUEST ", "header"),
                ("─" * 50 + "\n", "separator"),
                ("│ ", "separator"),
                (f"{method:8s}", "method"),
                (f"{path}\n", "url"),
            ]
            if host:
                partes += [("│ ", "separator"), ("Host:    ", "field"), (f"{host}\n", "result")]
            partes += [
                ("│ ", "separator"), ("Source:  ", "field"), (f"{src}\n", "result"),
                ("└" + "─" * 65 + "\n", "separator"),
            ]
            return ("http", partes)

        # ---------- CABEÇALHOS HTTP ----------
        header_match = re.match(
            r'^[•\-\s]*(Host|Connection|Cache-Control|Upgrade-Insecure-Requests|'
            r'User-Agent|Accept(?:-Encoding|-Language)?|Referer|Cookie|Authorization|'
            r'Content-Length|Content-Type|Origin)\s*:\s*(.*)$',
            strip
        )
        if header_match:
            campo, valor = header_match.groups()
            return ("header", [
                ("│ ", "separator"),
                (f"{campo:12s}", "field"),
                (f"{valor}\n", "result"),
            ])

        # ---------- CORPO HTTP (username=...&password=...) ----------
        body_match = re.match(
            r'^[•\-\s]*((?:username|user|login|email|password|pass|passwd|token)'
            r'\s*=\s*[^&\s]+(?:\s*&\s*[^&\s]+)*)\s*$',
            strip, re.IGNORECASE
        )
        if body_match:
            corpo = body_match.group(1)
            return ("cred", [
                ("│ ", "separator"),
                ("Body:     ", "field"),
                (f"{corpo}\n", "cred"),
                ("└" + "─" * 65 + "\n", "separator"),
            ])

        # ---------- LINHA DE REQUISIÇÃO ----------
        req_match = re.match(
            r'^[•\-\s]*(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(\S+)\s+HTTP/[\d\.]+$',
            strip, re.IGNORECASE
        )
        if req_match:
            method, path = req_match.groups()
            return ("header", [
                ("│ ", "separator"),
                (f"{method:8s}", "method"),
                (f"{path}\n", "url"),
            ])

        # ---------- ARP SPOOF ----------
        arp_match = re.search(r'arp\.spoof.*?([\d\.]+).*?([\d\.]+)', low)
        if 'arp.spoof' in low and arp_match:
            ip1, ip2 = arp_match.groups()
            return ("arp", [
                ("┌─ ARP SPOOF ", "header"),
                ("─" * 52 + "\n", "separator"),
                ("│ ", "separator"), ("Target:  ", "field"), (f"{ip1}\n", "ip"),
                ("│ ", "separator"), ("Gateway: ", "field"), (f"{ip2}\n", "ip"),
                ("└" + "─" * 65 + "\n", "separator"),
            ])

        # ---------- CREDENCIAIS ----------
        if 'credential' in low or 'password' in low:
            cred_match = re.search(r'(\S+)\s*:\s*(\S+)', strip)
            if cred_match:
                user, pwd = cred_match.groups()
                return ("cred", [
                    ("\n", None),
                    ("┌─ ⚠ CREDENCIAL ", "cred"),
                    ("─" * 49 + "\n", "separator"),
                    ("│ ", "separator"), ("User:     ", "field"), (f"{user}\n", "value"),
                    ("│ ", "separator"), ("Password: ", "field"), (f"{pwd}\n", "cred"),
                    ("└" + "─" * 65 + "\n", "separator"),
                ])

        # ---------- NEW HOST ----------
        host_match = re.search(r'(?:endpoint|new host).*?([\d\.]+).*?([0-9a-fA-F:]{17})?', low)
        if host_match and ('endpoint' in low or 'new host' in low):
            ip = host_match.group(1)
            mac = host_match.group(2) or "unknown"
            return ("host", [
                ("┌─ NEW HOST ", "header"),
                ("─" * 53 + "\n", "separator"),
                ("│ ", "separator"), ("IP:  ", "field"), (f"{ip}\n", "ip"),
                ("│ ", "separator"), ("MAC: ", "field"), (f"{mac}\n", "value"),
                ("└" + "─" * 65 + "\n", "separator"),
            ])

        # ---------- ERROS / WARN / STATUS ----------
        if 'error' in low or 'err' in low[:10]:
            return ("info", [("✗ ERROR: ", "error"), (strip + "\n", "error")])

        if 'warn' in low[:15]:
            return ("info", [("⚠ WARN:  ", "warn"), (strip + "\n", "info")])

        if 'started' in low or 'running' in low:
            return ("info", [("✓ ", "success"), (strip + "\n", "success")])

        if 'stopped' in low:
            return ("info", [("■ ", "warn"), (strip + "\n", "info")])

        linha_sem_prefixo = re.sub(r'^([•\-\s]*|\[[^\]]+\]\s*)+', '', strip)
        return ("info", [("• ", "subtext"), (linha_sem_prefixo + "\n", "info")])

    # =========================================================
    # LIGAR BETTERCAP
    # =========================================================

    def ligar(self):
        if self.process is not None:
            return

        comando = ["bettercap", "-iface", self.interface]

        self.escrever("\n[GUI] Iniciando Bettercap...\n", tag="gui")
        self.escrever("[GUI] Comando: " + " ".join(comando) + "\n\n", tag="gui")

        try:
            self.process = subprocess.Popen(
                comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                start_new_session=True
            )
        except FileNotFoundError:
            self.process = None
            self.escrever("[ERRO] Bettercap não encontrado.\n", tag="error")
            messagebox.showerror("Erro", "Bettercap não foi encontrado.\n\n"
                               "Instale com:\nsudo apt install bettercap")
            return
        except Exception as erro:
            self.process = None
            self.escrever(f"[ERRO] {erro}\n", tag="error")
            messagebox.showerror("Erro", str(erro))
            return

        self.status_dot.config(fg=self.green)
        self.status_label.config(text="LIGADO", fg=self.green)
        self.btn_ligar.config(state="disabled")
        self.btn_desligar.config(state="normal")
        self.btn_arp.config(state="normal", bg=self.orange)
        self.btn_sniff.config(state="normal", bg=self.purple)

        threading.Thread(target=self.ler_saida, daemon=True).start()

    # =========================================================
    # LER SAÍDA
    # =========================================================

    def ler_saida(self):
        processo = self.process
        if processo is None:
            return
        try:
            for linha in iter(processo.stdout.readline, ""):
                if linha:
                    self.output_queue.put(linha)
            processo.stdout.close()
        except Exception as erro:
            self.output_queue.put(f"[ERRO] {erro}\n")
        finally:
            self.output_queue.put("__ENCERRADO__")

    # =========================================================
    # PROCESSAR LOG (com filtro)
    # =========================================================

    def processar_saida(self):
        try:
            while True:
                linha = self.output_queue.get_nowait()

                if linha == "__ENCERRADO__":
                    self.process = None
                    self.status_dot.config(fg=self.red)
                    self.status_label.config(text="DESLIGADO", fg=self.red)
                    self.btn_ligar.config(state="normal")
                    self.btn_desligar.config(state="disabled")
                    self.arp_spoof_ativo = False
                    self.net_sniff_ativo = False
                    self.btn_arp.config(state="disabled", text="⚡  ARP SPOOF: OFF", bg="#6e7681")
                    self.btn_sniff.config(state="disabled", text="👁  NET SNIFF: OFF", bg="#6e7681")
                else:
                    resultado = self.formatar_linha(linha)
                    if resultado:
                        tipo, partes = resultado

                        self.buffer_filtrado.append((tipo, partes))
                        if len(self.buffer_filtrado) > self.MAX_BUFFER:
                            self.buffer_filtrado = self.buffer_filtrado[-self.MAX_BUFFER:]

                        if self.modo_raw:
                            self.escrever(linha)
                        elif self.deve_mostrar(tipo):
                            for texto, tag in partes:
                                self.escrever(texto, tag=tag)

        except queue.Empty:
            pass

        self.root.after(100, self.processar_saida)

    # =========================================================
    # ENVIAR COMANDO INTERNO
    # =========================================================

    def enviar_comando_interno(self, comando):
        if self.process is None:
            return False
        try:
            self.process.stdin.write(comando + "\n")
            self.process.stdin.flush()
            self.escrever(f"\n▶ {comando}\n", tag="gui")
            return True
        except Exception as erro:
            self.escrever(f"[ERRO] {erro}\n", tag="error")
            return False

    # =========================================================
    # TOGGLE ARP SPOOF
    # =========================================================

    def toggle_arp_spoof(self):
        if self.process is None:
            messagebox.showwarning("Bettercap", "O Bettercap está desligado.")
            return

        if not self.arp_spoof_ativo:
            alvo = self.entrada_alvo.get().strip()
            if not alvo:
                messagebox.showwarning("ARP Spoof", "Digite o(s) IP(s) alvo.")
                return
            self.enviar_comando_interno(f"set arp.spoof.targets {alvo}")
            self.enviar_comando_interno("set arp.spoof.fullduplex true")
            if self.enviar_comando_interno("arp.spoof on"):
                self.arp_spoof_ativo = True
                self.btn_arp.config(text="⚡  ARP SPOOF: ON", bg=self.green)
        else:
            if self.enviar_comando_interno("arp.spoof off"):
                self.arp_spoof_ativo = False
                self.btn_arp.config(text="⚡  ARP SPOOF: OFF", bg=self.orange)

    # =========================================================
    # TOGGLE NET SNIFF
    # =========================================================

    def toggle_net_sniff(self):
        if self.process is None:
            messagebox.showwarning("Bettercap", "O Bettercap está desligado.")
            return

        if not self.net_sniff_ativo:
            self.enviar_comando_interno("set net.sniff.verbose true")
            if self.enviar_comando_interno("net.sniff on"):
                self.net_sniff_ativo = True
                self.btn_sniff.config(text="👁  NET SNIFF: ON", bg=self.green)
        else:
            if self.enviar_comando_interno("net.sniff off"):
                self.net_sniff_ativo = False
                self.btn_sniff.config(text="👁  NET SNIFF: OFF", bg=self.purple)

    # =========================================================
    # TOGGLE SALVAR CAPTURA (PCAP)
    # =========================================================

    def toggle_pcap(self):
        if self.tcpdump_process is None:
            caminho = os.path.join(os.getcwd(), "captura.pcap")
            try:
                self.tcpdump_process = subprocess.Popen(
                    ["tcpdump", "-i", self.interface, "-w", caminho],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except FileNotFoundError:
                messagebox.showerror("Erro", "tcpdump não foi encontrado.\n\n"
                                     "Instale com:\nsudo apt install tcpdump")
                return
            self.escrever(f"\n[GUI] Salvando captura em: {caminho}\n", tag="gui")
            self.btn_pcap.config(text="💾  SALVAR CAPTURA: ON", bg=self.green)
        else:
            self.parar_pcap()
            self.escrever("[GUI] Captura encerrada — arquivo captura.pcap salvo.\n", tag="success")

    def parar_pcap(self):
        if self.tcpdump_process is not None:
            try:
                os.killpg(os.getpgid(self.tcpdump_process.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.tcpdump_process.terminate()
                except Exception:
                    pass
            self.tcpdump_process = None
            self.btn_pcap.config(text="💾  SALVAR CAPTURA: OFF", bg="#6e7681")

    # =========================================================
    # ENVIAR COMANDO MANUAL
    # =========================================================

    def enviar_comando(self):
        if self.process is None:
            messagebox.showwarning("Bettercap", "O Bettercap está desligado.")
            return
        comando = self.entrada.get().strip()
        if not comando:
            return
        try:
            self.process.stdin.write(comando + "\n")
            self.process.stdin.flush()
            self.escrever(f"\n▶ {comando}\n", tag="gui")
            self.entrada.delete(0, "end")
        except Exception as erro:
            self.escrever(f"[ERRO] {erro}\n", tag="error")

    # =========================================================
    # DESLIGAR
    # =========================================================

    def desligar(self):
        if self.process is None:
            return
        self.escrever("\n[GUI] Desligando Bettercap...\n", tag="gui")
        self.parar_pcap()

        if self.arp_spoof_ativo:
            try:
                self.enviar_comando_interno("arp.spoof off")
            except Exception:
                pass
        if self.net_sniff_ativo:
            try:
                self.enviar_comando_interno("net.sniff off")
            except Exception:
                pass

        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        except Exception:
            try:
                self.process.terminate()
            except Exception:
                pass

    # =========================================================
    # SAIR
    # =========================================================

    def sair(self):
        if self.process is not None:
            try:
                self.desligar()
            except Exception:
                pass
        self.parar_pcap()
        self.root.after(200, self.root.destroy)


# =============================================================
# TELA DE ERRO (quando não é Kali)
# =============================================================

def mostrar_erro_sistema(motivo):
    erro_root = tk.Tk()
    erro_root.title("Sistema Incompatível")
    erro_root.geometry("550x350")
    erro_root.configure(bg="#0d1117")
    erro_root.resizable(False, False)

    erro_root.update_idletasks()
    x = (erro_root.winfo_screenwidth() - 550) // 2
    y = (erro_root.winfo_screenheight() - 350) // 2
    erro_root.geometry(f"550x350+{x}+{y}")

    tk.Label(erro_root, text="⛔", font=("Segoe UI", 60),
             fg="#f85149", bg="#0d1117").pack(pady=(20, 5))

    tk.Label(erro_root, text="SISTEMA INCOMPATÍVEL",
             font=("Segoe UI", 16, "bold"),
             fg="#f85149", bg="#0d1117").pack(pady=(0, 15))

    frame_msg = tk.Frame(erro_root, bg="#161b22",
                         highlightbackground="#30363d", highlightthickness=1)
    frame_msg.pack(fill="x", padx=30, pady=(0, 20))

    tk.Label(frame_msg, text=motivo, font=("Consolas", 10),
             fg="#c9d1d9", bg="#161b22", justify="left",
             wraplength=470).pack(padx=15, pady=15)

    tk.Button(erro_root, text="FECHAR", command=erro_root.destroy,
              font=("Segoe UI", 10, "bold"),
              bg="#da3633", fg="white",
              activebackground="#f85149", activeforeground="white",
              relief="flat", cursor="hand2", padx=30, pady=8).pack()

    erro_root.mainloop()


# =============================================================
# INICIAR
# =============================================================

if __name__ == "__main__":
    valido, motivo = verificar_kali_linux()
    if not valido:
        mostrar_erro_sistema(motivo)
        sys.exit(1)

    root = tk.Tk()
    app = BettercapGUI(root)
    root.mainloop()
