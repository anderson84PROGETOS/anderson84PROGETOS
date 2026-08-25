import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import threading
import unicodedata
from html import escape
from datetime import datetime


# ============================================================
# WIFI SCANNER // NETSH TERMINAL EDITION
# Windows: netsh wlan show networks mode=bssid
# ============================================================

BG = "#030603"
PANEL = "#071007"
GREEN = "#00ff41"
GREEN_SOFT = "#00b82e"
GREEN_DIM = "#007a20"
CYAN = "#00e5ff"
YELLOW = "#ffff00"
ORANGE = "#ff9900"
RED = "#ff3333"
TEXT = "#b8ffb8"


class WifiScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📶 WiFi Scanner Windows")
        self.root.geometry("1250x720")
        self.root.state("zoomed")
        self.root.minsize(950, 560)
        self.root.configure(bg=BG)        

        self.networks = []
        self.filtered_networks = []
        self.scanning = False

        self.filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="[ SISTEMA PRONTO ]")
        self.total_var = tk.StringVar(value="REDES: 0")
        self.bssid_var = tk.StringVar(value="PONTOS: 0")
        self.open_var = tk.StringVar(value="ABERTAS: 0")
        self.strongest_var = tk.StringVar(value="MELHOR SINAL: --")
        self.details_var = tk.StringVar(
            value="> Selecione uma rede para visualizar os detalhes..."
        )

        self.setup_style()
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)        

    # --------------------------------------------------------
    # ESTILO
    # --------------------------------------------------------
    def setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG, foreground=GREEN, fieldbackground="#050a05", font=("Consolas", 10),)
        style.configure("TFrame", background=BG)
        style.configure("TLabelframe", background=BG, foreground=GREEN, bordercolor=GREEN_DIM,)
        style.configure("TLabelframe.Label", background=BG, foreground=GREEN, font=("Consolas", 10, "bold"),)
        style.configure("TLabel", background=BG, foreground=GREEN, font=("Consolas", 10),)
        style.configure("Title.TLabel", background=BG, foreground=GREEN, font=("Consolas", 20, "bold"),)
        style.configure("Status.TLabel", background=BG, foreground=CYAN, font=("Consolas", 9),)
        style.configure("Green.TButton", background="#14F147", foreground="black", bordercolor="#14F147", padding=(12, 7), font=("Arial", 10, "bold"),)
        style.map("Green.TButton", background=[("active", "#28ff58"), ("disabled", "#245a2d")],)
        style.configure("Pumpkin.TButton", background="#FF8C00", foreground="black", bordercolor="#FF8C00", padding=(12, 7), font=("Arial", 10, "bold"),)
        style.map("Pumpkin.TButton", background=[("active", "#ffad33")],)
        style.configure("Blue.TButton", background="#0BE8F8", foreground="black", bordercolor="#0BE8F8", padding=(12, 7), font=("Arial", 10, "bold"),)
        style.map("Blue.TButton", background=[("active", "#5ff3ff")],)
        style.configure("TEntry", fieldbackground="#050a05", foreground=GREEN, insertcolor=GREEN, bordercolor=GREEN_DIM, padding=6,)
        style.configure("Treeview", background="#050805", foreground=TEXT, fieldbackground="#050805", bordercolor=GREEN_DIM, rowheight=30, font=("Consolas", 9),)
        style.map("Treeview", background=[("selected", "#123d18")], foreground=[("selected", "#ffffff")],)
        style.configure("Treeview.Heading", background="#071a0a", foreground=GREEN, bordercolor=GREEN_DIM, relief="flat", font=("Consolas", 9, "bold"), padding=8,)
        style.map("Treeview.Heading", background=[("active", "#0d3015")], foreground=[("active", GREEN)],)
        style.configure("Vertical.TScrollbar", background="#0b220d", troughcolor=BG, bordercolor=BG, arrowcolor=GREEN,)
        style.configure("Horizontal.TScrollbar", background="#0b220d", troughcolor=BG, bordercolor=BG, arrowcolor=GREEN,)

    # --------------------------------------------------------
    # INTERFACE
    # --------------------------------------------------------
    def build_ui(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(header, text="📶 WIFI SCANNER WINDOWS", style="Title.TLabel",).pack(side="left")

        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel",).pack(side="right", padx=5)

        separator = tk.Frame(main, bg=GREEN_DIM, height=1)
        separator.pack(fill="x", pady=(0, 12))

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(0, 10))

        self.scan_button = ttk.Button(controls, text="[ INICIAR SCAN (NETSH) ]", command=self.scan, style="Green.TButton",)
        self.scan_button.pack(side="left", padx=(0, 8))

        ttk.Button(controls, text="[ EXPORTAR HTML ]",  command=self.export_html, style="Pumpkin.TButton",).pack(side="left", padx=(0, 8))

        ttk.Button(controls, text="[ COPIAR SELECIONADO ]", command=self.copy_selected, style="Blue.TButton",).pack(side="left", padx=(0, 14))

        ttk.Label(controls, text="FILTRAR BUSCA >",).pack(side="left")

        ttk.Entry(controls, textvariable=self.filter_var, width=30,).pack(side="left", padx=8)

        self.filter_var.trace_add("write", self.on_filter_changed)

        stats = tk.Frame(main, bg=PANEL, highlightbackground=GREEN_DIM, highlightthickness=1,)
        stats.pack(fill="x", pady=(0, 12))

        for var in (self.total_var, self.bssid_var, self.open_var, self.strongest_var,):
            tk.Label(stats, textvariable=var, bg=PANEL, fg=GREEN, font=("Consolas", 10, "bold"), padx=18, pady=9,).pack(side="left")

        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "rank",
            "ssid",
            "bssid",
            "signal",
            "radio",
            "channel",
            "auth",
            "crypto",
            "rates",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "rank": "#",
            "ssid": "SSID / REDE",
            "bssid": "BSSID",
            "signal": "SINAL",
            "radio": "RÁDIO",
            "channel": "CANAL",
            "auth": "AUTENTICAÇÃO",
            "crypto": "CRIPTOGRAFIA",
            "rates": "TAXAS Mbps",
        }

        widths = {
            "rank": 45,
            "ssid": 180,
            "bssid": 150,
            "signal": 85,
            "radio": 90,
            "channel": 65,
            "auth": 115,
            "crypto": 110,
            "rates": 300,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self.sort_by_column(c),)
            self.tree.column(col, width=widths[col], minwidth=45, anchor="center" if col != "ssid" else "w",)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview,)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview,)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set,)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        self.tree.tag_configure("signal_excellent", foreground=GREEN)
        self.tree.tag_configure("signal_good", foreground="#66ff66")
        self.tree.tag_configure("signal_medium", foreground=YELLOW)
        self.tree.tag_configure("signal_weak", foreground=ORANGE)
        self.tree.tag_configure("signal_bad", foreground=RED)
        self.tree.tag_configure("open_network", foreground=CYAN)

        # SSID OCULTO = ABÓBORA
        self.tree.tag_configure("hidden_ssid", foreground="#FF8C00")

        details = tk.LabelFrame(main, text="[ DETALHES DA REDE SELECIONADA ]", bg=BG, fg=GREEN, font=("Consolas", 10, "bold"), highlightbackground=GREEN_DIM, highlightthickness=1, padx=10, pady=8,)
        details.pack(fill="x", pady=(12, 0))
        tk.Label(details, textvariable=self.details_var, bg=BG, fg=TEXT, justify="left", anchor="w", font=("Consolas", 9),).pack(fill="x")

    # --------------------------------------------------------
    # EXECUTA NETSH
    # --------------------------------------------------------
    def scan(self):
        if self.scanning:
            return
        
        self.scanning = True
        self.scan_button.config(state="disabled")
        self.status_var.set("[ ESCANEANDO REDES... ]")
        self.root.update_idletasks()

        thread = threading.Thread(target=self._scan_worker, daemon=True,)
        thread.start()

    def _scan_worker(self):
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            result = subprocess.run(
                [
                    "netsh",
                    "wlan",
                    "show",
                    "networks",
                    "mode=bssid",
                ],
                capture_output=True,
                timeout=20,
                creationflags=creationflags,
            )

            raw = result.stdout

            text = None
            for encoding in ("utf-8", "cp850", "cp1252"):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                text = raw.decode("utf-8", errors="replace")

            if result.returncode != 0:
                error = result.stderr.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if not error:
                    error = result.stderr.decode(
                        "cp850",
                        errors="replace",
                    ).strip()

                raise RuntimeError(
                    error or "Falha ao executar o NETSH."
                )

            networks = self.parse_netsh(text)

            self.root.after(
                0,
                lambda data=networks: self.update_results(data),
            )

        except FileNotFoundError:
            self.root.after(
                0,
                lambda: self.show_scan_error(
                    "NETSH não encontrado. Execute este scanner no Windows."
                ),
            )

        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                lambda: self.show_scan_error(
                    "O comando NETSH demorou mais de 20 segundos para responder."
                ),
            )

        except Exception as exc:
            error_text = str(exc)
            self.root.after(
                0,
                lambda msg=error_text: self.show_scan_error(msg),
            )

    def show_scan_error(self, message):
        self.scanning = False
        self.scan_button.config(state="normal")
        self.status_var.set("[ ERRO ]")
        messagebox.showerror("ERRO DO SCANNER", message)

    # --------------------------------------------------------
    # UTILITÁRIOS
    # --------------------------------------------------------
    @staticmethod
    def normalize(text):
        text = str(text or "")
        text = unicodedata.normalize("NFKD", text)
        return "".join(
            c for c in text
            if not unicodedata.combining(c)
        ).lower()

    @staticmethod
    def signal_number(signal):
        match = re.search(r"\d+", str(signal or ""))
        return int(match.group()) if match else 0

    @staticmethod
    def is_open_auth(auth):
        normalized = WifiScannerApp.normalize(auth)
        return normalized in {
            "abrir",
            "aberta",
            "open",
            "none",
            "nenhuma",
            "sem autenticacao",
            "no authentication",
        }

