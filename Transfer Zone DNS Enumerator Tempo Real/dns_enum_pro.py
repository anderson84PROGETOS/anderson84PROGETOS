#!/usr/bin/env python3
"""
 ██████╗ ███╗   ██╗███████╗    ██████╗ ███╗   ██╗███████╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
 ██╔══██╗████╗  ██║██╔════╝    ██╔══██╗████╗  ██║██╔════╝    ██╔════╝████╗  ██║██║   ██║████╗ ████║
 ██║  ██║██╔██╗ ██║███████╗    ██║  ██║██╔██╗ ██║███████╗    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
 ██║  ██║██║╚██╗██║╚════██║    ██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
 ██████╔╝██║ ╚████║███████║    ██████╔╝██║ ╚████║███████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
 ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝

 DNS Enumerator Pro - Ferramenta Avançada de Enumeração DNS
 Author: Anderson | Uso autorizado apenas em alvos com permissão
────────────────────────────────────────────────────────────────────────────────
"""

import dns.resolver
import dns.query
import dns.zone
import dns.name
import dns.rdatatype
import dns.reversename
import sys
import os
import socket
import argparse
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from ipaddress import ip_address, ip_network

# ─── Cores ANSI ──────────────────────────────────────────────────────────────
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    C = Fore
    BG = Back
    S = Style
    HAS_COLORAMA = True
except ImportError:
    class Dummy:
        def __getattr__(self, name):
            return ""
    C = Dummy()
    BG = Dummy()
    S = Dummy()
    HAS_COLORAMA = False

# ─── Banner ──────────────────────────────────────────────────────────────────
BANNER = f"""
{C.CYAN}{S.BRIGHT}
██████╗ ███╗   ██╗███████╗    ██████╗ ███╗   ██╗███████╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗████╗  ██║██╔════╝    ██╔════╝████╗  ██║██║   ██║████╗ ████║
██║  ██║██╔██╗ ██║███████╗    ██║  ██║██╔██╗ ██║███████╗    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
██║  ██║██║╚██╗██║╚════██║    ██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
██████╔╝██║ ╚████║███████║    ██████╔╝██║ ╚████║███████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
{C.RESET}
{C.YELLOW}DNS Enumerator Pro - Advanced DNS Enumeration Tool{C.RESET}
{C.WHITE}Author: Anderson | {C.RED}Apenas para uso autorizado{C.RESET}
"""

# ─── Configurações Globais ──────────────────────────────────────────────────
TIMEOUT = 5
LIFETIME = 10
MAX_WORKERS = 20

# ─── CDN / Cloud Providers conhecidos ────────────────────────────────────────
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
    "Fastly": [
        "23.235.32.0/20", "104.156.80.0/20", "151.101.0.0/16",
        "199.27.72.0/21",
    ],
    "Akamai": [
        "23.32.0.0/11", "23.64.0.0/14", "23.72.0.0/13",
        "23.80.0.0/12", "23.208.0.0/12", "23.216.0.0/13",
        "2.16.0.0/13", "2.20.0.0/14", "2.22.0.0/15",
        "72.246.0.0/16", "92.122.0.0/15", "95.100.0.0/15",
        "173.223.0.0/16", "184.51.0.0/16", "184.85.0.0/16",
    ],
    "Google Cloud/CDN": [
        "8.34.208.0/20", "8.35.192.0/21", "23.236.48.0/20",
        "23.251.128.0/19", "34.64.0.0/10", "34.128.0.0/10",
        "35.184.0.0/14", "35.188.0.0/16", "35.190.0.0/17",
        "35.196.0.0/15", "35.203.0.0/16", "35.207.0.0/17",
        "35.210.0.0/16", "35.220.0.0/15", "35.222.0.0/15",
        "35.235.0.0/16", "35.236.0.0/14", "35.240.0.0/15",
        "35.242.0.0/15", "35.244.0.0/15", "35.246.0.0/16",
        "35.247.0.0/16", "104.154.0.0/15", "104.196.0.0/14",
        "104.197.0.0/16", "104.198.0.0/15", "107.167.160.0/19",
        "107.178.192.0/18", "130.211.0.0/16", "146.148.0.0/17",
        "162.222.176.0/21", "172.217.0.0/16", "172.253.0.0/16",
        "173.194.0.0/16", "173.255.112.0/20", "192.158.28.0/22",
        "199.192.112.0/22", "199.223.232.0/21", "199.223.236.0/23",
        "209.85.128.0/17", "216.58.192.0/19", "216.239.32.0/19",
    ],
}

