import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import json
import re
import os
import datetime

# ===== LISTA DE PACOTES SEGUROS PARA REMOVER (BLOATWARE COMUM) =====
SEGUROS_PARA_REMOVER = {

    # === OneDrive / Skype / Teams ===
    "Microsoft.OneDriveSync", "Microsoft.OneDrive", "Microsoft.SkypeApp",
    "Microsoft.Teams", "Microsoft.MixedReality.Portal",

    # === Bloatware / Apps pré-instalados ===
    "Microsoft.GetHelp", "Microsoft.Getstarted", "Microsoft.Messaging",
    "Microsoft.Microsoft3DViewer", "Microsoft.MicrosoftOfficeHub",
    "Microsoft.MicrosoftSolitaireCollection", "Microsoft.MicrosoftStickyNotes",
    "Microsoft.MSPaint", "Microsoft.Office.OneNote", "Microsoft.OutlookForWindows",
    "Microsoft.People", "Microsoft.ScreenSketch", "Microsoft.StorePurchaseApp",
    "Microsoft.Wallet", "Microsoft.WebMediaExtensions", "Microsoft.WebpImageExtension",
    "Microsoft.Windows.DevHome", "Microsoft.WindowsAlarms", "Microsoft.WindowsCalculator",
    "Microsoft.WindowsCamera", "Microsoft.WindowsCommunicationsApps",
    "Microsoft.WindowsFeedbackHub", "Microsoft.WindowsMaps", "Microsoft.WindowsNotepad",
    "Microsoft.WindowsSoundRecorder", "Microsoft.WindowsStore",
    "Microsoft.ZuneMusic", "Microsoft.ZuneVideo",
    "Microsoft.BingWeather", "Microsoft.BingNews", "Microsoft.BingSports",
    "Microsoft.BingFinance", "Microsoft.BingFoodAndDrink", "Microsoft.BingHealthAndFitness",
    "Microsoft.BingTravel", "Microsoft.Advertising.Xaml",
    "Microsoft.Windows.Photos",
    "Microsoft.YourPhone",

    # === Visual Studio Code & Insiders ===
    "Microsoft.VisualStudioCode",
    "Microsoft.VisualStudioCode.Insiders",

    # === Visual Studio 2022 ===
    "Microsoft.VisualStudio.2022.Community",
    "Microsoft.VisualStudio.2022.Professional",
    "Microsoft.VisualStudio.2022.Enterprise",

    # === App Connector ===
    "Microsoft.Appconnector",

    # === Cortana ===
    "Microsoft.549981C3F5F10",

    # === Extensões de imagem (HEIF, WebP) ===
    "Microsoft.HEIFImageExtension", "Microsoft.VP9VideoExtensions", "Microsoft.WebpImageExtension",
    "Microsoft.WebMediaExtensions", "Microsoft.VP9VideoExtensions",

    # === RunTimes .NET / VC++ avulsos (versões antigas não críticas) ===
    "Microsoft.NET.Native.Framework.2.2", "Microsoft.NET.Native.Framework.2.1",
    "Microsoft.NET.Native.Runtime.2.2", "Microsoft.NET.Native.Runtime.2.1",
    "Microsoft.UI.Xaml.2.0", "Microsoft.UI.Xaml.2.1", "Microsoft.UI.Xaml.2.2",
    "Microsoft.UI.Xaml.2.3", "Microsoft.UI.Xaml.2.4", "Microsoft.UI.Xaml.2.5",

    # === Apps de terceiros ===
    "SpotifyAB.SpotifyMusic", "Disney.37853FC22B2CE", "Netflix.Netflix",
    "AdobeSystemsIncorporated.AdobeCreativeCloud", "Canva.Canva",
    "Discord.Discord", "WhatsApp.WhatsApp", "Telegram.TelegramDesktop",
    "SlackTechnologies.Slack", "Zoom.Zoom",
    "Oracle.JavaRuntimeEnvironment", "Oracle.JDK",
    "AdoptOpenJDK.OpenJDK", "EclipseAdoptium.Temurin.JDK",
}

# ===== PACOTES CRÍTICOS DO SISTEMA (NÃO REMOVER) =====
CRITICOS = {
    "Microsoft.DesktopAppInstaller",
    "Microsoft.PowerShell",
    "Microsoft.WindowsTerminal",
    "Microsoft.WindowsAppRuntime",
    "Microsoft.Services.Store",
    "Microsoft.StoreFoundation",
    "Microsoft.VCLibs.140.00",
    "Microsoft.VCLibs.140.00.UWPDesktop",
    "Microsoft.VCLibs.14",
    "Microsoft.VCLibs.Desktop.14",
    "Microsoft.VCRedist.20xx",
    "Microsoft.UI.Xaml.*",
    "Microsoft.WindowsAppRuntime.*",
    "Microsoft.DirectX",
    "Microsoft.GameInput",
    "Microsoft.NET.Native.Framework",
    "Microsoft.NET.Native.Runtime",
    "Microsoft.Services.Store.Engagement",
    "Microsoft.UI.Xaml",
    "Microsoft.UI",
    "Microsoft.Winget.Source",
    "Microsoft.VCLibs.110.00.UWPDesktop",
    "Microsoft.VCLibs.120.00.UWPDesktop",
    "Microsoft.VCLibs.140.00.UWPDesktop",
    "Microsoft.VC++",
    "Microsoft.VisualCPlusPlus",
    "Microsoft.VisualCpp",
    "Microsoft Visual C++",
    "{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}",
    "Redistributable",
    "14.51.36231.0", "14.42.34438.0",
}

CRITICOS_EDGE = {
    "Microsoft.MicrosoftEdge",
    "Microsoft.Edge",
    "Microsoft.EdgeWebView2Runtime",
}
CRITICOS.update(CRITICOS_EDGE)

XBOX_PACKAGES = {
    "Microsoft.XboxGameBar",
    "Microsoft.XboxGameBarPlugin",
    "Microsoft.XboxGamingOverlay",
    "Microsoft.XboxIdentityProvider",
    "Microsoft.XboxSpeechToTextOverlay",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxApp",
    "Microsoft.GamingServices",
    "Microsoft.XboxGameCallableUI",
    "Microsoft.XboxGameOverlay",
}

PACOTES_CUSTOM_BRANCO = {
    "Microsoft.HEIFImageExtension",
    "Microsoft.WebpImageExtension",
    "Microsoft.WebMediaExtensions",
    "Microsoft.VP9VideoExtensions",
    "Microsoft.WindowsCalculator",
    "Microsoft.Appconnector",
    "Microsoft.549981C3F5F10",
    "Microsoft.Windows.Photos",
    "Microsoft.StorePurchaseApp",
    "Microsoft.WindowsMaps",
    "Microsoft.Wallet",
    "Microsoft.WindowsStore",
    "Microsoft.GetHelp",
    "Microsoft.OutlookForWindows",
    "Microsoft.People",
    "Microsoft.WindowsAlarms",
    "Microsoft.YourPhone",
    "Microsoft.Microsoft3DViewer",
    "7B1FCD52-8F6B-4F12-A143-361EA39F5E7C",
    "0746492E-47B6-4251-940C-44462DFD74BB",
}

