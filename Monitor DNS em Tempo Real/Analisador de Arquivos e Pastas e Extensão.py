import os
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

class FileSizeViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Arquivos e Pastas e Extensão")
        self.root.geometry("1450x780")
        self.root.state("zoomed")
        self.root.minsize(1000, 650)
        
        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.all_items = []
        
        self.create_widgets()

    # ==========================================================
    # INTERFACE
    # ==========================================================
    def create_widgets(self):
        # ================= TOP BAR =================
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Entry(
            top_frame,
            textvariable=self.path_var,
            font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Button(
            top_frame, text="Selecionar Pasta", command=self.select_folder,
            width=18, bg="#08D8E7", fg="black", font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        tk.Button(
            top_frame, text="Analisar", command=self.start_scan,
            width=12, bg="#08F864", fg="black", font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            top_frame, text="Salvar TXT", command=self.save_txt,
            width=12, bg="#FF9800", fg="black", font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            top_frame, text="Abrir Pasta", command=self.open_selected_folder,
            width=12, bg="#9C27B0", fg="black", font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(10, 0))

        # ================= PROGRESS BAR =================
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # ================= SEARCH =================
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(search_frame, text="🔍 Pesquisar:", font=("Segoe UI", 10)).pack(side="left")

        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))

        tk.Button(
            search_frame, text="Buscar", command=self.filter_items,
            bg="#08D419", fg="black", font=("Segoe UI", 10, "bold"), width=10
        ).pack(side="left")

        tk.Button(
            search_frame, text="Limpar", command=self.clear_search,
            bg="#f31c0c", fg="black", font=("Segoe UI", 10, "bold"), width=10
        ).pack(side="left", padx=(5, 0))

        self.search_entry.bind("<Return>", lambda e: self.filter_items())

        # ================= STATUS =================
        self.status_var = tk.StringVar(value="Selecione uma Pasta para começar")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bg="#e9e9e9",
            relief="sunken",
            font=("Segoe UI", 9),
            padx=10
        )
        self.status_bar.pack(fill="x", padx=10, pady=(0, 8))

        # ================= TREEVIEW =================
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("nome", "tipo", "extensao", "tamanho", "data", "caminho")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree.heading("nome", text="Nome")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("extensao", text="Extensão")
        self.tree.heading("tamanho", text="Tamanho")
        self.tree.heading("data", text="Data Modificação")
        self.tree.heading("caminho", text="Caminho Completo")

        self.tree.column("nome", width=280)
        self.tree.column("tipo", width=100)
        self.tree.column("extensao", width=110)
        self.tree.column("tamanho", width=130)
        self.tree.column("data", width=160)
        self.tree.column("caminho", width=550)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Menu de contexto
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Abrir Arquivo/Pasta", command=self.open_item)
        self.menu.add_command(label="Abrir Pasta do Item", command=self.open_item_folder)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_item())

    # ==========================================================
    # PESQUISA
    # ==========================================================
    def clear_search(self):
        self.search_var.set("")
        self.filter_items()

    def filter_items(self):
        search_term = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        if not search_term:
            for item in self.all_items:
                self.tree.insert("", "end", values=(
                    item["nome"],
                    item["tipo"],
                    item["extensao"],
                    format_size(item["tamanho"]),
                    item["data"],
                    item["caminho"]
                ))
            return

        filtered = [item for item in self.all_items if search_term in item["nome"].lower() or 
                    search_term in item["caminho"].lower() or 
                    search_term in item["data"].lower()]

        for item in filtered:
            self.tree.insert("", "end", values=(
                item["nome"], item["tipo"], item["extensao"],
                format_size(item["tamanho"]), item["data"], item["caminho"]
            ))

        self.status_var.set(f"{len(filtered)} itens Encontrados")

    # ==========================================================
    # PASTA
    # ==========================================================
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
        self.status_var.set("Analisando pasta...")
        self.search_var.set("")

        Thread(target=self.scan_folder, args=(folder,), daemon=True).start()

    # ==========================================================
    # ESCANEAR
    # ==========================================================
    def scan_folder(self, folder):
        items = []
        try:
            entries = list(os.scandir(folder))
            total = len(entries)

            for i, entry in enumerate(entries, 1):
                try:
                    item_date = self.get_date(entry.path)

                    if entry.is_file():
                        size = entry.stat().st_size
                        nome, extensao = os.path.splitext(entry.name)
                        tipo = "Arquivo"
                    else:
                        size = self.get_folder_size(entry.path)
                        extensao = "---"
                        tipo = "Pasta"

                    items.append({
                        "nome": entry.name,
                        "tipo": tipo,
                        "extensao": extensao,
                        "tamanho": size,
                        "data": item_date,
                        "caminho": entry.path
                    })
                except:
                    pass

                progress = (i / total) * 100 if total else 100
                self.root.after(0, self.update_progress, progress)

            items.sort(key=lambda x: x["tamanho"], reverse=True)
            self.all_items = items

            self.root.after(0, self.populate_tree, items)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))

    def get_folder_size(self, folder_path):
        total = 0
        try:
            for dirpath, _, filenames in os.walk(folder_path):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except:
                        pass
        except:
            pass
        return total

    def get_date(self, path):
        try:
            return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d/%m/%Y %H:%M:%S")
        except:
            return "Sem data"

    def update_progress(self, value):
        self.progress["value"] = value
        self.status_var.set(f"Analisando... {int(value)}%")

    def populate_tree(self, items):
        self.progress["value"] = 100
        total_size = sum(item["tamanho"] for item in items)

        self.tree.delete(*self.tree.get_children())
        for item in items:
            self.tree.insert("", "end", values=(
                item["nome"],
                item["tipo"],
                item["extensao"],
                format_size(item["tamanho"]),
                item["data"],
                item["caminho"]
            ))

        self.status_var.set(
            f"{len(items)} itens Encontrados | Tamanho Total: {format_size(total_size)}"
        )

    # ==========================================================
    # SALVAR TXT
    # ==========================================================
    def save_txt(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Nenhum dado para salvar!")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo TXT", "*.txt")],
            title="Salvar relatório"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("RELATÓRIO DE ARQUIVOS E PASTAS\n")
                f.write("=" * 100 + "\n\n")
                f.write(f"Gerado em: {datetime.now()}\n\n")

                for item in self.tree.get_children():
                    valores = self.tree.item(item)["values"]
                    f.write(f"Tipo      : {valores[1]}\n")
                    f.write(f"Nome      : {valores[0]}\n")
                    f.write(f"Extensão  : {valores[2]}\n")
                    f.write(f"Tamanho   : {valores[3]}\n")
                    f.write(f"Data      : {valores[4]}\n")
                    f.write(f"Caminho   : {valores[5]}\n")
                    f.write("-" * 100 + "\n\n")

            messagebox.showinfo("Sucesso", "Relatório salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ==========================================================
    # ABRIR
    # ==========================================================
    def open_selected_folder(self):
        folder = self.path_var.get().strip()
        if folder:
            try:
                os.startfile(folder) if os.name == "nt" else os.system(f'xdg-open "{folder}"')
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def open_item(self):
        self._open_item(open_folder=False)

    def open_item_folder(self):
        self._open_item(open_folder=True)

    def _open_item(self, open_folder=False):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])["values"][5]
        try:
            target = os.path.dirname(path) if open_folder and os.path.isfile(path) else path
            os.startfile(target) if os.name == "nt" else os.system(f'xdg-open "{target}"')
        except Exception as e:
            messagebox.showerror("Erro", str(e))

# ==========================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FileSizeViewer(root)
    root.mainloop()
