import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
from datetime import datetime


class VisualizadorHistoricoChrome:

    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Histórico do Chrome")

        self.dados_historico = []

        data_atual = datetime.now().strftime("%d/%m/%Y")

        frame_principal = ttk.Frame(root)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        titulo = ttk.Label(
            frame_principal,
            text="Visualizador de Histórico do Chrome",
            font=("Arial", 16, "bold")
        )
        titulo.pack(anchor="w")

        self.caminho_padrao = os.path.expanduser(
            "~/AppData/Local/Google/Chrome/User Data/Default/History"
        )

        self.label_caminho = ttk.Label(
            frame_principal,
            text=self.caminho_padrao,
            foreground="gray"
        )
        self.label_caminho.pack(anchor="w", pady=(0, 5))

        self.label_data = ttk.Label(
            frame_principal,
            text=f"Data atual: {data_atual}"
        )
        self.label_data.pack(anchor="w", pady=(0, 10))

        frame_botoes = ttk.Frame(frame_principal)
        frame_botoes.pack(fill=tk.X, pady=5)

        ttk.Button(
            frame_botoes,
            text="Selecionar arquivo History",
            command=self.selecionar_arquivo
        ).pack(side=tk.LEFT)

        ttk.Button(
            frame_botoes,
            text="Salvar histórico em TXT",
            command=self.salvar_txt
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            frame_botoes,
            text="Apagar URL selecionadas",
            command=self.apagar_urls
        ).pack(side=tk.LEFT, padx=5)

        # BUSCA
        frame_busca = ttk.Frame(frame_principal)
        frame_busca.pack(fill=tk.X, pady=10)

        ttk.Label(frame_busca, text="Buscar URL ou palavra:").pack(side=tk.LEFT)

        self.campo_busca = ttk.Entry(frame_busca, width=40)
        self.campo_busca.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            frame_busca,
            text="Buscar",
            command=self.buscar
        ).pack(side=tk.LEFT)

        ttk.Button(
            frame_busca,
            text="Limpar busca",
            command=self.mostrar_tudo
        ).pack(side=tk.LEFT, padx=5)

        colunas = ("url", "titulo", "visitas", "ultima_visita")

        self.tabela = ttk.Treeview(
            frame_principal,
            columns=colunas,
            show="headings",
            selectmode="extended"
        )

        self.tabela.heading("url", text="URL")
        self.tabela.heading("titulo", text="Título")
        self.tabela.heading("visitas", text="Visitas")
        self.tabela.heading("ultima_visita", text="Última visita")

        self.tabela.column("url", width=400)
        self.tabela.column("titulo", width=250)
        self.tabela.column("visitas", width=80)
        self.tabela.column("ultima_visita", width=180)

        barra = ttk.Scrollbar(
            frame_principal,
            orient=tk.VERTICAL,
            command=self.tabela.yview
        )

        self.tabela.configure(yscrollcommand=barra.set)

        self.tabela.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.pack(side=tk.RIGHT, fill=tk.Y)

        self.arquivo_atual = None

    def selecionar_arquivo(self):

        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo History do Chrome",
            filetypes=[("Todos arquivos", "*.*")]
        )

        if caminho:
            self.arquivo_atual = caminho
            self.label_caminho.config(text=caminho)
            self.carregar_historico()

    def carregar_historico(self):

        try:
            conexao = sqlite3.connect(self.arquivo_atual)
            cursor = conexao.cursor()

            cursor.execute("""
            SELECT url, title, visit_count,
            datetime(last_visit_time/1000000-11644473600,'unixepoch')
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT 2000
            """)

            self.dados_historico = cursor.fetchall()

            self.mostrar_tudo()

            conexao.close()

        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao carregar histórico\n{erro}")

    def mostrar_tudo(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for linha in self.dados_historico:
            self.tabela.insert("", tk.END, values=linha)

    def buscar(self):

        termo = self.campo_busca.get().lower()

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for linha in self.dados_historico:

            if termo in linha[0].lower() or termo in (linha[1] or "").lower():
                self.tabela.insert("", tk.END, values=linha)

    def apagar_urls(self):

        selecionados = self.tabela.selection()

        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione uma ou mais URLs.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            f"Deseja apagar {len(selecionados)} URL do histórico?"
        )

        if not confirmar:
            return

        try:

            conexao = sqlite3.connect(self.arquivo_atual)
            cursor = conexao.cursor()

            for item in selecionados:

                valores = self.tabela.item(item, "values")
                url = valores[0]

                cursor.execute(
                    "DELETE FROM urls WHERE url = ?",
                    (url,)
                )

            conexao.commit()
            conexao.close()

            self.carregar_historico()

            messagebox.showinfo(
                "Sucesso",
                "URL removidas do histórico."
            )

        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao apagar URL\n{erro}")

    def salvar_txt(self):

        if not self.dados_historico:
            messagebox.showwarning("Aviso", "Nenhum histórico carregado.")
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo TXT", "*.txt")],
            title="Salvar histórico"
        )

        if not caminho:
            return

        try:

            with open(caminho, "w", encoding="utf-8") as arquivo:

                arquivo.write("HISTÓRICO DO GOOGLE CHROME\n")
                arquivo.write(
                    "Data de exportação: "
                    + datetime.now().strftime("%d/%m/%Y")
                    + "\n\n"
                )

                for url, titulo, visitas, data in self.dados_historico:

                    arquivo.write(f"URL: {url}\n")
                    arquivo.write(f"Título: {titulo}\n")
                    arquivo.write(f"Visitas: {visitas}\n")
                    arquivo.write(f"Última visita: {data}\n")
                    arquivo.write("-" * 60 + "\n")

            messagebox.showinfo("Sucesso", "Histórico salvo com sucesso!")

        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo\n{erro}")


if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    app = VisualizadorHistoricoChrome(root)
    root.mainloop()
