import os
import winreg
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Identificação de Administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Chaves do Registro monitoradas
LOCATIONS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Usuário Atual"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Máquina Local"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Máquina Local (32-bit)")
]

# Chave interna para guardar os programas desativados
DISABLED_SUBKEY = r"Software\StartupManagerPro\Disabled"

class AdvancedStartupManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Inicialização Avançado")
        self.root.geometry("1100x560")
        self.root.minsize(900, 450)
        self.root.configure(bg="#1e1e2e")

        self.dados_completos = []

        self.configurar_estilos()
        self.criar_layout()
        self.carregar_programas()

    def identificar_categoria(self, nome, caminho):
        """Identifica automaticamente o tipo do programa com base no nome e caminho."""
        texto = f"{nome} {caminho}".lower()

        # Áudio
        if any(p in texto for p in ["realtek", "audio", "sound", "waves", "nahimic", "conexant", "creative", "smartbyte"]):
            return "🔊 Áudio"

        # Placa de Vídeo
        if any(p in texto for p in ["nvidia", "nvcontainer", "nvdisplay", "geforce", "shadowplay", "amd", "radeon", "catalyst", "igfx", "intel graphics"]):
            return "🖥️ Placa de Vídeo"

        # Periféricos / Mouse / Teclado
        if any(p in texto for p in ["mouse", "teclado", "keyboard", "touchpad", "synaptics", "logitech", "lghub", "razer", "synapse", "corsair", "icue", "steelseries", "redragon", "bloody"]):
            return "🖱️ Periféricos / Mouse"

        # Jogos e Plataformas
        if any(p in texto for p in ["steam", "epicgames", "riot", "ea desktop", "origin", "battle.net", "ubisoft", "gog galaxy"]):
            return "🎮 Jogos / Launcher"

        # Comunicação
        if any(p in texto for p in ["discord", "telegram", "whatsapp", "skype", "teams", "slack", "zoom"]):
            return "💬 Comunicação"

        # Nuvem / Sincronização
        if any(p in texto for p in ["onedrive", "googledrive", "dropbox", "mega", "icloud"]):
            return "☁️ Nuvem / Backup"

        # Segurança / Antivírus
        if any(p in texto for p in ["security", "defender", "antivirus", "avast", "avg", "kaspersky", "malwarebytes", "norton", "mcafee"]):
            return "🛡️ Segurança"

        # Navegadores
        if any(p in texto for p in ["chrome", "msedge", "edge", "firefox", "opera", "brave", "vivaldi"]):
            return "🌐 Navegador"

        return "📦 Aplicativo Geral"

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configuração das cores da tabela
        self.style.configure(
            "Treeview",
            background="#181825",
            foreground="#cdd6f4",
            rowheight=28,
            fieldbackground="#181825",
            font=("Segoe UI", 9)
        )
        self.style.map("Treeview", background=[('selected', '#45475a')])

        # Cabeçalho da tabela
        self.style.configure(
            "Treeview.Heading",
            background="#313244",
            foreground="#cdd6f4",
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        self.style.map("Treeview.Heading", background=[('active', '#45475a')])

    def criar_layout(self):
        # Topo: Cabeçalho & Status
        topo = tk.Frame(self.root, bg="#11111b", height=50)
        topo.pack(fill=tk.X, side=tk.TOP)

        lbl_titulo = tk.Label(
            topo, text="🚀 Gerenciador de Inicialização",
            font=("Segoe UI", 13, "bold"), fg="#89b4fa", bg="#11111b"
        )
        lbl_titulo.pack(side=tk.LEFT, padx=15, pady=10)

        # Indicador de privilégio Admin
        admin_text = "Modo Administrador: ATIVO" if is_admin() else "Modo: Usuário Padrão"
        admin_color = "#a6e3a1" if is_admin() else "#f9e2af"
        lbl_admin = tk.Label(topo, text=admin_text, font=("Segoe UI", 9), fg=admin_color, bg="#11111b")
        lbl_admin.pack(side=tk.RIGHT, padx=15)

        # Barra de Ações & Busca
        barra_ferramentas = tk.Frame(self.root, bg="#1e1e2e", pady=8)
        barra_ferramentas.pack(fill=tk.X, padx=15)

        btn_add = tk.Button(
            barra_ferramentas, text="+ Adicionar Programa", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=12, cursor="hand2", command=self.adicionar_programa
        )
        btn_add.pack(side=tk.LEFT, padx=(0, 6))

        btn_toggle = tk.Button(
            barra_ferramentas, text="⇄ Ativar / Desativar", bg="#89b4fa", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=12, cursor="hand2", command=self.alternar_status
        )
        btn_toggle.pack(side=tk.LEFT, padx=6)

        btn_del = tk.Button(
            barra_ferramentas, text="🗑 Remover Programa", bg="#f38ba8", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=12, cursor="hand2", command=self.excluir_registro
        )
        btn_del.pack(side=tk.LEFT, padx=6)

        # Campo de busca
        self.entry_busca = tk.Entry(barra_ferramentas, bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 10), width=24, relief="flat")
        self.entry_busca.pack(side=tk.RIGHT, ipady=3)
        self.entry_busca.bind("<KeyRelease>", self.filtrar_tabela)

        lbl_busca = tk.Label(barra_ferramentas, text="🔍 Buscar:", fg="#cdd6f4", bg="#1e1e2e", font=("Segoe UI", 9))
        lbl_busca.pack(side=tk.RIGHT, padx=5)

        # Container da Tabela
        frame_tabela = tk.Frame(self.root, bg="#1e1e2e")
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 5))

        colunas = ("status", "categoria", "nome", "local", "caminho")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("status", text="Status")
        self.tree.heading("categoria", text="Tipo / Categoria")
        self.tree.heading("nome", text="Nome do Programa")
        self.tree.heading("local", text="Local")
        self.tree.heading("caminho", text="Caminho do Executável")

        self.tree.column("status", width=100, anchor="center")
        self.tree.column("categoria", width=200, anchor="w")
        self.tree.column("nome", width=170)
        self.tree.column("local", width=140)
        self.tree.column("caminho", width=460)

        # Tags de cores para o Status
        self.tree.tag_configure("ATIVO", foreground="#a6e3a1")
        self.tree.tag_configure("DESATIVADO", foreground="#f38ba8")

        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Barra Inferior (Resumo)
        self.lbl_rodape = tk.Label(self.root, text="", bg="#11111b", fg="#a6adc8", font=("Segoe UI", 9), anchor="w", padx=15, pady=5)
        self.lbl_rodape.pack(fill=tk.X, side=tk.BOTTOM)

    def carregar_programas(self):
        self.dados_completos.clear()

        # 1. Carregar programas Ativos
        for hkey, subkey, desc in LOCATIONS:
            try:
                with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as key:
                    idx = 0
                    while True:
                        try:
                            nome, caminho, _ = winreg.EnumValue(key, idx)
                            categoria = self.identificar_categoria(nome, caminho)
                            self.dados_completos.append({
                                "status": "ATIVO", "categoria": categoria, "nome": nome,
                                "local": desc, "caminho": caminho, "hkey": hkey, "subkey": subkey
                            })
                            idx += 1
                        except OSError:
                            break
            except Exception:
                pass

        # 2. Carregar programas Desativados
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_SUBKEY, 0, winreg.KEY_READ) as key:
                idx = 0
                while True:
                    try:
                        nome, valor, _ = winreg.EnumValue(key, idx)
                        local_orig, caminho_real = valor.split("|", 1)
                        categoria = self.identificar_categoria(nome, caminho_real)
                        self.dados_completos.append({
                            "status": "DESATIVADO", "categoria": categoria, "nome": nome,
                            "local": local_orig, "caminho": caminho_real,
                            "hkey": winreg.HKEY_CURRENT_USER, "subkey": DISABLED_SUBKEY
                        })
                        idx += 1
                    except OSError:
                        break
        except Exception:
            pass

        self.atualizar_tabela(self.dados_completos)

    def atualizar_tabela(self, lista):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ativos = 0
        desativados = 0

        for dado in lista:
            status_formatado = "✔ ATIVO" if dado["status"] == "ATIVO" else "✖ DESATIVADO"
            if dado["status"] == "ATIVO":
                ativos += 1
            else:
                desativados += 1

            self.tree.insert(
                "", tk.END,
                values=(status_formatado, dado["categoria"], dado["nome"], dado["local"], dado["caminho"]),
                tags=(dado["status"],)
            )

        self.lbl_rodape.config(
            text=f"Total: {len(lista)} programas  |  Ativos: {ativos}  |  Desativados: {desativados}"
        )

    def filtrar_tabela(self, event=None):
        termo = self.entry_busca.get().lower()
        if not termo:
            self.atualizar_tabela(self.dados_completos)
            return

        filtrados = [
            d for d in self.dados_completos 
            if termo in d["nome"].lower() or termo in d["caminho"].lower() or termo in d["categoria"].lower()
        ]
        self.atualizar_tabela(filtrados)

    def alternar_status(self):
        item_sel = self.tree.selection()
        if not item_sel:
            messagebox.showwarning("Aviso", "Selecione um programa na lista antes de clicar.")
            return

        nome = self.tree.item(item_sel[0], "values")[2]
        item_dado = next((d for d in self.dados_completos if d["nome"] == nome), None)
        if not item_dado:
            return

        try:
            if item_dado["status"] == "ATIVO":
                # Desativar
                with winreg.OpenKey(item_dado["hkey"], item_dado["subkey"], 0, winreg.KEY_SET_VALUE) as k_orig:
                    winreg.DeleteValue(k_orig, item_dado["nome"])

                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, DISABLED_SUBKEY) as k_dest:
                    winreg.SetValueEx(k_dest, item_dado["nome"], 0, winreg.REG_SZ, f"{item_dado['local']}|{item_dado['caminho']}")
            else:
                # Reativar
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_SUBKEY, 0, winreg.KEY_SET_VALUE) as k_dis:
                    winreg.DeleteValue(k_dis, item_dado["nome"])

                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k_run:
                    winreg.SetValueEx(k_run, item_dado["nome"], 0, winreg.REG_SZ, item_dado["caminho"])

            self.carregar_programas()
        except PermissionError:
            messagebox.showerror("Erro de Permissão", "Para alterar este programa, abra o script como Administrador.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao alterar status:\n{e}")

    def adicionar_programa(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o Executável",
            filetypes=[("Programas (*.exe)", "*.exe"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho:
            return

        nome_padrao = os.path.splitext(os.path.basename(caminho))[0]

        janela = tk.Toplevel(self.root)
        janela.title("Nome do Programa")
        janela.geometry("320x130")
        janela.configure(bg="#1e1e2e")
        janela.transient(self.root)
        janela.grab_set()

        tk.Label(janela, text="Nome de exibição:", fg="#cdd6f4", bg="#1e1e2e", font=("Segoe UI", 9)).pack(pady=5)
        entry = tk.Entry(janela, bg="#313244", fg="#cdd6f4", insertbackground="white", width=30)
        entry.insert(0, nome_padrao)
        entry.pack(pady=5)

        def salvar():
            nome = entry.get().strip()
            if not nome:
                return
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, nome, 0, winreg.REG_SZ, f'"{caminho}"')
                janela.destroy()
                self.carregar_programas()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível adicionar:\n{e}")

        tk.Button(janela, text="Adicionar", bg="#a6e3a1", fg="#11111b", relief="flat", font=("Segoe UI", 9, "bold"), command=salvar).pack(pady=10)

    def excluir_registro(self):
        item_sel = self.tree.selection()
        if not item_sel:
            messagebox.showwarning("Aviso", "Selecione um programa na lista antes de clicar em Remover.")
            return

        nome = self.tree.item(item_sel[0], "values")[2]
        item_dado = next((d for d in self.dados_completos if d["nome"] == nome), None)
        if not item_dado:
            return

        if not messagebox.askyesno("Confirmar Remoção", f"Deseja realmente remover '{nome}' da lista de inicialização?"):
            return

        try:
            with winreg.OpenKey(item_dado["hkey"], item_dado["subkey"], 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, item_dado["nome"])
            self.carregar_programas()
        except PermissionError:
            messagebox.showerror("Acesso Negado", "Permissão negada. Abra o script como Administrador.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível remover:\n{e}")

if __name__ == "__main__":
    app_root = tk.Tk()
    app = AdvancedStartupManager(app_root)
    app_root.mainloop()
