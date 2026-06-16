import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import time
from PIL import Image
import warnings
import os
import zlib

warnings.filterwarnings("ignore", category=DeprecationWarning)


# ================== FUNÇÕES CORE ==================
def encode_lsb(image_path, message, output_path, compatible_mode=False):
    try:
        img = Image.open(image_path).convert('RGB')
        pixels = list(img.getdata())
        
        if compatible_mode:
            # Modo compatível com o site (texto puro)
            data_to_hide = (message + '<<<END>>>').encode('utf-8')
        else:
            # Nosso modo (com compressão)
            compressed = zlib.compress(message.encode('utf-8'), level=9)
            data_to_hide = compressed + b'<<<END>>>'
        
        binary_message = ''.join(format(byte, '08b') for byte in data_to_hide)
        max_bits = len(pixels) * 3
        
        if len(binary_message) > max_bits:
            max_bytes = max_bits // 8
            raise ValueError(f"Mensagem muito grande!\nCapacidade máxima ≈ {max_bytes:,} bytes")
        
        encoded_pixels = []
        index = 0
        for pixel in pixels:
            r, g, b = pixel
            if index < len(binary_message):
                r = (r & ~1) | int(binary_message[index])
                index += 1
            if index < len(binary_message):
                g = (g & ~1) | int(binary_message[index])
                index += 1
            if index < len(binary_message):
                b = (b & ~1) | int(binary_message[index])
                index += 1
            encoded_pixels.append((r, g, b))
        
        new_img = Image.new('RGB', img.size)
        new_img.putdata(encoded_pixels)
        new_img.save(output_path)
        return True, "Modo: " + ("Compatível com Site" if compatible_mode else "Com Compressão")
    
    except Exception as e:
        return False, str(e)


def decode_lsb_compatible(image_path):
    """Decode otimizado para o site stylesuxx"""
    try:
        img = Image.open(image_path).convert('RGB')
        pixels = list(img.getdata())
        binary_message = ''.join(str(r & 1) + str(g & 1) + str(b & 1) for r, g, b in pixels)
        
        # Tenta vários marcadores comuns
        markers = [b'<<<END>>>', b'###END###', b'END']
        for marker in markers:
            marker_bin = ''.join(format(byte, '08b') for byte in marker)
            if marker_bin in binary_message:
                message_bin = binary_message.split(marker_bin)[0]
                try:
                    data = bytes(int(message_bin[i:i+8], 2) for i in range(0, len(message_bin), 8))
                    # Tenta descomprimir (caso seja nosso método)
                    try:
                        return zlib.decompress(data).decode('utf-8', errors='replace')
                    except:
                        return data.decode('utf-8', errors='replace')
                except:
                    pass
        
        # Fallback: extrai caracteres imprimíveis
        message = ''
        for i in range(0, len(binary_message)-7, 8):
            byte_str = binary_message[i:i+8]
            try:
                char = chr(int(byte_str, 2))
                if 32 <= ord(char) <= 126 or char in '\n\r\t ':
                    message += char
                elif len(message) > 40 and not char.isprintable():
                    break
            except:
                break
        return message.strip() if len(message.strip()) > 5 else None
    except:
        return None


