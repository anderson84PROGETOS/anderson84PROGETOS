import re
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# Lista global para armazenar URLs encontradas
urls = []

# Função para abrir o arquivo e extrair URLs
def abrir_arquivo():
    global urls

    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo",
        filetypes=(
            ("Arquivos HTML", "*.html"),
            ("Arquivos TXT", "*.txt"),
            ("Todos os arquivos", "*.*")
        )
    )

    if not caminho_arquivo:
        return

    with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
        conteudo = f.read()

    # Regex para capturar URLs
    urls_encontradas = re.findall(
        r'https?://[^\s"\']+',
        conteudo,
        re.IGNORECASE
    )

    # Remover duplicadas e ordenar
    urls = sorted(list(set(urls_encontradas)))

    mostrar_urls(
        urls,
        titulo=f"Total de URLs únicas encontradas: {len(urls)}"
    )


# Função para exibir URLs
def mostrar_urls(lista, titulo="Resultados"):
    text_area.delete(1.0, tk.END)

    if lista:
        text_area.insert(tk.END, f"{titulo}\n\n")
        for url in lista:
            text_area.insert(tk.END, url + "\n\n")
    else:
        text_area.insert(tk.END, "Nenhum resultado encontrado.")


# Função para pesquisar URLs
def pesquisar_url():
    termo = entry_pesquisa.get().strip().lower()

    if not urls:
        messagebox.showwarning(
            "Aviso",
            "Primeiro abra um arquivo para extrair URLs."
        )
        return

    if not termo:
        messagebox.showwarning(
            "Aviso",
            "Digite algo para pesquisar."
        )
        return

    resultados = [
        url for url in urls
        if termo in url.lower()
    ]

    mostrar_urls(
        resultados,
        titulo=f"Resultados para: {termo} | Encontrados: {len(resultados)}"
    )


# Função para salvar URLs por categoria
def salvar_resultados():
    if not urls:
        messagebox.showwarning(
            "Aviso",
            "Nenhuma URL para salvar!"
        )
        return

    pasta_base = filedialog.askdirectory(
        title="Selecione a pasta para salvar as categorias"
    )

    if not pasta_base:
        return

    categorias = {
        "pdf": [],
        "fotos": [],
        "videos_mp4": [],
        "outros_urls": []
    }

    extensoes_imagem = [
        "png", "jpg", "jpeg", "gif",
        "bmp", "webp", "ico", "svg"
    ]

    extensoes_video = [
        "mp4", "avi", "mov", "mkv",
        "wmv", "flv", "webm"
    ]

    for url in urls:
        # Remove parâmetros após ?
        url_limpa = url.split("?")[0]

        # Extrai extensão
        if "." in url_limpa:
            ext = url_limpa.split(".")[-1].lower()
        else:
            ext = ""

        if ext == "pdf":
            categorias["pdf"].append(url)

        elif ext in extensoes_imagem:
            categorias["fotos"].append(url)

        elif ext in extensoes_video:
            categorias["videos_mp4"].append(url)

        else:
            categorias["outros_urls"].append(url)

    # Criar pastas e salvar arquivos
    for categoria, lista in categorias.items():
        if lista:
            pasta_categoria = os.path.join(
                pasta_base,
                categoria
            )

            os.makedirs(
                pasta_categoria,
                exist_ok=True
            )

            arquivo_saida = os.path.join(
                pasta_categoria,
                f"{categoria}.txt"
            )

            with open(
                arquivo_saida,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(
                    f"Total de URLs na categoria '{categoria}': {len(lista)}\n\n"
                )

                for url in lista:
                    f.write(url + "\n\n")

    messagebox.showinfo(
        "Sucesso",
        f"URLs salvas com sucesso em:\n\n{pasta_base}\n\nTotal geral: {len(urls)}"
    )


# Interface gráfica
root = tk.Tk()
root.title("Extrator de URL - PDF, Fotos, MP4 e Outros")
root.geometry("1000x600")
root.state("zoomed")

# Botão abrir arquivo
btn_abrir = tk.Button(root, text="Abrir arquivo", bg="#03fc24", fg="black", command=abrir_arquivo, font=("Arial", 11))
btn_abrir.pack(pady=10)

# Área de pesquisa
frame_pesquisa = tk.Frame(root)
frame_pesquisa.pack(pady=10)

entry_pesquisa = tk.Entry(frame_pesquisa, width=50, font=("Arial", 12))
entry_pesquisa.pack(side=tk.LEFT, padx=10)

btn_pesquisar = tk.Button(frame_pesquisa, text="Pesquisar", bg="#4da6ff", fg="black", command=pesquisar_url, font=("Arial", 11))
btn_pesquisar.pack(side=tk.LEFT)

# Botão salvar
btn_salvar = tk.Button( root, text="Salvar resultados por categoria", bg="#f5b507", fg="black", command=salvar_resultados, font=("Arial", 11))
btn_salvar.pack(pady=10)

# Área de texto
text_area = scrolledtext.ScrolledText(root, width=160, height=45, font=("Arial", 10))
text_area.pack(pady=10)

# Executar
root.mainloop()
