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
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time

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
    result += "-" * 50 + "\n"

    mx_ips = []
    for mx in geo_entries:
        try:
            ip = socket.gethostbyname(mx)
            mx_ips.append(ip)
            result += f"📍 {mx} → {ip}\n"
            subprocess.run(['ping', '-4', '-n', '2', ip], capture_output=True, text=True, timeout=8)
            
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


# ===================== SEGUNDA FERRAMENTA: WHOIS =====================
traducao = {
    "domain:": "Domínio", "owner:": "Entidade", "ownerid:": "CNPJ", "responsible:": "Responsável",
    "country:": "País", "created:": "Criado em", "changed:": "Alterado em", "expires:": "Expira em",
    "status:": "Status", "nserver:": "Servidor DNS", "nameserver:": "Servidor DNS",
    "person:": "Pessoa", "e-mail:": "E-mail", "email:": "E-mail", "abuse-mailbox:": "E-mail de Abuso",
}

def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
    for f in formatos:
        try:
            return datetime.strptime(texto.strip(), f).strftime("%d/%m/%Y")
        except:
            continue
    return texto

def traduzir_linha(linha):
    linha_lower = linha.lower()
    for termo, trad in traducao.items():
        if linha_lower.startswith(termo):
            valor = linha[len(termo):].strip()
            return f"{trad:<42}: {valor}"
    if ":" in linha:
        campo, valor = linha.split(":", 1)
        return f"{campo.strip():<42}: {valor.strip()}"
    return linha

def consultar_whois(entrada):
    try:
        # ... (mesmo código do WHOIS que você forneceu, mantido completo)
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
            servidores = {'.com': 'whois.verisign-grs.com', '.net': 'whois.verisign-grs.com',
                         '.org': 'whois.pir.org', '.br': 'whois.registro.br'}
            servidor = servidores.get(tld, 'whois.arin.net')

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
        texto = re.sub(r'(Information.*?support.*?access.*?)(\n\n|\Z)', '', texto, flags=re.IGNORECASE | re.DOTALL)

        linhas = texto.splitlines()
        saida = ["=" * 90, f"WHOIS → {entrada.upper()}", "=" * 90, ""]

        for linha in linhas:
            linha = linha.strip()
            if not linha or any(x in linha.lower() for x in ['copyright', 'terms', 'usage', 'legal', 'reserved', 'icann']):
                continue
            linha = re.sub(r"\d{4}-\d{2}-\d{2}(T[\d:.Z]+)?|\d{8}", lambda m: formatar_data_brasileira(m.group()), linha)
            saida.append(traduzir_linha(linha))

        return "\n".join(saida)
    except Exception as e:
        return f"[-] Erro na consulta: {e}"

# ===================== TERCEIRA FERRAMENTA: Listador CIDR =====================
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


# ===================== INTERFACE PRINCIPAL =====================
root = tk.Tk()
root.title("🔎 IP Real   📧 Consulta MX   🌍 Geolocalização    🌐 WHOIS   📋 Listador CIDR IP   🔗 HTTPX")
root.geometry("1100x780")
root.state("zoomed")

# Notebook (Abas)
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

# (Inserir aqui todo o código da interface WHOIS que você forneceu)

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

# ==================== ABA 4 - HTTX Scanner ====================
aba4 = ttk.Frame(notebook)
notebook.add(aba4, text="🚀 HTTX Scanner")

# ==================== VARIÁVEIS GLOBAIS ====================
HEADERS_BASE = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

user_agents_list = []
selected_user_agent = None
wordlist_path = None
ip_list_path = None
found_urls = []

# ==================== FUNÇÕES DO SCANNER ====================
def get_target_ip(target):  # ← RENOMEADA para evitar conflito
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
        "cloudflare": "Cloudflare",
        "nginx": "Nginx",
        "apache": "Apache",
        "iis": "Microsoft IIS",
        "microsoft-iis": "Microsoft IIS",
        "litespeed": "LiteSpeed",
        "openresty": "OpenResty",
        "caddy": "Caddy",
        "gunicorn": "Gunicorn",
        "uwsgi": "uWSGI",
        "tomcat": "Apache Tomcat",
        "jetty": "Jetty",
        "node": "Node.js",
        "express": "Express.js",
        "asp.net": "ASP.NET",
        "aspnet": "ASP.NET",
        "php": "PHP",
        "laravel": "Laravel",
        "wordpress": "WordPress",
        "joomla": "Joomla",
        "drupal": "Drupal",
        "magento": "Magento",
        "shopify": "Shopify",
        "woocommerce": "WooCommerce",
        "prestashop": "PrestaShop",
        "cpanel": "cPanel",
        "plesk": "Plesk",
        "varnish": "Varnish Cache",
        "haproxy": "HAProxy",
        "envoy": "Envoy",
        "cloudfront": "CloudFront",
        "akamai": "Akamai",
        "fastly": "Fastly",
        "sucuri": "Sucuri WAF",
        "imperva": "Imperva WAF",
        "f5": "F5 BIG-IP",
        "mod_security": "ModSecurity",
        "modsecurity": "ModSecurity",
        "kestrel": "Kestrel",
        "oracle": "Oracle",
        "jboss": "JBoss",
        "wildfly": "WildFly",
        "weblogic": "WebLogic",
        "websphere": "WebSphere",
        "firebase": "Firebase",
        "netlify": "Netlify",
        "vercel": "Vercel",
        "heroku": "Heroku"
    }

    for chave, nome in tecnologias.items():
        if chave in h and nome not in techs:
            techs.append(nome)
    return " | ".join(techs) if techs else "N/D"

