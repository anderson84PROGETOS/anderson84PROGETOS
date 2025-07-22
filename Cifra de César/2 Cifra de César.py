import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext

def cifra_cesar(texto, chave, modo):
    resultado = ""
    for char in texto:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            if modo == "Cifrar":
                resultado += chr((ord(char) - base + chave) % 26 + base)
            else:
                resultado += chr((ord(char) - base - chave) % 26 + base)
        else:
            resultado += char
    return resultado

def executar():
    texto = entrada_texto.get("1.0", tk.END).strip()
    try:
        chave = int(entrada_chave.get())
    except ValueError:
        resultado_label.config(text="Chave inválida. Use um número inteiro.", fg="red")
        return

    modo = modo_var.get()
    resultado = cifra_cesar(texto, chave, modo)
    saida_texto.delete("1.0", tk.END)
    saida_texto.insert(tk.END, resultado)
    resultado_label.config(text="", fg="green")

def salvar_chave_em_arquivo():
    try:
        chave = int(entrada_chave.get())
    except ValueError:
        messagebox.showerror("Erro", "Digite uma chave numérica antes de salvar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Salvar chave como..."
    )
    if caminho:
        try:
            with open(caminho, 'w') as f:
                f.write(str(chave))
            messagebox.showinfo("Sucesso", f"Chave salva em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

def carregar_chave_de_arquivo():
    caminho = filedialog.askopenfilename(
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Escolher Chave"
    )
    if caminho:
        try:
            with open(caminho, 'r') as f:
                chave = f.read().strip()
                entrada_chave.delete(0, tk.END)
                entrada_chave.insert(0, chave)
                resultado_label.config(text=f"Chave carregada: {chave}", fg="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar chave: {str(e)}")

def salvar_texto_entrada():
    texto = entrada_texto.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showerror("Erro", "Nenhum texto de entrada para salvar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Salvar texto de entrada como..."
    )
    if caminho:
        try:
            with open(caminho, 'w') as f:
                f.write(texto)
            messagebox.showinfo("Sucesso", f"Texto de entrada salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

def salvar_texto_resultado():
    texto = saida_texto.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showerror("Erro", "Nenhum texto de resultado para salvar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Salvar texto de resultado como..."
    )
    if caminho:
        try:
            with open(caminho, 'w') as f:
                f.write(texto)
            messagebox.showinfo("Sucesso", f"Texto de resultado salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

def carregar_texto_e_resultado():
    caminho = filedialog.askopenfilename(
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Carregar texto e resultado"
    )
    if caminho:
        try:
            with open(caminho, 'r') as f:
                conteudo = f.read()
                if '---' in conteudo:
                    texto_entrada, texto_resultado = conteudo.split('---')
                    entrada_texto.delete("1.0", tk.END)
                    entrada_texto.insert(tk.END, texto_entrada.strip())
                    saida_texto.delete("1.0", tk.END)
                    saida_texto.insert(tk.END, texto_resultado.strip())
                    resultado_label.config(text="Texto e resultado carregados com sucesso.", fg="green")
                else:
                    entrada_texto.delete("1.0", tk.END)
                    entrada_texto.insert(tk.END, conteudo.strip())
                    saida_texto.delete("1.0", tk.END)
                    resultado_label.config(text="Texto carregado (sem resultado).", fg="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")

def carregar_lista_palavras():
    # Change button color when clicked
    botao_wordlist.config(bg="#05fcf4")
    caminho = filedialog.askopenfilename(
        filetypes=[("Arquivos de Texto", "*.txt")],
        title="Escolher Lista de Palavras (ex. rockyou.txt)"
    )
    if not caminho:
        return

    texto_cifrado = entrada_texto.get("1.0", tk.END).strip()
    if not texto_cifrado:
        messagebox.showerror("Erro", "Nenhum texto cifrado para analisar.")
        return

    try:
        with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
            palavras = set(word.strip().lower() for word in f if word.strip())
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar lista de palavras: {str(e)}")
        return

    # Reset progress bar and label
    progress_bar['value'] = 0
    progress_label.config(text="Analisando chaves...")
    janela.update_idletasks()

    melhor_chave = 0
    maior_acertos = 0
    melhor_texto = ""
    chave = 0

    def processar_chave():
        nonlocal chave, melhor_chave, maior_acertos, melhor_texto
        if chave < 26:
            texto_decifrado = cifra_cesar(texto_cifrado, chave, "Decifrar")
            palavras_decifradas = texto_decifrado.lower().split()
            acertos = sum(1 for palavra in palavras_decifradas if palavra in palavras)
            if acertos > maior_acertos:
                maior_acertos = acertos
                melhor_chave = chave
                melhor_texto = texto_decifrado

            # Update progress bar
            progress_bar['value'] = (chave + 1) * (100 / 26)
            progress_label.config(text=f"Analisando chave {chave + 1}/26...")
            janela.update_idletasks()

            chave += 1
            # Schedule the next iteration
            janela.after(50, processar_chave)  # Small delay to keep GUI responsive
        else:
            # Analysis complete
            progress_bar['value'] = 0
            progress_label.config(text="Análise concluída")
            if maior_acertos > 0:
                entrada_chave.delete(0, tk.END)
                entrada_chave.insert(0, str(melhor_chave))
                saida_texto.delete("1.0", tk.END)
                saida_texto.insert(tk.END, melhor_texto)
                resultado_label.config(text=f"Chave estimada: {melhor_chave} (baseado em {maior_acertos} palavras encontradas).", fg="green")
            else:
                resultado_label.config(text="Nenhuma chave válida encontrada. Tente outra lista de palavras.", fg="red")

    # Start the analysis
    janela.after(50, processar_chave)

def executar_decifrar():
    modo_var.set("Decifrar")
    executar()

# Interface Gráfica
janela = tk.Tk()
janela.title("Cifra de César")
janela.wm_state('zoomed')
janela.geometry("1200x900")

# Texto de entrada
tk.Label(janela, text="Texto de Entrada").pack(pady=5)
entrada_texto = scrolledtext.ScrolledText(janela, width=100, height=15)
entrada_texto.pack()

# Entrada da chave
tk.Label(janela, text="Chave de Deslocamento").pack(pady=5)
entrada_chave = tk.Entry(janela, width=96)
entrada_chave.pack()

# Botões
frame_botoes = tk.Frame(janela)
botao_executar = tk.Button(frame_botoes, text="Executar", bg="#16fc05", fg="black", command=executar)
botao_executar.pack(side=tk.LEFT, padx=10)

botao_decifrar = tk.Button(frame_botoes, text="Decifrar", bg="#05fcf4", fg="black", command=executar_decifrar)
botao_decifrar.pack(side=tk.LEFT, padx=10)

ttk.Button(frame_botoes, text="Salvar Chave", command=salvar_chave_em_arquivo).pack(side=tk.LEFT, padx=10)
ttk.Button(frame_botoes, text="Salvar Texto de Entrada", command=salvar_texto_entrada).pack(side=tk.LEFT, padx=10)
ttk.Button(frame_botoes, text="Salvar Texto de Resultado", command=salvar_texto_resultado).pack(side=tk.LEFT, padx=10)
frame_botoes.pack(pady=10)

# Carregar chave, texto e lista de palavras
frame_chaves = tk.Frame(janela)
tk.Label(frame_chaves, text="Escolher Arquivo:").pack(side=tk.LEFT, padx=5)
ttk.Button(frame_chaves, text="Carregar Chave de Arquivo", command=carregar_chave_de_arquivo).pack(side=tk.LEFT, padx=10)
tk.Button(frame_chaves, text="Carregar Texto e Resultado", bg="#fcaa05", fg="black", command=carregar_texto_e_resultado).pack(side=tk.LEFT, padx=10)
botao_wordlist = tk.Button(frame_chaves, text="Carregar WordList", bg="#16fc05", fg="black", command=carregar_lista_palavras)
botao_wordlist.pack(side=tk.LEFT, padx=10)
frame_chaves.pack(pady=10)

# Progresso (always visible)
progress_label = tk.Label(janela, text="Análise concluída")
progress_label.pack(pady=5)
progress_bar = ttk.Progressbar(janela, orient="horizontal", length=250, mode="determinate", maximum=100)
progress_bar.pack(pady=5)

# Modo: Cifrar ou Decifrar
modo_var = tk.StringVar(value="Cifrar")
frame_modo = tk.Frame(janela)
tk.Radiobutton(frame_modo, text="Cifrar", variable=modo_var, value="Cifrar").pack(side=tk.LEFT)
tk.Radiobutton(frame_modo, text="Decifrar", variable=modo_var, value="Decifrar").pack(side=tk.LEFT)
frame_modo.pack(pady=10)

# Resultado
tk.Label(janela, text="Resultado").pack()
saida_texto = scrolledtext.ScrolledText(janela, width=100, height=15)
saida_texto.pack()

# Mensagem de status
resultado_label = tk.Label(janela, text="", fg="red")
resultado_label.pack(pady=5)

# Iniciar interface
janela.mainloop()
