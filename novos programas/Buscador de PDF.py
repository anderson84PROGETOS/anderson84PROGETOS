import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import tkinter as tk
from tkinter import messagebox

# Função para baixar PDFs de uma URL
def baixar_pdfs(url):

    # Adiciona um cabeçalho User-Agent para evitar erros 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        pdf_links = [link['href'] for link in links if link['href'].endswith('.pdf')]
        
        total_pdfs = len(pdf_links)
        messagebox.showinfo("PDFs encontrados", f'Total de PDF encontrados: {total_pdfs}')
        
        if total_pdfs == 0:
            messagebox.showinfo("Nenhum PDF", "Nenhum PDF encontrado.")
            return
        
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
        
        # Variável contador para numerar os PDFs baixados
        contador = 1
        for pdf_link in pdf_links:
            # Corrige URLs relativas
            pdf_url = urllib.parse.urljoin(url, pdf_link)
            file_name = os.path.join('pdfs', pdf_link.split('/')[-1])
            try:
                print(f'{contador} Baixando: {pdf_url}')
                pdf_response = requests.get(pdf_url)
                with open(file_name, 'wb') as pdf_file:
                    pdf_file.write(pdf_response.content)
                
                contador += 1  # Incrementa o número a cada download
                
            except Exception as e:
                print(f'Erro ao baixar {pdf_url}: {e}')
    else:
        messagebox.showerror("Erro", f'Erro ao acessar a URL: {response.status_code}')

# Função para executar a pesquisa e baixar PDFs
def buscar_pdfs():
    website = entry.get()
    page = page_entry.get()
    if not website:
        messagebox.showerror("Erro", "Por favor, insira um website.")
        return
    
    query = f"site:{website} filetype:pdf"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={(int(page)-1)*10}"
    
    baixar_pdfs(search_url)

# Interface gráfica usando Tkinter
root = tk.Tk()
root.title("Buscador de PDF")

# Campo de entrada para o nome do website
label = tk.Label(root, text="Digite o nome do website:")
label.pack(pady=10)
entry = tk.Entry(root, width=40)
entry.pack(pady=10)

# Campo de entrada para a página
page_label = tk.Label(root, text="Digite a página (1-10):")
page_label.pack(pady=10)
page_entry = tk.Entry(root, width=10)
page_entry.pack(pady=10)

# Botão para buscar PDFs
button = tk.Button(root, text="Buscar PDFs", command=buscar_pdfs)
button.pack(pady=20)

root.mainloop()
