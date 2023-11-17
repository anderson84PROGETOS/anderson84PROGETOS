import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from bs4 import BeautifulSoup
import requests
import re

def encontrar_codigos_analytics_adsense(url):
    try:
        # Faz o request da página
        response = requests.get(url)
        response.raise_for_status()

        # Parseia o HTML da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # Procura por padrões específicos do Google Analytics
        padrao_analytics_1 = re.compile(r'_gaq\.push\(\[\'_setAccount\', \'(UA-[0-9]+-[0-9]+)\'\]\);')
        padrao_analytics_2 = re.compile(r'ga\("create", "(UA-[0-9]+-[0-9]+)", "auto"\);')
        padrao_analytics_3 = re.compile(r'gtag\("config", "(UA-[0-9]+-[0-9]+)"\);')      
        padrao_analytics_4 = re.compile(r'_gac\.push\(\[\'_setAccount\', \'(UA-[0-9]+-[0-9]+)\'\]\);')
        padrao_analytics_5 = re.compile(r'ga\("create", "(UA-[0-9]+-[0-9]+)", "user"\);')
        padrao_analytics_6 = re.compile(r'gtag\("set", "account", "(UA-[0-9]+-[0-9]+)"\);')
        padrao_analytics_7 = re.compile(r'_gat\.push\(\[\'_setAccount\', \'(UA-[0-9]+-[0-9]+)\'\]\);')

        # Padrões específicos do Google AdSense
        padrao_adsense_1 = re.compile(r'ca\-pub\-[0-9]+')
        padrao_adsense_2 = re.compile(r'pub\-([0-9]+)')

        # Adicione todos os padrões à lista
        padroes = [
            padrao_analytics_1, padrao_analytics_2, padrao_analytics_3,
            padrao_analytics_4, padrao_analytics_5, padrao_analytics_6,
            padrao_analytics_7, padrao_adsense_1, padrao_adsense_2
        ]

        codigos_unicos = set()

        # Procura por cada padrão
        for padrao in padroes:
            matches = soup.find_all(string=padrao)
            codigos_unicos.update(matches)

        if codigos_unicos:
            return [match.string for match in codigos_unicos]
        else:
            return None

    except Exception as e:
        return str(e)

def buscar_codigos():
    url = entry_url.get()
    codigos = encontrar_codigos_analytics_adsense(url)

    if codigos:
        mensagem = "\n\n".join(codigos)
        result_text.delete(1.0, tk.END)  # Limpa o conteúdo atual
        result_text.insert(tk.END, mensagem)
        # Limpar mensagem de aviso anterior, se houver
        aviso_var.set("")
    else:
        aviso_var.set("Nenhum código do Google Analytics ou Google AdSense encontrado na página.")

# Interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("Encontrar Códigos do Google Analytics e AdSense")

# Elementos da interface
label_url = tk.Label(root, text="URL do Site:")
label_url.pack()

entry_url = tk.Entry(root, width=40)
entry_url.pack(pady=10)

btn_buscar = tk.Button(root, text="Buscar Códigos", command=buscar_codigos, font=("Arial", 12), bg="#00FFFF") 
btn_buscar.pack()

# Variável para armazenar a mensagem de aviso
aviso_var = tk.StringVar()

# Label para exibir a mensagem de aviso
label_aviso = tk.Label(root, textvariable=aviso_var, fg="red", font=("Arial", 12))
label_aviso.pack(pady=5)

# Janela de rolagem para exibir resultados
result_frame = ttk.Frame(root, padding="10")
result_frame.pack(fill=tk.BOTH, expand=True)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=138, height=47, font=("Arial", 12))
result_text.pack(fill=tk.BOTH, expand=True)

# Inicia o loop da interface gráfica
root.mainloop()
