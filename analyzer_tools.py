import urllib.request
import urllib.error
import socket
import requests
import subprocess
import re
import webbrowser

def analyze_and_check_website(url):
    try:
        response = urllib.request.urlopen("http://" + url, timeout=5)
        print('\nCabeçalhos HTTP do Response\n')
        print(response.headers)
        
        # Verifica o status da conexão
        status_code = response.getcode()
        print(f'\nStatus da conexão: {status_code}')
        if status_code == 200:
            print(f'\nConexão com o {url} estabelecida com sucesso!\n\n')
        else:
            print(f'\nErro ao conectar-se ao {url}: {response.reason}')
    except urllib.error.HTTPError as e:
        # Se a solicitação retornar um código de status 403 (Forbidden)
        if e.code == 403:
            print('\n============== Cabeçalhos HTTP =========================\n')
            print(e.headers)            
        else:
            print(f'\nErro ao conectar-se ao {url}: {e}')
    except Exception as e:
        print(f'\nErro ao conectar-se ao {url}: {e}')

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

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        print("\n\n============== Endereços IPv4 Encontrados ================\n")
        for ipv4_address in ipv4_addresses:
            print(ipv4_address)
    else:
        print("\nNenhum Endereço IPv4 encontrado.")

def get_geolocation_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print("\n\n\n============== Informações de Geolocalização ==============\n")
                print(f"\nProvedor de Internet: {data['isp']}\n")
                print(f"País: {data['country']}")
                print(f"Cidade: {data['city']}")        
                print(f"Latitude: {data['lat']}")
                print(f"Longitude: {data['lon']}")
                return data['lat'], data['lon']
            else:
                print("Erro ao obter informações de geolocalização: status não é 'success'")
                return None, None
        else:
            print(f"Erro ao obter informações de geolocalização: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Erro ao obter informações de geolocalização: {e}")
        return None, None

def obter_informacoes_website(endereco):
    user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}")
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                print("\n\n\n============== Informações sobre o website ================\n") 
                print(f"\nTECNOLOGIAS: {dados['isp']}\n")               
                print(f"\nIP: {dados['query']}")
                print(f"\nPaís: {dados['country']}")
                print(f"\nCidade: {dados['city']}")
                

                # Obtendo informações adicionais usando o Nominatim
                if 'lat' in dados and 'lon' in dados:
                    lat = dados['lat']
                    lon = dados['lon']
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
                    endereco_completo = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
                    if endereco_completo.status_code == 200:
                        endereco_completo = endereco_completo.json()
                        print(f"\nNome da Rua: {endereco_completo['display_name']}")
                        return lat, lon
                    else:
                        print(f"Erro ao obter informações do Nominatim: {endereco_completo.status_code}")
                        return None, None
            else:
                print("Não foi possível obter informações para este endereço.")
                return None, None
        else:
            print(f"Erro ao obter informações do site: {resposta.status_code}")
            return None, None
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None, None

def main():
    print("""

 █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗███████╗██████╗     ████████╗ ██████╗  ██████╗ ██╗     ███████╗
██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
███████║██╔██╗ ██║███████║██║      ╚████╔╝   ███╔╝ █████╗  ██████╔╝       ██║   ██║   ██║██║   ██║██║     ███████╗
██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗       ██║   ██║   ██║██║   ██║██║     ╚════██║
██║  ██║██║ ╚████║██║  ██║███████╗   ██║   ███████╗███████╗██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗███████║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
                                                                                                                  
                                                                                                                
""")

    url = input("\nDigite o nome do website: ").replace('http://', '').replace('https://', '').split('/')[0]
    print("\n")
    analyze_and_check_website(url)
    exibir_ipv4(url)
    ip = socket.gethostbyname(url)
    obter_informacoes_website(url)
    lat, lon = get_geolocation_info(ip)
    if lat and lon:
        google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
        print(f"\nURL do Google Maps: {google_maps_url}")
        open_map = input("\n\nAbrir o mapa do Google com a geolocalização? (s/n): ")
        if open_map.lower() == "s":
            webbrowser.open(google_maps_url)
    
if __name__ == "__main__":
    main()

input("\n\n\n🎯 Pressione Enter para sair 🎯\n")
