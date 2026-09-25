#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
msfconsole interativo em modo gráfico (Kali Linux)
Mostra TODOS os tipos de módulos na busca (exploit, auxiliary, post, etc.)
Painel de configuração completo com Canvas + Scrollbar, em 4 grupos,
e auto-preenchimento das opções a partir do 'show options'.
Console redimensionável com o mouse.
Uso: sudo python3 MetasploitGrafico.py
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

OPT_LINE_RE = re.compile(
    r"^\s*([A-Z][A-Z0-9_]{1,40})\s+(.*?)\s+(yes|no)\s*$", re.I)

TIPOS = ["Todos", "exploit", "auxiliary", "post", "payload", "encoder", "nop"]

GRUPOS = {
    "Conexão / Alvo": [
        ("RHOSTS",        "RHOSTS (alvo):",                     ""),
        ("RHOST",         "RHOST (alvo único legado):",         ""),
        ("RPORT",         "RPORT (porta alvo):",                ""),
        ("RPORTS",        "RPORTS (faixa de portas):",          ""),
        ("RHOSTS_FILE",   "RHOSTS_FILE (arquivo de alvos):",    ""),
        ("VHOST",         "VHOST (Host header/domínio):",       ""),
        ("TARGETURI",     "TARGETURI (URL):",                   ""),
        ("SESSION",       "SESSION:",                           ""),
        ("SESSIONS",      "SESSIONS (várias):",                 ""),
        ("TARGET",        "TARGET (ID do alvo):",               ""),
    ],
    "Autenticação": [
        ("USERNAME",      "USERNAME (usuário):",                ""),
        ("PASSWORD",      "PASSWORD (senha):",                  ""),
        ("USERPASS_FILE", "USERPASS_FILE:",                     ""),
        ("USER_FILE",     "USER_FILE (wordlist usuários):",     ""),
        ("PASS_FILE",     "PASS_FILE (wordlist senhas):",       ""),
        ("DOMAIN",        "DOMAIN (SMB/HTTP):",                 ""),
        ("SMBUser",       "SMBUser:",                           ""),
        ("SMBPass",       "SMBPass:",                           ""),
        ("SMBDomain",     "SMBDomain:",                         ""),
        ("HTTPUsername",  "HTTPUsername:",                      ""),
        ("HTTPPassword",  "HTTPPassword:",                      ""),
        ("FTPUSER",       "FTPUSER:",                           ""),
        ("FTPPASS",       "FTPPASS:",                           ""),
        ("SMTPUSER",      "SMTPUSER:",                          ""),
        ("SMTPPASS",      "SMTPPASS:",                          ""),
        ("DB_USERNAME",   "DB_USERNAME (banco):",               ""),
        ("DB_PASSWORD",   "DB_PASSWORD (banco):",               ""),
        ("BLANK_PASSWORDS","BLANK_PASSWORDS:",                  ""),
        ("USER_AS_PASS",  "USER_AS_PASS:",                      ""),
        ("STOP_ON_SUCCESS","STOP_ON_SUCCESS:",                  ""),
        ("BRUTEFORCE_SPEED","BRUTEFORCE_SPEED:",                "5"),
    ],
    "Payload / Web / Proxy": [
        ("PAYLOAD",       "Payload:",                           ""),
        ("LPORT",         "LPORT (porta local):",               ""),
        ("LHOST",         "LHOST (local):",                     ""),
        ("LURI",          "LURI (URI base do handler):",        ""),
        ("EXITFUNC",      "EXITFUNC:",                          "process"),
        ("ENCODER",       "ENCODER:",                           ""),
        ("SRVHOST",       "SRVHOST (servidor):",                ""),
        ("SRVPORT",       "SRVPORT (porta srv):",               ""),
        ("URIPATH",       "URIPATH:",                           ""),
        ("SSL",           "SSL:",                               ""),
        ("SSLCert",       "SSLCert (PEM):",                     ""),
        ("SSLVersion",    "SSLVersion:",                        "Auto"),
        ("HTTPHostHeader","HTTPHostHeader:",                    ""),
        ("UserAgent",     "UserAgent:",                         ""),
        ("ContentType",   "ContentType:",                       ""),
        ("Method",        "Method (HTTP):",                     ""),
        ("PROXIES",       "PROXIES (ex: http:127.0.0.1:8080):", ""),
        ("PROXY_TYPE",    "PROXY_TYPE:",                        ""),
        ("PROXY_HOST",    "PROXY_HOST:",                        ""),
        ("PROXY_PORT",    "PROXY_PORT:",                        ""),
    ],
    "Arquivos / Execução / Diversos": [
        ("PATH",          "PATH (arquivo):",                    ""),
        ("FILEPATH",      "FILEPATH (upload):",                 ""),
        ("FILENAME",      "FILENAME:",                          ""),
        ("LOCALFILE",     "LOCALFILE (download):",              ""),
        ("LFILE",         "LFILE (local):",                     ""),
        ("WfsDir",        "WfsDir (diretório loot):",           ""),
        ("STORE_LOOT",    "STORE_LOOT:",                        ""),
        ("LOOTDIR",       "LOOTDIR:",                           ""),
        ("THREADS",       "THREADS:",                           "1"),
        ("TIMEOUT",       "TIMEOUT:",                           ""),
        ("ConnectTimeout","ConnectTimeout:",                    ""),
        ("RUN_DELAY",     "RUN_DELAY (ms):",                    ""),
        ("PORTS",         "PORTS (scanner):",                   ""),
        ("SMBPort",       "SMBPort:",                           "445"),
        ("VERBOSE",       "VERBOSE:",                           ""),
        ("DEBUG",         "DEBUG:",                             ""),
        ("WORKSPACE",     "WORKSPACE:",                         ""),
        ("CHECK",         "CHECK:",                             ""),
        ("DeleteTempfiles","DeleteTempfiles:",                  ""),
        ("IterateHosts",  "IterateHosts:",                      ""),
    ],
}

