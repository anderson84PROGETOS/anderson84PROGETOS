# =========================================================
# LOCALIZADOR DE ARQUIVOS WINDOWS
# ✔ TEMPO REAL
# ✔ SALVAR TXT
# ✔ PESQUISAR NOS RESULTADOS
# ✔ CAMINHO
# ✔ DATA
# ✔ TAMANHO
# ✔ BARRA VERDE
# =========================================================

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

# =========================================================
# VARIÁVEIS
# =========================================================
buscando = False
texto_original = ""

# =========================================================
# FUNÇÕES
# =========================================================

def adicionar_log(texto):

    resultado_texto.insert(
        tk.END,
        texto + "\n"
    )

    resultado_texto.see(tk.END)


def adicionar_log_thread(texto):

    janela.after(
        0,
        lambda t=texto: adicionar_log(t)
    )


def formatar_tamanho(bytes_size):

    try:

        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:

            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unidade}"

            bytes_size /= 1024

    except:
        return "Desconhecido"


def escolher_pasta():

    pasta = filedialog.askdirectory(
        title="Escolher pasta ou disco"
    )

    if pasta:

        entrada_pasta.delete(0, tk.END)

        entrada_pasta.insert(
            0,
            pasta
        )


def contar_arquivos(pasta):

    total = 0

    try:

        for raiz, dirs, arquivos in os.walk(pasta):

            total += len(arquivos)

    except:
        pass

    return total


def atualizar_barra(valor):

    barra_progresso["value"] = valor

    label_porcentagem.config(
        text=f"{int(valor)}%"
    )


# =========================================================
# SALVAR TXT
# =========================================================

def salvar_txt():

    conteudo = resultado_texto.get(
        1.0,
        tk.END
    )

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo TXT", "*.txt")],
        title="Salvar resultado"
    )

    if caminho:

        try:

            with open(
                caminho,
                "w",
                encoding="utf-8"
            ) as arquivo:

                arquivo.write(conteudo)

            messagebox.showinfo(
                "SUCESSO",
                "Arquivo salvo com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "ERRO",
                str(erro)
            )


# =========================================================
# PESQUISAR NO RESULTADO
# =========================================================

def pesquisar_resultado():

    global texto_original

    texto_busca = entrada_pesquisa.get().lower().strip()

    if not texto_busca:
        return

    # SALVA TEXTO ORIGINAL
    texto_original = resultado_texto.get(
        1.0,
        tk.END
    )

    linhas = texto_original.splitlines()

    resultado_texto.delete(
        1.0,
        tk.END
    )

    encontrados = 0

    for linha in linhas:

        if texto_busca in linha.lower():

            resultado_texto.insert(
                tk.END,
                linha + "\n"
            )

            encontrados += 1

    if encontrados == 0:

        resultado_texto.insert(
            tk.END,
            "[NENHUM RESULTADO ENCONTRADO]\n"
        )

def limpar_pesquisa():

    entrada_pesquisa.delete(
        0,
        tk.END
    )

    # REMOVE DESTAQUES
    resultado_texto.tag_remove(
        "pesquisa",
        "1.0",
        tk.END
    )

    # LIMPA RESULTADO
    resultado_texto.delete(
        1.0,
        tk.END
    )

    # RESTAURA TEXTO ORIGINAL
    resultado_texto.insert(
        tk.END,
        texto_original
    )
# =========================================================
# INICIAR BUSCA
# =========================================================

def iniciar_busca():

    global buscando

    nome_arquivo = entrada_nome.get().strip()
    pasta = entrada_pasta.get().strip()

    if not nome_arquivo:

        messagebox.showerror(
            "ERRO",
            "Digite o nome do arquivo."
        )

        return

    if not pasta:

        messagebox.showerror(
            "ERRO",
            "Escolha uma pasta."
        )

        return

    resultado_texto.delete(
        1.0,
        tk.END
    )

    barra_progresso["value"] = 0

    label_porcentagem.config(
        text="0%"
    )

    buscando = True

    thread = threading.Thread(
        target=buscar_arquivos,
        args=(
            nome_arquivo.lower(),
            pasta
        ),
        daemon=True
    )

    thread.start()


def parar_busca():

    global buscando

    buscando = False

    adicionar_log_thread(
        "[BUSCA PARADA PELO USUÁRIO]"
    )


# =========================================================
# MOSTRAR ENCONTRADO
# =========================================================

