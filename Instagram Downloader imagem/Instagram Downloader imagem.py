import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import instaloader
import os
import sys
import threading
import time
import traceback
import re

class TextRedirector:
    """Redireciona print() para o ScrolledText, formatando arquivos .jpg/.jpeg como 'Imagem Baixada:'"""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag
        # Ignorar apenas mensagens irrelevantes do Instaloader (HTTP 403, JSON Query)
        self.ignore_patterns = [
            "Unable to fetch high quality",
            "could also be downloaded anonymously",
            "Retrieving posts from profile",
            "HTTP error code 403",
            "JSON Query to apiImagem Baixada",
        ]

    def write(self, msg):
        msg = msg.strip()
        if not msg:
            return
        # Ignora mensagens irrelevantes
        for pattern in self.ignore_patterns:
            if pattern in msg:
                return
        # Se for um arquivo .jpg ou .jpeg, mostra com 'Imagem Baixada:'
        if msg.lower().endswith(('.jpg', '.jpeg')):
            msg = os.path.basename(msg)
            msg = f"Imagem Baixada: {msg}"

        # Insere no ScrolledText
        self.widget.insert(tk.END, msg + "\n\n")
        self.widget.see(tk.END)

    def flush(self):
        pass  

class InstagramDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Downloader")
        self.root.geometry("1220x650")
        root.state('zoomed')
        self.folder = None
        self.downloading = False
        self.total_posts = 0

        # Entrada URL
        tk.Label(root, text="URL do Perfil do Instagram").pack(pady=5)
        self.entry_url = tk.Entry(root, width=60)
        self.entry_url.pack(pady=5)

        # Entrada usuário
        tk.Label(root, text="Usuário do Instagram").pack(pady=5)
        self.entry_user = tk.Entry(root, width=60)
        self.entry_user.pack(pady=5)

        # Entrada senha
        tk.Label(root, text="Senha do Instagram").pack(pady=5)
        self.entry_pass = tk.Entry(root, width=60, show="*")
        self.entry_pass.pack(pady=5)

        # Botão para escolher pasta
        self.btn_choose_folder = tk.Button(root, text="Escolher Pasta", command=self.choose_folder)
        self.btn_choose_folder.pack(pady=5)

        # Botão download
        self.btn_download = tk.Button(root, text="Baixar Fotos", command=self.start_download_thread)
        self.btn_download.pack(pady=10)

        # Barra de progresso
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", maximum=100)
        self.progress.pack(pady=10)

        # Área de log
        tk.Label(root, text="\nLog de Execução").pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(root, width=150, height=35)
        self.log_area.pack(pady=5)

        # Redirecionar stdout/stderr
        sys.stdout = TextRedirector(self.log_area, "stdout")
        sys.stderr = TextRedirector(self.log_area, "stderr")

    def choose_folder(self):
        self.folder = filedialog.askdirectory()
        if self.folder:
            print(f"\n[INFO] Pasta escolhida: {self.folder}")

    def start_download_thread(self):
        if self.downloading:
            messagebox.showwarning("Aviso", "Um download já está em andamento!")
            return

        url = self.entry_url.get().strip()
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not url:
            messagebox.showerror("Erro", "Por favor, insira a URL do perfil do Instagram.")
            return
        if not self.folder:
            messagebox.showerror("Erro", "Por favor, escolha uma pasta para salvar as fotos.")
            return
        if not username or not password:
            messagebox.showerror("Erro", "Por favor, insira usuário e senha do Instagram.")
            return

        self.downloading = True
        self.btn_download.config(state="disabled")
        self.progress["value"] = 0
        self.total_posts = 0

        download_thread = threading.Thread(target=self.download_photos, daemon=True)
        progress_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        download_thread.start()
        progress_thread.start()

        self.root.after(100, self.check_threads, download_thread, progress_thread)

    def check_threads(self, download_thread, progress_thread):
        if download_thread.is_alive() or progress_thread.is_alive():
            self.root.update()
            self.root.after(100, self.check_threads, download_thread, progress_thread)
        else:
            self.progress["value"] = 100
            self.btn_download.config(state="normal")
            self.downloading = False

    def monitor_progress(self):
        while self.downloading:
            if self.total_posts > 0:
                target_dir = os.path.join(self.folder, self.entry_url.get().strip().rstrip("/").split("/")[-1])
                if os.path.exists(target_dir):
                    downloaded_files = len([f for f in os.listdir(target_dir) if f.lower().endswith(('.jpg', '.jpeg'))])
                    percentage = min((downloaded_files / self.total_posts) * 100, 100)
                    self.root.after(0, lambda p=percentage: self.progress.config(value=p))
            time.sleep(1)

    def download_photos(self):
        try:
            url = self.entry_url.get().strip()
            ig_user = self.entry_user.get().strip()
            ig_pass = self.entry_pass.get().strip()
            username = url.rstrip("/").split("/")[-1]

            loader = instaloader.Instaloader(
                dirname_pattern=os.path.join(self.folder, "{target}"),
                download_videos=False,
                download_comments=False,
                save_metadata=False,
                post_metadata_txt_pattern=""
            )

            # Headers para evitar erro 403
            loader.context._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })

            print(f"[INFO] Fazendo login em: @{ig_user}")
            loader.login(ig_user, ig_pass)

            profile = instaloader.Profile.from_username(loader.context, username)
            self.total_posts = profile.mediacount
            print(f"\n[INFO] Total de posts a baixar: {self.total_posts}")

            print(f"\n[INFO] Baixando fotos de: @{username}")
            loader.download_profile(profile.username, profile_pic_only=False)

            print(f"\n[OK] Fotos de @{username} salvas em: {self.folder}")
            self.root.after(0, lambda: messagebox.showinfo("\nConcluído", f"Fotos de @{username} salvas em: {self.folder}"))

        except instaloader.exceptions.LoginRequiredException:
            print("[ERRO] Login falhou: usuário ou senha incorretos.")
        except instaloader.exceptions.ConnectionException as ce:
            print(f"[ERRO] Problema de conexão: {ce}")
        except Exception as e:
            print(f"[ERRO] Ocorreu um erro inesperado:\n{traceback.format_exc()}")
        finally:
            self.downloading = False
            self.btn_download.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDownloader(root)
    root.mainloop()
