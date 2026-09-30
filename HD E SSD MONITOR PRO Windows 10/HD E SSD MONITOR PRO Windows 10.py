import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import threading
import webbrowser
import os
import html
from pathlib import Path
from datetime import datetime

# ============================================================
# SSD MONITOR PRO
# Monitor de Disco / SMART - Windows 10
# ============================================================

BG = "#030603"
PANEL = "#071007"
CARD = "#101a10"

GREEN = "#00ff41"
GREEN_SOFT = "#00b82e"
CYAN = "#00e5ff"
WHITE = "#b8ffb8"
RED = "#ff3333"
YELLOW = "#ffcc00"

# COR DE ALERTA / ABÓBORA
ABOBORA = "#FF8C00"
ABOBORA_ESCURO = "#8A4B00"
ORANGE = ABOBORA  # alias para compatibilidade

MUTED = "#718071"

FONTE = ("Consolas", 10)
FONTE_TITULO = ("Consolas", 24, "bold")


# ============================================================
# VARIÁVEIS
# ============================================================

scan_ativo = False
ultimo_scan_ok = False
ultimo_dados = {}
ultimo_smart = []


# ============================================================
# NOMES SMART EM PORTUGUÊS
# ============================================================

NOMES_SMART = {
    "01": "Taxa de Erros de Leitura",
    "02": "Desempenho",
    "03": "Tempo de Partida",
    "04": "Contagem de Início/Parada",
    "05": "Setores Reatribuídos",
    "06": "Canal de Leitura",
    "07": "Taxa de Erros de Busca",
    "08": "Desempenho de Busca",
    "09": "Horas de Funcionamento",
    "0A": "Contagem de Novas Tentativas de Rotação",
    "0C": "Contagem de Ciclos de Energia",
    "A0": "Erros de Descartes",
    "A1": "Contagem de Bad Blocks",
    "A2": "Percentual de Vida",
    "A3": "Blocos Reservados",
    "A4": "Contagem de Apagamentos",
    "A5": "Máximo de Blocos Ruins",
    "A6": "Blocos Ruins Atuais",
    "B7": "Atributo SMART 183",
    "B8": "Erros de Integridade",
    "BB": "Erros Incorrigíveis",
    "BC": "Tempo Limite de Comando",
    "BD": "Gravações Fora da Especificação",
    "BE": "Temperatura do Fluxo de Ar",
    "C0": "Contagem de Desligamentos Inseguros",
    "C1": "Ciclos de Carga/Descarga",
    "C2": "Temperatura",
    "C3": "Atributo SMART 195",
    "C4": "Eventos de Retração",
    "C5": "Setores Pendentes Atuais",
    "C6": "Setores Incorrigíveis",
    "C7": "Erros CRC UltraDMA",
    "F0": "Horas de Transferência",
    "F1": "Total de Dados Gravados",
    "F2": "Total de Dados Lidos",
}


# ============================================================
# FORMATAÇÃO E TRADUÇÃO
# ============================================================

TRADUCOES_STATUS = {
    # HealthStatus
    "Healthy": "Saudável",
    "Warning": "Atenção",
    "Unhealthy": "Com Defeito / Crítico",
    "Unknown": "Desconhecido",
    # OperationalStatus
    "OK": "OK / Normal",
    "Degraded": "Degradado",
    "Stressed": "Sob Estresse",
    "Predictive Failure": "Falha Prevista",
    "Error": "Erro",
    "Non-Recoverable Error": "Erro Incorrigível",
    "Starting": "Iniciando",
    "Stopping": "Parando",
    "Stopped": "Parado",
    "In Service": "Em Manutenção",
    "No Contact": "Sem Contato",
    "Lost Communication": "Comunicação Perdida",
}


def traduzir_status(valor):
    if not valor or str(valor).strip() == "" or str(valor) == "0":
        return "N/D"
    texto = str(valor).strip()
    return TRADUCOES_STATUS.get(texto, texto)


def formatar_bytes(valor):
    try:
        valor = float(valor)
    except Exception:
        return "N/D"

    if valor <= 0:
        return "N/D"

    unidades = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    i = 0

    while valor >= 1024 and i < len(unidades) - 1:
        valor /= 1024
        i += 1

    if i == 0:
        return f"{int(valor)} {unidades[i]}"

    return f"{valor:.2f} {unidades[i]}"


def formatar_capacidade(valor):
    try:
        valor = float(valor)
    except Exception:
        return "N/D"

    if valor <= 0:
        return "N/D"

    return f"{valor / (1024 ** 3):.2f} GB"


def formatar_tempo_funcionamento(horas_total):
    try:
        horas_total = int(float(horas_total))
    except Exception:
        return "N/D"

    if horas_total < 0:
        return "N/D"

    dias = horas_total // 24
    horas = horas_total % 24

    anos = dias // 365
    dias_restantes = dias % 365

    meses = dias_restantes // 30
    dias_finais = dias_restantes % 30

    partes = []

    if anos:
        partes.append(f"{anos} ano" if anos == 1 else f"{anos} anos")

    if meses:
        partes.append(f"{meses} mês" if meses == 1 else f"{meses} meses")

    if dias_finais:
        partes.append(
            f"{dias_finais} dia" if dias_finais == 1 else f"{dias_finais} dias"
        )

    if horas:
        partes.append(f"{horas} hora" if horas == 1 else f"{horas} horas")

    if not partes:
        partes.append("0 horas")

    return " • ".join(partes)


# ============================================================
# POWERSHELL OTIMIZADO PARA RODAR EM BACKGROUND SEM JANELA
# ============================================================

def executar_powershell(comando, timeout=30):
    try:
        # Configura as informações de inicialização do processo para ocultar a janela no Windows
        startupinfo = None
        creationflags = 0
        
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # Equivalente a SW_HIDE (Ocultar Janela)
            creationflags = subprocess.CREATE_NO_WINDOW  # Impede a criação de console do CMD/PowerShell

        resultado = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                comando
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        if resultado.returncode != 0:
            return None

        texto = resultado.stdout.strip()

        if not texto:
            return None

        return texto

    except Exception:
        return None


# ============================================================
# INFORMAÇÕES DO DISCO
# ============================================================

