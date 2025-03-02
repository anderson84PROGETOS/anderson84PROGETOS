import dns.resolver
import socket
import subprocess
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ██████╗ ███████╗██╗   ██╗███████╗██████╗ ███████╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔════╝██║   ██║██╔════╝██╔══██╗██╔════╝██╔════╝
██║  ██║██╔██╗ ██║███████╗    ██████╔╝█████╗  ██║   ██║█████╗  ██████╔╝███████╗█████╗  
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██╔══╝  
██████╔╝██║ ╚████║███████║    ██║  ██║███████╗ ╚████╔╝ ███████╗██║  ██║███████║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
""")

# Tipos de registros DNS suportados
DNS_TYPES = ['A', 'MX']

def get_dns_records(domain, record_type):
    """Obtém os registros DNS do tipo especificado para um domínio."""
    try:
        answers = dns.resolver.resolve(domain, record_type)
        
        if record_type == 'A':
            return [rdata.to_text() for rdata in answers]
        elif record_type == 'MX':
            return [(rdata.exchange.to_text().rstrip('.'), rdata.preference) for rdata in answers]
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao obter registros {record_type}: {e}")
        return []

def resolve_ip_from_record(record, record_type, domain):
    """Resolve o IP do registro, se aplicável."""
    if record_type == 'A':
        return domain, record
    elif record_type == 'MX':
        exchange = record[0]  # exchange do MX
        try:
            ip = socket.gethostbyname(exchange)
            return exchange, ip
        except Exception as e:
            print(f"Erro ao resolver IP para {exchange}: {e}")
            return exchange, None
    return None, None  # Para segurança, caso algo inesperado ocorra

def iterate_ip_range(ip_prefix, domain, record_type):
    """Itera sobre os IPs com base no prefixo e consulta o host, ajustando o alinhamento por tipo."""
    results = []  # Para armazenar os resultados e salvar depois
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nConsultando IP na faixa: {ip_prefix}.0-255   Para: {domain}\n")
    results.append(f"Consultando IP na faixa: {ip_prefix}.0-255   Para: {domain}\n")
    
    for last_octet in range(256):
        ip = f"{ip_prefix}.{last_octet}"
        try:
            result = subprocess.run(["nslookup", ip], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                if "Nome:" in output:
                    lines = output.splitlines()
                    for line in lines:
                        if "Nome:" in line:
                            hostname = line.split("Nome:")[-1].strip()
                            align_width = 60 if record_type == 'A' else 40
                            formatted_line = f"Domínio: {hostname:<{align_width}} IP: {ip}"
                            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + formatted_line)
                            results.append(formatted_line)
        except Exception as e:
            error_msg = f"Erro ao consultar {ip}: {e}"
            print(error_msg)
            results.append(error_msg)
    return results

def save_results_to_file(results, filename):
    """Salva os resultados em um arquivo."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for line in results:
                f.write(line + '\n')
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos com sucesso em: {filename}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar o arquivo: {e}")

def main():
    # Lista os tipos de registros disponíveis primeiro
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nTipos de registros DNS disponíveis\n")
    for i, dns_type in enumerate(DNS_TYPES, 1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{i:<2} = {dns_type}")
    
    # Solicita a escolha do tipo de registro
    choice = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nEscolha o tipo de registro (digite o número): ").strip()
    try:
        record_type = DNS_TYPES[int(choice) - 1]
    except (IndexError, ValueError):
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nEscolha inválida!")
        return

    # Solicita o nome do website depois da escolha
    domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome do website: ").strip()

    records = get_dns_records(domain, record_type)

    if not records:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNenhum registro {record_type} encontrado.")
        return

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nRegistros {record_type} Encontrados\n")
    first_record = records[0]
    exchange, ip = resolve_ip_from_record(first_record, record_type, domain)
    if ip:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{exchange:<25} IP:  {ip}")
        ip_prefix = '.'.join(ip.split('.')[:-1])
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n\nIterando sobre o IP do registro {record_type}")
        results = iterate_ip_range(ip_prefix, domain, record_type)
        
        # Pergunta se deseja salvar os resultados
        save_choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT  + "\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
        if save_choice == 's':
            filename = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo (exemplo: arquivo.txt): ").strip()
            save_results_to_file(results, filename)
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nNão foi possível resolver o IP do {record_type}.")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
