import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

class PackageUpdater:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Vulnerabilidades — Segurança e Dependências")
        self.root.geometry("950x700")
        self.root.state("zoomed") # Windows
        self.root.minsize(750, 550)
        self.root.configure(bg="#0a0a0a")

        self.messages = queue.Queue()
        self.worker = None
        self.cancel_requested = False
        self.current_process = None
        self.running = False
        self.audit_running = False
        self.audit2_running = False
        self.check_running = False
        self.freeze_running = False
        self.install_running = False
        self.audit_process = None
        self.audit_path = tk.StringVar(value="")
        self.audit2_path = tk.StringVar(value="")
        self.freeze_path = tk.StringVar(value="")

        # cores do tema
        self.bg = "#0a0a0a"
        self.fg_green = "#00ff41"
        self.fg_red = "#ff2d2d"
        self.fg_yellow = "#ffd700"
        self.fg_cyan = "#00e5ff"
        self.fg_white = "#d0d0d0"
        self.entry_bg = "#1a1a2e"
        self.text_bg = "#0d0d0d"
        self.btn_bg = "#1a1a2e"
        self.btn_fg = "#00ff41"

        self.apply_dark_theme()

        style = ttk.Style()
        style.configure("Dark.TNotebook", background=self.bg)
        style.configure("Dark.TNotebook.Tab",
                        background="#1a1a2e", foreground=self.fg_green,
                        padding=[14, 6], font=("Consolas", 11, "bold"))
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", "#0d0d0d")],
                  foreground=[("selected", self.fg_cyan)])

        notebook = ttk.Notebook(root, style="Dark.TNotebook")
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.update_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.report_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.audit2_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.check_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.freeze_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.install_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)
        self.help_tab = tk.Frame(notebook, bg=self.bg, padx=12, pady=12)

        notebook.add(self.update_tab, text=" Atualizar ")
        notebook.add(self.report_tab, text=" Vulnerabilidades ")
        notebook.add(self.audit2_tab, text=" pip_audit ")
        notebook.add(self.check_tab, text=" pip check ")
        notebook.add(self.freeze_tab, text=" pip freeze ")
        notebook.add(self.install_tab, text=" Instalar pip-audit ")
        notebook.add(self.help_tab, text=" ❓ Ajuda ")

        self.build_update_tab()
        self.build_report_tab()
        self.build_audit2_tab()
        self.build_check_tab()
        self.build_freeze_tab()
        self.build_install_tab()
        self.build_help_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.process_messages)
        self.write_log(f"Python: {sys.executable}")
        self.write_log("Pronto. Selecione uma aba para começar.")

    def apply_dark_theme(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TFrame", background=self.bg)
        style.configure("TLabel", background=self.bg,
                        foreground=self.fg_green, font=("Consolas", 10))
        style.configure("TButton", background=self.btn_bg,
                        foreground=self.fg_green, font=("Consolas", 10, "bold"),
                        borderwidth=1, padding=6)
        style.map("TButton",
                  background=[("active", "#2a2a4e"), ("disabled", "#0a0a0a")],
                  foreground=[("disabled", "#555555")])
        style.configure("Red.TButton", background="#3a0a0a",
                        foreground=self.fg_red, font=("Consolas", 10, "bold"),
                        borderwidth=1, padding=6)
        style.map("Red.TButton",
                  background=[("active", "#5a1a1a"), ("disabled", "#0a0a0a")],
                  foreground=[("disabled", "#555555")])
        style.configure("Cyan.TButton", background="#0a2a3a",
                        foreground=self.fg_cyan, font=("Consolas", 10, "bold"),
                        borderwidth=1, padding=6)
        style.map("Cyan.TButton",
                  background=[("active", "#1a4a5a"), ("disabled", "#0a0a0a")])
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor="#1a1a2e", background=self.fg_green,
                        darkcolor=self.fg_green, lightcolor=self.fg_green,
                        bordercolor=self.bg)

    def make_text(self, parent, height=20):
        text = tk.Text(parent, height=height, wrap="word", state="disabled",
                       bg=self.text_bg, fg=self.fg_green, insertbackground=self.fg_green,
                       font=("Consolas", 10), relief="flat", bd=2,
                       selectbackground="#1a3a1a", selectforeground=self.fg_green)
        text.tag_configure("red", foreground=self.fg_red, font=("Consolas", 10, "bold"))
        text.tag_configure("green", foreground=self.fg_green)
        text.tag_configure("yellow", foreground=self.fg_yellow)
        text.tag_configure("cyan", foreground=self.fg_cyan)
        text.tag_configure("white", foreground=self.fg_white)
        text.tag_configure("title", foreground=self.fg_cyan, font=("Consolas", 14, "bold"))
        text.tag_configure("subtitle", foreground=self.fg_yellow, font=("Consolas", 11, "bold"))
        text.tag_configure("bullet", foreground=self.fg_green, font=("Consolas", 10))
        return text

    def make_progress_frame(self, parent):
        """Cria frame com barra de progresso + label de porcentagem."""
        pf = tk.Frame(parent, bg=self.bg)
        bar = ttk.Progressbar(pf, mode="determinate", maximum=100,
                               style="green.Horizontal.TProgressbar")
        bar.pack(side="left", fill="x", expand=True)
        lbl = tk.Label(pf, text="0%", font=("Consolas", 10, "bold"),
                       bg=self.bg, fg=self.fg_green, width=6, anchor="e")
        lbl.pack(side="left", padx=(8, 0))
        return pf, bar, lbl

    # ===================== ABA ATUALIZAR =====================

    def build_update_tab(self):
        frame = self.update_tab
        tk.Label(frame, text="⚡ Atualizar pacotes Python",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 4))
        tk.Label(frame, text="Atualiza todos os pacotes desatualizados do Python atual.",
                 font=("Consolas", 9), bg=self.bg,
                 fg=self.fg_white, wraplength=800).pack(pady=(0, 12))

        controls = tk.Frame(frame, bg=self.bg)
        controls.pack(fill="x")
        self.start_button = ttk.Button(controls, text="▶ Verificar e atualizar tudo", command=self.start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(controls, text="✖ Cancelar", command=self.cancel,
                                         state="disabled", style="Red.TButton")
        self.cancel_button.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Pronto para começar.")
        tk.Label(frame, textvariable=self.status_var, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(12, 4))

        pf, self.progress, self.progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 10))

        self.log = self.make_text(frame, height=16)
        self.log.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Button(frame, text="Fechar", command=self.close).pack(anchor="e")

    # ===================== ABA VULNERABILIDADES =====================

    def build_report_tab(self):
        frame = self.report_tab
        tk.Label(frame, text="🛡️ Relatório de vulnerabilidades",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))
        tk.Label(frame, text="Executa: python -m pip_audit\nVulnerabilidades aparecem em VERMELHO.",
                 font=("Consolas", 9), bg=self.bg, fg=self.fg_white,
                 justify="left", wraplength=800).pack(anchor="w", pady=(0, 12))

        file_row = tk.Frame(frame, bg=self.bg)
        file_row.pack(fill="x", pady=(0, 10))
        tk.Label(file_row, text="Salvar em:", font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_green).pack(side="left")
        self.path_entry = tk.Entry(file_row, textvariable=self.audit_path,
                                   bg=self.entry_bg, fg=self.fg_green,
                                   font=("Consolas", 10), insertbackground=self.fg_green,
                                   relief="flat", bd=2)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(file_row, text="📂 Escolher...", command=self.choose_report_path).pack(side="left")

        buttons = tk.Frame(frame, bg=self.bg)
        buttons.pack(fill="x", pady=(0, 10))
        self.audit_button = ttk.Button(buttons, text="▶ Executar pip-audit e salvar", command=self.start_audit)
        self.audit_button.pack(side="left")
        ttk.Button(buttons, text="🗑 Limpar", command=self.clear_audit_output).pack(side="left", padx=(8, 0))

        self.audit_status = tk.StringVar(value="Escolha onde salvar e clique no botão.")
        tk.Label(frame, textvariable=self.audit_status, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(2, 4))

        pf, self.audit_progress, self.audit_progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 8))

        self.audit_output = self.make_text(frame, height=16)
        self.audit_output.pack(fill="both", expand=True)

    # ===================== ABA pip_audit =====================

    def build_audit2_tab(self):
        frame = self.audit2_tab
        tk.Label(frame, text="🔐 python -m pip_audit",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))
        tk.Label(frame,
                 text="Executa diretamente: python -m pip_audit\n"
                      "Vulnerabilidades em VERMELHO. Seguros em VERDE.",
                 font=("Consolas", 9), bg=self.bg, fg=self.fg_white,
                 justify="left", wraplength=800).pack(anchor="w", pady=(0, 12))

        file_row = tk.Frame(frame, bg=self.bg)
        file_row.pack(fill="x", pady=(0, 10))
        tk.Label(file_row, text="Salvar em (opcional):", font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_green).pack(side="left")
        self.audit2_entry = tk.Entry(file_row, textvariable=self.audit2_path,
                                     bg=self.entry_bg, fg=self.fg_green,
                                     font=("Consolas", 10), insertbackground=self.fg_green,
                                     relief="flat", bd=2)
        self.audit2_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(file_row, text="📂 Escolher...", command=self.choose_audit2_path).pack(side="left")

        btn_row = tk.Frame(frame, bg=self.bg)
        btn_row.pack(fill="x", pady=(0, 10))
        self.audit2_button = ttk.Button(btn_row, text="▶ Executar python -m pip_audit",
                                         command=self.start_audit2, style="Cyan.TButton")
        self.audit2_button.pack(side="left")
        ttk.Button(btn_row, text="🗑 Limpar", command=self.clear_audit2_output).pack(side="left", padx=(8, 0))

        self.audit2_status = tk.StringVar(value="Clique para executar pip_audit.")
        tk.Label(frame, textvariable=self.audit2_status, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(2, 4))

        pf, self.audit2_progress, self.audit2_progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 8))

        self.audit2_output = self.make_text(frame, height=16)
        self.audit2_output.pack(fill="both", expand=True)

    # ===================== ABA pip check =====================

    def build_check_tab(self):
        frame = self.check_tab
        tk.Label(frame, text="🔍 pip check — Verificar dependências",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))
        tk.Label(frame, text="Executa: python -m pip check\nProblemas aparecem em VERMELHO.",
                 font=("Consolas", 9), bg=self.bg, fg=self.fg_white,
                 justify="left", wraplength=800).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(frame, bg=self.bg)
        btn_row.pack(fill="x", pady=(0, 10))
        self.check_button = ttk.Button(btn_row, text="▶ Executar pip check", command=self.start_check)
        self.check_button.pack(side="left")
        ttk.Button(btn_row, text="🗑 Limpar", command=self.clear_check_output).pack(side="left", padx=(8, 0))

        self.check_status = tk.StringVar(value="Clique para verificar dependências.")
        tk.Label(frame, textvariable=self.check_status, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(2, 4))

        pf, self.check_progress, self.check_progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 8))

        self.check_output = self.make_text(frame, height=18)
        self.check_output.pack(fill="both", expand=True)

    # ===================== ABA pip freeze =====================

    def build_freeze_tab(self):
        frame = self.freeze_tab
        tk.Label(frame, text="📋 pip freeze — Lista de pacotes",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))
        tk.Label(frame, text="Executa: python -m pip freeze\nSalva a lista num arquivo .txt",
                 font=("Consolas", 9), bg=self.bg, fg=self.fg_white,
                 justify="left", wraplength=800).pack(anchor="w", pady=(0, 12))

        file_row = tk.Frame(frame, bg=self.bg)
        file_row.pack(fill="x", pady=(0, 10))
        tk.Label(file_row, text="Salvar em:", font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_green).pack(side="left")
        self.freeze_entry = tk.Entry(file_row, textvariable=self.freeze_path,
                                     bg=self.entry_bg, fg=self.fg_green,
                                     font=("Consolas", 10), insertbackground=self.fg_green,
                                     relief="flat", bd=2)
        self.freeze_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(file_row, text="📂 Escolher...", command=self.choose_freeze_path).pack(side="left")

        btn_row = tk.Frame(frame, bg=self.bg)
        btn_row.pack(fill="x", pady=(0, 10))
        self.freeze_button = ttk.Button(btn_row, text="▶ Executar pip freeze e salvar", command=self.start_freeze)
        self.freeze_button.pack(side="left")
        ttk.Button(btn_row, text="🗑 Limpar", command=self.clear_freeze_output).pack(side="left", padx=(8, 0))

        self.freeze_status = tk.StringVar(value="Escolha onde salvar e clique no botão.")
        tk.Label(frame, textvariable=self.freeze_status, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(2, 4))

        pf, self.freeze_progress, self.freeze_progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 8))

        self.freeze_output = self.make_text(frame, height=16)
        self.freeze_output.pack(fill="both", expand=True)

    # ===================== ABA INSTALAR pip-audit =====================

    def build_install_tab(self):
        frame = self.install_tab
        tk.Label(frame, text="📦 Instalar pip-audit",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))
        tk.Label(frame,
                 text="Se o pip-audit não estiver instalado, clique abaixo.\nExecuta: pip install pip-audit",
                 font=("Consolas", 9), bg=self.bg, fg=self.fg_white,
                 justify="left", wraplength=800).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(frame, bg=self.bg)
        btn_row.pack(fill="x", pady=(0, 10))
        self.install_button = ttk.Button(btn_row, text="▶ Instalar pip-audit",
                                          command=self.start_install_pipaudit, style="Cyan.TButton")
        self.install_button.pack(side="left")
        self.verify_button = ttk.Button(btn_row, text="🔍 Verificar se está instalado",
                                         command=self.verify_pipaudit)
        self.verify_button.pack(side="left", padx=(8, 0))
        ttk.Button(btn_row, text="🗑 Limpar", command=self.clear_install_output).pack(side="left", padx=(8, 0))

        self.install_status = tk.StringVar(value="Clique para instalar ou verificar.")
        tk.Label(frame, textvariable=self.install_status, font=("Consolas", 10),
                 bg=self.bg, fg=self.fg_yellow).pack(anchor="w", pady=(2, 4))

        pf, self.install_progress, self.install_progress_lbl = self.make_progress_frame(frame)
        pf.pack(fill="x", pady=(0, 8))

        self.install_output = self.make_text(frame, height=16)
        self.install_output.pack(fill="both", expand=True)

    # ===================== ABA AJUDA =====================

    def build_help_tab(self):
        frame = self.help_tab
        tk.Label(frame, text="❓ Ajuda — Para que serve este script",
                 font=("Consolas", 16, "bold"), bg=self.bg,
                 fg=self.fg_cyan).pack(pady=(4, 8))

        container = tk.Frame(frame, bg=self.bg)
        container.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(container, bg="#1a1a2e", troughcolor=self.bg,
                                  activebackground=self.fg_green)
        scrollbar.pack(side="right", fill="y")

        self.help_text = tk.Text(
            container, wrap="word", state="disabled",
            bg=self.text_bg, fg=self.fg_green, insertbackground=self.fg_green,
            font=("Consolas", 10), relief="flat", bd=2,
            selectbackground="#1a3a1a", selectforeground=self.fg_green,
            yscrollcommand=scrollbar.set, padx=15, pady=15
        )
        self.help_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.help_text.yview)

        self.help_text.tag_configure("title", foreground=self.fg_cyan, font=("Consolas", 15, "bold"))
        self.help_text.tag_configure("subtitle", foreground=self.fg_yellow, font=("Consolas", 12, "bold"))
        self.help_text.tag_configure("body", foreground=self.fg_green, font=("Consolas", 10))
        self.help_text.tag_configure("highlight", foreground=self.fg_cyan, font=("Consolas", 10, "bold"))
        self.help_text.tag_configure("success", foreground="#00ff41", font=("Consolas", 10, "bold"))
        self.help_text.tag_configure("warning", foreground=self.fg_red, font=("Consolas", 10, "bold"))
        self.help_text.tag_configure("separator", foreground="#333333", font=("Consolas", 10))
        self.help_text.tag_configure("code", foreground=self.fg_yellow, font=("Consolas", 10), background="#1a1a2e")

        self.fill_help_text()

    def fill_help_text(self):
        t = self.help_text
        t.configure(state="normal")

        def add(text, tag="body"):
            t.insert("end", text, tag)

        add("╔══════════════════════════════════════════════════════╗\n", "separator")
        add("  ATUALIZADOR DE PACOTES PYTHON — AJUDA\n", "title")
        add("╚══════════════════════════════════════════════════════╝\n\n", "separator")

        add("Para que serve este script?\n\n", "subtitle")
        add("O ", "body")
        add("Atualizador de Pacotes Python", "highlight")
        add(" é um script criado para ajudar\n", "body")
        add("a manter o ambiente Python organizado, atualizado e\n", "body")
        add("mais seguro.\n\n", "body")
        add("Ele verifica os pacotes instalados no Python e auxilia\n", "body")
        add("na identificação de problemas relacionados a ", "body")
        add("vulnerabilidades\n", "warning")
        add("de segurança", "warning")
        add(" e ", "body")
        add("conflitos entre dependências", "warning")
        add(".\n\n", "body")

        add("─────────────────────────────────────────────\n", "separator")
        add("Principais funções:\n\n", "subtitle")

        funcoes = [
            "Verificar vulnerabilidades de segurança nos pacotes\n    instalados utilizando o pip_audit.",
            "Verificar conflitos de dependências utilizando o pip check.",
            "Identificar pacotes que possuem versões vulneráveis\n    ou incompatíveis.",
            "Auxiliar na atualização dos pacotes para versões\n    mais recentes e seguras.",
            "Registrar os resultados das verificações em arquivo.",
            "Manter um histórico das alterações realizadas.",
            "Identificar pacotes problemáticos que podem precisar\n    ser removidos quando causam conflitos.",
        ]
        for f in funcoes:
            add("  ▸ ", "highlight")
            add(f + "\n\n", "body")

        add("─────────────────────────────────────────────\n", "separator")
        add("Abas disponíveis:\n\n", "subtitle")

        abas = [
            ("  ⚡ Atualizar", "Verifica e atualiza todos os pacotes desatualizados."),
            ("  🛡️ Vulnerabilidades", "Executa pip_audit e salva relatório em arquivo."),
            ("  🔐 pip_audit", "Executa python -m pip_audit em tempo real."),
            ("  🔍 pip check", "Verifica conflitos e dependências quebradas."),
            ("  📋 pip freeze", "Lista todos os pacotes e salva em arquivo."),
            ("  📦 Instalar pip-audit", "Instala o pip-audit caso necessário."),
        ]
        for nome, desc in abas:
            add(nome + "\n", "highlight")
            add("    " + desc + "\n\n", "body")

        add("─────────────────────────────────────────────\n", "separator")
        add("Exemplo de resultado ideal:\n\n", "subtitle")
        add("  pip_audit:  ", "highlight")
        add("No known vulnerabilities found\n", "success")
        add("  pip check:  ", "highlight")
        add("No broken requirements found\n\n", "success")
        add("Isso significa que o ambiente está ", "body")
        add("sem vulnerabilidades\n", "success")
        add("e ", "body")
        add("sem conflitos de dependências", "success")
        add(".\n\n", "body")

        add("─────────────────────────────────────────────\n", "separator")
        add("Exemplo de problema encontrado:\n\n", "subtitle")
        add("  pip_audit encontrou vulnerabilidade no ", "body")
        add("Pillow\n", "warning")
        add("  Versão corrigida: ", "body")
        add("13.0.0\n", "success")
        add("  Conflito causado por: ", "body")
        add("instagrapi\n\n", "warning")
        add("  Após remover o pacote problemático:\n", "body")
        add("  ✅ No known vulnerabilities found\n", "success")
        add("  ✅ No broken requirements found\n\n", "success")

        add("─────────────────────────────────────────────\n", "separator")
        add("Objetivo principal:\n\n", "subtitle")
        add("Facilitar a ", "body")
        add("manutenção preventiva do Python", "highlight")
        add(", evitando\nque o ambiente fique com pacotes ", "body")
        add("desatualizados", "warning")
        add(", ", "body")
        add("vulneráveis", "warning")
        add("\nou com ", "body")
        add("dependências incompatíveis", "warning")
        add(".\n\n", "body")
        add("Funciona como ferramenta de manutenção, ajudando a\nmanter os programas mais ", "body")
        add("organizados", "success")
        add(", ", "body")
        add("seguros", "success")
        add(" e ", "body")
        add("estáveis", "success")
        add(".\n\n", "body")

        add("─────────────────────────────────────────────\n", "separator")
        add("Dicas:\n\n", "subtitle")
        add("  ▸ Execute periodicamente para manter tudo atualizado.\n", "body")
        add("  ▸ Sempre verifique o ", "body")
        add("pip check", "code")
        add(" após atualizar pacotes.\n", "body")
        add("  ▸ Use o ", "body")
        add("pip freeze", "code")
        add(" para backup antes de atualizar.\n", "body")
        add("  ▸ Se um pacote causar conflito, remova com:\n    ", "body")
        add("pip uninstall nome_pacote", "code")
        add("\n\n", "body")

        add("╔══════════════════════════════════════════════════════╗\n", "separator")
        add("  Python: ", "body")
        add(f"{sys.executable}\n", "highlight")
        add("╚══════════════════════════════════════════════════════╝\n", "separator")

        t.configure(state="disabled")

    # ===================== HELPERS =====================

    def write_to_text(self, widget, text, tag=None):
        widget.configure(state="normal")
        if tag:
            widget.insert("end", str(text).rstrip() + "\n", tag)
        else:
            widget.insert("end", str(text).rstrip() + "\n")
        widget.see("end")
        widget.configure(state="disabled")

    def write_log(self, text, tag=None):
        self.write_to_text(self.log, text, tag)

    def write_audit_output(self, text, tag=None):
        self.write_to_text(self.audit_output, text, tag)

    def write_audit2_output(self, text, tag=None):
        self.write_to_text(self.audit2_output, text, tag)

    def write_check_output(self, text, tag=None):
        self.write_to_text(self.check_output, text, tag)

    def write_freeze_output(self, text, tag=None):
        self.write_to_text(self.freeze_output, text, tag)

    def write_install_output(self, text, tag=None):
        self.write_to_text(self.install_output, text, tag)

    def clear_audit_output(self):
        self.audit_output.configure(state="normal")
        self.audit_output.delete("1.0", "end")
        self.audit_output.configure(state="disabled")

    def clear_audit2_output(self):
        self.audit2_output.configure(state="normal")
        self.audit2_output.delete("1.0", "end")
        self.audit2_output.configure(state="disabled")

    def clear_check_output(self):
        self.check_output.configure(state="normal")
        self.check_output.delete("1.0", "end")
        self.check_output.configure(state="disabled")

    def clear_freeze_output(self):
        self.freeze_output.configure(state="normal")
        self.freeze_output.delete("1.0", "end")
        self.freeze_output.configure(state="disabled")

    def clear_install_output(self):
        self.install_output.configure(state="normal")
        self.install_output.delete("1.0", "end")
        self.install_output.configure(state="disabled")

    def update_bar(self, bar, lbl, value):
        bar.configure(value=value)
        lbl.configure(text=f"{int(value)}%")

    # ===================== ANIMAÇÃO DE PROGRESSO =====================

    def animate_progress(self, bar, lbl, flag_attr, duration_ms=8000, steps=100):
        """
        Anima a barra de 0% a 90% suavemente durante a operação.
        Quando a operação termina, pula para 100%.
        flag_attr: nome do atributo bool que indica se ainda está rodando.
        """
        interval = duration_ms // steps
        self._animate_step(bar, lbl, flag_attr, 0, steps, interval)

    def _animate_step(self, bar, lbl, flag_attr, step, total_steps, interval):
        if not getattr(self, flag_attr, False):
            # operação terminou → 100%
            self.update_bar(bar, lbl, 100)
            return
        # vai de 0 a 90 suavemente
        progress = min(90, (step / total_steps) * 90)
        self.update_bar(bar, lbl, progress)
        next_step = step + 1 if step < total_steps else total_steps
        self.root.after(interval, self._animate_step, bar, lbl, flag_attr,
                        next_step, total_steps, interval)

    # ===================== FILE CHOOSERS =====================

    def choose_report_path(self):
        chosen = filedialog.asksaveasfilename(
            parent=self.root, title="Salvar relatório de vulnerabilidades",
            defaultextension=".txt", initialfile="relatorio_vulnerabilidades.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if chosen:
            self.audit_path.set(chosen)

    def choose_audit2_path(self):
        chosen = filedialog.asksaveasfilename(
            parent=self.root, title="Salvar saída do pip_audit",
            defaultextension=".txt", initialfile="pip_audit_resultado.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if chosen:
            self.audit2_path.set(chosen)

    def choose_freeze_path(self):
        chosen = filedialog.asksaveasfilename(
            parent=self.root, title="Salvar pip freeze",
            defaultextension=".txt", initialfile="requirements.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if chosen:
            self.freeze_path.set(chosen)

    def is_any_running(self):
        return (self.running or self.audit_running or self.audit2_running
                or self.check_running or self.freeze_running or self.install_running)

    # ===================== OPERAÇÃO: ATUALIZAR =====================

    def start(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        self.cancel_requested = False
        self.running = True
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.update_bar(self.progress, self.progress_lbl, 0)
        self.status_var.set("Verificando pacotes desatualizados...")
        self.write_log("\n" + "=" * 55, "cyan")
        self.write_log("Início: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "cyan")
        self.worker = threading.Thread(target=self.run_updates, daemon=True)
        self.worker.start()

    def cancel(self):
        if not self.running:
            return
        self.cancel_requested = True
        self.status_var.set("Cancelando... aguarde.")
        self.write_log("Cancelamento solicitado.", "yellow")
        if self.current_process is not None:
            try:
                self.current_process.terminate()
            except Exception:
                pass

    def run_command(self, args, label):
        if self.cancel_requested:
            return 1, ""
        self.emit("status", label)
        try:
            process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1
            )
            self.current_process = process
            output_lines = []
            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)
                    self.emit("log", line.rstrip())
                    if self.cancel_requested:
                        try:
                            process.terminate()
                        except Exception:
                            pass
            return_code = process.wait()
            self.current_process = None
            return return_code, "".join(output_lines)
        except Exception as exc:
            self.current_process = None
            self.emit("log", f"Erro ao executar comando: {exc}")
            return 1, str(exc)

    def run_updates(self):
        try:
            code, output = self.run_command(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                "Consultando pacotes desatualizados..."
            )
            if self.cancel_requested:
                self.emit("finished", "cancelled")
                return
            if code != 0:
                self.emit("finished", "error")
                return
            try:
                packages = json.loads(output)
            except json.JSONDecodeError:
                self.emit("log", "Não foi possível interpretar a lista do pip.")
                self.emit("finished", "error")
                return

            if not packages:
                self.emit("log", "Nenhum pacote desatualizado.")
            total = len(packages)
            failed = []
            for index, package in enumerate(packages, start=1):
                if self.cancel_requested:
                    break
                name = package.get("name", "")
                current = package.get("version", "?")
                latest = package.get("latest_version", "?")
                pct = ((index - 1) / max(total, 1)) * 80
                self.emit("update_progress", pct)
                self.emit("status", f"Atualizando {index}/{total}: {name}")
                self.emit("log", f"\n[{index}/{total}] {name}: {current} → {latest}")
                result, _ = self.run_command(
                    [sys.executable, "-m", "pip", "install", "--upgrade", name],
                    f"Instalando {name}..."
                )
                if result != 0:
                    failed.append(name)
                    self.emit("log_red", f"FALHA: atualização de {name} falhou.")
                pct = (index / max(total, 1)) * 80
                self.emit("update_progress", pct)

            if self.cancel_requested:
                self.emit("finished", "cancelled")
                return

            self.emit("update_progress", 85)
            self.emit("log", "\nVerificando dependências...")
            check_code, _ = self.run_command(
                [sys.executable, "-m", "pip", "check"],
                "Verificando conflitos..."
            )
            if self.cancel_requested:
                self.emit("finished", "cancelled")
                return

            self.emit("update_progress", 92)
            self.emit("log", "\nExecutando pip-audit...")
            audit_code, _ = self.run_command(
                [sys.executable, "-m", "pip_audit"],
                "Verificando vulnerabilidades..."
            )
            self.emit("update_progress", 100)
            self.emit("finished", {
                "failed": failed, "check_code": check_code, "audit_code": audit_code
            })
        except Exception as exc:
            self.emit("log", f"Erro inesperado: {exc}")
            self.emit("finished", "error")

    # ===================== OPERAÇÃO: AUDIT (vulnerabilidades) =====================

    def start_audit(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        path = self.audit_path.get().strip()
        if not path:
            self.choose_report_path()
            path = self.audit_path.get().strip()
        if not path:
            return

        self.audit_running = True
        self.audit_button.configure(state="disabled")
        self.audit_status.set("Executando pip-audit... aguarde.")
        self.update_bar(self.audit_progress, self.audit_progress_lbl, 0)
        self.write_audit_output("=" * 65, "cyan")
        self.write_audit_output("Início: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "cyan")
        self.animate_progress(self.audit_progress, self.audit_progress_lbl,
                              "audit_running", duration_ms=15000)
        threading.Thread(target=self.run_audit, args=(path,), daemon=True).start()

    def run_audit(self, path):
        command = [sys.executable, "-m", "pip_audit"]
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", check=False
            )
            output = result.stdout or "(Sem saída.)"
            report = (
                f"Comando: {' '.join(command)}\n"
                f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Código de saída: {result.returncode}\n"
                + "=" * 70 + "\n\n" + output
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(report)
            for line in output.splitlines():
                low = line.lower()
                if any(w in low for w in ["vuln", "critical", "high", "medium",
                                           "fix available", "no fix", "cve-"]):
                    self.messages.put(("audit_output_red", line))
                else:
                    self.messages.put(("audit_output", line))
            self.messages.put(("audit_finished", (result.returncode, path, None)))
        except Exception as exc:
            err = f"Erro: {exc}"
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(err + "\n")
            except Exception:
                pass
            self.messages.put(("audit_output_red", err))
            self.messages.put(("audit_finished", (1, path, str(exc))))

    # ===================== OPERAÇÃO: AUDIT2 (pip_audit) =====================

    def start_audit2(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        self.audit2_running = True
        self.audit2_button.configure(state="disabled")
        self.audit2_status.set("Executando python -m pip_audit... aguarde.")
        self.update_bar(self.audit2_progress, self.audit2_progress_lbl, 0)
        self.write_audit2_output("=" * 65, "cyan")
        self.write_audit2_output("Início: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "cyan")
        self.write_audit2_output(f"Comando: {sys.executable} -m pip_audit", "cyan")
        self.write_audit2_output("=" * 65, "cyan")
        self.animate_progress(self.audit2_progress, self.audit2_progress_lbl,
                              "audit2_running", duration_ms=15000)
        path = self.audit2_path.get().strip()
        threading.Thread(target=self.run_audit2, args=(path,), daemon=True).start()

    def run_audit2(self, path):
        command = [sys.executable, "-m", "pip_audit"]
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1
            )
            all_lines = []
            if process.stdout:
                for line in process.stdout:
                    stripped = line.rstrip()
                    all_lines.append(stripped)
                    low = stripped.lower()
                    if any(w in low for w in ["vuln", "critical", "high", "medium",
                                               "fix available", "no fix", "cve-",
                                               "fail", "error"]):
                        self.messages.put(("audit2_output_red", stripped))
                    elif "no known vulnerabilities" in low:
                        self.messages.put(("audit2_output_green", stripped))
                    else:
                        self.messages.put(("audit2_output", stripped))

            return_code = process.wait()

            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"Comando: {' '.join(command)}\n")
                        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        f.write(f"Código de saída: {return_code}\n")
                        f.write("=" * 70 + "\n\n")
                        f.write("\n".join(all_lines) + "\n")
                    self.messages.put(("audit2_output", f"\n📄 Salvo em: {path}"))
                except Exception as exc:
                    self.messages.put(("audit2_output_red", f"Erro ao salvar: {exc}"))

            self.messages.put(("audit2_finished", return_code))
        except Exception as exc:
            self.messages.put(("audit2_output_red", f"Erro: {exc}"))
            self.messages.put(("audit2_finished", 1))

    # ===================== OPERAÇÃO: CHECK =====================

    def start_check(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        self.check_running = True
        self.check_button.configure(state="disabled")
        self.check_status.set("Executando pip check... aguarde.")
        self.update_bar(self.check_progress, self.check_progress_lbl, 0)
        self.write_check_output("=" * 55, "cyan")
        self.write_check_output("Início: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "cyan")
        self.animate_progress(self.check_progress, self.check_progress_lbl,
                              "check_running", duration_ms=6000)
        threading.Thread(target=self.run_check, daemon=True).start()

    def run_check(self):
        command = [sys.executable, "-m", "pip", "check"]
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", check=False
            )
            output = result.stdout or "(Sem saída.)"
            for line in output.splitlines():
                low = line.lower()
                if any(w in low for w in ["not installed", "has requirement",
                                           "incompatible", "conflict", "error"]):
                    self.messages.put(("check_output_red", line))
                else:
                    self.messages.put(("check_output", line))
            self.messages.put(("check_finished", result.returncode))
        except Exception as exc:
            self.messages.put(("check_output_red", f"Erro: {exc}"))
            self.messages.put(("check_finished", 1))

    # ===================== OPERAÇÃO: FREEZE =====================

    def start_freeze(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        path = self.freeze_path.get().strip()
        if not path:
            self.choose_freeze_path()
            path = self.freeze_path.get().strip()
        if not path:
            return

        self.freeze_running = True
        self.freeze_button.configure(state="disabled")
        self.freeze_status.set("Executando pip freeze... aguarde.")
        self.update_bar(self.freeze_progress, self.freeze_progress_lbl, 0)
        self.write_freeze_output("=" * 55, "cyan")
        self.animate_progress(self.freeze_progress, self.freeze_progress_lbl,
                              "freeze_running", duration_ms=5000)
        threading.Thread(target=self.run_freeze, args=(path,), daemon=True).start()

    def run_freeze(self, path):
        command = [sys.executable, "-m", "pip", "freeze"]
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", check=False
            )
            output = result.stdout or "(Sem saída.)"
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# pip freeze — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(output)
            for line in output.splitlines():
                self.messages.put(("freeze_output", line))
            self.messages.put(("freeze_finished", (result.returncode, path)))
        except Exception as exc:
            self.messages.put(("freeze_output_red", f"Erro: {exc}"))
            self.messages.put(("freeze_finished", (1, path)))

    # ===================== OPERAÇÃO: INSTALAR pip-audit =====================

    def start_install_pipaudit(self):
        if self.is_any_running():
            messagebox.showwarning("Aguarde", "Termine a operação atual primeiro.")
            return
        self.install_running = True
        self.install_button.configure(state="disabled")
        self.install_status.set("Instalando pip-audit... aguarde.")
        self.update_bar(self.install_progress, self.install_progress_lbl, 0)
        self.write_install_output("=" * 55, "cyan")
        self.write_install_output("Executando: pip install pip-audit", "cyan")
        self.animate_progress(self.install_progress, self.install_progress_lbl,
                              "install_running", duration_ms=12000)
        threading.Thread(target=self.run_install_pipaudit, daemon=True).start()

    def run_install_pipaudit(self):
        command = [sys.executable, "-m", "pip", "install", "pip-audit"]
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", check=False
            )
            output = result.stdout or "(Sem saída.)"
            for line in output.splitlines():
                low = line.lower()
                if "error" in low or "failed" in low:
                    self.messages.put(("install_output_red", line))
                elif "successfully" in low:
                    self.messages.put(("install_output_green", line))
                else:
                    self.messages.put(("install_output", line))
            self.messages.put(("install_finished", result.returncode))
        except Exception as exc:
            self.messages.put(("install_output_red", f"Erro: {exc}"))
            self.messages.put(("install_finished", 1))

    def verify_pipaudit(self):
        self.write_install_output("\nVerificando pip-audit...", "yellow")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip_audit", "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", check=False
            )
            out = result.stdout.strip() if result.stdout else ""
            if result.returncode == 0 and out:
                self.write_install_output(f"✅ pip-audit encontrado: {out}", "green")
                self.install_status.set("pip-audit está instalado!")
            else:
                self.write_install_output("❌ pip-audit NÃO encontrado.", "red")
                self.install_status.set("pip-audit não está instalado.")
        except Exception as exc:
            self.write_install_output(f"❌ Erro ao verificar: {exc}", "red")
            self.install_status.set("Erro ao verificar pip-audit.")

    # ===================== EMIT / PROCESS =====================

    def emit(self, kind, data=None):
        self.messages.put((kind, data))

    def process_messages(self):
        try:
            while True:
                kind, data = self.messages.get_nowait()

                # --- update tab ---
                if kind == "log":
                    self.write_log(data)
                elif kind == "log_red":
                    self.write_log(data, "red")
                elif kind == "status":
                    self.status_var.set(data)
                elif kind == "update_progress":
                    self.update_bar(self.progress, self.progress_lbl, data)

                # --- audit tab (vulnerabilidades) ---
                elif kind == "audit_output":
                    self.write_audit_output(data)
                elif kind == "audit_output_red":
                    self.write_audit_output(data, "red")
                elif kind == "audit_finished":
                    self.audit_running = False
                    self.audit_button.configure(state="normal")
                    self.update_bar(self.audit_progress, self.audit_progress_lbl, 100)
                    code, path, error = data
                    if error:
                        self.audit_status.set("Erro ao gerar o relatório.")
                        messagebox.showerror("Erro", f"Falha:\n{error}")
                    else:
                        self.audit_status.set(f"Salvo: {path} (código: {code})")
                        if code != 0:
                            self.write_audit_output(
                                "\n⚠ VULNERABILIDADES DETECTADAS! Verifique acima.", "red")
                        else:
                            self.write_audit_output(
                                "\n✅ Nenhuma vulnerabilidade Encontrada!", "green")
                        messagebox.showinfo("Relatório", f"Salvo em:\n{path}")

                # --- audit2 tab (pip_audit) ---
                elif kind == "audit2_output":
                    self.write_audit2_output(data)
                elif kind == "audit2_output_red":
                    self.write_audit2_output(data, "red")
                elif kind == "audit2_output_green":
                    self.write_audit2_output(data, "green")
                elif kind == "audit2_finished":
                    self.audit2_running = False
                    self.audit2_button.configure(state="normal")
                    self.update_bar(self.audit2_progress, self.audit2_progress_lbl, 100)
                    if data == 0:
                        self.audit2_status.set("✅ Concluído — sem vulnerabilidades!")
                        self.write_audit2_output("\n✅ Nenhuma vulnerabilidade Encontrada!", "green")
                    else:
                        self.audit2_status.set("⚠ Concluído — verifique linhas vermelhas!")
                        self.write_audit2_output(
                            "\n⚠ VULNERABILIDADES OU ERROS DETECTADOS! Veja acima.", "red")

                # --- check tab ---
                elif kind == "check_output":
                    self.write_check_output(data)
                elif kind == "check_output_red":
                    self.write_check_output(data, "red")
                elif kind == "check_finished":
                    self.check_running = False
                    self.check_button.configure(state="normal")
                    self.update_bar(self.check_progress, self.check_progress_lbl, 100)
                    if data == 0:
                        self.check_status.set("✅ Sem conflitos de dependência!")
                        self.write_check_output("\n✅ Tudo OK — sem conflitos.", "green")
                    else:
                        self.check_status.set("⚠ Conflitos detectados! Veja acima.")
                        self.write_check_output(
                            "\n⚠ CONFLITOS DETECTADOS! Verifique linhas vermelhas.", "red")

                # --- freeze tab ---
                elif kind == "freeze_output":
                    self.write_freeze_output(data)
                elif kind == "freeze_output_red":
                    self.write_freeze_output(data, "red")
                elif kind == "freeze_finished":
                    self.freeze_running = False
                    self.freeze_button.configure(state="normal")
                    self.update_bar(self.freeze_progress, self.freeze_progress_lbl, 100)
                    code, path = data
                    if code == 0:
                        self.freeze_status.set(f"✅ Salvo em: {path}")
                        self.write_freeze_output(f"\n✅ Lista salva em: {path}", "green")
                    else:
                        self.freeze_status.set("⚠ Houve erro. Veja acima.")

                # --- install tab ---
                elif kind == "install_output":
                    self.write_install_output(data)
                elif kind == "install_output_red":
                    self.write_install_output(data, "red")
                elif kind == "install_output_green":
                    self.write_install_output(data, "green")
                elif kind == "install_finished":
                    self.install_running = False
                    self.install_button.configure(state="normal")
                    self.update_bar(self.install_progress, self.install_progress_lbl, 100)
                    if data == 0:
                        self.install_status.set("✅ pip-audit instalado com sucesso!")
                        self.write_install_output("\n✅ Instalação concluída!", "green")
                    else:
                        self.install_status.set("⚠ Falha na instalação. Veja acima.")
                        self.write_install_output("\n❌ Falha na instalação.", "red")

                # --- finished (update tab) ---
                elif kind == "finished":
                    self.running = False
                    self.current_process = None
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.update_bar(self.progress, self.progress_lbl, 100)
                    if data == "cancelled":
                        self.status_var.set("Operação cancelada.")
                        self.write_log("Operação cancelada.", "yellow")
                    elif data == "error":
                        self.status_var.set("Erro na operação.")
                        messagebox.showerror("Erro", "Verifique o registro.")
                    else:
                        self.status_var.set("Processo concluído.")
                        failed = data.get("failed", [])
                        self.write_log("\n" + "=" * 40, "cyan")
                        self.write_log("RESUMO FINAL:", "cyan")
                        if failed:
                            self.write_log(f"Falhas: {', '.join(failed)}", "red")
                        else:
                            self.write_log("Falhas: nenhuma", "green")
                        if data["check_code"] == 0:
                            self.write_log("pip check: OK", "green")
                        else:
                            self.write_log("pip check: conflitos encontrados", "red")
                        if data["audit_code"] == 0:
                            self.write_log("pip-audit: sem vulnerabilidades", "green")
                        else:
                            self.write_log("pip-audit: VULNERABILIDADES ENCONTRADAS", "red")
                        messagebox.showinfo("Concluído", "Rotina finalizada. Confira o registro.")
        except queue.Empty:
            pass
        self.root.after(100, self.process_messages)

    def close(self):
        if self.running:
            if not messagebox.askyesno("Sair", "Atualização em andamento. Cancelar e fechar?"):
                return
            self.cancel()
            self.root.after(500, self.root.destroy)
        elif self.is_any_running():
            if not messagebox.askyesno("Sair", "Operação em andamento. Fechar mesmo assim?"):
                return
            self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    PackageUpdater(root)
    root.mainloop()


if __name__ == "__main__":
    main()
