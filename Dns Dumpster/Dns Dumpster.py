#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DnsProbe v6.4 - Enumeração DNS por brute-force (wordlist) com geolocalização
(País, Cidade, ISP) e bandeiras em TODOS os registros (A, AAAA, CNAME,
MX, NS, TXT, SOA, SRV, HINFO, CAA), estilo DNSDumpster. Mapa interativo.
Relatório HTML completo COM mapa interativo embutido + exportação TXT.
v6.3: RESULTADOS EM TEMPO REAL + BARRA DE PROGRESSO 0-100%.
v6.4: NOVO registro HINFO (CPU/SO) + varredura de SERVIÇOS SRV comuns
      (SIP, XMPP, LDAP, Kerberos, IMAP, POP3, SMTP, H.323...).
Requisitos: pip install dnspython requests pillow
"""
import io
import random
import re
import socket
import string
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, messagebox, filedialog

from datetime import datetime
from html import escape as esc

import dns.resolver
import dns.reversename
import requests
from PIL import Image, ImageTk

# Compatibilidade Pillow (novo e antigo)
try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

# Cache de reverse DNS (IPs repetidos de CDNs são consultados só 1 vez)
REVERSO_CACHE = {}

# ---------------------------------------------------------------------------
# ISO 3166-1 alpha-2 -> nome do país em português
# ---------------------------------------------------------------------------
CODIGO_PARA_PAIS = {
    "AF": "Afeganistão", "AL": "Albânia", "DZ": "Argélia", "AD": "Andorra",
    "AO": "Angola", "AI": "Anguila", "AQ": "Antártida", "AG": "Antígua e Barbuda",
    "SA": "Arábia Saudita", "AR": "Argentina", "AM": "Armênia", "AW": "Aruba",
    "AU": "Austrália", "AT": "Áustria", "AZ": "Azerbaijão", "BS": "Bahamas",
    "BH": "Bahrein", "BD": "Bangladesh", "BB": "Barbados", "BY": "Bielorrússia",
    "BE": "Bélgica", "BZ": "Belize", "BJ": "Benim", "BM": "Bermudas",
    "BO": "Bolívia", "BA": "Bósnia e Herzegovina", "BW": "Botsuana", "BR": "Brasil",
    "BN": "Brunei", "BG": "Bulgária", "BF": "Burquina Faso", "BI": "Burundi",
    "BT": "Butão", "CV": "Cabo Verde", "CM": "Camarões", "KH": "Camboja",
    "CA": "Canadá", "QA": "Catar", "KZ": "Cazaquistão", "TD": "Chade",
    "CL": "Chile", "CN": "China", "CY": "Chipre", "CO": "Colômbia",
    "KM": "Comores", "CG": "Congo", "CD": "Congo (Rep. Democrática)",
    "KP": "Coreia do Norte", "KR": "Coreia do Sul", "CR": "Costa Rica",
    "CI": "Costa do Marfim", "HR": "Croácia", "CU": "Cuba", "CW": "Curaçau",
    "DK": "Dinamarca", "DJ": "Djibuti", "DM": "Dominica", "EG": "Egito",
    "SV": "El Salvador", "AE": "Emirados Árabes Unidos", "EC": "Equador",
    "ER": "Eritreia", "SK": "Eslováquia", "SI": "Eslovênia", "ES": "Espanha",
    "US": "Estados Unidos", "EE": "Estônia", "SZ": "Essuatíni", "ET": "Etiópia",
    "FJ": "Fiji", "PH": "Filipinas", "FI": "Finlândia", "FR": "França",
    "GA": "Gabão", "GM": "Gâmbia", "GH": "Gana", "GE": "Geórgia",
    "GI": "Gibraltar", "GD": "Granada", "GR": "Grécia", "GL": "Groenlândia",
    "GP": "Guadalupe", "GU": "Guam", "GT": "Guatemala", "GY": "Guiana",
    "GF": "Guiana Francesa", "GN": "Guiné", "GQ": "Guiné Equatorial",
    "GW": "Guiné-Bissau", "HT": "Haiti", "HN": "Honduras", "HK": "Hong Kong",
    "HU": "Hungria", "YE": "Iêmen", "CX": "Ilha Christmas", "NF": "Ilha Norfolk",
    "KY": "Ilhas Cayman", "CK": "Ilhas Cook", "FK": "Ilhas Malvinas",
    "MH": "Ilhas Marshall", "SB": "Ilhas Salomão", "TC": "Ilhas Turcas e Caicos",
    "VG": "Ilhas Virgens Britânicas", "VI": "Ilhas Virgens Americanas",
    "IN": "Índia", "ID": "Indonésia", "IR": "Irã", "IQ": "Iraque",
    "IE": "Irlanda", "IS": "Islândia", "IL": "Israel", "IT": "Itália",
    "JM": "Jamaica", "JP": "Japão", "JO": "Jordânia", "KI": "Kiribati",
    "KW": "Kuwait", "LA": "Laos", "LS": "Lesoto", "LV": "Letônia",
    "LB": "Líbano", "LR": "Libéria", "LY": "Líbia", "LI": "Liechtenstein",
    "LT": "Lituânia", "LU": "Luxemburgo", "MO": "Macau", "MK": "Macedônia do Norte",
    "MG": "Madagascar", "MY": "Malásia", "MW": "Malauí", "MV": "Maldivas",
    "ML": "Mali", "MT": "Malta", "MA": "Marrocos", "MQ": "Martinica",
    "MU": "Maurício", "MR": "Mauritânia", "YT": "Mayotte", "MX": "México",
    "MM": "Mianmar", "FM": "Micronésia", "MZ": "Moçambique", "MD": "Moldávia",
    "MC": "Mônaco", "MN": "Mongólia", "ME": "Montenegro", "MS": "Montserrat",
    "NA": "Namíbia", "NR": "Nauru", "NP": "Nepal", "NI": "Nicarágua",
    "NE": "Níger", "NG": "Nigéria", "NU": "Niue", "NO": "Noruega",
    "NC": "Nova Caledônia", "NZ": "Nova Zelândia", "OM": "Omã",
    "NL": "Países Baixos (Holanda)", "PW": "Palau", "PA": "Panamá",
    "PG": "Papua-Nova Guiné", "PK": "Paquistão", "PY": "Paraguai", "PE": "Peru",
    "PF": "Polinésia Francesa", "PL": "Polônia", "PR": "Porto Rico", "PT": "Portugal",
    "KE": "Quênia", "KG": "Quirguistão", "GB": "Reino Unido", "CF": "República Centro-Africana",
    "DO": "República Dominicana", "RE": "Reunião", "RO": "Romênia", "RW": "Ruanda",
    "RU": "Rússia", "EH": "Saara Ocidental", "WS": "Samoa", "AS": "Samoa Americana",
    "SM": "San Marino", "BL": "São Bartolomeu", "KN": "São Cristóvão e Neves",
    "MF": "São Martinho (França)", "SX": "São Martinho (Holanda)", "PM": "São Pedro e Miquelão",
    "ST": "São Tomé e Príncipe", "VC": "São Vicente e Granadinas", "LC": "Santa Lúcia",
    "SC": "Seicheles", "SN": "Senegal", "SL": "Serra Leoa", "RS": "Sérvia",
    "SG": "Singapura", "SY": "Síria", "SO": "Somália", "LK": "Sri Lanka",
    "SD": "Sudão", "SS": "Sudão do Sul", "SE": "Suécia", "CH": "Suíça",
    "SR": "Suriname", "TH": "Tailândia", "TW": "Taiwan", "TJ": "Tajiquistão",
    "TZ": "Tanzânia", "CZ": "Tchéquia", "IO": "Território Britânico do Oceano Índico",
    "TL": "Timor-Leste", "TG": "Togo", "TK": "Tokelau", "TO": "Tonga",
    "TT": "Trinidad e Tobago", "TN": "Tunísia", "TR": "Turquia", "TV": "Tuvalu",
    "UA": "Ucrânia", "UG": "Uganda", "UY": "Uruguai", "UZ": "Uzbequistão",
    "VU": "Vanuatu", "VA": "Vaticano", "VE": "Venezuela", "VN": "Vietnã",
    "ZM": "Zâmbia", "ZW": "Zimbábue",
}

# >>> v6.4: HINFO adicionado aos tipos reais (CPU/SO do servidor)
TIPOS = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV", "HINFO", "CAA"]

# >>> v6.4: chave interna dos SRV de serviços comuns (não é tipo DNS real)
SRV_SERVICOS_KEY = "SRV_SERVICOS"

# >>> v6.4: ordem de exibição na tabela/report (SRV_SERVICOS logo após SRV)
ORDEM = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV",
         SRV_SERVICOS_KEY, "HINFO", "CAA"]

# >>> v6.4: serviços SRV mais comuns (consultados em "_servico._proto.dominio")
COMMON_SRV_SERVICES = [
    "_sip._tcp", "_sip._udp", "_sips._tcp", "_h323cs._tcp", "_h323ls._udp",
    "_sip._tls", "_jabber._tcp", "_xmpp._tcp", "_ldap._tcp", "_kerberos._tcp",
    "_kerberos._udp", "_imap._tcp", "_pop3._tcp", "_smtp._tcp",
]

# Espaço do mapa (coordenadas do "mundo", independentes do tamanho da janela)
WORLD_W, WORLD_H = 1100, 620


# ---------------------------------------------------------------------------
# Camada de coleta
# ---------------------------------------------------------------------------

def detectar_wildcard(dominio):
    """Verifica se o domínio usa wildcard DNS (responde a qualquer nome)."""
    nome = "".join(random.choices(string.ascii_lowercase, k=14)) + "." + dominio
    try:
        resp = dns.resolver.resolve(nome, "A", lifetime=5)
        return bool(resp.rrset)
    except Exception:
        return False


def enum_subdominios_wordlist(dominio, caminho_wordlist, progresso=None, encontrado=None):
    """
    Brute-force de subdomínios usando uma wordlist via DNS.
    Cada linha da wordlist é testada como <palavra>.<dominio> (registro A).
    `progresso(i, total, palavra)` é chamado periodicamente (barra 0-100%).
    `encontrado(nome)` é chamado IMEDIATAMENTE para cada subdomínio vivo,
    permitindo exibir resultados em tempo real na interface.
    """
    try:
        with open(caminho_wordlist, "r", encoding="utf-8", errors="ignore") as f:
            palavras = [linha.strip().lower() for linha in f if linha.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"Wordlist não encontrada: {caminho_wordlist}")
    if not palavras:
        raise ValueError("Wordlist vazia.")

    if detectar_wildcard(dominio):
        raise RuntimeError(
            "Wildcard DNS detectado: o domínio responde para qualquer subdomínio.\n"
            "O brute-force geraria falsos positivos. Verifique a configuração do alvo.")

    subs = set()
    total = len(palavras)
    for i, palavra in enumerate(palavras, 1):
        if progresso and (i % 25 == 0 or i == total):
            progresso(i, total, palavra)
        nome = f"{palavra}.{dominio}"
        try:
            resp = dns.resolver.resolve(nome, "A", lifetime=4, raise_on_no_answer=False)
            if resp.rrset:
                subs.add(nome)
                if encontrado:
                    encontrado(nome)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            continue
        except Exception:
            continue
    return sorted(subs)


def consultar(dominio, tipo):
    """Consulta um tipo de registro DNS e retorna lista de strings."""
    try:
        resp = dns.resolver.resolve(dominio, tipo, lifetime=10, raise_on_no_answer=False)
        if not resp.rrset:
            return ["(sem registros)"]
        return [r.to_text() for r in resp.rrset]
    except dns.resolver.NXDOMAIN:
        return ["(domínio não existe)"]
    except dns.resolver.NoNameservers:
        return ["(sem nameservers respondendo)"]
    except Exception as e:
        return [f"(erro: {e.__class__.__name__})"]


def ips_de(dominio):
    """Resolve todos os IPs (A) de um host."""
    return [r for r in consultar(dominio, "A") if not r.startswith("(")]


def reverso(ip):
    """
    Reverse DNS de um IP usando dnspython:
    dns.reversename.from_address() monta o nome PTR (in-addr.arpa) e o
    resolver consulta o registro PTR — muito mais confiável que depender
    do resolver do sistema. Se falhar, tenta socket.gethostbyaddr.
    Resultados são cacheados (IPs repetidos de CDNs não são reconsultados).
    """
    if ip in REVERSO_CACHE:
        return REVERSO_CACHE[ip]
    try:
        nome_reverso = dns.reversename.from_address(ip)
        resp = dns.resolver.resolve(nome_reverso, "PTR", lifetime=6)
        resultado = resp[0].to_text().rstrip(".")
    except Exception:
        try:
            resultado = socket.gethostbyaddr(ip)[0]
        except Exception:
            resultado = ip
    REVERSO_CACHE[ip] = resultado
    return resultado


def _reversos(ips, limite=5):
    """
    Resolve o reverse DNS de até `limite` IPs em paralelo e junta com ", ".
    Se não houver IPs, retorna "-".
    """
    if not ips:
        return "-"
    with ThreadPoolExecutor(max_workers=16) as pool:
        return ", ".join(pool.map(reverso, ips[:limite]))


def hostnames_de_txt(valor):
    """
    Extrai possíveis hostnames de um registro TXT (SPF/DKIM/DMARC),
    para conseguir geolocalizar e mostrar a bandeira.
    """
    nomes = []
    texto = valor.lower()
    for m in re.findall(r'(?:include:|redirect=|_dmarc\.|a=|mx=)([a-z0-9._-]+\.[a-z]{2,})', texto):
        nomes.append(m.rstrip("."))
    for token in re.findall(r'[a-z0-9_][a-z0-9_.-]*\.[a-z]{2,}', texto):
        token = token.rstrip(".")
        if token not in nomes:
            nomes.append(token)
    return nomes


def hostnames_de_caa(valor):
    """Extrai o domínio do emissor de um registro CAA (ex.: letsencrypt.org)."""
    m = re.search(r'"([a-z0-9._-]+\.[a-z]{2,})"', valor.lower())
    if m:
        return [m.group(1).rstrip(".")]
    return []


def hostname_principal(tipo, valor):
    """
    >>> v6.4: extrai o hostname principal de um valor de registro para o mapa
    e a lista de hosts. SRV/SRV_SERVICOS mostram o ALVO (não a prioridade),
    MX mostra o servidor de e-mail.
    """
    partes = valor.split()
    if not partes:
        return valor
    if tipo == "SRV":
        return partes[3].rstrip(".") if len(partes) > 3 else valor
    if tipo == SRV_SERVICOS_KEY:
        # formato: "_sip._tcp 0 5 5060 alvo.exemplo.com"
        return partes[4].rstrip(".") if len(partes) > 4 else partes[0]
    if tipo == "MX":
        return partes[1].rstrip(".") if len(partes) > 1 else valor
    return partes[0].rstrip(".")


def ips_de_registro(tipo, valor):
    """
    Descobre os IPs associados a um registro DNS, para geolocalização.
    A/AAAA -> o próprio valor é o IP;
    MX/NS/CNAME/SOA/SRV -> resolve o hostname;
    TXT -> extrai hostnames do SPF/DKIM/DMARC e resolve;
    CAA -> resolve o domínio do emissor;
    HINFO -> CPU/SO, não tem hostname (retorna vazio);
    SRV_SERVICOS -> resolve o alvo do serviço.
    """
    if valor.startswith("("):
        return []
    tokens = valor.split()
    if not tokens:
        return []
    if tipo in ("A", "AAAA"):
        return [tokens[0]]
    if tipo == "HINFO":
        return []   # >>> v6.4: HINFO é "CPU" "OS" — não resolve IPs
    if tipo == SRV_SERVICOS_KEY:
        # "_sip._tcp 0 5 5060 alvo." -> alvo em tokens[4]
        hosts = [tokens[4].rstrip(".")] if len(tokens) > 4 else []
    elif tipo == "TXT":
        hosts = hostnames_de_txt(valor)
    elif tipo == "CAA":
        hosts = hostnames_de_caa(valor)
    elif tipo == "MX":
        hosts = [tokens[1].rstrip(".")] if len(tokens) > 1 else []
    elif tipo == "SOA":
        hosts = [tokens[0].rstrip(".")]
    elif tipo == "SRV":
        hosts = [tokens[3].rstrip(".")] if len(tokens) > 3 else []
    else:  # NS, CNAME
        hosts = [tokens[0].rstrip(".")]
    ips = []
    for h in hosts:
        h = h.strip()
        if not h or h == ".":
            continue
        ips.extend(ips_de(h))
    return ips


def consultar_srv_servicos(dominio, progresso=None):
    """
    >>> v6.4: consulta os registros SRV dos serviços mais comuns
    (SIP, XMPP, LDAP, Kerberos, IMAP, POP3, SMTP, H.323...).
    Cada entrada retornada tem o formato: "_sip._tcp 0 5 5060 alvo.exemplo.com"
    """
    resultados = []
    total = len(COMMON_SRV_SERVICES)
    for i, servico in enumerate(COMMON_SRV_SERVICES, 1):
        if progresso:
            progresso(i, total, servico)
        nome = f"{servico}.{dominio}"
        for valor in consultar(nome, "SRV"):
            if valor.startswith("("):
                continue
            resultados.append(f"{servico} {valor}")
    return resultados


def geolocalizar_ips(ips):
    """
    Geolocaliza uma lista de IPs via ip-api.com (gratuito, até 100 IPs por lote).
    Tenta HTTPS primeiro e cai para HTTP (o plano gratuito do ip-api só
    garante HTTP; HTTPS funciona em muitos casos com User-Agent).
    Retorna {ip: (codigo_iso, nome_pais_pt, cidade, isp)}.
    """
    resultado = {}
    ips = list(dict.fromkeys(ips))  # remove duplicados, preserva ordem
    cab = {"User-Agent": "DnsProbe/6.4"}
    for i in range(0, len(ips), 100):
        lote = ips[i:i + 100]
        dados = None
        for base in ("https://ip-api.com/batch", "http://ip-api.com/batch"):
            try:
                r = requests.post(
                    f"{base}?fields=status,query,country,countryCode,city,isp,org",
                    json=lote, timeout=12, headers=cab)
                if r.status_code == 200:
                    dados = r.json()
                    break
            except requests.RequestException:
                continue
        if not dados:
            continue
        for item in dados:
            if item.get("status") == "success":
                cod = item.get("countryCode", "").upper()
                cidade = item.get("city", "") or ""
                isp = item.get("isp", "") or item.get("org", "") or ""
                resultado[item["query"]] = (
                    cod,
                    CODIGO_PARA_PAIS.get(cod, item.get("country", "?")),
                    cidade,
                    isp)
    return resultado


def baixar_bandeira(codigo):
    """Baixa a bandeira do país via flagcdn.com e retorna PhotoImage (24x16)."""
    try:
        url = f"https://flagcdn.com/w160/{codigo.lower()}.png"
        img_data = requests.get(url, timeout=8,
                                headers={"User-Agent": "DnsProbe/6.4"}).content
        img = Image.open(io.BytesIO(img_data)).resize((24, 16), RESAMPLE)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Interface gráfica
# ---------------------------------------------------------------------------

class DnsProbeApp:
    def __init__(self, root):
        self.root = root
        root.title("Dns Dumpster - Enumeração DNS")
        root.geometry("1150x720")
        root.state("zoomed")
        root.minsize(860, 540)

        # ---- Barra superior ----
        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Domínio:").pack(side="left")
        self.ent_dominio = ttk.Entry(top, width=28)
        self.ent_dominio.pack(side="left", padx=6)
        self.ent_dominio.bind("<Return>", lambda e: self.consultar_tudo())

        ttk.Label(top, text="Wordlist:").pack(side="left", padx=(10, 0))
        self.ent_wordlist = ttk.Entry(top, width=22)
        self.ent_wordlist.insert(0, "")
        self.ent_wordlist.pack(side="left", padx=6)
        ttk.Button(top, text="...", width=3,
                   command=self.escolher_wordlist).pack(side="left")

        self.btn_tudo = ttk.Button(top, text="Enumerar tudo", command=self.consultar_tudo)
        self.btn_tudo.pack(side="left", padx=6)
        self.btn_sub = ttk.Button(top, text="Só subdomínios", command=self.consultar_subdominios)
        self.btn_sub.pack(side="left", padx=6)
        self.btn_html = ttk.Button(top, text="Salvar HTML", command=self.salvar_html)
        self.btn_html.pack(side="left", padx=6)
        self.btn_txt = ttk.Button(top, text="Salvar TXT", command=self.salvar_txt)
        self.btn_txt.pack(side="left", padx=6)

        # ---- Barra de status + BARRA DE PROGRESSO (0-100%) ----
        barra_status = ttk.Frame(root, padding=(8, 0, 8, 4))
        barra_status.pack(fill="x")
        self.lbl_status = ttk.Label(barra_status, text="Pronto.")
        self.lbl_status.pack(side="left")
        self.barra_progresso = ttk.Progressbar(barra_status, mode="determinate",
                                               maximum=100, value=0)
        self.barra_progresso.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_pct = ttk.Label(barra_status, text="0%", width=5, anchor="e")
        self.lbl_pct.pack(side="left")

        # ---- Abas ----
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_dns = self._criar_tab_dns()
        self.tab_subdominios = self._criar_tab_subdominios()
        self.tab_mapa = self._criar_tab_mapa()

        self.registros_cache = {}   # tipo -> [valores]
        self.registros_detalhe = {} # (tipo, valor) -> [ips]
        self.subdominios_cache = [] # [sub, ips, pais, reverso]
        self.geo_cache = {}         # ip -> (codigo_iso, nome_pais_pt, cidade, isp)
        self.flag_images = []       # mantém referência das PhotoImages
        self.flag_cache = {}        # codigo -> PhotoImage (evita baixar de novo)
        self._ips_por_sub = {}      # sub -> [ips] (tempo real)

        root.bind("<Control-s>", lambda e: self.salvar_html())
        root.bind("<Control-t>", lambda e: self.salvar_txt())

    # ------------------------------------------------------------------ abas
    def _criar_tab_dns(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Registros DNS")

        barra = ttk.Frame(tab, padding=4)
        barra.pack(fill="x")
        self.var_tipo = tk.StringVar(value="A")
        for t in TIPOS:
            ttk.Radiobutton(barra, text=t, value=t, variable=self.var_tipo,
                            command=self.consultar_registro).pack(side="left", padx=3)
        ttk.Button(barra, text="Consultar", command=self.consultar_registro).pack(side="left", padx=8)
        ttk.Label(barra, text="(Ctrl+C copia a linha selecionada)",
                  foreground="#888").pack(side="right")

        # ---- Frame para Treeview + Scrollbars ----
        frame_tree = ttk.Frame(tab)
        frame_tree.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("tipo", "valor", "pais", "cidade", "isp")
        self.tree_dns = ttk.Treeview(frame_tree, columns=cols, show="tree headings", height=22)

        # Cabeçalhos
        self.tree_dns.heading("#0", text="Flag", anchor="w")
        self.tree_dns.heading("tipo", text="Tipo", anchor="w")
        self.tree_dns.heading("valor", text="Valor", anchor="w")
        self.tree_dns.heading("pais", text="País", anchor="w")
        self.tree_dns.heading("cidade", text="Cidade", anchor="w")
        self.tree_dns.heading("isp", text="ISP / Org", anchor="w")

        # Colunas
        self.tree_dns.column("#0", width=60, anchor="w", stretch=False)
        self.tree_dns.column("tipo", width=100, anchor="w", stretch=False)
        self.tree_dns.column("valor", width=600, anchor="w", stretch=False)
        self.tree_dns.column("pais", width=160, anchor="w", stretch=False)
        self.tree_dns.column("cidade", width=120, anchor="w", stretch=False)
        self.tree_dns.column("isp", width=220, anchor="w", stretch=False)

        # Scrollbars
        vs = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_dns.yview)
        hs = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree_dns.xview)

        self.tree_dns.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)

        # Layout
        self.tree_dns.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")

        frame_tree.rowconfigure(0, weight=1)
        frame_tree.columnconfigure(0, weight=1)

        return tab

    def _criar_tab_subdominios(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Subdomínios")

        # Painel País
        self.painel_pais = ttk.LabelFrame(tab, text="País", padding=6)
        self.painel_pais.pack(fill="x", padx=4, pady=(4, 0))

        # Frame da tabela
        frame_tree = ttk.Frame(tab)
        frame_tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Tabela
        colunas = ("sub", "ip", "pais", "reverso")

        self.tree_sub = ttk.Treeview(
            frame_tree,
            columns=colunas,
            show="tree headings"
        )

        # Cabeçalhos
        self.tree_sub.heading("#0", text="Flag", anchor="w")
        self.tree_sub.heading("sub", text="Subdomínio", anchor="w")
        self.tree_sub.heading("ip", text="IP", anchor="w")
        self.tree_sub.heading("pais", text="País (ISO)", anchor="w")
        self.tree_sub.heading("reverso", text="Reverse DNS", anchor="w")

        # Colunas
        self.tree_sub.column("#0", width=60, anchor="w", stretch=False)
        self.tree_sub.column("sub", width=400, anchor="w", stretch=False)
        self.tree_sub.column("ip", width=650, anchor="w", stretch=False)
        self.tree_sub.column("pais", width=220, anchor="w", stretch=False)
        self.tree_sub.column("reverso", width=2000, anchor="w", stretch=False)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_sub.yview)
        scrollbar_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree_sub.xview)
        self.tree_sub.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Layout
        self.tree_sub.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Canto entre as duas barras (opcional)
        ttk.Frame(frame_tree, width=16, height=16).grid(row=1, column=1)

        frame_tree.grid_rowconfigure(0, weight=1)
        frame_tree.grid_columnconfigure(0, weight=1)

        # Eventos
        self.tree_sub.bind("<Control-c>", lambda e: self._copiar_selecao(self.tree_sub))

        return tab

    def _ajustar_colunas(self, event=None):
        """Faz as colunas da tabela de subdomínios ocuparem toda a largura."""
        total = self.tree_sub.winfo_width()
        if total < 50:
            return
        largura_flag = 50
        restante = total - largura_flag
        proporcoes = {"sub": 0.29, "ip": 0.21, "pais": 0.20, "reverso": 0.30}
        self.tree_sub.column("#0", width=largura_flag)
        for col, peso in proporcoes.items():
            self.tree_sub.column(col, width=int(restante * peso))

    def _criar_tab_mapa(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Mapa da infraestrutura")

        barra = ttk.Frame(tab, padding=2)
        barra.pack(fill="x")
        ttk.Label(barra, text="Arraste nó: reposicionar | Arraste fundo: pan | Scroll: zoom | "
                              "2x clique: copiar | Botão direito: menu",
                  foreground="#555").pack(side="left")
        ttk.Button(barra, text="＋", width=3,
                   command=lambda: self._aplicar_zoom(1.25, self.canvas.winfo_width() // 2,
                                                      self.canvas.winfo_height() // 2)).pack(side="right")
        ttk.Button(barra, text="－", width=3,
                   command=lambda: self._aplicar_zoom(0.8, self.canvas.winfo_width() // 2,
                                                      self.canvas.winfo_height() // 2)).pack(side="right")
        ttk.Button(barra, text="Centralizar", command=self._centralizar_mapa).pack(side="right", padx=4)
        ttk.Button(barra, text="Copiar hosts", command=self._copiar_hosts).pack(side="right")

        self.canvas = tk.Canvas(tab, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        # Estado do mapa (pan/zoom + nós arrastáveis)
        self.mapa_offset = [0.0, 0.0]
        self.mapa_zoom = 1.0
        self.mapa_inicializado = False
        self.mapa_nos = []           # (x1, y1, x2, y2, texto) em pixels da tela
        self.mapa_nos_data = []      # dados persistentes dos nós (coords do mundo)
        self.mapa_selecionado = None # índice do nó selecionado
        self.mapa_arrastando = False
        self.mapa_dragging_node = None  # índice do nó sendo arrastado (ou None = pan)
        self.mapa_press_xy = (0, 0)
        self.mapa_press_ini = (0, 0) # posição inicial do clique

        self.canvas.bind("<ButtonPress-1>", self.mapa_press)
        self.canvas.bind("<B1-Motion>", self.mapa_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mapa_release)
        self.canvas.bind("<Double-Button-1>", self.mapa_double)
        self.canvas.bind("<Button-3>", self.mapa_menu)
        self.canvas.bind("<MouseWheel>", self.mapa_zoom_evt)
        self.canvas.bind("<Button-4>", self.mapa_zoom_evt)   # Linux
        self.canvas.bind("<Button-5>", self.mapa_zoom_evt)   # Linux
        self.canvas.bind("<Configure>", lambda e: self.desenhar_mapa())
        return tab

    # ------------------------------------------------------------- utilidades
    def escolher_wordlist(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar wordlist", filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if caminho:
            self.ent_wordlist.delete(0, "end")
            self.ent_wordlist.insert(0, caminho)

    def dominio_atual(self):
        d = self.ent_dominio.get().strip().lower().lstrip(".").rstrip(".")
        if not d:
            messagebox.showwarning("DnsProbe", "Informe um domínio primeiro.")
            return None
        if "." not in d:
            messagebox.showwarning("DnsProbe", "Domínio inválido. Ex.: example.com")
            return None
        return d

    def _set_status(self, msg):
        self.lbl_status.config(text=msg)

    def _status_thread(self, msg):
        """Atualiza o status com segurança a partir de uma thread."""
        self.root.after(0, lambda m=msg: self._set_status(m))

    # --------------------------- progresso (barra 0-100%) ------------------
    def _reset_progresso(self, msg):
        """Zera a barra de progresso e define a mensagem inicial."""
        self.barra_progresso["value"] = 0
        self.lbl_pct.config(text="0%")
        self._set_status(msg)

    def _set_progresso(self, pct, msg=None):
        """Define o valor da barra (0-100) e a mensagem de status."""
        pct = max(0.0, min(100.0, float(pct)))
        self.barra_progresso["value"] = pct
        self.lbl_pct.config(text=f"{int(round(pct))}%")
        if msg:
            self._set_status(msg)

    def _progresso(self, pct, msg=None):
        """Atualiza a barra de progresso com segurança a partir de uma thread."""
        self.root.after(0, lambda p=pct, m=msg: self._set_progresso(p, m))

    # --------------------------- tempo real --------------------------------
    def _add_sub_linha_live(self, sub, ips):
        """
        Insere um subdomínio recém-descoberto EM TEMPO REAL na tabela.
        País e reverse são preenchidos na renderização final.
        """
        ips_str = ", ".join(ips) or "-"
        cod = pais = ""
        if ips and ips[0] in self.geo_cache:
            cod, pais, _, _ = self.geo_cache[ips[0]]
            pais = f"{pais} ({cod})"
        self._inserir_linha(self.tree_sub, ("sub", "ip", "pais", "reverso"),
                            (sub, ips_str, pais, ""))

    def _copiar(self, texto):
        """Copia texto para a área de transferência."""
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self._set_status("Copiado para a área de transferência.")

    def _copiar_selecao(self, tree):
        """Copia as linhas selecionadas de um Treeview (Ctrl+C)."""
        linhas = []
        for iid in tree.selection():
            valores = [str(v) for v in tree.item(iid, "values")]
            linhas.append("\t".join(valores))
        if linhas:
            self._copiar("\n".join(linhas))

    def _flag(self, codigo):
        """Bandeira com cache (evita baixar a mesma imagem várias vezes)."""
        if codigo in self.flag_cache:
            return self.flag_cache[codigo]
        img = baixar_bandeira(codigo)
        if img:
            self.flag_cache[codigo] = img
            self.flag_images.append(img)
        return img

    def _inserir_linha(self, tree, colunas, valores, flag=None):
        """
        Insere uma linha no Treeview de forma à prova de erro do Tcl.
        Cria o item vazio, preenche coluna por coluna com tree.set()
        e aplica a imagem depois com tree.item().
        """
        iid = tree.insert("", "end", text="")
        for col, val in zip(colunas, valores):
            tree.set(iid, col, str(val))
        if flag is not None:
            try:
                tree.item(iid, image=flag)
            except tk.TclError:
                pass
        return iid

    def _enriquecer_registros(self, tipos):
        """
        Descobre IPs de cada registro e geolocaliza (País/Cidade/ISP).
        Só remove os detalhes dos tipos recalculados, preservando os demais.
        """
        for k in [k for k in self.registros_detalhe if k[0] in tipos]:
            del self.registros_detalhe[k]
        ips_todos = []
        for t in tipos:
            for v in self.registros_cache.get(t, []):
                ips = ips_de_registro(t, v)
                self.registros_detalhe[(t, v)] = ips
                ips_todos.extend(ips)
        self.geo_cache.update(geolocalizar_ips(ips_todos))

    # ---------------------------------------------------------------- ações
    def consultar_tudo(self):
        d = self.dominio_atual()
        if not d:
            return
        self.notebook.select(self.tab_subdominios)   # mostra resultados ao vivo
        self._reset_progresso("Iniciando enumeração completa...")
        threading.Thread(target=self._trabalho_tudo, args=(d,), daemon=True).start()

    def _trabalho_tudo(self, dominio):
        """
        Enumerar tudo com BARRA DE PROGRESSO faseada:
        0-55% brute-force | 56-66% registros DNS | 66-69% serviços SRV
        70-75% geo registros | 78-95% geo subdomínios | 95-100% reverse DNS
        """
        wordlist = self.ent_wordlist.get().strip()
        try:
            self._ips_por_sub = {}
            self._status_thread("Brute-force de subdomínios (wordlist)...")

            def on_progresso(i, t, p):
                self._progresso((i / t) * 55.0, f"Testando {p} ({i}/{t})...")

            def on_encontrado(nome):
                ips = ips_de(nome)
                self._ips_por_sub[nome] = ips
                self.root.after(0, lambda n=nome, i=ips: self._add_sub_linha_live(n, i))

            subs = enum_subdominios_wordlist(dominio, wordlist,
                                             progresso=on_progresso,
                                             encontrado=on_encontrado)

            self._progresso(56, f"Consultando registros DNS de {dominio}...")
            self.registros_cache = {}
            n_tipos = len(TIPOS)
            for j, t in enumerate(TIPOS, 1):
                self.registros_cache[t] = consultar(dominio, t)
                self._progresso(56 + (j / n_tipos) * 10, f"Consultando registro {t}...")

            # >>> v6.4: serviços SRV comuns (SIP, XMPP, LDAP, Kerberos...)
            self._progresso(66, "Verificando serviços SRV comuns...")
            def on_srv_prog(i, t, s):
                self._progresso(66 + (i / t) * 3, f"SRV {s} ({i}/{t})...")
            self.registros_cache[SRV_SERVICOS_KEY] = consultar_srv_servicos(
                dominio, progresso=on_srv_prog)

            self._progresso(70, "Geolocalizando registros DNS...")
            self._enriquecer_registros(TIPOS + [SRV_SERVICOS_KEY])
            self._progresso(75, "Registros geolocalizados.")
            self.root.after(0, lambda: self._preencher_registros(dominio))

            linhas = [[sub, self._ips_por_sub.get(sub, [])] for sub in subs]
            ips_unicos = []
            for _s, ips in linhas:
                ips_unicos.extend(ips)

            self._progresso(78, "Geolocalizando subdomínios...")
            self.geo_cache.update(geolocalizar_ips(ips_unicos))
            self._progresso(95, "Geolocalização concluída.")

            self.subdominios_cache = []
            total_subs = len(linhas)
            for idx, (sub, ips) in enumerate(linhas, 1):
                if ips:
                    cod, pais, _, _ = self.geo_cache.get(ips[0], ("?", "?", "", ""))
                else:
                    cod, pais = "?", "?"
                reversos = _reversos(ips)
                self.subdominios_cache.append([sub, ", ".join(ips) or "-",
                                               f"{pais} ({cod})", reversos])
                self._progresso(95 + (idx / total_subs) * 5,
                                f"Reverse DNS {idx}/{total_subs}...")

            self.root.after(0, lambda: self._preencher_subdominios())
            self.root.after(0, lambda: self._set_progresso(
                100, f"Concluído: {len(subs)} subdomínios."))
            self.root.after(0, lambda: self.notebook.select(self.tab_mapa))
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            msg = str(e)
            self.root.after(0, lambda m=msg: messagebox.showerror("DnsProbe", m))
            self.root.after(0, lambda: self._set_status("Erro."))
        except Exception as e:
            msg = f"Erro: {e}"
            self.root.after(0, lambda m=msg: messagebox.showerror("DnsProbe", m))
            self.root.after(0, lambda: self._set_status("Erro."))

    def consultar_subdominios(self):
        d = self.dominio_atual()
        if not d:
            return
        self.notebook.select(self.tab_subdominios)   # mostra resultados ao vivo
        self._reset_progresso("Iniciando enumeração de subdomínios...")
        threading.Thread(target=self._trabalho_sub, args=(d,), daemon=True).start()

    def _trabalho_sub(self, dominio):
        """
        Só subdomínios com BARRA DE PROGRESSO faseada:
        0-70% brute-force | 72-95% geolocalização | 95-100% reverse DNS
        """
        wordlist = self.ent_wordlist.get().strip()
        try:
            self._ips_por_sub = {}
            self._status_thread("Brute-force de subdomínios (wordlist)...")

            def on_progresso(i, t, p):
                self._progresso((i / t) * 70.0, f"Testando {p} ({i}/{t})...")

            def on_encontrado(nome):
                ips = ips_de(nome)
                self._ips_por_sub[nome] = ips
                self.root.after(0, lambda n=nome, i=ips: self._add_sub_linha_live(n, i))

            subs = enum_subdominios_wordlist(dominio, wordlist,
                                             progresso=on_progresso,
                                             encontrado=on_encontrado)

            linhas = [[sub, self._ips_por_sub.get(sub, [])] for sub in subs]
            ips_unicos = []
            for _s, ips in linhas:
                ips_unicos.extend(ips)

            self._progresso(72, "Geolocalizando subdomínios...")
            self.geo_cache.update(geolocalizar_ips(ips_unicos))
            self._progresso(95, "Geolocalização concluída.")

            self.subdominios_cache = []
            total_subs = len(linhas)
            for idx, (sub, ips) in enumerate(linhas, 1):
                if ips:
                    cod, pais, _, _ = self.geo_cache.get(ips[0], ("?", "?", "", ""))
                else:
                    cod, pais = "?", "?"
                reversos = _reversos(ips)
                self.subdominios_cache.append([sub, ", ".join(ips) or "-",
                                               f"{pais} ({cod})", reversos])
                self._progresso(95 + (idx / total_subs) * 5,
                                f"Reverse DNS {idx}/{total_subs}...")

            self.root.after(0, lambda: self._preencher_subdominios())
            self.root.after(0, lambda: self._set_progresso(
                100, f"Concluído: {len(subs)} subdomínios."))
            self.root.after(0, lambda: self.notebook.select(self.tab_subdominios))
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            msg = str(e)
            self.root.after(0, lambda m=msg: messagebox.showerror("DnsProbe", m))
            self.root.after(0, lambda: self._set_status("Erro."))
        except Exception as e:
            msg = f"Erro: {e}"
            self.root.after(0, lambda m=msg: messagebox.showerror("DnsProbe", m))
            self.root.after(0, lambda: self._set_status("Erro."))

    def consultar_registro(self):
        d = self.dominio_atual()
        if not d:
            return
        tipo = self.var_tipo.get()
        threading.Thread(target=self._trabalho_reg, args=(d, tipo), daemon=True).start()

    def _trabalho_reg(self, dominio, tipo):
        try:
            self._status_thread(f"Consultando registro {tipo}...")
            valores = consultar(dominio, tipo)
            self.registros_cache[tipo] = valores
            extras = []
            # >>> v6.4: no botão SRV também verifica os serviços comuns
            if tipo == "SRV":
                self._status_thread("Verificando serviços SRV comuns...")
                self.registros_cache[SRV_SERVICOS_KEY] = consultar_srv_servicos(dominio)
                extras.append(SRV_SERVICOS_KEY)
            self._status_thread(f"Geolocalizando registros {tipo}...")
            self._enriquecer_registros([tipo] + extras)
            self.root.after(0, lambda: self._preencher_registros(dominio))
        except Exception as e:
            msg = f"Erro: {e}"
            self.root.after(0, lambda m=msg: messagebox.showerror("DnsProbe", m))

    # ----------------------------------------------------------- preencher
    def _preencher_registros(self, dominio):
        self.tree_dns.delete(*self.tree_dns.get_children())
        colunas = ("tipo", "valor", "pais", "cidade", "isp")
        # >>> v6.4: itera ORDEM (inclui SRV_SERVICOS depois do SRV)
        for t in ORDEM:
            rotulo = "SRV-SVC" if t == SRV_SERVICOS_KEY else t
            for v in self.registros_cache.get(t, []):
                pais = cidade = isp = ""
                flag = None
                if not v.startswith("("):
                    ips = self.registros_detalhe.get((t, v), [])
                    if ips and ips[0] in self.geo_cache:
                        cod, pais, cidade, isp = self.geo_cache[ips[0]]
                        if cod != "?":
                            flag = self._flag(cod)
                self._inserir_linha(self.tree_dns, colunas,
                                    (rotulo, v, pais, cidade, isp), flag=flag)
        self._set_status(f"Registros de {dominio} atualizados.")
        # Força recalcular o layout do mapa com os novos registros
        self.mapa_nos_data = []
        self.desenhar_mapa()

    def _preencher_subdominios(self):
        """Renderização FINAL: completa país, bandeiras, reverse e o mapa."""
        self.tree_sub.delete(*self.tree_sub.get_children())
        paises_vistos = []
        colunas = ("sub", "ip", "pais", "reverso")
        for sub, ips, pais, reversos in self.subdominios_cache:
            primeiro_ip = ips.split(",")[0].strip()
            flag = None
            if primeiro_ip != "-":
                cod, _, _, _ = self.geo_cache.get(primeiro_ip, ("?", "", "", ""))
                if cod != "?":
                    flag = self._flag(cod)
                    if cod not in paises_vistos:
                        paises_vistos.append(cod)
            self._inserir_linha(self.tree_sub, colunas,
                                (sub, ips, pais, reversos), flag=flag)

        self._preencher_painel_paises(paises_vistos)
        # Força recalcular o layout do mapa
        self.mapa_nos_data = []
        self.desenhar_mapa()

    def _preencher_painel_paises(self, codigos):
        """Mostra uma bandeira por país encontrado, com o código ISO embaixo."""
        for widget in self.painel_pais.winfo_children():
            widget.destroy()
        if not codigos:
            ttk.Label(self.painel_pais,
                      text="Nenhum país identificado.").pack(anchor="w")
            return
        linha = ttk.Frame(self.painel_pais)
        linha.pack(anchor="w")
        for cod in codigos:
            flag = self._flag(cod)
            if not flag:
                continue
            quadro = ttk.Frame(linha)
            quadro.pack(side="left", padx=6)
            ttk.Label(quadro, image=flag).pack()
            ttk.Label(quadro, text=cod, font=("TkDefaultFont", 8)).pack()

    # ------------------------------------------------------------ mapa
    def _layout_mapa(self):
        """Calcula os nós do mapa em coordenadas do mundo (WORLD_W x WORLD_H)."""
        cx, cy = WORLD_W / 2, WORLD_H / 2
        dominio = self.ent_dominio.get().strip() or "domínio"
        nos = [{"x": cx, "y": cy, "w": 170, "h": 60,
                "texto": dominio, "cor": "#dce6f1", "borda": "#2f6f9f",
                "fonte": ("TkDefaultFont", 12, "bold")}]

        grupos = {"DNS (NS)": [], "Mail (MX)": [], "Web (A/AAAA)": [],
                  "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": []}
        geo_info = {}   # grupo -> lista de (texto, cod_iso)
        for tipo, valores in self.registros_cache.items():
            for v in valores:
                if v.startswith("("):
                    continue
                if tipo == "NS":
                    grupo = "DNS (NS)"
                elif tipo == "MX":
                    grupo = "Mail (MX)"
                elif tipo in ("A", "AAAA"):
                    grupo = "Web (A/AAAA)"
                else:
                    grupo = "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)"
                grupos[grupo].append(v)
                # >>> v6.4: SRV mostra o alvo, não a prioridade
                texto = hostname_principal(tipo, v)
                # Trunca textos longos (TXT etc.) para não estourar a caixa
                if len(texto) > 38:
                    texto = texto[:35] + "..."
                cod = ""
                ips = self.registros_detalhe.get((tipo, v), [])
                if ips and ips[0] in self.geo_cache:
                    cod = self.geo_cache[ips[0]][0]
                geo_info.setdefault(grupo, []).append((texto, cod))

        cores = {"DNS (NS)": "#f2dcdb", "Mail (MX)": "#e2efda",
                 "Web (A/AAAA)": "#fde9d9",
                 "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": "#e6e0f5"}
        pos = {"DNS (NS)": 0, "Mail (MX)": 1, "Web (A/AAAA)": 2,
               "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": 3}

        for grupo, hosts in grupos.items():
            if not hosts:
                continue
            col = pos[grupo]
            itens = geo_info.get(grupo, [])[:10]  # até 10 nós por grupo
            n = len(itens)
            col_x = 160 + col * 245   # 4 colunas ao redor do centro
            # Espaçamento vertical mais generoso e uniforme
            espaco = max(58, (WORLD_H - 100) / max(n + 1, 1))
            for i, (texto, cod) in enumerate(itens):
                y = 50 + espaco * (i + 1)
                if cod:
                    texto += f"\n[{cod}]"
                nos.append({"x": col_x, "y": y, "w": 150, "h": 48,
                            "texto": texto, "cor": cores[grupo],
                            "borda": "#a06050",
                            "fonte": ("TkDefaultFont", 8)})
        return nos

    def desenhar_mapa(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        if not self.mapa_inicializado:
            self.mapa_offset = [cw / 2 - WORLD_W / 2, ch / 2 - WORLD_H / 2]
            self.mapa_inicializado = True

        # Gera layout só se ainda não existir (ou se dados mudaram)
        if not self.mapa_nos_data:
            self.mapa_nos_data = self._layout_mapa()

        ox, oy = self.mapa_offset
        z = self.mapa_zoom
        nos = self.mapa_nos_data
        self.mapa_nos = []

        legenda = {"DNS (NS)": 160, "Mail (MX)": 405, "Web (A/AAAA)": 650,
                   "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": 895}
        for grupo, gx in legenda.items():
            self.canvas.create_text(gx * z + ox, 20 * z + oy, text=grupo,
                                    font=("TkDefaultFont", 9, "bold"),
                                    fill="#666")

        for idx, no in enumerate(nos):
            x = no["x"] * z + ox
            y = no["y"] * z + oy
            w2 = no["w"] * z / 2
            h2 = no["h"] * z / 2

            if idx > 0:
                self.canvas.create_line(WORLD_W / 2 * z + ox, WORLD_H / 2 * z + oy,
                                        x, y, fill="#888", dash=(4, 2))

            selecionado = (idx == self.mapa_selecionado)
            contorno = "#ff6600" if selecionado else no["borda"]
            largura = 3 if selecionado else 1
            self.canvas.create_rectangle(x - w2, y - h2, x + w2, y + h2,
                                         fill=no["cor"], outline=contorno,
                                         width=largura)
            self.canvas.create_text(x, y, text=no["texto"],
                                    font=no["fonte"], width=no["w"] * 1.4)

            self.mapa_nos.append((x - w2, y - h2, x + w2, y + h2, no["texto"]))

        if not any(self.registros_cache.values()):
            self.canvas.create_text(cw // 2, ch // 2 + 80,
                                    text="Execute 'Enumerar tudo' para popular o mapa.",
                                    fill="#777")

    # ------------------------------------------- interação com o mouse (mapa)
    def _no_sob_ponto(self, x, y):
        """Retorna o índice do nó que contém o ponto (x, y) ou None."""
        for i in range(len(self.mapa_nos) - 1, -1, -1):
            x1, y1, x2, y2, _ = self.mapa_nos[i]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def mapa_press(self, event):
        self.mapa_arrastando = True
        self.mapa_press_xy = (event.x, event.y)
        self.mapa_press_ini = (event.x, event.y)
        # Verifica se clicou em um nó (para arrastar o nó) ou no fundo (pan)
        i = self._no_sob_ponto(event.x, event.y)
        self.mapa_dragging_node = i
        if i is not None:
            self.mapa_selecionado = i
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="fleur")

    def mapa_drag(self, event):
        if not self.mapa_arrastando:
            return
        x0, y0 = self.mapa_press_xy
        dx = event.x - x0
        dy = event.y - y0
        if abs(dx) + abs(dy) < 2:
            return

        if self.mapa_dragging_node is not None:
            # Arrasta o nó individual (converte delta de tela → coords do mundo)
            z = self.mapa_zoom or 1.0
            no = self.mapa_nos_data[self.mapa_dragging_node]
            no["x"] += dx / z
            no["y"] += dy / z
            # Limita dentro da área do mundo
            no["x"] = max(40, min(WORLD_W - 40, no["x"]))
            no["y"] = max(40, min(WORLD_H - 40, no["y"]))
        else:
            # Pan do mapa inteiro
            self.mapa_offset[0] += dx
            self.mapa_offset[1] += dy

        self.mapa_press_xy = (event.x, event.y)
        self.desenhar_mapa()

    def mapa_release(self, event):
        self.canvas.config(cursor="")
        self.mapa_arrastando = False
        self.mapa_dragging_node = None
        x0, y0 = self.mapa_press_ini   # posição inicial do clique
        if abs(event.x - x0) < 4 and abs(event.y - y0) < 4:
            i = self._no_sob_ponto(event.x, event.y)
            self.mapa_selecionado = i
            self.desenhar_mapa()

    def mapa_double(self, event):
        """Clique duplo: copia o texto do nó."""
        i = self._no_sob_ponto(event.x, event.y)
        if i is not None:
            self._copiar(self.mapa_nos[i][4])

    def mapa_menu(self, event):
        """Menu de botão direito no mapa."""
        i = self._no_sob_ponto(event.x, event.y)
        menu = tk.Menu(self.root, tearoff=0)
        if i is not None:
            texto = self.mapa_nos[i][4].replace("\n", " ")
            menu.add_command(label=f"Copiar: {texto[:45]}",
                             command=lambda t=texto: self._copiar(t))
            menu.add_separator()
        menu.add_command(label="Copiar todos os hosts", command=self._copiar_hosts)
        menu.add_command(label="Copiar IP, países, cidades e ISP", command=self._copiar_ips_paises)
        menu.add_separator()
        menu.add_command(label="Centralizar mapa", command=self._centralizar_mapa)
        menu.add_command(label="Resetar posições dos nós", command=self._reset_layout_mapa)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _reset_layout_mapa(self):
        """Volta os nós para o layout automático inicial."""
        self.mapa_nos_data = []
        self.mapa_selecionado = None
        self.desenhar_mapa()
        self._set_status("Layout do mapa resetado.")

    def mapa_zoom_evt(self, event):
        if event.num == 4:
            fator = 1.1
        elif event.num == 5:
            fator = 0.9
        else:
            fator = 1.1 if event.delta > 0 else 0.9
        self._aplicar_zoom(fator, event.x, event.y)

    def _aplicar_zoom(self, fator, px, py):
        """Aplica zoom mantendo o ponto sob o cursor fixo."""
        novo = max(0.4, min(3.0, self.mapa_zoom * fator))
        if novo == self.mapa_zoom:
            return
        wx = (px - self.mapa_offset[0]) / self.mapa_zoom
        wy = (py - self.mapa_offset[1]) / self.mapa_zoom
        self.mapa_zoom = novo
        self.mapa_offset[0] = px - wx * novo
        self.mapa_offset[1] = py - wy * novo
        self.desenhar_mapa()

    def _centralizar_mapa(self):
        self.mapa_zoom = 1.0
        self.mapa_selecionado = None
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        self.mapa_offset = [cw / 2 - WORLD_W / 2, ch / 2 - WORLD_H / 2]
        self.desenhar_mapa()

    def _hosts_do_mapa(self):
        """Junta hosts dos registros + subdomínios descobertos (únicos)."""
        hosts = []
        for tipo, valores in self.registros_cache.items():
            for v in valores:
                if v.startswith("("):
                    continue
                # >>> v6.4: SRV/SRV-SVC/MX mostram o alvo, não números
                hosts.append(hostname_principal(tipo, v))
        for sub, _, _, _ in self.subdominios_cache:
            hosts.append(sub)
        vistos = set()
        unicos = []
        for h in hosts:
            if h not in vistos:
                vistos.add(h)
                unicos.append(h)
        return unicos

    def _copiar_hosts(self):
        hosts = self._hosts_do_mapa()
        if hosts:
            self._copiar("\n".join(hosts))

    def _copiar_ips_paises(self):
        linhas = []
        for sub, ips, _, _ in self.subdominios_cache:
            if ips == "-":
                continue
            for ip in ips.split(", "):
                info = self.geo_cache.get(ip)
                if info:
                    cod, pais, cidade, isp = info
                    linhas.append(f"{ip}\t{pais} ({cod})\t{cidade}\t{isp}")
        if linhas:
            self._copiar("\n".join(linhas))

    # ------------------------------------------- mapa interativo para o HTML
    def _mapa_html(self, dominio):
        """Mapa da infraestrutura em HTML/JS — nós arrastáveis, pan e zoom."""
        import json as _json

        WORLD_W, WORLD_H = 1100, 620
        cx, cy = WORLD_W / 2, WORLD_H / 2

        nos = [{"x": cx, "y": cy, "w": 170, "h": 60,
                "texto": dominio or "domínio", "cor": "#dce6f1",
                "borda": "#2f6f9f", "centro": True}]

        grupos = {"DNS (NS)": [], "Mail (MX)": [], "Web (A/AAAA)": [],
                  "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": []}
        geo_info = {}
        for tipo, valores in self.registros_cache.items():
            for v in valores:
                if v.startswith("("):
                    continue
                grupo = ("DNS (NS)" if tipo == "NS" else
                         "Mail (MX)" if tipo == "MX" else
                         "Web (A/AAAA)" if tipo in ("A", "AAAA") else
                         "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)")
                grupos[grupo].append(v)
                # >>> v6.4: SRV mostra o alvo, não a prioridade
                texto = hostname_principal(tipo, v)
                cod = ""
                ips = self.registros_detalhe.get((tipo, v), [])
                if ips and ips[0] in self.geo_cache:
                    cod = self.geo_cache[ips[0]][0]
                geo_info.setdefault(grupo, []).append((texto, cod))

        cores = {"DNS (NS)": "#f2dcdb", "Mail (MX)": "#e2efda",
                 "Web (A/AAAA)": "#fde9d9",
                 "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": "#e6e0f5"}
        pos = {"DNS (NS)": 0, "Mail (MX)": 1, "Web (A/AAAA)": 2,
               "Outros (CNAME/SOA/SRV/HINFO/TXT/CAA)": 3}

        for grupo, hosts in grupos.items():
            if not hosts:
                continue
            col = pos[grupo]
            n = len(hosts)
            col_x = 160 + col * 245
            for i, (texto, cod) in enumerate(geo_info.get(grupo, [])[:8]):
                y = 60 + (WORLD_H - 120) * (i + 1) / (n + 1)
                if cod:
                    texto += f" [{cod}]"
                nos.append({"x": col_x, "y": y, "w": 150, "h": 50,
                            "texto": texto, "cor": cores[grupo],
                            "borda": "#a06050", "centro": False})

        dados_nos = _json.dumps(nos, ensure_ascii=False).replace("</", "<\\/")
        hosts = self._hosts_do_mapa()
        dados_hosts = _json.dumps(hosts, ensure_ascii=False).replace("</", "<\\/")

        geo_linhas = []
        for sub, ips, _p, _r in self.subdominios_cache:
            if ips == "-":
                continue
            for ip in ips.split(", "):
                info = self.geo_cache.get(ip)
                if info:
                    cod, pais, cidade, isp = info
                    geo_linhas.append(f"{ip}\t{pais} ({cod})\t{cidade}\t{isp}")
        dados_geo = _json.dumps(geo_linhas, ensure_ascii=False).replace("</", "<\\/")

        return f"""