DRIVERS_HARDWARE_PREFIXOS = {
    "Intel.Proset", "Intel.ProSet", "Intel.Wireless", "Intel.WiFi",
    "Intel.Bluetooth", "Intel.Network", "Intel.Ethernet",
    "Realtek.Realtek", "Realtek.Rtl", "Realtek.RTK", "Realtek.Audio",
    "Realtek.Ethernet", "Realtek.Wireless", "Realtek.Bluetooth",
    "Qualcomm.Wireless", "Qualcomm.Atheros", "Qualcomm.Bluetooth",
    "Qualcomm.Network", "Qualcomm.Cellular", "Qualcomm.Driver",
    "Broadcom.Broadcom", "Broadcom.Wireless", "Broadcom.Bluetooth",
    "Broadcom.Network", "Broadcom.802",
    "MediaTek.Wireless", "MediaTek.Bluetooth", "MediaTek.Network",
    "MediaTek.Driver",
    "TPLink.TPLink", "TP-Link.Wireless",
    "Dell.DellWireless", "Dell.WiFi", "Dell.Bluetooth",
    "Lenovo.Wireless", "Lenovo.Bluetooth",
    "B3142297-C1B4-41F0-87BE-4E5525583623",
    "NVIDIA.NVIDIA", "NVIDIA.Graphics", "NVIDIA.Display",
    "NVIDIA.PhysX", "NVIDIA.GeForce", "NVIDIA.Driver",
    "AMD.AMD", "AMD.Radeon", "AMD.Adrenalin", "AMD.Graphics",
    "AMD.Chipset", "AMD.Ryzen", "AMD.RadeonSoftware",
    "AMD.Catalyst", "AMD.CatalystInstallManager",
    "Intel.Graphics", "Intel.Display", "Intel.GPU",
    "Intel.Arc", "Intel.Iris",
    "Realtek.Audio", "Realtek.HDA", "Realtek.HighDefinitionAudio",
    "VIA.Audio", "VIA.VIA",
    "Creative.Creative", "Creative.Sound", "Creative.Audio",
    "Dolby.Dolby", "Dolby.Audio",
    "Intel.Chipset", "Intel.INF", "Intel.ManagementEngine",
    "Intel.ME", "Intel.SerialIO", "Intel.SSD",
    "AMD.Chipset", "AMD.GPIO", "AMD.SMBus",
    "ASMedia.ASMedia", "ASMedia.USB",
    "NVMExpress", "NVMe",
    "Intel.Thunderbolt", "Intel.USB",
    "AMD.USB",
    "DisplayLink.DisplayLink", "DisplayLink.Graphics",
    "Dell.Dock", "Dell.Thunderbolt", "Dell.USB",
    "Lenovo.Dock", "Lenovo.USB", "Lenovo.Thunderbolt",
    "HP.Dock", "HP.USB", "HP.Thunderbolt",
    "Intel.RST", "Intel.Storage", "Intel.RapidStorage",
    "AMD.Storage", "AMD.Raid",
    "Samsung.SSD", "Samsung.NVMe", "Samsung.Magician",
    "WesternDigital.WD", "WesternDigital.SSD",
    "Crucial.Storage", "Micron.Storage",
    "SKHynix.Storage", "SKHynix.SSD",
    "Microsoft.Camera", "Microsoft.Webcam",
    "Realtek.Camera", "Intel.Camera",
    "Synaptics.Synaptics", "Synaptics.TouchPad", "Synaptics.Pointing",
    "ELAN.ELAN", "ELAN.Touchpad", "ELAN.Input",
    "Alps.Alps", "Alps.Touchpad",
    "Wacom.Wacom", "Wacom.Tablet",
    "Dell.Display", "Dell.Monitor",
    "LG.Display", "LG.Monitor",
    "Samsung.Display", "Samsung.Monitor",
    "Qualcomm.Modem", "Qualcomm.Mobile",
    "Samsung.Modem", "Samsung.Mobile",
    "Mediatek.Modem", "Mediatek.Mobile",
    "Apple.Modem", "Apple.Mobile", "Apple.iPhone",
    "HP.HP", "HP.Print", "HP.Scan",
    "Canon.Canon", "Canon.Print", "Canon.Scan",
    "Epson.Epson", "Epson.Print", "Epson.Scan",
    "Brother.Brother", "Brother.Print",
    "Xerox.Xerox", "Xerox.Print",
    "Standard.NVMe", "Standard.SATA", "Standard.ATA",
    "Microsoft.HyperV", "Microsoft.Virtual",
    "Oracle.VirtualBox", "VMware.VMware",
}

PALAVRAS_DRIVER = [
    "driver", "drivers", "chipset", "bluetooth", "wireless", "wifi",
    "ethernet", "network", "lan", "modem", "cellular", "mobile",
    "graphics", "display", "audio", "sound", "hda", "nvme", "ssd",
    "storage", "raid", "touchpad", "keyboard", "webcam", "camera",
    "usb", "thunderbolt", "dock", "sensors",
    "catalyst", "radeon", "geforce", "adrenalin",
]

GUIDS_VC_REDIST = {
    "{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}",
    "{9A25302D-30C0-39D9-BD6F-21E6EC160475}",
    "{1F1C2DFC-2D24-3E06-BCB8-725134ADF989}",
    "{7299052B-02A4-4627-81F2-1818DA5D550D}",
    "{0F8FB34E-675E-42ED-850B-29D98C2ECE08}",
    "{ad8a2fa1-06e7-4b0d-927d-6e54b3d31028}",
}


