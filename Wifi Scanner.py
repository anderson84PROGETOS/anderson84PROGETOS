from pywifi import PyWiFi, const
import time
from mac_vendor_lookup import MacLookup

print("""

██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                                                       
""")
print("\n\nExemplo: Copiar e colar no website o BSSID: f0:25:8e:cb:5f:14")
print("\nSe não aparecer o nome do Fabricante, acesse o website: https://macvendors.com\n\n")
print("Procurando redes Wi-Fi\n")

def scan_ip(ip, results, mac_lookup):
    import scapy.all as scapy  # Importa scapy dentro da função para evitar problemas de importação global
    # Criando um pacote ARP
    arp_request = scapy.ARP(pdst=str(ip))
    # Criando um pacote Ethernet
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    # Combinando os pacotes ARP e Ethernet
    packet = ether / arp_request
    # Enviando o pacote e recebendo a resposta
    answered = scapy.srp(packet, timeout=0.5, verbose=0)[0]

    # Processando as respostas
    for sent, received in answered:
        # Obtenha o fabricante a partir do endereço MAC
        try:
            vendor = mac_lookup.lookup(received.hwsrc)
        except KeyError:
            vendor = "Desconhecido"

        # Adicionando o endereço IP, o endereço MAC e o fabricante aos resultados
        results.append((received.psrc, received.hwsrc, vendor))

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
            wps = 'WPS ativo' if network.akm[0] == const.AKM_TYPE_WPA2PSK else 'WPS não ativo'
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

            print(f"\nSSID: {ssid:<20} BSSID: {bssid:<20} {wps:<15} Fabricante: {vendor_name:<45} Sinal: {signal_strength} dBm ({signal_quality})")
            count += 1  # Incrementa o contador de redes Wi-Fi
    return count

def main(mac_lookup):    
   
    networks = scan_wifi()    
    count = print_networks(networks, mac_lookup)
    print(f"\n\n\nTotal de redes Wi-Fi Encontradas: {count}\n")

if __name__ == "__main__":
    # Inicializando a instância do MacLookup
    mac_lookup = MacLookup()
    mac_lookup.update_vendors()  # Atualizando a base de dados de fabricantes
    main(mac_lookup)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
