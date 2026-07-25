#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ NETSTAT + DNS REVERSO + GEOLOCALIZAÇÃO // HACKER MODE
→ Clique direito no IP → VirusTotal / Google Maps (pino vermelho)
→ Clique duplo no Remoto → VirusTotal
→ Só carrega dados ao clicar em ATUALIZAR (ou ative auto-refresh)
→ SEM JANELA DO CMD (CREATE_NO_WINDOW)
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import re
import json
import urllib.request
import urllib.error
import time as time_module
import webbrowser
import urllib.parse
import socket
import sys

# ── Flag para suprimir a janela do cmd no Windows ──
if sys.platform == "win32":
    _NO_WINDOW = subprocess.CREATE_NO_WINDOW  # 0x08000000
else:
    _NO_WINDOW = 0  # não tem efeito no Linux/macOS

# ═══════════════════════════════════════════════════════════
# CACHES
# ═══════════════════════════════════════════════════════════

_cache_processos: dict[str, str] = {}
_cache_dns: dict[str, str] = {}
_cache_geo: dict[str, dict] = {}

# ═══════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════

def nome_processo(pid: str) -> str:
    """Retorna o nome do executável a partir do PID (Windows)."""
    if not pid or pid == "-":
        return "-"
    if pid in _cache_processos:
        return _cache_processos[pid]
    try:
        raw = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL, timeout=3,
            creationflags=_NO_WINDOW          # ← SEM CMD
        ).decode("utf-8", errors="replace")
        if raw.strip():
            nome = raw.split(",")[0].strip('"')
            _cache_processos[pid] = nome
            return nome
    except Exception:
        pass
    _cache_processos[pid] = pid
    return pid


def reverse_dns(ip: str) -> str:
    """Resolve o nome de domínio via PTR record."""
    if ip in ("0.0.0.0", "127.0.0.1", "::1", "::", "", "*"):
        return "-"
    if ip in _cache_dns:
        return _cache_dns[ip]
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        hostname = hostname.rstrip(".")
        if len(hostname) > 80:
            parts = hostname.split(".")
            hostname = ".".join(parts[-3:]) if len(parts) > 3 else ".".join(parts[-2:])
        _cache_dns[ip] = hostname
        return hostname
    except Exception:
        _cache_dns[ip] = "-"
        return "-"


