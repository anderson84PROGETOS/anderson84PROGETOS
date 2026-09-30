import customtkinter as ctk
from tkinter import ttk, messagebox
import subprocess
import json
import webbrowser
import os
import threading

# ============================================================
# Ocultar janela preta do console no .py e no .exe
# ============================================================
CREATE_NO_WINDOW = 0x08000000

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Mapeamento de IDs S.M.A.R.T. em Português
SMART_NAMES = {
    1: "Taxa de Erro de Leitura",
    3: "Tempo de Rotação (Spin-Up)",
    4: "Contagem de Início/Parada",
    5: "Contagem de Setores Realocados",
    7: "Taxa de Erro de Busca",
    9: "Horas Ligado (Power-On Hours)",
    10: "Tentativas de Rotação",
    12: "Ciclos de Energia",
    184: "Erro End-to-End",
    187: "Erros Incorrigíveis Relatados",
    188: "Tempo Limite de Comando",
    190: "Temperatura do Ar (Airflow)",
    194: "Temperatura do Disco",
    196: "Contagem de Eventos de Realocação",
    197: "Setores Pendentes Atuais",
    198: "Setores Incorrigíveis",
    199: "Erros de CRC UltraDMA",
    240: "Horas de Voo da Cabeça",
    241: "Total de Gravações do Host (GB)",
    242: "Total de Leituras do Host (GB)"
}

def converter_horas(horas_totais):
    try:
        horas_totais = int(horas_totais)
    except (TypeError, ValueError):
        return "Indisponível"

    if horas_totais <= 0: return "Indisponível"

    anos = horas_totais // 8760
    resto = horas_totais % 8760
    meses = resto // 720
    resto = resto % 720
    dias = resto // 24
    horas = resto % 24

    partes = []
    if anos > 0: partes.append(f"{anos} ano" + ("s" if anos > 1 else ""))
    if meses > 0: partes.append(f"{meses} mês" + ("es" if meses > 1 else ""))
    if dias > 0: partes.append(f"{dias} dia" + ("s" if dias > 1 else ""))
    if horas > 0 or not partes: partes.append(f"{horas} hora" + ("s" if horas != 1 else ""))

    texto = ", ".join(partes[:-1]) + " e " + partes[-1] if len(partes) > 1 else partes[0]
    return f"{horas_totais} horas ({texto})"

def executar_powershell(comando):
    try:
        args = [
            "powershell.exe", "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
            "-Command", f"{comando} | ConvertTo-Json -Compress -Depth 4"
        ]
        processo = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            errors="ignore", creationflags=CREATE_NO_WINDOW, shell=False
        )
        saida = (processo.stdout or "").strip()
        return json.loads(saida) if saida else None
    except Exception as e:
        print(f"Erro PS: {e}")
        return None

