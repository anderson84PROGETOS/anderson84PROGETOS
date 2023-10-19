import tkinter as tk
import qrcode
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import filedialog
# Função para gerar um código QR com tamanho personalizado
def gerar_qrcode():
    texto = entrada_texto.get()
    tamanho_str = entrada_tamanho.get()
    # Obter a largura e altura do tamanho inserido pelo usuário
    largura, altura = map(int, tamanho_str.split('x'))    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white") 
    # Redimensionar a imagem para o tamanho desejado
    img = img.resize((largura, altura), Image.ANTIALIAS)  
    # Caixa de diálogo para escolher onde salvar o QR code
    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("Arquivos PNG", "*.png")])
    if file_path:
        img.save(file_path)  # Salvar o QR code como imagem no caminho escolhido
        # Exibir o QR code na janela
        img = Image.open(file_path)
        img = ImageTk.PhotoImage(img)
        label_qrcode.config(image=img)
        label_qrcode.image = img
# Configurar a janela gráfica
janela = tk.Tk()
janela.wm_state('zoomed')
janela.title("Gerador de QR Code")
janela.geometry("400x500")
# Estilo de fonte em negrito
font_negrito = ("Helvetica", 12, "bold")
# Entrada de texto em negrito
label_texto = tk.Label(janela, text="Texto para o QR Code", font=("Helvetica", 12, "bold"))
label_texto.pack(pady=10)
entrada_texto = ttk.Entry(janela, width=80, font=font_negrito)
entrada_texto.pack(pady=10)
# Entrada de tamanho do QR code em negrito
label_tamanho = tk.Label(janela, text="Tamanho do QR Code (Largura 200x200 Altura)", font=("Helvetica", 12, "bold"))
label_tamanho.pack(pady=10)
entrada_tamanho = ttk.Entry(janela, width=30, font=font_negrito)
entrada_tamanho.pack(pady=10)
# Botão para gerar o QR code
botao_gerar = tk.Button(janela, text="Gerar QR Code", command=gerar_qrcode, font=("Helvetica", 12, "bold"), bg="#00FFFF")
botao_gerar.pack(pady=20)
# Rótulo para exibir o QR code
label_qrcode = tk.Label(janela)
label_qrcode.pack(pady=20)
janela.mainloop()
