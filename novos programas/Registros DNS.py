import dns.resolver
import socket

print("""

██████╗ ███████╗ ██████╗ ██╗███████╗████████╗██████╗  ██████╗ ███████╗    ██████╗ ███╗   ██╗███████╗
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██╔════╝    ██╔══██╗████╗  ██║██╔════╝
██████╔╝█████╗  ██║  ███╗██║███████╗   ██║   ██████╔╝██║   ██║███████╗    ██║  ██║██╔██╗ ██║███████╗
██╔══██╗██╔══╝  ██║   ██║██║╚════██║   ██║   ██╔══██╗██║   ██║╚════██║    ██║  ██║██║╚██╗██║╚════██║
██║  ██║███████╗╚██████╔╝██║███████║   ██║   ██║  ██║╚██████╔╝███████║    ██████╔╝██║ ╚████║███████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                    
""")

def resolve_domain(domain):
    records = {}
    
    try:
        # Consultar registros A
        answers = dns.resolver.resolve(domain, 'A')
        records['A'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['A'] = []

    try:
        # Consultar registros NS
        answers = dns.resolver.resolve(domain, 'NS')
        records['NS'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['NS'] = []

    try:
        # Consultar registros MX
        answers = dns.resolver.resolve(domain, 'MX')
        records['MX'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['MX'] = []

    try:
        # Consultar registros CNAME
        answers = dns.resolver.resolve(domain, 'CNAME')
        records['CNAME'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['CNAME'] = []

    try:
        # Consultar registros HINFO
        answers = dns.resolver.resolve(domain, 'HINFO')
        records['HINFO'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['HINFO'] = []
        
    try:
        # Consultar registros TXT
        answers = dns.resolver.resolve(domain, 'TXT')
        records['TXT'] = [r.to_text() for r in answers]
    except dns.resolver.NoAnswer:
        records['TXT'] = []

    return records

def resolve_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.error:
        return 'IP não encontrado'

def print_records(records):
    # Flag para verificar o tipo de registro do último impresso
    last_record_type = None

    for record_type, values in records.items():
        for value in values:
            # Adicionar uma linha em branco antes de imprimir se o último registro foi MX e o atual é TXT
            if last_record_type == 'MX' and record_type == 'TXT':
                print("\n")  # Linha em branco
            # Adicionar uma linha em branco antes de imprimir se o último registro foi HINFO e o atual é TXT
            elif last_record_type == 'HINFO' and record_type == 'TXT':
                print("\n")  # Linha em branco
            # Remover ponto final de NS e MX
            if record_type in ['NS', 'MX']:
                value = value.rstrip('.')
                parts = value.split()
                hostname = parts[-1]
                ip = resolve_ip(hostname)
                print(f'{record_type: <10} {hostname:<35} IP: {ip}')
            elif record_type == 'TXT':
                print(f'{record_type: <10} {value}')
            else:
                print(f'{record_type: <10} {value}')
            
            # Atualizar o tipo do último registro impresso
            last_record_type = record_type

def main():
    domain = input('\nDigite o nome do domínio: ')
    records = resolve_domain(domain)
    
    if records:
        print(f'\n\nRegistros DNS para: {domain}')
        print("")
        print_records(records)
    else:
        print('Nenhum registro encontrado.')

if __name__ == '__main__':
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
