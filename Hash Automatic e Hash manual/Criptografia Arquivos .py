import tkinter as tk
from tkinter import filedialog, messagebox
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
import os

# Variável global para armazenar a chave na memória
chave_fixa = None

def carregar_ou_gerar_chave():
    """Gera uma nova chave de 16 bytes na memória."""
    global chave_fixa
    chave_fixa = get_random_bytes(16)
    messagebox.showinfo("Chave Gerada", "Uma nova chave foi gerada e está em uso. Salve a chave manualmente se desejar.")
    atualizar_label_chave()
    atualizar_chave_atual()
    return chave_fixa

def carregar_chave_de_arquivo():
    """Carrega uma chave salva de um arquivo .txt."""
    global chave_fixa
    caminho_chave = filedialog.askopenfilename(
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        title="Selecionar chave fixa"
    )
    if not caminho_chave:
        return
    try:
        with open(caminho_chave, "r") as f:
            chave_hex = f.read().strip()
            chave_fixa = bytes.fromhex(chave_hex)
        messagebox.showinfo("Sucesso", f"Chave carregada de:\n{caminho_chave}")
        atualizar_label_chave(caminho_chave)
        atualizar_chave_atual()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar chave:\n{e}")

def salvar_chave_em_outro_local():
    """Salva a chave atual em um arquivo escolhido pelo usuário."""
    global chave_fixa
    if chave_fixa is None:
        messagebox.showwarning("Aviso", "Nenhuma chave foi gerada ou carregada ainda.")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        initialfile="chave_fixa.txt",
        title="Salvar chave fixa como"
    )
    if not caminho_salvar:
        return

    try:
        with open(caminho_salvar, "w") as f:
            f.write(chave_fixa.hex())
        messagebox.showinfo("Sucesso", f"Chave fixa salva em:\n{caminho_salvar}")
        atualizar_label_chave(caminho_salvar)
        atualizar_chave_atual()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar chave:\n{e}")

def atualizar_label_chave(caminho=None):
    """Atualiza o texto da label com o status da chave."""
    if caminho:
        texto = f"Chave atual salva em: {caminho}"
    else:
        texto = "Chave atual NÃO salva. Gere ou carregue uma chave."
    label_status.config(text=texto)

def atualizar_chave_atual():
    """Adiciona a chave atual em hexadecimal à área de texto."""
    if chave_fixa:
        adicionar_mensagem_status(f"Chave atual: {chave_fixa.hex()}")
    else:
        adicionar_mensagem_status("Chave atual: Nenhuma chave carregada")

def adicionar_mensagem_status(mensagem):
    """Adiciona uma mensagem à área de texto de status."""
    area_status.config(state="normal")  # Habilita edição
    area_status.insert(tk.END, mensagem + "\n")
    area_status.see(tk.END)  # Rola automaticamente para o final
    area_status.config(state="disabled")  # Desabilita edição pelo usuário

def criptografar_arquivo():
    """Criptografa múltiplos arquivos selecionados, salva como .bin e remove os originais."""
    global chave_fixa
    if chave_fixa is None:
        messagebox.showwarning("Aviso", "Gere ou carregue uma chave antes de criptografar.")
        return

    caminhos_arquivo = filedialog.askopenfilenames(
        filetypes=[("Todos os arquivos", "*.*")],
        title="Selecionar arquivos para criptografar"
    )
    if not caminhos_arquivo:
        return

    for caminho_arquivo in caminhos_arquivo:
        try:
            with open(caminho_arquivo, "rb") as arquivo:
                dados = arquivo.read()

            cipher = AES.new(chave_fixa, AES.MODE_EAX)
            nonce = cipher.nonce
            criptografado, tag = cipher.encrypt_and_digest(dados)

            extensao = os.path.splitext(caminho_arquivo)[1]
            saida_bin = caminho_arquivo.replace(extensao, "_cripto.bin")

            with open(saida_bin, "wb") as out_file:
                out_file.write(extensao.encode().ljust(10, b'#'))  # Extensão fixada em 10 bytes
                out_file.write(nonce + tag + criptografado)

            # Remove o arquivo original após a criptografia bem-sucedida
            os.remove(caminho_arquivo)
            adicionar_mensagem_status(f"\n\nSeu arquivo foi Criptografado: {os.path.basename(caminho_arquivo)}       🔐  {os.path.basename(saida_bin)}")
        except Exception as e:
            adicionar_mensagem_status(f"Erro ao criptografar {os.path.basename(caminho_arquivo)}: {e}")

