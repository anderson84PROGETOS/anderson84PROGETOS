import tkinter as tk
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from tkinter import scrolledtext, filedialog, messagebox
import os
import sys
from datetime import datetime
from urllib.parse import parse_qs

# Função para iniciar o honeypot com arquivo HTML personalizado
def start_honeypot():
    # Solicitar ao usuário que escolha o arquivo HTML
    html_file_path = filedialog.askopenfilename(defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All files", "*.*")])

    if not html_file_path:
        messagebox.showwarning("Aviso", "Selecione um arquivo HTML válido.")
        return

    # Ler o conteúdo do arquivo HTML escolhido
    with open(html_file_path, 'r', encoding='utf-8') as html_file:
        global welcome_message
        welcome_message = html_file.read()

    # Obter a porta do campo de entrada
    try:
        port = int(port_entry.get())
        if not (1 <= port <= 65535):
            raise ValueError("Porta fora do intervalo permitido (1-65535).")
    except ValueError as ve:
        messagebox.showwarning("Aviso", f"Porta inválida: {ve}")
        return

    # Iniciar o servidor em uma thread separada
    threading.Thread(target=start_server, args=(port,), daemon=True).start()

    # Exibir a URL no resultado
    result_text.insert(tk.END, f"Honeypot em execução na porta: {port}\n")
    result_text.insert(tk.END, f"\nConecte-se usando a URL: http://127.0.0.1:{port}\n")

# Configurar a localidade para português do Brasil
from locale import setlocale, LC_TIME
setlocale(LC_TIME, 'pt_BR.utf8')

# Variável global para controlar a mensagem de intrusão
intrusion_detected = False
server = None  # Variável global para armazenar a instância do servidor

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
        
        status_message = f"\n\nTENTATIVA DE INTRUSAO DETECTADA    {ip}:{port}  ({weekday_name} -  {datetime.now().strftime('%c')})\n"
        result_text.insert(tk.END, status_message)

        # Adiciona cabeçalho da página à janela
        result_text.insert(tk.END, "\nCabeçalho da Página\n=================\n")
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
            self.end_headers()
            self.wfile.write(bytes(welcome_message, "utf8"))

    def do_POST(self):
    # Lidar com solicitações POST e extrair dados do corpo
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_params = parse_qs(post_data.decode('utf-8'))

        # Exibir os dados recebidos no resultado
        result_text.insert(tk.END, "\n\n\nDados Recebidos\n==============\n")
        
        # Chaves indesejadas a serem filtradas
        unwanted_keys = ["source"]

        for key, value in post_params.items():
            if key not in unwanted_keys:
                result_text.insert(tk.END, f"{key}: {value[0]}\n")

        # Enviar resposta HTTP 200 OK
        self.send_response(200)            
        self.end_headers()

        try:
            with open('success_page.html', 'r', encoding='utf-8') as success_page_file:
                success_page_content = success_page_file.read()
            self.wfile.write(bytes(success_page_content, "utf8"))
        except Exception as e:                
            self.wfile.write(bytes("Dados registrados com sucesso!", "utf8"))


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

# Função para salvar o log em um arquivo
def save_log():
    log_content = result_text.get(1.0, tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'w') as log_file:
            log_file.write(log_content)
        result_text.insert(tk.END, f"\n\nLog salvo em: {file_path}\n")

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

# Associar a função close_app ao evento de fechar a janela
app.protocol("WM_DELETE_WINDOW", close_app)

# Rótulo Honeypot
label_honeypot = tk.Label(app, text="👩‍💻 🍯 Honeypot 🍯 👩‍💻", font=("Arial", 18), pady=10, fg="yellow", bg="black", bd=5)
label_honeypot.grid(row=0, column=0, columnspan=3)

# Componentes da interface
port_label = tk.Label(app, text="Porta", font=("Arial", 11), fg="white", bg="black")
port_label.grid(row=1, column=0, columnspan=2, pady=10, padx=(0, 270), sticky=tk.E) 

port_entry = tk.Entry(app, font=("Arial", 11), width=10)
port_entry.grid(row=1, column=1, pady=10)
port_entry.insert(0, "8080")  # Valor padrão da porta

button_start = tk.Button(app, text="Iniciar Honeypot", command=start_honeypot, bg="#00FFFF", font=("Arial", 11))
button_save_log = tk.Button(app, text="Salvar Log Como", command=save_log, bg="#05fc47", font=("Arial", 11))
button_close = tk.Button(app, text="Fechar Tudo", command=close_app, bg="#f57d7d", font=("Arial", 11))

# Layout da interface
button_start.grid(row=2, column=0, pady=10)
button_save_log.grid(row=2, column=1, pady=10)
button_close.grid(row=2, column=2, pady=10)

# Criar o frame para o resultado
result_frame = tk.Frame(app, bg="black")
result_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=2)

# Criar o widget ScrolledText
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=130, height=42, font=("Arial", 12), bg="black", fg="white")
result_text.grid(column=0, row=0, sticky=tk.W + tk.E + tk.N + tk.S, padx=50)

app.mainloop()
