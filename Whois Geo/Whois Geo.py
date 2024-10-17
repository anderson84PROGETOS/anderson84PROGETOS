import socket
import requests
from ipwhois import IPWhois
from bs4 import BeautifulSoup
import re

print("""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗     ██████╗ ███████╗ ██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔════╝ ██╔════╝██╔═══██╗
██║ █╗ ██║███████║██║   ██║██║███████╗    ██║  ███╗█████╗  ██║   ██║
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║   ██║██╔══╝  ██║   ██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ╚██████╔╝███████╗╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝     ╚═════╝ ╚══════╝ ╚═════╝ 
                                                                   
""")

# Dicionário de servidores WHOIS para diferentes TLDs
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br'
}

# Função para realizar requisições WHOIS
def requisicao_whois(servidor_whois, endereco_host, padrao):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as objeto_socket:
        try:
            objeto_socket.connect((servidor_whois, 43))
            if padrao:
                if servidor_whois == 'whois.verisign-grs.com':  # Para domínios .com e .net
                    objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
                else:
                    objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'{endereco_host}\r\n'.encode())
                
            resposta = b""
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                resposta += dados
            return resposta.decode('latin-1')
        except Exception as e:
            return f"Erro: {str(e)}"

# Função para obter informações WHOIS usando requisições
def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    try:
        response_whois = requests.get(url_whois)
        response_registro_br = requests.get(url_registro_br)

        if response_whois.status_code == 200:
            soup_whois = BeautifulSoup(response_whois.text, "html.parser")
            whois_section = soup_whois.find("pre", class_="df-raw")
            if whois_section:
                whois_text = whois_section.get_text()
                print("\nInformações WHOIS (whois.com)\n")
                print(whois_text)

        if response_registro_br.status_code == 200:
            soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
            div_result = soup_registro_br.find("div", class_="result")
            if div_result:
                result_text = div_result.get_text()
                print("\nInformações WHOIS (registro.br)\n")
                print(result_text)
    except Exception as e:
        print(f"Erro: {str(e)}")

# Função para obter WHOIS específico para domínios .br
def obter_whois_br(endereco):
    servidor_whois = servidores_whois_tdl['.br']
    resposta = requisicao_whois(servidor_whois, endereco, False)
    print("\nInformações WHOIS (registro.br)\n")
    print(resposta)

# Função para obter geolocalização usando ip-api.com
def get_geolocation(domain_or_ip):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    response = requests.get(f'http://ip-api.com/json/{domain_or_ip}', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: Status code {response.status_code}")
        return None

# Função para obter nome da rua usando Nominatim (OpenStreetMap)
def get_street_name(lat, lon):
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
    response = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter nome da rua: Status code {response.status_code}")
        return None

# Função principal
def main():
    dominio = input("\nDigite o IP ou nome do website: ").strip()

    # Verificar se é .br para usar o servidor WHOIS adequado
    if dominio.endswith('.br'):
        obter_whois_br(dominio)
    else:
        obter_whois(dominio)

    # Obter geolocalização
    geo_data = get_geolocation(dominio)
    if geo_data:
        latitude = geo_data.get('lat', 'N/A')
        longitude = geo_data.get('lon', 'N/A')
        organization = geo_data.get('org', 'N/A')  # Obtém o nome da organização

        print("=================================")
        print(f"\nGeolocalização de: {dominio}\n")
        print(f"IP: {geo_data['query']}")
        print(f"País: {geo_data['country']}")
        print(f"Cidade: {geo_data['city']}")
        print(f"Organização: {organization}\n")  # Exibe o nome da organização
        
        # Obtendo o nome da rua
        street_data = get_street_name(latitude, longitude)
        if street_data:
            print(f"Nome da Rua: {street_data.get('display_name', 'N/A')}\n")
            print(f"\nLatitude: {latitude}, Longitude: {longitude}")
        
        # Gerando URL do Google Maps e Street View        
        google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}\n"
        street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80" if latitude != 'N/A' and longitude != 'N/A' else 'N/A'
        
        # Exibe as URLs
        print(f"\nGoogle Maps: {google_maps_url}\n")
        print(f"Google Street View: {street_view_url}\n")

main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
