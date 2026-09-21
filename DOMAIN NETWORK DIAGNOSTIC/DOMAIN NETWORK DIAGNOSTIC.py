import socket
import ssl
import threading
import time
import urllib.request
import urllib.error
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from html import escape


# ============================================================
# DOMAIN NETWORK DIAGNOSTIC
# Diagnóstico de domínio - sem abrir CMD ou PowerShell
# ============================================================

class DomainDiagnostic:

    def __init__(self, root):
        self.root = root

        self.root.title("DOMAIN NETWORK DIAGNOSTIC")
        self.root.geometry("1050x780")
        self.root.minsize(900, 650)
        self.root.configure(bg="#0a0a0a")

        self.running = False

        # Armazena linhas com tags para HTML
        self.log_entries = []

        # Contador de erros encontrados
        self.error_count = 0
        self.error_details = []

        self.setup_style()
        self.create_interface()

    # ========================================================
    # ESTILO
    # ========================================================

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            background="#00ff41",
            foreground="#000000",
            font=("Consolas", 11, "bold"),
            padding=8
        )

        style.map(
            "TButton",
            background=[
                ("active", "#00cc33"),
                ("pressed", "#00aa2a")
            ]
        )

        style.configure(
            "TLabel",
            background="#0a0a0a",
            foreground="#00ff41",
            font=("Consolas", 11)
        )

        style.configure(
            "TEntry",
            fieldbackground="#111111",
            foreground="#00ff41",
            insertcolor="#00ff41",
            font=("Consolas", 12)
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def create_interface(self):

        # CABEÇALHO
        header = tk.Frame(self.root, bg="#0a0a0a")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title = tk.Label(
            header,
            text="█ DOMAIN NETWORK DIAGNOSTIC █",
            bg="#0a0a0a",
            fg="#00ff41",
            font=("Consolas", 20, "bold")
        )
        title.pack()

        subtitle = tk.Label(
            header,
            text="Diagnóstico IPv4 • IPv6 • DNS • HTTPS • TCP",
            bg="#0a0a0a",
            fg="#00cc33",
            font=("Consolas", 10)
        )
        subtitle.pack(pady=(5, 0))

        # ÁREA DE DOMÍNIO
        domain_frame = tk.Frame(self.root, bg="#0a0a0a")
        domain_frame.pack(fill="x", padx=25, pady=20)

        label = tk.Label(
            domain_frame,
            text="DOMÍNIO:",
            bg="#0a0a0a",
            fg="#00ff41",
            font=("Consolas", 12, "bold")
        )
        label.pack(side="left")

        self.domain_var = tk.StringVar()

        self.domain_entry = tk.Entry(
            domain_frame,
            textvariable=self.domain_var,
            bg="#111111",
            fg="#00ff41",
            insertbackground="#00ff41",
            selectbackground="#00ff41",
            selectforeground="#000000",
            font=("Consolas", 12),
            relief="solid",
            bd=1
        )
        self.domain_entry.pack(
            side="left", fill="x",
            expand=True, padx=10
        )
        self.domain_entry.insert(0, "")

        self.test_button = tk.Button(
            domain_frame,
            text="▶ TESTAR",
            command=self.start_test,
            bg="#00ff41",
            fg="#000000",
            activebackground="#00cc33",
            activeforeground="#000000",
            font=("Consolas", 11, "bold"),
            relief="flat",
            padx=18, pady=8,
            cursor="hand2"
        )
        self.test_button.pack(side="right")

        # BOTÕES
        buttons_frame = tk.Frame(self.root, bg="#0a0a0a")
        buttons_frame.pack(fill="x", padx=25, pady=(0, 10))

        self.clear_button = tk.Button(
            buttons_frame,
            text="LIMPAR",
            command=self.clear_output,
            bg="#222222",
            fg="#00ff41",
            activebackground="#333333",
            activeforeground="#00ff41",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15, pady=6,
            cursor="hand2"
        )
        self.clear_button.pack(side="left")

        self.save_txt_button = tk.Button(
            buttons_frame,
            text="SALVAR TXT",
            command=self.save_report_txt,
            bg="#222222",
            fg="#00ff41",
            activebackground="#333333",
            activeforeground="#00ff41",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15, pady=6,
            cursor="hand2"
        )
        self.save_txt_button.pack(side="left", padx=10)

        self.save_html_button = tk.Button(
            buttons_frame,
            text="SALVAR HTML",
            command=self.save_report_html,
            bg="#005588",
            fg="#ffffff",
            activebackground="#006699",
            activeforeground="#ffffff",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15, pady=6,
            cursor="hand2"
        )
        self.save_html_button.pack(side="left", padx=5)

        # BOTÃO TESTE IPv6 ONLINE
        self.ipv6_test_button = tk.Button(
            buttons_frame,
            text="🌐 TESTE IPv6 ONLINE",
            command=self.open_ipv6_test,
            bg="#ff8800",
            fg="#000000",
            activebackground="#ff9922",
            activeforeground="#000000",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15, pady=6,
            cursor="hand2"
        )
        self.ipv6_test_button.pack(side="right")

        # STATUS
        self.status_var = tk.StringVar(
            value="● PRONTO PARA TESTAR"
        )

        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#0a0a0a",
            fg="#00ff41",
            font=("Consolas", 11, "bold")
        )
        self.status_label.pack(
            anchor="w", padx=25, pady=(0, 5)
        )

        # ÁREA DE RESULTADOS
        output_frame = tk.Frame(self.root, bg="#0a0a0a")
        output_frame.pack(
            fill="both", expand=True,
            padx=25, pady=(0, 20)
        )

        scrollbar = tk.Scrollbar(
            output_frame,
            bg="#111111",
            troughcolor="#0a0a0a",
            activebackground="#00ff41"
        )
        scrollbar.pack(side="right", fill="y")

        self.output = tk.Text(
            output_frame,
            bg="#050505",
            fg="#00ff41",
            insertbackground="#00ff41",
            selectbackground="#00ff41",
            selectforeground="#000000",
            font=("Consolas", 10),
            wrap="word",
            relief="solid",
            bd=1,
            padx=12, pady=12,
            yscrollcommand=scrollbar.set
        )
        self.output.pack(fill="both", expand=True)
        scrollbar.config(command=self.output.yview)

        # TAGS DE CORES
        self.output.tag_configure(
            "title",
            foreground="#00ff41",
            font=("Consolas", 13, "bold")
        )

        self.output.tag_configure(
            "ok",
            foreground="#00ff41",
            font=("Consolas", 10, "bold")
        )

        self.output.tag_configure(
            "error",
            foreground="#ff3333",
            font=("Consolas", 10, "bold")
        )

        self.output.tag_configure(
            "warning",
            foreground="#ffff00",
            font=("Consolas", 10, "bold")
        )

        self.output.tag_configure(
            "info",
            foreground="#00ccff",
            font=("Consolas", 10)
        )

        self.output.tag_configure(
            "normal",
            foreground="#cccccc",
            font=("Consolas", 10)
        )

        # Tag especial para TUDO OK
        self.output.tag_configure(
            "success_big",
            foreground="#00ff41",
            font=("Consolas", 14, "bold")
        )

        # Tag especial para ERROS ENCONTRADOS
        self.output.tag_configure(
            "error_big",
            foreground="#ff3333",
            font=("Consolas", 14, "bold")
        )

        # ENTER para testar
        self.domain_entry.bind(
            "<Return>",
            lambda event: self.start_test()
        )

    # ========================================================
    # ABRIR SITE TESTE IPv6
    # ========================================================

    def open_ipv6_test(self):
        url = "https://test-ipv6.com/index.html.pt_BR"
        try:
            webbrowser.open(url)
            self.log(
                f"\n[INFO] Abrindo navegador: {url}",
                "info"
            )
            self.log(
                "[INFO] Verifique a compatibilidade "
                "IPv6 da sua conexão no site.",
                "info"
            )
            self.log("", "normal")
        except Exception as error:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir o navegador:\n\n"
                f"{error}\n\n"
                f"Acesse manualmente:\n{url}"
            )

    # ========================================================
    # LOG
    # ========================================================

    def log(self, text="", tag="normal"):
        self.output.insert(tk.END, text + "\n", tag)
        self.output.see(tk.END)

        # Guardar para HTML
        self.log_entries.append((text, tag))

    # ========================================================
    # REGISTRAR ERRO
    # ========================================================

    def register_error(self, description):
        self.error_count += 1
        self.error_details.append(description)

    # ========================================================
    # LIMPAR
    # ========================================================

    def clear_output(self):
        self.output.delete("1.0", tk.END)
        self.log_entries.clear()
        self.error_count = 0
        self.error_details.clear()
        self.status_var.set("● PRONTO PARA TESTAR")

    # ========================================================
    # NORMALIZAR DOMÍNIO
    # ========================================================

    def normalize_domain(self, domain):
        domain = domain.strip()
        if not domain:
            return ""

        if "://" in domain:
            domain = domain.split("://", 1)[1]

        domain = domain.split("/", 1)[0]
        domain = domain.split("?", 1)[0]
        domain = domain.split("#", 1)[0]

        if ":" in domain:
            domain = domain.split(":", 1)[0]

        return domain.lower().strip()

    # ========================================================
    # INICIAR TESTE
    # ========================================================

    def start_test(self):
        if self.running:
            return

        domain = self.normalize_domain(
            self.domain_var.get()
        )

        if not domain:
            messagebox.showwarning(
                "Domínio",
                "Digite um Domínio para testar."
            )
            return

        self.domain_var.set(domain)
        self.running = True

        self.test_button.config(
            state="disabled",
            text="TESTANDO..."
        )

        self.clear_output()

        self.status_var.set(
            "● EXECUTANDO DIAGNÓSTICO..."
        )

        thread = threading.Thread(
            target=self.run_diagnostic,
            args=(domain,),
            daemon=True
        )
        thread.start()

    # ========================================================
    # DIAGNÓSTICO PRINCIPAL
    # ========================================================

    def run_diagnostic(self, domain):

        start_total = time.perf_counter()

        # Resetar contadores
        self.error_count = 0
        self.error_details.clear()

        self.safe_log(
            "\n╔════════════════════════════════════════════════════════╗",
            "title"
        )
        self.safe_log(
            "║             DOMAIN NETWORK DIAGNOSTIC                  ║",
            "title"
        )
        self.safe_log(
            "╚════════════════════════════════════════════════════════╝",
            "title"
        )

        self.safe_log(
            f"\n[INFO] Domínio: {domain}", "info"
        )
        self.safe_log(
            f"[INFO] Horário: "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "info"
        )
        self.safe_log("\n" + "=" * 60, "normal")

        # ────────────────────────────────────
        # 1 ─ DNS
        # ────────────────────────────────────
        self.safe_log("\n[1] RESOLUÇÃO DNS", "title")

        ipv4 = []
        ipv6 = []

        try:
            infos = socket.getaddrinfo(
                domain, 443,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM
            )

            for info in infos:
                family = info[0]
                address = info[4][0]

                if family == socket.AF_INET:
                    if address not in ipv4:
                        ipv4.append(address)

                elif family == socket.AF_INET6:
                    if address not in ipv6:
                        ipv6.append(address)

            if ipv4:
                self.safe_log("[OK] IPv4 Encontrado", "ok")
                for address in ipv4:
                    self.safe_log(
                        f"     └─ {address}", "normal"
                    )
            else:
                self.safe_log(
                    "[AVISO] Nenhum endereço IPv4 Encontrado",
                    "warning"
                )
                self.register_error(
                    "Nenhum endereço IPv4 Encontrado"
                )

            if ipv6:
                self.safe_log("[OK] IPv6 Encontrado:", "ok")
                for address in ipv6:
                    self.safe_log(
                        f"     └─ {address}", "normal"
                    )
            else:
                self.safe_log(
                    "[INFO] Nenhum IPv6 Encontrado.", "info"
                )

        except socket.gaierror as error:
            self.safe_log(
                f"[ERRO] Falha na resolução DNS: {error}",
                "error"
            )
            self.register_error(
                f"Falha na resolução DNS: {error}"
            )
            self.show_final_summary(domain, start_total)
            return

        # ────────────────────────────────────
        # 2 ─ TCP IPv4
        # ────────────────────────────────────
        self.safe_log(
            "\n[2] CONECTIVIDADE TCP / IPv4", "title"
        )

        if ipv4:
            for address in ipv4[:3]:
                result = self.test_tcp(
                    address, 443, socket.AF_INET
                )
                if result:
                    self.safe_log(
                        f"[OK] {address}:443 → TCP conectado",
                        "ok"
                    )
                else:
                    self.safe_log(
                        f"[ERRO] {address}:443 → TCP não conectou",
                        "error"
                    )
                    self.register_error(
                        f"TCP IPv4 falhou: {address}:443"
                    )
        else:
            self.safe_log(
                "[INFO] IPv4 não disponível.", "info"
            )

        # ────────────────────────────────────
        # 3 ─ TCP IPv6
        # ────────────────────────────────────
        self.safe_log(
            "\n[3] CONECTIVIDADE TCP / IPv6", "title"
        )

        if ipv6:
            for address in ipv6[:3]:
                result = self.test_tcp(
                    address, 443, socket.AF_INET6
                )
                if result:
                    self.safe_log(
                        f"[OK] [{address}]:443 → TCP conectado",
                        "ok"
                    )
                else:
                    self.safe_log(
                        f"[ERRO] [{address}]:443 → TCP não conectou",
                        "error"
                    )
                    self.register_error(
                        f"TCP IPv6 falhou: [{address}]:443"
                    )
        else:
            self.safe_log(
                "[INFO] IPv6 não disponível para este Domínio.",
                "info"
            )

        # ────────────────────────────────────
        # 4 ─ HTTPS
        # ────────────────────────────────────
        self.safe_log("\n[4] TESTE HTTPS", "title")

        https_result = self.test_https(domain)

        if https_result["success"]:
            self.safe_log(
                f"[OK] HTTPS respondeu: "
                f"HTTP {https_result['status']}",
                "ok"
            )
            self.safe_log(
                f"[OK] Tempo: "
                f"{https_result['time']:.3f} segundos",
                "ok"
            )
            if https_result["server"]:
                self.safe_log(
                    f"[INFO] Server: {https_result['server']}",
                    "info"
                )
        else:
            self.safe_log(
                f"[ERRO] HTTPS: {https_result['error']}",
                "error"
            )
            self.register_error(
                f"HTTPS falhou: {https_result['error']}"
            )

        # ────────────────────────────────────
        # 5 ─ TLS
        # ────────────────────────────────────
        self.safe_log(
            "\n[5] CERTIFICADO TLS / SSL", "title"
        )

        tls_result = self.test_tls(domain)

        if tls_result["success"]:
            self.safe_log(
                "[OK] Certificado TLS válido.", "ok"
            )
            if tls_result["issuer"]:
                self.safe_log(
                    f"[INFO] Emissor: {tls_result['issuer']}",
                    "info"
                )
            if tls_result["expires"]:
                self.safe_log(
                    f"[INFO] Expiração: {tls_result['expires']}",
                    "info"
                )
        else:
            self.safe_log(
                f"[ERRO] TLS: {tls_result['error']}",
                "error"
            )
            self.register_error(
                f"Certificado TLS falhou: {tls_result['error']}"
            )

        # ────────────────────────────────────
        # RESULTADO FINAL
        # ────────────────────────────────────
        self.show_final_summary(domain, start_total)

    # ========================================================
    # RESUMO FINAL COM STATUS
    # ========================================================

    def show_final_summary(self, domain, start_total):

        elapsed = time.perf_counter() - start_total

        self.safe_log("\n" + "=" * 60, "normal")
        self.safe_log("", "normal")

        # ── TUDO OK ──
        if self.error_count == 0:
            self.safe_log(
                "● TUDO OK — NENHUM ERRO LOCALIZADO",
                "success_big"
            )
            self.safe_log("", "normal")
            self.safe_log(
                "[OK] DNS .............. funcionando",
                "ok"
            )
            self.safe_log(
                "[OK] TCP .............. conectado",
                "ok"
            )
            self.safe_log(
                "[OK] HTTPS ............ respondendo",
                "ok"
            )
            self.safe_log(
                "[OK] TLS/SSL .......... válido",
                "ok"
            )
            self.safe_log("", "normal")
            self.safe_log(
                f"[OK] O Domínio: {domain:<20} Está 100% operacional.",
                "ok"
            )

        # ── ERROS ENCONTRADOS ──
        else:
            if self.error_count == 1:
                self.safe_log(
                    "● 1 ERRO LOCALIZADO NO DIAGNÓSTICO",
                    "error_big"
                )
            else:
                self.safe_log(
                    f"● {self.error_count} ERROS LOCALIZADOS NO DIAGNÓSTICO",
                    "error_big"
                )

            self.safe_log("", "normal")
            self.safe_log(
                "[ERROS ENCONTRADOS]",
                "error"
            )
            self.safe_log("", "normal")

            for i, detail in enumerate(
                self.error_details, 1
            ):
                self.safe_log(
                    f"  {i}. {detail}",
                    "error"
                )

            self.safe_log("", "normal")
            self.safe_log(
                f"[AVISO] O Domínio: {domain:<20} Apresentou "
                f"{self.error_count} Problemas",
                "warning"
            )

        # ── TEMPO ──
        self.safe_log("", "normal")
        self.safe_log(
            f"[INFO] Tempo total do diagnóstico: "
            f"{elapsed:.2f} segundos",
            "info"
        )

        self.safe_log("\n" + "=" * 60, "normal")
        self.safe_log(
            "\n[FINALIZADO] Diagnóstico concluído.", "ok"
        )

        self.root.after(0, self.test_finished)

    # ========================================================
    # TCP
    # ========================================================

    def test_tcp(self, address, port, family):
        sock = None
        try:
            sock = socket.socket(
                family, socket.SOCK_STREAM
            )
            sock.settimeout(5)

            if family == socket.AF_INET6:
                result = sock.connect_ex(
                    (address, port, 0, 0)
                )
            else:
                result = sock.connect_ex(
                    (address, port)
                )

            return result == 0

        except Exception:
            return False

        finally:
            if sock:
                sock.close()

    # ========================================================
    # HTTPS
    # ========================================================

    def test_https(self, domain):
        start = time.perf_counter()

        try:
            url = f"https://{domain}/"

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/153.0 Safari/537.36"
                }
            )

            with urllib.request.urlopen(
                request, timeout=10
            ) as response:

                elapsed = time.perf_counter() - start

                server = response.headers.get(
                    "Server", ""
                )

                return {
                    "success": True,
                    "status": response.status,
                    "time": elapsed,
                    "server": server,
                    "error": ""
                }

        except urllib.error.HTTPError as error:
            elapsed = time.perf_counter() - start

            return {
                "success": True,
                "status": error.code,
                "time": elapsed,
                "server": error.headers.get(
                    "Server", ""
                ),
                "error": ""
            }

        except Exception as error:
            return {
                "success": False,
                "status": None,
                "time": 0,
                "server": "",
                "error": str(error)
            }

    # ========================================================
    # TLS
    # ========================================================

    def test_tls(self, domain):
        context = ssl.create_default_context()
        sock = None

        try:
            sock = socket.create_connection(
                (domain, 443), timeout=10
            )

            with context.wrap_socket(
                sock, server_hostname=domain
            ) as secure_sock:

                certificate = secure_sock.getpeercert()

                issuer = ""
                issuer_data = certificate.get(
                    "issuer", ()
                )

                for group in issuer_data:
                    for key, value in group:
                        if key == "organizationName":
                            issuer = value

                expires = certificate.get(
                    "notAfter", ""
                )

                return {
                    "success": True,
                    "issuer": issuer,
                    "expires": expires,
                    "error": ""
                }

        except Exception as error:
            return {
                "success": False,
                "issuer": "",
                "expires": "",
                "error": str(error)
            }

        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    # ========================================================
    # LOG THREAD-SAFE
    # ========================================================

    def safe_log(self, text, tag="normal"):
        self.root.after(
            0,
            lambda: self.log(text, tag)
        )

    # ========================================================
    # FINALIZAR
    # ========================================================

    def test_finished(self):
        self.running = False
        self.test_button.config(
            state="normal",
            text="▶ TESTAR"
        )

        if self.error_count == 0:
            self.status_var.set(
                "● DIAGNÓSTICO CONCLUÍDO — TUDO OK ✅"
            )
            self.status_label.config(fg="#00ff41")
        else:
            self.status_var.set(
                f"● DIAGNÓSTICO CONCLUÍDO — "
                f"{self.error_count} ERRO(S) ❌"
            )
            self.status_label.config(fg="#ff3333")

    # ========================================================
    # SALVAR TXT
    # ========================================================

    def save_report_txt(self):
        content = self.output.get("1.0", tk.END).strip()

        if not content:
            messagebox.showwarning(
                "Relatório",
                "Não existe nenhum resultado para salvar."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Salvar relatório TXT",
            defaultextension=".txt",
            filetypes=[
                ("Arquivo de texto", "*.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not filename:
            return

        try:
            with open(
                filename, "w", encoding="utf-8"
            ) as file:
                file.write(content)

            messagebox.showinfo(
                "Sucesso",
                "Relatório TXT salvo com sucesso."
            )

        except Exception as error:
            messagebox.showerror(
                "Erro",
                f"Não foi possível salvar:\n\n{error}"
            )

    # ========================================================
    # SALVAR HTML (COM CORES E ERROS EM VERMELHO)
    # ========================================================

    def save_report_html(self):

        if not self.log_entries:
            messagebox.showwarning(
                "Relatório",
                "Não existe nenhum resultado para salvar."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Salvar relatório HTML",
            defaultextension=".html",
            filetypes=[
                ("Arquivo HTML", "*.html"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not filename:
            return

        # Mapeamento de tags para cores HTML
        tag_colors = {
            "title":       "#00ff41",
            "ok":          "#00ff41",
            "error":       "#ff3333",
            "error_big":   "#ff3333",
            "warning":     "#ffff00",
            "info":        "#00ccff",
            "normal":      "#cccccc",
            "success_big": "#00ff41"
        }

        tag_bold = {
            "title", "ok", "error", "warning",
            "error_big", "success_big"
        }

        tag_size = {
            "title":       "15px",
            "success_big": "16px",
            "error_big":   "16px"
        }

        # Construir linhas HTML
        lines_html = []

        for text, tag in self.log_entries:

            color = tag_colors.get(tag, "#cccccc")
            bold = (
                "font-weight:bold;"
                if tag in tag_bold else ""
            )
            size = (
                f"font-size:{tag_size[tag]};"
                if tag in tag_size else ""
            )

            safe_text = escape(text)
            safe_text = safe_text.replace(
                "  ", "&nbsp;&nbsp;"
            )

            # Classe especial para erros
            css_class = ""
            if tag in ("error", "error_big"):
                css_class = ' class="error-highlight"'

            # Classe especial para sucesso total
            if tag == "success_big":
                css_class = ' class="success-highlight"'

            if not safe_text.strip():
                lines_html.append("<br>")
            else:
                lines_html.append(
                    f'<div{css_class} style="color:{color};'
                    f'{bold}{size}">'
                    f'{safe_text}</div>'
                )

        body = "\n".join(lines_html)

        domain = self.domain_var.get() or "dominio"
        timestamp = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        # Status final para o cabeçalho HTML
        if self.error_count == 0:
            status_html = (
                '<span style="color:#00ff41;font-size:16px;'
                'font-weight:bold;">'
                '✅ TUDO OK — NENHUM ERRO LOCALIZADO</span>'
            )
        else:
            status_html = (
                f'<span style="color:#ff3333;font-size:16px;'
                f'font-weight:bold;">'
                f'❌ {self.error_count} ERRO(S) LOCALIZADO(S)'
                f'</span>'
            )

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">
    <title>Diagnóstico - {escape(domain)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: #0a0a0a;
            color: #cccccc;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            padding: 30px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #050505;
            border: 1px solid #00ff41;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.1);
        }}

        .header {{
            text-align: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #00ff41;
        }}

        .header h1 {{
            color: #00ff41;
            font-size: 22px;
            margin-bottom: 5px;
        }}

        .header p {{
            color: #00cc33;
            font-size: 11px;
            margin-top: 5px;
        }}

        .status-banner {{
            text-align: center;
            padding: 12px;
            margin: 15px 0;
            border-radius: 6px;
        }}

        .results {{
            padding: 15px;
            background-color: #0a0a0a;
            border-radius: 4px;
            border: 1px solid #1a1a1a;
        }}

        .results div {{
            padding: 1px 0;
        }}

        .error-highlight {{
            background-color: rgba(255, 51, 51, 0.15);
            border-left: 3px solid #ff3333;
            padding-left: 10px !important;
            margin: 3px 0;
            border-radius: 2px;
        }}

        .success-highlight {{
            background-color: rgba(0, 255, 65, 0.1);
            border-left: 3px solid #00ff41;
            padding-left: 10px !important;
            margin: 3px 0;
            border-radius: 2px;
        }}

        .footer {{
            text-align: center;
            margin-top: 25px;
            padding-top: 15px;
            border-top: 1px solid #222222;
            color: #555555;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>█ DOMAIN NETWORK DIAGNOSTIC █</h1>
            <p>Relatório gerado em {timestamp}</p>
            <p>Domínio: {escape(domain)}</p>
            <div class="status-banner">
                {status_html}
            </div>
        </div>

        <div class="results">
{body}
        </div>

        <div class="footer">
            Domain Network Diagnostic &bull;
            Relatório gerado automaticamente
        </div>
    </div>
</body>
</html>"""

        try:
            with open(
                filename, "w", encoding="utf-8"
            ) as file:
                file.write(html_content)

            messagebox.showinfo(
                "Sucesso",
                f"Relatório HTML salvo com sucesso.\n\n"
                f"{filename}"
            )

        except Exception as error:
            messagebox.showerror(
                "Erro",
                f"Não foi possível salvar:\n\n{error}"
            )


# ============================================================
# INICIAR PROGRAMA
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()
    app = DomainDiagnostic(root)
    root.mainloop()
