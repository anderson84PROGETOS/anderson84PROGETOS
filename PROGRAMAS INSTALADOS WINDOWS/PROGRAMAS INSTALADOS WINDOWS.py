import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg
import threading
from datetime import datetime
import subprocess
import os

# =========================================================
# VARIÁVEIS
# =========================================================

programas = []

# =========================================================
# FUNÇÕES
# =========================================================

def converter_tamanho(size_mb):

    try:

        size_mb = float(size_mb)

        if size_mb >= 1024:
            return f"{size_mb / 1024:.2f} GB"

        return f"{size_mb:.2f} MB"

    except:

        return "Desconhecido"


def formatar_data(data):

    try:

        data = str(data)

        if len(data) == 8 and data.isdigit():

            return datetime.strptime(
                data,
                "%Y%m%d"
            ).strftime("%d/%m/%Y")

        return data

    except:

        return "Desconhecida"


def pegar_data_pasta(caminho):

    try:

        if caminho and os.path.exists(caminho):

            timestamp = os.path.getctime(caminho)

            data = datetime.fromtimestamp(timestamp)

            return data.strftime("%d/%m/%Y")

    except:
        pass

    return "Desconhecida"


def abrir_pasta_programa(event):

    selecionado = tree.selection()

    if not selecionado:
        return

    item = tree.item(selecionado)

    nome = item["values"][0]

    for prog in programas:

        if prog["nome"] == nome:

            pasta = prog["local"]

            if pasta and os.path.exists(pasta):

                subprocess.Popen(f'explorer "{pasta}"')

            else:

                messagebox.showwarning(
                    "Aviso",
                    "Pasta do programa não encontrada."
                )

            return


def ler_programas_registro(root_key, path):

    lista = []

    try:

        registro = winreg.OpenKey(root_key, path)

        total_subchaves = winreg.QueryInfoKey(registro)[0]

        for i in range(total_subchaves):

            try:

                subkey_name = winreg.EnumKey(registro, i)

                subkey_path = path + "\\" + subkey_name

                subkey = winreg.OpenKey(root_key, subkey_path)

                # =====================================================
                # NOME
                # =====================================================

                try:
                    nome = winreg.QueryValueEx(
                        subkey,
                        "DisplayName"
                    )[0]
                except:
                    nome = ""

                if not nome:
                    continue

                # =====================================================
                # VERSÃO
                # =====================================================

                try:
                    versao = winreg.QueryValueEx(
                        subkey,
                        "DisplayVersion"
                    )[0]
                except:
                    versao = "Desconhecida"

                # =====================================================
                # FABRICANTE
                # =====================================================

                try:
                    fabricante = winreg.QueryValueEx(
                        subkey,
                        "Publisher"
                    )[0]
                except:
                    fabricante = "Desconhecido"

                # =====================================================
                # CAMINHO / LOCAL
                # =====================================================

                local = ""

                try:

                    local = winreg.QueryValueEx(
                        subkey,
                        "InstallLocation"
                    )[0]

                except:
                    pass

                # tenta pegar pelo ícone executável

                if not local:

                    try:

                        icone = winreg.QueryValueEx(
                            subkey,
                            "DisplayIcon"
                        )[0]

                        if icone:

                            local = os.path.dirname(
                                icone.split(",")[0]
                            )

                    except:
                        pass

                # tenta pegar pelo uninstall string

                if not local:

                    try:

                        uninstall = winreg.QueryValueEx(
                            subkey,
                            "UninstallString"
                        )[0]

                        if uninstall:

                            local = os.path.dirname(
                                uninstall.split(".exe")[0]
                            )

                    except:
                        pass

                # =====================================================
                # DATA
                # =====================================================

                data = "Desconhecida"

                try:

                    data_registro = winreg.QueryValueEx(
                        subkey,
                        "InstallDate"
                    )[0]

                    data = formatar_data(data_registro)

                except:
                    pass

                if data == "Desconhecida":

                    data = pegar_data_pasta(local)

                # =====================================================
                # TAMANHO
                # =====================================================

                try:

                    tamanho = winreg.QueryValueEx(
                        subkey,
                        "EstimatedSize"
                    )[0]

                    tamanho = converter_tamanho(
                        float(tamanho) / 1024
                    )

                except:

                    tamanho = "Desconhecido"

                # =====================================================
                # ADICIONA
                # =====================================================

                lista.append({

                    "nome": nome,
                    "versao": versao,
                    "fabricante": fabricante,
                    "data": data,
                    "tamanho": tamanho,
                    "local": local

                })

            except:
                pass

    except:
        pass

    return lista