def obter_dados_reais_disco():
    """Busca informações reais dos discos, Limiares e define status por cor"""
    raw_disks = executar_powershell("Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, SerialNumber, MediaType, BusType, Size, HealthStatus, FirmwareVersion")
    if not raw_disks: return None
    if isinstance(raw_disks, dict): raw_disks = [raw_disks]

    volumes = executar_powershell("Get-Volume | Where-Object { $_.DriveLetter } | Select-Object DriveLetter, FileSystem")
    if isinstance(volumes, dict): volumes = [volumes]

    letras, sis_arquivos = [], []
    if volumes:
        for v in volumes:
            if v.get("DriveLetter"): letras.append(f"{v['DriveLetter']}:")
            if v.get("FileSystem") and v.get("FileSystem") not in sis_arquivos: sis_arquivos.append(v['FileSystem'])

    # 1. Dados do SMART
    smart_data_raw = executar_powershell("Get-CimInstance -Namespace root/wmi -ClassName MSStorageDriver_FailurePredictData -ErrorAction SilentlyContinue | Select-Object InstanceName, VendorSpecific")
    
    # 2. Limiares (Thresholds)
    smart_thresh_raw = executar_powershell("Get-CimInstance -Namespace root/wmi -ClassName MSStorageDriver_FailurePredictThresholds -ErrorAction SilentlyContinue | Select-Object InstanceName, VendorSpecific")

    dicionario_limiares = {}
    if smart_thresh_raw:
        if isinstance(smart_thresh_raw, dict): smart_thresh_raw = [smart_thresh_raw]
        for instance in smart_thresh_raw:
            t_bytes = instance.get("VendorSpecific") or []
            if len(t_bytes) >= 362:
                for i in range(2, 362, 12):
                    attr_id = t_bytes[i]
                    if attr_id == 0: continue
                    dicionario_limiares[attr_id] = t_bytes[i+1]

    disco = raw_disks[0]
    tamanho_gb = round(int(disco.get("Size", 0)) / (1024 ** 3), 1)

    saude_raw = str(disco.get("HealthStatus", "Healthy")).lower()
    if saude_raw in ("healthy", "0"):
        saude_texto, cor_saude = "🟢 Saudável", "#2ed573"
    elif saude_raw == "warning":
        saude_texto, cor_saude = "🟡 Atenção", "#ffa502"
    else:
        saude_texto, cor_saude = "🔴 Ruim", "#ff4757"

    atributos_smart, horas_ligado, temperatura = [], 0, "N/A"

    attrs_criticos = ["05", "C5", "C6", "B8", "BB"]

    if smart_data_raw:
        if isinstance(smart_data_raw, dict): smart_data_raw = [smart_data_raw]
        for instance in smart_data_raw:
            vendor_bytes = instance.get("VendorSpecific") or []
            if len(vendor_bytes) >= 362:
                for i in range(2, 362, 12):
                    attr_id = vendor_bytes[i]
                    if attr_id == 0: continue
                    
                    atual = vendor_bytes[i+3]
                    pior = vendor_bytes[i+4]
                    limiar = dicionario_limiares.get(attr_id, 0)
                    
                    raw_val = vendor_bytes[i+5] | (vendor_bytes[i+6]<<8) | (vendor_bytes[i+7]<<16) | (vendor_bytes[i+8]<<24) | (vendor_bytes[i+9]<<32) | (vendor_bytes[i+10]<<40)
                    raw_hex = f"{raw_val:012X}"
                    nome = SMART_NAMES.get(attr_id, f"Atributo Específico (0x{attr_id:02X})")
                    
                    id_hex = f"{attr_id:02X}"

                    # Lógica da cor do atributo
                    if limiar > 0 and atual <= limiar:
                        tag_cor = "vermelho"
                        emoji_html = "🔴"
                    elif id_hex in attrs_criticos and raw_val > 0:
                        tag_cor = "amarelo"
                        emoji_html = "🟡"
                    else:
                        tag_cor = "verde"
                        emoji_html = "🟢"

                    id_script = f"● {id_hex}"
                    id_html = f"{emoji_html} {id_hex}"

                    if attr_id == 9: horas_ligado = raw_val
                    if attr_id in (194, 190, 231): temperatura = f"{vendor_bytes[i+5]} °C"
                    
                    atributos_smart.append((id_script, id_html, nome, str(atual), str(pior), str(limiar), raw_hex, tag_cor))

    if horas_ligado == 0:
        uptime = executar_powershell("[math]::Round(((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).TotalHours)")
        if isinstance(uptime, (int, float)): horas_ligado = int(uptime)

    if temperatura == "N/A":
        temp_wmi = executar_powershell("Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty CurrentTemperature")
        if isinstance(temp_wmi, (int, float)) and temp_wmi > 0:
            temperatura = f"{round((temp_wmi / 10.0) - 273.15)} °C"

    return {
        "Modelo": f"{disco.get('FriendlyName', 'Disco Desconhecido')} ({tamanho_gb} GB)",
        "Firmware": str(disco.get("FirmwareVersion") or "N/A"),
        "Número de Série": str(disco.get("SerialNumber") or "N/A").strip(),
        "Interface": str(disco.get("BusType") or "N/A"),
        "Tipo de Disco": str(disco.get("MediaType") or "N/A"),
        "Status de Saúde": saude_texto,
        "Cor_Saude": cor_saude,
        "Temperatura": temperatura if temperatura != "N/A" else "N/D",
        "Letra da Unidade": " ".join(letras) if letras else "—",
        "Sistema de Arquivos": ", ".join(sis_arquivos) if sis_arquivos else "—",
        "Tempo Total Ligado": converter_horas(horas_ligado),
        "Atributos_SMART": atributos_smart
    }

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Informações do Disco")
        self.geometry("1020x760")
        self.minsize(900, 600)        
        
        self.dados_atuais = None
        self.construir_interface()

    def construir_interface(self):
        frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        frame_topo.pack(fill="x", padx=20, pady=(15, 5))

        self.lbl_modelo = ctk.CTkLabel(frame_topo, text="Nenhum disco escaneado", font=("Arial", 22, "bold"), text_color="#aaa")
        self.lbl_modelo.pack(side="left")

        self.btn_scan = ctk.CTkButton(
            frame_topo, text="🔍 Escanear Disco", font=("Arial", 14, "bold"), 
            fg_color="#1e90ff", hover_color="#0984e3", width=180, height=40,
            command=self.iniciar_scan
        )
        self.btn_scan.pack(side="right")

        frame_sup = ctk.CTkFrame(self, fg_color="transparent")
        frame_sup.pack(fill="x", padx=20, pady=5)

        # Saúde e Temperatura
        frame_esq = ctk.CTkFrame(frame_sup, fg_color="transparent")
        frame_esq.pack(side="left", padx=(0, 25))

        ctk.CTkLabel(frame_esq, text="Status de Saúde", font=("Arial", 12)).pack()
        self.box_saude = ctk.CTkFrame(frame_esq, fg_color="#333", width=150, height=52, corner_radius=8)
        self.box_saude.pack(pady=4)
        self.box_saude.pack_propagate(False)
        self.lbl_saude = ctk.CTkLabel(self.box_saude, text="⚪ Aguardando...", font=("Arial", 15, "bold"), text_color="#ccc")
        self.lbl_saude.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame_esq, text="Temperatura", font=("Arial", 12)).pack(pady=(8, 0))
        self.box_temp = ctk.CTkFrame(frame_esq, fg_color="#333", width=150, height=52, corner_radius=8)
        self.box_temp.pack(pady=4)
        self.box_temp.pack_propagate(False)
        self.lbl_temp = ctk.CTkLabel(self.box_temp, text="-- °C", font=("Arial", 18, "bold"), text_color="#ccc")
        self.lbl_temp.place(relx=0.5, rely=0.5, anchor="center")

        # Metadados
        frame_dir = ctk.CTkFrame(frame_sup, fg_color="transparent")
        frame_dir.pack(side="left", fill="both", expand=True)

        self.campos = {}
        linhas = [
            ("Firmware", "Interface"),
            ("Número de Série", "Tipo de Disco"),
            ("Letra da Unidade", "Sistema de Arquivos"),
        ]

        for i, (campo1, campo2) in enumerate(linhas):
            ctk.CTkLabel(frame_dir, text=campo1, anchor="e").grid(row=i, column=0, padx=4, pady=3, sticky="e")
            entry1 = ctk.CTkEntry(frame_dir, height=24, fg_color="#2b2b2b")
            entry1.grid(row=i, column=1, padx=4, pady=3, sticky="we")
            entry1.insert(0, "---")
            entry1.configure(state="readonly")
            self.campos[campo1] = entry1

            ctk.CTkLabel(frame_dir, text=campo2, anchor="e").grid(row=i, column=2, padx=4, pady=3, sticky="e")
            entry2 = ctk.CTkEntry(frame_dir, height=24, fg_color="#2b2b2b")
            entry2.grid(row=i, column=3, padx=4, pady=3, sticky="we")
            entry2.insert(0, "---")
            entry2.configure(state="readonly")
            self.campos[campo2] = entry2

        ctk.CTkLabel(frame_dir, text="Tempo Total Ligado", text_color="#70a1ff", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=4, pady=(8, 4), sticky="e")
        self.campos["Tempo Total Ligado"] = ctk.CTkEntry(frame_dir, height=28, fg_color="#0f2a4a", text_color="#70a1ff", font=("Arial", 13, "bold"))
        self.campos["Tempo Total Ligado"].grid(row=3, column=1, columnspan=3, padx=4, pady=(8, 4), sticky="we")
        self.campos["Tempo Total Ligado"].insert(0, "---")
        self.campos["Tempo Total Ligado"].configure(state="readonly")

        frame_dir.columnconfigure(1, weight=1)
        frame_dir.columnconfigure(3, weight=1)

        # Tabela S.M.A.R.T.
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25, borderwidth=0)
        style.configure("Treeview.Heading", background="#333", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f538d")])

        frame_tab = ctk.CTkFrame(self)
        frame_tab.pack(fill="both", expand=True, padx=20, pady=10)

        colunas = ("ID", "Nome do Atributo", "Atual", "Pior", "Limiar", "Valor Bruto")
        self.tree = ttk.Treeview(frame_tab, columns=colunas, show="headings")

        # CONFIGURAÇÃO DE CORES PARA OS CÍRCULOS
        self.tree.tag_configure("verde", foreground="#2ed573")
        self.tree.tag_configure("amarelo", foreground="#ffa502")
        self.tree.tag_configure("vermelho", foreground="#ff4757")

        larguras = [60, 320, 70, 70, 70, 140]
        for col, larg in zip(colunas, larguras):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=larg, anchor="center" if col != "Nome do Atributo" else "w")

        scroll = ttk.Scrollbar(frame_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.btn_html = ctk.CTkButton(
            self, text="📄 Exportar Relatório HTML", font=("Arial", 14, "bold"), 
            height=38, fg_color="#27ae60", hover_color="#2ecc71", 
            state="disabled", command=self.salvar_html
        )
        self.btn_html.pack(pady=12)

    def iniciar_scan(self):
        self.btn_scan.configure(state="disabled", text="⏳ Escaneando...")
        self.lbl_modelo.configure(text="Lendo sensores e hardware...", text_color="#70a1ff")
        self.update()

        threading.Thread(target=self.processar_scan_bg, daemon=True).start()

    def processar_scan_bg(self):
        dados = obter_dados_reais_disco()
        self.after(0, self.atualizar_interface, dados)

    def atualizar_interface(self, dados):
        self.btn_scan.configure(state="normal", text="🔄 Atualizar Leitura")
        
        if not dados:
            self.lbl_modelo.configure(text="Erro de Leitura (Execute como Admin)", text_color="#ff4757")
            messagebox.showerror("Erro", "Não foi possível ler os discos. Tente executar o programa como Administrador.")
            return

        self.dados_atuais = dados

        self.lbl_modelo.configure(text=dados["Modelo"], text_color="#fff")
        
        self.box_saude.configure(fg_color=dados["Cor_Saude"])
        self.lbl_saude.configure(text=dados["Status de Saúde"], text_color="#000")

        self.box_temp.configure(fg_color="#1e90ff")
        self.lbl_temp.configure(text=dados["Temperatura"], text_color="#fff")

        for chave, entry in self.campos.items():
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, dados.get(chave, "---"))
            entry.configure(state="readonly")

        for item in self.tree.get_children():
            self.tree.delete(item)

        if dados["Atributos_SMART"]:
            for attr in dados["Atributos_SMART"]:
                # attr: (id_script, id_html, nome, atual, pior, limiar, raw_hex, tag_cor)
                val_tree = (attr[0], attr[2], attr[3], attr[4], attr[5], attr[6])
                self.tree.insert("", "end", values=val_tree, tags=(attr[7],))
        else:
            self.tree.insert("", "end", values=("--", "S.M.A.R.T. restrito pelo Sistema/Driver", "--", "--", "--", "--"))

        self.btn_html.configure(state="normal")

    def salvar_html(self):
        if not self.dados_atuais: return

        nome = "Relatorio_Disco_Real.html"
        linhas = ""
        for attr in self.dados_atuais["Atributos_SMART"]:
            # attr: (id_script, id_html, nome, atual, pior, limiar, raw_hex, tag_cor)
            linhas += f"<tr><td style='text-align:center;'>{attr[1]}</td><td style='text-align:left'>{attr[2]}</td><td>{attr[3]}</td><td>{attr[4]}</td><td>{attr[5]}</td><td>{attr[6]}</td></tr>"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório — {self.dados_atuais['Modelo']}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#121212;color:#e0e0e0;padding:24px;margin:0}}
