import subprocess
import re
from mac_vendor_lookup import MacLookup
from colorama import init, Fore, Style

# Inicializa colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗███████╗██╗    ██████╗ ██████╗  ██████╗ ███████╗██╗██╗     ███████╗███████╗
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██║██║     ██╔════╝██╔════╝
██║ █╗ ██║██║█████╗  ██║    ██████╔╝██████╔╝██║   ██║█████╗  ██║██║     █████╗  ███████╗
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║██║     ██╔══╝  ╚════██║
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║╚██████╔╝██║     ██║███████╗███████╗███████║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝                                                                                                                                                                                                                                                                                                 
""")

# Função para escanear redes Wi-Fi no Windows
def scan_wifi_windows():
    padrao_ssid = re.compile(r"SSID \d+ : (.+)")
    padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)")
    padrao_sinal = re.compile(r"Sinal\s+: (\d+)%")
    padrao_canal = re.compile(r"Canal\s+: (\d+)")
    padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)")
    redes_encontradas = {}

    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
        redes = result.split("\n\n")

        for rede in redes:
            ssid = padrao_ssid.search(rede)
            bssid = padrao_bssid.search(rede)
            sinal = padrao_sinal.search(rede)
            canal = padrao_canal.search(rede)
            autenticacao = padrao_autenticacao.search(rede)

            if ssid and bssid:
                mac_address = bssid.group(1)
                if mac_address not in redes_encontradas:
                    try:
                        fabricante = MacLookup().lookup(mac_address)
                    except:
                        fabricante = "Desconhecido"

                    sinal_status = "Fraco" if int(sinal.group(1)) < 40 else "Médio" if int(sinal.group(1)) < 70 else "Forte"
                    seguranca = autenticacao.group(1) if autenticacao else "Desconhecido"
                    redes_encontradas[mac_address] = (ssid.group(1), canal.group(1), fabricante, sinal.group(1), sinal_status, seguranca)
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao executar netsh: {e}")    
    return redes_encontradas

# Função para exibir resultados da varredura Wi-Fi
def mostrar_resultados_wifi():
    redes_netsh = scan_wifi_windows()
    resultados_wifi = []  # Lista para armazenar resultados da varredura
    resultados_wifi.append("=== Redes Wi-Fi detectadas (NETSH) ===\n")
    resultados_wifi.append("SSID                         BSSID                     Canal    Fabricante                               Sinal         Segurança")
    resultados_wifi.append("=" * 134)
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + resultados_wifi[0])
    print(resultados_wifi[1])
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + resultados_wifi[2])
    for bssid, (ssid, canal, fabricante, sinal, sinal_status, seguranca) in redes_netsh.items():
        linha = f"{ssid:<28} {bssid:<25} {canal:<8} {fabricante:<40} {sinal}% ({sinal_status:<5})    {seguranca}\n"
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + linha)
        resultados_wifi.append(linha)
    return resultados_wifi

# Função para buscar senhas salvas
def mostrar_senhas_salvas():
    results = []
    try:
        command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True)
        lines = command_output.split('\n')
        for line in lines[9:]:
            tokens = line.split(':')
            if len(tokens) >= 2:
                profile_name = tokens[1].strip()
                if profile_name:
                    result = subprocess.check_output(f'netsh wlan show profiles "{profile_name}" key=clear', shell=True, universal_newlines=True)
                    senha = ''
                    for r_line in result.split('\n'):
                        if "Conteúdo da Chave" in r_line or "Key Content" in r_line:
                            senha = r_line.strip()
                    perfil_info = f"SSID: {profile_name}\n{senha}\n{'='*40}"
                    results.append(perfil_info)
    except Exception as e:
        print(Fore.RED + f"Erro ao buscar perfis: {e}")
        results.append(f"Erro ao buscar perfis: {e}")
    return results

# Execução do script principal
if __name__ == "__main__":
    # Coleta os resultados da varredura de redes
    resultados_wifi = mostrar_resultados_wifi()

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\n========================================= Perfil na interface Wi-Fi =========================================")
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
                profile_info = "=============================================================================================================\n"
                profile_info += "\nPerfil na interface Wi-Fi\n"
                profile_info += f"\nSSID: {ssid}\n\n"            

                # Executa o comando netsh para exibir a chave do perfil atual
                key_output = subprocess.check_output(f'netsh wlan show profiles "{ssid}" key=clear', shell=True, universal_newlines=True)

                # Exibe o conteúdo filtrado da chave, mantendo "Conteúdo da Chave"
                if key_output:
                    # Filtra as linhas relevantes, mantendo a linha com "Conteúdo da Chave"
                    key_output_filtered = '\n'.join([line for line in key_output.split('\n') 
                                                      if "Conte£do da Chave" in line or "Key Content" in line])

                    # Adiciona a informação da chave de segurança ao resultado final
                    profile_info += key_output_filtered.strip()
                    results.append(profile_info)  # Adiciona o resultado à lista

    # Exibe todos os resultados
    for result in results:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + result)

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "=============================================================================================================")

    # Combina os resultados da varredura e dos perfis
    resultados_completos = resultados_wifi + ["\n\n========================================= Perfil na interface Wi-Fi ========================================="] + results + ["============================================================================================================="]

    # Pergunta ao usuário se deseja salvar os resultados
    save_option = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()

    if save_option == 's':
        filename = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo (com extensão .txt): ")
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("\n".join(resultados_completos))  # Salva todos os resultados no arquivo
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {filename}")

    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
