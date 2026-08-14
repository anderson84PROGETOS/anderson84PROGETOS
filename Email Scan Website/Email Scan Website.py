#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhishScan GUI — Tema Hacker (verde/preto)
==========================================
Escaneia .txt / .html / .eml e URL ao vivo (http/https):
extrai URL e e-mails, detecta ofuscação, resolve DNS,
analisa cabeçalhos .eml e gera relatório exportável ou enviável por SMTP.

Uso:  python3 Email Scan Website
Requisitos: Python 3.8+ (apenas biblioteca padrão).
"""

import re
import os
import socket
import threading
import smtplib
import ssl as ssl_mod
import html as html_mod
import webbrowser
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from datetime import datetime
from urllib.parse import urlparse, unquote, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import platform

# ---------------------------------------------------------------------------
# CORES DO TEMA HACKER
# ---------------------------------------------------------------------------
BG       = '#000000'      # fundo preto
FG       = '#00ff00'      # verde neón
FG_DIM   = '#33cc33'      # verde escurecido
FG_LIGHT = '#66ff66'      # verde claro (scrollbars)
SELECT   = '#003300'      # seleção verde escuro
BORDER   = '#006600'      # bordas verdes
ORANGE   = '#ff8c00'      # cor de abóbora (não ofuscado / risco médio)
RED      = '#ff4444'      # vermelho (risco alto)

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO / INDICADORES
# ---------------------------------------------------------------------------

URL_RE = re.compile(r'https?://[^\s<>"\')\]\}]+', re.IGNORECASE)
ATTR_RE = re.compile(
    r'(?:href|src|action|data-url|cite|formaction)\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE)
IP_DOTTED_RE = re.compile(r'^(\d{1,3})(?:\.(\d{1,3})){3}$')

EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
OBF_EMAIL_RE = re.compile(
    r'\b([A-Za-z0-9._%+\-]+)\s*(?:\[|\(|\{)?\s*(?:at|@)\s*(?:\[|\(|\{)?\s*'
    r'([A-Za-z0-9.\-]+?)\s*(?:\[|\(|\{)?\s*(?:dot|\.)\s*(?:\[|\(|\{)?\s*'
    r'([A-Za-z]{2,})\b', re.IGNORECASE)

LEGIT_EMAIL_DOMAINS = [
    'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com',
    'aol.com', 'protonmail.com', 'live.com', 'msn.com', 'uol.com.br',
    'bol.com.br', 'terra.com.br', 'ig.com.br', 'globo.com', 'zipmail.com.br',
]

URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'is.gd', 'buff.ly', 'ow.ly',
    'rebrand.ly', 'cutt.ly', 'shorturl.at', 'adf.ly', 'shorte.st', 'bc.vc',
    'soo.gd', 's2r.co', 'db.tt', 'lnkd.in', 'rb.gy', 'qr.ae', 'tiny.cc',
    'bl.ink', 'v.gd', 'youtu.be',
}

PHISH_KEYWORDS = [
    'login', 'signin', 'sign-in', 'logon', 'verify', 'verification', 'confirm',
    'account', 'update', 'secure', 'security', 'banking', 'banco', 'caixa',
    'itau', 'bradesco', 'santander', 'nubank', 'picpay', 'mercado', 'paypal',
    'apple', 'icloud', 'microsoft', 'office365', 'outlook', 'google', 'gmail',
    'dropbox', 'facebook', 'instagram', 'whatsapp', 'netflix', 'streaming',
    'boleto', 'fatura', 'pendente', 'bloquead', 'suspend', 'password', 'senha',
    'credential', 'wallet', 'carteira', 'pix', 'recuperar', 'restaurar',
    'alert', 'notice', 'invoice', 'documento', 'assinatura', 'cupom', 'premio',
    'promocao', 'ganhador',
]

OBFUSCATION_PATTERNS = [
    (r'\beval\s*\(', 'eval() — execução dinâmica de código'),
    (r'\bunescape\s*\(', 'unescape() — ofuscação'),
    (r'\bfromCharCode\s*\(', 'String.fromCharCode — ofuscação'),
    (r'\b(atob|btoa)\s*\(', 'Base64 dentro de JavaScript'),
    (r'\\x[0-9a-fA-F]{2}', 'código hexadecimal em string'),
    (r'&#x?[0-9a-fA-F]+;', 'entidade HTML/hexadecimal'),
    (r'document\.(write|location)', 'manipulação de DOM/localização'),
    (r'window\.location\s*=', 'redirecionamento via JavaScript'),
    (r'<meta[^>]+refresh', 'meta refresh — redirecionamento automático'),
]

HEADER_CHECKS = ['Received-Spf', 'Dkim-Signature', 'Authentication-Results',
                 'X-Spam-Status']

DEFAULT_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

# ---------------------------------------------------------------------------
# MOTOR DE ANÁLISE
# ---------------------------------------------------------------------------

def norm_host(host):
    return (host or '').strip().rstrip('.').lower()


def decode_numeric_ip(host):
    """Converte IPs em notação decimal/hex/octal para formato pontilhado."""
    h = host.lower()
    if IP_DOTTED_RE.match(h):
        parts = [int(p) for p in h.split('.')]
        if all(0 <= p <= 255 for p in parts):
            return h
        return None
    try:
        if h.startswith('0x'):
            val = int(h, 16)
        elif h.startswith('0') and len(h) > 1:
            val = int(h, 8)
        else:
            val = int(h)
        if 0 <= val <= 0xffffffff:
            return f'{(val >> 24) & 255}.{(val >> 16) & 255}.{(val >> 8) & 255}.{val & 255}'
    except ValueError:
        pass
    return None


def levenshtein(a, b):
    """Distância de edição — usada para detectar typosquatting."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def flag_suspicious_domain(domain):
    """Retorna motivo de suspeita do domínio do e-mail, ou string vazia."""
    d = domain.lower()
    if d in LEGIT_EMAIL_DOMAINS or any(d.endswith('.' + L) for L in LEGIT_EMAIL_DOMAINS):
        return ''
    if any(k in d for k in ('verify', 'account', 'login', 'secure',
                            'update', 'confirm', 'billing', 'bank')):
        return 'domínio com palavra suspeita'
    for legit in LEGIT_EMAIL_DOMAINS:
        if levenshtein(d, legit) <= 2:
            return f'possível typosquatting de {legit}'
    return ''


def extract_emails(content):
    """Extrai TODOS os e-mails do conteúdo (inclusive ofuscados)."""
    text = html_mod.unescape(content)
    found, order = {}, []

    def add(email, start, end, obf=False):
        email = email.strip('.,;:<>[](){}"\'')
        if len(email) > 254 or not re.match(
                r'^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$', email):
            return
        # rejeita falsos positivos de JS/React/minificado
        low = email.lower()
        if any(x in low for x in ('.react', '.js', '.css', '.map', 'webpack',
                                   'node_modules', 'cdninstagram', 'fbcdn')):
            return
        if re.search(r'@[a-z0-9_\-]+\.(react|js|css|ts|jsx|tsx|vue)\b', low):
            return
        # TLD precisa ter cara de domínio real (não "react", "js", etc.)
        tld = low.rsplit('.', 1)[-1]
        if tld in ('react', 'js', 'css', 'ts', 'jsx', 'tsx', 'vue', 'mjs', 'cjs'):
            return
        key = low
        if key not in found:
            found[key] = {'email': email, 'count': 0, 'context': '',
                          'obfuscated': obf}
            order.append(key)
        found[key]['count'] += 1
        if not found[key]['context']:
            s = max(0, start - 60)
            e = min(len(text), end + 60)
            found[key]['context'] = ' '.join(text[s:e].split())

    for m in EMAIL_RE.finditer(text):
        add(m.group(0), m.start(), m.end())
    for m in OBF_EMAIL_RE.finditer(text):
        add(f"{m.group(1)}@{m.group(2)}.{m.group(3)}",
            m.start(), m.end(), obf=True)

    emails = [found[k] for k in order]
    for em in emails:
        dom = em['email'].split('@', 1)[1].lower()
        em['suspicious'] = flag_suspicious_domain(dom)
    return emails


def analyze_url(raw_url):
    """Analisa uma URL e devolve dict com pontuação de risco."""
    url = raw_url.strip()
    url = re.sub(r'[.,;:!?)\]}]+$', '', url)
    if url.startswith('//'):
        url = 'http:' + url

    parsed = urlparse(url)
    scheme = (parsed.scheme or '').lower()
    host = norm_host(parsed.hostname or '')
    reasons, score = [], 0

    if scheme in ('javascript', 'vbscript', 'data', 'file'):
        score += 50
        reasons.append(f'Esquema perigoso: {scheme}:')

    if scheme == 'http':
        score += 10
        reasons.append('Sem TLS (http://)')

    ip = decode_numeric_ip(host)
    if ip:
        score += 40
        reasons.append(f'Host é IP (ou codificado): {ip}')
    elif host:
        after = url.split('://', 1)[1] if '://' in url else url
        if '@' in after[:64]:
            score += 15
            reasons.append('Usuário/senha no URL (@)')
        if re.search(r'xn--', host, re.I):
            score += 10
            reasons.append('Domínio punycode (xn--) — possível homógrafo')
        subs = host.split('.')
        if len(subs) > 3:
            score += 5
            reasons.append('Muitos subdomínios')
        base = '.'.join(subs[-2:]) if len(subs) >= 2 else host
        if base in URL_SHORTENERS:
            score += 15
            reasons.append(f'Encurtador de URL: {base}')
        haystack = (host + ' ' + unquote(parsed.path).lower())
        kw = [w for w in PHISH_KEYWORDS if w in haystack]
        if kw:
            score += min(20, len(kw) * 5)
            reasons.append('Palavras suspeitas: ' + ', '.join(kw[:6]))

    try:
        if parsed.port and parsed.port not in (80, 443):
            score += 5
            reasons.append(f'Porta não padrão: {parsed.port}')
    except ValueError:
        reasons.append('Porta inválida no URL')

    risk = 'alto' if score >= 60 else ('medio' if score >= 30 else 'baixo')
    return {'url': url, 'host': host or '(sem host)', 'ip': ip or '',
            'scheme': scheme or '(relativo)', 'score': score, 'risk': risk,
            'reasons': '; '.join(reasons) or 'Sem indicadores claros'}


def extract_urls(content, is_html):
    """Extrai URLs de texto ou HTML, com contagem de ocorrências."""
    found = {}
    if is_html:
        for m in ATTR_RE.finditer(content):
            u = html_mod.unescape(m.group(1)).strip()
            if u and not u.startswith(('#', '/', 'mailto:', 'tel:', '{')):
                found[u] = found.get(u, 0) + 1
    for m in URL_RE.finditer(content):
        found[m.group(0)] = found.get(m.group(0), 0) + 1
    return found


def analyze_content(content, is_html):
    """Detecta padrões de ofuscação / elementos suspeitos no conteúdo."""
    findings = []
    for pattern, label in OBFUSCATION_PATTERNS:
        n = len(re.findall(pattern, content, re.IGNORECASE))
        if n:
            findings.append(f'{label}: {n} ocorrência')
    if is_html:
        if re.search(r'<form', content, re.I):
            findings.append('Formulário presente — coleta de dados')
        if re.search(r'type\s*=\s*["\']?password', content, re.I):
            findings.append('Campo de senha presente')
        if re.search(r'<script', content, re.I):
            findings.append('JavaScript embutido/externo')
        hidden = re.findall(
            r'<iframe[^>]+(?:height|width)\s*=\s*["\']?[01]', content, re.I)
        if hidden:
            findings.append(f'iframe oculto (0/1 px): {len(hidden)}')
    return findings


def analyze_eml(data):
    """Analisa um e-mail .eml e devolve cabeçalhos, anexos e corpos."""
    msg = BytesParser(policy=policy.default).parsebytes(data)
    info = {
        'from': str(msg.get('From', '(vazio)')),
        'to': str(msg.get('To', '(vazio)')),
        'subject': str(msg.get('Subject', '(vazio)')),
        'date': str(msg.get('Date', '(vazio)')),
        'reply_to': str(msg.get('Reply-To', '(vazio)')),
        'return_path': str(msg.get('Return-Path', '(vazio)')),
        'auth': [], 'attachments': [], 'findings': [],
        'body_plain': '', 'body_html': '',
    }
    for h in HEADER_CHECKS:
        v = str(msg.get(h, '')).strip()
        if v:
            info['auth'].append(f'{h}: {v[:200]}')
    if not info['auth']:
        info['findings'].append(
            'Nenhum cabeçalho de autenticação (SPF/DKIM/DMARC) — risco de spoofing')

    from_addr = parseaddr(info['from'])[1].lower()
    reply_addr = parseaddr(info['reply_to'])[1].lower()
    if reply_addr and from_addr and reply_addr != from_addr:
        info['findings'].append(
            f'Reply-To ({reply_addr}) diferente do remetente ({from_addr}) — '
            'possível golpe de resposta')

    for part in msg.walk():
        ctype = part.get_content_type()
        fname = part.get_filename()
        if part.is_attachment() or fname:
            payload = part.get_payload(decode=True) or b''
            info['attachments'].append(
                f'{fname or "(sem nome)"} [{ctype}] {len(payload)} bytes')
        elif ctype == 'text/plain':
            info['body_plain'] = part.get_content() or ''
        elif ctype == 'text/html':
            info['body_html'] = part.get_content() or ''
    if not info['body_html']:
        info['findings'].append('Mensagem sem versão HTML (apenas texto)')
    return info


def looks_like_email(text):
    head = text.lstrip()[:400]
    return bool(re.match(
        r'^(?:From|To|Subject|Return-Path|Received|Date|Message-ID|Reply-To):',
        head, re.M))


def fetch_url(url, user_agent, timeout=20):
    """Baixa o conteúdo de uma URL http/https com User-Agent customizado."""
    url = url.strip()
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url
    req = Request(url, headers={
        'User-Agent': user_agent or DEFAULT_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    })
    ctx = ssl_mod.create_default_context()
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        raw = resp.read()
        charset = 'utf-8'
        ct = resp.headers.get_content_charset()
        if ct:
            charset = ct
        text = raw.decode(charset, errors='replace')
        final_url = resp.geturl()
        status = resp.status
    return text, final_url, status


# ---------------------------------------------------------------------------
# TEMA HACKER (ttk + tk) — scrollbars em verde claro
# ---------------------------------------------------------------------------

