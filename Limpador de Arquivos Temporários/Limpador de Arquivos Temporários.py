import os
import shutil
import tkinter as tk
from tkinter import messagebox
import subprocess

# Funções para abrir pastas
def abrir_temp():
    temp_path = os.environ.get("TEMP")
    if temp_path:
        subprocess.Popen(f'explorer "{temp_path}"')

def abrir_prefetch():
    path = r"C:\Windows\Prefetch"
    if os.path.exists(path):
        subprocess.Popen(f'explorer "{path}"')

def abrir_windows_temp():
    path = r"C:\Windows\Temp"
    if os.path.exists(path):
        subprocess.Popen(f'explorer "{path}"')

# Função genérica para limpar pastas individualmente
def limpar_pasta_sem_confirmacao(pasta_nome, pasta_caminho):
    erros = []

    if os.path.exists(pasta_caminho):
        for arquivo in os.listdir(pasta_caminho):
            caminho = os.path.join(pasta_caminho, arquivo)
            try:
                if os.path.isfile(caminho) or os.path.islink(caminho):
                    os.remove(caminho)
                elif os.path.isdir(caminho):
                    shutil.rmtree(caminho)
            except Exception as e:
                erros.append(f"Erro ao excluir: {caminho} - {str(e)}\n")

    return erros

# Limpar todas as pastas com confirmação única
def limpar_arquivos():
    confirm = messagebox.askyesno("Confirmação", "Deseja realmente limpar TODAS as pastas temporárias?")
    if not confirm:
        return

    erros_total = []

    erros_total += limpar_pasta_sem_confirmacao("%TEMP%", os.environ.get("TEMP"))
    erros_total += limpar_pasta_sem_confirmacao("Windows Temp", r"C:\Windows\Temp")
    erros_total += limpar_pasta_sem_confirmacao("Prefetch", r"C:\Windows\Prefetch")

    if erros_total:
        messagebox.showwarning("Aviso", f"Limpeza concluída com erros:\n\n" + "\n".join(erros_total[:5]))
    else:
        messagebox.showinfo("Sucesso", "Todas as pastas foram limpas com sucesso!")

# Função de limpeza com confirmação individual (usada nos botões individuais)
def limpar_pasta(pasta_nome, pasta_caminho):
    confirm = messagebox.askyesno("Confirmação", f"Deseja limpar a pasta {pasta_nome}?")
    if not confirm:
        return

    erros = limpar_pasta_sem_confirmacao(pasta_nome, pasta_caminho)

    if erros:
        messagebox.showwarning("Aviso", f"Limpeza da pasta {pasta_nome} concluída com erros:\n\n" + "\n".join(erros[:5]))
    else:
        messagebox.showinfo("Sucesso", f"Pasta {pasta_nome} limpa com sucesso!")

# Janela principal
janela = tk.Tk()
janela.title("🧹 Limpador de Arquivos Temporários")
janela.geometry("650x400")
janela.configure(bg="black")

# Estilo dos botões
botao_grande = {"font": ("Arial", 11), "bg": "#222", "fg": "lime", "width": 45, "height": 2}
botao_pequeno = {"font": ("Arial", 11), "bg": "#900", "fg": "white", "width": 5, "height": 2}
botao_lixeira = {"font": ("Arial", 14), "bg": "#900", "fg": "white", "width": 42, "height": 2}

# Título
tk.Label(janela, text="🧹 Limpador de Arquivos Temporários", fg="white", bg="black", font=("Arial", 14, "bold")).pack(pady=15)

# Criar uma linha com botão abrir + excluir
def criar_linha(nome_pasta, comando_abrir, comando_excluir):
    frame = tk.Frame(janela, bg="black")
    frame.pack(pady=5)
    tk.Button(frame, text=f"🗂 Abrir Pasta {nome_pasta}", command=comando_abrir, **botao_grande).pack(side="left", padx=5)
    tk.Button(frame, text="🗑", command=comando_excluir, **botao_pequeno).pack(side="left")

# Linhas
criar_linha("%TEMP%", abrir_temp, lambda: limpar_pasta("%TEMP%", os.environ.get("TEMP")))
criar_linha(r"C:\Windows\Temp", abrir_windows_temp, lambda: limpar_pasta("Windows Temp", r"C:\Windows\Temp"))
criar_linha(r"C:\Windows\Prefetch", abrir_prefetch, lambda: limpar_pasta("Prefetch", r"C:\Windows\Prefetch"))

# Botão para limpar tudo (vermelho)
tk.Button(
    janela,
    text="🗑  Limpar TODAS Pastas  %temp%   temp   prefetch ",
    command=limpar_arquivos,
    **botao_lixeira
).pack(pady=20)

# Iniciar interface
janela.mainloop()
