import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import re
import os
import webbrowser

class EditorSublimeAbas:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Sublime")
        root.wm_state('zoomed')  # Starts maximized
        self.root.configure(bg='#1E1E1E')

        # Temas
        self.temas = {
            'Escuro Padrão': {
                'bg': '#1E1E1E',          # Fundo do editor
                'fg': '#06d13c',          # Texto normal
                'select_bg': '#264F78',   # Fundo da seleção
                'cursor': '#FFFFFF',       # Cor do cursor

                # Python / palavras-chave
                'keyword': '#569CD6',     # Palavras-chave (def, class, if, etc.)
                'string': '#CE9178',      # Strings
                'comment': '#FFFFFF',     # Comentários
                'number': '#B5CEA8',      # Números
                'operator': '#D4D4D4',    # Operadores (+, -, *, /, =, etc.)

                
                # HTML
                'tag': '#FFFF00',           # tags <div>, <span>, <p> em amarelo puro
                'attr': '#05cffc',          # atributos em azul claro
                'value': '#CE9178',         # valores em laranja
                'comment': '#FFFFFF',       # comentários verdes
                'doctype': '#FFFF00',       # <!DOCTYPE html> também amarelo puro
                'html_keyword': '#D16DFF',  # palavras-chave HTML em lilás
                'number': '#0522fc',        # números em verde claro


                # CSS
                'property': '#9CDCFE',     # propriedades (color, font-size)
                'css_value': '#CE9178',    # valores (red, 12px)
                'selector': '#D4D4D4',     # seletores (.class, #id, tag)

                # JavaScript
                'js_keyword': '#569CD6',   # function, var, let, const, if, else
                'js_string': '#CE9178',    # strings
                'js_comment': '#FFFFFF',  # branco para comentários JS
                'js_number': '#B5CEA8',    # números                

                # JSON
                'json_key': '#9CDCFE',     # chaves
                'json_string': '#CE9178',  # valores de string
                'json_number': '#B5CEA8',  # números
                'json_keyword': '#569CD6', # true, false, null

                # Números de linha
                'line_number': '#D4D4D4'   # cor dos números da linha
            },
            'Claro': {
                'bg': '#FFFFFF', 'fg': '#000000', 'select_bg': '#3399FF', 'cursor': '#000000',
                'keyword': '#0000FF', 'string': '#A31515', 'comment': '#008000', 'number': '#098658',
                'tag': '#0000FF', 'attr': '#FF0000', 'property': '#FF0000', 'value': '#0000FF'
            }
        }
        self.tema_atual = 'Escuro Padrão'

        # Fonte
        self.tamanho_fonte = 12
        self.familia_fonte = 'Consolas'
        self.fonte_editor = font.Font(family=self.familia_fonte, size=self.tamanho_fonte)

        # Auto-salvar
        self.auto_salvar_ativo = True

        # Criar interface
        self.criar_menu()
        self.criar_toolbar()
        self.criar_abas()
        self.nova_aba()  # Create the first tab
        self.aplicar_tema()  # Apply theme after creating the tab

    # ---------- MENU ----------
    def criar_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_arquivo = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=menu_arquivo)
        menu_arquivo.add_command(label="Nova Aba", accelerator="Ctrl+N", command=self.nova_aba)
        menu_arquivo.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.abrir_arquivo)
        menu_arquivo.add_command(label="Salvar", accelerator="Ctrl+S", command=self.salvar_arquivo)
        menu_arquivo.add_command(label="Salvar Como...", command=self.salvar_como)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Fechar Aba", command=self.fechar_aba)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.root.quit)

        menu_exibir = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Exibir", menu=menu_exibir)
        menu_exibir.add_command(label="Tela Cheia", accelerator="F11", command=self.alternar_tela_cheia)
        submenu_tema = tk.Menu(menu_exibir, tearoff=0)
        menu_exibir.add_cascade(label="Temas", menu=submenu_tema)
        for tema in self.temas:
            submenu_tema.add_command(label=tema, command=lambda t=tema: self.mudar_tema(t))

        menu_ferramentas = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=menu_ferramentas)
        menu_ferramentas.add_command(label="Auto-Salvar", command=self.alternar_auto_salvar)
        menu_ferramentas.add_command(label="Executar Código", command=self.executar_codigo)

    # ---------- TOOLBAR ----------
    def criar_toolbar(self):
        toolbar = tk.Frame(self.root, bg='#252526')
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="Nova Aba", command=self.nova_aba, bg='#0E639C', fg='white', width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="Salvar", command=self.salvar_arquivo, bg='#0E639C', fg='white', width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="Executar", command=self.executar_codigo, bg='#007ACC', fg='white', width=10).pack(side=tk.LEFT, padx=1)

        tk.Label(toolbar, text="Fonte:", bg='#252526', fg='white').pack(side=tk.LEFT, padx=5)
        self.variavel_fonte = tk.StringVar(value=str(self.tamanho_fonte))
        tk.Spinbox(toolbar, from_=8, to=24, textvariable=self.variavel_fonte, width=5,
                   command=self.mudar_tamanho_fonte).pack(side=tk.LEFT, padx=1)

  
   # ---------- ABAS ----------
    def criar_abas(self):
        self.abas = ttk.Notebook(self.root)
        self.abas.pack(fill=tk.BOTH, expand=True)
        self.abas.enable_traversal()
        self.abas.bind("<<NotebookTabChanged>>", self.aba_trocada)
        self.abas_data = {}  # {'frame': {'texto':..., 'numeros':..., 'arquivo':..., 'status':...}}

    def nova_aba(self):
        frame = tk.Frame(self.abas)
        frame.pack(fill=tk.BOTH, expand=True)

        # Frame para linha de números + texto
        editor_frame = tk.Frame(frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        numeros_linhas = tk.Text(editor_frame, width=4, padx=3, takefocus=0, border=0,
                                bg='#252526', fg='#858585', font=('Consolas', 12))
        numeros_linhas.pack(side=tk.LEFT, fill=tk.Y)

        barra_vertical = tk.Scrollbar(editor_frame, orient=tk.VERTICAL)
        barra_vertical.pack(side=tk.RIGHT, fill=tk.Y)

        barra_horizontal = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        barra_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

        texto = tk.Text(editor_frame, wrap=tk.NONE, undo=True, font=self.fonte_editor,
                        yscrollcommand=barra_vertical.set, xscrollcommand=barra_horizontal.set,
                        selectbackground=self.temas[self.tema_atual]['select_bg'],
                        insertbackground=self.temas[self.tema_atual]['cursor'])
        texto.pack(fill=tk.BOTH, expand=True)

        barra_vertical.config(command=lambda *args: (texto.yview(*args), numeros_linhas.yview(*args)))
        barra_horizontal.config(command=texto.xview)

        texto.bind('<MouseWheel>', lambda e: numeros_linhas.yview_scroll(int(-1*(e.delta/120)), "units"))
        numeros_linhas.bind('<MouseWheel>', lambda e: texto.yview_scroll(int(-1*(e.delta/120)), "units"))

        texto.bind('<KeyRelease>', lambda e: self.atualizar_linhas_e_destacar(texto, numeros_linhas))

        status_bar = tk.Label(frame, text="Pronto",
                            bg=self.temas[self.tema_atual]['bg'],
                            fg=self.temas[self.tema_atual]['fg'],
                            anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Adiciona a aba com "×" para fechar
        self.abas.add(frame, text="Sem título ×")
        self.abas.select(frame)

        self.abas_data[frame] = {
            'texto': texto,
            'numeros': numeros_linhas,
            'arquivo': None,
            'status': status_bar
        }

        self.atualizar_linhas_e_destacar(texto, numeros_linhas)
        self.aplicar_tema()

        # Clique no título da aba para fechar ao clicar no "×"
        def click_aba(event):
            x, y = event.x, event.y
            try:
                index = self.abas.index("@%d,%d" % (x, y))
                titulo = self.abas.tab(index, "text")
                if "×" in titulo:
                    if messagebox.askyesno("Fechar Aba", "Deseja realmente fechar esta aba?"):
                        aba_frame = self.abas.nametowidget(self.abas.tabs()[index])
                        self.abas.forget(aba_frame)
                        self.abas_data.pop(aba_frame, None)
            except Exception:
                pass

        self.abas.bind("<Button-1>", click_aba)

    def fechar_aba(self):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            if messagebox.askyesno("Fechar Aba", "Deseja realmente fechar esta aba?"):
                self.abas.forget(frame)
                self.abas_data.pop(frame, None)

    def aba_trocada(self, event=None):
        self.atualizar_status()


    # ---------- UTILITÁRIOS ----------
    def get_texto_atual(self):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            return self.abas_data[frame]['texto']
        return None

    def get_numeros_atual(self):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            return self.abas_data[frame]['numeros']
        return None

    def get_status_atual(self):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            return self.abas_data[frame]['status']
        return None

    def get_arquivo_atual(self):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            return self.abas_data[frame]['arquivo']
        return None

    def set_arquivo_atual(self, caminho):
        aba_atual = self.abas.select()
        if aba_atual:
            frame = self.root.nametowidget(aba_atual)
            self.abas_data[frame]['arquivo'] = caminho
            self.abas.tab(frame, text=os.path.basename(caminho))

    # ---------- ARQUIVOS ----------
    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(defaultextension=".*",
                                            filetypes=[("Todos os arquivos", "*.*"), ("Python", "*.py"),
                                                        ("HTML", "*.html"), ("CSS", "*.css"),
                                                        ("JavaScript", "*.js"), ("JSON", "*.json")])
        if caminho:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            self.nova_aba()
            texto = self.get_texto_atual()
            numeros = self.get_numeros_atual()  # pegando o widget das linhas
            texto.delete('1.0', tk.END)
            texto.insert('1.0', conteudo)
            self.set_arquivo_atual(caminho)
            # Atualiza linhas numeradas e status
            self.atualizar_linhas_e_destacar(texto, numeros)
            # Reaplicar o tema ativo para garantir cores corretas
            self.aplicar_tema()
            # Configurar highlighter da linguagem
            self.configurar_highlighter_por_ext(caminho)


    def salvar_arquivo(self):
        arquivo = self.get_arquivo_atual()
        texto = self.get_texto_atual()
        if not arquivo:
            self.salvar_como()
        else:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(texto.get('1.0', tk.END))
            messagebox.showinfo("Salvo", "Arquivo salvo com sucesso!")

    def salvar_como(self):
        arquivo = filedialog.asksaveasfilename(defaultextension=".py",
                                               filetypes=[("Python", "*.py"), ("HTML", "*.html"),
                                                          ("CSS", "*.css"), ("JavaScript", "*.js"),
                                                          ("JSON", "*.json"), ("Todos os arquivos", "*.*")])
        if arquivo:
            texto = self.get_texto_atual()
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(texto.get('1.0', tk.END))
            self.set_arquivo_atual(arquivo)
            self.configurar_highlighter_por_ext(arquivo)

    # ---------- EXECUTAR CÓDIGO ----------
    def executar_codigo(self):
        arquivo = self.get_arquivo_atual()
        texto = self.get_texto_atual()
        if not arquivo:
            messagebox.showwarning("Executar", "Salve o arquivo antes de executar!")
            return
        ext = os.path.splitext(arquivo)[1].lower()
        if ext == '.py':
            try:
                exec(texto.get('1.0', tk.END))
            except Exception as e:
                messagebox.showerror("Erro de Execução", str(e))
        elif ext in ['.html', '.js']:
            webbrowser.open(f'file://{os.path.abspath(arquivo)}')
        else:
            messagebox.showwarning("Executar", "Não é possível executar este tipo de arquivo!")

    # ---------- DESTACAR SINTAXE ----------
    def configurar_highlighter_por_ext(self, arquivo):
        ext = os.path.splitext(arquivo)[1].lower()
        lang = 'python'
        if ext == '.html': lang='html'
        elif ext == '.css': lang='css'
        elif ext == '.js': lang='javascript'
        elif ext == '.json': lang='json'
        self.configurar_highlighter(lang)

    def configurar_highlighter(self, linguagem='python'):
        texto = self.get_texto_atual()
        if not texto: return

        padroes = {
            'python': [
                (r'\b(def|class|if|else|elif|for|while|try|except|return|import|from|as|with|pass|in|is|not|and|or)\b', 'keyword'),
                (r'".*?"|\'.*?\'', 'string'),
                (r'#.*$', 'comment'),
                (r'\b\d+\.?\d*\b', 'number')
            ],

            'html': [
                # Comentários
                (r'<!--.*?-->', 'comment'),                # verde
                # Tags de abertura e fechamento
                (r'<\s*/?\s*\w+', 'tag'),                  # amarelo ou roxo         
                # Fechamento de tags
                (r'/?>', 'tag'),                           # mesma cor das tags
                # Atributos
                (r'\b(class|id|src|href|alt|title|style|type|rel|lang|charset)\b', 'attr'),  
                # Valores de atributos
                (r'".*?"', 'value'),                        # laranja
                (r"'.*?'", 'value'),                        # laranja
                # Palavras-chave HTML
                (r'\b(doctype|html|head|body|meta|link|title|script|style|div|span|h[1-6]|p|a|img|ul|li|ol|form|input|button|nav|footer|header)\b', 'html_keyword'),
                # Números dentro de atributos
                (r'\b\d+\.?\d*\b', 'number')
            ],

            'css': [
                (r'/\*.*?\*/', 'comment'),
                (r'\b[\w-]+(?=\s*:)', 'property'),
                (r':\s*[^;]+;', 'value')
            ],
            'javascript': [
                (r'\b(function|var|let|const|if|else|for|while|return|try|catch|class|new|this|in|of|switch|case|break|continue)\b', 'js_keyword'),
                (r'".*?"|\'.*?\'|`.*?`', 'js_string'),
                (r'//.*$', 'js_comment'),      # tag separada para comentários JS
                (r'/\*.*?\*/', 'js_comment'),
                (r'\b\d+\.?\d*\b', 'js_number')

            ],
            'json': [
                (r'"[^"]*"\s*:', 'attr'),
                (r'".*?"', 'string'),
                (r'\b\d+\.?\d*\b', 'number'),
                (r'\b(true|false|null)\b', 'keyword')
            ]
        }

        def destacar(event=None):
            for tag in ['keyword','string','comment','number','tag','attr','property','value']:
                texto.tag_remove(tag,'1.0',tk.END)
            conteudo = texto.get("1.0", tk.END)
            for padrao, tag in padroes.get(linguagem, []):
                for m in re.finditer(padrao, conteudo, re.MULTILINE):
                    inicio = f"1.0 + {m.start()} chars"
                    fim = f"1.0 + {m.end()} chars"
                    texto.tag_add(tag, inicio, fim)
                    texto.tag_config(tag, foreground=self.temas[self.tema_atual].get(tag,'#FFFFFF'))

        destacar()
        texto.bind('<KeyRelease>', lambda e: destacar() or self.atualizar_linhas_e_destacar(texto, self.get_numeros_atual()))

    # ---------- LINHAS & STATUS ----------
    def atualizar_linhas_e_destacar(self, texto, numeros_linhas):
        numeros_linhas.config(state=tk.NORMAL)
        numeros_linhas.delete('1.0', tk.END)
        linhas = int(texto.index('end-1c').split('.')[0])
        numeros_linhas.insert('1.0', "\n".join(str(i) for i in range(1, linhas + 1)))
        numeros_linhas.config(state=tk.DISABLED)
        numeros_linhas.yview_moveto(texto.yview()[0])
        self.atualizar_status()

    def atualizar_status(self):
        texto = self.get_texto_atual()
        status = self.get_status_atual()
        arquivo = self.get_arquivo_atual()
        if texto and status:
            linha, coluna = texto.index(tk.INSERT).split('.')
            status.config(text=f"Linha {linha}, Coluna {coluna} | {arquivo or 'Sem título'}")

    # ---------- OUTROS ----------
    def alternar_tela_cheia(self, event=None):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    def alternar_auto_salvar(self):
        self.auto_salvar_ativo = not self.auto_salvar_ativo
        messagebox.showinfo("Auto-Salvar", f"Auto-salvar {'ativado' if self.auto_salvar_ativo else 'desativado'}")

    def aplicar_tema(self):
        for frame, data in self.abas_data.items():
            texto = data['texto']
            numeros = data['numeros']
            status = data['status']
            tema = self.temas[self.tema_atual]

            # Configurações do editor
            texto.configure(
                bg=tema['bg'],
                fg=tema['fg'],
                insertbackground=tema['cursor'],
                selectbackground=tema['select_bg']
            )

            # Números das linhas
            numeros.configure(
                bg=tema['bg'],
                fg=tema['line_number']  # <- aqui aplicamos a cor #D4D4D4
            )

            # Barra de status
            status.configure(
                bg=tema['bg'],
                fg=tema['fg']
            )


    def mudar_tema(self, nome):
        self.tema_atual = nome
        self.aplicar_tema()
        arquivo = self.get_arquivo_atual()
        if arquivo:
            self.configurar_highlighter_por_ext(arquivo)

    def mudar_tamanho_fonte(self):
        self.tamanho_fonte = int(self.variavel_fonte.get())
        self.fonte_editor.configure(size=self.tamanho_fonte)
        for frame, data in self.abas_data.items():
            data['texto'].configure(font=self.fonte_editor)
            data['numeros'].configure(font=self.fonte_editor)

# ---------- MAIN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = EditorSublimeAbas(root)
    root.mainloop()
