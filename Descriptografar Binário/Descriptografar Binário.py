import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import string

# --- Funções de conversão (segundo código) ---
def binario_para_texto(bstr: str) -> str:
    bits = ''.join(ch for ch in bstr if ch in '01')
    if len(bits) % 8 != 0:
        raise ValueError(f'Quantidade de bits ({len(bits)}) não é múltipla de 8.')
    chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
    return ''.join(chars)

# --- Funções de extração e inserção LSB (primeiro código) ---
def extract_lsb_bits(img):
    """Extrai os bits LSB do canal azul."""
    img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size
    bits = []
    for y in range(height):
        for x in range(width):
            _, _, b = pixels[x, y]
            bits.append(b & 1)
    return bits

def bits_to_bytes(bits, msb_first=True, stop_on_terminator=True):
    """Agrupa bits em bytes (MSB-first ou LSB-first)."""
    bytes_list = []
    zero_run = 0
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            idx = i + j
            bit = bits[idx] if idx < len(bits) else 0
            if msb_first:
                byte = (byte << 1) | (bit & 1)
            else:
                byte |= ((bit & 1) << j)
        bytes_list.append(byte)
        if stop_on_terminator:
            if byte == 0:
                zero_run += 1
            else:
                zero_run = 0
            if zero_run >= 8:
                return bytes_list[:-8]
    return bytes_list

def filtrar_printable(texto):
    """Remove caracteres não legíveis, deixando só ASCII imprimível."""
    return "".join(ch for ch in texto if ch in string.printable)

def decode_text_lsb(image):
    """Extrai e retorna apenas strings legíveis escondidas no LSB."""
    try:
        bits = extract_lsb_bits(image)
        bytes_msb = bits_to_bytes(bits, msb_first=True)
        txt_msb = filtrar_printable(bytes(bytes_msb).decode('utf-8', errors='ignore'))
        bytes_lsb = bits_to_bytes(bits, msb_first=False)
        txt_lsb = filtrar_printable(bytes(bytes_lsb).decode('utf-8', errors='ignore'))
        return txt_lsb if len(txt_lsb) > len(txt_msb) else txt_msb
    except Exception as e:
        return f"Erro ao decodificar: {e}"

def text_to_bits(text):
    """Converte string em lista de bits + terminador de 8 bytes nulos."""
    data = text.encode('utf-8') + b"\x00" * 8
    bits = []
    for byte in data:
        for i in range(7, -1, -1):  # MSB-first
            bits.append((byte >> i) & 1)
    return bits

def encode_text_in_image(img, text):
    """Esconde texto no canal azul de uma cópia da imagem."""
    img = img.convert('RGB')
    encoded = img.copy()
    pixels = encoded.load()
    bits = text_to_bits(text)
    width, height = encoded.size
    total_pixels = width * height
    if len(bits) > total_pixels:
        raise ValueError("Texto muito grande para caber nesta imagem!")
    bit_idx = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if bit_idx < len(bits):
                b = (b & ~1) | bits[bit_idx]
                bit_idx += 1
            pixels[x, y] = (r, g, b)
    return encoded

# --- Funções de ação em thread ---
def thread_acao(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper

# Variável global para armazenar o conteúdo de entrada e imagem
conteudo_entrada = ""
imagem_atual = None

@thread_acao
def acao_abrir_arquivo():
    global conteudo_entrada
    caminho = filedialog.askopenfilename(
        title='Abrir arquivo',
        filetypes=[
            ('Arquivos de texto', '*.txt'),
            ('Imagens', '*.png *.jpg *.bmp'),
            ('Todos os arquivos', '*.*')
        ]
    )
    if not caminho:
        return
    try:
        saida.delete('1.0', tk.END)
        if caminho.lower().endswith(('.png', '.jpg', '.bmp')):
            img = Image.open(caminho)
            bin_msg = ""
            for pixel in list(img.getdata()):
                for color in pixel[:3]:  # RGB
                    bin_msg += str(color & 1)  # Pegar LSB
            bin_msg = bin_msg[:len(bin_msg) - (len(bin_msg) % 8)]
            conteudo_entrada = bin_msg
            texto = binario_para_texto(bin_msg)
            saida.insert(tk.END, texto)
            status.set(f'Imagem carregada e mensagem decodificada: {caminho}')
        else:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo_entrada = f.read()
            saida.delete('1.0', tk.END)
            texto = binario_para_texto(conteudo_entrada)
            saida.insert(tk.END, texto)
            status.set(f'Arquivo de texto carregado: {caminho}')
    except Exception as e:
        messagebox.showerror('Erro ao abrir arquivo', str(e))

@thread_acao
def acao_abrir_imagem():
    global imagem_atual
    caminho = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png *.jpg *.bmp *.tiff *.webp"), ("Todos os arquivos", "*.*")]
    )
    if not caminho:
        return
    try:
        imagem_atual = Image.open(caminho).convert('RGB')
        # Exibir thumbnail
        img_display = imagem_atual.copy()
        img_display.thumbnail((400, 400), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_display)
        lbl_imagem.config(image=img_tk)
        lbl_imagem.image = img_tk
        # Decodificar texto oculto
        texto = decode_text_lsb(imagem_atual)
        saida.delete("1.0", tk.END)
        saida.insert(tk.END, texto)
        status.set(f'Imagem carregada: {caminho}')
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível processar a imagem:\n{e}")

