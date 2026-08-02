import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import socket
import ssl
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
import html          # ★ NOVO: para escapar caracteres no HTML 

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
# ★★★ NOVO: GERADOR DE HTML SIMPLES (abas 1, 2 e 3) ★★★
# ===================================================================
CSS_SIMPLES = """
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#c9d1d9; font-family:'Consolas','Courier New',monospace; padding:24px; }
h1 { color:#00ff88; font-family:'Segoe UI',Arial,sans-serif; font-size:22px;
     border-bottom:2px solid #30363d; padding-bottom:12px; margin-bottom:18px; }
pre { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px;
      white-space:pre-wrap; word-wrap:break-word; line-height:1.55; font-size:13px; }
.footer { color:#8b949e; font-family:'Segoe UI',Arial,sans-serif; margin-top:20px; font-size:12px; text-align:center; }
"""

def gerar_html_simples(titulo, texto):
    """Converte o conteúdo de um widget Text em uma página HTML bonita."""
    corpo = html.escape(texto)
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="dark">
<title>{html.escape(titulo)}</title>
<style>{CSS_SIMPLES}</style>
</head>
<body>
<h1>{html.escape(titulo)}</h1>
<pre>{corpo}</pre>
<div class="footer">Gerado por Recon Tool em {agora}</div>
</body>
</html>"""

# ===================================================================
# ★★★ NOVO: CSS DO RELATÓRIO HTML DO SCANNER (aba 4) ★★★
# ===================================================================
CSS_SCANNER = """
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#c9d1d9; font-family:'Segoe UI',Arial,sans-serif; padding:30px; }
.header { margin-bottom:22px; }
h1 { color:#00ff88; font-size:26px; margin-bottom:6px; }
.meta { color:#8b949e; font-size:13px; margin:3px 0; }
.meta b { color:#e8e8e8; }
.cards { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:22px; }
.card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px 20px;
        display:flex; align-items:center; gap:12px; }
.card-num { font-size:24px; font-weight:bold; color:#e8e8e8; }
.card-status { font-size:16px; font-weight:bold; font-family:Consolas,monospace; }
.table-wrap { overflow-x:auto; background:#161b22; border:1px solid #30363d;
              border-radius:8px; padding:12px; margin-bottom:24px; }
table { border-collapse:collapse; width:100%; font-size:12px; }
th { background:#0f3460; color:#00ff88; padding:10px 8px; text-align:left;
     font-size:11px; letter-spacing:0.8px; text-transform:uppercase; position:sticky; top:0; }
td { padding:8px; border-bottom:1px solid #21262d; white-space:nowrap;
     max-width:420px; overflow:hidden; text-overflow:ellipsis; }
tr:nth-child(even) td { background:#1a2029; }
tr:hover td { background:#1c2333; }
td.url a { color:#58a6ff; text-decoration:none; }
td.url a:hover { text-decoration:underline; color:#00d7ff; }
.badge { padding:3px 12px; border-radius:14px; font-family:Consolas,monospace; font-weight:bold; }
.detalhes h2 { color:#00ff88; font-size:18px; margin-bottom:10px; }
.detalhes pre { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:18px;
                white-space:pre-wrap; word-wrap:break-word; line-height:1.5; font-size:12px; }
.footer { margin-top:24px; color:#8b949e; font-size:12px; text-align:center; }
"""

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

def detect_cdn(headers):
    """Detecta CDN/WAF pelos headers (estilo HXPROBE)."""
    h = {k.lower(): v for k, v in headers.items()}
    server = h.get("server", "").lower()
    if h.get("cf-ray") or "cloudflare" in server:
        return "Cloudflare"
    if h.get("x-amz-cf-id") or "cloudfront" in server or h.get("x-amz-cdn-origin"):
        return "CloudFront"
    if "akamai" in server or h.get("x-akamai-request-id"):
        return "Akamai"
    if "fastly" in server or str(h.get("x-served-by", "")).lower().startswith("cache"):
        return "Fastly"
    if "sucuri" in server or h.get("x-sucuri-id"):
        return "Sucuri"
    if "incapsula" in server or h.get("x-iinfo"):
        return "Incapsula"
    if "imperva" in server or h.get("x-cdn"):
        return "Imperva"
    return ""

def tls_probe(host, timeout=5):
    """Extrai CN, SAN, emissor e versão TLS do certificado (estilo HXPROBE)."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                ver = ssock.version() or "?"
                cert = ssock.getpeercert()
                if not cert:
                    return f"TLS{ver}"
                cn = ""
                for k, v in cert.get("subject", ()):
                    if k == "commonName":
                        cn = v
                sans = [v for kind, v in cert.get("subjectAltName", ()) if kind == "DNS"]
                issuer = ""
                for k, v in cert.get("issuer", ()):
                    if k == "commonName":
                        issuer = v
                return f"{cn} | SAN:{len(sans)} | {issuer} | TLS{ver}"
    except Exception:
        return ""

# ===================================================================
# CLASSE PRINCIPAL - Application
# ===================================================================
class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔎 IP Real | 📧 MX | 🌍 Geo | 🌐 WHOIS Faixa de IP | 📋 CIDR | 🔗 Recon Scanner FUZZ")
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
        self.active_status_filter = set()   # ★ Filtro de status (snapshot no início do scan)

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

        # ★ TABELA MAIS VISÍVEL: linhas altas, fonte maior, cabeçalho destacado ★
        style.configure("Treeview",
                background="#0a0a0a",       # fundo preto
                fieldbackground="#0a0a0a",  # fundo das células
                foreground="#e8e8e8",       # texto claro
                rowheight=22,               # ★ linhas mais altas
                font=("Consolas", 10),      # ★ fonte maior
                borderwidth=0)
        style.configure("Treeview.Heading",
                background="#0f3460",
                foreground="#00ff88",       # ★ cabeçalho verde brilhante
                font=("Arial", 10, "bold"),
                relief="flat")
        style.map("Treeview.Heading", background=[("active", "#e94560")])

        # 🔵 BARRAS DE PROGRESSO VERDE
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor="#1a1a2e",
                        background="#00ff88",
                        lightcolor="#00ff88",
                        darkcolor="#00ff88",
                        bordercolor="#00ff88")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=2)

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

        # ★ NOVO: Botão Salvar HTML
        tk.Button(aba1, text="💾 Salvar HTML", command=self.save_aba1_html, 
                  bg="#00cc88", fg="black", font=("Arial", 10, "bold")).pack(pady=5)

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

    # ★ NOVO: Salvar aba 1 em HTML
    def save_aba1_html(self):
        global last_entrada
        texto = self.result_text.get(1.0, tk.END).strip()
        if not texto:
            messagebox.showwarning("Aviso", "Faça uma busca primeiro!")
            return
        filename = f"analise_{last_entrada}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=filename,
                                            filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(gerar_html_simples(f"🔎 Análise IP Real + MX + Geo — {last_entrada}", texto))
            messagebox.showinfo("Sucesso", f"Salvo em:\n{path}")

    # ===================================================================
    # ABA 2 - WHOIS (EXATAMENTE COMO VOCÊ PEDIU - FUNÇÕES SOLTAS)
    # ===================================================================
    def setup_aba2(self):
        aba2 = ttk.Frame(self.notebook)
        self.notebook.add(aba2, text="🌐 WHOIS Faixa de IP")

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

        # ★ NOVO: Salvar WHOIS em HTML
        def whois_salvar_html():
            texto = self.whois_text.get(1.0, tk.END).strip()
            if not texto or "Consultando" in texto:
                messagebox.showwarning("Aviso", "Faça uma consulta primeiro!")
                return

            dominio = self.entry_whois.get().strip() or "whois"
            filename = f"whois_{dominio.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"

            path = filedialog.asksaveasfilename(defaultextension=".html",
                                              initialfile=filename,
                                              filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(gerar_html_simples(f"🌐 WHOIS — {dominio}", texto))
                messagebox.showinfo("Sucesso", f"Arquivo HTML salvo em:\n{path}")

        # Botões
        btn_frame = ttk.Frame(aba2)
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="🔍 INICIAR CONSULTA", command=whois_consultar,
                  bg="#00cc00", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=10)

        tk.Button(btn_frame, text="💾 SALVAR TXT", command=whois_salvar,
                  bg="#ff8c00", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=10)

        # ★ NOVO: Botão Salvar HTML
        tk.Button(btn_frame, text="📄 SALVAR HTML", command=whois_salvar_html,
                  bg="#00cc88", fg="black", font=("Arial", 10, "bold"), width=22).pack(side="left", padx=10)

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

        # ★ NOVO: Botão Salvar HTML
        tk.Button(btn_frame3, text="Salvar HTML", command=self.salvar_cidr_html,
                  bg="#00cc88", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

    def listar_ips_cidr(self):
        listar_ips(self.entry_cidr, self.result_cidr, self.lbl_total)

    def salvar_cidr(self):
        salvar_txt(self.result_cidr)

    # ★ NOVO: Salvar CIDR em HTML
    def salvar_cidr_html(self):
        texto = self.result_cidr.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showwarning("Aviso", "Nada para salvar.")
            return
        bloco = self.entry_cidr.get().strip() or "cidr"
        arquivo = filedialog.asksaveasfilename(defaultextension=".html",
                                               initialfile=f"ips_{bloco.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                                               filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")])
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(gerar_html_simples(f"📋 Lista de IPs — {bloco}", texto))
            messagebox.showinfo("Sucesso", "Arquivo HTML salvo!")

    # ===================================================================
    # ABA 4 - Recon Scanner
    # ===================================================================
    def setup_aba4(self):
        aba4 = ttk.Frame(self.notebook)
        self.notebook.add(aba4, text="🚀 Recon Scanner FUZZ")

        tk.Label(aba4, text="🚀 Recon Scanner - Fuzzer + Scanner de IP (Portas customizáveis)", 
                 font=("Arial", 12, "bold")).pack(pady=2)

        tk.Label(aba4, text="Digite a URL (use /FUZZ no final para wordlist)", font=("Arial", 11, "bold")).pack(pady=5)
        self.url_entry = tk.Entry(aba4, width=90, font=("Consolas", 11))
        self.url_entry.pack(pady=2)
        self.url_entry.insert(0, "https://exemplo.com/FUZZ")

        ua_frame = ttk.Frame(aba4)
        ua_frame.pack(pady=2)
        tk.Button(ua_frame, text="📋 Carregar User-Agents", command=self.select_ua_file).pack(side=tk.LEFT, padx=5)
        self.ua_combo = ttk.Combobox(ua_frame, width=200, state="readonly")
        self.ua_combo.pack(side=tk.LEFT, padx=2)

        file_frame = ttk.Frame(aba4)
        file_frame.pack(pady=2)
        tk.Button(file_frame, text="📋 Wordlist", command=self.select_wordlist, bg="#03fcc6", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(file_frame, text="🌐 ip.txt", command=self.select_ip_file, bg="#ffcc00", width=15).pack(side=tk.LEFT, padx=10)

        self.word_count_label = tk.Label(aba4, text="Wordlist: Nenhum", bg="#03fcc6", fg="black", font=("Arial", 9, "bold"))
        self.word_count_label.pack(pady=2)
        self.ip_label = tk.Label(aba4, text="ip.txt: Nenhum", bg="#ffcc00", fg="black", font=("Arial", 9, "bold"))
        self.ip_label.pack(pady=2)

        # Portas
        port_frame = ttk.Frame(aba4)
        port_frame.pack(pady=2)
        ttk.Label(port_frame, text="Portas (separadas por vírgula):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.port_entry = tk.Entry(port_frame, width=40, font=("Consolas", 11, "bold"), bg="#ffffcc")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "80,443,8080,8443")

        btn_port_frame = ttk.Frame(aba4)
        btn_port_frame.pack(pady=2)

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

        # ★★★★★ FILTRO DE STATUS HTTP (NOVO) ★★★★★
        status_frame = tk.Frame(aba4, bg="#1a1a2e", bd=2, relief="groove")
        status_frame.pack(fill="x", padx=10, pady=4)

        tk.Label(status_frame, text="FILTRO DE STATUS HTTP (só exibe códigos marcados)",
                 bg="#1a1a2e", fg="#00ff88", font=("Arial", 10, "bold")).grid(
                 row=0, column=0, padx=8, pady=2, sticky="w")

        self.status_vars = {}
        codes_padrao = [200, 201, 202, 204, 301, 302, 303, 307, 308]
        for i, code in enumerate(codes_padrao):
            var = tk.BooleanVar(value=True)
            self.status_vars[code] = var
            tk.Checkbutton(status_frame, text=str(code), variable=var,
                           command=self._refresh_status_label,
                           bg="#1a1a2e", fg="#00ff88", selectcolor="#0a0a0a",
                           activebackground="#1a1a2e", activeforeground="#00ff88",
                           font=("Arial", 10, "bold"), bd=0, highlightthickness=0
                           ).grid(row=0, column=1 + i, padx=4, pady=4, sticky="w")

        tk.Label(status_frame, text="Custom:", bg="#1a1a2e", fg="#ffaa00",
                 font=("Arial", 10, "bold")).grid(row=0, column=10, padx=(15, 4), sticky="w")
        self.custom_status_entry = tk.Entry(status_frame, width=7, font=("Consolas", 10))
        self.custom_status_entry.grid(row=0, column=11, padx=4, sticky="w")
        self.custom_status_entry.insert(0, "")

        tk.Button(status_frame, text="✔ Aplicar Custom", command=self._apply_custom_status,
                  bg="#ffaa00", fg="black", font=("Arial", 9, "bold")).grid(row=0, column=12, padx=4)
        tk.Button(status_frame, text="☑ Todos", command=self._toggle_all_status,
                  bg="#00cc00", fg="black", font=("Arial", 9, "bold")).grid(row=0, column=13, padx=4)
        tk.Button(status_frame, text="☐ Nenhum", command=self._toggle_none_status,
                  bg="#ff5555", fg="white", font=("Arial", 9, "bold")).grid(row=0, column=14, padx=4)

        self.status_filter_label = tk.Label(aba4, text="", bg="#1a1a2e", fg="#00ff88",
                                            font=("Consolas", 9, "bold"))
        self.status_filter_label.pack(pady=2)
        self._refresh_status_label()

        # Botões principais
        btn_frame = ttk.Frame(aba4)
        btn_frame.pack(pady=5)

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

        # ★ NOVO: Botão Salvar HTML do scanner
        tk.Button(btn_frame, text="💾 Salvar HTML", command=self.save_results_html,
                  bg="#00cc88", fg="black", font=("Arial", 10, "bold"), width=18).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="🧹 Limpar", command=self.limpar_resultados,
                  bg="#ff4444", fg="white", font=("Arial", 12, "bold"), width=16).pack(side=tk.LEFT, padx=10)

        # ⬇️ BARRA VERDE - ABA 4
        self.progress = ttk.Progressbar(aba4, length=1056, mode="determinate",style="green.Horizontal.TProgressbar")
        self.progress.pack(pady=2) 
        
        self.total_label = tk.Label(aba4, text="Total Encontrados: 0", font=("Arial", 11, "bold"))
        self.total_label.pack(pady=2)

        # ★★★★★ TABELA DE RESULTADOS (estilo HXPROBE / httpx) ★★★★★

        table_frame = ttk.LabelFrame(
            aba4,
            text=" RESULTADOS — TABELA (httpx-style) "
        )
        table_frame.pack(fill="both", expand=True, pady=(0, 2), padx=10)

        # =====================================================
        # COLUNAS
        # =====================================================

        COLS = {
            "url":    ("URL", 500),
            "status": ("STATUS", 70),
            "title":  ("TITLE", 600),
            "length": ("SIZE", 80),
            "ctype":  ("CONTENT-TYPE", 240),
            "server": ("SERVER", 200),
            "final":  ("REDIRECT", 400),
            "tech":   ("TECHNOLOGY", 500),
            "tls":    ("TLS / SSL", 260),
            "cdn":    ("CDN", 100),
            "time":   ("TIME", 70),
        }

        self.table = ttk.Treeview(
            table_frame,
            columns=list(COLS.keys()),
            show="headings",
            selectmode="extended"
        )

        # =====================================================
        # CABEÇALHOS E COLUNAS
        # =====================================================

        for coluna, (titulo, largura) in COLS.items():

            self.table.heading(
                coluna,
                text=titulo,
                anchor="w"
            )

            self.table.column(
                coluna,
                width=largura,
                minwidth=60,
                anchor="w",
                stretch=True
            )

        tv = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        th = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=tv.set, xscrollcommand=th.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        tv.grid(row=0, column=1, sticky="ns")
        th.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.table.tag_configure("ok", foreground="#00ff41")
        self.table.tag_configure("redir", foreground="#00d7ff")
        self.table.tag_configure("warn", foreground="#ffb000")
        self.table.tag_configure("err", foreground="#ff5555")
        self.table.bind("<Button-3>", self._table_menu)

        # Detalhes (texto completo por alvo, abaixo da tabela)
        self.results_text = scrolledtext.ScrolledText(
            aba4, width=170, height=16, bg="#0a0a0a", fg="#ffffff",
            font=("Consolas", 10), wrap="none"
        )
        self.results_text.pack(pady=2, padx=10, fill="x")

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

    # ==================== FILTRO DE STATUS (NOVO) ====================
    def _get_selected_status(self):
        """Códigos marcados nos checkboxes + códigos do campo Custom."""
        codes = set()
        for code, var in self.status_vars.items():
            if var.get():
                codes.add(code)
        custom = self.custom_status_entry.get().strip()
        if custom:
            for part in custom.split(","):
                part = part.strip()
                if part.isdigit():
                    codes.add(int(part))
        return codes

    def _refresh_status_label(self):
        codes = sorted(self._get_selected_status())
        if not codes:
            self.status_filter_label.config(
                text="⚠ Filtro: nenhum código selecionado → mostra TODOS os status")
        else:
            self.status_filter_label.config(
                text="Filtro ativo: " + ", ".join(str(c) for c in codes))

    def _apply_custom_status(self):
        self._refresh_status_label()

    def _toggle_all_status(self):
        for var in self.status_vars.values():
            var.set(True)
        self._refresh_status_label()

    def _toggle_none_status(self):
        for var in self.status_vars.values():
            var.set(False)
        self._refresh_status_label()

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
            cdn = detect_cdn(response.headers)          # ★ NOVO: CDN/WAF
            tls_info = ""
            if urlparse(target).scheme == "https":      # ★ NOVO: dados TLS
                host = urlparse(target).hostname
                if host:
                    tls_info = tls_probe(host, 5)

            color = "green" if status == 200 else "orange" if status in (301,302,307,308) else "red"

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return
        except Exception:
            return

        if self.stop_flag:
            return

        # ⬇️ FILTRO DE STATUS: pula resultados fora dos códigos escolhidos
        if self.active_status_filter and status not in self.active_status_filter:
            if update_progress:
                update_progress()
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
        result += f"    CDN/WAF        : {cdn if cdn else 'N/D'}\n"
        result += f"    TLS            : {tls_info if tls_info else 'N/D'}\n"
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

        # ★★★★★ INSERE LINHA NA TABELA (estilo HXPROBE) ★★★★★
        ctype = (response.headers.get('Content-Type', 'N/D') if response else 'N/D').split(';')[0]
        length = str(len(response.content)) if response else "0"
        final_url = response.url if response and response.history else ""

        if status in (200, 201, 202, 204):
            tag = "ok"
        elif status in (301, 302, 303, 307, 308):
            tag = "redir"
        elif 400 <= status < 500:
            tag = "warn"
        else:
            tag = "err"

        row = (target, str(status), title, length, ctype, server, final_url,
               techs, tls_info, cdn, f"{elapsed*1000:.0f}ms")
        self.root.after(0, lambda r=row, t=tag: self._insert_table_row(r, t))

        # Só chega aqui quem passou no filtro de status → conta como encontrado
        self.found_urls.append(target)
        # ★ ATUALIZAÇÃO EM TEMPO REAL DO TOTAL ★
        self.results_text.after(0, lambda n=len(self.found_urls): 
            self.total_label.config(text=f"Total Encontrados: {n}"))

        if update_progress:
            update_progress()

    def _insert_table_row(self, row, tag):
        """Insere uma linha na Treeview (chamada na thread principal)."""
        self.table.insert("", "end", values=row, tags=(tag,))

    # ---- menu de contexto da tabela ----
    def _table_menu(self, event):
        iid = self.table.identify_row(event.y)
        if not iid:
            return
        self.table.selection_set(iid)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Copiar URL", command=self._copy_table_url)
        menu.add_command(label="Copiar linha inteira", command=self._copy_table_row)
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def _copy_table_url(self):
        sel = self.table.selection()
        if sel:
            vals = self.table.item(sel[0], "values")
            if vals:
                self.root.clipboard_clear()
                self.root.clipboard_append(vals[0])

    def _copy_table_row(self):
        sel = self.table.selection()
        if sel:
            vals = self.table.item(sel[0], "values")
            self.root.clipboard_clear()
            self.root.clipboard_append("\t".join(str(v) for v in vals))

    def start_scan(self):
        if self.is_running:
            return

        if not self.ip_list_path and not self.wordlist_path:
            messagebox.showerror("Erro", "Selecione ip.txt ou uma Wordlist!")
            return

        self.stop_flag = False
        self.is_running = True

        # ★ Snapshot do filtro de status (lido na thread principal = thread-safe)
        self.active_status_filter = self._get_selected_status()

        self.start_button.config(state="disabled")
        self.scan_ip_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.results_text.delete(1.0, tk.END)
        self.table.delete(*self.table.get_children())   # ★ limpa tabela
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
        """Salva apenas os blocos cujo status passou no filtro selecionado."""
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if not filename:
            return

        texto_completo = self.results_text.get(1.0, tk.END).strip()
        if not texto_completo:
            messagebox.showwarning("Aviso", "Nada para salvar.")
            return

        # ★ Filtro atual (checkboxes + custom)
        status_validos = self._get_selected_status()

        # Divide o texto em blocos separados por "---"
        blocos = re.split(r'\n-{100,}\n', texto_completo)
        filtrados = []

        for bloco in blocos:
            bloco = bloco.strip()
            if not bloco:
                continue
            # Pega o status no início: [200], [301], etc.
            match = re.match(r'\[(\d+)\]', bloco)
            if match:
                status = int(match.group(1))
                if not status_validos or status in status_validos:
                    filtrados.append(bloco + "\n" + "-" * 120 + "\n")

        if not filtrados:
            messagebox.showinfo("Info", "Nenhum resultado com os status selecionados para salvar.")
            return

        qtde = len(filtrados)
        codes_txt = ", ".join(str(c) for c in sorted(status_validos)) if status_validos else "todos"

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
            f"Filtro aplicado (status): {codes_txt}"
        )

    # ===================================================================
    # ★★★ NOVO: RELATÓRIO HTML DO SCANNER ★★★
    # ===================================================================
    def gerar_html_scanner(self):
        """Gera um relatório HTML completo a partir da tabela de resultados."""
        colunas = ["URL", "STATUS", "TITLE", "SIZE", "CONTENT-TYPE", "SERVER",
                   "REDIRECT", "TECHNOLOGY", "TLS/SSL", "CDN", "TIME"]

        rows = []
        for iid in self.table.get_children():
            values = self.table.item(iid, "values")
            if values and len(values) == len(colunas):
                rows.append([str(v) if v is not None else "" for v in values])

        if not rows:
            return None

        # Contagem por status
        status_counts = {}
        for r in rows:
            st = r[1]
            status_counts[st] = status_counts.get(st, 0) + 1

        def cor_status(status):
            try:
                s = int(status)
            except:
                return "#8b949e"
            if s < 300: return "#00ff41"   # verde
            if s < 400: return "#00d7ff"   # azul
            if s < 500: return "#ffb000"   # laranja
            return "#ff5555"               # vermelho

        # Cards de resumo por status
        cards = ""
        for st in sorted(status_counts, key=lambda x: int(x) if x.isdigit() else 999):
            cards += (f'<div class="card">'
                      f'<span class="card-num">{status_counts[st]}</span>'
                      f'<span class="card-status" style="color:{cor_status(st)}">{st}</span>'
                      f'</div>')

        # Linhas da tabela
        linhas_html = ""
        for r in rows:
            status = r[1]
            cor = cor_status(status)
            cells = ""
            for i, col in enumerate(colunas):
                valor = html.escape(r[i])
                if i == 0:  # URL clicável
                    cells += f'<td class="url"><a href="{valor}" target="_blank" rel="noopener">{valor}</a></td>'
                elif i == 1:  # Status com badge colorido
                    cells += (f'<td><span class="badge" '
                              f'style="background:{cor}22;color:{cor};border:1px solid {cor}55">{status}</span></td>')
                else:
                    cells += f'<td>{valor}</td>'
            linhas_html += f"<tr>{cells}</tr>\n"

        cabecalho = "".join(f"<th>{c}</th>" for c in colunas)

        # Detalhes completos (opcional, se houver)
        detalhes = html.escape(self.results_text.get(1.0, tk.END).strip())
        secao_detalhes = ""
        if detalhes:
            secao_detalhes = f"""
<div class="detalhes">
<h2>📄 Detalhes por alvo</h2>
<pre>{detalhes}</pre>
</div>"""

        agora = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="dark">
<title>Relatório Recon Scanner</title>
<style>{CSS_SCANNER}</style>
</head>
<body>
<div class="header">
<h1>🚀 Recon Scanner — Relatório</h1>
<div class="meta">Gerado em <b>{agora}</b></div>
<div class="meta">Total de resultados: <b>{len(rows)}</b></div>
<div class="meta">Filtro de status aplicado: <b>{", ".join(str(c) for c in sorted(self.active_status_filter)) if self.active_status_filter else "todos"}</b></div>
</div>
<div class="cards">{cards}</div>
<div class="table-wrap">
<table>
<thead><tr>{cabecalho}</tr></thead>
<tbody>
{linhas_html}
</tbody>
</table>
</div>
{secao_detalhes}
<div class="footer">Gerado por Recon Tool — uso autorizado</div>
</body>
</html>"""

    def save_results_html(self):
        """Salva os resultados do scanner em um relatório HTML bonito."""
        html_page = self.gerar_html_scanner()
        if not html_page:
            messagebox.showwarning("Aviso", "Nenhum resultado na tabela para salvar!")
            return

        alvo = self.url_entry.get().strip() or "recon"
        alvo_limpo = re.sub(r'[^\w.-]', '_', alvo)[:40]
        filename = f"relatorio_{alvo_limpo}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"

        path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=filename,
                                            filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_page)
            messagebox.showinfo("Sucesso", f"Relatório HTML salvo em:\n{path}")

    def limpar_resultados(self):
        if messagebox.askyesno("Confirmar Limpeza", "Deseja realmente limpar tudo?"):
            self.results_text.delete(1.0, tk.END)
            self.table.delete(*self.table.get_children())   # ★ limpa tabela
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
