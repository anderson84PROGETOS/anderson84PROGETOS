import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
import webbrowser
from datetime import datetime
import os

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

# ABRIR NO Chrome
def abrir_arquivo():
    caminho = filedialog.askopenfilename(
        title="Abrir arquivo HTML",
        filetypes=[("Arquivos HTML", "*.html *.htm")]
    )

    if not caminho:
        return

    try:
        chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        if os.path.exists(chrome):
            webbrowser.register(
                'chrome',
                None,
                webbrowser.BackgroundBrowser(chrome)
            )
            webbrowser.get('chrome').open(f"file:///{caminho}")
        else:
            # Se o Chrome não estiver nesse local, abre no navegador padrão
            webbrowser.open(f"file:///{caminho}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))

def consultar_cnpj(cnpj):
    url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            messagebox.showerror("Erro ao consultar CNPJ", f"Erro ao consultar CNPJ: {response.status_code}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro na requisição", f"Erro na requisição: {e}")
    return None

def calcular_idade(data_abertura):
    try:
        hoje = datetime.now()
        data_abertura = datetime.strptime(data_abertura, '%d/%m/%Y')
        diferenca = hoje - data_abertura
        anos = diferenca.days // 365
        meses = (diferenca.days % 365) // 30
        dias = (diferenca.days % 365) % 30
        return f"{anos} anos, {meses} meses e {dias} dias"
    except ValueError:
        return "Data de abertura inválida"

def abrir_google_maps(logradouro, numero, municipio, uf):
    endereco = f"{logradouro}, {numero}, {municipio}, {uf}"
    url = f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}"
    webbrowser.open(url)    

def limpar_cnpj(cnpj):
    return ''.join(filter(str.isdigit, cnpj))

def gerar_texto(dados_cnpj):

    logradouro = dados_cnpj.get('logradouro', 'Não encontrado')
    numero = dados_cnpj.get('numero', 'Não encontrado')
    municipio = dados_cnpj.get('municipio', 'Não encontrado')
    uf = dados_cnpj.get('uf', 'Não encontrado')


    # CONVERTER DATA ISO PARA BRASIL
    atualizacao_raw = dados_cnpj.get('ultima_atualizacao', '')

    if atualizacao_raw and atualizacao_raw != "Não encontrado":
        try:
            dt = datetime.strptime(
                atualizacao_raw[:19],
                "%Y-%m-%dT%H:%M:%S"
            )
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

IDADE: {calcular_idade(dados_cnpj['abertura']) if 'abertura' in dados_cnpj else 'Não encontrado'}

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

CÓDIGO: {dados_cnpj['atividade_principal'][0]['code'] if 'atividade_principal' in dados_cnpj and dados_cnpj['atividade_principal'] else 'Não encontrado'}
DESCRIÇÃO: {dados_cnpj['atividade_principal'][0]['text'] if 'atividade_principal' in dados_cnpj and dados_cnpj['atividade_principal'] else 'Não encontrado'}


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
            data_entrada = socio.get('data_entrada', None)
            if data_entrada:
                try:
                    data_entrada = datetime.strptime(data_entrada, '%d/%m/%Y').strftime('%d/%m/%Y')
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
ENTRADA: {data_entrada}
"""
                except ValueError:
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
ENTRADA: Data inválida
"""
            else:
                message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
