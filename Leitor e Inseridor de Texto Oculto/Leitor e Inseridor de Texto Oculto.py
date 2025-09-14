import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import textwrap, io, os
import fitz  # PyMuPDF
import docx

SIGNATURE = b"<HIDDEN_TEXT_START>"

# ---------- LSB PARA IMAGENS ----------
def encode_text_lsb(image, text):
    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size
    text_bytes = text.encode('utf-8') + b'\x00' * 8
    bits = [(b >> i) & 1 for b in text_bytes for i in range(7, -1, -1)]
    idx = 0
    for y in range(height):
        for x in range(width):
            if idx >= len(bits):
                return img
            r, g, b = pixels[x, y]
            b = (b & 0xFE) | bits[idx]
            pixels[x, y] = (r, g, b)
            idx += 1
    return img

def extract_lsb_text(image):
    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size
    bits = [(pixels[x, y][2] & 1) for y in range(height) for x in range(width)]
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        value = 0
        for bit in byte_bits:
            value = (value << 1) | bit
        bytes_list.append(value)
    terminator_len = 8
    zero_run = 0
    message_bytes = []
    for b in bytes_list:
        if b == 0:
            zero_run += 1
            if zero_run >= terminator_len:
                break
        else:
            zero_run = 0
            message_bytes.append(b)
    if not message_bytes:
        return None
    filtered = ''.join(chr(b) for b in message_bytes if 32 <= b <= 126)
    return "\n".join(textwrap.wrap(filtered, 80)) if filtered else None

# ---------- ARQUIVOS GENÉRICOS ----------
def hide_text_in_file(file_path, text, save_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        with open(save_path, "wb") as f:
            f.write(data)
            f.write(SIGNATURE + text.encode("utf-8"))
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao esconder texto:\n{e}")

def extract_text_from_any_file(path):
    """Retorna texto escondido no final do arquivo (assinatura) se existir"""
    try:
        with open(path, "rb") as f:
            data = f.read()
        idx = data.find(SIGNATURE)
        if idx != -1:
            return data[idx+len(SIGNATURE):].decode("utf-8", errors="ignore")
        return None
    except:
        return None

# ---------- INTERFACE ----------
def exibir_imagem_pillow(img):
    img_for_display = img.copy()
    img_for_display.thumbnail((500, 300), Image.Resampling.LANCZOS)
    background = Image.new("RGB", (315, 300), "white")
    x = (315 - img_for_display.width) // 2
    y = (300 - img_for_display.height) // 2
    background.paste(img_for_display, (x, y))
    tk_img = ImageTk.PhotoImage(background)
    image_canvas.create_image(0, 0, anchor="nw", image=tk_img)
    image_canvas.image = tk_img

def open_file():
    path = filedialog.askopenfilename(
        title="Escolha um arquivo",
        filetypes=[
            ("Todos os arquivos", "*.*"),
            ("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
            ("PDF", "*.pdf"),
            ("Word DOCX", "*.docx"),
            ("Texto", "*.txt")
        ]
    )
    if not path:
        return

    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"Arquivo: {path}\n\n")

    hidden_any = extract_text_from_any_file(path)
    if hidden_any:
        text_area.insert(tk.END, "=== Texto escondido no final do arquivo ===\n\n" + hidden_any + "\n\n")

    try:
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            img = Image.open(path)
            exibir_imagem_pillow(img)
            text_area.insert(tk.END, "=== Texto oculto por LSB ===\n\n")
            hidden = extract_lsb_text(img)
            text_area.insert(tk.END, hidden + "\n" if hidden else "[Nenhum texto LSB encontrado]\n")

        elif path.lower().endswith('.pdf'):
            pdf = fitz.open(path)
            page = pdf[0]
            pix = page.get_pixmap()
            img_data = Image.open(io.BytesIO(pix.tobytes("png")))
            exibir_imagem_pillow(img_data)
            texto = "".join(p.get_text() for p in pdf)
            text_area.insert(tk.END, "=== Conteúdo do PDF ===\n\n" + texto.strip())

        elif path.lower().endswith('.docx'):
            doc = docx.Document(path)
            conteudo = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            exibir_imagem_pillow(Image.new("RGB", (1,1), "white"))
            text_area.insert(tk.END, "=== Conteúdo do DOCX ===\n\n" + conteudo.strip())

        elif path.lower().endswith('.txt'):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
            exibir_imagem_pillow(Image.new("RGB", (1,1), "white"))
            text_area.insert(tk.END, "=== Conteúdo do TXT ===\n\n" + conteudo.strip())

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")

def encode_image():
    path = filedialog.askopenfilename(
        title="Escolha uma imagem PNG",
        filetypes=[("PNG", "*.png")]
    )
    if not path:
        return
    try:
        img = Image.open(path)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro abrindo imagem:\n{e}")
        return

    text = text_area.get(1.0, tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite o texto para ocultar!")
        return

    encoded_img = encode_text_lsb(img, text)
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
    if save_path:
        encoded_img.save(save_path)
        messagebox.showinfo("Sucesso", f"Imagem salva com texto LSB em {save_path}")

def encode_any_file():
    path = filedialog.askopenfilename(title="Escolha um arquivo qualquer")
    if not path:
        return
    text = text_area.get(1.0, tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite o texto para ocultar!")
        return
    save_path = filedialog.asksaveasfilename(title="Salvar como")
    if save_path:
        hide_text_in_file(path, text, save_path)
        messagebox.showinfo("Sucesso", f"Texto oculto dentro de {save_path}")

def salvar_texto():
    conteudo = text_area.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Não há texto para salvar!")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
    if save_path:
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Texto salvo em {save_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")

# ---------- GUI ----------
root = tk.Tk()
root.title("Leitor e Inseridor de Texto Oculto")
root.wm_state('zoomed')

frame_top = tk.Frame(root)
frame_top.pack(pady=5)

tk.Button(frame_top, text="Abrir arquivo", bg="#03fc24", command=open_file).pack(pady=5)

tk.Button(frame_top, text="Ocultar Texto em IMAGEM (LSB)", bg="#03f0fc", command=encode_image).pack(pady=5)

tk.Button(frame_top, text="Ocultar Texto em QUALQUER arquivo", bg="#ff8c00", command=encode_any_file).pack(pady=5)

tk.Button(frame_top, text="Salvar texto", bg="#fcd103", command=salvar_texto).pack(pady=5)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=5)

image_canvas = tk.Canvas(frame_bottom, width=312, height=300, bg="white", highlightthickness=1, relief="solid")
image_canvas.pack(pady=20)

text_area = scrolledtext.ScrolledText(frame_bottom, width=140, height=25)
text_area.pack(pady=5)

root.mainloop()
