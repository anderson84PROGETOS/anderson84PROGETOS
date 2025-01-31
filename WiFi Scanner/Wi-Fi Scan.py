import time
from mac_vendor_lookup import MacLookup
from pywifi import PyWiFi, const
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

class WifiScannerApp:
    def __init__(self, master):
        self.master = master
        master.title("Wi-Fi Scan")

        self.label = tk.Label(master, text="Resultados da Varredura Wi-Fi", font=("Arial", 16))
        self.label.pack(pady=10)

        self.scan_button = tk.Button(master, text="Iniciar Varredura", command=self.scan_wifi, font=("TkDefaultFont", 11, "bold"), bg='#1ff507')
        self.scan_button.pack(pady=5)

        self.save_button = tk.Button(master, text="Salvar Resultados", command=self.save_results, font=("TkDefaultFont", 11, "bold"), bg='#f5c107')
        self.save_button.pack(pady=5)

        self.quit_button = tk.Button(master, text="Sair", command=master.quit, font=("TkDefaultFont", 11, "bold"), bg='#fc036f')
        self.quit_button.pack(pady=5)

        self.text_area = scrolledtext.ScrolledText(master, width=153, height=46)
        self.text_area.pack(pady=10)

        self.mac_lookup = MacLookup()
        self.mac_lookup.update_vendors()

    def scan_wifi(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Para saber o nome do Fabricante, acesse o website: https://macvendors.com\n\n")        
        self.text_area.insert(tk.END, "\nSSID                                 BSSID Endereço MAC                  Fabricante                                      Sinal      dBm      \n=================================================================================================================================================\n")
        
        self.master.update()

        wifi = PyWiFi()
        iface = wifi.interfaces()[0]
        iface.scan()
        time.sleep(5)

        networks = iface.scan_results()
        count = self.print_networks(networks)

        self.text_area.insert(tk.END, f"\n\nTotal de redes Wi-Fi encontradas: {count}\n")

    def get_signal_quality(self, signal_strength):
        if signal_strength > -50:
            return "Forte"
        elif -70 < signal_strength <= -50:
            return "Moderado"
        else:
            return "Fraco"

    def print_networks(self, networks):
        seen_ssids = set()
        count = 0
        
        for network in networks:
            ssid = network.ssid.strip() or "<Rede Oculta>"
            bssid = network.bssid.rstrip(":")
            signal_strength = network.signal
            signal_quality = self.get_signal_quality(signal_strength)

            if (ssid, bssid) not in seen_ssids:
                seen_ssids.add((ssid, bssid))
                
                try:
                    vendor_name = self.mac_lookup.lookup(bssid)
                except KeyError:
                    vendor_name = "Desconhecido"
                
                self.text_area.insert(tk.END, 
                    f"\nSSID: {ssid:<30} MAC: {bssid:<30} Fabri: {vendor_name:<40} "
                    f"Sinal: {signal_strength} dBm ({signal_quality})\n")
                count += 1
        return count

    def save_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END))
                messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = WifiScannerApp(root)
    root.mainloop()
