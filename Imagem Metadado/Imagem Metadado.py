import os
import webbrowser
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image, ExifTags
from datetime import datetime

# Funções
def abrir_imagem_manual():
    caminho_imagem = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Arquivos de imagem", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp"), ("Todos os arquivos", "*.*")]
    )
    if not caminho_imagem:
        return
    mostrar_info_imagem(caminho_imagem)

def ifd_to_float(val):
    # Converte IFDRational ou tupla (num, den) para float
    try:
        return float(val)
    except:
        try:
            return float(val[0]) / float(val[1])
        except:
            return 0.0

def converter_gps_para_decimal(gps_coord, ref):
    graus = ifd_to_float(gps_coord[0])
    minutos = ifd_to_float(gps_coord[1])
    segundos = ifd_to_float(gps_coord[2])
    dec = graus + minutos / 60.0 + segundos / 3600.0
    if ref in ['S', 'W']:
        dec = -dec
    return dec

def mostrar_info_imagem(caminho):
    try:
        img = Image.open(caminho)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
        return

    text_area.delete(1.0, tk.END)
    
    # Informações básicas
    text_area.insert(tk.END, f"Arquivo: {caminho}\n\n")   

    # Formato exato do arquivo (pela extensão)
    ext_arquivo = os.path.splitext(caminho)[1].lower()  # pega extensão com ponto
    text_area.insert(tk.END, f"Formato Exato do Arquivo: {ext_arquivo}\n\n")

    text_area.insert(tk.END, f"Modo: {img.mode}\n\n")
    text_area.insert(tk.END, f"Tamanho (pixels): {img.size}\n\n")

    # Tamanho real do arquivo
    tamanho_bytes = os.path.getsize(caminho)
    tamanho_mb = tamanho_bytes / (1024*1024)
    tamanho_bytes_formatado = f"{tamanho_bytes:,}".replace(",", ".")
    tamanho_mb_formatado = f"{tamanho_mb:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    text_area.insert(tk.END, f"Tamanho da imagem: {tamanho_mb_formatado} MB ({tamanho_bytes_formatado} bytes)\n\n")

    # EXIF e Data/Hora
    gps_info = None
    date_time_str = None
    try:
        exif_data = img._getexif()
        if exif_data:
            text_area.insert(tk.END, "\n========== Metadados EXIF ==========\n")
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                text_area.insert(tk.END, f"\n{tag}: {value}\n")
                if tag in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                    date_time_str = value
                if tag == "GPSInfo":
                    gps_info = value
                    
            # Data/Hora legível
            if date_time_str:
                try:
                    dt = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")
                    data_formatada = dt.strftime("%d/%m/%Y")
                    hora_formatada = dt.strftime("%H:%M")
                    text_area.insert(tk.END, "\n\n========== Metadados EXIF Hora e Data E GPS ==========\n")
                    text_area.insert(tk.END, f"\nData da foto: {data_formatada}\n\nHora da foto: {hora_formatada}\n\n")
                except:
                    pass
            text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "Nenhum metadado EXIF encontrado.\n\n")
    except Exception as e:
        text_area.insert(tk.END, f"Erro ao ler EXIF: {e}\n\n")

    # GPS
    if gps_info:
        try:
            gps_tags = {}
            for key in gps_info:
                decoded = ExifTags.GPSTAGS.get(key, key)
                gps_tags[decoded] = gps_info[key]

            lat = converter_gps_para_decimal(gps_tags['GPSLatitude'], gps_tags['GPSLatitudeRef'])
            lon = converter_gps_para_decimal(gps_tags['GPSLongitude'], gps_tags['GPSLongitudeRef'])

            # Exibir GPS no formato exato que você quer
            text_area.insert(tk.END, f"GPS Latitude: {lat}\nGPS Longitude: {lon}\n\n")
            google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80"
            text_area.insert(tk.END, f"Google Maps: {google_maps_url}\n\n")
            text_area.insert(tk.END, f"Street View: {street_view_url}\n\n")

            # Habilita botões
            btn_maps.config(command=lambda: webbrowser.open(google_maps_url), state=tk.NORMAL)
            btn_street.config(command=lambda: webbrowser.open(street_view_url), state=tk.NORMAL)

        except Exception as e:
            text_area.insert(tk.END, f"Erro ao processar GPS: {e}\n\n")
            btn_maps.config(state=tk.DISABLED)
            btn_street.config(state=tk.DISABLED)
    else:
        btn_maps.config(state=tk.DISABLED)
        btn_street.config(state=tk.DISABLED)

# GUI
root = tk.Tk()
root.title("Visualizador de Imagem e Metadados")
root.geometry('1280x1024')

btn_abrir = tk.Button(root, text="Abrir Imagem", bg="#f7ff05", fg="black", command=abrir_imagem_manual)
btn_abrir.pack(pady=10)

# Botões fixos de Maps e Street View
btn_maps = tk.Button(root, text="Abrir no Google Maps", bg="#03fc24", fg="black", state=tk.DISABLED)
btn_maps.pack(pady=2)
btn_street = tk.Button(root, text="Abrir no Street View", bg="#03f0fc", fg="black", state=tk.DISABLED)
btn_street.pack(pady=2)

text_area = scrolledtext.ScrolledText(root, width=150, height=45, font=("Arial", 11, "bold"))
text_area.pack(padx=10, pady=10)

root.mainloop()
