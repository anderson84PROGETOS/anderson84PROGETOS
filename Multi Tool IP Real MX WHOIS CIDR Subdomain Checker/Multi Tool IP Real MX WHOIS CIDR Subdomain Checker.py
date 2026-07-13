import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import socket
import subprocess
import webbrowser
from datetime import datetime
import threading
import re
import ipaddress
from urllib.parse import urlparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# ===================== PRIMEIRA FERRAMENTA: IP Real + MX + Geo ===================== 
last_entrada = ""

def get_ip_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        response.raise_for_status()
        data = response.json()
        org = data.get("org", "")
        if org.startswith("AS"):
            partes = org.split(" ", 1)
            data["asn"] = partes[0]
            data["asn_name"] = partes[1] if len(partes) > 1 else "N/D"
        return data
    except:
        return None


def get_mx_and_real_ips(domain):
    result = f"🔍 ANÁLISE MX - {domain}\n"
    result += "=" * 60 + "\n\n"
    geo_entries = []

    try:
        mx_output = subprocess.run(['nslookup', '-type=MX', domain], 
                                 capture_output=True, text=True, timeout=10)
        
        result += "📧 REGISTROS MX ENCONTRADOS\n\n"
        for line in mx_output.stdout.splitlines():
            if "mail exchanger" in line.lower() or "MX" in line.upper():
                result += f"   {line.strip()}\n\n"
                if "mail exchanger" in line.lower():
                    mx_name = line.split()[-1].rstrip('.')
                    geo_entries.append(mx_name)
    except Exception as e:
        result += f"Erro ao consultar MX: {e}\n"

    result += "\n🌐 IP REAIS DOS SERVIDORES MX\n"
    result += "-" * 50 + "\n\n"

    mx_ips = []
    for mx in geo_entries:
        try:
            ip = socket.gethostbyname(mx)
            mx_ips.append(ip)
            result += f"📍 {mx} → {ip}\n"
            subprocess.run(['ping', '-4', '-n', '2', ip], capture_output=True, text=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW)
            
            data = get_ip_info(ip)
            if data and data.get('loc'):
                lat, lon = data['loc'].split(',')
                maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                result += f"\n🔗 Google Maps: {maps_url}\n\n"
                whatismyip_url = f"https://whatismyip.com.br/map.php?query={ip}"
                result += f"WhatIsMyIP: {whatismyip_url}\n\n"
                asn = data.get('asn')
                if asn and asn.startswith("AS"):
                    asn_num = asn[2:]
                    bgp_url = f"https://bgp.he.net/AS{asn_num}"
                    result += f"🌐 🔗 BGP.he.net : {bgp_url}\n\n"
        except:
            result += "\n"
    return result, mx_ips


