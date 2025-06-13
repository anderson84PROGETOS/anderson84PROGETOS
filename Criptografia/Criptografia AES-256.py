import tkinter as tk
from tkinter import messagebox, filedialog
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

chave_aes_global = None  # Variável global para guardar a chave gerada

# Função para gerar a chave AES-256
def gerar_chave():
    global chave_aes_global
    chave_aes_global = os.urandom(32)  # 32 bytes para AES-256
    chave_base64 = base64.b64encode(chave_aes_global).decode()

    campo_chave_gerada.delete(0, tk.END)
    campo_chave_gerada.insert(0, chave_base64)

    messagebox.showinfo("Chave Gerada", "Chave AES-256 gerada com sucesso!")

# Função para criptografar usando a chave gerada
def criptografar():
    global chave_aes_global
    texto = entrada_mensagem.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Atenção", "Digite uma mensagem.")
        return

    if not chave_aes_global:
        messagebox.showwarning("Atenção", "Primeiro gere uma chave AES-256.")
        return

    iv = os.urandom(16)  # Vetor de inicialização

    padder = padding.PKCS7(128).padder()
    texto_bytes = texto.encode()
    texto_preenchido = padder.update(texto_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(chave_aes_global), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    mensagem_criptografada = encryptor.update(texto_preenchido) + encryptor.finalize()

    criptografado_base64 = base64.b64encode(iv + mensagem_criptografada).decode()

    campo_criptografado.delete(0, tk.END)
    campo_criptografado.insert(0, criptografado_base64)

    messagebox.showinfo("Sucesso", "Mensagem criptografada com sucesso! Agora você pode salvar.")

# Função para salvar mensagem criptografada e chave
def salvar():
    global chave_aes_global
    criptografado_base64 = campo_criptografado.get()
    if not criptografado_base64:
        messagebox.showwarning("Atenção", "Não há mensagem criptografada para salvar.")
        return
    if not chave_aes_global:
        messagebox.showwarning("Atenção", "Não há chave gerada para salvar.")
        return

    caminho_mensagem = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Salvar mensagem criptografada")
    if caminho_mensagem:
        with open(caminho_mensagem, "w") as f:
            f.write(criptografado_base64)

        pasta_destino = os.path.dirname(caminho_mensagem)
        caminho_chave = os.path.join(pasta_destino, "AES-256.txt")
        chave_base64 = base64.b64encode(chave_aes_global).decode()
        with open(caminho_chave, "w") as f:
            f.write(chave_base64)

        messagebox.showinfo("Sucesso", "Mensagem e chave AES-256 salvas com sucesso!")

# Função para carregar a chave e tentar descriptografar
def carregar_chave():
    caminho = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")], title="Selecione o arquivo da chave (AES-256.txt)")
    if caminho:
        try:
            with open(caminho, "r") as f:
                chave_base64 = f.read().strip()

                campo_chave_carregada.delete(0, tk.END)
                campo_chave_carregada.insert(0, chave_base64)
                campo_chave_gerada.delete(0, tk.END)
                campo_chave_gerada.insert(0, chave_base64)

            # Procurar a mensagem criptografada na mesma pasta (qualquer outro .txt que não seja AES-256.txt)
            pasta = os.path.dirname(caminho)
            arquivos_txt = [arq for arq in os.listdir(pasta) if arq.endswith(".txt") and arq != "AES-256.txt"]
            if arquivos_txt:
                caminho_mensagem = os.path.join(pasta, arquivos_txt[0])
                with open(caminho_mensagem, "r") as f:
                    mensagem = f.read().strip()
                    campo_criptografado.delete(0, tk.END)
                    campo_criptografado.insert(0, mensagem)
                    
                descriptografar()
            else:
                label_mensagem_criptografada.config(text="")
                messagebox.showwarning("Aviso", "Mensagem criptografada não encontrada na mesma pasta.")

        except Exception as e:
            label_mensagem_criptografada.config(text="")
            messagebox.showerror("Erro", f"Erro ao carregar chave ou mensagem:\n{e}")

# Função para descriptografar a mensagem
def descriptografar():
    try:
        chave_input = campo_chave_carregada.get()
        chave_bytes = base64.b64decode(chave_input)
        dados = base64.b64decode(campo_criptografado.get().strip())
        iv_rec = dados[:16]
        cript = dados[16:]

        cipher = Cipher(algorithms.AES(chave_bytes), modes.CBC(iv_rec), backend=default_backend())
        decryptor = cipher.decryptor()
        texto_decifrado = decryptor.update(cript) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        texto_original = unpadder.update(texto_decifrado) + unpadder.finalize()

        campo_decifrado.config(state='normal')
        campo_decifrado.delete("1.0", tk.END)
        campo_decifrado.insert(tk.END, texto_original.decode())
        campo_decifrado.config(state='disabled')

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível descriptografar.\n\n{e}")

# Interface gráfica
janela = tk.Tk()
janela.title("Criptografia AES-256")
janela.geometry("920x800")

tk.Label(janela, text="Digite sua mensagem", font=("Arial", 12)).pack()
entrada_mensagem = tk.Text(janela, width=90, height=10, font=("Arial", 12))
entrada_mensagem.pack(pady=5)

# Botões separados para gerar chave, criptografar e salvar
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

btn_gerar_chave = tk.Button(frame_botoes, text="Gerar Chave AES-256", command=gerar_chave, bg="#03fc24", fg="black", font=("Arial", 12))
btn_gerar_chave.grid(row=0, column=0, padx=5)

btn_criptografar = tk.Button(frame_botoes, text="Criptografar", command=criptografar, bg="#03fcf0", fg="black", font=("Arial", 12))
btn_criptografar.grid(row=0, column=1, padx=5)

btn_salvar = tk.Button(frame_botoes, text="Salvar Mensagem e Chave", command=salvar, bg="#fc9d03", fg="black", font=("Arial", 12))
btn_salvar.grid(row=0, column=2, padx=5)

tk.Label(janela, text="Mensagem Criptografada (base64)", font=("Arial", 12)).pack()
campo_criptografado = tk.Entry(janela, width=90, font=("Arial", 12))
campo_criptografado.pack(pady=5)

tk.Label(janela, text="Chave AES-256 Gerada (base64)", font=("Arial", 12)).pack()
campo_chave_gerada = tk.Entry(janela, width=90, font=("Arial", 12))
campo_chave_gerada.pack(pady=5)

label_mensagem_criptografada = tk.Label(janela, text="", wraplength=680, justify="left", fg="blue")
label_mensagem_criptografada.pack(pady=(0,10))

tk.Label(janela, text="Colar a chave manualmente ou selecionar o arquivo AES-256.txt", font=("Arial", 12)).pack()
campo_chave_carregada = tk.Entry(janela, width=90, font=("Arial", 12))
campo_chave_carregada.pack(pady=5)

tk.Button(janela, text="Selecionar chave (AES-256.txt) e Descriptografar", command=carregar_chave, bg="#03fc24", fg="black", font=("Arial", 12)).pack(pady=10)

tk.Label(janela, text="Mensagem Original (descriptografada)").pack()
campo_decifrado = tk.Text(janela, width=90, height=10, state='disabled', font=("Arial", 12))
campo_decifrado.pack(pady=5)

janela.mainloop()
