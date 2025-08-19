import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import threading

def consultar():
    # Resetar barra de progresso
    progress['value'] = 0
    text_output.delete(1.0, tk.END)

    def task():
        dominio = entry_domain.get().strip()
        if not dominio:
            return

        url = f"https://www.hudsonrock.com/search?domain={dominio}"

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--window-size=1920,1080")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # Etapa 1: abrir página
            driver.get(url)
            time.sleep(5)
            progress['value'] = 20

            resultados = {}

            # Etapa 2: coletar usuários
            try:
                usuarios = driver.find_element(By.ID, "users-count").text
                resultados["Usuários comprometidos"] = usuarios
            except:
                resultados["Usuários comprometidos"] = "Não encontrado"
            progress['value'] = 40

            # Etapa 3: coletar funcionários
            try:
                funcionarios = driver.find_element(By.ID, "employees-count").text
                resultados["Funcionários comprometidos"] = funcionarios
            except:
                resultados["Funcionários comprometidos"] = "Não encontrado"
            progress['value'] = 60

            # Etapa 4: coletar terceiros
            try:
                terceiros = driver.find_element(By.ID, "tp-count").text
                resultados["Funcionários terceirizados"] = terceiros
            except:
                resultados["Funcionários terceirizados"] = "Não encontrado"
            progress['value'] = 80

            # Etapa 5: coletar URLs
            urls = []
            spans = driver.find_elements(By.TAG_NAME, "span")
            for span in spans:
                text = span.text.strip()
                if re.match(r'https?://\S+', text):
                    urls.append(text)
            resultados["\n\nURL Encontradas"] = "\n\n".join(urls) if urls else "\nNenhuma URL encontrada"
            progress['value'] = 100

            driver.quit()

            # Exibir no text_output
            text_output.delete(1.0, tk.END)
            for k, v in resultados.items():
                text_output.insert(tk.END, f"{k}: {v}\n\n")

        except Exception as e:
            text_output.delete(1.0, tk.END)            
            progress['value'] = 0
            messagebox.showerror("Erro", f"Falha ao consultar: {e}")

    threading.Thread(target=task).start()

def salvar_resultados():
    conteudo = text_output.get(1.0, tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Não há resultados para salvar.")
        return
    arquivo = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Arquivo de texto", "*.txt")],
                                           title="Salvar resultados")
    if arquivo:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        messagebox.showinfo("Sucesso", f"\nResultados salvos com sucesso em: {arquivo}")

# GUI
root = tk.Tk()
root.title("Hudson Rock Scraper")
root.geometry("1180x900")

frame = ttk.Frame(root, padding=10)
frame.pack(pady=10)

ttk.Label(frame, text="Digite o Domínio", font=("Arial", 10, "bold")).grid(pady=5)
entry_domain = ttk.Entry(frame, width=30, font=("Arial", 12, "bold"))
entry_domain.grid(pady=5)

btn_consultar = tk.Button(frame, text="Consultar", bg="#03fc24", fg="black", command=consultar)
btn_consultar.grid(padx=5, pady=5)

btn_salvar = tk.Button(frame, text="Salvar Resultados", bg="#fc9d03", fg="black", command=salvar_resultados)
btn_salvar.grid(padx=5, pady=5)

# Barra de progresso percentual
progress = ttk.Progressbar(frame, orient='horizontal', length=500, mode='determinate', maximum=100)
progress.grid(pady=10)

text_output = scrolledtext.ScrolledText(frame, width=120, height=35, font=("Arial", 12, "bold"))
text_output.grid(pady=10)

root.mainloop()
