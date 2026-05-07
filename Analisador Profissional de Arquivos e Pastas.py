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
        self.root.title("Analisador Profissional de Arquivos e Pastas")
        self.root.geometry("1300x700")
        self.root.state("zoomed")
        self.root.resizable(True, True)
        self.root.minsize(900, 550)

        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.all_items = []          # Guardar todos os itens para filtrar

        self.create_widgets()

    def create_widgets(self):
        # === TOP BAR ===
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Entry(top_frame, textvariable=self.path_var, font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Button(top_frame, text="Selecionar Pasta", command=self.select_folder,
                  width=18, bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left")

        tk.Button(top_frame, text="Analisar", command=self.start_scan,
                  width=12, bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 0))

        tk.Button(top_frame, text="Salvar TXT", command=self.save_txt,
                  width=12, bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 0))

        tk.Button(top_frame, text="Abrir Pasta", command=self.open_selected_folder,
                  width=12, bg="#9C27B0", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 0))

        # === PROGRESS BAR ===
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # === SEARCH BAR (Nova) ===
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(search_frame, text="🔍 Pesquisar:", font=("Segoe UI", 9)).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, font=("Segoe UI", 10)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))

        tk.Button(
            search_frame, text="Buscar", command=self.filter_items,
            bg="#2196F3", fg="white", width=10
        ).pack(side="left")

        tk.Button(
            search_frame, text="Limpar", command=self.clear_search,
            bg="#f44336", fg="white", width=10
        ).pack(side="left", padx=(5, 0))

        # Enter para pesquisar
        self.search_entry.bind("<Return>", lambda e: self.filter_items())

        # === STATUS BAR ===
        self.status_var = tk.StringVar(value="Selecione uma pasta para começar")
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            bg="#e9e9e9", relief="sunken", font=("Segoe UI", 9), padx=10
        )
        self.status_bar.pack(fill="x", padx=10, pady=(0, 8))

        # === TREEVIEW ===
        columns = ("nome", "tipo", "tamanho", "caminho")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        self.tree.heading("nome", text="Nome")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("tamanho", text="Tamanho")
        self.tree.heading("caminho", text="Caminho")

        self.tree.column("nome", width=320, minwidth=150, stretch=True)
        self.tree.column("tipo", width=100, minwidth=80, stretch=True)
        self.tree.column("tamanho", width=130, minwidth=90, stretch=True)
        self.tree.column("caminho", width=680, minwidth=200, stretch=True)

        scrollbar_y = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar_y.pack(side="right", fill="y", pady=5)
        scrollbar_x.pack(fill="x", padx=10)

        # === CONTEXT MENU ===
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Abrir Pasta do Item", command=self.open_item_folder)
        self.menu.add_command(label="Abrir Arquivo", command=self.open_item)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_item())

    def clear_search(self):
        self.search_var.set("")
        self.filter_items()

    def filter_items(self):
        search_term = self.search_var.get().strip().lower()
        
        self.tree.delete(*self.tree.get_children())

        if not search_term:
            # Mostra todos
            for name, item_type, size, path in self.all_items:
                self.tree.insert("", "end", values=(name, item_type, format_size(size), path))
        else:
            # Filtra
            filtered = [
                (name, item_type, size, path)
                for name, item_type, size, path in self.all_items
                if search_term in name.lower()
            ]
            for name, item_type, size, path in filtered:
                self.tree.insert("", "end", values=(name, item_type, format_size(size), path))

    # ====================== OUTROS MÉTODOS ======================
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
        self.status_var.set("Analisando...")
        self.search_var.set("")   # Limpa pesquisa ao iniciar nova análise

        Thread(target=self.scan_folder, args=(folder,), daemon=True).start()

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

    def update_progress(self, value):
        self.progress["value"] = value
        self.status_var.set(f"Analisando... {int(value)}%")

    def scan_folder(self, folder):
        items = []
        try:
            entries = list(os.scandir(folder))
            total = len(entries)

            for i, entry in enumerate(entries, 1):
                try:
                    if entry.is_file():
                        size = entry.stat().st_size
                        items.append((entry.name, "Arquivo", size, entry.path))
                    elif entry.is_dir():
                        size = self.get_folder_size(entry.path)
                        items.append((entry.name, "Pasta", size, entry.path))
                except:
                    pass

                self.root.after(0, self.update_progress, (i / total) * 100 if total else 100)

            items.sort(key=lambda x: x[2], reverse=True)
            self.all_items = items  # Salva para pesquisa
            self.root.after(0, self.populate_tree, items)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))

    def populate_tree(self, items):
        self.progress["value"] = 100
        total_size = sum(size for _, _, size, _ in items)

        self.tree.delete(*self.tree.get_children())
        for name, item_type, size, path in items:
            self.tree.insert("", "end", values=(name, item_type, format_size(size), path))

        self.status_var.set(f"{len(items)} itens encontrados | Tamanho total: {format_size(total_size)}")

    # ... (os demais métodos permanecem iguais: save_txt, open_selected_folder, etc.)

    def save_txt(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Nenhum dado para salvar")
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
                f.write("=" * 80 + "\n\n")
                f.write(f"Gerado em: {datetime.now()}\n\n")

                for item in self.tree.get_children():
                    nome, tipo, tamanho, caminho = self.tree.item(item)["values"]
                    f.write(f"{tipo} | {tamanho} | {nome}\n")
                    f.write(f"{caminho}\n\n")

            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def open_selected_folder(self):
        folder = self.path_var.get().strip()
        if folder:
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def show_context_menu(self, event):
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def open_item_folder(self):
        self._open_item(open_folder=True)

    def open_item(self):
        self._open_item(open_folder=False)

    def _open_item(self, open_folder=False):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])["values"][3]
        try:
            target = os.path.dirname(path) if open_folder and os.path.isfile(path) else path
            os.startfile(target)
        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSizeViewer(root)
    root.mainloop()
