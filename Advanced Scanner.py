import tkinter as tk
from tkinter import ttk
from scapy.all import ARP, Ether, srp
import requests
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cache para armazenar informações do fabricante
fabricante_cache = {}

def scan_ip(ip):
    try:
        arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
        result = srp(arp_request, timeout=1, verbose=False)[0]  # Reduzido o timeout
        hosts = []
        for sent, received in result:
            vendor = obter_fabricante(received.hwsrc)
            hosts.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "description": vendor
            })
        return hosts
    except Exception as e:
        print(f"Erro ao escanear IP {ip}: {e}")
        return []

def scan_network(ip_ranges, progress_callback):
    hosts = []
    total_ranges = len(ip_ranges)
    
    with ThreadPoolExecutor(max_workers=30) as executor:  # Aumentado o número de threads
        futures = {executor.submit(scan_ip, ip): ip for ip in ip_ranges}
        for i, future in enumerate(as_completed(futures), 1):
            hosts.extend(future.result())
            progress_callback(i, total_ranges)
    
    return hosts

def obter_fabricante(mac_address):
    if mac_address in fabricante_cache:
        return fabricante_cache[mac_address]
    
    try:
        url = f"https://api.macvendors.com/{mac_address}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            fabricante_cache[mac_address] = response.text
            return response.text
        return "Unknown"
    except Exception as e:
        print(f"Erro ao obter fabricante: {e}")
        return "Unknown"

def gerar_ip_ranges(cidr_notation):
    ip_ranges = []
    network = ipaddress.IPv4Network(cidr_notation, strict=False)
    for ip in network.hosts():
        ip_ranges.append(f"{ip}/32")
    return ip_ranges

class EttercapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Scanner")

        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        self.interfaces = tk.StringVar()
        self.interfaces.set("Ethernet")
        self.interface_combobox = ttk.Combobox(frame_top, textvariable=self.interfaces, values=self.load_interfaces())
        self.interface_combobox.pack(side=tk.LEFT, padx=5)

        self.scan_button = ttk.Button(frame_top, text="Escanear Rede", command=self.start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10, padx=10)

        self.hosts_tree = ttk.Treeview(self.root, columns=("IP", "MAC", "Description"), show="headings")
        self.hosts_tree.heading("IP", text="Endereço IP")
        self.hosts_tree.heading("MAC", text="Endereço MAC")
        self.hosts_tree.heading("Description", text="Descrição")

        self.hosts_tree.column("IP", width=250, anchor=tk.W)
        self.hosts_tree.column("MAC", width=250, anchor=tk.W)
        self.hosts_tree.column("Description", width=250, anchor=tk.W)

        self.hosts_tree.pack(pady=10, padx=10)
        self.hosts_tree.configure(height=25)

    def start_scan(self):
        self.scan_button.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.root.update_idletasks()

        cidr_notation = "192.168.0.0/24"
        ip_ranges_expanded = gerar_ip_ranges(cidr_notation)
        self.root.after(100, self.scan_network_async, ip_ranges_expanded)

    def scan_network_async(self, ip_ranges):
        def progress_callback(current, total):
            percentage = (current / total) * 100
            self.progress["value"] = percentage
            self.root.update_idletasks()
        
        hosts = scan_network(ip_ranges, progress_callback)
        for item in self.hosts_tree.get_children():
            self.hosts_tree.delete(item)
        for host in hosts:
            self.hosts_tree.insert("", tk.END, values=(host["ip"], host["mac"], host["description"]))

        self.scan_button.config(state=tk.NORMAL)

    def load_interfaces(self):
        return ['Ethernet', 'eth0', 'wlan0', 'lo', 'Wi-Fi']

if __name__ == "__main__":
    root = tk.Tk()
    app = EttercapGUI(root)
    root.mainloop()
