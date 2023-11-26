import tkinter as tk
import requests
from bs4 import BeautifulSoup
from translate import Translator

def get_explanation(command):
    url = f"https://www.explainshell.com/explain?cmd={command}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        explanation_pre = soup.find('pre')

        if explanation_pre:
            explanation = explanation_pre.text.strip()
            return explanation, find_portuguese_translation(explanation)
        else:
            return "A explicação não pôde ser encontrada no site.", ""
    else:
        return "Não foi possível obter a explicação.", ""

def find_portuguese_translation(text):
    # Traduz o texto para o português usando a biblioteca 'translate'
    translator = Translator(to_lang="pt")
    translation = translator.translate(text)
    return translation

def show_explanation():
    command = entry.get()
    explanation_en, explanation_pt = get_explanation(command)

    text_box.delete(1.0, tk.END)  # Limpa o conteúdo atual da Textbox

    # Exibe a explicação em inglês e português, se disponível
    if explanation_en:
        text_box.insert(tk.END, f"Inglês: {explanation_en}\n\n")
    if explanation_pt:
        text_box.insert(tk.END, f"Português: {explanation_pt}")

# Criar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Explique o Comando do Linux")

# Criar widgets
label = tk.Label(window, text="Digite um comando do Linux", font=("TkDefaultFont", 12, "bold"))
entry = tk.Entry(window, width=30, font=("TkDefaultFont", 12, "bold"))
button = tk.Button(window, text="Obter Explicação", command=show_explanation, font=("Arial", 12) ,bg="#00FFFF")
text_box = tk.Text(window, height=30, width=120, font=("TkDefaultFont", 12, "bold"))

# Posicionar widgets na janela
label.pack(pady=10)
entry.pack(pady=10)
button.pack(pady=10)
text_box.pack(pady=10)

# Iniciar o loop principal da interface gráfica
window.mainloop()
