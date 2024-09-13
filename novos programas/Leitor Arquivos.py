import pdfplumber
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

# Função para abrir e exibir o conteúdo do arquivo PDF
def abrir_tudo_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_paginas = len(pdf.pages)
            result_text.insert(tk.END, f'Total de páginas: {total_paginas}\n\n')

            # Percorre todas as páginas do PDF e imprime o texto
            for i, pagina in enumerate(pdf.pages):
                texto = pagina.extract_text()
                result_text.insert(tk.END, f'--- Página {i + 1} ---\n\n')
                result_text.insert(tk.END, texto if texto else "Conteúdo não extraído")
                result_text.insert(tk.END, '\n=============================================================\n')
    except Exception as e:
        result_text.insert(tk.END, f'\nErro ao abrir o PDF: {e}')

# Função para abrir e exibir o conteúdo de arquivos de texto
def abrir_tudo_txt(txt_file):
    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            texto = file.read()
            result_text.insert(tk.END, f'--- Conteúdo do arquivo de texto ---\n\n')
            result_text.insert(tk.END, texto)
            result_text.insert(tk.END, '\n=============================================================\n')
    except Exception as e:
        result_text.insert(tk.END, f'\nErro ao abrir o arquivo de texto: {e}')

# Função para buscar e abrir o arquivo, verificando o tipo de arquivo
def buscar_arquivo():
    arquivo = filedialog.askopenfilename(
        initialdir="/", 
        title="Selecione o arquivo",
        filetypes=(("Arquivos PDF", "*.pdf"), ("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )
    if arquivo:
        # Verifica a extensão do arquivo
        if arquivo.endswith(".pdf"):
            abrir_tudo_pdf(arquivo)
        elif arquivo.endswith(".txt"):
            abrir_tudo_txt(arquivo)
        else:
            result_text.insert(tk.END, f"Tipo de arquivo não suportado: {arquivo.split('.')[-1]}")

# Criação da interface gráfica com Tkinter
root = tk.Tk()
root.title("Leitor de Arquivos")
root.geometry("1000x900")

# Botão para buscar o arquivo
buscar_arquivo_btn = tk.Button(root, text="Buscar Arquivo", padx=10, pady=5, fg="black", bg="#09e845", command=buscar_arquivo)
buscar_arquivo_btn.pack(pady=10)

# Caixa de texto com barra de rolagem para exibir o conteúdo do arquivo
result_text = ScrolledText(root, wrap=tk.WORD, width=140, height=45, font=("TkDefaultFont", 11, "bold"))
result_text.pack()

# Iniciar a interface
root.mainloop()
