import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from datetime import datetime

# ---------- Função para formatar o tamanho ----------
def format_size(size_bytes):
    if size_bytes < 1024**2:  # menor que 1 MB
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:  # menor que 1 GB
        return f"{size_bytes / (1024**2):.2f} MB"
    else:  # 1 GB ou mais
        return f"{size_bytes / (1024**3):.2f} GB"

# ---------- Calcula informações de um diretório ----------
def get_dir_info(path):
    total_size = 0
    total_files = 0
    total_folders = 0
    last_modified = 0

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

    try:
        dir_mtime = os.path.getmtime(path)
    except:
        dir_mtime = 0

    return total_size, total_files, total_folders, dir_mtime, last_modified

# ---------- Função executada na thread separada ----------
def scan_disk_thread(folder):
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, f"Escaneando: {folder}\n\n")
    root.update_idletasks()

    try:
        entries = [os.path.join(folder, e) for e in os.listdir(folder) if os.path.isdir(os.path.join(folder, e))]
    except PermissionError:
        messagebox.showerror("Erro", "Permissão negada ao acessar essa pasta.")
        progress.stop()
        progress["value"] = 0
        return

    total = len(entries)
    progress["maximum"] = total
    progress["value"] = 0

    header = f"{'Nome':<38} {'Tamanho':>12} {'Arquivos':>12} {'Pastas':>10} {'Data de Modificação':>22} {'Última Modificação':>22}\n"
    text_area.insert(tk.END, header)
    text_area.insert(tk.END, "-"*121 + "\n")

    for i, entry in enumerate(entries, start=1):
        size, files, folders, dir_mtime, last_mtime = get_dir_info(entry)
        dir_date = datetime.fromtimestamp(dir_mtime).strftime("%d/%m/%Y %H:%M") if dir_mtime > 0 else "-"
        last_date = datetime.fromtimestamp(last_mtime).strftime("%d/%m/%Y %H:%M") if last_mtime > 0 else "-"
        size_str = format_size(size)
        name = os.path.basename(entry)

        # Insere linha normal até o tamanho
        text_area.insert(tk.END, f"{name:<40} ")

        # Escolhe cor de acordo com a unidade
        if "KB" in size_str:
            color = "blue"
        elif "MB" in size_str:
            color = "green"
        else:
            color = "red"

        text_area.insert(tk.END, f"{size_str:>10}", color)
        text_area.insert(tk.END, f" {files:>10} {folders:>9} {dir_date:>22} {last_date:>23}\n\n")

        progress["value"] = i
        root.update_idletasks()

    progress.stop()
    progress["value"] = 0

# ---------- Função chamada ao clicar no botão ----------
def scan_disk():
    folder = filedialog.askdirectory(title="Selecione o disco (ex: C:\\)")
    if not folder:
        return
    t = threading.Thread(target=scan_disk_thread, args=(folder,), daemon=True)
    t.start()

# ---------- Função para salvar o conteúdo ----------
def save_results():
    content = text_area.get("1.0", tk.END)
    if not content.strip():
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de texto", "*.txt")],
        title="Salvar resultados"
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Sucesso", f"Resultados salvos em\n\n{file_path}")

# ---------------- Interface ------------------
root = tk.Tk()
root.title("Analisar Disco")
root.geometry("1160x920")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

btn_scan = tk.Button(btn_frame, text="Selecionar Disco", bg="#03fc24", fg="black", command=scan_disk)
btn_scan.pack(pady=10)

btn_save = tk.Button(btn_frame, text="Salvar Resultados", bg="#f5a00c", fg="black", command=save_results)
btn_save.pack(pady=5)

progress = ttk.Progressbar(root, mode="determinate", length=600)
progress.pack(pady=5)

text_area = scrolledtext.ScrolledText(root, width=130, height=45)
text_area.pack(pady=10)

# Define as tags de cor
text_area.tag_config("blue", foreground="blue")
text_area.tag_config("green", foreground="green")
text_area.tag_config("red", foreground="red")

root.mainloop()
