import dns.resolver
import socket
import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ██████╗ ███████╗██╗   ██╗███████╗██████╗ ███████╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔════╝██║   ██║██╔════╝██╔══██╗██╔════╝██╔════╝
██║  ██║██╔██╗ ██║███████╗    ██████╔╝█████╗  ██║   ██║█████╗  ██████╔╝███████╗█████╗  
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██╔══╝  
██████╔╝██║ ╚████║███████║    ██║  ██║███████╗ ╚████╔╝ ███████╗██║  ██║███████║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
                                                                                      
""")

def get_mx_records(domain):
    """Obtém os registros MX de um domínio."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [(rdata.exchange.to_text().rstrip('.'), rdata.preference) for rdata in answers]
        return mx_records
    except Exception as e:
        print(f"Erro ao obter registros MX: {e}")
        return []

def resolve_ips(mx_records):
    """Resolve os IPs dos registros MX."""
    ips = []
    for exchange, _ in mx_records:
        try:
            ip = socket.gethostbyname(exchange)
            ips.append((exchange, ip))
        except Exception as e:
            print(f"Erro ao resolver IP para {exchange}: {e}")
    return ips

def iterate_ip_range(ip_prefix, domain, exchange):
    """Itera sobre os IPs com base no prefixo e consulta o host."""
    print(f"\nConsultando IP na faixa {ip_prefix}.0-255 para {exchange}\n")
    for last_octet in range(256):
        ip = f"{ip_prefix}.{last_octet}"
        try:
            result = subprocess.run(["nslookup", ip], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()

                # Procura pela linha com "Nome:" que contém o nome do host
                if "Nome:" in output:  # Procurando "Nome:" (em português)
                    # Dividindo a saída do nslookup em linhas e procurando pela linha com "Nome:"
                    lines = output.splitlines()
                    for line in lines:
                        if "Nome:" in line:
                            # Pegando o nome do host após a palavra 'Nome:'
                            hostname = line.split("Nome:")[-1].strip()
                            print(f"IP: {ip:<20} ->  Domínio: {hostname}")
        except Exception as e:
            print(f"Erro ao consultar {ip}: {e}")

def main():
    domain = input("\nDigite o nome do website: ").strip()
    mx_records = get_mx_records(domain)

    if not mx_records:
        print("Nenhum registro MX encontrado.")
        return

    print("\n\nRegistros MX encontrados\n")
    mx_ips = resolve_ips(mx_records)
    for exchange, ip in mx_ips:
        print(f"{exchange:<25} IP:  {ip}")

    print("\nIterando sobre os IP dos registros MX")
    for exchange, ip in mx_ips:
        ip_prefix = '.'.join(ip.split('.')[:-1])
        iterate_ip_range(ip_prefix, domain, exchange)

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================")
