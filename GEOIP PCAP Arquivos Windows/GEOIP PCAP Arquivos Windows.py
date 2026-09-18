import os
import warnings
import sys
import io
import re
import ipaddress
import socket
import threading
import urllib.request
import webbrowser
import time
import json
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ====================== SUPRESSÃO DE AVISOS ======================
os.environ["SCAPY_NO_WIRESHARK"] = "1"
warnings.filterwarnings("ignore")
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except:
    pass
sys.stderr = io.StringIO()

# Scapy
try:
    from scapy.all import rdpcap, IP, IPv6
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class GeoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GEOIP - PCAP + Arquivos Windows")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")

        self.current_ip = None
        self.current_lat = None
        self.current_lon = None
        self.data = []
        self.is_loading = False
        
        # Flags para scan e Regex
        self.stop_scan = False
        self.seen_ips = set()
        self.CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB de leitura por bloco

        self.ipv4_pattern = re.compile(rb'(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])')
        self.ipv4_text = re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b')
        self.ipv6_text = re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b')
        self.url_pattern = re.compile(rb'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]{3,800}')
        self.domain_text = re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+(?:com|net|org|br|io|dev|app|xyz|info|gov|edu|uk|de|fr|jp|cn|ru|in|co|tv|me|cc|gg|to|online|site|tech|cloud|ai|cdn|api|us|au|ca|es|it|nl|se|no|pl|ch|at|be|pt|ar|mx|cl|pe)\b', re.IGNORECASE)

        # ==================== ESTILO ====================
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0a0a0a")
        style.configure("TLabel", background="#0a0a0a", foreground="#00ff41")
        style.configure("Treeview", background="#0f0f0f", foreground="#00ff41", fieldbackground="#0f0f0f", rowheight=24)
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="#00ff41")
        style.map("Treeview", background=[("selected", "#004400")], foreground=[("selected", "#00ff41")])

        # ==================== Frame Superior ====================
        top_frame = tk.Frame(root, bg="#0a0a0a")
        top_frame.pack(fill="x", pady=10, padx=15)

        btn_font = ("Consolas", 11, "bold")
        
        tk.Button(top_frame, text="📦 PCAPNG", command=self.start_loading_pcap, bg="#00b300", fg="#0a0a0a", font=btn_font, width=12).pack(side="left", padx=4)
        tk.Button(top_frame, text="📂 ARQUIVO", command=self.start_loading_any_file, bg="#ff8800", fg="#0a0a0a", font=btn_font, width=12).pack(side="left", padx=4)
        tk.Button(top_frame, text="📁 PASTA", command=self.start_loading_folder, bg="#cc00ff", fg="#ffffff", font=btn_font, width=10).pack(side="left", padx=4)
        
        tk.Button(top_frame, text="🛑 STOP", command=self.stop_process, bg="#ff0000", fg="#ffffff", font=btn_font, width=8).pack(side="left", padx=15)
        tk.Button(top_frame, text="📄 HTML", command=self.export_html, bg="#00cccc", fg="#0a0a0a", font=btn_font, width=10).pack(side="left", padx=4)

        tk.Label(top_frame, text="🔎:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold")).pack(side="left", padx=(15, 0))

        search_frame = tk.Frame(top_frame, bg="#0a0a0a")
        search_frame.pack(side="left", padx=5)

        self.search = tk.Entry(search_frame, width=25, bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 11))
        self.search.pack(side="left", padx=(0, 4))
        self.search.bind("<KeyRelease>", self.live_filter)
        self.search.bind("<Return>", self.live_filter)

        tk.Button(top_frame, text="🗺 MAPS", command=self.open_google_maps, bg="#09b875", fg="#030303", font=("Consolas", 10, "bold"), width=8).pack(side="right", padx=4)
        tk.Button(top_frame, text="📍 STREET", command=self.open_street_view, bg="#00b7ff", fg="#020202", font=("Consolas", 10, "bold"), width=10).pack(side="right", padx=4)

        # ==================== Progresso ====================
        self.progress_frame = tk.Frame(root, bg="#0a0a0a")
        self.progress_frame.pack(fill="x", pady=8, padx=15)

        self.progress_label = tk.Label(self.progress_frame, text="PROGRESSO: 0%", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold"))
        self.progress_label.pack(side="left", padx=8)

        style.configure("green.Horizontal.TProgressbar", background="#00ff41", troughcolor="#1a1a1a", thickness=14)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=800, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side="right", padx=15)

        # ==================== Treeview ====================
        tree_frame = tk.Frame(root, bg="#0a0a0a")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        columns = ("IP", "Tipo", "Pais", "Cidade", "Estado", "Latitude", "Longitude", "Site", "Origem Nome do arquivo")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        widths = {"IP": 140, "Tipo": 50, "Pais": 100, "Cidade": 120, "Estado": 120, "Latitude": 90, "Longitude": 90, "Site": 250, "Origem Nome do arquivo": 200}
        for col in columns:
            self.tree.heading(col, text=col)
            anchor = "w" if col in ("IP", "Site", "Origem Nome do arquivo") else "center"
            self.tree.column(col, width=widths[col], minwidth=80, anchor=anchor)

        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.v_scrollbar.config(command=self.tree.yview)
        self.h_scrollbar.config(command=self.tree.xview)

        # ==================== MENU DE CONTEXTO ====================
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#1a1a1a", fg="#00ff41", activebackground="#00b300", activeforeground="#0a0a0a", font=("Consolas", 10))

        self.context_menu.add_command(label="🛡️ VirusTotal", command=self.open_virustotal)
        self.context_menu.add_command(label="🌐 BGP.HE.NET", command=self.open_bgphe)
        self.context_menu.add_command(label="🔍 WhatIsMyIP", command=self.open_whatismyip)
        self.context_menu.add_command(label="🌍 Web-Check.xyz", command=self.open_webcheck)
        self.context_menu.add_command(label="🔎 Hunter.how", command=self.open_hunterhow)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 AbuseIPDB", command=self.open_abuseipdb)
        self.context_menu.add_command(label="🔎 IPinfo.io", command=self.open_ipinfo)
        self.context_menu.add_command(label="👁️ Shodan", command=self.open_shodan)
        self.context_menu.add_command(label="📡 Censys", command=self.open_censys)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Copiar IP", command=self.copy_ip)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ==================== RODAPÉ ====================
        footer = tk.Frame(root, bg="#000000", height=40)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="Lê qualquer arquivo inteiro sem limites de tamanho. Botão direito sobre o IP para OSINT.",
                 bg="#000000", fg="#07e0f0", font=("Consolas", 10)).pack(pady=10)

    # ==================== UTILITÁRIOS ====================
    def stop_process(self):
        if self.is_loading:
            self.stop_scan = True
            self.progress_label.config(text="🛑 CANCELANDO... AGUARDE", fg="#ff0000")

    def _reset_ui(self):
        self.tree.delete(*self.tree.get_children())
        self.data.clear()
        self.seen_ips.clear()
        self.progress_bar["value"] = 0
        self.stop_scan = False

    def finish_loading(self):
        self.is_loading = False
        if self.stop_scan:
            self.update_progress(self.progress_bar["value"], "🛑 SCAN PARADO")
            messagebox.showwarning("Aviso", "Processo cancelado pelo usuário.")
        else:
            self.update_progress(100, "CONCLUÍDO ✅")
            messagebox.showinfo("SUCESSO", f"{len(self.data)} IP processados.")
        self.stop_scan = False

    def update_progress(self, value, text=""):
        self.progress_bar['value'] = value
        cor = "#ff0000" if self.stop_scan else "#00ff41"
        self.progress_label.config(text=f"PROGRESSO: {int(value)}% {text}", fg=cor)
        self.root.update_idletasks()

    def format_size(self, n):
        if n < 1024: return f"{n} B"
        if n < 1024**2: return f"{n/1024:.1f} KB"
        if n < 1024**3: return f"{n/(1024**2):.1f} MB"
        return f"{n/(1024**3):.2f} GB"

    def is_public_ip(self, ip_str):
        try:
            return ipaddress.ip_address(str(ip_str).strip()).is_global
        except:
            return False

    def resolve_domain(self, domain):
        try:
            for info in socket.getaddrinfo(domain, None, socket.AF_UNSPEC):
                ip = info[4][0]
                if self.is_public_ip(ip): return ip
        except: pass
        return None

    def copy_ip(self):
        if self.current_ip:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_ip)

    # ==================== EXTRAÇÃO ====================
    def extract_from_bytes(self, raw: bytes):
        ips, domains = set(), set()
        for m in self.ipv4_pattern.finditer(raw):
            try:
                ip = m.group().decode("ascii", errors="ignore")
                if self.is_public_ip(ip): ips.add(ip)
            except: pass
        for m in self.url_pattern.finditer(raw):
            try:
                u = re.sub(r'[\x00-\x1f\x7f-\xff]+$', '', m.group().decode("ascii", errors="ignore"))
                host = urlparse(u).hostname
                if host and "." in host: domains.add(host.lower().strip("."))
            except: pass
        for enc in ("utf-8", "latin-1"):
            try: text = raw.decode(enc, errors="ignore")
            except: continue
            for m in self.ipv4_text.finditer(text):
                if self.is_public_ip(m.group()): ips.add(m.group())
            for m in self.ipv6_text.finditer(text):
                if self.is_public_ip(m.group()): ips.add(m.group())
            for m in self.domain_text.finditer(text):
                d = m.group().lower()
                if not re.search(r'\.(png|jpg|gif|css|js|woff2?|ttf|ico|svg|mp4|webp|woff)$', d):
                    domains.add(d)
            break
        return ips, domains

    def scan_file_full(self, filepath: str):
        ips, domains = set(), set()
        try: total_size = os.path.getsize(filepath)
        except: return ips, domains
        
        read_total = 0
        fname = os.path.basename(filepath)
        overlap = b""
        OVERLAP_N = 256

        try:
            with open(filepath, "rb") as f:
                while True:
                    if self.stop_scan: break
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk: break
                    data = overlap + chunk
                    f_ips, f_doms = self.extract_from_bytes(data)
                    ips |= f_ips
                    domains |= f_doms
                    overlap = data[-OVERLAP_N:] if len(data) >= OVERLAP_N else data
                    read_total += len(chunk)
                    
                    pct = (read_total / max(total_size, 1)) * 35
                    self.root.after(0, self.update_progress, pct, f"Lendo {fname}: {self.format_size(read_total)}")
        except: pass
        return ips, domains

    # ==================== GEO API ====================
    def get_geo_info(self, ip, origin=""):
        ip_type = "IPv6" if ":" in str(ip) else "IPv4"
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,city,regionName,lat,lon,org"
            req = urllib.request.Request(url, headers={"User-Agent": "GeoIPTool/3.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    org = data.get("org") or socket.gethostbyaddr(ip)[0] if data.get("org") not in ["NA", "null", ""] else "Não resolvido"
                    return [ip, ip_type, data.get("country", "-"), data.get("city", "-"), data.get("regionName", "-"), data.get("lat", "-"), data.get("lon", "-"), org, origin]
        except: pass
        return [ip, ip_type, "-", "-", "-", "-", "-", "Não resolvido", origin]

    def process_ips_with_geo(self, ip_origin_map: dict):
        items = list(ip_origin_map.items())
        total = len(items)
        for i, (ip, origin) in enumerate(items):
            if self.stop_scan: break
            if ip in self.seen_ips: continue
            self.seen_ips.add(ip)

            row = self.get_geo_info(ip, origin)
            self.data.append(row)

            progress = 40 + ((i + 1) / max(total, 1)) * 60
            self.root.after(0, self.update_progress, progress, f"Geolocalizando {i+1}/{total} -> {ip}")
            self.root.after(0, lambda r=row: self.tree.insert("", tk.END, values=r))

            if (i + 1) % 40 == 0 and (i + 1) < total:
                for t in range(65, 0, -1):
                    if self.stop_scan: break
                    self.root.after(0, self.update_progress, progress, f"Pausa API gratuita: {t}s...")
                    time.sleep(1)
            else:
                time.sleep(0.3)

    # ==================== PCAP ====================
    def start_loading_pcap(self):
        if self.is_loading: return
        file = filedialog.askopenfilename(filetypes=[("Wireshark PCAPNG/PCAP", "*.pcapng *.pcap"), ("Todos", "*.*")])
        if not file: return
        if not SCAPY_AVAILABLE:
            messagebox.showerror("ERRO", "Instale o Scapy:\npip install scapy")
            return
        self._reset_ui()
        threading.Thread(target=self._thread_pcap, args=(file,), daemon=True).start()

    def _thread_pcap(self, filepath):
        self.is_loading = True
        ips = set()
        try:
            packets = rdpcap(filepath)
            total = len(packets)
            for i, pkt in enumerate(packets):
                if self.stop_scan: break
                if i % 250 == 0:
                    self.root.after(0, self.update_progress, (i / max(total, 1)) * 35, f"Lendo pacotes PCAP...")
                if IP in pkt:
                    if self.is_public_ip(pkt[IP].src): ips.add(pkt[IP].src)
                    if self.is_public_ip(pkt[IP].dst): ips.add(pkt[IP].dst)
                elif IPv6 in pkt:
                    if self.is_public_ip(pkt[IPv6].src): ips.add(pkt[IPv6].src)
                    if self.is_public_ip(pkt[IPv6].dst): ips.add(pkt[IPv6].dst)
        except: pass
        
        if not self.stop_scan and ips:
            self.process_ips_with_geo({ip: os.path.basename(filepath) for ip in sorted(ips)})
        self.root.after(0, self.finish_loading)

    # ==================== ARQUIVO QUALQUER ====================
    def start_loading_any_file(self):
        if self.is_loading: return
        file = filedialog.askopenfilename(filetypes=[("Todos", "*.*")])
        if file:
            self._reset_ui()
            threading.Thread(target=self._thread_file, args=(file,), daemon=True).start()

    def _thread_file(self, filepath):
        self.is_loading = True
        fname = os.path.basename(filepath)
        ips, domains = self.scan_file_full(filepath)
        ip_map = {ip: fname for ip in ips}

        dom_list = sorted(domains)
        for j, dom in enumerate(dom_list):
            if self.stop_scan: break
            self.root.after(0, self.update_progress, 35 + (j / max(len(dom_list), 1)) * 5, f"Resolvendo DNS: {dom}")
            res = self.resolve_domain(dom)
            if res and res not in ip_map: ip_map[res] = f"{fname} [{dom}]"
            time.sleep(0.02)

        if not self.stop_scan and ip_map:
            self.process_ips_with_geo(ip_map)
        self.root.after(0, self.finish_loading)

    # ==================== PASTA ====================
    def start_loading_folder(self):
        if self.is_loading: return
        folder = filedialog.askdirectory()
        if folder:
            self._reset_ui()
            threading.Thread(target=self._thread_folder, args=(folder,), daemon=True).start()

    def _thread_folder(self, folder):
        self.is_loading = True
        all_files = [os.path.join(r, f) for r, d, fs in os.walk(folder) for f in fs]
        ip_map = {}
        dom_global = set()

        for idx, fp in enumerate(all_files):
            if self.stop_scan: break
            fname = os.path.basename(fp)
            self.root.after(0, self.update_progress, (idx / max(len(all_files), 1)) * 30, f"Arquivo {idx+1}/{len(all_files)}: {fname}")
            ips, doms = self.scan_file_full(fp)
            for ip in ips: ip_map.setdefault(ip, set()).add(fname)
            dom_global |= doms

        dom_list = sorted(dom_global)
        for j, dom in enumerate(dom_list):
            if self.stop_scan: break
            self.root.after(0, self.update_progress, 30 + (j / max(len(dom_list), 1)) * 10, f"DNS: {dom}")
            res = self.resolve_domain(dom)
            if res: ip_map.setdefault(res, set()).add(f"DNS:{dom}")
            time.sleep(0.02)

        if not self.stop_scan:
            ip_map_str = {ip: ", ".join(list(o)[:4]) for ip, o in ip_map.items()}
            self.process_ips_with_geo(ip_map_str)
        self.root.after(0, self.finish_loading)

    # ==================== INTERFACE ====================
    def live_filter(self, event=None):
        txt = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for row in self.data:
            if not txt or any(txt in str(item).lower() for item in row):
                self.tree.insert("", tk.END, values=row)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.on_tree_select(None)
            self.context_menu.post(event.x_root, event.y_root)

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])['values']
            self.current_ip = vals[0]
            try: self.current_lat, self.current_lon = float(vals[5]), float(vals[6])
            except: self.current_lat = self.current_lon = None

    # ==================== SITES OSINT ====================
    def _open(self, url):
        if self.current_ip: webbrowser.open(url)
    
    def open_virustotal(self): self._open(f"https://www.virustotal.com/gui/ip-address/{self.current_ip}")
    def open_bgphe(self): self._open(f"https://bgp.he.net/ip/{self.current_ip}")
    def open_whatismyip(self): self._open(f"https://whatismyip.com.br/map.php?ip={self.current_ip}")
    def open_webcheck(self): self._open(f"https://web-check.xyz/check/{self.current_ip}")
    def open_hunterhow(self): self._open(f"https://hunter.how/list?searchValue={self.current_ip}")
    def open_abuseipdb(self): self._open(f"https://www.abuseipdb.com/check/{self.current_ip}")
    def open_ipinfo(self): self._open(f"https://ipinfo.io/{self.current_ip}")
    def open_shodan(self): self._open(f"https://www.shodan.io/host/{self.current_ip}")
    def open_censys(self): self._open(f"https://search.censys.io/hosts/{self.current_ip}")
    
    def open_google_maps(self):
        if self.current_lat: webbrowser.open(f"https://www.google.com/maps/place/{self.current_lat},{self.current_lon}")
    def open_street_view(self):
        if self.current_lat: webbrowser.open(f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={self.current_lat},{self.current_lon}&heading=-45&pitch=38&fov=80")

    # ==================== EXPORTAR HTML ====================
    def export_html(self):
        if not self.data: return messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("Relatório HTML", "*.html")])
        if not path: return

        def esc(x): return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        rows = []
        for r in self.data:
            ip, tipo, pais, cid, est, lat, lon, org, orig = r
            gps = f'<a class="maps-link" href="https://www.google.com/maps/place/{lat},{lon}" target="_blank">Ver Mapa 🗺️</a>' if str(lat) not in ("-", "None", "") else "N/A"
            rows.append(f"""
                <tr>
                    <td class="ip-cell"><a href="https://www.virustotal.com/gui/ip-address/{esc(ip)}" target="_blank" style="color:#00ffff;text-decoration:none">{esc(ip)}</a></td>
                    <td>{esc(tipo)}</td><td>{esc(pais)}</td><td>{esc(cid)} / {esc(est)}</td>
                    <td>{gps}</td><td class="org-cell">{esc(org)}</td><td style="color:#aaa">{esc(orig)}</td>
                </tr>""")

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><title>Relatório OSINT GeoIP</title>
<style>
body {{ background:#0a0a0a; color:#00ff41; font-family:Consolas,monospace; padding:20px; margin:0; }}
h1 {{ text-align:center; color:#00b300; text-shadow:0 0 10px #00ff41; border-bottom:1px solid #00ff41; padding-bottom:10px; }}
table {{ width:100%; border-collapse:collapse; background:#111; box-shadow:0 0 15px rgba(0,255,65,.2); }}
th,td {{ border:1px solid #004400; padding:10px; text-align:left; }}
th {{ background:#052605; position:sticky; top:0; }}
tr:nth-child(even) {{ background:#0d0d0d; }} tr:hover {{ background:#003300; }}
.org-cell {{ color:#ffaa00; }}
.maps-link {{ color:#ff3333; text-decoration:none; font-weight:bold; }} .maps-link:hover {{ text-shadow:0 0 8px #ff3333; }}
.info {{ text-align:center; color:#888; margin-bottom:16px; }}
</style>
</head>
<body>
<h1>🌐 RELATÓRIO DE INTELIGÊNCIA — GEOIP</h1>
<div class="info">Total de IP geolocalizados: <b>{len(self.data)}</b></div>
<table>
<thead><tr><th>IP</th><th>Tipo</th><th>País</th><th>Cidade / Estado</th><th>Mapa (GPS)</th><th>Organização / Site</th><th>Origem Nome do arquivo</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<div style="margin-top:24px;text-align:center;color:#444">Gerado automaticamente por GEOIP Tool</div>
</body></html>"""

        try:
            with open(path, "w", encoding="utf-8") as f: f.write(html)
            webbrowser.open("file://" + os.path.abspath(path))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = GeoGUI(root)
    root.mainloop()
