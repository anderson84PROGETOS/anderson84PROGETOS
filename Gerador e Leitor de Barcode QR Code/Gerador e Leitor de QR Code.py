import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from PIL import Image, ImageTk
import qrcode
import cv2

# ---------- Funções ----------
def generate_qrcode_image(data: str, size: int = 400) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.LANCZOS)

def read_qrcode_image(path: str) -> tuple[str, Image.Image]:
    """Lê QR Code de uma imagem e retorna o texto + imagem PIL."""
    img_cv = cv2.imread(path)
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img_cv)
    if not data:
        raise ValueError("Nenhum QR Code encontrado nesta imagem.")
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    return data, img_pil

# ---------- Interface gráfica ----------
class QRCodeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador e Leitor de QR Code")
        self.geometry("490x870")

        ttk.Label(self, text="Digite texto para gerar QR Code").pack(pady=10)
        self.txt_input = scrolledtext.ScrolledText(self, width=50, height=6)
        self.txt_input.pack(pady=5)

        tk.Button(self, text="Gerar QR Code", bg="#03fc24", fg="black", command=self.on_generate_qrcode).pack(pady=10)
        tk.Button(self, text="Salvar QR Code", bg="#fca103", fg="black", command=self.on_save_image).pack(pady=5)
        tk.Button(self, text="Ler QR Code de imagem", bg="#03f0fc", fg="black", command=self.on_read_qrcode).pack(pady=5)

        ttk.Label(self, text="Pré-visualização do QR Code").pack(pady=8)
        self.canvas = tk.Canvas(self, width=400, height=400, bg="white")
        self.canvas.pack(padx=8, pady=6)

        ttk.Label(self, text="Conteúdo do QR Code Lido").pack(pady=8)
        self.txt_output = scrolledtext.ScrolledText(self, width=50, height=5)
        self.txt_output.pack(pady=5)

        self._current_img = None

    def on_generate_qrcode(self):
        txt = self.txt_input.get("1.0", "end").strip()
        if not txt:
            tk.messagebox.showwarning("Aviso", "Digite algum texto para gerar o QR Code.")
            return
        img = generate_qrcode_image(txt, 400)
        self._current_img = img
        self.show_on_canvas(img)

    def show_on_canvas(self, img: Image.Image):
        disp = img.copy()
        disp.thumbnail((400, 400), Image.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(200, 200, image=self._tkimg)

    def on_save_image(self):
        if self._current_img is None:
            tk.messagebox.showinfo("Info", "Nenhum QR Code gerado ainda.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if not path:
            return
        self._current_img.save(path)
        tk.messagebox.showinfo("Salvo", f"QR Code salvo em: {path}")

    def on_read_qrcode(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        try:
            data, img = read_qrcode_image(path)
            self._current_img = img
            self.show_on_canvas(img)
            # Exibe o conteúdo no scrolled text
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", data)
        except Exception as e:
            tk.messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    app = QRCodeApp()
    app.mainloop()
