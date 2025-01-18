import json
import re
import requests
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nAcesse o site para saber mais: https://commentpicker.com/instagram-username.php")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗██████╗     ██╗   ██╗███████╗███████╗██████╗     ██╗███╗   ██╗███████╗████████╗ █████╗ 
██║██╔══██╗    ██║   ██║██╔════╝██╔════╝██╔══██╗    ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗
██║██║  ██║    ██║   ██║███████╗█████╗  ██████╔╝    ██║██╔██╗ ██║███████╗   ██║   ███████║
██║██║  ██║    ██║   ██║╚════██║██╔══╝  ██╔══██╗    ██║██║╚██╗██║╚════██║   ██║   ██╔══██║
██║██████╔╝    ╚██████╔╝███████║███████╗██║  ██║    ██║██║ ╚████║███████║   ██║   ██║  ██║
╚═╝╚═════╝      ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝
                                                                                                                                                                                                                                                                                                                                                                                          
""")

def get_profile_id(instagram_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Faz a requisição para a URL fornecida
        response = requests.get(instagram_url, headers=headers)
        response.raise_for_status()
        html_content = response.text

        # Procura pelo pattern "profile_id":"<número>"
        match = re.search(r'"profile_id":"(\d+)"', html_content)
        if match:
            return match.group(1)  # Retorna o número do profile_id
        else:
            return "profile_id não encontrado."
    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar a URL: {e}"

def useridToUsername(userid):
    # Função ajustada para obter o nome do usuário pelo ID
    header = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 Instagram 12.0.0.16.90 (iPhone9,4; iOS 10_3_3; en_US; en-US; scale=2.61; gamut=wide; 1080x1920)',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        r = requests.get(f'https://i.instagram.com/api/v1/users/{userid}/info/', headers=header)
        if r.status_code == 404:
            print("Usuário não encontrado.")
            return None
        response = r.json()
        if response.get("status") == 'ok':
            username = response['user']['username']            
            return username
        else:
            print("Erro na resposta da API.")
            return None
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON.")
    except KeyError:
        print("Resposta inesperada da API.")
    return None

def main():
    # Solicita ao usuário a escolha entre ID ou nome
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Escolha uma opção\n")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "1. Obter o profile_id  Digite a URL do perfil do Instagram")

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "2. Obter o nome de usuário")
    choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número da opção desejada: ").strip()

    if choice == "1":
        # Solicita a URL do perfil para obter o profile_id
        url = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite a URL do perfil do Instagram: ")
        profile_id = get_profile_id(url)
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nprofile_id: {profile_id}")

    elif choice == "2":
        # Solicita o ID do usuário
        try:
            userid = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o profile_id do usuário: ").strip()
            # Chama a função para obter o nome do usuário
            resolved_username = useridToUsername(userid)
            if resolved_username:
                print(f"\nNome do usuário: {resolved_username}")
            else:
                print("[-] Não foi possível encontrar o nome do usuário.")
        except ValueError:
            print("Entrada inválida. Digite um número válido para o ID do usuário.")

    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Opção inválida. Tente novamente.")    

if __name__ == '__main__':
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
