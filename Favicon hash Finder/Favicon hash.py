import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import codecs
import mmh3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser

class FaviconFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1240x960")  # Ajusta o tamanho da janela
        self.root.title("Favicon Hash")
        
        # Layout
        tk.Label(root, text="Digite a URL do WebSite", font=("TkDefaultFont", 11, "bold")).pack(pady=5)
        self.url_entry = tk.Entry(root, width=40, font=("TkDefaultFont", 11, "bold"))
        self.url_entry.pack(pady=5)
        
        self.search_button = tk.Button(root, text="Buscar favicon", command=self.find_favicons, font=("TkDefaultFont", 10, "bold"), bg='#0cf27b')
        self.search_button.pack(pady=5)

        self.save_button = tk.Button(root, text="Salvar Informações", command=self.save_to_file, font=("TkDefaultFont", 10, "bold"), bg='#f7233b')
        self.save_button.pack(pady=5)
        
        self.result_frame = tk.Frame(root)
        self.result_frame.pack(pady=5)
        
        self.result_text = tk.Text(self.result_frame, width=128, height=42, font=("TkDefaultFont", 11, "bold"))
        self.result_text.pack(side=tk.LEFT, fill=tk.Y)
        
        self.scrollbar = tk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text.config(yscrollcommand=self.scrollbar.set)
        
        self.favicon_urls = []
        self.hashes = []

    def find_favicons(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Entrada inválida", "Por favor, insira uma URL.")
            return
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        try:
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
            
            self.result_text.delete(1.0, tk.END)
            self.hashes = []
            
            if self.favicon_urls:                
                
                for favicon_url in self.favicon_urls:
                    self.result_text.insert(tk.END, f"{favicon_url}\n")
                    response = requests.get(favicon_url, headers=headers)    
                       
                    if response.status_code == 200:
                        favicon = response.content
                        favicon_hash = mmh3.hash(codecs.encode(favicon, "base64"))
                        self.hashes.append((favicon_url, favicon_hash))
                        self.result_text.insert(tk.END, f"\nO hash do favicon do website: {favicon_url} é: {favicon_hash}\n\n")
                        
                        shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
                        self.result_text.insert(tk.END, f"Link para pesquisa no Shodan: {shodan_url}\n")
                        
                        # Exibe o formato "http.favicon.hash:{hash_value}" logo abaixo do link Shodan
                        self.result_text.insert(tk.END, f"\nhttp.favicon.hash:{favicon_hash}\n\n")
                        
                        self.result_text.insert(tk.END, "\n===============================================================================================================\n\n")
                        
                        # Adiciona um botão para abrir o link do Shodan
                        open_button = tk.Button(self.result_frame, text="Abrir no Shodan", command=lambda url=shodan_url: self.open_shodan(url), font=("TkDefaultFont", 10, "bold"), bg='#fa9405')
                        open_button.pack(pady=2)
                        
                        # Muda a cor do botão quando clicado
                        open_button.bind("<Button-1>", lambda e, btn=open_button: self.change_button_color(btn))

                    else:
                        self.result_text.insert(tk.END, f"\nNão foi possível obter o favicon de {favicon_url}\n")
            else:
                self.result_text.insert(tk.END, "\nNenhum Ícone Encontrado\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar os ícones: {e}")

    def open_shodan(self, shodan_url):
        webbrowser.open(shodan_url)

    def change_button_color(self, button):
        button.config(bg='#05fa84')

    def save_to_file(self):
        file_name = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_name:
            return
        
        try:
            with open(file_name, 'w') as file:
                file.write(self.result_text.get(1.0, tk.END))  # Captura o texto exibido na caixa de texto
            messagebox.showinfo("Sucesso", f"As informações foram salvas no arquivo: {file_name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")        

if __name__ == "__main__":
    root = tk.Tk()
    app = FaviconFinderApp(root)
    root.mainloop()
