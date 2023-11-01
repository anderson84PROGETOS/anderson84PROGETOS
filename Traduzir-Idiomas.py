import tkinter as tk
from googletrans import Translator

def translate_to_languages():
    text_to_translate = info_text.get(1.0, tk.END)
    translator = Translator()
    info_text.delete(1.0, tk.END)  # Limpa o conteúdo anterior
    for lang, translation in translations.items():
        translated_text = translator.translate(text_to_translate, dest=lang)
        info_text.insert(tk.END, f'{lang} ({translation}): {translated_text.text}\n\n\n\n')  # Adiciona um espaço após cada tradução

def clear_results():
    info_text.delete(1.0, tk.END)

# Exemplo de idiomas para tradução
translations = {
    "en": "Inglês",
    "pt": "Português",
    "es": "Espanhol",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
    "ru": "Russo",
    "ja": "Japonês",
    "zh-CN": "Chinês",
    "ko": "Coreano"
}

# Configura a janela
window = tk.Tk()
window.title("Traduzir Texto para Vários Idiomas :   Inglês    Português    Espanhol    Francês    Alemão    Italiano    Russo    Japonês    Chinês    Coreano")
window.state('zoomed')
window.geometry("1200x1000")

translate_button = tk.Button(window, text="Traduzir Para idiomas", command=translate_to_languages, font=("Helvetica", 10, "bold"), bg="#00FFFF")
translate_button.pack(pady=10)

info_text = tk.Text(window, wrap=tk.WORD, width=130, height=45, font=("Helvetica", 12, "bold"))
info_text.pack()

clear_button = tk.Button(window, text="Limpar tudo", command=clear_results, font=("Helvetica", 10, "bold"), bg="#D2691E")
clear_button.pack(pady=10)

# Inicia a interface gráfica
window.mainloop()
