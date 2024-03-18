import socket

# Solicita ao usuário que insira o prefixo do IP
prefixo = input("\nDigite o prefixo do endereço IP (ex: 192.168.0): ")

print("")
# Loop através de todos os IPs possíveis na rede
for ip in range(256):
    # Formata o endereço IP
    endereco_ip = f"{prefixo}.{ip}"
    try:
        # Realiza a consulta DNS reversa para o endereço IP
        host = socket.gethostbyaddr(endereco_ip)
        # Exibe o resultado
        print(f"\nEndereço IP: {endereco_ip}, Hostname: {host[0]}")
    except socket.herror:
        pass
    
input("\nPressione ENTER Para Sair\n")
