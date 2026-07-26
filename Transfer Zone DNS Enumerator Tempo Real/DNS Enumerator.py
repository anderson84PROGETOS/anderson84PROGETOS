#!/usr/bin/env python3
"""
DNS ENUMERATOR PRO - Modo Gráfico (Tkinter)
Author: Anderson | Uso autorizado apenas em alvos com permissão
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
import json
import time
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_address, ip_network

try:
    import dns.resolver
    import dns.query
    import dns.zone
    import dns.name
    import dns.rdatatype
    import dns.reversename
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

# ─── Config ──────────────────────────────────────────────────────────────────
TIMEOUT = 5
LIFETIME = 10
MAX_WORKERS = 20

# ─── CDN Ranges ──────────────────────────────────────────────────────────────
CDN_RANGES = {
    "Cloudflare": [
        "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
        "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
        "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
        "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
        "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
    ],
    "CloudFront (AWS)": [
        "13.32.0.0/15", "13.35.0.0/16", "13.224.0.0/14",
        "52.46.0.0/18", "52.84.0.0/15", "54.182.0.0/16",
        "54.192.0.0/16", "54.230.0.0/16", "54.239.128.0/18",
        "99.84.0.0/16", "205.251.192.0/19",
    ],
    "Fastly": [
        "23.235.32.0/20", "104.156.80.0/20", "151.101.0.0/16",
        "199.27.72.0/21",
    ],
    "Akamai": [
        "23.32.0.0/11", "23.64.0.0/14", "23.72.0.0/13",
        "23.80.0.0/12", "23.208.0.0/12", "23.216.0.0/13",
        "2.16.0.0/13", "2.20.0.0/14", "2.22.0.0/15",
        "72.246.0.0/16", "92.122.0.0/15", "95.100.0.0/15",
        "173.223.0.0/16", "184.51.0.0/16", "184.85.0.0/16",
    ],
    "Google Cloud/CDN": [
        "8.34.208.0/20", "8.35.192.0/21", "23.236.48.0/20",
        "23.251.128.0/19", "34.64.0.0/10", "34.128.0.0/10",
        "35.184.0.0/14", "35.188.0.0/16", "35.190.0.0/17",
        "35.196.0.0/15", "35.203.0.0/16", "35.207.0.0/17",
        "35.210.0.0/16", "35.220.0.0/15", "35.222.0.0/15",
        "35.235.0.0/16", "35.236.0.0/14", "35.240.0.0/15",
        "35.242.0.0/15", "35.244.0.0/15", "35.246.0.0/16",
        "35.247.0.0/16", "104.154.0.0/15", "104.196.0.0/14",
        "104.197.0.0/16", "104.198.0.0/15", "107.167.160.0/19",
        "107.178.192.0/18", "130.211.0.0/16", "146.148.0.0/17",
        "162.222.176.0/21", "172.217.0.0/16", "172.253.0.0/16",
        "173.194.0.0/16", "173.255.112.0/20", "192.158.28.0/22",
        "199.192.112.0/22", "199.223.232.0/21", "199.223.236.0/23",
        "209.85.128.0/17", "216.58.192.0/19", "216.239.32.0/19",
    ],
}

COMMON_SRV_SERVICES = [
    "_sip._tcp", "_sip._udp", "_sips._tcp",
    "_h323cs._tcp", "_h323ls._udp",
    "_sip._tls", "_jabber._tcp", "_xmpp._tcp",
    "_ldap._tcp", "_kerberos._tcp", "_kerberos._udp",
    "_imap._tcp", "_pop3._tcp", "_smtp._tcp",
]

COMMON_SUBDOMAINS = [
    "www", "mail", "smtp", "pop", "imap", "admin", "blog",
    "ftp", "ssh", "webmail", "cpanel", "whm", "ns1", "ns2",
    "ns3", "mx", "mail1", "mail2", "vpn", "remote", "api",
    "dev", "test", "staging", "app", "portal", "secure",
    "login", "register", "forum", "support", "help", "status",
    "git", "jenkins", "jira", "confluence", "wiki", "docs",
    "cdn", "static", "assets", "img", "images", "css", "js",
    "download", "uploads", "files", "backup", "db", "database",
    "mysql", "redis", "rabbitmq", "kafka", "zookeeper",
    "monitor", "grafana", "prometheus", "kibana", "elastic",
    "swagger", "redoc", "graphql", "rest", "soap", "xmlrpc",
    "owa", "exchange", "autodiscover", "lync", "skype",
    "radius", "tacacs", "ldap", "ad", "dc1", "dc2",
    "dns", "dns1", "dns2", "ntp", "time", "syslog",
    "proxy", "squid", "firewall", "ids", "ips", "waf",
    "phpmyadmin", "phpmyadmin1", "phpmyadmin2",
    "pma", "adminer", "webmin", "usermin",
    "router", "switch", "ap", "wifi", "guest",
    "intranet", "extranet", "partner", "vendor",
    "s3", "bucket", "storage", "cloud", "direct",
    "m", "mobile", "mobi", "wap",
    "newsletter", "mailing", "lists", "bounce",
    "tracking", "analytics", "stats", "metrics",
]


# ══════════════════════════════════════════════════════════════════════════════
#  NÚCLEO DNS
# ══════════════════════════════════════════════════════════════════════════════

class DNSError(Exception):
    pass


def resolve_with_fallback(domain, rtype, nameserver=None, timeout=TIMEOUT, lifetime=LIFETIME):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = lifetime
    if nameserver:
        resolver.nameservers = [nameserver]
    try:
        resposta = resolver.resolve(domain, rtype, raise_on_no_answer=False)
        if resposta.rrset:
            return list(resposta.rrset)
        return []
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout) as e:
        raise DNSError(str(e))


def resolve_ip(hostname, rtype="A", timeout=TIMEOUT):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout * 2
        resp = resolver.resolve(hostname, rtype)
        return resp[0].address if resp.rrset else None
    except Exception:
        return None


def detect_cdn(ip_str):
    try:
        ip = ip_address(ip_str)
        for provider, ranges in CDN_RANGES.items():
            for cidr in ranges:
                if ip in ip_network(cidr, strict=False):
                    return provider
    except ValueError:
        pass
    return None


# ─── Módulos de Enumeração ──────────────────────────────────────────────────

def enum_a(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "A", nameserver)
    if not records:
        return results
    for rr in records:
        ip = rr.address
        cdn = detect_cdn(ip)
        line = f"A        {ip:20s}"
        if cdn:
            line += f"  [{cdn}]"
        results.append(line)
    random_sub = f"xkcd{int(time.time())%10000}.{domain}"
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5
        resp = resolver.resolve(random_sub, "A")
        if resp.rrset:
            results.insert(0, "⚠  WILDCARD DETECTED!")
    except Exception:
        pass
    return results


def enum_aaaa(domain, nameserver=None):
    return [f"AAAA     {rr.address}" for rr in resolve_with_fallback(domain, "AAAA", nameserver)]


def enum_ns(domain, nameserver=None):
    results = []
    for rr in resolve_with_fallback(domain, "NS", nameserver):
        ns_host = rr.target.to_text().rstrip(".")
        ns_ip = resolve_ip(ns_host) or resolve_ip(ns_host, "AAAA") or "?"
        results.append(f"NS       {ns_host:35s}  →  {ns_ip}")
    return results


def enum_mx(domain, nameserver=None):
    results = []
    for rr in resolve_with_fallback(domain, "MX", nameserver):
        pref = rr.preference
        mx_host = rr.exchange.to_text().rstrip(".")
        mx_ip = resolve_ip(mx_host) or resolve_ip(mx_host, "AAAA") or "?"
        results.append(f"MX       {mx_host:35s}  ({pref})  →  {mx_ip}")
    return results


def enum_txt(domain, nameserver=None):
    results = []
    for rr in resolve_with_fallback(domain, "TXT", nameserver):
        txt_data = " ".join(s.decode() if isinstance(s, bytes) else s for s in rr.strings)
        txt_short = txt_data[:200] + "..." if len(txt_data) > 200 else txt_data
        prefix = "[SPF] " if txt_data.startswith("v=spf1") else "[DMARC] " if txt_data.startswith("v=DMARC1") else ""
        results.append(f"TXT      {prefix}{txt_short}")
    return results


def enum_soa(domain, nameserver=None):
    results = []
    for rr in resolve_with_fallback(domain, "SOA", nameserver):
        results.append(
            f"SOA\n"
            f"         MNAME:   {rr.mname}\n"
            f"         RNAME:   {rr.rname}\n"
            f"         SERIAL:  {rr.serial}\n"
            f"         REFRESH: {rr.refresh}s\n"
            f"         RETRY:   {rr.retry}s\n"
            f"         EXPIRE:  {rr.expire}s\n"
            f"         MINIMUM: {rr.minimum}s"
        )
    return results


def enum_cname(domain, nameserver=None):
    try:
        return [f"CNAME    → {rr.target.to_text().rstrip('.')}" for rr in resolve_with_fallback(domain, "CNAME", nameserver)]
    except DNSError:
        return []


def enum_ptr(domain, nameserver=None):
    results = []
    try:
        for rr in resolve_with_fallback(domain, "A", nameserver):
            try:
                rev_name = dns.reversename.from_address(rr.address)
                for ptr_rr in resolve_with_fallback(rev_name, "PTR", nameserver):
                    results.append(f"PTR      {rr.address:20s}  ←  {ptr_rr.target.to_text().rstrip('.')}")
            except Exception:
                results.append(f"PTR      {rr.address:20s}  ←  (sem PTR)")
    except Exception:
        pass
    return results


def enum_hinfo(domain, nameserver=None):
    return [f"HINFO    CPU: {rr.cpu}  OS: {rr.os}" for rr in resolve_with_fallback(domain, "HINFO", nameserver)]


def enum_srv(domain, nameserver=None):
    results = []
    for service in COMMON_SRV_SERVICES:
        srv_domain = f"{service}.{domain}"
        try:
            for rr in resolve_with_fallback(srv_domain, "SRV", nameserver):
                target = rr.target.to_text().rstrip(".")
                target_ip = resolve_ip(target) or resolve_ip(target, "AAAA") or "?"
                results.append(f"SRV      {srv_domain:30s}  → {target} ({target_ip}):{rr.port}  prio={rr.priority} weight={rr.weight}")
        except DNSError:
            pass
    return results


def enum_ds(domain, nameserver=None):
    return [f"DS       KeyTag={rr.key_tag} Algorithm={rr.algorithm} DigestType={rr.digest_type} Digest={rr.digest.hex()}" for rr in resolve_with_fallback(domain, "DS", nameserver)]


def enum_nsec3(domain, nameserver=None):
    return [f"NSEC3    {rr.next_hashed_owner_name.hex()} Flags={rr.flags} Iterations={rr.iterations}" for rr in resolve_with_fallback(domain, "NSEC3", nameserver)]


def enum_caa(domain, nameserver=None):
    results = []
    try:
        for rr in resolve_with_fallback(domain, "CAA", nameserver):
            tag = rr.tag.decode() if isinstance(rr.tag, bytes) else rr.tag
            value = rr.value.decode() if isinstance(rr.value, bytes) else rr.value
            results.append(f"CAA      Flags={rr.flags} {tag}={value}")
    except DNSError:
        pass
    return results


def enum_dnskey(domain, nameserver=None):
    results = []
    try:
        for rr in resolve_with_fallback(domain, "DNSKEY", nameserver):
            algo_name = dns.dnssec.algorithm_to_text(rr.algorithm)
            results.append(f"DNSKEY   Flags={rr.flags} Protocol={rr.protocol} Algorithm={algo_name} Key={rr.key.hex()[:40]}...")
    except (DNSError, AttributeError):
        pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPAL DA INTERFACE GRÁFICA
# ══════════════════════════════════════════════════════════════════════════════

class DNSEnumeratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Enumerator")
        self.root.geometry("1100x750")
        self.root.state("zoomed")
        self.root.minsize(900, 650)

        # Variáveis de estado
        self.running = False
        self.stop_requested = False
        self.results_data = {}
        self.progress_var = tk.IntVar(value=0)
        self.total_steps = 0
        self.completed_steps = 0

        # Cores e estilo
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        self.warn_color = "#fab387"
        self.root.configure(bg=self.bg_color)

        self._build_ui()

        # Verifica dependências
        if not DNS_AVAILABLE:
            messagebox.showerror(
                "Dependência Ausente",
                "dnspython não está instalado!\n\n"
                "Instale com: pip install dnspython"
            )

    def _build_ui(self):
        """Constrói todos os componentes da interface."""
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Título
        title = tk.Label(
            main_frame,
            text="DNS ENUMERATOR PRO",
            font=("Consolas", 18, "bold"),
            fg=self.accent_color,
            bg=self.bg_color,
        )
        title.pack(pady=(0, 5))

        subtitle = tk.Label(
            main_frame,
            text="Enumeração DNS Avançada • Apenas para uso autorizado",
            font=("Segoe UI", 10),
            fg=self.warn_color,
            bg=self.bg_color,
        )
        subtitle.pack(pady=(0, 10))

        # ─── Configuração ────────────────────────────────────
        config_frame = tk.LabelFrame(
            main_frame,
            text=" Configuração do Alvo ",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_color,
            bg=self.bg_color,
            relief=tk.GROOVE,
            padx=10,
            pady=10,
        )
        config_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = tk.Frame(config_frame, bg=self.bg_color)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Domínio:", font=("Segoe UI", 9, "bold"),
                 fg=self.fg_color, bg=self.bg_color, width=10, anchor="w").pack(side=tk.LEFT)
        self.entry_domain = tk.Entry(row1, font=("Consolas", 10), bg="#313244",
                                      fg=self.fg_color, insertbackground=self.fg_color,
                                      relief=tk.SUNKEN, bd=2)
        self.entry_domain.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Label(row1, text="NS (opc.):", font=("Segoe UI", 9, "bold"),
                 fg=self.fg_color, bg=self.bg_color).pack(side=tk.LEFT)
        self.entry_ns = tk.Entry(row1, font=("Consolas", 10), bg="#313244",
                                  fg=self.fg_color, insertbackground=self.fg_color,
                                  relief=tk.SUNKEN, bd=2, width=20)
        self.entry_ns.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(row1, text="Timeout:", font=("Segoe UI", 9, "bold"),
                 fg=self.fg_color, bg=self.bg_color).pack(side=tk.LEFT)
        self.spin_timeout = tk.Spinbox(row1, from_=1, to=30, width=4,
                                        font=("Consolas", 10), bg="#313244",
                                        fg=self.fg_color, buttonbackground="#45475a",
                                        relief=tk.SUNKEN, bd=2)
        self.spin_timeout.pack(side=tk.LEFT)
        self.spin_timeout.delete(0, tk.END)
        self.spin_timeout.insert(0, "5")

        # ─── Tipos de Registro ───────────────────────────────
        types_frame = tk.LabelFrame(
            main_frame,
            text=" Tipos de Registro ",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_color,
            bg=self.bg_color,
            relief=tk.GROOVE,
            padx=10,
            pady=5,
        )
        types_frame.pack(fill=tk.X, pady=(0, 8))

        self.type_vars = {}
        all_types = [
            ("A", True), ("AAAA", False), ("NS", True), ("MX", True),
            ("TXT", True), ("SOA", True), ("CNAME", True), ("PTR", False),
            ("HINFO", False), ("SRV", False), ("DS", False),
            ("NSEC3", False), ("CAA", False), ("DNSKEY", False),
        ]

        row_frame = tk.Frame(types_frame, bg=self.bg_color)
        row_frame.pack(fill=tk.X)

        for i, (tname, default) in enumerate(all_types):
            var = tk.BooleanVar(value=default)
            self.type_vars[tname] = var
            cb = tk.Checkbutton(
                row_frame, text=tname, variable=var,
                font=("Consolas", 9, "bold"),
                fg=self.fg_color, bg=self.bg_color,
                selectcolor=self.bg_color,
                activebackground=self.bg_color,
                activeforeground=self.accent_color,
            )
            cb.grid(row=i // 7, column=i % 7, sticky="w", padx=3, pady=1)

        # ─── Opções Extras ───────────────────────────────────
        opts_frame = tk.LabelFrame(
            main_frame,
            text=" Opções Extras ",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_color,
            bg=self.bg_color,
            relief=tk.GROOVE,
            padx=10,
            pady=5,
        )
        opts_frame.pack(fill=tk.X, pady=(0, 8))

        row_opts = tk.Frame(opts_frame, bg=self.bg_color)
        row_opts.pack(fill=tk.X)

        self.var_axfr = tk.BooleanVar(value=False)
        tk.Checkbutton(row_opts, text="Tentar AXFR (Transferência de Zona)",
                       variable=self.var_axfr,
                       font=("Segoe UI", 9), fg=self.fg_color, bg=self.bg_color,
                       selectcolor=self.bg_color, activebackground=self.bg_color,
                       activeforeground=self.accent_color).pack(side=tk.LEFT, padx=(0, 20))

        self.var_brute = tk.BooleanVar(value=False)
        tk.Checkbutton(row_opts, text="Bruteforce de Subdomínios",
                       variable=self.var_brute,
                       font=("Segoe UI", 9), fg=self.fg_color, bg=self.bg_color,
                       selectcolor=self.bg_color, activebackground=self.bg_color,
                       activeforeground=self.accent_color,
                       command=self._toggle_wordlist).pack(side=tk.LEFT, padx=(0, 10))

        self.btn_wordlist = tk.Button(row_opts, text="📖 Wordlist...",
                                       font=("Segoe UI", 9), bg="#45475a",
                                       fg=self.fg_color, relief=tk.RAISED,
                                       state=tk.DISABLED, command=self._select_wordlist)
        self.btn_wordlist.pack(side=tk.LEFT, padx=(0, 5))

        self.lbl_wordlist = tk.Label(row_opts, text="(usando padrão)",
                                      font=("Segoe UI", 8), fg=self.warn_color,
                                      bg=self.bg_color)
        self.lbl_wordlist.pack(side=tk.LEFT)
        self.wordlist_path = None

        # ─── Ação ────────────────────────────────────────────
        action_frame = tk.Frame(main_frame, bg=self.bg_color)
        action_frame.pack(fill=tk.X, pady=(0, 8))

        self.btn_start = tk.Button(
            action_frame, text="▶  INICIAR ENUMERAÇÃO",
            font=("Segoe UI", 11, "bold"), bg="#a6e3a1", fg="#1e1e2e",
            relief=tk.RAISED, padx=20, pady=5, command=self._start_enumeration
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = tk.Button(
            action_frame, text="⏹  PARAR",
            font=("Segoe UI", 11, "bold"), bg=self.error_color, fg="#1e1e2e",
            relief=tk.RAISED, padx=20, pady=5, state=tk.DISABLED,
            command=self._stop_enumeration
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_save_txt = tk.Button(
            action_frame, text="💾 Salvar TXT",
            font=("Segoe UI", 9), bg="#45475a", fg=self.fg_color,
            relief=tk.RAISED, padx=10, pady=3, state=tk.DISABLED,
            command=self._save_txt
        )
        self.btn_save_txt.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_save_json = tk.Button(
            action_frame, text="💾 Salvar JSON",
            font=("Segoe UI", 9), bg="#45475a", fg=self.fg_color,
            relief=tk.RAISED, padx=10, pady=3, state=tk.DISABLED,
            command=self._save_json
        )
        self.btn_save_json.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_clear = tk.Button(
            action_frame, text="🗑 Limpar",
            font=("Segoe UI", 9), bg="#45475a", fg=self.fg_color,
            relief=tk.RAISED, padx=10, pady=3,
            command=self._clear_output
        )
        self.btn_clear.pack(side=tk.LEFT)

        self.lbl_status = tk.Label(action_frame, text="Pronto",
                                    font=("Segoe UI", 9, "italic"),
                                    fg=self.fg_color, bg=self.bg_color)
        self.lbl_status.pack(side=tk.RIGHT)

        # ─── Progresso ───────────────────────────────────────
        progress_frame = tk.Frame(main_frame, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        self.progress = ttk.Progressbar(
            progress_frame, mode="determinate",
            variable=self.progress_var, length=200
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_progress = tk.Label(
            progress_frame, text="  0%",
            font=("Consolas", 9, "bold"),
            fg=self.accent_color, bg=self.bg_color, width=6, anchor="e"
        )
        self.lbl_progress.pack(side=tk.LEFT, padx=(8, 0))

        # ─── Área de Saída ───────────────────────────────────
        output_frame = tk.LabelFrame(
            main_frame,
            text=" Resultados ",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_color,
            bg=self.bg_color,
            relief=tk.GROOVE,
            padx=5,
            pady=5,
        )
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.txt_output = scrolledtext.ScrolledText(
            output_frame,
            font=("Consolas", 10),
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief=tk.SUNKEN,
            bd=2,
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)

        # Tags de cor
        self.txt_output.tag_config("header", foreground="#89b4fa", font=("Consolas", 11, "bold"))
        self.txt_output.tag_config("section", foreground="#89b4fa", font=("Consolas", 10, "bold"))
        self.txt_output.tag_config("success", foreground="#a6e3a1")
        self.txt_output.tag_config("error", foreground="#f38ba8")
        self.txt_output.tag_config("warn", foreground="#fab387")
        self.txt_output.tag_config("info", foreground="#cdd6f4")
        self.txt_output.tag_config("cdn", foreground="#f5c2e7")
        self.txt_output.tag_config("separator", foreground="#585b70")

    def _log(self, message, tag="info"):
        """Adiciona texto ao widget de saída com a tag especificada."""
        self.txt_output.config(state=tk.NORMAL)
        self.txt_output.insert(tk.END, message + "\n", tag)
        self.txt_output.see(tk.END)
        self.txt_output.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _toggle_wordlist(self):
        if self.var_brute.get():
            self.btn_wordlist.config(state=tk.NORMAL)
        else:
            self.btn_wordlist.config(state=tk.DISABLED)
            self.wordlist_path = None
            self.lbl_wordlist.config(text="(usando padrão)")

    def _select_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecionar Wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if path:
            self.wordlist_path = path
            name = os.path.basename(path)
            self.lbl_wordlist.config(text=f"📄 {name}")

    def _set_running_state(self, running):
        """Altera estado dos botões durante execução."""
        self.running = running
        if running:
            self.btn_start.config(state=tk.DISABLED, bg="#585b70")
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_save_txt.config(state=tk.DISABLED)
            self.btn_save_json.config(state=tk.DISABLED)
            self.lbl_status.config(text="🔄 Executando...", fg=self.warn_color)
        else:
            self.btn_start.config(state=tk.NORMAL, bg="#a6e3a1")
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_save_txt.config(state=tk.NORMAL)
            self.btn_save_json.config(state=tk.NORMAL)
            self.lbl_status.config(text="✅ Concluído", fg=self.success_color)

    def _update_progress(self):
        """Atualiza a barra de progresso com base nos steps concluídos."""
        if self.total_steps == 0:
            pct = 0
        else:
            pct = int((self.completed_steps / self.total_steps) * 100)
            pct = min(pct, 100)
        self.progress_var.set(pct)
        self.lbl_progress.config(text=f"  {pct}%")
        self.root.update_idletasks()

    def _stop_enumeration(self):
        self.stop_requested = True
        self._log("\n⏹  Enumeração interrompida pelo usuário.", "warn")

    def _clear_output(self):
        self.txt_output.config(state=tk.NORMAL)
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.config(state=tk.DISABLED)
        self.results_data = {}
        self.btn_save_txt.config(state=tk.DISABLED)
        self.btn_save_json.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.lbl_progress.config(text="  0%")
        self.lbl_status.config(text="Pronto", fg=self.fg_color)

    def _save_txt(self):
        if not self.results_data:
            messagebox.showwarning("Sem dados", "Nenhum resultado para salvar.")
            return
        filename = filedialog.asksaveasfilename(
            title="Salvar como TXT",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("DNS ENUMERATOR PRO - Resultados\n")
                f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n")
                for key, data in self.results_data.items():
                    if isinstance(data, dict) and "title" in data and "lines" in data:
                        f.write(f"\n📌 {data['title']}\n")
                        f.write(f"  {'─' * 60}\n")
                        for line in data["lines"]:
                            f.write(line + "\n")
                f.write("\n" + "=" * 70 + "\n")
                f.write("FIM DO RELATÓRIO\n")
            self._log(f"\n💾  Resultados salvos em: {filename}", "success")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def _save_json(self):
        if not self.results_data:
            messagebox.showwarning("Sem dados", "Nenhum resultado para salvar.")
            return
        filename = filedialog.asksaveasfilename(
            title="Salvar como JSON",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")]
        )
        if not filename:
            return
        try:
            json_data = {"timestamp": datetime.now().isoformat(), "records": {}}
            for key, data in self.results_data.items():
                if isinstance(data, dict) and "title" in data and "lines" in data:
                    json_data["records"][key] = {
                        "type": data["title"],
                        "results": data["lines"]
                    }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            self._log(f"\n💾  Resultados salvos em JSON: {filename}", "success")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    #  EXECUÇÃO PRINCIPAL (THREAD)
    # ══════════════════════════════════════════════════════════════════════════

    def _start_enumeration(self):
        domain = self.entry_domain.get().strip()
        if not domain:
            messagebox.showwarning("Domínio obrigatório", "Informe um domínio alvo.")
            return

        if not DNS_AVAILABLE:
            messagebox.showerror("Dependência Ausente",
                                  "dnspython não está instalado!\n\nInstale com: pip install dnspython")
            return

        nameserver = self.entry_ns.get().strip() or None

        selected_types = [t for t, v in self.type_vars.items() if v.get()]
        if not selected_types:
            messagebox.showwarning("Nenhum tipo", "Selecione ao menos um tipo de registro.")
            return

        do_axfr = self.var_axfr.get()
        do_brute = self.var_brute.get()
        wordlist = self.wordlist_path if do_brute else None

        try:
            timeout = int(self.spin_timeout.get())
        except ValueError:
            timeout = 5

        # Calcula steps para barra de progresso
        self.total_steps = len(selected_types)
        if do_axfr:
            self.total_steps += 1
        if do_brute:
            self.total_steps += 1
        self.completed_steps = 0
        self.progress_var.set(0)
        self.lbl_progress.config(text="  0%")

        self.stop_requested = False
        self.results_data = {}
        self._clear_output()

        # Cabeçalho
        self._log(f"{'═' * 70}", "separator")
        self._log(f"📡  Alvo: {domain}", "header")
        self._log(f"📅  Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "info")
        self._log(f"🌐  Nameserver: {nameserver or 'Automático'}", "info")
        self._log(f"⏱  Timeout: {timeout}s", "info")
        self._log(f"📊  Steps totais: {self.total_steps}", "info")
        self._log(f"{'═' * 70}", "separator")

        self._set_running_state(True)

        thread = threading.Thread(target=self._run_enumeration,
                                   args=(domain, nameserver, selected_types,
                                         do_axfr, do_brute, wordlist, timeout),
                                   daemon=True)
        thread.start()

    def _run_enumeration(self, domain, nameserver, selected_types,
                          do_axfr, do_brute, wordlist, timeout):
        """Executa a enumeração em background e atualiza a GUI via callbacks."""
        try:
            type_funcs = {
                "A": ("Registros A (IPv4)", enum_a),
                "AAAA": ("Registros AAAA (IPv6)", enum_aaaa),
                "NS": ("Servidores de Nomes (NS)", enum_ns),
                "MX": ("Servidores de Email (MX)", enum_mx),
                "TXT": ("Registros TXT (SPF/DKIM/DMARC)", enum_txt),
                "SOA": ("Início de Autoridade (SOA)", enum_soa),
                "CNAME": ("Aliases (CNAME)", enum_cname),
                "PTR": ("Reverse DNS (PTR)", enum_ptr),
                "HINFO": ("Informações do Host (HINFO)", enum_hinfo),
                "SRV": ("Registros de Serviço (SRV)", enum_srv),
                "DS": ("DNSSEC - DS", enum_ds),
                "NSEC3": ("DNSSEC - NSEC3", enum_nsec3),
                "CAA": ("Autorização de CA (CAA)", enum_caa),
                "DNSKEY": ("DNSSEC - DNSKEY", enum_dnskey),
            }

            # ── FASE 1: Consultas DNS ──
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {}
                for rtype in selected_types:
                    if rtype in type_funcs:
                        name, func = type_funcs[rtype]
                        futures[executor.submit(func, domain, nameserver)] = (rtype, name)

                for future in as_completed(futures):
                    if self.stop_requested:
                        return
                    rtype, name = futures[future]
                    try:
                        lines = future.result()
                        if lines:
                            self.root.after(0, self._display_section, name, lines, rtype)
                    except Exception as e:
                        self.root.after(0, self._log, f"  Erro em {name}: {e}", "error")

                    self.completed_steps += 1
                    self.root.after(0, self._update_progress)

            if self.stop_requested:
                return

            # ── FASE 2: AXFR ──
            if do_axfr:
                self.root.after(0, self._log, f"\n▶  Tentando AXFR...", "section")
                axfr_lines = self._run_axfr(domain, nameserver, timeout)
                if axfr_lines:
                    self.root.after(0, self._display_section,
                                     "Transferência de Zona (AXFR)", axfr_lines, "AXFR")
                self.completed_steps += 1
                self.root.after(0, self._update_progress)

            if self.stop_requested:
                return

            # ── FASE 3: Subdomain bruteforce (TEMPO REAL) ──
            if do_brute:
                self._run_subdomain_brute(domain, wordlist)
                self.completed_steps += 1
                self.root.after(0, self._update_progress)

            # ── Finalização ──
            if not self.stop_requested:
                self.root.after(0, self._log, f"\n{'═' * 70}", "separator")
                self.root.after(0, self._log, "\n✅  Enumeração concluída!", "success")
                self.root.after(0, self._log,
                                 f"\n📅  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "info")
                self.root.after(0, self._log, f"{'═' * 70}", "separator")
                self.completed_steps = self.total_steps
                self.root.after(0, self._update_progress)

            self.root.after(0, self._set_running_state, False)

        except Exception as e:
            self.root.after(0, self._log, f"\n❌  Erro fatal: {e}", "error")
            self.root.after(0, self._set_running_state, False)

    def _display_section(self, title, lines, key):
        """Exibe uma seção de resultados na GUI."""
        self._log(f"\n📌  {title}", "section")
        self._log(f"  {'─' * 60}", "separator")
        for line in lines:
            if "WILDCARD" in line:
                self._log(f"  {line}", "warn")
            elif "[Cloudflare]" in line or "[CloudFront" in line or "[Fastly]" in line or "[Akamai]" in line or "[Google" in line:
                self._log(f"  {line}", "cdn")
            elif "✅" in line or "sucedida" in line or "concluído" in line:
                self._log(f"  {line}", "success")
            elif "✘" in line or "Erro" in line or "falhou" in line or "rejeitada" in line:
                self._log(f"  {line}", "error")
            elif "⚠" in line:
                self._log(f"  {line}", "warn")
            else:
                self._log(f"  {line}", "info")

        self.results_data[key] = {"title": title, "lines": lines}

    # ══════════════════════════════════════════════════════════════════════════
    #  AXFR
    # ══════════════════════════════════════════════════════════════════════════

    def _run_axfr(self, domain, nameserver, timeout):
        """Executa AXFR e retorna linhas de resultado."""
        results = []
        ns_list = []

        if nameserver:
            ns_list = [nameserver]
        else:
            try:
                records = resolve_with_fallback(domain, "NS")
                for rr in records:
                    ns_list.append(rr.target.to_text().rstrip("."))
            except DNSError:
                results.append("⚠  Não foi possível descobrir nameservers para AXFR")
                return results

        if not ns_list:
            results.append("⚠  Nenhum nameserver encontrado")
            return results

        zone_fqdn = domain if domain.endswith('.') else domain + '.'

        for ns_host in ns_list:
            if self.stop_requested:
                break

            results.append(f"▶  Tentando AXFR em: {ns_host}")
            ns_ip = resolve_ip(ns_host, "A", timeout)
            if not ns_ip:
                results.append(f"✘  Não foi possível resolver {ns_host}")
                continue
            results.append(f"   → IP: {ns_ip}")

            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout + 5)

            try:
                xfr = dns.query.xfr(ns_ip, zone_fqdn, timeout=timeout,
                                     lifetime=timeout + 5, port=53)
                try:
                    zone = dns.zone.from_xfr(xfr, relativize=True)
                except (ValueError, StopIteration, TypeError):
                    zone = dns.zone.Zone(zone_fqdn)
                    dns.query.inbound_xfr(ns_ip, zone, timeout=timeout,
                                           lifetime=timeout + 5, port=53)

                socket.setdefaulttimeout(old_timeout)

                results.append(f"\n✅ TRANSFERÊNCIA DE ZONA BEM-SUCEDIDA em: {ns_host}")
                results.append(f"  {'─' * 60}")

                origin = zone.origin
                names = sorted(zone.nodes.keys())

                if not names:
                    results.append("   ⚠  Zona vazia.")
                    continue

                for nome in names:
                    node = zone[nome]
                    for rdataset in node:
                        rdtype_str = dns.rdatatype.to_text(rdataset.rdtype)
                        for rr in rdataset:
                            try:
                                host_str = nome.relative_to(origin).to_text()
                            except Exception:
                                host_str = str(nome)
                            if host_str == '@' or host_str.rstrip('.') == origin.to_text().rstrip('.'):
                                host_str = '@'
                            results.append(f"    {host_str:40s} {rdtype_str:8s} {rr}")

                results.append(f"  {'─' * 60}")
                results.append(f"📊  Total: {len(names)} registros")

            except dns.query.TransferError:
                results.append(f"\n✘  AXFR rejeitada por: {ns_host}\n")
            except dns.exception.Timeout:
                results.append(f"✘  AXFR timeout em {ns_host}\n")
            except ConnectionRefusedError:
                results.append(f"✘  Conexão recusada em {ns_host}:53\n")
            except OSError as e:
                results.append(f"✘  Erro de socket: {e}\n")
            except Exception as e:
                results.append(f"✘  AXFR falhou: {e}\n")
            finally:
                try:
                    socket.setdefaulttimeout(old_timeout)
                except Exception:
                    pass

        return results

    # ══════════════════════════════════════════════════════════════════════════
    #  BRUTEFORCE DE SUBDOMÍNIOS (TEMPO REAL)
    # ══════════════════════════════════════════════════════════════════════════

    def _run_subdomain_brute(self, domain, wordlist_path):
        """Executa bruteforce de subdomínios e exibe resultados em tempo real."""
        if wordlist_path:
            try:
                with open(wordlist_path, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f if line.strip()]
                self.root.after(0, self._log,
                                 f"\n\n📖  Wordlist: {os.path.basename(wordlist_path)} ({len(words)} palavras)\n", "info")
            except Exception:
                words = COMMON_SUBDOMAINS
                self.root.after(0, self._log, "⚠  Erro ao ler wordlist. Usando padrão.", "warn")
        else:
            words = COMMON_SUBDOMAINS
            self.root.after(0, self._log,
                             f"\n📖  Usando wordlist padrão ({len(words)} palavras)\n", "info")

        self.root.after(0, self._log, f"▶  Bruteforce de subdomínios iniciado\n", "section")

        found = 0
        lock = threading.Lock()
        lines_for_save = []

        def check_sub(sub):
            nonlocal found
            if self.stop_requested:
                return
            subdomain = f"{sub}.{domain}"
            try:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 3
                resolver.lifetime = 5
                resp = resolver.resolve(subdomain, "A")
                if resp.rrset:
                    ip = resp[0].address
                    cdn = detect_cdn(ip)
                    tag = f" [{cdn}]" if cdn else ""
                    line = f"    ✅ {subdomain:45s} → {ip}{tag}"
                    with lock:
                        found += 1
                        lines_for_save.append(line)
                    # Exibe em TEMPO REAL na GUI
                    self.root.after(0, self._log, f"  {line}", "success")
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(check_sub, words))

        final_msg = f"\n✅ Bruteforce concluído. {found} subdomínios encontrados."
        self.root.after(0, self._log, final_msg, "success")

        # Guarda nos dados para salvar
        self.results_data["SUBDOMAIN"] = {
            "title": "Subdomínios (Bruteforce)",
            "lines": lines_for_save
        }


# ══════════════════════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app = DNSEnumeratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