# ================== INTERFACE ==================
class HackerSteganography:
    def __init__(self, root):
        self.root = root
        self.root.title("Esteganografia STEALTH-ENCODE v2.9 - Compatível com Stylesuxx")
        self.root.configure(bg="#0a0a0a")
        self.root.state("zoomed")
        
        self.root.option_add('*Font', 'Consolas 10')
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.create_widgets()
    
    def create_widgets(self):
        header = tk.Frame(self.root, bg="#000000", height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="STEALTH-ENCODE", 
                        font=("Consolas", 32, "bold"), fg="#00ff41", bg="#000000")
        title.pack(pady=10)
        
        subtitle = tk.Label(header, text="LSB STEGANOGRAPHY // MODO COMPATÍVEL COM STYLESUXX", 
                           font=("Consolas", 12), fg="#00ff41", bg="#000000")
        subtitle.pack()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.tab_encode = tk.Frame(self.notebook, bg="#0a0a0a")
        self.tab_decode = tk.Frame(self.notebook, bg="#0a0a0a")
        
        self.notebook.add(self.tab_encode, text="  CODIFICAR  ")
        self.notebook.add(self.tab_decode, text="  DECODIFICAR  ")
        
        self.create_encode_tab()
        self.create_decode_tab()
        
        self.status = tk.Label(self.root, text="PRONTO • Aguardando alvo...", 
                              fg="#00ff41", bg="#111111", anchor="w", font=("Consolas", 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.X, ipady=6, padx=10)
    
    def create_encode_tab(self):
        frame = tk.Frame(self.tab_encode, bg="#0a0a0a")
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        tk.Label(frame, text="SELECIONE O ALVO (IMAGEM)", font=("Consolas", 14, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(anchor="w")
        
        self.img_path_var = tk.StringVar()
        path_frame = tk.Frame(frame, bg="#0a0a0a")
        path_frame.pack(fill=tk.X, pady=8)
        
        tk.Entry(path_frame, textvariable=self.img_path_var, bg="#1a1a1a", fg="#00ff41", 
                insertbackground="#00ff41", font=("Consolas", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(path_frame, text="BROWSE", command=self.browse_image_encode, 
                 bg="#003300", fg="#00ff41", font=("Consolas", 10)).pack(side=tk.RIGHT, padx=5)
        
        tk.Label(frame, text="MENSAGEM A OCULTAR", font=("Consolas", 14, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(anchor="w", pady=(20,5))
        
        self.message_text = scrolledtext.ScrolledText(frame, height=12, bg="#0f0f0f", 
                                                     fg="#00ff41", insertbackground="#00ff41", 
                                                     font=("Consolas", 11))
        self.message_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Modo Compatível
        self.compat_var = tk.BooleanVar(value=True)
        compat_frame = tk.Frame(frame, bg="#0a0a0a")
        compat_frame.pack(fill=tk.X, pady=8)
        tk.Checkbutton(compat_frame, text="🔄 Modo Compatível com Stylesuxx (RECOMENDADO)", 
                      variable=self.compat_var, bg="#0a0a0a", fg="#00ff41", 
                      selectcolor="#003300", font=("Consolas", 10)).pack(anchor="w")
        
        out_frame = tk.Frame(frame, bg="#0a0a0a")
        out_frame.pack(fill=tk.X, pady=10)
        tk.Label(out_frame, text="NOME DO ARQUIVO DE SAÍDA", fg="#00ff41", bg="#0a0a0a", 
                font=("Consolas", 10)).pack(anchor="w")
        self.output_name = tk.Entry(out_frame, bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41")
        self.output_name.insert(0, "ghost_payload.png")
        self.output_name.pack(fill=tk.X, pady=5)
        
        self.encode_btn = tk.Button(frame, text="EXECUTAR CODIFICAÇÃO", font=("Consolas", 15, "bold"),
                                  bg="#003300", fg="#00ff41", height=2, command=self.start_encoding)
        self.encode_btn.pack(pady=20)
    
    def create_decode_tab(self):
        frame = tk.Frame(self.tab_decode, bg="#0a0a0a")
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        tk.Label(frame, text="SELECIONE A IMAGEM COM PAYLOAD", font=("Consolas", 14, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(anchor="w")
        
        self.decode_img_path = tk.StringVar()
        path_frame = tk.Frame(frame, bg="#0a0a0a")
        path_frame.pack(fill=tk.X, pady=8)
        
        tk.Entry(path_frame, textvariable=self.decode_img_path, bg="#1a1a1a", fg="#00ff41", 
                insertbackground="#00ff41", font=("Consolas", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(path_frame, text="BROWSE", command=self.browse_image_decode, 
                 bg="#003300", fg="#00ff41", font=("Consolas", 10)).pack(side=tk.RIGHT, padx=5)
        
        self.decode_btn = tk.Button(frame, text="EXTRAIR MENSAGEM OCULTA", font=("Consolas", 15, "bold"),
                                  bg="#003300", fg="#00ff41", height=2, command=self.start_decoding)
        self.decode_btn.pack(pady=25)
        
        tk.Label(frame, text="MENSAGEM EXTRAÍDA:", font=("Consolas", 12, "bold"), 
                fg="#00ff41", bg="#0a0a0a").pack(anchor="w")
        
        self.result_text = scrolledtext.ScrolledText(frame, height=18, bg="#0f0f0f", 
                                                    fg="#00ff41", font=("Consolas", 11))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # ================== FUNÇÕES ==================
    def browse_image_encode(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.img_path_var.set(path)
    
    def browse_image_decode(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.decode_img_path.set(path)
    
    def update_status(self, text):
        self.status.config(text=f"[{time.strftime('%H:%M:%S')}] {text}")
        self.root.update_idletasks()
    
    def start_encoding(self):
        threading.Thread(target=self.encode_message, daemon=True).start()
    
    def start_decoding(self):
        threading.Thread(target=self.decode_message, daemon=True).start()
    
    def encode_message(self):
        self.encode_btn.config(state="disabled", text="PROCESSANDO...")
        self.update_status("Injetando payload...")
        
        img_path = self.img_path_var.get()
        message = self.message_text.get("1.0", tk.END).strip()
        
        if not img_path or not message:
            messagebox.showerror("ERRO", "Selecione imagem e mensagem!")
            self.encode_btn.config(state="normal", text="EXECUTAR CODIFICAÇÃO")
            return
        
        output_name = self.output_name.get().strip() or "ghost_payload.png"
        output_path = os.path.join(os.path.dirname(img_path), output_name)
        
        success, info = encode_lsb(img_path, message, output_path, self.compat_var.get())
        
        if success:
            self.update_status(f"PAYLOAD INJETADO → {output_name}")
            messagebox.showinfo("SUCESSO", f"Codificado com sucesso!\n\nSalvo em:\n{output_path}\n\n{info}")
        else:
            messagebox.showerror("FALHA", f"Erro:\n{info}")
        
        self.encode_btn.config(state="normal", text="EXECUTAR CODIFICAÇÃO")
    
    def decode_message(self):
        self.decode_btn.config(state="disabled", text="EXTRAINDO...")
        self.update_status("Escaneando imagem...")
        
        img_path = self.decode_img_path.get()
        if not img_path:
            messagebox.showerror("ERRO", "Selecione uma imagem!")
            self.decode_btn.config(state="normal", text="EXTRAIR MENSAGEM OCULTA")
            return
        
        message = decode_lsb_compatible(img_path)
        
        self.result_text.delete("1.0", tk.END)
        if message and len(message.strip()) > 5:
            self.result_text.insert(tk.END, message)
            self.update_status("PAYLOAD EXTRAÍDO COM SUCESSO")
            messagebox.showinfo("SUCESSO", "Mensagem recuperada!")
        else:
            self.result_text.insert(tk.END, "Nenhum payload claro detectado.")
            messagebox.showwarning("AVISO", "Não foi possível extrair uma mensagem clara.")
        
        self.decode_btn.config(state="normal", text="EXTRAIR MENSAGEM OCULTA")


# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    root = tk.Tk()
    app = HackerSteganography(root)
    root.mainloop()
