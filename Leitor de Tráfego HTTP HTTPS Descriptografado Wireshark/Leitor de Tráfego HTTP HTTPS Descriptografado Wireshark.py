#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitor de Tráfego HTTP + HTTPS (descriptografado com sslkeylog + tshark)
- Oculta janelas pretas do tshark/CMD sem quebrar o asyncio/PyShark
- Relatório completo e exportação HTML
"""

import sys
import os
import subprocess

# ============================================================
# WINDOWS — OCULTAR JANELAS DO TSHARK (CORRIGIDO PARA PYTHON 3.11)
# ============================================================
CREATE_NO_WINDOW = 0x08000000

if sys.platform == "win32":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # Esconde o console do CMD
    except Exception:
        pass

    # Para não quebrar o asyncio/pyshark no Python 3.11, Popen DEVE ser uma Classe!
    _OriginalPopen = subprocess.Popen

    class PopenSemJanela(_OriginalPopen):
        def __init__(self, *args, **kwargs):
            flags = kwargs.get("creationflags", 0) or 0
            kwargs["creationflags"] = flags | CREATE_NO_WINDOW
            if kwargs.get("startupinfo") is None:
                try:
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = 0
                    kwargs["startupinfo"] = si
                except Exception:
                    pass
            super().__init__(*args, **kwargs)

    subprocess.Popen = PopenSemJanela

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import re
import shutil
import html

# Teste de importação do pyshark com mensagem amigável
try:
    import pyshark
except ImportError:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror(
        "Biblioteca Ausente",
        "A biblioteca 'pyshark' não está instalada no seu Python.\n\n"
        "Abra o CMD/Terminal e execute:\n"
        "pip install pyshark"
    )
    sys.exit(1)


# ================= Util: achar tshark =================

def encontrar_tshark(caminho_manual=None):
    if caminho_manual and os.path.isfile(caminho_manual):
        return caminho_manual
    w = shutil.which("tshark") or shutil.which("tshark.exe")
    if w:
        return w
    candidatos = [
        r"C:\Program Files\Wireshark\tshark.exe",
        r"C:\Program Files (x86)\Wireshark\tshark.exe",
        os.path.expandvars(r"%ProgramFiles%\Wireshark\tshark.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Wireshark\tshark.exe"),
    ]
    for c in candidatos:
        if c and os.path.isfile(c):
            return c
    return None


def limpar_texto(s, max_len=200):
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)
    s = ''.join(ch if 32 <= ord(ch) < 127 or ch in '\t' else ' ' for ch in s)
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > max_len:
        s = s[:max_len] + "…"
    return s


def limpar_headers_pyshark(layer_str):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    texto = ansi_escape.sub('', str(layer_str))
    linhas = texto.split('\n')
    headers_limpos = []
    ignorar = (
        "Layer ", "File Data", "Request Method", "Request URI",
        "Request Version", "Full request", "Cookie pair",
        "Content length:", "Response Code", "Response Version",
        "Response Phrase", "Request Line", "Response Line",
    )
    for l in linhas:
        l = l.strip().lstrip(":\t ")
        if not l:
            continue
        if any(l.startswith(ign) for ign in ignorar):
            continue
        if l.endswith("\\r\\n"):
            l = l[:-4]
        l = limpar_texto(l, 500)
        if l and ":" in l:
            headers_limpos.append(l)
    return "\n".join(headers_limpos)


def extrair_corpo_http(h):
    for campo in ("file_data", "data"):
        val = getattr(h, campo, None)
        if not val:
            continue
        try:
            s = str(val)
            if re.fullmatch(r'[0-9a-fA-F:]+', s.replace(' ', '')) and len(s) > 8:
                hx = s.replace(':', '').replace(' ', '')
                if len(hx) % 2 == 0:
                    corpo = bytes.fromhex(hx).decode('utf-8', errors='replace')
                else:
                    corpo = s
            else:
                corpo = s
            return limpar_texto(corpo, 2000)
        except Exception:
            continue
    return ""


# ================= Parser do sslkeylog.log =================

def parse_keylog(path):
    entradas = []
    with open(path, "r", errors="replace") as f:
        for n, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split()
            if len(partes) < 2:
                continue
            label = partes[0]
            resto = partes[1:]
            client_random = ""
            secret = ""
            if label in ("CLIENT_RANDOM",) or (
                "SECRET" in label and "CLIENT" in label
            ) or label.endswith("_SECRET"):
                if len(resto) >= 1:
                    client_random = resto[0].lower()
                if len(resto) >= 2:
                    secret = resto[1]
            if not client_random or len(client_random) < 16:
                continue
            entradas.append({
                "label": label,
                "client_random": client_random,
                "secret": secret,
                "linha": n,
            })
    return entradas


# ================= Parser de pacotes nativo =================

def processar_pacote(dados):
    if len(dados) < 14:
        return None
    eth_type = struct.unpack(">H", dados[12:14])[0]
    off = 14
    if eth_type == 0x8100:
        if len(dados) < 18:
            return None
        eth_type = struct.unpack(">H", dados[16:18])[0]
        off = 18
    if eth_type == 0x0001:
        if len(dados) < 22:
            return None
        if struct.unpack(">H", dados[20:22])[0] != 0x0800:
            return None
        ip = dados[16:]
    elif eth_type == 0x0800:
        ip = dados[off:]
    else:
        return None
    if len(ip) < 20:
        return None
    ihl = (ip[0] & 0x0F) * 4
    if ihl < 20 or len(ip) < ihl or ip[9] != 6:
        return None
    if struct.unpack(">H", ip[6:8])[0] & 0x1FFF:
        return None
    src = ".".join(str(b) for b in ip[12:16])
    dst = ".".join(str(b) for b in ip[16:20])
    tcp = ip[ihl:]
    if len(tcp) < 20:
        return None
    sport, dport = struct.unpack(">HH", tcp[0:4])
    data_off = (tcp[12] >> 4) * 4
    if data_off < 20 or len(tcp) < data_off:
        return None
    return (src, sport, dst, dport, tcp[data_off:])


def ler_pcap_ou_pcapng(caminho):
    with open(caminho, "rb") as f:
        magic = f.read(4)
        if magic in (b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4",
                     b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d"):
            endian = "<" if magic[:2] in (b"\xd4\xc3", b"\x4d\x3c") else ">"
            f.read(20)
            while True:
                hdr = f.read(16)
                if len(hdr) < 16:
                    break
                _, _, caplen, _ = struct.unpack(endian + "IIII", hdr)
                if caplen > 0x400000:
                    break
                dados = f.read(caplen)
                if len(dados) < caplen:
                    break
                res = processar_pacote(dados)
                if res:
                    yield res
            return
        if magic == b"\x0a\x0d\x0d\x0a":
            endian = "<"
            f.seek(0)
            while True:
                hdr = f.read(8)
                if len(hdr) < 8:
                    break
                blk_type, blk_len = struct.unpack("<II", hdr)
                if blk_len < 12 or blk_len % 4 != 0:
                    blk_type, blk_len = struct.unpack(">II", hdr)
                    if blk_len < 12 or blk_len % 4 != 0:
                        break
                    endian = ">"
                corpo = f.read(max(0, blk_len - 12))
                f.read(4)
                if blk_type == 0x0A0D0D0A and len(corpo) >= 4:
                    bom = corpo[0:4]
                    if bom == b"\x1a\x2b\x3c\x4d":
                        endian = "<"
                    elif bom == b"\x4d\x3c\x2b\x1a":
                        endian = ">"
                    continue
                if blk_type == 0x00000006 and len(corpo) >= 28:
                    caplen = struct.unpack(endian + "I", corpo[16:20])[0]
                    if caplen <= len(corpo) - 20:
                        res = processar_pacote(corpo[20:20 + caplen])
                        if res:
                            yield res
                elif blk_type == 0x00000003 and len(corpo) >= 4:
                    origlen = struct.unpack(endian + "I", corpo[0:4])[0]
                    caplen = min(origlen, len(corpo) - 4)
                    res = processar_pacote(corpo[4:4 + caplen])
                    if res:
                        yield res
            return
        raise ValueError("Formato desconhecido — use .pcap ou .pcapng")


# ================= ClientHello / SNI =================

def parse_client_hello(payload):
    if len(payload) < 6 or payload[0] != 0x16:
        return None
    pos = 5
    if pos >= len(payload) or payload[pos] != 0x01:
        return None
    pos += 4 + 2
    if pos + 32 > len(payload):
        return None
    client_random = payload[pos:pos + 32].hex().lower()
    pos += 32
    if pos >= len(payload):
        return None
    sid_len = payload[pos]
    pos += 1 + sid_len
    if pos + 2 > len(payload):
        return None
    cs_len = int.from_bytes(payload[pos:pos + 2], "big")
    pos += 2 + cs_len
    if pos >= len(payload):
        return None
    comp_len = payload[pos]
    pos += 1 + comp_len
    if pos + 2 > len(payload):
        return None
    ext_total = int.from_bytes(payload[pos:pos + 2], "big")
    pos += 2
    fim = min(pos + ext_total, len(payload))
    snis = []
    while pos + 4 <= fim:
        ext_type = int.from_bytes(payload[pos:pos + 2], "big")
        ext_len = int.from_bytes(payload[pos + 2:pos + 4], "big")
        corpo = payload[pos + 4:pos + 4 + ext_len]
        if ext_type == 0x0000 and len(corpo) >= 5 and corpo[2] == 0x00:
            host_len = int.from_bytes(corpo[3:5], "big")
            host = corpo[5:5 + host_len].decode(errors="replace")
            if host:
                snis.append(host)
        pos += 4 + ext_len
    return client_random, snis


def extrair_handshakes_tls(pcap_path):
    handshakes = []
    stream_buf = {}
    for src, sport, dst, dport, payload in ler_pcap_ou_pcapng(pcap_path):
        if not payload:
            continue
        chave = (src, sport, dst, dport)
        buf = stream_buf.get(chave, b"") + payload
        try:
            res = parse_client_hello(buf)
        except Exception:
            res = None
        if res:
            cr, snis = res
            handshakes.append({
                "src": src, "sport": sport, "dst": dst, "dport": dport,
                "client_random": cr, "snis": snis,
            })
            stream_buf.pop(chave, None)
        else:
            stream_buf[chave] = buf[-8192:]
    return handshakes


def snis_por_client_random(handshakes):
    resultado = {}
    for h in handshakes:
        lista = resultado.setdefault(h["client_random"].lower(), [])
        for s in h["snis"]:
            if s not in lista:
                lista.append(s)
    return resultado


# ================= HTTP texto claro (nativo) =================

def extrair_http_requests(pcap_path):
    streams = {}
    for src, sport, dst, dport, payload in ler_pcap_ou_pcapng(pcap_path):
        if not payload:
            continue
        chave = (src, sport, dst, dport)
        streams[chave] = streams.get(chave, b"") + payload

    METODOS = (b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ",
               b"OPTIONS ", b"PATCH ", b"TRACE ", b"CONNECT ")
    requests = []
    for (src, sport, dst, dport), buf in streams.items():
        pos = 0
        while pos < len(buf):
            idx, metodo = -1, None
            for m in METODOS:
                i = buf.find(m, pos)
                if i != -1 and (idx == -1 or i < idx):
                    idx, metodo = i, m
            if idx == -1:
                break
            fim_header = buf.find(b"\r\n\r\n", idx)
            if fim_header == -1:
                break
            linhas = buf[idx:fim_header].split(b"\r\n")
            partes = linhas[0].decode(errors="replace").split()
            if len(partes) < 2:
                pos = fim_header + 4
                continue
            metodo_req, uri = partes[0], partes[1]
            headers = {}
            for linha in linhas[1:]:
                if b":" in linha:
                    k, _, v = linha.partition(b":")
                    headers[k.decode(errors="replace").strip()] = \
                        v.decode(errors="replace").strip()
            body = b""
            headers_lower = {k.lower(): v for k, v in headers.items()}
            cl = headers_lower.get("content-length", "")
            if cl.isdigit():
                inicio = fim_header + 4
                body = buf[inicio:inicio + int(cl)]
                pos = inicio + int(cl)
            else:
                pos = fim_header + 4
            requests.append({
                "metodo": metodo_req,
                "host": headers_lower.get("host", ""),
                "uri": uri,
                "src": src, "dst": dst,
                "sport": sport, "dport": dport,
                "headers": headers,
                "body": body.decode(errors="replace"),
            })
    return requests


# ================= Análise profunda (pyshark + keylog) =================

def analise_profunda(pcap_path, keylog_path, filtro_regex="",
                     display_filter="", limite=800, tshark_path=None,
                     progresso=None):
    ts = encontrar_tshark(tshark_path)
    override_prefs = None
    if keylog_path and os.path.isfile(keylog_path):
        kl = os.path.abspath(keylog_path).replace("\\", "/")
        override_prefs = {"tls.keylog_file": kl}

    regex = None
    if filtro_regex:
        try:
            regex = re.compile(filtro_regex, re.IGNORECASE)
        except re.error as e:
            raise RuntimeError(f"Regex inválida: {e}")

    if not display_filter:
        display_filter = "http or http2 or tls.handshake.type == 1 or tls.app_data"

    cap = pyshark.FileCapture(
        pcap_path,
        display_filter=display_filter,
        keep_packets=False,
        override_prefs=override_prefs,
        tshark_path=ts,
    )

    pacotes = []
    total = 0
    for pkt in cap:
        total += 1
        if progresso and total % 40 == 0:
            progresso(total)
        try:
            resumo = {
                "num": str(getattr(pkt, "number", "")),
                "hora": str(getattr(pkt, "sniff_time", "")),
                "protocolos": " ".join(l.layer_name for l in pkt.layers),
                "src": "", "dst": "",
                "info": "", "http": "", "tls": "",
                "metodo": "", "host": "", "uri": "", "corpo": "",
                "headers_raw": "",
            }
            if hasattr(pkt, "ip"):
                resumo["src"] = str(pkt.ip.src)
                resumo["dst"] = str(pkt.ip.dst)
            elif hasattr(pkt, "ipv6"):
                resumo["src"] = str(pkt.ipv6.src)
                resumo["dst"] = str(pkt.ipv6.dst)

            if hasattr(pkt, "http"):
                h = pkt.http
                metodo = getattr(h, "request_method", None)
                status = getattr(h, "response_code", None)
                uri = str(getattr(h, "request_uri", "") or "")
                host = str(getattr(h, "host", "") or "")
                resumo["metodo"] = str(metodo or status or "")
                resumo["host"] = host
                resumo["uri"] = uri
                try:
                    resumo["headers_raw"] = limpar_headers_pyshark(str(h))
                except Exception:
                    pass
                resumo["corpo"] = extrair_corpo_http(h)
                if metodo:
                    resumo["http"] = limpar_texto(f"{metodo} http://{host}{uri}", 180)
                elif status:
                    resumo["http"] = limpar_texto(f"HTTP {status}", 80)
                else:
                    resumo["http"] = "HTTP"

            if hasattr(pkt, "http2"):
                h2 = pkt.http2
                try:
                    resumo["headers_raw"] = limpar_headers_pyshark(str(h2))
                except Exception:
                    pass

                def g(*nomes):
                    for n in nomes:
                        v = getattr(h2, n, None)
                        if v is not None and str(v):
                            return str(v)
                    try:
                        for s in h2:
                            for n in nomes:
                                v = getattr(s, n, None)
                                if v is not None and str(v):
                                    return str(v)
                    except Exception:
                        pass
                    return ""

                metodo = g("headers_method", "header_method", "method")
                status = g("headers_status", "header_status", "status")
                uri = g("headers_path", "header_path", "path", "headers_target")
                host = g("headers_authority", "header_authority",
                         "authority", "headers_host")
                scheme = g("headers_scheme", "header_scheme") or "https"

                if metodo or status or uri or host:
                    resumo["metodo"] = metodo or status or resumo["metodo"]
                    resumo["host"] = host or resumo["host"]
                    resumo["uri"] = uri or resumo["uri"]
                    if metodo:
                        resumo["http"] = limpar_texto(
                            f"[HTTPS/2] {metodo} {scheme}://{host}{uri}", 180)
                    elif status:
                        resumo["http"] = limpar_texto(
                            f"[HTTPS/2] Status {status}", 80)
                    else:
                        resumo["http"] = limpar_texto(
                            f"[HTTPS/2] {host}{uri}", 180)

            if hasattr(pkt, "tls"):
                t = pkt.tls
                sni = ""
                try:
                    sni = str(t.handshake_extensions_server_name)
                except Exception:
                    pass
                hs = getattr(t, "handshake_type", None)
                resumo["tls"] = limpar_texto(
                    "TLS" + (f" hs={hs}" if hs else "") +
                    (f" SNI={sni}" if sni else ""), 120)
                if sni and not resumo["host"]:
                    resumo["host"] = sni

            resumo["info"] = limpar_texto(
                resumo["http"] or resumo["tls"] or resumo["protocolos"], 180)
            texto = " ".join(str(v) for v in resumo.values())
            if regex and not regex.search(texto):
                continue
            pacotes.append(resumo)
            if len(pacotes) >= limite:
                break
        except Exception:
            continue

    try:
        cap.close()
    except Exception:
        pass
    return pacotes, total


# ================= Interface =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Leitor de Tráfego HTTP + HTTPS (Descriptografado)")
        self.geometry("1280x760")
        self.state("zoomed")

        self.keylog = []
        self.keylog_path = None
        self.handshakes = []
        self.snis = {}
        self.http_requests = []
        self.http_exibidos = []
        self.pcap_path = None
        self.pcap_nome = ""
        self.tshark_path = encontrar_tshark()
        self.dados_deep = []
        self.total_deep_analisados = 0

        topo = ttk.Frame(self, padding=8)
        topo.pack(fill="x")

        ttk.Button(topo, text="1. Abrir sslkeylog.log",
                   command=self.abrir_keylog).pack(side="left", padx=3)
        ttk.Button(topo, text="2. Abrir .pcap / .pcapng",
                   command=self.abrir_pcap).pack(side="left", padx=3)
        ttk.Button(topo, text="Analisar resultados.pcapng",
                   command=self.analisar_resultados).pack(side="left", padx=8)
        ttk.Button(topo, text="▶ DESCRIPTOGRAFAR AGORA",
                   command=self.rodar_analise_profunda).pack(side="left", padx=8)

        self.lbl_status = ttk.Label(
            topo, text="Carregue a chave e o pcap", foreground="blue")
        self.lbl_status.pack(side="right", padx=8)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=4)

        # ---- Aba 1: Deep ----
        aba_deep = ttk.Frame(self.nb)
        self.nb.add(aba_deep, text="🌐 HTTP + HTTPS Descriptografado")

        bar = ttk.Frame(aba_deep, padding=4)
        bar.pack(fill="x")
        ttk.Label(bar, text="Filtro Rápido:").pack(side="left")
        self.combo_filtro = ttk.Combobox(
            bar,
            values=["Todos", "POST", "GET", "PUT", "DELETE", "HEAD",
                    "OPTIONS", "PATCH", "TRACE", "CONNECT", "TLS"],
            width=8, state="readonly")
        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(side="left", padx=4)
        self.combo_filtro.bind("<<ComboboxSelected>>", self.aplicar_filtro_tabela)

        ttk.Label(bar, text="Regex:").pack(side="left", padx=(10, 0))
        self.ent_regex = ttk.Entry(bar, width=15)
        self.ent_regex.insert(0, "http|tls")
        self.ent_regex.pack(side="left", padx=4)

        ttk.Label(bar, text="Display filter:").pack(side="left", padx=(10, 0))
        self.ent_df = ttk.Entry(bar, width=35)
        self.ent_df.insert(0, "http or http2 or tls.handshake.type == 1")
        self.ent_df.pack(side="left", padx=4)

        self.lbl_deep = ttk.Label(bar, text="", foreground="darkgreen")
        self.lbl_deep.pack(side="left", padx=8)

        pw_deep = ttk.PanedWindow(aba_deep, orient=tk.VERTICAL)
        pw_deep.pack(fill="both", expand=True, padx=4, pady=2)

        frame_tabela = ttk.Frame(pw_deep)
        cols = ("num", "metodo", "host", "uri", "src", "dst", "info")
        self.tree_deep = ttk.Treeview(frame_tabela, columns=cols, show="headings")
        for cid, txt, w in (
            ("num", "#", 50), ("metodo", "Método", 70),
            ("host", "Host / SNI", 200), ("uri", "URI / Path", 260),
            ("src", "Origem", 120), ("dst", "Destino", 120),
            ("info", "Detalhe", 380),
        ):
            self.tree_deep.heading(cid, text=txt)
            self.tree_deep.column(cid, width=w, anchor="w")
        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical",
                                 command=self.tree_deep.yview)
        self.tree_deep.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.tree_deep.pack(fill="both", expand=True)
        self.tree_deep.bind("<<TreeviewSelect>>", self.mostrar_detalhe_deep)
        pw_deep.add(frame_tabela, weight=3)

        frame_detalhes = ttk.Frame(pw_deep)
        self.txt_detalhe_deep = tk.Text(
            frame_detalhes, wrap="word", font=("Consolas", 10))
        scroll_txt = ttk.Scrollbar(
            frame_detalhes, orient="vertical",
            command=self.txt_detalhe_deep.yview)
        self.txt_detalhe_deep.configure(yscrollcommand=scroll_txt.set)
        scroll_txt.pack(side="right", fill="y")
        self.txt_detalhe_deep.pack(fill="both", expand=True)
        pw_deep.add(frame_detalhes, weight=1)

        # ---- Aba 2: HTTP Claro ----
        aba_http = ttk.Frame(self.nb)
        self.nb.add(aba_http, text="HTTP Texto Claro")

        bar_http = ttk.Frame(aba_http, padding=4)
        bar_http.pack(fill="x")
        ttk.Label(bar_http, text="Filtro Rápido:").pack(side="left")
        self.combo_filtro_http = ttk.Combobox(
            bar_http,
            values=["Todos", "POST", "GET", "PUT", "DELETE", "HEAD",
                    "OPTIONS", "PATCH", "TRACE", "CONNECT"],
            width=8, state="readonly")
        self.combo_filtro_http.set("Todos")
        self.combo_filtro_http.pack(side="left", padx=4)
        self.combo_filtro_http.bind("<<ComboboxSelected>>", self.aplicar_filtro_http)

        pw_http = ttk.PanedWindow(aba_http, orient=tk.VERTICAL)
        pw_http.pack(fill="both", expand=True, padx=4, pady=4)

        frame_thttp = ttk.Frame(pw_http)
        cols2 = ("metodo", "host", "uri", "src", "dst")
        self.tree_http = ttk.Treeview(frame_thttp, columns=cols2, show="headings")
        for cid, txt, w in (("metodo", "Método", 80), ("host", "Host", 220),
                            ("uri", "URI", 300), ("src", "Origem", 140),
                            ("dst", "Destino", 140)):
            self.tree_http.heading(cid, text=txt)
            self.tree_http.column(cid, width=w)
        scroll_y_http = ttk.Scrollbar(
            frame_thttp, orient="vertical", command=self.tree_http.yview)
        self.tree_http.configure(yscrollcommand=scroll_y_http.set)
        scroll_y_http.pack(side="right", fill="y")
        self.tree_http.pack(fill="both", expand=True)
        self.tree_http.bind("<<TreeviewSelect>>", self.mostrar_detalhe_http)
        pw_http.add(frame_thttp, weight=2)

        frame_detalhe_http = ttk.Frame(pw_http)
        self.txt_detalhe = tk.Text(
            frame_detalhe_http, wrap="word", font=("Consolas", 10))
        scroll_txt_http = ttk.Scrollbar(
            frame_detalhe_http, orient="vertical",
            command=self.txt_detalhe.yview)
        self.txt_detalhe.configure(yscrollcommand=scroll_txt_http.set)
        scroll_txt_http.pack(side="right", fill="y")
        self.txt_detalhe.pack(fill="both", expand=True)
        pw_http.add(frame_detalhe_http, weight=1)

        # ---- Aba 3: SNI ----
        aba_tls = ttk.Frame(self.nb)
        self.nb.add(aba_tls, text="Sites HTTPS (SNI)")
        cols_tls = ("src", "dst", "snis", "client_random")
        self.tree_tls = ttk.Treeview(aba_tls, columns=cols_tls, show="headings")
        for cid, txt, w in (("src", "Origem", 160), ("dst", "Destino", 160),
                            ("snis", "Domínio (SNI)", 280),
                            ("client_random", "Client Random", 400)):
            self.tree_tls.heading(cid, text=txt)
            self.tree_tls.column(cid, width=w)
        self.tree_tls.pack(fill="both", expand=True)

        # ---- Aba 4: Chaves ----
        aba_keys = ttk.Frame(self.nb)
        self.nb.add(aba_keys, text="Chaves TLS")
        cols_k = ("client_random", "label", "site", "secret")
        self.tree_keys = ttk.Treeview(aba_keys, columns=cols_k, show="headings")
        for cid, txt, w in (("client_random", "Client Random", 320),
                            ("label", "Tipo", 240), ("site", "Site (SNI)", 220),
                            ("secret", "Secret (início)", 220)):
            self.tree_keys.heading(cid, text=txt)
            self.tree_keys.column(cid, width=w)
        self.tree_keys.pack(fill="both", expand=True)

        # ---- Aba 5: Relatório ----
        aba_res = ttk.Frame(self.nb)
        self.nb.add(aba_res, text="📄 Relatório / Todos os Resultados")

        bar_res = ttk.Frame(aba_res, padding=4)
        bar_res.pack(fill="x")

        ttk.Label(bar_res, text="Filtro Rápido:").pack(side="left")
        self.combo_filtro_res = ttk.Combobox(
            bar_res,
            values=["Todos", "POST", "GET", "PUT", "DELETE", "TLS"],
            width=8, state="readonly")
        self.combo_filtro_res.set("Todos")
        self.combo_filtro_res.pack(side="left", padx=4)
        self.combo_filtro_res.bind(
            "<<ComboboxSelected>>", lambda e: self.gerar_relatorio())

        ttk.Label(bar_res, text=" Pesquisar:").pack(side="left", padx=(10, 0))
        self.ent_busca_res = ttk.Entry(bar_res, width=20)
        self.ent_busca_res.pack(side="left", padx=4)
        self.ent_busca_res.bind("<Return>", self.buscar_no_relatorio)
        ttk.Button(bar_res, text="🔍 Buscar",
                   command=self.buscar_no_relatorio).pack(side="left")

        btn_html = tk.Button(
            bar_res, text="💾 Salvar HTML Completo",
            bg="#0056b3", fg="white", font=("Arial", 9, "bold"),
            command=self.salvar_html)
        btn_html.pack(side="right", padx=10)

        self.txt_resultados = tk.Text(
            aba_res, wrap="word", font=("Consolas", 10))
        scroll_res = ttk.Scrollbar(
            aba_res, orient="vertical", command=self.txt_resultados.yview)
        self.txt_resultados.configure(yscrollcommand=scroll_res.set)
        scroll_res.pack(side="right", fill="y")
        self.txt_resultados.pack(fill="both", expand=True, padx=4, pady=4)
        self.txt_resultados.tag_configure(
            "highlight", foreground="red", background="yellow",
            font=("Consolas", 10, "bold"))

        self.status_bar = ttk.Label(self, text="Pronto.", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

    # ---------- arquivos ----------
    def abrir_keylog(self):
        path = filedialog.askopenfilename(
            title="sslkeylog.log",
            filetypes=[("Arquivos de Log", "*.log;*.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            self.keylog = parse_keylog(path)
            self.keylog_path = path
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.atualizar_keys()
        self.lbl_status.config(
            text=f"Chaves: {len(self.keylog)} | Agora abra o pcap")
        if self.pcap_path:
            self.rodar_analise_profunda()

    def abrir_pcap(self):
        path = filedialog.askopenfilename(
            title="Captura de Rede",
            filetypes=[("Arquivos PCAP", "*.pcapng;*.pcap;*.cap"),
                       ("Todos", "*.*")])
        if path:
            self.carregar_pcap(path)

    def analisar_resultados(self):
        nome = "resultados.pcapng"
        candidatos = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), nome),
            os.path.join(os.getcwd(), nome),
            nome,
        ]
        path = next((c for c in candidatos if os.path.isfile(c)), None)
        if not path:
            path = filedialog.askopenfilename(
                title="Selecione resultados.pcapng",
                filetypes=[("Arquivos PCAP", "*.pcapng;*.pcap;*.cap")])
            if not path:
                return
        self.carregar_pcap(path, nome_exibido=nome)

    def carregar_pcap(self, path, nome_exibido=None):
        self.pcap_nome = nome_exibido or os.path.basename(path)
        self.pcap_path = path
        self.lbl_status.config(text=f"Lendo {self.pcap_nome}…")
        self.update_idletasks()
        try:
            self.handshakes = extrair_handshakes_tls(path)
            self.snis = snis_por_client_random(self.handshakes)
            self.http_requests = extrair_http_requests(path)
        except Exception as e:
            messagebox.showerror("Erro ao ler pcap", str(e))
            return
        self.atualizar_keys()
        self.atualizar_tls()
        self.aplicar_filtro_http()
        self.gerar_relatorio()
        self.lbl_status.config(text=f"Pronto: {self.pcap_nome}")

        if not self.keylog_path:
            cand = os.path.join(os.path.dirname(path), "sslkeylog.log")
            if os.path.isfile(cand):
                try:
                    self.keylog = parse_keylog(cand)
                    self.keylog_path = cand
                    self.atualizar_keys()
                except Exception:
                    pass
        if self.keylog_path:
            self.after(200, self.rodar_analise_profunda)

    def atualizar_keys(self):
        self.tree_keys.delete(*self.tree_keys.get_children())
        for e in self.keylog:
            site = ", ".join(
                self.snis.get(e["client_random"].lower(), [])) or "—"
            secret = (e["secret"][:28] + "…"
                      if len(e["secret"]) > 28 else e["secret"])
            self.tree_keys.insert(
                "", "end",
                values=(e["client_random"], e["label"], site, secret))

    def atualizar_tls(self):
        self.tree_tls.delete(*self.tree_tls.get_children())
        for h in self.handshakes:
            self.tree_tls.insert("", "end", values=(
                f"{h['src']}:{h['sport']}", f"{h['dst']}:{h['dport']}",
                ", ".join(h["snis"]) or "—", h["client_random"]))

    def aplicar_filtro_http(self, event=None):
        filtro = self.combo_filtro_http.get().upper()
        self.tree_http.delete(*self.tree_http.get_children())
        self.http_exibidos = []
        for r in self.http_requests:
            metodo = str(r.get("metodo") or "").strip().upper()
            if filtro == "TODOS" or filtro == metodo:
                self.tree_http.insert("", "end", values=(
                    r["metodo"], r["host"] or "—", r["uri"],
                    f"{r['src']}:{r['sport']}", f"{r['dst']}:{r['dport']}"))
                self.http_exibidos.append(r)

    def mostrar_detalhe_http(self, event=None):
        sel = self.tree_http.selection()
        self.txt_detalhe.delete("1.0", "end")
        if not sel:
            return
        try:
            r = self.http_exibidos[self.tree_http.index(sel[0])]
        except Exception:
            return
        self.txt_detalhe.insert("end", "=== Método HTTP ===\n")
        self.txt_detalhe.insert("end", f"{r['metodo']} {r['host']}{r['uri']}\n")
        self.txt_detalhe.insert(
            "end",
            f"Conexão: {r['src']}:{r['sport']} → {r['dst']}:{r['dport']}\n\n")
        self.txt_detalhe.insert("end", "--- Cabeçalhos (Headers) ---\n")
        for k, v in r["headers"].items():
            self.txt_detalhe.insert("end", f"{k}: {v}\n")
        if r["body"]:
            self.txt_detalhe.insert(
                "end", f"\n--- Corpo ---\n{limpar_texto(r['body'], 3000)}\n")

    def aplicar_filtro_tabela(self, event=None):
        if not self.dados_deep:
            return
        filtro = self.combo_filtro.get().upper()
        self.tree_deep.delete(*self.tree_deep.get_children())
        exibidos = 0
        for p in self.dados_deep:
            met = str(p.get("metodo") or "").upper()
            info = str(p.get("info") or "").upper()
            mostrar = False
            if filtro == "TODOS":
                mostrar = True
            elif filtro == "TLS":
                if "TLS" in info and not met:
                    mostrar = True
            elif filtro in met:
                mostrar = True
            if mostrar:
                self.tree_deep.insert("", "end", values=(
                    p["num"], p.get("metodo") or "", p.get("host") or "",
                    p.get("uri") or "", p["src"], p["dst"],
                    p.get("info") or ""))
                exibidos += 1
        self.lbl_deep.config(
            text=f"Exibindo {exibidos} pacotes de {len(self.dados_deep)} analisados")

    def rodar_analise_profunda(self):
        if not self.pcap_path:
            self.analisar_resultados()
            if not self.pcap_path:
                return
        if not self.keylog_path:
            cand = os.path.join(
                os.path.dirname(self.pcap_path), "sslkeylog.log")
            if os.path.isfile(cand):
                self.keylog = parse_keylog(cand)
                self.keylog_path = cand
                self.atualizar_keys()

        self.tshark_path = encontrar_tshark(self.tshark_path)
        regex = self.ent_regex.get().strip()
        df = self.ent_df.get().strip()
        self.lbl_deep.config(text="Descriptografando… aguarde")
        self.update_idletasks()

        def prog(n):
            self.lbl_deep.config(text=f"Processando pacote {n}…")
            self.update_idletasks()

        try:
            pacotes, total = analise_profunda(
                self.pcap_path, self.keylog_path,
                filtro_regex=regex, display_filter=df,
                limite=800, tshark_path=self.tshark_path, progresso=prog)
            self.total_deep_analisados = total
        except Exception as e:
            self.lbl_deep.config(text="")
            messagebox.showerror("Erro na análise", str(e))
            return

        self.dados_deep = pacotes
        self.aplicar_filtro_tabela()
        self.gerar_relatorio()
        self.nb.select(0)

    def mostrar_detalhe_deep(self, event=None):
        sel = self.tree_deep.selection()
        self.txt_detalhe_deep.delete("1.0", "end")
        if not sel:
            return
        num_pacote = self.tree_deep.item(sel[0])["values"][0]
        p = next(
            (x for x in self.dados_deep if str(x["num"]) == str(num_pacote)),
            None)
        if not p:
            return
        lines = [
            f"Pacote #{p['num']}  {p['hora']}",
            f"Protocolos: {p['protocolos']}",
            f"{p['src']}  →  {p['dst']}", "",
        ]
        if p.get("metodo") or p.get("host") or p.get("uri"):
            lines += [
                "=== Método HTTP ===",
                f"Método : {p.get('metodo')}",
                f"Host   : {p.get('host')}",
                f"URI    : {p.get('uri')}", "",
            ]
        if p.get("headers_raw"):
            lines += ["--- Cabeçalhos (Headers) ---", p["headers_raw"], ""]
        if p.get("tls"):
            lines += [f"--- TLS ---\n{p['tls']}", ""]
        if p.get("corpo"):
            lines += ["--- Corpo da Requisição ---", p["corpo"], ""]
        lines.append(f"Resumo: {p.get('info')}")
        self.txt_detalhe_deep.insert("end", "\n".join(lines))

    def gerar_relatorio(self):
        filtro = self.combo_filtro_res.get().upper()
        txt = self.txt_resultados
        txt.delete("1.0", "end")
        linha = "=" * 70 + "\n"
        txt.insert("end", linha)
        txt.insert(
            "end",
            f"RELATÓRIO GERAL — {self.pcap_nome} (Filtro: {filtro})\n")
        txt.insert("end", linha + "\n")

        txt.insert("end", ">>> SITES ACESSADOS (SNI) <<<\n")
        if self.snis:
            for s in sorted({x for l in self.snis.values() for x in l}):
                txt.insert("end", f"  • {s}\n")
        else:
            txt.insert("end", "  (nenhum)\n")
        txt.insert("end", "\n")

        txt.insert("end", ">>> CHAVES TLS (keylog) <<<\n")
        if self.keylog:
            for e in self.keylog:
                site = ", ".join(
                    self.snis.get(e["client_random"].lower(), [])) or "—"
                txt.insert(
                    "end",
                    f"  {e['client_random']}  [{e['label']}]  {site}\n")
        else:
            txt.insert("end", "  (nenhum keylog)\n")
        txt.insert("end", "\n")

        txt.insert("end", ">>> REQUISIÇÕES HTTP (Texto Claro) <<<\n")
        count_http = 0
        for i, r in enumerate(self.http_requests, 1):
            metodo = str(r.get("metodo") or "").strip().upper()
            if filtro not in ("TODOS", "TLS") and filtro != metodo:
                continue
            if filtro == "TLS":
                continue
            count_http += 1
            txt.insert("end", f"\n--- Requisição #{i} ---\n")
            txt.insert("end", f"  Método : {r['metodo']}\n")
            txt.insert("end", f"  Host   : {r['host'] or '—'}\n")
            txt.insert("end", f"  URI    : {r['uri']}\n")
            txt.insert(
                "end",
                f"  Origem : {r['src']}:{r['sport']} -> "
                f"{r['dst']}:{r['dport']}\n")
            txt.insert("end", "  Cabeçalhos:\n")
            for k, v in r["headers"].items():
                txt.insert("end", f"    {k}: {v}\n")
            if r.get("body"):
                txt.insert(
                    "end", f"  Corpo: {limpar_texto(r['body'], 300)}\n")
        if count_http == 0:
            txt.insert("end", "  (nenhuma)\n")
        txt.insert("end", "\n")

        txt.insert("end", ">>> ANÁLISE PROFUNDA (HTTPS DESCRIPTOGRAFADO) <<<\n")
        if not self.dados_deep:
            txt.insert("end", "  (Ainda não processado ou sem resultados)\n")
        else:
            count_deep = 0
            for p in self.dados_deep:
                met = str(p.get("metodo") or "").upper()
                info = str(p.get("info") or "").upper()
                mostrar = False
                if filtro == "TODOS":
                    mostrar = True
                elif filtro == "TLS":
                    if "TLS" in info and not met:
                        mostrar = True
                elif filtro in met:
                    mostrar = True
                if not mostrar:
                    continue
                if not p.get("metodo") and not p.get("tls"):
                    continue
                count_deep += 1
                txt.insert("end", f"\n--- Pacote #{p['num']} ---\n")
                txt.insert("end", f"    {p['src']} -> {p['dst']}\n")
                if p.get("metodo"):
                    txt.insert(
                        "end",
                        f"    {p.get('metodo')} "
                        f"{p.get('host', '')}{p.get('uri', '')}\n")
                if p.get("headers_raw"):
                    txt.insert("end", "    Cabeçalhos:\n")
                    for h_line in p["headers_raw"].split("\n"):
                        if h_line.strip():
                            txt.insert("end", f"      {h_line.strip()}\n")
                if p.get("corpo"):
                    txt.insert("end", f"    Corpo: {p['corpo'][:150]}\n")
                if p.get("tls"):
                    txt.insert("end", f"    TLS: {p['tls']}\n")
            if count_deep == 0:
                txt.insert("end", "  (nenhum pacote corresponde ao filtro)\n")
        txt.insert("end", "\n" + linha + "\n")

    def buscar_no_relatorio(self, event=None):
        termo = self.ent_busca_res.get().strip()
        self.txt_resultados.tag_remove("highlight", "1.0", tk.END)
        if not termo:
            return
        idx = "1.0"
        primeiro = None
        while True:
            idx = self.txt_resultados.search(
                termo, idx, nocase=True, stopindex=tk.END)
            if not idx:
                break
            if not primeiro:
                primeiro = idx
            fim = f"{idx}+{len(termo)}c"
            self.txt_resultados.tag_add("highlight", idx, fim)
            idx = fim
        if primeiro:
            self.txt_resultados.see(primeiro)

    def salvar_html(self):
        path = filedialog.asksaveasfilename(
            title="Salvar Relatório HTML",
            defaultextension=".html",
            initialfile=f"Relatorio_{self.pcap_nome or 'captura'}.html",
            filetypes=[("Página HTML", "*.html")])
        if not path:
            return

        def get_badge_class(metodo):
            m = str(metodo).upper()
            if "GET" in m:
                return "bg-green"
            if "POST" in m:
                return "bg-orange"
            if "PUT" in m:
                return "bg-blue"
            if "DELETE" in m:
                return "bg-red"
            if "STATUS" in m or m.isdigit():
                return "bg-teal"
            if "TLS" in m:
                return "bg-purple"
            return "bg-gray"

        html_code = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório de Tráfego - {html.escape(self.pcap_nome or '')}</title>
<style>
:root {{ --primary:#2c3e50; --secondary:#34495e; --accent:#3498db; --dark:#282c34; }}
body {{ font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background:#eef2f5; color:#333; margin:0; padding:0; }}
header {{ background:var(--primary); color:#fff; padding:20px 40px; box-shadow:0 4px 6px rgba(0,0,0,.1); }}
header h1 {{ margin:0; font-size:24px; }}
header p {{ margin:5px 0 0; color:#bdc3c7; font-size:14px; }}
nav {{ background:var(--secondary); padding:10px 40px; position:sticky; top:0; z-index:1000; }}
nav a {{ color:#fff; text-decoration:none; margin-right:20px; font-size:14px; font-weight:bold; }}
nav a:hover {{ color:var(--accent); }}
.container {{ max-width:1200px; margin:30px auto; padding:0 20px; }}
h2 {{ color:var(--primary); border-bottom:3px solid var(--accent); padding-bottom:8px; margin-top:40px; }}
.card {{ background:#fff; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,.08); padding:20px; margin-bottom:25px; border-left:5px solid var(--primary); }}
.card-header {{ display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:15px; flex-wrap:wrap; gap:8px; }}
.card-title {{ margin:0; font-size:18px; color:var(--primary); word-break:break-all; }}
.connection-info {{ font-size:13px; color:#7f8c8d; background:#f1f2f6; padding:4px 10px; border-radius:20px; font-family:Consolas,monospace; }}
.badge {{ display:inline-block; padding:4px 10px; border-radius:4px; font-size:12px; font-weight:bold; color:#fff; margin-right:10px; }}
.bg-green {{ background:#27ae60; }} .bg-orange {{ background:#d35400; }}
.bg-blue {{ background:#2980b9; }} .bg-red {{ background:#c0392b; }}
.bg-teal {{ background:#16a085; }} .bg-purple {{ background:#8e44ad; }}
.bg-gray {{ background:#7f8c8d; }}
.data-block {{ margin-top:15px; border-radius:5px; overflow:hidden; }}
.data-title {{ font-size:13px; font-weight:bold; padding:5px 10px; color:#fff; margin:0; }}
.data-content {{ margin:0; padding:15px; font-family:Consolas,monospace; font-size:13px; white-space:pre-wrap; word-wrap:break-word; }}
.block-headers .data-title {{ background:#f39c12; }}
.block-headers .data-content {{ background:#fffbe6; color:#333; border:1px solid #f39c12; border-top:none; }}
.block-body .data-title {{ background:var(--secondary); }}
.block-body .data-content {{ background:var(--dark); color:#2ecc71; border:1px solid var(--secondary); border-top:none; }}
.block-tls .data-title {{ background:#8e44ad; }}
.block-tls .data-content {{ background:#f5eef8; color:#333; border:1px solid #8e44ad; border-top:none; }}
table {{ width:100%; border-collapse:collapse; background:#fff; box-shadow:0 2px 10px rgba(0,0,0,.08); border-radius:8px; overflow:hidden; }}
th,td {{ border:1px solid #eee; padding:12px; text-align:left; font-size:14px; }}
th {{ background:var(--primary); color:#fff; }}
tr:hover {{ background:#f1f2f6; }}
.sni-tag {{ display:inline-block; background:#3498db; color:#fff; padding:6px 12px; border-radius:20px; font-size:13px; margin:5px 5px 5px 0; }}
</style>
</head>
<body>
<header>
  <h1>🌐 Relatório de Análise de Tráfego</h1>
  <p>Arquivo: <strong>{html.escape(self.pcap_nome or '')}</strong></p>
</header>
<nav>
  <a href="#sni">📍 Domínios (SNI)</a>
  <a href="#http">📄 HTTP Claro</a>
  <a href="#https">🔐 HTTPS Descriptografado</a>
  <a href="#keys">🔑 Chaves TLS</a>
</nav>
<div class="container">
<h2 id="sni">📍 Domínios HTTPS Acessados (SNI)</h2>
<div class="card" style="border-left-color:#3498db;">
"""
        if self.snis:
            for s in sorted({x for l in self.snis.values() for x in l}):
                html_code += f"<span class='sni-tag'>{html.escape(s)}</span>"
        else:
            html_code += "<p>Nenhum domínio SNI detectado.</p>"
        html_code += "</div>"

        html_code += "<h2 id='http'>📄 Requisições HTTP (Texto Claro)</h2>"
        if self.http_requests:
            for r in self.http_requests:
                badge = get_badge_class(r["metodo"])
                html_code += f"""
<div class='card' style='border-left-color:#f39c12;'>
  <div class='card-header'>
    <h3 class='card-title'><span class='badge {badge}'>{html.escape(r['metodo'])}</span>
      {html.escape(r['host'] or '')}{html.escape(r['uri'])}</h3>
    <span class='connection-info'>{html.escape(r['src'])}:{r['sport']} &rarr; {html.escape(r['dst'])}:{r['dport']}</span>
  </div>
  <div class='data-block block-headers'>
    <p class='data-title'>Cabeçalhos (Headers)</p>
    <pre class='data-content'>{html.escape(chr(10).join(f'{k}: {v}' for k,v in r['headers'].items()))}</pre>
  </div>"""
                if r.get("body"):
                    html_code += f"""
  <div class='data-block block-body'>
    <p class='data-title'>Corpo (Payload)</p>
    <pre class='data-content'>{html.escape(r['body'][:3000])}</pre>
  </div>"""
                html_code += "</div>"
        else:
            html_code += "<p>Nenhum tráfego HTTP claro.</p>"

        html_code += "<h2 id='https'>🔐 Análise Profunda (HTTPS Descriptografado)</h2>"
        if self.dados_deep:
            for p in self.dados_deep:
                if not p.get("metodo") and not p.get("tls"):
                    continue
                is_tls = not p.get("metodo")
                b_color = "#8e44ad" if is_tls else "#27ae60"
                badge = get_badge_class(p.get("metodo") or "TLS")
                metodo_text = html.escape(p.get("metodo") or "Handshake TLS")
                url_text = html.escape(f"{p.get('host','')}{p.get('uri','')}")
                html_code += f"""
<div class='card' style='border-left-color:{b_color};'>
  <div class='card-header'>
    <h3 class='card-title'><span class='badge {badge}'>{metodo_text}</span> {url_text}</h3>
    <span class='connection-info'>Pct #{p['num']} | {html.escape(p['src'])} &rarr; {html.escape(p['dst'])}</span>
  </div>"""
                if p.get("headers_raw"):
                    html_code += f"""
  <div class='data-block block-headers'>
    <p class='data-title'>Cabeçalhos Descriptografados</p>
    <pre class='data-content'>{html.escape(p['headers_raw'])}</pre>
  </div>"""
                if p.get("corpo"):
                    html_code += f"""
  <div class='data-block block-body'>
    <p class='data-title'>Corpo Descriptografado</p>
    <pre class='data-content'>{html.escape(p['corpo'][:3000])}</pre>
  </div>"""
                if p.get("tls"):
                    html_code += f"""
  <div class='data-block block-tls'>
    <p class='data-title'>TLS</p>
    <pre class='data-content'>{html.escape(p['tls'])}</pre>
  </div>"""
                html_code += "</div>"
        else:
            html_code += "<p>Sem resultados profundos.</p>"

        html_code += "<h2 id='keys'>🔑 Chaves Criptográficas</h2>"
        if self.keylog:
            html_code += ("<table><tr><th>Client Random</th>"
                          "<th>Tipo</th><th>Site (SNI)</th></tr>")
            for e in self.keylog:
                site = ", ".join(
                    self.snis.get(e["client_random"].lower(), []))
                html_code += (
                    f"<tr><td><code>{html.escape(e['client_random'])}</code></td>"
                    f"<td>{html.escape(e['label'])}</td>"
                    f"<td>{html.escape(site)}</td></tr>")
            html_code += "</table>"
        else:
            html_code += "<p>Nenhum keylog.</p>"

        html_code += "</div></body></html>"

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_code)
            messagebox.showinfo(
                "Relatório Salvo",
                f"HTML gerado com sucesso!\n\n{path}")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))


# ============================================================
# INICIALIZAÇÃO SEGURA DA APLICAÇÃO
# ============================================================
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        root_crash = tk.Tk()
        root_crash.withdraw()
        messagebox.showerror(
            "Erro de Execução",
            f"Ocorreu um erro ao iniciar a aplicação:\n\n{e}"
        )
        sys.exit(1)