def perform_lookup(entrada, progress_callback, result_callback):
    try:
        progress_callback(10)
        mx_analysis, mx_ips = get_mx_and_real_ips(entrada)
        progress_callback(45)

        mx_geo = "\n🌍 GEOLOCALIZAÇÃO DOS SERVIDORES MX\n" + "=" * 50 + "\n\n"
        for ip in mx_ips:
            data = get_ip_info(ip)
            if data:
                mx_geo += f"IP: {ip}\n\n"
                mx_geo += f"País     : {data.get('country', 'N/D')}\n"
                mx_geo += f"Região   : {data.get('region', 'N/D')}\n"
                mx_geo += f"Cidade   : {data.get('city', 'N/D')}\n"
                mx_geo += f"Org      : {data.get('org', 'N/D')}\n"
                mx_geo += f"ASN      : {data.get('asn','N/D')}\n"
                mx_geo += f"Empresa  : {data.get('asn_name','N/D')}\n\n"

                if data.get('loc'):
                    lat, lon = data['loc'].split(',')
                    maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                    mx_geo += f"Latitude  : {lat}\nLongitude : {lon}\n\n"
                    mx_geo += f"🔗 Maps   : {maps_url}\n\n"
                    mx_geo += f"WhatIsMyIP: https://whatismyip.com.br/map.php?query={ip}\n\n"
                    asn = data.get('asn')
                    if asn and asn.startswith("AS"):
                        mx_geo += f"🌐 BGP    : https://bgp.he.net/AS{asn[2:]}\n"
                mx_geo += "-" * 40 + "\n\n"
        progress_callback(75)

        # IP Principal
        main_geo = "\n🌐 GEOLOCALIZAÇÃO DO IP PRINCIPAL\n" + "=" * 50 + "\n\n"
        try:
            main_ip = socket.gethostbyname(entrada)
            main_data = get_ip_info(main_ip)
            if main_data:
                main_geo += f"IP        : {main_ip}\n\n"
                main_geo += f"País      : {main_data.get('country', 'N/D')}\n"
                main_geo += f"Região    : {main_data.get('region', 'N/D')}\n"
                main_geo += f"Cidade    : {main_data.get('city', 'N/D')}\n"
                main_geo += f"ASN       : {main_data.get('asn', 'N/D')}\n"
                main_geo += f"Empresa   : {main_data.get('asn_name', 'N/D')}\n"
                main_geo += f"Org       : {main_data.get('org', 'N/D')}\n\n"

                if main_data.get('loc'):
                    lat, lon = main_data['loc'].split(',')
                    main_geo += f"Latitude  : {lat}\nLongitude : {lon}\n\n"
                    main_geo += f"🔗 Maps   : https://www.google.com/maps/place/{lat},{lon}\n\n"
                    main_geo += f"WhatIsMyIP: https://whatismyip.com.br/map.php?query={main_ip}\n\n"
                    asn = main_data.get('asn')
                    if asn and asn.startswith("AS"):
                        main_geo += f"🌐 BGP    : https://bgp.he.net/AS{asn[2:]}\n"
        except:
            main_geo += "Não foi possível resolver o IP principal.\n"

        progress_callback(100)
        result_callback(mx_analysis + mx_geo + main_geo)
    except Exception as e:
        progress_callback(100)
        messagebox.showerror("Erro", str(e))

