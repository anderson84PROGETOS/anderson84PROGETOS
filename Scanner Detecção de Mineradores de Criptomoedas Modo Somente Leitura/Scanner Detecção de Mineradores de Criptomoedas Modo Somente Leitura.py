#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner de Diagnóstico de Mineradores de Criptomoedas - Modo Somente Leitura
Windows Only - 100% Read-Only (não apaga, não modifica, não encerra processos)
"""

import os
import sys
import platform
import socket
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from collections import defaultdict

# ============================================================
# Dependências opcionais / fallback
# ============================================================
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# ============================================================
# Configurações
# ============================================================
SUSPICIOUS_PROCESS_NAMES = [
    "xmrig", "ccminer", "cpuminer", "lolminer", "trex", "t-rex",
    "nbminer", "phoenixminer", "ethminer", "nanominer", "wildrig",
    "miner", "minerd", "cgminer", "bfgminer", "sgminer", "gminer",
    "teamredminer", "claymore", "bminer", "srbminer", "rigel",
    "onezerominer", "kawpowminer", "cryptonight", "monero"
]

SUSPICIOUS_KEYWORDS = [
    "xmrig", "ccminer", "cpuminer", "lolminer", "trex", "t-rex",
    "nbminer", "phoenixminer", "ethminer", "nanominer", "wildrig",
    "miner", "mining", "cryptonight", "stratum", "hashrate",
    "xmr", "monero", "ethash", "kawpow", "randomx"
]

# ============================================================
# Funções de coleta (somente leitura)
# ============================================================

def is_suspicious_name(name: str) -> bool:
    if not name:
        return False
    name_lower = name.lower()
    for s in SUSPICIOUS_PROCESS_NAMES:
        if s in name_lower:
            return True
    return False


def is_suspicious_text(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def get_system_info() -> dict:
    info = {
        "computer_name": platform.node(),
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "desconhecido",
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "desconhecido",
        "python_version": platform.python_version(),
    }
    if HAS_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            info["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
            info["ram_available_gb"] = round(mem.available / (1024 ** 3), 2)
            info["ram_percent"] = mem.percent
        except Exception:
            info["ram_total_gb"] = "N/A"
        try:
            disk = psutil.disk_usage("C:\\")
            info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
            info["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
            info["disk_percent"] = disk.percent
        except Exception:
            info["disk_total_gb"] = "N/A"
        try:
            info["boot_time"] = datetime.datetime.fromtimestamp(
                psutil.boot_time()
            ).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            info["boot_time"] = "N/A"
        try:
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            info["cpu_count_physical"] = psutil.cpu_count(logical=False)
            info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        except Exception:
            pass
    else:
        info["ram_total_gb"] = "psutil não instalado"
        info["disk_total_gb"] = "psutil não instalado"
    return info


def get_running_processes() -> list:
    """Lista processos ativos (somente leitura)."""
    processes = []
    if not HAS_PSUTIL:
        return [{"error": "psutil não está instalado. Execute: pip install psutil"}]

    for proc in psutil.process_iter(
        ["pid", "name", "exe", "cpu_percent", "memory_percent", "create_time", "status"]
    ):
        try:
            info = proc.info
            name = info.get("name") or ""
            exe = info.get("exe") or ""
            suspicious = is_suspicious_name(name) or is_suspicious_name(exe)
            processes.append({
                "pid": info.get("pid"),
                "name": name,
                "exe": exe,
                "cpu_percent": round(info.get("cpu_percent") or 0.0, 1),
                "memory_percent": round(info.get("memory_percent") or 0.0, 2),
                "status": info.get("status") or "",
                "suspicious": suspicious,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue
    # Ordena suspeitos primeiro, depois por CPU
    processes.sort(key=lambda x: (not x.get("suspicious", False), -(x.get("cpu_percent") or 0)))
    return processes


def get_startup_programs() -> list:
    """Lê programas de inicialização via Registro (somente leitura)."""
    startups = []
    if not HAS_WINREG:
        return [{"error": "winreg não disponível (só Windows)"}]

    # Chaves comuns de Run
    run_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]

    for hive, key_path in run_keys:
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        suspicious = is_suspicious_name(name) or is_suspicious_text(str(value))
                        startups.append({
                            "name": name,
                            "command": str(value),
                            "location": f"{'HKCU' if hive == winreg.HKEY_CURRENT_USER else 'HKLM'}\\{key_path}",
                            "type": "Registry Run",
                            "suspicious": suspicious,
                        })
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            continue
        except PermissionError:
            startups.append({"error": f"Sem permissão para ler: {key_path}"})
        except Exception as e:
            startups.append({"error": f"Erro em {key_path}: {e}"})
    return startups


def get_startup_folders() -> list:
    """Verifica pastas Startup (somente listagem)."""
    items = []
    folders = []

    appdata = os.environ.get("APPDATA")
    programdata = os.environ.get("PROGRAMDATA")

    if appdata:
        folders.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup")
    if programdata:
        folders.append(Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup")

    for folder in folders:
        if not folder.exists():
            items.append({"path": str(folder), "status": "não existe", "suspicious": False})
            continue
        try:
            for entry in folder.iterdir():
                name = entry.name
                suspicious = is_suspicious_name(name)
                items.append({
                    "name": name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "location": str(folder),
                    "type": "Startup Folder",
                    "suspicious": suspicious,
                })
        except PermissionError:
            items.append({"path": str(folder), "error": "Sem permissão", "suspicious": False})
        except Exception as e:
            items.append({"path": str(folder), "error": str(e), "suspicious": False})
    return items


def scan_appdata_suspicious() -> list:
    """Procura arquivos/pastas com nomes suspeitos em AppData (somente leitura, limitado)."""
    found = []
    roots = []
    for env in ("APPDATA", "LOCALAPPDATA"):
        val = os.environ.get(env)
        if val:
            roots.append(Path(val))
            # Temp dentro de LocalAppData
            if env == "LOCALAPPDATA":
                roots.append(Path(val) / "Temp")

    # Limita profundidade e quantidade para não travar
    max_files = 5000
    count = 0

    for root in roots:
        if not root.exists():
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                # Evita pastas muito profundas ou sensíveis
                depth = Path(dirpath).relative_to(root).parts
                if len(depth) > 4:
                    dirnames.clear()
                    continue

                for d in list(dirnames):
                    if is_suspicious_name(d):
                        found.append({
                            "type": "folder",
                            "name": d,
                            "path": str(Path(dirpath) / d),
                            "root": str(root),
                            "suspicious": True,
                        })
                for f in filenames:
                    count += 1
                    if count > max_files:
                        found.append({"note": f"Limite de {max_files} arquivos atingido em {root}"})
                        return found
                    if is_suspicious_name(f):
                        found.append({
                            "type": "file",
                            "name": f,
                            "path": str(Path(dirpath) / f),
                            "root": str(root),
                            "suspicious": True,
                        })
        except PermissionError:
            found.append({"error": f"Sem permissão em {root}"})
        except Exception as e:
            found.append({"error": f"Erro em {root}: {e}"})
    return found


def get_windows_services() -> list:
    """Lista serviços via psutil ou sc (somente leitura)."""
    services = []
    if HAS_PSUTIL:
        try:
            for s in psutil.win_service_iter():
                try:
                    info = s.as_dict()
                    name = info.get("name") or ""
                    display = info.get("display_name") or ""
                    binpath = info.get("binpath") or ""
                    suspicious = (
                        is_suspicious_name(name)
                        or is_suspicious_name(display)
                        or is_suspicious_text(binpath)
                    )
                    services.append({
                        "name": name,
                        "display_name": display,
                        "status": info.get("status"),
                        "start_type": info.get("start_type"),
                        "binpath": binpath,
                        "suspicious": suspicious,
                    })
                except Exception:
                    continue
            services.sort(key=lambda x: (not x.get("suspicious", False), x.get("name", "")))
            return services
        except Exception as e:
            services.append({"error": f"psutil.win_service_iter falhou: {e}"})

    # Fallback com sc query (somente leitura)
    try:
        result = subprocess.run(
            ["sc", "query", "type=", "service", "state=", "all"],
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode == 0:
            current = {}
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("SERVICE_NAME:"):
                    if current:
                        services.append(current)
                    name = line.split(":", 1)[1].strip()
                    current = {
                        "name": name,
                        "display_name": "",
                        "status": "",
                        "suspicious": is_suspicious_name(name),
                    }
                elif line.startswith("DISPLAY_NAME:"):
                    current["display_name"] = line.split(":", 1)[1].strip()
                    if is_suspicious_name(current["display_name"]):
                        current["suspicious"] = True
                elif line.startswith("STATE"):
                    current["status"] = line.split(":", 1)[1].strip() if ":" in line else line
            if current:
                services.append(current)
    except Exception as e:
        services.append({"error": f"Fallback sc query falhou: {e}"})
    return services


def get_scheduled_tasks() -> list:
    """Lista tarefas agendadas via schtasks (somente leitura)."""
    tasks = []
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST", "/v"],
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0:
            tasks.append({"error": f"schtasks retornou código {result.returncode}"})
            return tasks

        current = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current and current.get("task_name"):
                    tasks.append(current)
                current = {}
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip()
                if "taskname" in key or "nome da tarefa" in key:
                    current["task_name"] = val
                elif "task to run" in key or "executar" in key or "task to run" in key:
                    current["command"] = val
                elif "author" in key or "autor" in key:
                    current["author"] = val
                elif "status" in key:
                    current["status"] = val
                elif "schedule type" in key or "tipo de agendamento" in key:
                    current["schedule"] = val

        if current and current.get("task_name"):
            tasks.append(current)

        for t in tasks:
            name = t.get("task_name", "")
            cmd = t.get("command", "")
            t["suspicious"] = is_suspicious_name(name) or is_suspicious_text(cmd)

        tasks.sort(key=lambda x: (not x.get("suspicious", False), x.get("task_name", "")))
    except FileNotFoundError:
        tasks.append({"error": "schtasks não encontrado"})
    except Exception as e:
        tasks.append({"error": f"Erro ao listar tarefas: {e}"})
    return tasks


def get_network_connections() -> list:
    """Lista conexões de rede (somente leitura)."""
    conns = []
    if not HAS_PSUTIL:
        return [{"error": "psutil necessário para conexões de rede"}]

    try:
        for c in psutil.net_connections(kind="inet"):
            try:
                pid = c.pid
                proc_name = ""
                if pid:
                    try:
                        p = psutil.Process(pid)
                        proc_name = p.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_name = "?"
                laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""
                raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ""
                suspicious = is_suspicious_name(proc_name)
                conns.append({
                    "pid": pid,
                    "process": proc_name,
                    "local": laddr,
                    "remote": raddr,
                    "status": c.status,
                    "type": "TCP" if c.type == socket.SOCK_STREAM else "UDP",
                    "suspicious": suspicious,
                })
            except Exception:
                continue
        conns.sort(key=lambda x: (not x.get("suspicious", False), x.get("process", "")))
    except Exception as e:
        conns.append({"error": str(e)})
    return conns


# ============================================================
# Interface Gráfica
# ============================================================

class MinerScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner de Mineradores - Modo Somente Leitura")
        self.root.geometry("1100x750")
        self.root.state('zoomed')
        self.root.minsize(900, 600)

        # Dados coletados
        self.data = {
            "system": {},
            "processes": [],
            "startup_reg": [],
            "startup_folders": [],
            "appdata": [],
            "services": [],
            "tasks": [],
            "connections": [],
            "scan_time": None,
            "suspicious_count": 0,
        }

        # Mapeamento: nome_do_atributo_da_tree -> índice da coluna que contém o caminho do arquivo
        self._path_columns = {
            "tree_proc": 4,      # coluna "exe"
            "tree_startup": 3,   # coluna "command" (prioridade sobre "location")
            "tree_appdata": 2,   # coluna "path"
            "tree_svc": 4,       # coluna "binpath"
            "tree_tasks": 2,     # coluna "command"
            # tree_net (conexões) não tem caminho de arquivo — ignorado
        }

        self._build_ui()
        self._check_dependencies()

    def _check_dependencies(self):
        if not HAS_PSUTIL:
            messagebox.showwarning(
                "Dependência faltando",
                "A biblioteca 'psutil' não está instalada.\n\n"
                "Execute no terminal:\n  pip install psutil\n\n"
                "Algumas funções ficarão limitadas sem ela."
            )
        if platform.system() != "Windows":
            messagebox.showwarning(
                "Sistema operacional",
                "Este scanner foi projetado para Windows.\n"
                "Algumas funções podem não funcionar corretamente."
            )

    def _build_ui(self):
        # Frame superior - botões
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(
            top,
            text="Scanner de Diagnóstico de Detecção de Mineradores de Criptomoedas(100% Somente Leitura)",
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 20))

        self.btn_scan = ttk.Button(top, text="▶ Executar Scan Completo", command=self.start_full_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=4)

        self.btn_report = ttk.Button(top, text="📄 Gerar Relatório .txt", command=self.generate_report, state=tk.DISABLED)
        self.btn_report.pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Limpar", command=self.clear_results).pack(side=tk.LEFT, padx=4)

        # ========== BARRA DE PROGRESSO DETERMINATE (0 a 100) ==========
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100, value=0)
        self.progress.pack(fill=tk.X, padx=8, pady=(0, 4))

        self.status_var = tk.StringVar(value="Pronto. Clique em 'Executar Scan Completo'.")
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X, padx=8)

        # Notebook (abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Aba Sistema
        self.tab_system = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_system, text="Sistema")
        self.txt_system = scrolledtext.ScrolledText(self.tab_system, wrap=tk.WORD, font=("Consolas", 10))
        self.txt_system.pack(fill=tk.BOTH, expand=True)

        # Aba Processos
        self.tab_proc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_proc, text="Processos")
        self._build_tree(
            self.tab_proc,
            "tree_proc",
            columns=("pid", "name", "cpu", "mem", "exe", "suspicious"),
            headings=("PID", "Nome", "CPU %", "Mem %", "Caminho", "Suspeito?"),
            widths=(70, 200, 60, 60, 700, 80),
        )

        # Aba Inicialização
        self.tab_startup = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_startup, text="Inicialização")
        self._build_tree(
            self.tab_startup,
            "tree_startup",
            columns=("name", "type", "location", "command", "suspicious"),
            headings=("Nome", "Tipo", "Local", "Comando/Caminho", "Suspeito?"),
            widths=(200, 120, 500, 650, 80),
        )

        # Aba AppData / Temp
        self.tab_appdata = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_appdata, text="AppData / Temp")
        self._build_tree(
            self.tab_appdata,
            "tree_appdata",
            columns=("type", "name", "path", "suspicious"),
            headings=("Tipo", "Nome", "Caminho", "Suspeito?"),
            widths=(200, 600, 650, 80),
        )

        # Aba Serviços
        self.tab_svc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_svc, text="Serviços")
        self._build_tree(
            self.tab_svc,
            "tree_svc",
            columns=("name", "display", "status", "start", "binpath", "suspicious"),
            headings=("Nome", "Nome de Exibição", "Status", "Tipo Início", "Caminho", "Suspeito?"),
            widths=(350, 600, 80, 90, 1300, 80),
        )

        # Aba Tarefas
        self.tab_tasks = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tasks, text="Tarefas Agendadas")
        self._build_tree(
            self.tab_tasks,
            "tree_tasks",
            columns=("name", "status", "command", "suspicious"),
            headings=("Nome da Tarefa", "Status", "Comando", "Suspeito?"),
            widths=(820, 200, 650, 80),
        )

        # Aba Rede
        self.tab_net = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_net, text="Conexões de Rede")
        self._build_tree(
            self.tab_net,
            "tree_net",
            columns=("pid", "process", "local", "remote", "status", "type", "suspicious"),
            headings=("PID", "Processo", "Local", "Remoto", "Estado", "Tipo", "Suspeito?"),
            widths=(60, 120, 250, 250, 100, 50, 80),
        )

        # Aba Resumo
        self.tab_summary = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_summary, text="Resumo / Suspeitos")
        self.txt_summary = scrolledtext.ScrolledText(self.tab_summary, wrap=tk.WORD, font=("Consolas", 10))
        self.txt_summary.pack(fill=tk.BOTH, expand=True)

        # === BIND DE DUPLO CLIQUE PARA ABRIR CAMINHOS NO EXPLORER ===
        for attr_name in self._path_columns:
            tree = getattr(self, attr_name, None)
            if tree:
                tree.bind("<Double-1>", self._on_tree_double_click)

    def _build_tree(self, parent, attr_name, columns, headings, widths):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        for col, head, w in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, minwidth=40)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Tag para suspeitos
        tree.tag_configure("suspicious", background="#ffcccc", foreground="#8b0000")

        setattr(self, attr_name, tree)

    # =================================================================
    # NOVO MÉTODO: Abre o caminho no Explorer ao dar duplo clique
    # =================================================================
    def _on_tree_double_click(self, event):
        """Abre o Windows Explorer na pasta do arquivo, com o arquivo selecionado."""
        tree = event.widget

        # Descobre qual tree disparou o evento e qual coluna contém o caminho
        attr_name = None
        col_idx = None
        for name, idx in self._path_columns.items():
            if getattr(self, name, None) is tree:
                attr_name = name
                col_idx = idx
                break
        if attr_name is None:
            return

        # Pega o item selecionado
        selection = tree.selection()
        if not selection:
            return

        item = tree.item(selection[0])
        values = item.get("values", [])
        if col_idx >= len(values):
            return

        path = values[col_idx]
        if not path or not isinstance(path, str):
            return

        # Limpa: remove aspas e espaços extras
        path = path.strip().strip('"').strip("'")

        # Se o caminho não existir, tenta pegar só o primeiro token (ex: comando + argumentos)
        if not os.path.exists(path):
            parts = path.split()
            if parts:
                candidate = parts[0].strip().strip('"').strip("'")
                if os.path.exists(candidate):
                    path = candidate

        # Tenta abrir
        try:
            if os.path.isdir(path):
                # Se for uma pasta, abre diretamente
                os.startfile(path)
            elif os.path.isfile(path):
                # Se for um arquivo, abre o Explorer com ele selecionado
                subprocess.Popen(
                    ["explorer", "/select,", os.path.normpath(path)],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
            else:
                messagebox.showinfo(
                    "Caminho não encontrado",
                    f"O caminho não existe no sistema:\n{path}",
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o Explorer:\n{e}")

    def clear_results(self):
        self.txt_system.delete("1.0", tk.END)
        self.txt_summary.delete("1.0", tk.END)
        for name in ("tree_proc", "tree_startup", "tree_appdata", "tree_svc", "tree_tasks", "tree_net"):
            tree = getattr(self, name, None)
            if tree:
                for item in tree.get_children():
                    tree.delete(item)
        self.progress["value"] = 0
        self.btn_report.config(state=tk.DISABLED)
        self.status_var.set("Resultados limpos. Pronto para novo scan.")
        self.data = {k: ([] if isinstance(v, list) else {}) for k, v in self.data.items()}
        self.data["scan_time"] = None
        self.data["suspicious_count"] = 0

    def start_full_scan(self):
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_report.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.status_var.set("Escaneando... (somente leitura)")
        self.clear_results()
        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self):
        try:
            
            self.data["scan_time"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # 1. Sistema (0 → 10)
            self._update_status(0, "Coletando informações do sistema...")
            self.data["system"] = get_system_info()
            self.root.after(0, self._fill_system)

            # 2. Processos (10 → 25)
            self._update_status(10, "Listando processos...")
            self.data["processes"] = get_running_processes()
            self.root.after(0, self._fill_processes)

            # 3. Inicialização (25 → 35)
            self._update_status(25, "Verificando inicialização...")
            self.data["startup_reg"] = get_startup_programs()
            self.data["startup_folders"] = get_startup_folders()
            self.root.after(0, self._fill_startup)

            # 4. AppData / Temp (35 → 55)
            self._update_status(35, "Examinando AppData e Temp (pode demorar)...")
            self.data["appdata"] = scan_appdata_suspicious()
            self.root.after(0, self._fill_appdata)

            # 5. Serviços (55 → 65)
            self._update_status(55, "Listando serviços...")
            self.data["services"] = get_windows_services()
            self.root.after(0, self._fill_services)

            # 6. Tarefas (65 → 80)
            self._update_status(65, "Listando tarefas agendadas...")
            self.data["tasks"] = get_scheduled_tasks()
            self.root.after(0, self._fill_tasks)

            # 7. Rede (80 → 90)
            self._update_status(80, "Listando conexões de rede...")
            self.data["connections"] = get_network_connections()
            self.root.after(0, self._fill_network)

            # 8. Resumo (90 → 100)
            self._update_status(90, "Gerando resumo...")
            self.root.after(0, self._fill_summary)
            self.root.after(0, lambda: self._set_progress(100))
            self.root.after(0, self._scan_finished)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha no scan:\n{e}"))
            self.root.after(0, self._scan_finished)

    def _set_progress(self, value):
        """Define o valor da barra de progresso (thread-safe via after)."""
        self.progress["value"] = value

    def _update_status(self, progress_value, msg):
        """Atualiza barra + texto de status (chamado de thread secundária)."""
        self.root.after(0, lambda: self._set_progress(progress_value))
        self.root.after(0, lambda: self.status_var.set(msg))

    def _scan_finished(self):
        self.progress["value"] = 100
        self.btn_scan.config(state=tk.NORMAL)
        self.btn_report.config(state=tk.NORMAL)
        count = self.data.get("suspicious_count", 0)
        self.status_var.set(
            f"Scan concluído em {self.data.get('scan_time')}. "
            f"Itens suspeitos encontrados: {count}. Gere o relatório se desejar."
        )

    def _fill_system(self):
        s = self.data["system"]
        text = f"""=== INFORMAÇÕES DO SISTEMA ===
