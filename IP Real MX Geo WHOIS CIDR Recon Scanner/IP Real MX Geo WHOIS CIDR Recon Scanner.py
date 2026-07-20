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
import concurrent.futures
from urllib.parse import urljoin, urlparse
import sys
from bs4 import BeautifulSoup
import time
import urllib3
import os
import warnings
import atexit

# Suprime janela do console no Windows
_startupinfo = None
if sys.platform == 'win32':
    _startupinfo = subprocess.STARTUPINFO()
    _startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _startupinfo.wShowWindow = subprocess.SW_HIDE

# Suprime warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# ===================== VARIÁVEIS GLOBAIS (para funções soltas) =====================
last_entrada = ""

# ===================================================================
# FUNÇÕES DA ABA 1 - IP REAL + MX + GEO (mantidas como estavam)
# ===================================================================
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
        # NSLOOKUP SEM JANELA
        mx_output = subprocess.run(['nslookup', '-type=MX', domain], 
                                 capture_output=True, text=True, timeout=10,
                                 startupinfo=_startupinfo)  # <-- ADICIONADO
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
            
            # ✅ PING SILENCIOSO (sem janela, sem mostrar caminho)
            subprocess.run(['ping', '-4', '-n', '2', ip],
                          capture_output=True, text=True, timeout=8,
                          startupinfo=_startupinfo)
            
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

