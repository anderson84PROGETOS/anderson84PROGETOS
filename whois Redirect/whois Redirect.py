import re
import requests
from bs4 import BeautifulSoup
import socket
from colorama import Fore, Style, init
from datetime import datetime

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗    
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝    
██║ █╗ ██║███████║██║   ██║██║███████╗    ██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║       
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║       
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║       
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝                                                                                 
""")

# Cabeçalhos para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Mapeamento de NIC handles para AS numbers (fallback)
nic_to_as = {
    'INI74': '22548'  # NIC.br associated with AS22548
}

def obter_dados_asn(ip):
    try:
        resposta = requests.get(f"https://ipinfo.io/{ip}/json")
        dados = resposta.json()
        org = dados.get("org", "")
        pais = dados.get("country", "Desconhecido")
        
        if org.startswith("AS"):
            asn_num = org.split()[0][2:]  # Remove "AS"
            descricao = " ".join(org.split()[1:])
            return asn_num, descricao, pais
    except Exception as e:
        print(Fore.RED + f"Erro ao obter dados ASN: {e}")
    return None, None, None

def remover_direitos_autorais(texto):
    padrao_copyright = re.compile(r"%.*\n", re.MULTILINE)
    return re.sub(padrao_copyright, "", texto)

def requisicao_whois(servidor_whois, endereco_host, padrao):
    socket_objeto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao = socket_objeto.connect_ex((servidor_whois, 43))
    resultado = ''
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':
                socket_objeto.send(f'domain {endereco_host}\r\n'.encode())
            else:
                socket_objeto.send(f'n + {endereco_host}\r\n'.encode())
        else:
            socket_objeto.send(f'{endereco_host}\r\n'.encode())
        while True:
            dados = socket_objeto.recv(65500)
            if not dados:
                break
            resultado += dados.decode('latin-1')
    socket_objeto.close()
    return resultado

def encontrar_emails(soup):
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
    campo = secao_whois.find("div", string=re.compile(rotulo))
    if campo:
        valor = campo.find_next_sibling("div").get_text(strip=True)
        return valor
    return ""

def remover_informacoes_extras(texto):
    padrao_extra = re.compile(r"(URL do Sistema de Relatórios de Problemas de Dados WHOIS da ICANN:.*|Última atualização do banco de dados WHOIS:.*|Ao enviar uma consulta ao Registrador Amazon.*|Visite Amazon Registrar, Inc. em https://registrar.amazon.com.*|Informações de contato disponíveis aqui:.*|© \d{4}, Amazon\.com, Inc\..*|Para mais informações sobre códigos de status Whois, visite https://icann.org/epp|concorda em cumprir os seguintes termos.*?https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-contact-support.html)", re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return re.sub(padrao_extra, "", texto)

def formatar_data(data):
    if len(data) == 8 and data.isdigit():
        return f"{data[:4]}/{data[4:6]}/{data[6:]}"
    return data

def formatar_whois(texto, dominio=None):
    linhas = texto.splitlines()
    resultado = Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n=== Informações WHOIS ===\n\n"
    servidores_dns = []
    dns_atual = {}
    
    for linha in linhas:
        if linha.startswith("domain:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Domínio: {linha.split()[1]}\n\n"
        elif linha.startswith("owner:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Proprietário: {linha.split('owner:')[1].strip()}\n"
        elif linha.startswith("ownerid:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"CNPJ do Proprietário: {linha.split()[1]}\n"
        elif linha.startswith("responsible:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Responsável: {linha.split('responsible:')[1].strip()}\n\n"
        elif linha.startswith("country:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"País: {linha.split()[1]}\n"
        elif linha.startswith("owner-c:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Contato do Proprietário: {linha.split()[1]}\n"
        elif linha.startswith("tech-c:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Contato Técnico: {linha.split()[1]}\n"
        elif linha.startswith("nserver:"):
            if dns_atual:
                servidores_dns.append(dns_atual)
            dns_atual = {"nome": linha.split()[1], "status": "", "ultima_atualizacao": ""}
        elif linha.startswith("nsstat:") and dns_atual:
            dns_atual["status"] = formatar_data(linha.split()[1])
        elif linha.startswith("nslastaa:") and dns_atual:
            dns_atual["ultima_atualizacao"] = formatar_data(linha.split()[1])
        elif linha.startswith("inetnum:"):
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Faixa de Endereços de Rede: {linha.split('inetnum:')[1].strip()}\n\n"
        elif linha.startswith("inetrev:"):
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nResolução Reversa: {linha.split('inetrev:')[1].strip()}\n\n"
        elif linha.startswith("created:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Criação: {formatar_data(linha.split()[1])}\n"
        elif linha.startswith("changed:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Alteração: {formatar_data(linha.split()[1])}\n"
        elif linha.startswith("expires:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Data de Expiração: {formatar_data(linha.split()[1])}\n"
        elif linha.startswith("status:"):
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Status: {linha.split()[1]}\n"
        elif linha.startswith("nic-hdl-br:"):
            nic_handle = linha.split()[1]
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Identificador NIC-BR: {nic_handle}\n" 
            
        elif linha.startswith("person:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nPessoa: {linha.split('person:')[1].strip()}\n"
        elif linha.startswith("e-mail:"):
            resultado += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"E-mail: {linha.split()[1]}\n\n"          
                    
    if dns_atual:
        servidores_dns.append(dns_atual)

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
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    resposta_whois = requests.get(url_whois, headers=headers)
    resposta_registro_br = requests.get(url_registro_br, headers=headers)

    if resposta_whois.status_code == 200 and resposta_registro_br.status_code == 200:
        if re.search(r'\.br$', endereco):
            soup_registro_br = BeautifulSoup(resposta_registro_br.text, "html.parser")
            div_resultado = soup_registro_br.find("div", class_="result")
            if div_resultado:
                texto_resultado = div_resultado.get_text()
                print(Fore.LIGHTGREEN_EX + formatar_whois(remover_direitos_autorais(texto_resultado), dominio=endereco))

        elif re.search(r'\.com$', endereco):
            soup_whois = BeautifulSoup(resposta_whois.text, "html.parser")
            secao_whois = soup_whois.find("pre", class_="df-raw")
            if secao_whois:
                texto_whois = secao_whois.get_text()
                texto_whois = remover_direitos_autorais(texto_whois)
                texto_whois = remover_informacoes_extras(texto_whois)
                print(Fore.LIGHTYELLOW_EX + texto_whois)
                emails = encontrar_emails(soup_whois)
                if emails:
                    print("\nE-mails encontrados:")
                    for email in emails:
                        print(email)
                nome = extrair_campo(secao_whois, "Nome do Registrante:")
                data_registro = extrair_campo(secao_whois, "Data de Criação:")
                data_expiracao = extrair_campo(secao_whois, "Data de Expiração do Registro:")
                if nome:
                    print(f"Nome do Titular: {nome}")
                if data_registro:
                    print(f"Data de Registro: {formatar_data(data_registro)}")
                if data_expiracao:
                    print(f"Data de Expiração: {formatar_data(data_expiracao)}")
    else:
        print("Erro ao obter informações WHOIS.")

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    print(Fore.LIGHTGREEN_EX + formatar_whois(remover_direitos_autorais(resultado), dominio=endereco))

def obter_whois_gov(endereco):
    servidor_whois = servidores_whois_tdl.get('.gov', None)
    if servidor_whois:
        resultado = requisicao_whois(servidor_whois, endereco, False)
        print(remover_direitos_autorais(resultado))
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def obter_informacoes_dominio(endereco):
    for tld, servidor in servidores_whois_tdl.items():
        if endereco.endswith(tld):
            resultado = ""
            resultado += Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\n============== Mais Informações ==============\n\n"
            resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Domínio: {endereco}\n"
            try:
                ip = socket.gethostbyname(endereco)
                resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Endereço IP: {ip}\n"
                asn, descricao, pais = obter_dados_asn(ip)
                if asn and descricao:                   
                    
                    resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Descrição: {descricao}\n"

                    resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Autonomous System: AS{asn}\n"
                                       
                    resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Link para Detalhes: https://bgp.he.net/AS{asn}\n\n"
                else:
                    resultado += Fore.LIGHTRED_EX + Style.BRIGHT + "Não foi possível obter os dados ASN automaticamente.\n"
            except socket.gaierror:
                resultado += Fore.LIGHTRED_EX + Style.BRIGHT + "Erro: Não foi possível resolver o domínio para um IP.\n"
            print(resultado)
            return
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "Domínio não suportado para consulta WHOIS direta.")

def verificar_open_redirect(url):
    status_messages = {
        200: "OK",
        301: "MOVIDO PERMANENTEMENTE",
        302: "ENCONTRADO",
        303: "VEJA OUTRO",
        307: "REDIRECIONAMENTO TEMPORÁRIO",
        308: "REDIRECIONAMENTO PERMANENTE"
    } 
    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nVerificando Redirecionamentos em: {url}\n")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Histórico de Redirecionamentos\n")
    
    session = requests.Session()
    try:
        response = session.get(url, headers=headers, timeout=5, allow_redirects=True)
        
        final_status = response.status_code
        final_msg = status_messages.get(final_status, "STATUS DESCONHECIDO")
        if final_status == 200:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{final_status} - {final_msg} -> {response.url}")
        
        if response.history:
            for redirect in response.history:
                status_msg = status_messages.get(redirect.status_code, "STATUS DESCONHECIDO")
                location = redirect.headers.get("Location", "Nenhum Location encontrado")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{redirect.status_code} - {status_msg} -> {location}")
        
    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar a URL: {e}")
        return

def obter_informacoes_as(as_number):
    url = f"https://bgp.he.net/AS{as_number}"
    try:
        resposta = requests.get(url, headers=headers)
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, "html.parser")            
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"AS: {as_number}\n"
            resultado += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Link para Detalhes: {url}\n"

            # Tentar extrair informações adicionais
            try:
                org_tag = soup.select_one("table.table > tr > td > font")
                if org_tag:
                    resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Organização: {org_tag.text.strip()}\n"
                country_tag = soup.select_one("table.table > tr > td > a > img")
                if country_tag and country_tag.get("title"):
                    resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"País: {country_tag.get('title')}\n"
                # Adicionar Internet Exchanges genérico
                resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + "Internet Exchanges: Pode participar de IX.br ou outros (ver detalhes no link acima)\n"
            except:
                resultado += Fore.LIGHTGREEN_EX + Style.BRIGHT + "Informações detalhadas requerem acesso à API do bgp.he.net.\n"
            
            print(resultado)
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar informações do AS{as_number}: Status {resposta.status_code}")
    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar a URL do AS: {e}")

def main():
    entrada = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite Nome do Website (exemplo: example.com): ").strip()
    
    # Verifica se é um número AS
    if entrada.startswith("AS") and entrada[2:].isdigit():
        as_number = entrada[2:]
        obter_informacoes_as(as_number)
    else:
        if not entrada.startswith(('http://', 'https://')):
            url = 'https://' + entrada
        else:
            url = entrada

        # Executa as consultas WHOIS
        obter_whois(entrada)
        if re.search(r'\.br$', entrada):
            obter_whois_br(entrada)
        if re.search(r'\.gov$', entrada):
            obter_whois_gov(entrada)
        
        # Verifica redirecionamentos e informações adicionais do domínio
        verificar_open_redirect(url)
        obter_informacoes_dominio(entrada)

    input(Fore.LIGHTRED_EX + "========== PRESSIONE ENTER PARA SAIR ==========\n\n")

if __name__ == "__main__":
    main()
