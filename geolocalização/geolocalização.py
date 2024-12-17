import requests
import socket
import webbrowser
from datetime import datetime

print("""
 ██████╗ ███████╗ ██████╗ ██╗      ██████╗  ██████╗ █████╗ ██╗     ██╗███████╗ █████╗  ██████╗ 
██╔════╝ ██╔════╝██╔═══██╗██║     ██╔═══██╗██╔════╝██╔══██╗██║     ██║╚══███╔╝██╔══██╗██╔═══██╗
██║  ███╗█████╗  ██║   ██║██║     ██║   ██║██║     ███████║██║     ██║  ███╔╝ ███████║██║   ██║
██║   ██║██╔══╝  ██║   ██║██║     ██║   ██║██║     ██╔══██║██║     ██║ ███╔╝  ██╔══██║██║   ██║
╚██████╔╝███████╗╚██████╔╝███████╗╚██████╔╝╚██████╗██║  ██║███████╗██║███████╗██║  ██║╚██████╔╝
 ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
""")

# Solicita ao usuário o nome do site ou IP
entrada = input("Digite o nome do site ou o IP: ")

# Se a entrada for um nome de site, converte para IP
if not entrada.replace('.', '').isdigit():  # Verifica se não é um IP
    try:
        ip = socket.gethostbyname(entrada)  # Converte nome de domínio para IP
        print(f"\n\nwebsite: {entrada}    IP: {ip}")
    except socket.gaierror:
        print("Não foi possível resolver o domínio.")
        exit()
else:
    ip = entrada  # Se for um IP, usa diretamente

# Consulta à API para geolocalização
response = requests.get(f"http://ip-api.com/json/{ip}")
geo_data = response.json()

# Exibe a geolocalização
if geo_data['status'] == 'fail':
    print("Não foi possível obter geolocalização para esse IP.")
else:
    print(f"\n\nOrganização ISP: {geo_data.get('isp')}\n")
    print(f"AS: {geo_data.get('as')}\n")

    # Exibindo a data e hora atual
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    print(f"\nData e Hora Atual: {current_time}\n")

    # Exibe a resposta formatada
    print(f"Status: {geo_data['status']}\n")
    print(f"País: {geo_data.get('country')}")
    print(f"País (Código): {geo_data.get('countryCode')}")
    print(f"Região: {geo_data.get('region')}")
    print(f"Nome da Região: {geo_data.get('regionName')}")
    print(f"Cidade: {geo_data.get('city')}")
    print(f"Código Postal: {geo_data.get('zip')}")    
    print(f"Fuso Horário: {geo_data.get('timezone')}")    
    print(f"\nLatitude: {geo_data.get('lat')}")
    print(f"Longitude: {geo_data.get('lon')}")
    
    # Obtendo as coordenadas
    latitude = geo_data.get('lat')
    longitude = geo_data.get('lon')

    print(f"\nCoordenadas: {latitude}, {longitude}\n")

    # Gerando os links para Google Maps e Google Street View
    google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}\n"
    google_street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"

    print(f"\nGoogle Maps: {google_maps_url}")
    print(f"Google Street View: {google_street_view_url}")

    # Pergunta ao usuário qual link deseja abrir
    print("\n\n\nEscolha uma opção para abrir\n")
    print("Google Maps = 1")
    print("Google Street View = 2")
    escolha = input("\nDigite 1 ou 2 para selecionar: ").strip()

    if escolha == '1':
        # Abre o local no Google Maps
        webbrowser.open(google_maps_url)
    elif escolha == '2':
        # Abre o local no Google Street View
        webbrowser.open(google_street_view_url)
    else:
        print("\n\nEscolha inválida. Nenhum link será aberto.")    

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
