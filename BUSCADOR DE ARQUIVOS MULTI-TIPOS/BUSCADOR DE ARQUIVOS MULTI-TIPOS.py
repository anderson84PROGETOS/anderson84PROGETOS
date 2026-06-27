import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from datetime import datetime

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {units[index]}"


class FileFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("BUSCADOR DE ARQUIVOS MULTI-TIPOS")
        self.root.geometry("1450x780")
        self.root.state("zoomed")
        self.root.minsize(1150, 650)
        self.root.configure(bg="#000000")

        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_type = tk.StringVar(value="Tudo")
        
        self.extensions = ['.txt', '.pdf', '.docx', '.jpg', '.png', '.mp4', '.xlsx', '.zip', '.rar']

        self.all_items = []
        self.copy_all_btn = None

        # Variáveis para seleção com mouse
        self.drag_start = None
        self.current_selection = set()

        self.create_widgets()

    def create_widgets(self):
        # ================= TOP BAR =================
        top_frame = tk.Frame(self.root, bg="#000000", width=15300, height=50)
        top_frame.pack(padx=(0, 1), pady=10)
        top_frame.pack_propagate(False)

        tk.Label(top_frame, text="Pasta:", bg="#000000", fg="#00ff00", font=("Consolas", 10)).pack(side="left")
        tk.Entry(top_frame, textvariable=self.path_var, font=("Consolas", 10), 
                 bg="#111111", fg="#00ff00", insertbackground="#00ff00", width=55).pack(side="left", padx=(5, 10), fill="x", expand=True)

        tk.Button(top_frame, text="Selecionar Pasta", command=self.select_folder,
                  width=16, bg="#006600", fg="#ffffff", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        tk.Button(top_frame, text="Analisar", command=self.start_scan,
                  width=14, bg="#00cc00", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        # Filtro
        tk.Label(top_frame, text="Filtro:", bg="#000000", fg="#00ff00", font=("Consolas", 10)).pack(side="left", padx=(15, 5))
        filter_values = ["Tudo", "Arquivos", "Pastas"] + [ext.upper() for ext in self.extensions]
        self.filter_combo = ttk.Combobox(top_frame, textvariable=self.filter_type, 
                                        values=filter_values, state="readonly", width=14, font=("Consolas", 10))
        self.filter_combo.pack(side="left", padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # Botões de Copiar
        self.copy_all_btn = tk.Button(top_frame, text="Copiar Tudo", 
                                     command=self.copy_everything, width=12, bg="#ff00ff", fg="#000000", 
                                     font=("Consolas", 10, "bold"))
        self.copy_all_btn.pack(side="left", padx=5)

        tk.Button(top_frame, text="Copiar Arquivos", command=self.copy_all,
                  width=15, bg="#ff8800", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        tk.Button(top_frame, text="Copiar Selecionado", command=self.copy_selected,
                  width=22, bg="#ff5500", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # Search
        search_frame = tk.Frame(self.root, bg="#000000")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="🔍 Pesquisar:", font=("Consolas", 10), bg="#000000", fg="#00ff00").pack(side="left")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Consolas", 10), 
                                    bg="#111111", fg="#00ff00", insertbackground="#00ff00", width=80)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(search_frame, text="Buscar", command=self.filter_items,
                  bg="#00cc00", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        # Status
        self.status_var = tk.StringVar(value=f"Extensões suportadas: {', '.join(self.extensions)}")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                                   bg="#000000", fg="#00ff00", font=("Consolas", 9), padx=10)
        self.status_bar.pack(fill="x", padx=10, pady=5)

        # ================= TREEVIEW =================
        table_frame = tk.Frame(self.root, bg="#000000")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("nome", "tipo", "tamanho", "data", "horas", "caminho")
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background="#000000", foreground="#00ff00", fieldbackground="#000000", rowheight=28, font=("Consolas", 10))
        style.map("Treeview", background=[('selected', '#003300')], foreground=[('selected', '#ffffff')])
        style.configure("Treeview.Heading", background="#001100", foreground="#00ff00", font=("Consolas", 10, "bold"))

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")

        for col, text in zip(columns, ["Nome", "Tipo", "Tamanho", "Data", "Hora", "Caminho Completo"]):
            self.tree.heading(col, text=text)

        self.tree.column("nome", width=480)
        self.tree.column("tipo", width=90)
        self.tree.column("tamanho", width=110)
        self.tree.column("data", width=110)
        self.tree.column("horas", width=100)
        self.tree.column("caminho", width=500)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ================= SELEÇÃO COM MOUSE (DRAG) =================
        self.tree.bind("<ButtonPress-1>", self.on_mouse_press)
        self.tree.bind("<B1-Motion>", self.on_mouse_drag)
        self.tree.bind("<ButtonRelease-1>", self.on_mouse_release)

        # Menu e outros binds
        self.menu = tk.Menu(self.root, tearoff=0, bg="#000000", fg="#00ff00")
        self.menu.add_command(label="Abrir", command=self.open_item)
        self.menu.add_command(label="Abrir Pasta", command=self.open_file_folder)
        self.menu.add_separator()
        self.menu.add_command(label="🗑️ Excluir Selecionados", command=self.delete_selected, foreground="#ff4444")

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_item())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Control-a>", self.select_all)
        self.tree.bind("<Control-A>", self.select_all)

        # Roda Pé INSTRUÇÕES DE USO
        footer = tk.Label(
            self.root,
            text="""📖 INSTRUÇÕES DE USO

• Selecione uma Pasta → Clique em 'Analisar'
• Filtro: Tudo | Arquivos | Pastas | .PDF | .JPG | .MP4 ...
• Arraste o mouse (botão esquerdo) para selecionar vários itens de uma vez
• Duplo clique → Abrir item
• Botão Direito → Abrir / Abrir Pasta / Excluir
• Ctrl + A → Selecionar Todos
• Ctrl + Clique → Seleção múltipla
• Delete → Excluir arquivos selecionados""",

            bg="#111111",
            fg="#05fdf1",
            font=("Consolas", 11, "bold"),
            justify="left",
            anchor="w",
            padx=10,
            pady=20
        )

        footer.pack(side="bottom", fill="x")
        
    # ================= FUNÇÕES DE SELEÇÃO COM MOUSE =================
    def on_mouse_press(self, event):
        self.drag_start = self.tree.identify_row(event.y)
        if not self.drag_start:
            self.tree.selection_clear()
        self.current_selection = set(self.tree.selection())

    def on_mouse_drag(self, event):
        current_row = self.tree.identify_row(event.y)
        if current_row and self.drag_start:
            # Selecionar intervalo entre drag_start e current_row
            all_rows = self.tree.get_children()
            try:
                start_idx = all_rows.index(self.drag_start)
                end_idx = all_rows.index(current_row)
                if start_idx > end_idx:
                    start_idx, end_idx = end_idx, start_idx
                selected = all_rows[start_idx:end_idx+1]
                self.tree.selection_set(selected)
            except:
                pass

    def on_mouse_release(self, event):
        self.drag_start = None

    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

    # ================= RESTO DO CÓDIGO (mesmo de antes) =================
    def on_filter_change(self, event=None):
        if self.filter_type.get() == "Tudo":
            self.copy_all_btn.pack(side="left", padx=5)
        else:
            self.copy_all_btn.pack_forget()
        self.filter_items()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def start_scan(self):
        folder = self.path_var.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("Aviso", "Selecione uma pasta válida!")
            return

        self.tree.delete(*self.tree.get_children())
        self.progress["value"] = 0
        self.status_var.set("Escaneando...")

        Thread(target=self.scan_items, args=(folder,), daemon=True).start()

    def scan_items(self, root_folder):
        items = []
        for raiz, pastas, arquivos in os.walk(root_folder):
            for pasta in pastas:
                caminho = os.path.join(raiz, pasta)
                try:
                    dt = datetime.fromtimestamp(os.path.getmtime(caminho))
                    items.append({"nome": pasta, "tipo": "Pasta", "tamanho": 0, "data": dt.strftime("%d/%m/%Y"),
                                  "horas": dt.strftime("%H:%M:%S"), "caminho": caminho, "ext": ""})
                except: pass

            for arq in arquivos:
                ext = os.path.splitext(arq)[1].lower()
                if ext in self.extensions:
                    caminho = os.path.join(raiz, arq)
                    try:
                        tamanho = os.path.getsize(caminho)
                        dt = datetime.fromtimestamp(os.path.getmtime(caminho))
                        items.append({"nome": arq, "tipo": "Arquivo", "tamanho": tamanho,
                                      "data": dt.strftime("%d/%m/%Y"), "horas": dt.strftime("%H:%M:%S"),
                                      "caminho": caminho, "ext": ext})
                    except: pass

        items.sort(key=lambda x: (x["tipo"] == "Pasta", -x["tamanho"]))
        self.all_items = items
        self.root.after(0, self.populate_tree, items)

    def populate_tree(self, items):
        self.progress["value"] = 100
        self.tree.delete(*self.tree.get_children())

        total_size = sum(item.get("tamanho", 0) for item in items)

        for item in items:
            tamanho_str = "Pasta" if item["tipo"] == "Pasta" else format_size(item["tamanho"])
            self.tree.insert("", "end", values=(item["nome"], item["tipo"], tamanho_str, item["data"], item["horas"], item["caminho"]))

        self.status_var.set(f"{len(items)} itens | Total: {format_size(total_size)}")

    def filter_items(self):
        search_term = self.search_var.get().strip().lower()
        filtro = self.filter_type.get()

        self.tree.delete(*self.tree.get_children())
        filtered = []

        for item in self.all_items:
            match_search = not search_term or search_term in item["nome"].lower() or search_term in item["caminho"].lower()
            if filtro == "Tudo":
                match_filter = True
            elif filtro == "Arquivos":
                match_filter = item["tipo"] == "Arquivo"
            elif filtro == "Pastas":
                match_filter = item["tipo"] == "Pasta"
            else:
                match_filter = item.get("ext", "").lower() == filtro.lower()
            if match_search and match_filter:
                filtered.append(item)

        total_size = sum(item.get("tamanho", 0) for item in filtered)

        for item in filtered:
            tamanho_str = "Pasta" if item["tipo"] == "Pasta" else format_size(item["tamanho"])
            self.tree.insert("", "end", values=(item["nome"], item["tipo"], tamanho_str, item["data"], item["horas"], item["caminho"]))

        self.status_var.set(f"{len(filtered)} itens | Total: {format_size(total_size)}")

    def copy_everything(self):
        destino = filedialog.askdirectory(title="Escolha a pasta de DESTINO")
        if not destino: return

        copiados = 0
        for item in self.all_items:
            try:
                if item["tipo"] == "Pasta":
                    dest_folder = os.path.join(destino, item["nome"])
                    shutil.copytree(item["caminho"], dest_folder, dirs_exist_ok=True)
                else:
                    dest_file = os.path.join(destino, item["nome"])
                    contador = 1
                    while os.path.exists(dest_file):
                        nome, ext = os.path.splitext(item["nome"])
                        dest_file = os.path.join(destino, f"{nome}_{contador}{ext}")
                        contador += 1
                    shutil.copy2(item["caminho"], dest_file)
                copiados += 1
            except: pass

        messagebox.showinfo("Sucesso", f"{copiados} itens copiados!")   

    def copy_all(self):
        arquivos = [item for item in self.all_items if item["tipo"] == "Arquivo"]
        self._copy_files(arquivos)

    def copy_selected(self):
        files = []
        for iid in self.tree.selection():
            values = self.tree.item(iid)["values"]
            if values[1] == "Arquivo":
                files.append({"nome": values[0], "caminho": values[5]})
        self._copy_files(files)

    def _copy_files(self, files_list):
        if not files_list:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
            return
        destino = filedialog.askdirectory(title="Pasta de Destino")
        if not destino: return
        copiados = 0
        for file in files_list:
            try:
                dest = os.path.join(destino, file["nome"])
                c = 1
                while os.path.exists(dest):
                    nome, ext = os.path.splitext(file["nome"])
                    dest = os.path.join(destino, f"{nome}_{c}{ext}")
                    c += 1
                shutil.copy2(file["caminho"], dest)
                copiados += 1
            except: pass
        messagebox.showinfo("Sucesso", f"{copiados} arquivo(s) copiado(s)!")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        to_delete = [self.tree.item(i)["values"][5] for i in selected if self.tree.item(i)["values"][1] == "Arquivo"]
        if to_delete and messagebox.askyesno("Excluir", f"Apagar {len(to_delete)} arquivo(s)?", icon="warning"):
            for path in to_delete:
                try:
                    if os.path.exists(path): os.remove(path)
                except: pass
            self.all_items = [item for item in self.all_items if item["caminho"] not in to_delete]
            self.filter_items()

    def open_item(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][5]
            try:
                os.startfile(path) if os.name == "nt" else os.system(f'xdg-open "{path}"')
            except:
                messagebox.showerror("Erro", "Não foi possível abrir.")

    def open_file_folder(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][5]
            try:
                folder = os.path.dirname(path)
                os.startfile(folder) if os.name == "nt" else os.system(f'xdg-open "{folder}"')
            except: pass

    def show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileFinder(root)
    root.mainloop() 
