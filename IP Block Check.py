import subprocess
import requests
from bs4 import BeautifulSoup
import socket
import ipaddress

print("""

██╗██████╗     ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██║██╔══██╗    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██║██████╔╝    ██████╔╝██║     ██║   ██║██║     █████╔╝     ██║     ███████║█████╗  ██║     █████╔╝ 
██║██╔═══╝     ██╔══██╗██║     ██║   ██║██║     ██╔═██╗     ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██║██║         ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═╝╚═╝         ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
                                                                                                                                                                                                                                                                                                          
""")

def obter_informacoes_whois_com(endereco):
    url = f"https://www.whois.com/whois/{endereco}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        whois_section = soup.find("pre", class_="df-raw")
        
        if whois_section:
            print("\nWHOIS para:  {}\n".format(endereco))
            print(whois_section.get_text())
        else:
            print("Não foi possível encontrar informações WHOIS para este domínio.")
    else:
        print("Erro ao obter informações WHOIS.")

def obter_informacoes_whois_br(endereco):
    servidor_whois = 'whois.registro.br'
    porta = 43
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((servidor_whois, porta))
    sock.sendall((endereco + "\r\n").encode())
    resposta_whois = b''
    while True:
        dados = sock.recv(1024)
        if not dados:
            break
        resposta_whois += dados
    sock.close()
    codecs = ['utf-8', 'iso-8859-1', 'latin-1']
    for codec in codecs:
        try:
            decoded_response = resposta_whois.decode(codec)
            break
        except UnicodeDecodeError:
            pass
    else:
        print("Não foi possível decodificar a resposta WHOIS.")
        return
    print(decoded_response)

# Solicita ao usuário o nome do website
website = input("Digite o nome do website: ")

# Verifica se o argumento foi fornecido
if not website:
    print("\nO nome do website não foi fornecido.")
    exit(1)

# Realiza a consulta MX
print("\nConsultando registros MX para:", website)
print("")
subprocess.run(["nslookup", "-query=mx", website])

# Solicita ao usuário o nome do Post
post = input("\nDigite o Post (exemplo: post02.Exemplo.com): ")

if post:
    # Realiza a consulta MX com o nome do Post
    print("")
    print("\nConsultando registros MX para", post)
    print("")
    subprocess.run(["nslookup", "-query=mx", post])
    print("")
    print("Ping para", post)
    print("")
    subprocess.run(["ping", "-4", "-n", "1", post])

# Realiza o ping para o website original
print("")
print("Ping para", website)
print("")
subprocess.run(["ping", "-4", "-n", "1", website])

# Main menu
print("\n\n\nSelecione uma opção\n")
print("\n1. Obter informações WHOIS para um website .BR")
print("\n2. Obter informações WHOIS para um website .COM")
opcao = input("\nOpção: ")
print("\n")

if opcao == "1":
    endereco = input("Digite o IP do website (.BR): ")
    obter_informacoes_whois_br(endereco)
elif opcao == "2":
    endereco = input("Digite o IP do website (.COM): ")
    obter_informacoes_whois_com(endereco)
else:
    print("Opção inválida.")


# nmap Bloco de IP
def list_subnet_ips(subnet):
    try:
        # Cria um objeto de sub-rede com base na string fornecida
        network = ipaddress.ip_network(subnet)
    except ValueError as e:
        print("Erro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20")
        return

    print("\nEndereços IP disponíveis na sub-rede\n")
    ips = []  # Lista para armazenar os IPs

    # Percorre todos os endereços IP na sub-rede e os imprime
    for ip in network.hosts():
        ips.append(str(ip))
        print(ip)

    # Pergunta ao usuário se deseja salvar os IPs em um arquivo
    save = input("\nDeseja salvar os IPs em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input("\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(f"\nOs IPs foram salvos com sucesso no arquivo '{filename}'.")
        except Exception as e:
            print(f"Erro ao salvar os IPs no arquivo: {e}")

# Solicita ao usuário que insira o bloco de IP
subnet = input("\n\n\nDigite o bloco de IP (exemplo: 200.196.144.0/20): ")
list_subnet_ips(subnet)    

input("\n\n🎯 Pressione Enter para sair 🎯\n")
