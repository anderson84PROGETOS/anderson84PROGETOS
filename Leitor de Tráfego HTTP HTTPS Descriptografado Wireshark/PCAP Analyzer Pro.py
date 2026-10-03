import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import re
import base64
import logging
import warnings
import asyncio
import subprocess
import time
from datetime import datetime
from collections import Counter
from urllib.parse import unquote_plus, parse_qs


# ============================================================
# OCULTAR JANELA DO TSHARK NO WINDOWS
# ============================================================

if os.name == "nt":

    _original_popen = subprocess.Popen

    class HiddenPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs["startupinfo"] = startupinfo
            kwargs["creationflags"] = (
                kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
            )
            super().__init__(*args, **kwargs)

    subprocess.Popen = HiddenPopen

    _original_create_subprocess_exec = asyncio.create_subprocess_exec

    async def hidden_create_subprocess_exec(program, *args, **kwargs):
        if "tshark" in str(program).lower():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs["startupinfo"] = startupinfo
            kwargs["creationflags"] = (
                kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
            )
        return await _original_create_subprocess_exec(program, *args, **kwargs)

    asyncio.create_subprocess_exec = hidden_create_subprocess_exec


logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
logging.getLogger("scapy.loading").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

HAS_SCAPY = False
HAS_HTTP = False
HAS_TLS = False
HAS_PYSHARK = False

try:
    from scapy.all import rdpcap, IP, TCP, UDP, Raw, DNS, DNSQR, conf
    conf.verb = 0
    HAS_SCAPY = True
    try:
        from scapy.layers.http import HTTPRequest
        HAS_HTTP = True
    except Exception:
        pass
    try:
        from scapy.layers.tls.all import TLS
        HAS_TLS = True
    except Exception:
        try:
            from scapy.layers.tls import TLS
            HAS_TLS = True
        except Exception:
            pass
except Exception:
    pass

try:
    import pyshark
    HAS_PYSHARK = True
except ImportError:
    pass


KEYWORDS = [
    b"password", b"passwd", b"pass", b"senha", b"pwd", b"user", b"username",
    b"login", b"token", b"api_key", b"apikey", b"secret", b"auth",
    b"authorization", b"credential", b"cookie", b"session", b"jwt", b"bearer",
    b"agencia", b"conta", b"dac", b"portal", b"tipologon", b"pre-login",
    b"cpf", b"cnpj", b"email", b"mail", b"chave", b"pin", b"otp",
    b"client_id", b"client_secret", b"access_token", b"refresh_token",
    b"private_key", b"ssh-rsa", b"BEGIN RSA", b"BEGIN PRIVATE",
    b"agn", b"cta", b"digcta",
]

PATTERNS = {
    "HTTP Basic Auth": re.compile(rb"(?i)authorization:\s*basic\s+([a-z0-9+/=]+)"),
    "Bearer Token":    re.compile(rb"(?i)authorization:\s*bearer\s+([a-z0-9._\-]+)"),
    "FTP":             re.compile(rb"USER\s+(\S+)\s*[\r\n]+PASS\s+(\S+)", re.I),
    "Telnet":          re.compile(rb"(?i)login[: ]+\s*(\S+).{0,80}password[: ]+\s*(\S+)"),
    "SMTP AUTH":       re.compile(rb"AUTH\s+LOGIN[\r\n]+([^\r\n]+)[\r\n]+([^\r\n]+)"),
    "POP3":            re.compile(rb"(?i)user\s+(\S+)[\r\n]+pass\s+(\S+)"),
    "IMAP LOGIN":      re.compile(rb"(?i)LOGIN\s+(\S+)\s+(\S+)"),
    "LDAP Bind":       re.compile(rb"(?i)binddn[=:\s]+(\S+)[\r\n\s]*bindpw[=:\s]+(\S+)"),
    "POST creds":      re.compile(rb"(?i)(?:username|user|login|email|usuario)=([^&\s]+)&(?:password|pass|pwd|senha)=([^&\s]+)"),
    "JSON Login":      re.compile(rb'(?i)"(?:username|user|login|email)"\s*:\s*"([^"]+)"\s*,\s*"(?:password|pass|senha)"\s*:\s*"([^"]+)"'),
    "Form user/pass":  re.compile(rb"(?i)(?:user|login|usuario|email)=([^&\s]+).{0,40}(?:pass|pwd|senha)=([^&\s]+)"),
    "NTLM":            re.compile(rb"(?i)NTLMSSP"),
    "API Key":         re.compile(rb"(?i)(?:api[_-]?key|apikey|x-api-key)[=:\s]+([a-zA-Z0-9_\-]{16,})"),
}

FORM_ITEM_RE = re.compile(rb"([a-zA-Z0-9_.%-]+)=([^&\s]*)")
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def find_tshark():
    if os.name == "posix":
        path = os.popen("which tshark").read().strip()
        if path:
            return path
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "tshark.exe" if os.name == "nt" else "tshark")
        if os.path.exists(candidate):
            return candidate
    possible = [
        os.path.join(os.getenv("PROGRAMFILES", ""), "Wireshark", "tshark.exe"),
        os.path.join(os.getenv("PROGRAMFILES(X86)", ""), "Wireshark", "tshark.exe"),
        os.path.join(os.getenv("SYSTEMDRIVE", "C:"), "Wireshark", "tshark.exe"),
    ]
    for p in possible:
        if os.path.exists(p):
            return p
    return None


