import tkinter as tk
from tkinter import ttk, scrolledtext
import hashlib
import zlib
from Crypto.Hash import MD2, MD4, RIPEMD160  # Adiciona suporte via pycryptodome

# Função que retorna o hash conforme o algoritmo
def get_hash_function(name, text):
    try:
        if name == "MD5":
            return hashlib.md5(text).hexdigest()
        elif name == "MD4":
            return MD4.new(text).hexdigest()
        elif name == "MD2":
            return MD2.new(text).hexdigest()
        elif name == "SHA1":
            return hashlib.sha1(text).hexdigest()
        elif name == "SHA256":
            return hashlib.sha256(text).hexdigest()
        elif name == "SHA384":
            return hashlib.sha384(text).hexdigest()
        elif name == "SHA512":
            return hashlib.sha512(text).hexdigest()
        elif name == "RIPEMD160":
            return RIPEMD160.new(text).hexdigest()      
        elif name == "ADLER32":
            return format(zlib.adler32(text) & 0xffffffff, '08x')
        elif name == "CRC32":
            return format(zlib.crc32(text) & 0xffffffff, '08x')
        elif name == "HMAC":
            return hashlib.pbkdf2_hmac('sha256', text, b'secretkey', 100000).hex()
        elif name == "eDonkey/eMule":
            # eDonkey/eMule usa MD4
            return MD4.new(text).hexdigest()
        else:
            return "Não implementado"
    except ValueError as e:
        return f"Erro: {str(e)}"
    except NameError:
        return "Instale pycryptodome para suporte a este algoritmo"

# Função para calcular os hashes
def calcular_hashes():
    input_text = entry_text.get()
    if not input_text:
        resultado_texto.config(state='normal')
        resultado_texto.delete(1.0, tk.END)
        resultado_texto.insert(tk.END, "Digite algo para calcular os hashes.\n")
        resultado_texto.config(state='disabled')
        return

    resultado_texto.config(state='normal')
    resultado_texto.delete(1.0, tk.END)

    text_bytes = input_text.encode('utf-8')
    for nome, var in hash_vars.items():
        if var.get():
            try:
                hash_value = get_hash_function(nome, text_bytes)
                resultado_texto.insert(tk.END, f"{nome}: {hash_value}\n\n")
            except Exception as e:
                resultado_texto.insert(tk.END, f"{nome}: Erro ({e})\n\n")

    resultado_texto.config(state='disabled')

# Janela principal
janela = tk.Tk()
janela.title("Hash Calc")
janela.geometry("1200x800")
janela.wm_state('zoomed')

# Entrada de texto e opções no topo
tk.Label(janela, text="Texto ou chave").pack(pady=5)
entry_text = tk.Entry(janela, width=80)
entry_text.pack(pady=5)

# Key Format label
tk.Label(janela, text="Key Format").pack(pady=5)

# Frame para o botão Calculate centrado
button_frame = tk.Frame(janela)
button_frame.pack(pady=5)
tk.Button(button_frame, text="Calculate", command=calcular_hashes).pack()

# Frame principal horizontal
frame_principal = tk.Frame(janela)
frame_principal.pack(fill=tk.BOTH, expand=True)

# Frame lateral esquerdo (checkboxes)
frame_checks = tk.Frame(frame_principal)
frame_checks.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

tk.Label(frame_checks, text="Selecione Algoritmo").pack(pady=1)

algorithms = [
    "MD5", "MD4", "SHA1", "SHA256", "SHA384", "SHA512", "RIPEMD160",
    "MD2", "ADLER32", "CRC32", "HMAC", "eDonkey/eMule"
]

hash_vars = {}
for alg in algorithms:
    var = tk.BooleanVar()
    hash_vars[alg] = var
    tk.Checkbutton(frame_checks, text=alg, variable=var).pack(anchor='w')

# Frame direito (resultado)
frame_direito = tk.Frame(frame_principal)
frame_direito.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Área de resultados
resultado_texto = scrolledtext.ScrolledText(frame_direito, width=50, height=40)
resultado_texto.pack(pady=10, fill=tk.BOTH, expand=True)

# Iniciar interface
janela.mainloop()