# --------------------------------------------------------
    # PARSER DO NETSH
    # --------------------------------------------------------
    def parse_netsh(self, text):
        networks = []
        current_ssid = None
        current_network = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # SSID
            match = re.match(r"SSID\s+\d+\s*:\s*(.*)$", line, re.I)
            if match:
                current_ssid = match.group(1).strip()
                if not current_ssid:
                    current_ssid = "SSID OCULTO"
                continue

            # BSSID
            match = re.match(r"BSSID\s+\d+\s*:\s*(.+)$", line, re.I)
            if match and current_ssid is not None:
                current_network = {
                    "ssid": current_ssid,
                    "bssid": match.group(1).strip(),
                    "signal": "",
                    "radio": "",
                    "channel": "",
                    "auth": "",
                    "crypto": "",
                    "basic_rates": "",
                    "other_rates": "",
                    "rates": ""
                }
                networks.append(current_network)
                continue

            if current_network is None:
                continue

            normalized = self.normalize(line)
            if normalized.startswith("sinal"):
                match = re.search(r"(\d+)\s*%", line)
                if match:
                    current_network["signal"] = match.group(1) + "%"
            elif normalized.startswith("tipo de radio"):
                if ":" in line:
                    current_network["radio"] = line.split(":", 1)[1].strip()
            elif normalized.startswith("canal"):
                if ":" in line:
                    current_network["channel"] = line.split(":", 1)[1].strip()
            elif normalized.startswith("autenticacao"):
                if ":" in line:
                    current_network["auth"] = line.split(":", 1)[1].strip()
            elif normalized.startswith("criptografia"):
                if ":" in line:
                    current_network["crypto"] = line.split(":", 1)[1].strip()
            elif normalized.startswith("taxas basicas"):
                if ":" in line:
                    current_network["basic_rates"] = line.split(":", 1)[1].strip()
            elif normalized.startswith("outras taxas"):
                if ":" in line:
                    current_network["other_rates"] = line.split(":", 1)[1].strip()

        for network in networks:
            basic = network["basic_rates"]
            other = network["other_rates"]
            network["rates"] = f"{basic} | {other}" if basic and other else basic or other

        networks.sort(key=lambda n: self.signal_number(n["signal"]), reverse=True)
        return networks


    # --------------------------------------------------------
    # ATUALIZA RESULTADOS
    # --------------------------------------------------------
    def update_results(self, networks):
        self.scanning = False
        self.scan_button.config(state="normal")

        self.networks = sorted(
            networks,
            key=lambda n: self.signal_number(n["signal"]),
            reverse=True,
        )

        self.apply_filter()

        total_networks = len({
            n["ssid"] for n in self.networks
        })

        total_bssid = len(self.networks)

        total_open = sum(
            1 for n in self.networks
            if self.is_open_auth(n["auth"])
        )

        strongest = (
            self.networks[0]["signal"]
            if self.networks
            else "--"
        )

        self.total_var.set(f"REDES: {total_networks}")
        self.bssid_var.set(f"PONTOS: {total_bssid}")
        self.open_var.set(f"ABERTAS: {total_open}")
        self.strongest_var.set(f"MELHOR SINAL: {strongest}")

        self.status_var.set(
            f"[ SCAN CONCLUÍDO // {total_networks} REDES // "
            f"ORDENADO POR SINAL ↓ ]"
        )

    # --------------------------------------------------------
    # FILTRO
    # --------------------------------------------------------
    def on_filter_changed(self, *_):
        self.apply_filter()

    def apply_filter(self):
        term = self.normalize(
            self.filter_var.get().strip()
        )

        if not term:
            self.filtered_networks = list(self.networks)
        else:
            self.filtered_networks = [
                n for n in self.networks
                if term in self.normalize(
                    " ".join([
                        n["ssid"],
                        n["bssid"],
                        n["signal"],
                        n["radio"],
                        n["channel"],
                        n["auth"],
                        n["crypto"],
                        n["rates"],
                    ])
                )
            ]

        self.filtered_networks.sort(
            key=lambda n: self.signal_number(n["signal"]),
            reverse=True,
        )

        self.render_current_list()

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------
    def sort_by_column(self, column):
        if not self.filtered_networks:
            return

        if column == "signal":
            self.filtered_networks.sort(
                key=lambda n: self.signal_number(n["signal"]),
                reverse=True,
            )

        elif column == "ssid":
            self.filtered_networks.sort(
                key=lambda n: n["ssid"].casefold()
            )

        elif column == "channel":
            def channel_value(network):
                match = re.search(
                    r"\d+",
                    network.get("channel", ""),
                )
                return int(match.group()) if match else 999

            self.filtered_networks.sort(key=channel_value)

        elif column == "rank":
            self.filtered_networks.sort(
                key=lambda n: self.signal_number(n["signal"]),
                reverse=True,
            )

        else:
            self.filtered_networks.sort(
                key=lambda n: str(n.get(column, "")).casefold()
            )

        self.render_current_list()

    def render_current_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, network in enumerate(
            self.filtered_networks,
            start=1,
        ):
            signal = self.signal_number(network["signal"])

            if signal >= 80:
                tag = "signal_excellent"
            elif signal >= 60:
                tag = "signal_good"
            elif signal >= 40:
                tag = "signal_medium"
            elif signal >= 20:
                tag = "signal_weak"
            else:
                tag = "signal_bad"

            # Rede aberta continua com prioridade
            if self.is_open_auth(network["auth"]):
                tag = "open_network"

            # SSID OCULTO = COR ABÓBORA
            # prioridade máxima para o SSID oculto
            if network.get("ssid", "").strip().upper() == "SSID OCULTO":
                tag = "hidden_ssid"

            self.tree.insert(
                "",
                "end",
                iid=str(index - 1),
                values=(
                    index,
                    network["ssid"],
                    network["bssid"],
                    network["signal"],
                    network["radio"],
                    network["channel"],
                    network["auth"],
                    network["crypto"],
                    network["rates"],
                ),
                tags=(tag,),
            )

    # --------------------------------------------------------
    # DETALHES
    # --------------------------------------------------------
    def show_details(self, _event=None):
        selected = self.tree.selection()

        if not selected:
            return

        try:
            index = int(selected[0])
            n = self.filtered_networks[index]
        except (ValueError, IndexError):
            return

        self.details_var.set(
            f"> SSID: {n['ssid']}    |    "
            f"BSSID: {n['bssid']}    |    "
            f"SINAL: {n['signal']}    |    "
            f"RADIO: {n['radio']}    |    "
            f"CANAL: {n['channel']}\n"
            f"> AUTH: {n['auth']}    |    "
            f"CRIPTO: {n['crypto']}    |    "
            f"TAXAS BASICAS: {n['basic_rates'] or '-'}    |    "
            f"OUTRAS: {n['other_rates'] or '-'}"
        )

    # --------------------------------------------------------
    # COPIAR
    # --------------------------------------------------------
    def copy_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "COPIAR",
                "Selecione uma rede primeiro.",
            )
            return

        try:
            index = int(selected[0])
            n = self.filtered_networks[index]
        except (ValueError, IndexError):
            messagebox.showerror(
                "COPIAR",
                "Não foi possível identificar a rede selecionada.",
            )
            return

        text = (
            f"SSID: {n['ssid']}\n"
            f"BSSID: {n['bssid']}\n"
            f"Sinal: {n['signal']}\n"
            f"Radio: {n['radio']}\n"
            f"Canal: {n['channel']}\n"
            f"Autenticação: {n['auth']}\n"
            f"Criptografia: {n['crypto']}\n"
            f"Taxas básicas: {n['basic_rates']}\n"
            f"Outras taxas: {n['other_rates']}"
        )

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

        self.status_var.set("[ DADOS COPIADOS PARA A ÁREA DE TRANSFERÊNCIA ]")

    # --------------------------------------------------------
    # EXPORTAR HTML COMPLETO
    # --------------------------------------------------------
    def export_html(self):

        if not self.networks:
            messagebox.showinfo(
                "EXPORTAR HTML",
                "Execute um scan antes de gerar o relatório."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Salvar Relatório Completo de Auditoria Wi-Fi",
            defaultextension=".html",
            filetypes=[
                ("Documento HTML", "*.html"),
                ("Todos os arquivos", "*.*"),
            ],
            initialfile="wifi_audit_report.html",
        )

        if not path:
            return

        # ====================================================
        # ESTATÍSTICAS GERAIS
        # ====================================================

        total_ssids = len({
            n.get("ssid", "")
            for n in self.networks
        })

        total_bssids = len(self.networks)

        # Todas as redes abertas
        open_networks = [
            n for n in self.networks
            if self.is_open_auth(n.get("auth", ""))
        ]

        total_open = len(open_networks)

        # Todas as redes com 100%
        networks_100 = [
            n for n in self.networks
            if self.signal_number(
                n.get("signal", "")
            ) == 100
        ]

        total_100 = len(networks_100)

        # Todos os SSIDs ocultos
        hidden_networks = [
            n for n in self.networks
            if n.get("ssid", "").strip().upper()
            == "SSID OCULTO"
        ]

        total_hidden = len(hidden_networks)

        # ====================================================
        # MELHOR SINAL
        # ====================================================

        best_signal_number = max(
            (
                self.signal_number(
                    n.get("signal", "")
                )
                for n in self.networks
            ),
            default=0
        )

        best_networks = [
            n for n in self.networks
            if self.signal_number(
                n.get("signal", "")
            ) == best_signal_number
        ]

        # ====================================================
        # DATA
        # ====================================================

        generated_date = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        # ====================================================
        # FUNÇÃO PARA STATUS
        # ====================================================

        def status_html(network):

            if self.is_open_auth(
                network.get("auth", "")
            ):
                return """
                <span class="open-badge">
                    🔓 ABERTA
                </span>
                """

            return """
            <span class="secure-badge">
                🔐 PROTEGIDA
            </span>
            """

        # ====================================================
        # FUNÇÃO PARA SSID
        # ====================================================

        def ssid_html(network):

            ssid = network.get(
                "ssid",
                ""
            ).strip()

            if ssid.upper() == "SSID OCULTO":

                return """
                <span class="hidden-ssid">
                    ⚠ SSID OCULTO
                </span>
                """

            return escape(ssid)

        # ====================================================
        # [ MELHOR REDE DETECTADA ]
        # TODAS AS REDES COM MAIOR SINAL
        # ====================================================

        best_cards = []

        for n in best_networks:

            best_cards.append(
                f"""
                <div class="best-card">

                    <div class="best-header">

                        <div>

                            <div class="best-label">
                                ★ MELHOR REDE DETECTADA
                            </div>

                            <div class="best-name">
                                {ssid_html(n)}
                            </div>

                        </div>

                        <div class="best-signal">
                            {escape(n.get("signal", ""))}
                        </div>

                    </div>

                    <div class="best-status">

                        {status_html(n)}

                    </div>

                    <div class="info-grid">

                        <div class="info-box">
                            <span>BSSID</span>
                            <strong>
                                {escape(n.get("bssid", ""))}
                            </strong>
                        </div>

                        <div class="info-box">
                            <span>RÁDIO</span>
                            <strong>
                                {escape(n.get("radio", ""))}
                            </strong>
                        </div>

                        <div class="info-box">
                            <span>CANAL</span>
                            <strong>
                                {escape(n.get("channel", ""))}
                            </strong>
                        </div>

                        <div class="info-box">
                            <span>AUTENTICAÇÃO</span>
                            <strong>
                                {escape(n.get("auth", ""))}
                            </strong>
                        </div>

                        <div class="info-box">
                            <span>CRIPTOGRAFIA</span>
                            <strong>
                                {escape(n.get("crypto", ""))}
                            </strong>
                        </div>

                        <div class="info-box">
                            <span>TAXAS</span>
                            <strong>
                                {escape(n.get("rates", ""))}
                            </strong>
                        </div>

                    </div>

                </div>
                """
            )

        best_section = "".join(best_cards)

        # ====================================================
        # [ REDES COM 100% ]
        # ====================================================

        if networks_100:

            networks_100_cards = []

            for n in networks_100:

                networks_100_cards.append(
                    f"""
                    <div class="network-card">

                        <div class="network-header">

                            <span class="network-name">
                                {ssid_html(n)}
                            </span>

                            <span class="signal excellent">
                                {escape(n.get("signal", ""))}
                            </span>

                        </div>

                        <div class="network-status">

                            {status_html(n)}

                        </div>

                        <div class="network-details">

                            <b>BSSID:</b>
                            {escape(n.get("bssid", ""))}

                            &nbsp; | &nbsp;

                            <b>RÁDIO:</b>
                            {escape(n.get("radio", ""))}

                            &nbsp; | &nbsp;

                            <b>CANAL:</b>
                            {escape(n.get("channel", ""))}

                            &nbsp; | &nbsp;

                            <b>AUTH:</b>
                            {escape(n.get("auth", ""))}

                            &nbsp; | &nbsp;

                            <b>CRIPTO:</b>
                            {escape(n.get("crypto", ""))}

                        </div>

                    </div>
                    """
                )

            networks_100_section = "".join(
                networks_100_cards
            )

        else:

            networks_100_section = """
            <div class="empty-box">
                NENHUMA REDE COM 100% DE SINAL.
            </div>
            """

        # ====================================================
        # [ REDES ABERTAS ]
        # TODAS AS REDES ABERTAS
        # ====================================================

        if open_networks:

            open_cards = []

            for n in open_networks:

                open_cards.append(
                    f"""
                    <div class="open-card">

                        <div class="open-header">

                            <span class="open-name">
                                {ssid_html(n)}
                            </span>

                            <span class="open-signal">
                                {escape(n.get("signal", ""))}
                            </span>

                        </div>

                        <div class="open-status">
                            🔓 REDE ABERTA
                        </div>

                        <div class="open-details">

                            <div>
                                <span>BSSID</span>
                                <strong>
                                    {escape(n.get("bssid", ""))}
                                </strong>
                            </div>

                            <div>
                                <span>RÁDIO</span>
                                <strong>
                                    {escape(n.get("radio", ""))}
                                </strong>
                            </div>

                            <div>
                                <span>CANAL</span>
                                <strong>
                                    {escape(n.get("channel", ""))}
                                </strong>
                            </div>

                            <div>
                                <span>AUTENTICAÇÃO</span>
                                <strong>
                                    {escape(n.get("auth", ""))}
                                </strong>
                            </div>

                            <div>
                                <span>CRIPTOGRAFIA</span>
                                <strong>
                                    {escape(n.get("crypto", ""))}
                                </strong>
                            </div>

                            <div>
                                <span>TAXAS</span>
                                <strong>
                                    {escape(n.get("rates", ""))}
                                </strong>
                            </div>

                        </div>

                    </div>
                    """
                )

            open_section = "".join(
                open_cards
            )

        else:

            open_section = """
            <div class="empty-box">
                NENHUMA REDE ABERTA FOI DETECTADA.
            </div>
            """

        # ====================================================
        # [ SSIDS OCULTOS ]
        # ====================================================

        if hidden_networks:

            hidden_cards = []

            for n in hidden_networks:

                hidden_cards.append(
                    f"""
                    <div class="hidden-card">

                        <div class="hidden-header">

                            <span class="hidden-title">
                                ⚠ SSID OCULTO
                            </span>

                            <span class="hidden-signal">
                                {escape(n.get("signal", ""))}
                            </span>

                        </div>

                        <div class="hidden-details">

                            <b>BSSID:</b>
                            {escape(n.get("bssid", ""))}

                            &nbsp; | &nbsp;

                            <b>RÁDIO:</b>
                            {escape(n.get("radio", ""))}

                            &nbsp; | &nbsp;

                            <b>CANAL:</b>
                            {escape(n.get("channel", ""))}

                            &nbsp; | &nbsp;

                            <b>AUTH:</b>
                            {escape(n.get("auth", ""))}

                            &nbsp; | &nbsp;

                            <b>CRIPTO:</b>
                            {escape(n.get("crypto", ""))}

                        </div>

                    </div>
                    """
                )

            hidden_section = "".join(
                hidden_cards
            )

        else:

            hidden_section = """
            <div class="empty-box">
                NENHUM SSID OCULTO DETECTADO.
            </div>
            """

        # ====================================================
        # TABELA COMPLETA
        # ====================================================

        rows = []

        for idx, net in enumerate(
            self.networks,
            start=1
        ):

            sig_num = self.signal_number(
                net.get("signal", "")
            )

            if sig_num >= 80:

                sig_class = "excellent"

            elif sig_num >= 60:

                sig_class = "good"

            elif sig_num >= 40:

                sig_class = "medium"

            elif sig_num >= 20:

                sig_class = "weak"

            else:

                sig_class = "bad"

            is_open = self.is_open_auth(
                net.get("auth", "")
            )

            row_class = (
                "open-row"
                if is_open
                else ""
            )

            rows.append(
                f"""
                <tr class="{row_class}">

                    <td class="rank">
                        #{idx}
                    </td>

                    <td class="ssid">
                        {ssid_html(net)}
                    </td>

                    <td>
                        {escape(net.get("bssid", ""))}
                    </td>

                    <td>

                        <span class="signal {sig_class}">
                            {escape(net.get("signal", ""))}
                        </span>

                    </td>

                    <td>
                        {escape(net.get("radio", ""))}
                    </td>

                    <td>
                        {escape(net.get("channel", ""))}
                    </td>

                    <td>
                        {escape(net.get("auth", ""))}
                    </td>

                    <td>
                        {escape(net.get("crypto", ""))}
                    </td>

                    <td>
                        {escape(net.get("rates", ""))}
                    </td>

                    <td>
                        {status_html(net)}
                    </td>

                </tr>
                """
            )

        # ====================================================
        # HTML
        # ====================================================

        html_doc = f"""<!DOCTYPE html>

    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
    Wi-Fi Scanner // Relatório Completo
    </title>

    <style>

    /* =====================================================
    BASE
    ===================================================== */

    * {{
        box-sizing: border-box;
    }}

    body {{

        margin: 0;

        padding: 30px;

        background:
            radial-gradient(
                circle at top,
                #0b2410 0%,
                #000000 70%
            );

        color: #b8ffb8;

        font-family:
            Consolas,
            "Courier New",
            monospace;
    }}

    .container {{

        max-width: 1800px;

        margin: auto;
    }}

    .terminal {{

        border:
            1px solid #00ff41;

        background:
            rgba(3,10,4,.97);

        box-shadow:
            0 0 25px
            rgba(0,255,65,.20);
    }}

    /* =====================================================
    CABEÇALHO
    ===================================================== */

    .topbar {{

        padding: 25px;

        display: flex;

        justify-content:
            space-between;

        align-items: center;

        flex-wrap: wrap;

        border-bottom:
            1px solid #007a20;
    }}

    .title {{

        color: #00ff41;

        font-size: 28px;

        font-weight: bold;
    }}

    .subtitle {{

        margin-top: 7px;

        color: #00b82e;

        font-size: 11px;
    }}

    .date {{

        color: #00e5ff;

        font-size: 12px;
    }}

    /* =====================================================
    ESTATÍSTICAS
    ===================================================== */

    .stats {{

        display: grid;

        grid-template-columns:
            repeat(6,1fr);

        gap: 10px;

        padding: 15px;
    }}

    .stat {{

        padding: 16px;

        background: #071007;

        border:
            1px solid #0d3015;
    }}

    .stat-label {{

        color: #007a20;

        font-size: 9px;

        margin-bottom: 8px;
    }}

    .stat-value {{

        color: #00ff41;

        font-size: 24px;

        font-weight: bold;
    }}

    .stat-orange {{

        color: #ff9900;
    }}

    .stat-blue {{

        color: #00e5ff;
    }}

    /* =====================================================
    TÍTULOS DAS SEÇÕES
    ===================================================== */

    .section-title {{

        margin:
            20px 15px 12px;

        padding:
            14px 16px;

        border:
            1px solid #ff9900;

        background:
            rgba(255,153,0,.06);

        color:
            #ff9900;

        font-size: 16px;

        font-weight: bold;
    }}

    /* =====================================================
    MELHOR REDE
    ===================================================== */

    .best-container {{

        padding:
            0 15px;
    }}

    .best-card {{

        margin-bottom: 12px;

        padding: 20px;

        border:
            1px solid #ff9900;

        background:
            rgba(255,153,0,.06);

        box-shadow:
            0 0 15px
            rgba(255,153,0,.10);
    }}

    .best-header {{

        display: flex;

        justify-content:
            space-between;

        align-items:
            center;
    }}

    .best-label {{

        color:
            #ff9900;

        font-size:
            11px;

        font-weight:
            bold;
    }}

    .best-name {{

        margin-top:
            8px;

        color:
            #ff9900;

        font-size:
            22px;

        font-weight:
            bold;
    }}

    .best-signal {{

        color:
            #00ff41;

        font-size:
            30px;

        font-weight:
            bold;
    }}

    .best-status {{

        margin-top:
            8px;
    }}

    .info-grid {{

        display:
            grid;

        grid-template-columns:
            repeat(3,1fr);

        gap:
            8px;

        margin-top:
            15px;
    }}

    .info-box {{

        padding:
            10px;

        background:
            rgba(0,0,0,.30);

        border:
            1px solid #3d2800;
    }}

    .info-box span {{

        display:
            block;

        color:
            #996600;

        font-size:
            9px;

        margin-bottom:
            5px;
    }}

    .info-box strong {{

        color:
            #b8ffb8;

        font-size:
            11px;
    }}

    /* =====================================================
    REDES 100%
    ===================================================== */

    .network-container {{

        padding:
            0 15px;
    }}

    .network-card {{

        padding:
            14px;

        margin-bottom:
            8px;

        border:
            1px solid #00ff41;

        background:
            rgba(0,255,65,.04);
    }}

    .network-header {{

        display:
            flex;

        justify-content:
            space-between;

        align-items:
            center;
    }}

    .network-name {{

        color:
            #ffffff;

        font-size:
            16px;

        font-weight:
            bold;
    }}

    .network-status {{

        margin-top:
            7px;
    }}

    .network-details {{

        margin-top:
            10px;

        color:
            #66aa66;

        font-size:
            10px;

        line-height:
            1.8;
    }}

    /* =====================================================
    REDES ABERTAS
    ===================================================== */

    .open-container {{

        padding:
            0 15px;
    }}

    .open-card {{

        margin-bottom:
            10px;

        padding:
            17px;

        border:
            1px solid #00e5ff;

        background:
            rgba(0,229,255,.06);

        box-shadow:
            0 0 10px
            rgba(0,229,255,.08);
    }}

    .open-header {{

        display:
            flex;

        justify-content:
            space-between;

        align-items:
            center;
    }}

    .open-name {{

        color:
            #00e5ff;

        font-size:
            17px;

        font-weight:
            bold;
    }}

    .open-signal {{

        color:
            #00e5ff;

        font-size:
            20px;

        font-weight:
            bold;
    }}

    .open-status {{

        margin-top:
            8px;

        color:
            #00e5ff;

        font-weight:
            bold;
    }}

    .open-details {{

        display:
            grid;

        grid-template-columns:
            repeat(3,1fr);

        gap:
            8px;

        margin-top:
            12px;
    }}

    .open-details div {{

        padding:
            9px;

        background:
            rgba(0,0,0,.25);

        border:
            1px solid
            rgba(0,229,255,.20);
    }}

    .open-details span {{

        display:
            block;

        color:
            #008899;

        font-size:
            9px;
    }}

    .open-details strong {{

        color:
            #b8ffff;

        font-size:
            11px;
    }}

    /* =====================================================
    SSID OCULTO
    ===================================================== */

    .hidden-card {{

        margin:
            0 15px 10px;

        padding:
            16px;

        border:
            1px solid #ff9900;

        background:
            rgba(255,153,0,.06);
    }}

    .hidden-header {{

        display:
            flex;

        justify-content:
            space-between;
    }}

    .hidden-title {{

        color:
            #ff9900;

        font-size:
            16px;

        font-weight:
            bold;
    }}

    .hidden-signal {{

        color:
            #ff9900;

        font-weight:
            bold;
    }}

    .hidden-details {{

        margin-top:
            10px;

        color:
            #996600;

        font-size:
            10px;

        line-height:
            1.8;
    }}

    .hidden-ssid {{

        color:
            #ff9900
            !important;

        font-weight:
            bold;

        text-shadow:
            0 0 7px
            rgba(255,153,0,.45);
    }}

    /* =====================================================
    BADGES
    ===================================================== */

    .open-badge {{

        display:
            inline-block;

        padding:
            5px 10px;

        color:
            #00e5ff;

        border:
            1px solid #00e5ff;

        font-weight:
            bold;
    }}

    .secure-badge {{

        display:
            inline-block;

        padding:
            4px 8px;

        color:
            #00ff41;

        border:
            1px solid #00ff41;

        font-size:
            10px;

        font-weight:
            bold;
    }}

    /* =====================================================
    TABELA
    ===================================================== */

    .table-wrap {{

        padding:
            15px;

        overflow-x:
            auto;
    }}

    table {{

        width:
            100%;

        min-width:
            1400px;

        border-collapse:
            collapse;

        font-size:
            11px;
    }}

    th {{

        padding:
            12px 8px;

        background:
            #071a0a;

        color:
            #00ff41;

        border:
            1px solid #0d3015;

        text-align:
            left;
    }}

    td {{

        padding:
            11px 8px;

        color:
            #b8ffb8;

        border:
            1px solid #0d3015;
    }}

    tr:nth-child(even) {{

        background:
            rgba(7,26,10,.35);
    }}

    tr:hover {{

        background:
            rgba(0,255,65,.10);
    }}

    /* =====================================================
    LINHAS ABERTAS
    ===================================================== */

    tr.open-row {{

        background:
            rgba(0,229,255,.08)
            !important;
    }}

    tr.open-row td {{

        color:
            #00e5ff
            !important;

        border-color:
            rgba(0,229,255,.25)
            !important;
    }}

    tr.open-row .ssid {{

        color:
            #00e5ff
            !important;
    }}

    /* =====================================================
    RANK
    ===================================================== */

    .rank {{

        color:
            #00ff41;

        font-weight:
            bold;
    }}

    .ssid {{

        color:
            #ffffff;

        font-weight:
            bold;
    }}

    /* =====================================================
    SINAL
    ===================================================== */

    .signal {{

        display:
            inline-block;

        min-width:
            65px;

        padding:
            4px 8px;

        text-align:
            center;

        font-weight:
            bold;

        border:
            1px solid
            currentColor;
    }}

    .excellent {{

        color:
            #00ff41;

        box-shadow:
            0 0 8px
            rgba(0,255,65,.20);
    }}

    .good {{

        color:
            #66ff66;
    }}

    .medium {{

        color:
            #ffff00;
    }}

    .weak {{

        color:
            #ff9900;
    }}

    .bad {{

        color:
            #ff3333;
    }}

    /* =====================================================
    VAZIO
    ===================================================== */

    .empty-box {{

        margin:
            0 15px 15px;

        padding:
            16px;

        border:
            1px solid #007a20;

        color:
            #007a20;
    }}

    /* =====================================================
    FOOTER
    ===================================================== */

    .footer {{

        padding:
            18px;

        border-top:
            1px solid #007a20;

        color:
            #007a20;

        text-align:
            center;

        font-size:
            10px;
    }}

    @media(max-width:900px) {{

        body {{
            padding: 10px;
        }}

        .stats {{
            grid-template-columns:
                1fr 1fr;
        }}

        .info-grid {{
            grid-template-columns:
                1fr;
        }}

        .open-details {{
            grid-template-columns:
                1fr;
        }}
    }}

    </style>

    </head>

    <body>

    <div class="container">

    <div class="terminal">

    <!-- ==================================================
        CABEÇALHO
        ================================================== -->

    <div class="topbar">

        <div>

            <div class="title">
                &gt; WIFI SCANNER // RELATÓRIO COMPLETO
            </div>

            <div class="subtitle">

                [ NETSH WLAN ]

                [ BSSID ]

                [ SINAL ]

                [ CANAL ]

                [ AUTENTICAÇÃO ]

                [ CRIPTOGRAFIA ]

            </div>

        </div>

        <div class="date">

            RELATÓRIO:
            {escape(generated_date)}

        </div>

    </div>

    <!-- ==================================================
        ESTATÍSTICAS
        ================================================== -->

    <div class="stats">

        <div class="stat">

            <div class="stat-label">
                REDES ÚNICAS
            </div>

            <div class="stat-value">
                {total_ssids}
            </div>

        </div>

        <div class="stat">

            <div class="stat-label">
                PONTOS DE ACESSO (BSSIDs)
            </div>

            <div class="stat-value">
                {total_bssids}
            </div>

        </div>

        <div class="stat">

            <div class="stat-label">
                REDES ABERTAS
            </div>

            <div class="stat-value stat-blue">
                {total_open}
            </div>

        </div>

        <div class="stat">

            <div class="stat-label">
                REDES COM 100%
            </div>

            <div class="stat-value">
                {total_100}
            </div>

        </div>

        <div class="stat">

            <div class="stat-label">
                SSIDs OCULTOS
            </div>

            <div class="stat-value stat-orange">
                {total_hidden}
            </div>

        </div>

        <div class="stat">

            <div class="stat-label">
                MELHOR SINAL
            </div>

            <div class="stat-value stat-blue">
                {best_signal_number}%
            </div>

        </div>

    </div>

    <!-- ==================================================
        MELHOR REDE
        ================================================== -->

    <div class="section-title">

        [ MELHOR REDE DETECTADA ]

        — TODAS COM {best_signal_number}%

    </div>

    <div class="best-container">

        {best_section}

    </div>

    <!-- ==================================================
        REDES 100%
        ================================================== -->

    <div class="section-title">

        [ REDES COM SINAL DE 100% ]

        — TOTAL: {total_100}

    </div>

    <div class="network-container">

        {networks_100_section}

    </div>

    <!-- ==================================================
        REDES ABERTAS
        ================================================== -->

    <div class="section-title">

        [ REDES ABERTAS ]

        — TODAS AS REDES SEM AUTENTICAÇÃO

        — TOTAL: {total_open}

    </div>

    <div class="open-container">

        {open_section}

    </div>

    <!-- ==================================================
        SSID OCULTOS
        ================================================== -->

    <div class="section-title">

        [ SSIDs OCULTOS ]

        — TOTAL: {total_hidden}

    </div>

    {hidden_section}

    <!-- ==================================================
        TODAS AS REDES
        ================================================== -->

    <div class="section-title">

        [ TODAS AS REDES DETECTADAS ]

        — {total_bssids} BSSIDs

    </div>

    <div class="table-wrap">

    <table>

    <thead>

    <tr>

        <th>#</th>

        <th>SSID / REDE</th>

        <th>BSSID</th>

        <th>SINAL</th>

        <th>RÁDIO</th>

        <th>CANAL</th>

        <th>AUTENTICAÇÃO</th>

        <th>CRIPTOGRAFIA</th>

        <th>TAXAS Mbps</th>

        <th>STATUS</th>

    </tr>

    </thead>

    <tbody>

    {"".join(rows)}

    </tbody>

    </table>

    </div>

    <!-- ==================================================
        RODAPÉ
        ================================================== -->

    <div class="footer">

        WIFI NETSH SCANNER

        //

        RELATÓRIO COMPLETO

        //

        {total_ssids} REDES ÚNICAS

        //

        {total_bssids} BSSIDs

        //

        {total_open} ABERTAS

        //

        {total_100} COM 100%

        //

        {total_hidden} OCULTAS

    </div>

    </div>

    </div>

    </body>

    </html>
    """

        # ====================================================
        # SALVAR ARQUIVO
        # ====================================================

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(html_doc)

            messagebox.showinfo(
                "SUCESSO",
                f"Relatório HTML completo gerado!\n\n{path}"
            )

        except Exception as exc:

            messagebox.showerror(
                "ERRO DE ESCRITA",
                str(exc)
            )

    # --------------------------------------------------------
    # FECHAR
    # --------------------------------------------------------
    def on_close(self):
        self.scanning = False
        self.root.destroy()

# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = WifiScannerApp(root)
    root.mainloop()
