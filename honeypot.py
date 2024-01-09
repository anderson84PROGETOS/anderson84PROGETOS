import socket
import time
import os
import threading
from random import randint

class Honeypot_pb:
    def initialize(self):
        print("\n// Honeypot //\n")
        print("Você deve executar o Honeypot com privilégios de root.\n")
        print("Selecione a opção.\n")
        print("1- Configuração automática rápida")
        print("2- Configuração manual [Usuários avançados, mais opções]\n")
        configuration = input("   -> ")

        print("\nAcesse o link http://localhost/")
        print("Acesse o link http://127.0.0.1/")

        def honeyconfig(port, message, sound, log, logname, content_source):
            try:
                tcpserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcpserver.bind(("0.0.0.0", port))
                tcpserver.listen(5)

                print(f"\nHONEYPOT ATIVADO NO PORTO {port} ({time.ctime()})\n")

                if log.lower() == "y":
                    try:
                        with open(logname, "a") as logf:
                            logf.write("############## Honeypot log ##############\n\n")
                            logf.write(f"HONEYPOT ATIVADO NO PORTO {port} ({time.ctime()})\n\n")
                    except FileNotFoundError:
                        print("\nErro ao salvar log: Arquivo ou diretório inexistente.\n")

                if content_source == "file":
                    try:
                        with open("index.html", "r") as file:
                            custom_message = file.read()
                    except FileNotFoundError:
                        print("\nErro: Arquivo 'index.html' não encontrado.\n")
                        return
                elif content_source == "custom":
                    print("\nInsira a mensagem personalizada:\n")
                    custom_message = input("   -> ")
                elif content_source == "gif":
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
                        def handle_connection(socket_, logname, sound, custom_message):
                            try:
                                remote_port, remote_ip = socket_.getpeername()
                                print(f"\nTENTATIVA DE INTRUSAO DETECTADA! de {remote_ip}:{remote_port} ({time.ctime()})")
                                print(" -----------------------------")

                                received_data = socket_.recv(1000).decode()
                                print(received_data)

                                if sound.lower() == "y":
                                    print("\a\a\a")

                                if log.lower() == "y":
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

                        connection_thread = threading.Thread(target=handle_connection, args=(socket_, logname, sound, custom_message))
                        connection_thread.start()

            except PermissionError:
                print("\nErro: Honeypot requer privilégios de root.\n")
            except OSError:
                print("\nErro: Porta em uso.\n")
            except Exception as e:
                print(f"\nErro desconhecido: {e}\n")

        if configuration == "1":
            access = str(randint(0, 2))
            honeyconfig(80, f"<HEAD>\n<TITLE>Access denied</TITLE>\n</HEAD>\n<H2>Access denied</H2>\n"
                            f"<H3>HTTP Referrer login failed</H3>\n<H3>IP Address login failed</H3>\n"
                            f"<P>\n{time.ctime()}\n</P>", "N", "N", "", "")
        elif configuration == "2":
            print("\nInsira a porta para abrir.\n")
            port = int(input("   -> "))
            print("\nEscolha a fonte do conteúdo:\n")
            print("1- Arquivo 'index.html'")
            print("2- Mensagem personalizada")
            print("3- Imagem GIF (insira a URL)")
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

            print("\nSalvar um log com invasões?\n")
            log = input(" (y/n)   -> ").lower()

            if log == "y":
                print("\nNome do arquivo de log? (incremental)\n")
                print("Default: */Honeypot/other/log_honeypot.txt\n")
                logname = input("   -> ").replace("\"", "").replace("'", "")

                if logname == "":
                    logname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../other/log_honeypot.txt")
            else:
                logname = ""

            print("\nAtivar som de beep() em caso de intrusão?\n")
            sound = input(" (y/n)   -> ").lower()
            honeyconfig(port, "", sound, log, logname, content_source)
        else:
            print("\nOpção inválida.\n")

    def get_image_tag(self, image_url):
        return f'<img src="{image_url}" alt="GIF">'

if __name__ == "__main__":
    honeypot_instance = Honeypot_pb()
    honeypot_instance.initialize()
