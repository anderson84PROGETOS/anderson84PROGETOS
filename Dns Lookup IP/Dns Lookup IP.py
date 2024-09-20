import requests
import socket
import subprocess
import re
import dns.resolver  # Certifique-se de ter a biblioteca dnspython instalada

print("""

██████╗ ███╗   ██╗███████╗    ██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗     ██╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗    ██║██╔══██╗
██║  ██║██╔██╗ ██║███████╗    ██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝    ██║██████╔╝
██║  ██║██║╚██╗██║╚════██║    ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝     ██║██╔═══╝ 
██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║         ██║██║     
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝         ╚═╝╚═╝     
                                                                                               
""")

def get_ip_info(website):
    try:
        ip_address = socket.gethostbyname(website)
        print(f"Endereço IP: {ip_address}")
        print("")

        ipv4_addresses = get_ipv4_addresses(website)
        if ipv4_addresses:
            for ipv4_address in ipv4_addresses:
                print(f"IP do Website: {ipv4_address}")
        else:
            print("\nNenhum endereço IPv4 encontrado.")

        ip_response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        ip_data = ip_response.json()

        print("\n\nInformações do website\n")
        print(f"Hostname: {ip_data.get('hostname', 'N/A')}")
        print(f"Organização: {ip_data.get('org', 'N/A')}")
        print(f"Cidade: {ip_data.get('city', 'N/A')}")
        print(f"Região: {ip_data.get('region', 'N/A')}")
        print(f"País: {ip_data.get('country', 'N/A')}")

        loc = ip_data.get("loc", "N/A")
        if loc != "N/A":
            latitude, longitude = loc.split(',')
            print(f"\nLocalização: {loc}")
            print(f"Latitude: {latitude}")
            print(f"Longitude: {longitude}")
            google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
            print(f"\nGoogle Maps: {google_maps_url}")

        get_mx_records(website)

    except requests.RequestException as e:
        print(f"Erro de requisição: {e}")
    except socket.gaierror as e:
        print(f"Erro de socket: {e}")
    except KeyError as e:
        print(f"Erro de chave: {e}")
    except Exception as e:
        print(f"Erro: {e}")

def get_ipv4_addresses(site):
    try:
        output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
        lines = output_dns.stdout.splitlines()
        servers = [line.split()[-1] for line in lines if 'nameserver' in line]

        output_list_dns = []
        for server in servers:
            output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
            output_list_dns.append(output.stdout)

        ipv4_addresses = []
        for output in output_list_dns:
            ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
            ipv4_addresses.extend(ipv4_matches)

        ipv4_addresses = list(set(ipv4_addresses))
        return ipv4_addresses

    except subprocess.CalledProcessError as e:
        print(f"Erro no subprocesso: {e}")
    except Exception as e:
        print(f"Erro: {e}")

def get_mx_records(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        print("==================================================================")
        print("\n\nRegistros MX para:", domain)
        print("")
        for mx in mx_records:
            mx_host = str(mx.exchange).rstrip('.')
            #print(mx_host)
            consulta_dns(mx_host, 'A')
            print()  # Adiciona uma linha em branco após as consultas A

    except Exception as e:
        print(f"\nErro ao consultar registros MX: {e}")

def consulta_dns(host, record_type):
    try:
        answers = dns.resolver.resolve(host, record_type)
        print(f"Consulta {record_type} para: {host}")
        for answer in answers:
            print(answer.to_text())
    except Exception as e:
        print(f"\nErro ao consultar {record_type} para {host}: {e}")

if __name__ == "__main__":
    website = input("\nDigite o nome do website ou IP (ex. example.com ou IP): ")
    print("\n\nInformações do website\n======================\n")
    get_ip_info(website)

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