CAMPOS = [(key, label, default)
          for campos in GRUPOS.values() for key, label, default in campos]


class MSFGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Metasploit Gráfico")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#1e1e1e")

        self.proc = None
        self.master_fd = None
        self.q = queue.Queue()
        self.modules = []
        self.current_module = None
        self.alive = True
        self.pending_search = False

        self._build_style()
        self._build_ui()
        self.start_msf()
        self.root.after(100, self._poll)

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#00ff88",
                        font=("Consolas", 10))
        style.configure("TButton", background="#2d2d2d", foreground="#00ff88",
                        font=("Consolas", 10, "bold"))
        style.configure("TEntry", fieldbackground="#121212", foreground="#ffffff")
        style.configure("Treeview", background="#0d0d0d", fieldbackground="#0d0d0d",
                        foreground="#00ff88", rowheight=22)
        style.configure("Treeview.Heading", background="#2d2d2d", foreground="#00ff88")
        style.configure("TLabelframe", background="#1e1e1e", foreground="#00ff88")
        style.configure("TLabelframe.Label", background="#1e1e1e", foreground="#00ff88",
                        font=("Consolas", 10, "bold"))
        style.configure("TPanedwindow", background="#1e1e1e")

    def _build_ui(self):
        # ---- 1. Barra de pesquisa ----
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Pesquisar módulo:").pack(side="left")
        self.search_entry = ttk.Entry(top, width=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        ttk.Button(top, text="Buscar", command=self.do_search).pack(side="left", padx=3)

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
        self.cmd_entry.bind("<Return>", lambda e: self.send_cmd(self.cmd_entry.get()))
        ttk.Button(cmd, text="Enviar",
                   command=lambda: self.send_cmd(self.cmd_entry.get())).pack(side="left")
        ttk.Button(cmd, text="Salvar log", command=self.save_log).pack(side="left", padx=3)

        # ---- 3. Botões principais ----
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=10, pady=2)
        ttk.Button(btns, text="USAR MÓDULO SELECIONADO",
                   command=lambda: self.use_selected(None)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="EXPLOIT / RUN (job)",
                   command=self.run_exploit).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="check (testa alvo)",
                   command=lambda: self.send_cmd("check")).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="sessions",
                   command=lambda: self.send_cmd("sessions")).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="jobs",
                   command=lambda: self.send_cmd("jobs -v")).pack(side="left", expand=True, fill="x", padx=2)

        # ---- 4. Configuração do módulo ----
        self.cfg_frame = ttk.LabelFrame(
            self.root, text="Configuração (módulo atual: nenhum)", padding=8)
        self.cfg_frame.pack(fill="x", padx=10, pady=3)

        # Botões de ação fixos embaixo do cfg
        acoes = ttk.Frame(self.cfg_frame)
        acoes.pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(acoes, text="Aplicar Opções (set)", command=self.apply_options).pack(side="left", padx=4)
        ttk.Button(acoes, text="info / options", command=self.show_info).pack(side="left", padx=4)
        ttk.Button(acoes, text="Limpar campos", command=self.clear_fields).pack(side="left", padx=4)
        ttk.Button(acoes, text="Limpar console",
                   command=lambda: self.output.delete("1.0", "end")).pack(side="left", padx=4)

        # Canvas + Scrollbar
        scroll_frame = ttk.Frame(self.cfg_frame)
        scroll_frame.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(scroll_frame, bg="#1e1e1e", highlightthickness=0, height=200)
        vsb = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _wheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.opt_vars = {}
        col = 0
        row_offset = 0
        max_r_in_row = 0
        group_counter = 0

        for group_name, campos in GRUPOS.items():
            r = row_offset
            ttk.Label(inner, text=f"— {group_name} —",
                      font=("Consolas", 10, "bold")).grid(row=r, column=col, columnspan=2, sticky="w", pady=(5, 0))
            r += 1
            for key, label, default in campos:
                ttk.Label(inner, text=label).grid(row=r, column=col, sticky="e")
                v = tk.StringVar(value=default)
                ttk.Entry(inner, textvariable=v, width=28).grid(row=r, column=col + 1, padx=5, pady=1)
                self.opt_vars[key] = v
                r += 1

            if r > max_r_in_row:
                max_r_in_row = r
            col += 2
            group_counter += 1
            if group_counter == 2:
                col = 0
                row_offset = max_r_in_row + 1
                group_counter = 0

        # ============================================================
        # 5 + 6.  PANED WINDOW (Treeview + Console redimensionável)
        # ============================================================
        paned = ttk.Panedwindow(self.root, orient="vertical")
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Painel de cima: Resultados da busca ---
        tree_frame = ttk.LabelFrame(paned, text="Resultados da Busca", padding=5)
        self.tree = ttk.Treeview(tree_frame, columns=("name", "rank", "check", "desc"),
                                 show="headings", height=8)
        for col_id, w, txt in (("name", 430, "Módulo"), ("rank", 90, "Rank"),
                               ("check", 60, "Check"), ("desc", 380, "Descrição")):
            self.tree.heading(col_id, text=txt)
            self.tree.column(col_id, width=w, anchor="w")
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.use_selected)

        paned.add(tree_frame, weight=1)

        # --- Painel de baixo: Console Metasploit (redimensionável) ---
        out_frame = ttk.LabelFrame(paned, text="Console Metasploit  (arraste a barra cinza para cima para aumentar)", padding=5)
        
        self.output = tk.Text(out_frame, bg="#0d0d0d", fg="#00ff88",
                              font=("Consolas", 10), wrap="word")
        sb = ttk.Scrollbar(out_frame, command=self.output.yview)
        self.output.config(yscrollcommand=sb.set)
        self.output.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        paned.add(out_frame, weight=3)   # weight maior = console começa maior

        # Dica visual
        self.log("[*] Dica: clique e arraste a barra divisória (entre Resultados e Console) para cima/baixo.\n")

    def log(self, text):
        self.output.insert("end", ANSI_RE.sub("", text))
        self.output.see("end")

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
        self.log("[*] Módulo lançado como job. Use 'sessions -i 1' no comando manual para interagir.\n")

    def save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output.get("1.0", "end"))
            self.log(f"\n[*] Log salvo em {path}\n")

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
                    self.modules.append((path, rank.lower(), check, rest.strip()))
                    continue

            om = OPT_LINE_RE.match(line)
            if om and self.current_module:
                name, value, _req = om.groups()
                if name in self.opt_vars:
                    self.opt_vars[name].set(value.strip())

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
