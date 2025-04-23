import re
import requests
from bs4 import BeautifulSoup
from socket import *
from colorama import Fore, Style, init
from datetime import datetime

# Inicializando o Colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██╔══██╗
██║ █╗ ██║███████║██║   ██║██║███████╗    ██████╔╝██████╔╝
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══██╗██╔══██╗
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██████╔╝██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝
""")

# Servidores WHOIS por TLD
servidores_whois_tld = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Servidores WHOIS para IPs
servidor_whois_ip_br = 'whois.registro.br'
servidor_whois_ip_fallback = 'whois.arin.net'

# Formata datas para o padrão brasileiro DD/MM/AAAA
def formatar_data_brasileira(data_str):
    try:
        # Tenta diferentes formatos de entrada
        for fmt in (("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%d/%m/%Y")):
            try:
                data = datetime.strptime(data_str[:10], fmt)
                return data.strftime("%d/%m/%Y")
            except ValueError:
                continue
        return data_str  # Retorna original se não conseguir formatar
    except Exception:
        return data_str

# Traduz e formata a saída WHOIS para domínios .br com quebra de linha antes de Contato (ID)
def formatar_whois_br(texto):
    campos_traduzidos = {
        "domain": "Domínio",
        "owner": "Titular",
        "ownerid": "Documento",
        "responsible": "Responsável",
        "country": "País",
        "owner-c": "Contato Titular",
        "tech-c": "Contato Técnico",
        "created": "Criado",
        "changed": "Alterado",
        "expires": "Expiração",
        "status": "Status",
        "nserver": "Servidor DNS",
        "nsstat": "Status DNS",
        "nslastaa": "Último AA",
        "nic-hdl-br": "Contato (ID)",
        "person": "Nome",
        "e-mail": "E-mail",
    }

    linhas = texto.strip().splitlines()
    resultado_formatado = []
    ultimo_campo = None

    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('%'):
            continue
        partes = linha.split(":", 1)
        if len(partes) == 2:
            chave, valor = partes
            chave = chave.strip().lower()
            chave_formatada = campos_traduzidos.get(chave, chave)
            # Formata datas específicas
            if chave in ("created", "changed", "expires", "nsstat", "nslastaa"):
                valor = formatar_data_brasileira(valor.strip())

            # Adiciona quebra de linha antes de Contato (ID)
            if chave == "nic-hdl-br" and ultimo_campo != "nic-hdl-br":
                resultado_formatado.append("")  # Linha em branco antes do contato
            resultado_formatado.append(f"{chave_formatada}: {valor.strip()}")

            ultimo_campo = chave
        else:
            resultado_formatado.append(linha.strip())

    return "\n".join(resultado_formatado)

# Traduz e formata a saída WHOIS para domínios .com/.net com quebra de linha antes de contatos
def formatar_whois_com(texto):
    campos_traduzidos = {
        "domain name": "Domínio",
        "registrar": "Registrador",
        "registrar whois server": "Servidor WHOIS do Registrador",
        "registrar url": "URL do Registrador",
        "updated date": "Alterado",
        "creation date": "Criado",
        "registry expiry date": "Expiração",
        "name server": "Servidor DNS",
        "registrant name": "Titular",
        "registrant organization": "Organização",
        "registrant street": "Endereço",
        "registrant city": "Cidade",
        "registrant state/province": "Estado/Província",
        "registrant postal code": "Código Postal",
        "registrant country": "País",
        "registrant phone": "Telefone",
        "registrant email": "E-mail",
        "admin name": "Nome do Contato Administrativo",
        "admin organization": "Organização do Contato Administrativo",
        "admin street": "Endereço Administrativo",
        "admin city": "Cidade Administrativa",
        "admin state/province": "Estado/Província Administrativo",
        "admin postal code": "Código Postal Administrativo",
        "admin country": "País Administrativo",
        "admin phone": "Telefone Administrativo",
        "admin email": "E-mail Administrativo",
        "tech name": "Nome do Contato Técnico",
        "tech organization": "Organização do Contato Técnico",
        "tech street": "Endereço Técnico",
        "tech city": "Cidade Técnica",
        "tech state/province": "Estado/Província Técnico",
        "tech postal code": "Código Postal Técnico",
        "tech country": "País Técnico",
        "tech phone": "Telefone Técnico",
        "tech email": "E-mail Técnico",
    }

    linhas = texto.strip().splitlines()
    resultado_formatado = []
    ultimo_campo = None
    contato_section = False

    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('>>>'):
            continue
        partes = linha.split(":", 1)
        if len(partes) == 2:
            chave, valor = partes
            chave = chave.strip().lower()
            chave_formatada = campos_traduzidos.get(chave, chave)
            # Formata datas específicas
            if chave in ("creation date", "updated date", "registry expiry date"):
                valor = formatar_data_brasileira(valor.strip())

            # Adiciona quebra de linha antes de seções de contato
            if any(contato in chave for contato in ["registrant name", "admin name", "tech name"]) and not contato_section:
                resultado_formatado.append("")  # Linha em branco antes do contato
                contato_section = True
            resultado_formatado.append(f"{chave_formatada}: {valor.strip()}")

            ultimo_campo = chave
        else:
            resultado_formatado.append(linha.strip())

    return "\n".join(resultado_formatado)

# Remove informações de copyright e extras
def remover_copyright(texto):
    copyright_pattern = re.compile(r"%.*\n", re.MULTILINE)
    return re.sub(copyright_pattern, "", texto)

def remover_informacoes_extra(texto):
    extra_pattern = re.compile(
        r"(URL of the ICANN WHOIS Data Problem Reporting System:.*|"
        r"Last update of WHOIS database:.*|"
        r"By submitting a query to the Amazon Registrar.*|"
        r"Visit Amazon Registrar, Inc. at https://registrar.amazon.com.*|"
        r"Contact information available here:.*|"
        r"© \d{4}, Amazon\.com, Inc\..*|"
        r"For more information on Whois status codes, please visit https://icann.org/epp|"
        r"agree to abide by the following terms.*?https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-contact-support.html)",
        re.MULTILINE | re.IGNORECASE | re.DOTALL
    )
    return re.sub(extra_pattern, "", texto)

# Realiza requisição WHOIS por socket
def requisicao_whois(servidor_whois, endereco_host, padrao=True):
    try:
        objeto_socket = socket(AF_INET, SOCK_STREAM)
        objeto_socket.settimeout(10)
        conexao = objeto_socket.connect_ex((servidor_whois, 43))
        resultado = ''
        if conexao == 0:
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':
                    objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
                else:
                    objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'{endereco_host}\r\n'.encode())
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                resultado += dados.decode('latin-1', errors='ignore')
        else:
            resultado = "Erro: Não foi possível conectar ao servidor WHOIS."
        objeto_socket.close()
        return resultado
    except Exception as e:
        return f"Erro na requisição WHOIS: {str(e)}"

# Encontra e-mails no HTML
def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = set()

    email_section = soup.find("div", class_="row-fluid registry-data")
    if email_section:
        email_text = email_section.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        email_matches = re.findall(email_regex, email_text)
        emails.update(email_matches)

    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        email_matches = re.findall(email_regex, whois_text)
        emails.update(email_matches)

    return list(emails)

# Extrai campo específico do WHOIS
def extrair_campo(soup, label):
    field = soup.find("div", string=re.compile(label, re.IGNORECASE))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

# Valida se a entrada é um endereço IP (IPv4 ou IPv6)
def is_ip_address(endereco):
    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|^[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}$|^[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4}$"
    return re.match(ipv4_pattern, endereco) or re.match(ipv6_pattern, endereco)

# Verifica se o resultado WHOIS para IP é válido
def is_valid_ip_whois(resultado):
    # Considera o resultado inválido se for vazio, contém erro ou não tem informações úteis
    if not resultado or "Erro" in resultado or "No match" in resultado or len(resultado.strip().splitlines()) < 3:
        return False
    # Verifica se contém campos comuns em respostas WHOIS de IPs
    return any(keyword in resultado.lower() for keyword in ["inetnum", "netname", "owner", "orgname", "organization", "country"])

# Obtém informações WHOIS para qualquer domínio (exceto .com, .net, .br, .gov)
def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"

    try:
        # Consulta WHOIS para domínios que não são .br, .gov, .com ou .net
        if not re.search(r'\.br$|\.gov$|\.com$|\.net$', endereco):
            response_whois = requests.get(url_whois, timeout=10)
            if response_whois.status_code == 200:
                soup_whois = BeautifulSoup(response_whois.text, "html.parser")
                whois_section = soup_whois.find("pre", class_="df-raw")
                if whois_section:
                    whois_text = whois_section.get_text()
                    whois_text = remover_copyright(whois_text)
                    whois_text = remover_informacoes_extra(whois_text)
                    print(Fore.LIGHTYELLOW_EX + whois_text)

                    emails = encontrar_emails(soup_whois)
                    if emails:
                        print("\nE-mails encontrados:")
                        for email in emails:
                            print(email)

                    name = extrair_campo(soup_whois, "Registrant Name:")
                    registration_date = extrair_campo(soup_whois, "Creation Date:")
                    expiration_date = extrair_campo(soup_whois, "Registrar Registration Expiration Date:")

                    if name:
                        print(f"Nome do Titular: {name}")
                    if registration_date:
                        print(f"Data de Registro: {formatar_data_brasileira(registration_date)}")
                    if expiration_date:
                        print(f"Data de Expiração: {formatar_data_brasileira(expiration_date)}")
                else:
                    print(Fore.LIGHTRED_EX + "Nenhum resultado WHOIS encontrado.")
            else:
                print(Fore.LIGHTRED_EX + "Erro ao obter informações WHOIS via web.")
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + f"Erro na requisição web: {str(e)}")

# Obtém WHOIS via socket para domínios específicos
def obter_whois_socket(endereco, tld):
    servidor_whois = servidores_whois_tld.get(tld)
    if not servidor_whois:
        print(Fore.LIGHTRED_EX + f"Servidor WHOIS para {tld} não encontrado.")
        return
    resultado = requisicao_whois(servidor_whois, endereco, tld != '.br' and tld != '.gov')
    if tld == '.br':
        print(Fore.LIGHTGREEN_EX + formatar_whois_br(remover_copyright(resultado)))
    elif tld in ('.com', '.net'):
        print(Fore.LIGHTGREEN_EX + formatar_whois_com(remover_copyright(resultado)))
    else:
        print(Fore.LIGHTYELLOW_EX + remover_copyright(resultado))

# Obtém WHOIS para endereços IP
def obter_whois_ip(endereco):
    # Tenta consultar no whois.registro.br primeiro
    resultado = requisicao_whois(servidor_whois_ip_br, endereco, False)
    if is_valid_ip_whois(resultado):
        print(Fore.LIGHTYELLOW_EX + remover_copyright(resultado))
    else:
        # Fallback para whois.arin.net se o resultado não for válido
        resultado = requisicao_whois(servidor_whois_ip_fallback, endereco, False)
        print(Fore.LIGHTYELLOW_EX + remover_copyright(resultado))

# Função principal de consulta WHOIS
def consulta_whois():
    endereco = input(Fore.LIGHTMAGENTA_EX + "\nDigite o IP ou Nome do website Para Consultar WHOIS: ").strip()
    print("")
    if not endereco:
        print(Fore.LIGHTRED_EX + "Endereço inválido.")
        return

    # Verifica se é um endereço IP
    if is_ip_address(endereco):
        obter_whois_ip(endereco)
        return

    # Verifica o TLD para domínios
    tld = None
    for key in servidores_whois_tld:
        if endereco.endswith(key):
            tld = key
            break

    # Consulta via socket para .br, .gov, .com, .net, ou via web para outros
    if tld in ('.br', '.gov', '.com', '.net'):
        obter_whois_socket(endereco, tld)
    else:
        obter_whois(endereco)

# Executa a consulta WHOIS
consulta_whois()

input(Fore.LIGHTRED_EX + "\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
