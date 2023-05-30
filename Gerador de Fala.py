import tkinter as tk
import pyttsx3

def gerar_fala():
    texto = entrada.get("1.0", tk.END)
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)  # Velocidade da fala (opcional)
    engine.say(texto)
    engine.runAndWait()

def limpar_texto():
    entrada.delete("1.0", tk.END)

# Cria a janela
janela = tk.Tk()
janela.wm_state('zoomed')
janela.title("Gerador de Fala")
janela.geometry("400x400")

# Cria um botão para gerar a fala
botao_gerar = tk.Button(janela, text="Gerar Fala", command=gerar_fala, bg="#00FA9A")
botao_gerar.grid(row=0, column=0, pady=10)

# Cria um botão para limpar o texto
botao_limpar = tk.Button(janela, text="Limpar Texto", command=limpar_texto, bg="#D2691E")
botao_limpar.grid(row=0, column=1, pady=10)

# Cria um campo de entrada de texto
entrada = tk.Text(janela, height=50, width=150, font=("TkDefaultFont", 11, "bold"))
entrada.grid(row=1, column=0, columnspan=2, padx=10)

# Inicia o loop de eventos da janela
janela.mainloop()
