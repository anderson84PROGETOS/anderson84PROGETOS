import dns.resolver
import dns.query
import dns.zone

print("""

██████╗ ███╗   ██╗███████╗    ███████╗███████╗████████╗ ██████╗██╗  ██╗
██╔══██╗████╗  ██║██╔════╝    ██╔════╝██╔════╝╚══██╔══╝██╔════╝██║  ██║
██║  ██║██╔██╗ ██║███████╗    █████╗  █████╗     ██║   ██║     ███████║
██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██╔══╝     ██║   ██║     ██╔══██║
██████╔╝██║ ╚████║███████║    ██║     ███████╗   ██║   ╚██████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝     ╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
                                                                      
""")

def get_dns_records(domain):
    print(f"\n[+++]     Performing Enumeration for Website: {domain}\n")

    # Get SOA record
    try:
        soa_record = dns.resolver.resolve(domain, 'SOA')
        for soa in soa_record:
            print(f"[SOA]     {soa.mname} {soa.serial}\n")
    except Exception as e:
        print(f"")

    # Get NS records
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        for ns in ns_records:
            ns_ip = dns.resolver.resolve(ns.target, 'A')[0]
            print(f"[NS]      {ns.target} {ns_ip}")            
    except Exception as e:        
        print(f"")
        
    # Get MX records
    try:
        print("")
        mx_records = dns.resolver.resolve(domain, 'MX')
        for mx in mx_records:
            mx_ip = dns.resolver.resolve(mx.exchange, 'A')[0]            
            print(f"[MX]      {mx.exchange} {mx_ip}")
    except Exception as e:
        print(f"")

    # Get A records
    try:
        print("")
        a_records = dns.resolver.resolve(domain, 'A')
        for a in a_records:
            print(f"[A ]      {domain} {a.address}")
    except Exception as e:
        print(f"")    

    # Get HINFO records
    try:
        print()
        hinfo_records = dns.resolver.resolve(domain, 'HINFO')
        for hinfo in hinfo_records:
            print(f"[HINFO]   {hinfo.cpu} {hinfo.os}")
    except Exception as e:
        print(f"")    

    # Get SRV records for common services
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0]
                print(f"[SRV]     {srv_domain} {srv.target} {srv_ip} {srv.port}")
        except Exception as e:
            pass  # Ignorar exceções para serviços SRV não encontrados
    
     # Get TXT records
    try:
        print("\n")
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for txt in txt_records:
            print(f"[TXT]     {txt.strings}")
    except Exception as e:
        print(f"")

if __name__ == "__main__":
    domain = input("Digite o nome do website: ")
    get_dns_records(domain)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