# =====================================================================
#  DIRETÓRIOS ONDE PROCURAR EXECUTÁVEIS (FALLBACK)
# =====================================================================
DIRETORIOS_PROGRAMAS = [
    os.environ.get("ProgramFiles", "C:\\Program Files"),
    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps"),
    os.path.join(os.environ.get("ProgramData", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    "C:\\Program Files\\WindowsApps",
]


class WingetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WINGET UNINSTALL & INSTALL + FILTRO CATEGORIA + CAMINHOS")
        self.root.geometry("1400x750")
        self.root.state("zoomed")
        self.root.minsize(1050, 550)
        self.root.configure(bg="#0a0a0a")

        style = ttk.Style()
        style.theme_use("clam")

        BG = "#0a0a0a"
        FG = "#00ff41"
        FG_ORANGE = "#ff9f1c"
        SELECT_BG = "#003300"
        ENTRY_BG = "#111111"
        BORDER = "#00aa33"

        style.configure(".", background=BG, foreground=FG, fieldbackground=ENTRY_BG)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=("Consolas", 10))
        style.configure("TLabelframe", background=BG, foreground=FG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG, font=("Consolas", 10, "bold"))
        style.configure("TButton", background="#111111", foreground=FG, borderwidth=1, focusthickness=3, focuscolor=BORDER)
        style.map("TButton",
                  background=[("active", "#003300"), ("disabled", "#222222")],
                  foreground=[("disabled", "#555555")])

        style.configure("Treeview",
                        background="#0d0d0d",
                        foreground=FG,
                        fieldbackground="#0d0d0d",
                        borderwidth=0,
                        rowheight=28,
                        font=("Consolas", 10))
        style.configure("Treeview.Heading",
                        background="#111111",
                        foreground=FG,
                        font=("Consolas", 10, "bold"),
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", SELECT_BG)],
                  foreground=[("selected", "#00ff88")])
        style.map("Treeview.Heading",
                  background=[("active", "#003300")])

        style.configure("TEntry",
                        fieldbackground=ENTRY_BG,
                        foreground=FG_ORANGE,
                        insertcolor=FG_ORANGE,
                        borderwidth=1)
        style.configure("Horizontal.TScrollbar", background="#111111", troughcolor=BG, arrowcolor=FG)
        style.configure("Vertical.TScrollbar", background="#111111", troughcolor=BG, arrowcolor=FG)
        style.configure("Status.TLabel", background="#050505", foreground="#00aa33", font=("Consolas", 9))

        # ===== Cache de caminhos de instalação =====
        self.cache_caminhos = {}     # winget_id.lower() -> caminho ou executável
        self.cache_nomes_para_ids = {}  # nome.lower() -> winget_id.lower()

        # ===== Context Menu (botão direito) =====
        self.context_menu = tk.Menu(root, tearoff=0, bg="#111111", fg="#00ff41",
                                    activebackground="#003300", activeforeground="#00ff88",
                                    font=("Consolas", 10))
        self.context_menu.add_command(
            label="🔍 Abrir local do arquivo",
            command=self.abrir_local_arquivo
        )

        # ===== Frame superior =====
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill=tk.X)

        title = ttk.Label(top_frame, text="█ WINGET UNINSTALL & INSTALL + CAMINHOS █ ", font=("Consolas", 16, "bold"))
        title.pack(side=tk.LEFT)

        self.btn_list = ttk.Button(top_frame, text="[ LISTAR PACOTES ]", command=self.listar_pacotes)
        self.btn_list.pack(side=tk.LEFT, padx=5)

        self.btn_desatualizados = ttk.Button(
            top_frame,
            text="[ MOSTRAR DESATUALIZADOS ]",
            command=self.listar_desatualizados
        )
        self.btn_desatualizados.pack(side=tk.LEFT, padx=5)

        self.btn_salvar_html = ttk.Button(
            top_frame,
            text="[ SALVAR HTML ]",
            command=self.salvar_html
        )
        self.btn_salvar_html.pack(side=tk.LEFT, padx=5)

        # ================================================================
        #  FILTRO POR CATEGORIA
        # ================================================================
        filter_frame = ttk.LabelFrame(root, text=" Filtro por Categoria ", padding=8)
        filter_frame.pack(fill=tk.X, padx=10, pady=2)

        self.filtros = {}
        categorias = [
            ("seguro",        "✔️ Seguro",          True),
            ("xbox",          "🎮 Xbox",            False),
            ("custom_branco", "⬜ Custom",          False),
            ("nao_seguro",    "❌ Não Recomendado", False),
            ("driver",        "🧿 Driver/HW",       False),
            ("critico",       "⚠️ Crítico",         False),
        ]

        for i, (chave, rotulo, padrao) in enumerate(categorias):
            var = tk.BooleanVar(value=padrao)
            self.filtros[chave] = var
            cb = ttk.Checkbutton(
                filter_frame,
                text=rotulo,
                variable=var,
                command=self.aplicar_filtro
            )
            cb.grid(row=0, column=i, padx=8, sticky=tk.W)

        btn_todos = ttk.Button(filter_frame, text="[ TODOS ]", command=self.marcar_todos_filtros)
        btn_todos.grid(row=0, column=len(categorias), padx=15)

        btn_nenhum = ttk.Button(filter_frame, text="[ NENHUM ]", command=self.desmarcar_todos_filtros)
        btn_nenhum.grid(row=0, column=len(categorias) + 1, padx=5)

        filter_frame.columnconfigure(len(categorias) + 2, weight=1)

        # =====================================================================
        #  TREEVIEW — COLUNA CAMINHO POR ÚLTIMO
        # =====================================================================
        tree_frame = ttk.LabelFrame(root, text=" Pacotes Instalados ", padding=5)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("seguro", "name", "id", "version", "available", "source", "caminho")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="PROGRAMA", anchor=tk.W)
        self.tree.heading("id", text="ID", anchor=tk.W)
        self.tree.heading("version", text="VERSÃO", anchor=tk.W)
        self.tree.heading("available", text="DISPONÍVEL", anchor=tk.W)
        self.tree.heading("source", text="FONTE", anchor=tk.W)
        self.tree.heading("caminho", text="📁 CAMINHO DE INSTALAÇÃO", anchor=tk.W)

        self.tree.column("seguro", width=30, anchor=tk.W, minwidth=40)
        self.tree.column("name", width=700, anchor=tk.W)
        self.tree.column("id", width=560, anchor=tk.W)
        self.tree.column("version", width=170, anchor=tk.W)
        self.tree.column("available", width=150, anchor=tk.W)
        self.tree.column("source", width=80, anchor=tk.W)
        self.tree.column("caminho", width=750, anchor=tk.W)

        self.tree.tag_configure("seguro", foreground="#00ff41")
        self.tree.tag_configure("nao_seguro", foreground="#ff3333")
        self.tree.tag_configure("critico", foreground="#ff9f1c")
        self.tree.tag_configure("driver", foreground="#3399ff")
        self.tree.tag_configure("xbox", foreground="#9b59b6")
        self.tree.tag_configure("custom_branco", foreground="#ffffff")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Binds
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Button-3>", self.mostrar_context_menu)  # Botão direito

        # =====================================================================
        #  FRAME DE OPERAÇÕES
        # =====================================================================
        action_frame = ttk.LabelFrame(root, text=" Operações por ID ", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Linha 0: Desinstalar / Atualizar
        ttk.Label(action_frame, text="ID do programa:").grid(row=0, column=0, sticky=tk.W, padx=5)

        self.entry_id = ttk.Entry(action_frame, width=50, font=("Consolas", 11))
        self.entry_id.grid(row=0, column=1, padx=5, sticky=tk.EW)

        self.btn_uninstall = ttk.Button(action_frame, text="[ DESINSTALAR ]", command=self.desinstalar)
        self.btn_uninstall.grid(row=0, column=2, padx=5)

        self.btn_upgrade = ttk.Button(action_frame, text="[ ATUALIZAR ]", command=self.atualizar)
        self.btn_upgrade.grid(row=0, column=3, padx=5)

        # Linha 1: Instalar pacote
        ttk.Label(action_frame, text="📦 Instalar (ID ou nome):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(8, 0))

        self.entry_install = ttk.Entry(action_frame, width=50, font=("Consolas", 11))
        self.entry_install.grid(row=1, column=1, padx=5, pady=(8, 0), sticky=tk.EW)

        self.btn_install = ttk.Button(action_frame, text="[ INSTALAR ]", command=self.instalar)
        self.btn_install.grid(row=1, column=2, padx=5, pady=(8, 0))

        action_frame.columnconfigure(1, weight=1)

        # ===== Status bar =====
        self.status = ttk.Label(root, text="> Sistema pronto. Aguardando comando...", style="Status.TLabel", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM, ipady=4)

        # ===== Legenda =====
        legenda = ttk.Label(
            root,
            text=(
                "✔️ Seguro remover  |  🎮 Xbox  |  ⬜ Custom (branco)  |  "
                "❌ Não recomendado  |  🧿 Driver/HW (cuidado)  |  "
                "⚠️ Crítico (não remover)  |  Clique = copia ID  | 📦 Instalar ID ou Nome  |  "
                "🖱️ Botão direito = 🔍 Abrir local"
            ),
            foreground="#00aa33",
            font=("Consolas", 9)
        )
        legenda.pack(pady=4)

        self.todos_os_itens = []
        self.ultimo_html = None

    # =====================================================================
    #  CONTEXT MENU — LUPA (BOTÃO DIREITO)
    # =====================================================================
    def mostrar_context_menu(self, event):
        """Exibe o menu de contexto ao clicar com botão direito na tree."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.on_select(None)
            # Atualiza o label da lupa com o caminho disponível
            valores = self.tree.item(item, "values")
            if valores and len(valores) >= 7 and valores[6]:
                self.context_menu.entryconfig(
                    0,
                    label=f"🔍 Abrir local: {os.path.basename(valores[6]) if os.path.isfile(valores[6]) else 'pasta'}"
                )
            else:
                self.context_menu.entryconfig(0, label="🔍 Abrir local do arquivo")
            self.context_menu.post(event.x_root, event.y_root)

    def abrir_local_arquivo(self):
        """Abre o local do arquivo no Windows Explorer."""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showinfo("Aviso", "Selecione um pacote primeiro.")
            return

        valores = self.tree.item(selecionado[0], "values")
        if not valores or len(valores) < 7:
            return

        caminho = valores[6]  # Coluna CAMINHO (índice 6)
        if not caminho or caminho == "-":
            messagebox.showinfo("Caminho não encontrado", "Este pacote não possui um caminho de instalação registrado.")
            return

        try:
            if os.path.isfile(caminho):
                # Seleciona o arquivo no Explorer
                subprocess.run(["explorer", "/select,", caminho],
                               creationflags=subprocess.CREATE_NO_WINDOW)
            elif os.path.isdir(caminho):
                # Abre a pasta diretamente
                os.startfile(caminho)
            else:
                # Tenta abrir a pasta pai
                pasta = os.path.dirname(caminho)
                if pasta and os.path.isdir(pasta):
                    os.startfile(pasta)
                else:
                    messagebox.showwarning("Caminho inválido", f"O caminho não existe:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o local.\n{str(e)}")

    # =====================================================================
    #  COLETAR CAMINHOS DE INSTALAÇÃO (BATCH)
    # =====================================================================
    def coletar_todos_os_caminhos(self):
        """
        Coleta caminhos de instalação de TODAS as fontes possíveis em lotes.
        Preenche self.cache_caminhos e self.cache_nomes_para_ids.
        """
        self.cache_caminhos.clear()
        self.cache_nomes_para_ids.clear()

        self.atualizar_status("Coletando caminhos de instalação...")

        # ---------------------------------------------------------------
        # 1. AppX/MSIX packages via PowerShell
        # ---------------------------------------------------------------
        try:
            ps_cmd = (
                'Get-AppxPackage -AllUsers | '
                'Select-Object @{N="Family";E={$_.PackageFamilyName}}, '
                '@{N="Name";E={$_.Name}}, '
                'InstallLocation | '
                'ConvertTo-Json -Compress'
            )
            resultado = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=30
            )
            if resultado.returncode == 0 and resultado.stdout.strip():
                dados = json.loads(resultado.stdout)
                if isinstance(dados, dict):
                    dados = [dados]
                for item in dados:
                    family = (item.get("Family") or "").strip()
                    name = (item.get("Name") or "").strip()
                    loc = (item.get("InstallLocation") or "").strip()
                    if family and loc:
                        self.cache_caminhos[family.lower()] = loc
                        nome_pkg = family.split("_")[0].lower() if "_" in family else family.lower()
                        self.cache_caminhos[nome_pkg] = loc
                    if name:
                        self.cache_nomes_para_ids[name.lower()] = family.lower() if family else name.lower()
        except Exception:
            pass

        # ---------------------------------------------------------------
        # 2. Registry Uninstall (Win32/MSI)
        # ---------------------------------------------------------------
        try:
            ps_cmd_reg = (
                'Get-ItemProperty '
                '"HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*", '
                '"HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" '
                '2>$null | '
                'Select-Object PSChildName, DisplayName, InstallLocation, DisplayIcon '
                '| ConvertTo-Json -Compress'
            )
            resultado = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd_reg],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=30
            )
            if resultado.returncode == 0 and resultado.stdout.strip():
                dados = json.loads(resultado.stdout)
                if isinstance(dados, dict):
                    dados = [dados]
                for item in dados:
                    pschild = (item.get("PSChildName") or "").strip()
                    disp_name = (item.get("DisplayName") or "").strip()
                    install_loc = (item.get("InstallLocation") or "").strip()
                    display_icon = (item.get("DisplayIcon") or "").strip()

                    caminho = ""
                    if display_icon and os.path.isfile(display_icon.split(",")[0]):
                        caminho = display_icon.split(",")[0]
                    elif install_loc and os.path.isdir(install_loc):
                        caminho = self._procurar_exe_no_diretorio(install_loc, disp_name)

                    if caminho and os.path.exists(caminho):
                        chaves = set()
                        if pschild:
                            chaves.add(pschild.lower())
                            chaves.add(pschild.strip("{}").lower())
                        if disp_name:
                            chaves.add(disp_name.lower())
                            nome_slug = disp_name.lower().replace(" ", "").replace("-", "").replace("_", "")
                            chaves.add(nome_slug)
                            self.cache_nomes_para_ids[disp_name.lower()] = pschild.lower() if pschild else disp_name.lower()

                        for chave in chaves:
                            if chave and chave not in self.cache_caminhos:
                                self.cache_caminhos[chave] = caminho
        except Exception:
            pass

        # ---------------------------------------------------------------
        # 3. WinGet Links Directory (portable symlinks)
        # ---------------------------------------------------------------
        try:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            links_dir = os.path.join(local_appdata, "Microsoft", "WinGet", "Links")
            if os.path.isdir(links_dir):
                for item in os.listdir(links_dir):
                    item_path = os.path.join(links_dir, item)
                    try:
                        if os.path.islink(item_path):
                            target = os.readlink(item_path)
                            if os.path.isfile(target):
                                self.cache_caminhos[item.lower()] = target
                        elif os.path.isfile(item_path):
                            self.cache_caminhos[item.lower()] = item_path
                    except Exception:
                        pass
        except Exception:
            pass

        # ---------------------------------------------------------------
        # 4. WinGet Packages Directory (portable package root)
        # ---------------------------------------------------------------
        try:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            pkg_dir = os.path.join(local_appdata, "Microsoft", "WinGet", "Packages")
            if os.path.isdir(pkg_dir):
                for item in os.listdir(pkg_dir):
                    item_path = os.path.join(pkg_dir, item)
                    if os.path.isdir(item_path):
                        self.cache_caminhos[item.lower()] = item_path
                        exe = self._procurar_exe_no_diretorio(item_path, item)
                        if exe:
                            self.cache_caminhos[item.lower()] = exe
        except Exception:
            pass

    def _procurar_exe_no_diretorio(self, diretorio, nome_referencia=""):
        """Procura recursivamente por um .exe relevante dentro de um diretório."""
        if not os.path.isdir(diretorio):
            return diretorio

        try:
            if nome_referencia:
                nome_curto = nome_referencia.split(".")[-1] if "." in nome_referencia else nome_referencia
                for root, dirs, files in os.walk(diretorio):
                    profundidade = root.replace(diretorio, "").count(os.sep)
                    if profundidade > 4:
                        dirs.clear()
                        continue
                    for f in files:
                        if f.lower().endswith(".exe") and nome_curto.lower() in f.lower():
                            return os.path.join(root, f)

            for root, dirs, files in os.walk(diretorio):
                profundidade = root.replace(diretorio, "").count(os.sep)
                if profundidade > 3:
                    dirs.clear()
                    continue
                for f in files:
                    if f.lower().endswith(".exe"):
                        nome_base = f.lower().replace(".exe", "")
                        if "unins" not in nome_base and "setup" not in nome_base and "install" not in nome_base:
                            return os.path.join(root, f)

            return diretorio
        except Exception:
            return diretorio

    def _buscar_caminho_por_nome(self, package_id, package_name=""):
        """Busca o caminho de instalação para um pacote usando todas as fontes."""
        id_lower = (package_id or "").lower().strip()
        name_lower = (package_name or "").lower().strip()

        # 1. Tenta lookup direto pelo ID no cache
        if id_lower in self.cache_caminhos:
            return self.cache_caminhos[id_lower]

        # 2. Tenta partes do ID
        if id_lower:
            partes = id_lower.replace(".", " ").split()
            for parte in partes:
                if parte in self.cache_caminhos:
                    return self.cache_caminhos[parte]
                for chave in self.cache_caminhos:
                    if parte in chave:
                        return self.cache_caminhos[chave]

        # 3. Tenta pelo nome do programa
        if name_lower:
            if name_lower in self.cache_caminhos:
                return self.cache_caminhos[name_lower]
            for chave, caminho in self.cache_caminhos.items():
                if name_lower in chave:
                    return caminho

        # 4. Tenta com o nome curto (última parte do ID)
        if id_lower and "." in id_lower:
            nome_curto = id_lower.split(".")[-1]
            if nome_curto in self.cache_caminhos:
                return self.cache_caminhos[nome_curto]
            for chave, caminho in self.cache_caminhos.items():
                if nome_curto in chave:
                    return caminho

        # 5. Fallback: escaneia diretórios comuns
        try:
            nome_busca = (name_lower or id_lower or "").replace(".", " ").split()[-1] if (name_lower or id_lower) else ""
            if nome_busca and len(nome_busca) > 2:
                for dir_base in DIRETORIOS_PROGRAMAS:
                    if not dir_base or not os.path.isdir(dir_base):
                        continue
                    try:
                        for item in os.listdir(dir_base):
                            if nome_busca in item.lower():
                                item_path = os.path.join(dir_base, item)
                                if os.path.isfile(item_path):
                                    self.cache_caminhos[id_lower] = item_path
                                    return item_path
                                elif os.path.isdir(item_path):
                                    exe = self._procurar_exe_no_diretorio(item_path, nome_busca)
                                    if exe:
                                        self.cache_caminhos[id_lower] = exe
                                        return exe
                    except Exception:
                        continue
        except Exception:
            pass

        return ""

    # =====================================================================
    #  CLASSIFICAR PACOTE
    # =====================================================================
    def classificar_pacote(self, package_id, package_name=""):
        if not package_id:
            return "nao_seguro"

        id_lower = package_id.lower()
        name_lower = package_name.lower()

        for guid in GUIDS_VC_REDIST:
            if guid.lower() in id_lower or guid.lower() in package_id:
                return "critico"

        for critico in CRITICOS:
            if package_id.startswith(critico) or critico.lower() in id_lower:
                return "critico"

        for custom in PACOTES_CUSTOM_BRANCO:
            if package_id.startswith(custom) or custom.lower() in id_lower:
                return "custom_branco"

        for xbox_pkg in XBOX_PACKAGES:
            if package_id.startswith(xbox_pkg) or xbox_pkg.lower() in id_lower:
                return "xbox"

        for prefixo in DRIVERS_HARDWARE_PREFIXOS:
            if package_id.startswith(prefixo) or prefixo.lower() in id_lower:
                return "driver"

        for palavra in PALAVRAS_DRIVER:
            if palavra in id_lower or palavra in name_lower:
                return "driver"

        for seguro in SEGUROS_PARA_REMOVER:
            if package_id.startswith(seguro) or seguro.lower() in id_lower:
                return "seguro"

        if package_id.startswith("Microsoft."):
            return "nao_seguro"

        if package_id.startswith("{") and package_id.endswith("}"):
            return "nao_seguro"

        if "MSIX" in id_lower or "8wekyb3d8bbwe" in id_lower:
            for seguro in SEGUROS_PARA_REMOVER:
                nome_seguro = seguro.lower().split(".")[-1] if "." in seguro else seguro.lower()
                if nome_seguro in id_lower or nome_seguro in name_lower:
                    return "seguro"
            return "nao_seguro"

        return "seguro"

    def atualizar_status(self, texto):
        self.status.config(text=f"> {texto}")
        self.root.update_idletasks()

    def on_select(self, event):
        selecionado = self.tree.selection()
        if selecionado:
            valores = self.tree.item(selecionado[0], "values")
            if valores and len(valores) >= 3:
                self.entry_id.delete(0, tk.END)
                self.entry_id.insert(0, valores[2])

    def on_double_click(self, event):
        self.on_select(event)

    # =====================================================================
    #  FILTRO POR CATEGORIA
    # =====================================================================
    def _inserir_e_aplicar_filtro(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        contagem = {"seguro": 0, "nao_seguro": 0, "critico": 0, "driver": 0, "xbox": 0, "custom_branco": 0}

        for pkg in self.todos_os_itens:
            c = pkg["classificacao"]
            if not self.filtros.get(c, tk.BooleanVar(value=True)).get():
                continue
            contagem[c] = contagem.get(c, 0) + 1

            if c == "seguro":
                icone, tag = "✔️", "seguro"
            elif c == "critico":
                icone, tag = "⚠️", "critico"
            elif c == "driver":
                icone, tag = "🧿", "driver"
            elif c == "xbox":
                icone, tag = "🎮", "xbox"
            elif c == "custom_branco":
                icone, tag = "⬜", "custom_branco"
            else:
                icone, tag = "❌", "nao_seguro"

            self.tree.insert(
                "", tk.END,
                values=(icone, pkg["nome"], pkg["id"], pkg["versao"],
                        pkg["available"], pkg["fonte"],
                        pkg.get("caminho", "")),
                tags=(tag,)
            )

        total = sum(contagem.values())
        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)
        self.btn_salvar_html.config(state=tk.NORMAL)
        self.atualizar_status(
            f"Lista carregada — {total} pacotes exibidos. "
            f"✔️ {contagem['seguro']} S | 🎮 {contagem['xbox']} X | ⬜ {contagem['custom_branco']} C | "
            f"❌ {contagem['nao_seguro']} NR | 🧿 {contagem['driver']} D | ⚠️ {contagem['critico']} C"
        )

    def aplicar_filtro(self):
        if not self.todos_os_itens:
            return

        selecionado_antes = self.tree.selection()
        id_selecionado = None
        if selecionado_antes:
            valores = self.tree.item(selecionado_antes[0], "values")
            if valores and len(valores) >= 3:
                id_selecionado = valores[2]

        self._inserir_e_aplicar_filtro()

        if id_selecionado:
            for child in self.tree.get_children():
                child_val = self.tree.item(child, "values")
                if len(child_val) >= 3 and child_val[2] == id_selecionado:
                    self.tree.selection_set(child)
                    self.tree.focus(child)
                    self.on_select(None)
                    break

    def marcar_todos_filtros(self):
        for var in self.filtros.values():
            var.set(True)
        self.aplicar_filtro()

    def desmarcar_todos_filtros(self):
        for var in self.filtros.values():
            var.set(False)
        self.aplicar_filtro()

    # =====================================================================
    #  LISTAR PACOTES
    # =====================================================================
    def listar_pacotes(self):
        self.btn_list.config(state=tk.DISABLED)
        self.btn_desatualizados.config(state=tk.DISABLED)
        self.btn_salvar_html.config(state=tk.DISABLED)
        self.atualizar_status("Executando winget list... aguarde...")

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.todos_os_itens.clear()

        def tarefa():
            self.coletar_todos_os_caminhos()

            try:
                resultado = subprocess.run(
                    ["winget", "list", "--output", "json"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if resultado.returncode == 0 and resultado.stdout.strip():
                    try:
                        dados = json.loads(resultado.stdout)
                        pacotes = dados.get("Sources", [{}])[0].get("Packages", [])
                        self.root.after(0, lambda: self.preencher_tree_json(pacotes, todos=True))
                        return
                    except json.JSONDecodeError:
                        pass

                resultado = subprocess.run(
                    ["winget", "list"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                self.root.after(0, lambda: self.preencher_tree_texto(resultado.stdout, todos=True))

            except FileNotFoundError:
                self.root.after(0, lambda: self.mostrar_erro("Winget não encontrado. Instale o App Installer."))
            except Exception as e:
                self.root.after(0, lambda: self.mostrar_erro(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    # =====================================================================
    #  LISTAR DESATUALIZADOS
    # =====================================================================
    def listar_desatualizados(self):
        self.btn_list.config(state=tk.DISABLED)
        self.btn_desatualizados.config(state=tk.DISABLED)
        self.btn_salvar_html.config(state=tk.DISABLED)
        self.atualizar_status("Buscando programas desatualizados...")

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.todos_os_itens.clear()

        def tarefa():
            self.coletar_todos_os_caminhos()

            try:
                resultado = subprocess.run(
                    ["winget", "upgrade", "--include-unknown", "--output", "json"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if resultado.returncode == 0 and resultado.stdout.strip():
                    try:
                        dados = json.loads(resultado.stdout)
                        pacotes = dados.get("Sources", [{}])[0].get("Packages", [])
                        self.root.after(0, lambda: self.preencher_tree_json(pacotes, todos=True, so_desatualizados=True))
                        return
                    except json.JSONDecodeError:
                        pass

                resultado = subprocess.run(
                    ["winget", "upgrade", "--include-unknown"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                self.root.after(0, lambda: self.preencher_tree_texto(resultado.stdout, todos=True, so_desatualizados=True))

            except FileNotFoundError:
                self.root.after(0, lambda: self.mostrar_erro("Winget não encontrado."))
            except Exception as e:
                self.root.after(0, lambda: self.mostrar_erro(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    # =====================================================================
    #  PREENCHER TREE (JSON e TEXTO)
    # =====================================================================
    def preencher_tree_json(self, pacotes, todos=False, so_desatualizados=False):
        if todos:
            self.todos_os_itens.clear()

        for pkg in pacotes:
            nome = pkg.get("Name", "")
            id_ = pkg.get("Id", "") or pkg.get("PackageIdentifier", "")
            versao = pkg.get("Version", "")
            disponivel = (pkg.get("AvailableVersion") or pkg.get("Available") or "")
            fonte = pkg.get("Source", "") or ""
            classificacao = self.classificar_pacote(id_, nome)

            caminho = self._buscar_caminho_por_nome(id_, nome)

            item_dict = {
                "nome": nome, "id": id_, "versao": versao,
                "caminho": caminho,
                "available": disponivel, "fonte": fonte, "classificacao": classificacao
            }
            if so_desatualizados and not disponivel:
                continue
            if todos:
                self.todos_os_itens.append(item_dict)

        self._inserir_e_aplicar_filtro()

    def preencher_tree_texto(self, texto, todos=False, so_desatualizados=False):
        linhas = texto.strip().splitlines()
        if todos:
            self.todos_os_itens.clear()

        for linha in linhas:
            if not linha.strip() or linha.startswith("-") or ("Name" in linha and "Id" in linha):
                continue
            partes = re.split(r"\s{2,}", linha.strip())
            if len(partes) >= 3:
                nome = partes[0]
                id_ = partes[1]
                versao = partes[2] if len(partes) > 2 else ""
                disponivel = partes[3] if len(partes) > 3 else ""
                fonte = partes[4] if len(partes) > 4 else ""
                classificacao = self.classificar_pacote(id_, nome)

                caminho = self._buscar_caminho_por_nome(id_, nome)

                item_dict = {
                    "nome": nome, "id": id_, "versao": versao,
                    "caminho": caminho,
                    "available": disponivel, "fonte": fonte, "classificacao": classificacao
                }
                if so_desatualizados and not disponivel:
                    continue
                if todos:
                    self.todos_os_itens.append(item_dict)

        self._inserir_e_aplicar_filtro()

    def mostrar_erro(self, mensagem):
        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)
        self.btn_salvar_html.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao listar pacotes.")
        messagebox.showerror("Erro", mensagem)

    # =====================================================================
    #  DESINSTALAR
    # =====================================================================
    def desinstalar(self):
        package_id = self.entry_id.get().strip()
        if not package_id:
            messagebox.showwarning("Atenção", "Digite ou selecione o ID do programa.")
            return

        classificacao = self.classificar_pacote(package_id)

        if classificacao == "critico":
            aviso = messagebox.askyesno("⚠️ Pacote Crítico", f"Este pacote é CRÍTICO para o sistema.\n\nID: {package_id}\n\nRemovê-lo pode quebrar o Windows. Tem certeza?")
            if not aviso: return
        elif classificacao == "driver":
            aviso = messagebox.askyesno("🧿 Driver de Hardware", f"Este pacote é um DRIVER.\n\nID: {package_id}\n\nA remoção pode parar o dispositivo. Continuar?")
            if not aviso: return
        elif classificacao == "xbox":
            aviso = messagebox.askyesno("🎮 Pacote Xbox", f"Este pacote é do Xbox.\n\nID: {package_id}\n\nPode afetar Game Bar/Gaming Services. Continuar?")
            if not aviso: return
        elif classificacao == "custom_branco":
            aviso = messagebox.askyesno("⬜ Pacote Custom", f"Pacote da sua lista personalizada.\n\nID: {package_id}\n\nContinuar?")
            if not aviso: return
        elif classificacao == "nao_seguro":
            aviso = messagebox.askyesno("❌ Não Recomendado", f"Componente de sistema.\n\nID: {package_id}\n\nTem certeza?")
            if not aviso: return
        else:
            confirmar = messagebox.askyesno("✔️ Confirmar", f"Pacote SEGURO.\n\nID: {package_id}\n\nContinuar?")
            if not confirmar: return

        self.btn_uninstall.config(state=tk.DISABLED)
        self.atualizar_status(f"Desinstalando '{package_id}'...")

        def tarefa():
            try:
                resultado = subprocess.run(
                    ["winget", "uninstall", "--id", package_id, "--silent"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                saida = (resultado.stdout or "") + "\n" + (resultado.stderr or "")
                self.root.after(0, lambda: self.resultado_desinstalacao(package_id, saida, resultado.returncode))
            except Exception as e:
                self.root.after(0, lambda: self.erro_desinstalar(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def resultado_desinstalacao(self, package_id, saida, codigo):
        self.btn_uninstall.config(state=tk.NORMAL)
        self.entry_id.delete(0, tk.END)
        if codigo == 0:
            self.atualizar_status(f"'{package_id}' desinstalado com sucesso.")
            messagebox.showinfo("Sucesso", f"Pacote desinstalado:\n{package_id}")
            self.listar_pacotes()
        else:
            self.atualizar_status(f"Falha ao desinstalar '{package_id}'.")
            messagebox.showerror("Erro", f"Não foi possível desinstalar.\n\n{saida[:700]}")

    def erro_desinstalar(self, mensagem):
        self.btn_uninstall.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao desinstalar.")
        messagebox.showerror("Erro", mensagem)

    # =====================================================================
    #  ATUALIZAR
    # =====================================================================
    def atualizar(self):
        package_id = self.entry_id.get().strip()
        if not package_id:
            messagebox.showwarning("Atenção", "Digite ou selecione o ID do programa para atualizar.")
            return
        confirmar = messagebox.askyesno("🔄 Confirmar atualização", f"Deseja atualizar?\n\nID: {package_id}")
        if not confirmar:
            return

        self.btn_upgrade.config(state=tk.DISABLED)
        self.atualizar_status(f"Atualizando '{package_id}'...")

        def tarefa():
            try:
                resultado = subprocess.run(
                    ["winget", "upgrade", "--id", package_id, "--exact", "--include-unknown",
                     "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                saida = (resultado.stdout or "") + "\n" + (resultado.stderr or "")
                self.root.after(0, lambda: self.resultado_atualizacao(package_id, saida, resultado.returncode))
            except Exception as e:
                self.root.after(0, lambda: self.erro_atualizar(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def resultado_atualizacao(self, package_id, saida, codigo):
        self.btn_upgrade.config(state=tk.NORMAL)
        if codigo == 0:
            self.atualizar_status(f"'{package_id}' atualizado com sucesso.")
            messagebox.showinfo("Sucesso", f"Pacote atualizado\n\n{package_id}")
            self.listar_pacotes()
        else:
            self.atualizar_status(f"Falha ao atualizar '{package_id}'.")
            messagebox.showwarning("Resultado", f"Saída do winget upgrade:\n\n{saida[:700]}")

    def erro_atualizar(self, mensagem):
        self.btn_upgrade.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao atualizar.")
        messagebox.showerror("Erro", mensagem)

    # =====================================================================
    #  INSTALAR PACOTE
    # =====================================================================
    def instalar(self):
        package = self.entry_install.get().strip()
        if not package:
            messagebox.showwarning("Atenção", "Digite o ID ou nome do pacote para instalar.")
            return

        confirmar = messagebox.askyesno(
            "📦 Confirmar instalação",
            f"Deseja instalar o pacote?\n\n{package}\n\n"
            f"O winget tentará baixar e instalar a versão mais recente do repositório."
        )
        if not confirmar:
            return

        self.btn_install.config(state=tk.DISABLED)
        self.atualizar_status(f"Instalando '{package}'...")

        def tarefa():
            try:
                resultado = subprocess.run(
                    [
                        "winget", "install",
                        "--id", package,
                        "--exact",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                        "--disable-interactivity"
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                saida = (resultado.stdout or "") + "\n" + (resultado.stderr or "")
                self.root.after(0, lambda: self.resultado_instalacao(package, saida, resultado.returncode))
            except Exception as e:
                self.root.after(0, lambda: self.erro_instalar(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def resultado_instalacao(self, package, saida, codigo):
        self.btn_install.config(state=tk.NORMAL)

        if codigo != 0 and "No package found" in saida:
            self.atualizar_status(f"Tentando busca aproximada para '{package}'...")
            def tarefa_fallback():
                try:
                    resultado = subprocess.run(
                        [
                            "winget", "install",
                            package,
                            "--accept-package-agreements",
                            "--accept-source-agreements",
                            "--disable-interactivity"
                        ],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    saida2 = (resultado.stdout or "") + "\n" + (resultado.stderr or "")
                    self.root.after(0, lambda: self._final_instalacao(package, saida2, resultado.returncode))
                except Exception as e:
                    self.root.after(0, lambda: self.erro_instalar(str(e)))
            threading.Thread(target=tarefa_fallback, daemon=True).start()
            return

        self._final_instalacao(package, saida, codigo)

    def _final_instalacao(self, package, saida, codigo):
        self.btn_install.config(state=tk.NORMAL)

        if codigo == 0:
            self.atualizar_status(f"'{package}' instalado com sucesso!")
            messagebox.showinfo("Sucesso", f"Pacote instalado:\n{package}")
            self.entry_install.delete(0, tk.END)
            self.listar_pacotes()
        else:
            self.atualizar_status(f"Falha ao instalar '{package}'.")
            messagebox.showerror("Erro", f"Não foi possível instalar.\n\n{saida[:700]}")

    def erro_instalar(self, mensagem):
        self.btn_install.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao instalar.")
        messagebox.showerror("Erro", mensagem)

    # =====================================================================
    #  SALVAR HTML — SEM A COLUNA CAMINHO (TABELA COMPACTA)
    # =====================================================================
    def salvar_html(self):
        if not self.tree.get_children():
            if not self.todos_os_itens:
                messagebox.showwarning("Atenção", "Nenhum pacote carregado. Clique em LISTAR PACOTES primeiro.")
            else:
                messagebox.showwarning("Atenção", "Nenhum pacote visível com os filtros atuais. Marque pelo menos uma categoria.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
            title="Salvar relatório HTML",
            initialfile=f"winget_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        if not arquivo:
            return

        self.atualizar_status("Gerando relatório HTML (sem caminhos)...")
        self.btn_salvar_html.config(state=tk.DISABLED)

        def gerar():
            try:
                contagem = {"seguro": 0, "nao_seguro": 0, "critico": 0, "driver": 0, "xbox": 0, "custom_branco": 0}
                linhas_tabela = ""

                for child in self.tree.get_children():
                    values = self.tree.item(child, "values")
                    tags = self.tree.item(child, "tags")
                    if not values or len(values) < 6:
                        continue

                    c = tags[0] if tags else "nao_seguro"
                    contagem[c] = contagem.get(c, 0) + 1

                    badge_map = {
                        "seguro": ('<span class="badge badge-safe">✔️ Seguro</span>', "row-safe"),
                        "critico": ('<span class="badge badge-critical">⚠️ Crítico</span>', "row-critical"),
                        "driver": ('<span class="badge badge-driver">🧿 Driver</span>', "row-driver"),
                        "xbox": ('<span class="badge badge-xbox">🎮 Xbox</span>', "row-xbox"),
                        "custom_branco": ('<span class="badge badge-custom">⬜ Custom</span>', "row-custom"),
                    }
                    badge, row_class = badge_map.get(c, ('<span class="badge badge-unsafe">❌ Não Recomendado</span>', "row-unsafe"))

                    nome = values[1] if len(values) > 1 and values[1] else "-"
                    pkg_id = values[2] if len(values) > 2 and values[2] else "-"
                    versao = values[3] if len(values) > 3 and values[3] else "-"
                    disponivel = values[4] if len(values) > 4 and values[4] else "-"
                    fonte = values[5] if len(values) > 5 and values[5] else "-"

                    linhas_tabela += f"""\
                <tr class="{row_class}">
                    <td>{badge}</td>
                    <td class="td-name">{nome}</td>
                    <td class="td-id">{pkg_id}</td>
                    <td>{versao}</td>
                    <td>{disponivel}</td>
                    <td>{fonte}</td>
                </tr>"""

                total = sum(contagem.values())
                data_geracao = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

                total_desat = 0
                for child in self.tree.get_children():
                    v = self.tree.item(child, "values")
                    if len(v) > 5 and v[4]:
                        total_desat += 1

                html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Winget Report — Monitor de Pacotes</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100vh; overflow: hidden; }}
        body {{
            background: #0a0e0a;
            color: #c0c0c0;
            font-family: 'Segoe UI', 'Consolas', monospace;
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        h1 {{
            color: #00ff41;
            font-weight: 300;
            font-size: 28px;               /* ← AUMENTE AQUI (ex: 32px) */
            letter-spacing: 1px;
            border-bottom: 1px solid #00aa33;
            padding-bottom: 12px;
            margin-bottom: 20px;
            flex-shrink: 0;
        }}
        h1 small {{ color: #00aa33; font-size: 14px; font-weight: 400; margin-left: 20px; }}
        .stats-container {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 25px; flex-shrink: 0; }}
        .stat-card {{
            background: #111811; border: 1px solid #1a2a1a; border-radius: 8px;
            padding: 14px 12px;            /* ← AUMENTE (ex: 18px 28px) */
            min-width: 130px; text-align: center;
        }}
        .stat-card .num {{ font-size: 28px; font-weight: 700; display: block; }}  /* ← AUMENTE (ex: 32px) */
        .stat-card .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; opacity: 0.8; }}
        .stat-card.total .num {{ color: #00ff41; }}
        .stat-card.safe .num {{ color: #00ff41; }}
        .stat-card.xbox .num {{ color: #9b59b6; }}
        .stat-card.custom .num {{ color: #ffffff; }}
        .stat-card.unsafe .num {{ color: #ff3333; }}
        .stat-card.driver .num {{ color: #3399ff; }}
        .stat-card.critical .num {{ color: #ff9f1c; }}
        .stat-card.outdated .num {{ color: #ff9f1c; }}
        .legend {{ color: #00aa33; font-size: 12px; margin-bottom: 18px; padding: 8px 14px; background: #0d120d; border-left: 3px solid #00aa33; border-radius: 4px; flex-shrink: 0; }}

        /* ===== TABELA ===== */
        .table-wrap {{ flex: 1; overflow-y: auto; border: 1px solid #1a2a1a; border-radius: 8px; min-height: 0; }}
        table {{
            width: 100%; border-collapse: collapse;
            font-size: 11px;                /* ← AUMENTE → ex: 13px ou 14px */
        }}
        thead {{ background: #0d120d; position: sticky; top: 0; z-index: 2; }}
        th {{
            color: #ff9f1c; font-weight: 600; text-align: left;
            padding: 5px 8px;              /* ← AUMENTE (ex: 10px 12px) */
            border-bottom: 2px solid #1a3a1a;
            text-transform: uppercase;
            font-size: 9px;                /* ← AUMENTE (ex: 11px) */
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 2px 7px;              /* ←↑ AUMENTE AQUI — principal! ex: 8px 12px */
            border-bottom: 1px solid #141c14;
            vertical-align: middle;
        }}
        tr:last-child td {{ border-bottom: none; }}
        .row-safe td   {{ color: #00ff41; }}
        .row-unsafe td {{ color: #ff3333; }}
        .row-critical td {{ color: #ff9f1c; }}
        .row-driver td {{ color: #3399ff; }}
        .row-xbox td   {{ color: #9b59b6; }}
        .row-custom td {{ color: #ffffff; }}
        .badge {{
            display: inline-block;
            font-size: 12px;                /* ← AUMENTE (ex: 10px) */
            padding: 1px 2px;              /* ← AUMENTE (ex: 4px 10px) */
            border-radius: 10px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .badge-safe    {{ background: #003300; color: #00ff41; border: 1px solid #00aa33; }}
        .badge-unsafe  {{ background: #330000; color: #ff3333; border: 1px solid #aa0000; }}
        .badge-critical {{ background: #332200; color: #ff9f1c; border: 1px solid #aa6600; }}
        .badge-driver  {{ background: #002233; color: #3399ff; border: 1px solid #0066aa; }}
        .badge-xbox    {{ background: #1a0033; color: #9b59b6; border: 1px solid #6600aa; }}
        .badge-custom  {{ background: #1a1a1a; color: #ffffff; border: 1px solid #555555; }}
        .td-name {{ font-weight: 600; }}
        .td-id {{
            font-family: 'Consolas', monospace;
            font-size: 10px;               /* ← AUMENTE (ex: 12px) */
            opacity: 0.85;
        }}
        .footer {{
            text-align: center; flex-shrink: 0; margin-top: 6px;
            font-size: 14px;               /* ← AUMENTE (ex: 12px) */
            color: #3a6a3a; border-top: 1px solid #1a2a1a; padding-top: 6px;
        }}
        @media (max-width: 900px) {{ body {{ padding: 15px; }} .stat-card {{ min-width: 100px; padding: 10px 14px; }} .stat-card .num {{ font-size: 22px; }} }}
    </style>
</head>
<body>
    <h1>📦 Winget RESULTADOS <small>Gerado em {data_geracao}</small></h1>
    <div class="stats-container">
        <div class="stat-card total"><span class="num">{total}</span><span class="label">Total (filtrado)</span></div>
        <div class="stat-card safe"><span class="num">{contagem['seguro']}</span><span class="label">✔️ Seguros</span></div>
        <div class="stat-card xbox"><span class="num">{contagem['xbox']}</span><span class="label">🎮 Xbox</span></div>
        <div class="stat-card custom"><span class="num">{contagem['custom_branco']}</span><span class="label">⬜ Custom</span></div>
        <div class="stat-card unsafe"><span class="num">{contagem['nao_seguro']}</span><span class="label">❌ Não Recomendados</span></div>
        <div class="stat-card driver"><span class="num">{contagem['driver']}</span><span class="label">🧿 Drivers/HW</span></div>
        <div class="stat-card critical"><span class="num">{contagem['critico']}</span><span class="label">⚠️ Críticos</span></div>
        <div class="stat-card outdated"><span class="num">{total_desat}</span><span class="label">🔄 Desatualizados</span></div>
    </div>
    <div class="legend">✔️ Seguro remover &nbsp;&nbsp;|&nbsp;&nbsp; 🎮 Xbox &nbsp;&nbsp;|&nbsp;&nbsp; ⬜ Custom (branco) &nbsp;&nbsp;|&nbsp;&nbsp; ❌ Não recomendado remover &nbsp;&nbsp;|&nbsp;&nbsp; 🧿 Driver / Hardware (cuidado) &nbsp;&nbsp;|&nbsp;&nbsp; ⚠️ Crítico (não remover)</div>
    <div class="table-wrap">
        <table><thead><tr><th>Classificação</th><th>Programa</th><th>ID</th><th>Versão</th><th>Disponível</th><th>Fonte</th></tr></thead>
        <tbody>{linhas_tabela}</tbody></table>
    </div>
    <div class="footer">Gerado por Winget Uninstall &amp; Install Tool — {total} pacotes listados (filtro ativo) • {data_geracao}</div>
</body>
</html>"""

                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write(html)

                self.ultimo_html = arquivo
                self.root.after(0, lambda: self.html_salvo(arquivo))

            except Exception as e:
                self.root.after(0, lambda: self.erro_html(str(e)))

        threading.Thread(target=gerar, daemon=True).start()

    def html_salvo(self, caminho):
        self.btn_salvar_html.config(state=tk.NORMAL)
        nome_arquivo = os.path.basename(caminho)
        self.atualizar_status(f"✅ HTML salvo: {nome_arquivo}")
        resposta = messagebox.askyesno("HTML Salvo com Sucesso", f"Relatório salvo em\n\n{caminho}\n\nDeseja abrir o arquivo no navegador?")
        if resposta:
            try:
                os.startfile(caminho)
            except Exception:
                pass

    def erro_html(self, mensagem):
        self.btn_salvar_html.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao gerar HTML.")
        messagebox.showerror("Erro", f"Não foi possível gerar o HTML.\n{mensagem}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WingetGUI(root)
    root.mainloop()
