import subprocess
import time  # Importa a biblioteca time

print("""

██╗    ██╗██╗███████╗██╗    ███████╗███████╗███╗   ██╗██╗  ██╗ █████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝████╗  ██║██║  ██║██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ███████╗█████╗  ██╔██╗ ██║███████║███████║
██║███╗██║██║██╔══╝  ██║    ╚════██║██╔══╝  ██║╚██╗██║██╔══██║██╔══██║
╚███╔███╔╝██║██║     ██║    ███████║███████╗██║ ╚████║██║  ██║██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝
                                                                     
""")

# Lista para armazenar os resultados
results = []

# Executa o comando netsh para obter a lista de perfis WLAN com codificação CP850
command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True, encoding='cp850')

# Divide a saída em linhas
lines = command_output.split('\n')

# Itera sobre as linhas, ignorando as primeiras 9 linhas
for line in lines[9:]:
    # Divide cada linha em tokens usando ':' como delimitador
    tokens = line.split(':')

    # Extrai os dois primeiros tokens
    if len(tokens) >= 2:
        profile_name = tokens[0].strip()
        ssid = tokens[1].strip()

        # Verifica se o SSID não está vazio
        if ssid:
            print("\n=======================")            
            print(f"\nSSID: {ssid}")            
            results.append(f"\nSSID: {ssid}")  # Adiciona o SSID aos resultados

            # Executa o comando netsh para exibir a chave do perfil atual com codificação CP850
            key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid}" key=clear', shell=True, universal_newlines=True, encoding='cp850')

            # Procura e imprime o conteúdo da chave (em português "Conteúdo da Chave")
            key_content_line = [line for line in key_output.split('\n') if "Conteúdo da Chave" in line]
            if key_content_line:
                key_content = key_content_line[0].split(":")[1].strip()
                print(f"Senha: {key_content}")
                results.append(f"Senha: {key_content}")  # Adiciona a senha aos resultados
            else:
                print(f"Senha: Não disponível")
                results.append("Senha: Não disponível")  # Adiciona "Senha: Não disponível" aos resultados

print("=======================")

# Exibe a mensagem antes de salvar os resultados
results.insert(0, "Perfil na interface Wi-Fi")  # Insere no início da lista

# Nome do arquivo para salvar automaticamente
filename = 'Wifi_SSID_ Senha.txt'

# Salva os resultados no arquivo
with open(filename, 'w', encoding='utf-8') as file:
    file.write("\n".join(results))  # Salva os resultados no arquivo

print(f"\nResultados salvos em: {filename}")

# Aguarda 5 segundos antes de fechar o script
print("\nAguarda 5 segundos antes de fechar o script\n")
time.sleep(5)

