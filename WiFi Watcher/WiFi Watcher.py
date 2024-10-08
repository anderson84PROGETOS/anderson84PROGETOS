import time
from mac_vendor_lookup import MacLookup
from pywifi import PyWiFi, const

print("""

██╗    ██╗██╗███████╗██╗    ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ██║ █╗ ██║███████║   ██║   ██║     ███████║█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝     ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                                                                                                         
""")
print("\nExemplo: Copiar e colar no website o BSSID Endereço MAC: f0:25:8e:cb:5f:14")
print("\nSe não aparecer o nome do Fabricante, acesse o website: https://macvendors.com\n\n")
print("\n\n")
print("SSID                       BSSID Endereço MAC        WPS             Fabricante                                 Sinal      dBm         Segurança WPS\n====================================================================================================================================================")

def scan_wifi():
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Interface Wi-Fi

    iface.scan()  # Inicia a varredura
    time.sleep(5)  # Aguarda a conclusão da varredura

    scan_results = iface.scan_results()
    return scan_results

def print_networks(networks, mac_lookup):
    seen_ssids = set()  # Conjunto para armazenar SSIDs já vistos
    count = 0  # Contador de redes Wi-Fi
    for network in networks:
        ssid = network.ssid.strip()
        if ssid == "":
            ssid = "<Rede Oculta>"  # Se o SSID estiver vazio, marca como rede oculta
        
        bssid = network.bssid.rstrip(":")  # Remove ':' do final, se houver
        if (ssid, bssid) not in seen_ssids:  # Verifica se o SSID + BSSID já foram processados
            seen_ssids.add((ssid, bssid))  # Adiciona o SSID + BSSID ao conjunto
            
            # Identificar o tipo de segurança
            if const.AKM_TYPE_WPA2PSK in network.akm:
                security = "WPA2"
            elif const.AKM_TYPE_WPA in network.akm:
                security = "WPA"
            else:
                security = "Aberto"  # Considera redes abertas como padrão
            
            # Identificar se WPS está ativo
            wps = 'WPS: ativo' if const.AKM_TYPE_WPA2PSK in network.akm else 'WPS: não ativo'
            
            # Obter o nome do fabricante do BSSID
            try:
                vendor_name = mac_lookup.lookup(bssid)
            except KeyError:
                vendor_name = "Desconhecido"
            
            signal_strength = network.signal  # Obtém a força do sinal em dBm

            # Classifica a força do sinal
            if signal_strength >= -50:
                signal_quality = "Forte"
            elif -70 <= signal_strength < -50:
                signal_quality = "Médio"
            else:
                signal_quality = "Fraco"
            
            # Exibe os detalhes da rede
            print(f"\nSSID: {ssid:<20} MAC: {bssid:<20} {wps:<15} Fabri: {vendor_name:<35} Sinal: {signal_strength} dBm ({signal_quality}) Segury: {security}")
            count += 1  # Incrementa o contador de redes Wi-Fi
    return count

def main(mac_lookup):    
    networks = scan_wifi()    
    count = print_networks(networks, mac_lookup)
    print(f"\n\nTotal de redes Wi-Fi Encontradas: {count}\n")

if __name__ == "__main__":
    # Inicializando a instância do MacLookup
    mac_lookup = MacLookup()
    mac_lookup.update_vendors()  # Atualizando a base de dados de fabricantes
    main(mac_lookup)

input("\nPRESSIONE ENTER PARA SAIR\n=========================\n")