Data/Hora do Scan : {self.data.get('scan_time')}
Nome do Computador: {s.get('computer_name')}
Usuário atual     : {s.get('user')}
Sistema Operacional: {s.get('os')} {s.get('os_release')} ({s.get('os_version')})
Arquitetura       : {s.get('architecture')}
Processador       : {s.get('processor')}
CPU (lógicos)     : {s.get('cpu_count_logical', 'N/A')}
CPU (físicos)     : {s.get('cpu_count_physical', 'N/A')}
Uso de CPU        : {s.get('cpu_percent', 'N/A')} %
RAM Total         : {s.get('ram_total_gb')} GB
RAM Disponível    : {s.get('ram_available_gb', 'N/A')} GB
Uso de RAM        : {s.get('ram_percent', 'N/A')} %
Disco C: Total    : {s.get('disk_total_gb')} GB
Disco C: Livre    : {s.get('disk_free_gb', 'N/A')} GB
Uso do Disco      : {s.get('disk_percent', 'N/A')} %
Boot Time         : {s.get('boot_time', 'N/A')}
Python            : {s.get('python_version')}
"""
        self.txt_system.delete("1.0", tk.END)
        self.txt_system.insert(tk.END, text)

    def _fill_processes(self):
        tree = self.tree_proc
        for item in tree.get_children():
            tree.delete(item)
        for p in self.data["processes"]:
            if "error" in p:
                tree.insert("", tk.END, values=("", p["error"], "", "", "", ""))
                continue
            tags = ("suspicious",) if p.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    p.get("pid"),
                    p.get("name"),
                    p.get("cpu_percent"),
                    p.get("memory_percent"),
                    p.get("exe"),
                    "SIM" if p.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_startup(self):
        tree = self.tree_startup
        for item in tree.get_children():
            tree.delete(item)
        for item in self.data["startup_reg"] + self.data["startup_folders"]:
            if "error" in item:
                tree.insert("", tk.END, values=(item.get("error"), "", "", "", ""))
                continue
            tags = ("suspicious",) if item.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    item.get("name", ""),
                    item.get("type", ""),
                    item.get("location", item.get("path", "")),
                    item.get("command", item.get("path", "")),
                    "SIM" if item.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_appdata(self):
        tree = self.tree_appdata
        for item in tree.get_children():
            tree.delete(item)
        for item in self.data["appdata"]:
            if "error" in item or "note" in item:
                tree.insert("", tk.END, values=("", item.get("error") or item.get("note"), "", ""))
                continue
            tags = ("suspicious",) if item.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    item.get("type", ""),
                    item.get("name", ""),
                    item.get("path", ""),
                    "SIM" if item.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_services(self):
        tree = self.tree_svc
        for item in tree.get_children():
            tree.delete(item)
        for s in self.data["services"]:
            if "error" in s:
                tree.insert("", tk.END, values=(s["error"], "", "", "", "", ""))
                continue
            tags = ("suspicious",) if s.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    s.get("name"),
                    s.get("display_name"),
                    s.get("status"),
                    s.get("start_type", ""),
                    s.get("binpath", ""),
                    "SIM" if s.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_tasks(self):
        tree = self.tree_tasks
        for item in tree.get_children():
            tree.delete(item)
        for t in self.data["tasks"]:
            if "error" in t:
                tree.insert("", tk.END, values=(t["error"], "", "", ""))
                continue
            tags = ("suspicious",) if t.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    t.get("task_name", ""),
                    t.get("status", ""),
                    t.get("command", ""),
                    "SIM" if t.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_network(self):
        tree = self.tree_net
        for item in tree.get_children():
            tree.delete(item)
        for c in self.data["connections"]:
            if "error" in c:
                tree.insert("", tk.END, values=("", c["error"], "", "", "", "", ""))
                continue
            tags = ("suspicious",) if c.get("suspicious") else ()
            tree.insert(
                "",
                tk.END,
                values=(
                    c.get("pid"),
                    c.get("process"),
                    c.get("local"),
                    c.get("remote"),
                    c.get("status"),
                    c.get("type"),
                    "SIM" if c.get("suspicious") else "",
                ),
                tags=tags,
            )

    def _fill_summary(self):
        count = 0
        lines = []
        lines.append("=" * 60)
        lines.append("RESUMO DE ITENS SUSPEITOS")
        lines.append(f"Scan realizado em: {self.data.get('scan_time')}")
        lines.append("=" * 60)

        # Processos
        sus_proc = [p for p in self.data["processes"] if p.get("suspicious")]
        lines.append(f"\n[PROCESSOS SUSPEITOS] ({len(sus_proc)})")
        for p in sus_proc:
            lines.append(f"  PID {p.get('pid')}: {p.get('name')} | CPU {p.get('cpu_percent')}% | {p.get('exe')}")
            count += 1

        # Startup
        sus_start = [x for x in self.data["startup_reg"] + self.data["startup_folders"] if x.get("suspicious")]
        lines.append(f"\n[INICIALIZAÇÃO SUSPEITA] ({len(sus_start)})")
        for x in sus_start:
            lines.append(f"  {x.get('name')} | {x.get('type')} | {x.get('command') or x.get('path')}")
            count += 1

        # AppData
        sus_app = [x for x in self.data["appdata"] if x.get("suspicious")]
        lines.append(f"\n[ARQUIVOS/PASTAS SUSPEITOS EM APPDATA/TEMP] ({len(sus_app)})")
        for x in sus_app:
            lines.append(f"  [{x.get('type')}] {x.get('name')} → {x.get('path')}")
            count += 1

        # Serviços
        sus_svc = [s for s in self.data["services"] if s.get("suspicious")]
        lines.append(f"\n[SERVIÇOS SUSPEITOS] ({len(sus_svc)})")
        for s in sus_svc:
            lines.append(f"  {s.get('name')} ({s.get('display_name')}) | {s.get('binpath')}")
            count += 1

        # Tarefas
        sus_tasks = [t for t in self.data["tasks"] if t.get("suspicious")]
        lines.append(f"\n[TAREFAS AGENDADAS SUSPEITAS] ({len(sus_tasks)})")
        for t in sus_tasks:
            lines.append(f"  {t.get('task_name')} | {t.get('command')}")
            count += 1

        # Rede
        sus_net = [c for c in self.data["connections"] if c.get("suspicious")]
        lines.append(f"\n[CONEXÕES DE REDE DE PROCESSOS SUSPEITOS] ({len(sus_net)})")
        for c in sus_net:
            lines.append(f"  {c.get('process')} (PID {c.get('pid')}) → {c.get('remote')} [{c.get('status')}]")
            count += 1

        lines.append("\n" + "=" * 60)
        lines.append(f"TOTAL DE ITENS CONSIDERADOS SUSPEITOS: {count}")
        lines.append("=" * 60)
        lines.append(
            "\nAVISO: Este scanner apenas identifica possíveis indícios.\n"
            "Não realiza nenhuma alteração no sistema.\n"
            "Analise cuidadosamente antes de tomar qualquer ação."
        )

        self.data["suspicious_count"] = count
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(tk.END, "\n".join(lines))

    def generate_report(self):
        if not self.data.get("scan_time"):
            messagebox.showinfo("Relatório", "Execute o scan primeiro.")
            return

        # ---- Escolha do formato ----
        escolha = messagebox.askyesnocancel(
            "Formato do relatório",
            "Deseja salvar em formato HTML (mais bonito, com cores)?\n\n"
            "  Sim    → Salvar como .HTML\n"
            "  Não    → Salvar como .TXT (texto simples)\n"
            "  Cancel → Voltar",
        )
        if escolha is None:  # Cancelou
            return
        formato_html = escolha  # True = HTML, False = TXT

        ext = ".html" if formato_html else ".txt"
        default_name = f"relatorio_minerador_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[
                (f"Arquivo {'HTML' if formato_html else 'Texto'}", f"*{ext}"),
                ("Todos os arquivos", "*.*"),
            ],
            initialfile=default_name,
            title="Salvar relatório",
        )
        if not path:
            return

        # ---- Coleta dados para o relatório ----
        total_processos = len([p for p in self.data["processes"] if "error" not in p])
        total_startup = len([x for x in self.data["startup_reg"] + self.data["startup_folders"] if "error" not in x])
        total_servicos = len([s for s in self.data["services"] if "error" not in s])
        total_tarefas = len([t for t in self.data["tasks"] if "error" not in t])
        total_conexoes = len([c for c in self.data["connections"] if "error" not in c])

        contagens = {
            "Processos": sum(1 for p in self.data["processes"] if p.get("suspicious")),
            "Inicialização": sum(1 for x in self.data["startup_reg"] + self.data["startup_folders"] if x.get("suspicious")),
            "AppData/Temp": sum(1 for x in self.data["appdata"] if x.get("suspicious")),
            "Serviços": sum(1 for s in self.data["services"] if s.get("suspicious")),
            "Tarefas": sum(1 for t in self.data["tasks"] if t.get("suspicious")),
            "Conexões Rede": sum(1 for c in self.data["connections"] if c.get("suspicious")),
        }
        total_suspeitos = sum(contagens.values())
        s = self.data["system"]

        # ====================================================================
        # GERAR CONTEÚDO
        # ====================================================================
        try:
            if formato_html:
                conteudo = self._gerar_html(s, contagens, total_suspeitos,
                                            total_processos, total_startup,
                                            total_servicos, total_tarefas,
                                            total_conexoes)
            else:
                conteudo = self._gerar_txt_melhorado(s, contagens, total_suspeitos,
                                                     total_processos, total_startup,
                                                     total_servicos, total_tarefas,
                                                     total_conexoes)

            with open(path, "w", encoding="utf-8") as f:
                f.write(conteudo)

            # Pergunta se quer abrir o arquivo agora
            if messagebox.askyesno("Relatório salvo",
                                   f"Relatório salvo em:\n{path}\n\nDeseja abri-lo agora?"):
                os.startfile(path)

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o relatório:\n{e}")

    # =====================================================================
    # GERADOR TXT MELHORADO
    # =====================================================================
    def _gerar_txt_melhorado(self, s, contagens, total_suspeitos,
                              total_processos, total_startup,
                              total_servicos, total_tarefas,
                              total_conexoes):
        """Gera relatório em TXT com tabelas e organização visual."""
        W = 78  # largura da página
        linhas = []
        L = linhas.append

        def titulo(texto, char="="):
            resto = W - len(texto) - 4
            if resto < 4:
                L(f"{char * 3} {texto} {char * 3}")
            else:
                L(f"{char * 3} {texto} {char * resto}")
            L("")

        def subtitulo(texto, char="-"):
            L(f"  {char * 2} {texto}")
            L("")

        def tabela(headers, rows):
            """Tabela em texto puro com alinhamento."""
            if not rows:
                L("  (nenhum)")
                L("")
                return
            n = len(headers)
            # Calcula larguras
            largs = []
            for i in range(n):
                col_data = [str(r[i]) if i < len(r) else "" for r in rows] + [headers[i]]
                largs.append(max(len(c) for c in col_data) + 2)
            # Se passar da largura, reduz a última coluna
            total_larg = sum(largs) + (n * 3) + 1
            if total_larg > W:
                largs[-1] -= (total_larg - W)
                if largs[-1] < 10:
                    largs[-1] = 10
            # Linha horizontal
            sep_line = "+" + "+".join("-" * w for w in largs) + "+"
            # Cabeçalho
            L(sep_line)
            L("|" + "|".join(h.center(w) for h, w in zip(headers, largs)) + "|")
            L(sep_line)
            for r in rows:
                vals = [str(r[i]) if i < len(r) else "" for i in range(n)]
                # Trunca valores se necessário
                vals = [v[:w] if len(v) > w else v for v, w in zip(vals, largs)]
                L("|" + "|".join(v.ljust(w) for v, w in zip(vals, largs)) + "|")
            L(sep_line)
            L("")

        # ========== CABEÇALHO ==========
        L("=" * W)
        L("   RELATÓRIO DO SCANNER DE MINERADORES DE CRIPTOMOEDAS")
        L(f"   {self.data['scan_time']}")
        L("=" * W)
        L("")
        L(f"  Computador : {s.get('computer_name', '?')}")
        L(f"  Usuário    : {s.get('user', '?')}")
        L(f"  SO         : {s.get('os', '?')} {s.get('os_release', '?')}")
        L(f"  Modo       : 100% SOMENTE LEITURA   (nenhuma alteração feita)")
        L("=" * W)
        L("")

        # ========== RESUMO EXECUTIVO ==========
        titulo("RESUMO EXECUTIVO")
        resume_rows = [
            ["Processos em execução", str(total_processos), str(contagens["Processos"])],
            ["Programas de inicialização", str(total_startup), str(contagens["Inicialização"])],
            ["Arquivos em AppData/Temp", str(len(self.data["appdata"])), str(contagens["AppData/Temp"])],
            ["Serviços do Windows", str(total_servicos), str(contagens["Serviços"])],
            ["Tarefas agendadas", str(total_tarefas), str(contagens["Tarefas"])],
            ["Conexões de rede", str(total_conexoes), str(contagens["Conexões Rede"])],
        ]
        tabela(["Categoria", "Total", "Suspeitos"], resume_rows)
        L(f"  >>> TOTAL DE ITENS COM INDÍCIO DE MINERAÇÃO: {total_suspeitos}")
        L("")
        L("  AVISO: Itens 'suspeitos' são identificados por nome/palavra-chave.")
        L("  Podem ocorrer falsos-positivos. Analise cada caso antes de agir.")
        L("")

        # ========== SISTEMA ==========
        titulo("INFORMAÇÕES DO SISTEMA")
        sys_rows = [
            ["Nome", s.get("computer_name", "N/A")],
            ["Usuário", s.get("user", "N/A")],
            ["Sistema", f"{s.get('os', 'N/A')} {s.get('os_release', 'N/A')} (v{s.get('os_version', 'N/A')})"],
            ["Arquitetura", s.get("architecture", "N/A")],
            ["Processador", s.get("processor", "N/A")],
            ["CPUs (lóg./fís.)", f"{s.get('cpu_count_logical', '?')} / {s.get('cpu_count_physical', '?')}"],
            ["CPU em uso", f"{s.get('cpu_percent', 'N/A')}%"],
            ["RAM", f"{s.get('ram_total_gb', 'N/A')} GB (livre: {s.get('ram_available_gb', 'N/A')} GB, {s.get('ram_percent', 'N/A')}% usado)"],
            ["Disco C:", f"{s.get('disk_total_gb', 'N/A')} GB (livre: {s.get('disk_free_gb', 'N/A')} GB, {s.get('disk_percent', 'N/A')}% usado)"],
            ["Boot", s.get('boot_time', 'N/A')],
        ]
        tabela(["Propriedade", "Valor"], sys_rows)

        # ========== PROCESSOS ==========
        titulo(f"PROCESSOS ({total_processos} total, {contagens['Processos']} suspeitos)")
        if contagens["Processos"] > 0:
            subtitulo("Suspeitos:")
            for p in self.data["processes"]:
                if p.get("suspicious"):
                    L(f"   PID {p.get('pid'):>6}  {p.get('name',''):<20}  CPU {p.get('cpu_percent',0):>5}%  MEM {p.get('memory_percent',0):>5}%")
                    L(f"        {p.get('exe','')}")
            L("")

        # Top consumidores de CPU (mesmo não suspeitos)
        top_cpu = sorted(
            [p for p in self.data["processes"] if "error" not in p],
            key=lambda x: x.get("cpu_percent", 0) or 0,
            reverse=True
        )[:10]
        subtitulo("Top 10 processos que mais usam CPU:")
        top_rows = []
        for p in top_cpu:
            sus = " [!]" if p.get("suspicious") else ""
            top_rows.append([
                str(p.get("pid", "")),
                p.get("name", ""),
                f"{p.get('cpu_percent', 0)}%",
                f"{p.get('memory_percent', 0)}%",
                sus,
            ])
        tabela(["PID", "Nome", "CPU", "MEM", ""], top_rows)

        # ========== INICIALIZAÇÃO ==========
        total_start_items = len(self.data["startup_reg"]) + len(self.data["startup_folders"])
        titulo(f"INICIALIZAÇÃO ({total_start_items} itens, {contagens['Inicialização']} suspeitos)")
        if contagens["Inicialização"] > 0:
            for item in self.data["startup_reg"] + self.data["startup_folders"]:
                if item.get("suspicious") and "error" not in item:
                    L(f"   [!] {item.get('name',''):<25} | {item.get('type',''):<15} | {item.get('command') or item.get('path','')}")
            L("")

        # ========== APPDATA ==========
        titulo(f"APPDATA / TEMP ({len(self.data['appdata'])} itens escaneados, {contagens['AppData/Temp']} suspeitos)")
        if contagens["AppData/Temp"] > 0:
            for item in self.data["appdata"]:
                if item.get("suspicious") and "error" not in item and "note" not in item:
                    L(f"   [{item.get('type',''):>6}] {item.get('name',''):<25} → {item.get('path','')}")
            L("")

        # ========== SERVIÇOS ==========
        titulo(f"SERVIÇOS ({total_servicos} serviços, {contagens['Serviços']} suspeitos)")
        if contagens["Serviços"] > 0:
            for srv in self.data["services"]:
                if srv.get("suspicious") and "error" not in srv:
                    L(f"   [!] {srv.get('name',''):<30} | {srv.get('display_name',''):<25} | {srv.get('binpath','')}")
            L("")

        # ========== TAREFAS ==========
        titulo(f"TAREFAS AGENDADAS ({total_tarefas} tarefas, {contagens['Tarefas']} suspeitas)")
        if contagens["Tarefas"] > 0:
            for tsk in self.data["tasks"]:
                if tsk.get("suspicious") and "error" not in tsk:
                    L(f"   [!] {tsk.get('task_name',''):<40} | {tsk.get('command','')}")
            L("")

        # ========== REDE ==========
        titulo(f"CONEXÕES DE REDE ({total_conexoes} conexões, {contagens['Conexões Rede']} suspeitas)")
        if contagens["Conexões Rede"] > 0:
            for c in self.data["connections"]:
                if c.get("suspicious") and "error" not in c:
                    L(f"   [!] {c.get('process',''):<20} (PID {c.get('pid','')})  {c.get('local',''):<22} → {c.get('remote',''):<22}  {c.get('status','')}")
            L("")

        # ========== RODAPÉ ==========
        L("=" * W)
        L(f"   FIM DO RELATÓRIO — {self.data['scan_time']}")
        L(f"   Total de itens com indício suspeito: {total_suspeitos}")
        L("=" * W)
        L("   Operação 100% somente leitura.")
        L("   Nenhum arquivo foi modificado, nenhum processo encerrado.")
        L("")
        L("   Revise os itens marcados com [!] e, se confirmado,")
        L("   utilize ferramentas de remoção apropriadas.")
        L("=" * W)

        return "\n".join(linhas)

    # =====================================================================
    # GERADOR HTML (MUITO MAIS BONITO)
    # =====================================================================
    def _gerar_html(self, s, contagens, total_suspeitos,
                     total_processos, total_startup,
                     total_servicos, total_tarefas,
                     total_conexoes):
        """Gera relatório em HTML com TODOS os itens listados, suspeitos destacados."""

        cor_alta = "#dc3545"
        cor_media = "#fd7e14"
        cor_baixa = "#ffc107"
        cor_ok = "#28a745"
        cor_fundo = "#1e1e2e"
        cor_texto = "#cdd6f4"
        cor_tabela = "#313244"
        cor_susp = "#4a1a1a"

        def esc(val):
            if val is None:
                return ""
            return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def sev_label(suspicious, cpu=0):
            if not suspicious:
                return ""
            if cpu and cpu > 20:
                return f'<span style="background:{cor_alta};color:#fff;padding:1px 8px;border-radius:8px;font-size:0.75em">🔴 ALTO</span>'
            elif cpu and cpu > 5:
                return f'<span style="background:{cor_media};color:#fff;padding:1px 8px;border-radius:8px;font-size:0.75em">🟠 MÉDIO</span>'
            else:
                return f'<span style="background:{cor_baixa};color:#000;padding:1px 8px;border-radius:8px;font-size:0.75em">🟡 BAIXO</span>'

        def tabela_html(headers, rows):
            """rows: cada row é uma lista onde o ÚLTIMO elemento é True (suspeito) ou False.
               Esse último elemento NÃO é exibido, só controla o fundo."""
            if not rows:
                return '<p style="color:#888;font-style:italic">Nenhum item.</p>'
            h = "".join(f'<th>{esc(h)}</th>' for h in headers)
            r = ""
            for row in rows:
                # O último elemento é o sinalizador de suspeito
                is_susp = len(row) > 0 and row[-1] is True
                # Valores a exibir = TUDO menos o último
                vals = row[:-1]
                estilo = f' style="background:{cor_susp}"' if is_susp else ""
                r += f"<tr{estilo}>"
                for v in vals:
                    r += f"<td>{v}</td>"
                r += "</tr>"
            return f'''<table style="width:100%;border-collapse:collapse;font-size:0.85em;background:{cor_tabela};border-radius:8px;overflow:hidden">
            <thead style="background:#45475a;color:#cdd6f4"><tr>{h}</tr></thead>
            <tbody>{r}</tbody></table>'''

        # ========== MONTAGEM ==========
        partes = []

        css = f"""
        <style>
            body {{ font-family:'Segoe UI',Arial,sans-serif; background:{cor_fundo}; color:{cor_texto}; margin:20px; padding:20px; }}
            h1 {{ color:#fab387; border-bottom:2px solid #fab387; padding-bottom:8px; }}
            h2 {{ color:#a6e3a1; margin-top:30px; }}
            h3 {{ color:#89b4fa; }}
            table {{ margin:10px 0; }}
            th {{ padding:8px 12px; text-align:left; font-weight:600; }}
            td {{ padding:6px 12px; border-bottom:1px solid #45475a; }}
            tr:hover {{ background:#3a3a4e; }}
            .resumo-box {{ background:#313244; border-radius:10px; padding:15px; margin:15px 0; }}
            .resumo-item {{ display:inline-block; margin:8px 15px; text-align:center; }}
            .resumo-num {{ font-size:1.8em; font-weight:bold; }}
            .footer {{ margin-top:40px; padding-top:15px; border-top:1px solid #45475a; font-size:0.85em; color:#888; }}
        </style>
        """

        partes.append(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Relatório - Scanner Detecção de Mineradores de Criptomoedas</title>{css}</head>
<body>""")

        # ===== CABEÇALHO =====
        partes.append(f"""
<h1>🛡️ Relatório do Scanner de Detecção de Mineradores de Criptomoedas</h1>
<p><strong>Data da análise:</strong> {esc(self.data['scan_time'])}<br>
<strong>Computador:</strong> {esc(s.get('computer_name','?'))} &nbsp;|&nbsp; <strong>Usuário:</strong> {esc(s.get('user','?'))}<br>
<strong>Sistema:</strong> {esc(s.get('os','?'))} {esc(s.get('os_release','?'))} &nbsp;|&nbsp; <strong>Modo:</strong> ✅ Somente leitura</p>
""")

        # ===== RESUMO EXECUTIVO =====
        partes.append("<h2>📊 Resumo Executivo</h2>")
        partes.append(f"""<div class="resumo-box">
<div style="display:flex;flex-wrap:wrap;justify-content:space-around">""")
        cats = [
            ("Processos", contagens["Processos"], total_processos),
            ("Inicialização", contagens["Inicialização"], total_startup),
            ("AppData/Temp", contagens["AppData/Temp"], len(self.data["appdata"])),
            ("Serviços", contagens["Serviços"], total_servicos),
            ("Tarefas", contagens["Tarefas"], total_tarefas),
            ("Rede", contagens["Conexões Rede"], total_conexoes),
        ]
        for nome, sus, tot in cats:
            cor_num = cor_alta if sus > 5 else (cor_media if sus > 2 else (cor_baixa if sus > 0 else cor_ok))
            partes.append(f"""
<div class="resumo-item">
    <div style="font-size:0.8em;color:#a6adc8">{esc(nome)}</div>
    <div class="resumo-num" style="color:{cor_num}">{sus}</div>
    <div style="font-size:0.7em;color:#585b70">de {tot}</div>
</div>""")
        partes.append(f"""</div>
<div style="text-align:center;margin-top:10px;font-size:1.1em">
    <strong>Total de suspeitos: {total_suspeitos}</strong>
</div>
</div>""")
        partes.append('<p style="background:#3a1a1a;padding:10px;border-radius:8px;border-left:4px solid #dc3545">')
        partes.append("⚠️ Linhas com fundo <span style='background:#4a1a1a;padding:2px 6px;border-radius:4px'>vermelho escuro</span> indicam itens suspeitos. Falsos-positivos podem ocorrer.</p>")

        # ===== SISTEMA =====
        partes.append("<h2>💻 Sistema</h2>")
        sys_rows = [
            ["Nome do computador", esc(s.get("computer_name","N/A")), False],
            ["Usuário", esc(s.get("user","N/A")), False],
            ["Sistema Operacional", f"{esc(s.get('os','N/A'))} {esc(s.get('os_release','N/A'))} (v{esc(s.get('os_version','N/A'))})", False],
            ["Arquitetura", esc(s.get("architecture","N/A")), False],
            ["Processador", esc(s.get("processor","N/A")), False],
            ["CPUs (lógicas/físicas)", f"{s.get('cpu_count_logical','?')} / {s.get('cpu_count_physical','?')}", False],
            ["Uso da CPU", f"{s.get('cpu_percent','N/A')}%", False],
            ["RAM", f"{s.get('ram_total_gb','N/A')} GB (livre: {s.get('ram_available_gb','N/A')} GB, {s.get('ram_percent','N/A')}% usado)", False],
            ["Disco C:", f"{s.get('disk_total_gb','N/A')} GB (livre: {s.get('disk_free_gb','N/A')} GB, {s.get('disk_percent','N/A')}% usado)", False],
            ["Boot", esc(s.get('boot_time','N/A')), False],
        ]
        partes.append(tabela_html(["Propriedade", "Valor"], sys_rows))

        # ===== PROCESSOS — TODOS =====
        partes.append(f"<h2>⚙️ Processos ({total_processos} total, {contagens['Processos']} suspeitos)</h2>")
        partes.append("<p>Todos os processos em execução. Suspeitos destacados em vermelho.</p>")
        proc_rows = []
        for p in self.data["processes"]:
            if "error" in p:
                proc_rows.append([f"ERRO: {p['error']}", "", "", "", "", False])
                continue
            sus = p.get("suspicious", False)
            sev = sev_label(sus, p.get("cpu_percent", 0))
            nome = f"🚩 {esc(p.get('name',''))}" if sus else esc(p.get('name',''))
            proc_rows.append([
                esc(str(p.get("pid",""))),
                nome,
                f"{p.get('cpu_percent',0)}%",
                f"{p.get('memory_percent',0)}%",
                esc(p.get('exe','')),
                sev,
                sus,  # sinalizador (não é exibido)
            ])
        partes.append(tabela_html(["PID", "Nome", "CPU", "MEM", "Caminho", ""], proc_rows))

        # ===== INICIALIZAÇÃO — TODOS =====
        total_start_items = len(self.data["startup_reg"]) + len(self.data["startup_folders"])
        partes.append(f"<h2>🚀 Inicialização ({total_start_items} itens, {contagens['Inicialização']} suspeitos)</h2>")
        start_rows = []
        for item in self.data["startup_reg"] + self.data["startup_folders"]:
            if "error" in item:
                start_rows.append([f"ERRO: {item['error']}", "", "", "", False])
                continue
            sus = item.get("suspicious", False)
            nome = f"🚩 {esc(item.get('name',''))}" if sus else esc(item.get('name',''))
            start_rows.append([
                nome,
                esc(item.get('type','')),
                esc(item.get('location', item.get('path',''))),
                esc(item.get('command', item.get('path',''))),
                sus,
            ])
        partes.append(tabela_html(["Nome", "Tipo", "Local", "Comando/Caminho"], start_rows))

        # ===== APPDATA — TODOS =====
        partes.append(f"<h2>📁 AppData / Temp ({len(self.data['appdata'])} escaneados, {contagens['AppData/Temp']} suspeitos)</h2>")
        app_rows = []
        for item in self.data["appdata"]:
            if "error" in item or "note" in item:
                app_rows.append([f"{item.get('error') or item.get('note')}", "", "", False])
                continue
            sus = item.get("suspicious", False)
            nome = f"🚩 {esc(item.get('name',''))}" if sus else esc(item.get('name',''))
            app_rows.append([
                esc(item.get('type','')),
                nome,
                esc(item.get('path','')),
                sus,
            ])
        partes.append(tabela_html(["Tipo", "Nome", "Caminho"], app_rows))

        # ===== SERVIÇOS — TODOS =====
        partes.append(f"<h2>🛠️ Serviços ({total_servicos} serviços, {contagens['Serviços']} suspeitos)</h2>")
        svc_rows = []
        for srv in self.data["services"]:
            if "error" in srv:
                svc_rows.append([f"ERRO: {srv['error']}", "", "", "", "", False])
                continue
            sus = srv.get("suspicious", False)
            nome = f"🚩 {esc(srv.get('name',''))}" if sus else esc(srv.get('name',''))
            svc_rows.append([
                nome,
                esc(srv.get('display_name','')),
                esc(srv.get('status','')),
                esc(srv.get('start_type','')),
                esc(srv.get('binpath','')),
                sus,
            ])
        partes.append(tabela_html(["Nome", "Display", "Status", "Tipo Início", "BinPath"], svc_rows))

        # ===== TAREFAS — TODAS =====
        partes.append(f"<h2>📅 Tarefas Agendadas ({total_tarefas} tarefas, {contagens['Tarefas']} suspeitas)</h2>")
        task_rows = []
        for tsk in self.data["tasks"]:
            if "error" in tsk:
                task_rows.append([f"ERRO: {tsk['error']}", "", "", False])
                continue
            sus = tsk.get("suspicious", False)
            nome = f"🚩 {esc(tsk.get('task_name',''))}" if sus else esc(tsk.get('task_name',''))
            task_rows.append([
                nome,
                esc(tsk.get('status','')),
                esc(tsk.get('command','')),
                sus,
            ])
        partes.append(tabela_html(["Nome da Tarefa", "Status", "Comando"], task_rows))

        # ===== REDE — TODAS =====
        partes.append(f"<h2>🌐 Conexões de Rede ({total_conexoes} conexões, {contagens['Conexões Rede']} suspeitas)</h2>")
        net_rows = []
        for c in self.data["connections"]:
            if "error" in c:
                net_rows.append([f"ERRO: {c['error']}", "", "", "", "", "", False])
                continue
            sus = c.get("suspicious", False)
            proc = f"🚩 {esc(c.get('process',''))}" if sus else esc(c.get('process',''))
            net_rows.append([
                proc,
                esc(str(c.get('pid',''))),
                esc(c.get('local','')),
                esc(c.get('remote','')),
                esc(c.get('status','')),
                esc(c.get('type','')),
                sus,
            ])
        partes.append(tabela_html(["Processo", "PID", "Local", "Remoto", "Estado", "Tipo"], net_rows))

        # ===== RODAPÉ =====
        partes.append(f"""
<div class="footer">
    <p><strong>Total de itens suspeitos:</strong> {total_suspeitos}</p>
    <p>📅 Análise realizada em: {esc(self.data['scan_time'])}</p>
    <p>✅ Operação 100% somente leitura — nenhum arquivo foi modificado, nenhum processo encerrado.</p>
    <p style="color:#585b70">Gerado pelo Scanner de Mineradores de Criptomoedas — Modo Diagnóstico</p>
</div>
</body></html>""")

        return "\n".join(partes)


def main():
    if sys.platform != "win32":
        pass
    root = tk.Tk()
    # Tema um pouco mais moderno se disponível
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = MinerScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
