import socket
import time
import os
import threading
from random import randint

class Honeypot_pb:
    def honeyconfig(self, port, message, log, logname, content_source, gif_url):
        try:
            tcpserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpserver.bind(("0.0.0.0", port))
            tcpserver.listen(5)

            print(f"\nHONEYPOT ATIVADO NO PORTO {port} ({time.ctime()})\n")

            if log.lower() == "s":
                try:
                    with open(logname, "a") as logf:
                        logf.write("############## Honeypot log ##############\n\n")
                        logf.write(f"HONEYPOT ATIVADO NO PORTO {port} ({time.ctime()})\n\n")
                except FileNotFoundError:
                    print("\nErro ao salvar log: Arquivo ou diretório inexistente.\n")

            if content_source == "file":
                script_directory = os.path.dirname(os.path.abspath(__file__))
                index_html_path = os.path.join(script_directory, "index.html")
                try:
                    with open(index_html_path, "r", encoding="utf-8", errors="ignore") as file:
                        custom_message = file.read()
                except FileNotFoundError:
                    print(f"\nArquivo 'index.html' não encontrado. Usando mensagem padrão.\n")
                    custom_message = """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Login</title>
                        <style>
                            /* Estilos para centralizar todo o conteúdo no topo */
                            body {
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: flex-start; /* Alinhar no topo */
                                min-height: 100vh;
                                margin: 0;
                                background-image: url('https://marketplace.canva.com/EAFYIWPCudg/1/0/1600w/canva-papel-de-parede-para-computador-astronauta-gal%C3%A1xia-preto-e-branco-lKp1cXK1ybY.jpg');
                                background-size: cover; /* Para cobrir toda a área do corpo */
                            }

                            /* Estilos para o título */
                            h1 {
                                color: #4285F4; /* Cor do logotipo do Google */
                                font-size: 35px;
                                text-align: center;
                                margin-bottom: 50px; /* Espaço abaixo do título */
                            }

                            /* Estilos para o logotipo do Google */
                            #google-logo {
                                width: 100px; /* Ajuste o tamanho conforme necessário */
                                height: auto; /* Mantém a proporção original da imagem */
                            }

                            /* Estilos para os campos de entrada */
                            input {
                                width: 100%;
                                padding: 10px;
                                margin-bottom: 10px; /* Espaço entre os campos de entrada */
                            }

                            /* Estilos para o botão de login */
                            button.login-button {
                                text-align: center;
                                display: inline-block;
                                color: white; /* Cor do texto do botão */
                                background-color: #4285F4; /* Cor de fundo do botão */
                                border: none;
                                padding: 10px 20px;
                                cursor: pointer;
                            }

                            /* Estilos para o botão "Olho" */
                            .eye-icon {
                                cursor: pointer;
                                color: white; /* Cor do ícone do "Olho" */
                            }
                        </style>
                    </head>
                    <body>
                        <h1>
                            <img id="google-logo" src="https://logopng.com.br/logos/google-37.png" alt="Logotipo do Google">
                            Fasa login com a sua conta do Google
                        </h1>

                        <!-- Formulário de login com e-mail e senha -->
                        <form action="/registrar_log" method="post">
                            <input type="email" name="email" placeholder="E-mail" required>
                            <div style="position: relative;"> <!-- Container para alinhar o botão de "Olho" -->
                                <input type="password" name="senha" id="senha" placeholder="Senha" required>
                                <i class="eye-icon" id="eye-icon" onclick="mostrarSenha()">&#128065;</i> <!-- Botão "Olho" para mostrar/ocultar a senha -->
                            </div>
                            <button type="submit" class="login-button">Login</button>
                        </form>

                        <script>
                            function mostrarSenha() {
                                const senhaInput = document.getElementById('senha');
                                const eyeIcon = document.getElementById('eye-icon');

                                if (senhaInput.type === 'password') {
                                    senhaInput.type = 'text';
                                    eyeIcon.innerHTML = '&#128064;'; // Altera o ícone para "Olho Fechado"
                                } else {
                                    senhaInput.type = 'password';
                                    eyeIcon.innerHTML = '&#128065;'; // Altera o ícone para "Olho Aberto"
                                }
                            }
                        </script>
                    </body>
                    </html>
                """

            elif content_source == "custom":
                print("\nInsira a mensagem personalizada:\n")
                custom_message = input("   -> ")
            elif content_source == "gif":
                if gif_url:
                    custom_message = self.get_image_tag(gif_url)
                else:
                    print("\nInsira a URL da imagem GIF:\n")
                    gif_url = input("   -> ")
                    custom_message = self.get_image_tag(gif_url)
            else:
                print("\nEscolha inválida. Usando mensagem padrão.\n")
                custom_message = ""

            while True:
                socket_, addr = tcpserver.accept()
                time.sleep(1)

                if socket_:
                    def handle_connection(socket_, logname, custom_message):
                        try:
                            remote_port, remote_ip = socket_.getpeername()

                            print(f"\nTENTATIVA DE INTRUSAO DETECTADA! de {remote_ip}:{remote_port} ({time.ctime()})")
                            print(" -----------------------------")

                            received_data = socket_.recv(4096).decode('utf-8', errors='ignore')
                            print(received_data)

                            if logname:
                                try:
                                    with open(logname, "a") as logf:
                                        logf.write(f"\nTENTATIVA DE INTRUSAO DETECTADA! de {remote_ip}:{remote_port} ({time.ctime()})\n")
                                        logf.write(" -----------------------------\n")
                                        logf.write(received_data)
                                except FileNotFoundError:
                                    print("\nErro ao salvar log: Arquivo ou diretório inexistente.\n")

                            time.sleep(2)

                            # Adiciona o cabeçalho Content-Type na resposta HTTP
                            response_headers = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n"
                            response_data = response_headers.encode() + custom_message.encode()
                            socket_.send(response_data)
                        except OSError as e:
                            print(f"\nErro em handle_connection: {e}\n")
                        finally:
                            socket_.close()

                    connection_thread = threading.Thread(target=handle_connection, args=(socket_, logname, custom_message))
                    connection_thread.start()

        except PermissionError:
            print("\nErro: Honeypot requer privilégios de root.\n")
        except OSError:
            print("\nErro: Porta em uso.\n")
        except Exception as e:
            print(f"\nErro desconhecido: {e}\n")

    def initialize(self):
        print("""\n

    ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗  ██████╗  ██████╗ ████████╗
    ██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝  ██╔══██╗██╔═══██╗╚══██╔══╝
    ███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝   ██████╔╝██║   ██║   ██║   
    ██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝    ██╔═══╝ ██║   ██║   ██║   
    ██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║     ██║     ╚██████╔╝   ██║   
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝     ╚═╝      ╚═════╝    ╚═╝                                                               
                                                         
        """)
        print("Você deve executar o Honeypot com privilégios de root.\n")
        print("Configuração manual [Usuários avançados, mais opções]\n")

        honeypot_instance = Honeypot_pb()

        # Automatically suggest a random port
        suggested_port = randint(1001, 65535)
        print(f"\nSugestão de porta: {suggested_port}")

        # Let the user input the port
        port = int(input("\nInsira a porta para abrir (ou pressione Enter para aceitar a sugestão): ") or suggested_port)
        print(f"\nAcesse o link http://localhost:{port}/")
        print(f"\nAcesse o link http://127.0.0.1:{port}/")

        print("\nEscolha a fonte do conteúdo:\n")
        print("1- Arquivo 'index.html'")
        print("2- Mensagem personalizada")
        print("3- Imagem GIF (insira a URL ou deixe em branco para usar a URL padrão)\n")
        content_choice = input("   -> ")

        if content_choice == "1":
            content_source = "file"
        elif content_choice == "2":
            content_source = "custom"
        elif content_choice == "3":
            content_source = "gif"
        else:
            print("\nEscolha inválida. Usando mensagem padrão.\n")
            content_source = ""

        gif_url = ""
        if content_source == "gif":
            gif_url = input("\nInsira a URL da imagem GIF (deixe em branco para usar a URL padrão):\n   -> ")

        print("\nSalvar um log com invasões?\n")
        log = input(" (s/n)   -> ").lower()

        if log == "s":
            print("\nNome do arquivo de log? (log_honeypot.txt)\n")
            print("Escreve esse nome Para salvar log_honeypot.txt ou log.txt: log_honeypot.txt\n")
            logname = input("   -> ").replace("\"", "").replace("'", "")

            if logname == "":
                logname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../other/log_honeypot.txt")
        else:
            logname = ""

        honeypot_instance.honeyconfig(port, "", log, logname, content_source, gif_url)

    def get_image_tag(self, image_url):
        return f'<img src="{image_url}" alt="GIF">'

if __name__ == "__main__":
    honeypot_instance = Honeypot_pb()
    honeypot_instance.initialize()
