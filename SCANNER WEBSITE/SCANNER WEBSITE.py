import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import threading
import time
from collections import defaultdict
import urllib3

# Desativa aviso SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NeonVoidScanner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔥 SCANNER WEBSITE 🔥")
        self.root.geometry("1180x780")
        self.root.state('zoomed')
        self.root.configure(bg="#0A000F")
       
        self.root.option_add("*Font", "Consolas 11")
        self.create_widgets()
       
    def create_widgets(self):
        title = tk.Label(self.root, text="HTML VULNERABILITY SCANNER",
                        font=("Consolas", 20, "bold"), fg="#00FFAA", bg="#0A000F")
        title.pack(pady=15)
       
        frame_url = tk.Frame(self.root, bg="#0A000F")
        frame_url.pack(pady=8, fill="x", padx=30)
       
        tk.Label(frame_url, text="ALVO:", fg="#00FF41", bg="#0A000F",
                font=("Consolas", 12, "bold")).pack(side="left")
       
        self.url_entry = tk.Entry(frame_url, width=80, bg="#1A0022", fg="#00FFEE",
                                 insertbackground="#00FFAA", font=("Consolas", 11))
        self.url_entry.pack(side="left", padx=10, fill="x", expand=True)
        self.url_entry.insert(0, "https://")
       
        btn_frame = tk.Frame(self.root, bg="#0A000F")
        btn_frame.pack(pady=8)
       
        self.scan_btn = tk.Button(btn_frame, text="▶ INICIAR INTRUSÃO", command=self.start_scan,
                                  bg="#220033", fg="#00FF41", activebackground="#440066",
                                  font=("Consolas", 13, "bold"), height=2, width=28)
        self.scan_btn.pack(side="left", padx=10)
        
        self.save_btn = tk.Button(btn_frame, text="💾 SALVAR RESULTADOS .TXT", command=self.save_results,
                                  bg="#003322", fg="#00FFAA", activebackground="#006644",
                                  font=("Consolas", 13, "bold"), height=2, width=28)
        self.save_btn.pack(side="left", padx=10)
       
        self.result_text = scrolledtext.ScrolledText(self.root, height=38, bg="#000000", fg="#00FF41",
                                                     font=("Consolas", 11), wrap=tk.WORD)
        self.result_text.pack(pady=10, padx=30, fill="both", expand=True)
       
        self.status = tk.Label(self.root, text="AGUARDANDO ALVO...", fg="#008800", bg="#0A000F",
                              font=("Consolas", 10))
        self.status.pack(side="bottom", fill="x", padx=30, pady=8)
   
    def print_hacker(self, text, color="#00FF41", delay=0.008):
        self.result_text.tag_config(color, foreground=color)
        for char in text:
            self.result_text.insert(tk.END, char, color)
            self.result_text.see(tk.END)
            self.root.update()
            time.sleep(delay)
        self.result_text.insert(tk.END, "\n", color)
        self.result_text.see(tk.END)
   
    def clear_screen(self):
        self.result_text.delete("1.0", tk.END)
   
    def start_scan(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Erro", "Digite uma URL!")
            return
       
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
       
        self.clear_screen()
        self.scan_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.status.config(text="INTRUSÃO EM ANDAMENTO...", fg="#FFFF00")
       
        threading.Thread(target=self.scan, args=(url,), daemon=True).start()
   
    def scan(self, url):
        try:
            self.print_hacker("[+] CONECTANDO AO ALVO\n", "#00FF00", 0.02)
            self.print_hacker(f"Alvo: {url}", "#00AAFF", 0.01)
           
            # ================== USER-AGENT ATUALIZADO ==================
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53',
                
            }
            
            # ==========================================================
           
            response = requests.get(url, headers=headers, timeout=15, verify=False)
           
            soup = BeautifulSoup(response.text, 'html.parser')
           
            self.print_hacker("\n[+] EXTRAINDO URLS E RECURSOS\n", "#00FF00", 0.02)
           
            urls_dict = self.extract_urls(soup, url)
           
            links = urls_dict.get('Links', [])
            if links:
                self.print_hacker(f"[+] LINKS ENCONTRADOS: {len(links)}", "#00FFAA", 0.01)
                for i, link in enumerate(links, 1):
                    self.print_hacker(f"   {i} = {link}", "#00CCFF", 0.003)
            
            recursos = urls_dict.get('Recursos', [])
            if recursos:
                self.print_hacker(f"\n[+] RECURSOS ENCONTRADOS: {len(recursos)}", "#00FFAA", 0.01)
                for i, rec in enumerate(recursos, 1):
                    self.print_hacker(f"   {i} = {rec}", "#00CCFF", 0.003)
           
            contents = urls_dict.get('Content', [])
            if contents:
                self.print_hacker(f"\n[+] CONTENT ENCONTRADOS: {len(contents)}", "#A108C7", 0.01)
                for i, cont in enumerate(contents, 1):
                    self.print_hacker(f"   {i} = {cont}", "#07F81B", 0.005)
           
            forms = urls_dict.get('Forms', [])
            if forms:
                self.print_hacker(f"\n[+] FORMS ENCONTRADOS: {len(forms)}", "#FFAA00", 0.01)
                for i, form in enumerate(forms, 1):
                    self.print_hacker(f"   {i} = {form}", "#FF8800", 0.005)
           
            self.print_hacker("\n[+] ANALISANDO VULNERABILIDADES", "#FF5500", 0.03)
            vulns = self.analyze_vulnerabilities(soup, response, url)
           
            if vulns:
                for vuln in vulns:
                    self.print_hacker(f"⚠️  {vuln}", "#FF3333", 0.01)
            else:
                self.print_hacker("✅ Nenhuma vulnerabilidade crítica detectada", "#00FF00")
           
            self.print_hacker("\n[+] HEADERS HTTP RECEBIDOS", "#00FFAA", 0.03)
            for key, value in response.headers.items():
                self.print_hacker(f"   {key}: {value}", "#00CCFF", 0.003)
           
            self.print_hacker(f"\n[+] SCAN CONCLUÍDO | Status: {response.status_code}", "#00FF00", 0.02)
           
        except Exception as e:
            self.print_hacker(f"❌ ERRO: {str(e)}", "#FF0000", 0.01)
        finally:
            self.scan_btn.config(state="normal")
            self.save_btn.config(state="normal")
            self.status.config(text="INTRUSÃO FINALIZADA.", fg="#00FF00")
   
    def save_results(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Não há resultados para salvar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile=f"Resultados_Scan_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso!\n\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
   
    def extract_urls(self, soup, base_url):
        urls = defaultdict(set)
        
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(base_url, tag['href'])
            urls['Links'].add(full_url)
        
        for tag in soup.find_all(['img', 'script'], src=True):
            full_url = urljoin(base_url, tag['src'])
            urls['Recursos'].add(full_url)
        
        for tag in soup.find_all('link', href=True):
            full_url = urljoin(base_url, tag['href'])
            urls['Recursos'].add(full_url)

        for form in soup.find_all('form', action=True):
            full_url = urljoin(base_url, form['action'])
            urls['Forms'].add(full_url)
        
        for meta in soup.find_all('meta', content=True):
            content = meta.get('content', '')
            if content.startswith(('http://', 'https://')):
                full_url = urljoin(base_url, content)
                urls['Content'].add(full_url)
        
        return {k: sorted(list(v)) for k, v in urls.items()}
    
    def analyze_vulnerabilities(self, soup, response, target_url):
        vulns = []
        headers = response.headers
       
        if 'Content-Security-Policy' not in headers:
            vulns.append("Falta de Content-Security-Policy (vulnerável a XSS)")
        if 'X-Frame-Options' not in headers:
            vulns.append("Vulnerável a Clickjacking")
        if 'X-Content-Type-Options' not in headers:
            vulns.append("Falta de proteção contra MIME Sniffing")
        if 'Strict-Transport-Security' not in headers and target_url.startswith('https'):
            vulns.append("Falta de HSTS")
       
        for script in soup.find_all('script'):
            if script.string and re.search(r'eval\(|document\.write|innerHTML\s*=', str(script.string), re.I):
                vulns.append("Possível XSS via JavaScript perigoso")
       
        return vulns
   
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NeonVoidScanner()
    app.run()
