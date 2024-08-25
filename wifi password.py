import subprocess

print("""

██╗    ██╗██╗███████╗██╗    ██████╗  █████╗ ███████╗███████╗██╗    ██╗ ██████╗ ██████╗ ██████╗ 
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔════╝██╔════╝██║    ██║██╔═══██╗██╔══██╗██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ██████╔╝███████║███████╗███████╗██║ █╗ ██║██║   ██║██████╔╝██║  ██║
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██║╚════██║╚════██║██║███╗██║██║   ██║██╔══██╗██║  ██║
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║███████║███████║╚███╔███╔╝╚██████╔╝██║  ██║██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝ ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ 
                                                                                              
""")

# Run the netsh command to get the list of WLAN profiles
command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True)

# Split the output into lines
lines = command_output.split('\n')

# Mostrar as redes sem fio disponíveis
print("\nRedes Sem Fio Disponíveis\n")
ssids = []
for line in lines[9:]:
    tokens = line.split(':')
    if len(tokens) >= 2:
        ssid = tokens[1].strip()
        if ssid:
            ssids.append(ssid)
            print(f"{ssid}")

# Solicitar ao usuário que insira o SSID da rede desejada
ssid_input = input("\n\nDigite o nome da rede (SSID): ")
print("\n")

# Verificar se o SSID inserido está na lista
if ssid_input in ssids:
    # Executar o comando netsh para mostrar a chave para o perfil atual
    key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid_input}" key=clear', shell=True, universal_newlines=True)
    
    # Exibe toda a saída para que possamos verificar
    print(key_output)  
    
    # Encontrar e imprimir o conteúdo da chave (senha)
    key_content_line = [line for line in key_output.split('\n') if "Conteúdo da Chave" in line]
    if key_content_line:
        key_content = key_content_line[0].split(":")[1].strip()
        print("\n")
        print(f"SSID: {ssid_input}")
        print(f"Senha: {key_content}")
    
else:
    print(f"Não foi possível Encontrar a Rede: {ssid_input}")

input("\n\nAPERTE ENTER PARA SAIR\n")
