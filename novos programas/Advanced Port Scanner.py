import socket
from scapy.all import ARP, Ether, srp
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ipaddress
import time
from mac_vendor_lookup import MacLookup
import threading

# Função para escanear a rede e encontrar dispositivos
def scan_network(network, progress_callback):
    try:
        network_obj = ipaddress.IPv4Network(network, strict=False)
    except ValueError as e:
        print(f"Erro de rede: {e}")
        return []

    ip_list = list(network_obj.hosts())
    total_ips = len(ip_list)

    arp = ARP(pdst=str(network_obj))
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=3, verbose=0)[0]

    devices = []
    for i, (sent, received) in enumerate(result):
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
        progress_callback(int((i + 1) / total_ips * 100))
        time.sleep(0.1)  # Simula um atraso pequeno para evitar sobrecarga

    return devices

# Interface gráfica
class PortScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Port Scanner")
        root.geometry("1000x600")

        self.network_label = ttk.Label(root, text="Digite a rede (ex: 192.168.0.1/24):")
        self.network_label.pack(pady=10)

        self.network_entry = ttk.Entry(root)
        self.network_entry.pack(pady=5)
        self.network_entry.insert(0, "192.168.0.1/24")

        self.scan_button = tk.Button(
            root, 
            text="Escanear Rede", 
            command=self.start_scan, 
            bg="#23f507", 
            font=("TkDefaultFont", 11, "bold")
        )
        self.scan_button.pack(pady=10)

        # Cria um estilo personalizado para a Treeview
        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=("TkDefaultFont", 11, "bold"))

        self.tree = ttk.Treeview(root, columns=("IP", "MAC", "Fabricante"), show="headings", height=20)
        self.tree.heading("IP", text="IP Address", anchor=tk.CENTER)
        self.tree.heading("MAC", text="Endereço MAC", anchor=tk.CENTER)
        self.tree.heading("Fabricante", text="Fabricante", anchor=tk.CENTER)
        self.tree.column("IP", width=150, anchor=tk.CENTER)
        self.tree.column("MAC", width=200, anchor=tk.CENTER)
        self.tree.column("Fabricante", width=200, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

    def start_scan(self):
        self.progress['value'] = 0
        self.scan_button['state'] = 'disabled'  # Desativa o botão para evitar múltiplos cliques
        threading.Thread(target=self.run_scan).start()

    def run_scan(self):
        network = self.network_entry.get()

        def update_progress(percent):
            self.root.after(0, lambda: self.progress.configure(value=percent))

        devices = scan_network(network, update_progress)

        def update_tree():
            for item in self.tree.get_children():
                self.tree.delete(item)

            mac_lookup = MacLookup()
            for device in devices:
                ip = device['ip']
                mac = device['mac']
                try:
                    fabricante = mac_lookup.lookup(mac)
                except KeyError:
                    fabricante = "Desconhecido"
                self.tree.insert("", "end", values=(ip, mac, fabricante))
            
            self.progress['value'] = 100
            self.scan_button['state'] = 'normal'  # Reativa o botão
            messagebox.showinfo("Escaneamento Concluído", "Escaneamento da rede finalizado com sucesso!")

        self.root.after(0, update_tree)

# Execução da interface
if __name__ == "__main__":
    root = tk.Tk()
    app = PortScannerApp(root)
    root.mainloop()
