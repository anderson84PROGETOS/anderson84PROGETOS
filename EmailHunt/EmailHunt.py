import re
import requests
from bs4 import BeautifulSoup
from socket import *
from colorama import Fore, Style, init
from googlesearch import search
import ipaddress

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗███╗   ███╗ █████╗ ██╗██╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗
██╔════╝████╗ ████║██╔══██╗██║██║     ██║  ██║██║   ██║████╗  ██║╚══██╔══╝
█████╗  ██╔████╔██║███████║██║██║     ███████║██║   ██║██╔██╗ ██║   ██║   
██╔══╝  ██║╚██╔╝██║██╔══██║██║██║     ██╔══██║██║   ██║██║╚██╗██║   ██║   
███████╗██║ ╚═╝ ██║██║  ██║██║███████╗██║  ██║╚██████╔╝██║ ╚████║   ██║   
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   
                                                                                                                                                         
""")

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Mapa de servidores WHOIS para IPs por RIR (Regional Internet Registry)
servidores_whois_ip = {
    'arin': 'whois.arin.net',
    'ripe': 'whois.ripe.net',
    'apnic': 'whois.apnic.net',
    'lacnic': 'whois.lacnic.net',
    'afrinic': 'whois.afrinic.net',
}

def is_valid_ip(address):
    """Valida se o endereço é um IP válido."""
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

def get_ip_whois_server(ip):
    try:
        socket_obj = socket(AF_INET, SOCK_STREAM)
        socket_obj.settimeout(5)
        socket_obj.connect(('whois.iana.net', 43))
        socket_obj.send(f'{ip}\r\n'.encode())
        response = ''
        while True:
            data = socket_obj.recv(65500)
            if not data:
                break
            response += data.decode('utf-8')
        socket_obj.close()

        for line in response.splitlines():
            if line.startswith('refer:') or 'whois:' in line:
                server = line.split(':')[1].strip()
                return server
    except gaierror as e:        
        # Fallback to LACNIC for specific IP ranges
        if ip.startswith('196.') or ip.startswith('200.'):
            return servidores_whois_ip['lacnic']
        return servidores_whois_ip['arin']
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro ao consultar whois.iana.net: {e}")
        return servidores_whois_ip['arin']

def find_email_in_text(text):
    """Encontra e-mails em um texto usando regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails

def remover_direitos_autorais(texto):
    """Remove o texto de direitos autorais."""
    padrao_copyright = re.compile(r"%.*\n", re.MULTILINE)
    return re.sub(padrao_copyright, "", texto)

def requisicao_whois(servidor_whois, endereco, padrao):
    """Faz uma consulta WHOIS usando sockets."""
    try:
        socket_objeto = socket(AF_INET, SOCK_STREAM)
        socket_objeto.settimeout(5)  # Timeout reduzido
        conexao = socket_objeto.connect_ex((servidor_whois, 43))
        resultado = ''
        if conexao == 0:
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
                    socket_objeto.send(f'domain {endereco}\r\n'.encode())
                else:
                    socket_objeto.send(f'n + {endereco}\r\n'.encode())
            else:
                socket_objeto.send(f'{endereco}\r\n'.encode())
            while True:
                dados = socket_objeto.recv(65500)
                if not dados:
                    break
                resultado += dados.decode('utf-8')
        else:
            print(Fore.LIGHTRED_EX + f"Erro ao conectar ao servidor WHOIS {servidor_whois}.")
        socket_objeto.close()
        return resultado
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro na consulta WHOIS: {e}")
        return ""

def encontrar_emails(soup):
    """Extrai e-mails de uma página WHOIS."""
    regex_email = r"[\w\.-]+@[\w\.-]+"
    emails = []
    secao_email = soup.find("div", class_="row-fluid registry-data")
    if secao_email:
        texto_email = secao_email.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        correspondencias_email = re.findall(regex_email, texto_email)
        emails.extend(correspondencias_email)
    secao_whois = soup.find("pre", class_="df-raw")
    if secao_whois:
        texto_whois = secao_whois.get_text()
        correspondencias_email = re.findall(regex_email, texto_whois)
        emails.extend(correspondencias_email)
    return emails

def extrair_campo(secao_whois, rotulo):
    """Extrai um campo específico do WHOIS."""
    campo = secao_whois.find("div", string=re.compile(rotulo))
    if campo:
        valor = campo.find_next_sibling("div").get_text(strip=True)
        return valor
    return ""

