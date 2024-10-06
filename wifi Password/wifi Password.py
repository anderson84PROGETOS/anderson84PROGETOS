import subprocess

print("""
██╗    ██╗██╗███████╗██╗    ██████╗  █████╗ ███████╗███████╗██╗    ██╗ ██████╗ ██████╗ ██████╗ 
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔════╝██╔════╝██║    ██║██╔═══██╗██╔══██╗██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ██████╔╝███████║███████╗███████╗██║ █╗ ██║██║   ██║██████╔╝██║  ██║
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██║╚════██║╚════██║██║███╗██║██║   ██║██╔══██╗██║  ██║
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║███████║███████║╚███╔███╔╝╚██████╔╝██║  ██║██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝ ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ 
""")

# Executa o comando netsh para obter a lista de perfis WLAN
command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True)

# Divide a saída em linhas
lines = command_output.split('\n')

# Lista para armazenar os resultados
results = []

# Itera pelas linhas a partir da décima (pulando as primeiras 9)
for line in lines[9:]:
    # Divide cada linha em tokens usando ':' como delimitador
    tokens = line.split(':')

    # Extrai os dois primeiros tokens
    if len(tokens) >= 2:
        profile_name = tokens[0].strip()
        ssid = tokens[1].strip()

        # Verifica se o SSID não está vazio
        if ssid:
            profile_info = "=========================================\n"
            profile_info += "\nPerfil na interface Wi-Fi\n"
            profile_info += f"\nSSID: {ssid}\n\n"            

            # Executa o comando netsh para exibir a chave do perfil atual
            key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid}" key=clear', shell=True, universal_newlines=True)

            # Exibe o conteúdo filtrado da chave, mantendo "Conteúdo da Chave"
            if key_output:
                # Filtra as linhas relevantes, mantendo a linha com "Conteúdo da Chave"
                key_output_filtered = '\n'.join([line for line in key_output.split('\n') 
                                                  if "Conte£do da Chave" in line])

                # Adiciona a informação da chave de segurança ao resultado final
                profile_info += key_output_filtered.strip()
                results.append(profile_info)  # Adiciona o resultado à lista

# Exibe todos os resultados
for result in results:
    print(result)

print("=========================================")

# Pergunta ao usuário se deseja salvar os resultados
save_option = input("\n\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()

if save_option == 's':
    filename = input("\nDigite o nome do arquivo (com extensão .txt): ")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("\n".join(results))  # Salva os resultados no arquivo
    print(f"\nResultados salvos Em: {filename}")

input("\n\nAPERTE ENTER PARA SAIR\n")
