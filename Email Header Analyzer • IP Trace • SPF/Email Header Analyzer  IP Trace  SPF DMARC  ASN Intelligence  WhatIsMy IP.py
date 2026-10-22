import re
import os
import email
import email.policy
import email.utils
from email.header import decode_header as email_decode_header
import requests
from datetime import datetime
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import quote

# ====================== VARIÁVEIS GLOBAIS ======================
risk_score = 0
is_processing = False
last_ip_found = None
last_asn_found = None
loaded_file_path = None


# ====================== PARSING DE ARQUIVOS ======================

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_parts = []
    try:
        parts = email_decode_header(header_value)
        for part, charset in parts:
            if isinstance(part, bytes):
                charset = charset or 'utf-8'
                try:
                    decoded_parts.append(part.decode(charset, errors='replace'))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
    except Exception:
        return str(header_value)
    return ' '.join(decoded_parts)


def parse_eml_file(file_path):
    result = {
        'headers_raw': '',
        'headers_dict': {},
        'body_text': '',
        'body_html': '',
        'attachments': [],
        'from': '',
        'to': '',
        'subject': '',
        'date': '',
        'return_path': '',
        'message_id': '',
        'errors': []
    }

    # Função auxiliar para decodificar o payload com segurança (sem erro no VS Code)
    def safe_decode_payload(part_or_msg):
        payload_data = part_or_msg.get_payload(decode=True)
        if isinstance(payload_data, bytes):
            charset = part_or_msg.get_content_charset() or 'utf-8'
            try:
                return payload_data.decode(charset, errors='replace')
            except (LookupError, UnicodeError):
                return payload_data.decode('utf-8', errors='replace')
        elif isinstance(payload_data, str):
            return payload_data
        return ""

    try:
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        try:
            msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
        except Exception:
            raw_text = raw_bytes.decode('utf-8', errors='replace')
            msg = email.message_from_string(raw_text)

        # ===== EXTRAIR CABEÇALHOS =====
        header_lines = []
        if hasattr(msg, 'items'):
            for key, value in msg.items():
                decoded_val = decode_mime_header(str(value))
                header_lines.append(f"{key}: {decoded_val}")
                result['headers_dict'][key] = decoded_val

        result['headers_raw'] = '\n'.join(header_lines)

        # CAMPOS PRINCIPAIS
        result['from'] = decode_mime_header(str(msg.get('From', '')))
        result['to'] = decode_mime_header(str(msg.get('To', '')))
        result['subject'] = decode_mime_header(str(msg.get('Subject', '')))
        result['date'] = decode_mime_header(str(msg.get('Date', '')))
        result['return_path'] = decode_mime_header(str(msg.get('Return-Path', '')))
        result['message_id'] = decode_mime_header(str(msg.get('Message-ID', '')))

        # ===== EXTRAIR CORPO E ANEXOS =====
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disp = str(part.get('Content-Disposition', ''))

                # Se for anexo
                if 'attachment' in content_disp:
                    filename = part.get_filename()
                    filename = decode_mime_header(filename) if filename else f"anexo.{content_type.split('/')[-1]}"
                    att_payload = part.get_payload(decode=True)
                    size = len(att_payload) if isinstance(att_payload, bytes) else 0
                    result['attachments'].append({
                        'filename': filename,
                        'content_type': content_type,
                        'size': size
                    })
                    continue

                # Se for Texto Simples
                if content_type == 'text/plain' and not result['body_text']:
                    result['body_text'] = safe_decode_payload(part)

                # Se for HTML
                elif content_type == 'text/html' and not result['body_html']:
                    result['body_html'] = safe_decode_payload(part)
        else:
            # Mensagem simples (não multipart)
            content_type = msg.get_content_type()
            decoded_text = safe_decode_payload(msg)
            if content_type == 'text/html':
                result['body_html'] = decoded_text
            else:
                result['body_text'] = decoded_text

    except FileNotFoundError:
        result['errors'].append(f"Arquivo não encontrado: {file_path}")
    except PermissionError:
        result['errors'].append(f"Sem permissão: {file_path}")
    except Exception as e:
        result['errors'].append(f"Erro inesperado: {str(e)}")

    return result

