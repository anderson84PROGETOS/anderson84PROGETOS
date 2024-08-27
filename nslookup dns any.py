import subprocess
import re
import dns.resolver
from socket import gethostbyname, gaierror

print("""

███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗     ██████╗ ███╗   ██╗███████╗     █████╗ ███╗   ██╗██╗   ██╗
████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗    ██╔══██╗████╗  ██║██╔════╝    ██╔══██╗████╗  ██║╚██╗ ██╔╝
██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝    ██║  ██║██╔██╗ ██║███████╗    ███████║██╔██╗ ██║ ╚████╔╝ 
██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝     ██║  ██║██║╚██╗██║╚════██║    ██╔══██║██║╚██╗██║  ╚██╔╝  
██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║         ██████╔╝██║ ╚████║███████║    ██║  ██║██║ ╚████║   ██║   
╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝         ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   

""")

def nslookup_query(domain, query_type, dns_server=None):
    try:
        command = ['nslookup', f'-type={query_type}', domain]
        if dns_server:
            command.append(dns_server)
        
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout
        
        # Filtra as linhas que contêm "Servidor:" ou "Address:"
        filtered_output = "\n".join(
            line for line in output.splitlines() if not line.startswith("Servidor:") and not line.startswith("Address:")
        )
        
        print(filtered_output)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def get_mx_ip(domain):
    try:
        # Remove o esquema http/https
        domain = re.sub(r'^https?://', '', domain)
        
        # Obtém o registro MX do domínio
        answers = dns.resolver.resolve(domain, 'MX')
        mx_record = answers[0].exchange.to_text()
        print("\n===========================================================================================")
        
        # Obtém o IP do servidor MX
        real_ip = gethostbyname(mx_record)
        print(f"\n\n\nMX do domínio: {domain}   \n\nO IP Real Do Servidor É: {real_ip}")
        
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print("\nNenhum registro MX encontrado ou domínio não existe.")
    except gaierror as e:
        print(f"Erro ao tentar obter o IP: {e}")

def main():
    domain = input("\nDigite o nome do domínio: ")
    print("")
    # Consulta de registros NS
    nslookup_query(domain, 'ns')
    print("")
    
    # Consulta de registros ANY
    dns_server = input("\nDigite o servidor DNS (Ex: ns1.businesscorp.com.br): ")
    print("")        
    if dns_server:
        nslookup_query(domain, 'any', dns_server)
    else:
        nslookup_query(domain, 'any')
    
    # Obtém o IP real do servidor MX
    get_mx_ip(domain)

if __name__ == "__main__":
    main()
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
