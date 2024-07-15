import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
import re

def extrair_dados():
    url = url_entry.get()

    # Definindo os cabeçalhos HTTP para a solicitação
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Fazendo a solicitação HTTP para obter o conteúdo da página
    try:
        response = requests.get(url, headers=headers)

        # Verificando se a solicitação foi bem-sucedida
        if response.status_code == 200:
            # Parsing do conteúdo HTML com BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraindo todos os links (tags <a>)
            links = soup.find_all('a')
            
            # Usando um conjunto para armazenar URLs únicas
            urls_unicas = set()
            for link in links:
                href = link.get('href')
                if href and href.startswith('http'):
                    urls_unicas.add(href)

            # Buscando URLs dentro de atributos 'content=' usando expressão regular
            content_urls = re.findall(r'content=["\'](https?://\S+?)(?=["\'])', str(soup))

            # Adicionando URLs encontradas em 'content=' ao conjunto de URLs únicas
            for url in content_urls:
                urls_unicas.add(url)

            # Atualizando o texto na área de texto
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Foram Encontradas: {len(urls_unicas)}  URL\n\n\n")
            for url in urls_unicas:
                result_text.insert(tk.END, url + "\n\n")
        else:
            messagebox.showerror("Erro", f"Falha ao acessar a página. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro de Conexão", f"Erro ao conectar-se à URL: {str(e)}")

# Criando a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Extrair URL Website")

# Criando widgets
url_label = tk.Label(root, text="Digite a URL do WebSite", font=("TkDefaultFont", 12, "bold"))
url_entry = tk.Entry(root, width=40, font=("TkDefaultFont", 11, "bold"))
extract_button = tk.Button(root, text="Extrair URL", command=extrair_dados, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
result_text = scrolledtext.ScrolledText(root, width=120, height=40, font=("TkDefaultFont", 12, "bold"))

# Posicionando widgets na janela
url_label.pack(pady=5)
url_entry.pack(pady=5)
extract_button.pack(pady=10)
result_text.pack(padx=10, pady=10)

# Rodando a aplicação
root.mainloop()
