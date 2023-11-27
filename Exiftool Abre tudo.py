import tkinter as tk
from tkinter import filedialog
from PIL import Image, ExifTags
from tkinter import Scrollbar
import PyPDF2
import docx2txt
import webbrowser
from fractions import Fraction

latitude = None
longitude = None

def abrir_no_google_maps():
    if latitude is not None and longitude is not None:
        try:
            # Extraia graus, minutos e segundos
            lat_deg, lat_min, lat_sec = map(float, latitude)
            lon_deg, lon_min, lon_sec = map(float, longitude)

            # Calcular graus decimais
            lat_decimal = lat_deg + lat_min / 60 + lat_sec / 3600
            lon_decimal = lon_deg + lon_min / 60 + lon_sec / 3600

            # Converta latitude e longitude em strings com um número fixo de casas decimais
            lat_str = "-{:.13f}".format(lat_decimal)  # Adicione um hífen antes do valor da latitude
            lon_str = "-{:.13f}".format(lon_decimal)  # Adicione um hífen antes do valor da longitude

            google_maps_url = "https://www.google.com/maps?q={},{}".format(lat_str, lon_str)
            webbrowser.open(google_maps_url)
            text_box.insert(tk.END, f"\nGPS Latitude: {lat_str}\nGPS Longitude: {lon_str}")
        except Exception as e:
            error_message = f"Error: {str(e)}, latitude: {latitude}, longitude: {longitude}"
            text_box.insert(tk.END, f"\nFailed to open Google Maps. {error_message}")

def open_file():
    global latitude, longitude

    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.ico"),
                                                     ("CSV Files", "*.csv"),
                                                     ("Text Files", "*.txt"),
                                                     ("Word Documents", "*.docx"),
                                                     ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.ico"),
                                                     ("PDF Files", "*.pdf"),
                                                     ("Executable Files", "*.exe")])
    if file_path:
        try:
            if file_path.lower().endswith((".csv", ".txt")):
                with open(file_path, 'r', encoding='utf-8') as file:  # Especifica a codificação como utf-8
                    content = file.read()
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, content)
            elif file_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".ico")):
                image = Image.open(file_path)
                exif_data = image._getexif()
                if exif_data is not None:
                    exif_info = ""
                    latitude = None
                    longitude = None

                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_info += f"{tag_name}: {value}\n"

                        if tag_name == 'GPSInfo':
                            for key in value.keys():
                                sub_tag_name = ExifTags.GPSTAGS.get(key, key)
                                exif_info += f"{sub_tag_name}: {value[key]}\n"

                            # Extrair Latitude e Longitude
                            latitude = value.get(2)  # 2 representa a tag Latitude em GPSInfo
                            longitude = value.get(4)  # 4 representa a tag Longitude em GPSInfo

                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, exif_info)

                    if latitude is not None and longitude is not None:
                        text_box.insert(tk.END, f"\nGPS Latitude: {latitude}\nGPS Longitude: {longitude}\n\n")  # Adicione caracteres de nova linha
                        abrir_mapa_button.config(state=tk.NORMAL)
                else:
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, "No EXIF information found.")
            elif file_path.lower().endswith((".pdf", ".exe")):
                if file_path.lower().endswith(".pdf"):
                    pdf_file = open(file_path, 'rb')
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
                    pdf_file.close()
                else:  # .exe file
                    with open(file_path, 'rb') as file:
                        content = file.read().hex()
                    text_content = "Hexadecimal representation of the executable file:\n" + content
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, text_content)
            elif file_path.lower().endswith(".docx"):
                text_content = docx2txt.process(file_path)
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, text_content)
        except Exception as e:
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, f"Failed to open the file {file_path}. Error: {str(e)}.")

def clear_results():
    global latitude, longitude
    latitude = None
    longitude = None
    text_box.delete(1.0, tk.END)
    abrir_mapa_button.config(state=tk.DISABLED)

window = tk.Tk()
window.wm_state('zoomed')
window.title("Data Analysis")
window.geometry("400x400")

try:
    window.iconbitmap("icone.ico")
except tk.TclError:
    print("Failed to load the icon file.")

scrollbar = Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

btn_open_file = tk.Button(window, text="Open file", command=open_file, bg="#00FFFF")
btn_open_file.pack(pady=10)

btn_clear_results = tk.Button(window, text="Clear results", command=clear_results, bg="#D2691E")
btn_clear_results.pack(pady=10)

abrir_mapa_button = tk.Button(window, text="Abrir no Google Maps", command=abrir_no_google_maps, state=tk.DISABLED, font=("Arial", 12), bg="#00FF00")
abrir_mapa_button.pack(pady=5)

text_box = tk.Text(window, height=48, width=170, font=("TkDefaultFont", 10, "bold"))
text_box.pack(pady=10)

text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

window.mainloop()
