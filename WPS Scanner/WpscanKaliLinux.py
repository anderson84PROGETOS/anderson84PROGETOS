#!/usr/bin/env python3
"""
WPScan GUI para Kali Linux
- Tema hacker: fundo preto, verde neon
- Descobertas (robots.txt, versão WP, tema, usuários, plugins, backups) em laranja abóbora
- Username / Valid Combinations em laranja abóbora brilhante
- Password em amarelo brilhante (#ffd700)
- [SUCCESS] - user / pass → destaque especial: fundo laranja sólido, texto preto
- Filtra linhas de progresso (Progress: |===)
- Resultados em tempo real, relatório HTML estilizado
- Brute force: wpscan --url <alvo> --usernames <usuario> --passwords <wordlist>
- Suporta URL de login em qualquer formato:
    https://teste.com/wp-login.php
    http://192.168.0.13/wordpress/wp-login.php
    http://192.168.0.13/wordpress/
  → converte automaticamente para a URL base do WordPress
- Procura wordlist na mesma pasta do script (wordlist.txt por padrão)
"""

import subprocess, threading, re, os, html, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

WPSCAN_PATH = "/usr/bin/wpscan"

# Diretório onde o script está
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Procura wordlist na mesma pasta do script (ordem de prioridade)
def find_local_wordlist():
    candidatos = ["wordlist.txt", "rockyou.txt", "wordlists.txt", "senhas.txt"]
    for nome in candidatos:
        caminho = os.path.join(SCRIPT_DIR, nome)
        if os.path.isfile(caminho):
            return caminho
    return None

# Remove escapes ANSI (cores, barras de progresso, cursor)
ANSI_RE = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07')

# Filtra linhas de progresso do WPScan (barras e erros repetidos durante progresso)
PROGRESS_RE = re.compile(r'^(Progress:\s*\|*\s*(Error: .*)?$|Checking |Enumerating )')

# Linha de achado curto: [+] andrei  (usuário, plugin, backup, etc.)
SHORT_FINDING_RE = re.compile(r'^\[\+\]\s+(\S+)$')

# Linhas de descobertas importantes → laranja abóbora
HIGHLIGHT_RE = re.compile(
    r'^\[\+\]\s+.('
    r'robots\.txt found:|'
    r'WordPress version . identified|'
    r'WordPress theme in use:|'
    r'Plugin version . identified|'
    r'Theme version . identified|'
    r'Location:|'
    r'Style URL:|'
    r'Valid Usernames|'
    r'Config Backup|'
    r'DB Export'
    r')', re.IGNORECASE)

# Usuário/Senha encontrados (brute force e enumeração)
CREDENTIAL_RE = re.compile(
    r'(Username:|Password:|Valid Combinations|Valid Usernames)',
    re.IGNORECASE)

# Senha → amarelo brilhante
PASSWORD_RE = re.compile(r'Password:', re.IGNORECASE)

# Credencial encontrada: [SUCCESS] - root / admin → abóbora brilhante
SUCCESS_RE = re.compile(r'^\[SUCCESS\]\s*-\s*', re.IGNORECASE)

# ------------------- Cores do tema -------------------
BG_BLACK   = "#000000"    # fundo preto
FG_GREEN   = "#00ff41"    # verde hacker
FG_PUMPKIN = "#ff8c00"    # laranja abóbora (descobertas / usuários)
FG_GOLD    = "#ffd700"    # amarelo brilhante (senhas)
FG_DIM     = "#0a8f2a"    # verde escuro
FG_ERR     = "#ff2222"    # vermelho
FG_INFO    = "#00b3a4"    # ciano

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório WPScan — {url}</title>
<style>
 * {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Courier New',Consolas,monospace; background:#000; color:#00ff41;
       padding:30px; line-height:1.5; }}
.container {{ max-width:1100px; margin:0 auto; }}
h1 {{ color:#00ff41; text-shadow:0 0 10px #00ff41; border-bottom:2px solid #00ff41;
      padding-bottom:12px; }}
