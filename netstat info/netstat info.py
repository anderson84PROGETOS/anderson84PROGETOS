import subprocess
import re
import socket
import requests
from ipwhois import IPWhois  # Biblioteca para fazer consultas WHOIS

print(""" 

███╗   ██╗███████╗████████╗███████╗████████╗ █████╗ ████████╗    ██╗███╗   ██╗███████╗ ██████╗ 
████╗  ██║██╔════╝╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝    ██║████╗  ██║██╔════╝██╔═══██╗
██╔██╗ ██║█████╗     ██║   ███████╗   ██║   ███████║   ██║       ██║██╔██╗ ██║█████╗  ██║   ██║
██║╚██╗██║██╔══╝     ██║   ╚════██║   ██║   ██╔══██║   ██║       ██║██║╚██╗██║██╔══╝  ██║   ██║
██║ ╚████║███████╗   ██║   ███████║   ██║   ██║  ██║   ██║       ██║██║ ╚████║██║     ╚██████╔╝
╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝       ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                                                              
""")

print("Verificar IP acesse o site: https://www.abuseipdb.com\n\n")

# User-Agent padrão
USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para obter as conexões do netstat
def obter_ips_netstat():
    saida_netstat = subprocess.check_output(['netstat', '-na']).decode('latin-1')
    padrao_ip = re.compile(r'\d+\.\d+\.\d+\.\d+')
    ips = set(re.findall(padrao_ip, saida_netstat))  # Usar 'set' para evitar duplicatas
    return ips

# Função para obter informações WHOIS
def obter_informacoes_whois(ip):
    try:
        obj = IPWhois(ip)
        detalhes = obj.lookup_rdap(asn_methods=["whois", "http"])
        pais = detalhes['network'].get('country', 'Desconhecido')
        return pais
    except Exception:
        return 'Desconhecido'

# Função para verificar a conectividade com o IP
def verificar_conectividade(ip):
    try:
        socket.create_connection((ip, 80), timeout=2)
        return True
    except OSError:
        return False

# Função para obter informações de geolocalização usando ip-api.com
def get_geolocation(domain_or_ip):
    response = requests.get(f'http://ip-api.com/json/{domain_or_ip}', headers=USER_AGENT)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: Status code {response.status_code}")
        return None

# Função principal para executar o script
def main():
    ips = obter_ips_netstat()

    for ip in ips:
        if ip.startswith(('127.', '0.', '10.', '172.', '192.168.')):
            print(f"IP privado ou local: {ip}")
            continue

        conectado = verificar_conectividade(ip)
        conectividade_msg = "ativo" if conectado else "inativo"

        pais = obter_informacoes_whois(ip)
        geo_data = get_geolocation(ip)

        if geo_data and 'country' in geo_data:
            latitude = geo_data.get('lat', 'N/A')
            longitude = geo_data.get('lon', 'N/A')
            organizacao = geo_data.get('org', 'N/A')
            
            print("=====================================================")
            print(f"\n\nGeolocalização de: {ip}\n")
            print(f"IP: {geo_data['query']}")
            print(f"País: {geo_data['country']}")
            print(f"Cidade: {geo_data['city']}")
            print(f"Organização: {organizacao}")
            print(f"\nLatitude: {latitude}")
            print(f"Longitude: {longitude}")

            # Gerando URLs do Google Maps e Street View
            google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}\n"
            street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
            print(f"\nGoogle Maps: {google_maps_url}")
            print(f"Google Street View: {street_view_url}\n")
        else:
            print(f"IP: {ip:<20} está {conectividade_msg} | País: {pais} | Geolocalização: Não disponível")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
