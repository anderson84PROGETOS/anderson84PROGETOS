import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base64

def decode_base64():
    text = input_text.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite ou cole algum texto Base64.")
        return

    linhas = text.splitlines()
    resultados = []

    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        try:
            decoded_bytes = base64.b64decode(linha)
            try:
                decoded = decoded_bytes.decode('utf-8')
            except UnicodeDecodeError:
                decoded = decoded_bytes.hex()
            resultados.append(decoded)
        except Exception:
            resultados.append(f"[Erro ao decodificar]: {linha}")

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "\n\n".join(resultados))

def decode_file():
    file_path = filedialog.askopenfilename(
        title="Abrir arquivo .txt com Base64",
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        resultados = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                decoded_bytes = base64.b64decode(line)
                try:
                    decoded = decoded_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    decoded = decoded_bytes.hex()
                resultados.append(decoded)
            except Exception as e:
                resultados.append(f"[Erro ao decodificar linha]: {line}")

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "\n\n".join(resultados))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir ou ler o arquivo:\n{e}")

def encode_file():
    file_path = filedialog.askopenfilename(
        title="Abrir arquivo para codificar em Base64",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        encoded = base64.b64encode(file_bytes).decode('utf-8')

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, encoded)

        messagebox.showinfo("Sucesso", "Arquivo codificado em Base64 com sucesso.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir ou codificar o arquivo:\n{e}")

def encode_base64():
    text = input_text.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite um texto para codificar.")
        return

    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, encoded)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao codificar o texto:\n{e}")

def save_encoded_base64():
    text = input_text.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite um texto para codificar.")
        return

    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar como"
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(encoded)

        messagebox.showinfo("Sucesso", f"Texto codificado salvo em:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

root = tk.Tk()
root.title("Decodificador Codificador Base64")
root.geometry("1100x910")

ttk.Label(root, text="Texto Base64 ou Texto Normal").pack(pady=5)
input_text = tk.Text(root, width=120, height=23)
input_text.pack()

frame_buttons = ttk.Frame(root)
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="Decodificar Base64", command=decode_base64, bg="#fccf05", fg="black").grid(row=0, column=0, padx=5)
tk.Button(frame_buttons, text="Codificar Arquivo para Base64", command=encode_file, bg="#05c3fc", fg="black").grid(row=0, column=1, padx=5)
tk.Button(frame_buttons, text="Codificar Texto para Base64", command=encode_base64, bg="#fc035e", fg="black").grid(row=0, column=2, padx=5)
tk.Button(frame_buttons, text="Salvar Texto Codificado em .txt", command=save_encoded_base64, bg="#fc5895", fg="black").grid(row=0, column=3, padx=5)
tk.Button(frame_buttons, text="Decodificar de Arquivo Base64 .txt", command=decode_file, bg="#05fc3f", fg="black").grid(row=0, column=4, padx=5)

ttk.Label(root, text="Resultado").pack()
output_text = tk.Text(root, width=120, height=23)
output_text.pack()

root.mainloop()
