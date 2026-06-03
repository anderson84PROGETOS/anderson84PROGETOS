import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string

# ====================================
# GERAR SENHAS
# ====================================

def gerar_senha():
    try:
        tamanho = int(entry_tamanho.get())
        quantidade = int(entry_quantidade.get())

        if tamanho < 1:
            messagebox.showerror("Erro", "O tamanho da senha deve ser maior que 0.")
            return

        if quantidade < 1:
            messagebox.showerror("Erro", "A quantidade deve ser maior que 0.")
            return

        caracteres = ""

        if var_minuscula.get():
            caracteres += string.ascii_lowercase

        if var_maiuscula.get():
            caracteres += string.ascii_uppercase

        if var_numeros.get():
            caracteres += string.digits

        if var_simbolos.get():
            caracteres += (
                "!@#$%¨&*()_+-="
                "[]{}"
                "§"
                "ªº"
                "¹²³"
                "£¢¬"
                "´`^~"
                ".,;:"
                "/?|\\"
                "<>"
                "\"'"
            )

        if not caracteres:
            messagebox.showerror("Erro", "Selecione pelo menos uma opção.")
            return
        
        lista_senhas = []

        for _ in range(quantidade):
            senha = ''.join(
                secrets.choice(caracteres)
                for _ in range(tamanho)
            )
            lista_senhas.append(senha)

        resultado.delete("1.0", tk.END)
        resultado.insert(
            tk.END,
            "\n".join(lista_senhas)
        )

    except ValueError:
        messagebox.showerror("Erro", "Digite apenas números válidos.")

# ====================================
# SALVAR TXT
# ====================================

def salvar_txt():
    texto = resultado.get("1.0", tk.END).strip()

    if not texto:
        messagebox.showerror("Erro", "Nada para salvar.")
        return

    arquivo = filedialog.asksaveasfilename(
        title="Salvar Senhas",
        defaultextension=".txt",
        filetypes=[
            ("Arquivo TXT", "*.txt"),
            ("Todos os arquivos", "*.*")
        ]
    )

    if arquivo:
        with open(arquivo, "w", encoding="utf-8") as f: f.write(texto)

        messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")

# ====================================
# LIMPAR
# ====================================

def limpar():
    resultado.delete("1.0", tk.END)

# ====================================
# JANELA
# ====================================

janela = tk.Tk()
janela.title("Gerador de Senhas")
janela.geometry("650x600")
janela.resizable(False, False)

# ====================================
# TÍTULO
# ====================================

titulo = tk.Label(janela, text="GERADOR PROFISSIONAL DE SENHAS", font=("Arial", 16, "bold"))
titulo.pack(pady=10)

# ====================================
# TAMANHO
# ====================================

frame1 = tk.Frame(janela)

frame1.pack(pady=5)

tk.Label(frame1, text="Tamanho da senha:").pack(side=tk.LEFT)

entry_tamanho = tk.Entry(frame1, width=10)

entry_tamanho.insert(0, "16")

entry_tamanho.pack(side=tk.LEFT, padx=5)

# ====================================
# QUANTIDADE
# ====================================

frame2 = tk.Frame(janela)
frame2.pack(pady=5)

tk.Label(frame2, text="Quantidade de senhas:").pack(side=tk.LEFT)

entry_quantidade = tk.Entry(frame2, width=10)

entry_quantidade.insert(0, "1")
entry_quantidade.pack(side=tk.LEFT, padx=5)

# ====================================
# CHECKBOXES
# ====================================

var_minuscula = tk.BooleanVar(value=True)
var_maiuscula = tk.BooleanVar(value=True)
var_numeros = tk.BooleanVar(value=True)
var_simbolos = tk.BooleanVar(value=True)

tk.Checkbutton(janela, text="Letras minúsculas (a-z)", variable=var_minuscula).pack(anchor="w", padx=40)

tk.Checkbutton(janela, text="Letras maiúsculas (A-Z)", variable=var_maiuscula).pack(anchor="w", padx=40)

tk.Checkbutton(janela, text="Números (0-9)", variable=var_numeros).pack(anchor="w", padx=40)

tk.Checkbutton(janela, text="Símbolos especiais", variable=var_simbolos).pack(anchor="w", padx=40)

# ====================================
# BOTÕES
# ====================================

frame_botoes = tk.Frame(janela)

frame_botoes.pack(pady=15)

btn_gerar = tk.Button(frame_botoes, text="GERAR", bg="#28a745", fg="black", width=15, font=("Arial", 10, "bold"), command=gerar_senha)

btn_gerar.grid(row=0, column=0, padx=5)

btn_salvar = tk.Button(frame_botoes, text="SALVAR TXT", bg="#ff9800", fg="black", width=15, font=("Arial", 10, "bold"), command=salvar_txt)

btn_salvar.grid(row=0, column=2, padx=5)

btn_limpar = tk.Button(frame_botoes, text="LIMPAR", bg="#dc3545", fg="black", width=15, font=("Arial", 10, "bold"), command=limpar)

btn_limpar.grid(row=0, column=3, padx=5)

# ====================================
# RESULTADO
# ====================================

frame_texto = tk.Frame(janela)

frame_texto.pack(fill="both", expand=True, padx=10, pady=10)

scroll = tk.Scrollbar(frame_texto)

scroll.pack(side=tk.RIGHT, fill=tk.Y)

resultado = tk.Text(frame_texto, width=75, height=20, font=("Consolas", 10), yscrollcommand=scroll.set)

resultado.pack(side=tk.LEFT, fill="both", expand=True)

scroll.config(command=resultado.yview)

# ====================================
# EXECUTAR
# ====================================

janela.mainloop()