def consultar_ssd():
    comando = r'''
$erro = $null

try {

    $particao = Get-Partition -DriveLetter C -ErrorAction SilentlyContinue

    $disco = $null

    if ($particao) {
        $disco = Get-Disk -Number $particao.DiskNumber -ErrorAction SilentlyContinue
    }

    if (-not $disco) {
        $disco = Get-Disk |
            Where-Object { $_.IsBoot -eq $true } |
            Select-Object -First 1
    }

    if (-not $disco) {
        $disco = Get-Disk | Select-Object -First 1
    }

    $fisico = $null

    if ($disco) {
        $fisico = Get-PhysicalDisk -ErrorAction SilentlyContinue |
            Where-Object { $_.DeviceId -eq [string]$disco.Number } |
            Select-Object -First 1
    }

    if (-not $fisico) {
        $fisico = Get-PhysicalDisk -ErrorAction SilentlyContinue |
            Select-Object -First 1
    }

    $contador = $null

    if ($disco) {
        $contador = Get-StorageReliabilityCounter `
            -PhysicalDisk $fisico `
            -ErrorAction SilentlyContinue
    }

    $obj = [ordered]@{
        NumeroDisco = if ($disco) { $disco.Number } else { 0 }
        DeviceId = if ($fisico) { $fisico.DeviceId } else { 0 }
        NomeAmigavel = if ($fisico) { $fisico.FriendlyName } else { $disco.FriendlyName }
        Modelo = if ($fisico) { $fisico.Model } else { $disco.Model }
        NumeroSerie = if ($fisico) { $fisico.SerialNumber } else { $disco.SerialNumber }
        FirmwareVersion = if ($fisico) { $fisico.FirmwareVersion } else { "" }
        Fabricante = if ($fisico) { $fisico.Manufacturer } else { "" }
        TipoMidia = if ($fisico) { $fisico.MediaType } else { "" }
        TipoConexao = if ($fisico) { $fisico.BusType } else { $disco.BusType }
        StatusOperacional = if ($fisico) { $fisico.OperationalStatus } else { "" }
        StatusSaude = if ($fisico) { $fisico.HealthStatus } else { $disco.HealthStatus }
        Saude = if ($fisico) { $fisico.HealthStatus } else { $disco.HealthStatus }
        Capacidade = if ($fisico) { $fisico.Size } else { $disco.Size }
        Tamanho = if ($disco) { $disco.Size } else { 0 }
        SetorFisico = if ($disco) { $disco.PhysicalSectorSize } else { 0 }
        SetorLogico = if ($disco) { $disco.LogicalSectorSize } else { 0 }
        DiscoInicializacao = if ($disco) { $disco.IsBoot } else { $false }
        DiscoSistema = if ($disco) { $disco.IsSystem } else { $false }
        SomenteLeitura = if ($disco) { $disco.IsReadOnly } else { $false }
        Desgaste = if ($contador) { $contador.Wear } else { 0 }
        Temperatura = if ($contador) { $contador.Temperature } else { 0 }
        TemperaturaMaxima = if ($contador) { $contador.TemperatureMax } else { 0 }
        HorasFuncionamento = if ($contador) { $contador.PowerOnHours } else { 0 }
        BytesLidos = if ($contador) { $contador.ReadBytes } else { 0 }
        BytesGravados = if ($contador) { $contador.WriteBytes } else { 0 }
        ErrosLeitura = if ($contador) { $contador.ReadErrorsTotal } else { 0 }
        ErrosGravacao = if ($contador) { $contador.WriteErrorsTotal } else { 0 }
        ErrosNaoCorrigidos = if ($contador) { $contador.UncorrectableErrors } else { 0 }
    }

    $obj | ConvertTo-Json -Depth 5

}
catch {
    @{ erro = $_.Exception.Message } | ConvertTo-Json
}
'''

    texto = executar_powershell(comando, timeout=40)

    if not texto:
        raise RuntimeError("Não foi possível obter as informações do disco.")

    try:
        dados = json.loads(texto)
    except Exception:
        raise RuntimeError("O Windows retornou informações inválidas.")

    if "erro" in dados:
        raise RuntimeError(str(dados["erro"]))

    return dados


# ============================================================
# SMART VIA WMI
# ============================================================

def obter_dados_smart():
    comando = r'''
$lista = @()

try {

    $dados = Get-CimInstance `
        -Namespace root\wmi `
        -ClassName MSStorageDriver_FailurePredictData `
        -ErrorAction SilentlyContinue

    foreach ($item in $dados) {

        $bytes = @($item.VendorSpecific)

        if ($bytes.Count -gt 2) {
            $obj = [ordered]@{
                Instancia = $item.InstanceName
                Bytes = $bytes
            }
            $lista += $obj
        }
    }

    $lista | ConvertTo-Json -Depth 5

}
catch {
    @() | ConvertTo-Json
}
'''

    texto = executar_powershell(comando, timeout=30)

    if not texto:
        return []

    try:
        dados = json.loads(texto)
    except Exception:
        return []

    if isinstance(dados, dict):
        dados = [dados]

    resultado = []

    for item in dados:
        try:
            bytes_smart = item.get("Bytes", [])

            if len(bytes_smart) < 3:
                continue

            atributos = []

            for pos in range(2, len(bytes_smart) - 11, 12):
                attr_id = int(bytes_smart[pos])

                if attr_id == 0:
                    continue

                flags = (
                    int(bytes_smart[pos + 1])
                    | (int(bytes_smart[pos + 2]) << 8)
                )

                valor_atual = int(bytes_smart[pos + 3])
                pior_valor = int(bytes_smart[pos + 4])

                raw_bytes = bytes_smart[pos + 5:pos + 11]

                bruto = 0

                for i, b in enumerate(raw_bytes):
                    bruto |= int(b) << (8 * i)

                atributos.append({
                    "id": f"{attr_id:02X}",
                    "nome": NOMES_SMART.get(
                        f"{attr_id:02X}",
                        f"Atributo SMART {attr_id:02X}"
                    ),
                    "atual": valor_atual,
                    "pior": pior_valor,
                    "limiar": 0,
                    "bruto": bruto,
                    "bruto_hex": "".join(
                        f"{int(x):02X}" for x in reversed(raw_bytes)
                    )
                })

            if atributos:
                resultado.extend(atributos)

        except Exception:
            continue

    unicos = {}

    for item in resultado:
        unicos[item["id"]] = item

    return list(unicos.values())


