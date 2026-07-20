import os
import warnings
import sys
import io

# ====================== SUPRESSÃO DE AVISOS ======================
os.environ["SCAPY_NO_WIRESHARK"] = "1"
warnings.filterwarnings("ignore")
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except:
    pass
sys.stderr = io.StringIO()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import threading
import urllib.request
import webbrowser
import time
import socket

# Scapy
try:
    from scapy.all import rdpcap, IP, IPv6
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class GeoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GEOIP - Wireshark + VirusTotal")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")

        self.current_ip = None
        self.current_lat = None
        self.current_lon = None
        self.data = []
        self.is_loading = False

        # ==================== ESTILO ====================
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0a0a0a")
        style.configure("TLabel", background="#0a0a0a", foreground="#00ff41")
        style.configure("Treeview", background="#0f0f0f", foreground="#00ff41", fieldbackground="#0f0f0f")
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="#00ff41")

        # ==================== Frame Superior ====================
        top_frame = tk.Frame(root, bg="#0a0a0a")
        top_frame.pack(fill="x", pady=10, padx=15)

        tk.Button(top_frame, text="ABRIR PCAPNG", command=self.start_loading_pcap,
                  bg="#00b300", fg="#0a0a0a", font=("Consolas", 12, "bold"), width=20).pack(side="left", padx=6)

        tk.Button(top_frame, text="EXPORTAR JSON", command=self.export_json,
                  bg="#ff3300", fg="#030303", font=("Consolas", 12, "bold"), width=20).pack(side="left", padx=6)

        tk.Label(top_frame, text="PESQUISAR:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold")).pack(side="left", padx=15)

        search_frame = tk.Frame(top_frame, bg="#0a0a0a")
        search_frame.pack(side="left", padx=5)

        self.search = tk.Entry(search_frame, width=50, bg="#1a1a1a", fg="#00ff41",
                               insertbackground="#00ff41", font=("Consolas", 11))
        self.search.pack(side="left", padx=(0, 4))
        self.search.bind("<KeyRelease>", self.live_filter)
        self.search.bind("<Return>", self.live_filter)

        tk.Button(search_frame, text="🔍", command=self.live_filter,
                  bg="#1a1a1a", fg="#00ff41", font=("Consolas", 10, "bold"), width=3).pack(side="left")

        tk.Button(top_frame, text="🗺 GOOGLE MAPS", command=self.open_google_maps,
                  bg="#09b875", fg="#030303", font=("Consolas", 10, "bold"), width=16).pack(side="right", padx=6)
        tk.Button(top_frame, text="📍 STREET VIEW", command=self.open_street_view,
                  bg="#00b7ff", fg="#020202", font=("Consolas", 10, "bold"), width=16).pack(side="right", padx=6)

        # ==================== Progresso ====================
        self.progress_frame = tk.Frame(root, bg="#0a0a0a")
        self.progress_frame.pack(fill="x", pady=8, padx=15)

        self.progress_label = tk.Label(self.progress_frame, text="PROGRESSO: 0%", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold"))
        self.progress_label.pack(side="left", padx=8)

        style.configure("green.Horizontal.TProgressbar", background="#00ff41", troughcolor="#1a1a1a", thickness=14)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=700, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side="right", padx=15)

        # ==================== Treeview + Scrollbars ====================
        tree_frame = tk.Frame(root, bg="#0a0a0a")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        columns = ("IP", "Pais", "Cidade", "Estado", "Latitude", "Longitude", "Site")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # Configuração das colunas
        self.tree.heading("IP", text="IP")
        self.tree.column("IP", width=300, minwidth=100)

        self.tree.heading("Pais", text="Pais")
        self.tree.column("Pais", width=150, minwidth=100, anchor="center")

        self.tree.heading("Cidade", text="Cidade")
        self.tree.column("Cidade", width=150, minwidth=100, anchor="center")

        self.tree.heading("Estado", text="Estado")
        self.tree.column("Estado", width=150, minwidth=100, anchor="center")

        self.tree.heading("Latitude", text="Latitude")
        self.tree.column("Latitude", width=90, minwidth=100, anchor="center")

        self.tree.heading("Longitude", text="Longitude")
        self.tree.column("Longitude", width=100, minwidth=100, anchor="center")

        self.tree.heading("Site", text="Site")
        self.tree.column("Site", width=400, minwidth=100, anchor="w", stretch=False)

        # Pack Scrollbars e Treeview (correto)
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.v_scrollbar.config(command=self.tree.yview)
        self.h_scrollbar.config(command=self.tree.xview)

        # ==================== MENU DE CONTEXTO (BOTÃO DIREITO) ====================
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#1a1a1a", fg="#00ff41",
                                    activebackground="#00b300", activeforeground="#0a0a0a", font=("Consolas", 10))

        self.context_menu.add_command(label="🛡️ VirusTotal", command=self.open_virustotal)
        self.context_menu.add_command(label="🌐 BGP.HE.NET", command=self.open_bgphe)
        self.context_menu.add_command(label="🔍 WhatIsMyIP", command=self.open_whatismyip)
        self.context_menu.add_command(label="🌍 Web-Check.xyz", command=self.open_webcheck)  # ← NOVO
        self.context_menu.add_command(label="🔎 Hunter.how", command=self.open_hunterhow)    # ← NOVO
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 AbuseIPDB", command=self.open_abuseipdb)
        self.context_menu.add_command(label="🔎 IPinfo.io", command=self.open_ipinfo)
        self.context_menu.add_command(label="👁️ Shodan", command=self.open_shodan)
        self.context_menu.add_command(label="📡 Censys", command=self.open_censys)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ==================== RODAPÉ ====================
        footer = tk.Frame(root, bg="#000000", height=60)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="Clique com o BOTÃO DIREITO sobre um IP para abrir em diversas ferramentas de inteligência.",
                 bg="#000000", fg="#07e0f0", font=("Consolas", 10), wraplength=1200, justify="left").pack(pady=10)

    # ==================== FUNÇÕES ====================
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            values = self.tree.item(item)['values']
            self.current_ip = values[0]
            try:
                self.current_lat = float(values[4])
                self.current_lon = float(values[5])
            except:
                self.current_lat = self.current_lon = None
            self.context_menu.post(event.x_root, event.y_root)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.current_ip = values[0]
            try:
                self.current_lat = float(values[4])
                self.current_lon = float(values[5])
            except:
                self.current_lat = self.current_lon = None

    def live_filter(self, event=None):
        txt = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for row in self.data:
            if not txt or any(txt in str(item).lower() for item in row):
                self.tree.insert("", tk.END, values=row)

    # ==================== GEO ====================
    def get_geo_info(self, ip):
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,city,regionName,lat,lon,org"
            with urllib.request.urlopen(url, timeout=12) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    org = data.get("org") or "Desconhecido"
                    if org in ["NA", None, ""]:
                        try:
                            org = socket.gethostbyaddr(ip)[0]
                        except:
                            org = "Não resolvido"
                    return [ip, data.get("country", "-"), data.get("city", "-"),
                            data.get("regionName", "-"), data.get("lat", "-"),
                            data.get("lon", "-"), org]
        except:
            pass
        return [ip, "-", "-", "-", "-", "-", "Não resolvido"]

    # ==================== PCAP ====================
    def extract_ips_from_pcap(self, filepath):
        ips = set()
        try:
            packets = rdpcap(filepath)
            total = len(packets)
            for i, pkt in enumerate(packets):
                if i % 250 == 0 or i == total - 1:
                    progress = (i + 1) / total * 40
                    self.root.after(0, self.update_progress, progress, f"LENDO PCAP... ({i+1}/{total})")
                
                if IP in pkt:
                    ips.add(pkt[IP].src)
                    ips.add(pkt[IP].dst)
                elif IPv6 in pkt:
                    ips.add(pkt[IPv6].src)
                    ips.add(pkt[IPv6].dst)
            return sorted(list(ips))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("ERRO", f"Erro ao ler PCAP:\n{str(e)}"))
            return []

    def process_ips_with_geo(self, ips):
        for i, ip in enumerate(ips):
            row = self.get_geo_info(ip)
            self.data.append(row)
            progress = 40 + (i + 1) / len(ips) * 60
            self.root.after(0, self.update_progress, progress, f"Consultando {i+1}/{len(ips)}")
            self.root.after(0, lambda r=row: self.tree.insert("", tk.END, values=r))
            if i % 8 == 0:
                time.sleep(0.25)

    def update_progress(self, value, text=""):
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"PROGRESSO: {int(value)}% {text}")
        self.root.update_idletasks()

    def load_pcap_thread(self, filepath):
        self.is_loading = True
        self.update_progress(0, "INICIANDO...")
        ips = self.extract_ips_from_pcap(filepath)
        if ips:
            self.process_ips_with_geo(ips)
        self.root.after(0, self.finish_loading)

    def start_loading_pcap(self):
        if self.is_loading:
            messagebox.showinfo("AGUARDE", "Processamento em andamento...")
            return

        file = filedialog.askopenfilename(
            filetypes=[("Wireshark PCAPNG/PCAP", "*.pcapng *.pcap"), ("Todos", "*.*")]
        )
        if not file:
            return

        if not SCAPY_AVAILABLE:
            messagebox.showerror("ERRO", "Instale o Scapy:\npip install scapy")
            return

        self.tree.delete(*self.tree.get_children())
        self.data.clear()

        threading.Thread(target=self.load_pcap_thread, args=(file,), daemon=True).start()

    def finish_loading(self):
        self.is_loading = False
        self.update_progress(100, "CONCLUÍDO")
        messagebox.showinfo("SUCESSO", f"{len(self.data)} IP Processados")

    # ==================== ABRIR SITES ====================
    def open_webcheck(self):
        if self.current_ip:
            webbrowser.open(f"https://web-check.xyz/check/{self.current_ip}")
        else:
            messagebox.showwarning("Aviso", "Selecione um IP primeiro.")

    def open_hunterhow(self):
        if self.current_ip:
            webbrowser.open(f"https://hunter.how/list?searchValue={self.current_ip}")
        else:
            messagebox.showwarning("Aviso", "Selecione um IP primeiro.")        

    def open_virustotal(self):
        if self.current_ip: webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{self.current_ip}")

    def open_bgphe(self):
        if self.current_ip: webbrowser.open(f"https://bgp.he.net/ip/{self.current_ip}")

    def open_whatismyip(self):
        if self.current_ip: webbrowser.open(f"https://whatismyip.com.br/map.php?ip={self.current_ip}")

    def open_abuseipdb(self):
        if self.current_ip: webbrowser.open(f"https://www.abuseipdb.com/check/{self.current_ip}")

    def open_ipinfo(self):
        if self.current_ip: webbrowser.open(f"https://ipinfo.io/{self.current_ip}")

    def open_shodan(self):
        if self.current_ip: webbrowser.open(f"https://www.shodan.io/host/{self.current_ip}")

    def open_censys(self):
        if self.current_ip: webbrowser.open(f"https://search.censys.io/hosts/{self.current_ip}")

    def open_google_maps(self):
        if self.current_lat is not None and self.current_lon is not None:
            webbrowser.open(f"https://www.google.com/maps/place/{self.current_lat},{self.current_lon}")
        else:
            messagebox.showwarning("Aviso", "Selecione um IP com localização válida.")

    def open_street_view(self):
        if self.current_lat is not None and self.current_lon is not None:
            url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={self.current_lat},{self.current_lon}&heading=-45&pitch=38&fov=80"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Aviso", "Selecione um IP com localização válida.")

    def export_json(self):
        if not self.data:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file:
            data_dict = [{"IP": r[0], "Pais": r[1], "Cidade": r[2], "Estado": r[3],
                          "Latitude": r[4], "Longitude": r[5], "Site": r[6]} for r in self.data]
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{file}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GeoGUI(root)
    root.mainloop()
