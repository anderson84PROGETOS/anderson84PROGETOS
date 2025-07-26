import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

def mostrar_erro_personalizado(titulo, mensagem):
    erro_win = tk.Toplevel(janela)
    erro_win.title(titulo)
    erro_win.geometry("400x200")
    erro_win.configure(bg="white")
    erro_win.resizable(False, False)

    label_titulo = tk.Label(erro_win, text=titulo, font=("Arial", 14, "bold"), fg="red", bg="white")
    label_titulo.pack(pady=10)

    label_mensagem = tk.Label(erro_win, text=mensagem, font=("Arial", 12), wraplength=360, bg="white")
    label_mensagem.pack(pady=10)

    botao_ok = tk.Button(erro_win, text="OK", command=erro_win.destroy, font=("Arial", 11), bg="#05fc32", fg="black")
    botao_ok.pack(pady=10)

    erro_win.transient(janela)
    erro_win.grab_set()
    janela.wait_window(erro_win)

def converter_para_hex():
    texto = entrada.get("1.0", tk.END).rstrip('\n')
    if not texto.strip():
        messagebox.showwarning("Aviso", "Digite algum texto.")
        return

    resultado_hex = texto.encode("utf-8").hex()    
    texto_resultado.delete("1.0", tk.END)
    texto_resultado.insert(tk.END, resultado_hex)

def abrir_arquivo_hex_thread():
    threading.Thread(target=abrir_arquivo_hex, daemon=True).start()

def abrir_arquivo_hex():
    caminho = filedialog.askopenfilename(filetypes=[("Todos os arquivos", "*.*")])
    if not caminho:
        return

    try:
        tamanho_arquivo = os.path.getsize(caminho)
        if tamanho_arquivo == 0:
            messagebox.showinfo("Info", "Arquivo vazio.")
            return

        def reset_interface():
            hex_viewer.delete("1.0", tk.END)
            progresso['value'] = 0
        janela.after(0, reset_interface)

        with open(caminho, "rb") as f:
            bytes_lidos = 0
            bloco_tamanho = 4096
            while True:
                bloco = f.read(bloco_tamanho)
                if not bloco:
                    break

                linhas = []
                for i in range(0, len(bloco), 16):
                    segmento = bloco[i:i+16]
                    hex_part = ' '.join(f"{byte:02X}" for byte in segmento)
                    texto_legivel = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in segmento)
                    linha = f"{hex_part:<48}  {texto_legivel}\n"
                    linhas.append(linha)
                texto_para_inserir = ''.join(linhas)

                bytes_lidos += len(bloco)
                progresso_atual = (bytes_lidos / tamanho_arquivo) * 100

                def atualizar_interface():
                    hex_viewer.insert(tk.END, texto_para_inserir)
                    progresso['value'] = progresso_atual
                janela.after(0, atualizar_interface)

        def progresso_final():
            progresso['value'] = 100
        janela.after(0, progresso_final)

    except Exception as e:
        def mostra_erro():
            mostrar_erro_personalizado("Erro", f"Erro ao abrir arquivo:\n{e}")
        janela.after(0, mostra_erro)

def abrir_arquivo_hex_texto_thread():
    threading.Thread(target=abrir_arquivo_hex_texto, daemon=True).start()

def abrir_arquivo_hex_texto():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")])
    if not caminho:
        return

    try:
        tamanho_arquivo = os.path.getsize(caminho)
        if tamanho_arquivo == 0:
            messagebox.showinfo("Info", "Arquivo vazio.")
            return

        def reset_interface():
            hex_texto_entrada.delete("1.0", tk.END)
            texto_decodificado.delete("1.0", tk.END)
            progresso_texto['value'] = 0
        janela.after(0, reset_interface)

        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                messagebox.showinfo("Info", "Arquivo vazio ou sem conteúdo válido.")
                return

            def atualizar_entrada():
                hex_texto_entrada.insert(tk.END, conteudo)
            janela.after(0, atualizar_entrada)

            try:
                decoded_bytes = bytes.fromhex(conteudo)
                decoded_text = decoded_bytes.decode("utf-8")

                def atualizar_resultado():
                    texto_decodificado.delete("1.0", tk.END)
                    texto_decodificado.insert(tk.END, decoded_text)
                    progresso_texto['value'] = 100
                janela.after(0, atualizar_resultado)

            except ValueError:
                def erro_decodificacao():
                    mostrar_erro_personalizado("Erro", "O conteúdo do arquivo não é um hexadecimal válido.")
                janela.after(0, erro_decodificacao)
            except UnicodeDecodeError:
                def erro_unicode():
                    mostrar_erro_personalizado("Erro", "Não foi possível decodificar o hexadecimal para texto UTF-8.")
                janela.after(0, erro_unicode)

    except Exception as e:
        def mostra_erro():
            mostrar_erro_personalizado("Erro", f"Erro ao abrir arquivo:\n{e}")
        janela.after(0, mostra_erro)

