import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
import subprocess
import os
import requests
import socket
import threading

class ProxyBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Abrir Navegador Proxy")
        self.root.geometry("920x550")
        self.root.configure(bg="#1e1e1e")

        self.proxies = []
        self.proxies_display = []

        # Título
        tk.Label(root, text="Abrir Navegador com Proxy", font=("Consolas", 16, "bold"),
                 fg="#00ff00", bg="#1e1e1e").pack(pady=10)

        # Botão carregar proxies.txt
        tk.Button(root, text="📂 Carregar proxies.txt", font=("Consolas", 11, "bold"),
                  bg="#0066cc", fg="white", command=self.load_proxies,
                  width=25).pack(pady=5)

        # Lista de proxies
        frame_list = tk.Frame(root, bg="#1e1e1e")
        frame_list.pack(pady=5, fill=tk.BOTH, expand=True)

        scrollbar = Scrollbar(frame_list)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = Listbox(frame_list, font=("Consolas", 10),
                               bg="#2d2d2d", fg="#00ff00",
                               selectbackground="#00aa00",
                               yscrollcommand=scrollbar.set, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.config(command=self.listbox.yview)

        # Site
        frame_site = tk.Frame(root, bg="#1e1e1e")
        frame_site.pack(pady=10)

        tk.Label(frame_site, text="Site:", font=("Consolas", 11),
                 fg="white", bg="#1e1e1e").pack(side=tk.LEFT, padx=5)

        self.site_entry = tk.Entry(frame_site, width=40, font=("Consolas", 11),
                                   bg="#2d2d2d", fg="#00ff00", insertbackground="white")
        self.site_entry.pack(side=tk.LEFT)
        self.site_entry.insert(0, "whatismyip.com.br")

        # Botões de abrir
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="🌐 Abrir no Chromium", font=("Consolas", 11, "bold"),
                  bg="#00aa00", fg="black", width=22,
                  command=lambda: self.open_browser("chromium")).pack(side=tk.LEFT, padx=8)

        tk.Button(btn_frame, text="🦊 Abrir no Firefox", font=("Consolas", 11, "bold"),
                  bg="#ff6600", fg="black", width=20,
                  command=lambda: self.open_browser("firefox")).pack(side=tk.LEFT, padx=8)

    def get_country(self, ip):
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode", timeout=5)
            data = r.json()
            if data.get("country"):
                return f"{data['country']} ({data.get('countryCode', '')})"
        except:
            pass
        return "Desconhecido"

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ""

    def load_proxies(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o proxies.txt",
            filetypes=[("Arquivo de Texto", "*.txt")]
        )
        if not file_path:
            return

        self.proxies = []
        self.proxies_display = []
        self.listbox.delete(0, tk.END)

        with open(file_path, "r") as f:
            lines = [line.strip() for line in f if line.strip() and ":" in line]

        if not lines:
            messagebox.showwarning("Aviso", "Nenhum proxy válido encontrado no arquivo.")
            return

        self.listbox.insert(tk.END, "Carregando país e hostname, aguarde...")
        self.root.update()

        def process():
            self.listbox.delete(0, tk.END)
            for proxy in lines:
                ip = proxy.split(":")[0]
                country = self.get_country(ip)
                hostname = self.get_hostname(ip)
                display = f"{proxy:<25} | {country:<25} | {hostname}"
                
                self.proxies.append(proxy)
                self.proxies_display.append(display)
                self.listbox.insert(tk.END, display)
                self.root.update_idletasks()

            messagebox.showinfo("Sucesso", f"{len(self.proxies)} proxies carregados!")

        threading.Thread(target=process, daemon=True).start()

    def open_browser(self, browser):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um proxy na lista!")
            return

        proxy = self.proxies[selection[0]]
        site = self.site_entry.get().strip()

        if not site:
            messagebox.showwarning("Aviso", "Digite um site!")
            return

        if not site.startswith("http"):
            site = "http://" + site

        try:
            if browser == "chromium":
                cmd = [
                    "chromium",
                    f"--proxy-server=http://{proxy}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    site
                ]
                try:
                    subprocess.Popen(cmd)
                except FileNotFoundError:
                    cmd[0] = "google-chrome"
                    subprocess.Popen(cmd)

            elif browser == "firefox":
                env = os.environ.copy()
                env["http_proxy"] = f"http://{proxy}"
                env["https_proxy"] = f"http://{proxy}"
                env["HTTP_PROXY"] = f"http://{proxy}"
                env["HTTPS_PROXY"] = f"http://{proxy}"
                subprocess.Popen(["firefox", site], env=env)

            messagebox.showinfo("Aberto", f"Navegador aberto com proxy:\n{proxy}")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o navegador.\n\nErro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyBrowser(root)
    root.mainloop()
