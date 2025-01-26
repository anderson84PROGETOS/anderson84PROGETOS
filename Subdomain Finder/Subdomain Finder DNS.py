import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
import threading
import dns.resolver  # Importa o dns.resolver

subdomains = []  # Variável global para armazenar os subdomínios carregados
thread = None  # Variável global para armazenar a referência da thread em execução
exit_event = threading.Event()  # Evento para sinalizar a thread para sair

def selecionar_arquivo():
    global subdomains
    arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo subdomain.txt",
        filetypes=[("Arquivos de texto", "*.txt")]
    )

    if not arquivo:
        messagebox.showwarning("Aviso", "Nenhum arquivo foi selecionado!")
        return

    try:
        with open(arquivo, "r") as file:
            subdomains = [line.strip() for line in file.readlines() if line.strip()]
        messagebox.showinfo("Sucesso", "Arquivo carregado com sucesso!")
        escanear_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler o arquivo: {str(e)}")

def escanear_subdominios_thread(domain):
    global exit_event

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    }

    total_subdomains = len(subdomains)
    text_area.delete(1.0, tk.END)  # Limpar a área de resultados
    text_area.insert(tk.END, f"Procurando subdomínios para: {domain}\n\n")

    progress_bar["maximum"] = total_subdomains  # Definir o valor máximo da barra de progresso
    progress_bar["value"] = 0  # Resetar o valor da barra de progresso

    for idx, subdomain in enumerate(subdomains):
        if exit_event.is_set():  # Verificar se a thread deve ser interrompida
            break
        url = f"http://{subdomain}.{domain}"

        try:
            # Obter o IP do subdomínio usando o dns.resolver
            answer = dns.resolver.resolve(f"{subdomain}.{domain}", "A")
            ip = answer[0].to_text()
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
            ip = "IP não encontrado"

        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                text_area.insert(tk.END, f"[Encontrado] {url:<55} IP: {ip}\n")
        except requests.RequestException:
            continue

        # Atualizar a barra de progresso diretamente após cada iteração
        progress_bar["value"] = idx + 1
        root.update_idletasks()

    if not exit_event.is_set():
        progress_bar["value"] = total_subdomains  # Definir a barra de progresso como completa
        text_area.insert(tk.END, "\nBusca concluída!\n")
    else:
        text_area.insert(tk.END, "\nBusca interrompida!\n")

    escanear_button.config(state=tk.NORMAL)

def escanear_subdominios():
    if not subdomains:
        messagebox.showwarning("Aviso", "Nenhum arquivo foi carregado! Por favor, selecione um arquivo primeiro.")
        return

    domain = domain_entry.get().strip()
    if not domain:
        messagebox.showwarning("Aviso", "Digite o nome do domínio!")
        return

    escanear_button.config(state=tk.DISABLED)

    global thread
    global exit_event
    exit_event.clear()  # Resetar o evento de saída
    thread = threading.Thread(target=escanear_subdominios_thread, args=(domain,))
    thread.start()

def on_close():
    """Método para fechar o aplicativo e interromper a execução de forma completa."""
    global exit_event
    if thread and thread.is_alive():
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa? O escaneamento será interrompido."):
            exit_event.set()  # Sinalizar para interromper a execução da thread
            thread.join(timeout=1)  # Esperar a thread terminar por até 1 segundo
    root.destroy()

# Interface gráfica
root = tk.Tk()
root.title("Subdomain Finder DNS")
root.geometry("1200x950")

# Campo de entrada para o domínio
label = tk.Label(root, text="Nome do Domínio", font=("Arial", 11))
label.pack(pady=5)

domain_entry = tk.Entry(root, width=30, font=("Arial", 11))
domain_entry.pack(pady=5)

# Botão para escanear os subdomínios (inicialmente desabilitado)
escanear_button = tk.Button(root, text="Escanear Subdomínios", command=escanear_subdominios, font=("Arial", 11), bg="#0bfc03", state=tk.DISABLED)
escanear_button.pack(pady=10)

# Botão para selecionar o arquivo
buscar_button = tk.Button(root, text="Selecionar subdomain.txt", command=selecionar_arquivo, font=("Arial", 11), bg="#03e3fc")
buscar_button.pack(pady=10)

# Separador horizontal
separator = ttk.Separator(root, orient="horizontal")

# Barra de progresso (ajustada para preencher corretamente)
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

# Área de texto para exibir os resultados com barra de rolagem
text_area = scrolledtext.ScrolledText(root, width=120, height=35)
text_area.pack(pady=10)

# Iniciar a interface
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
