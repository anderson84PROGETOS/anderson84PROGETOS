import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import requests

class DirbLikeApp:
    def __init__(self, master):
        self.master = master
        master.title("Scan Fuzz")
        root.geometry("1180x910")

        frm = ttk.Frame(master, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Digite a url do website (ex: https://exemplo.com.br)", font=("Arial", 12)).pack(pady=10)
        self.url_entry = ttk.Entry(frm, width=40, font=("Arial", 12))
        self.url_entry.pack(pady=5)

        # Frame com os botões
        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Iniciar Scan", bg="#03fc24", fg="black", command=self.start_scan).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Carregar wordlist", bg="#05e6ff", fg="black", command=self.load_wordlist).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Salvar resultados", bg="#ff8c00", fg="black", command=self.save_results).pack(side="left", padx=5)

        # **Novo label para mostrar quantas entradas foram carregadas**
        self.wordlist_status = tk.Label(frm, text="Nenhuma wordlist carregada.", anchor="w", font=("Arial", 11))
        self.wordlist_status.pack(pady=(2, 8))  # um pouco de espaçamento

        self.progress = ttk.Progressbar(frm, mode="determinate", length=600)
        self.progress.pack(pady=5)

        self.status_label = tk.Label(frm, text="Aguardando início...", anchor="w", font=("Arial", 12))
        self.status_label.pack(pady=(5,0))

        self.text_area = scrolledtext.ScrolledText(frm, width=120, height=35, font=("Arial", 12))
        self.text_area.pack(pady=10)

        self.wordlist = []

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

    def load_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist", filetypes=[("Text files","*.txt")]
        )
        if path:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
            # Atualiza label logo abaixo dos botões
            self.wordlist_status.config(text=f"Wordlist carregada: {len(self.wordlist)} Entradas")
            

    def start_scan(self):
        target = self.url_entry.get().strip()
        if not target:
            messagebox.showwarning("Aviso", "Informe a URL alvo.")
            return
        if not self.wordlist:
            messagebox.showwarning("Aviso", "Carregue uma wordlist.")
            return
        self.text_area.delete("1.0", tk.END)
        self.status_label.config(text="Iniciando scan…")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.wordlist)
        threading.Thread(target=self.scan, args=(target,), daemon=True).start()

    def scan(self, target):
        for idx, word in enumerate(self.wordlist, start=1):
            url = f"{target.rstrip('/')}/{word}"

            self.status_label.config(text=f"Testando: {url}", font=("Arial", 12))
            self.master.update_idletasks()

            try:
                r = requests.get(url, timeout=5, headers=self.headers)
                if r.status_code == 200:
                    self.text_area.insert(tk.END, f"[200] {url}\n")
                elif r.status_code in (301, 302):
                    self.text_area.insert(tk.END, f"[{r.status_code}] {url}\n")
            except requests.RequestException:
                pass

            self.progress["value"] = idx

        self.status_label.config(text="Scan finalizado.")

    def save_results(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Salvar resultados como"
        )
        if path:
            try:
                content = self.text_area.get("1.0", tk.END).strip()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Salvar resultados", f"Resultados salvos em\n\n{path}")
            except Exception as e:
                messagebox.showerror("Erro ao salvar", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = DirbLikeApp(root)
    root.mainloop()  
