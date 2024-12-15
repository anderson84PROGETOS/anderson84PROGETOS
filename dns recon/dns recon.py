import dns.resolver

print("""

██████╗ ███╗   ██╗███████╗    ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██║  ██║██╔██╗ ██║███████╗    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██████╔╝██║ ╚████║███████║    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                      
""")

def dns_enum(domain):
    try:
        answers = dns.resolver.resolve(domain, 'A')        
        print("\n\n\nHost's addresses (A)")
        print("====================")
        for answer in answers:
            print(f"\n{domain: <40} {'IN A': <10} IP: {answer.address}")            
    except dns.resolver.NoAnswer:
        print(f"\n[!] Nenhum registro A encontrado para: {domain}")
    except dns.resolver.NXDOMAIN:
        print(f"\n[!] O domínio {domain} não foi encontrado.")
    except Exception as e:
        print(f"\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")
        
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        print("\n\n")
        print(f"\n\nMail Servers (MX)")
        print("=================")
        if answers:
            for answer in answers:
                print(f"\n{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {dns.resolver.resolve(answer.exchange, 'A')[0].address}")
        else:
            print(f"\n[!] Nenhum registro MX encontrado para: {domain}")
    except Exception as e:
        print(f"\n\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")
        
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        print("\n\n")
        print(f"\n\nName Servers (NS)")
        print("=================")
        for answer in answers:
            print(f"\n{answer.target.to_text(): <40} {'IN NS': <10} IP: {dns.resolver.resolve(answer.target, 'A')[0].address}")
    except dns.resolver.NoAnswer:
        print(f"\n[!] Nenhum registro NS encontrado para: {domain}")
    except Exception as e:
        print(f"\n\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")

    try:
        answers = dns.resolver.resolve(domain, 'HINFO')
        print("\n\n")
        print(f"\n\nHost Information (HINFO)")
        print("========================")
        for answer in answers:
            print(f"\n[HINFO]  {answer.cpu}  OS: {answer.os}")
    except dns.resolver.NoAnswer:
        print("\n\n\n")
        print(f"Host Information (HINFO)")
        print("========================")
        print(f"\n[!] Nenhum registro HINFO encontrado para: {domain}")
    except Exception as e:
        print(f"\n\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")

    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        print("\n\n")
        print(f"\n\nText Records (TXT)")
        print("==================")
        for answer in answers:
            for txt_record in answer.strings:
                print(f"\n[TXT]  {txt_record.decode()}")
    except dns.resolver.NoAnswer:
        print(f"\n[!] Nenhum registro TXT encontrado para {domain}.")
    except Exception as e:
        print(f"\n\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")    

    try:
        answers = dns.resolver.resolve(domain, 'SOA')
        print("\n\n")
        print(f"\n\nStart of Authority (SOA)")
        print("========================")
        for answer in answers:
            print(f"\n[SOA]  {answer.mname.to_text()} RNAME: {answer.rname.to_text()} Serial: {answer.serial} Refresh: {answer.refresh} Retry: {answer.retry} Expire: {answer.expire} Minimum: {answer.minimum}")
    except dns.resolver.NoAnswer:
        print(f"\n[!] Nenhum registro SOA encontrado para {domain}.")
    except Exception as e:
        print(f"\n\n\n[!] Ocorreu um erro ao consultar DNS para: {domain}  {e}")        

    # Get SRV records for common services
    print(f"\n\n\nService Records (SRV)")
    print("=====================")
    print()
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    srv_found = False
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0]
                print(f"[SRV]  {srv_domain} {srv.target} {srv_ip} {srv.port}\n")
                srv_found = True
        except Exception as e:
            pass  # Ignorar exceções para serviços SRV não encontrados

    if not srv_found:
        print(f"\n[!] Nenhum registro SRV encontrado para: {domain}")

if __name__ == "__main__":
    domain = input("\nDigite o Nome do Domínio Para Enumeração DNS: ").strip()
    dns_enum(domain)   

input("\n\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
