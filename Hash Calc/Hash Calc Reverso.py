import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import hashlib
import zlib
from Crypto.Hash import MD2, MD4, RIPEMD160
import threading  # Para evitar travar a GUI

wordlist = []  # Lista global

def get_hash_function(name, text):
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
        return MD4.new(text).hexdigest()
    else:
        return "Não implementado"

def descobrir_senha(hash_alvo, algoritmo):
    for senha in wordlist:
        senha = senha.strip()
        text_bytes = senha.encode('utf-8')
        if get_hash_function(algoritmo, text_bytes) == hash_alvo:
            return senha
    return "Não encontrada na wordlist"

def calcular_hashes():
    entrada = entry_text.get()
    if not entrada:
        resultado_texto.config(state='normal')
        resultado_texto.delete(1.0, tk.END)
        resultado_texto.insert(tk.END, "Digite ou cole algo.\n")
        resultado_texto.config(state='disabled')
        return

    modo = key_format.get()
    resultado_texto.config(state='normal')
    resultado_texto.delete(1.0, tk.END)

    if modo == "HASH":
        for nome, var in hash_vars.items():
            if var.get():
                senha = descobrir_senha(entrada.lower(), nome)
                resultado_texto.insert(tk.END, f"{nome} - Senha Encontrada: {senha}\n\n")
    else:
        text_bytes = entrada.encode('utf-8')
        for nome, var in hash_vars.items():
            if var.get():
                try:
                    hash_value = get_hash_function(nome, text_bytes)
                    resultado_texto.insert(tk.END, f"{nome}: {hash_value}\n\n")
                except Exception as e:
                    resultado_texto.insert(tk.END, f"{nome}: Erro ({e})\n\n")

    resultado_texto.config(state='disabled')

def carregar_wordlist():
    caminho = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if not caminho:
        return

    botao_carregar_wordlist.config(state='disabled')
    resultado_texto.config(state='normal')
    resultado_texto.insert(tk.END, f"[+] Carregando wordlist de: {caminho}\n")
    resultado_texto.config(state='disabled')

    def tarefa():
        global wordlist
        try:
            with open(caminho, encoding="utf-8", errors="ignore") as f:
                wordlist[:] = f.readlines()
        except Exception as e:
            resultado_texto.config(state='normal')
            resultado_texto.insert(tk.END, f"[!] Erro ao carregar wordlist: {e}\n")
            resultado_texto.config(state='disabled')
            botao_carregar_wordlist.config(state='normal')
            return

        # Ativar todos os algoritmos
        for var in hash_vars.values():
            var.set(True)

        resultado_texto.config(state='normal')
        resultado_texto.insert(tk.END, f"[+] Wordlist carregada com {len(wordlist)} senhas.\n")
        resultado_texto.config(state='disabled')

        # Se o modo for HASH, calcular automaticamente
        if key_format.get() == "HASH":
            calcular_hashes()

        botao_carregar_wordlist.config(state='normal')

    threading.Thread(target=tarefa).start()

# GUI
janela = tk.Tk()
janela.title("Hash Calc Reverso")
janela.geometry("1200x800")
janela.wm_state('zoomed')

tk.Label(janela, text="Texto ou Hash:").pack(pady=5)
entry_text = tk.Entry(janela, width=100)
entry_text.pack(pady=5)

tk.Label(janela, text="Modo de entrada:").pack(pady=5)
key_format = ttk.Combobox(janela, values=["Texto", "HASH"])
key_format.pack(pady=5)
key_format.set("Texto")

button_frame = tk.Frame(janela)
button_frame.pack(pady=5)
tk.Button(button_frame, text="Calculate", command=calcular_hashes).pack(side=tk.LEFT, padx=5)

botao_carregar_wordlist = tk.Button(button_frame, text="Carregar Wordlist", command=carregar_wordlist)
botao_carregar_wordlist.pack(side=tk.LEFT, padx=5)

frame_principal = tk.Frame(janela)
frame_principal.pack(fill=tk.BOTH, expand=True)

frame_checks = tk.Frame(frame_principal)
frame_checks.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
tk.Label(frame_checks, text="Algoritmos").pack(pady=1)

algorithms = [
    "MD5", "MD4", "SHA1", "SHA256", "SHA384", "SHA512",
    "RIPEMD160", "MD2", "ADLER32", "CRC32", "HMAC", "eDonkey/eMule"
]

hash_vars = {}
for alg in algorithms:
    var = tk.BooleanVar()
    hash_vars[alg] = var
    tk.Checkbutton(frame_checks, text=alg, variable=var).pack(anchor='w')

frame_direito = tk.Frame(frame_principal)
frame_direito.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

resultado_texto = scrolledtext.ScrolledText(frame_direito, width=50, height=40)
resultado_texto.pack(pady=10, fill=tk.BOTH, expand=True)

janela.mainloop()
