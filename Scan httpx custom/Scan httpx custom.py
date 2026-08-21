#!/usr/bin/env python3
"""
Httpx - Scan em tempo real com barra de progresso 0-100%
Customização completa — presets, headers, portas, colunas, args extras.
Requisitos: Python 3.7+, httpx no PATH
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import json
import os
import threading
import sys
import platform
from datetime import datetime
import configparser


# ─────────────────────────────────────────────────
#  CONFIG MANAGER (salva/carrega preferências)
# ─────────────────────────────────────────────────

class ConfigManager:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".httpx_gui")
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "settings.ini")
        self.presets_file = os.path.join(config_dir, "presets.ini")
        os.makedirs(config_dir, exist_ok=True)
        self.config = configparser.ConfigParser()
        self.presets = configparser.ConfigParser()
        self._load()

    def _load(self):
        self.config.read(self.config_file)
        self.presets.read(self.presets_file)

    def get(self, section, key, default=""):
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self._save()

    def _save(self):
        try:
            with open(self.config_file, "w") as f:
                self.config.write(f)
        except Exception:
            pass

    def list_presets(self):
        return self.presets.sections()

    def save_preset(self, name, flags):
        if self.presets.has_section(name):
            self.presets.remove_section(name)
        self.presets.add_section(name)
        self.presets.set(name, "flags", flags)
        self.presets.set(name, "created", datetime.now().isoformat())
        with open(self.presets_file, "w") as f:
            self.presets.write(f)

    def load_preset(self, name):
        try:
            return self.presets.get(name, "flags")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return ""

    def delete_preset(self, name):
        if self.presets.has_section(name):
            self.presets.remove_section(name)
            with open(self.presets_file, "w") as f:
                self.presets.write(f)

    def get_custom_headers(self):
        raw = self.get("custom", "headers", "")
        headers = {}
        if raw.strip():
            for line in raw.strip().split("\n"):
                line = line.strip()
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip()] = v.strip()
        return headers

    def get_custom_ports(self):
        raw = self.get("custom", "ports", "")
        if raw.strip():
            return [p.strip() for p in raw.split(",") if p.strip()]
        return []

    def get_threads(self):
        try:
            return int(self.get("custom", "threads", "5"))
        except ValueError:
            return 5

    def get_timeout(self):
        try:
            return int(self.get("custom", "timeout", "10"))
        except ValueError:
            return 10


# ─────────────────────────────────────────────────
#  CUSTOMIZAÇÃO DIALOG
# ─────────────────────────────────────────────────

class CustomizationDialog:
    def __init__(self, parent, config_mgr, on_apply=None):
        self.parent = parent
        self.config = config_mgr
        self.on_apply = on_apply
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Customização Httpx")
        self.dialog.geometry("700x600")
        self.dialog.minsize(600, 500)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Notebook com abas
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ─── ABA 1: PRESETS DE FLAGS ───
        self._build_presets_tab()

        # ─── ABA 2: HEADERS E PORTAS ───
        self._build_headers_tab()

        # ─── ABA 3: PERFORMANCE ───
        self._build_performance_tab()

        # ─── ABA 4: COLUNAS ───
        self._build_columns_tab()

        # ─── ABA 5: ARGUMENTOS EXTRAS ───
        self._build_extra_tab()

        # Botões
        btn_frame = ttk.Frame(self.dialog, padding=(10, 5))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Aplicar", command=self._apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # Carregar valores atuais
        self._load_current_values()

    # ─── ABA DE PRESETS ───

    def _build_presets_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Presets de Flags")

        ttk.Label(frame, text="Salvar / Carregar / Deletar presets de flags customizadas",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)

        # Nome do preset
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill=tk.X, pady=(10, 5))
        ttk.Label(name_frame, text="Nome do Preset:").pack(side=tk.LEFT)
        self.preset_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.preset_name_var, width=30).pack(side=tk.LEFT, padx=10)

        # Flags do preset
        ttk.Label(frame, text="Flags:").pack(anchor=tk.W)
        self.preset_flags_text = scrolledtext.ScrolledText(frame, height=3, font=("Consolas", 9))
        self.preset_flags_text.pack(fill=tk.X, pady=(2, 10))

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="💾 Salvar Preset", command=self._save_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 Carregar", command=self._load_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 Deletar", command=self._delete_preset).pack(side=tk.LEFT, padx=5)

        # Lista de presets
        ttk.Label(frame, text="Presets Salvos:").pack(anchor=tk.W, pady=(5, 2))
        self.presets_listbox = tk.Listbox(frame, height=6)
        self.presets_listbox.pack(fill=tk.X, pady=2)
        self.presets_listbox.bind("<<ListboxSelect>>", self._on_preset_select)
        self._refresh_presets_list()

    def _refresh_presets_list(self):
        self.presets_listbox.delete(0, tk.END)
        for name in self.config.list_presets():
            self.presets_listbox.insert(tk.END, name)

    def _on_preset_select(self, event):
        sel = self.presets_listbox.curselection()
        if sel:
            name = self.presets_listbox.get(sel[0])
            self.preset_name_var.set(name)
            flags = self.config.load_preset(name)
            self.preset_flags_text.delete("1.0", tk.END)
            self.preset_flags_text.insert("1.0", flags)

    def _save_preset(self):
        name = self.preset_name_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Digite um nome para o preset.")
            return
        flags = self.preset_flags_text.get("1.0", tk.END).strip()
        if not flags:
            messagebox.showwarning("Aviso", "Digite as flags para salvar.")
            return
        self.config.save_preset(name, flags)
        self._refresh_presets_list()
        messagebox.showinfo("Sucesso", f"Preset '{name}' salvo!")

    def _load_preset(self):
        sel = self.presets_listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um preset na lista.")
            return
        name = self.presets_listbox.get(sel[0])
        flags = self.config.load_preset(name)
        self.preset_name_var.set(name)
        self.preset_flags_text.delete("1.0", tk.END)
        self.preset_flags_text.insert("1.0", flags)

    def _delete_preset(self):
        sel = self.presets_listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um preset na lista.")
            return
        name = self.presets_listbox.get(sel[0])
        if messagebox.askyesno("Confirmar", f"Deletar preset '{name}'?"):
            self.config.delete_preset(name)
            self._refresh_presets_list()
            self.preset_name_var.set("")
            self.preset_flags_text.delete("1.0", tk.END)

    # ─── ABA DE HEADERS E PORTAS ───

    def _build_headers_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Headers & Portas")

        # Headers customizados
        ttk.Label(frame, text="Headers Customizados (Header: Valor, um por linha):",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.headers_text = scrolledtext.ScrolledText(frame, height=6, font=("Consolas", 9))
        self.headers_text.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="Exemplo:\nX-Custom-Header: valor123\nAuthorization: Bearer token",
                  font=("Consolas", 8), foreground="gray").pack(anchor=tk.W)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Portas customizadas
        ttk.Label(frame, text="Portas Customizadas (separadas por vírgula):",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.ports_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ports_var, font=("Consolas", 10), width=50).pack(fill=tk.X, pady=2)
        ttk.Label(frame, text="Exemplo: 80, 443, 8080, 8443, 3000",
                  font=("Consolas", 8), foreground="gray").pack(anchor=tk.W)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Métodos HTTP
        ttk.Label(frame, text="Método HTTP (GET, POST, PUT, etc):",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.method_var = tk.StringVar(value="GET")
        methods_frame = ttk.Frame(frame)
        methods_frame.pack(fill=tk.X, pady=2)
        for m in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
            ttk.Radiobutton(methods_frame, text=m, variable=self.method_var,
                          value=m).pack(side=tk.LEFT, padx=5)

    # ─── ABA DE PERFORMANCE ───

    def _build_performance_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Performance")

        ttk.Label(frame, text="Configurações de Rate Limiting e Timeout",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)

        # Threads
        ttk.Label(frame, text="Threads (concorrência):", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(15, 2))
        threads_frame = ttk.Frame(frame)
        threads_frame.pack(fill=tk.X)
        self.threads_var = tk.IntVar(value=5)
        ttk.Spinbox(threads_frame, from_=1, to=500, textvariable=self.threads_var,
                    width=8, font=("Consolas", 10)).pack(side=tk.LEFT)
        ttk.Label(threads_frame, text=" (2–3 muito fraco | 4–5 fraco | 5–10 médio | 10–20 forte | 50 muito forte)").pack(side=tk.LEFT, padx=5)

        # Timeout
        ttk.Label(frame, text="Timeout (segundos):", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(10, 2))
        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill=tk.X)
        self.timeout_var = tk.IntVar(value=10)
        ttk.Spinbox(timeout_frame, from_=1, to=120, textvariable=self.timeout_var,
                    width=8, font=("Consolas", 10)).pack(side=tk.LEFT)
        ttk.Label(timeout_frame, text="  (por requisição individual)").pack(side=tk.LEFT, padx=5)

        # Retries
        ttk.Label(frame, text="Retries (tentativas em falha):", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(10, 2))
        retries_frame = ttk.Frame(frame)
        retries_frame.pack(fill=tk.X)
        self.retries_var = tk.IntVar(value=0)
        ttk.Spinbox(retries_frame, from_=0, to=10, textvariable=self.retries_var,
                    width=8, font=("Consolas", 10)).pack(side=tk.LEFT)
        ttk.Label(retries_frame, text="  (0 = sem retry)").pack(side=tk.LEFT, padx=5)

        # Rate limit (ms)
        ttk.Label(frame, text="Delay entre requisições (ms):", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(10, 2))
        rate_frame = ttk.Frame(frame)
        rate_frame.pack(fill=tk.X)
        self.rate_limit_var = tk.IntVar(value=0)
        ttk.Spinbox(rate_frame, from_=0, to=5000, textvariable=self.rate_limit_var,
                    width=8, font=("Consolas", 10), increment=50).pack(side=tk.LEFT)
        ttk.Label(rate_frame, text="  (0 = sem delay, 1000 = 1 por segundo)").pack(side=tk.LEFT, padx=5)

    # ─── ABA DE COLUNAS ───

    def _build_columns_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Colunas Visíveis")

        ttk.Label(frame, text="Selecione quais colunas aparecem na tabela:",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)

        self.col_vars = {}
        all_columns = [
            ("url", "URL", True),
            ("status_code", "Status Code", True),
            ("title", "Título", True),
            ("location", "Location (Redirecionamento)", True),
            ("cname", "CNAME", True),
            ("technologies", "Tecnologias", True),
            ("webserver", "Web Server", True),
            ("content_type", "Content-Type", True),
            ("content_length", "Tamanho", True),
            ("response_time", "Tempo", True),
        ]

        col_frame = ttk.Frame(frame)
        col_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        for i, (col_key, col_label, default) in enumerate(all_columns):
            var = tk.BooleanVar(value=default)
            self.col_vars[col_key] = var
            cb = ttk.Checkbutton(col_frame, text=col_label, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)

    # ─── ABA DE ARGUMENTOS EXTRAS ───

    def _build_extra_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Args Extras")

        ttk.Label(frame, text="Argumentos Extras (qualquer flag que o httpx aceita):",
                  font=("Segoe UI", 10)).pack(anchor=tk.W)
        ttk.Label(frame, text="Coloque aqui flags que não estão nos controles acima.",
                  foreground="gray").pack(anchor=tk.W)

        self.extra_args_text = scrolledtext.ScrolledText(frame, height=10, font=("Consolas", 10))
        self.extra_args_text.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(frame, text="Exemplos:\n  -H 'Cookie: session=abc123'\n  -probe\n  -follow-host-redirects\n  -max-response-body-size 1000000",
                  font=("Consolas", 8), foreground="gray").pack(anchor=tk.W)

        # Dicas rápidas
        ttk.Label(frame, text="Dicas:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 2))
        tips_text = tk.Text(frame, height=5, font=("Consolas", 8), wrap=tk.WORD)
        tips_text.pack(fill=tk.X)
        tips_text.insert(tk.END, """Flags úteis que você pode adicionar:
