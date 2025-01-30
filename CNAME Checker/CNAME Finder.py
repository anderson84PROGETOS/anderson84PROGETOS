import tkinter as tk
from tkinter import filedialog, messagebox
import dns.resolver
import os
from tkinter import ttk
import threading  # Importando threading para rodar processos em segundo plano

# Funções de DNS
def obter_cname(site, cname_set, resultados):
    try:
        respostas = dns.resolver.resolve(site, 'CNAME', lifetime=10)
        for resposta in respostas:
            cname = resposta.to_text()
            if cname not in cname_set:
                cname_set.add(cname)
                try:
                    ip_respostas = dns.resolver.resolve(cname, 'A', lifetime=10)
                    for ip_resposta in ip_respostas:
                        ip = ip_resposta.to_text()
                        if ip:
                            pass
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                    pass
                except dns.exception.DNSException as e:
                    print(f"Erro ao consultar IP para {cname}: {e}")
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar CNAME para {site}: {e}")

def obter_ip_do_cname(cname, resultados):
    try:
        respostas = dns.resolver.resolve(cname, 'A', lifetime=10)
        for resposta in respostas:
            ip = resposta.to_text()
            if ip:
                resultados.append(f"CNAME: {cname:<65} -> IP: {ip}")
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar IP para {cname}: {e}")

def encontrar_subdominios(site, subdominios_comuns, cname_set, resultados, progress_var):    
    total_subdominios = len(subdominios_comuns)
    separador_adicionado = False  # Garante que o separador aparece apenas uma vez
    
    for idx, sub in enumerate(subdominios_comuns):
        subdominio = f"{sub}.{site}"
        try:
            respostas = dns.resolver.resolve(subdominio, 'A', lifetime=10)
            for resposta in respostas:
                if subdominio not in cname_set:
                    if not separador_adicionado:                        
                        root.after(0, lambda: resultados_text.insert(tk.END, "======== Subdomínios Encontrados =========\n\n"))
                        separador_adicionado = True  # Evita repetir
                    resultado_str = f"Subdominio: {subdominio:<60} -> IP: {resposta.to_text()}\n"                    
                    root.after(0, lambda r=resultado_str: resultados_text.insert(tk.END, r))  # Adiciona no GUI
                    obter_cname(subdominio, cname_set, resultados)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except dns.exception.DNSException:
            pass  # Remove erro
        # Atualiza a barra de progresso
        progress_var.set((idx + 1) / total_subdominios * 100)
        root.update_idletasks()  # Atualiza GUI para exibir os resultados corretamente

def process_wordlist(file_path):
    try:
        with open(file_path, "r") as file:
            linhas = file.readlines()
            subdominios = set(linha.strip() for linha in linhas if linha.strip())
            return subdominios
    except FileNotFoundError:
        print(f"Erro: Arquivo '{file_path}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None

def escolher_wordlist():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        subdominios_comuns = process_wordlist(file_path)
        if subdominios_comuns:
            messagebox.showinfo("Wordlist carregada", f"{len(subdominios_comuns)} subdomínios encontrados na wordlist.")
            return subdominios_comuns
    return []

def verificar_subdominios():
    site = site_entry.get()
    if not site:
        messagebox.showerror("Erro", "Digite o nome do website.")
        return

    subdominios_comuns = wordlist_data
    if not subdominios_comuns:
        messagebox.showerror("Erro", "Não há wordlist carregada.")
        return

    cname_set = set()
    resultados = []   
        
    # Barra de progresso
    progress_var.set(0)  # Inicializa a barra de progresso
    progress_bar.pack(pady=10, padx=5)  # Exibe a barra de progresso usando pack

    # Rodar a varredura em um thread para não travar a interface gráfica
    def run_thread():
        encontrar_subdominios(site, subdominios_comuns, cname_set, resultados, progress_var)
        # Adiciona separador entre CNAME e Subdomínios
        resultados.append("\n\n======= CNAME Encontrados =====\n")
        if cname_set:
            for cname in cname_set:
                obter_ip_do_cname(cname, resultados)
        else:
            resultados.append("Nenhum CNAME encontrado.\n")    
        
        # Separa e organiza os subdomínios encontrados
        if resultados:
            resultados_text.insert(tk.END, "\n".join(resultados) + "\n")
        else:
            resultados_text.insert(tk.END, "Nenhum subdomínio encontrado.\n")

        # Remover a barra de progresso após a conclusão
        progress_bar.pack_forget()

    # Iniciar thread para executar a varredura
    threading.Thread(target=run_thread, daemon=True).start()

def salvar_resultados():
    resultados = resultados_text.get("1.0", tk.END).strip()
    if not resultados:
        messagebox.showerror("Erro", "Não há resultados para salvar.")
        return

    nome_arquivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if nome_arquivo:
        try:
            with open(nome_arquivo, 'w') as file:
                file.write(resultados)
            messagebox.showinfo("Salvo", f"Resultados salvos em {nome_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

# Configuração da interface gráfica
root = tk.Tk()
root.title("CNAME Finder")
root.geometry("1200x950")

# Variáveis
wordlist_data = []
progress_var = tk.DoubleVar()  # Variável para a barra de progresso

# Widgets
site_label = tk.Label(root, text="Digite o nome do website:")
site_label.pack(pady=5)

site_entry = tk.Entry(root, width=40, font=("Arial", 11))
site_entry.pack(pady=5)

carregar_button = tk.Button(root, text="Escolher Wordlist", command=lambda: wordlist_data.extend(escolher_wordlist()), font=("Arial", 11), bg="#0ae7f2")
carregar_button.pack(pady=5)

verificar_button = tk.Button(root, text="Verificar Subdomínios", command=verificar_subdominios, font=("Arial", 11), bg="#0bfc03")
verificar_button.pack(pady=5)

salvar_button = tk.Button(root, text="Salvar Resultados", command=salvar_resultados, font=("Arial", 11), bg="#f2ac0a")
salvar_button.pack(pady=5)

# Barra de progresso com tamanho reduzido
progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

# Adicionando a Scrollbar ao Text widget
scrollbar = tk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

resultados_text = tk.Text(root, height=40, width=120, yscrollcommand=scrollbar.set)
resultados_text.pack(pady=10)

scrollbar.config(command=resultados_text.yview)

# Iniciar a interface gráfica
root.mainloop()

