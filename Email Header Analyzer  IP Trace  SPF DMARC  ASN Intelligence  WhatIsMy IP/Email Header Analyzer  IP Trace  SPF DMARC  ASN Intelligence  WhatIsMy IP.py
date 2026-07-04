import re
import requests
from datetime import datetime
import threading
import webbrowser
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import quote

# ====================== VARIÁVEIS GLOBAIS ======================
risk_score = 0
is_processing = False
last_ip_found = None
last_asn_found = None

# ====================== FUNÇÕES DE BACKEND ======================
def format_header(header_text):
    lines = header_text.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        line = line.strip()
        if line == "":
            if not prev_empty:
                cleaned.append("")
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    return '\n'.join(cleaned).strip()


def extract_email_from_header(header_content):
    patterns = [
        r'return-path:\s*<(.+?)>', 
        r'delivered-to:\s*(.+?)(?:\s|$)',
        r'to:\s*.*<(.+?)>',
        r'from:\s*.*<(.+?)>',
        r'X-Original-Recipient:\s*(.+?)(?:\s|$)'
    ]
    for pattern in patterns:
        match = re.search(pattern, header_content, re.IGNORECASE)
        if match:
            email = match.group(1).strip()
            if '@' in email:
                return email
    return None


def get_ip_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,query,as"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == 'fail':
            return {"error": data.get('message', 'IP inválido')}
        
        asn = data.get('as', 'N/A')
        asn_number = asn.split()[0] if asn and asn.startswith('AS') else 'N/A'
            
        return {
            "ip": ip,
            "country": data.get('country', 'N/A'),
            "region": data.get('regionName', 'N/A'),
            "city": data.get('city', 'N/A'),
            "isp": data.get('isp') or data.get('org', 'N/A'),
            "asn": asn_number
        }
    except Exception as e:
        return {"error": f"Falha de conexão: {str(e)[:80]}"}


def check_dns_records(domain, record_type):
    try:
        query_domain = f"_dmarc.{domain}" if record_type == 'DMARC' else domain
        url = f"https://dns.google/resolve?name={query_domain}&type=TXT"
        resp = requests.get(url, timeout=6)
        data = resp.json()
        records = []
        if data.get('Status') == 0:
            for ans in data.get('Answer', []):
                txt = ans.get('data', '').replace('"', '').replace("'", "")
                records.append(txt)
        return records
    except Exception:
        return []


def extract_header_info(header_content):
    ips = set()
    for line in header_content.split('\n'):
        if "Received:" in line:
            ip_matches = re.findall(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]', line)
            ip6_matches = re.findall(r'\[([a-fA-F0-9:]+)\]', line)
            for ip in ip_matches + ip6_matches:
                if not ip.startswith(("192.168.", "10.", "172.16.")) and not ip.startswith("fd"):
                    ips.add(ip)
    return list(ips)


def analyze_email_structure(email):
    try:
        user, domain = email.split('@')
    except ValueError:
        return 3, "Formato inválido"

    is_long = len(user) > 12
    has_numbers = any(char.isdigit() for char in user)
    numeric_ratio = sum(c.isdigit() for c in user) / len(user) if user else 0

    trusted_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com', 'protonmail.com',
                       'mail.ru', 'icloud.com', 'me.com', 'aol.com', 'gmx.com', 'gmx.net',
                       'zoho.com', 'yandex.com', 'tutanota.com', 'live.com', 'msn.com']

    risk = 0
    if is_long and has_numbers: 
        risk += 2
    if numeric_ratio > 0.5: 
        risk += 2
    if domain.lower() not in trusted_domains:
        risk += 1

    desc = "Suspeito (Padrão Aleatório)" if risk >= 3 else "Padrão Humano"
    return risk, desc


def log_msg(text_area, msg, color="white"):
    text_area.config(state=NORMAL)
    timestamp = datetime.now().strftime('%H:%M:%S')
    text_area.insert(END, f"[{timestamp}] {msg}\n", color)
    text_area.config(state=DISABLED)
    text_area.see(END)