"""
    else:
        message += "Não encontrado\n"
    
    return message

def salvar_html_bonito(dados_cnpj, filename):
    """Gera um HTML moderno, responsivo e visualmente bonito com os dados do CNPJ."""
    
    def safe(val, fallback="Não informado"):
        return val if val and val.strip() and val != "Não encontrado" else fallback
    
    def get_endereco_completo():
        logr = safe(dados_cnpj.get('logradouro', ''), '')
        num = safe(dados_cnpj.get('numero', ''), 'S/N')
        comp = safe(dados_cnpj.get('complemento', ''), '')
        bairro = safe(dados_cnpj.get('bairro', ''), '')
        cep = safe(dados_cnpj.get('cep', ''), '')
        return logr, num, comp, bairro, cep
    
    logr, num, comp, bairro, cep = get_endereco_completo()
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
    idade = calcular_idade(dados_cnpj['abertura']) if 'abertura' in dados_cnpj else 'Não informado'
    porte = safe(dados_cnpj.get('porte', ''))
    capital = safe(dados_cnpj.get('capital_social', ''))

    atualizacao_raw = dados_cnpj.get('ultima_atualizacao', '')

    if atualizacao_raw and atualizacao_raw != "Não encontrado":
        try:
            dt = datetime.strptime(
                atualizacao_raw[:19],
                "%Y-%m-%dT%H:%M:%S"
            )
            atualizacao = dt.strftime("%d/%m/%Y às %H:%M")
        except Exception:
            atualizacao = atualizacao_raw
    else:
        atualizacao = "Não informado"
        
    
    telefone = safe(dados_cnpj.get('telefone', ''))
    email = safe(dados_cnpj.get('email', ''))    

    # Endereço para o Google Maps
    logradouro = safe(dados_cnpj.get("logradouro", ""))
    numero = safe(dados_cnpj.get("numero", ""))
    municipio = safe(dados_cnpj.get("municipio", ""))
    uf = safe(dados_cnpj.get("uf", ""))

    endereco = f"{logradouro}, {numero}, {municipio}, {uf}"
    maps_url = f"https://www.google.com/maps/search/?api=1&query={endereco.replace(' ', '+')}"
    
    # Atividade principal
    cod_principal = ""
    desc_principal = ""
    if 'atividade_principal' in dados_cnpj and dados_cnpj['atividade_principal']:
        cod_principal = dados_cnpj['atividade_principal'][0].get('code', '')
        desc_principal = dados_cnpj['atividade_principal'][0].get('text', '')
    
    # Atividades secundárias
    atividades_sec_html = ""
    if 'atividades_secundarias' in dados_cnpj and dados_cnpj['atividades_secundarias']:
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
    if 'qsa' in dados_cnpj and dados_cnpj['qsa']:
        for socio in dados_cnpj['qsa']:
            nome_socio = safe(socio.get('nome', ''))
            qual_socio = safe(socio.get('qual', ''))
            entrada_socio = socio.get('data_entrada', '')
            if entrada_socio:
                try:
                    entrada_socio = datetime.strptime(entrada_socio, '%d/%m/%Y').strftime('%d/%m/%Y')
                except:
                    entrada_socio = "Data inválida"
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

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RESULTADO DA CONSULTA DO CNPJ - {cnpj_raw}</title>
    <style>
        /* ==================== RESET & BASE ==================== */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0b0e1a 0%, #141829 50%, #0b0e1a 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}

        /* ==================== HEADER ==================== */
        .header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.08) 0%, rgba(0, 200, 255, 0.05) 100%);
            border-radius: 20px;
            border: 1px solid rgba(0, 255, 65, 0.15);
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%; left: -50%; width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(0, 255, 65, 0.03) 0%, transparent 70%);
            animation: pulse 8s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.2); opacity: 1; }}
        }}
        .header h1 {{
            font-size: 2.2rem; font-weight: 800;
            background: linear-gradient(135deg, #00ff41, #00d4ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; letter-spacing: -0.5px;
            position: relative; z-index: 1;
        }}
        .header .subtitle {{
            font-size: 0.9rem; color: rgba(255,255,255,0.4);
            margin-top: 0.5rem; position: relative; z-index: 1;
        }}
        .header .cnpj-badge {{
            display: inline-block; margin-top: 1rem;
            padding: 0.4rem 1.2rem;
            background: rgba(0, 255, 65, 0.12);
            border: 1px solid rgba(0, 255, 65, 0.3);
            border-radius: 30px;
            font-family: 'Courier New', monospace;
            font-size: 1.1rem; font-weight: 600; color: #00ff41;
            position: relative; z-index: 1;
        }}

        /* ==================== SECTION CARD ==================== */
        .section {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px; padding: 1.8rem 2rem;
            margin-bottom: 1.8rem;
            backdrop-filter: blur(10px);
            transition: border-color 0.3s ease;
        }}
        .section:hover {{ border-color: rgba(0, 255, 65, 0.2); }}
        .section-title {{
            font-size: 1.15rem; font-weight: 700; color: #00ff41;
            margin-bottom: 1.2rem; display: flex; align-items: center;
            gap: 0.6rem; text-transform: uppercase; letter-spacing: 1px;
        }}
        .section-title .icon {{ font-size: 1.3rem; }}

        /* ==================== GRID INFO ==================== */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.8rem 1.5rem;
        }}
        .info-item {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .info-item .label {{
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1px; color: rgba(255,255,255,0.3);
            display: block; margin-bottom: 0.2rem;
        }}
        .info-item .value {{
            font-size: 0.95rem; font-weight: 500; color: #f0f0f0;
            word-break: break-word;
        }}
        .info-item .value.highlight {{ color: #00ff41; }}

        /* ==================== BADGES ==================== */
        .badge-code {{
            display: inline-block; padding: 0.2rem 0.6rem;
            background: rgba(0, 200, 255, 0.1);
            border: 1px solid rgba(0, 200, 255, 0.2);
            border-radius: 6px; font-family: 'Courier New', monospace;
            font-size: 0.75rem; color: #00d4ff; font-weight: 600;
            white-space: nowrap;
        }}
        .status-badge {{
            display: inline-block; padding: 0.25rem 0.9rem;
            border-radius: 20px; font-size: 0.8rem; font-weight: 600;
        }}
        .status-ok {{
            background: rgba(0, 255, 65, 0.15); color: #00ff41;
            border: 1px solid rgba(0, 255, 65, 0.3);
        }}
        .status-warn {{
            background: rgba(255, 200, 0, 0.15); color: #ffc800;
            border: 1px solid rgba(255, 200, 0, 0.3);
        }}
        .status-err {{
            background: rgba(255, 0, 50, 0.15); color: #ff0033;
            border: 1px solid rgba(255, 0, 50, 0.3);
        }}

        /* ==================== ATIVIDADES SECUNDÁRIAS ==================== */
        .atividade-sec-item {{
            padding: 0.5rem 0.8rem; margin-bottom: 0.4rem;
            background: rgba(255,255,255,0.02);
            border-radius: 8px; display: flex; align-items: center;
            gap: 0.8rem; flex-wrap: wrap;
        }}
        .atividade-sec-item .atv-desc {{ font-size: 0.9rem; color: #ccc; }}

        /* ==================== QSA CARDS ==================== */
        .socio-card {{
            padding: 1rem 1.2rem; margin-bottom: 0.7rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px; transition: all 0.2s ease;
        }}
        .socio-card:hover {{
            background: rgba(0, 255, 65, 0.04);
            border-color: rgba(0, 255, 65, 0.15);
            transform: translateX(4px);
        }}
        .socio-header {{
            display: flex; align-items: center; gap: 0.8rem;
            flex-wrap: wrap; margin-bottom: 0.3rem;
        }}
        .socio-nome {{ font-weight: 600; font-size: 1rem; color: #fff; }}
        .socio-qual {{
            font-size: 0.8rem; color: rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.06);
            padding: 0.15rem 0.6rem; border-radius: 12px;
        }}
        .socio-entrada {{ font-size: 0.8rem; color: rgba(255,255,255,0.4); }}
        .socio-entrada .label {{ font-weight: 600; color: rgba(255,255,255,0.3); }}

        .nao-encontrado {{
            color: rgba(255,255,255,0.25); font-style: italic; font-size: 0.9rem;
        }}

        /* ==================== FULL-WIDTH ITEMS ==================== */
        .info-full {{ grid-column: 1 / -1; }}

        /* ==================== GOOGLE MAPS LINK ==================== */
        .maps-link-container {{
            margin-top: 1.5rem;
            padding: 1.2rem 1.5rem;
            background: rgba(0, 200, 255, 0.05);
            border: 1px solid rgba(0, 200, 255, 0.15);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .maps-link-container .maps-label {{
            font-size: 0.8rem;
            color: rgba(255,255,255,0.4);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .maps-link-container .maps-coords {{
            font-size: 0.85rem;
            color: rgba(255,255,255,0.5);
            font-family: 'Courier New', monospace;
        }}
        .btn-maps {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.7rem 1.5rem;
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: #000;
            font-weight: 700;
            font-size: 0.9rem;
            border-radius: 30px;
            text-decoration: none;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}
        .btn-maps:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
        }}
        .btn-maps .pin-icon {{ font-size: 1.2rem; }}

        /* ==================== FOOTER ==================== */
        .footer {{
            text-align: center; margin-top: 2.5rem; padding: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.75rem; color: rgba(255,255,255,0.2);
        }}
        .footer span {{ color: #00ff41; }}

        /* ==================== RESPONSIVO ==================== */
        @media (max-width: 640px) {{
            body {{ padding: 1rem 0.6rem; }}
            .section {{ padding: 1.2rem 1rem; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 1.5rem; }}
            .maps-link-container {{ flex-direction: column; text-align: center; }}
        }}

        /* ==================== SCROLLBAR ==================== */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0b0e1a; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(0, 255, 65, 0.2); border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(0, 255, 65, 0.4); }}
    </style>
</head>
<body>
<div class="container">

    <!-- ========== HEADER ========== -->
    <div class="header">
        <h1>RESULTADO DA CONSULTA DO CNPJ</h1>
        <div class="cnpj-badge">{cnpj_raw}</div>
        <div class="subtitle">Dados obtidos Resultado &bull; {atualizacao}</div>
    </div>

    <!-- ========== INFORMAÇÕES GERAIS ========== -->
    <div class="section">
        <div class="section-title"><span class="icon">📋</span> Informações Gerais</div>
        <div class="info-grid">
            <div class="info-item">
                <span class="label">Razão Social</span>
                <span class="value highlight">{razao}</span>
            </div>
            <div class="info-item">
                <span class="label">Nome Fantasia</span>
                <span class="value">{fantasia_val}</span>
            </div>
            <div class="info-item">
                <span class="label">Matriz / Filial</span>
                <span class="value">{tipo}</span>
            </div>
            <div class="info-item">
                <span class="label">Situação Cadastral</span>
                <span class="value"><span class="status-badge status-ok">{situacao}</span></span>
            </div>
            <div class="info-item">
                <span class="label">DATA DA SITUAÇÃO CADASTRAL</span>
                <span class="value">{data_situacao}</span>
            </div>
            <div class="info-item">
                <span class="label">Motivo da Situação</span>
                <span class="value">{motivo_situacao}</span>
            </div>
            <div class="info-item">
                <span class="label">Natureza Jurídica</span>
                <span class="value">{natureza}</span>
            </div>
            <div class="info-item">
                <span class="label">Data de Abertura</span>
                <span class="value">{abertura}</span>
            </div>
            <div class="info-item">
                <span class="label">ATUALIZAÇÃO DESTA PÁGINA</span>
                <span class="value">{atualizacao}</span>
            </div>
            <div class="info-item">
                <span class="label">Idade</span>
                <span class="value highlight">{idade}</span>
            </div>
            <div class="info-item">
                <span class="label">Porte (RFB)</span>
                <span class="value">{porte}</span>
            </div>
            <div class="info-item info-full">
                <span class="label">Capital Social</span>
                <span class="value highlight">R$ {capital}</span>
            </div>
        </div>
    </div>

    <!-- ========== LOCALIZAÇÃO ========== -->
    <div class="section">
        <div class="section-title"><span class="icon">📍</span> Localização</div>
        <div class="info-grid">
            <div class="info-item info-full">
                <span class="label">Endereço</span>
                <span class="value">{logr}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;—&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#00d4ff; font-weight:600;">Número:</span>&nbsp;{num}{f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#FF8C00; font-weight:500;">{comp}</span>' if comp and comp != 'Não informado' else ''}</span>
            </div>
            <div class="info-item">
                <span class="label">Bairro</span>
                <span class="value">{bairro}</span>
            </div>
            <div class="info-item">
                <span class="label">Cidade / Estado</span>
                <span class="value">{municipio} / {uf}</span>
            </div>
            <div class="info-item">
                <span class="label">CEP</span>
                <span class="value">{cep}</span>
            </div>
            <div class="info-item">
                <span class="label">Telefone</span>
                <span class="value">{telefone}</span>
            </div>
            <div class="info-item">
                <span class="label">E-mail</span>
                <span class="value">{email}</span>
            </div>
        </div>

        <!-- ========== GOOGLE MAPS ========== -->
        <div class="maps-link-container">
            <div>
                <div class="maps-label">📍 Geolocalização</div><br>
                <div class="maps-coords">{logr}, {num} — {municipio}/{uf}</div>
            </div>
            <a href="{maps_url}" target="_blank" class="btn-maps">
                <span class="pin-icon">📌</span> ABRIR NO GOOGLE MAPS
            </a>
        </div>
    </div>

    <!-- ========== ATIVIDADE ECONÔMICA PRINCIPAL ========== -->
    <div class="section">
        <div class="section-title"><span class="icon">⚡</span> Atividade Econômica Principal</div>
        <div class="info-grid">
            <div class="info-item">
                <span class="label">Código CNAE</span>
                <span class="value"><span class="badge-code">{cod_principal}</span></span>
            </div>
            <div class="info-item info-full">
                <span class="label">Descrição</span>
                <span class="value">{desc_principal}</span>
            </div>
        </div>
    </div>

    <!-- ========== ATIVIDADES SECUNDÁRIAS ========== -->
    <div class="section">
        <div class="section-title"><span class="icon">🔗</span> Atividades Econômicas Secundárias</div>
        {atividades_sec_html}
    </div>

    <!-- ========== QSA ========== -->
    <div class="section">
        <div class="section-title"><span class="icon">👥</span> Quadro de Sócios e Administradores (QSA)</div>
        {qsa_html}
    </div>

    <!-- ========== FOOTER ========== -->
    <div class="footer">
        Relatório gerado em <span>{datetime.now().strftime('%d/%m/%Y às %H:%M')}</span> &bull; RESULTADO DA CONSULTA DO CNPJ
    </div>

</div>
</body>
</html>"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

def salvar_arquivo(dados_cnpj):
    """Salva APENAS em HTML bonito."""
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
            messagebox.showinfo("Sucesso", f"Relatório HTML salvo com sucesso!\n\n{filename}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar o arquivo:\n{str(e)}")

def consultar_e_mostrar(cnpj_entry, info_text, maps_button, salvar_button):
    cnpj = limpar_cnpj(cnpj_entry.get())
    if not cnpj:
        messagebox.showerror("Erro", "Por favor, insira um CNPJ válido")
        return
    dados_cnpj = consultar_cnpj(cnpj)
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

# ==================== INTERFACE ====================

def criar_interface_grafica():
    global text_area
    root = tk.Tk()
    root.title("CNPJ OSINT ANALYZER")
    root.geometry("1280x900")
    root.state('zoomed')
    root.configure(bg=HackerStyle.BG)

    # Título
    title = tk.Label(root, text="CNPJ OSINT ANALYZER",
                     font=HackerStyle.TITLE_FONT,
                     fg=HackerStyle.FG, bg=HackerStyle.BG)
    title.pack(pady=15)

    # ==================== FRAME SUPERIOR ====================
    top_frame = tk.Frame(root, bg=HackerStyle.BG)
    top_frame.pack(pady=10, fill="x", padx=40)

    # CNPJ Label + Entry
    tk.Label(top_frame, text="CNPJ →", font=HackerStyle.FONT_BOLD,
             fg=HackerStyle.FG, bg=HackerStyle.BG).pack(side="left", padx=(0, 8))

    cnpj_entry = tk.Entry(top_frame, width=32, font=("Consolas", 14),
                          bg="#111111", fg=HackerStyle.FG, insertbackground=HackerStyle.FG)
    cnpj_entry.pack(side="left", padx=4)

    # Botão Consultar
    consultar_button = tk.Button(top_frame, text="▶ CONSULTAR", font=HackerStyle.FONT_BOLD,
                                 bg="#00ff41", fg="black", activebackground="#00cc33", width=15)
    consultar_button.pack(side="left", padx=4)

    # Botão Google Maps
    maps_button = tk.Button(top_frame, text="🗺️ GOOGLE MAPS", font=HackerStyle.FONT_BOLD,
                            bg="#00FFFF", fg="black", state=tk.DISABLED, width=20)
    maps_button.pack(side="left", padx=4)

    # Botão Salvar (agora só HTML)
    salvar_button = tk.Button(top_frame, text="💾 SALVAR HTML", font=HackerStyle.FONT_BOLD,
                              bg="#FF4500", fg="black", state=tk.DISABLED, width=20)
    salvar_button.pack(side="left", padx=4)

    # Botão Abrir Arquivo
    btn_abrir = tk.Button(top_frame, text="📂 ABRIR ARQUIVO HTML", command=abrir_arquivo,
                          font=HackerStyle.FONT_BOLD, bg="#e09c08", fg="black", width=26)
    btn_abrir.pack(side="left", padx=4)

    # ==================== ÁREA DE TEXTO ====================
    text_area = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, width=145, height=38,
        font=("Consolas", 10), bg="#000000", fg=HackerStyle.FG,
        insertbackground=HackerStyle.FG, selectbackground="#00ff41", selectforeground="black"
    )
    text_area.pack(pady=20, padx=40, fill="both", expand=True)
    text_area.config(state=tk.DISABLED)

    # ==================== CONECTAR COMANDOS ====================
    consultar_button.config(command=lambda: consultar_e_mostrar(
        cnpj_entry, text_area, maps_button, salvar_button))

    root.mainloop()

if __name__ == "__main__":    
    criar_interface_grafica()
