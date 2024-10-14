import requests

print("""
 ██████╗ ███████╗ ██████╗ ███████╗██████╗ ██╗   ██╗
██╔════╝ ██╔════╝██╔═══██╗██╔════╝██╔══██╗╚██╗ ██╔╝
██║  ███╗█████╗  ██║   ██║███████╗██████╔╝ ╚████╔╝ 
██║   ██║██╔══╝  ██║   ██║╚════██║██╔═══╝   ╚██╔╝  
╚██████╔╝███████╗╚██████╔╝███████║██║        ██║   
 ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝        ╚═╝   
                                                   
""")

# Função para obter informações de geolocalização usando ip-api.com
def get_geolocation(domain_or_ip):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Faz a solicitação GET para a API ip-api.com
    response = requests.get(f'http://ip-api.com/json/{domain_or_ip}', headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: Status code {response.status_code}")
        return None

# Função para obter o nome da rua usando Nominatim (OpenStreetMap)
def get_street_name(lat, lon):
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
    response = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter nome da rua: Status code {response.status_code}")
        return None

# Exemplo de uso
if __name__ == '__main__':
    domain_or_ip = input("\nDigite o endereço IP ou nome de domínio: ")
    geo_data = get_geolocation(domain_or_ip)

    if geo_data:
        latitude = geo_data.get('lat', 'N/A')
        longitude = geo_data.get('lon', 'N/A')
        organization = geo_data.get('org', 'N/A')  # Obtém o nome da organização

        print(f"\nGeolocalização de: {domain_or_ip}\n")
        print(f"IP: {geo_data['query']}")
        print(f"País: {geo_data['country']}")
        print(f"Cidade: {geo_data['city']}")
        print(f"Organização: {organization}\n")  # Exibe o nome da organização
        

        # Obtendo o nome da rua
        street_data = get_street_name(latitude, longitude)
        if street_data:
            print(f"Nome da Rua: {street_data.get('display_name', 'N/A')}\n")
            print(f"\nLatitude: {latitude}, Longitude: {longitude}")
        # Gerando URL do Google Street View        
        google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}\n"
        street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80" if latitude != 'N/A' and longitude != 'N/A' else 'N/A'
        
        # Exibe as URLs
        print(f"\n\nGoogle Maps: {google_maps_url}\n")
        print(f"Google Street View: {street_view_url}\n")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
