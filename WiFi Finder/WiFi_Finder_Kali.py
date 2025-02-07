import subprocess
import re
from mac_vendor_lookup import MacLookup
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗███████╗██╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝                                                                                                                     
""")
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Exemplo: Copiar e colar no website o BSSID Endereço MAC: f0:25:8e:cb:5f:14")
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nSe não aparecer o nome do Fabricante, acesse o website: https://macvendors.com\n")

def scan_wifi_linux():
    """Escaneia redes Wi-Fi usando iwlist no Kali Linux."""
    padrao_ssid = re.compile(r'ESSID:"(.*?)"')
    padrao_bssid = re.compile(r"Address: ([\w:]+)")
    padrao_sinal = re.compile(r"Quality=(\d+)/(\d+)")
    padrao_canal = re.compile(r"Channel:(\d+)")

    redes_encontradas = {}

    try:
        result = subprocess.check_output(["iwlist", "wlan0", "scan"], encoding='utf-8')
        blocos = result.split("Cell")  # Divide por cada rede encontrada

        for bloco in blocos[1:]:  # Ignora a primeira parte (introdução do comando)
            ssid = padrao_ssid.search(bloco)
            bssid = padrao_bssid.search(bloco)
            sinal = padrao_sinal.search(bloco)
            canal = padrao_canal.search(bloco)

            if ssid and bssid:
                mac_address = bssid.group(1)
                if mac_address not in redes_encontradas:
                    try:
                        fabricante = MacLookup().lookup(mac_address)
                    except:
                        fabricante = "Desconhecido"

                    if sinal:
                        qualidade = int(sinal.group(1)) / int(sinal.group(2)) * 100  # Converte para percentual
                        sinal_status = "Fraco" if qualidade < 40 else "Médio" if qualidade < 70 else "Forte"
                    else:
                        qualidade = "Desconhecido"
                        sinal_status = "Desconhecido"

                    redes_encontradas[mac_address] = (
                        ssid.group(1),
                        canal.group(1) if canal else "Desconhecido",
                        fabricante,
                        f"{qualidade:.1f}%" if qualidade != "Desconhecido" else "Desconhecido",
                        sinal_status
                    )

    except subprocess.CalledProcessError as e:
        print(f"\nErro ao executar iwlist: {e}")    

    return redes_encontradas

def mostrar_resultados():
    redes_wifi = scan_wifi_linux()
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n=== Redes Wi-Fi detectadas no Kali Linux (iwlist) ===\n")
    print("SSID                         BSSID                     Canal    Fabricante                             Sinal        ")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "=" * 116)
    for bssid, (ssid, canal, fabricante, sinal, sinal_status) in redes_wifi.items():
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ssid:<28} {bssid:<25} {canal:<8} {fabricante:<38} {sinal} ({sinal_status:<5})")

if __name__ == "__main__":
    mostrar_resultados()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
