import socket

# Define o endereço IP do host a ser verificado
host = input("\nDigite o endereço IP do host que deseja verificar: ")

# Define o intervalo de portas a serem verificadas com base na entrada do usuário
inicio = int(input("\nDigite o número da porta inicial: "))
fim = int(input("\nDigite o número da porta final: "))
portas = range(inicio, fim+1)
print("\n   ↓↓ Escaneando ↓↓\n")
# Loop através de cada porta e verifica se ela está aberta
for porta in portas:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    resultado = sock.connect_ex((host, porta))
    if resultado == 0:
        print(f"A porta {porta} está aberta")
    sock.close()

input("\n fim do escaneamento \n")
