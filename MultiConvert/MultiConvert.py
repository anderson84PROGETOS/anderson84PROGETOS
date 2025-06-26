import os
import tkinter as tk
from tkinter import filedialog, Button, Label, messagebox, StringVar, OptionMenu
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Progressbar
from PIL import Image
import rawpy
import imageio

janela = tk.Tk()
janela.title("Multi Convert")
janela.geometry("1200x900")
janela.state("zoomed")

arquivos_selecionados = []

formato_saida = StringVar(janela)
formato_saida.set("png")  # formato padrão

# Nova variável para escolher largura da imagem
largura_saida = StringVar(janela)
largura_saida.set("original")  # padrão

# Opções de formato e largura
opcoes_formatos = ["png", "jpg", "jpeg", "bmp", "tiff", "webp", "gif", "ico"]
larguras_disponiveis = ["original", "1920", "1280", "1024", "720"]

# Lista de extensões suportadas
extensoes_suportadas = [".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".gif", ".heic", ".jfif", ".avif", ".ico", ".raw",
                        ".ppm", ".pgm", ".tga", ".svg", ".cr2"]

def selecionar_arquivos():
    global arquivos_selecionados
    arquivos = filedialog.askopenfilenames(
        title="Selecione as imagens",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if not arquivos:
        return

    arquivos_selecionados = list(arquivos)
    atualizar_lista_arquivos()
    messagebox.showinfo("Arquivos Selecionados", f"\nTotal de arquivos: {len(arquivos_selecionados)}\n\n{chr(10).join(arquivos_selecionados)}")

def atualizar_lista_arquivos():
    texto_arquivos.delete("1.0", tk.END)
    for caminho in arquivos_selecionados:
        texto_arquivos.insert(tk.END, f"\n{caminho}\n")

def salvar_imagens():
    if not arquivos_selecionados:
        messagebox.showwarning("Nenhuma imagem", "Você precisa selecionar imagens primeiro.")
        return

    pasta_destino = filedialog.askdirectory(title="Escolha a pasta para salvar as imagens")
    if not pasta_destino:
        return

    formato = formato_saida.get().lower()
    largura = largura_saida.get()
    convertidas = 0
    total_arquivos = len(arquivos_selecionados)

    barra_progresso["maximum"] = total_arquivos
    barra_progresso["value"] = 0
    janela.update()

    for caminho in arquivos_selecionados:
        try:
            ext = os.path.splitext(caminho)[1].lower()
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            novo_caminho = os.path.join(pasta_destino, nome_base + "." + formato)

            if ext == ".cr2":
                with rawpy.imread(caminho) as raw:
                    rgb = raw.postprocess()
                    imageio.imwrite(novo_caminho, rgb)
            else:
                imagem = Image.open(caminho)

                # Redimensionamento se necessário
                if largura != "original":
                    nova_largura = int(largura)
                    proporcao = nova_largura / imagem.width
                    nova_altura = int(imagem.height * proporcao)
                    imagem = imagem.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

                # Conversão de formato
                if formato == "png":
                    imagem = imagem.convert("RGBA")
                elif formato == "ico":
                    imagem = imagem.convert("RGBA")
                    imagem = imagem.resize((256, 256), Image.Resampling.LANCZOS)
                else:
                    imagem = imagem.convert("RGB")

                formato_real = "JPEG" if formato in ["jpg", "jpeg"] else formato.upper()
                imagem.save(novo_caminho, format=formato_real)

            convertidas += 1
            barra_progresso["value"] = convertidas
            janela.update()

        except Exception as e:
            messagebox.showerror("Erro na Conversão", f"Erro ao converter {caminho}:\n{str(e)}")

    messagebox.showinfo("Conversão concluída", f"{convertidas} imagem(ns) convertida(s) para {formato.upper()}.")
    arquivos_selecionados.clear()
    texto_arquivos.delete("1.0", tk.END)

# Interface Gráfica
Label(janela, text="Conversor de Imagens", font=("Arial", 16)).pack(pady=10)

Button(janela, text="Selecionar Imagens", command=selecionar_arquivos, width=30, bg="#05fc4f", fg="black").pack(pady=5)

Label(janela, text="Formato de saída", font=("Arial", 12)).pack()
OptionMenu(janela, formato_saida, *opcoes_formatos).pack(pady=5)

Label(janela, text="Largura da imagem de saída", font=("Arial", 12)).pack()
OptionMenu(janela, largura_saida, *larguras_disponiveis).pack(pady=5)

Button(janela, text="Salvar Todas as Imagens", command=salvar_imagens, width=30, bg="#fc056c", fg="black").pack(pady=5)

barra_progresso = Progressbar(janela, length=300, mode="determinate")
barra_progresso.pack(pady=10)

texto_arquivos = ScrolledText(janela, wrap=tk.WORD, width=140, height=35)
texto_arquivos.pack(padx=10, pady=10)

janela.mainloop()