# ===================== SUBDOMAIN CHECKER (VERSÃO CORRIGIDA) =====================
class SubdomainChecker:
    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ]

        self.is_running = False
        self.stop_flag = False
        self.executor = None

        # Protocolo de fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()

    def create_widgets(self):
        # Título
        title = tk.Label(self.parent, text="🔎 Subdomain Checker 🔍", 
                        font=("Consolas", 20, "bold"), fg="#00ffcc", bg="#0f0f17")
        title.pack(pady=12)

        main_frame = tk.Frame(self.parent, bg="#0f0f17")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Wordlist
        tk.Label(main_frame, text="📄 Wordlist:", font=("Arial", 11, "bold"), fg="white", bg="#0f0f17").grid(row=0, column=0, sticky="w", pady=5)
        self.wordlist_path = tk.StringVar()
        tk.Entry(main_frame, textvariable=self.wordlist_path, width=85, font=("Consolas", 10), bg="#1e1e2e", fg="white").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(main_frame, text="Selecionar Wordlist", command=self.select_wordlist, bg="#4a6bff", fg="white", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=5)

        # User-Agent
        tk.Label(main_frame, text="🛡️ User-Agent:", font=("Arial", 11, "bold"), fg="white", bg="#0f0f17").grid(row=2, column=0, sticky="w", pady=5)
        self.ua_path = tk.StringVar()
        tk.Entry(main_frame, textvariable=self.ua_path, width=85, font=("Consolas", 10), bg="#1e1e2e", fg="white").grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(main_frame, text="Selecionar UserAgente.txt", command=self.select_useragent_file, bg="#ff8800", fg="white", font=("Arial", 10, "bold")).grid(row=3, column=1, padx=5)

        # URL Base
        tk.Label(main_frame, text="🌐 URL Base:", font=("Arial", 11, "bold"), fg="white", bg="#0f0f17").grid(row=4, column=0, sticky="w", pady=5)
        self.url_entry = tk.Entry(main_frame, width=85, font=("Consolas", 11), bg="#1e1e2e", fg="white")
        self.url_entry.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.url_entry.insert(0, "https://")

        # Timeout
        tk.Label(main_frame, text="⏱️ Timeout (segundos):", fg="white", bg="#0f0f17").grid(row=6, column=0, sticky="w", pady=8)
        self.timeout_var = tk.IntVar(value=6)
        tk.Spinbox(main_frame, from_=3, to=15, textvariable=self.timeout_var, width=8, font=("Consolas", 10), bg="#1e1e2e", fg="white").grid(row=6, column=1, sticky="w")

        # Botões
        btn_frame = tk.Frame(main_frame, bg="#0f0f17")
        btn_frame.grid(row=7, column=0, columnspan=2, pady=15, sticky="ew")

        self.start_btn = tk.Button(btn_frame, text="🚀 INICIAR VERIFICAÇÃO SEGURA", command=self.start_scan,
                                  bg="#00cc66", fg="black", font=("Arial", 12, "bold"), height=2, width=28)
        self.start_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.stop_btn = tk.Button(btn_frame, text="⛔ STOP", command=self.stop_scan,
                                 bg="#ff2222", fg="white", font=("Arial", 12, "bold"), height=2, width=12, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        self.save_btn = tk.Button(btn_frame, text="💾 SALVAR RESULTADOS", command=self.save_results,
                                 bg="#ffaa00", fg="black", font=("Arial", 12, "bold"), height=2, width=25, state="disabled")
        self.save_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Resultados
        tk.Label(main_frame, text="📋 Resultados Detalhados:", font=("Arial", 11, "bold"), fg="white", bg="#0f0f17").grid(row=8, column=0, sticky="w", pady=(10,5))
        
        self.result_text = scrolledtext.ScrolledText(main_frame, height=30, font=("Consolas", 10),
                                                     bg="#000000", fg="#00ff88", insertbackground="white")
        self.result_text.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.result_text.tag_config("green", foreground="#00ff88")
        self.result_text.tag_config("yellow", foreground="#ffff00")
        self.result_text.tag_config("red", foreground="#ff4444")
        self.result_text.tag_config("normal", foreground="#00ff88")

        self.progress = ttk.Progressbar(main_frame, mode="determinate")
        self.progress.grid(row=10, column=0, columnspan=2, sticky="ew", pady=8)

        self.status_var = tk.StringVar(value="Pronto")
        self.status_label = tk.Label(main_frame, textvariable=self.status_var, fg="#00ffcc", bg="#0f0f17", font=("Consolas", 10))
        self.status_label.grid(row=11, column=0, columnspan=2, pady=5)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)

    def select_wordlist(self):
        file = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt"), ("Todos", "*.*")])
        if file:
            self.wordlist_path.set(file)

    def select_useragent_file(self):
        file = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt"), ("Todos", "*.*")])
        if file:
            self.ua_path.set(file)
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self.user_agents = [line.strip() for line in f if line.strip()]
                self.log(f"[+] Carregados {len(self.user_agents)} User-Agents\n")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar User-Agents: {e}")

    def get_random_user_agent(self):
        return random.choice(self.user_agents) if self.user_agents else "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    def log(self, text, tag="normal"):
        self.result_text.config(state="normal")
        self.result_text.insert("end", text + "\n", tag)
        self.result_text.see("end")
        self.result_text.config(state="disabled")

    def save_results(self):
        if not self.result_text.get(1.0, "end").strip():
            messagebox.showwarning("Aviso", "Não há resultados para salvar!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os Arquivos", "*.*")],
            initialfile=f"subdomains_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                content = self.result_text.get(1.0, "end")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso!\n\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

    def start_scan(self):
        if not self.wordlist_path.get():
            messagebox.showerror("Erro", "Selecione uma wordlist!")
            return
        url = self.url_entry.get().strip()
        if not url or url == "https://":
            messagebox.showerror("Erro", "Digite uma URL base válida!")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.save_btn.config(state="disabled")
        self.result_text.delete(1.0, "end")
        self.stop_flag = False
        self.is_running = True

        threading.Thread(target=self.run_scan, args=(url,), daemon=True).start()

    def stop_scan(self):
        self.stop_flag = True
        self.log("\n⛔ Verificação interrompida pelo usuário.\n", tag="red")
        self.status_var.set("Interrompido")
        self.enable_save_button()

    def enable_save_button(self):
        try:
            self.save_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
        except:
            pass

    def on_closing(self):
        """Gerencia o fechamento seguro da janela"""
        if self.is_running:
            if messagebox.askyesno("Confirmação", 
                                  "A verificação ainda está em andamento.\n\n"
                                  "Deseja realmente interromper e fechar o programa?"):
                self.stop_flag = True
                if self.executor:
                    try:
                        self.executor.shutdown(wait=False, cancel_futures=True)
                    except:
                        pass
                self.log("\n⛔ Fechando aplicação...", tag="red")
                self.root.after(800, self.root.destroy)
            # Se não confirmar, não fecha
        else:
            self.root.destroy()

    def run_scan(self, base_url):
        try:
            self.status_var.set("Carregando wordlist...")
            with open(self.wordlist_path.get(), 'r', encoding='utf-8') as f:
                subdominios = [line.strip() for line in f if line.strip()]

            self.log(f"[+] Wordlist carregada: {len(subdominios)} subdomínios\n")
            if len(self.user_agents) > 1:
                self.log(f"[+] Usando {len(self.user_agents)} User-Agents\n")
            
            parsed = urlparse(base_url)
            domain = parsed.netloc or parsed.path
            if not domain:
                raise ValueError("URL inválida")

            urls_to_check = [base_url] + [f"http://{sub}.{domain}" for sub in subdominios]

            self.progress["maximum"] = len(urls_to_check)
            self.status_var.set(f"Verificando {len(urls_to_check)} URLs...")

            with ThreadPoolExecutor(max_workers=5) as executor:
                self.executor = executor
                future_to_url = {executor.submit(self.check_url, u): u for u in urls_to_check}
                
                for future in as_completed(future_to_url):
                    if self.stop_flag:
                        self.log("\n⛔ Verificação interrompida pelo usuário.", tag="red")
                        break
                    result = future.result()
                    self.process_result(result)
                    self.progress["value"] += 1
                    self.parent.update_idletasks()

            if not self.stop_flag:
                self.log("\n" + "="*120)
                self.log("✅ VERIFICAÇÃO CONCLUÍDA!\n", tag="green")
            
        except Exception as e:
            self.log(f"❌ Erro geral: {e}", tag="red")
        finally:
            self.is_running = False
            self.executor = None
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.save_btn.config(state="normal")
            self.status_var.set("Concluído" if not self.stop_flag else "Interrompido")

    def check_url(self, url):
        start_time = datetime.now()
        try:
            if not urlparse(url).scheme:
                url = f"http://{url}"

            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path

            headers = {'User-Agent': self.get_random_user_agent()}

            response = requests.get(url, timeout=self.timeout_var.get(), allow_redirects=True, headers=headers)

            elapsed = (datetime.now() - start_time).total_seconds()
            size_kb = len(response.content) / 1024 if response.content else 0

            return {
                "url": url,
                "response": response,
                "status": response.status_code,
                "ip": self.get_ip(domain),
                "title": self.extract_title(response.text),
                "server": response.headers.get("Server", "N/A"),
                "size_kb": size_kb,
                "elapsed": elapsed
            }
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)[:120]
            if "NameResolutionError" in error_msg or "getaddrinfo" in error_msg:
                error_msg = "Domínio não resolvido"
            return {"url": url, "status": "ERROR", "error": error_msg, "elapsed": elapsed, "ip": "N/A"}

    def get_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except:
            return "N/A"

    def extract_title(self, html):
        try:
            start = html.find("<title>")
            end = html.find("</title>")
            if start != -1 and end != -1:
                return html[start + 7:end].strip()[:80]
            return "N/A"
        except:
            return "N/A"

    def process_result(self, res):
        if res.get("status") == "ERROR":
            return

        status = res["status"]
        target = res["url"]
        response = res.get("response")

        if status == 403:
            color_tag = "red"
        elif 300 <= status < 400:
            color_tag = "yellow"
        elif status == 200:
            color_tag = "green"
        else:
            color_tag = "normal"

        result = f"[{status}] {target}\n\n"
        result += f"    URL Final      : {response.url if response else target}\n\n"
        result += f"    IP             : {res['ip']}\n\n"
        result += f"    Porta          : {443 if target.startswith('https://') else 80}\n"
        result += f"    HTTPS          : {'SIM' if target.startswith('https://') else 'NÃO'}\n"
        result += f"    Tamanho        : {res['size_kb']:.2f} KB\n"
        result += f"    Tipo           : {response.headers.get('Content-Type','N/D') if response else 'N/D'}\n"
        result += f"    Charset        : {getattr(response, 'encoding', 'N/D')}\n"
        result += f"    Título         : {res.get('title', 'N/A')}\n"
        result += f"    Server         : {res.get('server', 'N/A')}\n"
        result += f"    Powered By     : {response.headers.get('X-Powered-By','N/D') if response else 'N/D'}\n"
        result += f"    Cookies        : {len(response.cookies) if response else 0}\n"
        result += f"    Última Mod.    : {response.headers.get('Last-Modified','N/D') if response else 'N/D'}\n"
        result += f"    Data           : {response.headers.get('Date','N/D') if response else 'N/D'}\n"
        result += f"    Compressão     : {response.headers.get('Content-Encoding','N/D') if response else 'N/D'}\n"
        result += f"    Redirecionou   : {'SIM' if response and response.history else 'NÃO'}\n"
        result += f"    Tempo          : {res['elapsed']:.3f} s\n"
        result += "-" * 110 + "\n\n"

        self.log(result, tag=color_tag)