COMMON_SRV_SERVICES = [
    "_sip._tcp", "_sip._udp", "_sips._tcp",
    "_h323cs._tcp", "_h323ls._udp",
    "_sip._tls", "_jabber._tcp", "_xmpp._tcp",
    "_ldap._tcp", "_kerberos._tcp", "_kerberos._udp",
    "_imap._tcp", "_pop3._tcp", "_smtp._tcp",
]

COMMON_SUBDOMAINS = [
    "www", "mail", "smtp", "pop", "imap", "admin", "blog",
    "ftp", "ssh", "webmail", "cpanel", "whm", "ns1", "ns2",
    "ns3", "mx", "mail1", "mail2", "vpn", "remote", "api",
    "dev", "test", "staging", "app", "portal", "secure",
    "login", "register", "forum", "support", "help", "status",
    "git", "jenkins", "jira", "confluence", "wiki", "docs",
    "cdn", "static", "assets", "img", "images", "css", "js",
    "download", "uploads", "files", "backup", "db", "database",
    "mysql", "redis", "rabbitmq", "kafka", "zookeeper",
    "monitor", "grafana", "prometheus", "kibana", "elastic",
    "swagger", "redoc", "graphql", "rest", "soap", "xmlrpc",
    "owa", "exchange", "autodiscover", "lync", "skype",
    "radius", "tacacs", "ldap", "ad", "dc1", "dc2",
    "dns", "dns1", "dns2", "ntp", "time", "syslog",
    "proxy", "squid", "firewall", "ids", "ips", "waf",
    "phpmyadmin", "phpmyadmin1", "phpmyadmin2",
    "pma", "adminer", "webmin", "usermin",
    "router", "switch", "ap", "wifi", "guest",
    "intranet", "extranet", "partner", "vendor",
    "s3", "bucket", "storage", "cloud", "direct",
    "m", "mobile", "mobi", "wap",
    "newsletter", "mailing", "lists", "bounce",
    "tracking", "analytics", "stats", "metrics",
]

# ══════════════════════════════════════════════════════════════════════════════
#  CLASSES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

class Spinner:
    def __init__(self, msg="Processando"):
        self.msg = msg
        self.spinning = False
        self.thread = None

    def start(self):
        self.spinning = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        chars = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u280f\u280f"
        i = 0
        while self.spinning:
            sys.stdout.write(f"\r{C.CYAN}{chars[i % len(chars)]} {self.msg}{C.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def stop(self, status="OK"):
        self.spinning = False
        if self.thread:
            self.thread.join(0.3)
        # Limpa a linha do spinner completamente
        sys.stdout.write(f"\r{' ' * (len(self.msg) + 10)}\r")
        sys.stdout.flush()


class DNSError(Exception):
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES DE RESOLUÇÃO DNS
# ══════════════════════════════════════════════════════════════════════════════

def resolve_with_fallback(domain, rtype, nameserver=None, timeout=TIMEOUT, lifetime=LIFETIME):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = lifetime
    if nameserver:
        resolver.nameservers = [nameserver]
    try:
        resposta = resolver.resolve(domain, rtype, raise_on_no_answer=False)
        if resposta.rrset:
            return list(resposta.rrset)
        return []
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout) as e:
        raise DNSError(str(e))


def resolve_ip(hostname, rtype="A", timeout=TIMEOUT):
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
#  MÓDULOS DE ENUMERAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def enum_a(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "A", nameserver)
    if not records:
        return results
    for rr in records:
        ip = rr.address
        cdn = detect_cdn(ip)
        line = f"  {C.GREEN}A{C.RESET}       {ip:20s}"
        if cdn:
            line += f"  {C.YELLOW}[{cdn}]{C.RESET}"
        results.append(line)
    # Wildcard detection
    random_sub = f"xkcd{int(time.time())%10000}.{domain}"
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5
        resp = resolver.resolve(random_sub, "A")
        if resp.rrset:
            results.insert(0, f"  {C.RED}⚠  WILDCARD DETECTED!{C.RESET}")
    except Exception:
        pass
    return results