def atualizar_tabela(lista):

    tree.delete(*tree.get_children())

    for prog in lista:

        tree.insert(
            "",
            "end",
            values=(

                prog['nome'],
                prog['versao'],
                prog['fabricante'],
                prog['data'],
                prog['tamanho'],
                prog['local']

            )
        )


def escanear_programas():

    global programas

    botao_scan.config(state="disabled")

    tree.delete(*tree.get_children())

    status_var.set("Escaneando programas instalados...")

    programas = []

    caminhos = [

        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),

        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ),

        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        )
    ]

    for root, path in caminhos:

        programas.extend(
            ler_programas_registro(root, path)
        )

    # =====================================================
    # REMOVE DUPLICADOS
    # =====================================================

    vistos = set()

    programas_unicos = []

    for prog in programas:

        chave = prog["nome"]

        if chave not in vistos:

            vistos.add(chave)

            programas_unicos.append(prog)

    programas = sorted(

        programas_unicos,

        key=lambda x: x['nome'].lower()

    )

    atualizar_tabela(programas)

    status_var.set(
        f"Programas encontrados: {len(programas)}"
    )

    botao_scan.config(state="normal")


def iniciar_scan():

    threading.Thread(
        target=escanear_programas,
        daemon=True
    ).start()


def pesquisar_programa(event=None):

    termo = entrada_pesquisa.get().lower().strip()

    if not termo:

        atualizar_tabela(programas)

        status_var.set(
            f"Mostrando todos os programas ({len(programas)})"
        )

        return

    filtrados = []

    for prog in programas:

        if (

            termo in prog['nome'].lower()
            or termo in prog['data'].lower()
            or termo in prog['fabricante'].lower()
            or termo in prog['local'].lower()

        ):

            filtrados.append(prog)

    atualizar_tabela(filtrados)

    status_var.set(
        f"Resultados encontrados: {len(filtrados)}"
    )


def salvar_txt():

    if not programas:

        messagebox.showwarning(
            "Aviso",
            "Nenhum dado encontrado."
        )

        return

    caminho = filedialog.asksaveasfilename(

        defaultextension=".txt",

        filetypes=[
            ("Arquivo TXT", "*.txt")
        ],

        title="Salvar relatório"

    )

    if not caminho:
        return

    try:

        with open(caminho, "w", encoding="utf-8") as f:

            f.write("=" * 90 + "\n")
            f.write("PROGRAMAS INSTALADOS WINDOWS\n")
            f.write("=" * 90 + "\n\n")

            for prog in programas:

                f.write(f"NOME: {prog['nome']}\n")
                f.write(f"VERSÃO: {prog['versao']}\n")
                f.write(f"FABRICANTE: {prog['fabricante']}\n")
                f.write(f"DATA: {prog['data']}\n")
                f.write(f"TAMANHO: {prog['tamanho']}\n")
                f.write(f"CAMINHO: {prog['local']}\n")

                f.write("-" * 90 + "\n")

        messagebox.showinfo(
            "Sucesso",
            "Arquivo salvo com sucesso."
        )

    except Exception as e:

        messagebox.showerror(
            "Erro",
            str(e)
        )

valor_copiado = ""


def selecionar_celula(event):

    global valor_copiado

    item_id = tree.identify_row(event.y)

    coluna = tree.identify_column(event.x)

    if not item_id or not coluna:
        return

    item = tree.item(item_id)

    valores = item["values"]

    indice = int(coluna.replace("#", "")) - 1

    if indice < len(valores):

        valor_copiado = str(valores[indice])

        status_var.set(
            f"Selecionado para copiar: {valor_copiado}"
        )


def copiar_valor():

    global valor_copiado

    if not valor_copiado:

        messagebox.showwarning(
            "Aviso",
            "Clique em uma célula primeiro."
        )

        return

    janela.clipboard_clear()

    janela.clipboard_append(valor_copiado)

    janela.update()

    status_var.set(
        f"Copiado: {valor_copiado}"
    )

    messagebox.showinfo(
        "Copiado",
        valor_copiado
    )

# =========================================================
# INTERFACE
# =========================================================

janela = tk.Tk()

janela.title("PROGRAMAS INSTALADOS WINDOWS")

janela.geometry("1600x750")

janela.state("zoomed")

janela.configure(bg="#111111")

# =========================================================
# ESTILO
# =========================================================

style = ttk.Style()

style.theme_use("clam")

style.configure(

    "Treeview",

    background="#1e1e1e",
    foreground="lime",

    fieldbackground="#1e1e1e",

    rowheight=30,

    font=("Consolas", 10)

)

