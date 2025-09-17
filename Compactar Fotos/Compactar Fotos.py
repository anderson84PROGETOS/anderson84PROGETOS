import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageSequence
import os

# Limite de tamanho (em KB) e resolução máxima
LIMITE_KB = 400
RESOLUCAO_MAX = (1920, 1080)

def selecionar_arquivos():
    arquivos = filedialog.askopenfilenames(
        filetypes=[("Todas as imagens", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                   ("Todos os arquivos", "*.*")]
    )
    if arquivos:
        lista_arquivos.clear()
        lista_arquivos.extend(arquivos)
        text_area.insert(tk.END, "Imagens selecionadas\n\n")
        for arq in arquivos:
            text_area.insert(tk.END, f"{arq}\n")

def compactar():
    if not lista_arquivos:
        messagebox.showerror("Erro", "Selecione pelo menos uma imagem!")
        return

    pasta_saida = filedialog.askdirectory(title="Escolha a pasta de destino")
    if not pasta_saida:
        return

    progress["value"] = 0
    root.update_idletasks()

    try:
        total = len(lista_arquivos)
        for i, arquivo in enumerate(lista_arquivos, start=1):
            nome_original = os.path.basename(arquivo)
            extensao = os.path.splitext(nome_original)[1].lower()

            # Definir saída e formato
            if extensao == ".webp":
                nome_saida = os.path.join(pasta_saida, "square-image.jpg")
                formato = "JPEG"
            else:
                nome_saida = os.path.join(pasta_saida, nome_original)
                formato = extensao.replace(".", "").upper()

            img = Image.open(arquivo)

            # Converter para RGB se JPEG
            if formato == "JPEG" and img.mode != "RGB":
                img = img.convert("RGB")

            # Reduzir resolução (exceto GIF)
            if formato != "GIF":
                img.thumbnail(RESOLUCAO_MAX, Image.LANCZOS)

            tamanho_original = os.path.getsize(arquivo)
            tamanho_final = tamanho_original
            qualidade = 85

            # SALVAR JPEG (WebP convertido ou JPEG original)
            if formato == "JPEG":
                img.save(nome_saida, formato, quality=qualidade, optimize=True, progressive=True)
                tamanho_final = os.path.getsize(nome_saida)
                while tamanho_final > LIMITE_KB * 1024:
                    qualidade -= 5
                    if qualidade < 5:
                        largura, altura = img.size
                        img = img.resize((largura // 2, altura // 2), Image.LANCZOS)
                        qualidade = 85
                    img.save(nome_saida, formato, quality=qualidade, optimize=True, progressive=True)
                    tamanho_final = os.path.getsize(nome_saida)

            # SALVAR PNG
            elif formato == "PNG":
                img.save(nome_saida, formato, optimize=True)
                tamanho_final = os.path.getsize(nome_saida)
                while tamanho_final > LIMITE_KB * 1024:
                    largura, altura = img.size
                    img = img.resize((largura // 2, altura // 2), Image.LANCZOS)
                    img.save(nome_saida, formato, optimize=True)
                    tamanho_final = os.path.getsize(nome_saida)

            # SALVAR GIF
            elif formato == "GIF":
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                frames[0].save(
                    nome_saida,
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    optimize=True,
                    duration=img.info.get('duration', 100)
                )
                tamanho_final = os.path.getsize(nome_saida)

            # OUTROS formatos → salvar como JPEG
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(nome_saida, "JPEG", quality=85, optimize=True)
                tamanho_final = os.path.getsize(nome_saida)

            text_area.insert(
                tk.END,
                f"\n[{i}/{total}] Imagem compactada → {nome_saida}\n"
                f"\nTamanho antes: {tamanho_original/(1024*1024):.2f} MB | "
                f"depois: {tamanho_final/1024:.0f} KB\n"
            )

            progress["value"] = int((i / total) * 100)
            root.update_idletasks()

        messagebox.showinfo("Sucesso", "Compactação finalizada!")

    except Exception as e:
        text_area.insert(tk.END, f"Erro: {e}\n")
        messagebox.showerror("Erro", str(e))

# GUI
root = tk.Tk()
root.title("Compactar Fotos")
root.geometry("1060x820")

lista_arquivos = []

tk.Button(root, text="Selecionar Imagens", bg="#05e6ff", fg="black", command=selecionar_arquivos).pack(pady=5)
tk.Button(root, text="Compactar", bg="#03fc24", fg="black", command=compactar).pack(pady=10)

progress = ttk.Progressbar(root, mode="determinate", length=600)
progress.pack(pady=5)

text_area = scrolledtext.ScrolledText(root, width=120, height=40)
text_area.pack(pady=10)

root.mainloop()
