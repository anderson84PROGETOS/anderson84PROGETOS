import re
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, END
import exifread
import tkinter.font as tkFont  # Importa a biblioteca para manipulação de fontes

def selecionar_arquivo():
    arquivo = filedialog.askopenfilename(title="Selecione um arquivo", filetypes=[
        ("Todos os Arquivos", "*.*"), 
        ("Imagens", "*.jpg;*.jpeg"), 
        ("HTML", "*.html"), 
        ("Texto", "*.txt")
    ])
    if arquivo:
        if arquivo.lower().endswith('.html'):
            mostrar_coordenadas_html(arquivo)
        elif arquivo.lower().endswith(('.jpg', '.jpeg')):
            mostrar_coordenadas_imagem(arquivo)
        elif arquivo.lower().endswith('.txt'):
            mostrar_coordenadas_txt(arquivo)
        else:
            mostrar_coordenadas_arquivo(arquivo)

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1]
    seconds = dms[2]
    
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def mostrar_coordenadas_html(arquivo):
    try:
        with open(arquivo, 'r') as file:
            content = file.read()

        coords_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
        matches = re.findall(coords_pattern, content)

        if matches:
            coordenadas_listbox.delete(0, END)
            for match in matches:
                latitude, longitude = match
                coordenadas_listbox.insert(END, f"{latitude}, {longitude}")
                coordenadas_listbox.insert(END, "")
            abrir_google_maps_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Erro", "Nenhuma coordenada encontrada no arquivo HTML.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo HTML: {str(e)}")

def mostrar_coordenadas_imagem(arquivo):
    try:
        with open(arquivo, 'rb') as file:
            tags = exifread.process_file(file)
        
        latitude = None
        longitude = None

        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat_tag = tags['GPS GPSLatitude'].values
            lon_tag = tags['GPS GPSLongitude'].values
            lat_ref = tags['GPS GPSLatitudeRef'].values
            lon_ref = tags['GPS GPSLongitudeRef'].values

            latitude = get_decimal_from_dms(lat_tag, lat_ref)
            longitude = get_decimal_from_dms(lon_tag, lon_ref)

        if latitude and longitude:
            coordenadas_listbox.delete(0, END)
            coordenadas_listbox.insert(END, f"{latitude}, {longitude}")
            coordenadas_listbox.insert(END, "")
            abrir_google_maps_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Erro", "Nenhuma coordenada encontrada nos dados EXIF da imagem.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo de imagem: {str(e)}")

def mostrar_coordenadas_txt(arquivo):
    try:
        with open(arquivo, 'r') as file:
            content = file.read()

        coords_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
        matches = re.findall(coords_pattern, content)

        if matches:
            coordenadas_listbox.delete(0, END)
            for match in matches:
                latitude, longitude = match
                coordenadas_listbox.insert(END, f"{latitude}, {longitude}")
                coordenadas_listbox.insert(END, "")
            abrir_google_maps_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Erro", "Nenhuma coordenada encontrada no arquivo de texto.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo de texto: {str(e)}")

def mostrar_coordenadas_arquivo(arquivo):
    try:
        with open(arquivo, 'r') as file:
            content = file.read()

        coords_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
        matches = re.findall(coords_pattern, content)

        if matches:
            coordenadas_listbox.delete(0, END)
            for match in matches:
                latitude, longitude = match
                coordenadas_listbox.insert(END, f"{latitude}, {longitude}")
                coordenadas_listbox.insert(END, "")
            abrir_google_maps_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Erro", "Nenhuma coordenada encontrada no arquivo.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo: {str(e)}")

def abrir_google_maps():
    selecao = coordenadas_listbox.curselection()
    if selecao:
        coordenada = coordenadas_listbox.get(selecao).strip()
        if coordenada:
            latitude, longitude = coordenada.split(", ")
            google_maps_url = f'https://www.google.com/maps?q={latitude},{longitude}'
            webbrowser.open(google_maps_url)
    else:
        messagebox.showerror("Erro", "Por favor, selecione uma coordenada.")

root = tk.Tk()
root.title("Leitor de Coordenadas e Google Maps")
root.geometry("800x500")

# Cria um objeto de fonte com tamanho 12
font_12 = tkFont.Font(family="TkDefaultFont", size=12)

selecionar_arquivo_button = tk.Button(root, text="Selecionar Arquivo", command=selecionar_arquivo, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
selecionar_arquivo_button.pack(pady=10)

scrollbar = Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

coordenadas_listbox = Listbox(root, yscrollcommand=scrollbar.set, font=font_12)
coordenadas_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
scrollbar.config(command=coordenadas_listbox.yview)

abrir_google_maps_button = tk.Button(root, text="Abrir no Google Maps", command=abrir_google_maps, state=tk.DISABLED, bg="#05fae5", font=("TkDefaultFont", 11, "bold"))
abrir_google_maps_button.pack(pady=10)

root.mainloop()
