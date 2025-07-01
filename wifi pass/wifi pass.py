import subprocess
import platform
import re
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

def banner():
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """ 
██╗    ██╗██╗███████╗██╗    ██████╗  █████╗ ███████╗███████╗
██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔════╝██╔════╝
██║ █╗ ██║██║█████╗  ██║    ██████╔╝███████║███████╗███████╗
██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██║╚════██║╚════██║
╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║███████║███████║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝                                                                                                    
""")

def list_saved_wifi_profiles_and_passwords():
    # Display banner
    banner()

    # Check if running on Windows
    if platform.system() != "Windows":
        return ["Este script só funciona em sistemas Windows."]

    results = []
    try:
        # Execute netsh command to get WLAN profiles
        command_output = subprocess.check_output('netsh wlan show profiles', shell=True, encoding='utf-8', errors='ignore')
        lines = command_output.split('\n')

        # Iterate through lines starting from the 9th (skip header)
        for line in lines[9:]:
            tokens = line.split(':')
            if len(tokens) >= 2:
                profile_name = tokens[0].strip()
                ssid = tokens[1].strip()
                if ssid and not ssid.lower().startswith(('perfis', 'nenhum', 'política')):
                    # Prepare profile info without color codes for file output
                    profile_info_file = f"=========================================\nPerfil na interface Wi-Fi\nSSID: {ssid}\n\n"
                    # Prepare profile info with color for terminal
                    profile_info_terminal = (
                        Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "=========================================\n" +
                        Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Perfil na interface Wi-Fi\nSSID: " +
                        Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ssid}\n\n"
                    )

                    # Get password for the profile
                    try:
                        key_output = subprocess.check_output(
                            f'netsh wlan show profile name="{ssid}" key=clear', shell=True, encoding='utf-8', errors='ignore'
                        )
                        key_lines = [l for l in key_output.split('\n') if "Conte" in l and "Chave" in l or "Key Content" in l]
                        key_info = key_lines[0].strip() if key_lines else "Senha não disponível."
                    except subprocess.CalledProcessError:
                        key_info = "Erro ao recuperar a senha (permissões de administrador podem ser necessárias)."

                    profile_info_file += key_info
                    profile_info_terminal += key_info
                    results.append((profile_info_terminal, profile_info_file))
    except subprocess.CalledProcessError as e:
        results.append((Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao listar perfis: {e}", f"Erro ao listar perfis: {e}"))
    except Exception as e:
        results.append((Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro inesperado: {e}", f"Erro inesperado: {e}"))

    return results

def show_available_networks():
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n📡 Redes Wi-Fi visíveis BSSID\n")
    try:
        output = subprocess.check_output("netsh wlan show networks mode=bssid", shell=True, encoding="utf-8", errors="ignore")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + output)
        return output
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao listar redes visíveis: {e}"
        print(Fore.LIGHTRED_EX + Style.BRIGHT + error_msg)
        return error_msg

def main():
    # Get Wi-Fi profiles
    results = list_saved_wifi_profiles_and_passwords()

    # Display profiles in terminal
    if not results:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Nenhum perfil Wi-Fi encontrado.")
    for terminal_output, _ in results:
        print(terminal_output)
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "=========================================\n\n")

    # Get and display available networks
    available_networks = show_available_networks()

    # Prompt to save results
    save_option = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if save_option == 's':
        filename = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo: ").strip()
        if not filename:
            filename = "wifi_results"
        if not filename.endswith('.txt'):
            filename += '.txt'

        # Validate filename
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNome de arquivo inválido. Usando 'wifi_results.txt'.")
            filename = ".txt"

        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write("Perfis Wi-Fi Salvos\n")
                for _, file_output in results:
                    file.write(file_output + "\n")
                file.write("=========================================\n\n")
                file.write("\nRedes Wi-Fi Visíveis BSSID\n")
                file.write(available_networks)
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {filename}")
        except IOError as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar o arquivo: {e}")

    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")

if __name__ == "__main__":
    main()
