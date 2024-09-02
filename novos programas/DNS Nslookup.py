import subprocess
import re
import dns.resolver
from socket import gethostbyname, gaierror

print("""

██████╗ ███╗   ██╗███████╗    ███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
██║  ██║██╔██╗ ██║███████╗    ██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
██║  ██║██║╚██╗██║╚════██║    ██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝ 
██████╔╝██║ ╚████║███████║    ██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║     
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                                                                  
""")

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def get_mx_ips(website):
    try:
        website = re.sub(r'^https?://', '', website)
        answers = dns.resolver.resolve(website, 'MX')

        mx_records = []
        for answer in answers:
            mx_record = answer.exchange.to_text().rstrip('.')  # Remove o ponto final
            real_ip = gethostbyname(mx_record)
            mx_records.append((mx_record, real_ip))
            print(f"\n\nMX do Domínio: {website}\n==============================================\nServidor: {mx_record} \nO IP Real do Servidor é: {real_ip}\n")
            
        return mx_records
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print("\nNenhum registro MX encontrado ou domínio não existe.")
        return None
    except gaierror as e:
        print(f"Erro ao tentar obter o IP: {e}")
        return None

def main():
    site = input("\nDigite o nome do WebSite: ")
    ipv4_addresses = get_ipv4_addresses(site)
    mx_records = get_mx_ips(site)

    if ipv4_addresses:
        print("\nEndereços IPv4 Encontrados\n==========================")
        for ipv4_address in ipv4_addresses:
            print(ipv4_address)
    else:
        print("\nNenhum endereço IPv4 encontrado.")

    save_option = input("\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if save_option == 's':
        file_name = input("\nDigite o nome do arquivo para salvar (EX: arquivo.txt): ")
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(f"Endereços IPv4 Encontrados do site: {site}\n\n")
            for ipv4_address in ipv4_addresses:
                file.write(ipv4_address + "\n")
            if mx_records:
                file.write("\n\nRegistros MX\n============\n")
                for mx_record, mx_ip in mx_records:
                    file.write(f"{mx_record} - IP: {mx_ip}\n")
        print(f"\nOs resultados foram salvos no arquivo: {file_name}")

if __name__ == "__main__":
    main()
    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
