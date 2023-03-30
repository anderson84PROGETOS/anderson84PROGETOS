import subprocess

# Solicita que o usuário digite o nome do website que deseja consultar
website = input("\nDigite o nome do website que deseja consultar: ")

# Executa o comando 'host -t ns' no terminal, passando o nome do website como argumento, e captura a saída
saida_ns = subprocess.check_output(["host", "-t", "ns", website]).decode()

# Imprime a saída na tela
print("Servidores DNS para {}: ".format(website))
print(saida_ns)

# Extrai a lista de servidores DNS da saída do comando 'host -t ns' e exibe para o usuário escolher um servidor DNS
servidores_dns = [linha.split()[-1] for linha in saida_ns.split("\n") if "NS" in linha]
print("Selecione um servidor DNS:")
for i, servidor in enumerate(servidores_dns):
    print("{}) {}".format(i+1, servidor))

# Solicita que o usuário selecione um servidor DNS da lista
selecao = input("\nDigite o número correspondente ao servidor DNS que deseja usar ou o nome do servidor DNS completo: ")
if selecao.isdigit() and int(selecao) <= len(servidores_dns):
    dns_selecionado = servidores_dns[int(selecao)-1]
else:
    dns_selecionado = selecao

# Executa o comando 'host -l' no terminal, passando o nome do website e o servidor DNS selecionado como argumentos, e captura a saída
try:
    saida_l = subprocess.check_output(["host", "-l", website, dns_selecionado]).decode()
    # Imprime a saída na tela
    print(saida_l)
except subprocess.CalledProcessError as e:
    print("\nNão foi possível consultar o website {} usando o servidor DNS {}. Erro: {}".format(website, dns_selecionado, e))
    
input("\nconsultar o website terminada Fim [ENTER]")    
