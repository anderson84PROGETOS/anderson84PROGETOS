import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from fpdf import FPDF
import os

def gerar_pdf(nome_arquivo):
    # Conteúdo do documento
    text = results_text.get("1.0", tk.END).strip()
    
    if not text:
        messagebox.showerror("Erro", "Por favor, insira o conteúdo para o PDF.")
        return
    
    # Criar o PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style="", size=12)

    # Título
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, "Comandos Mais Usados no Kali Linux", ln=True, align="C")
    pdf.ln(10)

    # Substituir caracteres problemáticos
    text = text.replace("–", "-")

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    # Salvar o PDF
    pdf.output(nome_arquivo)
    messagebox.showinfo("Sucesso", f"PDF gerado com sucesso: {nome_arquivo}")

def salvar_pdf():
    # Caixa de diálogo para escolher o local e nome do arquivo
    nome_arquivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
    
    if nome_arquivo:
        gerar_pdf(nome_arquivo)

# Criando a janela principal
window = tk.Tk()
window.title("Gerador PDF")
window.geometry("1200x950")

# Botão para salvar o PDF
tk.Button(window, text="Salvar PDF", command=salvar_pdf, font=("Arial", 11, "bold"), background='#05f244').pack(pady=20)

tk.Label(window, text="Texto para gerar no PDF", font=("Arial", 11, "bold")).pack()
results_text = scrolledtext.ScrolledText(window, width=120, height=42, font=("Arial", 11, "bold"))
results_text.pack(pady=5)

window.mainloop()
