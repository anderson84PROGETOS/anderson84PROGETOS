import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText  # Importar ScrolledText para barra de rolagem

# Função para escolher o diretório onde a pasta será criada
def escolher_diretorio():
    caminho = filedialog.askdirectory()
    if caminho:
        pasta_selecionada.set(caminho)

# Função para criar a pasta, salvar o arquivo e exibir o conteúdo
def salvar_arquivo():
    nome_pasta = entrada_pasta.get()
    nome_arquivo = entrada_arquivo.get()
    conteudo_usuario = entrada_conteudo.get("1.0", tk.END)

    if not nome_pasta or not nome_arquivo:
        messagebox.showwarning("Atenção", "Por favor, insira o nome da pasta e do arquivo.")
        return

    # Verificar se o arquivo tem a extensão .txt, senão adicionar
    if not nome_arquivo.endswith(".txt"):
        nome_arquivo += ".txt"

    caminho_pasta = os.path.join(pasta_selecionada.get(), nome_pasta)

    # Verifique se a pasta existe, caso contrário, crie-a
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)

    # Caminho completo do arquivo
    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)

    # Crie o arquivo e escreva o conteúdo do usuário nele
    with open(caminho_completo, 'w') as arquivo:
        arquivo.write(conteudo_usuario)
    
    # Exibe uma mensagem de sucesso
    messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' salvo com sucesso em '{caminho_pasta}'.")

    # Limpa o conteúdo do ScrolledText e exibe o conteúdo recém-salvo
    text_output.delete(1.0, tk.END)  # Limpar a área de texto
    text_output.insert(tk.END, f"Conteúdo salvo no arquivo: {nome_arquivo}\n\n{conteudo_usuario}")

# Configuração da janela principal
janela = tk.Tk()
janela.geometry("1200x950")
janela.title("Criar Pasta e Texto")

# Variáveis
pasta_selecionada = tk.StringVar()

# Labels e botões
label_diretorio = tk.Label(janela, text="Selecione o diretório onde a pasta será criada", font=("TkDefaultFont", 11, "bold"))
label_diretorio.pack(pady=5)

botao_diretorio = tk.Button(janela, text="Escolher Diretório", command=escolher_diretorio, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
botao_diretorio.pack(pady=5)

label_pasta = tk.Label(janela, text="Nome da Pasta", font=("TkDefaultFont", 11, "bold"))
label_pasta.pack(pady=5)

entrada_pasta = tk.Entry(janela, width=30, font=("TkDefaultFont", 11, "bold"))
entrada_pasta.pack(pady=5)

label_arquivo = tk.Label(janela, text="Nome do Arquivo (.txt)", font=("TkDefaultFont", 11, "bold"))
label_arquivo.pack(pady=5)

entrada_arquivo = tk.Entry(janela, width=30, font=("TkDefaultFont", 11, "bold"))
entrada_arquivo.pack(pady=5)

label_conteudo = tk.Label(janela, text="Conteúdo do Arquivo", font=("TkDefaultFont", 11, "bold"))
label_conteudo.pack(pady=5)

entrada_conteudo = tk.Text(janela, width=120, height=15, font=("TkDefaultFont", 11, "bold"))
entrada_conteudo.pack(pady=5)

botao_salvar = tk.Button(janela, text="Salvar Arquivo", command=salvar_arquivo, font=("TkDefaultFont", 11, "bold"), bg='red')
botao_salvar.pack(pady=10)

# Área de texto com barra de rolagem para exibir o conteúdo
text_output = ScrolledText(janela, wrap=tk.WORD, width=120, height=15, font=("TkDefaultFont", 11, "bold"))
text_output.pack(pady=10)

# Iniciar a interface
janela.mainloop()
