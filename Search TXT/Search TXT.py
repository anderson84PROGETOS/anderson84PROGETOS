#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App: Busca em TXT (GUI)
Descrição:
- Abrir arquivo .txt
- Pesquisar por um termo (ex.: "kubark06.htm")
- Mostrar todas as linhas que contêm o termo, com número da linha
- Opções: diferenciar maiúsculas/minúsculas, corresponder palavra inteira
- Salvar resultados em .txt
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os

class BuscaTXTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Search TXT")
        self.geometry("920x600")
        self.minsize(800, 500)

        self.arquivo_path = None
        self.linhas = []
        self.resultados = []

        self._criar_widgets()

    def _criar_widgets(self):
        # Frame superior: seleção de arquivo e termo de busca
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        btn_abrir = ttk.Button(top, text="Abrir .txt", command=self._abrir_arquivo)
        btn_abrir.grid(row=0, column=0, padx=(0,8), pady=4, sticky="w")

        self.lbl_arquivo = ttk.Label(top, text="Nenhum arquivo aberto")
        self.lbl_arquivo.grid(row=0, column=1, padx=4, pady=4, sticky="w")

        ttk.Label(top, text="Buscar:").grid(row=1, column=0, padx=(0,8), pady=4, sticky="w")
        self.var_busca = tk.StringVar()
        ent_busca = ttk.Entry(top, textvariable=self.var_busca, width=40)
        ent_busca.grid(row=1, column=1, padx=4, pady=4, sticky="w")
        ent_busca.bind("<Return>", lambda e: self._executar_busca())

        # Opções
        opts = ttk.Frame(top)
        opts.grid(row=1, column=2, padx=10, pady=4, sticky="w")
        self.var_case = tk.BooleanVar(value=False)
        self.var_whole = tk.BooleanVar(value=False)
        self.var_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Diferenciar maiúsc./minúsc.", variable=self.var_case).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(opts, text="Palavra inteira", variable=self.var_whole).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(opts, text="Regex", variable=self.var_regex).pack(side=tk.LEFT, padx=(0,10))

        btn_buscar = ttk.Button(top, text="Buscar", command=self._executar_busca)
        btn_buscar.grid(row=1, column=3, padx=4, pady=4, sticky="w")

        btn_limpar = ttk.Button(top, text="Limpar", command=self._limpar_resultados)
        btn_limpar.grid(row=1, column=4, padx=4, pady=4, sticky="w")

        # Separador
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Painel central com resultados
        center = ttk.Frame(self, padding=10)
        center.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Contador
        self.var_contador = tk.StringVar(value="0 resultados")
        lbl_contador = ttk.Label(center, textvariable=self.var_contador)
        lbl_contador.pack(anchor="w")

        # Treeview para mostrar nº linha e conteúdo
        cols = ("linha", "conteudo")
        self.tree = ttk.Treeview(center, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("linha", text="Linha")
        self.tree.heading("conteudo", text="Conteúdo")
        self.tree.column("linha", width=70, anchor="e")
        self.tree.column("conteudo", width=700, anchor="w")

        vsb = ttk.Scrollbar(center, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(center, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Rodapé com ações
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(bottom, text="Salvar resultados", command=self._salvar_resultados).pack(side=tk.RIGHT)
        ttk.Button(bottom, text="Sair", command=self.destroy).pack(side=tk.RIGHT, padx=8)

        # Estilo leve
        style = ttk.Style(self)
        try:
            self.tk.call("source", "sun-valley.tcl")
            style.theme_use("sun-valley-dark")
        except Exception:
            pass

    def _abrir_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecione um arquivo .txt",
            filetypes=[("Arquivos de texto", "*.txt *.log *.md *.csv *.json *.htm *.html *.xml *.cfg *.ini *.yaml *.yml"), ("Todos os arquivos", "*.*")]
        )
        if not path:
            return
        self.arquivo_path = path
        self.lbl_arquivo.config(text=os.path.basename(path))

        # Tenta ler com utf-8; se falhar, tenta latin-1
        conteudo = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(path, "r", encoding=enc, errors="strict") as f:
                    conteudo = f.read()
                break
            except Exception:
                continue
        if conteudo is None:
            # Em último caso, lê ignorando erros
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()

        # Normaliza quebras de linha
        self.linhas = conteudo.splitlines()
        self._limpar_resultados(clear_only=True)
        messagebox.showinfo("Arquivo carregado", f"{len(self.linhas)} linhas carregadas")

    def _montar_padrao(self, termo):
        # Constrói padrão de busca considerando as opções
        if self.var_regex.get():
            padrao = termo
        else:
            padrao = re.escape(termo)
        if self.var_whole.get():
            padrao = r"\b" + padrao + r"\b"
        flags = 0 if self.var_case.get() else re.IGNORECASE
        try:
            comp = re.compile(padrao, flags)
            return comp
        except re.error as e:
            messagebox.showerror("Erro de regex", f"Padrão inválido:\n{e}")
            return None

    def _executar_busca(self):
        termo = self.var_busca.get().strip()
        if not self.arquivo_path:
            messagebox.showwarning("Aviso", "Abra um arquivo antes de buscar.")
            return
        if not termo:
            messagebox.showwarning("Aviso", "Digite um termo para buscar.")
            return

        comp = self._montar_padrao(termo)
        if not comp:
            return

        self.resultados.clear()
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, linha in enumerate(self.linhas, start=1):
            if comp.search(linha):
                # Armazena tupla (n_linha, conteudo)
                self.resultados.append((idx, linha))

        for n_linha, conteudo in self.resultados:
            self.tree.insert("", tk.END, values=(n_linha, conteudo))

        self.var_contador.set(f"{len(self.resultados)} resultado(s)")

        if not self.resultados:
            messagebox.showinfo("Sem resultados", "Nenhuma ocorrência encontrada.")

    def _limpar_resultados(self, clear_only=False):
        # Limpa resultados/contador; se clear_only, mantém arquivo/linhas
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.resultados.clear()
        self.var_contador.set("0 resultados")
        if not clear_only:
            self.arquivo_path = None
            self.linhas = []
            self.lbl_arquivo.config(text="Nenhum arquivo aberto")

    def _salvar_resultados(self):
        if not self.resultados:
            messagebox.showwarning("Aviso", "Não há resultados para salvar.")
            return
        path = filedialog.asksaveasfilename(
            title="Salvar resultados",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile="resultados_busca.txt"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Arquivo: {self.arquivo_path or 'N/D'}\n")
                f.write(f"Termo: {self.var_busca.get()}\n")
                f.write(f"Opções: case={'on' if self.var_case.get() else 'off'}, whole={'on' if self.var_whole.get() else 'off'}, regex={'on' if self.var_regex.get() else 'off'}\n")
                f.write(f"Total: {len(self.resultados)}\n")
                f.write("-" * 80 + "\n")
                for n_linha, conteudo in self.resultados:
                    f.write(f"{n_linha}: {conteudo}\n")
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

def main():
    app = BuscaTXTApp()
    app.mainloop()

if __name__ == "__main__":
    main()
