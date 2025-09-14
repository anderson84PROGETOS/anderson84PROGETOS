import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import textwrap

def encode_text_lsb(image, text):
    """Insere texto no LSB do canal azul da imagem"""
    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size

    text_bytes = text.encode('utf-8') + b'\x00' * 8  # terminador
    bits = []
    for b in text_bytes:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

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
    """Extrai texto oculto do LSB e mostra apenas strings legíveis"""
    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size

    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(b & 1)

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

    filtered_chars = ''.join(chr(b) for b in message_bytes if 32 <= b <= 126)
    return "\n".join(textwrap.wrap(filtered_chars, 80)) if filtered_chars else None

def open_image():
    path = filedialog.askopenfilename(
        title="Escolha uma imagem",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if not path:
        return

    try:
        img = Image.open(path)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
        return

    # mostrar imagem sem diminuir o quadrado
    img_for_display = img.copy()
    img_for_display.thumbnail((500, 300), Image.Resampling.LANCZOS)

    # cria um fundo branco do tamanho fixo do canvas
    background = Image.new("RGB", (500, 300), "white")
    x = (500 - img_for_display.width) // 2
    y = (300 - img_for_display.height) // 2
    background.paste(img_for_display, (x, y))

    tk_img = ImageTk.PhotoImage(background)
    image_canvas.create_image(0, 0, anchor="nw", image=tk_img)
    image_canvas.image = tk_img

    # limpar e mostrar texto
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"Arquivo: {path}\n\n")
    text_area.insert(tk.END, "=== Texto oculto (LSB) ===\n\n")
    hidden = extract_lsb_text(img)
    if hidden:
        text_area.insert(tk.END, hidden + "\n")
    else:
        text_area.insert(tk.END, "[Nenhum texto oculto encontrado]\n")

def encode_image():
    path = filedialog.askopenfilename(
        title="Escolha uma imagem para esconder texto",
        filetypes=[("PNG", "*.png")]
    )
    if not path:
        return

    try:
        img = Image.open(path)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
        return

    text = text_area.get(1.0, tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite o texto para ocultar na área de texto!")
        return

    encoded_img = encode_text_lsb(img, text)
    save_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG", "*.png")]
    )
    if save_path:
        encoded_img.save(save_path)
        messagebox.showinfo("Sucesso", f"Imagem salva com texto oculto em {save_path}")

def salvar_texto():
    conteudo = text_area.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Não há texto para salvar!")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de texto", "*.txt")]
    )
    if save_path:
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Texto salvo em\n\n{save_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

# GUI
root = tk.Tk()
root.title("Leitor e Inseridor de Texto Oculto (LSB)")
root.wm_state('zoomed')

# botões
frame_top = tk.Frame(root)
frame_top.pack(pady=5)

open_btn = tk.Button(frame_top, text="Abrir imagem", bg="#03fc24", fg="black", command=open_image)
open_btn.pack(pady=5)

encode_btn = tk.Button(frame_top, text="Ocultar Texto em imagem", bg="#03f0fc", fg="black", command=encode_image)
encode_btn.pack(pady=5)

save_txt_btn = tk.Button(frame_top, text="Salvar", bg="#fcd103", fg="black",  command=salvar_texto)
save_txt_btn.pack(pady=5)

# parte de baixo: imagem à esquerda, texto à direita
frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=5)

# canvas fixo 500x300 para imagem
image_canvas = tk.Canvas(frame_bottom, width=500, height=300, bg="white", highlightthickness=1, relief="solid")
image_canvas.pack(pady=20)

text_area = scrolledtext.ScrolledText(frame_bottom, width=140, height=25)
text_area.pack(pady=5)

root.mainloop()
