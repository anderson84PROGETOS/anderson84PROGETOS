#!/usr/bin/env python3
"""
WHOIS + CNPJ + OSINT Extractor - Unified Toolkit
=================================================
Combina:
  • WHOIS com tradução PT-BR e cores
  • CNPJ Avançado (ReceitaWS) com exportação HTML
  • Histórico WHOIS (Whoxy)
  • Informações de URL
  • OSINT CNPJ Extractor (varredura de site + geolocalização + exportação HTML)
"""

import socket
import re
import requests
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import webbrowser
import os
import json
import threading
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup

# ==================== ESTILO ====================
class HackerStyle:
    BG = "#0a0a0a"
    FG = "#00ff41"
    ACCENT = "#00ff41"
    RED = "#ff0033"
    GRAY = "#1a1a1a"
    FONT = ("Consolas", 11)
    FONT_BOLD = ("Consolas", 12, "bold")
    TITLE_FONT = ("Consolas", 18, "bold")


# ==================== CONSTANTES OSINT ====================
TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 "
    "(KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53"
)
HEADERS = {"User-Agent": USER_AGENT}


# ==================== TRADUÇÃO WHOIS ====================
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
    "nsstat:": "Status DNS",
    "nslastaa:": "Última consulta DNS",
}


def formatar_data_brasileira(texto):
    """
    Converte qualquer formato ISO ou YYYYMMDD para DD/MM/AAAA HH:MM:SS
    Ex: 2026-07-27T18:57:49.710Z -> 27/07/2026 18:57:49
    Ex: 19950201 -> 01/02/1995 00:00:00
    """
    formatos = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y%m%d",
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(texto.strip(), formato)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            pass

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


# ==================== CONSULTA WHOIS ====================
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

            # ===== CORREÇÃO: captura YYYY-MM-DD (com ou sem timestamp) E YYYYMMDD =====
            linha = re.sub(
                r"\d{4}-\d{2}-\d{2}(T[\d:.Z]+)?",
                lambda m: formatar_data_brasileira(m.group()),
                linha
            )
            linha = re.sub(
                r"\b(\d{8})\b",
                lambda m: formatar_data_brasileira(m.group()),
                linha
            )

            linha_traduzida = traduzir_linha(linha)
            saida_formatada.append(linha_traduzida)

        return "\n".join(saida_formatada)

    except Exception as e:
        return f"[-] Erro na consulta: {e}"


# ==================== CNPJ (ORIGINAL) ====================
def limpar_cnpj(cnpj):
    return ''.join(filter(str.isdigit, str(cnpj)))


def consultar_cnpj_original(cnpj):
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        return None
    try:
        r = requests.get(f"https://www.receitaws.com.br/v1/cnpj/{cnpj}", timeout=12)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def calcular_idade(data_abertura):
    try:
        hoje = datetime.now()
        data = None
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y%m%d"]:
            try:
                data = datetime.strptime(data_abertura.strip(), fmt)
                break
            except:
                continue
        if not data:
            return "Data inválida"
        diferenca = hoje - data
        anos = diferenca.days // 365
        meses = (diferenca.days % 365) // 30
        dias = (diferenca.days % 365) % 30
        return f"{anos} anos, {meses} meses e {dias} dias"
    except:
        return "Data inválida"


def abrir_google_maps(logradouro, numero, municipio, uf):
    endereco = f"{logradouro}, {numero}, {municipio}, {uf}"
    webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}")


def gerar_texto(dados_cnpj):
    logradouro = dados_cnpj.get('logradouro', 'Não encontrado')
    numero = dados_cnpj.get('numero', 'Não encontrado')
    municipio = dados_cnpj.get('municipio', 'Não encontrado')
    uf = dados_cnpj.get('uf', 'Não encontrado')

    ultima_atualizacao = formatar_data_brasileira(dados_cnpj.get('ultima_atualizacao', 'Não encontrado'))
    abertura = dados_cnpj.get('abertura', 'Não encontrado')
    data_situacao = formatar_data_brasileira(dados_cnpj.get('data_situacao', 'Não encontrado'))

    message = f"""
CNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}

RAZÃO SOCIAL: {dados_cnpj.get('nome', 'Não encontrado')}

MATRIZ OU FILIAL: {dados_cnpj.get('tipo', 'Não encontrado')}

NOME FANTASIA: {dados_cnpj.get('fantasia', 'Não encontrado')}

SITUAÇÃO CADASTRAL: {dados_cnpj.get('situacao', 'Não encontrado')}

DATA DA SITUAÇÃO CADASTRAL: {data_situacao}

MOTIVO DA SITUAÇÃO CADASTRAL: {dados_cnpj.get('motivo_situacao', 'Não encontrado')}

NATUREZA JURÍDICA: {dados_cnpj.get('natureza_juridica', 'Não encontrado')}

DATA DE ABERTURA: {abertura}

IDADE: {calcular_idade(abertura) if abertura != 'Não encontrado' else 'Não encontrado'}

PORTE (RFB): {dados_cnpj.get('porte', 'Não encontrado')}

CAPITAL SOCIAL: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}

ATUALIZAÇÃO DESTA PÁGINA: {ultima_atualizacao}



LOCALIZAÇÃO
===========

ENDEREÇO: {logradouro} | Número: {numero}

COMPLEMENTO: {dados_cnpj.get('complemento', 'Não encontrado')}

BAIRRO: {dados_cnpj.get('bairro', 'Não encontrado')}

CIDADE | ESTADO: {municipio} | {uf}

CEP: {dados_cnpj.get('cep', 'Não encontrado')}

TELEFONES: {dados_cnpj.get('telefone', 'Não encontrado')}

E-MAILS: {dados_cnpj.get('email', 'Não encontrado')}



ATIVIDADE ECONÔMICA PRINCIPAL
==============================

CÓDIGO: {dados_cnpj.get('atividade_principal', [{}])[0].get('code', 'Não encontrado')}
DESCRIÇÃO: {dados_cnpj.get('atividade_principal', [{}])[0].get('text', 'Não encontrado')}


ATIVIDADES ECONÔMICAS SECUNDÁRIAS
=================================
"""
    if 'atividades_secundarias' in dados_cnpj and dados_cnpj['atividades_secundarias']:
        for atividade in dados_cnpj['atividades_secundarias']:
            message += f"CÓDIGO: {atividade['code']} | DESCRIÇÃO: {atividade['text']}\n"
    else:
        message += "Não encontrado\n"

    message += "\n\nQUADRO DE SÓCIOS E ADMINISTRADORES (QSA)\n==========================================\n"
    if 'qsa' in dados_cnpj and dados_cnpj['qsa']:
        for socio in dados_cnpj['qsa']:
            data_entrada = socio.get('data_entrada')
            message += f"NOME: {socio.get('nome', 'Não encontrado')}\n"
            message += f"QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}\n"
            if data_entrada:
                try:
                    data_entrada_fmt = formatar_data_brasileira(data_entrada)
                    message += f"ENTRADA: {data_entrada_fmt}\n"
                except:
                    message += "ENTRADA: Data inválida\n"
            message += "-" * 50 + "\n"
    else:
        message += "Não encontrado\n"

    return message


