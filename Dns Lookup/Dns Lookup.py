import dns.resolver

print("""

██████╗ ███╗   ██╗███████╗    ██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
██║  ██║██╔██╗ ██║███████╗    ██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
██║  ██║██║╚██╗██║╚════██║    ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝ 
██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║     
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                                                
""")

def dns_enum(domain):
    registros = ["A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "TXT", "CAA", "DS", "DNSKEY", "HINFO"]
    
    for registro in registros:
        try:
            # Resolve os registros DNS do tipo específico
            answers = dns.resolver.resolve(domain, registro)
            print(f"\n\n{registro} Records")
            print("====================")
            for answer in answers:
                try:
                    # Resolve IP para registros A e AAAA
                    if registro in ["A", "AAAA"]:
                        print(f"{domain: <40} {'IN ' + registro: <10} IP: {answer.address}")
                    elif registro == "MX":
                        # Para MX, resolve o IP do servidor de troca
                        exchange_ip = dns.resolver.resolve(answer.exchange, 'A')[0].address
                        print(f"{answer.exchange.to_text(): <40} {'IN MX': <10} IP: {exchange_ip}")
                    elif registro in ["NS", "CNAME"]:
                        # Para NS e CNAME, resolve o IP do alvo
                        target_ip = dns.resolver.resolve(answer.target, 'A')[0].address
                        print(f"{answer.target.to_text(): <40} {'IN ' + registro: <10} IP: {target_ip}")
                    elif registro == "PTR":
                        # Registros PTR normalmente fornecem uma pesquisa reversa de DNS
                        print(f"{answer.target.to_text(): <40} {'IN PTR': <10} IP: {answer.address}")
                    elif registro == "SOA":
                        # Para SOA, imprime os detalhes do Start of Authority
                        soa_ip = dns.resolver.resolve(answer.mname.to_text(), 'A')[0].address
                        print(f"{answer.mname.to_text()} RNAME: {answer.rname.to_text()} Serial: {answer.serial} Refresh: {answer.refresh} Retry: {answer.retry} Expire: {answer.expire} Minimum: {answer.minimum} \n\nSOA IP: {soa_ip}")
                    elif registro == "TXT":
                        # Para registros TXT, pode conter valores de string
                        for txt_record in answer.strings:
                            txt_value = txt_record.decode()
                            try:
                                # Resolve o IP para os registros TXT, se possível
                                ip_address = dns.resolver.resolve(domain, 'A')[0].address
                                print(f"\n[TXT] {txt_value}        IP: {ip_address:<20}")
                            except Exception as e:
                                print(f"[TXT] {txt_value}          IP: [Erro ao resolver IP]")
                    elif registro == "CAA":
                        # Registros CAA especificam as políticas da autoridade certificadora do domínio
                        print(f"[CAA] {answer.flags} {answer.tag} {answer.value} \n\nCAA IP: {ip_address:<20}")
                    elif registro == "DS" or registro == "DNSKEY":
                        # Registros DS e DNSKEY geralmente contêm informações relacionadas à segurança
                        print(f"[{registro}] {answer}")
                    elif registro == "HINFO":
                        # Registros HINFO fornecem informações sobre o sistema
                        print(f"[HINFO] {answer.cpu} {answer.os}     IP: {ip_address:<20}")
                except Exception as e:
                    print(f"[{registro}] Erro ao resolver IP: {e}")
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass
        except Exception as e:
            print(f"[!] Ocorreu um erro ao consultar o registro {registro} para {domain}: {e}")
    
    # SRV records para serviços comuns
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']
    
    srv_found = False
    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            if not srv_found:
                print(f"\n\nService Records (SRV)")
                print("=====================")
                srv_found = True  # Marca que ao menos um SRV foi encontrado
            for srv in srv_records:
                srv_ip = dns.resolver.resolve(srv.target, 'A')[0].address
                print(f"\n[SRV] {srv_domain:<30} {srv.target}              IP: {srv_ip:<20} PORT: {srv.port}")
        except Exception as e:
            pass  # Ignorar exceções para serviços SRV não encontrados

if __name__ == "__main__":
    domain = input("\nDigite o Nome do Domínio Para Enumeração DNS: ").strip()
    dns_enum(domain)

input("\n\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