<div id="mapa">
  <svg id="svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WORLD_W} {WORLD_H}"
       width="100%" height="560" style="background:#fafbfc;border:1px solid #d0d7de;border-radius:8px;cursor:grab">
    <defs>
      <marker id="seta" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
        <path d="M0,0 L8,4 L0,8 z" fill="#888"/>
      </marker>
    </defs>
    <g id="mundo" transform="translate(0,0) scale(1)">
      <g id="linhas"></g>
      <g id="nos"></g>
    </g>
    <text x="12" y="22" font-family="sans-serif" font-size="13" font-weight="bold" fill="#57606a">
      Mapa da infraestrutura — {esc(dominio)} — {datetime.now():%d/%m/%Y %H:%M}
    </text>
  </svg>
  <div style="font-family:sans-serif;font-size:12px;color:#57606a;margin-top:6px">
    <b>Arrastar nó:</b> reposiciona | <b>Arrastar fundo:</b> pan | <b>Scroll:</b> zoom |
    <b>2x clique:</b> copiar nó | <b>Botão direito:</b> copiar hosts.
  </div>
</div>
<script>
(function() {{
  var NOS = {dados_nos};
  var HOSTS = {dados_hosts};
  var GEO = {dados_geo};
  var SVG = document.getElementById('svg');
  var MUNDO = document.getElementById('mundo');
  var gLinhas = document.getElementById('linhas');
  var gNos = document.getElementById('nos');
  var estado = {{z: 1, x: 0, y: 0}};
  var dragging = null, pan = null;

  function aplica() {{
    MUNDO.setAttribute('transform', 'translate(' + estado.x + ',' + estado.y + ') scale(' + estado.z + ')');
  }}

  // desenha linhas do centro até cada nó
  NOS.forEach(function(n, i) {{
    if (i === 0) return;
    var l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    l.setAttribute('x1', NOS[0].x); l.setAttribute('y1', NOS[0].y);
    l.setAttribute('x2', n.x);     l.setAttribute('y2', n.y);
    l.setAttribute('stroke', '#888'); l.setAttribute('stroke-dasharray', '4,3');
    gLinhas.appendChild(l);
  }});

  // desenha os nós
  NOS.forEach(function(n, i) {{
    var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'no');
    g.setAttribute('data-i', i);
    g.style.cursor = 'pointer';

    var r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    r.setAttribute('x', n.x - n.w / 2); r.setAttribute('y', n.y - n.h / 2);
    r.setAttribute('width', n.w); r.setAttribute('height', n.h);
    r.setAttribute('rx', 8); r.setAttribute('fill', n.cor);
    r.setAttribute('stroke', n.borda); r.setAttribute('stroke-width', 1);
    g.appendChild(r);

    var txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', n.x); txt.setAttribute('y', n.y);
    txt.setAttribute('text-anchor', 'middle'); txt.setAttribute('dominant-baseline', 'middle');
    txt.setAttribute('font-family', 'sans-serif');
    txt.setAttribute('font-size', n.centro ? 15 : 11);
    txt.setAttribute('font-weight', n.centro ? 'bold' : 'normal');
    txt.setAttribute('fill', '#24292f');
    txt.textContent = n.texto;
    g.appendChild(txt);
    gNos.appendChild(g);
  }});

  // ---- arrastar nó ----
  gNos.addEventListener('mousedown', function(e) {{
    var alvo = e.target.closest('.no');
    if (!alvo) return;
    e.preventDefault(); e.stopPropagation();
    var i = parseInt(alvo.getAttribute('data-i'), 10);
    dragging = {{i: i, el: alvo}};
    alvo.style.cursor = 'grabbing';
    SVG.style.cursor = 'grabbing';
  }});

  SVG.addEventListener('mousemove', function(e) {{
    var rect = SVG.getBoundingClientRect();
    var px = (e.clientX - rect.left - estado.x) / estado.z;
    var py = (e.clientY - rect.top - estado.y) / estado.z;
    if (dragging) {{
      var n = NOS[dragging.i];
      n.x = Math.max(30, Math.min(1070, px));
      n.y = Math.max(30, Math.min(590, py));
      var g = dragging.el;
      g.querySelector('rect').setAttribute('x', n.x - n.w / 2);
      g.querySelector('rect').setAttribute('y', n.y - n.h / 2);
      g.querySelector('text').setAttribute('x', n.x);
      g.querySelector('text').setAttribute('y', n.y);
      var l = gLinhas.children[dragging.i - 1];
      if (l) {{ l.setAttribute('x2', n.x); l.setAttribute('y2', n.y); }}
    }}
  }});

  window.addEventListener('mouseup', function() {{
    if (dragging) {{ dragging.el.style.cursor = 'pointer'; }}
    dragging = null; pan = null;
    SVG.style.cursor = 'grab';
  }});

  // ---- pan no fundo ----
  SVG.addEventListener('mousedown', function(e) {{
    if (e.target.closest('.no')) return;
    pan = {{x: e.clientX, y: e.clientY, ox: estado.x, oy: estado.y}};
    SVG.style.cursor = 'grabbing';
  }});
  SVG.addEventListener('mousemove', function(e) {{
    if (!pan) return;
    estado.x = pan.ox + (e.clientX - pan.x);
    estado.y = pan.oy + (e.clientY - pan.y);
    aplica();
  }});

  // ---- zoom no scroll (centrado no cursor) ----
  SVG.addEventListener('wheel', function(e) {{
    e.preventDefault();
    var rect = SVG.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    var fator = e.deltaY < 0 ? 1.1 : 0.9;
    var novo = Math.max(0.4, Math.min(3, estado.z * fator));
    estado.x = mx - (mx - estado.x) * (novo / estado.z);
    estado.y = my - (my - estado.y) * (novo / estado.z);
    estado.z = novo;
    aplica();
  }});

  // ---- duplo clique: copia o texto do nó ----
  gNos.addEventListener('dblclick', function(e) {{
    var alvo = e.target.closest('.no');
    if (!alvo) return;
    var i = parseInt(alvo.getAttribute('data-i'), 10);
    copiarTexto(NOS[i].texto);
  }});

  // ---- botão direito: copiar hosts / geo ----
  SVG.addEventListener('contextmenu', function(e) {{
    e.preventDefault();
    var menu = document.createElement('div');
    menu.style.cssText = 'position:fixed;left:' + e.clientX + 'px;top:' + e.clientY +
      'px;background:#fff;border:1px solid #d0d7de;border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,.15);' +
      'font-family:sans-serif;font-size:13px;z-index:9999;min-width:220px;';
    var itens = [
      ['Copiar todos os hosts', function() {{ copiarTexto(HOSTS.join('\\n')); }}],
      ['Copiar IP / país / cidade / ISP', function() {{ copiarTexto(GEO.join('\\n')); }}]
    ];
    itens.forEach(function(p) {{
      var d = document.createElement('div');
      d.textContent = p[0];
      d.style.cssText = 'padding:7px 12px;cursor:pointer;';
      d.onmouseenter = function() {{ d.style.background = '#f0f3f6'; }};
      d.onmouseleave = function() {{ d.style.background = '#fff'; }};
      d.onclick = function() {{ p[1](); document.body.removeChild(menu); }};
      menu.appendChild(d);
    }});
    document.body.appendChild(menu);
    setTimeout(function() {{
      document.addEventListener('click', function f() {{
        if (menu.parentNode) document.body.removeChild(menu);
        document.removeEventListener('click', f);
      }});
    }}, 50);
  }});

  function copiarTexto(txt) {{
    var ta = document.createElement('textarea');
    ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try {{ document.execCommand('copy'); }} catch (err) {{}}
    document.body.removeChild(ta);
  }}
}})();
</script>"""        

    # ----------------------------------------------------------- relatórios
    def _html_completo(self, dominio):
        """Monta o relatório HTML completo (tabelas + mapa interativo)."""
        h = []
        h.append(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DnsProbe v6.4 — {esc(dominio)}</title>
<style>
  body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 0; background: #f6f8fa; color: #24292f; }}
  header {{ background: #24292f; color: #fff; padding: 18px 24px; }}
  header h1 {{ margin: 0; font-size: 20px; }}
  header p {{ margin: 4px 0 0; color: #b8c2cc; font-size: 13px; }}
  main {{ padding: 20px 24px; max-width: 1200px; margin: 0 auto; }}
  h2 {{ font-size: 16px; border-bottom: 2px solid #d0d7de; padding-bottom: 6px; margin-top: 28px; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff; font-size: 13px; }}
  th, td {{ border: 1px solid #d0d7de; padding: 6px 9px; text-align: left; vertical-align: top; }}
  th {{ background: #f0f3f6; position: sticky; top: 0; }}
  tr:nth-child(even) {{ background: #fafbfc; }}
  .flag {{ width: 24px; height: 16px; vertical-align: middle; margin-right: 6px; border-radius: 2px; }}
  .neg {{ color: #999; font-style: italic; }}
  code {{ background: #f0f3f6; padding: 1px 5px; border-radius: 4px; font-size: 12px; }}
  footer {{ text-align: center; color: #888; font-size: 12px; padding: 18px; }}
</style>
</head>
<body>
<header>
  <h1>🛰️ DnsProbe v6.4 — Relatório de enumeração DNS</h1>
  <p>Domínio: <b>{esc(dominio)}</b> &nbsp;|&nbsp; Gerado em {datetime.now():%d/%m/%Y às %H:%M:%S}</p>
</header>
<main>""")

        # ---- Tabela de registros DNS ----
        h.append("<h2>Registros DNS</h2>")
        h.append('<table><thead><tr><th>Tipo</th><th>Valor</th>'
                 '<th>País</th><th>Cidade</th><th>ISP / Org</th></tr></thead><tbody>')
        tem_registros = False
        for t in ORDEM:
            rotulo = "SRV-SVC" if t == SRV_SERVICOS_KEY else t
            for v in self.registros_cache.get(t, []):
                tem_registros = True
                pais = cidade = isp = ""
                cod = ""
                if not v.startswith("("):
                    ips = self.registros_detalhe.get((t, v), [])
                    if ips and ips[0] in self.geo_cache:
                        cod, pais, cidade, isp = self.geo_cache[ips[0]]
                h.append(f'<tr><td><b>{esc(rotulo)}</b></td>'
                         f'<td><code>{esc(v)}</code></td>'
                         f'<td>{"🇨🇴" if False else ""}<span class="flag-img">'
                         f'{f"<img class=flag src=https://flagcdn.com/w160/{cod.lower()}.png alt={esc(cod)}>" if cod else ""}'
                         f'{esc(pais)}</span></td>'
                         f'<td>{esc(cidade)}</td><td>{esc(isp)}</td></tr>')
        if not tem_registros:
            h.append('<tr><td colspan="5" class="neg">Nenhum registro consultado ainda.</td></tr>')
        h.append("</tbody></table>")

        # ---- Tabela de subdomínios ----
        h.append("<h2>Subdomínios encontrados (wordlist)</h2>")
        h.append('<table><thead><tr><th>Subdomínio</th><th>IP(s)</th>'
                 '<th>País</th><th>Reverse DNS</th></tr></thead><tbody>')
        if self.subdominios_cache:
            for sub, ips, pais, reversos in self.subdominios_cache:
                cod = ""
                primeiro = ips.split(",")[0].strip()
                if primeiro != "-":
                    cod = self.geo_cache.get(primeiro, ("", "", "", ""))[0]
                h.append(f'<tr><td>{esc(sub)}</td><td><code>{esc(ips)}</code></td>'
                         f'<td>{f"<img class=flag src=https://flagcdn.com/w160/{cod.lower()}.png alt={esc(cod)}> " if cod else ""}'
                         f'{esc(pais)}</td><td>{esc(reversos)}</td></tr>')
        else:
            h.append('<tr><td colspan="4" class="neg">Nenhum subdomínio encontrado '
                     '(ou enumeração ainda não executada).</td></tr>')
        h.append("</tbody></table>")

        # ---- Tabela de geolocalização (IP -> país/cidade/ISP) ----
        h.append("<h2>Geolocalização (IP → País / Cidade / ISP)</h2>")
        h.append('<table><thead><tr><th>IP</th><th>País</th>'
                 '<th>Cidade</th><th>ISP / Org</th></tr></thead><tbody>')
        ips_vistos = set()
        for sub, ips, _p, _r in self.subdominios_cache:
            if ips == "-":
                continue
            for ip in ips.split(", "):
                if ip in ips_vistos:
                    continue
                ips_vistos.add(ip)
                info = self.geo_cache.get(ip)
                if info:
                    cod, pais, cidade, isp = info
                    h.append(f'<tr><td><code>{esc(ip)}</code></td>'
                             f'<td>{f"<img class=flag src=https://flagcdn.com/w160/{cod.lower()}.png alt={esc(cod)}> " if cod else ""}'
                             f'{esc(pais)} ({esc(cod)})</td>'
                             f'<td>{esc(cidade)}</td><td>{esc(isp)}</td></tr>')
        if not ips_vistos:
            h.append('<tr><td colspan="4" class="neg">Sem IPs para geolocalizar.</td></tr>')
        h.append("</tbody></table>")

        # ---- Mapa interativo ----
        h.append("<h2>Mapa da infraestrutura</h2>")
        h.append(self._mapa_html(dominio))

        h.append("""</main>
<footer>Gerado por DnsProbe v6.4 — uso autorizado em avaliações de segurança.</footer>
</body>
</html>""")
        return "\n".join(h)

    def salvar_html(self):
        """Exporta o relatório HTML completo (com mapa interativo)."""
        d = self.dominio_atual()
        if not d:
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório HTML",
            defaultextension=".html",
            initialfile=f"dnsprobe_{d}.html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")])
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(self._html_completo(d))
            self._set_status(f"Relatório HTML salvo: {caminho}")
            messagebox.showinfo("DnsProbe", f"Relatório HTML salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("DnsProbe", f"Erro ao salvar HTML: {e}")

    def salvar_txt(self):
        """Exporta o relatório em texto puro (TXT)."""
        d = self.dominio_atual()
        if not d:
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório TXT",
            defaultextension=".txt",
            initialfile=f"dnsprobe_{d}.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not caminho:
            return
        try:
            linhas = []
            linhas.append("=" * 72)
            linhas.append(f"DnsProbe v6.4 - Relatório de enumeração DNS")
            linhas.append(f"Domínio: {d}")
            linhas.append(f"Gerado em: {datetime.now():%d/%m/%Y %H:%M:%S}")
            linhas.append("=" * 72)

            linhas.append("\n[REGISTROS DNS]")
            linhas.append("-" * 72)
            for t in ORDEM:
                rotulo = "SRV-SVC" if t == SRV_SERVICOS_KEY else t
                for v in self.registros_cache.get(t, []):
                    pais = cidade = isp = ""
                    if not v.startswith("("):
                        ips = self.registros_detalhe.get((t, v), [])
                        if ips and ips[0] in self.geo_cache:
                            _c, pais, cidade, isp = self.geo_cache[ips[0]]
                    linhas.append(f"[{rotulo}] {v}")
                    if pais:
                        linhas.append(f"          País: {pais} | Cidade: {cidade} | ISP: {isp}")

            linhas.append("\n[SUBDOMÍNIOS ENCONTRADOS]")
            linhas.append("-" * 72)
            if self.subdominios_cache:
                for sub, ips, pais, reversos in self.subdominios_cache:
                    linhas.append(f"{sub}")
                    linhas.append(f"  IPs: {ips}")
                    linhas.append(f"  País: {pais}")
                    linhas.append(f"  Reverse: {reversos}")
            else:
                linhas.append("Nenhum subdomínio encontrado.")

            linhas.append("\n[GEOLOCALIZAÇÃO]")
            linhas.append("-" * 72)
            ips_vistos = set()
            for sub, ips, _p, _r in self.subdominios_cache:
                if ips == "-":
                    continue
                for ip in ips.split(", "):
                    if ip in ips_vistos:
                        continue
                    ips_vistos.add(ip)
                    info = self.geo_cache.get(ip)
                    if info:
                        cod, pais, cidade, isp = info
                        linhas.append(f"{ip}\t{pais} ({cod})\t{cidade}\t{isp}")
            if not ips_vistos:
                linhas.append("Sem IPs para geolocalizar.")

            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
            self._set_status(f"Relatório TXT salvo: {caminho}")
            messagebox.showinfo("DnsProbe", f"Relatório TXT salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("DnsProbe", f"Erro ao salvar TXT: {e}")


def main():
    root = tk.Tk()
    DnsProbeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