# ===================== INTERFACE PRINCIPAL =====================
root = tk.Tk()
root.title("Multi Tool - IP Real • MX • WHOIS • CIDR • Subdomain Checker")
root.geometry("1150x800")
root.state("zoomed")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# ==================== ABA 1 - IP Real + MX ====================
aba1 = ttk.Frame(notebook)
notebook.add(aba1, text="🔎 IP Real + MX + Geo")

tk.Label(aba1, text="🔎 IP Real + MX + Google Maps + BGP + whatismyip", 
         font=("Arial", 16, "bold")).pack(pady=10)

frame1 = ttk.Frame(aba1)
frame1.pack(pady=8)

ttk.Label(frame1, text="Domínio / IP:").pack(side="left", padx=5)
entry1 = ttk.Entry(frame1, width=50, font=("Arial", 11, "bold"))
entry1.pack(side="left", padx=5)

progress_bar = ttk.Progressbar(aba1, orient="horizontal", length=600, mode="determinate")
progress_bar.pack(pady=8)

result_text = tk.Text(aba1, width=130, height=32, font=("Consolas", 10), bg="#0a0a0a", fg="#00ff99")
result_text.pack(pady=10, padx=10, fill="both", expand=True)

def lookup():
    global last_entrada
    entrada = entry1.get().strip()
    if not entrada:
        messagebox.showwarning("Aviso", "Digite um domínio ou IP!")
        return
    last_entrada = entrada
    result_text.delete(1.0, tk.END)
    progress_bar['value'] = 0

    def update_progress(v):
        root.after(0, lambda: progress_bar.configure(value=v))
    def update_result(text):
        root.after(0, lambda: update_gui(text))

    thread = threading.Thread(target=perform_lookup, args=(entrada, update_progress, update_result), daemon=True)
    thread.start()

