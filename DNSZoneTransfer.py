import subprocess
from ipwhois import IPWhois
import socket

print("""

██████╗ ███╗   ██╗███████╗    ███████╗ ██████╗ ███╗   ██╗███████╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███████╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ╚══███╔╝██╔═══██╗████╗  ██║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗      ███╔╝ ██║   ██║██╔██╗ ██║█████╗         ██║   ██████╔╝███████║██╔██╗ ██║███████╗█████╗  █████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║     ███╔╝  ██║   ██║██║╚██╗██║██╔══╝         ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██╔══╝  ██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝██║ ╚████║███████╗       ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║     ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                      
""")

def clean_output(output):
    # Filtra linhas que contêm "Authoritative answers can be found from:" e "Non-authoritative answer:"
    # Remove o ponto final do final do nome do servidor de nomes
    # Filtra linhas que começam com "Servidor:" e "Address:"
    filtered_lines = []
    for line in output.splitlines():
        if not (line.startswith("Authoritative answers can be found from:") or
                line.startswith("Non-authoritative answer:") or
                line.startswith("Servidor:") or
                line.startswith("Address:")):
            # Remove o ponto final do final do nome do servidor de nomes
            filtered_lines.append(line.rstrip('.'))
    return "\n".join(filtered_lines)

def get_isp_info(ip_address):
    try:
        obj = IPWhois(ip_address)
        res = obj.lookup_whois()
        return res['asn_description']
    except Exception as e:
        return str(e)

def dns_zone_transfer():
    # Solicita ao usuário o nome do website
    website = input("\nDigite o nome do website (ex: businesscorp.com.br): ")
    print()
    
    # Executa o comando nslookup para listar os registros NS
    print(f"\nListando registros NS para o website: {website}")
    print()
    nslookup_ns_command = f"nslookup -type=ns {website}"
    nslookup_ns_result = subprocess.run(nslookup_ns_command, shell=True, capture_output=True, text=True)
    cleaned_ns_result = clean_output(nslookup_ns_result.stdout)
    print(cleaned_ns_result)

    # Solicita ao usuário o servidor DNS para a transferência de zona
    dns_server = input("\n\nDigite o servidor DNS (ex: ns2.businesscorp.com.br): ")

    # Executa o comando nslookup para transferência de zona DNS
    print(f"\n\nTransferindo zona DNS para: {website} usando o servidor DNS: {dns_server}")
    print()
    try:
        ip_address = socket.gethostbyname(dns_server)
        print(f"\nEndereço IP Servidor  DNS: {ip_address}")
        isp_info = get_isp_info(ip_address)
        print(f"Servidor Organization ISP: {isp_info}\n")
        print("\nTransferência de zona DNS\n=========================\n")

        nslookup_any_command = f"nslookup -type=any {website} {dns_server}"
        nslookup_any_result = subprocess.run(nslookup_any_command, shell=True, capture_output=True, text=True)
        if nslookup_any_result.returncode != 0:
            print(f"Erro ao tentar transferir a zona DNS: {nslookup_any_result.stderr}")
        else:
            cleaned_any_result = clean_output(nslookup_any_result.stdout)
            if cleaned_any_result.strip():
                print(cleaned_any_result)
            else:
                print("Nenhuma informação de transferência de zona retornada. Verifique se o servidor DNS permite transferências de zona.")
    except socket.gaierror as e:
        print(f"Erro ao resolver o nome do servidor DNS: {e}")

if __name__ == "__main__":
    dns_zone_transfer()
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
