import re
import socket
import dns.resolver
import requests
import geocoder
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗ ███████╗██╗███╗   ██╗████████╗    ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗
██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝    ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║
██║   ██║███████╗██║██╔██╗ ██║   ██║       ██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║
██║   ██║╚════██║██║██║╚██╗██║   ██║       ██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║
╚██████╔╝███████║██║██║ ╚████║   ██║       ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
 ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝       ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
                                                                                           
""")

def obter_info_provedor(ip):
    url = f"https://ipinfo.io/{ip}/json"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        provedor = dados.get("org", "Provedor não encontrado")
        cidade = dados.get("city", "Cidade não disponível")
        codigo_pais = dados.get("country", None)
        
        # Obter nome completo do país
        if codigo_pais:
            pais_url = f"https://restcountries.com/v3.1/alpha/{codigo_pais}"
            pais_resposta = requests.get(pais_url)
            pais_dados = pais_resposta.json()
            pais = pais_dados[0].get("name", {}).get("common", "País não disponível")
        else:
            pais = "País não disponível"

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nProvedor: {provedor}\n")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Cidade: {cidade}\n")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"País: {pais}")
        
        return pais  # Retornando o nome do país para uso posterior
    except Exception as e:
        print(f"Erro ao obter informações do IP: {e}")
        return None


def get_street_name(lat, lon):
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
    response = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)

    if response.status_code == 200:
        return response.json().get('display_name', 'Nome da rua não disponível')
    else:
        print(f"Erro ao obter nome da rua: Status code {response.status_code}")
        return 'Nome da rua não disponível'


def obter_geolocalizacao(ip):
    try:
        g = geocoder.ip(ip)
        if g.ok:
            cidade = g.city
            pais = g.country
            latitude = g.latlng[0]
            longitude = g.latlng[1]
            
            # Exibindo a geolocalização no formato solicitado
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nGeolocalização: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{latitude},{longitude}")
            
            # Gerando URLs do Google Maps e Street View
            google_maps_url = Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"https://www.google.com/maps?q={latitude},{longitude}\n"
            street_view_url = Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
                    
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nURL do Google Maps: {google_maps_url}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"URL do Google Street View: {street_view_url}")

            # Obtendo o nome da rua
            street_name = get_street_name(latitude, longitude)
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nNome da Rua: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{street_name}")

    except Exception as e:
        print(f"Erro ao obter geolocalização do IP: {e}")

def domain_ip_lookup(domain_or_ip):
    print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n[+] Realizando consulta no domínio: {domain_or_ip}")
    
    try:
        # Verifica se é um IP com formato IPv4
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain_or_ip):
            host = socket.gethostbyaddr(domain_or_ip)
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\n[+] IP Resolvido: {host[0]}")
            
            # Obtendo informações do provedor
            pais = obter_info_provedor(domain_or_ip)
            
            # Obtendo geolocalização
            obter_geolocalizacao(domain_or_ip)
            
        else:  # Caso seja um domínio
            result = dns.resolver.resolve(domain_or_ip, 'A')  # Consulta registros A (endereço IP)
            for ipval in result:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\n[+] IP Resolvido: {ipval.to_text()}")
                
                # Obtendo informações do provedor para cada IP
                pais = obter_info_provedor(ipval.to_text())
                
                # Obtendo geolocalização para cada IP
                obter_geolocalizacao(ipval.to_text())
                
    except Exception:
        print(Fore.LIGHTWHITE_EX + Style.BRIGHT + "\n[-] Não achou nada na consulta")

if __name__ == "__main__":    
    domain_or_ip = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o IP ou nome do domínio: ")
    print()  # Adiciona uma linha em branco após a entrada
    domain_ip_lookup(domain_or_ip)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
