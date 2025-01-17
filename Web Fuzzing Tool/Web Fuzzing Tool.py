import requests
import concurrent.futures
from urllib.parse import urljoin
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import threading
from tkinter import ttk  # Importar o ttk para a barra de progresso

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para baixar o wordlist
def download_wordlist(wordlist_path):
    try:
        with open(wordlist_path, 'r') as file:
            return file.read().splitlines()
    except Exception as e:
        return None

# Função para fuzzar as URLs
def fuzz_url(base_url, word, results_text, found_urls, progress, total_words, update_progress):
    url = urljoin(base_url, word.strip())
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        status = response.status_code
        size = len(response.content)

        if status == 200 or status == 301:
            # Determinando o tipo de página
            if size < 1024:
                page_type = "Página bem pequena"
            elif size < 10240:
                page_type = "Página pequena"
            elif size < 1048576:
                page_type = "Página média"
            elif size < 10485760:
                page_type = "Página de tamanho normal"
            else:
                page_type = "Página grande"

            result = f"{url:<32} Status: {status}, Tamanho: {size / (1024 * 1024):.2f} MB, Tipo: {page_type}"
            
            # Exibir resultado em vermelho para status 301
            if status == 301:
                results_text.insert(tk.END, result + "\n", "red")
            else:
                results_text.insert(tk.END, result + "\n")
            
            results_text.yview(tk.END)  # Auto scroll para o final
            found_urls.append(url)  # Adiciona URL à lista de encontrados

    except requests.RequestException:
        pass

    update_progress()  # Atualizando a barra de progresso

# Função para salvar os resultados
def save_results(results_text):
    global found_urls  # Acessando a variável global found_urls
    save_choice = messagebox.askyesno("Salvar Resultados", "Deseja salvar os resultados?")
    if save_choice:
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filename:
            try:
                with open(filename, 'w') as file:
                    file.write(results_text.get(1.0, tk.END))
                messagebox.showinfo("Resultado", f"Total de URLs encontradas: {len(found_urls)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")

# Função principal que configura a GUI
def main():
    global found_urls  # A variável found_urls deve ser global
    found_urls = []  # Lista para armazenar URLs encontradas
    wordlist_path = None  # Inicializando a variável wordlist_path
    
    def select_wordlist():
        nonlocal wordlist_path  # Acessando a variável wordlist_path dentro da função
        wordlist_path = filedialog.askopenfilename(title="Selecione o arquivo wordlist", filetypes=[("Text Files", "*.txt")])
        if wordlist_path:
            messagebox.showinfo("Wordlist Selecionada", f"Wordlist selecionada: {wordlist_path}")
    
    def start_fuzzing():
        if not wordlist_path:
            messagebox.showerror("Erro", "Nenhum arquivo wordlist selecionado.")
            return
        
        base_url = url_entry.get().strip()
        if not base_url.endswith("/FUZZ"):
            if not base_url.endswith("/"):
                base_url += "/"
            base_url += "FUZZ"
        
        words = download_wordlist(wordlist_path)
        if not words:
            messagebox.showerror("Erro", "Ocorreu um erro ao carregar o wordlist.")
            return
        
        results_text.delete(1.0, tk.END)  # Limpar resultados anteriores

        # Função para atualizar a barra de progresso
        def update_progress():
            progress['value'] += (100 / len(words))  # Atualizando a barra de progresso
            progress.update()  # Forçando a atualização da barra de progresso

        # Função que executa o fuzzing em uma thread separada
        def fuzz_in_thread():
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(fuzz_url, base_url, word, results_text, found_urls, progress, len(words), update_progress) for word in words]
                    concurrent.futures.wait(futures)

                if results_text.get(1.0, tk.END).strip() == "":
                    messagebox.showinfo("Resultado", "Nenhum URL retornou o status 200 ou 301.")
                else:
                    messagebox.showinfo("Resultado", f"Total de URLs encontradas: {len(found_urls)}")

            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao processar as URLs: {e}")
            
            progress['value'] = 100  # Garantir que a barra de progresso chegue a 100% ao fim
            start_button.config(state=tk.NORMAL)  # Reabilitar o botão de fuzzing quando o processo terminar

        # Desabilitar o botão de fuzzing para evitar múltiplos cliques
        start_button.config(state=tk.DISABLED)

        # Iniciando o fuzzing em uma thread separada
        fuzz_thread = threading.Thread(target=fuzz_in_thread)
        fuzz_thread.daemon = True  # Permite que a thread seja fechada quando a GUI for fechada
        fuzz_thread.start()

    # Criando a janela principal
    window = tk.Tk()
    window.title("Web Fuzzing Tool")
    window.geometry("1200x960")

    # Estilo da barra de progresso
    style = ttk.Style()
    style.theme_use('default')  # Usar o tema padrão
    style.configure('green.Horizontal.TProgressbar', background='#00FF00')  # Definir cor verde para a barra

    # Adicionando campos de entrada
    tk.Label(window, text="Digite a URL base (ex: https://example.com):").pack(pady=5)
    url_entry = tk.Entry(window, width=50, font=("Arial", 11, "bold"))
    url_entry.pack(pady=5)

    # Adicionando o botão para selecionar o wordlist
    select_wordlist_button = tk.Button(window, text="Selecionar Wordlist", command=select_wordlist, font=("Arial", 11, "bold"), background='#0ae1f5')
    select_wordlist_button.pack(pady=5)

    # Adicionando o botão para iniciar o fuzzing
    start_button = tk.Button(window, text="Iniciar Fuzzing", command=start_fuzzing, font=("Arial", 11, "bold"), background='#00FF00')
    start_button.pack(pady=10)

    # Adicionando o botão para salvar os resultados
    save_button = tk.Button(window, text="Salvar Resultados", command=lambda: save_results(results_text), font=("Arial", 11, "bold"), background='#f5b20a')
    save_button.pack(pady=5)

    # Adicionando a barra de progresso
    progress = ttk.Progressbar(window, orient="horizontal", length=400, mode="determinate", style='green.Horizontal.TProgressbar')
    progress.pack(pady=10)

    # Adicionando a área de texto para exibir os resultados com tag para a cor vermelha
    results_text = ScrolledText(window, width=120, height=40)
    results_text.pack(pady=10)  
    results_text.tag_configure("red", foreground="#f50a16")  # Configurando a cor vermelha

    # Iniciando a GUI
    window.mainloop()

if __name__ == "__main__":
    main()