def check_target(target, results_text, update_progress):
    global selected_user_agent
    headers = HEADERS_BASE.copy()
    if selected_user_agent:
        headers['User-Agent'] = selected_user_agent

    start_time = time.time()
    response = None
    server = "N/D"

    try:
        response = requests.get(target, headers=headers, timeout=8, allow_redirects=True)
        elapsed = round(time.time() - start_time, 2)
        status = response.status_code
        size_kb = len(response.content) / 1024
        ip = get_target_ip(target)          # ← Usando a função renomeada
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

    except Exception:
        elapsed = round(time.time() - start_time, 2)
        status = "ERROR"
        size_kb = 0
        ip = get_target_ip(target)
        title = "Sem resposta"
        techs = "N/D"
        color = "red"

    # Resultado Rico
    result = f"[{status}] {target}\n\n"    
    result += f"    URL Final      : {response.url if response else target}\n"
    result += f"    IP             : {ip}\n"
    result += f"    Porta          : {443 if target.startswith('https') else 80}\n"
    result += f"    HTTPS          : {'SIM' if target.startswith('https') else 'NÃO'}\n"
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

    results_text.after(0, lambda c=color, r=result: [
        results_text.tag_configure(c, foreground="#53fa05" if c=="green" else "#ffaa00" if c=="orange" else "#ff4444"),
        results_text.insert(tk.END, r, c),
        results_text.yview(tk.END)
    ])

    if status in (200, 301, 302, 307, 308):
        found_urls.append(target)

    update_progress()

def save_results(results_text):
    filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(results_text.get(1.0, tk.END))
        messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")

# ==================== FUNÇÕES DO SCANNER limpar tudo ====================
def limpar_resultados():
    global ip_list_path, wordlist_path

    if messagebox.askyesno("Confirmar Limpeza", "Deseja realmente limpar tudo?"):

        # Limpa resultados
        results_text_scanner.delete(1.0, tk.END)

        # Limpa lista de URLs encontradas
        found_urls.clear()

        # Zera progresso
        progress["value"] = 0

        # Zera contador
        total_label.config(text="Total Encontrados: 0")

        # Remove os arquivos selecionados
        ip_list_path = None
        wordlist_path = None

        # Atualiza as labels
        ip_label.config(text="ip.txt: Nenhum")
        word_count_label.config(text="Wordlist: Nenhum")

        # Mantém a URL digitada

        results_text_scanner.update_idletasks()
    
# ==================== INTERFACE ====================
tk.Label(aba4, text="🚀 HTTX Scanner - Fuzzer + Scanner de IP", 
         font=("Arial", 16, "bold")).pack(pady=10)

tk.Label(aba4, text="URL Base (use /FUZZ no final para wordlist):", font=("Arial", 11, "bold")).pack(pady=5)
url_entry = tk.Entry(aba4, width=90, font=("Consolas", 11))
url_entry.pack(pady=5)
url_entry.insert(0, "https://exemplo.com/FUZZ")

ua_frame = ttk.Frame(aba4)
ua_frame.pack(pady=8)
tk.Button(ua_frame, text="📋 Carregar User-Agents", command=lambda: select_ua_file()).pack(side=tk.LEFT, padx=5)
ua_combo = ttk.Combobox(ua_frame, width=80, state="readonly")
ua_combo.pack(side=tk.LEFT, padx=5)

file_frame = ttk.Frame(aba4)
file_frame.pack(pady=10)
tk.Button(file_frame, text="📋 Wordlist", command=lambda: select_wordlist(), bg="#03fcc6", width=15).pack(side=tk.LEFT, padx=10)
tk.Button(file_frame, text="🌐 ip.txt", command=lambda: select_ip_file(), bg="#ffcc00", width=15).pack(side=tk.LEFT, padx=10)

word_count_label = tk.Label(aba4, text="Wordlist: Nenhum", bg="#03fcc6", fg="black", font=("Arial", 9, "bold"))
word_count_label.pack(pady=5)
ip_label = tk.Label(aba4, text="ip.txt: Nenhum", bg="#ffcc00", fg="black", font=("Arial", 9, "bold"))
ip_label.pack(pady=5)

# ==================== BOTÕES ====================
btn_frame = ttk.Frame(aba4)
btn_frame.pack(pady=15)

