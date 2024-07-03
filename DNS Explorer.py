import dns.resolver
import dns.query
import dns.zone
import requests
import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ███████╗██╗  ██╗██████╗ ██╗      ██████╗ ██████╗ ███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ██╔════╝╚██╗██╔╝██╔══██╗██║     ██╔═══██╗██╔══██╗██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗    █████╗   ╚███╔╝ ██████╔╝██║     ██║   ██║██████╔╝█████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║    ██╔══╝   ██╔██╗ ██╔═══╝ ██║     ██║   ██║██╔══██╗██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║    ███████╗██╔╝ ██╗██║     ███████╗╚██████╔╝██║  ██║███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                               
""")

def dns_enum(domain):
    result = []
    try:
        answers = dns.resolver.resolve(domain, 'A')
        result.append("\n\nEndereços do Host (A)\n=====================\n")
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
        result.append(f"\n\nServidores de Email (MX)\n========================\n")
        if answers:
            for answer in answers:
                mx_ip = dns.resolver.resolve(answer.exchange, 'A')[0].address
                result.append(f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {mx_ip}\n")
        else:
            result.append(f"[!] Nenhum registro MX encontrado para {domain}.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        result.append(f"\n\nServidores de Nomes (NS)\n========================\n")
        for answer in answers:
            ns_ip = dns.resolver.resolve(answer.target, 'A')[0].address
            result.append(f"{answer.target.to_text(): <40} {'IN NS': <10} IP: {ns_ip}\n")
    except dns.resolver.NoAnswer:
        result.append(f"[!] Nenhum registro NS encontrado para {domain}.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")
    
    return result

# Realiza a consulta Whois
def whois_query(ip):
    try:
        url = f"https://ipwhois.app/json/{ip}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Consulta Whois falhou para {ip}: {e}")
        return None

def format_whois_info(info):
    if not info:
        return "Nenhuma informação Whois disponível."
    formatted_info = ""
    for key, value in info.items():
        formatted_info += f"{key}: {value}\n"
    return formatted_info

def dns_transfer(site):
    result = []
    result.append(f"\n\nTransferência de Zona DNS\n=========================\n")
    
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    result.append(f"\nSaída de: nslookup -query=ns {site}\n\n")
    result.append(output_dns.stdout)
    
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]
    result.append(f"\n\nServidores DNS Encontrados\n==========================\n")
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

def get_dns_records(domain):
    result = []
    result.append(f"\n\nDetalhamento dos Registros DNS para: {domain}\n====================================\n")

    # Get SOA record
    try:
        soa_record = dns.resolver.resolve(domain, 'SOA')
        for soa in soa_record:
            result.append(f"[SOA]      SOA {soa.mname} {soa.serial}\n")
    except Exception as e:
        result.append(f"[SOA]      SOA record not found for {domain}: {e}\n")

    # Get NS records
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        for ns in ns_records:
            ns_ip = dns.resolver.resolve(ns.target, 'A')[0].address
            result.append(f"[NS ]      NS {ns.target} {ns_ip}\n")
    except Exception as e:
        result.append(f"[NS ]      NS records not found for {domain}: {e}\n")

    # Get MX records
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        for mx in mx_records:
            mx_ip = dns.resolver.resolve(mx.exchange, 'A')[0].address
            result.append(f"[MX ]      MX {mx.exchange} {mx_ip}\n")
    except Exception as e:
        result.append(f"[MX ]      MX records not found for {domain}: {e}\n")

    # Get A records
    try:
        a_records = dns.resolver.resolve(domain, 'A')
        for a in a_records:
            result.append(f"[A  ]      A {domain} {a.address}\n")
    except Exception as e:
        result.append(f"[A  ]      A records not found for {domain}: {e}\n")

    # Get HINFO records
    try:
        hinfo_records = dns.resolver.resolve(domain, 'HINFO')
        for hinfo in hinfo_records:
            result.append(f"[HIN]      HINFO {hinfo.cpu} {hinfo.os}\n")
    except Exception as e:
        result.append(f"[HIN]      HINFO records not found for {domain}: {e}\n")

    # Get TXT records
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for txt in txt_records:
            result.append(f"[TXT]      TXT {domain} {txt.strings}\n")
    except Exception as e:
        result.append(f"[TXT]      TXT records not found for {domain}: {e}\n")        

    # Get SRV records for common services
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0].address
                result.append(f"[SRV]      SRV {srv_domain} {srv.target} {srv_ip} {srv.port}\n")
        except Exception as e:
            result.append(f"[SRV]      SRV records not found for {srv_domain}: {e}\n")    

    return result

def main():
    domain = input("\nDigite o nome do domínio (ex: example.com): ").strip()

    # Resultados da enumeração DNS
    dns_results = dns_enum(domain)
    for result in dns_results:
        print(result)
    
    # Resultados das consultas Whois para todos os endereços IP associados ao domínio
    print("\n\nConsultando Whois para IP\n=========================\n")
    addresses = [line.split()[-1] for line in dns_results if 'IP:' in line]
    whois_results = []
    for addr in addresses:
        print(f"\nConsulta Whois para IP: {addr}\n")
        whois_info = whois_query(addr)
        formatted_info = format_whois_info(whois_info)
        print(formatted_info)
        whois_results.append({'ip': addr, 'info': formatted_info})
        print()
    
    # Resultados da transferência de zona DNS
    transfer_results = dns_transfer(domain)
    is_transfer_header_printed = False  # Variável para controlar se o cabeçalho já foi impresso
    for result in transfer_results:
        if not is_transfer_header_printed:
            print(result)
            is_transfer_header_printed = True
        else:
            print(result, end='')  # Imprime sem adicionar nova linha ao final
    
    # Resultados da função get_dns_records(domain)
    dns_records = get_dns_records(domain)
    for record in dns_records:
        print(record)

    # Opção para salvar todos os resultados em um arquivo
    save_option = input("\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if save_option == 's':
        file_name = input("\nDigite o nome do arquivo (ex: resultados.txt): ").strip()
        with open(file_name, 'w', encoding='utf-8') as file:
            # Salvando os resultados DNS
            file.write(f"Resultados Para o Dominio: {domain}\n")
            for result in dns_results:
                file.write(result)
            file.write("\n\nConsultando Whois para IP\n=========================\n")
            for whois_result in whois_results:
                file.write(f"\nConsulta Whois para IP: {whois_result['ip']}\n")
                file.write(whois_result['info'])
                file.write("\n")
            
            for result in transfer_results:
                file.write(result)
            
            for record in dns_records:
                file.write(record)
        print(f"\nResultados Salvos Em: {file_name}")
        
    input("\n\nPRESSIONE ENTER PARA SAIR\n==========================\n")
if __name__ == "__main__":
    main()
