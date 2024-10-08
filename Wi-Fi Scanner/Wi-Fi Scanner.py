import time
from mac_vendor_lookup import MacLookup
from pywifi import PyWiFi, const
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

class WifiScannerApp:
    def __init__(self, master):
        self.master = master
        master.title("Wi-Fi Scanner")

        self.label = tk.Label(master, text="Resultados da Varredura Wi-Fi", font=("Arial", 16))
        self.label.pack(pady=10)

        self.scan_button = tk.Button(master, text="Iniciar Varredura", command=self.scan_wifi, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
        self.scan_button.pack(pady=5)

        self.save_button = tk.Button(master, text="Salvar Resultados", command=self.save_results, font=("TkDefaultFont", 11, "bold"), bg='#0099ff')
        self.save_button.pack(pady=5)

        self.quit_button = tk.Button(master, text="Sair", command=master.quit, font=("TkDefaultFont", 11, "bold"), bg='#fc036f')
        self.quit_button.pack(pady=5)

        self.text_area = scrolledtext.ScrolledText(master, width=150, height=46)
        self.text_area.pack(pady=10)

        self.mac_lookup = MacLookup()
        self.mac_lookup.update_vendors()  # Atualizando a base de dados de fabricantes

    def scan_wifi(self):
        self.text_area.delete(1.0, tk.END)  # Limpa a área de texto
        self.text_area.insert(tk.END, "Iniciando a varredura...\n")
        self.master.update()  # Atualiza a interface

        wifi = PyWiFi()
        iface = wifi.interfaces()[0]  # Interface Wi-Fi
        iface.scan()  # Inicia a varredura
        time.sleep(5)  # Aguarda a conclusão da varredura

        networks = iface.scan_results()
        count = self.print_networks(networks)

        self.text_area.insert(tk.END, f"\n\nTotal de redes Wi-Fi encontradas: {count}\n")

    def print_networks(self, networks):
        seen_ssids = set()  # Conjunto para armazenar SSIDs já vistos
        count = 0  # Contador de redes Wi-Fi
        
        for network in networks:
            ssid = network.ssid.strip()
            if ssid == "":
                ssid = "<Rede Oculta>"  # Se o SSID estiver vazio, marca como rede oculta
            
            bssid = network.bssid.rstrip(":")  # Remove ':' do final, se houver
            if (ssid, bssid) not in seen_ssids:  # Verifica se o SSID + BSSID já foram processados
                seen_ssids.add((ssid, bssid))  # Adiciona o SSID + BSSID ao conjunto
                
                # Identificar o tipo de segurança
                if const.AKM_TYPE_WPA2PSK in network.akm:
                    security = "WPA2"
                elif const.AKM_TYPE_WPA in network.akm:
                    security = "WPA"
                else:
                    security = "Aberto"  # Considera redes abertas como padrão               
                
                # Obter o nome do fabricante do BSSID
                try:
                    vendor_name = self.mac_lookup.lookup(bssid)
                except KeyError:
                    vendor_name = "Desconhecido"
                
                signal_strength = network.signal  # Obtém a força do sinal em dBm

                # Classifica a força do sinal
                if signal_strength >= -50:
                    signal_quality = "Forte"
                elif -70 <= signal_strength < -50:
                    signal_quality = "Médio"
                else:
                    signal_quality = "Fraco"
                
                # Exibe os detalhes da rede
                self.text_area.insert(tk.END, 
                    f"\nSSID: {ssid:<18} MAC: {bssid:<20} Fabri: {vendor_name:<35} Sinal: {signal_strength} dBm ({signal_quality}) Segury: {security}\n")
                count += 1  # Incrementa o contador de redes Wi-Fi
        return count

    def save_results(self):
        # Abre um diálogo para escolher o local e o nome do arquivo
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                   filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:  # Se um caminho foi selecionado
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END))  # Escreve o conteúdo da área de texto no arquivo
                messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = WifiScannerApp(root)
    root.mainloop()