def apply_hacker_theme(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    style.configure('.', background=BG, foreground=FG,
                    fieldbackground=BG, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, troughcolor=BG,
                    selectbackground=SELECT, selectforeground=FG)

    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=FG)
    style.configure('TLabelframe', background=BG, bordercolor=BORDER,
                    foreground=FG)
    style.configure('TLabelframe.Label', background=BG, foreground=FG)

    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', background=BG, foreground=FG_DIM,
                    padding=(14, 7), borderwidth=0)
    style.map('TNotebook.Tab',
              background=[('selected', SELECT)],
              foreground=[('selected', FG)])

    style.configure('TButton', background=BG, foreground=FG,
                    bordercolor=BORDER, padding=6, focuscolor=BG)
    style.map('TButton',
              background=[('active', SELECT), ('pressed', SELECT)],
              foreground=[('active', FG)])

    style.configure('TEntry', fieldbackground=BG, foreground=FG,
                    insertcolor=FG, bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER)
    style.map('TEntry', bordercolor=[('focus', FG)])

    style.configure('TCheckbutton', background=BG, foreground=FG)
    style.map('TCheckbutton', background=[('active', BG)],
              indicatorcolor=[('selected', FG)])

    style.configure('Treeview', background=BG, fieldbackground=BG,
                    foreground=FG, bordercolor=BORDER, relief='flat',
                    rowheight=22)
    style.map('Treeview',
              background=[('selected', SELECT)],
              foreground=[('selected', FG)])
    style.configure('Treeview.Heading', background='#001500',
                    foreground=FG, relief='flat', bordercolor=BORDER,
                    padding=4)
    style.map('Treeview.Heading', background=[('active', SELECT)])

    # Scrollbars — verde claro
    style.configure('Vertical.TScrollbar',
                    background=FG_LIGHT, troughcolor='#001a00',
                    bordercolor=BORDER, arrowcolor=BG,
                    lightcolor=FG_LIGHT, darkcolor=FG_DIM, relief='flat')
    style.map('Vertical.TScrollbar',
              background=[('active', FG), ('pressed', FG_DIM)])
    style.configure('Horizontal.TScrollbar',
                    background=FG_LIGHT, troughcolor='#001a00',
                    bordercolor=BORDER, arrowcolor=BG,
                    lightcolor=FG_LIGHT, darkcolor=FG_DIM, relief='flat')
    style.map('Horizontal.TScrollbar',
              background=[('active', FG), ('pressed', FG_DIM)])

    style.configure('Status.TLabel', background=BG, foreground=FG,
                    relief='sunken', padding=4)
    style.configure('Verdict.TLabel', background=BG, foreground=FG,
                    font=('Segoe UI', 11, 'bold'))

    # Barra de progresso tema hacker
    style.configure(
        'Hacker.Horizontal.TProgressbar',
        troughcolor='#001a00',
        background=FG,
        bordercolor=BORDER,
        lightcolor=FG_LIGHT,
        darkcolor=FG_DIM,
    )
    return style

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ScrollableForm(ttk.Frame):
    """Frame com scrollbar vertical à direita (para a aba de envio)."""

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.sb = ttk.Scrollbar(self, orient='vertical',
                                command=self.canvas.yview,
                                style='Vertical.TScrollbar')
        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor='nw')
        self.inner.bind('<Configure>',
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',
                         lambda e: self.canvas.itemconfigure(self._win,
                                                             width=e.width))
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.sb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<Enter>', lambda e: self.canvas.bind_all(
            '<MouseWheel>', self._wheel))
        self.canvas.bind('<Leave>', lambda e: self.canvas.unbind_all(
            '<MouseWheel>'))

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), 'units')

