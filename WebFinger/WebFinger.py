#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebFinger Ferramenta de fingerprinting com seletor de temas
Requisitos: pip install requests beautifulsoup4
Uso: python3 WebFinger.py
"""
import platform
import re
import hashlib
import socket
import threading
import webbrowser
import datetime
import html as htmllib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) "
                  "AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 "
                  "Mobile/11D201 Safari/9537.53)"
}

# ═══════════════════════════════════════════════════════════════
#  ESQUEMAS DE CORES POR TEMA
# ═══════════════════════════════════════════════════════════════

TEMAS_CORES = {
    "escuro": {
        "bg_principal": "#0f1420",
        "bg_card": "#1a2233",
        "bg_input": "#1a2233",
        "fg_texto": "#e6e9f0",
        "fg_titulo": "#4fc3f7",
        "fg_sucesso": "#7ee787",
        "fg_aviso": "#ffcc00",
        "fg_erro": "#ff6b6b",
        "fg_muted": "#8a93a6",
        "bg_botao": "#4fc3f7",
        "fg_botao": "#0f1420",
        "bg_botao2": "#2a3550",
        "fg_botao2": "#e6e9f0",
        "bg_salvar": "#7ee787",
        "fg_salvar": "#0f1420",
        "bg_heading": "#2a3550",
        "fg_heading": "#4fc3f7",
        "bg_tree": "#1a2233",
        "fg_tree": "#e6e9f0",
        "bg_tree_sel": "#2a3550",
        "borda": "#2a3550",
        "fg_code": "#c9d3e8",
        "bg_progress": "#1a2233",
        "fg_progress": "#4fc3f7",
    },
    "claro": {
        "bg_principal": "#f0f2f5",
        "bg_card": "#ffffff",
        "bg_input": "#ffffff",
        "fg_texto": "#1a1a2e",
        "fg_titulo": "#0066cc",
        "fg_sucesso": "#28a745",
        "fg_aviso": "#e6a800",
        "fg_erro": "#dc3545",
        "fg_muted": "#6c757d",
        "bg_botao": "#0066cc",
        "fg_botao": "#ffffff",
        "bg_botao2": "#e0e4ea",
        "fg_botao2": "#1a1a2e",
        "bg_salvar": "#28a745",
        "fg_salvar": "#ffffff",
        "bg_heading": "#e0e4ea",
        "fg_heading": "#0066cc",
        "bg_tree": "#ffffff",
        "fg_tree": "#1a1a2e",
        "bg_tree_sel": "#cce5ff",
        "borda": "#ced4da",
        "fg_code": "#333333",
        "bg_progress": "#e0e4ea",
        "fg_progress": "#0066cc",
    },
}

# Mapeia temas ttk → esquema de cores
TEMA_PARA_ESQUEMA = {
    "clam": "escuro",
    "alt": "claro",
    "default": "claro",
    "classic": "claro",
    "vista": "claro",
    "winnative": "claro",
    "xpnative": "claro",
    "aqua": "claro",
}


# ═══════════════════════════════════════════════════════════════
#  MOTOR DE FINGERPRINT (sem alterações na lógica)
# ═══════════════════════════════════════════════════════════════

def normalize_url(url):
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


def get_ip(host):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return "N/D"


def get_dns_info(host):
    info = {}
    try:
        results = socket.getaddrinfo(host, None)
        ips = sorted(list(set(str(r[4][0]) for r in results)))
        info["todos_ips"] = ", ".join(ips)
    except Exception:
        info["todos_ips"] = "N/D"
    try:
        ip_addr = get_ip(host)
        if ip_addr != "N/D":
            info["reverso"] = str(socket.gethostbyaddr(ip_addr)[0])
        else:
            info["reverso"] = "N/D"
    except Exception:
        info["reverso"] = "N/D"
    return info


def detect_technologies(url, resp, body, soup):
    results = []
    headers = resp.headers
    body_l = body.lower()

    def add(name, version=""):
        results.append((name, version))

    server = headers.get("Server", "")
    if server:
        add("Servidor HTTP", server)
    powered = headers.get("X-Powered-By", "")
    if powered:
        add("X-Powered-By", powered)
    if "X-AspNet-Version" in headers:
        add("ASP.NET", headers["X-AspNet-Version"])
    if "X-Generator" in headers:
        add("Gerador", headers["X-Generator"])

    ct = headers.get("Content-Type", "")
    if ct:
        add("Content-Type", ct)

    cookies = resp.cookies
    if cookies:
        cookie_names = [c.name for c in cookies]
        add("Cookies", ", ".join(cookie_names[:15]))
        for cn in cookie_names:
            cn_l = cn.lower()
            if "phpsessid" in cn_l:
                add("PHP (via cookie)", "PHPSESSID detectado")
            if "asp.net" in cn_l or "aspsessionid" in cn_l:
                add("ASP.NET (via cookie)", cn)
            if "jsessionid" in cn_l:
                add("Java/JSP (via cookie)", "JSESSIONID detectado")
            if "laravel" in cn_l:
                add("Laravel (via cookie)", cn)
            if "django" in cn_l or "csrftoken" == cn_l:
                add("Django (via cookie)", cn)
            if "wordpress" in cn_l or "wp-" in cn_l:
                add("WordPress (via cookie)", cn)

    security_headers = {
        "Strict-Transport-Security": "HSTS",
        "Content-Security-Policy": "CSP",
        "X-Content-Type-Options": "X-Content-Type-Options",
        "X-Frame-Options": "X-Frame-Options",
        "X-XSS-Protection": "X-XSS-Protection",
        "Referrer-Policy": "Referrer-Policy",
        "Permissions-Policy": "Permissions-Policy",
        "Access-Control-Allow-Origin": "CORS",
    }
    presentes, ausentes = [], []
    for hdr, nome in security_headers.items():
        if hdr in headers:
            presentes.append(f"✅ {nome}: {headers[hdr][:80]}")
        else:
            ausentes.append(f"❌ {nome}")
    if presentes:
        add("Headers de Segurança ✅", f"{len(presentes)} presentes")
        for p in presentes:
            add("  ↳ Presente", p)
    if ausentes:
        add("Headers de Segurança ❌", f"{len(ausentes)} ausentes")
        for a in ausentes:
            add("  ↳ Ausente", a)

    cache = headers.get("Cache-Control", "")
    if cache:
        add("Cache-Control", cache)
    if "ETag" in headers:
        add("ETag", headers["ETag"])

    if headers.get("CF-RAY"):
        add("Cloudflare", f"CF-RAY: {headers['CF-RAY']}")
    if "cloudfront" in headers.get("Via", "").lower() or \
       "cloudfront" in headers.get("X-Cache", "").lower():
        add("Amazon CloudFront", "CDN")
    if "akamai" in str(headers).lower():
        add("Akamai", "CDN")
    if "varnish" in headers.get("Via", "").lower() or \
       "varnish" in headers.get("X-Varnish", "").lower():
        add("Varnish", "Cache proxy")
    if headers.get("X-Cache"):
        add("X-Cache", headers["X-Cache"])

    gen = soup.find("meta", attrs={"name": "generator"})
    if gen and gen.get("content"):
        add("Meta Generator", gen["content"])

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport and viewport.get("content"):
        add("Viewport (responsivo)", "Sim")

    charset_meta = soup.find("meta", attrs={"charset": True})
    if charset_meta:
        add("Charset", charset_meta["charset"])

    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        add("Open Graph", og["content"][:80])

    favicon = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
    if favicon and favicon.get("href"):
        add("Favicon", favicon["href"][:100])

    if "wp-content" in body_l or "wp-includes" in body_l:
        wp_ver = re.search(
            r'/wp-includes/(?:js|css)/[^"\']*?ver=([\d.]+)', body)
        add("WordPress", wp_ver.group(1) if wp_ver else "detectado")
    if "joomla" in body_l or "com_content" in body_l:
        add("Joomla", "detectado")
    if "drupal" in body_l or re.search(r'drupal\.js|sites/default/files', body_l):
        add("Drupal", "detectado")
    if "magento" in body_l or "mage/" in body_l:
        add("Magento", "detectado")
    if "wix.com" in body_l or "static.wixstatic" in body_l:
        add("Wix", "detectado")
    if "shopify" in body_l or "cdn.shopify" in body_l:
        add("Shopify", "detectado")

    if re.search(r'jquery[-.]?[\d.]*\.js|jquery\.min', body_l):
        m = re.search(r'jquery[.-]?(\d+\.\d+(?:\.\d+)?)', body_l)
        add("jQuery", m.group(1) if m else "detectado")
    if "react" in body_l and (
        "__NEXT_DATA__" in body or "reactjs" in body_l or "react.min" in body_l
    ):
        add("React", "detectado")
    if "angular" in body_l or "ng-app" in body_l:
        add("Angular", "detectado")
    if "vue" in body_l and (
        "vue.min" in body_l or "vue.js" in body_l or "__vue__" in body_l
    ):
        add("Vue.js", "detectado")
    if "bootstrap" in body_l:
        m = re.search(r'bootstrap[.-]?(\d+\.\d+(?:\.\d+)?)', body_l)
        add("Bootstrap", m.group(1) if m else "detectado")

    if re.search(r'laravel|csrf-token', body_l) and \
       "laravel" in str(cookies).lower():
        add("Laravel", "confirmado")
    if "django" in body_l or "csrfmiddlewaretoken" in body_l:
        add("Django", "possível")
    if "php" in ct.lower() or (
        "x-powered-by" in str(headers).lower() and "php" in powered.lower()
    ):
        add("PHP", powered if "php" in powered.lower() else "detectado")

    emails = sorted(set(re.findall(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body)))
    if emails:
        add("E-mails encontrados",
            ", ".join(emails[:10]) + ("..." if len(emails) > 10 else ""))

    forms = soup.find_all("form")
    if forms:
        add("Formulários HTML", f"{len(forms)} Encontrado")
    if re.search(r'type=["\']password["\']', body_l) or "wp-login" in body_l:
        add("Formulário de login", "detectado")

    return results


def extrair_links(url, soup, host):
    links_encontrados = []
    vistos = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        link_completo = urljoin(url, href)
        if link_completo not in vistos:
            vistos.add(link_completo)
            parsed_link = urlparse(link_completo)
            tipo = "Interno" if (
                parsed_link.hostname == host or parsed_link.hostname is None
            ) else "Externo"
            links_encontrados.append((tipo, link_completo))
    links_encontrados.sort(key=lambda x: (x[0] != "Interno", x[1]))
    return links_encontrados


def extrair_urls_do_codigo(body, host=None):
    padrao = re.compile(
        r'https?://'
        r'(?:[a-zA-Z0-9\-._~%!$&\'()*+,;=]+@)?'
        r'(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}'
        r'(?::\d{2,5})?'
        r'(?:/[^\s\'"<>\\]*)?',
        re.IGNORECASE,
    )
    encontradas = []
    vistos = set()
    for m in padrao.finditer(body):
        raw = m.group(0).rstrip('.,;:)]}>\'\"')
        raw = re.split(r'["\'\s<>]', raw)[0]
        if not raw or raw in vistos or len(raw) < 10:
            continue
        vistos.add(raw)
        parsed = urlparse(raw)
        esquema = (parsed.scheme or "").upper()
        dominio = parsed.hostname or "?"
        origem = "Interno" if (
            host and dominio and dominio.lower() == host.lower()
        ) else "Externo"
        path_l = (parsed.path or "").lower()
        if any(path_l.endswith(e) for e in (".js", ".mjs")):
            recurso = "JavaScript"
        elif path_l.endswith(".css"):
            recurso = "CSS"
        elif any(path_l.endswith(e) for e in (
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp"
        )):
            recurso = "Imagem"
        elif any(path_l.endswith(e) for e in (
            ".woff", ".woff2", ".ttf", ".eot", ".otf"
        )):
            recurso = "Fonte"
        elif any(path_l.endswith(e) for e in (
            ".mp4", ".webm", ".mp3", ".ogg", ".wav"
        )):
            recurso = "Mídia"
        elif any(path_l.endswith(e) for e in (".json", ".xml")):
            recurso = "Dados"
        elif any(path_l.endswith(e) for e in (".pdf", ".doc", ".zip", ".rar")):
            recurso = "Arquivo"
        elif "api" in path_l or "graphql" in path_l:
            recurso = "API"
        elif any(x in dominio for x in ("cdn", "cloudfront", "cloudflare")):
            recurso = "CDN"
        else:
            recurso = "Página/Outro"
        encontradas.append((esquema, origem, recurso, raw))
    encontradas.sort(key=lambda x: (x[0] != "HTTPS", x[1] != "Interno", x[3]))
    return encontradas


def scan_target(url, timeout=10, progress_callback=None):
    url = normalize_url(url)
    if not url:
        raise ValueError("URL vazia")
    parsed = urlparse(url)
    host = parsed.hostname or url
    total_steps = 10
    step = 0

    def advance(msg=""):
        nonlocal step
        step += 1
        if progress_callback:
            progress_callback(step, total_steps, msg)

    data = {
        "url": url, "ip": "", "erro": None, "techs": [],
        "status": None, "title": "", "hash_md5": "", "size": 0,
        "redirect": "", "headers": {}, "raw_headers": "",
        "dns_info": {}, "response_time": 0, "links": [],
        "source_code": "", "paths": [], "urls_codigo": [],
    }

    try:
        advance("Resolvendo DNS...")
        data["ip"] = get_ip(host)

        advance("Obtendo informações DNS...")
        data["dns_info"] = get_dns_info(host)

        advance("Enviando requisição HTTP...")
        import time
        t0 = time.time()
        resp = requests.get(
            url, headers=HEADERS, timeout=timeout,
            verify=False, allow_redirects=True,
        )
        data["response_time"] = round(time.time() - t0, 3)
        body = resp.text
        soup = BeautifulSoup(body, "html.parser")

        advance("Processando resposta e extraindo URLs...")
        data["status"] = resp.status_code
        data["redirect"] = (
            resp.url if resp.url.rstrip("/") != url.rstrip("/") else ""
        )
        data["headers"] = dict(resp.headers)
        data["raw_headers"] = "\n".join(
            f"{k}: {v}" for k, v in resp.headers.items()
        )
        title = soup.find("title")
        data["title"] = title.get_text(strip=True) if title else ""
        data["hash_md5"] = hashlib.md5(
            body.encode("utf-8", errors="ignore")
        ).hexdigest()
        data["size"] = len(body)
        data["source_code"] = body
        data["links"] = extrair_links(url, soup, host)
        data["urls_codigo"] = extrair_urls_do_codigo(body, host)

        advance("Detectando tecnologias...")
        data["techs"] = detect_technologies(url, resp, body, soup)

        probes = [
            ("wp-login.php", "WordPress Login"),
            ("admin", "Painel /admin"),
            ("administrator", "Painel Joomla"),
            ("robots.txt", "robots.txt"),
            ("sitemap.xml", "Sitemap XML"),
            (".env", "Arquivo .env (exposição)"),
            ("login", "Página de login"),
            ("wp-json", "WordPress REST API"),
            ("xmlrpc.php", "WordPress XML-RPC"),
            ("phpmyadmin", "phpMyAdmin"),
            ("wp-admin", "WordPress Admin"),
            ("api", "API endpoint"),
        ]

        advance("Testando paths comuns...")
        for path, label in probes:
            full_url = urljoin(
                url if url.endswith("/") else url + "/", path
            )
            try:
                r = requests.get(
                    full_url, headers=HEADERS, timeout=5,
                    verify=False, allow_redirects=True,
                )
                if r.status_code in (200, 401, 403, 301, 302):
                    status_txt = f"HTTP {r.status_code}"
                    if r.status_code == 200:
                        status_txt += " — Acessível"
                    elif r.status_code == 403:
                        status_txt += " — Proibido"
                    elif r.status_code == 401:
                        status_txt += " — Requer autenticação"
                    elif r.status_code in (301, 302):
                        status_txt += f" — Redirect → {r.url}"
                    data["paths"].append((full_url, label, status_txt))
                    data["techs"].append(
                        (f"Path: {full_url}", f"{label} ({status_txt})")
                    )
            except Exception:
                pass

        while step < total_steps:
            advance("Finalizando...")

    except Exception as e:
        data["erro"] = str(e)
        while step < total_steps:
            advance("Erro...")

    return data


# ═══════════════════════════════════════════════════════════════
#  RELATÓRIO HTML
# ═══════════════════════════════════════════════════════════════

def gerar_html(resultados, arquivo):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cards = []
    for r in resultados:
        if r["erro"]:
            corpo = (
                f'<div class="erro">Erro: {htmllib.escape(r["erro"])}</div>'
            )
        else:
            techs = ""
            for nome, ver in r["techs"]:
                techs += (
                    f"<tr><td class='tname'>{htmllib.escape(str(nome))}</td>"
                    f"<td>{htmllib.escape(str(ver))}</td></tr>"
                )
            if not techs:
                techs = (
                    "<tr><td colspan='2' class='nenhum'>"
                    "Nenhuma tecnologia identificada</td></tr>"
                )
            redirect = (
                f'<div class="mini">Redirect final: '
                f'{htmllib.escape(r["redirect"])}</div>'
                if r["redirect"] else ""
            )
            headers_html = ""
            if r.get("raw_headers"):
                headers_html = f"""
                <details>
                    <summary style="color:#4fc3f7;cursor:pointer;margin:10px 0;">
                        📋 Cabeçalhos HTTP completos</summary>
                    <pre style="background:#0f1420;padding:12px;border-radius:8px;
                    overflow-x:auto;font-size:.82em;">
{htmllib.escape(r['raw_headers'])}</pre>
                </details>"""

            links_html = ""
            if r.get("links"):
                links_list = "".join(
                    f"<li><b style='color:#8a93a6;'>[{htmllib.escape(t)}]</b> "
                    f"<a href='{htmllib.escape(u)}' target='_blank' "
                    f"style='color:#7ee787;text-decoration:none;'>"
                    f"{htmllib.escape(u)}</a></li>"
                    for t, u in r["links"]
                )
                links_html = f"""
                <details>
                    <summary style="color:#4fc3f7;cursor:pointer;margin:10px 0;">
                        🔗 Links &lt;a&gt; ({len(r['links'])})</summary>
                    <ul style="background:#0f1420;padding:12px 12px 12px 30px;
                    border-radius:8px;overflow-x:auto;font-size:.85em;margin:0;">
                        {links_list}
                    </ul>
                </details>"""

            urls_html = ""
            if r.get("urls_codigo"):
                urls_list = "".join(
                    f"<li><b style='color:#8a93a6;'>[{htmllib.escape(esq)}]</b> "
                    f"<b style='color:#c9d3e8;'>"
                    f"[{htmllib.escape(ori)}/{htmllib.escape(rec)}]</b> "
                    f"<a href='{htmllib.escape(u)}' target='_blank' "
                    f"style='color:#7ee787;text-decoration:none;'>"
                    f"{htmllib.escape(u)}</a></li>"
                    for esq, ori, rec, u in r["urls_codigo"]
                )
                urls_html = f"""
                <details>
                    <summary style="color:#4fc3f7;cursor:pointer;margin:10px 0;">
                        🌐 URLs no Código-Fonte ({len(r['urls_codigo'])})</summary>
                    <ul style="background:#0f1420;padding:12px 12px 12px 30px;
                    border-radius:8px;overflow-x:auto;font-size:.85em;margin:0;">
                        {urls_list}
                    </ul>
                </details>"""

            paths_html = ""
            if r.get("paths"):
                paths_list = "".join(
                    f"<li><a href='{htmllib.escape(u)}' target='_blank' "
                    f"style='color:#7ee787;'>{htmllib.escape(u)}</a> "
                    f"— {htmllib.escape(l)} <span style='color:#8a93a6;'>"
                    f"({htmllib.escape(s)})</span></li>"
                    for u, l, s in r["paths"]
                )
                paths_html = f"""
                <details>
                    <summary style="color:#4fc3f7;cursor:pointer;margin:10px 0;">
                        📂 Paths Testados ({len(r['paths'])})</summary>
                    <ul style="background:#0f1420;padding:12px 12px 12px 30px;
                    border-radius:8px;font-size:.85em;margin:0;">
                        {paths_list}
                    </ul>
                </details>"""

            source_html = ""
            if r.get("source_code"):
                source_html = f"""
                <details>
                    <summary style="color:#4fc3f7;cursor:pointer;margin:10px 0;">
                        📄 Código-Fonte HTML</summary>
                    <pre style="background:#0f1420;padding:12px;border-radius:8px;
                    overflow-x:auto;font-size:.75em;max-height:400px;">
{htmllib.escape(r['source_code'][:50000])}</pre>
                </details>"""

            corpo = f"""
            <div class="top">
              <span class="badge ok">HTTP {r['status']}</span>
              <span class="mini">IP: {htmllib.escape(r['ip'])} ·
              Tamanho: {r['size']} bytes ·
              Tempo: {r.get('response_time', 0)}s ·
              MD5: <code>{r['hash_md5']}</code></span>
            </div>
            {redirect}
            <div class="titulo-pagina">
                {htmllib.escape(r['title'] or '(sem título)')}</div>
            <table>{techs}</table>
            {headers_html}
            {paths_html}
            {links_html}
            {urls_html}
            {source_html}
            """
        cards.append(f"""
        <div class="card">
          <div class="url">{htmllib.escape(r['url'])}</div>
          {corpo}
        </div>""")

    html_doc = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatório WebFinger — {agora}</title>
<style>
  *{{box-sizing:border-box;}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f1420;
  color:#e6e9f0;margin:0;padding:30px;}}
  h1{{color:#4fc3f7;margin-top:0;}}
  .sub{{color:#8a93a6;margin-bottom:25px;}}
  .card{{background:#1a2233;border:1px solid #2a3550;border-radius:12px;
  padding:18px 22px;margin-bottom:18px;box-shadow:0 4px 14px rgba(0,0,0,.35);}}
  .url{{font-size:1.15em;font-weight:bold;color:#7ee787;
  word-break:break-all;margin-bottom:10px;}}
  .top{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;
  margin-bottom:6px;}}
  .badge{{padding:3px 10px;border-radius:20px;font-size:.8em;font-weight:bold;}}
  .ok{{background:#1d3a2a;color:#7ee787;}}
  .mini{{color:#8a93a6;font-size:.85em;word-break:break-all;}}
  .titulo-pagina{{color:#c9d3e8;margin:8px 0;font-style:italic;}}
  table{{width:100%;border-collapse:collapse;margin-top:10px;}}
  td{{padding:7px 10px;border-bottom:1px solid #2a3550;font-size:.92em;}}
  td.tname{{color:#4fc3f7;font-weight:600;width:280px;word-break:break-all;}}
  .nenhum{{color:#8a93a6;font-style:italic;text-align:center;}}
  .erro{{color:#ff6b6b;}}
  code{{background:#0f1420;padding:2px 6px;border-radius:4px;font-size:.85em;}}
  pre{{color:#c9d3e8;white-space:pre-wrap;word-break:break-all;}}
</style></head><body>
<h1>🔍 Relatório WebFinger</h1>
<div class="sub">Gerado em {agora} — {len(resultados)} alvos analisados</div>
{''.join(cards)}
</body></html>"""

    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(html_doc)


