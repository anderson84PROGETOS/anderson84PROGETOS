# Nome do arquivo: web_capture_total.py
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, END
import threading
import time
import json
import os
import random
import socket
from urllib.parse import urlparse
import re

from scapy.all import IP, TCP, Raw, wrpcap, sniff
from scapy.layers.http import HTTPRequest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class WebCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Capture Total")
        self.root.geometry("1140x860")

        self.driver = None
        self.is_capturing = False
        self.captured_data_browser = []
        self.captured_packets_network = []

        self.stop_sniff_event = threading.Event()
        self.setup_ui()
        self.setup_selenium()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Label(frame, text="Digite a URL").grid(row=0, column=0)
        self.url_entry = tk.Entry(frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=10)

        tk.Button(frame, text="Abrir Navegador", command=self.open_browser, bg="#03fcf4").grid(row=0, column=2)
        tk.Button(frame, text="Iniciar Captura Total", command=self.start_capture_all, bg="#1cfc03").grid(row=1, column=0, pady=5)
        tk.Button(frame, text="Parar Captura", command=self.stop_capture_all, bg="#fc0317").grid(row=1, column=1)
        tk.Button(frame, text="Salvar Tudo em PCAPNG", command=self.save_all_pcapng, bg="#fce303").grid(row=1, column=2)

        self.log_area = scrolledtext.ScrolledText(self.root, width=130, height=45)
        self.log_area.pack(pady=10)

    def setup_selenium(self):
        try:
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            service = Service(ChromeDriverManager().install())
            service.log_path = os.devnull
            self.driver = webdriver.Chrome(service=service, options=options)
            self.log("Navegador iniciado com sucesso.\n")
        except Exception as e:
            self.log(f"Erro ao iniciar navegador: {e}")
            messagebox.showerror("Erro", str(e))

    def log(self, msg):
        self.log_area.insert(END, f"{time.strftime('%H:%M:%S')} - {msg}\n\n")
        self.log_area.see(END)

    def open_browser(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Informe uma URL.")
            return
        if not url.startswith("http"):
            url = "https://" + url
        self.driver.get(url)
        self.log(f"Abrindo URL: {url}")

    def start_capture_all(self):
        if self.is_capturing:
            return
        self.is_capturing = True
        self.captured_data_browser.clear()
        self.captured_packets_network.clear()
        self.stop_sniff_event.clear()

        self.log("Captura TOTAL iniciada.")
        threading.Thread(target=self.capture_browser_thread, daemon=True).start()
        threading.Thread(target=self.capture_network_thread, daemon=True).start()

    def stop_capture_all(self):
        self.is_capturing = False
        self.stop_sniff_event.set()
        self.log("Captura TOTAL parada.")

    def capture_browser_thread(self):
        while self.is_capturing:
            try:
                logs = self.driver.get_log("performance")
                for entry in logs:
                    try:
                        msg = json.loads(entry["message"])["message"]
                        method = msg["method"]
                        params = msg.get("params", {})
                        if method == "Network.requestWillBeSent":
                            req = params.get("request", {})
                            self.captured_data_browser.append({
                                "type": "request",
                                "url": req.get("url", ""),
                                "method": req.get("method", ""),
                                "timestamp": params.get("timestamp", time.time())
                            })
                            self.log(f"Request: {req.get('method')} {req.get('url')}")
                        elif method == "Network.responseReceived":
                            res = params.get("response", {})
                            self.captured_data_browser.append({
                                "type": "response",
                                "url": res.get("url", ""),
                                "status": res.get("status", 0),
                                "headers": res.get("headers", {}),
                                "ip": res.get("remoteIPAddress", ""),
                                "timestamp": params.get("timestamp", time.time())
                            })
                            self.log(f"Response: {res.get('status')} {res.get('url')}")
                    except Exception:
                        continue
                time.sleep(1)
            except Exception as e:
                self.log(f"Erro na captura do navegador: {e}")
                break

    def get_valid_ip(self, ip_candidate):
        try:
            if not ip_candidate or not isinstance(ip_candidate, str):
                return "8.8.8.8"
            return socket.gethostbyname(ip_candidate)
        except Exception:
            return "8.8.8.8"

    def capture_network_thread(self):
        try:
            sniff(filter="tcp port 80 or tcp port 443 or udp port 443",
                  prn=self.process_packet, store=0,
                  stop_filter=lambda x: self.stop_sniff_event.is_set())
        except Exception as e:
            self.log(f"Erro ao capturar pacotes: {e}")

    def process_packet(self, packet):
        self.captured_packets_network.append(packet)
        if IP in packet:
            if packet.haslayer(HTTPRequest):
                http_layer = packet[HTTPRequest]
                try:
                    info = f"\nHTTP Capturado de {packet[IP].src} → {packet[IP].dst}\n"
                    info += f"Host: {http_layer.Host.decode()}\n"
                    info += f"Path: {http_layer.Path.decode()}\n"
                    info += f"Method: {http_layer.Method.decode()}\n"
                    self.log(info)
                except Exception:
                    pass

    def save_all_pcapng(self):
        if not self.captured_data_browser and not self.captured_packets_network:
            messagebox.showwarning("Aviso", "Nenhum dado capturado.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".pcapng", filetypes=[("PCAPNG", "*.pcapng")])
        if not path:
            return

        packets = self.captured_packets_network.copy()
        seq = 0

        for data in self.captured_data_browser:
            src_ip = "192.168.0." + str(random.randint(2, 254))
            raw_ip = data.get("ip", "")
            dst_ip = self.get_valid_ip(raw_ip)
            sport = random.randint(1024, 65535)
            dport = 443 if data["url"].startswith("https") else 80

            parsed_url = urlparse(data["url"])
            path_url = parsed_url.path or "/"
            if parsed_url.query:
                path_url += "?" + parsed_url.query

            if data["type"] == "request":
                payload = f"{data['method']} {path_url} HTTP/1.1\r\nHost: {parsed_url.netloc}\r\n\r\n"
            elif data["type"] == "response":
                headers = "\r\n".join(f"{k}: {v}" for k, v in data.get("headers", {}).items())
                payload = f"HTTP/1.1 {data['status']} OK\r\n{headers}\r\n\r\n"
            else:
                payload = ""

            pkt = IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="PA", seq=seq) / Raw(load=payload.encode())
            pkt.time = float(data.get("timestamp", time.time()))
            seq += len(payload)
            packets.append(pkt)

        try:
            wrpcap(path, packets)
            self.log(f"PCAPNG TOTAL salvo com sucesso: {path}")
            messagebox.showinfo("Sucesso", f"Todos os dados salvos em:\n{path}")
        except Exception as e:
            self.log(f"Erro ao salvar arquivo: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WebCaptureApp(root)
    root.mainloop()
