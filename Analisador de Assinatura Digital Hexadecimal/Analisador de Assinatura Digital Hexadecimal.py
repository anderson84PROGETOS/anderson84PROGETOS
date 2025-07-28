import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import base64
import os

def hex_para_bytes(hex_str):
    hex_str = hex_str.replace(":", "").replace("\n", "").replace(" ", "")
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        return None

def analisar_hex():
    entrada = caixa_hex.get("1.0", tk.END).strip()
    dados = hex_para_bytes(entrada)

    if not dados:
        messagebox.showerror("Erro", "Hexadecimal inválido!")
        return

    # Conversão Base64
    base64_str = base64.b64encode(dados).decode()

    # ASCII legível
    ascii_legivel = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in dados)

    # Exibir na tela
    caixa_base64.config(state=tk.NORMAL)
    caixa_base64.delete("1.0", tk.END)
    caixa_base64.insert(tk.END, base64_str)
    caixa_base64.config(state=tk.DISABLED)

    caixa_ascii.config(state=tk.NORMAL)
    caixa_ascii.delete("1.0", tk.END)
    caixa_ascii.insert(tk.END, ascii_legivel)
    caixa_ascii.config(state=tk.DISABLED)

    botao_salvar["state"] = tk.NORMAL

def salvar_txt():
    base64_str = caixa_base64.get("1.0", tk.END).strip()
    ascii_str = caixa_ascii.get("1.0", tk.END).strip()

    conteudo = (
        "=== Assinatura Digital (Base64) ===\n\n" +
        base64_str + "\n\n" +
        "\n=== ASCII Legível ===\n\n" +
        ascii_str + "\n"
    )

    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo Texto", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        messagebox.showinfo("Salvo", f"\nArquivo salvo em: {caminho}")

def abrir_arquivo_hex():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos Texto", "*.txt")])
    if not caminho:
        return
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
            caixa_hex.delete("1.0", tk.END)
            caixa_hex.insert(tk.END, conteudo.strip())
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir arquivo:\n{str(e)}")

# Interface Gráfica
janela = tk.Tk()
janela.title("Analisador de Assinatura Digital (Hexadecimal)")
janela.geometry("1200x900")
janela.wm_state('zoomed')
janela.configure(bg="#f4f4f4")

# Label e botões de controle
tk.Label(janela, text="Cole ou abra a Assinatura Hexadecimal", bg="#f4f4f4", font=("Arial", 12)).pack(pady=5)

frame_botoes = tk.Frame(janela, bg="#f4f4f4")
frame_botoes.pack(pady=5)
tk.Button(frame_botoes, text="📂 Abrir Arquivo .txt", command=abrir_arquivo_hex, bg="#FF9800", fg="black", font=("Arial", 11)).pack(side=tk.LEFT, padx=10)
tk.Button(frame_botoes, text="🔍 Analisar", command=analisar_hex, bg="#06c91a", fg="black", font=("Arial", 11, "bold")).pack(side=tk.LEFT)

# Botão salvar
botao_salvar = tk.Button(frame_botoes, text="💾 Salvar Resultado", command=salvar_txt, bg="#2196F3", fg="black", font=("Arial", 11, "bold"))
botao_salvar.pack(side=tk.LEFT, padx=10,pady=10)
botao_salvar["state"] = tk.DISABLED

# Caixa HEX com scrollbar
tk.Label(janela, text="Entrada Hexadecimal", bg="#f4f4f4", font=("Arial", 11, "bold")).pack()
caixa_hex = scrolledtext.ScrolledText(janela, height=15, font=("Courier", 10), bg="#ffffff", fg="#000000", wrap=tk.WORD)
caixa_hex.pack(fill="both", padx=10, pady=5, expand=False)

# Caixa BASE64 com scrollbar
tk.Label(janela, text="Assinatura em Base64", bg="#f4f4f4", font=("Arial", 11, "bold")).pack()
caixa_base64 = scrolledtext.ScrolledText(janela, height=15, font=("Courier", 10), bg="#eeeeee", fg="#000000", wrap=tk.WORD)
caixa_base64.pack(fill="both", padx=10, pady=5, expand=False)
caixa_base64.config(state=tk.DISABLED)

# Caixa ASCII com scrollbar
tk.Label(janela, text="Texto ASCII legível", bg="#f4f4f4", font=("Arial", 11, "bold")).pack()
caixa_ascii = scrolledtext.ScrolledText(janela, height=15, font=("Courier", 10), bg="#eeeeee", fg="#000000", wrap=tk.WORD)
caixa_ascii.pack(fill="both", padx=10, pady=5, expand=False)
caixa_ascii.config(state=tk.DISABLED)

janela.mainloop()
