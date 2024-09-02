import subprocess
import re
import requests
from bs4 import BeautifulSoup

print("""
██╗    ██╗██╗  ██╗ █████╗ ████████╗██╗    ██╗███████╗██████╗     
██║    ██║██║  ██║██╔══██╗╚══██╔══╝██║    ██║██╔════╝██╔══██╗    
██║ █╗ ██║███████║███████║   ██║   ██║ █╗ ██║█████╗  ██████╔╝    
██║███╗██║██╔══██║██╔══██║   ██║   ██║███╗██║██╔══╝  ██╔══██╗    
╚███╔███╔╝██║  ██║██║  ██║   ██║   ╚███╔███╔╝███████╗██████╔╝    
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚══════╝╚═════╝     
                                                                
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

    return list(set(ipv4_addresses))

def obter_informacoes_website(endereco):
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers={'User-Agent': 'Mozilla/5.0'})
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':                
                print(f"\nCompany ISP  : {dados['isp']}")
                print(f"Country      : {dados.get('country', 'N/A')} ({dados.get('countryCode', 'N/A')})\n"
                      f"Region       : {dados.get('region', 'N/A')} - {dados.get('regionName', 'N/A')}\n"
                      f"City         : {dados.get('city', 'N/A')}\n"
                      f"ZIP Code     : {dados.get('zip', 'N/A')}\n\n"
                      f"Latitude     : {dados.get('lat', 'N/A')}\n"
                      f"Longitude    : {dados.get('lon', 'N/A')}\n\n"
                      f"Timezone     : {dados.get('timezone', 'N/A')}\n"
                      f"Organization : {dados.get('org', 'N/A')}\n"
                      f"AS           : {dados.get('as', 'N/A')}\n")
                
                lat, lon = dados.get('lat'), dados.get('lon')
                if lat and lon:
                    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36'}
                    endereco_completo = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
                    if endereco_completo.status_code == 200:
                        endereco_completo = endereco_completo.json()
                        print(f"Nome da Rua  : {endereco_completo['display_name']}\n")                        
                        google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                        print(f"Google Maps  : {google_maps_url}\n")
                    else:
                        print(f"\nErro ao obter informações do Nominatim: {endereco_completo.status_code}\n")

                ipv4_addresses = get_ipv4_addresses(endereco)
                if ipv4_addresses:
                    for ipv4_address in ipv4_addresses:
                        print(f"Website IP   : {ipv4_address}")
                else:
                    print("Nenhum Endereço IPv4 encontrado.")

            else:
                print(f"Erro ao obter informações do site: {dados['message']}")
        else:
            print(f"Erro ao consultar serviço para informações do site: Código {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao obter informações do site: {str(e)}")

def capturar_pacotes(url):
    try:
        response = requests.head(url)
        headers = response.headers
        print(f"\n\n\nCabeçalhos HTTP para: {url}\n")
        for header, value in headers.items():
            print(f"{header}: {value}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar extrair cabeçalhos HTTP da URL: {e}")

def obter_informacoes_do_site(alvo):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        response = requests.get(alvo, headers=headers)
        if response.status_code == 200:
            print(f"\n\n\nRelatório WhatWeb para: {response.url}\n")
            print(f"Status       : {response.status_code} {response.reason}")

            soup = BeautifulSoup(response.text, 'html.parser')
            titulo = soup.title.string if soup.title else "Nenhum título encontrado"
            print(f"Título       : {titulo}")

            exibir_ipv4(alvo)

            capturar_pacotes(alvo)

        else:
            print(f"Falha ao obter informações de {alvo}. Código de status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Ocorreu um erro: {e}")

def exibir_ipv4(site):
    if site.startswith(('http://', 'https://')):
        site = site.split('//')[1]

    obter_informacoes_website(site)

if __name__ == "__main__":
    alvo = input("\nDigite a URL do website: ").strip()
    obter_informacoes_do_site(alvo)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
