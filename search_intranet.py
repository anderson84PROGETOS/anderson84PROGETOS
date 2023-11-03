import tkinter as tk
from tkinter import messagebox, filedialog
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

# Função para encontrar URLs de intranet
def find_intranet_urls():
    result_text.delete(1.0, tk.END)  # Limpar o texto anterior
    url = entry.get()
    if not url:
        messagebox.showerror("Erro", "Digite a URL do site.")
        return

    try:
        response = requests.get(url)
        if response.status_code != 200:
            messagebox.showerror("Erro", f"Não foi possível acessar a URL: {url}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        intranet_urls = set()
        for link in soup.find_all('a', href=True):
            link_url = link.get('href')
            if link_url.startswith('/') or urlparse(link_url).netloc == parsed_url.netloc:
                intranet_urls.add(base_url + link_url)

        if intranet_urls:
            for intranet_url in intranet_urls:
                result_text.insert(tk.END, intranet_url + "\n")
            
            # Atualizar a label com o número de URLs de intranet encontradas
            num_linhas = len(intranet_urls)
            label_num_linhas.config(text="Número de intranet encontrados: " + str(num_linhas))
        else:
            messagebox.showinfo("Nenhuma URL da Intranet Encontrada", "Nenhuma URL da Intranet encontrada neste site.")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar a URL: {str(e)}")

# Função para salvar o resultado em um arquivo
def save_to_file():
    text = result_text.get(1.0, tk.END)
    if not text.strip():
        messagebox.showinfo("Nenhum resultado para salvar", "Nenhum resultado encontrado para salvar.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text)
            messagebox.showinfo("Salvo com sucesso", "Os resultados foram salvos com sucesso no arquivo.")

# Função para limpar a área de resultados e redefinir o rótulo
def clear_results():
    result_text.delete(1.0, tk.END)
    label_num_linhas.config(text="Número de intranet encontrados: 0")

# Configuração da janela
window = tk.Tk()
window.title("Encontrar URL Intranet")
window.wm_state('zoomed')

# Rótulo e campo de entrada
label = tk.Label(window, text="Digite a URL do Site", fg='black', font=('TkDefaultFont', 11, 'bold'))
label.pack(pady=10)
entry = tk.Entry(window, width=60, fg='black', font=('TkDefaultFont', 11, 'bold'))
entry.pack()

# Botão para iniciar a pesquisa
find_button = tk.Button(window, text="Encontrar URL Intranet", command=find_intranet_urls, bg='#00FFFF', fg='black', font=('TkDefaultFont', 11, 'bold'))
find_button.pack(pady=10)

# Botão para salvar em arquivo
save_button = tk.Button(window, text="Salvar Arquivo", command=save_to_file, bg='#FFA500', fg='black', font=('TkDefaultFont', 10, 'bold'))
save_button.pack(pady=10)

# Botão para limpar a área de resultados
clear_button = tk.Button(window, text="Clear All", command=clear_results, bg='#FF0000', fg='black', font=('TkDefaultFont', 10, 'bold'))
clear_button.pack(pady=10)

# Área de resultados
result_text = tk.Text(window, height=38, width=155, fg='black', font=('TkDefaultFont', 11, 'bold'))
result_text.pack()

# Barra de rolagem vertical
scrollbar = tk.Scrollbar(window, command=result_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
result_text.config(yscrollcommand=scrollbar.set)

# Criação da label para o número de URLs de intranet encontradas
label_num_linhas = tk.Label(window, text="Número de intranet encontrados: 0", fg='black', font=('TkDefaultFont', 11, 'bold'))
label_num_linhas.pack(pady=10)

# Executar a interface gráfica
window.mainloop()
