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
        self.root.title("GEOIP WIRESHARK VIRUS TOTAL WEBSITE")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")

        self.current_lat = None
        self.current_lon = None
        self.current_ip = None

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
                  bg="#00b300", fg="#0a0a0a", font=("Consolas", 12, "bold"), width=18).pack(side="left", padx=6)

        tk.Button(top_frame, text="EXPORTAR JSON", command=self.export_json, 
                  bg="#ff3300", fg="#030303", font=("Consolas", 12, "bold"), width=18).pack(side="left", padx=6)

        tk.Label(top_frame, text="PESQUISAR:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold")).pack(side="left", padx=15)
        
        self.search = tk.Entry(top_frame, width=48, bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 11))
        self.search.pack(side="left", padx=5)
        self.search.bind("<KeyRelease>", self.live_filter)

        tk.Button(top_frame, text="VIRUS TOTAL", command=self.open_virustotal, 
                  bg="#8B00FF", fg="#050505", font=("Consolas", 10, "bold"), width=14).pack(side="right", padx=6)

        tk.Button(top_frame, text="📍 STREET VIEW", command=self.open_street_view, 
                  bg="#00b7ff", fg="#020202", font=("Consolas", 10, "bold"), width=14).pack(side="right", padx=6)

        tk.Button(top_frame, text="🗺 GOOGLE MAPS", command=self.open_google_maps, 
                  bg="#09b875", fg="#030303", font=("Consolas", 10, "bold"), width=16).pack(side="right", padx=6)

        # ==================== Progresso ====================
        self.progress_frame = tk.Frame(root, bg="#0a0a0a")
        self.progress_frame.pack(fill="x", pady=8, padx=15)

        self.progress_label = tk.Label(self.progress_frame, text="PROGRESSO: 0%", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold"))
        self.progress_label.pack(side="left", padx=8)

        style.configure("green.Horizontal.TProgressbar", background="#00ff41", troughcolor="#1a1a1a", thickness=14)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=748, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side="right", padx=15)

        # ==================== Treeview ====================
        tree_frame = tk.Frame(root, bg="#0a0a0a")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.v_scrollbar.pack(side="right", fill="y")

        columns = ("IP", "Pais", "Cidade", "Estado", "Latitude", "Longitude", "Site")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=self.v_scrollbar.set)
        
        # Configuração das colunas
        self.tree.heading("IP", text="IP")
        self.tree.column("IP", width=155, minwidth=100, anchor="center")

        self.tree.heading("Pais", text="Pais")
        self.tree.column("Pais", width=110, minwidth=80, anchor="center")

        self.tree.heading("Cidade", text="Cidade")
        self.tree.column("Cidade", width=135, minwidth=100, anchor="center")

        self.tree.heading("Estado", text="Estado")
        self.tree.column("Estado", width=125, minwidth=90, anchor="center")

        self.tree.heading("Latitude", text="Latitude")
        self.tree.column("Latitude", width=90, minwidth=70, anchor="center")

        self.tree.heading("Longitude", text="Longitude")
        self.tree.column("Longitude", width=100, minwidth=80, anchor="center")

        # Coluna Site - Mais larga e com stretch
        self.tree.heading("Site", text="Site")
        self.tree.column("Site", width=330, minwidth=350, anchor="w", stretch=True)

        self.tree.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # RODAPÉ
        footer = tk.Frame(root, bg="#000000", height=60)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="Site obtido automaticamente via API ip-api.com", 
                 bg="#000000", fg="#07e0f0", font=("Consolas", 10), wraplength=1250, justify="left").pack(pady=8, padx=15)

        self.data = []
        self.is_loading = False

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.current_ip = values[0]
            try:
                self.current_lat = float(values[4])
                self.current_lon = float(values[5])
            except:
                self.current_lat = None
                self.current_lon = None

    def live_filter(self, event=None):
        txt = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for row in self.data:
            if not txt or any(txt in str(item).lower() for item in row):
                self.tree.insert("", tk.END, values=row)

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None

    def get_geo_info(self, ip):
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,city,regionName,lat,lon,org"
            with urllib.request.urlopen(url, timeout=12) as response:
                data = json.loads(response.read().decode())
                
                if data.get("status") == "success":
                    org = data.get("org", "Desconhecido")
                    if org == "NA" or not org:
                        hostname = self.get_hostname(ip)
                        site = hostname if hostname else "Não resolvido"
                    else:
                        site = org
                    
                    return [
                        ip,
                        data.get("country", "-"),
                        data.get("city", "-"),
                        data.get("regionName", "-"),
                        data.get("lat", "-"),
                        data.get("lon", "-"),
                        site
                    ]
        except:
            pass
        return [ip, "-", "-", "-", "-", "-", "Não resolvido"]

    # ==================== Restante do código ====================
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
        total_ips = len(ips)
        processed = []
        for i, ip in enumerate(ips):
            row = self.get_geo_info(ip)
            processed.append(row)
            progress = 40 + (i + 1) / total_ips * 60
            self.root.after(0, self.update_progress, progress, f"Consultando API {i+1}/{total_ips}")
            self.root.after(0, self.add_row_to_tree, row)
            if i % 8 == 0:
                time.sleep(0.4)
        return processed

    def add_row_to_tree(self, row):
        self.tree.insert("", tk.END, values=row)

    def update_progress(self, value, text=""):
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"PROGRESSO: {int(value)}% {text}")
        self.root.update_idletasks()

    def load_pcap_thread(self, filepath):
        self.is_loading = True
        self.update_progress(0, "INICIANDO...")
        ips = self.extract_ips_from_pcap(filepath)
        if ips:
            self.data = self.process_ips_with_geo(ips)
        self.root.after(0, self.finish_loading)

    def start_loading_pcap(self):
        if self.is_loading:
            messagebox.showinfo("AGUARDE", "Processamento em andamento...")
            return

        file = filedialog.askopenfilename(filetypes=[("Wireshark PCAPNG", "*.pcapng"), ("PCAP", "*.pcap"), ("Todos", "*.*")])
        if not file:
            return

        if not SCAPY_AVAILABLE:
            messagebox.showerror("ERRO", "Instale o Scapy:\npip install scapy")
            return

        self.tree.delete(*self.tree.get_children())
        self.data = []

        thread = threading.Thread(target=self.load_pcap_thread, args=(file,), daemon=True)
        thread.start()

    def finish_loading(self):
        self.is_loading = False
        self.update_progress(100, "CONCLUÍDO!")
        messagebox.showinfo("SUCESSO", f"{len(self.data)} IPs processados")

    def open_google_maps(self):
        if self.current_lat is not None and self.current_lon is not None:
            url = f"https://www.google.com/maps/place/{self.current_lat},{self.current_lon}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("AVISO", "Selecione um IP com localização válida.")

    def open_street_view(self):
        if self.current_lat is not None and self.current_lon is not None:
            url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={self.current_lat},{self.current_lon}&heading=-45&pitch=38&fov=80"
            webbrowser.open(url)
        else:
            messagebox.showwarning("AVISO", "Selecione um IP com localização válida.")

    def open_virustotal(self):
        if self.current_ip:
            url = f"https://www.virustotal.com/gui/ip-address/{self.current_ip}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("AVISO", "Selecione um IP na tabela primeiro.")

    def export_json(self):
        if not self.data:
            messagebox.showwarning("AVISO", "Nenhum dado para exportar.")
            return

        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file:
            return

        data_dict = [{"IP": row[0], "Pais": row[1], "Cidade": row[2], "Estado": row[3],
                      "Latitude": row[4], "Longitude": row[5], "Site": row[6]} for row in self.data]

        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("SUCESSO", f"Arquivo salvo!\n{file}")


if __name__ == "__main__":
    root = tk.Tk()
    GeoGUI(root)
    root.mainloop()