def update_progress(progress_bar, value):
    progress_bar['value'] = value
    root.update_idletasks()

# ====================== FUNÇÕES DE DESTAQUE ======================
def highlight_emails():
    header_entry.tag_remove("email", "1.0", END)
    text = header_entry.get("1.0", END)
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    for match in re.finditer(email_pattern, text):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        header_entry.tag_add("email", start, end)


def highlight_ips():
    header_entry.tag_remove("IP", "1.0", END)
    text = header_entry.get("1.0", END)
    
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    for match in re.finditer(ipv4_pattern, text):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        header_entry.tag_add("IP", start, end)
    
    ipv6_pattern = r'\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b|\b(?:[a-fA-F0-9]{1,4}:){1,7}:\b'
    for match in re.finditer(ipv6_pattern, text):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        header_entry.tag_add("IP", start, end)


def auto_format_header(event=None):
    current = header_entry.get("1.0", END)
    formatted = format_header(current)
    if formatted != current.strip():
        header_entry.delete("1.0", END)
        header_entry.insert("1.0", formatted)
    highlight_emails()
    highlight_ips()

# ====================== FUNÇÕES DE BOTÕES ======================
def open_hibp():
    email = email_var.get().strip()
    if "@" not in email:
        messagebox.showwarning("Aviso", "Digite um email ou cole um cabeçalho!")
        return
    webbrowser.open(f"https://haveibeenpwned.com/account/{email}")
    log_msg(text_area, f"🔎 Have I Been Pwned aberto para: {email}", "cyan")


def open_google_dork():
    email = email_var.get().strip()
    if "@" not in email:
        messagebox.showwarning("Aviso", "Digite um email ou cole um cabeçalho!")
        return
    encoded = quote(email)
    webbrowser.open(f"https://www.google.com/search?q=%22{encoded}%22")
    log_msg(text_area, f"🔎 Google Dork aberto para: {email}", "cyan")


def open_virustotal_ip():
    global last_ip_found
    if not last_ip_found:
        messagebox.showwarning("Aviso", "Nenhum IP encontrado ainda.")
        return
    webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{last_ip_found}")
    log_msg(text_area, f"🌐 VirusTotal aberto para IP: {last_ip_found}", "cyan")


def open_bgp_he_net_ip():
    global last_ip_found
    if not last_ip_found:
        messagebox.showwarning("Aviso", "Nenhum IP encontrado ainda.")
        return
    webbrowser.open(f"https://bgp.he.net/ip/{last_ip_found}")
    log_msg(text_area, f"🌐 BGP.he.net IP aberto: {last_ip_found}", "cyan")


def open_bgp_he_net_asn():
    global last_asn_found
    if not last_asn_found or last_asn_found == "N/A":
        messagebox.showwarning("Aviso", "Nenhum ASN encontrado ainda.")
        return
    webbrowser.open(f"https://bgp.he.net/{last_asn_found}")
    log_msg(text_area, f"🌐 BGP.he.net ASN aberto: {last_asn_found}", "cyan")


def open_abuseipdb():
    global last_ip_found
    if not last_ip_found:
        messagebox.showwarning("Aviso", "Nenhum IP encontrado ainda.")
        return
    webbrowser.open(f"https://www.abuseipdb.com/check/{last_ip_found}")
    log_msg(text_area, f"🌐 AbuseIPDB aberto para IP: {last_ip_found}", "cyan")


def open_whatismyip_map():
    global last_ip_found
    if not last_ip_found:
        messagebox.showwarning("Aviso", "Nenhum IP encontrado ainda.")
        return
    webbrowser.open(f"https://whatismyip.com.br/map.php?query={last_ip_found}")
    log_msg(text_area, f"🌍 WhatIsMyIP Map aberto para: {last_ip_found}", "cyan")