# ============================================================
# ANÁLISE DOS RESULTADOS SMART
# ============================================================

def analisar_smart(atributos):
    alertas = []
    criticos = []

    for attr in atributos:
        attr_id = attr["id"].upper()

        try:
            atual = int(attr.get("atual", 0))
        except Exception:
            atual = 0

        try:
            pior = int(attr.get("pior", 0))
        except Exception:
            pior = 0

        try:
            limiar = int(attr.get("limiar", 0))
        except Exception:
            limiar = 0

        try:
            bruto = int(attr.get("bruto", 0))
        except Exception:
            bruto = 0

        if attr_id == "05" and bruto > 0:
            criticos.append({
                "id": attr_id,
                "nome": "Setores Reatribuídos",
                "motivo": f"{bruto} setor(es) reatribuído(s).",
                "bruto": attr.get("bruto_hex", "")
            })

        elif attr_id == "C5" and bruto > 0:
            criticos.append({
                "id": attr_id,
                "nome": "Setores Pendentes Atuais",
                "motivo": f"{bruto} setor(es) pendente(s).",
                "bruto": attr.get("bruto_hex", "")
            })

        elif attr_id == "C6" and bruto > 0:
            criticos.append({
                "id": attr_id,
                "nome": "Setores Incorrigíveis",
                "motivo": f"{bruto} setor(es) não corrigível(is).",
                "bruto": attr.get("bruto_hex", "")
            })

        elif attr_id == "C7" and bruto > 0:
            alertas.append({
                "id": attr_id,
                "nome": "Erros CRC UltraDMA",
                "motivo": f"Foram registrados {bruto} erro(s) CRC.",
                "bruto": attr.get("bruto_hex", "")
            })

        elif attr_id == "BB" and bruto > 0:
            criticos.append({
                "id": attr_id,
                "nome": "Erros Incorrigíveis",
                "motivo": (
                    f"Foram registrados {bruto} erro(s) incorrigível(is)."
                ),
                "bruto": attr.get("bruto_hex", "")
            })

        elif attr_id == "BC":
            if atual <= limiar and limiar > 0:
                alertas.append({
                    "id": attr_id,
                    "nome": "Tempo Limite de Comando",
                    "motivo": (
                        "O valor normalizado atingiu "
                        "ou ficou abaixo do limiar."
                    ),
                    "bruto": attr.get("bruto_hex", "")
                })

        elif limiar > 0 and atual > 0 and atual <= limiar:
            alertas.append({
                "id": attr_id,
                "nome": attr["nome"],
                "motivo": (
                    f"Valor atual ({atual}) atingiu o limiar ({limiar})."
                ),
                "bruto": attr.get("bruto_hex", "")
            })

    return criticos, alertas


# ============================================================
# STATUS GERAL
# ============================================================

def obter_status_smart(atributos):
    criticos, alertas = analisar_smart(atributos)

    if criticos:
        return "CRÍTICO", RED

    if alertas:
        return "ATENÇÃO", ORANGE

    return "SAUDÁVEL", GREEN


# ============================================================
# CRIAÇÃO DA INTERFACE
# ============================================================

app = tk.Tk()
app.title("HD E SSD MONITOR PRO • Windows 10")
app.geometry("1150x850")
app.minsize(900, 700)
app.configure(bg=BG)


# ============================================================
# ESTILO
# ============================================================

style = ttk.Style()

try:
    style.theme_use("clam")
except Exception:
    pass

style.configure(
    "Monitor.Horizontal.TProgressbar",
    troughcolor="#101810",
    background=GREEN,
    bordercolor="#101810",
    lightcolor=GREEN,
    darkcolor=GREEN,
)

style.configure(
    "Treeview",
    background=PANEL,
    foreground=GREEN,
    fieldbackground=PANEL,
    rowheight=25,
    font=FONTE
)
style.map('Treeview', background=[('selected', '#1a331a')])

style.configure(
    "Treeview.Heading",
    background="#0a1a0a",
    foreground=CYAN,
    font=("Consolas", 10, "bold"),
    relief="flat"
)
style.map("Treeview.Heading", background=[('active', '#102610')])

# ============================================================
# MAXIMIZAR
# ============================================================

try:
    app.state("zoomed")
except:
    try:
        app.attributes("-zoomed", True)
    except:
        pass


# ============================================================
# CABEÇALHO
# ============================================================

header = tk.Frame(app, bg=BG)
header.pack(fill="x", padx=25, pady=(18, 5))

titulo = tk.Label(
    header,
    text="HD E SSD MONITOR PRO • Windows 10",
    bg=BG,
    fg=GREEN,
    font=FONTE_TITULO
)
titulo.pack(side="left")

status_label = tk.Label(
    header,
    text="● AGUARDANDO SCAN",
    bg=BG,
    fg=MUTED,
    font=("Consolas", 11, "bold")
)
status_label.pack(side="right")


# ============================================================
# ÁREA DOS BOTÕES — TOPO FIXO
# ============================================================

area_botoes_topo = tk.Frame(app, bg=BG)
area_botoes_topo.pack(fill="x", padx=25, pady=(5, 12))

linha_botoes = tk.Frame(area_botoes_topo, bg=BG)
linha_botoes.pack(anchor="center")


def criar_botao(parent, texto, comando, bg_cor, fg_cor, largura=20):
    botao = tk.Button(
        parent,
        text=texto,
        command=comando,
        font=("Consolas", 12, "bold"),
        bg=bg_cor,
        fg=fg_cor,
        activebackground=CYAN,
        activeforeground="#000000",
        relief="flat",
        bd=0,
        cursor="hand2",
        width=largura,
        height=2
    )
    return botao


botao_scan = criar_botao(
    linha_botoes,
    "🔍 SCANEAR DISCO",
    lambda: iniciar_scan(),
    GREEN,
    "#000000",
    23
)
botao_scan.pack(side="left", padx=5)

botao_detalhes = criar_botao(
    linha_botoes,
    "ℹ INFORMAÇÕES DO DISCO",
    lambda: mostrar_detalhes(),
    "#182418",
    CYAN,
    25
)
botao_detalhes.pack(side="left", padx=5)

botao_smart = criar_botao(
    linha_botoes,
    "📊 RESULTADOS SMART",
    lambda: mostrar_resultados_smart(),
    "#182418",
    WHITE,
    24
)
botao_smart.pack(side="left", padx=5)

