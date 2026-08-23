#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wordlist / PIN Cleaner - Remover duplicados, ordena e mostra o que foi removido
Funciona com:
  - Listas de PIN WPS (8 dígitos)
  - Wordlists gerais (rockyou.txt, etc.)
  
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from collections import OrderedDict


class WordlistCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Wordlist / PIN Cleaner - Remover Duplicados 🔥")
        self.root.geometry("1180x800")
        self.root.minsize(750, 550)

        # Variáveis
        self.arquivo_entrada = tk.StringVar()
        self.modo = tk.StringVar(value="auto")  # auto | pin | wordlist
        self.case_sensitive = tk.BooleanVar(value=False)
        self.itens_originais = []
        self.itens_unicos = []
        self.itens_removidos = []

        self.criar_interface()

    def criar_interface(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Estilo personalizado da Progressbar (verde)
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#3a3a3a",
            background="#00ff88",
            bordercolor="#00ff88",
            lightcolor="#00ff88",
            darkcolor="#00ff88"
        )

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === Arquivo ===
        frame_arquivo = ttk.LabelFrame(main_frame, text="Arquivo de entrada", padding="10")
        frame_arquivo.pack(fill=tk.X, pady=(0, 8))

        ttk.Entry(frame_arquivo, textvariable=self.arquivo_entrada, width=70).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(frame_arquivo, text="Procurar...", command=self.selecionar_arquivo).pack(side=tk.LEFT)
        ttk.Button(frame_arquivo, text="Carregar", command=self.carregar_arquivo).pack(side=tk.LEFT, padx=(5, 0))

        # === Opções ===
        frame_opcoes = ttk.LabelFrame(main_frame, text="Opções de processamento", padding="8")
        frame_opcoes.pack(fill=tk.X, pady=(0, 8))

        # Modo
        ttk.Label(frame_opcoes, text="Modo:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(frame_opcoes, text="Automático", variable=self.modo, value="auto").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(frame_opcoes, text="PIN (numérico)", variable=self.modo, value="pin").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(frame_opcoes, text="Wordlist (alfabético)", variable=self.modo, value="wordlist").pack(side=tk.LEFT, padx=3)

        ttk.Separator(frame_opcoes, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Checkbutton(
            frame_opcoes,
            text="Diferenciar maiúsculas/minúsculas",
            variable=self.case_sensitive
        ).pack(side=tk.LEFT, padx=5)

        # === Botões ===
        frame_botoes = ttk.Frame(main_frame)
        frame_botoes.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(frame_botoes, text="🧹 Limpar Duplicados e Ordenar", command=self.processar).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(frame_botoes, text="💾 Salvar Lista Limpa", command=self.salvar_arquivo).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(frame_botoes, text="📋 Copiar Lista Limpa", command=self.copiar_limpa).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(frame_botoes, text="🗑️ Limpar Tela", command=self.limpar_tela).pack(side=tk.LEFT)

        # === Estatísticas ===
        frame_stats = ttk.LabelFrame(main_frame, text="Estatísticas", padding="6")
        frame_stats.pack(fill=tk.X, pady=(0, 8))

        self.label_stats = ttk.Label(
            frame_stats,
            text="Nenhum arquivo carregado ainda.",
            font=("Segoe UI", 10),
        )
        self.label_stats.pack(anchor=tk.W)

        # === Resultados (duas colunas) ===
        frame_resultados = ttk.Frame(main_frame)
        frame_resultados.pack(fill=tk.BOTH, expand=True)

        # Esquerda - Removidos
        frame_removidos = ttk.LabelFrame(frame_resultados, text="Itens Duplicados / Removidos", padding="5")
        frame_removidos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.txt_removidos = scrolledtext.ScrolledText(
            frame_removidos, wrap=tk.WORD, font=("Consolas", 9), height=22
        )
        self.txt_removidos.pack(fill=tk.BOTH, expand=True)

        # Direita - Lista limpa
        frame_limpos = ttk.LabelFrame(frame_resultados, text="Lista Limpa (Ordenada)", padding="5")
        frame_limpos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.txt_limpos = scrolledtext.ScrolledText(
            frame_limpos, wrap=tk.WORD, font=("Consolas", 9), height=22
        )
        self.txt_limpos.pack(fill=tk.BOTH, expand=True)

        # === BARRA DE PROGRESSO VERDE (estilo moderno) ===
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 8))

        self.progress_label = ttk.Label(self.progress_frame, text="Progresso: 0%  |  Pronto", anchor=tk.W)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            length=300,
            style="Green.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status = ttk.Label(
            main_frame,
            text="Pronto. Selecione um arquivo (pin.txt, rockyou.txt, etc.)",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status.pack(fill=tk.X, pady=(8, 0))

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo (pin.txt, rockyou.txt, etc.)",
            filetypes=[
                ("Arquivos de texto", "*.txt"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if caminho:
            self.arquivo_entrada.set(caminho)

    def carregar_arquivo(self):
        caminho = self.arquivo_entrada.get().strip()
        if not caminho:
            messagebox.showwarning("Aviso", "Selecione um arquivo primeiro.")
            return

        if not os.path.isfile(caminho):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}")
            return

        try:
            # Tenta detectar encoding
            for encoding in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
                try:
                    with open(caminho, "r", encoding=encoding, errors="strict") as f:
                        linhas = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    linhas = f.readlines()

            self.itens_originais = []
            for linha in linhas:
                item = linha.strip()
                if item:  # ignora linhas vazias
                    self.itens_originais.append(item)

            total = len(self.itens_originais)
            tamanho_mb = os.path.getsize(caminho) / (1024 * 1024)

            self.label_stats.config(
                text=f"Arquivo carregado: {total:,} itens  |  Tamanho: {tamanho_mb:.2f} MB"
            )
            self.status.config(text=f"Carregado: {os.path.basename(caminho)} ({total:,} itens)")
            self.txt_removidos.delete("1.0", tk.END)
            self.txt_limpos.delete("1.0", tk.END)
            self.txt_limpos.insert(
                tk.END,
                f"Arquivo carregado com {total:,} itens.\n\n"
                f"Clique em 'Limpar Duplicados e Ordenar' para processar."
            )

            # === BARRA DE PROGRESSO ENCHE AQUANDO CARREGA (vermelha) ===
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Progresso: 0%  |  Carregando arquivo...")
            self.root.update_idletasks()

            for i, item in enumerate(self.itens_originais):
                # Atualiza progresso a cada ~10% ou a cada 1000 itens (bem fluido)
                if i % max(1, total // 10) == 0:
                    progresso = int((i + 1) / total * 100)
                    self.progress_bar["value"] = progresso
                    self.progress_label.config(text=f"Progresso: {progresso}%  |  Carregando...")
                    self.root.update_idletasks()

            # Barra finaliza
            self.progress_bar["value"] = 100
            self.progress_label.config(text="Progresso: 100%  |  Carregado!")

            if total > 500000:
                messagebox.showinfo(
                    "Arquivo grande",
                    f"O arquivo tem {total:,} linhas.\n"
                    "O processamento pode demorar alguns segundos.\n"
                    "Aguarde a finalização."
                )

        except Exception as e:
            messagebox.showerror("Erro ao ler arquivo", str(e))
            # barra vermelha em caso de erro
            self.progress_bar["value"] = 100
            self.progress_label.config(text="Progresso: 100%  |  Erro ao carregar!")

    def detectar_modo(self):
        """Detecta se parece ser lista de PIN ou wordlist geral."""
        if not self.itens_originais:
            return "wordlist"

        amostra = self.itens_originais[: min(200, len(self.itens_originais))]
        pins = 0
        for item in amostra:
            limpo = "".join(c for c in item if c.isdigit())
            if len(limpo) == 8 and limpo == item.strip():
                pins += 1

        if pins / len(amostra) > 0.7:
            return "pin"
        return "wordlist"

    def processar(self):
        if not self.itens_originais:
            messagebox.showwarning("Aviso", "Carregue um arquivo primeiro.")
            return

        modo = self.modo.get()
        if modo == "auto":
            modo = self.detectar_modo()

        case_sensitive = self.case_sensitive.get()

        self.status.config(text="Processando... aguarde...")
        self.root.update_idletasks()

        # === BARRA DE PROGRESSO VERDE (novo) ===
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Progresso: 0%  |  Iniciando processamento...")
        self.root.update_idletasks()

        # Remove duplicados mantendo ordem de primeira aparição
        vistos = OrderedDict()
        self.itens_removidos = []

        total_itens = len(self.itens_originais)
        for i, item in enumerate(self.itens_originais):
            chave = item if case_sensitive else item.lower()

            if chave in vistos:
                self.itens_removidos.append(item)
            else:
                vistos[chave] = item  # guarda a versão original (primeira aparição)

            # Atualiza progresso a cada ~10% ou a cada 1000 itens
            if i % max(1, total_itens // 10) == 0:
                progresso = int((i + 1) / total_itens * 100)
                self.progress_bar["value"] = progresso
                self.progress_label.config(text=f"Progresso: {progresso}%  |  Removendo duplicados...")
                self.root.update_idletasks()

        self.itens_unicos = list(vistos.values())

        # Ordenação
        if modo == "pin":
            # Tenta ordenar numericamente (só números)
            def chave_ordenacao(x):
                digitos = "".join(c for c in x if c.isdigit())
                return int(digitos) if digitos else 0

            self.itens_unicos.sort(key=chave_ordenacao)
            tipo_ordenacao = "numérica (PIN)"
        else:
            # Ordem alfabética
            if case_sensitive:
                self.itens_unicos.sort()
            else:
                self.itens_unicos.sort(key=str.lower)
            tipo_ordenacao = "alfabética"

        # Estatísticas
        total_original = len(self.itens_originais)
        total_unico = len(self.itens_unicos)
        total_removido = len(self.itens_removidos)

        self.label_stats.config(
            text=f"Original: {total_original:,}  |  Únicos: {total_unico:,}  |  Removidos: {total_removido:,}  |  Ordenação: {tipo_ordenacao}"
        )

        # === Mostra removidos ===
        self.txt_removidos.delete("1.0", tk.END)

        if self.itens_removidos:
            # Conta quantas vezes cada um foi removido
            contagem = {}
            for item in self.itens_removidos:
                chave = item if case_sensitive else item.lower()
                contagem[chave] = contagem.get(chave, 0) + 1

            self.txt_removidos.insert(tk.END, f"Total de duplicados removidos: {total_removido:,}\n")
            self.txt_removidos.insert(tk.END, f"Itens únicos que tinham cópias: {len(contagem):,}\n")
            self.txt_removidos.insert(tk.END, "-" * 50 + "\n\n")

            # Ordena a contagem para exibição
            if modo == "pin":
                itens_ordenados = sorted(
                    contagem.items(),
                    key=lambda x: int("".join(c for c in x[0] if c.isdigit()) or 0)
                )
            else:
                itens_ordenados = sorted(contagem.items(), key=lambda x: x[0].lower())

            # Limita a exibição se for muito grande
            limite_exibicao = 5000
            for i, (item, qtd) in enumerate(itens_ordenados):
                if i >= limite_exibicao:
                    self.txt_removidos.insert(
                        tk.END,
                        f"\n... e mais {len(itens_ordenados) - limite_exibicao:,} itens (lista muito grande)\n"
                    )
                    break
                self.txt_removidos.insert(tk.END, f"{item}  →  removido {qtd}x\n")
        else:
            self.txt_removidos.insert(tk.END, "Nenhum item duplicado encontrado!\n")

        # === Mostra lista limpa ===
        self.txt_limpos.delete("1.0", tk.END)
        self.txt_limpos.insert(tk.END, f"Lista limpa e ordenada ({total_unico:,} itens):\n")
        self.txt_limpos.insert(tk.END, f"Ordenação: {tipo_ordenacao}\n")
        self.txt_limpos.insert(tk.END, "-" * 50 + "\n\n")

        limite_exibicao = 10000
        for i, item in enumerate(self.itens_unicos):
            if i >= limite_exibicao:
                self.txt_limpos.insert(
                    tk.END,
                    f"\n... e mais {total_unico - limite_exibicao:,} itens.\n"
                    f"(A lista completa será salva no arquivo)"
                )
                break
            self.txt_limpos.insert(tk.END, item + "\n")

        self.status.config(
            text=f"Concluído! {total_removido:,} duplicados removidos | "
                 f"{total_unico:,} itens únicos | Ordenação {tipo_ordenacao}"
        )

        # Barra de progresso finaliza
        self.progress_bar["value"] = 100
        self.progress_label.config(text="Progresso: 100%  |  Concluído!")

    def salvar_arquivo(self):
        if not self.itens_unicos:
            messagebox.showwarning("Aviso", "Processe a lista primeiro.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar lista limpa",
            defaultextension=".txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile="wordlist_limpa.txt",
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                for item in self.itens_unicos:
                    f.write(item + "\n")
            messagebox.showinfo(
                "Sucesso",
                f"Lista salva com sucesso!\n\n{caminho}\n\n{len(self.itens_unicos):,} itens únicos."
            )
            self.status.config(text=f"Salvo em: {os.path.basename(caminho)}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def copiar_limpa(self):
        if not self.itens_unicos:
            messagebox.showwarning("Aviso", "Processe a lista primeiro.")
            return

        # Limita o que vai para a área de transferência se for muito grande
        if len(self.itens_unicos) > 50000:
            resposta = messagebox.askyesno(
                "Lista grande",
                f"A lista tem {len(self.itens_unicos):,} itens.\n"
                "Copiar tudo pode demorar ou travar.\n\n"
                "Deseja copiar mesmo assim?"
            )
            if not resposta:
                return

        texto = "\n".join(self.itens_unicos)
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.status.config(text="Lista limpa copiada para a área de transferência!")

    def limpar_tela(self):
        self.txt_removidos.delete("1.0", tk.END)
        self.txt_limpos.delete("1.0", tk.END)
        self.itens_originais = []
        self.itens_unicos = []
        self.itens_removidos = []
        self.label_stats.config(text="Nenhum arquivo carregado ainda.")
        self.status.config(text="Tela limpa.")
        # Barra volta pro estado inicial
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Progresso: 0%  |  Pronto")


def main():
    root = tk.Tk()
    app = WordlistCleaner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
