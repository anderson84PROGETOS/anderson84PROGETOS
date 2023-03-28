import socket

# Cria o socket do servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define o endereço e porta do servidor
endereco_servidor = ('', 5000)

# Faz o bind do socket com o endereço do servidor
servidor.bind(endereco_servidor)

# Coloca o socket em modo de escuta
servidor.listen()

print('Servidor esperando conexão...')

# Aguarda a conexão com um cliente
cliente, endereco_cliente = servidor.accept()

print('Conexão estabelecida com', endereco_cliente)

# Loop para enviar e receber mensagens
while True:
    # Recebe a mensagem do cliente
    mensagem_cliente = cliente.recv(1024).decode()

    # Imprime a mensagem recebida
    print('Cliente:', mensagem_cliente)

    # Envia uma mensagem de volta para o cliente
    mensagem_servidor = input('\nServidor Digite algo: ')
    cliente.send(mensagem_servidor.encode())

# Fecha a conexão com o cliente e o socket do servidor
cliente.close()
servidor.close()

