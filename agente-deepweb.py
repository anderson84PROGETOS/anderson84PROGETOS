import subprocess

# Obter a entrada do usuário
url = input("\nDigite a URL Nome do site Para Consultar: ")

# Comando para executar com subprocess
cmd = "curl -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36' -L -s {0} | grep -Poi 'http\\K.*?(?=\")' | awk -F/ '{{print $3}}' | sort -n | uniq".format(url)

# Executar o comando e obter a saída
output = subprocess.check_output(cmd, shell=True, universal_newlines=True)

# Imprimir a saída
print(output)

input("\nConsulta Enserada Aperte Enter Sair !\n")
