import tkinter as tk
from tkinter import ttk, messagebox
import requests
import webbrowser
import threading

class RobotsTxtApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robots.txt Explorer")
        self.root.geometry("1050x900")
        self.root.configure(bg="#f5f7fa")

        # Estilo
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", 
                           background="#3498db",
                           foreground="white",
                           font=("Segoe UI", 11, "bold"),
                           padding=10)
        self.style.map("TButton",
                      background=[("active", "#07ad9d")])
        
        self.style.configure("TLabel",
                           background="#f5f7fa",
                           font=("Segoe UI", 12))

        # Container principal
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        # Título
        self.title_label = ttk.Label(self.main_frame,
                                   text="Robots.txt Explorer",
                                   font=("Segoe UI", 24, "bold"),
                                   foreground="#2c3e50")
        self.title_label.pack(pady=(0, 20))

        # Label da URL
        self.url_label = ttk.Label(self.main_frame,
                                 text="Digite a URL completa do site (exemplo: https://www.google.com)")
        self.url_label.pack(pady=(0, 10))

        # Frame para entrada e botões
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill="x", pady=10)

        # Campo de entrada
        self.url_entry = ttk.Entry(self.input_frame, font=("Segoe UI", 11), width=60)
        self.url_entry.pack(side="left", padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.get_robots_txt_thread())

        # Botões
        self.get_button = ttk.Button(self.input_frame,
                                   text="Obter robots.txt",
                                   command=self.get_robots_txt_thread)
        self.get_button.pack(side="left", padx=5)

        self.google_button = ttk.Button(self.input_frame,
                                      text="Pesquisar no Google",
                                      command=self.search_on_google)
        self.google_button.pack(side="left", padx=5)

        # Botão para abrir robots.txt diretamente
        self.open_button = ttk.Button(self.input_frame,
                                    text="Abrir robots.txt",
                                    command=self.open_robots_txt)
        self.open_button.pack(side="left", padx=5)

        # Área de resultado
        self.result_frame = tk.Frame(self.main_frame, bg="#0a0a0a", bd=1, relief="solid")
        self.result_frame.pack(expand=True, fill="both", pady=20)

        # Área de texto com cor de texto #07ed82
        self.result_text = tk.Text(self.result_frame,
                                 font=("Segoe UI", 11),
                                 wrap="word",
                                 width=100,
                                 height=40,
                                 bg="#0a0a0a",
                                 fg="#07ed82",  # Cor do texto adicionada
                                 bd=0)
        self.result_text.pack(side="left", expand=True, fill="both", padx=(10, 0), pady=10)

        # Scrollbar colada à direita
        scrollbar = ttk.Scrollbar(self.result_frame, command=self.result_text.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10))
        self.result_text.config(yscrollcommand=scrollbar.set)

        # Headers para evitar erro 403
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

    def get_robots_txt(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Atenção", "Por favor, digite uma URL válida.")
            return

        if not url.endswith('/'):
            url += '/'

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Carregando...")
        self.root.update()

        try:
            response = requests.get(url + "robots.txt", headers=self.headers, timeout=10)
            response.raise_for_status()
            content = response.text if response.text else "Nenhum conteúdo encontrado"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, content)
        except requests.RequestException as e:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Erro: {str(e)}")

    def get_robots_txt_thread(self):
        threading.Thread(target=self.get_robots_txt, daemon=True).start()

    def search_on_google(self):
        query = self.url_entry.get().strip() + '/robots.txt'
        if not query:
            messagebox.showwarning("Atenção", "Por favor, digite algo para pesquisar.")
            return
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def open_robots_txt(self):
        query = self.url_entry.get().strip() + '/robots.txt'
        if not query:
            messagebox.showwarning("Atenção", "Por favor, digite uma URL válida.")
            return
        webbrowser.open(f"{query}")

def main():
    root = tk.Tk()
    app = RobotsTxtApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
