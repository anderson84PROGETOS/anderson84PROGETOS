import subprocess
import requests

print("""


██████╗ ███╗   ██╗███████╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███████╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗       ██║   ██████╔╝███████║██╔██╗ ██║███████╗█████╗  █████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║       ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██╔══╝  ██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║       ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║     ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                                 
                                                     
""")

# Solicita ao usuário que insira o nome do site
site = input("\nDigite o nome do site: ")

print("\n")

# Executa o comando 'nslookup' e captura a saída
output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)

# Divide a saída em linhas e extrai os servidores DNS
lines = output_dns.stdout.splitlines()
servers = [line.split()[-1] for line in lines if 'nameserver' in line]

# Lista para armazenar a saída de cada consulta do nslookup
output_list_dns = []

# Itera sobre cada servidor DNS e executa o comando 'nslookup -type=any'
for server in servers:
    output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
    output_list_dns.append(output.stdout)

# Imprime a saída do nslookup na tela
for output in output_list_dns:
    print(output)

# Cabeçalhos com os agentes do usuário
headers = [
    'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
]

# Lista para armazenar a saída dos cabeçalhos HTTP
output_list_headers = []

# Fazendo solicitações HTTP com os agentes do usuário e armazenando os cabeçalhos
for agent in headers:
    response = requests.get("http://" + site, headers={'User-Agent': agent})
    output_list_headers.append(response.headers)

# Imprime os cabeçalhos HTTP na tela
for headers in output_list_headers:
    print("\n↓ Cabeçalhos HTTP ↓\n")
    for header, value in headers.items():
        print(f"{header}: {value}")
    print("\n")

# Verifica se o usuário deseja salvar em um arquivo
save_option = input("\nDeseja salvar a saída em um arquivo? (s/n): ")

if save_option.lower() == 's':
    # Solicita ao usuário o nome do arquivo
    file_name = input("\nDigite o nome do arquivo para salvar a saída: ")
    
    # Salva a saída e os cabeçalhos no arquivo
    with open(file_name, 'w') as file:
        file.write("Saída do nslookup:\n\n")
        for output in output_list_dns:
            file.write(output)
        file.write("\n\nCabeçalhos HTTP:\n\n")
        for headers in output_list_headers:
            for header, value in headers.items():
                file.write(f"{header}: {value}\n")
            file.write("\n")
    print(f"\nA saída foi salva em: {file_name}")

input("\n\nPressione ENTER para sair\n")