def mostrar_encontrado(
    numero,
    arquivo,
    caminho,
    tamanho,
    criado,
    modificado
):

    adicionar_log("")
    adicionar_log("=" * 80)

    adicionar_log(
        f"[ARQUIVO ENCONTRADO #{numero}]"
    )

    adicionar_log("=" * 80)

    adicionar_log(
        f"Nome Arquivo : {arquivo}"
    )

    adicionar_log(
        f"Caminho      : {caminho}\n"
    )

    adicionar_log(
        f"Tamanho      : {tamanho}"
    )

    adicionar_log(
        f"Criado em    : {criado}"
    )

    adicionar_log(
        f"Modificado   : {modificado}"
    )

    adicionar_log("")


# =========================================================
# BUSCA
# =========================================================

def buscar_arquivos(nome_arquivo, pasta_inicial):

    global buscando

    encontrados = 0
    processados = 0

    adicionar_log_thread("=" * 80)

    adicionar_log_thread(
        "LOCALIZADOR DE ARQUIVOS WINDOWS"
    )

    adicionar_log_thread("=" * 80)

    adicionar_log_thread(
        f"Nome pesquisado : {nome_arquivo}"
    )

    adicionar_log_thread(
        f"Pasta inicial   : {pasta_inicial}"
    )

    adicionar_log_thread("=" * 80)

    total_arquivos = contar_arquivos(
        pasta_inicial
    )

    if total_arquivos == 0:

        adicionar_log_thread(
            "[ERRO] Nenhum arquivo encontrado."
        )

        return

    try:

        for raiz, dirs, arquivos in os.walk(
            pasta_inicial
        ):

            if not buscando:
                break

            adicionar_log_thread(
                f"[PROCURANDO EM] {raiz}\n"
            )

            for arquivo in arquivos:

                if not buscando:
                    break

                processados += 1

                porcentagem = (
                    processados / total_arquivos
                ) * 100

                janela.after(
                    0,
                    atualizar_barra,
                    porcentagem
                )

                try:

                    if nome_arquivo in arquivo.lower():

                        caminho_completo = os.path.join(
                            raiz,
                            arquivo
                        )

                        tamanho = os.path.getsize(
                            caminho_completo
                        )

                        tamanho_formatado = formatar_tamanho(
                            tamanho
                        )

                        data_mod = os.path.getmtime(
                            caminho_completo
                        )

                        data_mod_formatada = datetime.fromtimestamp(
                            data_mod
                        ).strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )

                        data_criacao = os.path.getctime(
                            caminho_completo
                        )

                        data_criacao_formatada = datetime.fromtimestamp(
                            data_criacao
                        ).strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )

                        encontrados += 1

                        janela.after(
                            0,
                            mostrar_encontrado,
                            encontrados,
                            arquivo,
                            caminho_completo,
                            tamanho_formatado,
                            data_criacao_formatada,
                            data_mod_formatada
                        )

                except:
                    continue

    except Exception as erro:

        adicionar_log_thread(
            f"[ERRO GERAL] {erro}"
        )

    janela.after(
        0,
        atualizar_barra,
        100
    )

    adicionar_log_thread("")
    adicionar_log_thread("=" * 80)

    adicionar_log_thread(
        f"TOTAL ENCONTRADO: {encontrados}"
    )

    adicionar_log_thread("=" * 80)

    buscando = False


# =========================================================
# JANELA
# =========================================================

janela = tk.Tk()

janela.title("LOCALIZADOR DE ARQUIVOS WINDOWS")

janela.geometry("1250x800")

janela.state("zoomed")

janela.configure(bg="#111111")

# =========================================================
# ESTILO
# =========================================================

style = ttk.Style()

style.theme_use("clam")

style.configure(
    "green.Horizontal.TProgressbar",
    troughcolor="#222222",
    background="#00FF00",
    bordercolor="#111111",
    lightcolor="#00FF00",
    darkcolor="#00CC00",
    thickness=25
)

# =========================================================
# TÍTULO
# =========================================================

titulo = tk.Label(
    janela,
    text="LOCALIZADOR DE ARQUIVOS WINDOWS",
    font=("Arial", 24, "bold"),
    bg="#111111",
    fg="#00FF00"
)

titulo.pack(
    pady=10
)

# =========================================================
# FRAME
# =========================================================

frame = tk.Frame(
    janela,
    bg="#111111"
)

frame.pack(
    pady=10
)

# =========================================================
# NOME
# =========================================================

label_nome = tk.Label(
    frame,
    text="Nome do arquivo/programa:",
    font=("Arial", 12),
    bg="#111111",
    fg="white"
)

label_nome.grid(
    row=0,
    column=0,
    padx=5,
    pady=5,
    sticky="w"
)

