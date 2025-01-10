import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import tkinter as tk
from tkinter import messagebox, scrolledtext
import time  # Importando o módulo time
import random  # Importando para criar atrasos aleatórios

# Função para buscar PDFs de uma URL sem baixar
def buscar_pdfs_na_pagina(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',  # Definir um referer para a requisição
        'Origin': 'https://www.google.com',  # Definir a origem
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            pdf_links = [link['href'] for link in links if link['href'].endswith('.pdf')]
            return pdf_links
        else:
            messagebox.showerror("Erro", f'Erro ao acessar a URL: {response.status_code}')
            return []
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro", f'Erro ao acessar a URL: {str(e)}')
        return []

# Função para baixar PDF com atraso
def baixar_pdfs(links, url):
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')

    contador = 1
    for pdf_link in links:
        pdf_url = urllib.parse.urljoin(url, pdf_link)
        file_name = os.path.join('pdfs', pdf_link.split('/')[-1])
        try:
            text_resultado.insert(tk.END, f'{contador} Baixando: {pdf_url}\n')
            pdf_response = requests.get(pdf_url)
            with open(file_name, 'wb') as pdf_file:
                pdf_file.write(pdf_response.content)
            text_resultado.insert(tk.END, f'{contador} Download completo: {file_name}\n')
            contador += 1
            time.sleep(random.randint(5, 10))  # Aguardar de 5 a 10 segundos entre downloads para evitar bloqueios
        except Exception as e:
            text_resultado.insert(tk.END, f'Erro ao baixar {pdf_url}: {e}\n')

# Função para executar a pesquisa e baixar PDFs
def buscar_pdfs():
    website = entry.get()
    if not website:
        messagebox.showerror("Erro", "Por favor, insira um website.")
        return
    
    try:
        pagina = int(page_input.get())  # Pegando a página específica
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira um número válido de página.")
        return
    
    query = f"site:{website} filetype:pdf"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={(pagina-1)*10}"
    
    pdf_links = buscar_pdfs_na_pagina(search_url)
    
    if pdf_links:
        baixar_pdfs(pdf_links, search_url)
    else:
        text_resultado.insert(tk.END, f"Nenhum PDF encontrado na página {pagina}.\n")

# Função para contar quantos PDF existem na página (sem baixar)
def contar_pdfs():
    website = entry.get()
    if not website:
        messagebox.showerror("Erro", "Por favor, insira um website.")
        return

    try:
        pagina = int(page_input.get())  # Pegando a página específica
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira um número válido de página.")
        return
    
    query = f"site:{website} filetype:pdf"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={(pagina-1)*10}"

    pdf_links = buscar_pdfs_na_pagina(search_url)
    
    if pdf_links:
        total_pdfs = len(pdf_links)
        text_resultado.insert(tk.END, f'Total de PDF Encontrados na página: {pagina}     {total_pdfs}:PDF\n')
    else:
        text_resultado.insert(tk.END, f"\nNenhum PDF Encontrado na página: {pagina}.\n")

# Interface gráfica usando Tkinter
root = tk.Tk()
root.title("PDF Download")
root.geometry("1080x820")

label = tk.Label(root, text="Digite o nome do website", font=("TkDefaultFont", 11, "bold"))
label.pack(pady=2)
entry = tk.Entry(root, width=35, font=("TkDefaultFont", 10, "bold"))
entry.pack(pady=5)

page_label = tk.Label(root, text="Digite o número da página que deseja pesquisar", font=("TkDefaultFont", 10, "bold"))
page_label.pack(pady=10)

# Entrada para o número da página
page_input = tk.Entry(root, width=5, font=("TkDefaultFont", 10, "bold"))
page_input.pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

button = tk.Button(button_frame, text="Download PDF", command=buscar_pdfs, font=("TkDefaultFont", 10, "bold"), bg='#0cf27b')
button.grid(row=0, column=1, padx=10)

contar_button = tk.Button(button_frame, text="Contar PDF", command=contar_pdfs, font=("TkDefaultFont", 10, "bold"), bg='#f0ad4e')
contar_button.grid(row=0, column=2, padx=10)

# Campo de exibição dos resultados
text_resultado = scrolledtext.ScrolledText(root, width=120, height=34, wrap=tk.WORD, font=("TkDefaultFont", 11, "bold"))
text_resultado.pack(pady=10)

root.mainloop()