# ===================================================================
# FUNÇÕES DA ABA 2 - WHOIS (EXATAMENTE COMO VOCÊ PEDIU)
# ===================================================================
traducao = {
    "domain:": "Domínio",
    "owner:": "Entidade",
    "ownerid:": "CNPJ",
    "responsible:": "Responsável",
    "country:": "País",
    "created:": "Criado",
    "changed:": "Alterado",
    "expires:": "Expira",
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
    "updated date:": "Atualizado",
    "creation date:": "Criado",
    "registry expiry date:": "Expira",
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

# ===================================================================
# FUNÇÕES DA ABA 3 - CIDR
# ===================================================================
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

# ===================================================================
# FUNÇÕES DO SCANNER (ABA 4) - GLOBAIS
# ===================================================================
HEADERS_BASE = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

def get_target_ip(target):
    try:
        domain = target.split("://")[1].split("/")[0].split(':')[0]
        return socket.gethostbyname(domain)
    except:
        return "N/A"

def detect_technologies(headers):
    techs = []
    server = headers.get("Server", "")    
    powered = headers.get("X-Powered-By", "")
    if server: techs.append(server)
    if powered: techs.append(powered)

    h = str(headers).lower()
    tecnologias = {
        "cloudflare": "Cloudflare", "nginx": "Nginx", "apache": "Apache",
        "iis": "Microsoft IIS", "microsoft-iis": "Microsoft IIS",
        "litespeed": "LiteSpeed", "openresty": "OpenResty", "caddy": "Caddy",
        "gunicorn": "Gunicorn", "uwsgi": "uWSGI", "tomcat": "Apache Tomcat",
        "jetty": "Jetty", "node": "Node.js", "express": "Express.js",
        "asp.net": "ASP.NET", "aspnet": "ASP.NET", "php": "PHP",
        "laravel": "Laravel", "wordpress": "WordPress", "joomla": "Joomla",
        "drupal": "Drupal", "magento": "Magento", "shopify": "Shopify",
        "woocommerce": "WooCommerce", "prestashop": "PrestaShop",
        "cpanel": "cPanel", "plesk": "Plesk", "varnish": "Varnish Cache",
        "haproxy": "HAProxy", "envoy": "Envoy", "cloudfront": "CloudFront",
        "akamai": "Akamai", "fastly": "Fastly", "sucuri": "Sucuri WAF",
        "imperva": "Imperva WAF", "f5": "F5 BIG-IP", "mod_security": "ModSecurity",
        "modsecurity": "ModSecurity", "kestrel": "Kestrel", "oracle": "Oracle",
        "jboss": "JBoss", "wildfly": "WildFly", "weblogic": "WebLogic",
        "websphere": "WebSphere", "firebase": "Firebase", "netlify": "Netlify",
        "vercel": "Vercel", "heroku": "Heroku"
    }
    for chave, nome in tecnologias.items():
        if chave in h and nome not in techs:
            techs.append(nome)
    return " | ".join(techs) if techs else "N/D"


# ===================================================================
# CLASSE PRINCIPAL - Application
# ===================================================================
class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔎 IP Real | 📧 MX | 🌍 Geo | 🌐 WHOIS | 📋 CIDR | 🔗 Recon Scanner")
        self.root.geometry("1400x900")
        self.root.state("zoomed")

        # ============ CONTROLES ============
        self.is_running = False
        self.stop_flag = False
        self.executor = None
        self.found_urls = []
        self.wordlist_path = None
        self.ip_list_path = None
        self.user_agents_list = []
        self.selected_user_agent = None

        # Protocolo de fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Garantir que os._exit seja chamado mesmo se algo falhar
        atexit.register(self._force_exit)

        self.create_widgets()

    def _force_exit(self):
        try:
            os._exit(0)
        except:
            pass

    def on_closing(self):
        self.stop_flag = True
        self.is_running = False
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        try:
            os._exit(0)
        except:
            pass
        finally:
            try:
                self.root.destroy()
            except:
                pass
            os._exit(0)

    def create_widgets(self):
        # Notebook (Abas)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#16213e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#0f3460", foreground="white",
                        padding=[20, 5], font=("Arial", 11, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#e94560")])

        # 🔵 BARRAS DE PROGRESSO VERDE
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor="#1a1a2e",
                        background="#00ff88",
                        lightcolor="#00ff88",
                        darkcolor="#00ff88",
                        bordercolor="#00ff88")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Cria as 4 abas
        self.setup_aba1()
        self.setup_aba2()
        self.setup_aba3()
        self.setup_aba4()

    # ===================================================================
    # ABA 1 - IP REAL + MX + GEO
    # ===================================================================
    def setup_aba1(self):
        aba1 = ttk.Frame(self.notebook)
        self.notebook.add(aba1, text="🔎 IP Real + MX + Geo")

        tk.Label(aba1, text="🔎 IP Real + MX + Google Maps + BGP + whatismyip", 
                 font=("Arial", 16, "bold")).pack(pady=10)

        frame1 = ttk.Frame(aba1)
        frame1.pack(pady=8)

        ttk.Label(frame1, text="Domínio / IP:").pack(side="left", padx=5)
        self.entry1 = ttk.Entry(frame1, width=50, font=("Arial", 11, "bold"))
        self.entry1.pack(side="left", padx=5)

        # ⬇️ BARRA VERDE - ABA 1
        self.progress1 = ttk.Progressbar(aba1, orient="horizontal", length=600, mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress1.pack(pady=8)     

        self.result_text = tk.Text(aba1, width=130, height=32, font=("Consolas", 10), bg="#0a0a0a", fg="#00ff99")
        self.result_text.pack(pady=10, padx=10, fill="both", expand=True)

        # Configurar tags para links clicáveis
        self.result_text.tag_configure("url", foreground="#00ccff", underline=True)
        self.result_text.tag_configure("whatismyip", foreground="#c026d3", underline=True)
        self.result_text.tag_configure("bgp", foreground="#ff8800", underline=True, font=("Consolas", 10, "bold"))

        tk.Button(frame1, text="🔎 Analisar", command=self.lookup, 
                  bg="#00cc00", fg="black", font=("Arial", 10, "bold")).pack(side="left", padx=8)
        tk.Button(aba1, text="💾 Salvar TXT", command=self.save_aba1, 
                  bg="#ff8c00", fg="black", font=("Arial", 10, "bold")).pack(pady=5)

    def lookup(self):
        global last_entrada
        entrada = self.entry1.get().strip()
        if not entrada:
            messagebox.showwarning("Aviso", "Digite um domínio ou IP!")
            return
        last_entrada = entrada
        self.result_text.delete(1.0, tk.END)
        self.progress1['value'] = 0

        def update_progress(v):
            self.root.after(0, lambda: self.progress1.configure(value=v))
        def update_result(text):
            self.root.after(0, lambda: self.update_gui(text))

        thread = threading.Thread(target=perform_lookup, args=(entrada, update_progress, update_result), daemon=True)
        thread.start()

    def update_gui(self, full_text):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", full_text)
        
        texto = self.result_text.get("1.0", tk.END)
        for m in re.finditer(r"https://www\.google\.com/maps/place/[-0-9.,]+", texto):
            self.result_text.tag_add("url", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r"https://whatismyip\.com\.br/map\.php\?query=[0-9.]+", texto):
            self.result_text.tag_add("whatismyip", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r"https://bgp\.he\.net/AS\d+", texto):
            self.result_text.tag_add("bgp", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

        self.result_text.tag_bind("url", "<Double-Button-1>", self.abrir_url)
        self.result_text.tag_bind("whatismyip", "<Double-Button-1>", self.abrir_url)
        self.result_text.tag_bind("bgp", "<Double-Button-1>", self.abrir_url)

    def abrir_url(self, event):
        indice = self.result_text.index(f"@{event.x},{event.y}")
        inicio = self.result_text.search("https://", indice, backwards=True)
        url = self.result_text.get(inicio, "end").split()[0]
        webbrowser.open(url)

    def save_aba1(self):
        global last_entrada
        texto = self.result_text.get(1.0, tk.END).strip()
        if not texto:
            messagebox.showwarning("Aviso", "Faça uma busca primeiro!")
            return
        filename = f"analise_{last_entrada}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Sucesso", f"Salvo em:\n{path}")

    # ===================================================================
    # ABA 2 - WHOIS (EXATAMENTE COMO VOCÊ PEDIU - FUNÇÕES SOLTAS)
    # ===================================================================
    def setup_aba2(self):
        aba2 = ttk.Frame(self.notebook)
        self.notebook.add(aba2, text="🌐 WHOIS")

        tk.Label(aba2, text="🌐 WHOIS • Consulta Segura • Registro Público", 
                 font=("Arial", 16, "bold"), fg="#000000").pack(pady=12)

        frame_whois = ttk.Frame(aba2)
        frame_whois.pack(pady=8)

        ttk.Label(frame_whois, text="ALVO (Domínio ou IP):").pack(side="left", padx=5)
        self.entry_whois = ttk.Entry(frame_whois, width=55, font=("Consolas", 12, "bold"))
        self.entry_whois.pack(side="left", padx=5)
        self.entry_whois.insert(0, "200.196.152.57")

        # ScrolledText
        self.whois_text = scrolledtext.ScrolledText(aba2, font=("Consolas", 11), bg="#0a0a0a", fg="#00ff99",
                                                   insertbackground="#00ff41", relief="solid", bd=2,
                                                   selectbackground="#00aa00", selectforeground="white",
                                                   wrap="none")
        self.whois_text.pack(pady=10, padx=10, fill="both", expand=True)

        # Tags de cores
        self.whois_text.tag_configure("header", foreground="#0dfc41", font=("Consolas", 12, "bold"))
        self.whois_text.tag_configure("cnpj", foreground="#ffffff", font=("Consolas", 11, "bold"))
        self.whois_text.tag_configure("email", foreground="#ffaa00", font=("Consolas", 11, "bold"))

        def whois_consultar():
            entrada = self.entry_whois.get().strip()
            if not entrada:
                messagebox.showwarning("Aviso", "Digite um domínio ou IP!")
                return

            self.whois_text.delete(1.0, tk.END)
            self.whois_text.insert(tk.END, f"[+] Consultando WHOIS para: {entrada}\n\n", "header")
            self.root.update_idletasks()

            resultado = consultar_whois(entrada)
            self.whois_text.delete(1.0, tk.END)

            for linha in resultado.splitlines():
                if "CNPJ" in linha or "ownerid:" in linha:
                    self.whois_text.insert(tk.END, linha + "\n", "cnpj")
                elif "E-mail" in linha or "email:" in linha or "abuse-mailbox:" in linha:
                    self.whois_text.insert(tk.END, linha + "\n", "email")
                elif linha.startswith("=") or "WHOIS →" in linha:
                    self.whois_text.insert(tk.END, linha + "\n", "header")
                else:
                    self.whois_text.insert(tk.END, linha + "\n")

        def whois_salvar():
            texto = self.whois_text.get(1.0, tk.END).strip()
            if not texto or "Consultando" in texto:
                messagebox.showwarning("Aviso", "Faça uma consulta primeiro!")
                return
            
            dominio = self.entry_whois.get().strip() or "whois"
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

    # ===================================================================
    # ABA 3 - CIDR
    # ===================================================================
    def setup_aba3(self):
        aba3 = ttk.Frame(self.notebook)
        self.notebook.add(aba3, text="📋 Listador CIDR IP")

        tk.Label(aba3, text="Listador de Endereços IP (CIDR)", font=("Arial", 16, "bold")).pack(pady=10)

        frame3 = ttk.Frame(aba3)
        frame3.pack(pady=10)

        ttk.Label(frame3, text="Bloco CIDR:").grid(row=0, column=0, padx=5)
        self.entry_cidr = ttk.Entry(frame3, width=40)
        self.entry_cidr.grid(row=0, column=1, padx=5)
        self.entry_cidr.insert(0, "200.196.144.0/20")

        self.lbl_total = ttk.Label(aba3, text="Total de IP: 0")
        self.lbl_total.pack(pady=5)

        self.result_cidr = scrolledtext.ScrolledText(aba3, width=100, height=30, font=("Consolas", 10))
        self.result_cidr.pack(pady=10, padx=10, fill="both", expand=True)

        btn_frame3 = ttk.Frame(aba3)
        btn_frame3.pack(pady=5)

        tk.Button(btn_frame3, text="Listar IP", command=self.listar_ips_cidr,
                  bg="#0ae979", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame3, text="Salvar TXT", command=self.salvar_cidr,
                  bg="#e78f0c", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

    def listar_ips_cidr(self):
        listar_ips(self.entry_cidr, self.result_cidr, self.lbl_total)

    def salvar_cidr(self):
        salvar_txt(self.result_cidr)

    # ===================================================================
    # ABA 4 - Recon Scanner
    # ===================================================================
    def setup_aba4(self):
        aba4 = ttk.Frame(self.notebook)
        self.notebook.add(aba4, text="🚀 Recon Scanner")

        tk.Label(aba4, text="🚀 Recon Scanner - Fuzzer + Scanner de IP (Portas customizáveis)", 
                 font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(aba4, text="Digite a URL (use /FUZZ no final para wordlist)", font=("Arial", 11, "bold")).pack(pady=5)
        self.url_entry = tk.Entry(aba4, width=90, font=("Consolas", 11))
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, "https://exemplo.com/FUZZ")

        ua_frame = ttk.Frame(aba4)
        ua_frame.pack(pady=8)
        tk.Button(ua_frame, text="📋 Carregar User-Agents", command=self.select_ua_file).pack(side=tk.LEFT, padx=5)
        self.ua_combo = ttk.Combobox(ua_frame, width=200, state="readonly")
        self.ua_combo.pack(side=tk.LEFT, padx=5)

        file_frame = ttk.Frame(aba4)
        file_frame.pack(pady=10)
        tk.Button(file_frame, text="📋 Wordlist", command=self.select_wordlist, bg="#03fcc6", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(file_frame, text="🌐 ip.txt", command=self.select_ip_file, bg="#ffcc00", width=15).pack(side=tk.LEFT, padx=10)

        self.word_count_label = tk.Label(aba4, text="Wordlist: Nenhum", bg="#03fcc6", fg="black", font=("Arial", 9, "bold"))
        self.word_count_label.pack(pady=5)
        self.ip_label = tk.Label(aba4, text="ip.txt: Nenhum", bg="#ffcc00", fg="black", font=("Arial", 9, "bold"))
        self.ip_label.pack(pady=5)

        # Portas
        port_frame = ttk.Frame(aba4)
        port_frame.pack(pady=8)
        ttk.Label(port_frame, text="Portas (separadas por vírgula):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.port_entry = tk.Entry(port_frame, width=40, font=("Consolas", 11, "bold"), bg="#ffffcc")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "80,443,8080,8443")

        btn_port_frame = ttk.Frame(aba4)
        btn_port_frame.pack(pady=5)

        def set_portas(texto):
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, texto)

        tk.Button(btn_port_frame, text="HTTP (80)", command=lambda: set_portas("80"),
                  bg="#aaffaa", width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_port_frame, text="HTTPS (443)", command=lambda: set_portas("443"),
                  bg="#aaddff", width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_port_frame, text="HTTP+HTTPS", command=lambda: set_portas("80,443"),
                  bg="#ffcc00", width=14).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_port_frame, text="Comuns", command=lambda: set_portas("80,443,8080,8443,3000,5000,8000,9090"),
                  bg="#ffaa88", width=20).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_port_frame, text="Todas", command=lambda: set_portas("80,443,8080,8443,3000,5000,8000,9090,9000,9443,8888,8081,8082"),
                  bg="#ff8888", width=14).pack(side=tk.LEFT, padx=3)

        # Botões principais
        btn_frame = ttk.Frame(aba4)
        btn_frame.pack(pady=15)

        self.start_button = tk.Button(btn_frame, text="🚀 INICIAR FUZZ", command=self.start_scan,
                                      bg="#00FF00", font=("Arial", 12, "bold"), width=22)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.scan_ip_button = tk.Button(btn_frame, text="🔍 SCAN IP (portas custom)", command=self.start_scan_ip,
                                        bg="#00AAFF", fg="white", font=("Arial", 12, "bold"), width=28)
        self.scan_ip_button.pack(side=tk.LEFT, padx=10)

        # BOTÃO STOP
        self.stop_button = tk.Button(btn_frame, text="⏹ PARAR", command=self.stop_scan,
                                     bg="#ff2222", fg="white", font=("Arial", 12, "bold"), width=14)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        self.stop_button.config(state="disabled")

        tk.Button(btn_frame, text="💾 Salvar", command=self.save_results,
                  bg="#ff8c00", width=18).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="🧹 Limpar", command=self.limpar_resultados,
                  bg="#ff4444", fg="white", font=("Arial", 12, "bold"), width=16).pack(side=tk.LEFT, padx=10)

        # ⬇️ BARRA VERDE - ABA 4
        self.progress = ttk.Progressbar(aba4, length=1100, mode="determinate",style="green.Horizontal.TProgressbar")
        self.progress.pack(pady=10) 
        
        self.total_label = tk.Label(aba4, text="Total Encontrados: 0", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

        self.results_text = scrolledtext.ScrolledText(
            aba4, width=170, height=28, bg="#0a0a0a", fg="#ffffff",
            font=("Consolas", 10), wrap="none"
        )
        self.results_text.pack(pady=10, padx=10, fill="both", expand=True)

    # ==================== FUNÇÕES DO SCANNER ====================
    def select_ua_file(self):
        ua_file = filedialog.askopenfilename(title="User-Agents.txt", filetypes=[("TXT", "*.txt")])
        if ua_file:
            with open(ua_file, 'r', encoding='utf-8') as f:
                self.user_agents_list[:] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            self.ua_combo['values'] = self.user_agents_list
            if self.user_agents_list:
                self.ua_combo.current(0)
                self.selected_user_agent = self.user_agents_list[0]

    def select_wordlist(self):
        self.wordlist_path = filedialog.askopenfilename(title="Wordlist", filetypes=[("TXT", "*.txt")])
        if self.wordlist_path:
            with open(self.wordlist_path, 'r', encoding='utf-8') as f:
                count = sum(1 for line in f if line.strip())
            self.word_count_label.config(text=f"Wordlist: {count} palavras")

    def select_ip_file(self):
        self.ip_list_path = filedialog.askopenfilename(title="ip.txt", filetypes=[("TXT", "*.txt")])
        if self.ip_list_path:
            with open(self.ip_list_path, 'r', encoding='utf-8') as f:
                count = sum(1 for line in f if line.strip())
            self.ip_label.config(text=f"ip.txt: {count} IPs")

    def start_scan_ip(self):
        self.wordlist_path = None
        self.start_scan()

    def stop_scan(self):
        self.stop_flag = True
        self.is_running = False
        
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None
        
        self.stop_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.scan_ip_button.config(state="normal")
        self.total_label.config(text=f"Total Encontrados: {len(self.found_urls)} (PARADO)")

    def check_target(self, target, update_progress):
        if self.stop_flag:
            return

        headers = HEADERS_BASE.copy()
        if self.selected_user_agent:
            headers['User-Agent'] = self.selected_user_agent

        start_time = time.time()
        response = None

        try:
            response = requests.get(target, headers=headers, timeout=5, 
                                   allow_redirects=True, verify=False)
            elapsed = round(time.time() - start_time, 2)
            status = response.status_code
            size_kb = len(response.content) / 1024
            ip = get_target_ip(target)
            title = "Sem título"
            server = response.headers.get("Server", "N/D")

            if "text/html" in response.headers.get("Content-Type", "").lower():
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()[:70]
                except:
                    pass

            techs = detect_technologies(response.headers)
            color = "green" if status == 200 else "orange" if status in (301,302,307,308) else "red"

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return
        except Exception:
            return

        if self.stop_flag:
            return

        parsed = urlparse(target)
        porta = parsed.port or (443 if parsed.scheme == 'https' else 80)
        https_str = "SIM" if parsed.scheme == 'https' else "NÃO"

        result = f"[{status}] {target}\n\n"    
        result += f"    URL Final      : {response.url if response else target}\n"
        result += f"    IP             : {ip}\n"
        result += f"    Porta          : {porta}\n"
        result += f"    HTTPS          : {https_str}\n"
        result += f"    Tamanho        : {size_kb:.2f} KB\n"
        result += f"    Tipo           : {response.headers.get('Content-Type','N/D') if response else 'N/D'}\n"
        result += f"    Charset        : {response.encoding or 'N/D' if response else 'N/D'}\n"
        result += f"    Título         : {title}\n"
        result += f"    Server         : {server}\n"
        result += f"    Powered By     : {response.headers.get('X-Powered-By','N/D') if response else 'N/D'}\n"
        result += f"    Tecnologias    : {techs}\n"
        result += f"    Cookies        : {len(response.cookies) if response else 0}\n"
        result += f"    Última Mod.    : {response.headers.get('Last-Modified','N/D') if response else 'N/D'}\n"
        result += f"    Data           : {response.headers.get('Date','N/D') if response else 'N/D'}\n"
        result += f"    Cache          : {response.headers.get('Cache-Control','N/D') if response else 'N/D'}\n"
        result += f"    ETag           : {response.headers.get('ETag','N/D') if response else 'N/D'}\n"
        result += f"    Compressão     : {response.headers.get('Content-Encoding','N/D') if response else 'N/D'}\n"
        result += f"    Redirecionou   : {'SIM' if response and response.history else 'NÃO'}\n"
        result += f"    Tempo          : {elapsed:.3f} s\n"
        result += "-" * 120 + "\n\n"

        self.results_text.after(0, lambda c=color, r=result: [
            self.results_text.tag_configure(c, foreground="#53fa05" if c=="green" else "#ffaa00" if c=="orange" else "#ff4444"),
            self.results_text.insert(tk.END, r, c),
            self.results_text.yview(tk.END)
        ])

        if status in (200, 301, 302, 307, 308):
            self.found_urls.append(target)
            # ★ ATUALIZAÇÃO EM TEMPO REAL DO TOTAL ★
            self.results_text.after(0, lambda n=len(self.found_urls): 
                self.total_label.config(text=f"Total Encontrados: {n}"))

        if update_progress:
            update_progress()

    def start_scan(self):
        if self.is_running:
            return

        if not self.ip_list_path and not self.wordlist_path:
            messagebox.showerror("Erro", "Selecione ip.txt ou uma Wordlist!")
            return

        self.stop_flag = False
        self.is_running = True

        self.start_button.config(state="disabled")
        self.scan_ip_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.results_text.delete(1.0, tk.END)
        self.found_urls.clear()
        self.progress['value'] = 0

        targets = []

        if self.ip_list_path and not self.wordlist_path:
            portas_str = self.port_entry.get().strip()
            if not portas_str:
                messagebox.showerror("Erro", "Digite as portas para escanear!")
                self.stop_scan()
                return
            
            try:
                portas = [int(p.strip()) for p in portas_str.split(",") if p.strip().isdigit()]
            except:
                messagebox.showerror("Erro", "Formato de portas inválido! Use: 80,443,8080")
                self.stop_scan()
                return
            
            if not portas:
                messagebox.showerror("Erro", "Nenhuma porta válida!")
                self.stop_scan()
                return

            with open(self.ip_list_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if self.stop_flag:
                        break
                    raw = line.strip()
                    if not raw or raw.startswith('#'):
                        continue
                    
                    if '://' in raw:
                        targets.append(raw)
                    else:
                        for porta in portas:
                            if porta == 443 or porta == 8443 or porta == 9443:
                                targets.append(f"https://{raw}:{porta}")
                            else:
                                targets.append(f"http://{raw}:{porta}")
                            
        elif self.wordlist_path:
            base = self.url_entry.get().strip()
            if not base:
                messagebox.showerror("Erro", "Digite a URL base!")
                self.stop_scan()
                return
            if not base.endswith("/FUZZ"):
                base = base.rstrip("/") + "/FUZZ"
            with open(self.wordlist_path, 'r', encoding='utf-8') as f:
                for word in f:
                    if self.stop_flag:
                        break
                    word = word.strip()
                    if word:
                        targets.append(urljoin(base, word))

        if not targets:
            messagebox.showerror("Erro", "Nenhum alvo gerado.")
            self.stop_scan()
            return

        qtde = len(targets)
        completed = [0]

        def update_progress():
            completed[0] += 1
            pct = (completed[0] / qtde) * 100
            self.progress['value'] = pct
            self.progress.update_idletasks()

        def scan_thread():
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
                    self.executor = executor
                    futures = []
                    for target in targets:
                        if self.stop_flag:
                            break
                        future = executor.submit(self.check_target, target, update_progress)
                        futures.append(future)
                    
                    for future in concurrent.futures.as_completed(futures):
                        if self.stop_flag:
                            break
                        try:
                            future.result(timeout=1)
                        except:
                            pass
            finally:
                self.executor = None
                self.is_running = False
                self.root.after(0, self.scan_finished)

        threading.Thread(target=scan_thread, daemon=True).start()

    def scan_finished(self):
        self.progress['value'] = 100
        total = len(self.found_urls)
        if self.stop_flag:
            self.total_label.config(text=f"Total Encontrados: {total} (PARADO)")
        else:
            self.total_label.config(text=f"Total Encontrados: {total}")
        self.start_button.config(state="normal")
        self.scan_ip_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def save_results(self):
        """Salva apenas resultados com status 200, 301, 302, 307, 308"""
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if not filename:
            return

        texto_completo = self.results_text.get(1.0, tk.END).strip()
        if not texto_completo:
            messagebox.showwarning("Aviso", "Nada para salvar.")
            return

        # Divide o texto em blocos separados por "---"
        blocos = re.split(r'\n-{100,}\n', texto_completo)
        status_validos = {200, 301, 302, 307, 308}
        filtrados = []

        for bloco in blocos:
            bloco = bloco.strip()
            if not bloco:
                continue
            # Pega o status no início: [200], [301], etc.
            match = re.match(r'\[(\d+)\]', bloco)
            if match:
                status = int(match.group(1))
                if status in status_validos:
                    filtrados.append(bloco + "\n" + "-" * 120 + "\n")

        if not filtrados:
            messagebox.showinfo("Info", "Nenhum resultado com status 200/301/302/307/308 para salvar.")
            return

        qtde = len(filtrados)
        
        # Cria o conteúdo com o total no início
        conteudo_final = f"Total Encontrados: {qtde}\n"
        conteudo_final += "=" * 50 + "\n\n"
        conteudo_final += "\n".join(filtrados)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(conteudo_final)

        messagebox.showinfo(
            "Sucesso",
            f"Total Encontrados: {qtde}\n\n"
            f"{qtde} Resultados salvos com sucesso!\n\n"
            f"Apenas status: 200, 301, 302, 307, 308"
        )


    def limpar_resultados(self):
        if messagebox.askyesno("Confirmar Limpeza", "Deseja realmente limpar tudo?"):
            self.results_text.delete(1.0, tk.END)
            self.found_urls.clear()
            self.progress["value"] = 0
            self.total_label.config(text="Total Encontrados: 0")
            self.ip_list_path = None
            self.wordlist_path = None
            self.ip_label.config(text="ip.txt: Nenhum")
            self.word_count_label.config(text="Wordlist: Nenhum")

    def run(self):
        self.root.mainloop()

# ===================================================================
# MAIN
# ===================================================================
if __name__ == "__main__":
    app = Application()
    app.run()
