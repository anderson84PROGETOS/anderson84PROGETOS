import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import subprocess
from datetime import datetime


# =========================================================
# VARIÁVEIS GLOBAIS
# =========================================================

scan_ativo = False


# =========================================================
# FUNÇÕES
# =========================================================

def escolher_arquivo_saida():

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo TXT", "*.txt")],
        title="Salvar resultado"
    )

    if caminho:
        arquivo_saida_var.set(caminho)


def log(msg):

    resultado_text.config(state="normal")
    resultado_text.insert(tk.END, msg + "\n")
    resultado_text.see(tk.END)
    resultado_text.config(state="disabled")


def limpar_tela():

    resultado_text.config(state="normal")
    resultado_text.delete(1.0, tk.END)
    resultado_text.config(state="disabled")


# =========================================================
# ATUALIZAR COMANDO
# =========================================================

def atualizar_comando(event=None):

    alvo = alvo_var.get().strip()

    verbose = combo_verbose.get()

    scan_tipo = combo_scan.get()

    scans_preview = {

        "Scan rápido":
            f"nmap {verbose} -D RND:20 -sS -F {alvo}",

        "Top 100 portas":
            f"nmap {verbose} -D RND:20 --open -sS --top-ports 100 {alvo}",

        "Top 1000 portas":
            f"nmap {verbose} -D RND:20 --open -sS --top-ports 1000 {alvo}",

        "Detecção de serviços":
            f"nmap {verbose} -D RND:20 -sV {alvo}",

        "Detecção de sistema operacional":
            f"nmap {verbose} -D RND:20 -O {alvo}",

        "Scripts NSE padrão":
            f"nmap {verbose} -D RND:20 -sC {alvo}",

        "Scan de vulnerabilidades":
            f"nmap {verbose} -D RND:20 --script vuln {alvo}",

        "Scan de vulnerabilidades e serviços":
            f"nmap {verbose} -sV -D RND:20 --script vuln {alvo}", 

        "Scan de vulnerabilidades e serviços + sistema operacional":
            f"nmap {verbose} -sV -O -D RND:20 --script vuln {alvo}",       

        "Scan agressivo":
            f"nmap {verbose} -D RND:20 -A {alvo}",

        "Scan completo TCP":
            f"nmap {verbose} -D RND:20 -p- -sS {alvo}",

        "Scan UDP":
            f"nmap {verbose} -D RND:20 -sU {alvo}",

        "Detecção de firewall":
            f"nmap {verbose} -D RND:20 -sA {alvo}",

        "Scan stealth FIN":
            f"nmap {verbose} -D RND:20 -sF {alvo}",

        "Scan Xmas":
            f"nmap {verbose} -D RND:20 -sX {alvo}",

        "Scan NULL":
            f"nmap {verbose} -D RND:20 -sN {alvo}",

        "Enumeração SMB":
            f"nmap {verbose} --script smb-enum-shares,smb-enum-users {alvo}",

        "Brute FTP":
            f"nmap {verbose} --script ftp-brute {alvo}",

        "Brute SSH":
            f"nmap {verbose} --script ssh-brute {alvo}",

        "Detectar HTTP":
            f"nmap {verbose} -sV --script http-title,http-headers {alvo}",

        "SSL/TLS":
            f"nmap {verbose} --script ssl-enum-ciphers -p 443 {alvo}",

        "Whois":
            f"nmap {verbose} --script whois-domain.nse {alvo}",

        "dns-brute":
            f"nmap {verbose} --script dns-brute {alvo}",                                

        "Traceroute":
            f"nmap {verbose} --traceroute {alvo}",
    }

    comando = scans_preview.get(scan_tipo, "")

    entry_comando.delete(1.0, tk.END)

    entry_comando.insert(tk.END, comando)


# =========================================================
# EXECUTAR SCAN
# =========================================================

