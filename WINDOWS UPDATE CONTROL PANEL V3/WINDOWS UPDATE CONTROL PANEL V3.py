import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import subprocess
import threading
import time
import os
import shutil

# =========================
# FUNÇÕES SISTEMA
# =========================

def executar_comando(comando):
    try:
        resultado = subprocess.check_output(comando, shell=True)
        return resultado.decode('latin-1', errors='ignore')
    except:
        return "Erro ao executar comando."


def verificar_servico(nome):
    resultado = executar_comando(f'sc query {nome}')
    if "RUNNING" in resultado:
        return "ATIVO"
    elif "STOPPED" in resultado:
        return "DESATIVADO"
    return "DESCONHECIDO"


# =========================
# TERMINAL
# =========================

def escrever_terminal(texto):
    output.delete(1.0, tk.END)
    for linha in texto.split("\n"):
        output.insert(tk.END, linha + "\n")
        output.update()
        janela.after(5)


# =========================
# FUNÇÕES PRINCIPAIS
# =========================

def verificar_status():
    status_bar.set("Verificando serviços...")

    wua = verificar_servico("wuauserv")
    bits = verificar_servico("BITS")
    uso = verificar_servico("UsoSvc")

    texto = f"""
=== STATUS DO SISTEMA ===

Windows Update : {wua}
BITS           : {bits}
Orchestrator   : {uso}
"""

    if wua == "ATIVO":
        status_label.config(text="● WINDOWS UPDATE ATIVO", fg="#00ff00")
    else:
        status_label.config(text="● WINDOWS UPDATE DESATIVADO", fg="red")

    escrever_terminal(texto)
    status_bar.set("Status atualizado ✔")


def iniciar_update():
    status_bar.set("Ativando Windows Update...")
    executar_comando('net start wuauserv')
    verificar_status()


def parar_update():
    status_bar.set("Desativando Windows Update...")
    executar_comando('net stop wuauserv')
    verificar_status()


def ver_historico():
    status_bar.set("Carregando histórico...")
    comando = 'powershell "Get-HotFix | Sort-Object InstalledOn -Descending"'
    resultado = executar_comando(comando)
    escrever_terminal(resultado)
    status_bar.set("Histórico carregado ✔")


# =========================
# 💾 SALVAR LOG TERMINAL
# =========================

def salvar_log():
    conteudo = output.get(1.0, tk.END)

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar log como"
    )

    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

        status_bar.set(f"Log salvo em: {caminho}")


# =========================
# 💾 SALVAR WindowsUpdate.log REAL
# =========================

def salvar_windows_update_log():
    status_bar.set("Gerando WindowsUpdate.log...")

    caminho = filedialog.asksaveasfilename(
        initialfile="WindowsUpdate.log",  # 👈 nome fixo
        defaultextension=".log",
        filetypes=[("Arquivo LOG", "*.log")],
        title="Salvar WindowsUpdate.log"
    )

    if caminho:
        comando = f'powershell "Get-WindowsUpdateLog -LogPath \\"{caminho}\\""'
        executar_comando(comando)
        status_bar.set("WindowsUpdate.log salvo ✔")


# =========================
# 🧹 LIMPAR LOGS AUTOMÁTICO
# =========================

def limpar_logs():
    status_bar.set("Limpando logs...")

    try:
        temp_path = os.environ.get('TEMP')

        pasta_update_log = os.path.join(temp_path, "WindowsUpdateLog")

        if os.path.exists(pasta_update_log):
            shutil.rmtree(pasta_update_log, ignore_errors=True)

        escrever_terminal("Logs do Windows Update removidos com sucesso.")
        status_bar.set("Limpeza concluída ✔")

    except Exception as e:
        escrever_terminal(str(e))
        status_bar.set("Erro ao limpar logs")


# =========================
# BARRA DE PROGRESSO
# =========================

def animar_barra():
    progress['value'] = 0
    for i in range(101):
        progress['value'] = i
        janela.update_idletasks()
        time.sleep(0.01)


def executar_thread(func):
    def run():
        animar_barra()
        func()
    threading.Thread(target=run).start()


# =========================
# HOVER
# =========================

def on_enter(e):
    e.widget['bg'] = "#00ff00"
    e.widget['fg'] = "black"


def on_leave(e, cor_bg, cor_fg):
    e.widget['bg'] = cor_bg
    e.widget['fg'] = cor_fg


# =========================
# INTERFACE
# =========================

janela = tk.Tk()
janela.title("WINDOWS UPDATE CONTROL PANEL V3")
janela.geometry("1000x800")
janela.configure(bg="black")

titulo = tk.Label(janela, text="WINDOWS UPDATE CONTROL PANEL V3",
                  fg="#00ff00", bg="black",
                  font=("Consolas", 20, "bold"))
titulo.pack(pady=10)

status_label = tk.Label(janela, text="● CARREGANDO...",
                        fg="#00ff00", bg="black",
                        font=("Consolas", 16))
status_label.pack(pady=5)

style = ttk.Style()
style.theme_use('default')
style.configure("green.Horizontal.TProgressbar",
                background='#00ff00',
                troughcolor='black')

progress = ttk.Progressbar(janela,
                           style="green.Horizontal.TProgressbar",
                           orient="horizontal",
                           length=600,
                           mode="determinate")
progress.pack(pady=10)

frame_botoes = tk.Frame(janela, bg="black")
frame_botoes.pack(pady=10)


def criar_botao(texto, comando, cor_bg, cor_fg, row, col):
    btn = tk.Button(frame_botoes, text=texto,
                    command=lambda: executar_thread(comando),
                    bg=cor_bg, fg=cor_fg,
                    font=("Consolas", 11), width=22)
    btn.grid(row=row, column=col, padx=10, pady=5)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", lambda e: on_leave(e, cor_bg, cor_fg))


# Linha 1
criar_botao("VERIFICAR STATUS", verificar_status, "#003300", "#00ff00", 0, 0)
criar_botao("ATIVAR UPDATE", iniciar_update, "#001a33", "#00ccff", 0, 1)
criar_botao("DESATIVAR UPDATE", parar_update, "#330000", "red", 0, 2)
criar_botao("VER HISTÓRICO", ver_historico, "#332200", "#ffcc00", 0, 3)

# Linha 2 (novos)
criar_botao("💾 SALVAR LOG TELA", salvar_log, "#222222", "#ffffff", 1, 0)
criar_botao("💾 SALVAR WindowsUpdate.log", salvar_windows_update_log, "#004d4d", "#00ffff", 1, 1)
criar_botao("🧹 LIMPAR LOGS", limpar_logs, "#333300", "#ffff00", 1, 2)

output = scrolledtext.ScrolledText(janela,
                                   bg="black",
                                   fg="#00ff00",
                                   font=("Consolas", 10),
                                   insertbackground="green")
output.pack(fill="both", expand=True, padx=10, pady=10)

status_bar = tk.StringVar()
status_bar.set("Sistema pronto")

status = tk.Label(janela, textvariable=status_bar,
                  bd=1, relief="sunken",
                  anchor="w",
                  bg="black", fg="#00ff00",
                  font=("Consolas", 10))
status.pack(side="bottom", fill="x")

verificar_status()

janela.mainloop()