# ==================== SALVAR HTML (CNPJ) ====================
def salvar_html_cnpj(dados_cnpj):
    if not dados_cnpj:
        messagebox.showerror("Erro", "Nenhum dado de CNPJ para salvar. Faça uma consulta primeiro.")
        return

    cnpj = dados_cnpj.get('cnpj', 'desconhecido').replace('/', '_').replace('.', '_').replace('-', '_')
    filename = filedialog.asksaveasfilename(
        title="Salvar CNPJ como HTML",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile=f"consulta_cnpj_{cnpj}.html"
    )
    if not filename:
        return

    try:
        html_content = gerar_html_cnpj(dados_cnpj)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        messagebox.showinfo("Sucesso", f"CNPJ salvo em HTML\n\n{filename}")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Não foi possível salvar: {str(e)}")


def gerar_html_cnpj(dados_cnpj):
    socio_html = ""
    if 'qsa' in dados_cnpj and dados_cnpj['qsa']:
        for socio in dados_cnpj['qsa']:
            data_entrada = socio.get('data_entrada')
            socio_html += f"""<div class="socio">
                <p><strong>NOME:</strong> {socio.get('nome', 'Não encontrado')}</p>
                <p><strong>QUALIFICAÇÃO:</strong> {socio.get('qual', 'Não encontrado')}</p>"""
            if data_entrada:
                try:
                    data_entrada_fmt = formatar_data_brasileira(data_entrada)
                    socio_html += f"<p><strong>ENTRADA:</strong> {data_entrada_fmt}</p>"
                except:
                    socio_html += "<p><strong>ENTRADA:</strong> Data inválida</p>"
            socio_html += "</div><hr>"
    else:
        socio_html = "<p>Não encontrado</p>"

    ativ_sec_html = ""
    if 'atividades_secundarias' in dados_cnpj and dados_cnpj['atividades_secundarias']:
        for atividade in dados_cnpj['atividades_secundarias']:
            ativ_sec_html += f"<p><b>CÓDIGO:</b> {atividade['code']} | <b>DESCRIÇÃO:</b> {atividade['text']}</p>\n"
    else:
        ativ_sec_html = "<p>Não encontrado</p>"

    ultima_atualizacao = formatar_data_brasileira(dados_cnpj.get('ultima_atualizacao', 'Não encontrado'))
    data_situacao = formatar_data_brasileira(dados_cnpj.get('data_situacao', 'Não encontrado'))
    abertura = dados_cnpj.get('abertura', 'Não encontrado')

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Consulta CNPJ - {dados_cnpj.get('cnpj', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0a;
            color: #00ff41;
            padding: 40px 20px;
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{ text-align: center; color: #00ff80; font-size: 28px; margin-bottom: 30px; border-bottom: 2px solid #00ff41; padding-bottom: 15px; }}
        h2 {{ color: #00ff80; margin: 25px 0 10px 0; font-size: 20px; border-left: 4px solid #00ff41; padding-left: 10px; }}
        p {{ margin: 8px 0; font-size: 14px; line-height: 1.6; }}
        .socio {{ background: #111; padding: 12px; border-radius: 4px; margin: 8px 0; }}
        hr {{ border: 0; border-top: 1px solid #00ff41; opacity: 0.3; margin: 5px 0; }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #008800; }}
    </style>
</head>
<body>
    <h1>🔍 CONSULTA CNPJ</h1>

    <h2>Informações Gerais</h2>
    <p><b>CNPJ:</b> {dados_cnpj.get('cnpj', 'Não encontrado')}</p>
    <p><b>RAZÃO SOCIAL:</b> {dados_cnpj.get('nome', 'Não encontrado')}</p>
    <p><b>MATRIZ OU FILIAL:</b> {dados_cnpj.get('tipo', 'Não encontrado')}</p>
    <p><b>NOME FANTASIA:</b> {dados_cnpj.get('fantasia', 'Não encontrado')}</p>
    <p><b>SITUAÇÃO CADASTRAL:</b> {dados_cnpj.get('situacao', 'Não encontrado')}</p>
    <p><b>DATA DA SITUAÇÃO CADASTRAL:</b> {data_situacao}</p>
    <p><b>MOTIVO DA SITUAÇÃO CADASTRAL:</b> {dados_cnpj.get('motivo_situacao', 'Não encontrado')}</p>
    <p><b>NATUREZA JURÍDICA:</b> {dados_cnpj.get('natureza_juridica', 'Não encontrado')}</p>
    <p><b>DATA DE ABERTURA:</b> {abertura}</p>
    <p><b>IDADE:</b> {calcular_idade(abertura) if abertura != 'Não encontrado' else 'Não encontrado'}</p>
    <p><b>PORTE (RFB):</b> {dados_cnpj.get('porte', 'Não encontrado')}</p>
    <p><b>CAPITAL SOCIAL:</b> R$ {dados_cnpj.get('capital_social', 'Não encontrado')}</p>
    <p><b>ATUALIZAÇÃO:</b> {ultima_atualizacao}</p>

    <h2>Localização</h2>
    <p><b>ENDEREÇO:</b> {dados_cnpj.get('logradouro', 'Não encontrado')} | Número: {dados_cnpj.get('numero', 'Não encontrado')}</p>
    <p><b>COMPLEMENTO:</b> {dados_cnpj.get('complemento', 'Não encontrado')}</p>
    <p><b>BAIRRO:</b> {dados_cnpj.get('bairro', 'Não encontrado')}</p>
    <p><b>CIDADE | ESTADO:</b> {dados_cnpj.get('municipio', 'Não encontrado')} | {dados_cnpj.get('uf', 'Não encontrado')}</p>
    <p><b>CEP:</b> {dados_cnpj.get('cep', 'Não encontrado')}</p>
    <p><b>TELEFONES:</b> {dados_cnpj.get('telefone', 'Não encontrado')}</p>
    <p><b>E-MAILS:</b> {dados_cnpj.get('email', 'Não encontrado')}</p>

    <h2>Atividade Econômica Principal</h2>
    <p><b>CÓDIGO:</b> {dados_cnpj.get('atividade_principal', [{}])[0].get('code', 'Não encontrado')}</p>
    <p><b>DESCRIÇÃO:</b> {dados_cnpj.get('atividade_principal', [{}])[0].get('text', 'Não encontrado')}</p>

    <h2>Atividades Econômicas Secundárias</h2>
    {ativ_sec_html}

    <h2>Quadro de Sócios e Administradores (QSA)</h2>
    {socio_html}

    <div class="footer">
        WHOIS • Consulta Segura • Informações de Registro Público + CNPJ Avançado<br><br><br>
        Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</body>
</html>"""


# ==================== SALVAR HTML (WHOIS) ====================
def salvar_html_whois():
    conteudo = text_whois.get(1.0, tk.END).strip()
    if not conteudo or conteudo == "":
        messagebox.showerror("Erro", "Nenhum resultado WHOIS para salvar. Faça uma consulta primeiro.")
        return

    filename = filedialog.asksaveasfilename(
        title="Salvar WHOIS como HTML",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile="whois_resultado.html"
    )
    if not filename:
        return

    try:
        alvo = "desconhecido"
        for linha in conteudo.splitlines():
            if "WHOIS →" in linha:
                alvo = linha.split("→")[-1].strip()
                break

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>WHOIS - {alvo}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Consolas', 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff41;
            padding: 40px 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{ text-align: center; color: #00ff80; font-size: 26px; margin-bottom: 30px; border-bottom: 2px solid #00ff41; padding-bottom: 15px; }}
        pre {{
            background: #111;
            padding: 20px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #00ff41;
        }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #008800; }}
    </style>
</head>
<body>
    <h1>🔍 WHOIS — {alvo}</h1>
    <pre>{conteudo}</pre>
    <div class="footer">
        WHOIS • Consulta Segura • Informações de Registro Público<br><br>
        Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        messagebox.showinfo("Sucesso", f"WHOIS salvo em HTML\n\n{filename}")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Não foi possível salvar: {str(e)}")


# ==================== ABRIR ARQUIVO ====================
def abrir_arquivo():
    caminho = filedialog.askopenfilename(
        title="Abrir arquivo salvo",
        filetypes=[
            ("HTML", "*.html *.htm"),
            ("Todos os arquivos", "*.*")
        ]
    )
    if not caminho:
        return

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()

        widget = text_cnpj
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, f"--- ARQUIVO ABERTO: {os.path.basename(caminho)} ---\n\n")
        widget.insert(tk.END, conteudo)
        widget.config(state=tk.DISABLED)

        messagebox.showinfo("Sucesso", f"Arquivo aberto com sucesso!\n\n{os.path.basename(caminho)}")

    except Exception as e:
        messagebox.showerror("Erro ao abrir arquivo", f"Erro: {str(e)}")


# ==================== CONSULTAR URL ====================
def consultar_url_info(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        r = requests.get(url, timeout=10, allow_redirects=True)
        titulo = re.search(r'<title>(.*?)</title>', r.text, re.I | re.DOTALL)
        return f"""

STATUS: {r.status_code}

URL FINAL: {r.url}

TÍTULO: {titulo.group(1).strip() if titulo else 'Não encontrado'}

SERVIDOR: {r.headers.get('Server', 'N/A')}

ENCODING: {r.encoding}
        """.strip()
    except Exception as e:
        return f"Erro ao acessar URL: {e}"


# ==================== BUSCAR TUDO (ORIGINAL) ====================
def buscar_tudo():
    alvo = entry.get().strip()
    if not alvo:
        messagebox.showerror("Erro", "Digite um alvo!")
        return

    # ===================== WHOIS COM CORES E DATAS CONVERTIDAS =====================
    text_whois.config(state=tk.NORMAL)
    text_whois.delete(1.0, tk.END)
    resultado = consultar_whois(alvo)

    for linha in resultado.splitlines():
        if ":" in linha:
            campo, valor = linha.split(":", 1)
            campo_lower = campo.lower()

            text_whois.insert("end", campo + ": ")

            if any(x in campo_lower for x in ["domínio", "domain"]):
                text_whois.insert("end", valor + "\n", "dominio")
            elif "pessoa" in campo_lower:
                text_whois.insert("end", valor + "\n", "pessoa")
            elif any(x in campo_lower for x in ["entidade", "owner", "registrante", "responsável", "person", "organização"]):
                text_whois.insert("end", valor + "\n", "entidade")
            elif any(x in campo_lower for x in ["cnpj", "ownerid"]):
                text_whois.insert("end", valor + "\n", "cnpj")
            elif any(x in campo_lower for x in ["email", "e-mail", "abuse-mailbox"]):
                text_whois.insert("end", valor + "\n", "email")
            elif any(x in campo_lower for x in ["servidor dns", "servidores dns", "nameserver", "nserver", "dnssec"]):
                text_whois.insert("end", valor + "\n", "dns")
            elif any(x in campo_lower for x in ["criado em", "alterado em", "expira em", "atualizado em", "creation date", "updated date", "registry expiry", "nsstat", "nslastaa"]):
                text_whois.insert("end", valor + "\n", "data")
            elif any(x in campo_lower for x in ["status", "status do domínio", "domain status"]):
                text_whois.insert("end", valor + "\n", "status")
            elif any(x in campo_lower for x in ["endereço", "cidade", "estado", "cep", "país", "address", "country"]):
                text_whois.insert("end", valor + "\n", "endereco")
            else:
                text_whois.insert("end", valor + "\n")
        else:
            if "WHOIS" in linha or linha.startswith("=") or linha.startswith("-"):
                text_whois.insert("end", linha + "\n", "header")
            else:
                text_whois.insert("end", linha + "\n")
    text_whois.config(state=tk.DISABLED)

    # Histórico
    text_hist.config(state=tk.NORMAL)
    text_hist.delete(1.0, tk.END)
    text_hist.insert(tk.END, f"HISTÓRICO WHOIS\n\nPara ver o histórico completo acesse\n\nhttps://www.whoxy.com/{alvo}")
    text_hist.config(state=tk.DISABLED)

    # CNPJ
    text_cnpj.config(state=tk.NORMAL)
    text_cnpj.delete(1.0, tk.END)
    if len(limpar_cnpj(alvo)) == 14:
        dados = consultar_cnpj_original(alvo)
        if dados:
            text_cnpj.insert(tk.END, gerar_texto(dados))
            maps_btn.config(state=tk.NORMAL, command=lambda d=dados: abrir_google_maps(
                d.get('logradouro', ''), d.get('numero', ''),
                d.get('municipio', ''), d.get('uf', '')
            ))
            salvar_cnpj_btn.config(state=tk.NORMAL, command=lambda d=dados: salvar_html_cnpj(d))
        else:
            text_cnpj.insert(tk.END, "CNPJ não encontrado ou API indisponível.")
            maps_btn.config(state=tk.DISABLED)
            salvar_cnpj_btn.config(state=tk.DISABLED)
    else:
        text_cnpj.insert(tk.END, "Digite um CNPJ válido (14 dígitos).")
        maps_btn.config(state=tk.DISABLED)
        salvar_cnpj_btn.config(state=tk.DISABLED)
    text_cnpj.config(state=tk.DISABLED)

    # URL
    text_url.config(state=tk.NORMAL)
    text_url.delete(1.0, tk.END)
    text_url.insert(tk.END, consultar_url_info(alvo))
    text_url.config(state=tk.DISABLED)


# ==================== CONSULTAR CNPJ VIA BOTÃO ====================
def consultar_e_mostrar():
    cnpj = limpar_cnpj(cnpj_entry.get())
    if not cnpj:
        messagebox.showerror("Erro", "Por favor, insira um CNPJ válido")
        return

    dados_cnpj = consultar_cnpj_original(cnpj)
    text_cnpj.config(state=tk.NORMAL)
    text_cnpj.delete(1.0, tk.END)

    if dados_cnpj:
        message = gerar_texto(dados_cnpj)
        text_cnpj.insert(tk.END, message)

        maps_btn.config(state=tk.NORMAL, command=lambda: abrir_google_maps(
            dados_cnpj.get('logradouro', ''),
            dados_cnpj.get('numero', ''),
            dados_cnpj.get('municipio', ''),
            dados_cnpj.get('uf', '')
        ))
        salvar_cnpj_btn.config(state=tk.NORMAL, command=lambda d=dados_cnpj: salvar_html_cnpj(d))
    else:
        text_cnpj.insert(tk.END, "CNPJ não encontrado ou API indisponível.")
        maps_btn.config(state=tk.DISABLED)
        salvar_cnpj_btn.config(state=tk.DISABLED)

    text_cnpj.config(state=tk.DISABLED)


# ====================================================================
# FUNÇÕES OSINT (NOVA ABA)
# ====================================================================

def osint_normalizar_dominio(entrada: str) -> str:
    """Remove protocolo, barras, espaços e retorna só o domínio."""
    entrada = entrada.strip().lower()
    if not entrada.startswith(("http://", "https://")):
        entrada = "https://" + entrada
    parsed = urlparse(entrada)
    return parsed.netloc or parsed.path.split("/")[0]


def osint_extrair_cnpj_do_html(html: str) -> list:
    """Procura padrões de CNPJ (xx.xxx.xxx/xxxx-xx) no HTML."""
    padrao = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
    return re.findall(padrao, html)


def osint_extrair_emails_do_html(html: str) -> list:
    """Procura e-mails no HTML."""
    padrao = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ignorar = {"example.com", "domain.com", "email.com", "test.com", "@yoursite.com"}
    emails = set()
    for m in re.finditer(padrao, html):
        email = m.group().strip().lower()
        if not any(ig in email for ig in ignorar):
            emails.add(email)
    return list(emails)


def osint_extrair_numero_logradouro(logradouro: str, numero_api: str = "") -> tuple:
    """
    Extrai o número do logradouro.
    - Se numero_api já veio preenchido, usa ele.
    - Se não, tenta extrair do texto do logradouro.
    Retorna (rua_sem_numero, numero_encontrado)
    """
    if numero_api and numero_api.strip():
        return logradouro.strip(), numero_api.strip()

    if not logradouro:
        return "", ""

    logradouro = logradouro.strip()

    # Tenta "RUA ABC, 123"
    padrao = re.match(r"^(.*?),\s*(\d[\d\s]*[A-Za-z]?)\s*$", logradouro)
    if padrao:
        return padrao.group(1).strip(), padrao.group(2).strip()

    # Tenta "RUA ABC 123" (sem vírgula)
    padrao2 = re.match(r"^(.*?)\s+(\d[\d\s]*[A-Za-z]?)\s*$", logradouro)
    if padrao2:
        return padrao2.group(1).strip(), padrao2.group(2).strip()

    # Não encontrou número
    return logradouro, ""


def osint_consultar_receita_ws(cnpj: str) -> dict:
    """Consulta CNPJ na API pública da ReceitaWS."""
    cnpj_limpo = re.sub(r"\D", "", cnpj)
    url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            dados = resp.json()
            if dados.get("status") == "OK":
                return {
                    "cnpj": dados.get("cnpj", ""),
                    "razao_social": dados.get("nome", ""),
                    "fantasia": dados.get("fantasia", ""),
                    "email": dados.get("email", ""),
                    "telefone": dados.get("telefone", ""),
                    "situacao": dados.get("situacao", ""),
                    "logradouro": dados.get("logradouro", ""),
                    "numero": dados.get("numero", ""),
                    "complemento": dados.get("complemento", ""),
                    "bairro": dados.get("bairro", ""),
                    "municipio": dados.get("municipio", ""),
                    "uf": dados.get("uf", ""),
                    "cep": dados.get("cep", ""),
                }
        if resp.status_code == 429:
            return {"erro": "Rate limit da ReceitaWS (1 req/min por IP)"}
    except Exception as e:
        return {"erro": f"Erro na consulta ReceitaWS: {e}"}
    return {"erro": "CNPJ não encontrado na ReceitaWS"}


def osint_consultar_cnpja(cnpj: str) -> dict:
    """Consulta alternativa via CNPJá (gratuito, sem chave)."""
    cnpj_limpo = re.sub(r"\D", "", cnpj)
    url = f"https://www.cnpja.com.br/api/{cnpj_limpo}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            dados = resp.json()
            return {
                "cnpj": dados.get("cnpj", dados.get("documento", "")),
                "razao_social": dados.get("razao_social", dados.get("nome", "")),
                "fantasia": dados.get("fantasia", ""),
                "email": dados.get("email", ""),
                "situacao": dados.get("situacao_cadastral", dados.get("status", "")),
            }
    except Exception:
        pass
    return None


def osint_geocode_address(logradouro: str, numero: str, bairro: str, municipio: str, uf: str, cep: str = "") -> dict:
    """
    Geocodifica o endereço usando Nominatim (OpenStreetMap).
    Retorna dict com lat, lon, query_usada e os componentes do endereço original.
    """
    headers_nominatim = {
        "User-Agent": "OSINT_CNPJ_Extractor/1.0 (contato@ferramenta.br)"
    }

    queries_tentar = []

    # 1. Tenta com número + bairro
    if logradouro and numero and bairro:
        queries_tentar.append(f"{logradouro}, {numero} - {bairro}, {municipio}, {uf}, Brasil")
        queries_tentar.append(f"{logradouro} {numero}, {bairro}, {municipio}, {uf}, Brasil")

    # 2. Tenta com número, sem bairro
    if logradouro and numero:
        queries_tentar.append(f"{logradouro}, {numero}, {municipio}, {uf}, Brasil")
        queries_tentar.append(f"{logradouro} {numero}, {municipio}, {uf}, Brasil")

    # 3. Tenta sem número
    if logradouro:
        queries_tentar.append(f"{logradouro}, {municipio}, {uf}, Brasil")

    # 4. Tenta com CEP
    if cep:
        queries_tentar.append(f"{cep}, Brasil")

    for query in queries_tentar:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        try:
            resp = requests.get(url, params=params, headers=headers_nominatim, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return {
                        "lat": data[0]["lat"],
                        "lon": data[0]["lon"],
                        "query_usada": query,
                    }
        except Exception:
            continue
        threading.Event().wait(1.1)

    return None


def osint_extrair_dados_do_site(dominio: str) -> dict:
    """Acessa o site e extrai CNPJ, e-mails e outras infos."""
    resultado = {
        "dominio": dominio,
        "url_acessada": None,
        "cnpjs_encontrados": [],
        "emails_encontrados": [],
        "possivel_razao": None,
        "erros": [],
    }

    for protocolo in ["https://", "http://"]:
        url = f"{protocolo}{dominio}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            resultado["url_acessada"] = resp.url
            html = resp.text

            cnpjs = osint_extrair_cnpj_do_html(html)
            resultado["cnpjs_encontrados"] = list(set(cnpjs))

            emails = osint_extrair_emails_do_html(html)
            resultado["emails_encontrados"] = list(set(emails))

            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.string:
                resultado["possivel_razao"] = soup.title.string.strip()

            for meta in soup.find_all("meta"):
                if meta.get("property") in ("og:site_name", "og:title"):
                    if meta.get("content"):
                        resultado["possivel_razao"] = meta["content"].strip()
                        break

            if resultado["cnpjs_encontrados"]:
                break

        except requests.exceptions.RequestException as e:
            resultado["erros"].append(f"{protocolo}: {e}")
            continue

    if not resultado["url_acessada"]:
        resultado["erros"].append("Nenhum protocolo respondeu")

    return resultado


def osint_whois_consulta(dominio: str) -> dict:
    """Consulta WHOIS via whoisxmlapi (free tier)."""
    info = {}
    try:
        resp = requests.get(
            f"https://www.whoisxmlapi.com/whoisserver/WhoisService"
            f"?domainName={dominio}&outputFormat=JSON&apiKey=at_free",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                whois_data = (
                    data.get("WhoisRecord", {})
                    .get("registrant", {})
                    .get("organization", "")
                )
                if whois_data:
                    info["organizacao_whois"] = whois_data
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return info


# Variáveis globais da aba OSINT
osint_geo_data = None


def osint_log(texto, cor="#00ff41"):
    """Insere texto formatado no ScrolledText da aba OSINT."""
    text_osint.insert(tk.END, texto + "\n")
    text_osint.see(tk.END)
    root.update_idletasks()


def osint_abrir_google_maps():
    """Abre o Google Maps com busca por endereço (OSINT)."""
    global osint_geo_data
    if osint_geo_data:
        logradouro = osint_geo_data.get("logradouro", "")
        numero = osint_geo_data.get("numero", "")
        municipio = osint_geo_data.get("municipio", "")
        uf = osint_geo_data.get("uf", "")

        endereco = f"{logradouro}, {numero}, {municipio}, {uf}"
        url = f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}"

        webbrowser.open(url)
        osint_log(f"  → Google Maps aberto: {url}")
    else:
        messagebox.showinfo(
            "Geolocalização",
            "Nenhuma coordenada disponível. Execute uma busca primeiro.",
        )


def osint_salvar_html():
    """Salva o conteúdo da aba OSINT Extractor em HTML."""
    conteudo = text_osint.get(1.0, tk.END).strip()
    if not conteudo or conteudo == "":
        messagebox.showerror("Erro", "Nenhum resultado OSINT para salvar. Faça uma consulta primeiro.")
        return

    filename = filedialog.asksaveasfilename(
        title="Salvar OSINT como HTML",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile="osint_resultado.html"
    )
    if not filename:
        return

    try:
        alvo = "desconhecido"
        for linha in conteudo.splitlines():
            if "📌 ALVO:" in linha:
                alvo = linha.split("ALVO:")[-1].strip()
                break

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OSINT Extractor - {alvo}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Consolas', 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff41;
            padding: 40px 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{ text-align: center; color: #00ff80; font-size: 26px; margin-bottom: 30px; border-bottom: 2px solid #00ff41; padding-bottom: 15px; }}
        pre {{
            background: #111;
            padding: 20px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #00ff41;
        }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #008800; }}
    </style>
</head>
<body>
    <h1>🔍 OSINT Extractor — {alvo}</h1>
    <pre>{conteudo}</pre>
    <div class="footer">
        OSINT Extractor • Consulta Segura • Informações de Registro Público<br><br>
        Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        messagebox.showinfo("Sucesso", f"OSINT salvo em HTML\n\n{filename}")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Não foi possível salvar: {str(e)}")


def osint_iniciar_busca():
    threading.Thread(target=osint_buscar, daemon=True).start()


def osint_buscar():
    """Executa a busca OSINT completa em thread separada."""
    global osint_geo_data

    dominio_raw = osint_entry.get().strip()
    if not dominio_raw:
        messagebox.showwarning("Aviso", "Digite um domínio ou URL.")
        return

    # Desabilitar botões durante a busca
    osint_btn_buscar.config(state=tk.DISABLED)
    osint_btn_maps.config(state=tk.DISABLED)
    osint_btn_salvar.config(state=tk.DISABLED)
    osint_geo_data = None
    osint_lbl_geo.config(text="")

    osint_progress.start()
    osint_lbl_status.config(text=f"🔍 Buscando informações de {dominio_raw}...")
    text_osint.config(state=tk.NORMAL)
    text_osint.delete(1.0, tk.END)

    dados_cnpj = {"erro": "Nenhum CNPJ encontrado"}

    try:
        dominio = osint_normalizar_dominio(dominio_raw)
        osint_log(f"{'='*70}")
        osint_log(f"📌 ALVO: {dominio}")
        osint_log(f"{'='*70}")
        osint_log("")

        # ── ETAPA 1: Extrair dados do site ──
        osint_log("[1/4] Varrendo o site em busca de CNPJ e e-mails\n")
        site_data = osint_extrair_dados_do_site(dominio)

        if site_data["url_acessada"]:
            osint_log(f"    ✔ Site acessado: {site_data['url_acessada']}\n")
        if site_data["erros"]:
            for err in site_data["erros"]:
                osint_log(f"    ⚠ {err}")

        if site_data["possivel_razao"]:
            osint_log(f"    ℹ Possível Razão Social (title): {site_data['possivel_razao']}")

        if site_data["cnpjs_encontrados"]:
            osint_log(f"\n    ✅ CNPJ Encontrados no HTML: {', '.join(site_data['cnpjs_encontrados'])}")
        else:
            osint_log("\n    ❌ Nenhum CNPJ encontrado no HTML do site.")

        if site_data["emails_encontrados"]:
            osint_log(f"\n    📧 E-mails Encontrados: {', '.join(site_data['emails_encontrados'][:8])}")
            if len(site_data["emails_encontrados"]) > 8:
                osint_log(f"    ... e mais {len(site_data['emails_encontrados'])-8} e-mails.")

        osint_log("")

        # ── ETAPA 2: Consultar CNPJ nas APIs ──
        cnpj_para_consultar = None
        if site_data["cnpjs_encontrados"]:
            cnpj_para_consultar = site_data["cnpjs_encontrados"][0]
            osint_log(f"[2/4] Consultando CNPJ {cnpj_para_consultar}\n")
            dados_cnpj = osint_consultar_receita_ws(cnpj_para_consultar)

            if "erro" not in dados_cnpj:
                osint_log(f"    ✅ CNPJ: {dados_cnpj.get('cnpj', 'N/A')}")
                osint_log(f"    🏢 Razão Social: {dados_cnpj.get('razao_social', 'N/A')}")
                osint_log(f"    🏪 Fantasia: {dados_cnpj.get('fantasia', 'N/A')}")
                osint_log(f"    📧 E-mail: {dados_cnpj.get('email', 'N/A')}")
                osint_log(f"    📞 Telefone: {dados_cnpj.get('telefone', 'N/A')}")

                # ── Endereço ──
                logradouro = dados_cnpj.get("logradouro", "")
                numero_api = dados_cnpj.get("numero", "")
                bairro = dados_cnpj.get("bairro", "")
                municipio = dados_cnpj.get("municipio", "")
                uf = dados_cnpj.get("uf", "")
                cep = dados_cnpj.get("cep", "")

                rua_formatada, numero_final = osint_extrair_numero_logradouro(logradouro, numero_api)

                endereco_linha = f"{rua_formatada.upper()}, {municipio.upper()} - {uf.upper()}"
                if numero_final:
                    endereco_linha += f"   Número: {numero_final}"
                if bairro:
                    endereco_linha += f"   Bairro: {bairro.upper()}"

                osint_log(f"    📍 Endereço: {endereco_linha}")
                osint_log(f"    📊 Situação: {dados_cnpj.get('situacao', 'N/A')}")

                # ── Geolocalização ──
                osint_log(f"\n    🔍 Obtendo geolocalização\n")
                geo = osint_geocode_address(rua_formatada, numero_final, bairro, municipio, uf, cep)
                if geo:
                    osint_log(f"    🌐 Geolocalização: {geo['lat']}, {geo['lon']}\n")
                    osint_log(f"    🗺️ Query usada: {geo.get('query_usada', 'N/A')}\n")

                    osint_geo_data = {
                        "lat": geo["lat"],
                        "lon": geo["lon"],
                        "logradouro": rua_formatada,
                        "numero": numero_final,
                        "bairro": bairro,
                        "municipio": municipio,
                        "uf": uf,
                        "cep": cep,
                    }

                    endereco_url = f"{rua_formatada}, {numero_final}, {municipio}, {uf}"
                    maps_search_url = f"https://www.google.com/maps/search/?api=1&query={endereco_url.replace(' ', '+')}"
                    osint_log(f"    🔗 Google Maps: {maps_search_url}")

                    osint_btn_maps.config(state=tk.NORMAL)
                    osint_lbl_geo.config(text=f"📍 {geo['lat']}, {geo['lon']}")
                else:
                    osint_log("    ⚠ Geolocalização não disponível para este endereço")
            else:
                osint_log(f"    ⚠ ReceitaWS: {dados_cnpj['erro']}")
                osint_log("    🔄 Tentando API alternativa (CNPJá)...")
                alt = osint_consultar_cnpja(cnpj_para_consultar)
                if alt and "erro" not in alt:
                    osint_log(f"    ✅ CNPJá -> Razão: {alt.get('razao_social', 'N/A')}")
                    osint_log(f"    ✅ CNPJá -> E-mail: {alt.get('email', 'N/A')}")
                else:
                    osint_log("    ❌ APIs públicas não retornaram dados completos.")
        else:
            osint_log("[2/4] Nenhum CNPJ encontrado no site para consultar nas APIs.")

        osint_log("")

        # ── ETAPA 3: WHOIS ──
        osint_log("[3/4] Consultando WHOIS\n")
        whois_data = osint_whois_consulta(dominio)
        if whois_data.get("organizacao_whois"):
            osint_log(f"    ℹ Organização (WHOIS): {whois_data['organizacao_whois']}")
        else:
            osint_log("    ℹ WHOIS sem organização pública (ou uso de serviço de privacidade)")

        osint_log("")

        # ── ETAPA 4: Resumo Final ──
        osint_log(f"{'='*70}")
        osint_log("📋 RESUMO FINAL")
        osint_log(f"{'='*70}")

        razao_final = ""
        email_final = ""

        if "erro" not in dados_cnpj:
            razao_final = dados_cnpj.get("razao_social", "")
            email_final = dados_cnpj.get("email", "")
        if not email_final and site_data["emails_encontrados"]:
            email_final = site_data["emails_encontrados"][0]

        if cnpj_para_consultar:
            osint_log(f"   CNPJ: {cnpj_para_consultar}")
        if razao_final:
            osint_log(f"   Razão Social: {razao_final}")
        else:
            osint_log(f"   Razão Social: {site_data.get('possivel_razao', 'Não encontrada')}")
        if email_final:
            osint_log(f"   E-mail: {email_final}\n")
        elif site_data["emails_encontrados"]:
            osint_log(f"   E-mails: {', '.join(site_data['emails_encontrados'][:5])}")
        else:
            osint_log("   E-mail: Não encontrado")

        # Resumo da geolocalização
        if osint_geo_data:
            endereco_url = (
                f"{osint_geo_data['logradouro']}, "
                f"{osint_geo_data['numero']}, "
                f"{osint_geo_data['municipio']}, "
                f"{osint_geo_data['uf']}"
            )
            maps_url_resumo = (
                f"https://www.google.com/maps/search/?api=1"
                f"&query={endereco_url.replace(' ', '+')}"
            )
            osint_log(f"   🌐 Google Maps: {maps_url_resumo}")

        osint_log("")
        osint_log("\n✅ Busca concluída\n")
        if osint_geo_data:
            osint_log("💡 Clique no botão 'Abrir no Google Maps' para visualizar no mapa.")

        # Reabilita o botão de salvar após busca bem-sucedida
        osint_btn_salvar.config(state=tk.NORMAL)

    except Exception as e:
        osint_log(f"❌ Erro inesperado: {e}")

    finally:
        osint_progress.stop()
        osint_btn_buscar.config(state=tk.NORMAL)
        osint_lbl_status.config(text="✅ Busca concluída.")
        text_osint.config(state=tk.DISABLED)


# ==================== INTERFACE ====================
root = tk.Tk()
root.title("🔍 WHOIS + CNPJ + OSINT Extractor 🔎")
root.geometry("1200x850")
root.state('zoomed')
root.configure(bg="#0a0a0a")

# Frame Superior
top_frame = tk.Frame(root, bg="#0a0a0a")
top_frame.pack(fill="x", padx=10, pady=10)

tk.Label(top_frame, text="Digite o Domínio", bg="#0a0a0a", fg="#00ff41",
         font=("Consolas", 12, "bold")).pack(side=tk.LEFT, pady=5)

entry = tk.Entry(top_frame, font=("Consolas", 14), width=55, bg="#049e2b", fg="#000000")
entry.pack(side=tk.LEFT, padx=10, pady=5)

tk.Button(top_frame, text="🔍 BUSCAR WHOIS 🔎", font=("Consolas", 12, "bold"),
          bg="#001a00", fg="#00ff41", command=buscar_tudo).pack(side=tk.LEFT, padx=8, pady=10)

# Notebook
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=5)

aba_whois = ttk.Frame(notebook)
aba_hist = ttk.Frame(notebook)
aba_cnpj = ttk.Frame(notebook)
aba_url = ttk.Frame(notebook)
aba_osint = ttk.Frame(notebook)

notebook.add(aba_whois, text="WHOIS Atual")
notebook.add(aba_cnpj, text="CNPJ Avançado")
notebook.add(aba_osint, text="OSINT Extractor")
notebook.add(aba_hist, text="Histórico WHOIS")
notebook.add(aba_url, text="Informações URL")


# ===================== ABA CNPJ AVANÇADA =====================
cnpj_frame = tk.Frame(aba_cnpj, bg="#0a0a0a")
cnpj_frame.pack(fill="x", padx=10, pady=8)

tk.Label(cnpj_frame, text="CNPJ:", bg="#0a0a0a", fg="#00ff41", font=("Consolas", 12, "bold")).pack(side=tk.LEFT)

cnpj_entry = tk.Entry(cnpj_frame, font=("Consolas", 14), width=30, bg="#05A038", fg="#0a0a0a")
cnpj_entry.pack(side=tk.LEFT, padx=8)

btn_consultar = tk.Button(cnpj_frame, text="🔍 CONSULTAR CNPJ", font=("Consolas", 11, "bold"),
                          bg="#00ff41", fg="black", command=consultar_e_mostrar)
btn_consultar.pack(side=tk.LEFT, padx=5)

maps_btn = tk.Button(cnpj_frame, text="🗺️ GOOGLE MAPS", font=("Consolas", 11, "bold"),
                     bg="#00FFFF", fg="black", state=tk.DISABLED, width=18)
maps_btn.pack(side=tk.LEFT, padx=5)

salvar_cnpj_btn = tk.Button(cnpj_frame, text="💾 SALVAR HTML", font=("Consolas", 11, "bold"),
                            bg="#FF4500", fg="black", state=tk.DISABLED, width=18)
salvar_cnpj_btn.pack(side=tk.LEFT, padx=5)

btn_abrir = tk.Button(cnpj_frame, text="📂 ABRIR HTML", command=abrir_arquivo,
                      font=HackerStyle.FONT_BOLD, bg="#00ff41", fg="black", width=18)
btn_abrir.pack(side=tk.LEFT, padx=8)

# ===================== ABA OSINT EXTRACTOR =====================
osint_frame_top = tk.Frame(aba_osint, bg="#0a0a0a")
osint_frame_top.pack(fill="x", padx=10, pady=8)

tk.Label(osint_frame_top, text="Domínio:", bg="#0a0a0a", fg="#00ff41",
         font=("Consolas", 12, "bold")).pack(side=tk.LEFT)

osint_entry = tk.Entry(osint_frame_top, font=("Consolas", 14), width=45,
                        bg="#05A038", fg="#0a0a0a")
osint_entry.pack(side=tk.LEFT, padx=8)
osint_entry.insert(0, "")

osint_btn_buscar = tk.Button(osint_frame_top, text="🔎 BUSCAR OSINT",
                              font=("Consolas", 11, "bold"),
                              bg="#00ff41", fg="black", command=osint_iniciar_busca)
osint_btn_buscar.pack(side=tk.LEFT, padx=5)

osint_btn_maps = tk.Button(osint_frame_top, text="🌍 GOOGLE MAPS",
                            font=("Consolas", 11, "bold"),
                            bg="#00FFFF", fg="black", state=tk.DISABLED,
                            command=osint_abrir_google_maps, width=18)
osint_btn_maps.pack(side=tk.LEFT, padx=5)

# Botão SALVAR HTML na aba OSINT
osint_btn_salvar = tk.Button(osint_frame_top, text="💾 SALVAR HTML",
                              font=("Consolas", 11, "bold"),
                              bg="#FF4500", fg="black", state=tk.DISABLED,
                              command=osint_salvar_html, width=18)
osint_btn_salvar.pack(side=tk.LEFT, padx=5)

osint_lbl_geo = tk.Label(osint_frame_top, text="", bg="#0a0a0a", fg="#888888",
                          font=("Consolas", 9))
osint_lbl_geo.pack(side=tk.LEFT, padx=5)

# Progresso e status
osint_progress = ttk.Progressbar(aba_osint, mode="indeterminate")
osint_progress.pack(fill="x", padx=10, pady=(0, 5))

osint_lbl_status = tk.Label(aba_osint, text="Pronto.", bg="#0a0a0a", fg="#008800",
                             font=("Consolas", 9))
osint_lbl_status.pack(anchor=tk.W, padx=12, pady=(0, 5))

# Área de texto OSINT
text_osint = ScrolledText(aba_osint, font=("Consolas", 10), bg="#000000",
                           fg="#00ff41", wrap=tk.WORD, state=tk.NORMAL)
text_osint.pack(fill="both", expand=True, padx=5, pady=5)

# Enter também dispara busca na aba OSINT
osint_entry.bind("<Return>", lambda e: osint_iniciar_busca())

# ===================== BOTÃO SALVAR WHOIS =====================
whois_btn_frame = tk.Frame(aba_whois, bg="#0a0a0a")
whois_btn_frame.pack(fill="x", padx=5, pady=5)

btn_salvar_whois = tk.Button(whois_btn_frame, text="💾 SALVAR WHOIS EM HTML",
                             font=("Consolas", 11, "bold"), bg="#FF4500", fg="black",
                             command=salvar_html_whois)
btn_salvar_whois.pack(side=tk.RIGHT, padx=5)

# ===================== TEXT AREAS ORIGINAIS =====================
text_whois = ScrolledText(aba_whois, font=("Consolas", 11), bg="#000000", fg="#00ff41", wrap=tk.WORD)
text_whois.pack(fill="both", expand=True, padx=5, pady=5)

text_hist = ScrolledText(aba_hist, font=("Consolas", 11), bg="#000000", fg="#00ff41", wrap=tk.WORD)
text_hist.pack(fill="both", expand=True, padx=5, pady=5)

text_cnpj = ScrolledText(aba_cnpj, font=("Consolas", 11), bg="#000000", fg="#00ff41", wrap=tk.WORD)
text_cnpj.pack(fill="both", expand=True, padx=5, pady=5)

text_url = ScrolledText(aba_url, font=("Consolas", 11), bg="#000000", fg="#00ff41", wrap=tk.WORD)
text_url.pack(fill="both", expand=True, padx=5, pady=5)

# ===================== TAGS DE CORES =====================
tag_configs = {
    "header": ("#00FF80", ("Consolas", 13, "bold")),
    "cnpj": ("#F7F5F4", ("Consolas", 13, "bold")),
    "email": ("#f59f16", ("Consolas", 13, "bold")),
    "dominio": ("#00BFFF", ("Consolas", 13, "bold")),
    "entidade": ("#F765F7", ("Consolas", 13, "bold")),
    "dns": ("#002EFC", ("Consolas", 13, "bold")),
    "data": ("#00FFFF", ("Consolas", 13, "bold")),
    "status": ("#F765F7", ("Consolas", 13, "bold")),
    "endereco": ("#f5ff2e", ("Consolas", 13, "bold")),
    "pessoa": ("#ff2e6d", ("Consolas", 13, "bold")),
}

for area in [text_whois, text_cnpj]:
    for tag, (cor, fonte) in tag_configs.items():
        area.tag_configure(tag, foreground=cor, font=fonte)

# ===================== FOOTER =====================
footer = tk.Label(root, text="WHOIS • Consulta Segura • Informações de Registro Público + CNPJ Avançado + OSINT",
                  font=("Consolas", 9), fg="#008800", bg="#0a0a0a")
footer.pack(side=tk.BOTTOM, pady=8)

# ===================== DUPLO CLIQUE ABRIR LINK =====================
def abrir_link(event):
    widget = event.widget
    try:
        index = widget.index(f"@{event.x},{event.y}")
        line = widget.get(f"{index} linestart", f"{index} lineend")
        urls = re.findall(r'https?://\S+', line)
        if urls:
            webbrowser.open(urls[0])
    except:
        pass

for txt in [text_whois, text_hist, text_cnpj, text_url, text_osint]:
    txt.bind("<Double-Button-1>", abrir_link)

root.mainloop()
