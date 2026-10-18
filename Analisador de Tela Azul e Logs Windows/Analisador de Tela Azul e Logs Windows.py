import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import json
import re
import ctypes
import os
import html as html_escape
from datetime import datetime

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

# Caminhos dos logs
CAMINHO_MINIDUMP = r"C:\Windows\Minidump"
CAMINHO_MEMORY_DMP = r"C:\Windows\MEMORY.DMP"
CAMINHO_EVENTLOG = r"C:\Windows\System32\winevt\Logs\System.evtx"
PASTA_EVENTLOG = r"C:\Windows\System32\winevt\Logs"

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
            "Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001} "
            "-MaxEvents 20 -ErrorAction SilentlyContinue | ForEach-Object { "
            "[PSCustomObject]@{ Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); Mensagem = $_.Message } } | ConvertTo-Json -Depth 3"
        ]
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=30,
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
            f"🔴 Foram encontradas {len(resultados)} tela(s) azul(is):\n" + "═" * 60 + "\n\n",
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
        msg_bruta_esc = html_escape.escape(info.get("mensagem_bruta", "Sem log bruto disponível."))
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

    html += f"""
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
        "🖱️ Dica: Clique com botão direito nesta área para um menu rápido com opções de copiar e abrir pastas.",
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

    lbl_status_busca.config(text=f"Mostrando {count} log(s).")

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
            f"Get-WinEvent -Path '{caminho_abrir}' -MaxEvents 25 -ErrorAction SilentlyContinue | "
            "ForEach-Object { [PSCustomObject]@{ "
            "Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
            "Nivel = $_.LevelDisplayName; ID = $_.Id; Mensagem = $_.Message "
            "} } | ConvertTo-Json",
        ]

        resultado = subprocess.run(
            comando, capture_output=True, text=True,
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
            "Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001} -MaxEvents 50 -ErrorAction SilentlyContinue | "
            "ForEach-Object { [PSCustomObject]@{ "
            "Data = $_.TimeCreated.ToString('dd/MM/yyyy HH:mm:ss'); "
            "Provedor = $_.ProviderName; "
            "ID = $_.Id; "
            "Mensagem = $_.Message "
            "} } | ConvertTo-Json",
        ]

        resultado = subprocess.run(
            comando, capture_output=True, text=True,
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
                text=f"Total de {len(dados)} evento(s) de Tela Azul encontrado(s)."
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

        area_detalhes_bsod.insert(tk.END, "💥 REGISTRO BRUTO DO EVENTO DE TELA AZUL (EVENT ID 1001)\n")
        area_detalhes_bsod.insert(tk.END, "═" * 80 + "\n\n")
        area_detalhes_bsod.insert(tk.END, f"📅 Data e Hora: {evento.get('Data', 'N/A')}\n")
        area_detalhes_bsod.insert(tk.END, f"🏢 Origem (Provedor): {evento.get('Provedor', 'N/A')}\n")
        area_detalhes_bsod.insert(tk.END, f"🆔 Event ID: {evento.get('ID', 'N/A')}\n")
        area_detalhes_bsod.insert(tk.END, "-" * 80 + "\n\n")
        area_detalhes_bsod.insert(
            tk.END,
            f"📝 MENSAGEM NATIVA REGISTRADA PELO WINDOWS:\n\n{evento.get('Mensagem', 'Sem conteúdo')}\n",
        )

        area_detalhes_bsod.config(state=tk.DISABLED)

# ============================================================
#  INTERFACE GRÁFICA PRINCIPAL
# ============================================================
root = tk.Tk()
root.title("🔍 Analisador de Tela Azul e Logs - Windows")
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
    text="📋 Texto Nativo e Completo do Evento Selecionado (1 Clique acima):",
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
