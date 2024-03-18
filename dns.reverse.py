import subprocess

# Solicita ao usuário que insira o prefixo do IP
prefixo = input("\nDigite o prefixo do endereço IP (ex: 192.168.0): ")

print("")
# Loop através de todos os IPs possíveis na rede
for ip in range(256):
    # Formata o endereço IP
    endereco_ip = f"{prefixo}.{ip}"
    try:
        # Executa o comando 'host' para cada IP na rede e captura a saída
        resultado = subprocess.check_output(["host", endereco_ip], stderr=subprocess.DEVNULL)
        # Decodifica a saída e a verifica se não contém "not found: 3(NXDOMAIN)"
        if b"not found: 3(NXDOMAIN)" not in resultado:
            # Exibe o resultado
            print(resultado.decode().strip())
    except subprocess.CalledProcessError:
        pass

input("\nPressione ENTER Para Sair\n")
