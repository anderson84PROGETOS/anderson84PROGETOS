import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
import threading

subdomains = []
thread = None
exit_event = threading.Event()

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

def salvar_resultados():
    linhas = text_area.get("1.0", tk.END).strip().split("\n")
    subdominios_filtrados = [linha for linha in linhas if "." in linha and " " not in linha]

    if not subdominios_filtrados:
        messagebox.showwarning("Aviso", "Nenhum subdomínio para salvar!")
        return
    
    arquivo = filedialog.asksaveasfilename(
        title="Salvar resultados",
        defaultextension=".txt",
        filetypes=[("Arquivos de texto", "*.txt")]
    )
    
    if arquivo:
        try:
            with open(arquivo, "w") as file:
                file.write("\n".join(subdominios_filtrados))
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {str(e)}")

def escanear_subdominios_thread(domain):
    global exit_event

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    }

    total_subdomains = len(subdomains)
    
    def atualizar_texto(texto):
        text_area.insert(tk.END, texto)
        text_area.see(tk.END)  # Rolar para o final automaticamente

    root.after(0, lambda: atualizar_texto(f"Procurando subdomínios para: {domain}\n\n"))
    progress_bar["maximum"] = total_subdomains
    progress_bar["value"] = 0

    for idx, subdomain in enumerate(subdomains):
        if exit_event.is_set():
            break
        url = f"http://{subdomain}.{domain}"

        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                root.after(0, lambda subdomain=subdomain: atualizar_texto(f"{subdomain}.{domain}\n"))
        except requests.RequestException:
            pass

        root.after(0, lambda idx=idx: progress_bar.config(value=idx + 1))
    
    root.after(0, lambda: progress_bar.config(value=total_subdomains))
    
    if not exit_event.is_set():
        root.after(0, lambda: atualizar_texto("\n\n\nBusca concluída!\n"))
    else:
        root.after(0, lambda: atualizar_texto("\n\n\nBusca interrompida!\n"))

    root.after(0, lambda: escanear_button.config(state=tk.NORMAL))

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
    exit_event.clear()
    thread = threading.Thread(target=escanear_subdominios_thread, args=(domain,))
    thread.daemon = True
    thread.start()

def on_close():
    global exit_event
    if thread and thread.is_alive():
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa? O escaneamento será interrompido."):
            exit_event.set()
            thread.join(timeout=2)
    root.destroy()

root = tk.Tk()
root.title("subdomain checker")
root.geometry("1100x900")
root.protocol("WM_DELETE_WINDOW", on_close)

label = tk.Label(root, text="Nome do Domínio", font=("Arial", 11))
label.pack(pady=5)

domain_entry = tk.Entry(root, width=30, font=("Arial", 11))
domain_entry.pack(pady=5)

escanear_button = tk.Button(root, text="Escanear Subdomínios", command=escanear_subdominios, font=("Arial", 11), bg="#0bfc03", state=tk.DISABLED)
escanear_button.pack(pady=10)

buscar_button = tk.Button(root, text="Selecionar subdomain.txt", command=selecionar_arquivo, font=("Arial", 11), bg="#03e3fc")
buscar_button.pack(pady=10)

salvar_button = tk.Button(root, text="Salvar Resultados", command=salvar_resultados, font=("Arial", 11), bg="#fca503")
salvar_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

text_area = scrolledtext.ScrolledText(root, width=100, height=30, font=("Arial", 12))
text_area.pack(pady=10)

root.mainloop()
