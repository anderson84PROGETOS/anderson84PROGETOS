from scapy.all import sniff, TCP, wrpcap, IP
import socket

# Interface de rede para captura (por exemplo, 'eth0', 'wlan0')
interface = 'eth0'

# Arquivo de captura
pcap_file = 'capture.pcapng'

# Arquivo de log de texto
log_file = 'https.txt'

# Lista para armazenar pacotes
packets = []

# Função para resolver o nome do site a partir do IP
def resolve_hostname(ip):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except socket.herror:
        return "Hostname not found"

# Função para processar cada pacote capturado
def process_packet(packet):
    try:
        # Verifica se o pacote tem camada IP e TCP, e está na porta 443
        if IP in packet and TCP in packet and packet[TCP].dport == 443:
            ip_src = packet[IP].src
            ip_dst = packet[IP].dst
            hostname_src = resolve_hostname(ip_src)
            hostname_dst = resolve_hostname(ip_dst)
            
            log_entry = (f"Pacote capturado: {packet.summary()}\n"
                         f"IP de origem: {ip_src} (Hostname: {hostname_src})\n"
                         f"IP de destino: {ip_dst} (Hostname: {hostname_dst})\n")
            print(log_entry.strip())
            with open(log_file, 'a') as log_file_obj:
                log_file_obj.write(log_entry)
            packets.append(packet)
    except AttributeError:
        pass

print(f"\nIniciando captura na interface {interface} com filtro para porta 443\n")

# Inicia a captura de pacotes na interface especificada com filtro para porta 443
sniff(iface=interface, prn=process_packet, filter='tcp port 443', store=0)

# Salva os pacotes capturados em um arquivo .pcapng
wrpcap(pcap_file, packets)

print(f"\nCaptura salva em '{pcap_file}' e logs em '{log_file}'")
