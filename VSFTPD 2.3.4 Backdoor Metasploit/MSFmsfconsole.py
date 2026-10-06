#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSF GUI - Interface gráfica para o msfconsole (Kali Linux)
- Filtros de pesquisa (tipo, plataforma, termo)
- Botões rápidos: options, set RHOSTS/LHOST, payload, exploit, run, back...
- Botão Help
- Painéis redimensionáveis (arraste a divisória)
- Destaque vermelho no termo pesquisado
- Botão Limpar
Uso: sudo python3 MSFmsfconsole.py
"""

import os
import pty
import select
import re
import shutil
import subprocess
import threading
import queue
import time
import tkinter as tk
import tkinter.simpledialog
from tkinter import ttk, scrolledtext, messagebox

MSFCONSOLE = shutil.which("msfconsole") or "/usr/bin/msfconsole"

ANSI_RE = re.compile(
    r"\x1b\[\?[0-9;]*[a-zA-Z]"   # sequências privadas (ex: ?1034h)
    r"|\x1b\[[0-9;]*[a-zA-Z]"    # CSI comuns
    r"|\x1b\][^\x07]*\x07"       # OSC (títulos)
)

HELP_TEXT = """MSF GUI - Ajuda

PESQUISA:
  - Tipo: exploit, auxiliary, payload, encoder, nop, post, evasion
  - Plataforma: linux, windows, unix, multi, osx, android
  - Termo: parte do nome (ex: vsftpd_234)
  - Duplo clique num resultado -> use + info do módulo

BOTÕES RÁPIDOS:
  show options   -> mostra as opções do módulo atual
  set RHOSTS     -> pede o IP alvo e executa 'set RHOSTS <ip>'
  set RPORT      -> pede a porta alvo e executa 'set RPORT <porta>'
  set LHOST      -> pede o IP local (você) e executa 'set LHOST <ip>'
  set LPORT      -> pede a porta local e executa 'set LPORT <porta>'
  set payload    -> pede o payload (ex: cmd/unix/reverse)
  check          -> testa se o alvo é vulnerável
  exploit        -> executa o exploit
  exploit -j     -> executa em segundo plano (job)
  run            -> executa módulos auxiliary/post
  back           -> sai do módulo atual
  sessions -l    -> lista sessões abertas
  sessions -i 1  -> interage com a sessão 1
  sysinfo        -> info do sistema da sessão
  background     -> envia a sessão para segundo plano

COMANDO LIVRE:
  Digite qualquer comando do msfconsole no campo e pressione Enter.

BOTÕES DA JANELA:
  🧹 Limpar      -> limpa a saída
  ⏹ Parar MSF    -> encerra o msfconsole
