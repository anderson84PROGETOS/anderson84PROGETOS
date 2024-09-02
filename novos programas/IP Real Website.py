import re
import dns.resolver
from socket import gethostbyname, gaierror

print("""

██╗██████╗     ██████╗ ███████╗ █████╗ ██╗         ██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗
██║██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██║         ██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝
██║██████╔╝    ██████╔╝█████╗  ███████║██║         ██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗  
██║██╔═══╝     ██╔══██╗██╔══╝  ██╔══██║██║         ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝  
██║██║         ██║  ██║███████╗██║  ██║███████╗    ╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗
╚═╝╚═╝         ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝
                                                                                                        
""")

def get_mx_ips(website):
    try:
        # Remove o esquema HTTP/HTTPS do domínio, se presente
        website = re.sub(r'^https?://', '', website)
        
        # Resolve os registros MX
        answers = dns.resolver.resolve(website, 'MX')
        
        # Lista para armazenar IPs dos servidores MX
        mx_ips = []

        # Itera sobre todos os registros MX encontrados
        for rdata in answers:
            mx_record = rdata.exchange.to_text().rstrip('.')
            try:
                # Obtém o IP do servidor MX
                real_ip = gethostbyname(mx_record)
                mx_ips.append((mx_record, real_ip))
            except gaierror as e:
                print(f"\nErro ao tentar obter o IP para o servidor MX: {mx_record} {e}")

        if mx_ips:
            print(f"\nIP dos servidores MX do website: {website}")
            print("")
            for mx_record, ip in mx_ips:
                print(f"Servidor MX: {mx_record:<25}    IP: {ip}")
        else:
            print(f"\nNenhum registro MX encontrado para o domínio '{website}'.")
        
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print("\nNenhum registro MX encontrado ou domínio não existe.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    website = input("\nDigite o nome do website (ex: example.com): ")
    print("")
    get_mx_ips(website)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
