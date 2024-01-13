import tkinter as tk
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from random import randint
from tkinter import scrolledtext, filedialog
import os
import sys
from datetime import datetime
from PIL import Image, ImageTk
from io import BytesIO
import requests

# Configurar a localidade para português do Brasil
from locale import setlocale, LC_TIME
setlocale(LC_TIME, 'pt_BR.utf8')

# Variável global para controlar a mensagem de intrusão
intrusion_detected = False
server = None  # Variável global para armazenar a instância do servidor

# Mensagem HTML de boas-vindas
welcome_message = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem-vindo, site seguro!</title>
</head>
<body>
    <h1>Bem-vindo, site seguro!</h1>
    <p>Este é um site seguro. Todas as atividades são monitoradas.</p>
</body>
</html>
"""

# Salva as saídas padrão
original_stdout = sys.stdout
original_stderr = sys.stderr

# Redireciona a saída padrão e de erro para /dev/null (Linux) ou nul (Windows)
if sys.platform.startswith('linux'):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
elif sys.platform.startswith('win'):
    sys.stdout = open('nul', 'w')
    sys.stderr = open('nul', 'w')

# Classe para manipular as solicitações HTTP
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global intrusion_detected
        # Registra o IP e a URL acessada        
        ip = self.client_address[0]
        port = self.server.server_port
        url = self.path

        # Mapear o número do dia da semana para o nome em português
        weekday_names = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo"
        ]
        weekday_number = datetime.now().weekday()
        weekday_name = weekday_names[weekday_number]
        
        status_message = f"\nTENTATIVA DE INTRUSAO DETECTADA! de {port}:{ip} ({weekday_name} - {datetime.now().strftime('%c')})\n"
        result_text.insert(tk.END, status_message)

        # Adiciona cabeçalho da página à janela
        result_text.insert(tk.END, "\nCabeçalho da Página:\n")
        for header, value in self.headers.items():
            result_text.insert(tk.END, f"{header}: {value}\n")

        if intrusion_detected:
            # Exibe a mensagem de intrusão
            self.send_response(403)
            self.end_headers()
            result_text.insert(tk.END, "Resposta HTTP 403: Acesso Proibido\n")
            intrusion_detected = False  # Reinicia a variável após exibir a mensagem
        else:
            # Envia a mensagem de boas-vindas em HTML
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(welcome_message, "utf8"))

# Classe para criar um servidor HTTP
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

# Função para iniciar o servidor
def start_server(port):
    global server
    server = ThreadedHTTPServer(('0.0.0.0', port), RequestHandler)
    server.serve_forever()

# Função para parar o servidor
def stop_server():
    if server:
        server.shutdown()
        server.server_close()

# Função para gerar uma porta aleatória e atualizar a interface gráfica
def generate_random_port():
    port = randint(80, 1000)
    status_message = f"\nAcesse o link:  http://127.0.0.1:{port}\n" 
                     
    result_text.insert(tk.END, status_message + '\n')
    return port

# Função para iniciar o honeypot
def start_honeypot():
    port = generate_random_port()
    threading.Thread(target=start_server, args=(port,), daemon=True).start()
    result_text.insert(tk.END, f"Honeypot em execução na porta {port}\n")

# Função para salvar o log em um arquivo
def save_log():
    log_content = result_text.get(1.0, tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'w') as log_file:
            log_file.write(log_content)
        result_text.insert(tk.END, f"\n\nLog salvo em:  {file_path}\n")

def close_app():
    stop_server()  # Para o servidor antes de fechar
    # Restaura as saídas padrão
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    app.destroy()
    sys.exit(0)  # Isso é opcional e encerra completamente o programa

# Interface gráfica
app = tk.Tk()
app.wm_state('zoomed')
app.title("Honeypot")
app.configure(bg="black")

# URL do ícone
icon_url = "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_126364879a855974c6b01ee7c5066358/honeypot.png"  # Substitua pela URL do seu ícone

# Função para baixar o ícone da web
def download_icon(url):
    response = requests.get(url)
    icon_data = BytesIO(response.content)
    return Image.open(icon_data)

# Baixar o ícone da web
icon_image = download_icon(icon_url)

# Converter a imagem para o formato TKinter
tk_icon = ImageTk.PhotoImage(icon_image)

# Definir o ícone da janela
app.iconphoto(True, tk_icon)

# Associar a função close_app ao evento de fechar a janela
app.protocol("WM_DELETE_WINDOW", close_app)

# Rótulo Honeypot
label_honeypot = tk.Label(app, text="👩‍💻 🍯 Honeypot 🍯 👩‍💻", font=("Arial", 18), pady=10, fg="yellow", bg="black", bd=5)
label_honeypot.grid(row=0, column=0, columnspan=3)

# Componentes da interface
button_start = tk.Button(app, text="Iniciar Honeypot", command=start_honeypot, bg="#00FFFF", font=("Arial", 11))
button_save_log = tk.Button(app, text="Salvar Log Como", command=save_log, bg="#05fc47", font=("Arial", 11))
button_close = tk.Button(app, text="Fechar Tudo", command=close_app, bg="#f57d7d", font=("Arial", 11))

# Layout da interface
button_start.grid(row=1, column=0, pady=10)
button_save_log.grid(row=1, column=1, pady=10)
button_close.grid(row=1, column=2, pady=10)

# Criar o frame para o resultado
result_frame = tk.Frame(app, bg="black")
result_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=2)

# Criar o widget ScrolledText
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=130, height=45, font=("Arial", 12), bg="black", fg="white")
result_text.grid(column=0, row=0, sticky=tk.W + tk.E + tk.N + tk.S, padx=50)

app.mainloop()