start_button = tk.Button(btn_frame, text="🚀 INICIAR FUZZ",
                        command=lambda: start_scan(),
                        bg="#00FF00", font=("Arial", 12, "bold"), width=22)
start_button.pack(side=tk.LEFT, padx=10)

scan_ip_button = tk.Button(btn_frame, text="🔍 SCAN IP (http+https)",
                          command=lambda: start_scan_ip(),
                          bg="#00AAFF", fg="white", font=("Arial", 12, "bold"), width=28)
scan_ip_button.pack(side=tk.LEFT, padx=10)

tk.Button(btn_frame, text="💾 Salvar Resultados",
          command=lambda: save_results(results_text_scanner),
          bg="#ff8c00", width=20).pack(side=tk.LEFT, padx=10)

# ==================== NOVO BOTÃO: LIMPAR TUDO ====================
tk.Button(btn_frame, text="🧹 Limpar Tudo",
          command=lambda: limpar_resultados(),
          bg="#ff4444", fg="white", font=("Arial", 12, "bold"), width=20).pack(side=tk.LEFT, padx=10)

# ==================== PROGRESSO E TOTAL ====================
progress = ttk.Progressbar(aba4, length=1100, mode="determinate")
progress.pack(pady=10)

total_label = tk.Label(aba4, text="Total Encontrados: 0", font=("Arial", 12, "bold"))
total_label.pack(pady=5)

results_text_scanner = scrolledtext.ScrolledText(
    aba4, width=170, height=28, bg="#0a0a0a", fg="#ffffff",
    font=("Consolas", 10), wrap="none"
)
results_text_scanner.pack(pady=10, padx=10, fill="both", expand=True)

# ==================== FUNÇÕES AUXILIARES ====================
def select_ua_file():
    global user_agents_list, selected_user_agent
    ua_file = filedialog.askopenfilename(title="User-Agents.txt", filetypes=[("TXT", "*.txt")])
    if ua_file:
        with open(ua_file, 'r', encoding='utf-8') as f:
            user_agents_list[:] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        ua_combo['values'] = user_agents_list
        if user_agents_list:
            ua_combo.current(0)
            selected_user_agent = user_agents_list[0]

def select_wordlist():
    global wordlist_path
    wordlist_path = filedialog.askopenfilename(title="Wordlist", filetypes=[("TXT", "*.txt")])
    if wordlist_path:
        with open(wordlist_path, 'r', encoding='utf-8') as f:
            count = sum(1 for line in f if line.strip())
        word_count_label.config(text=f"Wordlist: {count} palavras")

def select_ip_file():
    global ip_list_path
    ip_list_path = filedialog.askopenfilename(title="ip.txt", filetypes=[("TXT", "*.txt")])
    if ip_list_path:
        with open(ip_list_path, 'r', encoding='utf-8') as f:
            count = sum(1 for line in f if line.strip())
        ip_label.config(text=f"ip.txt: {count} IPs")

def start_scan_ip():
    global wordlist_path
    wordlist_path = None
    start_scan()

def start_scan():
    global ip_list_path, wordlist_path

    if not ip_list_path and not wordlist_path:
        messagebox.showerror("Erro", "Selecione ip.txt ou uma Wordlist!")
        return

    start_button.config(state="disabled")
    scan_ip_button.config(state="disabled")

    results_text_scanner.delete(1.0, tk.END)
    found_urls.clear()
    progress['value'] = 0

    targets = []

    if ip_list_path and not wordlist_path:   # Modo IP
        with open(ip_list_path, 'r', encoding='utf-8') as f:
            for line in f:
                ip = line.strip()
                if ip and not ip.startswith('#'):
                    targets.append(f"http://{ip}")
                    targets.append(f"https://{ip}")
    elif wordlist_path:   # Modo Fuzz
        base = url_entry.get().strip()
        if not base:
            messagebox.showerror("Erro", "Digite a URL base!")
            start_button.config(state="normal")
            scan_ip_button.config(state="normal")
            return
        if not base.endswith("/FUZZ"):
            base = base.rstrip("/") + "/FUZZ"
        with open(wordlist_path, 'r', encoding='utf-8') as f:
            for word in f:
                word = word.strip()
                if word:
                    targets.append(urljoin(base, word))

    if not targets:
        messagebox.showerror("Erro", "Nenhum alvo gerado.")
        start_button.config(state="normal")
        scan_ip_button.config(state="normal")
        return

    def update_progress():
        progress['value'] += (100.0 / len(targets))
        progress.update_idletasks()

    def scan_thread():
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
                for target in targets:
                    executor.submit(check_target, target, results_text_scanner, update_progress)
        finally:
            progress['value'] = 100
            total_label.config(text=f"Total Encontrados: {len(found_urls)}")
            start_button.config(state="normal")
            scan_ip_button.config(state="normal")

    threading.Thread(target=scan_thread, daemon=True).start()

root.mainloop()
