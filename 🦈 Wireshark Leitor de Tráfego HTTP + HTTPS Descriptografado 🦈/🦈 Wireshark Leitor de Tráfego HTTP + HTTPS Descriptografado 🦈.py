#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitor de Tráfego HTTP + HTTPS (descriptografado com sslkeylog + tshark)
- Modo Escuro (Dark Mode) Corrigido para Windows (Textos Verdes, Fundos Escuros)
- Coloração de Sintaxe (Corpo = Vermelho, Headers = Azul)
- Display Filter e Regex GLOBAIS
- Filtros padronizados (POST, GET, TCP, UDP...) em todas as abas
- Seguir Fluxo TLS/HTTP (Botão Direito)
- Sem erros de sintaxe
"""

import sys
import os
import subprocess
import threading
import time
import asyncio
import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import re
import shutil
import html

# ============================================================
# WINDOWS — OCULTAR TODAS AS JANELAS
# ============================================================
if sys.platform == "win32":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

    CREATE_NO_WINDOW = 0x08000000
    _OriginalPopen = subprocess.Popen
    class PopenSemJanela(_OriginalPopen):
        def __init__(self, *args, **kwargs):
            kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    subprocess.Popen = PopenSemJanela

    _orig_create_subprocess_exec = asyncio.create_subprocess_exec
    async def _hidden_create_subprocess_exec(*args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
        return await _orig_create_subprocess_exec(*args, **kwargs)
    asyncio.create_subprocess_exec = _hidden_create_subprocess_exec

try:
    import pyshark
except ImportError:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror("Biblioteca Ausente", "A biblioteca 'pyshark' não está instalada.\n\nExecute: pip install pyshark")
    sys.exit(1)


# ================= Util =================

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
            if (re.fullmatch(r'[0-9a-fA-F:]+', s.replace(' ', '')) and len(s) > 8):
                hx = s.replace(':', '').replace(' ', '')
                if len(hx) % 2 == 0:
                    corpo = bytes.fromhex(hx).decode('utf-8', errors='replace')
                else:
                    corpo = s
            else:
                corpo = s
            return limpar_texto(corpo, 20000)
        except Exception:
            continue
    return ""


# ================= Parser do sslkeylog.log =================

def parse_keylog(path, callback=None):
    entradas = []
    total_linhas = 0
    with open(path, "r", errors="replace") as f:
        for _ in f:
            total_linhas += 1

    ultimo_pct = [-1]
    with open(path, "r", errors="replace") as f:
        for n, linha in enumerate(f, 1):
            if callback and total_linhas > 0 and n % 50 == 0:
                pct = int((n / total_linhas) * 100)
                if pct > ultimo_pct[0]:
                    ultimo_pct[0] = pct
                    callback(pct, f"Lendo linha {n}/{total_linhas}")

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
            if label in ("CLIENT_RANDOM",) or ("SECRET" in label and "CLIENT" in label) or label.endswith("_SECRET"):
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

def ler_pcap_ou_pcapng(caminho, callback=None):
    tamanho_arquivo = os.path.getsize(caminho)
    bytes_lidos = [0]
    ultimo_pct = [-1]

    with open(caminho, "rb") as f:
        magic = f.read(4)
        bytes_lidos[0] += 4

        def reportar_progresso():
            if callback and tamanho_arquivo > 0:
                pct = min(int((bytes_lidos[0] / tamanho_arquivo) * 100), 99)
                if pct > ultimo_pct[0]:
                    ultimo_pct[0] = pct
                    callback(pct)

        if magic in (b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4", b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d"):
            endian = "<" if magic[:2] in (b"\xd4\xc3", b"\x4d\x3c") else ">"
            f.read(20)
            bytes_lidos[0] += 20
            pkt_count = 0
            while True:
                hdr = f.read(16)
                if len(hdr) < 16:
                    break
                bytes_lidos[0] += 16
                _, _, caplen, _ = struct.unpack(endian + "IIII", hdr)
                if caplen > 0x400000:
                    break
                dados = f.read(caplen)
                bytes_lidos[0] += len(dados)
                if len(dados) < caplen:
                    break
                pkt_count += 1
                if pkt_count % 100 == 0:
                    reportar_progresso()
                res = processar_pacote(dados)
                if res:
                    yield res
            return

        if magic == b"\x0a\x0d\x0d\x0a":
            endian = "<"
            f.seek(0)
            bytes_lidos[0] = 0
            blk_count = 0
            while True:
                hdr = f.read(8)
                if len(hdr) < 8:
                    break
                bytes_lidos[0] += 8
                blk_type, blk_len = struct.unpack("<II", hdr)
                if blk_len < 12 or blk_len % 4 != 0:
                    blk_type, blk_len = struct.unpack(">II", hdr)
                    if blk_len < 12 or blk_len % 4 != 0:
                        break
                    endian = ">"
                corpo = f.read(max(0, blk_len - 12))
                f.read(4)
                bytes_lidos[0] += max(0, blk_len - 12) + 4
                blk_count += 1
                if blk_count % 100 == 0:
                    reportar_progresso()

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

def extrair_handshakes_tls(pcap_path, callback=None):
    handshakes = []
    stream_buf = {}
    for src, sport, dst, dport, payload in ler_pcap_ou_pcapng(pcap_path, callback=callback):
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


# ================= HTTP texto claro =================

def extrair_http_requests(pcap_path, callback=None):
    streams = {}
    for src, sport, dst, dport, payload in ler_pcap_ou_pcapng(pcap_path, callback=callback):
        if not payload:
            continue
        chave = (src, sport, dst, dport)
        streams[chave] = streams.get(chave, b"") + payload

    METODOS = (b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ",
               b"OPTIONS ", b"PATCH ", b"TRACE ", b"CONNECT ")
    requests = []
    total_streams = len(streams)
    ultimo_pct = [-1]

    for idx, ((src, sport, dst, dport), buf) in enumerate(streams.items()):
        if callback and total_streams > 0:
            pct = int((idx / total_streams) * 100)
            if pct > ultimo_pct[0]:
                ultimo_pct[0] = pct
                callback(pct)

        pos = 0
        while pos < len(buf):
            i_min, metodo = -1, None
            for m in METODOS:
                i = buf.find(m, pos)
                if i != -1 and (i_min == -1 or i < i_min):
                    i_min, metodo = i, m
            if i_min == -1:
                break
            fim_header = buf.find(b"\r\n\r\n", i_min)
            if fim_header == -1:
                break
            linhas = buf[i_min:fim_header].split(b"\r\n")
            partes = linhas[0].decode(errors="replace").split()
            if len(partes) < 2:
                pos = fim_header + 4
                continue
            metodo_req, uri = partes[0], partes[1]
            headers = {}
            for linha in linhas[1:]:
                if b":" in linha:
                    k, _, v = linha.partition(b":")
                    headers[k.decode(errors="replace").strip()] = v.decode(errors="replace").strip()
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


# ================= Análise profunda =================

def analise_profunda(pcap_path, keylog_path, filtro_regex="", display_filter="", limite=800, tshark_path=None, progresso=None):
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
    ultimo_tempo = [time.time()]

    for pkt in cap:
        total += 1
        if progresso and total % 10 == 0:
            agora = time.time()
            if agora - ultimo_tempo[0] > 0.1:
                ultimo_tempo[0] = agora
                progresso(total)
        try:
            resumo = {
                "num": str(getattr(pkt, "number", "")),
                "hora": str(getattr(pkt, "sniff_time", "")),
                "protocolos": " ".join(l.layer_name for l in pkt.layers),
                "src": "", "dst": "",
                "info": "", "http": "", "tls": "",
                "metodo": "", "host": "", "uri": "",
                "corpo": "", "headers_raw": "",
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
                host = g("headers_authority", "header_authority", "authority", "headers_host")
                scheme = g("headers_scheme", "header_scheme") or "https"

                if metodo or status or uri or host:
                    resumo["metodo"] = (metodo or status or resumo["metodo"])
                    resumo["host"] = host or resumo["host"]
                    resumo["uri"] = uri or resumo["uri"]
                    if metodo:
                        resumo["http"] = limpar_texto(f"[HTTPS/2] {metodo} {scheme}://{host}{uri}", 180)
                    elif status:
                        resumo["http"] = limpar_texto(f"[HTTPS/2] Status {status}", 80)
                    else:
                        resumo["http"] = limpar_texto(f"[HTTPS/2] {host}{uri}", 180)

            if hasattr(pkt, "tls"):
                t = pkt.tls
                sni = ""
                try:
                    sni = str(t.handshake_extensions_server_name)
                except Exception:
                    pass
                hs = getattr(t, "handshake_type", None)
                resumo["tls"] = limpar_texto("TLS" + (f" hs={hs}" if hs else "") + (f" SNI={sni}" if sni else ""), 120)
                if sni and not resumo["host"]:
                    resumo["host"] = sni

            resumo["info"] = limpar_texto(resumo["http"] or resumo["tls"] or resumo["protocolos"], 180)
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


# ================= Interface Principal =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🦈 Wireshark Leitor de Tráfego HTTP + HTTPS Descriptografado 🦈")
        self.geometry("1280x760")
        self.state("zoomed")

        # ATIVA MODO ESCURO POR PADRÃO
        self.is_dark_mode = True
        self.text_widgets = []

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
        self.todos_protocolos_dados = []
        self.ultimo_clique_treeview = None

        self.OPCOES_FILTRO_GERAL = ["Todos", "TCP", "UDP", "TLS", "HTTP", "POST", "GET", "PUT", "DELETE", "DNS", "ICMP", "ARP"]

        self.menu_contexto = tk.Menu(self, tearoff=0)
        self.menu_contexto.add_command(label="🔄 Seguir Fluxo TLS/HTTP (Estilo Wireshark)", command=self._acionar_seguir_fluxo)

        # ---- Topo ----
        self.topo = ttk.Frame(self, padding=8)
        self.topo.pack(fill="x")

        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))
        style.configure("Prog.Horizontal.TProgressbar", thickness=15)

        self.frame_botoes = tk.Frame(self.topo)
        self.frame_botoes.pack(fill="x", pady=(0, 5))

        ttk.Button(self.frame_botoes, text="1. Abrir sslkeylog.log (Manual)", command=self.abrir_keylog).pack(side="left", padx=5)
        ttk.Button(self.frame_botoes, text="2. Abrir .pcap / .pcapng", command=self.abrir_pcap).pack(side="left", padx=5)
        ttk.Button(self.frame_botoes, text="Analisar resultados.pcapng", command=self.analisar_resultados).pack(side="left", padx=5)

        btn_deep = tk.Button(self.frame_botoes, text="▶ DESCRIPTOGRAFAR", bg="#2980b9", fg="white", font=("Arial", 10, "bold"), command=self.rodar_analise_profunda)
        btn_deep.pack(side="left", padx=10)

        self.lbl_regex = ttk.Label(self.frame_botoes, text="Regex:", font=("Arial", 9, "bold"))
        self.lbl_regex.pack(side="left", padx=(15, 2))
        self.ent_regex = ttk.Entry(self.frame_botoes, width=12)
        self.ent_regex.insert(0, "http|tls")
        self.ent_regex.pack(side="left")

        self.lbl_df = ttk.Label(self.frame_botoes, text="Display Filter:", font=("Arial", 9, "bold"))
        self.lbl_df.pack(side="left", padx=(15, 2))
        self.ent_df = ttk.Entry(self.frame_botoes, width=35)
        self.ent_df.insert(0, "http or http2 or tls.handshake.type == 1")
        self.ent_df.pack(side="left")

        self.btn_theme = tk.Button(self.frame_botoes, text="☀️ Modo Claro", bg="#f1c40f", fg="black", font=("Arial", 9, "bold"), command=self._toggle_theme)
        self.btn_theme.pack(side="right", padx=10)

        self.lbl_status = ttk.Label(self.frame_botoes, text="Carregue a chave (sslkeylog) e depois a captura (pcap)", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side="right", padx=8)

        # ---- Progresso ----
        self.frame_progresso = tk.Frame(self, bg="#ecf0f1", height=30)
        self.frame_progresso.pack(fill="x")
        self.frame_progresso.pack_propagate(False)

        self.lbl_prog_msg = tk.Label(self.frame_progresso, text="", font=("Arial", 9, "bold"), bg="#ecf0f1", width=35, anchor="e")
        self.lbl_prog_msg.pack(side="left", padx=10)

        self.barra_progresso = ttk.Progressbar(self.frame_progresso, orient="horizontal", mode="determinate", style="Prog.Horizontal.TProgressbar")
        self.barra_progresso.pack(side="left", fill="x", expand=True, padx=5, pady=6)

        self.lbl_prog_pct = tk.Label(self.frame_progresso, text="", font=("Arial", 10, "bold"), bg="#ecf0f1", width=5)
        self.lbl_prog_pct.pack(side="left", padx=5)

        self.lbl_prog_detalhe = tk.Label(self.frame_progresso, text="", font=("Consolas", 8), bg="#ecf0f1", width=30, anchor="w")
        self.lbl_prog_detalhe.pack(side="left", padx=5)

        # ---- Abas ----
        self.COR_LETRA_PADRAO = "#FAFAFA"
        self.COR_LETRA_ATIVA = "#000000"

        self.config_abas = [
            {"texto": "🌐 HTTP + HTTPS Descriptografado", "bg": "#27ae60"},
            {"texto": "HTTP Texto Claro", "bg": "#da8b15"},
            {"texto": "Sites HTTPS (SNI)", "bg": "#0aa0bb"},
            {"texto": "Chaves TLS", "bg": "#8e44ad"},
            {"texto": "📄 Relatório / Todos Resultados", "bg": "#089679"},
            {"texto": "🗂️ Todos os Protocolos (Geral)", "bg": "#34495e"}
        ]

        style_nb = ttk.Style()
        style_nb.layout("SemAbasNativas.TNotebook", [])
        style_nb.layout("SemAbasNativas.TNotebook.Tab", [])

        self.frame_botoes_abas = tk.Frame(self, bg="#2c3e50")
        self.frame_botoes_abas.pack(fill="x", padx=8, pady=(4, 0))

        self.nb = ttk.Notebook(self, style="SemAbasNativas.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.lista_botoes_abas = []
        for idx, conf in enumerate(self.config_abas):
            btn = tk.Button(
                self.frame_botoes_abas, text=conf["texto"], bg=conf["bg"], fg=self.COR_LETRA_PADRAO,
                activebackground=conf["bg"], activeforeground="#ffffff",
                font=("Arial", 10, "bold"), relief="flat", bd=2, padx=10, pady=6,
                cursor="hand2", command=lambda i=idx: self.selecionar_aba_custom(i)
            )
            btn.pack(side="left", padx=2, pady=2)
            self.lista_botoes_abas.append(btn)

        def _criar_caixa_texto(parent, height=None):
            if height:
                txt = tk.Text(parent, wrap="word", font=("Consolas", 10), height=height, relief="sunken", bd=1)
            else:
                txt = tk.Text(parent, wrap="word", font=("Consolas", 10), relief="sunken", bd=1)
            self._config_text_tags(txt)
            self.text_widgets.append(txt)
            return txt

        # ================= ABA 1: DEEP =================
        aba_deep = ttk.Frame(self.nb)
        self.nb.add(aba_deep, text="🌐 HTTP + HTTPS Descriptografado")

        bar = ttk.Frame(aba_deep, padding=4)
        bar.pack(fill="x")
        ttk.Label(bar, text="Filtrar Tabela:").pack(side="left")
        self.combo_filtro = ttk.Combobox(bar, values=self.OPCOES_FILTRO_GERAL, width=10, state="readonly")
        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(side="left", padx=4)
        self.combo_filtro.bind("<<ComboboxSelected>>", self.aplicar_filtro_tabela)
        self.lbl_deep = ttk.Label(bar, text="", foreground="darkgreen")
        self.lbl_deep.pack(side="left", padx=8)

        pw_deep = tk.PanedWindow(aba_deep, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED, bd=2)
        pw_deep.pack(fill="both", expand=True, padx=4, pady=2)

        frame_tabela = ttk.Frame(pw_deep)
        cols = ("num", "metodo", "host", "uri", "src", "dst", "info")
        self.tree_deep = ttk.Treeview(frame_tabela, columns=cols, show="headings")
        for cid, txt, w in (("num", "#", 50), ("metodo", "Método", 70), ("host", "Host / SNI", 200),
                            ("uri", "URI / Path", 260), ("src", "Origem", 120), ("dst", "Destino", 120), ("info", "Detalhe", 380)):
            self.tree_deep.heading(cid, text=txt)
            self.tree_deep.column(cid, width=w, anchor="w")
        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree_deep.yview)
        self.tree_deep.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.tree_deep.pack(fill="both", expand=True)
        self.tree_deep.bind("<<TreeviewSelect>>", self.mostrar_detalhe_deep)
        self.tree_deep.bind("<Button-3>", lambda e: self._mostrar_menu_contexto(e, self.tree_deep))
        pw_deep.add(frame_tabela, minsize=150, stretch="always")

        frame_detalhes = ttk.Frame(pw_deep)
        self.txt_detalhe_deep = _criar_caixa_texto(frame_detalhes)
        scroll_txt = ttk.Scrollbar(frame_detalhes, orient="vertical", command=self.txt_detalhe_deep.yview)
        self.txt_detalhe_deep.configure(yscrollcommand=scroll_txt.set)
        scroll_txt.pack(side="right", fill="y")
        self.txt_detalhe_deep.pack(fill="both", expand=True)
        pw_deep.add(frame_detalhes, minsize=80, stretch="always")

        # ================= ABA 2: HTTP CLARO =================
        aba_http = ttk.Frame(self.nb)
        self.nb.add(aba_http, text="HTTP Texto Claro")

        bar_http = ttk.Frame(aba_http, padding=4)
        bar_http.pack(fill="x")
        ttk.Label(bar_http, text="Filtrar Tabela:").pack(side="left")
        self.combo_filtro_http = ttk.Combobox(bar_http, values=self.OPCOES_FILTRO_GERAL, width=10, state="readonly")
        self.combo_filtro_http.set("Todos")
        self.combo_filtro_http.pack(side="left", padx=4)
        self.combo_filtro_http.bind("<<ComboboxSelected>>", self.aplicar_filtro_http)

        pw_http = tk.PanedWindow(aba_http, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED, bd=2)
        pw_http.pack(fill="both", expand=True, padx=4, pady=4)

        frame_thttp = ttk.Frame(pw_http)
        cols2 = ("metodo", "host", "uri", "src", "dst")
        self.tree_http = ttk.Treeview(frame_thttp, columns=cols2, show="headings")
        for cid, txt, w in (("metodo", "Método", 80), ("host", "Host", 220), ("uri", "URI", 300), ("src", "Origem", 140), ("dst", "Destino", 140)):
            self.tree_http.heading(cid, text=txt)
            self.tree_http.column(cid, width=w)
        scroll_y_http = ttk.Scrollbar(frame_thttp, orient="vertical", command=self.tree_http.yview)
        self.tree_http.configure(yscrollcommand=scroll_y_http.set)
        scroll_y_http.pack(side="right", fill="y")
        self.tree_http.pack(fill="both", expand=True)
        self.tree_http.bind("<<TreeviewSelect>>", self.mostrar_detalhe_http)
        pw_http.add(frame_thttp, minsize=150, stretch="always")

        frame_detalhe_http = ttk.Frame(pw_http)
        self.txt_detalhe = _criar_caixa_texto(frame_detalhe_http)
        scroll_txt_http = ttk.Scrollbar(frame_detalhe_http, orient="vertical", command=self.txt_detalhe.yview)
        self.txt_detalhe.configure(yscrollcommand=scroll_txt_http.set)
        scroll_txt_http.pack(side="right", fill="y")
        self.txt_detalhe.pack(fill="both", expand=True)
        pw_http.add(frame_detalhe_http, minsize=80, stretch="always")

        # ================= ABA 3: SNI =================
        aba_tls = ttk.Frame(self.nb)
        self.nb.add(aba_tls, text="Sites HTTPS (SNI)")

        pw_tls = tk.PanedWindow(aba_tls, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED, bd=2)
        pw_tls.pack(fill="both", expand=True, padx=4, pady=4)

        frame_ttls = ttk.Frame(pw_tls)
        cols_tls = ("src", "dst", "snis", "client_random")
        self.tree_tls = ttk.Treeview(frame_ttls, columns=cols_tls, show="headings")
        for cid, txt, w in (("src", "Origem", 160), ("dst", "Destino", 160), ("snis", "Domínio (SNI)", 280), ("client_random", "Client Random", 400)):
            self.tree_tls.heading(cid, text=txt)
            self.tree_tls.column(cid, width=w)
        scroll_tls = ttk.Scrollbar(frame_ttls, orient="vertical", command=self.tree_tls.yview)
        self.tree_tls.configure(yscrollcommand=scroll_tls.set)
        scroll_tls.pack(side="right", fill="y")
        self.tree_tls.pack(fill="both", expand=True)
        self.tree_tls.bind("<<TreeviewSelect>>", self.mostrar_detalhe_sni)
        pw_tls.add(frame_ttls, minsize=150, stretch="always")

        frame_detalhe_tls = ttk.Frame(pw_tls)
        self.txt_detalhe_sni = _criar_caixa_texto(frame_detalhe_tls)
        scroll_txt_sni = ttk.Scrollbar(frame_detalhe_tls, orient="vertical", command=self.txt_detalhe_sni.yview)
        self.txt_detalhe_sni.configure(yscrollcommand=scroll_txt_sni.set)
        scroll_txt_sni.pack(side="right", fill="y")
        self.txt_detalhe_sni.pack(fill="both", expand=True)
        pw_tls.add(frame_detalhe_tls, minsize=80, stretch="always")

        # ================= ABA 4: CHAVES TLS =================
        aba_keys = ttk.Frame(self.nb)
        self.nb.add(aba_keys, text="Chaves TLS")

        pw_keys = tk.PanedWindow(aba_keys, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED, bd=2)
        pw_keys.pack(fill="both", expand=True, padx=4, pady=4)

        frame_keys = ttk.Frame(pw_keys)
        cols_k = ("client_random", "label", "site", "secret")
        self.tree_keys = ttk.Treeview(frame_keys, columns=cols_k, show="headings")
        for cid, txt, w in (("client_random", "Client Random", 320), ("label", "Tipo", 240), ("site", "Site (SNI)", 220), ("secret", "Secret (início)", 220)):
            self.tree_keys.heading(cid, text=txt)
            self.tree_keys.column(cid, width=w)
        scroll_keys = ttk.Scrollbar(frame_keys, orient="vertical", command=self.tree_keys.yview)
        self.tree_keys.configure(yscrollcommand=scroll_keys.set)
        scroll_keys.pack(side="right", fill="y")
        self.tree_keys.pack(fill="both", expand=True)
        self.tree_keys.bind("<<TreeviewSelect>>", self.mostrar_detalhe_chave)
        pw_keys.add(frame_keys, minsize=150, stretch="always")

        frame_detalhe_keys = ttk.Frame(pw_keys)
        self.txt_detalhe_keys = _criar_caixa_texto(frame_detalhe_keys)
        scroll_txt_keys = ttk.Scrollbar(frame_detalhe_keys, orient="vertical", command=self.txt_detalhe_keys.yview)
        self.txt_detalhe_keys.configure(yscrollcommand=scroll_txt_keys.set)
        scroll_txt_keys.pack(side="right", fill="y")
        self.txt_detalhe_keys.pack(fill="both", expand=True)
        pw_keys.add(frame_detalhe_keys, minsize=80, stretch="always")

        # ================= ABA 5: RELATÓRIO =================
        aba_res = ttk.Frame(self.nb)
        self.nb.add(aba_res, text="📄 Relatório / Todos os Resultados")

        bar_res = ttk.Frame(aba_res, padding=4)
        bar_res.pack(fill="x")
        ttk.Label(bar_res, text="Filtrar Relatório:").pack(side="left")
        self.combo_filtro_res = ttk.Combobox(bar_res, values=self.OPCOES_FILTRO_GERAL, width=10, state="readonly")
        self.combo_filtro_res.set("Todos")
        self.combo_filtro_res.pack(side="left", padx=4)
        self.combo_filtro_res.bind("<<ComboboxSelected>>", lambda e: self.gerar_relatorio())

        btn_html = tk.Button(bar_res, text="💾 Salvar HTML Completo", bg="#0056b3", fg="white", font=("Arial", 9, "bold"), command=self.salvar_html)
        btn_html.pack(side="right", padx=10)

        self.txt_resultados = _criar_caixa_texto(aba_res)
        scroll_res = ttk.Scrollbar(aba_res, orient="vertical", command=self.txt_resultados.yview)
        self.txt_resultados.configure(yscrollcommand=scroll_res.set)
        scroll_res.pack(side="right", fill="y")
        self.txt_resultados.pack(fill="both", expand=True, padx=4, pady=4)

        # ================= ABA 6: TODOS OS PROTOCOLOS =================
        aba_todos = ttk.Frame(self.nb)
        self.nb.add(aba_todos, text="🗂️ Todos os Protocolos (Geral)")

        bar_todos = ttk.Frame(aba_todos, padding=4)
        bar_todos.pack(fill="x")

        btn_load_todos = tk.Button(bar_todos, text="▶ Listar Pacotes Brutos (Rápido)", bg="#34495e", fg="white", font=("Arial", 9, "bold"), command=self.carregar_todos_protocolos)
        btn_load_todos.pack(side="left", padx=5)

        ttk.Label(bar_todos, text="Filtrar Tabela:").pack(side="left", padx=(15, 0))
        self.combo_filtro_todos = ttk.Combobox(bar_todos, values=self.OPCOES_FILTRO_GERAL, width=10, state="readonly")
        self.combo_filtro_todos.set("Todos")
        self.combo_filtro_todos.pack(side="left", padx=4)
        self.combo_filtro_todos.bind("<<ComboboxSelected>>", self.aplicar_filtro_todos)

        self.lbl_status_todos = ttk.Label(bar_todos, text="", foreground="#34495e")
        self.lbl_status_todos.pack(side="left", padx=15)

        pw_todos = tk.PanedWindow(aba_todos, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED, bd=2)
        pw_todos.pack(fill="both", expand=True, padx=4, pady=2)

        frame_ttodos = ttk.Frame(pw_todos)
        cols_todos = ("no", "time", "src", "dst", "protocol", "length", "info")
        self.tree_todos = ttk.Treeview(frame_ttodos, columns=cols_todos, show="headings")

        for cid, txt, w in (("no", "No.", 60), ("time", "Time", 100), ("src", "Source", 150),
                            ("dst", "Destination", 150), ("protocol", "Protocol", 80),
                            ("length", "Length", 80), ("info", "Info", 600)):
            self.tree_todos.heading(cid, text=txt, command=lambda c=cid: self._sort_tree_todos(c, False))
            self.tree_todos.column(cid, width=w, anchor="w" if cid == "info" else "center")

        scroll_y_todos = ttk.Scrollbar(frame_ttodos, orient="vertical", command=self.tree_todos.yview)
        scroll_x_todos = ttk.Scrollbar(frame_ttodos, orient="horizontal", command=self.tree_todos.xview)
        self.tree_todos.configure(yscrollcommand=scroll_y_todos.set, xscrollcommand=scroll_x_todos.set)
        scroll_x_todos.pack(side="bottom", fill="x")
        scroll_y_todos.pack(side="right", fill="y")
        self.tree_todos.pack(fill="both", expand=True)
        self.tree_todos.bind("<<TreeviewSelect>>", self.mostrar_detalhe_todos)
        self.tree_todos.bind("<Button-3>", lambda e: self._mostrar_menu_contexto(e, self.tree_todos))

        def _on_mousewheel_todos(event):
            self.tree_todos.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        self.tree_todos.bind("<MouseWheel>", _on_mousewheel_todos)

        pw_todos.add(frame_ttodos, minsize=150, stretch="always")

        frame_detalhe_todos = ttk.Frame(pw_todos)
        self.txt_detalhe_todos = _criar_caixa_texto(frame_detalhe_todos, height=8)
        scroll_txt_todos = ttk.Scrollbar(frame_detalhe_todos, orient="vertical", command=self.txt_detalhe_todos.yview)
        self.txt_detalhe_todos.configure(yscrollcommand=scroll_txt_todos.set)
        scroll_txt_todos.pack(side="right", fill="y")
        self.txt_detalhe_todos.pack(fill="both", expand=True)

        def _on_mousewheel_detalhe(event):
            self.txt_detalhe_todos.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        self.txt_detalhe_todos.bind("<MouseWheel>", _on_mousewheel_detalhe)

        pw_todos.add(frame_detalhe_todos, minsize=80, stretch="always")

        self.status_bar = ttk.Label(self, text="Pronto.", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

        self.paned_windows = [pw_deep, pw_http, pw_tls, pw_keys, pw_todos]
        
        # APLICA O TEMA ESCURO LOGO NA INICIALIZAÇÃO
        self._apply_theme()
        self.selecionar_aba_custom(0)


    # ================= TEMA (CLARO/ESCURO) =================

    def _config_text_tags(self, txt):
        fg_general = "#00ff00" if self.is_dark_mode else "#000000"
        fg_title = "#00aaff" if self.is_dark_mode else "#0000ff"
        txt.tag_config("general", foreground=fg_general)
        txt.tag_config("title", foreground=fg_title, font=("Consolas", 10, "bold"))
        txt.tag_config("body", foreground="red")

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self._apply_theme()

    def _apply_theme(self):
        style = ttk.Style()
        
        # O clam corrige o bug do fundo branco no Windows para elementos TTK
        if "clam" in style.theme_names():
            style.theme_use("clam")

        if self.is_dark_mode:
            self.btn_theme.config(text="☀️ Modo Claro", bg="#f1c40f", fg="black")
            bg_main = "#1a1a1a"
            fg_main = "#00ff00"
            bg_text = "#0a0a0a"
            bg_paned = "#333333"
            bg_head = "#2c3e50"
            
            self.configure(bg=bg_main)
            style.configure("TFrame", background=bg_main)
            style.configure("TLabel", background=bg_main, foreground=fg_main)
            
            style.configure("Treeview", background=bg_text, foreground=fg_main, fieldbackground=bg_text, borderwidth=0)
            style.map("Treeview", background=[('selected', '#005500')], foreground=[('selected', 'white')])
            style.configure("Treeview.Heading", background=bg_head, foreground="white", font=("Arial", 9, "bold"))
            
            self.tree_todos.tag_configure("tcp", background="#1a1a2e", foreground="#00ff00")
            self.tree_todos.tag_configure("udp", background="#16213e", foreground="#00aaff")
            self.tree_todos.tag_configure("tls", background="#2a1b38", foreground="#ff00ff")
            self.tree_todos.tag_configure("http", background="#1e3d2f", foreground="#00ff00")
            self.tree_todos.tag_configure("dns", background="#0f3443", foreground="#00ffff")
            self.tree_todos.tag_configure("icmp", background="#3e1f3b", foreground="#ff0055")
            self.tree_todos.tag_configure("padrao", background=bg_text, foreground=fg_main)

            bg_prog = "#222222"
            self.frame_progresso.config(bg=bg_prog)
            self.lbl_prog_msg.config(bg=bg_prog, fg=fg_main)
            self.lbl_prog_pct.config(bg=bg_prog, fg=fg_main)
            self.lbl_prog_detalhe.config(bg=bg_prog, fg="#888888")
            
        else:
            self.btn_theme.config(text="🌙 Modo Escuro", bg="#34495e", fg="white")
            bg_main = "#f0f0f0"
            fg_main = "#000000"
            bg_text = "#ffffff"
            bg_paned = "#bdc3c7"
            bg_head = "#e1e1e1"
            
            self.configure(bg=bg_main)
            style.configure("TFrame", background=bg_main)
            style.configure("TLabel", background=bg_main, foreground=fg_main)
            
            style.configure("Treeview", background=bg_text, foreground=fg_main, fieldbackground=bg_text)
            style.map("Treeview", background=[('selected', '#0078D7')], foreground=[('selected', 'white')])
            style.configure("Treeview.Heading", background=bg_head, foreground="black", font=("Arial", 9, "bold"))
            
            self.tree_todos.tag_configure("tcp", background="#e7e6eb", foreground="black")
            self.tree_todos.tag_configure("udp", background="#daeeff", foreground="black")
            self.tree_todos.tag_configure("tls", background="#d5c8e3", foreground="black")
            self.tree_todos.tag_configure("http", background="#e4ffc7", foreground="black")
            self.tree_todos.tag_configure("dns", background="#ccffff", foreground="black")
            self.tree_todos.tag_configure("icmp", background="#fce0ff", foreground="black")
            self.tree_todos.tag_configure("padrao", background=bg_text, foreground="black")

            bg_prog = "#ecf0f1"
            self.frame_progresso.config(bg=bg_prog)
            self.lbl_prog_msg.config(bg=bg_prog, fg="#34495e")
            self.lbl_prog_pct.config(bg=bg_prog, fg="#27ae60")
            self.lbl_prog_detalhe.config(bg=bg_prog, fg="#7f8c8d")

        # Atualiza os frames base que não são TTK
        self.frame_botoes.config(bg=bg_main)
        self.frame_botoes_abas.config(bg=bg_main)

        # Atualiza o interior das caixas de texto e recolore as tags
        for txt in self.text_widgets:
            txt.config(bg=bg_text, fg=fg_main, insertbackground=fg_main)
            self._config_text_tags(txt)
            
        for pw in self.paned_windows:
            pw.config(bg=bg_paned)
            
        self.lbl_status.config(foreground=fg_main, background=bg_main)
        self.lbl_regex.config(foreground=fg_main, background=bg_main)
        self.lbl_df.config(foreground=fg_main, background=bg_main)


    # ================= MENU CONTEXTO =================

    def _mostrar_menu_contexto(self, event, treeview):
        iid = treeview.identify_row(event.y)
        if iid:
            treeview.selection_set(iid)
            treeview.focus(iid)
            self.ultimo_clique_treeview = treeview
            self.menu_contexto.post(event.x_root, event.y_root)

    def _acionar_seguir_fluxo(self):
        if not self.ultimo_clique_treeview:
            return
        sel = self.ultimo_clique_treeview.selection()
        if not sel:
            return
        item = self.ultimo_clique_treeview.item(sel[0])["values"]
        if not item:
            return
        ip_src = ""
        ip_dst = ""
        if len(item) == 7 and self.ultimo_clique_treeview == self.tree_todos:
            ip_src = str(item[2])
            ip_dst = str(item[3])
        elif len(item) >= 6 and self.ultimo_clique_treeview == self.tree_deep:
            ip_src = str(item[4])
            ip_dst = str(item[5])
        if ip_src and ip_dst and ip_src != " — " and ip_dst != " — ":
            self._abrir_janela_seguir_fluxo(ip_src, ip_dst)
        else:
            messagebox.showwarning("Inválido", "O pacote selecionado não possui IPs válidos.")

    def _abrir_janela_seguir_fluxo(self, ip_a, ip_b):
        if not self.dados_deep:
            messagebox.showinfo("Sem dados", "Você precisa clicar em '▶ DESCRIPTOGRAFAR AGORA' antes.")
            return
        top = tk.Toplevel(self)
        top.title(f"Wireshark - Seguir Fluxo TLS ({ip_a} ↔ {ip_b})")
        top.geometry("1000x700")
        bg_main = "#1e1e1e" if self.is_dark_mode else "#f0f0f0"
        bg_txt = "#0c0c0c" if self.is_dark_mode else "white"
        fg_txt = "#00ff00" if self.is_dark_mode else "black"
        top.configure(bg=bg_main)

        frame_txt = tk.Frame(top, bg=bg_main)
        frame_txt.pack(fill="both", expand=True, padx=5, pady=5)
        txt_fluxo = tk.Text(frame_txt, wrap="word", font=("Consolas", 10), bg=bg_txt, fg=fg_txt, relief="sunken", bd=1)
        scroll = ttk.Scrollbar(frame_txt, orient="vertical", command=txt_fluxo.yview)
        txt_fluxo.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt_fluxo.pack(side="left", fill="both", expand=True)

        txt_fluxo.tag_configure("client", foreground="#ff5555" if self.is_dark_mode else "#c0392b")
        txt_fluxo.tag_configure("server", foreground="#00aaff" if self.is_dark_mode else "#2980b9")
        txt_fluxo.tag_configure("search", background="yellow", foreground="black")

        frame_rodape = tk.Frame(top, bg=bg_main)
        frame_rodape.pack(fill="x", side="bottom", padx=5, pady=(0, 5))
        frame_busca = tk.Frame(frame_rodape, bg=bg_main)
        frame_busca.pack(fill="x", pady=2)
        lbl_proc = tk.Label(frame_busca, text="Procurar:", bg=bg_main)
        if self.is_dark_mode:
            lbl_proc.config(fg="white")
        lbl_proc.pack(side="left")
        ent_busca = ttk.Entry(frame_busca, width=50)
        ent_busca.pack(side="left", padx=5)

        def _localizar_proximo():
            txt_fluxo.tag_remove("search", "1.0", tk.END)
            termo = ent_busca.get()
            if not termo:
                return
            pos_inicial = txt_fluxo.index(tk.INSERT)
            if pos_inicial == txt_fluxo.index(tk.END) or pos_inicial == "1.0":
                pos_inicial = "1.0"
            else:
                pos_inicial = f"{pos_inicial}+1c"
            pos_find = txt_fluxo.search(termo, pos_inicial, stopindex=tk.END, nocase=True)
            if not pos_find:
                pos_find = txt_fluxo.search(termo, "1.0", stopindex=tk.END, nocase=True)
            if pos_find:
                fim = f"{pos_find}+{len(termo)}c"
                txt_fluxo.tag_add("search", pos_find, fim)
                txt_fluxo.mark_set(tk.INSERT, pos_find)
                txt_fluxo.see(pos_find)

        ttk.Button(frame_busca, text="Localizar Próximo", command=_localizar_proximo).pack(side="left", padx=5)
        frame_botoes = tk.Frame(frame_rodape, bg=bg_main)
        frame_botoes.pack(fill="x", pady=2)

        def _salvar_como():
            path = filedialog.asksaveasfilename(title="Salvar Fluxo", defaultextension=".txt",
                                                initialfile=f"fluxo_{ip_a}_para_{ip_b}.txt",
                                                filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(txt_fluxo.get("1.0", tk.END))
                    messagebox.showinfo("Sucesso", "Fluxo salvo com sucesso.")
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao salvar:\n{e}")

        ttk.Button(frame_botoes, text="Fechar", command=top.destroy).pack(side="right", padx=5)
        ttk.Button(frame_botoes, text="Salvar como...", command=_salvar_como).pack(side="right", padx=5)

        cliente_ip = None
        conteudo_encontrado = 0
        for p in self.dados_deep:
            src = p.get("src", "")
            dst = p.get("dst", "")
            if (src == ip_a and dst == ip_b) or (src == ip_b and dst == ip_a):
                metodo = p.get("metodo", "")
                headers = p.get("headers_raw", "")
                corpo = p.get("corpo", "")
                if not metodo and not headers and not corpo:
                    continue
                if cliente_ip is None:
                    cliente_ip = src
                bloco = ""
                if metodo:
                    uri = p.get("uri", "")
                    if "HTTP" not in metodo.upper() and ("GET" in metodo or "POST" in metodo):
                        bloco += f"{metodo} {uri} HTTP/1.1\n"
                    else:
                        bloco += f"{metodo} {uri}\n"
                if headers:
                    bloco += f"{headers}\n"
                if corpo:
                    bloco += f"\n{corpo}\n"
                bloco += "\n"
                if src == cliente_ip:
                    txt_fluxo.insert(tk.END, bloco, "client")
                else:
                    txt_fluxo.insert(tk.END, bloco, "server")
                conteudo_encontrado += 1
        if conteudo_encontrado == 0:
            txt_fluxo.insert(tk.END, "Nenhum dado HTTP/TLS decifrado foi encontrado.\n", "server")
        txt_fluxo.config(state="disabled")

    def selecionar_aba_custom(self, index):
        self.nb.select(index)
        for i, btn in enumerate(self.lista_botoes_abas):
            if i == index:
                btn.config(fg=self.COR_LETRA_ATIVA, relief="solid", bd=2, font=("Arial", 10, "bold", "underline"))
            else:
                btn.config(fg=self.COR_LETRA_PADRAO, relief="flat", bd=2, font=("Arial", 10, "bold"))

    # ================= PROGRESSO =================

    def progresso_iniciar(self, mensagem, modo="determinate"):
        try:
            try:
                self.barra_progresso.stop()
            except Exception:
                pass
            self.barra_progresso['mode'] = modo
            if modo == "determinate":
                self.barra_progresso['value'] = 0
                self.lbl_prog_pct.config(text="0%", fg="#3498db")
            else:
                self.barra_progresso['value'] = 0
                self.barra_progresso.start(15)
                self.lbl_prog_pct.config(text="...", fg="#3498db")
            self.lbl_prog_msg.config(text=mensagem, fg="#2980b9")
            self.lbl_prog_detalhe.config(text="")
            self.update_idletasks()
        except Exception:
            pass

    def progresso_atualizar(self, pct, mensagem=None, detalhe=None):
        try:
            modo_atual = str(self.barra_progresso.cget("mode"))
            if modo_atual == "determinate":
                val = min(max(float(pct), 0), 100)
                self.barra_progresso['value'] = val
                self.lbl_prog_pct.config(text=f"{int(val)}%")
            if mensagem:
                self.lbl_prog_msg.config(text=mensagem)
            if detalhe is not None:
                self.lbl_prog_detalhe.config(text=detalhe)
            self.update_idletasks()
        except Exception:
            pass

    def progresso_finalizar(self, mensagem="Concluído!"):
        try:
            try:
                self.barra_progresso.stop()
            except Exception:
                pass
            self.barra_progresso['mode'] = "determinate"
            self.barra_progresso['value'] = 100
            self.lbl_prog_pct.config(text="100%", fg="#27ae60")
            self.lbl_prog_msg.config(text=mensagem, fg="#27ae60")
            self.lbl_prog_detalhe.config(text="")
            self.update_idletasks()
        except Exception:
            pass

    def progresso_erro(self, mensagem="Erro na operação"):
        try:
            try:
                self.barra_progresso.stop()
            except Exception:
                pass
            self.lbl_prog_msg.config(text=mensagem, fg="#c0392b")
            self.lbl_prog_pct.config(text="ERRO", fg="#c0392b")
            self.lbl_prog_detalhe.config(text="")
            self.update_idletasks()
        except Exception:
            pass

    @staticmethod
    def _formatar_tamanho(tamanho):
        if tamanho < 1024:
            return f"{tamanho} B"
        elif tamanho < 1024 * 1024:
            return f"{tamanho / 1024:.1f} KB"
        return f"{tamanho / (1024 * 1024):.1f} MB"

    # ================= ABRIR ARQUIVOS =================

    def abrir_keylog(self):
        path = filedialog.askopenfilename(title="sslkeylog.log", filetypes=[("Log", "*.log;*.txt"), ("Todos", "*.*")])
        if not path:
            return
        self.progresso_iniciar(f"Lendo {os.path.basename(path)}...")
        def _carregar():
            try:
                def cb(pct, msg):
                    self.after(0, lambda: self.progresso_atualizar(pct, detalhe=msg))
                chaves = parse_keylog(path, callback=cb)
                self.after(0, lambda: self._concluir_abrir_keylog(path, chaves))
            except Exception as e:
                self.after(0, lambda: self._erro_abrir(e))
        threading.Thread(target=_carregar, daemon=True).start()

    def _concluir_abrir_keylog(self, path, chaves):
        self.keylog = chaves
        self.keylog_path = path
        self.atualizar_keys()
        self.progresso_finalizar(f"✅ {len(self.keylog)} chaves carregadas!")
        # Atualiza label e garante que a cor no modo dark permaneça certa
        self.lbl_status.config(text=f"Chaves TLS: {len(self.keylog)} | Agora carregue o .pcap")
        if self.pcap_path:
            self.after(900, self.rodar_analise_profunda)

    def _erro_abrir(self, erro):
        self.progresso_erro("Falha ao abrir chave")
        messagebox.showerror("Erro", str(erro))

    def abrir_pcap(self):
        path = filedialog.askopenfilename(title="Captura de Rede", filetypes=[("PCAP", "*.pcapng;*.pcap;*.cap"), ("Todos", "*.*")])
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
            path = filedialog.askopenfilename(title="Selecione resultados.pcapng", filetypes=[("PCAP", "*.pcapng;*.pcap;*.cap")])
            if not path:
                return
        self.carregar_pcap(path, nome_exibido=nome)

    def carregar_pcap(self, path, nome_exibido=None):
        self.pcap_nome = nome_exibido or os.path.basename(path)
        self.pcap_path = path
        self.progresso_iniciar(f"Lendo captura: {self.pcap_nome}...")
        def _carregar():
            try:
                self.after(0, lambda: self.progresso_atualizar(5, "Extraindo handshakes TLS...", "Fase 1/3"))
                def cb_tls(pct):
                    self.after(0, lambda v=int(pct * 0.4): self.progresso_atualizar(v, detalhe=f"Lendo TLS... {v}%"))
                hs = extrair_handshakes_tls(path, callback=cb_tls)
                self.after(0, lambda: self.progresso_atualizar(40, "Extraindo HTTP...", "Fase 2/3"))
                def cb_http(pct):
                    self.after(0, lambda v=40 + int(pct * 0.4): self.progresso_atualizar(v, detalhe=f"Analisando streams... {v}%"))
                http_reqs = extrair_http_requests(path, callback=cb_http)
                self.after(0, lambda: self.progresso_atualizar(85, "Processando SNIs...", "Fase 3/3"))
                sni_map = snis_por_client_random(hs)
                self.after(0, lambda: self._concluir_pcap(hs, sni_map, http_reqs))
            except Exception as e:
                self.after(0, lambda: self._erro_pcap(e))
        threading.Thread(target=_carregar, daemon=True).start()

    def _concluir_pcap(self, hs, sni_map, http_reqs):
        self.handshakes = hs
        self.snis = sni_map
        self.http_requests = http_reqs
        self.atualizar_keys()
        self.atualizar_tls()
        self.aplicar_filtro_http()
        self.gerar_relatorio()
        resumo = f"✅ {self.pcap_nome} ({len(hs)} hs, {len(http_reqs)} http)"
        self.progresso_finalizar(resumo)
        self.lbl_status.config(text=resumo)
        self.todos_protocolos_dados = []
        self.tree_todos.delete(*self.tree_todos.get_children())
        self.lbl_status_todos.config(text="Pacotes não carregados. Clique no botão.")
        if self.keylog_path:
            self.after(1000, self.rodar_analise_profunda)
        else:
            messagebox.showinfo("Falta a Chave TLS", "Captura carregada!\n\nAgora clique em '1. Abrir sslkeylog.log (Manual)'.")

    def _erro_pcap(self, erro):
        self.progresso_erro("Falha ao ler PCAP")
        messagebox.showerror("Erro ao ler pcap", str(erro))

    # ================= TODOS OS PROTOCOLOS =================

    def carregar_todos_protocolos(self):
        if not self.pcap_path:
            messagebox.showwarning("Aviso", "Por favor, carregue um arquivo .pcap primeiro.")
            return
        self.tshark_path = encontrar_tshark(self.tshark_path)
        if not self.tshark_path:
            messagebox.showerror("Erro", "tshark não encontrado no sistema.")
            return
        self.progresso_iniciar("Lendo tabela completa de pacotes (tshark)...", modo="indeterminate")
        self.lbl_status_todos.config(text="Extraindo pacotes, aguarde...")
        self.tree_todos.delete(*self.tree_todos.get_children())
        self.todos_protocolos_dados = []

        def _thread_ler_tshark():
            cmd = [
                self.tshark_path, "-r", self.pcap_path,
                "-T", "fields",
                "-e", "frame.number", "-e", "frame.time_relative",
                "-e", "ip.src", "-e", "ipv6.src",
                "-e", "ip.dst", "-e", "ipv6.dst",
                "-e", "_ws.col.Protocol", "-e", "frame.len", "-e", "_ws.col.Info",
                "-E", "separator=\t"
            ]
            if self.keylog_path and os.path.isfile(self.keylog_path):
                cmd.extend(["-o", f"tls.keylog_file:{os.path.abspath(self.keylog_path).replace(chr(92), '/')}"])
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
                buffer_pacotes, count = [], 0
                if proc.stdout:
                    for linha in proc.stdout:
                        partes = linha.rstrip("\r\n").split("\t")
                        while len(partes) < 9:
                            partes.append("")
                        no = partes[0]
                        time_rel = partes[1]
                        src = partes[2] or partes[3] or " — "
                        dst = partes[4] or partes[5] or " — "
                        proto = partes[6] or "Desconhecido"
                        length = partes[7]
                        info = partes[8]
                        pacote = (no, time_rel, src, dst, proto, length, info)
                        buffer_pacotes.append(pacote)
                        self.todos_protocolos_dados.append(pacote)
                        count += 1
                        if len(buffer_pacotes) >= 1000:
                            lote = buffer_pacotes[:]
                            buffer_pacotes.clear()
                            self.after(0, lambda l=lote, c=count: self._inserir_lote_todos(l, c))
                if buffer_pacotes:
                    self.after(0, lambda l=buffer_pacotes, c=count: self._inserir_lote_todos(l, c))
                self.after(0, lambda: self._concluir_todos_protocolos(count))
            except Exception as e:
                self.after(0, lambda: self.progresso_erro(f"Erro no Tshark: {e}"))
        threading.Thread(target=_thread_ler_tshark, daemon=True).start()

    def _inserir_lote_todos(self, lote, count):
        for p in lote:
            proto_lower = str(p[4]).lower()
            tag = "padrao"
            if "tcp" in proto_lower:
                tag = "tcp"
            elif "udp" in proto_lower:
                tag = "udp"
            elif "tls" in proto_lower or "ssl" in proto_lower:
                tag = "tls"
            elif "http" in proto_lower:
                tag = "http"
            elif "dns" in proto_lower:
                tag = "dns"
            elif "icmp" in proto_lower:
                tag = "icmp"
            self.tree_todos.insert("", "end", values=p, tags=(tag,))
        self.lbl_status_todos.config(text=f"Carregando: {count} pacotes lidos...")
        self.progresso_atualizar(0, detalhe=f"{count} pacotes carregados...")

    def _concluir_todos_protocolos(self, count):
        self.progresso_finalizar(f"Tabela Completa carregada ({count} pacotes).")
        self.lbl_status_todos.config(text=f"Total: {count} pacotes exibidos.")

    def aplicar_filtro_todos(self, event=None):
        filtro = self.combo_filtro_todos.get().upper()
        self.lbl_status_todos.config(text="Aplicando filtro, aguarde...")
        self.update_idletasks()
        self.tree_todos.delete(*self.tree_todos.get_children())
        exibidos, lote_insercao = 0, []
        for p in self.todos_protocolos_dados:
            mostrar = False
            proto_str = str(p[4]).upper()
            info_str = str(p[6]).upper()
            if filtro == "TODOS":
                mostrar = True
            elif filtro in ["POST", "GET", "PUT", "DELETE"]:
                if filtro in info_str:
                    mostrar = True
            elif filtro in proto_str:
                mostrar = True
            if mostrar:
                lote_insercao.append(p)
                exibidos += 1
        self._inserir_lote_todos(lote_insercao, exibidos)
        self.lbl_status_todos.config(text=f"Exibindo {exibidos} de {len(self.todos_protocolos_dados)} pacotes.")
        self.progresso_finalizar("Filtro aplicado.")

    def mostrar_detalhe_todos(self, event=None):
        sel = self.tree_todos.selection()
        self.txt_detalhe_todos.delete("1.0", "end")
        if not sel:
            return
        item = self.tree_todos.item(sel[0])["values"]
        if not item:
            return
        self.txt_detalhe_todos.insert("end", f"Frame {item[0]}: {item[5]} bytes no fio\n", "title")
        self.txt_detalhe_todos.insert("end", f"Tempo: {item[1]} segundos\n", "general")
        self.txt_detalhe_todos.insert("end", f"Origem: {item[2]}\n", "general")
        self.txt_detalhe_todos.insert("end", f"Destino: {item[3]}\n", "general")
        self.txt_detalhe_todos.insert("end", f"Protocolo: {item[4]}\n", "general")
        self.txt_detalhe_todos.insert("end", "-" * 50 + "\n", "title")
        self.txt_detalhe_todos.insert("end", "Informação:\n", "title")
        self.txt_detalhe_todos.insert("end", f"{item[6]}\n", "body")

    def _sort_tree_todos(self, col, reverse):
        self.lbl_status_todos.config(text="Ordenando tabela, aguarde...")
        self.update_idletasks()
        colunas = ["no", "time", "src", "dst", "protocol", "length", "info"]
        idx = colunas.index(col)
        itens_visiveis = []
        for k in self.tree_todos.get_children(''):
            itens_visiveis.append((self.tree_todos.item(k)["values"], self.tree_todos.item(k)["tags"]))
        def sort_key(item):
            val = item[0][idx]
            if val is None or val == "":
                return -1 if reverse else float('inf')
            try:
                return float(val)
            except ValueError:
                return str(val).lower()
        itens_visiveis.sort(key=sort_key, reverse=reverse)
        self.tree_todos.delete(*self.tree_todos.get_children())
        for valores, tags in itens_visiveis:
            self.tree_todos.insert("", "end", values=valores, tags=tags)
        self.tree_todos.heading(col, command=lambda: self._sort_tree_todos(col, not reverse))
        self.lbl_status_todos.config(text="Ordenação concluída.")

    # ================= ANÁLISE PROFUNDA =================

    def rodar_analise_profunda(self):
        if not self.pcap_path:
            self.analisar_resultados()
            if not self.pcap_path:
                return
        if not self.keylog_path:
            messagebox.showwarning("Sem Chave", "Por favor, carregue o arquivo sslkeylog.log manualmente primeiro.")
            return
        self.tshark_path = encontrar_tshark(self.tshark_path)
        regex = self.ent_regex.get().strip()
        df = self.ent_df.get().strip()
        self.progresso_iniciar("Descriptografando HTTPS com Tshark...")
        def _analisar():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                pacotes_processados, estimativa_total = [0], [500]
                def prog(n):
                    pacotes_processados[0] = n
                    if n > estimativa_total[0]:
                        estimativa_total[0] = n + 200
                    pct = min(int((n / estimativa_total[0]) * 95), 95)
                    self.after(0, lambda: self.progresso_atualizar(pct, "Decifrando pacotes...", f"Pacote {n} processado"))
                pacotes, total = analise_profunda(
                    self.pcap_path, self.keylog_path, filtro_regex=regex, display_filter=df,
                    limite=800, tshark_path=self.tshark_path, progresso=prog)
                self.after(0, lambda: self._concluir_deep(pacotes, total))
            except Exception as e:
                self.after(0, lambda: self._erro_deep(e))
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
        threading.Thread(target=_analisar, daemon=True).start()

    def _concluir_deep(self, pacotes, total):
        self.total_deep_analisados = total
        self.dados_deep = pacotes
        self.aplicar_filtro_tabela()
        self.gerar_relatorio()
        resumo = f"✅ Decifrado: {len(pacotes)} pacotes HTTP/HTTPS de {total} analisados"
        self.progresso_finalizar(resumo)
        self.lbl_deep.config(text=resumo)
        self.selecionar_aba_custom(0)

    def _erro_deep(self, erro):
        self.progresso_erro("Erro na análise profunda")
        self.lbl_deep.config(text="")
        messagebox.showerror("Erro na análise", str(erro))

    # ================= UI =================

    def atualizar_keys(self):
        self.tree_keys.delete(*self.tree_keys.get_children())
        for e in self.keylog:
            site = ", ".join(self.snis.get(e["client_random"].lower(), [])) or "—"
            secret = (e["secret"][:28] + "…" if len(e["secret"]) > 28 else e["secret"])
            self.tree_keys.insert("", "end", values=(e["client_random"], e["label"], site, secret))

    def mostrar_detalhe_chave(self, event=None):
        sel = self.tree_keys.selection()
        self.txt_detalhe_keys.delete("1.0", "end")
        if not sel:
            return
        item = self.tree_keys.item(sel[0])["values"]
        if not item:
            return
        client_random = str(item[0]).lower()
        site = str(item[2])
        self.txt_detalhe_keys.insert("end", "=== Detalhes da Chave TLS ===\n", "title")
        self.txt_detalhe_keys.insert("end", f"Client Random: {client_random}\n", "general")
        self.txt_detalhe_keys.insert("end", f"Site (SNI): {site}\n\n", "general")
        ips_envolvidos = set()
        for hs in self.handshakes:
            if hs["client_random"].lower() == client_random:
                ips_envolvidos.add(hs["src"])
                ips_envolvidos.add(hs["dst"])
        encontrou_algo = False
        for p in self.dados_deep:
            if (p.get("src") in ips_envolvidos and p.get("dst") in ips_envolvidos) or (site != "—" and site in str(p.get("host", ""))):
                if p.get("headers_raw") or p.get("metodo"):
                    encontrou_algo = True
                    self.txt_detalhe_keys.insert("end", f"--- Pacote #{p.get('num')} ---\n", "title")
                    if p.get("metodo"):
                        self.txt_detalhe_keys.insert("end", f"Método: {p.get('metodo')} {p.get('uri','')}\n", "title")
                    if p.get("headers_raw"):
                        self.txt_detalhe_keys.insert("end", "Cabeçalhos (Headers):\n", "title")
                        self.txt_detalhe_keys.insert("end", f"{p['headers_raw']}\n", "title")
                    self.txt_detalhe_keys.insert("end", "-" * 50 + "\n\n", "general")
        if not encontrou_algo:
            if not self.dados_deep:
                self.txt_detalhe_keys.insert("end", "⚠️ Execute a descriptografia ('▶ DESCRIPTOGRAFAR AGORA') para ver os cabeçalhos HTTP vinculados a esta chave.", "body")
            else:
                self.txt_detalhe_keys.insert("end", "Nenhum cabeçalho HTTP descriptografado encontrado para os IPs desta chave específica.", "general")

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
        self.txt_detalhe.insert("end", "=== Método HTTP ===\n", "title")
        self.txt_detalhe.insert("end", f"{r['metodo']} {r['host']}{r['uri']}\n", "title")
        self.txt_detalhe.insert("end", f"Conexão: {r['src']}:{r['sport']} → {r['dst']}:{r['dport']}\n\n", "general")
        self.txt_detalhe.insert("end", "--- Cabeçalhos (Headers) ---\n", "title")
        for k, v in r["headers"].items():
            self.txt_detalhe.insert("end", f"{k}: {v}\n", "title")
        if r["body"]:
            self.txt_detalhe.insert("end", "\n--- Corpo ---\n", "body")
            self.txt_detalhe.insert("end", f"{limpar_texto(r['body'], 3000)}\n", "body")

    def aplicar_filtro_tabela(self, event=None):
        if not self.dados_deep:
            return
        filtro = self.combo_filtro.get().upper()
        self.tree_deep.delete(*self.tree_deep.get_children())
        exibidos = 0
        for p in self.dados_deep:
            met = str(p.get("metodo") or "").upper()
            info = str(p.get("info") or "").upper()
            proto = str(p.get("protocolos") or "").upper()
            mostrar = False
            if filtro == "TODOS":
                mostrar = True
            elif filtro in ["POST", "GET", "PUT", "DELETE"]:
                if filtro in met or filtro in info:
                    mostrar = True
            elif filtro in met or filtro in info or filtro in proto:
                mostrar = True
            if mostrar:
                self.tree_deep.insert("", "end", values=(
                    p["num"], p.get("metodo") or "",
                    p.get("host") or "", p.get("uri") or "",
                    p["src"], p["dst"], p.get("info") or ""))
                exibidos += 1
        self.lbl_deep.config(text=f"Exibindo {exibidos} de {len(self.dados_deep)} analisados")

    def mostrar_detalhe_deep(self, event=None):
        sel = self.tree_deep.selection()
        self.txt_detalhe_deep.delete("1.0", "end")
        if not sel:
            return
        num_pacote = self.tree_deep.item(sel[0])["values"][0]
        p = next((x for x in self.dados_deep if str(x["num"]) == str(num_pacote)), None)
        if not p:
            return
        self.txt_detalhe_deep.insert("end", f"Pacote #{p['num']}  {p['hora']}\n", "title")
        self.txt_detalhe_deep.insert("end", f"Protocolos: {p['protocolos']}\n", "general")
        self.txt_detalhe_deep.insert("end", f"{p['src']}  →  {p['dst']}\n\n", "general")
        if p.get("metodo") or p.get("host") or p.get("uri"):
            self.txt_detalhe_deep.insert("end", "=== Método HTTP ===\n", "title")
            self.txt_detalhe_deep.insert("end", f"Método : {p.get('metodo')}\n", "title")
            self.txt_detalhe_deep.insert("end", f"Host   : {p.get('host')}\n", "title")
            self.txt_detalhe_deep.insert("end", f"URI    : {p.get('uri')}\n\n", "title")
        if p.get("headers_raw"):
            self.txt_detalhe_deep.insert("end", "--- Cabeçalhos ---\n", "title")
            self.txt_detalhe_deep.insert("end", f"{p['headers_raw']}\n\n", "title")
        if p.get("tls"):
            self.txt_detalhe_deep.insert("end", f"--- TLS ---\n{p['tls']}\n\n", "title")
        if p.get("corpo"):
            self.txt_detalhe_deep.insert("end", "--- Corpo ---\n", "body")
            self.txt_detalhe_deep.insert("end", f"{p['corpo']}\n\n", "body")
        self.txt_detalhe_deep.insert("end", f"Resumo: {p.get('info')}\n", "general")

    def mostrar_detalhe_sni(self, event=None):
        sel = self.tree_tls.selection()
        self.txt_detalhe_sni.delete("1.0", "end")
        if not sel:
            return
        item = self.tree_tls.item(sel[0])["values"]
        if not item:
            return
        origem, destino, sni_nome = str(item[0]), str(item[1]), str(item[2])
        src_ip = origem.split(":")[0] if ":" in origem else origem
        dst_ip = destino.split(":")[0] if ":" in destino else destino
        self.txt_detalhe_sni.insert("end", "=== Detalhes da Conexão HTTPS ===\n", "title")
        self.txt_detalhe_sni.insert("end", f"SNI (Domínio): {sni_nome}\n", "general")
        self.txt_detalhe_sni.insert("end", f"Conexão: {origem} → {destino}\n\n", "general")
        encontrou_algo = False
        for p in self.dados_deep:
            if ((p.get("src") == src_ip and p.get("dst") == dst_ip) or
                (p.get("src") == dst_ip and p.get("dst") == src_ip) or
                (sni_nome != "—" and sni_nome in str(p.get("host", "")))):
                if p.get("headers_raw") or p.get("metodo"):
                    encontrou_algo = True
                    self.txt_detalhe_sni.insert("end", f"--- Pacote #{p.get('num')} ---\n", "title")
                    if p.get("metodo"):
                        self.txt_detalhe_sni.insert("end", f"Método: {p.get('metodo')} {p.get('uri','')}\n", "title")
                    if p.get("headers_raw"):
                        self.txt_detalhe_sni.insert("end", "Cabeçalhos (Headers):\n", "title")
                        self.txt_detalhe_sni.insert("end", f"{p['headers_raw']}\n", "title")
                    self.txt_detalhe_sni.insert("end", "-" * 50 + "\n\n", "general")
        if not encontrou_algo:
            if not self.dados_deep:
                self.txt_detalhe_sni.insert("end", "⚠️ A descriptografia ainda não foi executada.\n", "body")
            else:
                self.txt_detalhe_sni.insert("end", "Nenhum cabeçalho HTTP descriptografado foi encontrado para esta conexão específica.", "general")

    # ================= RELATÓRIO =================

    def gerar_relatorio(self):
        filtro = self.combo_filtro_res.get().upper()
        txt = self.txt_resultados
        txt.delete("1.0", "end")
        linha = "=" * 70 + "\n"
        txt.insert("end", linha, "title")
        txt.insert("end", f"RELATÓRIO — {self.pcap_nome} (Filtro: {filtro})\n", "title")
        txt.insert("end", linha + "\n", "title")

        if self.keylog_path:
            txt.insert("end", ">>> SSLKEY UTILIZADO <<<\n", "title")
            txt.insert("end", f"  {self.keylog_path}\n  Chaves: {len(self.keylog)}\n\n", "general")

        txt.insert("end", ">>> SITES (SNI) <<<\n", "title")
        if self.snis:
            for s in sorted({x for l in self.snis.values() for x in l}):
                txt.insert("end", f"  • {s}\n", "general")
        else:
            txt.insert("end", "  (nenhum)\n", "general")
        txt.insert("end", "\n")

        txt.insert("end", ">>> CHAVES TLS <<<\n", "title")
        if self.keylog:
            for e in self.keylog:
                site = ", ".join(self.snis.get(e["client_random"].lower(), [])) or "—"
                txt.insert("end", f"  {e['client_random']}  [{e['label']}]  {site}\n", "general")
        else:
            txt.insert("end", "  (nenhum)\n", "general")
        txt.insert("end", "\n")

        txt.insert("end", ">>> HTTP (Texto Claro) <<<\n", "title")
        ct = 0
        for i, r in enumerate(self.http_requests, 1):
            metodo = str(r.get("metodo") or "").strip().upper()
            if filtro not in ("TODOS", "TLS") and filtro != metodo:
                continue
            if filtro == "TLS":
                continue
            ct += 1
            txt.insert("end", f"\n--- #{i} ---\n", "title")
            txt.insert("end", f"  {r['metodo']} {r['host']}{r['uri']}\n", "title")
            txt.insert("end", f"  {r['src']}:{r['sport']} -> {r['dst']}:{r['dport']}\n", "general")
            for k, v in r["headers"].items():
                txt.insert("end", f"    {k}: {v}\n", "title")
            if r.get("body"):
                txt.insert("end", "  Corpo:\n", "body")
                txt.insert("end", f"{limpar_texto(r['body'], 300)}\n", "body")
        if ct == 0:
            txt.insert("end", "  (nenhuma)\n", "general")
        txt.insert("end", "\n")

        txt.insert("end", ">>> HTTPS DESCRIPTOGRAFADO <<<\n", "title")
        if not self.dados_deep:
            txt.insert("end", "  (não processado)\n", "general")
        else:
            cd = 0
            for p in self.dados_deep:
                met = str(p.get("metodo") or "").upper()
                info = str(p.get("info") or "").upper()
                mostrar = False
                if filtro == "TODOS":
                    mostrar = True
                elif filtro == "TLS" and "TLS" in info and not met:
                    mostrar = True
                elif filtro in met:
                    mostrar = True
                if not mostrar:
                    continue
                if not p.get("metodo") and not p.get("tls"):
                    continue
                cd += 1
                txt.insert("end", f"\n--- Pkt #{p['num']} ---\n", "title")
                txt.insert("end", f"    {p['src']} -> {p['dst']}\n", "general")
                if p.get("metodo"):
                    txt.insert("end", f"    {p.get('metodo')} {p.get('host', '')}{p.get('uri', '')}\n", "title")
                if p.get("headers_raw"):
                    for h_line in p["headers_raw"].split("\n"):
                        if h_line.strip():
                            txt.insert("end", f"      {h_line.strip()}\n", "title")
                if p.get("corpo"):
                    txt.insert("end", "    Corpo:\n", "body")
                    txt.insert("end", f"{p['corpo'][:150]}\n", "body")
                if p.get("tls"):
                    txt.insert("end", f"    TLS: {p['tls']}\n", "title")
            if cd == 0:
                txt.insert("end", "  (nenhum)\n", "general")
        txt.insert("end", "\n" + linha, "title")
        self.status_bar.config(text="Relatório atualizado.")

    # ================= SALVAR HTML =================

    def salvar_html(self):
        if not self.pcap_path and not self.keylog and not self.http_requests and not self.dados_deep:
            messagebox.showwarning("Salvar HTML", "Não há dados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            title="Salvar HTML", defaultextension=".html",
            initialfile=f"Relatorio_{self.pcap_nome or 'captura'}.html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")])
        if not path:
            return
        try:
            self.gerar_relatorio()
        except Exception:
            pass
        self.progresso_iniciar("Gerando Relatório HTML...")
        def _gerar():
            try:
                self.after(0, lambda: self.progresso_atualizar(15, "Montando estrutura...", "Cabeçalho e CSS"))
                html_code = self._montar_html()
                self.after(0, lambda: self.progresso_atualizar(70, "Escrevendo arquivo...", path[:60]))
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html_code)
                tamanho = os.path.getsize(path)
                def _ok():
                    self.progresso_finalizar("✅ HTML salvo com sucesso!")
                    self.status_bar.config(text=f"HTML salvo: {path} ({self._formatar_tamanho(tamanho)})")
                    self.after(200, lambda: messagebox.showinfo("HTML Salvo", f"Relatório HTML gerado com sucesso!\n\nArquivo:\n{path}"))
                self.after(0, _ok)
            except Exception as e:
                self.after(0, lambda: self.progresso_erro("Erro ao salvar HTML"))
        threading.Thread(target=_gerar, daemon=True).start()

    def _montar_html(self):
        def badge(metodo):
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

        nome_pcap = html.escape(self.pcap_nome or "captura")

        h = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Relatório - {nome_pcap}</title>
<style>
:root{{--p:#2c3e50;--s:#34495e;--a:#3498db;--d:#282c34}}
body{{font-family:'Segoe UI',sans-serif;background:#eef2f5;color:#333;margin:0;scroll-behavior:smooth}}
header{{background:var(--p);color:#fff;padding:20px 40px;display:flex;justify-content:space-between;align-items:center}}
header h1{{margin:0;font-size:24px}}
header p{{margin:5px 0 0;color:#bdc3c7;font-size:14px}}
nav{{background:var(--s);padding:10px 40px;position:sticky;top:0;z-index:1000;display:flex;align-items:center;flex-wrap:wrap;gap:8px}}
nav a{{color:#fff;text-decoration:none;margin-right:16px;font-size:14px;font-weight:bold}}
nav a:hover{{color:var(--a)}}
.c{{max-width:1200px;margin:30px auto;padding:0 20px}}
h2{{color:var(--p);border-bottom:3px solid var(--a);padding-bottom:8px;margin-top:40px}}
.card{{background:#fff;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.08);padding:20px;margin-bottom:25px;border-left:5px solid var(--p)}}
.ch{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #eee;padding-bottom:10px;margin-bottom:15px;flex-wrap:wrap;gap:8px}}
.ct{{margin:0;font-size:18px;color:var(--p);word-break:break-all}}
.ci{{font-size:13px;color:#7f8c8d;background:#f1f2f6;padding:4px 10px;border-radius:20px;font-family:Consolas,monospace}}
.b{{display:inline-block;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:bold;color:#fff;margin-right:10px}}
.bg-green{{background:#27ae60}}.bg-orange{{background:#d35400}}.bg-blue{{background:#2980b9}}
.bg-red{{background:#c0392b}}.bg-teal{{background:#16a085}}.bg-purple{{background:#8e44ad}}.bg-gray{{background:#7f8c8d}}
.db{{margin-top:15px;border-radius:5px;overflow:hidden}}
.dt{{font-size:13px;font-weight:bold;padding:5px 10px;color:#fff;margin:0}}
.dc{{margin:0;padding:15px;font-family:Consolas,monospace;font-size:13px;white-space:pre-wrap;word-wrap:break-word}}
.bh .dt{{background:#f39c12}}.bh .dc{{background:#fffbe6;color:#333;border:1px solid #f39c12;border-top:none}}
.bb .dt{{background:var(--s)}}.bb .dc{{background:var(--d);color:#ff5555;border:1px solid var(--s);border-top:none}}
.bt .dt{{background:#8e44ad}}.bt .dc{{background:#f5eef8;color:#333;border:1px solid #8e44ad;border-top:none}}
table{{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.08);border-radius:8px;overflow:hidden}}
th,td{{border:1px solid #eee;padding:12px;text-align:left;font-size:14px}}
th{{background:var(--p);color:#fff}}
tr:hover{{background:#f1f2f6}}
.sni{{display:inline-block;background:#3498db;color:#fff;padding:6px 12px;border-radius:20px;font-size:13px;margin:5px 5px 5px 0}}
.info{{background:#d5f5e3;border:2px solid #27ae60;border-radius:8px;padding:15px;margin-bottom:20px}}
.indice{{background:#fff;padding:15px;border-radius:8px;margin-bottom:20px;box-shadow:0 2px 5px rgba(0,0,0,.1);max-height:250px;overflow-y:auto;border:2px solid #8e44ad}}
.btn-shortcut{{display:inline-block;padding:8px 12px;background:#e67e22;color:#fff;text-decoration:none;border-radius:4px;margin:3px;font-size:12px;font-weight:bold}}
.btn-shortcut.green{{background:#27ae60}}
.btn-shortcut:hover{{opacity:.85}}
.btn-topo{{position:fixed;bottom:20px;right:20px;background:var(--a);color:#fff;padding:12px 18px;border-radius:50px;text-decoration:none;font-weight:bold;box-shadow:0 4px 10px rgba(0,0,0,.3);z-index:9999;font-size:14px}}
.btn-topo:hover{{background:var(--p)}}
</style>
</head><body id="topo">
<header><div><h1>🌐 Relatório de Tráfego</h1><p>Arquivo: <strong>{nome_pcap}</strong></p></div></header>
<nav>
  <a href="#sk">🔑 SSLKEY</a>
  <a href="#sni">📍 SNI</a>
  <a href="#http">📄 HTTP</a>
  <a href="#https">🔐 HTTPS</a>
  <a href="#keys">🔑 Chaves</a>
</nav>
<div class="c">
"""
        h += '<div class="indice"><h3>🔗 Acesso Rápido aos Corpos (Payloads)</h3>'
        tem_atalho = False
        for i, r in enumerate(self.http_requests):
            if r.get("body"):
                host = r.get("host") or r.get("src") or "?"
                h += f'<a href="#http_{i}" class="btn-shortcut">HTTP: {html.escape(str(host))} (Payload)</a> '
                tem_atalho = True
        for p in self.dados_deep:
            if p.get("corpo"):
                host = p.get("host") or p.get("dst") or "?"
                num = html.escape(str(p.get("num", "")))
                h += f'<a href="#https_{num}" class="btn-shortcut green">HTTPS #{num}: {html.escape(str(host))} (Descriptografado)</a> '
                tem_atalho = True
        if not tem_atalho:
            h += "<p>Nenhum corpo/payload disponível para atalho.</p>"
        h += "</div>"

        if self.keylog_path:
            h += f"""<div class="info" id="sk">
<h3>🔑 SSLKEY</h3>
<p><code>{html.escape(str(self.keylog_path))}</code></p>
<p>Chaves: {len(self.keylog)}</p></div>"""
        else:
            h += '<div class="info" id="sk"><h3>🔑 SSLKEY</h3><p>Nenhum arquivo de chaves carregado.</p></div>'

        h += '<h2 id="sni">📍 Domínios (SNI)</h2>'
        h += '<div class="card" style="border-left-color:#3498db">'
        if self.snis:
            for s in sorted({x for l in self.snis.values() for x in l}):
                h += f'<span class="sni">{html.escape(str(s))}</span>'
        else:
            h += "<p>Nenhum.</p>"
        h += "</div>"

        h += '<h2 id="http">📄 HTTP Claro</h2>'
        if self.http_requests:
            for i, r in enumerate(self.http_requests):
                bc = badge(r.get("metodo", ""))
                host = html.escape(str(r.get("host") or ""))
                uri = html.escape(str(r.get("uri") or ""))
                metodo = html.escape(str(r.get("metodo") or ""))
                src = html.escape(str(r.get("src") or ""))
                dst = html.escape(str(r.get("dst") or ""))
                sport = r.get("sport", "")
                dport = r.get("dport", "")
                h += f"""<div class="card" id="http_{i}" style="border-left-color:#f39c12">
<div class="ch"><h3 class="ct">
<span class="b {bc}">{metodo}</span>{host}{uri}
</h3><span class="ci">{src}:{sport} → {dst}:{dport}</span></div>
<div class="db bh"><p class="dt">Headers</p>
<pre class="dc">{html.escape(chr(10).join(f'{k}: {v}' for k, v in (r.get('headers') or {}).items()))}</pre></div>"""
                if r.get("body"):
                    h += f"""<div class="db bb">
<p class="dt">👇 Corpo (Payload)</p>
<pre class="dc">{html.escape(str(r['body'])[:3000])}</pre></div>"""
                h += "</div>"
        else:
            h += "<p>Nenhum.</p>"

        h += '<h2 id="https">🔐 HTTPS Descriptografado</h2>'
        if self.dados_deep:
            for p in self.dados_deep:
                if not p.get("metodo") and not p.get("tls"):
                    continue
                is_tls = not p.get("metodo")
                bc_color = "#8e44ad" if is_tls else "#27ae60"
                bc = badge(p.get("metodo") or "TLS")
                mt = html.escape(str(p.get("metodo") or "TLS Handshake"))
                ut = html.escape(f"{p.get('host', '')}{p.get('uri', '')}")
                num = html.escape(str(p.get("num", "")))
                src = html.escape(str(p.get("src", "")))
                dst = html.escape(str(p.get("dst", "")))
                h += f"""<div class="card" id="https_{num}" style="border-left-color:{bc_color}">
<div class="ch"><h3 class="ct">
<span class="b {bc}">{mt}</span> {ut}</h3>
<span class="ci">#{num} | {src} → {dst}</span></div>"""
                if p.get("headers_raw"):
                    h += f"""<div class="db bh"><p class="dt">Headers</p>
<pre class="dc">{html.escape(str(p['headers_raw']))}</pre></div>"""
                if p.get("corpo"):
                    h += f"""<div class="db bb"><p class="dt">👇 Corpo Descriptografado</p>
<pre class="dc">{html.escape(str(p['corpo'])[:3000])}</pre></div>"""
                if p.get("tls"):
                    h += f"""<div class="db bt"><p class="dt">TLS</p>
<pre class="dc">{html.escape(str(p['tls']))}</pre></div>"""
                h += "</div>"
        else:
            h += "<p>Sem resultados de descriptografia.</p>"

        h += '<h2 id="keys">🔑 Chaves TLS</h2>'
        if self.keylog:
            h += ("<table><thead><tr><th>Client Random</th>"
                  "<th>Tipo</th><th>Site (SNI)</th></tr></thead><tbody>")
            for e in self.keylog:
                site = ", ".join(self.snis.get(str(e.get("client_random", "")).lower(), []))
                h += (
                    f"<tr><td><code>{html.escape(str(e.get('client_random', '')))}</code></td>"
                    f"<td>{html.escape(str(e.get('label', '')))}</td>"
                    f"<td>{html.escape(site)}</td></tr>"
                )
            h += "</tbody></table>"
        else:
            h += "<p>Nenhuma chave.</p>"

        h += """
</div>
<a href="#topo" class="btn-topo">⬆ Topo</a>
</body></html>"""
        return h


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        try:
            root_crash = tk.Tk()
            root_crash.withdraw()
            messagebox.showerror("Erro fatal", str(e))
        except Exception:
            print("Erro fatal:", e)
        sys.exit(1)