def acao_salvar_texto():
    texto = saida.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Aviso", "Nenhum texto para salvar!")
        return
    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if caminho:
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Sucesso", f"Texto salvo em\n\n{caminho}")
            status.set(f'Texto salvo: {caminho}')
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

@thread_acao
def acao_ocultar_texto():
    global imagem_atual
    if imagem_atual is None:
        messagebox.showwarning("Aviso", "Abra uma imagem primeiro!")
        return
    texto = saida.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Aviso", "Digite algum texto na caixa antes de ocultar!")
        return
    try:
        img_encoded = encode_text_in_image(imagem_atual, texto)
        caminho = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            img_encoded.save(caminho)
            messagebox.showinfo("Sucesso", f"Texto oculto na imagem salva em\n\n{caminho}")
            status.set(f'Imagem com texto oculto salva: {caminho}')
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ocultar texto:\n{e}")

# --- GUI ---
root = tk.Tk()
root.title('Descriptografar Binário Texto e Imagems')
root.geometry("1000x850")

# Frame de botões
frm_btns = tk.Frame(root)
frm_btns.pack(fill='x', padx=10, pady=(10, 10))

btn_open = tk.Button(frm_btns, text='Abrir Arquivo Texto ou Binário na Imagems', bg="#03fc24", fg="black", command=acao_abrir_arquivo, width=33)
btn_open.pack(side='left', padx=15)

btn_abrir_imagem = tk.Button(frm_btns, text="Abrir Imagem", bg="#c5f542", fg="black", command=acao_abrir_imagem, width=20)
btn_abrir_imagem.pack(side="left", padx=15)

btn_salvar_texto = tk.Button(frm_btns, text="Salvar Texto", bg="#fcd103", fg="black", command=acao_salvar_texto, width=20)
btn_salvar_texto.pack(side="left", padx=15)

btn_ocultar_texto = tk.Button(frm_btns, text="Ocultar Texto em Imagem", bg="#03f0fc", fg="black", command=acao_ocultar_texto, width=25)
btn_ocultar_texto.pack(side="left", padx=15)

# Área principal
frame_main = tk.Frame(root)
frame_main.pack(fill="both", expand=True, padx=10, pady=10)

# Área da imagem
frame_imagem = tk.LabelFrame(frame_main, text="Imagem", width=400, height=400)
frame_imagem.pack(side="left", fill="both", expand=False, padx=5, pady=5)
frame_imagem.pack_propagate(False)

lbl_imagem = tk.Label(frame_imagem)
lbl_imagem.pack(fill="both", expand=True)

# Área do texto
frame_texto = tk.LabelFrame(frame_main, text="Saída")
frame_texto.pack(side="left", fill="both", expand=True, padx=5, pady=5)
frame_texto.pack_propagate(False)

saida = scrolledtext.ScrolledText(frame_texto, height=4, wrap=tk.WORD, font=("Arial", 12))
saida.pack(fill="both", expand=True, padx=5, pady=5)

status = tk.StringVar(value='Pronto.')
lbl_status = tk.Label(root, textvariable=status, anchor='w')
lbl_status.pack(fill='x', padx=10, pady=(0, 10))

root.minsize(700, 600)
root.mainloop()
