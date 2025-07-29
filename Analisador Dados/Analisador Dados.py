import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
import PyPDF2
import os

class AdvancedDataAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador Dados")
        self.root.geometry("1000x700")
        self.root.state('zoomed')  # Maximizar no Windows
        self.df = None

        # Topo
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        tk.Button(top_frame, text="Abrir Arquivo", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Estatísticas", command=self.show_stats).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Correlação", command=self.show_correlation).pack(side=tk.LEFT, padx=5)

        self.column_var = tk.StringVar()
        self.chart_type_var = tk.StringVar(value="Linha")
        self.combo_col = ttk.Combobox(top_frame, textvariable=self.column_var, state="readonly")
        self.combo_col.pack(side=tk.LEFT, padx=5)

        self.combo_chart = ttk.Combobox(top_frame, textvariable=self.chart_type_var, state="readonly",
                                        values=["Linha", "Barras", "Histograma", "Dispersão"])
        self.combo_chart.pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="Plotar Gráfico", command=self.plot_graph).pack(side=tk.LEFT, padx=5)

        # Tabela e Scroll
        table_frame = tk.Frame(root)
        table_frame.pack(expand=True, fill=tk.BOTH)

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        hsb = ttk.Scrollbar(root, orient="horizontal")
        hsb.pack(fill=tk.X)

        self.tree = ttk.Treeview(table_frame, show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Todos os arquivos", "*.*"),
            ("CSV", "*.csv"), ("Excel", "*.xlsx"),
            ("JSON", "*.json"),
            ("Texto", "*.txt"),
            ("PDF", "*.pdf"),
            ("Word", "*.docx")
        ])
        if not file_path:
            return

        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                self.df = pd.read_csv(file_path)
            elif ext == '.xlsx':
                self.df = pd.read_excel(file_path)
            elif ext == '.json':
                self.df = pd.read_json(file_path)
            elif ext == '.txt':
                self.df = pd.read_csv(file_path, delimiter=None, engine='python')
            elif ext == '.docx':
                self.df = self.load_docx_as_df(file_path)
            elif ext == '.pdf':
                self.df = self.load_pdf_as_df(file_path)
            else:
                raise ValueError("Formato não suportado.")
            
            if self.df is not None:
                self.display_data()
                self.populate_column_selector()
            else:
                messagebox.showwarning("Aviso", "Nenhum dado carregado.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar o arquivo:\n{e}")

    def load_docx_as_df(self, path):
        doc = Document(path)
        linhas = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return pd.DataFrame(linhas, columns=["Conteúdo"]) if linhas else None

    def load_pdf_as_df(self, path):
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            texto = ''
            for page in reader.pages:
                texto += page.extract_text() or ''
        linhas = texto.splitlines()
        return pd.DataFrame(linhas, columns=["Conteúdo"]) if linhas else None

    def display_data(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.df.columns)

        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor=tk.W)

        for i, row in self.df.iterrows():
            if i > 500:
                break
            self.tree.insert("", "end", values=list(row))

    def populate_column_selector(self):
        numeric_cols = self.df.select_dtypes(include='number').columns.tolist()
        self.combo_col['values'] = numeric_cols
        if numeric_cols:
            self.column_var.set(numeric_cols[0])
        else:
            self.column_var.set("")

    def show_stats(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Nenhum arquivo carregado.")
            return
        try:
            stats = self.df.describe()
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Estatísticas Descritivas")
            text = tk.Text(stats_window)
            text.pack(expand=True, fill=tk.BOTH)
            text.insert("1.0", str(stats))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar estatísticas:\n{e}")

    def show_correlation(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Carregue um arquivo primeiro.")
            return

        corr = self.df.corr(numeric_only=True)
        if corr.empty:
            messagebox.showinfo("Info", "Sem colunas numéricas suficientes para correlação.")
            return

        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Mapa de Correlação")
        plt.tight_layout()
        plt.show()

    def plot_graph(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Nenhum arquivo carregado.")
            return

        col = self.column_var.get()
        chart_type = self.chart_type_var.get()
        if col not in self.df.columns:
            messagebox.showwarning("Erro", "Coluna inválida ou não numérica.")
            return

        try:
            plt.figure(figsize=(8, 5))
            if chart_type == "Linha":
                self.df[col].plot(kind='line', title=f"Gráfico de Linha - {col}")
            elif chart_type == "Barras":
                self.df[col].head(20).plot(kind='bar', title=f"Gráfico de Barras - {col}")
            elif chart_type == "Histograma":
                self.df[col].plot(kind='hist', bins=20, title=f"Histograma - {col}")
            elif chart_type == "Dispersão":
                numeric_cols = self.df.select_dtypes(include='number').columns.tolist()
                if len(numeric_cols) >= 2:
                    plt.scatter(self.df[numeric_cols[0]], self.df[numeric_cols[1]])
                    plt.xlabel(numeric_cols[0])
                    plt.ylabel(numeric_cols[1])
                    plt.title(f"Dispersão: {numeric_cols[0]} vs {numeric_cols[1]}")
                else:
                    messagebox.showinfo("Info", "São necessárias ao menos 2 colunas numéricas.")
                    return

            plt.grid(True)
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Erro ao plotar", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedDataAnalyzer(root)
    root.mainloop()
