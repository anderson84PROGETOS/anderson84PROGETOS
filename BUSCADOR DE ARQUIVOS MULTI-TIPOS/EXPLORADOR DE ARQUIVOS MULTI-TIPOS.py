import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from datetime import datetime
from pathlib import Path


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


def get_file_type(item_name, is_file):
    if not is_file:
        return "Pasta"
    ext = os.path.splitext(item_name)[1].upper().strip()
    if ext:
        return ext[1:] if ext.startswith('.') else ext
    return "SEM EXT"


class FileFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("🏅 EXPLORADOR DE ARQUIVOS MULTI-TIPOS")
        self.root.geometry("1450x780")
        self.root.state("zoomed")
        self.root.minsize(1150, 650)
        self.root.configure(bg="#000000")

        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_type = tk.StringVar(value="Tudo")
        
        self.extensions = ['.txt', '.pdf', '.docx', '.jpg', '.png', '.mp4', '.xlsx', '.zip', '.rar']

        self.all_items = []
        self.create_widgets()

    def create_widgets(self):
        # ================= TOP BAR =================
        top_frame = tk.Frame(self.root, bg="#000000", height=50)
        top_frame.pack(padx=10, pady=10, fill="x")
        top_frame.pack_propagate(False)

        tk.Label(top_frame, text="Pasta:", bg="#000000", fg="#00ff00", font=("Consolas", 10)).pack(side="left")
        tk.Entry(top_frame, textvariable=self.path_var, font=("Consolas", 10), 
                 bg="#111111", fg="#00ff00", insertbackground="#00ff00").pack(side="left", padx=(5, 10), fill="x", expand=True)

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

        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        search_frame = tk.Frame(self.root, bg="#000000")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="🔍 Pesquisar:", font=("Consolas", 10), bg="#000000", fg="#00ff00").pack(side="left")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Consolas", 10), 
                                    bg="#111111", fg="#00ff00", insertbackground="#00ff00")
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(search_frame, text="Buscar", command=self.filter_items,
                  bg="#00cc00", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        self.status_var = tk.StringVar(value="Pronto")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                                   bg="#000000", fg="#00ff00", font=("Consolas", 9), padx=10, pady=6)
        self.status_bar.pack(fill="x", padx=10, pady=5)

        # Treeview
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

        self.tree.column("nome", width=700)
        self.tree.column("tipo", width=110)
        self.tree.column("tamanho", width=130)
        self.tree.column("data", width=110)
        self.tree.column("horas", width=100)
        self.tree.column("caminho", width=1000)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Binds
        self.tree.bind("<ButtonPress-1>", self.on_mouse_press)
        self.tree.bind("<B1-Motion>", self.on_mouse_drag)
        self.tree.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_item())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Control-a>", self.select_all)

        # Footer
        footer = tk.Label(self.root, text="""📖 GUIA RÁPIDO DE UTILIZAÇÃO

• Selecione a pasta desejada e clique em Analisar para iniciar a varredura.
• Utilize os filtros para localizar Todos, Arquivos, Pastas ou extensões específicas, como PDF, JPG, TXT, entre outras.
• Para selecionar vários itens, mantenha o botão esquerdo do mouse pressionado e arraste sobre os arquivos ou pastas desejados.
• Dê um duplo clique em um item para abri-lo.
• Pressione a tecla Delete para excluir os arquivos ou pastas selecionados.
• Utilize o botão direito do mouse para acessar opções adicionais, como Abrir, Abrir Pasta, Copiar e Excluir.""",
                          bg="#111111", fg="#05fdf1", font=("Consolas", 10), justify="left", anchor="w", padx=10, pady=15)
        footer.pack(side="bottom", fill="x")

    # ================= DELEÇÃO MELHORADA =================
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        items = []
        for iid in selected:
            values = self.tree.item(iid)["values"]
            if values:
                items.append({
                    "nome": values[0],
                    "tipo": values[1],
                    "caminho": values[5]
                })

        if not items:
            return

        pastas = [item for item in items if item["tipo"] == "Pasta"]
        arquivos = [item for item in items if item["tipo"] != "Pasta"]

        if pastas and arquivos:
            msg = f"Excluir {len(arquivos)} arquivos e {len(pastas)} pastas (com todo conteúdo)"
        elif pastas:
            msg = f"Excluir {len(pastas)} pastas e todo o conteúdo interno"
        else:
            msg = f"Excluir {len(arquivos)} arquivos"

        if not messagebox.askyesno("Confirmar Exclusão", msg, icon="warning"):
            return

        deletados = 0
        erros = 0

        for item in items:
            path = Path(item["caminho"]).resolve()  # Normaliza o caminho
            try:
                if item["tipo"] == "Pasta":
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    if path.exists():
                        path.unlink()
                    else:
                        raise FileNotFoundError("Arquivo não encontrado")
                deletados += 1
            except Exception as e:
                erros += 1
                

        messagebox.showinfo("Concluído", 
                          f"{deletados}  items excluídos com sucesso\n\n{erros} erros ignorados")
        self.filter_items()  # Atualiza a lista

    # ================= Outras funções =================
    def on_mouse_press(self, event):
        self.drag_start = self.tree.identify_row(event.y)

    def on_mouse_drag(self, event):
        current = self.tree.identify_row(event.y)
        if current and self.drag_start:
            try:
                children = self.tree.get_children()
                start = children.index(self.drag_start)
                end = children.index(current)
                if start > end:
                    start, end = end, start
                self.tree.selection_set(children[start:end+1])
            except:
                pass

    def on_mouse_release(self, event):
        self.drag_start = None

    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

    def get_folder_size(self, folder_path):
        total = 0
        try:
            for root, _, files in os.walk(folder_path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        except:
            pass
        return total

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def start_scan(self):
        folder = self.path_var.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("Aviso", "Selecione uma pasta válida")
            return

        self.tree.delete(*self.tree.get_children())
        self.progress["value"] = 0
        self.status_var.set("Escaneando...")

        Thread(target=self.scan_items, args=(folder,), daemon=True).start()

    def scan_items(self, root_folder):
        items = []
        for raiz, pastas, arquivos in os.walk(root_folder):
            for arq in arquivos:
                caminho = os.path.join(raiz, arq)
                try:
                    tamanho = os.path.getsize(caminho)
                    dt = datetime.fromtimestamp(os.path.getmtime(caminho))
                    items.append({
                        "nome": arq,
                        "tipo": get_file_type(arq, True),
                        "tamanho": tamanho,
                        "data": dt.strftime("%d/%m/%Y"),
                        "horas": dt.strftime("%H:%M:%S"),
                        "caminho": caminho,
                        "ext": os.path.splitext(arq)[1].lower()
                    })
                except:
                    pass

            for pasta in pastas:
                caminho_pasta = os.path.join(raiz, pasta)
                try:
                    dt = datetime.fromtimestamp(os.path.getmtime(caminho_pasta))
                    tamanho = self.get_folder_size(caminho_pasta)
                    items.append({
                        "nome": pasta,
                        "tipo": "Pasta",
                        "tamanho": tamanho,
                        "data": dt.strftime("%d/%m/%Y"),
                        "horas": dt.strftime("%H:%M:%S"),
                        "caminho": caminho_pasta,
                        "ext": ""
                    })
                except:
                    pass

        items.sort(key=lambda x: (x["tipo"] != "Pasta", -x.get("tamanho", 0)))
        self.all_items = items
        self.root.after(0, self.populate_tree, items)

    def populate_tree(self, items):
        self.progress["value"] = 100
        self.tree.delete(*self.tree.get_children())

        total_size = sum(item.get("tamanho", 0) for item in items)
        num_arquivos = sum(1 for item in items if item["tipo"] != "Pasta")
        num_pastas = len(items) - num_arquivos

        for item in items:
            self.tree.insert("", "end", values=(
                item["nome"], item["tipo"], format_size(item.get("tamanho", 0)),
                item["data"], item["horas"], item["caminho"]
            ))

        self.status_var.set(
            f"Contém: {num_arquivos} Arquivos | {num_pastas} Pastas | "
            f"{len(items)} itens | Total: {format_size(total_size)}"
        )

    def on_filter_change(self, event=None):
        if self.filter_type.get() == "Tudo":
            self.copy_all_btn.pack(side="left", padx=5)
        else:
            self.copy_all_btn.pack_forget()
        self.filter_items()

    def filter_items(self):
        search_term = self.search_var.get().strip().lower()
        filtro = self.filter_type.get()

        filtered = [
            item for item in self.all_items
            if (not search_term or search_term in item["nome"].lower() or search_term in item["caminho"].lower())
            and (filtro == "Tudo" or
                 (filtro == "Arquivos" and item["tipo"] != "Pasta") or
                 (filtro == "Pastas" and item["tipo"] == "Pasta") or
                 (filtro not in ["Tudo", "Arquivos", "Pastas"] and item.get("ext", "").lower() == filtro.lower()))
        ]

        self.tree.delete(*self.tree.get_children())
        total_size = sum(item.get("tamanho", 0) for item in filtered)
        num_arquivos = sum(1 for item in filtered if item["tipo"] != "Pasta")
        num_pastas = len(filtered) - num_arquivos

        for item in filtered:
            self.tree.insert("", "end", values=(
                item["nome"], item["tipo"], format_size(item.get("tamanho", 0)),
                item["data"], item["horas"], item["caminho"]
            ))

        self.status_var.set(
            f"Contém: {num_arquivos} Arquivos | {num_pastas} Pastas | "
            f"{len(filtered)} itens | Total: {format_size(total_size)}"
        )

    # Funções de cópia mantidas (melhoradas com Path)
    def copy_everything(self):
        destino = filedialog.askdirectory(title="Escolha a pasta de DESTINO")
        if not destino: return
        copiados = 0
        for item in self.all_items:
            try:
                src = Path(item["caminho"])
                dest = Path(destino) / item["nome"]
                if src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                else:
                    c = 1
                    while dest.exists():
                        nome, ext = os.path.splitext(item["nome"])
                        dest = Path(destino) / f"{nome}_{c}{ext}"
                        c += 1
                    shutil.copy2(src, dest)
                copiados += 1
            except:
                pass
        messagebox.showinfo("Sucesso", f"{copiados} itens copiados")

    def copy_all(self):
        self._copy_files([item for item in self.all_items if item["tipo"] != "Pasta"])

    def copy_selected(self):
        files = [{"nome": v[0], "caminho": v[5]} for iid in self.tree.selection() 
                 if (v := self.tree.item(iid)["values"])[1] != "Pasta"]
        self._copy_files(files)

    def _copy_files(self, files_list):
        if not files_list:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado")
            return
        destino = filedialog.askdirectory(title="Pasta de Destino")
        if not destino: return
        copiados = 0
        for f in files_list:
            try:
                src = Path(f["caminho"])
                dest = Path(destino) / f["nome"]
                c = 1
                while dest.exists():
                    nome, ext = os.path.splitext(f["nome"])
                    dest = Path(destino) / f"{nome}_{c}{ext}"
                    c += 1
                shutil.copy2(src, dest)
                copiados += 1
            except:
                pass
        messagebox.showinfo("Sucesso", f"{copiados} arquivos copiados")

    def open_item(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][5]
            try:
                os.startfile(path)
            except:
                messagebox.showerror("Erro", "Não foi possível abrir o item.")

    def open_file_folder(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][5]
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            try:
                os.startfile(folder)
            except:
                pass

    def show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Abrir", command=self.open_item)
            menu.add_command(label="Abrir Pasta", command=self.open_file_folder)
            menu.add_separator()
            menu.add_command(label="Copiar Selecionado", command=self.copy_selected)
            menu.add_command(label="Excluir", command=self.delete_selected)
            menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileFinder(root)
    root.mainloop()
