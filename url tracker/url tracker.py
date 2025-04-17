import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor
import os
import sys
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner ASCII
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗   ██╗██████╗ ██╗         ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║   ██║██╔══██╗██║         ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║   ██║██████╔╝██║            ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
██║   ██║██╔══██╗██║            ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║███████╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                      
""")

class PhotonTracer:
    def __init__(self, target_url, max_depth=3, output_dir="results"):
        self.target_url = target_url.rstrip('/')
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.visited_urls = set()
        self.internal_urls = set()
        self.external_urls = set()
        self.js_files = set()
        self.endpoints = set()
        self.robots_urls = set()
        self.Email = set()
        self.fuzzable_urls = set()
        self.archive_urls = set()
        self.total_requests = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def fetch_robots_txt(self):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT +"\n[~] Fetching robots.txt")
        robots_urls = set()
        for scheme in ['https', 'http']:
            try:
                robots_url = f"{scheme}://{urlparse(self.target_url).netloc}/robots.txt"
                response = requests.get(robots_url, headers=self.headers, timeout=5)
                self.total_requests += 1
                if response.status_code == 200:
                    for line in response.text.splitlines():
                        line = line.strip()
                        if line.startswith(('Disallow:', 'Allow:')):
                            path = line.split(':', 1)[1].strip()
                            if path and not path.startswith(('*', '#')):
                                full_url = urljoin(self.target_url, path)
                                robots_urls.add(full_url)
                break
            except Exception:
                continue
        self.robots_urls = robots_urls
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[+] URL from robots.txt: {len(self.robots_urls)}")

    def fetch_archive_urls(self):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[~] Fetching from archive.org")
        try:
            domain = urlparse(self.target_url).netloc
            # Usar HTTPS para a requisição
            api_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&filter=statuscode:200"
            response = requests.get(api_url, headers=self.headers, timeout=15)  # Aumentar o tempo limite para 15 segundos
            self.total_requests += 1
            if response.status_code == 200:
                data = response.json()
                for url in data[1:]:
                    self.archive_urls.add(url[0])
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[+] Archive.org URL: {len(self.archive_urls)}")
            else:
                print(f"\n[-] Archive.org retornou um status não esperado: {response.status_code}")
        except requests.exceptions.Timeout:
            print("\n[-] Archive.org: Timeout ao tentar acessar a URL.")
        except Exception as e:
            print(f"\n[-] Archive.org falhou: {e}")

    def is_internal(self, url):
        return urlparse(url).netloc == urlparse(self.target_url).netloc

    def extract_urls(self, url):
        try:
            if url in self.visited_urls:
                return set(), set(), set()
            self.visited_urls.add(url)
            self.total_requests += 1
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                return set(), set(), set()

            soup = BeautifulSoup(response.text, 'html.parser')
            page_urls = set()
            js_files = set()
            endpoints = set()

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if self.is_internal(full_url):
                    page_urls.add(full_url)
                    self.internal_urls.add(full_url)
                else:
                    self.external_urls.add(full_url)

            for script in soup.find_all('script', src=True):
                src = script['src']
                full_src = urljoin(url, src)
                if full_src.endswith('.js'):
                    js_files.add(full_src)
                    self.js_files.add(full_src)

            for u in page_urls:
                if '?' in u or '=' in u:
                    endpoints.add(u)
                    self.fuzzable_urls.add(u)

            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
            self.Email.update(emails)

            return page_urls, js_files, endpoints

        except Exception:
            return set(), set(), set()

    def crawl_level(self, urls, level):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[!] Crawling Level {level} - {len(urls)} URL")
        new_urls = set()
        total = len(urls)
        progress = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.extract_urls, url): url for url in urls}
            for future in future_to_url:
                page_urls, js_files, endpoints = future.result()
                new_urls.update(page_urls)
                self.endpoints.update(endpoints)
                progress += 1
                sys.stdout.write(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\r[~] Progress: {progress}/{total}")
                sys.stdout.flush()
        print()
        return new_urls

    def save_results(self):
        def save_set(data_set, name):
            path = os.path.join(self.output_dir, f"{name}.txt")
            with open(path, "w", encoding="utf-8") as f:
                for item in sorted(data_set):
                    f.write(f"{item}\n")

        save_set(self.archive_urls, "archive_urls")
        save_set(self.robots_urls, "robots_urls")
        save_set(self.internal_urls, "internal_urls")
        save_set(self.external_urls, "external_urls")
        save_set(self.js_files, "js_files")
        save_set(self.endpoints, "endpoints")
        save_set(self.fuzzable_urls, "fuzzable_urls")
        save_set(self.Email, "Email")

        # Também salvar tudo junto
        all_urls = self.archive_urls | self.robots_urls | self.internal_urls | self.external_urls
        save_set(all_urls, "all_found_urls")

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Todos os resultados foram salvos na pasta: {self.output_dir}")

    def run(self):
        print(f"\n[~] Iniciando Photon Tracer em: {self.target_url}")
        self.fetch_archive_urls()
        self.fetch_robots_txt()

        all_starting_urls = self.archive_urls | self.robots_urls
        current_urls = all_starting_urls

        for level in range(1, self.max_depth + 1):
            if not current_urls:
                break
            current_urls = self.crawl_level(current_urls, level)

        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[~] Coleta finalizada.")
        self.save_results()

if __name__ == "__main__":
    target = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (ex.: https://example.com): ").strip()
    if not target.startswith(('http://', 'https://')):
        target = 'https://' + target
    tracer = PhotonTracer(target)
    tracer.run()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
