import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import shutil

# ---------- Formata tamanho ----------
def format_size(size_bytes):
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024**2):.2f} MB"
    else:
        return f"{size_bytes / (1024**3):.2f} GB"

# ---------- Coleta infos ----------
def get_dir_info(path):
    total_size = 0
    total_files = 0
    total_folders = 0
    last_modified = 0
    try:
        for root, dirs, files in os.walk(path, topdown=True):
            total_folders += len(dirs)
            total_files += len(files)
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    stat = os.stat(fp)
                    total_size += stat.st_size
                    if stat.st_mtime > last_modified:
                        last_modified = stat.st_mtime
                except:
                    pass
    except:
        pass
    try:
        dir_mtime = os.path.getmtime(path)
    except:
        dir_mtime = 0
    return total_size, total_files, total_folders, dir_mtime, last_modified

# ---------- Cor ----------
def get_size_color(size_str):
    if "KB" in size_str:
        return "blue"
    elif "MB" in size_str:
        return "green"
    else:
        return "red"

# ---------- Carregar filhos ao expandir ----------
def on_open(event):
    item = tree.focus()
    path = tree.set(item, "path")

    children = tree.get_children(item)
    if children and tree.item(children[0], "text") == "...":
        tree.delete(children[0])

        def load_content():
            try:
                entries = list(os.scandir(path))
                total = len(entries)
                done = 0
                for entry in entries:
                    if entry.is_dir():
                        size, files, folders, dir_mtime, last_mtime = get_dir_info(entry.path)
                        dir_date = datetime.fromtimestamp(dir_mtime).strftime("%d/%m/%Y %H:%M") if dir_mtime else "-"
                        last_date = datetime.fromtimestamp(last_mtime).strftime("%d/%m/%Y %H:%M") if last_mtime else "-"
                        size_str = format_size(size)
                        node = tree.insert(item, "end", text=entry.name,
                                           values=(size_str, files, folders, dir_date, last_date, entry.path),
                                           tags=(get_size_color(size_str),))
                        tree.insert(node, "end", text="...")  # placeholder
                    else:
                        stat = entry.stat()
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                        size_str = format_size(size)
                        tree.insert(item, "end", text=entry.name,
                                    values=(size_str, 1, 0, mtime, mtime, entry.path),
                                    tags=(get_size_color(size_str),))
                    done += 1
                    progress["value"] = (done / total) * 100
                progress["value"] = 0
            except:
                pass

        threading.Thread(target=load_content, daemon=True).start()

# ---------- Escolher pasta ----------
def choose_root():
    folder = filedialog.askdirectory(title="Selecione o disco ou pasta inicial")
    if not folder:
        return
    for child in tree.get_children():
        tree.delete(child)

    name = os.path.basename(folder.rstrip(os.sep)) or folder
    size, files, folders, dir_mtime, last_mtime = get_dir_info(folder)
    dir_date = datetime.fromtimestamp(dir_mtime).strftime("%d/%m/%Y %H:%M") if dir_mtime else "-"
    last_date = datetime.fromtimestamp(last_mtime).strftime("%d/%m/%Y %H:%M") if last_mtime else "-"
    size_str = format_size(size)

    root_node = tree.insert("", "end", text=name,
                            values=(size_str, files, folders, dir_date, last_date, folder),
                            open=False, tags=("black",))
    tree.insert(root_node, "end", text="...")  # placeholder

# ---------- Salvar resultados ----------
def save_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Arquivo de texto", "*.txt")])
    if not file_path:
        return
    def write_node(f, item, prefix=""):
        text = tree.item(item, "text")
        vals = tree.item(item, "values")
        line = f"{prefix}{text:<40} {vals[0]:>10} {vals[1]:>8} {vals[2]:>8} {vals[3]:>20} {vals[4]:>20}\n"
        f.write(line)
        for child in tree.get_children(item):
            write_node(f, child, prefix + "   ")
    with open(file_path, "w", encoding="utf-8") as f:
        header = f"{'Nome':<40} {'Tamanho':>10} {'Arquivos':>8} {'Pastas':>8} {'Data de Modificação':>20} {'Última Modificação':>20}\n"
        f.write(header)
        f.write("-" * 120 + "\n")
        for item in tree.get_children():
            write_node(f, item)
    messagebox.showinfo("Sucesso", f"Resultados salvos em\n\n{file_path}")

# ---------- Deletar arquivo/pasta selecionada ----------
def delete_selected():
    item = tree.focus()
    if not item:
        messagebox.showwarning("Aviso", "Selecione um arquivo ou pasta para deletar")
        return
    path = tree.set(item, "path")
    confirm = messagebox.askyesno("Confirmar exclusão", f"Tem certeza que deseja deletar\n\n{path}")
    if not confirm:
        return
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        tree.delete(item)
        messagebox.showinfo("Sucesso", "Arquivo/Pasta deletado com sucesso")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível deletar\n\n{e}")

# ---------- Interface ----------
root = tk.Tk()
root.title("Analyze Disk")
root.geometry("1300x800")
root.wm_state('zoomed')

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

btn_scan = tk.Button(btn_frame, text="Selecionar Pasta", bg="#03fc24", command=choose_root)
btn_scan.pack(side="left", padx=5)

btn_save = tk.Button(btn_frame, text="Salvar Resultados", bg="#03f0fc", command=save_results)
btn_save.pack(side="left", padx=5)

btn_delete = tk.Button(btn_frame, text="Delete", bg="#ff8c00", fg="black", command=delete_selected)
btn_delete.pack(side="left", padx=5)

progress = ttk.Progressbar(root, mode="determinate", length=600)
progress.pack(pady=5)

# ---------- Frame para Treeview + Scrollbar ----------
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True)

columns = ("Tamanho", "Arquivos", "Pastas", "Data de Modificação", "Última Modificação", "path")
tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
tree.pack(side="left", fill="both", expand=True)

# Scrollbar vertical
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

for col in columns[:-1]:
    tree.heading(col, text=col)
    tree.column(col, width=150, anchor="center")

tree["displaycolumns"] = columns[:-1]

tree.tag_configure("blue", foreground="blue")
tree.tag_configure("green", foreground="green")
tree.tag_configure("red", foreground="red")
tree.tag_configure("black", foreground="black")

tree.bind("<<TreeviewOpen>>", on_open)

root.mainloop()
