import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
import subprocess

def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = [("TB", 1024**4), ("GB", 1024**3), ("MB", 1024**2), ("KB", 1024), ("B", 1)]
    for unit_name, unit_size in units:
        if size_bytes >= unit_size:
            value = size_bytes / unit_size
            return f"{value:.2f} {unit_name}"
    return f"{size_bytes:.2f} B"


def format_date_time(timestamp):
    if timestamp is None:
        return "", ""
    dt = datetime.fromtimestamp(timestamp)
    date_str = dt.strftime("%d/%m/%Y")
    time_str = dt.strftime("%H:%M:%S")
    return date_str, time_str


class ProfessionalFileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorador de Arquivos Profissional")
        self.root.geometry("1400x780")
        self.root.state("zoomed")
        self.root.configure(bg="#0A1A14")
        
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TFrame", background="#0A1A14")
        style.configure("TLabel", background="#0A1A14", foreground="#A0FFCC", font=("Segoe UI", 10))
        
        style.configure("Treeview", background="#11241B", foreground="#B8FFDB",
                       fieldbackground="#11241B", font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#00C17C", foreground="#0A1A14",
                       font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#00C17C")], 
                  foreground=[("selected", "#0A1A14")])
        
        # ==================== INICIA DIRETO NA PASTA APPDATA (raiz) ====================
        roaming = os.getenv("APPDATA")
        self.current_path = tk.StringVar(
            value=os.path.dirname(roaming) if roaming else os.path.expanduser("~")
        )
        
        self.all_folders = []
        self.all_files = []
        
        # ==================== BARRA SUPERIOR ====================
        top_frame = ttk.Frame(root)
        top_frame.pack(fill=tk.X, padx=12, pady=10)
        
        ttk.Label(top_frame, text="Caminho:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.path_entry = tk.Entry(top_frame, textvariable=self.current_path, 
                                  font=("Consolas", 10), bg="#1E3A2F", fg="#C2FFDD", 
                                  insertbackground="#00FF9D")
        self.path_entry.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        btn_padx = 3
        btn_pady = 2
        
        self.btn_ir = tk.Button(top_frame, text="Ir", command=self.go_to_path, 
                               bg="#1E90FF", fg="black", font=("Segoe UI", 9, "bold"), width=8)
        self.btn_ir.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        self.btn_escolher = tk.Button(top_frame, text="📁 Escolher", command=self.choose_folder, 
                                     bg="#00C17C", fg="black", font=("Segoe UI", 9, "bold"), width=12)
        self.btn_escolher.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        self.btn_atualizar = tk.Button(top_frame, text="🔄 Atualizar", command=self.refresh, 
                                      bg="#FF8C00", fg="black", font=("Segoe UI", 9, "bold"), width=12)
        self.btn_atualizar.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        self.btn_abrir_pasta = tk.Button(top_frame, text="📂 Abrir Pasta", 
                                        command=self.open_containing_folder,
                                        bg="#E3E622", fg="black", font=("Segoe UI", 9, "bold"), width=14)
        self.btn_abrir_pasta.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        self.btn_tarefas = tk.Button(top_frame, text="📍 Tarefas", command=self.go_to_tasks_folder, 
                                    bg="#9B59B6", fg="black", font=("Segoe UI", 9, "bold"), width=14)
        self.btn_tarefas.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        self.btn_copiar = tk.Button(top_frame, text="📋 Copiar", command=self.copy_path,
                                    bg="#3498DB", fg="black", font=("Segoe UI", 9, "bold"), width=12)
        self.btn_copiar.pack(side=tk.LEFT, padx=btn_padx, pady=btn_pady)
        
        # ==================== BARRA DE PESQUISA ====================
        search_frame = ttk.Frame(root)
        search_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        ttk.Label(search_frame, text="🔍 Pesquisar:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                    font=("Consolas", 10), bg="#1E3A2F", fg="#C2FFDD", 
                                    insertbackground="#00FF9D")
        self.search_entry.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.search_items())
        
        self.btn_pesquisar = tk.Button(search_frame, text="🔎 Pesquisar", command=self.search_items,
                                      bg="#00C17C", fg="black", font=("Segoe UI", 9, "bold"), width=12)
        self.btn_pesquisar.pack(side=tk.LEFT, padx=4)
        
        self.btn_limpar = tk.Button(search_frame, text="Limpar", command=self.clear_search,
                                   bg="#E74C3C", fg="black", font=("Segoe UI", 9, "bold"), width=10)
        self.btn_limpar.pack(side=tk.LEFT, padx=4)
        
        # ==================== PAINEL DIVIDIDO ====================
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        
        # === PASTAS ===
        tree_frame = ttk.LabelFrame(paned, text=" Pastas ")
        self.tree = ttk.Treeview(tree_frame, columns=("size", "date", "time"), show="tree headings")
        self.tree.heading("#0", text="Nome")
        self.tree.heading("size", text="PASTA")
        self.tree.heading("date", text="Data")
        self.tree.heading("time", text="Hora")
        
        self.tree.column("#0", width=300)
        self.tree.column("size", width=80)
        self.tree.column("date", width=110)
        self.tree.column("time", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(tree_frame)
        
        # === ARQUIVOS ===
        files_frame = ttk.LabelFrame(paned, text=" Arquivos ")
        self.files = ttk.Treeview(files_frame, columns=("fullpath", "size", "date", "time"), show="headings")
        self.files.heading("fullpath", text="Caminho Completo")
        self.files.heading("size", text="Tamanho")
        self.files.heading("date", text="Data")
        self.files.heading("time", text="Hora")
        
        self.files.column("fullpath", width=550)
        self.files.column("size", width=100)
        self.files.column("date", width=100)
        self.files.column("time", width=80)
        self.files.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        files_frame.pack(fill=tk.BOTH, expand=True)
        paned.add(files_frame)
        
        self.tree.bind("<Double-1>", self.double_click)
        
        self.status = tk.Label(root, text="Pronto", relief=tk.SUNKEN, anchor=tk.W, 
                              bg="#0A1A14", fg="#A0FFCC", font=("Segoe UI", 9))
        self.status.pack(fill=tk.X, padx=12, pady=6)
        
        self.load_folder()
    
    # ==================== DOUBLE CLICK ====================
    def double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        text = self.tree.item(selection[0], "text")
        
        if "Voltar" in text:
            new_path = os.path.dirname(self.current_path.get())
        else:
            new_path = os.path.join(self.current_path.get(), text)
        
        if os.path.isdir(new_path):
            self.current_path.set(new_path)
            self.load_folder()
    
    # ==================== PESQUISA ====================
    def search_items(self):
        term = self.search_var.get().strip()
        if not term:
            self.refresh()
            return
        
        term_lower = term.lower()
        self.status.config(text=f"🔎 Buscando por: {term}")
        self.root.update()
        
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in self.files.get_children():
            self.files.delete(i)
        
        path = self.current_path.get()
        if os.path.dirname(path) != path:
            self.tree.insert("", 0, text="◀️ Voltar ◀️", values=("", "", ""))   
            self.tree.insert("", 0, text="", values=("", ""))
            self.tree.insert("", "end", text="", values=("", ""))
        
        count_folders = 0
        count_files = 0
        
        is_year_search = term.isdigit() and len(term) == 4
        
        for folder in self.all_folders:
            name = folder[0].lower()
            date = folder[3].lower()
            time = folder[4].lower()
            if (is_year_search and term in date) or (term_lower in name or term_lower in date or term_lower in time):
                self.tree.insert("", "end", text=folder[0], values=(folder[2], folder[3], folder[4]))
                count_folders += 1
        
        for file in self.all_files:
            name = file[0].lower()
            date = file[3].lower()
            time = file[4].lower()
            if (is_year_search and term in date) or (term_lower in name or term_lower in date or term_lower in time):
                self.files.insert("", "end", values=(file[1], file[2], file[3], file[4]))
                count_files += 1
        
        self.status.config(text=f"✅ Encontrados: {count_folders} pastas e {count_files} arquivos")
    
    def clear_search(self):
        self.search_var.set("")
        self.refresh()
    
    # ==================== OUTROS MÉTODOS ====================
    def open_containing_folder(self):
        selection = self.files.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
            return
        fullpath = self.files.item(selection[0], "values")[0]
        if not os.path.exists(fullpath):
            messagebox.showerror("Erro", "Arquivo não encontrado.")
            return
        folder_path = os.path.dirname(fullpath)
        try:
            if os.name == 'nt':
                os.startfile(folder_path)
            else:
                cmd = ['xdg-open', folder_path] if os.name == 'posix' else ['open', folder_path]
                subprocess.call(cmd)
            self.status.config(text=f"📂 Pasta aberta: {folder_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
    
    def copy_path(self):
        path = self.current_path.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.root.update()
        self.status.config(text="📋 Caminho copiado!")
    
    def go_to_tasks_folder(self):
        tasks_path = r"C:\Windows\System32\Tasks"
        if os.path.exists(tasks_path):
            self.current_path.set(tasks_path)
            self.load_folder()
        else:
            messagebox.showinfo("Informação", "Pasta de Tarefas do Windows não encontrada.")
    
    def choose_folder(self):
        path = filedialog.askdirectory(initialdir=self.current_path.get())
        if path:
            self.current_path.set(path)
            self.load_folder()
    
    def go_to_path(self):
        path = self.current_path.get().strip()
        if os.path.isdir(path):
            self.load_folder()
        else:
            messagebox.showerror("Erro", "Caminho inválido!")
    
    def refresh(self):
        self.load_folder()
    
    def load_folder(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in self.files.get_children():
            self.files.delete(i)
        
        path = self.current_path.get()
        if not os.path.exists(path):
            self.status.config(text="❌ Caminho não encontrado!")
            return
        
        self.status.config(text=f"🔄 Carregando... {path}")
        self.root.update()
        
        self.all_folders = []
        self.all_files = []
        
        try:
            if os.path.dirname(path) != path:
                self.tree.insert("", 0, text="◀️ Voltar ◀️", values=("", "", ""))
                self.tree.insert("", 0, text="", values=("", ""))
                self.tree.insert("", "end", text="", values=("", ""))
            
            for entry in os.scandir(path):
                try:
                    stat = entry.stat()
                    date_str, time_str = format_date_time(stat.st_mtime)
                    size_str = "<Pasta>" if entry.is_dir() else human_readable_size(stat.st_size)
                    
                    if entry.is_dir():
                        self.all_folders.append((entry.name, entry.path, size_str, date_str, time_str))
                        self.tree.insert("", "end", text=entry.name, values=(size_str, date_str, time_str))
                    else:
                        self.all_files.append((entry.name, entry.path, size_str, date_str, time_str))
                except:
                    continue
            
            self.all_files.sort(key=lambda x: x[0].lower())
            for _, full, size, date, time in self.all_files:
                self.files.insert("", "end", values=(full, size, date, time))
            
            self.status.config(text=f"✅ {len(self.all_folders)} pastas e {len(self.all_files)} arquivos | {path}")
            
        except Exception as e:
            self.status.config(text=f"❌ Erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalFileExplorer(root)
    root.mainloop()
