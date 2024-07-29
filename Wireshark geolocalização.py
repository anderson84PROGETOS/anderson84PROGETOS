import os
from scapy.all import rdpcap
import requests

# Função para obter IPs de um pacote
def get_ips_from_packet(packet):
    ips = set()
    if packet.haslayer('IP'):
        src_ip = packet['IP'].src
        dst_ip = packet['IP'].dst
        ips.add(src_ip)
        ips.add(dst_ip)
    return ips

try:
    # Solicita ao usuário o nome do arquivo .pcapng
    file_name = input("\nDigite o nome do arquivo .pcapng: ")
    print("\n")
    
    # Caminho absoluto para o arquivo .pcapng
    file_path = os.path.abspath(file_name)

    # Verifica se o arquivo existe
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Arquivo {file_path} não encontrado.")

    # Carregar o arquivo .pcapng
    packets = rdpcap(file_path)

    # Extrair IPs
    ips = set()
    for packet in packets:
        ips.update(get_ips_from_packet(packet))

    # Armazenar resultados em uma lista
    results = []

    # Realizar a geolocalização
    for ip in ips:
        response = requests.get(f'https://ipapi.co/{ip}/json/')
        
        if response.status_code == 200:
            data = response.json()
            ip_addr = data.get('ip', 'N/A')
            city = data.get('city', 'N/A')
            region = data.get('region', 'N/A')
            country = data.get('country_name', 'N/A')
            latitude = data.get('latitude', 'N/A')
            longitude = data.get('longitude', 'N/A')

            result = (f"IP: {ip_addr}\n"
                      f"Location: {city}, {region}, {country}\n"
                      f"Latitude: {latitude}, Longitude: {longitude}\n")
            if latitude != 'N/A' and longitude != 'N/A':
                google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
                result += f"Google Maps: {google_maps_url}\n"
            
            results.append(result)
            print(result)
        else:
            print(f"\nErro ao obter dados para IP: {ip}")

    # Perguntar se o usuário deseja salvar as informações em um arquivo
    save = input("\nDeseja salvar todas as informações em um arquivo? (s/n): ").strip().lower()
    if save == 's':
        output_file = input("\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
        with open(output_file, 'w') as f:
            for result in results:
                f.write(result + "\n")
        print(f"\nInformações salvas em: {output_file}")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
