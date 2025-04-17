import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor

class PhotonTracer:
    def __init__(self, target_url, progress_callback, log_callback, max_depth=3):
        self.target_url = target_url.rstrip('/')
        self.max_depth = max_depth
        self.progress_callback = progress_callback
        self.log_callback = log_callback

        # Criação do nome da pasta com base no domínio
        domain = urlparse(self.target_url).netloc.replace('.', '_')
        self.output_dir = f'dados_{domain}'

        self.visited_urls = set()
        self.internal_urls = set()
        self.external_urls = set()
        self.js_files = set()
        self.endpoints = set()
        self.robots_urls = set()
        self.emails = set()
        self.fuzzable_urls = set()
        self.archive_urls = set()
        self.pdfs = set()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        os.makedirs(self.output_dir, exist_ok=True)

        self.file_handles = {}
        for name in ["archive_urls", "robots_urls", "internal_urls", "external_urls", "js_files", "endpoints", "fuzzable_urls", "emails", "pdfs"]:
            path = os.path.join(self.output_dir, f"{name}.txt")
            self.file_handles[name] = open(path, "w", encoding="utf-8")

    def log(self, text):
        self.log_callback(text)

    def save_line(self, name, item):
        if item not in getattr(self, name):
            getattr(self, name).add(item)
            self.file_handles[name].write(f"{item}\n")
            self.file_handles[name].flush()

    def fetch_robots_txt(self):
        self.log("\n[~] Buscando robots.txt...")
        for scheme in ['https', 'http']:
            try:
                robots_url = f"{scheme}://{urlparse(self.target_url).netloc}/robots.txt"
                response = requests.get(robots_url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    for line in response.text.splitlines():
                        line = line.strip()
                        if line.startswith(('Disallow:', 'Allow:')):
                            path = line.split(':', 1)[1].strip()
                            full_url = urljoin(self.target_url, path)
                            self.save_line("robots_urls", full_url)
                    break
            except Exception:
                continue
        self.log(f"[+] Encontrado no robots.txt: {len(self.robots_urls)} URLs")

    def fetch_archive_urls(self):
        self.log("\n[~] Buscando no archive.org...")
        try:
            domain = urlparse(self.target_url).netloc
            api_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&filter=statuscode:200"
            response = requests.get(api_url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for url in data[1:]:
                    self.save_line("archive_urls", url[0])
                self.log(f"\n[+] Encontrado no archive.org: {len(self.archive_urls)} URL")
            else:
                self.log("\n[-] Não foi possível buscar archive.org (status code diferente de 200)")
        except Exception:
            pass

    def is_internal(self, url):
        return urlparse(url).netloc == urlparse(self.target_url).netloc

    def extract_urls(self, url):
        try:
            if url in self.visited_urls:
                return set()
            self.visited_urls.add(url)
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                return set()

            soup = BeautifulSoup(response.text, 'html.parser')
            page_urls = set()

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if full_url.endswith('.pdf'):
                    self.save_line("pdfs", full_url)
                elif self.is_internal(full_url):
                    page_urls.add(full_url)
                    self.save_line("internal_urls", full_url)
                else:
                    self.save_line("external_urls", full_url)

            for script in soup.find_all('script', src=True):
                src = script['src']
                full_src = urljoin(url, src)
                if full_src.endswith('.js'):
                    self.save_line("js_files", full_src)

            for u in page_urls:
                if '?' in u or '=' in u:
                    self.save_line("endpoints", u)
                    self.save_line("fuzzable_urls", u)

            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
            for email in emails:
                self.save_line("emails", email)

            return page_urls
        except Exception:
            return set()

    def crawl_level(self, urls, level, total_levels):
        self.log(f"\n[!] Rastreando nível {level} - {len(urls)} URLs")
        new_urls = set()
        total = len(urls)
        progress_step = 100 / (total * total_levels) if total > 0 else 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.extract_urls, url): url for url in urls}
            for future in future_to_url:
                page_urls = future.result()
                new_urls.update(page_urls)
                self.progress_callback(progress_step)
        return new_urls

    def close_files(self):
        for f in self.file_handles.values():
            f.close()

    def run(self):
        self.log(f"Iniciando rastreamento em: {self.target_url}")
        self.fetch_archive_urls()
        self.fetch_robots_txt()
        all_starting_urls = self.archive_urls | self.robots_urls
        current_urls = all_starting_urls

        for level in range(1, self.max_depth + 1):
            if not current_urls:
                break
            current_urls = self.crawl_level(current_urls, level, self.max_depth)

        self.log("\n\n[~] Coleta finalizada.")
        self.progress_callback(100, force=True)
        self.close_files()


class PhotonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("url tracking Tools")
        self.root.geometry("1200x900")
        self.progress_value = 0

        self.url_label = tk.Label(root, text="Digite a URL do website (ex.: https://example.com)", font=("Arial", 12, "bold"))
        self.url_label.pack()
        self.url_entry = tk.Entry(root, width=45, font=("Arial", 12, "bold"))
        self.url_entry.pack(pady=5)

        self.start_button = tk.Button(root, text="Iniciar", command=self.start_scan, bg="#1e1e1e", fg="#00FF00", font=("Arial", 12, "bold"))
        self.start_button.pack(pady=10)

        self.progress = ttk.Progressbar(root, length=500, mode='determinate')
        self.progress.pack(pady=10)

        self.log_text = tk.Text(root, height=35, width=120, bg="#1e1e1e", fg="#00FF00", font=("Arial", 11, "bold"))
        self.log_text.pack(pady=10)

    def update_progress(self, step, force=False):
        if force:
            self.progress_value = 100
        else:
            self.progress_value += step
            self.progress_value = min(100, self.progress_value)
        self.progress["value"] = self.progress_value
        self.root.update_idletasks()

    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def start_scan(self):
        target_url = self.url_entry.get().strip()
        if not target_url:           
            return
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url

        self.progress["value"] = 0
        self.progress_value = 0
        self.log_text.delete(1.0, tk.END)
        threading.Thread(target=self.run_tracer, args=(target_url,), daemon=True).start()

    def run_tracer(self, target_url):
        tracer = PhotonTracer(target_url, self.update_progress, self.log)
        tracer.run()
        messagebox.showinfo("Concluído", f"Varredura finalizada.\nResultados salvos na pasta '{tracer.output_dir}'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotonGUI(root)
    root.mainloop()
