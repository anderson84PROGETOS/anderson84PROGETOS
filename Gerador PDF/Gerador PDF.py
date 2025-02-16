import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from fpdf import FPDF
import re

def remover_caracteres_invalidos(texto):
    """Remove caracteres não suportados pela codificação Latin-1 do fpdf."""
    return re.sub(r'[^\x00-\xFF]', '', texto)

def gerar_pdf(nome_arquivo):
    # Obtendo o título do campo de entrada
    titulo = titulo_entry.get().strip()
    if not titulo:
        titulo = "Documento Gerado"

    # Obtendo o conteúdo
    text = results_text.get("1.0", tk.END).strip()
    
    if not text:
        messagebox.showerror("Erro", "Por favor, insira o conteúdo para o PDF.")
        return
    
    # Criar o PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Definir fonte e título
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, titulo, ln=True, align="C")
    pdf.ln(10)

    # Substituir caracteres problemáticos
    text = remover_caracteres_invalidos(text)
    
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    # Salvar o PDF
    pdf.output(nome_arquivo)
    messagebox.showinfo("Sucesso", f"PDF gerado com sucesso: {nome_arquivo}")

def salvar_pdf():
    nome_arquivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
    if nome_arquivo:
        gerar_pdf(nome_arquivo)

# Criando a janela principal
window = tk.Tk()
window.title("Gerador PDF")
window.geometry("1200x950")

# Entrada para o título do PDF
tk.Label(window, text="Título do PDF", font=("Arial", 11, "bold")).pack(pady=5)
titulo_entry = tk.Entry(window, font=("Arial", 11, "bold"), width=50)
titulo_entry.pack(pady=5)

# Botão para salvar o PDF
tk.Button(window, text="Salvar PDF", command=salvar_pdf, font=("Arial", 11, "bold"), background='#05f244').pack(pady=20)

# Campo de texto para o conteúdo do PDF
tk.Label(window, text="Texto para gerar no PDF", font=("Arial", 11, "bold")).pack()
results_text = scrolledtext.ScrolledText(window, width=120, height=40, font=("Arial", 11, "bold"))
results_text.pack(pady=5)

window.mainloop()
