#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReconSuite v2 — Sublister + HTTPX em uma única GUI (abas)
Resultados visuais + exportação HTML estilizada nas duas abas.

Requisitos:
    pip install customtkinter aiohttp requests
"""

import asyncio
import aiohttp
import hashlib
import re
import json
import csv
import socket
import ssl
import time
import os
import html as html_mod
import random
import threading
import webbrowser
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from tkinter import filedialog, messagebox

import customtkinter as ctk
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# TEMA GLOBAL
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLORS = {
    "bg_dark": "#0d1117", "bg_med": "#161b22", "bg_light": "#21262d", "bg_in": "#0d1117",
    "border": "#30363d", "tp": "#c9d1d9", "ts": "#8b949e", "td": "#484f58",
    "blue": "#58a6ff", "green": "#3fb950", "red": "#f85149", "orange": "#d29922",
    "purple": "#bc8cff", "cyan": "#39d2c0",
    "s2": "#3fb950", "s3": "#d29922", "s4": "#f85149", "s5": "#f0883e", "se": "#484f58",
    "bp": "#238636", "bph": "#2ea043", "bd": "#da3633", "bdh": "#f85149",
    "bs": "#21262d", "bsh": "#30363d",
}
FONTS = {"f": "Consolas", "fu": "Segoe UI", "s": 10, "n": 12, "m": 14, "l": 16}

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
DEFAULT_THREADS = 5


def get_status_color(code):
    if 200 <= code < 300: return COLORS["s2"]
    if 300 <= code < 400: return COLORS["s3"]
    if 400 <= code < 500: return COLORS["s4"]
    if 500 <= code < 600: return COLORS["s5"]
    return COLORS["se"]


def _fmt_size(n):
    if not n: return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


# ============================================================
#   PARTE 1 — SUBLISTER (ENUMERAÇÃO DE SUBDOMÍNIOS)
# ============================================================

class SubdomainEngine:
    def __init__(self, domain, callback=None, stop_event=None):
        self.domain = domain
        self.subdomains = set()
        self.callback = callback
        self.stop_event = stop_event or threading.Event()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self._random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        })
        self.session.verify = False
        self.timeout = 25
        self.name = "Base"

    def _random_user_agent(self):
        return random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ])

    def _extract_subdomains(self, text):
        pattern = r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)+" + re.escape(self.domain)
        found = set()
        for m in re.findall(pattern, text, re.IGNORECASE):
            sub = m.strip().lower()
            if sub.endswith("." + self.domain) and sub != self.domain:
                self.subdomains.add(sub)
                found.add(sub)
        return found

    def _log(self, msg):
        if self.callback:
            self.callback(f"[{self.name}] {msg}")

    def enumerate(self):
        raise NotImplementedError

    def get_subdomains(self):
        return self.subdomains


class GoogleEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "Google"

    def enumerate(self):
        self._log("Iniciando enumeração...")
        page, no_new = 0, 0
        while not self.stop_event.is_set() and page < 200 and no_new < 3:
            try:
                query = f"site:{self.domain} -www.{self.domain}"
                for exc in list(self.subdomains)[:5]:
                    query += f" -site:{exc}"
                resp = self.session.get("https://www.google.com/search",
                    params={"q": query, "start": page, "num": 100, "hl": "en", "filter": "0"},
                    timeout=self.timeout)
                if resp.status_code == 429:
                    self._log("Rate limited, aguardando..."); time.sleep(5); continue
                new = self._extract_subdomains(resp.text)
                no_new = 0 if new else no_new + 1
                if new: self._log(f"+{len(new)} novos (Total: {len(self.subdomains)})")
                page += 100
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                self._log(f"Erro: {e}"); break
        self._log(f"Finalizado. Total: {len(self.subdomains)}")
        return self.subdomains


class BingEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "Bing"

    def enumerate(self):
        self._log("Iniciando...")
        page, no_new = 0, 0
        while not self.stop_event.is_set() and page < 500 and no_new < 3:
            try:
                resp = self.session.get("https://www.bing.com/search",
                    params={"q": f"site:{self.domain}", "first": page, "count": 50},
                    timeout=self.timeout)
                new = self._extract_subdomains(resp.text)
                no_new = 0 if new else no_new + 1
                if new: self._log(f"+{len(new)} (Total: {len(self.subdomains)})")
                page += 50
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                self._log(f"Erro: {e}"); break
        self._log(f"Finalizado. Total: {len(self.subdomains)}")
        return self.subdomains


class YahooEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "Yahoo"

    def enumerate(self):
        self._log("Iniciando...")
        page, no_new = 1, 0
        while not self.stop_event.is_set() and page < 200 and no_new < 3:
            try:
                resp = self.session.get("https://search.yahoo.com/search",
                    params={"p": f"site:{self.domain}", "b": page}, timeout=self.timeout)
                new = self._extract_subdomains(resp.text)
                no_new = 0 if new else no_new + 1
                if new: self._log(f"+{len(new)} (Total: {len(self.subdomains)})")
                page += 10
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                self._log(f"Erro: {e}"); break
        self._log(f"Finalizado. Total: {len(self.subdomains)}")
        return self.subdomains


class BaiduEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "Baidu"

    def enumerate(self):
        self._log("Iniciando...")
        page, no_new = 0, 0
        while not self.stop_event.is_set() and page < 200 and no_new < 3:
            try:
                resp = self.session.get("https://www.baidu.com/s",
                    params={"wd": f"site:{self.domain}", "pn": page}, timeout=self.timeout)
                new = self._extract_subdomains(resp.text)
                no_new = 0 if new else no_new + 1
                if new: self._log(f"+{len(new)} (Total: {len(self.subdomains)})")
                page += 10
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                self._log(f"Erro: {e}"); break
        self._log(f"Finalizado. Total: {len(self.subdomains)}")
        return self.subdomains


class DuckDuckGoEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "DuckDuckGo"

    def enumerate(self):
        self._log("Iniciando...")
        try:
            resp = self.session.post("https://duckduckgo.com/", data={"q": f"site:{self.domain}"},
                                     timeout=self.timeout)
            vqd = None
            m = re.search(r'vqd=["\']?([\d-]+)["\']?', resp.text)
            if m: vqd = m.group(1)
            if vqd:
                page, no_new = 0, 0
                while not self.stop_event.is_set() and page < 10 and no_new < 2:
                    resp = self.session.get("https://duckduckgo.com/html/",
                        params={"q": f"site:{self.domain}", "s": page, "vqd": vqd},
                        timeout=self.timeout)
                    new = self._extract_subdomains(resp.text)
                    no_new = 0 if new else no_new + 1
                    if new: self._log(f"+{len(new)} (Total: {len(self.subdomains)})")
                    page += 30
                    time.sleep(2)
            else:
                resp = self.session.get("https://html.duckduckgo.com/html/",
                    params={"q": f"site:{self.domain}"}, timeout=self.timeout)
                self._extract_subdomains(resp.text)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        self._log(f"Finalizado. Total: {len(self.subdomains)}")
        return self.subdomains


class CrtShEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "crt.sh"

    def enumerate(self):
        self._log("Consultando Certificate Transparency...")
        try:
            resp = self.session.get(f"https://crt.sh/?q=%.{self.domain}&output=json", timeout=40)
            if resp.ok:
                data = resp.json()
                for entry in data:
                    for name in entry.get("name_value", "").split("\n"):
                        name = name.strip().lower().lstrip("*.")
                        if name.endswith("." + self.domain):
                            self.subdomains.add(name)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class HackerTargetEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "HackerTarget"

    def enumerate(self):
        self._log("Consultando API...")
        try:
            resp = self.session.get(
                f"https://api.hackertarget.com/hostsearch/?q={self.domain}", timeout=self.timeout)
            if "error" not in resp.text.lower():
                for line in resp.text.splitlines():
                    parts = line.split(",")
                    if parts and parts[0].endswith("." + self.domain):
                        self.subdomains.add(parts[0].strip().lower())
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class AlienVaultEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "AlienVault"

    def enumerate(self):
        self._log("Consultando OTX...")
        try:
            resp = self.session.get(
                f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns",
                timeout=self.timeout)
            if resp.ok:
                for r in resp.json().get("passive_dns", []):
                    h = r.get("hostname", "").lower()
                    if h.endswith("." + self.domain):
                        self.subdomains.add(h)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class RapidDNSEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "RapidDNS"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get(f"https://rapiddns.io/subdomain/{self.domain}?full=1",
                                    timeout=self.timeout)
            self._extract_subdomains(resp.text)
            self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class BufferOverEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "BufferOver"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get(f"https://dns.bufferover.run/dns?q=.{self.domain}",
                                    timeout=self.timeout)
            if resp.ok:
                data = resp.json()
                for rec in (data.get("FDNS_A", []) or []) + (data.get("RDNS", []) or []):
                    sub = rec.split(",")[0].strip().lower()
                    if sub.endswith("." + self.domain):
                        self.subdomains.add(sub)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class CertSpotterEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "CertSpotter"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get("https://api.certspotter.com/v1/issuances",
                params={"domain": self.domain, "include_subdomains": "true", "expand": "dns_names"},
                timeout=self.timeout)
            if resp.ok:
                for entry in resp.json():
                    for name in entry.get("dns_names", []):
                        name = name.lower().lstrip("*.")
                        if name.endswith("." + self.domain):
                            self.subdomains.add(name)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class AnubisDBEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "AnubisDB"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get(f"https://jldc.me/anubis/subdomains/{self.domain}",
                                    timeout=self.timeout)
            if resp.ok:
                for sub in resp.json():
                    sub = str(sub).lower().lstrip("*.").strip()
                    if sub.endswith("." + self.domain):
                        self.subdomains.add(sub)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class URLScanEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "URLScan"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get("https://urlscan.io/api/v1/search/",
                params={"q": f"domain:{self.domain}", "size": 1000}, timeout=self.timeout)
            if resp.ok:
                for r in resp.json().get("results", []):
                    p = urlparse(r.get("page", {}).get("url", ""))
                    h = (p.netloc or "").lower().split(":")[0]
                    if h.endswith("." + self.domain):
                        self.subdomains.add(h)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class ThreatMinerEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "ThreatMiner"

    def enumerate(self):
        self._log("Consultando...")
        try:
            resp = self.session.get("https://api.threatminer.org/v2/domain.php",
                params={"q": self.domain, "rt": 5}, timeout=self.timeout)
            if resp.ok:
                for sub in resp.json().get("results", []):
                    sub = str(sub).lower()
                    if sub.endswith("." + self.domain):
                        self.subdomains.add(sub)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class VirusTotalEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None, api_key=None):
        super().__init__(d, c, s); self.name = "VirusTotal"; self.api_key = api_key

    def enumerate(self):
        if not self.api_key:
            self._log("Sem API key, pulando"); return self.subdomains
        self._log("Consultando (API key fornecida)...")
        try:
            url = f"https://www.virustotal.com/api/v3/domains/{self.domain}/subdomains"
            headers = {"x-apikey": self.api_key}
            resp = self.session.get(url, headers=headers, params={"limit": 40}, timeout=self.timeout)
            while resp.ok and not self.stop_event.is_set():
                data = resp.json()
                for item in data.get("data", []):
                    sid = item.get("id", "").lower()
                    if sid.endswith("." + self.domain):
                        self.subdomains.add(sid)
                self._log(f"Total: {len(self.subdomains)}")
                cursor = data.get("meta", {}).get("cursor")
                if not cursor: break
                resp = self.session.get(url, headers=headers,
                                        params={"limit": 40, "cursor": cursor}, timeout=self.timeout)
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class WebArchiveEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "WebArchive"

    def enumerate(self):
        self._log("Consultando Wayback Machine...")
        try:
            resp = self.session.get(
                f"https://web.archive.org/cdx/search/cdx?url=*.{self.domain}&output=json"
                f"&fl=original&collapse=urlkey&limit=10000", timeout=45)
            if resp.ok:
                for row in resp.json()[1:]:
                    p = urlparse(row[0])
                    h = (p.netloc or "").lower().split(":")[0]
                    if h.endswith("." + self.domain):
                        self.subdomains.add(h)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class CommonCrawlEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None):
        super().__init__(d, c, s); self.name = "CommonCrawl"

    def enumerate(self):
        self._log("Consultando índice CC...")
        try:
            resp = self.session.get("https://index.commoncrawl.org/CC-MAIN-2023-50-index",
                params={"url": f"*.{self.domain}", "output": "json"}, timeout=45)
            for line in resp.text.splitlines():
                try:
                    rec = json.loads(line)
                    p = urlparse(rec.get("url", ""))
                    h = (p.netloc or "").lower().split(":")[0]
                    if h.endswith("." + self.domain):
                        self.subdomains.add(h)
                except json.JSONDecodeError:
                    pass
            self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


class SecurityTrailsEngine(SubdomainEngine):
    def __init__(self, d, c=None, s=None, api_key=None):
        super().__init__(d, c, s); self.name = "SecurityTrails"; self.api_key = api_key

    def enumerate(self):
        if not self.api_key:
            self._log("Sem API key, pulando"); return self.subdomains
        self._log("Consultando (API key fornecida)...")
        try:
            resp = self.session.get(f"https://api.securitytrails.com/v1/domain/{self.domain}/subdomains",
                headers={"APIKEY": self.api_key, "Accept": "application/json"}, timeout=self.timeout)
            if resp.ok:
                for sub in resp.json().get("subdomains", []):
                    full = f"{sub}.{self.domain}".lower()
                    if full.endswith("." + self.domain):
                        self.subdomains.add(full)
                self._log(f"Total: {len(self.subdomains)}")
        except Exception as e:
            self._log(f"Erro: {e}")
        return self.subdomains


ENGINE_REGISTRY = [
    ("Google", lambda d, c, s, k: GoogleEngine(d, c, s), False),
    ("Bing", lambda d, c, s, k: BingEngine(d, c, s), False),
    ("Yahoo", lambda d, c, s, k: YahooEngine(d, c, s), False),
    ("Baidu", lambda d, c, s, k: BaiduEngine(d, c, s), False),
    ("DuckDuckGo", lambda d, c, s, k: DuckDuckGoEngine(d, c, s), False),
    ("crt.sh", lambda d, c, s, k: CrtShEngine(d, c, s), False),
    ("HackerTarget", lambda d, c, s, k: HackerTargetEngine(d, c, s), False),
    ("AlienVault", lambda d, c, s, k: AlienVaultEngine(d, c, s), False),
    ("RapidDNS", lambda d, c, s, k: RapidDNSEngine(d, c, s), False),
    ("BufferOver", lambda d, c, s, k: BufferOverEngine(d, c, s), False),
    ("CertSpotter", lambda d, c, s, k: CertSpotterEngine(d, c, s), False),
    ("AnubisDB", lambda d, c, s, k: AnubisDBEngine(d, c, s), False),
    ("URLScan", lambda d, c, s, k: URLScanEngine(d, c, s), False),
    ("ThreatMiner", lambda d, c, s, k: ThreatMinerEngine(d, c, s), False),
    ("VirusTotal", lambda d, c, s, k: VirusTotalEngine(d, c, s, k), True),
    ("WebArchive", lambda d, c, s, k: WebArchiveEngine(d, c, s), False),
    ("CommonCrawl", lambda d, c, s, k: CommonCrawlEngine(d, c, s), False),
    ("SecurityTrails", lambda d, c, s, k: SecurityTrailsEngine(d, c, s, k), True),
]


class Sublist3rCore:
    """Core: roda motores em paralelo, resolve DNS e faz port scan."""

    def __init__(self, domain, engines, threads=5, callback=None,
                 resolve_dns=True, scan_ports=False, vt_api_key=None):
        self.domain = domain.lower().strip()
        self.engine_names = engines
        self.threads = max(1, threads)
        self.callback = callback or (lambda m: None)
        self.resolve_dns = resolve_dns
        self.scan_ports = scan_ports
        self.vt_api_key = vt_api_key
        self.stop_event = threading.Event()
        self.running = False
        self.all_subdomains = set()
        self.resolved: Dict[str, str] = {}
        self.port_results: Dict[str, Dict] = {}

    def stop(self):
        self.stop_event.set()

    def _log(self, msg):
        self.callback(msg)

    def _run_engine(self, name):
        if self.stop_event.is_set():
            return name, set()
        for n, factory, needs_key in ENGINE_REGISTRY:
            if n == name:
                key = self.vt_api_key if needs_key else None
                try:
                    eng = factory(self.domain, self._log, self.stop_event, key)
                    eng.enumerate()
                    return name, eng.get_subdomains()
                except Exception as e:
                    self._log(f"[{name}] Falhou: {e}")
        return name, set()

    def _resolve(self, sub):
        if self.stop_event.is_set():
            return sub, None
        try:
            ip = socket.gethostbyname(sub)
            return sub, ip
        except Exception:
            return sub, None

    def _port_scan(self, sub, ip, ports=(21, 22, 23, 25, 53, 80, 110, 143, 993, 995, 3306, 3389, 5432, 8080, 8443, 8888)):
        found = []
        for p in ports:
            if self.stop_event.is_set():
                break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.5)
                    if s.connect_ex((ip, p)) == 0:
                        found.append(p)
            except Exception:
                pass
        return sub, found

    def run(self):
        self.running = True
        try:
            self._log(f"[*] Enumerando {self.domain} com {len(self.engine_names)} motores...")
            if self.engine_names:
                with ThreadPoolExecutor(max_workers=min(len(self.engine_names), 12)) as ex:
                    futs = {ex.submit(self._run_engine, n): n for n in self.engine_names}
                    for fut in as_completed(futs):
                        if self.stop_event.is_set():
                            break
                        name, subs = fut.result()
                        before = len(self.all_subdomains)
                        self.all_subdomains.update(subs)
                        self._log(f"[+] {name}: {len(subs)} | Acumulado: {len(self.all_subdomains)} "
                                  f"(+{len(self.all_subdomains) - before})")

            if self.resolve_dns and self.all_subdomains and not self.stop_event.is_set():
                self._log(f"[*] Resolvendo DNS para {len(self.all_subdomains)} hosts...")
                subs = sorted(self.all_subdomains)
                done = 0
                with ThreadPoolExecutor(max_workers=self.threads) as ex:
                    futs = {ex.submit(self._resolve, s): s for s in subs}
                    for fut in as_completed(futs):
                        done += 1
                        sub, ip = fut.result()
                        if ip:
                            self.resolved[sub] = ip
                        if done % 20 == 0:
                            self._log(f"[*] DNS {done}/{len(subs)} ({len(self.resolved)} resolvidos)")
                self._log(f"[*] DNS concluído: {len(self.resolved)} resolvidos")

            if self.scan_ports and self.resolved and not self.stop_event.is_set():
                self._log(f"[*] Port scan em {len(self.resolved)} hosts...")
                done = 0
                with ThreadPoolExecutor(max_workers=self.threads) as ex:
                    futs = {ex.submit(self._port_scan, s, ip): s for s, ip in self.resolved.items()}
                    for fut in as_completed(futs):
                        done += 1
                        sub, ports = fut.result()
                        if ports:
                            self.port_results[sub] = {"ip": self.resolved[sub], "ports": ports}
                        if done % 10 == 0:
                            self._log(f"[*] Portscan {done}/{len(self.resolved)}")
                self._log(f"[*] Port scan concluído: {len(self.port_results)} hosts com portas abertas")

            self._log(f"[*] FINALIZADO — {len(self.all_subdomains)} subdomínios, "
                      f"{len(self.resolved)} resolvidos, {len(self.port_results)} com portas")
            return self.all_subdomains
        finally:
            self.running = False


# ============================================================
#   PARTE 2 — HTTPX (PROBE HTTP ASSÍNCRONO)
# ============================================================

TECH_SIGNATURES = {
    "WordPress": [r"wp-content", r"wordpress", r"x-powered-by:\s*php"],
    "React": [r"__NEXT_DATA__", r"react"],
    "Vue": [r"vue", r"__VUE__"],
    "Angular": [r"ng-version", r"angular"],
    "Next.js": [r"__NEXT_DATA__", r"_next/static"],
    "Nuxt": [r"__NUXT__"],
    "jQuery": [r"jquery"],
    "Bootstrap": [r"bootstrap"],
    "Cloudflare": [r"cloudflare", r"cf-ray"],
    "Nginx": [r"nginx"],
    "Apache": [r"apache"],
    "IIS": [r"microsoft-iis"],
    "PHP": [r"x-powered-by:\s*php", r"\.php"],
    "ASP.NET": [r"asp\.net", r"x-aspnet"],
    "Express": [r"x-powered-by:\s*express"],
    "Laravel": [r"laravel", r"xsrf-token"],
    "Django": [r"csrfmiddlewaretoken", r"django"],
    "Shopify": [r"shopify", r"myshopify"],
    "Google Analytics": [r"google-analytics", r"gtag"],
    "Cloudflare CDN": [r"cf-cache-status"],
}


def detect_tech(headers, body):
    found = set()
    hstr = "\n".join(f"{k}:{v}" for k, v in headers.items()).lower()
    body_lower = (body or "").lower()
    for tech, patterns in TECH_SIGNATURES.items():
        for pat in patterns:
            if pat in hstr or (pat.startswith(r"\.") and pat in body_lower) or pat in body_lower[:5000]:
                found.add(tech)
                break
    return sorted(found)[:8]


@dataclass
class ProbeResult:
    input_target: str
    url: str = ""
    final_url: str = ""
    status_code: int = 0
    content_length: int = 0
    title: str = ""
    response_headers: Dict = field(default_factory=dict)
    response_time: float = 0.0
    web_server: str = ""
    content_type: str = ""
    method: str = "GET"
    host: str = ""
    port: int = 0
    scheme: str = ""
    path: str = "/"
    failed: bool = False
    error: str = ""
    ip_address: str = ""
    words: int = 0
    lines: int = 0
    hash_body: str = ""
    technologies: List[str] = field(default_factory=list)
    redirect_url: str = ""
    tls_version: str = ""
    tls_cipher: str = ""
    subject_cn: str = ""
    issuer: str = ""

    def to_oneliner(self):
        parts = [self.url, f"[{self.status_code}]" if not self.failed else "[ERR]"]
        if self.title: parts.append(f"[{self.title[:40]}]")
        if self.web_server: parts.append(f"[{self.web_server}]")
        if self.technologies: parts.append(f"[{','.join(self.technologies[:3])}]")
        if self.ip_address: parts.append(f"[{self.ip_address}]")
        return " ".join(parts)


@dataclass
class ScanConfig:
    method: str = "GET"
    threads: int = DEFAULT_THREADS
    timeout: int = 10
    retries: int = 0
    follow_redirects: bool = True
    ports: List[int] = field(default_factory=lambda: [80, 443])
    probe_title: bool = True
    probe_tech: bool = True
    probe_ip: bool = True
    probe_wl: bool = True
    probe_hash: bool = False
    match_codes: List[int] = field(default_factory=list)
    filter_codes: List[int] = field(default_factory=list)


class Scanner:
    """Scanner assíncrono aiohttp."""

    def __init__(self, targets, config: ScanConfig, callback=None, progress=None):
        self.targets = targets
        self.config = config
        self.callback = callback or (lambda m: None)
        self.progress_cb = progress or (lambda d, t: None)
        self.results: List[ProbeResult] = []
        self._stop = threading.Event()
        self._loop = None
        self._gen_tasks = None

    def stop(self):
        self._stop.set()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._cancel_tasks)

    def _cancel_tasks(self):
        if self._gen_tasks and not self._gen_tasks.done():
            self._gen_tasks.cancel()

    def _extract_title(self, body):
        if not body:
            return ""
        m = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()[:200]
        return ""

    def _gen_urls(self, target):
        target = target.strip()
        if not target or target.startswith("#"):
            return
        if re.match(r"^https?://", target):
            yield target
            return
        target = target.rstrip("/")
        for port in self.config.ports:
            scheme = "https" if port in (443, 8443) else "http"
            if port in (80, 443):
                yield f"{scheme}://{target}"
            else:
                yield f"{scheme}://{target}:{port}"

    async def _probe_one(self, session, url, input_target, sem):
        async with sem:
            if self._stop.is_set():
                return None
            p = urlparse(url)
            r = ProbeResult(input_target=input_target, url=url, method=self.config.method,
                            host=p.hostname or "", port=p.port or (443 if p.scheme == "https" else 80),
                            scheme=p.scheme, path=p.path or "/")
            
            start = time.monotonic()
            for attempt in range(self.config.retries + 1):
                if self._stop.is_set():
                    r.failed = True; r.error = "cancelled"; return r
                try:
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    async with session.request(self.config.method, url, timeout=timeout,
                                               allow_redirects=self.config.follow_redirects,
                                               ssl=False) as resp:
                        r.status_code = resp.status
                        r.response_headers = dict(resp.headers)
                        r.response_time = time.monotonic() - start
                        r.web_server = resp.headers.get("Server", "")[:60]
                        r.content_type = resp.headers.get("Content-Type", "")[:80]
                        r.content_length = int(resp.headers.get("Content-Length", 0) or 0)
                        r.redirect_url = str(resp.headers.get("Location", "") or "")[:300]
                        r.final_url = str(resp.url)
                        body = ""
                        if self.config.method != "HEAD":
                            try:
                                body = await resp.text(errors="ignore")
                            except Exception:
                                body = ""
                        if body:
                            if not r.content_length:
                                r.content_length = len(body.encode("utf-8", "ignore"))
                            if self.config.probe_title:
                                r.title = self._extract_title(body)
                            if self.config.probe_tech:
                                r.technologies = detect_tech(r.response_headers, body)
                            if self.config.probe_wl:
                                r.words = len(body.split())
                                r.lines = body.count("\n") + 1
                            if self.config.probe_hash:
                                r.hash_body = hashlib.sha256(
                                    body.encode("utf-8", "ignore")).hexdigest()[:16]
                        if self.config.probe_ip:
                            try:
                                loop = asyncio.get_event_loop()
                                info = await loop.getaddrinfo(r.host, r.port, family=socket.AF_INET)
                                r.ip_address = info[0][4][0]
                            except Exception:
                                pass
                        if p.scheme == "https":
                            try:
                                ctx = ssl.create_default_context()
                                ctx.check_hostname = False
                                ctx.verify_mode = ssl.CERT_NONE
                                reader, writer = await asyncio.open_connection(r.host, r.port, ssl=ctx)
                                ssl_obj = writer.get_extra_info("ssl_object")
                                if ssl_obj:
                                    r.tls_version = ssl_obj.version() or ""
                                    cipher = ssl_obj.cipher()
                                    r.tls_cipher = cipher[0] if cipher else ""
                                    cert = ssl_obj.getpeercert()
                                    if cert:
                                        r.subject_cn = dict(x[0] for x in cert.get("subject", [])).get("commonName", "")
                                        r.issuer = dict(x[0] for x in cert.get("issuer", [])).get("commonName", "")
                                writer.close()
                                try:
                                    await writer.wait_closed()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        break
                except asyncio.CancelledError:
                    r.failed = True; r.error = "cancelled"
                    return r
                except Exception as e:
                    if attempt < self.config.retries:
                        await asyncio.sleep(1)
                        continue
                    r.failed = True
                    r.response_time = time.monotonic() - start
                    r.error = str(e)[:120]

            if self.config.match_codes:
                if r.failed or r.status_code not in self.config.match_codes:
                    return None
            elif self.config.filter_codes and not r.failed and r.status_code in self.config.filter_codes:
                return None
            
            return r
        
    async def _run_async(self, loop):
        sem = asyncio.Semaphore(max(1, self.config.threads))
        connector = aiohttp.TCPConnector(limit=max(1, self.config.threads), ssl=False, ttl_dns_cache=300)
        ua = {"User-Agent": DEFAULT_UA}
        async with aiohttp.ClientSession(connector=connector, headers=ua) as session:
            tasks = []
            total = 0
            for target in self.targets:
                for url in self._gen_urls(target):
                    tasks.append(asyncio.create_task(self._probe_one(session, url, target, sem)))
                    total += 1
            done = 0
            for fut in asyncio.as_completed(tasks):
                try:
                    r = await fut
                except asyncio.CancelledError:
                    break
                except Exception:
                    r = None
                done += 1
                self.progress_cb(done, total)
                if r:
                    self.results.append(r)
                    tag = f"{r.status_code}" if not r.failed else "ERR"
                    self.callback(f"[{tag}] {r.to_oneliner()}")

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_async(self._loop))
        except Exception:
            pass
        finally:
            try:
                self._loop.close()
            except Exception:
                pass
        return self.results


class HTTPXExporter:
    @staticmethod
    def export(results, fp):
        ext = os.path.splitext(fp)[1].lower()
        if ext == ".json":
            with open(fp, "w", encoding="utf-8") as f:
                json.dump([r.__dict__ for r in results], f, indent=2, ensure_ascii=False)
        elif ext == ".csv":
            with open(fp, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["URL", "Status", "Method", "Title", "Server", "Content-Length",
                            "Response Time", "IP", "Technologies", "Words", "Lines"])
                for r in results:
                    w.writerow([r.url, "ERR" if r.failed else r.status_code, r.method, r.title,
                                r.web_server, r.content_length, f"{r.response_time:.4f}",
                                r.ip_address, ",".join(r.technologies), r.words, r.lines])
        elif ext in (".oneliner", ".txt"):
            with open(fp, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(r.to_oneliner() + "\n")
        else:
            with open(fp, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(r.url + "\n")


# ============================================================
#   PARTE 3 — GERADOR DE RELATÓRIOS HTML
# ============================================================

class ReportHTML:
    BASE_CSS = """
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',Consolas,monospace;
         padding:30px;min-height:100vh}
    .container{max-width:1200px;margin:0 auto}
    header{text-align:center;padding:30px 0;border-bottom:1px solid #30363d;margin-bottom:30px}
    header h1{font-size:2.2em;color:#58a6ff;margin-bottom:8px}
    header .meta{color:#8b949e;font-size:.95em}
    header .meta b{color:#c9d1d9}
    .stats{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:30px}
    .stat{flex:1;min-width:140px;background:#161b22;border:1px solid #30363d;
          border-radius:10px;padding:18px;text-align:center;transition:.2s}
    .stat:hover{transform:translateY(-3px);border-color:#58a6ff}
    .stat .num{font-size:2em;font-weight:bold}
    .stat .lbl{color:#8b949e;font-size:.85em;margin-top:4px;text-transform:uppercase;letter-spacing:1px}
    .filterbar{margin-bottom:14px;display:flex;gap:8px;flex-wrap:wrap}
    .filterbar button,.filterbar input{background:#21262d;color:#c9d1d9;border:1px solid #30363d;
      border-radius:6px;padding:7px 14px;font-family:inherit;cursor:pointer;font-size:.9em}
    .filterbar button:hover{border-color:#58a6ff;color:#58a6ff}
    .filterbar input{cursor:text;flex:1;min-width:200px;outline:none}
    .filterbar input:focus{border-color:#58a6ff}
    table{width:100%;border-collapse:collapse;background:#161b22;border-radius:10px;
          overflow:hidden;border:1px solid #30363d}
    th{background:#21262d;padding:12px 14px;text-align:left;font-size:.8em;
       text-transform:uppercase;letter-spacing:1px;color:#8b949e;border-bottom:2px solid #30363d}
    td{padding:10px 14px;border-bottom:1px solid #21262d;font-size:.92em}
    tr:hover td{background:#1c2129}
    .badge{display:inline-block;padding:3px 10px;border-radius:12px;font-weight:bold;
           font-size:.8em;color:#fff}
    .ip{color:#39d2c0;font-family:Consolas}
    .url{color:#58a6ff;text-decoration:none;font-family:Consolas}
    .url:hover{text-decoration:underline}
    .tech{display:inline-block;background:#21262d;border:1px solid #30363d;color:#d29922;
          border-radius:4px;padding:1px 8px;margin:1px;font-size:.75em;font-family:Consolas}
    .title-cell{color:#c9d1d9;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    footer{text-align:center;color:#484f58;margin-top:40px;padding:20px;
           border-top:1px solid #30363d;font-size:.85em}
    @media print{body{background:#fff;color:#000}}
    """

    @staticmethod
    def _page(title, subtitle, stats_html, body_html):
        return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_mod.escape(title)}</title>
<style>{ReportHTML.BASE_CSS}</style></head>
<body><div class="container">
<header><h1>{html_mod.escape(title)}</h1>
<div class="meta">{subtitle} &mdash; gerado por <b>ReconSuite</b> em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
</header>
{stats_html}
{body_html}
<footer>ReconSuite &bull; Recon Reports &bull; Uso autorizado apenas em testes de segurança legítimos</footer>
</div></body></html>"""

    @staticmethod
    def subdomains_to_html(domain, subdomains, resolved, port_results, fp):
        total = len(subdomains)
        nres = len(resolved)
        nports = len(port_results)
        stats = f"""
<div class="stats">
<div class="stat"><div class="num" style="color:#58a6ff">{total}</div><div class="lbl">Subdomínios</div></div>
<div class="stat"><div class="num" style="color:#3fb950">{nres}</div><div class="lbl">Resolvidos (DNS)</div></div>
<div class="stat"><div class="num" style="color:#d29922">{nports}</div><div class="lbl">Com portas abertas</div></div>
<div class="stat"><div class="num" style="color:#bc8cff">{total - nres}</div><div class="lbl">Sem resolução</div></div>
</div>"""

        rows = []
        for s in subdomains:
            ip = resolved.get(s)
            pr = port_results.get(s, {})
            ports = ",".join(map(str, pr.get("ports", [])))
            badge = ('<span class="badge" style="background:#3fb950">ATIVO</span>'
                     if ip else '<span class="badge" style="background:#484f58">NXDOMAIN</span>')
            if ports:
                badge += f' <span class="badge" style="background:#d29922">{len(pr.get("ports", []))} portas</span>'
            rows.append(f"""<tr data-q="{html_mod.escape(s.lower())} {html_mod.escape((ip or '').lower())}">
<td><a class="url" href="https://{html_mod.escape(s)}" target="_blank">{html_mod.escape(s)}</a></td>
<td>{badge}</td>
<td class="ip">{ip or '&mdash;'}</td>
<td class="ip">{ports or '&mdash;'}</td></tr>""")

        body = f"""
<div class="filterbar">
<input id="q" type="text" placeholder="Filtrar subdomínios..." onkeyup="flt()">
<button onclick="document.getElementById('q').value='';flt()">Limpar</button>
</div>
<table id="tbl">
<thead><tr><th>Subdomínio</th><th>Status</th><th>IP</th><th>Portas Abertas</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<script>
function flt(){{var q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('#tbl tbody tr').forEach(function(r){{
r.style.display=r.getAttribute('data-q').indexOf(q)>-1?'':'none';}});}}
</script>"""
        page = ReportHTML._page(
            f"Relatório de Subdomínios — {domain}",
            f"Alvo: <b>{html_mod.escape(domain)}</b> &bull; {total} subdomínios encontrados",
            stats, body)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(page)

    @staticmethod
    def httpx_to_html(results, fp):
        total = len(results)
        ok2 = sum(1 for r in results if not r.failed and 200 <= r.status_code < 300)
        ok3 = sum(1 for r in results if not r.failed and 300 <= r.status_code < 400)
        ok4 = sum(1 for r in results if not r.failed and 400 <= r.status_code < 500)
        ok5 = sum(1 for r in results if not r.failed and 500 <= r.status_code < 600)
        errs = sum(1 for r in results if r.failed)
        stats = f"""
<div class="stats">
<div class="stat"><div class="num" style="color:#58a6ff">{total}</div><div class="lbl">Total</div></div>
<div class="stat"><div class="num" style="color:#3fb950">{ok2}</div><div class="lbl">200 Sucesso</div></div>
<div class="stat"><div class="num" style="color:#d29922">{ok3}</div><div class="lbl">301 Redirect</div></div>
<div class="stat"><div class="num" style="color:#f85149">{ok4}</div><div class="lbl">405 Erro</div></div>
<div class="stat"><div class="num" style="color:#f0883e">{ok5}</div><div class="lbl">500 Servidor</div></div>
<div class="stat"><div class="num" style="color:#484f58">{errs}</div><div class="lbl">Falhas</div></div>
</div>"""

        rows = []
        for r in sorted(results, key=lambda x: (x.failed, x.status_code)):
            st = "ERR" if r.failed else str(r.status_code)
            clr = "#484f58" if r.failed else get_status_color(r.status_code)
            techs = "".join(f'<span class="tech">{html_mod.escape(t)}</span>' for t in r.technologies)
            rows.append(f"""<tr data-q="{html_mod.escape((r.url + ' ' + r.title + ' ' + r.web_server +
                ' ' + ' '.join(r.technologies) + ' ' + str(r.status_code)).lower())}">
<td><span class="badge" style="background:{clr}">{st}</span></td>
<td><a class="url" href="{html_mod.escape(r.url)}" target="_blank">{html_mod.escape(r.url[:60])}</a></td>
<td class="title-cell">{html_mod.escape(r.title or '') or '&mdash;'}</td>
<td>{html_mod.escape(r.web_server or '') or '&mdash;'}</td>
<td>{techs or '&mdash;'}</td>
<td class="ip">{html_mod.escape(r.ip_address or '') or '&mdash;'}</td>
<td>{_fmt_size(r.content_length)}</td>
<td>{r.response_time:.2f}s</td></tr>""")

        body = f"""
<div class="filterbar">
<input id="q" type="text" placeholder="Filtrar por URL, título, servidor, tecnologia..." onkeyup="flt()">
<button onclick="fltStatus('2')">200</button>
<button onclick="fltStatus('3')">301</button>
<button onclick="fltStatus('4')">405</button>
<button onclick="fltStatus('5')">500</button>
<button onclick="fltStatus('ERR')">Erros</button>
<button onclick="document.getElementById('q').value='';fltAll()">Todos</button>
</div>
<table id="tbl">
<thead><tr><th>Status</th><th>URL</th><th>Título</th><th>Servidor</th><th>Tecnologias</th>
<th>IP</th><th>Tamanho</th><th>Tempo</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<script>
function flt(){{var q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('#tbl tbody tr').forEach(function(r){{
r.style.display=r.getAttribute('data-q').indexOf(q)>-1?'':'none';}});}}
function fltAll(){{document.querySelectorAll('#tbl tbody tr').forEach(function(r){{
r.style.display='';}});}}
function fltStatus(s){{document.querySelectorAll('#tbl tbody tr').forEach(function(r){{
var t=r.cells[0].textContent.trim();
r.style.display=(s==='ERR')?(t==='ERR'?'':'none'):(t[0]===s?'':'none');}});}}
</script>"""
        page = ReportHTML._page(
            "Relatório de Varredura HTTP",
            f"{total} endpoints analisados", stats, body)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(page)


# ============================================================
#   PARTE 4 — GUI (RECONSUITE)
# ============================================================
import platform

class ReconSuite(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Recon Sublister + HTTPX")
        self.geometry("1280x1024")

        try:
            if platform.system() == "Windows":
                self.after(100, lambda: self.state("zoomed"))
            else:
                self.after(100, lambda: self.attributes("-zoomed", True))
        except Exception:
            try:
                self.after(100, lambda: self.state("zoomed"))
            except Exception:
                pass

        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        self.sub_core: Optional[Sublist3rCore] = None
        self.sub_running = False
        self.sub_all: List[str] = []

        self.hx_scanner: Optional[Scanner] = None
        self.hx_scanning = False
        self.hx_all_results: List[ProbeResult] = []

        self._logs_history = []

        self._build_header()
        self.tabview = ctk.CTkTabview(self, fg_color=COLORS["bg_dark"],
                                      segmented_button_fg_color=COLORS["bg_med"],
                                      segmented_button_selected_color=COLORS["bp"],
                                      segmented_button_selected_hover_color=COLORS["bph"],
                                      text_color=COLORS["tp"])
        self.tabview.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.tabview.add("  🔎 Sublister  ")
        self.tabview.add("  🌐 HTTPX  ")
        self.tabview.add("  📜 Logs  ")
        self._build_sublister_tab(self.tabview.tab("  🔎 Sublister  "))
        self._build_httpx_tab(self.tabview.tab("  🌐 HTTPX  "))
        self._build_logs_tab(self.tabview.tab("  📜 Logs  "))

    # ========================================================
    # ABA LOGS
    # ========================================================
    def _build_logs_tab(self, tab):
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(top, text="📜 Console Unificado",
                     font=(FONTS["fu"], FONTS["n"], "bold"),
                     text_color=COLORS["tp"]).pack(side="left")
        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.pack(side="right")
        self.log_filter_sv = ctk.StringVar()
        self.log_filter_sv.trace_add("write", lambda *a: self._logs_rehighlight())
        ctk.CTkEntry(btns, textvariable=self.log_filter_sv, width=200, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="🔍 Filtrar (reabre tudo)").pack(side="left", padx=2)
        ctk.CTkButton(btns, text="💾 Salvar Log", width=100, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._logs_save).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑 Limpar", width=80, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._logs_clear).pack(side="left", padx=2)

        self.logs_console = ctk.CTkTextbox(main, font=(FONTS["f"], FONTS["s"]),
                                           fg_color=COLORS["bg_in"], text_color=COLORS["ts"],
                                           border_color=COLORS["border"], border_width=1,
                                           corner_radius=6)
        self.logs_console.pack(fill="both", expand=True)
        self.logs_console.configure(state="disabled")

    def _logs_clear(self):
        self._logs_history = []
        self.logs_console.configure(state="normal")
        self.logs_console.delete("1.0", "end")
        self.logs_console.configure(state="disabled")

    def _logs_save(self):
        fp = filedialog.asksaveasfilename(defaultextension=".log",
            filetypes=[("Log", "*.log"), ("Texto", "*.txt")])
        if not fp:
            return
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.logs_console.get("1.0", "end"))
            messagebox.showinfo("Sucesso", f"Log salvo em:\n{fp}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _logs_rehighlight(self):
        self.logs_console.configure(state="normal")
        self.logs_console.delete("1.0", "end")
        q = self.log_filter_sv.get().lower()
        for line in self._logs_history:
            if not q or q in line.lower():
                self.logs_console.insert("end", line + "\n")
        self.logs_console.see("end")
        self.logs_console.configure(state="disabled")

    def _logs_append(self, msg):
        self._logs_history.append(msg)
        self.after(0, lambda: self._ui_append(msg))

    def _ui_append(self, msg):
        self.logs_console.configure(state="normal")
        self.logs_console.insert("end", msg + "\n")
        self.logs_console.see("end")
        self.logs_console.configure(state="disabled")

    def destroy(self):
        try:
            if self.sub_core: self.sub_core.stop()
            if self.hx_scanner: self.hx_scanner.stop()
        except Exception:
            pass
        super().destroy()

    # ---------- helpers visuais ----------
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=COLORS["bg_med"], height=56,
                         border_color=COLORS["border"], border_width=1)
        h.pack(fill="x", padx=14, pady=(14, 8)); h.pack_propagate(False)
        ctk.CTkLabel(h, text="🛡 ReconSuite", font=(FONTS["fu"], FONTS["l"], "bold"),
                     text_color=COLORS["blue"]).pack(side="left", padx=16)
        ctk.CTkLabel(h, text="Subdomain Enumeration + HTTP Probing Toolkit",
                     font=(FONTS["fu"], FONTS["s"]), text_color=COLORS["ts"]).pack(side="left", padx=4)

    # ========================================================
    # ABA SUBLISTER
    # ========================================================
    def _build_sublister_tab(self, tab):
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True)

        left = ctk.CTkFrame(main, fg_color=COLORS["bg_med"], border_color=COLORS["border"],
                            border_width=1, corner_radius=8, width=360)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        s = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                   scrollbar_button_color=COLORS["bg_light"],
                                   scrollbar_button_hover_color=COLORS["blue"])
        s.pack(fill="both", expand=True, padx=6, pady=6)

        self._sec(s, "🎯 DOMÍNIO ALVO")
        self.sub_domain_entry = ctk.CTkEntry(s, height=34, font=(FONTS["f"], FONTS["n"]),
                                             fg_color=COLORS["bg_in"], text_color=COLORS["tp"],
                                             border_color=COLORS["border"],
                                             placeholder_text="exemplo.com")
        self.sub_domain_entry.pack(fill="x", padx=4, pady=4)

        self._sec(s, "⚙️ OPÇÕES")
        self.sub_resolve_v = ctk.BooleanVar(value=True)
        r = self._row(s, "Resolver DNS")
        ctk.CTkSwitch(r, text="", variable=self.sub_resolve_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")
        self.sub_portscan_v = ctk.BooleanVar(value=False)
        r = self._row(s, "Port Scan (após resolver)")
        ctk.CTkSwitch(r, text="", variable=self.sub_portscan_v, width=40,
                      progress_color=COLORS["orange"], fg_color=COLORS["bg_light"]).pack(side="right")

        self.sub_threads_v = ctk.StringVar(value=str(DEFAULT_THREADS))
        r = self._row(s, "Threads DNS/Portas")
        ctk.CTkEntry(r, textvariable=self.sub_threads_v, width=70, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"]).pack(side="right")

        self.sub_vt_key_entry = ctk.CTkEntry(s, height=28, show="•",
                                             font=(FONTS["f"], FONTS["s"]),
                                             fg_color=COLORS["bg_in"], text_color=COLORS["tp"],
                                             border_color=COLORS["border"],
                                             placeholder_text="API Key VirusTotal/SecurityTrails (opcional)")
        self.sub_vt_key_entry.pack(fill="x", padx=4, pady=4)

        self._sec(s, "🔍 MOTORES (18)")
        self.sub_engine_vars = {}
        ef = ctk.CTkFrame(s, fg_color="transparent"); ef.pack(fill="x", padx=4)
        default_on = {"Google", "Bing", "Yahoo", "DuckDuckGo", "crt.sh", "HackerTarget",
                      "AlienVault", "RapidDNS", "BufferOver", "CertSpotter", "AnubisDB",
                      "URLScan", "ThreatMiner", "WebArchive", "CommonCrawl"}
        for i, (name, _, _) in enumerate(ENGINE_REGISTRY):
            v = ctk.BooleanVar(value=name in default_on)
            self.sub_engine_vars[name] = v
            ctk.CTkCheckBox(ef, text=name, variable=v, font=(FONTS["fu"], FONTS["s"]),
                            text_color=COLORS["ts"], fg_color=COLORS["bg_light"],
                            checkmark_color=COLORS["green"], border_color=COLORS["border"],
                            height=22).grid(row=i // 2, column=i % 2, sticky="w", padx=4)
        ef.columnconfigure(0, weight=1); ef.columnconfigure(1, weight=1)

        ctk.CTkFrame(s, fg_color="transparent", height=12).pack(fill="x")
        self.sub_start_btn = ctk.CTkButton(s, text="▶  INICIAR ENUMERAÇÃO",
                                           font=(FONTS["fu"], FONTS["m"], "bold"),
                                           fg_color=COLORS["bp"], hover_color=COLORS["bph"],
                                           text_color="#fff", corner_radius=8, height=45,
                                           command=self._sub_start)
        self.sub_start_btn.pack(fill="x", padx=4, pady=6)
        self.sub_stop_btn = ctk.CTkButton(s, text="⏹  PARAR", state="disabled",
                                          font=(FONTS["fu"], FONTS["m"], "bold"),
                                          fg_color=COLORS["bd"], hover_color=COLORS["bdh"],
                                          text_color="#fff", corner_radius=8, height=38,
                                          command=self._sub_stop)
        self.sub_stop_btn.pack(fill="x", padx=4, pady=(0, 6))

        self.sub_progress = ctk.CTkProgressBar(
            s, progress_color=COLORS["green"], fg_color=COLORS["bg_light"],
            height=6, corner_radius=3
        )
        self.sub_progress.pack(fill="x", padx=4, pady=(0, 4))
        self.sub_progress.set(0)

        self.sub_status_lbl = ctk.CTkLabel(
            s, text="Pronto", font=(FONTS["f"], FONTS["s"]), text_color=COLORS["td"]
        )
        self.sub_status_lbl.pack(fill="x", padx=4)

        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)

        stats = ctk.CTkFrame(right, fg_color="transparent", height=78)
        stats.pack(fill="x", pady=(0, 8)); stats.pack_propagate(False)
        self.sub_st_total = self._stat_card(stats, "Subdomínios", COLORS["blue"])
        self.sub_st_resolved = self._stat_card(stats, "Resolvidos", COLORS["green"])
        self.sub_st_ports = self._stat_card(stats, "C/ Portas", COLORS["orange"])

        res_header = ctk.CTkFrame(right, fg_color="transparent")
        res_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(res_header, text="📋 Resultados", font=(FONTS["fu"], FONTS["n"], "bold"),
                     text_color=COLORS["tp"]).pack(side="left")
        btns = ctk.CTkFrame(res_header, fg_color="transparent")
        btns.pack(side="right")
        ctk.CTkButton(btns, text="💾 HTML", width=90, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._sub_export_html).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="💾 TXT/JSON/CSV", width=120, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._sub_export).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="📋 Copiar", width=80, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._sub_copy).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑 Limpar", width=80, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._sub_clear).pack(side="left", padx=2)

        self.sub_sv = ctk.StringVar()
        self.sub_sv.trace_add("write", lambda *a: self._sub_render())
        ctk.CTkEntry(right, textvariable=self.sub_sv, height=30,
                     font=(FONTS["f"], FONTS["n"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="🔍 Filtrar subdomínios...").pack(fill="x", pady=(0, 6))

        self.sub_results_frame = ctk.CTkScrollableFrame(
            right, fg_color=COLORS["bg_med"], border_color=COLORS["border"],
            border_width=1, corner_radius=8,
            scrollbar_button_color=COLORS["bg_light"],
            scrollbar_button_hover_color=COLORS["blue"])
        self.sub_results_frame.pack(fill="both", expand=True)
        self._sub_render()

    def _sec(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=(FONTS["fu"], FONTS["s"], "bold"),
                     text_color=COLORS["blue"], anchor="w").pack(fill="x", padx=4, pady=(10, 2))

    def _row(self, parent, label):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(r, text=label, font=(FONTS["fu"], FONTS["s"]),
                     text_color=COLORS["ts"]).pack(side="left")
        return r

    def _stat_card(self, parent, title, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_med"],
                            border_color=COLORS["border"], border_width=1, corner_radius=8)
        card.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        num = ctk.CTkLabel(card, text="0", font=(FONTS["f"], 22, "bold"), text_color=color)
        num.pack(expand=True)
        ctk.CTkLabel(card, text=title, font=(FONTS["fu"], FONTS["s"]),
                     text_color=COLORS["ts"]).pack(pady=(0, 8))

        def _set(value):
            num.configure(text=str(value))
        return _set

    def _sub_log(self, msg):
        self._logs_append(msg)

    def _sub_render(self):
        for w in self.sub_results_frame.winfo_children():
            w.destroy()
        q = self.sub_sv.get().lower() if hasattr(self, "sub_sv") else ""
        shown = 0
        for s in sorted(self.sub_all):
            if q and q not in s.lower():
                continue
            shown += 1
            if shown > 500:
                break
            row = ctk.CTkFrame(self.sub_results_frame, fg_color=COLORS["bg_dark"],
                               border_color=COLORS["border"], border_width=1,
                               corner_radius=6, height=36)
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            core = self.sub_core
            ip = core.resolved.get(s) if core else None
            ports = core.port_results.get(s, {}).get("ports", []) if core else []

            if ip:
                ctk.CTkLabel(row, text=" ATIVO ", font=(FONTS["f"], FONTS["s"], "bold"),
                             text_color="#fff", fg_color=COLORS["green"], corner_radius=4,
                             width=56).pack(side="left", padx=(8, 4), pady=5)
            else:
                ctk.CTkLabel(row, text=" N/D ", font=(FONTS["f"], FONTS["s"], "bold"),
                             text_color="#fff", fg_color=COLORS["se"], corner_radius=4,
                             width=56).pack(side="left", padx=(8, 4), pady=5)

            url_lbl = ctk.CTkLabel(
                row, text=s, font=(FONTS["f"], FONTS["n"]),
                text_color=COLORS["tp"], anchor="w", cursor="hand2"
            )
            url_lbl.pack(side="left", padx=4, fill="x", expand=True)
            url_lbl.bind("<Button-1>", lambda e, sub=s: webbrowser.open(f"https://{sub}"))

            for p in ports[:5]:
                ctk.CTkLabel(row, text=f" :{p} ", font=(FONTS["f"], FONTS["s"]),
                             text_color=COLORS["orange"]).pack(side="right", padx=2)

            if ip:
                ctk.CTkLabel(row, text=ip, font=(FONTS["f"], FONTS["n"]),
                             text_color=COLORS["cyan"], width=120).pack(side="right", padx=6)

        if shown == 0:
            ctk.CTkLabel(
                self.sub_results_frame,
                text="Nenhum resultado ainda.\nInforme o domínio e inicie a enumeração.",
                font=(FONTS["fu"], FONTS["m"]),
                text_color=COLORS["td"]
            ).pack(expand=True, pady=60)

    def _sub_start(self):
        if self.sub_running:
            return
        domain = self.sub_domain_entry.get().strip().lower()
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-.]*\.[a-zA-Z]{2,}$", domain):
            messagebox.showwarning("Aviso", f"Domínio inválido: {domain}")
            return
        engines = [n for n, v in self.sub_engine_vars.items() if v.get()]
        if not engines:
            messagebox.showwarning("Aviso", "Selecione pelo menos um motor!")
            return
        try:
            threads = max(1, int(self.sub_threads_v.get()))
        except ValueError:
            threads = 5
        vt_key = self.sub_vt_key_entry.get().strip() or None

        self.sub_running = True
        self.sub_start_btn.configure(state="disabled")
        self.sub_stop_btn.configure(state="normal")
        self.sub_progress.set(0)
        self.sub_progress.configure(mode="indeterminate")
        self.sub_progress.start()
        self.sub_status_lbl.configure(text=f"Enumerando {domain}...")

        self.sub_core = Sublist3rCore(
            domain=domain, engines=engines, threads=threads,
            callback=self._sub_log, resolve_dns=self.sub_resolve_v.get(),
            scan_ports=self.sub_portscan_v.get(), vt_api_key=vt_key)

        threading.Thread(target=self._sub_run, daemon=True).start()

    def _sub_run(self):
        try:
            results = self.sub_core.run()
            self.after(0, lambda: self._sub_done(results))
        except Exception as e:
            self.after(0, lambda: self._sub_done(None, error=str(e)))

    def _sub_done(self, results, error=None):
        self.sub_progress.stop()
        self.sub_progress.configure(mode="determinate")
        self.sub_progress.set(0 if error else 1.0)
        self.sub_start_btn.configure(state="normal")
        self.sub_stop_btn.configure(state="disabled")
        core = self.sub_core
        if core:
            self.sub_all = sorted(core.all_subdomains)
            self.sub_st_total(str(len(core.all_subdomains)))
            self.sub_st_resolved(str(len(core.resolved)))
            self.sub_st_ports(str(len(core.port_results)))
        self._sub_render()

        if error:
            self.sub_status_lbl.configure(text=f"Erro: {error}")
            self._sub_log(f"[!] Erro: {error}")
        else:
            n = len(results) if results is not None else 0
            self.sub_status_lbl.configure(text=f"Concluído — {n} subdomínios")
        self.sub_running = False

    def _sub_stop(self):
        if self.sub_core:
            self.sub_core.stop()
        self.sub_status_lbl.configure(text="⏹ Interrompido pelo usuário")
        self.sub_start_btn.configure(state="normal")
        self.sub_stop_btn.configure(state="disabled")
        self.sub_running = False

    def _sub_export_html(self):
        if not self.sub_core or not self.sub_core.all_subdomains:
            messagebox.showinfo("Aviso", "Nenhum resultado para exportar.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".html",
            filetypes=[("Relatório HTML", "*.html")])
        if not fp:
            return
        try:
            ReportHTML.subdomains_to_html(
                self.sub_core.domain,
                sorted(self.sub_core.all_subdomains),
                self.sub_core.resolved,
                self.sub_core.port_results, fp)
            self._sub_log(f"[*] Relatório HTML salvo em: {fp}")
            if messagebox.askyesno("Sucesso", f"Relatório HTML salvo em:\n{fp}\n\nAbrir no navegador?"):
                webbrowser.open(fp)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _sub_export(self):
        if not self.sub_core or not self.sub_core.all_subdomains:
            messagebox.showinfo("Aviso", "Nenhum resultado para exportar.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("JSON", "*.json"), ("CSV", "*.csv")])
        if not fp:
            return
        try:
            ext = os.path.splitext(fp)[1].lower()
            subs = sorted(self.sub_core.all_subdomains)
            if ext == ".json":
                data = {"domain": self.sub_core.domain, "timestamp": datetime.now().isoformat(),
                        "total": len(subs), "resolved": self.sub_core.resolved,
                        "port_results": self.sub_core.port_results, "subdomains": subs}
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif ext == ".csv":
                with open(fp, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["Subdomain", "IP", "Ports"])
                    for s in subs:
                        ip = self.sub_core.resolved.get(s, "")
                        pr = self.sub_core.port_results.get(s, {})
                        w.writerow([s, ip, ";".join(map(str, pr.get("ports", [])))])
            else:
                with open(fp, "w", encoding="utf-8") as f:
                    for s in subs:
                        f.write(s + "\n")
            self._sub_log(f"[*] Exportado para: {fp}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _sub_copy(self):
        if self.sub_all:
            self.clipboard_clear()
            self.clipboard_append("\n".join(self.sub_all))
            self.sub_status_lbl.configure(text="📋 Copiado!")

    def _sub_clear(self):
        self.sub_st_total("0"); self.sub_st_resolved("0"); self.sub_st_ports("0")
        self.sub_progress.set(0)
        self.sub_status_lbl.configure(text="Pronto")
        self.sub_all = []
        self._sub_render()

    # ========================================================
    # ABA HTTPX
    # ========================================================
    def _build_httpx_tab(self, tab):
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True)

        left = ctk.CTkFrame(main, fg_color=COLORS["bg_med"], border_color=COLORS["border"],
                            border_width=1, corner_radius=8, width=380)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        s = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                   scrollbar_button_color=COLORS["bg_light"],
                                   scrollbar_button_hover_color=COLORS["blue"])
        s.pack(fill="both", expand=True, padx=6, pady=6)

        self._sec(s, "🎯 ALVOS (um por linha)")
        self.hx_targets_txt = ctk.CTkTextbox(s, height=110, font=(FONTS["f"], FONTS["n"]),
                                             fg_color=COLORS["bg_in"], text_color=COLORS["tp"],
                                             border_color=COLORS["border"], border_width=1,
                                             corner_radius=6)
        self.hx_targets_txt.pack(fill="x", padx=4, pady=4)
        self.hx_targets_txt.insert("1.0", "example.com\ngoogle.com")
        
        ctk.CTkButton(s, text="📂 Carregar Arquivo", height=28,
                      font=(FONTS["fu"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._hx_load).pack(fill="x", padx=4, pady=4)

        self._sec(s, "⚙️ CONFIGURAÇÃO")
        self.hx_method_v = ctk.StringVar(value="GET")
        r = self._row(s, "Método HTTP")
        ctk.CTkOptionMenu(r, values=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                          variable=self.hx_method_v, width=110, height=26,
                          font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                          button_color=COLORS["bg_light"], button_hover_color=COLORS["blue"],
                          text_color=COLORS["tp"]).pack(side="right")

        self.hx_threads_v = ctk.StringVar(value=str(DEFAULT_THREADS))
        r = self._row(s, "Threads")
        ctk.CTkEntry(r, textvariable=self.hx_threads_v, width=70, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"]).pack(side="right")

        self.hx_timeout_v = ctk.StringVar(value="10")
        r = self._row(s, "Timeout (s)")
        ctk.CTkEntry(r, textvariable=self.hx_timeout_v, width=70, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"]).pack(side="right")

        self.hx_retries_v = ctk.StringVar(value="0")
        r = self._row(s, "Tentativas")
        ctk.CTkEntry(r, textvariable=self.hx_retries_v, width=70, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"]).pack(side="right")

        self.hx_follow_v = ctk.BooleanVar(value=True)
        r = self._row(s, "Seguir Redirects")
        ctk.CTkSwitch(r, text="", variable=self.hx_follow_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")

        self._sec(s, "🔌 PORTAS")
        self.hx_ports_v = ctk.StringVar(value="80,443")
        ctk.CTkEntry(s, textvariable=self.hx_ports_v, height=28,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="80,443,8080").pack(fill="x", padx=4, pady=4)

        self._sec(s, "🔍 PROBES")
        self.hx_probe_title_v = ctk.BooleanVar(value=True)
        r = self._row(s, "Título")
        ctk.CTkSwitch(r, text="", variable=self.hx_probe_title_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")
        self.hx_probe_tech_v = ctk.BooleanVar(value=True)
        r = self._row(s, "Tecnologias")
        ctk.CTkSwitch(r, text="", variable=self.hx_probe_tech_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")
        self.hx_probe_ip_v = ctk.BooleanVar(value=True)
        r = self._row(s, "IP")
        ctk.CTkSwitch(r, text="", variable=self.hx_probe_ip_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")
        self.hx_probe_wl_v = ctk.BooleanVar(value=True)
        r = self._row(s, "Words/Lines")
        ctk.CTkSwitch(r, text="", variable=self.hx_probe_wl_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")
        self.hx_probe_hash_v = ctk.BooleanVar(value=False)
        r = self._row(s, "Hash do corpo")
        ctk.CTkSwitch(r, text="", variable=self.hx_probe_hash_v, width=40,
                      progress_color=COLORS["green"], fg_color=COLORS["bg_light"]).pack(side="right")

        self._sec(s, "🔧 FILTROS")
        self.hx_match_v = ctk.StringVar(value="")
        r = self._row(s, "Match Codes")
        ctk.CTkEntry(r, textvariable=self.hx_match_v, width=110, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="200,301").pack(side="right")
        self.hx_filter_v = ctk.StringVar(value="")
        r = self._row(s, "Filter Codes")
        ctk.CTkEntry(r, textvariable=self.hx_filter_v, width=110, height=26,
                     font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="404,500").pack(side="right")       

        ctk.CTkFrame(s, fg_color="transparent", height=12).pack(fill="x")
        self.hx_start_btn = ctk.CTkButton(s, text="▶  INICIAR PROBE HTTP",
                                          font=(FONTS["fu"], FONTS["m"], "bold"),
                                          fg_color=COLORS["bp"], hover_color=COLORS["bph"],
                                          text_color="#fff", corner_radius=8, height=45,
                                          command=self._hx_start)
        self.hx_start_btn.pack(fill="x", padx=4, pady=6)
        self.hx_stop_btn = ctk.CTkButton(s, text="⏹  PARAR", state="disabled",
                                         font=(FONTS["fu"], FONTS["m"], "bold"),
                                         fg_color=COLORS["bd"], hover_color=COLORS["bdh"],
                                         text_color="#fff", corner_radius=8, height=38,
                                         command=self._hx_stop)
        self.hx_stop_btn.pack(fill="x", padx=4, pady=(0, 6))

        self.hx_progress = ctk.CTkProgressBar(s, progress_color=COLORS["blue"],
                                              fg_color=COLORS["bg_light"], height=6, corner_radius=3)
        self.hx_progress.pack(fill="x", padx=4, pady=(0, 4)); self.hx_progress.set(0)
        self.hx_status_lbl = ctk.CTkLabel(s, text="Pronto", font=(FONTS["f"], FONTS["s"]),
                                          text_color=COLORS["td"])
        self.hx_status_lbl.pack(fill="x", padx=4)

        # ---- Direita ----
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)

        stats = ctk.CTkFrame(right, fg_color="transparent", height=78)
        stats.pack(fill="x", pady=(0, 8)); stats.pack_propagate(False)
        self.hx_st_total = self._stat_card(stats, "Total", COLORS["blue"])
        self.hx_st_ok = self._stat_card(stats, "200 OK", COLORS["green"])
        self.hx_st_err = self._stat_card(stats, "Falhas", COLORS["red"])

        res_header = ctk.CTkFrame(right, fg_color="transparent")
        res_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(res_header, text="📋 Resultados HTTP", font=(FONTS["fu"], FONTS["n"], "bold"),
                     text_color=COLORS["tp"]).pack(side="left")
        btns = ctk.CTkFrame(res_header, fg_color="transparent")
        btns.pack(side="right")
        ctk.CTkButton(btns, text="💾 HTML", width=90, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._hx_export_html).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="💾 TXT/JSON/CSV", width=120, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._hx_export).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="📋 Copiar", width=80, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._hx_copy).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑 Limpar", width=80, height=26,
                      font=(FONTS["f"], FONTS["s"]), fg_color=COLORS["bs"],
                      hover_color=COLORS["bsh"], command=self._hx_clear).pack(side="left", padx=2)

        self.hx_sv = ctk.StringVar()
        self.hx_sv.trace_add("write", lambda *a: self._hx_render())
        ctk.CTkEntry(right, textvariable=self.hx_sv, height=30,
                     font=(FONTS["f"], FONTS["n"]), fg_color=COLORS["bg_in"],
                     text_color=COLORS["tp"], border_color=COLORS["border"],
                     placeholder_text="🔍 Filtrar por URL, título, servidor, tecnologia...").pack(fill="x", pady=(0, 6))

        self.hx_results_frame = ctk.CTkScrollableFrame(
            right, fg_color=COLORS["bg_med"], border_color=COLORS["border"],
            border_width=1, corner_radius=8,
            scrollbar_button_color=COLORS["bg_light"],
            scrollbar_button_hover_color=COLORS["blue"])
        self.hx_results_frame.pack(fill="both", expand=True)
        self._hx_render()

    def _hx_log(self, msg):
        self._logs_append(msg)

    def _hx_progress(self, done, total):
        def _ui():
            if total > 0:
                self.hx_progress.set(done / total)
        self.after(0, _ui)

    def _hx_render(self):
        for w in self.hx_results_frame.winfo_children():
            w.destroy()

        q = self.hx_sv.get().lower() if hasattr(self, "hx_sv") else ""
        shown = 0

        for r in sorted(self.hx_all_results, key=lambda x: (x.failed, x.status_code)):
            hay = (
                f"{r.url} {r.title} {r.web_server} "
                f"{' '.join(r.technologies)} {r.status_code}"
            ).lower()

            if q and q not in hay:
                continue

            shown += 1

            if shown > 500:
                break

            row = ctk.CTkFrame(
                self.hx_results_frame, fg_color=COLORS["bg_dark"],
                border_color=COLORS["border"], border_width=1,
                corner_radius=6, height=38
            )
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            st = "ERR" if r.failed else str(r.status_code)
            clr = COLORS["se"] if r.failed else get_status_color(r.status_code)

            ctk.CTkLabel(
                row, text=f" {st} ", font=(FONTS["f"], FONTS["s"], "bold"),
                text_color="#fff", fg_color=clr, corner_radius=4, width=50
            ).pack(side="left", padx=(8, 4), pady=6)

            url_lbl = ctk.CTkLabel(
                row, text=r.url[:70], font=(FONTS["f"], FONTS["n"]),
                text_color=COLORS["blue"], anchor="w", cursor="hand2"
            )
            url_lbl.pack(side="left", padx=4, fill="x", expand=True)
            url_lbl.bind("<Button-1>", lambda e, u=r.url: webbrowser.open(u))

            if r.title:
                ctk.CTkLabel(row, text=r.title[:30], font=(FONTS["f"], FONTS["s"]),
                             text_color=COLORS["tp"]).pack(side="right", padx=6)

            if r.web_server:
                ctk.CTkLabel(row, text=r.web_server[:20], font=(FONTS["f"], FONTS["s"]),
                             text_color=COLORS["purple"]).pack(side="right", padx=6)

            if r.technologies:
                ctk.CTkLabel(row, text=",".join(r.technologies[:3]),
                             font=(FONTS["f"], FONTS["s"]),
                             text_color=COLORS["orange"]).pack(side="right", padx=6)

        if shown == 0:
            ctk.CTkLabel(
                self.hx_results_frame,
                text="Nenhum resultado ainda.\nInforme os alvos e inicie o probe HTTP.",
                font=(FONTS["fu"], FONTS["m"]),
                text_color=COLORS["td"]
            ).pack(expand=True, pady=60)

    def _hx_load(self):
        fp = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.hx_targets_txt.delete("1.0", "end")
            self.hx_targets_txt.insert("1.0", content)
            self._hx_log(f"[*] Arquivo carregado: {fp}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _hx_start(self):
        if self.hx_scanning:
            return
        raw = self.hx_targets_txt.get("1.0", "end").strip()
        targets = [t.strip() for t in raw.splitlines() if t.strip() and not t.strip().startswith("#")]
        if not targets:
            messagebox.showwarning("Aviso", "Informe pelo menos um alvo!")
            return
        try:
            threads = max(1, int(self.hx_threads_v.get()))
        except ValueError:
            threads = DEFAULT_THREADS
        try:
            timeout = max(1, int(self.hx_timeout_v.get()))
        except ValueError:
            timeout = 10
        try:
            retries = max(0, int(self.hx_retries_v.get()))
        except ValueError:
            retries = 0
        try:
            ports = [int(p) for p in self.hx_ports_v.get().split(",") if p.strip().isdigit()]
        except ValueError:
            ports = [80, 443]
        if not ports:
            ports = [80, 443]

        def _parse_codes(raw_codes):
            codes = []
            for part in raw_codes.replace(";", ",").split(","):
                part = part.strip()
                if not part:
                    continue
                if part.isdigit():
                    codes.append(int(part))
                elif part.endswith("xx") and part[:-2].isdigit():
                    base = int(part[:-2])
                    codes.extend(range(base * 100, base * 100 + 100))
            return codes

        match_codes = _parse_codes(self.hx_match_v.get())
        filter_codes = _parse_codes(self.hx_filter_v.get())
        if match_codes and filter_codes:
            filter_codes = [c for c in filter_codes if c not in match_codes]

        config = ScanConfig(
            method=self.hx_method_v.get(), threads=threads, timeout=timeout, retries=retries,
            follow_redirects=self.hx_follow_v.get(), ports=ports,
            probe_title=self.hx_probe_title_v.get(), probe_tech=self.hx_probe_tech_v.get(),
            probe_ip=self.hx_probe_ip_v.get(), probe_wl=self.hx_probe_wl_v.get(),
            probe_hash=self.hx_probe_hash_v.get(),
            match_codes=match_codes, filter_codes=filter_codes)

        self.hx_scanning = True
        self.hx_start_btn.configure(state="disabled")
        self.hx_stop_btn.configure(state="normal")
        self.hx_progress.set(0)
        filtro_txt = ""
        if match_codes:
            filtro_txt += f" | match: {match_codes}"
        if filter_codes:
            filtro_txt += f" | filter: {filter_codes}"
        self.hx_status_lbl.configure(text=f"Probe em {len(targets)} alvos{filtro_txt}")

        self.hx_scanner = Scanner(targets, config, callback=self._hx_log, progress=self._hx_progress)
        threading.Thread(target=self._hx_run, daemon=True).start()

    def _hx_run(self):
        try:
            results = self.hx_scanner.run()
            self.after(0, lambda: self._hx_done(results))
        except Exception as e:
            self.after(0, lambda: self._hx_done(None, error=str(e)))

    def _hx_done(self, results, error=None):
        self.hx_start_btn.configure(state="normal")
        self.hx_stop_btn.configure(state="disabled")
        if results is not None:
            self.hx_all_results = list(results)
        self.hx_progress.set(0 if error else 1.0)
        self.hx_st_total(str(len(self.hx_all_results)))
        self.hx_st_ok(str(sum(1 for r in self.hx_all_results if not r.failed and 200 <= r.status_code < 300)))
        self.hx_st_err(str(sum(1 for r in self.hx_all_results if r.failed)))
        self._hx_render()
        if error:
            self.hx_status_lbl.configure(text=f"Erro: {error}")
            self._hx_log(f"[!] Erro: {error}")
        else:
            self.hx_status_lbl.configure(text=f"Concluído — {len(self.hx_all_results)} resultados")
        self.hx_scanning = False

    def _hx_stop(self):
        if self.hx_scanner:
            self.hx_scanner.stop()
        self.hx_status_lbl.configure(text="⏹ Interrompido pelo usuário")
        self.hx_start_btn.configure(state="normal")
        self.hx_stop_btn.configure(state="disabled")
        self.hx_scanning = False

    def _hx_export_html(self):
        if not self.hx_all_results:
            messagebox.showinfo("Aviso", "Nenhum resultado para exportar.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".html",
            filetypes=[("Relatório HTML", "*.html")])
        if not fp:
            return
        try:
            ReportHTML.httpx_to_html(self.hx_all_results, fp)
            self._hx_log(f"[*] Relatório HTML salvo em: {fp}")
            if messagebox.askyesno("Sucesso", f"Relatório HTML salvo em:\n{fp}\n\nAbrir no navegador?"):
                webbrowser.open(fp)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _hx_export(self):
        if not self.hx_all_results:
            messagebox.showinfo("Aviso", "Nenhum resultado para exportar.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("JSON", "*.json"), ("CSV", "*.csv"), ("Oneliner", "*.oneliner")])
        if not fp:
            return
        try:
            HTTPXExporter.export(self.hx_all_results, fp)
            self._hx_log(f"[*] Exportado para: {fp}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _hx_copy(self):
        if self.hx_all_results:
            self.clipboard_clear()
            self.clipboard_append("\n".join(r.to_oneliner() for r in self.hx_all_results))
            self.hx_status_lbl.configure(text="📋 Copiado!")

    def _hx_clear(self):
        self.hx_st_total("0"); self.hx_st_ok("0"); self.hx_st_err("0")
        self.hx_progress.set(0)
        self.hx_status_lbl.configure(text="Pronto")
        self.hx_all_results = []
        self._hx_render()


if __name__ == "__main__":
    app = ReconSuite()
    app.mainloop()
