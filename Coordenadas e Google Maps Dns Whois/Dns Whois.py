import dns.resolver
import requests
import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝
██║  ██║██╔██╗ ██║███████╗    ██║ █╗ ██║███████║██║   ██║██║███████╗
██║  ██║██║╚██╗██║╚════██║    ██║███╗██║██╔══██║██║   ██║██║╚════██║
██████╔╝██║ ╚████║███████║    ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║
╚═════╝ ╚═╝  ╚═══╝╚══════╝     ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝
                                                                                                                                                             
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
                mx_ip = dns.resolver.resolve(answer.exchange, 'A')[0].address
                result.append(f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {mx_ip}\n")
        else:
            result.append(f"[!] Nenhum registro MX encontrado para {domain}.\n")
    except Exception as e:
        result.append(f"[!] Ocorreu um erro ao consultar DNS para {domain}: {e}\n")

    try:
        answers = dns.resolver.resolve(domain, 'NS')
        result.append(f"\n\nName Servers\n=============\n")
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

def main():
    domain = input("\nDigite o nome do domínio (ex: example.com): ").strip()
    dns_results = dns_enum(domain)
    for result in dns_results:
        print(result)    
    
    # Realiza a consulta Whois para todos os endereços IP associados ao domínio
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

    # Realiza a transferência de zona DNS    
    transfer_results = dns_transfer(domain)
    is_transfer_header_printed = False  # Variável para controlar se o cabeçalho já foi impresso
    for result in transfer_results:
        if "Transferência de Zona DNS\n=========================" in result:
            if not is_transfer_header_printed:
                print(result)  # Mostra apenas uma vez a linha de cabeçalho
                is_transfer_header_printed = True
        else:
            print(result)
    
    # Pergunta ao usuário se deseja salvar os resultados em um arquivo
    save_results = input("\nDeseja salvar todos os resultados em um arquivo? (s/n): ").strip().lower()
    if save_results == 's':
        file_name = input("\nDigite o nome do arquivo (ex: resultados.txt): ").strip()
        with open(file_name, 'w', encoding='utf-8') as file:
            # Salvando os resultados DNS
            file.write(f"Resultados Para o Dominio: {domain}\n")
            for line in dns_results:
                file.write(line)

            # Salvando os resultados Whois
            file.write("\n\nConsultando Whois Para IP\n=========================\n")
            for result in whois_results:
                file.write(f"\nWhois IP Result: {result['ip']}\n\n")
                file.write(result['info'] + "\n\n")

            # Salvando os resultados de transferência de zona DNS            
            for result in transfer_results:
                if "Transferência de Zona DNS\n=========================" in result:
                    file.write(result + "\n")  # Escreve apenas uma vez a linha de cabeçalho
                else:
                    file.write(result + "\n")

        print(f"\nResultados Salvos em: {file_name}")

    input("\n\nPRESSIONE ENTER PARA SAIR\n==========================\n")

if __name__ == "__main__":
    main()
