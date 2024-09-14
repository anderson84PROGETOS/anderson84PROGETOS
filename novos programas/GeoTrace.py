import requests

print("""

 ██████╗ ███████╗ ██████╗ ████████╗██████╗  █████╗  ██████╗███████╗
██╔════╝ ██╔════╝██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██║  ███╗█████╗  ██║   ██║   ██║   ██████╔╝███████║██║     █████╗  
██║   ██║██╔══╝  ██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
╚██████╔╝███████╗╚██████╔╝   ██║   ██║  ██║██║  ██║╚██████╗███████╗
 ╚═════╝ ╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
                                                                 
""")

def obter_informacoes_geonet(website):
    url = f"https://geonet.shodan.io/api/geoping/{website}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        resposta = requests.get(url, headers=headers)
        resposta.raise_for_status()  # Lança uma exceção se a resposta HTTP for um erro
        dados = resposta.json()  # Converte a resposta JSON em um dicionário Python
        return dados
    except requests.exceptions.RequestException as e:
        print(f"\nErro ao fazer a solicitação: {e}")
        return None

def formatar_informacoes(dados):
    if isinstance(dados, list) and len(dados) > 0:
        informacoes_formatadas = ""
        for info in dados:
            latlon = info.get('from_loc', {}).get('latlon', 'N/A')
            latitude, longitude = latlon.split(',') if latlon != 'N/A' else ('N/A', 'N/A')
            maps_url = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude != 'N/A' and longitude != 'N/A' else 'N/A'
            formatted_info = (
                f"IP: {info.get('ip', 'N/A')}\n\n"
                f"Está Vivo: {'Sim' if info.get('is_alive', False) else 'Não'}\n"
                f"RTT Mínimo: {info.get('min_rtt', 'N/A')} ms\n"
                f"RTT Médio: {info.get('avg_rtt', 'N/A')} ms\n"
                f"RTT Máximo: {info.get('max_rtt', 'N/A')} ms\n"
                f"Pacotes Enviados: {info.get('packets_sent', 'N/A')}\n"
                f"Pacotes Recebidos: {info.get('packets_received', 'N/A')}\n"
                f"Perda de Pacotes: {info.get('packet_loss', 'N/A') * 100}%\n"
                f"\nCidade: {info.get('from_loc', {}).get('city', 'N/A')}\n"
                f"País: {info.get('from_loc', {}).get('country', 'N/A')}\n"
                f"Latitude: {latitude}\n"
                f"Longitude: {longitude}\n"
                f"\nURL do Google Maps: {maps_url}\n"
                f"\n==================================\n"
            )
            informacoes_formatadas += formatted_info
        return informacoes_formatadas
    return "\nNenhuma informação disponível."

def main():
    website = input("\nDigite o nome do website: ")
    dados = obter_informacoes_geonet(website)
    informacoes_formatadas = formatar_informacoes(dados)
    print("\n\nInformações Website\n")
    print(informacoes_formatadas)

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