def executar_scan():

    global scan_ativo

    if scan_ativo:

        messagebox.showwarning(
            "Aviso",
            "Já existe um scan em execução."
        )

        return

    alvo = alvo_var.get().strip()

    salvar = salvar_var.get()

    arquivo_saida = arquivo_saida_var.get().strip()

    # =====================================================
    # PEGA O COMANDO MANUAL
    # =====================================================

    comando = entry_comando.get(1.0, tk.END).strip()

    if not alvo:

        messagebox.showerror(
            "Erro",
            "Digite um IP ou domínio."
        )

        return

    if not comando:

        messagebox.showerror(
            "Erro",
            "Digite um comando Nmap."
        )

        return

    if salvar and not arquivo_saida:

        messagebox.showerror(
            "Erro",
            "Escolha onde salvar o TXT."
        )

        return

    limpar_tela()

    progress_var.set(0)

    scan_ativo = True

    def run():

        global scan_ativo

        try:

            log("=" * 70)
            log("SCANNER NMAP GRÁFICO")
            log("=" * 70)
            log(f"Alvo: {alvo}")
            log("")
            log("COMANDO EXECUTADO\n")
            log(comando)
            log("=" * 70)
            log("")

            processo = subprocess.Popen(
                comando,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            saida_completa = ""

            progresso = 0

            for linha in processo.stdout:

                saida_completa += linha

                log(linha.rstrip())

                # =================================================
                # PROGRESSO
                # =================================================

                if progresso < 95:

                    progresso += 1

                    progress_var.set(progresso)

            processo.wait()

            progress_var.set(100)

            # =================================================
            # SALVAR RESULTADO
            # =================================================

            if salvar:

                with open(
                    arquivo_saida,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write("=" * 70 + "\n")
                    f.write("RESULTADO NMAP\n")
                    f.write("=" * 70 + "\n")
                    f.write(f"Data: {datetime.now()}\n\n")
                    f.write(f"Alvo: {alvo}\n\n")
                    f.write(f"Comando: {comando}\n\n")
                    f.write(saida_completa)

                log("")
                log(f"[+] Resultado salvo em: {arquivo_saida}")

            log("")
            log("[+] Scan finalizado com sucesso")

            messagebox.showinfo(
                "Concluído",
                "Scan finalizado."
            )

        except Exception as e:

            messagebox.showerror(
                "Erro",
                str(e)
            )

        finally:

            scan_ativo = False

    threading.Thread(
        target=run,
        daemon=True
    ).start()


# =========================================================
# JANELA
# =========================================================

root = tk.Tk()
root.title("Scanner Nmap Gráfico")
root.geometry("1150x850")
root.state("zoomed")
root.configure(bg="#0d1117")

# =========================================================
# ESTILO
# =========================================================

style = ttk.Style()

style.theme_use("clam")

style.configure(
    "TLabel",
    background="#0d1117",
    foreground="#00ff88",
    font=("Consolas", 11)
)

style.configure(
    "TButton",
    font=("Consolas", 10, "bold"),
    padding=6
)

style.configure(
    "TCheckbutton",
    background="#0d1117",
    foreground="#00ff88",
    font=("Consolas", 10)
)

style.configure(
    "green.Horizontal.TProgressbar",
    troughcolor="#161b22",
    background="#00ff88",
    bordercolor="#161b22",
    lightcolor="#00ff88",
    darkcolor="#00cc66"
)


# =========================================================
# VARIÁVEIS
# =========================================================

alvo_var = tk.StringVar()

arquivo_saida_var = tk.StringVar()

salvar_var = tk.BooleanVar(value=True)


# =========================================================
# TÍTULO
# =========================================================

titulo = tk.Label(root, text="SCANNER NMAP GRÁFICO", bg="#0d1117", fg="#00ff88",  font=("Consolas", 24, "bold"))
titulo.pack(pady=15)

# =========================================================
# FRAME PRINCIPAL
# =========================================================

frame = tk.Frame(root, bg="#161b22", bd=2, relief="groove")

frame.pack(fill="x", padx=15, pady=10)

# =========================================================
# ALVO
# =========================================================

ttk.Label(frame, text="IP ou Domínio:").grid(row=0, column=0, padx=10, pady=10, sticky="w")

entry_alvo = ttk.Entry(frame, textvariable=alvo_var, width=80)

entry_alvo.grid(row=0, column=1, padx=10, pady=10)

# =========================================================
# TIPO SCAN
# =========================================================

ttk.Label(frame, text="Tipo de Scan:").grid(row=1, column=0, padx=10, pady=10, sticky="w")

combo_scan = ttk.Combobox(
    frame,
    width=77,
    state="readonly",
    values=[

        "Scan rápido",
        "Top 100 portas",
        "Top 1000 portas",
        "Detecção de serviços",
        "Detecção de sistema operacional",
        "Scripts NSE padrão",
        "Scan de vulnerabilidades",
        "Scan de vulnerabilidades e serviços",
        "Scan de vulnerabilidades e serviços + sistema operacional",            
        "Scan agressivo",
        "Scan completo TCP",
        "Scan UDP",
        "Detecção de firewall",
        "Scan stealth FIN",
        "Scan Xmas",
        "Scan NULL",
        "Enumeração SMB",
        "Brute FTP",
        "Brute SSH",
        "Detectar HTTP",
        "SSL/TLS",
        "Whois",
        "dns-brute",
        "Traceroute"
    ]
)

combo_scan.current(0)

combo_scan.grid(row=1, column=1, padx=10, pady=10)

# =========================================================
# VERBOSE
# =========================================================

ttk.Label(frame, text="Verbose:").grid(row=2, column=0, padx=10, pady=10, sticky="w")

combo_verbose = ttk.Combobox(frame, width=20, state="readonly", values=["", "-v", "-vv", "-vvv"])

combo_verbose.current(0)

combo_verbose.grid(row=2, column=1, padx=10, pady=10, sticky="w")

# =========================================================
# COMANDO MANUAL EDITÁVEL
# =========================================================

ttk.Label(frame, text="Comando Nmap:").grid(row=3, column=0, padx=10, pady=10, sticky="nw")

entry_comando = tk.Text(frame, height=6, width=80, bg="#010409", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10))

entry_comando.grid(row=3, column=1, padx=10, pady=10)

# =========================================================
# SALVAR TXT
# =========================================================

check_salvar = ttk.Checkbutton(frame, text="Salvar resultado em TXT", variable=salvar_var)

check_salvar.grid(row=4, column=1, padx=10, pady=5, sticky="w")


# =========================================================
# ARQUIVO SAÍDA
# =========================================================

ttk.Label(frame, text="Arquivo TXT:").grid(row=5, column=0, padx=10, pady=10, sticky="w")

entry_saida = ttk.Entry(frame, textvariable=arquivo_saida_var, width=80)

entry_saida.grid(row=5, column=1, padx=10, pady=10)

btn_saida = ttk.Button(frame, text="Escolher", command=escolher_arquivo_saida)

btn_saida.grid( row=5, column=2, padx=10)

# =========================================================
# BOTÕES
# =========================================================

frame_botoes = tk.Frame(root, bg="#0d1117")
frame_botoes.pack(pady=10)

btn_scan = ttk.Button(frame_botoes, text="INICIAR SCAN", command=executar_scan)

btn_scan.grid(row=0, column=0, padx=10)

btn_limpar = ttk.Button(frame_botoes, text="LIMPAR LOG", command=limpar_tela)

btn_limpar.grid(row=0, column=1, padx=10)


# =========================================================
# BARRA DE PROGRESSO
# =========================================================

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate", variable=progress_var, maximum=100, style="green.Horizontal.TProgressbar")
progress.pack(pady=10)

# =========================================================
# LOG
# =========================================================

resultado_text = ScrolledText(root, bg="#010409", fg="#00ff88", insertbackground="#00ff88", font=("Consolas", 10), height=30)

resultado_text.pack(fill="both", expand=True, padx=15, pady=15)

resultado_text.config(state="disabled")

# =========================================================
# EVENTOS
# =========================================================

combo_scan.bind("<<ComboboxSelected>>", atualizar_comando)

combo_verbose.bind("<<ComboboxSelected>>", atualizar_comando)

entry_alvo.bind("<KeyRelease>", atualizar_comando)

# =========================================================
# INICIAR PREVIEW
# =========================================================

atualizar_comando()

# =========================================================
# LOOP
# =========================================================

root.mainloop()
