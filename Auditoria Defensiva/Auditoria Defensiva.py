import socket
import ssl
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse
from urllib import request, error
from datetime import datetime
from html import escape


PORTAS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB",
}

CABECALHOS = [
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Content-Type-Options", "X-Frame-Options",
    "X-XSS-Protection", "Referrer-Policy",
    "Permissions-Policy", "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
]

CABECALHOS_PERIGOSOS = [
    "Server", "X-Powered-By", "X-AspNet-Version",
    "X-AspNetMvc-Version", "Via",
]

EXPLORACOES = {
    "FTP": {
        "risco": "ALTO",
        "descricao": "FTP transmite credenciais em texto claro.",
        "como_explorar": [
            "1. Captura de credenciais com Wireshark/tcpdump",
            "   Filtra porta 21 e lê login/senha em texto puro",
            "", "2. Força bruta com Hydra",
            "   hydra -L users.txt -P senhas.txt ftp://alvo",
            "", "3. Login anônimo",
            "   Conecta com usuário anonymous sem senha",
        ],
        "correcao": (
            "1. Substitua FTP por SFTP ou FTPS\n"
            "2. Desative login anônimo\n"
            "3. Restrinja acesso por IP no firewall\n"
            "4. Use autenticação com chave pública"
        ),
    },
    "SSH": {
        "risco": "MÉDIO",
        "descricao": "SSH exposto permite força bruta e enumeração.",
        "como_explorar": [
            "1. Força bruta de credenciais",
            "   hydra -L users.txt -P senhas.txt ssh://alvo",
            "", "2. Enumeração de usuários (CVE-2018-15473)",
            "   Descobre usuários válidos no sistema",
        ],
        "correcao": (
            "1. Desative autenticação por senha, use chaves\n"
            "2. Configure fail2ban\n"
            "3. Permita acesso apenas de IPs autorizados\n"
            "4. Desative login como root"
        ),
    },
    "Telnet": {
        "risco": "CRÍTICO",
        "descricao": "Telnet transmite TUDO em texto claro.",
        "como_explorar": [
            "1. Interceptação total da sessão",
            "   Wireshark captura login, senha e comandos",
            "", "2. Sequestro de sessão com ettercap",
        ],
        "correcao": (
            "1. Desative Telnet IMEDIATAMENTE\n"
            "2. Substitua por SSH\n"
            "3. Bloqueie porta 23 no firewall"
        ),
    },
    "SMTP": {
        "risco": "ALTO",
        "descricao": "SMTP exposto pode ser usado para spam e phishing.",
        "como_explorar": [
            "1. Open relay para envio de spam",
            "", "2. Enumeração com VRFY e EXPN",
            "", "3. Spoofing sem SPF/DKIM/DMARC",
        ],
        "correcao": (
            "1. Configure autenticação obrigatória\n"
            "2. Desative VRFY e EXPN\n"
            "3. Force STARTTLS\n"
            "4. Configure SPF, DKIM e DMARC"
        ),
    },
    "SMB": {
        "risco": "CRÍTICO",
        "descricao": "SMB exposto é vetor de ransomware (EternalBlue).",
        "como_explorar": [
            "1. EternalBlue (MS17-010) - execução remota",
            "", "2. Enumeração: smbclient -L //alvo -N",
            "", "3. Pass-the-Hash para acesso sem senha",
        ],
        "correcao": (
            "1. NUNCA exponha SMB na internet\n"
            "2. Bloqueie porta 445 no firewall\n"
            "3. Desative SMBv1\n"
            "4. Mantenha patches atualizados"
        ),
    },
    "MySQL": {
        "risco": "CRÍTICO",
        "descricao": "MySQL exposto permite acesso direto ao banco.",
        "como_explorar": [
            "1. Credenciais padrão: root sem senha",
            "", "2. Força bruta com Hydra",
            "", "3. SELECT INTO OUTFILE para webshell",
        ],
        "correcao": (
            "1. Use bind-address = 127.0.0.1\n"
            "2. Defina senha forte para root\n"
            "3. Bloqueie porta 3306 no firewall"
        ),
    },
    "RDP": {
        "risco": "CRÍTICO",
        "descricao": "RDP exposto é vetor #1 de ransomware.",
        "como_explorar": [
            "1. BlueKeep (CVE-2019-0708) - execução remota",
            "", "2. Força bruta de credenciais",
            "", "3. Credential stuffing com senhas vazadas",
        ],
        "correcao": (
            "1. NUNCA exponha RDP na internet\n"
            "2. Use VPN ou RD Gateway\n"
            "3. Ative NLA\n"
            "4. Use autenticação multifator"
        ),
    },
    "PostgreSQL": {
        "risco": "CRÍTICO",
        "descricao": "PostgreSQL exposto permite execução de comandos.",
        "como_explorar": [
            "1. Autenticação trust permite acesso sem senha",
            "", "2. COPY TO/FROM PROGRAM executa comandos do SO",
        ],
        "correcao": (
            "1. Configure listen_addresses = localhost\n"
            "2. Restrinja pg_hba.conf\n"
            "3. Bloqueie porta 5432 no firewall"
        ),
    },
    "VNC": {
        "risco": "CRÍTICO",
        "descricao": "VNC frequentemente não exige autenticação.",
        "como_explorar": [
            "1. Acesso direto sem senha à área de trabalho",
            "", "2. Senhas VNC limitadas a 8 caracteres",
        ],
        "correcao": (
            "1. NUNCA exponha VNC na internet\n"
            "2. Use túnel SSH ou VPN\n"
            "3. Configure senha forte"
        ),
    },
    "Redis": {
        "risco": "CRÍTICO",
        "descricao": "Redis sem senha dá controle total dos dados.",
        "como_explorar": [
            "1. redis-cli -h alvo (acesso sem senha)",
            "", "2. Escrita de chave SSH para acesso root",
            "", "3. Escrita de webshell no diretório web",
        ],
        "correcao": (
            "1. Configure bind 127.0.0.1\n"
            "2. Defina requirepass\n"
            "3. Bloqueie porta 6379 no firewall"
        ),
    },
    "MongoDB": {
        "risco": "CRÍTICO",
        "descricao": "MongoDB sem autenticação expõe todos os dados.",
        "como_explorar": [
            "1. mongosh --host alvo (acesso livre)",
            "", "2. show dbs lista todos os bancos",
            "", "3. Ransomware apaga dados e exige resgate",
        ],
        "correcao": (
            "1. Configure bindIp: 127.0.0.1\n"
            "2. Ative autenticação obrigatória\n"
            "3. Bloqueie porta 27017 no firewall"
        ),
    },
    "HTTP": {
        "risco": "MÉDIO",
        "descricao": "HTTP expõe tráfego sem criptografia.",
        "como_explorar": [
            "1. Man-in-the-Middle com Wireshark",
            "", "2. SSL Stripping com sslstrip",
            "", "3. Roubo de cookies de sessão",
        ],
        "correcao": (
            "1. Redirecione HTTP para HTTPS\n"
            "2. Configure HSTS\n"
            "3. Marque cookies com Secure e HttpOnly"
        ),
    },
    "HTTP-Proxy": {
        "risco": "MÉDIO",
        "descricao": "Porta 8080 pode expor painéis administrativos.",
        "como_explorar": [
            "1. Proxy aberto para anonimizar ataques",
            "", "2. Painéis com credenciais padrão",
        ],
        "correcao": (
            "1. Bloqueie porta 8080 externamente\n"
            "2. Use VPN para painéis administrativos\n"
            "3. Altere credenciais padrão"
        ),
    },
    "POP3": {
        "risco": "ALTO",
        "descricao": "POP3 transmite credenciais em texto claro.",
        "como_explorar": [
            "1. Sniffer captura login e senha",
            "", "2. Força bruta sem proteção",
        ],
        "correcao": "1. Use POP3S (porta 995)\n2. Desative porta 110",
    },
    "IMAP": {
        "risco": "ALTO",
        "descricao": "IMAP sem TLS expõe credenciais e e-mails.",
        "como_explorar": [
            "1. Interceptação de credenciais",
            "", "2. Leitura de e-mails em trânsito",
        ],
        "correcao": "1. Use IMAPS (porta 993)\n2. Desative porta 143",
    },
    "DNS": {
        "risco": "MÉDIO",
        "descricao": "DNS exposto permite AXFR e amplificação DDoS.",
        "como_explorar": [
            "1. dig axfr dominio.com @alvo",
            "", "2. Amplificação DDoS via recursão aberta",
        ],
        "correcao": (
            "1. Desative AXFR para externos\n"
            "2. Desative recursão pública\n"
            "3. Implemente DNSSEC"
        ),
    },
    "TLS_ANTIGO": {
        "risco": "ALTO",
        "descricao": "TLS 1.0/1.1 possuem falhas conhecidas.",
        "como_explorar": [
            "1. BEAST - descriptografa cookies via CBC",
            "", "2. POODLE - força downgrade e descriptografa",
        ],
        "correcao": (
            "1. Desative TLS 1.0 e 1.1\n"
            "2. Mantenha TLS 1.2 e 1.3\n"
            "3. Teste com ssllabs.com"
        ),
    },
    "CERTIFICADO_INVALIDO": {
        "risco": "ALTO",
        "descricao": "Certificado inválido permite Man-in-the-Middle.",
        "como_explorar": [
            "1. MITM com certificado falso",
            "", "2. SSL Stripping",
        ],
        "correcao": (
            "1. Instale certificado válido (Let's Encrypt)\n"
            "2. Configure cadeia intermediária\n"
            "3. Ative HSTS"
        ),
    },
    "CABECALHO_AUSENTE": {
        "risco": "MÉDIO",
        "descricao": "Cabeçalhos ausentes expõem o site a ataques.",
        "como_explorar": [
            "1. Sem HSTS → SSL Stripping",
            "", "2. Sem CSP → XSS",
            "", "3. Sem X-Frame-Options → Clickjacking",
        ],
        "correcao": (
            "1. Configure todos os cabeçalhos de segurança\n"
            "2. Teste com securityheaders.com"
        ),
    },
    "INFO_EXPOSTA": {
        "risco": "BAIXO",
        "descricao": "Cabeçalhos revelam tecnologias e versões.",
        "como_explorar": [
            "1. Server: Apache/2.4.49 → CVE-2021-41773",
            "", "2. Busca automatizada de exploits",
        ],
        "correcao": (
            "1. Remova cabeçalho Server\n"
            "2. Remova X-Powered-By\n"
            "3. ServerTokens Prod / server_tokens off"
        ),
    },
}

