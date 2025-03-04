import requests
import json
from colorama import Fore, Style, init
from datetime import datetime
import pytz
import math
import socket

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗███╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ███╗ █████╗ ███████╗███████╗    ██╗██████╗ 
██║████╗  ██║██╔════╝██╔═══██╗██╔══██╗████╗ ████║██╔══██╗██╔════╝██╔════╝    ██║██╔══██╗
██║██╔██╗ ██║█████╗  ██║   ██║██████╔╝██╔████╔██║███████║█████╗  ███████╗    ██║██████╔╝
██║██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║██╔══██║██╔══╝  ╚════██║    ██║██╔═══╝ 
██║██║ ╚████║██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║██║  ██║███████╗███████║    ██║██║     
╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝╚═╝     
                                                                                     
""")

def generate_reference_ip(origin_ip):
    # Gera um IP de referência fictício baseado no IP de origem
    if origin_ip == 'N/A':
        return "192.168.1.254"  # Padrão se não houver IP de origem
    try:
        # Divide o IP de origem em octetos
        octets = origin_ip.split('.')
        # Altera os dois últimos octetos para criar um IP fictício próximo
        new_octets = octets[:2] + [str((int(octets[2]) + 1) % 256), str((int(octets[3]) + 1) % 256)]
        return '.'.join(new_octets)
    except (ValueError, IndexError):
        return "192.168.1.254"  # Retorna padrão em caso de erro

def get_ip_info(ip=None):
    # URL da API que retorna informações do IP público do usuário
    url = "http://ipwhois.app/json/" + (ip if ip else "")
    response = requests.get(url)
    
    # Verifica se a requisição foi bem-sucedida (status 200)
    if response.status_code == 200:
        # Converte a resposta JSON em um dicionário Python
        data = response.json()
        origin_ip = data.get('ip', 'N/A')  # IP de origem
        latitude = float(data.get('latitude', 0)) if data.get('latitude') else 0
        longitude = float(data.get('longitude', 0)) if data.get('longitude') else 0
        timezone = data.get('timezone', 'UTC')  # Pega o fuso horário retornado pela API
        city = data.get('city', 'Desconhecida')  # Cidade retornada pela API
        
        # Obtém a hora local com base no fuso horário
        try:
            tz = pytz.timezone(timezone)
            local_time = datetime.now(tz).strftime('%H:%M:%S %d/%m/%Y')
        except pytz.exceptions.UnknownTimeZoneError:
            local_time = "Fuso horário desconhecido, usando UTC: " + datetime.now(pytz.UTC).strftime('%H:%M:%S %d/%m/%Y')

        # Formata as informações com cores usando colorama
        formatted_data = (
            f"{Fore.LIGHTGREEN_EX}IP de Origem: {Fore.LIGHTCYAN_EX}{origin_ip}\n"
            f"{Fore.LIGHTGREEN_EX}País: {Fore.LIGHTCYAN_EX}{data.get('country', 'N/A')} ({data.get('country_code', 'N/A')})\n"
            f"{Fore.LIGHTGREEN_EX}Região: {Fore.LIGHTCYAN_EX}{data.get('region', 'N/A')}\n"
            f"{Fore.LIGHTGREEN_EX}Cidade: {Fore.LIGHTCYAN_EX}{city}\n"            
            f"{Fore.LIGHTGREEN_EX}Organização: {Fore.LIGHTCYAN_EX}{data.get('org', 'N/A')}\n"
            f"{Fore.LIGHTGREEN_EX}ASN: {Fore.LIGHTCYAN_EX}{data.get('asn', 'N/A')}\n\n" 
            f"{Fore.LIGHTMAGENTA_EX}Hora Local: {Fore.LIGHTGREEN_EX}{local_time}\n\n"       
            f"{Fore.LIGHTGREEN_EX}Latitude: {Fore.LIGHTCYAN_EX}{latitude}\n"
            f"{Fore.LIGHTGREEN_EX}Longitude: {Fore.LIGHTCYAN_EX}{longitude}\n"
        )
        print(formatted_data)
        
        # Exibe a geolocalização em formato de coordenadas
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Geolocalização do IP de Origem: ", end="")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{latitude}, {longitude}")
        
        # Link para o Google Maps
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nGoogle Maps (Origem): ", end="")            
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"https://www.google.com/maps?q={latitude},{longitude}\n")
        
        # Link para o Street View
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Street View (Origem): ", end="")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}")

        # Define uma localização de referência (simulada) para o "outro IP"
        provider_lat = latitude + (0.045 if latitude > 0 else -0.045)  # ~5 km norte/sul
        provider_lon = longitude + (0.045 if longitude > 0 else -0.045)  # ~5 km leste/oeste
        # Gera o IP de referência baseado no IP de origem
        provider_ip = generate_reference_ip(origin_ip)

        # Calcula a distância entre a localização do IP de origem e o ponto de referência
        distance_meters = haversine_distance(latitude, longitude, provider_lat, provider_lon)
        distance_km = distance_meters / 1000  # Converte para quilômetros

        # Determina se está "perto" ou "longe"
        if distance_km < 1:
            proximity = "perto"
        elif distance_km > 10:
            proximity = "longe"
        else:
            proximity = "distância moderada"

        # Exibe o "outro IP" e a distância
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nIP de Referência (estimado): ", end="")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{provider_ip}\n")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Geolocalização do IP de Referência: ", end="")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{provider_lat}, {provider_lon}\n")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Distância estimada do ponto de origem do IP: ", end="")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{distance_meters:.2f} metros ({distance_km:.2f} km) - {proximity}")
    else:
        # Exibe mensagem de erro se a requisição falhar
        print(Fore.RED + f"Erro ao obter informações do IP: {response.status_code}")

def haversine_distance(lat1, lon1, lat2, lon2):
    # Raio da Terra em metros
    R = 6371000
    
    # Converte graus para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças nas coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

if __name__ == "__main__":
    # Solicita input do usuário
    user_input = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite Enter (IP atual), um IP ou o nome de um website: ")
    print("\n")
    if user_input == "":
        # Se Enter for pressionado, usa o IP atual
        get_ip_info()
    else:
        try:
            # Tenta resolver o input como um nome de website
            ip = socket.gethostbyname(user_input)
            print(Fore.LIGHTGREEN_EX + f"IP resolvido para: {user_input}\n")
            get_ip_info(ip)
        except socket.gaierror:
            # Se não for um website válido, assume que é um IP
            print(Fore.LIGHTGREEN_EX + f"Assumindo que '{user_input}' é um IP...")
            get_ip_info(user_input)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
