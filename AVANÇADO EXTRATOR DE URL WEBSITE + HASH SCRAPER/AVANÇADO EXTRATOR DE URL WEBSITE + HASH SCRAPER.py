import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinter import Canvas
import requests
from PIL import Image, ImageTk
import socket
from urllib.parse import urlparse, urljoin
from io import BytesIO
import os
from bs4 import BeautifulSoup
import threading
import re
import subprocess
import sys
import shutil
import random
import time
from tkinter import font

# =========================================================
# USER AGENTS
# =========================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]

# =========================================================
# VARIÁVEIS GLOBAIS
# =========================================================

img_original = None
html_atual = ""
urls_extraidas = []
dominio_detectado = None
custom_user_agent_hash = None

# =========================================================
# FUNÇÕES COMPARTILHADAS
# =========================================================

def carregar_user_agents_txt():
    global USER_AGENTS
    caminho = filedialog.askopenfilename(title="Selecionar user-agent.txt", filetypes=[("Arquivo TXT", "*.txt")])
    if not caminho:
        return
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            novos_agents = [linha.strip() for linha in f if linha.strip()]
        if novos_agents:
            USER_AGENTS = novos_agents
            messagebox.showinfo("Sucesso", f"{len(USER_AGENTS)} User-Agents carregados.")
        else:
            messagebox.showwarning("Aviso", "Nenhum User-Agent encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao carregar TXT:\n{e}")

def gerar_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }

def abrir_no_chrome_anonimo(url):
    try:
        caminhos = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome = next((c for c in caminhos if os.path.isfile(c)), None)
        if not chrome and sys.platform != "win32":
            chrome = shutil.which("google-chrome") or shutil.which("chrome")

        if chrome:
            subprocess.Popen([chrome, "--incognito", "--start-maximized", url])
        else:
            messagebox.showerror("Erro", "Google Chrome não encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir Chrome:\n{e}")

def abrir_url_no_chrome_anonima(event):
    try:
        widget = event.widget
        index = widget.index(f"@{event.x},{event.y}")
        linha = widget.get(index + " linestart", index + " lineend").strip()
        match = re.search(r'(https?://[^\s"\'<>]+)', linha)
        if match:
            abrir_no_chrome_anonimo(match.group(1))
    except:
        pass

def abrir_todas_urls_anonimas():
    if not urls_extraidas:
        messagebox.showwarning("Aviso", "Nenhuma URL encontrada.")
        return
    if messagebox.askyesno("Confirmar", f"Abrir TODAS as {len(urls_extraidas)} URLs em modo anônimo?"):
        for url in urls_extraidas:
            if url.startswith(("http://", "https://")):
                abrir_no_chrome_anonimo(url)
                time.sleep(0.7)

def obter_as_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("org", "Unknown Organization")
        return "Unknown Organization"
    except:
        return "Error: Não foi possível obter"

