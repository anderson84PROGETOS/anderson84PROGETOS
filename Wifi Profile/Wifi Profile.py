import subprocess

print("""

██╗    ██╗██╗███████╗██╗    ██████╗ ██████╗  ██████╗ ███████╗██╗██╗     ███████╗
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██║██║     ██╔════╝
██║ █╗ ██║██║█████╗  ██║    ██████╔╝██████╔╝██║   ██║█████╗  ██║██║     █████╗  
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║██║     ██╔══╝  
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║╚██████╔╝██║     ██║███████╗███████╗
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝
                                                                                                                                                                    
""")

# Função para obter os perfis de Wi-Fi e suas senhas
def get_wifi_profiles():
    results = []  # Lista para armazenar os resultados

    # Executa o comando netsh para obter a lista de perfis WLAN usando a codificação CP850
    command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True, encoding='cp850')
    
    # Divide a saída do comando em linhas
    lines = command_output.split('\n')

    # Itera sobre as linhas, ignorando as primeiras linhas que não contêm perfis
    for line in lines[9:]:
        # Divide a linha em tokens usando ':' como delimitador
        tokens = line.split(':')

        # Verifica se há pelo menos 2 tokens na linha
        if len(tokens) >= 2:
            # O primeiro token é "Perfil de todos os usuários" e o segundo é o SSID
            profile_name = tokens[0].strip()
            ssid = tokens[1].strip()

            # Verifica se o SSID não está vazio
            if ssid:
                # Adiciona o perfil à lista de resultados
                result_str = f"Perfil na interface Wi-Fi: {ssid}\n"
                results.append(result_str)
                print("\n====================================================\n")
                print(result_str)               

                # Executa o comando para mostrar os detalhes do perfil e a chave (senha)
                try:
                    key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid}" key=clear', shell=True, universal_newlines=True, encoding='cp850')

                    # Encontra a linha que contém "Conteúdo da Chave" (senha)
                    key_content_line = [line for line in key_output.split('\n') if "Conteúdo da Chave" in line]
                    
                    # Se a linha que contém a senha for encontrada, exibe-a
                    if key_content_line:
                        key_content = key_content_line[0].split(":")[1].strip()
                        result_str = f"Senha: {key_content}\n"
                        results.append(result_str)
                        print(result_str)
                    else:
                        result_str = "Senha: Não disponível\n"
                        results.append(result_str)
                        print("Senha: Não disponível")

                except subprocess.CalledProcessError as e:
                    error_str = f"\nErro ao acessar detalhes do perfil (erro: {e.returncode})\n"
                    results.append(error_str)
                    print(error_str)

                # Adiciona uma linha de separação após cada perfil
                results.append("\n====================================================\n\n")

    print("====================================================\n")
    # Pergunta ao usuário se deseja salvar os resultados
    save_option = input("\n\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()

    if save_option == 's':
        filename = input("\nDigite o nome do arquivo (com extensão .txt): ")
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("".join(results))  # Salva os resultados no arquivo
        print(f"\nResultados salvos em: {filename}")

# Executa a função e exibe os resultados
get_wifi_profiles()

# Aguarda o usuário pressionar ENTER para sair
input("\n\nAPERTE ENTER PARA SAIR\n")
