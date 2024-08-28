import re
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar, Listbox
import tkinter.font as tkFont
from PIL import Image
import exifread

def extrair_coordenadas(conteudo):
    # Usar expressões regulares para encontrar todas as entradas de cidade, latitude e longitude
    coordenadas = re.findall(r'city:\s*(.*?)\s*latitude:\s*([-]?\d*\.\d+)\s*longitude:\s*([-]?\d*\.\d+)', conteudo, re.DOTALL)
    if coordenadas:
        return coordenadas
    else:
        raise ValueError("Coordenadas não encontradas no arquivo.")

def extrair_coordenadas_imagem(caminho_arquivo):
    # Extrair coordenadas GPS de uma imagem usando ExifRead
    with open(caminho_arquivo, 'rb') as img_file:
        tags = exifread.process_file(img_file)
        
        # Verificar se as coordenadas GPS estão disponíveis
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            latitude = tags['GPS GPSLatitude'].values
            longitude = tags['GPS GPSLongitude'].values
            lat_ref = tags.get('GPS GPSLatitudeRef').values
            lon_ref = tags.get('GPS GPSLongitudeRef').values
            
            # Converter coordenadas para formato decimal
            lat = convert_to_degrees(latitude)
            lon = convert_to_degrees(longitude)
            
            if lat_ref != "N":
                lat = -lat
            if lon_ref != "E":
                lon = -lon
            
            return f"Latitude: {lat}, Longitude: {lon}"
        else:
            raise ValueError("Coordenadas GPS não encontradas na imagem.")

def convert_to_degrees(value):
    # Converter valores de coordenadas GPS para formato decimal
    d = float(value[0].num) / float(value[0].den)
    m = float(value[1].num) / float(value[1].den)
    s = float(value[2].num) / float(value[2].den)
    
    return d + (m / 60.0) + (s / 3600.0)

def abrir_google_maps():
    coordenadas = coordenadas_listbox.get(tk.ACTIVE)
    if coordenadas:
        # Extrair latitude e longitude da string
        match = re.search(r'Latitude: ([\d.-]+), Longitude: ([\d.-]+)', coordenadas)
        if match:
            latitude, longitude = match.groups()
            url = f"https://www.google.com/maps?q={latitude},{longitude}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Aviso", "Formato de coordenadas inválido.")
    else:
        messagebox.showwarning("Aviso", "Nenhuma coordenada selecionada.")

def selecionar_arquivo():
    caminho_arquivo = filedialog.askopenfilename(filetypes=[("All files", "*.*")])  # Aceita todos os tipos de arquivo
    if caminho_arquivo:
        try:
            if caminho_arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                # Se o arquivo for uma imagem, extrair coordenadas da imagem
                coordenada = extrair_coordenadas_imagem(caminho_arquivo)
                coordenadas_listbox.delete(0, tk.END)
                coordenadas_listbox.insert(tk.END, coordenada)
            else:
                # Ler o arquivo como texto
                with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as file:
                    conteudo = file.read()
                coordenadas = extrair_coordenadas(conteudo)
                coordenadas_listbox.delete(0, tk.END)  # Limpa a lista antes de adicionar novas coordenadas
                for cidade, lat, lon in coordenadas:
                    coordenadas_listbox.insert(tk.END, f"City: {cidade}, Latitude: {lat}, Longitude: {lon}\n")
            
            abrir_google_maps_button.config(state=tk.NORMAL)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
        except Exception as e:
            messagebox.showerror("Erro", f"Um erro ocorreu: {str(e)}")

root = tk.Tk()
root.title("Leitor de Coordenadas e Google Maps")
root.geometry("900x600")

# Cria um objeto de fonte com tamanho 12
font_12 = tkFont.Font(family="TkDefaultFont", size=12)

# Botão para selecionar o arquivo
selecionar_arquivo_button = tk.Button(root, text="Selecionar Arquivo", command=selecionar_arquivo, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
selecionar_arquivo_button.pack(pady=10)

# Configura a scrollbar e a Listbox para exibir coordenadas
scrollbar = Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

coordenadas_listbox = Listbox(root, yscrollcommand=scrollbar.set, font=font_12, selectmode=tk.SINGLE)
coordenadas_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
scrollbar.config(command=coordenadas_listbox.yview)

# Botão para abrir coordenadas no Google Maps
abrir_google_maps_button = tk.Button(root, text="Abrir no Google Maps", command=abrir_google_maps, state=tk.DISABLED, bg="#05fae5", font=("TkDefaultFont", 11, "bold"))
abrir_google_maps_button.pack(pady=10)

root.mainloop()