def enum_aaaa(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "AAAA", nameserver)
    for rr in records:
        results.append(f"  {C.CYAN}AAAA{C.RESET}    {rr.address}")
    return results


def enum_ns(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "NS", nameserver)
    for rr in records:
        ns_host = rr.target.to_text().rstrip(".")
        ns_ip = resolve_ip(ns_host) or resolve_ip(ns_host, "AAAA") or "?"
        results.append(f"  {C.YELLOW}NS{C.RESET}      {ns_host:35s}  →  {ns_ip}")
    return results


def enum_mx(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "MX", nameserver)
    for rr in records:
        pref = rr.preference
        mx_host = rr.exchange.to_text().rstrip(".")
        mx_ip = resolve_ip(mx_host) or resolve_ip(mx_host, "AAAA") or "?"
        results.append(f"  {C.MAGENTA}MX{C.RESET}      {mx_host:35s}  ({pref})  →  {mx_ip}")
    return results


def enum_txt(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "TXT", nameserver)
    for rr in records:
        txt_data = " ".join(s.decode() if isinstance(s, bytes) else s for s in rr.strings)
        txt_short = txt_data[:200] + "..." if len(txt_data) > 200 else txt_data
        if txt_data.startswith("v=spf1"):
            results.append(f"  {C.GREEN}TXT{C.RESET}      {C.GREEN}[SPF]{C.RESET} {txt_short}")
        elif txt_data.startswith("v=DMARC1"):
            results.append(f"  {C.GREEN}TXT{C.RESET}      {C.GREEN}[DMARC]{C.RESET} {txt_short}")
        else:
            results.append(f"  {C.WHITE}TXT{C.RESET}      {txt_short}")
    return results


def enum_soa(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "SOA", nameserver)
    for rr in records:
        results.append(
            f"  {C.BLUE}SOA{C.RESET}\n"
            f"       MNAME:    {rr.mname}\n"
            f"       RNAME:    {rr.rname}\n"
            f"       SERIAL:   {rr.serial}\n"
            f"       REFRESH:  {rr.refresh}s\n"
            f"       RETRY:    {rr.retry}s\n"
            f"       EXPIRE:   {rr.expire}s\n"
            f"       MINIMUM:  {rr.minimum}s"
        )
    return results


def enum_cname(domain, nameserver=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "CNAME", nameserver)
        for rr in records:
            results.append(f"  {C.CYAN}CNAME{C.RESET}    → {rr.target.to_text().rstrip('.')}")
    except DNSError:
        pass
    return results


def enum_ptr(domain, nameserver=None):
    results = []
    try:
        a_records = resolve_with_fallback(domain, "A", nameserver)
        for rr in a_records:
            try:
                rev_name = dns.reversename.from_address(rr.address)
                rev_records = resolve_with_fallback(rev_name, "PTR", nameserver)
                for ptr_rr in rev_records:
                    results.append(f"  {C.YELLOW}PTR{C.RESET}     {rr.address:20s}  ←  {ptr_rr.target.to_text().rstrip('.')}")
            except Exception:
                results.append(f"  {C.YELLOW}PTR{C.RESET}     {rr.address:20s}  ←  {C.RED}(sem PTR){C.RESET}")
    except Exception:
        pass
    return results


def enum_hinfo(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "HINFO", nameserver)
    for rr in records:
        results.append(f"  {C.WHITE}HINFO{C.RESET}    CPU: {rr.cpu}  OS: {rr.os}")
    return results


def enum_srv(domain, nameserver=None):
    results = []
    for service in COMMON_SRV_SERVICES:
        srv_domain = f"{service}.{domain}"
        try:
            records = resolve_with_fallback(srv_domain, "SRV", nameserver)
            for rr in records:
                target = rr.target.to_text().rstrip(".")
                target_ip = resolve_ip(target) or resolve_ip(target, "AAAA") or "?"
                results.append(
                    f"  {C.MAGENTA}SRV{C.RESET}     {srv_domain:30s}  "
                    f"→ {target} ({target_ip}):{rr.port}  "
                    f"prio={rr.priority} weight={rr.weight}"
                )
        except DNSError:
            pass
    return results


