import requests
import builtwith
from colorama import init, Fore, Style
import socket

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

████████╗███████╗ ██████╗██╗  ██╗███╗   ██╗ ██████╗ ██╗      ██████╗  ██████╗      ██████╗ ███████╗ ██████╗     
╚══██╔══╝██╔════╝██╔════╝██║  ██║████╗  ██║██╔═══██╗██║     ██╔═══██╗██╔════╝     ██╔════╝ ██╔════╝██╔═══██╗    
   ██║   █████╗  ██║     ███████║██╔██╗ ██║██║   ██║██║     ██║   ██║██║  ███╗    ██║  ███╗█████╗  ██║   ██║    
   ██║   ██╔══╝  ██║     ██╔══██║██║╚██╗██║██║   ██║██║     ██║   ██║██║   ██║    ██║   ██║██╔══╝  ██║   ██║    
   ██║   ███████╗╚██████╗██║  ██║██║ ╚████║╚██████╔╝███████╗╚██████╔╝╚██████╔╝    ╚██████╔╝███████╗╚██████╔╝    
   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝ ╚═════╝     
                                                                                                                
""")

def obter_organizacao(ip):
    try:
        # Fazendo a consulta à API ipinfo.io para obter informações sobre o IP
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url)
        data = response.json()

        # Verifica se a chave 'org' existe na resposta
        organizacao = data.get('org', 'Organização não encontrada')

        # Caso não encontre organização, retorna mensagem padrão
        if organizacao == 'Organização não encontrada':
            return "Organização não disponível"
        
        return organizacao
    except requests.exceptions.RequestException as e:
        return f"Erro ao buscar organização: {e}"

def get_geolocation(ip):
    try:
        ip_response = requests.get(f"https://ipinfo.io/{ip}/json")
        ip_data = ip_response.json()        
        
        city = ip_data.get("city", "Cidade não encontrada")
        country = ip_data.get("country", "País não encontrado")
        region = ip_data.get("region", "Região não encontrada")
        loc = ip_data.get("loc", "Coordenadas não encontradas")

        if loc != "Coordenadas não encontradas":
            latitude, longitude = loc.split(',')
            google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
            street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
        else:
            latitude = longitude = google_maps_url = street_view_url = "Não disponível"

        return city, country, region, latitude, longitude, google_maps_url, street_view_url
    except Exception as e:
        return "Erro ao buscar localização", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro"

def identificar_tecnologias(site):
    # Verifica se o site já possui "http://" ou "https://"
    if not site.startswith(("http://", "https://")):
        site = "http://" + site  # Adiciona HTTP caso o usuário não insira

    try:
        response = requests.get(site, timeout=5)

        # Exibe as tecnologias identificadas apenas se o código de status for 200
        if response.status_code == 200:
            tecnologias = builtwith.builtwith(site)
            
            # Exibe as tecnologias identificadas
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\n=== Tecnologias Identificadas ===\n")
            for categoria, lista in tecnologias.items():
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{categoria}: {', '.join(lista)}")

        # Exibe os cabeçalhos HTTP independentemente do código de status
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\n=== Cabeçalhos HTTP ===\n")
        for header, value in response.headers.items():
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{header}: {value}")
        
        # Exibe o código de status e a mensagem associada        
        if response.status_code == 200:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nStatus: 200 OK")
        elif response.status_code == 403:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nCódigo de status: Acesso proibido (403)")        

        # Obtemos o IP do site usando o módulo socket
        ip = socket.gethostbyname(site.split("//")[-1].split("/")[0])

        # Consultar a organização associada ao IP
        organizacao = obter_organizacao(ip)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nOrganização: {organizacao}")

        # Obter a geolocalização do IP
        city, country, region, latitude, longitude, google_maps_url, street_view_url = get_geolocation(ip)
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nCidade: {city}")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"País: {country}")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Região: {region}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nGeolocalização: {latitude},{longitude}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nGoogle Maps: {google_maps_url}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nStreet View: {street_view_url}")

    except requests.exceptions.RequestException as e:
        print(f"Não foi possível conectar ao site. Erro: {e}")
    except socket.gaierror:
        print("Não foi possível resolver o IP do site.")

if __name__ == "__main__":
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do site: ")
    identificar_tecnologias(site)

input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
