import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import hashlib
import os
import webbrowser
import re

def calcular_hashes(caminho_arquivo):
    """Calcula MD5, SHA1, SHA256 e SHA512 de um arquivo."""
    hashes = {
        "MD5": hashlib.md5(),
        "SHA1": hashlib.sha1(),
        "SHA256": hashlib.sha256(),
        "SHA512": hashlib.sha512()
    }

    try:
        with open(caminho_arquivo, "rb") as f:
            while True:
                bloco = f.read(65536)
                if not bloco:
                    break
                for h in hashes.values():
                    h.update(bloco)
    except Exception as e:
        return f"Erro ao ler o arquivo: {e}"

    resultado = ""
    for nome, h in hashes.items():
        resultado += f"\n{nome}: {h.hexdigest()}\n"
    return resultado

def abrir_arquivo():
    arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo",
        filetypes=(("Todos os arquivos", "*.*"),)
    )
    if arquivo:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Calculando hashes, aguarde...\n")
        root.update()
        resultado = calcular_hashes(arquivo)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, resultado)
        tornar_hashes_clicaveis()

def salvar_resultado():
    if not text_area.get(1.0, tk.END).strip():
        messagebox.showwarning("Aviso", "Não há resultados para salvar!")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=(("Arquivo de Texto", "*.txt"),),
        title="Salvar resultados como"
    )
    if caminho_salvar:
        try:
            with open(caminho_salvar, "w", encoding="utf-8") as f:
                f.write(text_area.get(1.0, tk.END))
            messagebox.showinfo("Sucesso", f"Resultados salvos em\n\n{caminho_salvar}")
        except Exception as e:
            messagebox.showerror("Erro", f"\nNão foi possível salvar o arquivo:\n{e}")

def tornar_hashes_clicaveis():
    """Procura hashes na text_area e as torna clicáveis."""
    text_area.tag_remove("hash_link", "1.0", tk.END)
    # Detecta MD5 (32), SHA1 (40), SHA256 (64) e SHA512 (128)
    hashes = re.findall(r"\b[a-fA-F0-9]{32,128}\b", text_area.get("1.0", tk.END))
    for h in hashes:
        start = text_area.search(h, "1.0", tk.END)
        while start:
            end = f"{start}+{len(h)}c"
            text_area.tag_add("hash_link", start, end)
            start = text_area.search(h, end, tk.END)

    text_area.tag_config(
        "hash_link",
        foreground="blue",
        underline=1
    )
    text_area.tag_bind("hash_link", "<Button-1>", abrir_virustotal)

def abrir_virustotal(event):
    index = text_area.index(f"@{event.x},{event.y}")
    # Pega a hash clicada
    start = text_area.search(r"[a-fA-F0-9]{32,128}", index, backwards=True, regexp=True)
    if not start:
        start = index
    # Determina o fim do hash (maior 128 caracteres)
    end = f"{start}+128c"
    hash_text = text_area.get(start, end).split()[0]
    # Abre diretamente no link de análise de arquivo
    webbrowser.open(f"https://www.virustotal.com/gui/file/{hash_text}")

# Configuração da janela principal
root = tk.Tk()
root.title("Calculadora de Hashes")
root.geometry("1250x650")

# Botões
btn_abrir = tk.Button(root, text="Selecionar Arquivo", bg="#03fc24", fg="black", command=abrir_arquivo)
btn_abrir.pack(pady=10)

btn_salvar = tk.Button(root, text="Salvar Resultado em .txt", bg="#f5ad05", fg="black", command=salvar_resultado)
btn_salvar.pack(pady=5)

# Área de texto com scroll
text_area = scrolledtext.ScrolledText(root, width=145, height=30)
text_area.pack(padx=10, pady=10)

# Executa a interface
root.mainloop() 
