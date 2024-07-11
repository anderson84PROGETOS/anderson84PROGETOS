import requests
import socket

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
        ip_response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        ip_data = ip_response.json()

        # Exibir informações do IP
        ip = ip_data.get("ip")
        city = ip_data.get("city")
        country = ip_data.get("country")
        region = ip_data.get("region")  # Adicionando a região
        loc = ip_data.get("loc")
        org = ip_data.get("org")
        hostname = ip_data.get("hostname")

        # Separar latitude e longitude
        latitude, longitude = loc.split(',')

        print(f"IP Address: {ip}")
        print(f"\nHostname: {hostname}")
        print(f"City: {city}")
        print(f"Country: {country}")
        print(f"Region: {region}")              
        print(f"Organization: {org}")
        print(f"\nLocation: {loc}")
        print(f"\nLatitude: {latitude}")
        print(f"Longitude: {longitude}")  

        # Adicionar link do Google Maps
        google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
        print(f"\nGoogle Maps: {google_maps_url}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    website = input("\nDigite o nome do website ou IP (ex. example.com ou IP): ")
    print("\n\nInformações do website\n======================\n")
    get_ip_info(website)

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
