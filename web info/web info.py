import socket
import requests
import whois
from prettytable import PrettyTable
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """ 
██╗    ██╗███████╗██████╗     ██╗███╗   ██╗███████╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗    ██║████╗  ██║██╔════╝██╔═══██╗
██║ █╗ ██║█████╗  ██████╔╝    ██║██╔██╗ ██║█████╗  ██║   ██║
██║███╗██║██╔══╝  ██╔══██╗    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚███╔███╔╝███████╗██████╔╝    ██║██║ ╚████║██║     ╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                   
""")

def formatar_data(data):
    if isinstance(data, list):
        data = data[0]
    if isinstance(data, datetime):
        return data.strftime("%d/%m/%Y")
    return "Desconhecido"

def geolocalizar_ip(ip):
    try:
        url = f"http://ip-api.com/json/{ip}"
        resposta = requests.get(url, timeout=5)
        dados = resposta.json()

        if dados["status"] == "success":
            return {
                "país": dados.get("country", "Desconhecido"),
                "região": dados.get("regionName", "Desconhecido"),
                "cidade": dados.get("city", "Desconhecido"),
                "isp": dados.get("isp", "Desconhecido"),
                "lat": dados.get("lat", "Desconhecido"),
                "lon": dados.get("lon", "Desconhecido"),
                "as": dados.get("as", "Desconhecido")  # Ex: "AS15169 Google LLC"
            }
    except:
        pass
    return {}

def obter_info_site(site):
    if not site.startswith("http"):
        url = "http://" + site
    else:
        url = site

    dominio = site.replace("http://", "").replace("https://", "").split("/")[0]

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n🔍 Coletando informações de: {dominio}")

    try:
        ip = socket.gethostbyname(dominio)
    except socket.gaierror:
        print("❌ Não foi possível resolver o IP.")
        return

    try:
        w = whois.whois(dominio)
    except:
        w = {}

    geo = geolocalizar_ip(ip)

    try:
        r = requests.get(url, timeout=5)
        status_code = r.status_code
        headers = r.headers
    except:
        status_code = "Offline ou inacessível"
        headers = {}

    # Criar link para ASN se disponível
    as_info = geo.get("as", "Desconhecido")
    asn_link = "Desconhecido"
    if isinstance(as_info, str) and as_info.startswith("AS"):
        as_number = as_info.split()[0].replace("AS", "")
        asn_link = f"https://bgp.he.net/AS{as_number}"

    # Exibir resultados em tabela
    tabela = PrettyTable()
    tabela.field_names = [Fore.LIGHTYELLOW_EX + Style.BRIGHT + "🔎 Informação", "📄 Resultado"]    
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Status HTTP", status_code])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Registrador", str(w.get("registrar", "Desconhecido"))]) 
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Domínio", dominio])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Endereço IP", ip])   
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"País do IP", geo.get("país", "Desconhecido")])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Região", geo.get("região", "Desconhecida")])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Cidade", geo.get("cidade", "Desconhecida")])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Provedor (ISP)", geo.get("isp", "Desconhecido")])    
    tabela.add_row([Fore.LIGHTYELLOW_EX + Style.BRIGHT +"ASN Info", as_info])
    tabela.add_row([Fore.LIGHTYELLOW_EX + Style.BRIGHT +"Link ASN (BGPView)", asn_link])
    tabela.add_row([Fore.LIGHTCYAN_EX + Style.BRIGHT +"Criado em", formatar_data(w.get("creation_date", None))])
    tabela.add_row([Fore.LIGHTCYAN_EX + Style.BRIGHT +"Expira em", formatar_data(w.get("expiration_date", None))])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Latitude", geo.get("lat", "Desconhecida")])
    tabela.add_row([Fore.LIGHTGREEN_EX + Style.BRIGHT +"Longitude", geo.get("lon", "Desconhecida")])

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n📊 Resultado 📊\n")
    print(tabela)

    # Mostrar localização no Google Maps
    lat = geo.get("lat", None)
    lon = geo.get("lon", None)
    if lat and lon and isinstance(lat, (float, int)) and isinstance(lon, (float, int)):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n🌍 Geolocalização: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{lat},{lon}")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n📌 Google Maps: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"https://www.google.com/maps/place/{lat},{lon}")

    # Mostrar cabeçalhos HTTP
    if headers:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n📬 Cabeçalhos HTTP 📬\n")
        for key, value in headers.items():
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{key}: {value}")

# Entrada do usuário
site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "🌐 Digite o nome do site (ex: google.com): ")
obter_info_site(site)

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