def criptografar_pasta():
    """Criptografa todos os arquivos em uma pasta e suas subpastas, salva como .bin e remove os originais."""
    global chave_fixa
    if chave_fixa is None:
        messagebox.showwarning("Aviso", "Gere ou carregue uma chave antes de criptografar.")
        return

    pasta = filedialog.askdirectory(title="Selecionar pasta para criptografar")
    if not pasta:
        return

    for raiz, _, arquivos in os.walk(pasta):
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                with open(caminho_arquivo, "rb") as f:
                    dados = f.read()

                cipher = AES.new(chave_fixa, AES.MODE_EAX)
                nonce = cipher.nonce
                criptografado, tag = cipher.encrypt_and_digest(dados)

                extensao = os.path.splitext(caminho_arquivo)[1]
                saida_bin = caminho_arquivo.replace(extensao, "_cripto.bin")

                with open(saida_bin, "wb") as out_file:
                    out_file.write(extensao.encode().ljust(10, b'#'))  # Extensão fixada em 10 bytes
                    out_file.write(nonce + tag + criptografado)

                # Remove o arquivo original após a criptografia bem-sucedida
                os.remove(caminho_arquivo)
                adicionar_mensagem_status(f"\n\nSeu arquivo foi Criptografado: {os.path.relpath(caminho_arquivo, pasta)}       🔐  {os.path.relpath(saida_bin, pasta)}")
            except Exception as e:
                adicionar_mensagem_status(f"Erro ao criptografar {os.path.relpath(caminho_arquivo, pasta)}: {e}")

def descriptografar_arquivo():
    """Descriptografa múltiplos arquivos .bin, restaura com nome original e remove os .bin."""
    global chave_fixa
    if chave_fixa is None:
        messagebox.showwarning("Aviso", "Gere ou carregue uma chave antes de descriptografar.")
        return

    caminhos_bin = filedialog.askopenfilenames(
        filetypes=[
            ("Binários criptografados", "*.bin"),
            ("Todos os arquivos", "*.*")
        ],
        title="Selecionar arquivos criptografados"
    )
    if not caminhos_bin:
        return

    for caminho_bin in caminhos_bin:
        try:
            with open(caminho_bin, "rb") as bin_file:
                extensao = bin_file.read(10).decode().replace("#", "")
                conteudo = bin_file.read()
                nonce = conteudo[:16]
                tag = conteudo[16:32]
                dados_criptografados = conteudo[32:]

            cipher = AES.new(chave_fixa, AES.MODE_EAX, nonce=nonce)
            dados = cipher.decrypt_and_verify(dados_criptografados, tag)

            # Restaura o nome original removendo _cripto.bin e usando a extensão original
            saida_arquivo = caminho_bin.replace("_cripto.bin", extensao)
            with open(saida_arquivo, "wb") as arquivo:
                arquivo.write(dados)

            # Remove o arquivo .bin após descriptografia bem-sucedida
            os.remove(caminho_bin)
            adicionar_mensagem_status(f"\n\nSeu arquivo foi Descriptografado: {os.path.basename(caminho_bin)}      🔑   {os.path.basename(saida_arquivo)}")
        except ValueError:
            adicionar_mensagem_status(f"Erro ao descriptografar {os.path.basename(caminho_bin)}: Chave incorreta ou arquivo corrompido.")
        except Exception as e:
            adicionar_mensagem_status(f"Erro ao descriptografar {os.path.basename(caminho_bin)}: {e}")