# Cores do tema profissional escuro
COR_FUNDO = "#1a1a2e"
COR_PAINEL = "#16213e"
COR_ENTRADA = "#0f3460"
COR_TEXTO = "#e0e0e0"
COR_TITULO = "#00d4ff"
COR_VERDE = "#00c853"      # Botão Iniciar Auditoria (Verde)
COR_ABOBORA = "#ff8c00"    # Botão Salvar Relatório (Abóbora/Laranja)
COR_VERMELHO = "#ff1744"
COR_AMARELO = "#ffd600"
COR_AZUL = "#2979ff"
COR_CINZA = "#78909c"
COR_CRITICO = "#ff1744"
COR_ALTO = "#ff6d00"
COR_MEDIO = "#ffd600"
COR_BAIXO = "#00e676"
COR_OK = "#00e676"
COR_FALHA = "#ff1744"
COR_AVISO = "#ffab00"
COR_INFO = "#40c4ff"
COR_ABERTA = "#ff9100"


class Auditoria:
    def __init__(self, host, atualizar):
        self.host = host
        self.atualizar = atualizar
        self.resultados = []
        self.falhas = []

    def progresso(self, p, msg):
        self.atualizar(p, msg)

    def resultado(self, titulo, detalhe, status="INFO"):
        self.resultados.append(
            {"titulo": titulo, "detalhe": detalhe, "status": status}
        )

    def falha(self, titulo, detalhe, correcao, tipo=None):
        f = {"titulo": titulo, "detalhe": detalhe, "correcao": correcao}
        if tipo and tipo in EXPLORACOES:
            info = EXPLORACOES[tipo]
            f["risco"] = info["risco"]
            f["descricao_ataque"] = info["descricao"]
            f["como_explorar"] = info["como_explorar"]
            f["correcao_detalhada"] = info["correcao"]
        else:
            f["risco"] = "INFO"
            f["descricao_ataque"] = ""
            f["como_explorar"] = []
            f["correcao_detalhada"] = correcao
        self.falhas.append(f)

    def testar_porta(self, porta):
        try:
            with socket.create_connection((self.host, porta), timeout=4):
                return True, "conexão aceita"
        except socket.timeout:
            return False, "tempo limite"
        except ConnectionRefusedError:
            return False, "recusada"
        except OSError as e:
            return False, str(e)

    def obter_banner(self, porta):
        try:
            with socket.create_connection((self.host, porta), timeout=4) as s:
                s.settimeout(4)
                d = s.recv(1024)
                return d.decode("utf-8", errors="replace").strip() if d else "(vazio)"
        except Exception:
            return "(indisponível)"

    def verificar_tls(self):
        ctx = ssl.create_default_context()
        try:
            with socket.create_connection((self.host, 443), timeout=7) as s:
                with ctx.wrap_socket(s, server_hostname=self.host) as c:
                    cert = c.getpeercert()
                    cifra = c.cipher()
                    ver = c.version()
                    exp = cert.get("notAfter", "?")
                    self.resultado(
                        "TLS",
                        f"Versão: {ver} | Cifra: {cifra[0] if cifra else '?'} | Expira: {exp}",
                        "OK"
                    )
                    if ver in ("TLSv1", "TLSv1.1"):
                        self.falha("TLS antigo", f"Negociou {ver}.",
                                   "Desative TLS 1.0/1.1.", "TLS_ANTIGO")
        except ssl.SSLCertVerificationError as e:
            self.resultado("Certificado TLS", str(e), "FALHA")
            self.falha("Certificado inválido", str(e),
                       "Instale certificado válido.", "CERTIFICADO_INVALIDO")
        except Exception as e:
            self.resultado("TLS", str(e), "AVISO")

    def verificar_http(self, esquema):
        porta = 443 if esquema == "https" else 80
        url = f"{esquema}://{self.host}:{porta}/"
        req = request.Request(url, method="GET", headers={
            "User-Agent": "AuditoriaDefensiva/2.0",
            "Host": self.host, "Connection": "close",
        })
        try:
            with request.urlopen(req, timeout=10) as r:
                self.resultado("HTTP", f"{url} → HTTP {r.status}", "OK")
                self.verificar_info_exposta(r.headers)
                self.verificar_cabecalhos(r.headers)
        except error.HTTPError as e:
            self.resultado("HTTP", f"HTTP {e.code} {e.reason}", "AVISO")
        except error.URLError as e:
            self.resultado("HTTP", f"Falha: {e.reason}", "FALHA")
        except Exception as e:
            self.resultado("HTTP", str(e), "FALHA")

    def verificar_info_exposta(self, cab):
        for n in CABECALHOS_PERIGOSOS:
            v = cab.get(n)
            if v:
                self.resultado(f"Info exposta: {n}", v, "AVISO")
                self.falha(f"Expõe: {n}", f"Valor: {v}",
                           f"Remova {n}.", "INFO_EXPOSTA")

    def verificar_cabecalhos(self, cab):
        for n in CABECALHOS:
            v = cab.get(n)
            if v:
                self.resultado(n, v, "OK")
            else:
                self.resultado(n, "Ausente", "FALHA")
                self.falha(f"Ausente: {n}", f"{n} não enviado.",
                           self.correcao_cab(n), "CABECALHO_AUSENTE")

    def correcao_cab(self, n):
        m = {
            "Strict-Transport-Security": "Configure HSTS.",
            "Content-Security-Policy": "Crie política CSP.",
            "X-Content-Type-Options": "Adicione nosniff.",
            "X-Frame-Options": "Adicione DENY ou SAMEORIGIN.",
            "X-XSS-Protection": "Adicione X-XSS-Protection: 0 e use CSP.",
            "Referrer-Policy": "Use strict-origin-when-cross-origin.",
            "Permissions-Policy": "Desative APIs desnecessárias.",
            "Cross-Origin-Opener-Policy": "Adicione same-origin.",
            "Cross-Origin-Resource-Policy": "Adicione same-origin.",
        }
        return m.get(n, "Configure no servidor.")

    def executar(self, esquema):
        abertas = []
        self.progresso(5, "Verificando portas...")
        total = len(PORTAS)

        for i, (p, s) in enumerate(PORTAS.items()):
            ok, d = self.testar_porta(p)
            if ok:
                abertas.append(p)
                self.resultado(f"{p}/TCP {s}", "Acessível", "ABERTA")
            else:
                self.resultado(f"{p}/TCP {s}", d, "INFO")
            self.progresso(5 + int(((i + 1) / total) * 35),
                           f"Porta {p} verificada")

        self.progresso(45, "Banners...")
        for p in (21, 22, 23, 25, 110, 143):
            if p in abertas:
                b = self.obter_banner(p)
                self.resultado(f"Banner {PORTAS[p]}", b, "INFO")

        criticas = {
            21: "FTP", 23: "Telnet", 25: "SMTP", 53: "DNS",
            110: "POP3", 143: "IMAP", 445: "SMB", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
            6379: "Redis", 8080: "HTTP-Proxy", 27017: "MongoDB",
        }
        for p, t in criticas.items():
            if p in abertas:
                info = EXPLORACOES.get(t, {})
                self.falha(f"{t} exposto ({p})",
                           f"Porta {p}/TCP acessível.",
                           info.get("correcao", "Bloqueie no firewall."), t)

        if 22 in abertas:
            self.falha("SSH exposto (22)", "Porta 22/TCP acessível.",
                       EXPLORACOES["SSH"]["correcao"], "SSH")
        if 80 in abertas:
            self.falha("HTTP sem TLS (80)", "Porta 80 sem criptografia.",
                       EXPLORACOES["HTTP"]["correcao"], "HTTP")

        self.progresso(60, "TLS...")
        if 443 in abertas:
            self.verificar_tls()

        self.progresso(80, "HTTP/Cabeçalhos...")
        if 80 in abertas:
            self.verificar_http("http")
        if 443 in abertas:
            self.verificar_http("https")

        self.progresso(100, "Concluído")
        return self.resultados, self.falhas


