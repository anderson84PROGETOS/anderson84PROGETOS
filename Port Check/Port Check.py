import socket
from datetime import datetime
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner ASCII
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗  ██████╗ ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║██████╔╝   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔═══╝ ██║   ██║██╔══██╗   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██║     ╚██████╔╝██║  ██║   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

""")

# Verifica se uma porta está aberta
def verificar_porta(ip, porta):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        resultado = sock.connect_ex((ip, porta))
        sock.close()
        return resultado == 0
    except:
        return False

# Tenta obter o nome do serviço padrão da porta (tcp)
def nome_servico(porta):
    try:
        return socket.getservbyport(porta, 'tcp')
    except:
        return "tcpwrapped"

# Gera arquivo de relatório .txt
def gerar_relatorio(ip, resultados, nome_arquivo):    
    agora = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"🔍 Relatório de Verificação de Portas - IP: {ip}\n")
        arquivo.write(f"\nData/Hora: {agora}\n\n")
        for linha in resultados:
            arquivo.write(linha + "\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n📝 Relatório salvo como: {nome_arquivo}")

# Interpreta a entrada de portas (ex: "21,22, ou 80-85")
def parse_portas(entrada):
    portas = set()
    partes = entrada.split(",")
    for parte in partes:
        parte = parte.strip()
        if "-" in parte:
            inicio, fim = parte.split("-")
            portas.update(range(int(inicio), int(fim)+1))
        else:
            portas.add(int(parte))
    return sorted(portas)

# Entrada do usuário
ip_publico = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o IP ou nome do website a ser verificado: ").strip()
entrada_portas = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite as portas (ex: 23,80,443,5000 ou 80-5000): ").strip()
lista_portas = parse_portas(entrada_portas)

# Verificando as portas
print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n🔍 Verificando portas em: {ip_publico}\n")
resultados = []
for porta in lista_portas:
    if verificar_porta(ip_publico, porta):
        servico = nome_servico(porta)
        resultado = f"{porta}/tcp   open  {servico}"
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + resultado)
        resultados.append(resultado)
    else:
        resultado = f"{porta}/tcp   closed"
        print(Fore.LIGHTRED_EX + Style.BRIGHT + resultado)
        resultados.append(resultado)

# Pergunta se deseja salvar
salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT +"\n\nDeseja salvar os resultados em um arquivo (s/n): ").strip().lower()
if salvar == "s":
    nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo: ").strip()
    if not nome_arquivo.endswith(".txt"):
        nome_arquivo += ".txt"
    gerar_relatorio(ip_publico, resultados, nome_arquivo)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