botao_salvar = criar_botao(
    linha_botoes,
    "💾 SALVAR HTML",
    lambda: salvar_relatorio_html(),
    CYAN,
    "#000000",
    20
)
botao_salvar.pack(side="left", padx=5)


# ============================================================
# PAINEL PRINCIPAL COM SCROLL
# ============================================================

container = tk.Frame(app, bg=BG)
container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
conteudo = tk.Frame(canvas, bg=BG)

conteudo.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_window = canvas.create_window((0, 0), window=conteudo, anchor="nw")


def ajustar_largura_canvas(event):
    canvas.itemconfig(canvas_window, width=event.width)


canvas.bind("<Configure>", ajustar_largura_canvas)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# ============================================================
# IDENTIFICAÇÃO
# ============================================================

frame_identificacao = tk.LabelFrame(
    conteudo,
    text="  IDENTIFICAÇÃO DO DISCO  ",
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 12, "bold"),
    bd=1,
    relief="solid"
)
frame_identificacao.pack(fill="x", padx=10, pady=5)

lbl_modelo = tk.Label(
    frame_identificacao,
    text="Modelo: —",
    bg=PANEL,
    fg=WHITE,
    font=FONTE,
    anchor="w"
)
lbl_modelo.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

lbl_serial = tk.Label(
    frame_identificacao,
    text="Número de série: —",
    bg=PANEL,
    fg=WHITE,
    font=FONTE,
    anchor="w"
)
lbl_serial.grid(row=0, column=1, sticky="ew", padx=15, pady=10)

lbl_capacidade = tk.Label(
    frame_identificacao,
    text="Capacidade: —",
    bg=PANEL,
    fg=WHITE,
    font=FONTE,
    anchor="w"
)
lbl_capacidade.grid(row=1, column=0, sticky="ew", padx=15, pady=10)

lbl_tipo = tk.Label(
    frame_identificacao,
    text="Tipo de mídia: —",
    bg=PANEL,
    fg=WHITE,
    font=FONTE,
    anchor="w"
)
lbl_tipo.grid(row=1, column=1, sticky="ew", padx=15, pady=10)

frame_identificacao.columnconfigure(0, weight=1)
frame_identificacao.columnconfigure(1, weight=1)


# ============================================================
# CARDS
# ============================================================

frame_cards = tk.Frame(conteudo, bg=BG)
frame_cards.pack(fill="x", padx=10, pady=8)

cards = {}


def criar_card(parent, titulo_card, row, column):
    frame = tk.Frame(parent, bg=CARD, bd=1, relief="solid")
    frame.grid(
        row=row,
        column=column,
        sticky="nsew",
        padx=5,
        pady=5,
        ipadx=8,
        ipady=8
    )

    tk.Label(
        frame,
        text=titulo_card,
        bg=CARD,
        fg=MUTED,
        font=("Consolas", 12, "bold")
    ).pack(pady=(3, 5))

    valor = tk.Label(
        frame,
        text="—",
        bg=CARD,
        fg=GREEN,
        font=("Consolas", 14, "bold")
    )
    valor.pack(pady=(0, 5))

    cards[titulo_card] = valor
    return frame


for i in range(3):
    frame_cards.columnconfigure(i, weight=1)

criar_card(frame_cards, "VIDA ÚTIL", 0, 0)
criar_card(frame_cards, "TEMPERATURA", 0, 1)
criar_card(frame_cards, "HORAS DE FUNCIONAMENTO", 0, 2)
criar_card(frame_cards, "DADOS LIDOS", 1, 0)
criar_card(frame_cards, "DADOS GRAVADOS", 1, 1)
criar_card(frame_cards, "ERROS DE LEITURA", 1, 2)
criar_card(frame_cards, "ERROS DE GRAVAÇÃO", 2, 0)
criar_card(frame_cards, "ERROS NÃO CORRIGIDOS", 2, 1)
criar_card(frame_cards, "SAÚDE DO DISCO", 2, 2)


# ============================================================
# BARRA DE VIDA ÚTIL
# ============================================================

frame_vida = tk.LabelFrame(
    conteudo,
    text="  VIDA ÚTIL / DESGASTE  ",
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 12, "bold")
)
frame_vida.pack(fill="x", padx=10, pady=8)

progress_vida = ttk.Progressbar(
    frame_vida,
    style="Monitor.Horizontal.TProgressbar",
    orient="horizontal",
    mode="determinate",
    maximum=100
)
progress_vida.pack(fill="x", padx=15, pady=12)

label_vida = tk.Label(
    frame_vida,
    text="Vida útil: —",
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 12, "bold")
)
label_vida.pack(pady=(0, 10))


# ============================================================
# SCAN
# ============================================================

frame_scan = tk.LabelFrame(
    conteudo,
    text="  MONITORAMENTO  ",
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 12, "bold")
)
frame_scan.pack(fill="x", padx=10, pady=8)

progress_scan = ttk.Progressbar(
    frame_scan,
    style="Monitor.Horizontal.TProgressbar",
    orient="horizontal",
    mode="determinate",
    maximum=100
)
progress_scan.pack(fill="x", padx=15, pady=(15, 8))

label_percentual = tk.Label(
    frame_scan,
    text="0%",
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 12, "bold")
)
label_percentual.pack()

label_scan = tk.Label(
    frame_scan,
    text="Aguardando ação. Clique em 'SCANEAR DISCO' para iniciar.",
    bg=PANEL,
    fg=MUTED,
    font=FONTE
)
label_scan.pack(pady=(5, 15))


# ============================================================
# FUNÇÕES DE INTERFACE
# ============================================================

def atualizar_status(texto, cor):
    status_label.config(text=texto, fg=cor)


