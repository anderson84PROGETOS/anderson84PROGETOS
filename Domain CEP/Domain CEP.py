import socket
import requests
import webbrowser  # Para abrir o link no navegador

print("""

██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗███████╗██████╗ 
██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██╔════╝██╔══██╗
██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║    ██║     █████╗  ██████╔╝
██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██╔══╝  ██╔═══╝ 
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗███████╗██║     
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝╚══════╝╚═╝     
                                                                           
""")

# Cabeçalhos personalizados para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para resolver o IP do domínio/URL
def get_ip_from_domain(domain):
    try:
        # Obtém o endereço IP do domínio
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        print(f"Erro ao tentar resolver o domínio: {e}")
        return None

# Função para obter geolocalização pelo IP
def get_geo_info_by_ip(ip):
    try:
        # Faz a requisição para a API gratuita do ipinfo.io para obter a geolocalização
        response = requests.get(f"https://ipinfo.io/{ip}/json", headers=headers)
        response.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx/5xx
        data = response.json()
        
        # Verifica se houve sucesso na resposta
        if 'error' in data:
            print(f"Erro: {data['error']['message']}")
            return None
        return data
    except requests.RequestException as e:
        print(f"Erro ao tentar obter a geolocalização: {e}")
        return None

# Função para obter informações sobre um CEP
def get_address_by_cep(cep):
    try:
        # Faz a requisição para a API do ViaCEP para obter informações do CEP
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", headers=headers)
        response.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx/5xx
        data = response.json()
        
        # Verifica se houve sucesso na resposta
        if 'erro' in data:
            print("Erro: CEP não encontrado.")
            return None
        return data
    except requests.RequestException as e:
        print(f"Erro ao tentar obter o endereço pelo CEP: {e}")
        return None

# Função para obter a região do estado usando o código do estado (UF)
def get_region_by_uf(uf):
    try:
        # Faz a requisição para a API do IBGE para obter informações sobre a região do estado
        regiao_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}"
        response = requests.get(regiao_url, headers=headers)
        response.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx/5xx
        regiao_data = response.json()
        return regiao_data.get('regiao', {}).get('nome', 'Não disponível')
    except requests.RequestException as e:
        print(f"Erro ao tentar obter a região do estado: {e}")
        return None

# Função para obter coordenadas (latitude e longitude) a partir do endereço
def get_coordinates_from_address(address):
    try:
        # Adiciona um cabeçalho 'User-Agent' com informações de contato
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 (your.email@example.com)'
        }
        response = requests.get(f"https://nominatim.openstreetmap.org/search?format=json&q={address}&limit=1", headers=headers)
        response.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx/5xx
        data = response.json()
        
        # Verifica se houve sucesso na resposta
        if not data:
            print("Erro: Não foi possível obter coordenadas.")
            return None
        location = data[0]
        latitude = location.get('lat')
        longitude = location.get('lon')
        if latitude and longitude:
            return latitude, longitude
        else:
            print("Erro: Coordenadas não encontradas na resposta.")
            return None
    except requests.RequestException as e:
        print(f"Erro ao tentar obter as coordenadas: {e}")
        return None

def main():
    # Pergunta ao usuário se deseja buscar informações pelo domínio ou CEP
    escolha = input("\nDeseja Buscar informações Pelo Dominio (d) ou CEP (c): ").strip().lower()
    
    if escolha == 'd':
        url = input("\nDigite o nome do website: ")
        
        # Obtém o domínio sem protocolo (http/https)
        domain = url.split("//")[-1].split("/")[0]
        
        # Obtém o endereço IP do domínio
        ip = get_ip_from_domain(domain)
        
        if ip:
            print(f"\nEndereço IP para o domínio {domain}: {ip}")
            # Obtém as informações de geolocalização para o IP
            geo_info = get_geo_info_by_ip(ip)
            
            if geo_info:
                print(f"\n\nInformações de geolocalização para o IP: {ip}")
                print(" ")
                cidade = geo_info.get('city')
                regiao = geo_info.get('region')
                pais = geo_info.get('country')
                localizacao = geo_info.get('loc')  # Retorna como 'latitude,longitude'
                
                print(f"Cidade: {cidade}")
                print(f"Região: {regiao}")
                print(f"País: {pais}")
                print(f"Localização (latitude, longitude): {localizacao}")

                # Exibe o link do Google Maps com as coordenadas
                latitude, longitude = localizacao.split(',')
                google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}&hl=pt"
                print(f"\nVeja a localização no Google Maps: {google_maps_url}")
                
                # Exibe o link do Google Maps no modo "Street View"
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
                print(f"\nVeja a localização no Google Maps (Street View): {street_view_url}")

                # Pergunta ao usuário se deseja abrir o Google Maps
                abrir_mapa = input("\n\nDeseja abrir a localização no Google Maps (s/n): ").strip().lower()
                
                if abrir_mapa == 's':
                    # Abre o Google Maps diretamente no navegador                    
                    webbrowser.open(street_view_url)
                else:
                    print("\nO Google Maps não será aberto.")
            else:
                print("\nNão foi possível obter as informações de geolocalização.")
        else:
            print("\nNão foi possível resolver o domínio para um IP.")
    
    elif escolha == 'c':
        cep = input("\nDigite o CEP: ").strip()
        
        # Obtém as informações sobre o CEP
        address_info = get_address_by_cep(cep)
        
        if address_info:
            print(f"\nInformações para o CEP: {cep}")
            logradouro = address_info.get('logradouro')
            bairro = address_info.get('bairro')
            cidade = address_info.get('localidade')
            estado = address_info.get('uf')
            complemento = address_info.get('complemento', 'Não disponível')
            endereco_completo = f"{logradouro}, {bairro}, {cidade} - {estado}"
            
            print(f"Logradouro: {logradouro}")
            print(f"Bairro: {bairro}")
            print(f"Cidade: {cidade}")
            print(f"Estado: {estado}")
            print(f"Complemento: {complemento}")

            # Obtém a região do estado
            regiao = get_region_by_uf(estado)
            if regiao:
                print(f"Região: {regiao}")

            # Obtém as coordenadas a partir do endereço
            coordinates = get_coordinates_from_address(endereco_completo)
            
            if coordinates:
                latitude, longitude = coordinates
                print(f"\nLocalização (latitude, longitude): {latitude}, {longitude}")

                # Exibe o link do Google Maps com as coordenadas
                google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}&hl=pt"
                print(f"\nVeja a localização no Google Maps: {google_maps_url}")

                # Exibe o link do Google Maps no modo "Street View"
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"
                print(f"\nVeja a localização no Google Maps (Street View): {street_view_url}")

                # Pergunta ao usuário se deseja abrir o Google Maps
                abrir_mapa = input("\n\nDeseja abrir a localização no Google Maps (s/n): ").strip().lower()
                
                if abrir_mapa == 's':
                    # Abre o Street View diretamente no navegador
                    webbrowser.open(street_view_url)
                else:
                    print("\nO Google Maps não será aberto.")
            else:
                print("\nNão foi possível obter as coordenadas para o endereço.")
        else:
            print("\nNão foi possível obter informações para o CEP.")
    
    else:
        print("Escolha inválida. Por favor, escolha 'd' para domínio ou 'c' para CEP.")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
