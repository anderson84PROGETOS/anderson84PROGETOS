import os
import sys
import threading
import queue
import requests
from bs4 import BeautifulSoup
from tkinter import Tk, StringVar, Text, END, DISABLED, NORMAL
from tkinter import filedialog, messagebox
from tkinter import ttk

# Tenta importar yt_dlp
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

APP_TITLE = "Pinterest Video e Foto Downloader"
DEFAULT_TEMPLATE = "%(title)s.%(ext)s"

class DownloaderGUI:
    def __init__(self, master: Tk):
        self.master = master
        master.title(APP_TITLE)
        master.geometry("1200x800")
        master.minsize(640, 480)

        # Vars
        self.url_var = StringVar()
        self.outdir_var = StringVar(value="")  # Nenhum valor padrão
        self.template_var = StringVar(value=DEFAULT_TEMPLATE)
        self.format_var = StringVar(value="video")  # Opção padrão: vídeo        

        # Queue para logs/thread-safe
        self.log_queue = queue.Queue()

        # Thread de download
        self.worker = None
        self.cancel_flag = False

        # Layout
        self._build_widgets()

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 8}

        # URL
        frm_url = ttk.Frame(self.master)
        frm_url.pack(fill="x", **pad)
        ttk.Label(frm_url, text="URL do Pinterest (vídeo ou foto)").pack(anchor="w")
        self.ent_url = ttk.Entry(frm_url, textvariable=self.url_var)
        self.ent_url.pack(fill="x")

        # Tipo de mídia
        frm_type = ttk.Frame(self.master)
        frm_type.pack(fill="x", **pad)
        ttk.Label(frm_type, text="Tipo de mídia").pack(anchor="w")
        ttk.Radiobutton(frm_type, text="Vídeo", variable=self.format_var, value="video").pack(side="left", padx=5)
        ttk.Radiobutton(frm_type, text="Imagem", variable=self.format_var, value="image").pack(side="left", padx=5)

        # Pasta de saída
        frm_out = ttk.Frame(self.master)
        frm_out.pack(fill="x", **pad)
        ttk.Label(frm_out, text="Pasta de Destino").pack(anchor="w")
        row_out = ttk.Frame(frm_out)
        row_out.pack(fill="x")
        self.ent_outdir = ttk.Entry(row_out, textvariable=self.outdir_var)
        self.ent_outdir.pack(side="left", fill="x", expand=True)
        ttk.Button(row_out, text="Escolher…", command=self._choose_dir).pack(side="left", padx=6)

        # Template de arquivo
        frm_tmpl = ttk.Frame(self.master)
        frm_tmpl.pack(fill="x", **pad)
        ttk.Label(frm_tmpl, text="Nome do arquivo (template yt-dlp para vídeos)").pack(anchor="w")
        self.ent_tmpl = ttk.Entry(frm_tmpl, textvariable=self.template_var)
        self.ent_tmpl.pack(fill="x")
        ttk.Label(frm_tmpl, text="Ex.: %(title)s.%(ext)s  |  %(uploader)s - %(title)s.%(ext)s").pack(anchor="w")

        # Progresso
        frm_prog = ttk.Frame(self.master)
        frm_prog.pack(fill="x", **pad)
        ttk.Label(frm_prog, text="Progresso").pack(anchor="w")
        self.pbar = ttk.Progressbar(frm_prog, orient="horizontal", length=100, mode="determinate")
        self.pbar.pack(fill="x")
        self.lbl_status = ttk.Label(frm_prog, text="Aguardando…")
        self.lbl_status.pack(anchor="w")

        # Botões
        frm_btn = ttk.Frame(self.master)
        frm_btn.pack(fill="x", **pad)
        self.btn_start = ttk.Button(frm_btn, text="Baixar", command=self.start_download)
        self.btn_start.pack(side="left")
        self.btn_cancel = ttk.Button(frm_btn, text="Cancelar", command=self.cancel_download, state=DISABLED)
        self.btn_cancel.pack(side="left", padx=6)

        # Log
        frm_log = ttk.Frame(self.master)
        frm_log.pack(fill="both", expand=True, **pad)
        ttk.Label(frm_log, text="Log").pack(anchor="w")
        self.txt_log = Text(frm_log, height=10, wrap="word")
        self.txt_log.pack(fill="both", expand=True)

        # Estilo
        try:
            self.master.call("tk", "scaling", 1.2)
        except Exception:
            pass

        # Atualizador do log
        self.master.after(100, self._drain_logs)

    def _choose_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.outdir_var.get())
        if chosen:
            self.outdir_var.set(chosen)

    def log(self, msg: str):
        self.log_queue.put(msg)

    def _drain_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.txt_log.configure(state=NORMAL)
                self.txt_log.insert(END, msg + "\n")
                self.txt_log.configure(state=DISABLED)
                self.txt_log.see(END)
        except queue.Empty:
            pass
        self.master.after(100, self._drain_logs)

    def set_progress(self, percent: float, status: str):
        self.pbar["value"] = max(0, min(100, percent))
        self.lbl_status.configure(text=status)
        self.master.update_idletasks()

    def start_download(self):
        if yt_dlp is None:            
            return

        url = self.url_var.get().strip()
        outdir = self.outdir_var.get().strip()
        tmpl = self.template_var.get().strip() or DEFAULT_TEMPLATE
        media_type = self.format_var.get()

        if not url:
            messagebox.showwarning("URL vazia", "Informe a URL do Pinterest.")
            return
        if not os.path.isdir(outdir):
            messagebox.showwarning("Pasta inválida", "Escolha uma pasta de destino válida.")
            return

        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Em execução", "Um download já está em andamento.")
            return

        self.btn_start.configure(state=DISABLED)
        self.btn_cancel.configure(state=NORMAL)
        self.set_progress(0, "Iniciando…")
        self.txt_log.configure(state=NORMAL)
        self.txt_log.delete("1.0", END)
        self.txt_log.configure(state=DISABLED)

        self.worker = threading.Thread(target=self._download_thread, args=(url, outdir, tmpl, media_type), daemon=True)
        self.worker.start()

    def cancel_download(self):
        self.cancel_flag = True
        self.log("Cancelando… (pode demorar alguns segundos)")

    def _download_thread(self, url: str, outdir: str, tmpl: str, media_type: str):
        self.cancel_flag = False

        def hook(d):
            if self.cancel_flag:
                raise KeyboardInterrupt("Cancelado pelo usuário.")
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100) if total else 0
                spd = d.get("speed") or 0
                eta = d.get("eta") or 0
                self.set_progress(percent, f"Baixando… {percent:.1f}% | {self._fmt_size(downloaded)} de {self._fmt_size(total)} | {self._fmt_speed(spd)} | ETA {self._fmt_time(eta)}")
            elif d["status"] == "finished":
                self.set_progress(100, "Processando arquivo…")
                self.log("\n\nDownload concluído, finalizando\n\n")

        # Configurações base para yt-dlp
        ydl_opts = {
            "outtmpl": os.path.join(outdir, tmpl),
            "progress_hooks": [hook],
            "concurrent_fragment_downloads": 4,
            "noprogress": True,
            "quiet": True,
            "nopart": False,
            "retries": 5,
            "skip_download": False,
            "ignoreerrors": True,
        }

        # Ajusta opções com base no tipo de mídia
        if media_type == "video":
            ydl_opts["format"] = "bv"  # Somente o melhor stream de vídeo, sem áudio
            try:
                self.log(f"baixar vídeo de: {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                if info:
                    out = ydl.prepare_filename(info)
                    self.log(f"✅ Vídeo salvo em: {out}")
            except Exception as e:
                self.log(f"ℹ️ Erro ao baixar vídeo: {e}")
        else:  # Imagem
            try:
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    img_tag = soup.find("meta", property="og:image")
                    if img_tag and img_tag.get("content"):
                        img_url = img_tag["content"]
                        self.log(f"Imagem encontrada: {img_url}")
                        img_data = requests.get(img_url).content
                        filename = os.path.join(outdir, "pinterest_image.png")
                        with open(filename, "wb") as f:
                            f.write(img_data)
                        self.log(f"\n✅ Imagem salva em: {filename}")
                    else:
                        self.log("ℹ️ Nenhuma imagem encontrada na página.")
                else:
                    self.log(f"ℹ️ Falha ao acessar a URL: Status {resp.status_code}")
            except Exception as e:
                self.log(f"ℹ️ Erro ao baixar imagem: {e}")

        self.set_progress(100, "Concluído!")
        self.btn_start.configure(state=NORMAL)
        self.btn_cancel.configure(state=DISABLED)        

    @staticmethod
    def _fmt_size(n: int) -> str:
        try:
            n = float(n)
        except Exception:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while n >= 1024 and i < len(units) - 1:
            n /= 1024.0
            i += 1
        return f"{n:.2f} {units[i]}"

    @staticmethod
    def _fmt_speed(n: float) -> str:
        try:
            return f"{DownloaderGUI._fmt_size(n)}/s"
        except Exception:
            return "0 B/s"

    @staticmethod
    def _fmt_time(t: float) -> str:
        try:
            t = int(t)
        except Exception:
            return "--:--"
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

def main():
    root = Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = DownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    if yt_dlp is None:        
        sys.exit(1)
    main()
