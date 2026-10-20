import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import json
import re
import ctypes
import os
import html as html_escape
from datetime import datetime
import threading

# ── Forçar PowerShell a usar UTF-8 em TODAS as chamadas ──
PS_UTF8 = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;$OutputEncoding=[System.Text.Encoding]::UTF8;"

# ============================================================
#  DICIONÁRIO DE ERROS DE TELA AZUL
# ============================================================
BSOD_CODES = {
    "0x0000000A": {
        "nome": "IRQL_NOT_LESS_OR_EQUAL",
        "causa": "Um driver tentou acessar uma área de memória que não tinha permissão.",
        "solucao": [
            "Atualize todos os drivers (principalmente vídeo, rede e chipset)",
            "Desinstale drivers instalados recentemente",
            "Execute: sfc /scannow no CMD como administrador",
            "Teste a memória RAM com MemTest86",
        ],
    },
    "0x0000001A": {
        "nome": "MEMORY_MANAGEMENT",
        "causa": "Problema grave no gerenciamento de memória RAM.",
        "solucao": [
            "Teste a RAM com MemTest86 (rode por pelo menos 2 horas)",
            "Verifique se os pentes de RAM estão bem encaixados",
            "Execute: mdsched.exe (diagnóstico de memória do Windows)",
            "Se tiver overclock, remova-o",
        ],
    },
    "0x0000001E": {
        "nome": "KMODE_EXCEPTION_NOT_HANDLED",
        "causa": "Um programa do kernel gerou uma exceção não tratada.",
        "solucao": [
            "Atualize ou reinstale o driver mencionado",
            "Desinstale antivírus de terceiros (teste)",
            "Verifique se o Windows está atualizado",
            "Execute: DISM /Online /Cleanup-Image /RestoreHealth",
        ],
    },
    "0x0000003B": {
        "nome": "SYSTEM_SERVICE_EXCEPTION",
        "causa": "Erro em um serviço do sistema, geralmente driver de vídeo ou antivírus.",
        "solucao": [
            "Atualize o driver da placa de vídeo",
            "Desinstale antivírus de terceiros temporariamente",
            "Execute: sfc /scannow",
            "Verifique atualizações do Windows",
        ],
    },
    "0x00000050": {
        "nome": "PAGE_FAULT_IN_NONPAGED_AREA",
        "causa": "Memória RAM com defeito ou driver corrompido tentou acessar memória inválida.",
        "solucao": [
            "Teste a RAM com MemTest86 (prioridade!)",
            "Desative o arquivo de paginação temporariamente",
            "Atualize drivers de antivírus e armazenamento",
            "Verifique o HD/SSD com: chkdsk C: /f /r",
        ],
    },
    "0x0000007E": {
        "nome": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
        "causa": "Thread do sistema falhou devido a driver incompatível.",
        "solucao": [
            "Identifique o driver no relatório e atualize-o",
            "Reinicie em modo de segurança e desinstale drivers recentes",
            "Atualize o BIOS da placa-mãe",
            "Execute: sfc /scannow",
        ],
    },
    "0x0000007F": {
        "nome": "UNEXPECTED_KERNEL_MODE_TRAP",
        "causa": "Erro de hardware grave, geralmente RAM, CPU ou overclock.",
        "solucao": [
            "Remova qualquer overclock de CPU/GPU/RAM",
            "Teste a RAM com MemTest86",
            "Verifique temperaturas da CPU (HWMonitor)",
            "Verifique se a fonte está entregando energia suficiente",
        ],
    },
    "0x0000009F": {
        "nome": "DRIVER_POWER_STATE_FAILURE",
        "causa": "Driver não respondeu corretamente a uma mudança de estado de energia.",
        "solucao": [
            "Atualize drivers de Wi-Fi e Bluetooth",
            "Desative suspensão híbrida nas opções de energia",
            "Atualize o driver do chipset",
            "Desative inicialização rápida do Windows",
        ],
    },
    "0x000000C2": {
        "nome": "BAD_POOL_CALLER",
        "causa": "Driver fez uma chamada inválida ao pool de memória.",
        "solucao": [
            "Desinstale drivers instalados recentemente",
            "Verifique o HD/SSD com chkdsk",
            "Teste a RAM",
            "Faça scan completo com Windows Defender",
        ],
    },
    "0x000000D1": {
        "nome": "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "causa": "Driver acessou memória com nível de IRQL incorreto.",
        "solucao": [
            "Atualize ou reinstale o driver mencionado no relatório",
            "Reinicie em modo de segurança para remover driver problemático",
            "Verifique dispositivos USB conectados recentemente",
            "Execute: sfc /scannow",
        ],
    },
    "0x000000EA": {
        "nome": "THREAD_STUCK_IN_DEVICE_DRIVER",
        "causa": "Driver da placa de vídeo travou em loop infinito.",
        "solucao": [
            "Atualize o driver da placa de vídeo (NVIDIA/AMD/Intel)",
            "Verifique a temperatura da GPU (HWMonitor)",
            "Limpe o cooler da placa de vídeo",
            "Teste com driver mais antigo (rollback)",
        ],
    },
    "0x000000EF": {
        "nome": "CRITICAL_PROCESS_DIED",
        "causa": "Um processo essencial do Windows parou inesperadamente.",
        "solucao": [
            "Execute: sfc /scannow",
            "Execute: DISM /Online /Cleanup-Image /RestoreHealth",
            "Verifique o HD/SSD com chkdsk C: /f /r",
            "Faça scan completo contra malware",
            "Considere usar Restauração do Sistema",
        ],
    },
    "0x000000F4": {
        "nome": "CRITICAL_OBJECT_TERMINATION",
        "causa": "Processo crítico foi encerrado - geralmente problema no disco.",
        "solucao": [
            "Verifique o HD/SSD com CrystalDiskInfo",
            "Execute: chkdsk C: /f /r",
            "Teste cabos SATA (desconecte e reconecte)",
            "Faça backup imediato dos arquivos importantes",
        ],
    },
    "0x00000116": {
        "nome": "VIDEO_TDR_FAILURE",
        "causa": "A placa de vídeo parou de responder e não se recuperou a tempo.",
        "solucao": [
            "Atualize o driver da placa de vídeo",
            "Verifique temperatura da GPU (não deve passar de 85°C)",
            "Limpe o PC (poeira nos coolers)",
            "Reduza overclock da GPU se houver",
            "Teste em outro slot PCIe",
        ],
    },
    "0x00000124": {
        "nome": "WHEA_UNCORRECTABLE_ERROR",
        "causa": "Erro grave de hardware detectado pela CPU.",
        "solucao": [
            "Remova qualquer overclock",
            "Verifique temperaturas da CPU",
            "Teste a fonte de alimentação",
            "Teste a RAM com MemTest86",
            "Pode ser CPU ou placa-mãe defeituosa",
        ],
    },
    "0x00000133": {
        "nome": "DPC_WATCHDOG_VIOLATION",
        "causa": "Um driver demorou tempo demais para responder - comum com SSDs.",
        "solucao": [
            "Atualize o firmware do SSD",
            "Atualize o driver de armazenamento (SATA/NVMe)",
            "Atualize o driver do chipset",
            "Verifique drivers de rede",
            "Atualize o BIOS",
        ],
    },
    "0x00000139": {
        "nome": "KERNEL_SECURITY_CHECK_FAILURE",
        "causa": "Corrupção de memória detectada - pode ser RAM, driver ou vírus.",
        "solucao": [
            "Execute scan completo contra vírus",
            "Teste a RAM com MemTest86",
            "Execute: sfc /scannow e DISM",
            "Atualize todos os drivers",
            "Verifique o HD/SSD",
        ],
    },
}

resultados_atuais = []
arquivos_evtx_cache = []
eventos_bsod_cache = []
eventos_viewer_cache = []

# Caminhos dos logs
CAMINHO_MINIDUMP = r"C:\Windows\Minidump"
CAMINHO_MEMORY_DMP = r"C:\Windows\MEMORY.DMP"
CAMINHO_EVENTLOG = r"C:\Windows\System32\winevt\Logs\System.evtx"
PASTA_EVENTLOG = r"C:\Windows\System32\winevt\Logs"

# Estrutura de logs do Visualizador de Eventos (igual ao Windows)
ESTRUTURA_LOGS = {
    "Logs do Windows": {
        "Aplicativo": {"logname": "Application", "icone": "📋"},
        "Segurança": {"logname": "Security", "icone": "🔒"},
        "Instalação": {"logname": "Setup", "icone": "⚙️"},
        "Sistema": {"logname": "System", "icone": "🖥️"},
        "Eventos Encaminhados": {"logname": "ForwardedEvents", "icone": "📨"},
    },
    "Logs de Aplicativos e Serviços": {
        "Eventos de Hardware": {"logname": "HardwareEvents", "icone": "🔧"},
        "Internet Explorer": {"logname": "Internet Explorer", "icone": "🌐"},
        "Serviço de Gerenciamento de Chaves": {"logname": "Key Management Service", "icone": "🔑"},
        "Windows PowerShell": {"logname": "Windows PowerShell", "icone": "💻"},
    },
}

# ============================================================
#  FUNÇÕES AUXILIARES
# ============================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def copiar_caminho(caminho):
    root.clipboard_clear()
    root.clipboard_append(caminho)
    root.update()
    messagebox.showinfo("Copiado! 📋", f"Caminho copiado:\n\n{caminho}")


def abrir_pasta(caminho):
    try:
        if os.path.isfile(caminho):
            subprocess.Popen(["explorer", "/select,", caminho])
        elif os.path.isdir(caminho):
            os.startfile(caminho)
        else:
            pasta_pai = os.path.dirname(caminho)
            if os.path.isdir(pasta_pai):
                os.startfile(pasta_pai)
            else:
                messagebox.showwarning("Aviso", f"Caminho não encontrado:\n{caminho}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir:\n{e}")


