import subprocess
import re
import requests
import ipaddress
from bs4 import BeautifulSoup
from socket import *
from colorama import Fore, Style, init
from datetime import datetime

# Inicializa o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + Style.BRIGHT + """
    ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
    ██║ █╗ ██║███████║██║   ██║██║███████╗    ██████╔╝██║     ██║   ██║██║     █████╔╝ 
    ██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ 
    ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
     ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
""")

# Servidores WHOIS
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

# Traduções completas WHOIS Registro.br
traducoes_completas = {
    "domain": "Domínio",
    "owner": "Titular",
    "ownerid": "Documento CNPJ",
    "responsible": "Responsável",
    "country": "País",
    "phone": "Telefone",
    "owner-c": "Titular-c",
    "tech-c": "Tecnologia-c",
    "nserver": "Servidor DNS",
    "nsstat": "Status DNS",
    "nslastaa": "Última verificação DNS",
    "dsrecord": "Registro DS",
    "dsstatus": "Status DS",
    "dslastok": "Último DSOK",
    "created": "Criado",
    "changed": "Alterado",
    "expires": "Expiração",
    "status": "Status",
    "nic-hdl-br": "NIC-hdl",   
    "person": "Pessoa Nome",
    "e-mail": "E-mail",    
    "registrar": "Registrador",
    "contact": "Contato",
    "saci": "SACI",
    "tech": "Contato Técnico",
    "admin-c": "Contato Administrativo",
    "billing-c": "Contato Financeiro",
    "org": "Organização",
    "address": "Endereço",
    "postalcode": "CEP",
    "city": "Cidade",
    "state": "Estado",
    "remarks": "Observações",
    "remark": "Observações",
    "statusmsg": "Mensagem de Status",
    "ref": "Referência",
    "registrar-url": "Site do Registrador",
    "registrant-type": "Tipo de Registrante",
    "inetnum": "Bloco de IP (inetnum)",
    "aut-num": "ASN (aut-num)",
    "abuse-c": "Contato de Abuso (abuse-c)"
}

# Regex para detectar datas
regex_datas = re.compile(r'(\b\d{8}\b|\b\d{4}-\d{2}-\d{2}\b)')

def formatar_datas_em_linha(linha):
    """Formata datas de YYYYMMDD ou YYYY-MM-DD para DD/MM/YYYY"""
    def substituir(match):
        data_str = match.group(0)
        formatos = ["%Y%m%d", "%Y-%m-%d"]
        for fmt in formatos:
            try:
                dt = datetime.strptime(data_str, fmt)
                return dt.strftime("%d/%m/%Y")
            except:
                continue
        return data_str
    return regex_datas.sub(substituir, linha)

def traduzir_whois_br(conteudo):
    """Traduz WHOIS do Registro.br e aplica alinhamento com :<30"""
    linhas = conteudo.splitlines()
    resultado = []
    for linha in linhas:
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            chave_limpa = chave.strip().lower()
            traducao = traducoes_completas.get(chave_limpa, chave.strip())
            valor = formatar_datas_em_linha(valor.strip())
            if chave_limpa == "inetnum":
                valor = f"{valor}"
            # Alinhamento :<35 mantendo as cores originais
            resultado.append(f"{Fore.LIGHTYELLOW_EX}{traducao:<35}{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{valor}")
        else:
            resultado.append(Fore.WHITE + linha)
    return "\n".join(resultado)

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout

def get_mx_records(domain):
    nslookup_command = f'nslookup -query=mx {domain} | findstr "mail exchanger"'
    return run_command(nslookup_command)

def ping_host(host):
    ping_command = f'ping -4 -n 1 {host}'
    return run_command(ping_command)

def obter_ip_do_ping(ping_output):
    ip_regex = re.compile(r'\[(\d+\.\d+\.\d+\.\d+)\]')
    match = ip_regex.search(ping_output)
    if match:
        return match.group(1)
    return None

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
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
    objeto_socket.close()
    return resultado

def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resultado = requisicao_whois(servidor_whois, endereco, False)
    linhas_filtradas = [linha for linha in resultado.splitlines() if not linha.startswith('%')]
    resultado_filtrado = '\n'.join(linhas_filtradas)
    traduzido = traduzir_whois_br(resultado_filtrado)
    print("\n" + traduzido + "\n")

    # >>> NOVO: opção para salvar o WHOIS traduzido em arquivo
    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar o WHOIS em um arquivo? (s/n): ")
    if salvar.lower() == 's':
        nome_arquivo = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar o WHOIS: ")
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write(re.sub(r'\x1b\[[0-9;]*m', '', traduzido))  # remove as cores ANSI
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nWHOIS salvo com sucesso em: {nome_arquivo}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar WHOIS: {e}\n")

def consulta_whois(endereco):
    obter_whois_br(endereco)

def list_subnet_ips(subnet):
    try:
        network = ipaddress.ip_network(subnet)
    except ValueError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: Insira um bloco de IP válido. Exemplo: 200.196.144.0/20\n")
        return

    print(Fore.LIGHTGREEN_EX + "\nEndereços IP disponíveis na sub-rede\n")
    ips = []

    for ip in network.hosts():
        ips.append(str(ip))
        print(Fore.LIGHTYELLOW_EX + str(ip))

    save = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar os IP em um arquivo? (s/n): ")
    if save.lower() == 's':
        filename = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar os IP: ")
        try:
            with open(filename, 'w') as f:
                for ip in ips:
                    f.write(ip + '\n')
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nIP salvos no arquivo: {filename}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar os IP no arquivo: {e}\n")

def main():    
    domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nDigite o nome do Website: ")
    print()    
    mx_records = get_mx_records(domain)   
    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nRegistros MX para website: {domain}\n")
    
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()
            ping_result = ping_host(mx_host)
            ip_address = obter_ip_do_ping(ping_result)
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{domain}     MX = {mx_host}    IP: {ip_address}")
    
    for line in mx_records.splitlines():
        if "mail exchanger" in line:
            mx_host = line.split('=')[-1].strip()
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n\nPinging no website: {mx_host}\n")
            ping_result = ping_host(mx_host)
            ip_address = obter_ip_do_ping(ping_result)
            if ip_address:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Consultando WHOIS para IP: {ip_address}\n")
                consulta_whois(ip_address)
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNão foi possível obter o IP do host: {mx_host}\n")

    subnet = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o bloco de IP do inetnum: (exemplo: 200.196.144.0/20): ")
    list_subnet_ips(subnet)

if __name__ == "__main__":
    main()

input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
