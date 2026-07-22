import dns.zone
import dns.query
import dns.resolver
import dns.rdatatype
import dns.exception
import sys
import os
import socket
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
except ImportError:
    sys.exit(1)

# Cores do tema escuro (estilo Kali Linux)
CORES = {
    'bg': '#1a1a2e',
    'fg': '#00ff41',
    'fg2': '#ffffff',
    'entry_bg': '#16213e',
    'entry_fg': '#00ff41',
    'btn_bg': '#0f3460',
    'btn_fg': '#00ff41',
    'btn_active': '#1a5276',
    'text_bg': '#0d0d1a',
    'text_fg': '#00ff41',
    'title_bg': '#16213e',
    'title_fg': '#00ff41',
    'progress': '#00ff41',
    'error': '#ff4444',
    'success': '#00ff41',
    'warning': '#ffaa00',
    'info': "#44e3ff"
}


class DNSReconGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TRANSFERENCIA DE ZONA")
        self.root.geometry("1100x750")
        self.root.state("zoomed")
        self.root.configure(bg=CORES['bg'])

        try:
            self.root.iconbitmap(default='')
        except:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Variáveis de controle
        self.running = False
        self.queue = queue.Queue()
        self.progresso_atual = 0
        self.resultados = {
            'axfr': [],
            'subdominios': [],
            'registros': []
        }
        self.log_lines = []

        # --- TAMANHOS DE FONTE INDEPENDENTES (LOG / RESULTADOS) ---
        self.log_font_size = 9         # <<< NOVO
        self.result_font_size = 9      # <<< NOVO

        # Configurar grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Construir interface
        self.criar_topo()
        self.criar_abas()
        self.criar_rodape()

        # Iniciar processamento da fila
        self.processar_fila()

    def criar_topo(self):
        """Cria o cabeçalho com banner e controles."""
        # Frame do banner
        banner_frame = tk.Frame(self.root, bg=CORES['bg'])
        banner_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))

        banner_texto = """
╔══════════════════════════════════════════════╗
║         DNSReconPro - Pentest DNS            ║
║    Transferência de Zona + Enumeração        ║
║          Uso Autorizado Apenas               ║
╚══════════════════════════════════════════════╝"""

        lbl_banner = tk.Label(banner_frame, text=banner_texto,
                              font=('Courier', 9, 'bold'),
                              fg=CORES['fg'], bg=CORES['bg'],
                              justify=tk.LEFT)
        lbl_banner.pack(anchor='w')

        # Frame de entrada de dados
        entry_frame = tk.Frame(self.root, bg=CORES['bg'])
        entry_frame.grid(row=1, column=0, sticky='new', padx=10, pady=5)

        # Linha 1: Apenas Domínio
        linha1 = tk.Frame(entry_frame, bg=CORES['bg'])
        linha1.pack(fill='x', pady=2)

        tk.Label(linha1, text="Domínio:", fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 10)).pack(side='left', padx=(0, 5))
        self.entry_dominio = tk.Entry(linha1, width=30,
                                      bg=CORES['entry_bg'], fg=CORES['entry_fg'],
                                      insertbackground=CORES['fg'],
                                      font=('Courier', 10), relief='flat', bd=2)
        self.entry_dominio.pack(side='left', padx=(0, 15))
        self.entry_dominio.insert(0, "businesscorp.com.br")

        # Linha 2: Wordlist + Threads
        linha2 = tk.Frame(entry_frame, bg=CORES['bg'])
        linha2.pack(fill='x', pady=2)

        tk.Label(linha2, text="Wordlist:", fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 10)).pack(side='left', padx=(0, 5))
        self.entry_wordlist = tk.Entry(linha2, width=30,
                                       bg=CORES['entry_bg'], fg=CORES['entry_fg'],
                                       insertbackground=CORES['fg'],
                                       font=('Courier', 10), relief='flat', bd=2)
        self.entry_wordlist.pack(side='left', padx=(0, 5))

        # Wordlist padrão do Kali
        wordlist_padrao = '/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt'
        if os.path.exists(wordlist_padrao):
            self.entry_wordlist.insert(0, wordlist_padrao)
        elif os.path.exists('/usr/share/wordlists/dns/subdomains-top1million-5000.txt'):
            self.entry_wordlist.insert(0, '/usr/share/wordlists/dns/subdomains-top1million-5000.txt')

        btn_browse = tk.Button(linha2, text="Browse",
                               bg=CORES['btn_bg'], fg=CORES['btn_fg'],
                               activebackground=CORES['btn_active'],
                               font=('Courier', 9, 'bold'),
                               relief='flat', bd=2,
                               command=self.browse_wordlist)
        btn_browse.pack(side='left', padx=(0, 15))

        tk.Label(linha2, text="Threads:", fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 10)).pack(side='left', padx=(0, 5))
        self.entry_threads = tk.Spinbox(linha2, from_=1, to=100, width=5,
                                        bg=CORES['entry_bg'], fg=CORES['entry_fg'],
                                        buttonbackground=CORES['btn_bg'],
                                        font=('Courier', 10), relief='flat', bd=2)
        self.entry_threads.pack(side='left', padx=(0, 15))
        self.entry_threads.delete(0, tk.END)
        self.entry_threads.insert(0, "4")

        # Linha 3: Botões
        linha3 = tk.Frame(entry_frame, bg=CORES['bg'])
        linha3.pack(fill='x', pady=8)

        self.btn_iniciar = tk.Button(linha3, text="▶ INICIAR RECON",
                                     bg='#006400', fg='#ffffff',
                                     activebackground='#008000',
                                     font=('Courier', 11, 'bold'),
                                     relief='flat', bd=3, padx=15, pady=5,
                                     command=self.iniciar_recon)
        self.btn_iniciar.pack(side='left', padx=(0, 10))

        self.btn_parar = tk.Button(linha3, text="■ PARAR",
                                   bg='#8b0000', fg='#ffffff',
                                   activebackground='#cc0000',
                                   font=('Courier', 11, 'bold'),
                                   relief='flat', bd=3, padx=15, pady=5,
                                   command=self.parar_recon, state='disabled')
        self.btn_parar.pack(side='left', padx=(0, 10))

        self.btn_limpar = tk.Button(linha3, text="✕ LIMPAR LOG",
                                    bg=CORES['btn_bg'], fg=CORES['btn_fg'],
                                    activebackground=CORES['btn_active'],
                                    font=('Courier', 11, 'bold'),
                                    relief='flat', bd=3, padx=15, pady=5,
                                    command=self.limpar_log)
        self.btn_limpar.pack(side='left', padx=(0, 10))

        self.btn_salvar = tk.Button(linha3, text="💾 SALVAR LOG",
                                    bg=CORES['btn_bg'], fg=CORES['btn_fg'],
                                    activebackground=CORES['btn_active'],
                                    font=('Courier', 11, 'bold'),
                                    relief='flat', bd=3, padx=15, pady=5,
                                    command=self.salvar_log)
        self.btn_salvar.pack(side='left', padx=(0, 10))

        # Botão: SALVAR RESULTADOS (apenas .txt)
        self.btn_salvar_resultados = tk.Button(linha3, text="📊 SALVAR RESULTADOS",
                                               bg='#004d40', fg='#ffffff',
                                               activebackground='#00695c',
                                               font=('Courier', 10, 'bold'),
                                               relief='flat', bd=3, padx=12, pady=5,
                                               command=self.salvar_resultados_txt)
        self.btn_salvar_resultados.pack(side='left')

        # Barra de progresso
        self.progress = ttk.Progressbar(entry_frame, mode='determinate',
                                        length=1050, maximum=100, value=0,
                                        style='green.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(5, 0))

    def criar_abas(self):
        """Cria o notebook com abas de log e resultados."""
        abas_frame = tk.Frame(self.root, bg=CORES['bg'])
        abas_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0, 5))
        self.root.grid_rowconfigure(2, weight=1)
        abas_frame.grid_rowconfigure(0, weight=1)
        abas_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=CORES['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', background=CORES['btn_bg'],
                        foreground=CORES['fg2'], padding=[10, 5],
                        font=('Courier', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', CORES['entry_bg'])],
                  foreground=[('selected', CORES['fg'])])

        self.notebook = ttk.Notebook(abas_frame)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        # ==================== ABA 1: LOG ====================
        tab_log = tk.Frame(self.notebook, bg=CORES['bg'])
        self.notebook.add(tab_log, text="LOG DE EXECUÇÃO")

        # --- Controles de fonte do LOG (+/-) ---
        font_control_log = tk.Frame(tab_log, bg=CORES['bg'])
        font_control_log.pack(fill='x', padx=5, pady=(5, 2))

        tk.Label(font_control_log, text="Fonte do LOG:",
                 fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 9, 'bold')).pack(side='left', padx=(0, 5))

        self.lbl_log_font = tk.Label(font_control_log, text=f"{self.log_font_size}",
                                     fg=CORES['fg'], bg=CORES['entry_bg'],
                                     font=('Courier', 9, 'bold'), width=3,
                                     relief='flat', bd=2)
        self.lbl_log_font.pack(side='left', padx=(0, 5))

        btn_log_menos = tk.Button(font_control_log, text="−",
                                  bg=CORES['btn_bg'], fg=CORES['fg'],
                                  activebackground=CORES['btn_active'],
                                  font=('Courier', 10, 'bold'),
                                  relief='flat', bd=2, width=3,
                                  command=self.diminuir_fonte_log)
        btn_log_menos.pack(side='left', padx=(0, 5))

        btn_log_mais = tk.Button(font_control_log, text="+",
                                 bg=CORES['btn_bg'], fg=CORES['fg'],
                                 activebackground=CORES['btn_active'],
                                 font=('Courier', 10, 'bold'),
                                 relief='flat', bd=2, width=3,
                                 command=self.aumentar_fonte_log)
        btn_log_mais.pack(side='left', padx=(0, 10))

        # Separador visual
        tk.Frame(font_control_log, bg=CORES['btn_bg'], width=2,
                 height=20).pack(side='left', padx=(0, 10))

        self.lbl_log_info = tk.Label(font_control_log, text="LOG",
                                     fg=CORES['info'], bg=CORES['bg'],
                                     font=('Courier', 8, 'italic'))
        self.lbl_log_info.pack(side='left')

        # Widget de texto do LOG
        self.txt_log = scrolledtext.ScrolledText(
            tab_log, wrap=tk.WORD,
            bg=CORES['text_bg'], fg=CORES['text_fg'],
            insertbackground=CORES['fg'],
            font=('Courier', self.log_font_size),
            relief='flat', bd=2,
            state='disabled'
        )
        self.txt_log.pack(fill='both', expand=True, padx=5, pady=(0, 5))

        self.txt_log.tag_config('info', foreground=CORES['info'])
        self.txt_log.tag_config('success', foreground=CORES['success'])
        self.txt_log.tag_config('error', foreground=CORES['error'])
        self.txt_log.tag_config('warning', foreground=CORES['warning'])
        self.txt_log.tag_config('bold', font=('Courier', self.log_font_size, 'bold'))

        # ==================== ABA 2: RESULTADOS ====================
        tab_resultados = tk.Frame(self.notebook, bg=CORES['bg'])
        self.notebook.add(tab_resultados, text="RESULTADOS")

        # Estilo Treeview (salvo como self.estilo_tree para reconfigurar depois)
        self.estilo_tree = ttk.Style()
        self.estilo_tree.configure('Treeview',
                                   background=CORES['text_bg'],
                                   foreground=CORES['fg'],
                                   fieldbackground=CORES['text_bg'],
                                   font=('Courier', self.result_font_size))
        self.estilo_tree.configure('Treeview.Heading',
                                   background=CORES['btn_bg'],
                                   foreground=CORES['fg2'],
                                   font=('Courier', 10, 'bold'))
        self.estilo_tree.map('Treeview',
                             background=[('selected', CORES['entry_bg'])])

        filtro_frame = tk.Frame(tab_resultados, bg=CORES['bg'])
        filtro_frame.pack(fill='x', padx=5, pady=(5, 0))

        # --- Filtro à esquerda ---
        tk.Label(filtro_frame, text="Filtrar por tipo:",
                 fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 9)).pack(side='left', padx=(0, 5))

        self.filtro_tipo = ttk.Combobox(filtro_frame,
                                        values=['TODOS', 'AXFR', 'SUBDOMÍNIOS', 'REGISTROS DNS'],
                                        state='readonly', width=20,
                                        font=('Courier', 9))
        self.filtro_tipo.pack(side='left', padx=(0, 10))
        self.filtro_tipo.set('TODOS')
        self.filtro_tipo.bind('<<ComboboxSelected>>', self.filtrar_resultados)

        btn_refresh = tk.Button(filtro_frame, text="ATUALIZAR",
                                bg=CORES['btn_bg'], fg=CORES['btn_fg'],
                                font=('Courier', 9),
                                relief='flat', bd=2,
                                command=self.atualizar_resultados)
        btn_refresh.pack(side='left')

        # --- Controles de fonte dos RESULTADOS (+/-) à direita ---
        tk.Frame(filtro_frame, bg=CORES['bg'], width=30).pack(side='left')  # espaçador

        tk.Label(filtro_frame, text="Fonte:",
                 fg=CORES['fg2'], bg=CORES['bg'],
                 font=('Courier', 9, 'bold')).pack(side='left', padx=(0, 5))

        self.lbl_result_font = tk.Label(filtro_frame, text=f"{self.result_font_size}",
                                        fg=CORES['fg'], bg=CORES['entry_bg'],
                                        font=('Courier', 9, 'bold'), width=3,
                                        relief='flat', bd=2)
        self.lbl_result_font.pack(side='left', padx=(0, 5))

        btn_res_menos = tk.Button(filtro_frame, text="−",
                                  bg=CORES['btn_bg'], fg=CORES['fg'],
                                  activebackground=CORES['btn_active'],
                                  font=('Courier', 10, 'bold'),
                                  relief='flat', bd=2, width=3,
                                  command=self.diminuir_fonte_resultados)
        btn_res_menos.pack(side='left', padx=(0, 5))

        btn_res_mais = tk.Button(filtro_frame, text="+",
                                 bg=CORES['btn_bg'], fg=CORES['fg'],
                                 activebackground=CORES['btn_active'],
                                 font=('Courier', 10, 'bold'),
                                 relief='flat', bd=2, width=3,
                                 command=self.aumentar_fonte_resultados)
        btn_res_mais.pack(side='left')

        container_tree = tk.Frame(tab_resultados, bg=CORES['bg'])
        container_tree.pack(fill='both', expand=True, padx=5, pady=5)

        columns = ('#1', '#2', '#3', '#4', '#5')
        self.tree_resultados = ttk.Treeview(container_tree, columns=columns,
                                            show='headings', height=20)

        self.tree_resultados.heading('#1', text='TIPO')
        self.tree_resultados.heading('#2', text='NOME / VALOR')
        self.tree_resultados.heading('#3', text='TTL')
        self.tree_resultados.heading('#4', text='DETALHE 1')
        self.tree_resultados.heading('#5', text='DETALHE 2')

        self.tree_resultados.column('#1', width=100, anchor='w')
        self.tree_resultados.column('#2', width=400, anchor='w')
        self.tree_resultados.column('#3', width=50, anchor='w')
        self.tree_resultados.column('#4', width=300, anchor='w')
        self.tree_resultados.column('#5', width=530, anchor='w')

        scroll_tree = ttk.Scrollbar(container_tree, orient='vertical',
                                    command=self.tree_resultados.yview)
        self.tree_resultados.configure(yscrollcommand=scroll_tree.set)

        self.tree_resultados.pack(side='left', fill='both', expand=True)
        scroll_tree.pack(side='right', fill='y')

    def criar_rodape(self):
        """Cria o rodapé com status."""
        rodape = tk.Frame(self.root, bg=CORES['title_bg'], height=25)
        rodape.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 10))

        self.lbl_status = tk.Label(rodape, text="✅ PRONTO PARA EXECUTAR",
                                   fg=CORES['fg'], bg=CORES['title_bg'],
                                   font=('Courier', 9, 'bold'))
        self.lbl_status.pack(side='left', padx=10)

        self.lbl_contador = tk.Label(rodape, text="Registros: 0  |  Subdomínios: 0  |  AXFR: 0",
                                     fg=CORES['fg2'], bg=CORES['title_bg'],
                                     font=('Courier', 9))
        self.lbl_contador.pack(side='right', padx=10)

    # ================== CONTROLES DE FONTE INDEPENDENTES ==================

    def aumentar_fonte_log(self):
        """Aumenta a fonte do LOG sem afetar os RESULTADOS."""
        self.log_font_size += 1
        self.txt_log.configure(font=('Courier', self.log_font_size))
        # Atualiza também a tag 'bold' que tem fonte explícita
        self.txt_log.tag_config('bold', font=('Courier', self.log_font_size, 'bold'))
        self.lbl_log_font.configure(text=str(self.log_font_size))

    def diminuir_fonte_log(self):
        """Diminui a fonte do LOG sem afetar os RESULTADOS."""
        if self.log_font_size > 6:
            self.log_font_size -= 1
            self.txt_log.configure(font=('Courier', self.log_font_size))
            self.txt_log.tag_config('bold', font=('Courier', self.log_font_size, 'bold'))
            self.lbl_log_font.configure(text=str(self.log_font_size))

    def aumentar_fonte_resultados(self):
        """Aumenta a fonte dos RESULTADOS (Treeview) sem afetar o LOG."""
        self.result_font_size += 1
        self.estilo_tree.configure('Treeview',
                                   font=('Courier', self.result_font_size))
        self.lbl_result_font.configure(text=str(self.result_font_size))

    def diminuir_fonte_resultados(self):
        """Diminui a fonte dos RESULTADOS (Treeview) sem afetar o LOG."""
        if self.result_font_size > 6:
            self.result_font_size -= 1
            self.estilo_tree.configure('Treeview',
                                       font=('Courier', self.result_font_size))
            self.lbl_result_font.configure(text=str(self.result_font_size))

    # ================== MÉTODOS DE FUNCIONALIDADE ==================

    def browse_wordlist(self):
        filename = filedialog.askopenfilename(
            title="Selecionar Wordlist",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            self.entry_wordlist.delete(0, tk.END)
            self.entry_wordlist.insert(0, filename)

    def log(self, mensagem, tipo='info'):
        self.queue.put(('log', mensagem, tipo))

    def adicionar_log(self, mensagem, tipo='info'):
        try:
            self.txt_log.configure(state='normal')
            self.txt_log.insert(tk.END, mensagem + '\n', tipo)
            self.txt_log.see(tk.END)
            self.txt_log.configure(state='disabled')
        except:
            pass

    def atualizar_status(self, texto, cor=CORES['fg']):
        self.queue.put(('status', texto, cor))

    def atualizar_contador(self):
        axfr = sum(len(r.get('registros', [])) for r in self.resultados['axfr'])
        subs = len(self.resultados['subdominios'])
        regs = len(self.resultados['registros'])
        texto = f"Registros: {regs}  |  Subdomínios: {subs}  |  AXFR: {axfr}"
        self.queue.put(('contador', texto))

    def atualizar_progresso(self, valor):
        self.queue.put(('progress', max(0, min(100, valor))))

    def processar_fila(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'log':
                    self.adicionar_log(msg[1], msg[2])
                elif msg[0] == 'status':
                    self.lbl_status.configure(text=msg[1], fg=msg[2])
                elif msg[0] == 'contador':
                    self.lbl_contador.configure(text=msg[1])
                elif msg[0] == 'progress':
                    self.progresso_atual = msg[1]
                    self.progress['value'] = msg[1]
                    self.lbl_status.configure(
                        text=f"▶ PROGRESSO: {msg[1]:3.0f}%",
                        fg=CORES['warning']
                    )
                elif msg[0] == 'tree_update':
                    self.atualizar_treeview()
                elif msg[0] == 'done':
                    self.recon_concluido()
                elif msg[0] == 'result':
                    self.resultados[msg[1]].append(msg[2])
                    self.atualizar_contador()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.processar_fila)

    def iniciar_recon(self):
        dominio = self.entry_dominio.get().strip()
        if not dominio:
            messagebox.showwarning("Aviso", "Informe um domínio válido!")
            return

        if '.' not in dominio:
            messagebox.showwarning("Aviso", "Domínio inválido! Use o formato: exemplo.com.br")
            return

        self.btn_iniciar.configure(state='disabled', text='▶ EXECUTANDO...')
        self.btn_parar.configure(state='normal')
        self.running = True

        self.resultados = {'axfr': [], 'subdominios': [], 'registros': []}

        self.progresso_atual = 0
        self.progress['value'] = 0

        self.log(f"{'='*60}", 'bold')
        self.log(f"INICIANDO RECONHECIMENTO DNS: {dominio}", 'bold')
        self.log(f"{'='*60}", 'bold')

        self.atualizar_status("▶ EXECUTANDO...", CORES['warning'])

        thread = threading.Thread(target=self.executar_recon, daemon=True)
        thread.start()

    def parar_recon(self):
        """Para a execução sem salvar automaticamente."""
        self.running = False
        self.log("\n[!] RECONHECIMENTO INTERROMPIDO PELO USUÁRIO", 'warning')
        self.log("[*] Use os botões 'SALVAR LOG' ou 'SALVAR RESULTADOS' para exportar manualmente.", 'info')

        # Finaliza a interface
        self.btn_parar.configure(state='disabled')
        self.btn_iniciar.configure(state='normal', text='▶ INICIAR RECON')
        self.atualizar_status("■ INTERROMPIDO - Nada foi salvo automaticamente", CORES['warning'])
        self.progress['value'] = 0
        self.queue.put(('tree_update',))

    def limpar_log(self):
        self.txt_log.configure(state='normal')
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.configure(state='disabled')

        self.resultados = {'axfr': [], 'subdominios': [], 'registros': []}

        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)

        self.atualizar_contador()
        self.atualizar_status("✅ LOG LIMPO", CORES['fg'])
        self.progress['value'] = 0

    def salvar_log(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar Log",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.txt_log.get(1.0, tk.END))
                self.log(f"[✔] Log salvo em: {filename}", 'success')
                messagebox.showinfo("Sucesso", f"Log salvo com sucesso!\n\n{filename}")   # <<< POPUP
            except Exception as e:
                self.log(f"[-] Erro ao salvar: {e}", 'error')
                messagebox.showerror("Erro", f"Erro ao salvar log:\n{e}")                 # <<< POPUP de erro

    def salvar_resultados_txt(self):
        """Salva os resultados estruturados em formato .txt (apenas texto)."""
        if (not self.resultados['axfr'] and not self.resultados['subdominios']
                and not self.resultados['registros']):
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar!\nExecute um reconhecimento primeiro.")
            return

        filename = filedialog.asksaveasfilename(
            title="Salvar Resultados Estruturados",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("DNSReconPro - Relatório de Resultados Estruturados\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Domínio: {self.entry_dominio.get().strip()}\n\n")
                f.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("=" * 80 + "\n\n")

                f.write(">>> SECAO 1: AXFR (TRANSFERENCIA DE ZONA) <<<\n\n")
                if self.resultados['axfr']:
                    for axfr in self.resultados['axfr']:
                        ns = axfr.get('nameserver', 'N/A')
                        ip = axfr.get('ip', 'N/A')
                        f.write(f"Nameserver: {ns}  (IP: {ip})\n")
                        f.write("-" * 70 + "\n")
                        f.write(f"{'NOME':40s} {'TTL':8s} {'TIPO':8s} {'REGISTRO'}\n")
                        f.write("-" * 70 + "\n")
                        for reg in axfr.get('registros', []):
                            nome = reg.get('nome', '')
                            ttl = str(reg.get('ttl', ''))
                            tipo = reg.get('tipo', '')
                            rdata = reg.get('rdata', '')
                            f.write(f"{nome:40s} {ttl:8s} {tipo:8s} {rdata}\n")
                        f.write("\n")
                else:
                    f.write("Nenhuma transferencia de zona bem-sucedida.\n\n")

                f.write(">>> SECAO 2: SUBDOMINIOS ENCONTRADOS <<<\n\n")
                if self.resultados['subdominios']:
                    f.write(f"{'SUBDOMINIO':55s} {'IP(s)'}\n")
                    f.write("-" * 80 + "\n")
                    for sub in self.resultados['subdominios']:
                        nome = sub.get('nome', '')
                        ips = ', '.join(sub.get('ips', []))
                        f.write(f"{nome:55s} {ips}\n")
                else:
                    f.write("Nenhum subdominio encontrado.\n")
                f.write("\n")

                f.write(">>> SECAO 3: REGISTROS DNS <<<\n\n")
                if self.resultados['registros']:
                    f.write(f"{'TIPO':10s} {'VALOR'}\n")
                    f.write("-" * 80 + "\n")
                    for reg in self.resultados['registros']:
                        tipo = reg.get('tipo', '')
                        valor = reg.get('valor', '')
                        f.write(f"{tipo:10s} {valor}\n")
                else:
                    f.write("Nenhum registro DNS consultado.\n")
                f.write("\n")

                axfr_count = sum(len(r.get('registros', [])) for r in self.resultados['axfr'])
                subs_count = len(self.resultados['subdominios'])
                regs_count = len(self.resultados['registros'])
                f.write("=" * 80 + "\n")
                f.write(">>> RESUMO <<<\n\n")
                f.write(f"  Servidores AXFR: {len(self.resultados['axfr'])}\n")
                f.write(f"  Registros AXFR:  {axfr_count}\n")
                f.write(f"  Subdominios:     {subs_count}\n")
                f.write(f"  Registros DNS:   {regs_count}\n")
                f.write("=" * 80 + "\n")

            self.log(f"[✔] Resultados salvos em: {filename}", 'success')
            messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso!\n\n{filename}")   # <<< POPUP
        except Exception as e:
            self.log(f"[-] Erro ao salvar resultados: {e}", 'error')
            messagebox.showerror("Erro", f"Erro ao salvar resultados:\n{e}")                 # <<< POPUP de erro

    def on_close(self):
        if self.running:
            if messagebox.askokcancel("Sair", "Reconhecimento em andamento. Deseja realmente sair?"):
                self.parar_recon()
                self.root.destroy()
        else:
            self.root.destroy()

    # ================== LÓGICA DE RECONHECIMENTO ==================

    def resolver_ns(self, dominio):
        ns_list = []
        self.log(f"[*] Descobrindo nameservers de: {dominio}\n", 'info')
        self.atualizar_status("▶ Resolvendo NS...", CORES['info'])

        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '1.1.1.1']
            respostas = resolver.resolve(dominio, 'NS')
            for rr in respostas:
                ns = str(rr.target).rstrip('.')
                if ns not in ns_list:
                    ns_list.append(ns)
                    self.log(f"    [+] NS: {ns}\n", 'success')
        except Exception as e:
            self.log(f"    [-] Erro: {e}\n", 'error')

        return ns_list

    def resolver_ip_ns(self, ns):
        try:
            return socket.gethostbyname(ns)
        except:
            return None

    def transferencia_zona(self, ns, ip, dominio):
        if not self.running:
            return False

        alvo = ip if ip else ns
        self.log(f"\n[*] AXFR em {ns}    IP: {alvo}\n", 'info')

        try:
            zona = dns.zone.from_xfr(dns.query.xfr(alvo, dominio, timeout=15, lifetime=30))

            if zona and len(zona.nodes) > 0:
                self.log(f"\n    [✔] TRANSFERÊNCIA DE ZONA BEM-SUCEDIDA\n", 'success')

                registros_axfr = []
                for nome, node in zona.nodes.items():
                    nome_str = str(nome)
                    if nome_str == '@':
                        nome_completo = dominio
                    elif nome_str.endswith('.'):
                        nome_completo = nome_str
                    else:
                        nome_completo = f"{nome_str}.{dominio}"

                    for rdataset in node:
                        for rdata in rdataset:
                            tipo = dns.rdatatype.to_text(rdataset.rdtype)
                            texto_rdata = str(rdata)
                            registros_axfr.append({
                                'nome': nome_completo,
                                'ttl': rdataset.ttl,
                                'tipo': tipo,
                                'rdata': texto_rdata
                            })
                            self.log(f"      {nome_completo:35s} {rdataset.ttl:6d} {tipo:6s} {texto_rdata}", 'success')

                self.queue.put(('result', 'axfr', {
                    'nameserver': ns,
                    'ip': alvo,
                    'registros': registros_axfr
                }))
                return True
            else:
                self.log(f"    [-] AXFR falhou - zona vazia ou recusada", 'warning')
                return False

        except dns.exception.DNSException as e:
            self.log(f"\n    [-] AXFR recusado: {e}\n", 'warning')
            return False
        except Exception as e:
            self.log(f"\n    [-] Erro: {e}\n", 'error')
            return False

    def consultar_registros(self, dominio):
        self.log(f"\n[*] Consultando registros DNS para: {dominio}\n", 'info')
        self.atualizar_status("▶ Consultando registros...", CORES['info'])

        tipos = ['A', 'AAAA', 'MX', 'TXT', 'SOA', 'NS', 'CNAME', 'SRV', 'CAA']

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        resolver.timeout = 5
        resolver.lifetime = 10

        for idx, tipo in enumerate(tipos):
            if not self.running:
                break
            try:
                rdtype = dns.rdatatype.from_text(tipo)
                respostas = resolver.resolve(dominio, rdtype)

                for rr in respostas:
                    texto = str(rr)
                    self.log(f"    [{tipo:5s}]: {texto}", 'info')
                    self.queue.put(('result', 'registros', {
                        'tipo': tipo,
                        'valor': texto
                    }))
            except dns.resolver.NoAnswer:
                pass
            except dns.resolver.NXDOMAIN:
                pass
            except Exception as e:
                pass

            progresso_reg = 15 + int((idx + 1) / len(tipos) * 20)
            self.atualizar_progresso(progresso_reg)

    def brute_force_subdominios(self, dominio, wordlist_path):
        if not wordlist_path or not os.path.exists(wordlist_path):
            self.log("[!] Wordlist não encontrada. Pulando brute force \n", 'warning')
            return

        self.log(f"\n[*] Iniciando brute force de subdomínios...\n", 'info')
        self.log(f"[*] Wordlist: {wordlist_path}\n", 'info')
        self.atualizar_status("▶ Brute force de subdomínios...", CORES['warning'])

        try:
            with open(wordlist_path, 'r', errors='ignore') as f:
                subdominios = [linha.strip() for linha in f if linha.strip()]
        except Exception as e:
            self.log(f"[-] Erro ao ler wordlist: {e}", 'error')
            return

        if len(subdominios) > 114442:
            self.log(f"[!] Wordlist muito grande ({len(subdominios)}). Limitando a 114442.", 'warning')
            subdominios = subdominios[:114442]

        self.log(f"[*] Testando {len(subdominios)} subdomínios\n", 'info')

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        resolver.timeout = 3
        resolver.lifetime = 5

        threads = int(self.entry_threads.get())
        encontrados = 0
        total = len(subdominios)

        def testar_sub(sub):
            if not self.running:
                return None
            nome = f"{sub}.{dominio}"
            try:
                resp = resolver.resolve(nome, 'A', raise_on_no_answer=False)
                ips = [str(r) for r in resp]
                return (nome, ips)
            except:
                return None

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futuros = {executor.submit(testar_sub, s): s for s in subdominios}

            for i, futuro in enumerate(as_completed(futuros)):
                if not self.running:
                    break

                if i % 500 == 0 and i > 0:
                    self.log(f"\n    [-] Progresso: {i}/{total} (encontrados: {encontrados})\n", 'info')

                resultado = futuro.result()
                if resultado:
                    nome, ips = resultado
                    encontrados += 1
                    self.log(f"    [+] {nome:50s} -> {', '.join(ips)}", 'success')
                    self.queue.put(('result', 'subdominios', {
                        'nome': nome,
                        'ips': ips
                    }))

                if i % 100 == 0:
                    pct_brute = 35 + int((i + 1) / total * 55)
                    self.atualizar_progresso(pct_brute)

        self.log(f"\n[✔] Brute force concluído. {encontrados} subdomínios encontrados.", 'success')

    def executar_recon(self):
        try:
            dominio = self.entry_dominio.get().strip()
            threads = int(self.entry_threads.get())

            self.atualizar_progresso(2)

            # Nameservers descobertos automaticamente via DNS público
            nameservers = self.resolver_ns(dominio)

            self.log(f"\n[*] Nameservers: {', '.join(nameservers) if nameservers else 'Nenhum'}", 'info')
            self.atualizar_progresso(5)

            axfr_sucesso = False
            total_ns = len(nameservers) if nameservers else 1
            for idx, ns in enumerate(nameservers):
                if not self.running:
                    break
                ip = self.resolver_ip_ns(ns)
                if self.transferencia_zona(ns, ip, dominio):
                    axfr_sucesso = True
                pct_axfr = 5 + int((idx + 1) / total_ns * 10)
                self.atualizar_progresso(pct_axfr)

            if not axfr_sucesso and self.running:
                self.log("\n[!] Nenhuma transferência de zona possível.\n", 'warning')
                self.log("[!] Servidor configurado corretamente. Prosseguindo...\n", 'info')

            if self.running:
                self.consultar_registros(dominio)

            if self.running:
                wordlist = self.entry_wordlist.get().strip()
                self.brute_force_subdominios(dominio, wordlist)

            if self.running:
                self.atualizar_progresso(95)
                time.sleep(0.3)
                self.atualizar_progresso(100)

            self.queue.put(('done',))

        except Exception as e:
            self.log(f"[-] Erro na execução: {e}", 'error')
            self.queue.put(('done',))

    def recon_concluido(self):
        self.running = False
        self.btn_iniciar.configure(state='normal', text='▶ INICIAR RECON')
        self.btn_parar.configure(state='disabled')
        self.queue.put(('tree_update',))

        axfr_count = sum(len(r.get('registros', [])) for r in self.resultados['axfr'])
        subs_count = len(self.resultados['subdominios'])
        regs_count = len(self.resultados['registros'])

        self.log(f"\n{'='*60}", 'bold')
        self.log(f"RECONHECIMENTO CONCLUÍDO\n", 'bold')
        self.log(f"  AXFR: {len(self.resultados['axfr'])} servidores   {axfr_count} registros", 'success')
        self.log(f"  Subdomínios: {subs_count}", 'success')
        self.log(f"  Registros DNS: {regs_count}", 'success')
        self.log(f"{'='*60}", 'bold')

        self.atualizar_status(f"✅ CONCLUÍDO - {subs_count} subs, {axfr_count} registros AXFR", CORES['success'])

        self.progress['value'] = 100

        # Salvamento automático REMOVIDO — o usuário salva manualmente pelos botões

    def atualizar_resultados(self):
        self.atualizar_treeview()

    def atualizar_treeview(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        self._popular_treeview('TODOS')

    def filtrar_resultados(self, event=None):
        filtro = self.filtro_tipo.get()
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        self._popular_treeview(filtro)

    def _popular_treeview(self, filtro):
        if filtro in ('TODOS', 'AXFR'):
            for axfr in self.resultados['axfr']:
                for reg in axfr.get('registros', []):
                    self.tree_resultados.insert('', tk.END, values=(
                        'AXFR',
                        reg['nome'],
                        reg['ttl'],
                        reg['tipo'],
                        reg['rdata']
                    ))

        if filtro in ('TODOS', 'SUBDOMÍNIOS'):
            for sub in self.resultados['subdominios']:
                self.tree_resultados.insert('', tk.END, values=(
                    'SUBDOMÍNIO',
                    sub['nome'],
                    '-',
                    ', '.join(sub['ips'][:3]),
                    '...'
                ))

        if filtro in ('TODOS', 'REGISTROS DNS'):
            for reg in self.resultados['registros']:
                self.tree_resultados.insert('', tk.END, values=(
                    f"DNS {reg['tipo']}",
                    reg['valor'][:50],
                    '-',
                    '-',
                    '-'
                ))


def main():
    try:
        root = tk.Tk()
    except:
        sys.exit(1)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('green.Horizontal.TProgressbar',
                    background=CORES['progress'],
                    troughcolor=CORES['entry_bg'],
                    bordercolor=CORES['bg'],
                    lightcolor=CORES['progress'],
                    darkcolor=CORES['progress'])

    app = DNSReconGUI(root)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()

if __name__ == "__main__":
    main()
