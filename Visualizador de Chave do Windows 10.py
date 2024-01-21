import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog
from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE

def get_windows_key():
    try:
        with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as hkey:
            with OpenKey(hkey, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as subkey:
                digital_product_id = QueryValueEx(subkey, "DigitalProductId")[0]
                return convert_to_key(digital_product_id)
    except Exception as e:
        return f"Erro: {str(e)}"

def convert_to_key(key):
    key_offset = 52
    i = 28
    chars = "BCDFGHJKMPQRTVWXY2346789"
    key_bytes = bytearray(key)

    key_output = ""

    while i >= 0:
        cur = 0
        x = 14
        while x >= 0:
            cur = cur * 256
            cur = key_bytes[x + key_offset] + cur
            key_bytes[x + key_offset] = cur // 24
            cur = cur % 24
            x -= 1

        i -= 1
        key_output = chars[cur] + key_output

        if (((29 - i) % 6) == 0) and (i != -1):
            i -= 1
            key_output = "-" + key_output

    return key_output

def show_key():
    key = get_windows_key()
    result_text.delete(1.0, tk.END)  # Limpa o conteúdo atual do widget
    result_text.insert(tk.END, f"Chave de produto do Windows 10\n\n{key}")

def save_key():
    key = get_windows_key()
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(f"Chave de produto do Windows 10\n\n{key}")
        result_text.insert(tk.END, f"\n\n\nChave salva em: {file_path}")

# Configuração da janela principal
window = tk.Tk()
window.title("Visualizador de Chave do Windows 10")
window.geometry("800x500")

# Botão para exibir a chave
show_key_button = tk.Button(window, text="Exibir Chave", command=show_key, bg="#00FFFF", font=("Arial", 11))
show_key_button.pack(pady=10)

# Botão para salvar a chave
save_key_button = tk.Button(window, text="Salvar Chave", command=save_key, bg="#f57d7d", font=("Arial", 11))
save_key_button.pack(pady=10)

# Criar o widget ScrolledText para os resultados
result_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=20, font=("Arial", 12))
result_text.pack()

# Inicia o loop principal da interface gráfica
window.mainloop()
