import re
import webbrowser
import threading
import ipaddress
import datetime
from html import escape
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import platform

try:
    import dns.resolver
    import dns.reversename
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False

RECORD_TYPES = [
    "A", "AAAA", "NS", "MX", "TXT", "SOA", "CNAME", "PTR",
    "HINFO", "SRV", "DS", "DNSKEY", "NSEC3", "CAA", "Todos Resultado",
]

# Serviços comuns pesquisados no botão SRV
COMMON_SRV_SERVICES = [
    "_sip._tcp", "_sip._udp", "_sips._tcp", "_h323cs._tcp", "_h323ls._udp",
    "_sip._tls", "_jabber._tcp", "_xmpp._tcp", "_ldap._tcp", "_kerberos._tcp",
    "_kerberos._udp", "_imap._tcp", "_pop3._tcp", "_smtp._tcp",
]

# Parâmetros exibidos no cabeçalho das consultas
RESOLVER_TIMEOUT = 5.0
RESOLVER_LIFETIME = 15.0

# Token candidato a IP (IPv4 ou IPv6) — validado com ipaddress depois
_TOKEN_RE = re.compile(r"[0-9a-fA-F.:]{3,}")
# ----------------------------------------------------------------------
# Resolver / utilitários
# ----------------------------------------------------------------------
def _resolver(nameserver=None):
    r = dns.resolver.Resolver(configure=True)
    r.timeout = RESOLVER_TIMEOUT
    r.lifetime = RESOLVER_LIFETIME
    if nameserver:
        try:
            r.nameservers = [nameserver]
        except Exception:
            pass
    return r

def resolve_with_fallback(name, rdtype, nameserver=None):   
    return _resolver(nameserver).resolve(name, rdtype)

def resolve_ip(host, rdtype="A"):   
    if host in ("", "."):
        return "."
    try:
        ans = _resolver().resolve(host, rdtype)
        return ans[0].address
    except Exception:
        return None

def _ip(res, host):    
    if host == ".":
        return "sem IP"
    try:
        return str(res.resolve(host, "A")[0])
    except Exception:
        return "sem IP"

def _linha_titulo(titulo):
    return [f"📌 {titulo}", "  ────────────────────────────────────────────"]

def _has_dados(lines):    
    for l in lines:
        if l and not l.startswith("📌") and not l.startswith("  ─"):
            return True
    return False

def _segments_colored(line):  
    segs = []
    pos = 0
    for m in _TOKEN_RE.finditer(line):
        tok = m.group()
        try:
            ipaddress.ip_address(tok)
            is_ip = True
        except ValueError:
            is_ip = False
        if m.start() > pos:
            segs.append((line[pos:m.start()], "rec"))
        segs.append((tok, "ip4" if is_ip else "rec"))
        pos = m.end()
    if pos < len(line):
        segs.append((line[pos:], "rec"))
    return [s for s in segs if s[0] != ""]

# ----------------------------------------------------------------------
# Consultas: cada função retorna a lista de linhas formatadas
# ----------------------------------------------------------------------
def query_a(res, domain):
    lines = _linha_titulo("Registros A (IPv4)")
    for rr in res.resolve(domain, "A"):
        lines.append(f"  A        {rr.address}")
    return lines


def query_aaaa(res, domain):
    lines = _linha_titulo("Registros AAAA (IPv6)")
    for rr in res.resolve(domain, "AAAA"):
        lines.append(f"  AAAA     {rr.address}")
    return lines


def query_ns(res, domain):
    lines = _linha_titulo("Servidores de Nomes (NS)")
    for rr in res.resolve(domain, "NS"):
        host = str(rr.target).rstrip(".")
        lines.append(f"  NS       {host:<28} → {_ip(res, host)}")
    return lines


def query_mx(res, domain):
    lines = _linha_titulo("Servidores de Email (MX)")
    mx = sorted(res.resolve(domain, "MX"), key=lambda m: m.preference)
    for rr in mx:
        host = str(rr.exchange).rstrip(".")
        lines.append(f"  MX       {host:<28} ({rr.preference})  → {_ip(res, host)}")
    return lines


