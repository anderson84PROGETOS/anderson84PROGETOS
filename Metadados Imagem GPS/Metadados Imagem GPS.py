import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image
import piexif
from datetime import datetime
import webbrowser

latitude = None
longitude = None

def formatar_data_hora(exif_datetime):
    """Converte 'YYYY:MM:DD HH:MM:SS' em 'DD/MM/YYYY   HH:MM:SS'"""
    if isinstance(exif_datetime, bytes):
        exif_datetime = exif_datetime.decode()
    try:
        dt = datetime.strptime(exif_datetime, "%Y:%m:%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y   %H:%M:%S")
    except:
        return exif_datetime  # caso não siga o padrão

def abrir_imagem():
    global latitude, longitude
    caminho_imagem = filedialog.askopenfilename(
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if caminho_imagem:
        mostrar_metadados(caminho_imagem)   

def dms_para_decimal(dms, ref):
    """Converte EXIF DMS para graus decimais"""
    graus = dms[0][0] / dms[0][1]
    minutos = dms[1][0] / dms[1][1]
    segundos = dms[2][0] / dms[2][1]
    decimal = graus + minutos / 60 + segundos / 3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def mostrar_metadados(caminho):
    global latitude, longitude
    img = Image.open(caminho)
    exif_bytes = img.info.get('exif')
    resultado_texto.delete('1.0', tk.END)

    # Data e hora atuais
    agora = datetime.now()
    resultado_texto.insert(tk.END, f"Data atual: {agora.strftime('%d/%m/%Y')}   Hora atual: {agora.strftime('%H:%M:%S')}\n\n")

    if not exif_bytes:
        resultado_texto.insert(tk.END, "Nenhum metadado EXIF encontrado.\n")
        abrir_mapa_button.config(state=tk.DISABLED)
        abrir_streetview_button.config(state=tk.DISABLED)
        return

    exif_dict = piexif.load(exif_bytes)
    exif_dict.pop('thumbnail', None)

    # Data/Hora da foto
    date_time_original = exif_dict.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal, None)
    if date_time_original:
        date_time_original = formatar_data_hora(date_time_original)
        resultado_texto.insert(tk.END, f"Data/Hora da foto (DateTimeOriginal): {date_time_original}\n")

    date_time_digitized = exif_dict.get('Exif', {}).get(piexif.ExifIFD.DateTimeDigitized, None)
    if date_time_digitized:
        date_time_digitized = formatar_data_hora(date_time_digitized)
        resultado_texto.insert(tk.END, f"Data/Hora da foto (DateTimeDigitized): {date_time_digitized}\n")

    # GPS
    gps_info = exif_dict.get('GPS', {})
    if gps_info:
        lat_dms = gps_info.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef)
        lon_dms = gps_info.get(piexif.GPSIFD.GPSLongitude)
        lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef)

        if lat_dms and lat_ref and lon_dms and lon_ref:
            lat_ref = lat_ref.decode() if isinstance(lat_ref, bytes) else lat_ref
            lon_ref = lon_ref.decode() if isinstance(lon_ref, bytes) else lon_ref
            latitude = dms_para_decimal(lat_dms, lat_ref)
            longitude = dms_para_decimal(lon_dms, lon_ref)
            resultado_texto.insert(tk.END, f"\nGPS Latitude: {latitude}\nGPS Longitude: {longitude}\n")

            # Gerar links
            google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
            street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
            resultado_texto.insert(tk.END, f"\nGoogle Maps: {google_maps_url}\n\nStreet View: {street_view_url}\n")

            abrir_mapa_button.config(state=tk.NORMAL)
            abrir_streetview_button.config(state=tk.NORMAL)
        else:
            latitude = longitude = None
            resultado_texto.insert(tk.END, "\nEsta foto não possui dados de GPS.\n")
            abrir_mapa_button.config(state=tk.DISABLED)
            abrir_streetview_button.config(state=tk.DISABLED)
    else:
        latitude = longitude = None
        resultado_texto.insert(tk.END, "\nEsta foto não possui dados de GPS.\n")
        abrir_mapa_button.config(state=tk.DISABLED)
        abrir_streetview_button.config(state=tk.DISABLED)


    # Mostrar todos os outros metadados
    for ifd in exif_dict:
        resultado_texto.insert(tk.END, f"\n[{ifd}]\n")
        for tag in exif_dict[ifd]:
            nome_tag = piexif.TAGS[ifd][tag]["name"]
            valor_tag = exif_dict[ifd][tag]
            if isinstance(valor_tag, bytes):
                try:
                    valor_tag = valor_tag.decode()
                except:
                    valor_tag = str(valor_tag)
            resultado_texto.insert(tk.END, f"{nome_tag}: {valor_tag}\n")

def abrir_no_google_maps():
    if latitude is not None and longitude is not None:
        google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        webbrowser.open(google_maps_url)
        resultado_texto.insert(tk.END, f"\nGoogle Maps: {google_maps_url}")

def abrir_no_google_street_view():
    if latitude is not None and longitude is not None:
        street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
        webbrowser.open(street_view_url)
        resultado_texto.insert(tk.END, f"\n\nStreet View: {street_view_url}")

# Interface gráfica
window = tk.Tk()
window.title("Metadados Imagem GPS")
window.geometry("1280x950")

btn_abrir = tk.Button(window, text="Escolher Imagem", command=abrir_imagem, font=("Arial", 12), bg="#05e1fa")
btn_abrir.pack(pady=10)

abrir_mapa_button = tk.Button(window, text="Abrir no Google Maps", command=abrir_no_google_maps, state=tk.DISABLED, font=("Arial", 12), bg="#00FF00")
abrir_mapa_button.pack(pady=5)

abrir_streetview_button = tk.Button(window, text="Abrir no Google Street View", command=abrir_no_google_street_view, state=tk.DISABLED, font=("Arial", 12), bg="#fab005")
abrir_streetview_button.pack(pady=5)

resultado_texto = scrolledtext.ScrolledText(window, width=132, height=42, font=("Arial", 12))
resultado_texto.pack(padx=10, pady=10)

window.mainloop()
