from scapy.all import sniff, TCP, IP, UDP, wrpcap
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog  # Para salvar arquivo
from scapy.layers.http import HTTPRequest
import threading

# Lista para armazenar os pacotes capturados
captured_packets = []
capturing = False  # Variável para controle da captura

# Função para lidar com pacotes capturados
def packet_callback(packet):
    # Armazena o pacote capturado
    captured_packets.append(packet)
    
    # Verifica se o pacote possui a camada IP
    if packet.haslayer(IP):
        # Verifica se o pacote usa HTTP (porta 80) ou HTTPS (porta 443)
        if packet.haslayer(TCP):
            if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                packet_info = f"\nHTTP: {packet[IP].src:<20} {packet[IP].dst:<20}  {packet.summary():<20}\n\n"
                packet_text.insert(END, packet_info)  # Exibe na GUI
                
                # Verifica se o pacote é uma requisição HTTP
                if packet.haslayer(HTTPRequest):
                    http_layer = packet[HTTPRequest]
                    # Extrai o método e o campo de dados, se existir
                    if http_layer.Method == b"POST":
                        # Exibir dados de formulário
                        if http_layer.fields.get("Path"):
                            packet_text.insert(END, f"Form Data: {http_layer.fields}\n")
                            
            elif packet[TCP].dport == 443 or packet[TCP].sport == 443:
                packet_info = f"\nHTTPS: {packet[IP].src:<20} {packet[IP].dst:<20}  {packet.summary():<20}\n\n"
                packet_text.insert(END, packet_info)  # Exibe na GUI

        # Verifica pacotes UDP para HTTP/3 (transportados sobre QUIC)
        elif packet.haslayer(UDP) and (packet[UDP].dport == 443 or packet[UDP].sport == 443):
            packet_info = f"\nHTTP/3 (QUIC): {packet[IP].src:<20} {packet[IP].dst:<20}  {packet.summary():<20}\n\n"
            packet_text.insert(END, packet_info)  # Exibe na GUI

# Função para iniciar a captura de pacotes
def start_capture():
    global capturing
    capturing = True
    start_button.config(state=DISABLED)  # Desabilita o botão de iniciar
    stop_button.config(state=NORMAL)      # Habilita o botão de parar

    # Captura pacotes HTTP (porta 80), HTTPS (porta 443) e pacotes UDP para HTTP/3
    sniff(filter="tcp port 80 or tcp port 443 or udp port 443", prn=packet_callback, stop_filter=lambda x: not capturing)

# Função para parar a captura de pacotes
def stop_capture():
    global capturing
    capturing = False
    start_button.config(state=NORMAL)    # Reabilita o botão de iniciar
    stop_button.config(state=DISABLED)    # Desabilita o botão de parar
    print("Captura parada.")

# Função para salvar pacotes em formato PCAPNG
def save_capture():
    # Janela para selecionar o local de salvamento
    file_path = filedialog.asksaveasfilename(defaultextension=".pcapng",
                                             filetypes=[("PCAPNG files", "*.pcapng"), ("All files", "*.*")])
    if file_path:
        # Salva os pacotes capturados no arquivo especificado
        wrpcap(file_path, captured_packets)
        print(f"Pacotes salvos em: {file_path}")

# Criando a interface gráfica
root = Tk()
root.title("HTTP/HTTPS Packet Sniffer")
root.geometry("1250x950")
root.wm_state('zoomed')

# Label
label = Label(root, text="Pacotes HTTP/HTTPS/HTTP/3 capturados", font=("Arial", 12))
label.pack()

# Botão para iniciar a captura com formatação
start_button = Button(root, text="Iniciar Captura", command=lambda: threading.Thread(target=start_capture).start(),
                      font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
start_button.pack(pady=10)

# Botão para parar a captura
stop_button = Button(root, text="Parar Captura", command=stop_capture, state=DISABLED,
                     font=("TkDefaultFont", 11, "bold"), bg='#29eb0c')
stop_button.pack(pady=10)

# Botão para salvar os pacotes capturados em PCAPNG
save_button = Button(root, text="Salvar Captura", command=save_capture,
                     font=("TkDefaultFont", 11, "bold"), bg='#eb0c38')
save_button.pack(pady=10)

# Campo de texto com barra de rolagem para exibir pacotes
packet_text = scrolledtext.ScrolledText(root, width=145, height=45)
packet_text.pack(pady=10)

root.mainloop()