def decode_payload(payload: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return payload.decode(enc)
        except Exception:
            continue
    return repr(payload)


def clean_ansi(text: str) -> str:
    text = ANSI_ESCAPE.sub('', text)
    text = re.sub(r'\|\|?[0-9]*m', '', text)
    text = re.sub(r'\[0m|\[1m|\[0;1m', '', text)
    return text.strip()


def data_br(ts):
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def format_eta(seconds):
    if seconds is None or seconds < 0 or seconds > 86400:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class PCAPAnalyzer:
    def __init__(self, path: str, sslkeylog: str = None, status_callback=None, progress_callback=None):
        self.path = path
        self.sslkeylog = sslkeylog
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.packets = None
        self.creds = []
        self.form_data = []
        self.form_items_raw = []
        self.form_items_classic = []
        self.dns_queries = []
        self.sni_hosts = set()
        self.http_requests = []
        self.http_headers = []
        self.ip_counter = Counter()
        self.proto_counter = Counter()
        self.keyword_hits = []
        self.start_time = None
        self.end_time = None
        self.total = 0
        self._start_ts = None

    def _update_status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

    def _update_progress(self, percent, eta_sec=None):
        """Calcula ETA automaticamente com base no tempo real decorrido"""
        if self.progress_callback:
            if eta_sec is None and self._start_ts and percent > 2:
                elapsed = time.time() - self._start_ts
                total_estimated = elapsed / (percent / 100.0)
                remaining = total_estimated - elapsed
                if remaining < 0:
                    remaining = 0
                elif remaining > 86400:
                    remaining = None
                eta_sec = remaining
            self.progress_callback(percent, eta_sec)

    def analyze(self):
        self._start_ts = time.time()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception:
            pass

        self._update_status("Carregando pacotes com Scapy...")
        self._update_progress(2)

        if HAS_SCAPY:
            self._analyze_scapy()
        self._update_progress(55)

        self._update_status("Extraindo Form Items Classic (PyShark)...")
        if HAS_PYSHARK:
            self._analyze_form_items_classic()
        self._update_progress(75)

        if HAS_PYSHARK:
            self._analyze_http_headers_pyshark()
        self._update_progress(92)

        self._update_status("Processando formulários e credenciais...")
        self._forms_to_creds()
        self._update_progress(100, 0)  # força ETA = 00:00
        self._update_status("Análise concluída!")

    def _analyze_scapy(self):
        self.packets = rdpcap(self.path)
        self.total = len(self.packets)
        if self.total == 0:
            return
        self.start_time = data_br(self.packets[0].time)
        self.end_time = data_br(self.packets[-1].time)

        total = len(self.packets)

        for i, pkt in enumerate(self.packets):
            if i % 300 == 0 or i == total - 1:
                pct = 2 + int((i / total) * 53)  # 2% → 55%
                self._update_status(f"Scapy: processando pacote {i}/{total}...")
                self._update_progress(pct)  # ETA calculado automaticamente
            self._process_packet(pkt)

    def _process_packet(self, pkt):
        src = dst = ""
        if pkt.haslayer(IP):
            src, dst = pkt[IP].src, pkt[IP].dst
            self.ip_counter[src] += 1
            self.ip_counter[dst] += 1

        if pkt.haslayer(TCP):
            self.proto_counter["TCP"] += 1
        elif pkt.haslayer(UDP):
            self.proto_counter["UDP"] += 1
        elif pkt.haslayer("ICMP"):
            self.proto_counter["ICMP"] += 1
        elif pkt.haslayer("ARP"):
            self.proto_counter["ARP"] += 1
        else:
            self.proto_counter["Other"] += 1

        if pkt.haslayer(DNSQR):
            try:
                qname = pkt[DNSQR].qname.decode(errors="ignore").rstrip(".")
                self.dns_queries.append((qname, pkt[DNSQR].qtype))
            except Exception:
                pass

        if HAS_TLS and pkt.haslayer(TLS):
            try:
                tls = pkt[TLS]
                if hasattr(tls, "msg") and tls.msg:
                    for msg in tls.msg:
                        if hasattr(msg, "ext") and msg.ext:
                            for ext in msg.ext:
                                if hasattr(ext, "servernames") and ext.servernames:
                                    for sn in ext.servernames:
                                        if hasattr(sn, "servername"):
                                            self.sni_hosts.add(sn.servername.decode(errors="ignore"))
            except Exception:
                pass

        if pkt.haslayer(Raw):
            payload = bytes(pkt[Raw].load)
            self._search_credentials(pkt, payload)
            self._search_keywords(payload)
            self._search_forms_scapy(pkt, payload, src, dst)
            self._extract_http_headers(pkt, payload, src, dst)

        if HAS_HTTP and pkt.haslayer(HTTPRequest):
            try:
                req = pkt[HTTPRequest]
                host = req.Host.decode(errors="ignore") if req.Host else ""
                method = req.Method.decode(errors="ignore") if req.Method else ""
                uri = req.Path.decode(errors="ignore") if req.Path else ""
                ua = req.User_Agent.decode(errors="ignore") if req.User_Agent else ""
                self.http_requests.append((src, dst, method, host, uri, ua))
            except Exception:
                pass

    def _extract_http_headers(self, pkt, payload: bytes, src: str, dst: str):
        try:
            text = payload.decode("utf-8", errors="ignore")
            if not (text.startswith(("GET ", "POST ", "PUT ", "HEAD ", "OPTIONS ", "DELETE ", "PATCH ", "HTTP/"))):
                return
            if len(text) > 12000:
                text = text[:12000] + "\n... (truncado)"
            self.http_headers.append({
                "timestamp": data_br(pkt.time),
                "src": src,
                "dst": dst,
                "header": text.strip()
            })
        except Exception:
            pass

    def _search_forms_scapy(self, pkt, payload: bytes, src: str, dst: str):
        try:
            text = payload.decode("utf-8", errors="ignore")
            if "\r\n\r\n" in text:
                body = text.split("\r\n\r\n", 1)[1].strip()
            else:
                body = text.strip()
            if "=" not in body or ("&" not in body and "usuario." not in body.lower() and "agn=" not in body.lower()):
                return
            body = body.split("\n")[0].split("\r")[0]
            items = []
            try:
                parsed = parse_qs(body, keep_blank_values=True)
                for key, values in parsed.items():
                    items.append((key, values[0] if values else ""))
            except Exception:
                for m in FORM_ITEM_RE.finditer(body.encode()):
                    key = unquote_plus(m.group(1).decode(errors="ignore"))
                    value = unquote_plus(m.group(2).decode(errors="ignore"))
                    if key:
                        items.append((key, value))
            if items:
                self.form_data.append({
                    "timestamp": data_br(pkt.time),
                    "src": src,
                    "dst": dst,
                    "items": items,
                    "raw_body": body
                })
        except Exception:
            pass

    def _analyze_http_headers_pyshark(self):
        tshark = find_tshark()
        if not tshark:
            self._update_status("tshark não encontrado para Cabeçalhos HTTP")
            return

        KEYWORDS_LOCAL = [
            "username", "password", "passwd", "senha", "user=", "login=",
            "token", "agencia", "agência", "conta", "dac", "portal",
            "tipologon", "pre-login", "prelogin", "destino",
            "form item", "formitem", "usuario.", "usuario=", "cpf", "email",
            "agn=", "cta=", "digcta="
        ]

        def limpar(texto):
            texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)
            texto = re.sub(r'\|\|?[0-9]*m', '', texto)
            texto = re.sub(r'\[0m|\[1m|\[0;1m', '', texto)
            return texto.strip()

        try:
            self._update_status("Extraindo Cabeçalhos HTTP relevantes...")
            params = []
            if self.sslkeylog and os.path.isfile(self.sslkeylog):
                params = ['-o', f'tls.keylog_file:{self.sslkeylog}']

            capture = pyshark.FileCapture(
                self.path,
                display_filter="http",
                tshark_path=tshark,
                custom_parameters=params if params else None
            )

            count = 0
            seen = set()

            for packet in capture:
                count += 1
                if count % 100 == 0:
                    pct = 75 + min(17, int(count / 50))
                    self._update_status(f"Cabeçalhos HTTP: {count} pacotes processados...")
                    self._update_progress(min(92, pct))

                try:
                    packet_str = str(packet)
                    packet_lower = packet_str.lower()
                    if not any(kw in packet_lower for kw in KEYWORDS_LOCAL):
                        continue
                    clean = limpar(packet_str)
                    if clean in seen:
                        continue
                    seen.add(clean)
                    src = packet.ip.src if hasattr(packet, 'ip') else "?"
                    dst = packet.ip.dst if hasattr(packet, 'ip') else "?"
                    ts = data_br(float(packet.sniff_timestamp)) if hasattr(packet, 'sniff_timestamp') else datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    self.http_headers.append({
                        "timestamp": ts,
                        "src": src,
                        "dst": dst,
                        "header": clean
                    })
                except Exception:
                    continue

            capture.close()
            self._update_status(f"Cabeçalhos HTTP relevantes: {len(self.http_headers)} encontrados")
        except Exception as e:
            self._update_status(f"Erro ao extrair Cabeçalhos HTTP: {e}")

    def _analyze_form_items_classic(self):
        tshark = find_tshark()
        if not tshark:
            self._update_status("tshark não encontrado")
            return

        def limpar(texto):
            texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)
            texto = re.sub(r'\|\|?[0-9]*m', '', texto)
            texto = re.sub(r'\[0m|\[1m|\[0;1m', '', texto)
            return texto.strip()

        try:
            self._update_status("PyShark Classic: abrindo captura...")
            capture = pyshark.FileCapture(
                self.path,
                display_filter="http",
                tshark_path=tshark
            )

            count = 0
            for packet in capture:
                count += 1
                if count % 150 == 0:
                    pct = 55 + min(20, int(count / 40))
                    self._update_status(f"PyShark Classic: {count} pacotes HTTP processados...")
                    self._update_progress(min(75, pct))

                try:
                    packet_str = str(packet)
                    matches = re.findall(r'Form item.*', packet_str, re.IGNORECASE)
                    for m in matches:
                        clean = limpar(m)
                        if clean and "Form item" in clean and clean not in self.form_items_classic:
                            self.form_items_classic.append(clean)
                except Exception:
                    continue

            capture.close()
            self._update_status(f"Classic finalizado: {len(self.form_items_classic)} Form Items encontrados")
        except Exception as e:
            self._update_status(f"Erro Classic: {e}")

        if len(self.form_items_classic) == 0 and self.sslkeylog and os.path.isfile(self.sslkeylog):
            try:
                self._update_status("Tentando Classic com SSLKEYLOGFILE...")
                capture = pyshark.FileCapture(
                    self.path,
                    display_filter="http",
                    tshark_path=tshark,
                    custom_parameters=['-o', f'tls.keylog_file:{self.sslkeylog}']
                )
                for packet in capture:
                    try:
                        packet_str = str(packet)
                        matches = re.findall(r'Form item.*', packet_str, re.IGNORECASE)
                        for m in matches:
                            clean = limpar(m)
                            if clean and "Form item" in clean and clean not in self.form_items_classic:
                                self.form_items_classic.append(clean)
                    except Exception:
                        continue
                capture.close()
                self._update_status(f"Classic + keylog: {len(self.form_items_classic)} Form Items")
            except Exception as e:
                self._update_status(f"Erro Classic+keylog: {e}")

    def _forms_to_creds(self):
        seen = set()

        # 1. Formulários estruturados (Scapy)
        for form in self.form_data:
            agencia = conta = dac = portal = tipologon = prelogin = destino = None
            user = password = None
            outros = []

            for key, value in form["items"]:
                k = key.lower().strip()
                v = value.strip()

                if k in ("agn", "agencia"):
                    agencia = v
                elif k in ("cta", "conta"):
                    conta = v
                elif k in ("digcta", "dac") or k.endswith("dac"):
                    dac = v
                elif "portal" in k:
                    portal = v
                elif "tipologon" in k:
                    tipologon = v
                elif "pre-login" in k or "prelogin" in k:
                    prelogin = v
                elif "destino" in k:
                    destino = v
                elif any(x in k for x in ("username", "user", "login", "usuario", "tbusername", "email")):
                    user = v
                elif any(x in k for x in ("password", "pass", "pwd", "senha", "tbpassword")):
                    password = v
                else:
                    if v:
                        outros.append(f"{key}={v}")

            if agencia or conta or dac or portal:
                parts = []
                if agencia:   parts.append(f"Agência: {agencia}")
                if conta:     parts.append(f"Conta: {conta}")
                if dac:       parts.append(f"Dígito: {dac}")
                if portal:    parts.append(f"Portal: {portal}")
                if tipologon: parts.append(f"TipoLogon: {tipologon}")
                if prelogin:  parts.append(f"Pre-Login: {prelogin}")
                if destino:   parts.append(f"Destino: {destino}")
                if outros:    parts.append(" | ".join(outros))
                desc = " | ".join(parts)
                if desc not in seen:
                    seen.add(desc)
                    self.creds.append({
                        "protocolo": "Formulário Bancário / Login",
                        "usuario": desc,
                        "senha": "",
                        "timestamp": form["timestamp"]
                    })

            if user or password:
                key_id = ("Form Login", user or "", password or "")
                if key_id not in seen:
                    seen.add(key_id)
                    self.creds.append({
                        "protocolo": "Form Login",
                        "usuario": user or "(não informado)",
                        "senha": password or "(não informado)",
                        "timestamp": form["timestamp"]
                    })

        # 2. Form Items Classic
        current = {}
        for item in self.form_items_classic:
            m = re.search(r'Form item:\s*"?([^"=]+)"?\s*=\s*"?([^"]*)"?', item, re.I)
            if not m:
                continue

            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            current[key] = value

            if "usuario.agencia" in current and "usuario.conta" in current:
                ag = current.get("usuario.agencia", "")
                ct = current.get("usuario.conta", "")
                dc = current.get("usuario.dac", "")
                pt = current.get("portal", "")
                tl = current.get("tipologon", "")
                pl = current.get("pre-login", "")
                dest = current.get("destino", "")
                parts = []
                if ag:   parts.append(f"Agência: {ag}")
                if ct:   parts.append(f"Conta: {ct}")
                if dc:   parts.append(f"Dígito: {dc}")
                if pt:   parts.append(f"Portal: {pt}")
                if tl:   parts.append(f"TipoLogon: {tl}")
                if pl:   parts.append(f"Pre-Login: {pl}")
                if dest: parts.append(f"Destino: {dest}")
                desc = " | ".join(parts)
                if desc and desc not in seen:
                    seen.add(desc)
                    self.creds.append({
                        "protocolo": "Formulário Bancário / Login",
                        "usuario": desc,
                        "senha": "",
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    })
                current = {}
                continue

            if "agn" in current and "cta" in current:
                ag = current.get("agn", "")
                ct = current.get("cta", "")
                dc = current.get("digcta", "")
                parts = []
                if ag: parts.append(f"Agência: {ag}")
                if ct: parts.append(f"Conta: {ct}")
                if dc: parts.append(f"Dígito: {dc}")
                desc = " | ".join(parts)
                if desc and desc not in seen:
                    seen.add(desc)
                    self.creds.append({
                        "protocolo": "Formulário Bancário / Login",
                        "usuario": desc,
                        "senha": "",
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    })
                current = {}
                continue

            if any(x in key for x in ("password", "pass", "pwd", "senha", "tbpassword")):
                user = None
                password = value

                for uk in ("tbusername", "username", "user", "login", "usuario", "email"):
                    for ck, cv in current.items():
                        if uk in ck and cv:
                            user = cv
                            break
                    if user:
                        break

                if user or password:
                    key_id = ("Form Login (Classic)", user or "", password or "")
                    if key_id not in seen:
                        seen.add(key_id)
                        self.creds.append({
                            "protocolo": "Form Login (Classic)",
                            "usuario": user or "(não informado)",
                            "senha": password or "(não informado)",
                            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                current = {}

    def _search_credentials(self, pkt, payload: bytes):
        for name, pattern in PATTERNS.items():
            for m in pattern.finditer(payload):
                groups = m.groups()
                try:
                    if name == "HTTP Basic Auth":
                        decoded = base64.b64decode(groups[0]).decode(errors="ignore")
                        user, _, pw = decoded.partition(":")
                        cred = {"protocolo": name, "usuario": user, "senha": pw}
                    elif name in ("FTP", "POP3"):
                        cred = {
                            "protocolo": name,
                            "usuario": groups[0].decode(errors="ignore"),
                            "senha": groups[1].decode(errors="ignore")
                        }
                    elif name == "SMTP AUTH":
                        user = base64.b64decode(groups[0]).decode(errors="ignore")
                        pw = base64.b64decode(groups[1]).decode(errors="ignore")
                        cred = {"protocolo": name, "usuario": user, "senha": pw}
                    elif name == "JSON Login":
                        cred = {
                            "protocolo": name,
                            "usuario": groups[0].decode(errors="ignore"),
                            "senha": groups[1].decode(errors="ignore")
                        }
                    elif name == "API Key":
                        cred = {
                            "protocolo": name,
                            "usuario": "API Key",
                            "senha": groups[0].decode(errors="ignore")
                        }
                    else:
                        vals = [g.decode(errors="ignore") for g in groups if g]
                        cred = {
                            "protocolo": name,
                            "usuario": vals[0] if vals else "",
                            "senha": vals[1] if len(vals) > 1 else ""
                        }
                    cred["timestamp"] = data_br(pkt.time)
                    self.creds.append(cred)
                except Exception:
                    continue

    def _search_keywords(self, payload: bytes):
        lower = payload.lower()
        for kw in KEYWORDS:
            if kw in lower:
                start = max(0, lower.find(kw) - 30)
                end = min(len(payload), lower.find(kw) + 80)
                snippet = payload[start:end]
                self.keyword_hits.append((kw.decode(), decode_payload(snippet)))
                break

    def summary(self) -> str:
        lines = [
            "═" * 62,
            "  RESUMO DA CAPTURA",
            "═" * 62,
            f"  Arquivo               : {os.path.basename(self.path)}",
            f"  SSLKEYLOGFILE         : {self.sslkeylog or 'Não usado'}",
            f"  Total de pacotes      : {self.total}",
            f"  Início                : {self.start_time}",
            f"  Fim                   : {self.end_time}",
        ]
        lines += ["", "  Protocolos\n"]
        for proto, cnt in self.proto_counter.most_common():
            lines.append(f"    {proto:<10} → {cnt}")
        lines += ["", "\n  Top 10 IP\n"]
        for ip, cnt in self.ip_counter.most_common(10):
            lines.append(f"    {ip:<18} → {cnt}")
        lines += [
            "",
            f"  Credenciais           : {len(self.creds)}",
            f"  Formulários           : {len(self.form_data)}",
            f"  Form Items Classic    : {len(self.form_items_classic)}",
            f"  Requisições HTTP      : {len(self.http_requests)}",
            f"  Cabeçalhos HTTP       : {len(self.http_headers)}",
            f"  Queries DNS           : {len(self.dns_queries)}",
            f"  Hosts TLS (SNI)       : {len(self.sni_hosts)}",
            f"  Hits de palavras-chave: {len(self.keyword_hits)}",
            "═" * 62,
        ]
        return "\n".join(lines)

    def creds_text(self) -> str:
        if not self.creds:
            return "Nenhuma credencial encontrada.\n"
        lines = ["═" * 62, "  CREDENCIAIS ENCONTRADAS", "═" * 62]
        seen = set()
        count = 0
        for c in self.creds:
            key = (c["protocolo"], c["usuario"], c["senha"])
            if key in seen:
                continue
            seen.add(key)
            count += 1
            lines.append(f"\n[{count}] {c['protocolo']} ({c['timestamp']})")
            valor = c.get("usuario", "")
            if " | " in valor or "Agência" in valor or "Conta" in valor or len(valor) > 40:
                lines.append(f"\nDados: {valor}")
            else:
                lines.append(f"\nUsername: {valor}")
            if c.get("senha"):
                lines.append(f"Senha: {c['senha']}")
        return "\n".join(lines)

    def forms_text(self) -> str:
        lines = ["═" * 62, "  FORMULÁRIOS ESTRUTURADOS", "═" * 62]

        if self.form_data:
            for i, form in enumerate(self.form_data, 1):
                lines += [
                    f"\n[{i}] {form['timestamp']}  |  {form['src']} → {form['dst']}",
                    "─" * 55,
                ]
                for key, value in form["items"]:
                    lines.append(f'  Form item: "{key}" = "{value}"')

                agencia = conta = dac = portal = tipologon = prelogin = destino = None
                outros = []
                for key, value in form["items"]:
                    k = key.lower().strip()
                    v = value.strip()
                    if k in ("agn", "agencia"):
                        agencia = v
                    elif k in ("cta", "conta"):
                        conta = v
                    elif k in ("digcta", "dac") or k.endswith("dac"):
                        dac = v
                    elif "portal" in k:
                        portal = v
                    elif "tipologon" in k:
                        tipologon = v
                    elif "pre-login" in k or "prelogin" in k:
                        prelogin = v
                    elif "destino" in k:
                        destino = v
                    else:
                        if v:
                            outros.append(f"{key}={v}")

                if agencia or conta or dac or portal:
                    parts = []
                    if agencia:   parts.append(f"Agência: {agencia}")
                    if conta:     parts.append(f"Conta: {conta}")
                    if dac:       parts.append(f"Dígito: {dac}")
                    if portal:    parts.append(f"Portal: {portal}")
                    if tipologon: parts.append(f"TipoLogon: {tipologon}")
                    if prelogin:  parts.append(f"Pre-Login: {prelogin}")
                    if destino:   parts.append(f"Destino: {destino}")
                    if outros:    parts.append(" | ".join(outros))
                    desc = " | ".join(parts)
                    lines.append("")
                    lines.append(f"  Dados: {desc}")
        else:
            lines.append("\nNenhum formulário estruturado encontrado.")

        return "\n".join(lines)

    def form_items_classic_text(self) -> str:
        lines = ["═" * 62, "  FORM ITEMS CLASSIC", "═" * 62, ""]

        if not self.form_items_classic:
            lines.append("Nenhum 'Form item' encontrado.")
            return "\n".join(lines)

        for item in self.form_items_classic:
            lines.append(item)

        current = {}
        for item in self.form_items_classic:
            m = re.search(r'Form item:\s*"?([^"=]+)"?\s*=\s*"?([^"]*)"?', item, re.I)
            if not m:
                continue

            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            current[key] = value

            if "usuario.agencia" in current and "usuario.conta" in current:
                ag = current.get("usuario.agencia", "")
                ct = current.get("usuario.conta", "")
                dc = current.get("usuario.dac", "")
                pt = current.get("portal", "")
                tl = current.get("tipologon", "")
                pl = current.get("pre-login", "") or current.get("prelogin", "")
                dest = current.get("destino", "")

                parts = []
                if ag:   parts.append(f"Agência: {ag}")
                if ct:   parts.append(f"Conta: {ct}")
                if dc:   parts.append(f"Dígito: {dc}")
                if pt:   parts.append(f"Portal: {pt}")
                if tl:   parts.append(f"TipoLogon: {tl}")
                if pl:   parts.append(f"Pre-Login: {pl}")
                if dest: parts.append(f"Destino: {dest}")

                desc = " | ".join(parts)
                if desc:
                    lines.append("")
                    lines.append(f"Dados: {desc}")
                current = {}

            elif "agn" in current and "cta" in current:
                ag = current.get("agn", "")
                ct = current.get("cta", "")
                dc = current.get("digcta", "")

                parts = []
                if ag: parts.append(f"Agência: {ag}")
                if ct: parts.append(f"Conta: {ct}")
                if dc: parts.append(f"Dígito: {dc}")

                desc = " | ".join(parts)
                if desc:
                    lines.append("")
                    lines.append(f"Dados: {desc}")
                current = {}

        return "\n".join(lines)

    def http_text(self) -> str:
        lines = ["═" * 62, f"  REQUISIÇÕES HTTP ({len(self.http_requests)})", "═" * 62]
        for src, dst, method, host, uri, ua in self.http_requests[:400]:
            lines.append(f"{method:<7} {host}{uri}")
            lines.append(f"         {src} → {dst}  |  UA: {ua[:70]}")
            lines.append("")
        return "\n".join(lines)

    def http_headers_text(self) -> str:
        lines = [
            "═" * 70,
            "  CABEÇALHOS HTTP / HTTPS  (estilo Wireshark Follow Stream)",
            "═" * 70, ""
        ]
        if not self.http_headers:
            lines.append("Nenhum cabeçalho HTTP encontrado.")
            return "\n".join(lines)
        for i, h in enumerate(self.http_headers, 1):
            lines += [
                f"[{i}] {h['timestamp']}   |   {h['src']} → {h['dst']}",
                "─" * 70,
                h["header"],
                "",
                "═" * 70, ""
            ]
        return "\n".join(lines)

    def dns_text(self) -> str:
        lines = ["═" * 62, f"  DNS QUERIES ({len(self.dns_queries)})", "═" * 62]
        seen = set()
        for qname, qtype in self.dns_queries:
            if qname not in seen:
                seen.add(qname)
                lines.append(f"  {qname:<100}   (tipo {qtype})")
        return "\n".join(lines)

    def sni_text(self) -> str:
        lines = ["═" * 62, f"  HOSTS TLS / SNI ({len(self.sni_hosts)})", "═" * 62]
        for h in sorted(self.sni_hosts):
            lines.append(f"  {h}")
        return "\n".join(lines)

    def keywords_text(self) -> str:
        lines = ["═" * 62, f"  HITS DE PALAVRAS-CHAVE ({len(self.keyword_hits)})", "═" * 62]
        for kw, snippet in self.keyword_hits[:250]:
            clean = snippet.replace("\r", " ").replace("\n", " ").strip()
            lines.append(f"[{kw}] {clean[:130]}")
        lines += ["", "", "═" * 62, f"  CABEÇALHOS HTTP / HTTPS ({len(self.http_headers)})", "═" * 62]
        if not self.http_headers:
            lines.append("\nNenhum cabeçalho HTTP encontrado.")
        else:
            for i, h in enumerate(self.http_headers[:80], 1):
                lines += [
                    f"\n[{i}] {h['timestamp']}  |  {h['src']} → {h['dst']}",
                    "─" * 60,
                    h["header"], ""
                ]
        return "\n".join(lines)


class App:
    def __init__(self, root):
        self.root = root
        self.analyzer = None
        self.sslkeylog_path = None

        root.title("PCAP Analyzer Pro")
        root.state('zoomed')
        root.geometry("1100x820")
        root.minsize(900, 650)

        # ===== TOPO =====
        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        self.lbl_file = ttk.Label(top, text="Nenhum arquivo carregado", foreground="#555")
        self.lbl_file.pack(side="left")

        tk.Button(top, text="Pesquisar", command=self.search_in_tab,
                  bg="#bb0b31", fg="black", font=("Arial", 10, "bold")).pack(side="right", padx=(6, 0))
        tk.Button(top, text="Exportar relatório HTML", command=self.export_report,
                  bg="#f79707", font=("Arial", 10, "bold")).pack(side="right", padx=(6, 0))
        tk.Button(top, text="Selecionar SSLKEYLOGFILE", command=self.select_keylog,
                  bg="#0cf1f1", font=("Arial", 10, "bold")).pack(side="right", padx=(6, 0))
        tk.Button(top, text="Abrir .pcap / .pcapng", command=self.open_file,
                  bg="#33f707", font=("Arial", 10, "bold")).pack(side="right")

        self.lbl_keylog = ttk.Label(root, text="SSLKEYLOGFILE: não selecionado",
                                    foreground="#666", padding=(10, 0))
        self.lbl_keylog.pack(fill="x")

        # ===== BARRA DE PROGRESSO + ETA =====
        progress_frame = ttk.Frame(root, padding=(10, 5))
        progress_frame.pack(fill="x")

        self.progress = ttk.Progressbar(progress_frame, orient="horizontal",
                                        mode="determinate", length=400, maximum=100)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_progress = ttk.Label(progress_frame, text="0%", width=6)
        self.lbl_progress.pack(side="left")

        self.lbl_eta = ttk.Label(progress_frame, text="ETA: --:--", width=14)
        self.lbl_eta.pack(side="left", padx=(8, 0))

        # ===== NOTEBOOK =====
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.tab_resumo        = self._make_tab()
        self.tab_creds         = self._make_tab()
        self.tab_forms         = self._make_tab()
        self.tab_http          = self._make_tab()
        self.tab_dns           = self._make_tab()
        self.tab_sni           = self._make_tab()
        self.tab_kw            = self._make_tab()
        self.tab_formclassic   = self._make_tab()
        self.tab_http_headers  = self._make_tab()

        self.notebook.add(self.tab_resumo,       text="  Resumo  ")
        self.notebook.add(self.tab_creds,        text="  Credenciais  ")
        self.notebook.add(self.tab_forms,        text="  Formulários  ")
        self.notebook.add(self.tab_http,         text="  HTTP  ")
        self.notebook.add(self.tab_dns,          text="  DNS  ")
        self.notebook.add(self.tab_sni,          text="  TLS/SNI  ")
        self.notebook.add(self.tab_kw,           text="  Palavras-chave  ")
        self.notebook.add(self.tab_formclassic,  text="  Form Items Classic  ")
        self.notebook.add(self.tab_http_headers, text="  CABEÇALHOS HTTP  ")

        self.status = ttk.Label(root, text="Pronto.", anchor="w", padding=6, relief="sunken")
        self.status.pack(fill="x", side="bottom")

        self._append(self.tab_resumo,
            "PCAP Analyzer Pro — Versão com Progresso + ETA\n"
            "══════════════════════════════════════════════\n\n"
            "Como usar:\n"
            "  1. (Opcional) Clique em «Selecionar SSLKEYLOGFILE»\n"
            "  2. Clique em «Abrir .pcap / .pcapng»\n"
            "  3. Acompanhe a barra de progresso e o tempo estimado\n"
            "  4. Navegue pelas abas\n\n"
            "Novidades desta versão:\n"
            "  • Barra de progresso 0-100%\n"
            "  • Tempo estimado restante (ETA) calculado corretamente\n"
            "  • Mais padrões de credenciais (JSON, API Key, etc.)\n"
            "  • Suporte a AGN / CTA / DIGCTA\n"
            "  • Botão Pesquisar com navegação entre ocorrências\n"
        )

    def _make_tab(self):
        frame = ttk.Frame(self.notebook)
        txt = scrolledtext.ScrolledText(frame, wrap="word", font=("Consolas", 10), padx=8, pady=8)
        txt.pack(fill="both", expand=True)
        frame.text_widget = txt
        return frame

    def _append(self, tab, text: str):
        txt = tab.text_widget
        txt.delete("1.0", "end")
        txt.insert("1.0", text)

    def search_in_tab(self):
        """Abre uma janela de pesquisa na aba atual (não modal)
           e navega para a próxima ocorrência a cada clique em Pesquisar"""
        current = self.notebook.select()
        if not current:
            return

        tab = self.notebook.nametowidget(current)
        if not hasattr(tab, "text_widget"):
            return

        txt = tab.text_widget

        win = tk.Toplevel(self.root)
        win.title("Pesquisar Na Aba Atual")
        win.geometry("420x160")
        win.resizable(False, False)
        win.transient(self.root)

        ttk.Label(win, text="Digite o Que Deseja Pesquisar", font=("Arial", 10)).pack(pady=(12, 4))

        entry = ttk.Entry(win, width=45, font=("Consolas", 11))
        entry.pack(pady=4, padx=15)
        entry.focus()

        result_label = ttk.Label(win, text="", foreground="#555")
        result_label.pack(pady=4)

        last_term = [""]
        last_pos = ["1.0"]
        total_found = [0]

        def do_search(event=None):
            termo = entry.get().strip()
            if not termo:
                result_label.config(text="Digite algo para pesquisar")
                return

            if termo != last_term[0]:
                txt.tag_remove("highlight", "1.0", "end")
                last_term[0] = termo
                last_pos[0] = "1.0"
                total_found[0] = 0

                start = "1.0"
                while True:
                    pos = txt.search(termo, start, stopindex="end", nocase=True)
                    if not pos:
                        break
                    end_pos = f"{pos}+{len(termo)}c"
                    txt.tag_add("highlight", pos, end_pos)
                    total_found[0] += 1
                    start = end_pos

                txt.tag_config("highlight", background="#facc15", foreground="#000000")

                if total_found[0] == 0:
                    result_label.config(text="Nenhum resultado encontrado")
                    return

            pos = txt.search(termo, last_pos[0], stopindex="end", nocase=True)

            if not pos:
                pos = txt.search(termo, "1.0", stopindex="end", nocase=True)
                if not pos:
                    result_label.config(text="Nenhum resultado encontrado")
                    return
                result_label.config(text=f"1 / {total_found[0]} (voltou ao início)")
            else:
                count = 0
                start = "1.0"
                while True:
                    p = txt.search(termo, start, stopindex="end", nocase=True)
                    if not p or p == pos:
                        count += 1
                        break
                    count += 1
                    start = f"{p}+{len(termo)}c"
                result_label.config(text=f"{count} / {total_found[0]}")

            txt.tag_remove("current", "1.0", "end")
            end_pos = f"{pos}+{len(termo)}c"
            txt.tag_add("current", pos, end_pos)
            txt.tag_config("current", background="#f97316", foreground="#000000")

            txt.see(pos)
            txt.mark_set("insert", pos)
            last_pos[0] = end_pos

        def clear_search():
            txt.tag_remove("highlight", "1.0", "end")
            txt.tag_remove("current", "1.0", "end")
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="Pesquisar", command=do_search).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Limpar e Fechar", command=clear_search).pack(side="left", padx=6)

        entry.bind("<Return>", do_search)
        win.bind("<Escape>", lambda e: clear_search())

    def select_keylog(self):
        path = filedialog.askopenfilename(
            title="Selecionar SSLKEYLOGFILE",
            filetypes=[("Keylog", "*.log *.txt *"), ("Todos", "*.*")]
        )
        if path:
            self.sslkeylog_path = path
            self.lbl_keylog.config(text=f"SSLKEYLOGFILE: {os.path.basename(path)}")
            self.status.config(text=f"Keylog carregado: {path}")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar captura",
            filetypes=[("Capturas", "*.pcapng *.pcap"), ("Todos", "*.*")]
        )
        if not path:
            return
        self.lbl_file.config(text=os.path.basename(path))
        self.status.config(text="Iniciando análise...")
        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        self.lbl_eta.config(text="ETA: calculando...")
        threading.Thread(target=self._run_analysis, args=(path,), daemon=True).start()

    def _run_analysis(self, path):
        try:
            if not HAS_SCAPY and not HAS_PYSHARK:
                self.root.after(0, lambda: messagebox.showerror(
                    "Erro", "Nenhuma biblioteca disponível.\n\npip install scapy pyshark"))
                return

            def update_status(msg):
                self.root.after(0, lambda: self.status.config(text=msg))

            def update_progress(percent, eta_sec=None):
                def _upd():
                    self.progress["value"] = percent
                    self.lbl_progress.config(text=f"{int(percent)}%")
                    if eta_sec is not None:
                        self.lbl_eta.config(text=f"ETA: {format_eta(eta_sec)}")
                    elif percent >= 100:
                        self.lbl_eta.config(text="ETA: 00:00")
                self.root.after(0, _upd)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            a = PCAPAnalyzer(path, sslkeylog=self.sslkeylog_path,
                             status_callback=update_status,
                             progress_callback=update_progress)
            a.analyze()
            self.analyzer = a
            self.root.after(0, self._show_results)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro de análise", str(e)))
            self.root.after(0, lambda: self.status.config(text="Falha na análise"))
            self.root.after(0, lambda: self.progress.config(value=0))

    def _show_results(self):
        a = self.analyzer
        self._append(self.tab_resumo,        a.summary())
        self._append(self.tab_creds,         a.creds_text())
        self._append(self.tab_forms,         a.forms_text())
        self._append(self.tab_http,          a.http_text())
        self._append(self.tab_dns,           a.dns_text())
        self._append(self.tab_sni,           a.sni_text())
        self._append(self.tab_kw,            a.keywords_text())
        self._append(self.tab_formclassic,   a.form_items_classic_text())
        self._append(self.tab_http_headers,  a.http_headers_text())

        msg = (f"Concluído → {a.total} pacotes | "
               f"{len(a.creds)} credenciais | "
               f"{len(a.form_items_classic)} Form Items Classic | "
               f"{len(a.http_headers)} Cabeçalhos HTTP")
        self.status.config(text=msg)
        self.progress["value"] = 100
        self.lbl_progress.config(text="100%")
        self.lbl_eta.config(text="ETA: 00:00")

        if a.form_items_classic:
            self.notebook.select(self.tab_formclassic)
        elif a.creds:
            self.notebook.select(self.tab_creds)
        elif a.http_headers:
            self.notebook.select(self.tab_http_headers)

    def export_report(self):
        if not self.analyzer:
            messagebox.showwarning("Aviso", "Analise um arquivo primeiro.")
            return

        out = filedialog.asksaveasfilename(
            title="Salvar relatório HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")]
        )
        if not out:
            return

        a = self.analyzer
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        def limpar_texto(texto):
            if not texto:
                return ""
            texto = re.sub(r'[^\x20-\x7E\n\r\táàâãéèêíóôõúçÁÀÂÃÉÈÊÍÓÔÕÚÇ]', '.', str(texto))
            if len(texto) > 50000:
                texto = texto[:50000] + "\n\n... (conteúdo truncado)"
            return texto

        def esc(texto):
            return (str(texto)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;"))

        resumo_limpo      = esc(limpar_texto(a.summary()))
        creds_limpo       = esc(limpar_texto(a.creds_text()))
        forms_limpo       = esc(limpar_texto(a.forms_text()))
        http_limpo        = esc(limpar_texto(a.http_text()))
        headers_limpo     = esc(limpar_texto(a.http_headers_text()))
        formclassic_limpo = esc(limpar_texto(a.form_items_classic_text()))
        dns_limpo         = esc(limpar_texto(a.dns_text()))
        sni_limpo         = esc(limpar_texto(a.sni_text()))
        keywords_limpo    = esc(limpar_texto(a.keywords_text()))

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PCAP Analyzer Pro - Relatório</title>
<style>
:root {{
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
header {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 25px; text-align: center; }}
header h1 {{ font-size: 2rem; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.badge {{ display: inline-block; background: #1e40af; color: #bfdbfe; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; margin: 4px; }}
.nav {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 30px; background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; }}
.nav a {{ text-decoration: none; background: #1e40af; color: #bfdbfe; padding: 8px 16px; border-radius: 8px; font-size: 0.9rem; }}
.nav a:hover {{ background: #38bdf8; color: #0f172a; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-bottom: 25px; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px; text-align: center; }}
.card h3 {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; }}
.card .value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
section {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; margin-bottom: 22px; overflow: hidden; }}
section h2 {{ padding: 14px 20px; font-size: 1.15rem; border-bottom: 1px solid var(--border); color: #fff; }}
#resumo h2 {{ background: linear-gradient(90deg, #1e3a8a, #1e40af); }}
#credenciais h2 {{ background: linear-gradient(90deg, #14532d, #166534); color: #4ade80; }}
#formclassic h2 {{ background: linear-gradient(90deg, #581c87, #7e22ce); }}
#cabecalhos h2 {{ background: linear-gradient(90deg, #9a3412, #c2410c); }}
#formularios h2 {{ background: linear-gradient(90deg, #9d174d, #be185d); }}
#http h2 {{ background: linear-gradient(90deg, #155e75, #0e7490); }}
#dns h2 {{ background: linear-gradient(90deg, #854d0e, #a16207); }}
#sni h2 {{ background: linear-gradient(90deg, #312e81, #3730a3); }}
#keywords h2 {{ background: linear-gradient(90deg, #1e293b, #334155); }}
.content {{ padding: 18px 20px; }}
pre {{ background: #0f172a; border: 1px solid var(--border); border-radius: 10px; padding: 16px; overflow-x: auto; font-family: Consolas, monospace; font-size: 0.88rem; white-space: pre-wrap; max-height: 700px; overflow-y: auto; }}
footer {{ text-align: center; color: var(--muted); font-size: 0.9rem; margin-top: 30px; padding: 15px; }}

#btn-topo {{
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    color: #0f172a;
    border: none;
    border-radius: 50px;
    padding: 12px 22px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4);
    z-index: 9999;
    transition: all 0.25s ease;
    display: none;
}}
#btn-topo:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(56, 189, 248, 0.6);
}}
</style>
</head>
<body>
<div class="container">
<header>
    <h1>PCAP Analyzer Pro</h1>
    <p style="color:#94a3b8; margin-bottom:12px;">Relatório de Análise de Captura</p>
    <span class="badge">Arquivo: {esc(os.path.basename(a.path))}</span>
    <span class="badge">Pacotes: {a.total}</span>
    <span class="badge">SSLKEYLOG: {'Sim' if a.sslkeylog else 'Não'}</span>
    <span class="badge">Gerado em: {agora}</span>
</header>
<nav class="nav">
    <a href="#resumo">Resumo</a>
    <a href="#credenciais">Credenciais ({len(a.creds)})</a>
    <a href="#formclassic">Form Items Classic ({len(a.form_items_classic)})</a>
    <a href="#cabecalhos">Cabeçalhos HTTP ({len(a.http_headers)})</a>
    <a href="#formularios">Formulários ({len(a.form_data)})</a>
    <a href="#http">Requisições HTTP</a>
    <a href="#dns">DNS</a>
    <a href="#sni">TLS / SNI</a>
    <a href="#keywords">Palavras-chave</a>
</nav>
<div class="grid">
    <div class="card"><h3>Credenciais</h3><div class="value">{len(a.creds)}</div></div>
    <div class="card"><h3>Form Items</h3><div class="value">{len(a.form_items_classic)}</div></div>
    <div class="card"><h3>Cabeçalhos</h3><div class="value">{len(a.http_headers)}</div></div>
    <div class="card"><h3>Formulários</h3><div class="value">{len(a.form_data)}</div></div>
    <div class="card"><h3>HTTP</h3><div class="value">{len(a.http_requests)}</div></div>
    <div class="card"><h3>TLS/SNI</h3><div class="value">{len(a.sni_hosts)}</div></div>
</div>
<section id="resumo"><h2>Resumo da Captura</h2><div class="content"><pre>{resumo_limpo}</pre></div></section>
<section id="credenciais"><h2>Credenciais Encontradas</h2><div class="content"><pre>{creds_limpo}</pre></div></section>
<section id="formclassic"><h2>Form Items Classic</h2><div class="content"><pre>{formclassic_limpo}</pre></div></section>
<section id="cabecalhos"><h2>Cabeçalhos HTTP</h2><div class="content"><pre>{headers_limpo}</pre></div></section>
<section id="formularios"><h2>Formulários Estruturados</h2><div class="content"><pre>{forms_limpo}</pre></div></section>
<section id="http"><h2>Requisições HTTP</h2><div class="content"><pre>{http_limpo}</pre></div></section>
<section id="dns"><h2>DNS Queries</h2><div class="content"><pre>{dns_limpo}</pre></div></section>
<section id="sni"><h2>Hosts TLS / SNI</h2><div class="content"><pre>{sni_limpo}</pre></div></section>
<section id="keywords"><h2>Palavras-chave</h2><div class="content"><pre>{keywords_limpo}</pre></div></section>
<footer>Relatório gerado por <strong>PCAP Analyzer Pro</strong> • {agora}</footer>
</div>

<button id="btn-topo" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">↑ TOPO</button>

<script>
window.addEventListener('scroll', function() {{
    const btn = document.getElementById('btn-topo');
    if (window.scrollY > 400) {{
        btn.style.display = 'block';
    }} else {{
        btn.style.display = 'none';
    }}
}});
</script>
</body>
</html>
"""
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
            self.status.config(text=f"Relatório HTML salvo → {out}")
            messagebox.showinfo("Sucesso", "Relatório HTML salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{e}")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
