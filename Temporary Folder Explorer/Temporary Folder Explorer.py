import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import tempfile
from pathlib import Path
from datetime import datetime
import platform
import hashlib
import webbrowser
import string

class TempExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Temporary Folder Explorer 📁")

        sistema = platform.system()

        if sistema == "Windows":
            self.root.state("zoomed")  # Maximiza no Windows
        else:
            # Funciona na maioria dos ambientes Linux (GNOME, KDE, XFCE...)
            self.root.attributes("-zoomed", True)

        self.root.minsize(1000, 550)

        # === Barra de data e hora ===
        self.datetime_var = tk.StringVar()
        top_info = ttk.Frame(root, padding=(10, 8))
        top_info.pack(fill=tk.X)

        ttk.Label(top_info, text="Data e Hora:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.lbl_datetime = ttk.Label(top_info, textvariable=self.datetime_var, font=("Segoe UI", 11))
        self.lbl_datetime.pack(side=tk.LEFT, padx=8)

        ttk.Button(top_info, text="Atualizar Tudo", command=self.refresh).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_info, text="Selecionar Pasta...", command=self.select_folder).pack(side=tk.RIGHT, padx=5)

        self.update_datetime()

        # === Botões de ação ===
        btn_frame = ttk.Frame(root, padding=(10, 0, 10, 5))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Calcular SHA-256", command=self.calc_sha256).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Ver Strings", command=self.show_strings).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Abrir no VirusTotal", command=self.open_virustotal).pack(side=tk.LEFT, padx=3)

        self.hash_var = tk.StringVar(value="Hash: (selecione um arquivo)")
        ttk.Label(btn_frame, textvariable=self.hash_var, font=("Consolas", 9)).pack(side=tk.LEFT, padx=15)

        # === Treeview ===
        tree_frame = ttk.Frame(root, padding=(10, 5, 10, 10))
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("size", "type", "modified", "path"),
            show="tree headings",
            selectmode="browse"
        )

        self.tree.heading("#0", text="Nome / Pasta", anchor=tk.W)
        self.tree.heading("size", text="Tamanho", anchor=tk.E)
        self.tree.heading("type", text="Tipo", anchor=tk.W)
        self.tree.heading("modified", text="Modificado", anchor=tk.W)
        self.tree.heading("path", text="Caminho Completo", anchor=tk.W)

        self.tree.column("#0", width=700, minwidth=180)
        self.tree.column("size", width=100, minwidth=80, anchor=tk.E)
        self.tree.column("type", width=90, minwidth=70)
        self.tree.column("modified", width=130, minwidth=110)
        self.tree.column("path", width=2000, minwidth=200)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # === Menu de botão direito ===
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Abrir caminho", command=self.open_path)
        self.context_menu.add_command(label="Abrir arquivo", command=self.open_file)

        self.tree.bind("<Button-3>", self.show_context_menu)  # Botão direito

        # Status
        self.status = ttk.Label(root, text="Pronto", relief=tk.SUNKEN, anchor=tk.W, padding=6)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        # Eventos
        self.tree.bind("<<TreeviewOpen>>", self.on_open)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.current_hash = None
        self.current_path = None
        self.custom_folder = None

        self.refresh()

    def update_datetime(self):
        now = datetime.now()
        self.datetime_var.set(now.strftime("%d/%m/%Y  %H:%M:%S"))
        self.root.after(1000, self.update_datetime)

    def show_context_menu(self, event):
        """Mostra o menu ao clicar com o botão direito"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.on_select(None)  # Atualiza current_path

            # Atualiza o menu conforme o tipo
            self.context_menu.delete(0, tk.END)
            self.context_menu.add_command(label="🔍  Abrir Caminho", command=self.open_path)

            # Linha separadora
            self.context_menu.add_separator()

            if self.current_path and self.current_path.is_file():
                self.context_menu.add_command(label="🔍  Abrir Arquivo", command=self.open_file)

            self.context_menu.post(event.x_root, event.y_root)

    def open_path(self):
        """Abre a pasta do item no Explorer"""
        if not self.current_path:
            return
        try:
            path = self.current_path
            if path.is_file():
                # Abre a pasta e seleciona o arquivo
                if platform.system() == "Windows":
                    os.system(f'explorer /select,"{path}"')
                else:
                    os.system(f'xdg-open "{path.parent}"')
            else:
                # Abre a própria pasta
                if platform.system() == "Windows":
                    os.startfile(path)
                else:
                    os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o caminho:\n{e}")

    def open_file(self):
        """Abre o arquivo"""
        if not self.current_path or not self.current_path.is_file():
            return
        try:
            if platform.system() == "Windows":
                os.startfile(self.current_path)
            else:
                os.system(f'xdg-open "{self.current_path}"')
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Selecione uma pasta para explorar")
        if folder:
            self.custom_folder = Path(folder)
            self.load_custom_folder()

    def load_custom_folder(self):
        if not self.custom_folder or not self.custom_folder.exists():
            return

        self.tree.delete(*self.tree.get_children())
        self.current_hash = None
        self.current_path = None
        self.hash_var.set("Hash: (selecione um arquivo)")

        root_id = self.tree.insert(
            "", "end",
            text=str(self.custom_folder),
            values=("", "Pasta Selecionada", self.get_modified(self.custom_folder), str(self.custom_folder)),
            open=True
        )
        self.tree.item(root_id, tags=(str(self.custom_folder),))
        self.load_directory(root_id, self.custom_folder)

        self.status.config(text=f"Pasta selecionada: {self.custom_folder}")

    def find_temp_folders(self):
        candidates = []
        try:
            candidates.append(Path(tempfile.gettempdir()))
        except Exception:
            pass

        if platform.system() == "Windows":
            user = os.environ.get("USERNAME", "")
            drive = os.environ.get("SystemDrive", "C:")

            windows_temps = [
                Path(f"{drive}\\Windows\\Temp"),
                Path(f"{drive}\\Temp"),
                Path(f"{drive}\\Users\\{user}\\AppData\\Local\\Temp"),
                Path(f"{drive}\\Users\\{user}\\AppData\\Local\\Microsoft\\Windows\\INetCache"),
                Path(f"{drive}\\Users\\{user}\\AppData\\Local\\Temp\\Low"),
                Path(f"{drive}\\Program Files\\Temp"),
                Path(f"{drive}\\Program Files (x86)\\Temp"),
                Path(f"{drive}\\Users\\Public\\Temp"),
                Path(f"{drive}\\Users\\{user}\\AppData\\Local\\CrashDumps"),
                Path(f"{drive}\\Windows\\Prefetch"),
            ]
            candidates.extend(windows_temps)

            for var in ["TEMP", "TMP", "TMPDIR"]:
                val = os.environ.get(var)
                if val:
                    candidates.append(Path(val))
        else:
            linux_temps = [
                Path("/tmp"),
                Path("/var/tmp"),
                Path("/var/cache"),
                Path.home() / ".cache",
            ]
            candidates.extend(linux_temps)

        unique = []
        seen = set()
        for p in candidates:
            try:
                resolved = p.resolve()
                if resolved.exists() and resolved.is_dir() and str(resolved) not in seen:
                    seen.add(str(resolved))
                    unique.append(resolved)
            except Exception:
                continue
        return unique

    def format_size(self, size_bytes):
        if size_bytes is None:
            return ""
        try:
            size = float(size_bytes)
            if size >= 1024 ** 3:
                return f"{size / (1024 ** 3):.2f} GB"
            elif size >= 1024 ** 2:
                return f"{size / (1024 ** 2):.2f} MB"
            elif size >= 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{int(size)} B"
        except Exception:
            return ""

    def get_modified(self, path: Path):
        try:
            ts = path.stat().st_mtime
            return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            return ""

    def get_item_type(self, path: Path):
        if path.is_dir():
            return "Pasta"
        if path.is_file():
            return "Arquivo"
        if path.is_symlink():
            return "Atalho"
        return "Outro"

    def get_size(self, path: Path):
        try:
            if path.is_file():
                return path.stat().st_size
        except Exception:
            pass
        return 0

    def insert_item(self, parent, path: Path):
        try:
            name = path.name if path.name else str(path)
            size = self.get_size(path)

            item_id = self.tree.insert(
                parent, "end",
                text=name,
                values=(
                    self.format_size(size) if path.is_file() else "",
                    self.get_item_type(path),
                    self.get_modified(path),
                    str(path)
                ),
                open=False
            )

            if path.is_dir():
                self.tree.insert(item_id, "end", text="Carregando...")
                self.tree.item(item_id, tags=(str(path),))
            else:
                self.tree.item(item_id, tags=(str(path),))

            return item_id
        except PermissionError:
            self.tree.insert(parent, "end", text=f"[Sem permissão] {path.name}",
                             values=("", "Erro", "", ""))
        except Exception:
            self.tree.insert(parent, "end", text=f"[Erro] {path.name}",
                             values=("", "Erro", "", ""))

    def load_directory(self, parent, directory: Path):
        try:
            entries = list(directory.iterdir())

            folders = []
            files = []

            for entry in entries:
                try:
                    if entry.is_dir():
                        folders.append(entry)
                    else:
                        files.append(entry)
                except Exception:
                    continue

            folders.sort(key=lambda p: p.name.lower())

            def file_sort_key(p):
                size = self.get_size(p)
                if size == 0:
                    return (1, 0, p.name.lower())
                else:
                    return (0, -size, p.name.lower())

            files.sort(key=file_sort_key)

            for entry in folders + files:
                self.insert_item(parent, entry)

        except PermissionError:
            self.tree.insert(parent, "end", text="[Sem permissão para listar]", values=("", "Erro", "", ""))
        except Exception as e:
            self.tree.insert(parent, "end", text=f"[Erro: {e}]", values=("", "Erro", "", ""))

    def refresh(self):
        self.custom_folder = None
        self.tree.delete(*self.tree.get_children())
        self.temp_dirs = self.find_temp_folders()
        self.current_hash = None
        self.current_path = None
        self.hash_var.set("Hash: (selecione um arquivo)")

        if not self.temp_dirs:
            self.status.config(text="Nenhuma pasta Temp encontrada")
            messagebox.showwarning("Aviso", "Nenhuma pasta Temp foi encontrada neste computador.")
            return

        self.status.config(text=f"Carregando {len(self.temp_dirs)} pasta(s) Temp...")
        self.root.update_idletasks()

        for temp_dir in self.temp_dirs:
            root_id = self.tree.insert(
                "", "end",
                text=str(temp_dir),
                values=("", "Pasta Temp", self.get_modified(temp_dir), str(temp_dir)),
                open=False
            )
            self.tree.item(root_id, tags=(str(temp_dir),))
            self.tree.insert(root_id, "end", text="Carregando...")

        self.status.config(
            text=f"Encontradas {len(self.temp_dirs)} pasta(s) Temp  |  "
                 f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

    def on_open(self, event):
        item = self.tree.focus()
        if not item:
            return
        children = self.tree.get_children(item)
        if children and self.tree.item(children[0], "text") == "Carregando...":
            self.tree.delete(children[0])
            tags = self.tree.item(item, "tags")
            if tags:
                path = Path(tags[0])
                self.load_directory(item, path)

    def on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        tags = self.tree.item(item, "tags")
        if not tags:
            return
        path = Path(tags[0])
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir:\n{e}")

    def on_select(self, event):
        item = self.tree.focus()
        if not item:
            return
        tags = self.tree.item(item, "tags")
        if tags:
            self.current_path = Path(tags[0])
            self.current_hash = None
            self.hash_var.set("Hash: (clique em Calcular SHA-256)")
        else:
            self.current_path = None
            self.hash_var.set("Hash: (selecione um arquivo)")

    def calc_sha256(self):
        if not self.current_path or not self.current_path.is_file():
            messagebox.showwarning("Aviso", "Selecione um arquivo válido primeiro.")
            return
        try:
            self.status.config(text="Calculando SHA-256... aguarde...")
            self.root.update_idletasks()

            sha256 = hashlib.sha256()
            with open(self.current_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            self.current_hash = sha256.hexdigest()
            self.hash_var.set(f"SHA-256: {self.current_hash}")
            self.status.config(text=f"Hash calculado com sucesso | {self.current_path.name}")

        except PermissionError:
            messagebox.showerror("Erro", "Sem permissão para ler este arquivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao calcular hash:\n{e}")
            self.status.config(text="Erro ao calcular hash")

    # strings
    def show_strings(self):
        if not self.current_path or not self.current_path.is_file():
            messagebox.showwarning("Aviso", "Selecione um arquivo válido primeiro.")
            return
        try:
            self.status.config(text="Extraindo strings... aguarde...")
            self.root.update_idletasks()

            max_bytes = 20 * 1024 * 1024
            data = self.current_path.read_bytes()[:max_bytes]

            result = []
            current = []
            printable = set(string.printable)

            for byte in data:
                char = chr(byte)
                if char in printable and char not in "\t\r\n\x0b\x0c":
                    current.append(char)
                else:
                    if len(current) >= 4:
                        result.append("".join(current))
                    current = []
            if len(current) >= 4:
                result.append("".join(current))

            # ===== Janela =====
            win = tk.Toplevel(self.root)
            win.title(f"Strings - {self.current_path.name}")
            win.geometry("1000x700")
            win.minsize(700, 400)

            # --- Barra de pesquisa ---
            search_frame = ttk.Frame(win, padding=(8, 8, 8, 4))
            search_frame.pack(fill=tk.X)

            ttk.Label(search_frame, text="Pesquisar:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

            search_var = tk.StringVar()
            entry = ttk.Entry(search_frame, textvariable=search_var, font=("Consolas", 11), width=50)
            entry.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
            entry.focus()

            def filtrar(*args):
                termo = search_var.get().strip()
                termo_lower = termo.lower()

                txt.config(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                txt.tag_remove("highlight", "1.0", tk.END)

                if not termo:
                    if result:
                        txt.insert(tk.END, "\n".join(result))
                    else:
                        txt.insert(tk.END, "(Nenhuma string legível encontrada)")
                    status_label.config(text=f"Total: {len(result)} strings")
                else:
                    filtradas = [s for s in result if termo_lower in s.lower()]
                    if filtradas:
                        txt.insert(tk.END, "\n".join(filtradas))

                        # Destaca o termo em vermelho (mais confiável)
                        start = "1.0"
                        while True:
                            pos = txt.search(termo, start, stopindex=tk.END, nocase=True)
                            if not pos:
                                break
                            end = f"{pos}+{len(termo)}c"
                            txt.tag_add("highlight", pos, end)
                            start = end
                    else:
                        txt.insert(tk.END, f"(Nenhuma string contém: \"{termo}\")")

                    status_label.config(text=f"Mostrando {len(filtradas)} de {len(result)} strings")

                # Cor vermelha + negrito
                txt.tag_config("highlight", foreground="#FF1A1A", font=("Consolas", 10, "bold"))

                txt.config(state=tk.DISABLED)

            def salvar():
                conteudo = txt.get("1.0", tk.END).strip()
                if not conteudo or conteudo.startswith("("):
                    messagebox.showwarning("Aviso", "Nada para salvar.")
                    return

                nome_padrao = f"strings_{self.current_path.stem}"
                if search_var.get().strip():
                    nome_padrao += "_filtro"

                caminho = filedialog.asksaveasfilename(
                    title="Salvar strings filtradas",
                    defaultextension=".txt",
                    initialfile=nome_padrao + ".txt",
                    filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
                )

                if caminho:
                    try:
                        with open(caminho, "w", encoding="utf-8") as f:
                            f.write(conteudo)
                        messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n\n{caminho}")
                        self.status.config(text=f"Strings salvas: {caminho}")
                    except Exception as e:
                        messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

            ttk.Button(search_frame, text="🔍 Pesquisar", command=filtrar).pack(side=tk.LEFT, padx=4)
            ttk.Button(search_frame, text="💾 Salvar", command=salvar).pack(side=tk.LEFT, padx=2)
            ttk.Button(search_frame, text="Limpar", command=lambda: (search_var.set(""), filtrar())).pack(side=tk.LEFT, padx=2)
            
            entry.bind("<Return>", filtrar)
            search_var.trace_add("write", filtrar)

            # --- Área de texto ---
            txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10))
            txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

            status_label = ttk.Label(win, text="", anchor=tk.W, padding=(8, 4))
            status_label.pack(fill=tk.X, side=tk.BOTTOM)

            filtrar()

            self.status.config(text=f"Strings extraídas: {len(result)} | {self.current_path.name}")

        except PermissionError:
            messagebox.showerror("Erro", "Sem permissão para ler este arquivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao extrair strings:\n{e}")
            self.status.config(text="Erro ao extrair strings")
            
    # abrir o virus total
    def open_virustotal(self):
        if not self.current_path or not self.current_path.is_file():
            messagebox.showwarning("Aviso", "Selecione um arquivo válido primeiro.")
            return

        if not self.current_hash:
            self.calc_sha256()
            if not self.current_hash:
                return

        url = f"https://www.virustotal.com/gui/file/{self.current_hash}"
        webbrowser.open(url)
        self.status.config(text=f"Abrindo VirusTotal: {self.current_hash[:16]}...")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass

    app = TempExplorer(root)
    root.mainloop()
