import socket
import re
import os
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import requests

# ===================== ESTILO =====================
class HackerStyle:
    BG = "#0a0a0a"
    FG = "#00ff41"
    ACCENT = "#00ff41"
    RED = "#ff0033"
    GRAY = "#1a1a1a"
    FONT = ("Consolas", 11)
    FONT_BOLD = ("Consolas", 12, "bold")
    TITLE_FONT = ("Consolas", 18, "bold")

# ===================== TRADUÇÃO WHOIS =====================
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
}

# ===================== FUNÇÕES WHOIS =====================
def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
    for formato in formatos:
        try:
            data = datetime.strptime(texto.strip(), formato)
            return data.strftime("%d/%m/%Y")
        except:
            continue
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


def consultar_whois(entrada):
    try:
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
                    if not dados:
                        break
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
                if not dados:
                    break
                resposta += dados

        texto = resposta.decode(errors='ignore')
        texto = re.sub(
            r'(Information.*?support.*?access.*?)(\n\n|\Z)',
            '',
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        linhas = texto.splitlines()
        saida_formatada = [f"WHOIS  ▶  {entrada.upper()}\n"]

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
            linha = re.sub(
                r"\d{4}-\d{2}-\d{2}(T[\d:.Z]+)?|\d{8}",
                lambda m: formatar_data_brasileira(m.group()),
                linha
            )
            linha_traduzida = traduzir_linha(linha)
            saida_formatada.append(linha_traduzida)

        return "\n".join(saida_formatada)
    except Exception as e:
        return f"[-] Erro na consulta: {e}"


def get_tag_da_linha(linha: str) -> str:
    linha_lower = linha.lower()
    if linha.startswith("=") or "WHOIS →" in linha or "WHOIS  ▶" in linha:
        return "header"
    if any(x in linha_lower for x in ["domínio", "domain"]):
        return "dominio"
    if "pessoa" in linha_lower:
        return "pessoa"
    if any(x in linha_lower for x in ["entidade", "owner", "registrante", "responsável", "person", "organização"]):
        return "entidade"
    if any(x in linha_lower for x in ["cnpj", "ownerid"]):
        return "cnpj"
    if any(x in linha_lower for x in ["email", "e-mail", "abuse-mailbox"]):
        return "email"
    if any(x in linha_lower for x in ["servidor dns", "servidores dns", "nameserver", "nserver", "dnssec"]):
        return "dns"
    if any(x in linha_lower for x in ["criado em", "alterado em", "expira em", "atualizado em",
                                      "creation date", "updated date", "registry expiry",
                                      "nsstat", "nslastaa"]):
        return "data"
    if any(x in linha_lower for x in ["status", "status do domínio", "domain status"]):
        return "status"
    if any(x in linha_lower for x in ["endereço", "cidade", "estado", "cep", "país", "address", "country"]):
        return "endereco"
    return "normal"


def consultar_e_mostrar_whois(entry_domain, text_output):
    dominio = entry_domain.get().strip()
    if not dominio:
        messagebox.showerror("ERRO", "Digite um alvo válido.")
        return
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, f"[+] Iniciando consulta WHOIS em {dominio}...\n\n", "header")
    text_output.update()
    resultado = consultar_whois(dominio)
    text_output.delete(1.0, tk.END)
    for linha in resultado.splitlines():
        tag = get_tag_da_linha(linha)
        text_output.insert(tk.END, linha + "\n", tag)


