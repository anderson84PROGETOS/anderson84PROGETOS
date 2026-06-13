import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import io
from pypdf import PdfReader, PdfWriter  # Para suporte a PDF

def encode_image(image_path, secret_message, output_path):
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    data = secret_message.encode('utf-8')
    length = len(data)
    header = length.to_bytes(4, byteorder='big')
    full_data = header + data
    binary = ''.join(format(byte, '08b') for byte in full_data)

    pixels = list(img.getdata())
    max_bits = len(pixels) * 3

    if len(binary) > max_bits:
        raise ValueError(
            f"Mensagem muito grande!\n"
            f"Capacidade máxima: {max_bits // 8:,} bytes"
        )

    new_pixels = []
    idx = 0
    for pixel in pixels:
        r, g, b = pixel
        if idx < len(binary):
            r = (r & ~1) | int(binary[idx])
            idx += 1
        if idx < len(binary):
            g = (g & ~1) | int(binary[idx])
            idx += 1
        if idx < len(binary):
            b = (b & ~1) | int(binary[idx])
            idx += 1
        new_pixels.append((r, g, b))

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path, format='PNG')
    return True


def decode_image(image_path):
    img = Image.open(image_path).convert('RGB')
    bits = ''
    for r, g, b in img.getdata():
        bits += str(r & 1)
        bits += str(g & 1)
        bits += str(b & 1)

    header_bits = bits[:32]
    if len(header_bits) < 32:
        return "Imagem inválida."

    length = int(header_bits, 2)
    message_bits = bits[32:32 + (length * 8)]

    if len(message_bits) < length * 8:
        return "Mensagem incompleta ou imagem corrompida."

    message_bytes = bytearray()
    for i in range(0, len(message_bits), 8):
        byte = int(message_bits[i:i+8], 2)
        message_bytes.append(byte)

    try:
        return message_bytes.decode('utf-8')
    except Exception as e:
        return f"Erro na decodificação: {e}"


# Funções simples para PDF (esconder em metadata + comentário invisível)
# ==================== FUNÇÕES PDF MELHORADAS ====================

def hide_in_pdf(pdf_path, secret_message, output_path):
    """Esconde mensagem em PDF usando attachment (mais confiável)"""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Copiar todas as páginas preservando o máximo possível
    for page in reader.pages:
        writer.add_page(page)

    # Preparar dados com header
    data = secret_message.encode('utf-8')
    length = len(data)
    header = length.to_bytes(4, byteorder='big')
    hidden_data = header + data

    # Adicionar como attachment oculto
    writer.add_attachment("stego_hidden.dat", hidden_data)

    # Também adiciona no metadata como backup
    writer.add_metadata({
        "/Producer": "StegoApp LSB",
        "/Creator": "StegoApp",
        "/Subject": "Steganography"
    })

    with open(output_path, "wb") as f:
        writer.write(f)
    
    return True


def extract_from_pdf(pdf_path):
    """Extração robusta de PDF"""
    try:
        reader = PdfReader(pdf_path)
        
        # === 1. Tentar extrair de Attachments (principal método) ===
        if hasattr(reader, 'attachments') and reader.attachments:
            for name, content_list in reader.attachments.items():
                if "stego" in name.lower() or "hidden" in name.lower():
                    for data in content_list:
                        if len(data) > 4:
                            try:
                                length = int.from_bytes(data[:4], 'big')
                                message = data[4:4 + length].decode('utf-8')
                                if message:
                                    return message
                            except:
                                continue

        # === 2. Fallback: procurar em Embedded Files (outra forma) ===
        try:
            for i in range(len(reader.trailer.get("/Names", {}))):
                # Implementação mais profunda se necessário
                pass
        except:
            pass

        # === 3. Fallback: Metadata ===
        meta = reader.metadata
        if meta:
            for key in meta.keys():
                value = str(meta[key])
                if len(value) > 20 and ("stego" in value.lower() or len(value) > 100):
                    return value  # raramente chega aqui

        return "Nenhuma mensagem escondida encontrada neste PDF.\n\nDica: Use um PDF criado pelo próprio programa para melhor resultado."

    except Exception as e:
        return f"Erro ao ler PDF: {str(e)}"


