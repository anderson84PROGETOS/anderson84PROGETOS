import dns.resolver
import dns.zone
import socket

print("""

 █████╗ ██╗  ██╗███████╗██████╗     ███╗   ██╗███████╗██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗╚██╗██╔╝██╔════╝██╔══██╗    ████╗  ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
███████║ ╚███╔╝ █████╗  ██████╔╝    ██╔██╗ ██║███████╗██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
██╔══██║ ██╔██╗ ██╔══╝  ██╔══██╗    ██║╚██╗██║╚════██║██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝ 
██║  ██║██╔╝ ██╗██║     ██║  ██║    ██║ ╚████║███████║███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║     
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝    ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                                                                         
""")

# Definir o cabeçalho de agente do usuário
user_agent = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"

# Criar um resolver personalizado
resolver = dns.resolver.Resolver()

# Configurar o cabeçalho de agente do usuário no resolver
resolver.headers = {'User-Agent': user_agent}

# Prompt the user for a domain name
domain_name = input('\nDigite o nome do website que deseja consultar: ')

try:
    # Perform 'nslookup' command for the first query
    query1 = resolver.resolve(domain_name, 'NS')
    nameservers = [ns.to_text() for ns in query1]
except dns.resolver.NXDOMAIN:
    print(f'O domínio {domain_name} não foi Encontrado')
    exit()
except dns.exception.DNSException as e:
    print(f"Erro DNS: {e}")
    exit()

# Print the output of the first query
print('\n↓↓ Servidores DNS ↓↓\n')
print('\n'.join(nameservers))
print('\n')

# Flag to check if zone transfer is found
zone_transfer_found = False

# Iterate over all nameservers to perform zone transfer
for nameserver in nameservers:
    try:
        # Check if the input is an IP address, if not, resolve it to an IP address
        try:
            socket.inet_pton(socket.AF_INET, nameserver)
            nameserver_ip = nameserver
        except socket.error:
            nameserver_ip = socket.gethostbyname(nameserver)

        zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain_name))
        print('\n\n↓↓ Saída da consulta de transferência de zona para o servidor: ', nameserver, '\n\n\n')
        for name, node in zone.nodes.items():
            try:
                print(name, node.to_text(name))  # Pass the name as an argument
                zone_transfer_found = True
            except AttributeError:
                print(f"NoData exception for {name}")
    except dns.exception.FormError as e:
        pass  # Ignore FormError
    except dns.exception.DNSException as e:
        pass  # Ignore other DNS exceptions

# Check if zone transfer is not found and print a message
if not zone_transfer_found:
    print("\nTransferência de Zona não Encontrada")

input("\nConsulta de Transferência de zona Terminada [ENTER SAIR]\n")