# ====================== FUNÇÃO PARA COLORIR HTML ======================
def colorize_content(text):
    text = re.sub(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', 
                 r'<span class="email">\1</span>', text)
    text = re.sub(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', 
                 r'<span class="ip">\1</span>', text)
    text = re.sub(r'\b([a-fA-F0-9]{1,4}(:[a-fA-F0-9]{1,4}){1,7})\b', 
                 r'<span class="ip">\1</span>', text)
    text = re.sub(r'(RISCO FINAL: ALTO)', r'<span class="risk-alto">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(RISCO FINAL: MÉDIO)', r'<span class="risk-medio">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(RISCO FINAL: BAIXO)', r'<span class="risk-baixo">\1</span>', text, flags=re.IGNORECASE)
    return text


def save_results():
    log_content = text_area.get("1.0", END).strip()
    header_content = header_entry.get("1.0", END).strip()
    email = email_var.get().strip() or "Não informado"

    if not log_content and not header_content:
        messagebox.showwarning("Aviso", "Não há resultados para salvar!")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
    )
    if not file_path:
        return

    colored_log = colorize_content(log_content)
    colored_header = format_header(header_content).replace('<', '&lt;').replace('>', '&gt;')
    colored_header = colorize_content(colored_header)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MailTrace OSINT - Relatório</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 0 25px rgba(0,0,0,0.7); }}
        h1 {{ color: #ff5555; text-align: center; margin-bottom: 5px; }}
        h2 {{ color: #50fa7b; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .section {{ background: #282a36; padding: 18px; border-radius: 10px; margin: 18px 0; }}
        pre {{ background: #282a36; padding: 18px; border-radius: 8px; overflow-x: auto; line-height: 1.5; white-space: pre-wrap; }}
        .email {{ color: #50fa7b; font-weight: bold; }}
        .ip {{ color: #0bf0f8; font-weight: bold; }}
        .risk-alto {{ color: #ff5555; font-weight: bold; font-size: 1.1em; }}
        .risk-medio {{ color: #f1fa8c; font-weight: bold; }}
        .risk-baixo {{ color: #50fa7b; font-weight: bold; }}
        footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 Email Header Analyzer Email - OSINT - Relatório de Análise Email</h1>
        <p style="text-align:center; color:#8be9fd; font-size:1.1em;">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
        
        <h2>📧 Email Analisado</h2>
        <div class="section"><strong style="color:#ff79c6;">{email}</strong></div>

        <h2>📋 Cabeçalho Completo</h2>
        <div class="section">
            <pre>{colored_header}</pre>
        </div>

        <h2>📊 Log Completo da Análise</h2>
        <div class="section">
            <pre>{colored_log}</pre>
        </div>

        <footer>
            <p>Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence  WhatIsMy IP</p>
        </footer>
    </div>
</body>
</html>"""

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        messagebox.showinfo("Sucesso", f"Relatório HTML salvo com sucesso!\n\n{file_path}")
        if messagebox.askyesno("Abrir relatório?", "Deseja abrir o relatório no navegador agora?"):
            webbrowser.open(f"file://{file_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar:\n{str(e)}")

# ====================== thread ======================
def analysis_thread(email, header_raw, text_area, progress_bar, analyze_btn):
    global risk_score, last_ip_found, last_asn_found
    
    risk_score = 0
    last_ip_found = None
    last_asn_found = None

    try:
        log_msg(text_area, f"Iniciando análise para: {email}\n", "azul_neon")
        update_progress(progress_bar, 10)

        if header_raw:
            ips = extract_header_info(header_raw)
            if ips:
                last_ip_found = ips[0]
                log_msg(text_area, f"IP Encontrados: {', '.join(ips)}\n", "green")
                
                geo = get_ip_info(ips[0])
                if "error" not in geo:
                    last_asn_found = geo.get('asn', 'N/A')
                    log_msg(text_area, f"Local: {geo['city']}, {geo['region']}, {geo['country']}\n", "green")
                    log_msg(text_area, f"ISP: {geo['isp']}\n", "green")
                    log_msg(text_area, f"ASN: {last_asn_found}\n", "cyan")
                else:
                    log_msg(text_area, f"Geolocalização: {geo['error']}\n", "red")
        
        update_progress(progress_bar, 45)

        domain = email.split('@')[1]
        log_msg(text_area, f"Verificando domínio: {domain}\n", "laranja")

        spf_records = check_dns_records(domain, 'SPF')
        dmarc_records = check_dns_records(domain, 'DMARC')

        has_spf = any("v=spf1" in r.lower() for r in spf_records)
        has_dmarc = any("v=dmarc1" in r.lower() for r in dmarc_records)

        if has_spf:
            log_msg(text_area, "SPF: Configurado ✓", "green")
        else:
            log_msg(text_area, "SPF: Não configurado (Risco Alto)", "red")
            risk_score += 2

        if has_dmarc:
            log_msg(text_area, "DMARC: Configurado ✓\n", "green")
        else:
            log_msg(text_area, "DMARC: Não configurado\n", "red")
            risk_score += 1

        update_progress(progress_bar, 75)

        struct_risk, struct_desc = analyze_email_structure(email)
        risk_score += struct_risk
        log_msg(text_area, f"Estrutura: {struct_desc} (Risco +{struct_risk})\n", "yellow")

        if risk_score >= 5:
            final_risk, color = "ALTO", "red"
        elif risk_score >= 3:
            final_risk, color = "MÉDIO", "yellow"
        else:
            final_risk, color = "BAIXO", "green"

        log_msg(text_area, f"RISCO FINAL: {final_risk} (Score: {risk_score})\n", color)
        update_progress(progress_bar, 100)

    except Exception as e:
        log_msg(text_area, f"Erro durante a análise: {e}\n", "red")
        update_progress(progress_bar, 100)
    finally:
        global is_processing
        is_processing = False
        analyze_btn.config(state=NORMAL)

def start_analysis():
    global is_processing
    if is_processing:
        return

    email = email_var.get().strip()
    header_raw = header_entry.get("1.0", END).strip()

    if not email or "@" not in email:
        extracted = extract_email_from_header(header_raw)
        if extracted:
            email = extracted
            email_var.set(email)
            log_msg(text_area, f"Email extraído do cabeçalho: {email}", "cyan")
        else:
            messagebox.showerror("Erro", "Insira um email válido ou cole um cabeçalho com endereço.")
            return

    is_processing = True
    analyze_btn.config(state=DISABLED)

    progress_bar['value'] = 0
    text_area.config(state=NORMAL)
    text_area.delete(1.0, END)
    text_area.config(state=DISABLED)

    thread = threading.Thread(target=analysis_thread, 
                              args=(email, header_raw, text_area, progress_bar, analyze_btn),
                              daemon=True)
    thread.start()


# ====================== INTERFACE GRÁFICA ======================
root = Tk()
root.title("Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence  WhatIsMy IP")
root.geometry("1000x800")
root.state('zoomed')
root.configure(bg="#1e1e1e")

email_var = StringVar()

main_frame = Frame(root, bg="#1e1e1e", padx=15, pady=15)
main_frame.pack(fill=BOTH, expand=True)

Label(main_frame, text="Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence  WhatIsMy IP", 
      font=("Segoe UI", 16, "bold"), fg="#ff5555", bg="#1e1e1e").pack(pady=3)

frame_email = Frame(main_frame, bg="#1e1e1e")
frame_email.pack(fill=X, pady=8)
Label(frame_email, text="Email Alvo", fg="white", bg="#1e1e1e").pack(side=LEFT)
Entry(frame_email, textvariable=email_var, font=("Consolas", 11), bg="#282a36", fg="#f8f8f2",
      insertbackground="white", relief="flat").pack(side=LEFT, fill=X, expand=True, padx=2)

Label(main_frame, text="Cole o Cabeçalho Completo do Email", fg="white", bg="#1e1e1e").pack(anchor=W, pady=(12, 5))

header_entry = scrolledtext.ScrolledText(
    main_frame, height=18, bg="#282a36", fg="#FFFFFF", insertbackground="#FFFFFF",
    selectbackground="#44475a", selectforeground="#FFFFFF", font=("Consolas", 11), wrap=WORD
)
header_entry.pack(fill=BOTH, expand=True, pady=2)

header_entry.tag_configure("email", foreground="#50fa7b")
header_entry.tag_configure("IP", foreground="#0bf0f8")

header_entry.bind("<KeyRelease>", lambda e: (highlight_emails(), highlight_ips()))
header_entry.bind("<FocusOut>", auto_format_header)

btn_frame = Frame(main_frame, bg="#1e1e1e")
btn_frame.pack(pady=10)

analyze_btn = Button(btn_frame, text="ANALISAR EMAIL", command=start_analysis, bg="#0aec1d", fg="#282a36",
                     font=("Segoe UI", 10, "bold"), height=2, width=16)
analyze_btn.pack(side=LEFT, padx=2)

#botões

Button(btn_frame, text="Have I Been Pwned Email", command=open_hibp, bg="#1865f5", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=20).pack(side=LEFT, padx=2)

Button(btn_frame, text="Google Dork", command=open_google_dork, bg="#79ffde", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=LEFT, padx=2)

Button(btn_frame, text="VirusTotal IP", command=open_virustotal_ip, bg="#098b81", fg="#0A0A0A",
       font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=LEFT, padx=2)

Button(btn_frame, text="BGP.he.net IP", command=open_bgp_he_net_ip, bg="#ffb86c", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=LEFT, padx=2)

Button(btn_frame, text="BGP.he.net ASN", command=open_bgp_he_net_asn, bg="#b47808", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=14).pack(side=LEFT, padx=2)

Button(btn_frame, text="AbuseIPDB IP", command=open_abuseipdb, bg="#ff79c6", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=14).pack(side=LEFT, padx=2)

Button(btn_frame, text="WhatIsMy IP MAP", command=open_whatismyip_map, bg="#cee7eb", fg="#282a36",
    font=("Segoe UI", 10, "bold"), height=2, width=16).pack(side=LEFT, padx=2)

# Botão Salvar agora salva como HTML
Button(btn_frame, text="💾 Salvar Relatório HTML", command=save_results, bg="#f83909", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=20).pack(side=LEFT, padx=2)

progress_frame = Frame(main_frame, bg="#1e1e1e")
progress_frame.pack(fill=X, pady=5)
Label(progress_frame, text="Progresso", fg="white", bg="#1e1e1e").pack(side=LEFT, padx=(0,8))
progress_bar = ttk.Progressbar(progress_frame, length=650, mode='determinate')
progress_bar.pack(side=LEFT, fill=X, expand=True)

Label(main_frame, text="Log de Análise", fg="white", bg="#1e1e1e").pack(anchor=W, pady=(10, 2))
text_area = scrolledtext.ScrolledText(main_frame, height=18, bg="#282a36", fg="#f8f8f2", font=("Consolas", 11))
text_area.pack(fill=BOTH, expand=True, pady=1)

for color, hexcolor in [("red", "#ff5555"), ("green", "#50fa7b"), ("yellow", "#f1fa8c"),
                        ("cyan", "#8be9fd"), ("white", "#f8f8f2"), ("azul_neon", "#00BFFF"), 
                        ("laranja", "#fca762")]:
    text_area.tag_configure(color, foreground=hexcolor)

Label(main_frame, text="Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence  WhatIsMy IP", 
      fg="#05b90e", bg="#1e1e1e").pack(pady=5)

root.mainloop()
