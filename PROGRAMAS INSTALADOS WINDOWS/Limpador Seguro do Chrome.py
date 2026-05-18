import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime

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
    "BrowserMetrics-spare.pma": "Métrica temporária.",
    "CrashpadMetrics-active.pma": "Métrica temporária"
}

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
    def __init__(self, r):
        self.r = r
        r.title("Limpador Seguro do Chrome")
        r.geometry("1450x780")
        r.state("zoomed")

        self.path = tk.StringVar(value=os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"))

        # === Topo ===
        top = tk.Frame(r)
        top.pack(fill="x", padx=8, pady=8)

        tk.Label(top, text="Pasta do Chrome:").pack(anchor="w")
        tk.Entry(top, textvariable=self.path, width=120).pack(fill="x", pady=(0, 8))

        # === Botões lado a lado ===
        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Selecionar Pasta", command=self.pick, width=15).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Analisar", command=self.scan, bg="#0cdb04", fg="black", width=12).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Selecionar Tudo", command=self.sel_all, width=15).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Limpar Seleção", command=self.unsel_all, width=15).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Apagar Selecionados", command=self.delete, bg="#fa1b48", fg="black", width=18).pack(side="left", padx=3)

        # === Treeview com colunas ajustáveis ===
        cols = ("ok", "perfil", "nome", "tipo", "tamanho", "data", "caminho", "descricao")

        self.t = ttk.Treeview(r, columns=cols, show="headings")

        # Configuração das colunas (tamanhos iniciais)
        widths = {
            "ok": 25,
            "perfil": 75,
            "nome": 160,
            "tipo": 90,
            "tamanho": 70,
            "data": 120,
            "caminho": 510,
            "descricao": 220
        }

        for c in cols:
            self.t.heading(c, text=c.title())
            self.t.column(c, width=widths.get(c, 140), minwidth=50, stretch=False)

        self.t.pack(fill="both", expand=True, padx=8, pady=8)

        self.t.bind("<Button-1>", self.toggle_first_col)
        self.t.bind("<Double-1>", self.open_item)

        tk.Label(r, text="Clique na primeira coluna (☐) para marcar | Duplo clique na linha abre a pasta").pack(pady=4)

    # ==================== Métodos (mesmos de antes) ====================

    def pick(self):
        p = filedialog.askdirectory()
        if p:
            self.path.set(p)

    def size(self, p):
        if os.path.isfile(p):
            return os.path.getsize(p)
        total = 0
        for dp, _, fs in os.walk(p):
            for f in fs:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except:
                    pass
        return total

    def profiles(self, base):
        out = []
        if not os.path.exists(base):
            return out
        for n in os.listdir(base):
            p = os.path.join(base, n)
            if os.path.isdir(p) and (n == "Default" or n.startswith("Profile") or "Guest" in n):
                out.append((n, p))
        return out

    def scan(self):
        self.t.delete(*self.t.get_children())
        base = self.path.get()

        for prof, pp in self.profiles(base):
            for x in SAFE_DEFAULT:
                self.add_item(prof, os.path.join(pp, x))

        for x in SAFE_USER:
            self.add_item("User Data", os.path.join(base, x))

    def add_item(self, prof, p):
        if not os.path.exists(p):
            return
        nm = os.path.basename(p)
        sz = self.size(p)
        dt = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m/%Y %H:%M")
        tp = "Arquivo" if os.path.isfile(p) else "Pasta"
        desc = DESCR.get(nm, "Item seguro de cache.")

        self.t.insert("", "end", values=("☐", prof, nm, tp, fmt_size(sz), dt, p, desc))

    def toggle_first_col(self, e):
        row = self.t.identify_row(e.y)
        if row and self.t.identify_column(e.x) == "#1":
            vals = list(self.t.item(row, "values"))
            vals[0] = "☑" if vals[0] == "☐" else "☐"
            self.t.item(row, values=vals)

    def open_item(self, e):
        row = self.t.focus()
        if row:
            p = self.t.item(row, "values")[6]
            if os.path.exists(p):
                os.startfile(p)

    def sel_all(self):
        for i in self.t.get_children():
            vals = list(self.t.item(i, "values"))
            vals[0] = "☑"
            self.t.item(i, values=vals)

    def unsel_all(self):
        for i in self.t.get_children():
            vals = list(self.t.item(i, "values"))
            vals[0] = "☐"
            self.t.item(i, values=vals)

    def delete(self):
        if not messagebox.askyesno("Confirmar", "Apagar os caches selecionados?"):
            return

        freed = 0
        for i in self.t.get_children():
            vals = self.t.item(i, "values")
            if vals and vals[0] == "☑":
                p = vals[6]
                try:
                    size = self.size(p)
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    elif os.path.isfile(p):
                        os.remove(p)
                    freed += size
                except:
                    pass

        messagebox.showinfo("Concluído", f"Limpeza concluída!\n\nEspaço liberado: {fmt_size(freed)}")
        self.scan()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
