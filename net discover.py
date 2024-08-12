import scapy.all as scapy
from ipaddress import ip_network
import threading
import requests
import sys

print("""

███╗   ██╗███████╗████████╗    ██████╗ ██╗███████╗ ██████╗ ██████╗ ██╗   ██╗███████╗██████╗ 
████╗  ██║██╔════╝╚══██╔══╝    ██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗
██╔██╗ ██║█████╗     ██║       ██║  ██║██║███████╗██║     ██║   ██║██║   ██║█████╗  ██████╔╝
██║╚██╗██║██╔══╝     ██║       ██║  ██║██║╚════██║██║     ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
██║ ╚████║███████╗   ██║       ██████╔╝██║███████║╚██████╗╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
╚═╝  ╚═══╝╚══════╝   ╚═╝       ╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
                                                                                           
""")

# Função para obter o fabricante a partir do endereço MAC usando uma API pública
def get_mac_vendor(mac):
    try:
        response = requests.get(f"https://api.macvendors.com/{mac}")
        if response.status_code == 200:
            return response.text
        else:
            return "Desconhecido"
    except Exception:
        return "Desconhecido"

def scan_ip(ip, results):
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
        vendor = get_mac_vendor(received.hwsrc)

        # Adicionando o endereço IP, o endereço MAC e o fabricante aos resultados
        results.append((received.psrc, received.hwsrc, vendor))

def scan_network(network, progress_callback):
    # Criando uma lista para armazenar os resultados do escaneamento
    results = []

    # Calculando o número total de IPs na rede para a barra de progresso
    total_ips = network.num_addresses
    progress_step = 100 / total_ips

    threads = []

    # Percorrendo todos os endereços IP na rede
    for i, ip in enumerate(network, start=1):
        # Criar e iniciar uma nova thread para escanear o IP atual
        thread = threading.Thread(target=scan_ip, args=(ip, results))
        threads.append(thread)
        thread.start()

        # Atualizando a barra de progresso
        progress_callback(i, total_ips)
    
    # Aguardar todas as threads terminarem
    for thread in threads:
        thread.join()

    return results

def main():
    # Solicitar ao usuário o endereço de rede a ser escaneado
    network_address = input("\nDigite o Endereço de rede (ex: 192.168.0.0/24): ")
    
    try:
        # Convertendo o endereço de rede em um objeto de rede
        network = ip_network(network_address, strict=False)
    except ValueError:
        print("Endereço de rede inválido!")
        return
    
    # Realizando o escaneamento de rede
    print("\n\nIniciando Escaneamento...")
    print("\n")
    
    def update_progress(current, total):
        # Atualizando a linha de progresso no terminal
        sys.stdout.write(f"\rProgresso: {current}/{total}")
        sys.stdout.flush()
        
    scan_results = scan_network(network, update_progress)

    # Imprimindo os resultados do escaneamento
    print("\n\n")
    
    # Exibindo resultados no terminal
    print(f"{'Endereço IP':<20} {'Endereço MAC':<20} {'Fabricante':<60}")
    print("-" * 52)
    for ip, mac, vendor in scan_results:
        print(f"{ip:<20} {mac:<20} {vendor:<60}")

    # Solicitar ao usuário o local e nome do arquivo para salvar os resultados
    file_path = input("\n\n\nDigite o caminho do arquivo para salvar os resultados (ex: resultados.txt): ")
    if file_path:
        with open(file_path, "w") as file:
            # Escrevendo os cabeçalhos no arquivo
            file.write("Endereço IP\tEndereço MAC\t        Fabricante\n==================================================\n")
            for ip, mac, vendor in scan_results:
                file.write(f"{ip}\t{mac}\t{vendor}\n")
        print(f"\nResultados salvos Em: {file_path}")

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
