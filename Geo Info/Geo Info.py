import requests
import socket

print("""

 ██████╗ ███████╗ ██████╗     ██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝ ██╔════╝██╔═══██╗    ██║████╗  ██║██╔════╝██╔═══██╗
██║  ███╗█████╗  ██║   ██║    ██║██╔██╗ ██║█████╗  ██║   ██║
██║   ██║██╔══╝  ██║   ██║    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚██████╔╝███████╗╚██████╔╝    ██║██║ ╚████║██║     ╚██████╔╝
 ╚═════╝ ╚══════╝ ╚═════╝     ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                            
""")

def obter_informacoes_ip(ip):
    # Usando a API ipinfo.io
    url_ipinfo = f"https://ipinfo.io/{ip}/json"
    try:
        resposta = requests.get(url_ipinfo)
        resposta.raise_for_status()  # Lança um erro para códigos de status 4xx/5xx

        # Converte a resposta JSON em um dicionário Python
        informacoes = resposta.json()

        # Exibe as informações obtidas da API ipinfo.io
        print(f"\n\nEndereço IP: {informacoes.get('ip')}")
        print(f"\nHostname: {informacoes.get('hostname')}")
        print(f"\nOrganização: {informacoes.get('org')}")
        print(f"\nLocalização: {informacoes.get('city')}, {informacoes.get('region')}, {informacoes.get('country')}")
        print("\n\nGeolocalização:", informacoes.get('loc'))
        print("")

        # Obtendo latitude e longitude para links do Google Maps e Street View
        loc = informacoes.get('loc', '').split(',')
        if len(loc) == 2:
            latitude = loc[0]
            longitude = loc[1]           
            print(f"Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
            print(f"\nStreet View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}")
            print("==================================================================================================")
        else:
            print("Informações de localização geográfica não disponíveis.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter informações sobre o IP: {e}")

    # Usando a API ip-api
    url_ip_api = f"http://ip-api.com/json/{ip}"
    try:
        resposta = requests.get(url_ip_api)
        resposta.raise_for_status()  # Lança um erro para códigos de status 4xx/5xx

        # Converte a resposta JSON em um dicionário Python
        informacoes = resposta.json()

        # Exibe as informações obtidas da API ip-api
        print(f"\n\nEndereço IP: {informacoes.get('query')}")
        print(f"\nHostname: {informacoes.get('as')}")
        print(f"\nOrganização: {informacoes.get('org')}")
        print(f"\nLocalização: {informacoes.get('city')}, {informacoes.get('regionName')}, {informacoes.get('country')}")
        print("\n\nGeolocalização:", informacoes.get('lat'), informacoes.get('lon'))
        print("")
        # Obtendo latitude e longitude para links do Google Maps e Street View
        latitude = informacoes.get('lat')
        longitude = informacoes.get('lon')
        if latitude and longitude:
            print(f"Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
            print(f"\nStreet View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}")
        else:
            print("Informações de localização geográfica não disponíveis.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter informações sobre o IP: {e}")

def resolver_ip_ou_website(nome_entrada):
    try:
        # Tenta resolver o nome do website para um endereço IP
        ip = socket.gethostbyname(nome_entrada)        
        return ip
    except socket.gaierror:
        # Se não for um nome de domínio válido, assume que é um IP
        return nome_entrada

# Solicita ao usuário o IP ou o nome do website para consulta
entrada_usuario = input("\nDigite o Endereço IP ou o nome do website: ")

# Resolve o nome do website, se necessário, para obter o IP
ip_final = resolver_ip_ou_website(entrada_usuario)

# Obtém as informações detalhadas sobre o IP usando ambas as APIs
obter_informacoes_ip(ip_final)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
