import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
import threading

# Cabeçalhos para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

subdominios = []  # lista global para armazenar os subdomínios
ativos = []       # resultados encontrados
scan_thread = None
parar_scan = False


def carregar_wordlist():
    global subdominios
    caminho = filedialog.askopenfilename(
        title="Selecione a wordlist",
        filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )
    
    if not caminho:
        return
    
    try:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            subdominios = [linha.strip() for linha in f if linha.strip()]        
        
        lbl_wordlist_info.config(text=f"Wordlist carregada: {len(subdominios)} linhas")
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar wordlist:\n{e}")


def escanear():
    global subdominios, parar_scan, ativos
    dominio = entrada_url.get().strip()
    if not dominio:
        messagebox.showwarning("Aviso", "Digite um domínio primeiro (ex: meusite.com)")
        return
    
    if not subdominios:
        messagebox.showwarning("Aviso", "Carregue uma wordlist primeiro!")
        return

    total = len(subdominios)
    ativos = []
    text_box.delete("1.0", tk.END)

    # Configura barra de progresso
    progress["value"] = 0
    progress["maximum"] = total
    janela.update_idletasks()

    for i, entrada in enumerate(subdominios, start=1):
        if parar_scan:
            break

        entrada = entrada.strip()
        if not entrada:
            continue

        # Mostra em tempo real a entrada que está sendo testada
        lbl_atual.config(text=f"Testando: {entrada}")
        janela.update_idletasks()

        # Se a linha começa com "/" => é diretório
        if entrada.startswith("/"):
            urls = [f"https://{dominio}{entrada}", f"http://{dominio}{entrada}"]
        else:  
            urls = [f"https://{entrada}.{dominio}", f"http://{entrada}.{dominio}"]

        for url in urls:
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    resultado = f"[{r.status_code}] {url}"
                    ativos.append(url)
                    text_box.insert(tk.END, resultado + "\n")
                    text_box.see(tk.END)
                    break
            except requests.exceptions.RequestException:
                continue        

        progress["value"] = i
        janela.update_idletasks()

    lbl_resultado.config(
        text=f"Total de Entradas Testadas: {total}\n"
             f"Ativos (status 200): {len(ativos)}"
    )
    lbl_atual.config(text="Scan finalizado!")


def iniciar_scan():
    global scan_thread, parar_scan
    parar_scan = False
    if scan_thread is None or not scan_thread.is_alive():
        scan_thread = threading.Thread(target=escanear, daemon=True)
        scan_thread.start()


def parar_scan_func():
    global parar_scan
    parar_scan = True


def salvar_resultados():
    global ativos
    if not ativos:
        messagebox.showwarning("Aviso", "Nenhum resultado encontrado para salvar!")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")),
        title="Salvar resultados"
    )

    if not caminho:
        return

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            for item in ativos:
                f.write(item + "\n")
        messagebox.showinfo("Sucesso", f"Resultados salvos em: {caminho}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar resultados:\n{e}")


# GUI
janela = tk.Tk()
janela.title("Scanner de Subdomínios e Diretórios")
janela.geometry("1070x900")

lbl_dominio = tk.Label(janela, text="Digite o domínio (ex: exemplo.com)", font=("Arial", 10))
lbl_dominio.pack(pady=5)

entrada_url = tk.Entry(janela, width=23, font=("Arial", 12))
entrada_url.pack(pady=5)

tk.Button(janela, text="Carregar Wordlist", bg="#03fcdb", fg="black", font=("Arial", 10), command=carregar_wordlist).pack(pady=5)

# Mostra quantas linhas tem a wordlist carregada
lbl_wordlist_info = tk.Label(janela, text="Nenhuma wordlist carregada", font=("Arial", 10, "italic"))
lbl_wordlist_info.pack(pady=5)

tk.Button(janela, text="Iniciar Scan", bg="#03fc24", fg="black", font=("Arial", 10), command=iniciar_scan).pack(pady=5)

progress = ttk.Progressbar(janela, orient="horizontal", length=500, mode="determinate")
progress.pack(pady=5)

# Label que mostra a entrada atual
lbl_atual = tk.Label(janela, text="Nenhum teste iniciado", font=("Arial", 10, "italic"))
lbl_atual.pack(pady=5)

lbl_resultado = tk.Label(janela, text="", justify="left", font=("Arial", 12, "bold"))
lbl_resultado.pack(pady=5)

# Botão para salvar os resultados em arquivo
tk.Button(janela, text="Salvar Resultados", bg="#fcc603", fg="black", font=("Arial", 10), command=salvar_resultados).pack(pady=5)

text_box = scrolledtext.ScrolledText(janela, width=120, height=33)
text_box.pack(pady=5)

janela.mainloop()
