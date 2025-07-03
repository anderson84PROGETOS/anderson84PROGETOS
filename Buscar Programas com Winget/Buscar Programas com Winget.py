import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext

def run_winget(command_type):
    programa = entrada.get().strip()
    comando = []

    if command_type == "search":
        if not programa:
            resultado_text.delete("1.0", tk.END)
            resultado_text.insert(tk.END, "Digite o nome de um programa")
            return
        comando = ["winget", "search", programa]

    elif command_type in ("list", "list_all"):
        comando = ["winget", "list"]

    else:
        return

    try:
        # Run the command with UTF-8 encoding
        resultado = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', shell=True)
        saida = resultado.stdout if resultado.stdout else resultado.stderr
    except Exception as e:
        saida = f"Erro ao executar o comando: {e}"

    resultado_text.delete("1.0", tk.END)

    # Format output for winget list
    if command_type in ("list", "list_all"):
        linhas = saida.splitlines()

        # Skip header and format output
        cabecalho_formatado = "{:<90} {:<45} {:<15}".format("Nome", "ID", "Versão")
        resultado_formatado = [cabecalho_formatado, "-"*154]

        # Process lines after the header
        for linha in linhas[1:]:
            partes = linha.split()
            if len(partes) < 3:
                continue
            # Join parts for name, ID, and version
            nome = " ".join(partes[:-2])
            ident = partes[-2]
            versao = partes[-1]
            if command_type == "list" and programa.lower() not in nome.lower():
                continue
            resultado_formatado.append("{:<90} {:<45} {:<15}".format(nome, ident, versao))

        resultado_text.insert(tk.END, "\n\n".join(resultado_formatado if len(resultado_formatado) > 2 else ["Nenhuma correspondência encontrada."]))

    else:
        resultado_text.insert(tk.END, saida)

# Create the main window
janela = tk.Tk()
janela.title("Buscar Programas com Winget")
janela.geometry("850x500")
janela.state("zoomed")  # abre em tela cheia no Windows

# Input field
frame_top = ttk.Frame(janela)
frame_top.pack(pady=10)

ttk.Label(frame_top, text="Nome do programa").pack(pady=5)
entrada = ttk.Entry(frame_top, width=80)
entrada.pack(pady=5)

# Buttons
frame_botoes = ttk.Frame(janela)
frame_botoes.pack(pady=5)

botao_listar = tk.Button(frame_botoes, text="Listar Todos", command=lambda: run_winget("list_all"), bg="#05fc4f", fg="black")
botao_listar.pack(side="left", padx=5)

botao_filtrar = tk.Button(frame_botoes, text="Filtrar Instalados", command=lambda: run_winget("list"), bg="#05fcf0", fg="black")
botao_filtrar.pack(side="left", padx=5)

botao_pesquisar = tk.Button(frame_botoes, text="Pesquisar (winget search)", command=lambda: run_winget("search"), bg="#fcf005", fg="black")
botao_pesquisar.pack(side="left", padx=5)

# Result area with scrollbar
resultado_text = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=190, height=50)
resultado_text.pack(pady=10, padx=10)

# Start the main loop
janela.mainloop()
