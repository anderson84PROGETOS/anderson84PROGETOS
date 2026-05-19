import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# =========================
# FUNÇÃO DE LOG CMD
# =========================

def log(msg):
    console.insert(tk.END, msg + "\n")
    console.see(tk.END)

# =========================
# CONFIGURAR SSLKEY
# =========================

def configurar_sslkey():

    pasta_base = filedialog.askdirectory(title="Escolha o disco ou pasta para salvar SSLKEY")

    if not pasta_base:
        return

    def processo():

        try:
            log("\n[+] Iniciando configuração...")

            # Criar pasta
            pasta_ssl = os.path.join(pasta_base, "SSLKEY")

            log(f"\n[+] Criando pasta\n")
            log(pasta_ssl)

            os.makedirs(pasta_ssl, exist_ok=True)

            # Arquivo
            arquivo_log = os.path.join(
                pasta_ssl,
                "sslkeylog.log"
            )

            log(f"\n[+] Criando arquivo\n")
            log(arquivo_log)

            # Criar arquivo
            if not os.path.exists(arquivo_log):

                with open(
                    arquivo_log,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write("")

            log("\n[OK] Arquivo criado.")

            # Configurar variável
            log("\n[+] Configurando variável SSLKEYLOGFILE...")

            comando = f'setx SSLKEYLOGFILE "{arquivo_log}"'

            resultado_cmd = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True
            )

            log(resultado_cmd.stdout)

            if resultado_cmd.stderr:
                log(resultado_cmd.stderr)

            log("[OK] Variável configurada com sucesso!")

            resultado.config(
                text=(
                    "CONFIGURADO COM SUCESSO!\n\n"
                    f"{arquivo_log}"
                ),
                fg="#00ff88"
            )

            messagebox.showinfo(
                "Sucesso",
                "SSLKEYLOGFILE configurado!\n\n"
                "Reinicie o navegador."
            )

        except Exception as erro:

            log("[ERRO]")
            log(str(erro))

            messagebox.showerror(
                "Erro",
                str(erro)
            )

    threading.Thread(
        target=processo,
        daemon=True
    ).start()

# =========================
# JANELA
# =========================

janela = tk.Tk()

janela.title("Variáveis de Ambiente SSLKEYLOGFILE AUTO CONFIG")

janela.geometry("820x820")

janela.configure(bg="#1e1e1e")

# =========================
# TITULO
# =========================

titulo = tk.Label(janela, text="CONFIGURADOR SSLKEYLOGFILE", font=("Arial", 18, "bold"), bg="#1e1e1e", fg="white")

titulo.pack(pady=15)

# =========================
# DESCRIÇÃO
# =========================

descricao = tk.Label(
    janela,
    text=(
        "O programa irá:\n"
        "• Criar pasta SSLKEY automaticamente\n"
        "• Criar sslkeylog.log automaticamente\n"
        "• Configurar variável SSLKEYLOGFILE sozinho\n\n"
        "Você só escolhe o disco ou pasta."
    ),
    font=("Arial", 11),
    bg="#1e1e1e",
    fg="#cccccc",
    justify="center"
)

descricao.pack(pady=10)

# =========================
# BOTÃO
# =========================

botao = tk.Button(
    janela,
    text="ESCOLHER LOCAL",
    font=("Arial", 13, "bold"),
    width=22,
    height=2,
    bg="#0078D7",
    fg="white",
    activebackground="#005A9E",
    activeforeground="white",
    command=configurar_sslkey
)

botao.pack(pady=15)

# =========================
# RESULTADO
# =========================

resultado = tk.Label(
    janela,
    text="",
    font=("Arial", 10),
    bg="#1e1e1e",
    fg="white",
    wraplength=700,
    justify="center"
)

resultado.pack(pady=10)

# =========================
# CONSOLE ESTILO CMD
# =========================

frame_console = tk.Frame(
    janela,
    bg="#1e1e1e"
)

frame_console.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

label_console = tk.Label(
    frame_console,
    text="Console CMD",
    font=("Consolas", 11, "bold"),
    bg="#1e1e1e",
    fg="#00ff88"
)

label_console.pack(anchor="w")

console = scrolledtext.ScrolledText(
    frame_console,
    bg="black",
    fg="#00ff88",
    font=("Consolas", 10),
    insertbackground="white",
    height=15
)

console.pack(
    fill="both",
    expand=True
)

janela.mainloop()
