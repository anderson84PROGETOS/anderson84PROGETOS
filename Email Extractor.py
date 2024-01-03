import tkinter as tk
from tkinter import filedialog, scrolledtext
import re
import requests
from bs4 import BeautifulSoup

class EmailExtractorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Email Extractor")
        
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self.master, text="Digite a URL do site ou selecione um arquivo", font=("Arial", 12))
        self.label.pack(pady=10)

        self.url_entry = tk.Entry(self.master, width=40, font=("Arial", 12))
        self.url_entry.pack(pady=5)

        self.extract_button = tk.Button(self.master, text="Extrair E-mails", command=self.extract_emails, background="#11e7f2")
        self.extract_button.pack(pady=10)

        self.browse_button = tk.Button(self.master, text="Selecionar Arquivo", command=self.browse_file, background="#11f20a")
        self.browse_button.pack(pady=5)

        self.save_button = tk.Button(self.master, text="Salvar Arquivo", command=self.save_to_file, background="#fa7a83")
        self.save_button.pack(pady=5)          

        self.result_text = scrolledtext.ScrolledText(self.master, width=100, height=40, font=("Arial", 12))
        self.result_text.pack(pady=10)       

    def browse_file(self):
        file_path = filedialog.askopenfilename(title="Selecionar Arquivo", filetypes=[("Text files", "*.txt")])
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, file_path)

    def extract_emails(self):
        source = self.url_entry.get()
        if source.startswith("http"):
            emails = self.extract_emails_from_url(source)
        else:
            emails = self.extract_emails_from_file(source)

        if emails:
            result_text = "E-mails encontrados\n\n" + "\n".join(emails)
        else:
            result_text = "Nenhum e-mail encontrado."

        self.result_text.delete(1.0, tk.END)  # Limpar o conteúdo anterior
        self.result_text.insert(tk.END, result_text)

    def extract_emails_from_url(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.text)
            return emails
        except Exception as e:
            
            return []

    def extract_emails_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            return emails
        except Exception as e:
            
            return []

    def save_to_file(self):
        result_text = self.result_text.get(1.0, tk.END)
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

        if file_path:
            with open(file_path, 'w') as file:
                file.write(result_text)
                self.result_text.insert(tk.END, f"\nResultados salvos em {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = EmailExtractorApp(root)
    root.mainloop()
