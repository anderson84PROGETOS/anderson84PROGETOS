import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import subprocess
import io
import webbrowser
import re
import mimetypes
import os
import tempfile

def baixar_imagem():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Por favor, digite uma URL.")
        return
    
    try:
        # Criar um arquivo temporário para salvar a imagem baixada com wget
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "temp_image")
        
        # Baixar a imagem usando wget
        subprocess.run(
            ['wget', '-O', temp_file, url],
            check=True,
            capture_output=True
        )

        # Determinar o formato original da imagem
        mime_type, _ = mimetypes.guess_type(temp_file)
        original_ext = mimetypes.guess_extension(mime_type, strict=False) if mime_type else '.png'
        original_format = original_ext.lstrip('.').upper() if original_ext else 'PNG'

        # Abrir a imagem com Pillow para exibição e salvamento
        img = Image.open(temp_file)
        mostrar_imagem_e_salvar(img, original_format, temp_file)

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Falha ao baixar imagem com wget:\n{e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao processar imagem:\n{e}")
    finally:
        # Limpar o arquivo temporário
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def abrir_imagem_local():
    file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.jpeg *.png *.tiff *.bmp *.webp")])
    if not file_path:
        return
    try:
        img = Image.open(file_path)
        mostrar_imagem(img)
        exibir_metadados(file_path)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir ou processar imagem:\n{e}")

def mostrar_imagem_e_salvar(img, original_format, temp_file):
    img_preview = img.copy()
    img_preview.thumbnail((300, 300))
    img_tk = ImageTk.PhotoImage(img_preview)
    img_label.config(image=img_tk)
    img_label.image = img_tk

    # Lista de formatos disponíveis para salvar
    filetypes = [
        ("PNG", "*.png"),
        
    ]

    # Incluir o formato original se for suportado
    if original_format.lower() in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp']:
        if original_format.lower() == 'jpeg':
            original_format = 'JPG'
        filetypes.append(("Original Format ({})".format(original_format), f"*.{original_format.lower()}"))

    # Abrir diálogo para escolher nome e formato
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=filetypes,
        title="Salvar imagem como"
    )
    if not file_path:
        messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para salvar.")
        return

    # Extrair a extensão do caminho escolhido
    ext = os.path.splitext(file_path)[1].lstrip('.').lower()
    if ext == 'jpg':
        ext = 'jpeg'
    elif ext == '':
        ext = 'png'  # Fallback para PNG se nenhuma extensão for especificada

    # Mapear extensões para formatos Pillow
    format_map = {
        'png': 'PNG',
        'jpeg': 'JPEG',
        'jpg': 'JPEG',
        'tiff': 'TIFF',
        'bmp': 'BMP',
        'webp': 'WEBP'
    }

    save_format = format_map.get(ext, 'PNG')  # Default para PNG se formato inválido

    try:
        # Se o formato escolhido for o original, copiar diretamente o arquivo baixado
        if save_format == original_format.upper():
            with open(temp_file, 'rb') as src, open(file_path, 'wb') as dst:
                dst.write(src.read())
        else:
            # Converter para RGB se necessário (JPEG e BMP não suportam RGBA)
            if save_format in ['JPEG', 'BMP'] and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(file_path, format=save_format)
        
        messagebox.showinfo("Sucesso", f"Imagem salva em:\n{file_path}")
        exibir_metadados(file_path)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar imagem:\n{e}")

def mostrar_imagem(img):
    img_preview = img.copy()
    img_preview.thumbnail((300, 300))
    img_tk = ImageTk.PhotoImage(img_preview)
    img_label.config(image=img_tk)
    img_label.image = img_tk

