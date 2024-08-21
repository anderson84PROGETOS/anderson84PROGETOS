from pywifi import PyWiFi, const
import time
import requests
from tqdm import tqdm

print("""

██╗    ██╗██╗███████╗██╗     █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ███████║██╔██╗ ██║███████║██║      ╚████╔╝   ███╔╝ █████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ██║  ██║██║ ╚████║██║  ██║███████╗   ██║   ███████╗███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝
                                                                                              
""")

def get_vendor_name(mac_address):
    try:
        url = f"https://api.macvendors.com/{mac_address}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Desconhecido"
    except requests.RequestException:
        return "Erro ao buscar fabricante"

def scan_wifi():
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Interface Wi-Fi

    iface.scan()  # Inicia a varredura

    # Cria a barra de progresso com menos iterações e largura definida
    num_iterations = 100  # Número menor de iterações
    with tqdm(total=num_iterations, desc="Procurando redes Wi-Fi", unit="iteração", ncols=100) as pbar:
        for _ in range(num_iterations):
            time.sleep(0.1)  # Ajuste o tempo conforme necessário para a progressão
            pbar.update(1)  # Atualiza a barra de progresso

    scan_results = iface.scan_results()
    return scan_results

def print_networks(networks):
    seen_ssids = set()  # Conjunto para armazenar SSIDs já vistos
    count = 0  # Contador de redes Wi-Fi
    for network in networks:
        ssid = network.ssid.strip()
        if ssid == "":
            ssid = "<Rede Oculta>"  # Se o SSID estiver vazio, marca como rede oculta
        
        bssid = network.bssid.rstrip(":")  # Remove ':' do final, se houver
        if (ssid, bssid) not in seen_ssids:  # Verifica se o SSID + BSSID já foram processados
            seen_ssids.add((ssid, bssid))  # Adiciona o SSID + BSSID ao conjunto
            wps = 'WPS ativo' if network.akm[0] == const.AKM_TYPE_WPA2PSK else 'WPS não ativo'
            vendor_name = get_vendor_name(bssid)
            print(f"\nSSID: {ssid:<25} BSSID: {bssid:<25} {wps:<15} Fabricante: {vendor_name}")
            count += 1  # Incrementa o contador de redes Wi-Fi
    return count

def main():
    print("\nExemplo: Copiar e colar no website o  BSSID: f0:25:8e:cb:5f:14")
    print("\nSe não aparecer o nome do Fabricante, acesse o website: https://macvendors.com\n\n")
    networks = scan_wifi()
    print("\n")
    count = print_networks(networks)
    print(f"\n\n\nTotal de redes Wi-Fi Encontradas: {count}\n")

if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
