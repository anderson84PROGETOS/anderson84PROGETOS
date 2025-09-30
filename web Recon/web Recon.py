import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import requests
from bs4 import BeautifulSoup
import json, csv, time, queue, re
from urllib.parse import urlparse, urljoin, urldefrag

# ---------------- Configurações ----------------
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}
DEFAULT_TIMEOUT = 15
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w{2,}', re.I)
PHONE_REGEX = re.compile(r'(\+?\d[\d\-\s\(\)]{6,}\d)')

# ---------------- Crawler ----------------
class Crawler:
    def __init__(self, seed, depth=2, concurrency=4, max_pages=200, delay=0.5):
        self.seed = seed
        self.parsed = urlparse(seed)
        self.domain = self.parsed.netloc
        self.depth = depth
        self.concurrency = concurrency
        self.max_pages = max_pages
        self.delay = delay

        self.session = requests.Session()
        self.to_visit = queue.Queue()
        self.to_visit.put((seed, 0))
        self.visited = set()
        self.lock = threading.Lock()
        self.results = {}
        self.pages_crawled = 0

    def safe_get(self, url, max_retries=3):
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                r = self.session.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
                if r.status_code in (403, 429) and attempt < max_retries:
                    time.sleep(1 + attempt)
                    continue
                return r
            except Exception as e:
                last_exc = e
                time.sleep(0.5 + attempt)
        raise last_exc

    def normalize_url(self, base, link):
        if not link or link.startswith(('javascript:', 'mailto:', 'tel:')):
            return None
        try:
            joined = urljoin(base, link)
            clean, _ = urldefrag(joined)
            return clean
        except:
            return None

    def is_same_domain(self, url):
        return urlparse(url).netloc == self.domain

    def analyze_page(self, url, html, headers):
        soup = BeautifulSoup(html, "html.parser")
        data = {
            'url': url,
            'http_headers': dict(headers),
            'emails': [],
            'phones': [],
            'internal_links': [],
            'external_links': []
        }
        text = soup.get_text(" ")
        data['emails'] = list(set(EMAIL_REGEX.findall(text)))
        data['phones'] = list(set([p.strip() for p in PHONE_REGEX.findall(text)]))
        for a in soup.find_all('a', href=True):
            href = self.normalize_url(url, a['href'])
            if href:
                if self.is_same_domain(href):
                    data['internal_links'].append(href)
                else:
                    data['external_links'].append(href)
        # remover duplicados
        data['internal_links'] = list(set(data['internal_links']))
        data['external_links'] = list(set(data['external_links']))
        return data

    def worker(self, update_progress, log_func, logged_urls):
        while True:
            try:
                url, depth = self.to_visit.get(timeout=1)
            except:
                return
            if url in self.visited or self.pages_crawled >= self.max_pages:
                self.to_visit.task_done()
                continue
            try:
                r = self.safe_get(url)
                html = r.text if 'html' in r.headers.get('content-type','') else ''
                page_data = self.analyze_page(url, html, r.headers)
                with self.lock:
                    if url not in self.visited:
                        self.visited.add(url)
                        self.results[url] = page_data
                        self.pages_crawled += 1

                # Log no GUI, evitando repetir URLs
                with self.lock:
                    if url not in logged_urls:
                        logged_urls.add(url)
                        log_func(f"\n[URL] {url}")
                        for e in page_data['emails']:
                            log_func(f"\n[EMAIL] {e}")
                        for p in page_data['phones']:
                            log_func(f"\n[PHONE] {p}")
                        for link in page_data['internal_links']:
                            log_func(f"\n[INTERNAL LINK] {link}")
                        for link in page_data['external_links']:
                            log_func(f"\n[EXTERNAL LINK] {link}")

                update_progress(self.pages_crawled)
                if depth < self.depth:
                    for link in page_data['internal_links']:
                        if link not in self.visited:
                            self.to_visit.put((link, depth + 1))
                time.sleep(self.delay)
            except Exception as e:
                log_func(f"[ERROR] {url} -> {str(e)}")
            finally:
                self.to_visit.task_done()

    def run(self, update_progress=lambda x: None, log_func=lambda x: None):
        logged_urls = set()  # evita repetição no GUI
        threads = []
        for _ in range(self.concurrency):
            t = threading.Thread(target=self.worker, args=(update_progress, log_func, logged_urls), daemon=True)
            t.start()
            threads.append(t)
        self.to_visit.join()
        return self.results

