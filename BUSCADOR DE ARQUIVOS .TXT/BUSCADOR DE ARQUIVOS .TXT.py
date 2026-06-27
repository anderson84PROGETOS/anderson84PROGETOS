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


class TxtFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("BUSCADOR DE ARQUIVOS .TXT")
        self.root.geometry("1450x780")
        self.root.state("zoomed")
        self.root.minsize(1000, 650)
        self.root.configure(bg="#000000")

        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.all_txt_files = []

        self.create_widgets()

    def create_widgets(self):
        # TOP BAR
        top_frame = tk.Frame(self.root, bg="#000000", width=1212, height=50)
        top_frame.pack(padx=(0, 42), pady=10)
        top_frame.pack_propagate(False)    
        
        tk.Entry(top_frame, textvariable=self.path_var, font=("Consolas", 10), 
                 bg="#111111", fg="#00ff00", insertbackground="#00ff00").pack(side="left", fill="x", expand=True, padx=(0, 5))

        tk.Button(top_frame, text="Selecionar Pasta", command=self.select_folder,
                  width=18, bg="#006600", fg="#ffffff", font=("Consolas", 10, "bold")).pack(side="left")

        tk.Button(top_frame, text="Analisar .TXT", command=self.start_scan,
                  width=15, bg="#00cc00", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=(5, 0))

        tk.Button(top_frame, text="Copiar Todos .TXT", command=self.copy_all_txt,
                  width=18, bg="#ff8800", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=(5, 0))

        tk.Button(top_frame, text="Copiar Selecionados", command=self.copy_selected,
                  width=20, bg="#ff5500", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=(5, 0))

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100, length=2000)
        self.progress.pack(anchor="e", padx=(10, 60), pady=(0, 5))

        # Search
        search_frame = tk.Frame(self.root, bg="#000000")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="🔍 Pesquisar:", font=("Consolas", 10), bg="#000000", fg="#00ff00").pack(side="left")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Consolas", 10), bg="#111111", fg="#00ff00", insertbackground="#00ff00", width=150)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="Buscar", command=self.filter_items,
                  bg="#00cc00", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left")

        # Status
        self.status_var = tk.StringVar(value="Selecione uma pasta e clique em Analisar .TXT")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                                   bg="#000000", fg="#00ff00", font=("Consolas", 9), padx=10)
        self.status_bar.pack(fill="x", padx=10, pady=5)

        # ================= TREEVIEW =================
        table_frame = tk.Frame(self.root, bg="#000000")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("nome", "tamanho", "data", "horas", "caminho")

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", 
                       background="#000000", 
                       foreground="#00ff00", 
                       fieldbackground="#000000",
                       rowheight=28,
                       font=("Consolas", 10))
        style.map("Treeview", 
                 background=[('selected', '#003300')],
                 foreground=[('selected', '#ffffff')])
        style.configure("Treeview.Heading", 
                       background="#001100", 
                       foreground="#00ff00", 
                       font=("Consolas", 10, "bold"))

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")

        self.tree.heading("nome", text="Nome do Arquivo")
        self.tree.heading("tamanho", text="Tamanho")
        self.tree.heading("data", text="Data")
        self.tree.heading("horas", text="Horas")
        self.tree.heading("caminho", text="Caminho Completo")

        self.tree.column("nome", width=450)
        self.tree.column("tamanho", width=110)
        self.tree.column("data", width=110)
        self.tree.column("horas", width=100)
        self.tree.column("caminho", width=550)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ================= MENU E BINDINGS =================
        self.menu = tk.Menu(self.root, tearoff=0, bg="#000000", fg="#00ff00")
        self.menu.add_command(label="Abrir Arquivo", command=self.open_file)
        self.menu.add_command(label="Abrir Pasta do Arquivo", command=self.open_file_folder)
        self.menu.add_separator()
        self.menu.add_command(label="🗑️ Excluir Selecionados", command=self.delete_selected, foreground="#ff4444")

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_file())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Delete>", lambda e: self.delete_selected())

        # ================= NOVO: Ctrl + A para selecionar todos =================
        self.tree.bind("<Control-a>", self.select_all)
        self.tree.bind("<Control-A>", self.select_all)

        # Roda Pé INSTRUÇÕES DE USO
        footer = tk.Label(
            self.root,
            text="""📖 INSTRUÇÕES DE USO

Selecione uma Pasta → Clique Em 'Analisar .TXT'   → Utilize 'Pesquisar' Para Localizar Arquivos  → Duplo clique Para Abrir um Arquivo
Botão Direito: Abrir, Abrir Pasta ou Excluir | Ctrl = Múltipla Seleção | Shift = Selecionar intervalo | Ctrl + A = Selecionar Todos | Delete = Excluir Arquivos""",

            bg="#111111",
            fg="#05fdf1",
            font=("Consolas", 11, "bold"),
            justify="left",
            anchor="w",
            padx=1,
            pady=5
        )

        footer.pack(side="bottom", fill="x")

        footer = tk.Label(
            self.root,
            text="📂 BUSCADOR DE ARQUIVOS .TXT  |  Dev: Anderson  | github.com/anderson84PROGETOS |  © 2026",
            bg="#111111",
            fg="#666666",
            font=("Consolas", 10, "italic")
        )

        footer.pack(side="bottom", pady=3)

    # ====================== FUNÇÕES ======================
    def select_all(self, event=None):
        """Seleciona todos os itens do Treeview com Ctrl + A"""
        self.tree.selection_set(self.tree.get_children())
        return "break"  # Impede comportamento padrão do Tkinter

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
        self.status_var.set("Buscando arquivos .TXT...")

        Thread(target=self.scan_txt_files, args=(folder,), daemon=True).start()

    def scan_txt_files(self, folder):
        items = []
        try:
            for raiz, _, arquivos in os.walk(folder):
                for arq in arquivos:
                    if arq.lower().endswith('.txt'):
                        caminho = os.path.join(raiz, arq)
                        try:
                            tamanho = os.path.getsize(caminho)
                            dt = datetime.fromtimestamp(os.path.getmtime(caminho))
                            
                            items.append({
                                "nome": arq,
                                "tamanho": tamanho,
                                "data": dt.strftime("%d/%m/%Y"),
                                "horas": dt.strftime("%H:%M:%S"),
                                "caminho": caminho
                            })
                        except:
                            pass

            items.sort(key=lambda x: x["tamanho"], reverse=True)
            self.all_txt_files = items
            self.root.after(0, self.populate_tree, items)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))

    def populate_tree(self, items):
        self.progress["value"] = 100
        self.tree.delete(*self.tree.get_children())

        for item in items:
            self.tree.insert("", "end", values=(
                item["nome"],
                format_size(item["tamanho"]),
                item["data"],
                item["horas"],
                item["caminho"]
            ))

        total = sum(i['tamanho'] for i in items)
        self.status_var.set(f"{len(items)} arquivo(s) .TXT | Total: {format_size(total)}")

    def filter_items(self):
        term = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        filtered = [item for item in self.all_txt_files 
                   if term in item["nome"].lower() or term in item["caminho"].lower()]

        for item in filtered:
            self.tree.insert("", "end", values=(
                item["nome"], 
                format_size(item["tamanho"]), 
                item["data"], 
                item["horas"], 
                item["caminho"]
            ))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return

        files_to_delete = []
        for item_id in selected:
            values = self.tree.item(item_id)["values"]
            files_to_delete.append({
                "nome": values[0],
                "caminho": values[4]
            })

        if not files_to_delete:
            return

        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja realmente apagar {len(files_to_delete)} arquivo(s)?\n\n"
            "Esta ação não pode ser desfeita!",
            icon="warning"
        )

        if not confirm:
            return

        deletados = 0
        erros = 0

        for file in files_to_delete:
            try:
                if os.path.exists(file["caminho"]):
                    os.remove(file["caminho"])
                    deletados += 1
            except Exception:
                erros += 1

        self.all_txt_files = [f for f in self.all_txt_files if f["caminho"] not in [x["caminho"] for x in files_to_delete]]
        
        self.root.after(0, self.refresh_after_delete)

        if erros == 0:
            messagebox.showinfo("Sucesso", f"{deletados} arquivo(s) excluído(s) com sucesso!")
        else:
            messagebox.showwarning("Atenção", f"{deletados} arquivo(s) excluído(s).\n{erros} erro(s) ao excluir.")

    def refresh_after_delete(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.all_txt_files:
            self.tree.insert("", "end", values=(
                item["nome"],
                format_size(item["tamanho"]),
                item["data"],
                item["horas"],
                item["caminho"]
            ))
        
        total = sum(i['tamanho'] for i in self.all_txt_files)
        self.status_var.set(f"{len(self.all_txt_files)} arquivo(s) .TXT | Total: {format_size(total)}")

    def copy_all_txt(self):
        if not self.all_txt_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo .TXT encontrado!")
            return
        self._copy_files(self.all_txt_files)

    def copy_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo!")
            return
        
        files_to_copy = []
        for item_id in selected:
            values = self.tree.item(item_id)["values"]
            files_to_copy.append({"nome": values[0], "caminho": values[4]})
        
        self._copy_files(files_to_copy)

    def _copy_files(self, files_list):
        destino = filedialog.askdirectory(title="Escolha a pasta de DESTINO")
        if not destino:
            return

        copiados = 0
        try:
            for file in files_list:
                destino_final = os.path.join(destino, file["nome"])
                contador = 1
                while os.path.exists(destino_final):
                    nome, ext = os.path.splitext(file["nome"])
                    destino_final = os.path.join(destino, f"{nome}_{contador}{ext}")
                    contador += 1
                shutil.copy2(file["caminho"], destino_final)
                copiados += 1

            messagebox.showinfo("Sucesso", f"{copiados} arquivo(s) .TXT copiado(s)!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar:\n{str(e)}")

    def open_file(self):
        selected = self.tree.selection()
        if selected:
            path = self.tree.item(selected[0])["values"][4]
            try:
                os.startfile(path) if os.name == "nt" else os.system(f'xdg-open "{path}"')
            except:
                messagebox.showerror("Erro", "Não foi possível abrir o arquivo.")

    def open_file_folder(self):
        selected = self.tree.selection()
        if selected:
            path = self.tree.item(selected[0])["values"][4]
            try:
                folder = os.path.dirname(path)
                os.startfile(folder) if os.name == "nt" else os.system(f'xdg-open "{folder}"')
            except:
                pass

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = TxtFinder(root)
    root.mainloop()
