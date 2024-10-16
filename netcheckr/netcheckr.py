import subprocess
import re
import socket
import requests
from ipwhois import IPWhois  # Biblioteca para fazer consultas WHOIS

print("""

███╗   ██╗███████╗████████╗ ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗██████╗ 
████╗  ██║██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔══██╗
██╔██╗ ██║█████╗     ██║   ██║     ███████║█████╗  ██║     █████╔╝ ██████╔╝
██║╚██╗██║██╔══╝     ██║   ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══██╗
██║ ╚████║███████╗   ██║   ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗██║  ██║
╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝
                                                                           
""")

print("Verificar IP acesse o site: https://www.abuseipdb.com\n\n")

# Função para obter as conexões do netstat
def obter_ips_netstat():
    saida_netstat = subprocess.check_output(['netstat', '-na']).decode('latin-1')  # Decodifica a saída do netstat
    padrao_ip = re.compile(r'\d+\.\d+\.\d+\.\d+')
    ips = set(re.findall(padrao_ip, saida_netstat))  # Usar 'set' para evitar duplicatas
    return ips

# Função para obter informações WHOIS (incluindo o país)
def obter_informacoes_whois(ip):
    try:
        obj = IPWhois(ip)
        detalhes = obj.lookup_rdap(asn_methods=["whois", "http"])  # Faz consulta WHOIS via RDAP
        pais = detalhes['network']['country']  # Tenta capturar o país
        return pais if pais else 'Desconhecido'
    except Exception:
        return 'Desconhecido'

# Função para verificar a conectividade com o IP (ping básico)
def verificar_conectividade(ip):
    try:
        socket.create_connection((ip, 80), timeout=2)  # Tenta conectar à porta 80 (HTTP)
        return True
    except OSError:
        return False

# Função para obter informações de geolocalização usando ip-api.com
def get_geolocation(domain_or_ip):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
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

# Função principal para executar o script
def main():
    ips = obter_ips_netstat()

    for ip in ips:
        # Ignora IPs locais (127.x.x.x e outros IPs privados)
        if ip.startswith('127.') or ip.startswith('0.') or ip.startswith('10.') or ip.startswith('172.') or ip.startswith('192.168.'):
            print(f"IP privado ou local: {ip}")
            continue

        # Verifica conectividade
        conectado = verificar_conectividade(ip)
        conectividade_msg = "ativo" if conectado else "inativo"
        
        # Consulta o país via WHOIS
        pais = obter_informacoes_whois(ip)

        # Obtém informações de geolocalização
        geo_data = get_geolocation(ip)
        if geo_data and 'country' in geo_data:
            latitude = geo_data.get('lat', 'N/A')
            longitude = geo_data.get('lon', 'N/A')
            organization = geo_data.get('org', 'N/A')  # Obtém o nome da organização

            print(f"\n\nGeolocalização de: {ip}\n")
            print(f"IP: {geo_data['query']}")
            print(f"País: {geo_data['country']}")
            print(f"Cidade: {geo_data['city']}")
            print(f"Organização: {organization}\n")
        else:
            print(f"IP: {ip:<20} está {conectividade_msg} | País: {pais} | Geolocalização: Não disponível")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
