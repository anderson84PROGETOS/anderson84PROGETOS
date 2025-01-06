import dns.resolver
import socket
import requests
from ipwhois import IPWhois
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ██████╗ ███████╗███████╗ ██████╗ ██╗     ██╗   ██╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔═══██╗██║     ██║   ██║██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗    ██████╔╝█████╗  ███████╗██║   ██║██║     ██║   ██║█████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══╝  ╚════██║██║   ██║██║     ╚██╗ ██╔╝██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║    ██║  ██║███████╗███████║╚██████╔╝███████╗ ╚████╔╝ ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
""")

def get_records(domain, record_type):
    try:
        answers = dns.resolver.resolve(domain, record_type)
        if record_type == "TXT":
            return [str(answer) for answer in answers if "v=spf1" in str(answer)]
        return [str(answer) for answer in answers]
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:        
        return []
    except Exception as e:        
        return []

def get_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return "não Encontrado"

def get_ip_details(ip):
    try:
        # Faz a solicitação GET para a API ip-api.com
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()

        provider = data.get('org', 'N/A')  # Recuperando a organização da resposta
        asn = data.get('as', 'N/A')
        organization = data.get('country', 'N/A')  # País como uma "organização" no contexto do IP

        return provider, asn, organization
    except Exception as e:        
        return "N/A", "N/A", "N/A"

def get_srv_records(domain):
    srv_services = [
        '_sip._tcp', '_sip._udp', '_sips._tcp',
        '_h323cs._tcp', '_h323ls._udp', '_sip._tls'
    ]
    srv_results = []
    for service in srv_services:
        try:
            full_service = f"{service}.{domain}"
            answers = dns.resolver.resolve(full_service, 'SRV')
            for answer in answers:
                srv_results.append(str(answer))
        except dns.resolver.NoAnswer:
            continue
        except Exception as e:            
            continue
    return srv_results

def get_ns_ip(ns_record):
    ns_ip = get_ip(ns_record.strip('.'))
    return ns_ip

def main():
    domain = input(Fore.LIGHTMAGENTA_EX + "\nDigite o domínio (exemplo: businesscorp.com.br): ").strip()
    record_types = ['A', 'MX', 'NS', 'HINFO', 'SOA', 'TXT']

    for record_type in record_types:
        records = get_records(domain, record_type)
        if records:
            print(Fore.LIGHTYELLOW_EX + f"\n\nRegistros {record_type} para: {domain}\n")
            for record in records:
                if record_type == 'A':
                    ip = record
                    provider, asn, organization = get_ip_details(ip)
                    print(Fore.LIGHTYELLOW_EX + f"IP: {ip}")
                    print(Fore.LIGHTGREEN_EX + f"Provedor: {provider}  ASN: {asn}   País: {organization}\n")

                elif record_type == 'MX':
                    mx_host = record.split()[1].strip('.')
                    mx_ip = get_ip(mx_host)
                    print(Fore.LIGHTGREEN_EX + f"{mx_host:<25}     IP: {mx_ip}")
                elif record_type == 'NS':
                    ns_host = record.strip('.')
                    ns_ip = get_ns_ip(ns_host)
                    print(Fore.LIGHTGREEN_EX + f"{ns_host:<25}     IP: {ns_ip}")
                elif record_type == 'SOA':
                    soa_parts = record.split()
                    soa_host = soa_parts[0].strip('.')
                    soa_ip = get_ip(soa_host)
                    soa_details = " ".join(soa_parts[1:])
                    print(Fore.LIGHTGREEN_EX + f"[SOA]  {soa_host}  {soa_details}   IP: {soa_ip}")
                elif record_type == 'TXT':
                    if "v=spf1" in record:
                        print(Fore.LIGHTGREEN_EX + f"[TXT]  {record}")
                else:
                    print(Fore.LIGHTGREEN_EX + f"{record}")

    srv_records = get_srv_records(domain)
    if srv_records:
        print(Fore.LIGHTYELLOW_EX + f"\nRegistros SRV para: {domain}\n")
        for srv_record in srv_records:
            parts = srv_record.split()
            service_type = parts[0]  # _sip._tcp, _sip._udp, etc.
            target_host = parts[3].strip('.')
            ip = get_ip(target_host)
            port = parts[2]
            print(Fore.LIGHTGREEN_EX + f"[SRV] {service_type} {target_host:<40} IP: {ip:<10}  PORT: {port}")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