def query_txt(res, domain):
    lines = _linha_titulo("Registros TXT (SPF/DKIM/DMARC)")
    for rr in res.resolve(domain, "TXT"):
        txt = "".join(s.decode("utf-8", "replace") for s in rr.strings)
        marc = "[SPF]" if txt.startswith("v=spf1") else ""
        lines.append(f"  TXT      {txt}  {marc}")
    return lines


def query_soa(res, domain):
    lines = _linha_titulo("Início de Autoridade (SOA)")
    rr = res.resolve(domain, "SOA")[0]
    lines.append("  SOA")
    lines.append(f"       MNAME:    {rr.mname}")
    lines.append(f"       RNAME:    {rr.rname}")
    lines.append(f"       SERIAL:   {rr.serial}")
    lines.append(f"       REFRESH:  {rr.refresh}s")
    lines.append(f"       RETRY:    {rr.retry}s")
    lines.append(f"       EXPIRE:   {rr.expire}s")
    lines.append(f"       MINIMUM:  {rr.minimum}s")
    return lines


def query_cname(res, domain):
    lines = _linha_titulo("Aliases (CNAME)")
    for rr in res.resolve(domain, "CNAME"):
        lines.append(f"  CNAME    {domain}  →  {rr.target}")
    return lines


def query_ptr(res, domain):
    lines = _linha_titulo("Reverse DNS (PTR)")
    try:
        ip = ipaddress.ip_address(domain.strip())
    except ValueError:
        lines.append("  Cole um endereço IP (ex.: 8.8.8.8) para")
        lines.append("  fazer a consulta reversa.")
        return lines
    rev = dns.reversename.from_address(str(ip))
    for rr in res.resolve(rev, "PTR"):
        lines.append(f"  PTR      {ip}  ←  {rr.target}")
    return lines


def query_hinfo(res, domain):
    lines = _linha_titulo("Informações do Host (HINFO)")
    for rr in res.resolve(domain, "HINFO"):
        lines.append(f"  HINFO    CPU: {rr.cpu}  |  OS: {rr.os}")
    return lines


def enum_srv(domain, nameserver=None, result_callback=None, progress_cb=None):   
    results = []
    total = len(COMMON_SRV_SERVICES)
    for i, service in enumerate(COMMON_SRV_SERVICES):
        srv_domain = f"{service}.{domain}"
        if progress_cb:
            progress_cb(i / total * 100, f"SRV: {service} ...")
        try:
            records = sorted(
                resolve_with_fallback(srv_domain, "SRV", nameserver),
                key=lambda s: (s.priority, s.weight),
            )
            for rr in records:
                raw = rr.target.to_text()
                if raw == ".":  # RFC 2782: alvo "." = serviço indisponível
                    continue
                target = raw.rstrip(".")
                target_ip = resolve_ip(target) or resolve_ip(target, "AAAA") or "?"
                line = (f"  SRV      {srv_domain:30s}  "
                        f"→ {target} ({target_ip}):{rr.port}  "
                        f"prio={rr.priority} weight={rr.weight}")
                results.append(line)
                if result_callback:
                    result_callback(line, "white")
        except Exception:
            pass  # serviço não existe / sem resposta: segue para o próximo
    if progress_cb:
        progress_cb(100.0, "SRV: concluído")
    return results


def query_srv(res, domain, progress_cb=None):
    lines = _linha_titulo(
        f"Registros de Serviço (SRV) - {len(COMMON_SRV_SERVICES)} serviços comuns"
    )
    lines.extend(enum_srv(domain, nameserver=None, progress_cb=progress_cb))
    return lines


def query_ds(res, domain):
    lines = _linha_titulo("DNSSEC - DS")
    for rr in res.resolve(domain, "DS"):
        lines.append(f"  DS       keytag={rr.key_tag} algo={rr.algorithm} "
                     f"digest_type={rr.digest_type} digest={rr.digest.hex()}")
    return lines


def query_dnskey(res, domain):
    lines = _linha_titulo("DNSSEC - DNSKEY")
    for rr in res.resolve(domain, "DNSKEY"):
        lines.append(f"  DNSKEY   flags={rr.flags} proto={rr.protocol} "
                     f"algo={rr.algorithm}")
        lines.append(f"           key={rr.key.hex()}")
    return lines


