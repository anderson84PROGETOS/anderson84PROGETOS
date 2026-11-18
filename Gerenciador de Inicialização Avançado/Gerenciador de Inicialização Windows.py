import os
import sys
import winreg
import ctypes
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- VERIFICAÇÃO DE ADMINISTRADOR ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# --- CONFIGURAÇÕES DE LOCAIS DO WINDOWS ---
LOCATIONS_REG = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Usuário Atual (Registro)"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Máquina Local (Registro)"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Máquina Local 32-bit (Registro)")
]

# Pasta Inicializar do Windows (Startup Folder)
USER_STARTUP_DIR = os.path.join(os.getenv('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
USER_STARTUP_DISABLED_DIR = os.path.join(os.getenv('APPDATA', ''), r'StartupManagerPro\DisabledShortcuts')

# Chave interna do registro para guardar programas desativados
DISABLED_REG_SUBKEY = r"Software\StartupManagerPro\Disabled"


class AdvancedSystemCareStartupManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Inicialização Windows")
        self.root.geometry("1150x600")
        self.root.minsize(950, 500)
        self.root.configure(bg="#1e1e2e")

        self.dados_completos = []

        # Criar pasta de atalhos desativados se não existir
        os.makedirs(USER_STARTUP_DISABLED_DIR, exist_ok=True)

        self.configurar_estilos()
        self.criar_layout()
        self.carregar_programas()

    def identificar_categoria(self, nome, caminho):
        """Categoriza o aplicativo com base em palavras-chave."""
        texto = f"{nome} {caminho}".lower()

        if any(p in texto for p in ["realtek", "audio", "sound", "waves", "nahimic", "conexant", "creative"]):
            return "🔊 Áudio & Som"
        if any(p in texto for p in ["nvidia", "nvcontainer", "geforce", "amd", "radeon", "intel graphics"]):
            return "🖥️ Placa de Vídeo / Sistema"
        if any(p in texto for p in ["mouse", "teclado", "logitech", "lghub", "razer", "corsair", "icue", "steelseries"]):
            return "🖱️ Periféricos & Hardware"
        if any(p in texto for p in ["steam", "epicgames", "riot", "origin", "battle.net", "ubisoft"]):
            return "🎮 Jogos & Launchers"
        if any(p in texto for p in ["discord", "telegram", "whatsapp", "skype", "teams", "slack", "zoom"]):
            return "💬 Comunicação"
        if any(p in texto for p in ["onedrive", "googledrive", "dropbox", "mega", "icloud"]):
            return "☁️ Nuvem / Backup"
        if any(p in texto for p in ["defender", "antivirus", "avast", "avg", "kaspersky", "malwarebytes", "norton"]):
            return "🛡️ Segurança"
        if any(p in texto for p in ["chrome", "msedge", "edge", "firefox", "opera", "brave"]):
            return "🌐 Navegadores"

        return "📦 Aplicativo Geral"

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Tabela
        self.style.configure(
            "Treeview",
            background="#181825",
            foreground="#cdd6f4",
            rowheight=30,
            fieldbackground="#181825",
            font=("Segoe UI", 9)
        )
        self.style.map("Treeview", background=[('selected', '#45475a')])

        # Cabeçalho da Tabela
        self.style.configure(
            "Treeview.Heading",
            background="#313244",
            foreground="#cdd6f4",
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        self.style.map("Treeview.Heading", background=[('active', '#45475a')])

    def criar_layout(self):
        # Cabeçalho Topo
        topo = tk.Frame(self.root, bg="#11111b", height=55)
        topo.pack(fill=tk.X, side=tk.TOP)

        lbl_titulo = tk.Label(
            topo, text="🚀 Advanced Startup Optimizer",
            font=("Segoe UI", 14, "bold"), fg="#89b4fa", bg="#11111b"
        )
        lbl_titulo.pack(side=tk.LEFT, padx=15, pady=12)

        # Indicador Admin
        admin_text = "🛡️ Modo Administrador: ATIVO" if is_admin() else "⚠️ Modo Usuário (Limitado)"
        admin_color = "#a6e3a1" if is_admin() else "#f9e2af"
        lbl_admin = tk.Label(topo, text=admin_text, font=("Segoe UI", 9, "bold"), fg=admin_color, bg="#11111b")
        lbl_admin.pack(side=tk.RIGHT, padx=15)

        # Barra de Ferramentas / Ações
        barra = tk.Frame(self.root, bg="#1e1e2e", pady=10)
        barra.pack(fill=tk.X, padx=15)

        # Botão: Adicionar ao Startup
        btn_add = tk.Button(
            barra, text="➕ Permiti/Adicionar ao Startup", bg="#a6e3a1", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, cursor="hand2",
            command=self.adicionar_programa
        )
        btn_add.pack(side=tk.LEFT, padx=(0, 5))

        # Botão: Bloquear / Impedir Executável
        btn_block = tk.Button(
            barra, text="⛔ Impedir Executável de Abrir", bg="#f9e2af", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, cursor="hand2",
            command=self.bloquear_executavel_direto
        )
        btn_block.pack(side=tk.LEFT, padx=5)

        # Botão: Alternar Ativo/Desativado
        btn_toggle = tk.Button(
            barra, text="⇄ Ativar / Desativar Selecionado", bg="#89b4fa", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, cursor="hand2",
            command=self.alternar_status
        )
        btn_toggle.pack(side=tk.LEFT, padx=5)

        # Botão: Excluir
        btn_del = tk.Button(
            barra, text="🗑 Excluir Definitivo", bg="#f38ba8", fg="#11111b",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5, cursor="hand2",
            command=self.excluir_registro
        )
        btn_del.pack(side=tk.LEFT, padx=5)

        # Campo de busca
        self.entry_busca = tk.Entry(barra, bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 10), width=20, relief="flat")
        self.entry_busca.pack(side=tk.RIGHT, ipady=4)
        self.entry_busca.bind("<KeyRelease>", self.filtrar_tabela)

        lbl_busca = tk.Label(barra, text="🔍 Buscar:", fg="#cdd6f4", bg="#1e1e2e", font=("Segoe UI", 9))
        lbl_busca.pack(side=tk.RIGHT, padx=5)

        # Tabela (Treeview)
        frame_tabela = tk.Frame(self.root, bg="#1e1e2e")
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 5))

        colunas = ("status", "categoria", "nome", "local", "caminho")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("status", text="Status")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("nome", text="Nome do Programa")
        self.tree.heading("local", text="Origem / Local")
        self.tree.heading("caminho", text="Caminho do Arquivo")

        self.tree.column("status", width=110, anchor="center")
        self.tree.column("categoria", width=180, anchor="w")
        self.tree.column("nome", width=200)
        self.tree.column("local", width=170)
        self.tree.column("caminho", width=420)

        # Cores para Status
        self.tree.tag_configure("ATIVO", foreground="#a6e3a1")
        self.tree.tag_configure("DESATIVADO", foreground="#f38ba8")

        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Rodapé
        self.lbl_rodape = tk.Label(self.root, text="", bg="#11111b", fg="#a6adc8", font=("Segoe UI", 9), anchor="w", padx=15, pady=6)
        self.lbl_rodape.pack(fill=tk.X, side=tk.BOTTOM)

    def carregar_programas(self):
        """Carrega aplicativos dos Registros e da Pasta Inicializar do Windows."""
        self.dados_completos.clear()

        # 1. Registro: Programas ATIVOS
        for hkey, subkey, desc in LOCATIONS_REG:
            try:
                with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as key:
                    idx = 0
                    while True:
                        try:
                            nome, caminho, _ = winreg.EnumValue(key, idx)
                            self.dados_completos.append({
                                "status": "ATIVO", "categoria": self.identificar_categoria(nome, caminho),
                                "nome": nome, "local": desc, "caminho": caminho,
                                "tipo": "REGISTRY", "hkey": hkey, "subkey": subkey
                            })
                            idx += 1
                        except OSError:
                            break
            except Exception:
                pass

        # 2. Registro: Programas DESATIVADOS (Banco de dados interno)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_REG_SUBKEY, 0, winreg.KEY_READ) as key:
                idx = 0
                while True:
                    try:
                        nome, valor, _ = winreg.EnumValue(key, idx)
                        local_orig, caminho_real = valor.split("|", 1)
                        self.dados_completos.append({
                            "status": "DESATIVADO", "categoria": self.identificar_categoria(nome, caminho_real),
                            "nome": nome, "local": local_orig, "caminho": caminho_real,
                            "tipo": "REGISTRY_DISABLED", "hkey": winreg.HKEY_CURRENT_USER, "subkey": DISABLED_REG_SUBKEY
                        })
                        idx += 1
                    except OSError:
                        break
        except Exception:
            pass

        # 3. Pasta Inicializar do Windows (Ativos)
        if os.path.exists(USER_STARTUP_DIR):
            for arq in os.listdir(USER_STARTUP_DIR):
                caminho_completo = os.path.join(USER_STARTUP_DIR, arq)
                if os.path.isfile(caminho_completo) and not arq.lower() == "desktop.ini":
                    nome = os.path.splitext(arq)[0]
                    self.dados_completos.append({
                        "status": "ATIVO", "categoria": self.identificar_categoria(nome, caminho_completo),
                        "nome": nome, "local": "Pasta Inicializar (Startup)", "caminho": caminho_completo,
                        "tipo": "FOLDER", "file_path": caminho_completo
                    })

        # 4. Pasta Inicializar do Windows (Desativados)
        if os.path.exists(USER_STARTUP_DISABLED_DIR):
            for arq in os.listdir(USER_STARTUP_DISABLED_DIR):
                caminho_completo = os.path.join(USER_STARTUP_DISABLED_DIR, arq)
                if os.path.isfile(caminho_completo):
                    nome = os.path.splitext(arq)[0]
                    self.dados_completos.append({
                        "status": "DESATIVADO", "categoria": self.identificar_categoria(nome, caminho_completo),
                        "nome": nome, "local": "Pasta Inicializar (Startup)", "caminho": caminho_completo,
                        "tipo": "FOLDER_DISABLED", "file_path": caminho_completo
                    })

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
            text=f"📊 Total: {len(lista)} itens  |  🟢 Ativos: {ativos}  |  🔴 Desativados/Bloqueados: {desativados}"
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

    # --- RECURSO 1: ADICIONAR PARA INICIALIZAR COM O WINDOWS ---
    def adicionar_programa(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o Executável para Iniciar com o Windows",
            filetypes=[("Executáveis (*.exe)", "*.exe"), ("Atalhos (*.lnk)", "*.lnk"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho:
            return

        nome_padrao = os.path.splitext(os.path.basename(caminho))[0].capitalize()

        # Janela popup para nome
        janela = tk.Toplevel(self.root)
        janela.title("Permitir Inicialização")
        janela.geometry("360x160")
        janela.configure(bg="#1e1e2e")
        janela.transient(self.root)
        janela.grab_set()

        tk.Label(janela, text="Nome de Exibição do Programa:", fg="#cdd6f4", bg="#1e1e2e", font=("Segoe UI", 9, "bold")).pack(pady=(12, 5))
        entry = tk.Entry(janela, bg="#313244", fg="#cdd6f4", insertbackground="white", width=35, font=("Segoe UI", 10))
        entry.insert(0, nome_padrao)
        entry.pack(pady=5)

        def salvar():
            nome = entry.get().strip()
            if not nome:
                return
            try:
                # Salva no Registro do Usuário Atual (HKCU)
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, nome, 0, winreg.REG_SZ, f'"{caminho}"')

                messagebox.showinfo("Sucesso", f"'{nome}' foi adicionado para iniciar junto com o Windows!")
                janela.destroy()
                self.carregar_programas()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível adicionar ao registro:\n{e}")

        tk.Button(janela, text="✔ Adicionar ao Windows", bg="#a6e3a1", fg="#11111b", relief="flat", font=("Segoe UI", 9, "bold"), padx=10, command=salvar).pack(pady=12)

    # --- RECURSO 2: BLOQUEAR/IMPEDIR UM EXECUTÁVEL DIRETO ---
    def bloquear_executavel_direto(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um programa para IMPEDIR de abrir com o Windows",
            filetypes=[("Executáveis (*.exe)", "*.exe"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho:
            return

        nome = os.path.splitext(os.path.basename(caminho))[0].capitalize()

        try:
            # Adiciona direto na chave de desativados do aplicativo
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, DISABLED_REG_SUBKEY) as k_dest:
                winreg.SetValueEx(k_dest, nome, 0, winreg.REG_SZ, f"Bloqueio Manual|{caminho}")

            messagebox.showinfo("Programa Bloqueado", f"'{nome}' foi adicionado à lista de inicialização bloqueada.\nEle NÃO abrirá com o Windows.")
            self.carregar_programas()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao bloquear programa:\n{e}")

    # --- ALTERNAR STATUS (ATIVAR / DESATIVAR SELECIONADO) ---
    def alternar_status(self):
        item_sel = self.tree.selection()
        if not item_sel:
            messagebox.showwarning("Aviso", "Selecione um item na lista primeiro.")
            return

        nome = self.tree.item(item_sel[0], "values")[2]
        item_dado = next((d for d in self.dados_completos if d["nome"] == nome), None)
        if not item_dado:
            return

        try:
            # A) Se for do REGISTRO
            if "REGISTRY" in item_dado["tipo"]:
                if item_dado["status"] == "ATIVO":
                    # Desativar: Remove do local original -> Salva na chave "Disabled"
                    with winreg.OpenKey(item_dado["hkey"], item_dado["subkey"], 0, winreg.KEY_SET_VALUE) as k_orig:
                        winreg.DeleteValue(k_orig, item_dado["nome"])

                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, DISABLED_REG_SUBKEY) as k_dest:
                        winreg.SetValueEx(k_dest, item_dado["nome"], 0, winreg.REG_SZ, f"{item_dado['local']}|{item_dado['caminho']}")
                else:
                    # Reativar: Remove da chave "Disabled" -> Devolve para HKCU Run
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_REG_SUBKEY, 0, winreg.KEY_SET_VALUE) as k_dis:
                        winreg.DeleteValue(k_dis, item_dado["nome"])

                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k_run:
                        winreg.SetValueEx(k_run, item_dado["nome"], 0, winreg.REG_SZ, item_dado["caminho"])

            # B) Se for da PASTA INICIALIZAR
            elif "FOLDER" in item_dado["tipo"]:
                if item_dado["status"] == "ATIVO":
                    dest = os.path.join(USER_STARTUP_DISABLED_DIR, os.path.basename(item_dado["file_path"]))
                    shutil.move(item_dado["file_path"], dest)
                else:
                    dest = os.path.join(USER_STARTUP_DIR, os.path.basename(item_dado["file_path"]))
                    shutil.move(item_dado["file_path"], dest)

            self.carregar_programas()
        except PermissionError:
            messagebox.showerror("Erro de Permissão", "Execute o programa como ADMINISTRADOR para alterar este item.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao alternar status:\n{e}")

    # --- REMOVER DEFINITIVAMENTE ---
    def excluir_registro(self):
        item_sel = self.tree.selection()
        if not item_sel:
            messagebox.showwarning("Aviso", "Selecione um item para remover.")
            return

        nome = self.tree.item(item_sel[0], "values")[2]
        item_dado = next((d for d in self.dados_completos if d["nome"] == nome), None)
        if not item_dado:
            return

        if not messagebox.askyesno("Confirmar Remoção", f"Deseja remover permanentemente '{nome}' do gerenciador?"):
            return

        try:
            if "REGISTRY" in item_dado["tipo"]:
                with winreg.OpenKey(item_dado["hkey"], item_dado["subkey"], 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, item_dado["nome"])
            elif "FOLDER" in item_dado["tipo"]:
                if os.path.exists(item_dado["file_path"]):
                    os.remove(item_dado["file_path"])

            self.carregar_programas()
        except PermissionError:
            messagebox.showerror("Acesso Negado", "Execute como Administrador.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível remover:\n{e}")


if __name__ == "__main__":
    app_root = tk.Tk()
    app = AdvancedSystemCareStartupManager(app_root)
    app_root.mainloop()
