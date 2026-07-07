import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from datetime import datetime
from pathlib import Path
import hashlib
import webbrowser

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

def get_sha256(file_path):
    """Calcula o hash SHA-256 de um arquivo"""
    try:
        hash_sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha.update(chunk)
        return hash_sha.hexdigest()
    except:
        return "Erro ao calcular"

class FileFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ EXPLORADOR DE PASTAS E ARQUIVOS DO WINDOWS 🛡️")
        self.root.geometry("1450x780")
        self.root.state("zoomed")
        self.root.minsize(1150, 650)
        self.root.configure(bg="#000000")

        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_type = tk.StringVar(value="Tudo")
        
        self.extensions = [
        # Sistema Windows
        '.exe', '.dll', '.sys', '.drv', '.ocx', '.cpl', '.scr',
        '.msi', '.msp', '.cab', '.cat', '.inf',
        
        # Scripts e comandos
        '.bat', '.cmd', '.ps1', '.vbs', '.vbe', '.js', '.jse',
        '.wsf', '.wsh', '.py', '.pyw', '.rb', '.pl',

        # Configurações
        '.ini', '.cfg', '.conf', '.config', '.xml', '.json',
        '.yaml', '.yml', '.reg', '.log', '.tmp',

        # Documentos Microsoft Office
        '.doc', '.docx', '.docm',
        '.xls', '.xlsx', '.xlsm', '.xlsb',
        '.ppt', '.pptx', '.pptm',
        '.odt', '.ods', '.odp',
        '.rtf', '.txt', '.csv',

        # PDF e leitura
        '.pdf', '.epub', '.mobi',

        # Imagens
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.tif', '.tiff', '.webp', '.ico',
        '.svg', '.heic',

        # Vídeos
        '.mp4', '.mkv', '.avi', '.mov',
        '.wmv', '.flv', '.webm', '.mpeg',
        '.mpg', '.3gp',

        # Áudio
        '.mp3', '.wav', '.flac', '.aac',
        '.ogg', '.wma', '.m4a',

        # Compactação
        '.zip', '.rar', '.7z', '.tar',
        '.gz', '.bz2', '.xz',

        # Imagens de disco / backup
        '.iso', '.img', '.vhd', '.vhdx',
        '.wim', '.esd',

        # Banco de dados
        '.db', '.sqlite', '.sqlite3',
        '.mdb', '.accdb',

        # Desenvolvimento
        '.html', '.htm', '.css', '.scss',
        '.java', '.class', '.jar',
        '.cpp', '.c', '.h', '.hpp',
        '.cs', '.go', '.rs',
        '.php', '.sql',

        # Máquinas virtuais
        '.vmx', '.vmdk', '.ova', '.ovf',

        # Jogos e programas
        '.pak', '.dat', '.bin',
        '.res', '.asset',

        # Fontes
        '.ttf', '.otf', '.woff', '.woff2',

        # Certificados e segurança
        '.cer', '.crt', '.pem', '.pfx',
        '.key',

        # Windows Update / instalação
        '.mum', '.manifest',
        '.blf', '.regtrans-ms',

        # Atalhos Windows
        '.lnk', '.url',

        # E-mails
        '.eml', '.msg', '.pst', '.ost',

        # Torrent
        '.torrent'
    ]
        self.all_items = []
        self.root_folder_size = 0
        self.create_widgets()

    def open_guide(self):
        janela = tk.Toplevel(self.root)
        janela.title("📖 Guia Rápido -🛡️ EXPLORADOR DE PASTAS E ARQUIVOS DO WINDOWS 🛡️")
        janela.geometry("850x650")
        janela.configure(bg="#000000")
        janela.resizable(True, True)

        texto = """
    📖 GUIA RÁPIDO DE UTILIZAÇÃO

    🛡️ EXPLORADOR DE PASTAS E ARQUIVOS DO WINDOWS 🛡️

    • 1) SELECIONAR PASTA

    Selecione uma pasta ou unidade do computador

    e clique no botão "Analisar"

    O programa irá localizar

    ✓ Arquivos
    ✓ Pastas
    ✓ Extensões
    ✓ Tamanho dos dados
    ✓ Data e hora de modificação
    ✓ Hash SHA-256

    --------------------------------------------------

    • 2) PESQUISA

    Use o campo pesquisar para encontrar

    ✓ Nome do arquivo
    ✓ Extensão
    ✓ Caminho completo
    ✓ Data
    ✓ Tamanho
    ✓ Hash SHA-256

    --------------------------------------------------

    • 3) FILTROS

    Use o filtro para visualizar

    ✓ Todos os itens
    ✓ Apenas arquivos
    ✓ Apenas pastas
    ✓ Tipos específicos:

    .EXE
    .DLL
    .PDF
    .ZIP
    .RAR
    .JPG
    .TXT
    .PY
    .BAT
    entre outros

    --------------------------------------------------

    • 4) HASH SHA-256

    A coluna SHA-256 mostra a identificação
    única do arquivo.

    Pode ser utilizada para

    ✓ Conferir integridade
    ✓ Detectar alterações
    ✓ Pesquisar arquivos no VirusTotal

    --------------------------------------------------

    • 5) BOTÃO DIREITO DO MOUSE

    Clique com botão direito em um arquivo

    ✓ Abrir arquivo
    ✓ Abrir localização
    ✓ Abrir no VirusTotal
    ✓ Copiar selecionado
    ✓ Excluir arquivo

    --------------------------------------------------

    • 6) SELEÇÃO DE ARQUIVOS

    Atalhos

    CTRL + A

    Seleciona todos os itens.

    Mouse

    Clique e arraste para selecionar vários arquivos.

    --------------------------------------------------

    • 7) SEGURANÇA

    Recomendações

    ✓ Analise arquivos desconhecidos.
    ✓ Verifique hashes SHA-256.
    ✓ Consulte arquivos suspeitos no VirusTotal.
    ✓ Evite executar arquivos sem confirmação.

    --------------------------------------------------

    🛡️ EXPLORADOR DE PASTAS E ARQUIVOS DO WINDOWS 🛡️

    Ferramenta para análise

    investigação de arquivos e SHA-256  ✓ Pesquisar arquivos no VirusTotal

    """

        frame = tk.Frame(janela, bg="#000000")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        caixa = tk.Text(frame, bg="#111111", fg="#05fdf1", font=("Consolas", 11), wrap="word", yscrollcommand=scrollbar.set)
        caixa.pack(fill="both", expand=True)
        scrollbar.config(command=caixa.yview)
        caixa.insert("1.0", texto)
        caixa.config(state="disabled")

    def create_widgets(self):
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

        tk.Label(top_frame, text="Filtro:", bg="#000000", fg="#00ff00", font=("Consolas", 10)).pack(side="left", padx=(15, 5))
        filter_values = ["Tudo", "Arquivos", "Pastas"] + [ext.upper() for ext in self.extensions]
        self.filter_combo = ttk.Combobox(top_frame, textvariable=self.filter_type, 
                                        values=filter_values, state="readonly", width=14, font=("Consolas", 10))
        self.filter_combo.pack(side="left", padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # Botão Copiar Tudo sempre visível
        self.copy_all_btn = tk.Button(top_frame, text="Copiar Tudo", command=self.copy_everything,
                                     width=12, bg="#ff00ff", fg="#000000", font=("Consolas", 10, "bold"))
        self.copy_all_btn.pack(side="left", padx=5)

        tk.Button(top_frame, text="Copiar Arquivos", command=self.copy_all,
                  width=15, bg="#ff8800", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        tk.Button(top_frame, text="Copiar Selecionado", command=self.copy_selected,
                  width=22, bg="#ff5500", fg="#000000", font=("Consolas", 10, "bold")).pack(side="left", padx=5)

        # Botão do Guia
        tk.Button(self.root, text="📖 GUIA RÁPIDO DE UTILIZAÇÃO", command=self.open_guide,
                  bg="#0066cc", fg="#ffffff", font=("Consolas", 10, "bold"), width=35, height=2).pack(side="bottom", pady=8)

        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # Resumo
        self.summary_frame = tk.Frame(self.root, bg="#001100", height=32)
        self.summary_frame.pack(fill="x", padx=10, pady=(0, 5))
        self.summary_frame.pack_propagate(False)

        self.summary_var = tk.StringVar(value="Contém: 0 Arquivos | 0 Pastas | Tamanho: 0 B | Total: 0 itens")
        self.summary_label = tk.Label(self.summary_frame, textvariable=self.summary_var,
                                     bg="#001100", fg="#00ff88", font=("Consolas", 11, "bold"), anchor="w", padx=12)
        self.summary_label.pack(fill="both", expand=True)

        # Pesquisa
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

        columns = ("nome", "tipo", "tamanho", "data", "horas", "hash", "caminho")
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background="#000000", foreground="#00ff00", fieldbackground="#000000", rowheight=28, font=("Consolas", 10))
        style.map("Treeview", background=[('selected', '#003300')], foreground=[('selected', '#ffffff')])
        style.configure("Treeview.Heading", background="#001100", foreground="#00ff00", font=("Consolas", 10, "bold"))

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")

        headers = ["Nome", "Tipo", "Tamanho", "Data", "Hora", "Hash SHA-256", "Caminho Completo"]
        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text)

        self.tree.column("nome", width=550)
        self.tree.column("tipo", width=100)
        self.tree.column("tamanho", width=120)
        self.tree.column("data", width=110)
        self.tree.column("horas", width=120)
        self.tree.column("hash", width=520)
        self.tree.column("caminho", width=1200)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<ButtonPress-1>", self.on_mouse_press)
        self.tree.bind("<B1-Motion>", self.on_mouse_drag)
        self.tree.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.open_item())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Control-a>", self.select_all)

    def on_filter_change(self, event=None):
        """Botão 'Copiar Tudo' agora permanece sempre visível"""
        self.filter_items()

    def get_root_folder_size(self, folder_path):
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

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        items = [{"nome": v[0], "tipo": v[1], "caminho": v[6]} for iid in selected if (v := self.tree.item(iid)["values"])]
        if not items: return
        if not messagebox.askyesno("Confirmar Exclusão", f"Excluir {len(items)} items?", icon="warning"):
            return
        deletados = 0
        for item in items:
            try:
                path = Path(item["caminho"])
                if item["tipo"] == "Pasta":
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
                deletados += 1
            except: pass
        messagebox.showinfo("Concluído", f"{deletados} itens excluídos.")
        self.filter_items()

    def on_mouse_press(self, event): self.drag_start = self.tree.identify_row(event.y)
    def on_mouse_drag(self, event):
        current = self.tree.identify_row(event.y)
        if current and self.drag_start:
            try:
                children = self.tree.get_children()
                start = children.index(self.drag_start)
                end = children.index(current)
                if start > end: start, end = end, start
                self.tree.selection_set(children[start:end+1])
            except: pass
    def on_mouse_release(self, event): self.drag_start = None
    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

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
        self.summary_var.set("Calculando tamanho da pasta...")
        self.status_var.set("Iniciando varredura...")

        Thread(target=self.scan_with_progress, args=(folder,), daemon=True).start()

    def scan_with_progress(self, root_folder):
        self.root_folder_size = self.get_root_folder_size(root_folder)
        total_items = 0
        try:
            for _, pastas, arquivos in os.walk(root_folder):
                total_items += len(arquivos) + len(pastas)
        except: pass

        if total_items == 0:
            self.root.after(0, lambda: self.finish_scan([]))
            return

        items = []
        processed = 0
        for raiz, pastas, arquivos in os.walk(root_folder):
            for arq in arquivos:
                caminho = os.path.join(raiz, arq)
                try:
                    tamanho = os.path.getsize(caminho)
                    dt = datetime.fromtimestamp(os.path.getmtime(caminho))
                    sha = get_sha256(caminho)
                    items.append({
                        "nome": arq,
                        "tipo": get_file_type(arq, True),
                        "tamanho": tamanho,
                        "data": dt.strftime("%d/%m/%Y"),
                        "horas": dt.strftime("%H:%M:%S"),
                        "hash": sha,
                        "caminho": caminho,
                        "ext": os.path.splitext(arq)[1].lower()
                    })
                except: pass
                processed += 1
                self.root.after(0, lambda p=int((processed/total_items)*100): self.update_progress(p))

            for pasta in pastas:
                caminho_pasta = os.path.join(raiz, pasta)
                try:
                    dt = datetime.fromtimestamp(os.path.getmtime(caminho_pasta))
                    tamanho = self.get_root_folder_size(caminho_pasta)
                    items.append({
                        "nome": pasta,
                        "tipo": "Pasta",
                        "tamanho": tamanho,
                        "data": dt.strftime("%d/%m/%Y"),
                        "horas": dt.strftime("%H:%M:%S"),
                        "hash": "—",
                        "caminho": caminho_pasta,
                        "ext": ""
                    })
                except: pass
                processed += 1
                self.root.after(0, lambda p=int((processed/total_items)*100): self.update_progress(p))

        items.sort(key=lambda x: (x["tipo"] != "Pasta", -x.get("tamanho", 0)))
        self.root.after(0, lambda: self.finish_scan(items))

    def update_progress(self, value):
        self.progress["value"] = value
        self.status_var.set(f"Escaneando... {value}%")

    def finish_scan(self, items):
        self.all_items = items
        self.populate_tree(items)

    def populate_tree(self, items):
        self.tree.delete(*self.tree.get_children())
        num_arquivos = sum(1 for item in items if item["tipo"] != "Pasta")
        num_pastas = len(items) - num_arquivos

        for item in items:
            self.tree.insert("", "end", values=(
                item["nome"], item["tipo"], format_size(item.get("tamanho", 0)),
                item["data"], item["horas"], item.get("hash", "—"), item["caminho"]
            ))

        self.summary_var.set(
            f"Contém: {num_arquivos} Arquivos | {num_pastas} Pastas | "
            f"Tamanho: {format_size(self.root_folder_size)} | Total: {len(items)} itens"
        )
        self.status_var.set("Varredura concluída!")

    def filter_items(self):
        search_term = self.search_var.get().strip().lower()
        filtro = self.filter_type.get()
        filtered = []

        for item in self.all_items:
            pasta = os.path.basename(os.path.dirname(item["caminho"]))
            texto = " ".join([
                item["nome"], item.get("hash", ""), pasta, item["tipo"],
                item["data"], item["horas"], item["caminho"],
                item.get("ext", ""), format_size(item.get("tamanho", 0))
            ]).lower()

            pesquisa_ok = search_term == "" or search_term in texto
            filtro_ok = (
                filtro == "Tudo" or
                (filtro == "Arquivos" and item["tipo"] != "Pasta") or
                (filtro == "Pastas" and item["tipo"] == "Pasta") or
                (filtro not in ["Tudo", "Arquivos", "Pastas"] and 
                 item.get("ext", "").lower() == filtro.lower())
            )

            if pesquisa_ok and filtro_ok:
                filtered.append(item)

        self.populate_tree(filtered)

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
            except: pass
        messagebox.showinfo("Sucesso", f"{copiados} itens copiados")

    def copy_all(self):
        self._copy_items([item for item in self.all_items if item["tipo"] != "Pasta"])

    def copy_selected(self):
        items = [{"nome": v[0], "caminho": v[6], "tipo": v[1]} 
                 for iid in self.tree.selection() if (v := self.tree.item(iid)["values"])]
        self._copy_items(items)

    def _copy_items(self, items_list):
        if not items_list:
            messagebox.showwarning("Aviso", "Nenhum item selecionado")
            return
        destino = filedialog.askdirectory(title="Pasta de Destino")
        if not destino: return
        copiados = 0
        for item in items_list:
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
            except: pass
        messagebox.showinfo("Sucesso", f"{copiados} itens copiados")

    def open_item(self):
        sel = self.tree.selection()
        if sel:
            try:
                os.startfile(self.tree.item(sel[0])["values"][6])
            except:
                messagebox.showerror("Erro", "Não foi possível abrir o item.")

    def open_file_folder(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][6]
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            try:
                os.startfile(folder)
            except: pass

    def open_in_virustotal(self):
        sel = self.tree.selection()
        if not sel: return
        values = self.tree.item(sel[0])["values"]
        hash_val = values[5]
        if hash_val == "—" or hash_val == "Erro ao calcular" or len(hash_val) != 64:
            messagebox.showwarning("Aviso", "Hash SHA-256 inválido ou item é uma pasta.")
            return
        url = f"https://www.virustotal.com/gui/file/{hash_val}"
        webbrowser.open(url)

    def show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 10), bg="#1e1e1e", fg="#ffffff",
                          activebackground="#0078d4", activeforeground="#ffffff", relief="flat", bd=1)
            menu.add_command(label=" Abrir", command=self.open_item, background="#06033A", foreground="#ffffff")
            menu.add_command(label=" Abrir Pasta", command=self.open_file_folder, background="#06033A", foreground="#ffffff")
            menu.add_command(label=" Abrir no VirusTotal", command=self.open_in_virustotal,
                           background="#06033A", foreground="#00ffcc")
            menu.add_separator()
            menu.add_command(label=" Copiar Selecionado", command=self.copy_selected,
                           background="#1e1e1e", foreground="#ffffff")
            menu.add_command(label=" Excluir", command=self.delete_selected,
                           background="#1e1e1e", foreground="#ff5555")
            menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileFinder(root)
    root.mainloop()
