# -*- coding: utf-8 -*-
import socket
import threading
from scapy.all import sniff, conf
from scapy.layers.inet import IP, TCP
import tkinter as tk
from tkinter import scrolledtext

class PacketSnifferApp:
    def __init__(self, master):
        self.master = master
        self.master.title("tcpdump Capturador de Pacotes")
        self.master.geometry("600x400")

        self.label = tk.Label(master, text="Digite a URL do website (ex: http://exemplo.com):")
        self.label.pack(pady=10)

        self.entry = tk.Entry(master, width=50)
        self.entry.pack(pady=5)

        self.start_button = tk.Button(master, text="Iniciar Captura", command=self.start_sniffing, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(master, text="Parar Captura", command=self.stop_sniffing, bg="#f53a3a", font=("TkDefaultFont", 11, "bold"))
        self.stop_button.pack(pady=5)

        self.output_area = scrolledtext.ScrolledText(master, width=140, height=41, state='disabled', font=("TkDefaultFont", 11, "bold"))
        self.output_area.pack(pady=10)

        self.sniffing = False

    def append_output(self, text):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.yview(tk.END)
        self.output_area.config(state='disabled')

    def packet_callback(self, pacote):
        if pacote.haslayer(IP) and pacote.haslayer(TCP):
            ip_src = pacote[IP].src
            ip_dst = pacote[IP].dst
            tcp_sport = pacote[TCP].sport
            tcp_dport = pacote[TCP].dport
            carga_util = pacote[TCP].payload

            # Exibir informações do pacote capturado com IPs alinhados
            self.append_output(f"\n[+] Pacote capturado: {ip_src}:{tcp_sport:<10}   IP: {ip_dst}:{tcp_dport}\n\n")

            # Verifica se a carga útil está presente e tenta decodificá-la
            if carga_util:
                conteudo = None
                try:
                    conteudo = bytes(carga_util).decode('utf-8', errors='strict')
                except UnicodeDecodeError:
                    try:
                        conteudo = bytes(carga_util).decode('latin-1', errors='replace')
                    except Exception as e:
                        self.append_output(f"\nErro ao decodificar a carga útil: {e}\n")

                if conteudo:
                    self.append_output(f"{conteudo}\n")
                else:
                    self.append_output("Carga útil não pôde ser decodificada.\n")
            else:
                self.append_output("\n")

    def start_sniffing(self):
        website = self.entry.get()
        if not website:
            self.append_output("Por favor, insira uma URL válida.\n")
            return

        # Resolve o IP do website
        try:
            endereco_ip = socket.gethostbyname(website.split("://")[-1])  # Extrai o domínio da URL
            self.append_output(f"Endereço IP resolvido de: {website}    IP: {endereco_ip}\n")
        except socket.gaierror:
            self.append_output(f"Erro: Não foi possível resolver a URL do website '{website}'.\n")
            return

        # Filtrar pacotes para o IP do website especificado
        filtro = f"host {endereco_ip}"
        self.append_output(f"\nCapturando pacotes para: {endereco_ip}\n\n")

        self.sniffing = True  # Atualiza o estado da captura
        threading.Thread(target=sniff, kwargs={'filter': filtro, 'prn': self.packet_callback, 'store': 0}).start()

    def stop_sniffing(self):
        if self.sniffing:
            self.append_output("\n\nCaptura de pacotes parada\n\n")
            conf.sniffing = False  # Para a captura (se aplicável, isso pode precisar de ajustes dependendo da versão do Scapy)
            self.sniffing = False

if __name__ == "__main__":
    root = tk.Tk()
    app = PacketSnifferApp(root)
    root.wm_state('zoomed')
    root.mainloop()
