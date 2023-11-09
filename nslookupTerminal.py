import dns.resolver
import dns.zone
import socket

# Prompt the user for a domain name
domain_name = input('\nDigite o nome do website que deseja consultar: ')

# Perform 'nslookup' command for the first query
resolver = dns.resolver.Resolver()
resolver.nameservers = ['8.8.8.8']  # Use a default DNS server, or replace with your preferred DNS server

try:
    query1 = resolver.resolve(domain_name, 'NS')
    nameservers = [ns.to_text() for ns in query1]
except dns.resolver.NXDOMAIN:
    print(f'O domínio {domain_name} não foi encontrado.')
    exit()
except dns.exception.DNSException as e:
    print(f"Erro DNS: {e}")
    exit()

# Print the output of the first query
print('\n↓↓ Servidores DNS ↓↓\n')
print('\n'.join(nameservers))
print('\n')

# Prompt the user for a nameserver to use for the zone transfer
nameserver = input('Insira um servidor de nomes para a transferência de zona: ')

try:
    # Check if the input is an IP address, if not, resolve it to an IP address
    try:
        socket.inet_pton(socket.AF_INET, nameserver)
        nameserver_ip = nameserver
    except socket.error:
        nameserver_ip = socket.gethostbyname(nameserver)

    zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain_name))
    print('\n↓↓ Saída da consulta de transferência de zona ↓↓\n')
    for name, node in zone.nodes.items():
        try:
            print(name, node.to_text(name))  # Pass the name as an argument
        except AttributeError:
            print(f"NoData exception for {name}")
except dns.exception.FormError as e:
    print(f"Erro na transferência de zona: {e}")
except dns.exception.DNSException as e:
    print(f"Erro DNS: {e}")

input("\nConsulta de transferência de zona terminada [ENTER SAIR]\n")
