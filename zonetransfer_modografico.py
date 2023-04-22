import tkinter as tk
import subprocess

class ZoneTransferGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.lbl_title = tk.Label(self, text="Consulta de zona DNS")
        self.lbl_title.pack()

        self.lbl_website = tk.Label(self, text="Digite o nome do site:")
        self.lbl_website.pack()

        self.entry_website = tk.Entry(self, width=50)
        self.entry_website.pack()

        self.lbl_dns = tk.Label(self, text="Selecione o servidor DNS:")
        self.lbl_dns.pack()
        self.var_dns = tk.StringVar()
        self.var_dns.set("8.8.8.8")  # valor default
        self.option_dns = tk.OptionMenu(self, self.var_dns, "8.8.8.8", "1.1.1.1", "208.67.222.222")
        self.option_dns.pack()

        self.lbl_output = tk.Label(self, text="Resultado da consulta:")
        self.lbl_output.pack()

        self.txt_output = tk.Text(self, height=45, width=150)
        self.txt_output.pack()

        self.btn_consultar_ns = tk.Button(self, text="Consultar NS", command=self.consultar_ns)
        self.btn_consultar_ns.pack(side="left")

        self.btn_consultar_transferencia = tk.Button(self, text="Consultar transferência de zona", command=self.consultar_transferencia)
        self.btn_consultar_transferencia.pack(side="left")

        self.btn_limpar = tk.Button(self, text="Limpar", command=self.limpar_campos)
        self.btn_limpar.pack(side="left")

    def consultar_ns(self):
        website = self.entry_website.get()
        dns_selecionado = self.var_dns.get()
        saida_ns = subprocess.check_output(["nslookup", "-type=ns", website, dns_selecionado]).decode()
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, saida_ns)

    def consultar_transferencia(self):
        website = self.entry_website.get()
        dns_selecionado = self.var_dns.get()
        saida_transferencia = subprocess.check_output(["nslookup", "-type=any", "-vc", website, dns_selecionado]).decode()
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, saida_transferencia)

    def limpar_campos(self):
        self.entry_website.delete(0, tk.END)
        self.txt_output.delete("1.0", tk.END)


root = tk.Tk()
root.geometry("1000x1000")
app = ZoneTransferGUI(master=root)
app.mainloop()
