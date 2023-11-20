import tkinter as tk
from tkinter import scrolledtext, simpledialog
import shodan

class ShodanSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shodan Host Lookup")

        # Configurando a centralização
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Tenta carregar a chave API do arquivo
        self.api_key = self.load_api_key()

        if not self.api_key:
            # Se a chave não estiver disponível, solicita ao usuário que insira a chave
            self.api_key = simpledialog.askstring("API Shodan", "Digite sua chave de API Shodan:")
            if not self.api_key:
                self.root.destroy()
                return

            # Salva a chave API no arquivo
            self.save_api_key(self.api_key)

        # Entrada para o endereço IP
        self.ip_label = tk.Label(root, text="Digite o endereço IP")
        self.ip_label.grid(column=0, row=0, padx=10, pady=10, sticky="N")

        self.ip_entry = tk.Entry(root, width=30)
        self.ip_entry.grid(column=0, row=0, padx=20, pady=50, sticky="N")

        # Botão de pesquisa
        self.search_button = tk.Button(root, text="Pesquisar", command=self.search_shodan, bg="#0af7d8")
        self.search_button.grid(column=0, row=0, padx=10, pady=80, sticky="N")

        # Resultado
        self.result_frame = tk.Frame(root)
        self.result_frame.grid(column=0, row=0, columnspan=2)
        self.result_text = scrolledtext.ScrolledText(self.result_frame, wrap=tk.WORD, width=100, height=40, font=("Arial", 12))
        self.result_text.grid(column=0, row=0, sticky="N")

    def load_api_key(self):
        try:
            with open("api_key.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return None

    def save_api_key(self, api_key):
        with open("api_key.txt", "w") as file:
            file.write(api_key)

    def search_shodan(self):
        ip_address = self.ip_entry.get()

        if not ip_address:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Por favor, digite um endereço IP.")
            return

        try:
            shodan_api = shodan.Shodan(self.api_key)
            host_info = shodan_api.host(ip_address)

            # Exibindo informações do host na ScrolledText
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Hostnames: {', '.join(host_info.get('hostnames', ['N/A']))}\n\n")
            self.result_text.insert(tk.END, f"City: {host_info.get('city', 'N/A')}\n\n")
            self.result_text.insert(tk.END, f"Country: {host_info.get('country_name', 'N/A')}\n\n")
            self.result_text.insert(tk.END, f"Organization: {host_info.get('org', 'N/A')}\n\n")
            self.result_text.insert(tk.END, f"Updated: {host_info.get('last_update', 'N/A')}\n\n")
            self.result_text.insert(tk.END, f"Number of open ports: {len(host_info.get('ports', []))}\n")

            # Exibindo detalhes das portas
            self.result_text.insert(tk.END, "Ports:\n")
            for port in host_info.get('data', []):
                self.result_text.insert(tk.END, f"    {port['port']}/{port['transport']}\n")
                if 'ssl' in port:
                    self.result_text.insert(tk.END, f"        |-- Cert Issuer: {port['ssl']['cert']['issuer']}\n")
                    self.result_text.insert(tk.END, f"        |-- Cert Subject: {port['ssl']['cert']['subject']}\n")
                    self.result_text.insert(tk.END, f"        |-- SSL Versions: {', '.join(port['ssl']['versions'])}\n")

        except shodan.APIError as e:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Erro na API Shodan: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = ShodanSearchApp(root)
    root.mainloop()
