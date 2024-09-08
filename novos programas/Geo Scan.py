import http.cookiejar
import urllib.request
import socket
import json
import webbrowser
import dns.resolver
import pycountry

print("""

 ██████╗ ███████╗ ██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝ ██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██║  ███╗█████╗  ██║   ██║    ███████╗██║     ███████║██╔██╗ ██║
██║   ██║██╔══╝  ██║   ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╔╝███████╗╚██████╔╝    ███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                                                                        
""")

# Função para obter o nome completo do país a partir do código
def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return country.name
        else:
            return country_code
    except Exception as e:
        return f"Erro ao obter o nome do país: {e}"

# Função para obter geolocalização e organização
def getGeoLocation(ip):
    try:
        url = f"http://ipinfo.io/{ip}/json"
        response = urllib.request.urlopen(url)
        data = json.load(response)
        
        if 'error' in data:
            return "Não foi possível obter a geolocalização.", None, None, None, None
        
        country_name = get_country_name(data.get('country', ''))
        location = f"{country_name}: {data.get('region', 'N/A')}         Geo: {data.get('loc', 'N/A')}"
        org = data.get('org', 'N/A')
        
        # Obtém latitude e longitude
        loc = data.get('loc', 'N/A').split(',')
        lat = loc[0] if len(loc) > 0 else None
        lon = loc[1] if len(loc) > 1 else None
        
        return location, data.get('city', 'N/A'), lat, lon, org
    except Exception as e:
        return f"Erro ao obter geolocalização: {e}", None, None, None, None

# Função para consultar registros MX e obter o IP associado (via consulta A)
def getMXRecords(domain):
    try:
        print(f"Consultando registros MX para: {domain}\n")
        mx_records = dns.resolver.resolve(domain, 'MX')
        
        # Itera pelos registros MX encontrados
        for mx in mx_records:
            mx_target = str(mx.exchange).rstrip('.')  # Remove ponto final dos registros MX
            print(f"MX: {mx_target}")  # Removido o número de prioridade
            
            # Consulta o tipo A para o registro MX
            try:
                answer_any = dns.resolver.resolve(mx_target, 'A')
                for ip in answer_any:
                    print(f"Associado ao MX: {mx_target}     IP: {ip}\n")
            except dns.resolver.NoAnswer:
                print(f"Não foi encontrado IP associado ao MX {mx_target}")
                
    except Exception as e:
        print(f"Erro ao consultar registros MX: {e}")

# Função principal que obtém cookies, geolocalização e registros MX
def obtainCookiesAndGeo():
    url = input("\nDigite a URL do website ou nome do site (ex: wikipedia.org (ex: https://www.wikipedia.org): ")
    print("\n")
    
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url  # Usa HTTPS por padrão
    
    # Obtém o IP do site
    try:
        domain = url.replace('https://', '').replace('http://', '')
        ip_address = socket.gethostbyname(domain)
        
        # Obtém a geolocalização do IP
        location_info, city, lat, lon, org = getGeoLocation(ip_address)
        
        print(f"IP do website: {ip_address}\n")
        print(f"Organização: {org}\n\n")  # Impressão da organização movida para depois de obter a geolocalização
        
        # Obtém os registros MX e seus IPs associados
        getMXRecords(domain)
        print("")
        
    except Exception as e:
        print(f"Erro ao obter o IP do website: {e}")
        return
    
    print(f"Localização Geográfica: {location_info}\n")
    
    if lat and lon:
        print(f"City: {city} \n\nLatitude: {lat} \nLongitude: {lon}")
        
        map_url = f"https://www.google.com/maps?q={lat},{lon}"
        print(f"\nURL do Google Maps: {map_url}")
        
        open_map = input("\n\nDeseja abrir o Google Maps com essas coordenadas? (s/n): ").strip().lower()
        
        if open_map == 's':
            print(f"\nAbrindo o Google Maps: {map_url}")
            webbrowser.open(map_url)
        else:
            print("\nGoogle Maps não foi aberto.\n")
    
    # Cria o objeto CookieJar para armazenar os cookies
    cookie_jar = http.cookiejar.CookieJar()    
    
    # Configura os cabeçalhos que serão enviados na requisição
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    req = urllib.request.Request(url, headers=headers)
    url_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    try:
        response = url_opener.open(req)
        # Exibe os cabeçalhos HTTP da resposta
        print("\nCabeçalhos HTTP da resposta\n===========================")
        for header, value in response.headers.items():
            print(f"{header}: {value}")
        
        print("\n\nInformação\n==========\n")
        for cookie in cookie_jar:
            print(cookie.name, cookie.value)
            
    except Exception as e:
        print(f"Ocorreu um erro ao acessar a URL: {e}")

# Executa a função
obtainCookiesAndGeo()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
