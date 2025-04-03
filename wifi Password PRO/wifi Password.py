import subprocess
from colorama import Fore, Style, init
import os

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

def get_wifi_profiles():
    """Obtém todos os perfis Wi-Fi salvos no sistema."""
    try:
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='cp850')
        profiles = [line.split(':')[1].strip() for line in output.split('\n') if "Todos os Perfis de Usuário" in line or "All User Profile" in line]
        return profiles
    except (subprocess.CalledProcessError, UnicodeDecodeError, IndexError):
        return []

def get_wifi_password(profile):
    """Obtém a senha de um perfil Wi-Fi específico."""
    try:
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], encoding='cp850')
        password_lines = [line.split(':')[1].strip() for line in output.split('\n') if "Conteúdo da Chave" in line or "Key Content" in line]
        return password_lines[0] if password_lines else "Não disponível"
    except (subprocess.CalledProcessError, UnicodeDecodeError, IndexError):
        return "[Erro ao recuperar senha]"

def main():
    """Executa o programa principal."""
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Buscando Redes Wi-Fi salvas\n")
    profiles = get_wifi_profiles()
    
    if not profiles:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum perfil Wi-Fi encontrado!")
    else:
        # Obtém o diretório onde o script está sendo executado
        pasta_destino = os.getcwd()  
        file_path = os.path.join(pasta_destino, "Redes Wi-Fi salvas.txt")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("{:<30} | {:<20}\n".format("Perfil", "Senha"))
            file.write("-" * 44 + "\n")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "{:<30} | {:<20}".format("Perfil", "Senha"))
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "-" * 44)
            for profile in profiles:
                password = get_wifi_password(profile)
                line = f"{profile:<30} | {password:<20}\n"
                file.write(line)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + line.strip())

        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nAs redes Wi-Fi salvas foram registradas em\n")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Pasta: " + Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{pasta_destino}\n")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Arquivo: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Redes Wi-Fi salvas.txt")
    
if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
