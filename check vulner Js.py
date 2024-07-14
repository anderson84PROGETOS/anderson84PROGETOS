import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import socket

print("""

 ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗    ██╗   ██╗██╗   ██╗██╗     ███╗   ██╗███████╗██████╗          ██╗███████╗
██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝    ██║   ██║██║   ██║██║     ████╗  ██║██╔════╝██╔══██╗         ██║██╔════╝
██║     ███████║█████╗  ██║     █████╔╝     ██║   ██║██║   ██║██║     ██╔██╗ ██║█████╗  ██████╔╝         ██║███████╗
██║     ██╔══██║██╔══╝  ██║     ██╔═██╗     ╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║██╔══╝  ██╔══██╗    ██   ██║╚════██║
╚██████╗██║  ██║███████╗╚██████╗██║  ██╗     ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║███████╗██║  ██║    ╚█████╔╝███████║
 ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝      ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝     ╚════╝ ╚══════╝
                                                                                                                    
""")

# Lista de cabeçalhos de segurança e vulnerabilidades adicionais a verificar
cabecalhos = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "MySQL Error",
    "X-Powered-By",
    "Server"
]

# Função para verificar cabeçalhos de segurança e outras vulnerabilidades
def verificar_vulnerabilidades(url):
    links_desatualizados = []
    links_sensiveis = []

    try:
        # Resolve o endereço IP do website
        try:
            hostname = url.split('//')[-1].split('/')[0]  # Extrai o nome do host da URL
            ip = socket.gethostbyname(hostname)
            print(f'\n\nEndereço IP: {ip}   Website: {hostname}')
        except socket.gaierror as e:
            print(f'\nErro ao resolver o endereço IP do {url}: {e}')
            return
        
        # Tenta estabelecer uma conexão HTTP com o website
        try:
            response = requests.get(url, timeout=5)
            print('\n\n\nCabeçalho HTTP\n==============\n')
            for header, value in response.headers.items():
                print(f'{header}: {value}')
            
            # Verifica o status da conexão
            status_code = response.status_code
            print(f'\n\n\nStatus da conexão: {status_code}')
            if status_code == 200:
                print(f'\nConexão com o Website com sucesso!: {url} ')
            else:
                print(f'\nErro ao conectar-se ao: {url} {response.reason}')
        except requests.exceptions.RequestException as e:
            print(f'\nErro ao conectar-se ao: {url} {e}')
            return

        # Verificação de cabeçalhos de segurança essenciais
        cabecalhos_ausentes = [cabecalho for cabecalho in cabecalhos[:5] if cabecalho not in response.headers]

        if cabecalhos_ausentes:
            print()
        else:
            print(f"\nURL: {url} possui todos os cabeçalhos essenciais de segurança.")
        
        # Verificação de erros de MySQL
        erros_mysql = ["You have an error in your SQL syntax", "Warning: mysql", "MySQL server version for the right syntax"]
        for erro in erros_mysql:
            if erro in response.text:
                print(f"\nPossível vulnerabilidade MySQL encontrada: {erro}")
        
        # Verificação de cabeçalhos potencialmente problemáticos
        if "X-Powered-By" in response.headers or "Server" in response.headers:
            if "X-Powered-By" in response.headers:
                print(f"\nX-Powered-By: {response.headers['X-Powered-By']}")
            if "Server" in response.headers:
                print(f"\nServer: {response.headers['Server']}")

        # Verificação de formulários inseguros
        soup = BeautifulSoup(response.text, 'html.parser')
        formularios = soup.find_all('form')
        formularios_inseguros = [formulario for formulario in formularios if 'https://' not in formulario.get('action', '')]
        if formularios_inseguros:
            print(f"\nEncontrado(s) {len(formularios_inseguros)} formulário(s) inseguro(s):")
            for formulario in formularios_inseguros:
                print(formulario)
        else:
            print("")

        # Verificação de segurança de cookies
        for cookie in response.cookies:
            if not cookie.secure:
                print(f"\nCookie '{cookie.name}' não está marcado como Secure")
            if not cookie.has_nonstandard_attr('HttpOnly'):
                print(f"\nCookie '{cookie.name}' não está marcado como HttpOnly")

        # Verificação de configuração PHP padrão
        if "phpinfo()" in response.text:
            print(f"\nURL: {url} possui exposição de phpinfo()")
        
        # Verificação de bibliotecas de JavaScript desatualizadas
        scripts = soup.find_all('script')
        for script in scripts:
            src = script.get('src')
            if src:
                link_completo = urljoin(url, src)
                if "jquery" in src.lower() or "bootstrap" in src.lower():
                    links_desatualizados.append(link_completo)
                    print(f"\nURL: {url} versão desatualizada do JavaScript: {link_completo}")

        # Verificação de links para arquivos sensíveis ou diretórios não protegidos
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            link_completo = urljoin(url, href)
            if any(link_completo.endswith(extensao) for extensao in ['.bak', '.old', '.swp']) or "/config/" in link_completo.lower():
                links_sensiveis.append(link_completo)
                print(f"\nURL: {url} contém link para arquivo sensível ou diretório não protegido: {link_completo}")

        # Exibir os links encontrados, se houver algum
        if links_desatualizados or links_sensiveis:
            print("\n\nLinks Encontrados\n==================")
            for link in links_desatualizados:
                print(link)
            for link in links_sensiveis:
                print(link)
        else:
            print("\nNenhum link sensível ou diretório não protegido Encontrado")

        # Verificação de XSS (Cross-Site Scripting)
        if "<script>" in response.text:
            print("\nPossível vulnerabilidade XSS (Cross-Site Scripting) Encontrada")
            print(f"\nURL completa da vulnerabilidade: {response.url}")

            # Exemplo de exploração de XSS
            payload = '<script>alert("XSS Vulnerável!");</script>'
            exploit_url = response.url + '?' + payload  # Adiciona o payload à URL

            print(f"\nExemplo de exploração: {exploit_url}")

    except requests.exceptions.RequestException as e:
        print(f"\nErro ao conectar-se a {url}: {e}")

# Solicitar ao usuário a URL para verificar
url = input("\nDigite a URL do website (incluindo http:// ou https://): ").strip()

print(f"\n\n\nVerificando website: {url}")
verificar_vulnerabilidades(url)

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
