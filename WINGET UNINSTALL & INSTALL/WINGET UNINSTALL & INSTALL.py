import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json
import re

# ===== LISTA DE PACOTES SEGUROS PARA REMOVER (BLOATWARE COMUM) =====
SEGUROS_PARA_REMOVER = {
    # === Microsoft Edge / WebView ===
    "Microsoft.Edge", "Microsoft.Edge.Stable", "Microsoft.Edge.Update",
    "Microsoft.EdgeWebView2Runtime",

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
    "Microsoft.VCLibs.140.00", "Microsoft.VCLibs.140.00.UWPDesktop",

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
    # === Infraestrutura do Windows ===
    "Microsoft.DesktopAppInstaller",  # O próprio Winget!
    "Microsoft.PowerShell",
    "Microsoft.WindowsTerminal",
    "Microsoft.WindowsAppRuntime",
    "Microsoft.Services.Store",
    "Microsoft.StoreFoundation",

    # === Microsoft.NET.Native.Framework (CRÍTICO - apps UWP dependem) ===
    "Microsoft.NET.Native.Framework",
    "Microsoft.NET.Native.Runtime",

    # === Microsoft.Services.Store.Engagement ===
    "Microsoft.Services.Store.Engagement",

    # === Microsoft.UI (Framework de interface do Windows) ===
    "Microsoft.UI.Xaml",
    "Microsoft.UI",

    # === Microsoft.Winget.Source (FONTE DO REPOSITÓRIO DO WINGET!) ===
    "Microsoft.Winget.Source",

    # === Visual C++ Redistributables (CRÍTICOS - runtime essencial) ===
    "Microsoft.VCLibs.110.00.UWPDesktop",
    "Microsoft.VCLibs.120.00.UWPDesktop",
    "Microsoft.VCLibs.140.00.UWPDesktop",
    "Microsoft.VC++",
    "Microsoft.VisualCPlusPlus",
    "Microsoft.VisualCpp",
    "Microsoft Visual C++",

    # === GUIDs específicos de Visual C++ ===
    "{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}",  # VC++ 2008 Redist x86
    "Redistributable", "Redistributable",
    "14.51.36231.0", "14.42.34438.0",
}

# ===== PACOTES XBOX (CATEGORIA ROXA) =====
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

# ===== PACOTES PERSONALIZADOS — CATEGORIA BRANCA =====
# Adicione aqui qualquer pacote que você queira ver na cor BRANCA.
# Eles serão classificados com prioridade logo após os críticos.
PACOTES_CUSTOM_BRANCO = {    
    "Microsoft.HEIFImageExtension",
    "Microsoft.WebpImageExtension",
    "Microsoft.WebMediaExtensions",
    "Microsoft.VP9VideoExtensions",    
    # Adicione mais ID aqui conforme desejar
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

    # Microsoft update
    "7B1FCD52-8F6B-4F12-A143-361EA39F5E7C",
    "0746492E-47B6-4251-940C-44462DFD74BB",
    
}

