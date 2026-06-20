import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import time
from collections import deque

class WebCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WebCrawler Varredor de Sites")
        self.root.geometry("1050x800")
        self.root.state("zoomed")
        self.root.configure(bg='#f0f0f0')
        
        self.visited = set()
        self.to_visit = deque()
        self.to_visit_set = set()
        self.results = []
        self.crawling = False
        self.delay = 0.6
        
        self.create_widgets()
    
    def create_widgets(self):
        title_label = tk.Label(self.root, text="🌐 WebCrawler", 
                              font=("Helvetica", 18, "bold"), bg='#f0f0f0', fg='#1e3a8a')
        title_label.pack(pady=15)
        
        # === URL ===
        url_frame = tk.Frame(self.root, bg='#f0f0f0')
        url_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(url_frame, text="URL Inicial:", bg='#f0f0f0', font=("Helvetica", 11)).pack(side='left')
        self.url_entry = tk.Entry(url_frame, width=80, font=("Helvetica", 10))
        self.url_entry.pack(side='left', padx=10, fill='x', expand=True)
        self.url_entry.insert(0, "https://www.exemplo.com.br")
        
        # === Modo de Varredura (Novo!) ===
        mode_frame = tk.Frame(self.root, bg='#f0f0f0')
        mode_frame.pack(fill='x', padx=20, pady=8)
        
        tk.Label(mode_frame, text="🎯 Modo de Varredura:", bg='#f0f0f0', font=("Helvetica", 11, "bold")).pack(side='left')
        
        self.mode_var = tk.StringVar(value="Mais Profundo (Recomendado)")
        
        modes = [
            "Teste / Seguro",
            "Bom Equilíbrio",
            "Mais Profundo (Recomendado)",
            "Agressivo"
        ]
        
        self.mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=modes, state="readonly", width=35)
        self.mode_combo.pack(side='left', padx=10)
        self.mode_combo.bind("<<ComboboxSelected>>", self.apply_mode)
        
        # Opções manuais
        options_frame = tk.Frame(self.root, bg='#f0f0f0')
        options_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(options_frame, text="Máximo de páginas:", bg='#f0f0f0').pack(side='left')
        self.max_pages_var = tk.IntVar(value=2000)
        self.max_pages_entry = tk.Entry(options_frame, textvariable=self.max_pages_var, width=8)
        self.max_pages_entry.pack(side='left', padx=5)
        
        tk.Label(options_frame, text="Delay (segundos):", bg='#f0f0f0').pack(side='left', padx=(20,5))
        self.delay_var = tk.DoubleVar(value=0.6)
        self.delay_entry = tk.Entry(options_frame, textvariable=self.delay_var, width=6)
        self.delay_entry.pack(side='left')
        
        self.same_domain_var = tk.BooleanVar(value=True)
        self.same_domain_check = tk.Checkbutton(options_frame, text="🔒 Apenas mesmo domínio", 
                                               variable=self.same_domain_var, bg='#f0f0f0')
        self.same_domain_check.pack(side='left', padx=30)
        
        # Botões
        btn_frame = tk.Frame(self.root, bg='#f0f0f0')
        btn_frame.pack(pady=12)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Iniciar Varredura", command=self.start_crawl,
                                  bg='#10b981', fg='white', font=("Helvetica", 11, "bold"), padx=15, pady=8)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Parar", command=self.stop_crawl,
                                 bg='#ef4444', fg='white', font=("Helvetica", 11, "bold"), padx=15, pady=8, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        self.save_btn = tk.Button(btn_frame, text="💾 Salvar Resultados", command=self.save_results,
                                 bg='#8b5cf6', fg='white', font=("Helvetica", 11, "bold"), padx=15, pady=8)
        self.save_btn.pack(side='left', padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="🧹 Limpar", command=self.clear_results,
                                  bg='#3b82f6', fg='white', font=("Helvetica", 11, "bold"), padx=15, pady=8)
        self.clear_btn.pack(side='left', padx=5)
        
        # Progresso
        tk.Label(self.root, text="Progresso da Varredura:", bg='#f0f0f0', anchor='w').pack(fill='x', padx=20)
        self.progress = ttk.Progressbar(self.root, mode='determinate', length=950, maximum=100)
        self.progress.pack(fill='x', padx=20, pady=8)
        
        # Log e Resultados
        tk.Label(self.root, text="📋 Log da Varredura:", bg='#f0f0f0', anchor='w').pack(fill='x', padx=20)
        self.log_text = scrolledtext.ScrolledText(self.root, height=12, font=("Consolas", 9), bg='#1f2937', fg='#e5e7eb')
        self.log_text.pack(fill='both', expand=True, padx=20, pady=5)
        
        tk.Label(self.root, text="🔗 Páginas Encontradas (sem repetição):", bg='#f0f0f0', anchor='w').pack(fill='x', padx=20)
        self.results_text = scrolledtext.ScrolledText(self.root, height=14, font=("Consolas", 9))
        self.results_text.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Aplicar modo inicial
        self.apply_mode(None)
    
    def apply_mode(self, event):
        mode = self.mode_var.get()
        
        if mode == "Teste / Seguro":
            self.max_pages_var.set(400)
            self.delay_var.set(0.8)
        elif mode == "Bom Equilíbrio":
            self.max_pages_var.set(1200)
            self.delay_var.set(0.6)
        elif mode == "Mais Profundo (Recomendado)":
            self.max_pages_var.set(2500)
            self.delay_var.set(0.5)
        elif mode == "Agressivo":
            self.max_pages_var.set(6000)
            self.delay_var.set(0.7)
        
        self.log(f"Modo alterado para: {mode}")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    # (normalize_url, is_same_domain, crawl, update_results, save_results, etc. permanecem iguais)
    def normalize_url(self, url):
        url = url.rstrip('/')
        parsed = urlparse(url)
        netloc = parsed.netloc.replace('www.', '')
        normalized = f"{parsed.scheme}://{netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    
    def is_same_domain(self, url1, url2):
        d1 = urlparse(url1).netloc.replace('www.', '')
        d2 = urlparse(url2).netloc.replace('www.', '')
        return d1 == d2
    
    def crawl(self):
        self.crawling = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress['value'] = 0
        
        base_url = self.url_entry.get().strip()
        if not base_url.startswith("http"):
            base_url = "https://" + base_url
        
        max_pages = self.max_pages_var.get()
        self.delay = self.delay_var.get()
        same_domain = self.same_domain_var.get()
        
        self.to_visit.append(base_url)
        self.to_visit_set.add(base_url)
        
        self.log(f"🚀 Iniciando varredura - Modo: {self.mode_var.get()} | Máx: {max_pages} | Delay: {self.delay}s")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53'
        }
        
        while self.to_visit and len(self.visited) < max_pages and self.crawling:
            current_url = self.to_visit.popleft()
            self.to_visit_set.remove(current_url)
            
            if current_url in self.visited:
                continue
            
            try:
                self.log(f"Acessando → {current_url}")
                response = requests.get(current_url, headers=headers, timeout=12)
                response.raise_for_status()
                
                self.visited.add(current_url)
                self.results.append(current_url)
                
                progress_value = min(100, int((len(self.visited) / max_pages) * 100))
                self.progress['value'] = progress_value
                self.root.update_idletasks()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(current_url, link['href'])
                    full_url = self.normalize_url(full_url)
                    
                    if not full_url.startswith(('http://', 'https://')):
                        continue
                    if same_domain and not self.is_same_domain(full_url, base_url):
                        continue
                    if full_url not in self.visited and full_url not in self.to_visit_set:
                        self.to_visit.append(full_url)
                        self.to_visit_set.add(full_url)
                
                self.update_results()
                
            except Exception as e:
                self.log(f"❌ Erro: {str(e)[:90]}")
            
            time.sleep(self.delay)
        
        self.finish_crawl()
    
    def update_results(self):
        self.results_text.delete(1.0, tk.END)
        for url in list(self.results)[-100:]:
            self.results_text.insert(tk.END, f"✅ {url}\n")
    
    def save_results(self):
        if not self.results:
            messagebox.showwarning("Aviso", "Não há resultados para salvar!")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            initialfile="paginas_encontradas.txt"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Varredura - {time.strftime('%d/%m/%Y %H:%M')}\n")
                    f.write(f"Modo: {self.mode_var.get()}\n")
                    f.write(f"Total de páginas: {len(self.results)}\n\n")
                    for url in self.results:
                        f.write(f"{url}\n")
                messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
    
    def start_crawl(self):
        threading.Thread(target=self.crawl, daemon=True).start()
    
    def stop_crawl(self):
        self.crawling = False
        self.log("🛑 Varredura interrompida pelo usuário.")
        self.finish_crawl()
    
    def finish_crawl(self):
        self.progress['value'] = 100
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log(f"✅ Varredura finalizada! Total de páginas únicas: {len(self.visited)}")
    
    def clear_results(self):
        if messagebox.askyesno("Confirmar", "Limpar todos os resultados?"):
            self.visited.clear()
            self.to_visit.clear()
            self.to_visit_set.clear()
            self.results.clear()
            self.log_text.delete(1.0, tk.END)
            self.results_text.delete(1.0, tk.END)
            self.progress['value'] = 0
            self.log("🧹 Interface limpa.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebCrawlerGUI(root)
    root.mainloop()