def remover_informacoes_extras(texto):
    """Remove informações extras do texto WHOIS."""
    padrao_extra = re.compile(r"(URL do Sistema de Relatórios de Problemas de Dados WHOIS da ICANN:.*|Última atualização do banco de dados WHOIS:.*|Ao enviar uma consulta ao Registrador Amazon.*|Visite Amazon Registrar, Inc. em https://registrar.amazon.com.*|Informações de contato disponíveis aqui:.*|© \d{4}, Amazon\.com, Inc\..*|Para mais informações sobre códigos de status Whois, visite https://icann.org/epp|concorda em cumprir os seguintes termos.*?https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-contact-support.html)", re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return re.sub(padrao_extra, "", texto)

def formatar_data(data):
    """Converte data no formato YYYYMMDD para YYYY/MM/DD."""
    if len(data) == 8 and data.isdigit():
        return f"{data[:4]}/{data[4:6]}/{data[6:]}"
    return data

def formatar_whois(texto):
    """Formata e traduz os dados do WHOIS."""
    if not texto.strip():
        return Fore.LIGHTRED_EX + "Nenhuma informação WHOIS disponível.\n"
    
    linhas = texto.splitlines()
    resultado = Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n=== Informações WHOIS ===\n\n"
    servidores_dns = []
    dns_atual = {}
    
    for linha in linhas:
        if linha.startswith("domain:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Domínio: {linha.split()[1]}\n\n"
        elif linha.startswith("owner:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Proprietário: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('owner:')[1].strip()}\n"
        elif linha.startswith("ownerid:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"CNPJ do Proprietário: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("responsible:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Responsável: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('responsible:')[1].strip()}\n\n"
        elif linha.startswith("country:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"País: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("owner-c:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Contato do Proprietário: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("tech-c:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Contato Técnico: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("nserver:"):
            if dns_atual:  # Se já temos um servidor sendo processado, adicionamos antes de começar outro
                servidores_dns.append(dns_atual)
            dns_atual = {"nome": linha.split()[1], "status": "", "ultima_atualizacao": ""}
        elif linha.startswith("nsstat:") and dns_atual:
            dns_atual["status"] = formatar_data(linha.split()[1])  # Formata como data
        elif linha.startswith("nslastaa:") and dns_atual:
            dns_atual["ultima_atualizacao"] = formatar_data(linha.split()[1])
        elif linha.startswith("inetnum:"):
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Faixa de Endereços de Rede: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('inetnum:')[1].strip()}\n\n"
        elif linha.startswith("inetrev:"):
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nResolução Reversa: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('inetrev:')[1].strip()}\n\n"
        elif linha.startswith("created:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Criação: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{formatar_data(linha.split()[1])}\n"
        elif linha.startswith("changed:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Alteração: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{formatar_data(linha.split()[1])}\n"
        elif linha.startswith("expires:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Expiração: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{formatar_data(linha.split()[1])}\n"
        elif linha.startswith("status:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Status: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("nic-hdl-br:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nIdentificador NIC-BR: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n"
        elif linha.startswith("person:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Pessoa: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('person:')[1].strip()}\n"
        elif linha.startswith("e-mail:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"E-mail: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split()[1]}\n\n"
        # Campos comuns para IPs
        elif linha.startswith("netname:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Nome da Rede: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('netname:')[1].strip()}\n"
        elif linha.startswith("org-name:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Organização: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('org-name:')[1].strip()}\n"
        elif linha.startswith("admin-c:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Contato Administrativo: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{linha.split('admin-c:')[1].strip()}\n"
    
    # Adiciona o último servidor DNS processado
    if dns_atual:
        servidores_dns.append(dns_atual)

    # Exibe os servidores DNS formatados em uma linha
    if servidores_dns:
        resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nServidores de Nome DNS\n"
        for dns in servidores_dns:
            linha_formatada = (
                Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{dns['nome']:<30} "
                f"{Fore.LIGHTGREEN_EX + Style.BRIGHT + 'Status: ' + dns['status']:<30} "
                f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT + 'Última Atualização: ' + dns['ultima_atualizacao']}"
            )
            resultado += linha_formatada + "\n"

    return resultado

def obter_whois(endereco):
    """Obtém informações WHOIS de um domínio ou IP."""
    if is_valid_ip(endereco):
        # Consulta WHOIS para IP
        servidor_whois = get_ip_whois_server(endereco)
        if not servidor_whois:
            print(Fore.LIGHTRED_EX + "\nNão foi possível determinar o servidor WHOIS para o IP.\n")
            return
        resultado = requisicao_whois(servidor_whois, endereco, False)
        if not resultado:
            print(Fore.LIGHTRED_EX + "\nFalha ao obter informações WHOIS para o IP.\n")
            return
        texto_formatado = formatar_whois(remover_direitos_autorais(resultado))
        print(Fore.LIGHTGREEN_EX + texto_formatado)
        emails = find_email_in_text(resultado)
        if emails:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nE-mails Encontrados no WHOIS\n")
            for email in set(emails):
                print(Fore.LIGHTYELLOW_EX + email)
    else:
        # Consulta WHOIS para domínio
        url_whois = f"https://www.whois.com/whois/{endereco}"
        url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        try:
            resposta_whois = requests.get(url_whois, headers=headers, timeout=10)
            resposta_registro_br = requests.get(url_registro_br, headers=headers, timeout=10)

            if resposta_whois.status_code == 200 and resposta_registro_br.status_code == 200:
                emails = []
                if re.search(r'\.br$', endereco):
                    soup_registro_br = BeautifulSoup(resposta_registro_br.text, "html.parser")
                    div_resultado = soup_registro_br.find("div", class_="result")
                    if div_resultado:
                        texto_resultado = div_resultado.get_text()
                        print(Fore.LIGHTGREEN_EX + formatar_whois(remover_direitos_autorais(texto_resultado)))
                        emails.extend(find_email_in_text(texto_resultado))

                elif re.search(r'\.com$', endereco):
                    soup_whois = BeautifulSoup(resposta_whois.text, "html.parser")
                    secao_whois = soup_whois.find("pre", class_="df-raw")
                    if secao_whois:
                        texto_whois = secao_whois.get_text()
                        texto_whois = remover_direitos_autorais(texto_whois)
                        texto_whois = remover_informacoes_extras(texto_whois)
                        print(Fore.LIGHTYELLOW_EX + texto_whois)
                        emails.extend(find_email_in_text(texto_whois))
                        emails.extend(encontrar_emails(soup_whois))
                        nome = extrair_campo(secao_whois, "Nome do Registrante:")
                        data_registro = extrair_campo(secao_whois, "Data de Criação:")
                        data_expiracao = extrair_campo(secao_whois, "Data de Expiração do Registro:")
                        if nome:
                            print(f"Nome do Titular: {nome}")
                        if data_registro:
                            print(f"Data de Registro: {formatar_data(data_registro)}")
                        if data_expiracao:
                            print(f"Data de Expiração: {formatar_data(data_expiracao)}")
                
                if emails:
                    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nE-mails encontrados no WHOIS:")
                    for email in set(emails):
                        print(Fore.LIGHTYELLOW_EX + email)
                else:
                    pass
            
            else:
                print(Fore.LIGHTRED_EX + "\nErro ao obter informações WHOIS.\n")
        
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"\nErro ao consultar WHOIS: {e}\n")

def obter_whois_br(endereco):
    """Consulta WHOIS para domínios .br usando sockets."""
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    if not resultado:
        print(Fore.LIGHTRED_EX + "\nFalha ao obter informações WHOIS para o domínio .br.\n")
        return
    texto_formatado = formatar_whois(remover_direitos_autorais(resultado))
    print(Fore.LIGHTGREEN_EX + texto_formatado)
    emails = find_email_in_text(resultado)
    if emails:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nE-mails Encontrados no WHOIS br\n")
        for email in set(emails):
            print(Fore.LIGHTYELLOW_EX + email)

def obter_whois_gov(endereco):
    """Consulta WHOIS para domínios .gov."""
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        resultado = requisicao_whois(servidor_whois_gov, endereco, False)
        if not resultado:
            print(Fore.LIGHTRED_EX + "\nFalha ao obter informações WHOIS para o domínio .gov.\n")
            return
        print(Fore.LIGHTYELLOW_EX + remover_direitos_autorais(resultado))
        emails = find_email_in_text(resultado)
        if emails:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nE-mails Encontrados no WHOIS gov\n")
            for email in set(emails):
                print(Fore.LIGHTYELLOW_EX + email)
    else:
        print(Fore.LIGHTRED_EX + "Servidor WHOIS para domínios .gov não encontrado.")

def search_email_by_name(name):
    """Busca e-mails associados a um nome no Google."""
    try:
        query = f'"{name}" email'
        emails = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        # Limitar a 10 URLs manualmente
        for i, url in enumerate(search(query)):
            if i >= 10:  # Para após 10 resultados
                break
            try:
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                found_emails = find_email_in_text(text)
                emails.extend(found_emails)
            except:
                continue
        return list(set(emails)) if emails else None
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro ao buscar e-mail: {e}")
        return None

def main():
    """Menu principal para escolher entre busca por nome ou WHOIS."""
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n=== EmailHunt - Busca de E-mails ===\n")
    print(Fore.LIGHTGREEN_EX + "1 = Buscar e-mails por nome de usuário ou IP")
    print(Fore.LIGHTGREEN_EX + "2 = Consultar WHOIS por domínio IP")
    choice = input(Fore.LIGHTYELLOW_EX + "\nEscolha uma opção: ").strip()

    if choice == '1':
        name = input(Fore.LIGHTGREEN_EX + "\nDigite o nome do usuário: ").strip()
        print(Fore.LIGHTCYAN_EX + f"\nBuscando e-mails associados a: {name}")
        emails = search_email_by_name(name)
        if emails:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nE-mails Encontrados")
            for email in emails:
                print(Fore.LIGHTYELLOW_EX + email)
        else:
            print(Fore.LIGHTRED_EX + "\nNenhum e-mail Encontrado\n")
    
    elif choice == '2':
        endereco = input(Fore.LIGHTGREEN_EX + "\nDigite o domínio ou IP para consultar WHOIS: ").strip()
        print(Fore.LIGHTCYAN_EX + f"\nConsultando WHOIS para: {endereco}")
        if re.search(r'\.br$', endereco) and not is_valid_ip(endereco):
            obter_whois_br(endereco)
        elif re.search(r'\.gov$', endereco) and not is_valid_ip(endereco):
            obter_whois_gov(endereco)
        obter_whois(endereco)
    
    else:
        print(Fore.LIGHTRED_EX + "\nOpção inválida.")

if __name__ == "__main__":
    main()
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
