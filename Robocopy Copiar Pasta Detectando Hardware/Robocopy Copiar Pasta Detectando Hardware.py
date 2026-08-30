import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import platform
import time

class HardwareDetector:
    """Detecta automaticamente o hardware do PC"""

    @staticmethod
    def get_cpu_name():
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "Name"]
            return lines[0] if lines else "CPU desconhecida"
        except Exception:
            return "CPU desconhecida"

    @staticmethod
    def get_cpu_cores():
        try:
            return os.cpu_count() or 2
        except Exception:
            return 2

    @staticmethod
    def get_cpu_threads():
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "NumberOfLogicalProcessors"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n")
                     if l.strip() and l.strip() != "NumberOfLogicalProcessors"]
            return int(lines[0]) if lines else os.cpu_count() or 2
        except Exception:
            return os.cpu_count() or 2

    @staticmethod
    def get_ram_gb():
        try:
            result = subprocess.run(
                ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n")
                     if l.strip() and l.strip() != "TotalPhysicalMemory"]
            if lines:
                return round(int(lines[0]) / (1024 ** 3))
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_ram_speed():
        try:
            result = subprocess.run(
                ["wmic", "memorychip", "get", "Speed"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "Speed"]
            speeds = [int(l) for l in lines if l.isdigit()]
            return max(speeds) if speeds else 0
        except Exception:
            return 0

    @staticmethod
    def get_disk_type(drive="C:"):
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-PhysicalDisk | Select-Object MediaType, FriendlyName | Format-List"],
                capture_output=True, text=True, timeout=15
            )
            output = result.stdout.lower()
            if "ssd" in output or "solid state" in output:
                return "SSD"
            if "hdd" in output or "hard disk" in output:
                return "HDD"
        except Exception:
            pass
        return "SSD/HDD"

    @staticmethod
    def get_disk_model():
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "Model"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "Model"]
            return lines[0] if lines else "Disco desconhecido"
        except Exception:
            return "Disco desconhecido"

    @staticmethod
    def get_disk_free_gb(drive="C:"):
        try:
            result = subprocess.run(
                ["wmic", "logicaldisk", "where", f"DeviceID='{drive}'", "get", "FreeSpace"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "FreeSpace"]
            if lines and lines[0].isdigit():
                return round(int(lines[0]) / (1024 ** 3), 1)
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_disk_total_gb(drive="C:"):
        try:
            result = subprocess.run(
                ["wmic", "logicaldisk", "where", f"DeviceID='{drive}'", "get", "Size"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "Size"]
            if lines and lines[0].isdigit():
                return round(int(lines[0]) / (1024 ** 3), 1)
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_gpu_name():
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "name"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and l.strip() != "Name"]
            return lines[0] if lines else "GPU desconhecida"
        except Exception:
            return "GPU desconhecida"

    @staticmethod
    def get_os_info():
        try:
            result = subprocess.run(
                ["wmic", "os", "get", "Caption,Version"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip() and "Caption" not in l]
            return lines[0] if lines else f"Windows {platform.version()}"
        except Exception:
            return f"Windows {platform.version()}"

    def detect_all(self):
        return {
            "cpu_name": self.get_cpu_name(),
            "cpu_cores": self.get_cpu_cores(),
            "cpu_threads": self.get_cpu_threads(),
            "ram_gb": self.get_ram_gb(),
            "ram_speed": self.get_ram_speed(),
            "disk_type": self.get_disk_type(),
            "disk_model": self.get_disk_model(),
            "disk_free_gb": self.get_disk_free_gb(),
            "disk_total_gb": self.get_disk_total_gb(),
            "gpu_name": self.get_gpu_name(),
            "os_info": self.get_os_info(),
        }

    @staticmethod
    def calculate_optimal_settings(info):
        cores = info["cpu_cores"]
        ram = info["ram_gb"]
        disk = info["disk_type"]

        if disk == "SSD":
            optimal_threads = min(cores * 2, 16)
            max_threads = min(cores * 4, 32)
        else:
            optimal_threads = min(cores, 8)
            max_threads = min(cores * 2, 16)

        if ram <= 4:
            optimal_threads = min(optimal_threads, 4)
            max_threads = min(max_threads, 8)
        elif ram <= 8:
            optimal_threads = min(optimal_threads, 8)
            max_threads = min(max_threads, 12)

        max_gb = max(1, info.get("disk_free_gb", 32) or 32)
        retries, wait = (3, 2) if (ram >= 16 and disk == "SSD") else (2, 5)

        score = 0
        score += 3 if cores >= 8 else (2 if cores >= 4 else 1)
        score += 3 if ram >= 16 else (2 if ram >= 8 else 1)
        score += 3 if disk == "SSD" else (1 if disk == "HDD" else 2)

        if score >= 8:
            categoria, cor = "🟢 PC POTENTE", "#28a745"
        elif score >= 5:
            categoria, cor = "🟡 PC MÉDIO", "#ffc107"
        else:
            categoria, cor = "🔴 PC FRACO", "#dc3545"

        return {
            "optimal_threads": max(1, optimal_threads),
            "max_threads": max(1, max_threads),
            "max_gb": int(max_gb),
            "retries": retries,
            "wait": wait,
            "categoria": categoria,
            "cor": cor,
            "score": score,
        }


class RobocopyGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Robocopy Copiar Pasta Detectando Hardware")
        self.root.geometry("800x780")
        self.root.configure(bg="#1e1e2e")
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        self.process = None
        self.total_bytes = 0
        self.bytes_copiados = 0
        self.arquivos_copiados = 0
        self.cancelar_flag = False
        self.ocupado = False

        self.origem = tk.StringVar()
        self.destino = tk.StringVar()
        self.threads = tk.IntVar(value=4)
        self.max_gb = tk.IntVar(value=32)

        self.loading_label = tk.Label(
            self.root,
            text="⏳ Detectando hardware do PC\n\nAguarde...",
            font=("Arial", 18, "bold"),
            bg="#1e1e2e",
            fg="white",
        )
        self.loading_label.pack(expand=True)

        threading.Thread(target=self.detectar_e_construir, daemon=True).start()
        self.root.mainloop()

    def ao_fechar(self):
        self.cancelar_flag = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.root.destroy()

    def detectar_e_construir(self):
        detector = HardwareDetector()
        self.hw_info = detector.detect_all()
        self.settings = HardwareDetector.calculate_optimal_settings(self.hw_info)
        self.threads.set(self.settings["optimal_threads"])
        self.max_gb.set(min(self.settings["max_gb"], 999))
        self.root.after(0, self.criar_interface)

    def criar_interface(self):
        self.loading_label.destroy()

        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        entry_bg = "#313244"
        cat = self.settings["categoria"]
        cor_cat = self.settings["cor"]
        info = self.hw_info

        self.root.title(f"Robocopy Copiar Pasta - {cat}")
        self.root.configure(bg=bg)

        title_frame = tk.Frame(self.root, bg=bg)
        title_frame.pack(fill="x", pady=(10, 5))
        tk.Label(
            title_frame,
            text="🖥️ Robocopy Copiar Pasta - Auto Detect Hardware",
            font=("Arial", 17, "bold"),
            bg=bg,
            fg=accent,
        ).pack()
        tk.Label(title_frame, text=cat, font=("Arial", 14, "bold"), bg=bg, fg=cor_cat).pack()

        hw_frame = tk.LabelFrame(
            self.root,
            text="  🔍 Hardware Detectado Automaticamente ",
            font=("Arial", 11, "bold"),
            bg="#181825",
            fg=accent,
            bd=2,
            relief="groove",
            padx=15,
            pady=10,
        )
        hw_frame.pack(fill="x", padx=20, pady=5)

        ram_speed_text = f" @ {info['ram_speed']} MHz" if info["ram_speed"] else ""
        for line in [
            f"🔲 CPU:      {info['cpu_name']}",
            f"⚙️ Núcleos:  {info['cpu_cores']} núcleos / {info['cpu_threads']} threads",
            f"🧠 RAM:      {info['ram_gb']} GB{ram_speed_text}",
            f"💾 Disco:    {info['disk_model']}  [{info['disk_type']}]",
            f"📊 Espaço:   {info['disk_free_gb']} GB livres / {info['disk_total_gb']} GB total",
            f"🪟 Sistema:  {info['os_info']}",
        ]:
            tk.Label(hw_frame, text=line, font=("Consolas", 10), bg="#181825", fg=fg, anchor="w").pack(
                fill="x", pady=1
            )

        cfg_frame = tk.LabelFrame(
            self.root,
            text="  ⚡ Configurações Automáticas (ajuste se quiser)  ",
            font=("Arial", 11, "bold"),
            bg="#181825",
            fg="#a6e3a1",
            bd=2,
            relief="groove",
            padx=15,
            pady=10,
        )
        cfg_frame.pack(fill="x", padx=20, pady=5)

        f1 = tk.Frame(cfg_frame, bg="#181825")
        f1.pack(fill="x", pady=3)
        tk.Label(f1, text="📂 ORIGEM:", font=("Arial", 10, "bold"), bg="#181825", fg=fg, width=12, anchor="w").pack(
            side="left"
        )
        tk.Entry(
            f1, textvariable=self.origem, width=50, bg=entry_bg, fg=fg, insertbackground=fg, font=("Consolas", 10)
        ).pack(side="left", padx=5)
        tk.Button(
            f1,
            text="📁 Escolher",
            command=self.selecionar_origem,
            bg=accent,
            fg="#1e1e2e",
            font=("Arial", 9, "bold"),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=3)

        f2 = tk.Frame(cfg_frame, bg="#181825")
        f2.pack(fill="x", pady=3)
        tk.Label(f2, text="📂 DESTINO:", font=("Arial", 10, "bold"), bg="#181825", fg=fg, width=12, anchor="w").pack(
            side="left"
        )
        tk.Entry(
            f2, textvariable=self.destino, width=50, bg=entry_bg, fg=fg, insertbackground=fg, font=("Consolas", 10)
        ).pack(side="left", padx=5)
        tk.Button(
            f2,
            text="📁 Escolher",
            command=self.selecionar_destino,
            bg=accent,
            fg="#1e1e2e",
            font=("Arial", 9, "bold"),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=3)

        f3 = tk.Frame(cfg_frame, bg="#181825")
        f3.pack(fill="x", pady=3)
        tk.Label(f3, text="🧵 Threads:", font=("Arial", 10, "bold"), bg="#181825", fg=fg, width=12, anchor="w").pack(
            side="left"
        )
        max_t = self.settings["max_threads"]
        tk.Scale(
            f3,
            from_=1,
            to=max_t,
            orient="horizontal",
            variable=self.threads,
            length=300,
            bg="#181825",
            fg=fg,
            troughcolor=entry_bg,
            highlightthickness=0,
            font=("Arial", 9),
        ).pack(side="left", padx=5)
        tk.Label(
            f3,
            text=f"(Recomendado: {self.settings['optimal_threads']} | Max: {max_t})",
            font=("Arial", 9),
            bg="#181825",
            fg="#a6e3a1",
        ).pack(side="left", padx=5)

        f4 = tk.Frame(cfg_frame, bg="#181825")
        f4.pack(fill="x", pady=3)
        tk.Label(f4, text="📦 Max GB:", font=("Arial", 10, "bold"), bg="#181825", fg=fg, width=12, anchor="w").pack(
            side="left"
        )
        max_g = min(int(info["disk_free_gb"]) if info["disk_free_gb"] else 100, 999)
        if max_g < 1:
            max_g = 100
        tk.Scale(
            f4,
            from_=1,
            to=max_g,
            orient="horizontal",
            variable=self.max_gb,
            length=300,
            bg="#181825",
            fg=fg,
            troughcolor=entry_bg,
            highlightthickness=0,
            font=("Arial", 9),
        ).pack(side="left", padx=5)
        tk.Label(
            f4, text=f"(Livre: {info['disk_free_gb']} GB)", font=("Arial", 9), bg="#181825", fg="#f9e2af"
        ).pack(side="left", padx=5)

        prog_frame = tk.Frame(self.root, bg=bg)
        prog_frame.pack(fill="x", padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=entry_bg,
            background="#a6e3a1",
            thickness=25,
        )
        style.configure(
            "Scan.Horizontal.TProgressbar",
            troughcolor=entry_bg,
            background="#89b4fa",
            thickness=25,
        )

        self.progresso_bar = ttk.Progressbar(
            prog_frame, length=700, mode="determinate", style="Custom.Horizontal.TProgressbar"
        )
        self.progresso_bar.pack(pady=5)

        self.status_label = tk.Label(
            prog_frame,
            text="✅ Hardware detectado! Escolha origem e destino.",
            font=("Arial", 11),
            bg=bg,
            fg="#a6e3a1",
        )
        self.status_label.pack(pady=3)

        btn_frame = tk.Frame(self.root, bg=bg)
        btn_frame.pack(fill="x", padx=20, pady=5)

        self.btn_copiar = tk.Button(
            btn_frame,
            text=f"🚀 COPIAR (Modo Otimizado - {self.settings['optimal_threads']} threads)",
            font=("Arial", 13, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#218838",
            relief="flat",
            cursor="hand2",
            command=self.copiar_em_thread,
            height=2,
        )
        self.btn_copiar.pack(fill="x", pady=3)

        safe_threads = max(1, self.settings["optimal_threads"] // 2)
        self.btn_seguro = tk.Button(
            btn_frame,
            text=f"🛡️ COPIAR MODO SEGURO ({safe_threads} threads - mais leve)",
            font=("Arial", 11, "bold"),
            bg="#17a2b8",
            fg="white",
            activebackground="#138496",
            relief="flat",
            cursor="hand2",
            command=lambda: self.copiar_seguro(safe_threads),
            height=2,
        )
        self.btn_seguro.pack(fill="x", pady=3)

        self.btn_cancelar = tk.Button(
            btn_frame,
            text="❌ CANCELAR CÓPIA",
            font=("Arial", 10, "bold"),
            bg="#dc3545",
            fg="white",
            activebackground="#c82333",
            relief="flat",
            cursor="hand2",
            command=self.cancelar_copia,
        )
        self.btn_cancelar.pack(fill="x", pady=3)

    def selecionar_origem(self):
        if self.ocupado:
            return
        item = filedialog.askdirectory(title="Selecionar pasta ORIGEM")
        if item:
            self.origem.set(item)

    def selecionar_destino(self):
        if self.ocupado:
            return
        item = filedialog.askdirectory(title="Selecionar pasta DESTINO")
        if item:
            self.destino.set(item)

    def set_ocupado(self, ocupado):
        self.ocupado = ocupado
        estado = "disabled" if ocupado else "normal"
        try:
            self.btn_copiar.config(state=estado)
            self.btn_seguro.config(state=estado)
        except Exception:
            pass

    def copiar_em_thread(self):
        if self.ocupado:
            return
        if not self.origem.get() or not self.destino.get():
            messagebox.showerror("Erro", "Escolha a origem e o destino!")
            return
        if not os.path.isdir(self.origem.get()):
            messagebox.showerror("Erro", "A pasta de ORIGEM não existe!")
            return

        self.cancelar_flag = False
        self.progresso_bar.config(mode="determinate", style="Scan.Horizontal.TProgressbar")
        self.progresso_bar["value"] = 0
        self.arquivos_copiados = 0
        self.bytes_copiados = 0
        self.total_bytes = 0
        self.set_ocupado(True)
        self.ui_status("🔍 Etapa 1/2 — Calculando tamanho (interface livre, aguarde)...")

        # TUDO em background: calcular -> depois copiar (UI nunca trava)
        threading.Thread(target=self.pipeline_calcular_e_copiar, daemon=True).start()

    def copiar_seguro(self, threads):
        self.threads.set(threads)
        self.copiar_em_thread()

    def cancelar_copia(self):
        self.cancelar_flag = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.ui_status("❌ Cancelado pelo usuário.")
            messagebox.showwarning("Cancelado", "A operação foi cancelada.")
        else:
            self.ui_status("❌ Cancelamento solicitado...")

    def ui_status(self, texto, cor="#a6e3a1"):
        self.root.after(0, lambda: self.status_label.config(text=texto, fg=cor))

    def ui_progresso_scan(self, arquivos, gb):
        def _up():
            # barra “pulse” visual durante o scan (não é % da cópia)
            self.progresso_bar["value"] = (arquivos % 100)
            self.status_label.config(
                text=f"🔍 Escaneando origem... {arquivos} arquivos | {gb:.2f} GB encontrados",
                fg="#89b4fa",
            )

        self.root.after(0, _up)

    def ui_progresso_copia(self, pct, gb_ok, gb_tot, qtd, nome):
        def _up():
            self.progresso_bar.config(style="Custom.Horizontal.TProgressbar")
            self.progresso_bar["value"] = pct
            self.status_label.config(
                text=f"📋 Copiando [{pct:.1f}%]  {gb_ok:.2f}/{gb_tot:.2f} GB  |  {qtd} arq.  |  {nome}",
                fg="#a6e3a1",
            )

        self.root.after(0, _up)

    def pipeline_calcular_e_copiar(self):
        """Thread única: 1) calcula tamanho  2) só então inicia o robocopy"""
        origem = self.origem.get()
        destino = self.destino.get()

        # ===== ETAPA 1: CALCULAR (com feedback, sem travar UI) =====
        total = 0
        contagem = 0
        ultimo_update = 0.0

        try:
            for root, dirs, files in os.walk(origem):
                if self.cancelar_flag:
                    self.root.after(0, self._fim_cancelado)
                    return

                for name in files:
                    if self.cancelar_flag:
                        self.root.after(0, self._fim_cancelado)
                        return
                    try:
                        fp = os.path.join(root, name)
                        if os.path.islink(fp):
                            continue
                        total += os.path.getsize(fp)
                        contagem += 1
                    except OSError:
                        continue

                    # atualiza UI no máximo ~4x por segundo (não sobrecarrega)
                    agora = time.time()
                    if agora - ultimo_update >= 0.25:
                        ultimo_update = agora
                        gb = total / (1024 ** 3)
                        self.ui_progresso_scan(contagem, gb)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao calcular tamanho:\n{e}"))
            self.root.after(0, lambda: self.set_ocupado(False))
            return

        if self.cancelar_flag:
            self.root.after(0, self._fim_cancelado)
            return

        self.total_bytes = total if total > 0 else 1
        gb_total = self.total_bytes / (1024 ** 3)

        self.root.after(0, lambda: self.progresso_bar.config(value=0, style="Custom.Horizontal.TProgressbar"))
        self.ui_status(f"✅ Cálculo ok: {contagem} arquivos ({gb_total:.2f} GB). Iniciando cópia...")

        # pequena pausa só para o usuário ver a mensagem
        time.sleep(0.4)

        if self.cancelar_flag:
            self.root.after(0, self._fim_cancelado)
            return

        # ===== ETAPA 2: COPIAR =====
        self.executar_robocopy(origem, destino)

    def executar_robocopy(self, origem, destino):
        mt_val = self.threads.get()
        retries = self.settings["retries"]
        wait = self.settings["wait"]

        # /NP = sem porcentagem spam do robocopy (evita parse errado)
        # /NDL = sem lista de diretórios
        # /BYTES = tamanhos em bytes
        # /NJH /NJS = menos cabeçalho no começo
        cmd = [
            "robocopy",
            origem,
            destino,
            "/MIR",
            f"/MT:{mt_val}",
            f"/R:{retries}",
            f"/W:{wait}",
            "/NP",
            "/NDL",
            "/NJH",
            "/BYTES",
            "/XJ",
        ]

        creation = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                creationflags=creation,
            )
        except FileNotFoundError:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro", "Robocopy não encontrado!\nEste programa funciona apenas no Windows."
                ),
            )
            self.root.after(0, lambda: self.set_ocupado(False))
            return
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao iniciar: {e}"))
            self.root.after(0, lambda: self.set_ocupado(False))
            return

        self.arquivos_copiados = 0
        self.bytes_copiados = 0

        # Palavras/ruído do log do robocopy (PT/EN)
        ruido = {
            "new",
            "file",
            "newer",
            "older",
            "same",
            "*same",
            "extra",
            "*extra",
            "lonely",
            "tweaked",
            "changed",
            "modified",
            "mismatch",
            "novo",
            "arquivo",
            "dirs",
            "files",
            "bytes",
            "times",
            "ended",
            "started",
            "speed",
            "total",
        }

        try:
            for raw in self.process.stdout:
                if self.cancelar_flag:
                    break

                line = raw.strip()
                if not line:
                    continue

                # ignora linhas de resumo
                low = line.lower()
                if any(
                    x in low
                    for x in (
                        "dirs :",
                        "files :",
                        "bytes :",
                        "times :",
                        "speed :",
                        "total",
                        "------",
                        "options :",
                        "status",
                    )
                ):
                    continue

                parts = line.split()
                size_val = None
                nome = ""

                for i, part in enumerate(parts):
                    p = part.lower().strip("*")
                    if p in ruido:
                        continue
                    # tamanho em bytes (número puro)
                    if part.isdigit():
                        size_val = int(part)
                        resto = parts[i + 1 :]
                        caminho = " ".join(resto).strip()
                        nome = os.path.basename(caminho) if caminho else part
                        if len(nome) > 40:
                            nome = nome[:37] + "..."
                        break

                if size_val is None:
                    continue

                self.arquivos_copiados += 1
                self.bytes_copiados += size_val

                pct = min(100.0, (self.bytes_copiados / self.total_bytes) * 100.0)
                gb_ok = self.bytes_copiados / (1024 ** 3)
                gb_tot = self.total_bytes / (1024 ** 3)

                self.ui_progresso_copia(pct, gb_ok, gb_tot, self.arquivos_copiados, nome)
        except Exception:
            pass

        try:
            self.process.wait(timeout=5)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass

        if self.cancelar_flag:
            self.root.after(0, self._fim_cancelado)
            return

        code = self.process.returncode if self.process else 16
        # robocopy: 0–7 = sucesso / avisos; >=8 = erro
        self.root.after(0, lambda: self.finalizar(code is not None and code < 8, code))

    def _fim_cancelado(self):
        self.progresso_bar["value"] = 0
        self.set_ocupado(False)
        self.status_label.config(text="❌ Operação cancelada.", fg="#f38ba8")

    def finalizar(self, sucesso, code=0):
        self.set_ocupado(False)
        gb = self.bytes_copiados / (1024 ** 3)

        if sucesso:
            self.progresso_bar["value"] = 100
            self.status_label.config(text="✅ Cópia concluída com sucesso!", fg="#a6e3a1")
            messagebox.showinfo(
                "✅ Sucesso",
                f"Cópia concluída!\n\n"
                f"📁 Arquivos processados: {self.arquivos_copiados}\n"
                f"📊 Dados lidos no log: {gb:.2f} GB\n"
                f"🧵 Threads: {self.threads.get()}\n"
                f"💻 {self.settings['categoria']}",
            )
        else:
            self.status_label.config(text="❌ Erro na cópia!", fg="#f38ba8")
            messagebox.showerror(
                "Erro",
                f"Robocopy terminou com código {code}.\n\n"
                "Verifique:\n"
                "• Permissões de acesso\n"
                "• Se as pastas existem\n"
                "• Espaço em disco no destino",
            )


if __name__ == "__main__":
    RobocopyGUI()