def normalizar_host(v):
    v = v.strip()
    if "://" not in v:
        v = "https://" + v
    d = urlparse(v)
    h, e = d.hostname, d.scheme.lower()
    if not h:
        raise ValueError("Host inválido.")
    if e not in ("http", "https"):
        raise ValueError("Use http:// ou https://.")
    return h, e


def gerar_html(host, resultados, falhas):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linhas = ""
    for r in resultados:
        cor = {"OK": "#1b5e20", "ABERTA": "#e65100",
               "AVISO": "#f57f17", "FALHA": "#b71c1c",
               "INFO": "#0d47a1"}.get(r["status"], "#333")
        linhas += (
            f'<tr><td style="color:{cor};font-weight:bold">'
            f'{escape(r["status"])}</td>'
            f'<td>{escape(r["titulo"])}</td>'
            f'<td>{escape(r["detalhe"])}</td></tr>\n'
        )
    blocos = ""
    for f in falhas:
        cor_r = {"CRÍTICO": "#b71c1c", "ALTO": "#e65100",
                 "MÉDIO": "#f57f17", "BAIXO": "#1b5e20"
                 }.get(f.get("risco", ""), "#333")
        exp = ""
        for ln in f.get("como_explorar", []):
            if ln == "":
                exp += "<br>"
            elif ln.startswith("   "):
                exp += f'<div style="margin-left:18px;color:#666">{escape(ln.strip())}</div>'
            else:
                exp += f'<div style="margin-top:6px"><b>{escape(ln)}</b></div>'
        blocos += f"""
        <div style="background:#fff5f5;border-left:5px solid {cor_r};
                    padding:14px 18px;margin:16px 0;border-radius:0 8px 8px 0">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <h3 style="margin:0">{escape(f["titulo"])}</h3>
                <span style="background:{cor_r};color:#fff;padding:3px 12px;
                             border-radius:4px;font-weight:bold;font-size:.85em">
                    {escape(f.get("risco","INFO"))}</span>
            </div>
            <p><b>Problema:</b> {escape(f["detalhe"])}</p>
            {"<p><b>Ataque:</b> " + escape(f.get("descricao_ataque","")) + "</p>" if f.get("descricao_ataque") else ""}
            {"<div style='background:#fff8e1;border:1px solid #ffc107;padding:10px;margin:8px 0;border-radius:6px'><h4 style=margin:0>Como explorar:</h4>" + exp + "</div>" if exp else ""}
            <div style="background:#e8f5e9;border:1px solid #4caf50;padding:10px;margin:8px 0;border-radius:6px">
                <h4 style="margin:0">Correção:</h4>
                <pre style="white-space:pre-wrap;font-family:inherit;margin:4px 0 0">{escape(f.get("correcao_detalhada", f["correcao"]))}</pre>
            </div>
        </div>"""

    nc = sum(1 for x in falhas if x.get("risco") == "CRÍTICO")
    na = sum(1 for x in falhas if x.get("risco") == "ALTO")
    nm = sum(1 for x in falhas if x.get("risco") == "MÉDIO")
    nb = sum(1 for x in falhas if x.get("risco") == "BAIXO")

    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<title>Auditoria - {escape(host)}</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;margin:30px;color:#222;line-height:1.6}}
