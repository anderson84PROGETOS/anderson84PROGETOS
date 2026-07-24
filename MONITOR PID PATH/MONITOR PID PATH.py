import os
import sys
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import hashlib
import webbrowser
from datetime import datetime
import time


class ProcessMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("MONITOR - PID & PATH")
        self.root.geometry("1250x650")
        self.root.state("zoomed")
        self.root.minsize(950, 450)

        # --- Tema Hacker Verde ---
        self.root.configure(bg="#0a0a0a")
        style = ttk.Style()
        style.theme_use("clam")

        bg_dark = "#0a0a0a"
        bg_medium = "#111111"
        bg_light = "#1a1a1a"
        fg_green = "#00ff41"
        fg_dim = "#00cc33"
        select_bg = "#003300"
        select_fg = "#00ff41"

        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_green, font=("Consolas", 9))
        style.configure("TButton", background=bg_medium, foreground=fg_green,
                        font=("Consolas", 9, "bold"), borderwidth=1, focusthickness=0)
        style.map("TButton",
                  background=[("active", "#003300"), ("pressed", "#004400")],
                  foreground=[("active", "#66ff66")])
        style.configure("TEntry", fieldbackground=bg_light, foreground=fg_green,
                        insertcolor=fg_green, font=("Consolas", 9), borderwidth=1)
        style.configure("Treeview", background=bg_medium, foreground=fg_dim,
                        fieldbackground=bg_medium, font=("Consolas", 9),
                        borderwidth=0, rowheight=24)
        style.map("Treeview",
                  background=[("selected", select_bg)],
                  foreground=[("selected", select_fg)])
        style.configure("Treeview.Heading", background=bg_light, foreground=fg_green,
                        font=("Consolas", 9, "bold"), borderwidth=1)
        style.map("Treeview.Heading",
                  background=[("active", "#002200")],
                  foreground=[("active", "#66ff66")])

        style.configure("Vertical.TScrollbar",
                        background="#FFFFFF",
                        troughcolor="#002200",
                        bordercolor="#003300",
                        arrowcolor="#00ff41",
                        lightcolor="#007700",
                        darkcolor="#003300")

        style.configure("Horizontal.TScrollbar",
                        background="#FFFFFF",
                        troughcolor="#002200",
                        bordercolor="#003300",
                        arrowcolor="#00ff41",
                        lightcolor="#007700",
                        darkcolor="#003300")

        style.configure("StatusBar.TLabel", background=bg_dark, foreground="#008800",
                        font=("Consolas", 8))
        style.configure("Count.TLabel", background=bg_dark, foreground=fg_dim,
                        font=("Consolas", 9, "bold"))

        # --- Frame Superior ---
        top_frame = ttk.Frame(root, padding=5)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="⏣ MONITOR - PID & PATH ⏣",
                  font=("Consolas", 14, "bold"), foreground="#00ff41",
                  background="#0a0a0a").pack(side="left", padx=5)

        self.status_var = tk.StringVar(value="[+] Pronto")
        ttk.Label(top_frame, textvariable=self.status_var,
                  font=("Consolas", 8), foreground="#00cc33",
                  background="#0a0a0a").pack(side="right", padx=5)

        # --- Frame CPU Total ---
        cpu_frame = tk.Frame(root, bg="#0a0a0a")
        cpu_frame.pack(fill="x", padx=5, pady=(0, 2))

        self.cpu_total_var = tk.StringVar(value="[CPU TOTAL: --.-%]")
        ttk.Label(cpu_frame, textvariable=self.cpu_total_var,
                  font=("Consolas", 10, "bold"), foreground="#00ff41",
                  background="#0a0a0a").pack(side="left", padx=5)

        self.cpu_cores_var = tk.StringVar(value="")
        ttk.Label(cpu_frame, textvariable=self.cpu_cores_var,
                  font=("Consolas", 8), foreground="#00cc33",
                  background="#0a0a0a").pack(side="left", padx=10)

        # --- Frame Filtro ---
        filter_frame = ttk.Frame(root, padding=5)
        filter_frame.pack(fill="x")

        ttk.Label(filter_frame, text="Pesquisar", font=("Consolas", 9, "bold"),
                  foreground="#00ff41", background="#0a0a0a").pack(side="left", padx=2)
        self.filter_entry = ttk.Entry(filter_frame, width=40)
        self.filter_entry.pack(side="left", padx=2)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.aplicar_filtro())

        # --- BOTÕES ---
        btn_help = tk.Button(filter_frame, text="📖 AJUDA",
                             command=self.mostrar_ajuda,
                             bg="#003333", fg="#00cccc", font=("Consolas", 9, "bold"),
                             relief="ridge", bd=2, padx=10, pady=2,
                             activebackground="#005555", activeforeground="#66ffff",
                             cursor="hand2")
        btn_help.pack(side="right", padx=2)

        btn_vt = tk.Button(filter_frame, text="🔍 VIRUSTOTAL",
                           command=self.abrir_virustotal,
                           bg="#1a0033", fg="#bb77ff", font=("Consolas", 9, "bold"),
                           relief="ridge", bd=2, padx=10, pady=2,
                           activebackground="#330066", activeforeground="#dd99ff",
                           cursor="hand2")
        btn_vt.pack(side="right", padx=2)

        btn_refresh = tk.Button(filter_frame, text="⟳ ATUALIZAR",
                                command=self.atualizar_processos,
                                bg="#003300", fg="#00ff41", font=("Consolas", 9, "bold"),
                                relief="ridge", bd=2, padx=10, pady=2,
                                activebackground="#005500", activeforeground="#66ff66",
                                cursor="hand2")
        btn_refresh.pack(side="right", padx=2)

        btn_abrir = tk.Button(filter_frame, text="📂 LOCALIZAÇÃO",
                              command=self.abrir_localizacao,
                              bg="#002244", fg="#00ccff", font=("Consolas", 9, "bold"),
                              relief="ridge", bd=2, padx=10, pady=2,
                              activebackground="#003366", activeforeground="#66ddff",
                              cursor="hand2")
        btn_abrir.pack(side="right", padx=2)

        btn_export = tk.Button(filter_frame, text="💾 EXPORTAR TXT",
                               command=self.exportar_txt,
                               bg="#442200", fg="#ffaa00", font=("Consolas", 9, "bold"),
                               relief="ridge", bd=2, padx=10, pady=2,
                               activebackground="#663300", activeforeground="#ffcc44",
                               cursor="hand2")
        btn_export.pack(side="right", padx=2)

        btn_sair = tk.Button(filter_frame, text="✕ SAIR",
                             command=self.root.quit,
                             bg="#330000", fg="#ff4444", font=("Consolas", 9, "bold"),
                             relief="ridge", bd=2, padx=10, pady=2,
                             activebackground="#550000", activeforeground="#ff6666",
                             cursor="hand2")
        btn_sair.pack(side="right", padx=2)

        # --- Frame Principal com TreeView ---
        main_frame = ttk.Frame(root, padding=5)
        main_frame.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(main_frame, orient="vertical")
        hsb = ttk.Scrollbar(main_frame, orient="horizontal")

        colunas = ("PID", "Nome", "Caminho do Executável", "SHA-256",
                   "CPU %", "Memória (MB)", "Status", "Usuário", "Criado em")

        self.tree = ttk.Treeview(
            main_frame, columns=colunas, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
            selectmode="extended", height=20
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, larg in [
            ("PID", 70),
            ("Nome", 220),
            ("Caminho do Executável", 820),
            ("SHA-256", 500),
            ("CPU %", 65),
            ("Memória (MB)", 100),
            ("Status", 85),
            ("Usuário", 280),
            ("Criado em", 145)
        ]:
            self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_por(c))
            self.tree.column(col, width=larg, minwidth=60, anchor="w")

        self.tree.tag_configure("caminho_path", foreground="#00ccff")
        self.tree.tag_configure("cpu_alta", foreground="#ff4444")
        self.tree.tag_configure("mem_alta", foreground="#ffaa00")
        self.tree.tag_configure("system", foreground="#666666")
        self.tree.tag_configure("user_proc", foreground="#00ff41")

        vsb.pack(side="right", fill="y")
        self.tree.pack(side="top", fill="both", expand=True)
        hsb.pack(side="bottom", fill="x")

        # --- Barra de Status Inferior ---
        status_bar = ttk.Frame(root, padding=2)
        status_bar.pack(fill="x", side="bottom")
        self.count_label = ttk.Label(status_bar,
                                     text="[>] processos: 0 | filtrados: 0",
                                     style="Count.TLabel")
        self.count_label.pack(side="left", padx=5)
        ttk.Label(status_bar,
                  text="[ clique duplo = abrir localização ]",
                  style="StatusBar.TLabel").pack(side="right", padx=5)

        # --- Eventos e Atalhos ---
        self.tree.bind("<Double-1>", lambda e: self.abrir_localizacao())
        self.tree.bind("<Return>", lambda e: self.abrir_localizacao())
        self.root.bind("<F5>", lambda e: self.atualizar_processos())
        self.root.bind("<Control-f>", lambda e: self.filter_entry.focus())
        self.root.bind("<Control-e>", lambda e: self.exportar_txt())

        self._hash_cache = {}

        sep_frame = tk.Frame(root, height=2, bg="#003300")
        sep_frame.pack(fill="x")

        self.all_processes = []
        self.atualizar_processos()

    # =================================================================
    # JANELA DE AJUDA / COMO FUNCIONA
    # =================================================================
    def mostrar_ajuda(self):
        """Abre uma janela modal explicando o funcionamento do script."""

        help_win = tk.Toplevel(self.root)
        help_win.title("📖 MONITOR - PID & PATH — COMO FUNCIONA")
        help_win.configure(bg="#0a0a0a")
        help_win.geometry("750x620")
        self.root.state("zoomed")
        help_win.resizable(False, False)
        help_win.transient(self.root)
        help_win.grab_set()

        # Centraliza em relação à janela pai
        self.root.update_idletasks()
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        hw, hh = 750, 620
        help_win.geometry(f"{hw}x{hh}+{px + (pw - hw)//2}+{py + (ph - hh)//2}")

        # Frame com scroll para o conteúdo
        canvas = tk.Canvas(help_win, bg="#0a0a0a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(help_win, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, padding=10)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        help_win.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), help_win.destroy()))

        # --- TÍTULO ---
        titulo = tk.Label(scroll_frame, text="⏣ MONITOR - PID & PATH — COMO FUNCIONA ⏣",
                          font=("Consolas", 16, "bold"), fg="#00ff41", bg="#0a0a0a")
        titulo.pack(pady=(0, 5))

        subtitulo = tk.Label(scroll_frame, text="Monitor de Processos — PID, SHA-256 & VirusTotal",
                             font=("Consolas", 9), fg="#00cc33", bg="#0a0a0a")
        subtitulo.pack(pady=(0, 15))

        # --- LINHA SEPARADORA ---
        tk.Frame(scroll_frame, height=1, bg="#003300").pack(fill="x", pady=5)

        # --- 1. FUNCIONALIDADES ---
        sec1 = tk.Label(scroll_frame, text="⚙️  FUNCIONALIDADES",
                        font=("Consolas", 12, "bold"), fg="#00ff41", bg="#0a0a0a")
        sec1.pack(anchor="w", pady=(10, 5))

        funcs = [
            ("📋  Listagem completa", "PID, Nome, Caminho, SHA-256, CPU%,\n    Memória, Status, Usuário e Data de criação"),
            ("🔍  Filtro ao vivo", "Campo 'Pesquisar' filtra por PID, Nome,\n    Caminho, SHA-256 ou Usuário em tempo real"),
            ("🔗  VirusTotal", "Calcula o hash SHA-256 do executável\n    e abre a análise no VirusTotal com 1 clique"),
            ("📂  Localização", "Abre o Explorador do Windows com\n    o arquivo do processo selecionado"),
            ("💾  Exportar TXT", "Salva a lista completa de processos\n    visíveis em um arquivo .txt formatado"),
            ("🎨  Tema Hacker", "Interface verde neon com código de cores\n    por tipo de processo e consumo"),
            ("🔄  Ordenação", "Clique no cabeçalho de qualquer coluna\n    para ordenar crescente/decrescente"),
            ("⚡  CPU Real", "Usa duas passagens para calcular\n    o percentual real de CPU por processo"),
        ]

        for tit, desc in funcs:
            frame = tk.Frame(scroll_frame, bg="#0a0a0a")
            frame.pack(fill="x", pady=2)
            tk.Label(frame, text=tit, font=("Consolas", 9, "bold"),
                     fg="#00ccff", bg="#0a0a0a", anchor="w", width=22).pack(side="left")
            tk.Label(frame, text=desc, font=("Consolas", 8),
                     fg="#cccccc", bg="#0a0a0a", anchor="w", justify="left").pack(side="left")

        # --- 2. CORES ---
        tk.Frame(scroll_frame, height=1, bg="#003300").pack(fill="x", pady=10)

        sec2 = tk.Label(scroll_frame, text="🎨  SISTEMA DE CORES",
                        font=("Consolas", 12, "bold"), fg="#00ff41", bg="#0a0a0a")
        sec2.pack(anchor="w", pady=(0, 5))

        cores = [
            ("🟢  Verde", "#00ff41", "Processo normal do usuário"),
            ("🔵  Azul claro", "#00ccff", "Caminho do executável disponível"),
            ("🔴  Vermelho", "#ff4444", "CPU acima de 50%"),
            ("🟠  Laranja", "#ffaa00", "Memória acima de 500 MB"),
            ("⚫  Cinza", "#666666", "Processo do sistema"),
        ]

        for nome, cor_hex, desc in cores:
            frame = tk.Frame(scroll_frame, bg="#0a0a0a")
            frame.pack(fill="x", pady=1)
            lbl_nome = tk.Label(frame, text=nome, font=("Consolas", 9, "bold"),
                                fg=cor_hex, bg="#0a0a0a", width=16, anchor="w")
            lbl_nome.pack(side="left")
            tk.Label(frame, text=desc, font=("Consolas", 8),
                     fg="#aaaaaa", bg="#0a0a0a", anchor="w").pack(side="left")

        # --- 3. ATALHOS ---
        tk.Frame(scroll_frame, height=1, bg="#003300").pack(fill="x", pady=10)

        sec3 = tk.Label(scroll_frame, text="⌨️  TECLAS DE ATALHO",
                        font=("Consolas", 12, "bold"), fg="#00ff41", bg="#0a0a0a")
        sec3.pack(anchor="w", pady=(0, 5))

        atalhos = [
            ("F5", "⟳  Atualizar lista de processos"),
            ("Ctrl + F", "🔍  Focar no campo de filtro 'Pesquisar'"),
            ("Ctrl + E", "💾  Exportar para TXT"),
            ("Enter", "📂  Abrir localização do processo selecionado"),
            ("Duplo clique", "📂  Abrir localização do processo"),
        ]

        for tecla, desc in atalhos:
            frame = tk.Frame(scroll_frame, bg="#0a0a0a")
            frame.pack(fill="x", pady=1)
            tk.Label(frame, text=f"  {tecla:<15}", font=("Consolas", 9, "bold"),
                     fg="#ffaa00", bg="#0a0a0a", anchor="w", width=18).pack(side="left")
            tk.Label(frame, text=desc, font=("Consolas", 8),
                     fg="#cccccc", bg="#0a0a0a", anchor="w").pack(side="left")

        # --- 4. EXPLICAÇÃO TÉCNICA ---
        tk.Frame(scroll_frame, height=1, bg="#003300").pack(fill="x", pady=10)

        sec4 = tk.Label(scroll_frame, text="🧠  COMO FUNCIONA",
                        font=("Consolas", 12, "bold"), fg="#00ff41", bg="#0a0a0a")
        sec4.pack(anchor="w", pady=(0, 5))

        explicacoes = [
            ("Coleta de Processos",
             "Usa a biblioteca psutil para iterar sobre todos\n"
             "os processos ativos do sistema. Cada processo\n"
             "tem seus atributos lidos individualmente."),
            ("CPU % — Duas Passagens",
             "O psutil.cpu_percent() retorna 0.0 na primeira\n"
             "chamada pois precisa de um delta. O script faz:\n"
             "  1ª passada: inicializa o contador de CPU\n"
             "  Sleep 500ms: aguarda o delta\n"
             "  2ª passada: valores reais de CPU%"),
            ("CPU Total (topo)",
             "psutil.cpu_percent(interval=0.3) calcula o uso\n"
             "total da CPU, igual ao Gerenciador de Tarefas."),
            ("SHA-256",
             "Calculado localmente lendo o arquivo em blocos\n"
             "de 64KB. Resultados são cacheados para não\n"
             "recalcular o mesmo arquivo várias vezes.\n"
             "Usado para consulta no VirusTotal."),
            ("Filtro em tempo real",
             "A cada tecla pressionada no campo 'Pesquisar',\n"
             "a tree é refeita mostrando apenas processos\n"
             "que contêm o termo digitado em qualquer campo."),
            ("Ordenação",
             "Ao clicar no cabeçalho, os itens visíveis são\n"
             "reordenados por aquela coluna. Números (PID,\n"
             "CPU, Memória) são ordenados numericamente."),
        ]

        for tit, desc in explicacoes:
            frame = tk.Frame(scroll_frame, bg="#0a0a0a")
            frame.pack(fill="x", pady=4)
            tk.Label(frame, text=f"  ► {tit}", font=("Consolas", 9, "bold"),
                     fg="#00ccff", bg="#0a0a0a", anchor="w").pack(anchor="w")
            tk.Label(frame, text=f"{desc}", font=("Consolas", 8),
                     fg="#bbbbbb", bg="#0a0a0a", anchor="w", justify="left").pack(anchor="w", padx=(20, 0))

        # --- RODAPÉ ---
        tk.Frame(scroll_frame, height=1, bg="#003300").pack(fill="x", pady=10)
        rodape = tk.Label(scroll_frame,
                          text="Feito com ☕ e 💚  •  Python + psutil + Tkinter",
                          font=("Consolas", 8), fg="#006600", bg="#0a0a0a")
        rodape.pack(pady=(0, 5))

        # Botão fechar
        btn_fechar = tk.Button(scroll_frame, text="[ FECHAR ]",
                               command=lambda: (canvas.unbind_all("<MouseWheel>"), help_win.destroy()),
                               bg="#003300", fg="#00ff41", font=("Consolas", 9, "bold"),
                               relief="ridge", bd=2, padx=20, pady=3,
                               activebackground="#005500", activeforeground="#66ff66",
                               cursor="hand2")
        btn_fechar.pack(pady=(5, 0))

    # -----------------------------------------------------------------
    # CÁLCULO DO SHA-256 (COM CACHE)
    # -----------------------------------------------------------------
    def _calcular_sha256(self, caminho):
        if not caminho or caminho == "N/A":
            return "N/A"
        if not os.path.isfile(caminho):
            return "N/A"
        if caminho in self._hash_cache:
            return self._hash_cache[caminho]
        try:
            sha256 = hashlib.sha256()
            with open(caminho, "rb") as f:
                while True:
                    bloco = f.read(65536)
                    if not bloco:
                        break
                    sha256.update(bloco)
            hash_hex = sha256.hexdigest()
            self._hash_cache[caminho] = hash_hex
            return hash_hex
        except Exception:
            self._hash_cache[caminho] = "N/A"
            return "N/A"

    # -----------------------------------------------------------------
    # COLETA (com duas passagens para CPU real)
    # -----------------------------------------------------------------
    def coletar_processos(self):
        processos = []
        self._hash_cache.clear()

        # 1ª PASSADA: inicializa o contador de CPU
        try:
            procs = list(psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent',
                                            'memory_info', 'status', 'username',
                                            'create_time']))
            for proc in procs:
                _ = proc.info['cpu_percent']
        except Exception:
            pass

        time.sleep(0.5)

        # 2ª PASSADA: valores reais de CPU
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent',
                                            'memory_info', 'status', 'username',
                                            'create_time']):
                try:
                    pinfo = proc.info
                    pid = pinfo['pid']
                    nome = pinfo['name'] or "?"
                    caminho = pinfo['exe'] or "N/A"
                    cpu = pinfo['cpu_percent'] or 0.0
                    mem_info = pinfo['memory_info']
                    mem_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0
                    status = pinfo['status'] or "?"
                    usuario = pinfo['username'] or "?"
                    create_ts = pinfo['create_time']
                    # ═══════ DATA BRASIL ═══════
                    criado = datetime.fromtimestamp(create_ts).strftime("%d/%m/%Y %H:%M:%S") if create_ts else "N/A"
                    sha256 = self._calcular_sha256(caminho)
                    processos.append((pid, nome, caminho, sha256, cpu, mem_mb, status, usuario, criado))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao coletar processos:\n{e}")
        return processos

    # -----------------------------------------------------------------
    # ATUALIZAR (agora com CPU total)
    # -----------------------------------------------------------------
    def atualizar_processos(self):
        def task():
            self.status_var.set("[-] Coletando processos...")
            self.root.update_idletasks()

            # CPU TOTAL (como no Task Manager)
            uso_global = psutil.cpu_percent(interval=0.3)
            cores = psutil.cpu_count(logical=True)
            self.root.after(0, lambda: self.cpu_total_var.set(
                f"[CPU TOTAL: {uso_global:.1f}%]"))
            self.root.after(0, lambda: self.cpu_cores_var.set(
                f"[{cores} núcleos lógicos]"))

            self.all_processes = self.coletar_processos()
            self.root.after(0, self._preencher_tree)

        threading.Thread(target=task, daemon=True).start()

    # -----------------------------------------------------------------
    # PREENCHER TREE
    # -----------------------------------------------------------------
    def _preencher_tree(self, filtro_texto=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if filtro_texto is None:
            filtro_texto = self.filter_entry.get().strip().lower()

        filtrados = []
        if filtro_texto:
            for proc in self.all_processes:
                pid_str = str(proc[0])
                nome = (proc[1] or "").lower()
                caminho = (proc[2] or "").lower()
                sha256 = (proc[3] or "").lower()
                usuario = (proc[7] or "").lower()
                criado = (proc[8] or "").lower()
                if (filtro_texto in pid_str or filtro_texto in nome
                        or filtro_texto in caminho or filtro_texto in sha256
                        or filtro_texto in usuario or filtro_texto in criado):
                    filtrados.append(proc)
        else:
            filtrados = self.all_processes        

        filtrados.sort(key=lambda x: x[5], reverse=False)   # menor → maior

        for proc in filtrados:
            pid, nome, caminho, sha256, cpu, mem_mb, status, usuario, criado = proc
            cpu_str = f"{cpu:.1f}"
            mem_str = f"{mem_mb:.2f} MB"

            tags = []
            if caminho != "N/A" and len(caminho) > 2 and caminho[1] == ':':
                tags.append("caminho_path")
            if cpu > 50.0:
                tags.append("cpu_alta")
            if mem_mb > 500:
                tags.append("mem_alta")
            if usuario and ("system" in usuario.lower() or "local service" in usuario.lower()
                            or "network service" in usuario.lower()):
                tags.append("system")
            if not tags:
                tags.append("user_proc")

            self.tree.insert("", "end", values=(
                pid, nome, caminho, sha256, cpu_str, mem_str, status, usuario, criado
            ), tags=tuple(tags))

        total = len(self.all_processes)
        mostrados = len(filtrados)
        self.count_label.config(text=f"[>] processos: {total} | filtrados: {mostrados}")
        self.status_var.set(f"[+] {mostrados} exibidos (de {total})")

    # -----------------------------------------------------------------
    # FILTRO
    # -----------------------------------------------------------------
    def aplicar_filtro(self):
        self._preencher_tree()

    # -----------------------------------------------------------------
    # ORDENAR
    # -----------------------------------------------------------------
    def ordenar_por(self, coluna):
        idx_map = {
            "PID": 0, "Nome": 1, "Caminho do Executável": 2,
            "SHA-256": 3, "CPU %": 4, "Memória (MB)": 5,
            "Status": 6, "Usuário": 7, "Criado em": 8
        }
        idx = idx_map.get(coluna, 0)

        items = [(self.tree.set(item, coluna), item) for item in self.tree.get_children("")]

        if coluna in ("PID", "CPU %", "Memória (MB)"):
            try:
                items.sort(key=lambda x: float(x[0].split()[0].replace(",", ".")))
                
            except ValueError:
                items.sort(key=lambda x: x[0].lower())
        else:
            items.sort(key=lambda x: x[0].lower())

        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    # -----------------------------------------------------------------
    # ABRIR LOCALIZAÇÃO
    # -----------------------------------------------------------------
    def abrir_localizacao(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showinfo("[!]", "Selecione um processo primeiro.")
            return

        caminho = self.tree.item(selecionado[0], "values")[2]
        if not caminho or caminho == "N/A":
            messagebox.showwarning("[!]", "Caminho do executável não disponível.")
            return

        if not os.path.isfile(caminho):
            messagebox.showwarning("[!]", f"Arquivo não encontrado:\n{caminho}")
            return

        try:
            subprocess.run(f'explorer /select,"{caminho}"', shell=True)
            self.status_var.set(f"[+] {os.path.basename(caminho)} selecionado no explorador")
        except Exception as e:
            diretorio = os.path.dirname(caminho)
            if os.path.exists(diretorio):
                try:
                    os.startfile(diretorio)
                    self.status_var.set(f"[+] Diretório aberto (fallback): {diretorio}")
                except Exception as e2:
                    messagebox.showerror("ERRO", f"Não foi possível abrir:\n{e2}")
            else:
                messagebox.showerror("ERRO", f"Diretório não encontrado:\n{diretorio}")

    # -----------------------------------------------------------------
    # ABRIR VIRUSTOTAL
    # -----------------------------------------------------------------
    def abrir_virustotal(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showinfo("[!]", "Selecione um processo primeiro.")
            return

        sha256 = self.tree.item(selecionado[0], "values")[3]
        if not sha256 or sha256 == "N/A":
            messagebox.showwarning("[!]", "SHA-256 não disponível para este processo.")
            return

        try:
            url = f"https://www.virustotal.com/gui/file/{sha256}"
            webbrowser.open(url)
            self.status_var.set(f"[+] SHA-256: {sha256[:16]}... | VirusTotal aberto")
        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao abrir VirusTotal:\n{e}")

    # -----------------------------------------------------------------
    # EXPORTAR TXT (VERSÃO CORRIGIDA — ALINHAMENTO PERFEITO)
    # -----------------------------------------------------------------
    def exportar_txt(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Exportar processos para TXT"
        )
        if not arquivo:
            return

        # Larguras fixas de cada coluna (incluindo 2 espaços de separação entre elas)
        L = {
            "PID":     7,
            "sep1":    2,
            "NOME":   35,
            "sep2":    2,
            "CAMINHO": 118,
            "sep3":    2,
            "SHA256":  64,
            "sep4":    2,
            "CPU":     6,
            "sep5":    2,
            "MEM":     12,
            "sep6":    2,
            "STATUS":  9,
            "sep7":    2,
            "USUARIO": 40,
            "sep8":    2,
            "CRIADO": 19,
        }
        total_width = sum(L.values())

        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                # Linha superior
                f.write("=" * total_width + "\n")
                f.write(f"  ⏣ MONITOR - PID & PATH — PROCESS LISTA ⏣\n\n")
                # ═══════ DATA BRASIL no cabeçalho ═══════
                f.write(f"  Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(f"  Total de processos exibidos: {len(self.tree.get_children(''))}\n\n")
                f.write("=" * total_width + "\n\n")

                # Cabeçalho
                cab = (
                    f"{'PID':>{L['PID']}}"
                    f"{'':{L['sep1']}}"
                    f"{'NOME':<{L['NOME']}}"
                    f"{'':{L['sep2']}}"
                    f"{'CAMINHO DO EXECUTÁVEL':<{L['CAMINHO']}}"
                    f"{'':{L['sep3']}}"
                    f"{'SHA-256':<{L['SHA256']}}"
                    f"{'':{L['sep4']}}"
                    f"{'CPU%':>{L['CPU']}}"
                    f"{'':{L['sep5']}}"
                    f"{'MEM(MB)':>{L['MEM']}}"
                    f"{'':{L['sep6']}}"
                    f"{'STATUS':<{L['STATUS']}}"
                    f"{'':{L['sep7']}}"
                    f"{'USUÁRIO':<{L['USUARIO']}}"
                    f"{'':{L['sep8']}}"
                    f"{'CRIADO EM':<{L['CRIADO']}}"
                )
                f.write(cab + "\n")
                f.write("-" * total_width + "\n")

                for item in self.tree.get_children(""):
                    vals = self.tree.item(item, "values")
                    pid     = vals[0]
                    nome    = vals[1][:L['NOME']]
                    caminho = vals[2][:L['CAMINHO']]
                    sha256  = vals[3][:L['SHA256']]
                    cpu     = vals[4]
                    mem     = vals[5]
                    status  = vals[6][:L['STATUS']]
                    usuario = vals[7][:L['USUARIO']]
                    criado  = vals[8][:L['CRIADO']]

                    linha = (
                        f"{pid:>{L['PID']}}"
                        f"{'':{L['sep1']}}"
                        f"{nome:<{L['NOME']}}"
                        f"{'':{L['sep2']}}"
                        f"{caminho:<{L['CAMINHO']}}"
                        f"{'':{L['sep3']}}"
                        f"{sha256:<{L['SHA256']}}"
                        f"{'':{L['sep4']}}"
                        f"{cpu:>{L['CPU']}}"
                        f"{'':{L['sep5']}}"
                        f"{mem:>{L['MEM']}}"
                        f"{'':{L['sep6']}}"
                        f"{status:<{L['STATUS']}}"
                        f"{'':{L['sep7']}}"
                        f"{usuario:<{L['USUARIO']}}"
                        f"{'':{L['sep8']}}"
                        f"{criado:<{L['CRIADO']}}"
                    )
                    f.write(linha + "\n")

                f.write("\n" + "=" * total_width + "\n")
                f.write("  FIM DO RELATÓRIO\n")
                f.write("=" * total_width + "\n")

            self.status_var.set(f"[+] Exportado: {arquivo}")
            messagebox.showinfo("EXPORTAR",
                                f"Processos exportados com sucesso!\n\n{arquivo}")

        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao exportar:\n\n{e}")


def main():
    root = tk.Tk()
    app = ProcessMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
