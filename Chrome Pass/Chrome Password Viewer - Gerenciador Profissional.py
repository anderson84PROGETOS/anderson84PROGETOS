import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json
import os

class ChromePasswordViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Password Viewer - Gerenciador Profissional")
        self.root.geometry("1200x700")
        self.root.state("zoomed")
        self.root.configure(bg="#1e1e1e")
        
        self.data = []           # Todos os dados
        self.filtered_data = []  # Dados filtrados
        
        # Estilo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2d2d2d", foreground="#ffffff", fieldbackground="#2d2d2d")
        style.configure("Treeview.Heading", background="#0d7377", foreground="#ffffff", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#0d7377')])
        
        self.create_widgets()
        
    def create_widgets(self):
        # Título
        title = tk.Label(self.root, text="Visualizador de Senhas do Chrome", 
                        font=("Arial", 18, "bold"), bg="#1e1e1e", fg="#00ffcc")
        title.pack(pady=12)
        
        # Frame de Pesquisa
        search_frame = tk.Frame(self.root, bg="#1e1e1e")
        search_frame.pack(pady=8)
        
        tk.Label(search_frame, text="🔍 Pesquisar:", 
                font=("Arial", 10, "bold"), bg="#1e1e1e", fg="#ffffff").pack(side="left", padx=5)
        
        self.search_entry = tk.Entry(search_frame, width=50, font=("Arial", 11), bg="#FCFCFC", fg="#080808")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search())
        
        self.btn_search = tk.Button(search_frame, text="Pesquisar", 
                                   font=("Arial", 10, "bold"), bg="#0d7377", fg="white",
                                   activebackground="#0a5c61", width=12, command=self.search)
        self.btn_search.pack(side="left", padx=5)
        
        self.btn_clear_search = tk.Button(search_frame, text="Limpar", 
                                         font=("Arial", 10, "bold"), bg="#6c757d", fg="white",
                                         activebackground="#5a6268", width=10, command=self.clear_search)
        self.btn_clear_search.pack(side="left", padx=5)

        # Frame dos botões principais
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=10)
        
        self.btn_load = tk.Button(btn_frame, text="📂 Carregar Senhas do Chrome.csv", 
                                 font=("Arial", 10, "bold"), bg="#007acc", fg="white",
                                 activebackground="#005a99", width=30, height=2, command=self.load_csv)
        self.btn_load.grid(row=0, column=0, padx=10)
        
        self.btn_save = tk.Button(btn_frame, text="💾 Salvar como JSON", 
                                 font=("Arial", 10, "bold"), bg="#28a745", fg="white",
                                 activebackground="#218838", width=22, height=2, 
                                 command=self.save_json, state="disabled")
        self.btn_save.grid(row=0, column=1, padx=10)
        
        self.btn_clear = tk.Button(btn_frame, text="🗑️ Limpar Tabela", 
                                  font=("Arial", 10, "bold"), bg="#dc3545", fg="white",
                                  activebackground="#c82333", width=20, height=2, command=self.clear_table)
        self.btn_clear.grid(row=0, column=2, padx=10)
        
        # Tabela
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("Perfil", "URL", "Email", "Senha")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("Perfil", text="Perfil")
        self.tree.heading("URL", text="URL")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Senha", text="Senha")
        
        # Largura das colunas
        self.tree.column("Perfil", width=510)
        self.tree.column("URL", width=900)
        self.tree.column("Email", width=300)
        self.tree.column("Senha", width=580)
        
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Status
        self.status = tk.Label(self.root, text="Pronto - Nenhum arquivo carregado", 
                              bg="#1e1e1e", fg="#aaaaaa", anchor="w")
        self.status.pack(side="bottom", fill="x", padx=15, pady=8)
    
    def load_csv(self):
        default_path = os.path.expanduser("~/Downloads/Senhas do Chrome.csv")
        
        if os.path.exists(default_path):
            file_path = default_path
        else:
            file_path = filedialog.askopenfilename(
                title="Selecione o arquivo Senhas do Chrome.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        
        if not file_path:
            return
        
        try:
            self.tree.delete(*self.tree.get_children())
            self.data = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    perfil = row.get("name", row.get("Perfil", "Padrão"))
                    url = row.get("url", row.get("URL", ""))
                    email = row.get("username", row.get("Email", row.get("login", "")))
                    senha = row.get("password", row.get("Senha", ""))
                    
                    self.data.append({
                        "Perfil": perfil,
                        "URL": url,
                        "Email": email,
                        "Senha": senha
                    })
            
            self.filtered_data = self.data.copy()
            self.refresh_table()
            
            self.btn_save.config(state="normal")
            self.status.config(text=f"✅ {len(self.data)} senhas carregadas com sucesso!", fg="#00ff88")
            messagebox.showinfo("Sucesso", f"{len(self.data)} senhas carregadas!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar o arquivo:\n{str(e)}")
    
    def search(self):
        if not self.data:
            return
        term = self.search_entry.get().strip().lower()
        if not term:
            self.clear_search()
            return
        
        self.filtered_data = [
            item for item in self.data
            if term in item["Perfil"].lower() or
               term in item["URL"].lower() or
               term in item["Email"].lower() or
               term in item["Senha"].lower()
        ]
        self.refresh_table()
        self.status.config(text=f"🔍 {len(self.filtered_data)} resultado(s) para: '{term}'", fg="#00ffcc")
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.filtered_data = self.data.copy()
        self.refresh_table()
        self.status.config(text=f"✅ {len(self.data)} senhas carregadas", fg="#00ff88")
    
    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.filtered_data:
            self.tree.insert("", "end", values=(
                item["Perfil"], item["URL"], item["Email"], item["Senha"]
            ))
    
    def save_json(self):
        if not self.data:
            messagebox.showwarning("Aviso", "Nenhum dado para salvar!")
            return
        
        # === Escolha entre salvar tudo ou apenas o filtrado ===
        if self.filtered_data != self.data and len(self.filtered_data) > 0:
            choice = messagebox.askyesnocancel(
                title="Salvar como JSON",
                message=f"Você tem {len(self.filtered_data)} resultados filtrados de um total de {len(self.data)} senhas\n\n"
                        f"Deseja salvar\n\n\n"
                        f"✅ Sim  → Apenas os {len(self.filtered_data)} resultados da pesquisa\n\n\n"
                        f"❌ Não → Todas as {len(self.data)} senhas",
                icon="question"
            )
            
            if choice is None:  # Cancelou
                return
            save_all = not choice
        else:
            save_all = True  # Sem filtro ativo
        
        # Dados que serão salvos
        data_to_save = self.data if save_all else self.filtered_data
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="senhas_chrome_export.json"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
                qtd = len(data_to_save)
                messagebox.showinfo("Sucesso", 
                    f"{qtd} senhas salvas com sucesso!\n\n"
                    f"{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
    
    def clear_table(self):
        if messagebox.askyesno("Confirmar", "Limpar toda a tabela?"):
            self.tree.delete(*self.tree.get_children())
            self.data = []
            self.filtered_data = []
            self.btn_save.config(state="disabled")
            self.status.config(text="Tabela limpa.", fg="#aaaaaa")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChromePasswordViewer(root)
    root.mainloop()