h1{{color:#17365d;border-bottom:3px solid #17365d;padding-bottom:8px}}
h2{{color:#17365d;margin-top:28px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:9px;text-align:left;vertical-align:top}}
th{{background:#17365d;color:#fff}}
.stats{{display:flex;gap:12px;margin:18px 0;flex-wrap:wrap}}
.stat{{padding:12px 22px;border-radius:8px;color:#fff;font-weight:bold;text-align:center;min-width:100px}}
</style></head><body>
<h1>Relatório de Auditoria Defensiva</h1>
<p><b>Alvo:</b> {escape(host)} | <b>Data:</b> {data} | <b>Falhas:</b> {len(falhas)}</p>
<div class="stats">
<div class="stat" style="background:#b71c1c">Crítico: {nc}</div>
<div class="stat" style="background:#e65100">Alto: {na}</div>
<div class="stat" style="background:#f57f17;color:#333">Médio: {nm}</div>
<div class="stat" style="background:#1b5e20">Baixo: {nb}</div></div>
<h2>Resultados</h2>
<table><tr><th>Status</th><th>Verificação</th><th>Detalhes</th></tr>
{linhas}</table>
<h2>Falhas e Vetores de Ataque</h2>
{blocos if blocos else "<p style='color:green'>✓ Nenhuma falha identificada.</p>"}
<hr style="margin-top:35px"><p style="color:#888;font-size:.82em">
Auditoria Defensiva — {data}</p></body></html>"""


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Auditoria Defensiva")
        self.root.geometry("1020x720")

        self.root.configure(bg=COR_FUNDO)
        self.root.minsize(800, 600)
        self.dados = {}

        self.criar_interface()

    def criar_interface(self):
        # Topo
        topo = tk.Frame(self.root, bg=COR_PAINEL, pady=12, padx=16)
        topo.pack(fill="x")

        tk.Label(
            topo, text="⛨  AUDITORIA DEFENSIVA",
            font=("Segoe UI", 16, "bold"),
            fg=COR_TITULO, bg=COR_PAINEL
        ).pack(side="left")

        tk.Label(topo, text="⛨", font=("Segoe UI", 10), fg=COR_CINZA, bg=COR_PAINEL).pack(side="left", padx=(8, 0), pady=(6, 0))

        # Painel de Entrada
        painel = tk.Frame(self.root, bg=COR_FUNDO, padx=16, pady=10)
        painel.pack(fill="x")

        tk.Label(
            painel, text="ALVO (domínio ou IP autorizado):",
            font=("Segoe UI", 9, "bold"),
            fg=COR_CINZA, bg=COR_FUNDO
        ).pack(anchor="w")

        frame_entrada = tk.Frame(painel, bg=COR_FUNDO)
        frame_entrada.pack(fill="x", pady=(4, 0))

        self.entrada = tk.Entry(
            frame_entrada,
            font=("Consolas", 12),
            bg=COR_ENTRADA, fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat", bd=0,
            highlightthickness=2,
            highlightcolor=COR_TITULO,
            highlightbackground="#2a2a4a"
        )
        self.entrada.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self.entrada.insert(0, "exemplo.com")
        self.entrada.bind("<FocusIn>", self.limpar_placeholder)

        # Botão Iniciar (Verde)
        self.btn_iniciar = tk.Button(
            frame_entrada,
            text="▶  Iniciar Auditoria",
            font=("Segoe UI", 10, "bold"),
            bg=COR_VERDE, fg="#ffffff",
            activebackground="#00a844",
            activeforeground="#ffffff",
            relief="flat", bd=0,
            padx=20, pady=8,
            cursor="hand2",
            command=self.iniciar
        )
        self.btn_iniciar.pack(side="left", padx=(0, 6))

        # Botão Salvar (Abóbora)
        self.btn_salvar = tk.Button(
            frame_entrada,
            text="💾  Salvar HTML",
            font=("Segoe UI", 10, "bold"),
            bg=COR_ABOBORA, fg="#ffffff",
            activebackground="#e67e00",
            activeforeground="#ffffff",
            relief="flat", bd=0,
            padx=20, pady=8,
            cursor="hand2",
            state="disabled",
            command=self.salvar
        )
        self.btn_salvar.pack(side="left")

        # Barra de Progresso
        frame_prog = tk.Frame(self.root, bg=COR_FUNDO, padx=16)
        frame_prog.pack(fill="x", pady=(4, 0))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=COR_PAINEL,
            background=COR_TITULO,
            thickness=6
        )

        self.barra = ttk.Progressbar(
            frame_prog, orient="horizontal",
            mode="determinate", maximum=100,
            style="Custom.Horizontal.TProgressbar"
        )
        self.barra.pack(fill="x")

        self.status_var = tk.StringVar(value="Pronto")
        tk.Label(
            frame_prog, textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg=COR_CINZA, bg=COR_FUNDO, anchor="w"
        ).pack(fill="x", pady=(3, 0))

        # Área de resultados (Aqui estava o erro: as tuplas de pady foram movidas para o método .pack)
        frame_saida = tk.Frame(self.root, bg=COR_FUNDO)
        frame_saida.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        scroll = tk.Scrollbar(frame_saida, bg=COR_PAINEL,
                              troughcolor=COR_FUNDO,
                              activebackground=COR_TITULO)
        scroll.pack(side="right", fill="y")

        self.saida = tk.Text(
            frame_saida,
            wrap="word",
            font=("Consolas", 10),
            bg="#0d1117", fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            relief="flat", bd=0,
            padx=12, pady=10,
            yscrollcommand=scroll.set,
            selectbackground=COR_TITULO,
            selectforeground="#000000"
        )
        self.saida.pack(fill="both", expand=True)
        scroll.config(command=self.saida.yview)

        # Tags de cores nos resultados
        self.saida.tag_configure("titulo", foreground=COR_TITULO, font=("Consolas", 11, "bold"))
        self.saida.tag_configure("subtitulo", foreground=COR_TITULO, font=("Consolas", 10, "bold"))
        self.saida.tag_configure("ok", foreground=COR_OK)
        self.saida.tag_configure("falha", foreground=COR_FALHA)
        self.saida.tag_configure("aviso", foreground=COR_AVISO)
        self.saida.tag_configure("info", foreground=COR_INFO)
        self.saida.tag_configure("aberta", foreground=COR_ABERTA)
        self.saida.tag_configure("critico", foreground=COR_CRITICO, font=("Consolas", 10, "bold"))
        self.saida.tag_configure("alto", foreground=COR_ALTO, font=("Consolas", 10, "bold"))
        self.saida.tag_configure("medio", foreground=COR_MEDIO)
        self.saida.tag_configure("baixo", foreground=COR_BAIXO)
        self.saida.tag_configure("separador", foreground="#3a3a5c")
        self.saida.tag_configure("detalhe", foreground="#90a4ae")
        self.saida.tag_configure("correcao", foreground="#81c784")
        self.saida.tag_configure("explorar", foreground="#ffcc80")
        self.saida.tag_configure("cabecalho_secao", foreground="#ce93d8", font=("Consolas", 10, "bold"))

        # Mensagem inicial do painel
        self.saida.insert("end", "\n  ⛨  Auditoria Defensiva de Serviços\n", "titulo")
        self.saida.insert("end", "  ─" * 25 + "\n\n", "separador")
        self.saida.insert("end", "  Digite um domínio ou IP e clique em ", "detalhe")
        self.saida.insert("end", "Iniciar Auditoria\n\n", "ok")
        self.saida.insert("end", "  ⚠  Use apenas em sistemas autorizados.\n", "aviso")

    def limpar_placeholder(self, event):
        if self.entrada.get() == "exemplo.com":
            self.entrada.delete(0, "end")

    def inserir(self, texto, tag=""):
        self.saida.insert("end", texto, tag)
        self.saida.see("end")

    def iniciar(self):
        valor = self.entrada.get().strip()
        if not valor or valor == "exemplo.com":
            messagebox.showerror("Erro", "Informe um domínio ou IP.")
            return

        try:
            host, esquema = normalizar_host(valor)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        self.btn_iniciar.config(state="disabled")
        self.btn_salvar.config(state="disabled")
        self.barra["value"] = 0
        self.saida.delete("1.0", "end")

        def atualizar(p, msg):
            self.root.after(0, lambda: (
                self.barra.configure(value=p),
                self.status_var.set(f"{p}% — {msg}")
            ))

        def executar():
            aud = Auditoria(host, atualizar)
            resultados, falhas = aud.executar(esquema)
            self.dados = {"host": host, "resultados": resultados, "falhas": falhas}

            def mostrar():
                self.mostrar_resultados(host, resultados, falhas)
                self.btn_iniciar.config(state="normal")
                self.btn_salvar.config(state="normal")
                self.status_var.set("100% — Auditoria concluída")
            self.root.after(0, mostrar)

        threading.Thread(target=executar, daemon=True).start()

    def mostrar_resultados(self, host, resultados, falhas):
        self.saida.delete("1.0", "end")

        self.inserir("\n  ⛨  RELATÓRIO DE AUDITORIA DEFENSIVA\n", "titulo")
        self.inserir("  ─" * 28 + "\n", "separador")
        self.inserir(f"  Alvo: ", "detalhe")
        self.inserir(f"{host}\n", "info")
        self.inserir(f"  Data: ", "detalhe")
        self.inserir(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n", "info")

        self.inserir("  ┌─ RESULTADOS DA VARREDURA ─────────────────────┐\n", "subtitulo")
        self.inserir("  │\n", "separador")

        for r in resultados:
            status = r["status"]
            icone = {"OK": "✓", "ABERTA": "⬤", "AVISO": "⚠", "FALHA": "✗", "INFO": "ℹ"}
            tag = {"OK": "ok", "ABERTA": "aberta", "AVISO": "aviso", "FALHA": "falha", "INFO": "info"}

            self.inserir(f"  │  {icone.get(status, '·')} ", tag.get(status, "info"))
            self.inserir(f"[{status:6s}] ", tag.get(status, "info"))
            self.inserir(f"{r['titulo']}\n", tag.get(status, "info"))
            self.inserir(f"  │           {r['detalhe']}\n", "detalhe")
            self.inserir("  │\n", "separador")

        self.inserir("  └─────────────────────────────────────────────────┘\n\n", "subtitulo")

        nc = sum(1 for f in falhas if f.get("risco") == "CRÍTICO")
        na = sum(1 for f in falhas if f.get("risco") == "ALTO")
        nm = sum(1 for f in falhas if f.get("risco") == "MÉDIO")
        nb = sum(1 for f in falhas if f.get("risco") == "BAIXO")

        self.inserir("  ┌─ RESUMO DE RISCOS ────────────────────────────┐\n", "cabecalho_secao")
        self.inserir("  │\n", "separador")
        self.inserir(f"  │  Total de falhas: {len(falhas)}\n", "info")
        self.inserir("  │\n", "separador")

        if nc > 0:
            self.inserir(f"  │  ██ CRÍTICO:  {nc}\n", "critico")
        if na > 0:
            self.inserir(f"  │  ██ ALTO:     {na}\n", "alto")
        if nm > 0:
            self.inserir(f"  │  ██ MÉDIO:    {nm}\n", "medio")
        if nb > 0:
            self.inserir(f"  │  ██ BAIXO:    {nb}\n", "baixo")

        self.inserir("  │\n", "separador")
        self.inserir("  └─────────────────────────────────────────────────┘\n\n", "cabecalho_secao")

        if nc > 0:
            self.inserir("  ⚠  ATENÇÃO: Falhas CRÍTICAS requerem correção IMEDIATA!\n\n", "critico")

        if falhas:
            self.inserir("  ┌─ FALHAS, VETORES DE ATAQUE E CORREÇÕES ───────┐\n", "subtitulo")
            self.inserir("  │\n", "separador")

            for i, f in enumerate(falhas, 1):
                risco = f.get("risco", "INFO")
                tag_r = {"CRÍTICO": "critico", "ALTO": "alto",
                         "MÉDIO": "medio", "BAIXO": "baixo"}.get(risco, "info")

                self.inserir(f"  │  {'━' * 50}\n", "separador")
                self.inserir(f"  │  FALHA #{i}  ", "subtitulo")
                self.inserir(f"[{risco}]\n", tag_r)
                self.inserir(f"  │  {f['titulo']}\n", tag_r)
                self.inserir(f"  │  {'━' * 50}\n", "separador")
                self.inserir("  │\n", "separador")

                self.inserir("  │  Problema:\n", "info")
                self.inserir(f"  │    {f['detalhe']}\n", "detalhe")
                self.inserir("  │\n", "separador")

                if f.get("descricao_ataque"):
                    self.inserir("  │  Descrição do ataque:\n", "aviso")
                    self.inserir(f"  │    {f['descricao_ataque']}\n", "detalhe")
                    self.inserir("  │\n", "separador")

                if f.get("como_explorar"):
                    self.inserir("  │  ⚡ Como esta falha pode ser explorada:\n", "explorar")
                    for ln in f["como_explorar"]:
                        if ln == "":
                            self.inserir("  │\n", "separador")
                        elif ln.startswith("   "):
                            self.inserir(f"  │      {ln.strip()}\n", "detalhe")
                        else:
                            self.inserir(f"  │    {ln}\n", "explorar")
                    self.inserir("  │\n", "separador")

                self.inserir("  │  ✓ Correção detalhada:\n", "correcao")
                correcao = f.get("correcao_detalhada", f["correcao"])
                for ln in correcao.split("\n"):
                    self.inserir(f"  │    {ln}\n", "correcao")
                self.inserir("  │\n", "separador")

            self.inserir("  └─────────────────────────────────────────────────┘\n\n", "subtitulo")
        else:
            self.inserir("  ✓ Nenhuma falha básica identificada.\n\n", "ok")

        self.inserir("  ─" * 28 + "\n", "separador")
        self.inserir("  Auditoria Defensiva ⛨ — somente para fins educacionais\n", "detalhe")

        self.saida.see("1.0")

    def salvar(self):
        if not self.dados:
            messagebox.showwarning("Aviso", "Execute uma auditoria primeiro.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")]
        )
        if not caminho:
            return

        html = gerar_html(
            self.dados["host"],
            self.dados["resultados"],
            self.dados["falhas"]
        )
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(html)
            messagebox.showinfo("Sucesso", f"Salvo em:\n{caminho}")
        except OSError as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