-use-hosts            Usar arquivo hosts ao invés de DNS
-follow-host-redirects Seguir redirecionamento entre hosts diferentes
-store-response       Salvar respostas em disco
-omit-content-length  Não exibir content-length
-max-response-body-size Tamanho máximo do corpo da resposta (bytes)
-rate-limit           Taxa de requisições por segundo""")
        tips_text.config(state=tk.DISABLED)

    # ─── CARREGAR / APLICAR ───

    def _load_current_values(self):
        # Headers
        self.headers_text.delete("1.0", tk.END)
        self.headers_text.insert("1.0", self.config.get("custom", "headers", ""))

        # Portas
        self.ports_var.set(self.config.get("custom", "ports", ""))

        # Performance
        self.threads_var.set(self.config.get_threads())
        self.timeout_var.set(self.config.get_timeout())
        self.retries_var.set(int(self.config.get("custom", "retries", "0")))
        self.rate_limit_var.set(int(self.config.get("custom", "rate_limit", "0")))

        # Extra args
        self.extra_args_text.delete("1.0", tk.END)
        self.extra_args_text.insert("1.0", self.config.get("custom", "extra_args", ""))

        # Método
        self.method_var.set(self.config.get("custom", "method", "GET"))

        # Colunas
        col_state = self.config.get("columns", "visible", "url,status_code,title,location,cname,technologies,webserver,content_type,content_length,response_time")
        visible = [c.strip() for c in col_state.split(",") if c.strip()]
        for key, var in self.col_vars.items():
            var.set(key in visible)

    def _apply(self):
        # Salvar headers
        self.config.set("custom", "headers", self.headers_text.get("1.0", tk.END).strip())

        # Portas
        self.config.set("custom", "ports", self.ports_var.get().strip())

        # Performance
        self.config.set("custom", "threads", str(self.threads_var.get()))
        self.config.set("custom", "timeout", str(self.timeout_var.get()))
        self.config.set("custom", "retries", str(self.retries_var.get()))
        self.config.set("custom", "rate_limit", str(self.rate_limit_var.get()))

        # Extra args
        self.config.set("custom", "extra_args", self.extra_args_text.get("1.0", tk.END).strip())

        # Método
        self.config.set("custom", "method", self.method_var.get())

        # Colunas visíveis
        visible_cols = [k for k, v in self.col_vars.items() if v.get()]
        self.config.set("columns", "visible", ",".join(visible_cols))

        if self.on_apply:
            self.on_apply()

        messagebox.showinfo("Sucesso", "Configurações aplicadas!")
        self.dialog.destroy()


# ─────────────────────────────────────────────────
#  Httpx GUI (MODIFICADA)
# ─────────────────────────────────────────────────

class HttpxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scan httpx custom")
        self.root.geometry("1250x750")
        self.root.minsize(950, 550)

        # Config manager
        self.config_mgr = ConfigManager()

        # Variáveis de estado
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.custom_flags = tk.StringVar(
            value=self.config_mgr.get("flags", "default",
                   "-location -title -cname -probe -td -status-code -mc 200,301 -json -stream -sd")
        )
        self.raw_results = []
        self.running = False
        self.process = None
        self.total_hosts = 0
        self.results_count = 0

        self._build_ui()
        self._center_window()
        self._apply_column_visibility()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 1250, 750
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ──────────────────────────────────────────────
    #  CONSTRUÇÃO DA INTERFACE
    # ──────────────────────────────────────────────

    def _build_ui(self):
        # ========== TOP FRAME ==========
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        # Selecionar arquivo de entrada
        ttk.Label(top, text="Arquivo de Hosts:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(top, textvariable=self.input_file, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="📂 Selecionar", command=self._select_input).grid(row=0, column=2, padx=5)

        # Arquivo de saída
        ttk.Label(top, text="Salvar Resultados:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        ttk.Entry(top, textvariable=self.output_file, width=60).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(top, text="💾 Salvar Como", command=self._select_output).grid(row=1, column=2, padx=5, pady=5)

        # Flags exibidas (label informativa)
        flags_frame = ttk.LabelFrame(top, text="Flags do httpx", padding=5)
        flags_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(5, 0))
        ttk.Label(flags_frame, text=(
            "-location  -title  -cname  -probe  -td  -status-code  -mc 200,301  -json  -stream  -sd"
        ), font=("Consolas", 9)).pack(anchor=tk.W)

        # ─── CUSTOM FLAGS (ENTRY EDITÁVEL) ───
        custom_frame = ttk.Frame(top)
        custom_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(4, 0))
        ttk.Label(custom_frame, text="Custom Flags:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_custom_flags = ttk.Entry(
            custom_frame, textvariable=self.custom_flags, font=("Consolas", 9)
        )
        self.entry_custom_flags.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Botão para restaurar flags padrão
        ttk.Button(
            custom_frame, text="↺ Padrão",
            command=self._reset_default_flags
        ).pack(side=tk.LEFT, padx=(5, 0))

        # BOTÃO CUSTOMIZAR
        ttk.Button(
            custom_frame, text="⚙ Customizar",
            command=self._open_customization
        ).pack(side=tk.LEFT, padx=(5, 0))

        # ========== BOTÕES ==========
        btn_frame = ttk.Frame(self.root, padding=(10, 5))
        btn_frame.pack(fill=tk.X)

        self.btn_run = ttk.Button(btn_frame, text="▶  EXECUTAR", command=self._run_httpx)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(btn_frame, text="⏹  PARAR", command=self._stop_httpx, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_save = ttk.Button(btn_frame, text="💾  TXT", command=self._save_results,
                                    state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_save_html = ttk.Button(btn_frame, text="🌐  HTML", command=self._save_results_html,
                                         state=tk.DISABLED)
        self.btn_save_html.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(btn_frame, text="🗑  Limpar", command=self._clear_results)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # INFO: total hosts + resultados
        self.lbl_info = ttk.Label(btn_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_info.pack(side=tk.RIGHT, padx=10)

        # ========== BARRA DE PROGRESSO (0-100%) ==========
        progress_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        progress_frame.pack(fill=tk.X)

        self.lbl_progress = ttk.Label(progress_frame, text="0%", width=5, anchor=tk.E,
                                       font=("Consolas", 9, "bold"))
        self.lbl_progress.pack(side=tk.RIGHT, padx=(5, 0))

        self.progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            value=0,
            maximum=100,
        )
        self.progress.pack(fill=tk.X, expand=True, padx=(0, 5))

        self.lbl_progress_text = ttk.Label(progress_frame, text="Aguardando...", anchor=tk.W, width=30)
        self.lbl_progress_text.pack(side=tk.LEFT)

        # ========== TABELA DE RESULTADOS ==========
        tree_frame = ttk.Frame(self.root, padding=(10, 0))
        tree_frame.pack(fill=tk.BOTH, expand=True)

        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.columns = (
            "url", "status_code", "title", "location",
            "cname", "technologies", "webserver", "content_type",
            "content_length", "response_time"
        )
        col_labels = {
            "url": "URL",
            "status_code": "Status",
            "title": "Título",
            "location": "Location (Redirecionamento)",
            "cname": "CNAME",
            "technologies": "Tecnologias (td)",
            "webserver": "Web Server",
            "content_type": "Content-Type",
            "content_length": "Tamanho",
            "response_time": "Tempo",
        }

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.columns,
            show="headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            selectmode="extended",
            height=18,
        )

        # Larguras das colunas (cada um em sua linha)
        self.col_widths = {
            "url": 700,
            "status_code": 65,
            "title": 400,
            "location": 500,
            "cname": 500,
            "technologies": 600,
            "webserver": 200,
            "content_type": 200,
            "content_length": 100,
            "response_time": 85,
        }

        self.col_labels = col_labels

        for col in self.columns:
            self.tree.heading(col, text=col_labels.get(col, col))
            self.tree.column(col, width=self.col_widths.get(col, 100), minwidth=60,
                           anchor=tk.W if col != "status_code" else tk.CENTER,
                           stretch=False)   # <--- CORREÇÃO: stretch=False

        # Tag para colorir status
        self.tree.tag_configure("status_200", foreground="#006600")
        self.tree.tag_configure("status_301", foreground="#996600")

        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._show_detail)

        # ========== LOG EM TEMPO REAL ==========
        log_frame = ttk.Frame(self.root, padding=(10, 5))
        log_frame.pack(fill=tk.X)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=5, font=("Consolas", 9),
            wrap=tk.WORD, state=tk.DISABLED,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self._log("Pronto. Selecione um arquivo .txt com hosts e clique em EXECUTAR.")

    # ──────────────────────────────────────────────
    #  CUSTOMIZAÇÃO
    # ──────────────────────────────────────────────

    def _open_customization(self):
        CustomizationDialog(self.root, self.config_mgr, on_apply=self._on_customization_apply)

    def _on_customization_apply(self):
        """Chamado quando o usuário clica Aplicar no diálogo de customização."""
        self._apply_column_visibility()
        self._log("⚙ Configurações customizadas aplicadas.")

    def _apply_column_visibility(self):
        """Aplica quais colunas estão visíveis baseado na config."""
        col_state = self.config_mgr.get("columns", "visible",
                                         "url,status_code,title,location,cname,technologies,webserver,content_type,content_length,response_time")
        visible = [c.strip() for c in col_state.split(",") if c.strip()]

        for col in self.columns:
            if col in visible:
                self.tree.column(col, width=self.col_widths.get(col, 100), minwidth=60)
                self.tree.heading(col, text=self.col_labels.get(col, col))
            else:
                self.tree.column(col, width=0, minwidth=0, stretch=False)

    # ──────────────────────────────────────────────
    #  CUSTOM FLAGS
    # ──────────────────────────────────────────────

    def _reset_default_flags(self):
        """Restaura o valor padrão das flags."""
        self.custom_flags.set("-location -title -cname -probe -td -status-code -mc 200,301 -json -stream -sd")
        self._log("Flags restauradas para o padrão.")

    def _parse_custom_flags(self):
        """Converte a string de flags em uma lista de argumentos para o subprocess."""
        raw = self.custom_flags.get().strip()
        if not raw:
            self._log("Nenhuma flag customizada definida — usando nenhuma flag extra.")
            return []

        # Parse respeitando aspas
        flags = []
        current = ""
        in_quote = False
        quote_char = None
        for c in raw:
            if in_quote:
                if c == quote_char:
                    in_quote = False
                else:
                    current += c
            elif c in ('"', "'"):
                in_quote = True
                quote_char = c
            elif c.isspace():
                if current:
                    flags.append(current)
                    current = ""
            else:
                current += c
        if current:
            flags.append(current)

        return flags

    # ──────────────────────────────────────────────
    #  LOG
    # ──────────────────────────────────────────────

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    # ──────────────────────────────────────────────
    #  SELEÇÃO DE ARQUIVOS
    # ──────────────────────────────────────────────

    def _select_input(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo de hosts",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.input_file.set(path)
            basename = os.path.splitext(os.path.basename(path))[0]
            outdir = os.path.dirname(path)
            self.output_file.set(os.path.join(outdir, f"{basename}_resultados.txt"))

            try:
                with open(path, "r") as f:
                    count = sum(1 for line in f if line.strip())
                self.total_hosts = count
                self.lbl_info.config(text=f"📋 {count} hosts no arquivo")
            except:
                pass

    def _select_output(self):
        path = filedialog.asksaveasfilename(
            title="Salvar resultados como",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.output_file.set(path)

    # ──────────────────────────────────────────────
    #  EXECUÇÃO COM STREAMING EM TEMPO REAL
    # ──────────────────────────────────────────────

    def _run_httpx(self):
        if self.running:
            messagebox.showwarning("Aviso", "Já existe uma execução em andamento.")
            return

        input_path = self.input_file.get().strip()
        if not input_path:
            messagebox.showerror("Erro", "Selecione um arquivo de hosts primeiro.")
            return
        if not os.path.isfile(input_path):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{input_path}")
            return

        if not self._check_httpx():
            return

        try:
            with open(input_path, "r") as f:
                self.total_hosts = sum(1 for line in f if line.strip())
        except:
            self.total_hosts = 0

        if self.total_hosts == 0:
            messagebox.showerror("Erro", "Arquivo de hosts está vazio.")
            return

        self.running = True
        self.results_count = 0
        self.raw_results = []
        self.btn_run.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.DISABLED)
        self.btn_save_html.config(state=tk.DISABLED)
        self.btn_clear.config(state=tk.DISABLED)

        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        self.lbl_progress_text.config(text=f"0 / {self.total_hosts} hosts")
        self.lbl_info.config(text=f"📋 {self.total_hosts} hosts | 🔄 Escaneando...")

        for item in self.tree.get_children():
            self.tree.delete(item)

        self._log(f"Iniciando scan em: {input_path}")
        self._log(f"Total de hosts: {self.total_hosts}")
        self._log("Streaming ativado - resultados aparecerão em tempo real!")

        cmd = ["httpx", "-l", input_path]

        custom_args = self._parse_custom_flags()
        cmd.extend(custom_args)

        headers = self.config_mgr.get_custom_headers()
        for h_name, h_value in headers.items():
            cmd.extend(["-H", f"{h_name}: {h_value}"])

        ports = self.config_mgr.get_custom_ports()
        if ports:
            cmd.extend(["-ports", ",".join(ports)])

        threads = self.config_mgr.get_threads()
        cmd.extend(["-threads", str(threads)])

        timeout = self.config_mgr.get_timeout()
        cmd.extend(["-timeout", str(timeout)])

        extra_raw = self.config_mgr.get("custom", "extra_args", "")
        if extra_raw.strip():
            extra_args = self._parse_flags_with_quotes(extra_raw)
            cmd.extend(extra_args)

        cmd_str = " ".join(cmd)
        self._log(f"Comando: {cmd_str}")

        thread = threading.Thread(target=self._execute_stream, args=(cmd,), daemon=True)
        thread.start()

    def _parse_flags_with_quotes(self, raw):
        flags = []
        current = ""
        in_single = False
        in_double = False
        i = 0
        while i < len(raw):
            c = raw[i]
            if c == "'" and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            elif c.isspace() and not in_single and not in_double:
                if current:
                    flags.append(current)
                    current = ""
            else:
                current += c
            i += 1
        if current:
            flags.append(current)
        return flags

    def _check_httpx(self):
        try:
            subprocess.run(["httpx", "-version"], capture_output=True, timeout=5)
            return True
        except FileNotFoundError:
            messagebox.showerror(
                "Erro",
                "httpx não encontrado no PATH.\n\n"
                "Instalação:\n"
                "  go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest\n"
                "  ou: sudo apt install httpx (Kali Linux)"
            )
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar httpx:\n{e}")
            return False

    def _execute_stream(self, cmd):
        try:
            final_cmd = cmd[:]
            if platform.system() == "Linux":
                final_cmd = ["stdbuf", "-oL"] + final_cmd

            self.process = subprocess.Popen(
                final_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            stderr_thread.start()

            for line in iter(self.process.stdout.readline, ""):
                if not line or not self.running:
                    break
                line = line.strip()
                if not line:
                    continue
                self.root.after(0, self._process_line, line)

            self.process.wait()

        except Exception as e:
            self.root.after(0, self._log, f"ERRO na execução: {e}")
        finally:
            self.root.after(0, self._finish_run)

    def _read_stderr(self):
        if not self.process:
            return
        try:
            for line in iter(self.process.stderr.readline, ""):
                if line.strip():
                    self.root.after(0, self._log, f"[stderr] {line.strip()[:200]}")
        except:
            pass

    def _process_line(self, line):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            self._log(f"[ignorado] linha inválida: {line[:100]}")
            return

        self.raw_results.append(data)
        self.results_count += 1

        techs = data.get("technologies", []) or data.get("tech", [])
        if isinstance(techs, list):
            tech_str = ", ".join(techs) if techs else ""
        else:
            tech_str = str(techs)

        cname = data.get("cname", "")
        if isinstance(cname, list):
            cname = ", ".join(cname) if cname else ""

        sc = data.get("status_code", data.get("status-code", ""))

        values = (
            data.get("url", ""),
            str(sc),
            data.get("title", "") or "",
            data.get("location", "") or "",
            cname,
            tech_str,
            data.get("webserver", "") or "",
            data.get("content_type", "") or "",
            str(data.get("content_length", "") or ""),
            str(data.get("response_time", "") or ""),
        )

        tags = ()
        if str(sc) == "200":
            tags = ("status_200",)
        elif str(sc) == "301":
            tags = ("status_301",)

        self.tree.insert("", 0, values=values, tags=tags)

        if self.total_hosts > 0:
            pct = min(int(self.results_count / self.total_hosts * 100), 99)
            self.progress["value"] = pct
            self.lbl_progress.config(text=f"{pct}%")
            self.lbl_progress_text.config(text=f"{self.results_count} / {self.total_hosts} hosts respondendo")
            self.lbl_info.config(text=f"📋 {self.total_hosts} hosts | ✅ {self.results_count} respondendo")

    def _stop_httpx(self):
        if self.process and self.running:
            self._log("⛔ Parada solicitada pelo usuário.")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.running = False

    def _finish_run(self):
        self.running = False
        self.process = None

        self.btn_run.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_clear.config(state=tk.NORMAL)

        if self.raw_results:
            self.btn_save.config(state=tk.NORMAL)
            self.btn_save_html.config(state=tk.NORMAL)

        self.progress["value"] = 100
        self.lbl_progress.config(text="100%")
        self.lbl_progress_text.config(text=f"{self.results_count} / {self.total_hosts} hosts (concluído)")
        self.lbl_info.config(text=f"📋 {self.total_hosts} hosts | ✅ {self.results_count} resultados")

        self._log(f"Scan concluído. {self.results_count} hosts respondendo (200/301) de {self.total_hosts} totais.")

    # ──────────────────────────────────────────────
    #  SALVAR RESULTADOS EM TXT
    # ──────────────────────────────────────────────

    def _save_results(self):
        if not self.raw_results:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return

        output_path = self.output_file.get().strip()
        if not output_path:
            output_path = filedialog.asksaveasfilename(
                title="Salvar resultados como TXT",
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            )
            if not output_path:
                return
            self.output_file.set(output_path)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                header = (
                    f"{'URL':<50} {'Status':<8} {'Título':<40} {'Location':<50} "
                    f"{'CNAME':<35} {'Tecnologias':<30} {'Server':<15} "
                    f"{'Content-Type':<25} {'Tam':<10} {'Tempo':<8}\n"
                )
                f.write(header)
                f.write("=" * 271 + "\n")

                for data in self.raw_results:
                    techs = data.get("technologies", []) or data.get("tech", [])
                    tech_str = ", ".join(techs) if isinstance(techs, list) and techs else str(techs)

                    cname = data.get("cname", "")
                    if isinstance(cname, list):
                        cname = ", ".join(cname) if cname else ""

                    line = (
                        f"{str(data.get('url', '')):<50} "
                        f"{str(data.get('status_code', '')):<8} "
                        f"{str(data.get('title', ''))[:38]:<40} "
                        f"{str(data.get('location', ''))[:48]:<50} "
                        f"{str(cname)[:33]:<35} "
                        f"{str(tech_str)[:28]:<30} "
                        f"{str(data.get('webserver', ''))[:13]:<15} "
                        f"{str(data.get('content_type', ''))[:23]:<25} "
                        f"{str(data.get('content_length', '')):<10} "
                        f"{str(data.get('response_time', '')):<8}\n"
                    )
                    f.write(line)

                f.write("\n" + "=" * 271 + "\n")
                f.write(f"Resumo: {len(self.raw_results)} hosts respondendo (200/301)\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            self._log(f"Resultados TXT salvos em: {output_path}")
            messagebox.showinfo("Sucesso", f"Resultados salvos em TXT:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo:\n{e}")

    # ──────────────────────────────────────────────
    #  SALVAR RESULTADOS EM HTML
    # ──────────────────────────────────────────────

    def _save_results_html(self):
        if not self.raw_results:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return

        txt_path = self.output_file.get().strip()
        if txt_path:
            html_path = os.path.splitext(txt_path)[0] + "_report.html"
        else:
            html_path = ""

        output_path = filedialog.asksaveasfilename(
            title="Salvar relatório HTML",
            initialfile=os.path.basename(html_path) if html_path else "httpx_report.html",
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
        )
        if not output_path:
            return

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total = len(self.raw_results)

            status_counts = {}
            for d in self.raw_results:
                sc = str(d.get("status_code", d.get("status-code", "")))
                status_counts[sc] = status_counts.get(sc, 0) + 1

            status_badges = ""
            for sc in sorted(status_counts.keys()):
                color = "#28a745" if sc == "200" else "#fd7e14" if sc == "301" else "#dc3545"
                status_badges += f'<span class="badge" style="background:{color}">{sc}: {status_counts[sc]}</span>\n'

            table_rows = ""
            for i, data in enumerate(self.raw_results, 1):
                url = data.get("url", "")
                sc = str(data.get("status_code", data.get("status-code", "")))
                title = (data.get("title") or "")[:60]
                location = (data.get("location") or "")[:60]
                cname = data.get("cname", "")
                if isinstance(cname, list):
                    cname = ", ".join(cname) if cname else ""
                techs = data.get("technologies", []) or data.get("tech", [])
                if isinstance(techs, list):
                    tech_str = ", ".join(techs[:5])
                else:
                    tech_str = str(techs)
                webserver = data.get("webserver", "") or ""
                content_type = (data.get("content_type", "") or "")[:30]
                content_length = str(data.get("content_length", "") or "")
                response_time = str(data.get("response_time", "") or "")

                sc_color = "#28a745" if sc == "200" else "#fd7e14" if sc == "301" else "#dc3545"
                tech_badges = ""
                if tech_str:
                    for t in tech_str.split(", ")[:5]:
                        t = t.strip()
                        if t:
                            tech_badges += f'<span class="tech-badge">{t}</span> '

                url_display = url[:80] + "..." if len(url) > 80 else url

                table_rows += f"""\
                <tr>
                    <td class="url-cell" title="{url}"><a href="{url}" target="_blank">{url_display}</a></td>
                    <td><span class="status-code" style="color:{sc_color};font-weight:bold">{sc}</span></td>
                    <td>{title}</td>
                    <td class="loc-cell">{location}</td>
                    <td>{cname}</td>
                    <td class="tech-cell">{tech_badges}</td>
                    <td>{webserver}</td>
                    <td>{content_type}</td>
                    <td class="num">{content_length}</td>
                    <td class="num">{response_time}</td>
                </tr>
