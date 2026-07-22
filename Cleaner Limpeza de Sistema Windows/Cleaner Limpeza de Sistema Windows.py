#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyCleaner - Sistema de Limpeza 
Windows 10 / 11 - Versão com Duplo-Clique e Exibição de Caminhos
"""

import os
import sys
import shutil
import platform
import threading
import glob
import time
import subprocess                     # <-- ADICIONADO
from pathlib import Path

from tkinter import (
    Tk, Frame, Label, Button, Checkbutton, IntVar, BooleanVar,
    Canvas, Scrollbar, Text,
    messagebox, ttk
)

# ============================================================
# TEMA ESCURO
# ============================================================
CORES = {
    "bg": "#2b2b2b",
    "fg": "#e0e0e0",
    "select": "#3c3c3c",
    "btn": "#4a4a4a",
    "btn_hover": "#5a5a5a",
    "accent": "#07b115",
    "danger": "#e74c3c",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "header_bg": "#1e1e1e",
    "tree_bg": "#252526",
    "check_bg": "#333333",
    "progress_bg": "#404040",
    "progress_fill": "#0be942",
    "blue": "#0ebcd3",        # Azul vibrante
}

# ============================================================
# FUNÇÃO PARA ABRIR LIMPEZA DE DISCO DO WINDOWS
# ============================================================
def abrir_limpeza_de_disco():
    """Abre a ferramenta nativa 'Limpeza de Disco' do Windows (cleanmgr)."""
    try:
        subprocess.Popen("cleanmgr.exe", shell=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a Limpeza de Disco:\n\n{e}")


# ============================================================
# CATEGORIA DE LIMPEZA
# ============================================================
class CategoriaLimpeza:
    def __init__(self, nome, descricao, icone="📁", habilitado=False):
        self.nome = nome
        self.descricao = descricao
        self.icone = icone
        self.habilitado = BooleanVar(value=habilitado)
        self.sub_itens = []
        self.espaco_estimado = 0
        self.arquivos_encontrados = []
        # --- CAMINHOS LEGÍVEIS PARA EXIBIR ---
        self.caminhos_exibir = []  # lista de (nome_amigavel, caminho_real)

    def adicionar_sub_item(self, nome, lista_caminhos, descricao=""):
        """Adiciona um sub-item com nome amigável e lista de padrões de caminho."""
        self.sub_itens.append({
            "nome": nome,
            "caminhos": lista_caminhos,
            "descricao": descricao,
        })
        # Extrai caminhos reais ignorando placeholders (ex: __dns__)
        for p in lista_caminhos:
            caminho_limpo = p.replace("**/*", "").replace("**\\*", "").replace("*", "").rstrip("\\/")
            if caminho_limpo and not caminho_limpo.startswith("__"):
                # Evita duplicatas
                if not any(caminho_limpo == c[1] for c in self.caminhos_exibir):
                    self.caminhos_exibir.append((nome, caminho_limpo))

    def obter_caminhos_unicos(self):
        """Retorna lista de caminhos únicos que existem no disco."""
        vistos = set()
        unicos = []
        for nome, caminho in self.caminhos_exibir:
            if caminho not in vistos and os.path.exists(caminho):
                vistos.add(caminho)
                unicos.append((nome, caminho))
        return unicos

    def obter_todos_sub_itens_com_caminhos(self):
        """
        Retorna uma lista detalhada de todos os sub-itens com seus caminhos.
        Cada elemento: (nome_sub_item, lista_de_caminhos_existentes)
        """
        resultado = []
        for item in self.sub_itens:
            caminhos_validos = []
            for pattern in item["caminhos"]:
                if pattern.startswith("__"):
                    continue  # placeholder
                caminho_base = pattern.replace("**/*", "").replace("**\\*", "").replace("*", "").rstrip("\\/")
                if caminho_base and os.path.exists(caminho_base):
                    if caminho_base not in caminhos_validos:
                        caminhos_validos.append(caminho_base)
            if caminhos_validos:
                resultado.append((item["nome"], item.get("descricao", ""), caminhos_validos))
        return resultado

    def calcular_tamanho(self):
        """Percorre os padrões e calcula o espaço total ocupado."""
        total = 0
        self.arquivos_encontrados = []
        for item in self.sub_itens:
            for pattern in item["caminhos"]:
                try:
                    for path in glob.glob(pattern, recursive=True):
                        if os.path.isfile(path):
                            try:
                                total += os.path.getsize(path)
                                self.arquivos_encontrados.append(path)
                            except:
                                pass
                        elif os.path.isdir(path):
                            for root, dirs, files in os.walk(path):
                                for f in files:
                                    fp = os.path.join(root, f)
                                    try:
                                        total += os.path.getsize(fp)
                                        self.arquivos_encontrados.append(fp)
                                    except:
                                        pass
                except:
                    pass
        self.espaco_estimado = total
        return total

    def limpar(self, callback=None):
        """Remove todos os arquivos encontrados."""
        removidos = 0
        erros = 0
        total = len(self.arquivos_encontrados)
        for i, path in enumerate(self.arquivos_encontrados):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    removidos += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    removidos += 1
            except:
                erros += 1
            if callback and total > 0:
                callback(i + 1, total, f"Limpando {self.nome}...")
        self.arquivos_encontrados = []
        self.espaco_estimado = 0
        return removidos, erros


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def formatar_tamanho(bytes_):
    """Formata bytes em unidade legível."""
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1024 ** 3:
        return f"{bytes_ / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_ / (1024 ** 3):.2f} GB"


def abrir_pasta_explorer(caminho):
    """Abre uma pasta no Windows Explorer."""
    try:
        os.startfile(caminho)
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir:\n{caminho}\n\n{e}")
        return False


# ============================================================
# CATEGORIAS PADRÃO PARA WINDOWS
# ============================================================
def construir_categorias():
    categorias = []

    windir = os.environ.get("WINDIR", "C:\\Windows")
    temp = os.environ.get("TEMP", "")
    tmp = os.environ.get("TMP", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")

    # ================================================================
    # 1. ARQUIVOS TEMPORÁRIOS
    # ================================================================
    cat_temp = CategoriaLimpeza(
        "Arquivos Temporários",
        "Remove arquivos temporários do Windows e aplicativos",
        "🗑️"
    )
    if temp:
        cat_temp.adicionar_sub_item(
            "Temp (TEMP)",
            [os.path.join(temp, "**/*")],
            "Arquivos temporários do usuário (%TEMP%)"
        )
    if tmp:
        cat_temp.adicionar_sub_item(
            "Temp (TMP)",
            [os.path.join(tmp, "**/*")],
            "Arquivos temporários alternativos (%TMP%)"
        )
    cat_temp.adicionar_sub_item(
        "Windows Temp",
        [os.path.join(windir, "Temp", "**/*")],
        "Arquivos temporários do sistema (C:\\Windows\\Temp)"
    )
    cat_temp.adicionar_sub_item(
        "Arquivos .log (raiz usuário)",
        [os.path.join(userprofile, "*.log")],
        "Arquivos de log na raiz do perfil do usuário"
    )
    categorias.append(cat_temp)

    # ================================================================
    # 2. CACHE DE NAVEGADORES
    # ================================================================
    cat_browser = CategoriaLimpeza(
        "Cache de Navegadores",
        "Remove cache do Chrome, Edge e Firefox",
        "🌐"
    )
    chrome_cache = os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Cache")
    if os.path.exists(chrome_cache):
        cat_browser.adicionar_sub_item(
            "Chrome Cache",
            [os.path.join(chrome_cache, "**/*")],
            f"Cache do Google Chrome\n\n{chrome_cache}"
        )
    edge_cache = os.path.join(localappdata, "Microsoft", "Edge", "User Data", "Default", "Cache")
    if os.path.exists(edge_cache):
        cat_browser.adicionar_sub_item(
            "Edge Cache",
            [os.path.join(edge_cache, "**/*")],
            f"Cache do Microsoft Edge: {edge_cache}"
        )
    firefox_profiles = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(firefox_profiles):
        for profile in glob.glob(os.path.join(firefox_profiles, "*", "cache2")):
            cat_browser.adicionar_sub_item(
                "Firefox Cache",
                [os.path.join(profile, "**/*")],
                f"Cache do Firefox: {profile}"
            )
    categorias.append(cat_browser)

    # ================================================================
    # 3. LIXEIRA
    # ================================================================
    cat_lixo = CategoriaLimpeza(
        "Lixeira / Recycle Bin\n",
        "Esvazia a lixeira do sistema (requer Admin)\n",
        "♻️"
    )
    drive = os.path.splitdrive(windir)[0]
    cat_lixo.adicionar_sub_item(
        "Lixeira ($Recycle.Bin)\n",
        [os.path.join(drive, "$Recycle.Bin", "**/*")],
        "Conteúdo da lixeira do sistema\n\n (requer privilégios de administrador)"
    )
    categorias.append(cat_lixo)

    # ================================================================
    # 4. DOCUMENTOS RECENTES
    # ================================================================
    cat_recent = CategoriaLimpeza(
        "Documentos Recentes",
        "Remove atalhos de arquivos recentes do Explorer",
        "📄"
    )
    recent_dir = os.path.join(appdata, "Microsoft", "Windows", "Recent")
    if os.path.exists(recent_dir):
        cat_recent.adicionar_sub_item(
            "Atalhos Recentes",
            [os.path.join(recent_dir, "*")],
            f"Atalhos de documentos recentes: {recent_dir}"
        )
    categorias.append(cat_recent)

    # ================================================================
    # 5. CACHE DO SISTEMA (Thumbnails, Prefetch)
    # ================================================================
    cat_sys = CategoriaLimpeza(
        "Cache do Sistema",
        "Remove prefetch, thumbnails e caches diversos do Windows",
        "⚙️"
    )
    prefetch = os.path.join(windir, "Prefetch")
    if os.path.exists(prefetch):
        cat_sys.adicionar_sub_item(
            "Prefetch",
            [os.path.join(prefetch, "*")],
            f"Arquivos de pré-carregamento\n\n {prefetch}"
        )
    thumb = os.path.join(localappdata, "Microsoft", "Windows", "Explorer")
    if os.path.exists(thumb):
        cat_sys.adicionar_sub_item(
            "Thumbnail Cache",
            [os.path.join(thumb, "thumbcache_*.db"),
             os.path.join(thumb, "*.db")],
            f"Cache de miniaturas: {thumb}"
        )
    cat_sys.adicionar_sub_item(
        "DNS Cache",
        ["__dns__"],
        "Cache DNS (ipconfig /flushdns) - não possui pasta física"
    )
    categorias.append(cat_sys)

    # ================================================================
    # 6. ARQUIVOS DE LOG DO WINDOWS
    # ================================================================
    cat_logs = CategoriaLimpeza(
        "Arquivos de Log\n",
        "Remove logs do Windows (.log, .etl)",
        "📋"
    )
    cat_logs.adicionar_sub_item(
        "Windows Logs\n",
        [os.path.join(windir, "Logs", "**/*")],
        f"Logs do sistema: {os.path.join(windir, 'Logs')}"
    )
    cat_logs.adicionar_sub_item(
        "Arquivos .etl (LogFiles)\n",
        [os.path.join(windir, "System32", "LogFiles", "**/*")],
        f"ETL traces: {os.path.join(windir, 'System32', 'LogFiles')}"
    )
    categorias.append(cat_logs)

    # ================================================================
    # 7. ARQUIVOS RESIDUAIS (.bak, .old, .tmp)
    # ================================================================
    cat_backup = CategoriaLimpeza(
        "Arquivos Backup/Residual\n",
        "Remove .bak, .old, .log no perfil do usuário\n",
        "📎"
    )
    cat_backup.adicionar_sub_item(
        "Arquivos .bak\n",
        [os.path.join(userprofile, "**/*.bak")],
        f"Arquivos de backup (*.bak) em: {userprofile}"
    )
    cat_backup.adicionar_sub_item(
        "Arquivos .old\n",
        [os.path.join(userprofile, "**/*.old")],
        f"Arquivos antigos (*.old) em: {userprofile}"
    )
    cat_backup.adicionar_sub_item(
        "Arquivos .log (user)\n",
        [os.path.join(userprofile, "**/*.log")],
        f"Arquivos de log (*.log) em: {userprofile}"
    )
    categorias.append(cat_backup)

    # ================================================================
    # 8. HISTÓRICO DO EXPLORADOR
    # ================================================================
    cat_history = CategoriaLimpeza(
        "Histórico do Explorador\n",
        "Remove histórico de pesquisa e execução recentes\n",
        "🔍"
    )
    # RunMRU é via registro, não tem pasta física
    cat_history.adicionar_sub_item(
        "Execução Recente (RunMRU)\n",
        ["__runmru__"],
        "Histórico de comandos executados (regedit) - sem pasta"
    )
    if os.path.exists(recent_dir):
        cat_history.adicionar_sub_item(
            "Documentos Recentes\n",
            [os.path.join(recent_dir, "*")],
            f"Atalhos recentes do Explorer\n\n{recent_dir}"
        )
        
    categorias.append(cat_history)

    return categorias

# ============================================================
# INTERFACE GRÁFICA
# ============================================================
class PyCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cleaner - Limpeza de Sistema (Windows)")
        self.root.geometry("1100x720")
        self.root.state("zoomed")
        self.root.minsize(950, 600)
        self.root.configure(bg=CORES["bg"])

        self.categorias = construir_categorias()
        self.analisando = False
        self.limpando = False

        self._configurar_estilo()
        self._construir_header()
        self._construir_main()
        self._construir_footer()

        self.root.protocol("WM_DELETE_WINDOW", self._sair)
        self.atualizar_status(
            "Pronto. Clique em 'Analisar' para verificar espaço recuperável. "
            "Duplo clique numa categoria para ver seus caminhos e abrir no Explorer."
        )

    def _configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CORES["tree_bg"],
                        foreground=CORES["fg"],
                        fieldbackground=CORES["tree_bg"],
                        rowheight=28)
        style.map("Treeview", background=[("selected", CORES["accent"])])
        style.configure("Vertical.TScrollbar", background=CORES["btn"],
                        troughcolor=CORES["bg"], arrowcolor=CORES["fg"])
        style.configure("Horizontal.TProgressbar", background=CORES["progress_fill"],
                        troughcolor=CORES["progress_bg"], thickness=20)
        style.configure("TLabelframe", background=CORES["bg"], foreground=CORES["fg"])
        style.configure("TLabelframe.Label", background=CORES["bg"], foreground=CORES["fg"])
        style.configure("TButton", background=CORES["btn"], foreground=CORES["fg"],
                        borderwidth=1, focuscolor="none", relief="flat")
        style.map("TButton",
                  background=[("active", CORES["btn_hover"]), ("disabled", "#555555")],
                  foreground=[("disabled", "#888888")])

    def _construir_header(self):
        header = Frame(self.root, bg=CORES["header_bg"], height=40)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        Label(header, text="🪟 Cleaner - Limpeza de Sistema (Windows)",
              font=("Segoe UI", 16, "bold"),
              bg=CORES["header_bg"], fg=CORES["accent"]).pack(side="left", padx=15, pady=8)

        Label(header, text="• Duplo Clique para ver caminhos •",
              font=("Segoe UI", 9),
              bg=CORES["header_bg"], fg=CORES["fg"]).pack(side="left", padx=5, pady=8)

        Label(header,
              text=f"Windows {platform.release()} | {platform.machine()}",
              font=("Segoe UI", 8),
              bg=CORES["header_bg"], fg="#888888").pack(side="right", padx=15, pady=8)

    def _construir_main(self):
        main = Frame(self.root, bg=CORES["bg"])
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # --- PAINEL ESQUERDO (Lista de categorias) ---
        left = Frame(main, bg=CORES["bg"])
        left.pack(side="left", fill="both", expand=True)

        Label(left, text="📌  Categorias de Limpeza  (duplo clique = ver caminhos)",
              font=("Segoe UI", 11, "bold"),
              bg=CORES["bg"], fg=CORES["fg"], anchor="w").pack(fill="x", padx=5, pady=(5, 5))

        # Canvas + Scrollbar para as categorias
        canvas = Canvas(left, bg=CORES["bg"], highlightthickness=0)
        scroll = Scrollbar(left, orient="vertical", command=canvas.yview)
        self.scroll_frame = Frame(canvas, bg=CORES["bg"])
        self.scroll_frame.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.labels_espaco = []
        self.frames_categoria = []

        for cat in self.categorias:
            frame = Frame(self.scroll_frame, bg=CORES["check_bg"],
                          highlightbackground=CORES["select"],
                          highlightthickness=1, padx=8, pady=4)
            frame.pack(fill="x", padx=5, pady=3)
            self.frames_categoria.append(frame)

            # Handler de duplo clique para abrir caminhos
            def _make_handler(c):
                return lambda event: self._mostrar_caminhos_categoria(c)
            handler = _make_handler(cat)

            frame.bind("<Double-Button-1>", handler)

            cb = Checkbutton(frame,
                             text=f"{cat.icone}  {cat.nome}",
                             variable=cat.habilitado,
                             font=("Segoe UI", 9, "bold"),
                             bg=CORES["check_bg"], fg=CORES["fg"],
                             selectcolor=CORES["check_bg"],
                             activebackground=CORES["select"],
                             activeforeground=CORES["fg"],
                             command=self._atualizar_espaco_visivel)
            cb.pack(side="left", anchor="w")
            cb.bind("<Double-Button-1>", handler)

            lbl = Label(frame, text="0 B",
                        font=("Segoe UI", 10),
                        bg=CORES["check_bg"], fg="#F8AB05")
            lbl.pack(side="right")
            self.labels_espaco.append(lbl)

            Label(frame, text=cat.descricao,
                  font=("Segoe UI", 10),
                  bg=CORES["check_bg"], fg="#C76306",
                  anchor="w").pack(fill="x", padx=(25, 0))


            Label(frame,
                text=cat.descricao,
                font=("Segoe UI", 10),
                bg=CORES["check_bg"],
                fg="#0AEE0A",
                anchor="w").pack(fill="x", padx=(25, 0))

            # Mostrar caminhos da categoria
            caminhos = [c for _, c in cat.obter_caminhos_unicos()]
            if caminhos:
                Label(frame,
                    text="\n".join(caminhos),
                    font=("Consolas", 10),
                    bg=CORES["check_bg"],
                    fg="#07F02E",
                    justify="left",
                    anchor="w",
                    wraplength=500).pack(fill="x", padx=(25, 0), pady=(0, 4))
            

        # --- PAINEL DIREITO (Informações + Ações) ---
        right = Frame(main, bg=CORES["bg"], width=380)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        # ---- Painel de Caminhos detalhados ----
        caminhos_frame = ttk.LabelFrame(right, text="📂  Caminhos da Categoria",
                                        padding=(8, 8))
        caminhos_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.text_caminhos = Text(caminhos_frame,
                                  bg=CORES["tree_bg"],
                                  fg=CORES["fg"],
                                  font=("Consolas", 9),
                                  wrap="word",
                                  height=12,
                                  relief="flat",
                                  borderwidth=0,
                                  state="disabled",
                                  padx=5, pady=5)
        self.text_caminhos.pack(fill="both", expand=True)

        # Bind para abrir caminho com duplo clique no texto
        self.text_caminhos.bind("<Double-Button-1>", self._abrir_caminho_do_texto)

        # ---- Espaço recuperável ----
        esp_frame = ttk.LabelFrame(right, text="💾 Espaço Recuperável",
                                   padding=(10, 10))
        esp_frame.pack(fill="x", pady=(0, 10))

        self.label_espaco_total = Label(esp_frame, text="0 B",
                                        font=("Segoe UI", 24, "bold"),
                                        bg=CORES["bg"], fg=CORES["success"])
        self.label_espaco_total.pack()

        Label(esp_frame, text="espaço estimado (após análise)",
              font=("Segoe UI", 8),
              bg=CORES["bg"], fg="#0AEB3B").pack()

        # ---- Ações ----
        acoes = ttk.LabelFrame(right, text="⚡ Ações", padding=(10, 10))
        acoes.pack(fill="x", pady=(0, 10))

        self.btn_analisar = Button(acoes, text="🔍  Analisar",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=CORES["accent"], fg="black",
                                   padx=15, pady=8,
                                   relief="flat", borderwidth=0,
                                   cursor="hand2",
                                   command=self.analisar)
        self.btn_analisar.pack(fill="x", pady=2)

        self.btn_limpar = Button(acoes, text="🧹  Limpar Selecionados",
                                 font=("Segoe UI", 10, "bold"),
                                 bg=CORES["danger"], fg="black",
                                 padx=15, pady=8,
                                 relief="flat", borderwidth=0,
                                 cursor="hand2", state="disabled",
                                 command=self.limpar)
        self.btn_limpar.pack(fill="x", pady=2)

        # ===== BOTÃO PEQUENO: LIMPEZA DE DISCO DO WINDOWS =====
        self.btn_diskclean = Button(
            acoes,
            text="🔄  Limpeza de Disco (Windows)",
            font=("Segoe UI", 9, "bold"),
            bg=CORES["blue"],      # <-- AZUL (#0ebcd3)
            fg="black",           
            padx=8, pady=4,
            relief="flat", borderwidth=0,
            cursor="hand2",
            command=abrir_limpeza_de_disco
        )
        self.btn_diskclean.pack(fill="x", pady=(2, 6))
        # ======================================================

        self.btn_selecionar = Button(acoes, text="✅  Selecionar Todos",
                                     font=("Segoe UI", 9, "bold"),
                                     bg=CORES["btn"], fg=CORES["fg"],
                                     padx=10, pady=5,
                                     relief="flat", borderwidth=0,
                                     cursor="hand2",
                                     command=self.selecionar_todos)
        self.btn_selecionar.pack(fill="x", pady=2)

        self.btn_desselecionar = Button(acoes, text="⬜  Desmarcar Todos",
                                        font=("Segoe UI", 9, "bold"),
                                        bg=CORES["btn"], fg=CORES["fg"],
                                        padx=10, pady=5,
                                        relief="flat", borderwidth=0,
                                        cursor="hand2",
                                        command=self.desselecionar_todos)
        self.btn_desselecionar.pack(fill="x", pady=2)

        # ---- Barra de progresso ----
        prog_frame = Frame(right, bg=CORES["bg"])
        prog_frame.pack(fill="x", pady=(0, 5))
        self.progress = ttk.Progressbar(prog_frame, mode="determinate",
                                        style="Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        self.label_progresso = Label(prog_frame, text="",
                                     font=("Segoe UI", 8),
                                     bg=CORES["bg"], fg="#888888",
                                     anchor="w")
        self.label_progresso.pack(fill="x")

    def _construir_footer(self):
        footer = Frame(self.root, bg=CORES["header_bg"], height=70)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.status_label = Label(footer, text="Pronto.",
                                  font=("Segoe UI", 8),
                                  bg=CORES["header_bg"], fg="#888888",
                                  anchor="w")
        self.status_label.pack(side="left", padx=10, pady=2)

        self.status_detail = Label(footer, text="",
                                   font=("Segoe UI", 8),
                                   bg=CORES["header_bg"], fg="#666666",
                                   anchor="e")
        self.status_detail.pack(side="right", padx=10, pady=2)

    # ================================================================
    # MÉTODOS AUXILIARES
    # ================================================================

    def atualizar_status(self, msg):
        self.status_label.config(text=msg)
        self.root.update_idletasks()

    def _atualizar_espaco_visivel(self):
        """Atualiza os labels de espaço ao lado de cada categoria."""
        total = 0
        for i, cat in enumerate(self.categorias):
            if i < len(self.labels_espaco):
                self.labels_espaco[i].config(text=formatar_tamanho(cat.espaco_estimado))
                total += cat.espaco_estimado
        self.label_espaco_total.config(text=formatar_tamanho(total))

    def _sair(self):
        if self.limpando:
            if messagebox.askyesno("Saindo", "Uma limpeza está em andamento. Deseja sair?"):
                self.root.destroy()
        else:
            self.root.destroy()

    # ================================================================
    # EXIBIÇÃO DE CAMINHOS (Duplo Clique)
    # ================================================================

    def _mostrar_caminhos_categoria(self, cat):
        """
        Exibe todos os sub-itens e seus caminhos reais no painel direito
        quando o usuário dá duplo clique na categoria.
        """
        self.text_caminhos.config(state="normal")
        self.text_caminhos.delete("1.0", "end")

        # Cabeçalho
        self.text_caminhos.insert("end", f"{cat.icone}  {cat.nome}\n")
        self.text_caminhos.insert("end", f"{'═'*50}\n")
        self.text_caminhos.insert("end", f"{cat.descricao}\n")
        self.text_caminhos.insert("end", f"{'─'*50}\n\n")

        # Obtém detalhes dos sub-itens
        sub_itens = cat.obter_todos_sub_itens_com_caminhos()

        if not sub_itens:
            # Verifica se existem placeholders (DNS, RunMRU)
            placeholders = [item["nome"] for item in cat.sub_itens
                           if any(p.startswith("__") for p in item["caminhos"])]
            if placeholders:
                self.text_caminhos.insert("end", "📌  Itens especiais (sem pasta física):\n")
                for nome in placeholders:
                    self.text_caminhos.insert("end", f"   • {nome}\n")
                self.text_caminhos.insert("end", "\n")
            self.text_caminhos.insert("end", "⚠️  Nenhum caminho físico encontrado no disco.\n")
        else:
            for nome_sub, desc, caminhos in sub_itens:
                self.text_caminhos.insert("end", f"📁 {nome_sub}\n")
                if desc:
                    self.text_caminhos.insert("end", f"   {desc}\n")
                for caminho in caminhos:
                    self.text_caminhos.insert("end", f"\n📂 {caminho}\n")
                self.text_caminhos.insert("end", "\n")

        # Mostra espaço se já foi analisado
        if cat.espaco_estimado > 0:
            self.text_caminhos.insert("end", f"{'─'*60}\n")
            self.text_caminhos.insert("end",
                f"💾 Espaço ocupado: {formatar_tamanho(cat.espaco_estimado)}\n")
            self.text_caminhos.insert("end",
                f"📄 Arquivos encontrados: {len(cat.arquivos_encontrados)}\n")

        self.text_caminhos.config(state="disabled")

        # Tenta abrir o primeiro caminho no Explorer
        caminhos_unicos = cat.obter_caminhos_unicos()
        if caminhos_unicos:
            primeiro = caminhos_unicos[0][1]
            self.atualizar_status(f"📂 Categoria {cat.nome} {len(caminhos_unicos)} pasta - "
                                 f"abriu {primeiro}")
            abrir_pasta_explorer(primeiro)
        else:
            self.atualizar_status(f"📌 Categoria {cat.nome} sem pastas físicas para abrir")

    def _abrir_caminho_do_texto(self, event):
        """
        No duplo clique sobre uma linha no Text widget, tenta extrair
        o caminho e abrir no Explorer.
        """
        try:
            linha = self.text_caminhos.get("insert linestart", "insert lineend").strip()
            # Linhas com caminho começam com "📂 " ou "   📂 "
            caminho = linha.replace("📂 ", "", 1).strip()
            if caminho and os.path.exists(caminho):
                abrir_pasta_explorer(caminho)
            else:
                # Tenta pegar a linha anterior (pode ser o nome do sub-item)
                linha_anterior = self.text_caminhos.get("insert -1 lines linestart",
                                                        "insert -1 lines lineend").strip()
                caminho2 = linha_anterior.replace("📂 ", "", 1).strip()
                if caminho2 and os.path.exists(caminho2):
                    abrir_pasta_explorer(caminho2)
        except:
            pass

    # ================================================================
    # ANÁLISE
    # ================================================================

    def analisar(self):
        if self.analisando:
            return
        self.analisando = True
        self.btn_analisar.config(state="disabled", text="⏳  Analisando...")
        self.btn_limpar.config(state="disabled")

        for cat in self.categorias:
            cat.espaco_estimado = 0
            cat.arquivos_encontrados = []

        self.progress["value"] = 0
        self.progress["maximum"] = len(self.categorias)

        def _thread():
            for i, cat in enumerate(self.categorias):
                if not cat.habilitado.get():
                    continue
                self.atualizar_status(f"🔍 Analisando: {cat.nome}...")
                cat.calcular_tamanho()
                self.progress["value"] = i + 1
                self.label_progresso.config(
                    text=f"Categoria {i+1}/{len(self.categorias)}: "
                         f"{formatar_tamanho(cat.espaco_estimado)}")
                self.root.update_idletasks()
                time.sleep(0.05)

            self.analisando = False
            self.root.after(0, self._analisar_finalizada)

        threading.Thread(target=_thread, daemon=True).start()

    def _analisar_finalizada(self):
        self.btn_analisar.config(state="normal", text="🔍  Analisar")
        self.btn_limpar.config(state="normal")
        self._atualizar_espaco_visivel()
        total = sum(c.espaco_estimado for c in self.categorias if c.habilitado.get())
        self.atualizar_status(
            f"✅ Análise concluída! {formatar_tamanho(total)} podem ser recuperados.")
        self.label_progresso.config(text="Análise concluída.")
        self.progress["value"] = 0

    # ================================================================
    # LIMPEZA
    # ================================================================

    def limpar(self):
        if self.limpando:
            return
        selecionadas = [c for c in self.categorias
                       if c.habilitado.get() and c.espaco_estimado > 0]
        if not selecionadas:
            messagebox.showwarning(
                "Nada a limpar",
                "Nenhuma categoria com arquivos foi selecionada. "
                "Execute 'Analisar' primeiro."
            )
            return

        total_bytes = sum(c.espaco_estimado for c in selecionadas)
        msg = (f"Deseja realmente limpar {len(selecionadas)} categoria(s)?\n\n"
               f"Espaço a recuperar: {formatar_tamanho(total_bytes)}\n\n"
               f"⚠️  Esta ação não pode ser desfeita!")
        if not messagebox.askyesno("Confirmar Limpeza", msg, icon="warning"):
            return

        self.limpando = True
        self.btn_analisar.config(state="disabled")
        self.btn_limpar.config(state="disabled", text="⏳  Limpando...")

        total_arquivos = sum(len(c.arquivos_encontrados) for c in selecionadas)
        self.progress["maximum"] = total_arquivos if total_arquivos > 0 else 1
        self.progress["value"] = 0

        def _thread():
            total_rem = 0
            total_err = 0
            for cat in selecionadas:
                def cb(atual, total, msg_):
                    self.progress["value"] = atual
                    self.label_progresso.config(text=msg_)
                    self.status_detail.config(text=f"{atual}/{total} arquivos")
                    self.root.update_idletasks()
                r, e = cat.limpar(callback=cb)
                total_rem += r
                total_err += e
                self.root.after(0, self._atualizar_espaco_visivel)

            self.limpando = False
            self.root.after(0, lambda: self._limpeza_finalizada(total_rem, total_err))

        threading.Thread(target=_thread, daemon=True).start()

    def _limpeza_finalizada(self, removidos, erros):
        self.btn_analisar.config(state="normal", text="🔍  Analisar")
        self.btn_limpar.config(state="normal", text="🧹  Limpar Selecionados")
        self.progress["value"] = 0
        self.label_progresso.config(text="")

        if erros > 0:
            msg = (f"✅ Limpeza concluída!\n\n"
                   f"Removidos: {removidos}\n\n"
                   f"Erros (permissão): {erros}")
            self.atualizar_status(f"✅ Limpeza concluída com {erros} erro(s).")
        else:
            msg = (f"✅ Limpeza concluída com sucesso!\n\n"
                   f"Arquivos removidos: {removidos}")
            self.atualizar_status(f"✅ Limpeza concluída! {removidos} arquivo(s) removido(s).")

        self._atualizar_espaco_visivel()
        messagebox.showinfo("Limpeza Concluída", msg)

    # ================================================================
    # SELEÇÃO EM MASSA
    # ================================================================

    def selecionar_todos(self):
        for cat in self.categorias:
            cat.habilitado.set(True)
        self._atualizar_espaco_visivel()

    def desselecionar_todos(self):
        for cat in self.categorias:
            cat.habilitado.set(False)
        self._atualizar_espaco_visivel()        

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    try:
        from tkinter import Text
        root = Tk()
        app = PyCleanerGUI(root)
        root.mainloop()

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as e:
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro inesperado:\n\n{e}")
        sys.exit(1)
