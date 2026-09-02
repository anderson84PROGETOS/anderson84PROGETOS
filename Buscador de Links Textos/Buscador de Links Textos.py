import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import re
import platform

class BuscadorArquivoTxt:

    def __init__(self, root):
        self.root = root

        self.root.title("🔍 Buscador de Links & Textos")
        self.root.geometry("900x750")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(100, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass
        
        # Variáveis
        self.conteudo_arquivo = ""
        self.arquivo_carregado = False
        self.caminho_arquivo = "index.html"  # Padrão alterado para index.html
        self.carregando = False  # controle da barra de progresso

        self.criar_interface()
        self.carregar_arquivo_automatico()

    def criar_interface(self):
        # ===== TÍTULO =====
        frame_titulo = tk.Frame(self.root, bg="#1e1e2e")
        frame_titulo.pack(fill="x", padx=20, pady=(15, 5))

        titulo = tk.Label(
            frame_titulo,
            text="🔍 Buscador .html / .txt",
            font=("Segoe UI", 22, "bold"),
            fg="#cba6f7",
            bg="#1e1e2e"
        )
        titulo.pack()

        # ===== FRAME DO ARQUIVO =====
        frame_arquivo = tk.Frame(self.root, bg="#313244", relief="flat", bd=0)
        frame_arquivo.pack(fill="x", padx=20, pady=5)

        self.label_arquivo = tk.Label(
            frame_arquivo,
            text="📁 Nenhum arquivo carregado",
            font=("Segoe UI", 10),
            fg="#f38ba8",
            bg="#313244",
            pady=8,
            padx=10
        )
        self.label_arquivo.pack(side="left", fill="x", expand=True)

        btn_carregar = tk.Button(
            frame_arquivo,
            text="📂 Escolher Arquivo",
            font=("Segoe UI", 10, "bold"),
            fg="#1e1e2e",
            bg="#f9e2af",
            activebackground="#f5c211",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.escolher_arquivo
        )
        btn_carregar.pack(side="right", padx=10, pady=5)

        # ===== FRAME DE BUSCA =====
        frame_busca = tk.Frame(self.root, bg="#1e1e2e")
        frame_busca.pack(fill="x", padx=20, pady=10)

        label_busca = tk.Label(
            frame_busca,
            text="O que você procura (deixe em branco se quiser apenas extrair links)",
            font=("Segoe UI", 11, "bold"),
            fg="#a6e3a1",
            bg="#1e1e2e"
        )
        label_busca.pack(anchor="w")

        frame_input = tk.Frame(frame_busca, bg="#1e1e2e")
        frame_input.pack(fill="x", pady=(5, 0))

        self.entrada_busca = tk.Entry(
            frame_input,
            font=("Segoe UI", 14),
            fg="#cdd6f4",
            bg="#45475a",
            insertbackground="#cdd6f4",
            relief="flat",
            bd=0
        )
        self.entrada_busca.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.entrada_busca.bind("<Return>", lambda e: self.buscar())

        btn_buscar = tk.Button(
            frame_input,
            text="🔎 BUSCAR",
            font=("Segoe UI", 12, "bold"),
            fg="#1e1e2e",
            bg="#89b4fa",
            activebackground="#74c7ec",
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=8,
            command=self.buscar
        )
        btn_buscar.pack(side="right")

        # ===== OPÇÕES DE BUSCA =====
        frame_opcoes = tk.Frame(self.root, bg="#1e1e2e")
        frame_opcoes.pack(fill="x", padx=20, pady=(0, 5))

        self.var_case = tk.BooleanVar(value=False)
        check_case = tk.Checkbutton(
            frame_opcoes,
            text="Diferenciar maiúsculas/minúsculas",
            variable=self.var_case,
            font=("Segoe UI", 10),
            fg="#bac2de",
            bg="#1e1e2e",
            selectcolor="#45475a",
            activebackground="#1e1e2e",
            activeforeground="#bac2de"
        )
        check_case.pack(side="left")

        self.var_palavra_exata = tk.BooleanVar(value=False)
        check_exata = tk.Checkbutton(
            frame_opcoes,
            text="Palavra exata",
            variable=self.var_palavra_exata,
            font=("Segoe UI", 10),
            fg="#bac2de",
            bg="#1e1e2e",
            selectcolor="#45475a",
            activebackground="#1e1e2e",
            activeforeground="#bac2de"
        )
        check_exata.pack(side="left", padx=20)

        # NOVA OPÇÃO: EXTRAIR APENAS HTTP/HTTPS
        self.var_apenas_urls = tk.BooleanVar(value=False)
        check_urls = tk.Checkbutton(
            frame_opcoes,
            text="🔗 Trazer apenas URL (http/https)",
            variable=self.var_apenas_urls,
            font=("Segoe UI", 10, "bold"),
            fg="#89dceb",
            bg="#1e1e2e",
            selectcolor="#45475a",
            activebackground="#1e1e2e",
            activeforeground="#89dceb"
        )
        check_urls.pack(side="left", padx=10)

        # ===== BARRA DE PROGRESSO =====
        self.frame_progresso = tk.Frame(self.root, bg="#1e1e2e")
        self.frame_progresso.pack(fill="x", padx=20, pady=(0, 2))

        self.label_progresso = tk.Label(
            self.frame_progresso,
            text="",
            font=("Segoe UI", 9),
            fg="#f9e2af",
            bg="#1e1e2e"
        )
        self.label_progresso.pack(anchor="w")

        # Estilo da barra de progresso
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#45475a',
            background='#a6e3a1',
            darkcolor='#a6e3a1',
            lightcolor='#a6e3a1',
            bordercolor='#313244',
            thickness=20
        )

        self.barra_progresso = ttk.Progressbar(
            self.frame_progresso,
            style="Custom.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            length=300
        )
        self.barra_progresso.pack(fill="x", pady=(2, 2))

        self.label_porcentagem = tk.Label(
            self.frame_progresso,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg="#a6e3a1",
            bg="#1e1e2e"
        )
        self.label_porcentagem.pack(anchor="e")

        self.esconder_progresso()

        # ===== LABEL DE STATUS =====
        self.label_status = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg="#f9e2af",
            bg="#1e1e2e"
        )
        self.label_status.pack(fill="x", padx=20)

        # ===== ÁREA DE RESULTADOS =====
        frame_resultados = tk.Frame(self.root, bg="#1e1e2e")
        frame_resultados.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        label_resultados = tk.Label(
            frame_resultados,
            text="📋 Linhas / URL Encontradas",
            font=("Segoe UI", 12, "bold"),
            fg="#89dceb",
            bg="#1e1e2e"
        )
        label_resultados.pack(anchor="w")

        self.texto_resultados = scrolledtext.ScrolledText(
            frame_resultados,
            font=("Consolas", 11),
            fg="#cdd6f4",
            bg="#313244",
            insertbackground="#cdd6f4",
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled"
        )
        self.texto_resultados.pack(fill="both", expand=True, pady=(5, 0))

        # Estilos do texto de exibição
        self.texto_resultados.tag_configure(
            "destaque", background="#f9e2af", foreground="#1e1e2e",
            font=("Consolas", 11, "bold")
        )
        self.texto_resultados.tag_configure(
            "linha_num", foreground="#6c7086", font=("Consolas", 10)
        )
        self.texto_resultados.tag_configure("separador", foreground="#45475a")
        self.texto_resultados.tag_configure(
            "info", foreground="#a6e3a1", font=("Consolas", 11, "bold")
        )
        self.texto_resultados.tag_configure(
            "link", foreground="#89b4fa", underline=True, font=("Consolas", 11, "bold")
        )

        # ===== BARRA INFERIOR =====
        frame_inferior = tk.Frame(self.root, bg="#313244")
        frame_inferior.pack(fill="x", side="bottom")

        btn_limpar = tk.Button(
            frame_inferior,
            text="🗑️ Limpar",
            font=("Segoe UI", 10),
            fg="#1e1e2e",
            bg="#f38ba8",
            activebackground="#e06080",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.limpar
        )
        btn_limpar.pack(side="left", padx=10, pady=8)

        self.btn_mostrar_tudo = tk.Button(
            frame_inferior,
            text="📄 Mostrar Tudo",
            font=("Segoe UI", 10),
            fg="#1e1e2e",
            bg="#94e2d5",
            activebackground="#70d0c0",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.mostrar_tudo
        )
        self.btn_mostrar_tudo.pack(side="left", padx=5, pady=8)

        self.btn_cancelar = tk.Button(
            frame_inferior,
            text="⏹️ Cancelar",
            font=("Segoe UI", 10, "bold"),
            fg="#1e1e2e",
            bg="#fab387",
            activebackground="#e09070",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.cancelar_carregamento
        )

        self.label_info = tk.Label(
            frame_inferior,
            text="",
            font=("Segoe UI", 9),
            fg="#6c7086",
            bg="#313244"
        )
        self.label_info.pack(side="right", padx=10, pady=8)

    # ==========================================
    #        CONTROLE DE PROGRESSO
    # ==========================================

    def mostrar_progresso(self):
        self.label_progresso.config(text="⏳ Processando dados...")
        self.barra_progresso.pack(fill="x", pady=(2, 2))
        self.label_porcentagem.pack(anchor="e")
        self.label_progresso.pack(anchor="w")

    def esconder_progresso(self):
        self.label_progresso.config(text="")
        self.label_progresso.pack_forget()
        self.barra_progresso.pack_forget()
        self.label_porcentagem.pack_forget()

    def atualizar_progresso(self, atual, total):
        porcentagem = (atual / total) * 100 if total > 0 else 100
        self.barra_progresso["value"] = porcentagem
        tipo = "URL" if self.var_apenas_urls.get() else "linhas"
        self.label_porcentagem.config(
            text=f"{porcentagem:.1f}%  ({atual:,} / {total:,} {tipo})"
        )
        self.label_progresso.config(
            text=f"⏳ Renderizando {atual:,} de {total:,}..."
        )

    def cancelar_carregamento(self):
        self.carregando = False

    # ==========================================
    #        CARREGAR ARQUIVO AUTOMÁTICO
    # ==========================================

    def carregar_arquivo_automatico(self):
        """Tenta carregar index.html ou arquivo.txt"""
        alvos = ["index.html", "arquivo.txt"]
        dir_script = os.path.dirname(os.path.abspath(__file__))
        
        for nome in alvos:
            caminho_local = os.path.join(dir_script, nome)
            if os.path.exists(nome):
                self.carregar_conteudo(nome)
                return
            elif os.path.exists(caminho_local):
                self.carregar_conteudo(caminho_local)
                return

    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo .html ou .txt",
            filetypes=[
                ("Arquivos Suportados", "*.html *.htm *.txt"),
                ("Páginas HTML", "*.html *.htm"),
                ("Arquivos de texto", "*.txt"),
                ("Todos os arquivos", "*.*")
            ],
            initialfile="index.html"
        )
        if caminho:
            self.carregar_conteudo(caminho)

    def carregar_conteudo(self, caminho):
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for enc in encodings:
                try:
                    with open(caminho, 'r', encoding=enc) as f:
                        self.conteudo_arquivo = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            self.arquivo_carregado = True
            self.caminho_arquivo = caminho
            nome_arquivo = os.path.basename(caminho)
            num_linhas = len(self.conteudo_arquivo.splitlines())
            num_chars = len(self.conteudo_arquivo)

            self.label_arquivo.config(
                text=f"✅ {nome_arquivo} carregado!",
                fg="#a6e3a1"
            )
            self.label_info.config(
                text=f"📊 {num_linhas:,} linhas | {num_chars:,} caracteres | {nome_arquivo}"
            )

            self.mostrar_mensagem(
                f"Arquivo: {nome_arquivo} carregado com sucesso!\n\n"
                f"Total de {num_linhas:,} linhas encontradas.\n\n"
                f"Escolha uma das opções e clique em BUSCAR ou em MOSTRAR TUDO."
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir o arquivo:\n{str(e)}")
            self.label_arquivo.config(text="❌ Erro ao carregar arquivo", fg="#f38ba8")

    # ==========================================
    #        ALGORITMO DE FILTRAGEM & BUSCA
    # ==========================================

    def extrair_todas_urls(self):
        """Retorna uma lista de todas as URLs http/https do texto"""
        # Expressão regular otimizada para capturar URLs http ou https
        regex_url = r'(https?://[^\s\'"<>#]+)'
        return re.findall(regex_url, self.conteudo_arquivo)

    def buscar(self):
        if not self.arquivo_carregado:
            messagebox.showwarning("Aviso", "Por favor, carregue um arquivo primeiro!")
            return

        termo = self.entrada_busca.get().strip()
        case_sensitive = self.var_case.get()
        palavra_exata = self.var_palavra_exata.get()
        apenas_urls = self.var_apenas_urls.get()

        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", "end")

        if apenas_urls:
            # === BUSCA DE LINKS APENAS ===
            urls = self.extrair_todas_urls()
            if termo:
                termo_busca = termo if case_sensitive else termo.lower()
                urls_filtradas = []
                for url in urls:
                    url_comparar = url if case_sensitive else url.lower()
                    if palavra_exata:
                        if re.search(r'\b' + re.escape(termo_busca) + r'\b', url_comparar):
                            urls_filtradas.append(url)
                    else:
                        if termo_busca in url_comparar:
                            urls_filtradas.append(url)
                urls = urls_filtradas

            # Remover duplicatas mantendo a ordem
            urls = list(dict.fromkeys(urls))

            if urls:
                self.label_status.config(text=f"🔗 Encontradas {len(urls)} URL únicas correspondentes!", fg="#89b4fa")
                self.texto_resultados.insert("end", f"  LINKS EXTRAÍDOS ({len(urls)} Encontrados)\n", "info")
                self.texto_resultados.insert("end", "─" * 80 + "\n\n", "separador")
                for i, url in enumerate(urls, 1):
                    self.texto_resultados.insert("end", f"  [{i:>4}]: ", "linha_num")
                    self.texto_resultados.insert("end", f"{url}\n", "link")
            else:
                self.label_status.config(text="❌ Nenhuma URL encontrada.", fg="#f38ba8")
                self.texto_resultados.insert("end", "\n  ❌ Nenhuma URL corresponde aos critérios de busca.\n")

        else:
            # === BUSCA TRADICIONAL POR LINHAS ===
            if not termo:
                messagebox.showwarning("Aviso", "Digite algo para buscar no texto!")
                self.entrada_busca.focus()
                return

            linhas = self.conteudo_arquivo.splitlines()
            resultados = []
            for i, linha in enumerate(linhas, 1):
                linha_busca = linha if case_sensitive else linha.lower()
                termo_busca = termo if case_sensitive else termo.lower()

                if palavra_exata:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if re.search(r'\b' + re.escape(termo) + r'\b', linha, flags):
                        resultados.append((i, linha))
                else:
                    if termo_busca in linha_busca:
                        resultados.append((i, linha))

            if resultados:
                self.label_status.config(text=f"✅ Encontrado em {len(resultados)} linhas!", fg="#a6e3a1")
                for num, conteudo in resultados:
                    self.texto_resultados.insert("end", f"  Linha {num:>5}: ", "linha_num")
                    self.inserir_com_destaque(conteudo, termo, case_sensitive, palavra_exata)
                    self.texto_resultados.insert("end", "\n")
            else:
                self.label_status.config(text="❌ Nenhum resultado.", fg="#f38ba8")

        self.texto_resultados.config(state="disabled")

    def inserir_com_destaque(self, linha, termo, case_sensitive, palavra_exata):
        """Insere e destaca texto"""
        linha_lower = linha if case_sensitive else linha.lower()
        termo_lower = termo if case_sensitive else termo.lower()

        idx = 0
        while idx < len(linha):
            pos = linha_lower.find(termo_lower, idx)
            if pos == -1:
                self.texto_resultados.insert("end", linha[idx:])
                break
            else:
                if pos > idx:
                    self.texto_resultados.insert("end", linha[idx:pos])
                self.texto_resultados.insert("end", linha[pos:pos + len(termo)], "destaque")
                idx = pos + len(termo)

    # ==========================================
    #     MOSTRAR TUDO COM BARRA DE PROGRESSO
    # ==========================================

    def mostrar_tudo(self):
        if not self.arquivo_carregado:
            messagebox.showwarning("Aviso", "Nenhum arquivo carregado!")
            return

        if self.carregando:
            return

        self.carregando = True
        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", "end")

        self.mostrar_progresso()
        self.btn_mostrar_tudo.config(state="disabled", bg="#6c7086")
        self.btn_cancelar.pack(side="left", padx=5, pady=8)

        if self.var_apenas_urls.get():
            # Extrair apenas URLs
            dados = list(dict.fromkeys(self.extrair_todas_urls()))
            self.texto_resultados.insert("end", f"🔗 RELAÇÃO COMPLETA DE LINKS HTTP/HTTPS ({len(dados)} únicos)\n\n", "info")
            tipo_dados = "urls"
        else:
            # Mostrar linhas completas
            dados = self.conteudo_arquivo.splitlines()
            self.texto_resultados.insert("end", f"📄 CONTEÚDO COMPLETO DO DOCUMENTO ({len(dados)} linhas)\n\n", "info")
            tipo_dados = "linhas"

        self.texto_resultados.insert("end", "─" * 80 + "\n\n", "separador")
        
        total = len(dados)
        lote = max(1, total // 150)  # Renderização fluida em blocos
        self._carregar_dados_progressivo(dados, 0, total, lote, tipo_dados)

    def _carregar_dados_progressivo(self, dados, inicio, total, lote, tipo):
        if not self.carregando:
            self.texto_resultados.insert("end", "\n\n⏹️ Carregamento cancelado pelo usuário.\n", "info")
            self._finalizar_carregamento(inicio, total, cancelado=True)
            return

        fim = min(inicio + lote, total)

        for i in range(inicio, fim):
            if tipo == "urls":
                self.texto_resultados.insert("end", f"  [{i+1:>5}]: ", "linha_num")
                self.texto_resultados.insert("end", f"{dados[i]}\n", "link")
            else:
                self.texto_resultados.insert("end", f"  {i+1:>5}: ", "linha_num")
                self.texto_resultados.insert("end", f"{dados[i]}\n")

        self.atualizar_progresso(fim, total)
        self.texto_resultados.see("end")
        self.root.update_idletasks()

        if fim < total:
            self.root.after(5, self._carregar_dados_progressivo, dados, fim, total, lote, tipo)
        else:
            self.texto_resultados.insert("end", "\n" + "─" * 80 + "\n", "separador")
            self.texto_resultados.insert("end", f"  ✅ Concluído - {total:,} elementos carregados.\n", "info")
            self._finalizar_carregamento(total, total, cancelado=False)

    def _finalizar_carregamento(self, carregadas, total, cancelado=False):
        self.texto_resultados.config(state="disabled")
        self.carregando = False
        self.btn_mostrar_tudo.config(state="normal", bg="#94e2d5")
        self.btn_cancelar.pack_forget()

        if cancelado:
            self.label_status.config(text=f"⏹️ Parou em {carregadas:,} de {total:,}", fg="#fab387")
        else:
            self.label_status.config(text=f"✅ Todos os dados ({total:,}) foram renderizados!", fg="#a6e3a1")

        self.root.after(3000, self.esconder_progresso)

    # ==========================================
    #        UTILITÁRIOS
    # ==========================================

    def mostrar_mensagem(self, msg):
        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", "end")
        self.texto_resultados.insert("end", f"\n  {msg}\n", "info")
        self.texto_resultados.config(state="disabled")

    def limpar(self):
        self.carregando = False
        self.entrada_busca.delete(0, "end")
        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", "end")
        self.texto_resultados.config(state="disabled")
        self.label_status.config(text="")
        self.esconder_progresso()
        self.entrada_busca.focus()


# ===== EXECUTAR =====
if __name__ == "__main__":
    root = tk.Tk()
    largura, altura = 900, 750
    x = (root.winfo_screenwidth() // 2) - (largura // 2)
    y = (root.winfo_screenheight() // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")
    app = BuscadorArquivoTxt(root)
    root.mainloop()
