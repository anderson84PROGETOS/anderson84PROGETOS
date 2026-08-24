import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import socket
import datetime

# ====================== VARIÁVEL GLOBAL ======================
total_palavras = 0

# ====================== FUNÇÃO PRINCIPAL ======================
def buscar_dns():
    global total_palavras
    dominio = entry_dominio.get().strip()
    arquivo = entry_arquivo.get().strip()
    if not dominio or not arquivo:
        messagebox.showwarning("Atenção", "Preencha o domínio e o arquivo wordlist!")
        return
   
    # Limpa resultados anteriores
    tree.delete(*tree.get_children())
    progress_bar["value"] = 0
   
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo não encontrado!")
        return
   
    # ==================== CONTAGEM DA WORDLIST ====================
    total_palavras = sum(1 for linha in linhas if linha.strip() and not linha.endswith("."))
    if total_palavras == 0:
        messagebox.showwarning("Atenção", "Nenhum subdomínio válido encontrado na wordlist!")
        return

    # ==================== LEITURA ESPECIAL DA WORDLIST ====================
    subdominios = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        if linha.endswith("."):
            linha = linha[:-1]
        subdominios.append(linha)
        if not linha.endswith("."):
            subdominios.append(linha + ".")

    btn_verificar.config(state="disabled", text="🔍 Verificando...")

    def processar():
        encontrados = 0
        total = len(subdominios)
        for i, subdomain in enumerate(subdominios):
            host_completo = subdomain + "." + dominio
            try:
                ip = socket.gethostbyname(host_completo)
                encontrados += 1
                janela.after(0, adicionar_resultado, host_completo, ip, encontrados)
            except socket.gaierror:
                pass
            except Exception:
                pass
           
            # Atualiza barra de progresso
            progresso = int(((i + 1) / total) * 100)
            janela.after(0, lambda p=progresso: progress_bar.config(value=p))
       
        janela.after(0, finalizar_busca, encontrados, dominio)
   
    threading.Thread(target=processar, daemon=True).start()

# ====================== ADICIONAR RESULTADO ======================
def adicionar_resultado(host, ip, contador):
    tree.insert("", "end", values=(host, ip))
    label_contagem.config(text=f" {contador} subdomínios Encontrados | Palavras na wordlist: {total_palavras}")

# ====================== FINALIZAR BUSCA ======================
def finalizar_busca(total, dominio):
    btn_verificar.config(state="normal", text="🔍 Verificar DNS")
    label_contagem.config(text=f"✅ Busca finalizada   {total} subdomínios Encontrados | Palavras na wordlist: {total_palavras}")
    progress_bar.config(value=100)
    messagebox.showinfo("Busca finalizada", 
                        f"Processamento concluído!\n\n"
                        f"Domínio alvo: {dominio}\n"
                        f"Subdomínios Encontrados: {total}\n"
                        f"Palavras na wordlist: {total_palavras}")

# ====================== EXPORTAR TXT ======================
def exportar_txt():
    dominio = entry_dominio.get().strip()
    if not tree.get_children():
        messagebox.showwarning("Atenção", "Não existem resultados para exportar!")
        return
    arquivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")])
    if not arquivo:
        return
    try:
        encontrados = len(tree.get_children())
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("Resultado DNS Scanner - Wordlist\n")
            f.write("=" * 80 + "\n")
            f.write(f"Domínio Alvo: {dominio}\n")
            f.write(f"Subdomínios Encontrados: {encontrados}\n")
            f.write("Data: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M") + "\n")
            f.write("-" * 80 + "\n\n")
            for item in tree.get_children():
                valores = tree.item(item, "values")
                host = valores[0]
                ip = valores[1]
                f.write(f"{host:<60} IP: {ip}\n")
        messagebox.showinfo("Exportado", f"Arquivo salvo em:\n{arquivo}")
    except Exception as erro:
        messagebox.showerror("Erro", f"Não foi possível exportar:\n{erro}")

# ====================== PROCURAR ARQUIVO ======================
def procurar_arquivo():
    arquivo = filedialog.askopenfilename(filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")])
    if arquivo:
        entry_arquivo.delete(0, tk.END)
        entry_arquivo.insert(0, arquivo)

        global total_palavras
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            total_palavras = sum(1 for linha in linhas if linha.strip() and not linha.endswith("."))
            label_contagem.config(text=f"Total de subdomínios Encontrados: 0  |  Palavras na wordlist: {total_palavras}")
        except Exception:
            total_palavras = 0
            label_contagem.config(text="Total de subdomínios Encontrados: 0  |  Palavras na wordlist: 0")

# ====================== INTERFACE ======================
janela = tk.Tk()
janela.title("DNS Scanner")
janela.geometry("1000x800")
janela.minsize(800, 600)

tk.Label(janela, text="Domínio Alvo (ex: exemplo.com):", font=("Arial", 12)).pack(pady=10)
entry_dominio = tk.Entry(janela, width=60, font=("Arial", 12))
entry_dominio.pack(pady=5)

tk.Label(janela, text="Arquivo Wordlist (.txt):", font=("Arial", 12)).pack(pady=10)
entry_arquivo = tk.Entry(janela, width=60, font=("Arial", 12))
entry_arquivo.pack(pady=5)

tk.Button(janela, text="Procurar arquivo...", command=procurar_arquivo).pack(pady=5)

btn_frame = tk.Frame(janela)
btn_frame.pack(pady=20)
btn_verificar = tk.Button(btn_frame, text="🔍 Verificar DNS", font=("Arial", 14, "bold"), bg="#0078d4", fg="white", width=20, height=2, command=buscar_dns)
btn_verificar.pack(side="left", padx=10)
btn_export = tk.Button(btn_frame, text="💾 Exportar .txt", font=("Arial", 14, "bold"), bg="#28a745", fg="white", width=20, height=2, command=exportar_txt)
btn_export.pack(side="left", padx=10)

label_contagem = tk.Label(janela, text="Total de subdomínios Encontrados: 0  |  Palavras na wordlist: 0", 
                          font=("Arial", 14, "bold"), fg="#0078d4")
label_contagem.pack(pady=5)

# ==================== BARRA DE PROGRESSO ====================
progress_frame = tk.Frame(janela)
progress_frame.pack(pady=10, fill="x", padx=20)
progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=900, maximum=100)
progress_bar.pack(fill="x")

# ==================== TABELA DE RESULTADOS ====================
frame_tabela = tk.Frame(janela)
frame_tabela.pack(fill="both", expand=True, padx=20, pady=30)

tree = ttk.Treeview(frame_tabela, columns=("Host", "IP"), show="headings", height=5)
tree.heading("Host", text="Host/Domínio")
tree.heading("IP", text="IP")
tree.column("Host", width=500)
tree.column("IP", width=300)

scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

janela.mainloop()
