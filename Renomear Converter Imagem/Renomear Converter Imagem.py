import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
from tkinter.ttk import Progressbar
from PIL import Image
import rawpy

arquivos_selecionados = []

def abrir_imagem(caminho):
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".dng":
        with rawpy.imread(caminho) as raw:
            rgb = raw.postprocess()
            img = Image.fromarray(rgb)
        return img
    else:
        return Image.open(caminho)

def selecionar_fotos():
    global arquivos_selecionados
    arquivos = filedialog.askopenfilenames(
        title="Selecione as fotos",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if arquivos:
        arquivos_selecionados = arquivos
        log_text.insert(tk.END, f"[INFO] {len(arquivos_selecionados)} arquivos selecionados.\n")
    else:
        log_text.insert(tk.END, "[INFO] Nenhum arquivo selecionado.\n")

def converter_fotos():
    global arquivos_selecionados
    if not arquivos_selecionados:
        messagebox.showwarning("Aviso", "Nenhuma foto selecionada. Por favor, selecione as fotos primeiro.")
        return

    nome_base = simpledialog.askstring("Nome Base", "Digite o novo nome base (ex: viagem ou 1):")
    if not nome_base:
        return

    pasta = os.path.dirname(arquivos_selecionados[0])
    pasta_convertida = os.path.join(pasta, "convertidas")
    os.makedirs(pasta_convertida, exist_ok=True)

    total = len(arquivos_selecionados)
    progresso["maximum"] = total
    progresso["value"] = 0
    log_text.delete(1.0, tk.END)

    try:
        numero_inicial = int(nome_base)
        usar_numeros_simples = True
    except ValueError:
        numero_inicial = 1
        usar_numeros_simples = False

    formato = formato_saida.get()

    formato_pillow = formato.upper()
    if formato.lower() == "jpg":
        formato_pillow = "JPEG"
    elif formato.lower() == "jpeg":
        formato_pillow = "JPEG"

    for i, caminho in enumerate(arquivos_selecionados):
        try:
            img = abrir_imagem(caminho)
            img = img.convert("RGB")

            if usar_numeros_simples:
                novo_nome = f"{numero_inicial + i}.{formato}"
            else:
                novo_nome = f"{nome_base}_{i+1}.{formato}"

            novo_caminho = os.path.join(pasta_convertida, novo_nome)

            if formato == "ico":
                img_ico = img.resize((256, 256), Image.LANCZOS)
                img_ico.save(novo_caminho, "ICO")
            else:
                img.save(novo_caminho, formato_pillow)

            # Não apagar os arquivos originais
            log_text.insert(tk.END, f"[OK] {os.path.basename(caminho)} -> {novo_nome} (salvo em convertidas)\n")
        except Exception as e:
            log_text.insert(tk.END, f"[ERRO] {os.path.basename(caminho)}: {str(e)}\n")
        progresso["value"] += 1
        root.update_idletasks()

    messagebox.showinfo("Sucesso", f"Fotos convertidas para .{formato} e salvas na pasta 'convertidas'!")

# Interface
root = tk.Tk()
root.title("Renomear, Converter e Remover Originais")
root.wm_state('zoomed')
root.geometry("700x700")

formato_saida = tk.StringVar(value="png")

btn_selecionar = tk.Button(root, text="Selecionar Fotos", command=selecionar_fotos, bg="#05fc4f", padx=10, pady=10)
btn_selecionar.pack(pady=5)

btn_converter = tk.Button(root, text="Converter Fotos", command=converter_fotos, bg="#05c5ff", padx=10, pady=10)
btn_converter.pack(pady=5)

frame_formatos = tk.LabelFrame(root, text="Formato de saída", padx=10, pady=10)
frame_formatos.pack(pady=5)

formatos = ["png", "jpg", "jpeg", "bmp", "gif", "ico"]
for f in formatos:
    rb = tk.Radiobutton(frame_formatos, text=f.upper(), variable=formato_saida, value=f)
    rb.pack(side=tk.LEFT, padx=10)

progresso = Progressbar(root, orient="horizontal", length=600, mode="determinate")
progresso.pack(pady=10)

log_text = scrolledtext.ScrolledText(root, width=120, height=40)
log_text.pack(padx=10, pady=10)

root.mainloop()
