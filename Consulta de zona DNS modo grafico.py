import tkinter as tk
import subprocess
import requests

class ZoneTransferGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.lbl_title = tk.Label(self, text="Consulta de zona DNS")
        self.lbl_title.pack()

        self.lbl_website = tk.Label(self, text="Digite o nome do site:")
        self.lbl_website.pack()

        self.entry_website = tk.Entry(self, width=50)
        self.entry_website.pack()

        # Obtenha a lista de endereços IP de DNS públicos
        response = requests.get('https://public-dns.info/nameservers.txt')
        dns_list = response.text.splitlines()

        # Adicione mais endereços de DNS à lista        
        dns_list = [    
            "208.67.220.220",   # OpenDNS            
            "77.88.8.8",        # Yandex.DNS
            "114.114.114.114",  # 114DNS
            "80.80.80.80",      # Freenom World                   
            "8.8.8.8",          # dns.google
            "8.8.4.4",          # google
            "1.1.1.1",          # cloudflare
            "1.0.0.1",          # cloudflare
            "208.67.222.222",   # dns.opendns
            "9.9.9.9",          # dns9.quad9.net
            "185.228.168.168",  # family-filter-dns.cleanbrowsing.org

        ]    

        # Crie o menu suspenso com os endereços IP de DNS
        self.var_dns = tk.StringVar(self)
        self.var_dns.set(dns_list[0])
        self.option_dns = tk.OptionMenu(self, self.var_dns, *dns_list)
        self.option_dns.pack()

        self.lbl_output = tk.Label(self, text="Resultado da consulta:")
        self.lbl_output.pack()

        self.txt_output = tk.Text(self, height=45, width=158)
        self.txt_output.pack()

        self.btn_consultar_ns = tk.Button(self, text="Consultar NS", command=self.consultar_ns)
        self.btn_consultar_ns.pack(side="left")

        self.btn_consultar_transferencia = tk.Button(self, text="Consultar transferência de zona", command=self.consultar_transferencia)
        self.btn_consultar_transferencia.pack(side="left")

        self.btn_limpar = tk.Button(self, text="Limpar", command=self.limpar_campos)
        self.btn_limpar.pack(side="left")

    def consultar_ns(self):
        website = self.entry_website.get()
        dns = self.var_dns.get()
        cmd = f"nslookup -type=NS {website} {dns}"
        output = subprocess.check_output(cmd, shell=True, encoding='utf-8')
        self.txt_output.delete('1.0', tk.END)
        self.txt_output.insert(tk.END, output)

    def consultar_transferencia(self):
        website = self.entry_website.get()
        dns = self.var_dns.get()
        cmd = f"dig axfr {website} @{dns}"
        output = subprocess.check_output(cmd, shell=True, encoding='utf-8')
        self.txt_output.delete('1.0', tk.END)
        self.txt_output.insert(tk.END, output)

    def limpar_campos(self):
        self.entry_website.delete(0, tk.END)
        self.txt_output.delete('1.0', tk.END)
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
    
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1300x1000")
    root.wm_state('zoomed')
    app = ZoneTransferGUI(master=root)
    app.mainloop()
