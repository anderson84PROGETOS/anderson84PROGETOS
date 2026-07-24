#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExifTool Master BR — Leitor Universal + Editor EXIF + VirusTotal
Versão: 3.2.1 (Hex Dump com seletor de limite)
Idioma: Português (Brasil)
Formato de Data: DD/MM/AAAA
"""

import os
import sys
import json
import shutil
import struct
import hashlib
import subprocess
import platform
import webbrowser
import re
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS

try:
    import piexif
    TEM_PIEXIF = True
except ImportError:
    TEM_PIEXIF = False

try:
    import magic
    TEM_MAGIC = True
except ImportError:
    TEM_MAGIC = False

try:
    import olefile
    TEM_OLE = True
except ImportError:
    TEM_OLE = False

try:
    import zipfile
    TEM_ZIP = True
except ImportError:
    TEM_ZIP = False


# ═══════════════════════════════════════════════════════
# TRADUÇÕES PT-BR
# ═══════════════════════════════════════════════════════

TRADUCAO_TAGS = {
    "ImageWidth": "Largura da Imagem",
    "ImageLength": "Altura da Imagem",
    "BitsPerSample": "Bits por Amostra",
    "Compression": "Compressão",
    "PhotometricInterpretation": "Interpretação Fotométrica",
    "Orientation": "Orientação",
    "SamplesPerPixel": "Amostras por Pixel",
    "Make": "Fabricante da Câmera",
    "Model": "Modelo da Câmera",
    "Software": "Software",
    "DateTime": "Data e Hora",
    "Artist": "Artista",
    "Copyright": "Direitos Autorais",
    "DateTimeOriginal": "Data e Hora Original",
    "DateTimeDigitized": "Data e Hora Digitalização",
    "ImageDescription": "Descrição da Imagem",
    "ExposureTime": "Tempo de Exposição",
    "FNumber": "Número F (Abertura)",
    "ExposureProgram": "Programa de Exposição",
    "ISOSpeedRatings": "ISO",
    "ShutterSpeedValue": "Velocidade do Obturador",
    "ApertureValue": "Valor de Abertura",
    "BrightnessValue": "Valor de Brilho",
    "ExposureBiasValue": "Compensação de Exposição",
    "MaxApertureValue": "Abertura Máxima",
    "SubjectDistance": "Distância do Assunto",
    "MeteringMode": "Modo de Medição",
    "LightSource": "Fonte de Luz",
    "Flash": "Flash",
    "FocalLength": "Distância Focal",
    "FocalLengthIn35mmFilm": "Distância Focal (35mm)",
    "DigitalZoomRatio": "Fator de Zoom Digital",
    "SceneCaptureType": "Tipo de Captura de Cena",
    "GainControl": "Controle de Ganho",
    "Contrast": "Contraste",
    "Saturation": "Saturação",
    "Sharpness": "Nitidez",
    "ColorSpace": "Espaço de Cor",
    "ExposureMode": "Modo de Exposição",
    "WhiteBalance": "Balanço de Branco",
    "UserComment": "Comentário do Usuário",
    "GPSInfo": "Informações GPS",
    "GPSLatitudeRef": "Referência de Latitude",
    "GPSLatitude": "Latitude",
    "GPSLongitudeRef": "Referência de Longitude",
    "GPSLongitude": "Longitude",
    "GPSAltitudeRef": "Referência de Altitude",
    "GPSAltitude": "Altitude",
    "GPSTimeStamp": "Carimbo de Hora GPS",
    "GPSDateStamp": "Carimbo de Data GPS",
    "GPSMapDatum": "Datum do Mapa",
    "GPSProcessingMethod": "Método de Processamento",
    "GPSHPositioningError": "Erro de Posicionamento Horizontal",
    "CameraOwnerName": "Nome do Proprietário",
    "BodySerialNumber": "Número de Série do Corpo",
    "LensSpecification": "Especificação da Lente",
    "LensMake": "Fabricante da Lente",
    "LensModel": "Modelo da Lente",
    "LensSerialNumber": "Número de Série da Lente",
    
    "FILE_NAME": "Nome do Arquivo",
    "FILE_SIZE": "Tamanho do Arquivo",
    "FILE_TYPE": "Tipo do Arquivo",
    "FILE_MIME": "Tipo MIME",
    "FILE_EXT": "Extensão",
    "FILE_CREATED": "Data de Criação",
    "FILE_MODIFIED": "Data de Modificação",
    "FILE_ACCESSED": "Último Acesso",
    "FILE_PERMISSIONS": "Permissões",
    "FILE_OWNER": "Proprietário",
    "FILE_MD5": "MD5",
    "FILE_SHA1": "SHA1",
    "FILE_SHA256": "SHA256",
    "FILE_MAGIC": "Assinatura Mágica",
    "IMAGE_WIDTH": "Largura",
    "IMAGE_HEIGHT": "Altura",
    "IMAGE_FORMAT": "Formato",
    "IMAGE_MODE": "Modo de Cor",
    
    "VIDEO_CODEC": "Codec de Vídeo",
    "VIDEO_WIDTH": "Largura do Vídeo",
    "VIDEO_HEIGHT": "Altura do Vídeo",
    "VIDEO_FPS": "FPS (Quadros por Segundo)",
    "VIDEO_BITRATE": "Taxa de Bits (Bitrate)",
    "VIDEO_DURATION": "Duração",
    "VIDEO_FORMAT": "Formato de Vídeo",
    "VIDEO_ASPECT": "Proporção (Aspect Ratio)",
    "AUDIO_CODEC": "Codec de Áudio",
    "AUDIO_SAMPLE_RATE": "Taxa de Amostragem",
    "AUDIO_CHANNELS": "Canais de Áudio",
    "AUDIO_BITRATE": "Bitrate de Áudio",
    "AUDIO_LANGUAGE": "Idioma do Áudio",
    
    "PE_MACHINE": "Arquitetura (Machine)",
    "PE_SUBSYSTEM": "Subsistema",
    "PE_ENTRY_POINT": "Ponto de Entrada",
    "PE_IMAGE_BASE": "Base da Imagem",
    "PE_LINKER_VERSION": "Versão do Linker",
    "PE_OS_VERSION": "Versão mínima do SO",
    "PE_IMAGE_VERSION": "Versão da Imagem",
    "PE_SUBSYSTEM_VERSION": "Versão do Subsistema",
    "PE_SECTIONS": "Seções",
    "PE_COMPILED": "Data de Compilação",
    "PE_COMPANY": "Empresa",
    "PE_DESCRIPTION": "Descrição",
    "PE_PRODUCT": "Produto",
    "PE_VERSION": "Versão",
    "PE_COPYRIGHT": "Direitos Autorais",
    "PE_ORIGINAL_NAME": "Nome Original",
    "PE_INTERNAL_NAME": "Nome Interno",
    "PE_ARCH": "Arquitetura",
    
    "SCRIPT_LANGUAGE": "Linguagem",
    "SCRIPT_LINES": "Linhas de Código",
    "SCRIPT_SIZE": "Tamanho do Código",
    "SCRIPT_ENCODING": "Codificação",
    "SCRIPT_SHEBANG": "Shebang",
    
    "PDF_VERSION": "Versão PDF",
    "PDF_PAGES": "Páginas",
    "PDF_TITLE": "Título",
    "PDF_AUTHOR": "Autor",
    "PDF_SUBJECT": "Assunto",
    "PDF_KEYWORDS": "Palavras-chave",
    "PDF_CREATOR": "Criador",
    "PDF_PRODUCER": "Produtor",
    "PDF_ENCRYPTED": "Criptografado",
    "PDF_EMBEDDED_FILES": "Arquivos Incorporados",
    
    "ARCHIVE_FORMAT": "Formato do Arquivo",
    "ARCHIVE_FILES": "Arquivos Internos",
    "ARCHIVE_SIZE": "Tamanho Compactado",
    "ARCHIVE_UNCOMPRESSED": "Tamanho Original",
    "ARCHIVE_COMPRESSION": "Compressão",
    "ARCHIVE_COMMENT": "Comentário",
    
    "AUDIO_ALBUM": "Álbum",
    "AUDIO_ARTIST": "Artista",
    "AUDIO_TITLE": "Título",
    "AUDIO_YEAR": "Ano",
    "AUDIO_GENRE": "Gênero",
    "AUDIO_TRACK": "Faixa",
    "AUDIO_DURATION": "Duração",
    "AUDIO_FORMAT": "Formato",
}

TRADUCAO_VALORES = {
    "Orientation": {1:"Normal", 2:"Espelhada horizontalmente", 3:"Rotacionada 180°",
                    4:"Espelhada verticalmente", 5:"Rot. 90° + espelhada horizontal",
                    6:"Rotacionada 90°", 7:"Rot. 90° + espelhada vertical", 8:"Rotacionada 270°"},
    "Flash": {0:"Flash não disparou", 1:"Flash disparou",
              0x05:"Flash disparou, luz de retorno não detectada",
              0x07:"Flash disparou, luz de retorno detectada",
              0x09:"Flash disparou, modo obrigatório",
              0x0D:"Flash obrigatório, retorno não detectado",
              0x0F:"Flash obrigatório, retorno detectado",
              0x10:"Flash não disparou, modo compulsório",
              0x18:"Flash não disparou, modo automático",
              0x19:"Flash disparou, modo automático",
              0x1D:"Flash automático, retorno não detectado",
              0x1F:"Flash automático, retorno detectado",
              0x20:"Sem função de flash"},
    "ExposureProgram": {0:"Não definido", 1:"Manual", 2:"Programa normal",
                        3:"Prioridade de abertura", 4:"Prioridade de obturador",
                        5:"Criativo", 6:"Ação", 7:"Retrato", 8:"Paisagem"},
    "MeteringMode": {0:"Desconhecido", 1:"Média", 2:"Média ponderada ao centro",
                     3:"Ponto", 4:"Multiponto", 5:"Padrão"},
}

NOME_TIPO = {"imagem":"📷 Imagem","video":"🎬 Vídeo","audio":"🎵 Áudio",
             "executavel":"⚙️ Executável","script":"📜 Script",
             "documento":"📄 Documento","compactado":"🗜️ Compactado","outro":"📦 Outro"}

TIPOS_ARQUIVO = {
    ".jpg":"imagem",".jpeg":"imagem",".png":"imagem",".gif":"imagem",".bmp":"imagem",
    ".tiff":"imagem",".tif":"imagem",".webp":"imagem",".ico":"imagem",".heic":"imagem",
    ".heif":"imagem",".svg":"imagem",".raw":"imagem",".cr2":"imagem",".nef":"imagem",
    ".arw":"imagem",".dng":"imagem",
    ".mp4":"video",".avi":"video",".mkv":"video",".mov":"video",".wmv":"video",
    ".flv":"video",".webm":"video",".m4v":"video",".mpg":"video",".mpeg":"video",
    ".3gp":"video",".ts":"video",".ogv":"video",
    ".mp3":"audio",".wav":"audio",".flac":"audio",".aac":"audio",".ogg":"audio",
    ".wma":"audio",".m4a":"audio",".opus":"audio",
    ".exe":"executavel",".dll":"executavel",".sys":"executavel",".ocx":"executavel",
    ".scr":"executavel",".cpl":"executavel",".drv":"executavel",
    ".py":"script",".js":"script",".bat":"script",".ps1":"script",".sh":"script",
    ".vbs":"script",".php":"script",".pl":"script",".rb":"script",".lua":"script",
    ".go":"script",".rs":"script",".java":"script",".c":"script",".cpp":"script",
    ".h":"script",".cs":"script",".sql":"script",".html":"script",".css":"script",
    ".xml":"script",".json":"script",".yaml":"script",".yml":"script",".ini":"script",
    ".cfg":"script",".conf":"script",".toml":"script",".md":"script",
    ".pdf":"documento",".doc":"documento",".docx":"documento",".xls":"documento",
    ".xlsx":"documento",".ppt":"documento",".pptx":"documento",".odt":"documento",
    ".ods":"documento",".odp":"documento",".rtf":"documento",".txt":"documento",
    ".csv":"documento",".epub":"documento",
    ".zip":"compactado",".rar":"compactado",".7z":"compactado",".tar":"compactado",
    ".gz":"compactado",".bz2":"compactado",".xz":"compactado",".zst":"compactado",".iso":"compactado",
}


# ═══════════════════════════════════════════════════════
# ANALISADORES
# ═══════════════════════════════════════════════════════

class AnalisadorArquivo:
    @staticmethod
    def info_basica(caminho):
        dados = {}
        p = Path(caminho)
        dados["FILE_NAME"] = p.name
        dados["FILE_EXT"] = p.suffix.lower()
        dados["FILE_MIME"] = AnalisadorArquivo._detectar_mime(caminho, p.suffix.lower())
        dados["FILE_MAGIC"] = AnalisadorArquivo._magic_bytes(caminho)
        try:
            stat = os.stat(caminho)
            dados["FILE_SIZE"] = AnalisadorArquivo._formatar_tamanho(stat.st_size)
            dados["FILE_SIZE_BYTES"] = stat.st_size
            dados["FILE_CREATED"] = AnalisadorArquivo._formatar_data(stat.st_ctime)
            dados["FILE_MODIFIED"] = AnalisadorArquivo._formatar_data(stat.st_mtime)
            dados["FILE_ACCESSED"] = AnalisadorArquivo._formatar_data(stat.st_atime)
        except: pass
        try:
            with open(caminho, "rb") as f:
                data = f.read()
                dados["FILE_MD5"] = hashlib.md5(data).hexdigest()
                dados["FILE_SHA1"] = hashlib.sha1(data).hexdigest()
                dados["FILE_SHA256"] = hashlib.sha256(data).hexdigest()
        except: pass
        return dados

    @staticmethod
    def _detectar_mime(caminho, ext):
        if TEM_MAGIC:
            try:
                m = magic.Magic(mime=True)
                return m.from_file(caminho)
            except: pass
        mapa = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
                ".gif":"image/gif",".bmp":"image/bmp",".webp":"image/webp",
                ".mp4":"video/mp4",".avi":"video/x-msvideo",".mkv":"video/x-matroska",
                ".mov":"video/quicktime",".mp3":"audio/mpeg",".wav":"audio/wav",
                ".pdf":"application/pdf",".exe":"application/x-msdownload",
                ".dll":"application/x-msdownload",".zip":"application/zip",
                ".rar":"application/vnd.rar",".txt":"text/plain",".py":"text/x-python",
                ".html":"text/html",".json":"application/json"}
        return mapa.get(ext, "application/octet-stream")

    @staticmethod
    def _magic_bytes(caminho):
        ass = {b"\xff\xd8\xff":"JPEG",b"\x89PNG\r\n\x1a\n":"PNG",
               b"GIF87a":"GIF 87a",b"GIF89a":"GIF 89a",b"BM":"BMP",
               b"\x00\x00\x00 ftyp":"MP4/M4V",b"\x1a\x45\xdf\xa3":"MKV/WebM",
               b"\x49\x44\x33":"MP3 (ID3)",b"\xff\xfb":"MP3",b"\xff\xf3":"MP3",
               b"PK\x03\x04":"ZIP/DOCX/XLSX",b"Rar!\x1a\x07":"RAR",
               b"\x37\x7a\xbc\xaf\x27\x1c":"7z",b"%PDF":"PDF",
               b"MZ":"EXE/DLL (PE)",b"\x7fELF":"ELF (Linux)"}
        try:
            with open(caminho,"rb") as f:
                cab = f.read(16)
                for sig,nome in ass.items():
                    if cab.startswith(sig): return nome
                return "Desconhecida"
        except: return "Erro"

    @staticmethod
    def _formatar_tamanho(tam):
        if tam < 1024: return f"{tam} B"
        elif tam < 1024**2: return f"{tam/1024:.1f} KB"
        elif tam < 1024**3: return f"{tam/1024**2:.1f} MB"
        else: return f"{tam/1024**3:.2f} GB"

    @staticmethod
    def _formatar_data(ts):
        try: return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")
        except: return str(ts)


class AnalisadorImagem:
    @staticmethod
    def analisar(caminho):
        dados = {}
        try:
            img = Image.open(caminho)
            dados["IMAGE_WIDTH"] = img.width
            dados["IMAGE_HEIGHT"] = img.height
            dados["IMAGE_FORMAT"] = img.format
            dados["IMAGE_MODE"] = img.mode
            exif_raw = img._getexif()
            if exif_raw:
                for tid, valor in exif_raw.items():
                    nome_tag = TAGS.get(tid, f"Tag_{tid}")
                    if nome_tag == "GPSInfo":
                        gps = {}
                        for gtid, gvalor in valor.items():
                            gps[GPSTAGS.get(gtid, f"GPS_{gtid}")] = gvalor
                        dados["GPSInfo"] = gps
                        dados = {**dados, **AnalisadorImagem._processar_gps(gps)}
                    elif nome_tag == "UserComment" and isinstance(valor, bytes):
                        try: dados[nome_tag] = valor.decode("utf-8", errors="ignore")
                        except: dados[nome_tag] = str(valor)
                    else: dados[nome_tag] = valor
            img.close()
        except: pass
        return dados

    @staticmethod
    def _processar_gps(gps):
        dados = {}
        try:
            if "GPSLatitude" in gps and "GPSLatitudeRef" in gps:
                lat = AnalisadorImagem._dm_a_decimal(gps["GPSLatitude"])
                if str(gps["GPSLatitudeRef"]).upper() == "S": lat = -lat
                dados["GPSLatitude"] = f"{lat:.6f}"
                dados["GPSLatitudeDecimal"] = lat
            if "GPSLongitude" in gps and "GPSLongitudeRef" in gps:
                lon = AnalisadorImagem._dm_a_decimal(gps["GPSLongitude"])
                if str(gps["GPSLongitudeRef"]).upper() == "W": lon = -lon
                dados["GPSLongitude"] = f"{lon:.6f}"
                dados["GPSLongitudeDecimal"] = lon
            if "GPSAltitude" in gps:
                alt = gps["GPSAltitude"]
                if isinstance(alt, tuple) and len(alt)==2 and alt[1]!=0:
                    dados["GPSAltitude"] = f"{alt[0]/alt[1]:.1f} m"
                elif isinstance(alt,(int,float)):
                    dados["GPSAltitude"] = f"{float(alt):.1f} m"
            if "GPSDateStamp" in gps:
                dados["GPSDateStamp"] = str(gps["GPSDateStamp"])
        except: pass
        return dados

    @staticmethod
    def _dm_a_decimal(dados):
        try:
            if isinstance(dados[0], tuple):
                return float(dados[0][0])/dados[0][1] + float(dados[1][0])/dados[1][1]/60 + float(dados[2][0])/dados[2][1]/3600
        except: pass
        try:
            if len(dados)==3: return dados[0] + dados[1]/60.0 + dados[2]/3600.0
        except: pass
        return 0


class AnalisadorVideo:
    @staticmethod
    def analisar(caminho):
        dados = {}
        try:
            cmd = ["ffprobe","-v","quiet","-print_format","json",
                   "-show_format","-show_streams",caminho]
            r = subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            if r.returncode==0:
                info = json.loads(r.stdout)
                if "format" in info:
                    fmt = info["format"]
                    dados["VIDEO_FORMAT"] = fmt.get("format_name","---")
                    dur = fmt.get("duration","0")
                    try:
                        seg = float(dur)
                        h,re = divmod(seg,3600); m,s = divmod(re,60)
                        dados["VIDEO_DURATION"] = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                    except: dados["VIDEO_DURATION"] = dur
                    bitrate = fmt.get("bit_rate","0")
                    try: dados["VIDEO_BITRATE"] = f"{int(bitrate)//1000} kbps"
                    except: dados["VIDEO_BITRATE"] = bitrate
                if "streams" in info:
                    for s in info["streams"]:
                        ct = s.get("codec_type","")
                        if ct=="video":
                            dados["VIDEO_CODEC"] = s.get("codec_name","---")
                            dados["VIDEO_WIDTH"] = s.get("width","---")
                            dados["VIDEO_HEIGHT"] = s.get("height","---")
                            rf = s.get("r_frame_rate","0/0")
                            try: n,d = rf.split("/"); dados["VIDEO_FPS"] = f"{float(n)/float(d):.2f}"
                            except: dados["VIDEO_FPS"] = rf
                            if "display_aspect_ratio" in s: dados["VIDEO_ASPECT"] = s["display_aspect_ratio"]
                        elif ct=="audio":
                            if "AUDIO_CODEC" not in dados: dados["AUDIO_CODEC"] = s.get("codec_name","---")
                            dados["AUDIO_SAMPLE_RATE"] = s.get("sample_rate","---")
                            dados["AUDIO_CHANNELS"] = f"{s.get('channels','---')} canais"
        except FileNotFoundError:
            dados["VIDEO_DURATION"] = "ffprobe não encontrado (instale ffmpeg)"
        except: pass
        return dados


class AnalisadorExecutavel:
    @staticmethod
    def analisar(caminho):
        dados = {}
        try:
            with open(caminho,"rb") as f:
                if f.read(2)!=b"MZ": return dados
                f.seek(0x3C)
                pe_off = struct.unpack("<I",f.read(4))[0]
                f.seek(pe_off)
                if f.read(4)!=b"PE\x00\x00": return dados
                machine = struct.unpack("<H",f.read(2))[0]
                maq = {0x14c:"x86 (32 bits)",0x8664:"x64 (64 bits)",0x1c4:"ARMv7",
                       0xaa64:"ARM64",0x1c0:"ARM v4/v5",0x200:"Itanium"}
                dados["PE_MACHINE"] = maq.get(machine,f"0x{machine:04X}")
                dados["PE_ARCH"] = "x64" if machine==0x8664 else "x86" if machine==0x14c else f"0x{machine:04X}"
                dados["PE_SECTIONS"] = struct.unpack("<H",f.read(2))[0]
                ts = struct.unpack("<I",f.read(4))[0]
                try: dados["PE_COMPILED"] = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")
                except: dados["PE_COMPILED"] = str(ts)
        except: pass
        return dados


class AnalisadorScript:
    @staticmethod
    def analisar(caminho):
        dados = {}
        ext = Path(caminho).suffix.lower()
        langs = {".py":"Python",".js":"JavaScript",".bat":"Batch",".ps1":"PowerShell",
                 ".sh":"Shell",".vbs":"VBScript",".php":"PHP",".pl":"Perl",".rb":"Ruby",
                 ".lua":"Lua",".go":"Go",".rs":"Rust",".java":"Java",".c":"C",".cpp":"C++",
                 ".h":"C/C++",".cs":"C#",".html":"HTML",".css":"CSS",".json":"JSON",
                 ".xml":"XML",".yaml":"YAML",".sql":"SQL",".md":"Markdown"}
        dados["SCRIPT_LANGUAGE"] = langs.get(ext,"Texto")
        try:
            with open(caminho,"r",encoding="utf-8",errors="replace") as f:
                c = f.read()
                dados["SCRIPT_LINES"] = len(c.splitlines())
                dados["SCRIPT_SIZE"] = f"{len(c)} chars"
                if c.startswith("#!"): dados["SCRIPT_SHEBANG"] = c.split("\n")[0]
        except: pass
        return dados


class AnalisadorDocumento:
    @staticmethod
    def analisar(caminho):
        dados = {}
        ext = Path(caminho).suffix.lower()
        if ext==".pdf":
            try:
                with open(caminho,"rb") as f:
                    conteudo = f.read()
                m = re.search(rb"%PDF-(\d+\.\d+)",conteudo)
                if m: dados["PDF_VERSION"] = m.group(1).decode()
                for chave,nome in [(b"/Title","PDF_TITLE"),(b"/Author","PDF_AUTHOR"),
                                    (b"/Subject","PDF_SUBJECT"),(b"/Keywords","PDF_KEYWORDS"),
                                    (b"/Creator","PDF_CREATOR"),(b"/Producer","PDF_PRODUCER")]:
                    r = re.findall(chave+rb"\s*\(([^)]*)\)",conteudo)
                    if r: dados[nome] = r[0].decode("latin-1",errors="replace")
                pg = re.findall(rb"/Type\s*/Page[^s]",conteudo)
                dados["PDF_PAGES"] = len(pg) if pg else "---"
                dados["PDF_ENCRYPTED"] = "Sim" if b"/Encrypt" in conteudo else "Não"
            except: pass
        return dados


class AnalisadorCompactado:
    @staticmethod
    def analisar(caminho):
        dados = {}
        ext = Path(caminho).suffix.lower()
        try:
            if ext==".zip" and TEM_ZIP:
                with zipfile.ZipFile(caminho,"r") as z:
                    info = z.infolist()
                    dados["ARCHIVE_FORMAT"] = "ZIP"
                    dados["ARCHIVE_FILES"] = len(info)
                    total_orig = sum(f.file_size for f in info)
                    total_comp = sum(f.compress_size for f in info)
                    dados["ARCHIVE_UNCOMPRESSED"] = AnalisadorArquivo._formatar_tamanho(total_orig)
                    dados["ARCHIVE_SIZE"] = AnalisadorArquivo._formatar_tamanho(total_comp)
                    if total_orig>0:
                        dados["ARCHIVE_COMPRESSION"] = f"{(1-total_comp/total_orig)*100:.1f}%"
        except:
            dados["ARCHIVE_FORMAT"] = ext.upper()
        return dados


# ═══════════════════════════════════════════════════════
# INTERFACE GRÁFICA
# ═══════════════════════════════════════════════════════

class ExifToolMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 ExifTool 📷 EXIF  📄 Metadados 🔢 Hex Dump  🔐 Hashes 🦠 VirusTotal 📊 Relatórios 📂 Comparação de arquivos 📍 GPS ✏️ Editor EXIF")

        self.root.geometry("1200x780")
        self.root.state("zoomed")
        self.root.minsize(900, 600)
        
        self.caminho_arquivo = None
        self.tipo_arquivo = None
        self.metadados = {}
        self.coordenadas_mapa = None
        self.photo = None
        self.cor_destaque = "#09f344"
        
        # Atributo para o widget de texto da comparação (inicializa como None)
        self.text_comparacao = None
        
        self.icones = {"imagem":"📷","video":"🎬","audio":"🎵",
                       "executavel":"⚙️","script":"📜","documento":"📄",
                       "compactado":"🗜️","outro":"📦"}
        
        # ════════ VALOR PADRÃO DO HEX DUMP ════════
        # 1 MB
        self.HEX_MAX_BYTES = 1 * 1024 * 1024
        
        # Cores para Hex Dump
        self.hex_bg = "#1e1e1e"
        self.hex_offset = "#6a9955"
        self.hex_bytes = "#4ec9b0"
        self.hex_ascii = "#d69d85"
        self.hex_header = "#569cd6"
        
        self._construir_interface()
        self.status("✅ Pronto! Abra qualquer arquivo para começar.")
    
    def _construir_interface(self):
        # Barra decorativa
        self.barra_menu = tk.Frame(self.root, bg=self.cor_destaque, height=4)
        self.barra_menu.pack(fill=tk.X)
        
        # Toolbar
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill=tk.X, padx=5, pady=(5,0))
        ttk.Button(self.toolbar,text="📂 Abrir",command=self.abrir_arquivo_dialog).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="🔍 Comparar",command=self.comparar_arquivos).pack(side=tk.LEFT,padx=2)
        ttk.Separator(self.toolbar,orient=tk.VERTICAL).pack(side=tk.LEFT,padx=5,fill=tk.Y)
        ttk.Button(self.toolbar,text="📋 Copiar Visão",command=self.copiar_tudo_visao).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="🔐 Copiar SHA256",command=self.copiar_hash).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="🔍 VirusTotal",command=self.abrir_virustotal).pack(side=tk.LEFT,padx=2)
        ttk.Separator(self.toolbar,orient=tk.VERTICAL).pack(side=tk.LEFT,padx=5,fill=tk.Y)
        ttk.Button(self.toolbar,text="📝 Relatório",command=self.gerar_relatorio).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="💾 Exportar JSON",command=self.exportar_json).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="📂 Abrir Pasta",command=self.abrir_local_pasta).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="💾 Copiar Arquivo",command=self.salvar_copia).pack(side=tk.LEFT,padx=2)
        ttk.Separator(self.toolbar,orient=tk.VERTICAL).pack(side=tk.LEFT,padx=5,fill=tk.Y)
        ttk.Button(self.toolbar,text="🎨 Cor",command=self.personalizar_cores).pack(side=tk.LEFT,padx=2)
        ttk.Button(self.toolbar,text="ℹ️ Sobre",command=self.mostrar_sobre).pack(side=tk.LEFT,padx=2)
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH,expand=True,padx=5,pady=5)
        
        self.aba_visao = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_visao,text="📋 Visão Geral")
        self._construir_aba_visao()
        
        self.aba_metadados = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_metadados,text="📊 Metadados")
        self._construir_aba_metadados()
        
        self.aba_gps = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_gps,text="📍 GPS")
        self._construir_aba_gps()
        
        self.aba_hex = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_hex,text="🔢 Hex Dump")
        self._construir_aba_hex()
        
        self.aba_preview = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_preview,text="👁️ Preview")
        self._construir_aba_preview()
        
        self.aba_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_editor,text="✏️ Editor EXIF")
        self._construir_aba_editor()
        
        self.status_bar = ttk.Label(self.root,relief=tk.SUNKEN,anchor=tk.W,padding=(5,2))
        self.status_bar.pack(fill=tk.X,side=tk.BOTTOM)
    
    # ═══ ABA 1: VISÃO GERAL ═══
    def _construir_aba_visao(self):
        frame_filtro = ttk.Frame(self.aba_visao)
        frame_filtro.pack(fill=tk.X, pady=(5,0))
        ttk.Label(frame_filtro, text="🔍 Filtrar:").pack(side=tk.LEFT, padx=5)
        self.entry_filtro_visao = ttk.Entry(frame_filtro)
        self.entry_filtro_visao.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_filtro_visao.insert(0, "🔍 Filtrar...")
        self.entry_filtro_visao.bind("<FocusIn>", lambda e: self.entry_filtro_visao.delete(0,tk.END) if self.entry_filtro_visao.get()=="🔍 Filtrar..." else None)
        self.entry_filtro_visao.bind("<KeyRelease>", self.filtrar_visao_geral)
        ttk.Button(frame_filtro, text="❌ Limpar",
                   command=lambda: (self.entry_filtro_visao.delete(0,tk.END), self.filtrar_visao_geral())).pack(side=tk.RIGHT, padx=5)
        
        self.lista_visao = ttk.Treeview(self.aba_visao, columns=("prop","valor"), show="headings", height=15)
        self.lista_visao.heading("prop", text="Propriedade")
        self.lista_visao.heading("valor", text="Valor")
        self.lista_visao.column("prop", width=220, anchor=tk.W)
        self.lista_visao.column("valor", width=400, anchor=tk.W)
        vsb = ttk.Scrollbar(self.aba_visao, orient=tk.VERTICAL, command=self.lista_visao.yview)
        self.lista_visao.configure(yscrollcommand=vsb.set)
        self.lista_visao.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_visao.bind("<Double-1>", lambda e: self.copiar_valor_visao(e))
    
    def filtrar_visao_geral(self, event=None):
        filtro = self.entry_filtro_visao.get().lower()
        if filtro in ("", "🔍 filtrar..."):
            for i in self.lista_visao.get_children():
                self.lista_visao.item(i, tags=())
            return
        for i in self.lista_visao.get_children():
            vals = self.lista_visao.item(i)["values"]
            if vals and len(vals)>=2:
                ok = any(filtro in str(v).lower() for v in vals if v is not None)
                self.lista_visao.item(i, tags=("normal",) if ok else ("oculto",))
        self.lista_visao.tag_configure("oculto", foreground="white")
        self.lista_visao.tag_configure("normal", foreground="black")
    
    def copiar_valor_visao(self, event):
        i = self.lista_visao.selection()
        if i:
            v = self.lista_visao.item(i[0])["values"]
            if v and len(v)>=2:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(v[1]))
                self.status(f"📋 Copiado: {str(v[1])[:50]}...")
    
    # ═══ ABA 2: METADADOS ═══
    def _construir_aba_metadados(self):
        frame_filtro = ttk.Frame(self.aba_metadados)
        frame_filtro.pack(fill=tk.X, pady=(5,0))
        ttk.Label(frame_filtro, text="🔍 Filtrar:").pack(side=tk.LEFT, padx=5)
        self.entry_filtro = ttk.Entry(frame_filtro)
        self.entry_filtro.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_filtro.insert(0, "🔍 Filtrar...")
        self.entry_filtro.bind("<FocusIn>", lambda e: self.entry_filtro.delete(0,tk.END) if self.entry_filtro.get()=="🔍 Filtrar..." else None)
        self.entry_filtro.bind("<KeyRelease>", self.filtrar_metadados)
        ttk.Button(frame_filtro, text="❌ Limpar",
                   command=lambda: (self.entry_filtro.delete(0,tk.END), self.filtrar_metadados())).pack(side=tk.RIGHT, padx=5)
        
        cols = ("tag_br", "tag_en", "valor")
        self.tree_meta = ttk.Treeview(self.aba_metadados, columns=cols, show="headings", height=20)
        self.tree_meta.heading("tag_br", text="📌 Propriedade (PT-BR)")
        self.tree_meta.heading("tag_en", text="🏷️ Tag Original")
        self.tree_meta.heading("valor", text="📄 Valor")
        self.tree_meta.column("tag_br", width=200, anchor=tk.W)
        self.tree_meta.column("tag_en", width=150, anchor=tk.W)
        self.tree_meta.column("valor", width=350, anchor=tk.W)
        vsb = ttk.Scrollbar(self.aba_metadados, orient=tk.VERTICAL, command=self.tree_meta.yview)
        self.tree_meta.configure(yscrollcommand=vsb.set)
        self.tree_meta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.tree_meta.bind("<Double-1>", self.copiar_linha_metadado)
    
    def filtrar_metadados(self, event=None):
        filtro = self.entry_filtro.get().lower()
        if filtro in ("", "🔍 filtrar..."):
            for i in self.tree_meta.get_children():
                self.tree_meta.item(i, tags=())
            return
        for i in self.tree_meta.get_children():
            vals = self.tree_meta.item(i)["values"]
            if vals and len(vals)==3:
                ok = any(filtro in str(v).lower() for v in vals if v is not None)
                self.tree_meta.item(i, tags=("normal",) if ok else ("oculto",))
        self.tree_meta.tag_configure("oculto", foreground="white")
        self.tree_meta.tag_configure("normal", foreground="black")
    
    # ═══ ABA 3: GPS ═══
    def _construir_aba_gps(self):
        self.frame_gps = ttk.LabelFrame(self.aba_gps, text="📍 Coordenadas GPS")
        self.frame_gps.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_gps = tk.Text(self.frame_gps, font=("Consolas",12), wrap=tk.WORD,
                                bg="#f5f5f5", relief=tk.FLAT, padx=10, pady=10)
        self.text_gps.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_gps.insert(tk.END, "📌 Nenhuma coordenada GPS detectada.")
        self.text_gps.config(state=tk.DISABLED)
        bf = ttk.Frame(self.frame_gps)
        bf.pack(fill=tk.X, pady=5)
        self.btn_mapa = ttk.Button(bf, text="🌍 Ver no Google Maps", command=self.ver_no_mapa, state=tk.DISABLED)
        self.btn_mapa.pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="📋 Copiar", command=lambda: self._copiar_texto_gps()).pack(side=tk.LEFT, padx=5)
    
    def _copiar_texto_gps(self):
        t = self.text_gps.get(1.0, tk.END).strip()
        if t and "Nenhuma" not in t:
            self.root.clipboard_clear()
            self.root.clipboard_append(t)
            self.status("📋 GPS copiado!")
    
    # ═══ ABA 4: HEX DUMP (com seletor de limite) ═══
    def _construir_aba_hex(self):
        frame_ctrl = ttk.Frame(self.aba_hex)
        frame_ctrl.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(frame_ctrl, text="🔍 Buscar no Hex:").pack(side=tk.LEFT, padx=5)
        self.entry_hex_busca = ttk.Entry(frame_ctrl)
        self.entry_hex_busca.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_hex_busca.insert(0, "🔍 Buscar string ou hex...")
        self.entry_hex_busca.bind("<FocusIn>", lambda e: self.entry_hex_busca.delete(0,tk.END) if self.entry_hex_busca.get()=="🔍 Buscar string ou hex..." else None)
        self.entry_hex_busca.bind("<KeyRelease>", self.buscar_no_hex)
        
        # ═══ SELETOR DE LIMITE DO HEX DUMP ═══
        ttk.Label(frame_ctrl, text="Limite:").pack(side=tk.LEFT, padx=(10,2))
        self.combo_hex_limite = ttk.Combobox(frame_ctrl, values=[
            "1 MB",
            "5 MB", 
            "10 MB",
            "20 MB",
            "Sem Limite"
        ], state="readonly", width=12)
        self.combo_hex_limite.current(0)  # "1 MB"
        self.combo_hex_limite.pack(side=tk.LEFT, padx=2)
        self.combo_hex_limite.bind("<<ComboboxSelected>>", self._aplicar_limite_hex)
        
        self.lbl_hex_info = ttk.Label(frame_ctrl, text="")
        self.lbl_hex_info.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(frame_ctrl, text="🔄 Recarregar", command=self._atualizar_hex).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_ctrl, text="📋 Copiar Tudo", command=self.copiar_hex).pack(side=tk.RIGHT, padx=2)
        
        # Text widget estilizado
        self.text_hex = tk.Text(self.aba_hex, font=("Consolas",9), wrap=tk.NONE,
                                 bg=self.hex_bg, fg="#d4d4d4", insertbackground="white",
                                 selectbackground="#264f78", selectforeground="white")
        vsb = ttk.Scrollbar(self.aba_hex, orient=tk.VERTICAL, command=self.text_hex.yview)
        hsb = ttk.Scrollbar(self.aba_hex, orient=tk.HORIZONTAL, command=self.text_hex.xview)
        self.text_hex.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.text_hex.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tags de estilo
        self.text_hex.tag_configure("header", foreground=self.hex_header, font=("Consolas",9,"bold"))
        self.text_hex.tag_configure("offset", foreground=self.hex_offset)
        self.text_hex.tag_configure("hex_bytes", foreground=self.hex_bytes)
        self.text_hex.tag_configure("ascii", foreground=self.hex_ascii)
        self.text_hex.tag_configure("destaque", background="#264f78", foreground="#ffffff")
        self.text_hex.tag_configure("separador", foreground="#555555")
    
    def _aplicar_limite_hex(self, event=None):
        """Atualiza o limite com base na seleção do combobox e recarrega o hex dump."""
        escolha = self.combo_hex_limite.get()
        mapa = {
            "1 MB": 1 * 1024 * 1024,
            "5 MB": 5 * 1024 * 1024,
            "10 MB": 10 * 1024 * 1024,
            "20 MB": 20 * 1024 * 1024,
            "Sem Limite": float('inf')
        }
        self.HEX_MAX_BYTES = mapa.get(escolha, 10 * 1024 * 1024)
        self.status(f"🔢 Limite do Hex alterado para: {escolha}")
        self._atualizar_hex()
    
    def buscar_no_hex(self, event=None):
        termo = self.entry_hex_busca.get().strip()
        self.text_hex.tag_remove("destaque", "1.0", tk.END)
        if not termo or termo == "🔍 Buscar string ou hex...":
            return
        
        termo_busca = termo.lower()
        inicio = "1.0"
        count = 0
        while True:
            pos = self.text_hex.search(termo_busca, inicio, tk.END, nocase=True)
            if not pos:
                break
            fim = f"{pos}+{len(termo)}c"
            self.text_hex.tag_add("destaque", pos, fim)
            inicio = fim
            count += 1
        
        if count > 0:
            first = self.text_hex.tag_ranges("destaque")[0]
            self.text_hex.see(first)
            self.status(f"🔍 Encontrado: {count} ocorrências")
        else:
            self.status(f"🔍 Nada encontrado para: {termo}")
    
    # ═══ ABA 5: PREVIEW ═══
    def _construir_aba_preview(self):
        self.canvas_pv = tk.Canvas(self.aba_preview, bg="#f0f0f0", highlightthickness=0)
        self.canvas_pv.pack(fill=tk.BOTH, expand=True)
        self.text_pv = scrolledtext.ScrolledText(self.aba_preview, font=("Consolas",10), wrap=tk.WORD)
    
    # ═══ ABA 6: EDITOR EXIF ═══
    def _construir_aba_editor(self):
        self.aviso_editor = ttk.Label(self.aba_editor,
            text="⚠️ Edição disponível APENAS para imagens (JPG, PNG, WebP, TIFF).",
            foreground="#666", font=("Segoe UI",9))
        
        self.aviso_editor.pack(pady=(10,0))
        frame_campos = ttk.LabelFrame(self.aba_editor, text="✏️ Editar Metadados EXIF")
        frame_campos.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.campos_editor = {}
        labels = {"descricao":"📝 Descrição:","fabricante":"📷 Fabricante:",
                   "modelo":"📷 Modelo:","software":"💻 Software:",
                   "artista":"👤 Artista:","copyright":"©️ Copyright:",
                   "comentario":"💬 Comentário:"}
        row=0
        for chave,label in labels.items():
            ttk.Label(frame_campos,text=label).grid(row=row,column=0,sticky=tk.W,padx=5,pady=3)
            entry = ttk.Entry(frame_campos,width=60)
            entry.grid(row=row,column=1,sticky=tk.EW,padx=5,pady=3)
            self.campos_editor[chave]=entry
            row+=1
        ttk.Label(frame_campos,text="📅 Data (DD/MM/AAAA HH:MM:SS):").grid(row=row,column=0,sticky=tk.W,padx=5,pady=3)
        self.entry_data = ttk.Entry(frame_campos,width=60)
        self.entry_data.grid(row=row,column=1,sticky=tk.EW,padx=5,pady=3)
        frame_campos.columnconfigure(1,weight=1)
        bf = ttk.Frame(self.aba_editor)
        bf.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(bf,text="💾 Salvar",command=self.salvar_edicoes_exif).pack(side=tk.LEFT,padx=3)
        ttk.Button(bf,text="🔄 Recarregar",command=self.recarregar_campos_editor).pack(side=tk.LEFT,padx=3)
        ttk.Separator(bf,orient=tk.VERTICAL).pack(side=tk.LEFT,padx=10,fill=tk.Y)
        ttk.Button(bf,text="📋 Copiar EXIF",command=self.copiar_exif).pack(side=tk.LEFT,padx=3)
        ttk.Button(bf,text="🗑️ Remover EXIF",command=self.remover_exif).pack(side=tk.LEFT,padx=3)
    
    # ═══════════════════════════════════════════════════════
    # FUNÇÕES PRINCIPAIS
    # ═══════════════════════════════════════════════════════
    
    def status(self, msg):
        self.status_bar.config(text=msg)
        self.root.update_idletasks()
    
    def abrir_arquivo_dialog(self):
        caminho = filedialog.askopenfilename(title="Selecione QUALQUER arquivo", filetypes=[("Todos","*.*")])
        if caminho: self.abrir_arquivo(caminho)
    
    def abrir_arquivo(self, caminho):
        if not os.path.isfile(caminho):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}")
            return
        self.caminho_arquivo=caminho
        self.metadados={}
        self.coordenadas_mapa=None
        self.photo=None
        nome=os.path.basename(caminho)
        ext=Path(caminho).suffix.lower()
        self.tipo_arquivo=TIPOS_ARQUIVO.get(ext,"outro")
        self.status(f"🔄 Analisando: {nome}...")
        self.root.update_idletasks()
        try:
            self.metadados=AnalisadorArquivo.info_basica(caminho)
            if self.tipo_arquivo=="imagem": self.metadados.update(AnalisadorImagem.analisar(caminho))
            elif self.tipo_arquivo in ("video","audio"): self.metadados.update(AnalisadorVideo.analisar(caminho))
            elif self.tipo_arquivo=="executavel": self.metadados.update(AnalisadorExecutavel.analisar(caminho))
            elif self.tipo_arquivo=="script": self.metadados.update(AnalisadorScript.analisar(caminho))
            elif self.tipo_arquivo=="documento": self.metadados.update(AnalisadorDocumento.analisar(caminho))
            elif self.tipo_arquivo=="compactado": self.metadados.update(AnalisadorCompactado.analisar(caminho))
            self.atualizar_interface()
            icone=self.icones.get(self.tipo_arquivo,"📦")
            self.status(f"✅ {icone} {nome} — {len(self.metadados)} metadados")
        except Exception as e:
            messagebox.showerror("Erro",f"Falha ao analisar:\n{str(e)}")            
            self.status(f"❌ Erro: {str(e)}")
        
    def atualizar_interface(self):
        self._atualizar_visao_geral()
        self._atualizar_metadados()
        self._atualizar_gps()
        self._atualizar_hex()
        self._atualizar_preview()
        self.recarregar_campos_editor()
    
    def _atualizar_visao_geral(self):
        for i in self.lista_visao.get_children(): self.lista_visao.delete(i)
        ordem=["FILE_NAME","FILE_SIZE","FILE_EXT","FILE_MIME","FILE_MAGIC",
               "FILE_CREATED","FILE_MODIFIED","FILE_ACCESSED",
               "IMAGE_WIDTH","IMAGE_HEIGHT","IMAGE_FORMAT","IMAGE_MODE",
               "VIDEO_CODEC","VIDEO_WIDTH","VIDEO_HEIGHT","VIDEO_FPS",
               "VIDEO_DURATION","AUDIO_CODEC",
               "PE_MACHINE","PE_ARCH","PE_SUBSYSTEM","PE_COMPANY",
               "PE_DESCRIPTION","PE_VERSION","PE_COMPILED",
               "SCRIPT_LANGUAGE","SCRIPT_LINES","SCRIPT_SHEBANG",
               "PDF_VERSION","PDF_PAGES","PDF_TITLE","PDF_AUTHOR",
               "ARCHIVE_FORMAT","ARCHIVE_FILES","ARCHIVE_UNCOMPRESSED",
               "FILE_MD5","FILE_SHA1","FILE_SHA256"]
        adicionados=set()
        for tag in ordem:
            if tag in self.metadados:
                nome_pt=TRADUCAO_TAGS.get(tag,tag)
                self.lista_visao.insert("",tk.END,values=(nome_pt,self.formatar_valor(tag,self.metadados[tag])))
                adicionados.add(tag)
        for tag,valor in sorted(self.metadados.items()):
            if tag not in adicionados and not tag.startswith("GPS"):
                nome_pt=TRADUCAO_TAGS.get(tag,tag)
                self.lista_visao.insert("",tk.END,values=(nome_pt,self.formatar_valor(tag,valor)))
    
    def _atualizar_metadados(self):
        for i in self.tree_meta.get_children(): self.tree_meta.delete(i)
        for tag,valor in sorted(self.metadados.items()):
            nome_pt=TRADUCAO_TAGS.get(tag,tag)
            self.tree_meta.insert("",tk.END,values=(nome_pt,tag,self.formatar_valor(tag,valor)))
    
    def _atualizar_gps(self):
        self.text_gps.config(state=tk.NORMAL)
        self.text_gps.delete(1.0,tk.END)
        self.coordenadas_mapa=None
        self.btn_mapa.config(state=tk.DISABLED)
        if self.tipo_arquivo=="imagem":
            gps_info=self.metadados.get("GPSInfo")
            if gps_info:
                self.text_gps.insert(tk.END,"📍 INFORMAÇÕES GPS\n")
                self.text_gps.insert(tk.END,"═"*50+"\n")
                if isinstance(gps_info,dict):
                    for chave,valor in gps_info.items():
                        self.text_gps.insert(tk.END,f"\n🔹 {chave}: {valor}")
                lat=self.metadados.get("GPSLatitudeDecimal")
                lon=self.metadados.get("GPSLongitudeDecimal")
                if lat is not None and lon is not None:
                    self.coordenadas_mapa=(lat,lon)
                    self.text_gps.insert(tk.END,f"\n\n🌍 Google Maps: {lat:.6f}, {lon:.6f}")
                    self.btn_mapa.config(state=tk.NORMAL)
            else:
                self.text_gps.insert(tk.END,"📌 Nenhum metadado GPS encontrado.")
        else:
            self.text_gps.insert(tk.END,f"📌 GPS não se aplica para {NOME_TIPO.get(self.tipo_arquivo,'este tipo')}.")
        self.text_gps.config(state=tk.DISABLED)
    
    def _atualizar_hex(self):
        """Hex Dump do arquivo respeitando o limite selecionado"""
        self.text_hex.delete(1.0,tk.END)
        if not self.caminho_arquivo: return
        
        nome_arquivo = os.path.basename(self.caminho_arquivo)
        tamanho_total = os.path.getsize(self.caminho_arquivo)
        
        # Aplica o limite selecionado
        ler_bytes = int(min(tamanho_total, self.HEX_MAX_BYTES))
        truncado = tamanho_total > ler_bytes
        
        try:
            with open(self.caminho_arquivo,"rb") as f:
                dados = f.read(ler_bytes)

            # Cabeçalho
            self.text_hex.insert(tk.END,f"🔢 HEX DUMP — {nome_arquivo}\n\n","header")
            self.text_hex.insert(tk.END,f"📏 Arquivo: {AnalisadorArquivo._formatar_tamanho(tamanho_total)}  |  Exibindo: {AnalisadorArquivo._formatar_tamanho(ler_bytes)}\n\n","header")
            if truncado:
                limite_str = self.combo_hex_limite.get()
                self.text_hex.insert(tk.END,f"⚠️ Arquivo maior que o limite ({limite_str}). Mostrando apenas os primeiros bytes.\n","header")
            self.text_hex.insert(tk.END,f"═"*80+"\n","header")
            
            # Legenda
            self.text_hex.insert(tk.END,"OFFSET      ","offset")
            self.text_hex.insert(tk.END,"   00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ","hex_bytes")
            self.text_hex.insert(tk.END,"  ASCII\n","ascii")
            self.text_hex.insert(tk.END,"─"*80+"\n","separador")
            
            offset=0
            for i in range(0,len(dados),16):
                bloco=dados[i:i+16]
                # Offset (verde musgo)
                self.text_hex.insert(tk.END,f"{offset:08x}  ","offset")
                # Bytes (verde água)
                hex_parts=[]
                for j,b in enumerate(bloco):
                    hex_parts.append(f"{b:02x}")
                    if j==7: hex_parts.append(" ")
                hex_str=" ".join(hex_parts)
                hex_str=hex_str.ljust(49)
                self.text_hex.insert(tk.END,hex_str+" ","hex_bytes")
                # ASCII (laranja abóbora)
                ascii_str="".join(chr(b) if 32<=b<=126 else "." for b in bloco)
                self.text_hex.insert(tk.END,f"|{ascii_str}|\n","ascii")
                offset+=16
            
            if truncado:
                limite_str = self.combo_hex_limite.get()
                self.text_hex.insert(tk.END,f"\n⚠️ Arquivo truncado em {limite_str}. Total real: {AnalisadorArquivo._formatar_tamanho(tamanho_total)}","separador")
            
            # Atualizar label
            self.lbl_hex_info.config(text=f"{len(dados)} bytes de {AnalisadorArquivo._formatar_tamanho(tamanho_total)}")
            
        except Exception as e:
            self.text_hex.insert(tk.END,f"Erro ao ler arquivo: {str(e)}")
    
    def _atualizar_preview(self):
        self.canvas_pv.delete("all")
        self.text_pv.pack_forget()
        if not self.caminho_arquivo:
            w=self.canvas_pv.winfo_width()//2 or 200
            h=self.canvas_pv.winfo_height()//2 or 100
            self.canvas_pv.create_text(w,h,text="📂 Abra um arquivo para ver o preview",
                                       justify=tk.CENTER,font=("Segoe UI",14),fill="#999")
            return
        nome=os.path.basename(self.caminho_arquivo)
        tam=self.metadados.get("FILE_SIZE","---")
        data_mod=self.metadados.get("FILE_MODIFIED","---")
        ext=self.metadados.get("FILE_EXT","---")
        if self.tipo_arquivo=="imagem": self._preview_imagem()
        elif self.tipo_arquivo in ("script","documento") and ext in (".txt",".py",".js",".bat",".ps1",".sh",
                    ".html",".css",".xml",".json",".yaml",".yml",".ini",".cfg",".conf",
                    ".toml",".md",".csv",".sql",".log",".r",".php",".pl",".rb",".lua",
                    ".java",".c",".cpp",".h",".cs",".rs",".go"): self._preview_texto()
        elif self.tipo_arquivo=="video":
            w=self.canvas_pv.winfo_width()//2 or 200
            h=self.canvas_pv.winfo_height()//2 or 100
            self.canvas_pv.create_text(w,h,text=f"🎬 {nome}\n\nDuração: {self.metadados.get('VIDEO_DURATION','---')}\nResolução: {self.metadados.get('VIDEO_WIDTH','?')}x{self.metadados.get('VIDEO_HEIGHT','?')}\nCodec: {self.metadados.get('VIDEO_CODEC','---')}\nFPS: {self.metadados.get('VIDEO_FPS','---')}",justify=tk.CENTER,font=("Segoe UI",12),fill="#333")
        elif self.tipo_arquivo=="executavel":
            w=self.canvas_pv.winfo_width()//2 or 200
            h=self.canvas_pv.winfo_height()//2 or 100
            self.canvas_pv.create_text(w,h,text=f"⚙️ {nome}\n\nArquitetura: {self.metadados.get('PE_MACHINE','---')}\nSubsistema: {self.metadados.get('PE_SUBSYSTEM','---')}\nEmpresa: {self.metadados.get('PE_COMPANY','---')}\nVersão: {self.metadados.get('PE_VERSION','---')}\nCompilado: {self.metadados.get('PE_COMPILED','---')}",justify=tk.CENTER,font=("Segoe UI",12),fill="#333")
        else:
            icone={"audio":"🎵","compactado":"🗜️","documento":"📄"}.get(self.tipo_arquivo,"📦")
            w=self.canvas_pv.winfo_width()//2 or 200
            h=self.canvas_pv.winfo_height()//2 or 100
            self.canvas_pv.create_text(w,h,text=f"{icone} {nome}\n\n📌 Extensão: {ext.upper()}\n💾 {tam}\n📅 {data_mod}\n\n🔍 {len(self.metadados)} metadados",justify=tk.CENTER,font=("Segoe UI",12),fill="#333")
    
    def _preview_imagem(self):
        try:
            img=Image.open(self.caminho_arquivo)
            w=self.canvas_pv.winfo_width()
            h=self.canvas_pv.winfo_height()
            if w<=1 or h<=1: self.root.after(200,self._preview_imagem); return
            scale=min(w/img.width,h/img.height)*0.9
            nw,nh=int(img.width*scale),int(img.height*scale)
            if nw>0 and nh>0:
                cp=img.copy(); cp.thumbnail((nw,nh),Image.LANCZOS)
                self.photo=ImageTk.PhotoImage(cp)
                self.canvas_pv.create_image((w-nw)//2,(h-nh)//2,anchor=tk.NW,image=self.photo)
            img.close()
        except Exception as e:
            self.canvas_pv.create_text(self.canvas_pv.winfo_width()//2,self.canvas_pv.winfo_height()//2,
                                       text=f"Erro: {str(e)}",justify=tk.CENTER,fill="red")
    
    def _preview_texto(self):
        self.text_pv.pack(fill=tk.BOTH,expand=True)
        self.text_pv.delete(1.0,tk.END)
        try:
            with open(self.caminho_arquivo,"r",encoding="utf-8",errors="ignore") as f:
                self.text_pv.insert(1.0,f.read(50000))
        except Exception as e:
            self.text_pv.insert(1.0,f"Erro: {str(e)}")
    
    # ═══════════════════════════════════════════════════════
    # FORMATAÇÃO
    # ═══════════════════════════════════════════════════════
    
    def formatar_valor(self, tag, valor):
        if tag in TRADUCAO_VALORES and isinstance(valor,int) and valor in TRADUCAO_VALORES[tag]:
            return f"{TRADUCAO_VALORES[tag][valor]} ({valor})"
        if tag in ("DateTime","DateTimeOriginal","DateTimeDigitized"):
            if isinstance(valor,str) and ":" in valor:
                try: return datetime.strptime(valor,"%Y:%m:%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                except: pass
        if isinstance(valor,tuple) and len(valor)==2 and valor[1]!=0:
            return f"{valor[0]/valor[1]:.4f} ({valor[0]}/{valor[1]})"
        if isinstance(valor,dict): return f"{len(valor)} campos"
        if isinstance(valor,bytes):
            try: return valor.decode("utf-8",errors="ignore")[:200]
            except: return str(valor)[:200]
        return str(valor)
    
    # ═══════════════════════════════════════════════════════
    # AÇÕES
    # ═══════════════════════════════════════════════════════
    
    def abrir_virustotal(self):
        sha256=self.metadados.get("FILE_SHA256","")
        if not sha256:
            messagebox.showwarning("Aviso","Nenhum hash SHA256 disponível!")
            return
        webbrowser.open(f"https://www.virustotal.com/gui/file/{sha256}")
        self.status(f"🔍 VirusTotal: {sha256[:16]}...")
    
    def copiar_tudo_visao(self):
        linhas=[]
        for i in self.lista_visao.get_children():
            v=self.lista_visao.item(i)["values"]
            if v: linhas.append(f"{v[0]}: {v[1]}")
        if linhas:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(linhas))
            self.status("📋 Copiado!")
    
    def copiar_linha_metadado(self, event):
        i=self.tree_meta.selection()
        if i:
            v=self.tree_meta.item(i[0])["values"]
            if v and len(v)==3:
                self.root.clipboard_clear()
                self.root.clipboard_append(v[2])
                self.status(f"📋 Copiado: {v[2][:50]}...")
    
    def copiar_hex(self):
        t=self.text_hex.get(1.0,tk.END).strip()
        if t:
            self.root.clipboard_clear()
            self.root.clipboard_append(t)
            self.status("📋 Hex copiado!")
    
    def copiar_hash(self):
        if "FILE_SHA256" in self.metadados:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.metadados["FILE_SHA256"])
            self.status("🔐 SHA256 copiado!")
        else: messagebox.showwarning("Aviso","Nenhum hash disponível.")
    
    def ver_no_mapa(self):
        if self.coordenadas_mapa:
            lat,lon=self.coordenadas_mapa
            webbrowser.open(f"https://www.google.com/maps?q={lat},{lon}")
            self.status(f"🌍 Mapa: {lat:.6f},{lon:.6f}")
    
    def salvar_copia(self):
        if not self.caminho_arquivo: messagebox.showwarning("Aviso","Nenhum arquivo!"); return
        dest=filedialog.asksaveasfilename(initialfile=os.path.basename(self.caminho_arquivo))
        if dest:
            try: shutil.copy2(self.caminho_arquivo,dest); self.status(f"✅ Cópia: {os.path.basename(dest)}")
            except Exception as e: messagebox.showerror("Erro",str(e))
    
    def abrir_local_pasta(self):
        if not self.caminho_arquivo: return
        pasta=os.path.dirname(self.caminho_arquivo)
        if platform.system()=="Windows": os.startfile(pasta)
        elif platform.system()=="Darwin": subprocess.run(["open",pasta])
        else: subprocess.run(["xdg-open",pasta])
    
    def exportar_json(self):
        if not self.metadados: messagebox.showwarning("Aviso","Nenhum metadado!"); return
        dest=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if not dest: return
        dados={"arquivo":self.caminho_arquivo or "N/A","tipo":self.tipo_arquivo,
               "data":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),"total":len(self.metadados),"metadados":{}}
        for k,v in self.metadados.items():
            dados["metadados"][k]={"descricao":TRADUCAO_TAGS.get(k,k),"valor":str(v)}
        try:
            with open(dest,"w",encoding="utf-8") as f: json.dump(dados,f,ensure_ascii=False,indent=2)
            self.status(f"✅ Exportado: {os.path.basename(dest)}")
        except Exception as e: messagebox.showerror("Erro",str(e))
    
    def gerar_relatorio(self):
        if not self.metadados: messagebox.showwarning("Aviso","Nenhum metadado!"); return
        nome=os.path.basename(self.caminho_arquivo) if self.caminho_arquivo else "N/A"
        cats={"📄 Arquivo":["FILE_NAME","FILE_SIZE","FILE_EXT","FILE_MIME","FILE_MAGIC",
                           "FILE_CREATED","FILE_MODIFIED","FILE_ACCESSED"],
              "🔐 Hashes":["FILE_MD5","FILE_SHA1","FILE_SHA256"],
              "🖼️ Imagem":["IMAGE_WIDTH","IMAGE_HEIGHT","IMAGE_FORMAT","Make","Model",
                          "DateTimeOriginal","FNumber","ISOSpeedRatings","FocalLength","ExposureTime","Flash"],
              "📍 GPS":["GPSLatitude","GPSLongitude","GPSAltitude","GPSDateStamp"],
              "🎬 Vídeo/Áudio":["VIDEO_CODEC","VIDEO_WIDTH","VIDEO_HEIGHT","VIDEO_FPS",
                               "VIDEO_DURATION","AUDIO_CODEC","AUDIO_SAMPLE_RATE","AUDIO_CHANNELS"],
              "⚙️ Executável":["PE_MACHINE","PE_ARCH","PE_SUBSYSTEM","PE_COMPANY",
                              "PE_DESCRIPTION","PE_VERSION","PE_COMPILED"],
              "📜 Script":["SCRIPT_LANGUAGE","SCRIPT_LINES","SCRIPT_SHEBANG"],
              "📄 Documento":["PDF_VERSION","PDF_PAGES","PDF_TITLE","PDF_AUTHOR"],
              "🗜️ Compactado":["ARCHIVE_FORMAT","ARCHIVE_FILES","ARCHIVE_UNCOMPRESSED"]}
        todas=set()
        for v in cats.values(): todas.update(v)
        cats["📦 Outros"]=[k for k in self.metadados if k not in todas]
        linhas=[]
        linhas.append("="*70)
        linhas.append("  RELATÓRIO DE METADADOS")
        linhas.append("="*70)
        linhas.append(f"  Arquivo: {nome}")
        linhas.append(f"  Tipo: {NOME_TIPO.get(self.tipo_arquivo,'Desconhecido')}")
        linhas.append(f"  Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"  Total: {len(self.metadados)}")
        linhas.append(f"  SHA256 (VT): https://www.virustotal.com/gui/file/{self.metadados.get('FILE_SHA256','N/A')}")
        linhas.append("-"*70)
        for cat_nome,cat_tags in cats.items():
            itens=[]
            for tag in cat_tags:
                if tag in self.metadados:
                    nome_pt=TRADUCAO_TAGS.get(tag,tag)
                    valor=self.formatar_valor(tag,self.metadados[tag])
                    itens.append(f"  {nome_pt}: {valor}")
            if itens:
                linhas.append(f"\n{cat_nome}:")
                linhas.append("-"*50)
                linhas.extend(itens)
        linhas.append("\n"+"="*70)
        linhas.append("  Fim do Relatório")
        linhas.append("="*70)
        texto="\n".join(linhas)
        
        # ═══ RELATÓRIO — MAXIMIZADO + 2 SCROLLBARS ═══
        janela=tk.Toplevel(self.root)
        janela.title("📝 Relatório"); janela.transient(self.root)
        try:
            janela.state("zoomed")
        except:
            janela.geometry("1200x700")

        janela._is_zoomed = True  # começa maximizado

        def toggle_maximizar():
            if janela._is_zoomed:
                janela.state("normal")
                janela.geometry("1200x700")
                btn_toggle.config(text="⬜ Maximizar")
                janela._is_zoomed = False
            else:
                janela.state("zoomed")
                btn_toggle.config(text="❎ Restaurar")
                janela._is_zoomed = True
               

        # Frame para o Text + 2 scrollbars
        ta_frame = ttk.Frame(janela)
        ta_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ta = tk.Text(ta_frame, wrap=tk.NONE, font=("Consolas", 10))
        vsb = ttk.Scrollbar(ta_frame, orient=tk.VERTICAL, command=ta.yview)
        hsb = ttk.Scrollbar(ta_frame, orient=tk.HORIZONTAL, command=ta.xview)
        ta.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        ta.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        ta_frame.grid_rowconfigure(0, weight=1)
        ta_frame.grid_columnconfigure(0, weight=1)
        
        ta.insert(tk.END, texto)

        bf=ttk.Frame(janela); bf.pack(fill=tk.X, padx=10, pady=(0,10))
        ttk.Button(bf,text="📋 Copiar",command=lambda:(janela.clipboard_clear(),janela.clipboard_append(texto),self.status("📋 Copiado!"))).pack(side=tk.LEFT,padx=5)
        ttk.Button(bf,text="💾 Salvar",command=lambda:self._salvar_relatorio(texto)).pack(side=tk.LEFT,padx=5)
        btn_toggle = ttk.Button(bf, text="❎ Restaurar", command=toggle_maximizar)
        btn_toggle.pack(side=tk.LEFT, padx=5)
        ttk.Button(bf,text="❌ Fechar",command=janela.destroy).pack(side=tk.RIGHT,padx=5)

        # ===== Rodapé =====
        rodape = ttk.Frame(janela)
        rodape.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

        ttk.Separator(rodape, orient="horizontal").pack(fill=tk.X, pady=(0, 4))

        ttk.Label(
            rodape,
            text=(
                "📖 RELATÓRIO DE METADADOS • "
                "📋 Copiar o conteúdo | 💾 Salvar em arquivo | "
                "❎ Restaurar a janela | ❌ Fechar."
            ),
            anchor="center",
            justify="center"
        ).pack(fill="x", pady=(0, 40))


    def _salvar_relatorio(self, texto):
        dest=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Texto","*.txt")])
        if dest:
            try:
                with open(dest,"w",encoding="utf-8") as f: f.write(texto)
                self.status(f"✅ Relatório: {os.path.basename(dest)}")
            except Exception as e: messagebox.showerror("Erro",str(e))


    def buscar_comparacao(self):
        """Busca texto na janela de comparação (usa self.text_comparacao)"""
        if self.text_comparacao is None:
            self.status("⚠️ Nenhuma comparação ativa no momento.")
            return

        termo = self.entry_comparar.get().strip()

        self.text_comparacao.tag_remove("busca", "1.0", "end")

        if not termo:
            return

        inicio = "1.0"
        count = 0

        while True:
            pos = self.text_comparacao.search(
                termo,
                inicio,
                stopindex="end",
                nocase=True
            )

            if not pos:
                break

            fim = f"{pos}+{len(termo)}c"
            self.text_comparacao.tag_add("busca", pos, fim)
            inicio = fim
            count += 1

        self.text_comparacao.tag_config(
            "busca",
            background="yellow",
            foreground="black"
        )

        if count > 0:
            self.status(f"🔍 Encontrado: {count} ocorrências")
        else:
            self.status(f"🔍 Nada encontrado para: {termo}")
    
    # ═══════════════════════════════════════════════════════
    # COMPARAÇÃO DE ARQUIVOS — CORRIGIDO
    # ═══════════════════════════════════════════════════════
    
    def comparar_arquivos(self):
        arq1 = filedialog.askopenfilename(title="PRIMEIRO arquivo")
        if not arq1: return
        arq2 = filedialog.askopenfilename(title="SEGUNDO arquivo")
        if not arq2: return
        self.status("🔄 Comparando...")
        caminho_orig = self.caminho_arquivo
        self.analisar_tudo_simples(arq1)
        m1 = self.metadados.copy()
        n1 = os.path.basename(arq1)
        self.analisar_tudo_simples(arq2)
        m2 = self.metadados.copy()
        n2 = os.path.basename(arq2)
        if caminho_orig:
            self.analisar_tudo_simples(caminho_orig)
            self.atualizar_interface()

        TAGS_GPS_DERIVADAS = {
            "GPSLatitudeDecimal", "GPSLongitudeDecimal",
            "Latitude", "Longitude", "GPSAltitude",
        }

        todas = set(list(m1.keys()) + list(m2.keys()))
        
        def _fmt_valor(v):
            """Converte ANY valor para string limpa na comparação"""
            if isinstance(v, bytes):
                return f"[bytes: {len(v)}]"
            if isinstance(v, dict):
                return f"[dict: {len(v)} campos]"
            return str(v)

        linhas = [
            "=" * 182,
            "  COMPARAÇÃO",
            "=" * 182,
            f"\nFoto 🖼 1: {n1:<96}  Foto 🖼 2: {n2}\n",
            "-" * 182,
            " " * 182,
        ]

        

        for k in sorted(todas):
            nome_pt = TRADUCAO_TAGS.get(k, k)
            v1_raw = m1.get(k, "---")
            v2_raw = m2.get(k, "---")

            if k in TAGS_GPS_DERIVADAS:
                continue

            if k == "GPSInfo":
                linhas.append(f"\n{nome_pt}\n")
                linhas.append(f"{'Propriedade':<42} {'[1]':<65} {'[2]':<45}")
                linhas.append(f"{'─'*35} {'─'*45} {'─'*100}")

                chaves_gps = set()
                if isinstance(v1_raw, dict):
                    chaves_gps.update(v1_raw.keys())
                if isinstance(v2_raw, dict):
                    chaves_gps.update(v2_raw.keys())

                chaves_derivadas = []
                for deriv in ["GPSLatitudeDecimal", "GPSLongitudeDecimal", "Latitude", "Longitude", "GPSAltitude"]:
                    if deriv in m1 or deriv in m2:
                        chaves_derivadas.append(deriv)

                for ck in sorted(chaves_gps):
                    v1_val = v1_raw.get(ck, "---") if isinstance(v1_raw, dict) else "---"
                    v2_val = v2_raw.get(ck, "---") if isinstance(v2_raw, dict) else "---"
                    linhas.append(f"  {str(ck):<40} {str(v1_val):<65} {str(v2_val):<45}")

                for deriv in chaves_derivadas:
                    nome_deriv = {
                        "GPSLatitudeDecimal": "Latitude (decimal)",
                        "GPSLongitudeDecimal": "Longitude (decimal)",
                        "Latitude": "Latitude (formatada)",
                        "Longitude": "Longitude (formatada)",
                        "GPSAltitude": "Altitude",
                    }.get(deriv, deriv)
                    v1_val = m1.get(deriv, "---")
                    v2_val = m2.get(deriv, "---")
                    linhas.append(f"  {nome_deriv:<42} {str(v1_val):<65} {str(v2_val):<45}")

                linhas.append("")
                continue

            # --- QUALQUER valor: converte com _fmt_valor e exibe lado a lado ---
            v1 = _fmt_valor(v1_raw)
            v2 = _fmt_valor(v2_raw)

            # Se for string longa (>80), coloca em bloco com [1] / [2]
            if len(v1) > 80 or len(v2) > 80:
                linhas.append(f"{nome_pt}:")
                for l1 in v1.split("\n"):
                    linhas.append(f"  [1] {l1}")
                for l2 in v2.split("\n"):
                    linhas.append(f"  [2] {l2}")
                linhas.append("")
            else:
                linhas.append(f"{nome_pt:<42} {v1:<65} {v2:<100}")

        linhas.append("=" * 182)
        texto = "\n".join(linhas)

        # ═══ JANELA ═══
        janela = tk.Toplevel(self.root)
        janela.title("🔍 Comparação")
        janela.transient(self.root)
        try:
            janela.state("zoomed")
        except:
            janela.geometry("1200x700")
        janela._is_zoomed = True

        def toggle_maximizar():
            if janela._is_zoomed:
                janela.state("normal")
                janela.geometry("1200x700")
                btn_toggle.config(text="⬜ Maximizar")
                janela._is_zoomed = False
            else:
                janela.state("zoomed")
                btn_toggle.config(text="❎ Restaurar")
                janela._is_zoomed = True                       

        ta_frame = ttk.Frame(janela)
        ta_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ta = tk.Text(ta_frame, wrap=tk.NONE, font=("Consolas", 9))
        vsb = ttk.Scrollbar(ta_frame, orient=tk.VERTICAL, command=ta.yview)
        hsb = ttk.Scrollbar(ta_frame, orient=tk.HORIZONTAL, command=ta.xview)
        ta.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        ta.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        ta_frame.grid_rowconfigure(0, weight=1)
        ta_frame.grid_columnconfigure(0, weight=1)
        ta.insert(tk.END, texto)

        # ═══ ARMAZENA REFERÊNCIA PARA O MÉTODO buscar_comparacao ═══
        self.text_comparacao = ta

        # ===== Barra de pesquisa =====
        frame = ttk.Frame(janela)
        frame.pack(fill="x", padx=5, pady=5)

        self.entry_comparar = ttk.Entry(frame)
        self.entry_comparar.pack(side="left", fill="x", expand=True)

        ttk.Button(frame,  text="🔍 Pesquisar", command=self.buscar_comparacao).pack(side="left", padx=5)        

        bf = ttk.Frame(janela)
        bf.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(bf, text="📋 Copiar",
                command=lambda: (janela.clipboard_clear(), janela.clipboard_append(texto))).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="💾 Salvar",
                   command=lambda: self._salvar_comparacao(texto, n1, n2)).pack(side=tk.LEFT, padx=5)        
        btn_toggle = ttk.Button(bf, text="❎ Restaurar", command=toggle_maximizar)
        btn_toggle.pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="❌ Fechar", command=janela.destroy).pack(side=tk.RIGHT, padx=5)
        self.status(f"✅ Comparação: {n1} vs {n2}")        

        # ===== Rodapé =====
        rodape = ttk.Frame(janela)
        rodape.pack(side="bottom", fill="x", padx=5, pady=5)

        ttk.Separator(rodape, orient="horizontal").pack(fill="x", pady=(0, 5))

        ttk.Label(
            rodape,
            text=(
                "ℹ️ Como usar: Digite um termo na pesquisa e clique em '🔍 Pesquisar' "
                "para localizar ocorrências na comparação. Use '📋 Copiar' para copiar "
                "o resultado, '💾 Salvar' para exportar, '❎ Restaurar' para restaurar "
                "a janela e '❌ Fechar"
            ),
            anchor="center",
            justify="center"
        ).pack(fill="x", pady=(0, 40))  


    def _salvar_comparacao(self, texto, n1, n2):
        """Salva o resultado da comparação em um arquivo .txt"""
        nome_sugerido = f"comparacao_{Path(n1).stem}_vs_{Path(n2).stem}.txt"
        dest = filedialog.asksaveasfilename(
            title="Salvar Comparação",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")],
            initialfile=nome_sugerido
        )
        if dest:
            try:
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(texto)
                self.status(f"✅ Comparação salva: {os.path.basename(dest)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
    
    def analisar_tudo_simples(self, caminho):
        self.metadados=AnalisadorArquivo.info_basica(caminho)
        ext=Path(caminho).suffix.lower()
        t=TIPOS_ARQUIVO.get(ext,"outro")
        if t=="imagem": self.metadados.update(AnalisadorImagem.analisar(caminho))
        elif t in ("video","audio"): self.metadados.update(AnalisadorVideo.analisar(caminho))
        elif t=="executavel": self.metadados.update(AnalisadorExecutavel.analisar(caminho))
        elif t=="script": self.metadados.update(AnalisadorScript.analisar(caminho))
        elif t=="documento": self.metadados.update(AnalisadorDocumento.analisar(caminho))
        elif t=="compactado": self.metadados.update(AnalisadorCompactado.analisar(caminho))
    
    # ═══════════════════════════════════════════════════════
    # EDIÇÃO EXIF — CORRIGIDO: SUPORTE A PNG, WEBP, TIFF, JPEG
    # ═══════════════════════════════════════════════════════
    
    def recarregar_campos_editor(self):
        if not self.caminho_arquivo or self.tipo_arquivo != "imagem":
            for chave in self.campos_editor:
                self.campos_editor[chave].delete(0, tk.END)
            self.entry_data.delete(0, tk.END)
            return
        for chave in self.campos_editor:
            self.campos_editor[chave].delete(0, tk.END)
        self.entry_data.delete(0, tk.END)
        try:
            img = Image.open(self.caminho_arquivo)
            exif_raw = img._getexif()
            if exif_raw:
                mape = {
                    "descricao": "ImageDescription",
                    "fabricante": "Make",
                    "modelo": "Model",
                    "software": "Software",
                    "artista": "Artist",
                    "copyright": "Copyright",
                    "comentario": "UserComment",
                }
                for chave, tag in mape.items():
                    for tid, val in exif_raw.items():
                        if TAGS.get(tid, "") == tag:
                            if isinstance(val, bytes):
                                try:
                                    val = val.decode("utf-8", errors="ignore")
                                except:
                                    val = str(val)
                            self.campos_editor[chave].insert(0, str(val))
                            break
                for tid, val in exif_raw.items():
                    nome_tag = TAGS.get(tid, "")
                    if nome_tag == "DateTimeOriginal":
                        self.entry_data.insert(0, self.formatar_data(str(val)))
                        break
                    elif nome_tag == "DateTime":
                        self.entry_data.insert(0, self.formatar_data(str(val)))
                        break
            img.close()
        except:
            pass

    def formatar_data(self, data_str):
        try:
            return datetime.strptime(data_str, "%Y:%m:%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        except:
            return data_str

    def salvar_edicoes_exif(self):
        """Salva metadados editados em QUALQUER formato (JPEG, TIFF, PNG, WebP) com EXIF preservado"""
        if not self.caminho_arquivo or self.tipo_arquivo != "imagem":
            messagebox.showwarning("Aviso", "Carregue uma imagem!")
            return
        if not TEM_PIEXIF:
            messagebox.showerror("Erro", "Instale: pip install piexif")
            return

        # Tenta carregar EXIF existente; se falhar (ex: PNG sem EXIF), cria dict vazio
        try:
            exif_dict = piexif.load(self.caminho_arquivo)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        try:
            # Mapeia campos do editor para tags EXIF
            mape = {
                "descricao": ("0th", piexif.ImageIFD.ImageDescription),
                "fabricante": ("0th", piexif.ImageIFD.Make),
                "modelo": ("0th", piexif.ImageIFD.Model),
                "software": ("0th", piexif.ImageIFD.Software),
                "artista": ("0th", piexif.ImageIFD.Artist),
                "copyright": ("0th", piexif.ImageIFD.Copyright),
                "comentario": ("Exif", piexif.ExifIFD.UserComment),
            }
            for chave, (ifd, tag) in mape.items():
                valor = self.campos_editor[chave].get().strip()
                if valor:
                    val_final = valor.encode("utf-8") if chave == "comentario" else valor
                    if ifd == "0th":
                        exif_dict["0th"][tag] = val_final
                    else:
                        exif_dict.setdefault("Exif", {})[tag] = val_final
                else:
                    if ifd == "0th" and tag in exif_dict.get("0th", {}):
                        del exif_dict["0th"][tag]
                    elif ifd == "Exif" and tag in exif_dict.get("Exif", {}):
                        del exif_dict["Exif"][tag]

            data_valor = self.entry_data.get().strip()
            if data_valor:
                try:
                    dt = datetime.strptime(data_valor, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(data_valor, "%d/%m/%Y")
                    except ValueError:
                        messagebox.showwarning("Aviso", "Use DD/MM/AAAA ou DD/MM/AAAA HH:MM:SS")
                        return
                data_exif = dt.strftime("%Y:%m:%d %H:%M:%S")
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = data_exif
                exif_dict["0th"][piexif.ImageIFD.DateTime] = data_exif

            # --- DESTINO com suporte a múltiplos formatos ---
            dest = filedialog.asksaveasfilename(
                title="Salvar metadados editados",
                defaultextension=".jpg",
                filetypes=[
                    ("JPEG", "*.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("WebP", "*.webp"),
                    ("TIFF", "*.tiff *.tif"),
                    ("Todos", "*.*"),
                ],
                initialfile=f"editado_{os.path.basename(self.caminho_arquivo)}",
            )
            if not dest:
                return

            exif_bytes = piexif.dump(exif_dict)
            img = Image.open(self.caminho_arquivo)
            ext_dest = Path(dest).suffix.lower()

            # Salva com EXIF em todos os formatos suportados
            if ext_dest in (".jpg", ".jpeg"):
                img.save(dest, "JPEG", exif=exif_bytes, quality=95)
            elif ext_dest in (".tiff", ".tif"):
                img.save(dest, "TIFF", exif=exif_bytes)
            elif ext_dest == ".png":
                img.save(dest, "PNG", exif=exif_bytes)
            elif ext_dest == ".webp":
                img.save(dest, "WEBP", exif=exif_bytes, quality=90)
            else:
                # Fallback: salva sem EXIF
                img.save(dest)

            img.close()
            messagebox.showinfo("Sucesso", "✅ Metadados salvos com sucesso!")
            self.status(f"✅ Editado: {os.path.basename(dest)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")

    def copiar_exif(self):
        """Copia EXIF de uma imagem para JPEG, TIFF, PNG ou WebP"""
        if not self.caminho_arquivo or self.tipo_arquivo != "imagem":
            messagebox.showwarning("Aviso", "Carregue uma imagem!")
            return

        # Carrega EXIF da origem
        try:
            exif_dict = piexif.load(self.caminho_arquivo)
            exif_bytes = piexif.dump(exif_dict)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler EXIF da origem:\n{e}")
            return

        dest = filedialog.askopenfilename(
            title="Imagem DESTINO (receberá o EXIF)",
            filetypes=[
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("TIFF", "*.tiff *.tif"),
                ("Todos", "*.*"),
            ],
        )
        if not dest:
            return

        ext_dest = Path(dest).suffix.lower()

        try:
            if ext_dest in (".jpg", ".jpeg"):
                piexif.insert(exif_bytes, dest)
            elif ext_dest in (".tiff", ".tif"):
                piexif.insert(exif_bytes, dest)
            elif ext_dest == ".png":
                # Para PNG, abrimos e salvamos com o parâmetro exif
                img = Image.open(dest)
                img.save(dest, "PNG", exif=exif_bytes)
                img.close()
            elif ext_dest == ".webp":
                img = Image.open(dest)
                img.save(dest, "WEBP", exif=exif_bytes, quality=90)
                img.close()
            else:
                messagebox.showwarning("Aviso", f"Formato {ext_dest} não suporta EXIF.")
                return

            messagebox.showinfo(
                "Sucesso", f"✅ EXIF copiado para:\n{os.path.basename(dest)}"
            )
            self.status(f"✅ EXIF copiado para {os.path.basename(dest)}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def remover_exif(self):
        """Remove TODOS os metadados EXIF da imagem"""
        if not self.caminho_arquivo or self.tipo_arquivo != "imagem":
            messagebox.showwarning("Aviso", "Carregue uma imagem!")
            return
        if not messagebox.askyesno("Confirmação", "Remover TODOS os metadados EXIF?"):
            return

        dest = filedialog.asksaveasfilename(
            title="Salvar SEM metadados",
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("TIFF", "*.tiff *.tif"),
                ("Todos", "*.*"),
            ],
            initialfile=f"sem_exif_{os.path.basename(self.caminho_arquivo)}",
        )
        if not dest:
            return

        try:
            img = Image.open(self.caminho_arquivo)
            ext_dest = Path(dest).suffix.lower()

            if ext_dest in (".jpg", ".jpeg"):
                # JPEG precisa de EXIF vazio para não corromper
                exif_vazio = piexif.dump(
                    {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                )
                img.save(dest, "JPEG", exif=exif_vazio, quality=95)
            elif ext_dest in (".tiff", ".tif"):
                exif_vazio = piexif.dump(
                    {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                )
                img.save(dest, "TIFF", exif=exif_vazio)
            elif ext_dest in (".png", ".webp"):
                # PNG e WebP: salva SEM o parâmetro exif para remover metadados
                img.save(dest)
            else:
                img.save(dest)

            img.close()
            messagebox.showinfo("Sucesso", "✅ Metadados removidos!")
            self.status(f"✅ Sem EXIF: {os.path.basename(dest)}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ═══ OUTROS ═══
    def personalizar_cores(self):
        cor=colorchooser.askcolor(title="Cor de destaque",initialcolor=self.cor_destaque)
        if cor[1]: self.cor_destaque=cor[1]; self.barra_menu.config(bg=self.cor_destaque); self.status("🎨 Cor alterada!")
    
    def mostrar_sobre(self):
        messagebox.showinfo("ExifTool 📷 EXIF 📄 Metadados 🔢 Hex Dump 🔐 Hashes",
            "📊 Relatórios 📂 Comparação de arquivos 📍 GPS\n\n"
            "🔍 Leitor Universal + ✏️ Editor EXIF + 🔍 VirusTotal\n\n"
            "Novidades\n\n"
            "  ✅ Hex Dump seletor de limite 1 MB, 5 MB, 10 MB, 20 MB\n\n(Sem Limite)\n\n\n"
            "  ✅ Fundo preto, bytes verde-água, ASCII laranja abóbora\n\n"
            "  ✅ Filtro de pesquisa na Visão Geral\n\n"
            "  ✅ Busca no Hex Dump\n\n"
            "  ✅ Edição EXIF em PNG, WebP, TIFF e JPEG\n\n"
            "🌐 100% Português (Brasil) • 📅 DD/MM/AAAA\n\n"
            "🔧 Pillow + piexif")
    
    def mostrar_tipos(self):
        tipos=[]
        for ext,tipo in sorted(TIPOS_ARQUIVO.items()):
            tipos.append(f"  {ext:<8} → {NOME_TIPO.get(tipo,'📦')}")
        messagebox.showinfo("Tipos Suportados","📋 QUALQUER ARQUIVO é lido!\n\n"+"\n".join(tipos))


# ═══════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use("clam")
    except:
        pass

    app = ExifToolMaster(root)

    if len(sys.argv) > 1:
        caminho = sys.argv[1]
        if os.path.isfile(caminho):
            root.after(500, lambda: app.abrir_arquivo(caminho))

    root.mainloop()

if __name__ == "__main__":
    main()