def abrir_event_viewer():
    try:
        subprocess.Popen(["eventvwr.msc"], shell=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o Event Viewer:\n{e}")


# ============================================================
#  ABA 1: ANÁLISE DE TELA AZUL
# ============================================================
def buscar_telas_azuis():
    try:
        comando = [
            "powershell", "-NoProfile", "-Command",
            PS_UTF8 + 
            "Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001} "
            "-MaxEvents 20 -ErrorAction SilentlyContinue | ForEach-Object { "
            "[PSCustomObject]@{ Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
            "Mensagem = $_.Message } } | ConvertTo-Json -Depth 3"
        ]
        resultado = subprocess.run(
            comando, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if resultado.returncode == 0 and resultado.stdout.strip():
            dados = json.loads(resultado.stdout)
            if isinstance(dados, dict):
                dados = [dados]
            return dados
        return []
    except Exception:
        return []


def analisar_mensagem(mensagem):
    info = {
        "codigo": "Desconhecido",
        "nome": "Não identificado",
        "causa": "Não identificada.",
        "solucao": ["Pesquise o código no Google."],
        "driver": "Nenhum driver listado",
    }
    match = re.search(r"0x[0-9a-fA-F]{8,10}", mensagem)
    if match:
        codigo = match.group(0).upper()
        if len(codigo) < 10:
            codigo = "0x" + codigo[2:].zfill(8)
        info["codigo"] = codigo
        if codigo in BSOD_CODES:
            info["nome"] = BSOD_CODES[codigo]["nome"]
            info["causa"] = BSOD_CODES[codigo]["causa"]
            info["solucao"] = BSOD_CODES[codigo]["solucao"]
    driver_match = re.findall(r"([a-zA-Z0-9_]+\.sys)", mensagem, re.IGNORECASE)
    if driver_match:
        info["driver"] = ", ".join(set(driver_match))
    return info


def executar_analise():
    global resultados_atuais
    resultados_atuais = []
    area_texto.config(state=tk.NORMAL)
    area_texto.delete("1.0", tk.END)
    area_texto.insert(tk.END, "⏳ Buscando telas azuis no sistema...\n\n")
    area_texto.update()

    resultados = buscar_telas_azuis()

    if not resultados:
        area_texto.insert(
            tk.END,
            "✅ Nenhuma tela azul encontrada nos últimos registros!\n\n"
            "Seu PC está limpo de crashes recentes. 🎉",
        )
        btn_salvar_html.config(state=tk.DISABLED)
    else:
        area_texto.insert(
            tk.END,
            f"🔴 Foram encontradas {len(resultados)} telas azul:\n"
            + "═" * 60 + "\n\n",
        )
        for i, evento in enumerate(resultados, 1):
            msg_bruta = evento.get("Mensagem", "Sem mensagem.")
            info = analisar_mensagem(msg_bruta)
            info["data"] = evento.get("Data", "Desconhecida")
            info["mensagem_bruta"] = msg_bruta
            resultados_atuais.append(info)

            area_texto.insert(
                tk.END,
                f"📌 TELA AZUL #{i}  |  📅 {info['data']}\n"
                f"🔢 Código: {info['codigo']} ({info['nome']})\n"
                f"🔧 Driver: {info['driver']}\n"
                f"💡 Causa: {info['causa']}\n\n",
            )
        btn_salvar_html.config(state=tk.NORMAL)

    area_texto.config(state=tk.DISABLED)


def salvar_html():
    if not resultados_atuais:
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar!\nExecute uma análise primeiro.")
        return

    nome_padrao = f"relatorio_tela_azul_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    caminho = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
        initialfile=nome_padrao,
        title="Salvar relatório como...",
    )
    if not caminho:
        return

    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    total = len(resultados_atuais)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Tela Azul - {data_geracao}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Segoe UI', Tahoma, sans-serif;
        background: linear-gradient(135deg, #1e1e2e 0%, #313244 100%);
        color: #cdd6f4; padding: 30px; min-height: 100vh;
    }}
    .container {{ max-width: 1000px; margin: 0 auto; }}
    header {{
        text-align: center; padding: 30px;
        background: rgba(137, 180, 250, 0.1); border-radius: 15px;
        margin-bottom: 30px; border: 1px solid #89b4fa;
    }}
    h1 {{ font-size: 2.5em; color: #89b4fa; margin-bottom: 10px; }}
    .subtitulo {{ color: #a6adc8; font-size: 1.1em; }}
    .resumo {{
        background: #313244; padding: 20px; border-radius: 10px;
        margin-bottom: 30px; display: flex; justify-content: space-around;
        flex-wrap: wrap; gap: 20px;
    }}
    .card-resumo {{
        text-align: center; padding: 15px 25px; background: #45475a;
        border-radius: 8px; min-width: 180px;
    }}
    .card-resumo .numero {{ font-size: 2em; font-weight: bold; color: #f38ba8; }}
    .card-resumo .label {{ color: #a6adc8; font-size: 0.9em; margin-top: 5px; }}
    .tela-azul {{
        background: #313244; border-radius: 12px; padding: 25px;
        margin-bottom: 25px; border-left: 5px solid #f38ba8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .tela-azul h2 {{ color: #f38ba8; margin-bottom: 15px; font-size: 1.5em; }}
    .info-grid {{
        display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px; margin-bottom: 20px;
    }}
    .info-item {{ background: #45475a; padding: 12px 15px; border-radius: 8px; }}
    .info-item .rotulo {{
        color: #89b4fa; font-weight: bold; font-size: 0.85em;
        text-transform: uppercase; margin-bottom: 5px;
    }}
    .info-item .valor {{ color: #cdd6f4; font-size: 1em; word-break: break-word; }}
    .causa {{
        background: rgba(249, 226, 175, 0.1); border-left: 4px solid #f9e2af;
        padding: 15px; border-radius: 5px; margin-bottom: 15px;
    }}
    .causa .titulo {{ color: #f9e2af; font-weight: bold; margin-bottom: 8px; }}
    .solucao {{
        background: rgba(166, 227, 161, 0.1); border-left: 4px solid #a6e3a1;
        padding: 15px; border-radius: 5px; margin-bottom: 15px;
    }}
    .solucao .titulo {{ color: #a6e3a1; font-weight: bold; margin-bottom: 10px; }}
    .solucao ul {{ list-style: none; padding-left: 0; }}
    .solucao li {{ padding: 6px 0 6px 25px; position: relative; }}
    .solucao li:before {{ content: "✓"; color: #a6e3a1; font-weight: bold; position: absolute; left: 0; }}
    .log-bruto {{
        background: #11111b; border: 1px solid #45475a; border-radius: 8px;
        padding: 15px; margin-top: 10px; font-family: Consolas, monospace;
        font-size: 0.85em; color: #bac2de; white-space: pre-wrap; word-break: break-word;
        max-height: 320px; overflow-y: auto;
    }}
    .log-bruto .titulo {{
        color: #eba0ac; font-weight: bold; font-family: 'Segoe UI', sans-serif;
        font-size: 0.95em; margin-bottom: 10px; display: block;
    }}
    footer {{
        text-align: center; margin-top: 40px; padding: 20px;
        color: #6c7086; font-size: 0.9em; border-top: 1px solid #45475a;
    }}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>🔍 Relatório de Tela Azul</h1>
        <div class="subtitulo">Análise do sistema Windows 10</div>
        <div class="subtitulo" style="margin-top:10px;">📅 Gerado em: {data_geracao}</div>
    </header>
    <div class="resumo">
        <div class="card-resumo">
            <div class="numero">{total}</div>
            <div class="label">Telas Azuis Detectadas</div>
        </div>
    </div>
"""

    for i, info in enumerate(resultados_atuais, 1):
        solucoes_html = "".join(
            [f"<li>{html_escape.escape(str(s))}</li>" for s in info["solucao"]]
        )
        msg_bruta_esc = html_escape.escape(
            info.get("mensagem_bruta", "Sem log bruto disponível.")
        )
        codigo_esc = html_escape.escape(str(info.get("codigo", "")))
        nome_esc = html_escape.escape(str(info.get("nome", "")))
        driver_esc = html_escape.escape(str(info.get("driver", "")))
        causa_esc = html_escape.escape(str(info.get("causa", "")))
        data_esc = html_escape.escape(str(info.get("data", "")))

        html += f"""
    <div class="tela-azul">
        <h2>📌 Tela Azul #{i}</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="rotulo">📅 Data e Hora</div>
                <div class="valor">{data_esc}</div>
            </div>
            <div class="info-item">
                <div class="rotulo">🔢 Código do Erro</div>
                <div class="valor">{codigo_esc}</div>
            </div>
            <div class="info-item">
                <div class="rotulo">📛 Nome do Erro</div>
                <div class="valor">{nome_esc}</div>
            </div>
            <div class="info-item">
                <div class="rotulo">🔧 Driver Envolvido</div>
                <div class="valor">{driver_esc}</div>
            </div>
        </div>
        <div class="causa">
            <div class="titulo">💡 Causa Provável</div>
            <div>{causa_esc}</div>
        </div>
        <div class="solucao">
            <div class="titulo">🛠️ Como Resolver</div>
            <ul>{solucoes_html}</ul>
        </div>
        <div class="log-bruto">
            <span class="titulo">📄 LOG BRUTO NATIVO DO WINDOWS (Event ID 1001)</span>
{msg_bruta_esc}
        </div>
    </div>
"""

    html += """
    <footer>
        <p>Relatório gerado automaticamente pelo Analisador de Tela Azul</p>
        <p>📁 Minidump: C:\\Windows\\Minidump</p>
        <p>📁 MEMORY.DMP: C:\\Windows\\MEMORY.DMP</p>
        <p>📁 System.evtx: C:\\Windows\\System32\\winevt\\Logs\\System.evtx</p>
    </footer>
</div>
</body>
</html>
"""

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        resposta = messagebox.askyesno(
            "Sucesso! ✅",
            f"Relatório completo salvo!\n\n📁 {caminho}\n\nAbrir no navegador agora?",
        )
        if resposta:
            os.startfile(caminho)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar:\n\n{e}")


# ============================================================
#  ABA 2: CAMINHOS
# ============================================================
def atualizar_aba_logs():
    area_logs.config(state=tk.NORMAL)
    area_logs.delete("1.0", tk.END)
    area_logs.insert(tk.END, "  📁 ONDE O WINDOWS GRAVA OS LOGS\n" + "═" * 60 + "\n\n")

    ex_mini = os.path.exists(CAMINHO_MINIDUMP)
    area_logs.insert(
        tk.END,
        f"📌 MINIDUMP (Arquivo pequeno)\n📂 Caminho: {CAMINHO_MINIDUMP}\n"
        f"📊 Status: {'✅ Existe' if ex_mini else '❌ Não existe'}\n\n",
    )

    ex_mem = os.path.exists(CAMINHO_MEMORY_DMP)
    area_logs.insert(
        tk.END,
        f"📌 MEMORY.DMP (Despejo completo)\n📂 Caminho: {CAMINHO_MEMORY_DMP}\n"
        f"📊 Status: {'✅ Existe' if ex_mem else '❌ Não existe'}\n\n",
    )

    ex_evtx = os.path.exists(CAMINHO_EVENTLOG)
    area_logs.insert(
        tk.END,
        f"📌 SYSTEM.EVTX (Log de Eventos)\n📂 Caminho: {CAMINHO_EVENTLOG}\n"
        f"📊 Status: {'✅ Existe' if ex_evtx else '❌ Não existe'}\n\n",
    )

    area_logs.insert(
        tk.END,
        "🖱️ Dica: Clique com botão direito nesta área para um menu rápido.",
    )
    area_logs.config(state=tk.DISABLED)


def mostrar_menu_direito(event):
    menu = tk.Menu(root, tearoff=0, font=("Segoe UI", 10))
    menu.add_command(label="📂 Abrir Minidump", command=lambda: abrir_pasta(CAMINHO_MINIDUMP))
    menu.add_command(label="📂 Abrir System.evtx", command=lambda: abrir_pasta(PASTA_EVENTLOG))
    menu.add_separator()
    menu.add_command(label="📜 Abrir Event Viewer do Windows", command=abrir_event_viewer)
    menu.tk_popup(event.x_root, event.y_root)


# ============================================================
#  ABA 3: PESQUISA DE LOGS EVTX
# ============================================================
def carregar_arquivos_evtx():
    global arquivos_evtx_cache
    arquivos_evtx_cache = []
    tabela_evtx.delete(*tabela_evtx.get_children())

    if not os.path.exists(PASTA_EVENTLOG):
        return

    try:
        for f in os.listdir(PASTA_EVENTLOG):
            if f.lower().endswith(".evtx"):
                caminho = os.path.join(PASTA_EVENTLOG, f)
                stats = os.stat(caminho)
                data_obj = datetime.fromtimestamp(stats.st_mtime)

                arquivos_evtx_cache.append({
                    "nome": f,
                    "data_completa": data_obj.strftime("%d/%m/%Y %H:%M:%S"),
                    "tamanho": f"{(stats.st_size / 1024):,.0f} KB".replace(",", "."),
                    "caminho": caminho,
                    "obj_data": data_obj,
                })

        arquivos_evtx_cache.sort(key=lambda x: x["obj_data"], reverse=True)
        filtrar_tabela_evtx()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler pasta:\n{e}")


def filtrar_tabela_evtx(*args):
    tabela_evtx.delete(*tabela_evtx.get_children())
    termo = entry_busca.get().strip().lower()

    count = 0
    for arq in arquivos_evtx_cache:
        if termo in arq["nome"].lower() or termo in arq["data_completa"]:
            tabela_evtx.insert(
                "", "end", iid=count,
                values=(arq["nome"], arq["data_completa"], arq["tamanho"]),
            )
            count += 1

    lbl_status_busca.config(text=f"Mostrando {count} log")


def prever_log_selecionado(event):
    selecionado = tabela_evtx.selection()
    if not selecionado:
        return

    nome_arquivo = tabela_evtx.item(selecionado[0], "values")[0]
    caminho_abrir = next(
        (a["caminho"] for a in arquivos_evtx_cache if a["nome"] == nome_arquivo), None
    )
    if not caminho_abrir:
        return

    area_preview.config(state=tk.NORMAL)
    area_preview.delete("1.0", tk.END)
    area_preview.insert(
        tk.END,
        f"⏳ Lendo arquivo '{nome_arquivo}'...\n(Aguarde, extraindo dados do Windows...)",
    )
    area_preview.update()

    try:
        comando = [
            "powershell", "-NoProfile", "-Command",
            PS_UTF8 +
            f"Get-WinEvent -Path '{caminho_abrir}' -MaxEvents 25 -ErrorAction SilentlyContinue | "
            "ForEach-Object { [PSCustomObject]@{ "
            "Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
            "Nivel = $_.LevelDisplayName; ID = $_.Id; Mensagem = $_.Message "
            "} } | ConvertTo-Json",
        ]

        resultado = subprocess.run(
            comando, capture_output=True, text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        area_preview.delete("1.0", tk.END)

        if resultado.returncode == 0 and resultado.stdout.strip():
            eventos = json.loads(resultado.stdout)
            if isinstance(eventos, dict):
                eventos = [eventos]

            area_preview.insert(tk.END, f"📑 ÚLTIMOS {len(eventos)} EVENTOS REGISTRADOS:\n")
            area_preview.insert(tk.END, "═" * 80 + "\n\n")

            for ev in eventos:
                nivel = ev.get("Nivel", "Informações")
                icone = "ℹ️"
                if "Aviso" in nivel or "Warning" in nivel:
                    icone = "⚠️"
                elif "Erro" in nivel or "Error" in nivel or "Crítico" in nivel:
                    icone = "❌"

                area_preview.insert(
                    tk.END,
                    f"📅 Data: {ev.get('Data', 'N/A')}  |  {icone} {nivel}  |  🆔 ID: {ev.get('ID', 'N/A')}\n",
                )
                msg = str(ev.get("Mensagem", "")).replace("\n", " ").strip()
                area_preview.insert(tk.END, f"📝 {msg}\n")
                area_preview.insert(tk.END, "-" * 80 + "\n")
        else:
            area_preview.insert(
                tk.END,
                "Nenhum evento retornado. (O arquivo pode estar vazio, corrompido ou em uso exclusivo pelo sistema).",
            )

    except Exception as e:
        area_preview.insert(tk.END, f"Erro ao ler log: {e}")

    area_preview.config(state=tk.DISABLED)


def abrir_evtx_no_windows(event):
    selecionado = tabela_evtx.selection()
    if not selecionado:
        return

    nome_arquivo = tabela_evtx.item(selecionado[0], "values")[0]
    caminho_abrir = next(
        (a["caminho"] for a in arquivos_evtx_cache if a["nome"] == nome_arquivo), None
    )

    if caminho_abrir:
        try:
            os.startfile(caminho_abrir)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir no Windows:\n{e}")


# ============================================================
#  ABA 4: EVENTOS DE ERRO DE TELA AZUL (EVENT ID 1001)
# ============================================================
def carregar_eventos_bsod_exclusivos():
    global eventos_bsod_cache
    eventos_bsod_cache = []
    tabela_bsod_events.delete(*tabela_bsod_events.get_children())
    lbl_status_bsod.config(text="⏳ Buscando eventos de Tela Azul (ID 1001)...")
    root.update()

    try:
        comando = [
            "powershell", "-NoProfile", "-Command",
            PS_UTF8 +
            "Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001} "
            "-MaxEvents 50 -ErrorAction SilentlyContinue | "
            "ForEach-Object { [PSCustomObject]@{ "
            "Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
            "Provedor = $_.ProviderName; "
            "ID = $_.Id; "
            "Mensagem = $_.Message "
            "} } | ConvertTo-Json",
        ]

        resultado = subprocess.run(
            comando, capture_output=True, text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if resultado.returncode == 0 and resultado.stdout.strip():
            dados = json.loads(resultado.stdout)
            if isinstance(dados, dict):
                dados = [dados]

            eventos_bsod_cache = dados
            for idx, ev in enumerate(dados):
                msg = ev.get("Mensagem", "")
                match = re.search(r"0x[0-9a-fA-F]{8,10}", msg)
                codigo = match.group(0).upper() if match else "Ver detalhes"
                tabela_bsod_events.insert(
                    "", "end", iid=idx,
                    values=(
                        ev.get("Data", "N/A"),
                        ev.get("Provedor", "BugCheck"),
                        ev.get("ID", 1001),
                        codigo,
                    ),
                )

            lbl_status_bsod.config(
                text=f"Total de {len(dados)} eventos de Tela Azul encontrados."
            )
        else:
            lbl_status_bsod.config(text="Nenhum evento de Tela Azul (ID 1001) registrado.")
    except Exception as e:
        lbl_status_bsod.config(text="Erro ao carregar eventos.")
        messagebox.showerror("Erro", f"Falha ao carregar eventos BSOD:\n{e}")


def exibir_detalhes_evento_bsod(event):
    selecionado = tabela_bsod_events.selection()
    if not selecionado:
        return

    idx = int(selecionado[0])
    if idx < len(eventos_bsod_cache):
        evento = eventos_bsod_cache[idx]
        area_detalhes_bsod.config(state=tk.NORMAL)
        area_detalhes_bsod.delete("1.0", tk.END)

        area_detalhes_bsod.insert(
            tk.END, "💥 REGISTRO BRUTO DO EVENTO DE TELA AZUL (EVENT ID 1001)\n"
        )
        area_detalhes_bsod.insert(tk.END, "═" * 80 + "\n\n")
        area_detalhes_bsod.insert(
            tk.END, f"📅 Data e Hora: {evento.get('Data', 'N/A')}\n"
        )
        area_detalhes_bsod.insert(
            tk.END, f"🏢 Origem (Provedor): {evento.get('Provedor', 'N/A')}\n"
        )
        area_detalhes_bsod.insert(
            tk.END, f"🆔 Event ID: {evento.get('ID', 'N/A')}\n"
        )
        area_detalhes_bsod.insert(tk.END, "-" * 80 + "\n\n")
        area_detalhes_bsod.insert(
            tk.END,
            f"📝 MENSAGEM NATIVA REGISTRADA PELO WINDOWS:\n\n"
            f"{evento.get('Mensagem', 'Sem conteúdo')}\n",
        )

        area_detalhes_bsod.config(state=tk.DISABLED)


# ============================================================
#  ABA 5: VISUALIZADOR DE EVENTOS (ESTILO WINDOWS)
# ============================================================
def carregar_eventos_do_log(logname, max_eventos=100):
    """Carrega eventos de um log específico do Windows via PowerShell."""
    global eventos_viewer_cache
    eventos_viewer_cache = []

    tabela_viewer.delete(*tabela_viewer.get_children())
    area_detalhes_viewer.config(state=tk.NORMAL)
    area_detalhes_viewer.delete("1.0", tk.END)
    area_detalhes_viewer.insert(tk.END, f"⏳ Carregando eventos de '{logname}'...\n")
    area_detalhes_viewer.config(state=tk.DISABLED)

    lbl_status_viewer.config(text=f"⏳ Carregando '{logname}'...")
    root.update()

    def tarefa():
        global eventos_viewer_cache
        try:
            comando = [
                "powershell", "-NoProfile", "-Command",
                PS_UTF8 +
                f"Get-WinEvent -LogName '{logname}' -MaxEvents {max_eventos} "
                f"-ErrorAction SilentlyContinue | ForEach-Object {{ "
                f"[PSCustomObject]@{{ "
                f"Nivel = $_.LevelDisplayName; "
                f"DataHora = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
                f"Origem = $_.ProviderName; "
                f"EventID = $_.Id; "
                f"Categoria = $_.TaskDisplayName; "
                f"Mensagem = $_.Message "
                f"}} }} | ConvertTo-Json -Depth 3"
            ]

            resultado = subprocess.run(
                comando, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            root.after(0, lambda: _processar_resultado_viewer(resultado, logname))

        except subprocess.TimeoutExpired:
            root.after(0, lambda: _viewer_erro("Tempo limite excedido ao carregar eventos."))
        except Exception as e:
            root.after(0, lambda: _viewer_erro(str(e)))

    thread = threading.Thread(target=tarefa, daemon=True)
    thread.start()


def _processar_resultado_viewer(resultado, logname):
    """Processa o resultado do PowerShell e preenche a tabela."""
    global eventos_viewer_cache

    tabela_viewer.delete(*tabela_viewer.get_children())

    if resultado.returncode == 0 and resultado.stdout.strip():
        try:
            dados = json.loads(resultado.stdout)
            if isinstance(dados, dict):
                dados = [dados]

            eventos_viewer_cache = dados

            for idx, ev in enumerate(dados):
                nivel = str(ev.get("Nivel", "Informações") or "Informações")
                data_hora = ev.get("DataHora", "N/A")
                origem = ev.get("Origem", "N/A")
                event_id = ev.get("EventID", "N/A")
                categoria = ev.get("Categoria", "") or "Nenhum"

                # Ícone baseado no nível
                if "Erro" in nivel or "Error" in nivel:
                    icone_nivel = "❌ Erro"
                    tag = "erro"
                elif "Aviso" in nivel or "Warning" in nivel:
                    icone_nivel = "⚠️ Aviso"
                    tag = "aviso"
                elif "Crítico" in nivel or "Critical" in nivel:
                    icone_nivel = "🔴 Crítico"
                    tag = "critico"
                else:
                    icone_nivel = "ℹ️ Informação"
                    tag = "info"

                tabela_viewer.insert(
                    "", "end", iid=str(idx),
                    values=(icone_nivel, data_hora, origem, event_id, categoria),
                    tags=(tag,),
                )

            # Cores nas linhas
            tabela_viewer.tag_configure("erro", foreground="#f38ba8")
            tabela_viewer.tag_configure("aviso", foreground="#f9e2af")
            tabela_viewer.tag_configure("critico", foreground="#ff6b6b")
            tabela_viewer.tag_configure("info", foreground="#cdd6f4")

            lbl_status_viewer.config(
                text=f"✅ '{logname}' — {len(dados)} eventos carregados"
            )
        except json.JSONDecodeError:
            lbl_status_viewer.config(text=f"⚠️ Erro ao interpretar dados de '{logname}'")
    else:
        lbl_status_viewer.config(
            text=f"📭 Nenhum evento encontrado em '{logname}' (ou log não existe)"
        )

    area_detalhes_viewer.config(state=tk.NORMAL)
    area_detalhes_viewer.delete("1.0", tk.END)
    area_detalhes_viewer.insert(tk.END, "👆 Clique em um evento na tabela acima para ver os detalhes.")
    area_detalhes_viewer.config(state=tk.DISABLED)


def _viewer_erro(msg):
    lbl_status_viewer.config(text=f"❌ Erro: {msg}")
    area_detalhes_viewer.config(state=tk.NORMAL)
    area_detalhes_viewer.delete("1.0", tk.END)
    area_detalhes_viewer.insert(tk.END, f"Erro ao carregar eventos:\n{msg}")
    area_detalhes_viewer.config(state=tk.DISABLED)


def ao_selecionar_arvore(event):
    """Quando o usuário clica em um item da árvore de logs."""
    selecionado = arvore_logs.selection()
    if not selecionado:
        return

    item = selecionado[0]
    # Verificar se é um log (folha) e não uma categoria (pai)
    pai = arvore_logs.parent(item)
    if not pai:
        # É uma categoria, não um log
        return

    # Pegar o logname associado
    texto = arvore_logs.item(item, "text")

    # Procurar o logname na estrutura
    for categoria, logs in ESTRUTURA_LOGS.items():
        for nome_display, info in logs.items():
            if nome_display == texto or info.get("logname") == texto:
                max_ev = int(spin_max_eventos.get())
                carregar_eventos_do_log(info["logname"], max_ev)
                return

    # Se não encontrou na estrutura, tenta usar o texto diretamente
    max_ev = int(spin_max_eventos.get())
    carregar_eventos_do_log(texto, max_ev)


def ao_selecionar_evento_viewer(event):
    """Mostra detalhes do evento selecionado na tabela."""
    selecionado = tabela_viewer.selection()
    if not selecionado:
        return

    idx = int(selecionado[0])
    if idx < len(eventos_viewer_cache):
        ev = eventos_viewer_cache[idx]

        area_detalhes_viewer.config(state=tk.NORMAL)
        area_detalhes_viewer.delete("1.0", tk.END)

        nivel = str(ev.get("Nivel", "Informações") or "Informações")
        if "Erro" in nivel or "Error" in nivel:
            icone = "❌"
        elif "Aviso" in nivel or "Warning" in nivel:
            icone = "⚠️"
        elif "Crítico" in nivel or "Critical" in nivel:
            icone = "🔴"
        else:
            icone = "ℹ️"

        area_detalhes_viewer.insert(tk.END, f"{'═' * 80}\n")
        area_detalhes_viewer.insert(tk.END, f"  {icone}  DETALHES DO EVENTO\n")
        area_detalhes_viewer.insert(tk.END, f"{'═' * 80}\n\n")

        area_detalhes_viewer.insert(tk.END, f"  📋 Nome do Log:     {ev.get('Origem', 'N/A')}\n")
        area_detalhes_viewer.insert(tk.END, f"  🏢 Origem:          {ev.get('Origem', 'N/A')}\n")
        area_detalhes_viewer.insert(tk.END, f"  📅 Data e Hora:     {ev.get('DataHora', 'N/A')}\n")
        area_detalhes_viewer.insert(tk.END, f"  🆔 Event ID:        {ev.get('EventID', 'N/A')}\n")
        area_detalhes_viewer.insert(tk.END, f"  📊 Nível:           {nivel}\n")
        area_detalhes_viewer.insert(
            tk.END, f"  📂 Categoria:       {ev.get('Categoria', 'Nenhum') or 'Nenhum'}\n"
        )

        area_detalhes_viewer.insert(tk.END, f"\n{'─' * 80}\n")
        area_detalhes_viewer.insert(tk.END, f"  📝 MENSAGEM\n{'─' * 80}\n\n")

        mensagem = ev.get("Mensagem", "Sem mensagem disponível.") or "Sem mensagem disponível."
        area_detalhes_viewer.insert(tk.END, f"{mensagem}\n")

        area_detalhes_viewer.config(state=tk.DISABLED)


def filtrar_eventos_viewer(*args):
    """Filtra eventos já carregados na tabela do viewer."""
    termo = entry_filtro_viewer.get().strip().lower()

    tabela_viewer.delete(*tabela_viewer.get_children())

    for idx, ev in enumerate(eventos_viewer_cache):
        nivel = str(ev.get("Nivel", "Informações") or "Informações")
        data_hora = str(ev.get("DataHora", "N/A"))
        origem = str(ev.get("Origem", "N/A"))
        event_id = str(ev.get("EventID", "N/A"))
        categoria = str(ev.get("Categoria", "") or "Nenhum")
        mensagem = str(ev.get("Mensagem", "") or "")

        # Verifica filtro de nível (checkboxes)
        mostrar = True
        if "Erro" in nivel or "Error" in nivel:
            if not var_filtro_erro.get():
                mostrar = False
            tag = "erro"
            icone_nivel = "❌ Erro"
        elif "Aviso" in nivel or "Warning" in nivel:
            if not var_filtro_aviso.get():
                mostrar = False
            tag = "aviso"
            icone_nivel = "⚠️ Aviso"
        elif "Crítico" in nivel or "Critical" in nivel:
            if not var_filtro_critico.get():
                mostrar = False
            tag = "critico"
            icone_nivel = "🔴 Crítico"
        else:
            if not var_filtro_info.get():
                mostrar = False
            tag = "info"
            icone_nivel = "ℹ️ Informação"

        if not mostrar:
            continue

        # Verifica filtro de texto
        if termo:
            campos = f"{nivel} {data_hora} {origem} {event_id} {categoria} {mensagem}".lower()
            if termo not in campos:
                continue

        tabela_viewer.insert(
            "", "end", iid=str(idx),
            values=(icone_nivel, data_hora, origem, event_id, categoria),
            tags=(tag,),
        )

    tabela_viewer.tag_configure("erro", foreground="#f38ba8")
    tabela_viewer.tag_configure("aviso", foreground="#f9e2af")
    tabela_viewer.tag_configure("critico", foreground="#ff6b6b")
    tabela_viewer.tag_configure("info", foreground="#cdd6f4")

    total_vis = len(tabela_viewer.get_children())
    lbl_status_viewer.config(
        text=f"Mostrando {total_vis} de {len(eventos_viewer_cache)} eventos"
    )


def carregar_log_personalizado():
    """Permite carregar um log digitando o nome."""
    logname = entry_log_custom.get().strip()
    if not logname:
        messagebox.showwarning("Aviso", "Digite o nome de um log.\n\nExemplos:\n• Application\n• System\n• Security\n• Microsoft-Windows-TaskScheduler/Operational")
        return
    max_ev = int(spin_max_eventos.get())
    carregar_eventos_do_log(logname, max_ev)


def exportar_eventos_viewer():
    """Exporta os eventos visíveis em HTML formatado."""
    if not eventos_viewer_cache:
        messagebox.showwarning("Aviso", "Nenhum evento para exportar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("Arquivo HTML", "*.html"), ("Todos", "*.*")],
        initialfile=f"eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        title="Exportar eventos como HTML",
    )
    if not caminho:
        return

    try:
        data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        total = len(eventos_viewer_cache)

        # Contadores por nível
        cont_erro = 0
        cont_aviso = 0
        cont_info = 0
        cont_critico = 0

        for ev in eventos_viewer_cache:
            nivel = str(ev.get("Nivel", "") or "")
            if "Crítico" in nivel or "Critical" in nivel:
                cont_critico += 1
            elif "Erro" in nivel or "Error" in nivel:
                cont_erro += 1
            elif "Aviso" in nivel or "Warning" in nivel:
                cont_aviso += 1
            else:
                cont_info += 1

        # Nome do log carregado (pega da primeira entrada ou usa padrão)
        log_nome = "Eventos do Windows"
        if eventos_viewer_cache:
            log_nome = eventos_viewer_cache[0].get("Origem", "Eventos do Windows") or "Eventos do Windows"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Eventos - {data_geracao}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Segoe UI', Tahoma, sans-serif;
        background: linear-gradient(135deg, #1e1e2e 0%, #313244 100%);
        color: #cdd6f4;
        padding: 20px;
        min-height: 100vh;
    }}
    .container {{ max-width: 1400px; margin: 0 auto; }}

    header {{
        text-align: center;
        padding: 25px;
        background: rgba(137, 180, 250, 0.1);
        border-radius: 15px;
        margin-bottom: 25px;
        border: 1px solid #89b4fa;
    }}
    h1 {{ font-size: 2.3em; color: #89b4fa; margin-bottom: 8px; }}
    .subtitulo {{ color: #a6adc8; font-size: 1em; margin-top: 5px; }}

    .resumo {{
        background: #313244;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
    }}
    .card-resumo {{
        text-align: center;
        padding: 15px;
        background: #45475a;
        border-radius: 8px;
        border-top: 3px solid #89b4fa;
    }}
    .card-resumo.erro {{ border-top-color: #f38ba8; }}
    .card-resumo.aviso {{ border-top-color: #f9e2af; }}
    .card-resumo.info {{ border-top-color: #89b4fa; }}
    .card-resumo.critico {{ border-top-color: #ff6b6b; }}
    .card-resumo.total {{ border-top-color: #a6e3a1; }}

    .card-resumo .numero {{ font-size: 2em; font-weight: bold; }}
    .card-resumo.erro .numero {{ color: #f38ba8; }}
    .card-resumo.aviso .numero {{ color: #f9e2af; }}
    .card-resumo.info .numero {{ color: #89b4fa; }}
    .card-resumo.critico .numero {{ color: #ff6b6b; }}
    .card-resumo.total .numero {{ color: #a6e3a1; }}
    .card-resumo .label {{
        color: #a6adc8;
        font-size: 0.85em;
        margin-top: 5px;
        text-transform: uppercase;
    }}

    .controles {{
        background: #313244;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        align-items: center;
    }}
    .controles input[type="text"] {{
        flex: 1;
        min-width: 200px;
        padding: 10px 15px;
        background: #45475a;
        border: 1px solid #585b70;
        border-radius: 6px;
        color: #cdd6f4;
        font-size: 1em;
        outline: none;
    }}
    .controles input[type="text"]:focus {{ border-color: #89b4fa; }}
    .controles label {{
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        padding: 6px 12px;
        background: #45475a;
        border-radius: 6px;
        font-size: 0.9em;
        user-select: none;
    }}
    .controles label:hover {{ background: #585b70; }}
    .controles input[type="checkbox"] {{ cursor: pointer; }}

    .tabela-container {{
        background: #313244;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    thead {{
        background: #1e1e2e;
        position: sticky;
        top: 0;
    }}
    th {{
        padding: 12px 10px;
        text-align: left;
        color: #89b4fa;
        font-size: 0.9em;
        text-transform: uppercase;
        border-bottom: 2px solid #45475a;
        cursor: pointer;
        user-select: none;
    }}
    th:hover {{ background: #313244; }}
    tbody tr {{
        border-bottom: 1px solid #45475a;
        transition: background 0.15s;
        cursor: pointer;
    }}
    tbody tr:hover {{ background: #45475a; }}
    td {{
        padding: 10px;
        font-size: 0.9em;
        vertical-align: top;
    }}
    tr.erro td:first-child {{ color: #f38ba8; font-weight: bold; }}
    tr.aviso td:first-child {{ color: #f9e2af; font-weight: bold; }}
    tr.info td:first-child {{ color: #89b4fa; font-weight: bold; }}
    tr.critico td:first-child {{ color: #ff6b6b; font-weight: bold; }}

    .msg-curta {{
        max-width: 400px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #bac2de;
    }}

    .msg-completa {{
        display: none;
        background: #11111b;
        padding: 15px;
        border-left: 4px solid #89b4fa;
        margin-top: 10px;
        border-radius: 4px;
        font-family: Consolas, monospace;
        font-size: 0.85em;
        color: #cdd6f4;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 400px;
        overflow-y: auto;
    }}
    tr.expandida .msg-completa {{ display: block; }}
    tr.expandida .msg-curta {{ white-space: normal; }}

    .sem-resultados {{
        text-align: center;
        padding: 40px;
        color: #a6adc8;
        font-size: 1.1em;
    }}

    footer {{
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        color: #6c7086;
        font-size: 0.85em;
        border-top: 1px solid #45475a;
    }}

    .status-filtro {{
        padding: 8px 15px;
        background: rgba(137, 180, 250, 0.1);
        color: #89b4fa;
        border-radius: 6px;
        font-size: 0.9em;
    }}

    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: #1e1e2e; }}
    ::-webkit-scrollbar-thumb {{ background: #45475a; border-radius: 5px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #585b70; }}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>🖥️ Relatório de Eventos do Windows</h1>
        <div class="subtitulo">Log: <strong>{html_escape.escape(log_nome)}</strong></div>
        <div class="subtitulo">📅 Gerado em: {data_geracao}</div>
    </header>

    <div class="resumo">
        <div class="card-resumo total">
            <div class="numero">{total}</div>
            <div class="label">Total de Eventos</div>
        </div>
        <div class="card-resumo critico">
            <div class="numero">{cont_critico}</div>
            <div class="label">🔴 Críticos</div>
        </div>
        <div class="card-resumo erro">
            <div class="numero">{cont_erro}</div>
            <div class="label">❌ Erros</div>
        </div>
        <div class="card-resumo aviso">
            <div class="numero">{cont_aviso}</div>
            <div class="label">⚠️ Avisos</div>
        </div>
        <div class="card-resumo info">
            <div class="numero">{cont_info}</div>
            <div class="label">ℹ️ Informações</div>
        </div>
    </div>

    <div class="controles">
        <input type="text" id="busca" placeholder="🔍 Buscar em qualquer campo..." onkeyup="filtrar()">
        <label><input type="checkbox" id="f_critico" checked onchange="filtrar()"> 🔴 Críticos</label>
        <label><input type="checkbox" id="f_erro" checked onchange="filtrar()"> ❌ Erros</label>
        <label><input type="checkbox" id="f_aviso" checked onchange="filtrar()"> ⚠️ Avisos</label>
        <label><input type="checkbox" id="f_info" checked onchange="filtrar()"> ℹ️ Info</label>
        <div class="status-filtro" id="status">Mostrando {total} de {total} eventos</div>
    </div>

    <div class="tabela-container">
        <table id="tabela">
            <thead>
                <tr>
                    <th onclick="ordenar(0)">📊 Nível</th>
                    <th onclick="ordenar(1)">📅 Data e Hora</th>
                    <th onclick="ordenar(2)">🏢 Origem</th>
                    <th onclick="ordenar(3)">🆔 Event ID</th>
                    <th onclick="ordenar(4)">📂 Categoria</th>
                    <th>📝 Mensagem (clique para expandir)</th>
                </tr>
            </thead>
            <tbody id="corpo">
"""

        # Gerar linhas da tabela
        for idx, ev in enumerate(eventos_viewer_cache):
            nivel = str(ev.get("Nivel", "Informações") or "Informações")
            data_hora = str(ev.get("DataHora", "N/A") or "N/A")
            origem = str(ev.get("Origem", "N/A") or "N/A")
            event_id = str(ev.get("EventID", "N/A") or "N/A")
            categoria = str(ev.get("Categoria", "") or "Nenhum")
            mensagem = str(ev.get("Mensagem", "") or "Sem mensagem")

            if "Crítico" in nivel or "Critical" in nivel:
                classe = "critico"
                nivel_display = "🔴 Crítico"
            elif "Erro" in nivel or "Error" in nivel:
                classe = "erro"
                nivel_display = "❌ Erro"
            elif "Aviso" in nivel or "Warning" in nivel:
                classe = "aviso"
                nivel_display = "⚠️ Aviso"
            else:
                classe = "info"
                nivel_display = "ℹ️ Informação"

            nivel_esc = html_escape.escape(nivel_display)
            data_esc = html_escape.escape(data_hora)
            origem_esc = html_escape.escape(origem)
            eid_esc = html_escape.escape(event_id)
            cat_esc = html_escape.escape(categoria)
            msg_esc = html_escape.escape(mensagem)
            msg_curta = html_escape.escape(mensagem.replace("\n", " ").strip()[:200])

            html += f"""
                <tr class="{classe}" onclick="expandir(this)" data-nivel="{classe}">
                    <td>{nivel_esc}</td>
                    <td>{data_esc}</td>
                    <td>{origem_esc}</td>
                    <td>{eid_esc}</td>
                    <td>{cat_esc}</td>
                    <td>
                        <div class="msg-curta">{msg_curta}</div>
                        <div class="msg-completa">{msg_esc}</div>
                    </td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>
        <div class="sem-resultados" id="semResultados" style="display:none;">
            🔍 Nenhum evento corresponde aos filtros atuais.
        </div>
    </div>

    <footer>
        <p>📄 Relatório gerado pelo <strong>Analisador de Tela Azul e Logs</strong></p>
        <p>Total de {total} eventos analisados em {data_geracao}</p>
    </footer>
</div>

<script>
    function filtrar() {{
        const termo = document.getElementById('busca').value.toLowerCase();
        const fCritico = document.getElementById('f_critico').checked;
        const fErro = document.getElementById('f_erro').checked;
        const fAviso = document.getElementById('f_aviso').checked;
        const fInfo = document.getElementById('f_info').checked;

        const linhas = document.querySelectorAll('#corpo tr');
        let visiveis = 0;

        linhas.forEach(linha => {{
            const nivel = linha.dataset.nivel;
            const texto = linha.textContent.toLowerCase();

            let mostrarNivel = false;
            if (nivel === 'critico' && fCritico) mostrarNivel = true;
            if (nivel === 'erro' && fErro) mostrarNivel = true;
            if (nivel === 'aviso' && fAviso) mostrarNivel = true;
            if (nivel === 'info' && fInfo) mostrarNivel = true;

            const mostrarTexto = termo === '' || texto.includes(termo);

            if (mostrarNivel && mostrarTexto) {{
                linha.style.display = '';
                visiveis++;
            }} else {{
                linha.style.display = 'none';
            }}
        }});

        document.getElementById('status').textContent = 
            `Mostrando ${{visiveis}} de ${{linhas.length}} eventos`;
        document.getElementById('semResultados').style.display = 
            visiveis === 0 ? 'block' : 'none';
    }}

    function expandir(linha) {{
        linha.classList.toggle('expandida');
    }}

    let ordemAsc = {{}};
    function ordenar(colIdx) {{
        const tbody = document.getElementById('corpo');
        const linhas = Array.from(tbody.querySelectorAll('tr'));
        ordemAsc[colIdx] = !ordemAsc[colIdx];
        const asc = ordemAsc[colIdx];

        linhas.sort((a, b) => {{
            const textoA = a.cells[colIdx].textContent.trim().toLowerCase();
            const textoB = b.cells[colIdx].textContent.trim().toLowerCase();
            if (textoA < textoB) return asc ? -1 : 1;
            if (textoA > textoB) return asc ? 1 : -1;
            return 0;
        }});

        linhas.forEach(l => tbody.appendChild(l));
    }}
</script>
</body>
</html>
"""

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)

        resposta = messagebox.askyesno(
            "Exportado ✅",
            f"Relatório HTML salvo!\n\n📁 {caminho}\n\nAbrir no navegador agora?",
        )
        if resposta:
            os.startfile(caminho)

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao exportar:\n{e}")


# ============================================================
#  INTERFACE GRÁFICA PRINCIPAL
# ============================================================
root = tk.Tk()
root.title("🔍 Analisador Logs Windows")
root.geometry("1080x820")
root.state("zoomed")
root.configure(bg="#1e1e2e")

style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
style.configure(
    "TNotebook.Tab",
    background="#313244",
    foreground="#cdd6f4",
    padding=[14, 8],
    font=("Segoe UI", 10, "bold"),
)
style.map(
    "TNotebook.Tab",
    background=[("selected", "#89b4fa")],
    foreground=[("selected", "#1e1e2e")],
)

style.configure(
    "Treeview",
    background="#313244",
    foreground="#cdd6f4",
    fieldbackground="#313244",
    borderwidth=0,
    rowheight=25,
)
style.map(
    "Treeview",
    background=[("selected", "#89b4fa")],
    foreground=[("selected", "#1e1e2e")],
)
style.configure(
    "Treeview.Heading",
    background="#1e1e2e",
    foreground="#a6adc8",
    font=("Segoe UI", 10, "bold"),
)

tk.Label(
    root,
    text="🔍 Analisador de Tela Azul e Logs",
    font=("Segoe UI", 18, "bold"),
    bg="#1e1e2e",
    fg="#cdd6f4",
).pack(pady=(15, 5))

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

# ==================== ABA 1: ANÁLISE ====================
aba_analise = tk.Frame(notebook, bg="#1e1e2e")
notebook.add(aba_analise, text="  🔎 Diagnóstico BSOD  ")

frame_botoes = tk.Frame(aba_analise, bg="#1e1e2e")
frame_botoes.pack(pady=10)

tk.Button(
    frame_botoes,
    text="🔎 ANALISAR AGORA",
    font=("Segoe UI", 11, "bold"),
    bg="#89b4fa",
    fg="#1e1e2e",
    relief=tk.FLAT,
    cursor="hand2",
    padx=20,
    pady=8,
    command=executar_analise,
).pack(side=tk.LEFT, padx=10)

btn_salvar_html = tk.Button(
    frame_botoes,
    text="💾 SALVAR RELATÓRIO COMPLETO HTML",
    font=("Segoe UI", 11, "bold"),
    bg="#a6e3a1",
    fg="#1e1e2e",
    relief=tk.FLAT,
    cursor="hand2",
    padx=20,
    pady=8,
    command=salvar_html,
    state=tk.DISABLED,
)
btn_salvar_html.pack(side=tk.LEFT, padx=10)

area_texto = scrolledtext.ScrolledText(
    aba_analise,
    font=("Consolas", 10),
    bg="#313244",
    fg="#cdd6f4",
    relief=tk.FLAT,
    state=tk.DISABLED,
)
area_texto.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

# ==================== ABA 2: CAMINHOS ====================
aba_logs = tk.Frame(notebook, bg="#1e1e2e")
notebook.add(aba_logs, text="  📁 Caminhos  ")


def criar_linha_caminho(aba, titulo, caminho, cor):
    f = tk.LabelFrame(
        aba,
        text=f" {titulo} ",
        font=("Segoe UI", 10, "bold"),
        bg="#1e1e2e",
        fg=cor,
        padx=10,
        pady=8,
    )
    f.pack(fill=tk.X, padx=15, pady=10)
    tk.Label(f, text=caminho, bg="#1e1e2e", fg="#cdd6f4", font=("Consolas", 10)).pack(
        side=tk.LEFT, padx=5
    )
    tk.Button(
        f,
        text="📋 Copiar",
        bg="#f9e2af",
        relief=tk.FLAT,
        cursor="hand2",
        command=lambda: copiar_caminho(caminho),
    ).pack(side=tk.RIGHT, padx=5)
    tk.Button(
        f,
        text="📂 Abrir Pasta",
        bg=cor,
        relief=tk.FLAT,
        cursor="hand2",
        command=lambda: abrir_pasta(caminho),
    ).pack(side=tk.RIGHT, padx=5)


criar_linha_caminho(aba_logs, "1. Minidump", CAMINHO_MINIDUMP, "#89b4fa")
criar_linha_caminho(aba_logs, "2. MEMORY.DMP", CAMINHO_MEMORY_DMP, "#f38ba8")
criar_linha_caminho(aba_logs, "3. Pasta de Eventos (.evtx)", PASTA_EVENTLOG, "#a6e3a1")

area_logs = scrolledtext.ScrolledText(
    aba_logs,
    font=("Consolas", 10),
    bg="#313244",
    fg="#cdd6f4",
    relief=tk.FLAT,
    height=8,
)
area_logs.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
area_logs.bind("<Button-3>", mostrar_menu_direito)
atualizar_aba_logs()

# ==================== ABA 3: PESQUISAR LOGS (EVTX) ====================
aba_pesquisa = tk.Frame(notebook, bg="#1e1e2e")
notebook.add(aba_pesquisa, text="  📜 Pesquisar Logs (EVTX)  ")

frame_busca = tk.Frame(aba_pesquisa, bg="#1e1e2e")
frame_busca.pack(fill=tk.X, padx=15, pady=15)

tk.Label(
    frame_busca,
    text="Filtrar por Nome ou Data:",
    bg="#1e1e2e",
    fg="#cdd6f4",
    font=("Segoe UI", 10, "bold"),
).pack(side=tk.LEFT)

entry_busca = tk.Entry(
    frame_busca,
    font=("Segoe UI", 11),
    bg="#313244",
    fg="#cdd6f4",
    insertbackground="#cdd6f4",
    width=25,
)
entry_busca.pack(side=tk.LEFT, padx=10)
entry_busca.bind("<KeyRelease>", filtrar_tabela_evtx)

tk.Button(
    frame_busca,
    text="🔄 Carregar/Atualizar Arquivos",
    bg="#89b4fa",
    fg="#1e1e2e",
    font=("Segoe UI", 9, "bold"),
    relief=tk.FLAT,
    command=carregar_arquivos_evtx,
).pack(side=tk.LEFT, padx=10)

lbl_status_busca = tk.Label(
    frame_busca, text="...", bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 9)
)
lbl_status_busca.pack(side=tk.RIGHT, padx=10)

frame_tabela = tk.Frame(aba_pesquisa, bg="#1e1e2e")
frame_tabela.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 5))

scroll_tabela = ttk.Scrollbar(frame_tabela, orient="vertical")
scroll_tabela.pack(side=tk.RIGHT, fill=tk.Y)

tabela_evtx = ttk.Treeview(
    frame_tabela,
    columns=("nome", "data", "tamanho"),
    show="headings",
    height=8,
    yscrollcommand=scroll_tabela.set,
)
scroll_tabela.config(command=tabela_evtx.yview)

tabela_evtx.heading("nome", text="Nome do Arquivo Log (.evtx)")
tabela_evtx.heading("data", text="📅 Data")
tabela_evtx.heading("tamanho", text="💾 Tamanho")
tabela_evtx.column("nome", width=450, anchor="w")
tabela_evtx.column("data", width=180, anchor="w")
tabela_evtx.column("tamanho", width=100, anchor="w")
tabela_evtx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tabela_evtx.bind("<<TreeviewSelect>>", prever_log_selecionado)
tabela_evtx.bind("<Double-1>", abrir_evtx_no_windows)

tk.Label(
    aba_pesquisa,
    text="Detalhes Rápidos (1 clique na tabela)  |  Dê 2 cliques na tabela para abrir no Windows",
    bg="#1e1e2e",
    fg="#cdd6f4",
    font=("Segoe UI", 10, "bold"),
).pack(anchor="w", padx=15, pady=(10, 0))

area_preview = scrolledtext.ScrolledText(
    aba_pesquisa,
    font=("Consolas", 10),
    bg="#313244",
    fg="#cdd6f4",
    relief=tk.FLAT,
    height=12,
)
area_preview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

# ==================== ABA 4: EVENTOS BSOD ====================
aba_eventos_bsod = tk.Frame(notebook, bg="#1e1e2e")
notebook.add(aba_eventos_bsod, text="  💥 Eventos BSOD (ID 1001)  ")

frame_topo_bsod = tk.Frame(aba_eventos_bsod, bg="#1e1e2e")
frame_topo_bsod.pack(fill=tk.X, padx=15, pady=12)

tk.Button(
    frame_topo_bsod,
    text="🔄 Recarregar Eventos BSOD",
    bg="#f38ba8",
    fg="#1e1e2e",
    font=("Segoe UI", 10, "bold"),
    relief=tk.FLAT,
    cursor="hand2",
    padx=15,
    pady=5,
    command=carregar_eventos_bsod_exclusivos,
).pack(side=tk.LEFT)

lbl_status_bsod = tk.Label(
    frame_topo_bsod,
    text="Aguardando carregamento...",
    bg="#1e1e2e",
    fg="#a6adc8",
    font=("Segoe UI", 10),
)
lbl_status_bsod.pack(side=tk.LEFT, padx=15)

frame_tabela_bsod = tk.Frame(aba_eventos_bsod, bg="#1e1e2e")
frame_tabela_bsod.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 5))

scroll_tabela_bsod = ttk.Scrollbar(frame_tabela_bsod, orient="vertical")
scroll_tabela_bsod.pack(side=tk.RIGHT, fill=tk.Y)

tabela_bsod_events = ttk.Treeview(
    frame_tabela_bsod,
    columns=("data", "provedor", "id", "codigo"),
    show="headings",
    height=7,
    yscrollcommand=scroll_tabela_bsod.set,
)
scroll_tabela_bsod.config(command=tabela_bsod_events.yview)

tabela_bsod_events.heading("data", text="📅 Data / Hora")
tabela_bsod_events.heading("provedor", text="🏢 Origem")
tabela_bsod_events.heading("id", text="🆔 Event ID")
tabela_bsod_events.heading("codigo", text="🔢 Código de Erro")

tabela_bsod_events.column("data", width=180, anchor="w")
tabela_bsod_events.column("provedor", width=250, anchor="w")
tabela_bsod_events.column("id", width=100, anchor="w")
tabela_bsod_events.column("codigo", width=200, anchor="w")

tabela_bsod_events.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
tabela_bsod_events.bind("<<TreeviewSelect>>", exibir_detalhes_evento_bsod)

tk.Label(
    aba_eventos_bsod,
    text="📋 Texto Nativo e Completo do Evento Selecionado (1 Clique acima)",
    bg="#1e1e2e",
    fg="#cdd6f4",
    font=("Segoe UI", 10, "bold"),
).pack(anchor="w", padx=15, pady=(8, 2))

area_detalhes_bsod = scrolledtext.ScrolledText(
    aba_eventos_bsod,
    font=("Consolas", 10),
    bg="#313244",
    fg="#cdd6f4",
    relief=tk.FLAT,
    height=12,
)
area_detalhes_bsod.pack(fill=tk.BOTH, expand=True, padx=15, pady=(2, 15))

# ==================== ABA 5: VISUALIZADOR DE EVENTOS ====================
aba_viewer = tk.Frame(notebook, bg="#1e1e2e")
notebook.add(aba_viewer, text="  🖥️ Visualizador de Eventos  ")

# --- Barra de ferramentas superior ---
frame_toolbar_viewer = tk.Frame(aba_viewer, bg="#181825", height=50)
frame_toolbar_viewer.pack(fill=tk.X, padx=0, pady=0)
frame_toolbar_viewer.pack_propagate(False)

tk.Button(
    frame_toolbar_viewer,
    text="🖥️ Abrir Visualizador do Windows",
    font=("Segoe UI", 10, "bold"),
    bg="#cba6f7",
    fg="#1e1e2e",
    relief=tk.FLAT,
    cursor="hand2",
    padx=15,
    pady=4,
    command=abrir_event_viewer,
).pack(side=tk.LEFT, padx=10, pady=8)

tk.Button(
    frame_toolbar_viewer,
    text="📤 Exportar HTML",   # ← Mudou de "Exportar CSV" para "Exportar HTML"
    font=("Segoe UI", 9, "bold"),
    bg="#a6e3a1",
    fg="#1e1e2e",
    relief=tk.FLAT,
    cursor="hand2",
    padx=10,
    pady=4,
    command=exportar_eventos_viewer,
).pack(side=tk.LEFT, padx=5, pady=8)

tk.Label(
    frame_toolbar_viewer,
    text="Máx. eventos:",
    bg="#181825",
    fg="#a6adc8",
    font=("Segoe UI", 9),
).pack(side=tk.LEFT, padx=(15, 2), pady=8)

spin_max_eventos = tk.Spinbox(
    frame_toolbar_viewer,
    from_=10,
    to=5000,
    width=6,
    font=("Segoe UI", 10),
    bg="#313244",
    fg="#cdd6f4",
    buttonbackground="#45475a",
    insertbackground="#cdd6f4",
)
spin_max_eventos.delete(0, tk.END)
spin_max_eventos.insert(0, "100")
spin_max_eventos.pack(side=tk.LEFT, padx=2, pady=8)

# Log personalizado
tk.Label(
    frame_toolbar_viewer,
    text="│  Log:",
    bg="#181825",
    fg="#a6adc8",
    font=("Segoe UI", 9),
).pack(side=tk.LEFT, padx=(15, 2), pady=8)

entry_log_custom = tk.Entry(
    frame_toolbar_viewer,
    font=("Segoe UI", 10),
    bg="#313244",
    fg="#cdd6f4",
    insertbackground="#cdd6f4",
    width=30,
)
entry_log_custom.pack(side=tk.LEFT, padx=2, pady=8)
entry_log_custom.insert(0, "System")

tk.Button(
    frame_toolbar_viewer,
    text="▶ Carregar",
    font=("Segoe UI", 9, "bold"),
    bg="#89b4fa",
    fg="#1e1e2e",
    relief=tk.FLAT,
    cursor="hand2",
    padx=8,
    pady=3,
    command=carregar_log_personalizado,
).pack(side=tk.LEFT, padx=5, pady=8)

lbl_status_viewer = tk.Label(
    frame_toolbar_viewer,
    text="Selecione um log na árvore à esquerda",
    bg="#181825",
    fg="#f9e2af",
    font=("Segoe UI", 9),
)
lbl_status_viewer.pack(side=tk.RIGHT, padx=15, pady=8)

# --- Layout principal: Árvore à esquerda + Conteúdo à direita ---
frame_corpo_viewer = tk.PanedWindow(
    aba_viewer, orient=tk.HORIZONTAL, bg="#1e1e2e", sashwidth=4
)
frame_corpo_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ---- Painel esquerdo: Árvore de logs ----
frame_arvore = tk.Frame(frame_corpo_viewer, bg="#1e1e2e")
frame_corpo_viewer.add(frame_arvore, width=280)

tk.Label(
    frame_arvore,
    text="📂 Logs de Eventos",
    bg="#1e1e2e",
    fg="#89b4fa",
    font=("Segoe UI", 11, "bold"),
).pack(anchor="w", padx=8, pady=(8, 4))

scroll_arvore = ttk.Scrollbar(frame_arvore, orient="vertical")
scroll_arvore.pack(side=tk.RIGHT, fill=tk.Y)

arvore_logs = ttk.Treeview(
    frame_arvore,
    show="tree",
    yscrollcommand=scroll_arvore.set,
    selectmode="browse",
)
scroll_arvore.config(command=arvore_logs.yview)
arvore_logs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Popular a árvore com a estrutura de logs
for categoria, logs in ESTRUTURA_LOGS.items():
    cat_id = arvore_logs.insert("", "end", text=f"📁 {categoria}", open=True)
    for nome_display, info in logs.items():
        arvore_logs.insert(cat_id, "end", text=nome_display)

# Adicionar mais logs comuns do Microsoft
cat_microsoft = arvore_logs.insert("", "end", text="📁 Microsoft (Populares)", open=False)
logs_microsoft = [
    "Microsoft-Windows-Diagnostics-Performance/Operational",
    "Microsoft-Windows-TaskScheduler/Operational",
    "Microsoft-Windows-WindowsUpdateClient/Operational",
    "Microsoft-Windows-Kernel-Power/System",
    "Microsoft-Windows-DriverFrameworks-UserMode/Operational",
    "Microsoft-Windows-WLAN-AutoConfig/Operational",
    "Microsoft-Windows-NetworkProfile/Operational",
    "Microsoft-Windows-Dhcp-Client/Admin",
    "Microsoft-Windows-DNS-Client/Operational",
    "Microsoft-Windows-Bits-Client/Operational",
    "Microsoft-Windows-AppXDeploymentServer/Operational",
    "Microsoft-Windows-Store/Operational",
    "Microsoft-Windows-Security-Auditing",
    "Microsoft-Windows-Sysmon/Operational",
    "Microsoft-Windows-PrintService/Operational",
    "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational",
]
for log_ms in logs_microsoft:
    arvore_logs.insert(cat_microsoft, "end", text=log_ms)

arvore_logs.bind("<<TreeviewSelect>>", ao_selecionar_arvore)

# ---- Painel direito: Tabela + Detalhes ----
frame_direito = tk.Frame(frame_corpo_viewer, bg="#1e1e2e")
frame_corpo_viewer.add(frame_direito)

# Barra de filtros
frame_filtros = tk.Frame(frame_direito, bg="#1e1e2e")
frame_filtros.pack(fill=tk.X, padx=5, pady=(5, 2))

tk.Label(
    frame_filtros,
    text="🔍 Filtrar:",
    bg="#1e1e2e",
    fg="#cdd6f4",
    font=("Segoe UI", 9, "bold"),
).pack(side=tk.LEFT, padx=(0, 5))

entry_filtro_viewer = tk.Entry(
    frame_filtros,
    font=("Segoe UI", 10),
    bg="#313244",
    fg="#cdd6f4",
    insertbackground="#cdd6f4",
    width=25,
)
entry_filtro_viewer.pack(side=tk.LEFT, padx=3)
entry_filtro_viewer.bind("<KeyRelease>", filtrar_eventos_viewer)

tk.Label(
    frame_filtros,
    text="  │  Mostrar:",
    bg="#1e1e2e",
    fg="#a6adc8",
    font=("Segoe UI", 9),
).pack(side=tk.LEFT, padx=(10, 5))

var_filtro_erro = tk.BooleanVar(value=True)
var_filtro_aviso = tk.BooleanVar(value=True)
var_filtro_info = tk.BooleanVar(value=True)
var_filtro_critico = tk.BooleanVar(value=True)

tk.Checkbutton(
    frame_filtros,
    text="❌ Erros",
    variable=var_filtro_erro,
    bg="#1e1e2e",
    fg="#f38ba8",
    selectcolor="#313244",
    activebackground="#1e1e2e",
    font=("Segoe UI", 9),
    command=filtrar_eventos_viewer,
).pack(side=tk.LEFT, padx=3)

tk.Checkbutton(
    frame_filtros,
    text="⚠️ Avisos",
    variable=var_filtro_aviso,
    bg="#1e1e2e",
    fg="#f9e2af",
    selectcolor="#313244",
    activebackground="#1e1e2e",
    font=("Segoe UI", 9),
    command=filtrar_eventos_viewer,
).pack(side=tk.LEFT, padx=3)

tk.Checkbutton(
    frame_filtros,
    text="ℹ️ Info",
    variable=var_filtro_info,
    bg="#1e1e2e",
    fg="#89b4fa",
    selectcolor="#313244",
    activebackground="#1e1e2e",
    font=("Segoe UI", 9),
    command=filtrar_eventos_viewer,
).pack(side=tk.LEFT, padx=3)

tk.Checkbutton(
    frame_filtros,
    text="🔴 Crítico",
    variable=var_filtro_critico,
    bg="#1e1e2e",
    fg="#ff6b6b",
    selectcolor="#313244",
    activebackground="#1e1e2e",
    font=("Segoe UI", 9),
    command=filtrar_eventos_viewer,
).pack(side=tk.LEFT, padx=3)

# Splitter vertical: tabela em cima, detalhes embaixo
paned_vertical = tk.PanedWindow(
    frame_direito, orient=tk.VERTICAL, bg="#1e1e2e", sashwidth=4
)
paned_vertical.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Tabela de eventos
frame_tabela_viewer = tk.Frame(paned_vertical, bg="#1e1e2e")
paned_vertical.add(frame_tabela_viewer, height=350)

scroll_viewer = ttk.Scrollbar(frame_tabela_viewer, orient="vertical")
scroll_viewer.pack(side=tk.RIGHT, fill=tk.Y)

scroll_viewer_h = ttk.Scrollbar(frame_tabela_viewer, orient="horizontal")
scroll_viewer_h.pack(side=tk.BOTTOM, fill=tk.X)

tabela_viewer = ttk.Treeview(
    frame_tabela_viewer,
    columns=("nivel", "datahora", "origem", "eventid", "categoria"),
    show="headings",
    yscrollcommand=scroll_viewer.set,
    xscrollcommand=scroll_viewer_h.set,
)
scroll_viewer.config(command=tabela_viewer.yview)
scroll_viewer_h.config(command=tabela_viewer.xview)

tabela_viewer.heading("nivel", text="📊 Nível")
tabela_viewer.heading("datahora", text="📅 Data e Hora")
tabela_viewer.heading("origem", text="🏢 Origem")
tabela_viewer.heading("eventid", text="🆔 Event ID")
tabela_viewer.heading("categoria", text="📂 Categoria")

tabela_viewer.column("nivel", width=130, anchor="w")
tabela_viewer.column("datahora", width=170, anchor="w")
tabela_viewer.column("origem", width=250, anchor="w")
tabela_viewer.column("eventid", width=90, anchor="center")
tabela_viewer.column("categoria", width=200, anchor="w")

tabela_viewer.pack(fill=tk.BOTH, expand=True)
tabela_viewer.bind("<<TreeviewSelect>>", ao_selecionar_evento_viewer)

# Detalhes do evento
frame_detalhes_viewer = tk.Frame(paned_vertical, bg="#1e1e2e")
paned_vertical.add(frame_detalhes_viewer, height=250)

tk.Label(
    frame_detalhes_viewer,
    text="📋 Detalhes do Evento Selecionado:",
    bg="#1e1e2e",
    fg="#89b4fa",
    font=("Segoe UI", 10, "bold"),
).pack(anchor="w", padx=5, pady=(5, 2))

area_detalhes_viewer = scrolledtext.ScrolledText(
    frame_detalhes_viewer,
    font=("Consolas", 10),
    bg="#313244",
    fg="#cdd6f4",
    relief=tk.FLAT,
    state=tk.DISABLED,
)
area_detalhes_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))

# ============================================================
#  INICIALIZAÇÃO FINAL
# ============================================================
if not is_admin():
    root.after(
        500,
        lambda: messagebox.showwarning(
            "Atenção",
            "Execute o arquivo como ADMINISTRADOR!\n(Botão direito -> Executar como Administrador)",
        ),
    )

root.after(800, carregar_arquivos_evtx)
root.after(1000, carregar_eventos_bsod_exclusivos)

root.mainloop()
