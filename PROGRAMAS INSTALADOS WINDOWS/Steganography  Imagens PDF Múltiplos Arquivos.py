import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import fitz  # PyMuPDF
import os
from pathlib import Path
import zlib

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StegoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Steganography - Imagens & PDF (Múltiplos Arquivos)")
        self.geometry("1000x750")
        self.after(100, lambda: self.state("zoomed"))
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.create_image_batch_encode()
        self.create_image_batch_decode()
        self.create_pdf_tab()

    # ====================== ESCONDER EM IMAGENS (Lote) ======================
    def create_image_batch_encode(self):
        frame = ctk.CTkFrame(self.tabview.add("Esconder em Várias Imagens"))
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Selecione Várias Imagens (PNG, JPG, etc)",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
       
        self.img_paths_encode = []
        self.label_files = ctk.CTkLabel(frame, text="Nenhum arquivo selecionado", text_color="gray")
        self.label_files.pack(pady=5)
        
        ctk.CTkButton(frame, text="Selecionar Imagens", fg_color="#28a745", hover_color="#218838", 
                     text_color="black", font=ctk.CTkFont(size=14, weight="bold"), 
                     command=self.choose_multiple_images).pack(pady=5)
        
        ctk.CTkLabel(frame, text="Mensagem Secreta:", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.text_encode = ctk.CTkTextbox(frame, height=590)
        self.text_encode.pack(padx=20, pady=5, fill="x")
        
        ctk.CTkButton(frame, text="Esconder em Todas as Imagens", fg_color="#fd950d", 
                     hover_color="#d7560b", text_color="black", 
                     font=ctk.CTkFont(size=14, weight="bold"), height=40, 
                     command=self.encode_multiple_images).pack(pady=15)

    def choose_multiple_images(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp")])
        self.img_paths_encode = list(files)
        self.label_files.configure(text=f"{len(files)} imagem(ns) selecionada(s)")

    def encode_multiple_images(self):
        if not self.img_paths_encode:
            messagebox.showerror("Erro", "Selecione pelo menos uma imagem!")
            return
        
        message = self.text_encode.get("1.0", "end").strip()
        if not message:
            messagebox.showerror("Erro", "Digite uma mensagem!")
            return
        
        output_folder = filedialog.askdirectory(title="Escolha pasta para salvar as imagens modificadas")
        if not output_folder:
            return
        
        success = 0
        for img_path in self.img_paths_encode:
            try:
                img = Image.open(img_path).convert("RGB")
                encoded = self.lsb_encode(img, message)
                filename = Path(img_path).stem + ".png"
                save_path = os.path.join(output_folder, "stego_" + filename)
                encoded.save(save_path, format="PNG")
                success += 1
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar {Path(img_path).name}:\n{str(e)}")
        
        messagebox.showinfo("Sucesso", f"Pronto!\n{success}/{len(self.img_paths_encode)} imagens processadas.")

    # ====================== FUNÇÕES LSB ======================
    def lsb_encode(self, image, message):
        image = image.convert("RGB")
        compressed = zlib.compress(message.encode('utf-8'), level=9)
        data_to_hide = compressed + b'<<<END>>>'
        binary = ''.join(format(byte, '08b') for byte in data_to_hide)
        
        pixels = list(image.getdata())
        max_bits = len(pixels) * 3
        
        if len(binary) > max_bits:
            max_bytes = max_bits // 8
            raise ValueError(f"Mensagem muito grande!\nCapacidade máxima ≈ {max_bytes:,} bytes")

        new_pixels = []
        bit_index = 0
        for pixel in pixels:
            r, g, b = pixel
            if bit_index < len(binary):
                r = (r & ~1) | int(binary[bit_index])
                bit_index += 1
            if bit_index < len(binary):
                g = (g & ~1) | int(binary[bit_index])
                bit_index += 1
            if bit_index < len(binary):
                b = (b & ~1) | int(binary[bit_index])
                bit_index += 1
            new_pixels.append((r, g, b))
        
        encoded_img = Image.new("RGB", image.size)
        encoded_img.putdata(new_pixels)
        return encoded_img

    def lsb_decode(self, image):
        image = image.convert("RGB")
        pixels = list(image.getdata())
        bits = [str(p[0] & 1) + str(p[1] & 1) + str(p[2] & 1) for p in pixels]
        binary = ''.join(bits)
        
        data = bytearray()
        for i in range(0, len(binary) - 7, 8):
            byte = binary[i:i+8]
            data.append(int(byte, 2))
        
        try:
            end_pos = data.find(b'<<<END>>>')
            if end_pos != -1:
                compressed = data[:end_pos]
                decompressed = zlib.decompress(compressed)
                return decompressed.decode('utf-8')
        except Exception:
            pass
        return ""

    # ====================== EXTRAIR DE IMAGENS ======================
    def create_image_batch_decode(self):
        frame = ctk.CTkFrame(self.tabview.add("Extrair de Várias Imagens"))
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Selecione as Imagens com Mensagem Escondida", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
       
        self.img_paths_decode = []
        self.label_decode = ctk.CTkLabel(frame, text="Nenhum arquivo selecionado", text_color="gray")
        self.label_decode.pack(pady=5)
        
        ctk.CTkButton(frame, text="Selecionar Imagens", fg_color="#08ee3a", hover_color="#08960f", 
                     text_color="black", font=ctk.CTkFont(size=14, weight="bold"), 
                     command=self.choose_multiple_decode).pack(pady=5)
        
        ctk.CTkButton(frame, text="Extrair Mensagens", fg_color="orange", hover_color="#FF8C00", 
                     text_color="black", font=ctk.CTkFont(size=14, weight="bold"), 
                     command=self.decode_multiple_images).pack(pady=15)
        
        ctk.CTkButton(frame, text="Salvar Resultado em TXT", fg_color="#0d6efd", hover_color="#0b5ed7", 
                     text_color="black", font=ctk.CTkFont(size=14, weight="bold"), 
                     command=self.save_image_results).pack(pady=5)
        
        self.result_text = ctk.CTkTextbox(frame, height=300)
        self.result_text.pack(padx=20, pady=10, fill="both", expand=True)

    def choose_multiple_decode(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp")])
        self.img_paths_decode = list(files)
        self.label_decode.configure(text=f"{len(files)} imagem(ns) selecionada(s)")

    def decode_multiple_images(self):
        if not self.img_paths_decode:
            messagebox.showerror("Erro", "Selecione imagens!")
            return
        
        self.result_text.delete("1.0", "end")
        results = []
        for path in self.img_paths_decode:
            try:
                img = Image.open(path)
                msg = self.lsb_decode(img)
                if msg.strip():
                    results.append(f"✅ {Path(path).name}\n\n{msg}\n")
                else:
                    results.append(f"❌ {Path(path).name}: Nenhuma mensagem encontrada")
            except Exception as e:
                results.append(f"⚠️ Erro em {Path(path).name}: {e}")
        
        self.result_text.insert("1.0", "\n\n".join(results))

    def save_image_results(self):
        content = self.result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo TXT", "*.txt")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Resultado salvo em:\n{filename}")

    # ====================== PDF ======================
    def create_pdf_tab(self):
        frame = ctk.CTkFrame(self.tabview.add("PDF"))
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Operações com PDF", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkButton(frame, text="Esconder Mensagem no PDF", height=40, 
                     fg_color="#28a745", hover_color="#218838", text_color="black", 
                     font=ctk.CTkFont(size=14, weight="bold"), command=self.encode_pdf).pack(pady=8)
        
        ctk.CTkButton(frame, text="Extrair Mensagem do PDF", height=40, 
                     fg_color="#FFA500", hover_color="#FF8C00", text_color="black", 
                     font=ctk.CTkFont(size=14, weight="bold"), command=self.decode_pdf).pack(pady=8)
        
        ctk.CTkButton(frame, text="Salvar Resultado em TXT", fg_color="#0d6efd", 
                     hover_color="#0b5ed7", text_color="black", 
                     font=ctk.CTkFont(size=14, weight="bold"), command=self.save_pdf_results).pack(pady=5)
        
        self.pdf_result = ctk.CTkTextbox(frame, height=250)
        self.pdf_result.pack(padx=20, pady=15, fill="both", expand=True)

    def encode_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not pdf_path:
            return
        message = self.get_pdf_message()
        if not message:
            return
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata or {}
            metadata["subject"] = message
            doc.set_metadata(metadata)
            
            save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if save_path:
                doc.save(save_path)
                messagebox.showinfo("Sucesso", "Mensagem escondida no PDF com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            if 'doc' in locals():
                doc.close()

    def get_pdf_message(self):
        win = ctk.CTkToplevel(self)
        win.title("Mensagem para PDF")
        win.geometry("800x500")
        win.after(100, lambda: win.state("zoomed"))  # ← Maximiza
        
        ctk.CTkLabel(win, text="Digite a mensagem secreta:").pack(pady=10)
        
        textbox = ctk.CTkTextbox(win, width=750, height=350)
        textbox.pack(padx=20, pady=10, fill="both", expand=True)
        
        result = {"text": None}
        
        def salvar():
            result["text"] = textbox.get("1.0", "end").strip()
            win.destroy()
        
        ctk.CTkButton(win, text="Salvar Mensagem", command=salvar, height=40).pack(pady=10)
        
        win.grab_set()
        self.wait_window(win)
        return result["text"]

    def decode_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not pdf_path:
            return
        try:
            doc = fitz.open(pdf_path)
            msg = doc.metadata.get("subject", "") if doc.metadata else ""
            self.pdf_result.delete("1.0", "end")
            if msg.strip():
                self.pdf_result.insert("1.0", f"Mensagem Encontrada no PDF\n\n{msg}")
            else:
                self.pdf_result.insert("1.0", "Nenhuma mensagem encontrada no campo 'subject'.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            if 'doc' in locals():
                doc.close()

    def save_pdf_results(self):
        content = self.pdf_result.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo TXT", "*.txt")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Resultado salvo em:\n{filename}")


if __name__ == "__main__":
    app = StegoApp()
    app.mainloop()
