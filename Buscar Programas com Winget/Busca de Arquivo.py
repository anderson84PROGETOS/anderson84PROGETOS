import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

class FileSearcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Busca de Arquivo 🔎")
        self.root.geometry("700x550")
        self.root.configure(bg="#1e1e1e")
        root.state("zoomed")  # abre em tela cheia no Windows

        self.create_widgets()

    def create_widgets(self):
        # Label do nome do arquivo
        self.filename_label = tk.Label(self.root, text="💼 Nome Exato do Arquivo 💼", fg="white", bg="#1e1e1e")
        self.filename_label.pack(pady=(20, 5))
        self.filename_entry = tk.Entry(self.root, width=50)
        self.filename_entry.pack(pady=5)

        # Botão escolher diretório
        self.choose_dir_btn = tk.Button(self.root, text="📁 Escolher Diretório 📁", command=self.choose_directory)
        self.choose_dir_btn.pack(pady=5)

        # Label caminho selecionado
        self.path_label = tk.Label(self.root, text="", fg="yellow", bg="#1e1e1e")
        self.path_label.pack()

        # Botão buscar arquivo
        self.search_btn = tk.Button(self.root, text="🔍 Buscar Arquivo 🔎", command=self.search_thread)
        self.search_btn.pack(pady=10)

        # Barra de progresso fixa e sempre visível (logo após botão buscar)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(pady=(0, 10))
        self.progress['value'] = 0

        # Área de resultados com scroll, aparece sempre abaixo da barra
        self.result_area = scrolledtext.ScrolledText(self.root, width=130, height=40, bg="#121212", fg="lime", font=("Courier", 9))
        self.result_area.pack(pady=10)

    def choose_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_label.config(text=f"📂 Diretório selecionado: {folder}")
            self.selected_path = folder

    def search_thread(self):
        thread = threading.Thread(target=self.search_file)
        thread.start()

    def search_file(self):
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Erro", "Você precisa digitar o nome do arquivo.")
            return

        path = getattr(self, "selected_path", "")
        if not os.path.exists(path):
            messagebox.showerror("Erro", "Você precisa escolher um diretório válido.")
            return

        self.result_area.delete("1.0", tk.END)
        self.result_area.insert(tk.END, f"🔍 Procurando por: {filename}\n\n")
        self.root.update()

        self.progress['value'] = 0

        encontrados = []
        lista_pastas = list(os.walk(path))
        total_pastas = len(lista_pastas)

        for i, (pasta_atual, _, arquivos) in enumerate(lista_pastas):
            if filename in arquivos:
                caminho_completo = os.path.join(pasta_atual, filename)
                encontrados.append(caminho_completo)

            # Atualiza a barra de progresso
            progresso = ((i + 1) / total_pastas) * 100
            self.progress['value'] = progresso
            self.root.update_idletasks()

        # NÃO esconde mais a barra de progresso, fica fixa

        if encontrados:
            self.result_area.insert(tk.END, "✅ Arquivo Encontrado\n\n")
            for item in encontrados:
                self.result_area.insert(tk.END, item + "\n")
        else:
            self.result_area.insert(tk.END, "\n❌ Arquivo não Encontrado.\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearcherGUI(root)
    root.mainloop()
