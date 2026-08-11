#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARP Table Viewer - Hacker Style
Detecta ARP Spoofing: mesmo MAC com IP diferentes
"""

import subprocess
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from collections import defaultdict
import platform
from datetime import datetime
import html
import platform

# Cores estilo hacker
BG_COLOR = "#0a0a0a"
FG_GREEN = "#00ff41"
FG_ORANGE = "#ff8c00"
FG_RED = "#ff0033"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
FONT = ("Consolas", 11)
FONT_BOLD = ("Consolas", 11, "bold")
FONT_TITLE = ("Consolas", 16, "bold")

class ARPViewer(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("ARP Scanner // Spoofing Detector")
        self.geometry("950x620")
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)

        # Maximiza no Windows 10 e no Kali Linux
        if platform.system() == "Windows":
            self.state("zoomed")
        elif platform.system() == "Linux":
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                # Fallback caso o gerenciador de janelas não suporte -zoomed
                self.update_idletasks()
                self.state("normal")

        # Guarda o último scan para exportação HTML
        self.last_entries = []
        self.last_spoof_macs = set()
        self.last_conflict_ips = set()
        self.last_mac_to_ips = {}
        self.last_raw = ""
        self.last_has_spoof = False
        self.last_has_conflict = False

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_GREEN, font=FONT)
        style.configure("TButton", background="#111111", foreground=FG_GREEN,
                        font=FONT_BOLD, borderwidth=1, relief="flat")
        style.map("TButton",
                  background=[("active", "#1a1a1a")],
                  foreground=[("active", FG_CYAN)])

        self.create_widgets()
        self.scan_arp()

    def create_widgets(self):
        title = tk.Label(self, text="╔════════════════════════════════════════════╗\n"
                                      "║   ARP SPOOFING DETECTOR // HACKER MODE     ║\n"
                                      "╚════════════════════════════════════════════╝",
                         bg=BG_COLOR, fg=FG_GREEN, font=FONT_TITLE, justify="center")
        title.pack(pady=10)

        self.info_label = tk.Label(self, text="Carregando tabela ARP...",
                                   bg=BG_COLOR, fg=FG_CYAN, font=FONT)
        self.info_label.pack()

        self.text_area = scrolledtext.ScrolledText(
            self,
            bg="#050505",
            fg=FG_GREEN,
            insertbackground=FG_GREEN,
            font=FONT,
            wrap=tk.NONE,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=FG_GREEN,
            highlightcolor=FG_GREEN
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Tags de cor
        self.text_area.tag_configure("header", foreground=FG_CYAN, font=FONT_BOLD)
        self.text_area.tag_configure("normal", foreground=FG_GREEN)
        self.text_area.tag_configure("spoof", foreground=FG_ORANGE, font=FONT_BOLD)
        self.text_area.tag_configure("conflict", foreground=FG_YELLOW, font=FONT_BOLD)
        self.text_area.tag_configure("warning", foreground=FG_RED, font=FONT_BOLD)
        self.text_area.tag_configure("ok", foreground=FG_GREEN)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="[ RE-SCAN ]", command=self.scan_arp).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="[ SALVAR HTML ]", command=self.save_html).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="[ LIMPAR ]", command=self.clear_text).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="[ SAIR ]", command=self.destroy).pack(side=tk.LEFT, padx=8)

        footer = tk.Label(self, text=">> Mesmo MAC com IP diferentes = possível ARP Spoofing <<",
                          bg=BG_COLOR, fg="#555555", font=("Consolas", 9))
        footer.pack(pady=5)

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)

    def get_arp_table(self):
        system = platform.system().lower()
        try:
            if system == "windows":
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True,
                                        encoding="cp850", errors="ignore")
            else:
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True,
                                        encoding="utf-8", errors="ignore")
            return result.stdout
        except Exception as e:
            return f"ERRO ao executar arp -a: {e}"

    def parse_arp(self, raw):
        entries = []
        patterns = [
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?((?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})',
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+((?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2})',
        ]

        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            for pat in patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).lower().replace("-", ":")
                    if mac in ("ff:ff:ff:ff:ff:ff", "00:00:00:00:00:00"):
                        continue
                    entries.append((ip, mac, line))
                    break
        return entries

    def analyze(self, entries):
        """
        Retorna:
        - spoof_macs: MACs que aparecem com mais de 1 IP diferente (ARP Spoofing)
        - conflict_ips: IP que aparecem com mais de 1 MAC diferente (conflito de IP)
        """
        mac_to_ips = defaultdict(set)
        ip_to_macs = defaultdict(set)

        for ip, mac, _ in entries:
            mac_to_ips[mac].add(ip)
            ip_to_macs[ip].add(mac)

        spoof_macs = {mac for mac, ips in mac_to_ips.items() if len(ips) > 1}
        conflict_ips = {ip for ip, macs in ip_to_macs.items() if len(macs) > 1}

        return spoof_macs, conflict_ips, mac_to_ips

    def scan_arp(self):
        self.clear_text()
        self.info_label.config(text=">> Escaneando tabela ARP...", fg=FG_CYAN)
        self.update()

        raw = self.get_arp_table()
        entries = self.parse_arp(raw)

        if not entries:
            self.text_area.insert(tk.END, "[!] Nenhuma entrada ARP encontrada.\n", "warning")
            self.text_area.insert(tk.END, "\nSaída bruta:\n", "header")
            self.text_area.insert(tk.END, raw, "normal")
            self.info_label.config(text=">> Nenhuma entrada válida", fg=FG_RED)
            self.last_entries = []
            self.last_raw = raw
            return

        spoof_macs, conflict_ips, mac_to_ips = self.analyze(entries)

        # Guarda para exportação HTML
        self.last_entries = entries
        self.last_spoof_macs = spoof_macs
        self.last_conflict_ips = conflict_ips
        self.last_mac_to_ips = mac_to_ips
        self.last_raw = raw

        # Cabeçalho
        self.text_area.insert(tk.END, f"{'IP':<18} {'MAC Address':<20} STATUS\n", "header")
        self.text_area.insert(tk.END, "-" * 60 + "\n", "header")

        has_spoof = False
        has_conflict = False

        for ip, mac, _ in entries:
            if mac in spoof_macs:
                status = "⚠ ARP SPOOFING"
                tag = "spoof"
                has_spoof = True
            elif ip in conflict_ips:
                status = "⚡ CONFLITO IP"
                tag = "conflict"
                has_conflict = True
            else:
                status = "OK"
                tag = "normal"

            line = f"{ip:<18} {mac:<20} {status}\n"
            self.text_area.insert(tk.END, line, tag)

        self.last_has_spoof = has_spoof
        self.last_has_conflict = has_conflict

        # Resumo detalhado
        self.text_area.insert(tk.END, "\n" + "=" * 60 + "\n", "header")
        self.text_area.insert(tk.END, f"Total de Entradas : {len(entries)}\n", "ok")

        if spoof_macs:
            self.text_area.insert(tk.END, "\n[!] POSSÍVEL ARP SPOOFING DETECTADO\n\n", "spoof")
            for mac in sorted(spoof_macs):
                ips = sorted(mac_to_ips[mac])
                self.text_area.insert(tk.END, f"   MAC {mac} → IP: {', '.join(ips)}\n", "spoof")

        if conflict_ips:
            self.text_area.insert(tk.END, "\n[!] Conflito de IP (mesmo IP com MAC diferentes):\n", "conflict")
            for ip in sorted(conflict_ips):
                self.text_area.insert(tk.END, f"   IP {ip}\n", "conflict")

        if not has_spoof and not has_conflict:
            self.text_area.insert(tk.END, "\nNenhuma Anomalia Encontrada\n", "ok")
            self.info_label.config(text=">> Tabela limpa — nenhum spoofing detectado", fg=FG_GREEN)
        elif has_spoof:
            self.info_label.config(text=">> ATENÇÃO: Possível ARP Spoofing (mesmo MAC com IP diferentes)", fg=FG_ORANGE)
        else:
            self.info_label.config(text=">> Conflito de IP detectado", fg=FG_YELLOW)

        # Saída original
        self.text_area.insert(tk.END, "\n[ SAÍDA ORIGINAL DO ARP -A ]\n", "header")
        self.text_area.insert(tk.END, raw + "\n", "normal")

    def save_html(self):
        """Exporta o resultado do último scan para HTML colorido (estilo hacker)."""
        if not self.last_entries and not self.last_raw:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.\nFaça um scan primeiro.")
            return

        default_name = f"arp_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=default_name,
            title="Salvar resultados ARP em HTML"
        )
        if not filepath:
            return

        try:
            html_content = self._build_html()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar HTML:\n{e}")

    def _build_html(self):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        entries = self.last_entries
        spoof_macs = self.last_spoof_macs
        conflict_ips = self.last_conflict_ips
        mac_to_ips = self.last_mac_to_ips
        raw = self.last_raw
        has_spoof = self.last_has_spoof
        has_conflict = self.last_has_conflict

        # Monta linhas da tabela
        rows = []
        for ip, mac, _ in entries:
            if mac in spoof_macs:
                status = "⚠ ARP SPOOFING"
                css_class = "spoof"
            elif ip in conflict_ips:
                status = "⚡ CONFLITO IP"
                css_class = "conflict"
            else:
                status = "OK"
                css_class = "ok"
            rows.append(
                f'<tr class="{css_class}">'
                f'<td>{html.escape(ip)}</td>'
                f'<td>{html.escape(mac)}</td>'
                f'<td>{html.escape(status)}</td>'
                f'</tr>'
            )
        rows_html = "\n".join(rows) if rows else '<tr><td colspan="3" class="warning">Nenhuma entrada ARP encontrada.</td></tr>'

        # Resumo de spoofing
        spoof_section = ""
        if spoof_macs:
            items = []
            for mac in sorted(spoof_macs):
                ips = sorted(mac_to_ips.get(mac, []))
                items.append(f"<li><strong>MAC {html.escape(mac)}</strong> → IP: {html.escape(', '.join(ips))}</li>")
            spoof_section = f"""
            <div class="alert spoof-alert">
                <h2>[!] POSSÍVEL ARP SPOOFING DETECTADO</h2>
                <ul>
                    {''.join(items)}
                </ul>
            </div>
            """

        # Resumo de conflitos
        conflict_section = ""
        if conflict_ips:
            items = [f"<li>IP {html.escape(ip)}</li>" for ip in sorted(conflict_ips)]
            conflict_section = f"""
            <div class="alert conflict-alert">
                <h2>[!] Conflito de IP (mesmo IP com MACs diferentes)</h2>
                <ul>
                    {''.join(items)}
                </ul>
            </div>
            """

        # Status geral
        if not has_spoof and not has_conflict and entries:
            status_msg = '<p class="status-ok">Nenhuma anomalia Encontrada Tabela limpa</p>'
        elif has_spoof:
            status_msg = '<p class="status-spoof">ATENÇÃO: Possível ARP Spoofing detectado (mesmo MAC com IPs diferentes).</p>'
        elif has_conflict:
            status_msg = '<p class="status-conflict">Conflito de IP detectado.</p>'
        else:
            status_msg = '<p class="status-warning">Nenhuma entrada válida encontrada.</p>'

        raw_escaped = html.escape(raw) if raw else "(vazio)"

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARP Spoofing Detector — Relatório</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #0a0a0a;
        color: #00ff41;
        font-family: 'Consolas', 'Courier New', monospace;
        padding: 30px 20px;
        line-height: 1.5;
    }}
    .container {{
        max-width: 960px;
        margin: 0 auto;
        border: 1px solid #00ff41;
        padding: 25px;
        background: #050505;
        box-shadow: 0 0 25px rgba(0, 255, 65, 0.15);
    }}
    h1 {{
        text-align: center;
        color: #00ff41;
        font-size: 1.4rem;
        margin-bottom: 8px;
        letter-spacing: 1px;
    }}
    .subtitle {{
        text-align: center;
        color: #00ffff;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }}
    .meta {{
        text-align: center;
        color: #555;
        font-size: 0.85rem;
        margin-bottom: 25px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 0.95rem;
    }}
    th {{
        background: #111;
        color: #00ffff;
        padding: 10px 12px;
        text-align: left;
        border-bottom: 2px solid #00ff41;
    }}
    td {{
        padding: 8px 12px;
        border-bottom: 1px solid #1a1a1a;
    }}
    tr.ok td {{ color: #00ff41; }}
    tr.spoof td {{ color: #ff8c00; font-weight: bold; }}
    tr.conflict td {{ color: #ffff00; font-weight: bold; }}
    tr:hover {{ background: #0f0f0f; }}
    .summary {{
        margin: 20px 0;
        padding: 12px;
        border: 1px solid #222;
        background: #0d0d0d;
    }}
    .summary strong {{ color: #00ffff; }}
    .alert {{
        margin: 18px 0;
        padding: 15px;
        border-left: 4px solid;
    }}
    .spoof-alert {{
        border-color: #ff8c00;
        background: rgba(255, 140, 0, 0.08);
        color: #ff8c00;
    }}
    .conflict-alert {{
        border-color: #ffff00;
        background: rgba(255, 255, 0, 0.07);
        color: #ffff00;
    }}
    .alert h2 {{
        font-size: 1.05rem;
        margin-bottom: 10px;
    }}
    .alert ul {{
        margin-left: 20px;
    }}
    .status-ok {{ color: #00ff41; margin: 15px 0; }}
    .status-spoof {{ color: #ff8c00; font-weight: bold; margin: 15px 0; }}
    .status-conflict {{ color: #ffff00; font-weight: bold; margin: 15px 0; }}
    .status-warning {{ color: #ff0033; margin: 15px 0; }}
    .raw-section {{
        margin-top: 30px;
        border-top: 1px solid #222;
        padding-top: 20px;
    }}
    .raw-section h2 {{
        color: #00ffff;
        font-size: 1rem;
        margin-bottom: 10px;
    }}
    pre {{
        background: #080808;
        border: 1px solid #1a1a1a;
        padding: 15px;
        overflow-x: auto;
        color: #00ff41;
        font-size: 0.85rem;
        white-space: pre-wrap;
        word-break: break-all;
    }}
    footer {{
        text-align: center;
        margin-top: 25px;
        color: #444;
        font-size: 0.8rem;
    }}
</style>
</head>
<body>
<div class="container">
    <h1>╔════════════════════════════════════════════╗<br>
        ║     ARP SPOOFING DETECTOR // HACKER MODE   ║<br>
        ╚════════════════════════════════════════════╝</h1>
    <p class="subtitle">Relatório de varredura da tabela ARP</p>
    <p class="meta">Gerado em: {now}</p>

    {status_msg}

    <div class="summary">
        <strong>Total de entradas:</strong> {len(entries)}
    </div>

    <table>
        <thead>
            <tr>
                <th>IP</th>
                <th>MAC Address</th>
                <th>STATUS</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    {spoof_section}
    {conflict_section}

    <div class="raw-section">
        <h2>[ SAÍDA ORIGINAL DO ARP -A ]</h2>
        <pre>{raw_escaped}</pre>
    </div>

    <footer>
        &gt;&gt; Mesmo MAC com IP diferentes = possível ARP Spoofing &lt;&lt;<br>
        ARP Scanner // Spoofing Detector
    </footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    app = ARPViewer()
    app.mainloop()
