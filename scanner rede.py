import time
from scapy.all import ARP, Ether, srp
from mac_vendor_lookup import MacLookup

print("""

███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗     ██████╗ ███████╗██████╗ ███████╗
██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██╔════╝
███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ██████╔╝█████╗  ██║  ██║█████╗  
╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██╔══██╗██╔══╝  ██║  ██║██╔══╝  
███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ██║  ██║███████╗██████╔╝███████╗
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝
                                                                                               
""")

print("\nEscaneando Rede Aguarde\n")
def scan_ip_range(ip_range, mac_lookup):
    # Criando um pacote ARP para a faixa de IP
    arp_request = ARP(pdst=ip_range)
    # Criando um pacote Ethernet
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    # Combinando os pacotes ARP e Ethernet
    packet = ether / arp_request
    # Enviando o pacote e recebendo a resposta
    answered = srp(packet, timeout=2, verbose=0)[0]

    results = []

    # Processando as respostas
    for sent, received in answered:
        # Obtenha o fabricante a partir do endereço MAC
        try:
            vendor = mac_lookup.lookup(received.hwsrc)
        except KeyError:
            vendor = "Desconhecido"

        # Adicionando o endereço IP, o endereço MAC e o fabricante aos resultados
        results.append((received.psrc, received.hwsrc, vendor))

    return results

def print_devices(devices):
    print("\n\nDispositivos Encontrados na Rede")
    print("================================\n")
    for ip, mac, vendor in devices:
        print(f"IP: {ip:<20} MAC: {mac:<20} Fabricante: {vendor:<20}")

def main(mac_lookup):
    # Exibe a mensagem assim que o script é executado
    ip_range = input("\nDigite o range de IP (Ex: 192.168.0.1/24 : ")
    
    # Escaneando a faixa de IPs
    devices = scan_ip_range(ip_range, mac_lookup)
    
    # Exibindo os dispositivos encontrados
    print_devices(devices)
    
    print(f"\n\nTotal de Dispositivos Encontrados: {len(devices)}\n")

if __name__ == "__main__":
    # Inicializando a instância do MacLookup
    mac_lookup = MacLookup()
    mac_lookup.update_vendors()  # Atualizando a base de dados de fabricantes
    
    main(mac_lookup)
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