# ═══════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA COM SELETOR DE TEMAS
# ═══════════════════════════════════════════════════════════════

class App:
    def __init__(self, root):
        self.root = root
        root.title("WebFinger")
        root.geometry("980x740")
        root.minsize(780, 560)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        self.style = ttk.Style()

        # Detecta temas disponíveis no sistema
        self.temas_disponiveis = sorted(self.style.theme_names())
        self.tema_atual = tk.StringVar(value="clam")

        # Esquema de cores atual
        self.cores = TEMAS_CORES["escuro"].copy()

        # Coletar todos os widgets que precisam de recoloração
        self._widgets_recolorir = []
        self._labels_info = []

        self._construir_interface()
        self._aplicar_tema("clam")

    # ───────────────────────────────────────────────────
    #  CONSTRUÇÃO DA INTERFACE
    # ───────────────────────────────────────────────────

    def _construir_interface(self):
        root = self.root

        # === BARRA SUPERIOR: Tema + URL + Botão ===
        top_bar = tk.Frame(root)
        top_bar.pack(fill="x", padx=15, pady=(15, 5))
        self._widgets_recolorir.append(("frame", top_bar))

        # Seletor de tema
        tk.Label(top_bar, text="🎨 Tema:", font=("Segoe UI", 9, "bold")
                 ).pack(side="left", padx=(0, 5))
        self.lbl_tema = top_bar.winfo_children()[-1]
        self._widgets_recolorir.append(("label", self.lbl_tema))

        self.combo_tema = ttk.Combobox(
            top_bar, textvariable=self.tema_atual,
            values=self.temas_disponiveis, state="readonly",
            width=12, font=("Segoe UI", 9),
        )
        self.combo_tema.pack(side="left", padx=(0, 20))
        self.combo_tema.bind("<<ComboboxSelected>>", self._on_tema_changed)

        # Separador visual
        sep_lbl = tk.Label(top_bar, text="│", font=("Segoe UI", 12))
        sep_lbl.pack(side="left", padx=(0, 10))
        self._widgets_recolorir.append(("label", sep_lbl))

        # URL
        lbl_url = tk.Label(
            top_bar, text="🌐 URL:", font=("Segoe UI", 10, "bold"))
        lbl_url.pack(side="left", padx=(0, 10))
        self._widgets_recolorir.append(("label", lbl_url))

        self.entry_url = tk.Entry(
            top_bar, relief="flat", font=("Consolas", 11))
        self.entry_url.pack(side="left", fill="x", expand=True,
                            padx=(0, 10), ipady=4)
        self.entry_url.insert(0, "https://example.com")
        self.entry_url.bind("<Return>", lambda e: self.iniciar())
        self._widgets_recolorir.append(("entry", self.entry_url))

        self.btn_scan = tk.Button(
            top_bar, text="🔍 Analisar", command=self.iniciar,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=16, cursor="hand2",
        )
        self.btn_scan.pack(side="right")
        self._widgets_recolorir.append(("btn_primary", self.btn_scan))

        # === BARRA DE PROGRESSO ===
        prog_frame = tk.Frame(root)
        prog_frame.pack(fill="x", padx=15, pady=(0, 5))
        self._widgets_recolorir.append(("frame", prog_frame))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            prog_frame, mode="determinate",
            variable=self.progress_var, maximum=100,
        )
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_percent = tk.Label(
            prog_frame, text="0%", font=("Segoe UI", 9, "bold"), width=5)
        self.lbl_percent.pack(side="right")
        self._widgets_recolorir.append(("label_accent", self.lbl_percent))

        self.lbl_step = tk.Label(
            root, text="", font=("Segoe UI", 8), anchor="w")
        self.lbl_step.pack(fill="x", padx=15)
        self._widgets_recolorir.append(("label_muted", self.lbl_step))

        # === NOTEBOOK (ABAS) ===
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # --- Aba 1: Info ---
        tab_info = tk.Frame(self.notebook)
        self.notebook.add(tab_info, text=" ℹ️ Info ")
        self._widgets_recolorir.append(("frame", tab_info))

        info_inner = tk.Frame(tab_info, padx=15, pady=15)
        info_inner.pack(fill="both", expand=True, padx=5, pady=5)
        self._widgets_recolorir.append(("frame_card", info_inner))

        self.lbl_ip = self._campo(info_inner, "Endereço IP:", 0)
        self.lbl_status = self._campo(info_inner, "Status HTTP:", 1)
        self.lbl_title = self._campo(info_inner, "Título do Site:", 2)
        self.lbl_size = self._campo(info_inner, "Tamanho:", 3)
        self.lbl_time = self._campo(info_inner, "Tempo de Resposta:", 4)
        self.lbl_redirect = self._campo(info_inner, "Redirecionamento:", 5)
        self.lbl_hash = self._campo(info_inner, "MD5 do Body:", 6)
        self.lbl_dns = self._campo(info_inner, "DNS Reverso:", 7)
        self.lbl_all_ips = self._campo(info_inner, "Todos os IP:", 8)

        # --- Aba 2: Tecnologias ---
        tab_techs = tk.Frame(self.notebook)
        self.notebook.add(tab_techs, text=" 🛠️ Tecnologias ")
        self._widgets_recolorir.append(("frame", tab_techs))

        tree_frame = tk.Frame(tab_techs)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._widgets_recolorir.append(("frame", tree_frame))

        self.tree = ttk.Treeview(
            tree_frame, columns=("idx", "componente", "detalhe"),
            show="headings", selectmode="browse",
        )
        self.tree.heading("idx", text="#")
        self.tree.heading("componente", text="Componente / Tecnologia")
        self.tree.heading("detalhe", text="Detalhe / Assinatura")
        self.tree.column("idx", width=40, anchor="center", stretch=False)
        self.tree.column("componente", width=320, anchor="w")
        self.tree.column("detalhe", width=480, anchor="w")
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # --- Aba 3: Cabeçalhos ---
        tab_headers = tk.Frame(self.notebook)
        self.notebook.add(tab_headers, text=" 📋 Cabeçalhos ")
        self._widgets_recolorir.append(("frame", tab_headers))

        self.txt_headers = tk.Text(
            tab_headers, relief="flat", font=("Consolas", 10), wrap="word")
        sbh = ttk.Scrollbar(
            tab_headers, orient="vertical", command=self.txt_headers.yview)
        self.txt_headers.configure(yscrollcommand=sbh.set)
        self.txt_headers.pack(
            side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        sbh.pack(side="right", fill="y", pady=5, padx=(0, 5))
        self._widgets_recolorir.append(("text", self.txt_headers))

        # --- Aba 4: Paths ---
        tab_paths = tk.Frame(self.notebook)
        self.notebook.add(tab_paths, text=" 📂 Paths ")
        self._widgets_recolorir.append(("frame", tab_paths))

        pf = tk.Frame(tab_paths)
        pf.pack(fill="both", expand=True, padx=5, pady=5)
        self._widgets_recolorir.append(("frame", pf))

        self.tree_paths = ttk.Treeview(
            pf, columns=("url", "label", "status"),
            show="headings", selectmode="browse",
        )
        self.tree_paths.heading("url", text="URL Completa")
        self.tree_paths.heading("label", text="Descrição")
        self.tree_paths.heading("status", text="Status")
        self.tree_paths.column("url", width=420, anchor="w")
        self.tree_paths.column("label", width=200, anchor="w")
        self.tree_paths.column("status", width=220, anchor="w")
        sbp = ttk.Scrollbar(
            pf, orient="vertical", command=self.tree_paths.yview)
        self.tree_paths.configure(yscrollcommand=sbp.set)
        self.tree_paths.pack(side="left", fill="both", expand=True)
        sbp.pack(side="right", fill="y")

        # --- Aba 5: Links <a> ---
        tab_links = tk.Frame(self.notebook)
        self.notebook.add(tab_links, text=" 🔗 Links <a> ")
        self._widgets_recolorir.append(("frame", tab_links))

        lf = tk.Frame(tab_links)
        lf.pack(fill="both", expand=True, padx=5, pady=5)
        self._widgets_recolorir.append(("frame", lf))

        self.tree_links = ttk.Treeview(
            lf, columns=("tipo", "url"),
            show="headings", selectmode="browse",
        )
        self.tree_links.heading("tipo", text="Tipo")
        self.tree_links.heading("url", text="URL / Link <a href>")
        self.tree_links.column("tipo", width=100, anchor="center", stretch=False)
        self.tree_links.column("url", width=700, anchor="w")
        sbl = ttk.Scrollbar(
            lf, orient="vertical", command=self.tree_links.yview)
        self.tree_links.configure(yscrollcommand=sbl.set)
        self.tree_links.pack(side="left", fill="both", expand=True)
        sbl.pack(side="right", fill="y")

        # --- Aba 6: URLs no Código ---
        tab_urls = tk.Frame(self.notebook)
        self.notebook.add(tab_urls, text=" 🌐 URLs no Código ")
        self._widgets_recolorir.append(("frame", tab_urls))

        filter_frame = tk.Frame(tab_urls)
        filter_frame.pack(fill="x", padx=5, pady=(5, 0))
        self._widgets_recolorir.append(("frame", filter_frame))

        lbl_filtrar = tk.Label(
            filter_frame, text="Filtrar:", font=("Segoe UI", 8))
        lbl_filtrar.pack(side="left", padx=(0, 6))
        self._widgets_recolorir.append(("label_muted", lbl_filtrar))

        self.url_filter = tk.StringVar(value="Todas")
        self._radio_buttons = []
        for texto in ("Todas", "HTTPS", "HTTP", "Interno", "Externo"):
            rb = tk.Radiobutton(
                filter_frame, text=texto, variable=self.url_filter,
                value=texto, command=self._aplicar_filtro_urls,
                font=("Segoe UI", 8),
            )
            rb.pack(side="left", padx=4)
            self._radio_buttons.append(rb)
            self._widgets_recolorir.append(("radio", rb))

        btn_copiar_urls = tk.Button(
            filter_frame, text="📋 Copiar todas",
            command=self.copiar_urls, relief="flat",
            padx=8, cursor="hand2", font=("Segoe UI", 8),
        )
        btn_copiar_urls.pack(side="right", padx=4)
        self._widgets_recolorir.append(("btn_secondary", btn_copiar_urls))

        uf = tk.Frame(tab_urls)
        uf.pack(fill="both", expand=True, padx=5, pady=5)
        self._widgets_recolorir.append(("frame", uf))

        self.tree_urls = ttk.Treeview(
            uf, columns=("esquema", "origem", "recurso", "url"),
            show="headings", selectmode="browse",
        )
        self.tree_urls.heading("esquema", text="HTTP/S")
        self.tree_urls.heading("origem", text="Origem")
        self.tree_urls.heading("recurso", text="Tipo")
        self.tree_urls.heading("url", text="URL Completa (extraída do código-fonte)")
        self.tree_urls.column("esquema", width=70, anchor="center", stretch=False)
        self.tree_urls.column("origem", width=80, anchor="center", stretch=False)
        self.tree_urls.column("recurso", width=100, anchor="center", stretch=False)
        self.tree_urls.column("url", width=620, anchor="w")
        sbu = ttk.Scrollbar(
            uf, orient="vertical", command=self.tree_urls.yview)
        self.tree_urls.configure(yscrollcommand=sbu.set)
        self.tree_urls.pack(side="left", fill="both", expand=True)
        sbu.pack(side="right", fill="y")

        # --- Aba 7: Código-Fonte ---
        tab_source = tk.Frame(self.notebook)
        self.notebook.add(tab_source, text=" 📄 Código-Fonte ")
        self._widgets_recolorir.append(("frame", tab_source))

        src_top = tk.Frame(tab_source)
        src_top.pack(fill="x", padx=5, pady=(5, 0))
        self._widgets_recolorir.append(("frame", src_top))

        btn_copiar_src = tk.Button(
            src_top, text="📋 Copiar Código", command=self.copiar_fonte,
            relief="flat", padx=10, cursor="hand2",
        )
        btn_copiar_src.pack(side="left")
        self._widgets_recolorir.append(("btn_secondary", btn_copiar_src))

        btn_salvar_src = tk.Button(
            src_top, text="💾 Salvar .html", command=self.salvar_fonte,
            relief="flat", padx=10, cursor="hand2",
        )
        btn_salvar_src.pack(side="left", padx=8)
        self._widgets_recolorir.append(("btn_secondary", btn_salvar_src))

        self.lbl_src_info = tk.Label(
            src_top, text="", font=("Segoe UI", 8))
        self.lbl_src_info.pack(side="right")
        self._widgets_recolorir.append(("label_muted", self.lbl_src_info))

        self.txt_source = tk.Text(
            tab_source, relief="flat", font=("Consolas", 9), wrap="none")
        ssy = ttk.Scrollbar(
            tab_source, orient="vertical", command=self.txt_source.yview)
        ssx = ttk.Scrollbar(
            tab_source, orient="horizontal", command=self.txt_source.xview)
        self.txt_source.configure(yscrollcommand=ssy.set, xscrollcommand=ssx.set)
        ssx.pack(side="bottom", fill="x", padx=5)
        self.txt_source.pack(
            side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        ssy.pack(side="right", fill="y", pady=5, padx=(0, 5))
        self._widgets_recolorir.append(("text", self.txt_source))

        # === RODAPÉ ===
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill="x", padx=15, pady=(0, 15))
        self._widgets_recolorir.append(("frame", bottom_frame))

        self.status = tk.Label(
            bottom_frame, text="Pronto. Digite um site e clique em Analisar.",
            anchor="w", font=("Segoe UI", 9),
        )
        self.status.pack(side="left", fill="x", expand=True)
        self._widgets_recolorir.append(("label_muted", self.status))

        self.btn_save = tk.Button(
            bottom_frame, text="💾 Exportar HTML",
            command=self.salvar, font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, cursor="hand2",
        )
        self.btn_save.pack(side="right")
        self._widgets_recolorir.append(("btn_save", self.btn_save))

        self.resultados = []
        self.scanning = False
        self._source_code = ""
        self._all_urls = []

    # ───────────────────────────────────────────────────
    #  SISTEMA DE TEMAS
    # ───────────────────────────────────────────────────

    def _on_tema_changed(self, event=None):
        tema = self.tema_atual.get()
        self._aplicar_tema(tema)

    def _aplicar_tema(self, tema_ttk):
        """Aplica tema ttk + esquema de cores correspondente."""
        try:
            self.style.theme_use(tema_ttk)
        except Exception:
            self.style.theme_use("clam")
            tema_ttk = "clam"

        # Escolhe esquema de cores
        esquema = TEMA_PARA_ESQUEMA.get(tema_ttk, "escuro")
        self.cores = TEMAS_CORES[esquema].copy()
        c = self.cores

        # Configura root
        self.root.configure(bg=c["bg_principal"])

        # Configura estilos ttk
        self.style.configure(
            "Treeview",
            background=c["bg_tree"],
            fieldbackground=c["bg_tree"],
            foreground=c["fg_tree"],
            rowheight=24, borderwidth=0,
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Treeview.Heading",
            background=c["bg_heading"],
            foreground=c["fg_heading"],
            font=("Segoe UI", 9, "bold"), borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[("selected", c["bg_tree_sel"])],
        )

        # Progressbar
        pbar_style = "custom.Horizontal.TProgressbar"
        self.style.configure(
            pbar_style,
            troughcolor=c["bg_progress"],
            background=c["fg_progress"],
            darkcolor=c["fg_progress"],
            lightcolor=c["fg_progress"],
            bordercolor=c["bg_progress"],
            thickness=18,
        )
        self.progress.configure(style=pbar_style)

        # Tags das Treeviews
        self.tree_paths.tag_configure("ok", foreground=c["fg_sucesso"])
        self.tree_paths.tag_configure("forbid", foreground=c["fg_aviso"])
        self.tree_paths.tag_configure("auth", foreground=c["fg_titulo"])
        self.tree_paths.tag_configure("redir", foreground=c["fg_code"])
        self.tree_links.tag_configure("interno", foreground=c["fg_sucesso"])
        self.tree_links.tag_configure("externo", foreground=c["fg_titulo"])
        self.tree_urls.tag_configure("https", foreground=c["fg_sucesso"])
        self.tree_urls.tag_configure("http", foreground=c["fg_aviso"])

        # Recolorir todos os widgets registrados
        for tipo, widget in self._widgets_recolorir:
            try:
                if tipo == "frame":
                    widget.configure(bg=c["bg_principal"])
                elif tipo == "frame_card":
                    widget.configure(bg=c["bg_card"])
                elif tipo == "label":
                    widget.configure(bg=c["bg_principal"], fg=c["fg_texto"])
                elif tipo == "label_accent":
                    widget.configure(bg=c["bg_principal"], fg=c["fg_titulo"])
                elif tipo == "label_muted":
                    widget.configure(bg=c["bg_principal"], fg=c["fg_muted"])
                elif tipo == "label_info":
                    widget.configure(bg=c["bg_card"], fg=c["fg_texto"])
                elif tipo == "label_info_title":
                    widget.configure(bg=c["bg_card"], fg=c["fg_muted"])
                elif tipo == "entry":
                    widget.configure(
                        bg=c["bg_input"], fg=c["fg_texto"],
                        insertbackground=c["fg_texto"],
                    )
                elif tipo == "text":
                    widget.configure(
                        bg=c["bg_card"], fg=c["fg_code"],
                        insertbackground=c["fg_texto"],
                    )
                elif tipo == "btn_primary":
                    widget.configure(bg=c["bg_botao"], fg=c["fg_botao"])
                elif tipo == "btn_secondary":
                    widget.configure(bg=c["bg_botao2"], fg=c["fg_botao2"])
                elif tipo == "btn_save":
                    widget.configure(bg=c["bg_salvar"], fg=c["fg_salvar"])
                elif tipo == "radio":
                    widget.configure(
                        bg=c["bg_principal"], fg=c["fg_texto"],
                        selectcolor=c["bg_card"],
                        activebackground=c["bg_principal"],
                        activeforeground=c["fg_titulo"],
                    )
            except Exception:
                pass

        # Recolorir labels de info (aba Info)
        for tipo, widget in self._labels_info:
            try:
                if tipo == "title":
                    widget.configure(bg=c["bg_card"], fg=c["fg_muted"])
                elif tipo == "value":
                    widget.configure(bg=c["bg_card"], fg=c["fg_texto"])
            except Exception:
                pass

        # Recolorir tag de header nos cabeçalhos
        try:
            self.txt_headers.tag_configure(
                "header_name",
                foreground=c["fg_titulo"],
                font=("Consolas", 10, "bold"),
            )
        except Exception:
            pass

        self.root.update_idletasks()

    # ───────────────────────────────────────────────────
    #  HELPERS
    # ───────────────────────────────────────────────────

    def _campo(self, parent, label, row):
        lbl_title = tk.Label(
            parent, text=label, font=("Segoe UI", 9, "bold"), anchor="w")
        lbl_title.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
        self._labels_info.append(("title", lbl_title))

        lbl_value = tk.Label(
            parent, text="-", font=("Segoe UI", 9), anchor="w",
            wraplength=550, justify="left",
        )
        lbl_value.grid(row=row, column=1, sticky="w", pady=3)
        parent.columnconfigure(1, weight=1)
        self._labels_info.append(("value", lbl_value))
        return lbl_value

    def log(self, msg):
        self.status.config(text=msg)

    def update_progress(self, step, total, msg=""):
        pct = min(100, int((step / total) * 100))
        self.progress_var.set(pct)
        self.lbl_percent.config(text=f"{pct}%")
        if msg:
            self.lbl_step.config(text=f"  {msg}")
        self.root.update_idletasks()

    # ───────────────────────────────────────────────────
    #  SCAN
    # ───────────────────────────────────────────────────

    def iniciar(self):
        if self.scanning:
            return
        alvo = normalize_url(self.entry_url.get())
        if not alvo:
            messagebox.showwarning("Aviso", "Por favor, digite a URL de um site.")
            return

        self.scanning = True
        self.progress_var.set(0)
        self.lbl_percent.config(text="0%")
        self.lbl_step.config(text="  Iniciando análise...")
        self.log(f"Escaneando {alvo}...")

        c = self.cores
        for lbl in [
            self.lbl_ip, self.lbl_status, self.lbl_title, self.lbl_size,
            self.lbl_time, self.lbl_redirect, self.lbl_hash, self.lbl_dns,
            self.lbl_all_ips,
        ]:
            lbl.config(text="-", fg=c["fg_texto"])
        for tree in (self.tree, self.tree_links, self.tree_paths, self.tree_urls):
            for row in tree.get_children():
                tree.delete(row)
        self.txt_headers.delete("1.0", "end")
        self.txt_source.delete("1.0", "end")
        self.lbl_src_info.config(text="")
        self._source_code = ""
        self._all_urls = []

        threading.Thread(target=self._rodar, args=(alvo,), daemon=True).start()

    def _progress_cb(self, step, total, msg):
        self.root.after(0, self.update_progress, step, total, msg)

    def _rodar(self, alvo):
        self.resultados = []
        try:
            res = scan_target(alvo, progress_callback=self._progress_cb)
            self.resultados.append(res)
        except Exception as e:
            self.resultados.append({
                "url": alvo, "ip": "N/D", "erro": str(e), "techs": [],
                "status": None, "title": "", "hash_md5": "", "size": 0,
                "redirect": "", "headers": {}, "raw_headers": "",
                "dns_info": {}, "response_time": 0, "links": [],
                "source_code": "", "paths": [], "urls_codigo": [],
            })
        self.root.after(0, self._fim)

    def _popular_urls(self, lista):
        for row in self.tree_urls.get_children():
            self.tree_urls.delete(row)
        for esquema, origem, recurso, url_u in lista:
            tag = "https" if esquema == "HTTPS" else "http"
            self.tree_urls.insert(
                "", "end",
                values=(esquema, origem, recurso, url_u), tags=(tag,),
            )

    def _aplicar_filtro_urls(self):
        f = self.url_filter.get()
        if f == "Todas":
            filtrada = self._all_urls
        elif f in ("HTTPS", "HTTP"):
            filtrada = [u for u in self._all_urls if u[0] == f]
        elif f in ("Interno", "Externo"):
            filtrada = [u for u in self._all_urls if u[1] == f]
        else:
            filtrada = self._all_urls
        self._popular_urls(filtrada)
        self.notebook.tab(5, text=f" 🌐 URLs no Código ({len(filtrada)}) ")

    def _fim(self):
        self.scanning = False
        self.progress_var.set(100)
        self.lbl_percent.config(text="100%")
        self.lbl_step.config(text="  ✅ Análise finalizada!")
        c = self.cores

        if not self.resultados:
            self.log("Nenhum resultado retornado.")
            return

        res = self.resultados[0]

        if res.get("erro"):
            self.lbl_ip.config(text="N/D")
            self.lbl_status.config(text="Erro", fg=c["fg_erro"])
            self.lbl_title.config(text="Erro de conexão", fg=c["fg_erro"])
            self.tree.insert(
                "", "end",
                values=("!", "Falha ao carregar site", res["erro"]),
            )
            self.log("Falha na análise. Verifique a URL ou sua conexão.")
            return

        # Info
        self.lbl_ip.config(text=res.get("ip", "N/D"), fg=c["fg_sucesso"])
        status = res.get("status", "N/D")
        s_str = str(status)
        cor = (
            c["fg_sucesso"] if s_str.startswith("2")
            else c["fg_aviso"] if s_str.startswith("3")
            else c["fg_erro"]
        )
        self.lbl_status.config(text=s_str, fg=cor)
        titulo = res.get("title")
        self.lbl_title.config(
            text=titulo[:100] if titulo else "(Sem título)",
            fg=c["fg_texto"],
        )
        self.lbl_size.config(
            text=f"{res.get('size', 0):,} bytes".replace(",", "."),
            fg=c["fg_texto"],
        )
        self.lbl_time.config(
            text=f"{res.get('response_time', 0)} segundos",
            fg=c["fg_texto"],
        )
        redir = res.get("redirect")
        self.lbl_redirect.config(
            text=redir if redir else "Não", fg=c["fg_texto"])
        self.lbl_hash.config(
            text=res.get("hash_md5", "N/D"), fg=c["fg_muted"])
        dns = res.get("dns_info", {})
        self.lbl_dns.config(
            text=dns.get("reverso", "N/D"), fg=c["fg_texto"])
        self.lbl_all_ips.config(
            text=dns.get("todos_ips", "N/D"), fg=c["fg_texto"])

        # Cabeçalhos
        raw = res.get("raw_headers", "")
        if raw:
            self.txt_headers.insert("1.0", raw)
            self.txt_headers.tag_configure(
                "header_name",
                foreground=c["fg_titulo"],
                font=("Consolas", 10, "bold"),
            )
            for i, line in enumerate(raw.split("\n"), 1):
                if ":" in line:
                    self.txt_headers.tag_add(
                        "header_name",
                        f"{i}.0", f"{i}.{line.index(':')}",
                    )

        # Tecnologias
        techs = res.get("techs", [])
        for idx, (nome, ver) in enumerate(techs, 1):
            self.tree.insert("", "end", values=(idx, nome, ver))
        if not techs:
            self.tree.insert(
                "", "end",
                values=("-", "Nenhuma", "Nenhuma assinatura identificada."),
            )

        # Paths
        paths = res.get("paths", [])
        for full_url, label, status_txt in paths:
            if "200" in status_txt:
                tag = "ok"
            elif "403" in status_txt:
                tag = "forbid"
            elif "401" in status_txt:
                tag = "auth"
            else:
                tag = "redir"
            self.tree_paths.insert(
                "", "end",
                values=(full_url, label, status_txt), tags=(tag,),
            )
        if not paths:
            self.tree_paths.insert(
                "", "end",
                values=("-", "Nenhum path encontrado", "-"),
            )
        self.notebook.tab(3, text=f" 📂 Paths ({len(paths)}) ")

        # Links <a>
        links = res.get("links", [])
        for tipo, url_link in links:
            tag = "interno" if tipo == "Interno" else "externo"
            self.tree_links.insert(
                "", "end", values=(tipo, url_link), tags=(tag,))
        if not links:
            self.tree_links.insert(
                "", "end",
                values=("-", "Nenhum link <a> encontrado."),
            )
        self.notebook.tab(4, text=f" 🔗 Links <a> ({len(links)}) ")

        # URLs do código-fonte
        urls = res.get("urls_codigo", [])
        self._all_urls = urls
        self.url_filter.set("Todas")
        self._popular_urls(urls)
        if not urls:
            self.tree_urls.insert(
                "", "end",
                values=("-", "-", "-",
                        "Nenhuma URL http/https encontrada no código."),
            )
        self.notebook.tab(5, text=f" 🌐 URLs no Código ({len(urls)}) ")

        # Código-fonte
        src = res.get("source_code", "")
        self._source_code = src
        if src:
            self.txt_source.insert("1.0", src)
            linhas = src.count("\n") + 1
            self.lbl_src_info.config(
                text=(
                    f"{len(src):,} chars · {linhas} linhas · "
                    f"{res.get('url', '')}"
                ).replace(",", "."),
            )
        self.notebook.tab(
            6,
            text=f" 📄 Código-Fonte ({len(src):,} B) ".replace(",", "."),
        )

        self.log(
            f"✅ {len(techs)} techs · {len(paths)} paths · "
            f"{len(links)} links · {len(urls)} URLs no código"
        )
        self.notebook.select(1)

    # ───────────────────────────────────────────────────
    #  AÇÕES
    # ───────────────────────────────────────────────────

    def copiar_urls(self):
        if not self._all_urls:
            messagebox.showinfo("Info", "Nenhuma URL para copiar.")
            return
        f = self.url_filter.get()
        if f == "Todas":
            lista = self._all_urls
        elif f in ("HTTPS", "HTTP"):
            lista = [u for u in self._all_urls if u[0] == f]
        elif f in ("Interno", "Externo"):
            lista = [u for u in self._all_urls if u[1] == f]
        else:
            lista = self._all_urls
        texto = "\n".join(u[3] for u in lista)
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.log(
            f"📋 {len(lista)} URLs copiadas para a área de transferência!")

    def copiar_fonte(self):
        if not self._source_code:
            messagebox.showinfo("Info", "Nenhum código-fonte carregado.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._source_code)
        self.log("📋 Código-fonte copiado!")

    def salvar_fonte(self):
        if not self._source_code:
            messagebox.showinfo("Info", "Nenhum código-fonte carregado.")
            return
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML", "*.html"), ("Texto", "*.txt"), ("Todos", "*.*")
            ],
            initialfile="codigo_fonte.html",
        )
        if not arquivo:
            return
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(self._source_code)
        self.log(f"💾 Código-fonte salvo em {arquivo}")

    def salvar(self):
        if not self.resultados:
            messagebox.showinfo(
                "Info", "Execute uma análise antes de salvar o relatório.")
            return
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("Relatório HTML", "*.html")],
            initialfile="relatorio_webfinger.html",
        )
        if not arquivo:
            return
        gerar_html(self.resultados, arquivo)
        self.log(f"Relatório salvo em {arquivo}")
        if messagebox.askyesno(
            "Abrir relatório", "Relatório salvo. Abrir no navegador?"
        ):
            webbrowser.open("file://" + arquivo)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
