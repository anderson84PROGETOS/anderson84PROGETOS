import requests
from ipwhois import IPWhois
from colorama import Fore, Style, init
import re  # Importando o módulo para utilizar expressões regulares

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nMais Informações acesse o site: https://www.maxmind.com/en/geoip-demo\n")
print(Fore.LIGHTRED_EX + Style.BRIGHT + "Mais Informações acesse o site: https://bgp.he.net/")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗███╗   ██╗███████╗ ██████╗     ███████╗███████╗████████╗ ██████╗██╗  ██╗███████╗██████╗ 
██║████╗  ██║██╔════╝██╔═══██╗    ██╔════╝██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔════╝██╔══██╗
██║██╔██╗ ██║█████╗  ██║   ██║    █████╗  █████╗     ██║   ██║     ███████║█████╗  ██████╔╝
██║██║╚██╗██║██╔══╝  ██║   ██║    ██╔══╝  ██╔══╝     ██║   ██║     ██╔══██║██╔══╝  ██╔══██╗
██║██║ ╚████║██║     ╚██████╔╝    ██║     ███████╗   ██║   ╚██████╗██║  ██║███████╗██║  ██║
╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝     ╚═╝     ╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                                                                              
""")

# Função para validar se o endereço é IPv4
def is_ipv4(ip):
    # Expressão regular para validar IPv4
    pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    return re.match(pattern, ip) is not None

def obter_informacoes_ip(domain_or_ip):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # URL da API para consulta
    url = f'http://ip-api.com/json/{domain_or_ip}'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dados = response.json()
            if dados.get("status") == "success":
                # Verificando se o IP é IPv4 antes de processar
                ip = dados.get("query", "N/A")
                if not is_ipv4(ip):
                    return f"O endereço IP {ip} não é um IPv4 válido."

                rede_cidr = "Não disponível"
                try:
                    obj = IPWhois(ip)
                    whois_info = obj.lookup_whois()
                    cidr = whois_info.get('asn_cidr', 'Não disponível')
                    if cidr != ip:
                        rede_cidr = cidr
                except Exception as e:
                    rede_cidr = "Erro ao buscar rede CIDR"

                latitude = dados.get('lat', 'N/A')
                longitude = dados.get('lon', 'N/A')
                google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
                timezone = dados.get('timezone', 'N/A')  # Adicionando a informação de timezone
                
                # Remover a chave "Rede" antes de retornar as informações
                informacoes = {
                    f"{Fore.LIGHTMAGENTA_EX + Style.BRIGHT}Endereço IP": ip,
                    f"{Fore.LIGHTRED_EX + Style.BRIGHT}\nRede": rede_cidr,
                    f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}\n\nTimezone": timezone,  # Exibindo timezone
                    f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}País": dados.get("country", "N/A"),
                    f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Região": dados.get("regionName", "N/A"),
                    f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Cidade": dados.get("city", "N/A"),
                    f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Código postal": dados.get("zip", "N/A"),
                    f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}ISP": dados.get("isp", "N/A"),
                    f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Organização": dados.get("org", "N/A"),
                    f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Tipo de conexão": dados.get("as", "N/A"),
                    f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}\n\nLatitude/Longitude": f"{latitude}, {longitude}",
                    f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}\nURL do Google Maps": google_maps_url,
                    f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}\nURL do Google Street View": street_view_url,
                }

                return informacoes
            else:
                return f"Erro na consulta: {dados.get('message', 'Motivo desconhecido')}"
        else:
            return f"Erro HTTP: {response.status_code} - {response.reason}"
    except Exception as e:
        return f"Erro ao processar a solicitação: {e}"

# Entrada do usuário
ip_ou_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite um endereço IP ou nome do website: ")

# Obter informações
informacoes = obter_informacoes_ip(ip_ou_url)

# Exibir informações
if isinstance(informacoes, dict):
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nInformações Obtidas\n")
    for chave, valor in informacoes.items():
        print(f"{chave}: {valor}")
else:
    print(informacoes)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