def atualizar_cards(dados):
    modelo = dados.get("Modelo", dados.get("NomeAmigavel", "N/D"))
    serial = dados.get("NumeroSerie", "N/D")
    capacidade = dados.get("Capacidade", dados.get("Tamanho", 0))
    tipo = dados.get("TipoMidia", "N/D")

    lbl_modelo.config(text=f"Modelo: {modelo}")
    lbl_serial.config(text=f"Número de série: {serial}")
    lbl_capacidade.config(text=f"Capacidade: {formatar_capacidade(capacidade)}")
    lbl_tipo.config(text=f"Tipo de mídia: {tipo}")

    try:
        desgaste = int(float(dados.get("Desgaste", 0) or 0))
    except Exception:
        desgaste = 0

    if desgaste < 0:
        desgaste = 0

    if desgaste > 100:
        desgaste = 100

    vida = 100 - desgaste

    cards["VIDA ÚTIL"].config(
        text=f"{vida}%",
        fg=GREEN if vida >= 30 else ORANGE
    )

    progress_vida["value"] = vida
    label_vida.config(text=f"Vida útil restante: {vida}%")

    try:
        temperatura = int(float(dados.get("Temperatura", 0) or 0))
    except Exception:
        temperatura = 0

    cor_temp = GREEN

    if temperatura >= 55:
        cor_temp = ORANGE

    if temperatura >= 65:
        cor_temp = RED

    cards["TEMPERATURA"].config(text=f"{temperatura} °C", fg=cor_temp)

    horas = dados.get("HorasFuncionamento", 0)

    try:
        horas_int = int(float(horas or 0))
    except Exception:
        horas_int = 0

    cards["HORAS DE FUNCIONAMENTO"].config(
        text=formatar_tempo_funcionamento(horas_int),
        font=("Consolas", 10, "bold")
    )

    lidos = dados.get("BytesLidos", 0)
    gravados = dados.get("BytesGravados", 0)

    cards["DADOS LIDOS"].config(text=formatar_bytes(lidos))
    cards["DADOS GRAVADOS"].config(text=formatar_bytes(gravados))

    leitura = dados.get("ErrosLeitura", 0)
    gravacao = dados.get("ErrosGravacao", 0)
    incorrigiveis = dados.get("ErrosNaoCorrigidos", 0)

    cards["ERROS DE LEITURA"].config(
        text=str(leitura if leitura is not None else 0),
        fg=GREEN if not leitura else ORANGE
    )

    cards["ERROS DE GRAVAÇÃO"].config(
        text=str(gravacao if gravacao is not None else 0),
        fg=GREEN if not gravacao else ORANGE
    )

    cards["ERROS NÃO CORRIGIDOS"].config(
        text=str(incorrigiveis if incorrigiveis is not None else 0),
        fg=GREEN if not incorrigiveis else RED
    )

    saude_raw = dados.get("Saude", dados.get("StatusSaude", "N/D"))
    saude_pt = traduzir_status(saude_raw)

    if saude_pt.upper() in ("SAUDÁVEL", "OK / NORMAL"):
        cards["SAÚDE DO DISCO"].config(text=saude_pt.upper(), fg=GREEN)
    else:
        cards["SAÚDE DO DISCO"].config(text=saude_pt.upper(), fg=ORANGE)


# ============================================================
# ANIMAÇÃO DO SCAN
# ============================================================

def animar_progresso():
    if not scan_ativo:
        return

    valor = progress_scan["value"]

    if valor < 85:
        valor += 2
        progress_scan["value"] = valor
        label_percentual.config(text=f"{int(valor)}%")
        app.after(100, animar_progresso)


# ============================================================
# FINALIZAR SCAN
# ============================================================

def finalizar_scan(dados, smart):
    global scan_ativo, ultimo_scan_ok, ultimo_dados, ultimo_smart

    scan_ativo = False
    ultimo_scan_ok = True
    ultimo_dados = dict(dados)
    ultimo_smart = list(smart)

    progress_scan["value"] = 100
    label_percentual.config(text="100%")

    atualizar_cards(dados)

    criticos, alertas = analisar_smart(smart)

    if criticos:
        atualizar_status("● ALERTA CRÍTICO", RED)
        label_scan.config(
            text=f"Análise concluída — {len(criticos)} problema(s) crítico(s)",
            fg=RED
        )
    elif alertas:
        atualizar_status("● ATENÇÃO", ORANGE)
        label_scan.config(
            text=f"Análise concluída — {len(alertas)} alerta(s)",
            fg=ORANGE
        )
    else:
        atualizar_status("● DISCO SAUDÁVEL", GREEN)
        label_scan.config(
            text="Análise concluída — nenhum alerta crítico detectado",
            fg=GREEN
        )

    botao_scan.config(state="normal")


# ============================================================
# THREAD
# ============================================================

def executar_thread():
    global scan_ativo

    try:
        label_scan.config(
            text="Consultando informações do disco...",
            fg=CYAN
        )

        dados = consultar_ssd()

        label_scan.config(
            text="Consultando resultados SMART...",
            fg=CYAN
        )

        smart = obter_dados_smart()

        app.after(0, lambda: finalizar_scan(dados, smart))

    except Exception as erro:
        scan_ativo = False
        mensagem_erro = str(erro)
        app.after(0, lambda: erro_scan(mensagem_erro))


# ============================================================
# ERRO NO SCAN
# ============================================================

def erro_scan(mensagem):
    global scan_ativo, ultimo_scan_ok

    scan_ativo = False
    ultimo_scan_ok = False

    atualizar_status("● ERRO", RED)
    label_scan.config(text=f"Erro: {mensagem}", fg=RED)
    botao_scan.config(state="normal")

    messagebox.showerror("HD E SSD MONITOR PRO • Windows 10", mensagem)


# ============================================================
# INICIAR SCAN
# ============================================================

def iniciar_scan():
    global scan_ativo

    if scan_ativo:
        return

    scan_ativo = True
    botao_scan.config(state="disabled")
    atualizar_status("● ANALISANDO...", CYAN)
    progress_scan["value"] = 0
    label_percentual.config(text="0%")
    label_scan.config(text="Iniciando análise...", fg=CYAN)

    animar_progresso()

    thread = threading.Thread(target=executar_thread, daemon=True)
    thread.start()


# ============================================================
# INFORMAÇÕES DO DISCO
# ============================================================

