from scapy.all import ARP, Ether, srp
from mac_vendor_lookup import MacLookup

print("""
    
     █████╗ ██████╗ ██████╗     ██████╗  █████╗ ███╗   ██╗ ██████╗ ███████╗██████╗ 
    ██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██╔════╝██╔══██╗
    ███████║██████╔╝██████╔╝    ██████╔╝███████║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝
    ██╔══██║██╔══██╗██╔═══╝     ██╔══██╗██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
    ██║  ██║██║  ██║██║         ██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████╗██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝         ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                   
""")

def extract_info_from_arp(packets):
    results = []
    for packet in packets:
        if packet.haslayer(ARP) and packet[ARP].op == 2:  # ARP Reply
            ip = packet[ARP].psrc
            mac = packet[ARP].hwsrc
            try:
                vendor = MacLookup().lookup(mac)
            except:
                vendor = "Desconhecido"
            results.append([ip, mac, vendor])
    return results

def display_results(results):
    if results:
        print('\nResultados Encontrados\n======================\n')
        print('Endereço IP\t\tEndereço MAC\t\t\tFabricante\n==================================================================')
        for result in results:
            print(f'{result[0]}\t\t{result[1]}\t\t{result[2]}')
    else:
        print('Nenhum resultado encontrado.')

def save_to_txt(results, output_file):
    with open(output_file, 'w') as file:
        file.write('Endereço IP\t\tEndereço MAC\t\t\tFabricante\n==================================================================\n')
        for result in results:
            file.write(f'{result[0]}\t\t{result[1]}\t\t{result[2]}\n')

def scan_network(target_network):
    arp = ARP(pdst=target_network)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp

    result = srp(packet, timeout=3, verbose=False)[0]
    return [response[1] for response in result]

target_network = input("Digite o intervalo de IP para Escanear (ex: 192.168.0.1/24): ")

print("\n\nEscaneando com ARP\n")

packets = scan_network(target_network)
results = extract_info_from_arp(packets)

display_results(results)

save_option = input('\n\n\nDeseja salvar os resultados? (s/n): ').strip().lower()
if save_option == 's':
    output_file = input('\nDigite o nome do arquivo para salvar (ex: arquivo.txt): ')
    if results:
        save_to_txt(results, output_file)
        print(f'\nInformações salvas em: {output_file}')
    else:
        print('\nNão há informações para salvar.')
else:
    print('\nOs resultados não foram salvos.')

print("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
try:
    input()
except Exception as e:
    print(f"Ocorreu um erro: {e}")
