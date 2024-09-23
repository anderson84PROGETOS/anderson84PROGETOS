from scapy.all import rdpcap, IP, DNS, DNSQR, DNSRR, TCP, UDP
import tkinter as tk
from tkinter import scrolledtext, filedialog
from datetime import datetime

def process_pcap(file_path):
    # Listas para armazenar os diferentes tipos de resultados
    dns_results = []
    tls_results = []

    # Abrir o arquivo .pcap e processar
    packets = rdpcap(file_path)
    for packet in packets:
        # Processar pacotes DNS
        if packet.haslayer(IP) and packet.haslayer(DNS):
            # Extrair as informações relevantes do pacote DNS e IP
            ip_layer = packet[IP]

            # Converter timestamp
            timestamp = datetime.fromtimestamp(float(packet.time)).strftime('%H:%M:%S.%f')[:-3]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst

            # Inicialize variáveis para DNS Query e Response
            query_name = ""
            response_name = ""
            response_data = ""

            # Verifique se o pacote tem uma camada DNS de consulta
            if packet.haslayer(DNSQR):
                query_name = packet[DNSQR].qname.decode()  # Certifique-se de que qname é uma string

            # Verifique se o pacote tem uma camada DNS de resposta
            if packet.haslayer(DNSRR):
                response_name = packet[DNSRR].rrname.decode()  # Certifique-se de que rrname é uma string
                response_data = packet[DNSRR].rdata  # rdata pode ser uma string ou bytes

                # Verifique se response_data é bytes e decodifique se necessário
                if isinstance(response_data, bytes):
                    try:
                        response_data = response_data.decode()
                    except UnicodeDecodeError:
                        response_data = str(response_data)

            # Montar a linha de resultado
            if query_name:
                result = f"{timestamp:<15} {src_ip:<20} {dst_ip:<20} DNS                    Standard query {query_name}"
                dns_results.append(result)
            if response_name:
                result = f"{timestamp:<15} {src_ip:<20} {dst_ip:<20} DNS                    Standard query response {response_name} {response_data}"
                dns_results.append(result)

        # Verificar pacotes que poderiam incluir TLS com base na porta
        if packet.haslayer(IP):
            if packet.haslayer(UDP) and packet[UDP].dport == 443:
                timestamp = datetime.fromtimestamp(float(packet.time)).strftime('%H:%M:%S.%f')[:-3]
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                result = f"{timestamp:<15} {src_ip:<20} {dst_ip:<20} TLS                     Possible TLS (UDP/443)"
                tls_results.append(result)

            if packet.haslayer(TCP) and packet[TCP].dport == 443:
                timestamp = datetime.fromtimestamp(float(packet.time)).strftime('%H:%M:%S.%f')[:-3]
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                result = f"{timestamp:<15} {src_ip:<20} {dst_ip:<20} TLS                      Possible TLS (TCP/443)"
                tls_results.append(result)

    # Combinar todas as listas na ordem desejada
    combined_results = dns_results + tls_results

    # Remover duplicatas mantendo a ordem
    seen = set()
    unique_results = []
    for result in combined_results:
        if result not in seen:
            unique_results.append(result)
            seen.add(result)

    return unique_results

def show_results():
    # Limpar a área de texto
    output_text.delete('1.0', tk.END)
    # Ler e processar o arquivo
    results = process_pcap(file_path.get())
    # Cabeçalhos
    output_text.insert(tk.END, f"{'Time':<22} {'Origin IP':<20} {'Destination':<18} {'Protocol':<20} {'Information'}\n")
    output_text.insert(tk.END, "="*58 + '\n\n')
    # Exibir os resultados
    for result in results:
        output_text.insert(tk.END, result + '\n\n')

def select_file():
    # Abrir uma caixa de diálogo para selecionar um arquivo
    file = filedialog.askopenfilename(filetypes=[("PCAP Files", "*.pcapng")])
    if file:
        file_path.set(file)

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("DNS Packet Viewer")

# Área para inserir o caminho do arquivo
label = tk.Label(root, text="Caminho do arquivo .pcapng", font=("TkDefaultFont", 11, "bold"))
label.pack(padx=10, pady=5)

file_path = tk.StringVar()

entry = tk.Entry(root, textvariable=file_path, width=40, font=("TkDefaultFont", 11, "bold"))
entry.pack(padx=10, pady=5)

# Botão para abrir a caixa de diálogo para seleção do arquivo
select_file_button = tk.Button(root, text="Selecionar Arquivo", command=select_file, bg="#11edde", font=("TkDefaultFont", 11, "bold"))
select_file_button.pack(padx=10, pady=5)

# Botão para carregar e processar o arquivo
load_button = tk.Button(root, text="Carregar e Mostrar Resultados", command=show_results, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
load_button.pack(padx=10, pady=5)

# Área de texto para exibir os resultados
output_text = scrolledtext.ScrolledText(root, width=150, height=43, font=("TkDefaultFont", 11, "bold"))
output_text.pack(padx=10, pady=10)

# Iniciar a interface gráfica
root.mainloop()