def descriptografar_pasta():
    """Descriptografa todos os arquivos .bin em uma pasta e suas subpastas, restaura com nome original e remove os .bin."""
    global chave_fixa
    if chave_fixa is None:
        messagebox.showwarning("Aviso", "Gere ou carregue uma chave antes de descriptografar.")
        return

    pasta = filedialog.askdirectory(title="Selecionar pasta com arquivos criptografados")
    if not pasta:
        return

    for raiz, _, arquivos in os.walk(pasta):
        for arquivo in [arq for arq in arquivos if arq.endswith("_cripto.bin")]:
            caminho_bin = os.path.join(raiz, arquivo)
            try:
                with open(caminho_bin, "rb") as bin_file:
                    extensao = bin_file.read(10).decode().replace("#", "")
                    conteudo = bin_file.read()
                    nonce = conteudo[:16]
                    tag = conteudo[16:32]
                    dados_criptografados = conteudo[32:]

                cipher = AES.new(chave_fixa, AES.MODE_EAX, nonce=nonce)
                dados = cipher.decrypt_and_verify(dados_criptografados, tag)

                # Restaura o nome original removendo _cripto.bin e usando a extensão original
                saida_arquivo = caminho_bin.replace("_cripto.bin", extensao)
                with open(saida_arquivo, "wb") as arquivo:
                    arquivo.write(dados)

                # Remove o arquivo .bin após descriptografia bem-sucedida
                os.remove(caminho_bin)
                adicionar_mensagem_status(f"\n\nSeu arquivo foi Descriptografado: {os.path.relpath(caminho_bin, pasta)}      🔑   {os.path.relpath(saida_arquivo, pasta)}")
            except ValueError:
                adicionar_mensagem_status(f"Erro ao descriptografar {os.path.relpath(caminho_bin, pasta)}: Chave incorreta ou arquivo corrompido.")
            except Exception as e:
                adicionar_mensagem_status(f"Erro ao descriptografar {os.path.relpath(caminho_bin, pasta)}: {e}")

# --- Interface gráfica ---
janela = tk.Tk()
janela.title("Criptografia de Arquivos com Chave Fixa")
janela.geometry("820x850")  # Dimensões conforme fornecido

# Label para status da chave
label_status = tk.Label(janela, text="Nenhuma chave carregada. Gere ou carregue uma chave.", fg="red")
label_status.config(wraplength=500)
label_status.pack(pady=5)

# Label de instrução
label2 = tk.Label(janela, text="Escolha uma opção abaixo:")
label2.pack(pady=5)

# Botões para gerenciar a chave
botao_gerar_chave = tk.Button(janela, text="🔑 Gerar Nova Chave", command=carregar_ou_gerar_chave, bg="purple", width=30)
botao_gerar_chave.pack(pady=5)

botao_carregar_chave = tk.Button(janela, text="📂 Carregar Chave", command=carregar_chave_de_arquivo, bg="yellow", width=30)
botao_carregar_chave.pack(pady=5)

botao_salvar_chave = tk.Button(janela, text="💾 Salvar Chave em Outro Local", command=salvar_chave_em_outro_local, bg="orange", width=30)
botao_salvar_chave.pack(pady=5)

# Botões para criptografar/descriptografar arquivos e pastas
botao_cript_arquivo = tk.Button(janela, text="🔐 Criptografar Arquivo", command=criptografar_arquivo, bg="lightblue", width=30)
botao_cript_arquivo.pack(pady=5)

botao_descript_arquivo = tk.Button(janela, text="🔑 Descriptografar Arquivo", command=descriptografar_arquivo, bg="lightgreen", width=30)
botao_descript_arquivo.pack(pady=5)

botao_cript_pasta = tk.Button(janela, text="🔐 Criptografar Pasta", command=criptografar_pasta, bg="lightcoral", width=30)
botao_cript_pasta.pack(pady=5)

botao_descript_pasta = tk.Button(janela, text="🔑 Descriptografar Pasta", command=descriptografar_pasta, bg="lightyellow", width=30)
botao_descript_pasta.pack(pady=5)

# Frame para área de texto com scrollbar
frame_status = tk.Frame(janela)
frame_status.pack(pady=10, padx=10, fill="both", expand=True)

scrollbar = tk.Scrollbar(frame_status)
scrollbar.pack(side="right", fill="y")

area_status = tk.Text(frame_status, width=150, height=36, font=("Arial", 10), yscrollcommand=scrollbar.set)
area_status.pack(pady=10)
area_status.config(state="disabled")  # Desabilita edição pelo usuário

scrollbar.config(command=area_status.yview)

# Iniciar a interface
janela.mainloop()