def exibir_metadados(caminho_imagem):
    try:
        resultado = subprocess.run(
            ['exiftool', caminho_imagem],
            capture_output=True,
            text=True
        )
        saida = resultado.stdout
        if not saida.strip():
            saida = "Nenhum metadado EXIF encontrado ou exiftool não retornou dados."

        # Extrair coordenadas em DMS e converter para decimal
        lat_dms, lat_ref = extrair_dms(saida, 'GPS Latitude')
        lon_dms, lon_ref = extrair_dms(saida, 'GPS Longitude')

        if lat_dms and lon_dms:
            lat_dec = dms_para_decimal(*lat_dms, lat_ref)
            lon_dec = dms_para_decimal(*lon_dms, lon_ref)

            gps_info_str = (
                f"GPS Latitude: {lat_dms}\n"
                f"GPS Longitude: {lon_dms}\n\n"
                f"GPS Latitude (decimal): {lat_dec}\n"
                f"GPS Longitude (decimal): {lon_dec}\n\n"
                f"Google Maps URL: https://www.google.com/maps?q={lat_dec},{lon_dec}\n"
                f"Street View URL: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_dec},{lon_dec}&heading=-45&pitch=38&fov=80\n"
            )

            nova_saida = gps_info_str + "\n" + saida
            meta_text.delete("1.0", tk.END)
            meta_text.insert(tk.END, nova_saida)

            btn_google_maps.config(state="normal")
            btn_google_street.config(state="normal")
            btn_google_maps.lat = lat_dec
            btn_google_maps.lon = lon_dec
            btn_google_street.lat = lat_dec
            btn_google_street.lon = lon_dec
        else:
            meta_text.delete("1.0", tk.END)
            meta_text.insert(tk.END, saida)
            btn_google_maps.config(state="disabled")
            btn_google_street.config(state="disabled")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao executar exiftool:\n{e}")

def extrair_dms(texto, chave):
    """
    Extrai DMS e referência (N/S/E/W) dos metadados.
    Retorna ((graus, minutos, segundos), ref) ou (None, None).
    """
    regex = rf'{chave}\s+:\s+(\d+)\s+deg\s+(\d+)\'\s+([\d.]+)"\s+([NSEW])'
    m = re.search(regex, texto)
    if m:
        graus = int(m.group(1))
        minutos = int(m.group(2))
        segundos = float(m.group(3))
        ref = m.group(4)
        return (graus, minutos, segundos), ref
    return None, None

def dms_para_decimal(graus, minutos, segundos, ref):
    dec = graus + minutos/60 + segundos/3600
    if ref in ['S', 'W']:
        dec = -dec
    return round(dec, 13)

def abrir_google_maps():
    lat = btn_google_maps.lat
    lon = btn_google_maps.lon
    url = f"https://www.google.com/maps?q={lat},{lon}"
    webbrowser.open(url)

def abrir_google_street_view():
    lat = btn_google_street.lat
    lon = btn_google_street.lon
    url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80"
    webbrowser.open(url)

root = tk.Tk()
root.geometry("1300x1200")
root.title("Baixar / Abrir Foto + Metadados EXIF (exiftool)")

tk.Label(root, text="Digite a URL da imagem").pack(pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.pack(padx=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

btn_baixar = tk.Button(btn_frame, text="Baixar Foto e Ver Metadados", command=baixar_imagem, bg="#36a303")
btn_baixar.pack(side="left", padx=5)

btn_abrir = tk.Button(btn_frame, text="Abrir Foto Local", command=abrir_imagem_local, bg="#054bfc")
btn_abrir.pack(side="left", padx=5)

btn_google_maps = tk.Button(btn_frame, text="Abrir no Google Maps", command=abrir_google_maps, state="disabled", bg="#05fc81")
btn_google_maps.pack(side="left", padx=5)

btn_google_street = tk.Button(btn_frame, text="Abrir no Street View", command=abrir_google_street_view, state="disabled", bg="#05e4fc")
btn_google_street.pack(side="left", padx=5)

img_label = tk.Label(root)
img_label.pack()

tk.Label(root, text="Metadados EXIF extraídos com exiftool").pack(pady=5)

frame_text = tk.Frame(root)
frame_text.pack(padx=10, pady=5, fill="both", expand=True)

scrollbar = tk.Scrollbar(frame_text)
scrollbar.pack(side="right", fill="y")

meta_text = tk.Text(frame_text, height=30, width=150, yscrollcommand=scrollbar.set)
meta_text.pack(pady=5)

scrollbar.config(command=meta_text.yview)

root.mainloop()
