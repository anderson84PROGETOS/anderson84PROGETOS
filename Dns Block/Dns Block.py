import dns.resolver
import ipaddress
import subprocess
from colorama import Fore, Style, init

# Inicializa o Colorama para suportar cores no terminal
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
██║  ██║██╔██╗ ██║███████╗    ██████╔╝██║     ██║   ██║██║     █████╔╝ 
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ 
██████╔╝██║ ╚████║███████║    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
""")

# Realiza uma consulta DNS para o domínio fornecido e tipo de registro (A, MX, TXT).
def dns_query(domain, record_type):
    try:
        answers = dns.resolver.resolve(domain, record_type)
        results = [rdata.to_text() for rdata in answers]
        return results
    except dns.resolver.NoAnswer:
        return [f"No {record_type} record found for {domain}."]

    except dns.resolver.NXDOMAIN:
        return [f"Domain {domain} does not exist."]
    except Exception as e:
        return [f"Error querying {record_type} records for {domain}: {e}"]

# Usa o curl para pegar o nome do servidor de um IP
def reverse_lookup(ip):
    try:
        result = subprocess.run(["curl", "-I", f"http://{ip}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        headers = result.stdout
        # Busca o cabeçalho "Server" nos dados retornados
        for line in headers.splitlines():
            if "Server:" in line:
                return line.split(":")[1].strip()
        return None  # Retorna None se o servidor não for encontrado
    except Exception as e:
        return None  # Em caso de erro, retorna None

# Filtra os registros TXT para encontrar apenas aqueles que contêm a palavra-chave fornecida.
def filter_txt_records(txt_records, keyword):
    return [record for record in txt_records if keyword in record]

# Processa um intervalo de endereços IP (CIDR) e retorna uma lista de IPs.
def process_ip_range(ip_range):
    try:
        network = ipaddress.ip_network(ip_range, strict=False)
        return [str(ip) for ip in network]
    except ValueError as e:
        print(Fore.LIGHTRED_EX + f"Invalid IP range: {e}")
        return []

# Resolve o hostname para um endereço IP.
def resolve_hostname_to_ip(hostname):
    try:
        answers = dns.resolver.resolve(hostname, 'A')
        return [answer.to_text() for answer in answers]
    except Exception:
        return []

def save_ips_to_file(ip_list):
    save = input(Fore.LIGHTMAGENTA_EX + "\nDeseja salvar os IP (S/N): ").strip().lower()
    if save == 's':
        filename = input(Fore.LIGHTGREEN_EX + "\nDigite o nome do arquivo para salvar os IP (exemplo: ip.txt): ").strip()
        with open(filename, 'w') as file:
            for ip in ip_list:
                file.write(ip + '\n')
        print(Fore.LIGHTCYAN_EX + f"\nIP salvos com sucesso no arquivo: {filename}")
    else:
        print(Fore.LIGHTCYAN_EX + "\nIP não salvos.")

def main():
    # Domínio para consulta
    domain = input(Fore.LIGHTGREEN_EX + "\nDigite o domínio para consultas DNS: ")

    # Consultar registros A e realizar resolução reversa
    print(Fore.LIGHTMAGENTA_EX + f"\nConsultando registros A para: {domain}\n")
    a_records = dns_query(domain, "A")
    for record in a_records:
        server_name = reverse_lookup(record)
        print(Fore.LIGHTMAGENTA_EX + f"A: {record:<22} Servidor: {server_name if server_name else ''}")

    # Consultar registros MX e resolver seus IPs
    print(Fore.LIGHTRED_EX + f"\nConsultando registros MX para: {domain}\n")
    mx_records = dns_query(domain, "MX")
    for record in mx_records:
        priority, mail_server = record.split()
        ips = resolve_hostname_to_ip(mail_server)
        ip_list = ", ".join(ips) if ips else "N/A"
        
        # Apenas exibe o nome do servidor se estiver disponível
        server_name = reverse_lookup(ips[0]) if ips else None
        if server_name:
            print(Fore.LIGHTRED_EX + f"MX: {mail_server:<30} IP: {ip_list:<15} Servidor: {server_name}")
        else:
            print(Fore.LIGHTRED_EX + f"MX: {mail_server:<30} IP: {ip_list}")

    # Consultar registros TXT e filtrar por 'ip4'
    txt_records = dns_query(domain, "TXT")
    keyword = "ip4:"
    filtered_txt = filter_txt_records(txt_records, keyword)

    # Exibir registros TXT filtrados apenas se houver
    if filtered_txt:
        print(Fore.LIGHTYELLOW_EX + f"\nConsultando registros TXT para: {domain}")
        print(Fore.LIGHTYELLOW_EX + "\nRegistros TXT filtrados ip4\n")
        for record in filtered_txt:
            print(Fore.LIGHTYELLOW_EX + record)

        # Solicitar o intervalo de IPs apenas se houver registros TXT
        ip_range = input(Fore.LIGHTGREEN_EX + "\nDigite o intervalo de IPs (v=spf1 ip4: 200.196.144.0/20): ")
        ip_list = process_ip_range(ip_range)

        print(Fore.LIGHTCYAN_EX + f"\nEndereços IP no intervalo: {ip_range}\n")
        for ip in ip_list:
            print(Fore.LIGHTGREEN_EX + ip)

        # Perguntar se deseja salvar os IPs
        save_ips_to_file(ip_list)
            
    # Finalização
    input(Fore.LIGHTRED_EX + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")

if __name__ == "__main__":
    main()