def query_nsec3(res, domain):
    lines = _linha_titulo("DNSSEC - NSEC3")
    for rr in res.resolve(domain, "NSEC3"):
        salt = rr.salt.hex() if rr.salt else "-"
        try:
            nxt = rr.next.to_text()
        except AttributeError:  # compatibilidade entre versões do dnspython
            nxt = rr.next.hex()
        lines.append(f"  NSEC3    algo={rr.algorithm} flags={rr.flags} "
                     f"iterations={rr.iterations} salt={salt}")
        lines.append(f"           next={nxt}")
    return lines


def query_caa(res, domain):
    lines = _linha_titulo("Autorização de CA (CAA)")
    for rr in res.resolve(domain, "CAA"):
        lines.append(f"  CAA      flags={rr.flags}  tag={rr.tag}  value={rr.value}")
    return lines


def query_all(res, domain, progress_cb=None):    
    all_lines = []
    items = list(QUERIES.items())
    total = len(items)
    for idx, (qtype, fn) in enumerate(items):
        if qtype == "PTR":
            # PTR só faz sentido com IP no campo alvo
            try:
                ipaddress.ip_address(domain.strip())
            except ValueError:
                if progress_cb:
                    progress_cb((idx + 1) / total * 100, "PTR: pulado (alvo não é IP)")
                continue
        if progress_cb:
            progress_cb(idx / total * 100, f"TODOS: consultando {qtype} ...")
        try:
            if qtype == "SRV":
                base = idx / total * 100
                span = 100.0 / total

                def srv_cb(pct, msg, _b=base, _s=span):
                    if progress_cb:
                        progress_cb(_b + pct * _s / 100.0, msg)

                section = fn(res, domain, progress_cb=srv_cb)
            else:
                section = fn(res, domain)
        except dns.resolver.NXDOMAIN:
            return [f"  ✗ Domínio não existe (NXDOMAIN): {domain}"]
        except Exception:
            if progress_cb:
                progress_cb((idx + 1) / total * 100, f"{qtype}: sem resposta (omitido)")
            continue  # tipo sem resposta: não mostra nada
        if not _has_dados(section):
            if progress_cb:
                progress_cb((idx + 1) / total * 100, f"{qtype}: nada encontrado (omitido)")
            continue  # seção vazia: omitida
        if all_lines:
            all_lines.append("")  # linha em branco entre seções
        all_lines.extend(section)
        if progress_cb:
            progress_cb((idx + 1) / total * 100, f"{qtype}: ok")
    if not all_lines:
        all_lines.append("  Nenhum registro encontrado para o domínio informado.")
    return all_lines


QUERIES = {
    "A": query_a, "AAAA": query_aaaa, "NS": query_ns, "MX": query_mx,
    "TXT": query_txt, "SOA": query_soa, "CNAME": query_cname, "PTR": query_ptr,
    "HINFO": query_hinfo, "SRV": query_srv, "DS": query_ds,
    "DNSKEY": query_dnskey, "NSEC3": query_nsec3, "CAA": query_caa,
}

class DNSEnumGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NSLookup Consultas DNS")
        self.root.geometry("1000x720")
        self.root.minsize(780, 560)

        if platform.system() == "Windows":
            self.root.state("zoomed")
        else:
            try:
                self.root.attributes("-zoomed", True)
            except:
                pass

        style = ttk.Style()
        style.theme_use("clam")

        main = ttk.Frame(root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        # === BOTÕES (um por tipo de registro + Todos Resultado) ===
        btn_frame = ttk.LabelFrame(main, text="Escolha o tipo de registro", padding="8")
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.buttons = {}
        for i, qtype in enumerate(RECORD_TYPES):
            btn = ttk.Button(btn_frame, text=qtype, width=10,
                             command=lambda t=qtype: self.run_query(t))
            btn.grid(row=i // 5, column=i % 5, padx=4, pady=4, sticky="ew")
            self.buttons[qtype] = btn

        for col in range(5):
            btn_frame.columnconfigure(col, weight=1)

        ttk.Label(main,
                  text="Clique em UM botão por vez — 'Todos Resultado' mostra tudo de uma vez, "
                       "somente o que existir.",
                  foreground="#666").pack(anchor=tk.W, pady=(0, 8))

        # === CAMPO DE DOMÍNIO ===
        dom_frame = ttk.Frame(main)
        dom_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(dom_frame, text="Domínio", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.domain_entry = ttk.Entry(dom_frame, font=("", 11))
        self.domain_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.domain_entry.bind("<Return>", lambda e: self.run_query("A"))
        ttk.Button(dom_frame, text="Limpar", width=10, command=self.clear_output).pack(side=tk.LEFT)
        ttk.Button(dom_frame, text="Salvar HTML", width=12,
                   command=self._save_html).pack(side=tk.LEFT, padx=(6, 0))

        # === ÁREA DE RESULTADOS ===
        res_frame = ttk.LabelFrame(main, text="Resultado", padding="5")
        res_frame.pack(fill=tk.BOTH, expand=True)

        self.output = scrolledtext.ScrolledText(
            res_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            relief=tk.FLAT, padx=8, pady=8,
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        self.output.tag_configure("header", foreground="#569cd6", font=("Consolas", 10, "bold"))
        self.output.tag_configure("section", foreground="#4ec9b0", font=("Consolas", 10, "bold"))
        self.output.tag_configure("cmd", foreground="#ce9178")
        self.output.tag_configure("rec", foreground="#d4d4d4")
        self.output.tag_configure("error", foreground="#f14c4c")

        # Cores especiais: SPF e IPs (abóbora)
        self.output.tag_configure("spf", foreground="#3fb950")
        self.output.tag_configure("ip4", foreground="#ff8c00")
        self.output.tag_configure("include", foreground="#4FC3F7")
        self.output.tag_configure("all", foreground="#ff5555")

        # === BARRA DE PROGRESSO (0 a 100%) ===
        prog_frame = ttk.Frame(main)
        prog_frame.pack(fill=tk.X, pady=(8, 0))
        self.progress_label = ttk.Label(prog_frame, text="Progresso: 0%", width=16, anchor=tk.W)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 8))
        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100, value=0)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status = ttk.Label(main, text="Pronto. Digite o alvo e clique em um botão.",
                                relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, pady=(8, 0))

        if not HAS_DNSPYTHON:
            messagebox.showerror(
                "Dependência ausente",
                "O pacote 'dnspython' não está instalado.\n\n"
                "Instale com:\n  pip install dnspython\n"
                "ou (Debian/Ubuntu/Kali):\n  sudo apt install python3-dnspython\n\n"
                "Depois execute o script novamente."
            )
            self.status.config(text="ERRO: dnspython não instalado")
    # ------------------------------------------------------------------
    def clear_output(self):
        self.output.delete("1.0", tk.END)
        self.progress["value"] = 0
        self.progress_label.config(text="Progresso: 0%")
        self.status.config(text="Saída limpa.")

    def _set_progress(self, pct, msg=None):
        pct = max(0, min(100, int(pct)))
        self.progress["value"] = pct
        self.progress_label.config(text=f"Progresso: {pct}%")
        if msg:
            self.status.config(text=msg)

    def run_query(self, qtype):
        if not HAS_DNSPYTHON:
            return
        domain = self.domain_entry.get().strip().lower().rstrip(".")
        if not domain:
            messagebox.showwarning("Aviso", "Digite um domínio ou endereço IP.")
            return
        for btn in self.buttons.values():
            btn.state(["disabled"])
        self.progress["value"] = 0
        self.progress_label.config(text="Progresso: 0%")
        if qtype == "Todos Resultado":
            self.status.config(text=f"Consultando TODOS os tipos para {domain} ...")
        else:
            self.status.config(text=f"Consultando {qtype} para {domain} ...")

        thread = threading.Thread(target=self._execute, args=(qtype, domain), daemon=True)
        thread.start()

    def _execute(self, qtype, domain):       
        def report(pct, msg):
            self.root.after(0, self._set_progress, pct, msg)

        try:
            res = _resolver()
            if qtype == "Todos Resultado":
                lines = query_all(res, domain, progress_cb=report)
            else:
                report(5, f"Consultando {qtype} para {domain} ...")
                if qtype == "SRV":
                    lines = QUERIES[qtype](res, domain, progress_cb=report)
                else:
                    lines = QUERIES[qtype](res, domain)
                if qtype == "SRV" and not _has_dados(lines):
                    lines.append("  Nenhum registro SRV encontrado nos serviços testados.")
                report(100, "")
            ok = True
            if lines and "NXDOMAIN" in lines[0]:
                ok = False
        except dns.resolver.NXDOMAIN:
            lines = [f"  ✗ Domínio não existe (NXDOMAIN): {domain}"]
            ok = False
        except dns.resolver.NoAnswer:
            lines = [f"  Nenhum registro {qtype} encontrado para {domain}."]
            ok = False
        except dns.resolver.NoNameservers:
            lines = ["  Nenhum nameserver disponível respondeu."]
            ok = False
        except dns.exception.Timeout:
            lines = [f"  Tempo limite excedido ({RESOLVER_LIFETIME:.0f}s). Tente novamente."]
            ok = False
        except Exception as e:
            lines = [f"  Erro: {e}"]
            ok = False
        self.root.after(0, self._show_result, qtype, domain, lines, ok)

    def _show_result(self, qtype, domain, lines, ok):
        # Cabeçalho com Data / Nameserver / Timeout
        self.output.insert(tk.END, "\n" + "═" * 66 + "\n", "header")
        self.output.insert(tk.END, f"📡  Alvo: {domain}\n", "header")
        self.output.insert(tk.END, "\n", "rec")
        self.output.insert(tk.END,
                           f"  Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n",
                           "cmd")
        self.output.insert(tk.END, "  Nameserver: Automático\n", "cmd")
        self.output.insert(tk.END, f"  Timeout: {RESOLVER_LIFETIME:.0f}s\n", "cmd")
        self.output.insert(tk.END, "═" * 66 + "\n", "header")

        if qtype == "Todos Resultado":
            self.output.insert(tk.END,
                               f"  Tipo: TODOS  |  varredura de {len(QUERIES)} tipos "
                               f"(só o que achar)\n",
                               "cmd")
        elif qtype == "SRV":
            self.output.insert(tk.END,
                               f"  Tipo: SRV  |  varredura de {len(COMMON_SRV_SERVICES)} serviços comuns\n",
                               "cmd")
        else:
            self.output.insert(tk.END,
                               f"  Tipo: {qtype}  |  Equivalente: nslookup -q={qtype} {domain}\n",
                               "cmd")
        self.output.insert(tk.END, "─" * 66 + "\n", "header")

        for line in lines:
            if line.startswith("📌"):
                self.output.insert(tk.END, line + "\n", "section")
            elif line.startswith("  ✗"):
                self.output.insert(tk.END, line + "\n", "error")
            elif ok:
                # Destacar registros SPF com cores
                if line.startswith("  TXT") and "v=spf1" in line:
                    self.output.insert(tk.END, "  TXT      ", "rec")
                    txt = line.replace("  TXT      ", "").replace("[SPF]", "").strip()
                    for palavra in txt.split():
                        if palavra == "v=spf1":
                            self.output.insert(tk.END, palavra + " ", "spf")
                        elif palavra.startswith("ip4:"):
                            self.output.insert(tk.END, palavra + " ", "ip4")
                        elif palavra.startswith("include:"):
                            self.output.insert(tk.END, palavra + " ", "include")
                        elif palavra in ("-all", "~all", "+all", "?all"):
                            self.output.insert(tk.END, palavra + " ", "all")
                        else:
                            self.output.insert(tk.END, palavra + " ", "rec")
                    self.output.insert(tk.END, "[SPF]\n", "spf")
                elif not line.strip():
                    # linha em branco (separador entre seções no modo TODOS)
                    self.output.insert(tk.END, "\n", "rec")
                else:
                    # Linha normal: IPs válidos em cor abóbora
                    segs = _segments_colored(line)
                    for j, (txt, tag) in enumerate(segs):
                        self.output.insert(tk.END,
                                           txt + ("\n" if j == len(segs) - 1 else ""),
                                           tag)
            else:
                self.output.insert(tk.END, line + "\n", "error")

        # Rodapé
        self.output.insert(tk.END, "═" * 66 + "\n", "header")
        if ok:
            self.output.insert(tk.END, "✅  Consulta concluída.\n", "section")
        else:
            self.output.insert(tk.END, "⚠️  Consulta concluída (com ressalvas).\n", "section")

        self.output.see(tk.END)

        for btn in self.buttons.values():
            btn.state(["!disabled"])
        self.progress["value"] = 100
        self.progress_label.config(text="Progresso: 100%")
        self.status.config(text=f"Concluído: {qtype} → {domain}")

    # ---------------------------
    # Salvar resultados em HTML 
    # ---------------------------
    def _save_html(self):
        content = self.output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Nada para salvar.\nExecute uma consulta primeiro.")
            return

        default_name = f"dns_enum_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path = filedialog.asksaveasfilename(
            title="Salvar resultados em HTML",
            defaultextension=".html",
            initialfile=default_name,
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return

        html = self._build_html(content)
        if html is None:
            messagebox.showerror("Erro", "Não foi possível gerar o HTML.")
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Falha ao gravar o arquivo:\n{e}")
            return

        if messagebox.askyesno(
            "HTML salvo",
            f"Arquivo salvo com sucesso\n\n{path}\n\nDeseja abrir o HTML agora ?",
        ):
            try:
                webbrowser.open(Path(path).resolve().as_uri())
            except Exception:
                pass

    def _build_html(self, content):        
        tag_css = {
            "header": ("#569cd6", True),
            "section": ("#4ec9b0", True),
            "cmd": ("#ce9178", False),
            "rec": ("#d4d4d4", False),
            "error": ("#f14c4c", False),
            "spf": ("#3fb950", False),
            "ip4": ("#ff8c00", False),
            "include": ("#4FC3F7", False),
            "all": ("#ff5555", False),
        }
        priority = ["spf", "ip4", "include", "all",
                    "header", "section", "cmd", "error", "rec"]

        active = set()
        parts = []
        try:
            
            items = self.output.dump("1.0", tk.END, text=True, tag=True)
        except Exception:
            items = None

        if items:
            for kind, value, _idx in items:
                if isinstance(value, bytes):
                    value = value.decode("utf-8", "replace")
                if kind == "tagon":
                    active.add(value)
                    continue
                if kind == "tagoff":
                    active.discard(value)
                    continue
                if kind != "text":
                    continue
                tag = next((t for t in priority if t in active), None)
                escaped = escape(value, quote=False)
                if tag is None:
                    parts.append(escaped)
                else:
                    color, bold = tag_css[tag]
                    style = f"color:{color};" + ("font-weight:bold;" if bold else "")
                    parts.append(f'<span style="{style}">{escaped}</span>')
            body = "".join(parts).replace("\n", "<br>\n")
            
            if not parts:
                body = escape(content).replace("\n", "<br>\n")
        else:
            body = escape(content).replace("\n", "<br>\n")

        m = re.search(r"Alvo:\s*(\S+)", content)
        alvo = m.group(1) if m else "-"
        now = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        n_linhas = content.count("\n") + 1

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DNSEnum — {escape(alvo)}</title>
<style>
  body {{ background:#101418; color:#d4d4d4;
         font-family:Consolas,'Courier New',monospace; padding:20px; line-height:1.5; }}
  h1 {{ color:#569cd6; margin:0 0 4px 0; font-size:20px; }}
  .meta {{ color:#7f8c8d; font-size:12px; margin-bottom:16px;
          border-bottom:1px solid #2a2f36; padding-bottom:10px; }}
  pre {{ margin:0; white-space:pre-wrap; word-wrap:break-word; }}
</style>
</head>
<body>
  <h1>📡 DNSEnum — Resultados</h1>
  <div class="meta">Alvo: {escape(alvo)} &middot; Gerado em {now} &middot; {n_linhas} linhas</div>
  <pre>{body}</pre>
</body>
</html>
"""
    
def main():
    root = tk.Tk()
    DNSEnumGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