def mostrar_detalhes():
    if not ultimo_scan_ok:
        messagebox.showwarning(
            "INFORMAÇÕES DO DISCO",
            "Execute primeiro o SCANEAR DISCO."
        )
        return

    janela = tk.Toplevel(app)
    janela.title("HD E SSD MONITOR PRO • Windows 10 — Informações do Disco")
    janela.geometry("1000x840")
    janela.minsize(750, 500)
    janela.configure(bg=BG)

    titulo_janela = tk.Label(
        janela,
        text="INFORMAÇÕES DO DISCO",
        bg=BG,
        fg=GREEN,
        font=("Consolas", 18, "bold")
    )
    titulo_janela.pack(pady=15)

    frame = tk.Frame(janela, bg=PANEL)
    frame.pack(fill="both", expand=True, padx=15, pady=10)

    colunas = ("informacao", "valor")

    tree = ttk.Treeview(frame, columns=colunas, show="headings")

    tree.heading("informacao", text="INFORMAÇÃO")
    tree.heading("valor", text="VALOR")

    tree.column("informacao", width=300, anchor="w")
    tree.column("valor", width=600, anchor="w")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    dados = ultimo_dados

    informacoes = [
        ("Número do disco", dados.get("NumeroDisco", "N/D")),
        ("Identificador do dispositivo", dados.get("DeviceId", "N/D")),
        ("Nome amigável", dados.get("NomeAmigavel", "N/D")),
        ("Modelo", dados.get("Modelo", "N/D")),
        ("Número de série", dados.get("NumeroSerie", "N/D")),
        ("Versão do firmware", dados.get("FirmwareVersion", "N/D")),
        ("Fabricante", dados.get("Fabricante", "N/D")),
        ("Tipo de mídia", dados.get("TipoMidia", "N/D")),
        ("Tipo de conexão", dados.get("TipoConexao", "N/D")),
        ("Status operacional", traduzir_status(dados.get("StatusOperacional"))),
        ("Status de saúde", traduzir_status(dados.get("StatusSaude"))),
        ("Saúde", traduzir_status(dados.get("Saude"))),
        ("Capacidade", formatar_capacidade(dados.get("Capacidade", 0))),
        ("Tamanho", formatar_capacidade(dados.get("Tamanho", 0))),
        ("Tamanho do setor físico", dados.get("SetorFisico", "N/D")),
        ("Tamanho do setor lógico", dados.get("SetorLogico", "N/D")),
        (
            "Disco de inicialização",
            "Sim" if dados.get("DiscoInicializacao", False) else "Não"
        ),
        (
            "Disco do sistema",
            "Sim" if dados.get("DiscoSistema", False) else "Não"
        ),
        (
            "Somente leitura",
            "Sim" if dados.get("SomenteLeitura", False) else "Não"
        ),
        ("Desgaste", f"{dados.get('Desgaste', 0)}%"),
        ("Temperatura", f"{dados.get('Temperatura', 0)} °C"),
        ("Temperatura máxima", f"{dados.get('TemperaturaMaxima', 0)} °C"),
        (
            "Horas de funcionamento",
            (
                f"{formatar_tempo_funcionamento(dados.get('HorasFuncionamento', 0))} "
                f"({dados.get('HorasFuncionamento', 0)} horas)"
            )
        ),
        ("Dados lidos", formatar_bytes(dados.get("BytesLidos", 0))),
        ("Dados gravados", formatar_bytes(dados.get("BytesGravados", 0))),
        ("Erros de leitura", dados.get("ErrosLeitura", 0)),
        ("Erros de gravação", dados.get("ErrosGravacao", 0)),
        ("Erros não corrigidos", dados.get("ErrosNaoCorrigidos", 0)),
    ]

    for nome, valor in informacoes:
        tree.insert("", "end", values=(nome, str(valor)))


# ============================================================
# RESULTADOS SMART
# ============================================================

