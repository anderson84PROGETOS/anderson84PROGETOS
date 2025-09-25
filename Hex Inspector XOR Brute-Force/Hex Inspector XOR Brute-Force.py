import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import binascii
import string

def clean_hex(s: str) -> str:
    s = s.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    s = s.replace('0x', '')
    allowed = set('0123456789abcdefABCDEF ')
    s = ''.join(ch for ch in s if ch in allowed)
    s = s.replace(' ', '')
    return s

def hex_to_bytes(s: str) -> bytes:
    s = clean_hex(s)
    if len(s) % 2 != 0:
        s = '0' + s
    try:
        return binascii.unhexlify(s)
    except binascii.Error as e:
        raise ValueError('Hex inválido: ' + str(e))

def try_decodings(b: bytes) -> dict:
    results = {}
    try:
        results['utf-8'] = b.decode('utf-8')
    except Exception as e:
        results['utf-8'] = f'Erro: {e}'
    results['utf-8 (replace)'] = b.decode('utf-8', errors='replace')
    try:
        results['latin-1'] = b.decode('latin-1')
    except Exception as e:
        results['latin-1'] = f'Erro: {e}'
    try:
        results['ascii'] = b.decode('ascii')
    except Exception:
        printable = ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)
        results['ascii (best-effort)'] = printable
    results['hex'] = binascii.hexlify(b).decode()
    return results

def is_mostly_printable(s: str, threshold=0.7) -> bool:
    if not s:
        return False
    printable_count = sum(1 for ch in s if ch in string.printable)
    return (printable_count / len(s)) >= threshold

def xor_bytes(b: bytes, key: int) -> bytes:
    return bytes([x ^ key for x in b])

# ========== GUI ===========

class HexDecoderGUI:
    def __init__(self, master):
        self.master = master
        master.title('Hex Inspector XOR Brute-Force')
        master.geometry('1050x895')

        # Entrada
        tk.Label(master, text='Cole aqui a sequência hex (ou carregue .txt)').pack(pady=5)
        self.hex_text = scrolledtext.ScrolledText(width=120, height=12)  
        self.hex_text.pack(pady=5)

        # Botões principais
        tk.Button(master, text='Carregar .txt', bg="#03fc0b", fg="black", command=self.load_file).pack(pady=5)
        tk.Button(master, text='Converter & Analisar', bg="#07f5f5", fg="black", command=self.analyze).pack(pady=5)

        # Info
        self.info_label = tk.Label(master, text='Aguardando entrada...', anchor='w', justify='left')
        self.info_label.pack()

        # Decodificações
        tk.Label(master, text='Decodificações / Saídas').pack()
        self.out_text = scrolledtext.ScrolledText(width=120, height=12)
        self.out_text.pack(pady=5)

        # XOR brute
        xor_frame = tk.LabelFrame(master, text='XOR (brute-force 1 byte)')
        xor_frame.pack(pady=5)
        tk.Button(xor_frame, text='Rodar XOR 0..255 (mostrar resultados legíveis)', bg="#fcf803", fg="black", command=self.xor_bruteforce).pack(pady=2)
        self.xor_results = scrolledtext.ScrolledText(xor_frame, width=120, height=12)
        self.xor_results.pack(pady=5)

        # Salvar saída
        tk.Button(master, text='Salvar saída atual em arquivo', bg="#fca103", fg="black", command=self.save_output).pack(pady=5)

        self.last_bytes = b''

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            self.hex_text.delete('1.0', tk.END)
            self.hex_text.insert(tk.END, data)
        except Exception as e:
            messagebox.showerror('Erro', f'Não foi possível abrir o arquivo: {e}')

    def analyze(self):
        txt = self.hex_text.get('1.0', tk.END).strip()
        if not txt:
            messagebox.showinfo('Info', 'Cole uma sequência hex ou carregue um arquivo .txt primeiro.')
            return
        try:
            b = hex_to_bytes(txt)
        except Exception as e:
            messagebox.showerror('Erro na conversão', str(e))
            return
        self.last_bytes = b
        info = f'Bytes Lidos: {len(b)}\n'
        self.info_label.config(text=info)
        decs = try_decodings(b)
        self.out_text.delete('1.0', tk.END)
        for k, v in decs.items():
            self.out_text.insert(tk.END, f'--- {k} ---\n{v}\n\n')

    def xor_bruteforce(self):
        b = self.last_bytes
        if not b:
            messagebox.showinfo('Info', 'Converta/analise os hex primeiro (Converter & Analisar).')
            return
        self.xor_results.delete('1.0', tk.END)
        for key in range(256):
            out = xor_bytes(b, key)
            try:
                text = out.decode('utf-8')
            except Exception:
                text = ''.join(chr(c) if 32 <= c < 127 else '.' for c in out)
            if is_mostly_printable(text, threshold=0.7):
                self.xor_results.insert(tk.END, f'Key 0x{key:02x} ({key}) -> {text[:400]}\n\n')
        if self.xor_results.get('1.0', tk.END).strip() == '':
            self.xor_results.insert(tk.END, 'Nenhum resultado majoritariamente imprimível encontrado (com threshold 70%).\n')

    def save_output(self):
        data = self.out_text.get('1.0', tk.END)
        if not data.strip():
            messagebox.showinfo('Info', 'Nada para salvar (saída vazia).')
            return
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files', '*.txt')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(data)
            messagebox.showinfo('OK', f'Salvo em: {path}')
        except Exception as e:
            messagebox.showerror('Erro', f'Não foi possível salvar: {e}')

if __name__ == '__main__':
    root = tk.Tk()
    app = HexDecoderGUI(root)
    root.mainloop()
