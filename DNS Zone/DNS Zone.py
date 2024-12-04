import dns.resolver
import dns.reversename
import dns.zone
import dns.query
import dns.exception
import socket

print("""

██████╗ ███╗   ██╗███████╗    ███████╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗████╗  ██║██╔════╝    ╚══███╔╝██╔═══██╗████╗  ██║██╔════╝
██║  ██║██╔██╗ ██║███████╗      ███╔╝ ██║   ██║██╔██╗ ██║█████╗  
██║  ██║██║╚██╗██║╚════██║     ███╔╝  ██║   ██║██║╚██╗██║██╔══╝  
██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝██║ ╚████║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                                                 
""")

# Funções para realizar consultas DNS de diferentes tipos
def consultar_tipo_dns(domain, tipo):
    try:
        respostas = dns.resolver.resolve(domain, tipo)
        print(f"\n\nRespostas para {tipo} de: {domain}\n")
        for resposta in respostas:
            print(resposta.to_text())
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
        pass

# Função para consultar registros NS
def consultar_ns(domain):
    try:
        respostas = dns.resolver.resolve(domain, 'NS')
        print(f"\nServidores de nomes para: {domain}\n")
        for resposta in respostas:
            print(resposta.to_text())
        return [r.to_text() for r in respostas]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
        return []

# Função para consultar registros PTR (reverso)
def consultar_ptr(ip):
    try:
        reversed_domain = dns.reversename.from_address(ip)
        consultar_tipo_dns(reversed_domain, 'PTR')
    except (dns.exception.SyntaxError, dns.exception.DNSException):
        pass

# Função para realizar a transferência de zona
def transferencia_zona(domain, server):
    try:
        ip = socket.gethostbyname(server)
        if ip:
            pass
    except (dns.query.TransferError, dns.exception.DNSException):
        pass
    except socket.gaierror:
        pass

# Funções para consultar diferentes tipos de registros DNS
def consultar_txt(domain):
    consultar_tipo_dns(domain, 'TXT')

def consultar_mx(domain):
    consultar_tipo_dns(domain, 'MX')

def consultar_soa(domain):
    consultar_tipo_dns(domain, 'SOA')

def consultar_ds(domain):
    consultar_tipo_dns(domain, 'DS')

def consultar_srv(domain):
    consultar_tipo_dns(domain, 'SRV')

def consultar_nsec3(domain):
    consultar_tipo_dns(domain, 'NSEC3')

def consultar_hinfo(domain):
    consultar_tipo_dns(domain, 'HINFO')

def consultar_cname(domain):
    consultar_tipo_dns(domain, 'CNAME')

def consultar_any(domain):
    consultar_tipo_dns(domain, 'ANY')

# Função para tentar realizar a transferência de zona e listar subdomínios encontrados
def tentar_transferencia_zona(domain):
    try:
        ns_records = dns.resolver.resolve(domain, 'NS')
        subdominios = []

        for ns in ns_records:
            ns_server = str(ns.target).rstrip('.')
            try:
                ns_ip = dns.resolver.resolve(ns_server, 'A')[0].to_text()
                z = dns.zone.from_xfr(dns.query.xfr(ns_ip, domain))
                if z is not None:
                    subdominios.extend(f"{name}.{domain}" for name in z.nodes.keys())
            except (dns.query.TransferError, dns.exception.DNSException):
                pass

        return subdominios
    except dns.exception.DNSException:
        pass
    return []

# Execução principal do script
domain = input("\nDigite o domínio para realizar as consultas DNS: ").strip()

# Consultas A e NS
consultar_tipo_dns(domain, 'A')
ns_servers = consultar_ns(domain)

# Consultas PTR (requere um IP, você pode substituir pelo IP do domínio)
try:
    ip = socket.gethostbyname(domain)
    consultar_ptr(ip)
except socket.gaierror:
    pass

# Consultas restantes
consultar_txt(domain)
consultar_mx(domain)
consultar_soa(domain)
consultar_ds(domain)
consultar_srv(domain)
consultar_nsec3(domain)
consultar_hinfo(domain)
consultar_cname(domain)
consultar_any(domain)

# Realizando a transferência de zona para os servidores de nomes encontrados
for server in ns_servers:
    transferencia_zona(domain, server)

# Tentativa de transferência de zona e listagem de subdomínios encontrados
subdominios = tentar_transferencia_zona(domain)

if subdominios:
    print("\n\n\nSubdomínios Encontrados\n")
    for sub in subdominios:
        print(sub)
else:
    print("\n\n\nNenhum subdomínio Encontrado ou transferência de zona não permitida.")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
