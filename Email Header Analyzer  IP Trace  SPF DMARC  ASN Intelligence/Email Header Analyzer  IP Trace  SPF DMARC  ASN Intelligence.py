import re
import requests
from datetime import datetime
import threading
import webbrowser
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import quote

# --- Configuração da Interface ---
root = Tk()
root.title("Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence") 
root.geometry("1000x800")
root.state('zoomed')
root.configure(bg="#1e1e1e")

# Variáveis globais
email_var = StringVar()
risk_score = 0
is_processing = False
last_ip_found = None
last_asn_found = None

# --- Funções de Backend ---

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
        if asn and asn.startswith('AS'):
            asn_number = asn.split()[0]
        else:
            asn_number = 'N/A'
            
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
        line = line.strip()
        if "Received:" in line:
            ip_matches = re.findall(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]', line)
            for ip in ip_matches:
                if not ip.startswith(("192.168.", "10.", "172.16.")):
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

    # Lista expandida de provedores confiáveis
    trusted_domains = [
        'gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com', 'protonmail.com', 
        'mail.ru', 'icloud.com', 'me.com', 'aol.com', 'gmx.com', 'gmx.net',
        'zoho.com', 'yandex.com', 'tutanota.com', 'live.com', 'msn.com',
        'yahoo.co.jp', 'yahoo.fr', 'yahoo.co.uk', 'outlook.fr', 'outlook.de'
    ]

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


def open_hibp():
    email = email_var.get().strip()
    if "@" not in email:
        messagebox.showwarning("Aviso", "Digite um email ou cole um cabeçalho!")
        return
    webbrowser.open(f"https://haveibeenpwned.com/account/{email}")


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
        messagebox.showwarning("Aviso", "Nenhum IP encontrado ainda. Faça uma análise primeiro.")
        return
    webbrowser.open(f"https://www.abuseipdb.com/check/{last_ip_found}")
    log_msg(text_area, f"🌐 AbuseIPDB aberto para IP: {last_ip_found}", "cyan")


def auto_format_header(event=None):
    current = header_entry.get("1.0", END)
    formatted = format_header(current)
    if formatted != current.strip():
        header_entry.delete("1.0", END)
        header_entry.insert(END, formatted)


