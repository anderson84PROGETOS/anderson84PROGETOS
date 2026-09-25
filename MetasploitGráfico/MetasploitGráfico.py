#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
msfconsole interativo em modo gráfico (Kali Linux)
Mostra TODOS os tipos de módulos na busca (exploit, auxiliary, post, etc.)
Painel de configuração com todos os campos comuns (RHOSTS, LHOST, RPORT,
USERNAME, PASSWORD, PATH, THREADS, etc.)
Uso: sudo python3 MetasploitGráfico.py

"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import queue
import os
import re
import time
import pty
import select

MSFCONSOLE = "/usr/bin/msfconsole"

# ---------------- Parser da busca do msf6 ----------------
RANK_WORDS = r"(?:manual|low|normal|good|great|excellent)"
MOD_PATH = r"((?:exploit|auxiliary|post|payload|encoder|nop)/\S+)"

SEARCH_RE = re.compile(
    rf"^\s*\d+\s+{MOD_PATH}\s+"
    r"(?:(\d{4}-\d{2}-\d{2})\s+)?"
    rf"({RANK_WORDS})\s+"
    r"(Yes|No)\s+"
    r"(.*)$",
    re.I,
)
SEARCH_RE_FALLBACK = re.compile(rf"^\s*\d+\s+{MOD_PATH}\s+(.*)$")

RANK_END_RE = re.compile(rf"\b{RANK_WORDS}\b\s*$", re.I)
CHECK_END_RE = re.compile(r"\s+(Yes|No)\s*$", re.I)