# Criação da Janela Principal
janela = tk.Tk()
janela.title("Conversor de Texto e Hexadecimal")
janela.geometry("1200x900")

# Notebook com abas
abas = ttk.Notebook(janela)
abas.pack(fill="both", expand=True)

# Aba 1 - Conversor de Texto
aba1 = tk.Frame(abas)
abas.add(aba1, text="Conversor de Texto")

label = tk.Label(aba1, text="Digite seu texto", font=("Arial", 12))
label.pack(pady=10)

frame_entrada = tk.Frame(aba1)
frame_entrada.pack()

entrada = tk.Text(frame_entrada, width=115, height=16, font=("Arial", 12))
entrada.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_entrada = tk.Scrollbar(frame_entrada, command=entrada.yview)
scroll_entrada.pack(side=tk.RIGHT, fill=tk.Y)

entrada.config(yscrollcommand=scroll_entrada.set)

botao = tk.Button(aba1, text="Converter", bg="#05fc32", fg="black", command=converter_para_hex, font=("Arial", 12))
botao.pack(pady=10)

label_resultado = tk.Label(aba1, text="Texto em Hexadecimal", font=("Arial", 12, "bold"))
label_resultado.pack()

frame_resultado = tk.Frame(aba1)
frame_resultado.pack()

scrollbar = tk.Scrollbar(frame_resultado)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

texto_resultado = tk.Text(frame_resultado, width=130, height=25, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Courier", 10), fg="green")
texto_resultado.pack(side=tk.LEFT)

scrollbar.config(command=texto_resultado.yview)

# Aba 2 - Visualizador de Arquivos em Hexadecimal
aba2 = tk.Frame(abas)
abas.add(aba2, text="Abrir Arquivo em Hex")

frame_botao = tk.Frame(aba2)
frame_botao.pack(pady=10)

botao_abrir = tk.Button(frame_botao, text="Abrir Arquivo (qualquer tipo)", bg="#05fc32", fg="black", command=abrir_arquivo_hex_thread, font=("Arial", 12))
botao_abrir.pack()

progresso = ttk.Progressbar(aba2, orient='horizontal', mode='determinate', length=500)
progresso.pack(pady=10)

frame_hex = tk.Frame(aba2)
frame_hex.pack(fill="both", expand=True, padx=10, pady=10)

scroll_hex = tk.Scrollbar(frame_hex)
scroll_hex.pack(side=tk.RIGHT, fill=tk.Y)

hex_viewer = tk.Text(frame_hex, wrap=tk.NONE, width=140, height=45, font=("Courier", 10), yscrollcommand=scroll_hex.set)
hex_viewer.pack(pady=10)

scroll_hex.config(command=hex_viewer.yview)

# Aba 3 - Decodificador de Hexadecimal de Arquivo de Texto
aba3 = tk.Frame(abas)
abas.add(aba3, text="Decodificar Hex de Texto")

frame_botao_texto = tk.Frame(aba3)
frame_botao_texto.pack(pady=10)

botao_abrir_texto = tk.Button(frame_botao_texto, text="Abrir Arquivo de Texto (.txt)", bg="#05fc32", fg="black", command=abrir_arquivo_hex_texto_thread, font=("Arial", 12))
botao_abrir_texto.pack()

progresso_texto = ttk.Progressbar(aba3, orient='horizontal', mode='determinate', length=500)
progresso_texto.pack(pady=10)

label_hex_entrada = tk.Label(aba3, text="Conteúdo Hexadecimal do Arquivo", font=("Arial", 12))
label_hex_entrada.pack(pady=5)

frame_hex_texto = tk.Frame(aba3)
frame_hex_texto.pack(fill="both", expand=True, padx=10, pady=5)

scroll_hex_texto = tk.Scrollbar(frame_hex_texto)
scroll_hex_texto.pack(side=tk.RIGHT, fill=tk.Y)

hex_texto_entrada = tk.Text(frame_hex_texto, wrap=tk.WORD, width=130, height=10, font=("Courier", 10), yscrollcommand=scroll_hex_texto.set)
hex_texto_entrada.pack(pady=5)

scroll_hex_texto.config(command=hex_texto_entrada.yview)

label_texto_decodificado = tk.Label(aba3, text="Texto Decodificado", font=("Arial", 12, "bold"))
label_texto_decodificado.pack(pady=5)

frame_texto_decodificado = tk.Frame(aba3)
frame_texto_decodificado.pack(fill="both", expand=True, padx=10, pady=5)

scroll_texto_decodificado = tk.Scrollbar(frame_texto_decodificado)
scroll_texto_decodificado.pack(side=tk.RIGHT, fill=tk.Y)

texto_decodificado = tk.Text(frame_texto_decodificado, wrap=tk.WORD, width=130, height=15, font=("Courier", 10), fg="green", yscrollcommand=scroll_texto_decodificado.set)
texto_decodificado.pack(pady=5)

scroll_texto_decodificado.config(command=texto_decodificado.yview)

janela.mainloop()
 