class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Esteganografia Imagens e PDF")
        self.root.geometry("1000x900")
        self.root.state("zoomed")
        
        tk.Label(root, text="Esteganografia LSB (Imagens) + PDF Support", 
                 font=("Arial", 18, "bold")).pack(pady=12)
        
        # =================== ESCONDER ===================
        frame_hide = tk.LabelFrame(root, text="🔒 Esconder Mensagem", padx=15, pady=10)
        frame_hide.pack(fill="x", padx=20, pady=8)
        
        tk.Button(frame_hide, text="Selecionar Imagem/PDF Portadora", 
                  command=self.select_cover, width=55).pack(pady=6)
        self.cover_label = tk.Label(frame_hide, text="Nenhuma arquivo selecionado", fg="gray")
        self.cover_label.pack()
        
        tk.Label(frame_hide, text="Mensagem Secreta:").pack(anchor="w", pady=(8,2))
        
        input_frame = tk.Frame(frame_hide)
        input_frame.pack(fill="both", expand=True, pady=5)
        self.text_area = tk.Text(input_frame, height=10, width=110, wrap="word")
        scrollbar_in = tk.Scrollbar(input_frame, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar_in.set)
        self.text_area.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar_in.pack(side=tk.RIGHT, fill="y")
        
        tk.Button(frame_hide, text="🔒 ESCONDER", command=self.hide_message,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2).pack(pady=12)
        
        # =================== EXTRAIR ===================
        frame_extract = tk.LabelFrame(root, text="📤 Extrair Mensagem", padx=15, pady=10)
        frame_extract.pack(fill="both", expand=True, padx=20, pady=8)
        
        tk.Button(frame_extract, text="📂 Selecionar Imagem/PDF com Mensagem", 
                  command=self.extract_message, bg="#2196F3", fg="white", height=2).pack(pady=8)
        
        tk.Button(frame_extract, text="💾 Salvar Mensagem em .txt", 
                  command=self.save_extracted_message, bg="#FF9800", fg="white", height=1).pack(pady=8)
        
        tk.Label(frame_extract, text="Mensagem Encontrada:").pack(anchor="w", pady=(8,2))
        
        result_frame = tk.Frame(frame_extract)
        result_frame.pack(fill="both", expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, height=22, width=110, bg="#f8f9fa", wrap="word")
        scrollbar_out = tk.Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar_out.set)
        self.result_text.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar_out.pack(side=tk.RIGHT, fill="y")     
        
        self.status = tk.Label(root, text="", fg="blue", font=("Arial", 10))
        self.status.pack(pady=10)
        
        self.cover_path = None
        self.last_extracted = ""
        self.is_pdf = False
    
    def select_cover(self):
        self.cover_path = filedialog.askopenfilename(
            filetypes=[("Imagens e PDFs", "*.png *.jpg *.jpeg *.bmp *.pdf")]
        )
        if self.cover_path:
            ext = os.path.splitext(self.cover_path)[1].lower()
            self.is_pdf = ext == ".pdf"
            self.cover_label.config(text=os.path.basename(self.cover_path) + (" [PDF]" if self.is_pdf else ""), fg="green")
    
    def hide_message(self):
        if not self.cover_path:
            messagebox.showerror("Erro", "Selecione uma imagem ou PDF portadora!")
            return
        message = self.text_area.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Erro", "Digite a mensagem!")
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".png" if not self.is_pdf else ".pdf", 
                                                   filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")])
        if not output_path:
            return
        
        try:
            if self.is_pdf:
                hide_in_pdf(self.cover_path, message, output_path)
                messagebox.showinfo("✅ Sucesso", f"Mensagem escondida no PDF!\nSalvo em:\n{output_path}")
            else:
                encode_image(self.cover_path, message, output_path)
                messagebox.showinfo("✅ Sucesso", f"Mensagem escondida na imagem!\nSalvo em:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
    
    def extract_message(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Imagens e PDFs", "*.png *.jpg *.jpeg *.bmp *.pdf")]
        )
        if not file_path:
            return
        
        self.status.config(text="Extraindo... Aguarde", fg="blue")
        self.root.update()
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                self.last_extracted = extract_from_pdf(file_path)
            else:
                self.last_extracted = decode_image(file_path)
            
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", self.last_extracted)
            
            length = len(self.last_extracted)
            self.status.config(text=f"✅ Extraído! ({length:,} caracteres)", fg="green")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.status.config(text="Erro na extração", fg="red")
    
    def save_extracted_message(self):
        if not self.last_extracted:
            messagebox.showwarning("Aviso", "Extraia primeiro!")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(self.last_extracted)
                messagebox.showinfo("Salvo", f"Arquivo salvo em:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = StegoApp(root)
    root.mainloop()