SKIP_RE = re.compile(
    r"(Matching Modules|^\s*=+|^\s*$|\[!|msf\d?\s*\[?\]?|Module "
    r"details|^Time|^\s*#?\s*Name|^\s*\^|Last updated)",
    re.I,
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

TIPOS = ["Todos", "exploit", "auxiliary", "post", "payload", "encoder", "nop"]

# Campos do painel de configuração (chave, rótulo, valor padrão sugerido)
CAMPOS = [
    ("RHOSTS",   "RHOSTS (alvo):",        ""),
    ("RPORT",    "RPORT (porta alvo):",   ""),
    ("LHOST",    "LHOST (local):",        ""),
    ("LPORT",    "LPORT (porta local):",  ""),
    ("PAYLOAD",  "Payload:",              ""),
    ("USERNAME", "USERNAME (usuário):",   ""),
    ("PASSWORD", "PASSWORD (senha):",     ""),
    ("PATH",     "PATH (arquivo):",       ""),
    ("TARGETURI","TARGETURI (URL):",      ""),
    ("THREADS",  "THREADS:",              "1"),
    ("SRVHOST",  "SRVHOST (servidor):",   ""),
    ("SRVPORT",  "SRVPORT (porta srv):",  ""),
    ("SESSION",  "SESSION:",              ""),
    ("TIMEOUT",  "TIMEOUT:",              ""),
]


class MSFGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Metasploit Gráfico")
        self.root.geometry("1150x800")
        self.root.minsize(950, 640)
        self.root.configure(bg="#1e1e1e")

        self.proc = None
        self.master_fd = None
        self.q = queue.Queue()
        self.modules = []
        self.current_module = None
        self.alive = True

        self._build_style()
        self._build_ui()
        self.start_msf()
        self.root.after(100, self._poll)

    # ---------------- Estilo ----------------
    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#00ff88",
                        font=("Consolas", 10))
        style.configure("TButton", background="#2d2d2d", foreground="#00ff88",
                        font=("Consolas", 10, "bold"))
        style.configure("TEntry", fieldbackground="#121212",
                        foreground="#ffffff")
        style.configure("Treeview", background="#0d0d0d",
                        fieldbackground="#0d0d0d",
                        foreground="#00ff88", rowheight=22)
        style.configure("Treeview.Heading", background="#2d2d2d",
                        foreground="#00ff88")

    # ---------------- Interface ----------------
    def _build_ui(self):
        # ---- 1. Barra de pesquisa ----
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Pesquisar módulo:").pack(side="left")
        self.search_entry = ttk.Entry(top, width=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        ttk.Button(top, text="Buscar", command=self.do_search).pack(side="left",
                                                                    padx=3)

        ttk.Label(top, text="Tipo:").pack(side="left", padx=(15, 3))
        self.tipo_var = tk.StringVar(value="Todos")
        cb = ttk.Combobox(top, textvariable=self.tipo_var, state="readonly",
                          width=10, values=TIPOS)
        cb.pack(side="left")

        # ---- 2. Comando manual ----
        cmd = ttk.LabelFrame(self.root, text="Comando manual", padding=5)
        cmd.pack(fill="x", padx=10, pady=3)
        ttk.Label(cmd, text="Comando:").pack(side="left")
        self.cmd_entry = ttk.Entry(cmd)
        self.cmd_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.cmd_entry.bind("<Return>",
                            lambda e: self.send_cmd(self.cmd_entry.get()))
        ttk.Button(cmd, text="Enviar",
                   command=lambda: self.send_cmd(self.cmd_entry.get())).pack(
            side="left")
        ttk.Button(cmd, text="Salvar log", command=self.save_log).pack(
            side="left", padx=3)

        # ---- 3. Botões principais ----
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=10, pady=2)
        ttk.Button(btns, text="USAR MÓDULO SELECIONADO",
                   command=lambda: self.use_selected(None)).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="EXPLOIT / RUN (job)",
                   command=self.run_exploit).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="check (testa alvo)",
                   command=lambda: self.send_cmd("check")).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="sessions",
                   command=lambda: self.send_cmd("sessions")).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="jobs",
                   command=lambda: self.send_cmd("jobs -v")).pack(
            side="left", expand=True, fill="x", padx=2)

        # ---- 4. Configuração do módulo (expandida, em 2 colunas) ----
        self.cfg_frame = ttk.LabelFrame(
            self.root, text="Configuração (módulo atual: nenhum)", padding=8)
        self.cfg_frame.pack(fill="x", padx=10, pady=3)

        self.opt_vars = {}
        # Coluna 1: opções de conexão
        ttk.Label(self.cfg_frame, text="— Conexão —").grid(
            row=0, column=0, columnspan=2, sticky="w")
        row = 1
        for key, label, default in CAMPOS[:9]:
            ttk.Label(self.cfg_frame, text=label).grid(row=row, column=0,
                                                       sticky="e")
            v = tk.StringVar(value=default)
            ttk.Entry(self.cfg_frame, textvariable=v, width=38).grid(
                row=row, column=1, padx=5, pady=1)
            self.opt_vars[key] = v
            row += 1

        # Coluna 2: opções avançadas
        ttk.Label(self.cfg_frame, text="— Avançado —").grid(
            row=0, column=2, columnspan=2, sticky="w")
        row = 1
        for key, label, default in CAMPOS[9:]:
            ttk.Label(self.cfg_frame, text=label).grid(row=row, column=2,
                                                       sticky="e")
            v = tk.StringVar(value=default)
            ttk.Entry(self.cfg_frame, textvariable=v, width=38).grid(
                row=row, column=3, padx=5, pady=1)
            self.opt_vars[key] = v
            row += 1

        # Botões de ação da configuração
        acoes = ttk.Frame(self.cfg_frame)
        acoes.grid(row=10, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(acoes, text="Aplicar Opções (set)",
                   command=self.apply_options).pack(side="left", padx=4)
        ttk.Button(acoes, text="info / options",
                   command=self.show_info).pack(side="left", padx=4)
        ttk.Button(acoes, text="Limpar campos",
                   command=self.clear_fields).pack(side="left", padx=4)
        ttk.Button(acoes, text="Limpar console",
                   command=lambda: self.output.delete("1.0", "end")).pack(
            side="left", padx=4)

        # ---- 5. Resultados da busca ----
        self.tree = ttk.Treeview(self.root, columns=("name", "rank", "check",
                                                     "desc"),
                                 show="headings", height=6)
        for col, w, txt in (("name", 430, "Módulo"), ("rank", 90, "Rank"),
                            ("check", 60, "Check"), ("desc", 380, "Descrição")):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="x", padx=10, pady=3)
        self.tree.bind("<Double-1>", self.use_selected)

        # ---- 6. Console ----
        out_frame = ttk.LabelFrame(self.root, text="Console Metasploit",
                                   padding=5)
        out_frame.pack(fill="both", expand=True, padx=10, pady=3)
        self.output = tk.Text(out_frame, bg="#0d0d0d", fg="#00ff88",
                              font=("Consolas", 10), wrap="word")
        self.output.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(out_frame, command=self.output.yview)
        sb.pack(side="right", fill="y")
        self.output.config(yscrollcommand=sb.set)

    def log(self, text):
        self.output.insert("end", ANSI_RE.sub("", text))
        self.output.see("end")

    # ---------------- msfconsole ----------------
    def start_msf(self):
        self.log("[*] Iniciando msfconsole...\n")
        self.master_fd, slave_fd = pty.openpty()
        self.proc = subprocess.Popen(
            [MSFCONSOLE, "-q"],
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            start_new_session=True, close_fds=True
        )
        os.close(slave_fd)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buf = b""
        try:
            while self.alive and self.proc and self.proc.poll() is None:
                r, _, _ = select.select([self.master_fd], [], [], 0.2)
                if not r:
                    if buf:
                        self.q.put(buf.decode(errors="replace"))
                        buf = b""
                    continue
                try:
                    chunk = os.read(self.master_fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    self.q.put(line.decode(errors="replace") + "\n")
            if buf:
                self.q.put(buf.decode(errors="replace") + "\n")
        finally:
            self.q.put("\n[!] msfconsole foi encerrado.\n")

    def send_cmd(self, cmd, echo=True):
        cmd = cmd.rstrip()
        if not cmd:
            return
        if not self.proc or self.proc.poll() is not None:
            self.log("\n[!] msfconsole não está em execução.\n")
            return
        try:
            os.write(self.master_fd, (cmd + "\n").encode())
            if echo:
                self.log(f"\nmsf6 > {cmd}\n")
        except Exception as e:
            self.log(f"\n[!] Falha: {e}\n")

    # ---------------- Busca ----------------
    def do_search(self):
        term = self.search_entry.get().strip()
        if not term:
            return
        self.modules = []
        self.tree.delete(*self.tree.get_children())
        tipo = self.tipo_var.get()
        if tipo == "Todos":
            self.send_cmd(f"search {term}")
        else:
            self.send_cmd(f"search type:{tipo} {term}")

    # ---------------- Usar módulo ----------------
    def use_selected(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        name = str(values[0])
        self.current_module = name
        self.cfg_frame.config(text=f"Configuração (módulo atual: {name})")
        self.log(f"\n[*] Carregando módulo: {name}\n")
        self.send_cmd(f"use {name}")
        threading.Timer(1.0, lambda: self.send_cmd("show options")).start()

    # ---------------- Ações ----------------
    def apply_options(self):
        if not self.current_module:
            messagebox.showwarning("Atenção", "Selecione um módulo primeiro.")
            return
        for key, var in self.opt_vars.items():
            val = var.get().strip()
            if val:
                if " " in val:
                    val = f'"{val}"'
                self.send_cmd(f"set {key} {val}")

    def clear_fields(self):
        for var in self.opt_vars.values():
            var.set("")

    def show_info(self):
        if not self.current_module:
            messagebox.showwarning("Atenção", "Selecione um módulo primeiro.")
            return
        self.send_cmd("info")
        threading.Timer(1.0, lambda: self.send_cmd("show options")).start()

    def run_exploit(self):
        if not self.current_module:
            messagebox.showwarning("Atenção", "Selecione um módulo primeiro.")
            return
        if self.current_module.startswith("auxiliary"):
            self.send_cmd("run -j")
        else:
            self.send_cmd("exploit -j -z")
        self.log("[*] Módulo lançado como job. Use 'sessions -i 1' no comando "
                 "manual para interagir.\n")

    def save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output.get("1.0", "end"))
            self.log(f"\n[*] Log salvo em {path}\n")

    # ---------------- Fila de saída + parser ----------------
    def _poll(self):
        while not self.q.empty():
            raw = self.q.get()
            self.log(raw)
            line = ANSI_RE.sub("", raw)
            if SKIP_RE.search(line):
                continue
            m = SEARCH_RE.match(line)
            if m:
                path, date, rank, check, desc = m.groups()
                desc = RANK_END_RE.sub("", desc or "").strip()
                desc = CHECK_END_RE.sub("", desc).strip()
                self.modules.append((path, rank.lower(), check, desc))
            else:
                m2 = SEARCH_RE_FALLBACK.match(line)
                if m2:
                    path, rest = m2.groups()
                    rank = ""
                    rm = RANK_END_RE.search(rest)
                    if rm:
                        rank = rm.group(0).strip()
                        rest = RANK_END_RE.sub("", rest)
                    cm = CHECK_END_RE.search(rest)
                    check = ""
                    if cm:
                        check = cm.group(1)
                        rest = CHECK_END_RE.sub("", rest)
                    self.modules.append(
                        (path, rank.lower(), check, rest.strip()))
        if self.modules:
            for name, rank, check, desc in self.modules:
                self.tree.insert("", "end", values=(name, rank, check, desc))
            self.modules = []
        self.root.after(100, self._poll)

    def on_close(self):
        self.alive = False
        try:
            if self.proc and self.proc.poll() is None:
                self.send_cmd("exit", echo=False)
                time.sleep(0.5)
                self.proc.terminate()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MSFGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
