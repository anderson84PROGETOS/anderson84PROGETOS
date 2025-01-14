import socket
import requests
import subprocess
import dns.resolver
import geocoder
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗ ███████╗ ██████╗ ██╗      ██████╗  ██████╗ █████╗ ████████╗    ██████╗ ███╗   ██╗███████╗
██╔════╝ ██╔════╝██╔═══██╗██║     ██╔═══██╗██╔════╝██╔══██╗╚══██╔══╝    ██╔══██╗████╗  ██║██╔════╝
██║  ███╗█████╗  ██║   ██║██║     ██║   ██║██║     ███████║   ██║       ██║  ██║██╔██╗ ██║███████╗
██║   ██║██╔══╝  ██║   ██║██║     ██║   ██║██║     ██╔══██║   ██║       ██║  ██║██║╚██╗██║╚════██║
╚██████╔╝███████╗╚██████╔╝███████╗╚██████╔╝╚██████╗██║  ██║   ██║       ██████╔╝██║ ╚████║███████║
 ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝       ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                                                                                                                                             
""")

def ping_website(website):    
    try:
        # Usando subprocess para evitar exibir todos os detalhes do ping
        result = subprocess.run(
            ["ping", "-n", "1", website],  # Para Linux/Unix/MacOS
            # Para Windows, use: ["ping", "-n", "1", website]  linux ping -c 1
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Exibe apenas se o site está online ou não, sem detalhes do ping
        if result.returncode == 0:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{website} está online\n")
        else:
            print(f"\n{website} não responde ao ping.\n")
    except Exception as e:
        print(f"Ocorreu um erro ao tentar pingar o site: {e}")

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
        
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Provedor: {provedor}\n")
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Cidade: {cidade}\n")
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"País: {pais}")
    except Exception as e:
        print(f"Erro ao obter informações do IP: {e}")

# Função para obter a geolocalização a partir de um IP ou endereço
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
    except Exception as e:
        print(f"Erro ao obter geolocalização do IP: {e}")

def obter_ip(website):
    try:
        ip = socket.gethostbyname(website)
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT +  f"Endereço IP: {ip}\n")
        return ip
    except socket.gaierror:
        print(f"Não foi possível resolver o domínio: {website}")
        return None

def consultar_dns(website):
    try:
        # Consulta os registros A (IP) do site
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nConsultando registros A para: {website}\n")
        respostas = dns.resolver.resolve(website, 'A')
        for resposta in respostas:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{resposta.to_text()}")
    except dns.resolver.NoAnswer:
        print(f"Sem resposta para registros A de {website}")
    except dns.resolver.NXDOMAIN:
        print(f"Domínio {website} não encontrado")
    except Exception as e:
        print(f"Ocorreu um erro ao consultar DNS: {e}")

def main():
    website = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website (exemplo: example.com): ")

    # Realiza o ping
    ping_website(website)

    # Obtém o IP do website
    ip = obter_ip(website)
    
    # Obtém as informações do provedor, caso tenha o IP
    if ip:
        obter_info_provedor(ip)
        obter_geolocalizacao(ip)

    # Consulta os registros DNS
    consultar_dns(website)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
