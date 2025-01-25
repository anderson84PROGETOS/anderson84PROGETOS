import dns.zone
import dns.resolver
import dns.query
import warnings

# Desativar avisos de depreciação
warnings.filterwarnings("ignore", category=DeprecationWarning)

def dns_zone_xfer(domain_name):
    found_zone = False  # Variável de controle para verificar se foi encontrada uma transferência de zona
    try:
        # Obter servidores NS para o domínio
        ns_answer = dns.resolver.query(domain_name, 'NS')
        for server in ns_answer:
            # Obter IPs do servidor NS
            ip_answer = dns.resolver.query(str(server.target), 'A')
            for ip in ip_answer:
                try:
                    # Tentar realizar a transferência de zona
                    zone = dns.zone.from_xfr(dns.query.xfr(str(ip), domain_name))
                    if zone:
                        found_zone = True  # Indica que uma transferência de zona foi encontrada
                        print(f"\n[✔] Transferência de zona bem-sucedida no servidor: {server.target}\n")
                        
                        for host in zone:
                            full_url = f"{host}.{domain_name}"
                            print(f"[*] Encontrado Host: {full_url}")
                except Exception:
                    continue  # Ignorar erros e tentar o próximo servidor
    except dns.exception.DNSException:
        pass  # Ignorar erros de consulta DNS

    # Exibir mensagem apenas se nenhuma transferência de zona for encontrada
    if not found_zone:
        print(f"[!] Nenhuma transferência de zona foi encontrada no domínio: {domain_name}")

if __name__ == "__main__":
    domain_name = input("\nDigite o nome do domínio (Exemplo: zonetransfer.me): ")
    print("\n")
    dns_zone_xfer(domain_name)

input("\n\n🎯 Pressione Enter para sair 🎯\n")