class PhishScanApp:
    def __init__(self, root):
        self.root = root
        self.root.title('🔎 Email Scan Website🔍')
        self.root.geometry('1150x720')

        try:
            if platform.system() == 'Windows':
                self.root.state('zoomed')
            elif platform.system() == 'Linux':
                try:
                    self.root.attributes('-zoomed', True)
                except Exception:
                    largura = self.root.winfo_screenwidth()
                    altura = self.root.winfo_screenheight()
                    self.root.geometry(f'{largura}x{altura}+0+0')
        except Exception:
            pass

        apply_hacker_theme(root)
        self.filepath = None
        self.results = None
        self._dns_cache = {}
        self.filter_urls = None
        self.filter_emails = None
        self.url_filter_buttons = {}
        self.email_filter_buttons = {}
        self.user_agents = [DEFAULT_UA]
        self.selected_ua = DEFAULT_UA
        self.scraper_urls = []          # lista completa de URLs do scraper
        self.scraper_base_url = ''      # URL base usada no scrape
        self._raw_content = None        # conteúdo bruto para escanear (evita travar Text)
        self._open_busy = False
        self._scan_busy = False
        # Limite: acima disso não formata/destaca HTML inteiro na aba Conteúdo
        self._CONTENT_UI_LIMIT = 180_000

        style = ttk.Style()

        style.configure(
            'Abrir.TButton',
            background='#3498DB',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Colar.TButton',
            background='#9B59B6',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Scan.TButton',
            background='#2ECC71',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Limpar.TButton',
            background='#E74C3C',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Txt.TButton',
            background='#F39C12',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Html.TButton',
            background='#E67E22',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'Ambos.TButton',
            background='#1ABC9C',
            foreground='black',
            font=('Arial', 9, 'bold')
        )

        style.configure(
            'TudoHtml.TButton',
            background='#34495E',
            foreground="#F08808",
            font=('Arial', 9, 'bold')
        )

        self._build_menu()
        self._build_toolbar()
        self._build_notebook()
        self.status = tk.StringVar(
            value='Pronto. Abra um arquivo, cole conteúdo ou digite uma URL.')
        ttk.Label(root, textvariable=self.status,
                  style='Status.TLabel').pack(side='bottom', fill='x')

        # tenta carregar useragent.txt da pasta do script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_ua_path = os.path.join(script_dir, 'useragent.txt')
        if os.path.isfile(default_ua_path):
            self._load_ua_file(default_ua_path, silent=True)

    # ----------------------------- helpers de UI ---------------------------
    def _make_sb(self, parent, command):
        return ttk.Scrollbar(parent, orient='vertical', command=command,
                             style='Vertical.TScrollbar')

    def _make_text(self, parent, wheel=True):
        txt = tk.Text(parent, wrap='word', bg=BG, fg=FG,
                      insertbackground=FG, selectbackground=SELECT,
                      selectforeground=FG, relief='flat', bd=0,
                      highlightthickness=0, font=('Consolas', 10),
                      padx=8, pady=6)
        sb = self._make_sb(parent, txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        txt.pack(fill='both', expand=True)
        if wheel:
            txt.bind('<Enter>', lambda e: txt.bind_all(
                '<MouseWheel>', lambda ev: txt.yview_scroll(
                    int(-ev.delta / 120), 'units')))
            txt.bind('<Leave>', lambda e: txt.unbind_all('<MouseWheel>'))
        return txt

    def _make_tree(self, parent, cols, heads, widths, wheel=True, stretch=False):
        """Treeview com scrollbars via grid. stretch=False ativa a barra horizontal."""
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True)

        tree = ttk.Treeview(container, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=heads[c])
            tree.column(c, width=widths[c], minwidth=40, anchor='w',
                        stretch=stretch)

        ys = ttk.Scrollbar(container, orient='vertical', command=tree.yview,
                           style='Vertical.TScrollbar')
        xs = ttk.Scrollbar(container, orient='horizontal', command=tree.xview,
                           style='Horizontal.TScrollbar')
        tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)

        tree.grid(row=0, column=0, sticky='nsew')
        ys.grid(row=0, column=1, sticky='ns')
        xs.grid(row=1, column=0, sticky='ew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        if wheel:
            def _on_mousewheel(ev):
                if ev.state & 0x1:  # Shift pressionado
                    tree.xview_scroll(int(-ev.delta / 120), 'units')
                else:
                    tree.yview_scroll(int(-ev.delta / 120), 'units')
            tree.bind('<Enter>', lambda e: tree.bind_all('<MouseWheel>', _on_mousewheel))
            tree.bind('<Leave>', lambda e: tree.unbind_all('<MouseWheel>'))
        return tree

    def _legend_button(self, parent, text, color, command):
        """Botão colorido da legenda (com filtro ao clicar)."""
        b = tk.Button(parent, text=text, bg=color, fg='#000000',
                      activebackground=color, activeforeground='#000000',
                      relief='raised', bd=1, padx=8, cursor='hand2',
                      font=('Segoe UI', 9, 'bold'), command=command)
        b.pack(side='left', padx=2)
        return b

    # ----------------------------- construção -----------------------------
    def _build_menu(self):
        bar = tk.Menu(self.root, bg=BG, fg=FG, activebackground=SELECT,
                      activeforeground=FG, bd=0)
        m_arq = tk.Menu(bar, tearoff=0, bg=BG, fg=FG,
                        activebackground=SELECT, activeforeground=FG, bd=0)
        m_arq.add_command(label='Abrir arquivo...', accelerator='Ctrl+O',
                          command=self.open_file)
        m_arq.add_command(label='Colar da área de transferência',
                          command=self.paste_clipboard)
        m_arq.add_separator()
        m_arq.add_command(label='Exportar relatório (.txt)...',
                          command=lambda: self.export_report('txt'))
        m_arq.add_command(label='Exportar relatório (.html)...',
                          command=lambda: self.export_report('html'))
        m_arq.add_command(label='Exportar ambos (.txt + .html)...',
                          command=self.export_both)
        m_arq.add_command(label='Exportar TUDO em HTML (completo)...',
                          command=self.export_full_html)
        m_arq.add_separator()
        m_arq.add_command(label='Sair', command=self.root.quit)
        bar.add_cascade(label='Arquivo', menu=m_arq)

        m_ajuda = tk.Menu(bar, tearoff=0, bg=BG, fg=FG,
                          activebackground=SELECT, activeforeground=FG, bd=0)
        m_ajuda.add_command(label='Sobre', command=self.show_about)
        bar.add_cascade(label='Ajuda', menu=m_ajuda)
        self.root.config(menu=bar)
        self.root.bind('<Control-o>', lambda e: self.open_file())

    def _build_toolbar(self):
        fr = ttk.Frame(self.root, padding=(8, 6))
        fr.pack(fill='x')

        ttk.Button(
            fr,
            text='🚪  Abrir arquivo',
            command=self.open_file,
            style='Abrir.TButton'
        ).pack(side='left')

        ttk.Button(
            fr,
            text='Colar conteúdo',
            command=self.paste_clipboard,
            style='Colar.TButton'
        ).pack(side='left', padx=5)

        ttk.Button(
            fr,
            text='🔎  Escanear',
            command=self.start_scan,
            style='Scan.TButton'
        ).pack(side='left')

        ttk.Button(
            fr,
            text='🧹 Limpar',
            command=self.clear_all,
            style='Limpar.TButton'
        ).pack(side='left', padx=6)

        ttk.Button(
            fr,
            text='Salvar .txt',
            command=lambda: self.export_report('txt'),
            style='Txt.TButton'
        ).pack(side='left', padx=5)

        ttk.Button(
            fr,
            text='Salvar .html',
            command=lambda: self.export_report('html'),
            style='Html.TButton'
        ).pack(side='left', padx=5)

        ttk.Button(
            fr,
            text='Salvar ambos',
            command=self.export_both,
            style='Ambos.TButton'
        ).pack(side='left', padx=6)

        ttk.Button(
            fr,
            text='Salvar TUDO HTML',
            command=self.export_full_html,
            style='TudoHtml.TButton'
        ).pack(side='left', padx=5)
        
        self.file_label = ttk.Label(fr, text='Nenhum arquivo carregado')
        self.file_label.pack(side='left', padx=10)

        self.verdict = ttk.Label(fr, text='Risco geral: ',
                                 style='Verdict.TLabel')
        self.verdict.pack(side='left', padx=(10, 10))

        # barra de progresso global (abrir arquivo / escanear)
        fr_prog = ttk.Frame(self.root, padding=(8, 2))
        fr_prog.pack(fill='x')
        self.main_progress = ttk.Progressbar(
            fr_prog, mode='determinate', maximum=100, length=420,
            style='Hacker.Horizontal.TProgressbar',
        )
        self.main_progress.pack(side='left', padx=(0, 8))
        self.main_prog_label = ttk.Label(fr_prog, text='Pronto')
        self.main_prog_label.pack(side='left')

        # barra de URL ao vivo
        fr2 = ttk.Frame(self.root, padding=(8, 2))
        fr2.pack(fill='x')
        ttk.Label(fr2, text='URL ao vivo:').pack(side='left')
        self.url_var = tk.StringVar()
        ent = ttk.Entry(fr2, textvariable=self.url_var, width=70)
        ent.pack(side='left', padx=6, fill='x', expand=True)
        ttk.Button(fr2, text='[ Buscar e escanear ]',
                   command=self.fetch_and_scan).pack(side='left')

    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=8, pady=6)

        # ---------- aba conteúdo ----------
        fr_content = ttk.Frame(self.nb)
        self.txt_content = self._make_text(fr_content)
        self.nb.add(fr_content, text=' Conteúdo ')

        # ---------- aba links ----------
        fr_links = ttk.Frame(self.nb)
        bfr = ttk.Frame(fr_links)
        bfr.pack(side='bottom', fill='x', pady=4)
        ttk.Button(bfr, text='[ Copiar URL ]',
                   command=self.copy_url).pack(side='left')
        ttk.Button(bfr, text='[ Abrir no navegador (confirmar) ]',
                   command=self.open_browser).pack(side='left', padx=6)
        ttk.Label(bfr, text='  Filtro:').pack(side='left')
        self.url_filter_buttons['alto'] = self._legend_button(
            bfr, '■ ALTO', RED, lambda: self.toggle_url_filter('alto'))
        self.url_filter_buttons['medio'] = self._legend_button(
            bfr, '■ MÉDIO', ORANGE, lambda: self.toggle_url_filter('medio'))
        self.url_filter_buttons['baixo'] = self._legend_button(
            bfr, '■ BAIXO', FG, lambda: self.toggle_url_filter('baixo'))

        cols = ('url', 'host', 'ip', 'scheme', 'score', 'risk', 'reasons')

        heads = {
            'url': 'URL',
            'host': 'Domínio',
            'ip': 'IP',
            'scheme': 'Esquema',
            'score': 'Pontos',
            'risk': 'Risco',
            'reasons': 'Motivos',
        }
        widths = {
            'url': 1200,
            'host': 200,
            'ip': 200,
            'scheme': 90,
            'score': 60,
            'risk': 70,
            'reasons': 600,
        }
        self.tree = self._make_tree(fr_links, cols, heads, widths, stretch=False)        

        for col in cols:
            self.tree.heading(col, anchor='w')
            self.tree.column(col, anchor='w')

        self.tree.tag_configure('alto', foreground=RED)
        self.tree.tag_configure('medio', foreground=ORANGE)
        self.tree.tag_configure('baixo', foreground=FG)
        self.nb.add(fr_links, text=' Links e URL ')

        # ---------- aba E-MAILS ----------
        fr_emails = ttk.Frame(self.nb)
        bfr_e = ttk.Frame(fr_emails)
        bfr_e.pack(side='bottom', fill='x', pady=4)
        ttk.Button(bfr_e, text='[ Copiar e-mail ]',
                   command=self.copy_email).pack(side='left')
        ttk.Label(bfr_e, text='  Legenda:').pack(side='left')
        self.email_filter_buttons['obf'] = self._legend_button(
            bfr_e, '■ Ofuscado', FG, lambda: self.toggle_email_filter('obf'))
        self.email_filter_buttons['norm'] = self._legend_button(
            bfr_e, '■ Não ofuscado', ORANGE,
            lambda: self.toggle_email_filter('norm'))

        cols_e = ('email', 'count', 'obf', 'sus', 'context')
        
        heads_e = {'email': 'E-mail', 'count': 'Ocorr.', 'obf': 'Ofuscado',
                   'sus': 'Suspeita', 'context': 'Contexto'}
        
        widths_e = {
            'email': 520,
            'count': 55,
            'obf': 75,
            'sus': 400,
            'context': 1500,
        }

        self.tree_emails = self._make_tree(fr_emails, cols_e, heads_e, widths_e, stretch=False)

        for col in cols_e:
            self.tree_emails.heading(col, anchor='w')
            self.tree_emails.column(col, anchor='w')

        self.tree_emails.tag_configure('obfuscado', foreground=FG)
        self.tree_emails.tag_configure('normal', foreground=ORANGE)
        self.nb.add(fr_emails, text=' E-mails ')

        # ---------- aba análise ----------
        fr_find = ttk.Frame(self.nb)
        self.txt_findings = self._make_text(fr_find)
        self.nb.add(fr_find, text=' Análise ')

        # ---------- aba e-mail (.eml) ----------
        fr_eml = ttk.Frame(self.nb)
        self.txt_email = self._make_text(fr_eml)

        # Cor abóbora para e-mails não ofuscados
        self.txt_email.tag_configure('abobora', foreground='#FF8C00')

        self.nb.add(fr_eml, text=' E-mail (.eml) ')

        # ---------- aba relatório ----------
        fr_rep = ttk.Frame(self.nb)
        self.txt_report = self._make_text(fr_rep)
        self.txt_report.tag_configure('rep_of', foreground=FG)
        self.txt_report.tag_configure('rep_norm', foreground=ORANGE)
        self.txt_report.tag_configure('rep_alto', foreground=RED)
        self.txt_report.tag_configure('rep_medio', foreground=ORANGE)
        self.txt_report.tag_configure('rep_baixo', foreground=FG)
        bfr2 = ttk.Frame(fr_rep)
        bfr2.pack(fill='x', pady=4)
        ttk.Button(bfr2, text='[ Exportar .txt ]',
                   command=lambda: self.export_report('txt')).pack(side='left')
        ttk.Button(bfr2, text='[ Exportar .html ]',
                   command=lambda: self.export_report('html')).pack(side='left', padx=6)
        ttk.Button(bfr2, text='[ Exportar ambos (.txt + .html) ]',
                   command=self.export_both).pack(side='left', padx=6)
        ttk.Button(bfr2, text='[ Exportar TUDO HTML ]',
                   command=self.export_full_html).pack(side='left', padx=6)
        self.nb.add(fr_rep, text=' Relatório ')

        # ---------- aba Scraper HTML ----------
        fr_scraper = ttk.Frame(self.nb)
        self._build_scraper_tab(fr_scraper)
        self.nb.add(fr_scraper, text=' Scraper HTML ')

        # ---------- aba User-Agent ----------
        fr_ua = ttk.Frame(self.nb)
        self._build_ua_tab(fr_ua)
        self.nb.add(fr_ua, text=' User-Agent ')

        # ---------- aba envio por e-mail ----------
        fr_mail = ScrollableForm(self.nb)
        self._build_mail_form(fr_mail.inner)
        self.nb.add(fr_mail, text=' Enviar por e-mail ')

    def _build_scraper_tab(self, fr):
        """Aba Scraper HTML: baixa a página, extrai todas as URLs e permite filtrar."""
        top = ttk.Frame(fr, padding=8)
        top.pack(fill='x')

        # Botão laranja: abrir index.html local
        row0 = ttk.Frame(top)
        row0.pack(fill='x', pady=(0, 6))
        self.btn_open_index = tk.Button(
            row0,
            text='Abrir index.html',
            bg=ORANGE,
            fg='#000000',
            activebackground='#ffaa33',
            activeforeground='#000000',
            relief='raised',
            bd=2,
            padx=12,
            pady=4,
            cursor='hand2',
            font=('Segoe UI', 10, 'bold'),
            command=self.scraper_open_index_html,
        )
        self.btn_open_index.pack(side='left')
        ttk.Label(
            row0,
            text='  ← Digite a URL do site abaixo e abra o index.html local '
                 '(URL relativas usam o site, nunca file://)',
        ).pack(side='left', padx=6)

        # Barra de progresso do scraper (evita "Não está respondendo") 
        prog_row = ttk.Frame(top)
        prog_row.pack(fill='x', pady=(4, 2))
        self.scraper_progress = ttk.Progressbar(
            prog_row, mode='determinate', maximum=100, length=470,
            style='Hacker.Horizontal.TProgressbar',
        )
        self.scraper_progress.pack(side='left', padx=(0, 8))
        self.scraper_prog_label = ttk.Label(prog_row, text='Pronto')
        self.scraper_prog_label.pack(side='left')
        self._scraper_busy = False

        ttk.Label(top, text='URL do site (ex.: https://exemplo.com ou https://exemplo.com/index.html):').pack(anchor='w')
        row1 = ttk.Frame(top)
        row1.pack(fill='x', pady=4)
        self.scraper_url_var = tk.StringVar()
        ent = ttk.Entry(row1, textvariable=self.scraper_url_var, width=70)
        ent.pack(side='left', fill='x', expand=True, padx=(0, 6))
        ttk.Button(row1, text='[ Buscar e extrair URL ]',
                   command=self.scraper_fetch).pack(side='left')

        row2 = ttk.Frame(top)
        row2.pack(fill='x', pady=4)
        ttk.Label(row2, text='Pesquisar:').pack(side='left')
        self.scraper_search_var = tk.StringVar()
        self.scraper_search_var.trace_add('write', lambda *_: self.scraper_apply_filter())
        ent_s = ttk.Entry(row2, textvariable=self.scraper_search_var, width=50)
        ent_s.pack(side='left', padx=6, fill='x', expand=True)
        ttk.Button(row2, text='[ Pesquisar ]',
                   command=self.scraper_apply_filter).pack(side='left', padx=4)
        ttk.Button(row2, text='[ Limpar filtro ]',
                   command=self.scraper_clear_filter).pack(side='left', padx=4)

        self.scraper_count = ttk.Label(top, text='0 URL')
        self.scraper_count.pack(anchor='w', pady=(2, 0))

        mid = ttk.Frame(fr)
        mid.pack(fill='both', expand=True, padx=8, pady=4)
        cols = ('url', 'tipo')
        heads = {'url': 'URL Encontrada', 'tipo': 'Tipo'}
        widths = {'url': 1106, 'tipo': 120}
        self.tree_scraper = self._make_tree(mid, cols, heads, widths, stretch=False)

        # Alinha cabeçalho e conteúdo das colunas à esquerda
        for col in cols:
            self.tree_scraper.heading(col, anchor='w')
            self.tree_scraper.column(col, anchor='w')

        self.tree_scraper.tag_configure('abs', foreground=FG)
        self.tree_scraper.tag_configure('rel', foreground=ORANGE)

        bot = ttk.Frame(fr, padding=8)
        bot.pack(fill='x')
        ttk.Button(bot, text='[ Copiar URL selecionada ]',
                   command=self.scraper_copy_url).pack(side='left')
        ttk.Button(bot, text='[ Abrir no navegador ]',
                   command=self.scraper_open_browser).pack(side='left', padx=6)
        ttk.Button(bot, text='[ Enviar URL para análise ]',
                   command=self.scraper_send_to_scan).pack(side='left', padx=6)
        ttk.Button(bot, text='[ Limpar lista ]',
                   command=self.scraper_clear).pack(side='left', padx=6)

    def _build_ua_tab(self, fr):
        top = ttk.Frame(fr, padding=8)
        top.pack(fill='x')
        ttk.Label(top, text='User-Agents carregados (um por linha em useragent.txt):').pack(anchor='w')

        mid = ttk.Frame(fr)
        mid.pack(fill='both', expand=True, padx=8, pady=4)
        self.list_ua = tk.Listbox(mid, bg=BG, fg=FG, selectbackground=SELECT,
                                  selectforeground=FG, relief='flat',
                                  highlightthickness=1, highlightcolor=BORDER,
                                  font=('Consolas', 9), activestyle='none')
        sb = self._make_sb(mid, self.list_ua.yview)
        self.list_ua.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.list_ua.pack(fill='both', expand=True)
        self.list_ua.bind('<<ListboxSelect>>', self._on_ua_select)

        bot = ttk.Frame(fr, padding=8)
        bot.pack(fill='x')
        ttk.Button(bot, text='[ Carregar useragent.txt ]',
                   command=self.load_ua_dialog).pack(side='left')
        ttk.Button(bot, text='[ Adicionar User-Agent ]',
                   command=self.add_ua_dialog).pack(side='left', padx=6)
        ttk.Button(bot, text='[ Remover selecionado ]',
                   command=self.remove_ua).pack(side='left', padx=6)
        ttk.Button(bot, text='[ Salvar lista em arquivo ]',
                   command=self.save_ua_file).pack(side='left', padx=6)

        self.ua_status = ttk.Label(
            fr,
            text=f'UA ativo:\n{self.selected_ua}',
            wraplength=900,
            justify='left'
        )
        self.ua_status.pack(anchor='w', padx=8, pady=4)
        self._refresh_ua_list()

    def _build_mail_form(self, fr):
        frm = ttk.LabelFrame(fr, text='SMTP', padding=10)
        frm.pack(fill='x', pady=8)
        self.mail_vars = {}
        fields = [('servidor', 'Servidor SMTP (ex.: smtp.gmail.com)'),
                  ('porta', 'Porta (587 STARTTLS / 465 SSL)'),
                  ('user', 'Usuário (e-mail)'),
                  ('senha', 'Senha / App Password'),
                  ('to', 'Destinatário do relatório'),
                  ('subject', 'Assunto')]
        for key, label in fields:
            row = ttk.Frame(frm)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label, width=34).pack(side='left')
            var = tk.StringVar()
            if key == 'porta':
                var.set('587')
            if key == 'subject':
                var.set('Relatório de análise PhishScan')
            ent = ttk.Entry(row, textvariable=var, width=46)
            if key == 'senha':
                ent.config(show='*')
            ent.pack(side='left', expand=True, fill='x')
            self.mail_vars[key] = var
        self.var_starttls = tk.BooleanVar(value=True)
        self.var_ssl = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text='Usar STARTTLS',
                        variable=self.var_starttls).pack(anchor='w', pady=(8, 0))
        ttk.Checkbutton(frm, text='Usar SSL direto (porta 465)',
                        variable=self.var_ssl).pack(anchor='w')
        ttk.Button(frm, text='[ Enviar relatório por e-mail ]',
                   command=self.send_report_mail).pack(pady=12)

    # ----------------------------- User-Agent -----------------------------
    def _refresh_ua_list(self):
        self.list_ua.delete(0, 'end')
        for ua in self.user_agents:
            mark = ' ★ ' if ua == self.selected_ua else '   '
            self.list_ua.insert('end', mark + ua)

    def _on_ua_select(self, event=None):
        sel = self.list_ua.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self.user_agents):
            self.selected_ua = self.user_agents[idx]
            self.ua_status.config(text=f'UA ativo:\n{self.selected_ua}')
            self._refresh_ua_list()
            self.status.set('User-Agent selecionado.')

    def _load_ua_file(self, path, silent=False):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith('#')]
            if not lines:
                if not silent:
                    messagebox.showinfo('User-Agent', 'Arquivo vazio.')
                return
            for ua in lines:
                if ua not in self.user_agents:
                    self.user_agents.append(ua)
            if lines:
                self.selected_ua = lines[0]
            self._refresh_ua_list()
            self.ua_status.config(text=f'UA ativo:\n{self.selected_ua}')
            if not silent:
                messagebox.showinfo('User-Agent', f'{len(lines)} User-Agent carregado')
            self.status.set(f'User-Agents carregados de {os.path.basename(path)}.')
        except OSError as e:
            if not silent:
                messagebox.showerror('Erro', str(e))

    def load_ua_dialog(self):
        path = filedialog.askopenfilename(
            title='Selecione useragent.txt',
            filetypes=[('Texto', '*.txt'), ('Todos', '*.*')])
        if path:
            self._load_ua_file(path)

    def add_ua_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('Adicionar User-Agent')
        win.configure(bg=BG)
        win.geometry('600x120')
        win.transient(self.root)
        ttk.Label(win, text='Cole o User-Agent:').pack(anchor='w', padx=10, pady=6)
        var = tk.StringVar()
        ent = ttk.Entry(win, textvariable=var, width=80)
        ent.pack(fill='x', padx=10)
        ent.focus_set()

        def ok():
            ua = var.get().strip()
            if not ua:
                return
            if ua not in self.user_agents:
                self.user_agents.append(ua)
            self.selected_ua = ua
            self._refresh_ua_list()
            self.ua_status.config(text=f'UA ativo:\n{self.selected_ua}')
            win.destroy()
            self.status.set('User-Agent adicionado e selecionado.')

        ttk.Button(win, text='[ Adicionar ]', command=ok).pack(pady=10)

    def remove_ua(self):
        sel = self.list_ua.curselection()
        if not sel:
            return
        idx = sel[0]
        if len(self.user_agents) <= 1:
            messagebox.showinfo('User-Agent', 'É preciso manter pelo menos um UA.')
            return
        removed = self.user_agents.pop(idx)
        if self.selected_ua == removed:
            self.selected_ua = self.user_agents[0]
        self._refresh_ua_list()
        self.ua_status.config(text=f'UA ativo:\n{self.selected_ua}')

    def save_ua_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            initialfile='useragent.txt',
            filetypes=[('Texto', '*.txt')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('# User-Agents do PhishScan (um por linha)\n')
                for ua in self.user_agents:
                    f.write(ua + '\n')
            messagebox.showinfo('Salvo', f'Lista salva em:\n{path}')
        except OSError as e:
            messagebox.showerror('Erro', str(e))

    # ----------------------------- formatação conteúdo --------------------
    def _format_html_content(self, text):
        """Indentação simples de HTML para leitura na aba Conteúdo."""
        if not text or not re.search(r'<\s*(html|head|body|div|a|script|form)\b', text[:3000], re.I):
            return text
        # quebra tags e indenta de forma leve (sem dependências externas)
        out = []
        indent = 0
        # separa tags em linhas
        parts = re.split(r'(<[^>]+>)', text)
        for part in parts:
            if not part:
                continue
            if part.startswith('<'):
                tag = part
                is_close = bool(re.match(r'</\s*\w+', tag))
                is_self = bool(re.match(
                    r'<(br|hr|img|input|meta|link|source|area|base|col|embed|param|track|wbr)\b',
                    tag, re.I)) or tag.rstrip().endswith('/>')
                is_open = not is_close and not is_self and not tag.startswith('<!')
                if is_close:
                    indent = max(0, indent - 1)
                line = ('  ' * indent) + tag.strip()
                out.append(line)
                if is_open:
                    indent += 1
            else:
                chunk = part.strip()
                if chunk:
                    for ln in chunk.splitlines():
                        ln = ln.strip()
                        if ln:
                            out.append(('  ' * indent) + ln)
        return '\n'.join(out) if out else text

    def _highlight_content_html(self):
        """Aplica cores básicas em tags HTML e e-mails na aba Conteúdo.

        - tags ........ #66ff66
        - atributos ... ORANGE (abóbora)
        - comentários . #33aa33
        - e-mail ofuscado ...... FG (verde)
        - e-mail NÃO ofuscado .. ORANGE (abóbora)
        """
        txt = self.txt_content
        txt.tag_configure('html_tag', foreground='#66ff66')
        txt.tag_configure('html_attr', foreground=ORANGE)
        txt.tag_configure('html_comment', foreground='#33aa33')
        txt.tag_configure('email_obf', foreground=FG)
        txt.tag_configure('email_norm', foreground=ORANGE)
        content = txt.get('1.0', 'end-1c')
        # remove tags antigas
        for tag in ('html_tag', 'html_attr', 'html_comment',
                    'email_obf', 'email_norm'):
            txt.tag_remove(tag, '1.0', 'end')
        # comentários
        for m in re.finditer(r'<!--.*?-->', content, re.DOTALL):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            txt.tag_add('html_comment', start, end)
        # tags
        for m in re.finditer(r'</?[A-Za-z][^>]*>', content):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            txt.tag_add('html_tag', start, end)
            # atributos dentro da tag
            inner = m.group(0)
            for am in re.finditer(r'\s([A-Za-z_:][\w:.-]*)\s*=', inner):
                a0 = m.start() + am.start(1)
                a1 = m.start() + am.end(1)
                txt.tag_add('html_attr', f'1.0+{a0}c', f'1.0+{a1}c')
        # e-mails normais → cor de abóbora
        for m in EMAIL_RE.finditer(content):
            txt.tag_add('email_norm', f'1.0+{m.start()}c', f'1.0+{m.end()}c')
        # e-mails ofuscados → verde (por cima do normal se houver sobreposição)
        for m in OBF_EMAIL_RE.finditer(content):
            txt.tag_add('email_obf', f'1.0+{m.start()}c', f'1.0+{m.end()}c')

    def _safe_display_path(self, value):
        """Remove file:// e caminhos locais Windows; mostra só URL http(s) ou nome limpo."""
        if not value:
            return '—'
        s = str(value).strip()
        low = s.lower()
        # bloqueia file:// e caminhos Windows locais
        if low.startswith('file:'):
            return '—'
        if re.match(r'^[A-Za-z]:[\\/]', s) or s.startswith('\\\\'):
            return os.path.basename(s.replace('\\', '/')) or '—'
        return s

    def _colorize_html_for_export(self, text):
        """Gera HTML colorido (tags / atributos / comentários / e-mails) para o export.

        Cores alinhadas à GUI:
          - tags ........ #66ff66 (verde claro)
          - atributos ... #ff8c00 (abóbora / ORANGE)
          - comentários . #33aa33 (verde escuro)
          - e-mail ofuscado ...... #00ff00
          - e-mail NÃO ofuscado .. #ff8c00 (abóbora)
          - texto ........ #00ff00 (verde neón)
        """
        if not text or not text.strip():
            return '<span class="hc-text">(vazio)</span>'

        esc = html_mod.escape
        # intervalos coloridos: (start, end, css_class)
        spans = []

        for m in re.finditer(r'<!--.*?-->', text, re.DOTALL):
            spans.append((m.start(), m.end(), 'hc-comment'))

        for m in re.finditer(r'</?[A-Za-z][^>]*>', text):
            spans.append((m.start(), m.end(), 'hc-tag'))
            inner = m.group(0)
            for am in re.finditer(r'\s([A-Za-z_:][\w:.-]*)\s*=', inner):
                a0 = m.start() + am.start(1)
                a1 = m.start() + am.end(1)
                spans.append((a0, a1, 'hc-attr'))

        # e-mails: não ofuscados = abóbora; ofuscados = verde (maior prioridade)
        for m in EMAIL_RE.finditer(text):
            spans.append((m.start(), m.end(), 'hc-email-norm'))
        for m in OBF_EMAIL_RE.finditer(text):
            spans.append((m.start(), m.end(), 'hc-email-obf'))

        if not spans:
            return f'<span class="hc-text">{esc(text)}</span>'

        # prioridade: email-obf > email-norm > attr > comment > tag
        priority = {
            'hc-email-obf': 5, 'hc-email-norm': 4,
            'hc-attr': 3, 'hc-comment': 2, 'hc-tag': 1,
        }
        spans.sort(key=lambda s: (s[0], -priority.get(s[2], 0)))

        merged = []
        for start, end, cls in spans:
            if end <= start:
                continue
            while merged and start < merged[-1][1]:
                prev_s, prev_e, prev_c = merged[-1]
                if priority.get(cls, 0) >= priority.get(prev_c, 0):
                    if start > prev_s:
                        merged[-1] = (prev_s, start, prev_c)
                    else:
                        merged.pop()
                    break
                else:
                    start = prev_e
                    if start >= end:
                        break
            if start < end:
                merged.append((start, end, cls))

        merged.sort(key=lambda s: s[0])
        out = []
        pos = 0
        for start, end, cls in merged:
            if start > pos:
                out.append(f'<span class="hc-text">{esc(text[pos:start])}</span>')
            out.append(f'<span class="{cls}">{esc(text[start:end])}</span>')
            pos = end
        if pos < len(text):
            out.append(f'<span class="hc-text">{esc(text[pos:])}</span>')
        return ''.join(out)

    # ----------------------------- Scraper HTML ---------------------------
    def _scraper_set_progress(self, value, text):
        """Atualiza barra e rótulo do scraper (chamar na thread da UI)."""
        try:
            self.scraper_progress['value'] = max(0, min(100, value))
            self.scraper_prog_label.config(text=text)
            self.status.set(text)
        except Exception:
            pass

    def _scraper_set_busy(self, busy):
        self._scraper_busy = busy
        try:
            state = 'disabled' if busy else 'normal'
            self.btn_open_index.config(state=state)
        except Exception:
            pass

    def scraper_open_index_html(self):
        """Abre index.html em thread separada com barra de progresso (não trava a GUI)."""
        if getattr(self, '_scraper_busy', False):
            messagebox.showinfo('Scraper', 'Aguarde: já existe um processamento em andamento.')
            return
        path = filedialog.askopenfilename(
            title='Selecione o index.html do site',
            filetypes=[
                ('HTML', '*.html *.htm'),
                ('index.html', 'index.html'),
                ('Todos', '*.*'),
            ],
        )
        if not path:
            return

        typed = (self.scraper_url_var.get() or '').strip()
        self._scraper_set_busy(True)
        self._scraper_set_progress(2, 'Lendo arquivo...')
        threading.Thread(
            target=self._scraper_index_worker,
            args=(path, typed),
            daemon=True,
        ).start()

    def _scraper_index_worker(self, path, typed):
        """Worker em background: lê HTML, extrai URL e formata conteúdo."""
        try:
            self.root.after(0, lambda: self._scraper_set_progress(8, 'Abrindo arquivo...'))
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                text = data.decode('utf-8', errors='replace')
            except OSError as e:
                self.root.after(0, lambda: messagebox.showerror(
                    'Erro', f'Não foi possível abrir o arquivo:\n{e}'))
                self.root.after(0, lambda: self._scraper_set_progress(0, 'Erro ao abrir'))
                self.root.after(0, lambda: self._scraper_set_busy(False))
                return

            size_kb = len(data) / 1024
            self.root.after(0, lambda: self._scraper_set_progress(
                25, f'Arquivo lido ({size_kb:.0f} KB). Extraindo URL...'))

            # Preferir SEMPRE a URL do site digitada (http/https).
            # Nunca usar file:// como base quando o usuário informou o site —
            # assim cadastro.php vira https://site.com/cadastro.php e não
            # file://C:/Users/.../cadastro.php
            typed = (typed or '').strip()
            if typed and not typed.lower().startswith(('http://', 'https://')):
                typed = 'https://' + typed
            site_base = typed if typed.lower().startswith(('http://', 'https://')) else ''
            file_base = 'file://' + os.path.abspath(path).replace('\\', '/')
            base_url = site_base or file_base

            # Apenas extrai URL — sem formatar HTML (arquivos grandes travavam a GUI)
            found = extract_urls(text, is_html=True)
            total_raw = len(found)
            self.root.after(0, lambda: self._scraper_set_progress(
                55, f'Processando {total_raw} link...'))

            resolved = []
            seen = set()
            items = list(found.keys())
            n = len(items) or 1
            for i, raw in enumerate(items):
                raw_s = raw.strip()
                # Resolve relativo contra a base do site (ou file só se não houver site)
                abs_url = urljoin(base_url, raw_s)
                abs_url = abs_url.split('#')[0].strip()
                if not abs_url or abs_url in seen:
                    continue
                low = abs_url.lower()
                if low.startswith(('javascript:', 'mailto:', 'tel:', 'data:', 'vbscript:')):
                    continue
                # Nunca mostrar caminhos locais file:// na lista
                if low.startswith('file:'):
                    if site_base:
                        # refaz com a base do site
                        abs_url = urljoin(site_base, raw_s).split('#')[0].strip()
                        low = abs_url.lower()
                        if low.startswith('file:') or not abs_url or abs_url in seen:
                            continue
                    else:
                        continue
                seen.add(abs_url)
                tipo = 'absoluta' if raw_s.lower().startswith(
                    ('http://', 'https://', '//')) else 'relativa'
                resolved.append({'url': abs_url, 'tipo': tipo, 'original': raw})
                if i % 200 == 0 or i == n - 1:
                    pct = 55 + int(35 * (i + 1) / n)
                    self.root.after(0, lambda p=pct, cur=i + 1, tot=n: self._scraper_set_progress(
                        p, f'Normalizando URL ({cur}/{tot})...'))

            resolved.sort(key=lambda x: x['url'].lower())
            tree_rows = [(it['url'], it['tipo']) for it in resolved]
            fname = os.path.basename(path)
            display_base = site_base or '(informe a URL do site no campo acima)'

            def apply():
                self.scraper_urls = resolved
                # Nunca grava file:// como base (evita aparecer no HTML exportado)
                self.scraper_base_url = site_base  # pode ser '' se usuário não digitou
                self.scraper_search_var.set('')

                for i in self.tree_scraper.get_children():
                    self.tree_scraper.delete(i)
                for url, tipo in tree_rows:
                    tag = 'abs' if tipo == 'absoluta' else 'rel'
                    self.tree_scraper.insert('', 'end', values=(url, tipo), tags=(tag,))
                total = len(resolved)
                self.scraper_count.config(text=f'{total} URL')

                # filepath: só URL do site (nunca caminho local file://)
                self.filepath = site_base or None
                self.file_label.config(
                    text=(f'Site: {site_base[:60]}' if site_base
                          else f'Arquivo: {fname} (URL do site)'))
                # Resumo leve — não carrega o HTML inteiro (evita "Não está respondendo")
                self.txt_content.delete('1.0', 'end')
                aviso_base = (
                    f'Base do site: {display_base}\n'
                    if site_base else
                    '⚠️ Digite a URL do site (https://...) no campo do Scraper '
                    'antes de abrir o index.html, para as  relativas '
                    '(ex.: cadastro.php) saírem como URL do site e não file://\n'
                )
                self.txt_content.insert(
                    '1.0',
                    f'[Scraper HTML] Arquivo local: {fname}\n'
                    f'Tamanho: {size_kb:.0f} KB\n'
                    f'URL extraídas: {total}\n'
                    f'{aviso_base}\n'
                    'Conteúdo completo não carregado na aba Conteúdo '
                    'para não travar com arquivos grandes.\n'
                    'Use a lista de URL e o campo Pesquisar.'
                )

                self._scraper_set_progress(100, f'Concluído: {total} URL de {fname}')
                self._scraper_set_busy(False)
                self.status.set(
                    f'Scraper: {total} URL extraídas'
                    + (f' (base: {site_base})' if site_base else f' de {fname}')
                )

            self.root.after(0, apply)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Erro no scraper', str(e)))
            self.root.after(0, lambda: self._scraper_set_progress(0, 'Erro'))
            self.root.after(0, lambda: self._scraper_set_busy(False))

    def scraper_fetch(self):
        url = self.scraper_url_var.get().strip()
        if not url:
            messagebox.showwarning('Aviso', 'Digite a URL do site.')
            return
        if getattr(self, '_scraper_busy', False):
            messagebox.showinfo('Scraper', 'Aguarde: já existe um processamento em andamento.')
            return
        self._scraper_set_busy(True)
        self._scraper_set_progress(5, f'Baixando {url[:60]}...')
        threading.Thread(target=self._scraper_worker, args=(url,),
                         daemon=True).start()

    def _scraper_worker(self, url):
        try:
            self.root.after(0, lambda: self._scraper_set_progress(15, 'Baixando página...'))
            text, final_url, status = fetch_url(url, self.selected_ua)
            # Se a URL não terminar em arquivo, tenta também /index.html
            extra_urls = []
            parsed = urlparse(final_url)
            path = parsed.path or '/'
            if path.endswith('/') or path in ('', '/'):
                try:
                    self.root.after(0, lambda: self._scraper_set_progress(
                        35, 'Tentando index.html...'))
                    index_url = urljoin(final_url, 'index.html')
                    if index_url != final_url:
                        text2, final2, st2 = fetch_url(index_url, self.selected_ua)
                        if st2 == 200 and text2:
                            extra_urls.append((text2, final2))
                except Exception:
                    pass

            self.root.after(0, lambda: self._scraper_set_progress(55, 'Extraindo URL...'))
            all_raw = {}
            found = extract_urls(text, is_html=True)
            for u, c in found.items():
                all_raw[u] = all_raw.get(u, 0) + c
            for t2, _ in extra_urls:
                found2 = extract_urls(t2, is_html=True)
                for u, c in found2.items():
                    all_raw[u] = all_raw.get(u, 0) + c

            self.root.after(0, lambda: self._scraper_set_progress(75, 'Normalizando URL...'))
            resolved = []
            seen = set()
            for raw in all_raw:
                abs_url = urljoin(final_url, raw.strip())
                abs_url = abs_url.split('#')[0].strip()
                if not abs_url or abs_url in seen:
                    continue
                low = abs_url.lower()
                if low.startswith(('javascript:', 'mailto:', 'tel:', 'data:', 'vbscript:')):
                    continue
                seen.add(abs_url)
                tipo = 'absoluta' if raw.strip().lower().startswith(
                    ('http://', 'https://', '//')) else 'relativa'
                resolved.append({'url': abs_url, 'tipo': tipo, 'original': raw})

            resolved.sort(key=lambda x: x['url'].lower())

            def apply():
                self.scraper_urls = resolved
                self.scraper_base_url = final_url
                self.scraper_search_var.set('')
                self.scraper_apply_filter()
                msg = (
                    f'Scraper: {len(resolved)} URL extraídas de {final_url} '
                    f'(HTTP {status})' +
                    (f' + index.html' if extra_urls else '')
                )
                self._scraper_set_progress(100, f'Concluído: {len(resolved)} URL')
                self._scraper_set_busy(False)
                self.status.set(msg)
            self.root.after(0, apply)
        except HTTPError as e:
            self.root.after(0, lambda: messagebox.showerror(
                'HTTP Error', f'{e.code} {e.reason}'))
            self.root.after(0, lambda: self._scraper_set_progress(0, 'Falha HTTP'))
            self.root.after(0, lambda: self._scraper_set_busy(False))
        except URLError as e:
            self.root.after(0, lambda: messagebox.showerror(
                'Erro de rede', str(e.reason)))
            self.root.after(0, lambda: self._scraper_set_progress(0, 'Falha de rede'))
            self.root.after(0, lambda: self._scraper_set_busy(False))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Erro', str(e)))
            self.root.after(0, lambda: self._scraper_set_progress(0, 'Erro'))
            self.root.after(0, lambda: self._scraper_set_busy(False))

    def scraper_apply_filter(self):
        term = (self.scraper_search_var.get() or '').strip().lower()
        for i in self.tree_scraper.get_children():
            self.tree_scraper.delete(i)
        shown = 0
        for item in self.scraper_urls:
            if term and term not in item['url'].lower() and term not in item.get('original', '').lower():
                continue
            tag = 'abs' if item['tipo'] == 'absoluta' else 'rel'
            self.tree_scraper.insert('', 'end', values=(item['url'], item['tipo']), tags=(tag,))
            shown += 1
        total = len(self.scraper_urls)
        if term:
            self.scraper_count.config(
                text=f'{shown} de {total} URL (filtro: "{term}")')
        else:
            self.scraper_count.config(text=f'{total} URL')

    def scraper_clear_filter(self):
        self.scraper_search_var.set('')
        self.scraper_apply_filter()

    def scraper_clear(self):
        self.scraper_urls = []
        self.scraper_base_url = ''
        self.scraper_search_var.set('')
        self.scraper_url_var.set('')
        for i in self.tree_scraper.get_children():
            self.tree_scraper.delete(i)
        self.scraper_count.config(text='0 URL')
        self.status.set('Scraper limpo.')

    def scraper_copy_url(self):
        sel = self.tree_scraper.selection()
        if not sel:
            return
        url = self.tree_scraper.item(sel[0], 'values')[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.status.set('URL do scraper copiada.')

    def scraper_open_browser(self):
        sel = self.tree_scraper.selection()
        if not sel:
            return
        url = self.tree_scraper.item(sel[0], 'values')[0]
        if messagebox.askyesno(
                'Abrir no navegador',
                f'URL:\n{url}\n\nAbrir mesmo assim? Use ambiente controlado.'):
            webbrowser.open(url)

    def scraper_send_to_scan(self):
        """Coloca a URL selecionada na barra de URL ao vivo e inicia o scan."""
        sel = self.tree_scraper.selection()
        if not sel:
            messagebox.showinfo('Scraper', 'Selecione uma URL na lista.')
            return
        url = self.tree_scraper.item(sel[0], 'values')[0]
        self.url_var.set(url)
        self.nb.select(0)  # vai para a primeira aba (Conteúdo) ou deixa o usuário
        self.status.set(f'URL enviada para análise: {url[:80]}')
        if messagebox.askyesno('Analisar', f'Buscar e escanear agora?\n\n{url}'):
            self.fetch_and_scan()

    # ----------------------------- ações ----------------------------------
    # ----------------------- progresso global (abrir/scan) ----------------
    def _main_set_progress(self, value, text):
        try:
            self.main_progress['value'] = max(0, min(100, value))
            self.main_prog_label.config(text=text)
            self.status.set(text)
        except Exception:
            pass

    def _load_content_to_ui(self, text, is_html, label_text, status_msg):
        """Mostra conteúdo na aba sem travar: arquivos grandes vão truncados."""
        self._raw_content = text
        limit = self._CONTENT_UI_LIMIT
        self.txt_content.delete('1.0', 'end')
        if len(text) > limit:
            preview = text[:limit]
            if is_html:
                # não formata HTML gigante (travava a GUI)
                display = (
                    f'[Arquivo grande: {len(text):,} caracteres]\n'
                    f'Prévia dos primeiros {limit:,} caracteres '
                    f'(conteúdo completo fica em memória para o Escanear).\n'
                    f'{("=" * 60)}\n\n'
                    + preview
                )
            else:
                display = (
                    f'[Arquivo grande: {len(text):,} caracteres]\n'
                    f'Prévia dos primeiros {limit:,} caracteres.\n'
                    f'{("=" * 60)}\n\n'
                    + preview
                )
            self.txt_content.insert('1.0', display)
            # destaque leve só na prévia pequena
            if is_html and len(preview) < 80_000:
                try:
                    self._highlight_content_html()
                except Exception:
                    pass
        else:
            display = self._format_html_content(text) if is_html else text
            self.txt_content.insert('1.0', display)
            if is_html:
                try:
                    self._highlight_content_html()
                except Exception:
                    pass
        self.file_label.config(text=label_text)
        self.status.set(status_msg)

    def open_file(self):
        """Abre arquivo em thread (igual scraper) — não trava a GUI."""
        if self._open_busy or self._scan_busy:
            messagebox.showinfo(
                'Aguarde',
                'Já existe um processamento em andamento (abrir ou escanear).')
            return
        path = filedialog.askopenfilename(
            title='Selecione o arquivo',
            filetypes=[('Arquivos de texto/e-mail',
                        '*.txt *.html *.htm *.eml'),
                       ('E-mail', '*.eml'), ('HTML', '*.html *.htm'),
                       ('Texto', '*.txt'), ('Todos', '*.*')])
        if not path:
            return
        self._open_busy = True
        self._main_set_progress(5, f'Lendo {os.path.basename(path)}...')
        threading.Thread(
            target=self._open_file_worker,
            args=(path,),
            daemon=True,
        ).start()

    def _open_file_worker(self, path):
        try:
            self.root.after(0, lambda: self._main_set_progress(
                15, 'Abrindo arquivo...'))
            try:
                with open(path, 'rb') as f:
                    data = f.read()
            except OSError as e:
                self.root.after(0, lambda: messagebox.showerror(
                    'Erro', f'Não foi possível abrir: {e}'))
                self.root.after(0, lambda: self._main_set_progress(0, 'Erro'))
                self.root.after(0, lambda: setattr(self, '_open_busy', False))
                return

            size_kb = len(data) / 1024
            self.root.after(0, lambda: self._main_set_progress(
                40, f'Decodificando ({size_kb:.0f} KB)...'))
            text = data.decode('utf-8', errors='replace')
            is_html_file = path.lower().endswith(('.html', '.htm')) or bool(
                re.search(r'<\s*(html|head|body)\b', text[:2000], re.I))
            is_eml = path.lower().endswith('.eml') or looks_like_email(text)

            self.root.after(0, lambda: self._main_set_progress(
                70, 'Preparando visualização...'))

            fname = os.path.basename(path)
            label = fname if len(fname) < 50 else fname[:47] + '...'

            def apply():
                self.filepath = path
                self._load_content_to_ui(
                    text, is_html_file and not is_eml, label,
                    f'Arquivo carregado ({size_kb:.0f} KB). Clique em Escanear.')
                self._main_set_progress(100, f'Pronto: {fname}')
                self._open_busy = False

            self.root.after(0, apply)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Erro', str(e)))
            self.root.after(0, lambda: self._main_set_progress(0, 'Erro'))
            self.root.after(0, lambda: setattr(self, '_open_busy', False))

    def paste_clipboard(self):
        if self._open_busy or self._scan_busy:
            messagebox.showinfo(
                'Aguarde',
                'Já existe um processamento em andamento (abrir ou escanear).')
            return
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showinfo('Área de transferência', 'Nada para colar.')
            return
        if not text or not str(text).strip():
            messagebox.showinfo('Área de transferência', 'Nada para colar.')
            return
        self._open_busy = True
        self._main_set_progress(20, 'Processando conteúdo colado...')
        threading.Thread(
            target=self._paste_worker,
            args=(str(text),),
            daemon=True,
        ).start()

    def _paste_worker(self, text):
        try:
            is_html = bool(re.search(
                r'<\s*(html|head|body|div|a\s)\b', text[:2000], re.I))
            self.root.after(0, lambda: self._main_set_progress(
                60, 'Preparando visualização...'))

            def apply():
                self.filepath = None
                self._load_content_to_ui(
                    text, is_html, '(conteúdo colado)',
                    'Conteúdo colado. Clique em Escanear.')
                self._main_set_progress(100, 'Conteúdo colado — pronto')
                self._open_busy = False

            self.root.after(0, apply)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Erro', str(e)))
            self.root.after(0, lambda: self._main_set_progress(0, 'Erro'))
            self.root.after(0, lambda: setattr(self, '_open_busy', False))

    def fetch_and_scan(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning('Aviso', 'Digite uma URL (http ou https).')
            return
        if self._open_busy or self._scan_busy:
            messagebox.showinfo(
                'Aguarde',
                'Já existe um processamento em andamento (abrir ou escanear).')
            return
        self._open_busy = True
        self._main_set_progress(5, f'Baixando {url[:50]}...')
        threading.Thread(target=self._fetch_worker, args=(url,),
                         daemon=True).start()

    def _fetch_worker(self, url):
        try:
            text, final_url, status = fetch_url(url, self.selected_ua)

            def apply():
                self.filepath = final_url
                label = (f'URL: {final_url[:60]}...'
                         if len(final_url) > 60 else f'URL: {final_url}')
                is_html = True
                self._load_content_to_ui(
                    text, is_html, label,
                    f'Página baixada (HTTP {status}). Escaneando...')
                self._main_set_progress(50, 'Página baixada — iniciando scan...')
                self._open_busy = False
                self.start_scan()

            self.root.after(0, apply)
        except HTTPError as e:
            self.root.after(0, lambda: messagebox.showerror(
                'HTTP Error', f'{e.code} {e.reason}'))
            self.root.after(0, lambda: self._main_set_progress(0, 'Falha ao baixar'))
            self.root.after(0, lambda: setattr(self, '_open_busy', False))
        except URLError as e:
            self.root.after(0, lambda: messagebox.showerror(
                'Erro de rede', str(e.reason)))
            self.root.after(0, lambda: self._main_set_progress(0, 'Falha de rede'))
            self.root.after(0, lambda: setattr(self, '_open_busy', False))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Erro', str(e)))
            self.root.after(0, lambda: self._main_set_progress(0, 'Erro'))
            self.root.after(0, lambda: setattr(self, '_open_busy', False))

    def clear_all(self):
        for w in (self.txt_content, self.txt_findings, self.txt_email,
                  self.txt_report):
            w.delete('1.0', 'end')
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in self.tree_emails.get_children():
            self.tree_emails.delete(i)
        # limpa também o scraper
        if hasattr(self, 'tree_scraper'):
            for i in self.tree_scraper.get_children():
                self.tree_scraper.delete(i)
            self.scraper_urls = []
            self.scraper_base_url = ''
            if hasattr(self, 'scraper_search_var'):
                self.scraper_search_var.set('')
            if hasattr(self, 'scraper_url_var'):
                self.scraper_url_var.set('')
            if hasattr(self, 'scraper_count'):
                self.scraper_count.config(text='0 URL')
        self.filepath = None
        self.results = None
        self._raw_content = None
        self._dns_cache.clear()
        self.filter_urls = None
        self.filter_emails = None
        for b in self.url_filter_buttons.values():
            b.config(relief='raised')
        for b in self.email_filter_buttons.values():
            b.config(relief='raised')
        self.file_label.config(text='Nenhum arquivo carregado')
        self.verdict.config(text='Risco geral: ', foreground=FG)
        self.url_var.set('')
        try:
            self.main_progress['value'] = 0
            self.main_prog_label.config(text='Pronto')
        except Exception:
            pass
        self.status.set('Pronto.')

    def start_scan(self):
        """Escanear em thread — usa _raw_content (arquivo completo) se existir."""
        if self._scan_busy:
            messagebox.showinfo('Aguarde', 'Já existe um escaneamento em andamento.')
            return
        if self._open_busy:
            messagebox.showinfo('Aguarde', 'Aguarde o arquivo terminar de carregar.')
            return
        content = self._raw_content
        if not content or not str(content).strip():
            content = self.txt_content.get('1.0', 'end-1c')
        content = (content or '').strip()
        if not content:
            messagebox.showwarning(
                'Aviso',
                'Carregue um arquivo, cole conteúdo ou busque uma URL.')
            return
        # se a aba só tem prévia de arquivo grande, garante o bruto
        if content.startswith('[Arquivo grande:') and self._raw_content:
            content = self._raw_content
        self._scan_busy = True
        self._main_set_progress(5, 'Escaneando... (DNS pode demorar)')
        threading.Thread(target=self._scan_worker, args=(content,),
                         daemon=True).start()

    # --------------------------- motor (thread) ---------------------------
    def _scan_worker(self, content):
        try:
            self.root.after(0, lambda: self._main_set_progress(
                12, 'Detectando tipo de conteúdo...'))
            is_eml = (isinstance(self.filepath, str) and
                      str(self.filepath).lower().endswith('.eml')) or looks_like_email(content)
            is_html = (isinstance(self.filepath, str) and
                       str(self.filepath).lower().endswith(('.html', '.htm'))) or bool(
                re.search(r'<html|<head|<body|<a\s', content[:2000], re.I))
            # URL ao vivo → trata como HTML
            if isinstance(self.filepath, str) and str(self.filepath).lower().startswith(
                    ('http://', 'https://')):
                is_html = True
                is_eml = False

            eml_info = None
            if is_eml:
                self.root.after(0, lambda: self._main_set_progress(
                    25, 'Analisando cabeçalhos .eml...'))
                eml_info = analyze_eml(content.encode('utf-8', errors='replace'))
                body = eml_info['body_html'] or eml_info['body_plain'] or content
            else:
                body = content

            self.root.after(0, lambda: self._main_set_progress(
                40, 'Extraindo URL...'))
            urls = extract_urls(body, is_html)
            url_list = [analyze_url(u) for u in urls]

            n_hosts = sum(1 for it in url_list
                          if it['host'] and not it['ip'] and it['host'] != '(sem host)')
            done_dns = 0
            for item in url_list:
                host = item['host']
                if host and not item['ip'] and host != '(sem host)':
                    if host not in self._dns_cache:
                        try:
                            # timeout curto evita trava longa em DNS lento
                            old_to = socket.getdefaulttimeout()
                            socket.setdefaulttimeout(3)
                            try:
                                socket.getaddrinfo(host, None)
                                self._dns_cache[host] = True
                            finally:
                                socket.setdefaulttimeout(old_to)
                        except (socket.gaierror, socket.timeout, OSError):
                            self._dns_cache[host] = False
                    if not self._dns_cache[host]:
                        item['score'] += 10
                        item['reasons'] += '; DNS não resolve'
                        item['risk'] = 'alto' if item['score'] >= 60 else (
                            'medio' if item['score'] >= 30 else 'baixo')
                    done_dns += 1
                    if n_hosts and done_dns % max(1, n_hosts // 10) == 0:
                        pct = 40 + int(30 * done_dns / max(1, n_hosts))
                        self.root.after(0, lambda p=pct, d=done_dns, t=n_hosts:
                                        self._main_set_progress(
                                            p, f'DNS ({d}/{t})...'))

            self.root.after(0, lambda: self._main_set_progress(
                75, 'Extraindo e-mails e ofuscação...'))
            emails = extract_emails(content)

            findings = analyze_content(body, is_html)
            if eml_info:
                findings += eml_info['findings']
            for f in eml_info['attachments'] if eml_info else []:
                findings.append('Anexo: ' + f)

            file_score = max([u['score'] for u in url_list], default=0)
            file_score += min(30, len(findings) * 5)
            risk = 'ALTO' if file_score >= 60 else (
                'MÉDIO' if file_score >= 30 else 'BAIXO')

            self.root.after(0, lambda: self._main_set_progress(
                90, 'Montando relatório...'))
            report = self._build_report(url_list, emails, findings, eml_info,
                                        is_html, is_eml, risk, len(body))
            self.results = {'url': url_list, 'emails': emails,
                            'findings': findings, 'eml': eml_info,
                            'report': report, 'risk': risk,
                            'content_len': len(body), 'n_url': len(urls),
                            'is_html': is_html}

            def finish():
                self._show_results()
                self._main_set_progress(
                    100,
                    f"Análise concluída: {len(urls)} URL, "
                    f"{len(emails)} e-mail, {len(findings)} achado")
                self._scan_busy = False

            self.root.after(0, finish)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                'Erro na análise', str(e)))
            self.root.after(0, lambda: self._main_set_progress(0, 'Erro na análise'))
            self.root.after(0, lambda: setattr(self, '_scan_busy', False))

    # --------------------------- tabelas / filtros ------------------------
    def refresh_url_table(self):
        if not self.results:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        for u in self.results['url']:
            if self.filter_urls and u['risk'] != self.filter_urls:
                continue
            self.tree.insert('', 'end', values=(
                u['url'], u['host'], u['ip'], u['scheme'], u['score'],
                u['risk'].upper(), u['reasons']), tags=(u['risk'],))

    def toggle_url_filter(self, risk):
        self.filter_urls = None if self.filter_urls == risk else risk
        for key, btn in self.url_filter_buttons.items():
            btn.config(relief='sunken' if self.filter_urls == key else 'raised')
        self.refresh_url_table()

    def refresh_email_table(self):
        if not self.results:
            return
        for i in self.tree_emails.get_children():
            self.tree_emails.delete(i)
        for e in sorted(self.results['emails'], key=lambda x: -x['count']):
            obf = e['obfuscated']
            if self.filter_emails is not None and \
                    obf != (self.filter_emails == 'obf'):
                continue
            tag = 'obfuscado' if obf else 'normal'
            self.tree_emails.insert('', 'end', values=(
                e['email'], e['count'], 'SIM' if obf else 'não',
                e['suspicious'] or '—', e['context']), tags=(tag,))

    def toggle_email_filter(self, mode):
        self.filter_emails = None if self.filter_emails == mode else mode
        for key, btn in self.email_filter_buttons.items():
            btn.config(relief='sunken' if self.filter_emails == key else 'raised')
        self.refresh_email_table()

    def _show_results(self):
        r = self.results
        self.refresh_url_table()
        self.refresh_email_table()

        self.txt_findings.delete('1.0', 'end')
        if r['findings']:
            for f in r['findings']:
                self.txt_findings.insert('end', '• ' + f + '\n')
        else:
            self.txt_findings.insert('end', 'Nenhum padrão suspeito encontrado.\n')

        self.txt_email.delete('1.0', 'end')
        if r['eml']:
            e = r['eml']
            self.txt_email.insert('end',
                f"De: {e['from']}\nPara: {e['to']}\nAssunto: {e['subject']}\n"
                f"Data: {e['date']}\nReply-To: {e['reply_to']}\n"
                f"Return-Path: {e['return_path']}\n\n"
                '--- Autenticação ---\n' +
                ('\n'.join(e['auth']) or '(nenhum cabeçalho de autenticação)') +
                '\n\n--- Anexos ---\n' +
                ('\n'.join(e['attachments']) or '(nenhum)') + '\n')
        else:
            self.txt_email.insert(
                'end',
                'Conteúdo não identificado como mensagem de e-mail '
                '(sem cabeçalhos From/To/Subject).\n\n')
            if r['emails']:
                self.txt_email.insert('end',
                                      'E-mails Encontrados no conteúdo\n\n')
                for em in r['emails']:
                    tag = ' [OFUSCADO]' if em['obfuscated'] else ''
                    sus = f" | {em['suspicious']}" if em['suspicious'] else ''

                    texto = f"  • {em['email']} x{em['count']}{tag}{sus}\n"

                    if not em['obfuscated']:
                        self.txt_email.insert('end', texto, 'abobora')
                    else:
                        self.txt_email.insert('end', texto)
            else:
                self.txt_email.insert('end', 'Nenhum e-mail encontrado.\n')
            self.txt_email.insert(
                'end',
                '\nDica: para ver cabeçalhos completos (SPF/DKIM/DMARC), '
                'salve a mensagem como .eml e abra novamente.')

        self.txt_report.delete('1.0', 'end')
        for line in r['report'].split('\n'):
            tag = None
            stripped = line.lstrip()
            if '[OFUSCADO]' in line or (re.search(r'\bSIM\b', line) and '@' in line):
                tag = 'rep_of'
            elif re.search(r'@\S+', line) and ('não' in line or re.search(r'\s+não\s+', line)):
                tag = 'rep_norm'
            elif stripped.startswith('[ALTO'):
                tag = 'rep_alto'
            elif stripped.startswith('[MÉDIO'):
                tag = 'rep_medio'
            elif stripped.startswith('[BAIXO'):
                tag = 'rep_baixo'
            elif 'Risco geral' in line and 'ALTO' in line:
                tag = 'rep_alto'
            elif 'Risco geral' in line and 'MÉDIO' in line:
                tag = 'rep_medio'
            elif 'Risco geral' in line and 'BAIXO' in line:
                tag = 'rep_baixo'
            self.txt_report.insert('end', line + '\n', tag)

        self.verdict.config(
            text=f"Risco geral: {r['risk']}",
            foreground={'ALTO': RED, 'MÉDIO': ORANGE, 'BAIXO': FG}[r['risk']])
        self.status.set(f"Análise Concluída: {r['n_url']} URL, "
                        f"{len(r['emails'])} E-mail, "
                        f"{len(r['findings'])} Achado")

    # --------------------------- relatório --------------------------------
    def _build_report(self, urls, emails, findings, eml_info, is_html, is_eml,
                      risk, content_len):
        """Relatório TXT profissional, alinhado e legível."""
        W = 78
        sep = '=' * W
        thin = '-' * W
        L = []
        L.append(sep)
        L.append('  PHISHSCAN  —  RELATÓRIO DE ANÁLISE DE PHISHING'.center(W))
        L.append(sep)
        L.append('')
        L.append('  RESUMO')
        L.append(thin)
        _src = self._safe_display_path(self.filepath) if self.filepath else '(conteúdo colado)'
        if _src == '—':
            _src = '(conteúdo colado)'
        L.append(f'  Arquivo / URL ......: {_src}')
        L.append(f'  Data / hora ........: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        L.append(f'  Tamanho analisado ..: {content_len:,} bytes')
        tipo = 'E-mail (.eml)' if is_eml else ('HTML' if is_html else 'Texto')
        L.append(f'  Tipo de conteúdo ...: {tipo}')
        L.append(f'  User-Agent .........: {self.selected_ua}')
        L.append(f'  Risco geral ........: {risk}')
        L.append(f'  URL encontradas ...:  {len(urls)}')
        L.append(f'  E-mails encontrados : {len(emails)}')
        L.append(f'  Achados de conteúdo : {len(findings)}')
        L.append('')

        n_alto = sum(1 for u in urls if u['risk'] == 'alto')
        n_medio = sum(1 for u in urls if u['risk'] == 'medio')
        n_baixo = sum(1 for u in urls if u['risk'] == 'baixo')
        L.append('  DISTRIBUIÇÃO DE RISCO (URL)')
        L.append(thin)
        L.append(f'  [ALTO ]  {n_alto:4d}   |  [MÉDIO]  {n_medio:4d}   |  [BAIXO]  {n_baixo:4d}')
        L.append('')

        L.append('  E-MAILS ENCONTRADOS')
        L.append(thin)
        if emails:
            L.append(f'  {"E-mail":<42} {"Ocorr.":>6}  {"Ofuscado":<10}  Suspeita')
            L.append('  ' + ('-' * 42) + '  ' + ('-' * 6) + '  ' + ('-' * 10) + '  ' + ('-' * 20))
            for e in sorted(emails, key=lambda x: -x['count']):
                obf = 'SIM' if e['obfuscated'] else 'não'
                sus = e['suspicious'] or '—'
                em = e['email'][:42]
                L.append(f'  {em:<42} {e["count"]:>6}  {obf:<10}  {sus}')
        else:
            L.append('  Nenhum e-mail encontrado.')
        L.append('')

        L.append('  LINKS E URL')
        L.append(thin)
        if urls:
            for u in sorted(urls, key=lambda x: -x['score']):
                risk_tag = f"[{u['risk'].upper():5}]"
                L.append(f'  {risk_tag}  {u["score"]:3d} pts')
                L.append(f'         URL ....: {u["url"]}')
                L.append(f'         Host ...: {u["host"]}')
                L.append(f'         IP .....: {u["ip"] or "—"}')
                L.append(f'         Esquema : {u["scheme"]}')
                L.append(f'         Motivos : {u["reasons"]}')
                L.append('')
        else:
            L.append('  Nenhuma URL encontrada.')
            L.append('')

        L.append('  ACHADOS DE CONTEÚDO / OFUSCAÇÃO')
        L.append(thin)
        if findings:
            for f in findings:
                L.append(f'  • {f}')
        else:
            L.append('  Nenhum padrão suspeito detectado.')
        L.append('')

        if eml_info:
            L.append('  CABEÇALHOS DO E-MAIL (.eml)')
            L.append(thin)
            L.append(f'  De ...........: {eml_info["from"]}')
            L.append(f'  Para .........: {eml_info["to"]}')
            L.append(f'  Assunto ......: {eml_info["subject"]}')
            L.append(f'  Data .........: {eml_info["date"]}')
            L.append(f'  Reply-To .....: {eml_info["reply_to"]}')
            L.append(f'  Return-Path ..: {eml_info["return_path"]}')
            if eml_info['auth']:
                L.append('  Autenticação :')
                for a in eml_info['auth']:
                    L.append(f'    • {a}')
            else:
                L.append('  Autenticação : (nenhum cabeçalho SPF/DKIM/DMARC)')
            if eml_info['attachments']:
                L.append('  Anexos .......:')
                for a in eml_info['attachments']:
                    L.append(f'    • {a}')
            L.append('')

        L.append(sep)
        L.append('  LEGENDA')
        L.append(thin)
        L.append('  URL   : [ALTO] vermelho  |  [MÉDIO] laranja  |  [BAIXO] verde')
        L.append('  E-mails: OFUSCADO = verde  |  Não ofuscado = laranja')
        L.append('')
        L.append('  Ferramenta para análise autorizada de conteúdo próprio.')
        L.append(f'  Gerado por PhishScan GUI — {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        L.append(sep)
        return '\n'.join(L)

    def _build_html_report(self, urls, emails, findings, eml_info, is_html, is_eml,
                           risk, content_len):
        """Relatório HTML profissional com tema hacker e cores iguais à GUI."""
        esc = html_mod.escape
        risk_color = {'ALTO': '#ff4444', 'MÉDIO': '#ff8c00', 'BAIXO': '#00ff00'}.get(risk, '#00ff00')
        n_alto = sum(1 for u in urls if u['risk'] == 'alto')
        n_medio = sum(1 for u in urls if u['risk'] == 'medio')
        n_baixo = sum(1 for u in urls if u['risk'] == 'baixo')
        tipo = 'E-mail (.eml)' if is_eml else ('HTML' if is_html else 'Texto')
        agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        _src_raw = self.filepath or '(conteúdo colado)'
        if str(_src_raw).lower().startswith('file:') or re.match(r'^[A-Za-z]:[\\/]', str(_src_raw)):
            _src_raw = '(conteúdo colado)'
        src = esc(self._safe_display_path(_src_raw) if _src_raw != '(conteúdo colado)' else _src_raw)
        if src == '—':
            src = '(conteúdo colado)'
        ua = esc(self.selected_ua)

        # --- linhas de e-mails ---
        email_rows = []
        for e in sorted(emails, key=lambda x: -x['count']):
            color = '#00ff00' if e['obfuscated'] else '#ff8c00'
            obf = 'SIM' if e['obfuscated'] else 'não'
            sus = esc(e['suspicious'] or '—')
            email_rows.append(
                f'<tr style="color:{color}">'
                f'<td>{esc(e["email"])}</td>'
                f'<td class="c">{e["count"]}</td>'
                f'<td class="c">{obf}</td>'
                f'<td>{sus}</td>'
                f'<td class="ctx">{esc(e.get("context") or "")}</td>'
                f'</tr>'
            )
        if not email_rows:
            email_rows.append('<tr><td colspan="5" style="color:#33cc33">Nenhum e-mail encontrado.</td></tr>')

        # --- linhas de URL ---
        url_rows = []
        for u in sorted(urls, key=lambda x: -x['score']):
            rc = {'alto': '#ff4444', 'medio': '#ff8c00', 'baixo': '#00ff00'}[u['risk']]
            url_rows.append(
                f'<tr style="color:{rc}">'
                f'<td><span class="badge" style="background:{rc};color:#000">'
                f'{u["risk"].upper()}</span></td>'
                f'<td class="c">{u["score"]}</td>'
                f'<td class="url">{esc(u["url"])}</td>'
                f'<td>{esc(u["host"])}</td>'
                f'<td>{esc(u["ip"] or "—")}</td>'
                f'<td>{esc(u["scheme"])}</td>'
                f'<td>{esc(u["reasons"])}</td>'
                f'</tr>'
            )
        if not url_rows:
            url_rows.append('<tr><td colspan="7" style="color:#33cc33">Nenhuma URL encontrada.</td></tr>')

        findings_html = ''
        if findings:
            findings_html = '<ul class="findings">' + ''.join(
                f'<li>{esc(f)}</li>' for f in findings) + '</ul>'
        else:
            findings_html = '<p class="ok">Nenhum padrão suspeito detectado.</p>'

        eml_block = ''
        if eml_info:
            auth_list = ''.join(f'<li>{esc(a)}</li>' for a in eml_info['auth']) or '<li>(nenhum)</li>'
            att_list = ''.join(f'<li>{esc(a)}</li>' for a in eml_info['attachments']) or '<li>(nenhum)</li>'
            eml_block = f'''
<section>
  <h2>Cabeçalhos do e-mail (.eml)</h2>
  <table class="meta">
    <tr><th>De</th><td>{esc(eml_info["from"])}</td></tr>
    <tr><th>Para</th><td>{esc(eml_info["to"])}</td></tr>
    <tr><th>Assunto</th><td>{esc(eml_info["subject"])}</td></tr>
    <tr><th>Data</th><td>{esc(eml_info["date"])}</td></tr>
    <tr><th>Reply-To</th><td>{esc(eml_info["reply_to"])}</td></tr>
    <tr><th>Return-Path</th><td>{esc(eml_info["return_path"])}</td></tr>
  </table>
  <h3>Autenticação (SPF / DKIM / DMARC)</h3>
  <ul class="findings">{auth_list}</ul>
  <h3>Anexos</h3>
  <ul class="findings">{att_list}</ul>
</section>'''

        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhishScan — Relatório de Análise</title>
<style>
  :root {{
    --bg: #000000;
    --fg: #00ff00;
    --fg-dim: #33cc33;
    --border: #006600;
    --select: #003300;
    --orange: #ff8c00;
    --red: #ff4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px;
    background: var(--bg); color: var(--fg);
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px; line-height: 1.45;
  }}
  h1 {{
    margin: 0 0 4px; font-size: 22px; letter-spacing: 2px;
    color: var(--fg); border-bottom: 2px solid var(--border); padding-bottom: 8px;
  }}
  h2 {{
    margin: 28px 0 10px; font-size: 15px; color: var(--fg);
    border-left: 4px solid var(--fg); padding-left: 10px;
  }}
  h3 {{ margin: 14px 0 6px; font-size: 13px; color: var(--fg-dim); }}
  .header-sub {{ color: var(--fg-dim); margin-bottom: 20px; }}
  .risk-banner {{
    display: inline-block; padding: 8px 18px; margin: 12px 0 20px;
    font-size: 16px; font-weight: bold; border-radius: 4px;
    background: {risk_color}; color: #000;
  }}
  table {{
    width: 100%; border-collapse: collapse; margin: 8px 0 16px;
    border: 1px solid var(--border);
  }}
  th {{
    background: #001500; color: var(--fg); text-align: left;
    padding: 8px 10px; border-bottom: 1px solid var(--border);
    font-weight: bold; white-space: nowrap;
  }}
  td {{
    padding: 6px 10px; border-bottom: 1px solid #002200;
    vertical-align: top; word-break: break-word;
  }}
  tr:hover td {{ background: var(--select); }}
  td.c {{ text-align: center; white-space: nowrap; }}
  td.url {{ max-width: 320px; }}
  td.ctx {{ max-width: 280px; color: var(--fg-dim); font-size: 12px; }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-weight: bold; font-size: 11px; letter-spacing: 0.5px;
  }}
  table.meta {{ width: auto; min-width: 480px; }}
  table.meta th {{ width: 130px; background: #001500; }}
  .stats {{
    display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0 20px;
  }}
  .stat {{
    border: 1px solid var(--border); padding: 10px 16px; border-radius: 4px;
    min-width: 120px; background: #001a00;
  }}
  .stat .n {{ font-size: 22px; font-weight: bold; }}
  .stat .l {{ color: var(--fg-dim); font-size: 11px; }}
  ul.findings {{ margin: 6px 0; padding-left: 22px; }}
  ul.findings li {{ margin: 4px 0; }}
  .ok {{ color: var(--fg-dim); }}
  .legend {{
    margin-top: 28px; padding: 12px 16px; border: 1px solid var(--border);
    background: #001000; font-size: 12px;
  }}
  .legend span {{ margin-right: 18px; }}
  footer {{
    margin-top: 28px; padding-top: 12px; border-top: 1px solid var(--border);
    color: var(--fg-dim); font-size: 11px;
  }}
  @media print {{
    body {{ background: #fff; color: #000; }}
    th {{ background: #eee; color: #000; }}
  }}
</style>
</head>
<body>
  <h1>PHISHSCAN — RELATÓRIO DE ANÁLISE</h1>
  <div class="header-sub">Análise autorizada de conteúdo próprio · Tema Hacker</div>

  <div class="risk-banner">Risco geral: {esc(risk)}</div>

  <section>
    <h2>Resumo</h2>
    <table class="meta">
      <tr><th>Arquivo / URL</th><td>{src}</td></tr>
      <tr><th>Data / hora</th><td>{agora}</td></tr>
      <tr><th>Tamanho</th><td>{content_len:,} bytes</td></tr>
      <tr><th>Tipo</th><td>{esc(tipo)}</td></tr>
      <tr><th>User-Agent</th><td>{ua}</td></tr>
    </table>
    <div class="stats">
      <div class="stat"><div class="n" style="color:#ff4444">{n_alto}</div><div class="l">URL  risco ALTO</div></div>
      <div class="stat"><div class="n" style="color:#ff8c00">{n_medio}</div><div class="l">URL risco MÉDIO</div></div>
      <div class="stat"><div class="n" style="color:#00ff00">{n_baixo}</div><div class="l">URL risco BAIXO</div></div>
      <div class="stat"><div class="n">{len(emails)}</div><div class="l">E-mails</div></div>
      <div class="stat"><div class="n">{len(findings)}</div><div class="l">Achados</div></div>
    </div>
  </section>

  <section>
    <h2>E-mails encontrados ({len(emails)})</h2>
    <table>
      <thead>
        <tr>
          <th>E-mail</th><th>Ocorr.</th><th>Ofuscado</th><th>Suspeita</th><th>Contexto</th>
        </tr>
      </thead>
      <tbody>
        {''.join(email_rows)}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Links e URL ({len(urls)})</h2>
    <table>
      <thead>
        <tr>
          <th>Risco</th><th>Pts</th><th>URL</th><th>Domínio</th><th>IP</th><th>Esquema</th><th>Motivos</th>
        </tr>
      </thead>
      <tbody>
        {''.join(url_rows)}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Achados de conteúdo / ofuscação</h2>
    {findings_html}
  </section>

  {eml_block}

  <div class="legend">
    <strong>LEGENDA</strong><br><br>
    <span style="color:#ff4444">■ ALTO</span>
    <span style="color:#ff8c00">■ MÉDIO</span>
    <span style="color:#00ff00">■ BAIXO</span>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <span style="color:#00ff00">■ E-mail ofuscado</span>
    <span style="color:#ff8c00">■ E-mail não ofuscado</span>
  </div>

  <footer>
    Gerado por PhishScan · {agora}<br>
    Uso exclusivo para análise autorizada de conteúdo próprio.
  </footer>
</body>
</html>'''
        return html

    def export_report(self, fmt):
        if not self.results:
            messagebox.showwarning('Aviso', 'Execute um escaneamento primeiro.')
            return
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'phishscan_relatorio_{stamp}.{fmt}'
        path = filedialog.asksaveasfilename(
            defaultextension=f'.{fmt}',
            initialfile=default_name,
            filetypes=[
                ('Texto' if fmt == 'txt' else 'HTML', f'*.{fmt}'),
                ('Todos os arquivos', '*.*'),
            ])
        if not path:
            return
        r = self.results
        if fmt == 'txt':
            data = r['report']
        else:
            data = self._build_html_report(
                r['url'], r['emails'], r['findings'], r.get('eml'),
                r.get('is_html', False),
                bool(r.get('eml')),
                r['risk'], r.get('content_len', 0))
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(data)
            messagebox.showinfo('Exportado', f'Relatório salvo em:\n{path}')
            self.status.set(f'Relatório exportado: {path}')
        except OSError as e:
            messagebox.showerror('Erro', str(e))

    def export_both(self):
        """Salva TXT e HTML de uma vez, com formatação profissional."""
        if not self.results:
            messagebox.showwarning('Aviso', 'Execute um escaneamento primeiro.')
            return
        folder = filedialog.askdirectory(title='Escolha a pasta para salvar os relatórios')
        if not folder:
            return
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        r = self.results
        txt_path = os.path.join(folder, f'phishscan_relatorio_{stamp}.txt')
        html_path = os.path.join(folder, f'phishscan_relatorio_{stamp}.html')
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(r['report'])
            html_data = self._build_html_report(
                r['url'], r['emails'], r['findings'], r.get('eml'),
                r.get('is_html', False),
                bool(r.get('eml')),
                r['risk'], r.get('content_len', 0))
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_data)
            messagebox.showinfo(
                'Exportado',
                f'Relatórios salvos:\n\n{txt_path}\n\n{html_path}')
            self.status.set(f'Relatórios exportados: {os.path.basename(txt_path)} + .html')
        except OSError as e:
            messagebox.showerror('Erro', str(e))

    def export_full_html(self):
        """Exporta HTML completo com Conteúdo, Links, E-mails, Análise, .eml, Relatório e Scraper."""
        content = self._raw_content or self.txt_content.get('1.0', 'end-1c')
        has_scan = bool(self.results)
        has_scraper = bool(self.scraper_urls)
        has_content = bool((content or '').strip())
        if not (has_scan or has_scraper or has_content):
            messagebox.showwarning(
                'Aviso',
                'Não há dados para exportar.\n'
                'Carregue conteúdo, execute um escaneamento ou use o Scraper HTML.')
            return
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = filedialog.asksaveasfilename(
            defaultextension='.html',
            initialfile=f'phishscan_completo_{stamp}.html',
            filetypes=[('HTML', '*.html'), ('Todos', '*.*')],
        )
        if not path:
            return
        try:
            html = self._build_full_html_export()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            messagebox.showinfo('Exportado', f'HTML completo salvo em:\n{path}')
            self.status.set(f'HTML completo exportado: {path}')
        except OSError as e:
            messagebox.showerror('Erro', str(e))

    def _build_full_html_export(self):
        """Monta HTML com todas as áreas da análise + scraper + conteúdo."""
        esc = html_mod.escape
        agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        r = self.results or {}
        urls = r.get('url') or []
        emails = r.get('emails') or []
        findings = r.get('findings') or []
        eml_info = r.get('eml')
        risk = r.get('risk', '—')
        risk_color = {'ALTO': '#ff4444', 'MÉDIO': '#ff8c00', 'BAIXO': '#00ff00'}.get(risk, '#00ff00')
        # Preferir conteúdo bruto completo (não a prévia truncada da aba)
        content = self._raw_content or self.txt_content.get('1.0', 'end-1c') or ''
        # limita conteúdo muito grande no HTML (mantém legível)
        content_export = content
        content_truncated = False
        if len(content_export) > 200000:
            content_export = content_export[:200000]
            content_truncated = True

        n_alto = sum(1 for u in urls if u['risk'] == 'alto')
        n_medio = sum(1 for u in urls if u['risk'] == 'medio')
        n_baixo = sum(1 for u in urls if u['risk'] == 'baixo')

        # --- Links ---
        url_rows = []
        for u in sorted(urls, key=lambda x: -x['score']):
            rc = {'alto': '#ff4444', 'medio': '#ff8c00', 'baixo': '#00ff00'}[u['risk']]
            url_rows.append(
                f'<tr style="color:{rc}">'
                f'<td><span class="badge" style="background:{rc};color:#000">{u["risk"].upper()}</span></td>'
                f'<td class="c">{u["score"]}</td>'
                f'<td class="url">{esc(u["url"])}</td>'
                f'<td>{esc(u["host"])}</td>'
                f'<td>{esc(u["ip"] or "—")}</td>'
                f'<td>{esc(u["scheme"])}</td>'
                f'<td>{esc(u["reasons"])}</td>'
                f'</tr>'
            )
        if not url_rows:
            url_rows.append('<tr><td colspan="7" class="ok">Nenhuma URL da análise.</td></tr>')

        # --- E-mails (ofuscado = verde | não ofuscado = abóbora #ff8c00) ---
        email_rows = []
        for e in sorted(emails, key=lambda x: -x['count']):
            # cor de abóbora para e-mails NÃO ofuscados (igual legenda da GUI)
            cls = 'email-obf' if e['obfuscated'] else 'email-norm'
            color = '#00ff00' if e['obfuscated'] else '#ff8c00'
            obf = 'SIM' if e['obfuscated'] else 'não'
            email_rows.append(
                f'<tr class="{cls}" style="color:{color}">'
                f'<td>{esc(e["email"])}</td>'
                f'<td class="c">{e["count"]}</td>'
                f'<td class="c">{obf}</td>'
                f'<td>{esc(e["suspicious"] or "—")}</td>'
                f'<td class="ctx">{esc(e.get("context") or "")}</td>'
                f'</tr>'
            )
        if not email_rows:
            email_rows.append('<tr><td colspan="5" class="ok">Nenhum e-mail encontrado.</td></tr>')

        # --- Achados ---
        if findings:
            findings_html = '<ul class="findings">' + ''.join(
                f'<li>{esc(f)}</li>' for f in findings) + '</ul>'
        else:
            findings_html = '<p class="ok">Nenhum padrão suspeito detectado (ou escaneamento não executado).</p>'

        # --- EML + e-mails extraídos do conteúdo ---
        eml_block = ''
        # tabela de e-mails encontrados (sempre, com cor de abóbora)
        eml_email_rows = []
        for e in sorted(emails, key=lambda x: -x['count']):
            color = '#00ff00' if e['obfuscated'] else '#ff8c00'
            obf = 'SIM' if e['obfuscated'] else 'não'
            eml_email_rows.append(
                f'<tr style="color:{color}">'
                f'<td>{esc(e["email"])}</td>'
                f'<td class="c">{e["count"]}</td>'
                f'<td class="c">{obf}</td>'
                f'<td>{esc(e["suspicious"] or "—")}</td>'
                f'<td class="ctx">{esc(e.get("context") or "")}</td>'
                f'</tr>'
            )
        if not eml_email_rows:
            eml_email_rows.append(
                '<tr><td colspan="5" class="ok">Nenhum e-mail encontrado no conteúdo.</td></tr>')
        emails_table = f'''
  <h3>E-mails encontrados no conteúdo ({len(emails)})</h3>
  <p class="ok">
    <span style="color:#00ff00">■ Ofuscado</span>
    &nbsp;&nbsp;
    <span style="color:#ff8c00">■ Não ofuscado (cor de abóbora)</span>
  </p>
  <table>
    <thead>
      <tr>
        <th>E-mail</th><th>Ocorr.</th><th>Ofuscado</th><th>Suspeita</th><th>Contexto</th>
      </tr>
    </thead>
    <tbody>
      {''.join(eml_email_rows)}
    </tbody>
  </table>'''

        if eml_info:
            auth_list = ''.join(f'<li>{esc(a)}</li>' for a in eml_info['auth']) or '<li>(nenhum)</li>'
            att_list = ''.join(f'<li>{esc(a)}</li>' for a in eml_info['attachments']) or '<li>(nenhum)</li>'
            findings_eml = ''.join(
                f'<li>{esc(f)}</li>' for f in (eml_info.get('findings') or [])
            ) or '<li class="ok">(nenhum)</li>'
            body_preview = ''
            plain = (eml_info.get('body_plain') or '')[:3000]
            html_body = (eml_info.get('body_html') or '')[:3000]
            if plain or html_body:
                body_preview = '<h3>Prévia do corpo</h3>'
                if plain:
                    body_preview += f'<pre class="content">{esc(plain)}</pre>'
                if html_body:
                    body_preview += (
                        '<p class="ok">HTML do corpo (colorido):</p>'
                        f'<pre class="content">{self._colorize_html_for_export(html_body)}</pre>'
                    )
            eml_block = f'''
<section id="eml">
  <h2>E-mail (.eml)</h2>
  <table class="meta">
    <tr><th>De</th><td>{esc(eml_info["from"])}</td></tr>
    <tr><th>Para</th><td>{esc(eml_info["to"])}</td></tr>
    <tr><th>Assunto</th><td>{esc(eml_info["subject"])}</td></tr>
    <tr><th>Data</th><td>{esc(eml_info["date"])}</td></tr>
    <tr><th>Reply-To</th><td>{esc(eml_info["reply_to"])}</td></tr>
    <tr><th>Return-Path</th><td>{esc(eml_info["return_path"])}</td></tr>
  </table>
  <h3>Autenticação (SPF / DKIM / DMARC)</h3>
  <ul class="findings">{auth_list}</ul>
  <h3>Anexos</h3>
  <ul class="findings">{att_list}</ul>
  <h3>Achados do .eml</h3>
  <ul class="findings">{findings_eml}</ul>
  {body_preview}
  {emails_table}
</section>'''
        else:
            eml_block = f'''
<section id="eml">
  <h2>E-mail (.eml)</h2>
  <p class="ok">Nenhum arquivo .eml analisado nesta sessão.
  Abaixo estão os e-mails extraídos do conteúdo escaneado.</p>
  {emails_table}
</section>'''

        # --- Scraper (sem file://) ---
        scraper_rows = []
        for item in self.scraper_urls:
            url_show = self._safe_display_path(item['url'])
            if url_show == '—' or str(item['url']).lower().startswith('file:'):
                continue  # não exporta caminhos locais
            color = '#00ff00' if item['tipo'] == 'absoluta' else '#ff8c00'
            scraper_rows.append(
                f'<tr style="color:{color}">'
                f'<td class="url">{esc(url_show)}</td>'
                f'<td>{esc(item["tipo"])}</td>'
                f'<td class="ctx">{esc(item.get("original") or "")}</td>'
                f'</tr>'
            )
        if not scraper_rows:
            scraper_rows.append('<tr><td colspan="3" class="ok">Nenhuma URL no Scraper HTML.</td></tr>')
        # Base Scraper: nunca file://
        raw_base = self.scraper_base_url or ''
        if str(raw_base).lower().startswith('file:') or re.match(r'^[A-Za-z]:[\\/]', str(raw_base)):
            raw_base = ''
        scraper_base = esc(self._safe_display_path(raw_base) if raw_base else '—')

        # --- Relatório texto ---
        report_txt = esc(r.get('report') or '(Execute um escaneamento para gerar o relatório.)')

        # --- Conteúdo (colorido: tags / atributos / comentários / e-mails) ---
        trunc_note = ''
        if content_truncated:
            trunc_note = '<p class="ok">Conteúdo truncado em 200.000 caracteres para o HTML.</p>'
        content_block = self._colorize_html_for_export(content_export)

        # Arquivo / URL: sem file:// nem caminho Windows
        raw_src = self.filepath or ''
        if str(raw_src).lower().startswith('file:') or re.match(r'^[A-Za-z]:[\\/]', str(raw_src or '')):
            raw_src = raw_base or os.path.basename(str(self.filepath or '')) or '(conteúdo colado / scraper)'
        src = esc(self._safe_display_path(raw_src) if raw_src else '(conteúdo colado / scraper)')
        ua = esc(self.selected_ua)

        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhishScan — Exportação Completa</title>
<style>
  :root {{
    --bg: #000000; --fg: #00ff00; --fg-dim: #33cc33;
    --border: #006600; --select: #003300; --orange: #ff8c00; --red: #ff4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px; background: var(--bg); color: var(--fg);
    font-family: Consolas, "Courier New", monospace; font-size: 13px; line-height: 1.45;
  }}
  h1 {{ margin: 0 0 4px; font-size: 22px; letter-spacing: 2px;
        border-bottom: 2px solid var(--border); padding-bottom: 8px; }}
  h2 {{ margin: 28px 0 10px; font-size: 15px; border-left: 4px solid var(--fg); padding-left: 10px; }}
  h3 {{ margin: 14px 0 6px; font-size: 13px; color: var(--fg-dim); }}
  .nav {{
    display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 24px;
  }}
  .nav a {{
    color: #000; background: var(--fg); text-decoration: none;
    padding: 6px 12px; border-radius: 3px; font-weight: bold; font-size: 12px;
  }}
  .nav a:hover {{ background: var(--orange); }}
  .risk-banner {{
    display: inline-block; padding: 8px 18px; margin: 12px 0 20px;
    font-size: 16px; font-weight: bold; border-radius: 4px;
    background: {risk_color}; color: #000;
  }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 16px; border: 1px solid var(--border); }}
  th {{ background: #001500; color: var(--fg); text-align: left; padding: 8px 10px;
       border-bottom: 1px solid var(--border); white-space: nowrap; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #002200; vertical-align: top; word-break: break-word; }}
  tr:hover td {{ background: var(--select); }}
  td.c {{ text-align: center; white-space: nowrap; }}
  td.url {{ max-width: 420px; }}
  td.ctx {{ max-width: 280px; color: var(--fg-dim); font-size: 12px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-weight: bold; font-size: 11px; }}
  table.meta {{ width: auto; min-width: 480px; }}
  table.meta th {{ width: 130px; }}
  .stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0 20px; }}
  .stat {{ border: 1px solid var(--border); padding: 10px 16px; border-radius: 4px;
           min-width: 120px; background: #001a00; }}
  .stat .n {{ font-size: 22px; font-weight: bold; }}
  .stat .l {{ color: var(--fg-dim); font-size: 11px; }}
  ul.findings {{ margin: 6px 0; padding-left: 22px; }}
  ul.findings li {{ margin: 4px 0; }}
  .ok {{ color: var(--fg-dim); }}
  pre.content {{
    background: #001000; border: 1px solid var(--border); padding: 12px;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word;
    max-height: 600px; font-size: 12px;
  }}
  /* Coloração do conteúdo (igual à aba Conteúdo da GUI) */
  .hc-tag {{ color: #66ff66; }}
  .hc-attr {{ color: #ff8c00; }}   /* abóbora — atributos */
  .hc-comment {{ color: #33aa33; }}
  .hc-text {{ color: #00ff00; }}
  .hc-email-norm {{ color: #ff8c00; font-weight: bold; }}  /* abóbora */
  .hc-email-obf {{ color: #00ff00; font-weight: bold; }}
  /* E-mails na tabela: ofuscado = verde | não ofuscado = abóbora */
  .email-obf {{ color: #00ff00; }}
  .email-norm {{ color: #ff8c00; }}
  pre.report {{
    background: #001000; border: 1px solid var(--border); padding: 12px;
    overflow-x: auto; white-space: pre-wrap; font-size: 12px;
  }}
  footer {{
    margin-top: 28px; padding-top: 12px; border-top: 1px solid var(--border);
    color: var(--fg-dim); font-size: 11px;
  }}
  @media print {{
    body {{ background: #fff; color: #000; }}
    th {{ background: #eee; color: #000; }}
    .nav a {{ background: #ccc; }}
    pre.content, pre.report {{ max-height: none; }}
  }}
</style>
</head>
<body>
  <h1>PHISHSCAN — EXPORTAÇÃO COMPLETA</h1>
  <div style="color:var(--fg-dim);margin-bottom:8px">Todas as áreas · Tema Hacker · {agora}</div>
  <div class="risk-banner">Risco geral: {esc(risk)}</div>

  <nav class="nav">
    <a href="#resumo">Resumo</a>
    <a href="#conteudo">Conteúdo</a>
    <a href="#links">Links e URL</a>
    <a href="#emails">E-mails</a>
    <a href="#analise">Análise</a>
    <a href="#eml">E-mail (.eml)</a>
    <a href="#scraper">Scraper HTML</a>
    <a href="#relatorio">Relatório</a>
  </nav>

  <section id="resumo">
    <h2>Resumo</h2>
    <table class="meta">
      <tr><th>Arquivo / URL</th><td>{src}</td></tr>
      <tr><th>Data / hora</th><td>{agora}</td></tr>
      <tr><th>User-Agent</th><td>{ua}</td></tr>
      <tr><th>Base Scraper</th><td>{scraper_base}</td></tr>
    </table>
    <div class="stats">
      <div class="stat"><div class="n" style="color:#ff4444">{n_alto}</div><div class="l">URL risco ALTO</div></div>
      <div class="stat"><div class="n" style="color:#ff8c00">{n_medio}</div><div class="l">URL risco MÉDIO</div></div>
      <div class="stat"><div class="n" style="color:#00ff00">{n_baixo}</div><div class="l">URL risco BAIXO</div></div>
      <div class="stat"><div class="n">{len(emails)}</div><div class="l">E-mails</div></div>
      <div class="stat"><div class="n">{len(findings)}</div><div class="l">Achados</div></div>
      <div class="stat"><div class="n">{len(self.scraper_urls)}</div><div class="l">Scraper URL</div></div>
    </div>
  </section>

  <section id="conteudo">
    <h2>Conteúdo</h2>
    {trunc_note}
    <p class="ok">
      <span style="color:#66ff66">■ Tags HTML</span>
      &nbsp;&nbsp;
      <span style="color:#ff8c00">■ Atributos (abóbora)</span>
      &nbsp;&nbsp;
      <span style="color:#33aa33">■ Comentários</span>
      &nbsp;&nbsp;
      <span style="color:#ff8c00">■ E-mail (abóbora)</span>
      &nbsp;&nbsp;
      <span style="color:#00ff00">■ E-mail ofuscado / texto</span>
    </p>
    <pre class="content">{content_block}</pre>
  </section>

  <section id="links">
    <h2>Links e URL ({len(urls)})</h2>
    <table>
      <thead>
        <tr>
          <th>Risco</th><th>Pts</th><th>URL</th><th>Domínio</th><th>IP</th><th>Esquema</th><th>Motivos</th>
        </tr>
      </thead>
      <tbody>
        {''.join(url_rows)}
      </tbody>
    </table>
  </section>

  <section id="emails">
    <h2>E-mails ({len(emails)})</h2>
    <p class="ok">
      <span style="color:#00ff00">■ Ofuscado</span>
      &nbsp;&nbsp;
      <span style="color:#ff8c00">■ Não ofuscado (cor de abóbora)</span>
    </p>
    <table>
      <thead>
        <tr>
          <th>E-mail</th><th>Ocorr.</th><th>Ofuscado</th><th>Suspeita</th><th>Contexto</th>
        </tr>
      </thead>
      <tbody>
        {''.join(email_rows)}
      </tbody>
    </table>
  </section>

  <section id="analise">
    <h2>Análise / Ofuscação</h2>
    {findings_html}
  </section>

  {eml_block}

  <section id="scraper">
    <h2>Scraper HTML ({len(self.scraper_urls)})</h2>
    <p class="ok">Base: {scraper_base}</p>
    <table>
      <thead>
        <tr><th>URL</th><th>Tipo</th><th>Original</th></tr>
      </thead>
      <tbody>
        {''.join(scraper_rows)}
      </tbody>
    </table>
  </section>

  <section id="relatorio">
    <h2>Relatório (texto)</h2>
    <pre class="report">{report_txt}</pre>
  </section>

  <footer>
    Gerado por PhishScan · Exportação completa · {agora}<br>
    Uso exclusivo para análise autorizada de conteúdo próprio.
  </footer>
</body>
</html>'''
        return html

    # ------------------------------ e-mail --------------------------------
    def send_report_mail(self):
        if not self.results:
            messagebox.showwarning('Aviso', 'Execute um escaneamento primeiro.')
            return
        v = self.mail_vars
        host, porta = v['servidor'].get().strip(), v['porta'].get().strip()
        user, senha = v['user'].get().strip(), v['senha'].get().strip()
        to_addr, subject = v['to'].get().strip(), v['subject'].get().strip()
        if not all([host, porta, user, senha, to_addr]):
            messagebox.showwarning('Aviso', 'Preencha todos os campos SMTP.')
            return
        try:
            porta = int(porta)
        except ValueError:
            messagebox.showerror('Erro', 'Porta inválida.')
            return
        self.status.set('Enviando e-mail...')
        threading.Thread(target=self._mail_worker,
                         args=(host, porta, user, senha, to_addr, subject),
                         daemon=True).start()

    def _mail_worker(self, host, porta, user, senha, to_addr, subject):
        try:
            if self.var_ssl.get():
                server = smtplib.SMTP_SSL(
                    host, porta, timeout=25,
                    context=ssl_mod.create_default_context())
            else:
                server = smtplib.SMTP(host, porta, timeout=25)
                if self.var_starttls.get():
                    server.starttls(context=ssl_mod.create_default_context())
            server.login(user, senha)
            msg = (f'From: {user}\nTo: {to_addr}\nSubject: {subject}\n'
                   'MIME-Version: 1.0\n'
                   'Content-Type: text/plain; charset=utf-8\n\n'
                   + self.results['report'])
            server.sendmail(user, [to_addr], msg.encode('utf-8'))
            server.quit()
            self.root.after(0, lambda: messagebox.showinfo(
                'Enviado', 'Relatório enviado por e-mail.'))
            self.root.after(0, lambda: self.status.set('Relatório enviado.'))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                'Falha no envio', str(e)))
            self.root.after(0, lambda: self.status.set('Falha no envio.'))

    # --------------------------- utilidades -------------------------------
    def copy_url(self):
        sel = self.tree.selection()
        if not sel:
            return
        url = self.tree.item(sel[0], 'values')[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.status.set('URL copiada.')

    def copy_email(self):
        sel = self.tree_emails.selection()
        if not sel:
            return
        email = self.tree_emails.item(sel[0], 'values')[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(email)
        self.status.set('E-mail copiado.')

    def open_browser(self):
        sel = self.tree.selection()
        if not sel:
            return
        url = self.tree.item(sel[0], 'values')[0]
        if messagebox.askyesno(
                'Abrir no navegador',
                f'URL analisada:\n{url}\n\nAbrir mesmo assim? '
                'Use apenas em ambiente controlado.'):
            webbrowser.open(url)

    def show_about(self):
        messagebox.showinfo(
            'Sobre',
            'PhishScan Pro — E-mail · Site · HTML\n'
            '====================================\n\n'
            'Ferramenta de análise autorizada de conteúdo próprio.\n'
            'Detecta indicadores de phishing, links maliciosos,\n'
            'e-mails ofuscados e técnicas de ofuscação.\n\n'
            'O QUE ANALISA\n'
            '• Arquivos .txt, .html, .htm e .eml\n'
            '• Conteúdo colado da área de transferência\n'
            '• Páginas ao vivo (URL http/https)\n\n'
            'SCRAPER HTML\n'
            '• Extrai TODAS as URL de uma página (href, src, etc.)\n'
            '• Tenta também index.html quando a URL termina em /\n'
            '• Filtro de pesquisa em tempo real\n'
            '• Copiar, abrir no navegador ou enviar para análise\n\n'
            'E-MAIL (.eml)\n'
            '• Cabeçalhos: From, To, Subject, Date,\n'
            '  Reply-To, Return-Path\n'
            '• Autenticação: SPF, DKIM, DMARC, X-Spam-Status\n'
            '• Reply-To diferente do remetente (golpe de resposta)\n'
            '• Anexos (nome, tipo e tamanho)\n'
            '• Corpo em texto e HTML\n\n'
            'LINKS E URL\n'
            '• Extração de todas as URL do conteúdo\n'
            '• Pontuação de risco (alto / médio / baixo)\n'
            '• HTTP sem TLS, IP no host, encurtadores\n'
            '• Punycode, subdomínios excessivos, porta estranha\n'
            '• Palavras de phishing (login, banco, PIX, etc.)\n'
            '• Resolução DNS (domínio que não resolve)\n\n'
            'E-MAILS NO CONTEÚDO\n'
            '• Extração de e-mails normais e ofuscados\n'
            '  (ex.: usuario [at] dominio [dot] com)\n'
            '• Detecção de typosquatting e domínios suspeitos\n\n'
            'OFUSCAÇÃO E CONTEÚDO\n'
            '• eval(), unescape(), fromCharCode, Base64\n'
            '• Meta refresh, redirecionamentos JS\n'
            '• Formulários, campos de senha, iframes ocultos\n'
            '• JavaScript embutido\n\n'
            'RELATÓRIOS E ENVIO\n'
            '• Exportar .txt e .html formatados (com cores)\n'
            '• Exportar ambos de uma vez\n'
            '• Envio do relatório por SMTP\n\n'
            'USER-AGENT\n'
            '• Carregar lista (useragent.txt)\n'
            '• Adicionar, remover e selecionar UA\n'
            '• Usado nas requisições de URL ao vivo\n\n'
            'LEGENDA — E-mails\n'
            '  ■ Verde   = e-mail ofuscado\n'
            '  ■ Laranja = e-mail não ofuscado\n\n'
            'LEGENDA — Links e URL\n'
            '  ■ Vermelho = risco alto\n'
            '  ■ Laranja  = risco médio\n'
            '  ■ Verde    = risco baixo\n\n'
            'Uso exclusivo para análise autorizada de conteúdo próprio.')


def main():
    root = tk.Tk()
    PhishScanApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
