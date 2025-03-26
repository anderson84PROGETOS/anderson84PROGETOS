import subprocess
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """   

██╗    ██╗██╗███████╗██╗    ██████╗  █████╗ ███████╗███████╗██╗    ██╗ ██████╗ ██████╗ ██████╗ 
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔════╝██╔════╝██║    ██║██╔═══██╗██╔══██╗██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ██████╔╝███████║███████╗███████╗██║ █╗ ██║██║   ██║██████╔╝██║  ██║
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██║╚════██║╚════██║██║███╗██║██║   ██║██╔══██╗██║  ██║
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║███████║███████║╚███╔███╔╝╚██████╔╝██║  ██║██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝ ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ 
                                                                                               
                                                                                                                                                                                                                                                                                                                       
""")

# Lista para armazenar os resultados
wifi_list = []

# Executa o comando para listar perfis Wi-Fi
command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True, encoding='cp850')

# Busca linhas contendo "Todos os Perfis de Usuário" ou "All User Profile"
lines = command_output.split('\n')
for line in lines:
    if "Todos os Perfis de Usuário" in line or "All User Profile" in line:
        ssid = line.split(":")[1].strip()
        
        if ssid:
            # Obtém a senha do perfil Wi-Fi
            key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid}" key=clear', shell=True, universal_newlines=True, encoding='cp850')
            
            key_content_line = [l for l in key_output.split('\n') if "Conteúdo da Chave" in l or "Key Content" in l]
            if key_content_line:
                key_content = key_content_line[0].split(":")[1].strip()
                wifi_list.append((ssid, key_content))
            else:
                wifi_list.append((ssid, "Não disponível"))

# Nome do arquivo para salvar
filename = 'Wifi_Senha.txt'

# Formata os resultados para salvar no arquivo
with open(filename, 'w', encoding='utf-8') as file:
    file.write("Nome da Rede Wi-Fi             | Senha\n")
    file.write("-" * 50 + "\n")
    for wifi in wifi_list:
        file.write(f"{wifi[0]:<30} | {wifi[1]}\n")
    file.write("-" * 50 + "\n")

# Exibe os resultados formatados no console

print(Fore.LIGHTYELLOW_EX + f"{'                           Nome da Rede Wi-Fi':<57} | {'Senha'}")
print(Fore.LIGHTYELLOW_EX + "                           ===============================================")
for wifi in wifi_list:
    print(Fore.LIGHTGREEN_EX + f"                           {wifi[0]:<30} | {wifi[1]}")
print(Fore.LIGHTYELLOW_EX + "                           ================================================")

# mostrar o arquivo salvo
print(Fore.LIGHTYELLOW_EX + f"\n\n                              Resultados salvos em: {filename}")

# sair do programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n                                   PRESSIONE ENTER PARA SAIR ")
