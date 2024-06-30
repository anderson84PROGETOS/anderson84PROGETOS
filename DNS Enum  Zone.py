import subprocess
import dns.resolver

print("""
    
██████╗ ███╗   ██╗███████╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗        ███████╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██╔════╝████╗  ██║██║   ██║████╗ ████║        ╚══███╔╝██╔═══██╗████╗  ██║██╔════╝
██║  ██║██╔██╗ ██║███████╗    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║          ███╔╝ ██║   ██║██╔██╗ ██║█████╗  
██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║         ███╔╝  ██║   ██║██║╚██╗██║██╔══╝  
██████╔╝██║ ╚████║███████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║        ███████╗╚██████╔╝██║ ╚████║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝        ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                               

""")
def dns_enum(domain):
    try:
        answers = dns.resolver.resolve(domain, 'A')
        print("\n\n\nHost's addresses")
        print("================")
        for answer in answers:
            print(f"{domain: <40} {'IN A': <10} IP: {answer.address}")
    except dns.resolver.NoAnswer:
        print(f"[!] Nenhum registro A encontrado para {domain}.")
    except dns.resolver.NXDOMAIN:
        print(f"[!] O domínio {domain} não foi encontrado.")
    except Exception as e:
        print(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}")
    
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        print(f"\n\nMail (MX) Servers")
        print("=================")
        if answers:
            for answer in answers:
                print(f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {dns.resolver.resolve(answer.exchange, 'A')[0].address}")
        else:
            print(f"[!] Nenhum registro MX encontrado para {domain}.")
    except Exception as e:
        print(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        print(f"\n\nName Servers")
        print("=================")
        for answer in answers:
            print(f"{answer.target.to_text(): <40} {'IN NS': <10} IP: {dns.resolver.resolve(answer.target, 'A')[0].address}")
    except dns.resolver.NoAnswer:
        print(f"[!] Nenhum registro NS encontrado para {domain}.")
    except Exception as e:
        print(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}")

def dns_transfer(site):
    print("\n\n\n========== Transferência de Zona DNS ==========\n")
    
    # Executa o comando 'nslookup' e captura a saída
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    print("Saída de nslookup -query=ns:")
    print(output_dns.stdout)
    
    # Divide a saída em linhas e extrai os servidores DNS
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]
    print("\n========== Servidores DNS Encontrados ==========\n")
    for server in servers:
        print(server)
    
    # Conjunto para armazenar e verificar duplicatas de saída
    unique_outputs = set()
    
    # Itera sobre cada servidor DNS e executa o comando 'nslookup -type=mx' e 'nslookup -type=a'
    for server in servers:
        # Consulta MX records
        output_mx = subprocess.run(['nslookup', '-type=mx', site, server], capture_output=True, text=True)
        print(f"\nSaída de nslookup -type=mx {site} {server}:")
        print(output_mx.stdout)
        
        filtered_lines_mx = [line for line in output_mx.stdout.splitlines() if "mail exchanger" in line]
        unique_outputs.add("\n".join(filtered_lines_mx))
        
        # Consulta A records para nameserver
        output_ns = subprocess.run(['nslookup', site, server], capture_output=True, text=True)
        print(f"\nSaída de nslookup {site} {server}:")
        print(output_ns.stdout)
        
        filtered_lines_ns = [line for line in output_ns.stdout.splitlines() if "name =" in line]
        unique_outputs.add("\n".join(filtered_lines_ns))
        
        # Consulta A records para IP address dos nameservers
        for ns_line in filtered_lines_ns:
            ns_name = ns_line.split("name =")[-1].strip()
            if ns_name:
                output_ip = subprocess.run(['nslookup', ns_name], capture_output=True, text=True)
                print(f"\nSaída de nslookup {ns_name}:")
                print(output_ip.stdout)
                
                filtered_lines_ip = [line for line in output_ip.stdout.splitlines() if "Address" in line]
                unique_outputs.add("\n".join(filtered_lines_ip))
    
    # Imprime a saída única do nslookup na tela
    print("\n\n================= Saída Única =================\n")
    for output in unique_outputs:
        print(output)

# Solicita a URL do usuário e executa as funções DNS
url = input("\nDigite a URL do website: ")
site = url.replace('http://', '').replace('https://', '').split('/')[0]

dns_enum(site)
dns_transfer(site)

input("\n\n============ PRESSIONE ENTER PARA SAIR =========\n")