def update_gui(full_text):
    result_text.delete("1.0", tk.END)
    result_text.insert("1.0", full_text)
    # Tags e binds (mantidos do original)
    result_text.tag_configure("url", foreground="#00ccff", underline=True)
    result_text.tag_configure("whatismyip", foreground="#c026d3", underline=True)
    result_text.tag_configure("bgp", foreground="#ff8800", underline=True, font=("Consolas", 10, "bold"))
    
    texto = result_text.get("1.0", tk.END)
    for m in re.finditer(r"https://www\.google\.com/maps/place/[-0-9.,]+", texto):
        result_text.tag_add("url", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
    for m in re.finditer(r"https://whatismyip\.com\.br/map\.php\?query=[0-9.]+", texto):
        result_text.tag_add("whatismyip", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
    for m in re.finditer(r"https://bgp\.he\.net/AS\d+", texto):
        result_text.tag_add("bgp", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    result_text.tag_bind("url", "<Double-Button-1>", abrir_url)
    result_text.tag_bind("whatismyip", "<Double-Button-1>", abrir_url)
    result_text.tag_bind("bgp", "<Double-Button-1>", abrir_url)

def abrir_url(event):
    indice = result_text.index(f"@{event.x},{event.y}")
    inicio = result_text.search("https://", indice, backwards=True)
    url = result_text.get(inicio, "end").split()[0]
    webbrowser.open(url)

tk.Button(frame1, text="🔎 Analisar", command=lookup, bg="#00cc00", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=8)
tk.Button(aba1, text="💾 Salvar TXT", command=lambda: save_to_txt(result_text, last_entrada), bg="#ff8c00", fg="black", font=("Arial", 10, "bold")).pack(pady=5)

def save_to_txt(widget, last_entrada):
    if not widget.get(1.0, tk.END).strip():
        messagebox.showwarning("Aviso", "Faça uma busca primeiro!")
        return
    filename = f"analise_{last_entrada}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(widget.get(1.0, tk.END))
        messagebox.showinfo("Sucesso", f"Salvo em:\n{path}")

# ==================== ABA 2 - WHOIS ====================
aba2 = ttk.Frame(notebook)
notebook.add(aba2, text="🌐 WHOIS")

# ===================== TRADUÇÃO WHOIS =====================
traducao = {
    "domain:": "Domínio",
    "owner:": "Entidade",
    "ownerid:": "CNPJ",
    "responsible:": "Responsável",
    "country:": "País",
    "created:": "Criado em",
    "changed:": "Alterado em",
    "expires:": "Expira em",
    "status:": "Status",
    "nserver:": "Servidor DNS",
    "nameserver:": "Servidor DNS",
    "nameservers:": "Servidores DNS",
    "person:": "Pessoa",
    "e-mail:": "E-mail",
    "email:": "E-mail",
    "inetnum:": "Faixa de IP",
    "netname:": "Nome da Rede",
    "descr:": "Descrição",
    "org:": "Organização",
    "address:": "Endereço",
    "phone:": "Telefone",
    "abuse-mailbox:": "E-mail de Abuso",
    "source:": "Fonte",
    # Campos .gov e internacionais
    "registrar:": "Registrador",
    "registrant:": "Registrante",
    "registrant organization:": "Organização Registrante",
    "registrant street:": "Endereço",
    "registrant city:": "Cidade",
    "registrant state/province:": "Estado/Província",
    "registrant postal code:": "CEP",
    "registrant country:": "País",
    "registrant phone:": "Telefone",
    "registrant email:": "E-mail",
    "admin:": "Administrador",
    "tech:": "Técnico",
    "name server:": "Servidor DNS",
    "dnssec:": "DNSSEC",
    "domain status:": "Status do Domínio",
    "updated date:": "Atualizado em",
    "creation date:": "Criado em",
    "registry expiry date:": "Expira em",
}

def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
    for formato in formatos:
        try:
            data = datetime.strptime(texto.strip(), formato)
            return data.strftime("%d/%m/%Y")
        except:
            continue
    return texto

def traduzir_linha(linha):
    linha_lower = linha.lower()
    for termo, traducao_pt in traducao.items():
        if linha_lower.startswith(termo):
            valor = linha[len(termo):].strip()
            return f"{traducao_pt:<42}: {valor}"
    if ":" in linha:
        campo, valor = linha.split(":", 1)
        campo = campo.strip()
        return f"{campo:<42}: {valor.strip()}"
    return linha

def consultar_whois(entrada):
    try:
        # Detecta tipo
        try:
            socket.inet_pton(socket.AF_INET, entrada)
            tipo = "ipv4"
        except:
            try:
                socket.inet_pton(socket.AF_INET6, entrada)
                tipo = "ipv6"
            except:
                tipo = "dominio"

        if tipo in ["ipv4", "ipv6"]:
            servidor = 'whois.iana.org'
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((servidor, 43))
                s.send((entrada + "\r\n").encode())
                resposta = b""
                while True:
                    dados = s.recv(4096)
                    if not dados: break
                    resposta += dados
            texto_iana = resposta.decode(errors='ignore')
            match = re.search(r"refer:\s*(\S+)", texto_iana, re.IGNORECASE)
            servidor = match.group(1) if match else 'whois.arin.net'
        else:
            tld = '.' + entrada.split('.')[-1].lower()
            servidores_whois_tld = {
                '.com': 'whois.verisign-grs.com',
                '.net': 'whois.verisign-grs.com',
                '.org': 'whois.pir.org',
                '.br': 'whois.registro.br',
                '.gov': 'whois.nic.gov',
                '.edu': 'whois.educause.edu',
            }
            servidor = servidores_whois_tld.get(tld)
            if not servidor:
                return "TLD não suportado no momento."

        # Consulta WHOIS
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(15)
            s.connect((servidor, 43))
            s.send((entrada + "\r\n").encode())
            resposta = b""
            while True:
                dados = s.recv(4096)
                if not dados: break
                resposta += dados

        texto = resposta.decode(errors='ignore')

        # ==================== LIMPEZA DE DISCLAIMERS ====================
        texto = re.sub(
            r'(Information.*?support.*?access.*?)(\n\n|\Z)',
            '',
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        linhas = texto.splitlines()
        saida_formatada = ["=" * 90, f"WHOIS → {entrada.upper()}", "=" * 90, ""]

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            linha_lower = linha.lower()
            
            if re.search(r'copyright|terms|usage|legal|reserved|icann|verisign|notice|for more|information is provided', linha_lower):
                continue

            disclaimers = ["information is provided", "informational purposes", "as is without", "guarantee of accuracy"]
            if any(frase in linha_lower for frase in disclaimers):
                continue

            if linha.startswith(('%', '#', '>>>', '---', '==')):
                continue

            # Formatar datas
            linha = re.sub(r"\d{4}-\d{2}-\d{2}(T[\d:.Z]+)?|\d{8}",
                          lambda m: formatar_data_brasileira(m.group()), linha)

            linha_traduzida = traduzir_linha(linha)
            saida_formatada.append(linha_traduzida)

        return "\n".join(saida_formatada)

    except Exception as e:
        return f"[-] Erro na consulta: {e}"

# ===================== INTERFACE ABA 2 =====================
tk.Label(aba2, text="🌐 WHOIS • Consulta Segura • Registro Público", 
         font=("Arial", 16, "bold"), fg="#000000").pack(pady=12)

frame_whois = ttk.Frame(aba2)
frame_whois.pack(pady=8)

ttk.Label(frame_whois, text="ALVO (Domínio ou IP):").pack(side="left", padx=5)
entry_whois = ttk.Entry(frame_whois, width=55, font=("Consolas", 12, "bold"))
entry_whois.pack(side="left", padx=5)
entry_whois.insert(0, "200.196.152.57")

# ScrolledText corrigido
whois_text = scrolledtext.ScrolledText(aba2, font=("Consolas", 11), bg="#0a0a0a", fg="#00ff99",
                                       insertbackground="#00ff41", relief="solid", bd=2,
                                       selectbackground="#00aa00", selectforeground="white",
                                       wrap="none")
whois_text.pack(pady=10, padx=10, fill="both", expand=True)

# Tags de cores
whois_text.tag_configure("header", foreground="#0dfc41", font=("Consolas", 12, "bold"))
whois_text.tag_configure("cnpj", foreground="#ffffff", font=("Consolas", 11, "bold"))
whois_text.tag_configure("email", foreground="#ffaa00", font=("Consolas", 11, "bold"))

def whois_consultar():
    entrada = entry_whois.get().strip()
    if not entrada:
        messagebox.showwarning("Aviso", "Digite um domínio ou IP!")
        return

    whois_text.delete(1.0, tk.END)
    whois_text.insert(tk.END, f"[+] Consultando WHOIS para: {entrada}\n\n", "header")
    root.update_idletasks()

    resultado = consultar_whois(entrada)
    whois_text.delete(1.0, tk.END)

    for linha in resultado.splitlines():
        if "CNPJ" in linha or "ownerid:" in linha:
            whois_text.insert(tk.END, linha + "\n", "cnpj")
        elif "E-mail" in linha or "email:" in linha or "abuse-mailbox:" in linha:
            whois_text.insert(tk.END, linha + "\n", "email")
        elif linha.startswith("=") or "WHOIS →" in linha:
            whois_text.insert(tk.END, linha + "\n", "header")
        else:
            whois_text.insert(tk.END, linha + "\n")

def whois_salvar():
    texto = whois_text.get(1.0, tk.END).strip()
    if not texto or "Consultando" in texto:
        messagebox.showwarning("Aviso", "Faça uma consulta primeiro!")
        return
    
    dominio = entry_whois.get().strip() or "whois"
    filename = f"whois_{dominio.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                      initialfile=filename,
                                      filetypes=[("Arquivo TXT", "*.txt")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(texto)
        messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{path}")

# Botões
btn_frame = ttk.Frame(aba2)
btn_frame.pack(pady=8)

tk.Button(btn_frame, text="🔍 INICIAR CONSULTA", command=whois_consultar,
          bg="#00cc00", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=10)

tk.Button(btn_frame, text="💾 SALVAR TXT", command=whois_salvar,
          bg="#ff8c00", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=10)


# ==================== ABA 3 - Listador CIDR ====================
aba3 = ttk.Frame(notebook)
notebook.add(aba3, text="📋 Listador CIDR IP")

ttk.Label(aba3, text="Listador de Endereços IP (CIDR)", font=("Arial", 16, "bold")).pack(pady=10)

frame3 = ttk.Frame(aba3)
frame3.pack(pady=10)

ttk.Label(frame3, text="Bloco CIDR:").grid(row=0, column=0, padx=5)
entry_cidr = ttk.Entry(frame3, width=40)
entry_cidr.grid(row=0, column=1, padx=5)
entry_cidr.insert(0, "200.196.144.0/20")

btn_listar = tk.Button(frame3, text="Listar IP", command=lambda: listar_ips(entry_cidr, result_cidr, lbl_total), bg="#0ae979", fg="black", font=("Arial", 10, "bold"))
btn_listar.grid(row=0, column=2, padx=5)

btn_salvar_cidr = tk.Button(frame3, text="Salvar TXT", command=lambda: salvar_txt(result_cidr), bg="#e78f0c", fg="black", font=("Arial", 10, "bold"))
btn_salvar_cidr.grid(row=0, column=3, padx=5)

lbl_total = ttk.Label(aba3, text="Total de IP: 0")
lbl_total.pack(pady=5)

result_cidr = scrolledtext.ScrolledText(aba3, width=100, height=30, font=("Consolas", 10))
result_cidr.pack(pady=10, padx=10, fill="both", expand=True)

def listar_ips(entrada, resultado, lbl_total):
    resultado.delete("1.0", tk.END)
    bloco = entrada.get().strip()
    try:
        rede = ipaddress.ip_network(bloco, strict=False)
        total = 0
        for ip in rede.hosts():
            resultado.insert(tk.END, str(ip) + "\n")
            total += 1
        lbl_total.config(text=f"Total de IP: {total}")
    except ValueError:
        messagebox.showerror("Erro", "Bloco de IP inválido!")

def salvar_txt(resultado):
    texto = resultado.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Aviso", "Nada para salvar.")
        return
    arquivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo TXT", "*.txt")])
    if arquivo:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(texto)
        messagebox.showinfo("Sucesso", "Arquivo salvo!")

# ==================== ABA 4 - SUBDOMAIN CHECKER ====================
aba4 = ttk.Frame(notebook)
notebook.add(aba4, text="🔍 Subdomain Checker")
SubdomainChecker(aba4)

root.mainloop()