# ===== DRIVERS E COMPONENTES DE HARDWARE (COR AZUL) =====
DRIVERS_HARDWARE_PREFIXOS = {
    # --- Drivers de Rede (Wi-Fi, Ethernet, Bluetooth) ---
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

    # --- Drivers de Vídeo / GPU ---
    "NVIDIA.NVIDIA", "NVIDIA.Graphics", "NVIDIA.Display",
    "NVIDIA.PhysX", "NVIDIA.GeForce", "NVIDIA.Driver",
    "AMD.AMD", "AMD.Radeon", "AMD.Adrenalin", "AMD.Graphics",
    "AMD.Chipset", "AMD.Ryzen", "AMD.RadeonSoftware",
    "AMD.Catalyst", "AMD.CatalystInstallManager",
    "Intel.Graphics", "Intel.Display", "Intel.GPU",
    "Intel.Arc", "Intel.Iris",

    # --- Drivers de Áudio ---
    "Realtek.Audio", "Realtek.HDA", "Realtek.HighDefinitionAudio",
    "VIA.Audio", "VIA.VIA",
    "Creative.Creative", "Creative.Sound", "Creative.Audio",
    "Dolby.Dolby", "Dolby.Audio",

    # --- Drivers de Chipset / Placa-mãe ---
    "Intel.Chipset", "Intel.INF", "Intel.ManagementEngine",
    "Intel.ME", "Intel.SerialIO", "Intel.SSD",
    "AMD.Chipset", "AMD.GPIO", "AMD.SMBus",
    "ASMedia.ASMedia", "ASMedia.USB",
    "NVMExpress", "NVMe",

    # --- Drivers USB / Thunderbolt / Dock ---
    "Intel.Thunderbolt", "Intel.USB",
    "AMD.USB",
    "DisplayLink.DisplayLink", "DisplayLink.Graphics",
    "Dell.Dock", "Dell.Thunderbolt", "Dell.USB",
    "Lenovo.Dock", "Lenovo.USB", "Lenovo.Thunderbolt",
    "HP.Dock", "HP.USB", "HP.Thunderbolt",

    # --- Drivers de Armazenamento / Disco ---
    "Intel.RST", "Intel.Storage", "Intel.RapidStorage",
    "AMD.Storage", "AMD.Raid",
    "Samsung.SSD", "Samsung.NVMe", "Samsung.Magician",
    "WesternDigital.WD", "WesternDigital.SSD",
    "Crucial.Storage", "Micron.Storage",
    "SKHynix.Storage", "SKHynix.SSD",

    # --- Drivers de Câmera / Webcam ---
    "Microsoft.Camera", "Microsoft.Webcam",
    "Realtek.Camera", "Intel.Camera",

    # --- Drivers de Touchpad / Teclado ---
    "Synaptics.Synaptics", "Synaptics.TouchPad", "Synaptics.Pointing",
    "ELAN.ELAN", "ELAN.Touchpad", "ELAN.Input",
    "Alps.Alps", "Alps.Touchpad",
    "Wacom.Wacom", "Wacom.Tablet",

    # --- Drivers de Monitor ---
    "Dell.Display", "Dell.Monitor",
    "LG.Display", "LG.Monitor",
    "Samsung.Display", "Samsung.Monitor",

    # --- Drivers de Modem / Celular ---
    "Qualcomm.Modem", "Qualcomm.Mobile",
    "Samsung.Modem", "Samsung.Mobile",
    "Mediatek.Modem", "Mediatek.Mobile",
    "Apple.Modem", "Apple.Mobile", "Apple.iPhone",

    # --- Drivers de Impressora / Scanner ---
    "HP.HP", "HP.Print", "HP.Scan",
    "Canon.Canon", "Canon.Print", "Canon.Scan",
    "Epson.Epson", "Epson.Print", "Epson.Scan",
    "Brother.Brother", "Brother.Print",
    "Xerox.Xerox", "Xerox.Print",

    # --- Drivers de controladoras / barramento ---
    "Standard.NVMe", "Standard.SATA", "Standard.ATA",
    "Microsoft.HyperV", "Microsoft.Virtual",
    "Oracle.VirtualBox", "VMware.VMware",
}

# Palavras-chave que indicam driver no nome ou ID
PALAVRAS_DRIVER = [
    "driver", "drivers", "chipset", "bluetooth", "wireless", "wifi",
    "ethernet", "network", "lan", "modem", "cellular", "mobile",
    "graphics", "display", "audio", "sound", "hda", "nvme", "ssd",
    "storage", "raid", "touchpad", "keyboard", "webcam", "camera",
    "usb", "thunderbolt", "dock", "sensors",
    "catalyst", "radeon", "geforce", "adrenalin",
]

# GUIDs conhecidos de Visual C++ Redistributable (ARP)
GUIDS_VC_REDIST = {
    "{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}",  # VC++ 2008 Redist x86
    "{9A25302D-30C0-39D9-BD6F-21E6EC160475}",  # VC++ 2008 Redist x64
    "{1F1C2DFC-2D24-3E06-BCB8-725134ADF989}",  # VC++ 2005 Redist
    "{7299052B-02A4-4627-81F2-1818DA5D550D}",  # VC++ 2005 SP1 Redist x86
    "{0F8FB34E-675E-42ED-850B-29D98C2ECE08}",  # VC++ 2005 SP1 Redist ia64
    "{ad8a2fa1-06e7-4b0d-927d-6e54b3d31028}",  # VC++ 2005 SP1 MFC Security Update
    
}


class WingetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WINGET UNINSTALL & INSTALL")
        self.root.geometry("1250x720")
        self.root.state("zoomed")
        self.root.minsize(950, 550)
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

        # ===== Frame superior =====
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill=tk.X)

        title = ttk.Label(top_frame, text="█ WINGET UNINSTALL & INSTALL █ ", font=("Consolas", 16, "bold"))
        title.pack(side=tk.LEFT)

        # --- Botão LISTAR PACOTES ---
        self.btn_list = ttk.Button(top_frame, text="[ LISTAR PACOTES ]", command=self.listar_pacotes)
        self.btn_list.pack(side=tk.LEFT, padx=5)

        # --- Botão MOSTRAR DESATUALIZADOS ---
        self.btn_desatualizados = ttk.Button(
            top_frame,
            text="[ MOSTRAR DESATUALIZADOS ]",
            command=self.listar_desatualizados
        )
        self.btn_desatualizados.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.LabelFrame(root, text=" Pacotes Instalados ", padding=5)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("seguro", "name", "id", "version", "available", "source")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        style = ttk.Style()
        style.configure("Treeview.Heading", foreground="#ff9f1c",
            background="#1e1e1e",
            font=("Segoe UI", 10, "bold")
            )

        self.tree.heading("seguro", text="SEGURO", anchor=tk.W)
        self.tree.heading("name", text="PROGRAMA", anchor=tk.W)
        self.tree.heading("id", text="ID", anchor=tk.W)
        self.tree.heading("version", text="VERSÃO", anchor=tk.W)
        self.tree.heading("available", text="DISPONÍVEL", anchor=tk.W)
        self.tree.heading("source", text="FONTE", anchor=tk.W)

        self.tree.column("seguro", width=60, anchor=tk.W, minwidth=50)
        self.tree.column("name", width=720, anchor=tk.W)
        self.tree.column("id", width=560, anchor=tk.W)
        self.tree.column("version", width=250, anchor=tk.W)
        self.tree.column("available", width=200, anchor=tk.W)
        self.tree.column("source", width=100, anchor=tk.W)

        # Tags de cores
        self.tree.tag_configure("seguro", foreground="#00ff41")
        self.tree.tag_configure("nao_seguro", foreground="#ff3333")
        self.tree.tag_configure("critico", foreground="#ff9f1c")
        self.tree.tag_configure("driver", foreground="#3399ff")
        self.tree.tag_configure("xbox", foreground="#9b59b6")   # 🔮 ROXO
        self.tree.tag_configure("custom_branco", foreground="#ffffff")  # ⬜ BRANCO

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # ===== Frame de desinstalação e atualização =====
        action_frame = ttk.LabelFrame(root, text=" Operações por ID ", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(action_frame, text="ID do programa:").grid(row=0, column=0, sticky=tk.W, padx=5)

        self.entry_id = ttk.Entry(action_frame, width=50, font=("Consolas", 11))
        self.entry_id.grid(row=0, column=1, padx=5, sticky=tk.EW)

        self.btn_uninstall = ttk.Button(
            action_frame,
            text="[ DESINSTALAR ]",
            command=self.desinstalar
        )
        self.btn_uninstall.grid(row=0, column=2, padx=5)

        self.btn_upgrade = ttk.Button(
            action_frame,
            text="[ ATUALIZAR ]",
            command=self.atualizar
        )
        self.btn_upgrade.grid(row=0, column=3, padx=5)

        action_frame.columnconfigure(1, weight=1)

        # ===== Status bar =====
        self.status = ttk.Label(root, text="> Sistema pronto. Aguardando comando...", style="Status.TLabel", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM, ipady=4)

        # ===== Legenda =====
        legenda = ttk.Label(
            root,
            text=(
                "✔️ Seguro remover  |  🎮 Xbox  |  ⬜ Custom (branco)  |  "
                "❌ Não recomendado  |  🔵 Driver/HW (cuidado)  |  "
                "⚠️ Crítico (não remover)  |  Clique = copia ID  | UM clique = preenche"
            ),
            foreground="#00aa33",
            font=("Consolas", 9)
        )
        legenda.pack(pady=4)

        # Armazena a lista completa de itens (para uso no filtro)
        self.todos_os_itens = []

    def classificar_pacote(self, package_id, package_name=""):
        """Classifica o pacote: seguro, nao_seguro, critico, driver, xbox, custom_branco."""
        if not package_id:
            return "nao_seguro"

        id_lower = package_id.lower()
        name_lower = package_name.lower()

        # 1) Verifica GUIDs de VC++ Redist (críticos)
        for guid in GUIDS_VC_REDIST:
            if guid.lower() in id_lower or guid.lower() in package_id:
                return "critico"

        # 2) Verifica se é crítico
        for critico in CRITICOS:
            if package_id.startswith(critico) or critico.lower() in id_lower:
                return "critico"

        # 3) VERIFICA CATEGORIA PERSONALIZADA BRANCA (logo após críticos)
        for custom in PACOTES_CUSTOM_BRANCO:
            if package_id.startswith(custom) or custom.lower() in id_lower:
                return "custom_branco"

        # 4) Verifica Xbox
        for xbox_pkg in XBOX_PACKAGES:
            if package_id.startswith(xbox_pkg) or xbox_pkg.lower() in id_lower:
                return "xbox"

        # 5) Verifica drivers por prefixo (lista azul)
        for prefixo in DRIVERS_HARDWARE_PREFIXOS:
            if package_id.startswith(prefixo) or prefixo.lower() in id_lower:
                return "driver"

        # 6) Verifica drivers por palavra-chave no nome ou ID
        for palavra in PALAVRAS_DRIVER:
            if palavra in id_lower or palavra in name_lower:
                return "driver"

        # 7) Verifica se é da lista de seguros
        for seguro in SEGUROS_PARA_REMOVER:
            if package_id.startswith(seguro) or seguro.lower() in id_lower:
                return "seguro"

        # 8) Componentes Microsoft não listados = não seguro
        if package_id.startswith("Microsoft."):
            return "nao_seguro"

        # 9) GUIDs de ARP não identificados = não seguro (cuidado)
        if package_id.startswith("{") and package_id.endswith("}"):
            return "nao_seguro"

        # 10) MSIX com GUID ou hash = verifica nome
        if "MSIX" in id_lower or "8wekyb3d8bbwe" in id_lower:
            for seguro in SEGUROS_PARA_REMOVER:
                nome_seguro = seguro.lower().split(".")[-1] if "." in seguro else seguro.lower()
                if nome_seguro in id_lower or nome_seguro in name_lower:
                    return "seguro"
            return "nao_seguro"

        # 11) Terceiros = seguro
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

    def listar_pacotes(self):
        """Lista TODOS os pacotes instalados."""
        self.btn_list.config(state=tk.DISABLED)
        self.btn_desatualizados.config(state=tk.DISABLED)
        self.atualizar_status("Executando winget list... aguarde...")

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.todos_os_itens.clear()

        def tarefa():
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

    def listar_desatualizados(self):
        """
        Lista APENAS os pacotes que têm atualização disponível
        (coluna 'available' não vazia) e que são seguros/drivers/etc.
        """
        if not self.todos_os_itens:
            self.btn_list.config(state=tk.DISABLED)
            self.btn_desatualizados.config(state=tk.DISABLED)
            self.atualizar_status("Carregando lista completa primeiro...")

            def tarefa_dupla():
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
                            self.root.after(0, lambda: self.preencher_tree_json(pacotes, todos=True, so_desatualizados=True))
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
                    self.root.after(0, lambda: self.preencher_tree_texto(resultado.stdout, todos=True, so_desatualizados=True))

                except FileNotFoundError:
                    self.root.after(0, lambda: self.mostrar_erro("Winget não encontrado."))
                except Exception as e:
                    self.root.after(0, lambda: self.mostrar_erro(str(e)))

            threading.Thread(target=tarefa_dupla, daemon=True).start()
            return

        self.atualizar_status("Filtrando pacotes desatualizados...")
        for item in self.tree.get_children():
            self.tree.delete(item)

        desatualizados = [
            item for item in self.todos_os_itens
            if item["available"]
        ]

        total_desat = len(desatualizados)
        contagem = {"seguro": 0, "nao_seguro": 0, "critico": 0, "driver": 0, "xbox": 0, "custom_branco": 0}

        for pkg in desatualizados:
            classificacao = pkg["classificacao"]
            contagem[classificacao] = contagem.get(classificacao, 0) + 1

            if classificacao == "seguro":
                icone = "✔️"
                tag = "seguro"
            elif classificacao == "critico":
                icone = "⚠️"
                tag = "critico"
            elif classificacao == "driver":
                icone = "🔵"
                tag = "driver"
            elif classificacao == "xbox":
                icone = "🎮"
                tag = "xbox"
            elif classificacao == "custom_branco":
                icone = "⬜"
                tag = "custom_branco"
            else:
                icone = "❌"
                tag = "nao_seguro"

            self.tree.insert(
                "", tk.END,
                values=(icone, pkg["nome"], pkg["id"], pkg["versao"], pkg["available"], pkg["fonte"]),
                tags=(tag,)
            )

        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)
        self.atualizar_status(
            f"📦 {total_desat} pacotes com atualização disponível. "
            f"✔️ {contagem['seguro']} S | 🎮 {contagem['xbox']} X | ⬜ {contagem['custom_branco']} C | "
            f"❌ {contagem['nao_seguro']} NR | 🔵 {contagem['driver']} D | ⚠️ {contagem['critico']} C"
        )

    def preencher_tree_json(self, pacotes, todos=False, so_desatualizados=False):
        """Preenche a TreeView a partir do JSON do winget."""
        contagem = {"seguro": 0, "nao_seguro": 0, "critico": 0, "driver": 0, "xbox": 0, "custom_branco": 0}

        if todos:
            self.todos_os_itens.clear()

        for pkg in pacotes:
            nome = pkg.get("Name", "")
            id_ = pkg.get("Id", "") or pkg.get("PackageIdentifier", "")
            versao = pkg.get("Version", "")
            disponivel = pkg.get("Available", "") or ""
            fonte = pkg.get("Source", "") or ""

            classificacao = self.classificar_pacote(id_, nome)

            item_dict = {
                "nome": nome,
                "id": id_,
                "versao": versao,
                "available": disponivel,
                "fonte": fonte,
                "classificacao": classificacao
            }

            if todos:
                self.todos_os_itens.append(item_dict)

            if so_desatualizados and not disponivel:
                continue

            if not todos and so_desatualizados and not disponivel:
                continue

            contagem[classificacao] = contagem.get(classificacao, 0) + 1

            if classificacao == "seguro":
                icone = "✔️"
                tag = "seguro"
            elif classificacao == "critico":
                icone = "⚠️"
                tag = "critico"
            elif classificacao == "driver":
                icone = "🔵"
                tag = "driver"
            elif classificacao == "xbox":
                icone = "🎮"
                tag = "xbox"
            elif classificacao == "custom_branco":
                icone = "⬜"
                tag = "custom_branco"
            else:
                icone = "❌"
                tag = "nao_seguro"

            self.tree.insert("", tk.END, values=(icone, nome, id_, versao, disponivel, fonte), tags=(tag,))

        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)

        total = sum(contagem.values())
        self.atualizar_status(
            f"Lista carregada — {total} pacotes. "
            f"✔️ {contagem['seguro']} S | 🎮 {contagem['xbox']} X | ⬜ {contagem['custom_branco']} C | "
            f"❌ {contagem['nao_seguro']} NR | 🔵 {contagem['driver']} D | ⚠️ {contagem['critico']} C"
        )

    def preencher_tree_texto(self, texto, todos=False, so_desatualizados=False):
        """Preenche a TreeView a partir da saída texto do winget."""
        linhas = texto.strip().splitlines()
        contagem = {"seguro": 0, "nao_seguro": 0, "critico": 0, "driver": 0, "xbox": 0, "custom_branco": 0}

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

                item_dict = {
                    "nome": nome,
                    "id": id_,
                    "versao": versao,
                    "available": disponivel,
                    "fonte": fonte,
                    "classificacao": classificacao
                }

                if todos:
                    self.todos_os_itens.append(item_dict)

                if so_desatualizados and not disponivel:
                    continue

                contagem[classificacao] = contagem.get(classificacao, 0) + 1

                if classificacao == "seguro":
                    icone = "✔️"
                    tag = "seguro"
                elif classificacao == "critico":
                    icone = "⚠️"
                    tag = "critico"
                elif classificacao == "driver":
                    icone = "🔵"
                    tag = "driver"
                elif classificacao == "xbox":
                    icone = "🎮"
                    tag = "xbox"
                elif classificacao == "custom_branco":
                    icone = "⬜"
                    tag = "custom_branco"
                else:
                    icone = "❌"
                    tag = "nao_seguro"

                self.tree.insert("", tk.END, values=(icone, nome, id_, versao, disponivel, fonte), tags=(tag,))

        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)
        total = sum(contagem.values())
        self.atualizar_status(
            f"Lista carregada — {total} pacotes. "
            f"✔️ {contagem['seguro']} S | 🎮 {contagem['xbox']} X | ⬜ {contagem['custom_branco']} C | "
            f"❌ {contagem['nao_seguro']} NR | 🔵 {contagem['driver']} D | ⚠️ {contagem['critico']} C"
        )

    def mostrar_erro(self, mensagem):
        self.btn_list.config(state=tk.NORMAL)
        self.btn_desatualizados.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao listar pacotes.")
        messagebox.showerror("Erro", mensagem)

    def desinstalar(self):
        package_id = self.entry_id.get().strip()
        if not package_id:
            messagebox.showwarning("Atenção", "Digite ou selecione o ID do programa.")
            return

        classificacao = self.classificar_pacote(package_id)

        if classificacao == "critico":
            aviso = messagebox.askyesno(
                "⚠️ Pacote Crítico",
                f"Este pacote é classificado como CRÍTICO para o sistema.\n\n"
                f"ID: {package_id}\n\n"
                f"Removê-lo pode quebrar o Windows ou apps importantes.\n"
                f"Tem certeza?"
            )
            if not aviso:
                return

        elif classificacao == "driver":
            aviso = messagebox.askyesno(
                "🔵 Driver de Hardware",
                f"Este pacote é um DRIVER ou componente de hardware.\n\n"
                f"ID: {package_id}\n\n"
                f"A remoção pode fazer o dispositivo parar de funcionar.\n"
                f"Deseja continuar?"
            )
            if not aviso:
                return

        elif classificacao == "xbox":
            aviso = messagebox.askyesno(
                "🎮 Pacote Xbox",
                f"Este pacote é um componente do Xbox.\n\n"
                f"ID: {package_id}\n\n"
                f"A remoção pode afetar Game Bar, Gaming Services ou outros recursos.\n"
                f"Deseja continuar?"
            )
            if not aviso:
                return

        elif classificacao == "custom_branco":
            aviso = messagebox.askyesno(
                "⬜ Pacote Custom (Branco)",
                f"Este pacote está na sua lista personalizada.\n\n"
                f"ID: {package_id}\n\n"
                f"Deseja continuar com a desinstalação?"
            )
            if not aviso:
                return

        elif classificacao == "nao_seguro":
            aviso = messagebox.askyesno(
                "❌ Pacote não recomendado",
                f"Este pacote pode ser um componente do sistema.\n\n"
                f"ID: {package_id}\n\n"
                f"Tem certeza que deseja desinstalar?"
            )
            if not aviso:
                return

        else:
            confirmar = messagebox.askyesno(
                "✔️ Confirmar desinstalação",
                f"Pacote classificado como SEGURO para remoção.\n\n"
                f"ID: {package_id}\n\n"
                f"Deseja continuar?"
            )
            if not confirmar:
                return

        self.btn_uninstall.config(state=tk.DISABLED)
        self.atualizar_status(f"Desinstalando '{package_id}'...")

        def tarefa():
            try:
                resultado = subprocess.run(
                    ["winget", "uninstall", "--id", package_id, "--silent"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
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
    #  ATUALIZAR (winget upgrade)
    # =====================================================================
    def atualizar(self):
        package_id = self.entry_id.get().strip()
        if not package_id:
            messagebox.showwarning("Atenção", "Digite ou selecione o ID do programa para atualizar.")
            return

        confirmar = messagebox.askyesno(
            "🔄 Confirmar atualização",
            f"Deseja atualizar o pacote?\n\nID: {package_id}\n\n"
            f"O winget tentará baixar e instalar a versão mais recente."
        )
        if not confirmar:
            return

        self.btn_upgrade.config(state=tk.DISABLED)
        self.atualizar_status(f"Atualizando '{package_id}'...")

        def tarefa():
            try:
                resultado = subprocess.run(
                    ["winget", "upgrade", "--id", package_id, "--silent", "--accept-package-agreements"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
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
            messagebox.showinfo("Sucesso", f"Pacote atualizado:\n{package_id}")
            self.listar_pacotes()
        else:
            self.atualizar_status(f"Falha ao atualizar '{package_id}'.")
            messagebox.showwarning(
                "Resultado",
                f"Saída do winget upgrade:\n\n{saida[:700]}"
            )

    def erro_atualizar(self, mensagem):
        self.btn_upgrade.config(state=tk.NORMAL)
        self.atualizar_status("Erro ao atualizar.")
        messagebox.showerror("Erro", mensagem)


if __name__ == "__main__":
    root = tk.Tk()
    app = WingetGUI(root)
    root.mainloop()
