import socket
hostname = input("\033[32m\ninsira o nome do site:\033[m")
# Pesquisa de IP do nome do host
print(f'\033[31m\n{hostname} Endereço IP:\033[m{socket.gethostbyname(hostname)}')
input("\033[32m\nAPERTE ENTER PRA SAIR")