def geoip(ip: str) -> dict:
    """Retorna dados de geolocalização para um IP."""
    if ip in ("0.0.0.0", "127.0.0.1", "::1", "::", "", "*"):
        return {"pais": "Local", "estado": "-", "cidade": "localhost",
                "lat": None, "lon": None}
    if ip in _cache_geo:
        return _cache_geo[ip]
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,query"
        req = urllib.request.urlopen(url, timeout=3)
        data = json.loads(req.read().decode())
        if data.get("status") == "success":
            resultado = {
                "pais": data.get("country", "??"),
                "estado": data.get("regionName", "??"),
                "cidade": data.get("city", "??"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
            _cache_geo[ip] = resultado
            return resultado
        return {"pais": "Desconhecido", "estado": "-", "cidade": "-",
                "lat": None, "lon": None}
    except Exception:
        return {"pais": "Erro", "estado": "-", "cidade": "-",
                "lat": None, "lon": None}


def parse_netstat() -> list:
    """Executa netstat -ano e retorna lista de dicts."""
    resultados = []
    try:
        raw = subprocess.check_output(
            ["netstat", "-ano"], stderr=subprocess.DEVNULL, timeout=8,
            creationflags=_NO_WINDOW          # ← SEM CMD
        ).decode("utf-8", errors="replace")
    except Exception:
        return []

    padrao_ip = re.compile(
        r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\[?::[\da-f:]+\]?):(\d+)"
    )
    estados_validos = re.compile(
        r"(ESTABLISHED|LISTENING?|TIME_WAIT|CLOSE_WAIT|SYN_SENT|"
        r"SYN_RCVD|FIN_WAIT\d?|LAST_ACK|CLOSING|CLOSED)", re.IGNORECASE
    )

    linhas = raw.splitlines()
    for linha in linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            continue

        upper = linha_strip.upper()
        if ("PROTO" in upper and "LOCAL" in upper) \
           or upper in ("ATIVO", "ACTIVE", "CONEXÕES", "CONNECTIONS") \
           or "CONEXÕES ATIVAS" in upper \
           or "ACTIVE CONNECTIONS" in upper:
            continue

        partes = linha_strip.split()
        if len(partes) < 4:
            continue

        proto = partes[0].upper()
        if proto not in ("TCP", "UDP", "TCP6", "UDP6"):
            continue

        ips_encontrados = padrao_ip.findall(linha_strip)

        if proto.startswith("UDP"):
            if len(ips_encontrados) >= 1:
                local_ip, local_porta = ips_encontrados[0]
                remote_ip = "*"
                remote_porta = "*"
                estado = "UDP"
            else:
                continue
        else:
            if len(ips_encontrados) < 2:
                continue
            local_ip, local_porta = ips_encontrados[0]
            remote_ip, remote_porta = ips_encontrados[1]
            estado_match = estados_validos.search(linha_strip)
            estado = estado_match.group(1).upper() if estado_match else "-"

        local_ip = local_ip.strip("[]")
        remote_ip = remote_ip.strip("[]")
        pid = partes[-1] if partes[-1].isdigit() else ""

        resultados.append({
            "protocolo": proto,
            "local": f"{local_ip}:{local_porta}",
            "remoto": f"{remote_ip}:{remote_porta}",
            "remote_ip": remote_ip,
            "remote_porta": remote_porta,
            "estado": estado,
            "pid": pid,
            "processo": nome_processo(pid),
        })

    return resultados


# ═══════════════════════════════════════════════════════════
# INTERFACE GRÁFICA — HACKER MODE
# ═══════════════════════════════════════════════════════════

class NetstatGeoApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("⚡ NETSTAT + DNS REVERSO + GEOLOCALIZAÇÃO ⚡")
        master.geometry("1480x820")
        self.master.state("zoomed")   # Maximiza a janela
        master.minsize(1100, 650)
        master.configure(bg="#000000")

        # ── Cores do tema ──
        self.BG       = "#000000"
        self.FG       = "#00ff41"
        self.FG_DIM   = "#00aa2a"
        self.BG_DARK  = "#0a0f0a"
        self.BG_SEL   = "#003311"
        self.HEADER   = "#001a00"
        self.ACCENT   = "#00ff88"
        self.WARNING  = "#ffaa00"

        self.dados_originais: list[dict] = []
        self.geo_executando = False

        # ── Controle do auto-refresh ──
        self._auto_refresh_id = None    # ID do after() agendado
        self._auto_intervalo = 0         # 0 = desligado

        # ── Configurar estilo ttk ──
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.BG, foreground=self.FG,
                        fieldbackground=self.BG_DARK, selectbackground=self.BG_SEL,
                        selectforeground=self.ACCENT, font=("Consolas", 10))

        style.configure("TFrame", background=self.BG)
        style.configure("TLabel", background=self.BG, foreground=self.FG,
                        font=("Consolas", 10))
        style.configure("TButton", background=self.BG_DARK, foreground=self.FG,
                        bordercolor=self.FG_DIM, lightcolor=self.BG_DARK,
                        darkcolor=self.BG_DARK, focuscolor=self.BG_SEL,
                        font=("Consolas", 9, "bold"), padding=5)
        style.map("TButton",
                  background=[("active", self.BG_SEL), ("disabled", self.BG)],
                  foreground=[("disabled", "#004400")])
        style.configure("Treeview", background=self.BG_DARK,
                        fieldbackground=self.BG_DARK, foreground=self.FG,
                        font=("Consolas", 9), rowheight=22,
                        bordercolor=self.FG_DIM)
        style.map("Treeview",
                  background=[("selected", self.BG_SEL)],
                  foreground=[("selected", self.ACCENT)])
        style.configure("Treeview.Heading", background=self.HEADER,
                        foreground=self.FG, font=("Consolas", 9, "bold"),
                        bordercolor=self.FG_DIM, relief="flat")
        style.map("Treeview.Heading",
                  background=[("active", "#002200")])
        style.configure("TEntry", fieldbackground=self.BG_DARK,
                        foreground=self.FG, bordercolor=self.FG_DIM,
                        font=("Consolas", 10))
        style.configure("TSpinbox", fieldbackground=self.BG_DARK,
                        foreground=self.FG, font=("Consolas", 10))
        style.configure("TScrollbar", background=self.BG_DARK,
                        troughcolor=self.BG, bordercolor=self.FG_DIM,
                        arrowcolor=self.FG)
        style.configure("TCombobox", fieldbackground=self.BG_DARK,
                        foreground=self.FG, background=self.BG_DARK,
                        arrowcolor=self.FG, font=("Consolas", 9))

        # ── Estilos específicos para o Combobox de auto-refresh ──
        style.configure("AutoOff.TCombobox",
                        fieldbackground=self.BG_DARK,
                        foreground="#000000",          # PRETO quando OFF
                        background=self.BG_DARK,
                        arrowcolor=self.FG,
                        font=("Consolas", 9, "bold"))
        style.configure("AutoOn.TCombobox",
                        fieldbackground=self.BG_DARK,
                        foreground=self.FG,            # VERDE quando ligado
                        background=self.BG_DARK,
                        arrowcolor=self.FG,
                        font=("Consolas", 9, "bold"))

        # ── Frame superior ──
        frame_topo = ttk.Frame(master)
        frame_topo.pack(fill=tk.X, padx=10, pady=10)

        titulo = ttk.Label(
            frame_topo,
            text="⚡ NETSTAT + DNS REVERSO + GEOLOCALIZAÇÃO",
            font=("Consolas", 14, "bold"), foreground=self.ACCENT
        )
        titulo.pack(side=tk.LEFT, padx=5)

        # ── AUTO-REFRESH: Combobox para intervalo ──
        ttk.Label(frame_topo, text="⟳ AUTO",
                  font=("Consolas", 9, "bold")).pack(side=tk.RIGHT, padx=(5, 0))    

        self.cb_auto = ttk.Combobox(
            frame_topo, width=8, state="readonly",
            values=["OFF", "1s", "2s", "3s", "4s", "5s"],
            style="AutoOff.TCombobox"       # ← início com OFF em PRETO
        )
        
        self.cb_auto.current(0)
        self.cb_auto.pack(side=tk.RIGHT, padx=(0, 5))
        self.cb_auto.bind("<<ComboboxSelected>>", self._on_auto_intervalo_change)

        # Botões
        self.btn_atualizar = ttk.Button(
            frame_topo, text="⟳ ATUALIZAR", command=self.iniciar_atualizacao
        )
        self.btn_atualizar.pack(side=tk.RIGHT, padx=3)

        self.btn_filtrar_br = ttk.Button(
            frame_topo, text="BR", command=self.filtrar_brasil, width=6
        )
        self.btn_filtrar_br.pack(side=tk.RIGHT, padx=2)

        self.btn_filtrar_sp = ttk.Button(
            frame_topo, text="SP", command=self.filtrar_sp, width=4
        )
        self.btn_filtrar_sp.pack(side=tk.RIGHT, padx=2)

        self.btn_limpar_filtro = ttk.Button(
            frame_topo, text="⟲ TUDO", command=self.mostrar_tudo, width=8
        )
        self.btn_limpar_filtro.pack(side=tk.RIGHT, padx=2)

        self.lbl_status = ttk.Label(frame_topo, text="[ AGUARDANDO ]")
        self.lbl_status.pack(side=tk.RIGHT, padx=15)

        # ── TreeView ──
        colunas = ("protocolo", "local", "remoto", "hostname", "estado",
                   "pid", "processo", "pais", "estado_geo", "cidade")
        frame_tabela = ttk.Frame(master)
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings",
                                 height=25)

        headers = {
            "protocolo":  "PROTO",
            "local":      "LOCAL",
            "remoto":     "REMOTO 🔍",
            "hostname":   "DOMÍNIO / SITE",
            "estado":     "ESTADO",
            "pid":        "PID",
            "processo":   "PROCESSO",
            "pais":       "PAÍS",
            "estado_geo": "ESTADO (GEO)",
            "cidade":     "CIDADE",
        }
        larguras = {
            "protocolo": 60, "local": 180, "remoto": 180, "hostname": 350,
            "estado": 100, "pid": 55, "processo": 180, "pais": 120,
            "estado_geo": 140, "cidade": 140
        }

        for col, texto in headers.items():
            self.tree.heading(
                col, text=texto,
                command=lambda c=col: self.ordenar_por(c)
            )
            self.tree.column(
                col, width=larguras.get(col, 100), minwidth=50,
                anchor=tk.CENTER if col in ("protocolo","estado","pid") else tk.W
            )

        scroll_y = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL,
                                 command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient=tk.HORIZONTAL,
                                 command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set,
                            xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)

        # ── Bindings de clique ──
        self.tree.bind("<Button-3>", self._mostrar_menu_contexto)
        self.tree.bind("<Double-1>", self._clique_duplo_remoto)

        # ── Filtro por texto ──
        frame_filtro = ttk.Frame(master)
        frame_filtro.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(frame_filtro, text="▸ FILTRO:", font=("Consolas", 9, "bold")
                  ).pack(side=tk.LEFT, padx=2)
        self.entry_filtro = ttk.Entry(frame_filtro, width=60)
        self.entry_filtro.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_filtro.bind("<KeyRelease>",
                               lambda e: self.aplicar_filtro_texto())
        self.entry_filtro.insert(0, "")
        ttk.Label(frame_filtro, text="[ hostname | ip | país | processo ]",
                  foreground=self.FG_DIM, font=("Consolas", 8)
                  ).pack(side=tk.LEFT, padx=5)

        # ── Barra de resumo ──
        self.lbl_resumo = ttk.Label(
            master, text="[ AGUARDE ]  Carregue os dados com ATUALIZAR",
            font=("Consolas", 9), foreground=self.FG_DIM
        )
        self.lbl_resumo.pack(anchor=tk.W, padx=12, pady=(0, 8))

    # ════════════════════════════════════════════════════════
    # AUTO-REFRESH LOGIC
    # ════════════════════════════════════════════════════════

    def _on_auto_intervalo_change(self, event=None):
        """Dispara quando o usuário muda o valor do Combobox de auto-refresh."""
        texto = self.cb_auto.get()
        if texto == "OFF":
            self.cb_auto.configure(style="AutoOff.TCombobox")   # ← PRETO
            self._parar_auto_refresh()
        else:
            self.cb_auto.configure(style="AutoOn.TCombobox")    # ← VERDE
            segundos = int(texto.replace("s", ""))
            self._iniciar_auto_refresh(segundos)

    def _iniciar_auto_refresh(self, intervalo_seg: int):
        """Inicia (ou reinicia) o timer de auto-refresh com o intervalo dado."""
        self._parar_auto_refresh()  # cancela qualquer timer anterior
        self._auto_intervalo = intervalo_seg
        self.lbl_status.config(text=f"[ ⟳ AUTO: {intervalo_seg}s ]")
        # Agenda o primeiro ciclo
        self._agendar_proximo_auto()

    def _parar_auto_refresh(self):
        """Cancela o auto-refresh timer."""
        if self._auto_refresh_id is not None:
            self.master.after_cancel(self._auto_refresh_id)
            self._auto_refresh_id = None
        self._auto_intervalo = 0

    def _agendar_proximo_auto(self):
        """Agenda o próximo ciclo de auto-refresh."""
        if self._auto_intervalo <= 0:
            return
        # Só agenda se não houver um já pendente
        if self._auto_refresh_id is None:
            ms = self._auto_intervalo * 1000
            self._auto_refresh_id = self.master.after(ms, self._executar_auto_cycle)

    def _executar_auto_cycle(self):
        """Callback do timer: executa a atualização e re-agenda."""
        self._auto_refresh_id = None  # limpa o ID pois o after já executou

        # Se já está rodando uma atualização, não sobrepõe — re-agenda
        if self.geo_executando:
            self._agendar_proximo_auto()
            return

        # Dispara a atualização (thread)
        self.iniciar_atualizacao()

        # Re-agenda o próximo ciclo (o timer corre em paralelo com a thread)
        self._agendar_proximo_auto()

    # ════════════════════════════════════════════════════════
    # AÇÕES COM IP
    # ════════════════════════════════════════════════════════

    def _extrair_ip_remoto_da_linha(self, item) -> tuple:
        valores = self.tree.item(item, "values")
        if not valores or len(valores) < 10:
            return (None, None, None, None, None, None, None)
        remoto = valores[2]
        ip = remoto.rsplit(":", 1)[0] if ":" in remoto else remoto
        if ip in ("0.0.0.0", "127.0.0.1", "::1", "::", "*", "-"):
            return (None, None, None, None, None, None, None)
        geo = _cache_geo.get(ip, {})
        lat = geo.get("lat")
        lon = geo.get("lon")
        cidade = valores[9]
        estado = valores[8]
        pais   = valores[7]
        hostname = valores[3]
        return (ip, lat, lon, cidade, estado, pais, hostname)

    def _abrir_virustotal(self, ip: str):
        webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

    def _abrir_google_maps_com_pin(self, ip, lat, lon, cidade, estado, pais):
        if lat is not None and lon is not None:
            url = f"https://www.google.com/maps?q={lat},{lon}"
        elif cidade and cidade != "-" and estado and estado != "-":
            query = urllib.parse.quote(f"{cidade}, {estado}, {pais}")
            url = f"https://www.google.com/maps?q={query}"
        else:
            url = f"https://www.google.com/maps?q={ip}"
        webbrowser.open(url)

    def _mostrar_menu_contexto(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        ip, lat, lon, cidade, estado, pais, hostname = \
            self._extrair_ip_remoto_da_linha(item)
        if not ip:
            return

        menu = tk.Menu(self.master, tearoff=0,
                       bg=self.BG_DARK, fg=self.FG,
                       font=("Consolas", 9),
                       activebackground=self.BG_SEL,
                       activeforeground=self.ACCENT,
                       borderwidth=1, relief="solid")

        vt_label = f"🔍 VIRUSTOTAL — {hostname} ({ip})" if hostname != "-" else f"🔍 VIRUSTOTAL — {ip}"
        menu.add_command(label=vt_label, command=lambda i=ip: self._abrir_virustotal(i))

        if lat is not None and lon is not None:
            maps_label = f"📍 GOOGLE MAPS ({lat:.4f}, {lon:.4f})"
        elif cidade and cidade != "-":
            maps_label = f"📍 GOOGLE MAPS — {cidade}, {estado}"
        else:
            maps_label = f"📍 GOOGLE MAPS — {ip}"
        menu.add_command(
            label=maps_label,
            command=lambda i=ip, la=lat, lo=lon, c=cidade, e=estado, p=pais:
                self._abrir_google_maps_com_pin(i, la, lo, c, e, p)
        )

        menu.add_separator()
        menu.add_command(label="📋 COPIAR IP", command=lambda: self._copiar_ip(ip))
        if hostname and hostname != "-":
            menu.add_command(label=f"📋 COPIAR DOMÍNIO: {hostname}",
                             command=lambda: self._copiar_texto(hostname, "DOMÍNIO"))
        if lat is not None and lon is not None:
            menu.add_command(label=f"📐 COORD: {lat:.4f}, {lon:.4f}",
                             command=lambda: self._copiar_coords(lat, lon))

        menu.post(event.x_root, event.y_root)

    def _clique_duplo_remoto(self, event):
        col_id = self.tree.identify_column(event.x)
        try:
            col_idx = int(col_id.replace("#", "")) - 1
        except ValueError:
            return
        if col_idx != 2:
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        ip, _, _, _, _, _, _ = self._extrair_ip_remoto_da_linha(item)
        if ip:
            self._abrir_virustotal(ip)

    def _copiar_ip(self, ip: str):
        self.master.clipboard_clear()
        self.master.clipboard_append(ip)
        self.lbl_status.config(text=f"📋 IP {ip} COPIADO!")

    def _copiar_coords(self, lat: float, lon: float):
        texto = f"{lat:.6f}, {lon:.6f}"
        self.master.clipboard_clear()
        self.master.clipboard_append(texto)
        self.lbl_status.config(text=f"📐 COORDS {texto} COPIADAS!")

    def _copiar_texto(self, texto: str, tipo: str = "TEXTO"):
        self.master.clipboard_clear()
        self.master.clipboard_append(texto)
        self.lbl_status.config(text=f"📋 {tipo} '{texto}' COPIADO!")

    # ════════════════════════════════════════════════════════
    # ATUALIZAÇÃO DOS DADOS
    # ════════════════════════════════════════════════════════

    def iniciar_atualizacao(self):
        if self.geo_executando:
            return
        self.geo_executando = True
        self.btn_atualizar.config(state=tk.DISABLED)
        self.lbl_status.config(text="[ COLETANDO NETSTAT... ]")
        threading.Thread(target=self._atualizar_dados, daemon=True).start()

    def _atualizar_dados(self):
        try:
            conexoes = parse_netstat()
        except Exception:
            conexoes = []
        self.master.after(0, lambda: self._processar_geo(conexoes))

    def _processar_geo(self, conexoes: list[dict]):
        if not conexoes:
            self.dados_originais = []
            self.master.after(0, self._exibir_dados)
            return

        ips_unicos = sorted({
            c["remote_ip"] for c in conexoes
            if c["remote_ip"] not in ("0.0.0.0","127.0.0.1","::1","::","*","")
        })

        self.lbl_status.config(text=f"[ RESOLVENDO DNS: {len(ips_unicos)} IPs ]")

        # FASE 1: DNS reverso
        for i, ip in enumerate(ips_unicos):
            if ip not in _cache_dns:
                if i > 0 and i % 20 == 0:
                    time_module.sleep(0.3)
                reverse_dns(ip)

        self.lbl_status.config(text=f"[ GEOLOCALIZANDO... ]")

        # FASE 2: Geolocalização
        ips_geo = [ip for ip in ips_unicos if ip not in _cache_geo]
        for i, ip in enumerate(ips_geo):
            if i > 0 and i % 40 == 0:
                time_module.sleep(1.2)
            geoip(ip)

        # Monta dados
        self.dados_originais = []
        for c in conexoes:
            ip = c["remote_ip"]
            geo = _cache_geo.get(ip, {"pais": "-", "estado": "-", "cidade": "-",
                                       "lat": None, "lon": None})
            hostname = _cache_dns.get(ip, "-")
            self.dados_originais.append({
                **c,
                "hostname": hostname if hostname != "-" else "-",
                "pais": geo["pais"],
                "estado_geo": geo["estado"],
                "cidade": geo["cidade"],
                "lat": geo.get("lat"),
                "lon": geo.get("lon"),
            })

        self.master.after(0, self._exibir_dados)

    def _exibir_dados(self):
        # Preserva o filtro de texto atual, se houver
        texto_filtro = self.entry_filtro.get().strip()
        if texto_filtro:
            self.aplicar_filtro_texto()
        else:
            self.mostrar_tudo()
        self.geo_executando = False
        self.btn_atualizar.config(state=tk.NORMAL)
        n = len(self.dados_originais)
        com_dns = sum(1 for d in self.dados_originais if d["hostname"] != "-")

        # Mantém o indicador de auto-refresh no status se estiver ativo
        if self._auto_intervalo > 0:
            self.lbl_status.config(
                text=f"[ ✅ {n} CONEXÕES | 🌐 {com_dns} DOMÍNIOS | ⟳ AUTO: {self._auto_intervalo}s ]"
            )
        else:
            self.lbl_status.config(
                text=f"[ ✅ {n} CONEXÕES | 🌐 {com_dns} DOMÍNIOS ]"
            )

    # ════════════════════════════════════════════════════════
    # FILTROS
    # ════════════════════════════════════════════════════════

    def mostrar_tudo(self):
        self._popular_tree(self.dados_originais)

    def filtrar_brasil(self):
        filtrados = [
            d for d in self.dados_originais
            if d["pais"].lower() in ("brazil", "brasil")
        ]
        self._popular_tree(filtrados)

    def filtrar_sp(self):
        filtrados = [
            d for d in self.dados_originais
            if "sao paulo" in d["estado_geo"].lower()
            or "são paulo" in d["estado_geo"].lower()
        ]
        self._popular_tree(filtrados)

    def aplicar_filtro_texto(self):
        texto = self.entry_filtro.get().strip().lower()
        if not texto:
            self._popular_tree(self.dados_originais)
            return
        filtrados = [
            d for d in self.dados_originais
            if texto in d["remoto"].lower()
            or texto in d["local"].lower()
            or texto in d["pais"].lower()
            or texto in d["estado_geo"].lower()
            or texto in d["cidade"].lower()
            or texto in d["estado"].lower()
            or texto in d["pid"]
            or texto in d.get("processo", "").lower()
            or texto in d.get("hostname", "").lower()
        ]
        self._popular_tree(filtrados)

    def _popular_tree(self, dados: list[dict]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for d in dados:
            tags = ()
            if d["pais"].lower() in ("brazil", "brasil"):
                tags = ("brasil",)
                if ("sao paulo" in d["estado_geo"].lower()
                        or "são paulo" in d["estado_geo"].lower()):
                    tags = ("sp",)

            self.tree.insert("", tk.END, values=(
                d["protocolo"],
                d["local"],
                d["remoto"],
                d.get("hostname", "-"),
                d["estado"],
                d["pid"],
                d.get("processo", "-"),
                d["pais"],
                d["estado_geo"],
                d["cidade"],
            ), tags=tags)

        self.tree.tag_configure("brasil", background="#002200")
        self.tree.tag_configure("sp", background="#003311")

        total = len(dados)
        br = sum(1 for d in dados if d["pais"].lower() in ("brazil","brasil"))
        sp = sum(1 for d in dados
                 if "sao paulo" in d["estado_geo"].lower()
                 or "são paulo" in d["estado_geo"].lower())
        com_dns = sum(1 for d in dados if d.get("hostname", "-") != "-")
        self.lbl_resumo.config(
            text=f"[ 📊 TOTAL: {total} | 🌐 DOMÍNIOS: {com_dns} | "
                 f"🇧🇷 BR: {br} | 📍 SP: {sp} ]"
        )

    def ordenar_por(self, coluna: str):
        items = self.tree.get_children("")
        if not items:
            return
        dados_tela = [self.tree.item(i)["values"] for i in items]
        col_order = ("protocolo","local","remoto","hostname","estado",
                     "pid","processo","pais","estado_geo","cidade")
        idx = col_order.index(coluna)
        dados_tela.sort(key=lambda r: str(r[idx]).lower())
        for i, vals in enumerate(dados_tela):
            self.tree.move(items[i], "", i)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = NetstatGeoApp(root)
    root.mainloop()
