import dns.resolver
import dns.query
import dns.zone
import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║    ██╔════╝████╗  ██║██║   ██║████╗ ████║
██║  ██║██╔██╗ ██║███████╗    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
██████╔╝██║ ╚████║███████║    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝

""")

def dns_enum(domain):
    try:
        # Consultar registros A (endereços do host)
        answers = dns.resolver.resolve(domain, 'A')        
        print("\n\n\nHost's addresses (A)")
        print("====================")
        for answer in answers:
            print(f"\n{domain: <40} {'IN A': <10} IP: {answer.address}")            
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, Exception):
        pass  # Ignora erros sem exibir mensagens
    try:
        # Consultar servidores de email (MX)
        answers = dns.resolver.resolve(domain, 'MX')
        if answers:
            print("\n\nMail Servers (MX)")
            print("=================")
            for answer in answers:
                print(f"\n{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {dns.resolver.resolve(answer.exchange, 'A')[0].address}")
    except (dns.resolver.NoAnswer, Exception):
        pass  # Ignora erros sem exibir mensagens        
    try:
        # Consultar servidores de nome (NS)
        answers = dns.resolver.resolve(domain, 'NS')
        if answers:
            print("\n\nName Servers (NS)")
            print("=================")
            for answer in answers:
                print(f"\n{answer.target.to_text(): <40} {'IN NS': <10} IP: {dns.resolver.resolve(answer.target, 'A')[0].address}")
    except (dns.resolver.NoAnswer, Exception):
        pass  # Ignora erros sem exibir mensagens
    try:
        # Consultar registros HINFO
        answers = dns.resolver.resolve(domain, 'HINFO')
        if answers:
            print("\n\nHost Information (HINFO)")
            print("========================")
            for answer in answers:
                print(f"\nCPU: {answer.cpu}  OS: {answer.os}")
    except (dns.resolver.NoAnswer, Exception):
        pass  # Ignora erros sem exibir mensagens

    try:
        # Consultar registros TXT
        answers = dns.resolver.resolve(domain, 'TXT')
        if answers:
            print("\n\nText Records (TXT)")
            print("==================")
            for answer in answers:
                for txt_record in answer.strings:
                    print(f"\nTXT: {txt_record.decode()}")
    except (dns.resolver.NoAnswer, Exception):
        pass  # Ignora erros sem exibir mensagens 
    try:
        # Consultar registros SOA
        answers = dns.resolver.resolve(domain, 'SOA')
        if answers:
            print("\n\nStart of Authority (SOA)")
            print("========================")
            for answer in answers:
                print(f"\nMNAME: {answer.mname.to_text()} RNAME: {answer.rname.to_text()} Serial: {answer.serial} Refresh: {answer.refresh} Retry: {answer.retry} Expire: {answer.expire} Minimum: {answer.minimum}")
    except (dns.resolver.NoAnswer, Exception):
        pass  # Ignora erros sem exibir mensagens
    # Consultar registros SRV para serviços comuns
    srv_found = False  # Flag para verificar se encontrou registros SRV
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            if srv_records:
                if not srv_found:
                    print(f"\n\nService Records (SRV)")
                    print("=====================")
                    srv_found = True
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0]
                print(f"[SRV]      SRV {srv_domain} {srv.target} {srv_ip} {srv.port}")
        except Exception:
            pass  # Ignorar exceções para serviços SRV não encontrados
    if not srv_found:
        pass  # Não exibe mensagem de erro se não encontrar registros SRV
    # Consultar tentativa de transferência de zona (zone transfer)
    print("=" * 80)  # Linha de separação
    ns_servers = []
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        for rdata in answers:
            ns_domain = str(rdata.target).strip('.')
            ns_servers.append(ns_domain)
    except:
        pass
    # Tentativa de Transferência de Zona
    for ns_domain in ns_servers:
        try:
            zone = dns.zone.from_xfr(dns.query.xfr(ns_domain, domain))
            for name, node in zone.nodes.items():
                record = zone[name].to_text(name)
                print(record)
        except:
            pass
    # Tentativa de Transferência de Zona usando nslookup
    for ns_domain in ns_servers:
        print(f"\nExecutando transferência de zona: {domain}    {ns_domain}")
        print("=" * 80)  # Linha de separação
        try:
            result = subprocess.run(
                ["nslookup", "-type=any", domain, ns_domain],
                text=True,
                capture_output=True,
                check=True
            )
            print(result.stdout)
        except:
            pass
if __name__ == "__main__":
    domain = input("\nDigite o nome do domínio para enumeração DNS: ").strip()
    dns_enum(domain)

input("\n========== PRESSIONE ENTER PARA SAIR ==========\n")