style.configure(

    "Treeview.Heading",

    background="#222222",

    foreground="cyan",

    font=("Consolas", 10, "bold")

)

# =========================================================
# TOPO
# =========================================================

frame_topo = tk.Frame(
    janela,
    bg="#111111"
)

frame_topo.pack(
    fill="x",
    pady=10
)

# BOTÃO ESCANEAR

botao_scan = tk.Button(

    frame_topo,

    text="ESCANEAR PROGRAMAS",

    command=iniciar_scan,

    bg="#00aa00",

    fg="white",

    font=("Consolas", 11, "bold"),

    width=24

)

botao_scan.pack(
    side="left",
    padx=10
)

# BOTÃO SALVAR

botao_salvar = tk.Button(

    frame_topo,

    text="SALVAR TXT",

    command=salvar_txt,

    bg="#0055aa",

    fg="white",

    font=("Consolas", 11, "bold"),

    width=18

)

botao_salvar.pack(
    side="left",
    padx=10
)

botao_copiar = tk.Button(

    frame_topo,

    text="COPIAR",

    command=copiar_valor,

    bg="#aa5500",

    fg="white",

    font=("Consolas", 11, "bold"),

    width=14

)

botao_copiar.pack(
    side="left",
    padx=10
)

# PESQUISA

label_pesquisa = tk.Label(

    frame_topo,

    text="PESQUISAR:",

    bg="#111111",

    fg="cyan",

    font=("Consolas", 11, "bold")

)

label_pesquisa.pack(
    side="left",
    padx=(40, 5)
)

entrada_pesquisa = tk.Entry(

    frame_topo,

    bg="#1e1e1e",

    fg="lime",

    insertbackground="white",

    font=("Consolas", 11),

    width=45

)

entrada_pesquisa.pack(
    side="left",
    padx=5
)

entrada_pesquisa.bind(
    "<KeyRelease>",
    pesquisar_programa
)

# =========================================================
# TABELA
# =========================================================

colunas = (

    "Nome",
    "Versão",
    "Fabricante",
    "Data",
    "Tamanho",
    "Caminho"

)

frame_tabela = tk.Frame(
    janela,
    bg="#111111"
)

frame_tabela.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =========================================================
# ESTILO SCROLLBAR VERDE
# =========================================================

style.configure(
    "Vertical.TScrollbar",
    background="#00ff00",
    troughcolor="#111111",
    arrowcolor="black",
    bordercolor="#111111",
    darkcolor="#00aa00",
    lightcolor="#00ff00"
)

style.configure(
    "Horizontal.TScrollbar",
    background="#00ff00",
    troughcolor="#111111",
    arrowcolor="black",
    bordercolor="#111111",
    darkcolor="#00aa00",
    lightcolor="#00ff00"
)

# =========================================================
# SCROLLBARS
# =========================================================

scroll_y = ttk.Scrollbar(
    frame_tabela,
    orient="vertical",
    style="Vertical.TScrollbar"
)

scroll_y.pack(
    side="right",
    fill="y"
)

scroll_x = ttk.Scrollbar(
    frame_tabela,
    orient="horizontal",
    style="Horizontal.TScrollbar"
)

scroll_x.pack(
    side="bottom",
    fill="x"
)

tree = ttk.Treeview(

    frame_tabela,

    columns=colunas,

    show="headings",

    yscrollcommand=scroll_y.set,

    xscrollcommand=scroll_x.set

)

scroll_y.config(command=tree.yview)

scroll_x.config(command=tree.xview)

for col in colunas:

    tree.heading(col, text=col)

tree.column("Nome", width=510)

tree.column("Versão", width=160)

tree.column("Fabricante", width=250)

tree.column("Data", width=120)

tree.column("Tamanho", width=120)

tree.column("Caminho", width=700)

tree.pack(
    fill="both",
    expand=True
)

# DETECTA O MOUSE EM CIMA DAS CÉLULAS

# CLIQUE SELECIONA A CÉLULA

tree.bind(
    "<Button-1>",
    selecionar_celula
)

# =========================================================
# DUPLO CLIQUE
# =========================================================

tree.bind(
    "<Double-1>",
    abrir_pasta_programa
)

# =========================================================
# STATUS
# =========================================================

status_var = tk.StringVar()

status_var.set("Pronto")

status = tk.Label(

    janela,

    textvariable=status_var,

    bg="#111111",

    fg="lime",

    anchor="w",

    font=("Consolas", 10)

)

status.pack(
    fill="x",
    side="bottom"
)

# =========================================================
# EXECUTAR
# =========================================================

janela.mainloop()
