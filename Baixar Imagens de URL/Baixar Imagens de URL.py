import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
from io import BytesIO
from PIL import Image
import os
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ImageDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Baixar Imagens de URL em .txt ou .html e Salvar como PNG")
        self.root.geometry("820x730")

        self.urls = []
        self.output_dir = ""
        self.base_url = ""

        # Seleção de arquivo
        tk.Label(root, text="Selecione o arquivo (.txt ou .html) com as URL").pack(pady=5)
        self.file_label = tk.Label(root, text="Nenhum arquivo selecionado")
        self.file_label.pack(pady=5)
        tk.Button(root, text="Selecionar Arquivo", bg="#f5ad05", fg="black", command=self.select_file).pack(pady=5)

        # Seleção de pasta
        tk.Label(root, text="Selecione a pasta para salvar as imagens PNG").pack(pady=5)
        self.folder_label = tk.Label(root, text="Nenhuma pasta selecionada")
        self.folder_label.pack(pady=5)
        tk.Button(root, text="Selecionar Pasta", bg="#4df7f5", fg="black", command=self.select_output_folder).pack(pady=5)

        # Botão processar
        tk.Button(root, text="Processar e Baixar Imagens", bg="#03fc24", fg="black", command=self.start_process_thread).pack(pady=10)

        # Barra de progresso
        self.progress = ttk.Progressbar(root, orient="horizontal", length=700, mode="determinate")
        self.progress.pack(pady=10)

        # Caixa de logs
        self.log_box = scrolledtext.ScrolledText(root, width=95, height=25)
        self.log_box.pack(pady=5)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text or HTML files", "*.txt *.html")])
        if file_path:
            self.file_label.config(text=f"Arquivo: {file_path}")
            try:
                ext = os.path.splitext(file_path)[1].lower()
                self.urls = []
                if ext == ".txt":
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.urls = [line.strip() for line in f.readlines() if line.strip()]
                elif ext == ".html":
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    soup = BeautifulSoup(content, "html.parser")

                    # pega base_url se existir
                    meta_url = soup.find("meta", property="og:url")
                    self.base_url = meta_url["content"] if meta_url else ""

                    # coleta imagens
                    img_tags = [img.get("src") for img in soup.find_all("img")]
                    link_imgs = [link.get("href") for link in soup.find_all("link", {"as": "image"})]
                    meta_imgs = [meta.get("content") for meta in soup.find_all("meta", {"property": ["og:image","twitter:image"]})]

                    raw_urls = img_tags + link_imgs + meta_imgs
                    self.urls = [urljoin(self.base_url, u) for u in raw_urls if u]

                # remove duplicadas
                self.urls = list(dict.fromkeys(self.urls))

                self.add_log(f"{len(self.urls)} URL carregadas do arquivo.")
            except:
                self.urls = []

    def select_output_folder(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.folder_label.config(text=f"Pasta: {self.output_dir}")

    def start_process_thread(self):
        if not self.urls:
            messagebox.showwarning("Aviso", "Selecione um arquivo com URLs primeiro.")
            return
        if not self.output_dir:
            messagebox.showwarning("Aviso", "Selecione uma pasta de saída primeiro.")
            return
        threading.Thread(target=self.process, daemon=True).start()

    def add_log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def update_progress(self, value):
        self.progress["value"] = value

    def process(self):
        total = len(self.urls)
        self.root.after(0, lambda: self.progress.config(maximum=total))
        self.root.after(0, lambda: self.update_progress(0))
        self.add_log("\nIniciando download das imagens...\n")

        for i, url in enumerate(self.urls, start=1):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    file_path = os.path.join(self.output_dir, f"image_{i}.png")
                    img.save(file_path, "PNG")
                    self.add_log(f"[{i}/{total}] Salva: {file_path}")
                else:
                    self.add_log(f"[{i}/{total}] Falha ao baixar {url}")
            except:
                pass
            self.root.after(0, lambda val=i: self.update_progress(val))

        self.add_log("\nProcesso finalizado.\n")
        messagebox.showinfo("Conclusão", "Todos os downloads foram processados.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDownloader(root)
    root.mainloop()