def parse_txt_file(file_path):
    result = {
        'headers_raw': '',
        'headers_dict': {},
        'body_text': '',
        'body_html': '',
        'attachments': [],
        'from': '',
        'to': '',
        'subject': '',
        'date': '',
        'return_path': '',
        'message_id': '',
        'errors': []
    }

    try:
        content = None
        for enc in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')

        result['headers_raw'] = content

        from_match = re.search(r'^From:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        to_match = re.search(r'^To:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        subj_match = re.search(r'^Subject:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        date_match = re.search(r'^Date:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)

        if from_match:
            result['from'] = from_match.group(1).strip()
        if to_match:
            result['to'] = to_match.group(1).strip()
        if subj_match:
            result['subject'] = subj_match.group(1).strip()
        if date_match:
            result['date'] = date_match.group(1).strip()

    except Exception as e:
        result['errors'].append(f"Erro ao ler arquivo: {str(e)}")

    return result


def extract_email_address(field_value):
    if not field_value:
        return None
    match = re.search(r'<([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})>', field_value)
    if match:
        return match.group(1)
    match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', field_value)
    if match:
        return match.group(1)
    return None


def open_email_file():
    global loaded_file_path

    file_path = filedialog.askopenfilename(
        title="Selecionar Arquivo de Email",
        filetypes=[
            ("Arquivos de Email", "*.eml *.msg *.txt *.mhtml *.mht"),
            ("Email Message", "*.eml"),
            ("Text Files", "*.txt"),
            ("MHTML Files", "*.mhtml *.mht"),
            ("Todos os arquivos", "*.*")
        ]
    )

    if not file_path:
        return

    loaded_file_path = file_path
    file_ext = os.path.splitext(file_path)[1].lower()
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    header_entry.delete("1.0", tk.END)
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.config(state=tk.DISABLED)
    progress_bar['value'] = 0

    log_msg(text_area, f"📂 Arquivo carregado: {file_name} ({file_size:,} bytes)", "cyan")

    if file_ext in ['.eml', '.mhtml', '.mht']:
        log_msg(text_area, "🔄 Parsing de arquivo EML/MHTML...", "laranja")
        parsed = parse_eml_file(file_path)
    else:
        log_msg(text_area, "📄 Leitura genérica do arquivo...", "yellow")
        parsed = parse_txt_file(file_path)

    if parsed['errors']:
        for err in parsed['errors']:
            log_msg(text_area, f"❌ {err}", "red")
        if not parsed['headers_raw']:
            return

    if parsed['headers_raw']:
        header_entry.insert("1.0", parsed['headers_raw'])
        highlight_emails()
        highlight_ips()
        log_msg(text_area, f"✅ Cabeçalhos extraídos: {len(parsed['headers_raw'])} caracteres", "green")

    sender_email = None
    for field in [parsed['return_path'], parsed['from'], parsed['to']]:
        sender_email = extract_email_address(field)
        if sender_email:
            break

    if not sender_email:
        sender_email = extract_email_from_header(parsed['headers_raw'])

    if sender_email:
        email_var.set(sender_email)
        log_msg(text_area, f"📧 Email detectado: {sender_email}", "green")

    log_msg(text_area, "\n━━━ INFORMAÇÕES DO ARQUIVO ━━━", "azul_neon")
    if parsed['from']:
        log_msg(text_area, f"  De: {parsed['from']}", "white")
    if parsed['to']:
        log_msg(text_area, f"  Para: {parsed['to']}", "white")
    if parsed['subject']:
        log_msg(text_area, f"  Assunto: {parsed['subject']}", "yellow")
    if parsed['date']:
        log_msg(text_area, f"  Data: {parsed['date']}", "white")

    if parsed['attachments']:
        log_msg(text_area, f"\n📎 Anexos encontrados: {len(parsed['attachments'])}", "laranja")
        dangerous_exts = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.js', '.vbs', '.wsf', '.ps1', '.msi']
        for att in parsed['attachments']:
            size_kb = att['size'] / 1024
            log_msg(text_area, f"   • {att['filename']} ({att['content_type']}, {size_kb:.1f} KB)", "yellow")
            if any(att['filename'].lower().endswith(ext) for ext in dangerous_exts):
                log_msg(text_area, "   ⚠️ ALERTA: Anexo potencialmente perigoso!", "red")

    log_msg(text_area, "\n✅ Arquivo carregado com sucesso!\n", "green")
    file_label_var.set(f"📂 {file_name}")


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
            email_addr = match.group(1).strip()
            if '@' in email_addr:
                return email_addr
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
        if "Received:" in line or "received:" in line:
            ip_matches = re.findall(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]', line)
            ip6_matches = re.findall(r'\[([a-fA-F0-9:]+)\]', line)
            for ip in ip_matches + ip6_matches:
                if not ip.startswith(("192.168.", "10.", "172.16.")) and not ip.startswith("fd"):
                    ips.add(ip)

    xorig = re.findall(r'X-Originating-IP:\s*\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', header_content, re.IGNORECASE)
    for ip in xorig:
        ips.add(ip)

    return list(ips)


def analyze_email_structure(email_addr):
    try:
        user, domain = email_addr.split('@')
    except ValueError:
        return 3, "Formato inválido"

    is_long = len(user) > 12
    has_numbers = any(char.isdigit() for char in user)
    numeric_ratio = sum(c.isdigit() for c in user) / len(user) if user else 0

    trusted_domains = [
        'gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com',
        'protonmail.com', 'mail.ru', 'icloud.com', 'me.com',
        'aol.com', 'gmx.com', 'gmx.net', 'zoho.com',
        'yandex.com', 'tutanota.com', 'live.com', 'msn.com'
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


def log_msg(text_area_widget, msg, color="white"):
    text_area_widget.config(state=tk.NORMAL)
    timestamp = datetime.now().strftime('%H:%M:%S')
    text_area_widget.insert(tk.END, f"[{timestamp}] {msg}\n", color)
    text_area_widget.config(state=tk.DISABLED)
    text_area_widget.see(tk.END)


def update_progress(progress_bar_widget, value):
    progress_bar_widget['value'] = value
    root.update_idletasks()


# ====================== FUNÇÕES DE DESTAQUE ======================
def highlight_emails():
    header_entry.tag_remove("email", "1.0", tk.END)
    text = header_entry.get("1.0", tk.END)
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    for match in re.finditer(email_pattern, text):
        start = f"1.0+{match.start()}c"
        end_pos = f"1.0+{match.end()}c"
        header_entry.tag_add("email", start, end_pos)


def highlight_ips():
    header_entry.tag_remove("IP", "1.0", tk.END)
    text = header_entry.get("1.0", tk.END)

    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    for match in re.finditer(ipv4_pattern, text):
        start = f"1.0+{match.start()}c"
        end_pos = f"1.0+{match.end()}c"
        header_entry.tag_add("IP", start, end_pos)

    ipv6_pattern = r'\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b|\b(?:[a-fA-F0-9]{1,4}:){1,7}:\b'
    for match in re.finditer(ipv6_pattern, text):
        start = f"1.0+{match.start()}c"
        end_pos = f"1.0+{match.end()}c"
        header_entry.tag_add("IP", start, end_pos)


def auto_format_header(event=None):
    current = header_entry.get("1.0", tk.END)
    formatted = format_header(current)
    if formatted != current.strip():
        header_entry.delete("1.0", tk.END)
        header_entry.insert("1.0", formatted)
    highlight_emails()
    highlight_ips()


# ====================== FUNÇÕES DE BOTÕES ======================
def open_hibp():
    em = email_var.get().strip()
    if "@" not in em:
        messagebox.showwarning("Aviso", "Digite um email ou cole um cabeçalho!")
        return
    webbrowser.open(f"https://haveibeenpwned.com/account/{em}")
    log_msg(text_area, f"🔎 Have I Been Pwned aberto para: {em}", "cyan")


def open_google_dork():
    em = email_var.get().strip()
    if "@" not in em:
        messagebox.showwarning("Aviso", "Digite um email ou cole um cabeçalho!")
        return
    encoded = quote(em)
    webbrowser.open(f"https://www.google.com/search?q=%22{encoded}%22")
    log_msg(text_area, f"🔎 Google Dork aberto para: {em}", "cyan")


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


def colorize_content(text):
    text = re.sub(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', r'<span class="email">\1</span>', text)
    text = re.sub(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', r'<span class="ip">\1</span>', text)
    text = re.sub(r'\b([a-fA-F0-9]{1,4}(:[a-fA-F0-9]{1,4}){1,7})\b', r'<span class="ip">\1</span>', text)
    text = re.sub(r'(RISCO FINAL: ALTO)', r'<span class="risk-alto">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(RISCO FINAL: MÉDIO)', r'<span class="risk-medio">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'(RISCO FINAL: BAIXO)', r'<span class="risk-baixo">\1</span>', text, flags=re.IGNORECASE)
    return text


def save_results():
    log_content = text_area.get("1.0", tk.END).strip()
    header_content = header_entry.get("1.0", tk.END).strip()
    em = email_var.get().strip() or "Não informado"

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
    colored_header = colorize_content(format_header(header_content).replace('<', '&lt;').replace('>', '&gt;'))
    now_str = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>MailTrace OSINT - Relatório</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; }}
        h1 {{ color: #ff5555; text-align: center; }}
        h2 {{ color: #50fa7b; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .section {{ background: #282a36; padding: 18px; border-radius: 10px; margin: 18px 0; }}
        pre {{ background: #282a36; padding: 18px; border-radius: 8px; white-space: pre-wrap; }}
        .email {{ color: #50fa7b; font-weight: bold; }}
        .ip {{ color: #0bf0f8; font-weight: bold; }}
        .risk-alto {{ color: #ff5555; font-weight: bold; }}
        .risk-medio {{ color: #f1fa8c; font-weight: bold; }}
        .risk-baixo {{ color: #50fa7b; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 Email Header Analyzer - Relatório OSINT</h1>
        <p style="text-align:center; color:#8be9fd;">Gerado em: {now_str}</p>
        <h2>📧 Email Analisado</h2>
        <div class="section"><strong style="color:#ff79c6;">{em}</strong></div>
        <h2>📋 Cabeçalho Completo</h2>
        <div class="section"><pre>{colored_header}</pre></div>
        <h2>📊 Log Completo da Análise</h2>
        <div class="section"><pre>{colored_log}</pre></div>
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


def analysis_thread(email_addr, header_raw, text_area_widget, progress_bar_widget, analyze_btn_widget):
    global risk_score, last_ip_found, last_asn_found
    risk_score = 0
    last_ip_found = None
    last_asn_found = None

    try:
        log_msg(text_area_widget, f"Iniciando análise para: {email_addr}\n", "azul_neon")
        update_progress(progress_bar_widget, 10)

        if header_raw:
            ips = extract_header_info(header_raw)
            if ips:
                last_ip_found = ips[0]
                log_msg(text_area_widget, f"IP Encontrados: {', '.join(ips)}\n", "green")
                geo = get_ip_info(ips[0])
                if "error" not in geo:
                    last_asn_found = geo.get('asn', 'N/A')
                    log_msg(text_area_widget, f"Local: {geo['city']}, {geo['region']}, {geo['country']}\n", "green")
                    log_msg(text_area_widget, f"ISP: {geo['isp']}\n", "green")
                    log_msg(text_area_widget, f"ASN: {last_asn_found}\n", "cyan")

        update_progress(progress_bar_widget, 45)

        domain = email_addr.split('@')[1]
        log_msg(text_area_widget, f"Verificando domínio: {domain}\n", "laranja")

        spf_records = check_dns_records(domain, 'SPF')
        dmarc_records = check_dns_records(domain, 'DMARC')

        has_spf = any("v=spf1" in r.lower() for r in spf_records)
        has_dmarc = any("v=dmarc1" in r.lower() for r in dmarc_records)

        if has_spf:
            log_msg(text_area_widget, "SPF: Configurado ✓", "green")
        else:
            log_msg(text_area_widget, "SPF: Não configurado (Risco Alto)", "red")
            risk_score += 2

        if has_dmarc:
            log_msg(text_area_widget, "DMARC: Configurado ✓\n", "green")
        else:
            log_msg(text_area_widget, "DMARC: Não configurado\n", "red")
            risk_score += 1

        update_progress(progress_bar_widget, 75)

        struct_risk, struct_desc = analyze_email_structure(email_addr)
        risk_score += struct_risk
        log_msg(text_area_widget, f"Estrutura: {struct_desc} (Risco +{struct_risk})\n", "yellow")

        if risk_score >= 5:
            final_risk, color = "ALTO", "red"
        elif risk_score >= 3:
            final_risk, color = "MÉDIO", "yellow"
        else:
            final_risk, color = "BAIXO", "green"

        log_msg(text_area_widget, f"RISCO FINAL: {final_risk} (Score: {risk_score})\n", color)
        update_progress(progress_bar_widget, 100)

    except Exception as e:
        log_msg(text_area_widget, f"Erro durante a análise: {e}\n", "red")
        update_progress(progress_bar_widget, 100)
    finally:
        global is_processing
        is_processing = False
        analyze_btn_widget.config(state=tk.NORMAL)


def start_analysis():
    global is_processing
    if is_processing:
        return

    em = email_var.get().strip()
    header_raw = header_entry.get("1.0", tk.END).strip()

    if not em or "@" not in em:
        extracted = extract_email_from_header(header_raw)
        if extracted:
            em = extracted
            email_var.set(em)
            log_msg(text_area, f"Email extraído do cabeçalho: {em}", "cyan")
        else:
            messagebox.showerror("Erro", "Insira um email válido ou cole um cabeçalho com endereço.")
            return

    is_processing = True
    analyze_btn.config(state=tk.DISABLED)
    progress_bar['value'] = 0
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.config(state=tk.DISABLED)

    thread = threading.Thread(
        target=analysis_thread,
        args=(em, header_raw, text_area, progress_bar, analyze_btn),
        daemon=True
    )
    thread.start()


# ====================== INTERFACE GRÁFICA ======================
root = tk.Tk()
root.title("Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence")
root.geometry("1100x850")
root.state('zoomed')
root.configure(bg="#1e1e1e")

email_var = tk.StringVar()
file_label_var = tk.StringVar(value="Nenhum arquivo carregado")

main_frame = tk.Frame(root, bg="#1e1e1e", padx=15, pady=15)
main_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(
    main_frame, text="Email Header Analyzer • IP Trace • SPF/DMARC • ASN Intelligence",
    font=("Segoe UI", 16, "bold"), fg="#ff5555", bg="#1e1e1e"
).pack(pady=3)

frame_email = tk.Frame(main_frame, bg="#1e1e1e")
frame_email.pack(fill=tk.X, pady=8)

tk.Label(frame_email, text="Email Alvo ", fg="white", bg="#1e1e1e").pack(side=tk.LEFT)
tk.Entry(
    frame_email, textvariable=email_var, font=("Consolas", 11),
    bg="#282a36", fg="#f8f8f2", insertbackground="white", relief="flat"
).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

tk.Button(
    frame_email, text="📂 Abrir Arquivo (.eml, .txt...)", command=open_email_file,
    bg="#bd93f9", fg="#282a36", font=("Segoe UI", 10, "bold"), height=1, width=28, cursor="hand2"
).pack(side=tk.LEFT, padx=5)

tk.Label(
    frame_email, textvariable=file_label_var, fg="#6272a4", bg="#1e1e1e", font=("Segoe UI", 9, "italic")
).pack(side=tk.LEFT, padx=5)

tk.Label(
    main_frame, text="Cole o Cabeçalho Completo do Email (ou abra um arquivo .eml)",
    fg="white", bg="#1e1e1e"
).pack(anchor=tk.W, pady=(12, 5))

header_entry = scrolledtext.ScrolledText(
    main_frame, height=16, bg="#282a36", fg="#FFFFFF", insertbackground="#FFFFFF",
    selectbackground="#44475a", selectforeground="#FFFFFF", font=("Consolas", 11), wrap=tk.WORD
)
header_entry.pack(fill=tk.BOTH, expand=True, pady=2)

header_entry.tag_configure("email", foreground="#50fa7b")
header_entry.tag_configure("IP", foreground="#0bf0f8")
header_entry.bind("<KeyRelease>", lambda e: (highlight_emails(), highlight_ips()))
header_entry.bind("<FocusOut>", auto_format_header)

btn_frame = tk.Frame(main_frame, bg="#1e1e1e")
btn_frame.pack(pady=10)

analyze_btn = tk.Button(
    btn_frame, text="ANALISAR EMAIL", command=start_analysis,
    bg="#0aec1d", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=16
)
analyze_btn.pack(side=tk.LEFT, padx=2)

tk.Button(btn_frame, text="Have I Been Pwned", command=open_hibp, bg="#1865f5", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=18).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="Google Dork", command=open_google_dork, bg="#79ffde", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="VirusTotal IP", command=open_virustotal_ip, bg="#098b81", fg="#0A0A0A", font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="BGP.he.net IP", command=open_bgp_he_net_ip, bg="#ffb86c", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="BGP.he.net ASN", command=open_bgp_he_net_asn, bg="#b47808", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=14).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="AbuseIPDB IP", command=open_abuseipdb, bg="#ff79c6", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=14).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="WhatIsMy IP MAP", command=open_whatismyip_map, bg="#cee7eb", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=16).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="💾 Salvar HTML", command=save_results, bg="#f83909", fg="#282a36", font=("Segoe UI", 10, "bold"), height=2, width=14).pack(side=tk.LEFT, padx=2)

progress_frame = tk.Frame(main_frame, bg="#1e1e1e")
progress_frame.pack(fill=tk.X, pady=5)
tk.Label(progress_frame, text="Progresso", fg="white", bg="#1e1e1e").pack(side=tk.LEFT, padx=(0, 8))
progress_bar = ttk.Progressbar(progress_frame, length=650, mode='determinate')
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

tk.Label(main_frame, text="Log de Análise", fg="white", bg="#1e1e1e").pack(anchor=tk.W, pady=(10, 2))
text_area = scrolledtext.ScrolledText(main_frame, height=16, bg="#282a36", fg="#f8f8f2", font=("Consolas", 11))
text_area.pack(fill=tk.BOTH, expand=True, pady=1)

for color, hexcolor in [
    ("red", "#ff5555"), ("green", "#50fa7b"), ("yellow", "#f1fa8c"),
    ("cyan", "#8be9fd"), ("white", "#f8f8f2"), ("azul_neon", "#00BFFF"), ("laranja", "#fca762")
]:
    text_area.tag_configure(color, foreground=hexcolor)

root.mainloop()
