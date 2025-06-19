import zlib
from stegano import lsb
import tkinter as tk
from tkinter import filedialog
import os

# Função para escolher a imagem PNG
def escolher_imagem():
    caminho = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
    if caminho:
        entrada_imagem.set(caminho)
        area_status.insert(tk.END, f"[INFO] Imagem selecionada: {caminho}\n\n")

# Função para escolher o arquivo payload
def escolher_payload():
    caminho = filedialog.askopenfilename()
    if caminho:
        arquivo_payload.set(caminho)
        area_status.insert(tk.END, f"[INFO] Payload selecionado: {caminho}\n\n")

# Função para esconder o payload comprimido na imagem
def esconder_payload():
    try:
        input_image = entrada_imagem.get()
        payload_file = arquivo_payload.get()

        if not input_image or not payload_file:
            raise ValueError("Selecione uma imagem e um arquivo payload.")

        area_status.insert(tk.END, "\n[PROCESSANDO] Lendo e comprimindo o payload\n\n")
        with open(payload_file, "rb") as file:
            payload_data = file.read()

        compressed_payload = zlib.compress(payload_data)
        compressed_payload_str = compressed_payload.decode('latin-1')

        output_image = os.path.splitext(input_image)[0] + "_com_payload.png"
        lsb.hide(input_image, compressed_payload_str).save(output_image)

        area_status.insert(tk.END, f"[SUCESSO] Payload escondido em: {output_image}\n\n")
    except Exception as e:
        area_status.insert(tk.END, f"[ERRO] {str(e)}\n\n")

# Função para extrair o payload de uma imagem
def extrair_payload():
    try:
        input_image = entrada_imagem.get()
        if not input_image:
            raise ValueError("Selecione uma imagem com payload embutido.")

        area_status.insert(tk.END, "\n[PROCESSANDO] Extraindo payload da imagem\n\n")
        mensagem_oculta = lsb.reveal(input_image)

        if not mensagem_oculta:
            raise ValueError("Nenhum payload encontrado na imagem.")

        payload_descomprimido = zlib.decompress(mensagem_oculta.encode('latin-1'))

        output_file = os.path.splitext(input_image)[0] + "_extraido.exe"
        with open(output_file, "wb") as file:
            file.write(payload_descomprimido)

        area_status.insert(tk.END, f"[SUCESSO] Payload extraído e salvo em: {output_file}\n\n")
    except Exception as e:
        area_status.insert(tk.END, f"[ERRO] {str(e)}\n\n")

# ------------------ GUI ------------------ #

# Janela principal
janela = tk.Tk()
janela.geometry("970x650")
janela.title("Esteganografia com Payload (LSB + Zlib)")

entrada_imagem = tk.StringVar()
arquivo_payload = tk.StringVar()

# Seção de entrada
tk.Label(janela, text="Imagem PNG:").pack(pady=5)
tk.Entry(janela, textvariable=entrada_imagem, width=50).pack()
tk.Button(janela, text="Escolher Imagem", command=escolher_imagem).pack(pady=5)

tk.Label(janela, text="Arquivo Payload:").pack(pady=5)
tk.Entry(janela, textvariable=arquivo_payload, width=50).pack()
tk.Button(janela, text="Escolher Payload", command=escolher_payload).pack(pady=5)

tk.Button(janela, text="Esconder Payload na Imagem", command=esconder_payload, bg="green", fg="white").pack(pady=10)
tk.Button(janela, text="Extrair Payload da Imagem", command=extrair_payload, bg="blue", fg="white").pack(pady=5)

# Área de status (log)
frame_status = tk.Frame(janela)
frame_status.pack(pady=10)

scrollbar = tk.Scrollbar(frame_status)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

area_status = tk.Text(frame_status, width=130, height=20, font=("Arial", 10), yscrollcommand=scrollbar.set)
area_status.pack()

scrollbar.config(command=area_status.yview)

# Executar a aplicação
janela.mainloop() 
