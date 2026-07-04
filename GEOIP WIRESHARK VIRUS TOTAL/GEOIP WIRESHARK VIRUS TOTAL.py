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
import ipaddress
import json
import threading
import urllib.request
import webbrowser
import time

# Scapy para ler PCAPNG
try:
    from scapy.all import rdpcap, IP, IPv6
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class GeoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GEOIP WIRESHARK VIRUS TOTAL")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")

        self.current_lat = None
        self.current_lon = None
        self.current_ip = None

        # ==================== ESTILO HACKER ====================
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0a0a0a")
        style.configure("TLabel", background="#0a0a0a", foreground="#00ff41")
        style.configure("Treeview", background="#0f0f0f", foreground="#00ff41", fieldbackground="#0f0f0f")
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="#00ff41")
        style.map("Treeview", background=[('selected', '#003300')], foreground=[('selected', '#00ff41')])

        # ==================== Frame Superior ====================
        top_frame = tk.Frame(root, bg="#0a0a0a")
        top_frame.pack(fill="x", pady=10, padx=15)

        # Botões com CORES DIFERENTES
        tk.Button(top_frame, text="ABRIR PCAPNG", command=self.start_loading_pcap, 
                  bg="#00b300", fg="#0a0a0a", font=("Consolas", 12, "bold"), width=18, activebackground="#00ff00").pack(side="left", padx=6)

        tk.Button(top_frame, text="EXPORTAR JSON", command=self.export_json, 
                  bg="#ff3300", fg="#030303", font=("Consolas", 12, "bold"), width=18, activebackground="#3399ff").pack(side="left", padx=6)

        tk.Label(top_frame, text="PESQUISAR:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold")).pack(side="left", padx=15)
        
        self.search = tk.Entry(top_frame, width=48, bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 11))
        self.search.pack(side="left", padx=5)
        self.search.bind("<KeyRelease>", self.live_filter)
        self.search.bind("<Return>", self.live_filter)

        # Botão VirusTotal
        tk.Button(top_frame, text="VIRUS TOTAL", command=self.open_virustotal, 
                  bg="#8B00FF", fg="#050505", font=("Consolas", 10, "bold"), width=14, activebackground="#4a0583").pack(side="right", padx=6)

        # Botões Google
        tk.Button(top_frame, text="📍 STREET VIEW", command=self.open_street_view, 
                  bg="#00b7ff", fg="#020202", font=("Consolas", 10, "bold"), width=14, activebackground="#0820f3").pack(side="right", padx=6)

        tk.Button(top_frame, text="🗺 GOOGLE MAPS", command=self.open_google_maps, 
                  bg="#09b875", fg="#030303", font=("Consolas", 10, "bold"), width=16, activebackground="#026423").pack(side="right", padx=6)

        # ==================== Barra de Progresso ====================
        self.progress_frame = tk.Frame(root, bg="#0a0a0a")
        self.progress_frame.pack(fill="x", pady=8, padx=15)

        self.progress_label = tk.Label(self.progress_frame, text="PROGRESSO: 0%", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11, "bold"))
        self.progress_label.pack(side="left", padx=8)

        style = ttk.Style()
        style.configure("green.Horizontal.TProgressbar", background="#00ff41", troughcolor="#1a1a1a", thickness=14)

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=748, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side="right", padx=15)

        # Treeview + Scrollbar
                # ==================== Treeview + Scrollbar (Preto + Verde Neon) ====================
        tree_frame = tk.Frame(root, bg="#0a0a0a")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Scrollbar estilo Hacker (Preto + Verde forte)
        style = ttk.Style()
        style.configure("Vertical.TScrollbar",
                       background="#00ff41",        # Verde neon principal
                       troughcolor="#111111",       # Fundo preto escuro
                       arrowcolor="#0e0d0d",        # Setas verdes
                       bordercolor="#1a1a1a",
                       lightcolor="#00ff41",
                       darkcolor="#00cc33",
                       gripcount=0)

        # Hover effect (quando mouse passa)
        style.map("Vertical.TScrollbar",
                  background=[('active', '#00ff80')])

        self.v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
        self.v_scrollbar.pack(side="right", fill="y")

        columns = ("IP", "Pais", "Cidade", "Estado", "Latitude", "Longitude")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=self.v_scrollbar.set)
        
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=175, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ==================== RODAPÉ ====================
        footer = tk.Frame(root, bg="#000000", height=60)
        footer.pack(side="bottom", fill="x")

        footer_text = (
            "COMO USAR:  "
            "1. Clique em 'ABRIR PCAPNG' → Selecione o arquivo  |  "
            "2. Aguarde o processamento  |  "
            "3. Clique em um IP na tabela → Use Google Maps, Street View ou VirusTotal    \n\n"

            "4. Digite no campo para pesquisar automaticamente"
        )

        tk.Label(footer, text=footer_text, bg="#000000", fg="#07e0f0", 
                 font=("Consolas", 10), wraplength=1250, justify="left").pack(pady=8, padx=15)

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

        if not txt:
            for row in self.data:
                self.tree.insert("", tk.END, values=row)
        else:
            for row in self.data:
                if any(txt in str(item).lower() for item in row):
                    self.tree.insert("", tk.END, values=row)

    def open_virustotal(self):
        """Abre o VirusTotal para o IP selecionado"""
        if self.current_ip:
            url = f"https://www.virustotal.com/gui/ip-address/{self.current_ip}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("AVISO", "Selecione um IP na tabela primeiro.")

    # ==================== RESTANTE DO CÓDIGO ====================
    def get_geo_info(self, ip):
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=status,message,country,city,regionName,lat,lon", timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    return [ip, data.get("country", "-"), data.get("city", "-"), data.get("regionName", "-"), data.get("lat", "-"), data.get("lon", "-")]
        except:
            pass
        return [ip, "-", "-", "-", "-", "-"]

    def extract_ips_from_pcap(self, filepath):
        ips = set()
        try:
            packets = rdpcap(filepath)
            total = len(packets)
            for i, pkt in enumerate(packets):
                if i % 300 == 0 or i == total - 1:
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
            self.root.after(0, self.update_progress, progress, f"GEOLOCALIZANDO {i+1}/{total_ips}")
            self.root.after(0, self.add_row_to_tree, row)
            if i % 8 == 0:
                time.sleep(0.6)
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
        self.current_lat = None
        self.current_lon = None

        thread = threading.Thread(target=self.load_pcap_thread, args=(file,), daemon=True)
        thread.start()

    def finish_loading(self):
        self.is_loading = False
        self.update_progress(100, "CONCLUÍDO!")
        messagebox.showinfo("SUCESSO", f"{len(self.data)} IP GEOLOCALIZADOS")

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

    def export_json(self):
        if not self.data:
            messagebox.showwarning("AVISO", "Nenhum dado para exportar.")
            return

        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file:
            return

        data_dict = [{"IP": row[0],"Pais": row[1],"Cidade": row[2],"Estado": row[3],"Latitude": row[4],"Longitude": row[5]} for row in self.data]

        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("SUCESSO", f"Arquivo salvo com sucesso!\n{file}")


if __name__ == "__main__":
    root = tk.Tk()
    GeoGUI(root)
    root.mainloop()
