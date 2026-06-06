#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import threading
import time
from datetime import datetime
import webbrowser
import socket
import subprocess
import re


class IPTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rastreador de IP WEB")
        self.root.geometry("1020x800")
        self.root.state("zoomed")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.ip_var = tk.StringVar()
        self.last_coords = None
        self.as_number = None
        self.as_name = None
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, text="Rastreador de IP WEB", 
                               font=("Arial", 19, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ip_frame = ttk.LabelFrame(main_frame, 
            text="Domínio(s) ou IP (separados por espaço ou vírgula)", 
            padding="10")
        ip_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ip_entry = ttk.Entry(ip_frame, textvariable=self.ip_var, width=75, font=("Arial", 10))
        ip_entry.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        ip_entry.bind('<Return>', lambda event: self.start_tracking())
        
        ttk.Button(ip_frame, text="🔍 Rastrear", command=self.start_tracking).grid(row=0, column=1)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 20))
        
        self.style.configure('Save.TButton', foreground='black', background='#28a745')
        self.style.configure('Clear.TButton', foreground='black', background='#dc3545')
        self.style.configure('Maps.TButton', foreground='black', background='#007bff')
        self.style.configure('BGP.TButton', foreground='black', background='#6f42c1')
        
        ttk.Button(button_frame, text="💾 Salvar", command=self.save_results, 
                  style='Save.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="🗑️ Limpar", command=self.clear_results, 
                  style='Clear.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🗺️ Google Maps", command=self.open_google_maps, 
                  style='Maps.TButton').grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🌐 BGP Lookup", command=self.open_bgp_lookup, 
                  style='BGP.TButton').grid(row=0, column=3, padx=5)
        
        result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, height=36, width=120, font=("Consolas", 10)
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
    def extract_as_info(self, text):
        if not text:
            return None, None
        match = re.search(r'AS(\d+)', str(text), re.IGNORECASE)
        if match:
            as_number = match.group(1)
            as_name = re.sub(r'AS\d+\s*', '', str(text), flags=re.IGNORECASE).strip()
            as_name = re.sub(r'^(Org|ISP|Organization|AS)[:\-\s]*', '', as_name, flags=re.IGNORECASE).strip()
            return as_number, as_name
        
        match = re.search(r'\b(\d{4,6})\b', str(text))
        if match:
            as_number = match.group(1)
            as_name = str(text).replace(as_number, '').strip()
            return as_number, as_name
        return None, None
        
    def resolve_domain(self, domain):
        try:
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('//')[1].split('/')[0].split(':')[0]
            return socket.gethostbyname(domain)
        except:
            return None
            
    def run_nslookup(self, domain, record_type="ANY"):
        try:
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('//')[1].split('/')[0].split(':')[0]
            
            cmd = ['nslookup', f'-type={record_type}', domain]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            output = result.stdout.strip()
            if result.stderr:
                output += "\n" + result.stderr.strip()
            return output if output else f"Nenhuma resposta."
        except FileNotFoundError:
            return "❌ nslookup não encontrado (instale dnsutils)"
        except Exception as e:
            return f"Erro: {str(e)}"
        
    def extract_mx_servers(self, mx_output):
        mx_servers = []
        for line in mx_output.splitlines():
            if "mail exchanger =" in line.lower():
                match = re.search(r'mail exchanger = (\S+)', line, re.IGNORECASE)
                if match:
                    server = match.group(1).rstrip('.')
                    if server not in mx_servers:
                        mx_servers.append(server)
        return mx_servers
        
    def start_tracking(self):
        input_str = self.ip_var.get().strip()
        if not input_str:
            self.update_output("⚠️ Insira um ou mais domínios!")
            return
        
        self.as_number = None
        self.as_name = None
        self.last_coords = None
        
        self.update_output(f"🔄 Processando: {input_str}\n")
        
        thread = threading.Thread(target=self.track_ip, args=(input_str,))
        thread.daemon = True
        thread.start()
        
    def track_ip(self, input_str):
        try:
            domains = re.split(r'[,;\s]+', input_str.strip())
            domains = [d.strip() for d in domains if d.strip()]
            
            dns_section = ""
            main_ip = None
            
            for domain in domains:
                dns_section += f"{'='*80}\n"
                dns_section += f"🔹 DOMÍNIO: {domain}\n"
                dns_section += f"{'='*80}\n\n"
                
                mx_result = self.run_nslookup(domain, "MX")
                dns_section += f"=== MX RECORDS ===\n{mx_result}\n\n"
                
                mx_servers = self.extract_mx_servers(mx_result)
                if mx_servers:
                    dns_section += f"🔸 MX Encontrados: {', '.join(mx_servers)}\n\n"
                    for mx in mx_servers:
                        dns_section += f"{'─'*65}\n"
                        dns_section += f"🔸 MX: {mx}\n"
                        dns_section += f"{'─'*65}\n\n"
                        
                        any_mx = self.run_nslookup(mx, "ANY")
                        dns_section += f"=== ANY RECORDS ({mx}) ===\n{any_mx}\n\n"
                        
                        resolved_mx = self.resolve_domain(mx)
                        if resolved_mx:
                            dns_section += f"✅ IP: {resolved_mx}\n\n"
                            if main_ip is None:
                                main_ip = resolved_mx
                
                any_result = self.run_nslookup(domain, "ANY")
                dns_section += f"=== ANY RECORDS ({domain}) ===\n{any_result}\n\n"
                
                resolved = self.resolve_domain(domain)
                if resolved and main_ip is None:
                    main_ip = resolved
            
            if not main_ip and domains:
                main_ip = domains[0]
            
            self.update_output(f"🚀 Consultando geolocalização...\n")
            
            results = []
            if main_ip:
                apis = [
                    {"name": "IP-API", "url": f"http://ip-api.com/json/{main_ip}"},
                    {"name": "IPInfo", "url": f"https://ipinfo.io/{main_ip}/json"}
                ]
                for api in apis:
                    try:
                        resp = requests.get(api["url"], timeout=8)
                        if resp.status_code == 200:
                            results.append({"source": api["name"], "data": resp.json()})
                        else:
                            results.append({"source": api["name"], "error": f"HTTP {resp.status_code}"})
                    except Exception as e:
                        results.append({"source": api["name"], "error": str(e)})
                    time.sleep(1.2)
            
            self.display_results(results, dns_section, main_ip)
            
        except Exception as e:
            self.update_output(f"❌ Erro: {str(e)}")
            
    def display_results(self, results, dns_section, main_ip):
        output = "=== RESULTADOS DO RASTREAMENTO ===\n\n"
        if main_ip:
            output += f"IP Principal: {main_ip}\n"
        output += "=" * 80 + "\n\n"
        output += dns_section
        
        for result in results:
            source = result["source"]
            output += f"\n--- Fonte: {source} ---\n\n"
            if "error" in result:
                output += f"ERRO: {result['error']}\n\n"
                continue
            data = result["data"]
            
            if source == "IP-API":
                output += "===== IDENTIFICAÇÃO =====\n"
                output += f"  IP: {data.get('query', 'N/A')}\n"
                output += f"  ASN: {data.get('as', 'N/A')}\n"
                output += f"  ISP: {data.get('isp', 'N/A')}\n"
                output += f"  Org: {data.get('org', 'N/A')}\n\n"
                output += "===== LOCALIZAÇÃO =====\n"
                output += f"  País: {data.get('country', 'N/A')}\n"
                output += f"  Cidade: {data.get('city', 'N/A')}\n"
                output += f"  Lat: {data.get('lat', 'N/A')}\n"
                output += f"  Lon: {data.get('lon', 'N/A')}\n\n"
                
                if data.get('lat') and data.get('lon'):
                    self.last_coords = {
                        'lat': float(data['lat']),
                        'lon': float(data['lon']),
                        'city': data.get('city'),
                        'country': data.get('country')
                    }
                    output += f"✅ Coordenadas salvas para Google Maps\n\n"
                
                if data.get('as'):
                    as_num, as_name = self.extract_as_info(data['as'])
                    if as_num:
                        self.as_number = as_num
                        self.as_name = as_name
                        output += f"✅ ASN Detectado: AS{as_num} - {as_name}\n\n"
                
            elif source == "IPInfo":
                if data.get('org'):
                    as_num, as_name = self.extract_as_info(data['org'])
                    if as_num:
                        self.as_number = as_num
                        self.as_name = as_name
                        output += f"✅ ASN Detectado: AS{as_num} - {as_name}\n\n"
        
        output += "=" * 85
        self.update_output(output)
        
    def update_output(self, message):
        self.root.after(0, lambda: self.result_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.result_text.insert(tk.END, message))
        
    def save_results(self):
        content = self.result_text.get(1.0, tk.END).strip()
        if len(content) < 30:
            self.update_output("⚠️ Nada para salvar.")
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rastreamento_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.update_output(f"✅ Salvo: {filename}")
        except Exception as e:
            self.update_output(f"❌ Erro ao salvar: {str(e)}")
            
    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Resultados aparecerão aqui...\n")
        self.as_number = None
        self.as_name = None
        self.last_coords = None
        
    def open_google_maps(self):
        if not self.last_coords:
            self.update_output("⚠️ Rastreie um domínio/IP primeiro para usar o Google Maps.")
            return
        
        try:
            lat = self.last_coords['lat']
            lon = self.last_coords['lon']
            # Link mais confiável com zoom
            url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}&zoom=15"
            webbrowser.open(url)
            self.update_output(f"🗺️ Google Maps aberto: {lat}, {lon} (Zoom 15)")
        except Exception as e:
            self.update_output(f"❌ Erro ao abrir Google Maps: {str(e)}")
        
    def open_bgp_lookup(self):
        if not self.as_number:
            self.update_output("⚠️ Nenhum ASN encontrado. Tente rastrear novamente.")
            return
        url = f"https://bgp.he.net/AS{self.as_number}"
        webbrowser.open(url)
        name = f" - {self.as_name}" if self.as_name else ""
        self.update_output(f"🌐 BGP Lookup aberto → AS{self.as_number}{name}")


if __name__ == "__main__":
    root = tk.Tk()
    app = IPTrackerGUI(root)
    root.mainloop()
