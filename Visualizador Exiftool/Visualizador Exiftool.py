import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ExifTags
import webbrowser
import re  # Para encontrar URLs no texto

# Variável global para armazenar a URL clicada
selected_url = ""

def extract_exif(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data is not None:
            exif_info = {}
            for tag, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_info[tag_name] = value
            return exif_info
        else:
            return None
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível extrair os dados EXIF.\n{e}")
        return None

def convert_to_degrees(value):
    """Converte o formato de coordenada GPS para graus decimais."""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def open_image():
    # Abrir o seletor de arquivos para escolher a imagem
    image_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg;*.jpeg;*.png")])
    if image_path:
        exif_info = extract_exif(image_path)
        display_exif(exif_info)

def display_exif(exif_info):
    global google_maps_url, selected_url
    google_maps_url = ""
    selected_url = ""  # Reseta a URL selecionada

    # Limpa a área de texto antes de exibir novos dados
    text_output.delete(1.0, tk.END)
    
    if exif_info:
        formatted_output = []
        gps_latitude = None
        gps_longitude = None
        
        for tag, value in exif_info.items():
            if tag == 'GPSInfo':
                gps_info = value
                gps_latitude = gps_info.get(2)  # Latitude
                gps_latitude_ref = gps_info.get(1)  # Norte/Sul
                gps_longitude = gps_info.get(4)  # Longitude
                gps_longitude_ref = gps_info.get(3)  # Leste/Oeste

                if gps_latitude and gps_longitude:
                    lat = convert_to_degrees([x for x in gps_latitude])
                    lon = convert_to_degrees([x for x in gps_longitude])
                    
                    if gps_latitude_ref == 'S':
                        lat = -lat
                    if gps_longitude_ref == 'W':
                        lon = -lon
                        
                    # Define a URL do Google Maps
                    google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                    street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80"
                    
                    formatted_output.append(f"Latitude: {lat}")
                    formatted_output.append(f"Longitude: {lon}")
                    formatted_output.append(f"\nURL do Google Maps: {google_maps_url}\n")
                    formatted_output.append(f"\nGoogle Maps (Street View): {street_view_url}\n")
            else:
                formatted_output.append(f"{tag}: {value}")
        
        # Exibe os resultados formatados
        formatted_text = "\n".join(formatted_output)
        text_output.insert(tk.END, formatted_text)
        
        if google_maps_url:
            btn_google_maps.config(state=tk.NORMAL)
        else:
            btn_google_maps.config(state=tk.DISABLED)
    else:
        text_output.insert(tk.END, "Nenhum dado EXIF encontrado.")
        btn_google_maps.config(state=tk.DISABLED)

def open_google_maps():
    """Função para abrir a URL selecionada no navegador."""
    if selected_url:
        webbrowser.open(selected_url)
    else:
        messagebox.showinfo("Aviso", "Nenhuma URL selecionada.")

def click_on_text(event):
    """Detecta clique em URLs e define a URL selecionada."""
    global selected_url
    index = text_output.index(f"@{event.x},{event.y}")
    line = text_output.get(f"{index} linestart", f"{index} lineend")
    
    # Procurar por uma URL na linha
    urls = re.findall(r'(https?://[^\s]+)', line)
    
    if urls:
        # Armazena a URL selecionada
        selected_url = urls[0]
        
        # Seleciona o texto da URL
        start_index = line.index(selected_url)
        end_index = start_index + len(selected_url)
        text_output.tag_add("highlight", f"{text_output.index(f'{index} linestart')} + {start_index} chars", f"{text_output.index(f'{index} linestart')} + {end_index} chars")
        text_output.tag_config("highlight", background="yellow")
        
        messagebox.showinfo("URL Selecionada", f"URL selecionada: {selected_url}")
    else:
        selected_url = ""

# Criação da janela principal
root = tk.Tk()
root.title("Visualizador Exiftool")
root.geometry("1200x950")

# Botão para selecionar a imagem
btn_open_image = tk.Button(root, text="Abrir Imagem", command=open_image, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
btn_open_image.pack(pady=10)

# Botão para abrir o Google Maps
btn_google_maps = tk.Button(root, text="Abrir no Google Maps", command=open_google_maps, font=("TkDefaultFont", 11, "bold"), bg='#ffcc00', state=tk.DISABLED)
btn_google_maps.pack(pady=10)

# Área de texto com barra de rolagem para exibir as informações EXIF
text_output = ScrolledText(root, wrap=tk.WORD, width=135, height=42, font=("TkDefaultFont", 11, "bold"))           
text_output.pack(pady=10)

# Detecta clique na área de texto
text_output.bind("<Button-1>", click_on_text)

# Executa a janela
root.mainloop()
