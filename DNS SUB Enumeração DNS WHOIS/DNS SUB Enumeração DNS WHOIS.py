import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import socket
import requests
import urllib3
from threading import Thread
from datetime import datetime
import html
import re
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run_subprocess_hidden(cmd, **kwargs):
    """Executa subprocessos sem abrir uma janela/console no Windows."""
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return subprocess.run(cmd, **kwargs)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class DNSSUBGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("DNS SUB Enumeração DNS WHOIS")
        self.geometry("1180x850")
        self.minsize(980, 700)

        try:
            if platform.system() == "Windows":
                self.after(100, lambda: self.state("zoomed"))
            else:
                largura = self.winfo_screenwidth()
                altura = self.winfo_screenheight()
                self.geometry(f"{largura}x{altura}+0+0")
        except Exception:
            pass

        self.scanning = False
        self.wordlist_path = tk.StringVar()
        self.scan_mode = tk.StringVar(value="subdomain")

        self.total_words = 0
        self.remaining_words = 0
        self.found_count = 0
        self.results = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.create_banner()
        self.create_config_frame()
        self.create_controls()
        self.create_stats()
        self.create_results()

    # ========================================
    # INTERFACE
    # ========================================
    def create_banner(self):
        banner_frame = ctk.CTkFrame(self, fg_color="#050a05", corner_radius=10)
        banner_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        ascii_art = r"""
    ██████╗ ███╗   ██╗███████╗    ███████╗██╗   ██╗██████╗ 
    ██╔══██╗████╗  ██║██╔════╝    ██╔════╝██║   ██║██╔══██╗
    ██║  ██║██╔██╗ ██║███████╗    ███████╗██║   ██║██████╔╝
    ██║  ██║██║╚██╗██║╚════██║    ╚════██║██║   ██║██╔══██╗
    ██████╔╝██║ ╚████║███████║    ███████║╚██████╔╝██████╔╝
    ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝ ╚═════╝ 
                                                       
            Enumeração DNS Avançada & HTTP/HTTPS
"""
        banner_label = ctk.CTkLabel(
            banner_frame, text=ascii_art, font=("Consolas", 11, "bold"),
            text_color="#00ff41", justify="center"
        )
        banner_label.pack(padx=10, pady=5)

    def create_config_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame, text="🎯 Domínio Alvo:",
            font=("Consolas", 13, "bold")
        ).grid(row=0, column=0, padx=10, pady=8, sticky="w")

        self.domain_entry = ctk.CTkEntry(
            frame, placeholder_text="exemplo.com.br",
            font=("Consolas", 13), height=35
        )
        self.domain_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(
            frame, text="📄 Wordlist:",
            font=("Consolas", 13, "bold")
        ).grid(row=1, column=0, padx=10, pady=8, sticky="w")

        wl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        wl_frame.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        wl_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            wl_frame, textvariable=self.wordlist_path,
            placeholder_text="Caminho para wordlist (.txt)",
            font=("Consolas", 12), height=35
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            wl_frame, text="📁 Procurar", width=110,
            command=self.browse_file,
            fg_color="#1a6b1a", hover_color="#0d3d0d"
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            frame, text="⚙️ Modo:",
            font=("Consolas", 13, "bold")
        ).grid(row=2, column=0, padx=10, pady=8, sticky="nw")

        mode_frame = ctk.CTkFrame(frame, fg_color="transparent")
        mode_frame.grid(row=2, column=1, padx=10, pady=8, sticky="w")

        # 8 modos agora (2 x 4 Grid)
        modes = [
            ("🔍 Subdomínios (HTTP/HTTPS)", "subdomain"),
            ("🔄 DNS Reverso (/24)", "reverse"),
            ("📋 Consulta DNS (ANY)", "dnsany"),
            ("📡 Zone Transfer (AXFR)", "zonetransfer"),
            ("🌐 Whois Domain", "whois_domain"),
            ("🔎 Whois IP", "whois_ip"),
            ("🌍 Whois Lookup (API)", "whois"),
            ("📋 Headers HTTP", "headers"),
            
        ]

        for index, (label, value) in enumerate(modes):
            row = index // 4
            col = index % 4
            ctk.CTkRadioButton(
                mode_frame, text=label,
                variable=self.scan_mode, value=value,
                font=("Consolas", 12),
                fg_color="#00ff41", hover_color="#00aa2a"
            ).grid(row=row, column=col, padx=12, pady=6, sticky="w")

    def create_controls(self):
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.start_btn = ctk.CTkButton(
            ctrl, text="Iniciar Scan", width=160, height=40,
            fg_color="#00a000", hover_color="#006b00",
            text_color="#000000", font=("Consolas", 14, "bold"),
            command=self.toggle_scan
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(
            ctrl, text="🛑 Parar", width=120, height=40,
            fg_color="#cc2222", hover_color="#881111",
            text_color="#ffffff", font=("Consolas", 14, "bold"),
            command=self.stop_scan, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            ctrl, text="🧹 Limpar", width=120, height=40,
            fg_color="#555555", hover_color="#333333",
            text_color="#ffffff", font=("Consolas", 14, "bold"),
            command=self.clear_results
        )
        self.clear_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            ctrl, text="💾 Salvar HTML", width=140, height=40,
            fg_color="#0066aa", hover_color="#004477",
            text_color="#ffffff", font=("Consolas", 14, "bold"),
            command=self.save_html
        )
        self.save_btn.pack(side="left", padx=5)

        self.save_txt_btn = ctk.CTkButton(
            ctrl, text="📝 Salvar TXT", width=140, height=40,
            fg_color="#886600", hover_color="#553300",
            text_color="#ffffff", font=("Consolas", 14, "bold"),
            command=self.save_txt
        )
        self.save_txt_btn.pack(side="left", padx=5)

    def create_stats(self):
        stats = ctk.CTkFrame(self, fg_color="#0a120a", corner_radius=8)
        stats.grid(row=3, column=0, padx=20, pady=(5, 0), sticky="ew")

        self.total_label = ctk.CTkLabel(
            stats, text="📚 WORDLIST: 0",
            font=("Consolas", 12, "bold"), text_color="#ffffff"
        )
        self.total_label.pack(side="left", padx=15, pady=8)

        self.remaining_label = ctk.CTkLabel(
            stats, text="⏳ RESTANTES: 0",
            font=("Consolas", 12, "bold"), text_color="#ffff00"
        )
        self.remaining_label.pack(side="left", padx=15, pady=8)

        self.found_label = ctk.CTkLabel(
            stats, text="✅ ENCONTRADOS: 0",
            font=("Consolas", 12, "bold"), text_color="#00ff41"
        )
        self.found_label.pack(side="left", padx=15, pady=8)

        self.current_target = ctk.CTkLabel(
            stats, text="",
            font=("Consolas", 11), text_color="#00ffff", anchor="w"
        )
        self.current_target.pack(
            side="left", padx=(30, 10),
            fill="x", expand=True, pady=8
        )

    def create_results(self):
        self.result_area = ctk.CTkTextbox(
            self, font=("Consolas", 13),
            corner_radius=10, fg_color="#050a05"
        )
        self.result_area.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.result_area.insert("0.0", "DNS SUB - Aguardando início do scan...\n")
        self.result_area.configure(state="disabled")

        text = self.result_area._textbox
        text.tag_config("green", foreground="#00ff41")
        text.tag_config("pumpkin", foreground="#ff9900")
        text.tag_config("red", foreground="#ff3333")
        text.tag_config("yellow", foreground="#ffff00")
        text.tag_config("cyan", foreground="#00ffff")
        text.tag_config("white", foreground="#ffffff")
        text.tag_config("normal", foreground="#b8ffb8")

    # ========================================
    # FUNÇÕES AUXILIARES
    # ========================================
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist_path.set(filename)
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                    words = [line.strip() for line in f if line.strip()]
                self.total_words = len(words)
                self.remaining_words = self.total_words
                self.update_counters()
                self.log(
                    f"[*] Wordlist carregada: {self.total_words} entradas",
                    "yellow"
                )
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler:\n{e}")

    def update_counters(self):
        self.total_label.configure(text=f"📚 WORDLIST: {self.total_words}")
        self.remaining_label.configure(
            text=f"⏳ RESTANTES: {self.remaining_words}"
        )
        self.found_label.configure(
            text=f"✅ ENCONTRADOS: {self.found_count}"
        )

    def log(self, message, tag="normal"):
        self.result_area.configure(state="normal")
        text = self.result_area._textbox
        text.insert("end", message + "\n", tag)
        text.see("end")
        self.result_area.configure(state="disabled")

    def clear_results(self):
        self.result_area.configure(state="normal")
        self.result_area.delete("0.0", "end")
        self.result_area.insert("0.0", "DNS SUB - Console limpo.\n")
        self.result_area.configure(state="disabled")
        self.results.clear()
        self.found_count = 0
        self.remaining_words = 0
        self.total_words = 0
        self.update_counters()

    def stop_scan(self):
        self.scanning = False
        self.log("[!] Scan interrompido pelo usuário.", "red")

    def toggle_scan(self):
        if self.scanning:
            self.stop_scan()
        else:
            self.start_scan()

    def detect_url_protocol(self, host):
        for proto in ("https://", "http://"):
            try:
                url = f"{proto}{host}"
                requests.head(
                    url, timeout=1.8,
                    allow_redirects=False, verify=False
                )
                return url
            except Exception:
                pass
        return f"http://{host}"

    def get_ns_servers(self, domain):
        ns_servers = []
        try:
            if platform.system() == "Windows":
                res = run_subprocess_hidden(
                    ["nslookup", "-type=NS", domain],
                    capture_output=True, text=True,
                    timeout=10, errors="ignore"
                )
                for line in res.stdout.splitlines():
                    low = line.lower()
                    if "nameserver" in low or "name server" in low:
                        parts = line.split("=")
                        if len(parts) > 1:
                            ns = parts[1].strip().rstrip(".")
                            if ns and ns not in ns_servers:
                                ns_servers.append(ns)
            else:
                res = run_subprocess_hidden(
                    ["dig", "NS", domain, "+short"],
                    capture_output=True, text=True,
                    timeout=10, errors="ignore"
                )
                for line in res.stdout.strip().splitlines():
                    ns = line.strip().rstrip(".")
                    if ns and ns not in ns_servers:
                        ns_servers.append(ns)
        except Exception:
            pass
        return ns_servers

    def query_all_records(self, domain, ns_target=None):
        try:
            if platform.system() == "Windows":
                if ns_target:
                    cmd = ["nslookup", "-type=any", domain, ns_target]
                else:
                    cmd = ["nslookup", "-type=any", domain]
            else:
                if ns_target:
                    cmd = [
                        "dig", f"@{ns_target}", domain,
                        "ANY", "+noall", "+answer"
                    ]
                else:
                    cmd = ["dig", domain, "ANY", "+noall", "+answer"]

            self.after(
                0,
                lambda c=" ".join(cmd): self.log(f"$ {c}", "white")
            )
            res = run_subprocess_hidden(
                cmd, capture_output=True, text=True,
                timeout=15, errors="ignore"
            )
            out = res.stdout or ""

            if out.strip():
                self.after(0, lambda: self.log("", "normal"))
                for line in out.splitlines():
                    if not line.strip():
                        self.after(0, lambda: self.log(""))
                        continue

                    low = line.lower()
                    tag = "normal"

                    if "text =" in low or \
                       (line.count('"') >= 2 and "=" in line):
                        tag = "pumpkin"
                    elif "hinfo" in low or \
                         ("cpu" in low and "os" in low):
                        tag = "pumpkin"
                    elif "internet address" in low or \
                         "name =" in low:
                        tag = "green"
                    elif "nameserver" in low or \
                         "name server" in low:
                        tag = "green"
                    elif "mail exchanger" in low:
                        tag = "green"
                    elif any(k in low for k in (
                        "primary name server",
                        "responsible mail addr",
                        "serial", "refresh", "retry",
                        "expire", "default ttl"
                    )):
                        tag = "cyan"
                    elif low.strip().startswith("address:"):
                        tag = "yellow"
                    elif low.strip().startswith("server:"):
                        tag = "yellow"

                    self.after(
                        0,
                        lambda l=line, t=tag: self.log(l, t)
                    )
                    self.results.append({
                        "type": "DNS_RECORD",
                        "url": line.strip(),
                        "ip": ns_target if ns_target else "DNS_Local"
                    })
                    self.found_count += 1
                self.after(0, self.update_counters)
        except Exception as e:
            self.after(
                0,
                lambda err=e: self.log(
                    f"[!] Erro na consulta ANY: {err}", "red"
                )
            )

        self.after(
            0,
            lambda: self.log(
                "\n[*] Consultando registros individuais...\n",
                "yellow"
            )
        )

        record_types = [
            "A", "AAAA", "MX", "TXT", "NS",
            "SOA", "CNAME", "HINFO", "PTR", "SRV"
        ]

        for rtype in record_types:
            if not self.scanning:
                break
            try:
                if platform.system() == "Windows":
                    if ns_target:
                        cmd = [
                            "nslookup", f"-type={rtype}",
                            domain, ns_target
                        ]
                    else:
                        cmd = ["nslookup", f"-type={rtype}", domain]
                else:
                    if ns_target:
                        cmd = [
                            "dig", f"@{ns_target}",
                            domain, rtype, "+short"
                        ]
                    else:
                        cmd = ["dig", domain, rtype, "+short"]

                res = run_subprocess_hidden(
                    cmd, capture_output=True, text=True,
                    timeout=8, errors="ignore"
                )
                out = (res.stdout or "").strip()

                if not out:
                    continue

                useful_lines = []
                for line in out.splitlines():
                    s = line.strip()
                    if not s:
                        continue
                    slow = s.lower()
                    if slow.startswith("server:") or \
                       slow.startswith("address:") or \
                       slow.startswith("default server"):
                        continue
                    if slow.startswith("non-authoritative") or \
                       slow.startswith("***"):
                        continue
                    if "can't find" in slow or \
                       "no records" in slow:
                        continue
                    useful_lines.append(s)

                if not useful_lines:
                    continue

                self.after(
                    0,
                    lambda t=rtype: self.log(
                        f"[+] Registro {t}:", "cyan"
                    )
                )
                for line in useful_lines:
                    self.after(
                        0,
                        lambda l=line: self.log(f"    {l}", "green")
                    )
                    self.results.append({
                        "type": f"DNS_{rtype}",
                        "url": f"{rtype}: {line}",
                        "ip": ns_target or "DNS_Local"
                    })
                    self.found_count += 1
                self.after(0, self.update_counters)
                self.after(0, lambda: self.log(""))
            except Exception:
                pass

    # ========================================
    # INÍCIO DO SCAN (ROUTER)
    # ========================================
    def start_scan(self):
        domain = self.domain_entry.get().strip()
        mode = self.scan_mode.get()

        if not domain:
            messagebox.showerror("Erro", "Digite o domínio alvo!")
            return

        domain = re.sub(r'^https?://', '', domain).strip("/")

        self.found_count = 0
        self.results.clear()
        self.scanning = True

        self.start_btn.configure(text="Scanning...", state="disabled")
        self.stop_btn.configure(state="normal")

        self.result_area.configure(state="normal")
        self.result_area.delete("0.0", "end")
        self.result_area.configure(state="disabled")

        self.log("=" * 110, "green")
        self.log(
            "     DNS SUB  -  Enumeração DNS & Protocolos HTTP/HTTPS",
            "green"
        )
        self.log("=" * 110, "green")
        self.log(f"[*] Alvo        : {domain}", "yellow")
        self.log(f"[*] Modo        : {mode.upper()}", "yellow")
        self.log(
            f"[*] Data/Hora   : "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "yellow"
        )

        if mode == "subdomain":
            wordlist = self.wordlist_path.get().strip()
            if not wordlist:
                messagebox.showerror("Erro", "Selecione uma wordlist!")
                self.reset_buttons()
                return
            try:
                with open(
                    wordlist, "r", encoding="utf-8", errors="ignore"
                ) as f:
                    words = [line.strip() for line in f if line.strip()]
            except Exception as e:
                messagebox.showerror("Erro", f"Erro:\n{e}")
                self.reset_buttons()
                return

            self.total_words = len(words)
            self.remaining_words = self.total_words
            self.update_counters()
            self.log(
                f"[*] Wordlist    : {self.total_words} entradas",
                "yellow"
            )
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_subdomains,
                args=(domain, words), daemon=True
            ).start()

        elif mode == "reverse":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_reverse,
                args=(domain,), daemon=True
            ).start()

        elif mode == "dnsany":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_dnsany,
                args=(domain,), daemon=True
            ).start()

        elif mode == "zonetransfer":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_zonetransfer,
                args=(domain,), daemon=True
            ).start()

        elif mode == "whois_domain":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_whois_domain,
                args=(domain,), daemon=True
            ).start()

        elif mode == "whois_ip":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_whois_ip,
                args=(domain,), daemon=True
            ).start()

        elif mode == "headers":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_headers,
                args=(domain,), daemon=True
            ).start()

        elif mode == "whois":
            self.log("-" * 110, "white")
            Thread(
                target=self.scan_whois,
                args=(domain,), daemon=True
            ).start()

    def reset_buttons(self):
        self.scanning = False
        self.start_btn.configure(text="Iniciar Scan", state="normal")
        self.stop_btn.configure(state="disabled")

    # ========================================
    # SCAN DE SUBDOMÍNIOS
    # ========================================
    def scan_subdomains(self, domain, words):
        try:
            main_ip = socket.gethostbyname(domain)
            main_url = self.detect_url_protocol(domain)
            self.after(
                0,
                lambda u=main_url, ip=main_ip:
                    self.log(f"[+] {u:<65} IP: {ip}", "green")
            )
            self.results.append({
                "type": "PRINCIPAL",
                "url": main_url, "ip": main_ip
            })
            self.found_count += 1
        except Exception:
            self.after(
                0,
                lambda: self.log(
                    f"[!] Falha resolução: {domain}", "red"
                )
            )

        self.after(0, lambda: self.log("", "normal"))

        try:
            for word in words:
                if not self.scanning:
                    break
                word = word.strip().lstrip(".")
                if not word:
                    continue
                subdomain = f"{word}.{domain}"
                self.after(
                    0,
                    lambda s=subdomain:
                        self.current_target.configure(
                            text=f"🔍 Testando: {s}"
                        )
                )

                try:
                    ip = socket.gethostbyname(subdomain)
                    target_url = self.detect_url_protocol(subdomain)
                    self.results.append({
                        "type": "SUBDOMAIN",
                        "url": target_url, "ip": ip
                    })
                    self.found_count += 1
                    self.after(
                        0,
                        lambda u=target_url, i=ip:
                            self.log(
                                f"[+] {u:<65} IP: {i}", "green"
                            )
                    )
                except Exception:
                    pass

                self.remaining_words -= 1
                self.after(0, self.update_counters)

            self.finish_scan()
        except Exception as e:
            self.after(
                0,
                lambda: self.log(f"[!] Erro: {e}", "red")
            )
            self.after(0, self.reset_buttons)

    # ========================================
    # DNS REVERSO
    # ========================================
    def scan_reverse(self, domain):
        self.after(
            0,
            lambda: self.log("[*] Iniciando DNS Reverso\n", "yellow")
        )

        try:
            ip = socket.gethostbyname(domain)
            self.after(
                0,
                lambda: self.log(f"[*] IP base: {ip}\n", "cyan")
            )

            try:
                hostname, aliases, _ = socket.gethostbyaddr(ip)
                url_host = self.detect_url_protocol(hostname)
                self.after(
                    0,
                    lambda u=url_host, i=ip:
                        self.log(
                            f"[+] Reverso: {u:<81} IP: {i}",
                            "green"
                        )
                )
                self.results.append({
                    "type": "REVERSE",
                    "url": url_host, "ip": ip
                })
                self.found_count += 1
            except socket.herror:
                self.after(
                    0,
                    lambda: self.log(
                        "[!] Sem registro PTR para IP base.",
                        "pumpkin"
                    )
                )

            self.after(
                0,
                lambda: self.log(
                    "\n[*] Varrendo /24 com threads\n", "yellow"
                )
            )

            parts = ip.split(".")
            base_ip = ".".join(parts[:3])
            self.total_words = 256
            self.remaining_words = 256
            self.after(0, self.update_counters)

            def lookup_ptr(last_octet):
                if not self.scanning:
                    return None
                target_ip = f"{base_ip}.{last_octet}"
                self.after(
                    0,
                    lambda t=target_ip:
                        self.current_target.configure(
                            text=f"🔄 {t}"
                        )
                )
                try:
                    hostname, _, _ = socket.gethostbyaddr(target_ip)
                    return target_ip, hostname
                except Exception:
                    return None

            with ThreadPoolExecutor(max_workers=40) as executor:
                futures = {
                    executor.submit(lookup_ptr, i): i
                    for i in range(256)
                }
                for future in as_completed(futures):
                    if not self.scanning:
                        break
                    res = future.result()
                    if res:
                        t_ip, host = res
                        url_found = self.detect_url_protocol(host)
                        self.after(
                            0,
                            lambda u=url_found, t=t_ip:
                                self.log(
                                    f"[+] {u:<90} IP: {t}",
                                    "green"
                                )
                        )
                        self.results.append({
                            "type": "REVERSE_RANGE",
                            "url": url_found, "ip": t_ip
                        })
                        self.found_count += 1
                    self.remaining_words -= 1
                    self.after(0, self.update_counters)

        except Exception as e:
            self.after(
                0,
                lambda: self.log(f"[!] Erro: {e}", "red")
            )

        self.finish_scan()

    # ========================================
    # CONSULTA DNS ANY
    # ========================================
    def scan_dnsany(self, domain):
        self.after(
            0,
            lambda: self.log(
                "[*] Consulta DNS Completa (todos os registros)\n",
                "yellow"
            )
        )

        ns_servers = self.get_ns_servers(domain)

        if ns_servers:
            self.after(
                0,
                lambda: self.log(
                    f"[*] Name Servers: {', '.join(ns_servers)}\n",
                    "cyan"
                )
            )
            ns_target = ns_servers[0]
            self.after(
                0,
                lambda n=ns_target:
                    self.log(f"[*] Consultando via: {n}\n", "cyan")
            )
        else:
            ns_target = None
            self.after(
                0,
                lambda: self.log(
                    "[*] Usando resolvedor local.\n", "cyan"
                )
            )

        self.after(0, lambda: self.log("-" * 90, "white"))
        self.query_all_records(domain, ns_target)
        self.finish_scan()

    # ========================================
    # ZONE TRANSFER
    # ========================================
    def scan_zonetransfer(self, domain):
        self.after(
            0,
            lambda: self.log(
                "[*] Verificando transferência de zona (AXFR)\n",
                "yellow"
            )
        )

        ns_servers = self.get_ns_servers(domain)

        if not ns_servers:
            ns_servers = [f"ns1.{domain}", f"ns2.{domain}"]
            self.after(
                0,
                lambda: self.log(
                    f"[*] NS não descobertos. Tentando padrões: "
                    f"{', '.join(ns_servers)}",
                    "pumpkin"
                )
            )
        else:
            self.after(
                0,
                lambda: self.log(
                    f"[*] Name Servers: {', '.join(ns_servers)}\n",
                    "cyan"
                )
            )

        axfr_ok = False

        for ns in ns_servers:
            if not self.scanning:
                break

            self.after(
                0,
                lambda n=ns:
                    self.log(f"[*] Testando AXFR em: {n}", "yellow")
            )
            self.after(
                0,
                lambda n=ns:
                    self.current_target.configure(
                        text=f"📡 AXFR: {n}"
                    )
            )

            try:
                if platform.system() == "Windows":
                    cmd = ["nslookup", "-type=AXFR", domain, ns]
                else:
                    cmd = [
                        "dig", f"@{ns}", domain,
                        "AXFR", "+noall", "+answer"
                    ]

                res = run_subprocess_hidden(
                    cmd, capture_output=True, text=True,
                    timeout=15, errors="ignore"
                )
                out = (res.stdout or "") + "\n" + (res.stderr or "")
                out_lower = out.lower()

                refused = any(x in out_lower for x in [
                    "transfer failed", "refused", "timeout",
                    "timed-out", "timed out",
                    "***", "query refused",
                    "connection timed out"
                ])

                def is_header_line(l):
                    s = l.strip().lower()
                    if not s:
                        return True
                    if s.startswith("server:") or \
                       s.startswith("address:"):
                        return True
                    if s.startswith("default server:") or \
                       s.startswith("dns request"):
                        return True
                    if s.startswith("***") or s.startswith(";"):
                        return True
                    return False

                meaningful = [
                    l for l in out.splitlines()
                    if not is_header_line(l)
                ]

                if refused or not meaningful:
                    self.after(
                        0,
                        lambda n=ns:
                            self.log(
                                f"[!] AXFR RECUSADO em {n}", "red"
                            )
                    )
                    try:
                        ns_ip = socket.gethostbyname(ns)
                        self.after(
                            0,
                            lambda n=ns, i=ns_ip:
                                self.log(
                                    f"    NS {n} → {i}", "pumpkin"
                                )
                        )
                        self.results.append({
                            "type": "NS_INFO",
                            "url": ns, "ip": ns_ip
                        })
                        self.found_count += 1
                        self.after(0, self.update_counters)
                    except Exception:
                        pass
                else:
                    axfr_ok = True
                    self.after(
                        0,
                        lambda n=ns:
                            self.log(
                                f"[+] AXFR ACEITO em {n}!\n", "green"
                            )
                    )
                    for l in meaningful:
                        self.after(
                            0,
                            lambda line=l:
                                self.log(f"    {line}", "green")
                        )
                        self.results.append({
                            "type": "ZONE_RECORD",
                            "url": l.strip(), "ip": ns
                        })
                        self.found_count += 1
                    self.after(0, self.update_counters)

            except Exception as e:
                self.after(
                    0,
                    lambda err=e, n=ns:
                        self.log(f"[!] Erro em {n}: {err}", "red")
                )

        if not axfr_ok and self.scanning:
            self.after(
                0,
                lambda: self.log(
                    "\n[!] Nenhum servidor autorizou AXFR.",
                    "pumpkin"
                )
            )
            self.after(
                0,
                lambda: self.log(
                    "[*] FALLBACK: consulta completa de "
                    "todos registros DNS...\n",
                    "yellow"
                )
            )
            self.after(0, lambda: self.log("=" * 90, "white"))

            ns_target = ns_servers[0] if ns_servers else None
            self.query_all_records(domain, ns_target)

        self.finish_scan()

    # ========================================
    # WHOIS DOMAIN (Porta 43 - Registro Real)
    # ========================================
    def query_whois_socket(self, domain):
        """Consulta WHOIS real via socket TCP porta 43."""
        domain = domain.lower().strip()

        parts = domain.split(".")
        if len(parts) >= 2:
            tld = parts[-1]
            sld = ".".join(parts[-2:])
        else:
            tld = parts[-1]
            sld = domain

        whois_servers = {
            "br": "whois.registro.br",
            "com": "whois.verisign-grs.com",
            "net": "whois.verisign-grs.com",
            "org": "whois.pir.org",
            "info": "whois.afilias.net",
            "biz": "whois.neulevel.biz",
            "us": "whois.nic.us",
            "uk": "whois.nic.uk",
            "io": "whois.nic.io",
            "co": "whois.nic.co",
            "me": "whois.nic.me",
            "online": "whois.nic.online",
            "dev": "whois.nic.google",
            "app": "whois.nic.google",
            "xyz": "whois.nic.xyz",
            "tech": "whois.nic.tech",
            "site": "whois.nic.site",
            "club": "whois.nic.club",
            "pro": "whois.registrypro.pro",
            "edu": "whois.educause.edu",
            "gov": "whois.dotgov.gov",
            "mil": "whois.nic.mil",
            "name": "whois.nic.name",
            "mobi": "whois.dotmobi.mobi",
            "tel": "whois.nic.tel",
            "asia": "whois.nic.asia",
            "cat": "whois.nic.cat",
            "jobs": "whois.nic.jobs",
            "museum": "whois.nic.museum",
            "travel": "whois.nic.travel",
            "coop": "whois.nic.coop",
            "aero": "whois.aero",
            "eu": "whois.eu",
            "de": "whois.denic.de",
            "fr": "whois.nic.fr",
            "it": "whois.nic.it",
            "nl": "whois.sidn.nl",
            "au": "whois.auda.org.au",
            "ca": "whois.cira.ca",
            "jp": "whois.jprs.jp",
            "kr": "whois.kr",
            "cn": "whois.cnnic.cn",
            "ru": "whois.tcinet.ru",
            "in": "whois.registry.in",
            "pt": "whois.dns.pt",
            "es": "whois.nic.es",
            "ar": "whois.nic.ar",
            "mx": "whois.mx",
            "cl": "whois.nic.cl",
            "co": "whois.nic.co",
            "pe": "kero.yachay.pe",
        }

        server = whois_servers.get(tld, None)

        if not server:
            server = "whois.iana.org"

        all_responses = []

        def do_whois_query(srv, query_str):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((srv, 43))
                s.send(f"{query_str}\r\n".encode("utf-8"))
                response = b""
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data
                s.close()
                return response.decode("utf-8", errors="ignore")
            except Exception as e:
                return f"[Erro ao consultar {srv}]: {e}"

        if tld in ("com", "net") and \
           server == "whois.verisign-grs.com":
            query = f"domain {domain}"
        else:
            query = domain

        self.after(
            0,
            lambda sv=server:
                self.log(f"[*] Consultando: {sv} (porta 43)\n", "cyan")
        )
        self.after(
            0,
            lambda sv=server:
                self.current_target.configure(
                    text=f"🌐 WHOIS: {sv}"
                )
        )

        resp1 = do_whois_query(server, query)
        all_responses.append(("Servidor Primário", server, resp1))

        if server == "whois.iana.org":
            for line in resp1.splitlines():
                low = line.lower().strip()
                if low.startswith("whois:") or \
                   low.startswith("refer:"):
                    ref_server = line.split(":", 1)[1].strip()
                    if ref_server:
                        self.after(
                            0,
                            lambda rs=ref_server:
                                self.log(
                                    f"[*] Redirecionado para: {rs}\n",
                                    "yellow"
                                )
                        )
                        resp2 = do_whois_query(ref_server, domain)
                        all_responses.append((
                            "Servidor Autoritativo",
                            ref_server, resp2
                        ))
                    break

        if tld in ("com", "net"):
            for line in resp1.splitlines():
                if "registrar whois server" in line.lower():
                    registrar_server = line.split(":", 1)[1].strip()
                    if registrar_server and \
                       registrar_server != server:
                        self.after(
                            0,
                            lambda rs=registrar_server:
                                self.log(
                                    f"[*] Consultando registrar: "
                                    f"{rs}\n",
                                    "yellow"
                                )
                        )
                        resp3 = do_whois_query(
                            registrar_server, domain
                        )
                        all_responses.append((
                            "Registrar Detalhado",
                            registrar_server, resp3
                        ))
                    break

        return all_responses

    def scan_whois_domain(self, domain):
        """Whois Domain - Consulta registro real do domínio."""
        self.after(
            0,
            lambda: self.log(
                f"[*] Whois Domain Lookup: {domain}\n", "yellow"
            )
        )
        self.after(
            0,
            lambda: self.log(
                "[*] Consulta direta via socket TCP "
                "(porta 43 - WHOIS oficial)\n",
                "cyan"
            )
        )

        try:
            responses = self.query_whois_socket(domain)

            for source_name, server_used, text in responses:
                if not self.scanning:
                    break

                self.after(
                    0,
                    lambda sn=source_name, sv=server_used:
                        self.log(
                            f"\n{'='*90}\n"
                            f"[+] Fonte: {sn} ({sv})\n"
                            f"{'='*90}",
                            "green"
                        )
                )

                lines = text.splitlines()
                for line in lines:
                    if not self.scanning:
                        break

                    clean = line.strip()
                    if not clean:
                        self.after(0, lambda: self.log(""))
                        continue

                    low = clean.lower()
                    skip_terms = [
                        "terms of use", "by submitting",
                        "https://www.icann.org",
                        "for more information",
                        "notice:", "disclaimer:",
                        "the data in this record",
                        "this information is provided",
                        "accuracy of this data",
                        "by the following terms",
                        "you agree that you",
                        "registrar url:",
                    ]
                    if any(t in low for t in skip_terms):
                        continue

                    tag = "normal"

                    if any(k in low for k in (
                        "owner:", "titular:", "registrant name:",
                        "registrant organization:",
                        "registrant:", "responsible:",
                        "responsavel:", "admin name:",
                        "tech name:"
                    )):
                        tag = "green"

                    elif any(k in low for k in (
                        "ownerid:", "document:", "cnpj:",
                        "cpf:", "tax-id:", "registrant id:"
                    )):
                        tag = "pumpkin"

                    elif any(k in low for k in (
                        "nserver:", "nameserver:",
                        "name server:", "dns:",
                        "ns1", "ns2", "ns3", "ns4"
                    )):
                        tag = "cyan"

                    elif any(k in low for k in (
                        "created:", "criado:", "creation date:",
                        "changed:", "alterado:",
                        "updated date:", "update date:",
                        "expires:", "expiracao:",
                        "expiry date:", "expiration date:",
                        "registry expiry"
                    )):
                        tag = "yellow"

                    elif "status:" in low or "domain status:" in low:
                        tag = "white"

                    elif any(k in low for k in (
                        "e-mail:", "email:",
                        "registrant email:",
                        "admin email:", "tech email:",
                        "abuse", "phone:", "fax:"
                    )):
                        tag = "pumpkin"

                    elif any(k in low for k in (
                        "registrar:", "sponsoring registrar:",
                        "registrar name:", "registry domain"
                    )):
                        tag = "green"

                    elif clean.startswith("%") or \
                         clean.startswith("#"):
                        tag = "white"

                    self.after(
                        0,
                        lambda l=clean, t=tag: self.log(l, t)
                    )

                    if ":" in clean and \
                       not clean.startswith(("%", "#", ">>>")):
                        parts = clean.split(":", 1)
                        key = parts[0].strip()
                        val = parts[1].strip() if len(parts) > 1 \
                            else ""
                        self.results.append({
                            "type": "WHOIS_DOMAIN",
                            "url": key,
                            "ip": val
                        })
                        self.found_count += 1

                self.after(0, self.update_counters)

        except Exception as e:
            self.after(
                0,
                lambda err=e:
                    self.log(f"[!] Erro no Whois: {err}", "red")
            )

        self.finish_scan()

    # ========================================
    # WHOIS IP (APIs - Geolocalização / ASN)
    # ========================================
    def scan_whois_ip(self, domain):
        """Whois IP - Consulta informações do IP via APIs."""
        self.after(
            0,
            lambda: self.log(
                f"[*] Whois IP Lookup: {domain}\n", "yellow"
            )
        )
        self.after(
            0,
            lambda: self.log(
                "[*] Consultando informações de IP "
                "(geolocalização, ASN, provedor)\n",
                "cyan"
            )
        )

        try:
            ip = socket.gethostbyname(domain)
            url_detected = self.detect_url_protocol(domain)
            self.after(
                0,
                lambda: self.log(
                    f"[+] Alvo: {url_detected:<55} IP: {ip}\n",
                    "green"
                )
            )
        except Exception:
            ip = domain
            self.after(
                0,
                lambda: self.log(
                    f"[*] Usando entrada direta: {domain}\n",
                    "pumpkin"
                )
            )

        apis = [
            {
                "name": "ipwhois.app",
                "url": f"https://ipwhois.app/json/{ip}"
            },
            {
                "name": "ipinfo.io",
                "url": f"https://ipinfo.io/{ip}/json"
            },
            {
                "name": "ip-api.com",
                "url": f"http://ip-api.com/json/{ip}"
            },
        ]

        for api in apis:
            if not self.scanning:
                break

            api_name = api["name"]
            api_url = api["url"]

            self.after(
                0,
                lambda n=api_name:
                    self.current_target.configure(
                        text=f"🔎 API: {n}"
                    )
            )
            self.after(
                0,
                lambda n=api_name:
                    self.log(
                        f"\n[*] Consultando: {n}",
                        "yellow"
                    )
            )
            self.after(
                0,
                lambda: self.log("-" * 60, "white")
            )

            try:
                resp = requests.get(api_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for k, v in data.items():
                        if v and str(v).strip():
                            val_str = str(v)

                            low_k = k.lower()
                            if any(x in low_k for x in (
                                "org", "isp", "as",
                                "company", "provider"
                            )):
                                c = "green"
                            elif any(x in low_k for x in (
                                "country", "region", "city",
                                "timezone", "loc", "lat", "lon"
                            )):
                                c = "pumpkin"
                            elif any(x in low_k for x in (
                                "ip", "hostname", "type"
                            )):
                                c = "cyan"
                            else:
                                c = "normal"

                            self.after(
                                0,
                                lambda key=k, val=val_str, col=c:
                                    self.log(
                                        f"    {key:<25}: {val}",
                                        col
                                    )
                            )
                            self.results.append({
                                "type": "WHOIS_IP",
                                "url": f"{k}: {val_str}",
                                "ip": ip
                            })
                            self.found_count += 1
                else:
                    self.after(
                        0,
                        lambda n=api_name, code=resp.status_code:
                            self.log(
                                f"[!] {n}: HTTP {code}", "red"
                            )
                    )
            except Exception as e:
                self.after(
                    0,
                    lambda err=e, n=api_name:
                        self.log(
                            f"[!] Erro em {n}: {err}", "red"
                        )
                )

            self.after(0, self.update_counters)

        self.finish_scan()

    # ========================================
    # Whois Lookup
    # ========================================
    def scan_whois(self, domain):
        """Novo modo misto para consulta Whois rápida via APIs externa."""
        self.after(0, lambda: self.log("[*] Whois Lookup\n", "yellow"))
        try:
            ip = socket.gethostbyname(domain)
            url_whois = self.detect_url_protocol(domain)
            self.after(0, lambda: self.log(f"[+] Alvo: {url_whois:<55} IP: {ip}\n", "green"))
        except Exception:
            ip = "N/A"

        apis = [f"https://ipwhois.app/json/{domain}", f"https://ipinfo.io/{ip}/json"]

        for api in apis:
            if not self.scanning:
                break
            try:
                resp = requests.get(api, timeout=8)
                if resp.status_code == 200:
                    for k, v in resp.json().items():
                        if v and str(v).strip():
                            self.after(0, lambda key=k, val=v: self.log(f"    {key:<25}: {val}", "cyan"))
                            self.results.append({"type": "WHOIS", "url": f"{k}: {v}", "ip": ip})
                            self.found_count += 1
            except Exception as e:
                self.after(0, lambda err=e: self.log(f"[!] Erro: {err}", "red"))

        self.finish_scan()

    # ========================================
    # HEADERS HTTP
    # ========================================
    def scan_headers(self, domain):
        self.after(
            0,
            lambda: self.log("[*] Headers HTTP/HTTPS\n", "yellow")
        )

        for proto in ("https://", "http://"):
            if not self.scanning:
                break
            url = f"{proto}{domain}"
            try:
                resp = requests.get(
                    url, timeout=8, verify=False,
                    allow_redirects=True
                )
                self.after(
                    0,
                    lambda u=url, code=resp.status_code:
                        self.log(
                            f"[+] {u} (Status: {code})\n",
                            "green"
                        )
                )
                for h, v in resp.headers.items():
                    c = "pumpkin" if h.lower() in (
                        "server", "x-powered-by", "set-cookie"
                    ) else "cyan"
                    self.after(
                        0,
                        lambda hk=h, hv=v, col=c:
                            self.log(
                                f"    {hk:<35}: {hv}", col
                            )
                    )
                    self.results.append({
                        "type": "HEADER",
                        "url": f"{h}: {v}", "ip": url
                    })
                    self.found_count += 1
                break
            except Exception:
                continue

        self.finish_scan()

    # ========================================
    # FINALIZAÇÃO
    # ========================================
    def finish_scan(self):
        if self.scanning:
            self.after(
                0,
                lambda: self.log("-" * 110, "green")
            )
            self.after(
                0,
                lambda: self.log(
                    f"    Scan finalizado! "
                    f"{self.found_count} Resultados",
                    "green"
                )
            )
            self.after(
                0,
                lambda: self.log("=" * 110, "green")
            )
        else:
            self.after(
                0,
                lambda: self.log("[!] Interrompido.", "red")
            )

        self.after(
            0,
            lambda: self.current_target.configure(
                text="✅ Concluído"
            )
        )
        self.after(0, self.reset_buttons)

    # ========================================
    # SALVAR TXT
    # ========================================
    def save_txt(self):
        if not self.results:
            messagebox.showinfo("Salvar TXT", "Nenhum resultado.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Todos", "*.*")],
            initialfile="dns_SUB_resultados.txt"
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 90 + "\n")
                f.write("  DNS SUB v3.0 - Relatório\n")
                f.write(
                    f"  Data: "
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    f"\n"
                )
                f.write(
                    f"  Domínio: "
                    f"{self.domain_entry.get().strip()}\n"
                )
                f.write(f"  Encontrados: {self.found_count}\n")
                f.write("=" * 90 + "\n\n")
                for r in self.results:
                    tipo = r.get("type", "")
                    url = r.get("url", "")
                    ip = r.get("ip", "")
                    if tipo in ("WHOIS_DOMAIN", "WHOIS_IP", "WHOIS"):
                        f.write(
                            f"[{tipo:<15}] {url:<50} "
                            f"{ip}\n"
                        )
                    else:
                        f.write(
                            f"[{tipo:<15}] {url:<70} "
                            f"IP: {ip}\n"
                        )
                f.write("\n" + "=" * 90 + "\n")
            messagebox.showinfo("Salvo", f"{filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"{e}")

    # ========================================
    # SALVAR HTML
    # ========================================
    def save_html(self):
        if not self.results:
            messagebox.showinfo("Salvar HTML", "Nenhum resultado.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")],
            initialfile="dns_SUB_resultados.html"
        )
        if not filename:
            return

        rows = ""
        for r in self.results:
            tipo = html.escape(r.get("type", ""))
            raw_url = r.get("url", "")
            ip = html.escape(r.get("ip", ""))

            if raw_url.startswith(("http://", "https://")):
                display_url = (
                    f'<a href="{html.escape(raw_url)}" '
                    f'target="_blank" '
                    f'style="color:#00ffff;">'
                    f'{html.escape(raw_url)}</a>'
                )
            else:
                display_url = html.escape(raw_url)

            if tipo in (
                "SUBDOMAIN", "PRINCIPAL",
                "REVERSE", "REVERSE_RANGE"
            ):
                cls = "green"
            elif tipo.startswith("DNS_") or \
                 tipo == "ZONE_RECORD":
                cls = "cyan"
            elif tipo.startswith("WHOIS") or tipo == "WHOIS":
                cls = "whois"
            else:
                cls = "pumpkin"

            if tipo in ("WHOIS_DOMAIN", "WHOIS_IP", "WHOIS"):
                col3_label = ip
            else:
                col3_label = ip

            rows += f"""
            <tr>
                <td class="{cls}">{tipo}</td>
                <td>{display_url}</td>
                <td style="color:#00ff41;
                    font-weight:bold;">{col3_label}</td>
            </tr>"""

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dom = html.escape(self.domain_entry.get().strip())

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>DNS SUB - Relatório</title>
<style>
body {{
    background: #030603;
    color: #b8ffb8;
    font-family: Consolas, monospace;
    margin: 0; padding: 30px;
}}
.container {{ max-width: 1400px; margin: auto; }}
h1 {{
    color: #00ff41;
    text-align: center;
    font-size: 26px;
}}
.info {{
    background: #071007;
    border: 1px solid #174d17;
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 20px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: #071007;
}}
th {{
    background: #101d10;
    color: #00ff41;
    padding: 12px;
    text-align: left;
}}
td {{
    padding: 10px 12px;
    border-bottom: 1px solid #173017;
    word-break: break-word;
}}
tr:hover {{ background: #0d1a0d; }}
.green {{ color: #00ff41; font-weight: bold; }}
.pumpkin {{ color: #ff9900; font-weight: bold; }}
.cyan {{ color: #00ffff; font-weight: bold; }}
.whois {{ color: #ffcc00; font-weight: bold; }}
.footer {{
    margin-top: 30px;
    text-align: center;
    color: #666;
    font-size: 12px;
}}
</style>
</head>
<body>
<div class="container">
<h1>🛡️ DNS SUB - SCAN REPORT</h1>
<div class="info">
    <b>📅 Data:</b> {now}<br><br>
    <b>🎯 Domínio:</b> {dom}<br><br>
    <b>✅ Encontrados:</b> {self.found_count}
</div>
<table>
<thead>
<tr>
    <th>TIPO</th>
    <th>PROPRIEDADE / URL</th>
    <th>VALOR / IP</th>
</tr>
</thead>
<tbody>{rows}</tbody>
</table>
<div class="footer">
    DNS SUB v3.0 - Gerado automaticamente
</div>
</div>
</body>
</html>"""

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Salvo", f"{filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"{e}")


if __name__ == "__main__":
    app = DNSSUBGUI()
    app.mainloop()
