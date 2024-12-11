import socket
import dns.resolver
import requests

print("""

 ██████╗ ███████╗ ██████╗     ███╗   ███╗██╗  ██╗    ██╗██████╗ 
██╔════╝ ██╔════╝██╔═══██╗    ████╗ ████║╚██╗██╔╝    ██║██╔══██╗
██║  ███╗█████╗  ██║   ██║    ██╔████╔██║ ╚███╔╝     ██║██████╔╝
██║   ██║██╔══╝  ██║   ██║    ██║╚██╔╝██║ ██╔██╗     ██║██╔═══╝ 
╚██████╔╝███████╗╚██████╔╝    ██║ ╚═╝ ██║██╔╝ ██╗    ██║██║     
 ╚═════╝ ╚══════╝ ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝    ╚═╝╚═╝     
                                                              
""")

def get_mx_records_with_ip(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = []
        for rdata in answers:
            exchange = rdata.exchange.to_text()
            try:
                ip = socket.gethostbyname(exchange.strip('.'))
            except Exception as e:
                ip = f"Erro ao resolver IP: {e}"
            mx_records.append((exchange, ip))
        return mx_records
    except Exception as e:
        return f"Erro ao buscar registros MX: {e}"

def get_ip(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        return f"Erro ao resolver o IP: {e}"

def get_geolocation(ip):
    try:
        ip_response = requests.get(f"https://ipinfo.io/{ip}/json")
        ip_data = ip_response.json()

        hostname = ip_data.get("hostname", "Hostname não encontrado")
        org = ip_data.get("org", "Organização não encontrada")
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

        return hostname, org, city, country, region, latitude, longitude, google_maps_url, street_view_url
    except Exception as e:
        return "Erro ao buscar localização", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro"

def main():
    domain = input("\nDigite o nome ou a URL do website: ").strip()

    # Remove http/https caso esteja na entrada
    domain = domain.replace("http://", "").replace("https://", "").split('/')[0]

    print(f"\n\nConsultando informações para: {domain}\n")

    # Obter registros MX com IP
    mx_records = get_mx_records_with_ip(domain)
    if isinstance(mx_records, list):
        print("\nRegistros MX\n")
        for exchange, ip in mx_records:
            if "Erro" not in ip:
                hostname, org, city, country, region, latitude, longitude, google_maps_url, street_view_url = get_geolocation(ip)
                print(f"Servidor MX: {exchange:<35} IP: {ip:<15}\n\nHostname: {hostname}\nOrganização: {org}\nCidade: {city}\nPaís: {country}\nRegião: {region}\n\nGeolocalização: {latitude},{longitude}\n\nGoogle Maps: {google_maps_url}\nGoogle Street View: {street_view_url}")
                print("================================================================================================================================\n\n")
            else:
                print(f"Servidor MX: {exchange:<35} IP: {ip}")
    else:
        print(mx_records)

    # Obter endereço IP e informações geográficas
    ip = get_ip(domain)
    if "Erro" not in ip:
        hostname, org, city, country, region, latitude, longitude, google_maps_url, street_view_url = get_geolocation(ip)
        print(f"\n\nEndereço IP do domínio principal: {ip:<15}\n\nHostname: {hostname}\nOrganização: {org}\nCidade: {city}\nPaís: {country}\nRegião: {region}\n\nGeolocalização: {latitude},{longitude}\n\nGoogle Maps: {google_maps_url}\nGoogle Street View: {street_view_url}\n")
    else:
        print(f"Erro ao obter o IP principal: {ip}")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================")
