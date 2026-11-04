import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import socket
import dns.resolver
import dns.zone
import dns.query
import dns.exception
import dns.rdatatype
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import platform

# Evita warnings de SSL (normal em recon de subdomínios com certs inválidos/self-signed)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Códigos HTTP considerados "ativos"
STATUS_OK = {200}
# Opcional: descomente para aceitar também redirects e outros sucesso
# STATUS_OK = {200, 201, 301, 302, 307, 308}

TIMEOUT_HTTP = 6          # timeout das requisições HTTP (segundos)
MAX_WORKERS = 5           # threads paralelas para verificação HTTP
USER_AGENT = "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53"

class DNSZoneTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Zone Transfer (AXFR)")

        sistema = platform.system()

        if sistema == "Windows":
            self.root.state("zoomed") # Windows
        else:
            self.root.attributes("-zoomed", True) # Kali Linux

        self.root.configure(bg="#2b2b2b")

        self.found_urls = set()   # todas as URL candidatas
        self.results = {}         # url -> status code (ou None)

        # Estilo das abas
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background="#2b2b2b", borderwidth=0)
        style.configure('TNotebook.Tab', background="#3c3f41",
                        foreground="white", padding=[10, 5],
                        font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#007acc')])

        # ---------- BARRA DE PROGRESSO VERDE (0 a 100%) ----------
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor="#1e1e1e",   # fundo da barra
            background="#00ff00",    # cor de preenchimento (VERDE)
            bordercolor="#00ff00",
            lightcolor="#00ff00",
            darkcolor="#00cc44",
            thickness=20
        )

        title_label = tk.Label(
            root,
            text="🌐 DNS Zone Transfer & Subdomain Extractor",
            font=("Arial", 16, "bold"),
            bg="#2b2b2b", fg="#00ff00"
        )
        title_label.pack(pady=10)

        # Frame de entrada e botões
        input_frame = tk.Frame(root, bg="#2b2b2b")
        input_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(input_frame, text="Domínio:", font=("Arial", 11),
                 bg="#2b2b2b", fg="white").pack(side="left", padx=5)

        self.domain_entry = tk.Entry(
            input_frame, font=("Arial", 11), width=30,
            bg="#3c3f41", fg="white", insertbackground="white"
        )
        self.domain_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.domain_entry.insert(0, "zonetransfer.me")

        self.scan_button = tk.Button(
            input_frame, text="🔍 Iniciar Scan", command=self.start_scan,
            bg="#007acc", fg="white", font=("Arial", 10, "bold"),
            cursor="hand2", relief="flat", padx=10
        )
        self.scan_button.pack(side="left", padx=5)

        self.clear_button = tk.Button(
            input_frame, text="🗑️ Limpar", command=self.clear_output,
            bg="#cc3300", fg="white", font=("Arial", 10, "bold"),
            cursor="hand2", relief="flat", padx=10
        )
        self.clear_button.pack(side="left", padx=5)

        self.save_button = tk.Button(
            input_frame, text="💾 Salvar HTML", command=self.save_html,
            bg="#28a745", fg="white", font=("Arial", 10, "bold"),
            cursor="hand2", relief="flat", padx=10
        )
        self.save_button.pack(side="left", padx=5)

        # Barra de progresso determinada (0-100), verde
        self.progress = ttk.Progressbar(
            root, style="green.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate",
            length=960, maximum=100
        )
        self.progress.pack(pady=5, padx=20, fill="x")

        # Percentual ao lado da barra
        self.progress_label = tk.Label(
            root, text="0%", font=("Arial", 10, "bold"),
            bg="#2b2b2b", fg="#00ff00"
        )
        self.progress_label.pack()

        # Abas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=20, fill="both", expand=True)

        # Aba 1: Log AXFR bruto
        self.tab_log = tk.Frame(self.notebook, bg="#2b2b2b")
        self.notebook.add(self.tab_log, text="📋 Log AXFR Bruto")

        self.output_text = scrolledtext.ScrolledText(
            self.tab_log, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#00ff00", insertbackground="white"
        )
        self.output_text.pack(fill="both", expand=True, pady=5, padx=5)

        # Aba 2: URL ativas (HTTP 200)
        self.tab_urls = tk.Frame(self.notebook, bg="#2b2b2b")
        self.notebook.add(self.tab_urls, text="🔗 URL Ativas (200)")

        self.url_text = scrolledtext.ScrolledText(
            self.tab_urls, wrap=tk.WORD, font=("Consolas", 11),
            bg="#1e1e1e", fg="#00ff00", insertbackground="white"
        )
        self.url_text.pack(fill="both", expand=True, pady=5, padx=5)

        # Aba 3: todos os resultados (com cores por status)
        self.tab_all = tk.Frame(self.notebook, bg="#2b2b2b")
        self.notebook.add(self.tab_all, text="📊 Todos os Resultados")

        self.all_text = scrolledtext.ScrolledText(
            self.tab_all, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#d0d0d0", insertbackground="white"
        )
        self.all_text.pack(fill="both", expand=True, pady=5, padx=5)

        # ---------- TAGS DE COR (Aba: Todos os Resultados) ----------
        # Verde = 200 (ativo)
        self.all_text.tag_configure("ok", foreground="#00ff00")
        # Vermelho = inacessível / erro
        self.all_text.tag_configure("fail", foreground="#ff4444")
        # Laranja = outros códigos (301, 403, 404, etc.)
        self.all_text.tag_configure("other", foreground="#ffaa00")

        # ---------- TAGS DE COR (Aba: URL Ativas) ----------
        self.url_text.tag_configure("ok", foreground="#00ff00")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        status_bar = tk.Label(
            root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
            anchor=tk.W, bg="#1e1e1e", fg="#00ff00"
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------------ #
    # Utilitários de UI (thread-safe)
    # ------------------------------------------------------------------ #
    def log(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def log_url(self, url):
        """Adiciona URL ativa (200) em verde na aba de URL"""
        self.url_text.insert(tk.END, url + "\n", "ok")
        self.url_text.see(tk.END)
        self.root.update_idletasks()

    def log_result(self, line, tag):
        """Adiciona linha na aba de resultados com a cor correspondente"""
        self.all_text.insert(tk.END, line + "\n", tag)
        self.all_text.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    # ------------------------------------------------------------------ #
    # Controle da barra de progresso (0 a 100%)
    # ------------------------------------------------------------------ #
    def set_progress(self, value):
        """Define o progresso absoluto (0-100)"""
        value = max(0, min(100, value))
        self.progress["value"] = value
        self.progress_label.config(text=f"{int(value)}%")
        self.root.update_idletasks()

    def reset_progress(self):
        self.set_progress(0)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.url_text.delete(1.0, tk.END)
        self.all_text.delete(1.0, tk.END)
        self.found_urls.clear()
        self.results.clear()
        self.status_var.set("Pronto")
        self.reset_progress()

    # ------------------------------------------------------------------ #
    # DNS
    # ------------------------------------------------------------------ #
    def get_nameservers(self, domain):
        nameservers = []
        try:
            answers = dns.resolver.resolve(domain, 'NS')
            for rdata in answers:
                nameservers.append(str(rdata.target).rstrip('.'))
        except Exception as e:
            self.log(f"❌ Erro ao obter nameservers: {e}")
        return nameservers

    def try_zone_transfer(self, domain, nameserver, hosts):
        """Tenta AXFR; adiciona hosts (A/CNAME) encontrados à lista 'hosts'"""
        try:
            self.log(f"\n🔎 Tentando AXFR em: {nameserver:<30} Para {domain}\n")

            ns_ip = socket.gethostbyname(nameserver)
            self.log(f"   IP do servidor: {ns_ip}")

            zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, domain, timeout=10))

            self.log(f"\n✅ TRANSFERÊNCIA DE ZONA BEM-SUCEDIDA em: {nameserver}\n")
            self.log("=" * 60)

            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    self.log(f"   {name} {rdataset}")

                    if rdataset.rdtype in [dns.rdatatype.A, dns.rdatatype.CNAME]:
                        nome_sub = str(name)
                        if nome_sub == "@":
                            full_domain = domain
                        else:
                            nome_sub = nome_sub.rstrip('.')
                            full_domain = f"{nome_sub}.{domain}"

                        if full_domain not in hosts:
                            hosts.append(full_domain)

            self.log(f"\n   📦 Hosts extraídos desta zona: {len(hosts)}")
            self.log("=" * 60)
            return True

        except socket.gaierror:
            self.log(f"   ❌ Não foi possível resolver o IP de {nameserver}")
        except socket.timeout:
            self.log(f"   ⏱️ Tempo limite esgotado ao conectar em {nameserver}")
        except dns.exception.DNSException:
            self.log("   ⛔ Transferência negada (servidor protegido ou recusou)")
        except Exception as e:
            self.log(f"   ❌ Erro: {str(e)}")

        return False

    # ------------------------------------------------------------------ #
    # Verificação HTTP
    # ------------------------------------------------------------------ #
    def check_url(self, url):
        """Retorna (url, status_code ou None)."""
        headers = {"User-Agent": USER_AGENT}
        try:
            r = requests.get(url, timeout=TIMEOUT_HTTP, verify=False,
                             allow_redirects=True, headers=headers, stream=True)
            code = r.status_code
            r.close()
            return url, code
        except requests.exceptions.SSLError:
            if url.startswith("https://"):
                try:
                    r = requests.get(url.replace("https://", "http://", 1),
                                     timeout=TIMEOUT_HTTP, allow_redirects=True,
                                     headers=headers, stream=True)
                    code = r.status_code
                    r.close()
                    return url, code
                except requests.RequestException:
                    return url, None
            return url, None
        except requests.RequestException:
            return url, None

    def verify_all(self, candidates):
        """Verifica todas as URL candidatas em paralelo (5 threads), com cores e progresso."""
        urls = []
        for host in candidates:
            for scheme in ("https", "http"):
                u = f"{scheme}://{host}"
                if u not in self.found_urls:
                    self.found_urls.add(u)
                    urls.append(u)

        self.log(f"\n🌐 Verificando {len(urls)} URL em {MAX_WORKERS} threads\n")
        done = 0
        total = len(urls)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(self.check_url, u): u for u in urls}
            for fut in as_completed(futures):
                url, code = fut.result()
                self.results[url] = code
                done += 1
                self.set_status(f"Verificando HTTP... {done}/{total}")

                # Progresso: fase HTTP ocupa de 20% até 100%
                self.set_progress(20 + (done / total) * 80)

                if code is None:
                    # Inacessível -> VERMELHO
                    line = f"  [----] {url} (inacessível)"
                    self.log_result(line, "fail")
                elif code in STATUS_OK:
                    # 200 -> VERDE
                    line = f"  [{code}] {url}"
                    self.log_result(line, "ok")
                    self.log_url(line)
                else:
                    # Outros códigos (301, 403...) -> LARANJA
                    line = f"  [{code}] {url}"
                    self.log_result(line, "other")

    # ------------------------------------------------------------------ #
    # Fluxo principal
    # ------------------------------------------------------------------ #
    def scan_domain(self, domain):
        try:
            self.reset_progress()
            self.log(f"🎯 Iniciando scan para: {domain}")
            self.log("=" * 60)

            self.set_status(f"Buscando nameservers de {domain}...")
            nameservers = self.get_nameservers(domain)

            if not nameservers:
                self.log("❌ Nenhum nameserver encontrado!")
                messagebox.showerror("Erro", "Nenhum nameserver encontrado para este domínio")
                self.reset_progress()
                return

            self.log(f"\n📡 Nameservers Encontrados: {len(nameservers)}\n")
            for ns in nameservers:
                self.log(f"   • {ns}")

            # Progresso: fase AXFR ocupa de 0% até 20%
            success_count = 0
            hosts = []
            for i, ns in enumerate(nameservers, start=1):
                self.set_status(f"Testando AXFR em {ns}...")
                if self.try_zone_transfer(domain, ns, hosts):
                    success_count += 1
                # 20% divididos entre os nameservers
                self.set_progress((i / len(nameservers)) * 20)

            self.log("\n" + "=" * 60)
            self.log(f"✔️ AXFR concluído! {success_count}/{len(nameservers)} servidores vulneráveis\n")
            self.log(f"   Total de hosts coletados: {len(hosts)}")

            if hosts:
                # Progresso: fase HTTP ocupa de 20% até 100%
                self.verify_all(hosts)
            else:
                self.set_progress(100)

            ok = sum(1 for c in self.results.values() if c in STATUS_OK)
            self.log("\n" + "=" * 60)
            self.log(f"🏁 Scan completo! URL ativas (200): {ok}")
            self.set_status(f"Concluído - {success_count}/{len(nameservers)} NS vulneráveis | {ok} URL ativas (200)")
            self.set_progress(100)

        except Exception as e:
            self.log(f"❌ Erro geral: {e}")
            messagebox.showerror("Erro", str(e))
            self.reset_progress()
        finally:
            self.scan_button.config(state="normal")

    def start_scan(self):
        domain = self.domain_entry.get().strip()
        if not domain:
            messagebox.showwarning("Aviso", "Por favor, insira um domínio!")
            return

        self.clear_output()
        self.scan_button.config(state="disabled")
        self.set_progress(1)  # começa já visível

        thread = threading.Thread(target=self.scan_domain, args=(domain,), daemon=True)
        thread.start()

    # ------------------------------------------------------------------ #
    # Relatório HTML
    # ------------------------------------------------------------------ #
    def save_html(self):
        domain = self.domain_entry.get().strip() or "Scan_Result"

        raw_log = self.output_text.get(1.0, tk.END).strip()
        results_log = self.all_text.get(1.0, tk.END).strip()
        url_log = self.url_text.get(1.0, tk.END).strip()

        if not raw_log:
            messagebox.showwarning("Aviso", "Não há resultados para salvar!")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile=f"AXFR_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            title="Salvar Relatório HTML",
            filetypes=[("HTML files", "*.html")]
        )
        if not filepath:
            return

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório AXFR - {domain}</title>
            <style>
                :root {{ --bg-color: #121212; --card-bg: #1e1e1e; --text-main: #e0e0e0;
                         --accent: #00ff00; --url-color: #4da6ff; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: var(--bg-color); color: var(--text-main);
                        margin: 0; padding: 20px; line-height: 1.6; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                header {{ border-bottom: 2px solid var(--accent); padding-bottom: 10px; margin-bottom: 30px; }}
                h1 {{ color: var(--accent); margin: 0; }}
                .meta {{ font-size: 0.9em; color: #888; margin-top: 5px; }}
                .card {{ background-color: var(--card-bg); border-radius: 8px; padding: 20px;
                         margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                h2 {{ color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 0; }}
                pre {{ font-family: 'Consolas', 'Courier New', monospace; background-color: #000;
                       padding: 15px; border-radius: 5px; overflow-x: auto;
                       white-space: pre-wrap; word-wrap: break-word; font-size: 14px;
                       border: 1px solid #333; }}
                .url-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; }}
                .url-item {{ padding: 10px; border-radius: 5px; word-break: break-all; }}
                .r-ok   {{ background-color: #0d2b0d; border-left: 4px solid #00cc44; color: #00ff88; }}
                .r-fail {{ background-color: #2b0d0d; border-left: 4px solid #ff3333; color: #ff6666; }}
                .r-other{{ background-color: #2b220d; border-left: 4px solid #ffaa00; color: #ffcc55; }}
                a {{ color: inherit; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .badge {{ font-weight: bold; padding: 2px 8px; border-radius: 3px;
                          font-size: 0.85em; margin-right: 8px; }}
                .b200 {{ background: #00cc44; color: #000; }}
                .bfail {{ background: #ff3333; color: #fff; }}
                .bother {{ background: #ffaa00; color: #000; }}
                /* Cores no log */
                pre .ok {{ color: #00ff00; }}
                pre .fail {{ color: #ff4444; }}
                pre .other {{ color: #ffaa00; }}
                /* Barra de progresso no relatório */
                .pbar {{ background: #1e1e1e; border: 1px solid #333; border-radius: 10px;
                         height: 24px; overflow: hidden; margin-top: 8px; }}
                .pfill {{ background: linear-gradient(90deg, #00cc44, #00ff00);
                          height: 100%; width: 100%; text-align: center;
                          color: #000; font-weight: bold; font-size: 0.85em; line-height: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🌐 Relatório de Transferência de Zona DNS (AXFR)</h1>
                    <div class="meta">Alvo: <strong>{domain}</strong> |
                        Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
                    <div class="pbar"><div class="pfill">100% Concluído</div></div>
                </header>

                <div class="card">
                    <h2>🔗 URL Ativas (HTTP 200)</h2>
                    <div class="url-list">
        """

        urls = [u for u in url_log.split("\n") if u.strip()]
        if urls:
            for line in urls:
                parts = line.split("] ", 1)
                code = parts[0].strip("[ ") if line.startswith("[") else "200"
                url = parts[1] if len(parts) > 1 else line
                html_content += (f'<div class="url-item r-ok">'
                                 f'<span class="badge b200">{code}</span>'
                                 f'<a href="{url}" target="_blank">{url}</a></div>\n')
        else:
            html_content += "<p>Nenhuma URL ativa encontrada.</p>"

        html_content += """
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Todos os Resultados (com status HTTP)</h2>
                    <pre>"""

        # Resultados coloridos por linha no HTML
        for line in results_log.split("\n"):
            esc = line.replace("<", "&lt;").replace(">", "&gt;")
            if "(inacessível)" in line:
                html_content += f'<span class="fail">{esc}</span>\n'
            elif "] http" in line or "] https" in line:
                code = line.strip().split("]")[0].strip("[ ")
                if code == "200":
                    html_content += f'<span class="ok">{esc}</span>\n'
                else:
                    html_content += f'<span class="other">{esc}</span>\n'
            else:
                html_content += esc + "\n"

        html_content += """
                    </pre>
                </div>

                <div class="card">
                    <h2>📋 Log Completo do Servidor (Raw Data)</h2>
                    <pre>""" + raw_log.replace("<", "&lt;").replace(">", "&gt;") + """</pre>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Ocorreu um erro ao salvar o arquivo:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DNSZoneTransferApp(root)
    root.mainloop()
