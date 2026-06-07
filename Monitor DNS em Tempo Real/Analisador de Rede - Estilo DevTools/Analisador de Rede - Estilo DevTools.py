import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
from datetime import datetime
import webbrowser
from PIL import Image, ImageTk
from io import BytesIO
import threading
import re
import random


class NetworkAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Rede - Estilo DevTools")
        self.root.geometry("1640x1020")
        
        self.response_data = {}
        self.user_agents = []
        self.current_user_agent = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(url_frame, text="URL:").pack(side='left')
        self.url_entry = ttk.Entry(url_frame, font=("Consolas", 11))
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        self.url_entry.insert(0, "https://google.com")
        
        self.analyze_btn = ttk.Button(url_frame, text="▶ Enviar", command=self.start_analysis)
        self.analyze_btn.pack(side='left', padx=(5, 0))
        
        self.load_ua_btn = ttk.Button(url_frame, text="📂 Carregar User-Agents.txt", command=self.load_user_agents)
        self.load_ua_btn.pack(side='left', padx=(5, 0))
        
        self.ua_label = ttk.Label(url_frame, text="Nenhum UA carregado", foreground="gray")
        self.ua_label.pack(side='left', padx=(10, 0))
        
        self.progress = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress.pack(fill='x', pady=(0, 8))
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        self.rede_tab = ttk.Frame(self.notebook)
        self.cabecalhos_tab = ttk.Frame(self.notebook)
        self.visualizacao_tab = ttk.Frame(self.notebook)
        self.resposta_tab = ttk.Frame(self.notebook)
        self.iniciador_tab = ttk.Frame(self.notebook)
        self.tempo_tab = ttk.Frame(self.notebook)
        self.cookies_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.rede_tab, text="Rede")
        self.notebook.add(self.cabecalhos_tab, text="Cabeçalhos")
        self.notebook.add(self.visualizacao_tab, text="Visualização")
        self.notebook.add(self.resposta_tab, text="Resposta")
        self.notebook.add(self.iniciador_tab, text="Iniciador")
        self.notebook.add(self.tempo_tab, text="Tempo")
        self.notebook.add(self.cookies_tab, text="Cookies")
        
        self.setup_rede_tab()
        self.setup_cabecalhos_tab()
        self.setup_visualizacao_tab()
        self.setup_resposta_tab()
        self.setup_iniciador_tab()
        self.setup_tempo_tab()
        self.setup_cookies_tab()
    
    def load_user_agents(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo user-agents.txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.user_agents = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if self.user_agents:
                self.current_user_agent = random.choice(self.user_agents)
                self.ua_label.config(text=f"{len(self.user_agents)} UAs carregados ✓", foreground="green")
                messagebox.showinfo("Sucesso", f"{len(self.user_agents)} User-Agents carregados!")
            else:
                messagebox.showwarning("Aviso", "O arquivo está vazio.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler o arquivo:\n{str(e)}")
    
    # ====================== ABA RESPOSTA (MELHORADA) ======================
    def setup_resposta_tab(self):
        frame = ttk.Frame(self.resposta_tab)
        frame.pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=(0, 5))
        ttk.Button(btn_frame, text="🌐 Abrir no Navegador", command=self.open_in_browser).pack(side='left', padx=5)
        
        self.response_text = scrolledtext.ScrolledText(
            frame, wrap=tk.NONE, font=("Consolas", 10), background="#f8f9fa"
        )
        self.response_text.pack(fill='both', expand=True)
        
        self.response_text.tag_configure("title", font=("Consolas", 12, "bold"), foreground="#1a73e8")
        self.response_text.tag_configure("key", font=("Consolas", 10, "bold"), foreground="#0066cc")
        self.response_text.tag_configure("highlight", foreground="#d32f2f", background="#ffebee")
        self.response_text.tag_configure("url", foreground="#0066cc", underline=True)
        self.response_text.tag_configure("license", foreground="#006400", font=("Consolas", 10, "bold"))
    
    def update_resposta(self, response):
        self.response_text.delete(1.0, tk.END)
        text = self.response_text
        content = self.response_data['content']
        url = self.response_data['url']
        
        text.insert(tk.END, "📄 ANÁLISE DA RESPOSTA\n", "title")
        text.insert(tk.END, "="*70 + "\n\n")
        
        text.insert(tk.END, "🔗 URL: ", "key")
        text.insert(tk.END, f"{url}\n")
        text.insert(tk.END, "Status: ", "key")
        text.insert(tk.END, f"{response.status_code} {response.reason}\n")
        text.insert(tk.END, "User-Agent usado: ", "key")
        text.insert(tk.END, f"{self.current_user_agent[:80]}...\n" if self.current_user_agent else "Padrão\n")
        text.insert(tk.END, "Tipo: ", "key")
        text.insert(tk.END, f"{self.response_data['content_type']}\n")
        text.insert(tk.END, "Tamanho: ", "key")
        text.insert(tk.END, f"{self.response_data['content_size']:,} bytes\n\n")
        
        # ==================== INFORMAÇÕES IMPORTANTES ====================
        text.insert(tk.END, "🔍 INFORMAÇÕES IMPORTANTES\n", "title")
        text.insert(tk.END, "-"*55 + "\n")
        
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            text.insert(tk.END, "📌 Título: ", "key")
            text.insert(tk.END, f"{title_match.group(1).strip()}\n\n")
        
        copyright_matches = re.findall(r'Copyright.*?[0-9]{4}.*?', content, re.IGNORECASE)
        for cp in copyright_matches[:6]:
            text.insert(tk.END, f"© {cp.strip()}\n", "highlight")
        
        license_match = re.search(r'SPDX-License-Identifier:?\s*([^\n<]+)', content, re.IGNORECASE)
        if license_match:
            text.insert(tk.END, f"📜 Licença: {license_match.group(1).strip()}\n", "license")
        
        text.insert(tk.END, "\n" + "="*60 + "\n\n")
        
        # ==================== URLs ENCONTRADAS (MELHORADO) ====================
        text.insert(tk.END, "🔗 URLs ENCONTRADAS NO HTML (http/https)\n", "title")
        text.insert(tk.END, "-"*65 + "\n\n")
        
        # Regex melhorada - só URLs completas com http/https
        url_pattern = r'https?://[^\s"<>{}|\\]+\.[^\s"<>{}|\\]+'
        urls = re.findall(url_pattern, content)
        
        # Remover duplicatas mantendo a ordem
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        
        if unique_urls:
            for i, link in enumerate(unique_urls[:100], 1):   # limite aumentado para 100
                text.insert(tk.END, f"{i:2d}. ", "key")
                text.insert(tk.END, f"{link}\n", "url")
        else:
            text.insert(tk.END, "Nenhuma URL completa (http/https) encontrada.\n")
        
        text.insert(tk.END, f"\nTotal de URLs únicas encontradas: {len(unique_urls)}\n\n")
        
        # ==================== CONTEÚDO RELEVANTE ====================
        text.insert(tk.END, "📝 TRECHO RELEVANTE DO CONTEÚDO\n", "title")
        text.insert(tk.END, "-"*55 + "\n\n")
        preview = content[:12000]
        text.insert(tk.END, preview)
        if len(content) > 12000:
            text.insert(tk.END, "\n\n... [Conteúdo truncado]", "highlight")
    
    # ====================== ANÁLISE ======================
    def start_analysis(self):
        self.analyze_btn.config(state='disabled')
        self.progress['value'] = 0
        threading.Thread(target=self.analyze_network, daemon=True).start()
    
    def analyze_network(self):
        url = self.url_entry.get().strip()
        if not url.startswith("http"):
            url = "https://" + url
        
        try:
            self.update_progress(5)
            start = datetime.now()
            
            headers = {}
            if self.user_agents:
                self.current_user_agent = random.choice(self.user_agents)
                headers = {'User-Agent': self.current_user_agent}
            
            response = requests.get(
                url, 
                headers=headers,
                allow_redirects=True, 
                timeout=15
            )
            end = datetime.now()
            self.update_progress(45)
            
            total_ms = (end - start).total_seconds() * 1000
            
            self.response_data = {
                "url": response.url,
                "status": response.status_code,
                "reason": response.reason,
                "headers": dict(response.headers),
                "cookies": response.cookies,
                "content": response.text,
                "content_size": len(response.content),
                "content_type": response.headers.get('Content-Type', ''),
                "encoding": response.encoding,
                "timing_ms": total_ms,
                "request_headers": dict(response.request.headers) if response.request else {}
            }
            
            self.update_progress(65)
            self.update_all_tabs(response)
            self.update_progress(80)
            self.load_screenshot()
            self.update_progress(100)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao acessar o site:\n{str(e)}"))
        finally:
            self.root.after(0, self.finish_analysis)
    
    def update_all_tabs(self, response):
        self.update_rede_tab(response)
        self.update_cabecalhos(response)
        self.update_resposta(response)
        self.update_cookies(response)
        self.update_tempo(response)
    
    def update_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))
    
    def finish_analysis(self):
        self.analyze_btn.config(state='normal')
        self.progress['value'] = 100
    
    # ====================== RESTANTE DO CÓDIGO ======================
    def update_cabecalhos(self, response):
        self.headers_text.delete(1.0, tk.END)
        text = self.headers_text
        text.insert(tk.END, "🔗 URL: ", "section")
        text.insert(tk.END, f"{response.url}\n")
        text.insert(tk.END, "📡 Status: ", "section")
        text.insert(tk.END, f"{response.status_code} {response.reason}\n")
        text.insert(tk.END, "⏱️ Tempo Total: ", "section")
        text.insert(tk.END, f"{self.response_data['timing_ms']:.2f} ms\n\n")
        
        text.insert(tk.END, "📤 REQUEST HEADERS\n", "section")
        text.insert(tk.END, "="*50 + "\n")
        for key in sorted(self.response_data.get("request_headers", {})):
            text.insert(tk.END, f"{key}: ", "key")
            text.insert(tk.END, f"{self.response_data['request_headers'][key]}\n", "value")
        
        text.insert(tk.END, "\n📥 RESPONSE HEADERS\n", "section")
        text.insert(tk.END, "="*50 + "\n")
        important = ["Content-Type", "Content-Length", "Server", "Date", "Cache-Control", "Set-Cookie", "Location", "Expires"]
        resp_headers = self.response_data.get("headers", {})
        for key in sorted(resp_headers.keys()):
            if key in important:
                text.insert(tk.END, f"{key}: ", "key")
                text.insert(tk.END, f"{resp_headers[key]}\n", "value")
        text.insert(tk.END, "\n" + "-"*30 + " Outros Headers " + "-"*30 + "\n\n")
        for key in sorted(resp_headers.keys()):
            if key not in important:
                text.insert(tk.END, f"{key}: ", "key")
                text.insert(tk.END, f"{resp_headers[key]}\n", "value")
    
    def update_rede_tab(self, response):
        for i in self.tree.get_children():
            self.tree.delete(i)
        size = f"{self.response_data['content_size']/1024:.1f} KB"
        tempo = f"{self.response_data['timing_ms']:.1f} ms"
        self.tree.insert("", "end", values=(
            response.url[:85] + "..." if len(response.url) > 85 else response.url,
            f"{response.status_code} {response.reason}",
            response.headers.get('Content-Type', 'unknown').split(';')[0][:40],
            size,
            tempo,
            "Requisição Principal"
        ))
    
    def update_cookies(self, response):
        for i in self.cookies_tree.get_children():
            self.cookies_tree.delete(i)
        for cookie in response.cookies:
            self.cookies_tree.insert("", "end", values=(
                cookie.name,
                cookie.value[:55] + ("..." if len(cookie.value) > 55 else ""),
                cookie.domain,
                cookie.path,
                "Sim" if cookie.secure else "Não",
                "Sim" if getattr(cookie, 'has_nonstandard_attr', lambda x: False)('HttpOnly') else "Não",
                cookie.expires or "Sessão"
            ))
    
    def update_tempo(self, response):
        total = self.response_data['timing_ms']
        self.timing_vars["Tempo Total"].set(f"{total:.1f} ms")
        self.timing_vars["Waiting (TTFB)"].set(f"{total*0.6:.1f} ms")
        self.timing_vars["Download do Conteúdo"].set(f"{total*0.3:.1f} ms")
        for k in ["DNS Lookup", "Conexão TCP", "Handshake TLS", "Tempo de Redirecionamento"]:
            self.timing_vars[k].set("—")
    
    def load_screenshot(self):
        if not self.response_data.get("url"):
            return
        url = self.response_data["url"]
        try:
            screenshot_url = f"https://image.thum.io/get/width/1600/fullpage/{url}"
            screen = requests.get(screenshot_url, timeout=80)
            screen.raise_for_status()
            img_data = BytesIO(screen.content)
            img_original = Image.open(img_data)
            largura = 1150
            ratio = largura / img_original.width
            altura = int(img_original.height * ratio)
            img_resize = img_original.resize((largura, altura), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img_resize)
            self.visual_canvas.delete("all")
            self.visual_canvas.create_image(0, 0, anchor='nw', image=tk_img)
            self.visual_canvas.image = tk_img
            self.visual_canvas.config(scrollregion=(0, 0, largura, altura))
        except:
            pass
    
    def open_in_browser(self):
        if self.response_data.get("url"):
            webbrowser.open(self.response_data["url"])

    # ====================== SETUP DAS OUTRAS ABAS ======================
    def setup_rede_tab(self):
        frame = ttk.Frame(self.rede_tab)
        frame.pack(fill='both', expand=True)
        columns = ("Nome", "Status", "Tipo", "Tamanho", "Tempo", "Iniciador")
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        widths = [480, 90, 140, 110, 110, 200]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        vscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vscroll.pack(side='right', fill='y')
        hscroll.pack(side='bottom', fill='x')
        self.tree.bind('<Double-1>', lambda e: self.notebook.select(self.resposta_tab))
    
    def setup_cabecalhos_tab(self):
        frame = ttk.Frame(self.cabecalhos_tab)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(frame, text="Cabeçalhos HTTP", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0,8))
        self.headers_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10), background="#f8f9fa")
        self.headers_text.pack(fill='both', expand=True)
        self.headers_text.tag_configure("section", font=("Consolas", 11, "bold"), foreground="#1a73e8")
        self.headers_text.tag_configure("key", font=("Consolas", 10, "bold"), foreground="#0066cc")
        self.headers_text.tag_configure("value", foreground="#333333")
    
    def setup_visualizacao_tab(self):
        frame = ttk.Frame(self.visualizacao_tab)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text="Visualização do Site (Screenshot - Alta Qualidade)", font=("Arial", 12, "bold")).pack(pady=8)
        canvas_frame = ttk.Frame(frame); canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.visual_canvas = tk.Canvas(canvas_frame, bg="#f8f9fa", highlightthickness=1)
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.visual_canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.visual_canvas.xview)
        self.visual_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.visual_canvas.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y'); h_scroll.pack(side='bottom', fill='x')
        ttk.Button(frame, text="🔄 Atualizar Screenshot", command=self.load_screenshot).pack(pady=8)
    
    def setup_iniciador_tab(self):
        frame = ttk.Frame(self.iniciador_tab); frame.pack(fill='both', expand=True, padx=15, pady=15)
        self.iniciador_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10), background="#f8f9fa")
        self.iniciador_text.pack(fill='both', expand=True)
        self.iniciador_text.insert(tk.END, "Iniciador: Requisição Principal\n\nEsta requisição foi iniciada manualmente pelo usuário.")
    
    def setup_tempo_tab(self):
        frame = ttk.LabelFrame(self.tempo_tab, text="Detalhamento de Tempo", padding=15)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.timing_vars = {}
        timings = ["Tempo Total", "DNS Lookup", "Conexão TCP", "Handshake TLS", "Waiting (TTFB)", "Download do Conteúdo", "Tempo de Redirecionamento"]
        for label in timings:
            row = ttk.Frame(frame); row.pack(fill='x', pady=6)
            ttk.Label(row, text=label + ":", width=28, anchor='w').pack(side='left')
            var = tk.StringVar(value="—")
            self.timing_vars[label] = var
            ttk.Label(row, textvariable=var, font=("Consolas", 10, "bold")).pack(side='left')
    
    def setup_cookies_tab(self):
        columns = ("Nome", "Valor", "Domínio", "Caminho", "Seguro", "HttpOnly", "Expira")
        self.cookies_tree = ttk.Treeview(self.cookies_tab, columns=columns, show='headings')
        for col in columns: self.cookies_tree.heading(col, text=col)
        self.cookies_tree.column("Nome", width=150); self.cookies_tree.column("Valor", width=500)
        self.cookies_tree.column("Domínio", width=180); self.cookies_tree.column("Caminho", width=120)
        self.cookies_tree.column("Seguro", width=80); self.cookies_tree.column("HttpOnly", width=80)
        self.cookies_tree.column("Expira", width=150)
        scroll = ttk.Scrollbar(self.cookies_tab, orient="vertical", command=self.cookies_tree.yview)
        self.cookies_tree.configure(yscrollcommand=scroll.set)
        self.cookies_tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkAnalyzerGUI(root)
    root.mainloop()
