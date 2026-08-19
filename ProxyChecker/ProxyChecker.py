import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import threading
import requests
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProxyCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxy Checker")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")

        # Título
        tk.Label(root, text="Proxy Checker", font=("Consolas", 16, "bold"),
                 fg="#00ff00", bg="#1e1e1e").pack(pady=10)

        # Campo do site
        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(pady=5)

        tk.Label(frame, text="Site alvo:", font=("Consolas", 11),
                 fg="white", bg="#1e1e1e").pack(side=tk.LEFT, padx=5)

        self.site_entry = tk.Entry(frame, width=40, font=("Consolas", 11),
                                   bg="#2d2d2d", fg="#00ff00", insertbackground="white")
        self.site_entry.pack(side=tk.LEFT, padx=5)
        self.site_entry.insert(0, "")

        # Botões
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(
            btn_frame, text="▶ Iniciar Verificação", font=("Consolas", 11, "bold"),
            bg="#00aa00", fg="black", command=self.start_check,
            width=22, height=1
        )
        self.start_btn.pack(side=tk.LEFT, padx=8)

        self.stop_btn = tk.Button(
            btn_frame, text="■ Parar", font=("Consolas", 11),
            bg="#aa0000", fg="white", command=self.stop_check,
            width=12, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=8)

        self.save_btn = tk.Button(
            btn_frame, text="💾 Salvar .txt", font=("Consolas", 11, "bold"),
            bg="#0066cc", fg="black", command=self.save_proxies,
            width=14
        )
        self.save_btn.pack(side=tk.LEFT, padx=8)

        # Área de log
        self.log = scrolledtext.ScrolledText(
            root, width=150, height=40, font=("Consolas", 10),
            bg="black", fg="#00ff00", insertbackground="white"
        )
        self.log.pack(padx=10, pady=5)

        self.running = False
        self.success_count = 0
        self.success_proxies = []

    def log_msg(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def get_proxies(self):
        urls = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        ]
        proxies = set()
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                for line in r.text.strip().splitlines():
                    line = line.strip()
                    if ":" in line and not line.startswith("#"):
                        proxies.add(line)
            except:
                continue
        return list(proxies)

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
        """Resolve o nome do host (PTR)"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return ""

    def test_proxy(self, proxy, target):
        """Testa o proxy e rejeita se pedir senha"""
        if not self.running:
            return None
        try:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            r = requests.get(
                target,
                proxies=proxies,
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=True
            )
            if r.status_code == 407:
                return None
            if 200 <= r.status_code < 400:
                return proxy
        except requests.exceptions.ProxyError:
            return None
        except:
            pass
        return None

    def start_check(self):
        site = self.site_entry.get().strip()
        if not site:
            messagebox.showwarning("Aviso", "Digite um site!")
            return

        if not site.startswith("http"):
            site = "http://" + site

        self.running = True
        self.success_count = 0
        self.success_proxies = []
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)

        self.log_msg(f"[+] Alvo: {site}")
        self.log_msg("\n[+] Baixando lista de Proxies...")
        self.log_msg("\n[+] Filtrando apenas proxies SEM senha...\n")
        
        threading.Thread(target=self.run_check, args=(site,), daemon=True).start()

    def run_check(self, target):
        proxies = self.get_proxies()
        self.log_msg(f"[+] {len(proxies)} Proxies encontrados. Testando...\n")

        with ThreadPoolExecutor(max_workers=40) as executor:
            futures = {executor.submit(self.test_proxy, p, target): p for p in proxies}
            
            for future in as_completed(futures):
                if not self.running:
                    break
                result = future.result()
                if result:
                    self.success_count += 1
                    self.success_proxies.append(result)
                    ip = result.split(":")[0]
                    country = self.get_country(ip)
                    hostname = self.get_hostname(ip)
                    self.log_msg(f"[ SUCCESS ] -> {result:<30} {country:<30} {hostname}")

        self.log_msg(f"\n[+] Finalizado! {self.success_count} proxies SEM senha funcionando")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.running = False

    def stop_check(self):
        self.running = False

    def save_proxies(self):
        if not self.success_proxies:
            messagebox.showwarning("Aviso", "Nenhum proxy para salvar ainda!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            initialfile="proxies.txt",
            title="Salvar proxies"
        )

        if file_path:
            with open(file_path, "w") as f:
                for proxy in self.success_proxies:
                    f.write(proxy + "\n")
            messagebox.showinfo("Sucesso", f"Salvo com sucesso!\n{len(self.success_proxies)} proxies sem senha\n\nArquivo: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyCheckerGUI(root)
    root.mainloop()
