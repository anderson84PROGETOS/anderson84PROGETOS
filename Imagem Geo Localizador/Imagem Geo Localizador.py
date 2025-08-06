import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if not info:
        return None
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_data[sub_decoded] = value[t]
            exif_data["GPSInfo"] = gps_data
        else:
            exif_data[decoded] = value
    return exif_data

def convert_to_decimal(value):
    d, m, s = value
    return float(d) + float(m) / 60 + float(s) / 3600

def get_coordinates(gps_info):
    try:
        lat = convert_to_decimal(gps_info["GPSLatitude"])
        if gps_info["GPSLatitudeRef"] == "S":
            lat = -lat
        lon = convert_to_decimal(gps_info["GPSLongitude"])
        if gps_info["GPSLongitudeRef"] == "W":
            lon = -lon
        return lat, lon
    except Exception:
        return None
        
def abrir_navegador(url):
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

def open_google_maps():
    if current_coords:
        lat, lon = current_coords
        url = f"https://www.google.com/maps?q={lat},{lon}"
        abrir_navegador(url)

def open_google_street_view():
    if current_coords:
        lat, lon = current_coords
        url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
        abrir_navegador(url)

def open_yandex_search():
    if current_image_path:
        url = "https://yandex.com/search?text=&lr=219083"
        abrir_navegador(url)
        messagebox.showinfo(
            "Yandex Images",
            "A imagem foi selecionada.\nAgora faça o upload manualmente no site do Yandex Images que foi aberto no navegador."
        )

def format_date(date_str):
    if isinstance(date_str, str) and re.match(r"\d{4}:\d{2}:\d{2}", date_str):
        parts = date_str.split(":")
        if len(parts) >= 3:
            year, month, day = parts[:3]
            return f"{day}/{month}/{year}"
    return date_str

def select_image():
    global current_coords, current_image_path
    filepath = filedialog.askopenfilename(
        filetypes=[("Imagens", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tiff;*.gif"), ("Todos os arquivos", "*.*")]
    )
    if not filepath:
        return

    current_image_path = filepath
    current_coords = None

    exif_textbox.delete(1.0, tk.END)

    try:
        image = Image.open(filepath)
        exif_data = get_exif_data(image)

        if not exif_data:
            messagebox.showinfo("Sem EXIF", "A imagem não contém metadados EXIF.")
            exif_textbox.insert(tk.END, "Nenhum dado EXIF encontrado.")
            btn_maps.config(state=tk.DISABLED)
            btn_street.config(state=tk.DISABLED)
        else:
            for key, val in exif_data.items():
                if isinstance(val, dict):
                    exif_textbox.insert(tk.END, f"{key}:\n")
                    for subkey, subval in val.items():
                        if isinstance(subval, str):
                            subval = format_date(subval)
                        exif_textbox.insert(tk.END, f"{subkey}: {subval}\n")
                else:
                    if isinstance(val, str):
                        val = format_date(val)
                    exif_textbox.insert(tk.END, f"{key}: {val}\n\n")

            gps_info = exif_data.get("GPSInfo")
            coords = get_coordinates(gps_info) if gps_info else None

            if coords:
                current_coords = coords
                lat, lon = coords
                lat_round = round(lat, 4)
                lon_round = round(lon, 4)
                exif_textbox.insert(
                    tk.END,
                    f"\n\nCoordenadas Extraídas\n\n"
                    f"Latitude: {lat}\nLongitude: {lon}\n\n\n"
                    f"Latitude: {lat_round}\nLongitude: {lon_round}\n"
                    f"\nGeolocalização: {lat_round}, {lon_round}"
                )
                btn_maps.config(state=tk.NORMAL)
                btn_street.config(state=tk.NORMAL)
            else:
                exif_textbox.insert(tk.END, "\n\nA imagem não possui coordenadas GPS.")
                btn_maps.config(state=tk.DISABLED)
                btn_street.config(state=tk.DISABLED)

        btn_yandex.config(state=tk.NORMAL)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar a imagem: {e}")

# Interface gráfica
root = tk.Tk()
root.title("Imagem Geo Localizador")
root.geometry("1280x1024")

current_coords = None
current_image_path = None

btn_select = tk.Button(root, text="Selecionar Imagem", bg="#f7b705", command=select_image)
btn_select.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

btn_maps = tk.Button(btn_frame, text="Abrir no Google Maps", bg="#05fc32", command=open_google_maps, state=tk.DISABLED)
btn_maps.pack(side=tk.LEFT, padx=10)

btn_street = tk.Button(btn_frame, text="Abrir no Street View", bg="#05d3f7", command=open_google_street_view, state=tk.DISABLED)
btn_street.pack(side=tk.LEFT, padx=10)

btn_yandex = tk.Button(btn_frame, text="Buscar no Yandex Images", bg="#f76505", command=open_yandex_search, state=tk.DISABLED)
btn_yandex.pack(side=tk.LEFT, padx=10)

exif_textbox = scrolledtext.ScrolledText(root, width=120, height=50, wrap=tk.NONE)
exif_textbox.pack(pady=10)

x_scroll = tk.Scrollbar(root, orient="horizontal", command=exif_textbox.xview)
exif_textbox.configure(xscrollcommand=x_scroll.set)
x_scroll.pack(fill="x")

root.mainloop()
