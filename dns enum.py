import dns.resolver
import dns.query
import dns.zone

print("""

██████╗ ███╗   ██╗███████╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
██╔══██╗████╗  ██║██╔════╝    ██╔════╝████╗  ██║██║   ██║████╗ ████║
██║  ██║██╔██╗ ██║███████╗    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
██████╔╝██║ ╚████║███████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
                                                                   
""")

def get_dns_records(domain):
    print(f"\n[+++] Performing Enumeration for Website: {domain}\n")

    # Get SOA record
    try:
        soa_record = dns.resolver.resolve(domain, 'SOA')
        for soa in soa_record:
            print(f"[SOA]      SOA {soa.mname} {soa.serial}")
    except Exception as e:
        print(f"[- ] SOA record not found for {domain}: {e}")

    # Get NS records
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        for ns in ns_records:
            ns_ip = dns.resolver.resolve(ns.target, 'A')[0]
            print(f"[NS ]      NS {ns.target} {ns_ip}")
    except Exception as e:
        print(f"[-  ] NS records not found for {domain}: {e}")

    # Get MX records
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        for mx in mx_records:
            mx_ip = dns.resolver.resolve(mx.exchange, 'A')[0]
            print(f"[MX ]      MX {mx.exchange} {mx_ip}")
    except Exception as e:
        print(f"[-  ] MX records not found for {domain}: {e}")

    # Get A records
    try:
        a_records = dns.resolver.resolve(domain, 'A')
        for a in a_records:
            print(f"[A  ]      A {domain} {a.address}")
    except Exception as e:
        print(f"[-  ] A records not found for {domain}: {e}")

    # Get TXT records
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for txt in txt_records:
            print(f"[TXT]      TXT {domain} {txt.strings}")
    except Exception as e:
        print(f"[-  ]      TXT records not found for {domain}: {e}")

    # Get HINFO records
    try:
        hinfo_records = dns.resolver.resolve(domain, 'HINFO')
        for hinfo in hinfo_records:
            print(f"[HIN]      HINFO {hinfo.cpu} {hinfo.os}")
    except Exception as e:
        print(f"[Hin]      HINFO records not found for {domain}: {e}")

    # Get SRV records for common services
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0]
                print(f"[SRV]      SRV {srv_domain} {srv.target} {srv_ip} {srv.port}")
        except Exception as e:
            pass  # Ignorar exceções para serviços SRV não encontrados

if __name__ == "__main__":
    domain = input("Digite o nome do website: ")
    get_dns_records(domain)

input("\n\n============ PRESSIONE ENTER PARA SAIR =========\n")
