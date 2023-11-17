import tkinter as tk
from tkinter import filedialog
from http.cookiejar import MozillaCookieJar
from browser_cookie3 import chrome

class CookieManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Cookie Manager")

        self.cookie_jar = MozillaCookieJar()
        self.load_cookies()

        self.botao_mostrar = tk.Button(self.master, text="Mostrar Cookies", command=self.mostrar_cookies, font=("Arial", 10, "bold"), bg="#00FFFF")  
        self.botao_mostrar.pack(side=tk.TOP, pady=5)        

        self.botao_salvar = tk.Button(self.master, text="Salvar Cookies", command=self.salvar_cookies, font=("Arial", 10, "bold"), bg="#07f75f") 
        self.botao_salvar.pack(side=tk.TOP, pady=5)

        self.formato_salvamento = tk.StringVar(self.master)
        self.formato_salvamento.set(".txt")  # Defina o formato padrão como .txt

        self.opcoes_formato = [(".txt"), (".docx")]
        self.menu_formato = tk.OptionMenu(self.master, self.formato_salvamento, *self.opcoes_formato)
        self.menu_formato.pack(side=tk.TOP, pady=5)

        self.lista_cookies = tk.Listbox(self.master, selectmode=tk.SINGLE, height=50, width=180, font=("Arial", 10, "bold"))
        self.lista_cookies.pack(pady=10)

    def load_cookies(self):
        try:
            # Obtém os cookies do Chrome
            chrome_cookies = chrome(domain_name=".google.com", cookie_file=None)
            for cookie in chrome_cookies:
                self.cookie_jar.set_cookie(cookie)

        except Exception as e:
            print(f"Erro ao carregar cookies: {e}")

    def salvar_cookies(self):
        try:
            # Pede ao usuário para escolher o diretório de salvamento
            default_name = "arquivo_cookies" + self.formato_salvamento.get()
            file_path = filedialog.asksaveasfilename(defaultextension=self.formato_salvamento.get(), initialfile=default_name, filetypes=[(formato[1], f"*{formato[0]}") for formato in self.opcoes_formato])
            
            # Salva os cookies no arquivo escolhido
            if file_path:
                with open(file_path, 'w') as file:
                    for cookie in self.cookie_jar:
                        file.write(f"{cookie.domain}: {cookie.name}={cookie.value}\n")
                print(f"Cookies salvos em: {file_path}")
        except Exception as e:
            print(f"Erro ao salvar cookies: {e}")

    def mostrar_cookies(self):
        self.lista_cookies.delete(0, tk.END)
        for cookie in self.cookie_jar:
            self.lista_cookies.insert(tk.END, f"{cookie.domain}: {cookie.name}={cookie.value}")    

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = CookieManager(root)
    root.mainloop()
