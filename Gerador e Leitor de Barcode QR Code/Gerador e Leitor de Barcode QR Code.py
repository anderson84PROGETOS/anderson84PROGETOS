#!/usr/bin/env python3
"""
Gerador e Leitor de Barcode / QR Code
=====================================

Permite:
 - Digitar texto ou abrir arquivo .txt
 - Gerar barcode Code128
 - Gerar QR Code
 - Salvar códigos como imagem
 - Abrir imagem (barcode ou QR) e decodificar texto
 - Suporte extra para interpretação de boletos

Dependências:
    pip install pillow
    pip install python-barcode
    pip install pyzbar
    pip install qrcode[pil]

⚠️ Importante:
 - O pyzbar precisa do ZBar instalado no sistema:
   • Windows: https://github.com/NaturalHistoryMuseum/pyzbar/wiki/Installation
   • Linux (Debian/Ubuntu): sudo apt-get install libzbar0
   • Mac (brew): brew install zbar
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from io import BytesIO
from PIL import Image, ImageTk
import barcode
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode
import qrcode   

# ---------- Funções de Barcode ----------
def generate_code128_image(data: str, width: int = 800, height: int = 200) -> Image.Image:
    """Gera uma imagem de barcode Code128 a partir de texto."""
    CODE128 = barcode.get_barcode_class('code128')
    writer = ImageWriter()
    options = {
        'module_width': 0.2,
        'module_height': 15.0,
        'font_size': 10,
        'text_distance': 2.0,
        'quiet_zone': 6.5,
    }
    bar = CODE128(data, writer=writer)
    fp = BytesIO()
    bar.write(fp, options=options)
    fp.seek(0)
    img = Image.open(fp).convert('RGBA')
    resized = img.resize((max(1, width), max(1, height)), Image.LANCZOS)
    final = Image.new('RGBA', resized.size, (255, 255, 255, 255))
    final.paste(resized, (0, 0), resized)
    return final.convert('RGB')

def generate_qrcode_image(data: str, size: int = 400) -> Image.Image:
    """Gera uma imagem de QR Code a partir de texto."""
    qr = qrcode.QRCode(
        version=None,  # ajusta automaticamente
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.LANCZOS)

def decode_barcode_image(path: str) -> str:
    """Decodifica o conteúdo de um barcode/QR a partir de uma imagem."""
    try:
        img = Image.open(path)
        decoded = decode(img)
        if not decoded:
            return "<nenhum código encontrado>"
        return decoded[0].data.decode("utf-8")
    except Exception as e:
        return f"<erro ao decodificar: {e}>"

def interpretar_codigo_boleto(codigo: str) -> str:
    """Interpreta valor de boletos com código iniciando com 846 (exemplo)."""
    if codigo.startswith("846") and len(codigo) >= 20:
        valor_str = codigo[8:12]  # Pega 4 dígitos que representam centavos
        valor_centavos = int(valor_str)
        valor = valor_centavos / 50.0
        return f"Total a pagar\t{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ""

# ---------- Interface gráfica ----------
class BarcodeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador e Leitor de Barcode QR Code")
        self.geometry("950x870")

        # Entrada de texto
        ttk.Label(self, text="Digite texto para gerar código").pack(pady=10)
        self.txt_input = tk.Text(self, height=10, wrap='word')
        self.txt_input.pack(pady=5)

        # Botões principais
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Gerar Code128", command=self.on_generate_code128).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="Salvar Code128", command=self.on_save_barcode).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="Gerar QR Code", command=self.on_generate_qrcode).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="Salvar QR Code", command=self.on_save_qrcode).pack(side='left', padx=4)

        ttk.Button(btn_frame, text="Abrir imagem (decodificar)", command=self.on_open_image).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="Abrir arquivo .txt", command=self.on_open_txt).pack(side='left', padx=4)

        # Canvas para mostrar o código
        ttk.Label(self, text="Pré-visualização do código gerado").pack(pady=8)
        self.canvas = tk.Canvas(self, width=500, height=300, bg="white")
        self.canvas.pack(padx=8, pady=6)

        # Texto decodificado
        ttk.Label(self, text="Texto decodificado da imagem / arquivo").pack(pady=8)
        self.txt_output = tk.Text(self, height=10, wrap='word')
        self.txt_output.pack(pady=4)

        # Configuração de tamanho do Code128
        opts = ttk.Frame(self)
        opts.pack(pady=6)
        ttk.Label(opts, text="Width (px)").grid(row=0, column=0, sticky='w')
        self.ent_w = ttk.Entry(opts, width=6)
        self.ent_w.grid(row=0, column=1, padx=4)
        self.ent_w.insert(0, "800")

        ttk.Label(opts, text="Height (px)").grid(row=0, column=2, sticky='w')
        self.ent_h = ttk.Entry(opts, width=6)
        self.ent_h.grid(row=0, column=3, padx=4)
        self.ent_h.insert(0, "200")

        self._current_img = None

    # ---------- Eventos ----------
    def on_generate_code128(self):
        txt = self.txt_input.get("1.0", "end").strip()
        if not txt:
            messagebox.showwarning("Aviso", "Digite algum texto para gerar o barcode.")
            return
        try:
            w = int(self.ent_w.get())
            h = int(self.ent_h.get())
        except:
            w, h = 800, 200

        img = generate_code128_image(txt, w, h)
        self._current_img = img
        self.show_on_canvas(img)

    def on_generate_qrcode(self):
        txt = self.txt_input.get("1.0", "end").strip()
        if not txt:
            messagebox.showwarning("Aviso", "Digite algum texto para gerar o QR Code.")
            return
        img = generate_qrcode_image(txt, 400)
        self._current_img = img
        self.show_on_canvas(img)

    def show_on_canvas(self, img: Image.Image):
        disp = img.copy()
        disp.thumbnail((500, 300), Image.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(250, 150, image=self._tkimg)

    def on_save_barcode(self):
        if self._current_img is None:
            messagebox.showinfo("Info", "Nenhum código gerado ainda.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if not path:
            return
        self._current_img.save(path)
        messagebox.showinfo("Salvo", f"Imagem salva em: {path}")

    def on_save_qrcode(self):
        self.on_save_barcode()

    def on_open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not path:
                return
        try:
            img = Image.open(path).convert("RGB")
            self._current_img = img
            self.show_on_canvas(img)   # <-- mostra a imagem no canvas
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem: {e}")
            return

        text = decode_barcode_image(path)
        self.show_result(text)    

    def on_open_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir arquivo: {e}")
            return
        self.txt_input.delete("1.0", "end")
        self.txt_input.insert("end", text)
        self.show_result(text)

    def show_result(self, text: str):
        self.txt_output.delete("1.0", "end")
        extra = interpretar_codigo_boleto(text)
        if extra:
            self.txt_output.insert("end", f"Código lido\n\n{text}  {extra}")
        else:
            self.txt_output.insert("end", f"Código lido\n\n{text}")

# ---------- Executar aplicação ----------
if __name__ == "__main__":
    app = BarcodeApp()
    app.mainloop()
