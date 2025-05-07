import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar
from PIL import Image, ExifTags
import PyPDF2
import docx2txt
import webbrowser
import os

# Global variables for GPS coordinates
latitude = None
longitude = None

def extract_image_metadata(file_path):
    """Extract metadata and GPS coordinates from image files using PIL."""
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            metadata = {}
            gps_data = None
            if exif_data:
                metadata = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}
                # Check for GPSInfo
                if 34853 in exif_data:  # 34853 is the EXIF tag for GPSInfo
                    gps_data = exif_data[34853]
            return {"Metadata": metadata, "GPSData": gps_data}
    except Exception as e:
        return {"Error": f"Failed to extract image metadata: {str(e)}"}

def extract_pdf_metadata(file_path):
    """Extract metadata and text from PDF files using PyPDF2."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            metadata = reader.metadata
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            return {
                "Metadata": metadata if metadata else {"Message": "No PDF metadata found"},
                "ExtractedText": text[:500] + "..." if text else "No text extracted"
            }
    except Exception as e:
        return {"Error": f"PyPDF2 failed to extract metadata or text: {str(e)}"}

def extract_docx_text(file_path):
    """Extract text from DOCX files using docx2txt."""
    try:
        text = docx2txt.process(file_path)
        return {"ExtractedText": text[:500] + "..." if text else "No text extracted"}
    except Exception as e:
        return {"Error": f"docx2txt failed to extract text: {str(e)}"}

def open_file():
    global latitude, longitude
    file_path = filedialog.askopenfilename(
        filetypes=[("All files", "*.*"), ("Images", "*.jpg *.jpeg *.png *.tiff *.webp"), ("PDFs", "*.pdf"), ("Documents", "*.docx *.doc")]
    )
    if not file_path:
        text_box.insert(tk.END, "\nNo file selected.\n")
        return

    # Clear previous text
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, f"Selected file: {file_path}\n\n")

    # Reset GPS coordinates
    latitude = None
    longitude = None

    # Extract metadata based on file type
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in ('.jpg', '.jpeg', '.png', '.tiff', '.webp'):
        data = extract_image_metadata(file_path)
        if "Error" in data:
            text_box.insert(tk.END, f"Error: {data['Error']}\n")
            return

        # Display metadata
        text_box.insert(tk.END, "=== Image Metadata (PIL) ===\n\n")
        for key, value in data["Metadata"].items():
            text_box.insert(tk.END, f"{key}: {value}\n")
        text_box.insert(tk.END, "\n")

        # Extract GPS coordinates
        if data["GPSData"]:
            try:
                gps_info = {ExifTags.GPSTAGS.get(k, k): v for k, v in data["GPSData"].items()}
                text_box.insert(tk.END, "=== GPS Data ===\n\n")
                for key, value in gps_info.items():
                    text_box.insert(tk.END, f"{key}: {value}\n")
                text_box.insert(tk.END, "\n")

                # Parse GPS coordinates
                if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                    lat = gps_info['GPSLatitude']
                    lon = gps_info['GPSLongitude']
                    lat_ref = gps_info.get('GPSLatitudeRef', 'N')
                    lon_ref = gps_info.get('GPSLongitudeRef', 'E')

                    # Convert DMS to decimal
                    def dms_to_decimal(dms):
                        degrees, minutes, seconds = dms
                        decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
                        return decimal

                    latitude = dms_to_decimal(lat)
                    longitude = dms_to_decimal(lon)

                    # Adjust for direction
                    latitude = -latitude if lat_ref == 'S' else latitude
                    longitude = -longitude if lon_ref == 'W' else longitude

                    text_box.insert(tk.END, f"Parsed GPS Latitude: {latitude:.13f}\nParsed GPS Longitude: {longitude:.13f}\n")
                else:
                    text_box.insert(tk.END, "No GPS coordinates found in image.\n")
            except Exception as e:
                text_box.insert(tk.END, f"Error parsing GPS coordinates: {str(e)}\n")
        else:
            text_box.insert(tk.END, "No GPS data found in image.\n")

    elif file_ext == '.pdf':
        data = extract_pdf_metadata(file_path)
        if "Error" in data:
            text_box.insert(tk.END, f"Error: {data['Error']}\n")
            return

        text_box.insert(tk.END, "=== PDF Metadata (PyPDF2) ===\n")
        for key, value in data['Metadata'].items():
            text_box.insert(tk.END, f"{key}: {value}\n")
        text_box.insert(tk.END, f"Extracted Text (first 500 chars): {data['ExtractedText']}\n\n")
        text_box.insert(tk.END, "No GPS coordinates typically available in PDFs.\n")

    elif file_ext in ('.docx', '.doc'):
        data = extract_docx_text(file_path)
        if "Error" in data:
            text_box.insert(tk.END, f"Error: {data['Error']}\n")
            return

        text_box.insert(tk.END, "=== DOCX/DOC Text (docx2txt) ===\n")
        text_box.insert(tk.END, f"Extracted Text (first 500 chars): {data['ExtractedText']}\n\n")
        text_box.insert(tk.END, "No GPS coordinates typically available in DOCX/DOC files.\n")

    else:
        text_box.insert(tk.END, "Unsupported file type for metadata extraction.\n")

def abrir_no_google_maps():
    if latitude is None or longitude is None:
        text_box.insert(tk.END, "\nNo GPS coordinates available. Please select an image with GPS metadata.\n")
        return
    try:
        # Format latitude and longitude as strings
        lat_str = f"{latitude:.13f}"
        lon_str = f"{longitude:.13f}"

        # Generate Google Maps URL
        google_maps_url = f"https://www.google.com/maps?q={lat_str},{lon_str}"
        text_box.insert(tk.END, f"\nGoogle Maps URL: {google_maps_url}\n")

        # Open in Google Maps
        webbrowser.open(google_maps_url)
    except Exception as e:
        text_box.insert(tk.END, f"\nFailed to open Google Maps: {str(e)}\n")

def abrir_no_google_street_view():
    if latitude is None or longitude is None:
        text_box.insert(tk.END, "\nNo GPS coordinates available. Please select an image with GPS metadata.\n")
        return
    try:
        # Format latitude and longitude as strings
        lat_str = f"{latitude:.13f}"
        lon_str = f"{longitude:.13f}"

        # Generate Google Street View URL
        street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_str},{lon_str}&heading=-45&pitch=38&fov=80"
        text_box.insert(tk.END, f"\nGoogle Street View URL: {street_view_url}\n")

        # Open in Google Street View
        webbrowser.open(street_view_url)
    except Exception as e:
        text_box.insert(tk.END, f"\nFailed to open Google Street View: {str(e)}\n")

# Create GUI
root = tk.Tk()
root.title("ExifTool Metadata")
root.wm_state('zoomed')
root.geometry("1280x900")

# Botões
open_button = tk.Button(root, text="Open File", command=open_file, bg='#f7af07',font=("Arial", 12, "bold"))
open_button.pack(pady=5)

maps_button = tk.Button(root, text="Open in Google Maps", command=abrir_no_google_maps, bg='#00FF00',font=("Arial", 12, "bold"))
maps_button.pack(pady=5)

street_view_button = tk.Button(root, text="Open in Google Street View", command=abrir_no_google_street_view, bg='#07f7eb',font=("Arial", 12, "bold"))
street_view_button.pack(pady=5)

# Frame com Text e Scrollbar centralizados
frame = tk.Frame(root)
frame.pack(pady=10)
frame.pack_propagate(False)  # Impede o frame de se ajustar ao conteúdo

# Define tamanho fixo do frame
frame.config(width=1000, height=700)

# Centraliza o frame
frame.pack(anchor='center')

# Text box com tamanho fixo
text_box = tk.Text(frame, width=132, height=42, font=("Arial", 12))
text_box.grid(row=0, column=0, sticky="nsew")

# Scrollbar
scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_box.yview)
scrollbar.grid(row=0, column=1, sticky="ns")

# Conecta scrollbar ao Text
text_box.config(yscrollcommand=scrollbar.set)

# Permite que grid se expanda corretamente
frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

# Scrollbar
scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_box.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_box.config(yscrollcommand=scrollbar.set)

# Start GUI
root.mainloop()
