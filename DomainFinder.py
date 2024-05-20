import socket
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Domain Finder")
        self.wordlist_path = ""
        self.resultados = []

        self.create_widgets()

    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, padx=20, pady=20)

        # Nome do website
        self.label_website = tk.Label(main_frame, text="Digite o Nome do website", font=('TkDefaultFont', 12, 'bold'))
        self.label_website.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        self.entry_website = tk.Entry(main_frame, width=30, font=('TkDefaultFont', 12, 'bold'))
        self.entry_website.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Botão para iniciar a pesquisa
        self.btn_start = tk.Button(main_frame, text="Iniciar Pesquisa", command=self.start_search, bg="#00FF00", font=("TkDefaultFont", 11, "bold"))
        self.btn_start.grid(row=2, column=0, columnspan=2, pady=10)

        # Botão para procurar arquivo
        self.btn_browse = tk.Button(main_frame, text="Procurar word.txt", command=self.browse_file, bg="#03fcfc", font=("TkDefaultFont", 10, "bold"))
        self.btn_browse.grid(row=3, column=0, columnspan=2, pady=10)

        # Campo de texto para exibir resultados
        self.text_results = scrolledtext.ScrolledText(main_frame, width=100, height=33, font=('TkDefaultFont', 12, 'bold'))
        self.text_results.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Botão para salvar resultados
        self.btn_save = tk.Button(main_frame, text="Salvar Resultados", command=self.save_results, bg="#ffc803", font=("TkDefaultFont", 10, "bold"))
        self.btn_save.grid(row=5, column=0, columnspan=2, pady=10)

    def browse_file(self):
        self.wordlist_path = filedialog.askopenfilename(title="Selecione o arquivo word.txt", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if self.wordlist_path:
            messagebox.showinfo("Arquivo Selecionado", f"Arquivo selecionado: {self.wordlist_path}")
        else:
            messagebox.showwarning("Nenhum Arquivo", "Nenhum arquivo foi selecionado.")

    def start_search(self):
        self.resultados = []
        alvo = self.entry_website.get().strip()
        if not alvo:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira o nome do website.")
            return
        
        if not self.wordlist_path:
            messagebox.showwarning("Arquivo não encontrado", "Por favor, selecione o arquivo word.txt.")
            return
        
        self.text_results.delete(1.0, tk.END)
        try:
            with open(self.wordlist_path, "r") as word:
                for linha in word:
                    txt = linha.strip()
                    result = txt + alvo
                    try:
                        ip = socket.gethostbyname(result)
                        result_text = f"HOST ENCONTRADO: {result} ====> IP: {ip}\n"
                        self.text_results.insert(tk.END, result_text)
                        self.resultados.append(result_text)
                        self.root.update()  # Atualiza a interface para exibir imediatamente o resultado
                    except socket.gaierror:
                        continue
        except FileNotFoundError:
            messagebox.showerror("Erro", "Arquivo da wordlist não encontrado.")
        
        total_domains_text = f"\n\n\nTotal de Domínios Encontrados: {len(self.resultados)}\n\n"
        self.text_results.insert(tk.END, total_domains_text)

    def save_results(self):
        if not self.resultados:
            messagebox.showwarning("Nenhum Resultado", "Nenhum resultado para salvar.")
            return

        nome_arquivo = filedialog.asksaveasfilename(title="Salvar Resultados", defaultextension=".txt", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if not nome_arquivo:
            return

        try:
            with open(nome_arquivo, "w") as arquivo:
                alvo = self.entry_website.get().strip()
                arquivo.write(f"Resultados para o alvo: {alvo}\n\n")
                arquivo.writelines(self.resultados)
                arquivo.write(f"\n\nTotal de Domínios Encontrados: {len(self.resultados)}\n")
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except IOError:
            messagebox.showerror("Erro", "Erro ao salvar os resultados.")

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = App(root)
    root.mainloop()