# ---------------- Funções de salvar ----------------
def save_json(data, path):
    # salvar sem URLs repetidas
    unique_results = {}
    for url, info in data['results'].items():
        unique_results[url] = info
    data['results'] = unique_results
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv_links(results, path):
    all_links = set()
    for page in results.values():
        all_links.update(page['internal_links'])
        all_links.update(page['external_links'])
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Primeira linha indicando quantidade de URLs únicas
        writer.writerow([f'[+] URL únicas Encontradas: {len(all_links)}'])
        writer.writerow([])  # Linha em branco
        writer.writerow([])  # Linha em branco
        # Escrever cada link em linha separada com uma linha em branco entre eles
        for link in sorted(all_links):
            writer.writerow([link])
            writer.writerow([])  # linha em branco após cada URL

def save_csv_emails(results, path):
    all_emails = set()
    for page in results.values():
        all_emails.update(page['emails'])
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Primeira linha com a contagem de emails
        writer.writerow([f'[+] Email Encontrados: {len(all_emails)}'])
        # Linha em branco
        writer.writerow([])
        # Escrever cada email em linha separada
        for email in sorted(all_emails):
            writer.writerow([email])

# ---------------- GUI ----------------
class SiteReconGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('web Recon')
        self.geometry('1280x1024')
        self.grid_columnconfigure(0, weight=1)

        tk.Label(self, text='URL do site:').grid(row=0, column=0, pady=5)
        self.url_entry = tk.Entry(self, width=60)
        self.url_entry.grid(row=1, column=0, pady=5)

        tk.Label(self, text='Profundidade (depth):').grid(row=2, column=0, pady=5)
        self.depth_var = tk.IntVar(value=2)
        tk.Entry(self, textvariable=self.depth_var).grid(row=3, column=0, pady=5)

        tk.Label(self, text='Concorrência (threads):').grid(row=4, column=0, pady=5)
        self.concurrency_var = tk.IntVar(value=4)
        tk.Entry(self, textvariable=self.concurrency_var).grid(row=5, column=0, pady=5)

        tk.Label(self, text='Max páginas:').grid(row=6, column=0, pady=5)
        self.max_pages_var = tk.IntVar(value=200)
        tk.Entry(self, textvariable=self.max_pages_var).grid(row=7, column=0, pady=5)

        tk.Label(self, text='Delay (s):').grid(row=8, column=0, pady=5)
        self.delay_var = tk.DoubleVar(value=0.5)
        tk.Entry(self, textvariable=self.delay_var).grid(row=9, column=0, pady=5)

        self.start_btn = tk.Button(self, text='Iniciar Crawl', command=self.start_crawl)
        self.start_btn.grid(row=10, column=0, pady=5)

        self.progress = ttk.Progressbar(self, orient='horizontal', length=800, mode='determinate')
        self.progress.grid(row=11, column=0, pady=5)

        self.status_text = tk.Text(self, width=150, height=33)
        self.status_text.grid(row=12, column=0, pady=5)
        self.status_text.config(state='disabled')

        self.scrollbar = ttk.Scrollbar(self, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=12, column=1, sticky='ns')

    def log(self, msg):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')

    def update_progress(self, value):
        self.progress['value'] = value

    def start_crawl(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror('Erro', 'Digite uma URL válida!')
            return
        if not url.startswith('http'):
            url = 'http://' + url

        depth = self.depth_var.get()
        concurrency = self.concurrency_var.get()
        max_pages = self.max_pages_var.get()
        delay = self.delay_var.get()

        self.start_btn.config(state='disabled')
        self.progress['value'] = 0
        self.progress['maximum'] = max_pages

        thread = threading.Thread(
            target=self.run_crawl,
            args=(url, depth, concurrency, max_pages, delay),
            daemon=True
        )
        thread.start()

    def run_crawl(self, url, depth, concurrency, max_pages, delay):
        self.log(f'[+] Iniciando crawl em {url}')
        crawler = Crawler(seed=url, depth=depth, concurrency=concurrency, max_pages=max_pages, delay=delay)
        results = crawler.run(update_progress=self.update_progress, log_func=self.log)

        self.log(f'\n\n[+] Concluído. URL únicas Encontradas: {len(results)}')

        output = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files','*.json')], title='Salvar resultado JSON')
        if output:
            save_json({'seed': url, 'results': results}, output)
            base_name = os.path.splitext(output)[0]
            save_csv_links(results, base_name + '_links.csv')
            save_csv_emails(results, base_name + '_emails.csv')

        self.start_btn.config(state='normal')
        self.progress['value'] = max_pages

if __name__ == '__main__':
    app = SiteReconGUI()
    app.mainloop()
