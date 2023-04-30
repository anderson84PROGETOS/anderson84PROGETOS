import tkinter as tk
import webbrowser
import requests
import mmh3
import codecs
import pyperclip

class ZoneTransferGUI(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        
        # entrada de URL do favicon
        self.url_label = tk.Label(master, text="Digite a URL completa do favicon:")
        self.url_label.pack()

        self.entry = tk.Entry(master, width=150)
        self.entry.pack(padx=5, pady=5)

        # botão para obter o hash do favicon
        self.button = tk.Button(master, text="Obter Hash", command=self.get_hash)
        self.button.pack(padx=5, pady=5)

        # resultado da operação
        self.result_label = tk.Label(master, text="")
        self.result_label.pack(padx=5, pady=5)

        # hash http.favicon
        self.http_favicon_hash = tk.Label(master, text="")
        self.http_favicon_hash.pack(padx=5, pady=5)

        # link para a pesquisa no Shodan
        self.shodan_label = tk.Label(master, text="")
        self.shodan_label.pack(padx=5, pady=5)      
        
        # botão de sair
        self.quit_button = tk.Button(master, text="SAIR", command=self.master.destroy, fg="white", bg="#1E90FF")
        self.quit_button.pack(side=tk.BOTTOM, padx=5, pady=50)

    def get_hash(self):
        favicon_url = self.entry.get()
        response = requests.get(favicon_url)
        if response.status_code == 200:
            favicon = codecs.encode(response.content, "base64")
            favicon_hash = mmh3.hash(favicon)
            self.result_label.configure(text=f"O hash do favicon de {favicon_url} é: {favicon_hash}")
            self.http_favicon_hash.configure(text=f"[🔑] http.favicon.hash:{favicon_hash}")

            shodan_link = tk.Label(self.master, text=f"Clique aqui para ver os resultados no Shodan", fg="blue", cursor="hand2")
            shodan_link.pack(padx=5, pady=20)
            shodan_link.bind("<Button-1>", lambda e: self.open_shodan(favicon_hash))
            self.shodan_label.configure(text=f"Resultados no Shodan: https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}")

        # botão para copiar resultados
            self.copy_button = tk.Button(self.master, text="Copiar Resultados", command=self.copy_results)
            self.copy_button.pack(padx=5, pady=100)

        else:
            self.result_label.configure(text=f"Não foi possível obter o favicon de {favicon_url}")
            self.http_favicon_hash.configure(text="")
            self.shodan_label.configure(text="")

    def open_shodan(self, favicon_hash):
        shodan_url = f"https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}"
        webbrowser.open(shodan_url)
        self.shodan_label.configure(text=f"Você foi redirecionado para a pesquisa do Shodan")

    def copy_results(self):
        results = self.result_label.cget("text") + "\n" + self.http_favicon_hash.cget("text") + "\n" + self.shodan_label.cget("text")
        pyperclip.copy(results)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1300x1000")
    root.wm_state('zoomed')
    app = ZoneTransferGUI(master=root)
    app.mainloop()




