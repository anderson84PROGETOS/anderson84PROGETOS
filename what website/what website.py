import subprocess
import re
import requests
from bs4 import BeautifulSoup

print("""

██╗    ██╗██╗  ██╗ █████╗ ████████╗    ██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗
██║    ██║██║  ██║██╔══██╗╚══██╔══╝    ██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝
██║ █╗ ██║███████║███████║   ██║       ██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗  
██║███╗██║██╔══██║██╔══██║   ██║       ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝  
╚███╔███╔╝██║  ██║██║  ██║   ██║       ╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝        ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝
                                                                                           
""")

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_informacoes_ips(ips, site):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    for ip in ips:
        try:
            resposta = requests.get(f"http://ip-api.com/json/{ip}", headers={'User-Agent': 'Mozilla/5.0'})
            if resposta.status_code == 200:
                dados = resposta.json()
                if dados['status'] == 'success':
                    print("\n\nInformações do website e IP\n===========================")
                    print(f"Status       : {resposta.status_code} {resposta.reason}")
                    
                    # Obter o título do site (removido o print do título)
                    resposta_site = requests.get(f"http://{site}", headers=headers)
                    soup = BeautifulSoup(resposta_site.text, 'html.parser')
                    titulo = soup.title.string if soup.title else 'Título não encontrado'
                    
                    print(f"Website IP   : {ip}\n")
                    print(f"Company      : {dados['isp']}\n")
                    print(f"ZIP Code     : {dados.get('zip', 'N/A')}")
                    print(f"Timezone     : {dados.get('timezone', 'N/A')}\n")
                    print(f"Region       : {dados.get('region', 'N/A')} - {dados.get('regionName', 'N/A')}")                    
                    print(f"Country      : {dados.get('country', 'N/A')} ({dados.get('countryCode', 'N/A')})")
                    print(f"City         : {dados.get('city', 'N/A')}")
                    print(f"Latitude     : {dados.get('lat', 'N/A')}")
                    print(f"Longitude    : {dados.get('lon', 'N/A')}")

                    # Obtém informações completas do endereço
                lat, lon = dados.get('lat'), dados.get('lon')
                if lat and lon:
                    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36'}
                    endereco_completo = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
                    if endereco_completo.status_code == 200:
                        endereco_completo = endereco_completo.json()
                        print("")
                        print(f"Nome da Rua  : {endereco_completo['display_name']}\n")                        
                        google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                        print(f"Google Maps  : {google_maps_url}\n")
                        google_street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80"                                         
                        print(f"Google Street View: {google_street_view_url}")
                else:
                    print(f"Erro ao obter informações para o IP {ip}: {dados['message']}")
            else:
                print(f"Erro ao consultar API para o IP {ip}: Código {resposta.status_code}")
        except Exception as e:
            print(f"Erro ao obter informações para o IP {ip}: {str(e)}")

def obter_informacoes_do_site(site):
    if site.startswith(('http://', 'https://')):
        site = site.split('//')[1]

    print(f"\nObtendo IP para o site: {site}")
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        print(f"\nIP Encontrados para: {site}\n")
        for ip in ipv4_addresses:
            print(f"Website IP   : {ip}")

        exibir_informacoes_ips(ipv4_addresses, site)
    else:
        print("Nenhum endereço IPv4 encontrado.")

if __name__ == "__main__":
    alvo = input("\nDigite a URL do website: ").strip()
    obter_informacoes_do_site(alvo)

input("\n\nPRESSIONE ENTER PARA SAIR\n")