def save_results():
    content = text_area.get("1.0", END).strip()
    if not content:
        messagebox.showwarning("Aviso", "Não há resultados para salvar!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"MailTrace OSINT - Relatório\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(content)
            messagebox.showinfo("Sucesso", f"Salvo em:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))


def analysis_thread(email, header_raw, text_area, progress_bar, analyze_btn):
    global risk_score, is_processing, last_ip_found, last_asn_found
    risk_score = 0
    last_ip_found = None
    last_asn_found = None
    try:
        log_msg(text_area, f"Iniciando análise para: {email}", "cyan")
        update_progress(progress_bar, 10)

        struct_risk, struct_desc = analyze_email_structure(email)
        risk_score += struct_risk
        log_msg(text_area, f"Estrutura: {struct_desc} (Risco +{struct_risk})", "yellow")
        update_progress(progress_bar, 30)

        if header_raw:
            log_msg(text_area, "Processando cabeçalho...", "white")
            ips = extract_header_info(header_raw)
            if ips:
                last_ip_found = ips[0]
                log_msg(text_area, f"IP Encontrados: {', '.join(ips)}", "green")
                
                geo = get_ip_info(ips[0])
                if "error" not in geo:
                    last_asn_found = geo.get('asn', 'N/A')
                    log_msg(text_area, f"Local: {geo['city']}, {geo['region']}, {geo['country']}", "green")
                    log_msg(text_area, f"ISP: {geo['isp']}", "green")
                    log_msg(text_area, f"ASN: {last_asn_found}", "cyan")
                else:
                    log_msg(text_area, f"Geolocalização: {geo['error']}", "red")

        update_progress(progress_bar, 70)
        domain = email.split('@')[1]
        log_msg(text_area, f"Verificando domínio: {domain}", "white")

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
            log_msg(text_area, "DMARC: Configurado ✓", "green")
        else:
            log_msg(text_area, "DMARC: Não configurado", "yellow")
            risk_score += 1

        update_progress(progress_bar, 100)

        if risk_score >= 5:
            final_risk, color = "ALTO", "red"
        elif risk_score >= 3:
            final_risk, color = "MÉDIO", "yellow"
        else:
            final_risk, color = "BAIXO", "green"

        log_msg(text_area, f"RISCO FINAL: {final_risk} (Score: {risk_score})", color)

    except Exception as e:
        log_msg(text_area, f"Erro: {e}", "red")
    finally:
        is_processing = False
        analyze_btn.config(state=NORMAL)


def start_analysis():
    global is_processing
    if is_processing: return

    email = email_var.get().strip()
    header_raw = header_entry.get("1.0", END).strip()

    if not email or "@" not in email:
        extracted = extract_email_from_header(header_raw)
        if extracted:
            email = extracted
            email_var.set(email)
            log_msg(text_area, f"Email extraído: {email}", "cyan")
        else:
            messagebox.showerror("Erro", "Insira um email ou cole um cabeçalho com endereço válido.")
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


# ====================== INTERFACE ======================

main_frame = Frame(root, bg="#1e1e1e", padx=15, pady=15)
main_frame.pack(fill=BOTH, expand=True)

Label(main_frame, text="Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence", 
      font=("Segoe UI", 18, "bold"), fg="#ff5555", bg="#1e1e1e").pack(pady=8)

# ... (o resto da interface permanece igual)

# Email
frame_email = Frame(main_frame, bg="#1e1e1e")
frame_email.pack(fill=X, pady=8)
Label(frame_email, text="Email Alvo", fg="white", bg="#1e1e1e").pack(side=LEFT)
Entry(frame_email, textvariable=email_var, font=("Consolas", 11), bg="#282a36", fg="#f8f8f2",
      insertbackground="white", relief="flat").pack(side=LEFT, fill=X, expand=True, padx=8)

# Cabeçalho
Label(main_frame, text="Cole o Cabeçalho Completo do Email", fg="white", bg="#1e1e1e").pack(anchor=W, pady=(12, 5))

header_entry = scrolledtext.ScrolledText(
    main_frame,
    height=18,
    bg="#282a36",
    fg="#FFFFFF",
    insertbackground="#FFFFFF",
    selectbackground="#44475a",
    selectforeground="#FFFFFF",
    font=("Consolas", 9),
    wrap=WORD,
    highlightthickness=0
)

header_entry.pack(fill=X, pady=5)
header_entry.pack(fill=X, pady=5)
header_entry.bind("<FocusOut>", auto_format_header)

# Botões (mantidos iguais ao seu último código)
btn_frame = Frame(main_frame, bg="#1e1e1e")
btn_frame.pack(pady=10)

analyze_btn = Button(btn_frame, text="ANALISAR EMAIL", command=start_analysis, bg="#bd93f9", fg="#282a36",
                     font=("Segoe UI", 10, "bold"), height=2, width=18)
analyze_btn.pack(side=LEFT, padx=2)

Button(btn_frame, text="🌐 Have I Been Pwned", command=open_hibp, bg="#50fa7b", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="🔎 Google Dork", command=open_google_dork, bg="#ff79c6", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="🌐 VirusTotal IP", command=open_virustotal_ip, bg="#ff5555", fg="#0630A3",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="🌐 BGP.he.net IP", command=open_bgp_he_net_ip, bg="#ffb86c", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="🌐 BGP.he.net ASN", command=open_bgp_he_net_asn, bg="#8be9fd", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="🌐 AbuseIPDB IP", command=open_abuseipdb, bg="#ff79c6", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

Button(btn_frame, text="💾 Salvar Resultados", command=save_results, bg="#50fa7b", fg="#282a36",
       font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=LEFT, padx=2)

# Progresso e Log (mantidos iguais)
progress_frame = Frame(main_frame, bg="#1e1e1e")
progress_frame.pack(fill=X, pady=5)
Label(progress_frame, text="Progresso", fg="white", bg="#1e1e1e").pack(side=LEFT, padx=(0,8))
progress_bar = ttk.Progressbar(progress_frame, length=650, mode='determinate')
progress_bar.pack(side=LEFT, fill=X, expand=True)

Label(main_frame, text="Log de Análise", fg="white", bg="#1e1e1e").pack(anchor=W, pady=(10, 2))
text_area = scrolledtext.ScrolledText(main_frame, height=18, bg="#282a36", fg="#f8f8f2", font=("Consolas", 12))
text_area.pack(fill=BOTH, expand=True, pady=5)

for color, hexcolor in [("red", "#ff5555"), ("green", "#50fa7b"), ("yellow", "#f1fa8c"),
                        ("cyan", "#8be9fd"), ("white", "#f8f8f2")]:
    text_area.tag_configure(color, foreground=hexcolor)

Label(main_frame, text="Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence", 
      fg="#05b90e", bg="#1e1e1e").pack(pady=8)

root.mainloop()