def enum_ds(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "DS", nameserver)
    for rr in records:
        results.append(
            f"  {C.RED}DS{C.RESET}      KeyTag={rr.key_tag} Algorithm={rr.algorithm} "
            f"DigestType={rr.digest_type} Digest={rr.digest.hex()}"
        )
    return results


def enum_nsec3(domain, nameserver=None):
    results = []
    records = resolve_with_fallback(domain, "NSEC3", nameserver)
    for rr in records:
        results.append(
            f"  {C.RED}NSEC3{C.RESET}   {rr.next_hashed_owner_name.hex()} "
            f"Flags={rr.flags} Iterations={rr.iterations}"
        )
    return results


def enum_caa(domain, nameserver=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "CAA", nameserver)
        for rr in records:
            tag = rr.tag.decode() if isinstance(rr.tag, bytes) else rr.tag
            value = rr.value.decode() if isinstance(rr.value, bytes) else rr.value
            results.append(f"  {C.BLUE}CAA{C.RESET}     Flags={rr.flags} {tag}={value}")
    except DNSError:
        pass
    return results


def enum_dnskey(domain, nameserver=None):
    results = []
    try:
        records = resolve_with_fallback(domain, "DNSKEY", nameserver)
        for rr in records:
            algo_name = dns.dnssec.algorithm_to_text(rr.algorithm)
            results.append(
                f"  {C.RED}DNSKEY{C.RESET}  Flags={rr.flags} Protocol={rr.protocol} "
                f"Algorithm={algo_name} Key={rr.key.hex()[:40]}..."
            )
    except (DNSError, AttributeError):
        pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSFERÊNCIA DE ZONA (AXFR) — SAÍDA EM TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def enum_axfr(domain, nameserver=None, timeout=TIMEOUT, live=True):
    """
    Tenta transferência de zona (AXFR) em todos os nameservers.
    Com live=True, imprime cada linha assim que descoberta.
    """
    results = []
    ns_list = []

    if nameserver:
        ns_list = [nameserver]
    else:
        try:
            records = resolve_with_fallback(domain, "NS")
            for rr in records:
                ns_host = rr.target.to_text().rstrip(".")
                ns_list.append(ns_host)
        except DNSError:
            msg = f"  {C.RED}⚠  Não foi possível descobrir nameservers para AXFR{C.RESET}"
            results.append(msg)
            if live: print(msg)
            return results

    if not ns_list:
        msg = f"  {C.RED}⚠  Nenhum nameserver encontrado para tentar AXFR{C.RESET}"
        results.append(msg)
        if live: print(msg)
        return results

    zone_fqdn = domain if domain.endswith('.') else domain + '.'

    for ns_host in ns_list:
        msg = f"\n  {C.YELLOW}▶  Tentando AXFR em: {ns_host}{C.RESET}"
        results.append(msg)
        if live: print(msg)

        ns_ip = resolve_ip(ns_host, "A", timeout)
        if not ns_ip:
            msg = f"  {C.RED}✘  Não foi possível resolver {ns_host} para IPv4{C.RESET}"
            results.append(msg)
            if live: print(msg)
            continue

        msg = f"  {C.WHITE}   → IP: {ns_ip}{C.RESET}"
        results.append(msg)
        if live: print(msg)

        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout + 5)

        try:
            xfr_generator = dns.query.xfr(
                ns_ip,
                zone_fqdn,
                timeout=timeout,
                lifetime=timeout + 5,
                port=53,
            )

            try:
                zone = dns.zone.from_xfr(xfr_generator, relativize=True)
            except (ValueError, StopIteration, TypeError) as e:
                msg = f"  {C.YELLOW}   ⚡ from_xfr: {e}, tentando inbound_xfr...{C.RESET}"
                results.append(msg)
                if live: print(msg)
                zone = dns.zone.Zone(zone_fqdn)
                dns.query.inbound_xfr(
                    ns_ip,
                    zone,
                    timeout=timeout,
                    lifetime=timeout + 5,
                    port=53,
                )

            socket.setdefaulttimeout(old_timeout)

            msg = f"\n  {C.GREEN}✅ TRANSFERÊNCIA DE ZONA BEM-SUCEDIDA em: {ns_host}{C.RESET}"
            results.append(msg)
            if live: print(msg)

            results.append(f"  {'─'*60}")
            if live: print(f"  {'─'*60}")

            origin = zone.origin
            names = sorted(zone.nodes.keys())

            if not names:
                msg = f"  {C.YELLOW}   ⚠  Zona transferida, mas nenhum registro encontrado.{C.RESET}"
                results.append(msg)
                if live: print(msg)
                continue

            for nome in names:
                node = zone[nome]
                for rdataset in node:
                    rdtype_str = dns.rdatatype.to_text(rdataset.rdtype)
                    for rr in rdataset:
                        try:
                            host_str = nome.relative_to(origin).to_text()
                        except Exception:
                            host_str = str(nome)
                        if host_str == '@' or host_str.rstrip('.') == origin.to_text().rstrip('.'):
                            host_str = '@'
                        line = f"    {host_str:40s} {rdtype_str:8s} {rr}"
                        results.append(line)
                        if live:
                            print(line)
                            sys.stdout.flush()

            footer = f"  {'─'*60}"
            results.append(footer)
            if live: print(footer)

            count_msg = f"  {C.GREEN}📊  Total: {len(names)} registros de {ns_host}{C.RESET}"
            results.append(count_msg)
            if live: print(count_msg)

        except dns.query.TransferError:
            msg = f"\n\n  {C.RED}✘  AXFR rejeitada por: {ns_host}{C.RESET}"
            results.append(msg)
            if live: print(msg)
        except dns.exception.Timeout:
            msg = f"  {C.RED}✘  AXFR timeout em {ns_host} ({timeout}s){C.RESET}"
            results.append(msg)
            if live: print(msg)
        except ConnectionRefusedError:
            msg = f"  {C.RED}✘  Conexão recusada em {ns_host}: porta 53 fechada{C.RESET}"
            results.append(msg)
            if live: print(msg)
        except OSError as e:
            msg = f"  {C.RED}✘  Erro de socket em {ns_host}: {e}{C.RESET}"
            results.append(msg)
            if live: print(msg)
        except Exception as e:
            msg = f"  {C.RED}✘  AXFR falhou em {ns_host}: {e}{C.RESET}"
            results.append(msg)
            if live: print(msg)
        finally:
            try:
                socket.setdefaulttimeout(old_timeout)
            except Exception:
                pass

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  SUBDOMAIN BRUTEFORCE — SAÍDA EM TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def enum_subdomains(domain, wordlist=None, max_threads=MAX_WORKERS, live=True):
    """
    Bruteforce de subdomínios com saída em tempo real.
    Cada subdomínio encontrado é impresso imediatamente.
    """
    results = []

    if isinstance(wordlist, str):
        try:
            with open(wordlist, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            msg = f"\n  {C.GREEN}📖  Wordlist carregada: {wordlist} ({len(words)} palavras){C.RESET}"
            results.append(msg)
            if live: print(msg)
        except FileNotFoundError:
            msg = f"  {C.RED}✘  Wordlist não encontrada: {wordlist}. Usando padrão.{C.RESET}"
            results.append(msg)
            if live: print(msg)
            words = COMMON_SUBDOMAINS
        except Exception as e:
            msg = f"  {C.RED}✘  Erro ao ler wordlist: {e}. Usando padrão.{C.RESET}"
            results.append(msg)
            if live: print(msg)
            words = COMMON_SUBDOMAINS
    elif wordlist is None:
        words = COMMON_SUBDOMAINS
    else:
        words = wordlist

    total = len(words)
    if total == 0:
        msg = f"  {C.RED}⚠  Wordlist vazia!{C.RESET}"
        results.append(msg)
        if live: print(msg)
        return results

    msg = f"\n  {C.YELLOW}▶  Bruteforce de subdomínios iniciado ({total} palavras){C.RESET}\n"
    results.append(msg)
    if live: print(msg)

    found_count = [0]
    lock = threading.Lock()

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
                tag = f" [{cdn}]" if cdn else ""
                line = f"    {C.GREEN}✅ {subdomain:45s} → {ip}{tag}{C.RESET}"
                with lock:
                    found_count[0] += 1
                    results.append(line)
                    if live:
                        print(line)
                        sys.stdout.flush()
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        list(executor.map(check_sub, words))

    msg = f"\n  {C.GREEN}✅ Bruteforce concluído. {found_count[0]} subdomínios encontrados.{C.RESET}"
    results.append(msg)
    if live: print(msg)
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÃO PRINCIPAL DE ENUMERAÇÃO — SAÍDA EM TEMPO REAL
# ══════════════════════════════════════════════════════════════════════════════

def enumerate_domain(domain, nameserver=None, record_types=None,
                     do_axfr=False, do_subdomain=False, wordlist=None,
                     timeout=TIMEOUT, live=True):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    all_results = {}

    separator = f"{'═' * 70}"

    header = [
        f"\n\n{C.GREEN}{S.BRIGHT}📡  Alvo: {domain}{C.RESET}\n",
        f"\n  {C.WHITE}Data: {timestamp}{C.RESET}\n",
        f"\n  {C.WHITE}Nameserver: {nameserver or 'Automático (padrão do sistema)'}{C.RESET}\n",
        f"\n  {C.WHITE}Timeout: {timeout}s{C.RESET}\n",
        separator,
    ]

    if live:
        for line in header:
            print(line, end="")
            sys.stdout.flush()

    all_results["__header__"] = header

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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for rtype in record_types:
            if rtype in type_funcs:
                name, func = type_funcs[rtype]
                futures[executor.submit(func, domain, nameserver)] = (rtype, name)

        for future in as_completed(futures):
            rtype, name = futures[future]
            try:
                result_lines = future.result()
                if result_lines:
                    if live:
                        print(f"\n{C.BLUE}{S.BRIGHT}📌  {name}{C.RESET}")
                        print(f"  {C.WHITE}{'─' * 60}{C.RESET}")
                        for line in result_lines:
                            print(line)
                        sys.stdout.flush()
                    all_results[rtype] = {"title": name, "lines": result_lines}
            except Exception as e:
                err = [f"  {C.RED}Erro: {e}{C.RESET}"]
                all_results[rtype] = {"title": name, "lines": err}
                if live:
                    print(f"\n{C.BLUE}{S.BRIGHT}📌  {name}{C.RESET}")
                    print(f"  {C.RED}Erro: {e}{C.RESET}")
                    sys.stdout.flush()

    if do_axfr:
        axfr_results = enum_axfr(domain, nameserver, timeout, live=live)
        if axfr_results:
            all_results["AXFR"] = {
                "title": "Transferência de Zona (AXFR)",
                "lines": axfr_results,
            }

    if do_subdomain:
        sub_results = enum_subdomains(domain, wordlist, live=live)
        if sub_results:
            all_results["SUBDOMAIN"] = {
                "title": "Subdomínios (Bruteforce)",
                "lines": sub_results,
            }

    return all_results


# ══════════════════════════════════════════════════════════════════════════════
#  FORMATAÇÃO E SAÍDA
# ══════════════════════════════════════════════════════════════════════════════

def print_results(results):
    separator = f"{'═' * 70}"
    if "__header__" in results:
        for line in results["__header__"]:
            print(line)

    for key, data in results.items():
        if key == "__header__":
            continue
        if isinstance(data, dict) and "title" in data and "lines" in data:
            if data["lines"]:
                print(f"\n{C.BLUE}{S.BRIGHT}📌  {data['title']}{C.RESET}")
                print(f"  {C.WHITE}{'─' * 60}{C.RESET}")
                for line in data["lines"]:
                    print(line)

    print(f"\n{separator}\n")
    print(f"{C.GREEN}{S.BRIGHT}✅  Enumeração concluída!{C.RESET}\n")
    print(f"{C.WHITE}Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{C.RESET}\n")
    print(f"{separator}\n")


def save_results(results, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("DNS ENUMERATOR PRO - Resultados\n")
        f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n")
        for key, data in results.items():
            if key == "__header__":
                continue
            if isinstance(data, dict) and "title" in data and "lines" in data:
                f.write(f"\n📌  {data['title']}\n")
                f.write(f"  {'─' * 60}\n")
                for line in data["lines"]:
                    clean = line
                    for code in [C.RED, C.GREEN, C.YELLOW, C.BLUE, C.MAGENTA,
                                 C.CYAN, C.WHITE, C.RESET, S.BRIGHT]:
                        clean = clean.replace(code, "")
                    f.write(clean + "\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("FIM DO RELATÓRIO\n")
    print(f"\n{C.GREEN}💾  Resultados salvos em: {filename}{C.RESET}")


def save_json(results, filename):
    json_data = {"timestamp": datetime.now().isoformat(), "records": {}}
    for key, data in results.items():
        if key == "__header__":
            continue
        if isinstance(data, dict) and "title" in data and "lines" in data:
            clean_lines = []
            for line in data["lines"]:
                for code in [C.RED, C.GREEN, C.YELLOW, C.BLUE, C.MAGENTA,
                             C.CYAN, C.WHITE, C.RESET, S.BRIGHT]:
                    line = line.replace(code, "")
                clean_lines.append(line.strip())
            json_data["records"][key] = {"type": data["title"], "results": clean_lines}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"\n{C.GREEN}💾  Resultados salvos em JSON: {filename}{C.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  MODO INTERATIVO - CORRIGIDO (SEM SPINNER)
# ══════════════════════════════════════════════════════════════════════════════

def interactive_mode():
    print(BANNER)
    print(f"{C.YELLOW}╔══════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.YELLOW}║       MODO INTERATIVO - DNS ENUMERATOR PRO       ║{C.RESET}")
    print(f"{C.YELLOW}╚══════════════════════════════════════════════════╝{C.RESET}\n")

    domain = input(f"\n{C.CYAN}🎯  Domínio alvo: {C.RESET}").strip()
    if not domain:
        print(f"{C.RED}✘  Domínio inválido.{C.RESET}")
        return

    ns = input(f"{C.CYAN}🌐  Nameserver (opcional, Enter para auto): {C.RESET}").strip() or None

    print(f"\n{C.WHITE}📋  Tipos de registro disponíveis:{C.RESET}")
    all_types = ["A", "AAAA", "NS", "MX", "TXT", "SOA", "CNAME", "PTR",
                 "HINFO", "SRV", "DS", "NSEC3", "CAA", "DNSKEY"]
    print(f"  {', '.join(all_types)}")
    types_input = input(f"{C.CYAN}📌  Tipos (separados por vírgula, Enter para TODOS): {C.RESET}").strip()
    record_types = [t.strip().upper() for t in types_input.split(",") if t.strip()] if types_input else None

    do_axfr = input(f"{C.CYAN}⬇  Tentar transferência de zona? (s/N): {C.RESET}").strip().lower() == "s"
    do_sub = input(f"{C.CYAN}🔍  Bruteforce de subdomínios? (s/N): {C.RESET}").strip().lower() == "s"

    wordlist_file = None
    if do_sub:
        wl = input(f"{C.CYAN}📖  Wordlist personalizada? (caminho ou Enter para padrão): {C.RESET}").strip()
        if wl:
            wordlist_file = wl

    timeout_input = input(f"{C.CYAN}⏱️  Timeout em segundos (padrão 5): {C.RESET}").strip()
    timeout = int(timeout_input) if timeout_input.isdigit() else 5

    save_file = input(f"{C.CYAN}💾  Salvar em arquivo? (nome.txt ou Enter para não salvar): {C.RESET}").strip()
    save_file_json = input(f"{C.CYAN}💾  Salvar em JSON? (nome.json ou Enter para não salvar): {C.RESET}").strip()

    print(f"\n{C.GREEN}▶  Iniciando enumeração de: {domain} {C.RESET}\n")

    # ═══ CORREÇÃO: sem spinner, usa live=True direto ═══
    results = enumerate_domain(
        domain=domain,
        nameserver=ns,
        record_types=record_types,
        do_axfr=do_axfr,
        do_subdomain=do_sub,
        wordlist=wordlist_file,
        timeout=timeout,
        live=True,
    )
    # ════════════════════════════════════════════════════

    # Footer
    separator = f"{'═' * 70}"
    print(f"\n{separator}\n")
    print(f"\n{C.GREEN}{S.BRIGHT}✅  Enumeração concluída!{C.RESET}\n")
    print(f"{C.WHITE}Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{C.RESET}\n")
    print(f"{separator}\n")

    if save_file:
        save_results(results, save_file)
    if save_file_json:
        save_json(results, save_file_json)


# ══════════════════════════════════════════════════════════════════════════════
#  MODO ARGUMENTOS DE LINHA DE COMANDO
# ══════════════════════════════════════════════════════════════════════════════

def cli_mode(args):
    if args.types:
        record_types = [t.upper() for t in args.types]
    else:
        record_types = None

    wordlist_arg = args.wordlist if args.bruteforce and args.wordlist else None

    results = enumerate_domain(
        domain=args.domain,
        nameserver=args.nameserver,
        record_types=record_types,
        do_axfr=args.axfr,
        do_subdomain=args.bruteforce,
        wordlist=wordlist_arg,
        timeout=args.timeout,
        live=True,
    )

    if args.output:
        save_results(results, args.output)
    elif args.json_output:
        save_json(results, args.json_output)
    else:
        separator = f"{'═' * 70}"
        print(f"\n{separator}\n")
        print(f"{C.GREEN}{S.BRIGHT}✅  Enumeração concluída!{C.RESET}\n")
        print(f"{C.WHITE}Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{C.RESET}\n")
        print(f"{separator}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=f"{C.CYAN}DNS Enumerator Pro - Enumeração DNS Avançada (Tempo Real){C.RESET}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{C.YELLOW}EXEMPLOS:{C.RESET}
  {C.GREEN}# Modo interativo (recomendado){C.RESET}
  python3 dns_enum_pro.py

  {C.GREEN}# Enumeração rápida via CLI{C.RESET}
  python3 dns_enum_pro.py -d exemplo.com

  {C.GREEN}# Tipos específicos + AXFR + salvar{C.RESET}
  python3 dns_enum_pro.py -d exemplo.com -t A MX TXT SOA NS --axfr -o resultado.txt

  {C.GREEN}# Bruteforce com wordlist personalizada{C.RESET}
  python3 dns_enum_pro.py -d exemplo.com --bruteforce -w wordlist.txt

  {C.GREEN}# JSON output{C.RESET}
  python3 dns_enum_pro.py -d exemplo.com --json resultado.json

{C.YELLOW}ATENÇÃO:{C.RESET} Use apenas em domínios que você possui autorização para testar.
        """
    )

    parser.add_argument("-d", "--domain", help="Domínio alvo para enumeração")
    parser.add_argument("-n", "--nameserver", help="Nameserver específico para consultas")
    parser.add_argument("-t", "--types", nargs="+", help="Tipos de registro (ex: A MX NS TXT)")
    parser.add_argument("--axfr", action="store_true", help="Tentar transferência de zona (AXFR)")
    parser.add_argument("--bruteforce", action="store_true", help="Bruteforce de subdomínios")
    parser.add_argument("-w", "--wordlist", help="Arquivo de wordlist (uma palavra por linha)")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout em segundos (padrão: 5)")
    parser.add_argument("-o", "--output", help="Salvar resultados em arquivo de texto")
    parser.add_argument("--json", help="Salvar resultados em JSON", dest="json_output")
    parser.add_argument("-i", "--interactive", action="store_true", help="Forçar modo interativo")

    args = parser.parse_args()

    if not HAS_COLORAMA:
        print("ℹ️  Para melhores cores, instale colorama: pip install colorama", file=sys.stderr)

    if args.interactive or not args.domain:
        interactive_mode()
    else:
        if not args.json_output and not args.output:
            print(BANNER)
            print(f"{C.GREEN}▶  Modo CLI - Domínio: {args.domain}{C.RESET}\n")

        cli_mode(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}⚠  Interrompido pelo usuário.{C.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{C.RED}✘  Erro fatal: {e}{C.RESET}")
        sys.exit(1)
