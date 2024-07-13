import requests
import socket
import subprocess
import re

print("""

 ██████╗ ███████╗ ██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
██╔════╝ ██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
██║  ███╗█████╗  ██║   ██║    ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
██║   ██║██╔══╝  ██║   ██║    ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
╚██████╔╝███████╗╚██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
 ╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                                                          
""")

def get_ip_info(website):
    try:
        # Obter o endereço IP do website
        ip_address = socket.gethostbyname(website)
        print(f"IP Address: {ip_address}")

        # Obter e imprimir endereços IPv4        
        ipv4_addresses = get_ipv4_addresses(website)
        if ipv4_addresses:
            for ipv4_address in ipv4_addresses:
                print(f"IP Website: {ipv4_address}")
        else:
            print("")

        # Obter informações detalhadas do IP
        ip_response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        ip_data = ip_response.json()

        hostname = ip_data.get("hostname")
        org = ip_data.get("org")
        city = ip_data.get("city")
        country = ip_data.get("country")
        region = ip_data.get("region")
        loc = ip_data.get("loc")
        latitude, longitude = loc.split(',')

        print(f"\nHostname: {hostname}")
        print(f"\nOrganization: {org}\n\n")
        print(f"City: {city}")
        print(f"Country: {country}")
        print(f"Region: {region}")        
        print(f"\nLocation: {loc}")
        print(f"\nLatitude: {latitude}")
        print(f"Longitude: {longitude}")  

        # Adicionar link do Google Maps
        google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
        print(f"\nGoogle Maps: {google_maps_url}")

    except requests.RequestException as e:
        print(f"Request Error: {e}")
    except socket.gaierror as e:
        print(f"Socket Error: {e}")
    except KeyError as e:
        print(f"Key Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

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
        print(f"Subprocess Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    website = input("\nDigite o nome do website ou IP (ex. example.com ou IP): ")
    print("\n\nInformações do website\n======================\n")
    get_ip_info(website)

    input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
