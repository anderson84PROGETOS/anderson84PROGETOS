import subprocess
import re
import ipaddress

print("""

███╗   ██╗███████╗████████╗███████╗████████╗ █████╗ ████████╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
████╗  ██║██╔════╝╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██╔██╗ ██║█████╗     ██║   ███████╗   ██║   ███████║   ██║       ███████╗██║     ███████║██╔██╗ ██║
██║╚██╗██║██╔══╝     ██║   ╚════██║   ██║   ██╔══██║   ██║       ╚════██║██║     ██╔══██║██║╚██╗██║
██║ ╚████║███████╗   ██║   ███████║   ██║   ██║  ██║   ██║       ███████║╚██████╗██║  ██║██║ ╚████║
╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                                                  
""")
print("\nEscaneando Aguarde....\n")
def get_netstat_output():
    try:
        # Executa o comando 'netstat -f' e captura a saída
        result = subprocess.run(['netstat', '-f'], stdout=subprocess.PIPE, text=True)
        return result.stdout
    except Exception as e:
        print(f"Erro ao executar o comando netstat: {e}")
        return ""

def extract_ip_info(netstat_output):
    # Regex para encontrar endereços IPv4 e IPv6
    ip_pattern = re.compile(r'([0-9a-fA-F:.]+)\s+(\S+:\S+)')
    matches = ip_pattern.findall(netstat_output)
    return matches

def nslookup(ip):
    try:
        # Usa o comando nslookup para obter o IPv4 associado a um domínio
        result = subprocess.run(['nslookup', '-q=A', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        
        # Filtra mensagens de erro
        if 'Non-existent domain' in output or 'timeout' in output:
            return None
        
        # Regex para encontrar o endereço IPv4 no resultado do nslookup
        ip_pattern = re.compile(r'Address:\s+(\d+\.\d+\.\d+\.\d+)')
        matches = ip_pattern.findall(output)
        
        if matches:
            return matches[0]
        return None
    except Exception as e:
        # Se o nslookup falhar, retorna None
        print(f"Erro ao executar o nslookup para {ip}: {e}")
        return None

def convert_ipv6_to_ipv4(ipv6):
    try:
        # Converte IPv6 para IPv4-mapped IPv6 e depois para IPv4
        ipv6_addr = ipaddress.IPv6Address(ipv6)
        if ipv6_addr.ipv4_mapped:
            ipv4_addr = ipv6_addr.ipv4_mapped
            return str(ipv4_addr)
        return None
    except ipaddress.AddressValueError:
        return None

def main():
    netstat_output = get_netstat_output()
    
    # Exibe a saída capturada para verificação
    print("Saída completa do netstat -f")
    print(netstat_output)
    
    if not netstat_output:
        return
    
    ip_info = extract_ip_info(netstat_output)
    print("\nSaída completa do nslookup -q=A\n")
    for ip, fqdn in ip_info:
        # Tenta converter o IPv6 para IPv4, se aplicável
        ipv4_address = convert_ipv6_to_ipv4(ip)
        if ipv4_address:
            ip = ipv4_address
        
        # Resolve o IPv4 usando nslookup
        resolved_ip = nslookup(ip)
        if resolved_ip:
            
            print(f"Site: {fqdn.split(':')[0]} | IP: {resolved_ip}")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
