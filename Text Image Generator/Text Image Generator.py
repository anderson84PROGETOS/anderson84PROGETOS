import tkinter as tk
from tkinter import filedialog, colorchooser, scrolledtext, messagebox
from PIL import Image, ImageDraw, ImageFont

def escolher_cor_fundo():
    cor = colorchooser.askcolor()[1]
    if cor:
        entry_cor_fundo.delete(0, tk.END)
        entry_cor_fundo.insert(0, cor)

def escolher_cor_texto():
    cor = colorchooser.askcolor()[1]
    if cor:
        entry_cor_texto.delete(0, tk.END)
        entry_cor_texto.insert(0, cor)

def salvar_imagem():
    texto = results_text.get("1.0", tk.END).strip()
    cor_fundo = entry_cor_fundo.get()
    cor_texto = entry_cor_texto.get()
    
    # Caixa de diálogo para escolher onde salvar o arquivo
    nome_arquivo = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("Arquivos PNG", "*.png"), ("Todos os arquivos", "*.*")])
    
    if not nome_arquivo:
        return  # Se o usuário cancelar, não faz nada
    
    largura = 1000
    altura = 1500  # Altura ajustável
    img = Image.new("RGB", (largura, altura), cor_fundo)
    draw = ImageDraw.Draw(img)
    
    try:
        fonte = ImageFont.truetype("arial.ttf", 24)
    except:
        fonte = ImageFont.load_default()
    
    x, y = 20, 20
    for linha in texto.split("\n"):
        draw.text((x, y), linha, font=fonte, fill=cor_texto)
        y += 30
    
    img = img.crop((0, 0, largura, y + 20))
    img.save(nome_arquivo)
    messagebox.showinfo("Sucesso", f"Imagem salva como {nome_arquivo}")

# Criando a janela principal
window = tk.Tk()
window.title("Text Image Generator")
window.geometry("1200x950")

# Botão para salvar a imagem
tk.Button(window, text="Salvar Imagem", command=salvar_imagem, font=("Arial", 11, "bold"), background='#f2a305').pack(pady=20)

tk.Label(window, text="Cor de fundo", font=("Arial", 11, "bold")).pack()
entry_cor_fundo = tk.Entry(window, width=20)
entry_cor_fundo.pack(padx=5)

# Botão para escolher cor de fundo
tk.Button(window, text="Escolher", command=escolher_cor_fundo, font=("Arial", 11, "bold"), background='#05f244').pack(pady=5)

tk.Label(window, text="Cor do texto", font=("Arial", 11, "bold")).pack()
entry_cor_texto = tk.Entry(window, width=20)
entry_cor_texto.pack(padx=5)

# Botão para escolher cor do texto
tk.Button(window, text="Escolher", command=escolher_cor_texto, font=("Arial", 11, "bold"), background='#07dce3').pack(pady=5)

tk.Label(window, text="Texto para transformar Em imagem", font=("Arial", 11, "bold")).pack()
results_text = scrolledtext.ScrolledText(window, width=120, height=35, font=("Arial", 11, "bold"))
results_text.pack(pady=5)

window.mainloop()
