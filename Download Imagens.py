import tkinter as tk
import requests
from io import BytesIO
from PIL import Image, ImageFile
import os
import shutil
import webbrowser
from tkinter import messagebox

# Cria a janela
window = tk.Tk()
window.geometry('500x500')
window.title("Baixar Imagens")

# Cria os widgets
image_name_label = tk.Label(window, text="Insira o nome da imagem:")
image_name_entry = tk.Entry(window)
num_images_label = tk.Label(window, text="Quantas imagens deseja baixar?")
num_images_entry = tk.Entry(window)
format_label = tk.Label(window, text="Selecione o formato da imagem:")
formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico"]
format_var = tk.StringVar()
format_var.set(formats[0])
format_dropdown = tk.OptionMenu(window, format_var, *formats)
download_button = tk.Button(window, text="Baixar")

# Define a função para baixar a imagem
def download_images():
    # Obtem os valores dos widgets
    image_name = image_name_entry.get()
    num_images = int(num_images_entry.get())
    format = format_var.get()

    # Cria a pasta para salvar as imagens
    folder_name = image_name.replace(" ", "_")
    os.makedirs(folder_name, exist_ok=True)

    # Faz a busca no Google Imagens
    url = f"https://www.google.com.br/search?q={image_name}&tbm=isch"
    response = requests.get(url)
    response.raise_for_status()

    # Obtém as URLs das imagens
    image_urls = response.content.decode('latin1').split('"https://')[1:] 

    # Baixa as imagens
    for i in range(num_images):
        # Obtém a URL da imagem
        image_url = "https://" + image_urls[i].split('"')[0]

        # Faz o download da imagem
        response = requests.get(image_url)
        response.raise_for_status()

        # Cria um objeto Image a partir do conteúdo baixado
        img = Image.open(BytesIO(response.content))

        # Define o nome do arquivo de acordo com o número da imagem
        filename = os.path.join(folder_name, f"{image_name}_{i+1}{format.lower()}")

        # Salva a imagem no disco
        ImageFile.MAXBLOCK = img.size[0] * img.size[1]
        img.save(filename)

    # Mostra a mensagem de sucesso
    messagebox.showinfo("Sucesso", f"{num_images} imagens baixadas e salvas em '{folder_name}'")

# Adiciona os widgets à janela
image_name_label.pack()
image_name_entry.pack()
num_images_label.pack()
num_images_entry.pack()
format_label.pack()
format_dropdown.pack()
download_button.pack()

# Define o botão de download para baixar as imagens quando clicado
download_button.config(command=download_images)

# Inicia o loop da GUI
window.mainloop()
