import tkinter as tk
from tkinter import messagebox
import os
import shutil
import subprocess

# ==================================
# FUNÇÕES GERAIS
# ==================================

def abrir_pasta(caminho):
    try:
        os.startfile(caminho)
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def limpar_pasta(caminho):
    if not os.path.exists(caminho):
        messagebox.showwarning("Aviso", f"Pasta não encontrada:\n{caminho}")
        return

    apagados = 0
    erros = 0

    for item in os.listdir(caminho):
        arquivo = os.path.join(caminho, item)

        try:
            if os.path.isfile(arquivo) or os.path.islink(arquivo):
                os.remove(arquivo)
                apagados += 1

            elif os.path.isdir(arquivo):
                shutil.rmtree(arquivo, ignore_errors=True)
                apagados += 1

        except:
            erros += 1

    messagebox.showinfo(
        "Limpeza concluída",
        f"Arquivos removidos: {apagados}\nErros: {erros}"
    )

# ==================================
# SHELL WINDOWS
# ==================================

def abrir_apps():
    try:
        os.startfile("shell:appsfolder")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def abrir_recentes():
    try:
        os.startfile("shell:recent")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def abrir_startup():
    try:
        os.startfile("shell:startup")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# ==================================
# PASTAS
# ==================================

TEMP_USER = os.environ["TEMP"]
WINDOWS_TEMP = r"C:\Windows\Temp"
PREFETCH = r"C:\Windows\Prefetch"
CRASHDUMPS = os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps")

# ==================================
# LIMPEZA DE DISCO
# ==================================

def limpeza_disco():
    try:
        subprocess.Popen("cleanmgr")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# ==================================
# JANELA
# ==================================

janela = tk.Tk()
janela.title("⚙️ Central de Limpeza e Ferramentas Windows")
janela.geometry("800x920")
janela.state("zoomed")
janela.configure(bg="#1e1e1e")

# ==================================
# TÍTULO
# ==================================

tk.Label(
    janela,
    text="⚙️ Central de Limpeza e Ferramentas Windows",
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(pady=2)


tk.Label(janela, text="Algumas limpezas podem exigir execução como Administrador", bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 10)).pack(pady=2)

# ==================================
# SHELL
# ==================================

tk.Button(
    janela,
    text="📦 Aplicações Instaladas",
    bg="#3498db",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=abrir_apps
).pack(pady=5)

tk.Button(
    janela,
    text="📂 Arquivos Recentes",
    bg="#2ecc71",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=abrir_recentes
).pack(pady=5)

tk.Button(
    janela,
    text="🚀 Programas de Inicialização",
    bg="#f39c12",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=abrir_startup
).pack(pady=5)

# ==================================
# TEMP USUÁRIO
# ==================================

tk.Label(
    janela,
    text="TEMP DO USUÁRIO",
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 12, "bold"),
).pack(pady=(15, 5))

tk.Button(
    janela,
    text="🧊 Abrir TEMP",
    bg="#9b59b6",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: abrir_pasta(TEMP_USER)
).pack()

tk.Button(
    janela,
    text="🧹 Limpar TEMP",
    bg="#e74c3c",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: limpar_pasta(TEMP_USER)
).pack(pady=5)

# ==================================
# WINDOWS TEMP
# ==================================

tk.Label(
    janela,
    text="WINDOWS TEMP",
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 12, "bold"),
    
).pack(pady=(15, 5))

tk.Button(
    janela,
    text="📁 Abrir Windows Temp",
    bg="#16a085",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: abrir_pasta(WINDOWS_TEMP)
).pack()

tk.Button(
    janela,
    text="🗑️ Limpar Windows Temp",
    bg="#c0392b",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: limpar_pasta(WINDOWS_TEMP)
).pack(pady=5)

# ==================================
# PREFETCH
# ==================================

tk.Label(
    janela,
    text="PREFETCH",
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 12, "bold"),
).pack(pady=(15, 5))

tk.Button(
    janela,
    text="⚡ Abrir Prefetch",
    bg="#2980b9",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: abrir_pasta(PREFETCH)
).pack()

tk.Button(
    janela,
    text="🧹 Limpar Prefetch",
    bg="#8e44ad",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: limpar_pasta(PREFETCH)
).pack(pady=5)

# ==================================
# CRASHDUMPS
# ==================================

tk.Label(
    janela,
    text="CRASHDUMPS",
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 10, "bold"),
).pack(pady=(15, 5))

tk.Button(
    janela,
    text="💥 Abrir CrashDumps",
    bg="#34495e",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: abrir_pasta(CRASHDUMPS)
).pack()

tk.Button(
    janela,
    text="🗑️ Limpar CrashDumps",
    bg="#d35400",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=30,
    height=2,
    command=lambda: limpar_pasta(CRASHDUMPS)
).pack(pady=5)

# ==================================
# LIMPEZA DE DISCO
# ==================================

tk.Button(
    janela,
    text="💽 Abrir Limpeza de Disco do Windows",
    bg="#27ae60",
    fg="black",
    font=("Segoe UI", 10, "bold"),
    width=31,
    height=2,
    command=limpeza_disco
).pack(pady=20)

# ==================================
# RODAPÉ
# ==================================

janela.mainloop()
