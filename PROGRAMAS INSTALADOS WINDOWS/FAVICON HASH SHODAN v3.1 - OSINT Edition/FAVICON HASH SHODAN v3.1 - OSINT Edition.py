import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser
import os

class FaviconFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1280x860")
        self.root.title("🔥 FAVICON HASH SHODAN v3.1 - OSINT Edition")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")
        
        self.favicon_urls = []
        self.hashes = []
        self.user_agents = []
        self.selected_ua = tk.StringVar()
        self.ua_file_path = tk.StringVar()
        
        self.style()
        self.create_ui()
        self.load_user_agents()

    def style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=18, background="#00ff41", troughcolor="#1a1a1a")

    def create_ui(self):
        # Header
        header = tk.Label(self.root, text="🔥 FAVICON HASH SHODAN", 
                         font=("Consolas", 20, "bold"), fg="#00ff41", bg="#0a0a0a")
        header.pack(pady=15)

        tk.Label(self.root, text="Digite a URL do WebSite", font=("Consolas", 12, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(pady=5)
        
        self.url_entry = tk.Entry(self.root, width=70, font=("Consolas", 12), 
                                 bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41")
        self.url_entry.pack(pady=8)

        # === USER-AGENT CONTROLS ===
        ua_frame = tk.Frame(self.root, bg="#0a0a0a")
        ua_frame.pack(pady=8)

        # Checkbox marcado por padrão
        self.use_ua_var = tk.BooleanVar(value=True)
        self.ua_check = tk.Checkbutton(ua_frame, text="✅ Usar User-Agent do arquivo .txt", 
                                      variable=self.use_ua_var, bg="#0a0a0a", fg="#00ff41",
                                      font=("Consolas", 11, "bold"), selectcolor="#1a1a1a")
        self.ua_check.pack(side=tk.LEFT, padx=10)

        self.select_ua_btn = tk.Button(ua_frame, text="📁 Selecionar & Carregar user_agents.txt", 
                                      command=self.select_and_load_ua_file, bg="#d4a50a", fg="black",
                                      font=("Consolas", 10, "bold"))
        self.select_ua_btn.pack(side=tk.LEFT, padx=10)

        self.ua_combo = ttk.Combobox(ua_frame, textvariable=self.selected_ua, width=90, font=("Consolas", 10))
        self.ua_combo.pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(self.root, bg="#0a0a0a")
        btn_frame.pack(pady=12)

        self.search_button = tk.Button(btn_frame, text="🚀 BUSCAR FAVICON SHODAN", 
                                      command=self.find_favicons, 
                                      font=("Consolas", 11, "bold"), bg="#0be64c", fg="black", width=25, height=2)
        self.search_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(btn_frame, text="💾 SALVAR INFORMAÇÕES", 
                                    command=self.save_to_file, 
                                    font=("Consolas", 11, "bold"), bg="#d4a50a", fg="black", width=25, height=2)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # Progress
        self.progress_label = tk.Label(self.root, text="Progresso:", font=("Consolas", 11), 
                                      fg="#00ff41", bg="#0a0a0a")
        self.progress_label.pack(pady=(5,0))

        self.progress_bar = ttk.Progressbar(self.root, length=900, mode='determinate', 
                                           style="TProgressbar")
        self.progress_bar.pack(pady=8)

        # Resultados
        result_label = tk.Label(self.root, text="RESULTADOS", font=("Consolas", 12, "bold"),
                               fg="#00ff41", bg="#0a0a0a")
        result_label.pack(pady=(10,5))

        self.result_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.result_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.result_text = tk.Text(self.result_frame, width=140, height=32, font=("Consolas", 10),
                                  bg="#0a0a0a", fg="#00ff41", insertbackground="#00ff41")
        scrollbar = tk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20,0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def select_and_load_ua_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo user_agents.txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.ua_file_path.set(file_path)
            self.load_user_agents()

    def load_user_agents(self):
        try:
            file_path = self.ua_file_path.get()
            if not file_path:
                file_path = "user_agents.txt"

            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.user_agents = [line.strip() for line in f if line.strip()]
                
                self.ua_combo['values'] = self.user_agents
                if self.user_agents:
                    self.selected_ua.set(self.user_agents[0])
                self.result_text.insert(tk.END, f"[+] {len(self.user_agents)} User-Agents carregados!\n")
            else:
                default_ua = "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53"
                self.user_agents = [default_ua]
                self.ua_combo['values'] = self.user_agents
                self.selected_ua.set(default_ua)
                self.result_text.insert(tk.END, "[+] Usando User-Agent padrão.\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"[!] Erro ao carregar: {e}\n")

    def get_headers(self):
        headers = {}
        if self.use_ua_var.get() and self.selected_ua.get():
            headers['User-Agent'] = self.selected_ua.get()
        else:
            # User-Agent mínimo se não estiver marcado
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        return headers

    def find_favicons(self):
        # ... (mesmo código anterior, sem alteração aqui)
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Entrada inválida", "Por favor, insira uma URL.")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            self.result_text.delete(1.0, tk.END)
            self.progress_bar['value'] = 10
            self.root.update_idletasks()

            headers = self.get_headers()

            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.favicon_urls = set()
           
            for link in soup.find_all('link', rel='icon'):
                favicon_url = link.get('href')
                if favicon_url:
                    self.favicon_urls.add(urljoin(url, favicon_url))
           
            default_favicon_url = urljoin(url, '/favicon.ico')
            default_favicon_response = requests.head(default_favicon_url, headers=headers)
           
            if default_favicon_response.status_code == 200:
                self.favicon_urls.add(default_favicon_url)
           
            self.progress_bar['value'] = 30
           
            if self.favicon_urls:
                for idx, favicon_url in enumerate(self.favicon_urls, 1):
                    self.result_text.insert(tk.END, f"{favicon_url}\n")
                    response = requests.get(favicon_url, headers=headers)
                      
                    if response.status_code == 200:
                        favicon = response.content
                        favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                        self.hashes.append((favicon_url, favicon_hash))
                        
                        self.result_text.insert(tk.END, f"\nO hash do favicon do website: {favicon_url:<60} HASH é: {favicon_hash}\n\n")
                        shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                        self.result_text.insert(tk.END, f"Link para pesquisa no Shodan: {shodan_url}\n")
                        self.result_text.insert(tk.END, f"\nhttp.favicon.hash:{favicon_hash}\n\n")
                        self.result_text.insert(tk.END, "="*100 + "\n\n")
                       
                        open_button = tk.Button(self.root, text=f"Abrir Shodan #{idx}", 
                                              bg="#ff8800", fg="black", font=("Consolas", 10, "bold"))
                        open_button.config(command=lambda u=shodan_url, btn=open_button: self.open_shodan(u, btn))
                        self.result_text.window_create(tk.END, window=open_button)
                        self.result_text.insert(tk.END, "\n\n")
                    else:
                        self.result_text.insert(tk.END, f"\nNão foi possível obter o favicon de {favicon_url}\n")
            else:
                self.result_text.insert(tk.END, "\nNenhum Ícone Encontrado\n")
                
            self.progress_bar['value'] = 100
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar os ícones: {e}")
            self.progress_bar['value'] = 0

    def open_shodan(self, shodan_url, button):
        webbrowser.open(shodan_url)
        button.config(bg="#0eb5e7", fg="black", text="✅ Aberto")

    def save_to_file(self):
        file_name = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_name:
            return
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.result_text.get(1.0, tk.END))
            messagebox.showinfo("Sucesso", f"As informações foram salvas no arquivo: {file_name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaviconFinderApp(root)
    root.mainloop()