def salvar_html_whois(text_output):
    conteudo = text_output.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showerror("Erro", "Nenhum resultado WHOIS para salvar. Faça uma consulta primeiro.")
        return
    filename = filedialog.asksaveasfilename(
        title="Salvar WHOIS como HTML",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile="whois_resultado.html",
    )
    if not filename:
        return
    try:
        alvo = "desconhecido"
        for linha in conteudo.splitlines():
            if "WHOIS" in linha and ("▶" in linha or "→" in linha):
                alvo = linha.split("▶")[-1].split("→")[-1].strip()
                break

        def escape_html(texto):
            return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def cor_da_linha(campo_lower):
            if any(x in campo_lower for x in ["domínio", "domain"]):
                return "#00BFFF"
            if "pessoa" in campo_lower:
                return "#ff2e6d"
            if any(x in campo_lower for x in ["entidade", "owner", "registrante", "responsável", "person", "organização"]):
                return "#F765F7"
            if any(x in campo_lower for x in ["cnpj", "ownerid"]):
                return "#F7F5F4"
            if any(x in campo_lower for x in ["email", "e-mail", "abuse-mailbox"]):
                return "#f59f16"
            if any(x in campo_lower for x in ["servidor dns", "servidores dns", "nameserver", "nserver", "dnssec"]):
                return "#5B8CFF"
            if any(x in campo_lower for x in ["criado em", "alterado em", "expira em", "atualizado em",
                                              "creation date", "updated date", "registry expiry",
                                              "nsstat", "nslastaa"]):
                return "#00FFFF"
            if any(x in campo_lower for x in ["status", "status do domínio", "domain status"]):
                return "#F765F7"
            if any(x in campo_lower for x in ["endereço", "cidade", "estado", "cep", "país", "address", "country"]):
                return "#f5ff2e"
            return "#00ff41"

        linhas_html = []
        for linha in conteudo.splitlines():
            linha = linha.rstrip()
            if not linha:
                linhas_html.append("")
                continue
            if "WHOIS" in linha or linha.startswith("=") or linha.startswith("-"):
                linhas_html.append(f'<span style="color:#00FF80;font-weight:bold;">{escape_html(linha)}</span>')
                continue
            if ":" in linha:
                campo, valor = linha.split(":", 1)
                cor = cor_da_linha(campo.lower())
                linhas_html.append(
                    f'<span style="color:#00ff41;">{escape_html(campo)}:</span> '
                    f'<span style="color:{cor};font-weight:bold;">{escape_html(valor)}</span>'
                )
            else:
                linhas_html.append(f'<span style="color:#00ff41;">{escape_html(linha)}</span>')

        corpo = "\n".join(linhas_html)
        alvo_esc = escape_html(alvo)
        data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WHOIS - {alvo_esc}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0b0e1a 0%, #141829 50%, #0b0e1a 100%);
            color: #e0e0e0; min-height: 100vh; padding: 2rem 1rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center; margin-bottom: 2.5rem; padding: 2rem 1rem;
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.08) 0%, rgba(0, 200, 255, 0.05) 100%);
            border-radius: 20px; border: 1px solid rgba(0, 255, 65, 0.15);
            position: relative; overflow: hidden;
        }}
        .header h1 {{
            font-size: 2.2rem; font-weight: 800;
            background: linear-gradient(135deg, #00ff41, #00d4ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; position: relative; z-index: 1;
        }}
        .header .subtitle {{ font-size: 0.9rem; color: rgba(255,255,255,0.4); margin-top: 0.5rem; }}
        .header .cnpj-badge {{
            display: inline-block; margin-top: 1rem; padding: 0.4rem 1.2rem;
            background: rgba(0, 255, 65, 0.12); border: 1px solid rgba(0, 255, 65, 0.3);
            border-radius: 30px; font-family: 'Courier New', monospace;
            font-size: 1.1rem; font-weight: 600; color: #00ff41;
        }}
        .section {{
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px; padding: 1.8rem 2rem; margin-bottom: 1.8rem;
        }}
        .section-title {{
            font-size: 1.15rem; font-weight: 700; color: #00ff41;
            margin-bottom: 1.2rem; display: flex; align-items: center; gap: 0.6rem;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        pre.whois-pre {{
            background: #000; border: 1px solid rgba(0, 255, 65, 0.15);
            border-radius: 12px; padding: 1.4rem 1.6rem;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.92rem; line-height: 1.7; white-space: pre; overflow-x: auto;
        }}
        .footer {{
            text-align: center; margin-top: 2.5rem; padding: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.75rem; color: rgba(255,255,255,0.2);
        }}
        .footer span {{ color: #00ff41; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>RELATÓRIO WHOIS</h1>
        <div class="cnpj-badge">{alvo_esc}</div>
        <div class="subtitle">Consulta de registro público &bull; {data_hora}</div>
    </div>
    <div class="section">
        <div class="section-title"><span>🌐</span> Resultado WHOIS</div>
        <pre class="whois-pre">{corpo}</pre>
    </div>
    <div class="footer">
        Relatório gerado em <span>{data_hora}</span> &bull; WHOIS Extractor
    </div>
</div>
</body>
</html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        abrir = messagebox.askyesno("Sucesso", f"WHOIS salvo com sucesso!\n\n{filename}\n\nDeseja abrir no navegador?")
        if abrir:
            webbrowser.open(filename)
    except Exception as e:
        messagebox.showerror("Erro ao salvar", f"Não foi possível salvar: {str(e)}")


# ===================== FUNÇÕES CNPJ =====================
def limpar_cnpj(cnpj):
    return ''.join(filter(str.isdigit, str(cnpj)))


def formatar_cnpj(cnpj):
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def extrair_holdings_brasilapi(dados_brasilapi):
    """Extrai sócios JURÍDICOS (CNPJ de 14 dígitos) do QSA da BrasilAPI."""
    holdings = []
    qsa = dados_brasilapi.get('qsa', []) or []
    for socio in qsa:
        cnpj_cpf = (
            socio.get('cnpj_cpf_do_socio') or
            socio.get('cnpj_cpf_socio') or
            ''
        )
        digitos = limpar_cnpj(cnpj_cpf)
        if len(digitos) == 14 and '*' not in str(cnpj_cpf):
            razao = (
                socio.get('nome_socio') or
                socio.get('nome') or
                'Não informado'
            )
            try:
                r2 = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{digitos}', timeout=8)
                if r2.status_code == 200:
                    razao = r2.json().get('razao_social', razao)
            except:
                pass

            qualificacao = (
                socio.get('qualificacao_socio') or
                socio.get('descricao_qualificacao_socio') or
                socio.get('qual') or
                'Não informado'
            )
            entrada = (
                socio.get('data_entrada_sociedade') or
                socio.get('data_entrada') or
                'Não informada'
            )
            holdings.append({
                'cnpj': formatar_cnpj(digitos),
                'razao_social': razao,
                'qualificacao': qualificacao,
                'entrada': entrada,
            })
    return holdings


def consultar_cnpj(cnpj, url_custom=None):
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        messagebox.showerror("Erro", "CNPJ deve ter 14 dígitos.")
        return None

    holdings = []
    dados = None

    # ===== 1º Tenta URL CUSTOM (se fornecida) =====
    if url_custom and "{cnpj}" in url_custom:
        try:
            url = url_custom.replace("{cnpj}", cnpj)
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                dados_custom = r.json()
                # Tenta extrair holdings se a resposta tiver QSA no formato BrasilAPI
                holdings = extrair_holdings_brasilapi(dados_custom)
                # Se a resposta já tiver formato parecido com ReceitaWS, usa ela
                if 'nome' in dados_custom or 'razao_social' in dados_custom:
                    # Normaliza para o formato esperado pelo resto do código
                    if 'razao_social' in dados_custom and 'nome' not in dados_custom:
                        dados_custom['nome'] = dados_custom.get('razao_social')
                    dados = dados_custom
                    dados['holdings'] = holdings
                    return dados
        except Exception as e:
            print(f"[URL Custom] {e}")

    # ===== 2º BrasilAPI (Holdings) =====
    try:
        r = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}', timeout=12)
        if r.status_code == 200:
            holdings = extrair_holdings_brasilapi(r.json())
    except Exception as e:
        pass

    # ===== 3º ReceitaWS (dados principais) =====
    try:
        response = requests.get(f'https://www.receitaws.com.br/v1/cnpj/{cnpj}', timeout=12)
        if response.status_code == 200:
            dados = response.json()
            dados['holdings'] = holdings
            return dados
        elif response.status_code == 429:
            messagebox.showerror(
                "Limite da ReceitaWS",
                "Limite de consultas atingido (3/min).\nAguarde cerca de 60 segundos e tente novamente."
            )
        else:
            messagebox.showerror("Erro ao consultar CNPJ", f"Erro: {response.status_code}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro na requisição", f"Erro: {e}")

    return None


def calcular_idade(data_abertura):
    try:
        if not data_abertura:
            return "Não informado"
        if '/' in str(data_abertura):
            data_abertura = datetime.strptime(data_abertura, '%d/%m/%Y')
        else:
            data_abertura = datetime.strptime(str(data_abertura)[:10], '%Y-%m-%d')
        hoje = datetime.now()
        diferenca = hoje - data_abertura
        anos = diferenca.days // 365
        meses = (diferenca.days % 365) // 30
        dias = (diferenca.days % 365) % 30
        return f"{anos} anos, {meses} meses e {dias} dias"
    except:
        return "Data de abertura inválida"


def abrir_google_maps(logradouro, numero, municipio, uf):
    endereco = f"{logradouro}, {numero}, {municipio}, {uf}"
    url = f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}"
    webbrowser.open(url)


def gerar_texto(dados_cnpj):
    logradouro = dados_cnpj.get('logradouro', 'Não encontrado')
    numero = dados_cnpj.get('numero', 'Não encontrado')
    municipio = dados_cnpj.get('municipio', 'Não encontrado')
    uf = dados_cnpj.get('uf', 'Não encontrado')

    atualizacao_raw = dados_cnpj.get('ultima_atualizacao', '')
    if atualizacao_raw and atualizacao_raw != "Não encontrado":
        try:
            dt = datetime.strptime(atualizacao_raw[:19], "%Y-%m-%dT%H:%M:%S")
            atualizacao = dt.strftime("%d/%m/%Y às %H:%M")
        except:
            atualizacao = atualizacao_raw
    else:
        atualizacao = "Não informado"

    message = f"""
CNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}

RAZÃO SOCIAL: {dados_cnpj.get('nome', 'Não encontrado')}

MATRIZ OU FILIAL: {dados_cnpj.get('tipo', 'Não encontrado')}

NOME FANTASIA: {dados_cnpj.get('fantasia', 'Não encontrado')}

SITUAÇÃO CADASTRAL: {dados_cnpj.get('situacao', 'Não encontrado')}

DATA DA SITUAÇÃO CADASTRAL: {dados_cnpj.get('data_situacao', 'Não encontrado')}

MOTIVO DA SITUAÇÃO CADASTRAL: {dados_cnpj.get('motivo_situacao', 'Não encontrado')}

NATUREZA JURÍDICA: {dados_cnpj.get('natureza_juridica', 'Não encontrado')}

DATA DE ABERTURA: {dados_cnpj.get('abertura', 'Não encontrado')}

IDADE: {calcular_idade(dados_cnpj.get('abertura'))}

PORTE (RFB): {dados_cnpj.get('porte', 'Não encontrado')}

CAPITAL SOCIAL: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}

ATUALIZAÇÃO DESTA PÁGINA: {atualizacao}




LOCALIZAÇÃO
===========

ENDEREÇO: {logradouro}       |  Número: {numero}

COMPLEMENTO: {dados_cnpj.get('complemento', 'Não encontrado')}

BAIRRO: {dados_cnpj.get('bairro', 'Não encontrado')}

CIDADE | ESTADO: {municipio} | {uf}

CEP: {dados_cnpj.get('cep', 'Não encontrado')}

TELEFONES: {dados_cnpj.get('telefone', 'Não encontrado')}

E-MAILS: {dados_cnpj.get('email', 'Não encontrado')}



ATIVIDADE ECONÔMICA PRINCIPAL
==============================

CÓDIGO: {dados_cnpj['atividade_principal'][0]['code'] if dados_cnpj.get('atividade_principal') else 'Não encontrado'}
DESCRIÇÃO: {dados_cnpj['atividade_principal'][0]['text'] if dados_cnpj.get('atividade_principal') else 'Não encontrado'}


ATIVIDADES ECONÔMICAS SECUNDÁRIAS
=================================

"""
    if dados_cnpj.get('atividades_secundarias'):
        for atividade in dados_cnpj['atividades_secundarias']:
            message += f"CÓDIGO: {atividade.get('code', '')} | DESCRIÇÃO: {atividade.get('text', '')}\n"
    else:
        message += "Não encontrado\n"

    message += "\n\nQUADRO DE SÓCIOS E ADMINISTRADORES (QSA)\n==========================================\n"
    if dados_cnpj.get('qsa'):
        for socio in dados_cnpj['qsa']:
            data_entrada = socio.get('data_entrada') or ''
            if data_entrada:
                try:
                    data_entrada = datetime.strptime(data_entrada, '%d/%m/%Y').strftime('%d/%m/%Y')
                except:
                    pass
                message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
ENTRADA: {data_entrada}
"""
            else:
                message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
"""
    else:
        message += "Não encontrado\n"

    # ===== HOLDINGS =====
    message += "\n\nHOLDINGS / SÓCIOS JURÍDICOS\n==========================================\n"
    holdings = dados_cnpj.get('holdings', [])
    if holdings:
        for h in holdings:
            message += f"""
CNPJ: {h.get('cnpj', 'Não informado')}
RAZÃO SOCIAL: {h.get('razao_social', 'Não informado')}
QUALIFICAÇÃO: {h.get('qualificacao', 'Não informado')}
ENTRADA: {h.get('entrada', 'Não informada')}
"""
    else:
        message += "Nenhuma holding/sócio jurídico encontrado.\n"

    return message


def salvar_html_bonito(dados_cnpj, filename):
    def safe(val, fallback="Não informado"):
        if val is None:
            return fallback
        val = str(val).strip()
        return val if val and val != "Não encontrado" else fallback

    logr = safe(dados_cnpj.get('logradouro', ''), '')
    num = safe(dados_cnpj.get('numero', ''), 'S/N')
    comp = safe(dados_cnpj.get('complemento', ''), '')
    bairro = safe(dados_cnpj.get('bairro', ''), '')
    cep = safe(dados_cnpj.get('cep', ''), '')
    municipio = safe(dados_cnpj.get('municipio', ''))
    uf = safe(dados_cnpj.get('uf', ''))
    cnpj_raw = safe(dados_cnpj.get('cnpj', ''))
    razao = safe(dados_cnpj.get('nome', ''))
    fantasia_val = safe(dados_cnpj.get('fantasia', ''))
    tipo = safe(dados_cnpj.get('tipo', ''))
    situacao = safe(dados_cnpj.get('situacao', ''))
    data_situacao = safe(dados_cnpj.get('data_situacao', ''))
    motivo_situacao = safe(dados_cnpj.get('motivo_situacao', ''))
    natureza = safe(dados_cnpj.get('natureza_juridica', ''))
    abertura = safe(dados_cnpj.get('abertura', ''))
    idade = calcular_idade(dados_cnpj.get('abertura'))
    porte = safe(dados_cnpj.get('porte', ''))
    capital = safe(dados_cnpj.get('capital_social', ''))

    atualizacao_raw = dados_cnpj.get('ultima_atualizacao', '')
    if atualizacao_raw and atualizacao_raw != "Não encontrado":
        try:
            dt = datetime.strptime(atualizacao_raw[:19], "%Y-%m-%dT%H:%M:%S")
            atualizacao = dt.strftime("%d/%m/%Y às %H:%M")
        except:
            atualizacao = atualizacao_raw
    else:
        atualizacao = "Não informado"

    telefone = safe(dados_cnpj.get('telefone', ''))
    email = safe(dados_cnpj.get('email', ''))

    endereco = f"{logr}, {num}, {municipio}, {uf}"
    maps_url = f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}"

    cod_principal = ""
    desc_principal = ""
    if dados_cnpj.get('atividade_principal'):
        cod_principal = dados_cnpj['atividade_principal'][0].get('code', '')
        desc_principal = dados_cnpj['atividade_principal'][0].get('text', '')

    atividades_sec_html = ""
    if dados_cnpj.get('atividades_secundarias'):
        for atv in dados_cnpj['atividades_secundarias']:
            atividades_sec_html += f"""
                <div class="atividade-sec-item">
                    <span class="badge-code">{atv.get('code', '')}</span>
                    <span class="atv-desc">{atv.get('text', '')}</span>
                </div>"""
    else:
        atividades_sec_html = '<p class="nao-encontrado">Nenhuma atividade secundária registrada</p>'

    # QSA
    qsa_html = ""
    if dados_cnpj.get('qsa'):
        for socio in dados_cnpj['qsa']:
            nome_socio = safe(socio.get('nome', ''))
            qual_socio = safe(socio.get('qual', ''))
            entrada_socio = socio.get('data_entrada', '')
            if entrada_socio:
                try:
                    entrada_socio = datetime.strptime(entrada_socio, '%d/%m/%Y').strftime('%d/%m/%Y')
                except:
                    entrada_socio = str(entrada_socio)
            else:
                entrada_socio = "Não informada"
            qsa_html += f"""
                <div class="socio-card">
                    <div class="socio-header">
                        <span class="socio-nome">{nome_socio}</span>
                        <span class="socio-qual">{qual_socio}</span>
                    </div>
                    <div class="socio-entrada">
                        <span class="label">Entrada:</span> {entrada_socio}
                    </div>
                </div>"""
    else:
        qsa_html = '<p class="nao-encontrado">Nenhum sócio ou administrador registrado</p>'

    # ===== HOLDINGS =====
    holdings_html = ""
    holdings = dados_cnpj.get('holdings', [])
    if holdings:
        for h in holdings:
            holdings_html += f"""
                <div class="socio-card">
                    <div class="socio-header">
                        <span class="socio-nome">{h.get('razao_social', 'Não informado')}</span>
                        <span class="socio-qual">{h.get('qualificacao', '')}</span>
                    </div>
                    <div class="socio-entrada">
                        <span class="label">CNPJ:</span> {h.get('cnpj', 'Não informado')}
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <span class="label">Entrada:</span> {h.get('entrada', 'Não informada')}
                    </div>
                </div>"""
    else:
        holdings_html = '<p class="nao-encontrado">Nenhuma holding/sócio jurídico encontrado</p>'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RESULTADO DA CONSULTA DO CNPJ - {cnpj_raw}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0b0e1a 0%, #141829 50%, #0b0e1a 100%);
            color: #e0e0e0; min-height: 100vh; padding: 2rem 1rem;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{
            text-align: center; margin-bottom: 2.5rem; padding: 2rem 1rem;
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.08) 0%, rgba(0, 200, 255, 0.05) 100%);
            border-radius: 20px; border: 1px solid rgba(0, 255, 65, 0.15);
            position: relative; overflow: hidden;
        }}
        .header h1 {{
            font-size: 2.2rem; font-weight: 800;
            background: linear-gradient(135deg, #00ff41, #00d4ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; position: relative; z-index: 1;
        }}
        .header .subtitle {{ font-size: 0.9rem; color: rgba(255,255,255,0.4); margin-top: 0.5rem; }}
        .header .cnpj-badge {{
            display: inline-block; margin-top: 1rem; padding: 0.4rem 1.2rem;
            background: rgba(0, 255, 65, 0.12); border: 1px solid rgba(0, 255, 65, 0.3);
            border-radius: 30px; font-family: 'Courier New', monospace;
            font-size: 1.1rem; font-weight: 600; color: #00ff41;
        }}
        .section {{
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px; padding: 1.8rem 2rem; margin-bottom: 1.8rem;
            transition: border-color 0.3s ease;
        }}
        .section:hover {{ border-color: rgba(0, 255, 65, 0.2); }}
        .section-title {{
            font-size: 1.15rem; font-weight: 700; color: #00ff41;
            margin-bottom: 1.2rem; display: flex; align-items: center; gap: 0.6rem;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        .info-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.8rem 1.5rem;
        }}
        .info-item {{ padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.04); }}
        .info-item .label {{
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1px; color: rgba(255,255,255,0.3); display: block; margin-bottom: 0.2rem;
        }}
        .info-item .value {{ font-size: 0.95rem; font-weight: 500; color: #f0f0f0; word-break: break-word; }}
        .info-item .value.highlight {{ color: #00ff41; }}
        .badge-code {{
            display: inline-block; padding: 0.2rem 0.6rem;
            background: rgba(0, 200, 255, 0.1); border: 1px solid rgba(0, 200, 255, 0.2);
            border-radius: 6px; font-family: 'Courier New', monospace;
            font-size: 0.75rem; color: #00d4ff; font-weight: 600;
        }}
        .status-badge {{
            display: inline-block; padding: 0.25rem 0.9rem;
            border-radius: 20px; font-size: 0.8rem; font-weight: 600;
        }}
        .status-ok {{
            background: rgba(0, 255, 65, 0.15); color: #00ff41;
            border: 1px solid rgba(0, 255, 65, 0.3);
        }}
        .atividade-sec-item {{
            padding: 0.5rem 0.8rem; margin-bottom: 0.4rem;
            background: rgba(255,255,255,0.02); border-radius: 8px;
            display: flex; align-items: center; gap: 0.8rem; flex-wrap: wrap;
        }}
        .atividade-sec-item .atv-desc {{ font-size: 0.9rem; color: #ccc; }}
        .socio-card {{
            padding: 1rem 1.2rem; margin-bottom: 0.7rem;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px; transition: all 0.2s ease;
        }}
        .socio-card:hover {{
            background: rgba(0, 255, 65, 0.04); border-color: rgba(0, 255, 65, 0.15);
            transform: translateX(4px);
        }}
        .socio-header {{ display: flex; align-items: center; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 0.3rem; }}
        .socio-nome {{ font-weight: 600; font-size: 1rem; color: #fff; }}
        .socio-qual {{
            font-size: 0.8rem; color: rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.06); padding: 0.15rem 0.6rem; border-radius: 12px;
        }}
        .socio-entrada {{ font-size: 0.8rem; color: rgba(255,255,255,0.4); }}
        .socio-entrada .label {{ font-weight: 600; color: rgba(255,255,255,0.3); }}
        .nao-encontrado {{ color: rgba(255,255,255,0.25); font-style: italic; font-size: 0.9rem; }}
        .info-full {{ grid-column: 1 / -1; }}
        .maps-link-container {{
            margin-top: 1.5rem; padding: 1.2rem 1.5rem;
            background: rgba(0, 200, 255, 0.05); border: 1px solid rgba(0, 200, 255, 0.15);
            border-radius: 12px; display: flex; align-items: center;
            justify-content: space-between; flex-wrap: wrap; gap: 1rem;
        }}
        .maps-link-container .maps-label {{
            font-size: 0.8rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px;
        }}
        .maps-link-container .maps-coords {{
            font-size: 0.85rem; color: rgba(255,255,255,0.5); font-family: 'Courier New', monospace;
        }}
        .btn-maps {{
            display: inline-flex; align-items: center; gap: 0.5rem;
            padding: 0.7rem 1.5rem; background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: #000; font-weight: 700; font-size: 0.9rem; border-radius: 30px;
            text-decoration: none; transition: all 0.3s ease;
        }}
        .btn-maps:hover {{ transform: scale(1.05); box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); }}
        .footer {{
            text-align: center; margin-top: 2.5rem; padding: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.75rem; color: rgba(255,255,255,0.2);
        }}
        .footer span {{ color: #00ff41; }}
        @media (max-width: 640px) {{
            body {{ padding: 1rem 0.6rem; }}
            .section {{ padding: 1.2rem 1rem; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 1.5rem; }}
            .maps-link-container {{ flex-direction: column; text-align: center; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>RESULTADO DA CONSULTA DO CNPJ</h1>
        <div class="cnpj-badge">{cnpj_raw}</div>
        <div class="subtitle">Dados obtidos • {atualizacao}</div>
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">📋</span> Informações Gerais</div>
        <div class="info-grid">
            <div class="info-item"><span class="label">Razão Social</span><span class="value highlight">{razao}</span></div>
            <div class="info-item"><span class="label">Nome Fantasia</span><span class="value">{fantasia_val}</span></div>
            <div class="info-item"><span class="label">Matriz / Filial</span><span class="value">{tipo}</span></div>
            <div class="info-item"><span class="label">Situação Cadastral</span><span class="value"><span class="status-badge status-ok">{situacao}</span></span></div>
            <div class="info-item"><span class="label">Data da Situação</span><span class="value">{data_situacao}</span></div>
            <div class="info-item"><span class="label">Motivo da Situação</span><span class="value">{motivo_situacao}</span></div>
            <div class="info-item"><span class="label">Natureza Jurídica</span><span class="value">{natureza}</span></div>
            <div class="info-item"><span class="label">Data de Abertura</span><span class="value">{abertura}</span></div>
            <div class="info-item"><span class="label">Atualização</span><span class="value">{atualizacao}</span></div>
            <div class="info-item"><span class="label">Idade</span><span class="value highlight">{idade}</span></div>
            <div class="info-item"><span class="label">Porte (RFB)</span><span class="value">{porte}</span></div>
            <div class="info-item info-full"><span class="label">Capital Social</span><span class="value highlight">R$ {capital}</span></div>
        </div>
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">📍</span> Localização</div>
        <div class="info-grid">
            <div class="info-item info-full">
                <span class="label">Endereço</span>
                <span class="value">{logr} — <span style="color:#00d4ff;font-weight:600;">Número:</span> {num}{f' <span style="color:#FF8C00;">{comp}</span>' if comp and comp != 'Não informado' else ''}</span>
            </div>
            <div class="info-item"><span class="label">Bairro</span><span class="value">{bairro}</span></div>
            <div class="info-item"><span class="label">Cidade / Estado</span><span class="value">{municipio} / {uf}</span></div>
            <div class="info-item"><span class="label">CEP</span><span class="value">{cep}</span></div>
            <div class="info-item"><span class="label">Telefone</span><span class="value">{telefone}</span></div>
            <div class="info-item"><span class="label">E-mail</span><span class="value">{email}</span></div>
        </div>
        <div class="maps-link-container">
            <div>
                <div class="maps-label">📍 Geolocalização</div><br>
                <div class="maps-coords">{logr}, {num} — {municipio}/{uf}</div>
            </div>
            <a href="{maps_url}" target="_blank" class="btn-maps">📌 ABRIR NO GOOGLE MAPS</a>
        </div>
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">⚡</span> Atividade Econômica Principal</div>
        <div class="info-grid">
            <div class="info-item"><span class="label">Código CNAE</span><span class="value"><span class="badge-code">{cod_principal}</span></span></div>
            <div class="info-item info-full"><span class="label">Descrição</span><span class="value">{desc_principal}</span></div>
        </div>
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">🔗</span> Atividades Econômicas Secundárias</div>
        {atividades_sec_html}
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">👥</span> Quadro de Sócios e Administradores (QSA)</div>
        {qsa_html}
    </div>

    <div class="section">
        <div class="section-title"><span class="icon">🏛️</span> Holdings / Sócios Jurídicos</div>
        {holdings_html}
    </div>

    <div class="footer">
        Relatório gerado em <span>{datetime.now().strftime('%d/%m/%Y às %H:%M')}</span> • RESULTADO DA CONSULTA DO CNPJ
    </div>

</div>
</body>
</html>"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)


def salvar_arquivo(dados_cnpj):
    cnpj = dados_cnpj.get('cnpj', 'desconhecido').replace('/', '_').replace('.', '_').replace('-', '_')
    default_name = f"consulta_cnpj_{cnpj}.html"
    filename = filedialog.asksaveasfilename(
        title="Salvar relatório HTML",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile=default_name
    )
    if filename:
        try:
            salvar_html_bonito(dados_cnpj, filename)
            abrir = messagebox.askyesno(
                "Sucesso",
                f"Relatório HTML salvo com sucesso!\n\n{filename}\n\nDeseja abrir no navegador?"
            )
            if abrir:
                webbrowser.open(filename)
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar:\n{str(e)}")


def consultar_e_mostrar_cnpj(cnpj_entry, url_entry, info_text, maps_button, salvar_button):
    cnpj = limpar_cnpj(cnpj_entry.get())
    if not cnpj:
        messagebox.showerror("Erro", "Por favor, insira um CNPJ válido")
        return

    url_custom = url_entry.get().strip() if url_entry else None

    dados_cnpj = consultar_cnpj(cnpj, url_custom)
    if dados_cnpj:
        info_text.config(state=tk.NORMAL)
        info_text.delete(1.0, tk.END)
        message = gerar_texto(dados_cnpj)
        info_text.insert(tk.END, message)
        info_text.config(state=tk.DISABLED)

        logradouro = dados_cnpj.get('logradouro', 'Não encontrado')
        numero = dados_cnpj.get('numero', 'Não encontrado')
        municipio = dados_cnpj.get('municipio', 'Não encontrado')
        uf = dados_cnpj.get('uf', 'Não encontrado')

        maps_button.config(state=tk.NORMAL, command=lambda: abrir_google_maps(logradouro, numero, municipio, uf))
        salvar_button.config(state=tk.NORMAL, command=lambda: salvar_arquivo(dados_cnpj))


# ===================== ABA WHOIS =====================
def criar_aba_whois(parent):
    header = tk.Label(parent, text="WHOIS • Consulta Segura • Informações de Registro Público",
                      font=("Consolas", 14, "bold"), fg="#00ff41", bg=HackerStyle.BG)
    header.pack(pady=5)

    label_domain = tk.Label(parent, text="DIGITE O DOMINIO", font=("Consolas", 16, "bold"),
                            fg="#00ff41", bg=HackerStyle.BG)
    label_domain.pack(pady=5)

    entry_domain = tk.Entry(parent, font=("Consolas", 14), width=45, bg="#000000", fg="#00ff41",
                            insertbackground="#00ff41", relief="flat", bd=0, highlightthickness=2,
                            highlightbackground="#00ff41", highlightcolor="#00ff80",
                            selectbackground="#00ff80", selectforeground="black")
    entry_domain.pack(pady=8)

    frame_botoes = tk.Frame(parent, bg=HackerStyle.BG)
    frame_botoes.pack(pady=12)

    borda_scan = tk.Frame(frame_botoes, bg="#00ff41", padx=2, pady=2)
    borda_scan.pack(side=tk.LEFT, padx=15)
    btn_consultar = tk.Button(borda_scan, text="INICIAR SCAN", font=("Consolas", 12, "bold"),
                              bg="#001a00", fg="#00ff41", activebackground="#00ff80",
                              activeforeground="black", relief="flat", bd=0, width=20, height=2, cursor="hand2")
    btn_consultar.pack()

    borda_salvar = tk.Frame(frame_botoes, bg="#00ff41", padx=2, pady=2)
    borda_salvar.pack(side=tk.LEFT, padx=15)
    btn_salvar_whois = tk.Button(borda_salvar, text="💾 SALVAR WHOIS EM HTML", font=("Consolas", 12, "bold"),
                                 bg="#001a00", fg="#ff9100", activebackground="#00ff80",
                                 activeforeground="black", relief="flat", bd=0, width=25, height=2, cursor="hand2")
    btn_salvar_whois.pack()

    text_output = ScrolledText(parent, font=("Consolas", 12), bg="#000000", fg="#00ff41",
                               insertbackground="#00ff41", relief="flat", bd=0, highlightthickness=2,
                               highlightbackground="#00ff41", highlightcolor="#00ff80",
                               selectbackground="#00ff80", selectforeground="black", wrap="none")
    text_output.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

    tag_configs = {
        "header": ("#00FF80", ("Consolas", 13, "bold")),
        "dominio": ("#00BFFF", ("Consolas", 12, "bold")),
        "entidade": ("#F765F7", ("Consolas", 12, "bold")),
        "cnpj": ("#F7F5F4", ("Consolas", 12, "bold")),
        "pessoa": ("#ff2e6d", ("Consolas", 12, "bold")),
        "email": ("#f59f16", ("Consolas", 12, "bold")),
        "dns": ("#5B8CFF", ("Consolas", 12, "bold")),
        "data": ("#00FFFF", ("Consolas", 12, "bold")),
        "status": ("#F765F7", ("Consolas", 12, "bold")),
        "endereco": ("#f5ff2e", ("Consolas", 12, "bold")),
        "normal": ("#00ff41", ("Consolas", 12)),
    }
    for tag, (cor, fonte) in tag_configs.items():
        text_output.tag_configure(tag, foreground=cor, font=fonte)

    btn_consultar.config(command=lambda: consultar_e_mostrar_whois(entry_domain, text_output))
    btn_salvar_whois.config(command=lambda: salvar_html_whois(text_output))
    entry_domain.bind("<Return>", lambda e: consultar_e_mostrar_whois(entry_domain, text_output))


# ===================== ABA CNPJ =====================
def criar_aba_cnpj(parent):
    title = tk.Label(parent, text="CNPJ OSINT ANALYZER", font=HackerStyle.TITLE_FONT,
                     fg=HackerStyle.FG, bg=HackerStyle.BG)
    title.pack(pady=15)

    top_frame = tk.Frame(parent, bg=HackerStyle.BG)
    top_frame.pack(pady=10, fill="x", padx=40)

    tk.Label(top_frame, text="CNPJ →", font=HackerStyle.FONT_BOLD,
             fg=HackerStyle.FG, bg=HackerStyle.BG).pack(side="left", padx=(0, 8))

    cnpj_entry = tk.Entry(top_frame, width=32, font=("Consolas", 14),
                          bg="#111111", fg=HackerStyle.FG, insertbackground=HackerStyle.FG)
    cnpj_entry.pack(side="left", padx=4)

    consultar_button = tk.Button(top_frame, text="▶ CONSULTAR", font=HackerStyle.FONT_BOLD,
                                 bg="#00ff41", fg="black", activebackground="#00cc33", width=15)
    consultar_button.pack(side="left", padx=4)

    maps_button = tk.Button(top_frame, text="🗺️ GOOGLE MAPS", font=HackerStyle.FONT_BOLD,
                            bg="#00FFFF", fg="black", state=tk.DISABLED, width=20)
    maps_button.pack(side="left", padx=4)

    salvar_button = tk.Button(top_frame, text="💾 SALVAR HTML", font=HackerStyle.FONT_BOLD,
                              bg="#FF4500", fg="black", state=tk.DISABLED, width=20)
    salvar_button.pack(side="left", padx=4)


    # ========== URL CUSTOM (agora funcional) ==========
    uf = tk.Frame(parent, bg=HackerStyle.BG)
    uf.pack(pady=6, fill="x", padx=40)

    tk.Label(uf, text="URL CUSTOM →", font=HackerStyle.FONT_BOLD, fg="#00d4ff", bg=HackerStyle.BG).pack(side="left", padx=(0, 8))

    url_entry = tk.Entry(uf, width=70, font=("Consolas", 11), bg="#111", fg="#00d4ff", insertbackground="#00d4ff")
    url_entry.pack(side="left", padx=4, fill="x", expand=False)
    url_entry.insert(0, "")   # começa vazio

    # Frame com as URLs padrão + botões de copiar
    urls_frame = tk.Frame(parent, bg=HackerStyle.BG)
    urls_frame.pack(pady=(2, 8), fill="x", padx=40)

    # ===== URLs =====
    brasil_url = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    receita_url = "https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    cnpjws_url = "https://publica.cnpj.ws/cnpj/{cnpj}"
    cnpja_url = "https://open.cnpja.com/office/{cnpj}"
    opencnpj_url = "https://api.opencnpj.org/{cnpj}"
    minhareceita_url = "https://minhareceita.org/{cnpj}"

    def fazer_botao_copiar(frame, texto, url):
        tk.Label(frame, text=texto, font=("Consolas", 9), fg="#00ff41", bg=HackerStyle.BG).pack(side="left")
        tk.Label(frame, text=url, font=("Consolas", 8), fg="#666", bg=HackerStyle.BG).pack(side="left", padx=(3, 2))
        btn = tk.Button(
            frame, text="📋", font=("Consolas", 8),
            bg="#222", fg="#00ff41", relief="flat", cursor="hand2",
            command=lambda u=url: (
                url_entry.delete(0, tk.END),
                url_entry.insert(0, u),
                parent.clipboard_clear(),
                parent.clipboard_append(u)
            )
        )
        btn.pack(side="left", padx=(0, 12))

    # Linha 1
    fazer_botao_copiar(urls_frame, "BrasilAPI:", brasil_url)
    fazer_botao_copiar(urls_frame, "ReceitaWS:", receita_url)
    fazer_botao_copiar(urls_frame, "CNPJ.ws:", cnpjws_url)

    # Linha 2
    urls_frame2 = tk.Frame(parent, bg=HackerStyle.BG)
    urls_frame2.pack(pady=(0, 8), fill="x", padx=40)

    fazer_botao_copiar(urls_frame2, "CNPJá:", cnpja_url)
    fazer_botao_copiar(urls_frame2, "OpenCNPJ:", opencnpj_url)
    fazer_botao_copiar(urls_frame2, "minhaReceita:", minhareceita_url)

    text_area = ScrolledText(parent, wrap=tk.WORD, width=145, height=40,
                             font=("Consolas", 10), bg="#000000", fg=HackerStyle.FG,
                             insertbackground=HackerStyle.FG, selectbackground="#00ff41",
                             selectforeground="black")
    text_area.pack(pady=20, padx=40, fill="both", expand=True)
    text_area.config(state=tk.DISABLED)

    consultar_button.config(command=lambda: consultar_e_mostrar_cnpj(
        cnpj_entry, url_entry, text_area, maps_button, salvar_button))
    cnpj_entry.bind("<Return>", lambda e: consultar_e_mostrar_cnpj(
        cnpj_entry, url_entry, text_area, maps_button, salvar_button))


# ===================== INTERFACE PRINCIPAL =====================
def criar_interface_grafica():
    root = tk.Tk()
    root.title("WHOIS + CNPJ OSINT TOOLKIT")
    root.geometry("1280x900")
    root.state('zoomed')
    root.configure(bg=HackerStyle.BG)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TNotebook", background=HackerStyle.BG, borderwidth=0)
    style.configure("TNotebook.Tab", background="#111111", foreground=HackerStyle.FG,
                    font=("Consolas", 12, "bold"), padding=(25, 10))
    style.map("TNotebook.Tab",
              background=[("selected", "#003300")],
              foreground=[("selected", "#00ff80")])

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    aba_whois = tk.Frame(notebook, bg=HackerStyle.BG)
    aba_cnpj = tk.Frame(notebook, bg=HackerStyle.BG)

    notebook.add(aba_whois, text="  🌐 WHOIS  ")
    notebook.add(aba_cnpj, text="  🏢 CNPJ  ")

    criar_aba_whois(aba_whois)
    criar_aba_cnpj(aba_cnpj)

    footer = tk.Label(
        root,
        text="WHOIS + CNPJ • OSINT TOOLKIT • ReceitaWS + BrasilAPI • Holdings incluídas • URL Custom funcional",
        font=("Consolas", 9), fg="#008800", bg=HackerStyle.BG
    )
    footer.pack(side=tk.BOTTOM, pady=5)

    root.mainloop()


if __name__ == "__main__":
    criar_interface_grafica()
