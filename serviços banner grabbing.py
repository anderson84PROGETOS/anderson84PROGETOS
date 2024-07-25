import requests
import socket
import time
import sys

print("""
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
| S | E | R | V | I | Ç | O | S |   | B | A | N | N | E | R |   | G | R | A | B | B | I | N | G |
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
""")

# Exibe uma lista padrão de portas e serviços
print("""
Portas comuns e serviços

21/tcp   open  ftp
22/tcp   open  ssh
23/tcp   open  telnet
25/tcp   open  smtp
53/tcp   open  domain
80/tcp   open  http
111/tcp  open  rpcbind
139/tcp  open  netbios-ssn
445/tcp  open  microsoft-ds
512/tcp  open  exec
513/tcp  open  login
514/tcp  open  shell
1099/tcp open  rmiregistry
1524/tcp open  ingreslock
2049/tcp open  nfs
2121/tcp open  ccproxy-ftp
3306/tcp open  mysql
5432/tcp open  postgresql
5900/tcp open  vnc
6000/tcp open  X11
6667/tcp open  irc
8009/tcp open  ajp13
8180/tcp open  unknown

""")

# Função para obter cabeçalhos HTTP
def obter_cabecalhos(url, cabecalho):
    try:
        resposta = requests.get(f'http://{url}', headers=cabecalho)
        return resposta.headers
    except requests.RequestException as e:
        print(f'\nErro ao tentar obter cabeçalhos: {e}')
        return None

# Função para obter banner de um serviço em uma porta específica
def obter_banner(ip, porta):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((ip, porta))
            s.send(b'HEAD / HTTP/1.0\r\n\r\n')
            resposta = s.recv(4096)  # Aumenta o tamanho do buffer para garantir que receba o banner completo
            
            try:
                # Tenta decodificar com UTF-8, se falhar, apenas exibe os bytes brutos
                return resposta.decode('latin-1', errors='ignore')
            except UnicodeDecodeError:
                return resposta.decode('latin-1', errors='ignore')  # Tenta outra codificação
    except Exception as e:
        return None

# Função para mostrar mensagem de progresso
def mostrar_mensagem(progresso):
    sys.stdout.write(f"\r{progresso}")
    sys.stdout.flush()
    time.sleep(0.1)  # Pequeno atraso para não sobrecarregar a saída

# Função para converter intervalo de portas em uma lista de portas
def criar_lista_de_portas(intervalo):
    portas = []
    try:
        if '-' in intervalo:
            inicio, fim = map(int, intervalo.split('-'))
            portas = list(range(inicio, fim + 1))
        else:
            portas = [int(intervalo)]
    except ValueError:
        print("\n[!] Intervalo inválido. Use o formato 'início-fim' ou um único número.")
    return portas

# Entrada do usuário
url = input('\n[+] Digite a URL ou IP do site: ')
# Remover esquema HTTP/HTTPS do URL para capturar apenas o hostname ou IP
url = url.replace('http://', '').replace('https://', '').split('/')[0]

# Solicitar intervalo de portas
intervalo_portas = input('\n\n[+] Digite o intervalo de portas (ex: 21-8180) ou uma única porta (ex: 80): ')
portas = criar_lista_de_portas(intervalo_portas)

# Define o cabeçalho padrão para a requisição
cabecalho = {'User-Agent': 'Mozilla/5.0'}

def iterar_enderecos():
    inicio = time.time()
    print('\n\nEscaneando, Aguarde....\n')
    
    # Obter banner para cada porta especificada
    banners = []
    portas_abertas = []
    for porta in portas:
        mostrar_mensagem(f"Escaneando porta: {porta}")
        banner = obter_banner(url, porta)
        if banner:
            banners.append((porta, banner))
            portas_abertas.append(porta)  # Adiciona a porta à lista de portas abertas
            
    fim = time.time()
    
    # Exibir portas abertas
    if portas_abertas:
        print()
        print(f"\n[+] Portas abertas: {', '.join(map(str, portas_abertas))}")
        print("\n", '*' * 55, '\n')
    else:
        print("\n\n[!] Nenhuma porta aberta encontrada.")
        
    # Exibir banners encontrados
    if banners:
        for porta, banner in banners:
            print("[+] Porta : {} | Banner : {}\n".format(porta, banner))
    else:
        print("\n[!] Nenhum banner encontrado.")
    
    print("\n", '*' * 55, '\n')
    print("[+] Varredura Iniciada    Em: ", time.ctime(inicio))
    print("[+] Varredura Finalizada  Em: ", time.ctime(fim))
    print('[+] Tempo Total Decorrido Em: ', end=' ')
    tempo_decorrido = (fim - inicio) / 60  # Converter para minutos
    print(f"{tempo_decorrido:.2f} minutos")
    print("\n", '*' * 55, '\n')

# Executa a função de varredura
iterar_enderecos()
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")    