.card{{max-width:980px;margin:auto;background:#1e1e1e;padding:28px;border-radius:12px;border:1px solid #333;box-shadow:0 8px 24px rgba(0,0,0,.5)}}
h1{{color:#70a1ff;text-align:center;font-size:22px;margin-top:0; border-bottom: 1px solid #333; padding-bottom: 15px;}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}}
.box{{background:#2b2b2b;padding:10px 12px;border-radius:6px;font-family:Consolas,monospace;border:1px solid #444; color:#fff;}}
.label{{font-weight:600;color:#aaa;font-size:11px;display:block;margin-bottom:4px}}
.destaque{{grid-column:span 4;background:#0f2a4a;border-color:#1e90ff;color:#70a1ff;font-weight:bold;font-size:15px}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{border:1px solid #333;padding:10px;text-align:center;font-size:13px}}
th{{background:#1e90ff;color:#fff}}
tr:nth-child(even){{background:#262626}}
tr:hover{{background:#333}}
.bolinha-saude {{ background:{self.dados_atuais['Cor_Saude']}; color: #000; font-weight: bold; border-color: {self.dados_atuais['Cor_Saude']}; }}
</style>
</head>
<body>
<div class="card">
<h1>{self.dados_atuais['Modelo']}</h1>
<div class="grid">
  <div><span class="label">STATUS (Saúde)</span><div class="box bolinha-saude">{self.dados_atuais['Status de Saúde']}</div></div>
  <div><span class="label">TEMPERATURA</span><div class="box" style="background:#1e90ff; border-color:#1e90ff; font-weight:bold;">{self.dados_atuais['Temperatura']}</div></div>
  <div><span class="label">INTERFACE</span><div class="box">{self.dados_atuais['Interface']}</div></div>
  <div><span class="label">TIPO DE MÍDIA</span><div class="box">{self.dados_atuais['Tipo de Disco']}</div></div>
  <div><span class="label">FIRMWARE</span><div class="box">{self.dados_atuais['Firmware']}</div></div>
  <div><span class="label">Nº DE SÉRIE</span><div class="box">{self.dados_atuais['Número de Série']}</div></div>
  <div><span class="label">UNIDADES</span><div class="box">{self.dados_atuais['Letra da Unidade']}</div></div>
  <div><span class="label">SISTEMA DE ARQUIVOS</span><div class="box">{self.dados_atuais['Sistema de Arquivos']}</div></div>
  <div class="destaque"><span class="label" style="color:#1e90ff">TEMPO TOTAL LIGADO</span>{self.dados_atuais['Tempo Total Ligado']}</div>
</div>
<table>
<thead><tr>
<th>ID</th><th style="text-align:left">Atributo S.M.A.R.T.</th>
<th>Atual</th><th>Pior</th><th>Limiar</th><th>Valor Bruto (Hex)</th>
</tr></thead>
<tbody>{linhas}</tbody>
</table>
</div>
</body>
</html>"""

        caminho = os.path.abspath(nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(f"file://{caminho}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
