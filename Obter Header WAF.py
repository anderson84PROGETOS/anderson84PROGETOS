import tkinter as tk
from tkinter import scrolledtext
import requests
import socket
from urllib.parse import urlparse

def obter_header_servidor():
    url_alvo = url_entry.get()

    # Validação da URL
    try:
        parsed_url = urlparse(url_alvo)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("URL inválida")
    except ValueError as ve:
        exibir_erro(f"Erro ao validar a URL: {ve}")
        return
    
    try:
        # Obtém o endereço IP correspondente ao domínio
        ip = socket.gethostbyname(parsed_url.netloc)

        # Envia uma solicitação HTTP GET para a URL
        resposta = requests.get(url_alvo)

        # Obtém o cabeçalho 'Server' da resposta
        servidor = resposta.headers.get('Server')

        # Exibe todos os cabeçalhos da resposta
        headers = resposta.headers
        headers_text = "\n\nCabeçalhos:\n"
        for header, value in headers.items():
            headers_text += f"\n{header}: {value}\n"

        # Atualiza o campo de texto com o cabeçalho do servidor, o domínio, o IP e os cabeçalhos adicionais
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)  # Limpa o campo de texto
        result_text.insert(tk.END, f"Domínio: {parsed_url.netloc}\n")
        result_text.insert(tk.END, f"\n\nIP: {ip}\n\n")

        # Configura a cor de fundo antes de inserir o texto
        result_text.tag_config("green_background", background="#1df50a", font=("Arial", 18))
        result_text.insert(tk.END, f"Servidor WAF: {servidor}", "green_background") 
        
        result_text.insert(tk.END, headers_text)
        result_text.config(state=tk.DISABLED)

    except requests.RequestException as e:
        # Em caso de erro na solicitação HTTP, exibe uma mensagem de erro no campo de texto
        exibir_erro(f"Erro ao fazer a solicitação: {e}")
    except socket.gaierror as e:
        # Tratamento de exceção para erros de resolução de DNS
        exibir_erro(f"Erro de DNS: {e}")

def exibir_erro(mensagem):
    # Exibe mensagens de erro no campo de texto
    result_text.config(state=tk.NORMAL)
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, mensagem)
    result_text.config(state=tk.DISABLED)

# Cria a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Obter Header do Servidor WAF")

# Cria e posiciona os widgets na janela
url_label = tk.Label(window, text="Digite a URL do WebSite")
url_label.pack(pady=5)

url_entry = tk.Entry(window, width=40, font=("Arial", 12))
url_entry.pack(pady=5)

obter_button = tk.Button(window, text="Obter Header do Servidor WAF", command=obter_header_servidor, background="#11e7f2")
obter_button.pack(pady=10)

# Área de exibição dos resultados
result_text = scrolledtext.ScrolledText(window, width=130, height=40, font=("Arial", 13))
result_text.pack(pady=10)
result_text.config(state=tk.DISABLED)

# Inicia o loop principal da interface gráfica
window.mainloop()
