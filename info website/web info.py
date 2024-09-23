import requests
from urllib.parse import urlparse

print("""

██╗    ██╗███████╗██████╗     ██╗███╗   ██╗███████╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗    ██║████╗  ██║██╔════╝██╔═══██╗
██║ █╗ ██║█████╗  ██████╔╝    ██║██╔██╗ ██║█████╗  ██║   ██║
██║███╗██║██╔══╝  ██╔══██╗    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚███╔███╔╝███████╗██████╔╝    ██║██║ ╚████║██║     ╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                            
""")

def acessar_site(url):
    try:
        # Extraindo o hostname da URL
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname        
        
        # Consultando a API do ipwhois.io para obter o nome do provedor
        try:
            ip_info_url = f"https://ipwhois.app/json/{hostname}"
            ip_info_response = requests.get(ip_info_url).json()

            # Formatando a resposta manualmente
            print("\nResposta completa da API\n========================")
            print(f"ip: {ip_info_response.get('ip')}")
            print(f"success: {ip_info_response.get('success')}")
            print(f"type: {ip_info_response.get('type')}")
            print(f"continent: {ip_info_response.get('continent')}")
            print(f"continent_code: {ip_info_response.get('continent_code')}")
            print(f"country: {ip_info_response.get('country')}")
            print(f"country_code: {ip_info_response.get('country_code')}")
            print(f"country_flag: {ip_info_response.get('country_flag')}")
            print(f"country_capital: {ip_info_response.get('country_capital')}")
            print(f"country_phone: {ip_info_response.get('country_phone')}")
            print(f"country_neighbours: {ip_info_response.get('country_neighbours')}")
            print(f"region: {ip_info_response.get('region')}")
            print(f"city: {ip_info_response.get('city')}")
            latitude = ip_info_response.get('latitude')
            longitude = ip_info_response.get('longitude')
            print(f"latitude: {latitude}")
            print(f"longitude: {longitude}")
            print(f"asn: {ip_info_response.get('asn')}")
            print(f"org: {ip_info_response.get('org')}")
            print(f"isp: {ip_info_response.get('isp')}")
            print(f"timezone: {ip_info_response.get('timezone')}")
            print(f"timezone_name: {ip_info_response.get('timezone_name')}")
            print(f"timezone_dstOffset: {ip_info_response.get('timezone_dstOffset')}")
            print(f"timezone_gmtOffset: {ip_info_response.get('timezone_gmtOffset')}")
            print(f"timezone_gmt: {ip_info_response.get('timezone_gmt')}")
            print(f"currency: {ip_info_response.get('currency')}")
            print(f"currency_code: {ip_info_response.get('currency_code')}")
            print(f"currency_symbol: {ip_info_response.get('currency_symbol')}")
            print(f"currency_rates: {ip_info_response.get('currency_rates')}")
            print(f"currency_plural: {ip_info_response.get('currency_plural')}\n\n")            

            maps_url = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude != 'N/A' and longitude != 'N/A' else 'N/A'
            print(f"\nURL do Google Maps: {maps_url}\n")

            # Gerando a URL do Google Maps com base na latitude e longitude
            map_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
            print(f"\nURL do Google Maps: {map_url}")
            
        except Exception as e:
            print(f"Erro ao obter informações de provedor: {e}")
        
        # Definindo cabeçalhos personalizados (exemplo com User-Agent)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Realizando a requisição GET
        response = requests.get(url, headers=headers)
        
        # Exibindo os cabeçalhos da resposta
        print(f"\nStatus Code: {response.status_code}")
        print("\nCabeçalhos da Resposta\n======================\n")
        for header, value in response.headers.items():
            print(f"{header}: {value}")        

    except requests.exceptions.RequestException as e:
        print(f"\n\nErro ao acessar o site: {e}")

if __name__ == "__main__":
    url = input("\nDigite a URL do website: ")
    acessar_site(url)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