def detectar_dominio_base(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        for attr in ['href', 'src']:
            if tag.has_attr(attr):
                valor = tag[attr]
                if valor.startswith("http"):
                    parsed = urlparse(valor)
                    return f"{parsed.scheme}://{parsed.netloc}"
    return None

def extrair_todas_urls(html_content, base_url=None):
    global dominio_detectado
    dominio_detectado = detectar_dominio_base(html_content) if not base_url else base_url
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = set()
    tags = [('a','href'),('img','src'),('script','src'),('link','href'),('iframe','src'),('video','src'),('audio','src'),('form','action')]
    for tag in soup.find_all(True):
        for name, attr in tags:
            if tag.name == name and tag.has_attr(attr):
                valor = tag[attr]
                if isinstance(valor, str):
                    if valor.startswith("http"):
                        urls.add(valor)
                    elif valor.startswith("/") and dominio_detectado:
                        urls.add(urljoin(dominio_detectado, valor))
    urls.update(re.compile(r'http[s]?://[^\s"\'<>]+').findall(html_content))
    return sorted(urls)

# =========================================================
# CLASSE HASH SCRAPER
# =========================================================

class HashScraperGUI:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.frame = ttk.Frame(parent_frame)
        
        # Fontes
        label_font = font.Font(family="Consolas", size=10)
        text_font = font.Font(family="Consolas", size=10)
        stats_font = font.Font(family="Consolas", size=9)
        
        # Frame URL
        url_frame = tk.Frame(self.frame, bg="#0d0d0d")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_label = tk.Label(url_frame, text="🌐 URL:", font=label_font,
                             fg="#00ff00", bg="#0d0d0d")
        url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = tk.Entry(url_frame, font=text_font, bg="#1a1a1a",
                                  fg="#00ff00", insertbackground="#00ff00",
                                  relief=tk.FLAT, bd=5, highlightthickness=1,
                                  highlightcolor="#00ff00", highlightbackground="#333333")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.url_entry.insert(0, "https://")
        
        # Botões
        btn_frame = tk.Frame(self.frame, bg="#0d0d0d")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.scrape_btn = tk.Button(btn_frame, text="▶ INICIAR SCAN", 
                                    font=label_font, bg="#00aa00", fg="#ffffff",
                                    relief=tk.FLAT, padx=25, pady=10,
                                    activebackground="#00ff00", activeforeground="#000000",
                                    cursor="hand2", command=self.start_scrape)
        self.scrape_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(btn_frame, text="✕ LIMPAR", font=label_font,
                              bg="#444444", fg="#ffffff", relief=tk.FLAT,
                              padx=25, pady=10, activebackground="#666666",
                              cursor="hand2", command=self.clear_results)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ PARAR", font=label_font,
                                  bg="#cc0000", fg="#ffffff", relief=tk.FLAT,
                                  padx=25, pady=10, activebackground="#ff0000",
                                  cursor="hand2", state=tk.DISABLED,
                                  command=self.stop_scrape)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = tk.Button(btn_frame, text="💾 SALVAR", font=label_font,
                             bg="#0055aa", fg="#ffffff", relief=tk.FLAT,
                             padx=25, pady=10, activebackground="#0077dd",
                             cursor="hand2", command=self.save_results)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ua_btn = tk.Button(btn_frame, text="📂 USER-AGENT", font=label_font,
                                bg="#880088", fg="#ffffff", relief=tk.FLAT,
                                padx=25, pady=10, activebackground="#aa00aa",
                                cursor="hand2", command=self.load_user_agent)
        self.ua_btn.pack(side=tk.LEFT)
        
        self.ua_label = tk.Label(btn_frame, text="UA: padrão", font=label_font,
                                 fg="#888888", bg="#0d0d0d")
        self.ua_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Barra de progresso
        progress_frame = tk.Frame(self.frame, bg="#0d0d0d")
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        progress_label_frame = tk.Frame(progress_frame, bg="#0d0d0d")
        progress_label_frame.pack(fill=tk.X)
        
        tk.Label(progress_label_frame, text="📊 PROGRESSO:", font=label_font,
                 fg="#00ff00", bg="#0d0d0d").pack(side=tk.LEFT)
        
        self.percent_label = tk.Label(progress_label_frame, text="0%", 
                                      font=label_font, fg="#00ff00", bg="#0d0d0d")
        self.percent_label.pack(side=tk.RIGHT)
        
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.configure("green.Horizontal.TProgressbar", 
                        background="#00ff00", troughcolor="#1a1a1a",
                        bordercolor="#00ff00", lightcolor="#00ff00", darkcolor="#00aa00")
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                            variable=self.progress_var,
                                            maximum=100,
                                            style="green.Horizontal.TProgressbar",
                                            length=900)
        self.progress_bar.pack(fill=tk.X, pady=(2, 0))
        
        self.progress_status = tk.Label(progress_frame, text="⏳ Aguardando...", 
                                        font=stats_font, fg="#888888", bg="#0d0d0d",
                                        anchor=tk.W)
        self.progress_status.pack(fill=tk.X, pady=(2, 0))
        
        # Estatísticas
        stats_frame = tk.Frame(self.frame, bg="#0d0d0d")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_cards = {}
        stats_config = [
            ("pages", "📄 Páginas", "0"),
            ("hashes", "🔑 Hashes", "0"),
            ("types", "🏷️ Tipos", "0"),
            ("status", "📡 Status", "---"),
        ]
        
        for key, label, value in stats_config:
            card = tk.Frame(stats_frame, bg="#1a1a1a", padx=15, pady=8, 
                           highlightthickness=1, highlightcolor="#333333")
            card.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
            
            tk.Label(card, text=label, font=stats_font, fg="#888888", 
                    bg="#1a1a1a").pack()
            self.stats_cards[key] = tk.Label(card, text=value, 
                                            font=font.Font(family="Consolas", size=14, weight="bold"),
                                            fg="#00ff00", bg="#1a1a1a")
            self.stats_cards[key].pack()
        
        # Área de resultados
        result_label = tk.Label(self.frame, text="📋 HASHES COMPLETAS ENCONTRADAS:", 
                                font=label_font, fg="#00ff00", bg="#0d0d0d", anchor=tk.W)
        result_label.pack(fill=tk.X, pady=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(self.frame, font=text_font,
                                                      bg="#0a0a0a", fg="#00ff00",
                                                      insertbackground="#00ff00",
                                                      relief=tk.FLAT, bd=5,
                                                      wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Status
        self.status_label = tk.Label(self.frame, text="✅ Pronto para iniciar scan...",
                                     font=label_font, fg="#888888", bg="#0d0d0d",
                                     anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(5, 0))
        
        # Tags de cores
        self.result_text.tag_config("hash_found", foreground="#00ff00",
                                    font=font.Font(family="Consolas", size=9, weight="bold"))
        self.result_text.tag_config("hash_type", foreground="#ffaa00",
                                    font=font.Font(family="Consolas", size=10, weight="bold"))
        self.result_text.tag_config("error", foreground="#ff4444")
        self.result_text.tag_config("info", foreground="#8888ff")
        self.result_text.tag_config("success", foreground="#00ff00")
        self.result_text.tag_config("warning", foreground="#ffaa00")
        self.result_text.tag_config("separator", foreground="#333333")
        self.result_text.tag_config("progress", foreground="#00aa00")
        self.result_text.tag_config("hash_value", foreground="#ff66ff",
                                    font=font.Font(family="Consolas", size=9))
        
        # Flags de controle
        self.scanning = False
        self.stop_requested = False
    
    def identify_hash(self, hash_string):
        hash_length = len(hash_string)
        
        hash_patterns = {
            32:   "MD5 / NTLM",
            40:   "SHA-1",
            56:   "SHA-224",
            64:   "SHA-256",
            96:   "SHA-384",
            128:  "SHA-512",
            8:    "CRC32 / Adler-32",
            16:   "MySQL 3.23 / CRC-16",
            24:   "LM Hash / Snefru-128",
            48:   "SHA-384 / Snefru-256",
            20:   "Tiger/160 / HAVAL-160",
            28:   "Tiger/192 / HAVAL-192",
        }
        
        if hash_string.startswith("$2a$") or hash_string.startswith("$2b$") or \
           hash_string.startswith("$2y$"):
            return "bcrypt"
        if hash_string.startswith("$6$"):
            return "SHA-512 Crypt (Linux Shadow)"
        if hash_string.startswith("$5$"):
            return "SHA-256 Crypt (Linux Shadow)"
        if hash_string.startswith("$1$"):
            return "MD5 Crypt (Linux Shadow)"
        
        return hash_patterns.get(hash_length, f"Desconhecido ({hash_length} chars)")
    
    def extract_hashes(self, content):
        found = []
        
        patterns = [
            r'\b[0-9a-fA-F]{128}\b',
            r'\b[0-9a-fA-F]{96}\b',
            r'\b[0-9a-fA-F]{64}\b',
            r'\b[0-9a-fA-F]{56}\b',
            r'\b[0-9a-fA-F]{40}\b',
            r'\b[0-9a-fA-F]{32}\b',
            r'\b[0-9a-fA-F]{16}\b',
            r'\b[0-9a-fA-F]{8}\b',
            r'\$2[aby]\$\d+\$[./A-Za-z0-9]{53}',
            r'\$6\$\w+\$[./A-Za-z0-9]{86}',
            r'\$5\$\w+\$[./A-Za-z0-9]{43}',
            r'\$1\$\w+\$[./A-Za-z0-9]{22}',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                hash_val = match.group()
                if hash_val not in [h[0] for h in found]:
                    hash_type = self.identify_hash(hash_val)
                    found.append((hash_val, hash_type))
        
        return found
    
    def update_progress(self, percent, status_text="", status_type="progress"):
        self.progress_var.set(percent)
        self.percent_label.config(text=f"{int(percent)}%")
        if status_text:
            self.progress_status.config(text=status_text, 
                                       fg={"progress": "#00aa00", 
                                           "error": "#ff4444", 
                                           "success": "#00ff00",
                                           "info": "#8888ff",
                                           "warning": "#ffaa00"}.get(status_type, "#888888"))
        self.parent.update_idletasks()
    
    def update_stats(self, pages=0, hashes=0, types=0, status="---"):
        self.stats_cards["pages"].config(text=str(pages))
        self.stats_cards["hashes"].config(text=str(hashes))
        self.stats_cards["types"].config(text=str(types))
        self.stats_cards["status"].config(text=status)
        self.parent.update_idletasks()
    
    def log_result(self, message, tag="info"):
        self.result_text.insert(tk.END, message + "\n", tag)
        self.result_text.see(tk.END)
        self.parent.update_idletasks()
    
    def get_headers(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        if custom_user_agent_hash:
            headers['User-Agent'] = custom_user_agent_hash
        else:
            headers['User-Agent'] = random.choice(USER_AGENTS)
        return headers
    
    def load_user_agent(self):
        global custom_user_agent_hash
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo UserAgent.txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            defaultextension=".txt"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ua = f.read().strip()
            
            if not ua:
                messagebox.showwarning("⚠️ AVISO", "O arquivo está vazio! Usando User-Agent padrão.")
                custom_user_agent_hash = None
                self.ua_label.config(text="UA: padrão", fg="#888888")
                return
            
            lines = [line.strip() for line in ua.split('\n') if line.strip()]
            if lines:
                custom_user_agent_hash = lines[0]
                display_ua = custom_user_agent_hash[:40] + "..." if len(custom_user_agent_hash) > 40 else custom_user_agent_hash
                self.ua_label.config(text=f"UA: {display_ua}", fg="#ff66ff")
                self.log_result(f"✅ User-Agent carregado: {custom_user_agent_hash[:60]}...", "success")
                messagebox.showinfo("✅ SUCESSO", f"User-Agent carregado com sucesso!\n\n{custom_user_agent_hash[:80]}{'...' if len(custom_user_agent_hash) > 80 else ''}")
            else:
                messagebox.showwarning("⚠️ AVISO", "Arquivo vazio! Usando User-Agent padrão.")
                custom_user_agent_hash = None
                self.ua_label.config(text="UA: padrão", fg="#888888")
                
        except Exception as e:
            messagebox.showerror("❌ ERRO", f"Erro ao carregar User-Agent:\n{str(e)}")
            custom_user_agent_hash = None
            self.ua_label.config(text="UA: padrão", fg="#888888")
    
    def save_results(self):
        content = self.result_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("⚠️ ATENÇÃO", "Nenhum resultado para salvar!\nExecute um scan primeiro.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Salvar resultados como...",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile="hash_scraper_resultados.txt"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("  HASH SCRAPER - RELATÓRIO DE HASHS\n")
                f.write("=" * 80 + "\n\n")
                
                if custom_user_agent_hash:
                    f.write(f"  User-Agent: {custom_user_agent_hash}\n")
                f.write(f"  URL Alvo: {self.url_entry.get().strip()}\n")
                f.write(f"  Data/Hora: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("  RESULTADOS\n")
                f.write("-" * 80 + "\n\n")
                
                clean_content = content
                f.write(clean_content)
                
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("  FIM DO RELATÓRIO\n")
                f.write("=" * 80 + "\n")
            
            messagebox.showinfo("✅ SUCESSO", f"Resultados salvos com sucesso em:\n{file_path}")
            self.status_label.config(text=f"✅ Resultados salvos em: {os.path.basename(file_path)}", fg="#00ff00")
            
        except Exception as e:
            messagebox.showerror("❌ ERRO", f"Erro ao salvar arquivo:\n{str(e)}")
    
    def scrape_url(self, url):
        all_hashes = []
        all_types = set()
        pages_scanned = 0
        
        try:
            self.update_progress(0, "🔄 Iniciando conexão...", "info")
            self.update_stats(status="Conectando...")
            
            parsed = urlparse(url)
            if not parsed.netloc:
                self.log_result("❌ ERRO: URL inválida!", "error")
                return
            
            headers = self.get_headers()
            
            self.log_result(f"🌐 Alvo: {url}", "info")
            self.log_result(f"{'─' * 80}", "separator")
            
            self.update_progress(10, "📡 Baixando página principal...", "progress")
            
            response = requests.get(url, headers=headers, timeout=30, verify=True)
            pages_scanned += 1
            
            self.update_progress(25, f"📄 Página recebida ({response.status_code})", "success")
            self.update_stats(pages=pages_scanned, status=f"{response.status_code}")
            
            if response.status_code != 200:
                self.log_result(f"⚠️ Status HTTP: {response.status_code}", "warning")
                self.update_progress(100, "⚠️ Scan incompleto", "warning")
                return
            
            content = response.text
            
            self.update_progress(30, "🔍 Escaneando HTML por hashes...", "progress")
            self.log_result("🔍 Extraindo hashes do HTML\n", "info")
            
            html_hashes = self.extract_hashes(content)
            
            for i, (h, t) in enumerate(html_hashes, 1):
                all_hashes.append((h, t))
                all_types.add(t)
                
                self.log_result(f"\n{'─' * 60}", "separator")
                self.log_result(f"  🔑 HASH #{len(all_hashes)}", "hash_found")
                self.log_result(f"  ├─ 🏷️  Tipo: {t}", "hash_type")
                self.log_result(f"  ├─ 📏 Tamanho: {len(h)} caracteres", "info")
                self.log_result(f"  └─ 🔐 Valor:", "info")
                self.log_result(f"     {h}", "hash_value")
                
                progress = 30 + (i / max(len(html_hashes), 1)) * 30
                self.update_progress(min(progress, 60), 
                                    f"🔑 Encontradas {len(all_hashes)} hash(es)...", "progress")
                self.update_stats(pages=pages_scanned, hashes=len(all_hashes), 
                                 types=len(all_types), status="Extraindo HTML...")
            
            if html_hashes:
                self.log_result(f"\n✅ {len(html_hashes)} hash(es) no HTML principal", "success")
            else:
                self.log_result(f"❌ Nenhum hash no HTML principal", "warning")
            
            self.update_progress(60, "🔗 Seguindo links e scripts...", "progress")
            self.log_result(f"\n{'═' * 60}", "separator")
            self.log_result("🔗 Escaneando recursos vinculados...", "info")
            
            link_pattern = re.findall(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', content)
            total_links = len(link_pattern)
            
            for idx, link in enumerate(link_pattern):
                if self.stop_requested:
                    self.log_result("⏹ Scan interrompido pelo usuário!", "warning")
                    break
                
                if link.startswith('/'):
                    full_url = f"{parsed.scheme}://{parsed.netloc}{link}"
                elif link.startswith('http'):
                    full_url = link
                else:
                    continue
                
                link_progress = 60 + (idx / max(total_links, 1)) * 30
                self.update_progress(link_progress, 
                                    f"🔗 Link {idx+1}/{total_links}...", "progress")
                
                try:
                    link_resp = requests.get(full_url, headers=headers, timeout=10)
                    pages_scanned += 1
                    
                    if 'text' in link_resp.headers.get('Content-Type', ''):
                        link_hashes = self.extract_hashes(link_resp.text)
                        
                        for h, t in link_hashes:
                            if h not in [item[0] for item in all_hashes]:
                                all_hashes.append((h, t))
                                all_types.add(t)
                                
                                self.log_result(f"\n{'─' * 60}", "separator")
                                self.log_result(f"  🔗 {full_url}", "info")
                                self.log_result(f"  🔑 HASH #{len(all_hashes)}", "hash_found")
                                self.log_result(f"  ├─ 🏷️  Tipo: {t}", "hash_type")
                                self.log_result(f"  ├─ 📏 Tamanho: {len(h)} caracteres", "info")
                                self.log_result(f"  └─ 🔐 Valor:", "info")
                                self.log_result(f"     {h}", "hash_value")
                                
                                self.update_stats(pages=pages_scanned, hashes=len(all_hashes),
                                                 types=len(all_types), status="Links...")
                
                except:
                    continue
            
            self.update_progress(90, "📊 Gerando relatório final...", "progress")
            
            self.log_result(f"\n{'═' * 80}", "separator")
            self.log_result("📊 RELATÓRIO FINAL", "success")
            self.log_result(f"{'═' * 80}", "separator")
            self.log_result(f"  📄 Páginas escaneadas: {pages_scanned}", "info")
            self.log_result(f"  🔑 Total de hashes: {len(all_hashes)}", "info")
            self.log_result(f"  🏷️ Tipos diferentes: {len(all_types)}", "info")
            
            if all_types:
                self.log_result(f"\n📋 Tipos de hash encontrados:", "info")
                for t in sorted(all_types):
                    count = sum(1 for _, ht in all_hashes if ht == t)
                    self.log_result(f"  ├─ {t}: {count}", "hash_type")
            
            if all_hashes:
                self.log_result(f"\n📋 LISTA COMPLETA DE HASHES:", "hash_found")
                for i, (h, t) in enumerate(all_hashes, 1):
                    self.log_result(f"\n  HASH #{i}", "hash_found")
                    self.log_result(f"  ├─ 🏷️  {t}", "hash_type")
                    self.log_result(f"  └─ 🔐 {h}", "hash_value")
            
            self.update_progress(100, "✅ SCAN CONCLUÍDO COM SUCESSO!", "success")
            self.update_stats(pages=pages_scanned, hashes=len(all_hashes),
                             types=len(all_types), status="✅ Concluído")
            
            self.status_label.config(text=f"✅ Scan concluído! {len(all_hashes)} hash(es) encontrada(s) em {pages_scanned} página(s)",
                                    fg="#00ff00")
            
        except requests.exceptions.SSLError:
            self.log_result("❌ ERRO SSL: Certificado inválido!", "error")
            self.update_progress(100, "❌ Erro SSL", "error")
        except requests.exceptions.ConnectionError:
            self.log_result("❌ ERRO DE CONEXÃO: URL inacessível!", "error")
            self.update_progress(100, "❌ Erro de conexão", "error")
        except requests.exceptions.Timeout:
            self.log_result("❌ TIMEOUT: Servidor demorou muito!", "error")
            self.update_progress(100, "❌ Timeout", "error")
        except Exception as e:
            self.log_result(f"❌ ERRO INESPERADO: {str(e)}", "error")
            self.update_progress(100, "❌ Erro", "error")
    
    def start_scrape(self):
        url = self.url_entry.get().strip()
        if not url or url == "https://":
            messagebox.showwarning("⚠️ ATENÇÃO", "Digite uma URL válida para scanear!")
            return
        
        self.stop_requested = False
        self.scanning = True
        
        self.scrape_btn.config(state=tk.DISABLED, bg="#444444", text="⏳ SCANEANDO...")
        self.stop_btn.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.percent_label.config(text="0%")
        self.progress_status.config(text="⏳ Iniciando scan...", fg="#8888ff")
        self.status_label.config(text="🔍 Scaneando...", fg="#00ff00")
        
        self.update_stats(pages=0, hashes=0, types=0, status="🔍 Scaneando...")
        
        thread = threading.Thread(target=self.run_scrape, args=(url,))
        thread.daemon = True
        thread.start()
    
    def run_scrape(self, url):
        try:
            self.scrape_url(url)
        finally:
            self.scanning = False
            self.parent.after(0, self.finish_scrape)
    
    def finish_scrape(self):
        self.scrape_btn.config(state=tk.NORMAL, bg="#00aa00", text="▶ INICIAR SCAN")
        self.stop_btn.config(state=tk.DISABLED)
    
    def stop_scrape(self):
        self.stop_requested = True
        self.progress_status.config(text="⏹ Parando scan...", fg="#ff4444")
        self.log_result("⏹ Solicitando parada...", "warning")
    
    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.percent_label.config(text="0%")
        self.progress_status.config(text="⏳ Limpo", fg="#888888")
        self.update_stats(pages=0, hashes=0, types=0, status="---")
        self.status_label.config(text="✅ Pronto para iniciar scan...", fg="#888888")
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "https://")
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

# =========================================================
# FUNÇÕES DO EXTRATOR DE URL
# =========================================================

def abrir_asn_bgp():
    texto = aba_geral_texto.get(1.0, tk.END)
    match = re.search(r'Organização:\s*(AS\d+)', texto)
    
    if not match:
        messagebox.showwarning("Aviso", "ASN não encontrado.")
        return

    numero_as = match.group(1)
    url = f"https://bgp.he.net/{numero_as}"

    try:
        abrir_no_chrome_anonimo(url)
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir ASN:\n{e}")

def update_progress(value):
    barra_progresso['value'] = value
    root.update_idletasks()

def salvar_imagem():
    global img_original
    if img_original:
        caminho = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if caminho:
            img_original.save(caminho, format="PNG")
            messagebox.showinfo("OK", "Imagem salva com sucesso.")
    else:
        messagebox.showwarning("Aviso", "Nenhuma imagem carregada.")

def salvar_todas_imagens():
    global html_atual
    url = entrada_url.get().strip()
    if not html_atual:
        messagebox.showwarning("Aviso", "Nenhum HTML carregado.")
        return
    pasta = filedialog.askdirectory()
    if not pasta: return

    soup = BeautifulSoup(html_atual, "html.parser")
    baixadas = 0
    for idx, tag in enumerate(soup.find_all("img"), 1):
        src = tag.get("src")
        if not src or src.startswith("data:"): continue
        src_url = urljoin(url, src)
        try:
            resp = requests.get(src_url, headers=gerar_headers(), timeout=15)
            resp.raise_for_status()
            ext = os.path.splitext(urlparse(src_url).path)[1] or ".png"
            caminho = os.path.join(pasta, f"image_{idx}{ext}")
            with open(caminho, "wb") as f:
                f.write(resp.content)
            baixadas += 1
        except:
            pass
    messagebox.showinfo("Finalizado", f"Imagens baixadas: {baixadas}")

def mostrar_urls():
    aba_urls_texto.delete(1.0, tk.END)
    if urls_extraidas:
        aba_urls_texto.insert(tk.END, f"TOTAL URL: {len(urls_extraidas)}\n\n")
        if dominio_detectado:
            aba_urls_texto.insert(tk.END, f"DOMINIO: {dominio_detectado}\n\n")
        for idx, url in enumerate(urls_extraidas, 1):
            aba_urls_texto.insert(tk.END, f"URL #{idx}: {url}\n\n")

def pesquisar_urls():
    termo = entrada_pesquisa.get().strip().lower()
    aba_urls_texto.delete(1.0, tk.END)
    filtradas = [url for url in urls_extraidas if termo in url.lower()]
    for i, url in enumerate(filtradas, 1):
        aba_urls_texto.insert(tk.END, f"URL: {i}\n\n{url}\n\n\n\n")

def salvar_urls():
    if not urls_extraidas:
        messagebox.showwarning("Aviso", "Nenhuma URL encontrada.")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"TOTAL URL: {len(urls_extraidas)}\n\n")
            if dominio_detectado:
                f.write(f"DOMINIO DETECTADO: {dominio_detectado}\n\n")
            for idx, url in enumerate(urls_extraidas, 1):
                f.write(f"URL #{idx}: {url}\n\n")
        messagebox.showinfo("OK", f"{len(urls_extraidas)} URLs salvas.")

def abrir_arquivo():
    global urls_extraidas, html_atual
    caminho = filedialog.askopenfilename(filetypes=[("HTML", "*.html *.htm")])
    if caminho:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                html_atual = f.read()
            urls_extraidas = extrair_todas_urls(html_atual)
            mostrar_urls()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

def buscar_dados():
    def run_fetch():
        global img_original, html_atual, urls_extraidas

        url = entrada_url.get().strip()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            update_progress(10)

            parsed = urlparse(url)
            hostname = parsed.hostname
            ip = socket.gethostbyname(hostname)
            porta = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)
            org_info = obter_as_info(ip)

            update_progress(20)

            headers = gerar_headers()
            sessao = requests.Session()
            resposta = sessao.get(url, headers=headers, timeout=20, allow_redirects=True)

            if resposta.status_code == 403:
                for _ in range(5):
                    headers = gerar_headers()
                    resposta = sessao.get(url, headers=headers, timeout=20)
                    if resposta.status_code != 403:
                        break
                    time.sleep(1)

            resposta.raise_for_status()
            html_atual = resposta.text

            org_info = obter_as_info(ip)
            if org_info.startswith("AS") and " " in org_info:
                numero_as, organizacao = org_info.split(" ", 1)
                detalhes_as = f"https://bgp.he.net/{numero_as}"
            else:
                numero_as = "Unknown AS"
                organizacao = org_info if org_info != "Unknown Organization" else org_info
                detalhes_as = "N/A"

            geral = (
                f"Request URL: {resposta.url}\n"
                f"\nRemote Address: {ip}:{porta}\n"
                f"\nRequest Method: {resposta.request.method}\n"
                f"\nStatus Code: {resposta.status_code} {resposta.reason}\n"
                f"\nOrganização: {numero_as} {organizacao}\n"
                f"\nDetalhes AS: {detalhes_as}\n\n"                
                f"\nUSER-AGENT\n\n{headers['User-Agent']}"
            )

            aba_geral_texto.delete(1.0, tk.END)
            aba_geral_texto.insert(tk.END, geral)
            update_progress(30)

            cabecalhos = "\n".join(f"{k}: {v}" for k, v in resposta.headers.items())
            aba_cabecalhos_texto.delete(1.0, tk.END)
            aba_cabecalhos_texto.insert(tk.END, cabecalhos)
            update_progress(40)

            aba_resposta_texto.delete(1.0, tk.END)
            aba_resposta_texto.insert(tk.END, html_atual[:50000])
            update_progress(50)

            soup = BeautifulSoup(html_atual, "html.parser")
            payload = ""

            for script in soup.find_all("script"):
                if script.get("src"):
                    script_url = urljoin(url, script.get("src"))
                    try:
                        headers = gerar_headers()
                        r = requests.get(script_url, headers=headers, timeout=10)
                        payload += f"\n\n===== {script_url} =====\n\n"
                        payload += r.text
                    except Exception as ex:
                        payload += f"\nERRO: {ex}\n"
                else:
                    if script.string:
                        payload += script.string + "\n"

            aba_payload_texto.delete(1.0, tk.END)
            aba_payload_texto.insert(tk.END, payload if payload else "Nenhum payload.")
            update_progress(60)

            recursos = []
            for script in soup.find_all("script", src=True):
                recursos.append({"tipo": "SCRIPT", "url": urljoin(url, script["src"])})
            for link in soup.find_all("link", href=True):
                recursos.append({"tipo": "CSS", "url": urljoin(url, link["href"])})
            for img in soup.find_all("img", src=True):
                if not img["src"].startswith("data:"):
                    recursos.append({"tipo": "IMAGE", "url": urljoin(url, img["src"])})

            aba_iniciador_texto.delete(1.0, tk.END)
            aba_iniciador_texto.tag_configure("green", foreground="#00ff00")
            aba_iniciador_texto.tag_configure("yellow", foreground="#ffff00")
            aba_iniciador_texto.tag_configure("red", foreground="#ff4444")
            aba_iniciador_texto.tag_configure("blue", foreground="#00aaff")
            aba_iniciador_texto.tag_configure("gray", foreground="#aaaaaa")

            for idx, r in enumerate(recursos, 1):
                try:
                    headers = gerar_headers()
                    resp = requests.head(r["url"], headers=headers, timeout=10, allow_redirects=True)
                    status = resp.status_code
                    tamanho = resp.headers.get("Content-Length", "?")
                except:
                    status = "ERRO"
                    tamanho = "?"

                if isinstance(status, int):
                    if status == 200:
                        status_tag = "green"
                    elif status in (301, 302, 307, 308):
                        status_tag = "yellow"
                    elif status in (403, 404, 500, 502, 503):
                        status_tag = "red"
                    else:
                        status_tag = "gray"
                else:
                    status_tag = "red"

                aba_iniciador_texto.insert(tk.END, f"RESOURCE #{idx}\n", "green")
                aba_iniciador_texto.insert(tk.END, f"TYPE: {r['tipo']}\n", "gray")
                aba_iniciador_texto.insert(tk.END, f"URL: {r['url']}\n", "blue")
                aba_iniciador_texto.insert(tk.END, f"STATUS: {status}\n", status_tag)
                aba_iniciador_texto.insert(tk.END, f"SIZE: {tamanho}\n", "gray")
                aba_iniciador_texto.insert(tk.END, "-" * 70 + "\n", "gray")

            update_progress(70)

            urls_extraidas = extrair_todas_urls(html_atual, base_url=url)
            mostrar_urls()
            update_progress(80)

            try:
                screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
                screen = requests.get(screenshot_url, timeout=60)
                img_data = BytesIO(screen.content)
                img_original = Image.open(img_data)
                largura = 1200
                ratio = largura / img_original.width
                altura = int(img_original.height * ratio)
                img_resize = img_original.resize((largura, altura), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img_resize)
                aba_visualizacao_canvas.delete("all")
                aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
                aba_visualizacao_canvas.image = tk_img
                aba_visualizacao_canvas.config(scrollregion=(0, 0, largura, altura))
            except:
                pass

            update_progress(100)

        except Exception as e:
            update_progress(0)
            messagebox.showerror("ERRO", str(e))

    threading.Thread(target=run_fetch, daemon=True).start()

# =========================================================
# GUI PRINCIPAL
# =========================================================

root = tk.Tk()
root.title("AVANÇADO EXTRATOR DE URL WEBSITE + HASH SCRAPER")
root.geometry("1280x1024")
root.wm_state("zoomed")
root.configure(bg="#0f0f0f")

# Estilo Dark
style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background="#0f0f0f")
style.configure("TLabel", background="#0f0f0f", foreground="#00ff88")
style.configure("TButton", background="#1e1e1e", foreground="#00ff88", font=("Arial", 10, "bold"))
style.configure("TEntry", fieldbackground="#1e1e1e", foreground="#ffffff", insertcolor="#00ff88")
style.configure("TNotebook", background="#0f0f0f", borderwidth=0)
style.configure("TNotebook.Tab", background="#1e1e1e", foreground="#00cc77", padding=[10, 5])
style.map("TNotebook.Tab", background=[("selected", "#00ff88")], foreground=[("selected", "#000000")])
style.configure("TProgressbar", background="#00ff88", troughcolor="#1e1e1e")

# Notebook principal - Abas
notebook_principal = ttk.Notebook(root)
notebook_principal.pack(fill='both', expand=True, padx=10, pady=10)

# ===== ABA 1: EXTRATOR DE URL =====
frame_extrator = ttk.Frame(notebook_principal)
notebook_principal.add(frame_extrator, text="🔍 Extrator URL")

# URL Frame
frame_url = ttk.Frame(frame_extrator)
frame_url.pack(pady=10, padx=10, fill='x')

ttk.Label(frame_url, text="Digite a URL do website", font=("Arial", 12, "bold")).pack(pady=5)
entrada_url = ttk.Entry(frame_url, width=90, font=("Arial", 11))
entrada_url.pack(pady=5)

# Botões
frame_buttons = ttk.Frame(frame_url)
frame_buttons.pack(pady=5)

tk.Button(frame_buttons, text="🔍 Extrair URL", bg="#00ff44", fg="black", font=("Arial", 10, "bold"), command=buscar_dados).pack(side='left', padx=4)
tk.Button(frame_buttons, text="📁 Abrir HTML", bg="#00ccff", fg="black", font=("Arial", 10, "bold"), command=abrir_arquivo).pack(side='left', padx=4)
tk.Button(frame_buttons, text="Abrir ASN BGP", bg="#ff8566", fg="black", font=("Arial", 10, "bold"), command=abrir_asn_bgp).pack(side='left', padx=5)
tk.Button(frame_buttons, text="💾 Salvar URL", bg="#ffcc00", fg="black", font=("Arial", 10, "bold"), command=salvar_urls).pack(side='left', padx=4)
tk.Button(frame_buttons, text="🌐 Abrir Todas Anônimo", bg="#ff4444", fg="black", font=("Arial", 10, "bold"), command=abrir_todas_urls_anonimas).pack(side='left', padx=4)
tk.Button(frame_buttons, text="📋 User-Agents", bg="#ff66ff", fg="black", font=("Arial", 10, "bold"), command=carregar_user_agents_txt).pack(side='left', padx=4)

entrada_pesquisa = ttk.Entry(frame_buttons, width=30)
entrada_pesquisa.pack(side="left", padx=5)
ttk.Button(frame_buttons, text="Pesquisar", command=pesquisar_urls).pack(side="left", padx=5)

barra_progresso = ttk.Progressbar(frame_extrator, length=600, mode='determinate')
barra_progresso.pack(pady=10)

# Abas do extrator
abas = ttk.Notebook(frame_extrator)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# General
frame_geral = ttk.Frame(abas)
aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_geral_texto.pack(fill='both', expand=True)
abas.add(frame_geral, text="General")

# Headers
frame_headers = ttk.Frame(abas)
aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_headers, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_cabecalhos_texto.pack(fill='both', expand=True)
abas.add(frame_headers, text="Headers")

# Response
frame_response = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_response, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_resposta_texto.pack(fill='both', expand=True)
abas.add(frame_response, text="Response")

# Initiator
frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_iniciador_texto.pack(fill='both', expand=True)
aba_iniciador_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_iniciador, text="Initiator")

# URL
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_urls_texto.pack(fill='both', expand=True)
aba_urls_texto.bind("<Double-Button-1>", abrir_url_no_chrome_anonima)
abas.add(frame_urls, text="URL")

# Payload
frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))
aba_payload_texto.pack(fill='both', expand=True)
abas.add(frame_payload, text="Payload")

