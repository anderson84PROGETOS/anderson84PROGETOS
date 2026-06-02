import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime

# ==================== DESCRIÇÕES ====================
DESCR = {
    "Cache": "Arquivos temporários de navegação",
    "Code Cache": "Cache de JavaScript compilado",
    "GPUCache": "Cache gráfico da GPU",
    "Media Cache": "Vídeos e áudios temporários",
    "DawnCache": "Cache gráfico interno do Chrome",
    "GrShaderCache": "Cache de shaders gráficos",
    "ShaderCache": "Cache de renderização",
    "component_crx_cache": "Cache de extensões",
    "extensions_crx_cache": "Cache de extensões baixadas",
    "BrowserMetrics": "Métricas temporárias",
    "Crashpad": "Relatórios de falha",
    "BrowserMetrics-spare.pma": "Métrica temporária",
    "CrashpadMetrics-active.pma": "Métrica temporária"
}

# Pastas seguras para limpar
SAFE_DEFAULT = ["Cache", "Code Cache", "GPUCache", "Media Cache", "DawnCache", "GrShaderCache", "ShaderCache"]
SAFE_USER = ["component_crx_cache", "extensions_crx_cache", "BrowserMetrics", "Crashpad",
             "BrowserMetrics-spare.pma", "CrashpadMetrics-active.pma"]


def fmt_size(n):
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Limpador Seguro do Chrome")
        self.root.geometry("1450x780")
        self.root.state("zoomed")

        self.path = tk.StringVar(value=os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"))

        # ==================== INTERFACE ====================
        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Pasta do Chrome:", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Entry(top, textvariable=self.path, width=120, font=("Consolas", 10)).pack(fill="x", pady=(2, 8))

        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Selecionar Pasta", command=self.pick, width=18).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Analisar", command=self.scan, bg="#0cdb04", fg="black", width=15, font=("Segoe UI", 9, "bold")).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Selecionar Tudo", command=self.sel_all, width=18).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Limpar Seleção", command=self.unsel_all, width=18).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Apagar Selecionados", command=self.delete, bg="#fa1b48", fg="black", width=20, font=("Segoe UI", 9, "bold")).pack(side="left", padx=3)

        # ==================== TREEVIEW ====================
        cols = ("ok", "perfil", "nome", "tipo", "tamanho", "data", "caminho", "descricao")

        self.tree = ttk.Treeview(root, columns=cols, show="headings")

        widths = {"ok": 26, "perfil": 76, "nome": 161, "tipo": 91, "tamanho": 71, "data": 118, "caminho": 505, "descricao": 220}

        for col in cols:
            self.tree.heading(col, text=col.title().replace("_", " "))
            self.tree.column(col, width=widths.get(col, 140), minwidth=50, stretch=False)

        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        self.tree.bind("<Button-1>", self.toggle_check)
        self.tree.bind("<Double-1>", self.open_item)

        tk.Label(root, text="☐ Clique na primeira coluna para marcar | Duplo clique abre a pasta", 
                 fg="gray").pack(pady=4)

    # ==================== MÉTODOS ====================

    def pick(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path.set(folder)

    def get_size(self, path):
        if os.path.isfile(path):
            try:
                return os.path.getsize(path)
            except:
                return 0
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except:
                    pass
        return total

    def get_profiles(self, base):
        profiles = []
        if not os.path.exists(base):
            return profiles
        for item in os.listdir(base):
            full = os.path.join(base, item)
            if os.path.isdir(full) and (item == "Default" or item.startswith("Profile") or "Guest" in item):
                profiles.append((item, full))
        return profiles

    def scan(self):
        self.tree.delete(*self.tree.get_children())
        base = self.path.get().strip()

        if not os.path.exists(base):
            messagebox.showerror("Erro", "Pasta não encontrada!")
            return

        itens = []

        # Pastas por perfil
        for prof_name, prof_path in self.get_profiles(base):
            for folder in SAFE_DEFAULT:
                full_path = os.path.join(prof_path, folder)
                if os.path.exists(full_path):
                    size = self.get_size(full_path)
                    itens.append((prof_name, full_path, size))

        # Itens no nível User Data
        for folder in SAFE_USER:
            full_path = os.path.join(base, folder)
            if os.path.exists(full_path):
                size = self.get_size(full_path)
                itens.append(("User Data", full_path, size))

        # Ordenar por tamanho (maior primeiro)
        itens.sort(key=lambda x: x[2], reverse=True)

        for prof, path, _ in itens:
            self.add_item(prof, path)

    def add_item(self, profile, path):
        if not os.path.exists(path):
            return

        name = os.path.basename(path)
        size = self.get_size(path)
        mtime = os.path.getmtime(path)
        date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        item_type = "Arquivo" if os.path.isfile(path) else "Pasta"
        desc = DESCR.get(name, "Item de cache seguro")

        self.tree.insert("", "end", values=(
            "☐", profile, name, item_type, fmt_size(size), date_str, path, desc
        ))

    def toggle_check(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if row and col == "#1":  # Primeira coluna
            values = list(self.tree.item(row, "values"))
            values[0] = "☑" if values[0] == "☐" else "☐"
            self.tree.item(row, values=values)

    def open_item(self, event):
        row = self.tree.focus()
        if row:
            path = self.tree.item(row, "values")[6]
            if os.path.exists(path):
                os.startfile(path)

    def sel_all(self):
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            values[0] = "☑"
            self.tree.item(item, values=values)

    def unsel_all(self):
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            values[0] = "☐"
            self.tree.item(item, values=values)

    def delete(self):
        if not messagebox.askyesno("Confirmação", "Deseja realmente apagar os itens selecionados?"):
            return

        freed = 0
        to_delete = []

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == "☑":
                to_delete.append((item, values[6]))

        for item_id, path in to_delete:
            try:
                size = self.get_size(path)
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
                freed += size
                self.tree.delete(item_id)
            except Exception as e:
                print(f"Erro ao deletar {path}: {e}")

        messagebox.showinfo("Concluído", f"Limpeza finalizada!\n\nEspaço liberado: {fmt_size(freed)}")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