entrada_nome = tk.Entry(
    frame,
    width=60,
    font=("Arial", 12),
    bg="#222222",
    fg="#00FF00",
    insertbackground="white"
)

entrada_nome.grid(
    row=0,
    column=1,
    padx=5
)

# =========================================================
# PASTA
# =========================================================

label_pasta = tk.Label(
    frame,
    text="Pasta ou Disco:",
    font=("Arial", 12),
    bg="#111111",
    fg="white"
)

label_pasta.grid(
    row=1,
    column=0,
    padx=5,
    pady=5,
    sticky="w"
)

entrada_pasta = tk.Entry(
    frame,
    width=60,
    font=("Arial", 12),
    bg="#222222",
    fg="#00FF00",
    insertbackground="white"
)

entrada_pasta.grid(
    row=1,
    column=1,
    padx=5
)

botao_escolher = tk.Button(
    frame,
    text="ESCOLHER",
    command=escolher_pasta,
    bg="#333333",
    fg="white",
    font=("Arial", 10, "bold")
)

botao_escolher.grid(
    row=1,
    column=2,
    padx=5
)

# =========================================================
# BOTÕES
# =========================================================

frame_botoes = tk.Frame(
    janela,
    bg="#111111"
)

frame_botoes.pack(
    pady=10
)

botao_buscar = tk.Button(
    frame_botoes,
    text="INICIAR BUSCA",
    command=iniciar_busca,
    bg="#008000",
    fg="white",
    width=18,
    height=2,
    font=("Arial", 11, "bold")
)

botao_buscar.grid(
    row=0,
    column=0,
    padx=5
)

botao_parar = tk.Button(
    frame_botoes,
    text="PARAR BUSCA",
    command=parar_busca,
    bg="#800000",
    fg="white",
    width=18,
    height=2,
    font=("Arial", 11, "bold")
)

botao_parar.grid(
    row=0,
    column=1,
    padx=5
)

botao_salvar = tk.Button(
    frame_botoes,
    text="SALVAR TXT",
    command=salvar_txt,
    bg="#004080",
    fg="white",
    width=18,
    height=2,
    font=("Arial", 11, "bold")
)

botao_salvar.grid(
    row=0,
    column=2,
    padx=5
)

# =========================================================
# PESQUISA RESULTADO
# =========================================================

frame_pesquisa = tk.Frame(
    janela,
    bg="#111111"
)

frame_pesquisa.pack(
    pady=5
)

label_pesquisa = tk.Label(
    frame_pesquisa,
    text="Pesquisar nos resultados:",
    bg="#111111",
    fg="white",
    font=("Arial", 11)
)

label_pesquisa.grid(
    row=0,
    column=0,
    padx=5
)

entrada_pesquisa = tk.Entry(
    frame_pesquisa,
    width=40,
    font=("Arial", 11),
    bg="#222222",
    fg="#00FF00",
    insertbackground="white"
)

entrada_pesquisa.grid(
    row=0,
    column=1,
    padx=5
)

botao_pesquisar = tk.Button(
    frame_pesquisa,
    text="PESQUISAR",
    command=pesquisar_resultado,
    bg="#555500",
    fg="white",
    font=("Arial", 10, "bold")
)

botao_pesquisar.grid(
    row=0,
    column=2,
    padx=5
)

botao_limpar_pesquisa = tk.Button(
    frame_pesquisa,
    text="LIMPAR",
    command=limpar_pesquisa,
    bg="#444444",
    fg="white",
    font=("Arial", 10, "bold")
)

botao_limpar_pesquisa.grid(
    row=0,
    column=3,
    padx=5
)

# =========================================================
# BARRA
# =========================================================

frame_barra = tk.Frame(
    janela,
    bg="#111111"
)

frame_barra.pack(
    pady=10
)

barra_progresso = ttk.Progressbar(
    frame_barra,
    style="green.Horizontal.TProgressbar",
    orient="horizontal",
    length=950,
    mode="determinate",
    maximum=100
)

barra_progresso.grid(
    row=0,
    column=0,
    padx=10
)

label_porcentagem = tk.Label(
    frame_barra,
    text="0%",
    font=("Arial", 12, "bold"),
    bg="#111111",
    fg="#00FF00"
)

label_porcentagem.grid(
    row=0,
    column=1
)

# =========================================================
# RESULTADO
# =========================================================

resultado_texto = ScrolledText(
    janela,
    bg="black",
    fg="#00FF00",
    insertbackground="white",
    font=("Consolas", 10)
)

resultado_texto.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =========================================================
# EXECUTAR
# =========================================================

janela.mainloop()
