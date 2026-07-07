import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import win32com.client
import webbrowser
from zoneinfo import ZoneInfo
import pypdf

# Dependências opcionais
try:
    from PIL import Image, ExifTags, ImageCms
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False
try:    
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

def get_brazil_time():
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime.now(tz)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def format_exif_date(date_str):
    if not date_str or not isinstance(date_str, str):
        return date_str
    try:
        date_str = date_str.strip()
        # Suporte a múltiplos formatos de data EXIF
        for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                continue
    except:
        pass
    return date_str


def get_gps_from_exif(file_path):
    if not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif or 34853 not in exif:
            return None
        gps_info = exif[34853]

        def to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = to_degrees(gps_info[2])
        if gps_info[1] == 'S': lat = -lat
        lon = to_degrees(gps_info[4])
        if gps_info[3] == 'W': lon = -lon
        return lat, lon
    except:
        return None


def get_image_metadata(file_path):
    """Extrai metadados detalhados de qualquer formato de imagem suportado pelo Pillow"""
    if not PIL_AVAILABLE:
        return {}
    
    metadata = {}
    try:
        with Image.open(file_path) as img:
            metadata['📐 Dimensões'] = f"{img.width} x {img.height} pixels"
            metadata['🎨 Modo'] = img.mode
            metadata['📁 Formato'] = img.format or "Desconhecido"
            
            # Informações ICC (perfil de cores)
            if hasattr(img, 'info') and img.info.get('icc_profile'):
                metadata['🌈 Perfil de Cores'] = "Presente (ICC)"
            
            # EXIF completo
            exif = img._getexif()
            if exif:
                for k, v in exif.items():
                    tag = ExifTags.TAGS.get(k, f"Tag_{k}")
                    value = str(v)
                    if any(date_tag in tag.lower() for date_tag in ["datetime", "date", "time"]):
                        value = format_exif_date(value)
                    metadata[f"📷 EXIF_{tag}"] = value
            
            # XMP / outros metadados (se disponíveis)
            if hasattr(img, 'info'):
                for key, value in img.info.items():
                    if key.lower() not in ['exif', 'icc_profile', 'dpi']:
                        if isinstance(value, (str, int, float)):
                            metadata[f"📋 INFO_{key}"] = str(value)
            
            # DPI
            if 'dpi' in img.info:
                metadata['📏 DPI'] = str(img.info['dpi'])
                
    except Exception as e:
        metadata['❌ Erro PIL'] = str(e)
    
    return metadata


def get_file_metadata(file_path):
    metadata = {}
    ext = os.path.splitext(file_path)[1].lower()

    metadata['🕒 Análise'] = get_brazil_time()
    metadata['📂 Caminho'] = file_path
    metadata['📄 Nome'] = os.path.basename(file_path)
    metadata['📎 Extensão'] = ext.upper()
    metadata['💾 Tamanho'] = f"{os.path.getsize(file_path):,} bytes"
    metadata['📅 Criado'] = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%d/%m/%Y %H:%M:%S')
    metadata['📅 Modificado'] = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%d/%m/%Y %H:%M:%S')

    # Metadados Windows (detalhado)
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.Namespace(os.path.dirname(file_path))
        file_item = folder.ParseName(os.path.basename(file_path))
        for i in range(350):
            try:
                name = folder.GetDetailsOf(None, i)
                if name and name.strip():
                    value = folder.GetDetailsOf(file_item, i)
                    if value:
                        traducao = {
                            "Date created": "📅 Data de criação",
                            "Date modified": "📅 Data de modificação",
                            "Size": "💾 Tamanho",
                            "Author": "👤 Autor",
                            "Title": "📖 Título",
                            "Subject": "📝 Assunto",
                            "Comments": "💬 Comentários",
                            "Camera model": "📷 Modelo da Câmera",
                            "Date taken": "📸 Data da Foto",
                        }.get(name.strip(), name.strip())
                        metadata[traducao] = value
            except:
                continue
    except:
        pass

    # Metadados específicos de imagens (melhorado para todos os formatos)
    image_meta = {}
    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.bmp', '.gif', '.heic', '.heif']:
        image_meta = get_image_metadata(file_path)
        metadata.update(image_meta)

    # Geo Localização
    gps = get_gps_from_exif(file_path)
    if gps:
        lat, lon = gps
        metadata['🌍 Latitude'] = f"{lat:.6f}"
        metadata['🌍 Longitude'] = f"{lon:.6f}"
        metadata['🗺️ Google Maps'] = f"https://www.google.com/maps?q={lat},{lon}"
    else:
        metadata['🌍 GPS'] = "Não encontrado"

    # Metadados PDF (melhorado)
    if PDF_AVAILABLE and ext == '.pdf':
        try:
            reader = pypdf.PdfReader(file_path)
            metadata['📑 Páginas'] = len(reader.pages)
            if reader.metadata:
                for key, value in reader.metadata.items():
                    metadata[f"📕 PDF_{key}"] = str(value)
        except:
            pass

    return metadata


