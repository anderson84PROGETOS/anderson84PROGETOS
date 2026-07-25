#!/usr/bin/env python3
"""
DNS Enumerator Pro - Graphical Edition v2.5
Barra de progresso 0-100% verde e determinística.
Resultados em TEMPO REAL - subdomínios aparecem nas DUAS abas.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import time
import subprocess
import platform
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_address, ip_network

# ─── Dependências DNS ────────────────────────────────────────────────────────
try:
    import dns.resolver
    import dns.query
    import dns.zone   
    import dns.rdatatype    
    import dns.reversename
    from dns.exception import DNSException
    DNSPYTHON_AVAILABLE = True
except ImportError:
    DNSPYTHON_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    C, BG, S = Fore, Back, Style
except ImportError:
    class Dummy:
        def __getattr__(self, name): return ""
    C = BG = S = Dummy()


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES GLOBAIS
# ══════════════════════════════════════════════════════════════════════════════

CDN_RANGES = {
    "Cloudflare": [
        "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
        "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
        "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
        "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
        "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
    ],
    "CloudFront (AWS)": [
        "13.32.0.0/15", "13.35.0.0/16", "13.224.0.0/14",
        "52.46.0.0/18", "52.84.0.0/15", "54.182.0.0/16",
        "54.192.0.0/16", "54.230.0.0/16", "54.239.128.0/18",
        "99.84.0.0/16", "205.251.192.0/19",
    ],
    "Fastly": ["23.235.32.0/20", "104.156.80.0/20", "151.101.0.0/16", "199.27.72.0/21"],
    "Akamai": [
        "23.32.0.0/11", "23.64.0.0/14", "23.72.0.0/13", "23.80.0.0/12",
        "23.208.0.0/12", "23.216.0.0/13", "2.16.0.0/13", "2.20.0.0/14",
        "2.22.0.0/15", "72.246.0.0/16", "92.122.0.0/15", "95.100.0.0/15",
        "173.223.0.0/16", "184.51.0.0/16", "184.85.0.0/16",
    ],
    "Google Cloud/CDN": [
        "8.34.208.0/20", "8.35.192.0/21", "23.236.48.0/20", "23.251.128.0/19",
        "34.64.0.0/10", "34.128.0.0/10", "35.184.0.0/14", "35.188.0.0/16",
        "35.190.0.0/17", "35.196.0.0/15", "35.203.0.0/16", "35.207.0.0/17",
        "35.210.0.0/16", "35.220.0.0/15", "35.222.0.0/15", "35.235.0.0/16",
        "35.236.0.0/14", "35.240.0.0/15", "35.242.0.0/15", "35.244.0.0/15",
        "35.246.0.0/16", "35.247.0.0/16", "104.154.0.0/15", "104.196.0.0/14",
        "104.197.0.0/16", "104.198.0.0/15", "107.167.160.0/19", "107.178.192.0/18",
        "130.211.0.0/16", "146.148.0.0/17", "162.222.176.0/21", "172.217.0.0/16",
        "172.253.0.0/16", "173.194.0.0/16", "173.255.112.0/20", "192.158.28.0/22",
        "199.192.112.0/22", "199.223.232.0/21", "199.223.236.0/23",
        "209.85.128.0/17", "216.58.192.0/19", "216.239.32.0/19",
    ],
}

COMMON_SRV_SERVICES = [
    "_sip._tcp", "_sip._udp", "_sips._tcp", "_h323cs._tcp", "_h323ls._udp",
    "_sip._tls", "_jabber._tcp", "_xmpp._tcp", "_ldap._tcp", "_kerberos._tcp",
    "_kerberos._udp", "_imap._tcp", "_pop3._tcp", "_smtp._tcp",
]

COMMON_SUBDOMAINS = [
    "www", "mail", "smtp", "pop", "imap", "admin", "blog", "ftp", "ssh",
    "webmail", "cpanel", "whm", "ns1", "ns2", "ns3", "mx", "mail1", "mail2",
    "vpn", "remote", "api", "dev", "test", "staging", "app", "portal", "secure",
    "login", "register", "forum", "support", "help", "status", "git", "jenkins",
    "jira", "confluence", "wiki", "docs", "cdn", "static", "assets", "img",
    "images", "css", "js", "download", "uploads", "files", "backup", "db",
    "database", "mysql", "redis", "rabbitmq", "kafka", "zookeeper", "monitor",
    "grafana", "prometheus", "kibana", "elastic", "swagger", "redoc", "graphql",
    "rest", "soap", "xmlrpc", "owa", "exchange", "autodiscover", "lync", "skype",
    "radius", "tacacs", "ldap", "ad", "dc1", "dc2", "dns", "dns1", "dns2",
    "ntp", "time", "syslog", "proxy", "squid", "firewall", "ids", "ips", "waf",
    "phpmyadmin", "phpmyadmin1", "phpmyadmin2", "pma", "adminer", "webmin",
    "usermin", "router", "switch", "ap", "wifi", "guest", "intranet", "extranet",
    "partner", "vendor", "s3", "bucket", "storage", "cloud", "direct", "m",
    "mobile", "mobi", "wap", "newsletter", "mailing", "lists", "bounce",
    "tracking", "analytics", "stats", "metrics", "bkp",
]


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

class DNSError(Exception):
    pass


def resolve_with_fallback(domain, rtype, nameserver=None, timeout=5, lifetime=10):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = lifetime
    if nameserver:
        resolver.nameservers = [nameserver]
    try:
        resposta = resolver.resolve(domain, rtype, raise_on_no_answer=False)
        return list(resposta.rrset) if resposta.rrset else []
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout) as e:
        raise DNSError(str(e))


def resolve_ip(hostname, rtype="A", timeout=5):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout * 2
        resp = resolver.resolve(hostname, rtype)
        return resp[0].address if resp.rrset else None
    except Exception:
        return None


def detect_cdn(ip_str):
    try:
        ip = ip_address(ip_str)
        for provider, ranges in CDN_RANGES.items():
            for cidr in ranges:
                if ip in ip_network(cidr, strict=False):
                    return provider
    except ValueError:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES DE ENUMERAÇÃO — COM CALLBACK DE RESULTADO EM TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def enum_a(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "A", nameserver)
        for rr in records:
            ip = rr.address
            cdn = detect_cdn(ip)
            line = f"  A       {ip:20s}"
            tag = "white"
            if cdn:
                line += f"  [CDN: {cdn}]"
                tag = "cdn"
            results.append(line)
            if result_callback:
                result_callback(line, tag)
        random_sub = f"xkcd{int(time.time())%10000}.{domain}"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 5
            resp = resolver.resolve(random_sub, "A")
            if resp.rrset:
                wc_line = "  ⚠  WILDCARD DETECTED! Domínio responde para subdomínios aleatórios."
                results.insert(0, wc_line)
                if result_callback:
                    result_callback(wc_line, "orange")
        except Exception:
            pass
    except Exception:
        pass
    return results


def enum_aaaa(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "AAAA", nameserver)
        for rr in records:
            line = f"  AAAA    {rr.address}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_ns(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "NS", nameserver)
        for rr in records:
            ns_host = rr.target.to_text().rstrip(".")
            ns_ip = resolve_ip(ns_host) or resolve_ip(ns_host, "AAAA") or "?"
            line = f"  NS       {ns_host:35s}  →  {ns_ip}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_mx(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "MX", nameserver)
        for rr in records:
            pref = rr.preference
            mx_host = rr.exchange.to_text().rstrip(".")
            mx_ip = resolve_ip(mx_host) or resolve_ip(mx_host, "AAAA") or "?"
            line = f"  MX       {mx_host:35s}  ({pref})  →  {mx_ip}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_txt(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "TXT", nameserver)
        for rr in records:
            txt_data = " ".join(s.decode() if isinstance(s, bytes) else s for s in rr.strings)
            txt_short = txt_data[:200] + "..." if len(txt_data) > 200 else txt_data
            if txt_data.startswith("v=spf1"):
                line = f"  TXT      [SPF] {txt_short}"
                tag = "spf"
            elif txt_data.startswith("v=DMARC1"):
                line = f"  TXT      [DMARC] {txt_short}"
                tag = "spf"
            else:
                line = f"  TXT      {txt_short}"
                tag = "white"
            results.append(line)
            if result_callback:
                result_callback(line, tag)
    except Exception:
        pass
    return results


def enum_soa(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "SOA", nameserver)
        for rr in records:
            lines = [
                f"  SOA",
                f"       MNAME:    {rr.mname}",
                f"       RNAME:    {rr.rname}",
                f"       SERIAL:   {rr.serial}",
                f"       REFRESH:  {rr.refresh}s",
                f"       RETRY:    {rr.retry}s",
                f"       EXPIRE:   {rr.expire}s",
                f"       MINIMUM:  {rr.minimum}s",
            ]
            results.extend(lines)
            if result_callback:
                for l in lines:
                    result_callback(l, "white")
    except Exception:
        pass
    return results


def enum_cname(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "CNAME", nameserver)
        for rr in records:
            line = f"  CNAME    → {rr.target.to_text().rstrip('.')}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_ptr(domain, nameserver=None, result_callback=None):
    results = []
    try:
        a_records = resolve_with_fallback(domain, "A", nameserver)
        for rr in a_records:
            try:
                rev_name = dns.reversename.from_address(rr.address)
                rev_records = resolve_with_fallback(rev_name, "PTR", nameserver)
                for ptr_rr in rev_records:
                    line = f"  PTR      {rr.address:20s}  ←  {ptr_rr.target.to_text().rstrip('.')}"
                    results.append(line)
                    if result_callback:
                        result_callback(line, "white")
            except Exception:
                line = f"  PTR      {rr.address:20s}  ←  (sem PTR)"
                results.append(line)
                if result_callback:
                    result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_hinfo(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "HINFO", nameserver)
        for rr in records:
            line = f"  HINFO    CPU: {rr.cpu}  OS: {rr.os}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_srv(domain, nameserver=None, result_callback=None):
    results = []
    for service in COMMON_SRV_SERVICES:
        srv_domain = f"{service}.{domain}"
        try:
            records = resolve_with_fallback(srv_domain, "SRV", nameserver)
            for rr in records:
                target = rr.target.to_text().rstrip(".")
                target_ip = resolve_ip(target) or resolve_ip(target, "AAAA") or "?"
                line = (f"  SRV      {srv_domain:30s}  "
                        f"→ {target} ({target_ip}):{rr.port}  "
                        f"prio={rr.priority} weight={rr.weight}")
                results.append(line)
                if result_callback:
                    result_callback(line, "white")
        except Exception:
            pass
    return results


def enum_ds(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "DS", nameserver)
        for rr in records:
            line = (f"  DS       KeyTag={rr.key_tag} Algorithm={rr.algorithm} "
                    f"DigestType={rr.digest_type} Digest={rr.digest.hex()}")
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_nsec3(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "NSEC3", nameserver)
        for rr in records:
            line = (f"  NSEC3    {rr.next_hashed_owner_name.hex()} "
                    f"Flags={rr.flags} Iterations={rr.iterations}")
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_caa(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "CAA", nameserver)
        for rr in records:
            tag = rr.tag.decode() if isinstance(rr.tag, bytes) else rr.tag
            value = rr.value.decode() if isinstance(rr.value, bytes) else rr.value
            line = f"  CAA      Flags={rr.flags} {tag}={value}"
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


def enum_dnskey(domain, nameserver=None, result_callback=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "DNSKEY", nameserver)
        for rr in records:
            algo_name = dns.dnssec.algorithm_to_text(rr.algorithm)
            line = (f"  DNSKEY   Flags={rr.flags} Protocol={rr.protocol} "
                    f"Algorithm={algo_name} Key={rr.key.hex()[:40]}...")
            results.append(line)
            if result_callback:
                result_callback(line, "white")
    except Exception:
        pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSFERÊNCIA DE ZONA (AXFR) — TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def _axfr_via_inbound_xfr(ns, domain, timeout=10):
    if not hasattr(dns.query, 'inbound_xfr') or not hasattr(dns.query, 'UDPMode'):
        raise AttributeError("inbound_xfr não disponível")
    zone = dns.zone.Zone(domain)
    dns.query.inbound_xfr(
        ns, zone,
        timeout=timeout,
        lifetime=timeout + 10,
        udp_mode=dns.query.UDPMode.NEVER
    )
    return zone


def _axfr_via_from_xfr(ns, domain, timeout=10):
    zone = dns.zone.from_xfr(
        dns.query.xfr(ns, domain, timeout=timeout)
    )
    return zone


def _parse_nslookup_output(stdout, domain):
    results = []
    linhas = stdout.splitlines()
    soa_lines = []
    
    for linha in linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            continue
        if any(linha_strip.startswith(x) for x in [
            "Servidor:", "Address:", "DNS request timed out",
            "***", "não encontrado", "can't find", "Default Server"
        ]):
            continue
        if "Non-authoritative answer" in linha_strip or "Resposta não autoritativa" in linha_strip:
            continue
        
        m = re.match(r'^(\S+)\s+text\s*=\s*"([^"]*)"', linha_strip)
        if m:
            host, text_val = m.groups()
            if text_val.startswith("v=spf1"):
                results.append((f"    {host:40s} TXT      [SPF] {text_val}", "spf"))
            elif text_val.startswith("v=DMARC1"):
                results.append((f"    {host:40s} TXT      [DMARC] {text_val}", "spf"))
            else:
                results.append((f"    {host:40s} TXT      {text_val}", "white"))
            continue
        
        m = re.match(r'^(\S+)\s+HINFO\s+CPU\s*=\s*(.+?)\s+OS\s*=\s*(.+)', linha_strip)
        if m:
            host, cpu, os_val = m.groups()
            results.append((f"    {host:40s} HINFO    CPU: {cpu.strip()}  OS: {os_val.strip()}", "white"))
            continue
        
        m = re.match(r'^(\S+)\s+internet\s+address\s*=\s*(\S+)', linha_strip)
        if m:
            host, ip_val = m.groups()
            cdn = detect_cdn(ip_val)
            line = f"    {host:40s} A        {ip_val:20s}"
            tag = "white"
            if cdn:
                line += f"  [CDN: {cdn}]"
                tag = "cdn"
            results.append((line, tag))
            continue
        
        m = re.match(r'^(\S+)\s+nameserver\s*=\s*(\S+)', linha_strip)
        if m:
            host, ns_val = m.groups()
            results.append((f"    {host:40s} NS       {ns_val}", "white"))
            continue
        
        m = re.match(r'^(\S+)\s+MX\s+preference\s*=\s*(\d+)\s*,\s*mail\s+exchanger\s*=\s*(\S+)', linha_strip)
        if m:
            host, pref, mx_val = m.groups()
            results.append((f"    {host:40s} MX       {mx_val:35s}  ({pref})", "white"))
            continue
        
        m = re.match(r'^\s+primary\s+name\s+server\s*=\s*(\S+)', linha_strip)
        if m:
            soa_lines.append(f"       MNAME:    {m.group(1)}")
            continue
        m = re.match(r'^\s+responsible\s+mail\s+addr\s*=\s*(\S+)', linha_strip)
        if m:
            soa_lines.append(f"       RNAME:    {m.group(1)}")
            continue
        m = re.match(r'^\s+serial\s*=\s*(\d+)', linha_strip)
        if m:
            soa_lines.append(f"       SERIAL:   {m.group(1)}")
            continue
        m = re.match(r'^\s+refresh\s*=\s*(\d+)', linha_strip)
        if m:
            soa_lines.append(f"       REFRESH:  {m.group(1)}s")
            continue
        m = re.match(r'^\s+retry\s*=\s*(\d+)', linha_strip)
        if m:
            soa_lines.append(f"       RETRY:    {m.group(1)}s")
            continue
        m = re.match(r'^\s+expire\s*=\s*(\d+)', linha_strip)
        if m:
            soa_lines.append(f"       EXPIRE:   {m.group(1)}s")
            continue
        m = re.match(r'^\s+default\s+TTL\s*=\s*(\d+)', linha_strip)
        if m:
            soa_lines.append(f"       MINIMUM:  {m.group(1)}s")
            continue
    
    if soa_lines:
        results.append((f"    {domain:40s} SOA", "white"))
        for line in soa_lines:
            results.append((f"  {line}", "white"))
    
    return results


def _axfr_via_subprocess_any(ns, domain, timeout=15):
    results = []
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["nslookup", "-type=any", domain, ns]
    else:
        cmd = ["dig", "ANY", domain, f"@{ns}"]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if system == "windows" else 0
        )
        stdout = proc.stdout or ""
        if not stdout.strip():
            return results
        
        parsed = _parse_nslookup_output(stdout, domain)
        if parsed:
            return parsed
        return results
            
    except Exception:
        return results


def _axfr_via_subprocess_axfr(ns, domain, timeout=15):
    results = []
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["nslookup", "-type=axfr", domain, ns]
    else:
        cmd = ["dig", "AXFR", domain, f"@{ns}"]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if system == "windows" else 0
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + stderr
        
        if not combined.strip():
            return results
        
        linhas = combined.splitlines()
        for l in linhas:
            if l.strip() and not l.startswith(";") and \
               not l.startswith("Servidor:") and \
               not l.startswith("Address:") and \
               not l.startswith("DNS request timed out") and \
               not l.startswith("***") and \
               "não encontrado" not in l.lower() and \
               "can't find" not in l.lower() and \
               "failed" not in l.lower() and \
               "SERVFAIL" not in l and \
               "REFUSED" not in l:
                results.append((l.strip(), "white"))
        
        if results and len(results) > 2:
            return results
        return results
            
    except Exception:
        return results


def enum_axfr(domain, nameserver=None, timeout=10, result_callback=None):
    results = []
    ns_list = []
    
    if nameserver:
        ns_list = [nameserver]
    else:
        try:
            records = resolve_with_fallback(domain, "NS")
            for rr in records:
                ns_list.append(rr.target.to_text().rstrip("."))
        except Exception:
            return results

    if not ns_list:
        return results

    for ns in ns_list:
        line = f"\n  ▶  Tentando AXFR em: {ns} ({domain})\n"
        results.append(line)
        if result_callback:
            result_callback(line, "orange")
        
        encontrados = False
        registros_finais = []
        
        if not encontrados:
            try:
                zone = _axfr_via_inbound_xfr(ns, domain, timeout)
                names = sorted(zone.nodes.keys())
                for nome in names:
                    node = zone[nome]
                    for rdataset in node:
                        tipo = dns.rdatatype.to_text(rdataset.rdtype)
                        for rr in rdataset:
                            host_str = str(nome.relative(zone.origin)) if nome != zone.origin else "@"
                            line = f"    {host_str:40s} {tipo:8s} {rr}"
                            registros_finais.append(line)
                            if result_callback:
                                result_callback(line, "white")
                if registros_finais:
                    encontrados = True
            except Exception:
                pass            
        
        if not encontrados:
            try:
                zone = _axfr_via_from_xfr(ns, domain, timeout)
                names = sorted(zone.nodes.keys())
                for nome in names:
                    node = zone[nome]
                    for rdataset in node:
                        tipo = dns.rdatatype.to_text(rdataset.rdtype)
                        for rr in rdataset:
                            host_str = str(nome.relative(zone.origin)) if nome != zone.origin else "@"
                            line = f"    {host_str:40s} {tipo:8s} {rr}"
                            registros_finais.append(line)
                            if result_callback:
                                result_callback(line, "white")
                if registros_finais:
                    encontrados = True
            except Exception:
                pass
        
        if not encontrados:
            data = _axfr_via_subprocess_axfr(ns, domain, timeout)
            if data:
                for line, tag in data:
                    registros_finais.append(line)
                    if result_callback:
                        result_callback(line, tag)
                encontrados = True
        
        if not encontrados:
            data = _axfr_via_subprocess_any(ns, domain, timeout)
            if data:
                for line, tag in data:
                    registros_finais.append(line)
                    if result_callback:
                        result_callback(line, tag)
                encontrados = True
        
        if encontrados:
            line = f"\n  ▶  Zona completa via {ns}:"
            results.append(line)
            if result_callback:
                result_callback(line, "green")
            sep = f"  {'─'*60}"
            results.append(sep)
            if result_callback:
                result_callback(sep, "white")
            results.extend(registros_finais)
            results.append(f"  {'─'*60}")
            total_line = f"  📊 Total: {len(registros_finais)} registros"
            results.append(total_line)
            if result_callback:
                result_callback(f"  {'─'*60}", "white")
                result_callback(total_line, "green")
        else:
            line = f"  ⚠  AXFR não disponível em {ns}"
            results.append(line)
            if result_callback:
                result_callback(line, "orange")

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  SUBDOMAIN BRUTEFORCE — TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def enum_subdomains(domain, wordlist=None, max_threads=50,
                    progress_callback=None, result_callback=None):
    results = []
    words = wordlist or COMMON_SUBDOMAINS
    total = len(words)
    line = f"  ▶  Bruteforce de subdomínios iniciado ({total} palavras)\n"
    results.append(line)
    if result_callback:
        result_callback(line, "orange")
    
    found_count = [0]
    lock = threading.Lock()
    counter = [0]

    def check_sub(sub):
        subdomain = f"{sub}.{domain}"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 5
            resp = resolver.resolve(subdomain, "A")
            if resp.rrset:
                ip = resp[0].address
                cdn = detect_cdn(ip)
                tag_str = f" [CDN: {cdn}]" if cdn else ""
                with lock:
                    line = f"    ✅ {subdomain:45s} → {ip}{tag_str}"
                    found_count[0] += 1
                    if result_callback:
                        result_callback(line, "green" if not cdn else "cdn")
        except Exception:
            pass
        finally:
            with lock:
                counter[0] += 1
                if progress_callback:
                    progress_callback(counter[0], total, found_count[0])

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        list(executor.map(check_sub, words))

    final_line = f"\n✅ Bruteforce concluído: {found_count[0]} subdomínios encontrados"
    results.append(final_line)
    if result_callback:
        result_callback(final_line, "green")
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  ENUMERAÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def enumerate_domain(domain, nameserver=None, record_types=None,
                     do_axfr=False, do_subdomain=False, wordlist=None,
                     timeout=5,
                     progress_callback=None,
                     result_callback=None,
                     sub_progress_callback=None):    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    for line in [
        f"\n{'═'*70}",
        f"📡  Alvo: {domain}\n",
        f"  Data: {timestamp}\n",
        f"  Nameserver: {nameserver or 'Automático'}\n",
        f"  Timeout: {timeout}s\n",
        f"  AXFR: {'Sim' if do_axfr else 'Não'} | Subdomínios: {'Sim' if do_subdomain else 'Não'}",
        f"{'─'*70}",
    ]:
        if result_callback:
            result_callback(line, "header")

    type_funcs = {
        "A":       ("Registros A (IPv4)", enum_a),
        "AAAA":    ("Registros AAAA (IPv6)", enum_aaaa),
        "NS":      ("Servidores de Nomes (NS)", enum_ns),
        "MX":      ("Servidores de Email (MX)", enum_mx),
        "TXT":     ("Registros TXT (SPF/DKIM/DMARC)", enum_txt),
        "SOA":     ("Início de Autoridade (SOA)", enum_soa),
        "CNAME":   ("Aliases (CNAME)", enum_cname),
        "PTR":     ("Reverse DNS (PTR)", enum_ptr),
        "HINFO":   ("Informações do Host (HINFO)", enum_hinfo),
        "SRV":     ("Registros de Serviço (SRV)", enum_srv),
        "DS":      ("DNSSEC - DS", enum_ds),
        "NSEC3":   ("DNSSEC - NSEC3", enum_nsec3),
        "CAA":     ("Autorização de CA (CAA)", enum_caa),
        "DNSKEY":  ("DNSSEC - DNSKEY", enum_dnskey),
    }

    if not record_types:
        record_types = list(type_funcs.keys())

    total_tasks = len(record_types) + (1 if do_axfr else 0) + (1 if do_subdomain else 0)
    completed_tasks = [0]

    for rtype in record_types:
        if rtype in type_funcs:
            name, func = type_funcs[rtype]
            if result_callback:
                result_callback(f"\n📌  {name}", "blue")
                result_callback(f"  {'─'*60}", "white")
            try:
                func(domain, nameserver, result_callback=result_callback)
            except Exception:
                pass
            completed_tasks[0] += 1
            if progress_callback:
                progress_callback(completed_tasks[0], total_tasks, f"Consultando {rtype}...")

    if do_axfr:
        if result_callback:
            result_callback(f"\n📌  Transferência de Zona (AXFR)", "blue")
            result_callback(f"  {'─'*60}", "white")
        enum_axfr(domain, nameserver, timeout, result_callback=result_callback)
        completed_tasks[0] += 1
        if progress_callback:
            progress_callback(completed_tasks[0], total_tasks, "Transferência de Zona concluída")

    if do_subdomain:
        if result_callback:
            result_callback(f"\n📌  Subdomínios (Bruteforce)", "blue")
            result_callback(f"  {'─'*60}", "white")
        
        def sub_cb(current, total, found):
            if sub_progress_callback:
                sub_progress_callback(current, total, found)
            pct = int(current / total * 100) if total > 0 else 0
            overall_progress = int((completed_tasks[0] / total_tasks) * 100 + (pct / total_tasks))
            overall_progress = min(overall_progress, 99)
            if progress_callback:
                progress_callback(overall_progress, 100, f"Subdomínios: {current}/{total} ({found} encontrados)")

        enum_subdomains(domain, wordlist, progress_callback=sub_cb,
                        result_callback=result_callback)
        completed_tasks[0] += 1
        if progress_callback:
            progress_callback(total_tasks, total_tasks, "Finalizando...")

    if result_callback:
        result_callback(f"\n{'═'*70}", "header")
        result_callback("✅  Enumeração concluída com sucesso!", "green")


# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA - TKINTER
# ══════════════════════════════════════════════════════════════════════════════

class DNSEnumeratorGUI:
    """Interface gráfica completa para enumeração DNS — resultados em tempo real."""

    def __init__(self, root):
        self.root = root
        self.root.title("Transfer Zone DNS Enumerator - Tempo Real")
        self.root.geometry("1200x800")
        self.root.state("zoomed")
        self.root.minsize(900, 650)

        # Tema escuro
        self.bg_color = "#1a1a2e"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#0f3460"
        self.highlight_color = "#16213e"
        self.root.configure(bg=self.bg_color)

        # Estilo
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabelframe", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", background=self.accent_color, foreground="white", font=("Segoe UI", 10))
        self.style.map("TButton", background=[("active", "#1a5276")])
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TRadiobutton", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TEntry", fieldbackground=self.highlight_color, foreground=self.fg_color)
        self.style.configure("TSpinbox", fieldbackground=self.highlight_color, foreground=self.fg_color)
        self.style.configure("green.Horizontal.TProgressbar", background="#50fa7b", troughcolor="#0d0d1a", bordercolor="#0d0d1a", lightcolor="#50fa7b", darkcolor="#2ea85e")

        # Variáveis
        self.domain_var = tk.StringVar()
        self.nameserver_var = tk.StringVar()
        self.timeout_var = tk.IntVar(value=10)
        self.record_vars = {}
        self.do_axfr_var = tk.BooleanVar(value=True)
        self.do_subdomain_var = tk.BooleanVar(value=False)
        self.is_running = False

        # Banner
        self._create_banner()

        # Notebook (abas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Aba principal
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="📋  Enumeração")
        self._create_main_tab()

        # Aba de resultados
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="📄  Resultados")
        self._create_results_tab()

        # Aba de subdomínios
        self.sub_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sub_frame, text="🔍  Subdomínios")
        self._create_subdomain_tab()

        # Status bar
        self._create_status_bar()

        self.log("🟢  Transfer Zone DNS Enumerator - Resultados em Tempo Real\n", "header")

    def _create_banner(self):
        banner_frame = tk.Frame(self.root, bg="#0d0d1a", height=80)
        banner_frame.pack(fill=tk.X, padx=0, pady=0)

        banner_text = """Transfer Zone DNS Enumerator — Tempo Real"""
        lbl = tk.Label(banner_frame, text=banner_text,
                       fg="#00d4aa", bg="#0d0d1a",
                       font=("Consolas", 14, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        subtitle = tk.Label(banner_frame, 
            text="🔎 Resultados em TEMPO REAL • 14 tipos de registro • AXFR • CDN Detection",
            fg="#8888aa", bg="#0d0d1a", font=("Segoe UI", 9))
        subtitle.place(relx=0.5, rely=0.8, anchor="center")

    def _create_main_tab(self):
        main = self.main_frame

        config_frame = ttk.LabelFrame(main, text="🎯  Configurações do Alvo", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="Domínio:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        entry_domain = ttk.Entry(row1, textvariable=self.domain_var, font=("Consolas", 11))
        entry_domain.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        entry_domain.bind("<Return>", lambda e: self._start_enum())

        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="Nameserver:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.nameserver_var, font=("Consolas", 10)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        ttk.Label(row2, text="Timeout:").pack(side=tk.LEFT, padx=(10, 2))
        spin_timeout = ttk.Spinbox(row2, from_=1, to=60, textvariable=self.timeout_var, width=5)
        spin_timeout.pack(side=tk.LEFT)

        types_frame = ttk.LabelFrame(main, text="📌  Tipos de Registro", padding=10)
        types_frame.pack(fill=tk.X, padx=10, pady=5)

        canvas = tk.Canvas(types_frame, bg=self.bg_color, height=120, highlightthickness=0)
        scrollbar = ttk.Scrollbar(types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        record_types_info = {
            "A": "IPv4", "AAAA": "IPv6", "NS": "Nameservers", "MX": "Mail",
            "TXT": "Text/SPF", "SOA": "Authority", "CNAME": "Alias",
            "PTR": "Reverse", "HINFO": "Host Info", "SRV": "Services",
            "DS": "DNSSEC DS", "NSEC3": "DNSSEC NSEC3", "CAA": "CA Auth",
            "DNSKEY": "DNSSEC Key",
        }

        row_num, col_num = 0, 0
        for rtype, desc in record_types_info.items():
            var = tk.BooleanVar(value=True)
            self.record_vars[rtype] = var
            cb = ttk.Checkbutton(scrollable_frame, text=f"{rtype} ({desc})", variable=var)
            cb.grid(row=row_num, column=col_num, sticky="w", padx=10, pady=2)
            col_num += 1
            if col_num >= 3:
                col_num = 0
                row_num += 1

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_row = ttk.Frame(types_frame)
        btn_row.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_row, text="✅ Selecionar Todos", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="❌ Limpar", command=self._deselect_all).pack(side=tk.LEFT, padx=2)

        extra_frame = ttk.LabelFrame(main, text="⚙️  Opções Extras", padding=10)
        extra_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(extra_frame, text="⬇  Tentar AXFR (transferência de zona)",
                         variable=self.do_axfr_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(extra_frame, text="🔍  Bruteforce de Subdomínios",
                         variable=self.do_subdomain_var).pack(side=tk.LEFT, padx=10)

        progress_frame = ttk.LabelFrame(main, text="📊  Progresso", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        bar_row = ttk.Frame(progress_frame)
        bar_row.pack(fill=tk.X)

        self.pct_var = tk.StringVar(value="0%")
        self.pct_label = tk.Label(bar_row, textvariable=self.pct_var,
                                  fg="#50fa7b", bg=self.bg_color,
                                  font=("Consolas", 12, "bold"), width=5)
        self.pct_label.pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(bar_row, mode="determinate",
                                         length=600, maximum=100,
                                         style="green.Horizontal.TProgressbar")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.progress_label = ttk.Label(bar_row, text="")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_run = ttk.Button(action_frame, text="▶  EXECUTAR ENUMERAÇÃO",
                                  command=self._start_enum)
        self.btn_run.pack(side=tk.LEFT, padx=2)
        self.btn_stop = ttk.Button(action_frame, text="⏹  PARAR",
                                   command=self._stop_enum, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="🗑️  Limpar Resultados",
                   command=self._clear_results).pack(side=tk.LEFT, padx=2)

        # ─── AJUDA DO NAMESERVER ──────────────────────────────────────────────
        ns_help_frame = ttk.LabelFrame(main, text="💡  Dica: Nameserver (opcional)", padding=8)
        ns_help_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        help_text = tk.Text(
            ns_help_frame,
            height=50,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#0d0d1a",
            fg="#0be64c",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
        help_text.pack(fill=tk.X, padx=5, pady=5)
        help_text.insert(tk.END, "💡 Para AXFR, deixe em branco — o script descobre os NS automaticamente\n\n")
        help_text.insert(tk.END, "Situação".ljust(40) + "O que colocar\n")
        help_text.insert(tk.END, "─" * 70 + "\n")
        help_text.insert(tk.END, "Consultar direto no DNS da empresa".ljust(40) + "ns1.businesscorp.com.br  ou  37.59.174.225\n\n")
        help_text.insert(tk.END, "Usar Cloudflare".ljust(40) + "1.1.1.1\n\n")
        help_text.insert(tk.END, "Usar Google DNS".ljust(40) + "8.8.8.8\n\n")
        help_text.insert(tk.END, "Usar OpenDNS".ljust(40) + "208.67.222.222\n\n")
        help_text.insert(tk.END, "Testar servidor DNS específico".ljust(40) + "IP ou hostname do servidor\n\n")
        help_text.insert(tk.END, "Testar AXFR (zonetransfer.me)".ljust(40) + "nsztm1.digi.ninja  (81.4.108.41)\n\n")
        help_text.insert(tk.END, "".ljust(40) + "nsztm2.digi.ninja  (5.196.105.10)\n\n")
        help_text.insert(tk.END, "".ljust(40) + "zonetransfer.me")
        help_text.config(state=tk.DISABLED)

    def _create_results_tab(self):
        frame = self.results_frame

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="💾  Salvar como TXT",
                   command=self._save_txt).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾  Salvar como JSON",
                   command=self._save_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋  Copiar Tudo",
                   command=self._copy_results).pack(side=tk.LEFT, padx=2)

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.result_text = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0d0d1a", fg="#d0d0e0",
            insertbackground="white",
            state=tk.NORMAL,
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.result_text.tag_configure("green", foreground="#50fa7b", font=("Consolas", 10, "bold"))
        self.result_text.tag_configure("red", foreground="#ff5555")
        self.result_text.tag_configure("orange", foreground="#f1fa8c")
        self.result_text.tag_configure("blue", foreground="#8be9fd", font=("Consolas", 10, "bold"))
        self.result_text.tag_configure("white", foreground="#f8f8f2")
        self.result_text.tag_configure("header", foreground="#00d4aa", font=("Consolas", 11, "bold"))
        self.result_text.tag_configure("cdn", foreground="#ffb86c")
        self.result_text.tag_configure("spf", foreground="#50fa7b")
        self.result_text.tag_configure("error", foreground="#ff5555")

    def _create_subdomain_tab(self):
        frame = self.sub_frame

        wl_frame = ttk.LabelFrame(frame, text="📖  Wordlist para Bruteforce", padding=5)
        wl_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(wl_frame, text="Arquivo externo (opcional):").pack(side=tk.LEFT)
        self.wordlist_var = tk.StringVar()
        ttk.Entry(wl_frame, textvariable=self.wordlist_var, font=("Consolas", 10)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(wl_frame, text="📂  Abrir", command=self._browse_wordlist).pack(side=tk.LEFT, padx=2)

        sub_text_frame = ttk.Frame(frame)
        sub_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sub_result_text = scrolledtext.ScrolledText(
            sub_text_frame, wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0d0d1a", fg="#d0d0e0",
            insertbackground="white",
            state=tk.NORMAL,
        )
        self.sub_result_text.pack(fill=tk.BOTH, expand=True)

        self.sub_result_text.tag_configure("green", foreground="#50fa7b")
        self.sub_result_text.tag_configure("red", foreground="#ff5555")
        self.sub_result_text.tag_configure("orange", foreground="#f1fa8c")
        self.sub_result_text.tag_configure("cyan", foreground="#8be9fd")

    def _create_status_bar(self):
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W,
                               font=("Segoe UI", 9), background="#0d0d1a")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, msg, tag="white"):
        """Exibe uma mensagem na aba de resultados (thread-safe via root.after)."""
        self.root.after(0, self._do_log, msg, tag)

    def _do_log(self, msg, tag):
        self.result_text.insert(tk.END, msg + "\n", tag)
        self.result_text.see(tk.END)
        self.root.update_idletasks()

    def sub_log(self, msg, tag="white"):
        """Exibe uma mensagem na aba de subdomínios (thread-safe via root.after)."""
        self.root.after(0, self._do_sub_log, msg, tag)

    def _do_sub_log(self, msg, tag):
        self.sub_result_text.insert(tk.END, msg + "\n", tag)
        self.sub_result_text.see(tk.END)
        self.root.update_idletasks()

    def _select_all(self):
        for var in self.record_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.record_vars.values():
            var.set(False)

    def _clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.sub_result_text.delete(1.0, tk.END)
        self._update_progress(0, "0%")

    def _update_progress(self, value, label_text=""):
        if value < 0: value = 0
        if value > 100: value = 100
        self.progress["value"] = value
        self.pct_var.set(f"{int(value)}%")
        if value < 30:
            color = "#50fa7b"
        elif value < 70:
            color = "#2ea85e"
        else:
            color = "#1a8a4a"
        self.pct_label.config(fg=color)
        self.progress_label.config(text=label_text)
        self.root.update_idletasks()

    def _browse_wordlist(self):
        filename = filedialog.askopenfilename(
            title="Selecionar wordlist",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist_var.set(filename)

    def _copy_results(self):
        content = self.result_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("📋 Resultados copiados para a área de transferência!")

    def _save_txt(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar como TXT",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            content = self.result_text.get(1.0, tk.END)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_var.set(f"💾 Salvo em: {filename}")

    def _save_json(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar como JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            content = self.result_text.get(1.0, tk.END)
            data = {
                "timestamp": datetime.now().isoformat(),
                "raw_output": content,
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.status_var.set(f"💾 Salvo em: {filename}")

    def _start_enum(self):
        if self.is_running:
            return

        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showerror("Erro", "Informe um domínio válido.")
            return

        if not DNSPYTHON_AVAILABLE:
            messagebox.showerror("Erro",
                "Biblioteca 'dnspython' não encontrada.\n\n"
                "Instale com: pip install dnspython")
            return

        self.is_running = True
        self.btn_run.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._update_progress(0, "Iniciando...")

        self._clear_results()

        nameserver = self.nameserver_var.get().strip() or None
        timeout = self.timeout_var.get()
        selected_types = [rt for rt, var in self.record_vars.items() if var.get()]
        do_axfr = self.do_axfr_var.get()
        do_sub = self.do_subdomain_var.get()
        wordlist_file = self.wordlist_var.get().strip() or None

        external_words = None
        if wordlist_file and do_sub:
            try:
                with open(wordlist_file, "r") as f:
                    external_words = [line.strip() for line in f if line.strip()]
                self.log(f"📖  Wordlist carregada: {len(external_words)} palavras", "green")
            except FileNotFoundError:
                self.log(f"❌  Wordlist não encontrada: {wordlist_file}", "error")

        self.enum_thread = threading.Thread(
            target=self._run_enum,
            args=(domain, nameserver, selected_types, do_axfr, do_sub, external_words, timeout),
            daemon=True
        )
        self.enum_thread.start()

    def _stop_enum(self):
        self.is_running = False
        self.status_var.set("⏹  Interrompido pelo usuário")
        self._update_progress(0, "Interrompido")
        self._finalize()

    def _run_enum(self, domain, nameserver, selected_types, do_axfr, do_sub, wordlist, timeout):
        try:
            def progress_callback(current, total, msg):
                if not self.is_running:
                    return
                pct = int((current / total) * 100) if total > 0 else 0
                pct = min(pct, 100)
                self.root.after(0, self._update_progress, pct, msg)

            def sub_progress_callback(current, total, found):
                if not self.is_running:
                    return
                pct = int((current / total) * 100) if total > 0 else 0
                msg = f"Subdomínios: {current}/{total} ({found} encontrados) [{pct}%]"
                self.root.after(0, self._do_sub_log, msg, "cyan")

            # ─── CALLBACK PRINCIPAL CORRIGIDO ────────────────────────────────
            def result_callback(text, tag="white"):
                """Exibe NA ABA PRINCIPAL e, se for subdomínio, TAMBÉM na aba de subdomínios."""
                if not self.is_running:
                    return
                # SEMPRE mostra na aba principal "📄 Resultados"
                self.root.after(0, self._do_log, text, tag)
                # Se for um subdomínio encontrado (✅), mostra TAMBÉM na aba "🔍 Subdomínios"
                if "✅" in text and domain in text:
                    self.root.after(0, self._do_sub_log, text, tag)

            enumerate_domain(
                domain=domain,
                nameserver=nameserver,
                record_types=selected_types,
                do_axfr=do_axfr,
                do_subdomain=do_sub,
                wordlist=wordlist,
                timeout=timeout,
                progress_callback=progress_callback,
                result_callback=result_callback,
                sub_progress_callback=sub_progress_callback,
            )

            if not self.is_running:
                return

            self.root.after(0, self._update_progress, 100, "Enumeração concluída!")

        except Exception as e:
            self.root.after(0, self._do_log, f"❌  Erro fatal: {type(e).__name__}: {e}", "error")
        finally:
            self.root.after(0, self._finalize)

    def _finalize(self):
        self.is_running = False
        self.btn_run.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_var.set("✅  Concluído")


# ══════════════════════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app = DNSEnumeratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