def mostrar_resultados_smart():
    if not ultimo_scan_ok:
        messagebox.showwarning(
            "RESULTADOS SMART",
            "Execute primeiro o SCANEAR DISCO."
        )
        return

    janela = tk.Toplevel(app)
    janela.title("HD E SSD MONITOR PRO • Windows 10 — Resultados SMART")
    janela.geometry("1150x820")
    janela.minsize(850, 500)
    janela.configure(bg=BG)

    criticos, alertas = analisar_smart(ultimo_smart)

    if criticos:
        texto_status = "🔴 PROBLEMAS CRÍTICOS DETECTADOS"
        cor_status = RED
    elif alertas:
        texto_status = "🟠 ATENÇÃO"
        cor_status = ORANGE
    else:
        texto_status = "🟢 SMART SAUDÁVEL"
        cor_status = GREEN

    label_status = tk.Label(
        janela,
        text=texto_status,
        bg=BG,
        fg=cor_status,
        font=("Consolas", 15, "bold")
    )
    label_status.pack(pady=(15, 5))

    if not criticos and not alertas:
        mensagem = (
            "Nenhum indicador SMART crítico foi detectado.\n"
            "O atributo BC não é considerado defeito apenas "
            "porque possui valor bruto diferente de zero."
        )
        tk.Label(
            janela,
            text=mensagem,
            bg=BG,
            fg=GREEN,
            font=FONTE,
            justify="center"
        ).pack(pady=(0, 12))
    elif criticos:
        mensagem = "Existem indicadores que merecem atenção imediata."
        tk.Label(
            janela,
            text=mensagem,
            bg=BG,
            fg=RED,
            font=FONTE
        ).pack(pady=(0, 12))
    else:
        mensagem = (
            "Existem avisos SMART, mas nenhum indicador "
            "crítico foi identificado."
        )
        tk.Label(
            janela,
            text=mensagem,
            bg=BG,
            fg=ORANGE,
            font=FONTE
        ).pack(pady=(0, 12))

    frame = tk.Frame(janela, bg=PANEL)
    frame.pack(fill="both", expand=True, padx=15, pady=10)

    colunas = ("id", "nome", "atual", "pior", "limiar", "bruto", "status")

    tree = ttk.Treeview(frame, columns=colunas, show="headings")

    titulos = {
        "id": "ID",
        "nome": "NOME DO ATRIBUTO",
        "atual": "ATUAL",
        "pior": "PIOR VALOR",
        "limiar": "LIMIAR",
        "bruto": "VALOR BRUTO",
        "status": "STATUS"
    }

    for coluna in colunas:
        tree.heading(coluna, text=titulos[coluna])

    tree.column("id", width=55, anchor="center")
    tree.column("nome", width=330, anchor="w")
    tree.column("atual", width=90, anchor="center")
    tree.column("pior", width=100, anchor="center")
    tree.column("limiar", width=90, anchor="center")
    tree.column("bruto", width=190, anchor="center")
    tree.column("status", width=160, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    for attr in ultimo_smart:
        attr_id = attr["id"]

        status = "NORMAL"
        tag = "normal"

        if any(x["id"] == attr_id for x in criticos):
            status = "CRÍTICO"
            tag = "critico"
        elif any(x["id"] == attr_id for x in alertas):
            status = "ATENÇÃO"
            tag = "alerta"

        tree.insert(
            "",
            "end",
            values=(
                attr_id,
                attr["nome"],
                attr["atual"],
                attr["pior"],
                attr["limiar"],
                attr["bruto_hex"],
                status
            ),
            tags=(tag,)
        )

    tree.tag_configure("normal", foreground=GREEN)
    tree.tag_configure("alerta", foreground=ORANGE)
    tree.tag_configure("critico", foreground=RED)

    if criticos or alertas:
        frame_alertas = tk.Frame(janela, bg="#140b03")
        frame_alertas.pack(fill="x", padx=15, pady=(0, 15))

        if criticos:
            for alerta in criticos:
                texto = (
                    f"🔴 ID {alerta['id']} - "
                    f"{alerta['nome']}: "
                    f"{alerta['motivo']}"
                )
                tk.Label(
                    frame_alertas,
                    text=texto,
                    bg="#140b03",
                    fg=RED,
                    font=("Consolas", 9, "bold"),
                    anchor="w",
                    justify="left"
                ).pack(fill="x", padx=10, pady=3)

        if alertas:
            for alerta in alertas:
                texto = (
                    f"🟠 ID {alerta['id']} - "
                    f"{alerta['nome']}: "
                    f"{alerta['motivo']}"
                )
                tk.Label(
                    frame_alertas,
                    text=texto,
                    bg="#140b03",
                    fg=ORANGE,
                    font=("Consolas", 9, "bold"),
                    anchor="w",
                    justify="left"
                ).pack(fill="x", padx=10, pady=3)


# ============================================================
# HTML
# ============================================================

def salvar_relatorio_html():
    if not ultimo_scan_ok:
        messagebox.showwarning(
            "SALVAR HTML",
            "Execute primeiro o SCANEAR DISCO."
        )
        return

    caminho = filedialog.asksaveasfilename(
        title="Salvar relatório HTML",
        defaultextension=".html",
        filetypes=[
            ("Página HTML", "*.html"),
            ("Todos os arquivos", "*.*")
        ],
        initialfile=(
            "SSD_MONITOR_PRO_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".html"
        )
    )

    if not caminho:
        return

    dados = ultimo_dados
    criticos, alertas = analisar_smart(ultimo_smart)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if criticos:
        status_texto = "ALERTA CRÍTICO DETECTADO"
        status_classe = "critico"
    elif alertas:
        status_texto = "ATENÇÃO"
        status_classe = "alerta"
    else:
        status_texto = "DISCO SAUDÁVEL"
        status_classe = "normal"

    modelo = html.escape(str(dados.get("Modelo", "N/D")))
    serial = html.escape(str(dados.get("NumeroSerie", "N/D")))
    tipo = html.escape(str(dados.get("TipoMidia", "N/D")))
    capacidade = formatar_capacidade(dados.get("Capacidade", 0))
    horas = dados.get("HorasFuncionamento", 0)
    tempo = formatar_tempo_funcionamento(horas)

    html_smart = ""

    for attr in ultimo_smart:
        eh_critico = any(x["id"] == attr["id"] for x in criticos)
        eh_alerta = any(x["id"] == attr["id"] for x in alertas)

        if eh_critico:
            classe = "critico"
            status = "CRÍTICO"
        elif eh_alerta:
            classe = "alerta"
            status = "ATENÇÃO"
        else:
            classe = "normal"
            status = "NORMAL"

        html_smart += f"""
        <tr class="{classe}">
            <td>{html.escape(attr["id"])}</td>
            <td>{html.escape(attr["nome"])}</td>
            <td>{attr["atual"]}</td>
            <td>{attr["pior"]}</td>
            <td>{attr["limiar"]}</td>
            <td>{html.escape(attr["bruto_hex"])}</td>
            <td>{status}</td>
        </tr>
        """

    html_alertas = ""

    if criticos:
        html_alertas += """
        <div class="alert-box critico-box">
            <h2>🔴 ALERTAS CRÍTICOS DOS RESULTADOS SMART</h2>
        """

        for alerta in criticos:
            html_alertas += f"""
            <div class="alert-item">
                <b>ID {html.escape(alerta["id"])} -
                {html.escape(alerta["nome"])}</b><br>
                {html.escape(alerta["motivo"])}<br>
                Valor bruto:
                {html.escape(alerta["bruto"])}
            </div>
            """

        html_alertas += "</div>"

    if alertas:
        html_alertas += """
        <div class="alert-box alerta-box">
            <h2>🟠 ATENÇÃO NOS RESULTADOS SMART</h2>
        """

        for alerta in alertas:
            html_alertas += f"""
            <div class="alert-item">
                <b>ID {html.escape(alerta["id"])} -
                {html.escape(alerta["nome"])}</b><br>
                {html.escape(alerta["motivo"])}<br>
                Valor bruto:
                {html.escape(alerta["bruto"])}
            </div>
            """

        html_alertas += "</div>"

    if not criticos and not alertas:
        html_alertas = """
        <div class="alert-box normal-box">
            <h2>🟢 NENHUM ALERTA CRÍTICO DETECTADO</h2>
            <p>
                Os resultados SMART não apresentaram indicadores
                críticos conforme as regras de análise.
            </p>
            <p>
                O atributo BC (Tempo Limite de Comando) não é
                considerado defeito apenas porque o valor bruto
                é diferente de zero.
            </p>
        </div>
        """

    informacoes = [
        ("Número do disco", dados.get("NumeroDisco", "N/D")),
        ("Identificador do dispositivo", dados.get("DeviceId", "N/D")),
        ("Nome amigável", dados.get("NomeAmigavel", "N/D")),
        ("Modelo", modelo),
        ("Número de série", serial),
        ("Versão do firmware", dados.get("FirmwareVersion", "N/D")),
        ("Fabricante", dados.get("Fabricante", "N/D")),
        ("Tipo de mídia", tipo),
        ("Tipo de conexão", dados.get("TipoConexao", "N/D")),
        ("Status operacional", traduzir_status(dados.get("StatusOperacional"))),
        ("Status de saúde", traduzir_status(dados.get("StatusSaude"))),
        ("Saúde", traduzir_status(dados.get("Saude"))),
        ("Capacidade", capacidade),
        ("Tamanho do setor físico", dados.get("SetorFisico", "N/D")),
        ("Tamanho do setor lógico", dados.get("SetorLogico", "N/D")),
        (
            "Disco de inicialização",
            "Sim" if dados.get("DiscoInicializacao", False) else "Não"
        ),
        (
            "Disco do sistema",
            "Sim" if dados.get("DiscoSistema", False) else "Não"
        ),
        (
            "Somente leitura",
            "Sim" if dados.get("SomenteLeitura", False) else "Não"
        ),
        ("Desgaste", f"{dados.get('Desgaste', 0)}%"),
        ("Temperatura", f"{dados.get('Temperatura', 0)} °C"),
        ("Temperatura máxima", f"{dados.get('TemperaturaMaxima', 0)} °C"),
        ("Horas de funcionamento", f"{tempo} ({horas} horas)"),
        ("Dados lidos", formatar_bytes(dados.get("BytesLidos", 0))),
        ("Dados gravados", formatar_bytes(dados.get("BytesGravados", 0))),
        ("Erros de leitura", dados.get("ErrosLeitura", 0)),
        ("Erros de gravação", dados.get("ErrosGravacao", 0)),
        ("Erros não corrigidos", dados.get("ErrosNaoCorrigidos", 0)),
    ]

    linhas_info = ""

    for nome, valor in informacoes:
        linhas_info += f"""
        <tr>
            <td>{html.escape(str(nome))}</td>
            <td>{html.escape(str(valor))}</td>
        </tr>
        """

    documento = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HD E SSD MONITOR PRO • Windows 10</title>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 30px;
    background: #030603;
    color: #b8ffb8;
    font-family: Consolas, "Courier New", monospace;
}}
.container {{ max-width: 1400px; margin: auto; }}
h1 {{ color: #00ff41; text-align: center; font-size: 30px; }}
h2 {{
    color: #00e5ff;
    border-bottom: 1px solid #00b82e;
    padding-bottom: 8px;
}}
.data {{ text-align: center; color: #718071; }}
.status {{
    text-align: center;
    padding: 15px;
    margin: 20px 0;
    font-size: 20px;
    font-weight: bold;
    border: 1px solid;
}}
.status.normal {{ color: #00ff41; border-color: #00ff41; background: #071407; }}
.status.alerta {{ color: #ff8c00; border-color: #ff8c00; background: #180e03; }}
.status.critico {{ color: #ff3333; border-color: #ff3333; background: #180303; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0 30px; }}
th {{
    background: #071007;
    color: #00e5ff;
    padding: 10px;
    border: 1px solid #263826;
    text-align: left;
}}
td {{ padding: 8px; border: 1px solid #263826; }}
tr.normal {{ color: #00ff41; }}
tr.alerta {{ color: #ff8c00; background: #160d03; }}
tr.critico {{ color: #ff3333; background: #180303; }}
.alert-box {{ padding: 15px; margin: 20px 0; border: 1px solid; }}
.normal-box {{ color: #00ff41; border-color: #00ff41; background: #071407; }}
.alerta-box {{ color: #ff8c00; border-color: #ff8c00; background: #180e03; }}
.critico-box {{ color: #ff3333; border-color: #ff3333; background: #180303; }}
.alert-item {{
    padding: 10px;
    margin: 8px 0;
    border-left: 4px solid currentColor;
}}
.footer {{
    margin-top: 40px;
    padding-top: 15px;
    border-top: 1px solid #263826;
    text-align: center;
    color: #718071;
}}
</style>
</head>
<body>
<div class="container">
<h1>HD E SSD MONITOR PRO • Windows 10</h1>
<div class="data">Relatório gerado em: {agora}</div>
<div class="status {status_classe}">● {status_texto}</div>

<h2>DISCO ANALISADO</h2>
<table>
<tr><th>INFORMAÇÃO</th><th>VALOR</th></tr>
<tr><td>Modelo</td><td>{modelo}</td></tr>
<tr><td>Número de série</td><td>{serial}</td></tr>
<tr><td>Tipo de mídia</td><td>{tipo}</td></tr>
<tr><td>Capacidade</td><td>{html.escape(str(capacidade))}</td></tr>
<tr><td>Horas de funcionamento</td><td>{html.escape(str(tempo))} ({horas} horas)</td></tr>
</table>

{html_alertas}

<h2>INFORMAÇÕES DO DISCO</h2>
<table>
<tr><th>INFORMAÇÃO</th><th>VALOR</th></tr>
{linhas_info}
</table>

<h2>RESULTADOS SMART</h2>
<table>
<thead>
<tr>
<th>ID</th><th>NOME DO ATRIBUTO</th><th>ATUAL</th>
<th>PIOR VALOR</th><th>LIMIAR</th><th>VALOR BRUTO</th><th>STATUS</th>
</tr>
</thead>
<tbody>
{html_smart}
</tbody>
</table>

<div class="footer">
HD E SSD MONITOR PRO • Windows 10<br>
Relatório gerado automaticamente.
</div>
</div>
</body>
</html>
"""

    try:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(documento)
    except Exception as erro:
        messagebox.showerror(
            "ERRO AO SALVAR",
            f"Não foi possível salvar o HTML:\n\n{erro}"
        )
        return

    resposta = messagebox.askyesno(
        "HTML SALVO",
        (
            "Relatório HTML salvo com sucesso.\n\n"
            f"{caminho}\n\n"
            "Deseja abrir o relatório agora?"
        )
    )

    if resposta:
        try:
            webbrowser.open(Path(caminho).resolve().as_uri())
        except Exception:
            pass


# ============================================================
# ROLAGEM COM MOUSE
# ============================================================

def mousewheel(event):
    try:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    except Exception:
        pass


canvas.bind_all("<MouseWheel>", mousewheel)


# ============================================================
# FECHAR
# ============================================================

def fechar_programa():
    global scan_ativo
    scan_ativo = False
    app.destroy()


app.protocol("WM_DELETE_WINDOW", fechar_programa)


# ============================================================
# INICIAR (Loop Principal sem auto-start)
# ============================================================

app.mainloop()
