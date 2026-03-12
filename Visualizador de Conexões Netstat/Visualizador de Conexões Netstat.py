import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil


class NetstatGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Conexões (Netstat)        Comando 1   netstat -ano          Comando 2    tasklist | findstr 852                    Numero do PID 852")
        
        self.root.state("zoomed")
        self.root.geometry("950x550")       

        # Frame da tabela
        tabela_frame = tk.Frame(root)
        tabela_frame.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(tabela_frame)
        scrollbar.pack(side="right", fill="y")

        # Tabela
        self.tree = ttk.Treeview(
            tabela_frame,
            columns=("name", "port", "address", "pid", "path"),
            show="headings",
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=self.tree.yview)

        self.tree.heading("name", text="Processo")
        self.tree.heading("port", text="Porta")
        self.tree.heading("address", text="Endereço")
        self.tree.heading("pid", text="PID")
        self.tree.heading("path", text="Caminho")

        self.tree.column("name", width=200)
        self.tree.column("port", width=80)
        self.tree.column("address", width=200)
        self.tree.column("pid", width=80)
        self.tree.column("path", width=450)

        self.tree.pack(fill="both", expand=True)

        # Evento clique
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_caminho)

        # Frame inferior
        frame = tk.Frame(root)
        frame.pack(fill="x", pady=10)

        self.caminho_label = tk.Label(frame, text="Caminho do arquivo:", anchor="w")
        self.caminho_label.pack(fill="x")

        # Botões
        botoes = tk.Frame(root)
        botoes.pack(pady=5)

        self.botao_copiar = tk.Button(
            botoes,
            text="Copiar local do arquivo",
            bg="#03e8fc",
            fg="black",
            command=self.copiar_caminho
        )
        self.botao_copiar.grid(row=0, column=0, padx=5)

        self.botao_salvar = tk.Button(
            botoes,
            text="Salvar em TXT",
            bg="#fc9d03",
            fg="black",
            command=self.salvar_txt
        )
        self.botao_salvar.grid(row=0, column=1, padx=5)

        self.botao_atualizar = tk.Button(
            botoes,
            text="Atualizar",
            bg="#03fc0b",
            fg="black",
            command=self.atualizar
        )
        self.botao_atualizar.grid(row=0, column=2, padx=5)

        self.caminho_processo = ""

        self.carregar_conexoes()

    def carregar_conexoes(self):

        for conn in psutil.net_connections(kind='inet'):

            try:
                processo = psutil.Process(conn.pid)
                nome = processo.name()
                pid = conn.pid
                caminho = processo.exe()
            except:
                nome = "N/A"
                pid = "N/A"
                caminho = "N/A"

            port = conn.laddr.port if conn.laddr else "N/A"
            address = conn.laddr.ip if conn.laddr else "N/A"

            self.tree.insert("", "end", values=(nome, port, address, pid, caminho))

    def atualizar(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.carregar_conexoes()

    def mostrar_caminho(self, event):

        item = self.tree.selection()

        if not item:
            return

        dados = self.tree.item(item)["values"]

        self.caminho_processo = dados[4]

        self.caminho_label.config(text=f"Caminho do arquivo: {self.caminho_processo}")

    def copiar_caminho(self):

        if self.caminho_processo == "":
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(self.caminho_processo)

        messagebox.showinfo("Copiado", "Caminho copiado!")

    def salvar_txt(self):

        caminho = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )

        if not caminho:
            return

        try:

            with open(caminho, "w", encoding="utf-8") as f:

                f.write("Processo | Porta | Endereço | PID | Caminho\n")
                f.write("-"*100 + "\n")

                for item in self.tree.get_children():

                    dados = self.tree.item(item)["values"]

                    linha = f"{dados[0]} | {dados[1]} | {dados[2]} | {dados[3]} | {dados[4]}\n\n"

                    f.write(linha)

            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")

        except Exception as e:

            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":

    root = tk.Tk()    
    app = NetstatGUI(root)
    root.mainloop()
