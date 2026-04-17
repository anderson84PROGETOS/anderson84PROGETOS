import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import xml.etree.ElementTree as ET

# Lista de veículos alvo
TARGET_VEHICLES = [
    "CivilianSedan",
    "CivilianSedan_Black",
    "CivilianSedan_Wine",
    "OffroadHatchback",
    "OffroadHatchback_Blue",
    "OffroadHatchback_White",
    "Offroad_02",
    "Sedan_02",
    "Hatchback_02",
    "Hatchback_02_Black",
    "Hatchback_02_Blue",
    "Boat_01_Black",
    "Boat_01_Blue",
    "Boat_01_Camo",
    "Boat_01_Orange"
]

NEW_LIFETIME = "3888000"


def selecionar_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione o types.xml",
        filetypes=[("XML files", "*.xml")]
    )

    if caminho:
        entrada_path.delete(0, tk.END)
        entrada_path.insert(0, caminho)


def editar_xml():
    caminho = entrada_path.get()

    if not caminho:
        messagebox.showerror("Erro", "Selecione um arquivo primeiro.")
        return

    try:
        tree = ET.parse(caminho)
        root = tree.getroot()

        tipos = root.findall("type")
        total = len(tipos)
        modificados = 0

        progress["value"] = 0
        janela.update_idletasks()

        for i, tipo in enumerate(tipos):
            nome = tipo.get("name")

            if nome in TARGET_VEHICLES:
                lifetime = tipo.find("lifetime")

                if lifetime is not None:
                    lifetime.text = NEW_LIFETIME
                    modificados += 1

            # Atualiza progresso
            porcentagem = ((i + 1) / total) * 100
            progress["value"] = porcentagem
            janela.update_idletasks()

        # Salvar novo arquivo
        novo_caminho = caminho.replace(".xml", "_editado.xml")
        tree.write(novo_caminho, encoding="utf-8", xml_declaration=True)

        progress["value"] = 100

        messagebox.showinfo(
            "Sucesso",
            f"Arquivo editado!\n\nVeículos modificados: {modificados}\n\nSalvo em: {novo_caminho}"
        )

    except Exception as e:
        messagebox.showerror("Erro", str(e))


# Interface gráfica
janela = tk.Tk()
janela.title("Editor DayZ types.xml")
janela.geometry("550x320")
janela.resizable(False, False)

label = tk.Label(janela, text="Selecione o arquivo types.xml:", font=("Arial", 10, "bold"))
label.pack(pady=8)

entrada_path = tk.Entry(janela, width=70)
entrada_path.pack(pady=5)

btn_procurar = tk.Button(janela, text="Procurar", command=selecionar_arquivo, bg="#ff6666", fg="black", font=("Arial", 10, "bold"))
btn_procurar.pack(pady=5)

btn_executar = tk.Button(janela, text="Editar Lifetime", command=editar_xml, bg="#2ecc71", fg="black", font=("Arial", 10, "bold"))
btn_executar.pack(pady=10)

# Barra de progresso
progress = Progressbar(janela, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=10)

janela.mainloop()