# Preview
frame_visualizacao = ttk.Frame(abas)
canvas_frame = tk.Frame(frame_visualizacao, bg="#0f0f0f")
canvas_frame.pack(fill='both', expand=True)

aba_visualizacao_canvas = Canvas(canvas_frame, bg='#0a0a0a')
scrollbar_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=aba_visualizacao_canvas.yview)
aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)
scrollbar_v.pack(side='right', fill='y')
aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)

aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")
aba_visualizacao_texto.pack()
abas.add(frame_visualizacao, text="Preview")

# Save Images
frame_save = ttk.Frame(abas)
texto_save = scrolledtext.ScrolledText(frame_save, height=8, bg="#1e1e1e", fg="#00ff88")
texto_save.insert(tk.END, "Salvar screenshot e imagens do website.")
texto_save.config(state='disabled')
texto_save.pack(fill='x')
ttk.Button(frame_save, text="Salvar Screenshot", command=salvar_imagem).pack(pady=5)
ttk.Button(frame_save, text="Salvar Todas Imagens", command=salvar_todas_imagens).pack(pady=5)
abas.add(frame_save, text="Salvar Images")

# ===== ABA 2: HASH SCRAPER =====
frame_hash = ttk.Frame(notebook_principal)
notebook_principal.add(frame_hash, text="🔑 Hash Scraper")

hash_scraper = HashScraperGUI(frame_hash)
hash_scraper.pack(fill='both', expand=True)

# ===== RODAPÉ =====
frame_rodape = tk.Frame(root, bg="#1e1e1e", height=40)
frame_rodape.pack(side='bottom', fill='x')

instrucoes = (
    "Como usar: 1. Cole a URL → 2. Clique em 'Extrair URL' ou 'INICIAR SCAN' → "
    "3. Clique duplo em qualquer URL para abrir no Chrome Anônimo → "
    "4. Use 'Abrir Todas Anônimo' para abrir todas de uma vez"
)

label_rodape = tk.Label(
    frame_rodape,
    text=instrucoes,
    bg="#1e1e1e",
    fg="#00c3ff",
    font=("Arial", 9),
    wraplength=1200,
    justify="center"
)
label_rodape.pack(pady=8, padx=10)

label_versao = tk.Label(
    frame_rodape,
    text="AVANÇADO EXTRATOR DE URL WEBSITE + HASH SCRAPER | Clique duplo = Chrome Anônimo",
    bg="#1e1e1e",
    fg="#919191",
    font=("Arial", 8)
)
label_versao.pack(side='bottom', pady=2)

# =========================================================
# START
# =========================================================

root.mainloop()
