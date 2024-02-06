import socket

# Função para enviar solicitação HEAD
def send_head_request(site, porta):
    try:
        with socket.create_connection((site, porta), timeout=5) as conn:
            conn.sendall(b"HEAD / HTTP/1.1\r\nHost: " + site.encode() + b"\r\nConnection: close\r\n\r\n")
            response = conn.recv(4096).decode()
            print(f"\n🟢 Resposta da porta {porta}\n")
            print(response)
    except Exception as e:
        print(f"\n🔴 Acesso Proibido: 403 Forbidden 🔴   ao acessar {porta}: {e}")

if __name__ == "__main__":
    # Solicita ao usuário o nome do site
    site = input("\nDigite o nome do site: ")

    # Verifica se o nome do site foi fornecido
    if not site:
        print("\nVocê não forneceu um nome de site válido. Saindo")
        exit(1)

    portas = [80, 443]

    # Loop pelas portas e envia a solicitação HEAD para cada uma
    for porta in portas:
        print(f"\nEnviando solicitação 🟢 HEAD 🟢 para {site} na porta {porta}\n")
        send_head_request(site, porta)

    input("\n🎯 Pressione Enter para sair 🎯 \n")

