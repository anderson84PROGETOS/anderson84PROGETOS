import socket

print("""

  ██╗  ██╗███████╗ █████╗ ██████╗     ██████╗ ███████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗
  ██║  ██║██╔════╝██╔══██╗██╔══██╗    ██╔══██╗██╔════╝██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
  ███████║█████╗  ███████║██║  ██║    ██████╔╝█████╗  ██║   ██║██║   ██║█████╗  ███████╗   ██║   
  ██╔══██║██╔══╝  ██╔══██║██║  ██║    ██╔══██╗██╔══╝  ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   
  ██║  ██║███████╗██║  ██║██████╔╝    ██║  ██║███████╗╚██████╔╝╚██████╔╝███████╗███████║   ██║   
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝                            
""") 

# Função para enviar solicitação HEAD
def send_head_request(site, porta):
    try:
        with socket.create_connection((site, porta), timeout=5) as conn:
            conn.sendall(b"HEAD / HTTP/1.1\r\nHost: " + site.encode() + b"\r\nConnection: close\r\n\r\n")
            response = conn.recv(4096).decode()
            print(f"\n🟢 Resposta da porta {porta}\n")
            print(response)
    except Exception as e:
        print(f"\nAcesso Proibido:403 Forbidden 🔴 acessar {porta}: {e}")

if __name__ == "__main__":
    # Solicita ao usuário o nome do site
    site = input("\nDigite o nome do WebSite: ")

    # Verifica se o nome do site foi fornecido
    if not site:
        print("\nVocê não forneceu um nome de site válido. Saindo")
        exit(1)

    # Solicita ao usuário a escolha da porta
    print("\nEscolha uma das seguintes portas: 21, 22,23, ou uma porta só 80 ")
    porta_input = input("\nDigite os números das Portas Escolhidas: ")

    # Separar as portas fornecidas pelo usuário
    portas = [int(porta.strip()) for porta in porta_input.split(",")]

    # Verifica se os números das portas são válidos
    if any(porta < 1 or porta > 65535 for porta in portas):
        print("\nNúmero de porta(s) inválido(s). Saindo")
        exit(1)

    print(f"\nEnviando solicitação 🟢 HEAD 🟢 para {site} nas portas {portas}\n")
    for porta in portas:
        send_head_request(site, porta)

    input("\n🎯 Pressione Enter para sair 🎯 \n")