# ==================== INTERFACE ====================
root = tk.Tk()
root.title("METADADOS EXTRACTOR")
root.configure(bg='black')
root.geometry("1100x780")
root.state('zoomed')

tk.Label(root, text="═ METADADOS EXTRACTOR ═", 
         bg='black', fg='#00FF00', font=("Courier", 18, "bold")).pack(pady=15)

btn_frame = tk.Frame(root, bg='black')
btn_frame.pack(pady=20)

select_btn = tk.Button(btn_frame, text="SELECIONAR ARQUIVO", 
                       command=lambda: display_metadata(),
                       bg="#0FC70F", fg="#0A0A0A", font=("Courier", 12, "bold"), 
                       width=25, height=2, relief="ridge")
select_btn.pack(side=tk.LEFT, padx=20)

save_btn = tk.Button(btn_frame, text="SALVAR METADADOS", 
                     command=lambda: save_metadata(),
                     bg="#EE8309", fg="#080808", font=("Courier", 12, "bold"), 
                     width=25, height=2, relief="ridge")
save_btn.pack(side=tk.LEFT, padx=20)

map_btn = tk.Button(btn_frame, text="🗺️ ABRIR GOOGLE MAPS", 
                    command=lambda: open_map(), state='disabled',
                    bg="#06CCCC", fg="#030303", font=("Courier", 12, "bold"), 
                    width=25, height=2, relief="ridge")
map_btn.pack(side=tk.LEFT, padx=20)

frame = tk.Frame(root, bg='black')

frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

scroll = tk.Scrollbar(frame)
scroll.pack(side=tk.RIGHT, fill=tk.Y)

text_area = tk.Text(frame, bg="#0a0a0a", fg="#00FF41", font=("Consolas", 12), wrap=tk.WORD, yscrollcommand=scroll.set)
text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll.config(command=text_area.yview)

tk.Label(root, text="Suporte Total: .jpg .jpeg .png .webp .tiff .bmp .gif .pdf .docx .mp4 .exe ... e MUITO MAIS", 
         bg='black', fg='#00AA00', font=("Courier", 9)).pack(pady=8)

current_metadata = None
current_file = None

def display_metadata():
    global current_metadata, current_file
    path = filedialog.askopenfilename(title="Escolha o arquivo", 
                                     filetypes=[("Todos os arquivos", "*.*")])
    if not path:
        return
   
    current_metadata = get_file_metadata(path)
    current_file = path
   
    text_area.delete(1.0, tk.END)
    
    # Cabeçalho
    text_area.insert(tk.END, f"METADATA REPORT - {get_brazil_time()}\n\n")
    text_area.insert(tk.END, f"Arquivo: {current_file}\n\n")
    text_area.insert(tk.END, "=" * 90 + "\n\n")
    
    # Conteúdo formatado
    for k, v in sorted(current_metadata.items()):
        text_area.insert(tk.END, f"{k}:\n\n")
        text_area.insert(tk.END, f"   {v}\n\n")
        text_area.insert(tk.END, "-" * 90 + "\n\n")
    
    # Ativar botão Google Maps
    has_gps = any("Google Maps" in key for key in current_metadata.keys())
    map_btn.config(state='normal' if has_gps else 'disabled')


def open_map():
    global current_metadata
    if not current_metadata:
        messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
        return
    
    for key, value in current_metadata.items():
        if "Google Maps" in key and isinstance(value, str) and value.startswith("http"):
            webbrowser.open(value)
            return
    
    messagebox.showinfo("GPS", "Nenhuma localização GPS encontrada neste arquivo.")


def save_metadata():
    global current_metadata, current_file
    if not current_metadata:
        messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
        return
   
    save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Arquivo de texto", "*.txt")])
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"METADATA REPORT - {get_brazil_time()}\n\n")
            f.write(f"Arquivo: {current_file}\n")
            f.write("=" * 90 + "\n\n")
            
            for k, v in sorted(current_metadata.items()):
                f.write(f"{k}:\n\n")
                f.write(f"   {v}\n\n")
                f.write("-" * 90 + "\n\n")
        
        messagebox.showinfo("Salvo", f"Metadados salvos com sucesso\n\n{save_path}")


root.mainloop()
