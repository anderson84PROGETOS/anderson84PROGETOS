import tkinter as tk
from tkinter import scrolledtext
import urllib.parse

def decodificar_url():
    """
    Função chamada quando o botão é pressionado.
    Decodifica a URL inserida pelo usuário, incluindo decodificação dupla.
    """
    # Obtém a URL do campo de entrada
    encoded_url = url_entry.get()

    # Decodifica a URL duas vezes para lidar com codificação dupla
    decoded_url = urllib.parse.unquote(urllib.parse.unquote(encoded_url))

    # Exibe o resultado no ScrolledText
    output_text.config(state='normal')  # Ativa edição temporariamente
    output_text.delete('1.0', tk.END)   # Limpa conteúdo anterior
    output_text.insert(tk.END, decoded_url)
    output_text.config(state='disabled')  # Desativa edição novamente

# Cria a janela principal
root = tk.Tk()
root.title("Decodificador de URL da Barra de Pesquisa do Windows")
root.geometry("1200x600")
root.state('zoomed')  # Abre a janela maximizada

# Label e Entry para a URL
tk.Label(root, text="Decodificador de URL da Barra de Pesquisa do Windows", font=("Arial", 11)).pack(pady=5)
url_entry = tk.Entry(root, width=120, font=("Arial", 11))
url_entry.pack(pady=5)

# Botão para decodificar
tk.Button(root, text="Decodificar URL", bg="#03fc24", fg="black", command=decodificar_url, font=("Arial", 10)).pack(pady=10)

# ScrolledText para mostrar o resultado
output_text = scrolledtext.ScrolledText(root, width=130, height=40, font=("Arial", 12), wrap=tk.WORD, state='disabled')
output_text.pack(pady=10)

# Inicia o loop da interface
root.mainloop()