.meta {{ color:#0a8f2a; font-size:0.85em; margin-bottom:24px; }}
.badge {{ background:#003b0f; color:#00ff41; border:1px solid #00ff41; padding:3px 10px;
          border-radius:4px; font-size:0.75em; margin-right:8px; }}
pre {{ background:#050505; border:1px solid #00ff41; box-shadow:0 0 8px #00ff4133;
       border-radius:6px; padding:20px; white-space:pre-wrap; word-wrap:break-word;
       font-size:0.88em; }}
.ok      {{ color:#00ff41; font-weight:bold; }}
.user    {{ color:#ff8c00; font-weight:bold; text-shadow:0 0 8px #ff8c0088; }}
.pass    {{ color:#ffd700; font-weight:bold; text-shadow:0 0 10px #ffd700, 0 0 18px #ffd70088; }}
.cred    {{ color:#ffa500; font-weight:bold; text-shadow:0 0 12px #ff8c00, 0 0 20px #ff8c00; }}
.success {{ background:#ff8c00; color:#000; font-weight:bold; padding:1px 6px;
            border-radius:3px; text-shadow:none; }}
.info    {{ color:#00b3a4; font-weight:bold; }}
.warn    {{ color:#ffd700; font-weight:bold; }}
.err     {{ color:#ff2222; font-weight:bold; }}
footer   {{ margin-top:24px; color:#0a8f2a; text-align:center;
            border-top:1px solid #00ff41; padding-top:14px; }}
</style>
</head>
<body>
<div class="container">
<h1>&gt;_ Relatório WPScan</h1>
<div class="meta"><span class="badge">{url}</span> Gerado em: {timestamp}</div>
<pre id="report">{content}</pre>
<footer>Gerado por WPScan GUI — Kali Linux</footer>
</div>
</body>
</html>"""


def normalize_url(url):
    """
    Converte URL de login para URL base do WordPress.

    Exemplos:
      https://teste.com/wp-login.php            → https://teste.com/
      http://192.168.0.13/wordpress/wp-login.php    → http://192.168.0.13/wordpress/
      http://192.168.0.13/wordpress/wp-admin/       → http://192.168.0.13/wordpress/
      https://teste.com/                        → https://teste.com/  (inalterada)
    """
    url = url.strip().rstrip("/")
    # Remove qualquer página de login/admin do final (com ou sem subpasta)
    url = re.sub(r'/(wp-login\.php|wp-admin/?|login/?)$', '', url, flags=re.IGNORECASE)
    # Se sobrou só o domínio (ex.: teste.com), mantém a barra final
    return url + "/"


class WPScanGUI:
    def __init__(self, root):
        self.root = root

        root.title("WPScan — Kali Linux")
        root.geometry("900x620")
        root.configure(bg=BG_BLACK)

        # Maximizar no Kali Linux e Windows
        try:
            root.state("zoomed")
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)
            except tk.TclError:
                pass

        self.wpscan = None
        if os.path.isfile(WPSCAN_PATH):
            self.wpscan = WPSCAN_PATH
        else:
            r = subprocess.run(["which", "wpscan"], capture_output=True, text=True)
            if r.returncode == 0:
                self.wpscan = r.stdout.strip()
            else:
                messagebox.showerror("Erro",
                    "WPScan não encontrado.\nInstale: sudo apt update && sudo apt install wpscan")
                root.destroy()
                return

        # ---------- Estilo ttk escuro ----------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=BG_BLACK, foreground=FG_GREEN,
                        fieldbackground=BG_BLACK, font=("Courier New", 10))
        style.configure("TFrame", background=BG_BLACK)
        style.configure("TLabel", background=BG_BLACK, foreground=FG_GREEN)
        style.configure("TButton", background="#001a08", foreground=FG_GREEN)
        style.map("TButton",
                  background=[("active", "#003b0f")],
                  foreground=[("active", FG_PUMPKIN)])
        style.configure("TCheckbutton", background=BG_BLACK, foreground=FG_GREEN)
        style.map("TCheckbutton",
                  background=[("active", BG_BLACK)],
                  foreground=[("active", FG_PUMPKIN)])
        style.configure("TRadiobutton", background=BG_BLACK, foreground=FG_GREEN)
        style.map("TRadiobutton",
                  background=[("active", BG_BLACK)],
                  foreground=[("active", FG_PUMPKIN)])
        style.configure("TSpinbox", background=BG_BLACK, foreground=FG_GREEN,
                        fieldbackground=BG_BLACK, bordercolor=FG_GREEN)

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="x")

        # URL
        ttk.Label(frame, text="URL alvo:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frame, width=55)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=3)
        self.url_entry.insert(0, "http://192.168.0.13/wordpress/wp-login.php")
        ttk.Label(frame, text="(wp-login.php é convertido automaticamente)").grid(
            row=0, column=2, sticky="w")

        # Wordlist (procura primeiro na pasta do script)
        ttk.Label(frame, text="Wordlist:").grid(row=1, column=0, sticky="w")
        self.wordlist_entry = ttk.Entry(frame, width=55)

        local = find_local_wordlist()
        if local:
            self.wordlist_entry.insert(0, local)
        else:
            self.wordlist_entry.insert(0, os.path.join(SCRIPT_DIR, "wordlist.txt"))
        self.wordlist_entry.grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Button(frame, text="Procurar...", command=self.choose_wordlist).grid(row=1, column=2, padx=5)

        # Usuário
        ttk.Label(frame, text="Usuário:").grid(row=2, column=0, sticky="w")
        self.user_entry = ttk.Entry(frame, width=55)
        self.user_entry.grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Label(frame, text="(obrigatório no brute force)", foreground=FG_DIM).grid(
            row=2, column=2, sticky="w")

        # Opções
        opts = ttk.Frame(frame)
        opts.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        self.enum_users = tk.BooleanVar(value=True)
        self.enum_plugins = tk.BooleanVar()
        self.enum_themes = tk.BooleanVar()
        self.enum_backups = tk.BooleanVar()
        self.do_bruteforce = tk.BooleanVar()
        ttk.Checkbutton(opts, text="Usuários (u)", variable=self.enum_users).pack(side="left")
        ttk.Checkbutton(opts, text="Plugins (vp)", variable=self.enum_plugins).pack(side="left")
        ttk.Checkbutton(opts, text="Temas (vt)", variable=self.enum_themes).pack(side="left")
        ttk.Checkbutton(opts, text="Backups/dados (cb,dbe)", variable=self.enum_backups).pack(side="left")
        ttk.Checkbutton(opts, text="Brute force", variable=self.do_bruteforce).pack(side="left")

        # Tipo de ataque
        atk = ttk.Frame(frame)
        atk.grid(row=5, column=0, columnspan=3, sticky="w", pady=2)
        ttk.Label(atk, text="Ataque:").pack(side="left")
        self.attack = tk.StringVar(value="login-form")
        ttk.Radiobutton(atk, text="Login Form", value="login-form", variable=self.attack).pack(side="left", padx=5)
        ttk.Radiobutton(atk, text="XML-RPC", value="xmlrpc", variable=self.attack).pack(side="left", padx=5)

        # Threads
        th = ttk.Frame(frame)
        th.grid(row=6, column=0, columnspan=3, sticky="w", pady=2)
        ttk.Label(th, text="Threads:").pack(side="left")
        self.threads = tk.StringVar(value="5")
        ttk.Spinbox(th, from_=1, to=20, width=5, textvariable=self.threads).pack(side="left", padx=5)

        # Botões
        btns = ttk.Frame(frame)
        btns.grid(row=7, column=0, columnspan=3, pady=5)
        ttk.Button(btns, text="Iniciar Scan", command=self.start_scan).pack(side="left", padx=5)
        ttk.Button(btns, text="Parar", command=self.stop_scan).pack(side="left", padx=5)
        ttk.Button(btns, text="Limpar", command=lambda: self.output.delete("1.0", tk.END)).pack(side="left", padx=5)
        ttk.Button(btns, text="Salvar HTML", command=self.save_html).pack(side="left", padx=5)

        # ---------- Terminal verde/preto ----------
        self.output = scrolledtext.ScrolledText(
            root, font=("Courier New", 10),
            bg=BG_BLACK, fg=FG_GREEN,
            insertbackground=FG_GREEN,
            selectbackground="#003b0f", selectforeground=FG_GREEN,
            relief="solid", bd=1)
        self.output.pack(fill="both", expand=True, padx=10, pady=5)

        # Tags de cor
        self.output.tag_configure("ok", foreground=FG_GREEN)
        self.output.tag_configure("user", foreground=FG_PUMPKIN,
                                  font=("Courier New", 10, "bold"))
        self.output.tag_configure("pass", foreground=FG_GOLD,
                                  background="#332900",
                                  font=("Courier New", 10, "bold"))
        self.output.tag_configure("success", foreground="#000000",
                                  background="#ff8c00",
                                  font=("Courier New", 10, "bold"))
        self.output.tag_configure("info", foreground=FG_INFO)
        self.output.tag_configure("warn", foreground=FG_GOLD)
        self.output.tag_configure("err", foreground=FG_ERR)

        self.proc = None
        self.scan_url = ""
        self.finished_at = ""

    # ----------------------------------------------------------
    def choose_wordlist(self):
        path = filedialog.askopenfilename(
            initialdir=SCRIPT_DIR,
            title="Escolher wordlist",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if path:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, path)

    def build_command(self):
        raw_url = self.url_entry.get().strip()
        if not raw_url:
            raise ValueError("Informe a URL alvo.")

        # Converte wp-login.php para a URL base do WordPress
        # https://teste.com/wp-login.php → https://teste.com/
        url = normalize_url(raw_url)
        self.scan_url = raw_url   # exibe a URL original no relatório

        cmd = [self.wpscan, "--url", url]

        # ---------------- Brute force ----------------
        # Formato exato:
        #   wpscan --url https://alvo.com/ --usernames usuario --passwords /caminho/wordlist.txt
        if self.do_bruteforce.get():
            wl = self.wordlist_entry.get().strip()
            if not wl or not os.path.isfile(wl):
                raise ValueError(
                    "Wordlist inválida.\n"
                    "Coloque wordlist.txt na pasta do script ou escolha pelo botão Procurar...")
            user = self.user_entry.get().strip()
            if not user:
                raise ValueError(
                    "Informe o usuário para brute force\n"
                    "(ou rode a enumeração primeiro para descobrir usuários).")
            cmd += ["--usernames", user, "--passwords", wl]
            return cmd

        # ---------------- Enumeração normal ----------------
        flags = []
        if self.enum_users.get():
            flags.append("u")
        if self.enum_plugins.get():
            flags.append("vp")
        if self.enum_themes.get():
            flags.append("vt")
        if self.enum_backups.get():
            flags.extend(["cb", "dbe"])

        if flags:
            cmd += ["--enumerate", ",".join(flags)]
        return cmd

    def start_scan(self):
        try:
            cmd = self.build_command()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        self.output.delete("1.0", tk.END)
        self.log("CMD: " + " ".join(cmd) + "\n\n")

        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True, bufsize=1)
        threading.Thread(target=self.read_output, daemon=True).start()

    def read_output(self):
        """
        Leitura segura do stdout do WPScan.
        - Usa readline() em loop (funciona mesmo com buffering do subprocesso)
        - Protege contra processo encerrado/pipe fechado (evita ValueError
          quando o scan é interrompido)
        """
        proc = self.proc
        if proc is None or proc.stdout is None:
            return
        try:
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                self.log(line)
        except (ValueError, OSError):
            # Pipe fechado (scan interrompido pelo usuário) — segue o fluxo
            pass
        finally:
            self.finished_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.log("\n--- Scan finalizado ---\n")

    def stop_scan(self):
        if self.proc:
            try:
                self.proc.terminate()
            except OSError:
                pass
            self.finished_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " (interrompido)"
            self.log("\n--- Scan interrompido ---\n")

    # ----------------------------------------------------------
    def is_highlight_line(self, stripped):
        """True se a linha inteira deve ficar em laranja abóbora."""
        if HIGHLIGHT_RE.search(stripped):
            return True
        # Username: / Valid Combinations → abóbora brilhante
        if CREDENTIAL_RE.search(stripped):
            return True
        # [SUCCESS] - user / pass → abóbora brilhante (tag especial)
        if SUCCESS_RE.match(stripped):
            return True
        # Achados curtos sem dois-pontos: usuários, plugins, backups...
        m = SHORT_FINDING_RE.match(stripped)
        if m and ':' not in stripped and len(m.group(1)) <= 40:
            return True
        return False

    def log(self, text):
        """Insere no terminal em tempo real, com cores por marcador."""
        def _append():
            clean = ANSI_RE.sub('', text)
            # Filtra linhas de progresso/barras do WPScan
            if PROGRESS_RE.match(clean.strip()):
                return

            self.output.insert(tk.END, clean)
            self.output.see(tk.END)

            stripped = clean.rstrip("\n")
            if not stripped:
                return

            line_start = "end-2c linestart"
            line_end = "end-1c linestart"

            # [SUCCESS] - credencial encontrada → fundo laranja sólido
            if SUCCESS_RE.match(stripped):
                self.output.tag_add("success", line_start, line_end)
                return

            # Linha com Password: → amarelo brilhante
            if PASSWORD_RE.search(stripped):
                self.output.tag_add("pass", line_start, line_end)
                return

            # Descobertas importantes / usuários → abóbora brilhante
            if self.is_highlight_line(stripped):
                self.output.tag_add("user", line_start, line_end)
                return

            # Demais linhas por marcador
            if stripped.startswith("[!]"):
                self.output.tag_add("warn", line_start, line_end)
            elif stripped.startswith("[i]"):
                self.output.tag_add("info", line_start, line_end)
            elif stripped.startswith("[E]"):
                self.output.tag_add("err", line_start, line_end)
        self.root.after(0, _append)   # thread-safe

    # ----------------------------------------------------------
    def colorize(self, line):
        """Prepara a linha para o HTML."""
        # [SUCCESS] - user / pass → abóbora brilhante com glow
        if SUCCESS_RE.match(line):
            body = html.escape(re.sub(r'^\[SUCCESS\]\s*-\s*', '', line, flags=re.IGNORECASE))
            return '<span class="success">[SUCCESS]</span> <span class="cred">' + body + '</span>'

        # Linhas com Password → amarelo brilhante com glow
        if PASSWORD_RE.search(line):
            body = html.escape(line)
            body = re.sub(r'(Password:)', r'<span class="pass">\1</span>', body)
            return '<span class="ok">[+]</span> <span class="user">' + body + '</span>'

        # Username / Valid Combinations → abóbora brilhante com glow
        if CREDENTIAL_RE.search(line):
            body = html.escape(line)
            body = re.sub(
                r'(Username:|Valid Combinations[^:]*:)',
                r'<span class="cred">\1</span>', body)
            return '<span class="ok">[+]</span> <span class="user">' + body + '</span>'

        # [+] verde + resto da linha em abóbora
        if HIGHLIGHT_RE.search(line):
            body = html.escape(re.sub(r'^\[\+\]\s*', '', line))
            return '<span class="ok">[+]</span> <span class="user">' + body + '</span>'

        # Achado curto (usuário etc.)
        m = SHORT_FINDING_RE.match(line)
        if m and ':' not in line and len(m.group(1)) <= 40:
            name = html.escape(m.group(1))
            return '<span class="ok">[+]</span> <span class="user">' + name + '</span>'

        # Demais linhas: só o marcador colorido
        line = html.escape(line)
        line = re.sub(r'^\[\+\]', '<span class="ok">[+]</span>', line)
        line = re.sub(r'^\[i\]', '<span class="info">[i]</span>', line)
        line = re.sub(r'^\[!\]', '<span class="warn">[!]</span>', line)
        line = re.sub(r'^\[E\]', '<span class="err">[E]</span>', line)
        return line

    def save_html(self):
        content = self.output.get("1.0", tk.END).rstrip("\n")
        if not content:
            messagebox.showwarning("Aviso", "Nada para salvar — rode um scan primeiro.")
            return
        default_name = "wpscan_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"
        path = filedialog.asksaveasfilename(
            defaultextension=".html", initialfile=default_name,
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")])
        if not path:
            return
        colored = "\n".join(self.colorize(l) for l in content.splitlines())
        page = HTML_TEMPLATE.format(
            url=html.escape(self.scan_url or "N/A"),
            timestamp=self.finished_at or datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            content=colored)
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
        messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WPScanGUI(root)
    if root.winfo_exists():
        root.mainloop()
