import socket

# Cria o socket do cliente
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define o endereço e porta do servidor
endereco_servidor = ('localhost', 5000)

# Conecta com o servidor
cliente.connect(endereco_servidor)

# Loop para enviar e receber mensagens
while True:
    # Envia uma mensagem para o servidor
    mensagem_cliente = input('\nCliente Digite algo: ')
    cliente.send(mensagem_cliente.encode())

    # Recebe a mensagem do servidor
    mensagem_servidor = cliente.recv(1024).decode()

    # Imprime a mensagem recebida
    print('Servidor:', mensagem_servidor)

# Fecha a conexão com o servidor e o socket do cliente
cliente.close()