"""


class MSFGUI:
    def __init__(self, root):
        self.root = root
        root.title("MSF - msfconsole")
        root.geometry("1000x720")

        self.master_fd = None
        self.proc = None
        self.running = False
        self.out_queue = queue.Queue()
        self.last_output = ""
        self.termo_atual = ""
        self._lock = threading.Lock()

        self._build_ui()
        self.root.after(100, self._poll_output)
        self._start_msf()

    # ---------------- UI ----------------
    def _build_ui(self):
        # ---- Pesquisa com filtros ----
        search_frame = ttk.LabelFrame(self.root, text="Pesquisar Módulos", padding=8)
        search_frame.pack(fill="x", padx=8, pady=6)

        ttk.Label(search_frame, text="Tipo:").grid(row=0, column=0, padx=4)
        self.tipo_var = tk.StringVar(value="todos")
        ttk.Combobox(search_frame, textvariable=self.tipo_var, width=12,
                     values=["todos", "exploit", "auxiliary", "payload",
                             "encoder", "nop", "post", "evasion"],
                     state="readonly").grid(row=0, column=1, padx=4)

        ttk.Label(search_frame, text="Plataforma:").grid(row=0, column=2, padx=4)
        self.plat_var = tk.StringVar(value="")
        ttk.Combobox(search_frame, textvariable=self.plat_var, width=14,
                     values=["", "linux", "windows", "unix", "multi", "osx", "android"]
                     ).grid(row=0, column=3, padx=4)

        ttk.Label(search_frame, text="Termo:").grid(row=0, column=4, padx=4)
        self.termo_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.termo_var, width=20)
        entry.grid(row=0, column=5, padx=4)
        entry.bind("<Return>", lambda e: self._search())

        self.btn_search = ttk.Button(search_frame, text="🔍 Pesquisar", command=self._search)
        self.btn_search.grid(row=0, column=6, padx=8)

        ttk.Button(search_frame, text="❓ Help", command=self._show_help).grid(row=0, column=7, padx=8)

        # ---- Painel vertical redimensionável ----
        self.paned = ttk.PanedWindow(self.root, orient="vertical")
        self.paned.pack(fill="both", expand=True, padx=8, pady=4)

        # --- Painel superior: resultados ---
        result_frame = ttk.LabelFrame(self.paned,
                                      text="Resultados da Pesquisa (duplo clique para usar)",
                                      padding=4)
        cols = ("caminho", "nome", "rank")
        self.tree = ttk.Treeview(result_frame, columns=cols, show="headings", height=7)
        self.tree.heading("caminho", text="Caminho do Módulo")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("rank", text="Rank")
        self.tree.column("caminho", width=480)
        self.tree.column("nome", width=280)
        self.tree.column("rank", width=80)
        sb = ttk.Scrollbar(result_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._use_module)
        self.tree.tag_configure("destaque", background="#5c1010", foreground="#ff5555")

        # --- Painel inferior: botões rápidos + comando + saída ---
        bottom = ttk.Frame(self.paned)

        quick_frame = ttk.LabelFrame(bottom, text="Comandos Rápidos", padding=6)
        quick_frame.pack(fill="x", pady=(0, 4))

        quick_cmds = [
            ("show options", None),
            ("set RHOSTS", "ip"),
            ("set RPORT", "porta"),
            ("set LHOST", "ip"),
            ("set LPORT", "porta"),
            ("set payload", "payload"),
            ("check", None),
            ("exploit", None),
            ("exploit -j", None),
            ("run", None),
            ("back", None),
            ("sessions -l", None),
            ("sessions -i 1", None),
            ("background", None),
            ("sysinfo", None),
        ]
        col = 0
        row = 0
        for cmd, ask in quick_cmds:
            b = ttk.Button(quick_frame, text=cmd,
                           command=lambda c=cmd, a=ask: self._quick_cmd(c, a))
            b.grid(row=row, column=col, padx=3, pady=2, sticky="ew")
            col += 1
            if col > 4:
                col = 0
                row += 1
        for c in range(5):
            quick_frame.columnconfigure(c, weight=1)

        # Campo de comando livre
        cmd_frame = ttk.LabelFrame(bottom, text="Comando", padding=8)
        cmd_frame.pack(fill="x", pady=(0, 4))

        self.cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.cmd_var)
        cmd_entry.pack(side="left", fill="x", expand=True, padx=4)
        cmd_entry.bind("<Return>", lambda e: self._send_cmd())
        ttk.Button(cmd_frame, text="⏵ Enviar", command=self._send_cmd).pack(side="left", padx=4)
        ttk.Button(cmd_frame, text="🧹 Limpar", command=self._clear).pack(side="left", padx=4)
        ttk.Button(cmd_frame, text="⏹ Parar MSF", command=self._stop_msf).pack(side="left", padx=4)

        # Saída
        out_frame = ttk.LabelFrame(bottom, text="Saída do msfconsole", padding=4)
        out_frame.pack(fill="both", expand=True)

        self.output = scrolledtext.ScrolledText(out_frame, bg="#1e1e1e", fg="#d4d4d4",
                                                font=("Monospace", 10),
                                                insertbackground="#d4d4d4")
        self.output.pack(fill="both", expand=True)
        self.output.configure(state="disabled")
        self.output.tag_configure("destaque", background="#5c1010", foreground="#ff5555")

        self.paned.add(result_frame, weight=2)
        self.paned.add(bottom, weight=3)

        self.status = ttk.Label(self.root, text="msfconsole: iniciando...")
        self.status.pack(anchor="w", padx=10)

    # ---------------- msfconsole com PTY ----------------
    def _start_msf(self):
        if not os.path.exists(MSFCONSOLE):
            messagebox.showerror(
                "Erro",
                f"msfconsole não encontrado em: {MSFCONSOLE}\n"
                "Instale com: sudo apt install metasploit-framework"
            )
            self.status.configure(text="msfconsole: não encontrado")
            return
        try:
            self.master_fd, slave_fd = pty.openpty()
            env = dict(os.environ)
            env["TERM"] = "xterm"
            self.proc = subprocess.Popen(
                [MSFCONSOLE, "-q"],
                stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
                close_fds=True, env=env,
                start_new_session=True)
            os.close(slave_fd)
            self.running = True
            self.status.configure(text="msfconsole: executando")
            threading.Thread(target=self._reader, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar msfconsole:\n{e}")
            self.status.configure(text="msfconsole: erro ao iniciar")

    def _reader(self):
        fd = self.master_fd
        while self.running and fd is not None:
            try:
                r, _, _ = select.select([fd], [], [], 0.5)
                if r:
                    try:
                        data = os.read(fd, 4096)
                    except OSError:
                        break
                    if not data:
                        break
                    self.out_queue.put(data)
                if self.master_fd is None or not self.running:
                    break
            except (OSError, ValueError):
                break
        self.out_queue.put(b"\n[msfconsole encerrado]\n")

    def _poll_output(self):
        try:
            while not self.out_queue.empty():
                data = self.out_queue.get()
                text = ANSI_RE.sub("", data.decode("utf-8", errors="replace"))
                self.last_output += text
                self._insert_output(text)
        except Exception:
            pass
        self.root.after(100, self._poll_output)

    def _insert_output(self, text):
        self.output.configure(state="normal")
        if self.termo_atual:
            padrao = re.escape(self.termo_atual)
            partes = re.split(f"({padrao})", text, flags=re.IGNORECASE)
            for p in partes:
                if p and p.lower() == self.termo_atual.lower():
                    self.output.insert("end", p, "destaque")
                else:
                    self.output.insert("end", p)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _write_msf(self, text):
        with self._lock:
            fd = self.master_fd
            if fd is not None:
                try:
                    os.write(fd, (text + "\r").encode())
                except OSError:
                    pass

    def _send_cmd(self):
        cmd = self.cmd_var.get().strip()
        if not cmd:
            return
        self._write_msf(cmd)
        self.cmd_var.set("")

    # ---------------- botões rápidos ----------------
    def _quick_cmd(self, cmd, ask):
        if ask:
            titulo = {"ip": "Digite o IP",
                      "porta": "Digite a porta",
                      "payload": "Digite o payload (ex: cmd/unix/reverse)"}.get(ask, "Digite o valor")
            valor = tkinter.simpledialog.askstring(titulo, f"{cmd} -> valor:", parent=self.root)
            if not valor:
                return
            self._write_msf(f"{cmd} {valor.strip()}")
        else:
            self._write_msf(cmd)

    # ---------------- help ----------------
    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Ajuda - MSF GUI")
        win.geometry("560x480")
        txt = scrolledtext.ScrolledText(win, wrap="word", font=("Monospace", 10))
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        txt.insert("1.0", HELP_TEXT)
        txt.configure(state="disabled")
        ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=4)

    def _clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.last_output = ""

    def _stop_msf(self):
        self.running = False
        if self.proc:
            try:
                self._write_msf("exit")
                time.sleep(0.3)
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None

        with self._lock:
            fd, self.master_fd = self.master_fd, None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            self.status.configure(text="msfconsole: parado")
        except Exception:
            pass

    # ---------------- pesquisa ----------------
    def _search(self):
        termo = self.termo_var.get().strip()
        tipo = self.tipo_var.get()
        plat = self.plat_var.get().strip()

        self.termo_atual = termo

        cmd = "search "
        if tipo != "todos":
            cmd += f"type:{tipo} "
        if plat:
            cmd += f"platform:{plat} "
        if termo:
            cmd += f"{termo} "

        cmd = cmd.strip()
        self.btn_search.configure(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.last_output = ""
        self._write_msf(cmd)
        threading.Thread(target=self._wait_results, daemon=True).start()

    def _wait_results(self):
        time.sleep(5)
        self.root.after(0, self._parse_results)

    def _parse_results(self):
        termo = self.termo_atual.lower() if self.termo_atual else ""
        for ln in self.last_output.splitlines():
            # Formato típico:  #  Name  Disclosure Date  Rank  Check  Description
            # Ex: "  12  exploit/unix/ftp/vsftpd_234_backdoor  2011-07-03  excellent  No  ..."
            m = re.match(r"\s*(\d+)\s+(\S+)(?:\s+(.*))?$", ln)
            if m and "/" in m.group(2):
                caminho = m.group(2)
                resto = m.group(3) or ""
                nome = caminho.split("/")[-1]
                # Tenta pegar rank entre tokens conhecidos
                rank = ""
                tokens = resto.split()
                for t in tokens:
                    if t.lower() in ("excellent", "great", "good", "normal",
                                     "average", "low", "manual", "unknown"):
                        rank = t
                        break
                tags = ("destaque",) if termo and (termo in caminho.lower()
                                                   or termo in nome.lower()) else ()
                self.tree.insert("", "end", values=(caminho, nome, rank), tags=tags)
        self.last_output = ""
        try:
            self.btn_search.configure(state="normal")
        except Exception:
            pass

    def _use_module(self, event):
        item = self.tree.focus()
        if not item:
            return
        vals = self.tree.item(item, "values")
        if not vals:
            return
        path = vals[0]
        self._write_msf(f"use {path}")
        self._write_msf(f"info")

    def on_close(self):
        self._stop_msf()
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MSFGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
