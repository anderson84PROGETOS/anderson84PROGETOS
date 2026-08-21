#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
import socket
import time
import os
import sys
import json
import csv
from queue import Queue, Empty
from datetime import datetime

TIMEOUT = 10

USER_AGENT = (
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) "
    "AppleWebKit/537.51.2 (KHTML, like Gecko) "
    "Version/7.0 Mobile/11D201 Safari/9537.53"
)


class GoBusterGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Domínio e Subdomínios")
        self.root.geometry("1100x800")

        # =====================================================
        # MAXIMIZAR
        # =====================================================

        for attr in ("zoomed", "-zoomed"):
            try:
                if attr == "zoomed":
                    self.root.state(attr)
                else:
                    self.root.attributes(attr, True)
            except tk.TclError:
                pass

        # =====================================================
        # CONTROLE
        # =====================================================

        self.running = False
        self.stop_event = threading.Event()

        self.threads_list = []

        self.results = []

        self.results_queue = Queue()
        self.log_queue = Queue()
        self.progress_queue = Queue()

        self.counter_lock = threading.Lock()

        self.total_words = 0
        self.processed_words = 0
        self.start_time = None

        # =====================================================
        # GUI
        # =====================================================

        self._build_ui()

        self._update_log()
        self._update_results()
        self._update_progress()

    # =========================================================
    # EXTENSÕES
    # =========================================================

    def _toggle_extensions(self):

        if self.use_ext_var.get():
            self.ext_entry.config(state=tk.NORMAL)
        else:
            self.ext_entry.config(state=tk.DISABLED)

    # =========================================================
    # GUI
    # =========================================================

    def _build_ui(self):

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # =====================================================
        # CONFIGURAÇÕES
        # =====================================================

        cfg = ttk.LabelFrame(
            main,
            text="Configurações do Scan",
            padding=10
        )

        cfg.pack(fill=tk.X, pady=(0, 5))

        # =====================================================
        # LINHA 1
        # =====================================================

        r1 = ttk.Frame(cfg)
        r1.pack(fill=tk.X, pady=2)

        ttk.Label(r1, text="Modo:").pack(side=tk.LEFT)

        self.mode_var = tk.StringVar(value="dir (Domínio)")

        self.mode_cb = ttk.Combobox(r1, textvariable=self.mode_var, values=["dir (Domínio)", "dns (Subdomínios)"],
            state="readonly",
            width=20
        )

        self.mode_cb.pack(side=tk.LEFT, padx=5)

        self.mode_cb.bind("<<ComboboxSelected>>", self._on_mode_change)

        ttk.Label(r1, text="Alvo:").pack(side=tk.LEFT, padx=(10, 0))

        self.target_var = tk.StringVar(value="businesscorp.com.br")

        ttk.Entry(r1, textvariable=self.target_var).pack(
            side=tk.LEFT,
            padx=5,
            fill=tk.X,
            expand=True
        )

        # =====================================================
        # LINHA 2
        # =====================================================

        r2 = ttk.Frame(cfg)
        r2.pack(fill=tk.X, pady=2)

        ttk.Label(r2, text="Wordlist:").pack(side=tk.LEFT)

        self.wl_var = tk.StringVar()

        ttk.Entry(r2, textvariable=self.wl_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(r2, text="Procurar...", command=self._browse_wl).pack(side=tk.LEFT, padx=2)

        self.btn_common = ttk.Button(r2, text="Wordlists Comuns", command=self._show_common_wl)

        self.btn_common.pack(side=tk.LEFT, padx=2)

        # =====================================================
        # LINHA 3
        # =====================================================

        r3 = ttk.Frame(cfg)
        r3.pack(fill=tk.X, pady=2)

        ttk.Label(r3, text="Threads:").pack(side=tk.LEFT)

        self.threads_var = tk.StringVar(value="5")

        ttk.Spinbox(
            r3,
            from_=1,
            to=100,
            textvariable=self.threads_var,
            width=6
        ).pack(
            side=tk.LEFT,
            padx=5
        )

        ttk.Label(
            r3,
            text="Extensões:"
        ).pack(
            side=tk.LEFT,
            padx=(10, 0)
        )

        self.use_ext_var = tk.BooleanVar(
            value=False
        )

        ttk.Checkbutton(
            r3,
            text="Usar",
            variable=self.use_ext_var,
            command=self._toggle_extensions
        ).pack(
            side=tk.LEFT,
            padx=(5, 2)
        )

        self.ext_var = tk.StringVar(
            value="php,html,txt,bak,zip,sql,json"
        )

        self.ext_entry = ttk.Entry(
            r3,
            textvariable=self.ext_var,
            width=22,
            state=tk.DISABLED
        )

        self.ext_entry.pack(
            side=tk.LEFT,
            padx=5
        )

        ttk.Label(
            r3,
            text="Filtrar Status:"
        ).pack(
            side=tk.LEFT,
            padx=(10, 0)
        )

        self.filter_var = tk.StringVar(
            value="200,204,301,302"
        )

        ttk.Entry(
            r3,
            textvariable=self.filter_var,
            width=20
        ).pack(
            side=tk.LEFT,
            padx=5
        )

        self.ignore_ssl_var = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(
            r3,
            text="Ignorar SSL",
            variable=self.ignore_ssl_var
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        self.show_ips_var = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(r3, text="Mostrar IPs (DNS)", variable=self.show_ips_var).pack(side=tk.LEFT)

        # =====================================================
        # CONTROLES
        # =====================================================

        ctrl = ttk.Frame(main)

        ctrl.pack(fill=tk.X, pady=5)

        self.btn_start = ttk.Button(ctrl, text="▶ INICIAR SCAN", command=self._start)

        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_stop = ttk.Button(ctrl, text="⏹ PARAR", command=self._stop, state=tk.DISABLED)

        self.btn_stop.pack(side=tk.LEFT, padx=2)

        ttk.Button(ctrl, text="💾 Exportar", command=self._export).pack(side=tk.LEFT, padx=2)

        ttk.Button(ctrl, text="🗑 Limpar", command=self._clear).pack(side=tk.LEFT, padx=2)

        self.lbl_progress = ttk.Label(ctrl, text="")

        self.lbl_progress.pack(side=tk.RIGHT, padx=5)

        self.lbl_status = ttk.Label(ctrl, text="✅ Pronto")

        self.lbl_status.pack(side=tk.RIGHT, padx=5)

        # =====================================================
        # PROGRESSO
        # =====================================================

        self.progress = ttk.Progressbar(main, maximum=100)

        self.progress.pack(fill=tk.X, pady=5)

        # =====================================================
        # RESULTADOS
        # =====================================================

        res = ttk.LabelFrame(main, text="📋 Resultados Encontrados", padding=5)

        res.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(res, columns=("status", "size", "extra"), show="tree headings")

        # =====================================================
        # CABEÇALHO CORRETO
        # =====================================================

        self._update_tree_heading()

        self.tree.heading("status", text="Status")

        self.tree.heading("size", text="Tamanho")

        self.tree.heading("extra", text="IP / Redirecionamento")

        self.tree.column("#0", width=480, stretch=True)

        self.tree.column("status", width=70,  anchor=tk.CENTER)

        self.tree.column("size", width=80, anchor=tk.CENTER)

        self.tree.column("extra", width=280, stretch=True)

        # =====================================================
        # CORES DOS RESULTADOS
        # =====================================================

        status_colors = {
            "200": "#28a745",
            "204": "#6c757d",
            "301": "#fd7e14",
            "302": "#fd7e14",
            "307": "#fd7e14",
            "401": "#dc3545",
            "403": "#dc3545",
            "500": "#dc3545",
            "found": "#17a2b8"
        }

        for code, color in status_colors.items():

            self.tree.tag_configure(
                code,
                foreground=color
            )

        # =====================================================
        # SCROLLBAR
        # =====================================================

        vsb = ttk.Scrollbar(
            res,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=vsb.set
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vsb.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        res.grid_rowconfigure(
            0,
            weight=1
        )

        res.grid_columnconfigure(
            0,
            weight=1
        )

        # =====================================================
        # LOG
        # =====================================================

        log_frame = ttk.LabelFrame(
            main,
            text="📝 Log de Execução",
            padding=5
        )

        log_frame.pack(
            fill=tk.X
        )

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=18,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD
        )

        self.log_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        for tag, color in {
            "error": "#f44747",
            "warn": "#ffcc00",
            "info": "#6a9955",
            "debug": "#569cd6",
            "found": "#4ec9b0"
        }.items():

            self.log_text.tag_configure(
                tag,
                foreground=color
            )

        # =====================================================
        # LOG INICIAL
        # =====================================================

        self._log(
            "SISTEMA",
            (
                f"Enumeração de Domínio e Subdomínios Python "
                f"{sys.version_info.major}."
                f"{sys.version_info.minor} | "
                f"requests {requests.__version__}\n"
            ),
            "info"
        )

    # =========================================================
    # CABEÇALHO DA TREEVIEW
    # =========================================================

    def _update_tree_heading(self):

        mode = self.mode_var.get().lower()

        if "dns" in mode:

            self.tree.heading(
                "#0",
                text="dns (Subdomínio)"
            )

        else:

            self.tree.heading(
                "#0",
                text="dir (Domínio)"
            )

    # =========================================================
    # LOG
    # =========================================================

    def _log(
        self,
        tag,
        msg,
        level="debug"
    ):

        self.log_queue.put(
            (tag, msg, level)
        )

    def _update_log(self):

        try:

            while True:

                tag, msg, level = (
                    self.log_queue.get_nowait()
                )

                self.log_text.insert(
                    tk.END,
                    f"{tag} {msg}\n",
                    level
                )

                self.log_text.see(
                    tk.END
                )

        except Empty:
            pass

        self.root.after(
            150,
            self._update_log
        )

    # =========================================================
    # RESULTADOS
    # =========================================================

    def _update_results(self):

        try:

            while True:

                r = self.results_queue.get_nowait()

                self.results.append(r)

                extra = (
                    r.get("extra")
                    or r.get("ip")
                    or r.get("redirect", "")
                )

                tag = r.get(
                    "tag",
                    str(r.get("status", "found"))
                )

                self.tree.insert(
                    "",
                    tk.END,
                    text=r.get("url", ""),
                    values=(
                        r.get("status", ""),
                        r.get("size", "-"),
                        extra
                    ),
                    tags=(tag,)
                )

        except Empty:
            pass

        self.root.after(
            100,
            self._update_results
        )

    # =========================================================
    # PROGRESSO
    # =========================================================

    def _increment_progress(self):

        with self.counter_lock:

            self.processed_words += 1

            p = self.processed_words
            t = self.total_words
            s = self.start_time

        if p % 5 == 0 or p >= t:

            self.progress_queue.put(
                (p, t, s)
            )

    def _update_progress(self):

        try:

            while True:

                p, total, start = (
                    self.progress_queue.get_nowait()
                )

                if total <= 0:
                    continue

                pct = (
                    p / total
                ) * 100

                elapsed = (
                    time.time() - start
                    if start else 0
                )

                wps = (
                    p / elapsed
                    if elapsed > 0
                    else 0
                )

                eta = (
                    (total - p) / wps
                    if wps
                    else 0
                )

                self.progress["value"] = pct

                self.lbl_progress.config(
                    text=(
                        f"{p}/{total} "
                        f"({pct:.0f}%) | "
                        f"{wps:.0f} w/s | "
                        f"ETA: {eta:.0f}s"
                    )
                )

        except Empty:
            pass

        self.root.after(
            100,
            self._update_progress
        )

    # =========================================================
    # DNS
    # =========================================================

    @staticmethod
    def _clean_dns_word(word):

        if not isinstance(word, str):
            return None

        word = word.strip().lower()

        if not word:
            return None

        for proto in (
            "https://",
            "http://"
        ):

            if word.startswith(proto):

                word = word[
                    len(proto):
                ]

        word = (
            word
            .split("/")[0]
            .strip()
        )

        if ":" in word:

            word = word.split(
                ":",
                1
            )[0]

        word = word.strip(".")

        if (
            not word
            or ".." in word
            or len(word) > 253
        ):

            return None

        allowed = (
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789-."
        )

        if any(
            c not in allowed
            for c in word
        ):

            return None

        labels = word.split(".")

        if any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            for label in labels
        ):

            return None

        return word

    @staticmethod
    def _valid_hostname(hostname):

        if not isinstance(
            hostname,
            str
        ):

            return False

        hostname = (
            hostname
            .rstrip(".")
            .lower()
        )

        if (
            not hostname
            or len(hostname) > 253
        ):

            return False

        try:

            ascii_host = (
                hostname
                .encode("idna")
                .decode("ascii")
            )

        except (
            UnicodeError,
            UnicodeEncodeError
        ):

            return False

        labels = ascii_host.split(".")

        return all(
            label
            and len(label) <= 63
            and not label.startswith("-")
            and not label.endswith("-")
            and all(
                c.isalnum() or c == "-"
                for c in label
            )
            for label in labels
        )

    @staticmethod
    def _normalize_domain(domain):

        if not domain:
            return None

        domain = (
            domain
            .strip()
            .lower()
        )

        for proto in (
            "https://",
            "http://"
        ):

            if domain.startswith(proto):

                domain = domain[
                    len(proto):
                ]

        domain = domain.split("/")[0]
        domain = domain.split("?", 1)[0]
        domain = domain.split("#", 1)[0]

        domain = (
            domain
            .strip()
            .rstrip(".")
        )

        if ":" in domain:

            domain = domain.split(
                ":",
                1
            )[0]

        if not GoBusterGUI._valid_hostname(
            domain
        ):

            return None

        return domain

    # =========================================================
    # WORDLIST
    # =========================================================

    def _browse_wl(self):

        path = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[
                (
                    "Wordlists",
                    "*.txt *.lst"
                ),
                (
                    "Todos",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        self.wl_var.set(path)

        try:

            with open(
                path,
                encoding="utf-8",
                errors="ignore"
            ) as f:

                count = sum(
                    1
                    for line in f
                    if line.strip()
                )

            self._log("WORDLIST", f"Selecionada: {path}\n", "info")

            self._log("WORDLIST", f"{count} linhas válidas\n", "info")

        except Exception as exc:

            self._log("\nWORDLIST", f"Erro: {exc}\n", "error")

    def _show_common_wl(self):

        paths = {

            "dirb common.txt":
                "/usr/share/wordlists/dirb/common.txt",

            "dirb big.txt":
                "/usr/share/wordlists/dirb/big.txt",

            "dirbuster medium":
                "/usr/share/wordlists/dirbuster/"
                "directory-list-2.3-medium.txt",

            "SecLists Web-Content common":
                "/usr/share/seclists/Discovery/"
                "Web-Content/common.txt",

            "SecLists raft-large":
                "/usr/share/seclists/Discovery/"
                "Web-Content/raft-large-directories.txt",

            "SecLists subdomains 5000":
                "/usr/share/seclists/Discovery/"
                "DNS/subdomains-top1million-5000.txt",

            "SecLists subdomains 20000":
                "/usr/share/seclists/Discovery/"
                "DNS/subdomains-20000.txt"
        }

        menu = tk.Menu(
            self.root,
            tearoff=0
        )

        for name, path in paths.items():

            exists = os.path.exists(path)

            label = (
                f"{'✅' if exists else '❌'} "
                f"{name}"
            )

            if not exists:

                label += (
                    " (não encontrado)"
                )

            menu.add_command(
                label=label,
                command=lambda p=path:
                    self._set_wl(p)
            )

        menu.tk_popup(
            self.btn_common.winfo_rootx(),
            (
                self.btn_common.winfo_rooty()
                + self.btn_common.winfo_height()
            )
        )

    def _set_wl(self, path):

        self.wl_var.set(path)

        exists = os.path.exists(path)

        self._log(
            "WORDLIST",
            (
                f"{'✅' if exists else '⚠'} "
                f"{path}"
            ),
            "info" if exists else "warn"
        )

    # =========================================================
    # MODO
    # =========================================================

    def _on_mode_change(self, event=None):

        dns = (
            "dns"
            in self.mode_var.get().lower()
        )

        # Atualiza o cabeçalho
        self._update_tree_heading()

        # Extensões não são usadas no DNS
        if dns:

            self.ext_entry.config(
                state=tk.DISABLED
            )

            self.ext_var.set(
                "(n/a para DNS)"
            )

        else:

            self.ext_entry.config(
                state=tk.NORMAL
            )

            self.ext_var.set(
                "php,html,txt,bak,zip,sql,json"
            )

    # =========================================================
    # START
    # =========================================================

    def _start(self):

        if self.running:

            messagebox.showwarning(
                "Scan",
                "Já existe um scan em execução."
            )

            return

        target = (
            self.target_var
            .get()
            .strip()
        )

        wl_path = (
            self.wl_var
            .get()
            .strip()
        )

        if not target:

            messagebox.showerror(
                "Erro",
                "Informe o alvo!"
            )

            return

        if not os.path.isfile(
            wl_path
        ):

            messagebox.showerror(
                "Erro",
                "Selecione uma wordlist válida!"
            )

            return

        mode = (
            "dns"
            if "dns"
            in self.mode_var.get().lower()
            else "dir"
        )

        # =====================================================
        # LER WORDLIST
        # =====================================================

        try:

            with open(
                wl_path,
                encoding="utf-8",
                errors="ignore"
            ) as f:

                words = list(
                    dict.fromkeys(
                        line.strip()
                        for line in f
                        if line.strip()
                    )
                )

        except Exception as exc:

            messagebox.showerror(
                "Erro",
                f"Erro ao ler wordlist:\n{exc}"
            )

            return

        if not words:

            messagebox.showerror(
                "Erro",
                "Wordlist vazia!"
            )

            return

        # =====================================================
        # THREADS
        # =====================================================

        try:

            threads = max(
                1,
                min(
                    int(
                        self.threads_var.get()
                    ),
                    100
                )
            )

        except ValueError:

            messagebox.showerror(
                "Erro",
                "Threads deve ser um número inteiro."
            )

            return

        # =====================================================
        # STATUS
        # =====================================================

        status_filter = {

            int(x.strip())

            for x in self.filter_var
            .get()
            .split(",")

            if x.strip().isdigit()
        }

        # =====================================================
        # EXTENSÕES
        # =====================================================

        extensions = []

        if (
            mode == "dir"
            and self.use_ext_var.get()
        ):

            raw = (
                self.ext_var
                .get()
                .strip()
            )

            if (
                raw
                and raw != "(n/a para DNS)"
            ):

                extensions = [

                    (
                        x.strip()
                        if x.strip().startswith(".")
                        else "." + x.strip()
                    )

                    for x in raw.split(",")

                    if x.strip()
                ]

        # =====================================================
        # DNS
        # =====================================================

        if mode == "dns":

            target = self._normalize_domain(
                target
            )

            if not target:

                messagebox.showerror(
                    "DNS",
                    "Domínio inválido.\n\n"
                    "Exemplo válido: "
                    "businesscorp.com.br"
                )

                return

            valid_words = []
            invalid = 0

            for word in words:

                clean = (
                    self._clean_dns_word(word)
                )

                if clean:

                    valid_words.append(
                        clean
                    )

                else:

                    invalid += 1

            words = list(
                dict.fromkeys(
                    valid_words
                )
            )

            if invalid:

                self._log("\nDNS",(f"⚠ {invalid} "
                        f"entrada inválida "
                        f"removida\n"
                    ),
                    "warn"
                )

            if not words:

                messagebox.showerror("\nDNS", "Nenhuma entrada DNS válida " "na wordlist\n")

                return

            try:

                ip = socket.getaddrinfo(
                    target,
                    None,
                    type=socket.SOCK_STREAM
                )[0][4][0]

                self._log("DNS",(f"🌐 {target:<40} "f"-> {ip}\n"), "info")

            except (
                socket.gaierror,
                UnicodeError
            ) as exc:

                self._log("DNS",(f"⚠ Não resolveu " f"{target:<40}: {exc}\n"),"warn")

        # =====================================================
        # DOMÍNIO / DIRETÓRIOS
        # =====================================================

        else:

            if not target.startswith(
                (
                    "http://",
                    "https://"
                )
            ):

                target = (
                    "http://"
                    + target
                )

            target = target.rstrip("/")

            try:

                r = requests.get(
                    target,
                    timeout=5,
                    headers={
                        "User-Agent": USER_AGENT
                    },
                    verify=not self.ignore_ssl_var.get()
                )

                self._log("\nSCAN", (f"✅ Alvo respondeu: "
                        f"HTTP {r.status_code} "
                        f"({len(r.content)} bytes)\n"
                    ),
                    "info"
                )

            except requests.RequestException as exc:

                self._log(
                    "SCAN",
                    (
                        f"⚠ Alvo não respondeu: "
                        f"{exc}"
                    ),
                    "warn"
                )

        # =====================================================
        # INICIALIZAÇÃO
        # =====================================================

        self.running = True

        self.stop_event.clear()

        self.results.clear()

        self.tree.delete(
            *self.tree.get_children()
        )

        with self.counter_lock:

            self.total_words = len(words)
            self.processed_words = 0
            self.start_time = time.time()

        self.progress["value"] = 0

        self.lbl_progress.config(
            text=f"0/{len(words)}"
        )

        self.lbl_status.config(
            text="▶ Rodando..."
        )

        self.btn_start.config(
            state=tk.DISABLED
        )

        self.btn_stop.config(
            state=tk.NORMAL
        )

        q = Queue()

        for word in words:
            q.put(word)

        self.threads_list = []

        show_ips = (
            self.show_ips_var.get()
        )

        worker_count = min(
            threads,
            len(words)
        )

        for _ in range(
            worker_count
        ):

            if mode == "dns":

                args = (
                    q,
                    target,
                    show_ips
                )

                worker = (
                    self._dns_worker
                )

            else:

                args = (
                    q,
                    target,
                    extensions,
                    status_filter,
                    self.ignore_ssl_var.get()
                )

                worker = (
                    self._dir_worker
                )

            t = threading.Thread(
                target=worker,
                args=args,
                daemon=True
            )

            t.start()

            self.threads_list.append(t)

        threading.Thread(
            target=self._monitor,
            daemon=True
        ).start()

        self._log(
            "SCAN",
            (
                f"🚀 Scan iniciado | "
                f"Modo: {mode.upper()} | "
                f"Threads: {worker_count} | "
                f"Entradas: {len(words)}\n\n"
            ),
            "info"
        )

    # =========================================================
    # DIRETÓRIOS
    # =========================================================

    def _dir_worker(
        self,
        queue,
        base_url,
        extensions,
        status_filter,
        ignore_ssl
    ):

        session = requests.Session()

        session.headers.update({
            "User-Agent": USER_AGENT
        })

        while not self.stop_event.is_set():

            try:

                word = queue.get(
                    timeout=.5
                )

            except Empty:

                break

            try:

                if extensions:

                    targets = [
                        f"{base_url}/{word}{ext}"
                        for ext in extensions
                    ]

                else:

                    targets = [
                        f"{base_url}/{word}"
                    ]

                for url in targets:

                    if self.stop_event.is_set():
                        break

                    try:

                        r = session.get(
                            url,
                            timeout=TIMEOUT,
                            verify=not ignore_ssl,
                            allow_redirects=False
                        )

                        if (
                            not status_filter
                            or r.status_code
                            in status_filter
                        ):

                            location = (
                                r.headers
                                .get(
                                    "Location",
                                    ""
                                )
                            )

                            size = len(
                                r.content
                            )

                            self._log(
                                "DIR",
                                (
                                    f"✅ "
                                    f"{r.status_code} | "
                                    f"{url:<60} | "
                                    f"{size} bytes"
                                ),
                                "found"
                            )

                            self.results_queue.put({

                                "url": url,

                                "status":
                                    r.status_code,

                                "size":
                                    size,

                                "extra":
                                    location,

                                "tag":
                                    str(
                                        r.status_code
                                    )
                            })

                    except requests.exceptions.SSLError:

                        self._log(
                            "DIR",
                            f"❌ SSL | {url}",
                            "error"
                        )

                    except requests.exceptions.ConnectionError:

                        self._log(
                            "DIR",
                            f"❌ CONN | {url}",
                            "error"
                        )

                    except requests.exceptions.Timeout:

                        pass

                    except requests.RequestException as exc:

                        self._log(
                            "DIR",
                            (
                                f"❌ HTTP | "
                                f"{url} | {exc}"
                            ),
                            "debug"
                        )

            finally:

                queue.task_done()

                self._increment_progress()

    # =========================================================
    # DNS WORKER
    # =========================================================

    def _dns_worker(
        self,
        queue,
        domain,
        show_ips
    ):

        while not self.stop_event.is_set():

            try:

                word = queue.get(
                    timeout=.5
                )

            except Empty:

                break

            try:

                word = (
                    self._clean_dns_word(
                        word
                    )
                )

                if not word:
                    continue

                subdomain = (
                    f"{word}.{domain}"
                )

                if not self._valid_hostname(
                    subdomain
                ):

                    self._log(
                        "DNS",
                        (
                            "⚠ Hostname inválido "
                            f"ignorado: {subdomain}"
                        ),
                        "warn"
                    )

                    continue

                try:

                    infos = socket.getaddrinfo(
                        subdomain,
                        None,
                        type=socket.SOCK_STREAM
                    )

                    ips = []

                    for info in infos:

                        ip = info[4][0]

                        if ip not in ips:

                            ips.append(ip)

                    if not ips:
                        continue

                    ip_text = ", ".join(ips)

                    self._log(
                        "DNS",
                        (
                            f"✅ ENCONTRADO | "
                            f"{subdomain:<40} "
                            f"-> {ip_text}"
                        ),
                        "found"
                    )

                    self.results_queue.put({

                        "url":
                            subdomain,

                        "status":
                            200,

                        "size":
                            0,

                        "ip":
                            ip_text
                            if show_ips
                            else "",

                        "extra":
                            ip_text
                            if show_ips
                            else "",

                        "tag":
                            "found"
                    })

                except socket.gaierror:

                    pass

                except (
                    UnicodeError,
                    UnicodeEncodeError
                ) as exc:

                    self._log(
                        "DNS",
                        (
                            f"⚠ IDNA inválido "
                            f"ignorado: {subdomain} "
                            f"| {exc}"
                        ),
                        "warn"
                    )

                except OSError as exc:

                    self._log(
                        "DNS",
                        (
                            f"⚠ Erro DNS: "
                            f"{subdomain} | {exc}"
                        ),
                        "debug"
                    )

            finally:

                queue.task_done()

                self._increment_progress()

    # =========================================================
    # MONITOR
    # =========================================================

    def _monitor(self):

        for thread in self.threads_list:

            thread.join()

        self.threads_list = []

        with self.counter_lock:

            elapsed = (
                time.time()
                - self.start_time
                if self.start_time
                else 0
            )

        self.root.after(
            150,
            lambda: self._finish_when_empty(
                elapsed
            )
        )

    def _finish_when_empty(
        self,
        elapsed
    ):

        if not self.results_queue.empty():

            self.root.after(
                100,
                lambda: self._finish_when_empty(
                    elapsed
                )
            )

            return

        self.running = False

        self._finish(
            elapsed
        )

    def _finish(self, elapsed):

        found = len(
            self.results
        )

        self.progress["value"] = 100

        self.lbl_progress.config(
            text=(
                f"{self.total_words}/"
                f"{self.total_words} "
                f"(100%)"
            )
        )

        self.lbl_status.config(
            text=(
                f"✅ Concluído — "
                f"{found} Encontrado "
                f"em {elapsed:.1f}s"
            )
        )

        self.btn_start.config(
            state=tk.NORMAL
        )

        self.btn_stop.config(
            state=tk.DISABLED
        )

        self._log("\n\nSCAN",(f"✅ FINALIZADO — "
                f"{found} Resultado "
                f"em {elapsed:.1f}s"
            ),
            "info"
        )

        if not found:

            self._log("SCAN", "⚠ Nenhum Resultado Encontrado.", "warn")

    # =========================================================
    # PARAR
    # =========================================================

    def _stop(self):

        if not self.running:
            return

        self.stop_event.set()

        self.lbl_status.config(
            text="⏹ Interrompendo..."
        )

        self.btn_stop.config(
            state=tk.DISABLED
        )

        self._log("\n\nSCAN", "⏹ Scan interrompido pelo usuário.", "warn")

        self._wait_workers()

    def _wait_workers(self):

        if any(
            t.is_alive()
            for t in self.threads_list
        ):

            self.root.after(
                100,
                self._wait_workers
            )

            return

        self.threads_list = []

        self.running = False

        self.btn_start.config(
            state=tk.NORMAL
        )

        self.btn_stop.config(
            state=tk.DISABLED
        )

        self.lbl_status.config(
            text=(
                f"⏹ Interrompido — "
                f"{len(self.results)} Resultados"
            )
        )

        self._log(
            "SCAN",
            "⏹ Workers Encerrados",
            "warn"
        )

    # =========================================================
    # LIMPAR
    # =========================================================

    def _clear(self):

        if self.running:

            messagebox.showwarning(
                "Limpar",
                "Pare o scan antes de limpar."
            )

            return

        self.tree.delete(
            *self.tree.get_children()
        )

        self.results.clear()

        self.log_text.delete(
            "1.0",
            tk.END
        )

        self.progress["value"] = 0

        self.lbl_status.config(
            text="✅ Pronto"
        )

        self.lbl_progress.config(
            text=""
        )

        self._log(
            "SISTEMA",
            "🧹 Tudo limpo",
            "info"
        )

    # =========================================================
    # EXPORTAR
    # =========================================================

    def _export(self):

        if not self.results:

            messagebox.showinfo(
                "Exportar",
                "Nenhum Resultado para exportar."
            )

            return

        fname = filedialog.asksaveasfilename(

            title="Exportar Resultados",

            defaultextension=".html",

            filetypes=[

                (
                    "HTML",
                    "*.html"
                ),

                (
                    "Texto",
                    "*.txt"
                ),

                (
                    "CSV",
                    "*.csv"
                ),

                (
                    "JSON",
                    "*.json"
                ),

                (
                    "Todos",
                    "*.*"
                )
            ]
        )

        if not fname:
            return

        try:

            name = fname.lower()

            # =================================================
            # HTML
            # =================================================

            if name.endswith(".html"):

                from html import escape

                rows = []

                for r in self.results:

                    status = str(
                        r.get(
                            "status",
                            ""
                        )
                    )

                    url = escape(
                        str(
                            r.get(
                                "url",
                                ""
                            )
                        )
                    )

                    size = escape(
                        str(
                            r.get(
                                "size",
                                "-"
                            )
                        )
                    )

                    extra = escape(
                        str(
                            r.get(
                                "extra",
                                ""
                            )
                        )
                    )

                    if status in (
                        "200",
                        "204"
                    ):

                        status_class = "success"

                    elif status in (
                        "301",
                        "302",
                        "307"
                    ):

                        status_class = "redirect"

                    elif status in (
                        "401",
                        "403",
                        "500"
                    ):

                        status_class = "error"

                    else:

                        status_class = "status-info"

                    rows.append(
                        f"""
                        <tr>
                            <td class="url">
                                <a href="{url}" target="_blank">
                                    {url}
                                </a>
                            </td>

                            <td class="center">
                                <span class="status {status_class}">
                                    {escape(status)}
                                </span>
                            </td>

                            <td class="center">
                                {size}
                            </td>

                            <td>
                                {extra}
                            </td>
                        </tr>
                        """
                    )

                html = f"""<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>GoBusterGUI - Scan Results</title>

<style>

* {{
    box-sizing: border-box;
}}

html,
body {{
    margin: 0;
    padding: 0;
    min-height: 100%;
}}

body {{
    background: #0d1117;
    color: #c9d1d9;
    font-family: Consolas, "Courier New", monospace;
    padding: 30px;
}}

.container {{
    max-width: 1600px;
    margin: 0 auto;
}}

.header {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 20px;
}}

.header h1 {{
    margin: 0 0 20px 0;
    color: #00ff66;
    font-size: 28px;
}}

.info-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
}}

.info-box {{
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px;
    overflow-wrap: anywhere;
}}

.info-box strong {{
    display: block;
    color: #8b949e;
    font-size: 12px;
    margin-bottom: 7px;
}}

.info-box span {{
    color: #00ff66;
    word-break: break-word;
}}

.card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    overflow: hidden;
}}

.card-header {{
    padding: 18px 20px;
    border-bottom: 1px solid #30363d;
    color: #00ff66;
    font-size: 18px;
    font-weight: bold;
}}

.table-wrapper {{
    width: 100%;
    overflow-x: auto;
}}

table {{
    width: 100%;
    min-width: 1000px;
    border-collapse: collapse;
}}

thead {{
    background: #21262d;
}}

th {{
    color: #00ff66;
    padding: 14px;
    text-align: left;
    white-space: nowrap;
    border-bottom: 1px solid #30363d;
}}

td {{
    padding: 12px 14px;
    border-bottom: 1px solid #21262d;
    vertical-align: middle;
}}

tbody tr:hover {{
    background: #1c2128;
}}

.url {{
    min-width: 400px;
    word-break: break-all;
}}

.center {{
    text-align: center;
    white-space: nowrap;
}}

a {{
    color: #58a6ff;
    text-decoration: none;
}}

a:hover {{
    color: #79c0ff;
    text-decoration: underline;
}}

.status {{
    display: inline-block;
    padding: 5px 10px;
    border-radius: 5px;
    font-weight: bold;
    min-width: 45px;
    text-align: center;
}}

.success {{
    background: #238636;
    color: #ffffff;
}}

.redirect {{
    background: #9e6a03;
    color: #ffffff;
}}

.error {{
    background: #da3633;
    color: #ffffff;
}}

.status-info {{
    background: #1f6feb;
    color: #ffffff;
}}

.footer {{
    margin-top: 20px;
    padding: 15px;
    text-align: center;
    color: #8b949e;
    font-size: 12px;
}}

@media (max-width: 700px) {{

    body {{
        padding: 10px;
    }}

    .header h1 {{
        font-size: 21px;
    }}

}}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>
            🔎 Resultados do Scan
        </h1>

        <div class="info-grid">

            <div class="info-box">
                <strong>ALVO</strong>
                <span>
                    {escape(
                        str(
                            self.target_var.get()
                        )
                    )}
                </span>
            </div>

            <div class="info-box">
                <strong>MODO</strong>
                <span>
                    {escape(
                        str(
                            self.mode_var.get()
                        )
                    )}
                </span>
            </div>

            <div class="info-box">
                <strong>WORDLIST</strong>
                <span>
                    {escape(
                        str(
                            self.wl_var.get()
                        )
                    )}
                </span>
            </div>

            <div class="info-box">
                <strong>RESULTADOS</strong>
                <span>
                    {len(self.results)}
                </span>
            </div>

            <div class="info-box">
                <strong>DATA</strong>
                <span>
                    {
                        datetime.now().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )
                    }
                </span>
            </div>

        </div>

    </div>

    <div class="card">

        <div class="card-header">
            📋 Resultados Encontrados
        </div>

        <div class="table-wrapper">

            <table>

                <thead>

                    <tr>

                        <th>
                            {
                                "Subdomínio"
                                if "dns"
                                in self.mode_var
                                .get()
                                .lower()
                                else "Domínio"
                            }
                        </th>

                        <th>
                            Status
                        </th>

                        <th>
                            Tamanho
                        </th>

                        <th>
                            IP / Redirecionamento
                        </th>

                    </tr>

                </thead>

                <tbody>

                    {''.join(rows)}

                </tbody>

            </table>

        </div>

    </div>

    <div class="footer">
        Relatório gerado automaticamente
    </div>

</div>

</body>

</html>
"""

                # UTF-8 preserva acentos e emojis.

                with open(
                    fname,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(html)

            # =================================================
            # JSON
            # =================================================

            elif name.endswith(".json"):

                with open(
                    fname,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        self.results,
                        f,
                        indent=2,
                        ensure_ascii=False
                    )

            # =================================================
            # CSV
            # =================================================

            elif name.endswith(".csv"):

                with open(
                    fname,
                    "w",
                    newline="",
                    encoding="utf-8"
                ) as f:

                    writer = csv.writer(f)

                    writer.writerow([
                        "URL",
                        "Status",
                        "Size",
                        "Extra"
                    ])

                    for r in self.results:

                        writer.writerow([

                            r.get(
                                "url",
                                ""
                            ),

                            r.get(
                                "status",
                                ""
                            ),

                            r.get(
                                "size",
                                ""
                            ),

                            r.get(
                                "extra",
                                ""
                            )
                        ])

            # =================================================
            # TXT
            # =================================================

            else:

                with open(
                    fname,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(
                        "GoBusterGUI - Scan Results\n"
                    )

                    f.write(
                        "Data: "
                        + datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        + "\n"
                    )

                    f.write(
                        f"Alvo: "
                        f"{self.target_var.get()}\n"
                    )

                    f.write(
                        f"Wordlist: "
                        f"{self.wl_var.get()}\n"
                    )

                    f.write(
                        f"Modo: "
                        f"{self.mode_var.get()}\n"
                    )

                    f.write(
                        "=" * 60
                        + "\n\n"
                    )

                    for r in self.results:

                        f.write(
                            f"[{r.get('status', '')}] "
                            f"{r.get('url', '')}"
                        )

                        if r.get("size"):

                            f.write(
                                f" | Size: "
                                f"{r['size']}"
                            )

                        if r.get("extra"):

                            f.write(
                                f" | "
                                f"{r['extra']}"
                            )

                        f.write("\n")

            messagebox.showinfo(
                "Exportar",
                (
                    "Relatório salvo com sucesso em:"
                    f"\n\n{fname}"
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "Erro",
                f"Erro ao exportar:\n\n{exc}"
            )


# =============================================================
# MAIN
# =============================================================

def main():

    root = tk.Tk()

    GoBusterGUI(root)

    root.mainloop()


if __name__ == "__main__":

    main()
