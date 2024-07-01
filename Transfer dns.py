import subprocess
import dns.resolver

print("""


████████╗██████╗  █████╗ ███╗   ██╗███████╗███████╗███████╗██████╗     ██████╗ ███╗   ██╗███████╗
╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔════╝
   ██║   ██████╔╝███████║██╔██╗ ██║███████╗█████╗  █████╗  ██████╔╝    ██║  ██║██╔██╗ ██║███████╗
   ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██╔══╝  ██╔══╝  ██╔══██╗    ██║  ██║██║╚██╗██║╚════██║
   ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║     ███████╗██║  ██║    ██████╔╝██║ ╚████║███████║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                                                  
""")

def dns_enum(domain):
    result = []
    try:
        answers = dns.resolver.resolve(domain, 'A')
        result.append("\n\nHost's addresses\n================\n")
        for answer in answers:
            result.append(f"{domain: <40} {'IN A': <10} IP: {answer.address}\n")
    except dns.resolver.NoAnswer:
        result.append(f"[!] Nenhum registro A encontrado para {domain}.\n")
    except dns.resolver.NXDOMAIN:
        result.append(f"[!] O domínio {domain} não foi encontrado.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")
    
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        result.append(f"\n\nMail (MX) Servers\n=================\n")
        if answers:
            for answer in answers:
                result.append(f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {dns.resolver.resolve(answer.exchange, 'A')[0].address}\n")
        else:
            result.append(f"[!] Nenhum registro MX encontrado para {domain}.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        result.append(f"\n\nName Servers\n===============\n")
        for answer in answers:
            result.append(f"{answer.target.to_text(): <40} {'IN NS': <10} IP: {dns.resolver.resolve(answer.target, 'A')[0].address}\n")
    except dns.resolver.NoAnswer:
        result.append(f"[!] Nenhum registro NS encontrado para {domain}.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

    return result

def dns_transfer(site):
    result = []
    result.append(f"\n\n\nTransferência de Zona DNS\n=========================\n")
    
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    result.append(f"\nSaída de: nslookup -query=ns {site}\n\n")
    result.append(output_dns.stdout)
    
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]
    result.append(f"\nServidores DNS Encontrados\n==========================\n")
    for server in servers:
        result.append(f"{server}\n")
    
    unique_outputs = set()
    
    for server in servers:
        output_mx = subprocess.run(['nslookup', '-type=mx', site, server], capture_output=True, text=True)
        result.append(f"\nSaída de: nslookup -type=mx {site} {server}\n\n")
        result.append(output_mx.stdout)
        
        filtered_lines_mx = [line for line in output_mx.stdout.splitlines() if "mail exchanger" in line]
        unique_outputs.add("\n".join(filtered_lines_mx))
        
        output_ns = subprocess.run(['nslookup', site, server], capture_output=True, text=True)
        result.append(f"\nSaída de: nslookup {site} {server}\n\n")
        result.append(output_ns.stdout)
        
        filtered_lines_ns = [line for line in output_ns.stdout.splitlines() if "name =" in line]
        unique_outputs.add("\n".join(filtered_lines_ns))
        
        for ns_line in filtered_lines_ns:
            ns_name = ns_line.split("name =")[-1].strip()
            if ns_name:
                output_ip = subprocess.run(['nslookup', ns_name], capture_output=True, text=True)
                result.append(f"\nSaída de: nslookup {ns_name}\n\n")
                result.append(output_ip.stdout)
                
                filtered_lines_ip = [line for line in output_ip.stdout.splitlines() if "Address" in line]
                unique_outputs.add("\n".join(filtered_lines_ip))    

    return result

def execute_dns_operations(url):
    site = url.replace('http://', '').replace('https://', '').split('/')[0]
    
    dns_enum_result = dns_enum(site)
    dns_transfer_result = dns_transfer(site)
    
    print("\n".join(dns_enum_result))
    print("\n".join(dns_transfer_result))

if __name__ == "__main__":
    url = input("Digite o nome do website ou a URL do website: ")
    execute_dns_operations(url)

input("\n\n============ PRESSIONE ENTER PARA SAIR =========\n")