"""

            html = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>httpx Scan Report - {now}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f5f7fa;
    color: #333;
    padding: 30px;
}}
.container {{
    max-width: 1400px;
    margin: 0 auto;
}}
.header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}}
.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header .sub {{ opacity: 0.85; font-size: 14px; }}
.stats {{ display: flex; gap: 15px; flex-wrap: wrap; margin-top: 15px; }}
.stat-card {{ background: rgba(255,255,255,0.12); padding: 12px 20px; border-radius: 8px; text-align: center; min-width: 100px; }}
.stat-card .num {{ font-size: 24px; font-weight: 700; }}
.stat-card .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }}
.badges {{ margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }}
.badge {{ padding: 4px 12px; border-radius: 20px; color: #fff; font-size: 12px; font-weight: 600; }}
.table-wrap {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #1a1a2e; color: #fff; }}
th {{ padding: 12px 10px; text-align: left; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }}
tbody tr {{ border-bottom: 1px solid #e9ecef; transition: background 0.15s; }}
tbody tr:hover {{ background: #f0f4ff; }}
td {{ padding: 10px; vertical-align: middle; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.url-cell {{ max-width: 300px; }}
.url-cell a {{ color: #0066cc; text-decoration: none; }}
.url-cell a:hover {{ text-decoration: underline; }}
.loc-cell {{ max-width: 200px; }}
.tech-cell {{ max-width: 250px; }}
.tech-badge {{ display: inline-block; background: #e7f3ff; color: #0066cc; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin: 2px; white-space: nowrap; }}
.num {{ text-align: right; font-family: 'Consolas', monospace; }}
.footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; margin-top: 20px; }}
@media (max-width: 900px) {{ .stats {{ flex-direction: column; }} table {{ font-size: 12px; }} td, th {{ padding: 8px 6px; }} }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔍 httpx Scan Report</h1>
        <div class="sub">Gerado em {now}</div>
        <div class="stats">
            <div class="stat-card"><div class="num">{total}</div><div class="label">Total de Hosts</div></div>
            <div class="stat-card"><div class="num">{len(set(d.get('url','') for d in self.raw_results))}</div><div class="label">URLs Únicas</div></div>
            <div class="stat-card"><div class="num">{total}</div><div class="label">Resultados</div></div>
        </div>
        <div class="badges">{status_badges}</div>
    </div>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>URL</th><th>Status</th><th>Título</th><th>Location</th><th>CNAME</th><th>Tecnologias</th><th>Server</th><th>Content-Type</th><th>Tamanho</th><th>Tempo</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    <div class="footer">Gerado por Httpx GUI v2 &mdash; {now}</div>
</div>
</body>
</html>"""

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            self._log(f"Relatório HTML salvo em: {output_path}")
            messagebox.showinfo("Sucesso", f"Relatório HTML salvo em:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar HTML:\n{e}")

    # ──────────────────────────────────────────────
    #  LIMPAR
    # ──────────────────────────────────────────────

    def _clear_results(self):
        if self.running:
            messagebox.showwarning("Aviso", "Pare a execução antes de limpar.")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.raw_results = []
        self.results_count = 0
        self.btn_save.config(state=tk.DISABLED)
        self.btn_save_html.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        self.lbl_progress_text.config(text="Aguardando...")
        if self.total_hosts > 0:
            self.lbl_info.config(text=f"📋 {self.total_hosts} hosts no arquivo")
        else:
            self.lbl_info.config(text="")
        self._log("Resultados limpos.")

    # ──────────────────────────────────────────────
    #  DETALHES (duplo clique)
    # ──────────────────────────────────────────────

    def _show_detail(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.tree.item(item, "values")
        url = values[0] if values else ""

        data = None
        for d in self.raw_results:
            if d.get("url") == url:
                data = d
                break

        if not data:
            return

        detail = tk.Toplevel(self.root)
        detail.title(f"Detalhes: {url}")
        detail.geometry("750x550")
        detail.transient(self.root)
        detail.grab_set()

        txt = scrolledtext.ScrolledText(detail, font=("Consolas", 10), wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        txt.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
        txt.config(state=tk.DISABLED)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        messagebox.showerror("Erro", "Python 3.7+ é necessário.")
        sys.exit(1)

    root = tk.Tk()
    app = HttpxGUI(root)
    root.mainloop()
