import requests
import socket
import time
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"""
██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗    ██╗███╗   ██╗███████╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝    ██║████╗  ██║██╔════╝██╔═══██╗
██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗      ██║██╔██╗ ██║█████╗  ██║   ██║
██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝      ██║██║╚██╗██║██╔══╝  ██║   ██║
╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗    ██║██║ ╚████║██║     ╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 

""")

def obter_info_ip(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            dados = response.json()
            asn = dados.get("org", "Desconhecido")
            cidade = dados.get("city", "Desconhecido")
            regiao = dados.get("region", "Desconhecido")
            pais = dados.get("country", "Desconhecido")
            provedor = dados.get("isp", asn)
            coordenadas = dados.get("loc", "Desconhecido")
            return asn, cidade, regiao, pais, provedor, coordenadas
    except requests.RequestException:
        pass
    return "Desconhecido", "Desconhecido", "Desconhecido", "Desconhecido", "Desconhecido", "Desconhecido"
         
def detectar_sistema_operacional(url):    
    if not url.startswith("http"):
        url_http = "http://" + url
        url_https = "https://" + url
    else:
        url_http = url.replace("https://", "http://")
        url_https = url.replace("http://", "https://")

    sistemas_conhecidos = {
        "windows": "Windows",
        "unix": "Unix",
        "linux": "Linux",
        "apache": "Provavelmente Linux",
        "nginx": "Provavelmente Linux",
        "freebsd": "FreeBSD",
        "openbsd": "OpenBSD",
        "netbsd": "NetBSD",
        "solaris": "Solaris",
        "aix": "AIX",
        "hp-ux": "HP-UX",
        "irix": "IRIX",
        "macos": "MacOS",
        "darwin": "MacOS"
    }

    tecnologias_conhecidas = {
        "x-powered-by": "Linguagem de Programação",
        "server": "Servidor Web",
        "set-cookie": "Cookies Ativos",
        "content-security-policy": "Política de Segurança",
        "strict-transport-security": "HSTS Ativado",
        "x-frame-options": "Proteção contra Clickjacking",
        "x-xss-protection": "Proteção contra XSS"
    }

    for site in [url_https, url_http]:
        try:
            inicio = time.time()
            response = requests.get(site, timeout=5)
            fim = time.time()
            tempo_resposta = round(fim - inicio, 3)

            # Obtendo o IP do site
            dominio = url.replace("http://", "").replace("https://", "").split('/')[0]
            ip_servidor = socket.gethostbyname(dominio)

            # Obtendo ASN, localização e provedor
            asn_info, cidade, regiao, pais, provedor, coordenadas = obter_info_ip(ip_servidor)

            # Links para Google Maps e Street View
            maps_link = Fore.LIGHTGREEN_EX + Style.BRIGHT + f"https://www.google.com/maps?q={coordenadas}"
            street_view_link = Fore.LIGHTGREEN_EX + Style.BRIGHT + f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={coordenadas}&heading=-45&pitch=38&fov=80"

            # Identificando o sistema operacional a partir do cabeçalho
            sistema = "Desconhecido"
            for chave, valor in sistemas_conhecidos.items():
                if chave in response.text.lower():
                    sistema = valor
                    break
            
            # Se não encontrou no conteúdo, verificar os cabeçalhos
            if sistema == "Desconhecido":
                for chave, valor in tecnologias_conhecidas.items():
                    if chave in response.headers:
                        if chave == "server":
                            if "Apache" in response.headers[chave]:
                                sistema = "Linux (Apache)"
                            elif "nginx" in response.headers[chave]:
                                sistema = "Linux (Nginx)"
                            break

            # Exibindo as informações do servidor
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\n========== INFORMAÇÕES DO SERVIDOR ==========")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nEndereço IP: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ip_servidor}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nASN e Provedor: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{asn_info}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nSistema Operacional: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{sistema}")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nLocalização: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{cidade}, {regiao}, {pais}")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nCoordenadas: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{coordenadas}")           
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nGoogle Maps: {maps_link}")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nGoogle Street View: {street_view_link}")
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nTempo de resposta: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{tempo_resposta} segundos")

            # Exibindo os cabeçalhos HTTP
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT +  "\n\n========== CABEÇALHOS HTTP ==========\n")
            for chave, valor in response.headers.items():
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{chave}: {valor}")
            return        
        except (requests.RequestException, socket.gaierror):
            continue

    print("Erro ao acessar o site em HTTP e HTTPS.")

# Função principal
if __name__ == "__main__":
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website: ")
    detectar_sistema_operacional(site)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
