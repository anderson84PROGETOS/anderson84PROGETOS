import os
import sys
import warnings
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗███╗   ██╗██╗███████╗███████╗███████╗██████╗     ██████╗  █████╗  ██████╗ ██████╗ ████████╗███████╗███████╗
██╔════╝████╗  ██║██║██╔════╝██╔════╝██╔════╝██╔══██╗    ██╔══██╗██╔══██╗██╔════╝██╔═══██╗╚══██╔══╝██╔════╝██╔════╝
███████╗██╔██╗ ██║██║█████╗  █████╗  █████╗  ██████╔╝    ██████╔╝███████║██║     ██║   ██║   ██║   █████╗  ███████╗
╚════██║██║╚██╗██║██║██╔══╝  ██╔══╝  ██╔══╝  ██╔══██╗    ██╔═══╝ ██╔══██║██║     ██║   ██║   ██║   ██╔══╝  ╚════██║
███████║██║ ╚████║██║██║     ██║     ███████╗██║  ██║    ██║     ██║  ██║╚██████╗╚██████╔╝   ██║   ███████╗███████║
╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝    ╚═╝   ╚══════╝╚══════╝
""")

# === Silenciar saída padrão de erros (como Wireshark warnings)
sys.stderr = open(os.devnull, "w")

# === Silenciar CryptographyDeprecationWarning específico
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

# === Agora sim, importar o Scapy depois de redirecionar os avisos
import threading
from scapy.all import sniff, wrpcap, conf
from scapy.layers.inet import IP

# === Silenciar logs internos do Scapy
conf.verb = 0

# === Variáveis globais
captured_packets = []
sniffing = False

def print_packet(pkt):
    if IP in pkt:
        proto = pkt[IP].proto
        proto_name = {1: "ICMP", 6: "TCP", 17: "UDP"}.get(proto, "OTHER")
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst

        if proto_name in ["TCP", "UDP"]:
            sport = pkt.sport
            dport = pkt.dport
            msg = Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[{proto_name:<7}] {src_ip:<20} {str(sport):<10}  {dst_ip:<25} {str(dport):<10}"
        elif proto_name == "ICMP":
            msg = Fore.LIGHTGREEN_EX + Style.BRIGHT + f"[{proto_name:<7}] {src_ip:<20} {'-':<10}  {dst_ip:<25} {'-':<10}"
        else:
            msg = Fore.LIGHTCYAN_EX + Style.BRIGHT +  f"[{proto_name:<7}] {src_ip:<20} {'???':<10}  {dst_ip:<25} {'???':<10}"

        print(msg)
        captured_packets.append(pkt)

def start_sniff():
    global sniffing
    sniffing = True
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n>> Iniciando captura\n")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{'PROTO':<9} {'SRC IP':<20} {'PORT':<10}  {'DST IP':<25} {'PORT':<10}")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "-" * 80)

    def sniff_packets():
        sniff(prn=print_packet, stop_filter=lambda x: not sniffing)

    t = threading.Thread(target=sniff_packets, daemon=True)
    t.start()

def stop_sniff():
    global sniffing
    sniffing = False
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n>> Captura finalizada\n")

    salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + ">> Deseja salvar os resultados? (s/n): ").strip().lower()
    if salvar != 's':
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n>> Resultados descartados.\n")
        return

    path = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n>> Digite o nome do arquivo para salvar (.pcap): ").strip()

    if not path.endswith(".pcap"):
        path += ".pcap"

    if path:
        wrpcap(path, captured_packets)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n>> Pacotes salvos em: {path}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n>> Nome de arquivo inválido. Nada foi salvo.\n")

# ====== Interface CLI ======
if __name__ == "__main__":
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "===== SNIFFER DE PACOTES =====")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n  Comandos disponíveis\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT +"  start - Iniciar captura")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT +"  stop  - Parar e salvar | Ctrl + C")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT +"  exit  - Sair sem salvar\n")

    while True:
        try:
            cmd = input("").strip().lower()

            if cmd == "start":
                if sniffing:
                    print("\n>> Captura já em andamento.\n")
                else:
                    start_sniff()

            elif cmd == "stop":
                if sniffing:
                    stop_sniff()
                else:
                    print("\n>> Nenhuma captura em andamento.\n")

            elif cmd == "exit":
                if sniffing:
                    print("\n>> Parando captura antes de sair\n")
                    stop_sniff()
                print("\n>> Encerrando.\n")
                break

            else:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n>> Comando desconhecido. Use: start, stop, exit.\n")
        except KeyboardInterrupt:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n>> Interrompido pelo usuário.\n")
            if sniffing:
                stop_sniff()
            break

input(Fore.LIGHTRED_EX + "\n\n  ========== PRESSIONE ENTER PARA SAIR ==========\n")
